"""CLI 진입점 — 명령 레지스트리와 ``main``.

## 명령 → 핸들러 대응

``parser`` 가 남긴 문자열 키(``"category.add"``)를 ``HANDLERS`` 가 함수로 바꾼다.
파서가 함수 객체를 들고 있던 이전 방식과 달리 두 모듈이 서로를 import 하지 않으므로
순환이 없고, 하위 명령마다 핸들러가 하나씩 대응해 ``if/elif`` 분기가 사라졌다.

명령을 추가하는 절차는 셋이다 — ``parser`` 에 문법, ``handlers`` 에 함수,
여기 ``HANDLERS`` 에 한 줄. ``main`` 은 영원히 그대로다.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

from . import config
from ..context import AppContext
from . import handlers, output, parser as parser_module
from .error_handler import handle_errors


Handler = Callable[[AppContext, argparse.Namespace], int]

HANDLERS: Dict[str, Handler] = {
    "add": handlers.cmd_add,
    "list": handlers.cmd_list,
    "search": handlers.cmd_search,
    "summary": handlers.cmd_summary,
    "budget.set": handlers.cmd_budget_set,
    "category.add": handlers.cmd_category_add,
    "category.list": handlers.cmd_category_list,
    "category.remove": handlers.cmd_category_remove,
    "update": handlers.cmd_update,
    "delete": handlers.cmd_delete,
    "export": handlers.cmd_export,
    "import": handlers.cmd_import,
    "backup": handlers.cmd_backup,
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


@handle_errors
def _dispatch(args: argparse.Namespace) -> int:
    """컨텍스트를 조립하고 핸들러를 부른다 — **오류 방패 안에서**.

    이 함수가 따로 있는 이유가 3-1 수정의 전부다. 이전에는 ``AppContext`` 생성과
    ``prepare()`` 가 ``main`` 안, 즉 ``@handle_errors`` **밖**에 있었다. 그래서
    ``--data-dir`` 에 파일 경로를 주면(오타 하나로 충분하다) ``mkdir`` 이
    ``FileExistsError`` 를 던지고, 그것을 아무도 잡지 않아 **원시 트레이스백**과
    종료 코드 1 로 끝났다. "사용자에게 스택트레이스를 노출하지 않는다", "입출력
    문제는 3번" 이라는 두 정책이 동시에 깨지는 자리였다.

    파일을 여는 코드가 방패 밖에 있으면 방패가 아니다. 그래서 저장소를 만지는
    모든 경로를 한 함수로 모아 데코레이터를 한 번만 씌운다.

    핸들러 각각에 붙어 있던 ``@handle_errors`` 는 이제 없앴다. 정책이 한 곳에서
    적용되면 "핸들러를 추가할 때 데코레이터를 빠뜨리는" 실수 자체가 사라진다.
    """
    ctx = AppContext(Path(args.data_dir))
    if args.needs_storage:
        ctx.prepare()
    return HANDLERS[args.handler](ctx, args)


def main(argv: Optional[List[str]] = None) -> int:
    try:
        args = parser_module.build_parser().parse_args(argv)
        # 로거에 핸들러를 붙이는 유일한 지점. 이 호출이 없으면 handle_errors 가
        # exc_info 로 보존한 스택트레이스가 아무 데도 출력되지 않는다.
        output.setup_logging(getattr(args, "debug", False))
        return _dispatch(args)
    except BrokenPipeError:
        # 예: `budget_app list | head` — head 가 먼저 닫음. 오류가 아니므로 조용히 종료.
        _silence_broken_pipe()
        return config.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
