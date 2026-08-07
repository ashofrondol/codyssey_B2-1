"""카테고리 관리 — 사용 중 카테고리 보호(참조 무결성).

거래가 참조하는 카테고리를 그냥 지우면 "존재하지 않는 카테고리를 가리키는 거래"가
남는다. 관계형 DB 의 ``ON DELETE RESTRICT`` / ``SET DEFAULT`` 를 코드로 구현한 것이다.
"""

from __future__ import annotations

from typing import List, Optional

from . import messages
from ..domain import validators
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

        **진입부에서 두 이름을 먼저 정규화한다.** 이 메서드는 아래 넷을 비교하는데,
        그중 일부만 정규화되면 판정이 서로 어긋난다.

        =====================  ==============================
        비교                   정규화 없이 ``' etc '`` 를 주면
        =====================  ==============================
        ``exists(name)``       내부에서 정규화 → 존재한다고 나옴
        ``replace_with==name`` 문자열 비교 → **다르다고 나옴**
        ``reassign`` 결과       엔티티 생성자가 정규화 → 실제로는 같은 값
        =====================  ==============================

        결과가 "자기 자신으로 재지정한 뒤 그 카테고리를 삭제"였다. 거래는 남고
        카테고리만 사라져 **참조 무결성이 깨진다** — 이 클래스가 막으려던 바로 그
        상태다. 비교하는 값들의 정규화 시점이 다르면 가드는 언제든 우회된다.
        """
        target = validators.parse_category(name)
        replacement = validators.parse_category(replace_with) if replace_with else None

        if not self.cats.exists(target):
            raise AppError(
                messages.ERR_CATEGORY_NOT_EXIST.format(name=target),
                hint=messages.HINT_CATEGORY_LIST,
            )
        reassigned = 0
        if self.txs.category_in_use(target):
            reassigned = self._reassign_before_remove(target, replacement)
        self.cats.remove(target)
        return reassigned

    def _reassign_before_remove(self, name: str, replace_with: Optional[str]) -> int:
        """두 인자는 **이미 정규화된 값**이어야 한다(``remove`` 가 책임진다)."""
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
