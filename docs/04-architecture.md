# 04. 아키텍처 — 계층 구조와 설계 원칙

이 문서는 budget_app 이 왜 43개 파일(구현 38 + 패키지 선언 `__init__.py` 5)로 나뉘어 있는지, 명령 하나가 파일 저장까지 어떤 경로를 지나가는지, 그리고 그 구조가 어떤 설계 원칙과 리팩터링 과정을 거쳐 만들어졌는지를 코드로 실증합니다.

> **난이도**: 🟡 중급
>
> **먼저 읽으면 좋은 문서**: 없음 — 이 편은 전체 코드의 "지도" 역할을 하므로 시리즈의 다른 편보다 먼저 읽어도 됩니다. 개별 기법(데코레이터, dataclass, 제너레이터 등)의 상세는 [03. 파이썬 중·고급 기법](./03-python-advanced.md)에서, 각 문법이 **어느 PEP·어느 버전에서 왔고 파이썬이 그것을 무엇으로 바꾸는지**와 표준 라이브러리 호출의 내부 동작은 [12. 문법·표준 라이브러리 레퍼런스](./12-syntax-and-stdlib.md)에서 다룹니다. 이 문서 곳곳의 🔎/⚙️ 블록이 그 요약이자 링크입니다.

---

## 1. 전체 그림 — 계층 다이어그램

budget_app 은 "명령을 받는 곳(CLI) → 규칙을 판단하는 곳(서비스) → 파일을 읽고 쓰는 곳(저장소) → 데이터가 무엇인지 정의하는 곳(도메인)" 순서로 **한 방향으로만 의존하는** 구조입니다.

```
 사용자 터미널
      │  python -m budget_app add ...
      ▼
┌──────────────────────────────────────────────────────────────┐
│  __main__.py        엔트리포인트 — main() 호출, 종료 코드 전달  │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  cli/               CLI 계층                                   │
│    app.py           HANDLERS 레지스트리 + main                  │
│    handlers.py      cmd_* 13개 (오케스트레이션만)               │
│    parser.py        argparse 문법 정의                          │
│    prompts.py       대화형 입력 (재입력 루프 / EOF)             │
│    presenter.py     도메인 → 화면 문자열 (반환만, 출력 안 함)    │
│    output.py        채널 결정 — stdout / stderr / logging       │
│    error_handler.py 예외 → 사용자 메시지 → 종료 코드            │
│    config/messages  이 계층 전용 상수·문구                       │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  context.py         합성 루트 — 저장소·서비스 조립 (계층 밖)     │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  services/          서비스 계층 — 판단만 (open() 이 0개)        │
│    transactions / budgets / categories / importexport         │
│    config/messages  중복 정책·한도, AppError 문구               │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  storage/           저장소 계층 — open() 은 전부 여기           │
│    jsonl.py         JsonlStore / RawLine / stage·commit        │
│    ids.py           IdAllocator                                │
│    repositories.py  거래·카테고리·예산 저장소                    │
│    csv_io.py        CSV 경계 어댑터                             │
│    unit_of_work.py  UnitOfWork — 다중 파일 커밋                 │
│    backup.py        데이터 폴더 백업                            │
│    config/messages  파일명·인코딩·CSV 스키마, 로그 문구          │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  domain/            도메인 계층 — I/O 를 전혀 모름              │
│    tx_id.py         TransactionId 값 객체                       │
│    entities.py      Transaction / Budget / Category / Patch    │
│    specs.py         Specification — 조합 가능한 조건            │
│    queries.py       SearchFilter (명세 조립 어댑터)             │
│    results.py       MonthlySummary / ImportReport              │
│    periods.py       month_range                                │
│    validators.py    규칙 하나 = 함수 하나                        │
│    config/messages  타입·날짜 형식·id 패턴, 검증 오류 문구       │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  (루트)             횡단 — 어느 계층에도 속하지 않음             │
│    errors.py        ValidationError / AppError (import 0개)    │
│    config.py        앱 정체성(로거 이름)                        │
│    decorators.py    @log_call / @measure_time                  │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  data/*.jsonl       transactions / categories / budgets        │
└──────────────────────────────────────────────────────────────┘
```

**폴더 이름이 곧 계층입니다.** 평평하게 두면 알파벳순이 계층을 흩뜨립니다 — `cli(L6) config(L0) csv_io(L3) decorators(L3) error_handler(L5) errors(L0) …` 처럼 계층 번호가 뒤죽박죽 나열됩니다. 횡단 4개만 폴더 없이 루트에 두어 "이들은 계층이 아니다"를 위치로 표현합니다.

핵심 규칙은 **화살표가 아래로만 향한다**는 것입니다. `storage/` 는 `services/` 를 모르고, `services/` 는 `cli/` 를 모릅니다. 아래 계층은 위 계층이 누구인지 신경 쓰지 않으므로, 예를 들어 나중에 CLI 대신 웹 UI 를 붙여도 `services/` 이하는 한 줄도 바꿀 필요가 없습니다.

> **⚙️ 내부 동작** — 맨 위의 `python -m budget_app` 은 셸이 `budget_app` 이라는 파일을 찾는 것이 아닙니다. `-m` 은 인터프리터가 `runpy` 모듈로 넘어가라는 지시이고, `runpy` 는 이름이 패키지면 그 안의 `__main__.py` 를 찾아 **`__name__` 을 `"__main__"` 으로 바꿔 실행**합니다. 그래서 이 프로젝트에는 `budget_app/__main__.py` 가 8줄짜리로 존재합니다. `sys.path[0]` 이 현재 디렉터리가 되므로 `budget_app` 패키지가 import 가능해지고, 아래에서 설명할 상대 import 가 전부 성립합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

### 1.1 왜 이렇게 잘게 나눴나 — "파일 하나 = 책임 하나"

구현 파일이 38개(패키지 선언 `__init__.py` 5개 제외, 전체 4,203줄)인 것이 많아 보일 수 있습니다. 판단 기준은 **"이 파일을 고칠 이유가 몇 개인가"** 입니다.

리팩터 전의 `cli.py` 는 512줄이었고, 고칠 이유가 네 개였습니다.

| 고칠 이유 | 예 |
|---|---|
| 명령줄 문법이 바뀔 때 | 새 옵션 추가 |
| 대화형 입력 정책이 바뀔 때 | 재입력 횟수 변경 |
| 화면 표시가 바뀔 때 | 표 컬럼 순서 변경 |
| 명령 처리 순서가 바뀔 때 | 검증 시점 이동 |

지금은 각각 `cli/parser.py` / `cli/prompts.py` / `cli/presenter.py` / `cli/handlers.py` 로 나뉘어 파일마다 이유가 하나입니다(`cli/app.py` 는 그 넷을 엮는 레지스트리와 진입점만 남았습니다). 파일 크기도 함께 줄었습니다.

아래는 상위 파일들의 실제 줄 수입니다(주석·docstring 포함).

| 파일 | 줄 수 | 파일 | 줄 수 |
|---|---|---|---|
| storage/jsonl.py | 329 | domain/validators.py | 169 |
| storage/repositories.py | 308 | storage/csv_io.py | 163 |
| domain/specs.py | 243 | cli/presenter.py | 141 |
| cli/parser.py | 243 | domain/tx_id.py | 132 |
| services/importexport.py | 206 | cli/prompts.py | 128 |
| domain/entities.py | 190 | cli/messages.py | 121 |
| cli/handlers.py | 190 | cli/error_handler.py | 121 |
| storage/unit_of_work.py | 181 | storage/ids.py | 116 |

나머지 22개 구현 파일은 전부 100줄 이하입니다(`cli/output.py` 100, `cli/app.py` 98, `domain/results.py` 97, `services/transactions.py` 91, `services/categories.py` 89, `domain/queries.py` 82, `context.py` 80, `services/budgets.py` 66, `decorators.py` 66, `errors.py` 51, `storage/backup.py` 47, … 가장 작은 `__main__.py` 8).

가장 큰 `storage/jsonl.py` 329줄 중에서도 설명 주석·docstring 이 상당 부분을 차지합니다. 실제 로직은 어느 파일도 한 화면을 크게 벗어나지 않습니다.

> **분할을 어떻게 끝냈나.** 이 표는 **분할이 끝난 뒤**의 값입니다. 재배치 단계에서는 파일을 폴더로 **이동만** 했고(`git mv` 는 이력이 이어지지만 분할은 "전부 삭제 + 전부 추가"로 보여서, 두 가지를 한 커밋에 섞으면 리뷰가 불가능해집니다), 분할은 그다음 커밋에서 했습니다. 쪼갠 축은 넷입니다.
>
> | 분할 전 | 분할 후 | 나눈 축 |
> |---|---|---|
> | `storage/repository.py` (528줄) | `jsonl.py`(JSONL 공통 처리) / `ids.py`(ID 발급) / `repositories.py`(엔티티별 저장소) / `backup.py`(폴더 복사) | 기술적 관심사 |
> | `services.py` (342줄) | `transactions.py` / `budgets.py` / `categories.py` / `importexport.py` (+ `maintenance.py`) | 유스케이스 = 클래스 = 파일 |
> | `domain/models.py` (305줄) | `entities.py`(Transaction·Budget·Category·Patch) / `queries.py`(SearchFilter) / `results.py`(MonthlySummary·ImportReport) / `periods.py`(month_range) | 값의 역할 — 저장되는 것 / 묻는 것 / 답인 것 |
> | 루트 `config.py`·`messages.py` | 계층마다 하나씩(`domain/config.py`, `storage/messages.py`, `cli/config.py`, …) + 루트에는 앱 이름만 | 누가 쓰는가(§2.7) |
>
> 분할 뒤 새로 생긴 `storage/unit_of_work.py`·`domain/specs.py`·`domain/tx_id.py` 는 이동이 아니라 신설입니다.

### 1.2 의존 방향을 import 문으로 실증하기

다이어그램은 그림일 뿐이므로, 각 파일의 실제 import 문으로 화살표 방향을 확인합니다. 아래는 소스의 상대 import(`from . ...` / `from .. ...`)만 추출한 결과입니다. 표준 라이브러리 import(`json`, `argparse` 등)는 계층 구조와 무관하므로 뺐습니다.

```
  L0 (잎)  config                -> (없음)
  L0 (잎)  errors                -> (없음)
  L0 (잎)  domain.config         -> (없음)
  L0 (잎)  domain.messages       -> (없음)
  L0 (잎)  storage.messages      -> (없음)
  L0 (잎)  services.config       -> (없음)
  L0 (잎)  services.messages     -> (없음)
  L0 (잎)  cli.messages          -> (없음)

  L1 domain.tx_id               -> domain.config, domain.messages, errors
  L1 domain.validators          -> domain.config, domain.messages, errors
  L1 domain.entities            -> domain.tx_id, domain.validators
  L1 domain.periods             -> domain.config, domain.validators
  L1 domain.specs               -> domain.entities, domain.validators
  L1 domain.queries             -> domain.entities, domain.periods, domain.specs
  L1 domain.results             -> domain.entities

  L2 storage.config             -> config
  L2 storage.messages           -> (없음)
  L2 storage.backup             -> storage.config
  L2 storage.jsonl              -> errors, storage.config, storage.messages
  L2 storage.ids                -> domain.tx_id, storage.config, storage.jsonl,
                                   storage.messages
  L2 storage.unit_of_work       -> storage.config, storage.jsonl, storage.messages
  L2 storage.csv_io             -> domain.config, domain.entities, domain.tx_id,
                                   domain.validators, errors, storage.config,
                                   storage.messages
  L2 storage.repositories       -> domain.entities, domain.tx_id, domain.validators,
                                   storage.config, storage.ids, storage.jsonl

  L3 services.maintenance       -> storage.backup
  L3 services.categories        -> domain.validators, errors, services.messages,
                                   storage.repositories
  L3 services.transactions      -> decorators, domain.entities, domain.queries, errors,
                                   services.messages, storage.repositories
  L3 services.budgets           -> decorators, domain.config, domain.entities,
                                   domain.queries, domain.results, domain.validators,
                                   services.config, storage.repositories
  L3 services.importexport      -> domain.entities, domain.queries, domain.results,
                                   domain.tx_id, errors, services.config,
                                   services.messages, storage.csv_io, storage.ids,
                                   storage.repositories, storage.unit_of_work

  L4 cli.config                 -> config
  L4 cli.output                 -> cli.config, cli.messages
  L4 cli.presenter              -> cli.messages, domain.entities, domain.results
  L4 cli.parser                 -> cli.config, cli.messages, domain.config,
                                   services.config
  L4 cli.error_handler          -> cli.config, cli.messages, cli.output, errors
  L4 cli.prompts                -> cli.config, cli.messages, cli.output,
                                   domain.validators, errors, services.categories,
                                   services.messages
  L4 cli.handlers               -> cli.config, cli.messages, cli.output, cli.presenter,
                                   cli.prompts, context, domain.entities,
                                   domain.queries, domain.validators, errors
  L4 cli.app                    -> cli.config, cli.error_handler, cli.handlers,
                                   cli.output, cli.parser, context

  (횡단) decorators             -> config
  (횡단) context                -> services.budgets, services.categories,
                                   services.importexport, services.maintenance,
                                   services.transactions, storage.repositories
  (진입) __main__               -> cli

  [위로 향하는 의존] : 없음
```

