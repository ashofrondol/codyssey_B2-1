"""명령 핸들러 — 인자를 서비스 호출로 번역하고 결과를 프레젠터에 넘긴다.

여기에는 문법 정의(``parser``)도, 화면 문자열 조립(``presenter``)도, 입력 루프
(``prompts``)도 없다. 남은 것은 **오케스트레이션**뿐이라 핸들러 하나가 대개
3~6줄이다.

모든 핸들러가 ``(ctx, args) -> int`` 라는 같은 모양을 갖는다. 그 계약을
``app.Handler`` 타입 별칭이 적어 두고, ``app.HANDLERS`` 가 문자열 키와 짝지어 준다.

## 예외 처리가 여기 없는 이유

이전에는 함수 13개에 ``@handle_errors`` 가 각각 붙어 있었다. 그런데 정작
``AppContext`` 생성과 ``prepare()`` 는 그 밖에 있어서, ``--data-dir`` 오타 하나로
원시 트레이스백이 터졌다 — **방패가 필요한 자리에만 없었다.**

지금은 ``app._dispatch`` 한 곳에 데코레이터를 씌운다. 정책 적용점이 하나면
"핸들러를 추가할 때 데코레이터를 빠뜨리는" 실수가 성립하지 않는다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..context import AppContext
from ..domain import validators
from ..domain.entities import TransactionPatch
from ..domain.queries import SearchFilter
from ..errors import AppError
from . import config, messages, output, presenter, prompts


def cmd_add(ctx: AppContext, args: argparse.Namespace) -> int:
    if not ctx.cat_service.list_names():
        # 0 이 아닌 종료 코드로 끝나는 실패 경로 → 진단 채널(stderr).
        output.err(messages.MSG_NO_CATEGORIES)
        return config.EXIT_NO_CATEGORY

    output.out(messages.MSG_ADD_INTERACTIVE)
    entered = prompts.ask_transaction(ctx.cat_service)
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


def cmd_list(ctx: AppContext, args: argparse.Namespace) -> int:
    output.out_lines(presenter.tx_table(ctx.tx_service.stream_sorted(), limit=args.limit))
    return config.EXIT_OK


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


def cmd_summary(ctx: AppContext, args: argparse.Namespace) -> int:
    summary = ctx.budget_service.monthly_summary(args.month, top_n=args.top)
    output.out_lines(presenter.summary_lines(summary))
    return config.EXIT_OK


def cmd_budget_set(ctx: AppContext, args: argparse.Namespace) -> int:
    budget = ctx.budget_service.set_budget(args.month, args.amount)
    output.out(messages.MSG_SAVED_BUDGET.format(month=budget.month, amount=budget.amount))
    return config.EXIT_OK


def cmd_category_add(ctx: AppContext, args: argparse.Namespace) -> int:
    name = prompts.ask_category_name(args.name)
    if ctx.cat_service.add(name):
        output.out(messages.MSG_SAVED_CATEGORY.format(name=name))
    else:
        output.out(messages.MSG_CATEGORY_EXISTS.format(name=name))
    return config.EXIT_OK


def cmd_category_list(ctx: AppContext, args: argparse.Namespace) -> int:
    output.out_lines(presenter.category_lines(ctx.cat_service.list_names()))
    return config.EXIT_OK


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


def _build_patch(args: argparse.Namespace) -> TransactionPatch:
    """``--tags "a,b"`` 를 ``["a", "b"]`` 로 바꿔 넣는다 — **타입 계약을 지키기 위해**.

    ``TransactionPatch.tags`` 는 ``Optional[List[str]]`` 로 선언돼 있는데 argparse 가
    주는 것은 쉼표 문자열이다. 지금까지는 ``Transaction.__post_init__`` 의
    ``parse_tags`` 가 뒤에서 우연히 구제해 줘서 동작했지만, **선언된 타입과 실제 값이
    다른** 상태였다. patch 를 저장 전에 읽는 코드가 하나만 생겨도 곧바로 깨진다.

    경계에서 값을 그 타입으로 만들어 넣는 것이 어댑터(핸들러)의 일이다.
    ``--tags ""`` 는 ``[]`` 가 되어 "태그를 모두 지운다"는 뜻이 된다.
    """
    return TransactionPatch(
        date=args.date,
        type=args.type,
        category=args.category,
        amount=args.amount,
        memo=args.memo,
        tags=validators.parse_tags(args.tags) if args.tags is not None else None,
    )


def cmd_update(ctx: AppContext, args: argparse.Namespace) -> int:
    # 값 검증은 Transaction.__post_init__ 이 수행하므로 여기서는 조립만 한다.
    patch = _build_patch(args)
    if patch.is_empty:
        raise AppError(messages.ERR_NO_UPDATE_FIELDS, hint=messages.HINT_UPDATE_FIELDS)

    updated = ctx.tx_service.update(args.id, patch)
    output.out(messages.MSG_UPDATED_TX.format(id=updated.id))
    output.out(presenter.tx_line(updated))
    return config.EXIT_OK


def cmd_delete(ctx: AppContext, args: argparse.Namespace) -> int:
    ctx.tx_service.delete(args.id)
    output.out(messages.MSG_DELETED_TX.format(id=args.id))
    return config.EXIT_OK


def cmd_export(ctx: AppContext, args: argparse.Namespace) -> int:
    flt = _export_filter(args)
    count = ctx.io_service.export_csv(Path(args.out), flt, include_id=args.include_id)
    output.out(messages.MSG_EXPORT_DONE.format(out=args.out, count=count))
    return config.EXIT_OK


def _export_filter(args: argparse.Namespace) -> SearchFilter:
    """기간 조건은 필수 — ``--month`` 또는 ``--from``/``--to`` **중 하나**.

    둘을 함께 주면 오류로 막는다. 이전에는 ``--month`` 를 먼저 검사하고 나머지를
    **조용히 무시**했다. 사용자가 원한 것은 십중팔구 좁은 쪽인데 넓은 한 달이
    나가고, 파일에는 아무 표시도 남지 않는다. 무시할 바에는 묻는 편이 낫다.
    """
    if args.month and (args.from_ or args.to):
        raise AppError(messages.ERR_EXPORT_PERIOD_CONFLICT, hint=messages.HINT_EXPORT_PERIOD)
    if args.month:
        return SearchFilter.for_month(args.month)
    if args.from_ and args.to:
        return SearchFilter(date_from=args.from_, date_to=args.to)
    raise AppError(messages.ERR_EXPORT_PERIOD_REQUIRED, hint=messages.HINT_EXPORT_PERIOD)


def cmd_import(ctx: AppContext, args: argparse.Namespace) -> int:
    mode = messages.MODE_ATOMIC if args.atomic else messages.MODE_PARTIAL
    report = ctx.io_service.import_csv(
        Path(args.from_), atomic=args.atomic, on_duplicate=args.on_duplicate
    )
    # 요약 한 줄은 결과(stdout), 건너뛴 줄의 사유는 진단(stderr)이다.
    output.out(presenter.import_result_line(report, mode))
    output.err_lines(presenter.import_problem_lines(report))
    return config.EXIT_OK


def cmd_backup(ctx: AppContext, args: argparse.Namespace) -> int:
    dest = ctx.backup_service.create()
    output.out(messages.MSG_BACKUP_DONE.format(dest=dest))
    return config.EXIT_OK
