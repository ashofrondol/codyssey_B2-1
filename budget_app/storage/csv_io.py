"""CSV 경계 어댑터 — 외부 교환 포맷과 도메인 사이의 번역만 담당한다.

왜 서비스에서 떼어냈나:

``repository.py`` 는 "파일 입출력만 담당"한다고 선언해 놓고, 정작 CSV 를 여는
``open()`` 은 ``services.py`` 안에 있었다. **JSONL I/O 는 저장소, CSV I/O 는 서비스**
라는 일관성 없는 규칙이었다. 지금은 파일을 여는 코드가 전부 저장소 계층
(``repository``/``csv_io``)에 있고, ``services`` 에는 정책만 남는다.

## id 컬럼 — 왕복 중복을 막는 열쇠

이전 스키마에는 ``id`` 가 없었다. 그래서 ``export`` → ``import`` 왕복을 하면 같은
거래가 **새 id 를 받아 한 번 더 저장**됐다. 내보낸 CSV 가 원본 거래를 식별할 수단을
갖고 있지 않았기 때문이다.

``id`` 는 **선택** 컬럼으로 추가했다.

- ``export`` 는 기본으로 포함한다 → 자기 파일을 다시 넣어도 중복이 생기지 않는다.
- ``import`` 는 있으면 쓰고, 없거나 비어 있으면 새로 발급한다 → 필수 컬럼만 갖춘
  외부 CSV(엑셀·타 가계부)는 예전 그대로 들어온다.
- 외부 도구에 넘길 때 id 가 거슬리면 ``export --no-id`` 로 뺄 수 있다.
"""

from __future__ import annotations

import csv
import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from ..domain import config as domain_config
from ..domain import validators
from ..domain.entities import Transaction
from ..domain.tx_id import TransactionId
from ..errors import AppError
from . import config, messages


@dataclass(frozen=True)
class ParsedRow:
    """검증을 마친 CSV 한 행 — 아직 ``Transaction`` 은 아니다.

    id 가 아직 정해지지 않았을 수 있어서(빈 컬럼 → 발급 대상) 완성된 엔티티로
    만들 수 없다. 그 마지막 한 조각을 채우는 것은 중복 정책을 아는 서비스의 몫이다.
    """

    tx_id: TransactionId | None
    type: str
    date: str
    amount: int
    category: str
    memo: str
    tags: list[str]

    def to_transaction(self, tx_id: TransactionId) -> Transaction:
        return Transaction(
            id=tx_id,
            type=self.type,
            date=self.date,
            amount=self.amount,
            category=self.category,
            memo=self.memo,
            tags=self.tags,
        )


# ============================================================
# 읽기
# ============================================================