다섯 가지를 확인할 수 있습니다.

1. **레벨 번호가 절대 거꾸로 가지 않습니다.** L3(`services.*`)가 L4(`cli.*`)를 import 하는 일은 없고, L1(`domain.*`)은 `errors` 외에는 자기 계층만 봅니다.
2. **각 계층의 `config`/`messages` 는 잎(leaf)입니다.** `storage.config`·`cli.config` 만 루트 `config` 에서 앱 이름을 물려받고, 나머지 상수 모듈은 아무것도 import 하지 않습니다. 어휘와 상수는 누구에게도 의존하지 않습니다.
3. **`cli.app` 과 `context` 가 조립을 맡습니다.** `cli.app` 은 CLI 부품 전체와 `context` 를, `context` 는 서비스 5개와 저장소 3개를 압니다 — "조립하는 쪽이 부품을 안다".
4. **`cli.*` 중 `storage.*` 를 import 하는 것이 하나도 없습니다.** 리팩터 전에는 `cli.prompts` 가 `CategoryStore` 를, 핸들러가 `storage.backup` 을 직접 import 했습니다. 지금은 CLI 가 서비스와만 말합니다. 이것을 감시하는 테스트가 `tests/test_architecture.py::test_cli_never_touches_storage` 입니다.
5. **`cli.output` 을 import 하는 곳은 전부 `cli.*` 입니다.** 그래서 `output` 이 `cli/` 안에 있는 것이 실측으로 정당화됩니다. 리팩터 전에는 `decorators` 도 이것을 import 했는데, `handle_errors` 를 떼어내면서 그 의존이 사라졌습니다(지금 `decorators` 가 아는 것은 루트 `config` 하나뿐).

이것을 직접 확인하고 싶다면 프로젝트 루트에서 다음을 실행하면 됩니다.

```bash
python -c "
import ast, pathlib
for p in sorted(pathlib.Path('budget_app').rglob('*.py')):
    if p.name == '__init__.py': continue
    pkg = list(p.parent.relative_to('budget_app').parts)
    me = '.'.join(list(p.relative_to('budget_app').with_suffix('').parts))
    deps = set()
    for n in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
        if isinstance(n, ast.ImportFrom) and n.level:
            up = pkg[:len(pkg) - (n.level - 1)]          # '..' 는 한 단계 위 패키지
            mods = [n.module] if n.module else [a.name for a in n.names]
            deps |= {'.'.join(up + [m]) if up else m for m in mods}
    print(f'{me:<22} -> {sorted(deps)}')
"
```

`n.level` 이 1이면 같은 패키지(`from . import x`), 2면 한 단계 위(`from .. import x`)입니다. 패키지가 생기면서 이 계산이 필요해졌습니다.

> **🔎 문법의 출처** — `from . import x` 같은 **명시적 상대 import** 는 PEP 328 이 도입했습니다. 같은 PEP 가 "점 없는 import 는 무조건 절대 경로"라는 규칙도 함께 정해서, 파이썬 3 에서는 `budget_app/domain/config.py` 가 있어도 `import calendar` 가 표준 라이브러리를 가져옵니다. `domain/periods.py` 의 모듈 docstring 이 "모듈 이름이 `calendar` 가 아닌 이유"를 설명하는 배경이 이것입니다 — 동작은 안전하지만 **읽는 사람이 헷갈리는 비용**은 남습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — 상대 import 의 점(`.`)은 **파일 위치가 아니라 `__package__` 를 기준**으로 풀립니다. import 시스템은 `__package__` 에서 `level - 1` 만큼 조각을 떼어내 절대 이름을 만듭니다. `budget_app/cli/app.py` 는 `__package__ == "budget_app.cli"` 이므로 `from ..context import AppContext` 는 `budget_app.context` 가 됩니다. 그래서 `python budget_app/cli/app.py` 로 **직접 실행하면 반드시 깨집니다** — 그때 `__name__` 은 `"__main__"`, `__package__` 는 빈 문자열이라 위로 올라갈 패키지가 없고, `ImportError: attempted relative import with no known parent package` 가 납니다. 이 프로젝트를 `python -m budget_app` 으로만 실행하는 것은 취향이 아니라 **문법적 요구**입니다. → [12 §1-A](./12-syntax-and-stdlib.md)

### 1.2.1 순환 import 가 없는 것이 우연이 아닌 이유

위 목록에서 두 모듈이 서로를 가리키는 쌍은 하나도 없습니다. 이것은 파이썬에서 **선택이 아니라 필수에 가깝습니다.**

`cli/app.py` 의 모듈 docstring 이 그 이유를 직접 말합니다.

budget_app/cli/app.py:3-7

```python
## 명령 → 핸들러 대응

``parser`` 가 남긴 문자열 키(``"category.add"``)를 ``HANDLERS`` 가 함수로 바꾼다.
파서가 함수 객체를 들고 있던 이전 방식과 달리 두 모듈이 서로를 import 하지 않으므로
순환이 없고, 하위 명령마다 핸들러가 하나씩 대응해 ``if/elif`` 분기가 사라졌다.
```

리팩터 전에는 `parser.py` 가 `p.set_defaults(func=cmd_add)` 로 **핸들러 함수 객체**를 들고 있었습니다. 그러려면 `parser` 가 `handlers` 를 import 해야 하는데, `handlers` 는 프롬프트·프레젠터를 쓰고 `app` 은 둘 다 쓰므로 모듈 그래프가 금방 얽힙니다. 지금은 파서가 `handler="add"` 라는 **문자열**만 남기고, 문자열 → 함수 변환은 `app.HANDLERS` 딕셔너리 한 곳이 담당합니다. 의존 화살표가 `app → parser`, `app → handlers` 두 개로 갈라지고 `parser ↔ handlers` 사이에는 아무것도 없습니다.

> **⚙️ 내부 동작** — 순환이 생기면 파이썬은 어떻게 실패하는가. import 는 모듈 객체를 만들어 `sys.modules` 에 **먼저 등록한 다음** 본문을 위에서 아래로 실행합니다. A 를 실행하던 중 B 를 import 하고 B 가 다시 A 를 import 하면, `sys.modules["A"]` 는 이미 있으므로 재실행 없이 그 객체가 반환되는데 — 그 객체는 **아직 본문을 끝내지 않은 반쯤 채워진 모듈**입니다. 그래서 `from .a import A` 는 아직 대입되지 않은 이름을 찾다 실패하고, 다음 오류가 납니다.
>
> ```
> ImportError: cannot import name 'A' from partially initialized module 'pkg.a'
> (most likely due to a circular import)
> ```
>
> 무서운 점은 **실행 순서에 따라 나기도 하고 안 나기도 한다**는 것입니다. `import a.b` 형태(모듈 객체만 받고 속성 접근은 나중)면 통과하고, `from a import X` 형태면 터집니다. 그래서 "돌아가니까 괜찮다"가 성립하지 않고, 애초에 순환을 만들지 않는 설계가 필요합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

### 1.2.2 계층 규칙을 문서가 아니라 **테스트가** 강제합니다

문서에 적힌 규칙은 검증되지 않습니다. 그래서 `tests/test_architecture.py` (115줄)가 규칙을 실행 가능한 형태로 갖고 있습니다.

tests/test_architecture.py:25-29

```python
#: 숫자가 작을수록 아래 계층. 같은 계층끼리는 허용한다.
LAYERS: dict[str, int] = {"domain": 0, "storage": 1, "services": 2, "cli": 3}

#: 계층에 속하지 않는 루트 모듈 — 아무나 써도 되는 공용 어휘
ROOT_MODULES = {"errors", "config", "decorators", "context", "__main__"}
```

이 파일이 검사하는 것은 다섯 가지입니다.

| 테스트 | 검사 내용 |
|---|---|
| `test_no_upward_imports` | 모든 모듈에 대해 `LAYERS[import한 계층] <= LAYERS[자기 계층]`. `@pytest.mark.parametrize` 로 파일마다 케이스가 하나씩 생겨, 깨지면 **어느 파일인지** 이름으로 나옵니다 |
| `test_cli_never_touches_storage` | `cli/*.py` 중 `storage` 계층을 import 하는 파일 목록이 빈 리스트여야 함 |
| `test_domain_imports_nothing_above_itself` | `domain/*.py` 가 import 하는 계층이 `{"domain", "<root>"}` 부분집합이어야 함 |
| `test_app_context_does_not_expose_repositories` | `AppContext` 인스턴스의 **공개 속성**에 `txs`/`cats`/`budgets` 가 없어야 함(§6) |
| `test_every_handler_is_registered` | `handlers` 의 `cmd_*` 함수 집합 == `app.HANDLERS` 값들의 `__name__` 집합 |

핵심은 판정을 **문자열 검색이 아니라 AST 로** 한다는 점입니다. 테스트 docstring 이 그 이유를 적어 뒀습니다.

tests/test_architecture.py:12-13

```python
import 를 AST 로 세는 이유: 문자열 검색은 주석·docstring 에 적힌 모듈 이름까지
세어서 거짓 양성이 나온다.
```

실제로 이 프로젝트의 docstring 에는 `storage.repositories` 같은 이름이 설명용으로 여러 번 등장합니다. `grep` 이었다면 전부 위반으로 잡혔을 것입니다.

> **⚙️ 내부 동작** — `ast.parse(source)` 는 사실 `compile(source, filename, mode, flags=ast.PyCF_ONLY_AST)` 의 얇은 래퍼입니다. CPython 이 실제 컴파일에 쓰는 것과 **같은 파서**를 돌리되 바이트코드 생성 직전에 멈춰서 구문 트리를 돌려주므로, "파이썬이 이 코드를 어떻게 읽는가"와 결과가 어긋날 수 없습니다. 모듈을 import 하지 않고 읽기만 하므로 부작용도 없습니다.
>
> `ast.walk(tree)` 는 `collections.deque` 를 쓴 **너비 우선 순회**입니다 — 노드를 꺼내 `iter_child_nodes()` 의 결과를 뒤에 붙이고 자신을 yield 하는 것이 전부라, 트리 전체를 순서 상관없이 훑을 때 쓰는 관용구입니다. 특정 노드만 필요하면 `isinstance(node, ast.ImportFrom)` 로 거릅니다.
>
> `ast.ImportFrom` 노드가 들고 있는 것은 셋입니다 — `module`(점 뒤 모듈 이름, `from . import x` 면 `None`), `level`(점 개수), `names`(가져오는 이름들). `from ..storage.repositories import X` 는 `module="storage.repositories", level=2` 로 파싱되므로 **`module` 의 첫 조각이 곧 계층 이름**이 됩니다. 테스트가 `(node.module or "").split(".")[0]` 한 줄로 계층을 뽑아내는 근거가 이것입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

### 1.3 리팩터가 고친 역류 — services → decorators → output

이 구조가 처음부터 이랬던 것은 아닙니다. 리팩터 전에는 **아래 계층이 위 계층에 전이 의존**하는 경로가 있었습니다.

```
[리팩터 전]
services.py ──import AppError──▶ decorators.py ──import──▶ output.py
   (서비스)                         (횡단?)                 (프레젠테이션)
   └──────────── 서비스가 화면 출력 모듈에 전이 의존 ──────────────┘
```

