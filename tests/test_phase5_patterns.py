"""Phase 5 — 디자인 패턴 정합화의 결과를 고정한다.

"패턴을 썼다"는 주장은 검증되지 않으면 문서에만 있는 말이다. 여기서 확인하는 것은
패턴의 이름이 아니라 **그 패턴이 약속한 성질**이다.
"""

from __future__ import annotations

import dataclasses

import pytest

from budget_app.domain import specs
from budget_app.domain.entities import Budget, Category, Transaction, TransactionPatch
from budget_app.domain.queries import SearchFilter
from budget_app.domain.tx_id import TransactionId
from budget_app.storage.unit_of_work import UnitOfWork


def _tx(n: int, **kw) -> Transaction:
    base = dict(type="expense", date="2024-01-01", amount=100, category="food")
    base.update(kw)
    return Transaction(id=TransactionId.of(n), **base)


# ============================================================
# 5-4. 엔티티 불변
# ============================================================


@pytest.mark.parametrize(
    ("entity", "attr", "value"),
    [
        (_tx(1), "amount", -1),
        (_tx(1), "category", "다른값"),
        (Budget(month="2024-01", amount=100), "amount", -1),
        (Category(name="food"), "name", ""),
    ],
)
def test_entities_reject_mutation(entity, attr, value):
    """"생성자가 유일한 불변식 강제 지점"이 되려면 생성 후 바꿀 수 없어야 한다."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(entity, attr, value)


def test_tags_are_immutable_too():
    """``frozen`` 은 필드 재바인딩만 막는다 — 리스트 안을 바꾸는 구멍은 튜플로 닫는다."""
    tx = _tx(1, tags=["a"])
    assert isinstance(tx.tags, tuple)
    with pytest.raises(AttributeError):
        tx.tags.append("b")


def test_transaction_is_hashable():
    """frozen 이 만들어 주는 __hash__ 는 필드가 전부 해시 가능해야 동작한다."""
    assert len({_tx(1), _tx(1), _tx(2)}) == 2


def test_with_patch_returns_a_new_object():
    original = _tx(1, amount=100)
    updated = original.with_patch(TransactionPatch(amount=500))
    assert original.amount == 100 and updated.amount == 500
    assert updated is not original


# ============================================================
# 5-3. 한 번만 읽기 / 변경 없으면 쓰지 않기
# ============================================================


def _count_scans(repo, monkeypatch) -> dict:
    """``iter_raw`` 호출 횟수를 센다 — 전체 스캔 한 번이 한 호출이다."""
    seen = {"n": 0}
    original = type(repo).iter_raw

    def counting(self, *a, **kw):
        if self is repo:
            seen["n"] += 1
        return original(self, *a, **kw)

    monkeypatch.setattr(type(repo), "iter_raw", counting)
    return seen


def test_delete_scans_the_file_once(txs, monkeypatch):
    txs.append(_tx(1))
    scans = _count_scans(txs, monkeypatch)
    assert txs.delete("TX-000001") is True
    assert scans["n"] == 1, f"전체 스캔이 {scans['n']}회 일어났다"


def test_replace_scans_the_file_once(txs, monkeypatch):
    txs.append(_tx(1))
    scans = _count_scans(txs, monkeypatch)
    assert txs.replace("TX-000001", _tx(1, amount=999)) is True
    assert scans["n"] == 1


def test_reassign_scans_the_file_once(txs, monkeypatch):
    txs.append(_tx(1))
    scans = _count_scans(txs, monkeypatch)
    assert txs.reassign_category("food", "etc") == 1
    assert scans["n"] == 1


def test_missing_target_does_not_touch_the_file(txs):
    """대상이 없으면 파일을 쓰지 않는다 — 조회만 한 명령이 수정 시각을 바꾸면 안 된다."""
    txs.append(_tx(1))
    before = txs.path.stat().st_mtime_ns
    assert txs.delete("TX-999999") is False
    assert txs.path.stat().st_mtime_ns == before


def test_rewrite_reports_whether_it_wrote(txs):
    txs.append(_tx(1))
    assert txs.rewrite(lambda t: t) is False        # 바뀐 것 없음
    assert txs.rewrite(lambda t: None) is True      # 전부 삭제


def test_delete_and_replace_agree_on_existence(txs):
    """존재 판정 기준이 둘로 갈리지 않는다 — 해석 불가 줄의 id 는 어느 쪽도 못 만진다."""
    txs.path.write_text('{"id": "TX-000005", "amount": "깨짐"}\n', encoding="utf-8")
    assert txs.delete("TX-000005") is False
    assert txs.replace("TX-000005", _tx(5)) is False
    assert "TX-000005" in txs.path.read_text(encoding="utf-8"), "손상 줄이 사라졌다"


# ============================================================
# 5-2. UnitOfWork — 서비스가 줄 목록을 나르지 않는다
# ============================================================


def test_uow_stage_takes_a_transform_not_lines(txs, cats):
    """호출자는 "무엇을 반영할지"만 넘기고, 계획은 UoW 가 저장소에게 시킨다."""
    with UnitOfWork() as uow:
        assert uow.stage(txs, extra=[_tx(1)]) is True
    assert [t.id.value for t in txs.stream()] == ["TX-000001"]


def test_uow_stage_skips_when_nothing_changes(txs, tmp_path):
    txs.append(_tx(1))
    with UnitOfWork() as uow:
        assert uow.stage(txs) is False
    assert list(txs.path.parent.glob("*.tmp")) == []


# ============================================================
# 5-1. Specification — 남겨 둔 조합 대수가 실제로 동작하는가
# ============================================================


def test_date_range_helper_is_gone():
    """소비자가 없던 축약 함수는 제거했다 — 죽은 코드는 읽는 사람을 속인다."""
    assert not hasattr(specs, "date_range")


def test_and_or_not_compose():
    food = _tx(1, category="food", tags=["정기"])
    cafe = _tx(2, category="cafe")

    either = specs.InCategory("food") | specs.InCategory("cafe")
    assert either.is_satisfied_by(food) and either.is_satisfied_by(cafe)

    without_regular = either & ~specs.HasTag("정기")
    assert not without_regular.is_satisfied_by(food)
    assert without_regular.is_satisfied_by(cafe)


def test_always_is_the_identity_of_and():
    """Null Object — 조건이 하나도 없을 때 ``None`` 검사 없이 같은 코드로 흐른다."""
    assert SearchFilter().matches(_tx(1)) is True
    # 항등원이므로 조합에서 사라진다 — 평가 한 겹이 줄고 repr 이 읽힌다.
    combined = specs.Always() & specs.InCategory("food")
    assert [type(s).__name__ for s in combined.specs] == ["InCategory"]


def test_specs_normalize_their_values():
    """저장할 때와 찾을 때의 규칙이 어긋나면 검색은 오류 없이 조용히 틀린다."""
    assert specs.InCategory("  food  ").is_satisfied_by(_tx(1, category="food"))
    assert specs.OfType(" EXPENSE ").is_satisfied_by(_tx(1))
    assert specs.DateFrom("2024-1-1").is_satisfied_by(_tx(1, date="2024-01-01"))
