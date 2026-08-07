"""JSONL 파일 포맷을 다루는 공통 층 — 어떤 엔티티인지 모른 채 동작한다.

여기 있는 것 셋:

- ``atomic_write_lines``  : 임시 파일 + fsync + ``os.replace``
- ``RawLine``             : 한 줄의 세 가지 상태(원문만 / dict 까지 / 객체까지)
- ``JsonlStore``          : 열기·스트리밍·원자적 재작성 (제네릭)

## 읽기 경로가 둘인 이유

이전에는 읽기 진입점이 ``stream()`` 하나였고 그것이 파싱 실패 줄을 **건너뛰었다**.
그런데 ``delete``/``update``/``reassign`` 이 파일을 다시 쓸 때도 같은 ``stream()`` 을
재료로 썼다. 결과적으로 무관한 거래 하나를 지우면 **손상된 줄이 디스크에서 영구
삭제**됐다. 또 같은 원인으로 ID 스캔이 검증 실패 줄의 id 를 놓쳐 번호가 재발급됐다.

- ``iter_raw()`` — 모든 줄을 원문과 함께 준다. 재작성 경로와 ID 스캔이 쓴다.
- ``stream()``   — 검증을 통과한 도메인 객체만 준다. 조회 경로가 쓴다.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Generic, Iterable, Iterator, List, Optional, TypeVar

from ..errors import ValidationError
from . import config, messages

logger = logging.getLogger(config.LOGGER_NAME)

T = TypeVar("T")

# 한 줄을 도메인 객체로 세우다 실패할 수 있는 경우들.
# JSONDecodeError: JSON 이 아님 / KeyError: 필수 키 없음 / ValidationError: 규칙 위반
# TypeError: JSON 은 맞지만 객체가 아님(예: 최상위가 리스트)
_LINE_ERRORS = (json.JSONDecodeError, ValidationError, KeyError, TypeError)


# ============================================================
# 원자적 쓰기
# ============================================================


def stage_lines(path: Path, lines: Iterable[str]) -> Path:
    """임시 파일에 전부 쓰고 디스크에 내린 뒤, 그 임시 경로를 돌려준다.

    아직 **교체하지 않는다.** 교체는 ``commit_staged`` 가 한다. 둘로 나눈 이유는
    여러 파일을 함께 커밋하기 위해서다 — 전부 준비해 둔 뒤 ``os.replace`` 만 연달아
    실행하면, 두 파일이 어긋난 상태로 남는 창이 rename 두 번 사이로 줄어든다.

    ``flush`` + ``fsync`` 를 여기서 하는 이유: ``replace`` 가 보장하는 것은 "이름이
    가리키는 대상이 순간적으로 바뀐다"이지 "내용이 디스크에 도달했다"가 아니다.
    fsync 없이 전원이 끊기면 새 이름이 **내용이 비어 있는 파일**을 가리킬 수 있다.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + config.TMP_SUFFIX)
    with open(
        tmp,
        "w",
        encoding=config.FILE_ENCODING,
        errors=config.FILE_ERRORS,
        newline=config.LINE_TERMINATOR,
    ) as f:
        for line in lines:
            f.write(line + config.LINE_TERMINATOR)
        f.flush()
        os.fsync(f.fileno())
    return tmp


def commit_staged(tmp: Path, target: Path) -> None:
    """준비된 임시 파일을 대상 이름으로 교체한다 — 같은 파일시스템에서 원자적."""
    os.replace(tmp, target)


def atomic_write_lines(path: Path, lines: Iterable[str]) -> None:
    """파일 하나를 원자적으로 교체한다 — 준비와 커밋을 연달아 수행.

    이름에 밑줄이 없는 이유: 같은 계층의 ``ids.IdWatermark`` 도 이 함수를 쓴다.
    "JSONL 파일을 다루는 법"이 아니라 "파일 하나를 안전하게 갈아 끼우는 법"이라
    저장소 계층의 공용 도구다.
    """
    commit_staged(stage_lines(path, lines), path)


# ============================================================
# 한 줄의 세 가지 상태
# ============================================================