원인이 둘이었습니다.

**(1) `AppError` 가 `decorators.py` 에 있었습니다.** `AppError` 는 "등록되지 않은 카테고리입니다" 같은 **도메인 오류**인데, 이름이 `decorators` 인 파일에 살고 있었습니다. 서비스는 이 예외 하나를 쓰려고 `decorators` 를 import 해야 했습니다.

**(2) `handle_errors` 도 `decorators.py` 에 있었습니다.** 예외를 화면 문구와 종료 코드로 바꾸는 것은 **CLI 표현 정책**입니다. 그것이 있으니 `decorators` 가 `output` 을 import 해야 했고, 그 의존이 서비스까지 전파됐습니다.

리팩터는 둘을 각각 제자리로 옮겼습니다.

```
[리팩터 후]
errors.py         ← AppError / ValidationError  (계층 공통 어휘, 아무것도 import 안 함)
decorators.py     ← @log_call / @measure_time   (관측만, 루트 config 만 앎)
cli/error_handler.py ← @handle_errors           (CLI 표현 정책, cli.output 을 앎)

services/ ──▶ errors, decorators   (둘 다 output 을 모름) ✅
```

§1.2 의 실측 목록이 이 결말을 확인해 줍니다 — `decorators -> config` 한 줄뿐이고, `services.transactions`/`services.budgets` 가 `decorators` 를 import 해도 거기서 `cli.output` 으로 이어지는 길이 없습니다.

**과제 방어 포인트**: "계층을 왜 나눴나"라는 질문에 "나눠 봤더니 이런 역류가 있었고 이렇게 고쳤다"까지 답할 수 있으면, 계층 구조를 그림으로만 아는 것과 실제로 이해한 것의 차이가 드러납니다.

---

## 2. 각 계층의 책임과 금지사항

계층 구조가 의미를 가지려면 "무엇을 하는가"만큼 **"무엇을 하면 안 되는가"** 가 지켜져야 합니다. 아래 표의 금지사항은 전부 grep 으로 검증 가능한 형태로 적었습니다.

| 모듈 | 책임 | 금지사항 (검증 방법) |
| --- | --- | --- |
| `__main__.py` | 프로세스 시작과 종료 코드 전달 | 로직 금지 — 8줄뿐 |
| `cli/app.py` | `HANDLERS` 레지스트리 + `main` + `_dispatch`(컨텍스트 조립·호출) | `print(` 0회, 문자열 조립 금지 |
| `cli/handlers.py` | 인자 → 서비스 호출 번역, 결과 → 프레젠터 전달 | 검증 규칙 금지, `storage.*` import 금지 |
| `cli/parser.py` | argparse 문법 정의 | 핸들러 함수 참조 금지 (문자열 키만) |
| `cli/prompts.py` | 표준입력에서 값 받기 | 저장소 직접 접근 금지 (`CategoryService` 만 받음) |
| `cli/presenter.py` | 도메인 → 문자열 | `print(` 0회 — **반환만** |
| `cli/output.py` | 채널 결정(stdout/stderr/log) | 문자열 조립 금지 |
| `cli/error_handler.py` | 예외 → 메시지 + 종료 코드 | 도메인 규칙 금지 |
| `services/*.py` | 도메인 규칙과 정책 | `open(` 0회, `print(` 0회 |
| `storage/jsonl.py` | JSONL 열기·스트리밍·원자적 재작성 | 엔티티 종류 인식 금지 (제네릭 `T`) |
| `storage/repositories.py` | 엔티티별 저장소 (거래·카테고리·예산) | `print(` 0회, 도메인 판단 금지 |
| `storage/ids.py` | ID 발급·워터마크 | 거래 내용 해석 금지 |
| `storage/unit_of_work.py` | 여러 파일 한 단위 커밋 | 정책 판단 금지 |
| `storage/csv_io.py` | CSV ↔ 도메인 번역 | 정책 판단 금지 (중복/원자 정책 모름) |
| `domain/entities.py` | 데이터 구조 + 불변식 | I/O 전면 금지 |
| `domain/validators.py` | 필드 규칙 | 저장소 접근 금지 |
| `domain/specs.py` | 조합 가능한 조건 객체 | 파일·화면 금지 |
| `errors.py` | 예외 타입 정의 | import 0개 |
| `decorators.py` | 관측(로그/시간) | `cli.output` import 금지 |
| `context.py` | 합성 루트 — 저장소·서비스 조립 | `cli.*` import 금지 |
| `<계층>/config.py` | 값 상수 | 함수/클래스 금지, 문구 금지 |
| `<계층>/messages.py` | 문자열 | 값 정책 금지 |

각 항목을 풀어서 확인합니다.

### 2.1 `print` 는 `output.py` 에만 있습니다

리팩터 전에는 `cli.py` 에 `print(` 가 26회 있었습니다. 지금은 0회입니다. 프로그램이 밖으로 글자를 내보내는 지점은 `output.py` 의 네 함수뿐입니다.

budget_app/cli/output.py:42-44

```python
def out(message: str = "") -> None:
    """프로그램의 결과 한 줄을 stdout 으로 출력한다."""
    print(message)
```

네 함수는 `out` / `out_lines` / `err` / `err_lines` 입니다(`cli/output.py:42-71`).

**리팩터 전에는 이 규칙이 선언만 있고 지켜지지 않았습니다.** `output.py` 의 첫 줄은 원래도 "어떤 메시지가 어느 스트림으로 나가는지 이 모듈에서만 정한다"였는데, 정작 `err()` 만 있고 stdout 출력은 전부 `cli.py` 에 흩어져 있었습니다. `out()` 을 추가해 선언과 코드를 일치시킨 것이 리팩터의 작은 성과 중 하나입니다.

### 2.2 `presenter.py` 는 출력하지 않고 **반환**합니다

budget_app/cli/presenter.py:1-2 (docstring 발췌)

```python
"""프레젠터 — 도메인 객체를 사람이 읽을 줄로 바꾼다.

```

그 결과 핸들러가 이렇게 짧아집니다.

budget_app/cli/handlers.py:72-75

```python
def cmd_summary(ctx: AppContext, args: argparse.Namespace) -> int:
    summary = ctx.budget_service.monthly_summary(args.month, top_n=args.top)
    output.out_lines(presenter.summary_lines(summary))
    return config.EXIT_OK
```

세 줄에 세 계층이 각각 한 번씩 등장합니다 — 서비스가 계산하고, 프레젠터가 문자열로 바꾸고, 출력 모듈이 채널을 고릅니다. 리팩터 전 `cmd_summary` 는 25줄짜리 렌더링 함수였습니다.

> **🔎 문법의 출처** — `summary_lines` 는 `return` 대신 `yield` 를 쓰는 **제너레이터 함수**입니다(§4 에 본문이 있습니다). 함수 본문 어딘가에 `yield` 가 있으면 컴파일러가 코드 객체에 제너레이터 플래그를 세워서, 호출해도 본문이 실행되지 않고 제너레이터 객체만 돌아옵니다. 그래서 프레젠터는 "출력을 만들지 않고 **만드는 방법**을 넘긴다"가 되고, `output.out_lines` 가 `for` 로 돌릴 때 비로소 한 줄씩 계산됩니다. 조기 반환(`if summary.is_empty: ... return`)이 자연스럽게 쓰이는 것도 제너레이터라서입니다 — 여기서 `return` 은 값이 아니라 **종료**를 뜻합니다. → [12 §1-C](./12-syntax-and-stdlib.md)

### 2.3 `services/` 에는 `open(` 이 없습니다

리팩터 전에는 `services.py` 안에서 CSV 파일을 직접 열었습니다. `repository.py` 는 "파일 입출력만 담당"한다고 선언해 놓고 실제로는 **JSONL I/O 는 저장소, CSV I/O 는 서비스**라는 일관성 없는 규칙이었습니다.

지금은 파일을 여는 코드가 전부 저장소 계층(`storage/jsonl.py` / `storage/csv_io.py` / `storage/backup.py`)에 있고, `services/` 패키지 전체에서 `open(` 는 docstring 안의 설명 한 줄뿐입니다.

budget_app/services/__init__.py:1-15
```python
"""서비스 계층 — 유스케이스와 정책.

저장소(파일 I/O)와 CLI(화면) 사이에서 **판단**만 담당한다. 이 패키지에는
``open()`` 이 하나도 없다. 파일을 여는 일은 ``storage`` 가, 글자를 내는 일은
``cli.presenter`` 가 한다.

- ``transactions`` : 거래 추가·수정·삭제·정렬 조회
- ``budgets``      : 예산 설정 + 월별 요약(단일 패스 집계)
- ``categories``   : 카테고리 관리 + 참조 무결성 보호
- ``importexport`` : CSV 가져오기/내보내기 정책 (실패 축 × 중복 축)

**재수출하지 않는다** — ``from ..services.budgets import BudgetService`` 처럼 소유
모듈을 명시한다. 서비스가 넷뿐이라 어느 파일에 있는지 외우기 어렵지 않고,
import 문이 곧 "이 모듈이 어느 유스케이스를 쓰는가"의 목록이 된다.
"""
```

### 2.4 `storage/repositories.py` 는 도메인 판단을 하지 않습니다

부모 클래스 `JsonlStore.append` 는 "받은 엔티티를 한 줄로 인코딩해 파일 끝에 붙인다"가 전부입니다.

budget_app/storage/jsonl.py:210-211

```python
    def append(self, entity: T) -> None:
        self._append_lines([self._encode(entity)])
```

`TransactionRepository` 가 이것을 재정의하지만, 더하는 일도 도메인 판단이 아니라 **ID 워터마크 갱신**뿐입니다.

budget_app/storage/repositories.py:128-136

```python
    def append(self, tx: Transaction) -> None:
        """한 건을 이어 쓰고 워터마크를 갱신한다.

        워터마크를 **쓰기 전에** 올린다. 그래야 "발급된 번호는 어느 순간에도
        기준선 아래로 내려가지 않는다"가 항상 성립한다. 쓰기가 실패하면 번호가
        하나 건너뛰지만, 빈 번호는 아무 문제도 일으키지 않는다.
        """
        self._watermark.remember(tx.id.number)
        super().append(tx)
```

"이 거래의 카테고리가 등록된 것인가?" 같은 판단은 여기에 없습니다. 저장소는 넘어온 객체를 의심하지 않는데, 그럴 수 있는 이유는 `Transaction` 이 생성 시점에 이미 검증을 마친 객체이기 때문입니다.

**리팩터가 되돌린 위반이 하나 있습니다.** 이전 `repository.update` 는 이런 코드였습니다.

```python
# (리팩터 전 — 지금은 없는 코드)
    def update(self, tx_id: str, changes: Dict[str, object]) -> Optional[Transaction]:
        ...
        data = tx.to_dict()
        data.update(changes)
        # from_dict 가 검증을 다시 수행
        new_tx = Transaction.from_dict(data)
```

저장소가 **"무엇으로 바꿀지 해석하고 도메인 규칙을 다시 적용"** 하고 있었습니다. 지금은 그 일이 도메인(`Transaction.with_patch`)과 서비스로 올라가고, 저장소는 완성된 객체를 받아 교체만 합니다.

budget_app/storage/repositories.py:184-189

```python
        def _swap(tx: Transaction) -> Transaction:
            nonlocal found
            if tx.id == target:
                found = True
                return new_tx
            return tx
```

### 2.5 `csv_io.py` 는 정책을 모릅니다

CSV 어댑터는 "행을 읽고 검증한다"까지만 하고, **중복 id 를 어떻게 처리할지는 모릅니다.** 그래서 `parse_row` 는 완성된 `Transaction` 이 아니라 `ParsedRow` 를 돌려줍니다.

budget_app/storage/csv_io.py:39-64

```python
@dataclass(frozen=True)
class ParsedRow:
    """검증을 마친 CSV 한 행 — 아직 ``Transaction`` 은 아니다.

    id 가 아직 정해지지 않았을 수 있어서(빈 컬럼 → 발급 대상) 완성된 엔티티로
    만들 수 없다. 그 마지막 한 조각을 채우는 것은 중복 정책을 아는 서비스의 몫이다.
    """

    tx_id: TransactionId | None
    type: str
    date: str
    amount: int
    category: str
    memo: str
    tags: list[str]

    def to_transaction(self, tx_id: TransactionId) -> Transaction:
        return Transaction(
            id=tx_id,
            type=self.type,
            date=self.date,
            amount=self.amount,
            category=self.category,
            memo=self.memo,
            tags=self.tags,
        )
```

