"""프레젠터 — 도메인 객체를 사람이 읽을 줄로 바꾼다.

**출력하지 않고 문자열을 돌려준다.** 이것이 이 모듈의 유일한 규칙이다.

왜 그런가:

- 채널 결정(stdout/stderr)은 ``output`` 의 책임이다. 프레젠터가 ``print`` 를 하면
  두 모듈이 같은 책임을 나눠 갖게 된다.
- 반환값이 문자열이면 화면 없이 검증할 수 있다. 이전에는 요약 출력이
  ``cmd_summary`` 안에서 곧바로 ``print`` 되어, 형식을 확인하려면 프로세스를 띄우고
  stdout 을 캡처하는 수밖에 없었다.

프레젠터는 도메인 모델을 읽기만 하고 계산하지 않는다. "예산 미설정이면 N/A" 같은
판단은 ``MonthlySummary`` 의 property 가 이미 끝내 놓았고, 여기서는 ``None`` 인지만
본다.
"""

from __future__ import annotations

from typing import Iterable, Iterator, List, Optional, Sequence

from ..domain.entities import Transaction
from ..domain.results import ImportReport, MonthlySummary
from . import messages


# ============================================================
# 거래 표
# ============================================================


def tx_line(tx: Transaction) -> str:
    return messages.FMT_TX_LINE.format(
        id=tx.id,
        date=tx.date,
        type=tx.type,
        category=tx.category,
        amount=tx.amount,
        memo=tx.memo,
    )


def tx_table(rows: Iterable[Transaction], limit: Optional[int] = None) -> Iterator[str]:
    """거래 표를 줄 단위로 yield 한다 — 비어 있으면 안내 한 줄.

    제너레이터인 이유: 상류(``stream_sorted``)가 제너레이터이므로 여기서 리스트로
    모으면 스트리밍이 끊긴다. ``limit`` 이 걸리면 그 지점에서 상류 소비도 멈춘다.
    """
    count = 0
    for tx in rows:
        if limit is not None and count >= limit:
            break
        yield tx_line(tx)
        count += 1
    if count == 0:
        yield messages.MSG_NO_DATA


# ============================================================
# 월별 요약
# ============================================================


def summary_lines(summary: MonthlySummary) -> Iterator[str]:
    if summary.is_empty:
        yield messages.MSG_SUMMARY_NO_DATA.format(month=summary.month)
        return

    yield messages.MSG_SUMMARY_INCOME.format(income=summary.income)
    yield messages.MSG_SUMMARY_EXPENSE.format(expense=summary.expense)
    yield messages.MSG_SUMMARY_BALANCE.format(balance=summary.balance)

    if summary.budget is not None:
        yield from _budget_lines(summary)

    if summary.top_expense:
        yield messages.MSG_TOP_EXPENSE_HEADER.format(n=len(summary.top_expense))
        for rank, (category, amount) in enumerate(summary.top_expense, start=1):
            yield messages.FMT_TOP_EXPENSE_ITEM.format(rank=rank, category=category, amount=amount)


def _budget_lines(summary: MonthlySummary) -> Iterator[str]:
    usage = summary.usage_pct
    usage_str = (
        messages.FMT_USAGE_PCT.format(usage=usage) if usage is not None else messages.MSG_USAGE_NA
    )
    yield messages.MSG_SUMMARY_BUDGET.format(amount=summary.budget.amount, usage=usage_str)
    if summary.over_budget:
        yield messages.MSG_OVER_BUDGET


# ============================================================
# 카테고리
# ============================================================


def category_lines(names: Sequence[str]) -> Iterator[str]:
    if not names:
        yield messages.MSG_NO_CATEGORIES_LISTED
        return
    for name in names:
        yield messages.FMT_CATEGORY_ITEM.format(name=name)


# ============================================================
# 가져오기 결과
# ============================================================


def import_result_line(report: ImportReport, mode: str) -> str:
    return messages.MSG_IMPORT_DONE.format(
        mode=mode,
        imported=report.imported,
        duplicated=report.duplicated,
        skipped=report.skipped,
    )


def import_problem_lines(report: ImportReport) -> List[str]:
    """건너뛴 줄의 사유 — 결과가 아니라 진단이므로 호출자가 stderr 로 보낸다.

    오류와 중복을 따로 보여 준다. 사용자가 해야 할 일이 다르기 때문이다
    (오류는 CSV 를 고쳐야 하고, 중복은 아무것도 안 해도 된다).
    """
    lines: List[str] = []
    if report.errors:
        lines.append(messages.MSG_IMPORT_ERROR_HEADER)
        lines.extend(messages.FMT_IMPORT_ERROR_ITEM.format(error=e) for e in report.errors)
    if report.duplicate_notes:
        lines.extend(messages.FMT_IMPORT_ERROR_ITEM.format(error=d) for d in report.duplicate_notes)
        lines.append(messages.MSG_IMPORT_DUPLICATE_HINT)
    return lines
