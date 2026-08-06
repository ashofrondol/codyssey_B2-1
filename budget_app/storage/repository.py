"""저장소 계층 — JSONL 파일 입출력만 담당한다.

설계 메모:

- 모든 읽기는 제너레이터로 한 줄씩 스트리밍한다. 대용량 파일도 메모리에 전부
  올리지 않는다.
- 파일 전체를 다시 써야 하는 작업(update/delete/재지정)은 '임시 파일 +
  ``os.replace``' 의 원자적 교체 패턴을 쓴다. 쓰는 도중 프로세스가 죽어도 원본이
  깨지지 않는다.
- 저장소는 **도메인 판단을 하지 않는다.** 완성된 객체를 받아 쓰고, 저장된 객체를
  돌려줄 뿐이다. "무엇으로 바꿀지"는 서비스와 모델이 정한다.

## 읽기 경로가 둘인 이유 (리팩터 핵심)

이전에는 읽기 진입점이 ``stream()`` 하나였고, 그것이 파싱 실패 줄을 **건너뛰었다**.
그런데 ``delete``/``update``/``reassign`` 이 파일을 다시 쓸 때도 같은 ``stream()``
을 재료로 썼다. 결과적으로 무관한 거래 하나를 지우면 **손상된 줄이 디스크에서
영구 삭제**됐다. 경고 로그는 "읽을 때 건너뛴다"는 뜻이었지 "파일에서 지웠다"는
뜻이 아니라서 사용자는 유실을 알 수 없었다.

또 같은 원인으로 ID 가 충돌했다. ``max_id_num()`` 이 ``stream()`` 을 통해 최대
번호를 구했기 때문에, 검증에 실패하는 줄(예: ``amount: 0``)에 들어 있던 id 는
보이지 않았다. 그 파일에 새 거래를 넣으면 **이미 쓰인 번호가 다시 발급**됐다.

그래서 읽기를 둘로 나눴다.

- ``iter_raw()`` — 모든 줄을 원문과 함께 준다. 파싱 실패도 버리지 않는다.
  재작성 경로와 ID 스캔이 쓴다.
- ``stream()``   — 검증을 통과한 도메인 객체만 준다. 조회 경로가 쓴다.

재작성은 ``iter_raw()`` 기반이므로 손상 줄이 **원문 그대로 보존**된다.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Generic, Iterable, Iterator, List, Optional, Set, Tuple, TypeVar

from .. import config, messages
from ..domain import validators
from ..domain.models import Budget, Category, Transaction, TransactionPatch
from ..errors import ValidationError

logger = logging.getLogger(config.LOGGER_NAME_REPOSITORY)

T = TypeVar("T")

_ID_SCAN_RE = re.compile(config.TX_ID_SCAN_PATTERN)

# 한 줄을 도메인 객체로 세우다 실패할 수 있는 경우들.
# JSONDecodeError: JSON 이 아님 / KeyError: 필수 키 없음 / ValidationError: 규칙 위반
# TypeError: JSON 은 맞지만 객체가 아님(예: 최상위가 리스트)
_LINE_ERRORS = (json.JSONDecodeError, ValidationError, KeyError, TypeError)


# ============================================================
# 원자적 쓰기
# ============================================================


def _atomic_write_lines(path: Path, lines: Iterable[str]) -> None:
    """임시 파일에 모두 쓴 뒤 ``os.replace`` 로 원자적 교체.

    ``os.replace`` 는 같은 파일시스템 안에서 원자적이다. 교체 전에
    ``flush`` + ``fsync`` 를 하는 이유: ``replace`` 가 보장하는 것은 "이름이 가리키는
    대상이 순간적으로 바뀐다"이지 "내용이 디스크에 도달했다"가 아니다. fsync 없이
    전원이 끊기면 새 이름이 **내용이 비어 있는 파일**을 가리킬 수 있다.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + config.TMP_SUFFIX)
    with open(tmp, "w", encoding=config.FILE_ENCODING, newline=config.LINE_TERMINATOR) as f:
        for line in lines:
            f.write(line + config.LINE_TERMINATOR)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


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
        """
        if not self.path.exists():
            return
        with open(self.path, encoding=config.FILE_ENCODING) as f:
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
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding=config.FILE_ENCODING, newline=config.LINE_TERMINATOR) as f:
            f.write(self._encode(entity) + config.LINE_TERMINATOR)

    def append_all(self, entities: Iterable[T]) -> int:
        entities = list(entities)
        if not entities:
            return 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding=config.FILE_ENCODING, newline=config.LINE_TERMINATOR) as f:
            for entity in entities:
                f.write(self._encode(entity) + config.LINE_TERMINATOR)
        return len(entities)

    def rewrite(
        self,
        transform: Callable[[T], Optional[T]],
        *,
        extra: Iterable[T] = (),
    ) -> None:
        """파일 전체를 원자적으로 다시 쓴다.

        ``transform(entity)`` 는 새 엔티티를 돌려주거나 ``None`` 으로 삭제를 뜻한다.
        **해석하지 못한 줄은 원문 그대로 다시 쓴다** — 그래서 손상된 줄이 무관한
        수정 작업에 휩쓸려 사라지지 않는다.

        ``extra`` 는 재작성 뒤에 이어 붙일 신규 항목이다(원자적 일괄 추가용).
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
        _atomic_write_lines(self.path, lines)
        if preserved:
            logger.warning(messages.LOG_CORRUPT_PRESERVED, self.path.name, preserved)


