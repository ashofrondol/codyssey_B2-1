"""CLI 계층의 조립부 — 명령 핸들러와 진입점.

이 파일에는 문법 정의(``parser``)도, 화면 문자열 조립(``presenter``)도, 입력 루프
(``prompts``)도 없다. 남은 것은 **오케스트레이션**뿐이다: 인자를 서비스 호출로
번역하고, 결과를 프레젠터에 넘기고, 채널을 골라 내보낸다. 핸들러 하나가 대개
3~6줄인 것이 그 증거다.

## 명령 → 핸들러 대응

``parser`` 가 남긴 문자열 키(``"category.add"``)를 ``HANDLERS`` 가 함수로 바꾼다.
파서가 함수 객체를 들고 있던 이전 방식과 달리 두 모듈이 서로를 import 하지 않으므로
순환이 없고, 하위 명령마다 핸들러가 하나씩 대응해 ``if/elif`` 분기가 사라졌다.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

from . import config, messages, output, parser as parser_module, presenter, prompts
from .error_handler import handle_errors
from .errors import AppError
from .models import SearchFilter, TransactionPatch
from .repository import BudgetStore, CategoryStore, TransactionRepository, backup_data_dir
from .services import (
    BudgetService,
    CategoryService,
    ImportExportService,
    TransactionService,
)


# ============================================================
# 합성 루트
# ============================================================


class AppContext:
    """저장소/서비스를 한 번에 조립해 핸들러로 전달한다.

    생성자는 **객체만 만든다.** 디스크를 건드리는 것은 ``prepare()`` 의 일이다.
    이전에는 저장소 생성자가 mkdir·touch·기본 카테고리 시딩까지 해서, 핸들러마다
    ``AppContext(...)`` 를 새로 만드는 것만으로 부작용이 10번 일어났고 오타 난
    ``--data-dir`` 도 조용히 폴더가 생겼다. 지금은 ``main()`` 이 한 번만 준비한다.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.txs = TransactionRepository(self.data_dir)
        self.cats = CategoryStore(self.data_dir)
        self.budgets = BudgetStore(self.data_dir)
        self.tx_service = TransactionService(self.txs, self.cats)
        self.cat_service = CategoryService(self.cats, self.txs)
        self.budget_service = BudgetService(self.txs, self.budgets)
        self.io_service = ImportExportService(self.txs, self.cats)

    def prepare(self) -> None:
        """데이터 폴더와 파일을 준비한다 — 명령 실행 전 한 번만."""
        self.txs.ensure_ready()
        self.budgets.ensure_ready()
        self.cats.ensure_ready()
        self.cats.seed_defaults()


# ============================================================
# 명령 핸들러
# ============================================================


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


# ============================================================
# 명령 레지스트리
# ============================================================

Handler = Callable[[AppContext, argparse.Namespace], int]

HANDLERS: Dict[str, Handler] = {
    "add": cmd_add,
    "list": cmd_list,
    "search": cmd_search,
    "summary": cmd_summary,
    "budget.set": cmd_budget_set,
    "category.add": cmd_category_add,
    "category.list": cmd_category_list,
    "category.remove": cmd_category_remove,
    "update": cmd_update,
    "delete": cmd_delete,
    "export": cmd_export,
    "import": cmd_import,
    "backup": cmd_backup,
}


# ============================================================
# 진입점
# ============================================================


def _silence_broken_pipe() -> None:
    """하류 파이프(``list | head``)가 먼저 닫혔을 때 남은 출력을 os.devnull 로 돌려,
    인터프리터 종료 시 BrokenPipeError 재발과 'Exception ignored' 출력을 막는다
    (파이썬 공식 권장 레시피)."""
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
    except OSError:
        pass


def main(argv: Optional[List[str]] = None) -> int:
    try:
        args = parser_module.build_parser().parse_args(argv)
        # 로거에 핸들러를 붙이는 유일한 지점. 이 호출이 없으면 handle_errors 가
        # exc_info=True 로 보존한 스택트레이스가 아무 데도 출력되지 않는다.
        output.setup_logging(getattr(args, "debug", False))

        ctx = AppContext(Path(args.data_dir))
        if args.needs_storage:
            ctx.prepare()
        return HANDLERS[args.handler](ctx, args)
    except BrokenPipeError:
        # 예: `budget_app list | head` — head 가 먼저 닫음. 오류가 아니므로 조용히 종료.
        _silence_broken_pipe()
        return config.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
