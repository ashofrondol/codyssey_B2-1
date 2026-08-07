"""카테고리 관리 — 사용 중 카테고리 보호(참조 무결성).

거래가 참조하는 카테고리를 그냥 지우면 "존재하지 않는 카테고리를 가리키는 거래"가
남는다. 관계형 DB 의 ``ON DELETE RESTRICT`` / ``SET DEFAULT`` 를 코드로 구현한 것이다.
"""

from __future__ import annotations

from typing import List, Optional

from . import messages
from ..errors import AppError
from ..storage.repositories import CategoryStore, TransactionRepository


class CategoryService:
    """카테고리 추가/조회/삭제 — 사용 중 카테고리 보호."""

    def __init__(self, cats: CategoryStore, txs: TransactionRepository):
        self.cats = cats
        self.txs = txs

    def add(self, name: str) -> bool:
        return self.cats.add(name)

    def list_names(self) -> List[str]:
        return self.cats.list_names()

    def remove(self, name: str, replace_with: Optional[str] = None) -> int:
        """카테고리 삭제. 사용 중이라면:

        - ``replace_with`` 지정 시 → 해당 카테고리로 일괄 재지정 후 삭제
        - 미지정 시 → ``AppError`` 로 차단

        반환: 재지정된 거래 건수 (사용 중이 아니었으면 0).
        """
        if not self.cats.exists(name):
            raise AppError(
                messages.ERR_CATEGORY_NOT_EXIST.format(name=name),
                hint=messages.HINT_CATEGORY_LIST,
            )
        reassigned = 0
        if self.txs.category_in_use(name):
            reassigned = self._reassign_before_remove(name, replace_with)
        self.cats.remove(name)
        return reassigned

    def _reassign_before_remove(self, name: str, replace_with: Optional[str]) -> int:
        if not replace_with:
            raise AppError(
                messages.ERR_CATEGORY_IN_USE.format(name=name),
                hint=messages.HINT_REPLACE_WITH,
            )
        if replace_with == name:
            raise AppError(messages.ERR_REPLACE_SELF)
        if not self.cats.exists(replace_with):
            raise AppError(
                messages.ERR_REPLACE_NOT_REGISTERED.format(name=replace_with),
                hint=messages.HINT_ADD_FIRST,
            )
        return self.txs.reassign_category(name, replace_with)
