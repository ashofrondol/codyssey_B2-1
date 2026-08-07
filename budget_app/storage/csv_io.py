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
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from . import config, messages
from ..domain import config as domain_config
from ..domain import validators
from ..domain.entities import Transaction
from ..domain.tx_id import TransactionId
from ..errors import AppError


@dataclass(frozen=True)
class ParsedRow:
    """검증을 마친 CSV 한 행 — 아직 ``Transaction`` 은 아니다.

    id 가 아직 정해지지 않았을 수 있어서(빈 컬럼 → 발급 대상) 완성된 엔티티로
    만들 수 없다. 그 마지막 한 조각을 채우는 것은 중복 정책을 아는 서비스의 몫이다.
    """

    lineno: int
    tx_id: Optional[TransactionId]
    type: str
    date: str
    amount: int
    category: str
    memo: str
    tags: List[str]

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


def read_rows(path: Path) -> Iterator[tuple[int, Dict[str, str]]]:
    """CSV 를 읽어 ``(줄번호, 원시 dict)`` 를 yield 한다.

    헤더 검증은 첫 행을 읽는 시점에 한 번만 한다. 필수 컬럼은 예전과 동일하며
    ``id`` 는 요구하지 않는다.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(str(path))

    with open(path, encoding=config.CSV_ENCODING, newline="") as f:
        reader = csv.DictReader(f)
        _check_header(path, reader.fieldnames)
        for lineno, row in enumerate(reader, start=config.CSV_DATA_START_LINE):
            yield lineno, row


def _check_header(path: Path, fieldnames: Optional[Iterable[str]]) -> None:
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


def parse_row(lineno: int, row: Dict[str, str]) -> ParsedRow:
    """원시 CSV 행을 검증한다 — 실패 시 ``ValidationError``.

    필드 규칙은 ``validators`` 를 그대로 쓴다. CSV 경로라고 해서 별도의 검증 코드를
    두지 않는 것이 핵심이다(규칙은 한 곳에만 있어야 한다).
    """
    raw_id = (row.get(config.CSV_ID_COLUMN) or "").strip()
    return ParsedRow(
        lineno=lineno,
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

    인코딩은 BOM 없는 UTF-8 로 고정한다. BOM 을 넣으면 다시 ``import`` 할 때 헤더
    첫 컬럼명이 ``﻿id`` 로 깨져 왕복이 실패한다(왕복 안전성 우선).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(config.CSV_FIELDS if include_id else config.CSV_FIELDS_WITHOUT_ID)

    count = 0
    with open(path, "w", encoding=config.CSV_ENCODING, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tx in txs:
            writer.writerow(_to_row(tx, include_id))
            count += 1
    return count


def _to_row(tx: Transaction, include_id: bool) -> Dict[str, object]:
    row: Dict[str, object] = {
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
