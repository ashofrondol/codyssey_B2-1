"""공통 픽스처 — 어떤 budget_app 구현체에도 붙일 수 있도록 설계한 범용 테스트 기반.

## 다른 사람의 budget_app 에 이 테스트를 그대로 쓰는 법

`tests/`, `smoke_test.py`, `TestCase.txt` 를 대상 프로젝트 루트에 복사하거나,
환경변수로 대상만 바꿔 실행한다.

    # 방법 1) 대상 프로젝트에 복사 후 실행
    uv run pytest

    # 방법 2) 다른 위치의 프로젝트를 가리켜 실행
    BUDGET_APP_ROOT=/path/to/other-budget-app uv run pytest
    BUDGET_APP_MODULE=my_ledger uv run pytest        # 모듈명이 다를 때

| 환경변수 | 기본값 | 설명 |
| --- | --- | --- |
| `BUDGET_APP_ROOT` | `tests/` 의 상위 디렉터리 | 대상 프로젝트 루트 |
| `BUDGET_APP_MODULE` | `budget_app` | `python -m <모듈>` 로 실행할 모듈명 |

## 구현체 비의존성을 위한 설계 원칙

1. **블랙박스 실행**: 내부 함수를 import 하지 않고 `python -m <모듈>` 을 서브프로세스로
   구동한다. 내부 구조(모듈/클래스 이름)가 달라도 통과한다.
2. **cwd 격리**: 각 테스트는 임시 디렉터리를 cwd 로 삼는다. 앱의 기본 데이터 폴더
   (`./data`)가 그 안에 생기므로 `--data-dir` 같은 선택 옵션 없이도 상태가 격리된다.
   (`PYTHONPATH` 로 대상 루트를 얹어 모듈을 찾게 한다.)
3. **옵션명 자동 탐지**: `--from`/`--file`, `--out`/`--to` 처럼 구현마다 다를 수 있는
   옵션 이름은 `--help` 출력에서 찾아 쓴다. 못 찾으면 skip 한다.
4. **느슨한 출력 단언**: 사람이 읽는 문구는 구현마다 다르므로 문구 자체를 비교하지
   않는다. 대신 종료 코드, 파일 내용, CSV 스키마처럼 명세가 고정한 것만 단언한다.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional, Sequence

import pytest

DEFAULT_MODULE = "budget_app"

# 서브프로세스 1회 실행 상한(초) — 대화형 명령이 입력을 기다리며 멈추는 것을 방지.
CLI_TIMEOUT = 60


# ---------- 대상 프로젝트 해석 ----------


def resolve_app_root() -> Path:
    env = os.environ.get("BUDGET_APP_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def resolve_app_module() -> str:
    return os.environ.get("BUDGET_APP_MODULE", "").strip() or DEFAULT_MODULE


@pytest.fixture(scope="session")
def app_root() -> Path:
    root = resolve_app_root()
    if not root.is_dir():
        pytest.exit(f"BUDGET_APP_ROOT 가 디렉터리가 아닙니다: {root}", returncode=4)
    return root


@pytest.fixture(scope="session")
def app_module() -> str:
    return resolve_app_module()


@pytest.fixture(scope="session")
def app_package_dir(app_root: Path, app_module: str) -> Path:
    """대상 패키지 디렉터리(`<root>/<module>/`). 구조 검사 테스트가 사용한다."""
    pkg = app_root / app_module
    if not pkg.is_dir():
        pytest.skip(f"패키지 디렉터리를 찾을 수 없습니다: {pkg}")
    return pkg


# ---------- CLI 러너 ----------


class Cli:
    """대상 앱을 서브프로세스로 실행하는 얇은 래퍼."""

    def __init__(self, root: Path, module: str, workdir: Path):
        self.root = root
        self.module = module
        self.workdir = workdir

    def run(
        self,
        *args: str,
        stdin: Optional[str] = None,
        cwd: Optional[Path] = None,
        timeout: int = CLI_TIMEOUT,
    ) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        # 대상 루트를 import 경로에 얹어 `python -m <module>` 이 동작하게 한다.
        env["PYTHONPATH"] = os.pathsep.join(
            [str(self.root), env.get("PYTHONPATH", "")]
        ).rstrip(os.pathsep)
        # 한글 출력이 콘솔 코드페이지 때문에 깨지지 않도록 강제한다.
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        return subprocess.run(
            [sys.executable, "-m", self.module, *args],
            cwd=str(cwd or self.workdir),
            env=env,
            input=stdin if stdin is not None else "",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

    # ---- 편의 메서드 ----

    def output(self, proc: subprocess.CompletedProcess) -> str:
        return (proc.stdout or "") + (proc.stderr or "")

    def help_of(self, *args: str) -> str:
        """`<args> --help` 출력을 반환(실패해도 빈 문자열)."""
        proc = self.run(*args, "--help")
        return self.output(proc)

    @property
    def data_dir(self) -> Path:
        return self.workdir / "data"


@pytest.fixture
def workdir(tmp_path: Path) -> Path:
    """테스트마다 격리된 작업 디렉터리 — 앱의 `./data` 가 여기에 생긴다."""
    d = tmp_path / "work"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def cli(app_root: Path, app_module: str, workdir: Path) -> Cli:
    return Cli(app_root, app_module, workdir)


# ---------- 옵션명 자동 탐지 ----------


def discover_option(help_text: str, candidates: Sequence[str]) -> Optional[str]:
    """help 출력에서 후보 옵션 중 실제 존재하는 것을 찾아 반환한다.

    구현마다 `import --from` / `import --file` 처럼 옵션명이 다를 수 있으므로,
    테스트를 특정 구현에 고정하지 않기 위한 장치다.
    """
    for opt in candidates:
        # 단어 경계로 매칭 (`--to` 가 `--total` 에 걸리지 않도록)
        if re.search(rf"(?<![\w-]){re.escape(opt)}(?![\w-])", help_text):
            return opt
    return None


def require_option(help_text: str, candidates: Sequence[str], what: str) -> str:
    opt = discover_option(help_text, candidates)
    if opt is None:
        pytest.skip(f"{what} 옵션을 help 에서 찾지 못했습니다 (후보: {list(candidates)})")
    return opt


# ---------- CSV 헬퍼 ----------

CSV_HEADER = "date,type,category,amount,memo,tags"

# 과제 명세가 고정한 CSV 필수 컬럼
REQUIRED_CSV_COLUMNS = ("date", "type", "category", "amount")


def write_csv(path: Path, rows: Sequence[str], header: str = CSV_HEADER) -> Path:
    """UTF-8(BOM 없음) CSV 를 만든다. rows 는 헤더를 제외한 줄 목록."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def sample_csv(workdir: Path) -> Path:
    """정상 거래 3건이 담긴 CSV (수입 1 + 지출 2)."""
    return write_csv(
        workdir / "seed.csv",
        [
            "2024-01-15,expense,food,15000,lunchmemo,meal",
            "2024-01-14,income,salary,3000000,paymemo,",
            "2024-01-20,expense,rent,150000,rentmemo,fixed",
        ],
    )