@dataclass(frozen=True)
class RawLine:
    """파일의 한 줄 — 원문과 해석 결과를 함께 들고 다닌다.

    상태가 셋이다: 원문만 있음(JSON 아님) / dict 까지 됨(도메인 규칙 위반) /
    도메인 객체까지 됨(정상). 재작성 시 앞의 둘은 ``text`` 를 그대로 다시 쓴다.
    """

    lineno: int
    text: str
    data: Optional[dict] = None
    entity: Optional[Any] = None
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.entity is not None


# ============================================================
# JSONL 공통 저장소
# ============================================================


class JsonlStore(Generic[T]):
    """JSONL 파일 하나를 다루는 공통 동작.

    세 저장소가 열기/스트리밍/원자적 재작성 코드를 각자 복사해 갖고 있었다.
    "파일 포맷을 다루는 법"은 여기 한 번만 두고, 하위 클래스는 **엔티티별 규칙**
    (어떤 dataclass 인가, 무엇이 유일 키인가)만 갖는다.
    """

    #: 하위 클래스가 지정 — 줄 하나를 세울 dataclass
    entity_cls: type

    def __init__(self, path: Path) -> None:
        # 생성자는 경로 계산만 한다. 파일/폴더를 만드는 것은 ensure_ready() 의 일이다.
        # (이전에는 생성자가 mkdir·touch·기본 카테고리 시딩까지 해서, 객체를 만드는
        #  것만으로 디스크가 바뀌었다. 오타 난 --data-dir 도 조용히 폴더가 생겼다.)
        self.path = Path(path)

    # ---------- 준비 ----------

    def ensure_ready(self) -> None:
        """파일이 없으면 만든다 — 명시적으로 호출될 때만 디스크를 건드린다."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    @property
    def is_empty(self) -> bool:
        return not self.path.exists() or self.path.stat().st_size == 0

    # ---------- 읽기 ----------

    def iter_raw(self) -> Iterator[RawLine]:
        """모든 줄을 원문과 함께 yield 한다 — 어떤 줄도 버리지 않는다.

        빈 줄은 의미 없는 여백이므로 건너뛴다(보존 대상이 아니다).

        ``errors=surrogateescape`` 가 "손상 줄 격리" 약속을 **인코딩 층까지** 넓힌다.
        이전에는 엄격 디코딩이라 UTF-8 이 아닌 바이트 한 줄이 ``UnicodeDecodeError``
        로 **파일 전체 읽기를 죽였다** — JSON 이 깨진 줄은 격리하면서 바이트가 깨진
        줄은 격리하지 못하는, 같은 약속의 구멍이었다.
        """
        if not self.path.exists():
            return
        with open(self.path, encoding=config.FILE_ENCODING, errors=config.FILE_ERRORS) as f:
            for lineno, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line:
                    continue
                yield self._parse_line(lineno, line)

    def _parse_line(self, lineno: int, line: str) -> RawLine:
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            return RawLine(lineno=lineno, text=line, error=str(exc))
        try:
            entity = self.entity_cls.from_dict(data)
        except _LINE_ERRORS as exc:
            data_dict = data if isinstance(data, dict) else None
            return RawLine(lineno=lineno, text=line, data=data_dict, error=str(exc))
        return RawLine(lineno=lineno, text=line, data=data, entity=entity)

    def stream(self) -> Iterator[T]:
        """검증을 통과한 도메인 객체만 yield 한다 — 조회 전용 경로.

        손상된 줄은 건너뛰되 조용히 버리지 않고 경고 로그로 남긴다(사용자가
        데이터 이상을 인지할 수 있도록). 파일 자체는 손대지 않는다.
        """
        for raw in self.iter_raw():
            if raw.is_valid:
                yield raw.entity
            else:
                logger.warning(messages.LOG_CORRUPT_LINE, self.path.name, raw.lineno, raw.error)

    # ---------- 쓰기 ----------

    def _encode(self, entity: T) -> str:
        return json.dumps(entity.to_dict(), ensure_ascii=False)

    def append(self, entity: T) -> None:
        self._append_lines([self._encode(entity)])

    def append_all(self, entities: Iterable[T]) -> int:
        entities = list(entities)
        if not entities:
            return 0
        self._append_lines([self._encode(e) for e in entities])
        return len(entities)

    def _append_lines(self, lines: List[str]) -> None:
        """줄을 파일 끝에 이어 쓴다 — 이어 쓰기의 두 가지 위험을 함께 막는다.

        1. **찢어진 꼬리**: 마지막 줄에 개행이 없는 파일(쓰다 만 흔적, 손으로 편집한
           파일)에 그냥 이어 쓰면 새 JSON 이 그 줄 뒤에 붙어 **한 줄**이 된다. 결과는
           두 레코드가 동시에 죽는 것이다 — 기존 줄은 손상 줄로 보존되기라도 하지만,
           방금 "저장 완료" 라고 알린 레코드까지 목록에서 사라진다. 그래서 마지막
           바이트를 확인하고 필요하면 개행을 먼저 쓴다.
        2. **내구성 비대칭**: 재작성 경로만 fsync 를 하고 있었다. 같은 프로그램의 두
           쓰기 경로가 서로 다른 내구성을 약속할 이유가 없다. CLI 는 명령 하나에
           한 번 쓰고 끝나므로 비용도 무시할 수 있다.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        needs_newline = self._has_torn_tail()
        with open(
            self.path,
            "a",
            encoding=config.FILE_ENCODING,
            errors=config.FILE_ERRORS,
            newline=config.LINE_TERMINATOR,
        ) as f:
            if needs_newline:
                f.write(config.LINE_TERMINATOR)
                logger.warning(messages.LOG_TORN_TAIL, self.path.name)
            for line in lines:
                f.write(line + config.LINE_TERMINATOR)
            f.flush()
            os.fsync(f.fileno())

    def _has_torn_tail(self) -> bool:
        """마지막 바이트가 개행이 아닌가 — 바이트로 직접 확인한다.

        텍스트 모드로 끝을 보려면 파일을 통째로 읽어야 한다. ``rb`` + ``seek`` 이면
        1바이트만 읽으면 되고, 인코딩이 깨진 파일에서도 안전하다.
        """
        try:
            if self.path.stat().st_size == 0:
                return False
            with open(self.path, "rb") as f:
                f.seek(-1, os.SEEK_END)
                return f.read(1) != config.LINE_TERMINATOR.encode(config.FILE_ENCODING)
        except OSError:
            return False  # 파일이 없다 — 이어 쓰기가 새로 만든다

    def plan_rewrite(
        self,
        transform: Callable[[T], Optional[T]],
        *,
        extra: Iterable[T] = (),
    ) -> List[str]:
        """재작성 결과를 **계산만** 하고 줄 목록으로 돌려준다 — 파일은 건드리지 않는다.

        ``transform(entity)`` 는 새 엔티티를 돌려주거나 ``None`` 으로 삭제를 뜻한다.
        **해석하지 못한 줄은 원문 그대로 다시 쓴다** — 그래서 손상된 줄이 무관한
        수정 작업에 휩쓸려 사라지지 않는다.

        쓰기와 분리한 이유: 여러 저장소의 변경을 **한꺼번에** 커밋하려면(``UnitOfWork``)
        "무엇을 쓸지"와 "언제 쓸지"가 나뉘어야 한다.
        """
        lines: List[str] = []
        preserved = 0
        for raw in self.iter_raw():
            if not raw.is_valid:
                lines.append(raw.text)  # 해석 불가 — 원문 보존
                preserved += 1
                continue
            new_entity = transform(raw.entity)
            if new_entity is None:
                continue  # 삭제
            lines.append(self._encode(new_entity))
        lines.extend(self._encode(e) for e in extra)
        if preserved:
            logger.warning(messages.LOG_CORRUPT_PRESERVED, self.path.name, preserved)
        return lines

    def rewrite(
        self,
        transform: Callable[[T], Optional[T]],
        *,
        extra: Iterable[T] = (),
    ) -> None:
        """파일 하나를 원자적으로 다시 쓴다 — 계산 후 곧바로 커밋."""
        atomic_write_lines(self.path, self.plan_rewrite(transform, extra=extra))
