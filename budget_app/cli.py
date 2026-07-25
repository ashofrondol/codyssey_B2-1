"""CLI 진입점 — argparse 기반 명령 파싱과 각 핸들러.

규칙:
- 모든 옵션은 리눅스 표준 '-' 로 통일 (argparse 기본).
- 핸들러는 @handle_errors 로 감싸 스택트레이스 대신 사용자 친화 메시지를 출력한다.
- add 등은 대화형 입력을 기본으로, 옵션 인자는 search/list/summary/export/import/delete/update 에서 사용한다.
"""

from __future__ import annotations

import argparse
import calendar
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from . import config
from .decorators import AppError, handle_errors
from .models import Budget, Transaction, ValidationError
from .repository import BudgetStore, CategoryStore, TransactionRepository
from .services import (
    BudgetService,
    CategoryService,
    ImportExportService,
    SearchFilter,
    TransactionService,
    backup_data_dir,
)


# ---------- 대화형 입력 헬퍼 ----------


class InputAborted(AppError):
    """대화형 입력이 EOF(Ctrl+D)/스트림 종료로 중단됨.

    handle_errors 가 AppError 로 처리하므로 스택트레이스 없이 깔끔히 종료된다.
    이 예외가 없으면 파이프로 입력을 주다가 EOF 가 나는 순간 `_ask` 가 빈
    문자열을 돌려주고, validator 가 이를 거부하며 while 루프가 영원히 돈다.
    """

    def __init__(self) -> None:
        super().__init__(
            config.ERR_INPUT_ABORTED,
            hint=config.HINT_INPUT_ABORTED,
        )


def _ask(prompt: str) -> str:
    """대화형 한 줄 입력. EOF 는 무한 대기/무한 루프 대신 즉시 중단으로 처리한다."""
    try:
        return input(prompt)
    except EOFError as exc:
        raise InputAborted() from exc


def _ask_until(prompt: str, validator):
    """validator(raw) 가 정상값을 반환할 때까지 재입력을 요구한다.

    - EOF → InputAborted 로 즉시 종료(무한 루프 방지).
    - 유효하지 않은 값이 계속 들어오면 MAX_INPUT_RETRIES 회에서 중단한다.
    """
    for _ in range(config.MAX_INPUT_RETRIES):
        raw = _ask(prompt)
        try:
            return validator(raw)
        except ValidationError as exc:
            print(config.MSG_ERROR_LINE.format(msg=exc))
            print(config.MSG_HINT_RETRY)
    raise AppError(
        config.ERR_MAX_RETRIES,
        hint=config.HINT_MAX_RETRIES,
    )


def _make_category_validator(cats):
    """등록된 카테고리만 통과시키는 validator (미등록이면 ValidationError → 재입력)."""

    def _validate(raw: str) -> str:
        name = (raw or "").strip()
        if cats.exists(name):
            return name
        available = ", ".join(cats.list_names())
        raise ValidationError(
            config.ERR_CATEGORY_NOT_REGISTERED_AVAILABLE.format(name=name, available=available)
        )

    return _validate


# ---------- 기간 헬퍼 ----------


def _month_bounds(month: str) -> tuple[str, str]:
    """'YYYY-MM' → ('YYYY-MM-01', 'YYYY-MM-<그 달의 말일>').

    이전 코드는 모든 달을 31일로 가정해 2월/30일 달에서 검증이 실패했다.
    calendar 로 실제 말일을 구해 그 문제를 없앤다. 형식 오류는 AppError.
    """
    try:
        normalized = Budget.validate_month(month)  # '유효한 월' 규칙은 한 곳(모델)에만 둔다.
    except ValidationError as exc:
        raise AppError(config.ERR_MONTH_ARG_INVALID) from exc
    dt = datetime.strptime(normalized, config.MONTH_FORMAT)
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return f"{dt:%Y-%m}-01", f"{dt:%Y-%m}-{last_day:02d}"


# ---------- 출력 포맷 ----------


def _fmt_tx_line(tx: Transaction) -> str:
    memo = tx.memo or ""
    return config.FMT_TX_LINE.format(
        id=tx.id, date=tx.date, type=tx.type, category=tx.category, amount=tx.amount, memo=memo
    )


def _print_tx_table(rows, limit: Optional[int] = None) -> int:
    count = 0
    for tx in rows:
        if limit is not None and count >= limit:
            break
        print(_fmt_tx_line(tx))
        count += 1
    if count == 0:
        print(config.MSG_NO_DATA)
    return count


# ---------- 컨텍스트 빌더 ----------