**"거의 다 됐지만 한 조각이 비어 있는 값"을 타입으로 표현**한 것이 이 설계의 핵심입니다. 어댑터와 정책의 경계가 타입 하나로 그어집니다.

> **🔎 문법의 출처** — `tx_id: TransactionId | None` 의 `|` 유니온 표기는 PEP 604 로 파이썬 3.10 에 들어왔습니다. 그 전에는 `typing.Optional[TransactionId]` 또는 `typing.Union[...]` 을 썼습니다. 이 프로젝트의 `requires-python = ">=3.10"` 은 이 표기를 쓰기 위한 조건 중 하나입니다. 다만 타입 어노테이션을 쓰는 파일 28개(43개 중)는 모두 `from __future__ import annotations` 를 켜 두어서 어노테이션이 문자열로만 보관되므로, 실행 시점에는 3.10 미만에서도 평가되지 않습니다 — 그래도 `list[str]`·`dict[str, int]` 같은 내장 제네릭(PEP 585, 3.9)과 함께 쓰이므로 하한선은 유지됩니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **🔎 문법의 출처** — `@dataclass(frozen=True)` 는 PEP 557 로 파이썬 3.7 에 들어온 `dataclasses` 입니다. 데코레이터가 클래스 어노테이션을 읽어 `__init__`·`__repr__`·`__eq__` **소스 코드를 문자열로 조립한 뒤 `exec` 로 컴파일**해 클래스에 붙입니다. `frozen=True` 면 추가로 `__setattr__`/`__delattr__` 을 심어 대입을 `FrozenInstanceError` 로 막고, `__hash__` 도 생성해 줍니다. `ParsedRow` 를 얼려 두면 "검증을 마친 값"이 어댑터를 떠난 뒤 몰래 바뀌는 일이 없습니다. → [12 §1-B](./12-syntax-and-stdlib.md)

### 2.6 `domain/` 패키지는 I/O 를 전혀 모릅니다

`domain/` 의 9개 파일 어디에도 `open`, `print`, `input` 이 없고, dataclass 정의와 계산만 있습니다(§1.2 의 목록에서 `domain.*` 가 import 하는 것은 자기 계층과 루트 `errors` 뿐입니다). 그래서 도메인은 파일 없이 단독으로 테스트할 수 있고, `tests/test_architecture.py::test_domain_imports_nothing_above_itself` 가 이 규칙을 매 실행마다 확인합니다.

### 2.7 `config.py` 와 `messages.py` — 나눈 기준

둘 다 "상수 파일"이지만 **바꿨을 때 일어나는 일이 다릅니다.** 지금은 이 두 이름이 계층마다 하나씩, 총 9개 존재합니다(`domain/`·`storage/`·`services/`·`cli/` 각각 `config.py`·`messages.py` + 루트 `config.py`).

두 축이 있습니다. **무엇을 정하는가**(정책 vs 문구)와 **누가 쓰는가**(계층)입니다.

- **`<계층>/config.py`** — *정책*. 유효한 타입 목록, 날짜 형식, 파일명, 한도, 종료 코드처럼 **동작이 달라지는 값**. 바꾸면 프로그램이 다르게 동작합니다.
- **`<계층>/messages.py`** — *문구*. 프롬프트·오류·힌트·출력 템플릿. 바꿔도 동작은 같고 화면 글자만 바뀝니다.

이전에는 한 파일에 둘 다 있어서 도메인 모델이 CLI 한국어 문구까지 들어 있는 모듈에 의존했습니다. 그리고 **계층별로 다시 나눴습니다** — 실측 결과 옛 `config.py` 상수 46개 중 39개, `messages.py` 105개 중 104개가 **단일 계층에서만** 쓰이고 있었기 때문입니다.

budget_app/config.py:1-25 (루트에 남은 것은 앱 이름 하나뿐)

```python
"""애플리케이션 정체성 — 어느 계층에도 속하지 않는 앱 전역 이름.

## 진입 기준

여기 남는 것은 **"이 프로그램이 무엇으로 불리는가"** 뿐이다. 계층 하나만 쓰는 값은
그 계층의 ``config.py`` 로 내려갔다.
...
"""

#: 앱 이름 하나만 소유한다. 계층별 자식 로거는 각 계층 config 가 여기서 **파생**시킨다
...
LOGGER_NAME = "budget_app"
```

계층을 넘나드는 값은 **아래 계층이 소유하고 위 계층이 가져다 씁니다**(`VALID_TYPES` 는 `domain.config` 가 갖고 argparse 의 `choices` 가 빌려 쓰는 식). §1.2 의 import 목록이 이 분업이 실제로 작동함을 보여 줍니다 — `cli.parser -> domain.config, services.config` 한 줄이 그 증거입니다.

로거 이름이 이 소유 규칙의 가장 깔끔한 예입니다. 루트가 `"budget_app"` 하나만 갖고, 저장소 계층이 거기서 **파생**시킵니다.

budget_app/storage/config.py:11

```python
LOGGER_NAME = f"{app_config.LOGGER_NAME}.storage"
```

> **⚙️ 내부 동작** — `logging` 의 로거 이름은 **점으로 계층을 만드는 문자열**입니다. `logging.getLogger("budget_app.storage")` 는 이름이 같으면 항상 같은 객체를 돌려주고(모듈 수준 딕셔너리 캐시), 레코드를 처리할 때는 자기 핸들러를 부른 뒤 `propagate` 를 따라 부모 `"budget_app"` → 루트 로거로 **거슬러 올라갑니다.** 그래서 `output.setup_logging()` 이 `logging.basicConfig` 로 루트에 핸들러 하나만 붙여 두면 모든 계층의 로그가 그리로 모이고, 나중에 "저장소 로그만 끄고 싶다"가 생기면 `budget_app.storage` 한 줄만 조정하면 됩니다. 즉 **모듈 트리와 로거 트리가 같은 모양**이 되도록 이름을 파생시킨 것입니다. 현재 자식 로거는 `budget_app.storage` 하나뿐이고, `cli`·`decorators` 는 루트 이름 `"budget_app"` 을 그대로 씁니다(`cli/config.py:10`). → [12 §2-B](./12-syntax-and-stdlib.md)

---

## 3. 실행 흐름 완전 추적 1 — 쓰기 경로 (`python -m budget_app add`)

거래 한 건이 저장되기까지의 전체 여정을 단계별로 따라갑니다. 이 경로 하나만 완전히 설명할 수 있으면 아키텍처의 절반을 설명한 셈입니다.

```
python -m budget_app add
  → __main__.py (진입)  sys.exit(main())
  → cli.app.main
      → parser.build_parser() → parse_args() → args.handler == "add"
      → output.setup_logging(args.debug)
      → _dispatch(args)                         ← @handle_errors 는 여기 하나뿐
          → AppContext(Path(args.data_dir)) 조립  (경로 계산만, 디스크 무접촉)
          → args.needs_storage 면 ctx.prepare()  (폴더·파일 준비)
          → HANDLERS["add"](ctx, args) == cmd_add
              → prompts.ask_transaction(ctx.cat_service)  대화형 입력 + 필드 검증
                  → prompts.ask_until(..., validators.parse_date)
              → TransactionService.add(...)      도메인 규칙: 카테고리 등록됐나?
                  → TransactionRepository.next_id()   ID 발급 (IdAllocator)
                  → Transaction(...) 생성 → __post_init__ (불변식 검증)
                  → TransactionRepository.append()    파일 쓰기
              → output.out(MSG_SAVED_TX.format(...))
  → data/transactions.jsonl 에 한 줄 추가
```

**1단계 — 진입.** `python -m budget_app` 은 패키지의 `__main__.py` 를 실행합니다. `sys.exit(main())` 이 `cli.main` 의 반환값(정수)을 프로세스 종료 코드로 만듭니다.

> **⚙️ 내부 동작** — `sys.exit(n)` 은 프로세스를 즉시 죽이는 것이 아니라 `SystemExit(n)` **예외를 던지는** 것입니다. 그래서 `try`/`finally` 와 컨텍스트 매니저의 정리 코드가 정상적으로 돌고, 인터프리터 최상단이 그 예외를 받아 종료 코드로 씁니다. 인자가 정수면 그대로 종료 코드, 문자열이면 stderr 에 찍고 코드 1, `None`/생략이면 0 입니다. `main()` 이 `int` 를 돌려주도록 설계한 이유가 여기 있습니다 — 모든 핸들러가 `config.EXIT_*` 상수를 `return` 하면 그 값이 그대로 셸의 `$?` 가 됩니다. 예외로 종료 코드를 정하지 않으므로 `handle_errors` 가 예외를 잡아 `return EXIT_IO` 하는 방식이 성립합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

**2단계 — 파싱·준비·디스패치.**

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

`args.handler` 가 어떻게 `"add"` 가 되는지는 파서 등록에 있습니다.

budget_app/cli/parser.py:108-111

```python
def _add_add(sub) -> None:
    p = sub.add_parser("add", help="거래 추가 (대화형)")
    _add_shared_options(p)
    p.set_defaults(handler="add")
```

> **⚙️ 내부 동작** — `set_defaults(handler="add")` 는 인자를 정의하는 것이 아니라, 이 파서가 선택됐을 때 결과 `Namespace` 에 **그냥 꽂아 넣을 값**을 등록하는 것입니다. argparse 는 하위 명령을 만나면 그 하위 파서로 파싱을 위임하고, 하위 파서의 `_defaults` 를 상위 `Namespace` 에 합칩니다. 그래서 `args.handler` 는 사용자가 입력한 적 없는데도 값이 들어 있고, `--data-dir` 처럼 실제 옵션이 아니라서 `--help` 에도 나오지 않습니다. `needs_storage` 도 같은 통로로 들어옵니다 — 최상위에서 `set_defaults(needs_storage=True)`, `backup` 하위 파서만 `False` 로 덮습니다(`cli/parser.py:91`, `cli/parser.py:243`). → [12 §2-B](./12-syntax-and-stdlib.md)

**3단계 — 컨텍스트 조립과 핸들러 실행.** `@handle_errors` 는 개별 핸들러가 아니라 **`_dispatch` 한 곳에만** 붙습니다.

budget_app/cli/app.py:61-81

```python
@handle_errors
def _dispatch(args: argparse.Namespace) -> int:
    """컨텍스트를 조립하고 핸들러를 부른다 — **오류 방패 안에서**.

    이 함수가 따로 있는 이유가 3-1 수정의 전부다. 이전에는 ``AppContext`` 생성과
    ``prepare()`` 가 ``main`` 안, 즉 ``@handle_errors`` **밖**에 있었다. 그래서
    ``--data-dir`` 에 파일 경로를 주면(오타 하나로 충분하다) ``mkdir`` 이
    ``FileExistsError`` 를 던지고, 그것을 아무도 잡지 않아 **원시 트레이스백**과
    종료 코드 1 로 끝났다. ...
    """
    ctx = AppContext(Path(args.data_dir))
    if args.needs_storage:
        ctx.prepare()
    return HANDLERS[args.handler](ctx, args)
```

`AppContext` 생성과 `prepare()` 까지 방패 안에 들어와 있다는 점이 중요합니다. **파일을 여는 코드가 방패 밖에 있으면 방패가 아닙니다.** 이 아래 모든 단계에서 발생하는 예외는 스택트레이스 대신 `[오류]`/`[힌트]` 메시지와 종료 코드로 변환됩니다(§7).

> **🔎 문법의 출처** — `@handle_errors` 라는 데코레이터 문법은 PEP 318 로 파이썬 2.4 에 들어왔고, 하는 일은 순수한 문법 설탕입니다. `@deco` 다음에 오는 `def f(...)` 는 파이썬이 `f = deco(f)` 로 바꿔 씁니다(정확히는 함수를 만든 직후 `deco` 를 적용하고 그 결과를 `f` 라는 이름에 대입합니다). 그래서 위 코드에서 `_dispatch` 라는 이름이 실제로 가리키는 것은 원본 함수가 아니라 `handle_errors` 가 돌려준 `wrapper` 입니다. "정책을 한 줄로 붙인다"가 가능한 이유가 이 재대입 하나입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

