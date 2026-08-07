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
