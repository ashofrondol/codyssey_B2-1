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

from collections.abc import Iterable, Iterator, Sequence

from ..domain import config as domain_config
from ..domain.entities import Budget, Transaction
from ..domain.results import ImportReport, MonthlySummary
from . import messages

# ============================================================
# 거래 표
# ============================================================


#: ``FMT_TX_LINE`` 이 ``{id}`` 에만 폭을 주지 못하므로(값 객체에 ``__format__`` 이
#: 없다) 머리글의 ``id`` 칸만 여기서 채운다. 숫자 9 를 손으로 적지 않고 id 포맷에서
#: **계산해** 온다 — 자릿수를 늘리는 날 머리글이 저절로 따라오게 하려는 것이다.
_TX_ID_WIDTH = len(domain_config.TX_ID_FORMAT.format(0))


def _header_line() -> str:
    """표의 머리글 — 본문과 **같은 템플릿**으로 찍는다.

    따로 쓴 문자열을 두면 폭이 두 곳에 적히고, 둘은 언젠가 어긋난다. 그때 깨지는
    것은 프로그램이 아니라 화면이라 아무도 실패로 알려 주지 않는다.
    """
    cells = dict(messages.TX_HEADERS)
    cells["id"] = cells["id"].ljust(_TX_ID_WIDTH)
    return messages.FMT_TX_LINE.format(**cells)


def _rule_line(header: str) -> str:
    """구분선 — 머리글 줄을 글자 단위로 바꿔 만든다.

    폭을 다시 세지 않고 이미 완성된 줄을 훑기 때문에, 열을 늘리거나 폭을 고쳐도
    구분선이 뒤처질 수 없다. 파이프 자리만 ``+`` 로 남겨 열 경계가 보이게 한다.
    """
    return "".join(
        messages.TX_RULE_JOINT if ch == "|" else messages.TX_RULE_CHAR for ch in header
    )


def tx_line(tx: Transaction) -> str:
    return messages.FMT_TX_LINE.format(
        id=tx.id,
        date=tx.date,
        type=tx.type,
        category=tx.category,
        amount=tx.amount,
        memo=tx.memo,
    )


def tx_table(rows: Iterable[Transaction], limit: int | None = None) -> Iterator[str]:
    """거래 표를 줄 단위로 yield 한다 — 비어 있으면 안내 한 줄.

    제너레이터인 이유: 상류(``stream_sorted``)가 제너레이터이므로 여기서 리스트로
    모으면 스트리밍이 끊긴다.

    ``limit`` 은 **표시 한도**일 뿐 메모리 한도가 아니다. 여기서 ``break`` 해도 상류가
    이미 만들어 둔 것은 줄지 않는다(정렬은 전부 훑어야 끝난다). 메모리를 잡는 것은
    같은 ``limit`` 을 받은 ``TransactionService.stream_sorted`` 쪽이다.

    머리글은 **첫 행을 실제로 받은 뒤에** 낸다. 미리 내면 결과가 없을 때 머리글만
    덩그러니 남아 "(데이터 없음)" 과 모순되는 화면이 되고, 표를 파이프로 넘겨 세는
    쪽도 빈 결과와 한 건을 구분하지 못한다. 행을 하나도 못 받은 경우에만 안내 한 줄이
    나가는 성질은 그대로다.
    """
    count = 0
    for tx in rows:
        if limit is not None and count >= limit:
            break
        if count == 0:
            header = _header_line()
            yield header
            yield _rule_line(header)
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
# 예산
# ============================================================


def budget_lines(month: str, budget: Budget | None) -> Iterator[str]:
    """``budget get`` 한 건 — 설정돼 있지 않으면 그렇다고 말한다.

    ``month`` 를 따로 받는 이유: 예산이 없으면 물어볼 객체도 없는데, 사용자가 알아야
    할 것은 "어느 달이 비어 있는가"이기 때문이다.
    """
    if budget is None:
        yield messages.MSG_BUDGET_NOT_SET.format(month=month)
        return
    yield messages.MSG_BUDGET_FOUND.format(month=budget.month, amount=budget.amount)


def budget_table(budgets: Sequence[Budget]) -> Iterator[str]:
    """``budget list`` — 거래 표와 같은 머리글·구분선 규칙을 쓴다."""
    if not budgets:
        yield messages.MSG_NO_BUDGETS
        return
    header = messages.FMT_BUDGET_LINE.format(**messages.BUDGET_HEADERS)
    yield header
    yield _rule_line(header)
    for budget in budgets:
        yield messages.FMT_BUDGET_LINE.format(month=budget.month, amount=budget.amount)


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


def import_problem_lines(report: ImportReport) -> list[str]:
    """건너뛴 줄의 사유 — 결과가 아니라 진단이므로 호출자가 stderr 로 보낸다.

    오류와 중복을 따로 보여 준다. 사용자가 해야 할 일이 다르기 때문이다
    (오류는 CSV 를 고쳐야 하고, 중복은 아무것도 안 해도 된다).

    **문장을 만드는 것이 여기로 왔다.** 이전에는 서비스가 ``"line 3: ..."`` 까지
    완성해 넘겼다. 지금 서비스가 넘기는 것은 ``(줄번호, 사유)`` 뿐이고, 그것을
    어떤 문장으로 보여 줄지는 화면의 결정이다.
    """
    lines: list[str] = []
    if report.new_categories:
        # 마스터 데이터가 늘어난 것은 사용자가 알아야 할 부수 효과다
        # (`--auto-category` 를 명시했을 때만 일어난다).
        lines.append(
            messages.MSG_IMPORT_NEW_CATEGORIES.format(
                count=len(report.new_categories), names=", ".join(report.new_categories)
            )
        )
    if report.errors:
        lines.append(messages.MSG_IMPORT_ERROR_HEADER)
        lines.extend(
            messages.FMT_IMPORT_ERROR_ITEM.format(lineno=e.lineno, reason=e.reason)
            for e in report.errors
        )
    if report.duplicates:
        lines.extend(
            messages.FMT_IMPORT_DUPLICATE_ITEM.format(lineno=d.lineno, tx_id=d.tx_id)
            for d in report.duplicates
        )
        lines.append(messages.MSG_IMPORT_DUPLICATE_HINT)
    return lines
