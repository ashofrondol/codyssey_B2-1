# 01. 프로젝트 개요와 사용법

budget_app 이 무엇을 하는 프로그램인지, 어떻게 실행하고, 11개 명령을 어떻게 쓰는지, 데이터가 어디에 어떤 형식으로 저장되는지를 한 번에 정리합니다.

> **난이도**: 🟢 초보
>
> **먼저 읽으면 좋은 문서**: 없음 — 이 문서가 시리즈의 첫 문서입니다.

---

## 1. 이 프로젝트는 무엇인가

budget_app 은 **파일 기반 가계부 콘솔 프로그램**입니다. 터미널에서 명령을 입력해 수입/지출 거래를 기록하고, 목록·검색·월별 요약·예산 관리·CSV 가져오기/내보내기를 수행합니다. 데이터베이스 서버 없이 로컬의 JSONL(JSON Lines) 텍스트 파일 3개에 모든 데이터를 저장합니다.

세 가지 배경을 먼저 알아두면 좋습니다.

1. **표준 라이브러리만 사용합니다.** `pyproject.toml` 의 `dependencies = []` 가 보여주듯 외부 패키지 의존성이 0입니다. `argparse`(명령 파싱), `json`(저장 형식), `csv`(가져오기/내보내기), `dataclasses`(모델), `pathlib`(경로), `logging`(로그) 등 파이썬에 기본 내장된 모듈만 씁니다. 따라서 Python 3.10 이상만 있으면 `pip install` 없이 바로 실행됩니다.
2. **이 저장소는 과제 명세에 따라 AI 가 생성한 코드입니다.** 그래서 이 문서 시리즈(01~11)의 목적은 "코드를 직접 쓰지 않았어도, 쓰인 문법·기법·설계를 완전히 이해하고 남에게 설명할 수 있게 만드는 것"입니다. 이 문서는 그 출발점으로, 사용자 관점(무엇을 하고 어떻게 쓰는가)을 다룹니다. 내부 구조는 [04. 아키텍처](./04-architecture.md)에서 깊게 다룹니다.
3. **파일 하나 = 책임 하나** 원칙으로 `budget_app/` 아래 43개 파이썬 파일(그중 `__init__.py` 5개)에 책임이 나뉘어 있습니다. 이 문서에서는 "그런 파일이 있다" 수준으로만 소개합니다.

> **🔎 문법의 출처** — 이 프로젝트가 쓰는 문법의 하한선은 `pyproject.toml` 의 `requires-python = ">=3.10"` 이 정합니다. 3.10 을 요구하는 실제 이유는 `main(argv: list[str] | None = None)` 같은 **`X | Y` 유니온 표기**(PEP 604, 3.10)입니다. `list[str]` 처럼 내장 타입을 그대로 제네릭으로 쓰는 표기는 그보다 한 버전 이른 PEP 585(3.9)에서 왔습니다. 문법의 출처와 표준 라이브러리 내부 동작을 한곳에 모은 참조 문서는 [12. 문법과 표준 라이브러리](./12-syntax-and-stdlib.md)입니다.

---

## 2. 저장소 구조

```
codyssey_B2-1/
├── budget_app/                # 애플리케이션 패키지 — 계층이 폴더로 드러난다
│   ├── __main__.py                # 엔트리포인트 (python -m budget_app)
│   ├── config.py                  # 앱 정체성 (로거 이름) — 계층 아님
│   ├── errors.py                  # 예외 어휘 (ValidationError / AppError) — import 0개
│   ├── decorators.py              # 관측 — @log_call / @measure_time
│   ├── context.py                 # 합성 루트 — 저장소·서비스 조립 (계층 밖)
│   │
│   ├── domain/                    # ── 도메인 (I/O 를 전혀 모름) ──
│   │   ├── config.py              #    타입 어휘·날짜 형식·ID 형식
│   │   ├── messages.py            #    필드 검증 실패 메시지
│   │   ├── validators.py          #    규칙 하나 = 함수 하나
│   │   ├── tx_id.py               #    TransactionId 값 객체
│   │   ├── entities.py            #    Transaction / Budget / Category / TransactionPatch
│   │   ├── specs.py               #    Specification — 조합 가능한 검색 조건
│   │   ├── queries.py             #    SearchFilter — CLI 인자를 명세로 조립
│   │   ├── results.py             #    MonthlySummary / ImportReport
│   │   └── periods.py             #    month_range — "이 달"의 정의처
│   │
│   ├── storage/                   # ── 저장소 (open() 은 전부 여기) ──
│   │   ├── config.py              #    파일명·인코딩·CSV 스키마·백업
│   │   ├── messages.py            #    손상 줄 로그 / CSV 헤더 오류
│   │   ├── jsonl.py               #    JsonlStore / RawLine / stage·commit
│   │   ├── ids.py                 #    IdAllocator
│   │   ├── repositories.py        #    거래·카테고리·예산 저장소
│   │   ├── csv_io.py              #    CSV 경계 어댑터
│   │   ├── unit_of_work.py        #    UnitOfWork — 다중 파일 커밋
│   │   └── backup.py              #    데이터 폴더 백업
│   │
│   ├── services/                  # ── 서비스 (판단만) ──
│   │   ├── config.py              #    중복 정책·한도
│   │   ├── messages.py            #    AppError message / hint
│   │   ├── transactions.py        #    거래 유스케이스
│   │   ├── budgets.py             #    예산 + 월별 요약
│   │   ├── categories.py          #    카테고리 + 참조 무결성
│   │   ├── importexport.py        #    CSV 정책 (실패 축 × 중복 축)
│   │   └── maintenance.py         #    BackupService — 백업 유스케이스
│   │
│   └── cli/                       # ── CLI (사람과 만나는 곳) ──
│       ├── __init__.py            #    main 만 재수출
│       ├── config.py              #    한도·종료 코드
│       ├── messages.py            #    프롬프트·결과·오류 표시 (전체의 3분의 2)
│       ├── app.py                 #    HANDLERS 레지스트리 + main
│       ├── handlers.py            #    cmd_* 13개
│       ├── parser.py              #    argparse 문법
│       ├── prompts.py             #    대화형 입력
│       ├── presenter.py           #    도메인 → 문자열 (출력 안 함)
│       ├── output.py              #    채널 결정
│       └── error_handler.py       #    예외 → 종료 코드
├── data/                      # 데이터 폴더 (첫 실행 시 자동 생성)
│   ├── transactions.jsonl     # 거래 내역 (한 줄 = 거래 1건)
│   ├── categories.jsonl       # 카테고리 목록
│   └── budgets.jsonl          # 월별 예산
├── docs/                      # 학습용 기술 문서 (이 시리즈)
├── tests/                     # pytest 계약/구조 테스트 (런타임 의존성 아님 — §7.4)
├── README.md                  # 사용자 매뉴얼
└── pyproject.toml             # 프로젝트 메타데이터 + Ruff/pytest 설정
```

각 모듈의 역할을 한 줄씩 정리하면 다음과 같습니다. **`config.py` 와 `messages.py` 는 계층마다 하나씩 있습니다** — 루트에 한 벌만 두던 것을 계층별로 내려보냈기 때문입니다(자세한 근거는 [05. 설정과 모델](./05-config-and-models.md)).

| 파일 | 역할 |
| --- | --- |
| `__init__.py` | 이 폴더를 **일반 패키지**로 선언하고 `__version__` 을 둡니다. 파이썬 3.3 부터는 이 파일이 없어도 폴더가 네임스페이스 패키지로 import 되지만, 두면 "이 폴더는 패키지다"가 명시되고 패키지 import 시점에 실행할 코드를 놓을 자리가 생깁니다 → [02 §1.1](./02-python-basics.md) |
| `__main__.py` | `python -m budget_app` 으로 실행될 때의 진입점입니다. |
| `config.py` (루트) | 앱 **정체성**만 남습니다 — `LOGGER_NAME = "budget_app"` 한 줄뿐이고, 계층 하나만 쓰는 값은 전부 그 계층의 `config.py` 로 내려갔습니다. |
| `errors.py` | `ValidationError`(값이 틀림) / `AppError`(상황이 틀림). import 가 0개입니다. |
| `decorators.py` | `@log_call`, `@measure_time` — 관측만 담당합니다. |
| `context.py` | 합성 루트. 저장소 3개 + 서비스 5개를 조립하는 `AppContext` 하나만 있습니다(§3.5). |
| `domain/config.py` · `domain/messages.py` | 타입 어휘·날짜/ID 형식 / 필드 검증 실패 문구. |
| `domain/entities.py` | `Transaction`·`TransactionPatch`·`Budget`·`Category` — 저장되는 것들의 모양과 불변식. |
| `domain/tx_id.py` | `TransactionId` 값 객체. `TX-000001` 의 형식·비교·파싱이 여기 한 곳입니다. |
| `domain/validators.py` | `parse_date`/`parse_amount` 등 **규칙 하나 = 함수 하나**. |
| `domain/specs.py` | `Spec` 과 `And`/`Or`/`Not` + 조건 6종 — 조합 가능한 검색 명세(Specification 패턴). |
| `domain/queries.py` | `SearchFilter` — 평평한 CLI 옵션 묶음을 명세 트리로 번역하는 어댑터. |
| `domain/results.py` | `MonthlySummary` / `ImportReport` 등 **계산 결과**를 담는 모델. |
| `domain/periods.py` | `month_range` — "이 달"의 경계를 정의하는 단 하나의 함수. |
| `storage/config.py` · `storage/messages.py` | 파일명·인코딩·CSV 스키마·백업 설정 / 손상 줄 로그 문구. |
| `storage/jsonl.py` | JSONL 을 한 줄씩 읽고(제너레이터), 임시 파일 + `os.replace` 로 안전하게 씁니다. 이 패키지에서 가장 큰 파일(329줄)입니다. |
| `storage/ids.py` | `IdWatermark` / `IdAllocator` — 삭제된 id 를 재사용하지 않게 발급 번호를 기억합니다. |
| `storage/repositories.py` | `TransactionRepository` / `CategoryStore` / `BudgetStore` — 엔티티별 저장소. |
| `storage/csv_io.py` | 외부 교환 포맷(CSV)과 도메인 사이의 번역을 담당합니다. |
| `storage/unit_of_work.py` | `UnitOfWork` — 여러 파일을 한 번에 커밋하거나 한 번에 되돌립니다. |
| `storage/backup.py` | `backup_data_dir` — 데이터 폴더를 타임스탬프 폴더로 복사합니다. |
| `services/config.py` · `services/messages.py` | 중복 정책·한도 / `AppError` 의 message·hint 문구. |
| `services/transactions.py` | 거래 추가·수정·삭제·정렬 스트림. `open()` 이 하나도 없습니다. |
| `services/budgets.py` | 예산 설정과 월별 요약 계산. |
| `services/categories.py` | 카테고리 추가·삭제와 **참조 무결성**(사용 중 카테고리 보호). |
| `services/importexport.py` | CSV 가져오기/내보내기 정책 — 실패 축(`--atomic`) × 중복 축(`--on-duplicate`). |
| `services/maintenance.py` | `BackupService` — 백업 유스케이스(저장소의 `backup_data_dir` 을 감쌉니다). |
| `cli/__init__.py` | `main` 만 재수출합니다 — 이 패키지의 유일한 공개 심볼. |
| `cli/config.py` · `cli/messages.py` | 한도·종료 코드 / 프롬프트·결과·오류 문구. |
| `cli/app.py` | `HANDLERS` 레지스트리 + `main` + `_dispatch`(오류 방패를 쓰는 유일한 자리). 98줄뿐입니다. |
| `cli/handlers.py` | `cmd_*` 13개 — **인자를 서비스 호출로 번역**하고 결과를 프레젠터에 넘깁니다. |
| `cli/parser.py` | argparse 파서를 구성합니다. 핸들러 함수를 모르고 **문자열 키**만 남깁니다. |
| `cli/prompts.py` | 대화형 입력을 받습니다. 재입력 횟수와 EOF 처리 정책이 여기 있습니다. |
| `cli/presenter.py` | 도메인 객체를 화면 문자열로 바꿉니다. **출력하지 않고 반환**합니다. |
| `cli/output.py` | 어떤 메시지가 stdout/stderr/로그 중 어디로 나갈지 정합니다. |
| `cli/error_handler.py` | `@handle_errors` — 예외를 `[오류]`/`[힌트]` 와 종료 코드로 바꿉니다. |