# ============================================================
# ID 발급
# ============================================================


class IdAllocator:
    """거래 ID 발급기 — 이미 쓰인 번호를 건너뛰며 순차 발급한다.

    이전에는 발급 규칙이 두 곳에 있었다. 저장소의 ``next_id()`` 와, 성능 때문에
    그것을 흉내 낸 ``import_csv`` 안의 ``next_num += 1``. 서비스가 저장소의 ID
    포맷을 알아야 했고, 두 경로가 어긋날 여지가 있었다. 발급기를 객체로 만들어
    한 번 받아 여러 번 쓰면, 파일 재스캔 없이도 규칙은 한 곳에 남는다.

    ``taken`` 을 들고 다니는 이유: CSV 가 명시한 id 를 그대로 쓰는 경우가 생기면서,
    "자동 발급 번호가 나중에 그 id 와 부딪치지 않는다"를 보장해야 한다.
    """

    def __init__(self, start: int = 0, taken: Optional[Set[str]] = None) -> None:
        self._counter = start
        self._taken: Set[str] = set(taken or ())

    def is_taken(self, tx_id: str) -> bool:
        return tx_id in self._taken

    def reserve(self, tx_id: str) -> None:
        """외부에서 지정한 id 를 점유 처리한다(CSV 가 실어 온 id 등)."""
        self._taken.add(tx_id)
        self._counter = max(self._counter, validators.tx_id_number(tx_id))

    def next(self) -> str:
        while True:
            self._counter += 1
            tx_id = config.TX_ID_FORMAT.format(self._counter)
            if tx_id not in self._taken:
                self._taken.add(tx_id)
                return tx_id


# ============================================================
# 엔티티별 저장소
# ============================================================