`HANDLERS["add"]` 가 가리키는 함수가 이것입니다.

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

**핸들러가 하는 일은 넷뿐입니다** — 전제 조건 확인, 입력 수집 위임, 서비스 호출, 결과 출력. 대화형 입력의 "어떻게"는 전혀 모릅니다.

**4단계 — 입력 수집.** `prompts` 가 순서와 검증기를 알고 있습니다.

budget_app/cli/prompts.py:112-121

```python
def ask_transaction(cat_service: CategoryService) -> TransactionInput:
    """거래 한 건에 필요한 값을 순서대로 받아 온다."""
    return TransactionInput(
        date=ask_until(messages.PROMPT_DATE, validators.parse_date),
        type=ask_until(messages.PROMPT_TYPE, validators.parse_type),
        category=ask_until(messages.PROMPT_CATEGORY, registered_category_validator(cat_service)),
        amount=ask_until(messages.PROMPT_AMOUNT, validators.parse_amount),
        memo=validators.parse_memo(ask(messages.PROMPT_MEMO)),
        tags=validators.parse_tags(ask(messages.PROMPT_TAGS)),
    )
```

여기서 **CLI 가 자체 검증 규칙을 갖지 않는다**는 점이 중요합니다. `validators.parse_date` 를 그대로 넘길 뿐입니다. 카테고리만 서비스에 물어봐야 하므로 클로저 팩토리로 감쌉니다 — `registered_category_validator(cat_service)` 는 `cat_service` 를 기억하는 **한 인자짜리 함수**를 만들어 돌려주므로, `ask_until` 이 요구하는 `Callable[[str], T]` 모양에 맞아떨어집니다(`cli/prompts.py:77-109`, 자세한 것은 [03 §4.5](./03-python-advanced.md)).

`ask_until` 은 재입력 루프의 뼈대이고, EOF 와 무한 반복이라는 두 함정을 막아 둡니다(`cli/prompts.py:60-74`) — EOF 면 `InputAborted` 를 던지고, 재입력은 `config.MAX_INPUT_RETRIES` 회로 끊습니다.

> **🔎 문법의 출처** — `ask_until` 이 검증 **함수 자체**를 인자로 받을 수 있는 것은 파이썬에서 함수가 일급 객체(first-class object)이기 때문입니다. `def` 는 선언이 아니라 **실행되는 문**이고, 함수 객체를 만들어 이름에 대입합니다. 그래서 `validators.parse_date` 는 호출하지 않으면 그냥 값이고, 딕셔너리에 담거나(`app.HANDLERS`) 인자로 넘기거나(`ask_until`) 감싸서 새 함수를 만들 수 있습니다(`registered_category_validator`). 별도의 "함수 포인터" 개념이 필요 없습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

**5단계 — 서비스의 도메인 규칙.**

budget_app/services/transactions.py:27-35

```python
    @log_call
    def add(
        self,
        date: str,
        type_: str,
        category: str,
        amount: int,
        memo: str = "",
        tags: list[str] | None = None,
```

서비스가 판단하는 것은 **"카테고리가 등록되어 있는가"** 하나입니다. 이것은 필드 규칙이 아니라 **저장된 상태를 봐야 아는 규칙**이라 `validators` 가 아니라 서비스에 있습니다. 이 구분이 `ValidationError`(값) vs `AppError`(상황)의 구분과 정확히 대응합니다.

budget_app/services/transactions.py:89-91

```python
    def _require_registered_category(self, name: str, *, hint: str) -> None:
        if not self.cats.exists(name):
            raise AppError(messages.ERR_CATEGORY_NOT_REGISTERED.format(name=name), hint=hint)
```

**6단계 — ID 발급.** 저장소가 파일 상태를 훑어 다음 번호를 정합니다.

budget_app/storage/repositories.py:53-63

```python
    def id_state(self) -> tuple[int, set[TransactionId]]:
        """(최대 번호, 사용 중인 id 집합) — 파일을 한 번만 훑는다."""
        max_n = 0
        taken: set[TransactionId] = set()
        for raw in self.iter_raw():
            found = self._scan_id(raw)
            if found is None:
                continue
            taken.add(found)
            max_n = max(max_n, found.number)
        return max_n, taken
```

**`iter_raw()` 를 쓴다는 점이 핵심입니다.** 검증에 실패하는 줄에도 id 는 들어 있고, 그 번호는 이미 쓰인 번호입니다. `stream()`(유효한 것만)으로 훑으면 그 번호가 보이지 않아 **재발급으로 중복 id 가 생깁니다**. 저장소는 읽기 경로를 둘로 나눠 두었습니다 — `iter_raw()` 는 해석 실패 줄까지 원문 그대로 주고, `stream()` 은 해석에 성공한 엔티티만 줍니다([07 §4](./07-repository.md)).

**7단계 — 생성자 불변식.** `Transaction(...)` 호출이 `__post_init__` 을 태우고, 여기서 모든 필드가 검증·정규화됩니다. 여기까지 예외 없이 왔다면 **객체는 반드시 유효**합니다.

> **⚙️ 내부 동작** — `__post_init__` 은 파이썬 언어의 특수 메서드가 아니라 **`dataclasses` 모듈의 약속**입니다. `@dataclass` 가 생성해 주는 `__init__` 의 마지막 줄에 "클래스에 `__post_init__` 이 있으면 부른다"는 호출이 삽입되는 것뿐입니다. 그런데 `Transaction` 은 `frozen=True` 라 `self.date = ...` 같은 정규화 대입이 막히므로, 정규화가 필요한 자리는 `object.__setattr__(self, "date", ...)` 로 얼음을 우회합니다(`domain/entities.py:68-80`). "검증은 생성자에서 단 한 번" 규칙이 성립하는 지점이 여기입니다. → [12 §1-B](./12-syntax-and-stdlib.md)

**8단계 — 파일 쓰기.** `append` 가 한 줄을 파일 끝에 붙입니다(§2.4). 새 거래 추가는 파일 전체를 다시 쓰지 않으므로 O(1) 입니다.

---

## 4. 실행 흐름 완전 추적 2 — 읽기 경로 (`summary --month 2024-01`)

```
python -m budget_app summary --month 2024-01
  → cmd_summary(ctx, args)
      → BudgetService.monthly_summary("2024-01", top_n=5)     @measure_time
          → validators.parse_month("2024-01")                  형식 검증
          → SearchFilter.for_month("2024-01")
              → periods.month_range() → ("2024-01-01", "2024-01-31")
              → specs 조립: DateFrom & DateTo
          → TransactionRepository.stream()                     제너레이터
              → iter_raw() → RawLine → 유효한 것만 통과
          → 단일 패스로 income/expense/카테고리별 합계 집계
          → BudgetStore.get("2024-01")
          → MonthlySummary(...) 반환
      → presenter.summary_lines(summary)                       문자열 생성
      → output.out_lines(...)                                  stdout
```

budget_app/services/budgets.py:30-66

```python
    @measure_time
    def monthly_summary(self, month: str, top_n: int = config.DEFAULT_TOP_N) -> MonthlySummary:
        """월별 요약을 계산해 ``MonthlySummary`` 로 돌려준다.

        "이 달에 속하는가"의 판정을 ``SearchFilter.for_month`` 에 위임한 것이 핵심이다.
        이전에는 요약은 ``date.startswith(month + "-")``, 내보내기는 CLI 가 계산한
        말일 범위를 써서 **같은 개념이 두 알고리즘으로** 구현돼 있었다.
        """
        target = validators.parse_month(month)
        flt = SearchFilter.for_month(target)

        income_total = 0
        expense_total = 0
        per_category: dict[str, int] = {}
        has_data = False

        for tx in self.txs.stream():
            if not flt.matches(tx):
                continue
            has_data = True
            if tx.type == domain_config.TYPE_INCOME:
                income_total += tx.amount
            else:
                expense_total += tx.amount
                per_category[tx.category] = per_category.get(tx.category, 0) + tx.amount

        top_expense = tuple(
            sorted(per_category.items(), key=lambda kv: kv[1], reverse=True)[: max(0, top_n)]
        )
        return MonthlySummary(
            month=target,
            income=income_total,
            expense=expense_total,
            top_expense=top_expense,
            has_data=has_data,
            budget=self.budgets.get(target),
        )
```

세 가지를 눈여겨보세요.

**(1) 단일 패스 집계.** 파일을 **한 번만** 순회하며 수입 합계·지출 합계·카테고리별 합계를 동시에 누적합니다. 세 값을 각각 구하려고 세 번 읽는 방식보다 파일 I/O 가 1/3 입니다.

**(2) 파생값을 계산하지 않습니다.** `balance`, `usage_pct`, `over_budget` 이 여기 없습니다. 전부 `MonthlySummary` 의 `@property` 입니다(`domain/results.py:38-50`). 서비스는 **원자료만** 담아 넘깁니다.

> **⚙️ 내부 동작** — `@property` 는 문법이 아니라 **내장 클래스**입니다. `property(fget)` 가 `__get__` 을 가진 객체(디스크립터)를 만들어 클래스 속성 자리에 앉으면, `summary.balance` 라는 **속성 접근**이 파이썬 내부에서 `type(summary).balance.__get__(summary)` 로 바뀌어 함수가 호출됩니다. 그래서 호출 괄호 없이도 계산이 일어나고, 프레젠터 쪽 코드는 "필드를 읽는 것"과 "계산을 요청하는 것"을 구분할 필요가 없어집니다. 파생값의 정의처가 데이터 옆에 붙어 있게 되는 것이 이 설계의 이득입니다. → [12 §1-B](./12-syntax-and-stdlib.md)

**(3) 리팩터 전에는 dict 를 돌려줬습니다.** `{"month": ..., "income": ..., "usage_pct": ...}` 형태의 9키 딕셔너리였고, CLI 가 `result["has_data"]` 처럼 꺼내 썼습니다. 키 오타는 런타임 `KeyError` 였고, "예산이 없으면 N/A" 같은 **도메인 상태 해석이 화면 코드에 섞여** 있었습니다.

프레젠터는 그 결과를 읽기만 합니다.

budget_app/cli/presenter.py:63-88

```python
def summary_lines(summary: MonthlySummary) -> Iterator[str]:
    if summary.is_empty:
        yield messages.MSG_SUMMARY_NO_DATA.format(month=summary.month)
        return

    yield messages.MSG_SUMMARY_INCOME.format(income=summary.income)
    yield messages.MSG_SUMMARY_EXPENSE.format(expense=summary.expense)
    yield messages.MSG_SUMMARY_BALANCE.format(balance=summary.balance)

    if summary.budget is not None:
        yield from _budget_lines(summary)

    if summary.top_expense:
        yield messages.MSG_TOP_EXPENSE_HEADER.format(n=len(summary.top_expense))
        for rank, (category, amount) in enumerate(summary.top_expense, start=1):
            yield messages.FMT_TOP_EXPENSE_ITEM.format(rank=rank, category=category, amount=amount)


def _budget_lines(summary: MonthlySummary) -> Iterator[str]:
    usage = summary.usage_pct
    usage_str = (
        messages.FMT_USAGE_PCT.format(usage=usage) if usage is not None else messages.MSG_USAGE_NA
    )
    yield messages.MSG_SUMMARY_BUDGET.format(amount=summary.budget.amount, usage=usage_str)
    if summary.over_budget:
        yield messages.MSG_OVER_BUDGET
```

`summary.is_empty`, `summary.balance`, `summary.over_budget` — 프레젠터는 **묻기만 하고 계산하지 않습니다.**

---

## 5. 실행 흐름 완전 추적 3 — 가장 복잡한 경로 (`import`)

`import` 는 이 프로그램에서 계층이 가장 많이 관여하는 명령입니다. 정책이 셋(실패/중복/카테고리 자동 등록) 얽혀 있고, 준비와 커밋이 나뉘어 있습니다.

