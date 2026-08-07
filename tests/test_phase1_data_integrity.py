"""Phase 1 회귀 — 조용한 데이터 손상 버그 재현.

여기 있는 테스트는 **수정 전에 전부 실패**해야 한다. 전부 "오류 없이 잘못된
결과가 나오는" 부류라, 실행만 해서는 드러나지 않는다.
"""

from __future__ import annotations

import pytest

from budget_app.domain import validators
from budget_app.domain.entities import Transaction
from budget_app.domain.tx_id import TransactionId
from budget_app.errors import AppError
from budget_app.services.budgets import BudgetService
from budget_app.services.categories import CategoryService

# ============================================================
# 0-1. 날짜 정규화 — strptime 은 비패딩을 통과시킨다
# ============================================================


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2024-01-05", "2024-01-05"),
        ("2024-1-5", "2024-01-05"),
        ("2024-1-05", "2024-01-05"),
        (" 2024-01-05 ", "2024-01-05"),
    ],
)
def test_parse_date_normalizes_to_padded_form(raw, expected):
    """``strptime`` 은 ``2024-1-5`` 를 받아 준다 — 검증만 하고 원문을 돌려주면
    파일에 두 가지 표기가 공존하고 문자열 비교가 깨진다."""
    assert validators.parse_date(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("2024-01", "2024-01"), ("2024-1", "2024-01"), (" 2024-1 ", "2024-01")],
)
def test_parse_month_normalizes_to_padded_form(raw, expected):
    assert validators.parse_month(raw) == expected


def test_non_padded_date_transaction_appears_in_monthly_summary(txs, cats, budgets):
    """비패딩 날짜로 저장된 거래가 그 달 요약에서 사라지면 안 된다.

    ``'2024-1-5' <= '2024-01-31'`` 이 문자열 비교에서 **거짓**이라 범위 필터를
    통과하지 못한다. 사용자에게는 "저장은 됐는데 요약에 안 잡히는" 상태로 보인다.
    """
    txs.append(Transaction(id=TransactionId.of(1), type="expense", date="2024-1-5",
                           amount=1000, category="food"))
    summary = BudgetService(txs, budgets).monthly_summary("2024-01")
    assert summary.expense == 1000
    assert summary.has_data is True


def test_search_finds_non_padded_date_transaction(txs, cats, run):
    txs.append(Transaction(id=TransactionId.of(1), type="expense", date="2024-1-5",
                           amount=1000, category="food"))
    result = run("search", "--from", "2024-01-01", "--to", "2024-01-31")
    assert "TX-000001" in result.out


# ============================================================
# 0-2. 예산 월 정규화
# ============================================================


def test_budget_set_with_non_padded_month_is_visible_in_summary(run, add_tx):
    """``budget set --month 2024-1`` 로 넣은 예산이 ``summary --month 2024-01`` 에
    보여야 한다. 같은 달을 가리키는 두 표기가 별개 키가 되면 안 된다."""
    add_tx(date="2024-01-15", amount=5000)
    assert run("budget", "set", "--month", "2024-1", "--amount", "100000").code == 0
    result = run("summary", "--month", "2024-01")
    assert "예산" in result.out


def test_budget_same_month_two_spellings_do_not_coexist(budgets):
    budgets.set("2024-1", 100)
    budgets.set("2024-01", 200)
    stored = [b.month for b in budgets.stream()]
    assert stored == ["2024-01"], f"같은 달이 두 줄로 남았다: {stored}"


# ============================================================
# 0-3. 삭제된 최대 ID 재사용
# ============================================================


def test_deleting_max_id_does_not_reissue_that_id(txs):
    """최대 번호 거래를 지운 뒤 추가하면 **새 번호**가 나와야 한다.

    파일 스캔만으로 시작점을 잡으면 지워진 번호가 다시 최대가 되어, export 한
    CSV 를 skip 정책으로 다시 넣을 때 **다른 거래가 중복으로 판정돼 사라진다**.
    """
    first = txs.next_id()
    txs.append(Transaction(id=first, type="expense", date="2024-01-01",
                           amount=100, category="food"))
    second = txs.next_id()
    txs.append(Transaction(id=second, type="expense", date="2024-01-02",
                           amount=200, category="food"))
    assert txs.delete(second) is True

    third = txs.next_id()
    assert third != second, f"삭제된 id 가 재발급됐다: {third}"


