# 테스트 보고서 — budget_app

| 항목 | 값 |
| --- | --- |
| 대상 | `codyssey_B2-1` (파일 기반 가계부 콘솔 프로그램) |
| 실행일 | 2026-07-16 |
| 환경 구축 | `DevEnvAuto/dev-env-bootstrap` 스택 (uv · pytest) |
| 결과 | **자동화 테스트 46건 통과, 스모크 테스트 통과, 실패 0** |
| 신뢰성 검증 | 뮤테이션 4종 주입 → **4종 모두 검출** |

체크리스트 항목별 대응은 [CHECKLIST_VERIFICATION.md](CHECKLIST_VERIFICATION.md) 참고.

---

## 1. 개발환경 구축

### 1.1 사용한 경로와 제약

`dev-env-bootstrap` 은 **`make` + WSL2** 를 전제로 한다. 이 머신에서는 그 경로를
그대로 쓸 수 없어 **도구의 실제 스택과 스크립트를 직접 호출**하는 방식으로 구축했다.

| 확인 항목 | 결과 | 영향 |
| --- | --- | --- |
| `make` | **없음** (Git Bash / Windows 네이티브) | `make setup`·`make project`·`make test` 직접 실행 불가 |
| WSL2 배포판 | `docker-desktop`, `docker-desktop-data` (둘 다 Stopped) | 범용 리눅스 배포판이 아니라 개발 셸로 부적합 |
| Makefile 가드 | `bootstrap-check` 가 Windows 네이티브를 **명시적으로 차단**하고 종료 | 설계상 의도된 동작 |
| `uv` | **0.5.12 설치됨** (Windows 네이티브) | 도구의 핵심 스택을 그대로 사용 가능 |

`bootstrap.ps1` 은 WSL2가 없으면 **자동 설치 후 재부팅**을 수행한다. 사용자 확인 없이
재부팅을 유발할 수 없어 실행하지 않았다.

### 1.2 실제 수행한 구축 절차

부트스트랩의 스캐폴딩(`scripts/scaffold_project.sh`)은 `uv init` 으로 **새 프로젝트를 생성**하는
용도라, 이미 존재하는 이 프로젝트에는 적용하지 않았다(기존 `README.md` 를 덮어쓸 위험).
대신 같은 도구·같은 템플릿으로 동등한 환경을 구성했다.

| 부트스트랩의 원래 동작 | 이번에 수행한 것 | 이유 |
| --- | --- | --- |
| `uv init` + `uv python pin` | `uv python pin 3.13` + [pyproject.toml](pyproject.toml) 직접 작성 | `uv init` 이 기존 파일을 건드릴 위험 회피 |
| `uv add --dev pytest` | `uv sync --dev` (`[dependency-groups] dev = ["pytest>=8"]`) | 동일 결과 |
| `templates/python/pyproject.toml` | 해당 템플릿의 Ruff·pytest 설정을 이식 (단, `py310` 타깃) | 앱이 Python 3.10+ 를 지원 |
| `templates/python/smoke_test.py` | [smoke_test.py](smoke_test.py) 를 budget_app 용으로 재작성 | 템플릿은 `add(2,3)==5` 예제 |
| `templates/python/tests/test_from_testcases.py` | [tests/test_from_testcases.py](tests/test_from_testcases.py) 로 확장 | 템플릿 파서는 정수 인자 전용 (README 가 확장을 권고) |
| `make test` (= `scripts/run_tests.sh`) | **해당 스크립트를 그대로 실행** | 도구의 테스트 러너를 실제로 사용 |

```bash
uv python pin 3.13     # .python-version 고정 (부트스트랩 DEFAULT_PYTHON_VERSION)
uv sync --dev          # .venv 생성 + pytest 설치
```

### 1.3 구축 결과

| 항목 | 값 |
| --- | --- |
| 가상환경 | `.venv/` (uv 생성) |
| Python | 3.13.1 (`.python-version` 으로 3.13 고정) |
| pytest | 9.1.1 |
| uv | 0.5.12 |
| 런타임 의존성 | **0개** (앱은 표준 라이브러리만 사용 — dev 의존성만 설치됨) |
| 플랫폼 | Windows 11 (10.0.26200) |

