"""명령 핸들러 — 인자를 서비스 호출로 번역하고 결과를 프레젠터에 넘긴다.

여기에는 문법 정의(``parser``)도, 화면 문자열 조립(``presenter``)도, 입력 루프
(``prompts``)도 없다. 남은 것은 **오케스트레이션**뿐이라 핸들러 하나가 대개
3~6줄이다.

모든 핸들러가 ``(ctx, args) -> int`` 라는 같은 모양을 갖는다. 그 계약을
``app.Handler`` 타입 별칭이 적어 두고, ``app.HANDLERS`` 가 문자열 키와 짝지어 준다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import config, messages
from ..context import AppContext
from ..domain.entities import TransactionPatch
from ..domain.queries import SearchFilter
from ..errors import AppError
from ..storage.backup import backup_data_dir
from . import output, presenter, prompts
from .error_handler import handle_errors


@handle_errors
def cmd_add(ctx: AppContext, args: argparse.Namespace) -> int:
    if not ctx.cats.list_names():
        # 0 이 아닌 종료 코드로 끝나는 실패 경로 → 진단 채널(stderr).
        output.err(messages.MSG_NO_CATEGORIES)
        return config.EXIT_NO_CATEGORY

    output.out(messages.MSG_ADD_INTERACTIVE)
    entered = prompts.ask_transaction(ctx.cats)
    tx = ctx.tx_service.add(
        date=entered.date,
        type_=entered.type,
        category=entered.category,
        amount=entered.amount,
        memo=entered.memo,
        tags=entered.tags,
    )
    output.out(messages.MSG_SAVED_TX.format(id=tx.id))
    return config.EXIT_OK


@handle_errors
def cmd_list(ctx: AppContext, args: argparse.Namespace) -> int:
    output.out_lines(presenter.tx_table(ctx.tx_service.stream_sorted(), limit=args.limit))
    return config.EXIT_OK


@handle_errors
def cmd_search(ctx: AppContext, args: argparse.Namespace) -> int:
    # 조건 검증·정규화는 SearchFilter.__post_init__ 이 수행한다.
    flt = SearchFilter(
        date_from=args.from_,
        date_to=args.to,
        category=args.category,
        type=args.type,
        query=args.q,
        tag=args.tag,
    )
    output.out_lines(presenter.tx_table(ctx.tx_service.stream_sorted(flt)))
    return config.EXIT_OK


@handle_errors
def cmd_summary(ctx: AppContext, args: argparse.Namespace) -> int:
    summary = ctx.budget_service.monthly_summary(args.month, top_n=args.top)
    output.out_lines(presenter.summary_lines(summary))
    return config.EXIT_OK


@handle_errors
def cmd_budget_set(ctx: AppContext, args: argparse.Namespace) -> int:
    budget = ctx.budget_service.set_budget(args.month, args.amount)
    output.out(messages.MSG_SAVED_BUDGET.format(month=budget.month, amount=budget.amount))
    return config.EXIT_OK


@handle_errors
def cmd_category_add(ctx: AppContext, args: argparse.Namespace) -> int:
    name = prompts.ask_category_name(args.name)
    if ctx.cat_service.add(name):
        output.out(messages.MSG_SAVED_CATEGORY.format(name=name))
    else:
        output.out(messages.MSG_CATEGORY_EXISTS.format(name=name))
    return config.EXIT_OK


@handle_errors
def cmd_category_list(ctx: AppContext, args: argparse.Namespace) -> int:
    output.out_lines(presenter.category_lines(ctx.cat_service.list_names()))
    return config.EXIT_OK


@handle_errors
def cmd_category_remove(ctx: AppContext, args: argparse.Namespace) -> int:
    name = (args.name or "").strip()
    if not name:
        raise AppError(messages.ERR_NAME_REQUIRED, hint=messages.HINT_CATEGORY_REMOVE)
    reassigned = ctx.cat_service.remove(name, replace_with=args.replace_with)
    if reassigned:
        output.out(
            messages.MSG_CATEGORY_REMOVED_REASSIGNED.format(
                name=name, count=reassigned, replace_with=args.replace_with
            )
        )
    else:
        output.out(messages.MSG_CATEGORY_REMOVED.format(name=name))
    return config.EXIT_OK


@handle_errors
def cmd_update(ctx: AppContext, args: argparse.Namespace) -> int:
    # 값 검증은 Transaction.__post_init__ 이 수행하므로 여기서는 조립만 한다.
    patch = TransactionPatch(
        date=args.date,
        type=args.type,
        category=args.category,
        amount=args.amount,
        memo=args.memo,
        tags=args.tags,
    )
    if patch.is_empty:
        raise AppError(messages.ERR_NO_UPDATE_FIELDS, hint=messages.HINT_UPDATE_FIELDS)

    updated = ctx.tx_service.update(args.id, patch)
    output.out(messages.MSG_UPDATED_TX.format(id=updated.id))
    output.out(presenter.tx_line(updated))
    return config.EXIT_OK


@handle_errors
def cmd_delete(ctx: AppContext, args: argparse.Namespace) -> int:
    ctx.tx_service.delete(args.id)
    output.out(messages.MSG_DELETED_TX.format(id=args.id))
    return config.EXIT_OK


@handle_errors
def cmd_export(ctx: AppContext, args: argparse.Namespace) -> int:
    flt = _export_filter(args)
    count = ctx.io_service.export_csv(Path(args.out), flt, include_id=args.include_id)
    output.out(messages.MSG_EXPORT_DONE.format(out=args.out, count=count))
    return config.EXIT_OK


def _export_filter(args: argparse.Namespace) -> SearchFilter:
    """기간 조건은 필수 — ``--month`` 또는 ``--from``/``--to`` 중 하나."""
    if args.month:
        return SearchFilter.for_month(args.month)
    if args.from_ and args.to:
        return SearchFilter(date_from=args.from_, date_to=args.to)
    raise AppError(messages.ERR_EXPORT_PERIOD_REQUIRED, hint=messages.HINT_EXPORT_PERIOD)


@handle_errors
def cmd_import(ctx: AppContext, args: argparse.Namespace) -> int:
    mode = messages.MODE_ATOMIC if args.atomic else messages.MODE_PARTIAL
    report = ctx.io_service.import_csv(
        Path(args.from_), atomic=args.atomic, on_duplicate=args.on_duplicate
    )
    # 요약 한 줄은 결과(stdout), 건너뛴 줄의 사유는 진단(stderr)이다.
    output.out(presenter.import_result_line(report, mode))
    output.err_lines(presenter.import_problem_lines(report))
    return config.EXIT_OK


@handle_errors
def cmd_backup(ctx: AppContext, args: argparse.Namespace) -> int:
    dest = backup_data_dir(ctx.data_dir)
    output.out(messages.MSG_BACKUP_DONE.format(dest=dest))
    return config.EXIT_OK