def test_reissued_id_does_not_shadow_a_different_transaction(run, add_tx, tmp_path):
    """0-3 이 실제 데이터 손실로 이어지는 경로 — 왕복 중복 판정이 어긋난다."""
    add_tx(date="2024-01-01", amount=100, memo="첫번째")
    add_tx(date="2024-01-02", amount=200, memo="두번째")
    run("delete", "--id", "TX-000002")
    add_tx(date="2024-01-03", amount=300, memo="세번째")

    out_csv = tmp_path / "dump.csv"
    run("export", "--out", str(out_csv), "--month", "2024-01")
    result = run("import", "--from", str(out_csv))
    # 전부 이미 저장된 거래이므로 중복 2건, 신규 0건이어야 한다.
    assert "imported=0" in result.out


# ============================================================
# 0-4. 카테고리 비교 정규화
# ============================================================


def test_remove_with_whitespace_self_replacement_is_blocked(cats, txs):
    """`` ' etc ' `` 는 정규화하면 ``'etc'`` 자기 자신이다 — 자기 대체 가드를
    우회해 카테고리만 지워지고 거래는 고아가 되면 안 된다."""
    txs.append(Transaction(id=TransactionId.of(1), type="expense", date="2024-01-01",
                           amount=100, category="etc"))
    service = CategoryService(cats, txs)

    with pytest.raises(AppError):
        service.remove("etc", replace_with=" etc ")

    assert cats.exists("etc") is True


def test_no_orphan_transaction_after_category_remove(cats, txs):
    """어떤 경로로 삭제되든, 남은 거래의 카테고리는 반드시 등록돼 있어야 한다."""
    txs.append(Transaction(id=TransactionId.of(1), type="expense", date="2024-01-01",
                           amount=100, category="etc"))
    service = CategoryService(cats, txs)
    try:
        service.remove("etc", replace_with=" etc ")
    except AppError:
        pass

    registered = cats.name_set()
    orphans = [tx.id.value for tx in txs.stream() if tx.category not in registered]
    assert orphans == [], f"등록되지 않은 카테고리를 가리키는 거래: {orphans}"


def test_remove_normalizes_replace_with(cats, txs):
    """대체 카테고리 이름의 앞뒤 공백은 정규화 후 판정돼야 한다."""
    txs.append(Transaction(id=TransactionId.of(1), type="expense", date="2024-01-01",
                           amount=100, category="food"))
    service = CategoryService(cats, txs)
    assert service.remove("food", replace_with="  etc  ") == 1
    assert [tx.category for tx in txs.stream()] == ["etc"]


# ============================================================
# 0-5. TransactionId 정규형
# ============================================================


def test_tx_id_aliases_are_the_same_value():
    """``TX-1`` 과 ``TX-000001`` 은 같은 거래를 가리킨다 — 별개 값이면 안 된다.

    별칭이 공존하면 (1) ``taken`` 집합이 중복을 못 걸러 같은 번호가 두 번 발급되고
    (2) ``order=True`` 가 전제한 "고정 폭이라 문자열 순서 = 숫자 순서"가 깨진다.
    """
    assert TransactionId("TX-1") == TransactionId("TX-000001")


def test_tx_id_normalizes_value():
    assert TransactionId("TX-1").value == "TX-000001"
    assert TransactionId("TX-000001").value == "TX-000001"


def test_tx_id_alias_does_not_duplicate_in_a_set():
    assert len({TransactionId("TX-1"), TransactionId("TX-000001")}) == 1


def test_tx_id_string_order_matches_numeric_order():
    """정렬이 문자열 비교로 이뤄지므로 자릿수가 섞이면 순서가 뒤집힌다."""
    ids = sorted([TransactionId("TX-9"), TransactionId("TX-10")])
    assert [i.number for i in ids] == [9, 10]


def test_lookup_by_alias_finds_the_transaction(txs):
    txs.append(Transaction(id=TransactionId.of(1), type="expense", date="2024-01-01",
                           amount=100, category="food"))
    assert txs.get("TX-1") is not None