> 앱은 Python 3.10+ 를 지원한다고 문서화되어 있고, 테스트는 부트스트랩 기본값인
> **3.13.1 에서 수행**했다. 즉 하한(3.10)이 아니라 상한 쪽에서의 동작을 확인한 셈이다.

---

## 2. 테스트 구성

체크리스트 16개 항목을 **모듈 단위 테스트**와 **스모크 테스트**로 나눠 덮었다.

| 파일 | 건수 | 성격 | 덮는 체크리스트 |
| --- | --- | --- | --- |
| [tests/test_cli_functional.py](tests/test_cli_functional.py) | 19 | 블랙박스 CLI 기능 테스트 | §1 전체, §4.3 |
| [tests/test_from_testcases.py](tests/test_from_testcases.py) | 12 | `TestCase.txt` 기반 종료 코드 계약 | §1.6, §1.7 |
| [tests/test_structure_unit.py](tests/test_structure_unit.py) | 15 | 모듈 단위 (AST 정적 분석 + 동적 import) | §2 전체, §3 전체 |
| [smoke_test.py](smoke_test.py) | 1 | 핵심 경로 6단계 스모크 | §1 핵심 경로 |
| **합계** | **47** | | |

### 2.1 모듈 단위 테스트 ([tests/test_structure_unit.py](tests/test_structure_unit.py))

구현마다 모듈·클래스 이름이 다르므로 **이름이 아니라 설계 속성**을 검사한다.

| 테스트 | 검사 내용 | 이 프로젝트 측정치 |
| --- | --- | --- |
| `test_package_is_split_into_at_least_3_modules` | 책임 모듈 ≥ 3 | **5개** (cli/services/repository/models/decorators) |
| `test_has_at_least_2_classes` | 클래스 ≥ 2 | **14개** |
| `test_update_delete_uses_atomic_replace` | 임시 파일 + 원자적 교체 | `os.replace` + `.tmp` 확인 |
| `test_uses_generator_streaming` | `yield` 사용 함수 존재 | **6개** |
| `test_uses_decorators_for_cross_cutting_concerns` | 자체 데코레이터 정의 + 적용 | `handle_errors`/`log_call`/`measure_time` |
| `test_type_hints_are_widely_applied` | 타입 힌트 비율 ≥ 70% | **95% (76/80)** |
| `test_all_modules_import_cleanly` | 각 모듈 단독 import (순환참조 탐지) | 5개 모듈 정상 |
| `test_amount_validation_rejects_invalid` ×4 | 금액 검증이 음수/0/문자열/빈값 거부 | 통과 |
| `test_date_validation_rejects_invalid` ×4 | 날짜 검증이 무효 형식 거부 | 통과 |

### 2.2 스모크 테스트 ([smoke_test.py](smoke_test.py))

핵심 경로가 끝까지 도는지 빠르게 확인한다. **pytest 없이 표준 라이브러리만으로** 동작해
의존성이 없는 환경에서도 실행 가능하며, `run_tests.sh` 가 자동 감지해 실행한다.

`help` → `import`(3건) → `list`(영속성) → `summary`(합계 검산) → `export`(CSV 왕복 3건)
→ `오류 처리`(종료 코드 ≠ 0, 스택트레이스 미노출)

### 2.3 `TestCase.txt` 확장 ([TestCase.txt](TestCase.txt))

부트스트랩 템플릿의 `함수인자 => 기대값` 규약을 CLI 앱에 맞게 확장했다
(템플릿 README 의 *"파서는 정수 인자 기준이니 필요하면 확장하라"* 지침을 따름).

```
<서브커맨드와 옵션...>  =>  <기대 종료코드>     # list => 0
<서브커맨드와 옵션...>  =>  !0                  # 0이 아닌 값(오류)
```

케이스를 늘릴 때 **파이썬을 건드릴 필요 없이 텍스트 한 줄만 추가**하면 된다.

---

## 3. 실행 결과

부트스트랩의 테스트 러너(`make test` 의 구현체)를 그대로 실행했다.

```bash
$ bash DevEnvAuto/dev-env-bootstrap/scripts/run_tests.sh python

==> pytest 실행 (TestCase.txt 포함)
============================= 46 passed in 11.46s =============================
==> 스모크 테스트 감지됨 -> 실행
[i] 대상: C:\Users\ashof\Desktop\codyssey_B2-1  (모듈: budget_app)
[OK] 스모크 테스트 통과 — help/import/list/summary/export/오류처리 정상
```