def read_rows(path: Path) -> Iterator[tuple[int, dict[str, str]]]:
    """CSV 를 읽어 ``(줄번호, 원시 dict)`` 를 yield 한다.

    헤더 검증은 첫 행을 읽는 시점에 한 번만 한다. 필수 컬럼은 예전과 동일하며
    ``id`` 는 요구하지 않는다.

    ``csv.Error`` 를 ``AppError`` 로 바꾸는 이유: 파서가 던지는 이 예외는 **일반
    사용자 조작만으로** 닿는다(한 필드가 128KB 를 넘거나, 따옴표가 닫히지 않아 파일
    끝까지 한 필드로 읽히는 CSV). 그대로 흘려보내면 CLI 의 최후 방어선까지 올라가
    "예기치 못한 오류"로 표시된다 — 원인도 해결 방법도 알 수 있는 오류인데
    분류되지 않은 버그처럼 보이는 것은 요구사항 Q2(원인 + 해결 힌트)에 어긋난다.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(str(path))

    with open(path, encoding=config.CSV_READ_ENCODING, newline="") as f:
        reader = csv.DictReader(f)
        try:
            # ``fieldnames`` 조회가 첫 행을 실제로 읽으므로 이것도 try 안에 둔다.
            _check_header(path, reader.fieldnames)
            # 이 함수가 소비되는 동안 ``with`` 블록이 살아 있고, 파일은 마지막 행을
            # 꺼낸 뒤에 닫힌다(제너레이터라 그 시점이 호출자에 달렸다).
            for item in enumerate(reader, start=config.CSV_DATA_START_LINE):
                yield item
        except csv.Error as exc:
            raise AppError(
                messages.ERR_CSV_PARSE.format(error=exc), hint=messages.HINT_CSV_PARSE
            ) from exc


def _check_header(path: Path, fieldnames: Iterable[str] | None) -> None:
    names = list(fieldnames or [])
    if not names:
        raise AppError(
            messages.ERR_CSV_NO_HEADER.format(path=path),
            hint=messages.HINT_CSV_NO_HEADER.format(
                columns=domain_config.TAG_SEPARATOR.join(config.CSV_REQUIRED_COLUMNS)
            ),
        )
    missing = [c for c in config.CSV_REQUIRED_COLUMNS if c not in names]
    if missing:
        raise AppError(
            messages.ERR_CSV_MISSING.format(missing=missing),
            hint=messages.HINT_CSV_REQUIRED.format(columns=list(config.CSV_REQUIRED_COLUMNS)),
        )


def parse_row(row: dict[str, str]) -> ParsedRow:
    """원시 CSV 행을 검증한다 — 실패 시 ``ValidationError``.

    필드 규칙은 ``validators`` 를 그대로 쓴다. CSV 경로라고 해서 별도의 검증 코드를
    두지 않는 것이 핵심이다(규칙은 한 곳에만 있어야 한다).
    """
    raw_id = (row.get(config.CSV_ID_COLUMN) or "").strip()
    return ParsedRow(
        # 빈 id 는 "발급해 달라"는 뜻이므로 오류가 아니다. 값이 있으면 형식을 강제한다.
        tx_id=TransactionId.parse(raw_id) if raw_id else None,
        type=validators.parse_type(row["type"]),
        date=validators.parse_date(row["date"]),
        amount=validators.parse_amount(row["amount"]),
        category=validators.parse_category(row.get("category") or ""),
        memo=validators.parse_memo(row.get("memo")),
        tags=validators.parse_tags(row.get("tags")),
    )


# ============================================================
# 쓰기
# ============================================================


def write_transactions(path: Path, txs: Iterable[Transaction], *, include_id: bool = True) -> int:
    """거래를 CSV 로 저장하고 작성 건수를 반환한다.

    인코딩은 BOM 없는 UTF-8 로 고정한다 — 우리가 내보낸 파일에는 BOM 을 넣지 않는다.
    반대로 **읽기는** ``CSV_READ_ENCODING`` (``utf-8-sig``) 이라 엑셀이 붙인 BOM 은
    흡수한다. 즉 왕복도 외부 CSV 도 모두 안전하다.

    쓰기는 **임시 파일 + ``os.replace``** 다(JSONL 쓰기와 같은 규칙). 대상 경로를
    곧바로 열면 쓰다가 실패했을 때 헤더만 남은 **반쪽 CSV** 가 그 자리에 남는다.
    사용자에게는 "내보내기 실패"라고 알렸는데 파일은 존재하는 상태라, 그 파일을
    백업으로 믿고 쓰면 데이터가 조용히 사라진다. 지금은 준비가 끝난 뒤에만 이름이
    바뀌므로 결과는 "완전한 새 파일" 또는 "손대지 않은 기존 파일" 둘 중 하나다.
    """
    path = Path(path)
    if path.is_dir():
        # 임시 파일 경로로 먼저 쓰기 때문에, 이 검사가 없으면 폴더를 준 실수가
        # ``os.replace`` 단계에서야 드러나 오류 메시지에 사용자가 치지 않은
        # ``.tmp`` 경로가 찍힌다. 읽기 쪽 ``read_rows`` 의 존재 검사와 같은 자리다.
        raise IsADirectoryError(str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(config.CSV_FIELDS if include_id else config.CSV_FIELDS_WITHOUT_ID)

    tmp = path.with_name(path.name + config.TMP_SUFFIX)
    count = 0
    try:
        with open(tmp, "w", encoding=config.CSV_ENCODING, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for tx in txs:
                writer.writerow(_to_row(tx, include_id))
                count += 1
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        # 실패했으면 임시 파일을 남기지 않는다(정리 실패가 원인 예외를 가리면 안 된다).
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return count


def _to_row(tx: Transaction, include_id: bool) -> dict[str, object]:
    row: dict[str, object] = {
        "date": tx.date,
        "type": tx.type,
        "category": tx.category,
        "amount": tx.amount,
        "memo": tx.memo,
        "tags": domain_config.TAG_SEPARATOR.join(tx.tags),
    }
    if include_id:
        # 값 객체는 경계에서 원시 값으로 푼다 (CSV 셀은 문자열이어야 한다).
        row[config.CSV_ID_COLUMN] = tx.id.value
    return row
