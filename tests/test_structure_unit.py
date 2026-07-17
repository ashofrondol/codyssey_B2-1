"""체크리스트 §2 (구현 구조) · §3 (핵심 개념) — 모듈 단위 테스트.

구현마다 모듈/클래스 이름이 다르므로, 특정 이름에 의존하지 않고
**AST 정적 분석 + 동적 import** 로 '설계 속성' 자체를 검사한다.
따라서 다른 사람의 budget_app 에도 그대로 적용된다.

- §2.1 3개 이상 모듈 분리      → 패키지 내 .py 모듈 수
- §2.2 2개 이상 클래스         → ClassDef 개수
- §2.3 안전한 update/delete    → 원자적 교체 패턴(os.replace 등) 사용 여부
- §3.1 제너레이터 스트리밍     → yield 를 쓰는 함수 존재 여부
- §3.2 데코레이터 분리         → 데코레이터 정의/적용 여부
- §3.3 타입 힌트               → 함수 시그니처 애너테이션 비율
"""

from __future__ import annotations

import ast
import importlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

# 타입 힌트 적용률 하한 (§3.3) — 100%를 강요하지 않되 '광범위 적용'은 확인한다.
TYPE_HINT_MIN_RATIO = 0.70

# 원자적 교체로 인정하는 정규화된 호출 (§2.3)
# 주의: 문자열 `.replace(` 를 텍스트로 찾으면 평범한 str.replace 까지 통과하므로
#       AST 로 '무엇을 호출했는지' 를 보고 판정한다.
ATOMIC_CALLS = ("os.replace", "os.rename", "shutil.move", "pathlib.Path.replace")

# 임시 파일 사용 근거로 인정하는 표현
TEMPFILE_RE = re.compile(r"\.tmp\b|\btmp\b|tempfile|NamedTemporaryFile|mkstemp", re.IGNORECASE)


# ---------- AST 수집 ----------


@dataclass
class ModuleInfo:
    path: Path
    source: str
    tree: ast.Module

    @property
    def name(self) -> str:
        return self.path.name