**폴더 이름이 곧 계층입니다.** 파일이 평평하게 늘어서 있으면 알파벳순이 계층을 흩뜨려서(`csv_io.py` 와 `decorators.py` 가 나란히 보이는 식) 구조가 코드에는 있는데 파일 트리에는 없는 상태가 됩니다. 폴더로 묶으면 새 파일을 추가할 때 "이건 어느 계층인가"를 강제로 결정하게 되는 이점도 있습니다.

루트에 폴더 없이 남은 4개(`config.py`/`errors.py`/`decorators.py`/`context.py`)는 **어느 계층에도 속하지 않는다**는 뜻입니다. 실제 import 수를 세어 보면 성격이 갈립니다 — `errors` 는 10개 모듈이 import 하는 진짜 횡단 어휘이고, `decorators` 는 2개(`services/transactions.py`, `services/budgets.py`)뿐이며, 루트 `config` 는 2개(`cli/config.py`, `storage/config.py`)가 자식 로거 이름을 파생시키려고만 가져갑니다. `messages` 는 루트에 아예 없습니다 — 문구는 100% 한 계층에서만 쓰이므로 계층별 `messages.py` 로 전부 내려갔습니다.

`data/` 폴더는 저장소에 처음부터 있을 필요가 없습니다. 어떤 명령이든 처음 실행하면 자동으로 생성됩니다(§5.2 참고).

---

## 3. 실행 방법 — `python -m budget_app` 이 동작하는 원리

### 3.1 기본 실행

프로젝트 루트(`codyssey_B2-1/`)에서 실행합니다.

```bash
python -m budget_app <command> [options]
python -m budget_app --help
python -m budget_app <command> --help
```

### 3.2 `-m` 옵션의 원리

일반 개념부터 설명하면, `python -m 패키지명` 은 "그 패키지를 **모듈로서** 실행하라"는 뜻입니다. 파이썬 인터프리터는 `budget_app` 패키지를 찾은 뒤, 그 안의 `__main__.py` 파일을 `__name__ == "__main__"` 상태로 실행합니다. 즉 `__main__.py` 는 패키지의 "실행 버튼" 역할을 하는 관례적 파일명입니다.

> **🔎 문법의 출처** — `-m` 으로 "패키지 안에 있는 모듈"까지 실행할 수 있게 만든 것은 PEP 338 이고, 그 구현체가 표준 라이브러리 `runpy` 모듈입니다. `__main__.py` 라는 파일명은 문법이 아니라 `runpy` 가 **찾기로 정해 둔 이름**입니다 — 인자가 패키지면 `패키지.__main__` 서브모듈을 찾아 실행합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — `python -m budget_app` 은 대략 이 순서로 진행됩니다. ① `sys.path[0]` 을 **현재 작업 디렉터리**로 세팅합니다(그래서 프로젝트 루트에서 실행해야 `budget_app` 이 보입니다). ② `budget_app` 패키지를 **먼저 import** 합니다 — 즉 `budget_app/__init__.py` 가 `__main__.py` 보다 앞서 실행됩니다. ③ 그다음 `budget_app/__main__.py` 의 코드를, 모듈 이름만 `"__main__"` 으로 바꾼 새 네임스페이스에서 실행합니다(`runpy._run_module_as_main`). 이때 `__package__` 는 `"budget_app"` 으로 남기 때문에 아래의 상대 import 가 성립합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

이 프로젝트의 `__main__.py` 는 전체가 8줄입니다.

budget_app/__main__.py:1-8

```python
"""python -m budget_app 진입점."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
```

`from .cli import main` 의 앞에 붙은 점(`.`)은 **상대 import** 로, "같은 패키지 안의 cli 모듈"을 뜻합니다. 이 상대 import 는 파일을 직접 실행(`python budget_app/__main__.py`)하면 실패하고, 반드시 `-m` 으로 패키지로서 실행해야 동작합니다. 그래서 이 프로그램의 공식 실행법이 `python -m budget_app` 인 것입니다.

> **⚙️ 내부 동작** — 왜 직접 실행하면 실패할까요. 점 하나로 시작하는 import 는 실행 시점에 그 모듈의 `__package__` 값을 기준으로 절대 이름을 계산합니다(`.cli` + `__package__="budget_app"` → `budget_app.cli`). 파일을 경로로 직접 주면 `__package__` 가 빈 문자열이라 "기준점이 없다"는 뜻의 `ImportError: attempted relative import with no known parent package` 가 납니다. 반대로 `-m` 은 위에서 본 대로 `__package__` 를 채워 주므로 성립합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

`sys.exit(main())` 은 `main()` 이 반환한 정수를 그대로 **프로세스 종료 코드**로 만듭니다. `main()` 은 `cli/app.py` 에 있습니다.

> **⚙️ 내부 동작** — `sys.exit()` 은 프로세스를 그 자리에서 끝내는 함수가 아니라 **`SystemExit` 예외를 던지는 함수**입니다. 그 예외가 아무에게도 잡히지 않고 인터프리터 최상단까지 올라오면, 그때 인터프리터가 예외의 인자를 종료 코드로 삼아 프로세스를 끝냅니다. 그래서 `sys.exit(main())` 은 "`main()` 을 먼저 끝까지 실행해 정수를 받고 → 그 정수를 담은 `SystemExit` 을 던진다"는 두 단계입니다. 이 사실은 §6 에서 다시 중요해집니다 — `SystemExit` 은 `Exception` 이 아니라 **`BaseException` 의 직계 자식**이라 `except Exception` 그물에 걸리지 않습니다. → [12 §1-C](./12-syntax-and-stdlib.md)

budget_app/cli/app.py:84-94

```python
def main(argv: list[str] | None = None) -> int:
    try:
        args = parser_module.build_parser().parse_args(argv)
        # 로거에 핸들러를 붙이는 유일한 지점. 이 호출이 없으면 handle_errors 가
        # exc_info 로 보존한 스택트레이스가 아무 데도 출력되지 않는다.
        output.setup_logging(getattr(args, "debug", False))
        return _dispatch(args)
    except BrokenPipeError:
        # 예: `budget_app list | head` — head 가 먼저 닫음. 오류가 아니므로 조용히 종료.
        _silence_broken_pipe()
        return config.EXIT_OK
```

> **🔎 문법의 출처** — 시그니처 `def main(argv: list[str] | None = None) -> int:` 한 줄에 서로 다른 세 시기의 문법이 겹쳐 있습니다. `list[str]` 처럼 내장 타입을 그대로 첨자로 쓰는 표기는 PEP 585(3.9)이고 그 전에는 `typing.List[str]` 이었습니다. `X | None` 은 PEP 604(3.10)이며 그 전에는 `typing.Optional[X]` 였습니다. `-> int` 라는 반환 어노테이션 자체는 PEP 3107(파이썬 3.0)에서 도입됐습니다. 그리고 이 파일 맨 위의 `from __future__ import annotations`(`cli/app.py:13`)가 이 어노테이션들을 **실행하지 않고 문자열로만 보관**하게 만듭니다(PEP 563). → [12 §1-C](./12-syntax-and-stdlib.md)

흐름을 그림으로 정리하면 다음과 같습니다.

```
$ python -m budget_app list --limit 3
        │
        ▼
budget_app/__main__.py          sys.exit(main())
        │
        ▼
cli/app.py  main()              parser.build_parser() 로 argparse 파서 구성
        │                       parse_args() 로 옵션 해석
        │                       output.setup_logging() 으로 로거 준비
        │                       (BrokenPipeError 만 여기서 잡는다)
        ▼
cli/app.py  _dispatch()         @handle_errors — 저장소를 만지는 모든 경로가
        │                       이 방패 **안**에 있다
        ▼
AppContext(data_dir)            저장소 3개 + 서비스 5개를 조립 (합성 루트)
        │                       needs_storage 면 ctx.prepare() 로 폴더·파일 준비
        ▼
HANDLERS[args.handler]          문자열 키 → 핸들러 함수 (예: "list" → cmd_list)
        │
        ▼
반환된 int                       프로세스 종료 코드가 됨 (0=성공, 그 외=오류)
```