class AppContext:
    """저장소/서비스를 한 번에 만들어 핸들러로 전달."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.txs = TransactionRepository(self.data_dir)
        self.cats = CategoryStore(self.data_dir, seed_defaults=True)
        self.budgets = BudgetStore(self.data_dir)
        self.tx_service = TransactionService(self.txs, self.cats)
        self.cat_service = CategoryService(self.cats, self.txs)
        self.budget_service = BudgetService(self.txs, self.budgets)
        self.io_service = ImportExportService(self.txs, self.cats)


# ---------- 명령 핸들러 ----------


@handle_errors
def cmd_add(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    if not ctx.cats.list_names():
        print(config.MSG_NO_CATEGORIES)
        return config.EXIT_NO_CATEGORY
    print(config.MSG_ADD_INTERACTIVE)
    date = _ask_until(config.PROMPT_DATE, Transaction.validate_date)
    type_ = _ask_until(config.PROMPT_TYPE, Transaction.validate_type)
    category = _ask_until(config.PROMPT_CATEGORY, _make_category_validator(ctx.cats))
    amount = _ask_until(config.PROMPT_AMOUNT, Transaction.validate_amount)
    memo = _ask(config.PROMPT_MEMO).strip()
    tags_raw = _ask(config.PROMPT_TAGS).strip()
    tags = Transaction.parse_tags(tags_raw)

    tx = ctx.tx_service.add(date=date, type_=type_, category=category, amount=amount, memo=memo, tags=tags)
    print(config.MSG_SAVED_TX.format(id=tx.id))
    return 0


@handle_errors
def cmd_list(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    _print_tx_table(ctx.tx_service.stream_sorted(), limit=args.limit)
    return 0


@handle_errors
def cmd_search(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    flt = SearchFilter(
        date_from=Transaction.validate_date(args.from_) if args.from_ else None,
        date_to=Transaction.validate_date(args.to) if args.to else None,
        category=args.category,
        type=args.type,  # argparse choices 가 이미 값을 제한하므로 재검증 불필요.
        query=args.q,
        tag=args.tag,
    )
    _print_tx_table(ctx.tx_service.stream_sorted(flt))
    return 0


@handle_errors
def cmd_summary(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    result = ctx.budget_service.monthly_summary(args.month, top_n=args.top)
    if not result["has_data"] and result["budget"] is None:
        print(config.MSG_SUMMARY_NO_DATA.format(month=result["month"]))
        return 0

    print(config.MSG_SUMMARY_INCOME.format(income=result["income"]))
    print(config.MSG_SUMMARY_EXPENSE.format(expense=result["expense"]))
    print(config.MSG_SUMMARY_BALANCE.format(balance=result["balance"]))

    budget = result["budget"]
    if budget is not None:
        usage = result["usage_pct"]
        usage_str = config.FMT_USAGE_PCT.format(usage=usage) if usage is not None else config.MSG_USAGE_NA
        print(config.MSG_SUMMARY_BUDGET.format(amount=budget.amount, usage=usage_str))
        if result["over_budget"]:
            print(config.MSG_OVER_BUDGET)

    if result["top_expense"]:
        n = len(result["top_expense"])
        print(config.MSG_TOP_EXPENSE_HEADER.format(n=n))
        for i, (cat, amt) in enumerate(result["top_expense"], start=1):
            print(config.FMT_TOP_EXPENSE_ITEM.format(rank=i, category=cat, amount=amt))
    return 0


@handle_errors
def cmd_budget(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    if args.budget_cmd == "set":
        b = ctx.budget_service.set_budget(args.month, args.amount)
        print(config.MSG_SAVED_BUDGET.format(month=b.month, amount=b.amount))
        return 0
    raise AppError(config.ERR_UNKNOWN_BUDGET_CMD, hint=config.HINT_BUDGET_USAGE)


@handle_errors
def cmd_category(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    sub = args.cat_cmd
    if sub == "add":
        name = (args.name or _ask(config.PROMPT_CATEGORY_NAME)).strip()
        if ctx.cat_service.add(name):
            print(config.MSG_SAVED_CATEGORY.format(name=name))
        else:
            print(config.MSG_CATEGORY_EXISTS.format(name=name))
        return 0
    if sub == "list":
        names = ctx.cat_service.list_names()
        if not names:
            print(config.MSG_NO_CATEGORIES_LISTED)
            return 0
        for n in names:
            print(config.FMT_CATEGORY_ITEM.format(name=n))
        return 0
    if sub == "remove":
        name = (args.name or "").strip()
        if not name:
            raise AppError(config.ERR_NAME_REQUIRED, hint=config.HINT_CATEGORY_REMOVE)
        reassigned = ctx.cat_service.remove(name, replace_with=args.replace_with)
        if reassigned:
            print(
                config.MSG_CATEGORY_REMOVED_REASSIGNED.format(
                    name=name, count=reassigned, replace_with=args.replace_with
                )
            )
        else:
            print(config.MSG_CATEGORY_REMOVED.format(name=name))
        return 0
    raise AppError(config.ERR_UNKNOWN_CATEGORY_CMD, hint=config.HINT_CATEGORY_SUBCMD)


@handle_errors
def cmd_update(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    changes = {}
    if args.date is not None:
        changes["date"] = Transaction.validate_date(args.date)
    if args.type is not None:
        changes["type"] = Transaction.validate_type(args.type)
    if args.category is not None:
        changes["category"] = args.category
    if args.amount is not None:
        changes["amount"] = Transaction.validate_amount(args.amount)
    if args.memo is not None:
        changes["memo"] = args.memo
    if args.tags is not None:
        changes["tags"] = Transaction.parse_tags(args.tags)
    if not changes:
        raise AppError(
            config.ERR_NO_UPDATE_FIELDS,
            hint=config.HINT_UPDATE_FIELDS,
        )
    updated = ctx.tx_service.update(args.id, changes)
    print(config.MSG_UPDATED_TX.format(id=updated.id))
    print(_fmt_tx_line(updated))
    return 0


@handle_errors
def cmd_delete(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    ctx.tx_service.delete(args.id)
    print(config.MSG_DELETED_TX.format(id=args.id))
    return 0


@handle_errors
def cmd_export(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    # 기간 조건은 필수 — month 또는 from/to 중 하나
    date_from = args.from_
    date_to = args.to
    if args.month:
        date_from, date_to = _month_bounds(args.month)
    elif not (date_from and date_to):
        raise AppError(
            config.ERR_EXPORT_PERIOD_REQUIRED,
            hint=config.HINT_EXPORT_PERIOD,
        )

    if date_from:
        Transaction.validate_date(date_from)
    if date_to:
        Transaction.validate_date(date_to)

    flt = SearchFilter(date_from=date_from, date_to=date_to)
    count = ctx.io_service.export_csv(Path(args.out), flt)
    print(config.MSG_EXPORT_DONE.format(out=args.out, count=count))
    return 0


@handle_errors
def cmd_import(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    mode = config.MODE_ATOMIC if args.atomic else config.MODE_PARTIAL
    imported, skipped, errors = ctx.io_service.import_csv(Path(args.from_), atomic=args.atomic)
    print(config.MSG_IMPORT_DONE.format(mode=mode, imported=imported, skipped=skipped))
    if errors:
        print(config.MSG_IMPORT_ERROR_HEADER)
        for e in errors:
            print(config.FMT_IMPORT_ERROR_ITEM.format(error=e))
    return 0


@handle_errors
def cmd_backup(args: argparse.Namespace) -> int:
    dest = backup_data_dir(Path(args.data_dir))
    print(config.MSG_BACKUP_DONE.format(dest=dest))
    return 0


# ---------- argparse 빌더 ----------


def _add_data_dir(p: argparse.ArgumentParser) -> None:
    p.add_argument("--data-dir", dest="data_dir", default=config.DEFAULT_DATA_DIR, help="데이터 저장 폴더 (기본: ./data)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=config.PROG_NAME,
        description=config.PROG_DESCRIPTION,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="거래 추가 (대화형)")
    _add_data_dir(p_add)
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = sub.add_parser("list", help="최신순 거래 목록")
    _add_data_dir(p_list)
    p_list.add_argument("--limit", type=int, default=config.DEFAULT_LIST_LIMIT, help="표시 건수 (기본 20)")
    p_list.set_defaults(func=cmd_list)

    # search
    p_search = sub.add_parser("search", help="조건 검색")
    _add_data_dir(p_search)
    p_search.add_argument("--from", dest="from_", help="시작일 YYYY-MM-DD")
    p_search.add_argument("--to", dest="to", help="종료일 YYYY-MM-DD")
    p_search.add_argument("--category", help="카테고리")
    p_search.add_argument("--type", choices=list(config.VALID_TYPES), help="타입")
    p_search.add_argument("--q", help="메모 키워드 부분 일치")
    p_search.add_argument("--tag", help="태그 정확 일치")
    p_search.set_defaults(func=cmd_search)

    # summary
    p_sum = sub.add_parser("summary", help="월별 요약")
    _add_data_dir(p_sum)
    p_sum.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    p_sum.add_argument("--top", type=int, default=config.DEFAULT_TOP_N, help="지출 TOP N (기본 5)")
    p_sum.set_defaults(func=cmd_summary)

    # budget
    p_bud = sub.add_parser("budget", help="예산 설정")
    _add_data_dir(p_bud)
    bud_sub = p_bud.add_subparsers(dest="budget_cmd", required=True)
    p_bset = bud_sub.add_parser("set", help="월 예산 설정")
    p_bset.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    p_bset.add_argument("--amount", required=True, type=int, help="예산 금액(양수)")
    p_bset.set_defaults(func=cmd_budget)
    # NOTE: budget 의 모든 하위 명령은 한 핸들러에서 처리한다.
    # data_dir 는 상위 p_bud 에 달아두고, 하위 파서가 같은 namespace 를 공유한다.

    # category
    p_cat = sub.add_parser("category", help="카테고리 관리")
    _add_data_dir(p_cat)
    cat_sub = p_cat.add_subparsers(dest="cat_cmd", required=True)
    p_cadd = cat_sub.add_parser("add", help="카테고리 추가")
    p_cadd.add_argument("--name", help="카테고리명 (생략 시 대화형)")
    p_cadd.set_defaults(func=cmd_category)
    p_clist = cat_sub.add_parser("list", help="카테고리 목록")
    p_clist.set_defaults(func=cmd_category)
    p_crem = cat_sub.add_parser("remove", help="카테고리 삭제")
    p_crem.add_argument("--name", required=True, help="삭제할 카테고리")
    p_crem.add_argument("--replace-with", dest="replace_with", help="사용 중일 때 대체할 카테고리")
    p_crem.set_defaults(func=cmd_category)

    # update (옵션 방식 고정)
    p_upd = sub.add_parser("update", help="거래 수정 (옵션 방식)")
    _add_data_dir(p_upd)
    p_upd.add_argument("--id", required=True, help="수정 대상 거래 id")
    p_upd.add_argument("--date", help="YYYY-MM-DD")
    p_upd.add_argument("--type", choices=list(config.VALID_TYPES))
    p_upd.add_argument("--category")
    p_upd.add_argument("--amount", type=int)
    p_upd.add_argument("--memo")
    p_upd.add_argument("--tags", help="쉼표로 구분")
    p_upd.set_defaults(func=cmd_update)

    # delete
    p_del = sub.add_parser("delete", help="거래 삭제")
    _add_data_dir(p_del)
    p_del.add_argument("--id", required=True, help="삭제 대상 거래 id")
    p_del.set_defaults(func=cmd_delete)

    # export
    p_exp = sub.add_parser("export", help="CSV 내보내기")
    _add_data_dir(p_exp)
    p_exp.add_argument("--out", required=True, help="출력 CSV 경로")
    p_exp.add_argument("--month", help="대상 월 YYYY-MM")
    p_exp.add_argument("--from", dest="from_", help="시작일 YYYY-MM-DD")
    p_exp.add_argument("--to", dest="to", help="종료일 YYYY-MM-DD")
    p_exp.set_defaults(func=cmd_export)

    # import
    p_imp = sub.add_parser("import", help="CSV 가져오기")
    _add_data_dir(p_imp)
    p_imp.add_argument("--from", dest="from_", required=True, help="입력 CSV 경로")
    p_imp.add_argument(
        "--atomic",
        action="store_true",
        help="전수 롤백 모드 — 한 줄이라도 오류면 아무것도 저장하지 않음 (기본: 부분 성공)",
    )
    p_imp.set_defaults(func=cmd_import)

    # backup (보너스)
    p_bak = sub.add_parser("backup", help="데이터 폴더 백업 (보너스)")
    _add_data_dir(p_bak)
    p_bak.set_defaults(func=cmd_backup)

    return parser


def _silence_broken_pipe() -> None:
    """하류 파이프(`list | head`)가 먼저 닫혔을 때 남은 출력을 os.devnull 로 돌려,
    인터프리터 종료 시 BrokenPipeError 재발과 'Exception ignored' 출력을 막는다
    (파이썬 공식 권장 레시피)."""
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
    except OSError:
        pass


def main(argv: Optional[List[str]] = None) -> int:
    try:
        parser = build_parser()
        args = parser.parse_args(argv)
        return args.func(args)
    except BrokenPipeError:
        # 예: `budget_app list | head` — head 가 먼저 닫음. 오류가 아니므로 조용히 종료.
        _silence_broken_pipe()
        return 0


if __name__ == "__main__":
    sys.exit(main())