class TransactionRepository(JsonlStore[Transaction]):
    """transactions.jsonl 의 CRUD + 스트리밍 조회."""

    entity_cls = Transaction
    FILE_NAME = config.TX_FILE_NAME

    def __init__(self, data_dir: Path) -> None:
        super().__init__(Path(data_dir) / self.FILE_NAME)

    # ---------- ID ----------

    def _scan_id(self, raw: RawLine) -> str:
        """한 줄에서 거래 id 를 최대한 건져낸다.

        검증에 실패한 줄에도 id 는 들어 있을 수 있고, 그 번호는 **이미 쓰인 번호**다.
        놓치면 재발급으로 중복 id 가 생긴다. dict 까지 해석된 줄은 키에서, JSON 조차
        아닌 줄은 원문 정규식으로 찾는다.
        """
        if raw.data is not None:
            candidate = raw.data.get("id")
            if isinstance(candidate, str):
                return candidate.strip()
        match = _ID_SCAN_RE.search(raw.text)
        return match.group(1) if match else ""

    def id_state(self) -> Tuple[int, Set[str]]:
        """(최대 번호, 사용 중인 id 집합) — 파일을 한 번만 훑는다."""
        max_n = 0
        taken: Set[str] = set()
        for raw in self.iter_raw():
            tx_id = self._scan_id(raw)
            if not tx_id:
                continue
            taken.add(tx_id)
            max_n = max(max_n, validators.tx_id_number(tx_id))
        return max_n, taken

    def id_allocator(self) -> IdAllocator:
        """이 파일 상태에 맞춘 발급기를 만든다. 배치 작업은 이걸 한 번만 받아 쓴다."""
        max_n, taken = self.id_state()
        return IdAllocator(start=max_n, taken=taken)

    def next_id(self) -> str:
        """단건 추가용 — 발급기를 한 번 쓰고 버린다."""
        return self.id_allocator().next()

    def exists(self, tx_id: str) -> bool:
        _, taken = self.id_state()
        return tx_id in taken

    # ---------- 조회 ----------

    def get(self, tx_id: str) -> Optional[Transaction]:
        for tx in self.stream():
            if tx.id == tx_id:
                return tx
        return None

    def category_in_use(self, name: str) -> bool:
        return any(tx.category == name for tx in self.stream())

    # ---------- 쓰기 ----------

    def append_many(self, txs: Iterable[Transaction], *, atomic: bool = False) -> int:
        """여러 거래를 추가하고 추가된 건수를 반환한다.

        - ``atomic=False``: 파일 끝에 이어 쓰기. 중간에 죽으면 일부만 기록될 수
          있다(부분 성공 정책과 짝).
        - ``atomic=True``: 기존 내용 + 신규 전부를 임시 파일에 쓴 뒤 교체한다.
          '전부 반영' 또는 '전혀 반영 안 됨' 만 존재한다. 기존 손상 줄도 그대로
          보존된다(``rewrite`` 가 원문을 유지하므로).
        """
        txs = list(txs)
        if not atomic:
            return self.append_all(txs)
        self.rewrite(lambda tx: tx, extra=txs)
        return len(txs)

    def delete(self, tx_id: str) -> bool:
        """삭제 성공 시 True, 대상 없으면 False."""
        found = False

        def _drop(tx: Transaction) -> Optional[Transaction]:
            nonlocal found
            if tx.id == tx_id:
                found = True
                return None
            return tx

        # 대상이 있을 때만 파일을 다시 쓴다 — 조회만으로 파일 mtime 이 바뀌지 않도록.
        if not self.exists(tx_id):
            return False
        self.rewrite(_drop)
        return found

    def replace(self, tx_id: str, new_tx: Transaction) -> bool:
        """``tx_id`` 인 거래를 완성된 ``new_tx`` 로 통째 교체한다.

        저장소는 "무엇이 어떻게 바뀌는지" 모른다. 부분 변경 해석은 서비스가
        ``Transaction.with_patch`` 로 끝내고 완성품만 여기로 온다.
        """
        found = False

        def _swap(tx: Transaction) -> Transaction:
            nonlocal found
            if tx.id == tx_id:
                found = True
                return new_tx
            return tx

        if self.get(tx_id) is None:
            return False
        self.rewrite(_swap)
        return found

    def reassign_category(self, old: str, new: str) -> int:
        """old → new 카테고리 일괄 재지정. 변경된 건수 반환."""
        changed = 0

        patch = TransactionPatch(category=new)

        def _reassign(tx: Transaction) -> Transaction:
            nonlocal changed
            if tx.category != old:
                return tx
            changed += 1
            return tx.with_patch(patch)

        if not self.category_in_use(old):
            return 0
        self.rewrite(_reassign)
        return changed


