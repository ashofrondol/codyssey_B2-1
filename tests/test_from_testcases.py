"""`TestCase.txt` 를 읽어 CLI 종료 코드 계약을 파라미터화 테스트로 생성한다.

dev-env-bootstrap 템플릿의 `함수인자 => 기대값` 규약을 CLI 애플리케이션에 맞게
확장했다(템플릿 README 의 "파서는 정수 인자 예시 기준이니 필요하면 확장하라" 지침).

형식:
    <서브커맨드와 옵션...>  =>  <기대 종료코드>     # 예: list => 0
    <서브커맨드와 옵션...>  =>  !0                  # 0이 아닌 값(오류)

케이스를 늘리고 싶으면 파이썬을 건드리지 말고 `TestCase.txt` 에 줄만 추가하면 된다.
"""

from __future__ import annotations

import pathlib
import shlex

import pytest

from conftest import Cli, assert_no_traceback

TESTCASE_FILENAME = "TestCase.txt"


def _testcase_path() -> pathlib.Path:
    """TestCase.txt 위치 — 대상 프로젝트 루트 우선, 없으면 이 테스트의 상위."""
    from conftest import resolve_app_root

    candidates = [
        resolve_app_root() / TESTCASE_FILENAME,
        pathlib.Path(__file__).resolve().parent.parent / TESTCASE_FILENAME,
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def _load_cases() -> list[tuple[list[str], str]]:
    """(CLI 인자 목록, 기대값) 튜플 목록을 반환."""
    path = _testcase_path()
    if not path.exists():
        return []
    cases: list[tuple[list[str], str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=>" not in line:
            continue
        left, expected = line.split("=>", 1)
        args = shlex.split(left.strip())
        if not args:
            continue
        cases.append((args, expected.strip()))
    return cases


_CASES = _load_cases()


def _case_id(case: tuple[list[str], str]) -> str:
    args, expected = case
    return f"{' '.join(args)} => {expected}"


@pytest.mark.skipif(not _CASES, reason=f"{TESTCASE_FILENAME} 에 유효한 케이스가 없습니다.")
@pytest.mark.parametrize("case", _CASES, ids=[_case_id(c) for c in _CASES])
def test_cli_exit_code_contract(cli: Cli, case: tuple[list[str], str]):
    args, expected = case
    proc = cli.run(*args)
    out = cli.output(proc)

    # 어떤 케이스든 스택트레이스가 사용자에게 보여선 안 된다.
    assert_no_traceback(out)

    if expected == "!0":
        assert proc.returncode != 0, (
            f"`{' '.join(args)}` 는 오류로 끝나야 하는데 종료 코드가 0입니다.\n{out}"
        )
    else:
        assert proc.returncode == int(expected), (
            f"`{' '.join(args)}` 기대 종료 코드 {expected}, 실제 {proc.returncode}\n{out}"
        )
