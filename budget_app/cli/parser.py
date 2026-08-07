"""argparse 구성 — 명령줄 문법 정의만 담당한다.

## 왜 핸들러 함수 대신 문자열 키를 두는가

이전에는 각 서브파서가 ``set_defaults(func=cmd_category)`` 로 **함수 객체**를 직접
들고 있었다. 그러면 파서 정의와 핸들러 구현이 같은 파일에 있어야 하거나
(``cli.py`` 512줄의 한 원인), 나누면 순환 import 가 생긴다.

지금은 파서가 ``handler="category.add"`` 라는 **문자열 키**만 남기고, 키→함수 대응은
``cli.py`` 의 레지스트리가 갖는다. 파서는 핸들러를 모르고 핸들러는 파서를 모른다.

부수 효과로 죽은 코드가 사라졌다. 예전에는 ``category`` 의 세 하위 명령이 한
핸들러로 들어와 ``if sub == "add" ... elif ...`` 로 갈라졌고, 맨 끝에 "알 수 없는
하위 명령" 분기가 있었다. ``add_subparsers(required=True)`` 가 값을 이미 세 개로
제한하므로 **그 분기는 도달할 수 없는 코드**였다. 하위 명령마다 키를 따로 주면
분기 자체가 없어진다.
"""

from __future__ import annotations

import argparse

from . import config, messages
from ..services import config as services_config
from ..domain import config as domain_config

DEBUG_HELP = "디버그 로그 활성화 — 예기치 못한 오류의 스택트레이스를 stderr 로 출력"


DATA_DIR_HELP = "데이터 저장 폴더 (기본: ./data)"


def positive_int(raw: str) -> int:
    """1 이상의 정수만 통과시키는 argparse ``type``.

    ``--limit 0`` 은 "데이터가 있는데 (데이터 없음) 이라고 출력"되는 원인이었다.
    프레젠터는 "한 줄도 못 냈다"와 "0개만 내라고 해서 안 냈다"를 구분할 수단이
    없고, 구분하게 만들어 봐야 **0건을 보여 달라는 요청 자체가 의미 없다.**
    값이 규칙을 어겼으면 실행하지 말고 거절하는 편이 맞다.

    ``ArgumentTypeError`` 를 쓰면 argparse 가 usage 와 함께 종료 코드 2 로 끝낸다 —
    다른 인자 오류와 같은 경로다.
    """
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(messages.ERR_ARG_NOT_INT.format(value=raw)) from exc
    if value < 1:
        raise argparse.ArgumentTypeError(messages.ERR_ARG_NOT_POSITIVE.format(value=raw))
    return value


def _add_shared_options(p: argparse.ArgumentParser) -> None:
    """모든 하위 명령이 공유하는 옵션 — 데이터 폴더와 디버그 스위치.

    둘 다 **최상위 파서에도** 붙어 있어 ``budget_app --data-dir X list`` 와
    ``budget_app list --data-dir X`` 가 모두 동작한다. 2단 명령의 말단 파서
    (``category list``)에도 같은 것을 달아 ``category list --data-dir X`` 까지
    받는다 — argparse 는 하위 명령 뒤의 인자를 말단 파서에게 넘기기 때문이다.

    **기본값이 ``argparse.SUPPRESS`` 인 것이 핵심이다.** 실제 기본값은 최상위 파서
    한 곳에만 두고, 아래 파서들은 "값을 받으면 덮어쓰고 안 받으면 아무것도 안
    한다". 여기에 ``default=DEFAULT_DATA_DIR`` 를 주면 하위 파서가 앞에서 읽어 둔
    값을 기본값으로 되돌려 버린다(``--debug`` 도 False 로 꺼진다).

    이전에는 이 함수가 ``_add_common_options``/``_add_leaf_options`` 둘로 나뉘어
    있었고, 차이는 ``--data-dir`` 의 기본값 하나였다. 그 기본값을 최상위로 올리자
    두 함수가 같아져 하나로 합쳤다.
    """
    p.add_argument("--data-dir", dest="data_dir", default=argparse.SUPPRESS, help=DATA_DIR_HELP)
    p.add_argument("--debug", action="store_true", default=argparse.SUPPRESS, help=DEBUG_HELP)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=config.PROG_NAME,
        description=messages.PROG_DESCRIPTION,
    )
    # 실제 기본값은 여기 한 곳에만 있다 — 아래 파서들은 전부 SUPPRESS 다.
    parser.add_argument("--debug", action="store_true", help=DEBUG_HELP)
    parser.add_argument(
        "--data-dir", dest="data_dir", default=config.DEFAULT_DATA_DIR, help=DATA_DIR_HELP
    )
    # 저장소 준비가 필요한지의 기본값. backup 만 끈다(없는 폴더를 만들어 버리면
    # "백업할 데이터가 없다"는 오류 대신 빈 백업이 생긴다).
    parser.set_defaults(needs_storage=True)
    sub = parser.add_subparsers(dest="command", required=True)

    _add_add(sub)
    _add_list(sub)
    _add_search(sub)
    _add_summary(sub)
    _add_budget(sub)
    _add_category(sub)
    _add_update(sub)
    _add_delete(sub)
    _add_export(sub)
    _add_import(sub)
    _add_backup(sub)
    return parser


def _add_add(sub) -> None:
    p = sub.add_parser("add", help="거래 추가 (대화형)")
    _add_shared_options(p)
    p.set_defaults(handler="add")