class CategoryStore(JsonlStore[Category]):
    """categories.jsonl — 카테고리 이름 집합 관리."""

    entity_cls = Category
    FILE_NAME = config.CATEGORY_FILE_NAME

    def __init__(self, data_dir: Path) -> None:
        super().__init__(Path(data_dir) / self.FILE_NAME)

    def seed_defaults(self) -> int:
        """비어 있을 때만 기본 카테고리를 심는다. 심은 개수를 반환.

        "파일을 만드는 일"(``ensure_ready``)과 "초기 데이터를 넣는 일"은 다른 작업이라
        메서드를 나눴다. 둘 다 생성자가 아니라 명시적 호출인 이유는 부트스트랩이
        *한 번* 일어나야 하는 일이지 객체를 만들 때마다 일어날 일이 아니기 때문이다.
        """
        if not self.is_empty:
            return 0
        return self.append_all(Category(name=name) for name in config.DEFAULT_CATEGORIES)

    def list_names(self) -> List[str]:
        return [c.name for c in self.stream()]

    def name_set(self) -> Set[str]:
        """존재 확인을 반복할 때 쓰는 스냅숏 — 매번 파일을 훑지 않기 위해."""
        return {c.name for c in self.stream()}

    def exists(self, name: str) -> bool:
        target = validators.parse_category(name)
        return any(c.name == target for c in self.stream())

    def add(self, name: str) -> bool:
        """추가 성공 시 True, 이미 존재하면 False."""
        cat = Category(name=name)
        if self.exists(cat.name):
            return False
        self.append(cat)
        return True

    def add_many(self, names: Iterable[str]) -> int:
        """여러 이름을 한 번에 추가한다 — 존재 확인을 위해 파일을 한 번만 훑는다."""
        known = self.name_set()
        fresh: List[Category] = []
        for name in names:
            cat = Category(name=name)
            if cat.name in known:
                continue
            known.add(cat.name)
            fresh.append(cat)
        return self.append_all(fresh)

    def remove(self, name: str) -> bool:
        target = validators.parse_category(name)
        found = False

        def _drop(cat: Category) -> Optional[Category]:
            nonlocal found
            if cat.name == target:
                found = True
                return None
            return cat

        if not self.exists(target):
            return False
        self.rewrite(_drop)
        return found


class BudgetStore(JsonlStore[Budget]):
    """budgets.jsonl — 월별 예산 저장. 같은 월은 덮어쓴다."""

    entity_cls = Budget
    FILE_NAME = config.BUDGET_FILE_NAME

    def __init__(self, data_dir: Path) -> None:
        super().__init__(Path(data_dir) / self.FILE_NAME)

    def get(self, month: str) -> Optional[Budget]:
        target = validators.parse_month(month)
        result: Optional[Budget] = None
        for b in self.stream():
            if b.month == target:
                result = b  # 같은 월의 마지막 값을 유효값으로 본다
        return result

    def set(self, month: str, amount: int) -> Budget:
        budget = Budget(month=month, amount=amount)

        # month 별 단일 값 유지 — 같은 달의 기존 항목은 지우고 새 값을 끝에 붙인다.
        def _drop_same_month(existing: Budget) -> Optional[Budget]:
            return None if existing.month == budget.month else existing

        self.rewrite(_drop_same_month, extra=[budget])
        return budget


# ============================================================
# 백업
# ============================================================


def backup_data_dir(data_dir: Path, now: Optional[datetime] = None) -> Path:
    """data 폴더의 모든 ``*.jsonl`` 을 타임스탬프 폴더로 복사한다.

    서비스가 아니라 저장소 계층에 있는 이유: 도메인 판단이 전혀 없고 데이터
    디렉터리의 파일을 다루는 일이다. ``now`` 를 주입 가능하게 둔 이유: 이전에는
    ``datetime.now()`` 를 직접 불러서 시간을 고정하지 않으면 결과 경로를 검증할
    수 없었다.
    """
    src = Path(data_dir)
    if not src.exists():
        raise FileNotFoundError(str(src))
    ts = (now or datetime.now()).strftime(config.BACKUP_TS_FORMAT)
    dest = src.parent / f"{config.BACKUP_DIR_PREFIX}{ts}"
    dest.mkdir(parents=True, exist_ok=False)
    for p in src.glob(config.BACKUP_GLOB):
        (dest / p.name).write_bytes(p.read_bytes())
    return dest
