"""CLI 진입점 — argparse 기반 명령 파싱과 각 핸들러.

규칙:
- 모든 옵션은 리눅스 표준 '-' 로 통일 (argparse 기본).
- 핸들러는 @handle_errors 로 감싸 스택트레이스 대신 사용자 친화 메시지를 출력한다.
- add 등은 대화형 입력을 기본으로, 옵션 인자는 search/list/summary/export/import/delete/update 에서 사용한다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .decorators import AppError, handle_errors
from .models import Transaction, ValidationError
from .repository import BudgetStore, CategoryStore, TransactionRepository
from .services import (
    BudgetService,
    CategoryService,
    ImportExportService,
    SearchFilter,
    TransactionService,
    backup_data_dir,
)


DEFAULT_DATA_DIR = "./data"


# ---------- 대화형 입력 헬퍼 ----------


def _ask(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        return ""


def _ask_until(prompt: str, validator) -> str:
    """validator(s) 가 정상값을 반환할 때까지 재입력을 요구한다."""
    while True:
        raw = _ask(prompt)
        try:
            return validator(raw)
        except ValidationError as exc:
            print(f"[오류] {exc}")
            print("[힌트] 다시 입력해 주세요.")


# ---------- 출력 포맷 ----------


def _fmt_tx_line(tx: Transaction) -> str:
    memo = tx.memo or ""
    return f"{tx.id} | {tx.date} | {tx.type:<7} | {tx.category} | {tx.amount} | {memo}"


def _print_tx_table(rows, limit: Optional[int] = None) -> int:
    count = 0
    for tx in rows:
        if limit is not None and count >= limit:
            break
        print(_fmt_tx_line(tx))
        count += 1
    if count == 0:
        print("(데이터 없음)")
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
        print("[안내] 등록된 카테고리가 없습니다. 먼저 `category add` 로 추가하세요.")
        return 5
    print("[안내] 거래 추가 - 대화형 입력입니다.")
    date = _ask_until("날짜(YYYY-MM-DD): ", Transaction.validate_date)
    type_ = _ask_until("타입(income/expense): ", Transaction.validate_type)

    while True:
        category = _ask("카테고리: ").strip()
        if ctx.cats.exists(category):
            break
        print(f"[오류] 등록되지 않은 카테고리입니다: {category}")
        print(f"[힌트] 사용 가능: {', '.join(ctx.cats.list_names())}")

    amount = _ask_until("금액(양수): ", Transaction.validate_amount)
    memo = _ask("메모(선택): ").strip()
    tags_raw = _ask("태그(쉼표로 구분, 없으면 엔터): ").strip()
    tags = Transaction.parse_tags(tags_raw)

    tx = ctx.tx_service.add(date=date, type_=type_, category=category, amount=amount, memo=memo, tags=tags)
    print(f"[저장 완료] id={tx.id}")
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
        type=Transaction.validate_type(args.type) if args.type else None,
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
        print(f"{result['month']}: 데이터 없음")
        return 0

    print(f"총 수입: {result['income']}원")
    print(f"총 지출: {result['expense']}원")
    print(f"잔액: {result['balance']}원")

    budget = result["budget"]
    if budget is not None:
        usage = result["usage_pct"]
        usage_str = f"{usage}%" if usage is not None else "N/A"
        print(f"예산: {budget.amount}원 (사용률 {usage_str})")
        if result["over_budget"]:
            print("[경고] 예산을 초과했습니다!")

    if result["top_expense"]:
        n = len(result["top_expense"])
        print(f"\n지출 TOP {n}")
        for i, (cat, amt) in enumerate(result["top_expense"], start=1):
            print(f"{i}) {cat} {amt}원")
    return 0


@handle_errors
def cmd_budget(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    if args.budget_cmd == "set":
        b = ctx.budget_service.set_budget(args.month, args.amount)
        print(f"[저장 완료] {b.month} 예산 {b.amount}원")
        return 0
    raise AppError("알 수 없는 budget 하위 명령입니다.", hint="`budget set --month YYYY-MM --amount 금액`")


@handle_errors
def cmd_category(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    sub = args.cat_cmd
    if sub == "add":
        name = (args.name or _ask("카테고리명: ")).strip()
        if ctx.cat_service.add(name):
            print(f"[저장 완료] category={name}")
        else:
            print(f"[안내] 이미 존재하는 카테고리입니다: {name}")
        return 0
    if sub == "list":
        names = ctx.cat_service.list_names()
        if not names:
            print("(등록된 카테고리 없음)")
            return 0
        for n in names:
            print(f"- {n}")
        return 0
    if sub == "remove":
        name = (args.name or "").strip()
        if not name:
            raise AppError("--name 이 필요합니다.", hint="`category remove --name <카테고리>`")
        reassigned = ctx.cat_service.remove(name, replace_with=args.replace_with)
        if reassigned:
            print(f"[완료] '{name}' 삭제, {reassigned}건을 '{args.replace_with}' 로 재지정했습니다.")
        else:
            print(f"[완료] '{name}' 삭제")
        return 0
    raise AppError("알 수 없는 category 하위 명령입니다.", hint="add | list | remove")


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
            "수정할 필드가 없습니다.",
            hint="--date/--type/--category/--amount/--memo/--tags 중 하나 이상 지정하세요.",
        )
    updated = ctx.tx_service.update(args.id, changes)
    print(f"[수정 완료] id={updated.id}")
    print(_fmt_tx_line(updated))
    return 0


@handle_errors
def cmd_delete(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    ctx.tx_service.delete(args.id)
    print(f"[삭제 완료] id={args.id}")
    return 0


@handle_errors
def cmd_export(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    # 기간 조건은 필수 — month 또는 from/to 중 하나
    date_from = args.from_
    date_to = args.to
    if args.month:
        month = args.month
        # YYYY-MM 검증
        from datetime import datetime as _dt
        try:
            _dt.strptime(month, "%Y-%m")
        except ValueError as exc:
            raise AppError("--month 형식이 올바르지 않습니다 (YYYY-MM).") from exc
        date_from = f"{month}-01"
        # 월의 마지막은 31로 잡아도 문자열 비교상 문제 없음
        date_to = f"{month}-31"
    elif not (date_from and date_to):
        raise AppError(
            "--month 또는 --from/--to 중 하나는 필수입니다.",
            hint="예: `export --out a.csv --month 2024-01`",
        )

    if date_from:
        Transaction.validate_date(date_from)
    if date_to:
        Transaction.validate_date(date_to)

    flt = SearchFilter(date_from=date_from, date_to=date_to)
    count = ctx.io_service.export_csv(Path(args.out), flt)
    print(f"[완료] {args.out} ({count} records)")
    return 0


@handle_errors
def cmd_import(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    mode = "원자(전수 롤백)" if args.atomic else "부분 성공"
    imported, skipped, errors = ctx.io_service.import_csv(Path(args.from_), atomic=args.atomic)
    print(f"[완료] mode={mode}, imported={imported}, skipped={skipped}")
    if errors:
        print("[오류 라인 일부]")
        for e in errors:
            print(f"  - {e}")
    return 0


@handle_errors
def cmd_backup(args: argparse.Namespace) -> int:
    dest = backup_data_dir(Path(args.data_dir))
    print(f"[백업 완료] {dest}")
    return 0


# ---------- argparse 빌더 ----------


def _add_data_dir(p: argparse.ArgumentParser) -> None:
    p.add_argument("--data-dir", dest="data_dir", default=DEFAULT_DATA_DIR, help="데이터 저장 폴더 (기본: ./data)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="파일 기반 가계부 콘솔 프로그램",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="거래 추가 (대화형)")
    _add_data_dir(p_add)
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = sub.add_parser("list", help="최신순 거래 목록")
    _add_data_dir(p_list)
    p_list.add_argument("--limit", type=int, default=20, help="표시 건수 (기본 20)")
    p_list.set_defaults(func=cmd_list)

    # search
    p_search = sub.add_parser("search", help="조건 검색")
    _add_data_dir(p_search)
    p_search.add_argument("--from", dest="from_", help="시작일 YYYY-MM-DD")
    p_search.add_argument("--to", dest="to", help="종료일 YYYY-MM-DD")
    p_search.add_argument("--category", help="카테고리")
    p_search.add_argument("--type", choices=["income", "expense"], help="타입")
    p_search.add_argument("--q", help="메모 키워드 부분 일치")
    p_search.add_argument("--tag", help="태그 정확 일치")
    p_search.set_defaults(func=cmd_search)

    # summary
    p_sum = sub.add_parser("summary", help="월별 요약")
    _add_data_dir(p_sum)
    p_sum.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    p_sum.add_argument("--top", type=int, default=5, help="지출 TOP N (기본 5)")
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
    p_upd.add_argument("--type", choices=["income", "expense"])
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


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
