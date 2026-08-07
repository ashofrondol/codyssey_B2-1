"""계층 규칙을 **테스트로 강제**한다 — 문서에 적힌 규칙은 검증되지 않는다.

이 프로젝트의 의존 방향은 아래로만 흐른다::

    cli → services → storage → domain → errors

규칙을 문서에만 적어 두면 다음 사람이(또는 다음 달의 내가) 한 줄 어긴 것을 아무도
못 잡는다. 실제로 그런 자리가 셋 있었다 — ``cli/handlers`` 가 ``storage.backup`` 을
직접 부르고, ``cli/prompts`` 가 ``CategoryStore`` 를 타입으로 받고, 핸들러가
``ctx.cats`` 로 저장소에 직접 닿았다.

import 를 AST 로 세는 이유: 문자열 검색은 주석·docstring 에 적힌 모듈 이름까지
세어서 거짓 양성이 나온다.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parent.parent / "budget_app"

#: 숫자가 작을수록 아래 계층. 같은 계층끼리는 허용한다.
LAYERS: dict[str, int] = {"domain": 0, "storage": 1, "services": 2, "cli": 3}

#: 계층에 속하지 않는 루트 모듈 — 아무나 써도 되는 공용 어휘
ROOT_MODULES = {"errors", "config", "decorators", "context", "__main__"}


def _modules() -> list[Path]:
    return sorted(p for p in PACKAGE.rglob("*.py") if "__pycache__" not in p.parts)


def _layer_of(path: Path) -> str:
    rel = path.relative_to(PACKAGE)
    return rel.parts[0] if len(rel.parts) > 1 else "<root>"


def _imported_layers(path: Path) -> set[str]:
    """이 파일이 **패키지 안에서** 어느 계층을 import 하는지.

    상대 import 만 본다. ``from ..storage.repositories import X`` 는 level=2,
    module="storage.repositories" 로 파싱되므로 첫 조각이 계층 이름이다.
    ``from . import config`` 처럼 같은 패키지 안을 가리키는 것은 자기 계층이다.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    here = _layer_of(path)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or not node.level:
            continue
        head = (node.module or "").split(".")[0]
        if node.level == 1 and not node.module:
            continue  # from . import x — 자기 계층
        if head in LAYERS:
            found.add(head)
        elif node.level >= 2 and head in ROOT_MODULES:
            found.add("<root>")
        elif node.level == 1 and here in LAYERS:
            found.add(here)
    return found


@pytest.mark.parametrize("path", _modules(), ids=lambda p: str(p.relative_to(PACKAGE)))
def test_no_upward_imports(path: Path):
    """어떤 모듈도 자기보다 위 계층을 import 하지 않는다."""
    here = _layer_of(path)
    if here not in LAYERS:
        return  # 루트 모듈은 조립을 위해 아래로 자유롭게 내려간다
    for imported in _imported_layers(path) - {"<root>"}:
        assert LAYERS[imported] <= LAYERS[here], (
            f"{path.relative_to(PACKAGE)} ({here}) 가 위 계층 {imported} 를 import 한다"
        )


def test_cli_never_touches_storage():
    """CLI 는 **서비스와만** 말한다 — 저장소를 건너뛰어 부르지 않는다.

    한 자리라도 질러가면 이 규칙은 규칙이 아니라 관습이 된다. 관습은 검증할 수 없다.
    """
    offenders = [
        str(p.relative_to(PACKAGE))
        for p in _modules()
        if _layer_of(p) == "cli" and "storage" in _imported_layers(p)
    ]
    assert offenders == [], f"CLI 가 저장소를 직접 import 한다: {offenders}"


def test_domain_imports_nothing_above_itself():
    """도메인은 파일도 화면도 모른다 — 순수한 규칙만 남는 계층."""
    for p in _modules():
        if _layer_of(p) != "domain":
            continue
        assert _imported_layers(p) <= {"domain", "<root>"}, str(p.relative_to(PACKAGE))


def test_app_context_does_not_expose_repositories():
    """핸들러가 서비스를 건너뛸 수 있는 통로를 남기지 않는다."""
    from budget_app.context import AppContext

    ctx = AppContext(Path("."))
    public = {name for name in vars(ctx) if not name.startswith("_")}
    assert not {"txs", "cats", "budgets"} & public, f"저장소가 공개돼 있다: {public}"
    assert "tx_service" in public and "backup_service" in public


def test_every_handler_is_registered():
    """``HANDLERS`` 에 빠진 핸들러가 없다 — 등록을 잊으면 KeyError 로만 드러난다."""
    from budget_app.cli import app, handlers

    defined = {n for n in dir(handlers) if n.startswith("cmd_")}
    registered = {f.__name__ for f in app.HANDLERS.values()}
    assert defined == registered, f"등록 누락/잉여: {defined ^ registered}"
