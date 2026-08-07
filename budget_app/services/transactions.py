"""거래 유스케이스 — 추가·수정·삭제·정렬 조회.

서비스가 판단하는 것은 **저장된 상태를 봐야 아는 것**뿐이다("카테고리가 등록됐나").
값 규칙(날짜 형식·금액 부호)은 ``Transaction.__post_init__`` 이 처리하므로 여기서
손대지 않는다. 그 구분이 ``ValidationError``(값) vs ``AppError``(상황)와 대응한다.
"""

from __future__ import annotations

from typing import Iterator, List, Optional

from . import messages
from ..decorators import log_call
from ..domain.entities import Transaction, TransactionPatch
from ..domain.queries import SearchFilter
from ..errors import AppError
from ..storage.repositories import CategoryStore, TransactionRepository


class TransactionService:
    """거래 추가/수정/삭제/조회 — 카테고리 등록 여부 검증 포함."""

    def __init__(self, txs: TransactionRepository, cats: CategoryStore):
        self.txs = txs
        self.cats = cats

    @log_call
    def add(
        self,
        date: str,
        type_: str,
        category: str,
        amount: int,
        memo: str = "",
        tags: Optional[List[str]] = None,
    ) -> Transaction:
        self._require_registered_category(category, hint=messages.HINT_CATEGORY_ADD_OR_LIST)
        # 검증·정규화는 Transaction.__post_init__ 이 일괄 수행한다(생성자가 유일한
        # 강제 지점). 여기서는 원값을 그대로 넘긴다.
        tx = Transaction(
            id=self.txs.next_id(),
            type=type_,
            date=date,
            amount=amount,
            category=category,
            memo=memo,
            tags=tags,
        )
        self.txs.append(tx)
        return tx

    @log_call
    def update(self, tx_id: str, patch: TransactionPatch) -> Transaction:
        """부분 수정 — 도메인이 새 객체를 만들고, 저장소는 그것을 쓰기만 한다.

        이전에는 저장소가 ``to_dict → dict.update → from_dict`` 로 변경을 해석했다.
        지금 순서는 조회 → ``with_patch`` (도메인) → ``replace`` (저장)다.
        """
        if patch.category is not None:
            self._require_registered_category(patch.category, hint=messages.HINT_CATEGORY_ADD)

        current = self.txs.get(tx_id)
        if current is None:
            raise AppError(messages.ERR_TX_NOT_FOUND.format(tx_id=tx_id), hint=messages.HINT_LIST_ID)

        updated = current.with_patch(patch)
        self.txs.replace(tx_id, updated)
        return updated

    @log_call
    def delete(self, tx_id: str) -> None:
        if not self.txs.delete(tx_id):
            raise AppError(messages.ERR_TX_NOT_FOUND.format(tx_id=tx_id), hint=messages.HINT_LIST_ID)

    def stream_sorted(self, flt: Optional[SearchFilter] = None) -> Iterator[Transaction]:
        """최신순 정렬된 거래를 yield 한다.

        주의: 정렬을 위해 한 번은 전체를 읽어야 한다(파일이 정렬되어 있지 않으므로).
        그러나 메모리 사용량은 '필터 통과 항목'으로 제한된다.
        """
        items = [tx for tx in self.txs.stream() if flt is None or flt.matches(tx)]
        items.sort(key=lambda t: (t.date, t.id), reverse=True)
        yield from items

    def _require_registered_category(self, name: str, *, hint: str) -> None:
        if not self.cats.exists(name):
            raise AppError(messages.ERR_CATEGORY_NOT_REGISTERED.format(name=name), hint=hint)