| 지표 | 값 |
| --- | --- |
| 통과 | **46 / 46** (pytest) + **1 / 1** (스모크) |
| 실패 | 0 |
| skip | 0 |
| 소요 | 약 11.5초 (pytest) |

**부작용 없음 확인**: 테스트는 임시 디렉터리를 cwd 로 삼아 실행되므로 실제 `data/` 는
건드리지 않는다. 실행 후 `git status data/` 결과 변경 없음.

---

## 4. 테스트 신뢰성 검증 (뮤테이션 테스트)

*"46건 전부 통과"* 는 테스트가 결함을 **잡을 수 있을 때만** 의미가 있다. 코드를 고의로
망가뜨린 복사본을 만들어 스위트가 실제로 실패하는지 확인했다.

| # | 주입한 결함 | 결과 | 검출한 테스트 |
| --- | --- | --- | --- |
| 기준선 | 없음 (정상 복사본) | ✅ 통과 | — (거짓 실패 없음) |
| A | 오류 시 종료 코드를 `0` 으로 위조 | 🔴 **11건 실패** | 종료 코드 계약 전반 + `TestCase.txt` 케이스 7건 |
| B | 원자적 교체 제거 (`os.replace` 삭제, 원본 직접 덮어쓰기) | 🔴 **1건 실패** | `test_update_delete_uses_atomic_replace` |
| C | 제너레이터 스트리밍 제거 (`yield` → `pass`) | 🔴 **1건 실패** | `test_uses_generator_streaming` |
| D | `summary` 지출 합계 누락 (기능 버그) | 🔴 **3건 실패** | `test_summary_reports_income_and_expense`, `test_budget_set_and_summary_shows_usage`, `test_summary_warns_when_over_budget` |

이 과정에서 **테스트 자체의 결함 1건을 발견해 수정**했다.

> 초기 `test_update_delete_uses_atomic_replace` 는 소스에서 `.replace(` 라는 **문자열**을
> 찾았다. 이러면 평범한 `문자열.replace("a","b")` 만 있어도 "원자적 쓰기 있음"으로
> 통과하는 **거짓 안심**을 준다. AST 로 *무엇을 호출했는지* 판별하도록 고쳤다
> (`os.replace`/`os.rename`/`shutil.move`, 또는 수신자가 임시 파일인 `.replace()`).
> 수정 후에야 뮤턴트 B 를 검출했다.

뮤턴트 C 에서도 AST 방식의 이점이 드러났다. `yield` 를 모두 제거한 뒤에도 소스에는
`yield` 라는 문자열이 3개 남아 있었지만(**docstring 속 설명 문구**), AST 는 이를
실행 코드로 세지 않아 정확히 실패를 보고했다. 텍스트 검색이었다면 통과했을 것이다.

---

## 5. 범용성 — 다른 사람의 budget_app 테스트하기

이 스위트는 **특정 구현에 고정되지 않도록** 설계했다. 뮤테이션 테스트는 전부
`BUDGET_APP_ROOT` 로 **외부 디렉터리의 프로젝트**를 겨냥해 수행했으므로, 이 메커니즘이
실제로 동작함은 이미 입증되었다.

### 5.1 사용법

```bash
# 방법 1) tests/, smoke_test.py, TestCase.txt 를 대상 프로젝트에 복사 후
uv run pytest
uv run python smoke_test.py

# 방법 2) 이 프로젝트에서 다른 위치의 앱을 겨냥
BUDGET_APP_ROOT=/path/to/other-budget-app uv run pytest
BUDGET_APP_MODULE=my_ledger BUDGET_APP_ROOT=/path/to/app uv run pytest
```

| 환경변수 | 기본값 | 용도 |
| --- | --- | --- |
| `BUDGET_APP_ROOT` | `tests/` 의 상위 디렉터리 | 대상 프로젝트 루트 |
| `BUDGET_APP_MODULE` | `budget_app` | `python -m <모듈>` 로 실행할 모듈명 |

### 5.2 구현 비의존성을 위한 5가지 설계

