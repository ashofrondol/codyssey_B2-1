"""스모크 테스트 — budget_app 이 최소한 '핵심 경로'를 끝까지 수행하는지 빠르게 확인한다.

dev-env-bootstrap 규약: 프로젝트 루트에 이 파일이 있으면 `make test`
(= scripts/run_tests.sh)가 `uv run python smoke_test.py` 로 자동 실행한다.
실패 시 0이 아닌 종료 코드를 반환한다.

pytest 없이 표준 라이브러리만으로 동작하므로, 의존성이 없는 어떤 환경에서도 돌아간다.

## 다른 사람의 budget_app 에 쓰는 법

    python smoke_test.py                                   # 현재 폴더의 앱
    BUDGET_APP_ROOT=/path/to/app  python smoke_test.py     # 다른 위치의 앱
    BUDGET_APP_MODULE=my_ledger   python smoke_test.py     # 모듈명이 다를 때

내부 구조를 import 하지 않고 `python -m <모듈>` 을 서브프로세스로 구동하므로,
구현이 달라도 CLI 계약만 지키면 통과한다.
"""

from __future__ import annotations

import csv
import io
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

APP_ROOT = Path(os.environ.get("BUDGET_APP_ROOT") or Path(__file__).resolve().parent).resolve()
APP_MODULE = os.environ.get("BUDGET_APP_MODULE") or "budget_app"
TIMEOUT = 60

SEED_CSV = """date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,lunchmemo,meal
2024-01-14,income,salary,3000000,paymemo,
2024-01-20,expense,rent,150000,rentmemo,fixed
"""


class SmokeFailure(AssertionError):
    """스모크 단계 실패 — 어떤 단계가 왜 실패했는지 메시지에 담는다."""


def run(workdir: Path, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(APP_ROOT), env.get("PYTHONPATH", "")]).rstrip(
        os.pathsep
    )
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, "-m", APP_MODULE, *args],
        cwd=str(workdir),
        env=env,
        input="",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIMEOUT,
    )


def out_of(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout or "") + (proc.stderr or "")


def check(cond: bool, step: str, detail: str = "") -> None:
    if not cond:
        raise SmokeFailure(f"[{step}] 실패\n{detail}".rstrip())


def find_opt(help_text: str, candidates: list[str], step: str) -> str:
    """구현마다 다를 수 있는 옵션명을 help 에서 찾는다."""
    for opt in candidates:
        if re.search(rf"(?<![\w-]){re.escape(opt)}(?![\w-])", help_text):
            return opt
    raise SmokeFailure(f"[{step}] 옵션을 help 에서 찾지 못했습니다: {candidates}\n{help_text}")


def smoke(workdir: Path) -> None:
    # 1) 실행 가능성 — help
    proc = run(workdir, "--help")
    check(proc.returncode == 0, "help", out_of(proc))

    # 2) import — 거래 3건 적재
    csv_path = workdir / "seed.csv"
    csv_path.write_text(SEED_CSV, encoding="utf-8")
    from_opt = find_opt(out_of(run(workdir, "import", "--help")), ["--from", "--file", "--in"], "import")
    proc = run(workdir, "import", from_opt, str(csv_path))
    check(proc.returncode == 0, "import", out_of(proc))

    # 3) list — 적재한 데이터가 보이는가 (파일 영속성 확인: 별도 프로세스)
    proc = run(workdir, "list")
    check(proc.returncode == 0, "list", out_of(proc))
    check("lunchmemo" in out_of(proc), "list", f"시드 거래가 목록에 없습니다:\n{out_of(proc)}")

    # 4) summary — 합계 계산
    m_opt = find_opt(out_of(run(workdir, "summary", "--help")), ["--month", "-m"], "summary")
    proc = run(workdir, "summary", m_opt, "2024-01")
    body = re.sub(r"(?<=\d),(?=\d)", "", out_of(proc))  # 3,000,000 → 3000000
    check(proc.returncode == 0, "summary", body)
    check("3000000" in body, "summary", f"총 수입 3000000 이 없습니다:\n{body}")
    check("165000" in body, "summary", f"총 지출 165000 이 없습니다:\n{body}")

    # 5) export — CSV 왕복
    ehelp = out_of(run(workdir, "export", "--help"))
    out_opt = find_opt(ehelp, ["--out", "--to", "--output"], "export")
    target = workdir / "out.csv"
    args = ["export", out_opt, str(target)]
    if re.search(r"(?<![\w-])--month(?![\w-])", ehelp):
        args += ["--month", "2024-01"]
    proc = run(workdir, *args)
    check(proc.returncode == 0, "export", out_of(proc))
    check(target.exists(), "export", f"출력 파일이 없습니다: {target}")

    rows = list(csv.DictReader(io.StringIO(target.read_text(encoding="utf-8"))))
    check(len(rows) == 3, "export", f"import 3건 → export {len(rows)}건 (불일치)")

    # 6) 오류 처리 — 0이 아닌 종료 코드 + 스택트레이스 미노출
    proc = run(workdir, "summary", m_opt, "2024-13")
    check(proc.returncode != 0, "error-handling", f"잘못된 월인데 종료 코드가 0입니다:\n{out_of(proc)}")
    check(
        "Traceback (most recent call last)" not in out_of(proc),
        "error-handling",
        f"스택트레이스가 노출되었습니다:\n{out_of(proc)}",
    )


def main() -> int:
    print(f"[i] 대상: {APP_ROOT}  (모듈: {APP_MODULE})")
    with tempfile.TemporaryDirectory(prefix="budget_smoke_") as tmp:
        try:
            smoke(Path(tmp))
        except SmokeFailure as exc:
            print(f"[FAIL] 스모크 테스트 실패\n{exc}")
            return 1
        except subprocess.TimeoutExpired:
            print("[FAIL] 명령이 응답하지 않습니다(대화형 입력 대기 가능성).")
            return 1
    print("[OK] 스모크 테스트 통과 — help/import/list/summary/export/오류처리 정상")
    return 0


if __name__ == "__main__":
    sys.exit(main())