```
python -m budget_app import --from data.csv --atomic --on-duplicate skip
  → cmd_import(ctx, args)
      → ImportExportService.import_csv(path, atomic=True, on_duplicate="skip")
          │
          │  ── 준비(prepare) 단계: 파일을 전혀 건드리지 않음 ──
          ├─ TransactionRepository.id_allocator()   파일 1회 스캔 → 발급기
          ├─ CategoryStore.name_set()               파일 1회 스캔 → 이름 집합
          └─ for (lineno, row) in csv_io.read_rows(path):     ← CSV 어댑터
                 ├─ csv_io.parse_row()              필드 검증 (validators 사용)
                 │     실패 → atomic? AppError 발생 : batch.note_error()
                 ├─ _resolve_id()                   id 결정 (중복 정책)
                 │     중복 + skip → batch.note_duplicate(), 이 행 버림
                 └─ batch.transactions.append(ParsedRow.to_transaction(tx_id))
          │
          │  ── 커밋(commit) 단계: 여기서 처음 파일이 바뀜 ──
          └─ _commit(batch, atomic=True) → _commit_atomic(batch)
                 ├─ TransactionRepository.remember_ids(txs)   워터마크 먼저
                 └─ with UnitOfWork() as uow:                 두 파일 = 한 단위
                        ├─ uow.stage(cats, extra=새 카테고리)  → categories.jsonl.tmp
                        ├─ uow.stage(txs,  extra=거래들)       → transactions.jsonl.tmp
                        └─ __exit__ → commit() → os.replace 두 번 연달아
           (--atomic 없이 부분 성공 모드면 _commit_appending:
            CategoryStore.add_many → TransactionRepository.append_many, 둘 다 이어쓰기)
      → presenter.import_result_line(report, mode)   결과 한 줄 (stdout)
      → presenter.import_problem_lines(report)       사유들 (stderr)
```

budget_app/services/importexport.py:88-102

```python
    def import_csv(
        self,
        in_path: Path,
        *,
        atomic: bool = False,
        on_duplicate: str = config.DEFAULT_ON_DUPLICATE,
    ) -> ImportReport:
        """CSV 거래 일괄 등록.

        준비 단계에서 모든 행을 검증·판정한 뒤에만 커밋 단계로 넘어간다.
        카테고리 자동 등록과 ID 발급도 커밋 단계에서 한 번에 일어나므로, 원자
        모드에서 준비 중 중단되면 카테고리·거래 어느 쪽도 남지 않는다.
        """
        batch = self._prepare(Path(in_path), atomic=atomic, on_duplicate=on_duplicate)
        return self._commit(batch, atomic=atomic)
```

**메서드 본문이 두 줄**입니다. 이름이 곧 구조 설명이 됩니다 — 준비하고, 커밋한다.

이 경로에서 각 계층이 무엇을 아는지 정리하면 다음과 같습니다.

| 계층 | 이 명령에서 아는 것 | 모르는 것 |
|---|---|---|
| `cli/handlers.py` | 인자 이름, 모드 표시 문구, 두 출력 채널 | 검증 규칙, 중복 판정 |
| `services/importexport.py` | 실패 정책, 중복 정책, 카테고리 자동 등록 | CSV 파일 형식, JSONL 쓰기 방법 |
| `storage/csv_io.py` | CSV 헤더/컬럼/인코딩, 필드 검증 | 중복이 무엇인지, 원자성이 무엇인지 |
| `storage/ids.py` | 어떤 번호가 이미 쓰였는지, 다음 번호 | 그 번호가 CSV 에서 왔는지 |
| `storage/unit_of_work.py` | 여러 파일을 한 단위로 바꾸는 법 | 무엇을 왜 쓰는지 |
| `storage/repositories.py` `jsonl.py` | 원자적 쓰기, 이어쓰기 | CSV 가 존재한다는 사실 |
| `domain/validators.py` | 각 필드의 규칙 | 파일이 존재한다는 사실 |

`csv_io` 가 "중복"을 모른다는 점이 특히 중요합니다. 그래서 CSV 스키마가 바뀌어도 정책 코드는 그대로고, 정책이 바뀌어도 CSV 파싱 코드는 그대로입니다.

> **🔎 문법의 출처** — `with UnitOfWork() as uow:` 는 PEP 343 으로 파이썬 2.5 에 들어온 `with` 문입니다. 파이썬은 이것을 "`__enter__()` 를 불러 그 반환값을 `uow` 에 대입하고, 블록이 어떻게 끝나든 — 정상 종료든 예외든 — `__exit__(예외타입, 예외값, 트레이스백)` 을 반드시 부른다"로 풀어냅니다. `UnitOfWork.__exit__` 은 예외 인자가 `None` 인지 보고 `commit()` 할지 `rollback()` 할지 정합니다(`storage/unit_of_work.py:172-181`). "준비 중 죽으면 아무것도 남지 않는다"는 약속이 `try/finally` 를 손으로 쓰지 않고도 지켜지는 이유입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

정책 3축(실패 축 × 중복 축 × 카테고리 자동 등록)의 조합이 어떻게 결정되는지는 [08. 서비스 계층](./08-services.md)에서 다룹니다 — 요지는 `--atomic` 이 "준비 중 한 줄이라도 실패하면 즉시 `AppError` 로 중단(파일 무접촉)", 기본 모드는 "실패한 줄만 기록하고 나머지는 넣는다"이고, `--on-duplicate` 는 그와 **독립적으로** id 충돌만 다룬다는 것입니다.

---

## 6. AppContext — 수동 의존성 주입(DI)과 부작용 분리

**개념.** 의존성 주입이란 "객체가 필요한 협력자를 스스로 만들지 않고 **밖에서 받는** 것"입니다.

budget_app/services/transactions.py:23-25

```python
    def __init__(self, txs: TransactionRepository, cats: CategoryStore):
        self.txs = txs
        self.cats = cats
```

`TransactionService` 는 저장소를 **인자로 받습니다**. 만약 생성자 안에서 `self.txs = TransactionRepository(Path("./data"))` 라고 직접 만들었다면, 이 서비스는 영원히 `./data` 폴더에 묶이고 테스트에서 가짜 저장소로 바꿀 수도 없습니다. 네 서비스가 모두 같은 모양입니다(`services/budgets.py:23-25`, `services/categories.py:18-20`, `services/importexport.py:71-73`).

그럼 그 저장소는 누가 만드나 — **합성 루트(composition root)** 인 `AppContext` 입니다.

budget_app/context.py:33-65

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

### 6.1 저장소 객체가 서비스 사이에서 공유됩니다

`self._txs` 하나가 `tx_service`, `cat_service`, `budget_service`, `io_service` 네 곳에 전달됩니다. 저장소는 상태를 거의 갖지 않지만(경로와 ID 워터마크), 파일 경로 계산이 한 곳에서 끝나므로 "서비스마다 다른 폴더를 보는" 사고가 구조적으로 불가능합니다.

밑줄이 붙은 `_txs`/`_cats`/`_budgets` 는 관례가 아니라 **테스트로 강제되는 규칙**입니다.

tests/test_architecture.py:99-106

```python
def test_app_context_does_not_expose_repositories():
    """핸들러가 서비스를 건너뛸 수 있는 통로를 남기지 않는다."""
    from budget_app.context import AppContext

    ctx = AppContext(Path("."))
    public = {name for name in vars(ctx) if not name.startswith("_")}
    assert not {"txs", "cats", "budgets"} & public, f"저장소가 공개돼 있다: {public}"
    assert "tx_service" in public and "backup_service" in public
```

> **⚙️ 내부 동작** — `vars(ctx)` 는 `ctx.__dict__` 를 그대로 돌려줍니다. 파이썬 객체의 인스턴스 속성은 클래스에 선언되는 것이 아니라 **생성자가 대입할 때 이 딕셔너리에 들어가는** 것이므로, `vars()` 한 번이면 "이 객체가 실제로 무엇을 들고 있는가"의 전체 목록이 나옵니다. 그래서 이 테스트는 소스를 읽지 않고 객체를 실제로 만들어 확인합니다. `AppContext(Path("."))` 를 만들어도 디스크가 안전한 것은 생성자가 경로 계산만 하기 때문입니다(§6.2) — 만약 이전처럼 생성자가 mkdir 을 했다면 **이 테스트 자체가 부작용**이 됐을 것입니다. → [12 §1-B](./12-syntax-and-stdlib.md)

### 6.2 생성자와 `prepare()` 를 나눈 이유 (리팩터)

**리팩터 전에는 저장소 생성자가 디스크를 건드렸습니다.**

```python
# (리팩터 전 — 지금은 없는 코드)
    def __init__(self, data_dir: Path, seed_defaults: bool = True):
        self.path = Path(data_dir) / self.FILE_NAME
        _ensure_parent(self.path)              # mkdir!
        created = not self.path.exists()
        if created:
            self.path.touch()                  # 파일 생성!
        if seed_defaults and self._is_empty():
            for name in config.DEFAULT_CATEGORIES:
                self._append(Category(name=name))   # 파일 쓰기!
```

여기에 더해 **핸들러마다 `AppContext(args.data_dir)` 를 새로 만들었습니다**(10곳). 결과적으로:

- 객체를 만드는 것만으로 디스크가 바뀝니다.
- `budget_app list --data-dir /오타난/경로` 가 조용히 폴더를 만들고 기본 카테고리 5개를 씁니다.
- `backup` 명령도 백업하려는 폴더를 먼저 만들어 버려, "백업할 데이터가 없다"는 오류 대신 **빈 백업**이 생깁니다.

지금은 셋이 분리되어 있습니다.

| 단계 | 하는 일 | 호출 시점 |
|---|---|---|
| `__init__` | 경로 계산만 | 객체 생성 시 |
| `ensure_ready()` | 폴더·파일 생성 | `prepare()` 안에서 |
| `seed_defaults()` | 기본 카테고리 심기 | `prepare()` 안에서 |

그리고 진입점(`cli/app.py:78-80` 의 `_dispatch`)이 **한 번만** `prepare()` 를 호출하되, 필요 없는 명령은 건너뜁니다. 건너뛸지 여부는 파서가 남긴 `needs_storage` 플래그가 정합니다.

budget_app/cli/parser.py:239-243

```python
def _add_backup(sub) -> None:
    p = sub.add_parser("backup", help="데이터 폴더 백업 (보너스)")
    _add_shared_options(p)
    # 백업은 기존 폴더를 읽기만 한다 — 없으면 만들지 말고 오류로 알려야 한다.
    p.set_defaults(handler="backup", needs_storage=False)
```

### 6.3 왜 DI 프레임워크를 쓰지 않았나

이 프로젝트는 표준 라이브러리만 쓴다는 제약이 있고, 의존 관계가 8개 객체(저장소 3 + 서비스 5)로 단순합니다. `AppContext.__init__` 열여섯 줄이 프레임워크가 할 일을 전부 하며, **"무엇이 무엇에 의존하는지"가 한 화면에 보인다**는 장점까지 있습니다. 규모가 커지면 그때 도구를 고려하면 됩니다.

그런데 "규모가 작아서"만이 이유는 아닙니다. **파이썬에는 DI 컨테이너가 해결하려는 문제 자체가 거의 없습니다.**

> **🔎 문법의 출처** — 자바·C# 계열의 DI 컨테이너는 두 가지를 대신해 줍니다. (1) "이 인터페이스의 구현체를 찾아 꽂아라" — 리플렉션으로 타입을 뒤져 생성자를 호출하는 일, (2) "테스트에서는 다른 구현으로 바꿔라" — 컴파일 시점에 타입이 고정돼 있어 언어만으로는 못 하는 일. 파이썬에서는 둘 다 언어 기능으로 끝납니다.
>
> - **함수와 클래스가 일급 객체**입니다. 클래스 자체가 값이므로 `TransactionService(repo, cats)` 처럼 그냥 부르면 되고, "팩토리"가 필요하면 함수 하나면 됩니다. 별도의 등록 DSL 이 필요 없습니다.
> - **덕 타이핑(duck typing)** 이라 타입 선언이 실행에 관여하지 않습니다. `def __init__(self, txs: TransactionRepository, ...)` 의 어노테이션은 문서이자 정적 검사용일 뿐, 인터프리터는 검사하지 않습니다. 그래서 테스트가 `.stream()` 과 `.append()` 만 있는 가짜 객체를 넘겨도 그대로 동작합니다 — 인터페이스를 추상 클래스로 뽑아 두지 않아도 교체가 됩니다(§8.5 에서 다시 다룹니다).
>
> 그 결과 파이썬의 "DI 프레임워크"는 대개 **딕셔너리 하나와 생성자 호출 몇 줄**로 축소되고, 그것이 이 프로젝트의 `AppContext` 입니다. → [12 §1-B](./12-syntax-and-stdlib.md)

