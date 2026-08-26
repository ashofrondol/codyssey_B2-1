"""거래 유스케이스 — 추가·수정·삭제·정렬 조회.

서비스가 판단하는 것은 **저장된 상태를 봐야 아는 것**뿐이다("카테고리가 등록됐나").
값 규칙(날짜 형식·금액 부호)은 ``Transaction.__post_init__`` 이 처리하므로 여기서
손대지 않는다. 그 구분이 ``ValidationError``(값) vs ``AppError``(상황)와 대응한다.
"""

from __future__ import annotations

import heapq
from collections.abc import Iterator

from ..decorators import log_call
from ..domain.entities import Transaction, TransactionPatch
from ..domain.queries import SearchFilter
from ..domain.tx_id import TransactionId
from ..errors import AppError
from ..storage.repositories import CategoryStore, TransactionRepository
from . import messages


def _sort_key(tx: Transaction) -> tuple[str, TransactionId]:
    """최신순 정렬 키 — 날짜가 같으면 발급 번호로 가른다(둘 다 유일 순서를 만든다)."""
    return (tx.date, tx.id)


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
        tags: list[str] | None = None,
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
            raise AppError(
                messages.ERR_TX_NOT_FOUND.format(tx_id=tx_id), hint=messages.HINT_LIST_ID
            )

        updated = current.with_patch(patch)
        self.txs.replace(tx_id, updated)
        return updated

    @log_call
    def delete(self, tx_id: str) -> None:
        if not self.txs.delete(tx_id):
            raise AppError(
                messages.ERR_TX_NOT_FOUND.format(tx_id=tx_id), hint=messages.HINT_LIST_ID
            )

    def stream_sorted(
        self, flt: SearchFilter | None = None, *, limit: int | None = None
    ) -> Iterator[Transaction]:
        """최신순 정렬된 거래를 yield 한다 — ``limit`` 이 있으면 **상위 N 만** 들고 있는다.

        파일이 시간순으로 정렬돼 있지 않으므로 어느 쪽이든 전체를 한 번은 **훑어야**
        한다. 문제는 훑는 것이 아니라 **모으는 것**이었다: 이전 구현은 필터 통과분
        전체를 리스트로 적재한 뒤 정렬해서, ``list --limit 1`` 인데도 20만 행 파일이
        통째로 메모리에 올라왔다(피크 RSS 146MB). 요구사항 G2 의 "파일 전체를 한 번에
        로드하지 않고"가 여기서 깨졌다 — 하류 제너레이터의 ``break`` 는 **이미 만들어진
        리스트**를 자를 뿐이라 아무것도 아끼지 못했다.

        ``heapq.nlargest`` 는 크기 ``limit`` 짜리 힙 하나만 유지하며 스트림을 흘려
        보낸다. 메모리 상한이 파일 크기가 아니라 **O(limit)** 이 되고, 결과 순서는
        전체 정렬과 같다(키가 같은 항목이 없으므로 — id 는 유일하다).

        ``limit`` 이 없으면(``search`` 경로) 전체 정렬이 필요하므로 예전과 같다.
        """
        filtered = (tx for tx in self.txs.stream() if flt is None or flt.matches(tx))
        if limit is not None:
            yield from heapq.nlargest(limit, filtered, key=_sort_key)
            return
        yield from sorted(filtered, key=_sort_key, reverse=True)

    def _require_registered_category(self, name: str, *, hint: str) -> None:
        if not self.cats.exists(name):
            raise AppError(messages.ERR_CATEGORY_NOT_REGISTERED.format(name=name), hint=hint)
