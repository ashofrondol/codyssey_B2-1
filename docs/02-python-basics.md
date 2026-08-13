# 02. 이 코드에 쓰인 파이썬 기초 문법

## 쉬운 말로 먼저

budget_app 은 가계부를 파일에 적어 두고, 검은 화면에 명령어를 쳐서 꺼내 보는 프로그램입니다. 이 문서는 그 프로그램의 어느 한 기능을 설명하지 않습니다. 대신 프로그램 곳곳에 흩어져 있는 **파이썬이라는 언어의 문장 규칙** 중, 이 소스에 실제로 쓰인 것만 골라 모았습니다. 까다로운 점은 파이썬이 같은 일을 하는 길을 여러 개 열어 둔다는 데 있습니다. 빈칸에 값을 채워 넣는 방법만 해도 세 가지가 있고, 목록을 훑는 방법도 여럿입니다. 이 소스는 그중 하나씩을 골라 썼고 고른 이유가 매번 다른데, 이 문서가 진짜로 다루는 것은 문법 자체가 아니라 **그 선택의 이유**입니다.

한 가지 미리 말해 둡니다 — 이 문서는 처음부터 끝까지 읽는 글이 아닙니다. 1,300줄이 넘고 열두 개의 절이 서로 이어지지 않으므로, 코드를 읽다 모르는 기호를 만났을 때 그 기호를 찾아보는 **사전**으로 쓰는 편이 맞습니다.

**이 문서에 자주 나오는 말**

| 말 | 쉬운 뜻 |
| --- | --- |
| 모듈 | 코드가 담긴 파일 한 장(`.py`) |
| 패키지 | 그런 파일들을 모아 둔 폴더 |
| 인자 | 함수가 값을 받기로 정해 둔 자리, 또는 부를 때 그 자리에 넣어 주는 값(문맥에 따라 둘 다 인자라고 부릅니다) |
| 반환 | 함수가 일을 마치고 돌려주는 값 |
| 예외 | 일이 잘못됐을 때 그 자리에서 얼버무리지 않고 위로 올려 보내는 신호 |
| 타입 힌트 | "여기엔 숫자가 들어옵니다" 같은 메모. 적어 둘 뿐 지키라고 강제하지는 않습니다 |
| 제너레이터 | 결과를 한꺼번에 쌓아 두지 않고 필요할 때마다 하나씩 내주는 것 |
| 컴프리헨션 | 줄 세 개짜리 반복문을 한 줄로 접어 쓴 표기 |

**바쁘면 여기만**

