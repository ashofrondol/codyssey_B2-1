"""정상 경로 스모크 — 11개 명령이 살아 있는지 확인하는 안전망.

Phase 1~5 의 수정이 **정상 동작을 깨지 않았음**을 매 단계 확인하기 위한 것이다.
버그 재현 테스트와 달리 이쪽은 처음부터 전부 통과해야 한다.
"""

from __future__ import annotations

from budget_app.cli import config as cli_config


def test_category_list_shows_seeded_defaults(run):
    result = run("category", "list")
    assert result.code == 0
    assert "food" in result.out


def test_category_add_and_remove(run):
    assert run("category", "add", "--name", "book").code == 0
    assert "book" in run("category", "list").out
    assert run("category", "remove", "--name", "book").code == 0
    assert "book" not in run("category", "list").out


def test_add_then_list(run, add_tx):
    assert add_tx(date="2024-03-01", amount=1500, memo="커피").code == 0
    out = run("list").out
    assert "TX-000001" in out
    assert "커피" in out


def test_search_by_category_and_tag(run, add_tx):
    add_tx(date="2024-03-01", category="food", amount=1000, memo="점심", tags="회식")
    add_tx(date="2024-03-02", category="transport", amount=2000, memo="택시")

    assert "TX-000001" in run("search", "--category", "food").out
    assert "TX-000002" not in run("search", "--category", "food").out
    assert "TX-000001" in run("search", "--tag", "회식").out
    assert "TX-000002" in run("search", "--q", "택시").out
    assert "TX-000002" in run("search", "--type", "expense").out


def test_summary_with_budget(run, add_tx):
    add_tx(date="2024-03-01", amount=30000, category="food")
    run("budget", "set", "--month", "2024-03", "--amount", "100000")
    out = run("summary", "--month", "2024-03").out
    assert "총 지출: 30000원" in out
    assert "30.0%" in out


def test_summary_over_budget_warns(run, add_tx):
    add_tx(date="2024-03-01", amount=200000, category="food")
    run("budget", "set", "--month", "2024-03", "--amount", "100000")
    assert "예산을 초과" in run("summary", "--month", "2024-03").out


def test_update_and_delete(run, add_tx):
    add_tx(date="2024-03-01", amount=1000)
    assert run("update", "--id", "TX-000001", "--amount", "9999").code == 0
    assert "9999" in run("list").out
    assert run("delete", "--id", "TX-000001").code == 0
    assert "(데이터 없음)" in run("list").out


def test_export_import_roundtrip_does_not_duplicate(tmp_path, run, add_tx):
    """리팩터 3번 버그의 회귀 — 내보낸 파일을 다시 넣어도 거래가 늘지 않는다."""
    add_tx(date="2024-03-01", amount=1000, memo="A")
    add_tx(date="2024-03-02", amount=2000, memo="B")

    csv_path = tmp_path / "out.csv"
    assert run("export", "--out", str(csv_path), "--month", "2024-03").code == 0

    result = run("import", "--from", str(csv_path))
    assert "imported=0" in result.out
    assert "duplicated=2" in result.out
    assert run("list").out.count("TX-0000") == 2


def test_import_external_csv_without_id(tmp_path, run):
    csv_path = tmp_path / "ext.csv"
    csv_path.write_text(
        "date,type,category,amount,memo,tags\n"
        "2024-03-01,expense,food,1000,점심,\n"
        "2024-03-02,income,salary,50000,월급,\n",
        encoding="utf-8",
    )
    result = run("import", "--from", str(csv_path))
    assert "imported=2" in result.out


def test_import_partial_mode_keeps_valid_rows(tmp_path, run):
    csv_path = tmp_path / "mixed.csv"
    csv_path.write_text(
        "date,type,category,amount\n"
        "2024-03-01,expense,food,1000\n"
        "bad-date,expense,food,2000\n",
        encoding="utf-8",
    )
    result = run("import", "--from", str(csv_path))
    assert "imported=1" in result.out
    assert "skipped=1" in result.out


def test_import_atomic_mode_rolls_back_everything(tmp_path, run):
    csv_path = tmp_path / "mixed.csv"
    csv_path.write_text(
        "date,type,category,amount\n"
        "2024-03-01,expense,food,1000\n"
        "bad-date,expense,food,2000\n",
        encoding="utf-8",
    )
    result = run("import", "--from", str(csv_path), "--atomic")
    assert result.code == cli_config.EXIT_APP
    assert "(데이터 없음)" in run("list").out


def test_backup_creates_timestamped_folder(data_dir, run, add_tx):
    add_tx()
    result = run("backup")
    assert result.code == 0
    backups = list(data_dir.parent.glob("backup_*"))
    assert len(backups) == 1
    assert (backups[0] / "transactions.jsonl").exists()


def test_backup_on_missing_dir_is_a_clean_error(tmp_path, capsys, monkeypatch):
    import io
    import sys

    from budget_app.cli.app import main

    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    code = main(["backup", "--data-dir", str(tmp_path / "nope")])
    cap = capsys.readouterr()
    assert code == cli_config.EXIT_IO
    assert "Traceback" not in cap.err


def test_unknown_transaction_id_exits_with_app_code(run):
    assert run("delete", "--id", "TX-999999").code == cli_config.EXIT_APP


def test_invalid_value_exits_with_validation_code(run):
    assert run("summary", "--month", "not-a-month").code == cli_config.EXIT_VALIDATION


def test_category_in_use_is_protected(run, add_tx):
    add_tx(category="food")
    assert run("category", "remove", "--name", "food").code == cli_config.EXIT_APP
    assert "food" in run("category", "list").out


def test_category_remove_with_replacement_reassigns(run, add_tx):
    add_tx(category="food", amount=1000)
    result = run("category", "remove", "--name", "food", "--replace-with", "etc")
    assert result.code == 0
    assert "etc" in run("list").out


def test_corrupt_line_is_preserved_across_unrelated_delete(txs, run, add_tx):
    """리팩터 1번 버그의 회귀 — 무관한 삭제가 손상 줄을 지우면 안 된다."""
    add_tx(date="2024-03-01", amount=1000)
    with open(txs.path, "a", encoding="utf-8") as f:
        f.write("이건 JSON 이 아니다\n")
    add_tx(date="2024-03-02", amount=2000)

    run("delete", "--id", "TX-000001")
    assert "이건 JSON 이 아니다" in txs.path.read_text(encoding="utf-8")


def test_id_scan_sees_ids_on_corrupt_lines(txs, run, add_tx):
    """리팩터 2번 버그의 회귀 — 검증 실패 줄의 id 도 '이미 쓰인 번호'다."""
    with open(txs.path, "a", encoding="utf-8") as f:
        f.write('{"id": "TX-000005", "type": "expense", "date": "bad", '
                '"amount": 1, "category": "food"}\n')
    add_tx()
    ids = [tx.id.value for tx in txs.stream()]
    assert "TX-000005" not in ids or len(set(ids)) == len(ids)
    assert txs.path.read_text(encoding="utf-8").count("TX-000005") == 1