`AppContext` 조립과 `prepare()` 가 `main` 이 아니라 `_dispatch` 안에 있는 것이 핵심입니다. `@handle_errors` 는 `_dispatch` **한 곳에만** 붙어 있으므로(`cli/app.py:61`), 여기 밖에서 파일을 건드리면 그 예외는 방패를 통과하지 못하고 원시 트레이스백으로 새어 나갑니다.

### 3.3 명령 → 핸들러 대응은 문자열 키로

`args.handler` 는 각 하위 명령 파서를 만들 때 `set_defaults(handler="list")` 처럼 심어둔 **문자열**입니다. 그 문자열을 함수로 바꾸는 표는 `cli/app.py` 에 있습니다.

budget_app/cli/app.py:28-42

```python
HANDLERS: dict[str, Handler] = {
    "add": handlers.cmd_add,
    "list": handlers.cmd_list,
    "search": handlers.cmd_search,
    "summary": handlers.cmd_summary,
    "budget.set": handlers.cmd_budget_set,
    "category.add": handlers.cmd_category_add,
    "category.list": handlers.cmd_category_list,
    "category.remove": handlers.cmd_category_remove,
    "update": handlers.cmd_update,
    "delete": handlers.cmd_delete,
    "export": handlers.cmd_export,
    "import": handlers.cmd_import,
    "backup": handlers.cmd_backup,
}
```

파서가 **함수 객체** 대신 문자열을 들고 있는 이유는 `cli/parser.py` 와 `cli/app.py` 가 서로를 import 하지 않게 하기 위해서입니다. 파서가 `cmd_list` 를 직접 참조하면 두 모듈이 순환 import 가 되거나 한 파일에 뭉쳐 있어야 합니다. 자세한 논의는 [09. CLI 계층](./09-cli.md)에 있습니다.

> **🔎 문법의 출처** — 표의 타입 `dict[str, Handler]` 와 그 위의 `Handler = Callable[[AppContext, argparse.Namespace], int]`(`cli/app.py:26`)는 **타입 별칭**입니다. `Callable` 을 `typing` 이 아니라 `collections.abc` 에서 가져오는 것(`cli/app.py:18`)이 요즘 방식이며, `typing.Callable` 은 3.9 부터 비권장입니다 — Ruff 의 `UP` 규칙군(§7.3)이 이런 자리를 잡아 줍니다. 이 별칭은 실행에 아무 영향이 없습니다. 딕셔너리에 들어가는 값이 실제로 저 시그니처인지는 파이썬이 검사하지 않고, 사람과 타입 검사기만 봅니다. → [12 §2-B](./12-syntax-and-stdlib.md)

### 3.4 `--data-dir` 옵션 — 데이터 폴더 바꾸기

모든 명령은 `--data-dir` 옵션을 공통으로 받습니다. 기본값은 `./data` 입니다.

budget_app/cli/parser.py:86-88 (실제 기본값은 최상위 파서 한 곳에만 있다)

```python
    parser.add_argument(
        "--data-dir", dest="data_dir", default=config.DEFAULT_DATA_DIR, help=DATA_DIR_HELP
    )
```

budget_app/cli/parser.py:75-76 (하위·말단 파서는 전부 SUPPRESS)

```python
    p.add_argument("--data-dir", dest="data_dir", default=argparse.SUPPRESS, help=DATA_DIR_HELP)
    p.add_argument("--debug", action="store_true", default=argparse.SUPPRESS, help=DEBUG_HELP)
```

```bash
python -m budget_app list --data-dir ./mydata
python -m budget_app category list --data-dir ./mydata     # 2단 명령에서도 동작
```

이 옵션을 쓰면 실험용 데이터와 실제 데이터를 폴더로 분리할 수 있습니다.

> **옵션을 어디에 놓아도 되는 이유** — argparse 는 하위 명령 이후의 인자를 **말단 파서**에게 넘깁니다. 그래서 최상위·하위·말단 파서 셋 다에 같은 옵션을 달아 두어야 `--data-dir` 를 명령 앞·뒤·2단 명령 말단 어디에 써도 동작합니다(`cli/parser.py:58-76` 의 `_add_shared_options()`).
>
> 기본값을 `argparse.SUPPRESS` 로 두는 것이 핵심입니다. 실제 기본값은 최상위 파서 한 곳에만 두고 나머지는 "값을 받으면 덮어쓰고 안 받으면 아무것도 안 한다"로 둡니다. 여기에 `DEFAULT_DATA_DIR` 를 주면 상위 파서가 이미 읽어 둔 값을 말단 파서가 기본값으로 되돌려 버립니다(`--debug` 도 False 로 꺼집니다).
>
> 이전에는 이 함수가 `_add_common_options` / `_add_leaf_options` 둘로 나뉘어 있었고 차이는 `--data-dir` 의 기본값 하나였습니다. 그 기본값을 최상위로 올리자 두 함수가 같아져 하나로 합쳐졌습니다.

> **⚙️ 내부 동작** — 왜 하위 파서의 기본값이 상위 파서의 값을 **덮어쓰는지**는 argparse 소스를 보면 정확히 보입니다. 하위 명령을 만나면 `_SubParsersAction.__call__` 이 남은 인자를 **새 빈 네임스페이스**에 파싱한 뒤(`subparser.parse_known_args(arg_strings, None)`), 그 결과의 모든 키를 `setattr(namespace, key, value)` 로 상위 네임스페이스에 **통째로 복사**합니다. 그러니 하위 파서가 `--data-dir` 의 기본값을 갖고 있으면 그 기본값까지 복사되어 상위가 읽어 둔 값을 지웁니다. `default=argparse.SUPPRESS`(값은 문자열 `'==SUPPRESS=='`)를 주면 argparse 가 애초에 그 속성을 네임스페이스에 **세팅하지 않으므로** 복사할 키 자체가 생기지 않습니다. → [12 §2-B](./12-syntax-and-stdlib.md)

### 3.5 `AppContext` — 저장소와 서비스의 조립 지점

핸들러는 `AppContext` 를 통해 필요한 저장소·서비스에 접근합니다.

budget_app/context.py:33-65 (클래스 docstring 은 `...` 로 축약)

```python
class AppContext:
    """저장소/서비스를 한 번에 조립해 핸들러로 전달한다.
    ...
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

        # 저장소는 비공개다 — 조립하는 데만 쓰고 밖으로 내보이지 않는다.
        # 공개해 두면 핸들러가 서비스를 건너뛰어 `ctx.cats.list_names()` 처럼
        # 부를 수 있고, 실제로 그런 자리가 있었다. 이름 앞의 밑줄 하나가
        # "이 계층은 서비스와만 말한다"를 코드로 강제한다.
        self._txs = TransactionRepository(self.data_dir)
        self._cats = CategoryStore(self.data_dir)
        self._budgets = BudgetStore(self.data_dir)

        self.tx_service = TransactionService(self._txs, self._cats)
        self.cat_service = CategoryService(self._cats, self._txs)
        self.budget_service = BudgetService(self._txs, self._budgets)
        self.io_service = ImportExportService(self._txs, self._cats)
        self.backup_service = BackupService(self.data_dir)

    def prepare(self) -> None:
        """데이터 폴더와 파일을 준비한다 — 명령 실행 전 한 번만."""
        self._require_usable_data_dir()
        self._txs.ensure_ready()
        self._budgets.ensure_ready()
        self._cats.ensure_ready()
        self._cats.seed_defaults()
```

**생성자와 `prepare()` 가 나뉜 이유**를 눈여겨보세요. 객체를 만드는 것(`__init__`)과 환경을 준비하는 것(`prepare`)은 다른 일입니다. 저장소 생성자가 폴더를 만들고 파일을 건드리면, 객체를 만드는 것만으로 디스크가 바뀝니다. 그러면 오타 난 `--data-dir` 도 조용히 새 폴더를 만들고 기본 카테고리를 심어 버립니다. 지금은 `_dispatch()` 가 한 번만 `prepare()` 를 호출하고, `backup` 처럼 준비가 필요 없는 명령은 `needs_storage=False` 로 건너뜁니다(`cli/parser.py:239-243`. 기본값 `True` 는 최상위 파서 한 곳에 `set_defaults(needs_storage=True)` 로 있습니다 — `cli/parser.py:91`).

> **⚙️ 내부 동작** — `prepare()` 가 마지막에 부르는 `_require_usable_data_dir` 는 `raise NotADirectoryError(errno.ENOTDIR, "not a directory", str(self.data_dir))` 로 예외를 직접 만듭니다(`context.py:79-80`). `NotADirectoryError` 같은 세분화된 예외들은 PEP 3151(파이썬 3.3)이 만든 `OSError` 하위 클래스 계층이고, 그전에는 전부 `OSError` 하나를 받아 `e.errno == errno.ENOTDIR` 로 직접 갈라야 했습니다. 인자 3개를 주는 형태는 OS 가 던지는 것과 **같은 모양**(errno, strerror, filename)이라 `exc.filename` 이 채워지고, 그 덕분에 `handle_errors` 가 `exc.filename or exc` 로 사용자에게 경로를 보여줄 수 있습니다(`cli/error_handler.py:88`). → [12 §2-B](./12-syntax-and-stdlib.md)

---

## 4. 명령어 11종 상세

이 프로그램은 11개 명령을 제공합니다: `add` / `list` / `search` / `summary` / `budget set` / `category add·list·remove` / `update` / `delete` / `import` / `export` / `backup`.

