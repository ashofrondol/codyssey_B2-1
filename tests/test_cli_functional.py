"""체크리스트 §1 (기능 동작 검증) — CLI 를 블랙박스로 구동하는 계약 테스트.

구현 내부를 import 하지 않으므로 다른 사람의 budget_app 에도 그대로 쓸 수 있다.
사람이 읽는 문구는 구현마다 다르므로 단언하지 않고, 명세가 고정한 것
(종료 코드 / 저장 파일 / CSV 스키마 / 데이터 보존)만 단언한다.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

import pytest

from conftest import (
    REQUIRED_CSV_COLUMNS,
    Cli,
    assert_no_traceback,
    data_files,
    discover_option,
    require_option,
    write_csv,
)

# 체크리스트가 요구하는 명령 집합
REQUIRED_COMMANDS = ("add", "list", "search", "summary", "export", "import", "update", "delete")

# 시드 데이터(sample_csv)에서 파생되는 기대값
SEED_INCOME = 3000000
SEED_EXPENSE = 165000  # 15000 + 150000
SEED_MONTH = "2024-01"


def norm(text: str) -> str:
    """금액 표기 차이를 흡수한다: '3,000,000' → '3000000'."""
    return re.sub(r"(?<=\d),(?=\d)", "", text)


def first_tx_id(text: str) -> str | None:
    """목록 출력에서 거래 ID 로 보이는 첫 토큰을 찾는다.

    'TX-000001' 처럼 <접두어>-<숫자> 형태를 가정한다(가장 흔한 관례).
    못 찾으면 None → 호출 측에서 skip 한다.
    """
    m = re.search(r"\b([A-Za-z]{1,6}-\d{1,12})\b", text)
    return m.group(1) if m else None


# ---------- 1.1 명령 존재 및 동작 ----------


@pytest.mark.contract
def test_help_lists_required_commands(cli: Cli):
    """add/list/search/summary/export/import/update/delete 가 모두 노출되는가."""
    proc = cli.run("--help")
    out = cli.output(proc)
    assert proc.returncode == 0, f"--help 가 실패했습니다:\n{out}"
    missing = [c for c in REQUIRED_COMMANDS if not re.search(rf"(?<![\w-]){c}(?![\w-])", out)]
    assert not missing, f"help 에 노출되지 않은 필수 명령: {missing}\n{out}"


@pytest.mark.contract
def test_list_runs_and_shows_seeded_data(cli: Cli, seed):
    seed()
    proc = cli.run("list")
    out = cli.output(proc)
    assert proc.returncode == 0, f"list 실패:\n{out}"
    assert_no_traceback(out)
    assert "lunchmemo" in out, f"list 출력에 시드 거래가 보이지 않습니다:\n{out}"


@pytest.mark.contract
def test_search_filters_by_category(cli: Cli, seed):
    seed()
    opt = require_option(cli.help_of("search"), ["--category", "--cat"], "search 카테고리")
    proc = cli.run("search", opt, "food")
    out = cli.output(proc)
    assert proc.returncode == 0, f"search 실패:\n{out}"
    assert_no_traceback(out)
    assert "lunchmemo" in out, f"food 카테고리 거래가 검색되지 않았습니다:\n{out}"
    assert "rentmemo" not in out, f"필터가 적용되지 않아 rent 거래까지 나왔습니다:\n{out}"


@pytest.mark.contract
def test_summary_reports_income_and_expense(cli: Cli, seed):
    seed()
    opt = require_option(cli.help_of("summary"), ["--month", "-m"], "summary 월")
    proc = cli.run("summary", opt, SEED_MONTH)
    out = norm(cli.output(proc))
    assert proc.returncode == 0, f"summary 실패:\n{out}"
    assert_no_traceback(out)
    assert str(SEED_INCOME) in out, f"총 수입 {SEED_INCOME} 이 보이지 않습니다:\n{out}"
    assert str(SEED_EXPENSE) in out, f"총 지출 {SEED_EXPENSE} 가 보이지 않습니다:\n{out}"


@pytest.mark.optional
def test_add_interactive_persists_transaction(cli: Cli, seed):
    """add 대화형 입력 — 프롬프트 순서는 구현마다 다를 수 있어 optional 로 둔다.

    명세 순서(날짜→타입→카테고리→금액→메모→태그)로 입력해 성공하면,
    '실제로 저장되었는지' 를 강하게 검증한다.
    """
    seed()  # 카테고리(food)가 등록된 상태를 만든다
    stdin = "2024-03-01\nexpense\nfood\n77777\naddedmemo\n\n"
    proc = cli.run("add", stdin=stdin)
    out = cli.output(proc)
    assert_no_traceback(out)
    if proc.returncode != 0:
        pytest.skip(f"대화형 add 의 프롬프트 순서가 명세와 다른 것으로 보입니다 (rc={proc.returncode})")
    listed = norm(cli.output(cli.run("list")))
    assert "77777" in listed, f"add 로 넣은 거래가 목록에 없습니다:\n{listed}"


# ---------- 1.2 영속성 ----------


@pytest.mark.contract
def test_data_persists_across_process_restarts(cli: Cli, seed):
    """별개 프로세스로 다시 실행해도 데이터가 유지되는가 (저장 파일 3개 이상)."""
    seed()
    # 완전히 새로운 프로세스에서 조회 — 메모리 상태가 아닌 파일에서 읽어야 통과한다.
    proc = cli.run("list")
    out = cli.output(proc)
    assert proc.returncode == 0, f"재실행 list 실패:\n{out}"
    assert "lunchmemo" in out, "재실행 후 거래 데이터가 유지되지 않았습니다."

    files = data_files(cli.data_dir)
    assert len(files) >= 3, (
        f"저장 파일이 3개 미만입니다(거래/카테고리/예산 분리 필요): "
        f"{[f.name for f in files]}"
    )


# ---------- 1.3 카테고리 ----------


@pytest.mark.contract
def test_category_add_list_remove(cli: Cli):
    add_opt = require_option(cli.help_of("category", "add"), ["--name", "-n"], "category add 이름")
    assert cli.run("category", "add", add_opt, "groceries").returncode == 0

    listed = cli.output(cli.run("category", "list"))
    assert "groceries" in listed, f"추가한 카테고리가 목록에 없습니다:\n{listed}"

    rem_opt = require_option(
        cli.help_of("category", "remove"), ["--name", "-n"], "category remove 이름"
    )
    proc = cli.run("category", "remove", rem_opt, "groceries")
    assert proc.returncode == 0, f"미사용 카테고리 삭제 실패:\n{cli.output(proc)}"
    assert "groceries" not in cli.output(cli.run("category", "list"))


@pytest.mark.contract
def test_category_remove_in_use_never_loses_data(cli: Cli, seed):
    """사용 중 카테고리 삭제 시 데이터가 소실되지 않아야 한다.

    정책은 구현 자유(차단 / 재지정 요구)지만, 어느 쪽이든
    '거래가 조용히 사라지는' 결과는 허용하지 않는다.
    """
    seed()
    before = cli.output(cli.run("list"))
    assert "lunchmemo" in before

    rem_opt = require_option(
        cli.help_of("category", "remove"), ["--name", "-n"], "category remove 이름"
    )
    proc = cli.run("category", "remove", rem_opt, "food")  # food 는 사용 중
    out = cli.output(proc)
    assert_no_traceback(out)

    after = cli.output(cli.run("list"))
    assert "lunchmemo" in after, (
        "사용 중 카테고리를 삭제하면서 거래가 사라졌습니다. "
        "차단하거나 대체 카테고리로 재지정해야 합니다.\n" + out
    )
    if proc.returncode == 0:
        # 삭제를 허용했다면 재지정 등으로 처리했어야 한다 → 목록에서 사라져야 함
        assert "food" not in cli.output(cli.run("category", "list")), (
            "삭제 성공(rc=0)이라면서 카테고리가 그대로 남아 있습니다."
        )


# ---------- 1.4 예산 ----------


@pytest.mark.contract
def test_budget_set_and_summary_shows_usage(cli: Cli, seed):
    seed()
    bhelp = cli.help_of("budget", "set")
    m_opt = require_option(bhelp, ["--month", "-m"], "budget 월")
    a_opt = require_option(bhelp, ["--amount", "-a"], "budget 금액")
    proc = cli.run("budget", "set", m_opt, SEED_MONTH, a_opt, "500000")
    assert proc.returncode == 0, f"budget set 실패:\n{cli.output(proc)}"

    s_opt = require_option(cli.help_of("summary"), ["--month", "-m"], "summary 월")
    out = norm(cli.output(cli.run("summary", s_opt, SEED_MONTH)))
    assert "500000" in out, f"summary 에 예산액이 보이지 않습니다:\n{out}"
    # 165000 / 500000 = 33.0%
    assert "33" in out, f"summary 에 예산 사용률(33%)이 보이지 않습니다:\n{out}"


@pytest.mark.contract
def test_summary_warns_when_over_budget(cli: Cli, seed):
    seed()
    bhelp = cli.help_of("budget", "set")
    m_opt = require_option(bhelp, ["--month", "-m"], "budget 월")
    a_opt = require_option(bhelp, ["--amount", "-a"], "budget 금액")
    # 지출 165000 > 예산 100000 → 초과
    assert cli.run("budget", "set", m_opt, SEED_MONTH, a_opt, "100000").returncode == 0

    s_opt = require_option(cli.help_of("summary"), ["--month", "-m"], "summary 월")
    out = norm(cli.output(cli.run("summary", s_opt, SEED_MONTH)))
    assert re.search(r"초과|경고|over|exceed", out, re.IGNORECASE), (
        f"예산 초과 상황인데 초과/경고 표시가 없습니다:\n{out}"
    )


# ---------- 1.5 CSV 스키마 ----------


@pytest.mark.contract
def test_export_csv_is_utf8_with_header_and_columns(cli: Cli, seed, workdir: Path):
    seed()
    ehelp = cli.help_of("export")
    out_opt = require_option(ehelp, ["--out", "--to", "--file", "--output"], "export 출력")
    target = workdir / "export_check.csv"

    # 기간 조건을 필수로 요구하는 구현을 위해 --month 가 있으면 함께 준다.
    args = ["export", out_opt, str(target)]
    if (month_opt := discover_option(ehelp, ["--month"])) is not None:
        args += [month_opt, SEED_MONTH]
    proc = cli.run(*args)
    out = cli.output(proc)
    assert proc.returncode == 0, f"export 실패:\n{out}"
    assert target.exists(), f"export 파일이 생성되지 않았습니다: {target}"

    raw = target.read_bytes()
    # UTF-8 로 디코드되어야 한다.
    text = raw.decode("utf-8")  # UnicodeDecodeError 면 테스트 실패
    reader = csv.DictReader(io.StringIO(text))
    fields = [f.lstrip("﻿") for f in (reader.fieldnames or [])]
    assert fields, "CSV 에 헤더가 없습니다."
    missing = [c for c in REQUIRED_CSV_COLUMNS if c not in fields]
    assert not missing, f"CSV 헤더에 필수 컬럼이 없습니다: {missing} (실제: {fields})"

    rows = list(reader)
    assert len(rows) >= 1, "export 결과에 데이터 행이 없습니다."


@pytest.mark.contract
def test_import_export_roundtrip_preserves_rows(cli: Cli, seed, workdir: Path):
    """import 한 3건이 export 로 그대로 나와야 한다(왕복 안전성)."""
    seed()
    ehelp = cli.help_of("export")
    out_opt = require_option(ehelp, ["--out", "--to", "--file", "--output"], "export 출력")
    target = workdir / "roundtrip.csv"

    args = ["export", out_opt, str(target)]
    if (month_opt := discover_option(ehelp, ["--month"])) is not None:
        args += [month_opt, SEED_MONTH]
    assert cli.run(*args).returncode == 0

    rows = list(csv.DictReader(io.StringIO(target.read_text(encoding="utf-8"))))
    assert len(rows) == 3, f"import 3건 → export {len(rows)}건 (건수 불일치)"
    amounts = sorted(int(r["amount"]) for r in rows)
    assert amounts == [15000, 150000, 3000000], f"금액이 보존되지 않았습니다: {amounts}"


# ---------- 1.6 / 1.7 오류 처리와 종료 코드 ----------


@pytest.mark.contract
def test_invalid_argument_exits_nonzero_without_traceback(cli: Cli):
    """잘못된 입력 → 스택트레이스 없이 0이 아닌 종료 코드."""
    opt = require_option(cli.help_of("summary"), ["--month", "-m"], "summary 월")
    proc = cli.run("summary", opt, "2024-13")  # 13월은 존재하지 않음
    out = cli.output(proc)
    assert_no_traceback(out)
    assert proc.returncode != 0, f"잘못된 월인데 종료 코드가 0입니다:\n{out}"


@pytest.mark.contract
def test_missing_file_exits_nonzero_without_traceback(cli: Cli, workdir: Path):
    """존재하지 않는 파일 → 스택트레이스 없이 0이 아닌 종료 코드."""
    opt = require_option(cli.help_of("import"), ["--from", "--file", "--in", "--input"], "import 입력")
    proc = cli.run("import", opt, str(workdir / "does_not_exist.csv"))
    out = cli.output(proc)
    assert_no_traceback(out)
    assert proc.returncode != 0, f"없는 파일인데 종료 코드가 0입니다:\n{out}"


@pytest.mark.contract
def test_error_output_gives_a_hint(cli: Cli):
    """오류 시 원인만이 아니라 해결 힌트를 제시하는가(체크리스트 1.6).

    문구는 구현마다 다르므로 '힌트/hint/확인/사용법' 류의 안내가 있는지만 본다.
    """
    opt = require_option(cli.help_of("summary"), ["--month", "-m"], "summary 월")
    out = cli.output(cli.run("summary", opt, "2024-13"))
    assert re.search(r"힌트|hint|확인|usage|사용법|예:", out, re.IGNORECASE), (
        f"오류 출력에 해결 힌트가 없습니다:\n{out}"
    )


@pytest.mark.contract
def test_delete_unknown_id_exits_nonzero(cli: Cli, seed):
    seed()
    opt = require_option(cli.help_of("delete"), ["--id", "-i"], "delete id")
    proc = cli.run("delete", opt, "NOPE-999999")
    out = cli.output(proc)
    assert_no_traceback(out)
    assert proc.returncode != 0, f"없는 id 삭제인데 종료 코드가 0입니다:\n{out}"


# ---------- update / delete ----------


@pytest.mark.contract
def test_update_changes_field_and_persists(cli: Cli, seed):
    seed()
    listed = cli.output(cli.run("list"))
    tx_id = first_tx_id(listed)
    if tx_id is None:
        pytest.skip(f"목록에서 거래 ID 형식(<접두어>-<숫자>)을 찾지 못했습니다:\n{listed}")

    uhelp = cli.help_of("update")
    id_opt = require_option(uhelp, ["--id", "-i"], "update id")
    amt_opt = require_option(uhelp, ["--amount", "-a"], "update 금액")
    proc = cli.run("update", id_opt, tx_id, amt_opt, "24680")
    out = cli.output(proc)
    assert proc.returncode == 0, f"update 실패:\n{out}"
    assert_no_traceback(out)

    after = norm(cli.output(cli.run("list")))
    assert "24680" in after, f"update 한 금액이 반영되지 않았습니다:\n{after}"


@pytest.mark.contract
def test_delete_removes_transaction(cli: Cli, seed):
    seed()
    tx_id = first_tx_id(cli.output(cli.run("list")))
    if tx_id is None:
        pytest.skip("목록에서 거래 ID 를 찾지 못했습니다.")

    opt = require_option(cli.help_of("delete"), ["--id", "-i"], "delete id")
    proc = cli.run("delete", opt, tx_id)
    assert proc.returncode == 0, f"delete 실패:\n{cli.output(proc)}"

    after = cli.output(cli.run("list"))
    assert tx_id not in after, f"삭제한 거래가 목록에 남아 있습니다:\n{after}"


# ---------- §4.3 깨진 CSV 처리 정책 ----------


@pytest.mark.contract
def test_import_with_broken_rows_is_consistent(cli: Cli, workdir: Path):
    """깨진 행이 섞인 CSV 는 '부분 성공' 또는 '전수 롤백' 중 하나로 일관되게 처리되어야 한다.

    어떤 정책이든 허용하되, 다음은 공통으로 요구한다:
      - 스택트레이스를 노출하지 않는다
      - 성공(rc=0)이면 유효 행은 저장되고, 실패(rc!=0)면 아무것도 저장되지 않는다
        (= 어중간하게 일부만 남고 실패로 보고하는 상태를 금지)
    """
    csv_path = write_csv(
        workdir / "broken.csv",
        [
            "2024-05-01,expense,food,5000,goodrow,",
            "2024-05-02,expense,food,-3,brokenrow,",  # 음수 금액 → 무효
            "2024-05-03,income,salary,7000,goodrow2,",
        ],
    )
    opt = require_option(cli.help_of("import"), ["--from", "--file", "--in", "--input"], "import 입력")
    proc = cli.run("import", opt, str(csv_path))
    out = cli.output(proc)
    assert_no_traceback(out)

    listed = cli.output(cli.run("list"))
    good_saved = "goodrow" in listed
    broken_saved = "brokenrow" in listed

    assert not broken_saved, f"무효한 행(-3원)이 저장되었습니다:\n{listed}"

    if proc.returncode == 0:
        # 부분 성공 정책 — 유효 행은 저장되고, 건너뛴 사실이 보고되어야 한다
        assert good_saved, f"부분 성공(rc=0)인데 유효 행이 저장되지 않았습니다:\n{listed}"
        assert re.search(r"skip|건너|무시|오류|error|실패", out, re.IGNORECASE), (
            f"건너뛴 행에 대한 리포트가 없습니다:\n{out}"
        )
    else:
        # 전수 롤백 정책 — 아무것도 남지 않아야 한다
        assert not good_saved, (
            f"실패(rc={proc.returncode})로 보고했지만 일부 행이 저장되어 있습니다"
            f"(부분 반영 상태 = 롤백 실패):\n{listed}"
        )
