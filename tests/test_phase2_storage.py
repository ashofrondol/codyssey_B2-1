"""Phase 2 회귀 — 저장 계층 견고성.

파일이 이상적인 상태가 아닐 때(꼬리가 찢어짐, 바이트가 깨짐, BOM 이 붙음)
프로그램이 어떻게 되는지를 고정한다.
"""

from __future__ import annotations

import pytest

from budget_app.domain.entities import Transaction
from budget_app.domain.tx_id import TransactionId
from budget_app.storage import csv_io


def _tx(n: int, **kw) -> Transaction:
    base = dict(type="expense", date="2024-01-01", amount=100, category="food")
    base.update(kw)
    return Transaction(id=TransactionId.of(n), **base)


# ============================================================
# 2-1. append 꼬리 개행
# ============================================================


def test_append_to_file_without_trailing_newline_keeps_both_records(txs):
    """마지막 줄에 개행이 없는 파일(쓰다 만 흔적)에 이어 쓰면, 두 JSON 이 한 줄로
    합쳐져 **두 레코드가 동시에 사라진다**.

    기존 줄은 손상 줄로 보존되기라도 하지만, 새로 추가한 레코드까지 같이 죽는 것이
    문제다 — 사용자는 "저장 완료"를 보고 나서 목록에서 그것을 찾지 못한다.
    """
    txs.path.write_text('{"id": "TX-000001", "type": "expense", "date": "2024-01-01", '
                        '"amount": 100, "category": "food", "memo": "", "tags": []}',
                        encoding="utf-8")
    txs.append(_tx(2))

    ids = [tx.id.value for tx in txs.stream()]
    assert "TX-000002" in ids, f"새로 추가한 레코드가 사라졌다: {ids}"


def test_append_all_to_file_without_trailing_newline(txs):
    txs.path.write_text('{"id": "TX-000001", "type": "expense", "date": "2024-01-01", '
                        '"amount": 100, "category": "food", "memo": "", "tags": []}',
                        encoding="utf-8")
    txs.append_all([_tx(2), _tx(3)])
    ids = {tx.id.value for tx in txs.stream()}
    assert {"TX-000002", "TX-000003"} <= ids


# ============================================================
# 2-4. 바이트 손상 라인 격리
# ============================================================


def test_undecodable_byte_line_does_not_kill_the_whole_file(txs):
    """``\\xff`` 한 줄이 파일 전체 읽기를 죽이면 안 된다.

    "손상된 줄은 격리한다"는 약속이 JSON 층에만 있고 인코딩 층에는 없어서,
    바이트가 깨진 줄 하나로 ``list`` 전체가 실패한다.
    """
    good = ('{"id": "TX-000001", "type": "expense", "date": "2024-01-01", '
            '"amount": 100, "category": "food", "memo": "", "tags": []}')
    txs.path.write_bytes(good.encode("utf-8") + b"\n" + b"\xff\xfe not utf-8\n")

    ids = [tx.id.value for tx in txs.stream()]
    assert ids == ["TX-000001"]


def test_undecodable_line_is_preserved_on_rewrite(txs):
    """격리한 줄은 무관한 재작성에 휩쓸려 사라지면 안 된다(1번 버그와 같은 규칙)."""
    good1 = ('{"id": "TX-000001", "type": "expense", "date": "2024-01-01", '
             '"amount": 100, "category": "food", "memo": "", "tags": []}')
    good2 = ('{"id": "TX-000002", "type": "expense", "date": "2024-01-02", '
             '"amount": 200, "category": "food", "memo": "", "tags": []}')
    broken = b"\xff\xfe not utf-8"
    txs.path.write_bytes(good1.encode() + b"\n" + broken + b"\n" + good2.encode() + b"\n")

    txs.delete("TX-000002")
    assert broken in txs.path.read_bytes(), "손상 줄이 재작성에 휩쓸려 사라졌다"