> **⚙️ 내부 동작** — argparse 에서 "하위 명령"은 별도 기능이 아니라 **위치 인자 하나**입니다. `parser.add_subparsers()`(`cli/parser.py:92`)는 `_SubParsersAction` 이라는 액션을 등록하는데, 이 액션의 `choices` 가 `add_parser()` 로 붙인 이름들의 사전이고 값은 **완전히 독립된 `ArgumentParser` 객체**입니다. 상위 파서가 `list` 라는 단어를 만나면 그 액션을 실행하고, 액션은 사전에서 하위 파서를 꺼내 **나머지 인자 전부**를 넘깁니다. `budget set` 처럼 2단인 명령은 하위 파서가 다시 `add_subparsers()` 를 하는 재귀 구조일 뿐입니다(`cli/parser.py:150`). 그래서 `--help` 도, `--data-dir` 도 단계마다 따로 정의해야 합니다(§3.4). `required=True` 를 붙인 것도 의미가 있습니다. argparse 의 기본은 "하위 명령을 생략해도 통과"라서, 명시하지 않으면 `python -m budget_app` 만 쳤을 때 `args.handler` 가 아예 존재하지 않아 `AttributeError` 로 죽습니다. 명시해 두면 usage 를 보여 주고 종료 코드 2 로 끝납니다. → [12 §2-B](./12-syntax-and-stdlib.md)

### 4.1 add — 거래 추가 (대화형)

거래 1건을 **대화형 프롬프트**로 입력받아 저장합니다. 옵션은 `--data-dir` 뿐이고, 날짜·타입·카테고리·금액·메모·태그를 순서대로 물어봅니다.

```text
$ python -m budget_app add
[안내] 거래 추가 - 대화형 입력입니다.
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000001
```

잘못된 값을 입력하면 `[오류] ...` 와 `[힌트] 다시 입력해 주세요.` 를 출력하고 재입력을 요구합니다(최대 10회, `cli/config.py:14` 의 `MAX_INPUT_RETRIES`). 카테고리는 등록된 것만 통과하며, 미등록이면 사용 가능한 목록을 함께 보여줍니다. 등록된 카테고리가 하나도 없으면 즉시 안내 후 종료 코드 5로 끝납니다.

핸들러는 값을 받는 일을 `prompts` 에 통째로 위임합니다.

budget_app/cli/handlers.py:33-50

```python
def cmd_add(ctx: AppContext, args: argparse.Namespace) -> int:
    if not ctx.cat_service.list_names():
        # 0 이 아닌 종료 코드로 끝나는 실패 경로 → 진단 채널(stderr).
        output.err(messages.MSG_NO_CATEGORIES)
        return config.EXIT_NO_CATEGORY

    output.out(messages.MSG_ADD_INTERACTIVE)
    entered = prompts.ask_transaction(ctx.cat_service)
    tx = ctx.tx_service.add(
        date=entered.date,
        type_=entered.type,
        category=entered.category,
        amount=entered.amount,
        memo=entered.memo,
        tags=entered.tags,
    )
    output.out(messages.MSG_SAVED_TX.format(id=tx.id))
    return config.EXIT_OK
```

### 4.2 list — 최신순 거래 목록

거래를 날짜 내림차순(같은 날짜면 id 내림차순)으로 출력합니다.

| 옵션 | 의미 | 기본값 |
| --- | --- | --- |
| `--limit` | 표시 건수 | 20 (`cli/config.py:15` 의 `DEFAULT_LIST_LIMIT`) |

```bash
python -m budget_app list --limit 3
```

```text
TX-000005 | 2024-01-22 | expense | food | 35000 | 회식
TX-000004 | 2024-01-20 | expense | rent | 150000 | 공과금
TX-000001 | 2024-01-15 | expense | food | 15000 | 점심
```

한 줄의 형식은 `cli/messages.py` 의 템플릿 하나로 정의되어 있습니다.

budget_app/cli/messages.py:42-43

```python
MSG_NO_DATA = "(데이터 없음)"
FMT_TX_LINE = "{id} | {date} | {type:<7} | {category} | {amount} | {memo}"
```

`{type:<7}` 은 타입 컬럼을 7칸 왼쪽 정렬한다는 뜻입니다. `expense` 는 정확히 7글자라 그대로 나오고, `income` 은 6글자라 뒤에 공백 1칸이 붙어 세로줄이 맞습니다. 거래가 없으면 `(데이터 없음)` 을 출력합니다.

> **🔎 문법의 출처** — 콜론 뒤의 `<7` 은 PEP 3101 이 정의한 **형식 명세 미니 언어**(format spec mini-language)입니다. `[[fill]align][sign][#][0][width]...` 문법에서 `<` 가 왼쪽 정렬, `7` 이 최소 폭입니다. 같은 미니 언어를 f-string(PEP 498, 3.6)도 그대로 씁니다 — `f"{x:<7}"` 과 `"{:<7}".format(x)` 는 같은 코드 경로를 탑니다. 이 프로젝트가 f-string 대신 `.format()` 을 쓰는 이유는 **템플릿을 `messages.py` 에 미리 정의해 두고 나중에 값을 채우기 위해서**입니다. f-string 은 정의되는 자리에서 값이 필요하므로 이 용도로는 쓸 수 없습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — `"...{type:<7}...".format(**kwargs)` 는 먼저 템플릿을 (리터럴 조각, 필드 이름, 형식 명세) 튜플들로 쪼갭니다. 위 템플릿이라면 `('', 'id', '', None)`, `(' | ', 'type', '<7', None)`, … 식입니다. 그다음 각 필드에 대해 내장 함수 `format(값, "<7")` 을 부릅니다. `format()` 은 다시 그 값의 `__format__` 특수 메서드에 명세 문자열을 넘깁니다. 즉 정렬을 실제로 수행하는 것은 `str.__format__` 이고, 만약 값이 문자열이 아닌 다른 타입이면 **그 타입이 정의한 `__format__`** 이 대신 불립니다(예: `datetime.__format__` 은 명세를 `strftime` 패턴으로 해석합니다). → [12 §1-A](./12-syntax-and-stdlib.md)

### 4.3 search — 조건 검색

여러 조건을 조합해 거래를 필터링합니다. 모든 옵션은 선택이며, 지정한 조건은 전부 만족(AND)해야 합니다. `list` 와 달리 `--limit` 가 없어 일치 항목을 전부 출력합니다.

| 옵션 | 의미 |
| --- | --- |
| `--from` | 시작일 `YYYY-MM-DD` (이상) |
| `--to` | 종료일 `YYYY-MM-DD` (이하) |
| `--category` | 카테고리 정확 일치 |
| `--type` | `income` / `expense` (argparse `choices` 로 제한) |
| `--q` | 메모 키워드 **부분** 일치 |
| `--tag` | 태그 **정확** 일치 |

```bash
python -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food
python -m budget_app search --type expense --tag meal
python -m budget_app search --q 점심
```

출력 형식은 `list` 와 동일한 `FMT_TX_LINE` 입니다. 참고로 `--from` 은 파이썬 예약어 `from` 과 겹치기 때문에 코드에서는 `dest="from_"` 으로 받습니다(`cli/parser.py:127`).

> **⚙️ 내부 동작** — `dest` 를 생략하면 argparse 는 가장 긴 옵션 이름에서 앞의 `--` 를 떼고 남은 `-` 를 `_` 로 바꿔 속성 이름을 만듭니다(`--data-dir` → `args.data_dir`, `--replace-with` → `args.replace_with`). 그런데 `--from` 은 그 규칙대로면 `args.from` 이 되고, 파싱 결과를 담는 `argparse.Namespace` 는 속성 이름에 아무 제약이 없으므로 **객체 자체는 만들어집니다**. 문제는 그다음입니다 — `args.from` 이라고 쓰는 순간 파이썬 **파서**가 `from` 을 import 문의 시작으로 읽어 `SyntaxError` 를 냅니다. 즉 값은 있는데 평범한 문법으로는 꺼낼 수 없는 상태가 됩니다. 그래서 뒤에 밑줄을 붙인 `from_` 으로 받습니다. 이 "예약어와 겹치면 뒤에 밑줄" 은 PEP 8 이 권장하는 관례입니다. → [12 §2-B](./12-syntax-and-stdlib.md)

> **조건값도 저장값과 같은 규칙으로 정규화됩니다.** `--category " food "` 처럼 공백이 낀 입력은 저장 시점과 똑같은 함수로 다듬어집니다. 다만 그 일을 하는 자리가 `SearchFilter` 가 아니라는 점이 중요합니다. `SearchFilter.__post_init__`(`domain/queries.py:54-55`)은 조건들을 명세 트리로 **조립만** 하고, 실제 정규화는 각 명세의 생성자가 합니다 — `specs.InCategory.__init__`(`domain/specs.py:199-200`)이 `validators.parse_category` 를 직접 부릅니다. 규칙이 한 곳(`domain/validators.py`)에만 있어야 "저장할 때의 규칙"과 "찾을 때의 규칙"이 갈라지지 않기 때문입니다. 갈라지면 검색은 오류 없이 조용히 틀립니다.

### 4.4 summary — 월별 요약

지정한 달의 총 수입/총 지출/잔액을 계산하고, 그 달의 예산이 설정되어 있으면 사용률과 초과 경고, 지출 상위 카테고리 TOP N 을 함께 보여줍니다.

| 옵션 | 의미 | 기본값 |
| --- | --- | --- |
| `--month` | 대상 월 `YYYY-MM` | (필수) |
| `--top` | 지출 TOP N | 5 (`services/config.py:17` 의 `DEFAULT_TOP_N`) |

```bash
python -m budget_app summary --month 2024-01 --top 3
```

```text
총 수입: 3000000원
총 지출: 215000원
잔액: 2785000원
예산: 500000원 (사용률 43.0%)

지출 TOP 3
1) rent 150000원
2) food 45000원
3) transport 20000원
```

지출이 예산을 초과하면 `[경고] 예산을 초과했습니다!` 가 추가로 출력됩니다(`cli/messages.py:58` 의 `MSG_OVER_BUDGET`). 해당 월에 거래도 없고 예산도 없으면 `2024-01: 데이터 없음` 형식으로 한 줄만 출력합니다.

### 4.5 budget set — 월 예산 설정

한 달 예산을 설정합니다. 같은 월에 다시 설정하면 덮어씁니다(`BudgetStore.set` 이 같은 달의 기존 항목을 지우고 새 값을 끝에 붙입니다 — `storage/repositories.py:300-308`).

| 옵션 | 의미 |
| --- | --- |
| `--month` | 대상 월 `YYYY-MM` (필수) |
| `--amount` | 예산 금액, 양의 정수 (필수) |

```bash
python -m budget_app budget set --month 2024-01 --amount 500000
```