- **[§2](#2-if-__name__--__main__-관용구와-sysexitmain)** — 프로그램이 어디서 시작해 어떤 숫자를 남기고 끝나는지. 입구와 출구라, 여기만 알아도 나머지 절이 어디쯤 붙는지 가늠이 됩니다.
- **[§4.2](#42-왜-포맷-방식이-3가지나-쓰였는가)** — 같은 일에 방법이 셋이고 각각 살아남은 이유가 있다는, 이 문서 전체의 성격이 가장 잘 드러나는 절입니다.
- **[§10.3](#103-타입-힌트는-런타임에-강제되지-않는다)** — 짧고, 비전공자가 가장 자주 하는 오해 하나를 확실히 걷어냅니다.

---

budget_app 소스에 **실제로 등장하는** 기초 문법만 골라, "개념 → 실제 코드 → 왜 여기서 이렇게 썼는가" 순서로 설명합니다.

> **난이도**: 🟢 초보
>
> **먼저 읽으면 좋은 문서**: 없음 — 이 문서가 문법 학습의 출발점입니다. 예외 처리의 심화 내용은 [03. 파이썬 중·고급 기법](./03-python-advanced.md), 계층 구조(왜 파일이 이렇게 나뉘었는가)는 [04. 아키텍처](./04-architecture.md)에서 다룹니다.

---

## 1. 패키지와 모듈

### 1.1 `__init__.py` — 폴더를 **일반 패키지**로 만드는 파일

파이썬에서 `.py` 파일 하나가 **모듈**이고, 모듈을 담은 폴더가 **패키지**입니다. 폴더에 `__init__.py` 가 있으면 그 폴더는 **일반 패키지(regular package)** 가 됩니다. 그리고 `import budget_app` 을 하면 이 `__init__.py` 가 실행됩니다.

> **💡 쉽게 말하면** — 코드 파일 하나는 서랍 한 칸이고, 그것들을 모아 둔 폴더는 서랍장입니다. `__init__.py` 는 서랍장 앞면에 붙인 이름표에 가깝습니다. 이름표가 붙어 있으면 "이건 하나의 서랍장이다"가 분명해지고, 서랍장 자체에 대한 메모(무엇을 담는 장인지, 몇 번째 판인지)를 적어 둘 자리도 생깁니다.
> 다만 이 비유는 "이름표가 없으면 서랍장이 아니다"라는 대목에서 깨집니다 — 파이썬 3.3 부터는 이름표가 없어도 서랍장으로 취급되고(바로 아래에서 다룹니다), 그때는 같은 이름의 서랍장 여럿이 하나로 합쳐지는 다른 규칙이 적용됩니다.
> 깨지는 곳이 하나 더 있습니다. 이름표는 읽히기만 하지만 `__init__.py` 는 서랍장을 열 때마다 — 즉 `import` 할 때마다 — **실행되는 코드**입니다. 그래서 여기에 무언가를 적어 두면 import 하는 것만으로 그 일이 벌어집니다. 이 프로젝트가 이 파일을 거의 비워 둔 이유가 그것입니다(아래 "설계 의도").

budget_app/__init__.py:1-3
```python
"""파일 기반 가계부 콘솔 프로그램."""

__version__ = "1.0.0"
```

이 프로젝트의 `__init__.py` 는 딱 두 가지만 합니다.

- 첫 줄의 문자열은 **docstring** 으로, `import budget_app; help(budget_app)` 을 하면 보이는 패키지 설명입니다.
- `__version__` 은 파이썬 문법 키워드가 아니라 **관례적인 변수 이름**입니다.

설계 의도: `__init__.py` 를 최대한 비워 두면 "패키지를 import 하는 것"만으로는 아무 부수효과(파일 생성, 로깅 설정 등)가 생기지 않습니다. 실제 동작은 전부 각 모듈에 있습니다.

#### `__init__.py` 는 필수가 아닙니다 — 그런데 왜 두었나

흔한 오해 하나를 짚고 갑니다. **파이썬 3.3 부터 `__init__.py` 는 패키지의 필수 조건이 아닙니다.** `__init__.py` 가 없는 폴더도 **네임스페이스 패키지(namespace package, PEP 420)** 로 import 됩니다. 실제로 이 프로젝트에서 `__init__.py` 만 지운 뒤 `python -m budget_app --help` 를 실행해도 **정상 동작합니다.** 상대 임포트 `from .cli import main` 도 그대로 작동합니다.

그럼에도 이 파일을 두는 이유는 세 가지입니다.

**첫째, 패키지 수준 정보를 담을 자리가 필요합니다.** `__version__` 과 docstring 은 `__init__.py` 에만 넣을 수 있습니다.

**둘째, 같은 이름의 폴더를 만났을 때 동작이 다릅니다.** 일반 패키지는 `sys.path` 에서 **처음 찾은 하나만** 쓰고 나머지는 무시(차폐)하지만, 네임스페이스 패키지는 경로상의 **같은 이름 폴더를 전부 하나로 합칩니다(병합)**.

```
sys.path = [ dirA, dirB ]   (양쪽 모두 budget_app/ 폴더를 가지고 있음)

[ __init__.py 있음 — 일반 패키지 ]        [ __init__.py 없음 — 네임스페이스 패키지 ]
  __path__ : list                           __path__ : _NamespacePath
             ['dirA/budget_app']                       ['dirA/budget_app',
                                                        'dirB/budget_app']   ← 병합!
  dirA 의 모듈 → import 성공                dirA 의 모듈 → import 성공
  dirB 의 모듈 → ModuleNotFoundError        dirB 의 모듈 → import 성공
```

> **⚙️ 내부 동작 — `__path__` 의 타입이 실제로 다릅니다.** 위 그림의 `list` / `_NamespacePath` 는 비유가 아니라 실측입니다. 로컬(CPython 3.13.1)에서 확인하면 이렇습니다.
>
>     :::python
>     import budget_app
>     type(budget_app.__path__)            # <class 'list'>                     ← 일반 패키지
>     # __init__.py 없는 폴더를 import 하면
>     type(ns.__path__)                    # _frozen_importlib_external._NamespacePath
>     ns.__file__, ns.__spec__.origin      # (None, None)  ← 실행된 코드가 없다는 뜻
>
> `list` 는 import 시점에 한 번 정해지고 끝이지만, `_NamespacePath` 는 `sys.path` 가 바뀌면 **다시 계산되는 동적 객체**입니다. "나중에 경로가 추가되면 조용히 섞여 들어온다"는 위험이 여기서 나옵니다. 또 `__file__` 이 `None` 이라 `Path(pkg.__file__).parent` 같은 흔한 관용구가 그 자리에서 `TypeError` 로 죽습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

병합은 여러 배포 패키지가 `google.cloud.*` 처럼 같은 최상위 이름을 나눠 쓸 때를 위한 기능입니다. 하지만 이 프로젝트처럼 **독립된 단일 애플리케이션**에서는, 어딘가에 우연히 `budget_app` 이라는 폴더가 하나 더 있으면 조용히 섞여 들어와 원인을 찾기 어려운 버그가 됩니다.

**셋째, 도구 호환성과 명시성입니다.** setuptools 의 `find_packages()` 같은 일부 도구는 `__init__.py` 가 있는 폴더만 패키지로 인식합니다.

> 정리하면 `__init__.py` 는 **문법적 필수 요소가 아니라 설계 선택**입니다. 같은 내용을 질문 형태로 요약한 [11. 설계 FAQ](./11-faq-and-glossary.md) 의 **Q24** 도 함께 보세요.

### 1.2 `__main__.py` 와 `python -m budget_app` 실행 원리

`python -m 패키지명` 으로 패키지를 실행하면, 파이썬은 그 패키지 안의 `__main__.py` 를 찾아 **스크립트처럼** 실행합니다. 이때 그 파일의 `__name__` 변수는 `"__main__"` 이 됩니다.

budget_app/__main__.py:1-8
```python
"""python -m budget_app 진입점."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
```

실행 흐름을 그림으로 그리면 다음과 같습니다.

```
$ python -m budget_app list --limit 5
        │
        ▼
budget_app/__init__.py 실행  (패키지 초기화: docstring, __version__)
        │
        ▼
budget_app/__main__.py 실행  (__name__ == "__main__" 이 참)
        │   from .cli import main
        ▼
cli.main() ── argparse 파싱 ──▶ HANDLERS[args.handler](ctx, args)
        │
        ▼
sys.exit(정수) ──▶ 셸 종료 코드로 전달 ($?, %ERRORLEVEL%)
```

설계 의도: `python budget_app/cli/app.py` 처럼 파일을 직접 실행하면 상대 임포트(`from .. import config`)가 깨집니다(패키지 문맥이 없기 때문). `python -m budget_app` 방식은 패키지 문맥을 유지한 채 실행하므로, 상대 임포트를 쓰는 이 프로젝트의 표준 실행 방법입니다.

> **⚙️ 내부 동작 — "패키지 문맥"의 정체는 `__package__` 입니다.** `-m` 옵션은 표준 라이브러리 **`runpy`** 모듈이 처리합니다. `runpy._run_module_as_main` 이 `budget_app.__main__` 을 찾아 코드 객체를 얻은 뒤, **이름만 `__main__` 인 새 네임스페이스**에서 실행합니다. 그래서 두 값이 동시에 성립합니다 — 실측:
>
>     $ python -m budget_app._probe
>     '__main__'  'budget_app'  'C:\Users\...\codyssey_B2-1'
>      __name__    __package__   sys.path[0]
>
> 상대 임포트 `from .cli import main` 은 `__name__` 이 아니라 **`__package__`** 를 기준점으로 삼아 `budget_app.cli` 를 계산합니다. 파일을 직접 실행하면 `__package__` 가 `''` 이라 기준점이 없어 `ImportError: attempted relative import with no known parent package` 가 납니다. 덤으로 `-m` 은 `sys.path[0]` 에 **현재 작업 디렉터리**를 넣지만(위 실측), 파일 직접 실행은 **그 파일이 있는 폴더**를 넣습니다. 예외 트레이스백에 `File "<frozen runpy>", line 198, in _run_module_as_main` 이 맨 위에 찍히는 것도 이 때문입니다. → [12 §1-A](./12-syntax-and-stdlib.md)

### 1.3 상대 임포트와 절대 임포트

**절대 임포트**는 최상위 패키지 이름부터 전체 경로를 적는 방식(`import budget_app.config`)이고, **상대 임포트**는 현재 모듈의 위치를 기준으로 점(`.`)을 찍는 방식입니다. `.` 하나는 "같은 패키지", `..` 두 개는 "부모 패키지"입니다.

budget_app/cli/handlers.py:22-30
```python
import argparse
from pathlib import Path

from ..context import AppContext
from ..domain import validators
from ..domain.entities import TransactionPatch
from ..domain.queries import SearchFilter
from ..errors import AppError
from . import config, messages, output, presenter, prompts
```

이 아홉 줄에 형태가 전부 들어 있습니다.

- `import argparse` / `from pathlib import Path` — **절대 임포트**. 표준 라이브러리는 언제나 이쪽입니다.
- `from . import config, messages, ...` — 같은 패키지(`cli`)의 **모듈 자체**를 가져옵니다. 이후 `config.MAX_INPUT_RETRIES` 처럼 항상 `config.` 접두어를 붙여 씁니다. "상수는 `config.X`, 문구는 `messages.X` 로 참조한다"는 프로젝트 규칙이 이 형태에서 나옵니다. 계층마다 `config`/`messages` 가 따로 있으므로 접두어가 곧 "어느 계층의 상수인가"입니다.
- `from ..domain import validators` — **부모 패키지(`budget_app`)를 거쳐** 형제 패키지의 모듈을 가져옵니다. 여기서도 모듈 자체를 받아 `validators.parse_date(...)` 로 씁니다.
- `from ..domain.queries import SearchFilter` — 모듈 안의 **특정 이름**만 가져옵니다. 자주 쓰는 클래스는 접두어 없이 짧게 쓰기 위한 선택입니다.
- `parser as parser_module`(cli/app.py:23) — **별칭(alias)** 입니다. 지역 변수 이름 `parser` 와 헷갈리지 않도록 모듈에 다른 이름을 붙였습니다.

> **🔎 문법의 출처** — `from . import X` 라는 **명시적** 상대 임포트는 PEP 328 로 파이썬 2.5 에 들어왔고, 파이썬 3.0 에서 옛날식 **암묵적** 상대 임포트(같은 폴더의 `config.py` 를 그냥 `import config` 로 집어 오던 것)가 **제거**되면서 유일한 방법이 되었습니다. 그 제거 덕분에 `import config` 는 이제 언제나 "최상위의 `config` 모듈"만 뜻하고, 표준 라이브러리와 프로젝트 모듈이 이름 하나로 충돌하는 사고가 사라졌습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

설계 의도: 프로젝트 내부 참조를 전부 상대 임포트로 통일하면, 나중에 패키지 이름이 바뀌어도 내부 코드는 한 줄도 고칠 필요가 없습니다. 반면 표준 라이브러리(`import sys`, `import csv` 등)는 절대 임포트로 씁니다.

> **import 문을 읽으면 계층이 보입니다.** `cli.py` 는 11개 모듈을 가져오지만 `errors.py` 는 하나도 가져오지 않습니다. "위 계층이 아래를 알고, 아래는 위를 모른다"가 import 목록에 그대로 드러납니다([04 §2](./04-architecture.md)).

---

## 2. `if __name__ == "__main__"` 관용구와 `sys.exit(main())`

### 2.1 관용구의 의미

모든 파이썬 모듈에는 `__name__` 이라는 변수가 자동으로 생깁니다. **직접 실행되면** `"__main__"` 이고, **import 되면** 모듈 이름(예: `"budget_app.cli"`)입니다. 그래서 `if __name__ == "__main__":` 블록은 "직접 실행될 때만 동작하는 코드"가 됩니다.

budget_app/cli/app.py:84-98
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


if __name__ == "__main__":
    sys.exit(main())
```

이 관용구 덕분에 테스트 코드나 `__main__.py` 가 `from .cli import main` 으로 **import 만 해도** 프로그램이 제멋대로 실행되지 않습니다. `app.py` 와 `__main__.py` 양쪽에 같은 블록이 있는데, 실제 진입점은 `__main__.py` 쪽이고 `app.py` 의 것은 `python budget_app/cli/app.py` 로 눌러 봤을 때를 위한 보조입니다(그 경로는 §1.2 에서 본 대로 상대 임포트가 깨집니다).

### 2.2 종료 코드가 셸로 전달되는 과정

`main()` 은 항상 **정수**를 반환하도록 설계되어 있습니다(`-> int`). 이 정수를 `sys.exit()` 에 넘기면 파이썬 프로세스가 그 값을 **종료 코드(exit code)** 로 삼아 끝나고, 셸은 이 값을 `$?`(bash) 또는 `$LASTEXITCODE`(PowerShell)로 읽을 수 있습니다.

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

| 상수 | 값 | 의미 |
|---|---|---|
| EXIT_OK | 0 | 정상 종료 |
| EXIT_ERROR | 1 | 예기치 못한 오류 |
| EXIT_VALIDATION | 2 | 입력값 검증 실패 |
| EXIT_IO | 3 | 파일 입출력 오류 |
| EXIT_APP | 4 | 애플리케이션 정의 오류(AppError) |
| EXIT_NO_CATEGORY | 5 | 등록된 카테고리 없음 |
| EXIT_ENCODING | 6 | UTF-8 이 아닌 파일 |
| EXIT_INTERRUPT | 130 | Ctrl+C 중단 (128+SIGINT 관례) |

설계 의도: 각 명령 핸들러가 정수를 반환하고, 그것이 `main()` → `sys.exit()` 를 거쳐 셸까지 전달되므로, 이 프로그램을 셸 스크립트에서 호출해 `if` 문으로 성공/실패를 분기할 수 있습니다. 예외 종류별로 어떤 코드가 반환되는지는 `error_handler.py` 의 `handle_errors` 가 결정합니다([06](./06-decorators.md)).

---

## 3. 함수 — 기본값 인자, 키워드 인자, 키워드 전용 인자, 가변 인자

### 3.1 기본값 인자 (default argument)

인자에 `= 값` 을 붙이면 호출 시 생략할 수 있고, 생략하면 기본값이 쓰입니다.

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

`date`~`amount` 는 필수, `memo` 와 `tags` 는 선택입니다. 주의할 점: `tags` 의 기본값이 `[]` 가 아니라 `None` 입니다. 파이썬에서 **기본값은 함수 정의 시점에 딱 한 번 만들어져 모든 호출이 공유**하므로, 리스트 같은 가변(mutable — 만든 뒤에도 내용을 바꿀 수 있는) 객체를 기본값으로 쓰면 호출들끼리 값이 섞이는 유명한 버그가 생깁니다. 그래서 `None` 을 기본값으로 두고, 실제 빈 리스트 변환은 `validators.parse_tags`(domain/validators.py:128-169)가 담당합니다.

> **💡 쉽게 말하면** — 기본값은 함수를 만들 때 한 번 준비해 두고 계속 돌려쓰는 물건입니다. 빈 바구니를 기본값으로 두면 손님마다 새 바구니를 내주는 게 아니라 **모두가 같은 바구니 하나**를 씁니다. 앞 손님이 담아 둔 물건이 다음 손님 바구니에 그대로 들어 있게 됩니다. `None` 을 기본값으로 두는 것은 "바구니는 미리 주지 않을 테니 필요하면 그때 새로 꺼내 쓰라"고 미루는 셈입니다.
> 다만 이 비유는 기본값이 늘 위험하다는 인상을 주는 데서 깨집니다 — 공유돼도 안전한 것, 즉 내용이 바뀔 수 없는 값(숫자, 문자열)은 기본값으로 두어도 아무 일이 없습니다. 바로 윗줄의 `memo: str = ""` 가 그대로 남아 있는 이유입니다.

> **⚙️ 내부 동작 — 기본값은 함수 객체에 붙어 있습니다.** "정의 시점에 한 번"이라는 말은 비유가 아닙니다. `def` 문이 실행될 때 기본값들이 평가되어 **함수 객체의 `__defaults__` 튜플**(키워드 전용 인자는 `__kwdefaults__` 딕셔너리)에 담기고, 호출할 때마다 그 **같은 객체**가 인자로 꽂힙니다.
>
>     :::python
>     def f(a, tags=None, memo=""): ...
>     f.__defaults__          # (None, '')   ← 실측. 호출과 무관하게 여기 살아 있다
>
> 그래서 기본값이 `[]` 였다면 모든 호출이 리스트 **하나**를 공유합니다. 반대로 `None` 은 불변 싱글턴이라 공유돼도 아무 일이 없고, 함수 본문에서 새 리스트를 만들면 호출마다 독립입니다. 파이썬이 "호출할 때마다 기본값을 다시 계산"하지 않는 이유는 그렇게 하면 `def` 가 매 호출마다 표현식을 재평가해야 하기 때문입니다. → [12 §1-A](./12-syntax-and-stdlib.md)

또 하나, 인자 이름이 `type` 이 아니라 `type_` 인 것은 내장 함수 `type()` 을 가리지 않기 위한 관례(뒤에 밑줄)입니다. 이 관례는 PEP 8 이 "이름이 예약어·내장과 충돌하면 **뒤에** 밑줄 하나를 붙인다(`class_`, `type_`)"로 명시한 것이며, `_type` 처럼 앞에 붙이는 것과는 뜻이 전혀 다릅니다 — 앞 밑줄은 "내부용"이라는 신호입니다.

### 3.2 키워드 인자 (keyword argument)

호출할 때 `이름=값` 형태로 넘기면 인자 순서를 외울 필요가 없고, 읽는 사람이 무엇이 무엇인지 바로 압니다.

budget_app/cli/handlers.py:41-48
```python
    tx = ctx.tx_service.add(
        date=entered.date,
        type_=entered.type,
        category=entered.category,
        amount=entered.amount,
        memo=entered.memo,
        tags=entered.tags,
    )
```

여섯 개 인자를 전부 이름 붙여 넘깁니다. 위치로 넘겨도 동작은 같지만, 문자열 인자가 연달아 3개라 순서를 하나만 틀려도 조용히 잘못된 데이터가 저장됩니다. 키워드 호출은 그 실수를 원천 차단합니다.

### 3.3 키워드 전용 인자 (keyword-only argument) — `*` 뒤의 인자

시그니처의 `*` **뒤에 오는 인자는 반드시 이름을 붙여서만** 넘길 수 있습니다.

budget_app/services/importexport.py:88-94
```python
    def import_csv(
        self,
        in_path: Path,
        *,
        atomic: bool = False,
        on_duplicate: str = config.DEFAULT_ON_DUPLICATE,
    ) -> ImportReport:
```

> **🔎 문법의 출처** — 이 벌거벗은 `*` 표기는 PEP 3102 로 **파이썬 3.0** 에 들어왔습니다. 그 전(파이썬 2)에는 키워드 전용 인자를 언어로 강제할 방법이 없어서, `def f(a, **kwargs):` 로 받아 본문에서 `kwargs.pop("atomic", False)` 로 꺼내고 남은 키가 있으면 직접 `TypeError` 를 던지는 수동 흉내를 냈습니다. 지금은 인터프리터가 **호출 시점에** 검사하므로 본문에 검사 코드가 한 줄도 필요 없습니다. 짝이 되는 PEP 570 의 위치 전용 표기 `/` 는 파이썬 3.8 에 들어왔지만 **이 소스에는 쓰이지 않습니다**. → [12 §1-A](./12-syntax-and-stdlib.md)

`import_csv(path, True)` 는 **문법 오류가 아니라 TypeError** 로 거부되고, 반드시 `import_csv(path, atomic=True)` 로 써야 합니다. 실제 호출부도 그렇게 되어 있습니다.

budget_app/services/importexport.py:166-177
```python
    def _commit(self, batch: _Batch, *, atomic: bool) -> ImportReport:
        """준비된 것을 파일에 반영한다 — 여기서 처음 파일이 바뀐다."""
        imported = (
            self._commit_atomic(batch) if atomic else self._commit_appending(batch)
        )
        return ImportReport(
            imported=imported,
            skipped=batch.skipped,
            duplicated=batch.duplicated,
            errors=tuple(batch.errors),
            duplicates=tuple(batch.duplicates),
        )
```

설계 의도: `atomic` 은 저장 방식 자체를 바꾸는 중요한 플래그입니다. 호출부에 `True` 만 덜렁 있으면 무슨 의미인지 알 수 없으므로, 언어 차원에서 `atomic=True` 라고 쓰도록 강제한 것입니다. 불리언 플래그 인자에 특히 권장되는 패턴입니다. 같은 기법이 여러 곳에 쓰입니다 — `export_csv(..., *, include_id=True)`, `import_csv(..., *, atomic, on_duplicate)`, `rewrite(transform, *, extra=())`.

> `TransactionRepository.append_many` 에도 같은 `atomic` 플래그가 있었지만 제거했습니다. `UnitOfWork` 가 생기면서 **원자적 커밋 수단이 둘**이 됐고, 같은 일을 하는 길이 둘이면 한쪽만 고치는 사고가 나기 때문입니다. 지금 여러 파일을 한 단위로 묶는 것은 `UnitOfWork` 하나입니다.

#### `*` 는 "바로 뒤 하나"가 아니라 "그 뒤 전부"에 적용됩니다

헷갈리기 쉬운 지점입니다. `*` 는 특정 인자를 지목하는 표시가 아니라 **"위치 인자는 여기서 끝"이라는 경계선**입니다. 따라서 그 뒤에 인자가 몇 개가 오든 **전부** 키워드 전용이 됩니다.

```python
def f(a, *, b, c=10, d=20): ...

#   a : positional or keyword
#   b : keyword-only      ← * 바로 뒤
#   c : keyword-only      ← 그 뒤도
#   d : keyword-only      ← 전부

f(1, 2, 3, 4)         # TypeError: f() takes 1 positional argument but 4 were given
f(1, b=2)             # OK — c, d 는 기본값 사용
f(1, d=4, b=2)        # OK — 키워드끼리는 순서도 자유
```

기본값이 있고 없고와도 무관합니다. 바로 위에서 본 `import_csv`(services/importexport.py:88-94)가 실제로 `*` 뒤에 인자 두 개를 두는 예입니다.

참고로 `f(1, b=2, 3)` 처럼 키워드 인자 **뒤에** 위치 인자를 쓰면 `TypeError` 가 아니라 `SyntaxError: positional argument follows keyword argument` 입니다.

### 3.4 가변 인자 `*args` / `**kwargs`

`*args` 는 위치 인자를 튜플로, `**kwargs` 는 키워드 인자를 딕셔너리로 몽땅 받습니다. "어떤 시그니처의 함수든 그대로 감싸서 통과시키는" 데코레이터의 핵심 재료입니다.

budget_app/decorators.py:37-47
```python
def log_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """함수 호출/반환을 DEBUG 로그로 남긴다."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(LOG_CALL, func.__name__)
        result = func(*args, **kwargs)
        logger.debug(LOG_DONE, func.__name__)
        return result

    return wrapper
```

`wrapper` 는 인자가 몇 개든(`*args, **kwargs` 로 받아서) 원래 함수 `func` 에 **그대로 다시 풀어**(`func(*args, **kwargs)` — 호출 위치의 `*`/`**` 는 "포장 풀기") 넘깁니다.

### 3.5 `**` 로 딕셔너리 펼치기 — 병합 관용구

호출 위치에서 `**dict` 는 "이 딕셔너리를 키워드 인자로 펼쳐라"입니다. 이 프로젝트에서 가장 인상적인 사용처는 부분 수정입니다.

budget_app/domain/entities.py:113-124
```python
    def with_patch(self, patch: TransactionPatch) -> Transaction:
        """부분 변경을 적용한 **새 Transaction** 을 만든다.
        ...
        """
        return Transaction(**{**self.to_dict(), **patch.changed_fields()})
```

한 줄에 `**` 가 세 번 나오는데 역할이 두 가지입니다.

- 안쪽의 `{**A, **B}` — **딕셔너리 병합**입니다(3.5+). A 를 펼친 뒤 B 를 펼치므로 **겹치는 키는 B 가 이깁니다**. 즉 "원래 값 위에 변경분을 덮어쓴다"가 그대로 표현됩니다.
- 바깥의 `Transaction(**{...})` — 완성된 딕셔너리를 **키워드 인자로** 펼쳐 생성자에 넘깁니다.

> **🔎 문법의 출처 / ⚙️ 무엇으로 풀리는가** — 딕셔너리 **리터럴 안**의 `**` 는 PEP 448("추가 언패킹 일반화")로 **파이썬 3.5** 에 들어왔습니다. 그 전에는 `d = dict(A); d.update(B)` 로 두 줄을 쓰거나 `dict(A, **B)` 를 썼는데, 후자는 키가 문자열이어야 하고 파이썬 2 에서만 관용적이었습니다. 파이썬은 `{**A, **B}` 를 사실상 "빈 dict 를 만들고 A 를 `update`, 이어서 B 를 `update`"로 실행합니다(바이트코드로는 `BUILD_MAP` + `DICT_UPDATE` 두 번) — **"뒤에 온 것이 이긴다"가 곧 `update` 의 의미**입니다.
>
> 헷갈리기 쉬운 이웃 문법이 하나 더 있습니다. `A | B`(딕셔너리 합집합 연산자)는 PEP 584 로 **3.9** 에 들어온 별개 문법입니다. 이 소스는 그쪽을 쓰지 않습니다 — `{**A, **B}` 는 두 개를 넘겨도 세 개를 넘겨도 같은 모양이고, 곧바로 `Transaction(**...)` 로 이어 쓸 수 있기 때문입니다. → [12 §1-A](./12-syntax-and-stdlib.md)

`self.to_dict()` 가 새 딕셔너리를 만들어 주므로 원본은 건드리지 않습니다. 이 한 줄이 "수정은 새 객체를 만드는 일"이라는 설계를 코드로 보여 줍니다.

---

## 4. 문자열 — 메서드 실사용례와 3가지 포맷 방식

### 4.1 strip / lower / split / join

**strip + lower** — 입력 정규화의 기본입니다. 앞뒤 공백을 지우고 소문자로 통일합니다.

budget_app/domain/validators.py:73-77
```python
def parse_type(value: Any) -> str:
    v = str(value or "").strip().lower()
    if v not in config.VALID_TYPES:
        raise ValidationError(messages.ERR_TYPE_INVALID.format(types=config.VALID_TYPES))
    return v
```

사용자가 `" Income "` 이라고 입력해도 `"income"` 으로 정규화(들쭉날쭉하게 들어온 입력을 한 가지 모양으로 맞추는 것)되어 통과합니다. 메서드 호출을 점으로 이어붙이는 **메서드 체이닝**도 눈여겨보세요 — 각 메서드가 새 문자열을 반환하므로 이어서 부를 수 있습니다.

> **⚙️ 내부 동작 — 문자열은 불변이라 체이닝이 "새 객체 릴레이"입니다.** `str` 은 불변(immutable)이므로 `strip()`·`lower()` 는 원본을 고치지 못하고 **새 `str` 객체**를 만들어 돌려줍니다. 그래서 `a.strip().lower()` 는 중간 객체를 하나 만들어 버리는 셈입니다. 다만 CPython 은 `strip()` 에서 **깎을 것이 없으면 원본 객체를 그대로 되돌려줍니다**(실측: `'income'.strip() is 'income'` → `True`). `lower()` 는 이미 소문자여도 새 객체를 만듭니다(`False`). 짧은 사용자 입력에서는 어느 쪽이든 비용이 무시할 수준이지만, 루프에서 `s = s + x` 를 반복하면 매번 전체 복사가 일어난다는 점은 같은 불변성의 다른 얼굴입니다 — 이 소스가 태그를 이어 붙일 때 `"...".join(...)` 을 쓰는 이유입니다. → [12 §1-A](./12-syntax-and-stdlib.md)

**split + join** — 문자열 ↔ 리스트 변환의 짝입니다. 태그는 저장할 땐 리스트, CSV 로 내보낼 땐 쉼표 문자열입니다.

budget_app/domain/validators.py:128-158 (split — 쉼표 문자열을 리스트로)
```python
def parse_tags(value: Any) -> list[str]:
    """리스트 또는 쉼표 구분 문자열을 태그 리스트로 정규화한다.
    ...
    """
    if value is None:
        return []
    if isinstance(value, str):
        items: Iterable[Any] = value.split(config.TAG_SEPARATOR)
    elif isinstance(value, Iterable):
        items = value
    else:
        items = [value]

    seen: list[str] = []
```

budget_app/storage/csv_io.py:151-159 (join — 리스트를 쉼표 문자열로)
```python
def _to_row(tx: Transaction, include_id: bool) -> dict[str, object]:
    row: dict[str, object] = {
        "date": tx.date,
        "type": tx.type,
        "category": tx.category,
        "amount": tx.amount,
        "memo": tx.memo,
        "tags": domain_config.TAG_SEPARATOR.join(tx.tags),
    }
```

`join` 은 구분자 문자열의 메서드라는 점이 처음엔 낯섭니다. `", ".join(리스트)` 는 "리스트 원소들을 `', '` 로 이어 붙여라"입니다. 카테고리 안내 메시지에서도 쓰입니다.

budget_app/cli/prompts.py:106
```python
            + messages.FMT_AVAILABLE_SUFFIX.format(available=", ".join(cat_service.list_names()))
```

> **`startswith` 는 어디로 갔나요?** 리팩터(겉으로 하는 일은 그대로 두고 코드 구조만 다시 짜는 작업) 전에는 월별 집계가 `tx.date.startswith(target + "-")` 로 "이 달의 거래인가"를 판정했습니다. 지금은 `SearchFilter.for_month` 가 `calendar` 로 계산한 실제 말일 범위와 비교합니다(domain/queries.py:74-78). 문자열 접두 비교가 틀린 것은 아니었지만, **내보내기는 범위 비교, 요약은 접두 비교**로 같은 개념이 두 알고리즘으로 구현돼 있었던 것이 문제였습니다([04 §5](./04-architecture.md)).

### 4.2 왜 포맷 방식이 3가지나 쓰였는가

이 코드에는 f-string, `str.format`, %-스타일이 **전부** 등장합니다. 중구난방이 아니라, **포맷이 실행되는 "시점"이 달라서** 각각 적합한 자리가 다릅니다.

> **💡 쉽게 말하면** — 셋의 차이는 **빈칸을 언제 채우느냐**입니다. f-string 은 그 자리에서 바로 손으로 써 넣는 것이고, `str.format` 은 빈칸이 뚫린 서식 용지를 미리 만들어 두었다가 값이 생긴 곳에서 채우는 것입니다. 세 번째가 미뤄지는 것은 `%` 스타일이 특별해서가 아니라 **logging 에 용지와 채울 값을 따로 건네주기 때문**입니다 — 받아 둔 쪽이 **그 서류를 실제로 제출하기로 결정했을 때만** 채우고, 제출하지 않기로 하면 채우는 수고 자체가 없습니다.
> 다만 이 비유는 f-string 이 굼뜬 방식이라는 인상을 주는 데서 깨집니다 — 셋 중 f-string 이 가장 빠릅니다(아래 ⚙️ 상자). 문제는 속도가 아니라 **미리 만들어 보관해 둘 수 없다**는 점입니다. 그리고 `"%s" % x` 를 이렇게 logging 을 거치지 않고 직접 쓰면 f-string 과 똑같이 그 자리에서 바로 채워집니다 — 미뤄 주는 것은 `%` 기호가 아니라 logging 쪽입니다.

> **🔎 문법의 출처 — 셋은 20년에 걸쳐 하나씩 쌓인 지층입니다.**
>
> | 방식 | 출처 | 정체 |
> |---|---|---|
> | `"%s" % x` | 파이썬 1.x 부터. C 의 `printf` 서식을 그대로 가져온 것 | **`str.__mod__` 연산자.** `"a %s" % x` 는 `str.__mod__("a %s", x)` 호출입니다 |
> | `"{}".format(x)` | PEP 3101, **파이썬 2.6/3.0** | **`str` 의 메서드.** 안쪽 `{...}` 는 `string.Formatter` 문법이고 값마다 `__format__` 을 부릅니다 |
> | `f"{x}"` | PEP 498, **파이썬 3.6** | **문법(리터럴)**. 메서드도 연산자도 아니라 컴파일 시점에 코드로 펼쳐집니다 |
>
> 셋이 남아 있는 이유는 하위 호환입니다. 파이썬은 오래된 문법을 잘 지우지 않습니다. 그러니 "옛날 것이 나쁘다"가 아니라 **각자 살아남은 이유가 있다**는 관점으로 읽어야 하고, 이 소스가 정확히 그렇게 나눠 씁니다. → [12 §1-A](./12-syntax-and-stdlib.md)

**(1) f-string — 값이 지금 이 자리에 있을 때.** f-string 은 문자열이 평가되는 **그 순간** 변수를 채워 넣습니다.

budget_app/domain/periods.py:20-30
```python
def month_range(month: str) -> tuple[str, str]:
    """``'YYYY-MM'`` → ``('YYYY-MM-01', 'YYYY-MM-<그 달의 말일>')``.

    모든 달을 31일로 가정하면 2월·30일 달에서 범위가 어긋난다. ``calendar`` 로
    실제 말일을 구한다. 검색·요약·내보내기가 모두 이 함수 하나를 쓰므로
    "이 달에 속하는가"의 정의가 프로그램 전체에서 하나다.
    """
    normalized = validators.parse_month(month)
    dt = datetime.strptime(normalized, config.MONTH_FORMAT)
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return f"{normalized}-01", f"{normalized}-{last_day:02d}"
```

`{last_day:02d}` 는 정수를 두 자리로 0 채움(`5` → `"05"`)합니다. `normalized` 와 `last_day` 가 바로 위 줄에 있으므로 f-string 이 가장 자연스럽습니다.

> **⚙️ 내부 동작 — f-string 은 "런타임 문자열 조립"이 아닙니다.** `f"{normalized}-{last_day:02d}"` 는 실행 중에 중괄호를 **파싱하지 않습니다.** 컴파일러가 소스를 읽을 때 이미 조각으로 쪼개어, `format(last_day, "02d")` 를 부르고 결과들을 이어 붙이는 바이트코드로 펼쳐 둡니다(로컬 3.13.1 에서 `dis` 로 확인: `FORMAT_SIMPLE` → `FORMAT_WITH_SPEC` → `BUILD_STRING`. 명령어 이름은 버전마다 다릅니다). `str.format` 이 호출될 때마다 템플릿 문자열을 훑어 `{`/`}` 를 찾아내는 것과 결정적으로 다르며, f-string 이 빠른 이유가 이것입니다.
>
> 반대급부가 이 절의 주제입니다 — **컴파일 시점에 이름이 확정되므로 템플릿으로 보관할 수 없습니다.** 그래서 `messages.py` 는 f-string 을 쓸 수 없습니다. 참고로 f-string 의 문법 규정이 파서에 정식 편입된 것은 PEP 701(파이썬 3.12)이고, 그 전에는 중괄호 안에 같은 종류의 따옴표를 넣을 수 없는 등의 제약이 있었습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

**(2) str.format — 템플릿을 만들어 두고 나중에 채울 때.** messages.py 의 메시지들은 정의 시점에 채울 값이 없습니다.

budget_app/cli/messages.py:48
```python
MSG_SAVED_TX = "[저장 완료] id={id}"
```

budget_app/cli/handlers.py:49
```python
    output.out(messages.MSG_SAVED_TX.format(id=tx.id))
```

여기에 f-string 을 쓸 수 없는 이유: f-string 은 **정의되는 그 줄에서 즉시** 변수를 찾습니다. messages.py 가 로드되는 시점에는 `tx` 라는 변수가 존재하지 않으므로 `f"[저장 완료] id={tx.id}"` 는 NameError 가 됩니다. "빈칸 뚫린 템플릿을 상수로 보관 → 실제 값이 생긴 곳에서 `.format()` 으로 채움"이라는 **지연 치환**에는 `str.format` 이 정답입니다.

ID 생성 템플릿도 같은 방식입니다.

budget_app/domain/config.py:26
```python
TX_ID_FORMAT = "TX-{:06d}"
```

budget_app/storage/ids.py:105-116
```python
    def next(self) -> TransactionId:
        """아직 쓰이지 않은 다음 번호를 발급한다.

        ``while`` 인 이유: CSV 가 큰 번호를 먼저 실어 오면 ``reserve`` 가 카운터를
        끌어올리지만, 순서가 뒤죽박죽이면 이미 점유된 번호에 부딪칠 수 있다.
        """
        while True:
            self._counter += 1
            candidate = TransactionId.of(self._counter)
            if candidate not in self._taken:
                self._taken.add(candidate)
                return candidate
```

`{:06d}` 는 "정수를 6자리, 빈자리는 0"이므로 `1` → `"TX-000001"` 이 됩니다.

**(3) %-스타일 — logging 의 지연 포맷.** 로그 메시지 템플릿만은 옛날식 `%s`/`%d` 를 씁니다.

budget_app/decorators.py:27-32
```python

#: 이 세 문구는 이 모듈만 쓴다. 별도 messages 파일로 빼면 3줄짜리 파일이 생기고
#: 오히려 찾기 어려워진다. %-스타일인 이유는 logging 의 지연 포맷팅 때문이다.
LOG_CALL = "call %s"
LOG_DONE = "done %s"
LOG_TOOK = "%s took %.2fms"
```

budget_app/storage/jsonl.py:203
```python
                logger.warning(messages.LOG_CORRUPT_LINE, self.path.name, raw.lineno, raw.error)
```

`logger.warning(템플릿, 인자1, 인자2, ...)` 형태에 주목하세요. 템플릿과 인자를 **따로** 넘기면, logging 모듈은 **이 로그가 실제로 출력될 때만** `%` 치환을 수행합니다. 로그 레벨이 꺼져 있으면 문자열 조합 비용이 아예 발생하지 않습니다. 만약 `logger.debug(f"call {func.__name__}")` 처럼 f-string 을 쓰면 로그가 버려지는 경우에도 문자열을 만들어 놓고 버리는 낭비가 생깁니다.

> **⚙️ 내부 동작 — 치환이 미뤄지는 지점이 정확히 어디인가.** `logger.debug(msg, *args)` 는 세 단계를 거칩니다.
>
> 1. **`self.isEnabledFor(DEBUG)`** — 레벨이 안 맞으면 **여기서 즉시 반환**합니다. 인자는 손도 대지 않습니다.
> 2. 통과하면 `LogRecord` 객체를 만드는데, 이때도 합치지 않고 `record.msg = "call %s"`, `record.args = ("add",)` 로 **따로 보관**합니다.
> 3. 핸들러가 포매터를 통해 `record.getMessage()` 를 부르는 순간, 그 안에서 `msg % self.args` 가 실행됩니다 — 여기가 진짜 치환 지점입니다.
>
>     :::python
>     r = logging.LogRecord("x", 20, "p", 1, "call %s", ("add",), None)
>     r.msg, r.args        # ('call %s', ('add',))   ← 아직 문자열이 아니다
>     r.getMessage()       # 'call add'              ← 이때 합쳐진다   (실측)
>
> f-string 은 1번보다 **먼저** 실행되므로 이 사다리 전체를 건너뛰게 만듭니다. `decorators.py` 의 `LOG_CALL = "call %s"` 가 `%` 스타일인 것은 취향이 아니라 이 구조에 맞춘 것입니다. logging 만 `%` 를 고수하는 이유는 `logging` 이 파이썬 2.3 시절 모듈이라 `str.format` 보다 먼저 태어났고, 지금 바꾸면 전 세계의 기존 호출이 깨지기 때문입니다. → [12 §2-B](./12-syntax-and-stdlib.md)

정리하면:

| 방식 | 치환 시점 | 이 프로젝트에서의 자리 |
|---|---|---|
| f-string | 그 줄이 실행되는 즉시 | 값이 바로 옆에 있는 곳 (domain/periods.py:30, storage/backup.py:29) |
| str.format | 템플릿 보관 후 호출 시 | messages.py 의 사용자 메시지 템플릿 전부 |
| %-스타일 | logging 이 출력할 때만 | messages.py 의 LOG_* + logger.debug/warning 호출 |

### 4.3 콜론 뒤의 암호 — 포맷 스펙 미니 언어

f-string 과 `str.format` 은 중괄호 안을 **세 부분**으로 읽습니다.

```
{ 이름 !변환 :스펙 }
   │    │     └── 포맷 스펙 미니 언어 — 값의 __format__ 에 그대로 넘어간다
   │    └── 변환(conversion) — !r=repr(), !s=str(), !a=ascii()
   └── 무엇을 채울지 (이름, 번호, 또는 생략)
```

이 구분이 중요한 이유는 **부르는 메서드가 다르기 때문**입니다.

| 표기 | 실제로 호출되는 것 |
|---|---|
| `{x}` | `format(x, "")` → `type(x).__format__(x, "")`. `object.__format__` 의 기본 구현이 `str(x)` 이므로 대개 `__str__` 과 같아 보일 뿐입니다 |
| `{x:06d}` | `format(x, "06d")` → `int.__format__` |
| `{x!r}` | **먼저** `repr(x)` 를 부르고, 그 결과 문자열을 포맷합니다 — `__format__` 은 건너뜁니다 |
| `{x!s}` | 먼저 `str(x)` 를 부릅니다 |

`__format__` 을 직접 정의한 클래스에 넣어 보면 차이가 눈에 보입니다(일반론 예시 — 이 소스에는 `__format__` 정의가 없습니다).

```python
class C:
    def __str__(self): return "STR"
    def __repr__(self): return "REPR"
    def __format__(self, spec): return f"FMT<{spec}>"

f"{C()}"        # 'FMT<>'      ← __format__(spec="")
f"{C():>10}"    # 'FMT<>10>'   ← 스펙 문자열이 통째로 전달된다
f"{C()!r}"      # 'REPR'       ← __format__ 을 안 부른다
f"{C()!s}"      # 'STR'
```

스펙 자체는 `[[채움]정렬][부호][#][0][너비][,][.정밀도][타입]` 순서인데, 이 소스에 실제로 쓰인 것은 넷뿐입니다.

| 소스의 표기 | 위치 | 뜻 | 결과 |
|---|---|---|---|
| `{:06d}` | domain/config.py:26 `TX_ID_FORMAT` | 너비 6, 빈자리 `0`, 십진 정수 | `7` → `"000007"` → `"TX-000007"` |
| `{last_day:02d}` | domain/periods.py:30 | 너비 2, 0 채움 | `5` → `"05"` |
| `{type:<7}` | cli/messages.py:43 `FMT_TX_LINE` | 왼쪽 정렬, 너비 7 | `"income"` → `"income "` (표의 열 맞춤) |
| `{self.value!r}` | domain/specs.py:182 등 `__repr__` | repr 변환 | `"2024-01"` → `'2024-01'` (따옴표 포함) |

읽는 요령이 두 가지 있습니다.

- **`0` 은 채움 문자가 아니라 축약입니다.** `{:06d}` 의 `0` 은 `{:0>6d}`(채움 문자 `0`, 오른쪽 정렬)의 줄임입니다. 그래서 `{:<7}` 처럼 정렬 기호를 직접 쓸 때와 문법 위치가 다릅니다.
- **정렬 기본값이 타입마다 다릅니다.** 숫자는 오른쪽 정렬, 문자열은 왼쪽 정렬이 기본입니다. `{type:<7}` 의 `<` 는 그래서 사실 생략해도 같은 결과지만, "이건 표의 열이다"라는 의도를 명시적으로 남긴 것입니다.
- **너비는 표시 폭이 아니라 문자 개수입니다.** `{:<7}` 은 한글처럼 터미널에서 두 칸을 먹는 글자에서는 열이 어긋납니다. 이 자리의 값이 `income`/`expense` 라는 ASCII 두 종류뿐이라 문제가 없는 것이고, 카테고리 열에는 폭 지정이 없는 이유도 여기 있습니다.

`{!r}` 이 `__repr__` 을 부른다는 사실이 `domain/specs.py` 에서 실질적으로 쓰입니다. `f"DateFrom({self.value!r})"` 은 `DateFrom('2024-01-01')` 처럼 **따옴표까지 살아 있는** 문자열을 만들어, 명세 조합을 디버거에서 그대로 읽을 수 있게 합니다(자세한 것은 [10. 고급 설계](./10-advanced-design.md) 의 명세 패턴).

---

## 5. 자료구조 — list / dict / tuple / set 과 컴프리헨션

### 5.1 네 가지 기본 자료구조의 실사용례

**tuple — 바뀌면 안 되는 상수 목록.**

budget_app/storage/config.py:13-14
```python
# 부트스트랩
DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "etc")
```

리스트가 아니라 튜플인 이유: 튜플은 불변(immutable — 만든 뒤에는 내용을 바꿀 수 없는)이라 어디선가 실수로 `append` 할 수 없습니다. "허용 타입 목록"처럼 프로그램 내내 고정인 값에 적합합니다. 같은 이유로 `ImportReport.errors` 도 `tuple[RejectedRow, ...]` 입니다(domain/results.py:96) — **결과 보고서는 만들어진 뒤 바뀌면 안 되기 때문**입니다.

**list — 순서 있는 수집.** 정렬 전 거래를 모으는 버퍼로 쓰입니다.

budget_app/services/transactions.py:79-87
```python
    def stream_sorted(self, flt: SearchFilter | None = None) -> Iterator[Transaction]:
        """최신순 정렬된 거래를 yield 한다.

        주의: 정렬을 위해 한 번은 전체를 읽어야 한다(파일이 정렬되어 있지 않으므로).
        그러나 메모리 사용량은 '필터 통과 항목'으로 제한된다.
        """
        items = [tx for tx in self.txs.stream() if flt is None or flt.matches(tx)]
        items.sort(key=lambda t: (t.date, t.id), reverse=True)
        yield from items
```

**dict — 이름표가 달린 값 묶음.** 카테고리별 합계 누적이 대표적입니다.

budget_app/services/budgets.py:46-54
```python
        for tx in self.txs.stream():
            if not flt.matches(tx):
                continue
            has_data = True
            if tx.type == domain_config.TYPE_INCOME:
                income_total += tx.amount
            else:
                expense_total += tx.amount
                per_category[tx.category] = per_category.get(tx.category, 0) + tx.amount
```

> 리팩터 전에는 "수정할 필드"도 `Dict[str, object]` 였습니다. 지금은 `TransactionPatch` dataclass 입니다. **"이름표가 자유로워도 되는 데이터"에는 dict 가 맞지만, "이름표가 정해져 있는 데이터"에는 dataclass 가 맞습니다** — 후자에 dict 를 쓰면 오타가 조용히 무시됩니다([05 §4](./05-config-and-models.md)).

**set — 중복 없는 집합, 빠른 소속 검사.**

budget_app/storage/repositories.py:240-242
```python
    def name_set(self) -> set[str]:
        """존재 확인을 반복할 때 쓰는 스냅숏 — 매번 파일을 훑지 않기 위해."""
        return {c.name for c in self.stream()}
```

`name in known` 검사가 리스트라면 매번 전체를 훑지만(선형 탐색), set 은 해시(값을 정해진 길이의 숫자로 바꿔 보관 자리를 곧바로 계산해 내는 방법)로 즉시 판정합니다. `IdAllocator._taken`(storage/ids.py:94-95)도 같은 이유로 set 입니다 — 발급할 때마다 "이 번호가 이미 쓰였나"를 물어야 하기 때문입니다.

> **⚙️ 내부 동작 — `in` 이 set 에서 빠른 진짜 이유.** `x in some_set` 은 `set.__contains__` 를 부르고, 그 안에서 `hash(x)` 로 버킷 위치를 곧바로 계산합니다. 훑지 않으므로 원소가 100 개든 10만 개든 평균 비용이 같습니다(평균 O(1)). 대가는 **원소가 해시 가능해야 한다**는 조건입니다. 그래서 `_taken` 에 담기는 `TransactionId` 가 `@dataclass(frozen=True)` 여야 합니다 — `frozen=True` 가 `__hash__` 를 자동 생성해 주기 때문이고, 보통의 dataclass(`frozen=False`)는 `__hash__` 가 `None` 으로 막혀 `set` 에 넣는 순간 `TypeError: unhashable type` 이 납니다. "불변으로 만든 것"과 "집합에 넣을 수 있는 것"이 이 소스에서는 같은 결정입니다. → [12 §1-B](./12-syntax-and-stdlib.md)

### 5.2 컴프리헨션 3종 — 실제 코드로

> **💡 쉽게 말하면** — 컴프리헨션은 **줄 세 개짜리 반복문을 한 줄로 접어 둔 표기**입니다. "빈 상자를 하나 놓는다 → 원소를 하나씩 꺼내 본다 → 조건에 맞으면 상자에 넣는다"를 매번 세 줄로 쓰는 대신, "무엇을 / 어디서 / 어떤 조건으로"만 한 줄에 적습니다.
> 다만 접어 둔 것일 뿐, 펴 놓은 for 문과 똑같지는 않습니다 — 컴프리헨션 안에서 쓴 이름(`c` 같은 것)은 밖으로 새어 나오지 않고, 같은 이름의 바깥 변수를 덮어쓰지도 않습니다. for 문은 둘 다 합니다(아래 ⚙️ 상자에서 실측과 함께 다룹니다).
> 비유가 깨지는 자리가 하나 더 있습니다 — 괄호 종류입니다. 소괄호로 감싸면 상자에 담지 않고 **필요할 때마다 하나씩 꺼내 주는 것**(제너레이터 식)이 되어, 결과가 어디에도 쌓이지 않습니다. §6.2 는 바로 그 차이 덕분에 파일 읽기를 도중에 멈춥니다.

> **🔎 문법의 출처 — 세 컴프리헨션은 따로따로 들어왔습니다.** 리스트 컴프리헨션이 PEP 202 로 **파이썬 2.0** 에 먼저 들어왔고(하스켈에서 빌려온 표기입니다), 딕셔너리 컴프리헨션은 PEP 274 로 제안되어 **2.7/3.0** 에서 구현되었으며, 집합 컴프리헨션도 같은 시기에 함께 들어왔습니다. 그래서 이 셋은 "한 문법의 세 변형"이 아니라 **10년에 걸쳐 모양만 맞춰 온 세 기능**입니다. 괄호 종류가 셋을 가르고, 소괄호는 리스트가 아니라 **제너레이터 식**(PEP 289, 파이썬 2.4)이라는 것이 자주 걸리는 함정입니다 — §6.2 의 `any(c.name == target for c in ...)` 가 바로 그 소괄호입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

**리스트 컴프리헨션** — "리스트를 만드는 for 문"을 한 줄로 씁니다. `[식 for 원소 in 반복대상 if 조건]`.

budget_app/storage/repositories.py:238
```python
        return [c.name for c in self.stream()]
```

`Category` 객체 스트림에서 이름만 뽑아 리스트로 만듭니다. `[식 for 원소 in 반복대상]` 이 for 문 세 줄을 한 줄로 줄인 것입니다.

> **⚙️ 내부 동작 — 컴프리헨션은 자기만의 스코프를 가집니다.** 파이썬 3 에서 컴프리헨션의 루프 변수 `c` 는 **바깥으로 새어 나오지 않습니다.** 원래는 컴프리헨션마다 이름 없는 함수를 하나 만들어 그 안에서 돌리는 방식으로 구현했기 때문이고(그래서 스코프가 생겼습니다), 파이썬 3.12 의 PEP 709 부터는 함수를 만들지 않고 인라인하면서도 **스코프 격리는 그대로 유지**합니다.
>
>     :::python
>     x = "outer"
>     r = [x for x in range(3)]
>     x                      # 'outer'  ← 실측. 파이썬 2 였다면 2 로 덮어써졌습니다
>
> 실무적 의미는 이렇습니다 — `repositories.py` 의 `[c.name for c in self.stream()]` 이 같은 메서드 안의 다른 `c` 를 건드릴 걱정이 없고, 그래서 짧은 한 글자 변수를 마음 놓고 쓸 수 있습니다. 다만 예외가 하나 있습니다: 가장 바깥쪽 반복 대상(`self.stream()` 부분)은 **바깥 스코프에서 즉시 평가**됩니다. → [12 §1-C](./12-syntax-and-stdlib.md)

조건을 붙이면 걸러 낼 수도 있습니다.

budget_app/services/transactions.py:85
```python
        items = [tx for tx in self.txs.stream() if flt is None or flt.matches(tx)]
```

`if` 절이 뒤에 붙어 "통과한 것만" 남깁니다. 이 한 줄이 `list`/`search` 의 메모리 사용량을 **필터를 통과한 건수**로 제한합니다 — 파일 전체가 아니라.

**딕셔너리 컴프리헨션** — `{키식: 값식 for ... if ...}`. 변경된 필드만 골라낼 때 씁니다.

budget_app/domain/entities.py:144-151
```python
    def changed_fields(self) -> dict[str, Any]:
        """``None`` 이 아닌 필드만 골라 dict 로 준다."""
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if getattr(self, f.name) is not None
        }

```

`fields(self)` 는 `dataclasses.fields` 로 이 dataclass 의 필드 목록을 돌려주고, `getattr(self, 이름)` 으로 값을 꺼냅니다. **필드를 하나씩 나열하지 않아도 되므로, 나중에 `TransactionPatch` 에 필드를 추가해도 이 함수는 고칠 필요가 없습니다.**

**set 컴프리헨션** — `{식 for ... }`. 위 §5.1 의 `name_set()` 이 그 예입니다.

가져오기에서는 두 자료구조를 나란히 씁니다.

budget_app/services/importexport.py:126-129
```python
            batch.transactions.append(parsed.to_transaction(tx_id))
            if parsed.category not in known_categories:
                known_categories.add(parsed.category)
                batch.new_categories.append(parsed.category)
```

`known_categories`(set)는 "중복 없는 빠른 소속 검사"용, `new_categories`(list)는 "등록 **순서** 유지"용 — 같은 데이터를 두 자료구조로 이중 관리하는 이유가 각각 다르다는 점이 학습 포인트입니다.

### 5.3 `dict.get(key, 0)` 누적 패턴

없는 키를 대괄호로 읽으면(`d[k]`) KeyError 가 나지만, `d.get(k, 기본값)` 은 기본값을 돌려줍니다. 위 §5.1 의 `per_category.get(tx.category, 0) + tx.amount` 가 그 패턴입니다. 처음 보는 카테고리면 `get` 이 0 을 돌려주므로 `0 + 금액` 으로 시작하고, 이후에는 기존 합계에 더해집니다.

(일반론: `collections.defaultdict(int)` 로도 같은 일을 할 수 있지만, 이 코드는 표준 dict 만으로 해결해 자료구조를 단순하게 유지했습니다.)

---

## 6. 반복과 내장 함수

### 6.1 `enumerate(반복대상, start=N)` — 번호를 함께 세기

`enumerate` 는 반복하면서 (번호, 원소) 튜플을 내놓습니다. `start` 로 시작 번호를 정할 수 있습니다.

budget_app/storage/jsonl.py:162-179
```python
    def iter_raw(self) -> Iterator[RawLine]:
        """모든 줄을 원문과 함께 yield 한다 — 어떤 줄도 버리지 않는다.
        ...
        """
        if not self.path.exists():
            return
        with open(self.path, encoding=config.FILE_ENCODING, errors=config.FILE_ERRORS) as f:
            for lineno, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line:
                    continue
                yield self._parse_line(lineno, line)
```

파일 객체 `f` 를 for 문에 넣으면 **한 줄씩** 나옵니다. `start=1` 로 사람이 세는 방식(1행부터)의 줄 번호를 얻어, 손상된 줄 경고 로그에 씁니다.

> **🔎 문법의 출처 / ⚙️ 내부 동작** — `enumerate` 는 PEP 279 로 **파이썬 2.3** 에 추가되었고, `start` 인자는 **2.6** 에 뒤늦게 붙었습니다. 그 전에는 `for i in range(len(items)):` 로 인덱스를 만들어 `items[i]` 로 되짚는 코드가 흔했는데, 그 방식은 **인덱싱이 되는 대상에만** 통합니다. 여기서 중요한 것이 그 차이입니다 — `f`(파일 객체)는 `len()` 도 `f[3]` 도 되지 않는 순수 반복자이므로 `range(len(...))` 방식이 아예 불가능합니다. `enumerate` 는 게으른 반복자를 감싸 `(번호, 원소)` 튜플을 하나씩 만들어 내므로, **파일 전체를 메모리에 올리지 않고도** 줄 번호를 셀 수 있습니다. 이 소스의 스트리밍 설계가 성립하는 조건입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

CSV 가져오기에서는 시작 번호가 2 입니다 — 1행은 헤더가 차지하므로 데이터는 2행부터이기 때문입니다. 그 숫자마저 상수로 뽑혀 있습니다.

budget_app/storage/csv_io.py:87
```python
        yield from enumerate(reader, start=config.CSV_DATA_START_LINE)
```

`yield from` 은 "이 반복을 통째로 위임한다"는 뜻입니다([§11.5](#115-yield-from--반복을-통째로-위임)). `for` 로 받아 그대로 `yield` 하던 것을 한 줄로 줄인 것이고, ruff 의 `UP028` 이 지적해 준 자리입니다.

지출 TOP N 출력에서는 순위 표시용으로 씁니다. `(category, amount)` 부분은 튜플 안의 튜플을 한 번에 푸는 **중첩 언패킹**(묶음으로 온 값을 그 자리에서 여러 변수로 풀어 받는 것)입니다.

budget_app/cli/presenter.py:76-78
```python
        yield messages.MSG_TOP_EXPENSE_HEADER.format(n=len(summary.top_expense))
        for rank, (category, amount) in enumerate(summary.top_expense, start=1):
            yield messages.FMT_TOP_EXPENSE_ITEM.format(rank=rank, category=category, amount=amount)
```

### 6.2 `any()` — 하나라도 참이면 True

budget_app/storage/repositories.py:244-246
```python
    def exists(self, name: str) -> bool:
        target = validators.parse_category(name)
        return any(c.name == target for c in self.stream())
```

괄호 안은 제너레이터 식(결과를 미리 다 만들어 두지 않고, 요구가 있을 때 하나씩 내주는 표기)으로, `any` 는 참인 원소를 **처음 만나는 순간 즉시** True 를 반환하고 반복을 멈춥니다. 파일 앞쪽에서 카테고리를 찾으면 나머지는 읽지 않으므로, for 문 + 플래그 변수보다 짧고 효율적입니다.

> **⚙️ 내부 동작 — "단축 평가"가 여기서는 파일 읽기를 멈춘다는 뜻입니다.** `any(...)` 의 실제 구현은 `for element in iterable: if element: return True` 와 같습니다(`all` 은 거짓을 만나면 `return False`). 두 함수 모두 인자를 **반복자로만** 다루므로, 소괄호 제너레이터 식과 짝을 이루면 원소가 **필요한 만큼만** 만들어집니다.
>
> 그 연쇄가 여기서는 디스크까지 닿습니다. `self.stream()` 은 `iter_raw()` → `open(...)` 의 줄 반복자에 얹혀 있는 제너레이터라, `any` 가 `return True` 로 빠져나가면 제너레이터가 그 자리에서 멈추고 with 블록이 정리되며 **파일이 닫힙니다.** 만약 대괄호를 써서 `any([c.name == target for c in self.stream()])` 이라고 적었다면 리스트를 먼저 다 만들어야 하므로 파일 전체를 항상 끝까지 읽습니다. **괄호 하나가 I/O 량을 바꿉니다.** → [12 §1-C](./12-syntax-and-stdlib.md)

budget_app/storage/repositories.py:121-124
```python
    def category_in_use(self, name: str) -> bool:
        """저장된 카테고리는 정규형이므로 **묻는 쪽도 정규화**해야 판정이 맞는다."""
        target = validators.parse_category(name)
        return any(tx.category == target for tx in self.stream())
```

### 6.3 `sorted(key=lambda, reverse=True)` 와 슬라이싱

budget_app/services/budgets.py:56-58
```python
        top_expense = tuple(
            sorted(per_category.items(), key=lambda kv: kv[1], reverse=True)[: max(0, top_n)]
        )
```

네 가지가 한 줄에 결합되어 있습니다.

- `per_category.items()` 는 `("food", 50000)` 같은 (카테고리, 금액) 튜플들입니다.
- `key=lambda kv: kv[1]` — 정렬 기준을 "튜플의 두 번째 값(금액)"으로 지정합니다. `lambda` 는 이름 없는 한 줄짜리 함수입니다. `reverse=True` 로 큰 금액부터 내림차순.
- `[: max(0, top_n)]` — 앞에서 N 개만 자르는 **슬라이싱**입니다. `max(0, ...)` 방어가 중요합니다: 사용자가 `--top -3` 처럼 음수를 넣으면 `[:-3]` 은 "뒤 3개 제외"라는 전혀 다른 의미가 되는데, `max(0, -3)` → `[:0]` → 빈 리스트로 만들어 그 오동작을 차단합니다.
- 바깥의 `tuple(...)` — 결과를 불변 튜플로 굳힙니다. `MonthlySummary` 가 `frozen=True` dataclass 라 담기는 값도 불변인 편이 일관됩니다.

참고로 `items.sort(key=lambda t: (t.date, t.id), reverse=True)`(services/transactions.py:86)는 **튜플을 key 로** 써서 "날짜가 같으면 id 로" 2차 정렬하는 기법입니다(튜플은 앞 원소부터 차례로 비교됨).

> **⚙️ 내부 동작 — `key` 는 원소당 딱 한 번만 계산됩니다.** `sorted`/`list.sort` 는 비교할 때마다 `key` 를 부르지 않습니다. 먼저 전체를 훑어 키 값 배열을 만들어 두고(그래서 호출 횟수는 정확히 **n 회**), 그다음부터는 키끼리만 비교합니다. `lambda t: (t.date, t.id)` 처럼 튜플을 새로 만드는 key 함수를 마음 놓고 쓸 수 있는 이유입니다.
>
> 두 가지가 더 따라옵니다. 첫째, 파이썬의 정렬은 **Timsort** 로 **안정 정렬(stable)** 입니다 — 키가 같은 원소들의 원래 순서가 보존됩니다. 둘째, `reverse=True` 는 "정렬한 뒤 뒤집기"가 아니라 비교 방향을 뒤집는 것이라 **안정성이 그대로 유지**됩니다. 그래서 `(t.date, t.id)` 튜플 키 하나로 "날짜 내림차순, 같으면 id 내림차순"이 흔들림 없이 결정되고, 같은 목록을 두 번 뽑아도 순서가 늘 같습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

### 6.4 `max()` 의 두 가지 얼굴

같은 내장 함수가 두 자리에서 다르게 쓰입니다.

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

여기서 `max(a, b)` 는 "둘 중 큰 것"입니다. `max(0, top_n)` 도 같은 형태인데, 하나는 **누적 갱신**(가장 큰 값 추적)이고 다른 하나는 **하한 고정**(0 아래로 못 내려가게)입니다. 인자를 두 개 주는 형태와 반복 가능 객체를 하나 주는 형태(`max([1,2,3])`)를 구분해서 읽으세요.

### 6.5 `zip` 은 왜 안 쓰였나

이 프로젝트에는 `zip` 이 한 번도 등장하지 않습니다. `zip` 은 "두 개 이상의 시퀀스를 나란히 묶을 때" 필요한데, 이 코드의 반복은 전부 (1) 단일 스트림 순회, (2) 번호가 필요하면 `enumerate`, (3) 키-값 쌍이 필요하면 `dict.items()` 로 해결됩니다. 즉 "안 쓴 것"도 설계입니다 — 필요 없는 도구를 억지로 쓰지 않았다는 뜻입니다.

---

## 7. 예외 처리 기초

예외 처리의 전체 설계는 [03. 파이썬 중·고급 기법](./03-python-advanced.md)과 [06](./06-decorators.md)에서 깊게 다룹니다. 계층, `raise ... from`, `handle_errors` 데코레이터가 거기 있습니다. 여기서는 문법 기초만 짚습니다.

> **💡 쉽게 말하면** — 예외는 일하다 막혔을 때 **위로 올려 보내는 신호**입니다. 창구 직원이 자기 권한으로 처리할 수 없는 서류를 만나면, 대충 넘기지 않고 손을 들어 상급자에게 올립니다. 아무도 받아 주지 않으면 신호는 계속 위로 올라가고, 맨 위까지 가면 프로그램이 멈춥니다. `try` / `except` 는 "이 종류의 신호는 내가 받겠다"고 미리 손을 들어 두는 것입니다.
> 다만 이 비유는 신호가 곧 사고라는 인상을 주는 데서 깨집니다 — 이 프로그램에서 `ValidationError` 는 사고가 아니라 **예정된 대답**입니다. §7.3 의 재입력 안내처럼, 신호를 올리는 것 자체가 정상 동작인 자리가 있습니다.

### 7.1 try / except — 튜플로 여러 예외를 한 번에 잡기

`except (A, B) as exc:` 처럼 괄호(튜플)로 묶으면 여러 종류의 예외를 같은 블록에서 처리합니다.

budget_app/domain/validators.py:40-70
```python
def parse_amount(value: Any) -> int:
    """금액을 양의 정수로 검증·정규화한다.
    ...
    """
    text = str(value).strip()
    if not _INTEGER.match(text):
        raise ValidationError(messages.ERR_AMOUNT_NOT_INT)
    n = int(text)
    if n <= 0:
        raise ValidationError(messages.ERR_AMOUNT_NOT_POSITIVE)
    return n
```

`int("abc")` 는 ValueError, `int(None)` 은 TypeError — 원인은 달라도 사용자에게는 똑같이 "금액은 정수여야 합니다"이므로 함께 잡습니다.

**예외 튜플을 상수로 뽑는 기법**도 있습니다. 저장 파일의 한 줄을 도메인 객체로 세울 때 날 수 있는 예외들이 여러 개라, 이름과 주석을 붙여 한곳에 모았습니다.

budget_app/storage/jsonl.py:37-40
```python
# 한 줄을 도메인 객체로 세우다 실패할 수 있는 경우들.
# JSONDecodeError: JSON 이 아님 / KeyError: 필수 키 없음 / ValidationError: 규칙 위반
# TypeError: JSON 은 맞지만 객체가 아님(예: 최상위가 리스트)
_LINE_ERRORS = (json.JSONDecodeError, ValidationError, KeyError, TypeError)
```

budget_app/storage/jsonl.py:181-191
```python
    def _parse_line(self, lineno: int, line: str) -> RawLine:
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            return RawLine(lineno=lineno, text=line, error=str(exc))
        try:
            entity = self.entity_cls.from_dict(data)
        except _LINE_ERRORS as exc:
            data_dict = data if isinstance(data, dict) else None
            return RawLine(lineno=lineno, text=line, data=data_dict, error=str(exc))
        return RawLine(lineno=lineno, text=line, data=data, entity=entity)
```

`try` 를 **두 단계로 나눈 것**이 핵심입니다. JSON 파싱까지만 성공한 줄은 `data` 를 갖고, 도메인 검증까지 성공한 줄은 `entity` 도 갖습니다. 이 구분 덕분에 "검증에 실패했지만 id 는 읽을 수 있는 줄"을 ID 발급이 인식할 수 있습니다([07](./07-repository.md)).

### 7.2 finally — 무슨 일이 있어도 실행되는 블록

budget_app/decorators.py:50-66
```python
def measure_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """함수 실행 시간을 DEBUG 로그로 남긴다.

    ``try/finally`` 인 이유: 예외로 빠져나가는 경로에서도 시간이 찍혀야 "느려서
    타임아웃이 났다"와 "즉시 터졌다"를 구분할 수 있다.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(LOG_TOOK, func.__name__, elapsed)

    return wrapper
```

`finally` 블록은 `try` 에서 **return 을 하든 예외가 나든** 반드시 실행됩니다.

### 7.3 raise — 예외 던지기

`raise 예외클래스(메시지)` 로 예외를 발생시킵니다. 이 프로젝트는 상황 설명과 해결 힌트를 함께 담아 던집니다.

budget_app/cli/prompts.py:60-74
```python
def ask_until(prompt: str, validator: Callable[[str], T]) -> T:
    """``validator(raw)`` 가 정상값을 반환할 때까지 재입력을 요구한다.

    - EOF → ``InputAborted`` 로 즉시 종료(무한 루프 방지).
    - 유효하지 않은 값이 계속 들어오면 ``MAX_INPUT_RETRIES`` 회에서 중단한다.
    """
    for _ in range(config.MAX_INPUT_RETRIES):
        raw = ask(prompt)
        try:
            return validator(raw)
        except ValidationError as exc:
            # 재입력 안내는 결과가 아니라 진단이므로 stderr 로 보낸다.
            output.err(messages.MSG_ERROR_LINE.format(msg=exc))
            output.err(messages.MSG_HINT_RETRY)
    raise AppError(messages.ERR_MAX_RETRIES, hint=messages.HINT_MAX_RETRIES)
```

`for` 루프가 끝까지 돌면(= 재입력이 계속 실패하면) 마지막 줄의 `raise` 에 도달합니다. `AppError` 는 이 프로젝트가 직접 정의한 예외 클래스(errors.py:41-51)이며, `raise ... from exc`(원인 예외 연결)와 함께 [03](./03-python-advanced.md)에서 자세히 설명합니다.

> **🔎 문법의 출처** — `except (A, B) as exc:` 에서 `as` 표기는 파이썬 3.0 이 옛 `except A, exc:` 를 대체하며 유일한 형태로 굳힌 것입니다(2.6 부터 병용 가능). 옛 문법은 `except (A, B), exc` 와 `except A, B` 가 눈으로 구별되지 않는 함정이 있었습니다. 여기 나오는 `raise ... from exc`(PEP 3134, 파이썬 3.0)와 예외 그룹 `except*`(PEP 654, 파이썬 3.11)도 같은 계보인데, **`except*` 는 이 소스에 쓰이지 않습니다** — 동시에 여러 예외가 날 병렬 작업이 없기 때문입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

---

## 8. 파일 입출력 — open 모드, encoding, newline, with 문

### 8.1 open 의 세 가지 모드가 모두 쓰인다

| 모드 | 의미 | 이 프로젝트의 사용처 |
|---|---|---|
| `"r"` (기본) | 읽기 | storage/jsonl.py:174 — JSONL 스트리밍 읽기 |
| `"w"` | 새로 쓰기 (기존 내용 삭제) | storage/jsonl.py:61 — 임시 파일 전체 쓰기 |
| `"a"` | 끝에 이어 쓰기 (append) | storage/jsonl.py:234 — 엔티티 이어 쓰기 |
| `"rb"` | 바이너리 읽기 | storage/jsonl.py:258 — 마지막 바이트가 개행인지 확인 |

budget_app/storage/jsonl.py:210-212
```python
    def append(self, entity: T) -> None:
        self._append_lines([self._encode(entity)])

```

`"a"` 모드는 파일 끝에만 붙이므로 기존 데이터를 건드리지 않습니다 — "추가만 하는" JSONL 저장 방식과 정확히 맞아떨어집니다. 반면 update/delete 처럼 전체를 다시 써야 할 때는 `"w"` 로 임시 파일에 쓴 뒤 교체합니다.

budget_app/storage/jsonl.py:48-72
```python
def stage_lines(path: Path, lines: Iterable[str]) -> Path:
    """임시 파일에 전부 쓰고 디스크에 내린 뒤, 그 임시 경로를 돌려준다.
    ...
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + config.TMP_SUFFIX)
    with open(
        tmp,
        "w",
        encoding=config.FILE_ENCODING,
        errors=config.FILE_ERRORS,
        newline=config.LINE_TERMINATOR,
    ) as f:
        for line in lines:
            f.write(line + config.LINE_TERMINATOR)
        f.flush()
        os.fsync(f.fileno())
    return tmp
```

**쓰기가 두 단계로 나뉜 것**은 여러 파일을 함께 커밋(준비해 둔 변경을 되돌릴 수 없게 확정하는 것)하기 위해서입니다 — 여러 파일의 tmp 를 **전부 만들어 둔 뒤** 마지막에 이름 교체만 몰아서 하면, 중간에 실패해도 원본이 하나도 바뀌지 않습니다(`UnitOfWork` — [07 §9](./07-repository.md)).
`stage_lines` 가 tmp 작성 + `fsync` 까지, `commit_staged` 가 `os.replace` 만 담당하고,
파일 하나만 바꾸는 경로는 `atomic_write_lines`(storage/jsonl.py:80-87)가 둘을 연달아 부릅니다.
이 이름에 **밑줄이 없는 것은 의도적**입니다 — 소스의 docstring 이 직접 설명하듯, `ids.IdWatermark` 처럼 JSONL 이 아닌 파일을 다루는 쪽도 이 함수를 쓰기 때문에 "저장소 계층의 공용 도구"라는 표시입니다.

`f.flush()` 와 `os.fsync(f.fileno())` 가 새로 들어간 부분입니다. `flush` 는 파이썬 버퍼(디스크로 바로 보내지 않고 잠시 모아 두는 임시 보관소)를 OS 에 넘기고, `fsync` 는 OS 버퍼를 물리 디스크에 내리라고 요구합니다. `f.fileno()` 는 파일 객체에서 **OS 수준 파일 디스크립터(정수)** 를 꺼내는 메서드입니다.

> **💡 쉽게 말하면** — 편지로 치면 세 단계입니다. 다 썼다(`write`) / 봉투에 넣어 현관에 내놓았다(`flush`) / 집배원이 실제로 가져갔다(`fsync`). 정전은 현관에 놓인 편지를 태웁니다 — 분명히 다 썼는데도 남지 않습니다. `fsync` 까지 마쳐야 "이건 확실히 갔다"고 말할 수 있고, 이 코드가 임시 파일을 쓴 직후에 굳이 `fsync` 를 부르는 이유가 그것입니다.
> 다만 이 비유는 `fsync` 를 완결로 보이게 하는 데서 깨집니다 — `fsync` 가 하는 일은 **OS 에게 내리라고 요구하는 데까지**이고, 디스크 장치가 자기 캐시에 들고 있으면서 다 됐다고 답하는 경우까지 막아 주지는 못합니다.

> **⚙️ 내부 동작 — `open()` 하나가 사실 객체 세 개입니다.** 내장 `open` 은 `io.open` 과 같은 함수이고, 텍스트 모드에서 **3층 구조**를 조립해 돌려줍니다. 로컬에서 확인하면 이렇습니다.
>
>     :::python
>     f = open(path, encoding="utf-8")
>     type(f)          # _io.TextIOWrapper   ← 인코딩 + 줄바꿈 변환 담당
>     type(f.buffer)   # _io.BufferedReader  ← 파이썬 쪽 버퍼 (flush 가 비우는 대상)
>     type(f.buffer.raw)  # _io.FileIO       ← OS 파일 디스크립터를 쥔 맨 아래층
>
> 이 그림이 있어야 `flush` 와 `fsync` 의 분업이 이해됩니다. `f.flush()` 는 가운데 `BufferedReader/Writer` 층의 내용을 아래로 밀어 **OS 에 넘기는 데까지**입니다. 거기서 끝나면 데이터는 아직 OS 의 페이지 캐시에 있고, 전원이 끊기면 사라집니다. `os.fsync(f.fileno())` 는 맨 아래 `FileIO` 가 쥔 정수 디스크립터를 꺼내 **OS 에게 물리 디스크까지 내리라고 시스템 콜을 부르는 것**입니다. `errors=` 와 `newline=` 은 맨 위 `TextIOWrapper` 의 옵션이라 `"rb"` 같은 바이너리 모드에는 아예 존재하지 않습니다 — `_has_torn_tail` 이 `"rb"` 로 여는 순간 인코딩·줄바꿈 이야기가 사라지는 이유입니다. → [12 §3](./12-syntax-and-stdlib.md)

### 8.2 `encoding="utf-8"` 을 항상 명시하는 이유

`open` 의 인코딩 기본값은 OS 와 설정에 따라 다릅니다(특히 Windows 는 흔히 cp949). 명시하지 않으면 "내 컴퓨터에서는 되는데 다른 컴퓨터에서 한글이 깨지는" 문제가 생깁니다.

> **⚙️ 내부 동작 — 기본값의 정체는 `locale.getencoding()` 입니다.** `encoding` 을 생략하면 `TextIOWrapper` 가 `locale.getencoding()` 을 불러 그 결과를 씁니다. 이 문서를 쓰는 개발 환경에서 실제로 확인하면 **`cp949`** 가 나옵니다 — 즉 `open(path)` 한 줄이 이 컴퓨터에서는 조용히 "cp949 로 읽어라"가 됩니다. 같은 코드가 리눅스/macOS 에서는 `utf-8` 이 되므로, **소스는 한 글자도 다르지 않은데 결과가 다릅니다.**
>
> 파이썬도 이것을 함정으로 인정해서, PEP 597 로 **파이썬 3.10** 부터 `EncodingWarning` 을 도입했습니다. `python -X warn_default_encoding` 으로 실행하면 인코딩을 생략한 `open` 마다 경고가 찍힙니다(실측: `EncodingWarning: 'encoding' argument not specified`). 이 프로젝트가 모든 `open` 에 `encoding=` 을 붙여 둔 것은 그 경고를 미리 통과한 상태라는 뜻입니다. → [12 §3](./12-syntax-and-stdlib.md)

이 프로젝트의 **모든** `open` 호출은 인코딩을 명시하며, 값 자체도 상수입니다.

budget_app/storage/config.py:22-22
```python
FILE_ENCODING = "utf-8"
```

UTF-8 이 아닌 파일을 읽으면 UnicodeDecodeError 가 나고, `handle_errors` 가 이를 잡아 "엑셀에서 CSV UTF-8 로 다시 저장하라"는 힌트(cli/messages.py:115-116)를 보여줍니다.

한 가지 예외가 있는데, 그것도 상수로 설명되어 있습니다. JSONL 파일은 `errors="surrogateescape"`(storage/config.py:25)로 엽니다.

> **🔎 문법의 출처 / ⚙️ 내부 동작** — `errors="surrogateescape"` 는 PEP 383 으로 **파이썬 3.1** 에 들어온 오류 처리기입니다. 디코딩할 수 없는 바이트를 예외로 터뜨리는 대신 유니코드의 **대리 영역(U+DC80~U+DCFF)** 문자로 바꿔 담아 두고, 같은 처리기로 인코딩할 때 **원래 바이트를 그대로 복원**합니다. 즉 손상된 바이트가 왕복해도 한 비트도 변하지 않습니다.
>
> 이 소스가 이것을 고른 이유는 저장 정책과 맞물립니다 — JSONL 재작성은 "손상된 줄은 해석하지 않고 원문 그대로 보존한다"인데, 기본값인 `errors="strict"` 였다면 읽는 순간 `UnicodeDecodeError` 로 터져 **보존할 기회 자체가 없습니다.** 읽기와 쓰기가 같은 처리기를 쓰기 때문에 무손실 왕복이 성립합니다. → [12 §3](./12-syntax-and-stdlib.md)

### 8.3 `newline` 인자 — 두 가지 값이 쓰이는 이유

텍스트 모드의 파이썬은 기본적으로 줄바꿈을 OS 방식으로 자동 변환합니다(Windows 에서 `"\n"` 을 쓰면 실제 파일엔 `"\r\n"`). 이 프로젝트는 목적에 따라 두 값을 구분해 씁니다.

- **JSONL 쓰기: `newline="\n"`** (storage/jsonl.py:61, 234) — 자동 변환을 끄고 항상 LF 로 고정합니다. Windows 에서 만든 데이터 파일과 리눅스에서 만든 파일이 바이트 단위로 같아져, 어느 OS 에서든 동일하게 읽힙니다.
- **CSV 읽고 쓰기: `newline=""`** (storage/csv_io.py:82, 142) — csv 모듈 공식 문서가 요구하는 값입니다. 줄바꿈 처리를 csv 모듈에 완전히 맡긴다는 뜻으로, 이를 빼면 Windows 에서 `\r\r\n` 이 생겨 한 줄 걸러 빈 줄이 들어가는 유명한 버그가 납니다.

> **⚙️ 내부 동작 — 세 값이 실제로 무엇을 바꾸는가.** `newline` 은 맨 위 `TextIOWrapper` 층의 옵션이며, 쓰기와 읽기에서 하는 일이 다릅니다.
>
> | `newline` | 쓸 때 | 읽을 때 |
> |---|---|---|
> | `None` (기본) | 코드의 `"\n"` 을 **`os.linesep` 으로 치환** (Windows 면 `"\r\n"`) | `\r\n`, `\r`, `\n` 을 전부 `"\n"` 으로 통일해서 준다 (유니버설 개행) |
> | `""` | 치환하지 **않는다** | 통일하지 않고 원문 그대로 주되, 줄 나누기는 세 종류 모두 인정한다 |
> | `"\n"` | 치환하지 **않는다** | `"\n"` 만 줄 끝으로 인정한다 |
>
> Windows 에서 직접 확인한 결과입니다.
>
>     :::python
>     Path("a.txt").write_text("a\nb\n", encoding="utf-8")            # newline 기본값
>     Path("a.txt").read_bytes()      # b'a\r\nb\r\n'   ← \n 이 \r\n 으로 부풀었다
>
>     with open("b.txt", "w", encoding="utf-8", newline="\n") as f:
>         f.write("a\nb\n")
>     Path("b.txt").read_bytes()      # b'a\nb\n'       ← 코드 그대로
>
> 이것이 왜 데이터 파일에서 중요하냐면, JSONL 은 **줄이 곧 레코드**라서 줄 끝 바이트가 파일 포맷의 일부이기 때문입니다. 기본값으로 두면 같은 프로그램이 만든 파일이 OS 마다 바이트가 달라지고, `_has_torn_tail` 처럼 **마지막 바이트를 직접 검사하는 코드**(storage/jsonl.py:249-262)가 플랫폼마다 다른 답을 내게 됩니다. `newline=config.LINE_TERMINATOR` 는 그 변수를 아예 없애는 선택입니다. → [12 §3](./12-syntax-and-stdlib.md)

budget_app/storage/csv_io.py:141-148
```python
    count = 0
    with open(path, "w", encoding=config.CSV_ENCODING, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tx in txs:
            writer.writerow(_to_row(tx, include_id))
            count += 1
    return count
```

### 8.4 with 문(컨텍스트 매니저)이 보장하는 것

`with open(...) as f:` 블록은 블록을 **어떤 이유로 빠져나가든**(정상 종료, return, 예외) 파일을 자동으로 닫아 줍니다. `f.close()` 를 직접 부르는 방식은 중간에 예외가 나면 닫기가 건너뛰어지지만, with 문은 언어 차원에서 닫기를 보장합니다.

> **🔎 문법의 출처 / ⚙️ 무엇으로 풀리는가** — `with` 문은 PEP 343 으로 **파이썬 2.5** 에 들어왔고, 하는 일은 **`try/finally` 를 문법으로 굳힌 것**입니다. 파이썬은 `with A() as f:` 를 대략 이렇게 실행합니다.
>
>     :::python
>     mgr = open(...)
>     f = type(mgr).__enter__(mgr)          # as 뒤 변수에 담기는 것은 __enter__ 의 반환값
>     try:
>         ...본문...
>     except BaseException:
>         if not type(mgr).__exit__(mgr, *sys.exc_info()):
>             raise                          # __exit__ 이 True 를 돌려주면 예외가 삼켜진다
>     else:
>         type(mgr).__exit__(mgr, None, None, None)
>
> 핵심 세 가지입니다. (1) `as f` 에 담기는 것은 `open(...)` 객체가 아니라 **`__enter__` 의 반환값**입니다(파일 객체는 자기 자신을 돌려주므로 같아 보일 뿐입니다). (2) `__exit__` 은 예외 정보 3개를 인자로 받으므로, **왜 빠져나왔는지 알고** 다르게 행동할 수 있습니다. (3) `__exit__` 이 참 같은 값을 반환하면 예외가 **삼켜집니다**.
>
> (2)와 (3)이 왜 중요한지가 이 프로젝트에서 그대로 드러납니다. `UnitOfWork.__exit__`(storage/unit_of_work.py:172-181)는 첫 인자 `exc_type` 이 `None` 인지 보고 커밋과 롤백을 갈라 부릅니다 — (2)를 그대로 쓴 것입니다. 그리고 반환 타입이 `-> None` 입니다. `None` 은 거짓이므로 **롤백한 뒤 예외를 그대로 위로 올려 보냅니다** — 실패를 조용히 삼키지 않겠다는 결정이 "아무것도 반환하지 않는다"에 들어 있습니다. 여기서 실수로 `return True` 를 적으면 저장 실패가 성공처럼 보이게 됩니다. `open` 을 넘어선 `with` 의 활용은 [03](./03-python-advanced.md) 과 [07](./07-repository.md) 에서 이어집니다. → [12 §1-C](./12-syntax-and-stdlib.md)

특히 쓰기 파일은 닫혀야 버퍼가 디스크로 완전히 내려가므로, `stage_lines` 가 `return tmp` 를 with 블록 **바깥**에서 하는 순서가 중요합니다. 블록을 빠져나온 뒤에야 파일이 닫히고, 그다음에 `commit_staged` 가 `os.replace` 를 부릅니다.

---

## 9. pathlib.Path — 객체지향 경로 다루기

`pathlib.Path` 는 경로를 문자열이 아닌 객체로 다루는 표준 라이브러리입니다. 이 프로젝트의 경로 조작은 전부 Path 로 통일되어 있습니다.

> **💡 쉽게 말하면** — 경로를 문자열로 다루는 것은 주소를 **글자 뭉치**로 다루는 것이고, `Path` 는 주소를 **주소로** 다루는 것입니다. 글자 뭉치일 때는 앞뒤에 빗금이 하나인지 둘인지를 사람이 매번 신경 써야 합니다. 주소로 다루면 "상위 폴더가 어디냐", "파일 이름만 떼어 달라" 같은 요청을 그 자리에서 할 수 있습니다.
> 다만 이 비유는 `Path` 가 그 자리에 실제로 파일이 있다는 뜻이라는 오해를 부르는 데서 깨집니다 — `Path` 는 **주소를 적어 둔 쪽지**일 뿐이라, 그 자리에 파일이 있는지는 `exists()` 로 따로 물어봐야 합니다.

### 9.1 `/` 연산자 — 경로 이어 붙이기

budget_app/storage/repositories.py:33-34
```python
    def __init__(self, data_dir: Path) -> None:
        super().__init__(Path(data_dir) / self.FILE_NAME)
```

> **🔎 문법의 출처 / ⚙️ `/` 의 정체** — `pathlib` 은 PEP 428 로 **파이썬 3.4** 에 표준 라이브러리가 되었습니다. 그 전에는 `os.path.join`·`os.path.dirname` 같은 **문자열을 받아 문자열을 돌려주는 함수 묶음**만 있었습니다.
>
> 여기서 `/` 는 새로 만든 문법이 아닙니다. `Path` 가 **`__truediv__` 라는 특수 메서드를 정의한 것**뿐입니다 — 즉 `Path("data") / "x"` 는 `Path.__truediv__(Path("data"), "x")` 이고, 파이썬이 `a / b` 를 `type(a).__truediv__(a, b)` 로 옮기는 규칙을 그대로 탄 것입니다. (`__truediv__` 라는 이름은 PEP 238 에서 파이썬 3 의 `/` 가 "참 나눗셈"으로 바뀌면서 붙은 것이고, 경로와는 아무 상관이 없습니다.) 왼쪽이 문자열이어도 되도록 `__rtruediv__` 도 함께 정의돼 있어 `"data" / Path("x")` 까지 동작합니다.
>
> 연산자 오버로딩이라는 같은 장치를 이 소스도 직접 씁니다 — `domain/specs.py` 의 `Spec.__and__`/`__or__`/`__invert__`(specs.py:84-91)가 `&`, `|`, `~` 를 명세 조합으로 바꿉니다. 즉 `/` 를 이해하면 그 코드도 같은 원리로 읽힙니다. → [12 §1-B](./12-syntax-and-stdlib.md)

`Path("./data") / "transactions.jsonl"` 은 OS 에 맞는 구분자로 경로를 이어 줍니다. 그런데 "OS 구분자"는 사실 **부차적인 이유**입니다 — Windows API 도 `/` 를 받아들이므로 문자열 덧셈으로도 대개 동작합니다. 진짜 이유는 넷입니다.

#### ① 구분자 개수를 호출자가 책임지지 않아도 됨

`--data-dir` 는 사용자 입력이라 끝에 구분자가 있을 수도, 없을 수도 있습니다.

| `--data-dir` 입력 | `base + "/" + FN` | `Path(base) / FN` |
|---|---|---|
| `"./data"` | `./data/transactions.jsonl` | `data\transactions.jsonl` |
| `"data/"` | `data//transactions.jsonl` ← 중복 | `data\transactions.jsonl` |
| `"data//"` | `data///transactions.jsonl` ← 3중 | `data\transactions.jsonl` |

`//` 는 대부분의 OS 가 관대하게 처리하지만, **경로를 문자열로 비교하는 순간 깨집니다.** `"data//x" != "data/x"` 인데 가리키는 파일은 같습니다. 이 코드는 원본 경로와 `.tmp` 경로를 함께 다루므로 그런 비교가 언제든 생길 수 있습니다.

#### ② 빈 문자열이 절대 경로로 바뀜 — 가장 위험

```python
base = ""
base + "/" + "transactions.jsonl"   # → '/transactions.jsonl'  ← 파일시스템 루트!
str(Path(base) / "transactions.jsonl")  # → 'transactions.jsonl'   ← 현재 폴더
```

`--data-dir ""` 를 주면 문자열 덧셈은 데이터를 **드라이브 루트**(`C:\transactions.jsonl`)에 씁니다. 예외도 나지 않고 조용히 엉뚱한 곳에 쓰는 유형이라 발견이 늦습니다.

#### ③ 타입이 실수를 막음

`Path` 는 `+` 를 **아예 정의하지 않습니다.**

```python
Path("data") + "/x.jsonl"
# TypeError: unsupported operand type(s) for +: 'WindowsPath' and 'str'
```

습관적으로 문자열 덧셈을 쓰면 그 자리에서 죽습니다. 문자열 변수였다면 조용히 통과했을 실수입니다.

절대 경로 처리도 `os.path.join` 과 같은 규칙(이어붙이기가 아니라 **교체**)을 따릅니다.

```python
Path("data") / "/etc/passwd"    # → '\etc\passwd'       올바름
"data" + "/" + "/etc/passwd"    # → 'data//etc/passwd'  존재하지 않는 경로
```

`--data-dir /var/lib/budget` 처럼 절대 경로를 주는 정상 사용에서 이 규칙이 필요합니다.

#### ④ 후속 연산이 전부 따라옴 — 이 코드에서 실제로 쓰는 이유

가장 실질적인 이유입니다. 경로를 만든 **뒤에** 하는 일들이 `Path` 에 이미 들어 있습니다.

```python
p = Path(data_dir) / "transactions.jsonl"

p.parent                          # ensure_ready 의 mkdir 대상      (storage/jsonl.py:152)
p.name                            # 백업의 dest / p.name            (storage/backup.py:32)
p.with_suffix(p.suffix + ".tmp")  # stage_lines 의 임시 파일 이름    (storage/jsonl.py:60)
```

문자열이었다면 `os.path.dirname`·`os.path.basename` 을 따로 import 해 써야 하고, 확장자 붙이기는 직접 문자열을 조작해야 합니다. `with_suffix` 가 특히 그런데, `"transactions.jsonl" + ".tmp"` 는 우연히 맞지만 이름에 점이 여럿이면 "확장자가 어디부터인가"가 모호해집니다.

### 9.2 `mkdir(parents=True, exist_ok=True)` — 폴더 준비

budget_app/storage/jsonl.py:150-154
```python
    def ensure_ready(self) -> None:
        """파일이 없으면 만든다 — 명시적으로 호출될 때만 디스크를 건드린다."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()
```

- `path.parent` — 파일의 부모 폴더 (`data/transactions.jsonl` → `data`).
- `parents=True` — 중간 폴더까지 전부 생성 (`a/b/c` 를 한 번에).
- `exist_ok=True` — 이미 있어도 오류를 내지 않음.
- `touch()` — 빈 파일 생성.

이 조합은 "폴더가 있든 없든 이 줄 이후에는 반드시 존재한다"를 보장하는 관용구입니다. 반대로 백업 폴더는 `exist_ok=False`(storage/backup.py:30)입니다 — 타임스탬프 폴더가 이미 있다면 같은 초에 백업이 두 번 실행된 비정상 상황이므로 **일부러 오류를 내는** 선택입니다.

### 9.3 `stat().st_size` — 파일 크기로 빈 파일 판정

budget_app/storage/jsonl.py:156-158
```python
    @property
    def is_empty(self) -> bool:
        return not self.path.exists() or self.path.stat().st_size == 0
```

`stat()` 은 파일 메타데이터를 돌려주고 `st_size` 가 바이트 크기입니다. 파일 내용을 읽지 않고 0 바이트인지만 보므로, "카테고리 파일이 비어 있으면 기본 카테고리를 심는다"는 판정을 가장 싸게 합니다. `not self.path.exists() or ...` 순서에 주의하세요 — 파일이 없으면 `stat()` 이 예외를 내므로, **단락 평가로 앞에서 막습니다**(§11.1). 단락 평가란 앞쪽만으로 답이 정해지면 뒤쪽은 아예 실행하지 않는 규칙입니다.

### 9.4 `with_suffix` — 확장자 조작

`tmp = path.with_suffix(path.suffix + config.TMP_SUFFIX)`(storage/jsonl.py:60)는 `transactions.jsonl` → `transactions.jsonl.tmp` 를 만듭니다. `path.suffix` 는 현재 확장자(`".jsonl"`)이고, 거기에 `".tmp"` 를 이어 새 확장자로 교체합니다. 문자열 조작 없이 임시 파일 이름을 안전하게 만드는 방법입니다.

> **⚙️ 내부 동작 — `with_suffix` 는 붙이는 게 아니라 "갈아 끼우는" 메서드입니다.** 이름이 `add_suffix` 가 아닌 데는 이유가 있습니다. `with_suffix(s)` 는 **마지막 확장자를 s 로 대체**합니다. 그래서 `path.suffix + ".tmp"` 라는 한 겹이 반드시 필요합니다 — 실측으로 비교하면 이렇습니다.
>
>     :::python
>     p = Path("a.b.jsonl")
>     p.suffix                          # '.jsonl'      ← 마지막 하나만
>     p.with_suffix(".tmp")             # a.b.tmp       ← .jsonl 이 사라졌다! (틀린 사용)
>     p.with_suffix(p.suffix + ".tmp")  # a.b.jsonl.tmp ← 소스의 방식 (원본 이름이 살아 있다)
>
> 왼쪽 방식으로 썼다면 `transactions.jsonl` 의 임시 파일이 `transactions.tmp` 가 되는데, 이름이 다르면 `os.replace` 로 되돌아갈 원본을 짐작할 수 없고, 실패로 남은 찌꺼기가 어느 파일의 것인지도 알 수 없습니다. `.jsonl.tmp` 라는 이름은 **"이건 transactions.jsonl 을 쓰다 만 것"** 이라는 정보를 파일 이름에 남기는 선택이며, 동시에 `*.jsonl` 글롭에 걸리지 않아 백업 대상에서 자동으로 빠집니다(storage/backup.py:36-47). → [12 §2-B](./12-syntax-and-stdlib.md)

### 9.5 `glob` / `read_bytes` / `write_bytes` — 백업 함수에 총집합

budget_app/storage/backup.py:17-33
```python
def backup_data_dir(data_dir: Path, now: datetime | None = None) -> Path:
    """data 폴더의 모든 ``*.jsonl`` 을 타임스탬프 폴더로 복사한다.
    ...
    """
    src = Path(data_dir)
    if not src.exists():
        raise FileNotFoundError(str(src))
    ts = (now or datetime.now()).strftime(config.BACKUP_TS_FORMAT)
    dest = src.parent / f"{config.BACKUP_DIR_PREFIX}{ts}"
    dest.mkdir(parents=True, exist_ok=False)
    for p in _files_to_copy(src):
        (dest / p.name).write_bytes(p.read_bytes())
    return dest
```

- `src.glob("*.jsonl")` — 패턴에 맞는 파일들을 순회합니다. 데이터 폴더에 다른 파일이 섞여 있어도 `.jsonl` 만 백업됩니다.
- `p.read_bytes()` / `write_bytes(...)` — 파일 전체를 **바이트 그대로** 읽고 씁니다. 백업은 내용 해석이 아니라 복제가 목적이므로, 텍스트 모드(인코딩/줄바꿈 변환)를 거치지 않는 바이너리 복사가 정확합니다.
- `p.name` — 경로에서 파일 이름만 (`data/transactions.jsonl` → `transactions.jsonl`).
- `now: Optional[datetime] = None` — **의존성 주입**(필요한 것을 안에서 직접 만들지 않고 밖에서 받아 쓰는 방식)의 가장 작은 형태입니다. 기본은 현재 시각이지만, 테스트에서 시각을 넘기면 결과 폴더 이름을 예측할 수 있습니다.

이 17줄 함수 하나에 `exists`, `/` 연산자, `mkdir`, `glob`, `read_bytes`/`write_bytes`, `name` 이 모두 등장하므로, pathlib 복습용으로 통째로 읽어 보기를 권합니다.

---

## 10. 타입 힌트 기초

> **💡 쉽게 말하면** — 타입 힌트는 설계도 위에 적어 둔 **치수 표기**입니다. "이 자리에는 숫자가 들어옵니다", "여기서는 글자가 나갑니다" 하고 도면에 써 두는 것이라, 읽는 사람과 편집기가 그 표기를 보고 일합니다.
> 다만 이 비유는 **가장 중요한 곳에서 깨집니다** — 건축이라면 감리가 치수를 재고 어긋나면 공사를 세우지만, 파이썬은 실행 중에 **아무도 재지 않습니다.** 힌트와 전혀 다른 값이 들어와도 프로그램은 그냥 굴러갑니다(§10.3). 그래서 이 프로젝트는 힌트와 별개로 실행 시점 검사를 따로 두었습니다.

### 10.1 인자와 반환 타입 표기

`def f(x: int) -> str:` 처럼 인자 뒤에는 `: 타입`, 반환은 `-> 타입` 으로 적습니다. 기본 자료형 이름만으로는 적을 수 없는 타입 — 함수나 반복자 같은 것 — 은 `typing`, 그리고 이 소스에서는 `collections.abc` 에서 가져옵니다. 다만 예전에 `typing` 에서 가져오던 것 중 일부는 이제 기본 자료형으로 대체할 수 있고, 일부는 그럴 수 없습니다. 그 구분은 §10.2 에서 다룹니다.

> **🔎 문법의 출처 — 표기 자리와 의미가 따로 들어왔습니다.** `def f(x: int) -> str:` 이라는 **자리**는 PEP 3107(파이썬 3.0)이 "함수 어노테이션"이라는 이름으로 먼저 뚫어 둔 것입니다. 그때는 아무 객체나 적을 수 있는 빈 슬롯이었고, "여기 적히는 것은 **타입**이다"라는 의미를 확정한 것이 7년 뒤 PEP 484(**파이썬 3.5**)입니다. 그래서 `typing` 모듈은 문법이 아니라 **나중에 얹힌 라이브러리**이고, 이 절 전체의 이상한 사정(`List` 와 `list` 가 둘 다 있는 것 등)이 여기서 나옵니다.
>
> 변수에 붙이는 표기 — 이 소스의 `seen: list[str] = []`(domain/validators.py:158) 나 `taken: set[TransactionId] = set()`(storage/repositories.py:56) 같은 것 — 은 또 별개로 PEP 526(**파이썬 3.6**)에서 들어왔습니다. dataclass 가 `field: type` 줄만으로 필드를 선언할 수 있는 것도 이 PEP 526 표기 위에 세워진 기능입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

budget_app/storage/jsonl.py:25-28
```python
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar
```

이 프로젝트에 실제로 쓰인 대표 시그니처들:

budget_app/storage/jsonl.py:193 (Iterator — 하나씩 꺼내 쓰는 반복자를 반환)
```python
    def stream(self) -> Iterator[T]:
```

budget_app/storage/repositories.py:53 (Tuple — 정확히 (int, 문자열 집합) 2개 묶음 반환)
```python
    def id_state(self) -> tuple[int, set[TransactionId]]:
```

budget_app/storage/repositories.py:112 (`| None` — "Transaction 또는 None")
```python
    def get(self, tx_id: object) -> Transaction | None:
```

각 타입의 뜻:

| 표기 | 의미 | 어디서 오나 |
|---|---|---|
| `X \| None` | X 이거나 None (예전 표기: `Optional[X]`) | 문법 자체 |
| `list[X]` / `dict[K, V]` / `set[X]` | X 의 리스트 / K→V 딕셔너리 / X 의 집합 | **기본 자료형** |
| `tuple[A, B]` | 정확히 이 순서·개수의 튜플 | 기본 자료형 |
| `tuple[X, ...]` | X 가 몇 개든 들어가는 튜플 (`...` 는 문법 그대로 씀) | 기본 자료형 |
| `Iterator[X]` | `next()` 로 하나씩 꺼낼 수 있는 것 (제너레이터의 반환 타입) | `collections.abc` |
| `Iterable[X]` | for 문에 넣을 수 있는 모든 것 (리스트, 튜플, 제너레이터 …) | `collections.abc` |
| `Sequence[X]` | 길이를 물어보고 인덱스로 접근할 수 있는 것 | `collections.abc` |
| `Callable[[A], B]` | A 를 받아 B 를 돌려주는 함수 | `collections.abc` |

아래 넷이 **기본 자료형이 아니라 `collections.abc`** 에서 오는 것이 우연이 아닙니다. 이들은 "무엇으로 만들어졌는가"가 아니라 **"무엇을 할 수 있는가"** 를 말하는 추상 기반 클래스입니다. 그 차이가 §10.2 의 주제입니다.

`Iterable` 과 `Iterator` 의 구분이 실전 포인트입니다. `append_all(self, entities: Iterable[T])`(storage/jsonl.py:213)는 "리스트든 제너레이터든 반복만 되면 받겠다"는 **관대한 입력**이고, `stream(self) -> Iterator[T]`(storage/jsonl.py:193)은 "한 번 순회하면 소진되는 반복자를 준다"는 **정확한 출력** 선언입니다.

`Callable` 은 함수를 인자로 받는 자리에 쓰입니다.

budget_app/cli/prompts.py:60
```python
def ask_until(prompt: str, validator: Callable[[str], T]) -> T:
```

"문자열을 받아 T 를 돌려주는 함수"를 받고, 그 T 를 그대로 돌려준다는 뜻입니다. `validators.parse_date` 를 넘기면 `str` 이, `parse_amount` 를 넘기면 `int` 가 나온다는 것을 타입만으로 표현합니다.

### 10.2 `list` 와 `typing` — 무엇이 대체 가능하고 무엇이 아닌가

`List[str]` 과 `list[str]` 중 무엇을 쓰는지는 사실 **성격이 다른 세 질문이 섞인 것**이라, 하나씩 떼어 놓아야 답이 됩니다. 지금 코드를 세어 보면 이렇게 갈립니다.

| 부류 | 개수 | 표기 |
|---|---|---|
| 리스트/딕셔너리/튜플/집합 | 43 | `list[str]`, `dict[str, Any]`, `tuple[int, ...]` … **기본 자료형** |
| "X 이거나 None" | 45 | `X \| None` |
| `Iterable` 17, `Callable` 12, `Iterator` 9, `Sequence` 4, `Generic` 1 | 43 | **기본 자료형에 대응물이 없다** — `collections.abc` / `typing` |

앞의 둘은 예전에 `List`/`Optional` 로 적혀 있던 것을 [Phase 6-1 리팩터](#)에서 정리한 결과입니다(아래 ③). 마지막 부류는 정리 대상이 아니라 **이 코드에서 가장 중요한 타입 표기**입니다.

#### ① `Iterable` 은 `list` 의 옛날 표기가 아니다 — 추상화 수준이 다르다

`list` 는 **구체적인 자료형**(메모리에 다 들어 있고, `len()` 이 되고, 몇 번이든 다시 순회 가능)이고 `Iterable` 은 **약속**(한 번 for 문에 넣을 수 있다)입니다. 후자가 훨씬 넓습니다. 이 코드는 그 차이를 의도적으로 씁니다 — **받을 때는 넓게, 돌려줄 때는 정확하게**.

budget_app/storage/jsonl.py:213 (받는 쪽 — 리스트든 제너레이터든 튜플이든)
```python
    def append_all(self, entities: Iterable[T]) -> int:
```

budget_app/storage/jsonl.py:193 (주는 쪽 — "한 번 순회하면 소진된다"는 경고)
```python
    def stream(self) -> Iterator[T]:
```

파라미터에 `Iterable`/`Sequence` 를 쓴 자리가 17곳입니다. 여기에 `List` 라고 적었다면 호출자는 제너레이터를 넘기기 전에 `list(...)` 로 통째로 메모리에 올려야 했을 것이고, [07 §2](./07-repository.md)의 스트리밍 설계가 그 자리에서 무너집니다. **`Iterable` 은 "게으르게 넘겨도 된다"는 허가증입니다.**

#### ② `Sequence` 를 고른 자리는 버그 방지선이다

budget_app/cli/presenter.py:96-101
```python
def category_lines(names: Sequence[str]) -> Iterator[str]:
    if not names:
        yield messages.MSG_NO_CATEGORIES_LISTED
        return
    for name in names:
        yield messages.FMT_CATEGORY_ITEM.format(name=name)
```

여기만 `Iterable` 이 아니라 `Sequence` 입니다. 이유는 3번째 줄의 `if not names` 입니다.

```python
bool([])                 # False  ← 빈 리스트는 거짓
bool(x for x in [])      # True   ← 빈 제너레이터는 참!
len(x for x in [])       # TypeError: object of type 'generator' has no len()
```

제너레이터는 **비어 있어도 참**입니다. 만약 이 함수가 `Iterable` 을 받는다고 선언해서 누군가 빈 제너레이터를 넘기면, `if not names` 가 거짓이 되어 "등록된 카테고리가 없습니다" 안내가 나오지 않고, 이어지는 for 문도 아무것도 내놓지 않아 **화면에 아무 줄도 안 찍히고 조용히 끝납니다**. `Sequence` 는 "길이를 물어볼 수 있는 것만 달라"는 요구이고, 그 조건이 곧 `if not names` 가 성립하는 조건입니다.

같은 이유로 `plan_rewrite` 는 `Iterator` 가 아니라 `RewritePlan`(줄 목록 + 변경 여부)을 돌려줍니다. 제너레이터로 돌려주면 줄 계산이 **파일에 쓰는 도중에** 일어나고, 그건 같은 파일을 읽으면서 교체하는 것이 되어 `UnitOfWork` 의 전제가 깨집니다. `list[str]` 을 담아 돌려주는 것은 "이미 다 계산해 놨다"는 선언입니다.

> 이 두 자리에서 타입 표기는 장식이 아니라 **계약**입니다. 다만 이 프로젝트에는 mypy 같은 정적 검사기(프로그램을 실행하지 않고 소스만 읽어 어긋난 곳을 찾아 주는 도구)가 없으므로(§10.3), 계약을 지키는 것은 어디까지나 읽는 사람의 몫입니다.

#### ③ `List` vs `list` 는 역사적 잔재였다 — 그래서 정리했다

`List`, `Dict`, `Tuple`, `Optional` 은 다릅니다. 이건 설계가 아니라 **파이썬 버전 사정**이었습니다.

| 파이썬 | 상황 |
|---|---|
| ~3.8 | `list[int]` 은 실행 시 `TypeError`. 그래서 `typing.List` 가 **필요**했다 |
| 3.9+ | [PEP 585] 기본 자료형이 `[]` 를 받는다 — `list[int]` 가 정상 동작 |
| 3.10+ | [PEP 604] `X \| None` 이 `Optional[X]` 를 대체 |

이 프로젝트는 `requires-python = ">=3.10"`(pyproject.toml)이라 **둘 다 쓸 수 있습니다.** 그런데 코드에는 `typing.List` 가 남아 있었고, 정작 `pyproject.toml` 은 `select = ["E", "F", "I", "UP", "B"]` 로 `UP`(pyupgrade)을 켜 두고 있었습니다. 돌려 보면 이렇게 나왔습니다.

```
46  UP006  non-pep585-annotation            ← List[x] → list[x]
45  UP045  non-pep604-annotation-optional   ← Optional[X] → X | None
42  UP035  deprecated-import                ← Iterable 등은 collections.abc 에서
15  UP037  quoted-annotation                ← "TransactionId" 따옴표 불필요
 9  E501   line-too-long
 1  UP028  yield-in-for-loop
```

**취향 차이가 아니라 설정과 코드가 어긋난 상태**였습니다. 켜 두고 지키지 않는 설정은 설정이 아니라 문서입니다. 그래서 전부 정리했고, 지금은 통과합니다.

```bash
uv run --no-project --with ruff ruff check budget_app/ tests/
# All checks passed!
```

> **과제 방어 포인트** — "왜 `List` 를 썼나"와 "왜 `Iterable` 을 썼나"는 **같은 질문이 아닙니다.** 전자는 표기 문제라 "구식 표기였고 정리했다"가 답이고, 후자는 ①②의 설계 근거를 대야 합니다. 이 둘을 구분해 답하는 것이 핵심입니다.

정리 후에는 `typing` 에서 가져오는 것이 `Any`·`TypeVar`·`Generic` 셋뿐입니다. `Iterable`/`Iterator`/`Callable`/`Sequence` 는 원래 있어야 할 자리인 `collections.abc` 에서 가져옵니다 — 이들은 자료형이 아니라 **추상 기반 클래스**이기 때문입니다.

budget_app/storage/jsonl.py:25-28
```python
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar
```

#### ④ `from __future__ import annotations` 가 하는 일

각 모듈 첫머리(43개 중 28개)에 있는 이 한 줄은 [PEP 563] 으로, **타입 표기를 실행하지 않고 문자열로 남겨 둡니다.**

```python
def f(x: list[int]) -> None: ...
# 이 줄은 파이썬 3.8 에서 TypeError.
# from __future__ import annotations 가 있으면 "list[int]" 라는 문자열로만 저장되어
# 실행되지 않으므로 오류가 나지 않는다.
```

효과는 두 가지입니다. (1) 구버전에서도 새 표기를 쓸 수 있고, (2) 아직 정의되지 않은 클래스 이름을 따옴표 없이 쓸 수 있습니다 — `TransactionId.of()` 가 `-> "TransactionId"` 대신 `-> TransactionId` 라고 적을 수 있는 이유이고, 위 `UP037` 15건이 바로 "이제 따옴표 지워도 된다"는 지적입니다.

**한계도 분명합니다.** 문자열이 되는 것은 *표기 위치*뿐입니다. 아래처럼 표기가 아닌 자리에서 타입을 값으로 쓰면 그대로 실행되므로, 그 자리에는 구버전 호환이 적용되지 않습니다.

```python
T = TypeVar("T")                      # 표기가 아니라 실행되는 코드
class JsonlStore(Generic[T]): ...     # 상속 목록도 실행된다 (storage/jsonl.py:131)
```

### 10.3 타입 힌트는 런타임에 강제되지 않는다

가장 중요한 사실: 파이썬은 타입 힌트를 **실행 중에 검사하지 않습니다**. `def stream(self) -> Iterator[T]:` 에 문자열을 반환하는 코드를 넣어도 파이썬은 그냥 실행합니다. 힌트는 (1) 읽는 사람을 위한 문서, (2) IDE 자동완성, (3) mypy 같은 정적 검사 도구를 위한 정보일 뿐입니다.

> **⚙️ 내부 동작 — 힌트는 검사되는 대신 딕셔너리에 보관됩니다.** 파이썬이 어노테이션으로 하는 일은 딱 하나, **`__annotations__` 라는 딕셔너리에 담아 두는 것**입니다. 검사하는 코드는 인터프리터 어디에도 없습니다.
>
>     :::python
>     def f(x: int) -> str: return x      # int 를 받아 int 를 그대로 돌려준다
>     f.__annotations__     # {'x': <class 'int'>, 'return': <class 'str'>}
>     f("hello")            # 'hello'  ← 아무 일도 일어나지 않는다
>
> `from __future__ import annotations`(§10.2 ④)를 켜면 이 딕셔너리의 **값이 문자열**이 됩니다(`{'x': 'int', 'return': 'str'}`). 그래서 mypy 같은 도구는 실행이 아니라 **소스를 읽어서** 검사하고, `dataclasses` 처럼 실행 중에 어노테이션을 활용하는 라이브러리는 이 딕셔너리를 뒤져 필드 목록을 알아냅니다 — `TransactionPatch.changed_fields()` 가 쓰는 `fields(self)`(§5.2)의 정보가 바로 여기서 옵니다. 즉 어노테이션은 **검사 장치가 아니라 데이터**입니다. → [12 §2-B](./12-syntax-and-stdlib.md)

그래서 이 프로젝트는 타입을 믿지 않고 **런타임 검증을 따로** 둡니다 — `Transaction.__post_init__`(domain/entities.py:68-80)이 실제 값 검사를 수행합니다. "힌트는 개발 시점 도구, 검증은 실행 시점 코드"라는 역할 분담을 과제 방어 때 설명할 수 있어야 합니다.

**다만 타입 힌트가 실제로 오류를 잡아 주는 자리도 있습니다.** dataclass 는 필드 이름이 선언돼 있으므로, 없는 이름을 넘기면 런타임에 `TypeError` 가 납니다.

```python
TransactionPatch(catgeory="food")   # TypeError: 오타가 즉시 드러남
{"catgeory": "food"}                # 그냥 통과 — 나중에 조용히 무시됨
```

리팩터에서 `Dict[str, object]` 를 `TransactionPatch` 로 바꾼 실질적 이유가 이것입니다.

---

## 11. 자주 나오는 관용구

### 11.1 `or` 단락 평가 — `(value or "")`

파이썬의 `or` 는 왼쪽이 거짓 같은 값(None, `""`, 0, 빈 리스트 …)이면 오른쪽을 반환합니다. `(value or "")` 는 "value 가 None 이면 빈 문자열로 대체"라는 뜻입니다.

budget_app/domain/validators.py:74
```python
    v = str(value or "").strip().lower()
```

`None.strip()` 은 AttributeError 로 즉사하지만, `(None or "")` 는 `""` 가 됩니다. None 일 수도 있는 값에 문자열 메서드를 안전하게 체이닝하는 정석 패턴이며, `validators.py` 의 문자열 파서들(74, 94, 108, 117, 125행)이 모두 이 패턴으로 시작합니다.

> **⚙️ 내부 동작 — `or` 는 bool 을 돌려주지 않습니다.** 다른 언어와 갈리는 지점입니다. 파이썬의 `a or b` 는 "`bool(a)` 가 참이면 **`a` 자체**를, 아니면 **`b` 자체**를" 돌려줍니다. `True`/`False` 로 바꾸지 않습니다.
>
>     :::python
>     None or ""          # ''      ← 문자열이 나온다
>     "Income" or ""      # 'Income'
>     5 or 0              # 5       (bool 이 아니라 int)
>
> 그래서 `str(value or "")` 가 성립합니다 — `or` 의 결과가 곧 문자열이거나 원래 값이라 `str()` 이 그대로 받습니다. 참/거짓 판정 자체는 `bool(a)`, 즉 `type(a).__bool__` 을 부르고, 그것이 없으면 `__len__` 이 0 인지를 봅니다. **빈 리스트·빈 문자열이 거짓인 이유가 `__len__` 이 0 이기 때문**이고(`0` 은 `__len__` 이 아예 없고 `int.__bool__` 이 `False` 를 돌려주기 때문입니다), 제너레이터가 `__bool__` 도 `__len__` 도 없어서 **비어 있어도 참**인 이유(§10.2 ②)가 정확히 같은 규칙에서 나옵니다. → [12 §1-B](./12-syntax-and-stdlib.md)

**지연 실행**에도 쓰입니다.

budget_app/storage/backup.py:28
```python
    ts = (now or datetime.now()).strftime(config.BACKUP_TS_FORMAT)
```

`now` 가 주어졌으면 그 값을 쓰고, 없으면(None → 거짓) **그때서야** `datetime.now()` 를 호출합니다. `or` 는 왼쪽이 참이면 오른쪽을 **아예 평가하지 않으므로**(단락 평가), 인자가 있을 땐 현재 시각을 읽지 않습니다.

**주의점**: `or` 는 None 만이 아니라 `""`, `0` 도 거짓으로 취급합니다. 그래서 "0 이나 빈 문자열도 유효한 값"인 자리에서는 `or` 대신 `is not None` 으로 **None 만 정확히** 검사해야 합니다.

budget_app/domain/entities.py:146-150
```python
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if getattr(self, f.name) is not None
        }
```

만약 여기서 `if getattr(...)` 라고만 썼다면 `--memo ""`(메모를 지우려는 의도)가 "변경 없음"으로 취급돼 동작하지 않습니다. 두 패턴의 구분이 이 코드를 이해하는 열쇠입니다.

`handle_errors` 의 반환값 처리에도 같은 논리가 있습니다.

budget_app/cli/error_handler.py:50-54
```python
            result = func(*args, **kwargs)
            # `func(...) or EXIT_OK` 로 쓰면 0/""/[]/False 같은 falsy 반환값까지
            # 전부 EXIT_OK 로 바뀐다. 규약은 "None 이면 EXIT_OK" 이므로 None 만
            # 정확히 검사한다 (EXIT_OK 가 0 이 아니게 되어도 의미가 흔들리지 않는다).
            return config.EXIT_OK if result is None else result
```

### 11.2 조건 표현식 (삼항 연산자)

`A if 조건 else B` 는 한 줄로 두 값 중 하나를 고릅니다.

> **🔎 문법의 출처 — 순서가 이상한 데는 사연이 있습니다.** 조건 표현식은 PEP 308 로 **파이썬 2.5** 에 들어왔습니다. C 계열의 `조건 ? A : B` 와 달리 **값이 먼저, 조건이 가운데** 오는 것은 "평소에 쓰는 값을 앞세우고 예외 조건을 뒤에 단다"는 영어 어순(`x if y else z`)을 따른 결과입니다. 그 전에는 `조건 and A or B` 라는 관용구를 썼는데, **`A` 가 거짓 같은 값이면 조건이 참인데도 `B` 가 나오는** 치명적 버그가 있어 PEP 308 이 도입된 직접적 이유가 되었습니다. 이 소스의 `TransactionId.parse(raw_id) if raw_id else None` 이 딱 그 함정에 걸릴 자리인데(정상 결과가 거짓일 수 있는 값이라면), 조건 표현식은 조건만 보고 가지를 고르므로 안전합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

budget_app/storage/csv_io.py:113-123
```python
    raw_id = (row.get(config.CSV_ID_COLUMN) or "").strip()
    return ParsedRow(
        # 빈 id 는 "발급해 달라"는 뜻이므로 오류가 아니다. 값이 있으면 형식을 강제한다.
        tx_id=TransactionId.parse(raw_id) if raw_id else None,
        type=validators.parse_type(row["type"]),
        date=validators.parse_date(row["date"]),
        amount=validators.parse_amount(row["amount"]),
        category=validators.parse_category(row.get("category") or ""),
        memo=validators.parse_memo(row.get("memo")),
        tags=validators.parse_tags(row.get("tags")),
    )
```

"id 값이 있으면 형식을 검증하고, 없으면 None(= 새로 발급해 달라)" — 빈 id 가 오류가 아니라는 정책이 한 줄에 들어 있습니다.

budget_app/storage/jsonl.py:189
```python
            data_dict = data if isinstance(data, dict) else None
```

### 11.3 bool 반환 관례 — 성공/실패를 True/False 로

예외를 던질 정도의 "오류"는 아니고, 호출한 쪽이 분기만 하면 되는 결과는 bool 로 반환합니다.

budget_app/storage/repositories.py:248-254
```python
    def add(self, name: str) -> bool:
        """추가 성공 시 True, 이미 존재하면 False."""
        cat = Category(name=name)
        if self.exists(cat.name):
            return False
        self.append(cat)
        return True
```

호출부는 이 반환값으로 메시지만 바꿉니다.

budget_app/cli/handlers.py:84-90
```python
def cmd_category_add(ctx: AppContext, args: argparse.Namespace) -> int:
    name = prompts.ask_category_name(args.name)
    if ctx.cat_service.add(name):
        output.out(messages.MSG_SAVED_CATEGORY.format(name=name))
    else:
        output.out(messages.MSG_CATEGORY_EXISTS.format(name=name))
    return config.EXIT_OK
```

"이미 존재하는 카테고리 추가"는 사용자 실수라기보다 정상 시나리오이므로 예외가 아닌 False 가 적절합니다. 같은 관례가 `TransactionRepository.delete`(storage/repositories.py:150-171)에도 쓰이는데, 이쪽은 서비스 계층(services/transactions.py:72-77)이 False 를 받아 AppError 로 승격시킵니다 — **"저장소는 사실만 보고, 오류 판정은 서비스가 한다"** 는 계층 분리입니다([04](./04-architecture.md)).

### 11.4 튜플 언패킹 — 여러 값을 한 번에 받기

함수가 튜플을 반환하면, 받는 쪽에서 쉼표로 나눠 한 번에 변수에 담을 수 있습니다.

budget_app/storage/repositories.py:65-77
```python
    def id_allocator(self) -> IdAllocator:
        """이 파일 상태에 맞춘 발급기를 만든다. 배치 작업은 이걸 한 번만 받아 쓴다.
        ...
        """
        max_n, taken = self.id_state()
        return IdAllocator(start=max(max_n, self._watermark.read()), taken=taken)
```

budget_app/domain/queries.py:77-78
```python
        start, end = month_range(month)
        return cls(date_from=start, date_to=end, **extra)
```

`month_range` 는 `return f"...", f"..."` 로 값 두 개를 쉼표로 반환하는데, 이것이 곧 튜플입니다(괄호 없이도 튜플). 받는 쪽의 `start, end =` 가 그 튜플을 풉니다. for 문 안의 언패킹(`for lineno, row in ...`, `for rank, (category, amount) in enumerate(...)`)도 모두 같은 원리입니다.

### 11.5 `yield from` — 반복을 통째로 위임

budget_app/services/transactions.py:87
```python
        yield from items
```

`for it in items: yield it` 과 같은 뜻이지만 한 줄입니다. 프레젠터에서는 다른 제너레이터 함수에 위임하는 데 씁니다.

budget_app/cli/presenter.py:72-73
```python
    if summary.budget is not None:
        yield from _budget_lines(summary)
```

`_budget_lines` 가 내놓는 줄들을 그대로 흘려보냅니다.

> **🔎 문법의 출처 / ⚙️ 왜 for 문보다 나은가** — `yield from` 은 PEP 380 으로 **파이썬 3.3** 에 들어왔습니다. 그 전에는 `for it in items: yield it` 이 유일한 방법이었습니다. 단순한 줄임말처럼 보이지만 하는 일이 더 많습니다 — `yield from`은 바깥 소비자와 안쪽 제너레이터를 **직접 연결**해서, 값뿐 아니라 `send()`·`throw()`·`close()` 와 안쪽의 `return` 값까지 그대로 통과시킵니다.
>
> 이 소스에서 실질적인 이득은 **닫힘의 전파**입니다. `tx_table` 이 `limit` 에 도달해 `break` 하면 상류 제너레이터가 닫히는데, `yield from` 으로 이어져 있으면 그 닫힘이 `_budget_lines`·`stream_sorted` 를 거쳐 `open()` 된 파일까지 한 번에 전해집니다. 손으로 쓴 for 루프는 그 신호를 삼켜 버릴 수 있습니다. ruff 의 `UP028` 규칙이 `for ... : yield ...` 를 지적하는 것도 이 때문이고, §6.1 의 `yield from enumerate(...)` 가 바로 그 지적을 받아 고친 자리입니다. 제너레이터의 자세한 동작은 [03 §4](./03-python-advanced.md)에서 다룹니다. → [12 §1-C](./12-syntax-and-stdlib.md)

---

## 12. 정리 — 어느 파일에서 무엇을 배우는가

| 문법 요소 | 대표 위치 |
|---|---|
| 패키지/`__main__`/상대 임포트 | `__init__.py:1-3`, `__main__.py:1-8`, cli/handlers.py:22-30 |
| `if __name__` + `sys.exit` | cli/app.py:97-98, cli/config.py:22-29 |
| 기본값·키워드·키워드 전용 인자 | services/transactions.py:27-35, cli/handlers.py:33-50, services/importexport.py:88-94 |
| `*args`/`**kwargs`, `{**A, **B}` 병합 | decorators.py:37-47, domain/entities.py:113-124 |
| 문자열 메서드·3가지 포맷 | domain/validators.py:73-77, domain/periods.py:30, cli/messages.py:48, storage/jsonl.py:203 |
| 포맷 스펙 미니 언어 (`{:06d}`·`{:<7}`·`{!r}`) | domain/config.py:26, cli/messages.py:43, domain/specs.py:182 |
| 컴프리헨션 3종 + dict.get 누적 | storage/repositories.py:238·242, domain/entities.py:144-150, services/budgets.py:54 |
| enumerate/any/sorted/슬라이싱/max | storage/jsonl.py:175, storage/csv_io.py:87, storage/repositories.py:246, services/budgets.py:56-58, storage/repositories.py:53-63 |
| try/except/finally/raise | domain/validators.py:40-70, storage/jsonl.py:181-191, decorators.py:50-66 |
| open 모드/encoding/newline/with/fsync | storage/jsonl.py:48-72, 220-247, storage/csv_io.py:131-148 |
| pathlib.Path 전반 | storage/backup.py:17-33, storage/jsonl.py:48-60, 150-158 |
| 타입 힌트 | storage/jsonl.py:25-28·193·213, cli/prompts.py:60 |
| or 단락 평가·조건 표현식·bool 관례·언패킹·yield from | domain/validators.py:74, storage/csv_io.py:113-123, storage/repositories.py:248-254, domain/queries.py:77, services/transactions.py:87 |

이 문서의 문법 요소들이 **왜 그 자리에 배치되었는지**(계층 구조)는 [04. 아키텍처](./04-architecture.md)에서, 예외 처리와 dataclass·제너레이터·데코레이터의 전체 그림은 [03. 파이썬 중·고급 기법](./03-python-advanced.md)에서 이어집니다.