| # | 설계 | 이유 |
| --- | --- | --- |
| 1 | **블랙박스 실행** — 내부를 import 하지 않고 `python -m <모듈>` 서브프로세스로 구동 | 모듈·클래스·함수 이름이 달라도 통과 |
| 2 | **cwd 격리** — 테스트마다 임시 폴더를 cwd 로 삼아 앱의 기본 `./data` 가 그 안에 생기게 함 | `--data-dir` 같은 **선택 옵션 없이도** 상태 격리. 실제 데이터 오염 방지 |
| 3 | **옵션명 자동 탐지** — `--from`/`--file`/`--in`, `--out`/`--to` 등을 `--help` 에서 찾아 사용 | 옵션 이름이 다른 구현도 지원, 못 찾으면 skip |
| 4 | **느슨한 출력 단언** — 사람이 읽는 문구는 비교하지 않음. 종료 코드·파일 내용·CSV 스키마만 단언. 금액은 `3,000,000`→`3000000` 로 정규화 | 문구·포맷은 구현 자유 |
| 5 | **정책 중립 검증** — 깨진 CSV 는 "부분 성공이든 롤백이든 **일관되면 통과**"로 검사 | 명세가 정책을 강제하지 않음. 단, *일부만 저장된 채 실패 보고* 같은 모순 상태는 불허 |

§2·§3 의 구조 항목은 이름 대신 **AST 로 설계 속성**(모듈 수, 클래스 수, `yield` 존재,
데코레이터 정의·적용, 타입 힌트 비율)을 본다. 임계치는 파일 상단 상수
(`TYPE_HINT_MIN_RATIO` 등)로 뽑아 두어 조정할 수 있다.

### 5.3 다른 구현에서 기대되는 동작

| 상황 | 이 스위트의 반응 |
| --- | --- |
| 옵션명이 다름 (`import --file`) | 자동 탐지해 통과 |
| 옵션 자체가 없음 | 해당 테스트만 **skip** (전체 실패 아님) |
| `add` 프롬프트 순서가 다름 | 해당 테스트만 **skip** |
| 거래 ID 형식이 `<접두어>-<숫자>` 가 아님 | update/delete 테스트 **skip** |
| import 가 전수 롤백 정책 | 롤백 분기로 검증 (통과) |
| 저장 포맷이 CSV/SQLite | §1 기능 테스트는 그대로 통과 (포맷 무관) |

---

## 6. 한계 및 후속 과제

| 한계 | 설명 | 제안 |
| --- | --- | --- |
| `make` 경로 미검증 | 이 머신에 `make`/WSL2 배포판이 없어 `make setup`·`make project` 는 실행하지 못했다. `make test` 는 그 구현체(`run_tests.sh`)를 직접 실행해 동등하게 검증했다. | WSL2 + Ubuntu 설치 후 `make setup` 부터 재검증 |
| 단일 Python 버전 | 3.13.1 에서만 검증. 앱은 3.10+ 를 표방한다. | 3.10/3.13 매트릭스 (CI 도입 시) |
| 대용량 미검증 | [README.md](README.md) §9 의 100k+ 병목 분석은 **문서상 설계 근거**이며, 실측 벤치마크는 수행하지 않았다. | 10만 건 생성 후 `list`/`import` 시간·메모리 계측 |
| 동시성 미검증 | 두 프로세스가 동시에 쓰는 상황은 테스트하지 않았다(과제 범위 밖). | 파일 잠금 도입 시 추가 |
| Ruff 미실행 | [pyproject.toml](pyproject.toml) 에 설정만 넣었고 린트는 이번 범위에서 실행하지 않았다. | `uvx ruff check` 를 `make test` 전에 추가 |
| 구조 테스트의 성격 | AST 검사는 *설계 속성의 존재*를 확인할 뿐, 그 설계가 **잘** 되었는지는 판단하지 못한다(예: `yield` 가 있어도 호출부에서 `list()` 로 감싸면 스트리밍 이점이 사라짐). | 코드 리뷰로 보완 |

## 부록 — 재현 명령

```bash
cd codyssey_B2-1
uv sync --dev                                                   # 환경 구축
uv run pytest -v                                                # 자동화 테스트 46건
uv run python smoke_test.py                                     # 스모크 테스트
bash ../DevEnvAuto/dev-env-bootstrap/scripts/run_tests.sh python  # 부트스트랩 러너 (= make test)
```