```text
[저장 완료] 2024-01 예산 500000원
```

### 4.6 category add / list / remove — 카테고리 관리

거래에 쓸 카테고리를 관리합니다. 하위 명령 3개가 **각각 별도의 핸들러**를 가집니다(`cmd_category_add` / `cmd_category_list` / `cmd_category_remove`).

| 하위 명령 | 옵션 | 의미 |
| --- | --- | --- |
| `add` | `--name` (생략 시 대화형으로 물음) | 카테고리 추가 |
| `list` | 없음 | 카테고리 목록 출력 |
| `remove` | `--name` (필수), `--replace-with` | 카테고리 삭제 (사용 중이면 대체 필요) |

```bash
python -m budget_app category add --name groceries
python -m budget_app category list
python -m budget_app category remove --name food --replace-with etc
```

```text
[저장 완료] category=groceries
```

```text
- food
- transport
- rent
- salary
- etc
- groceries
```

```text
[완료] 'food' 삭제, 2건을 'etc' 로 재지정했습니다.
```

**사용 중인 카테고리는 보호됩니다.** 거래에서 쓰이고 있는 카테고리를 `--replace-with` 없이 삭제하려 하면 `[오류] 카테고리 'food' 는 거래에서 사용 중입니다.` 와 힌트가 출력되고 종료 코드 4로 끝납니다. `--replace-with` 를 지정하면 해당 거래들의 카테고리를 먼저 일괄 재지정한 뒤 삭제합니다(`services/categories.py:38-73` 의 `CategoryService.remove`). 이미 존재하는 이름을 add 하면 오류가 아니라 `[안내] 이미 존재하는 카테고리입니다: ...` 안내 후 정상 종료(0)합니다.

### 4.7 update — 거래 수정 (옵션 방식)

거래 1건을 수정합니다. **대화형이 아니라 옵션 방식으로 고정**되어 있습니다. `--id` 로 대상을 지정하고, 바꿀 필드만 옵션으로 넘깁니다.

| 옵션 | 의미 |
| --- | --- |
| `--id` | 수정 대상 거래 id (필수) |
| `--date` | 날짜 `YYYY-MM-DD` |
| `--type` | `income` / `expense` |
| `--category` | 카테고리 (등록된 것만) |
| `--amount` | 금액 (양의 정수) |
| `--memo` | 메모 |
| `--tags` | 쉼표로 구분한 태그 문자열 |

```bash
python -m budget_app update --id TX-000005 --amount 35000 --memo "회식"
```

```text
[수정 완료] id=TX-000005
TX-000005 | 2024-01-22 | expense | food | 35000 | 회식
```

수정 후 갱신된 행을 한 줄 다시 보여줍니다. 변경 필드를 하나도 지정하지 않으면 `[오류] 수정할 필드가 없습니다.` 와 힌트가 출력됩니다(종료 코드 4). 존재하지 않는 id 면 `[오류] 해당 id 의 거래를 찾을 수 없습니다: ...` 입니다.

내부적으로 변경 요청은 `TransactionPatch` dataclass 로 표현됩니다. 필드가 선언돼 있으므로 이름을 잘못 쓰면 조용히 무시되지 않고 즉시 `TypeError` 가 납니다([05 §4](./05-config-and-models.md)).

### 4.8 delete — 거래 삭제

| 옵션 | 의미 |
| --- | --- |
| `--id` | 삭제 대상 거래 id (필수) |

```bash
python -m budget_app delete --id TX-000005
```

```text
[삭제 완료] id=TX-000005
```

없는 id 를 지정하면 `update` 와 같은 `[오류] 해당 id 의 거래를 찾을 수 없습니다: ...` (종료 코드 4)입니다.

### 4.9 import — CSV 일괄 가져오기

CSV 파일의 거래들을 일괄 등록합니다. 필수 컬럼은 `date,type,category,amount` 이고, `id`·`memo`·`tags` 는 선택입니다. 미등록 카테고리는 자동 등록됩니다.

| 옵션 | 의미 | 기본값 |
| --- | --- | --- |
| `--from` | 입력 CSV 경로 (필수) | — |
| `--atomic` | 전수 롤백 모드 — 한 줄이라도 오류면 아무것도 저장하지 않음 | 꺼짐(부분 성공) |
| `--on-duplicate` | 이미 있는 id 를 만났을 때의 정책: `skip` / `new-id` / `error` | `skip` |

**두 정책 축은 서로 독립입니다.** `--atomic` 은 "데이터가 **잘못된** 줄"을 어떻게 다룰지, `--on-duplicate` 는 "이미 **저장된** 거래"를 어떻게 다룰지 정합니다. 함께 쓸 수 있습니다.

| `--atomic` | 손상된 줄이 있을 때 | 종료 코드 |
| --- | --- | --- |
| 없음 (기본, 부분 성공) | 그 줄만 건너뛰고(skip) 나머지는 저장 | 0 |
| 있음 (원자적·전수 롤백) | 첫 오류에서 중단, 아무것도 저장하지 않음 | 4 |

| `--on-duplicate` | 이미 있는 id 를 만났을 때 |
| --- | --- |
| `skip` (기본) | 건너뛰고 `duplicated` 로 집계 |
| `new-id` | 새 id 를 발급해 별도 거래로 추가 |
| `error` | `AppError` 로 중단 (아무것도 저장 안 됨, 종료 코드 4) |

```bash
python -m budget_app import --from import.csv
```

```text
[완료] mode=부분 성공, imported=2, duplicated=0, skipped=1
[오류 라인 일부]
  - line 3: 금액은 양의 정수여야 합니다 (0 또는 음수 불가).
```

```bash
python -m budget_app import --from import.csv --atomic
```

```text
[오류] 원자적 가져오기 실패 — line 3: 금액은 양의 정수여야 합니다 (0 또는 음수 불가). (반영된 항목 없음)
[힌트] CSV 를 고쳐 다시 시도하거나, --atomic 없이 부분 가져오기를 사용하세요.
```

`skipped` 와 `duplicated` 를 나눠 보여주는 이유는 **사용자가 해야 할 일이 정반대**이기 때문입니다. `skipped` 는 데이터가 잘못돼 CSV 를 고쳐야 하고, `duplicated` 는 이미 저장돼 있어서 아무것도 안 해도 됩니다. 한 숫자로 합치면 정상 왕복이 실패처럼 읽힙니다.

내부 동작은 두 단계로 나뉩니다 — 먼저 CSV 를 끝까지 읽으며 **메모리 위에서만** 거래 목록과 오류 목록을 만들고(`_prepare`), 그다음에 정책에 따라 파일에 반영합니다(`_commit`). `--atomic` 이 "아무것도 저장하지 않음"을 지킬 수 있는 것은 준비 단계가 파일을 전혀 바꾸지 않기 때문입니다. 커밋 방식은 모드에 따라 다릅니다 — 기본(부분 성공)은 파일 끝에 이어 쓰고(O(1)), `--atomic` 은 거래 파일과 카테고리 파일의 최종 내용을 각각 `.tmp` 로 만든 뒤 `os.replace` 두 번으로 갈아 끼웁니다. 자세한 것은 [08. 서비스 계층](./08-services.md)에 있습니다.

### 4.10 export — CSV 내보내기

기간 조건에 맞는 거래를 CSV 파일로 내보냅니다. **`--month` 또는 `--from/--to` 쌍 중 하나가 필수**입니다.

| 옵션 | 의미 | 기본값 |
| --- | --- | --- |
| `--out` | 출력 CSV 경로 (필수) | — |
| `--month` | 대상 월 `YYYY-MM` | — |
| `--from` / `--to` | 시작일 / 종료일 `YYYY-MM-DD` | — |
| `--no-id` | `id` 컬럼을 빼고 내보냄 (외부 도구용) | id 포함 |

기간 필수 규칙은 핸들러 코드에서 직접 확인할 수 있습니다.

budget_app/cli/handlers.py:160-173

```python
def _export_filter(args: argparse.Namespace) -> SearchFilter:
    """기간 조건은 필수 — ``--month`` 또는 ``--from``/``--to`` **중 하나**.

    둘을 함께 주면 오류로 막는다. 이전에는 ``--month`` 를 먼저 검사하고 나머지를
    **조용히 무시**했다. 사용자가 원한 것은 십중팔구 좁은 쪽인데 넓은 한 달이
    나가고, 파일에는 아무 표시도 남지 않는다. 무시할 바에는 묻는 편이 낫다.
    """
    if args.month and (args.from_ or args.to):
        raise AppError(messages.ERR_EXPORT_PERIOD_CONFLICT, hint=messages.HINT_EXPORT_PERIOD)
    if args.month:
        return SearchFilter.for_month(args.month)
    if args.from_ and args.to:
        return SearchFilter(date_from=args.from_, date_to=args.to)
    raise AppError(messages.ERR_EXPORT_PERIOD_REQUIRED, hint=messages.HINT_EXPORT_PERIOD)
```

`--month 2024-01` 을 주면 `SearchFilter.for_month`(`domain/queries.py:74-78`)가 `domain/periods.py:20-30` 의 `month_range` 를 통해 `2024-01-01` ~ `2024-01-31`(그 달의 실제 말일)로 변환합니다. 2월이나 30일까지인 달도 `calendar.monthrange` 로 정확한 말일을 계산합니다. **`summary` 도 같은 함수를 씁니다** — "이 달에 속하는가"의 정의가 프로그램 전체에서 하나입니다.

> **⚙️ 내부 동작** — `calendar.monthrange(year, month)` 는 `(그 달 1일의 요일, 그 달의 날 수)` 튜플을 돌려주므로 `[1]` 로 말일을 뽑습니다. 날 수 계산은 표에서 꺼내되 2월만 윤년 규칙(4로 나뉘고, 100 으로 나뉘면 제외하되 400 으로 나뉘면 다시 포함)으로 보정합니다 — 즉 근사가 아니라 그레고리력 규칙 그대로입니다. 이어지는 `f"{normalized}-{last_day:02d}"` 의 `:02d` 는 §4.2 에서 본 형식 명세 미니 언어로, `5` 를 `05` 로 만들어 문자열 날짜 비교가 성립하게 합니다. 날짜를 `YYYY-MM-DD` 고정폭으로 저장했기 때문에 **문자열 사전순 비교 = 시간순 비교**가 되고, 그래서 이 프로그램은 검색에서 `datetime` 객체를 만들지 않고 문자열끼리 비교합니다(`domain/specs.py:178-179`). → [12 §2-A](./12-syntax-and-stdlib.md)