def _add_list(sub) -> None:
    p = sub.add_parser("list", help="최신순 거래 목록")
    _add_shared_options(p)
    p.add_argument(
        "--limit", type=positive_int, default=config.DEFAULT_LIST_LIMIT,
        help="표시 건수 (1 이상, 기본 20)",
    )
    p.set_defaults(handler="list")


def _add_search(sub) -> None:
    p = sub.add_parser("search", help="조건 검색")
    _add_shared_options(p)
    p.add_argument("--from", dest="from_", help="시작일 YYYY-MM-DD")
    p.add_argument("--to", dest="to", help="종료일 YYYY-MM-DD")
    p.add_argument("--category", help="카테고리")
    p.add_argument("--type", choices=list(domain_config.VALID_TYPES), help="타입")
    p.add_argument("--q", help="메모 키워드 부분 일치")
    p.add_argument("--tag", help="태그 정확 일치")
    p.set_defaults(handler="search")


def _add_summary(sub) -> None:
    p = sub.add_parser("summary", help="월별 요약")
    _add_shared_options(p)
    p.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    p.add_argument(
        "--top", type=positive_int, default=services_config.DEFAULT_TOP_N,
        help="지출 TOP N (1 이상, 기본 5)",
    )
    p.set_defaults(handler="summary")


def _add_budget(sub) -> None:
    p = sub.add_parser("budget", help="예산 설정")
    _add_shared_options(p)
    bud = p.add_subparsers(dest="budget_cmd", required=True)
    p_set = bud.add_parser("set", help="월 예산 설정")
    _add_shared_options(p_set)
    p_set.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    p_set.add_argument("--amount", required=True, type=int, help="예산 금액(양수)")
    p_set.set_defaults(handler="budget.set")


def _add_category(sub) -> None:
    p = sub.add_parser("category", help="카테고리 관리")
    _add_shared_options(p)
    cat = p.add_subparsers(dest="cat_cmd", required=True)

    p_add = cat.add_parser("add", help="카테고리 추가")
    _add_shared_options(p_add)
    p_add.add_argument("--name", help="카테고리명 (생략 시 대화형)")
    p_add.set_defaults(handler="category.add")

    p_list = cat.add_parser("list", help="카테고리 목록")
    _add_shared_options(p_list)
    p_list.set_defaults(handler="category.list")

    p_remove = cat.add_parser("remove", help="카테고리 삭제")
    _add_shared_options(p_remove)
    p_remove.add_argument("--name", required=True, help="삭제할 카테고리")
    p_remove.add_argument("--replace-with", dest="replace_with", help="사용 중일 때 대체할 카테고리")
    p_remove.set_defaults(handler="category.remove")


def _add_update(sub) -> None:
    p = sub.add_parser("update", help="거래 수정 (옵션 방식)")
    _add_shared_options(p)
    p.add_argument("--id", required=True, help="수정 대상 거래 id")
    p.add_argument("--date", help="YYYY-MM-DD")
    p.add_argument("--type", choices=list(domain_config.VALID_TYPES))
    p.add_argument("--category")
    p.add_argument("--amount", type=int)
    p.add_argument("--memo")
    p.add_argument("--tags", help="쉼표로 구분")
    p.set_defaults(handler="update")


def _add_delete(sub) -> None:
    p = sub.add_parser("delete", help="거래 삭제")
    _add_shared_options(p)
    p.add_argument("--id", required=True, help="삭제 대상 거래 id")
    p.set_defaults(handler="delete")


def _add_export(sub) -> None:
    p = sub.add_parser("export", help="CSV 내보내기")
    _add_shared_options(p)
    p.add_argument("--out", required=True, help="출력 CSV 경로")
    p.add_argument("--month", help="대상 월 YYYY-MM")
    p.add_argument("--from", dest="from_", help="시작일 YYYY-MM-DD")
    p.add_argument("--to", dest="to", help="종료일 YYYY-MM-DD")
    p.add_argument(
        "--no-id",
        dest="include_id",
        action="store_false",
        help="id 컬럼을 빼고 내보낸다 (외부 도구용). 기본은 포함 — 다시 import 할 때 중복을 막는다",
    )
    p.set_defaults(handler="export", include_id=True)


def _add_import(sub) -> None:
    p = sub.add_parser("import", help="CSV 가져오기")
    _add_shared_options(p)
    p.add_argument("--from", dest="from_", required=True, help="입력 CSV 경로")
    p.add_argument(
        "--atomic",
        action="store_true",
        help="전수 롤백 모드 — 한 줄이라도 오류면 아무것도 저장하지 않음 (기본: 부분 성공)",
    )
    p.add_argument(
        "--on-duplicate",
        dest="on_duplicate",
        choices=list(services_config.ON_DUPLICATE_CHOICES),
        default=services_config.DEFAULT_ON_DUPLICATE,
        help=(
            "이미 있는 id 를 만났을 때: skip=건너뜀(기본), "
            "new-id=새 id 로 추가, error=오류로 중단"
        ),
    )
    p.set_defaults(handler="import")


def _add_backup(sub) -> None:
    p = sub.add_parser("backup", help="데이터 폴더 백업 (보너스)")
    _add_shared_options(p)
    # 백업은 기존 폴더를 읽기만 한다 — 없으면 만들지 말고 오류로 알려야 한다.
    p.set_defaults(handler="backup", needs_storage=False)
