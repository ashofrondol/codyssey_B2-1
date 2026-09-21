"""예산 설정과 월별 요약.

``monthly_summary`` 는 파일을 **한 번만** 순회하며 수입·지출·카테고리별 합계를
동시에 누적한다. 파생값(``balance``/``usage_pct``/``over_budget``)은 계산하지 않고
``MonthlySummary`` 의 property 에 맡긴다 — 서비스는 원자료만 담아 넘긴다.
"""

from __future__ import annotations

from ..decorators import measure_time
from ..domain import config as domain_config
from ..domain import validators
from ..domain.entities import Budget
from ..domain.queries import SearchFilter
from ..domain.results import MonthlySummary
from ..storage.repositories import BudgetStore, TransactionRepository
from . import config


class BudgetService:
    """예산 설정/조회 + 월별 요약."""

    def __init__(self, txs: TransactionRepository, budgets: BudgetStore):
        self.txs = txs
        self.budgets = budgets

    def set_budget(self, month: str, amount: int) -> Budget:
        return self.budgets.set(month, amount)

    def get_budget(self, month: str) -> Budget | None:
        """그 달의 예산 — 설정된 적이 없으면 ``None``.

        ``monthly_summary`` 가 이미 쓰던 조회를 그대로 밖으로 연다. 조회 경로가
        하나뿐이어야 ``budget get`` 과 ``summary`` 가 서로 다른 답을 낼 수 없다.
        """
        return self.budgets.get(month)

    def list_budgets(self) -> list[Budget]:
        """설정된 모든 월 예산 — 월 오름차순.

        같은 달이 두 줄 이상 남아 있으면(손으로 고친 파일) **마지막 줄**을 유효값으로
        본다. ``BudgetStore.get`` 이 쓰는 규칙과 같은 것이며, 다르게 고르면 같은
        파일을 두고 ``budget get`` 과 ``budget list`` 가 서로를 반박하게 된다.
        """
        latest: dict[str, Budget] = {}
        for budget in self.budgets.stream():
            latest[budget.month] = budget
        return [latest[month] for month in sorted(latest)]

    @measure_time
    def monthly_summary(self, month: str, top_n: int = config.DEFAULT_TOP_N) -> MonthlySummary:
        """월별 요약을 계산해 ``MonthlySummary`` 로 돌려준다.

        "이 달에 속하는가"의 판정을 ``SearchFilter.for_month`` 에 위임한 것이 핵심이다.
        이전에는 요약은 ``date.startswith(month + "-")``, 내보내기는 CLI 가 계산한
        말일 범위를 써서 **같은 개념이 두 알고리즘으로** 구현돼 있었다.
        """
        target = validators.parse_month(month)
        flt = SearchFilter.for_month(target)

        income_total = 0
        expense_total = 0
        per_category: dict[str, int] = {}
        has_data = False

        for tx in self.txs.stream():
            if not flt.matches(tx):
                continue
            has_data = True
            if tx.type == domain_config.TYPE_INCOME:
                income_total += tx.amount
            else:
                expense_total += tx.amount
                per_category[tx.category] = per_category.get(tx.category, 0) + tx.amount

        top_expense = tuple(
            sorted(per_category.items(), key=lambda kv: kv[1], reverse=True)[: max(0, top_n)]
        )
        return MonthlySummary(
            month=target,
            income=income_total,
            expense=expense_total,
            top_expense=top_expense,
            has_data=has_data,
            budget=self.budgets.get(target),
        )