```bash
python -m budget_app export --out export.csv --month 2024-01
python -m budget_app export --out range.csv --from 2024-01-01 --to 2024-03-31
python -m budget_app export --out plain.csv --month 2024-01 --no-id
```

```text
[완료] export.csv (5 records)
```

출력 CSV 는 UTF-8(BOM 없음), 헤더 포함이며 기본적으로 `id` 컬럼을 포함합니다.

```csv
id,date,type,category,amount,memo,tags
TX-000001,2024-01-15,expense,food,15000,점심,meal
TX-000002,2024-01-14,income,salary,3000000,월급,
TX-000004,2024-01-20,expense,rent,150000,공과금,
```

### 4.11 backup — 데이터 폴더 백업 (보너스)

`data/` 폴더의 모든 `*.jsonl` 파일을 타임스탬프가 붙은 새 폴더로 복사합니다. 옵션은 `--data-dir` 뿐입니다.

```bash
python -m budget_app backup
```

```text
[백업 완료] backup_20240115_103000
```

백업 폴더는 데이터 폴더의 **부모 디렉터리** 아래에 `backup_YYYYMMDD_HHMMSS` 이름으로 생성됩니다(`storage/backup.py:17-33` 의 `backup_data_dir`, 접두사와 시각 형식은 `storage/config.py:30-31` 의 `BACKUP_DIR_PREFIX` 와 `BACKUP_TS_FORMAT`). 기본 `./data` 기준으로는 프로젝트 루트에 만들어집니다. 복사 대상은 `*.jsonl` 세 파일에 더해 확장자가 없는 `id_counter` 파일까지입니다 — 이것을 빠뜨리면 백업을 되돌렸을 때 "이미 발급한 번호" 기록이 사라져 삭제된 id 가 재사용됩니다(`storage/backup.py:36-47`).

> **⚙️ 내부 동작** — 시각 문자열은 `datetime.strftime("%Y%m%d_%H%M%S")` 로 만듭니다. `strftime` 의 `%` 지시자 집합은 파이썬이 정한 것이 아니라 **C 표준 라이브러리의 `strftime(3)`** 에서 온 것이고, 그래서 일부 지시자(`%-d` 같은 것)는 플랫폼마다 다릅니다. 여기서 쓰는 `%Y%m%d_%H%M%S` 는 C89 에 있는 것뿐이라 어디서나 같게 동작합니다. 폴더를 만들 때 `mkdir(parents=True, exist_ok=False)` 로 `exist_ok` 를 **꺼 둔 것**도 의도입니다 — 같은 초에 두 번 백업하면 조용히 덮어쓰는 대신 `FileExistsError` 로 멈춥니다. → [12 §2-A](./12-syntax-and-stdlib.md)

`backup` 은 유일하게 `needs_storage=False` 인 명령입니다. 존재하지 않는 폴더를 백업하려 하면 폴더를 만드는 대신 종료 코드 3(`FileNotFoundError`)으로 알려 줍니다. 폴더를 자동 생성해 버리면 "백업할 데이터가 없다"는 사실 대신 **빈 백업**이 만들어지기 때문입니다.

---

## 5. 데이터 파일 3종과 기본 카테고리 시드

### 5.1 JSONL 형식

세 파일 모두 **JSONL(JSON Lines)** 형식입니다. "한 줄 = JSON 객체 1개 = 레코드 1건" 이라는 단순한 규칙으로, 텍스트 에디터로 열어 바로 읽을 수 있습니다.

> **🔎 문법의 출처** — JSONL 은 **공식 표준이 아닙니다.** JSON 자체는 RFC 8259 로 표준화돼 있지만, "줄바꿈으로 JSON 값을 잇는다"는 규약은 표준 문서 없이 굳어진 **관행**이고 `jsonlines.org` 라는 비공식 문서와 `.jsonl` 확장자로 통용됩니다(`ndjson` 이라는 다른 이름도 같은 것을 가리킵니다). 그래서 파이썬 표준 라이브러리에는 `jsonl` 모듈이 없고, 이 프로젝트도 `json.dumps` 한 줄과 `"\n"` 로 직접 만듭니다(`storage/jsonl.py:207-208`). 규약이 이렇게 단순하기 때문에 **줄 하나가 깨져도 나머지 줄은 멀쩡**하고, 그것이 이 프로젝트가 손상 줄을 격리해 살려 두는 설계의 전제입니다. → [12 §2-A](./12-syntax-and-stdlib.md)

| 파일 | 내용 | 실제 예시 줄 |
| --- | --- | --- |
| `data/transactions.jsonl` | 거래 내역 | `{"id":"TX-000001","type":"expense","date":"2024-01-15","amount":15000,"category":"food","memo":"점심","tags":["meal"]}` |
| `data/categories.jsonl` | 카테고리 목록 | `{"name":"food"}` |
| `data/budgets.jsonl` | 월별 예산 | `{"month":"2024-01","amount":500000}` |

파일명은 `TX_FILE_NAME` / `CATEGORY_FILE_NAME` / `BUDGET_FILE_NAME`(`storage/config.py:17-19`)으로 중앙 관리됩니다. 거래 id 는 `TX-000001` 처럼 `TX-` 뒤에 6자리 연번이 붙는 형식(`domain/config.py:26` 의 `TX_ID_FORMAT = "TX-{:06d}"`)이며, 저장소가 자동 발급합니다. 왜 내부 저장을 CSV 가 아닌 JSONL 로 했는지(타입 보존, append O(1), 스트리밍, 손상 격리)는 README.md 8절과 [07. 저장소 계층](./07-repository.md)에서 다룹니다.

위 예시 줄에서 한글 메모가 `\uc810\uc2ec` 같은 이스케이프가 아니라 `점심` 그대로 보이는 것도 우연이 아닙니다.

budget_app/storage/jsonl.py:207-208

```python
    def _encode(self, entity: T) -> str:
        return json.dumps(entity.to_dict(), ensure_ascii=False)
```

> **⚙️ 내부 동작** — `json.dumps` 의 `ensure_ascii` 는 **기본값이 `True`** 이고, 그 상태에서는 ASCII 범위를 벗어난 모든 문자를 `\uXXXX` 이스케이프로 바꿉니다(`json.dumps({"memo":"점심"})` → `{"memo": "\uc810\uc2ec"}`). 옛날 환경에서 파일이 순수 ASCII 로만 오가게 하려던 배려인데, 지금은 사람이 파일을 열어 읽을 수 없게 만드는 손해가 더 큽니다. `ensure_ascii=False` 로 끄면 문자를 그대로 내보내고, 실제 바이트는 파일을 열 때 지정한 인코딩(`storage/config.py:22` 의 `FILE_ENCODING = "utf-8"`)이 결정합니다. 두 방식 모두 **같은 JSON 을 표현**하므로 `json.loads` 로 읽으면 결과는 동일합니다 — 바뀌는 것은 사람이 읽을 수 있는지뿐입니다. → [12 §2-A](./12-syntax-and-stdlib.md)

### 5.2 폴더·파일 자동 생성

`data/` 폴더와 세 파일은 미리 만들 필요가 없습니다. `AppContext.prepare()` 가 각 저장소의 `ensure_ready()` 를 불러 폴더를 만들고, 파일이 없으면 빈 파일을 `touch()` 로 생성합니다.

budget_app/storage/jsonl.py:150-154

```python
    def ensure_ready(self) -> None:
        """파일이 없으면 만든다 — 명시적으로 호출될 때만 디스크를 건드린다."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()
```

> **⚙️ 내부 동작** — 두 줄 다 `pathlib` 이지만 실제 일은 `os` 가 합니다. `Path.mkdir(parents=True, exist_ok=True)` 는 `os.mkdir` 를 부르고 `FileNotFoundError` 가 나면 부모를 먼저 만든 뒤 재시도하며(그것이 `parents=True`), `FileExistsError` 는 `exist_ok=True` 일 때 삼킵니다. `Path.touch()` 는 (기본값 `exist_ok=True` 에서) 먼저 `os.utime(path, None)` 으로 수정 시각만 갱신해 보고, 파일이 없어 실패하면 `os.open(path, O_CREAT | O_WRONLY)` 로 만든 뒤 곧바로 닫습니다 — 즉 **비어 있는 파일이 생기고 기존 내용은 잘리지 않습니다**(`O_TRUNC` 가 없습니다). 그래서 `exists()` 검사를 빼도 데이터가 날아가지는 않지만, 코드가 "없을 때만 만든다"는 의도를 말하도록 검사를 남겨 두었습니다. → [12 §2-B](./12-syntax-and-stdlib.md)

### 5.3 기본 카테고리 자동 시드

카테고리 파일이 **비어 있으면** 기본 카테고리 5종이 자동 등록됩니다.

budget_app/storage/repositories.py:226-235

```python
    def seed_defaults(self) -> int:
        """비어 있을 때만 기본 카테고리를 심는다. 심은 개수를 반환.

        "파일을 만드는 일"(``ensure_ready``)과 "초기 데이터를 넣는 일"은 다른 작업이라
        메서드를 나눴다. 둘 다 생성자가 아니라 명시적 호출인 이유는 부트스트랩이
        *한 번* 일어나야 하는 일이지 객체를 만들 때마다 일어날 일이 아니기 때문이다.
        """
        if not self.is_empty:
            return 0
        return self.append_all(Category(name=name) for name in config.DEFAULT_CATEGORIES)
```

> **🔎 문법의 출처** — `append_all(Category(name=name) for name in ...)` 에서 괄호 없이 바로 들어간 것이 **제너레이터 표현식**입니다(PEP 289, 파이썬 2.4). 리스트 컴프리헨션 `[...]` 이 5개를 전부 만들어 리스트에 담는 반면, 이것은 값을 요구받을 때 하나씩 만듭니다. 함수 호출의 **유일한 인자**일 때만 이렇게 바깥 괄호를 생략할 수 있고, 인자가 둘 이상이면 `f(x, (i for i in y))` 처럼 괄호를 써야 합니다. 이 소스에서 5개짜리 시드에 굳이 제너레이터를 쓴 것은 성능 때문이 아니라 `append_all` 의 매개변수 타입이 `Iterable` 이라 호출부가 리스트를 만들 이유가 없기 때문입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