def test_cli_list_survives_undecodable_line(txs, run):
    good = ('{"id": "TX-000001", "type": "expense", "date": "2024-01-01", '
            '"amount": 100, "category": "food", "memo": "", "tags": []}')
    txs.path.write_bytes(good.encode("utf-8") + b"\n" + b"\xff\xfe\n")
    result = run("list")
    assert result.code == 0
    assert "TX-000001" in result.out


# ============================================================
# 2-5. CSV BOM
# ============================================================


def test_import_csv_with_utf8_bom(tmp_path, run, add_tx):
    """엑셀이 저장한 CSV 는 BOM 이 붙는다. 첫 컬럼명이 ``\\ufeffdate`` 로 깨져
    "필수 컬럼 없음" 으로 거절되면 안 된다."""
    csv_path = tmp_path / "bom.csv"
    csv_path.write_text("date,type,category,amount,memo,tags\n"
                        "2024-01-01,expense,food,1000,점심,\n",
                        encoding="utf-8-sig")
    result = run("import", "--from", str(csv_path))
    assert result.code == 0
    assert "imported=1" in result.out


def test_import_csv_with_bom_preserves_id_column(tmp_path, run):
    """BOM 이 ``id`` 컬럼명을 깨뜨리면 왕복 중복 방지가 조용히 무력화된다."""
    csv_path = tmp_path / "bom_id.csv"
    csv_path.write_text("id,date,type,category,amount,memo,tags\n"
                        "TX-000042,2024-01-01,expense,food,1000,,\n",
                        encoding="utf-8-sig")
    run("import", "--from", str(csv_path))
    result = run("list")
    assert "TX-000042" in result.out


def test_read_rows_accepts_bom(tmp_path):
    csv_path = tmp_path / "b.csv"
    csv_path.write_text("date,type,category,amount\n2024-01-01,expense,food,1\n",
                        encoding="utf-8-sig")
    rows = list(csv_io.read_rows(csv_path))
    assert rows[0][1]["date"] == "2024-01-01"


# ============================================================
# 2-6. 태그 CSV 왕복
# ============================================================


def test_tag_containing_separator_is_rejected():
    """쉼표를 담은 태그는 CSV join/split 로 왕복하면 두 개로 쪼개진다.
    포맷을 바꾸지 않기로 했으므로 **검증에서 막는다**."""
    from budget_app.domain import validators
    from budget_app.errors import ValidationError

    with pytest.raises(ValidationError):
        validators.parse_tags(["a,b"])


def test_tags_roundtrip_through_csv(tmp_path, txs, run):
    txs.append(_tx(1, tags=["점심", "회식"]))
    out_csv = tmp_path / "t.csv"
    run("export", "--out", str(out_csv), "--month", "2024-01")
    rows = [r for _, r in csv_io.read_rows(out_csv)]
    assert rows[0]["tags"] == "점심,회식"


# ============================================================
# 2-3. UnitOfWork 커밋 실패 후처리
# ============================================================


def test_uow_commit_failure_cleans_up_and_reports(tmp_path, monkeypatch):
    """두 번째 ``os.replace`` 가 실패하면 ``.tmp`` 를 남기지 말고 예외를 올려야 한다."""
    from budget_app.storage import unit_of_work as uow_module

    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    a.write_text("", encoding="utf-8")
    b.write_text("", encoding="utf-8")

    class _Store:
        def __init__(self, path):
            self.path = path

    calls = {"n": 0}
    real_commit = uow_module.commit_staged

    def _flaky_commit(tmp, target):
        calls["n"] += 1
        if calls["n"] == 2:  # 두 번째 rename 만 실패시킨다 — 반쪽 커밋 상황
            raise PermissionError(13, "locked", str(target))
        real_commit(tmp, target)

    monkeypatch.setattr(uow_module, "commit_staged", _flaky_commit)

    uow = uow_module.UnitOfWork()
    uow.stage(_Store(a), ["1"])
    uow.stage(_Store(b), ["2"])
    with pytest.raises(PermissionError):
        uow.commit()

    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == [], f"커밋 실패 후 임시 파일이 남았다: {leftovers}"