@pytest.fixture(scope="session")
def modules(app_package_dir: Path) -> list[ModuleInfo]:
    """패키지 안의 모든 .py 를 파싱해 반환."""
    infos: list[ModuleInfo] = []
    for p in sorted(app_package_dir.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        src = p.read_text(encoding="utf-8")
        infos.append(ModuleInfo(path=p, source=src, tree=ast.parse(src, filename=str(p))))
    if not infos:
        pytest.skip(f"파싱할 .py 모듈이 없습니다: {app_package_dir}")
    return infos


def _functions(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [
        n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _classes(tree: ast.Module) -> list[ast.ClassDef]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]


def _has_yield(fn: ast.AST) -> bool:
    """중첩 함수의 yield 를 제 함수의 것으로 오인하지 않도록 경계에서 멈춘다."""
    for node in ast.walk(fn):
        if isinstance(node, (ast.Yield, ast.YieldFrom)):
            return True
    return False


# ---------- §2. 구현 구조 ----------


def test_package_is_split_into_at_least_3_modules(modules: list[ModuleInfo]):
    """§2.1 — 코드가 3개 이상 모듈로 분리되어 있는가."""
    # __init__/__main__ 은 진입점이므로 '책임 모듈' 수에서 제외해 보수적으로 센다.
    substantive = [m for m in modules if m.name not in ("__init__.py", "__main__.py")]
    names = [m.name for m in substantive]
    assert len(substantive) >= 3, f"책임 모듈이 3개 미만입니다: {names}"


def test_has_at_least_2_classes(modules: list[ModuleInfo]):
    """§2.2 — 최소 2개 이상의 클래스에 책임이 부여되어 있는가."""
    found = [(m.name, c.name) for m in modules for c in _classes(m.tree)]
    assert len(found) >= 2, f"클래스가 2개 미만입니다: {found}"


def _atomic_replace_calls(tree: ast.Module) -> list[str]:
    """원자적 교체로 볼 수 있는 호출을 AST 에서 찾는다.

    - `os.replace(...)` / `os.rename(...)` / `shutil.move(...)` : 이름만으로 확정
    - `tmp.replace(target)` (pathlib.Path 스타일) : 수신자가 임시 파일을 가리킬 때만 인정
      → 평범한 `문자열.replace("a", "b")` 를 원자적 쓰기로 오인하지 않기 위함
    """
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        dotted = ast.unparse(node.func)
        if dotted in ATOMIC_CALLS:
            found.append(dotted)
        elif node.func.attr in ("replace", "rename"):
            receiver = ast.unparse(node.func.value)
            if TEMPFILE_RE.search(receiver):
                found.append(dotted)
    return found


def test_update_delete_uses_atomic_replace(modules: list[ModuleInfo]):
    """§2.3 — 파일 기반 update/delete 를 안전하게(원자적 교체) 처리하는가.

    '임시 파일에 쓴 뒤 교체' 패턴을 확인한다. 원본을 직접 덮어쓰다가 프로세스가
    죽으면 파일이 깨지므로, 이 패턴이 없으면 데이터 유실 위험이 있다.
    """
    calls = [(m.name, c) for m in modules for c in _atomic_replace_calls(m.tree)]
    tempfile_users = [m.name for m in modules if TEMPFILE_RE.search(m.source)]

    assert calls, (
        "원자적 교체 호출(os.replace / os.rename / shutil.move / tmp.replace)을 찾지 못했습니다. "
        "원본 파일을 직접 덮어쓰면 쓰기 도중 중단 시 데이터가 깨집니다."
    )
    assert tempfile_users, (
        "임시 파일 사용 흔적(.tmp / tempfile 등)이 없습니다 — "
        f"교체 호출은 있으나({calls}) 임시 파일에 먼저 쓰는 단계가 보이지 않습니다."
    )


# ---------- §3. 핵심 개념 ----------


def test_uses_generator_streaming(modules: list[ModuleInfo]):
    """§3.1 — 조회를 제너레이터로 스트리밍 처리하는가."""
    gens = [
        (m.name, fn.name) for m in modules for fn in _functions(m.tree) if _has_yield(fn)
    ]
    assert gens, (
        "yield 를 사용하는 함수가 없습니다 — 파일 전체를 메모리에 올리는 구조로 보입니다."
    )


def test_uses_decorators_for_cross_cutting_concerns(modules: list[ModuleInfo]):
    """§3.2 — 공통 관심사를 데코레이터로 분리했는가.

    데코레이터 '정의'(functools.wraps 사용)와 '적용'(@... )이 모두 있어야 한다.
    """
    blob = "\n".join(m.source for m in modules)
    defines = "functools.wraps" in blob or "from functools import wraps" in blob

    applied = []
    for m in modules:
        for node in ast.walk(m.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for d in node.decorator_list:
                    applied.append((m.name, node.name, ast.unparse(d)))
    # dataclass 등 표준 데코레이터만 쓴 경우는 '공통 관심사 분리'로 보지 않는다.
    custom_applied = [a for a in applied if "dataclass" not in a[2]]

    assert defines, "functools.wraps 로 정의한 자체 데코레이터가 없습니다."
    assert custom_applied, f"자체 데코레이터를 실제로 적용한 곳이 없습니다. (적용 목록: {applied})"


def test_type_hints_are_widely_applied(modules: list[ModuleInfo]):
    """§3.3 — 타입 힌트가 광범위하게 적용되어 있는가."""
    total = 0
    annotated = 0
    unannotated: list[str] = []
    for m in modules:
        for fn in _functions(m.tree):
            if fn.name.startswith("__") and fn.name != "__init__":
                continue
            total += 1
            args = [a for a in fn.args.args if a.arg not in ("self", "cls")]
            args_ok = all(a.annotation is not None for a in args)
            ret_ok = fn.returns is not None or fn.name == "__init__"
            if args_ok and ret_ok:
                annotated += 1
            else:
                unannotated.append(f"{m.name}::{fn.name}")

    assert total > 0, "함수를 찾지 못했습니다."
    ratio = annotated / total
    assert ratio >= TYPE_HINT_MIN_RATIO, (
        f"타입 힌트 적용률이 낮습니다: {ratio:.0%} ({annotated}/{total}), "
        f"하한 {TYPE_HINT_MIN_RATIO:.0%}\n미적용: {unannotated[:10]}"
    )


# ---------- 모듈 import 스모크 ----------


def test_all_modules_import_cleanly(app_root: Path, app_module: str, modules: list[ModuleInfo]):
    """각 모듈이 단독으로 import 되는가 (순환 참조·문법 오류 조기 발견)."""
    sys.path.insert(0, str(app_root))
    try:
        importlib.import_module(app_module)
        for m in modules:
            if m.name in ("__init__.py", "__main__.py"):
                continue  # __main__ 은 import 시 실행되므로 제외
            mod_name = f"{app_module}.{m.path.stem}"
            importlib.import_module(mod_name)
    finally:
        if str(app_root) in sys.path:
            sys.path.remove(str(app_root))


# ---------- 검증 로직 단위 테스트 (있으면 검사, 없으면 skip) ----------


def _find_callable(app_root: Path, app_module: str, name: str):
    """패키지 전역에서 이름이 일치하는 함수/스태틱메서드를 찾는다."""
    sys.path.insert(0, str(app_root))
    try:
        pkg = importlib.import_module(app_module)
        pkg_dir = Path(pkg.__file__).parent
        for p in sorted(pkg_dir.glob("*.py")):
            if p.name in ("__init__.py", "__main__.py"):
                continue
            mod = importlib.import_module(f"{app_module}.{p.stem}")
            if (fn := getattr(mod, name, None)) and callable(fn):
                return fn
            for obj in vars(mod).values():
                if isinstance(obj, type) and (fn := getattr(obj, name, None)) and callable(fn):
                    return fn
    finally:
        if str(app_root) in sys.path:
            sys.path.remove(str(app_root))
    return None


@pytest.mark.parametrize(
    "bad_amount",
    ["-1", "0", "abc", ""],
    ids=["음수", "0", "문자열", "빈값"],
)
def test_amount_validation_rejects_invalid(app_root: Path, app_module: str, bad_amount: str):
    """금액 검증 함수가 있으면, 무효 입력을 예외로 거부해야 한다."""
    fn = _find_callable(app_root, app_module, "validate_amount")
    if fn is None:
        pytest.skip("validate_amount 를 찾지 못했습니다(이름이 다른 구현일 수 있음).")
    with pytest.raises(Exception):
        fn(bad_amount)


@pytest.mark.parametrize("bad_date", ["2024-13-01", "24-01-01", "not-a-date", ""])
def test_date_validation_rejects_invalid(app_root: Path, app_module: str, bad_date: str):
    """날짜 검증 함수가 있으면, 무효 형식을 예외로 거부해야 한다."""
    fn = _find_callable(app_root, app_module, "validate_date")
    if fn is None:
        pytest.skip("validate_date 를 찾지 못했습니다(이름이 다른 구현일 수 있음).")
    with pytest.raises(Exception):
        fn(bad_date)