---

## 7. 오류 처리 아키텍처 — 예외의 발생지와 변환지

### 7.1 예외의 3가지 종류와 발생 계층

| 예외 | 정의 위치 | 발생 계층 | 의미 |
| --- | --- | --- | --- |
| `ValidationError` | errors.py:33 | domain/validators, entities, tx_id, storage/jsonl | **값**이 규칙 위반 |
| `AppError` | errors.py:41 | services/*, storage/csv_io, cli | **상황**이 규칙 위반 |
| `InputAborted` | cli/prompts.py:28 | cli/prompts | EOF 로 입력 중단 (AppError 의 자식) |
| 내장 예외 | (파이썬) | storage/*, context | 파일 없음/권한/인코딩/폴더 아님 등 |

`ValidationError` 는 `ValueError` 를 상속합니다(`errors.py:33`) — 이 예외를 모르는 호출자도 `except ValueError` 로 자연스럽게 받게 하려는 선택입니다. `AppError` 는 `message` 와 `hint` 두 속성을 갖는 것이 존재 이유이므로 `Exception` 을 직접 상속합니다(`errors.py:41-51`).

**`ValidationError` vs `AppError` 의 구분 기준**이 이 아키텍처의 작지만 중요한 결정입니다.

- `ValidationError` — **값 하나만 보고 판단 가능**. `"2024-13-45"` 는 저장된 데이터를 몰라도 틀렸음을 압니다. 그래서 `validators` 가 던집니다.
- `AppError` — **저장된 상태를 봐야 판단 가능**. `"food"` 라는 카테고리가 유효한지는 `categories.jsonl` 을 읽어야 압니다. 그래서 서비스가 던집니다.

이 구분이 그대로 종료 코드로 이어집니다(2 vs 4).

### 7.2 변환지 — `handle_errors` 한 곳

아무리 깊은 곳에서 예외가 나도, 사용자에게 보이는 형태로 바꾸는 곳은 **단 한 군데**입니다.

```
validators.parse_date()      ── ValidationError ──┐
services.*.add()             ── AppError ─────────┤
storage.jsonl.iter_raw()     ── FileNotFoundError ┤
storage.csv_io.read_rows()   ── AppError ─────────┤
context._require_usable_...  ── NotADirectoryError┤
                                                  ▼
                        @handle_errors  (cli/error_handler.py:20-121)
                                    ↑ 붙는 자리는 cli/app.py:61 의 _dispatch 하나
                                                  │
                     ┌────────────────────────────┼────────────────────────┐
                     ▼                            ▼                        ▼
              output.err("[오류] ...")      output.err("[힌트] ...")   return EXIT_*
                     │                            │                        │
                     └──── stderr ────────────────┘             main → __main__ → sys.exit
```

**이 구조의 이점이 셋입니다.**

1. **각 계층은 자기 언어로 실패를 말하면 됩니다.** 저장소는 `FileNotFoundError`, 서비스는 `AppError` 를 던지고 "이걸 사용자에게 어떻게 보여줄까"를 고민하지 않습니다.
2. **메시지 정책이 한 곳입니다.** `[오류]`/`[힌트]` 형식, stderr 채널, 종료 코드 매핑이 전부 `cli/error_handler.py` 한 파일에 있습니다.
3. **적용 지점도 한 곳입니다.** 이전에는 핸들러 13개에 `@handle_errors` 가 각각 붙어 있었고, 정작 `AppContext` 생성과 `prepare()` 는 그 **밖**이라 `--data-dir` 오타 하나로 원시 트레이스백이 났습니다. 지금은 `_dispatch` 하나에만 붙습니다 — "핸들러를 추가할 때 데코레이터를 빠뜨리는" 실수가 성립하지 않습니다.

전체 except 체인과 순서 정책은 [06. 횡단 관심사와 예외 처리](./06-decorators.md)에서 상세히 다룹니다 — 순서의 핵심은 **좁은 것부터**입니다. `try` 문은 위에서부터 `isinstance` 검사를 하고 **처음 맞는 절 하나만** 실행하므로, `FileNotFoundError`·`IsADirectoryError`·`NotADirectoryError`·`PermissionError` 를 부모인 `except OSError` 보다 위에 두지 않으면 그 네 절이 영원히 도달 불가능해집니다. `cli/error_handler.py` 는 네 부류(종료 신호 → 입력 오류 → 환경 상태 → 최후 방어선)로 묶고 각 부류 안에서 이 순서를 지킵니다.

### 7.3 출력 채널도 아키텍처입니다

"어디로 나가는가"가 계층 설계의 일부입니다.

| 채널 | 내용 | 함수 | 왜 |
|---|---|---|---|
| stdout | 명령의 **결과** | `output.out()` | `list > out.txt` 로 데이터만 받을 수 있어야 함 |
| stderr | 사용자용 **진단** | `output.err()` | 오류가 데이터 파일을 오염시키면 안 됨 |
| logging | 개발자용 **진단** | `logger.debug()` | 기본은 꺼짐, `--debug` 로만 켬 |

budget_app/cli/output.py:11-18 (모듈 docstring 발췌)

```python
"""...
왜 stdout 과 stderr 를 나누나:

1. **리다이렉트 오염 방지** — 오류가 stdout 으로 나가면 ``list > out.txt`` 의 데이터
   파일에 오류 문자열이 섞인다. 파이프라인에서 쓰는 도구로서는 버그다.
2. **파이프가 끊겨도 살아남음** — 하류가 먼저 닫혀 stdout 이 ``BrokenPipeError`` 로
   깨진 상황에서도 stderr 는 열려 있어 사용자에게 원인을 전할 수 있다.
3. **셸에서 골라 버릴 수 있음** — ``2>/dev/null`` 은 진단만, ``1>/dev/null`` 은 결과만
   버린다. 두 채널이 섞여 있으면 둘 다 불가능하다.
"""
```

이 규칙이 실제로 지켜지는지는 셸에서 확인할 수 있습니다.

```bash
python -m budget_app search --category 없는것 2>/dev/null   # 진단만 버림 → "(데이터 없음)"
python -m budget_app import --from nope.csv 1>/dev/null     # 결과만 버림 → 오류만 보임
```

> **⚙️ 내부 동작** — `output.err()` 이 `print(..., file=sys.stderr)` **앞에** `sys.stdout.flush()` 를 부르는 이유는 두 스트림의 버퍼링 정책이 다르기 때문입니다. CPython 은 stdout 이 터미널(tty)이면 줄 단위 버퍼링, 파이프나 파일이면 **블록 버퍼링**(보통 8KB 단위)으로 잡고, stderr 는 대상이 무엇이든 라인 버퍼(`line_buffering=True`)라 개행마다 곧바로 흘러나갑니다. 그래서 `cmd 2>&1 | less` 처럼 두 채널을 다시 합치면, 아직 버퍼에 남은 결과보다 진단이 먼저 튀어나와 순서가 뒤집힙니다. 비우고 쓰면 그 역전이 사라집니다.
>
> 같은 이유로 `_silence_broken_pipe()` 가 필요합니다. 하류가 먼저 닫힌 뒤 인터프리터가 종료하면서 stdout 버퍼를 마지막으로 비우려다 또 `BrokenPipeError` 가 나고, 그것은 이미 예외 처리 밖이라 `Exception ignored in: ...` 가 찍힙니다. `os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())` 는 **파일 서술자 1번 자체를 `/dev/null` 로 갈아 끼워서**, 남은 바이트가 아무 데도 가지 않고 조용히 사라지게 합니다(파이썬 공식 문서가 권장하는 레시피입니다). → [12 §3](./12-syntax-and-stdlib.md)

`import` 는 한 명령이 두 채널을 모두 쓰는 예입니다.

budget_app/cli/handlers.py:176-184

```python
def cmd_import(ctx: AppContext, args: argparse.Namespace) -> int:
    mode = messages.MODE_ATOMIC if args.atomic else messages.MODE_PARTIAL
    report = ctx.io_service.import_csv(
        Path(args.from_), atomic=args.atomic, on_duplicate=args.on_duplicate
    )
    # 요약 한 줄은 결과(stdout), 건너뛴 줄의 사유는 진단(stderr)이다.
    output.out(presenter.import_result_line(report, mode))
    output.err_lines(presenter.import_problem_lines(report))
    return config.EXIT_OK
```

---

## 8. 설계 원칙 정리 — 이 코드가 지키고 있는 것

### 8.1 관심사 분리 (Separation of Concerns)

"입력 받기 / 규칙 판단 / 파일 쓰기 / 화면 표시"를 서로 다른 파일에 두었습니다. `cmd_summary` 세 줄(§2.2)이 이 원칙의 가장 압축된 증거입니다.

### 8.2 단일 책임 원칙 (Single Responsibility Principle)

**"이 파일을 고칠 이유가 몇 개인가"** 가 기준입니다(§1.1). 클래스 수준에서도 같습니다 — `TransactionService`(거래 CRUD), `BudgetService`(예산·요약), `CategoryService`(카테고리 보호), `ImportExportService`(CSV 정책)가 각각 하나의 이유로만 바뀝니다.

`JsonlStore` 와 하위 클래스의 관계도 이 원칙입니다.

| 클래스 | 아는 것 |
|---|---|
| `JsonlStore` | JSONL 파일을 읽고 쓰는 법 |
| `TransactionRepository` | 거래 고유의 것 — ID 발급, 카테고리 재지정 |
| `CategoryStore` | 카테고리 고유의 것 — 이름 중복, 기본값 시딩 |
| `BudgetStore` | 예산 고유의 것 — 같은 달은 덮어쓰기 |

### 8.3 DRY (Don't Repeat Yourself) — 네 가지 "단일 출처"

**(1) 값·문구의 단일 출처.** 계층별 `config.py` 와 `messages.py`(§2.7). 파일명·형식·한도·종료 코드·모든 화면 문자열이 한 번씩만 정의됩니다.

**(2) 검증 규칙의 단일 출처.** `domain/validators.py`. 규칙 하나 = 함수 하나이고, 엔티티(`__post_init__`)·CSV 어댑터·대화형 입력이 같은 함수를 부릅니다. 리팩터 전에는 금액 규칙이 세 형태(모듈 함수 / `Transaction.validate_amount` / `Budget` 이 부르는 모듈 함수)로 존재했습니다.

**(3) 파일 처리의 단일 출처.** `JsonlStore`. 세 저장소가 복사해 갖고 있던 열기/스트리밍/원자적 재작성 코드가 한 곳으로 모였습니다.

**(4) 기간 규칙의 단일 출처.** `domain/periods.py` 의 `month_range`(20-30행). 리팩터 전에는 `summary` 가 `date.startswith(month + "-")`, `export` 가 CLI 의 `_month_bounds()` 로 **같은 개념을 두 알고리즘으로** 구현하고 있었습니다.

```
[리팩터 전]
cli._month_bounds()  ──calendar 로 말일 계산──▶  export 만 사용
services.monthly_summary()  ──startswith 접두 비교──▶  summary 만 사용
        ↑ 같은 개념, 다른 구현, 다른 계층

[리팩터 후]
domain/periods.py :: month_range()  ──calendar.monthrange 로 실제 말일 계산
        ↓
domain/queries.py :: SearchFilter.for_month()
        ├──▶ services/budgets.py :: BudgetService.monthly_summary()
        └──▶ cli/handlers.py :: _export_filter()
```

> **⚙️ 내부 동작** — `calendar.monthrange(year, month)` 는 `(그 달 1일의 요일, 그 달의 일수)` 튜플을 돌려줍니다. `month_range` 가 쓰는 것은 두 번째 값뿐입니다(`[1]`). 윤년 판정까지 포함해 실제 말일을 주므로 "모든 달을 31일로 가정"하는 실수가 원천 봉쇄됩니다. 이 모듈의 이름이 `calendar.py` 가 아니라 `periods.py` 인 것은 표준 라이브러리와 이름이 겹치면 읽는 사람이 헷갈리기 때문입니다 — 파이썬 3 의 절대 import 규칙(PEP 328) 덕분에 동작은 안전하지만, 혼동 자체가 비용이라는 판단입니다. → [12 §2-A](./12-syntax-and-stdlib.md)

**DRY 의 본질은 "코드 줄이기"가 아니라 "지식의 중복 제거"** 입니다. 위 네 가지는 전부 "같은 지식이 두 곳에 있으면 어긋날 수 있다"는 문제를 해결한 것입니다.

### 8.4 명시적 계약 (Explicit Contract)

타입으로 계약을 적어 둔 자리들입니다.

| 계약 | 표현 | 적힌 자리 |
|---|---|---|
| 검증기 | `Callable[[str], T]` — 문자열 받아 T 반환, 실패는 ValidationError | `cli/prompts.py:60` |
| 재작성 콜백 | `Callable[[T], T \| None]` — 바꾼 것 / 그대로 / 삭제(None) | `storage/jsonl.py:266`, `315` |
| 명령 핸들러 | `Callable[[AppContext, Namespace], int]` — 컨텍스트+인자 → 종료 코드 | `cli/app.py:26` (`Handler` 별칭) |
| 수정 요청 | `TransactionPatch` — 필드가 선언돼 있어 오타가 TypeError | `domain/entities.py:127-154` |
| 계산 결과 | `MonthlySummary` / `ImportReport` — 문자열 키 dict 대체 | `domain/results.py` |

리팩터의 상당 부분이 **"암묵적 dict 계약 → 명시적 타입 계약"** 이었습니다.

> **🔎 문법의 출처** — `Callable[[str], T]` 의 `T` 는 `TypeVar` 로 선언한 타입 변수입니다(`cli/prompts.py:25` 의 `T = TypeVar("T")`). "무엇이든 좋지만 **입력과 출력에서 같은 것**"을 뜻하므로, `ask_until(prompt, parse_amount)` 의 결과가 `int` 로, `ask_until(prompt, parse_date)` 의 결과가 `str` 로 각각 추론됩니다. 여기서 중요한 것은 **이 어노테이션이 실행에 아무 영향을 주지 않는다**는 점입니다 — 어노테이션을 쓰는 파일 28개가 모두 `from __future__ import annotations` 를 켜 두어 어노테이션은 문자열로만 보관되고, 검사는 mypy/pyright 같은 별도 도구가 합니다. 계약은 **사람과 정적 검사기를 향한 선언**이고, 실행 시점의 강제는 여전히 `__post_init__` 같은 코드가 합니다. → [12 §2-B](./12-syntax-and-stdlib.md)

### 8.5 의존성 역전은 아닐까? (구분해 두기)

이 프로젝트는 의존성 **주입**(DI)은 쓰지만 의존성 **역전**(DIP, 추상 인터페이스에 의존)은 쓰지 않습니다. `TransactionService` 는 `TransactionRepository` **구체 클래스**를 타입 힌트로 받습니다(`services/transactions.py:23`).

규모상 추상화 계층(`ABC`/`Protocol`)을 도입할 실익이 없기 때문이며, 필요해지면(예: SQLite 저장소 추가) 그때 인터페이스를 뽑으면 됩니다. **지금 없는 것과 못 하는 것을 구분해서 말할 수 있어야** 합니다.

여기서 §6.3 의 논점이 다시 걸립니다 — 파이썬에서는 어노테이션이 실행에 관여하지 않으므로, DIP 가 없어도 **교체 자체는 이미 가능합니다.** 필요한 메서드만 가진 객체를 넘기면 그대로 돕니다. `Protocol` 을 도입해서 얻는 것은 실행 시점의 능력이 아니라 **"저장소란 무엇인가"를 한 곳에 적어 두고 정적 검사기가 확인하게 하는 것**입니다. 그 구분을 정확히 말할 수 있으면 "왜 안 했나"에 대한 답이 변명이 아니라 판단이 됩니다.

한편 도메인 계층은 다른 방식으로 추상화를 씁니다. `domain/specs.py` 의 `Spec` 은 `is_satisfied_by` 하나를 요구하는 기반 클래스이고, `And`/`Or`/`Not`/`DateFrom`/… 이 이를 구현해 조건을 조합 가능한 값으로 만듭니다. 즉 **이 코드에 다형성이 없는 것이 아니라, 저장소 축에만 없습니다.**

---

## 9. 설계의 진화 — 리팩터 전후 대조표

이 코드는 처음부터 지금 모습이 아니었습니다. 리팩터에서 바뀐 것을 한눈에 정리합니다.

| # | 리팩터 전 | 문제 | 리팩터 후 |
|---|---|---|---|
| 1 | `AppError` 가 `decorators.py` | services → decorators → output 역류 | `errors.py` 신설 |
| 2 | `handle_errors` 가 `decorators.py` | 관측과 표현이 한 파일 | `error_handler.py` 분리 |
| 3 | `config.py` 에 값+문구 | models 가 CLI 문구에 의존 | `messages.py` 분리 |
| 4 | 검증이 3형태(모듈함수/staticmethod) | 규칙 중복, 의존 역류 | `validators.py` 단일 정의 |
| 5 | `changes: Dict[str, object]` 가 3계층 관통 | 오타가 조용히 무시됨 | `TransactionPatch` dataclass |
| 6 | `repository.update` 가 도메인 변경 수행 | 저장소가 도메인 판단 | `with_patch` + `replace` |
| 7 | `stream()` 하나 (손실적 읽기) | **재작성 시 손상 줄 영구 삭제** | `iter_raw()` / `stream()` 분리 |
| 8 | `max_id_num` 이 `stream()` 사용 | **검증 실패 줄의 id 를 못 봐 중복 발급** | `iter_raw()` 기반 `id_state()` |
| 9 | ID 발급 규칙이 2곳 | 서비스가 저장소 ID 포맷을 앎 | `IdAllocator` |
| 10 | CSV I/O 가 `services.py` | JSONL 은 저장소, CSV 는 서비스 | `storage/csv_io.py` 분리 |
| 11 | `backup_data_dir` 가 `services.py` | 도메인 판단 없는 파일 복사 | `storage/backup.py` 로 이동 (`services/maintenance.py` 가 얇게 호출) |
| 12 | 요약이 9키 dict | 문자열 키, 화면이 상태 해석 | `MonthlySummary` + property |
| 13 | "이 달" 규칙이 2곳 2방식 | 갈라질 수 있는 구조 | `domain/periods.py::month_range` 통합 |
| 14 | 저장소 생성자가 디스크 조작 | 객체 생성 = 부작용 | `ensure_ready()` / `seed_defaults()` |
| 15 | `cli.py` 512줄, 책임 4개 | 고칠 이유가 넷 | parser/prompts/presenter/handlers 분리 |
| 16 | `set_defaults(func=cmd_x)` | 파서와 핸들러 결합(순환 위험) | 문자열 키 + `HANDLERS` (§1.2.1) |
| 17 | `category`/`budget` 통합 핸들러 | 도달 불가 분기(죽은 코드) | 하위 명령별 핸들러 |
| 18 | export CSV 에 `id` 없음 | **왕복 시 거래 중복 생성** | `id` 선택 컬럼 + 중복 정책 |
| 19 | 3저장소가 파일 처리 코드 복제 | 약 60줄 중복 | `JsonlStore` 제네릭 기반 클래스 |
| 20 | 원자적 쓰기에 fsync 없음 (당시 이름 `_atomic_write_jsonl`) | 크래시 시 빈 파일 가능 | `atomic_write_lines`(밑줄 없음, `storage/jsonl.py:80-87`)에 `flush` + `fsync` |
| 21 | 핸들러 13개에 `@handle_errors` 개별 부착 | 컨텍스트 조립이 방패 **밖** | `_dispatch` 한 곳에만 부착 (§7.2) |
| 22 | `--atomic` 이 거래 파일 안에서만 원자적 | 카테고리만 남는 중간 상태 | `UnitOfWork` — 두 파일 한 단위 (§5) |
| 23 | 계층 규칙이 문서에만 존재 | 위반을 아무도 못 잡음 | `tests/test_architecture.py` (AST 검사, §1.2.2) |

**7·8·18·21·22 번은 단순한 구조 개선이 아니라 실제 버그였습니다.** 7번은 무관한 삭제가 손상 줄을 지웠고, 8번은 중복 id 를 발급했으며, 18번은 export→import 왕복 때마다 거래가 복제됐고, 21번은 `--data-dir` 오타 하나에 원시 트레이스백을 냈고, 22번은 `--atomic` 의 약속을 절반만 지켰습니다. 앞의 세 버그는 뿌리가 같다는 점이 흥미롭습니다 — **읽기 경로 하나가 두 가지 용도(조회 / 재작성·스캔)를 겸하고 있었던 것**입니다.

---

## 10. 요약 — 과제 방어용 문답 정리

**Q. 코드를 몇 개 모듈로 나눴고, 각 모듈의 책임을 어떻게 정했나요?**

구현 파일 38개(패키지 선언 5개 별도), 4계층입니다. 기준은 "이 파일을 고칠 이유가 몇 개인가"입니다. CLI 계층만 해도 문법(`parser`)·입력(`prompts`)·표시(`presenter`)·채널(`output`)·오류표현(`error_handler`)·오케스트레이션(`handlers`)·조립과 진입(`app`)으로 나뉘는데, 각각 바뀌는 이유가 다르기 때문입니다. 의존 방향은 import 문으로 검증 가능하며(§1.2) 위로 향하는 의존이 하나도 없고, 그것을 `tests/test_architecture.py` 가 AST 로 매 실행마다 확인합니다.

**Q. 클래스에 부여한 책임 경계를 어떻게 정했나요?**

두 예를 듭니다. (1) `JsonlStore` 와 세 하위 저장소 — "JSONL 파일을 다루는 법"은 공통이므로 부모에, "무엇이 유일 키인가" 같은 엔티티 고유 규칙은 자식에 두었습니다. (2) `csv_io.ParsedRow` 와 `services.ImportExportService` — 어댑터는 "CSV 행을 검증"까지, 정책은 "중복이면 어떻게 할지"부터 담당하고, 그 경계를 `ParsedRow`(id 가 아직 비어 있는 값)라는 타입으로 그었습니다.

**Q. 파일 기반 update/delete 를 어떻게 안전하게 처리했나요?**

임시 파일에 전부 쓰고 `flush` + `fsync` 로 디스크에 내린 뒤 `os.replace` 로 이름을 교체합니다. `os.replace` 는 같은 파일시스템에서 원자적이라 "교체 전" 아니면 "교체 후"만 존재합니다. 여기에 더해, 재작성의 재료를 `iter_raw()`(모든 줄 보존)로 바꿔서 **해석하지 못한 줄이 원문 그대로 살아남게** 했습니다. 리팩터 전에는 무관한 거래를 지울 때 손상된 줄이 함께 사라졌습니다.

**Q. 계층을 나눠서 실제로 얻은 게 뭔가요?**

세 가지를 실증할 수 있습니다. (1) 화면 문구를 고쳐도 도메인은 영향을 받지 않습니다 — `domain/*` 는 `cli.messages` 를 import 하지 않고, 자기 계층의 `domain/messages.py` 만 봅니다(§1.2 목록). (2) 서비스 계층이 파일을 열지 않으므로 저장 방식을 SQLite 로 바꿔도 정책 코드는 그대로입니다. (3) 프레젠터가 문자열을 반환하므로 화면 형식을 프로세스 없이 검증할 수 있습니다.

**Q. 계층 구조에서 가장 아쉬운 점은?**

의존성 **역전**(추상 인터페이스)이 없어 서비스가 구체 저장소 클래스에 묶여 있습니다. 지금 규모에서는 실익이 없다고 판단했지만, 저장 방식을 실제로 교체하게 되면 `Protocol` 을 도입해야 합니다. 또 `update` 경로가 파일을 3번 훑습니다(서비스의 `get` → 저장소의 `get` → `rewrite`) — 정확성을 위해 성능을 양보한 지점입니다([10](./10-advanced-design.md)).

---

**다음 문서**: 계층별 상세는 [05. 설정·검증·모델](./05-config-and-models.md) → [06. 횡단 관심사와 예외 처리](./06-decorators.md) → [07. 저장소 계층](./07-repository.md) → [08. 서비스 계층](./08-services.md) → [09. CLI 계층](./09-cli.md) 순으로 이어집니다.
