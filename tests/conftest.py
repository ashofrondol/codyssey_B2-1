"""테스트 공통 픽스처.

CLI 를 서브프로세스가 아니라 ``main(argv)`` **직접 호출**로 실행한다. 종료 코드를
그대로 받을 수 있고, 예외가 어디서 났는지도 그대로 보인다(서브프로세스로 돌리면
스택이 문자열로만 남는다).

각 테스트는 ``tmp_path`` 아래의 빈 데이터 폴더에서 시작하므로 서로 간섭하지 않는다.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import NamedTuple

import pytest

from budget_app.cli.app import main
from budget_app.storage.repositories import BudgetStore, CategoryStore, TransactionRepository


class Result(NamedTuple):
    """CLI 한 번 실행의 결과 — 종료 코드와 두 채널."""

    code: int
    out: str
    err: str


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    d = tmp_path / "data"
    d.mkdir()
    return d


@pytest.fixture
def run(data_dir, capsys, monkeypatch):
    """``run("list")`` 처럼 부른다. ``--data-dir`` 는 자동으로 붙는다.

    ``stdin`` 인자로 대화형 입력을 미리 넣어 둘 수 있다. ``input()`` 은 실제
    표준입력이 아닌 객체가 ``sys.stdin`` 에 있으면 그 ``readline`` 을 쓰므로
    ``StringIO`` 로 갈아 끼우면 된다.
    """

    def _run(*argv: str, stdin: str = "") -> Result:
        monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
        args = list(argv)
        if "--data-dir" not in args:
            args += ["--data-dir", str(data_dir)]
        code = main(args)
        cap = capsys.readouterr()
        return Result(code, cap.out, cap.err)

    return _run


@pytest.fixture
def txs(data_dir) -> TransactionRepository:
    repo = TransactionRepository(data_dir)
    repo.ensure_ready()
    return repo


@pytest.fixture
def cats(data_dir) -> CategoryStore:
    store = CategoryStore(data_dir)
    store.ensure_ready()
    store.seed_defaults()
    return store


@pytest.fixture
def budgets(data_dir) -> BudgetStore:
    store = BudgetStore(data_dir)
    store.ensure_ready()
    return store


@pytest.fixture
def add_tx(run):
    """대화형 ``add`` 를 한 줄로 부르는 헬퍼 — 6개 입력을 순서대로 넣는다."""

    def _add(date="2024-01-15", type_="expense", category="food", amount=1000, memo="", tags=""):
        stdin = f"{date}\n{type_}\n{category}\n{amount}\n{memo}\n{tags}\n"
        return run("add", stdin=stdin)

    return _add