기본 카테고리 목록은 `storage/config.py` 에 상수로 정의되어 있습니다.

budget_app/storage/config.py:13-14

```python
# 부트스트랩
DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "etc")
```

설계 의도는 "처음 쓰는 사용자가 `category add` 를 먼저 하지 않아도 `add` 를 바로 시도할 수 있게" 하는 것입니다. 조건이 "파일이 없을 때"가 아니라 "파일이 **비어 있을 때**"(`is_empty` — 파일 크기 0 검사)라는 점이 중요합니다. 사용자가 모든 카테고리를 의도적으로 지운 경우 파일은 존재하지만 크기가 0이므로, 다음 실행에서 기본 5종이 다시 시드됩니다. 반대로 카테고리가 하나라도 있으면 시드는 건너뜁니다.

---

## 6. 종료 코드 표

콘솔 프로그램은 종료 코드(exit code)로 성공/실패의 종류를 호출자(셸, 스크립트, 채점기)에게 알립니다. 이 프로젝트는 8종을 `cli/config.py` 에 상수로 정의합니다. 종료 코드가 도메인이나 저장소가 아니라 **CLI 계층**의 config 에 있는 이유는 "셸에게 무엇을 말할 것인가"가 CLI 의 계약이기 때문입니다 — 서비스는 `AppError` 를 던질 뿐 그것이 4번인지 모릅니다.

budget_app/cli/config.py:22-29

```python
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_VALIDATION = 2
EXIT_IO = 3
EXIT_APP = 4
EXIT_NO_CATEGORY = 5
EXIT_ENCODING = 6
EXIT_INTERRUPT = 130
```

| 코드 | 상수 | 의미 | 발생 예 |
| --- | --- | --- | --- |
| 0 | `EXIT_OK` | 정상 종료 | 모든 성공 케이스 |
| 1 | `EXIT_ERROR` | 예기치 못한 오류 | 분류되지 않은 `Exception` |
| 2 | `EXIT_VALIDATION` | 입력 검증 실패 (`ValidationError`) | 잘못된 날짜/금액/id 형식. **argparse 의 인자 오류도 같은 2** — 아래 참고 |
| 3 | `EXIT_IO` | 파일 입출력 오류 | 파일 없음, 디렉터리 지정, 권한 없음, 디스크 오류 |
| 4 | `EXIT_APP` | 애플리케이션 오류 (`AppError`) | 없는 id, 미등록 카테고리, `--atomic` import 실패, `--on-duplicate error` |
| 5 | `EXIT_NO_CATEGORY` | 카테고리 미등록 상태에서 `add` 시도 | 카테고리 파일을 모두 비운 특수 상황 |
| 6 | `EXIT_ENCODING` | 파일 인코딩 오류 (UTF-8 아님) | CP949 로 저장된 CSV import |
| 130 | `EXIT_INTERRUPT` | 사용자 Ctrl+C 중단 | 대화형 입력 중 `KeyboardInterrupt` |

예외를 어느 코드로 매핑할지는 `cli/error_handler.py:20-121` 의 `@handle_errors` 데코레이터가 한곳에서 결정합니다(예: `ValidationError → EXIT_VALIDATION`, `FileNotFoundError → EXIT_IO`). 자세한 원리는 [06. 횡단 관심사와 예외 처리](./06-decorators.md)에서 설명합니다.