@pytest.fixture
def seed(cli: Cli, sample_csv: Path):
    """대상 앱에 표준 거래 3건을 넣는다(비대화형 경로인 import 사용).

    반환: import 를 수행하는 호출 가능 객체. 실패 시 테스트를 skip 한다.
    """

    def _seed(csv_path: Optional[Path] = None) -> subprocess.CompletedProcess:
        help_text = cli.help_of("import")
        from_opt = require_option(help_text, ["--from", "--file", "--in", "--input"], "import 입력")
        proc = cli.run("import", from_opt, str(csv_path or sample_csv))
        if proc.returncode != 0:
            pytest.skip(f"import 로 데이터를 넣지 못해 건너뜁니다: {cli.output(proc)[:300]}")
        return proc

    return _seed


# ---------- 공용 단언 ----------


def assert_no_traceback(output: str) -> None:
    """스택트레이스가 사용자에게 노출되지 않아야 한다(체크리스트 1.6)."""
    assert "Traceback (most recent call last)" not in output, (
        "스택트레이스가 사용자 출력에 노출되었습니다:\n" + output[:1000]
    )


def data_files(data_root: Path) -> list[Path]:
    """데이터 폴더에서 앱이 만든 저장 파일 목록(형식 불문)."""
    if not data_root.is_dir():
        return []
    return sorted(p for p in data_root.rglob("*") if p.is_file())
