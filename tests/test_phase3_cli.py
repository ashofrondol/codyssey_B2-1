"""Phase 3 회귀 — CLI 정확성.

"오류 상황에서 프로그램이 어떻게 끝나는가"를 고정한다. 종료 코드는 셸 스크립트가
읽는 **공개 계약**이므로 트레이스백으로 끝나는 경로가 있으면 안 된다.
"""

from __future__ import annotations

import pytest

from budget_app.cli import config as cli_config
from budget_app.domain.entities import Transaction
from budget_app.domain.tx_id import TransactionId


def _tx(n: int, **kw) -> Transaction:
    base = dict(type="expense", date="2024-01-01", amount=100, category="food")
    base.update(kw)
    return Transaction(id=TransactionId.of(n), **base)


# ============================================================
# 3-1. --data-dir 오류가 오류 방패 밖에서 터진다
# ============================================================


def test_data_dir_pointing_at_a_file_exits_with_io_code(tmp_path, capsys, monkeypatch):
    """``--data-dir`` 가 파일을 가리키면 친절한 오류 + ``EXIT_IO`` 여야 한다.

    ``AppContext`` 생성과 ``prepare()`` 가 ``@handle_errors`` **밖**에 있어서
    지금은 원시 트레이스백으로 죽는다(사용자에게 스택을 노출하지 않는다는 정책 위반).
    """
    import io
    import sys

    from budget_app.cli.app import main

    victim = tmp_path / "not_a_dir.txt"
    victim.write_text("나는 파일이다", encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))

    code = main(["list", "--data-dir", str(victim)])
    cap = capsys.readouterr()
    assert code == cli_config.EXIT_IO
    assert "Traceback" not in cap.err
    assert "[오류]" in cap.err


def test_data_dir_error_does_not_leak_traceback(tmp_path, capsys, monkeypatch):
    import io
    import sys

    from budget_app.cli.app import main

    victim = tmp_path / "f.txt"
    victim.write_text("x", encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    main(["summary", "--month", "2024-01", "--data-dir", str(victim)])
    assert "Traceback" not in capsys.readouterr().err


# ============================================================
# 3-2. --limit / --top 양수 검증
# ============================================================


def test_list_limit_zero_is_rejected(txs, run):
    """``--limit 0`` 이 데이터가 있는데도 "(데이터 없음)" 을 출력하면 안 된다.

    프레젠터가 ``count == 0`` 하나로 "비었다"와 "잘라서 아무것도 안 냈다"를 같이
    취급한다. 애초에 0/음수를 argparse 에서 막는 것이 맞다.
    """
    txs.append(_tx(1))
    result = run("list", "--limit", "0")
    assert "(데이터 없음)" not in result.out


@pytest.mark.parametrize("bad", ["0", "-1"])
def test_list_limit_non_positive_exits_with_error(txs, run, bad):
    txs.append(_tx(1))
    with pytest.raises(SystemExit) as exc:
        run("list", "--limit", bad)
    assert exc.value.code != 0


@pytest.mark.parametrize("bad", ["0", "-3"])
def test_summary_top_non_positive_exits_with_error(run, bad):
    with pytest.raises(SystemExit) as exc:
        run("summary", "--month", "2024-01", "--top", bad)
    assert exc.value.code != 0


# ============================================================
# 3-3. export 기간 옵션 조합
# ============================================================


def test_export_rejects_month_together_with_range(tmp_path, txs, run):
    """``--month`` 와 ``--from/--to`` 를 함께 주면 지금은 ``--month`` 만 쓰고
    나머지를 **조용히 무시**한다. 사용자가 의도한 범위가 아닐 수 있으므로 막는다."""
    txs.append(_tx(1))
    result = run("export", "--out", str(tmp_path / "o.csv"),
                 "--month", "2024-01", "--from", "2024-01-01", "--to", "2024-01-05")
    assert result.code == cli_config.EXIT_APP


def test_export_with_only_from_is_rejected(tmp_path, txs, run):
    txs.append(_tx(1))
    result = run("export", "--out", str(tmp_path / "o.csv"), "--from", "2024-01-01")
    assert result.code == cli_config.EXIT_APP


# ============================================================
# 3-5. update --tags 타입 계약
# ============================================================


def test_update_tags_is_parsed_into_a_list(txs, cats, run):
    """``--tags "a,b"`` 는 ``["a", "b"]`` 로 저장돼야 한다.

    핸들러가 쉼표 문자열을 그대로 ``TransactionPatch.tags`` 에 넣는다. 지금은
    ``Transaction.__post_init__`` 의 ``parse_tags`` 가 우연히 구제해 주지만,
    **선언된 타입(``Optional[List[str]]``)과 실제 값이 다른** 상태다.
    """
    txs.append(_tx(1))
    assert run("update", "--id", "TX-000001", "--tags", "a,b").code == 0
    assert [tx.tags for tx in txs.stream()] == [["a", "b"]]


def test_update_patch_receives_list_not_string():
    """계약 자체를 직접 확인한다 — 핸들러가 만든 patch 의 tags 는 리스트여야 한다."""
    import argparse

    from budget_app.cli import handlers

    args = argparse.Namespace(id="TX-000001", date=None, type=None, category=None,
                              amount=None, memo=None, tags="a,b")
    patch = handlers._build_patch(args)
    assert patch.tags == ["a", "b"]


# ============================================================
# 3-6. 예기치 못한 예외 로깅
# ============================================================


def test_unexpected_exception_is_logged_at_error_level(caplog, run, monkeypatch):
    """스택트레이스가 DEBUG 로만 남으면 기본 실행에서 증발한다 — 사후 분석 불가."""
    import logging

    from budget_app.cli import handlers

    def _boom(*a, **kw):
        raise RuntimeError("의도적 폭발")

    monkeypatch.setattr(handlers.presenter, "category_lines", _boom)
    with caplog.at_level(logging.ERROR):
        result = run("category", "list")

    assert result.code == cli_config.EXIT_ERROR
    assert any(r.levelno >= logging.ERROR and r.exc_info for r in caplog.records)


# ============================================================
# 3-4. --data-dir 위치 규칙
# ============================================================


def test_data_dir_accepted_before_the_command(tmp_path, capsys, monkeypatch):
    """``--debug`` 처럼 최상위에서도 받아야 한다 — 위치에 따라 되고 안 되고가
    갈리면 사용자는 규칙을 외워야 한다."""
    import io
    import sys

    from budget_app.cli.app import main

    d = tmp_path / "data"
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    code = main(["--data-dir", str(d), "list"])
    capsys.readouterr()
    assert code == 0
    assert (d / "transactions.jsonl").exists()