> **🔎 관례의 출처 (130 = 128 + 2)** — 이것은 파이썬 규칙이 아니라 **셸의 관례**입니다. POSIX 셸은 자식 프로세스가 신호로 죽으면 `$?` 를 `128 + 신호번호` 로 보고합니다. `Ctrl+C` 가 보내는 SIGINT 의 번호가 2 이므로 `128 + 2 = 130` 입니다. 그래서 유닉스 도구들이 Ctrl+C 중단을 130 으로 알리고, 이 프로그램도 같은 숫자를 씁니다 — 실제로 신호에 죽는 것이 아니라 `KeyboardInterrupt` 를 잡아 130 을 **직접 반환**하는데, 호출자 입장에서 구분할 필요가 없는 값을 굳이 다르게 할 이유가 없기 때문입니다. 참고로 이 프로그램에서 신호는 하나도 직접 다루지 않습니다(`signal` 모듈을 import 하는 곳이 없습니다) — `Ctrl+C` 는 파이썬 런타임이 `KeyboardInterrupt` 예외로 바꿔 주고, 그 예외를 `handle_errors` 가 잡습니다. → [12 §3](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — 2번은 두 갈래이고, 한쪽은 `handle_errors` 를 지나지 않습니다.** `--limit 0` 이나 없는 하위 명령처럼 **argparse 가 거절한** 인자는 `parser.error()` → `parser.exit(2, …)` → `sys.exit(2)` 를 거칩니다. §3.2 에서 본 대로 `sys.exit` 은 `SystemExit` 예외이고, `SystemExit` 은 `Exception` 이 아니라 **`BaseException` 의 직계 자식**입니다. 그래서 `handle_errors` 의 마지막 그물인 `except Exception` 에 걸리지 않습니다 — 애초에 걸릴 기회도 없습니다. `parse_args()` 는 `main()` 안에서 `_dispatch()` 보다 **먼저** 호출되고 `@handle_errors` 는 `_dispatch` 에만 붙어 있으니, argparse 오류는 방패 바깥에서 usage 를 stderr 로 찍고 프로세스를 끝냅니다. `main()` 의 `except BrokenPipeError` 도 `SystemExit` 을 잡지 않으므로 그대로 통과합니다. 결과적으로 같은 숫자 2 가 **두 경로**로 나오지만, 하나는 `[오류]`/`[힌트]` 두 줄이고 다른 하나는 argparse 의 `usage:` 블록이라 화면으로 구분됩니다. → [12 §1-C](./12-syntax-and-stdlib.md)

셸에서 직접 확인하려면 명령 실행 직후 PowerShell 은 `$LASTEXITCODE`, bash 는 `$?` 를 출력해 보면 됩니다.

```text
$ python -m budget_app badcmd        ; echo $?   # argparse 거절 → 2 (usage 출력)
$ python -m budget_app list --limit 0; echo $?   # positive_int 의 ArgumentTypeError → 2
$ python -m budget_app delete --id TX-999999 ; echo $?   # AppError → 4
$ python -m budget_app backup --data-dir ./없는폴더 ; echo $?   # FileNotFoundError → 3
```

---

## 7. 개발 도구 — pyproject.toml 해설

`pyproject.toml` 은 파이썬 프로젝트의 표준 설정 파일입니다. 이 프로젝트에서는 (1) 프로젝트 메타데이터, (2) uv 실행 방식, (3) Ruff 린터/포매터 설정, (4) pytest 설정, 네 가지 역할을 합니다.

> **🔎 문법의 출처 — TOML 이라는 형식과 `[project]` 라는 이름** — 파일 형식은 **TOML**(Tom's Obvious, Minimal Language)입니다. `[대괄호]` 한 줄이 테이블(섹션)을 열고, 점이 들어간 `[tool.ruff.lint]` 는 중첩 테이블을 뜻합니다 — JSON 으로 치면 `{"tool": {"ruff": {"lint": {...}}}}` 입니다. 파이썬이 이 파일을 프로젝트 설정 자리로 정한 것은 PEP 518 이고(그때는 `[build-system]` 하나뿐이었습니다), `[project]` 테이블에 이름·버전·의존성을 적는 지금의 표기는 **PEP 621** 이 정했습니다. 그리고 이 형식을 읽는 파서가 파이썬 3.11 부터 표준 라이브러리 `tomllib` 로 들어왔습니다(PEP 680) — 그전에는 외부 패키지가 필요했습니다. 즉 이 파일은 파이썬 코드가 아니라 **데이터**이고, `import` 하듯 실행되지 않습니다. → [12 §2-B](./12-syntax-and-stdlib.md)

> **🔎 `[tool.*]` 는 도구들이 나눠 쓰는 이름 공간입니다.** PEP 518 이 "`[tool.<도구이름>]` 아래는 그 도구가 마음대로 쓴다"고 못 박아 두었기 때문에, `[tool.uv]` 는 uv 만, `[tool.ruff]` 는 Ruff 만, `[tool.pytest.ini_options]` 는 pytest 만 읽습니다. 서로의 키를 검사하지도 않고, 모르는 테이블은 그냥 무시합니다. 그래서 도구를 하나 걷어내려면 그 도구의 테이블만 지우면 되고, 설정 파일이 `setup.cfg`·`.flake8`·`pytest.ini` 처럼 여러 개로 흩어지지 않습니다. 반대로 `[project]` 는 특정 도구의 것이 아니라 **표준 스키마**라 아무 도구나 같은 뜻으로 읽습니다.

### 7.1 프로젝트 메타데이터 — 의존성 0

pyproject.toml:7-12

```toml
[project]
name = "budget-app"
version = "0.1.0"
description = "파일 기반 가계부 콘솔 프로그램 (표준 라이브러리만 사용)"
requires-python = ">=3.10"
dependencies = []
```

`dependencies = []` 가 "표준 라이브러리만 사용" 제약을 선언적으로 보여줍니다. `requires-python = ">=3.10"` 은 이 코드가 `tuple[str, str]` 같은 내장 제네릭 표기(PEP 585, 3.9+)와 `list[str] | None` 같은 유니온 표기(PEP 604, 3.10+)를 쓰기 때문입니다. 둘 중 더 높은 3.10 이 하한선이 됩니다.

> **🔎 문법의 출처** — `">=3.10"` 이라는 문자열의 문법은 TOML 이 정한 것도, uv 가 정한 것도 아니고 **PEP 440** 의 버전 명세(version specifier)입니다. `>=`, `==`, `!=`, `~=`(호환 릴리스), `<` 를 쉼표로 이어 붙일 수 있고, `dependencies` 목록에 적는 `"requests>=2,<3"` 같은 표기도 같은 문법 위에 PEP 508 이 정의한 형태입니다. 이 프로젝트는 `dependencies = []` 라 PEP 508 쪽은 쓸 일이 없습니다. 그리고 이 값은 **선언일 뿐 인터프리터가 강제하지 않습니다** — `python -m budget_app` 은 `pyproject.toml` 을 읽지도 않습니다. 이 줄을 보고 거절하는 것은 이 파일을 읽는 설치·실행 도구(uv, pip) 쪽입니다.

### 7.2 `[tool.uv] package = false` 의 의미

pyproject.toml:14-16

```toml
# 애플리케이션(빌드/설치 대상 아님).
[tool.uv]
package = false
```

uv 는 파이썬 패키지/프로젝트 관리 도구입니다. 기본적으로 uv 는 `pyproject.toml` 이 있는 프로젝트를 "빌드해서 가상환경에 설치할 패키지"로 취급하려 합니다. `package = false` 는 그 동작을 끄는 스위치로, **"이건 배포용 라이브러리가 아니라 그 자리에서 실행하는 애플리케이션이다"** 라는 선언입니다. 이 설정 덕분에 빌드 시스템(`[build-system]`) 정의 없이도 uv 환경에서 오류가 나지 않고, 실행은 오직 `python -m budget_app` 으로만 합니다.

### 7.3 Ruff — 린터 + 포매터

pyproject.toml:19-28

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
# E/F: pyflakes+pycodestyle, I: isort, UP: pyupgrade, B: bugbear
select = ["E", "F", "I", "UP", "B"]

[tool.ruff.format]
quote-style = "double"
```

Ruff 는 여러 기존 린터의 규칙을 하나로 통합한 고속 린터/포매터입니다. `select` 에 지정한 다섯 규칙군의 의미는 다음과 같습니다.

| 코드 | 유래 도구 | 잡아내는 것 |
| --- | --- | --- |
| `E` | pycodestyle (Error) | PEP 8 스타일 위반 — 들여쓰기, 공백, 줄 길이 등 |
| `F` | Pyflakes | 논리적 결함 — 사용하지 않는 import/변수, 정의되지 않은 이름 등 |
| `I` | isort | import 문 정렬·그룹화 (표준 라이브러리 → 서드파티 → 로컬 순) |
| `UP` | pyupgrade | 구식 문법 — 예: `typing.List` 대신 내장 `list` 사용 권장 |
| `B` | flake8-bugbear | 버그가 되기 쉬운 패턴 — 예: 가변 기본 인자, 루프 변수 캡처 |

- `line-length = 100`: 한 줄 최대 100자입니다. PEP 8 기본(79자)보다 넉넉하게 잡아, 한국어 문자열 템플릿과 긴 함수 시그니처가 어색하게 줄바꿈되지 않도록 했습니다.
- `target-version = "py310"`: `UP` 규칙이 "3.10 에서 쓸 수 있는 최신 문법"을 기준으로 판단하게 합니다.
- `quote-style = "double"`: 포매터가 문자열 따옴표를 큰따옴표로 통일합니다.

참고로 소스의 `# noqa` 주석(`cli/error_handler.py:106` 의 `except Exception as exc:  # noqa: BLE001`)은 특정 줄에서 특정 린트 규칙을 의도적으로 끄는 표기입니다.

> **🔎 표기의 출처** — `# noqa` 는 파이썬 문법이 아니라 **그냥 주석**입니다. 인터프리터는 이 줄을 완전히 무시하고, 린터만 소스를 텍스트로 읽으며 이 주석을 봅니다. 이름은 "**no** **q**uality **a**ssurance" 에서 왔고 flake8 계열이 굳힌 관례를 Ruff 가 그대로 따릅니다. 콜론 뒤에 규칙 코드를 적으면(`# noqa: BLE001`) **그 규칙만** 끄고, 코드 없이 `# noqa` 만 쓰면 그 줄의 모든 규칙이 꺼집니다 — 후자는 나중에 진짜 문제가 생겨도 조용해지므로 코드를 명시하는 편이 낫습니다. `BLE001` 은 flake8-blind-except 계열의 "포괄적 `except Exception`" 경고인데, `handle_errors` 의 (4)번 최후 방어선은 **의도적으로** 모든 예외를 잡는 자리라 이 줄에서만 껐습니다.

### 7.4 pytest 설정과 "블랙박스 계약 테스트"

pyproject.toml:30-34

```toml
# ---------- pytest ----------
# 런타임 의존성은 여전히 0 이다. pytest 는 개발 도구이며 .venv 에만 있다.
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
```

`testpaths = ["tests"]` 는 `pytest` 를 인자 없이 실행했을 때 뒤질 폴더를, `addopts = "-q"` 는 매번 자동으로 붙일 옵션(조용한 출력)을 지정합니다. 실제로 이 저장소에는 `tests/` 폴더가 있고 `conftest.py` 와 `test_*.py` 6개가 들어 있습니다.

여기서 **pytest 가 `dependencies` 에 없다는 점**이 중요합니다. `[project].dependencies` 는 "이 프로그램을 **실행**하는 데 필요한 것"이고 pytest 는 개발할 때만 쓰는 도구이므로, 런타임 의존성 0 이라는 선언은 그대로 유효합니다. `[tool.pytest.ini_options]` 는 §7 서두에서 본 대로 pytest 만 읽는 이름 공간이라, pytest 가 없는 환경에서 `python -m budget_app` 을 실행하는 데에도 아무 영향이 없습니다.

한편 파일 최상단 주석은 **다른 종류의 테스트**를 이야기합니다.

pyproject.toml:1-5

```toml
# ============================================================
# budget_app 설정 — 런타임 의존성 0 (표준 라이브러리만 사용).
# 린트/포맷은 Ruff(전역 도구)를 쓴다. 별도 런타임/개발 패키지는 없다.
# (블랙박스 계약 테스트는 별도 그레이더 저장소로 분리되었다.)
# ============================================================
```

핵심 문장은 "**블랙박스 계약 테스트는 별도 그레이더 저장소로 분리되었다**" 입니다. 여기서 "블랙박스 계약 테스트"란 내부 구현을 들여다보지 않고, 프로그램을 실제 명령(`python -m budget_app ...`)으로 실행해 **입력 → 출력·종료 코드·파일 상태**라는 외부 계약만 검증하는 테스트를 말합니다. 이런 테스트는 소스 코드 import 없이 실행 파일만 있으면 되므로 채점기 쪽에 두는 편이 자연스럽습니다. 분리해 두면 채점기가 구현 저장소와 독립적으로 계약을 검증할 수 있습니다.

정리하면 테스트는 두 곳에 나뉘어 있습니다 — **바깥의 그레이더**가 외부 계약(명령 → 출력·종료 코드)을 검증하고, **이 저장소의 `tests/`** 는 그와 별개로 데이터 무결성·저장소 동작·CLI 동작·계층 규칙 같은 내부 약속을 검증합니다(`tests/test_architecture.py` 는 "도메인은 자기보다 위 계층을 import 하지 않는다", "CLI 는 저장소를 직접 import 하지 않는다" 같은 **계층 규칙 자체**를 import 그래프로 검사합니다 — 문서에만 적어 둔 원칙이 아니라 어기면 테스트가 깨지는 규칙입니다).

이 문서에서 정리한 종료 코드 표(§6)와 출력 메시지가 바로 그 "계약"의 실체이며, 출력 문자열을 계층별 `messages.py` 에 모아 둔 것도 계약 문면을 한 파일에서 관리하기 위한 설계와 맞물립니다.

---

## 8. 정리와 다음 문서

이 문서에서 확인한 것을 요약합니다.

- budget_app 은 **표준 라이브러리만으로 만든 파일 기반 가계부 콘솔 앱**이며, 과제 명세에 따라 생성된 코드를 학습·설명하는 것이 이 문서 시리즈의 목적입니다.
- 실행은 `python -m budget_app` 으로 하며, `runpy` 가 패키지를 import 한 뒤 `__main__.py` → `cli/app.py` 의 `main()` → `_dispatch()`(오류 방패) → `AppContext` 조립 → `HANDLERS[args.handler]` → 종료 코드 반환의 흐름입니다. `sys.exit()` 은 그 정수를 담은 `SystemExit` 예외를 던지는 함수입니다.
- 명령은 11종: `add`(대화형), `list`, `search`, `summary`, `budget set`, `category add/list/remove`, `update`(옵션 방식 고정), `delete`, `import`(`--atomic`·`--on-duplicate`), `export`(기간 필수, `--no-id`), `backup`.
- 데이터는 JSONL 파일 3종에 저장되고, 카테고리 파일이 비어 있으면 기본 5종이 자동 시드됩니다.
- CSV 교환 스키마는 `id` 를 **선택 컬럼**으로 포함합니다. 내보내기는 기본 포함, 가져오기는 있으면 복원·없으면 발급이라 왕복해도 중복이 생기지 않습니다.
- 종료 코드 8종은 `cli/config.py` 의 `EXIT_*` 상수로 정의되고 `@handle_errors` 가 매핑합니다. 다만 argparse 가 거절한 인자의 2번은 `SystemExit`(= `BaseException`) 이라 그 방패를 **지나지 않습니다**.
- pyproject.toml 은 PEP 621 의 `[project]` 로 의존성 0 을 선언하고, 나머지는 도구별 이름 공간(`[tool.uv]`·`[tool.ruff]`·`[tool.pytest.ini_options]`)입니다. 테스트는 저장소 안의 `tests/`(내부 규칙)와 바깥 그레이더(외부 계약)로 나뉘어 있습니다.

다음으로 읽기를 권하는 문서는 전체 구조를 계층 관점에서 설명하는 [04. 아키텍처](./04-architecture.md)입니다. 이 문서에서 "그런 파일이 있다" 수준으로 소개한 각 모듈이 왜 그렇게 나뉘었는지를 다룹니다. 이 문서 곳곳의 **🔎 문법의 출처** / **⚙️ 내부 동작** 노트를 더 깊게 파고든 참조 문서는 [12. 문법과 표준 라이브러리](./12-syntax-and-stdlib.md)입니다.
