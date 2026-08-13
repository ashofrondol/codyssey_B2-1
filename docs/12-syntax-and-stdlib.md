# 12. 문법의 출처와 표준 라이브러리 내부 동작

## 쉬운 말로 먼저

이 문서는 **앞에서부터 읽는 문서가 아닙니다.** 두꺼운 사전에 가깝습니다 — 프로그램의 소스 코드를 직접 들여다보다가 뜻을 알 수 없는 기호나 낯선 이름을 만났을 때, 그 자리에서 펴 보라고 만든 것입니다. 여기 실린 항목은 하나같이 두 가지에만 답합니다. **"이 표기는 누가, 언제, 어떤 불편을 없애려고 만들었나"** 와 **"이 한 줄이 안에서 실제로 무슨 일을 하나"** 입니다. 항목이 수백 개인 이유도 그래서입니다. 다 읽으라고 모아 둔 것이 아니라, 무엇에 걸리든 찾을 수 있게 모아 둔 것입니다. 시리즈의 다른 문서들이 본문 곳곳에 달아 둔 🔎·⚙️ 상자는 전부 이 문서의 어느 항목을 줄여 적은 쪽지이고, 그 쪽지의 원본이 여기 있습니다.

**이 문서에 자주 나오는 말**

| 말 | 쉬운 뜻 |
| --- | --- |
| PEP | 파이썬에 새 기능을 넣기 전에 "무엇을, 왜, 어떻게"를 적어 공개해 둔 제안서. 번호가 붙습니다(PEP 557 처럼) |
| 표준 라이브러리 | 파이썬을 설치하면 함께 딸려 오는 기본 도구 모음. 따로 내려받지 않아도 바로 쓸 수 있습니다 |
| 데코레이터 | 함수나 클래스 정의 바로 위에 `@이름` 을 한 줄 얹어, 그 정의를 `이름(...)` 에 한 번 통과시킨 결과로 **바꿔치기**하는 표기. 겉을 한 겹 감싸는 경우도 있고(`@log_call`), 원래 것을 그대로 돌려주면서 내용만 채워 넣는 경우도 있습니다(`@dataclass`) |
| 제너레이터 | 결과를 한꺼번에 다 만들어 주지 않고, 달라고 할 때마다 하나씩 내어 주는 함수 |
| 바이트코드 | 사람이 쓴 파이썬 코드를, 파이썬이 실행하기 좋게 잘게 옮겨 적어 둔 중간 형태 |
| 원자적 교체 | 남이 그 파일을 열어 보는 순간에는 **옛 내용 아니면 새 내용**만 보이게, 통째로 한 번에 갈아 끼우는 것. 파일 **하나**에 대한, **같은 파일시스템 안에서의** 약속입니다(§3 에 못 지키는 것 세 가지가 정리돼 있습니다) |
| 버퍼 | 한 글자 쓸 때마다 매번 디스크까지 다녀오지 않도록, 잠시 모아 두는 임시 자리 |
| 인코딩 | 글자를 저장·전송용 숫자(바이트)로 바꾸는 약속. 읽는 쪽과 쓰는 쪽의 약속이 어긋나면 글자가 깨집니다 |

**바쁘면 여기만**

- **[§4 역색인](#4-역색인--소스-파일에서-이-문서로)** — 이 문서를 쓰는 정상적인 방법입니다. 읽고 있던 소스 파일의 이름을 표에서 찾으면, 그 파일에서 걸릴 만한 표기와 설명이 있는 절이 짝지어져 있습니다. 무엇을 찾을지 아직 모르겠다면 여기부터 여세요.
- **[§3 운영체제 계층](#3-운영체제-계층--파일-원자성-스트림-파이프-인코딩)** — 이 프로그램이 "저장하다 멈춰도 데이터 파일이 반쯤 망가진 채 남지는 않는다"고 약속하는 근거, **그리고 그 약속이 어디까지만 유효한지**(파일 한 개 단위·같은 파일시스템·Windows 에서는 보장이 다름)가 함께 모여 있습니다. 코드를 몰라도 무엇을 지키려는 것인지, 그리고 무엇까지는 지키지 못하는지가 읽히는 절입니다.
- **[§1-B 의 `@dataclass` 항목](#dataclass)** — 짧은 한 줄이 실제로는 여러 벌의 코드를 대신 만들어 낸다는 이야기입니다. 이 소스의 `domain/` 폴더 전체가 그 위에 서 있어서, 결국 가장 자주 돌아오게 되는 항목입니다.

---

budget_app 소스에 등장하는 문법·관용구·표준 라이브러리 호출을 하나씩 붙잡아, **"이 표기는 어디서 왔는가"** 와 **"이 호출은 안에서 무슨 일을 하는가"** 두 가지에만 답하는 참조 문서입니다.

시리즈의 다른 문서와 역할이 다릅니다. [02](./02-python-basics.md)·[03](./03-python-advanced.md)이 "이 코드에 어떤 문법이 쓰였나"를, [04](./04-architecture.md)~[10](./10-advanced-design.md)이 "왜 이렇게 설계했는가"를 다룬다면, 이 문서는 그 아래 한 층을 팝니다 — 설계 판단이 아니라 **언어와 라이브러리 자체의 사실**입니다. 그래서 여기에는 "이 파일이 저 계층에 있어야 하는 이유" 같은 설명이 없고, 대신 `@dataclass` 가 `exec` 로 만들어 내는 소스 코드, `argparse` 가 하위 파서의 값을 상위 네임스페이스로 복사하는 여섯 줄, `os.replace` 가 보장하지 **않는** 것 같은 이야기가 있습니다.

> **난이도**: 🟡 중급 ~ 🔴 고급
>
> **먼저 읽으면 좋은 문서**: [02. 파이썬 기초 문법](./02-python-basics.md), [03. 파이썬 중·고급 기법](./03-python-advanced.md) — 두 문서가 "무엇이 쓰였는가"를 먼저 보여 줍니다. 계층 구조가 궁금해지면 [04. 아키텍처](./04-architecture.md)로 빠져나가는 것이 좋습니다.
>
> **읽는 법**: 처음부터 순서대로 읽어도 되지만(§1 언어 문법 → §2 표준 라이브러리 → §3 운영체제 계층), 그렇게 쓰라고 만든 문서는 아닙니다. **소스를 읽다 막힌 표기가 생겼을 때 맨 끝 [§4 역색인](#4-역색인--소스-파일에서-이-문서로)에서 그 파일이나 그 이름을 찾아 들어오는 것**이 원래 용도입니다. 시리즈의 다른 문서들이 본문 곳곳에 달아 둔 **🔎 문법의 출처** / **⚙️ 내부 동작** 상자는 전부 이 문서의 어느 항목을 가리키는 압축 노트입니다.

> 아래 두 표는 이 문서를 **정확하게** 읽기 위한 약속입니다 — 어떤 문장이 직접 실행해 확인한 결과이고 어떤 문장이 문서에 근거한 역사적 사실인지, 그리고 각 항목이 어떤 순서로 쓰였는지를 정해 둡니다. 처음 펴 보는 것이라면 건너뛰었다가, 어떤 주장의 근거가 궁금해질 때 돌아오셔도 됩니다.

**버전 기준선.** 이 프로젝트는 `pyproject.toml` 에서 `requires-python = ">=3.10"` 을 선언하고 Ruff 도 `target-version = "py310"` 으로 맞춰 두었습니다. 그러나 이 문서의 실행 결과·바이트코드·CPython 소스 인용은 전부 **로컬 CPython 3.13.1(Windows 11)** 에서 직접 확인한 것입니다. 두 층위를 문장에서 구분해 읽으셔야 합니다.

| 표기 | 뜻 | 확인 방법 |
| --- | --- | --- |
| "3.13.1 에서 확인", "실측" | 이 저장소의 로컬 환경에서 **직접 실행해 얻은 결과** | 재현 가능. 다른 버전·플랫폼에서는 달라질 수 있음 |
| "PEP NNN", "파이썬 N.N 에 도입" | 문서·PEP 에 근거한 **역사적 사실** | 실행으로 확인할 수 없음. 로컬에서 근거를 댈 수 없는 도입 버전은 적지 않았음 |

바이트코드 옵코드 **이름**과 CPython 표준 라이브러리의 **줄 번호**는 파이썬 버전마다 바뀝니다. 3.10 에서 같은 코드를 열면 구현 위치가 다를 수 있으나, 이 문서가 주장하는 **기제**는 그대로입니다.

**각 항목의 형식.** 항목은 대체로 네 단으로 되어 있습니다. 필요 없는 단은 생략하고, 어떤 항목은 「무엇으로 풀리나」 대신 「내부에서 무슨 일이 일어나나」를 씁니다.

| 단 | 답하는 질문 |
| --- | --- |
| **어디서 왔나** | 이 표기·API 는 언제, 어떤 문제를 풀려고 생겼나. 그 전에는 어떻게 썼나 |
| **무엇으로 풀리나** / **내부에서 무슨 일이 일어나나** | 파이썬이 이것을 실제로 무엇으로 바꾸나 (바이트코드·생성된 소스·CPython 구현) |
| **이 소스에서** | budget_app 의 어느 줄이 그것을 쓰고, 왜 하필 그 형태인가 |
| **없으면 어떻게 되나** | 그 표기를 빼거나 다른 것으로 바꾸면 무엇이 깨지나 |

코드 인용은 시리즈 규약을 따릅니다 — 코드블록 바로 위 줄의 `budget_app/파일.py:시작-끝` 이 작성 시점의 실제 위치이고, "일반론 예시"라고 표시한 블록은 **이 소스에 없는** 코드입니다.

---

## 1-A. 모듈과 실행 모델, 함수 시그니처, 문자열

> **이 절은 무엇인가** — 파이썬 파일을 열면 맨 위에서 늘 만나게 되는 것들을 다룹니다. 흩어진 파일 여러 개를 어떻게 묶어 하나의 프로그램으로 만드는지, 그 프로그램이 어디서부터 시작되는지, 함수에 값을 넘길 때 "이름을 붙여서 넘겨라"라고 강제하는 표기는 무엇인지, 화면에 보일 문장을 어떤 방식으로 조립하는지입니다. 소스를 처음 여는 사람이 가장 먼저 걸려 넘어지는 자리들이라 맨 앞에 두었습니다.

이 절은 파일을 열자마자 만나는 것들 — 패키지와 진입점, 함수 시그니처, 문자열 포맷 — 의 출처를 따라갑니다. `python -m budget_app` 이 왜 동작하는지, `from . import config` 의 점이 바이트코드에서 무엇이 되는지, `cli/messages.py` 가 f-string 대신 `str.format` 을 쓸 수밖에 없는 이유가 여기 있습니다. 세 소절로 나뉩니다 — **1-A-1** 모듈·패키지·실행 모델, **1-A-2** 함수 시그니처와 인자, **1-A-3** 문자열과 포맷.

### 1-A-1. 모듈·패키지·실행 모델

> 이 절의 "3.13.1 에서 확인" 표시가 붙은 내용은 로컬 CPython 3.13.1 에서 직접 실행해
> 얻은 결과입니다. PEP 번호와 "도입 버전"은 실행으로 확인할 수 없는 역사적 사실이므로
> 표시를 나눠 적었습니다. 바이트코드 옵코드 **이름**은 파이썬 버전마다 바뀝니다.

#### `__init__.py` — 일반 패키지와 네임스페이스 패키지

**어디서 왔나** — 원래 파이썬은 `__init__.py` 가 있는 폴더만 패키지로 인정했습니다.
**PEP 420(Implicit Namespace Packages, 파이썬 3.3)** 이 그 요구를 없애서, 지금은
`__init__.py` 가 없는 폴더도 import 됩니다. 그래서 이 파일은 "패키지의 조건"이 아니라
**"일반 패키지(regular package)를 선언하는 표식"** 으로 의미가 바뀌었습니다.

**내부에서 무슨 일이 일어나나** — 두 종류의 차이는 import 시스템이 모듈 객체에 붙이는
`__path__` 의 **타입**으로 드러납니다. 3.13.1 에서 확인한 결과입니다.

| | `__init__.py` 있음 | `__init__.py` 없음 |
|---|---|---|
| `type(pkg.__path__)` | `list` | `_NamespacePath` |
| `pkg.__spec__.loader` | 소스 파일 로더 | `NamespaceLoader` |
| 같은 이름 폴더가 둘 | 처음 것만 쓰고 나머지 차폐 | **전부 병합** |

`list` 는 import 시점에 한 번 정해진 고정 목록입니다. 반면 `_NamespacePath` 는
`sys.path` 를 다시 훑어 **동적으로 재계산**하는 객체라, 나중에 `sys.path` 가 바뀌면
경로 목록도 따라 바뀝니다. "같은 이름 폴더가 조용히 섞여 든다"는 위험은 이 동적
재계산에서 나옵니다.

**이 소스에서** — 이 프로젝트의 `__init__.py` 는 최소한만 담습니다.

budget_app/__init__.py:1-3
```python
"""파일 기반 가계부 콘솔 프로그램."""

__version__ = "1.0.0"
```

**없으면 어떻게 되나** — `python -m budget_app` 은 그래도 동작합니다(네임스페이스
패키지로 잡히므로). 대신 `__version__` 과 패키지 docstring 을 놓을 자리가 사라지고,
`sys.path` 어딘가에 `budget_app` 이라는 이름의 폴더가 하나 더 생기면 두 폴더의 모듈이
한 패키지로 합쳐집니다. 설계 배경은 [02. 파이썬 기초](./02-python-basics.md) 1.1 절에
자세히 있습니다.

#### `__main__.py` 와 `python -m` — runpy 가 실제로 하는 일

**어디서 왔나** — `-m` 스위치의 실행 규칙을 정한 것이 **PEP 338(Executing modules as
scripts)** 이고, 그 구현이 표준 라이브러리 `runpy` 모듈입니다. `-m` 이 없던 시절에는
파일 경로를 직접 줘야 했고(`python budget_app/cli/app.py`), 그러면 패키지 문맥이
사라져 상대 임포트가 깨졌습니다.

**내부에서 무슨 일이 일어나나** — `python -m budget_app` 이 부르는 것은
`runpy._run_module_as_main("budget_app")` 입니다. 3.13.1 의 `Lib/runpy.py` 를 읽으면
순서가 이렇습니다.

1. `_get_module_details("budget_app")` 이 `importlib.util.find_spec("budget_app")` 로
   **spec 만 찾습니다. 이 단계는 아직 아무것도 import 하지 않습니다.** 함수 첫머리의
   `pkg_name, _, _ = mod_name.rpartition(".")` 이 최상위 이름에 대해 **빈 문자열**을
   주므로, 그 아래 `if pkg_name:` 블록의 `__import__(pkg_name)` 이 통째로 건너뛰어집니다.

        :::python
        pkg_name, _, _ = mod_name.rpartition(".")
        if pkg_name:                 # "budget_app" → pkg_name == "" → 거짓, 건너뜀
            __import__(pkg_name)

2. 찾아낸 spec 이 패키지면(`spec.submodule_search_locations is not None`) 이름 뒤에
   `.__main__` 을 붙여 **자기 자신을 다시 호출**합니다. **부모 패키지가 실제로 import
   되는 것은 이 재귀 호출 안에서입니다** — 이번에는 `mod_name == "budget_app.__main__"`
   이라 `pkg_name == "budget_app"` 이 되어 `__import__("budget_app")` 이 불리고, 그래서
   `budget_app/__init__.py` 가 **이 시점에** 실행됩니다.

        :::python
        pkg_main_name = mod_name + ".__main__"
        return _get_module_details(pkg_main_name, error)

   `__main__.py` 가 없으면 여기서 `"... is a package and cannot be directly executed"`
   가 납니다.

   3.13.1 에서 `_get_module_details` 와 `__import__` 를 감싸 호출 순서를 찍은
   결과입니다 — 바깥 호출이 아니라 **안쪽 재귀 호출**에서 import 가 일어납니다.

        ENTER _get_module_details 'budget_app'
          ENTER _get_module_details 'budget_app.__main__'
            >>> __import__('budget_app') 호출        ← __init__.py 가 여기서 실행
          EXIT  'budget_app.__main__'
        EXIT  'budget_app'
3. 그다음 코드 객체를 **이미 존재하는 `__main__` 모듈의 전역 딕셔너리 안에서**
   실행합니다.

        :::python
        main_globals = sys.modules["__main__"].__dict__
        return _run_code(code, main_globals, None, "__main__", mod_spec)

4. `_run_code` 가 그 전역에 이름들을 심습니다. 여기가 핵심입니다.

        :::python
        run_globals.update(__name__ = mod_name,        # "__main__"
                           __package__ = pkg_name,     # mod_spec.parent → "budget_app"
                           __spec__ = mod_spec)
        exec(code, run_globals)

즉 `__name__ == "__main__"` 이 성립하는 이유는 파일 이름이 `__main__.py` 라서가 아니라,
runpy 가 전역 딕셔너리에 `__name__` 을 문자열 `"__main__"` 으로 **대입해 놓고** 코드를
`exec` 하기 때문입니다. 그리고 같은 자리에서 `__package__` 는 `"budget_app"` 으로
남으므로, `__name__` 이 `"__main__"` 인데도 상대 임포트가 계속 동작합니다(그 규칙을 정한
것이 **PEP 366** 입니다).

**이 소스에서** — 진입점 파일 전체가 8줄입니다.

budget_app/__main__.py:1-8
```python
"""python -m budget_app 진입점."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
```

`from .cli import main` 이 여기서 동작하는 것이 위 4번의 직접적 결과입니다.

**없으면 어떻게 되나** — 파일을 직접 실행하면 `__package__` 가 비므로 상대 임포트가
곧바로 깨집니다. 3.13.1 에서 실제로 확인한 출력입니다.

```
$ python budget_app/cli/app.py
ImportError: attempted relative import with no known parent package
```

#### `sys.exit` — 함수가 아니라 예외입니다

**어디서 왔나** — 파이썬에는 "프로세스를 즉시 끝내는 문법"이 없습니다. `sys.exit(n)` 은
`SystemExit(n)` 예외를 **raise 할 뿐**이고, 그 예외가 아무에게도 잡히지 않고 최상위까지
올라가면 인터프리터가 종료 코드로 해석합니다.

**내부에서 무슨 일이 일어나나** — `SystemExit` 은 `Exception` 이 아니라 `BaseException`
의 직계 자식입니다. 3.13.1 에서 확인했습니다.

```
issubclass(SystemExit, BaseException) → True
issubclass(SystemExit, Exception)     → False
```

이 상속 위치는 설계된 것입니다. `except Exception:` 으로 광범위하게 잡는 코드가
**프로그램 종료 요청까지 삼켜 버리지 않도록** 하기 위해서입니다.

**이 소스에서** — `main()` 이 돌려준 정수를 셸 종료 코드로 바꾸는 자리는 두 곳입니다.

budget_app/__main__.py:7-8
```python
if __name__ == "__main__":
    sys.exit(main())
```

budget_app/cli/app.py:97-98
```python
if __name__ == "__main__":
    sys.exit(main())
```

종료 코드의 어휘 자체는 CLI 계층이 소유합니다.

budget_app/cli/config.py:21-29
```python
# 종료 코드
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_VALIDATION = 2
EXIT_IO = 3
EXIT_APP = 4
EXIT_NO_CATEGORY = 5
EXIT_ENCODING = 6
EXIT_INTERRUPT = 130
```

**없으면 어떻게 되나** — `sys.exit(main())` 대신 `main()` 만 부르면 반환값이 버려지고
프로세스는 항상 0 으로 끝납니다. 검증 실패(2)·입출력 실패(3)를 구분하는 이 표 전체가
셸 입장에서는 존재하지 않는 것이 되고, `budget_app add ... && echo ok` 같은 조합이
실패할 때도 `ok` 를 찍습니다.

상속 위치가 왜 중요한지는 이 프로젝트의 오류 방패가 보여 줍니다.

budget_app/cli/error_handler.py:105-106
```python
        # ---------- (4) 최후 방어선 — 분류 밖의 버그 ----------
        except Exception as exc:  # noqa: BLE001 — 어떤 예외도 트레이스백으로 끝내지 않기 위함
```

이 절은 `_dispatch` 안에서 일어나는 **모든** 예외를 잡아 `EXIT_ERROR`(1)로 바꿉니다.
만약 `SystemExit` 이 `Exception` 의 자식이었다면, 핸들러 안에서 부른 어떤 종료 요청도
여기서 삼켜져 "예기치 못한 오류가 발생했습니다"로 둔갑했을 것입니다. `BaseException`
바로 아래에 있기 때문에 이 절을 그대로 통과합니다.

#### 상대 임포트 — `from . import x` 가 `__package__` 를 쓰는 방식

**어디서 왔나** — 파이썬 2 는 "암묵적 상대 임포트"를 허용해서, `budget_app/config.py`
가 있으면 표준 라이브러리를 쓰려는 `import config` 조차 그 파일을 집어 갔습니다.
**PEP 328** 이 이 모호함을 없애 파이썬 3 에서 `import x` 는 **항상 절대 임포트**가 되고,
상대 참조는 점(`.`)으로 **명시**하게 됐습니다.

**무엇으로 풀리나** — 점은 표기법이 아니라 인자입니다. `import` 문은 `IMPORT_NAME`
옵코드로 컴파일되는데, 바로 앞에 **`level` 상수**가 실립니다. 3.13.1 에서 확인한
바이트코드입니다.

```
from . import config      →  LOAD_CONST 1 (level)   LOAD_CONST ('config',)  IMPORT_NAME ''
from .cli import main     →  LOAD_CONST 1 (level)   LOAD_CONST ('main',)    IMPORT_NAME 'cli'
import sys                →  LOAD_CONST 0 (level)   LOAD_CONST None         IMPORT_NAME 'sys'
```

점 개수가 곧 `level` 이고, `level == 0` 이 절대 임포트입니다. `level > 0` 이면
`importlib._bootstrap.__import__` 가 기준점을 계산합니다.

```python
if level == 0:
    module = _gcd_import(name)
else:
    globals_ = globals if globals is not None else {}
    package = _calc___package__(globals_)      # ← 여기
    module = _gcd_import(name, package, level)
```

`_calc___package__` 는 모듈 전역의 `__package__` 를 먼저 보고, 없으면 `__spec__.parent`
로 떨어집니다. 그렇게 얻은 패키지 이름을 `_resolve_name` 이 점 개수만큼 잘라 절대
이름을 만듭니다.

```python
def _resolve_name(name, package, level):
    bits = package.rsplit('.', level - 1)
    if len(bits) < level:
        raise ImportError('attempted relative import beyond top-level package')
    base = bits[0]
    return f'{base}.{name}' if name else base
```

`budget_app/cli/app.py` 는 `__package__ == "budget_app.cli"` 이므로(3.13.1 에서 확인),
`from ..context import AppContext`(level 2)는 `rsplit('.', 1)` → `["budget_app", "cli"]`
→ base `"budget_app"` → 최종 `budget_app.context` 로 풀립니다.

**이 소스에서** — 내부 참조는 전부 상대, 표준 라이브러리는 전부 절대입니다.

budget_app/cli/app.py:13-24
```python
from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from pathlib import Path

from ..context import AppContext
from . import config, handlers, output
from . import parser as parser_module
from .error_handler import handle_errors
```

**없으면 어떻게 되나** — 절대 임포트(`from budget_app.context import AppContext`)로
바꾸면 동작 자체는 같지만, 최상위 패키지 이름을 바꿀 때 **패키지 내부 임포트가 있는 31개 파일**을 고쳐야 합니다(나머지 12개는 상대 임포트가 한 줄도 없어 영향을 받지 않습니다 — `errors.py`, 각 계층의 `config.py`·`messages.py`, `__init__.py` 계열).
반대로 `level` 이 패키지 깊이보다 크면 위 `_resolve_name` 이
`"attempted relative import beyond top-level package"` 로 즉시 막습니다.

#### `import a as b` — 이름 하나만 바꾸는 문법

**어디서 왔나** — `as` 절은 파이썬 2 시절부터 있던 import 문법의 일부입니다. 하는 일은
"import 한 객체를 어느 지역 이름에 묶을 것인가"를 바꾸는 것뿐이고, 모듈이 복제되거나
캐시(`sys.modules`)가 달라지지는 않습니다. 위 바이트코드에서 마지막 `STORE_NAME` 의
피연산자만 바뀝니다.

**이 소스에서** — 이 프로젝트에는 계층마다 `config.py` / `messages.py` 가 따로 있어서,
같은 파일 안에 두 개 이상이 들어오면 `as` 로 구분합니다.

budget_app/cli/parser.py:28-29
```python
from ..domain import config as domain_config
from ..services import config as services_config
```

budget_app/cli/app.py:23-23
```python
from . import parser as parser_module
```

이쪽은 이름 충돌이 아니라 **지역 변수와의 혼동**을 피한 경우입니다. 이 파일에서
`parser` 는 argparse 파서 객체를 담는 흔한 변수명이라, 모듈 쪽에 다른 이름을 줬습니다.

#### `__version__` 과 `__all__` — 문법이 아니라 관례입니다

**어디서 왔나** — 둘 다 파이썬 키워드가 아니라 **이름 규약**입니다. 앞뒤 밑줄 두 개는
"파이썬 생태계가 의미를 약속한 이름"이라는 표시일 뿐, 인터프리터가 특별 취급하는 것은
`__all__` **하나뿐**이고 그것도 딱 한 상황에서만입니다.

**내부에서 무슨 일이 일어나나** — `__all__` 은 `from 모듈 import *` 를 만났을 때
import 시스템이 "무엇을 별로 풀 것인가"를 정하는 목록입니다. `__all__` 이 없으면
밑줄로 시작하지 않는 모든 전역 이름이 새어 나갑니다. **`import 모듈` 이나
`from 모듈 import 이름` 에는 아무 영향도 주지 않습니다** — 자주 오해되는 지점입니다.
`__version__` 은 인터프리터가 전혀 모르는 이름이고, 읽는 쪽(사람·패키징 도구)만 봅니다.

**이 소스에서** — `__version__` 은 패키지 루트에, `__all__` 은 CLI 패키지에만 있습니다.

budget_app/cli/__init__.py:22-24
```python
from .app import main

__all__ = ["main"]
```

`__main__.py` 의 `from .cli import main` 이 성립하게 하는 것은 위의 **재수출 한 줄**이지
`__all__` 이 아닙니다. `__all__` 은 "이 패키지가 밖에 내보이는 공개 심볼은 `main`
하나"라는 **선언**의 역할입니다.

**없으면 어떻게 되나** — 이 프로젝트에는 `from ... import *` 가 한 곳도 없으므로 실행
동작은 전혀 달라지지 않습니다. 달라지는 것은 정적 검사입니다 — 린터는 `__all__` 에 적힌
이름을 "쓰이지 않지만 의도적으로 재수출한 것"으로 인정하는데, 이 줄이 없으면
`from .app import main` 이 **미사용 import 경고**로 잡힙니다.

### 1-A-2. 함수 시그니처와 인자

#### 키워드 전용 인자 `*`

**어디서 왔나** — **PEP 3102(Keyword-Only Arguments, 파이썬 3.0)** 가 도입했습니다.
그전에는 "이 인자는 반드시 이름을 붙여 부르게 한다"를 문법으로 강제할 방법이 없어서,
`**kwargs` 로 받아 함수 첫머리에서 직접 꺼내 검사하는 관용구를 썼습니다.

**무엇으로 풀리나** — 이것은 런타임 검사가 아니라 **함수 객체의 구조**입니다. 시그니처
안의 홀로 선 `*` 는 인자 목록을 두 구획으로 나누고, 컴파일러가 그 경계 뒤의 이름을
코드 객체의 `co_kwonlyargcount` 에 셈해 둡니다. 위치로 넘기려 하면 함수 본문에 진입하기
전에 `TypeError: ... takes N positional arguments but M were given` 이 납니다.

**이 소스에서** — 이 프로젝트에서 `*` 뒤로 넘어간 인자는 예외 없이 **bool 플래그이거나
동작을 바꾸는 옵션**입니다. 호출부만 봐도 뜻이 읽히게 만드는 것이 목적입니다.

budget_app/storage/jsonl.py:264-269
```python
    def plan_rewrite(
        self,
        transform: Callable[[T], T | None],
        *,
        extra: Iterable[T] = (),
    ) -> RewritePlan:
```

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

budget_app/storage/csv_io.py:131-131
```python
def write_transactions(path: Path, txs: Iterable[Transaction], *, include_id: bool = True) -> int:
```

budget_app/services/transactions.py:89-91
```python
    def _require_registered_category(self, name: str, *, hint: str) -> None:
        if not self.cats.exists(name):
            raise AppError(messages.ERR_CATEGORY_NOT_REGISTERED.format(name=name), hint=hint)
```

마지막 것은 bool 이 아닌데도 키워드 전용입니다. 이 메서드는 호출처가 둘인데 각각 다른
힌트 문구를 넘깁니다 — `add` 는 `HINT_CATEGORY_ADD_OR_LIST`, `update` 는
`HINT_CATEGORY_ADD` 입니다(transactions.py:37, 60). 두 문자열 인자(`name`, `hint`)가
나란히 위치 인자로 서 있으면 순서를 바꿔 써도 타입 오류가 나지 않고 **엉뚱한 문구가
사용자에게 나갑니다**. `*` 가 그 실수를 문법 차원에서 없앱니다.

**없으면 어떻게 되나** — `import_csv(path, True, "skip")` 같은 호출이 합법이 됩니다.
읽는 사람은 `True` 가 무엇인지 알 수 없고, 나중에 인자 순서를 바꾸는 리팩터가 **오류
없이 의미만 뒤집는** 변경이 됩니다. `*` 가 있으면 그 리팩터는 호출부를 건드릴 필요조차
없습니다.

#### `*args` / `**kwargs` — 시그니처를 모르는 채로 넘기기

**어디서 왔나** — 파이썬 초기부터 있던 가변 인자 문법입니다. `*args` 는 남은 위치
인자를 **튜플**로, `**kwargs` 는 남은 키워드 인자를 **딕셔너리**로 모읍니다. 호출 쪽에
쓰면 반대로 **펼칩니다**.

**이 소스에서** — 데코레이터 세 개가 전부입니다. 데코레이터는 자기가 감쌀 함수의
시그니처를 알 수 없으므로, 받은 것을 그대로 흘려보내는 것 말고는 방법이 없습니다.

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

같은 형태가 `measure_time`(decorators.py:57-64)과
`handle_errors.wrapper`(cli/error_handler.py:47-52)에 있습니다.

한 곳만 성격이 다릅니다.

budget_app/domain/queries.py:74-78
```python
    @classmethod
    def for_month(cls, month: str, **extra: Any) -> SearchFilter:
        """월 전체를 덮는 필터 — 요약과 내보내기가 같은 경계를 쓰게 한다."""
        start, end = month_range(month)
        return cls(date_from=start, date_to=end, **extra)
```

여기서 `**extra` 는 "`date_from`/`date_to` 는 내가 정하고, **나머지 검색 조건은 그대로
전달**한다"는 뜻입니다. `SearchFilter` 에 필드를 추가해도 이 메서드는 고칠 필요가
없습니다.

**없으면 어떻게 되나** — `wrapper(*args, **kwargs)` 대신 구체적 시그니처를 적으면
데코레이터가 특정 모양의 함수에만 붙습니다. `@log_call` 은 인자 개수가 서로 다른
`TransactionService.add`/`update`/`delete` 셋에 붙어 있으므로(transactions.py:27, 52,
72) 곧바로 깨집니다.

#### `**{**a, **b}` — 언패킹 일반화와 "뒤가 이긴다"

**어디서 왔나** — **PEP 448(Additional Unpacking Generalizations, 파이썬 3.5)** 입니다.
그전에는 딕셔너리 리터럴 안에 `**` 를 쓸 수 없었고, 한 호출에 `**` 를 두 번 쓰는 것도
안 됐습니다. 병합하려면 임시 변수를 만들어 `d = dict(a); d.update(b)` 처럼 두 문장으로
써야 했습니다.

**무엇으로 풀리나** — 3.13.1 에서 `Transaction.with_patch` 의 본문을 디스어셈블한
결과입니다.

```
LOAD_GLOBAL   Transaction
LOAD_CONST    ()               ← 위치 인자 없음
BUILD_MAP     0                ← 바깥 {} : 호출에 넘길 kwargs 딕셔너리
BUILD_MAP     0                ← 안쪽 {} : 병합 결과를 담을 새 딕셔너리
  self.to_dict()          → DICT_UPDATE 1
  patch.changed_fields()  → DICT_UPDATE 1
DICT_MERGE    1
CALL_FUNCTION_EX 1
```

읽어야 할 것이 셋 있습니다.

- **새 딕셔너리가 만들어집니다.** `BUILD_MAP 0` 으로 빈 dict 를 만든 뒤 두 소스를
  차례로 `DICT_UPDATE` 합니다. 원본 두 개는 건드리지 않습니다.
- **"뒤가 이긴다"는 `dict.update` 의 의미 그 자체입니다.** 왼쪽부터 순서대로
  `update` 하므로, 같은 키가 있으면 나중에 update 된 값이 앞의 값을 덮어씁니다.
  파이썬 3.7 부터 딕셔너리의 **삽입 순서 보존**이 언어 명세이므로 이 순서는 우연이
  아니라 보장된 동작입니다.
- `DICT_MERGE` 는 `DICT_UPDATE` 와 달리 **키 중복을 허용하지 않습니다**. 함수 호출의
  키워드 인자를 만드는 자리라, 같은 이름이 두 번 오면
  `got multiple values for keyword argument` 를 내야 하기 때문입니다.

**이 소스에서** — 부분 수정을 적용해 새 엔티티를 만드는 한 줄입니다.

budget_app/domain/entities.py:113-124
```python
    def with_patch(self, patch: TransactionPatch) -> Transaction:
        """부분 변경을 적용한 **새 Transaction** 을 만든다.

        수정이 도메인 연산인 이유: 이전에는 저장소가
        ``to_dict() → dict.update(changes) → from_dict()`` 를 수행했다. 즉
        "무엇으로 바꿀지 해석하고 규칙을 다시 적용하는" 도메인 작업이 파일 계층에
        있었다. 이제 저장소는 완성된 객체를 받아 쓰기만 한다.

        새 객체를 만드는(제자리 수정이 아닌) 이유: ``__post_init__`` 을 다시 통과
        시켜 변경 후에도 불변식이 성립함을 생성자가 보장하게 하기 위해서다.
        """
        return Transaction(**{**self.to_dict(), **patch.changed_fields()})
```

한 줄을 풀면 이렇습니다 — **일반론 예시(이 소스에는 이 형태로 적혀 있지 않습니다)**.

```python
merged = {}
merged.update(self.to_dict())            # 현재 값 전부 (7개 필드)
merged.update(patch.changed_fields())    # None 이 아닌 필드만 → 덮어쓰기
return Transaction(id=merged["id"], type=merged["type"], ...)   # 키워드로 펼침
```

이 식이 성립하려면 **`to_dict()` 의 키와 `Transaction.__init__` 의 파라미터 이름이 정확히
같아야** 합니다(entities.py:89-97 과 60-66). 그리고 `changed_fields()` 가 `None` 인
필드를 버리기 때문에(entities.py:144-150) "변경 없음"이 자동으로 "원래 값 유지"가 됩니다.

budget_app/domain/entities.py:144-150
```python
    def changed_fields(self) -> dict[str, Any]:
        """``None`` 이 아닌 필드만 골라 dict 로 준다."""
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if getattr(self, f.name) is not None
        }
```

**없으면 어떻게 되나** — 두 방향으로 깨집니다.

- 순서를 뒤집어 `{**patch.changed_fields(), **self.to_dict()}` 로 쓰면 **원본이 패치를
  덮어써서** 수정이 조용히 무시됩니다. 오류가 나지 않는 부류라 가장 위험합니다.
- `**` 를 쓰지 않고 7개 필드를 손으로 적으면, `Transaction` 에 필드를 하나 추가할 때
  이 줄을 고치는 것을 빠뜨리는 순간 그 필드가 수정 때마다 기본값으로 리셋됩니다.

참고로 파이썬 3.9 부터는 `a | b` 로도 딕셔너리를 병합할 수 있습니다(PEP 584).
**일반론 예시 — 이 소스에는 없습니다.** 이 소스가 `{**a, **b}` 를 쓰는 이유는 결과를
곧바로 `**` 로 다시 펼쳐야 해서 한 식 안에 두 연산이 붙는 편이 짧기 때문입니다.

#### 기본값 인자는 **정의 시점에 한 번** 평가됩니다

**어디서 왔나** — 문법이라기보다 파이썬의 실행 모델입니다. `def` 문을 실행할 때 기본값
식이 **그 자리에서 한 번** 계산되어 함수 객체의 `__defaults__` / `__kwdefaults__` 에
저장됩니다. 호출할 때마다 다시 계산되지 않습니다. 그래서 `def f(x=[])` 는 **모든
호출이 같은 리스트 하나를 공유**하는 유명한 함정이 됩니다.

**이 소스에서** — 이 프로젝트는 가변 기본값을 두 가지 방식으로 피합니다.

첫째, **`None` 을 센티널로 쓰고 안에서 만듭니다.**

budget_app/services/transactions.py:27-36
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
    ) -> Transaction:
```

여기서 `tags=None` 은 `Transaction.__post_init__` → `validators.parse_tags` 로 흘러가고,
그 함수의 첫 줄이 `None` 을 빈 리스트로 바꿉니다.

budget_app/domain/validators.py:149-150
```python
    if value is None:
        return []
```

`return []` 이 **함수 본문 안**에 있다는 점이 전부입니다. 호출할 때마다 새 리스트가
만들어집니다.

둘째, **불변 기본값을 씁니다.**

budget_app/storage/jsonl.py:264-269
```python
    def plan_rewrite(
        self,
        transform: Callable[[T], T | None],
        *,
        extra: Iterable[T] = (),
    ) -> RewritePlan:
```

같은 형태가 `JsonlStore.rewrite`(jsonl.py:313-318)와
`UnitOfWork.stage`(storage/unit_of_work.py:92-98)에도 있습니다. 빈 튜플 `()` 은
불변이라 **공유되어도 안전**합니다. 게다가 CPython 은 빈 튜플을 싱글턴으로 캐시하므로
비용도 0 입니다. 실제로 `extra` 는 읽기만 됩니다.

budget_app/storage/jsonl.py:304-307
```python
        extra_lines = [self._encode(e) for e in extra]
        if extra_lines:
            changed = True
        lines.extend(extra_lines)
```

같은 원리가 엔티티 필드에도 적용됩니다 — `Transaction.tags` 의 기본값이
`[]` 가 아니라 `()` 입니다.

budget_app/domain/entities.py:65-66
```python
    memo: str = ""
    tags: tuple[str, ...] = ()
```

`dataclass` 는 리스트나 딕셔너리를 필드 기본값으로 주면 아예 `ValueError` 로 막고
`field(default_factory=...)` 를 쓰라고 요구합니다. 튜플은 불변이므로 그 검사를 그냥
통과합니다.

**없으면 어떻게 되나** — `extra: Iterable[T] = []` 로 썼다면, 어딘가에서 실수로
`extra.append(...)` 를 한 순간 그 원소가 **프로그램이 끝날 때까지 모든 후속 호출에
따라붙습니다**. 관련 없는 명령의 저장 결과에 남의 레코드가 섞이는 종류의 버그이고,
재현 조건이 "앞서 어떤 명령을 실행했는가"라 추적이 매우 어렵습니다.

### 1-A-3. 문자열과 포맷

#### f-string / `str.format` / %-포맷 — 셋이 나뉜 이유

**어디서 왔나** — 세 문법은 도입 순서대로 세 세대입니다.

| 방식 | 근거 | 특징 |
|---|---|---|
| `"%s" % x` | 파이썬 초기부터 (C 의 `printf` 계승) | 튜플 하나만 받음, 표현력 제한 |
| `"{}".format(x)` | **PEP 3101**, 파이썬 2.6 부터 | 이름 있는 필드, 템플릿을 변수로 분리 가능 |
| `f"{x}"` | **PEP 498**, 파이썬 3.6 | 식을 자리에 직접 적음, 가장 빠름 |

새 것이 옛 것을 완전히 대체하지 못한 이유는 **평가 시점이 다르기** 때문입니다.
f-string 은 그 줄을 만나는 순간 문자열이 **완성**되고, `str.format` 은 템플릿과 데이터를
떼어 놓을 수 있으며, `logging` 의 %-스타일은 **끝까지 안 만들 수도 있습니다.**

**이 소스에서** — 셋의 분업이 명확하고, 그 규칙이 문서화까지 되어 있습니다.

**(1) `str.format` — 사용자에게 나가는 모든 문구.** 문구를 `messages.py` 로 몰아
넣으려면 템플릿이 **문자열 상수**여야 하는데, f-string 은 정의 지점에서 곧바로
평가되므로 상수가 될 수 없습니다. 이 프로젝트가 `str.format` 을 버리지 않은 유일하고
결정적인 이유입니다.

budget_app/cli/messages.py:42-43
```python
MSG_NO_DATA = "(데이터 없음)"
FMT_TX_LINE = "{id} | {date} | {type:<7} | {category} | {amount} | {memo}"
```

budget_app/cli/presenter.py:31-39
```python
def tx_line(tx: Transaction) -> str:
    return messages.FMT_TX_LINE.format(
        id=tx.id,
        date=tx.date,
        type=tx.type,
        category=tx.category,
        amount=tx.amount,
        memo=tx.memo,
    )
```

**(2) f-string — 값을 즉시 합치는 내부 계산.** 사용자 문구가 아니라 경로·이름·repr 을
만드는 자리입니다.

budget_app/storage/config.py:10-11
```python
# 로거 — 저장소 로그만 따로 조정할 수 있게 앱 로거의 자식으로 둔다
LOGGER_NAME = f"{app_config.LOGGER_NAME}.storage"
```

budget_app/storage/backup.py:28-29
```python
    ts = (now or datetime.now()).strftime(config.BACKUP_TS_FORMAT)
    dest = src.parent / f"{config.BACKUP_DIR_PREFIX}{ts}"
```

budget_app/domain/specs.py:181-182
```python
    def __repr__(self) -> str:
        return f"DateFrom({self.value!r})"
```

**(3) %-포맷 — `logging` 전용.** 이 소스의 %-표기는 전부 로그입니다. 두 종류가 있는데
서로 다른 자리에서 쓰입니다.

budget_app/decorators.py:28-32
```python
#: 이 세 문구는 이 모듈만 쓴다. 별도 messages 파일로 빼면 3줄짜리 파일이 생기고
#: 오히려 찾기 어려워진다. %-스타일인 이유는 logging 의 지연 포맷팅 때문이다.
LOG_CALL = "call %s"
LOG_DONE = "done %s"
LOG_TOOK = "%s took %.2fms"
```

budget_app/cli/messages.py:15-18
```python
# 로그 포맷 (%-스타일)
LOG_FORMAT = "[%(levelname)s] %(message)s"
LOG_FORMAT_DEBUG = "[%(levelname)s] %(asctime)s %(name)s:%(lineno)d %(message)s"
LOG_UNHANDLED = "unhandled error"
```

앞의 셋은 **로그 메시지 본문**의 템플릿이고, 뒤의 둘은 **핸들러가 한 줄을 조립하는**
템플릿입니다. 뒤쪽이 이름 있는 필드(`%(levelname)s`)를 쓰는 것은 `logging.Formatter` 의
기본 스타일이 `'%'` 이고 그 구현이 딕셔너리 하나를 넘기기 때문입니다. 3.13.1 의
`logging.PercentStyle._format` 입니다.

```python
    def _format(self, record):
        if defaults := self._defaults:
            values = defaults | record.__dict__
        else:
            values = record.__dict__
        return self._fmt % values
```

**내부에서 무슨 일이 일어나나 — 왜 `logger.debug(LOG_CALL, name)` 이지
`logger.debug(LOG_CALL % name)` 이 아닌가.** `Logger.debug` 는 `isEnabledFor(DEBUG)` 가
거짓이면 그 자리에서 반환하고, `%` 결합은 핸들러가 출력 직전에 부르는
`LogRecord.getMessage` 안에서만 일어납니다. 두 구현의 실제 소스는 §2-B 의
「지연 포매팅」 항목에 줄 번호와 함께 인용해 두었으므로 여기서는 반복하지 않습니다.

즉 템플릿과 인자를 **따로** 넘기면, 레벨이 꺼져 있을 때 `LogRecord` 조차 만들어지지
않고 `%` 연산도 일어나지 않습니다. 이 프로젝트의 로그는 기본이 WARNING 이므로
(cli/output.py:94-99) **`@log_call` 과 `@measure_time` 의 DEBUG 로그는 평상시 문자열
포매팅을 단 한 번도 수행하지 않습니다.**

budget_app/decorators.py:40-45
```python
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(LOG_CALL, func.__name__)
        result = func(*args, **kwargs)
        logger.debug(LOG_DONE, func.__name__)
        return result
```

**없으면 어떻게 되나** — `logger.debug(f"call {func.__name__}")` 로 바꾸면 f-string 은
`debug` 를 **부르기 전에** 이미 완성됩니다. `isEnabledFor` 가 `False` 를 돌려줘도 문자열은
이미 만들어진 뒤입니다. `@log_call` 이 붙은 서비스 메서드가 호출될 때마다, 아무도 보지
않을 문자열을 두 개씩 만드는 셈이 됩니다. 반대로 사용자 문구를 f-string 으로 바꾸면
`messages.py` 라는 파일 자체가 성립하지 않습니다 — 상수로 저장할 수 없기 때문입니다.

#### 포맷 스펙 미니 언어와 `__format__` / `__str__` / `__repr__`

**어디서 왔나** — 중괄호 안 콜론 뒤의 문자열(`{:06d}` 의 `06d`)은 **PEP 3101** 이 정의한
별도의 미니 언어입니다. `str.format` 과 f-string 이 같은 규칙을 공유합니다. 문법은
`[[fill]align][sign][#][0][width][,][.precision][type]` 이고, `!r` 같은 **변환(conversion)**
은 콜론 앞에 붙으며 포맷 스펙보다 **먼저** 적용됩니다.

**무엇으로 풀리나 — 호출 순서.** 자리 하나를 채울 때 파이썬이 하는 일은 셋입니다.

1. `!r` / `!s` / `!a` 가 있으면 각각 `repr()` / `str()` / `ascii()` 를 먼저 적용하고,
   **그 결과 문자열**을 다음 단계로 넘깁니다.
2. `format(값, 스펙)` 을 호출합니다. 이것은 `type(값).__format__(값, 스펙)` 입니다.
3. `object.__format__` 은 스펙이 **비어 있으면** `str(self)` 를 돌려주고, 스펙이 있으면
   `TypeError` 를 냅니다.

그래서 **불리는 것은 언제나 `__format__` 이고, `__str__`/`__repr__` 은 그 안에서
간접적으로 불립니다.** 3.13.1 에서 확인한 결과입니다.

```
class C:  __str__ → 'STR',  __repr__ → 'REPR'
"{}".format(c)  → 'STR'      # object.__format__ 이 str() 로 위임
"{!r}".format(c) → 'REPR'    # 변환이 먼저
```

**이 소스에서 — 네 가지 스펙.**

**`{:06d}`** — `0` 은 "부호를 인식하는 0 채움", `6` 은 최소 폭, `d` 는 10진 정수입니다.

budget_app/domain/config.py:24-27
```python
# 거래 ID — 형식·검증·발굴 세 패턴이 값 객체(tx_id.TransactionId)와 짝을 이룬다
TX_ID_PATTERN = r"^TX-(\d+)$"
TX_ID_FORMAT = "TX-{:06d}"
TX_ID_SCAN_PATTERN = r'"id"\s*:\s*"(TX-\d+)"'
```

이 상수는 두 곳에서 쓰입니다. 하나는 번호로 새 id 를 만드는 자리이고,

budget_app/domain/tx_id.py:99-102
```python
    @classmethod
    def of(cls, number: int) -> TransactionId:
        """번호로부터 만든다 — ``7`` → ``TX-000007``."""
        return cls(config.TX_ID_FORMAT.format(number))
```

다른 하나는 **이미 존재하는 id 를 정규형으로 다시 찍는** 자리입니다.

budget_app/domain/tx_id.py:83-89
```python
    def __post_init__(self) -> None:
        # frozen dataclass 라 object.__setattr__ 로 정규화한다.
        v = str(self.value or "").strip()
        m = _EXACT.match(v)
        if not m:
            raise ValidationError(messages.ERR_TX_ID_INVALID.format(value=v))
        object.__setattr__(self, "value", config.TX_ID_FORMAT.format(int(m.group(1))))
```

`d` 는 정수 전용이라, 문자열을 그대로 넘기면 3.13.1 기준
`ValueError: Unknown format code 'd' for object of type 'str'` 가 납니다. 그래서
`int(m.group(1))` 로 한 번 정수화한 뒤 다시 찍습니다 — 이 왕복이 `TX-1` 과 `TX-000001`
을 같은 값으로 만듭니다(3.13.1 에서 `TransactionId('TX-1')` → `TX-000001` 확인).

**`{:<7}`** — `<` 는 왼쪽 정렬, `7` 은 최소 폭입니다. 문자열은 원래 왼쪽 정렬이
기본이지만, 여기서는 **폭 7 을 주기 위해** 정렬 기호를 명시했습니다.

budget_app/cli/messages.py:43-43
```python
FMT_TX_LINE = "{id} | {date} | {type:<7} | {category} | {amount} | {memo}"
```

값이 `"income"`(6자) 아니면 `"expense"`(7자)뿐이므로, 폭 7 이면 `income` 뒤에 공백 하나가
붙어 두 경우의 열 시작 위치가 정확히 같아집니다. 3.13.1 에서 확인:
`"{:<7}".format("income")` → `'income '`.

**`{:02d}`** — 같은 규칙의 폭 2 판입니다.

budget_app/domain/periods.py:27-30
```python
    normalized = validators.parse_month(month)
    dt = datetime.strptime(normalized, config.MONTH_FORMAT)
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return f"{normalized}-01", f"{normalized}-{last_day:02d}"
```

`calendar.monthrange` 가 주는 말일은 `28`~`31` 이라 두 자리 같지만, 이 프로젝트는
**날짜를 문자열로 비교**합니다. 폭을 고정하지 않으면 언젠가 한 자리 값이 섞였을 때
`"2024-02-9" <= "2024-02-28"` 이 `False` 가 되어 조회에서 조용히 빠집니다.

**`{!r}`** — `repr()` 변환입니다. `specs.py` 의 모든 `__repr__` 이 씁니다.

budget_app/domain/specs.py:181-182
```python
    def __repr__(self) -> str:
        return f"DateFrom({self.value!r})"
```

`{self.value}` 였다면 `DateFrom(2024-01-01)` 이 나옵니다. `{self.value!r}` 이면
`DateFrom('2024-01-01')` 이 되어, **그 값이 문자열이라는 사실**이 출력에 남고 그대로
소스에 붙여 넣을 수 있는 형태가 됩니다.

**없으면 어떻게 되나** — `TransactionId` 가 `__str__` 을 갖지 않았다면(tx_id.py:126-127)
거래 목록 한 줄이 이렇게 나옵니다. 3.13.1 에서 확인한 결과입니다.

```
TransactionId(value='TX-000001') | 2024-01-05 | expense | food | 12000 |
```

`@dataclass` 가 만들어 주는 것은 `__repr__` 뿐이고 `__str__` 은 만들지 않습니다.
`object.__str__` 은 `__repr__` 로 위임하므로, `FMT_TX_LINE` 의 빈 스펙 `{id}` 가
데이터클래스 repr 을 그대로 화면에 쏟아 냅니다. `tx_id.py` 의 두 줄짜리 `__str__` 이
값 객체를 "경계에서 원시 값으로 푸는" 마지막 장치입니다.

budget_app/domain/tx_id.py:126-127
```python
    def __str__(self) -> str:
        return self.value
```

덧붙이면 `TransactionId` 는 `__format__` 을 정의하지 않으므로, 스펙이 붙은
`{id:>10}` 같은 표기는 3.13.1 에서
`TypeError: unsupported format string passed to TransactionId.__format__` 로 막힙니다.
`FMT_TX_LINE` 이 `{id}` 를 빈 스펙으로 둔 것은 그래서 필수 조건입니다.

#### 문자열 메서드 — `strip` / `lower` / `split` / `join`

**어디서 왔나** — 전부 `str` 의 내장 메서드이며 파이썬 초기부터 있는 기본
어휘입니다. 넷 다 **원본을 바꾸지 않고 새 문자열(또는 리스트)을 돌려줍니다** — 파이썬
문자열이 불변이기 때문입니다.

**이 소스에서** — 넷의 역할이 뚜렷하게 갈립니다.

**`strip()` — 정규화의 첫 동작.** `validators` 의 모든 파서가 같은 첫 줄로 시작합니다.

budget_app/domain/validators.py:116-120
```python
def parse_category(value: Any) -> str:
    v = str(value or "").strip()
    if not v:
        raise ValidationError(messages.ERR_CATEGORY_EMPTY)
    return v
```

`str(value or "")` 라는 관용구도 함께 봐야 합니다. `value` 가 `None` 이면 `or` 가 빈
문자열로 떨어뜨리므로, `None.strip()` 에서 `AttributeError` 가 나는 대신 "빈 값" 이라는
도메인 오류로 처리됩니다.

**`lower()` — 대소문자 무시가 정책인 자리에만.** 소스 전체에서 두 곳뿐입니다.

budget_app/domain/validators.py:73-77
```python
def parse_type(value: Any) -> str:
    v = str(value or "").strip().lower()
    if v not in config.VALID_TYPES:
        raise ValidationError(messages.ERR_TYPE_INVALID.format(types=config.VALID_TYPES))
    return v
```

budget_app/cli/output.py:74-76
```python
def _env_debug() -> bool:
    value = os.environ.get(config.DEBUG_ENV_VAR, "").strip().lower()
    return value not in config.FALSY_ENV_VALUES
```

거래 타입(`Income` → `income`)과 환경변수 값(`FALSE` → `false`)은 대소문자를 구분하지
않는 것이 맞습니다. 반대로 **카테고리명과 태그에는 `lower()` 를 쓰지 않습니다** — 사용자가
정한 이름이라 원래 표기를 지키는 것이 맞기 때문입니다. 이 비대칭이 의도적이라는 점이
구술에서 물어보기 좋은 대목입니다.

**`split()` / `join()` — 태그 한 칸의 왕복.** 둘은 정확히 역연산 관계로 쓰입니다.

budget_app/domain/validators.py:151-152
```python
    if isinstance(value, str):
        items: Iterable[Any] = value.split(config.TAG_SEPARATOR)
```

budget_app/storage/csv_io.py:157-158
```python
        "memo": tx.memo,
        "tags": domain_config.TAG_SEPARATOR.join(tx.tags),
```

여기서 중요한 것은 양쪽 모두 **같은 상수 `domain_config.TAG_SEPARATOR` 를 쓴다**는
점입니다. 구분자가 도메인 소유이고 CSV 는 빌려 씁니다(domain/config.py:17-18).

`join` 은 사용자 안내에도 쓰입니다.

budget_app/cli/prompts.py:104-107
```python
        raise ValidationError(
            service_messages.ERR_CATEGORY_NOT_REGISTERED.format(name=name)
            + messages.FMT_AVAILABLE_SUFFIX.format(available=", ".join(cat_service.list_names()))
        )
```

**참고 — `startswith` 는 지금 이 소스에 없습니다.** 두 docstring 에만 흔적으로
남아 있습니다(services/budgets.py:35, domain/periods.py:4). 이전에는 "이 달에 속하는가"를
`date.startswith(month + "-")` 로 판정했는데, 같은 개념이 CLI 와 서비스에 서로 다른
알고리즘으로 구현돼 있어서 `domain/periods.month_range` 하나로 합쳤습니다.

**없으면 어떻게 되나** — `strip()` 하나가 빠지면 `" food "` 와 `"food"` 가 서로 다른
카테고리가 되어 참조 무결성이 깨집니다. 실제로 `CategoryService.remove` 의 docstring 이
"정규화 시점이 다르면 가드는 언제든 우회된다"며 그 사고 사례를 기록해
두었습니다(services/categories.py:46-59).

#### raw 문자열 `r"..."` 과 정규식 — `\d` 와 `[0-9]`

**어디서 왔나** — raw 문자열 접두어 `r` 은 **백슬래시 이스케이프 해석을 끄는** 문자열
리터럴입니다. 정규식 자체가 백슬래시를 문법으로 쓰기 때문에, raw 가 없으면 파이썬
문자열 단계와 정규식 단계에서 백슬래시가 **두 번 소비**됩니다(`"\\d"` 를 써야 `\d` 가
전달됨). 그래서 `re` 문서가 정규식 패턴에 raw 문자열을 권장합니다.

**이 소스에서** — raw 문자열로 쓰인 정규식은 셋입니다. 아래 블록의 `TX_ID_PATTERN` 과 `TX_ID_SCAN_PATTERN`, 그리고 `domain/validators.py:37` 의 `_INTEGER` 입니다. 가운데 낀 `TX_ID_FORMAT` 은 raw 도 정규식도 아닌 `str.format` 용 형식 문자열이라는 점에 주의하세요 — 이름이 비슷해 셋을 셀 때 잘못 짚기 쉽습니다.

budget_app/domain/config.py:25-27
```python
TX_ID_PATTERN = r"^TX-(\d+)$"
TX_ID_FORMAT = "TX-{:06d}"
TX_ID_SCAN_PATTERN = r'"id"\s*:\s*"(TX-\d+)"'
```

`TX_ID_SCAN_PATTERN` 만 **작은따옴표 raw** 인 것도 이유가 있습니다. 패턴 안에 JSON 의
큰따옴표가 들어 있어서, 큰따옴표로 감쌌다면 안쪽을 전부 이스케이프해야 했습니다.
`\s*` 는 `"id" : "TX-..."` 처럼 콜론 주위에 공백이 있어도 걸리게 합니다 — JSON 파싱이
실패한 손상된 줄에서 id 만 건져 내는 용도라(tx_id.py:109-117) 관대해야 맞습니다.

budget_app/domain/tx_id.py:44-48
```python
#: 전체가 이 형식이어야 한다 — 검증용
_EXACT = re.compile(config.TX_ID_PATTERN)

#: 줄 어딘가에 있으면 된다 — JSON 이 깨진 줄에서 id 만 건져낼 때
_SCAN = re.compile(config.TX_ID_SCAN_PATTERN)
```

`re.compile` 을 모듈 수준에서 한 번만 하는 것도 의도된 선택입니다. `re.match(pattern, s)`
를 매번 부르면 내부 캐시를 조회하는 비용이 매 호출 붙는데, `TransactionId.__post_init__`
은 **파일에서 읽는 모든 거래마다** 실행되는 경로입니다.

**`\d` 와 `[0-9]` 의 차이는 §2-A 에서 따로 다룹니다.** 요약하면, 파이썬 3 의 `str`
정규식에서 `\d` 는 **유니코드 전체의 십진 숫자**(아라비아-인도 숫자 `١٢٣` 포함)이고
`[0-9]` 는 ASCII 다섯 문자 범위뿐입니다. 그래서 금액 검증기
`_INTEGER`(domain/validators.py:36-37)는 의도적으로 `[0-9]` 를 쓰고, 그 판정을
`parse_amount`(domain/validators.py:64-70)가 `int()` 보다 **먼저** 수행합니다.
3.13.1 에서 그 함수를 직접 호출한 결과만 여기 옮겨 둡니다.

| 입력 | `int()` 단독 | `parse_amount` |
|---|---|---|
| `"1_000"` | `1000` | `ValidationError` (금액은 정수여야 합니다) |
| `"١٢٣"` | `123` | `ValidationError` |
| `"+100"` | `100` | `100` (부호는 허용) |

`"1_000"` 이 특히 위험합니다. 오타 `"1_00"` 이 `int()` 로는 `100` 이 되어 **오류 없이
0 이 하나 사라진 금액**이 저장됩니다(`int()` 가 밑줄 구분자를 받아 주는 것은 PEP 515
입니다). 정규식이 이 표기를 먼저 거부하므로 그 경로가 막힙니다. 같은 소스인데
`TX_ID_PATTERN` 은 `\d` 를 쓰는 이유 — "정규화가 뒤따르는 패턴은 관대해도 무해하다"는
대조 — 도 §2-A 의 같은 항목에 있습니다.

**없으면 어떻게 되나** — `_INTEGER` 를 `\d` 로 바꿨을 때 벌어지는 일은 §2-A 에서 다루므로,
여기서는 이 항목의 주제인 raw 접두어만 봅니다. `r` 을 빼면 문제가 두 단계로 나뉩니다. `\d` 는 파이썬이 아는 이스케이프가
아니라 지금은 백슬래시가 그대로 남지만, 3.13.1 에서 확인한 대로
`SyntaxWarning: invalid escape sequence '\d'` 가 뜹니다(장래 버전에서 오류가 될
예정이라는 예고입니다). 더 위험한 것은 `"\s"`·`"\b"` 처럼 **파이썬이 아는 조합**입니다 —
`"\b"` 는 문자열 단계에서 백스페이스 문자(U+0008)로 바뀌어 버려서, 정규식 엔진은
"단어 경계" 대신 제어 문자를 찾게 됩니다. 오류 없이 패턴의 의미만 바뀌는 부류입니다.

---

## 1-B. 클래스, dataclass, 특수 메서드, 연산자 오버로딩

> **이 절은 무엇인가** — "거래 한 건"처럼 이 프로그램이 다루는 대상을 코드 안에서 어떻게 한 덩어리로 만들어 두는지를 다룹니다. 한 번 만든 거래를 그 뒤로는 아무도 고치지 못하게 잠그는 방법, 두 거래가 같은 것인지 판단하는 규칙, 검색 조건 여러 개를 기호로 이어 붙여 하나의 조건으로 만드는 표기가 여기 있습니다. `domain/` 폴더를 읽다 막혔다면 대개 이 절에서 답이 나옵니다.

이 절은 `domain/` 폴더를 읽을 때 필요한 것 전부입니다. `@dataclass` 가 실제로 **문자열로 조립해 `exec` 하는** 소스 코드에서 출발해, `frozen=True` 가 덮어쓰는 메서드가 무엇인지, 그 때문에 `object.__setattr__` 관용구가 왜 꼼수가 아니라 표준인지, `frozen`+`eq` 조합이 만들어 주는 `__hash__` 에 `IdAllocator` 가 어떻게 의존하는지, 그리고 `Spec` 계열이 `and`/`or` 대신 `&`/`|` 를 빌려 쓸 수밖에 없는 **언어 구조상의 이유**까지 따라갑니다.

이 절의 실행 확인은 모두 로컬 **CPython 3.13.1** 에서 수행했습니다. "도입 버전"은 문서에 근거한 별개의 주장이고, "3.13 에서 이렇게 나왔습니다"는 실행 결과입니다. 둘을 섞지 않도록 표기를 구분합니다.

---

### `@dataclass`

**어디서 왔나** — PEP 557 로 제안되어 **파이썬 3.7** 에 표준 라이브러리 `dataclasses` 모듈로 들어왔습니다. 그 전에는 같은 일을 하려면 `__init__`/`__repr__`/`__eq__` 를 손으로 전부 쓰거나, `collections.namedtuple` 을 쓰거나(불변이고 튜플처럼 인덱싱돼서 필드를 늘리기 나쁩니다), 서드파티 `attrs` 를 설치해야 했습니다. 이 프로젝트는 표준 라이브러리만 쓰므로 `attrs` 는 애초에 선택지가 아닙니다.

> **💡 쉽게 말하면** — 같은 서식을 매번 손으로 채우는 대신, 필요한 칸 이름만 불러 주면 서류를 대신 작성해 주는 창구가 생긴 셈입니다. `@dataclass` 는 "이 자료에는 이런 칸들이 있다"만 적어 두면 그 칸들을 받아 채우는 절차, 내용을 보기 좋게 늘어놓는 절차, 두 장이 같은 내용인지 대조하는 절차를 알아서 만들어 붙입니다.
> 다만 이 비유는 대신 작성되는 것이 서류가 아니라 **파이썬 코드 그 자체**라는 점에서 깨집니다 — 바로 아래에서 보듯, 문자열로 조립한 소스를 진짜로 컴파일해 클래스에 붙입니다.

**무엇으로 풀리나** — 흔한 오해가 "데코레이터가 마법을 부린다"인데, 실제로는 훨씬 평범합니다. `dataclasses` 는 **메서드의 파이썬 소스 코드를 문자열로 조립한 뒤 `exec` 로 컴파일**해 클래스에 붙입니다. 3.13 기준으로 그 일을 하는 것은 `dataclasses._FuncBuilder` 이고, 핵심은 다음 두 줄입니다(`Lib/dataclasses.py`, `_FuncBuilder.add_fns_to_class`).

```python
txt = f"def __create_fn__({local_vars}):\n{fns_src}\n return {return_names}"
ns = {}
exec(txt, self.globals, ns)
fns = ns['__create_fn__'](**self.locals)
```

바깥 함수 `__create_fn__` 을 만들어 그 안에서 `__init__` 등을 정의하고, 즉시 호출해 함수 객체들을 돌려받는 구조입니다. 왜 이렇게 하냐면 **기본값·타입 애너테이션·`object` 같은 것을 전역 이름 조회가 아니라 클로저 변수로 붙잡아 두기 위해서**입니다. 그래서 생성된 코드에는 `__dataclass_dflt_memo__`, `__dataclass_type_id__`, `__dataclass_builtins_object__` 같은 충돌 불가능한 이름이 등장합니다.

`Transaction` 을 정의할 때 실제로 `exec` 에 넘어가는 소스를 뽑아 보면 이렇습니다(`_FuncBuilder.add_fns_to_class` 를 가로채 출력, 3.13.1).

```python
def __init__(self, id:__dataclass_type_id__, type:__dataclass_type_type__, ...,
             memo:__dataclass_type_memo__=__dataclass_dflt_memo__,
             tags:__dataclass_type_tags__=__dataclass_dflt_tags__) -> ...:
  __dataclass_builtins_object__.__setattr__(self,'id',id)
  __dataclass_builtins_object__.__setattr__(self,'type',type)
  ...
  __dataclass_builtins_object__.__setattr__(self,'tags',tags)
  self.__post_init__()
```

이 한 덩어리 안에 이 절에서 다룰 사실이 거의 다 들어 있습니다 — frozen 이라 대입 대신 `object.__setattr__` 을 쓴다, `__post_init__` 이 **맨 마지막**에 불린다, 기본값은 함수 기본 인자로 박힌다.

같은 방식으로 만들어진 `__eq__` 는 이렇게 생겼습니다(뒤의 `NotImplemented` 항목과 이어집니다).

```python
def __eq__(self,other):
  if self is other: return True
  if other.__class__ is self.__class__:
   return self.id==other.id and ... and self.tags==other.tags
  return NotImplemented
```

**이 소스에서** — `Transaction` 은 필드 일곱 개를 선언만 하고 생성자를 쓰지 않습니다.

budget_app/domain/entities.py:60-66
```python
    id: TransactionId
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: tuple[str, ...] = ()
```

`inspect.signature(Transaction.__init__)` 로 생성된 시그니처를 실제로 찍어 보면 이렇습니다.

```
(self, id: 'TransactionId', type: 'str', date: 'str', amount: 'int',
 category: 'str', memo: 'str' = '', tags: 'tuple[str, ...]' = ()) -> None
```

선언 순서가 그대로 위치 인자 순서가 되고, 기본값이 있는 두 필드가 뒤로 몰려 있어 문법 오류가 나지 않습니다(기본값 있는 필드를 없는 필드보다 앞에 두면 `dataclass` 가 `TypeError` 를 냅니다). 애너테이션이 문자열로 보이는 것은 이 파일 맨 위의 `from __future__ import annotations` 때문입니다.

이 프로젝트에서 `@dataclass` 를 쓰는 클래스는 모두 **15개**입니다(`grep -rn "@dataclass" budget_app --include=*.py` 로 전수 확인) — 도메인 엔티티(`Transaction`, `TransactionPatch`, `Budget`, `Category`), 결과 모델(`MonthlySummary`, `RejectedRow`, `DuplicateRow`, `ImportReport`), 값 객체(`TransactionId`), 질의 모델(`SearchFilter`), 저장 계층의 `RawLine`·`RewritePlan`·`ParsedRow`, 서비스의 `_Batch`, CLI 의 `TransactionInput` 입니다.

**없으면 어떻게 되나** — `Transaction` 하나만 손으로 쓰면 7개 필드에 대해 `__init__` 7줄, `__repr__` 1줄, `__eq__` 7항 비교, `__hash__` 7-튜플을 직접 적어야 하고, 필드를 하나 추가할 때마다 **네 곳**을 같이 고쳐야 합니다. 한 곳을 빠뜨려도 프로그램은 조용히 돌아갑니다 — 예를 들어 `__eq__` 에 `tags` 비교를 빠뜨리면 태그만 다른 두 거래가 같다고 판정됩니다. dataclass 는 그 동기화 실수를 구조적으로 없앱니다.

---

### `frozen=True`

**어디서 왔나** — PEP 557 의 옵션입니다(파이썬 3.7). 파이썬에는 원래 "이 객체는 불변" 을 선언하는 문법이 없고, 불변성은 `tuple`/`str`/`frozenset` 처럼 타입이 C 레벨에서 제공하거나, `__setattr__` 을 직접 덮어써서 흉내 내는 수밖에 없었습니다.

**내부에서 무슨 일이 일어나나** — `frozen=True` 는 정확히 **후자를 자동으로 해 주는 것**입니다. 마법이 아니라 메서드 두 개를 덮어씁니다. 3.13 의 `dataclasses._frozen_get_del_attr` 가 생성하는 소스는 이렇습니다.

```python
def __setattr__(self,name,value):
  if type(self) is cls or name in {'id', 'type', 'date', ...}:
   raise FrozenInstanceError(f"cannot assign to field {name!r}")
  super(cls, self).__setattr__(name, value)
def __delattr__(self,name):
  if type(self) is cls or name in {...}:
   raise FrozenInstanceError(f"cannot delete field {name!r}")
  super(cls, self).__delattr__(name)
```

여기서 세 가지가 따라 나옵니다.

1. `FrozenInstanceError` 는 `AttributeError` 의 서브클래스입니다(3.13 에서 확인: `FrozenInstanceError → AttributeError → Exception`). 그래서 `except AttributeError` 로도 잡힙니다.
2. 조건이 `type(self) is cls **or** name in {필드들}` 입니다. 즉 이 클래스의 인스턴스면 **필드가 아닌 이름을 붙이는 것도** 막고, 서브클래스 인스턴스에 대해서는 **선언된 필드 이름만** 막습니다.
3. 막는 것은 **이름에 다른 것을 다시 묶는 일**뿐입니다. 그 이름이 가리키는 객체 자체가 바뀌는 것은 이 코드가 볼 수 없습니다.

3번이 이 소스의 설계와 직결됩니다. 일반론 예시 — 이 소스에는 없습니다.

```python
@dataclass(frozen=True)
class WithList:
    xs: list = field(default_factory=list)

w = WithList()
w.xs.append('mutated')   # 예외 없음
print(w)                 # WithList(xs=['mutated'])
```

`w.xs = []` 는 `FrozenInstanceError` 지만 `w.xs.append(...)` 는 그냥 됩니다. `__setattr__` 이 호출되지 않기 때문입니다.

**이 소스에서** — `Transaction` 의 `tags` 가 `list[str]` 이 아니라 `tuple[str, ...]` 인 것이 이 구멍을 닫으려는 선택입니다.

budget_app/domain/entities.py:66
```python
    tags: tuple[str, ...] = ()
```

`__post_init__` 도 마지막 줄에서 굳이 `tuple(...)` 로 다시 감쌉니다.

budget_app/domain/entities.py:80
```python
        _set(self, "tags", tuple(validators.parse_tags(self.tags)))
```

`parse_tags` 는 리스트를 돌려주는데, 그것을 그대로 두면 `tx.tags.append("가짜")` 가 통합니다. 튜플로 바꾸는 순간 (a) 내부 변경 경로가 막히고 (b) `Transaction` 이 해시 가능해집니다(다음다음 항목). 실행 확인:

```
>>> t.amount = -1
dataclasses.FrozenInstanceError: cannot assign to field 'amount'
>>> type(t.tags)
<class 'tuple'>
```

**없으면 어떻게 되나** — `Transaction` 의 docstring 은 "생성자가 유일한 불변식 강제 지점"이라고 주장하는데, `frozen` 이 없으면 그 주장이 거짓입니다. `tx.amount = -1` 이 그냥 통하고, 그 순간 이 객체는 `validators.parse_amount` 를 통과한 적 없는 값을 들고 저장 계층까지 갑니다. 즉 `frozen=True` 는 문서에 적힌 규약을 **타입 시스템이 강제하는 규칙**으로 바꾸는 장치입니다.

---

### `object.__setattr__(self, ...)` 관용구

**어디서 왔나** — `object.__setattr__` 자체는 파이썬의 기본 속성 설정 구현이고, 새 문법이 아닙니다. 이 관용구가 필요해진 것은 `frozen=True` (파이썬 3.7) 때문입니다.

**무엇으로 풀리나** — `self.x = v` 는 `type(self).__setattr__(self, 'x', v)` 로 갑니다. frozen dataclass 에서는 그 `__setattr__` 이 위에서 본 "무조건 던지는" 버전입니다. 그런데 `object.__setattr__(self, 'x', v)` 는 **클래스에 붙은 `__setattr__` 을 우회해 기본 구현을 직접 부르는 것**이므로 그 검사를 지나가지 않고 인스턴스 `__dict__` 에 값을 씁니다.

이것이 "몰래 뚫는 꼼수"가 아니라 **표준 관용구**인 근거는, `dataclasses` 모듈 자신이 생성한 `__init__` 에서 정확히 같은 방법을 쓴다는 점입니다. `Lib/dataclasses.py` 의 `_field_assign`:

```python
def _field_assign(frozen, name, value, self_name):
    if frozen:
        return f'  __dataclass_builtins_object__.__setattr__({self_name},{name!r},{value})'
    return f'  {self_name}.{name}={value}'
```

`__dataclass_builtins_object__` 는 클로저로 넘겨진 내장 `object` 그 자체입니다(같은 파일에서 `'__dataclass_builtins_object__': object` 로 바인딩). 즉 frozen dataclass의 필드는 **처음 채워질 때부터** `object.__setattr__` 으로 채워집니다. `__post_init__` 이 하는 일은 그 직후에 같은 문을 한 번 더 쓰는 것뿐입니다.

**이 소스에서** — `Transaction.__post_init__` 이 이 관용구를 일곱 번 씁니다. 지역 이름 `_set` 으로 한 번 묶어 반복을 줄였습니다.

budget_app/domain/entities.py:68-80
```python
    def __post_init__(self) -> None:
        # TransactionId 를 받든 문자열을 받든 같은 결과가 되게 한다
        # (JSONL 은 문자열로, 서비스는 값 객체로 넘긴다).
        # frozen 이라 대입 대신 object.__setattr__ 로 정규화한다 — 생성자가 끝나는
        # 순간 객체는 검증·정규화가 끝난 상태로 굳는다.
        _set = object.__setattr__
        _set(self, "id", TransactionId.parse(self.id))
        _set(self, "type", validators.parse_type(self.type))
        ...
```

같은 관용구가 `Budget.__post_init__`(budget_app/domain/entities.py:164-166), `Category.__post_init__`(budget_app/domain/entities.py:182-183), `TransactionId.__post_init__` 에도 있습니다.

budget_app/domain/tx_id.py:83-89
```python
    def __post_init__(self) -> None:
        # frozen dataclass 라 object.__setattr__ 로 정규화한다.
        v = str(self.value or "").strip()
        m = _EXACT.match(v)
        if not m:
            raise ValidationError(messages.ERR_TX_ID_INVALID.format(value=v))
        object.__setattr__(self, "value", config.TX_ID_FORMAT.format(int(m.group(1))))
```

**없으면 어떻게 되나** — `self.value = ...` 로 쓰면 **객체를 만드는 것 자체가** `FrozenInstanceError` 로 실패합니다. `__post_init__` 은 `__init__` 안에서 불리므로, 생성자가 자기 자신이 만든 객체에 막히는 셈입니다. 그러면 남는 선택지는 "정규화를 포기하고 `TX-1` 과 `TX-000001` 을 다른 값으로 공존시키기" 또는 "frozen 을 포기하기" 둘뿐인데, 앞의 것은 `IdAllocator` 의 중복 검출을 무력화하고(tx_id.py 의 docstring 이 설명하는 바로 그 버그), 뒤의 것은 불변식 강제를 포기하는 것입니다.

---

### `__post_init__`

**어디서 왔나** — PEP 557(3.7)이 정의한 훅입니다. dataclass 가 `__init__` 을 대신 만들어 주는 대가로 "생성 직후에 뭔가 더 하고 싶다"를 표현할 자리가 필요해져 생겼습니다.

**언제 불리나** — 생성된 `__init__` 이 **모든 필드를 대입한 뒤 마지막 줄에서** `self.__post_init__()` 을 호출합니다. 앞서 뽑아 본 `Transaction` 의 생성 소스 마지막 줄이 그 증거입니다.

```python
  __dataclass_builtins_object__.__setattr__(self,'tags',tags)
  self.__post_init__()
```

호출은 **정의돼 있을 때만** 생성됩니다(`hasattr(cls, '__post_init__')` 로 판단). 그래서 `RejectedRow` 처럼 훅이 없는 dataclass 의 `__init__` 에는 그 줄이 아예 없습니다. 인자도 넘기지 않습니다 — 다만 `InitVar` 필드가 있으면 그것들이 인자로 전달되는데, **이 소스는 `InitVar` 를 쓰지 않습니다**.

"마지막에 불린다"가 중요한 이유는, `__post_init__` 안에서 `self.<필드>` 를 읽을 수 있다는 뜻이기 때문입니다. `Transaction.__post_init__` 은 `self.id`, `self.type` 을 **읽어서** 정규화한 값을 다시 씁니다. 대입 전이었다면 `AttributeError` 가 났을 것입니다.

**`field(init=False)` 와의 상호작용** — 여기서 `SearchFilter` 가 재미있는 사례입니다.

budget_app/domain/queries.py:51-55
```python
    #: 조립된 명세 — 생성 시 한 번만 만든다(거래마다 다시 만들지 않는다)
    spec: specs.Spec = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.spec = self._build_spec()
```

`init=False` 는 "이 필드를 `__init__` 의 매개변수로 만들지 말라"는 뜻이고, 기본값도 `default_factory` 도 없으므로 **`__init__` 은 `spec` 을 대입하지 않습니다**. 실제 생성된 `SearchFilter.__init__` 을 뽑아 보면 `spec` 이 아예 없습니다.

```python
def __init__(self, date_from=..., date_to=..., category=..., type=..., query=..., tag=...):
  self.date_from=date_from
  ...
  self.tag=tag
  self.__post_init__()
```

즉 **`spec` 을 채워 넣는 유일한 주체가 `__post_init__`** 입니다. 그런데 같은 dataclass 가 만든 `__eq__` 는 `spec` 을 비교에 포함합니다(`compare` 기본값이 `True` 이므로).

```python
   return self.date_from==other.date_from and ... and self.spec==other.spec
```

`repr=False` 라서 `repr()` 에는 안 보이지만 `==` 에는 들어간다는 뜻이고, `Spec` 계열은 `__eq__` 를 정의하지 않으므로 이 비교는 **객체 동일성 비교**가 됩니다. 따라서 같은 인자로 만든 두 `SearchFilter` 는 서로 다르다고 판정됩니다. 실행 확인:

```
>>> SearchFilter(category='food') == SearchFilter(category='food')
False
>>> repr(SearchFilter(category='food', tag='meal'))
"SearchFilter(date_from=None, ..., category='food', ..., tag='meal')"   # spec 없음
>>> SearchFilter(category='food', tag='meal').spec
(InCategory('food') & HasTag('meal'))
```

이 코드는 `SearchFilter` 를 `==` 로 비교하지 않으므로 실제 문제가 되지는 않습니다. 다만 "`init=False` 필드는 `repr` 에서는 빠져도 `eq` 에서는 안 빠진다"는 것은 알고 있어야 하는 비대칭입니다.

**없으면 어떻게 되나** — `SearchFilter` 가 `matches` 마다 `_build_spec()` 을 다시 부르게 됩니다. 그러면 거래 한 건을 판정할 때마다 명세 객체 여섯 개 후보를 새로 만들고 `validators` 를 다시 돌리는 셈이라, 전체 스캔이 거래 수에 비례해 훨씬 느려집니다. 그리고 "잘못된 날짜를 준 경우 `ValidationError` 가 **필터를 만들 때** 난다"는 계약도 깨져, 오류가 스트리밍 도중에 튀어나옵니다.

---

### `frozen=True` + `eq=True` 가 만드는 `__hash__`

**어디서 왔나** — PEP 557(3.7)의 규칙입니다. 파이썬 자체의 오래된 규칙은 "`__eq__` 를 정의하면 `__hash__` 는 `None` 이 된다"(파이썬 3에서 도입된 동작)입니다. 같다고 판정되는 두 객체가 다른 해시를 가지면 dict/set 이 깨지기 때문입니다. dataclass 는 그 위에 자기 규칙을 얹습니다.

**무엇이 생기나** — `eq` 와 `frozen` 조합에 따라 세 갈래입니다.

| `eq` | `frozen` | `__hash__` |
|---|---|---|
| True | True | dataclass 가 **생성**한다 |
| True | False | `None` 으로 설정된다 (해시 불가) |
| False | (무관) | 손대지 않는다 (`object.__hash__` 상속) |

생성되는 본문은 `_hash_add` 가 만들며, `compare=True` 인 필드들의 튜플을 해시합니다.

budget_app 의 `Transaction` 에 대해 실제로 생성된 것:

```python
def __hash__(self):
  return hash((self.id,self.type,self.date,self.amount,self.category,self.memo,self.tags,))
```

여기서 조건이 드러납니다 — **필드가 전부 해시 가능해야 합니다.** 튜플의 해시는 원소들의 해시를 조합하는 것이라, 원소 하나가 `list` 면 그 자리에서 `TypeError: unhashable type: 'list'` 가 납니다. 그리고 이 오류는 클래스를 정의할 때가 아니라 **`hash()` 를 실제로 부르는 순간**에 납니다. 이 소스에 실제로 그런 사례가 있습니다.

budget_app/domain/entities.py:142
```python
    tags: list[str] | None = None
```

`TransactionPatch` 는 `frozen=True` 라 `__hash__` 를 갖지만, `tags` 가 리스트일 수 있습니다. 실행 확인:

```
>>> hash(TransactionPatch(memo='x'))      # 정상
>>> hash(TransactionPatch(tags=['a']))
TypeError: unhashable type: 'list'
```

`TransactionPatch` 를 set/dict 키로 쓰는 코드는 없으므로 잠재된 상태로만 남아 있습니다. 반면 `SearchFilter` 는 `frozen` 이 아니므로 `SearchFilter.__hash__ is None` 이고, `hash(SearchFilter())` 는 `TypeError: unhashable type: 'SearchFilter'` 입니다.

**이 소스에서** — 이 규칙에 실제로 **의존하는** 곳은 `IdAllocator` 입니다.

budget_app/storage/ids.py:93-95
```python
    def __init__(self, start: int = 0, taken: Iterable[TransactionId] | None = None) -> None:
        self._counter = start
        self._taken: set[TransactionId] = set(taken or ())
```

`set[TransactionId]` 가 성립하려면 `TransactionId` 가 (1) 해시 가능하고 (2) 값이 같으면 해시도 같아야 합니다. `@dataclass(frozen=True)` 가 `__eq__` 와 `__hash__` 를 **한 쌍으로** 만들어 주므로 둘 다 성립합니다. 게다가 `__post_init__` 의 정규화 덕분에 `TX-1` 과 `TX-000001` 이 같은 원소가 됩니다.

```
>>> len({TransactionId('TX-1'), TransactionId('TX-000001')})
1
```

**없으면 어떻게 되나** — `frozen` 없이 `@dataclass` 만 붙였다면 `TransactionId.__hash__` 가 `None` 이 되어 `set(taken)` 이 즉시 `TypeError` 로 죽습니다. 반대로 `eq=False` 로 껐다면 `object.__hash__`(id 기반)를 물려받아 **오류 없이 조용히 틀립니다** — 값이 같은 두 `TransactionId` 가 서로 다른 원소가 되어 `is_taken` 이 항상 `False` 를 돌려주고, 중복 id 방어가 통째로 사라집니다. 앞의 실패는 즉시 드러나고 뒤의 실패는 데이터가 깨진 뒤에야 드러납니다.

---

### `field(default_factory=...)` 와 가변 기본값 금지

**어디서 왔나** — PEP 557(3.7). 함수의 가변 기본 인자 문제(`def f(xs=[])`)와 뿌리가 같습니다. 파이썬은 기본값을 **정의 시점에 한 번** 평가해 함수 객체에 매달아 두므로, 그것이 리스트면 모든 호출이 같은 리스트를 공유합니다.

**무엇으로 풀리나** — dataclass 는 이 실수를 런타임 오류로 **강제 차단**합니다. 3.13 에서 실행 확인:

```
>>> @dataclass
... class Bad:
...     xs: list = []
ValueError: mutable default <class 'list'> for field xs is not allowed: use default_factory
```

`dict` 도 같습니다(`mutable default <class 'dict'> ...`). 판정 기준은 "기본값의 타입이 `__hash__` 가 없는가"이므로, 튜플·문자열·정수·`None` 은 통과하고 리스트·딕트·셋은 막힙니다. 그래서 `Transaction` 의 `tags: tuple[str, ...] = ()` 는 factory 없이 그냥 씁니다 — 빈 튜플은 불변이라 공유해도 안전하기 때문입니다.

`default_factory` 를 쓰면 생성 코드가 이렇게 달라집니다. 실제 `_Batch` 에서 뽑은 것:

```python
def __init__(self, transactions=__dataclass_HAS_DEFAULT_FACTORY__, ..., skipped=__dataclass_dflt_skipped__, ...):
  self.transactions=__dataclass_dflt_transactions__() if transactions is __dataclass_HAS_DEFAULT_FACTORY__ else transactions
  ...
  self.skipped=skipped
```

기법이 그대로 보입니다. 기본값 자리에 **센티넬 객체**(`_HAS_DEFAULT_FACTORY`, `repr` 이 `<factory>`)를 넣어 두고, 본문에서 `is` 로 그것인지 확인해 맞으면 **호출할 때마다 factory 를 새로 부릅니다**. 값이 아니라 "값을 만드는 법"을 저장한 것이고, 그래서 인스턴스마다 다른 리스트가 생깁니다. `skipped: int = 0` 처럼 불변 기본값은 이 우회 없이 그냥 인자 기본값으로 박힙니다.

**이 소스에서** — 가져오기 준비 단계의 누적 상태입니다.

budget_app/services/importexport.py:38-43
```python
    transactions: list[Transaction] = field(default_factory=list)
    new_categories: list[str] = field(default_factory=list)
    skipped: int = 0
    duplicated: int = 0
    errors: list[RejectedRow] = field(default_factory=list)
    duplicates: list[DuplicateRow] = field(default_factory=list)
```

**없으면 어떻게 되나** — 문법상 `= []` 는 애초에 못 씁니다(`ValueError`). 만약 파이썬이 막지 않았다면, `import_csv` 를 두 번 호출했을 때 두 번째 `_Batch` 가 첫 번째의 `transactions` 를 그대로 물려받아 **첫 가져오기의 거래가 두 번째에서 다시 저장**됩니다. 한 프로세스에서 CSV 를 두 번 가져와야 비로소 드러나는 종류의 버그입니다.

---

### `fields()`

**어디서 왔나** — PEP 557(3.7)이 함께 제공하는 조회 함수입니다.

**무엇을 돌려주나** — 3.13 확인 결과 반환 타입은 **`tuple`** 이고 원소는 `dataclasses.Field` 객체입니다(리스트가 아닙니다).

```
>>> type(fields(TransactionPatch)), type(fields(TransactionPatch)[0])
(<class 'tuple'>, <class 'dataclasses.Field'>)
>>> fields(TransactionPatch)[0]
Field(name='date',type='str | None',default=None,default_factory=<...MISSING...>,
      init=True,repr=True,hash=None,compare=True,metadata=mappingproxy({}),kw_only=False,_field_type=_FIELD)
```

`Field` 는 필드 선언을 통째로 담은 기술 객체입니다. 주의할 점 둘: `type` 은 **문자열**입니다(이 프로젝트는 `from __future__ import annotations` 를 쓰므로 더더욱), 그리고 `fields()` 는 `ClassVar`/`InitVar` 를 제외한 진짜 필드만 돌려줍니다. **값은 들어 있지 않습니다** — 그래서 값을 얻으려면 `getattr(instance, f.name)` 이 필요합니다.

**이 소스에서** — 부분 수정 요청에서 "실제로 지정된 필드"만 골라내는 데 씁니다.

budget_app/domain/entities.py:144-150
```python
    def changed_fields(self) -> dict[str, Any]:
        """``None`` 이 아닌 필드만 골라 dict 로 준다."""
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if getattr(self, f.name) is not None
        }
```

`fields(self)` — 인스턴스를 넘겨도 됩니다(클래스와 인스턴스 둘 다 받습니다). 결과는 `Transaction.with_patch` 에서 병합에 쓰입니다.

budget_app/domain/entities.py:124
```python
        return Transaction(**{**self.to_dict(), **patch.changed_fields()})
```

`is_empty` 도 같은 결과를 재사용합니다.

budget_app/domain/entities.py:152-154
```python
    @property
    def is_empty(self) -> bool:
        return not self.changed_fields()
```

**없으면 어떻게 되나** — 필드 이름 여섯 개를 문자열 리스트로 하드코딩해야 합니다. 그러면 `TransactionPatch` 에 필드를 하나 추가할 때 그 리스트를 같이 고치는 것을 잊는 순간, 새 필드는 **오류 없이 조용히 무시**됩니다. 이 클래스의 docstring 이 "이전의 `changes: Dict[str, object]` 는 키를 잘못 쓰면 조용히 무시됐다"고 지적한 바로 그 실패 모드가 다른 형태로 되돌아옵니다.

---

### `@classmethod` / `@staticmethod` / `@property`

**어디서 왔나** — 셋 다 **파이썬 2.2** 의 new-style class 와 함께 들어온 내장 타입이고, 전부 같은 것 위에 서 있습니다 — **디스크립터 프로토콜**. 데코레이터 문법(`@`) 자체는 파이썬 2.4 부터라, 2.2~2.3 에서는 `foo = classmethod(foo)` 처럼 클래스 본문 끝에서 다시 대입하는 방식으로 썼습니다.

**내부에서 무슨 일이 일어나나** — `x.attr` 을 평가할 때 파이썬은 타입의 MRO 에서 `attr` 을 찾고, 찾은 객체에 `__get__` 이 있으면 **그것을 호출한 결과**를 돌려줍니다. 세 데코레이터의 차이는 오로지 `__get__` 이 무엇을 돌려주느냐입니다. 3.13 실행 확인:

| 데코레이터 | 클래스 딕셔너리에 든 것 | `__get__(instance, cls)` 결과 |
|---|---|---|
| `@classmethod` | `<classmethod(<function ...>)>` | **클래스에 바인딩된** 메서드 (`self` 자리에 클래스가 들어감) |
| `@staticmethod` | `<staticmethod(<function ...>)>` | 원래 함수 **그대로** (바인딩 없음) |
| `@property` | `<property object>` | **`fget(instance)` 를 호출한 값** |

```
>>> Transaction.__dict__['from_dict'].__get__(None, Transaction)
<bound method Transaction.from_dict of <class '...Transaction'>>
>>> TransactionRepository.__dict__['_scan_id'].__get__(None, TransactionRepository)
<function TransactionRepository._scan_id at 0x...>
>>> MonthlySummary.__dict__['balance'].__get__(summary, MonthlySummary)
6
```

`property` 만 `__set__` 도 갖습니다(**데이터 디스크립터**). 그래서 `property` 는 인스턴스 `__dict__` 를 이기지만, `classmethod`/`staticmethod` 는 지지 않습니다 — 인스턴스 속성으로 같은 이름을 만들면 가려집니다.

**이 소스에서**

`@classmethod` — **대체 생성자**입니다. `cls` 를 받으므로 서브클래스에서도 올바른 타입을 만듭니다.

budget_app/domain/entities.py:99-111
```python
    @classmethod
    def from_dict(cls, data: dict) -> Transaction:
        # 필수 키는 하드 접근(누락 시 KeyError → 저장소가 손상 줄로 처리).
        # 검증·정규화는 __post_init__ 이 일괄 수행하므로 여기서는 형태만 넘긴다.
        return cls(
            id=data["id"],
            ...
        )
```

`cls` 를 받는 것이 **구조적으로 필요합니다.** `JsonlStore._parse_line` 이 `self.entity_cls.from_dict(data)` 를 부르는데, `entity_cls` 는 하위 클래스마다 다른 클래스(`Transaction`/`Category`/`Budget`)입니다. 세 엔티티가 같은 이름의 classmethod 를 가지므로 저장 계층이 어떤 엔티티인지 몰라도 같은 코드로 줄을 세울 수 있습니다. `TransactionId.of`/`parse`/`scan` 도 같은 형태입니다.

budget_app/domain/tx_id.py:99-102
```python
    @classmethod
    def of(cls, number: int) -> TransactionId:
        """번호로부터 만든다 — ``7`` → ``TX-000007``."""
        return cls(config.TX_ID_FORMAT.format(number))
```

`@staticmethod` — `self` 도 `cls` 도 안 쓰는데 개념적으로 그 클래스에 속하는 함수입니다.

budget_app/storage/repositories.py:39-51
```python
    @staticmethod
    def _scan_id(raw: RawLine) -> TransactionId | None:
        """한 줄에서 거래 id 를 최대한 건져낸다.
        ...
        """
        if raw.data is not None:
            candidate = raw.data.get("id")
            if isinstance(candidate, str) and tx_id_module.is_valid(candidate):
                return TransactionId(candidate.strip())
        return TransactionId.scan(raw.text)
```

인스턴스 상태(`self.path` 등)를 하나도 안 쓰므로 `@staticmethod` 가 그 사실을 **서명으로 선언**합니다. 모듈 수준 함수로 빼도 동작은 같지만, "이것은 거래 저장소의 규칙"이라는 소속이 사라집니다. `TransactionRepository._as_id`(budget_app/storage/repositories.py:93-101)도 같은 이유입니다.

`@property` — 저장하지 않고 **계산으로 얻는 값**입니다.

budget_app/domain/results.py:38-40
```python
    @property
    def balance(self) -> int:
        return self.income - self.expense
```

`MonthlySummary` 는 **집계 원자료 여섯 개만** 필드로 갖습니다(budget_app/domain/results.py:31-36 — `month`, `income`, `expense`, `top_expense`, `has_data`, `budget`). 그리고 그것들로부터 계산되는 `balance`/`usage_pct`/`over_budget`/`is_empty` 를 property 로 둡니다 — `balance` 는 `income`·`expense` 를, `usage_pct`/`over_budget` 은 `expense`·`budget` 을, `is_empty` 는 `has_data`·`budget` 을 읽습니다. 클래스 docstring 이 "집계 원자료만 담고 파생값은 property 로 계산한다"고 적은 그대로입니다. dataclass 관점에서 property 는 **필드가 아니므로** `__init__` 인자에도, `__repr__` 에도, `__eq__`/`__hash__` 에도 들어가지 않습니다. 파생값이 원자료와 어긋날 여지가 원천적으로 없습니다.

`TransactionId.number` 도 property 입니다.

budget_app/domain/tx_id.py:121-124
```python
    @property
    def number(self) -> int:
        """``TX-000007`` → ``7``."""
        return int(_EXACT.match(self.value).group(1))
```

`__post_init__` 이 값을 정규형으로 굳혀 놓았으므로 `_EXACT.match` 가 실패할 수 없다는 것이 이 구현의 전제입니다. 이 property 가 `__lt__` 와 `IdAllocator.reserve` 양쪽의 근거입니다.

**없으면 어떻게 되나** — `balance` 를 필드로 두면 `income` 이 바뀔 때 갱신을 잊는 경로가 생깁니다(`frozen` 이라 지금은 애초에 못 바꾸지만, 생성자에서 잘못 계산해 넣는 실수는 여전히 가능합니다). 더 실질적으로는, 이 파일 docstring 이 지적하듯 이전에는 서비스가 dict 를 돌려주고 CLI 가 `result["usage_pct"]` 로 꺼냈습니다 — 오타가 런타임 `KeyError` 였고, "예산이 없으면 N/A" 같은 상태 해석이 화면 코드에 흩어져 있었습니다.

> 참고: `MonthlySummary` 는 frozen dataclass 이므로 `s.balance = 3` 은 property 의 "setter 없음"이 아니라 **frozen 의 `__setattr__` 에** 먼저 걸립니다(`FrozenInstanceError: cannot assign to field 'balance'`). 두 방어가 겹쳐 있는 셈입니다.

---

### `functools.total_ordering`

**어디서 왔나** — 표준 라이브러리 `functools` 의 클래스 데코레이터로, 파이썬 **2.7 / 3.2** 계열에 추가됐습니다. 그 전에는 `__lt__`/`__le__`/`__gt__`/`__ge__` 네 개를 손으로 다 쓰거나, 파이썬 2 의 `__cmp__`(-1/0/1 을 돌려주는 단일 비교 메서드, 파이썬 3에서 제거됨)를 썼습니다.

**내부에서 무슨 일이 일어나나** — 마법이 아니라 **표 하나를 보고 빠진 메서드를 채워 넣는 것**입니다. `functools._convert` 가 그 표입니다. 3.13 에서 `python -c "import functools; print(functools._convert)"` 로 실제로 찍어 본 내용입니다(줄바꿈과 주소 `0x...` 만 읽기 좋게 손봤습니다).

```
{'__lt__': [('__gt__', <function _gt_from_lt at 0x...>),
            ('__le__', <function _le_from_lt at 0x...>),
            ('__ge__', <function _ge_from_lt at 0x...>)],
 '__le__': [('__ge__', <function _ge_from_le at 0x...>),
            ('__lt__', <function _lt_from_le at 0x...>),
            ('__gt__', <function _gt_from_le at 0x...>)],
 '__gt__': [('__lt__', <function _lt_from_gt at 0x...>),
            ('__ge__', <function _ge_from_gt at 0x...>),
            ('__le__', <function _le_from_gt at 0x...>)],
 '__ge__': [('__le__', <function _le_from_ge at 0x...>),
            ('__gt__', <function _gt_from_ge at 0x...>),
            ('__lt__', <function _lt_from_ge at 0x...>)]}
```

값은 **메서드 이름만 든 리스트가 아니라 `(채울 이름, 그 자리에 넣을 구현 함수)` 2-튜플의 리스트**입니다. 즉 "`__lt__` 가 있으면 `__gt__`/`__le__`/`__ge__` 자리에 `_gt_from_lt`/`_le_from_lt`/`_ge_from_lt` 를 꽂는다"는 표이고, 이름과 구현이 한 쌍으로 묶여 있습니다. 데코레이터 본문은 이게 전부입니다.

```python
def total_ordering(cls):
    roots = {op for op in _convert if getattr(cls, op, None) is not getattr(object, op, None)}
    if not roots:
        raise ValueError('must define at least one ordering operation: < > <= >=')
    root = max(roots)       # prefer __lt__ to __le__ to __gt__ to __ge__
    for opname, opfunc in _convert[root]:
        if opname not in roots:
            opfunc.__name__ = opname
            setattr(cls, opname, opfunc)
    return cls
```

`for opname, opfunc in _convert[root]:` 가 위 표의 2-튜플을 그대로 풀어 쓰는 자리입니다 — `opname` 이 채울 이름, `opfunc` 가 넣을 함수입니다. `getattr(cls, op) is not getattr(object, op)` 로 "사용자가 정의했는가"를 판단하고, 하나도 없으면 `ValueError` 를 냅니다. `root = max(roots)` 는 문자열 비교라서 결과적으로 `__lt__` 가 우선됩니다(주석이 그렇게 말합니다).

채워지는 구현은 이렇게 생겼습니다(`inspect.getsource(functools._gt_from_lt)`, 3.13.1).

```python
def _gt_from_lt(self, other):
    'Return a > b.  Computed by @total_ordering from (not a < b) and (a != b).'
    op_result = type(self).__lt__(self, other)
    if op_result is NotImplemented:
        return op_result
    return not op_result and self != other
```

`__lt__` 가 `NotImplemented` 를 돌려주면 그것을 그대로 전파하고, 아니면 `not (a < b) and a != b` 로 답을 만듭니다. 즉 **`__eq__` 에 의존합니다** — dataclass 가 `__eq__` 를 만들어 주므로 이 소스에서는 자동으로 충족됩니다.

**이 소스에서** — 데코레이터가 두 겹입니다. 순서에 의미가 있습니다.

budget_app/domain/tx_id.py:51-53
```python
@functools.total_ordering
@dataclass(frozen=True)
class TransactionId:
```

데코레이터는 **아래에서 위로** 적용되므로 `dataclass` 가 먼저 돌아 `__eq__`/`__hash__` 를 만들고, 그다음 `total_ordering` 이 그 클래스를 받습니다. 정의된 비교 메서드는 하나뿐입니다.

budget_app/domain/tx_id.py:91-95
```python
    def __lt__(self, other: Any) -> Any:
        """번호 순서로 비교한다. ``total_ordering`` 이 나머지 셋을 채운다."""
        if not isinstance(other, TransactionId):
            return NotImplemented
        return self.number < other.number
```

무엇이 생겼는지 실행으로 확인하면 이렇습니다.

```
>>> for n in ('__lt__','__le__','__gt__','__ge__'):
...     f = getattr(TransactionId, n); print(n, f.__qualname__, f.__module__)
__lt__ TransactionId.__lt__   budget_app.domain.tx_id
__le__ _le_from_lt            functools
__gt__ _gt_from_lt            functools
__ge__ _ge_from_lt            functools
```

세 개가 `functools` 모듈의 함수로 대체된 것이 그대로 보입니다. 동작도 맞습니다.

```
>>> a, b = TransactionId('TX-000009'), TransactionId('TX-000010')
>>> a < b, a > b, a <= b, a >= b
(True, False, True, False)
```

**없으면 어떻게 되나** — `TransactionService.stream_sorted` 가 `(date, id)` 튜플로 정렬합니다.

budget_app/services/transactions.py:85-86
```python
        items = [tx for tx in self.txs.stream() if flt is None or flt.matches(tx)]
        items.sort(key=lambda t: (t.date, t.id), reverse=True)
```

튜플 비교는 앞 원소가 같을 때만 뒤로 내려가므로, **같은 날짜의 거래가 둘 이상일 때** 비로소 `TransactionId` 끼리 비교됩니다. `__lt__` 조차 없으면 그 순간 `TypeError: '<' not supported between instances of 'TransactionId' and 'TransactionId'` 가 납니다 — 날짜가 전부 다른 테스트 데이터에서는 절대 드러나지 않는 잠재 버그입니다.

`total_ordering` 없이 `__lt__` 만 두면 정렬은 되지만(`sorted` 는 `<` 만 씁니다) `id_a >= id_b` 같은 코드가 `TypeError` 로 죽습니다. 반대로 `dataclass(order=True)` 를 썼다면 네 개가 다 생기지만 **`value` 문자열을 비교**하게 되고, 100만 건을 넘기는 순간 `TX-1000000`(7자리)이 `TX-999999`(6자리)보다 작다고 판정됩니다. 클래스 docstring 이 그 이유를 적어 두었습니다.

---

### 연산자 오버로딩 `__and__` / `__or__` / `__invert__`

**어디서 왔나** — 파이썬 데이터 모델의 원래 일부로, 특정 PEP 하나에 귀속되지 않습니다. `&`/`|`/`~` 는 원래 정수의 비트 연산자지만, 파이썬은 이것을 **어떤 타입이든 가로챌 수 있는 훅**으로 열어 두었습니다.

**무엇으로 풀리나** — 컴파일러는 이항 연산자를 타입에 무관한 바이트코드 하나로 낮춥니다. 3.13 에서 `a & b | ~c` 를 컴파일하면:

```
LOAD_NAME  a
LOAD_NAME  b
BINARY_OP  1 (&)
LOAD_NAME  c
UNARY_INVERT
BINARY_OP  7 (|)
```

`BINARY_OP` 는 런타임에 왼쪽 피연산자 타입의 `__and__` 를 부르고, 그것이 `NotImplemented` 면 오른쪽 타입의 **반사 메서드** `__rand__` 를 부릅니다. `UNARY_INVERT` 는 `__invert__` 하나만 봅니다(단항이라 반사가 없습니다).

**왜 `and`/`or` 키워드는 오버로딩할 수 없나** — 같은 자리에서 `a and b` 를 컴파일해 보면 답이 나옵니다.

```
LOAD_NAME  a
COPY       1
TO_BOOL
POP_JUMP_IF_FALSE  → L1
POP_TOP
LOAD_NAME  b
RETURN_VALUE
```

**연산 호출이 아니라 점프**입니다. `and`/`or` 는 단축 평가(short-circuit) 라서 왼쪽 값의 진리값을 보고 오른쪽을 **아예 평가하지 않을 수도** 있는 제어 흐름이고, 그러려면 `b` 가 미평가 상태여야 합니다. 특수 메서드로 만들면 `__and__(a, b)` 를 부르기 위해 `b` 를 먼저 평가해야 하므로 단축 평가가 성립하지 않습니다. 파이썬이 열어 준 훅은 `TO_BOOL` 이 부르는 `__bool__` 뿐이고, 그것은 "참인가 거짓인가"만 정할 수 있지 "결과가 무엇인가"는 정할 수 없습니다. 그래서 Specification·ORM 질의 빌더 같은 조합 DSL 은 전부 비트 연산자를 빌려 씁니다 — 관례가 아니라 **언어 구조상의 강제**입니다.

**이 소스에서** — 명세를 조합하는 세 메서드가 기반 클래스에 한 번만 정의돼 모든 하위 명세가 물려받습니다.

budget_app/domain/specs.py:84-91
```python
    def __and__(self, other: Spec) -> Spec:
        return And(self, other)

    def __or__(self, other: Spec) -> Spec:
        return Or(self, other)

    def __invert__(self) -> Spec:
        return Not(self)
```

세 메서드 모두 **판정을 하지 않고 새 명세 객체를 만들어 돌려줄 뿐**입니다. 판정은 나중에 `is_satisfied_by(tx)` 가 트리를 내려가며 합니다 — 이것이 "조합"과 "평가"를 분리하는 지점입니다.

실행 확인:

```
>>> DateFrom('2026-01-01') & ~HasTag('x')
(DateFrom('2026-01-01') & ~HasTag('x'))
>>> type(_).__name__
'And'
```

`_flatten`(budget_app/domain/specs.py:150-164)이 중첩을 펴기 때문에 `(a & b) & c` 가 `And(And(a,b),c)` 가 아니라 `And(a,b,c)` 로 평탄해집니다.

**없으면 어떻게 되나** — 조합을 `And(Or(a, b), Not(c))` 처럼 함수 호출로 써야 합니다. 동작은 같지만 조건이 셋만 넘어가도 괄호 중첩이 읽히지 않습니다. specs.py 의 docstring 은 이 점을 정직하게 덧붙입니다 — 현재 `SearchFilter._build_spec` 은 언제나 AND 하나만 조립하므로 `|`/`~` 는 **지금 소비자가 없는 선행 투자**입니다.

---

### `NotImplemented` 를 돌려주는 규약

**어디서 왔나** — PEP 207(Rich Comparisons, **파이썬 2.1**)이 도입한 규약입니다. 그 전 파이썬 2 의 `__cmp__` 는 -1/0/1 을 돌려주는 단일 메서드라 "나는 이 타입을 어떻게 비교해야 할지 모른다"를 표현할 수단이 없었습니다.

**무엇이 다른가 / 파이썬이 무엇을 하나** — `NotImplemented` 는 내장 싱글턴 객체이고, 의미는 **"거짓"이 아니라 "나는 모른다"** 입니다. 세 후보를 비교하면 차이가 분명합니다.

| 돌려주는 값 | 파이썬이 하는 일 |
|---|---|
| `NotImplemented` | 반사 연산으로 넘어가고, 그쪽도 모른다고 하면 `TypeError` |
| `False` | 그대로 결과가 됨 — **조용히 틀린 답** |
| `None` | 그대로 결과가 됨 — 거짓처럼 취급되지만 비교식으로는 무의미 |

`a < b` 를 만나면 파이썬은 `type(a).__lt__(a, b)` 를 부르고, 결과가 `NotImplemented` 면 **반사 연산** `type(b).__gt__(b, a)` 를 시도합니다(`<` 의 반사는 `>`, `<=` 의 반사는 `>=`). 그것마저 `NotImplemented` 면 비로소 `TypeError` 를 냅니다. 일반론 예시 — 이 소스에는 없습니다.

```python
class L:
    def __lt__(self, o): return NotImplemented
class R:
    def __gt__(self, o): return 'RESULT'

L() < R()      # → 'RESULT'   (R.__gt__ 가 대신 처리)
```

`False` 를 돌려주면 이 협상 자체가 일어나지 않습니다.

```python
class BadCmp:
    def __lt__(self, o): return False

BadCmp() < 3   # → False, 예외 없음. "3보다 크거나 같다"는 뜻으로 읽힘
```

**이 소스에서** — `TransactionId.__lt__` 가 정확히 이 규약을 지킵니다.

budget_app/domain/tx_id.py:91-95
```python
    def __lt__(self, other: Any) -> Any:
        """번호 순서로 비교한다. ``total_ordering`` 이 나머지 셋을 채운다."""
        if not isinstance(other, TransactionId):
            return NotImplemented
        return self.number < other.number
```

반환 타입이 `bool` 이 아니라 `Any` 인 것도 그래서입니다 — `NotImplemented` 는 `bool` 이 아닙니다. 실행 확인:

```
>>> TransactionId.__lt__(TransactionId('TX-1'), 'TX-000010')   # 직접 호출
NotImplemented
>>> TransactionId('TX-1') < 'TX-000010'                         # 연산자로
TypeError: '<' not supported between instances of 'TransactionId' and 'str'
```

앞서 본 dataclass 생성 `__eq__` 의 마지막 줄도 같은 규약입니다 — 클래스가 다르면 `return NotImplemented` 라서, `Transaction() == 어떤객체` 를 그 객체의 `__eq__` 가 처리할 기회가 남습니다.

**없으면 어떻게 되나** — `return False` 로 바꾸면 `TransactionId('TX-000001') < 'TX-000010'` 이 예외 없이 `False` 가 됩니다. 그러면 `total_ordering` 이 그것을 근거로 만든 `__ge__` 가 `True` 를 돌려주고, "거래 ID 가 문자열보다 크거나 같다"는 무의미한 참이 만들어집니다. 정렬이나 비교가 섞인 코드에서 **오류 대신 잘못된 순서**가 나오는 것이 최악의 결과입니다. `NotImplemented` 는 그런 상황을 반드시 `TypeError` 로 끝나게 만드는 안전장치입니다.

> 주의: `NotImplemented` 는 예외 `NotImplementedError` 와 다릅니다. 전자는 돌려주는 **값**, 후자는 던지는 **예외**입니다. 그리고 `NotImplemented` 를 불리언 문맥에서 쓰는 것(`if result:`)은 3.13 에서 `DeprecationWarning: NotImplemented should not be used in a boolean context` 를 냅니다 — 실수로 진리값 취급하는 것을 언어가 경고합니다.

---

### `abc.ABC` / `@abstractmethod`

**어디서 왔나** — `abc` 모듈은 PEP 3119(Introducing Abstract Base Classes)로 **파이썬 2.6 / 3.0** 에 들어왔습니다. 편의 클래스 `abc.ABC` 는 나중에 **파이썬 3.4** 에 추가됐습니다 — 그 전에는 `class Spec(metaclass=ABCMeta)` 라고 메타클래스를 직접 지정해야 했고, `ABC` 는 정확히 그 한 줄을 대신하는 빈 클래스입니다.

**내부에서 무슨 일이 일어나나** — 두 조각이 협력합니다.

1. `@abstractmethod` 는 **함수에 표식 하나를 붙일 뿐**입니다: `func.__isabstractmethod__ = True`. 그 자체로는 아무것도 막지 않습니다.
2. 클래스를 만들 때 메타클래스 `ABCMeta` 가 본문과 기반 클래스를 훑어 그 표식이 붙은 이름을 모아 `cls.__abstractmethods__` 라는 **frozenset** 에 넣습니다.
3. `object.__new__` 가 인스턴스를 만들기 전에 그 집합이 비어 있지 않은지 검사하고, 비어 있지 않으면 `TypeError` 를 냅니다.

3번이 검사의 **실제 위치**입니다. 3.13 에서 그것을 직접 확인할 수 있습니다.

```
>>> Spec.__abstractmethods__
frozenset({'is_satisfied_by'})
>>> type(Spec)
<class 'abc.ABCMeta'>
>>> object.__new__(Spec)
TypeError: Can't instantiate abstract class Spec without an implementation for abstract method 'is_satisfied_by'
```

`Spec()` 이 아니라 `object.__new__(Spec)` 을 직접 불러도 같은 오류가 나는 것이 근거입니다. 반대 방향으로도 증명됩니다 — 집합을 비우면 그냥 만들어집니다.

```
>>> Spec.__abstractmethods__ = frozenset()
>>> Spec().is_satisfied_by(None)
None
```

즉 추상성은 언어에 박힌 특별한 상태가 아니라 **클래스 속성 하나로 표현된 데이터**이고, 상속으로 자동 전파됩니다. `Spec` 을 상속하고 `is_satisfied_by` 를 구현하지 않은 클래스는 `__abstractmethods__` 가 그대로 물려져 여전히 추상입니다.

```
>>> class Half(Spec): pass
>>> Half.__abstractmethods__
frozenset({'is_satisfied_by'})
>>> And.__abstractmethods__          # 구현했으므로 비어 있음
frozenset()
```

**`...`(Ellipsis)를 본문으로 쓰는 관용구** — `...` 는 파이썬 3 에서 아무 데서나 쓸 수 있는 내장 싱글턴 상수입니다(원래는 확장 슬라이싱 문법의 일부였습니다). 함수 본문에 `...` 만 쓰는 것은 `pass` 나 `raise NotImplementedError` 와 같은 자리를 채우는 관용구이고, 타입 스텁 파일(`.pyi`)에서 표준으로 굳으면서 "구현이 여기 없다"는 신호로 널리 쓰이게 됐습니다.

주목할 점은 `...` 가 **본문에 아무 흔적도 남기지 않는다**는 것입니다. `Spec.is_satisfied_by` 를 디스어셈블하면 이렇습니다.

```
RESUME        0
RETURN_CONST  0 (None)
```

상수식 하나뿐인 문은 컴파일러가 버리고, 함수는 암묵적으로 `None` 을 돌려줍니다. 그래서 위 실험처럼 `__abstractmethods__` 를 비우면 이 메서드는 **예외 없이 `None` 을 돌려줍니다** — 방어는 전적으로 `ABCMeta` + `object.__new__` 쪽에 있습니다. `raise NotImplementedError` 를 본문으로 쓰는 스타일과 갈리는 지점이 여기입니다.

**이 소스에서**

budget_app/domain/specs.py:76-91
```python
class Spec(ABC):
    """거래 하나가 조건을 만족하는지 판단하는 명세."""

    @abstractmethod
    def is_satisfied_by(self, tx: Transaction) -> bool: ...

    # ---------- 조합 ----------

    def __and__(self, other: Spec) -> Spec:
        return And(self, other)
    ...
```

한 클래스에 두 종류가 공존하는 좋은 예입니다 — `is_satisfied_by` 는 **하위 클래스가 반드시 채워야 할 구멍**이고, `__and__`/`__or__`/`__invert__` 는 **모두가 공짜로 물려받는 구현**입니다. 이 소스에는 `Spec` 을 상속하는 클래스가 10개(`And`, `Or`, `Not`, `Always`, `DateFrom`, `DateTo`, `InCategory`, `OfType`, `MemoContains`, `HasTag`) 있고, 전부 `is_satisfied_by` 하나만 구현하면 조합 연산자가 따라옵니다.

**없으면 어떻게 되나** — `ABC` 를 떼고 그냥 `class Spec:` 로 두면 `is_satisfied_by` 를 구현하지 않은 하위 클래스를 **만들 수도 있고 인스턴스화할 수도 있습니다**. 그 객체는 `SearchFilter.matches` 에 실려 스트림을 타다가 `None` 을 돌려주고, `None` 은 거짓이므로 그 조건에 걸린 거래가 **오류 없이 전부 걸러집니다**. "검색 결과가 왜 비었지?"로 나타나는, 원인을 찾기 가장 어려운 종류의 실패입니다. `ABCMeta` 는 그것을 클래스를 인스턴스화하는 그 줄에서 `TypeError` 로 끝냅니다.

---

### `super().__init__(...)` 와 MRO

**어디서 왔나** — 인자 없는 `super()` 는 PEP 3135(New Super)로 **파이썬 3.0** 에 들어왔습니다. 파이썬 2 에서는 `super(AppError, self).__init__(message)` 처럼 클래스와 인스턴스를 반드시 명시해야 했고, 클래스 이름을 바꾸거나 복사-붙여넣기 하면서 틀린 클래스를 적는 실수가 흔했습니다.

**내부에서 무슨 일이 일어나나** — `super()` 는 "부모 클래스"를 가리키는 것이 아니라 **MRO(Method Resolution Order) 상에서 현재 클래스의 다음 자리부터 탐색하는 프록시 객체**입니다. 인자 없는 형태가 성립하는 방법이 흥미롭습니다 — 컴파일러가 메서드 본문에서 `super` 를 발견하면 **그 클래스를 가리키는 `__class__` 라는 암묵적 클로저 셀**을 함수에 심어 줍니다. 3.13 에서 확인:

```
>>> AppError.__init__.__code__.co_freevars
('__class__',)
>>> AppError.__init__.__closure__[0].cell_contents
<class 'budget_app.errors.AppError'>
```

바이트코드에도 그대로 보입니다(3.13 은 전용 명령 `LOAD_SUPER_ATTR` 를 씁니다).

```
COPY_FREE_VARS   1
LOAD_GLOBAL      super
LOAD_DEREF       __class__      ← 심어진 셀
LOAD_FAST        self
LOAD_SUPER_ATTR  __init__
```

여기서 중요한 결론 하나: `super()` 의 출발점은 **`type(self)` 가 아니라 메서드가 정의된 클래스**입니다. 그래서 상속이 깊어져도 각 메서드가 자기 다음 자리를 정확히 가리키고, 무한 재귀가 생기지 않습니다.

**이 소스에서** — 예외 계층의 초기화입니다.

budget_app/errors.py:48-51
```python
    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.message = message
        self.hint = hint
```

`super().__init__(message)` 로 `BaseException.__init__` 에 메시지를 넘기는 것이 핵심입니다. 이것이 `self.args = (message,)` 를 설정하고, 그 결과 `str(err)` 이 메시지를 돌려줍니다. `self.message` 만 설정하고 `super()` 를 생략하면 `args` 가 비어 `str(err)` 이 **빈 문자열**이 됩니다 — 로깅이나 `except Exception as e: print(e)` 경로에서 아무것도 안 보이게 되는 조용한 사고입니다.

한 겹 더 쌓인 사례가 CLI 쪽에 있습니다.

budget_app/cli/prompts.py:36-37
```python
    def __init__(self) -> None:
        super().__init__(messages.ERR_INPUT_ABORTED, hint=messages.HINT_INPUT_ABORTED)
```

MRO 는 `InputAborted → AppError → Exception → BaseException → object` 이고, 여기서 `super().__init__` 은 `AppError.__init__` 로 갑니다. 그 안에서 다시 `super().__init__(message)` 가 `Exception.__init__` 로 갑니다 — **두 단계의 `super()` 가 연쇄**해 `args`/`message`/`hint` 가 전부 채워집니다. `InputAborted` 는 인자를 하나도 받지 않는 생성자로 "이 오류는 언제나 같은 문구"라는 사실을 타입에 새겼습니다.

저장 계층에서는 상속 3종이 같은 패턴을 씁니다.

budget_app/storage/repositories.py:27-35
```python
class TransactionRepository(JsonlStore[Transaction]):
    """transactions.jsonl 의 CRUD + 스트리밍 조회."""

    entity_cls = Transaction
    FILE_NAME = config.TX_FILE_NAME

    def __init__(self, data_dir: Path) -> None:
        super().__init__(Path(data_dir) / self.FILE_NAME)
        self._watermark = IdWatermark(Path(data_dir) / config.ID_COUNTER_FILE_NAME)
```

`CategoryStore.__init__`(budget_app/storage/repositories.py:223-224)와 `BudgetStore.__init__`(budget_app/storage/repositories.py:289-290)은 같은 한 줄만 있습니다. **인터페이스 변환**이 이 생성자들의 목적입니다 — 부모는 "파일 경로"를 받고 자식은 "데이터 폴더"를 받으므로, 자식이 자기 `FILE_NAME` 을 붙여 부모가 원하는 형태로 바꿔 넘깁니다. 세 저장소의 MRO 는 `TransactionRepository → JsonlStore → Generic → object` 형태입니다.

**없으면 어떻게 되나** — `super().__init__(...)` 을 빼면 `JsonlStore.__init__` 이 실행되지 않아 `self.path` 가 존재하지 않습니다. 그러면 객체를 만드는 것은 성공하고 **처음 파일을 읽으려는 순간** `AttributeError` 가 납니다. 생성 시점과 실패 시점이 떨어져 있어 추적이 어려운 형태입니다.

---

### 클래스 변수 vs 인스턴스 변수

**어디서 왔나** — 파이썬의 원래 객체 모델입니다. `class` 본문에서 대입한 이름은 **클래스 객체의 `__dict__`** 에 들어가고, `__init__` 안에서 `self.x = ...` 로 대입한 이름은 **인스턴스의 `__dict__`** 에 들어갑니다. 속성을 읽을 때 파이썬은 인스턴스 → 타입의 MRO 순으로 찾으므로, 인스턴스가 없으면 클래스 것이 보입니다.

**이 소스에서** — `JsonlStore` 는 하위 클래스가 채울 자리를 **애너테이션만** 선언합니다.

budget_app/storage/jsonl.py:139-146
```python
    #: 하위 클래스가 지정 — 줄 하나를 세울 dataclass
    entity_cls: type

    def __init__(self, path: Path) -> None:
        # 생성자는 경로 계산만 한다. 파일/폴더를 만드는 것은 ensure_ready() 의 일이다.
        ...
        self.path = Path(path)
```

`entity_cls: type` 은 **대입이 아니라 애너테이션**이라서 값을 만들지 않습니다. 3.13 확인:

```
>>> 'entity_cls' in JsonlStore.__dict__
False
>>> JsonlStore.__annotations__
{'entity_cls': 'type'}
```

즉 `JsonlStore` 자체에는 `entity_cls` 가 존재하지 않고, "하위 클래스가 반드시 채워야 하는 계약"을 **타입체커에게만** 말하는 선언입니다(`@abstractmethod` 의 속성판을 손으로 흉내 낸 셈입니다). 실제 값은 각 하위 클래스가 클래스 본문에서 채웁니다.

budget_app/storage/repositories.py:30-31
```python
    entity_cls = Transaction
    FILE_NAME = config.TX_FILE_NAME
```

같은 자리가 `CategoryStore`(budget_app/storage/repositories.py:220-221)와 `BudgetStore`(budget_app/storage/repositories.py:286-287)에도 있습니다.

**왜 인스턴스 변수가 아니라 클래스 속성인가** — 판단 기준은 "이 값이 인스턴스마다 다른가"입니다.

- `entity_cls` / `FILE_NAME` — **타입 자체의 성질**입니다. `TransactionRepository` 는 언제나 `Transaction` 을 다루고 언제나 `transactions.jsonl` 을 봅니다. 두 저장소 인스턴스가 이 값이 다를 이유가 없습니다. 클래스 속성으로 두면 인스턴스마다 같은 참조를 복사하지 않고, 무엇보다 **인스턴스를 만들기 전에도 읽을 수 있습니다** — 실제로 `TransactionRepository.__init__` 이 `super().__init__(Path(data_dir) / self.FILE_NAME)` 에서 그렇게 씁니다.
- `self.path` / `self._watermark` — **인스턴스마다 다릅니다**. `--data-dir` 이 달라지면 값도 달라집니다.

`self.FILE_NAME` 처럼 인스턴스를 통해 읽는 것이 자연스러운 이유도 속성 탐색 규칙 때문입니다. 인스턴스 `__dict__` 에 없으면 타입에서 찾으므로 그대로 클래스 값이 보입니다. 실행 확인:

```
>>> r = TransactionRepository.__new__(TransactionRepository)   # __init__ 없이
>>> r.entity_cls, r.FILE_NAME
(<class '...Transaction'>, 'transactions.jsonl')
```

`self.FILE_NAME` 으로 쓰는 것이 `TransactionRepository.FILE_NAME` 보다 나은 이유는, 하위 클래스가 이 값을 덮어썼을 때 자동으로 따라간다는 점입니다.

`Spec` 계열 명세들은 반대편 예시입니다 — `DateFrom.value`, `InCategory.name` 은 명세 객체마다 다르므로 전부 `__init__` 안의 인스턴스 변수입니다.

**없으면 어떻게 되나** — `entity_cls` 를 각 하위 클래스의 `__init__` 에서 `self.entity_cls = Transaction` 으로 넣어도 동작은 같습니다. 다만 (a) 하위 클래스마다 `super().__init__` 위/아래 어디에 넣느냐에 따라 순서 버그가 생길 여지가 있고, (b) 클래스만 보고는 "이 저장소가 무엇을 다루는지" 알 수 없어져 클래스 본문 첫 두 줄이 주던 문서 효과가 사라집니다. 반대로 **가변 객체를 클래스 속성으로 두면** 모든 인스턴스가 그것을 공유하는 고전적 버그가 생기는데, 여기 있는 값은 클래스와 문자열이라 그 위험이 없습니다.

---

## 1-C. 제너레이터, 데코레이터/클로저, 예외, 컨텍스트 매니저

> **이 절은 무엇인가** — **"이 코드는 언제 실행되는가"** 하나로 묶인 절입니다. 큰 파일을 통째로 메모리에 올리지 않고 한 줄씩 흘려보내는 장치, 이미 적어 둔 정의를 다른 함수에 한 번 통과시켜 그 결과로 갈아 끼우는 장치(겉을 한 겹 감싸기도 하고, 원래 것에 내용만 채워 그대로 돌려주기도 합니다), 일이 잘못됐을 때 어디까지 되돌리고 무엇을 알릴지 정하는 장치, 그리고 한 번 연 것은 반드시 닫히게 만드는 장치를 차례로 봅니다. 저장 담당 코드와 명령줄 담당 코드의 뼈대라, 그 두 폴더를 읽는 동안 가장 자주 돌아오게 됩니다.

이 절은 저장소와 CLI 계층의 뼈대입니다 — 파일을 한 줄씩 흘려보내는 제너레이터, 함수를 감싸는 데코레이터와 클로저, 열 단으로 늘어선 `except` 체인, `with` 가 보장하는 것, 그리고 애너테이션과 제네릭. **"이 코드는 언제 실행되는가"** 라는 하나의 질문이 절 전체를 관통합니다. 제너레이터의 본문이 언제 시작되는지, 로그 문자열이 언제 만들어지는지, 애너테이션이 언제(혹은 영영) 평가되지 않는지가 전부 같은 질문의 변주입니다.

이 절의 실행 확인은 모두 **CPython 3.13.1**(Windows)에서 수행했습니다. 프로젝트의
`requires-python` 은 `>=3.10` 이므로, "3.13 에서 관찰한 사실"과 "이 버전에서 도입되었다"는
주장을 문장에서 구분해 적었습니다.

---

### `yield` — 제너레이터 함수 (PEP 255)

**어디서 왔나** — PEP 255 *Simple Generators* 로 파이썬 2.2 에 들어왔고(당시에는
`from __future__ import generators` 가 필요했으며 2.3 부터 기본), 2.5 의 PEP 342 가
`send()`/`throw()`/`close()` 와 `GeneratorExit` 를 얹어 지금 형태가 되었습니다.
그전에는 "한 번에 하나씩 주는 객체"를 만들려면 `__iter__`/`__next__` 를 가진 클래스를
직접 써야 했습니다. 즉 `yield` 는 **이터레이터 클래스를 한 줄로 대체하는 문법**입니다.

> **💡 쉽게 말하면** — 도서관 책을 통째로 복사해 가방에 넣어 오는 대신, 열람실에 앉아 한 장씩 넘겨 보는 것입니다. 백만 줄짜리 파일이어도 **읽어 들이는 동안** 손에 들려 있는 것은 늘 한 줄뿐이라, 파일 전체를 문자열로 들고 있는 순간이 없습니다.
> 다만 이 비유는 되돌아갈 수 없다는 점에서 깨집니다 — 책은 앞 장을 다시 펼 수 있지만, 제너레이터는 한 번 지나간 줄로 돌아가지 못하고 처음부터 다시 만들어야 합니다. 그리고 중간에 **정렬**이 끼면 한 줄씩의 이점이 사라집니다 — 첫 결과가 무엇인지 알려면 마지막 줄까지 봐야 해서, `stream_sorted` 는 조건을 통과한 거래를 한 번 다 모아 둡니다(같은 항목 뒤쪽의 "정렬은 근본적으로 지연될 수 없는 연산입니다" 부분).

**무엇으로 풀리나** — 핵심은 "함수 안에 `yield` 가 하나라도 있으면 그 함수는 더 이상
보통 함수가 아니다"라는 점이고, 이 판정은 **실행 시점이 아니라 컴파일 시점**에 끝납니다.
컴파일러가 코드 객체에 `CO_GENERATOR`(값 `0x20`) 플래그를 세우고, 그 플래그가 켜진
코드 객체를 호출하면 CPython 은 본문을 시작하지 않고 제너레이터 객체만 만들어
돌려줍니다. 이 소스의 제너레이터들을 직접 확인해 보면 이렇습니다.

```
$ python -c "
import inspect
from budget_app.storage.jsonl import JsonlStore
from budget_app.cli import presenter
for f in (JsonlStore.stream, JsonlStore.iter_raw, presenter.tx_table):
    c = f.__code__
    print(f.__qualname__, hex(c.co_flags), bool(c.co_flags & inspect.CO_GENERATOR))
"
JsonlStore.stream   0x1000023 True
JsonlStore.iter_raw 0x1000023 True
tx_table            0x1000023 True
```

`0x...23` 의 하위 비트를 풀면 `OPTIMIZED(0x1) | NEWLOCALS(0x2) | GENERATOR(0x20)` 입니다.
"본문이 실행되지 않는다"는 것도 관찰할 수 있습니다.

```
>>> s = JsonlStore(Path('없는파일.jsonl'))
>>> s.iter_raw()          # 파일이 없어도 아무 일도 일어나지 않는다
<generator object JsonlStore.iter_raw at ...>
```

**이 소스에서** — 읽기 경로 전체가 제너레이터로 이어져 있습니다.

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

여기서 `return` 은 "빈 제너레이터로 끝낸다"는 뜻이지 `None` 을 돌려주는 것이 아닙니다.
`yield` 가 함수 전체의 의미를 바꿔 놓았기 때문에, 같은 `return` 키워드가 다른 일을 합니다.

budget_app/storage/jsonl.py:193-203
```python
    def stream(self) -> Iterator[T]:
        """검증을 통과한 도메인 객체만 yield 한다 — 조회 전용 경로.
        ...
        """
        for raw in self.iter_raw():
            if raw.is_valid:
                yield raw.entity
            else:
                logger.warning(messages.LOG_CORRUPT_LINE, self.path.name, raw.lineno, raw.error)
```

budget_app/cli/presenter.py:42-55
```python
def tx_table(rows: Iterable[Transaction], limit: int | None = None) -> Iterator[str]:
    """거래 표를 줄 단위로 yield 한다 — 비어 있으면 안내 한 줄.

    제너레이터인 이유: 상류(``stream_sorted``)가 제너레이터이므로 여기서 리스트로
    모으면 스트리밍이 끊긴다. ``limit`` 이 걸리면 그 지점에서 상류 소비도 멈춘다.
    """
    count = 0
    for tx in rows:
        if limit is not None and count >= limit:
            break
        yield tx_line(tx)
        count += 1
    if count == 0:
        yield messages.MSG_NO_DATA
```

docstring 의 마지막 주장은 실제로 관찰됩니다. `limit=3` 으로 1000개짜리 상류를
소비시키면 상류가 **4개**만 만들어 냅니다(3개를 내보내고, 4번째를 꺼낸 직후에
`break` 하기 때문입니다).

**없으면 어떻게 되나** — `stream()` 이 리스트를 돌려주면 `budget_app list --limit 5`
가 5줄을 찍기 위해 파일 전체를 메모리에 세워야 하고, `tx_table` 의 `break` 는
"이미 다 만들어 둔 것 중 앞 5개만 쓰는" 무의미한 동작이 됩니다. 무엇보다
`iter_raw` 가 리스트를 돌려주면 손상 줄 경고 로그가 **파일을 여는 순간 한꺼번에**
쏟아지고, 그 시점에는 아직 사용자가 무슨 명령을 실행했는지도 화면에 나오기 전입니다.

---

### `yield from` — 위임 (PEP 380)

**어디서 왔나** — PEP 380 *Syntax for Delegating to a Subgenerator*, 파이썬 3.3.
그전에는 `for x in sub: yield x` 로 손수 옮겨 담아야 했습니다.

**무엇으로 풀리나 / 무엇이 다른가** — `yield from sub` 는 단순한 `for`-`yield` 의
줄임말이 아닙니다. 세 가지가 더 있습니다.

1. **반환값** — 하위 제너레이터가 `return v` 로 끝내면 `StopIteration.value` 에 실려
   오고, `result = yield from sub` 가 그것을 받습니다. `for`-`yield` 로는 잡을 수 없습니다.
2. **양방향 전달** — 소비자가 보낸 `send()`/`throw()` 가 위임된 하위 제너레이터에
   그대로 전달됩니다. `for`-`yield` 를 쓰면 바깥 제너레이터가 값을 가로챕니다.
3. **`close()` 전파** — 바깥 제너레이터를 닫으면 안쪽까지 닫힙니다.

이 소스는 (1)(2)를 쓰지 않지만 (3)이 조용히 매우 중요합니다.

**이 소스에서** — CSV 읽기 경로입니다.

budget_app/storage/csv_io.py:72-87
```python
def read_rows(path: Path) -> Iterator[tuple[int, dict[str, str]]]:
    """CSV 를 읽어 ``(줄번호, 원시 dict)`` 를 yield 한다.

    헤더 검증은 첫 행을 읽는 시점에 한 번만 한다. 필수 컬럼은 예전과 동일하며
    ``id`` 는 요구하지 않는다.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(str(path))

    with open(path, encoding=config.CSV_READ_ENCODING, newline="") as f:
        reader = csv.DictReader(f)
        _check_header(path, reader.fieldnames)
        # ``yield from`` 이라 이 함수가 소비되는 동안 ``with`` 블록이 살아 있고,
        # 파일은 마지막 행을 꺼낸 뒤에 닫힌다(제너레이터라 그 시점이 호출자에 달렸다).
        yield from enumerate(reader, start=config.CSV_DATA_START_LINE)
```

여기서 벌어지는 일을 정확히 말하면 이렇습니다. **`with` 블록이 이 함수의 프레임 안에
있으므로, `with` 의 수명은 이 제너레이터 프레임의 수명이고, 그 수명은 소비자가
결정합니다.** `raise FileNotFoundError` 조차 함수를 호출할 때가 아니라 **첫 `next()`
때** 일어납니다. 다음은 같은 구조를 축소해 실행한 결과입니다.

```
호출만 하고 소비 안 함   → 파일이 열리지도 않음
한 행만 꺼냄             → 파일 열림, closed = False
gen.close()             → closed = True   (with 의 __exit__ 이 실행됨)
del gen; gc.collect()   → closed = True   (참조가 사라지면 close() 가 자동 호출됨)
끝까지 소비              → with 블록을 정상적으로 빠져나가고 closed = True
```

`close()` 는 정지 지점에 `GeneratorExit`(이것은 `BaseException` 의 직계 자식입니다)을
던집니다. 그 예외가 `with` 블록을 통과하면서 `__exit__` 이 호출되어 파일이 닫히고,
그다음에는 `GeneratorExit` 가 계속 올라가기 때문에 **`with` 블록 뒤에 적은 코드는
실행되지 않습니다**(이것도 실행으로 확인했습니다). 즉 "파일은 닫히지만 뒷정리 코드는
안 돌 수 있다"가 정확한 표현입니다.

**없으면 어떻게 되나** — 이 구조가 실제로 걸리는 자리는 원자 모드 가져오기입니다.

budget_app/services/importexport.py:109-118
```python
        for lineno, row in csv_io.read_rows(in_path):
            try:
                parsed = csv_io.parse_row(row)
            except (ValidationError, KeyError) as exc:
                if atomic:
                    # 전수 롤백: 준비 단계에서 즉시 중단, 파일은 손대지 않는다.
                    raise AppError(
                        messages.ERR_ATOMIC_IMPORT_FAILED.format(lineno=lineno, reason=exc),
                        hint=messages.HINT_ATOMIC_IMPORT,
                    ) from exc
```

`--atomic` 에서 3번째 줄이 깨지면 `for` 문이 **중간에** 버려집니다. 이때 CSV 파일을
닫는 것은 `finally` 도 `close()` 호출도 아니고, **버려진 제너레이터의 참조 카운트가
0 이 되면서 CPython 이 `gen.close()` 를 대신 불러 주는 것**입니다. 만약 `read_rows`
가 `with` 대신 `f = open(...)` 후 마지막에 `f.close()` 만 했다면, 이 경로에서 파일
핸들이 그대로 남습니다. Windows 에서는 열린 핸들이 `os.replace` 를 `PermissionError`
로 실패시키므로, 그 누수가 곧 `UnitOfWork` 커밋 실패로 이어집니다.

> 참고로 CPython 이 참조 카운팅을 쓰기 때문에 "버려지는 즉시" 닫히는 것이고,
> 이는 언어 명세의 보장이 아니라 **구현 세부**입니다. 그래서 `with` 를 쓰는 것이
> 여전히 옳습니다 — `with` 는 `gen.close()` 가 언제 불리든 그 시점에 확실히 닫습니다.

---

### 제너레이터의 지연 평가와 메모리 — `stream_sorted` 의 정직한 한계

**이 소스에서** — 제너레이터를 쓴다고 항상 메모리가 상수가 되는 것은 아닙니다.
이 코드가 그 반례를 정직하게 적어 두었습니다.

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

**정렬은 근본적으로 지연될 수 없는 연산입니다.** 첫 번째 결과가 무엇인지 알려면
마지막 원소까지 봐야 하기 때문입니다. 그래서 `yield from items` 앞에서 리스트가
한 번 완성됩니다. 그럼에도 이 함수가 제너레이터인 것은 무의미하지 않습니다.

- `self.txs.stream()` 이 제너레이터이므로 **파일 전체를 문자열로 들고 있는 순간이
  없습니다.** 한 줄씩 읽어 객체로 만들고, 필터를 통과한 것만 리스트에 남습니다.
  `--category 식비` 검색이면 메모리는 "식비 거래 수"에 비례하지 전체 파일 크기가 아닙니다.
- 반환 타입이 `Iterator[Transaction]` 로 유지되므로 하류(`tx_table`)의 계약이 깨지지
  않습니다. 나중에 파일이 정렬 저장으로 바뀌면 이 함수 안만 고치면 됩니다.
- `co_flags` 로 확인해 보면 `stream_sorted` 도 `CO_GENERATOR` 가 켜져 있습니다. 즉
  `TransactionService().stream_sorted()` 를 호출한 시점에는 **파일을 아직 열지도
  않았습니다.** 정렬 비용은 첫 `next()` 때 지불됩니다.

**없으면 어떻게 되나** — `return items` 로 바꾸면 타입이 `list` 가 되어 하류에서
`len()` 을 쓰거나 두 번 순회하는 코드가 슬금슬금 생기고, 그 순간 "이 계층은
스트리밍한다"는 계약이 사라집니다.

---

### 제너레이터 표현식 vs 리스트 컴프리헨션 — `any`/`all` 의 단축 평가

**어디서 왔나** — 리스트 컴프리헨션은 PEP 202(파이썬 2.0), 제너레이터 표현식은
PEP 289(파이썬 2.4)입니다. 문법은 대괄호와 괄호 하나 차이지만 **평가 시점이
정반대**입니다.

**무엇으로 풀리나** — `[f(x) for x in it]` 은 즉시 전부 계산해 리스트를 만들고,
`(f(x) for x in it)` 은 `CO_GENERATOR` 가 켜진 익명 코드 객체를 만들어 제너레이터를
돌려줍니다. `any()`/`all()` 은 인자를 순회하다가 결론이 나면 **거기서 멈추므로**,
안에 무엇을 넣느냐가 실제 평가 횟수를 바꿉니다.

```
any(probe(i) for i in range(10))    → True, probe 4회 호출
any([probe(i) for i in range(10)])  → True, probe 10회 호출   ← 대괄호 하나 차이
```

**이 소스에서** — 대괄호가 붙었다면 파일을 끝까지 읽었을 자리들입니다.

budget_app/storage/repositories.py:121-124
```python
    def category_in_use(self, name: str) -> bool:
        """저장된 카테고리는 정규형이므로 **묻는 쪽도 정규화**해야 판정이 맞는다."""
        target = validators.parse_category(name)
        return any(tx.category == target for tx in self.stream())
```

`self.stream()` 은 파일을 한 줄씩 읽는 제너레이터입니다. 첫 줄이 그 카테고리를
쓰고 있으면 `any` 가 즉시 `True` 를 반환하고, 그 순간 `stream()` 제너레이터는
버려져 파일이 닫힙니다. **10만 줄짜리 파일에서 1줄만 읽고 끝납니다.**

budget_app/domain/specs.py:105-106
```python
    def is_satisfied_by(self, tx: Transaction) -> bool:
        return all(s.is_satisfied_by(tx) for s in self.specs)
```

budget_app/domain/specs.py:118-119
```python
    def is_satisfied_by(self, tx: Transaction) -> bool:
        return any(s.is_satisfied_by(tx) for s in self.specs)
```

`And` 는 첫 실패에서, `Or` 는 첫 성공에서 멈춥니다. 즉 명세 조합기가 파이썬의
`and`/`or` 연산자와 **같은 단축 평가 성질**을 갖게 되는데, 이것은 `all`/`any` 가
제너레이터를 받기 때문에 공짜로 따라온 것입니다.

**없으면 어떻게 되나** — `any([...])` 로 쓰면 `category_in_use` 가 항상 파일 전체를
읽습니다. 카테고리 삭제 한 번에 O(전체 파일)이 되고, 더 나쁜 것은 성능 문제가
**조용해서** 테스트로는 드러나지 않는다는 점입니다.

---

### 데코레이터 `@` — 문법 설탕의 정확한 전개 (PEP 318)

**어디서 왔나** — PEP 318 *Decorators for Functions and Methods*, 파이썬 2.4.
클래스 데코레이터는 PEP 3129 로 3.0 에 추가되었습니다. 2.4 이전에는 정의 **아래에**
`f = deco(f)` 를 손으로 적었고, 그러면 함수 이름을 세 번 쓰게 되며 무엇보다
"이 함수에 무엇이 적용되었는가"가 정의부에서 보이지 않았습니다.

> **💡 쉽게 말하면** — 선물 포장과 같습니다. 상자 안의 물건은 손대지 않은 채 겉에 포장지가 한 겹 더해지고, 그다음부터 사람들은 포장된 상태로 그것을 주고받습니다.
> 다만 이 비유는 데코레이터가 **꼭 감싸는 것은 아니라는** 점에서 깨집니다 — `@dataclass` 는 포장지를 두르지 않고 원래 클래스에 메서드를 직접 붙인 뒤 그 클래스 자신을 돌려주고(§1-B), `@property` 는 아예 다른 종류의 객체로 갈아 끼웁니다. 공통점은 포장이 아니라 **원래 이름에 결과를 다시 대입한다**는 것 하나뿐이고, 그래서 그 뒤로 그 이름을 부르면 데코레이터가 돌려준 쪽이 응답합니다.

**무엇으로 풀리나** — 정확히 다음과 같습니다.

```python
@deco
def g(): ...
```
는
```python
def g(): ...
g = deco(g)
```
로 풀립니다. 이름 `g` 에 **다시 대입**한다는 것이 핵심입니다. 즉 데코레이터가 무엇을
돌려주든 그것이 앞으로 `g` 라는 이름이 가리키는 물건이 됩니다. 여러 개를 겹치면
**아래에서 위로** 적용됩니다.

```python
@A
@B
def g(): ...
# g = A(B(g))
```

실행으로 확인하면 `B applied to g` 가 먼저 찍히고 `A applied to g` 가 나중에 찍힙니다.

**이 소스에서** — 겹쳐 쓰는 자리는 `TransactionId` 한 곳입니다.

budget_app/domain/tx_id.py:51-53
```python
@functools.total_ordering
@dataclass(frozen=True)
class TransactionId:
```

적용 순서는 `TransactionId = functools.total_ordering(dataclass(frozen=True)(TransactionId))`
입니다. 즉 **`dataclass` 가 먼저 돌아** `__init__`/`__eq__`/`__repr__`/`__hash__` 를
붙이고, 그 결과 클래스를 `total_ordering` 이 받아 비교 연산을 채웁니다. 결과를
확인하면 클래스 자신의 `__dict__` 안에 네 개가 모두 들어 있습니다.

```
own dict ops: ['__eq__', '__ge__', '__gt__', '__hash__', '__le__', '__lt__']
TransactionId.__gt__ → <function _gt_from_lt ...>     ← functools 가 만들어 넣은 것
```

`total_ordering` 이 하는 일은 "클래스에 정의된 비교 연산이 `object` 의 것과 다른가"로
뿌리를 찾고 나머지 셋을 `setattr` 로 꽂아 넣는 것입니다. `TransactionId` 는 `__lt__` 만
정의했으므로 뿌리가 `__lt__` 이고, `__gt__`/`__le__`/`__ge__` 가 `_gt_from_lt` 류의
함수로 채워집니다. 구현 소스와 `_convert` 표는 §1-B 의 「`functools.total_ordering`」
항목에 그대로 인용해 두었으므로 여기서는 반복하지 않습니다.

**순서를 뒤집으면?** 이 자리에 한해서는 결과가 같습니다 — `dataclass` 의 `order` 가
기본값 `False` 라 비교 연산을 만들지 않기 때문입니다. 다만 `order=True` 를 켜면
순서가 **의미를 갖다 못해 아예 실패합니다**.

```
@functools.total_ordering
@dataclass(frozen=True, order=True)   → TypeError: Cannot overwrite attribute __lt__ in class C
                                        Consider using functools.total_ordering
```

이 오류 자체가 "안쪽 데코레이터가 먼저 돈다"는 증거입니다. `dataclass` 가 먼저 실행되어
클래스 본문의 `__lt__` 와 충돌한 것이니까요.

**없으면 어떻게 되나** — `total_ordering` 없이 `__lt__` 만 있으면 `sort()` 는 되지만
`>`/`<=`/`>=` 가 `TypeError` 로 죽습니다. 정렬은 `__lt__` 만 쓰기 때문에 이 결함은
**정렬 테스트를 통과하면서도** 남아 있습니다.

---

### 클로저와 `__closure__` / `nonlocal` (PEP 227, PEP 3104)

**어디서 왔나** — 중첩 함수가 바깥 지역 변수를 보는 성질(어휘적 스코프)은
PEP 227 *Statically Nested Scopes* 로 2.1 에 들어왔습니다(2.2 부터 기본). 하지만
그때는 **읽기만** 가능했습니다. 안쪽에서 바깥 변수에 대입하면 새 지역 변수가 생겨
버렸고, 그래서 사람들은 `found = [False]` 처럼 리스트에 담아 우회했습니다.
`nonlocal` 키워드는 PEP 3104 로 파이썬 3.0 에 추가된, 그 우회를 없애는 문법입니다.

**무엇으로 풀리나 / 내부에서 무슨 일이** — 안쪽 함수가 바깥 이름을 쓰면 컴파일러가
그 이름을 **셀(cell) 객체**에 담고, 안쪽 함수의 `__closure__` 튜플에 셀 참조를
넣습니다. 이름 목록은 `__code__.co_freevars` 에 남습니다. `log_call` 이 만든 래퍼를
직접 들여다보면 이렇습니다.

```
>>> w = TransactionService.add          # @log_call 이 돌려준 wrapper
>>> w.__code__.co_freevars
('func',)
>>> w.__closure__
(<cell at 0x...: function object at 0x...>,)
>>> [c.cell_contents for c in w.__closure__]
[<function TransactionService.add at 0x...>]
```

**`func` 는 인자도 전역도 아닙니다.** `log_call` 이라는 함수 호출은 이미 오래전에
끝났는데도, `wrapper` 는 그때의 `func` 를 셀을 통해 계속 붙잡고 있습니다. 이것이
데코레이터가 성립하는 유일한 이유입니다.

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

**`nonlocal` 이 필요한 자리** — 읽기만 하면 `nonlocal` 이 필요 없지만, **쓰면** 필요합니다.

budget_app/storage/repositories.py:158-171
```python
        target = self._as_id(tx_id)
        if target is None:
            return False
        found = False

        def _drop(tx: Transaction) -> Transaction | None:
            nonlocal found
            if tx.id == target:
                found = True
                return None
            return tx

        self.rewrite(_drop)
        return found
```

`_drop` 은 `target`(읽기)과 `found`(쓰기) 둘 다 클로저로 잡습니다. `target` 에는
`nonlocal` 이 필요 없고 `found` 에는 필요합니다. `nonlocal found` 를 빼면 `found = True`
가 `_drop` 의 **지역 변수**를 만들고, `delete` 는 언제나 `False` 를 돌려줍니다 —
파일에서 줄은 정확히 지워지는데 서비스는 "그런 거래 없습니다"라고 답하는, 조용하고
찾기 어려운 버그가 됩니다. 같은 형태가 `replace._swap`(repositories.py:184-189, `found`)
과 `reassign_category._reassign`(repositories.py:206-211, `changed`)에도 있습니다.

**클로저로 함수를 만들어 내보내는 자리** — 데코레이터가 아닌 순수한 팩토리도 있습니다.

budget_app/cli/prompts.py:100-109
```python
    def _validate(raw: str) -> str:
        name = validators.parse_category(raw)
        if cat_service.exists(name):
            return name
        raise ValidationError(
            service_messages.ERR_CATEGORY_NOT_REGISTERED.format(name=name)
            + messages.FMT_AVAILABLE_SUFFIX.format(available=", ".join(cat_service.list_names()))
        )

    return _validate
```

`_validate` 는 `Callable[[str], str]` 이라는 단순한 계약을 만족하면서 `cat_service` 를
몸에 지니고 다닙니다. `ask_until(prompt, validator)` 는 검증기가 무엇을 알고 있는지
전혀 모른 채 호출만 하면 됩니다. 클로저가 없다면 `ask_until` 이 `cat_service` 를
받아 넘겨 주는 형태가 되어야 하고, 그 순간 `ask_until` 이 카테고리 서비스를 알게 됩니다.

---

### `functools.wraps` — 무엇을 복사하고, 없으면 무엇을 잃나

**어디서 왔나** — `functools` 모듈의 `update_wrapper`/`wraps` 는 파이썬 2 시절부터
있던 오래된 도구입니다. `__wrapped__` 속성을 함께 설정하는 동작은 그보다 나중에
덧붙었고, 로컬 3.13.1 의 `Lib/functools.py` 를 읽어 보면 `update_wrapper` 의
**맨 마지막 줄**에 그 이유가 주석으로 남아 있습니다 — `# Issue #17482: set
__wrapped__ last so we don't inadvertently copy it from the wrapped function when
updating __dict__`.

> **💡 쉽게 말하면** — 물건을 포장하고 나면 겉면에는 포장지 자기 이름(`wrapper`)이 붙어, 안에 무엇이 들었는지가 밖에서는 엉뚱하게 읽힙니다. 정보가 사라진 것이 아니라 이름표가 잘못 붙은 것입니다. `functools.wraps` 는 안쪽 물건에 붙어 있던 이름표와 설명서를 **포장지 겉에 그대로 옮겨 붙이는** 일만 합니다.
> 다만 이 비유는 옮겨 붙는 항목이 미리 정해져 있다는 점에서 깨집니다 — 아래 목록에 있는 것만 복사되고, 나머지는 "원본은 이쪽입니다"라는 꼬리표(`__wrapped__`)를 따라가야 되찾을 수 있습니다.

**무엇으로 풀리나** — `@functools.wraps(func)` 는 `functools.partial(update_wrapper, wrapped=func)`
를 돌려주는 데코레이터 팩토리이고, 실제 일은 `update_wrapper` 가 합니다. 복사 목록은
모듈 상수로 공개되어 있습니다(3.13.1 확인값).

```
>>> functools.WRAPPER_ASSIGNMENTS
('__module__', '__name__', '__qualname__', '__doc__', '__annotations__', '__type_params__')
>>> functools.WRAPPER_UPDATES
('__dict__',)
```

`ASSIGNMENTS` 는 **덮어쓰기**(래퍼의 값이 원본 값으로 대체), `UPDATES` 는
**병합**(`wrapper.__dict__.update(func.__dict__)`)입니다. 마지막 `__type_params__` 는
제네릭 문법이 언어에 들어오면서 목록에 추가된 항목이라 옛 버전에는 없습니다.
그리고 목록에 없지만 `update_wrapper` 가 마지막에 반드시 하는 일이 하나 더 있습니다 —
`wrapper.__wrapped__ = func` 입니다.

```
>>> TransactionService.add.__name__
'add'
>>> TransactionService.add.__wrapped__
<function TransactionService.add at 0x...>          ← 원본으로 되돌아갈 수 있다
>>> inspect.signature(TransactionService.add)
(self, date: 'str', type_: 'str', category: 'str', amount: 'int', memo: 'str' = '', tags: 'list[str] | None' = None) -> 'Transaction'
```

래퍼가 `(*args, **kwargs)` 인데도 원본의 매개변수 이름·기본값·애너테이션이 그대로
나옵니다 — `inspect.signature` 가 `__wrapped__` 를 따라갔기 때문입니다. 덤으로,
애너테이션이 `'str'`, `'list[str] | None'` 처럼 **작은따옴표 문자열**로 찍히는 것이
보입니다. 이 모듈에 `from __future__ import annotations` 가 있어서 애너테이션이
타입 객체가 아니라 소스 문자열로 보관되기 때문이며, 뒤의 「PEP 563」 절에서
다시 다룹니다.

**이 소스에서** — `decorators.py:40`, `decorators.py:57`, `error_handler.py:47` 세 곳
전부 래퍼 정의 바로 위에 붙어 있습니다.

**없으면 어떻게 되나 — 여기서 흔한 오해 하나를 바로잡습니다.** "wraps 가 없으면
로그가 전부 `wrapper` 로 찍힌다"는 설명을 자주 보는데, **이 코드에 한해서는 그렇지
않습니다.** `log_call` 의 로그 문구는 `func.__name__` 을 쓰고, `func` 는 클로저가
붙잡은 **원본**이기 때문입니다. 실제로 확인하면 이렇습니다.

```
데코레이터 1겹, wraps 없음   →  로그 "call add"       (정상)
데코레이터 1겹, wraps 있음   →  로그 "call add2"      (정상)
데코레이터 2겹, wraps 없음   →  로그 "call wrapper", "call deep"    ← 여기서 깨진다
데코레이터 2겹, wraps 있음   →  로그 "call deep2", "call deep2"
```

바깥 데코레이터가 받는 `func` 는 **안쪽 데코레이터가 돌려준 `wrapper`** 이므로,
`wraps` 가 이름을 복사해 두지 않았다면 바깥에서 본 이름이 `wrapper` 가 됩니다.
지금 이 소스는 `@log_call`/`@measure_time`/`@handle_errors` 를 겹쳐 쓰지 않으므로
이 증상이 드러나지 않지만, `@log_call` 을 `@measure_time` 위에 하나 더 붙이는
순간 나타납니다. `wraps` 는 그 미래를 막아 두는 장치입니다.

`wraps` 가 없을 때 **지금 당장** 잃는 것들은 따로 있습니다.

```
wraps 없음:  __name__='wrapper', __doc__=None, __wrapped__ 없음,
             inspect.signature → (*a, **k)
wraps 있음:  __name__='add',     원본 docstring 유지, __wrapped__ 있음,
             inspect.signature → 원본 시그니처
```

즉 `help(TransactionService.add)` 가 빈 설명을 보여 주고, 트레이스백에 노출되는
함수 정보와 `pydoc`/IDE 의 표시가 전부 `wrapper` 가 됩니다.

---

### 예외 계층과 `except` 매칭 규칙 — 순서가 곧 정책

**어디서 왔나** — `except E as e` 문법은 PEP 3110(파이썬 3.0)이고, 지금 이 코드가
잡는 세분화된 OS 예외들(`FileNotFoundError`, `PermissionError`, `IsADirectoryError`,
`NotADirectoryError`, `BrokenPipeError`)은 PEP 3151 *Reworking the OS and IO exception
hierarchy* 로 **파이썬 3.3** 에 생겼습니다. 그전에는 전부 `IOError`/`OSError` 하나였고,
구분하려면 `except OSError as e: if e.errno == errno.ENOENT:` 처럼 errno 를 손으로
분기해야 했습니다. 이 소스의 10단 `except` 체인은 PEP 3151 이 있어서 가능한 형태입니다.

**규칙 — "먼저 일치하는 절"** — 파이썬은 `except` 절을 **위에서 아래로** 훑다가
`isinstance` 로 처음 맞는 것 하나만 실행하고 나머지는 보지 않습니다. "가장 구체적인
절"을 고르지 **않습니다**. 그래서 부모 클래스를 위에 두면 자식 절이 영영 죽습니다.

```
try: raise FileNotFoundError(2, "no such file")
except OSError:           → 이 절이 잡는다
except FileNotFoundError: → 도달 불가 (죽은 코드)
```

**`__mro__` 로 확인한 실제 계층** — 이 소스가 잡는 예외들의 상속 사슬입니다.

```
BrokenPipeError      → ConnectionError → OSError → Exception → BaseException
FileNotFoundError    → OSError → Exception → BaseException
IsADirectoryError    → OSError → Exception → BaseException
NotADirectoryError   → OSError → Exception → BaseException
PermissionError      → OSError → Exception → BaseException
UnicodeDecodeError   → UnicodeError → ValueError → Exception → BaseException
KeyboardInterrupt    → BaseException                        ← Exception 이 없다
ValidationError      → ValueError → Exception → BaseException
AppError             → Exception → BaseException
```

**이 소스에서**

budget_app/cli/error_handler.py:56-74
```python
        # ---------- (1) 종료 신호 — 오류가 아님 ----------
        except BrokenPipeError:
            # 하류 파이프(`list | head`)가 먼저 닫힘. 여기서 출력하면 또 깨지므로
            # 최상위(main)로 넘겨 조용히 처리하게 한다.
            raise
        except KeyboardInterrupt:
            output.err(messages.MSG_INTERRUPTED)
            return config.EXIT_INTERRUPT

        # ---------- (2) 입력 오류 — 사용자가 값을 고치면 해결됨 ----------
        except ValidationError as exc:
            output.err(messages.MSG_ERROR_LINE.format(msg=exc))
            output.err(messages.HINT_VALIDATION)
            return config.EXIT_VALIDATION
        except AppError as exc:
            output.err(messages.MSG_ERROR_LINE.format(msg=exc.message))
            if exc.hint:
                output.err(messages.MSG_HINT_LINE.format(msg=exc.hint))
            return config.EXIT_APP
```

`__mro__` 를 보면 이 순서가 **선택이 아니라 강제**임을 알 수 있습니다.

- `BrokenPipeError` 는 `OSError` 의 손자이므로 (3) 의 `except OSError` 보다 반드시
  위여야 합니다. 아래로 내리면 파이프 끊김이 "입출력 오류입니다" 메시지와 종료
  코드 3(`config.EXIT_IO`, error_handler.py:99-103 / config.py:25)으로 끝나고,
  `list | head` 가 매번 오류를 뿜습니다.
- `FileNotFoundError`/`IsADirectoryError`/`NotADirectoryError`/`PermissionError` 네
  개는 전부 `OSError` 의 직계 자식이라 error_handler.py:99 의 `except OSError` 보다
  위여야 합니다. 하나라도 아래로 내려가면 그 절은 죽은 코드가 되고, 사용자는
  "파일을 찾을 수 없습니다" 대신 일반 입출력 메시지를 봅니다.
- `ValidationError` 는 `ValueError` 의 자식이고 `UnicodeDecodeError` 도 `ValueError`
  의 자손입니다. 두 절이 서로를 가리지 않는 이유는 **둘 다 `ValueError` 자체를
  잡지 않기 때문**입니다. 만약 어느 절이든 `except ValueError` 로 넓히면 다른 쪽이
  즉시 죽습니다.
- 마지막 error_handler.py:106 의 `except Exception` 은 위 어느 것과도 겹치지 않는
  버그만 받아야 하므로 반드시 맨 아래여야 합니다.

**없으면 어떻게 되나** — `except` 순서를 알파벳순이나 "중요한 것 먼저"로 정리하는
순간 절반이 도달 불가능해집니다. 그리고 파이썬은 그것을 **경고하지 않습니다** —
문법 오류도, 린트 기본 규칙도 아닙니다.

---

### `raise ... from exc` — `__cause__` vs `__context__` (PEP 3134)

**어디서 왔나** — PEP 3134 *Exception Chaining and Embedded Tracebacks*, 파이썬 3.0.
파이썬 2 에는 예외 연결이 없었고, 안쪽 예외를 감싸면 원래 원인이 **사라졌습니다**.

**무엇으로 풀리나 / 내부에서 무슨 일이** — 파이썬 3 은 예외 객체에 두 개의 슬롯을
둡니다.

- `__context__` — **자동**입니다. `except` 블록 안에서 새 예외가 발생하면 인터프리터가
  현재 처리 중이던 예외를 여기에 넣습니다. 아무것도 안 해도 붙습니다.
- `__cause__` — **명시적**입니다. `raise X from Y` 가 `X.__cause__ = Y` 를 설정하고
  동시에 `X.__suppress_context__ = True` 로 만듭니다.

화면 출력은 이 둘을 다르게 표현합니다(실행 확인).

```
raise ... from exc            →  __cause__ = ValueError(...), __suppress_context__ = True
   트레이스백: "The above exception was the direct cause of the following exception:"

raise ... (from 없이)         →  __cause__ = None, __context__ = ValueError(...)
   트레이스백: "During handling of the above exception, another exception occurred:"

raise ... from None           →  __cause__ = None, __suppress_context__ = True
   → 안쪽 예외가 화면에서 완전히 사라진다 (__context__ 에는 남아 있다)
```

"직접적 원인(direct cause)"과 "처리 도중 또 터짐(during handling)"의 차이는 진단할 때
전혀 다른 정보입니다. 앞은 의도적 번역이고, 뒤는 **오류 처리 코드 자체의 버그일
가능성**을 뜻합니다.

**이 소스에서** — 경계에서 예외를 도메인 어휘로 번역하는 자리마다 붙어 있습니다.

budget_app/domain/validators.py:94-99
```python
    v = str(value or "").strip()
    try:
        dt = datetime.strptime(v, config.DATE_FORMAT)
    except ValueError as exc:
        raise ValidationError(messages.ERR_DATE_INVALID) from exc
    return dt.strftime(config.DATE_FORMAT)
```

사용자에게 나가는 것은 `ERR_DATE_INVALID`("YYYY-MM-DD 형식…")이지, `strptime` 이
던진 `time data '2024/01/05' does not match format '%Y-%m-%d'` 가 아닙니다. 그러나
`--debug` 로 스택을 남길 때는 원본이 함께 보존됩니다 — **사용자용 문구와 개발자용
원인을 동시에 갖는 것**이 `from` 의 요점입니다. 같은 형태가
`validators.py:112`(`parse_month`), `prompts.py:57`(`EOFError` → `InputAborted`),
`parser.py:52`(`ValueError` → `ArgumentTypeError`), `importexport.py:118`
(`ValidationError` → `AppError`)에 있습니다.

**없으면 어떻게 되나** — `from exc` 를 빼도 `__context__` 덕분에 원인이 완전히
사라지지는 않습니다. 다만 트레이스백 문구가 "처리 도중 또 다른 예외가 발생했습니다"
로 바뀌어, **의도적인 번역이 사고처럼 보입니다.** 로그를 읽는 사람이
`validators.py` 를 버그로 의심하게 되는 비용이 실제 비용입니다.

---

### 인자 없는 `raise` — 재전파

**어디서 왔나** — 파이썬 2 시절부터 있던 문법으로, `except` 블록(또는 그 안에서
호출된 코드) 안에서만 의미가 있습니다. 밖에서 쓰면 `RuntimeError: No active exception
to reraise` 가 납니다.

**무엇으로 풀리나** — `raise exc` 와 다릅니다. 인자 없는 `raise` 는 **지금 처리 중인
예외 객체를 그대로** 다시 올리므로 트레이스백이 이어 붙고, `__context__` 도 건드리지
않습니다. `except OSError as exc: ... raise exc` 로 쓰면 새 `raise` 지점이 트레이스백에
추가되어 원래 발생 위치가 한 겹 흐려집니다.

**이 소스에서** — 두 곳입니다.

budget_app/cli/error_handler.py:57-60
```python
        except BrokenPipeError:
            # 하류 파이프(`list | head`)가 먼저 닫힘. 여기서 출력하면 또 깨지므로
            # 최상위(main)로 넘겨 조용히 처리하게 한다.
            raise
```

여기서 `raise` 는 "나는 이 예외를 **인식했지만 처리하지 않는다**"는 선언입니다.
그냥 절을 지우면 아래의 `except OSError` 가 잡아 오류 메시지를 찍어 버립니다.
즉 이 절은 **아무 일도 하지 않기 위해 존재**합니다. 그리고 진짜 처리는 여기 있습니다.

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

budget_app/storage/unit_of_work.py:152-156
```python
        except OSError:
            pending = [target.name for _, target in self._staged]
            logger.warning(messages.LOG_UOW_PARTIAL, done or "없음", pending)
            self.rollback()
            raise
```

이쪽은 "부수 효과(로그 + `.tmp` 정리)만 수행하고 판단은 위로 넘긴다"는 뜻입니다.
`raise` 를 빼면 커밋이 중간에 실패했는데도 함수가 정상 반환하고, 호출자는 가져오기가
성공한 줄 압니다.

---

### `try/finally` — return 경로에서도 실행된다는 보장

**어디서 왔나** — `try/finally` 자체는 파이썬 1.x 부터 있었지만, `try/except/finally`
를 **한 문장에** 쓸 수 있게 된 것은 PEP 341(파이썬 2.5)부터입니다. 그전에는 중첩해야
했습니다.

**무엇으로 풀리나 / 보장의 정확한 범위** — `finally` 블록은 `try` 를 빠져나가는
**모든 경로**에서 실행됩니다: 정상 종료, `return`, `break`, `continue`, 예외 전파.
특히 `return` 은 "반환값을 계산해 두고 → `finally` 실행 → 그다음 실제로 반환"의
순서입니다.

```
def f():
    try: return "returned"
    finally: print("finally 실행됨(return 직전)")
→ "finally 실행됨(return 직전)" 이 먼저 찍히고 "returned" 가 반환된다
```

**이 소스에서**

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

`return func(...)` 과 `finally` 의 조합이 이 함수의 전부입니다. 성공하면 반환값을
계산한 뒤 시간을 찍고 반환하며, 실패하면 예외가 올라가기 **직전에** 시간을 찍고
예외는 그대로 전파됩니다. 즉 `measure_time` 은 예외를 **삼키지 않습니다**.
`@measure_time` 이 붙은 곳은 `BudgetService.monthly_summary`(budgets.py:30) 한 곳입니다.

**주의 — `finally` 안의 `return` 은 예외를 삼킵니다.** 이것은 일반론 예시이며
이 소스에는 없습니다.

```python
def h():
    try: raise ValueError("boom")
    finally: return "삼켜짐"     # ← 예외가 사라진다
```

`measure_time` 의 `finally` 가 `logger.debug` 만 하고 `return` 하지 않는 것이
중요한 이유입니다.

**없으면 어떻게 되나** — `try/finally` 없이 함수 호출 뒤에 시간 측정을 적으면,
예외로 끝난 호출은 **측정되지 않습니다.** "느린 명령을 찾겠다"는 목적에서 정작
가장 알고 싶은 실패 경로만 빠지게 됩니다.

---

### 예외 튜플로 잡기 — `_LINE_ERRORS`

**어디서 왔나** — `except (A, B, C):` 는 파이썬 1.x 부터 있는 기본 문법입니다.
튜플을 **상수로 빼서 이름 붙이는 것**은 문법이 아니라 관용입니다.

**무엇으로 풀리나** — `except (A, B)` 는 `isinstance(exc, (A, B))` 와 같은 판정을
합니다. 튜플 안 순서는 의미가 없습니다(어느 하나에 맞으면 됩니다). 중요한 것은
**튜플이 평범한 값**이라 모듈 상수로 뽑아 재사용할 수 있다는 점입니다.

**이 소스에서**

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

이 튜플이 상수인 것에는 이름값이 있습니다. **"한 줄이 깨지는 방법의 목록"이 곧
손상 줄 격리 정책의 정의**이기 때문입니다. 인라인으로 적혀 있으면 `KeyError` 를
왜 잡는지 아무도 모른 채 남고, 목록을 늘려야 할 때 어디를 고칠지도 불분명합니다.

여기서 잡히는 것과 안 잡히는 것의 경계도 분명합니다. `ValidationError` 는
`ValueError` 의 자식이라 잡히지만, 튜플에 `ValueError` 자체는 없으므로
`from_dict` 안에서 나온 **예상 밖의** `ValueError` 는 그대로 위로 올라가
`handle_errors` 의 최후 방어선까지 갑니다. 즉 "우리가 아는 실패는 격리하고,
모르는 실패는 숨기지 않는다"가 튜플의 내용으로 표현되어 있습니다.

**없으면 어떻게 되나** — `except Exception` 으로 넓히면 격리 범위 안에
`MemoryError`, 오타로 인한 `AttributeError` 까지 들어옵니다. 그러면 코드 버그가
"이 줄은 손상됐습니다"라는 경고 한 줄로 위장되어, **모든 줄이 손상 줄로 보이는데
파일은 멀쩡한** 상태가 됩니다.

---

### `BaseException` vs `Exception`

**어디서 왔나** — 파이썬 2.5 에서 `BaseException` 이 최상위로 도입되고
`KeyboardInterrupt`/`SystemExit` 가 `Exception` 밑에서 빠져나왔습니다. 파이썬 3 부터는
모든 예외가 `BaseException` 을 상속해야 합니다.

**무엇으로 풀리나 / 왜 이렇게 나눴나** — 계층은 다음과 같습니다.

```
BaseException
├── SystemExit          — sys.exit() 가 던진다
├── KeyboardInterrupt   — Ctrl+C (SIGINT)
├── GeneratorExit       — gen.close() 가 던진다
└── Exception           — 그 밖의 "프로그램이 다룰 만한" 모든 오류
    ├── OSError, ValueError, KeyError, TypeError, ...
    └── AppError, ValidationError (이 프로젝트가 정의한 것)
```

`Exception` 아래에 두지 않은 셋의 공통점은 **"오류가 아니라 흐름 제어 신호"** 라는
점입니다. 사용자가 Ctrl+C 를 눌렀거나, 프로그램이 스스로 끝내기로 했거나,
제너레이터를 닫는 중입니다. 이런 것을 `except Exception` 이 잡아 버리면 Ctrl+C 가
안 먹는 프로그램이 됩니다. 실행으로 확인하면 정확히 이렇습니다.

```
KeyboardInterrupt → except Exception 을 통과, BaseException 만 잡는다
SystemExit        → except Exception 을 통과
GeneratorExit     → except Exception 을 통과
```

**이 소스에서** — 이 성질 때문에 `handle_errors` 의 구조가 성립합니다.

budget_app/cli/error_handler.py:105-109
```python
        # ---------- (4) 최후 방어선 — 분류 밖의 버그 ----------
        except Exception as exc:  # noqa: BLE001 — 어떤 예외도 트레이스백으로 끝내지 않기 위함
            # 사용자용 한 줄 요약을 먼저 내고, 그다음에 원인 추적용 기록을 남긴다.
            output.err(messages.MSG_ERR_UNEXPECTED.format(error=exc))
            output.err(messages.HINT_UNEXPECTED)
```

주석은 "어떤 예외도 트레이스백으로 끝내지 않기 위함"이라고 적혀 있지만, 정확히는
**`Exception` 계열만** 그렇습니다. `KeyboardInterrupt` 는 이 절에 도달하지 않고,
그래서 error_handler.py:61 에 **전용 절**이 따로 필요했던 것입니다. 만약
`KeyboardInterrupt` 가 `Exception` 의 자식이었다면 전용 절을 지워도 동작이 같았을
테고(메시지만 달라짐), 지금처럼 "종료 신호"라는 부류를 맨 위에 둘 이유도 약해집니다.

**없으면 어떻게 되나** — 만약 최후 방어선을 `except BaseException` 으로 넓히면,
Ctrl+C 가 "예상치 못한 오류가 발생했습니다" 메시지와 종료 코드 1 로 끝나고,
`sys.exit(2)` 로 나가려던 argparse 의 종료 코드까지 뭉개집니다.

---

### `with` — 컨텍스트 매니저 프로토콜 (PEP 343)

**어디서 왔나** — PEP 343 *The "with" Statement*, 파이썬 2.5(2.5 에서는
`from __future__ import with_statement` 필요, 2.6 부터 기본). 그전에는 정리 코드를
`try/finally` 로 직접 써야 했고, "열고 → 쓰고 → 반드시 닫는다"는 관용구가 매번
5줄로 반복되었습니다.

**무엇으로 풀리나** — PEP 343 이 정의한 전개는 대략 다음과 같습니다.

```python
with EXPR as VAR:
    BLOCK
```
는
```python
mgr = EXPR
exit_ = type(mgr).__exit__          # ← 인스턴스가 아니라 '타입'에서 찾는다
value = type(mgr).__enter__(mgr)
hit_except = False
try:
    VAR = value
    BLOCK
except:
    hit_except = True
    if not exit_(mgr, *sys.exc_info()):
        raise
finally:
    if not hit_except:
        exit_(mgr, None, None, None)
```

여기서 놓치기 쉬운 두 가지가 있습니다.

**첫째, 조회가 인스턴스가 아니라 타입에서 일어납니다.** 특수 메서드 조회는 인스턴스
`__dict__` 를 건너뜁니다(실행 확인: 인스턴스에 `m.__exit__ = ...` 를 꽂아도
`type(m).__exit__` 이 실행됩니다). 그리고 `__exit__` 이 없으면 블록에 들어가기도
전에 실패합니다 — `TypeError: 'NoExit' object does not support the context manager
protocol (missed __exit__ method)`.

**둘째, `__exit__` 의 반환값이 예외의 운명을 결정합니다.** 참 같은 값(truthy)을
돌려주면 예외를 **삼키고**, 거짓 같은 값(`None` 포함)이면 예외가 계속 전파됩니다.

```
__exit__ 이 True 를 반환   → with 밖에서 예외가 보이지 않는다 (삼켜짐)
__exit__ 이 None 을 반환   → 예외가 그대로 전파된다
```

3.13 의 바이트코드로 보면 `BEFORE_WITH` 가 `__enter__`/`__exit__` 를 준비하고,
예외 경로에서 `WITH_EXCEPT_START` → `TO_BOOL` → `POP_JUMP_IF_TRUE` / `RERAISE` 가
바로 그 "반환값을 boolean 으로 보고 삼킬지 결정하는" 부분입니다.

**이 소스에서**

budget_app/storage/unit_of_work.py:169-181
```python
    def __enter__(self) -> UnitOfWork:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
```

**반환 타입이 `-> None` 인 것이 이 클래스의 계약입니다.** `__exit__` 이 항상 `None`
을 돌려주므로 `UnitOfWork` 는 **예외를 절대 삼키지 않습니다.** 블록 안에서 예외가
나면 `.tmp` 를 지우고 나서 그 예외를 그대로 올려 보냅니다. 사용처는 이렇습니다.

budget_app/services/importexport.py:199-206
```python
        fresh_categories = [Category(name=n) for n in batch.new_categories]
        # 파일을 저장소 밖(UoW)에서 쓰므로 id 워터마크는 여기서 명시적으로 알린다.
        self.txs.remember_ids(batch.transactions)
        with UnitOfWork() as uow:
            if fresh_categories:
                uow.stage(self.cats, extra=fresh_categories)
            uow.stage(self.txs, extra=batch.transactions)
        return len(batch.transactions)
```

`return len(...)` 이 `with` **밖에** 있는 것이 중요합니다. 커밋은 블록을 나가는
순간(`__exit__` 안)에 일어나므로, 커밋이 실패하면 `__exit__` 이 예외를 올리고
`return` 문에는 도달하지 않습니다. 즉 "커밋에 성공했을 때만 건수를 보고한다"가
`with` 의 구조로 표현되어 있습니다. `stage` 는 `.tmp` 만 만들고
(unit_of_work.py:119) 원본을 건드리지 않으므로, 예외로 빠져나가도 `rollback()` 이
`.tmp` 를 지우는 것으로 정리가 끝납니다.

**없으면 어떻게 되나** — `try/finally` 로 똑같이 쓸 수는 있습니다. 다만 그러면
"정상 종료면 commit, 예외면 rollback"이라는 분기를 **호출하는 쪽마다** 반복해야
하고, 한 곳에서 빠뜨리면 `.tmp` 찌꺼기가 남습니다. `__exit__` 은 그 분기를
`exc_type is None` 한 줄로 클래스 안에 가둡니다.

---

### `open()` 이 컨텍스트 매니저인 이유

**어디서 왔나** — 파일 객체의 `__enter__`/`__exit__` 는 PEP 343 과 함께 들어왔고,
파이썬 3 에서 `io` 모듈로 재작성되면서 `IOBase` 의 기본 동작이 되었습니다.

**무엇으로 풀리나 / 내부에서 무슨 일이** — `open()` 이 돌려주는 것은 텍스트 모드에서
`_io.TextIOWrapper` 인스턴스이고, 그 상속 사슬은 `TextIOWrapper → _TextIOBase →
_IOBase → object` 입니다. **`__enter__`/`__exit__` 는 `_IOBase` 에 정의되어 있습니다.**
`__enter__` 는 (닫힌 파일인지 확인한 뒤) 자기 자신을 돌려주고, `__exit__` 은
`self.close()` 를 부른 뒤 **아무것도 돌려주지 않습니다**(즉 `None`). 그래서
`with open(...)` 은 예외를 삼키지 않습니다 — 쓰기 도중 디스크가 가득 차면 파일은
닫히고 `OSError` 는 그대로 올라갑니다.

```
>>> type(open('x'))
<class '_io.TextIOWrapper'>
>>> io.IOBase.__exit__
<method '__exit__' of '_io._IOBase' objects>
```

**이 소스에서** — 파일을 여는 모든 자리가 `with` 입니다: `jsonl.py:61`(`.tmp` 쓰기),
`jsonl.py:174`(읽기), `jsonl.py:234`(이어 쓰기), `jsonl.py:258`(꼬리 1바이트 확인),
`csv_io.py:82`(CSV 읽기), `csv_io.py:142`(CSV 쓰기). 예외가 있는 자리가 하나도
없다는 것 자체가 규칙입니다.

budget_app/storage/jsonl.py:61-72
```python
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

여기서 `with` 는 단순한 정리 이상의 일을 합니다. `flush()` + `fsync()` 를 블록
**안에서** 하고 블록을 나가며 `close()` 가 되는 순서라, "버퍼를 비우고 → 디스크에
내리고 → 닫는다"가 코드 모양 그대로 보장됩니다. 그 뒤에야 `commit_staged` 의
`os.replace` 가 실행됩니다.

**없으면 어떻게 되나** — `f = open(...); ...; f.close()` 로 쓰면 중간에서 예외가
날 때 파일이 열린 채 남습니다. CPython 에서는 참조 카운트가 0 이 되며 곧 닫히지만,
그 시점이 언제인지 보장되지 않습니다. 그리고 이 프로젝트에서 그 창은 실질적인
위험입니다 — Windows 는 열린 핸들이 있는 파일에 `os.replace` 를 허용하지 않으므로,
누수된 핸들 하나가 다음 쓰기를 `PermissionError` 로 실패시킵니다.

---

### `from __future__ import annotations` (PEP 563)

**어디서 왔나** — 함수 애너테이션 자체는 PEP 3107(파이썬 3.0), 변수 애너테이션은
PEP 526(3.6)입니다. 원래 이들은 **정의 시점에 즉시 평가되는 일반 표현식**이었습니다.
PEP 563 *Postponed Evaluation of Annotations* 가 파이썬 3.7 에 `from __future__ import
annotations` 를 도입해, 이 import 가 있는 모듈에서는 애너테이션을 평가하지 않고
**소스 문자열 그대로** 보관하게 만들었습니다.

**무엇으로 풀리나 / 실행 확인** — 차이가 그대로 드러납니다.

```
# future import 없음
class A:
    x: int
    def f(self) -> "A": ...
→ A.__annotations__ = {'x': <class 'int'>}      ← 실제 타입 객체
→ A.f.__annotations__ = {'return': 'A'}         ← 따옴표로 감싼 것은 문자열 그대로

# from __future__ import annotations 있음
class A:
    x: int
    def f(self) -> A: ...                       ← 따옴표 없이 자기 클래스 참조
→ A.__annotations__ = {'x': 'int'}              ← 전부 문자열
→ A.f.__annotations__ = {'return': 'A'}
```

`from __future__ import ...` 는 평범한 import 가 아니라 **컴파일러 지시문**이라
파일 맨 위(docstring 다음)에 있어야 합니다. 이 소스의 거의 모든 모듈이 이 줄로
시작합니다 — 43개 모듈 중 28개이고(entities.py:14, jsonl.py:20, csv_io.py:24,
decorators.py:18 …), 빠진 15개는 `config`·`messages` 계열과 `__init__.py`·`__main__.py`, 즉 애너테이션을
하나도 쓰지 않는 파일들입니다.

**이 소스에서 — 이것이 없으면 실제로 문법 오류가 나는 자리**

budget_app/domain/entities.py:113-124
```python
    def with_patch(self, patch: TransactionPatch) -> Transaction:
        """부분 변경을 적용한 **새 Transaction** 을 만든다.
        ...
        """
        return Transaction(**{**self.to_dict(), **patch.changed_fields()})
```

`with_patch` 는 `Transaction` 클래스 **본문 안에** 있고, 반환 타입으로 `Transaction`
을 씁니다. 그런데 클래스 본문이 실행되는 시점에는 `Transaction` 이라는 이름이 아직
바인딩되기 전입니다. 애너테이션이 즉시 평가된다면 여기서 `NameError` 가 납니다.
PEP 563 덕분에 이 애너테이션은 그냥 문자열 `'Transaction'` 으로 남아 아무 일도
일어나지 않습니다. 실제 저장 결과를 확인하면 이렇습니다.

```
>>> Transaction.__annotations__
{'id': 'TransactionId', 'type': 'str', 'date': 'str', 'amount': 'int',
 'category': 'str', 'memo': 'str', 'tags': 'tuple[str, ...]'}
>>> Transaction.with_patch.__annotations__
{'patch': 'TransactionPatch', 'return': 'Transaction'}
>>> [(f.name, f.type) for f in dataclasses.fields(Transaction)]
[('id', 'TransactionId'), ('type', 'str'), ...]        ← dataclass 도 문자열을 그대로 저장
```

같은 형태가 `TransactionId.of`/`parse`/`scan`(tx_id.py:99-117),
`Budget.from_dict`(entities.py:171-173), `UnitOfWork.__enter__`(unit_of_work.py:169)에
있습니다. `__enter__` 는 자기 클래스 이름을 반환 타입으로 쓰는 전형적인 자리입니다.

**문자열이 필요할 때 되돌리는 방법** — `typing.get_type_hints()` 가 문자열을 모듈
네임스페이스에서 평가해 실제 객체로 돌려줍니다.

```
>>> typing.get_type_hints(Transaction)
{'id': <class 'budget_app.domain.tx_id.TransactionId'>, 'amount': <class 'int'>,
 'tags': tuple[str, ...], ...}
```

이 소스는 `get_type_hints` 를 쓰지 않습니다. **런타임에 타입을 읽어 무언가를 하는
코드가 하나도 없다**는 뜻이고, 그래서 애너테이션이 문자열로 남아도 아무 손해가
없습니다. 검증은 전부 `validators` 함수가 값으로 수행합니다.

**3.14 의 변화(짧게)** — 파이썬 3.14 에서 PEP 649(및 후속 PEP 749)가 적용되어
애너테이션의 **기본** 동작이 "즉시 평가"도 "문자열"도 아닌 **지연 평가**로
바뀝니다. PEP 563 과는 별개의 이야기입니다. 이 문서의 실행
확인은 전부 3.13.1 에서 했으므로 3.14 의 동작은 직접 검증하지 못했습니다.
당장 이 코드에 영향은 없지만, "애너테이션은 문자열이다"라는 지식이 영구적이지
않다는 점만 기억해 두면 됩니다.

**없으면 어떻게 되나** — 이 줄을 지우면 `entities.py`, `tx_id.py`, `unit_of_work.py`
등이 **import 되는 순간** `NameError` 로 죽습니다. 되살리려면 자기 참조 애너테이션을
전부 `-> "Transaction"` 처럼 따옴표로 감싸야 합니다.

---

### `X | Y` 유니온 (PEP 604) 와 `list[str]` 내장 제네릭 (PEP 585)

**어디서 왔나**

- **PEP 585** *Type Hinting Generics In Standard Collections*, 파이썬 **3.9**.
  `list[str]`, `dict[str, int]`, `tuple[str, ...]` 처럼 **내장 타입에 직접 첨자**를
  붙일 수 있게 되었습니다. 그전에는 `typing.List[str]` 을 써야 했습니다.
- **PEP 604** *Allow writing union types as X | Y*, 파이썬 **3.10**.
  그전에는 `typing.Optional[str]` 또는 `typing.Union[str, None]` 이었습니다.

**무엇으로 풀리나** — 둘 다 진짜 런타임 객체를 만듭니다(문자열 트릭이 아닙니다).

```
>>> list[str]
list[str]                     type: <class 'types.GenericAlias'>
>>> int | None
int | None                    type: <class 'types.UnionType'>
>>> typing.Optional[int]
typing.Optional[int]          type: <class 'typing._UnionGenericAlias'>
```

`types.UnionType` 은 3.10 에, `types.GenericAlias` 는 3.9 에 생긴 타입입니다.
`X | Y` 는 `type.__or__` 를 호출하는 것이므로 **일반 연산자**입니다. 그래서
애너테이션 밖에서도 씁니다 — `isinstance(x, int | str)` 이 됩니다(3.10+).

**이 소스에서** — `Optional`/`Union`/`List`/`Dict` 는 **한 번도 등장하지 않습니다.**
전부 새 문법입니다.

budget_app/domain/entities.py:60-66
```python
    id: TransactionId
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: tuple[str, ...] = ()
```

budget_app/storage/csv_io.py:47-53
```python
    tx_id: TransactionId | None
    type: str
    date: str
    amount: int
    category: str
    memo: str
    tags: list[str]
```

**`requires-python = ">=3.10"` 과의 관계 — 정직하게** 이 프로젝트의 `X | Y` 는
**전부 애너테이션 자리**에 있습니다. 그리고 **애너테이션을 쓰는 모든 모듈**에
`from __future__ import annotations` 가 있으므로 그 표현들은 **실행되지 않습니다**
(43개 모듈 중 그 줄이 없는 15개는 `config`·`messages` 계열과 `__init__.py`·`__main__.py` 인데, 그
파일들에는 애너테이션 자체가 없습니다). `match`/`case` 같은
3.10 전용 문법도 이 소스에는 없습니다. 즉 `>=3.10` 은 문법이 강제하는 하한선이
아니라 **"이 아래는 지원하지 않겠다"는 선언**에 가깝습니다(`pyproject.toml:11`,
Ruff 의 `target-version = "py310"` 도 같은 선언입니다).

다만 애너테이션이 아닌, **진짜 평가되는** 타입 표현식이 두 부류 있습니다.

budget_app/cli/app.py:26-28
```python
Handler = Callable[[AppContext, argparse.Namespace], int]

HANDLERS: dict[str, Handler] = {
```

`Handler = ...` 는 애너테이션이 아니라 **대입문**이므로 import 시점에 실제로
평가됩니다(`collections.abc.Callable` 에 첨자 → PEP 585 필요). 반대로 바로 아랫줄
`HANDLERS: dict[str, Handler]` 는 변수 애너테이션이라 문자열로 남습니다. 같은 줄에
붙어 있는 두 표현이 서로 다르게 취급되는 좋은 예입니다. 다른 한 부류는
`class TransactionRepository(JsonlStore[Transaction])` 같은 **기반 클래스 표현식**으로,
다음 항목에서 다룹니다.

**없으면 어떻게 되나** — `typing.Optional[str]` 로 되돌리면 동작은 같지만 `typing`
import 가 모든 모듈에 다시 필요해집니다. 더 실질적인 차이는 `str | None | int`
처럼 늘어날 때인데, `Optional` 은 두 개짜리 유니온만 표현하므로 `Union[str, int, None]`
로 갈아타야 하고 그 지점에서 표기가 두 종류로 갈립니다.

---

### `TypeVar` / `Generic` — 런타임에는 아무 검사도 없다 (PEP 484)

**어디서 왔나** — PEP 484 *Type Hints*, 파이썬 3.5. `typing.TypeVar`/`Generic` 이
함께 들어왔습니다. (파이썬 3.12 의 PEP 695 는 `class JsonlStore[T]:` 라는 더 짧은
문법을 추가했지만, `>=3.10` 을 요구하는 이 프로젝트는 옛 표기를 씁니다.)

**무엇으로 풀리나 / 내부에서 무슨 일이** — 핵심은 **런타임 검사가 전혀 없다**는
것입니다. `TypeVar` 는 그냥 이름표 객체이고, `Generic[T]` 를 상속하면 클래스에
`__class_getitem__` 이 생겨 첨자를 붙일 수 있게 될 뿐입니다.

```
>>> JsonlStore[Transaction]
budget_app.storage.jsonl.JsonlStore[budget_app.domain.entities.Transaction]
>>> type(JsonlStore[Transaction])
<class 'typing._GenericAlias'>          ← 클래스가 아니라 '별칭' 객체
>>> JsonlStore[Transaction] is JsonlStore
False
>>> typing.get_origin(JsonlStore[Transaction])
<class 'budget_app.storage.jsonl.JsonlStore'>
>>> JsonlStore.__parameters__
(~T,)
```

그런데 이 별칭을 **호출하면** 결국 원래 클래스의 인스턴스가 나옵니다.

```
>>> s = JsonlStore[Transaction](Path('x.jsonl'))
>>> type(s)
<class 'budget_app.storage.jsonl.JsonlStore'>     ← 별칭이 아니라 원본 클래스
>>> s.__orig_class__
budget_app.storage.jsonl.JsonlStore[...Transaction]   ← 흔적만 남는다
```

상속에서도 같습니다. `class TransactionRepository(JsonlStore[Transaction])` 은
평가되는 순간 별칭을 만들고, `Generic.__mro_entries__` 가 그것을 실제 기반 클래스인
`JsonlStore` 로 바꿔 놓습니다. 원래 적은 표현은 `__orig_bases__` 에만 남습니다.

```
>>> TransactionRepository.__bases__
(<class 'budget_app.storage.jsonl.JsonlStore'>,)                    ← 첨자가 사라졌다
>>> TransactionRepository.__orig_bases__
(budget_app.storage.jsonl.JsonlStore[...Transaction],)              ← 여기 보존
```

**즉 `T` 는 타입 체커와 사람에게만 보이는 정보이고, 실행 중인 파이썬은 `T` 가
무엇인지 알지도, 확인하지도 않습니다.**

**이 소스에서**

budget_app/storage/jsonl.py:35-35
```python
T = TypeVar("T")
```

budget_app/storage/jsonl.py:131-140
```python
class JsonlStore(Generic[T]):
    """JSONL 파일 하나를 다루는 공통 동작.
    ...
    """

    #: 하위 클래스가 지정 — 줄 하나를 세울 dataclass
    entity_cls: type
```

`Generic[T]` 는 기반 클래스 표현식이라 **실제로 평가됩니다.** 그리고 바로 아래에
있는 `entity_cls: type` 이 이 설계의 핵심을 드러냅니다 — 런타임에 실제로 쓰이는
"어떤 엔티티인가" 정보는 `T` 가 아니라 **평범한 클래스 속성 `entity_cls`** 입니다.
`_parse_line` 이 `self.entity_cls.from_dict(data)` 를 호출하는 것이 그 증거입니다
(jsonl.py:187). `T` 가 하는 일은 오직 `stream()` 의 반환 타입을
`Iterator[Transaction]` 으로 좁혀 주는 것뿐입니다.

budget_app/storage/repositories.py:27-27
```python
class TransactionRepository(JsonlStore[Transaction]):
```

세 저장소가 각각 `JsonlStore[Transaction]`, `JsonlStore[Category]`,
`JsonlStore[Budget]` 을 상속합니다(repositories.py:27, 217, 283).

budget_app/cli/prompts.py:25-25
```python
T = TypeVar("T")
```

여기 `T` 는 `ask_until(prompt, validator: Callable[[str], T]) -> T` 에 쓰여
"검증기가 돌려주는 타입이 곧 `ask_until` 의 반환 타입"을 표현합니다
(prompts.py:60). `parse_amount` 를 넘기면 `int`, `parse_date` 를 넘기면 `str` 이라는
관계가 타입으로 적혀 있습니다.

**없으면 어떻게 되나** — 런타임 동작은 **하나도 바뀌지 않습니다.** `Generic[T]` 를
지우고 그냥 `class JsonlStore:` 로 두어도 프로그램은 똑같이 돕니다. 잃는 것은
정적 검사입니다 — `for tx in txs.stream()` 의 `tx` 가 `Transaction` 인지 `Category`
인지 타입 체커가 모르게 되고, `tx.categry` 같은 오타를 잡아 주지 못합니다.
반대로 말하면, **`T` 를 붙였다고 해서 잘못된 타입이 들어오는 것을 막지는 못합니다** —
`JsonlStore[Transaction]` 에 `Budget` 을 넣어도 파이썬은 아무 말도 하지 않습니다.

---

### `collections.abc` 를 `typing` 대신 쓰는 이유

**어디서 왔나** — 추상 기반 클래스는 PEP 3119 *Introducing Abstract Base Classes*
로 도입되었습니다(같은 흐름에서 `abc` 모듈과 컨테이너 ABC 들이 들어왔습니다 —
편의 클래스 `abc.ABC` 는 그보다 한참 뒤에 추가된 별개의 물건이니 도입 시점을
섞어 기억하면 안 됩니다). 컨테이너 ABC 들은 이후 `collections` 에서
`collections.abc` 라는 별도 모듈로 분리되었습니다(로컬 3.13.1 에서
`inspect.getsourcefile(collections.abc)` 는 `Lib/_collections_abc.py` 를 가리킵니다).
PEP 484(3.5)가
`typing.Iterable` 같은 **별칭**을 만든 이유는 그때 `collections.abc.Iterable` 에
첨자를 붙일 수 없었기 때문입니다. PEP 585(3.9)가 그 제약을 없애면서 `typing` 쪽
별칭들은 **비권장(deprecated)** 이 되었습니다.

**무엇으로 풀리나** — 3.13 에서 확인하면 `typing.Iterable` 은 여전히 동작하고
`__origin__` 이 `collections.abc.Iterable` 을 가리킵니다. 즉 한 겹 얇은 포장입니다.

```
>>> typing.Iterator.__origin__ is collections.abc.Iterator
True
>>> collections.abc.Iterator[int]
collections.abc.Iterator[int]        type: <class 'types.GenericAlias'>
```

`typing` 별칭은 `typing._GenericAlias`, `collections.abc` 첨자는 `types.GenericAlias`
로 서로 다른 객체를 만듭니다. 후자가 더 가볍고 인터프리터 내장입니다.
(3.13 에서 `typing.List` 등을 써도 `DeprecationWarning` 이 뜨지는 않습니다 —
비권장이지만 아직 경고를 내지 않는 상태입니다.)

**이 소스에서** — 규칙이 일관됩니다. **`collections.abc` 에 있는 것은 `collections.abc`
에서, 없는 것만 `typing` 에서** 가져옵니다.

budget_app/cli/presenter.py:18-20
```python
from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
```

budget_app/storage/jsonl.py:25-28
```python
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar
```

`Callable`/`Iterable`/`Iterator` 는 `collections.abc` 에서, `Any`/`Generic`/`TypeVar`
는 `collections.abc` 에 존재하지 않으므로 `typing` 에서 가져옵니다. 소스 전체에서
`typing` 이 제공하는 것은 `Any`(7개 모듈 — decorators.py, domain/entities.py,
domain/queries.py, domain/tx_id.py, domain/validators.py, storage/jsonl.py,
storage/unit_of_work.py), `Generic`/`TypeVar`(jsonl.py, prompts.py) 뿐이고,
`List`/`Dict`/`Optional`/`Union` 은 한 번도 나오지 않습니다.

**타입 자리가 아닌 진짜 용도도 있습니다.**

budget_app/domain/validators.py:149-156
```python
    if value is None:
        return []
    if isinstance(value, str):
        items: Iterable[Any] = value.split(config.TAG_SEPARATOR)
    elif isinstance(value, Iterable):
        items = value
    else:
        items = [value]
```

`isinstance(value, Iterable)` 은 애너테이션이 아니라 **실행되는 검사**입니다.
`collections.abc.Iterable` 은 `__subclasshook__` 으로 "`__iter__` 를 가졌는가"를
확인하는 진짜 ABC 이므로, 리스트든 튜플이든 제너레이터든 사용자 정의 클래스든
전부 참이 됩니다. 여기서 주의할 점은 **첨자를 붙인 형태로는 `isinstance` 를 쓸 수
없다**는 것입니다.

```
>>> isinstance([], collections.abc.Iterable[int])
TypeError: isinstance() argument 2 cannot be a parameterized generic
```

즉 `Iterable[Any]`(윗줄의 애너테이션)와 `Iterable`(아랫줄의 `isinstance` 인자)는
같은 이름이지만 서로 다른 역할로 쓰이고 있습니다.

**없으면 어떻게 되나** — `typing.Iterable` 로 바꿔도 지금은 동작합니다. 다만
비권장 경로이고, `pyupgrade` 계열 규칙(이 프로젝트 Ruff 설정의 `UP`)이 자동으로
`collections.abc` 로 되돌리라고 지적합니다. 그리고 `validators.py:153` 의
`isinstance` 자리에서는 의미가 더 분명합니다 — 그 자리는 처음부터 "타입 힌트"가
아니라 **런타임 프로토콜 검사**이므로 `collections.abc` 가 원래 있어야 할 자리입니다.

---

## 2-A. 표준 라이브러리 내부 (1) — json / csv / re / datetime / calendar

> **이 절은 무엇인가** — 여기서부터는 파이썬의 문법이 아니라, 파이썬을 설치하면 딸려 오는 기성품 도구들의 속을 봅니다. 이 절이 다루는 넷은 자료를 글자로 바꿔 파일에 담는 도구, 표 형식으로 주고받는 도구, 글자 모양이 정해진 규칙에 맞는지 검사하는 도구, 날짜를 다루는 도구입니다. 항목 대부분이 결국 같은 곳으로 모입니다 — 기성품은 생각보다 너그러워서 어지간한 입력을 다 받아 주고, 그래서 이 프로그램이 그 위에 자기 기준을 한 겹 더 얹어야 했다는 이야기입니다.

여기서부터는 문법이 아니라 표준 라이브러리입니다. 이 절은 데이터를 읽고 쓰는 네 갈래 — `json`, `csv`, `re`, `datetime`/`calendar` — 가 CPython 안에서 실제로 무엇을 하는지 따라갑니다. 항목 대부분이 같은 결론으로 수렴합니다: **표준 라이브러리 API 는 생각보다 관대하고, 그래서 이 소스가 그 위에 무엇을 덧붙였는가**. `strptime` 이 `"2024-1-5"` 를 받아 준다는 사실 하나가 `parse_date` 의 마지막 줄을 설명합니다.

budget_app 이 실제로 호출하는 표준 라이브러리 API 는 열 몇 개뿐입니다. 이 절은 그 API 들이 CPython 안에서 무엇을 하는지를 따라갑니다. 본문의 실측값은 모두 이 저장소의 로컬 환경(**CPython 3.13.1, Windows**)에서 실행해 확인한 것이며, "3.13.1 에서 확인"이라고 적은 것과 "이 버전에서 도입"이라고 적은 것은 다른 층위의 주장이므로 구분해서 읽으셔야 합니다.

---

### `json.loads` — C 가속기와 순수 파이썬 폴백

**어디서 왔나** — `json` 은 파이썬 2.6 에서 서드파티 `simplejson` 을 표준 라이브러리로 들여온 모듈입니다. 그 전에는 각자 `eval()` 을 쓰거나(임의 코드 실행 위험) 외부 패키지를 깔았습니다. 다만 **2.6 에 들어온 것은 순수 파이썬 구현뿐**이었습니다(`json/decoder.py`, `json/scanner.py`, `json/encoder.py`). C 로 짠 같은 파서(`Modules/_json.c`)는 **2.7 / 3.1 에서 뒤늦게 붙었고**(bpo-4136, simplejson 2.0.9 반영), 그때부터 `c_make_scanner or py_make_scanner` 라는 **이중 구조**가 되어 지금까지 이어집니다.

**내부에서 무슨 일이 일어나나** — `json/scanner.py` 와 `json/decoder.py` 의 마지막 줄들이 이 모듈 전체의 성격을 요약합니다.

```python
# json/scanner.py 마지막 줄
make_scanner = c_make_scanner or py_make_scanner

# json/decoder.py
scanstring = c_scanstring or py_scanstring
```

`from _json import ...` 를 `try` 로 감싸고 실패하면 `None` 을 넣어 두었다가, `or` 로 골라 씁니다. 즉 **C 확장이 있으면 C, 없으면 순수 파이썬**이며 두 경로의 의미는 동일합니다. 3.13.1 에서는 C 쪽이 잡혔습니다.

이 `or` 폴백 구조 자체가 **위 역사의 흔적**입니다. 순수 파이썬이 먼저 있었고 C 가 나중에 얹혔기 때문에, 코드는 지금도 "C 가 없을 수도 있다"를 전제로 쓰여 있습니다. 순수 파이썬 경로는 죽은 코드가 아니라 **C 확장을 빌드하지 않은 배포판에서 실제로 도는 경로**입니다.

```
>>> json.scanner.c_make_scanner        <class '_json.Scanner'>
>>> json.decoder.c_scanstring          <built-in function scanstring>
```

`json.loads(s)` 호출은 다음 순서로 흘러갑니다.

1. `s` 가 `str` 이면 맨 앞이 `\ufeff`(U+FEFF, BOM)인지 본다 → 맞으면 `JSONDecodeError("Unexpected UTF-8 BOM (decode using utf-8-sig)")`.
2. `str` 이 아니고 `bytes`/`bytearray` 도 아니면 **`TypeError`**. (여기서 나오는 것은 `JSONDecodeError` 가 아닙니다.)
3. 커스터마이즈 인자(`object_hook`, `parse_int` …)를 하나도 안 줬으면 **모듈 전역에 미리 만들어 둔 `_default_decoder` 를 재사용**한다 → 호출마다 디코더 객체를 새로 만들지 않는다.
4. `decoder.decode(s)` → `raw_decode` → `scan_once`. `scan_once` 가 값 하나를 읽고 끝난 위치를 돌려주면, `decode` 는 남은 문자가 공백뿐인지 확인하고 아니면 `JSONDecodeError("Extra data")` 를 던집니다.

3번 덕분에 `json.loads` 는 인자 없이 부르는 것이 가장 빠른 경로입니다. budget_app 은 정확히 그렇게 부릅니다.

**이 소스에서**

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

한 줄이 곧 한 JSON 문서인 JSONL 포맷이라 `loads` 를 줄 단위로 부릅니다. 실패해도 예외를 위로 던지지 않고 `RawLine.error` 에 `str(exc)` 로 담아 두는데, 그 문자열은 `JSONDecodeError.__str__` 이 만들어 주는 위치 정보 포함 메시지입니다(실측).

```
json.loads('{oops')  →  Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
json.loads('{"a": 1')→  Expecting ',' delimiter: line 1 column 8 (char 7)
```

`e.msg` / `e.lineno` / `e.colno` / `e.pos` 로 나눠 꺼낼 수도 있지만, 이 소스는 통째로 로그에 흘립니다(`stream()` 의 경고 로그).

**없으면 어떻게 되나** — `json.loads` 대신 손으로 파서를 짜면 이스케이프(`\u`, `\"`), 중첩, 숫자 문법을 전부 다시 구현해야 합니다. 더 중요한 것은 `except json.JSONDecodeError` 라는 **명확한 실패 신호**입니다. 이것이 있어서 "이 줄은 JSON 이 아니다"와 "JSON 은 맞지만 규칙 위반이다"를 두 개의 `try` 블록으로 나눌 수 있고, `RawLine` 의 세 상태(원문만 / dict 까지 / 엔티티까지)가 성립합니다.

> 곁가지 하나: 이 소스는 JSONL 을 `utf-8` 로 읽습니다(`FILE_ENCODING`). 사용자가 편집기로 `transactions.jsonl` 을 열었다 BOM 을 붙여 저장하면 첫 줄만 `Unexpected UTF-8 BOM` 으로 손상 줄 처리되고 나머지는 멀쩡합니다. CSV 와 달리 BOM 흡수 정책을 두지 않은 것은, JSONL 은 이 프로그램만 쓰는 내부 포맷이기 때문입니다.

---

### `json.JSONDecodeError` 와 `TypeError` — 왜 둘 다 잡아야 하나

**어디서 왔나** — 예전에는 JSON 파싱 실패가 그냥 `ValueError` 였습니다. 위치 정보를 담은 전용 예외 `json.JSONDecodeError` 가 뒤에 추가되면서, **기존 `except ValueError` 코드를 깨뜨리지 않으려고 `ValueError` 를 상속**했습니다. 3.13.1 에서 확인한 상속 사슬입니다.

```
json.JSONDecodeError → ValueError → Exception → BaseException → object
```

**무엇이 문제인가** — `json.loads` 가 성공했다는 것은 "**유효한 JSON 값** 하나를 읽었다"는 뜻이지 "dict 를 읽었다"가 아닙니다. JSON 의 최상위 값은 객체·배열·문자열·숫자·`true`/`false`/`null` 무엇이든 될 수 있습니다(실측).

```
json.loads('[1,2]')  → [1, 2]      (list)
json.loads('12')     → 12          (int)
json.loads('null')   → None
json.loads('"abc"')  → 'abc'
json.loads('NaN')    → nan         ← 표준 JSON 은 아니지만 파이썬은 받아 줍니다
```

그다음 `Transaction.from_dict(data)` 가 `data["id"]` 를 하면 무엇이 나오는지가 핵심입니다. 전부 `TypeError` 이고 종류마다 문구만 다릅니다.

```
[1,2]["id"]  → TypeError: list indices must be integers or slices, not str
12["id"]     → TypeError: 'int' object is not subscriptable
None["id"]   → TypeError: 'NoneType' object is not subscriptable
"abc"["id"]  → TypeError: string indices must be integers, not 'str'
```

**이 소스에서**

budget_app/storage/jsonl.py:37-40
```python
# 한 줄을 도메인 객체로 세우다 실패할 수 있는 경우들.
# JSONDecodeError: JSON 이 아님 / KeyError: 필수 키 없음 / ValidationError: 규칙 위반
# TypeError: JSON 은 맞지만 객체가 아님(예: 최상위가 리스트)
_LINE_ERRORS = (json.JSONDecodeError, ValidationError, KeyError, TypeError)
```

네 개가 각각 다른 층의 실패입니다.

| 예외 | 어느 층에서 | 상위 타입 |
|---|---|---|
| `json.JSONDecodeError` | JSON 문법 | `ValueError` |
| `TypeError` | JSON 은 맞지만 dict 가 아님 | (내장) |
| `KeyError` | 필수 키 없음 — `data["id"]` 등 하드 접근 | `LookupError` |
| `ValidationError` | 도메인 규칙 위반 | `ValueError` (budget_app/errors.py:33) |

`ValidationError` 와 `JSONDecodeError` 는 **둘 다 `ValueError` 의 자식이지만 서로 남남**이라, 하나를 잡아도 다른 하나는 안 잡힙니다. 그래서 튜플에 나란히 적혀 있습니다. `except ValueError` 한 줄로 줄일 수도 있지만, 그러면 도메인 코드가 실수로 던진 무관한 `ValueError`(예: `int("abc")`)까지 "손상된 줄"로 조용히 삼켜집니다.

**없으면 어떻게 되나** — `TypeError` 를 빼면 `[{"id": ...}]` 처럼 **배열로 감싸 저장된 한 줄**(다른 도구가 만든 파일, 손으로 편집하다 대괄호를 남긴 파일)이 격리되지 않고 `_parse_line` 밖으로 튀어나갑니다. `iter_raw()` 는 제너레이터라 그 예외가 `stream()`, `plan_rewrite()`, ID 스캔까지 거슬러 올라가 **`list` 명령 하나가 통째로 죽습니다**. 한 줄의 문제가 파일 전체의 문제가 되는 것이 이 모듈이 가장 피하려는 상황입니다.

---

### `json.dumps(..., ensure_ascii=False)` — 사람이 읽을 수 있는 파일

**어디서 왔나** — `ensure_ascii=True` 가 기본값인 것은 JSON 이 처음부터 "7비트 ASCII 로만 이루어진 텍스트로도 표현 가능하다"를 보장하기 위해서였습니다. 인코딩 협상이 불안하던 시절 안전한 기본값이었고, 지금도 기본값은 그대로입니다.

**무엇이 달라지나** — 인코더 선택이 딱 한 줄로 갈립니다(`json/encoder.py`).

```python
encode_basestring_ascii = (c_encode_basestring_ascii or py_encode_basestring_ascii)
...
    _encoder = encode_basestring_ascii    # ensure_ascii=True
    _encoder = encode_basestring          # ensure_ascii=False
```

`..._ascii` 쪽만 비-ASCII 문자를 `\uXXXX` 로 바꿉니다. 실측입니다.

```
>>> d = {"id": "TX-000001", "memo": "점심", "tags": ["식비", "현금"]}

json.dumps(d)                     # ensure_ascii=True (기본값)
{"id": "TX-000001", "memo": "\uc810\uc2ec", "tags": ["\uc2dd\ube44", "\ud604\uae08"]}

json.dumps(d, ensure_ascii=False)
{"id": "TX-000001", "memo": "점심", "tags": ["식비", "현금"]}

str 길이       85 → 55
utf-8 바이트   85 → 67
```

`점` 한 글자가 `\uc810` 여섯 글자로 부풀고, 그 여섯 글자는 전부 ASCII 라 1바이트씩입니다. 반대로 `ensure_ascii=False` 는 `점` 을 그대로 두고 UTF-8 이 3바이트로 인코딩합니다 — 그래서 문자 수는 55 로 줄지만 바이트는 67 로, 줄어드는 비율이 다릅니다.

여기서 **반드시 짚어야 할 것**은, 어느 쪽이든 **왕복 동등성은 지켜진다**는 사실입니다.

```
json.loads(a) == d          True     (ensure_ascii=True 로 찍은 것)
json.loads(b) == d          True     (False 로 찍은 것)
json.loads(a) == json.loads(b)  True
```

즉 `ensure_ascii=False` 는 **정확성의 문제가 아니라 가독성·크기의 문제**입니다. 이 소스처럼 "데이터 파일을 사용자가 직접 열어 볼 수 있어야 한다"가 목표일 때만 의미가 있습니다. 한글 파일 크기가 약 21% 줄어드는 것은 덤입니다(위 실측 85바이트 → 67바이트). `점` 한 글자를 이스케이프 표기 `점` 으로 적으면 ASCII 6글자라 6바이트가 되지만, UTF-8 로 그냥 적으면 3바이트입니다 — **한글이 원래 6바이트인 것이 아니라, 이스케이프 표기가 6바이트인 것**입니다.

구분자 기본값도 실측으로 확인해 둡니다. `separators` 를 주지 않으면 `(', ', ': ')` 이고, `indent` 를 주면 항목 구분자에서 공백이 빠져 `(',', ': ')` 가 됩니다.

```
json.dumps({'a':1,'b':2})            → '{"a": 1, "b": 2}'
json.dumps({'a':1,'b':2}, indent=2)  → '{\n  "a": 1,\n  "b": 2\n}'
```

**이 소스에서**

budget_app/storage/jsonl.py:207-208
```python
    def _encode(self, entity: T) -> str:
        return json.dumps(entity.to_dict(), ensure_ascii=False)
```

`indent` 를 주지 않는 것이 여기서는 선택이 아니라 **필수**입니다. JSONL 은 "한 줄 = 한 레코드"이므로 들여쓰기를 켜면 개행이 들어가 포맷 자체가 깨집니다. 기본 구분자 `", "`/`": "` 는 그대로 두는데, `separators=(",", ":")` 로 공백을 뺄 수도 있지만 그러면 사람이 읽기 어려워져 `ensure_ascii=False` 를 준 이유와 정면으로 충돌합니다.

이 함수가 만든 문자열은 `plan_rewrite` 에서 **원문과 직접 비교**됩니다.

budget_app/storage/jsonl.py:298-302
```python
            encoded = self._encode(new_entity)
            if encoded != raw.text:
                # 값이 바뀌었거나, 정규화로 표기가 바뀌었다(비패딩 날짜 자동 치유 등).
                changed = True
            lines.append(encoded)
```

`_encode` 가 항상 같은 인자로 호출되기 때문에 이 문자열 비교가 성립합니다. 만약 어떤 경로는 `ensure_ascii=True`, 어떤 경로는 `False` 로 찍었다면 내용이 똑같은 줄도 문자열은 달라져서 `changed` 가 늘 `True` 가 되고, 조회성 명령이 매번 파일을 통째로 다시 쓰게 됩니다.

**없으면 어떻게 되나** — `ensure_ascii` 를 기본값으로 두면 데이터는 멀쩡하지만 `transactions.jsonl` 을 열었을 때 메모와 카테고리가 전부 `점심` 처럼 보입니다. "표준 라이브러리만 쓰는 파일 기반"이라는 이 프로그램의 성격상, 사용자가 파일을 직접 확인할 수 있다는 점이 기능의 일부입니다.

---

### `csv.DictReader` — `reader` 위의 얇은 래퍼와 **지연** `fieldnames`

**어디서 왔나** — `csv` 모듈은 **PEP 305 (CSV File API)** 로 표준 라이브러리에 들어왔습니다. 이 사실은 모듈 자신의 docstring 에 적혀 있습니다: *"implements the interface described by PEP 305"*. 그전에는 다들 `line.split(",")` 을 썼고, 그 docstring 이 바로 다음 줄에서 그것이 왜 실패하는지 경고합니다 — 따옴표로 감싼 필드 안의 쉼표와 개행 때문입니다.

**내부에서 무슨 일이 일어나나** — `DictReader` 는 C 로 짠 `_csv.reader` 를 감싼 **순수 파이썬 클래스**입니다. 실제로 파싱하는 상태 기계는 C 쪽에 있고, `DictReader` 는 그 결과 리스트를 dict 로 바꾸는 일만 합니다.

```python
class DictReader:
    def __init__(self, f, fieldnames=None, restkey=None, restval=None, ...):
        self._fieldnames = fieldnames
        self.restkey = restkey          # key to catch long rows
        self.restval = restval          # default value for short rows
        self.reader = reader(f, dialect, *args, **kwds)   # ← _csv.reader
        self.line_num = 0

    @property
    def fieldnames(self):
        if self._fieldnames is None:
            try:
                self._fieldnames = next(self.reader)      # ← 첫 행을 소비한다
            except StopIteration:
                pass
        self.line_num = self.reader.line_num
        return self._fieldnames
```

핵심은 `fieldnames` 가 **속성이 아니라 프로퍼티**라는 점입니다. 생성자는 헤더를 읽지 않습니다. **처음 `reader.fieldnames` 를 읽는 순간** `next(self.reader)` 가 실행돼 첫 행이 소비되고, 그 결과가 `_fieldnames` 에 캐시됩니다. `__next__` 도 `if self.line_num == 0: self.fieldnames` 로 같은 프로퍼티를 부르는데, 주석에 *"Used only for its side effect"* 라고 적혀 있습니다 — 값이 아니라 **첫 행을 건너뛰는 부수효과**를 노린 호출입니다.

파일이 비어 있으면 `next()` 가 `StopIteration` 을 내고 `pass` 로 삼켜져 `fieldnames` 는 **`None`** 이 됩니다(실측 확인).

행 길이가 헤더와 다를 때의 처리는 `__next__` 의 마지막 여섯 줄입니다.

```python
        d = dict(zip(self.fieldnames, row))
        lf = len(self.fieldnames); lr = len(row)
        if lf < lr:
            d[self.restkey] = row[lf:]          # 긴 행 → 잉여는 restkey 에 리스트로
        elif lf > lr:
            for key in self.fieldnames[lr:]:
                d[key] = self.restval           # 짧은 행 → 나머지 키는 restval
```

`restkey`/`restval` 은 **둘 다 기본이 `None`** 입니다(`DictWriter` 의 `restval` 기본값 `""` 과 다릅니다). 실측입니다.

```
헤더 a,b,c  /  행 1,2      → {'a': '1', 'b': '2', 'c': None}
헤더 a,b,c  /  행 1,2,3,4,5 → {'a': '1', 'b': '2', 'c': '3', None: ['4', '5']}
```

**이 소스에서**

budget_app/storage/csv_io.py:82-87
```python
    with open(path, encoding=config.CSV_READ_ENCODING, newline="") as f:
        reader = csv.DictReader(f)
        _check_header(path, reader.fieldnames)
        # ``yield from`` 이라 이 함수가 소비되는 동안 ``with`` 블록이 살아 있고,
        # 파일은 마지막 행을 꺼낸 뒤에 닫힌다(제너레이터라 그 시점이 호출자에 달렸다).
        yield from enumerate(reader, start=config.CSV_DATA_START_LINE)
```

`_check_header(path, reader.fieldnames)` 이 **바로 그 지연 시점을 이용합니다.** 이 한 줄이 (1) 헤더 행을 소비하고 (2) 검증하고 (3) 그 결과를 캐시하는 세 가지를 한꺼번에 합니다. 다음 줄의 `enumerate(reader, ...)` 는 이미 헤더가 소비된 상태에서 시작하므로 데이터 행부터 나옵니다.

budget_app/storage/csv_io.py:90-94
```python
def _check_header(path: Path, fieldnames: Iterable[str] | None) -> None:
    names = list(fieldnames or [])
    if not names:
        raise AppError(
            messages.ERR_CSV_NO_HEADER.format(path=path),
```

`fieldnames` 가 `None` 일 수 있다는 것이 시그니처 타입에 그대로 드러나 있고(`Iterable[str] | None`), `list(fieldnames or [])` 가 그 `None` 과 빈 리스트를 한 번에 처리합니다. **빈 파일 → `fieldnames is None` → `ERR_CSV_NO_HEADER`** 라는 경로가 여기서 완성됩니다.

짧은 행이 `restval=None` 으로 채워진다는 사실도 이 소스의 오류 메시지에 영향을 줍니다.

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

헤더가 `date,type,category,amount` 인데 행이 `2024-01-01,expense` 두 칸뿐이면, `row["amount"]` 는 **`KeyError` 가 아니라 `None`** 입니다. 그래서 `parse_amount(None)` → `str(None).strip()` → `"None"` → `_INTEGER` 불일치 → `ValidationError` 가 나고, 사용자는 "그 줄의 금액이 잘못됐다"는 (맞는) 메시지를 받습니다. `row["type"]` 처럼 하드 접근을 쓰면서도 KeyError 가 실전에서 잘 안 나오는 이유가 이것입니다 — `_check_header` 가 필수 컬럼의 **존재**를 이미 보장했고, DictReader 가 **모든 헤더 키를 채워** 주기 때문입니다. 그럼에도 `_prepare` 가 `except (ValidationError, KeyError)` 로 둘 다 받는 것은 방어입니다.

반대로 **긴 행의 잉여 값은 `row[None]` 에 담겨 아무도 읽지 않습니다.** `parse_row` 는 이름 있는 컬럼만 꺼내므로, 컬럼이 남는 CSV 는 오류 없이 초과분이 버려집니다. 이것은 "필수 컬럼만 맞으면 외부 CSV 를 받아 준다"는 이 모듈의 관용 정책과 일치하는 동작입니다.

한 가지 정확히 알아 둘 함정은 **줄 번호**입니다.

budget_app/storage/config.py:45
```python
CSV_DATA_START_LINE = 2  # 1행은 헤더
```

`enumerate(reader, start=2)` 는 **레코드 번호**를 셉니다. 반면 `reader.line_num` 은 **물리적 파일 줄**을 셉니다. 따옴표 안에 개행이 들어간 메모가 있으면 둘이 어긋납니다(실측).

```
enumerate=2  reader.line_num=3  row={'a': 'x\ny', 'b': '2'}
enumerate=3  reader.line_num=4  row={'a': '3', 'b': '4'}
```

즉 여러 줄 메모가 섞인 CSV 를 가져오다 오류가 나면, 보고되는 번호가 편집기의 줄 번호와 한 칸씩 밀립니다.

**없으면 어떻게 되나** — `DictReader` 없이 `csv.reader` 만 쓰면 컬럼 순서에 위치로 의존하게 됩니다. 이 소스는 `CSV_REQUIRED_COLUMNS` 만 있으면 순서가 어떻든, `id`/`memo`/`tags` 가 없든 받아들이는데(엑셀·타 가계부 호환), 그 관용성은 전적으로 "이름으로 꺼낸다"에서 나옵니다.

---

### `csv.DictWriter.writerow` — `_dict_to_list` 가 순서를 맞춘다

**내부에서 무슨 일이 일어나나** — `DictWriter` 도 `_csv.writer` 위의 얇은 파이썬 래퍼이며, 실질은 `_dict_to_list` 한 함수입니다.

```python
    def _dict_to_list(self, rowdict):
        if self.extrasaction == "raise":
            wrong_fields = rowdict.keys() - self.fieldnames
            if wrong_fields:
                raise ValueError("dict contains fields not in fieldnames: "
                                 + ", ".join([repr(x) for x in wrong_fields]))
        return (rowdict.get(key, self.restval) for key in self.fieldnames)

    def writerow(self, rowdict):
        return self.writer.writerow(self._dict_to_list(rowdict))
```

읽어야 할 것이 세 가지입니다.

1. **출력 순서는 dict 순서가 아니라 `fieldnames` 순서입니다.** 마지막 줄의 제너레이터가 `fieldnames` 를 순회합니다. dict 에 어떤 순서로 넣었는지는 전혀 상관없습니다.
2. **키가 없으면 `restval` 로 채웁니다 — 오류가 아닙니다.** `rowdict.get(key, self.restval)` 이고 `DictWriter.restval` 의 기본값은 `""` 입니다.
3. **오류가 나는 것은 반대 방향, 즉 `fieldnames` 에 없는 키가 dict 에 있을 때입니다.** `rowdict.keys() - self.fieldnames` 는 dict 의 키뷰가 지원하는 집합 차집합 연산이고, 남는 것이 있으면 `ValueError` 입니다. 기본 `extrasaction="raise"` 라 켜져 있습니다.

실측으로 두 방향을 나란히 확인합니다.

```
fieldnames=['a','b','c']
writerow({'a':1,'c':3})            → 'a,b,c\r\n1,,3\r\n'      ← b 는 restval('')
writerow({'a':1,'b':2,'c':3,'z':9})→ ValueError: dict contains fields not in fieldnames: 'z'
```

`writeheader()` 도 특별한 것이 아니라 `writerow(dict(zip(fieldnames, fieldnames)))` 입니다 — 헤더 행조차 같은 경로로 나갑니다.

**이 소스에서**

budget_app/storage/csv_io.py:139-148
```python
    fieldnames = list(config.CSV_FIELDS if include_id else config.CSV_FIELDS_WITHOUT_ID)

    count = 0
    with open(path, "w", encoding=config.CSV_ENCODING, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tx in txs:
            writer.writerow(_to_row(tx, include_id))
            count += 1
    return count
```

budget_app/storage/csv_io.py:151-163
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
    if include_id:
        # 값 객체는 경계에서 원시 값으로 푼다 (CSV 셀은 문자열이어야 한다).
        row[config.CSV_ID_COLUMN] = tx.id.value
    return row
```

`_to_row` 가 만드는 dict 의 순서(`date` 먼저, `id` 가 맨 뒤)와 실제 CSV 컬럼 순서(`CSV_FIELDS = ("id", "date", ...)` 라 `id` 가 맨 앞)가 **다릅니다.** 그런데도 결과가 맞는 이유가 위의 1번입니다. `_dict_to_list` 가 `fieldnames` 순서로 뽑아 가기 때문에 dict 를 어떤 순서로 만들어도 상관없습니다.

그리고 `include_id` 플래그가 **두 곳에 같이** 전달되는 것이 3번 때문입니다. `fieldnames` 는 `include_id` 로 고르고, `_to_row(tx, include_id)` 도 같은 값을 받습니다. 둘이 어긋나 `include_id=False` 인데 `_to_row` 가 `id` 를 넣으면 그 즉시 `ValueError: dict contains fields not in fieldnames: 'id'` 가 나서 **조용히 잘못된 파일이 나오는 대신 멈춥니다.** 반대 방향(fieldnames 에는 `id` 가 있는데 row 에 없음)은 오류 없이 빈 칸이 되므로, 이 코드가 두 값을 한 인자로 묶어 넘기는 것이 유일한 방어입니다.

`row[config.CSV_ID_COLUMN] = tx.id.value` 에서 `TransactionId` 객체가 아니라 `.value` 문자열을 넣는 것도 필수입니다. `_csv.writer` 는 문자열이 아닌 값에 `str()` 을 적용하므로 값 객체를 그대로 넣으면 `TransactionId(value='TX-000001')` 같은 repr 이 셀에 박혀 왕복이 깨집니다.

`amount` 는 `int` 그대로 넣는데, 이것은 `str(1000)` → `"1000"` 이 원하는 결과와 같아서 안전한 경우입니다.

---

### `open(..., newline="")` — **csv 모듈이 요구하는 사항**

**어디서 왔나** — 파이썬 3 의 텍스트 I/O(`io.TextIOWrapper`)는 **범용 개행(universal newlines)** 변환을 기본으로 켭니다. `newline=None` 이면 읽을 때 `\r`, `\n`, `\r\n` 을 전부 `\n` 으로 바꿔 주고, 쓸 때 `\n` 을 `os.linesep`(Windows 에서 `\r\n`)으로 바꿉니다. 파이썬 2 의 `open(..., "rb")` / `"rU"` 로 갈라져 있던 것이 3 에서 `newline` 매개변수로 정리됐습니다.

**왜 CSV 와 충돌하나** — CSV 에서 `\r\n` 은 두 가지 역할을 겸합니다.

- **행 종결자**로서의 `\r\n` (`csv.excel.lineterminator` 의 기본값이 정확히 `'\r\n'` 입니다)
- **따옴표 안 필드의 내용**으로서의 개행 — 여러 줄 메모는 합법적인 CSV 입니다

텍스트 계층은 이 둘을 구분할 수 없습니다. 개행처럼 생긴 것을 전부 똑같이 변환하기 때문입니다. 그래서 csv 모듈은 "개행 변환을 끄고 나에게 원문을 달라"고 요구합니다. `newline=""` 이 정확히 그 뜻입니다 — 변환 없음.

실측으로 무엇이 깨지는지 보겠습니다(Windows, 메모에 `\n` 이 든 행 하나).

```
newline 미지정   b'memo\r\r\n"line1\r\nline2"\r\r\nplain\r\r\n'
newline=""       b'memo\r\n"line1\nline2"\r\nplain\r\n'
```

두 곳이 동시에 망가집니다.

1. **행 종결자가 `\r\r\n`** 이 됐습니다. csv 가 쓴 `\r\n` 의 `\n` 부분이 다시 `\r\n` 으로 번역돼 `\r` + `\r\n` 이 된 것입니다. 파이썬 자신은 관대해서 다시 읽히지만, 엄격한 파서나 스프레드시트에서는 빈 행으로 보이거나 오류가 납니다.
2. **따옴표 안의 내용이 바뀌었습니다.** 사용자가 저장한 `line1\nline2` 가 파일에는 `line1\r\nline2` 로 들어갔습니다. 다시 읽으면 `'line1\r\nline2'` — **오류 없이 데이터가 달라지는** 부류입니다.

읽을 때도 같은 이유로 필요합니다.

```
파일 내용: b'memo\r\n"line1\r\nline2"\r\nplain\r\n'
newline="" 로 읽으면    ['line1\r\nline2', 'plain']   ← 원문 그대로
newline=None 로 읽으면  ['line1\nline2',  'plain']   ← \r\n 이 \n 으로 번역됨
```

**이 소스에서** — CSV 는 읽기·쓰기 양쪽 모두 `newline=""` 입니다.

budget_app/storage/csv_io.py:82-83
```python
    with open(path, encoding=config.CSV_READ_ENCODING, newline="") as f:
        reader = csv.DictReader(f)
```

budget_app/storage/csv_io.py:142-143
```python
    with open(path, "w", encoding=config.CSV_ENCODING, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
```

**JSONL 은 다릅니다** — 쓰기에서 `newline="\n"` 을 씁니다.

budget_app/storage/jsonl.py:61-69
```python
    with open(
        tmp,
        "w",
        encoding=config.FILE_ENCODING,
        errors=config.FILE_ERRORS,
        newline=config.LINE_TERMINATOR,
    ) as f:
        for line in lines:
            f.write(line + config.LINE_TERMINATOR)
```

budget_app/storage/config.py:26
```python
LINE_TERMINATOR = "\n"
```

이 대조가 이 절의 핵심입니다. **쓰기에서 `newline=""` 과 `newline="\n"` 은 완전히 같은 동작**입니다 — 둘 다 "변환하지 않음"입니다(실측).

```
newline=""    로 'a\nb\n' 쓰기 → b'a\nb\n'
newline="\n"  로 'a\nb\n' 쓰기 → b'a\nb\n'
newline=None  로 'a\nb\n' 쓰기 → b'a\r\nb\r\n'    ← Windows
```

그럼 왜 다르게 적었을까요. **의도를 드러내기 위해서입니다.**

- CSV 의 `newline=""` 은 "**csv 모듈이 시킨 것**"입니다. 이 자리에 다른 값을 넣으면 안 됩니다.
- JSONL 의 `newline="\n"` 은 "**이 파일의 줄 종결자는 `\n` 이다**"라는 이 프로그램 자신의 포맷 선언이고, 그래서 상수 `LINE_TERMINATOR` 를 참조합니다. 같은 상수가 `f.write(line + config.LINE_TERMINATOR)` 와 `_has_torn_tail()` 의 마지막 바이트 비교에도 쓰입니다.

budget_app/storage/jsonl.py:258-260
```python
            with open(self.path, "rb") as f:
                f.seek(-1, os.SEEK_END)
                return f.read(1) != config.LINE_TERMINATOR.encode(config.FILE_ENCODING)
```

"찢어진 꼬리" 판정이 **바이트 단위 비교**라는 점을 보세요. 만약 쓰기에서 `newline` 을 지정하지 않아 Windows 에서 `\r\n` 이 나갔다면, 마지막 바이트는 `\n` 이라 이 검사는 통과하지만 파일 안에는 `\r` 이 섞여 들어갑니다. 그러면 `iter_raw()` 의 `raw.strip()` 이 `\r` 을 떼 주긴 해도, `plan_rewrite` 가 보존한 손상 줄의 원문 `text` 와 새로 인코딩한 문자열이 미묘하게 달라집니다. `newline=LINE_TERMINATOR` 는 **플랫폼과 무관하게 파일 바이트를 하나로 고정**해 그 종류의 흔들림을 원천 차단합니다.

읽기 쪽(`iter_raw`)은 `newline` 을 지정하지 않는데, 이것은 의도적으로 관대한 선택입니다. 다른 플랫폼에서 만들어졌거나 편집기가 CRLF 로 저장한 파일도 범용 개행 덕에 그대로 읽히고, 어차피 `line = raw.strip()` 이 잔여 공백을 떼기 때문입니다.

**없으면 어떻게 되나** — CSV 에서 `newline=""` 을 빼면 Windows 에서 내보낸 파일이 위처럼 `\r\r\n` 로 오염되고, 여러 줄 메모의 내용이 조용히 바뀝니다. 이 프로그램이 가장 강조하는 성질인 **export → import 왕복 동등성**이 그 순간 깨집니다.

---

### `utf-8-sig` vs `utf-8` — 읽을 때만 BOM 을 흡수하는 비대칭

**어디서 왔나** — BOM(Byte Order Mark, U+FEFF)은 원래 UTF-16/32 의 바이트 순서를 알리는 표식입니다. UTF-8 은 바이트 순서라는 개념 자체가 없어 BOM 이 필요 없지만, 마이크로소프트 도구들이 "이 파일은 UTF-8 이다"라는 **표시**로 `EF BB BF` 3바이트를 붙이는 관행을 만들었습니다. 파이썬은 그 관행을 다루려고 `utf-8-sig` 코덱을 따로 둡니다("sig" 는 signature).

**codecs 가 무엇을 하나** — `utf-8-sig` 는 방향에 따라 비대칭입니다.

- **디코딩**: 맨 앞 3바이트가 `b'\xef\xbb\xbf'` 이면 **떼어 내고** 나머지를 UTF-8 로 읽습니다. BOM 이 없으면 그냥 UTF-8 과 동일하게 동작합니다(실측: BOM 없는 파일도 정상적으로 읽힙니다).
- **인코딩**: 출력 맨 앞에 **BOM 을 붙입니다**.

반면 `utf-8` 코덱은 BOM 을 특별 취급하지 않아서, BOM 이 있으면 그것을 U+FEFF 라는 **평범한 문자 하나**로 읽어들입니다.

실측입니다.

```
파일: BOM + 'id,date\nTX-000001,2024-01-01\n'
utf-8     로 열면 → fieldnames = ['\ufeffid', 'date']   ← 첫 컬럼명이 오염
utf-8-sig 로 열면 → fieldnames = ['id', 'date']

쓰기:
utf-8-sig → b'\xef\xbb\xbfid\n'
utf-8     → b'id\n'
```

`'\ufeffid'` 는 `'id'` 와 **다른 문자열**입니다. 그래서 `_check_header` 의 `"id" not in names` 판정이 어긋나고, `row["date"]` 같은 키 접근도 첫 컬럼에서만 실패합니다. 첫 컬럼 하나만 이상해지는, 원인을 짐작하기 어려운 버그입니다.

**이 소스에서**

budget_app/storage/config.py:36-40
```python
# CSV 교환 스키마 — `id` 는 **선택** 컬럼이다(왕복 시 중복 방지, 외부 CSV 호환 유지)
#: 쓰기는 BOM 없는 UTF-8 고정(왕복 안전성). 읽기만 utf-8-sig 로 BOM 을 흡수한다 —
#: 엑셀이 저장한 CSV 는 BOM 이 붙고, 그러면 첫 컬럼명이 깨져 헤더 검증이 실패한다.
CSV_ENCODING = "utf-8"
CSV_READ_ENCODING = "utf-8-sig"
```

읽기와 쓰기에 **다른 상수**를 둔 것이 정책 그 자체입니다.

- **읽기 = `utf-8-sig`** → 엑셀이 저장한 CSV(BOM 있음)와 이 프로그램이 내보낸 CSV(BOM 없음)를 **둘 다** 받습니다. `utf-8-sig` 는 BOM 이 없어도 잘 읽히므로, 관용 범위가 순수하게 넓어지기만 합니다.
- **쓰기 = `utf-8`** → BOM 을 붙이지 않습니다. 그 이유가 `write_transactions` 의 docstring 에 적혀 있습니다.

budget_app/storage/csv_io.py:134-135
```python
    인코딩은 BOM 없는 UTF-8 로 고정한다. BOM 을 넣으면 다시 ``import`` 할 때 헤더
    첫 컬럼명이 ``﻿id`` 로 깨져 왕복이 실패한다(왕복 안전성 우선).
```

여기서 흥미로운 점은, 이 소스가 읽기를 `utf-8-sig` 로 하고 있으니 **자기가 BOM 을 붙여 내보내도 자기는 다시 읽을 수 있다**는 것입니다. 그럼에도 안 붙이는 이유는 상대가 자기 자신만이 아니기 때문입니다. 내보낸 CSV 를 받는 다른 프로그램·스크립트가 BOM 을 처리하지 못하면 거기서 깨집니다. **"관대하게 받고, 엄격하게 내보낸다"** 는 원칙의 교과서적 적용입니다.

이 정책은 JSONL 쪽과 대비하면 더 분명해집니다.

budget_app/storage/config.py:22-26
```python
FILE_ENCODING = "utf-8"
#: 디코딩 불가 바이트를 예외 대신 대리 문자로 받아 **무손실 왕복**시킨다.
#: 읽기와 쓰기가 같은 정책을 쓰므로 손상된 줄이 원문 바이트 그대로 보존된다.
FILE_ERRORS = "surrogateescape"
LINE_TERMINATOR = "\n"
```

JSONL 은 **읽기와 쓰기가 같은 상수**를 씁니다. 내부 포맷이라 양쪽 끝이 모두 이 프로그램이고, 그래서 대칭이 옳습니다. CSV 는 반대쪽 끝이 남이라 비대칭이 옳습니다. **인코딩 정책은 "누가 그 파일의 반대편에 있는가"로 정해집니다.**

**없으면 어떻게 되나** — 읽기를 `utf-8` 로 바꾸면 엑셀에서 편집·저장한 CSV 를 가져올 때마다 `id` 컬럼이 없는 것으로 인식돼 모든 행이 새 id 를 받고 중복 저장됩니다. 쓰기를 `utf-8-sig` 로 바꾸면 이 프로그램이 만든 CSV 를 다른 도구가 읽을 때 첫 컬럼명이 오염됩니다.

---

### `re.compile` 과 모듈 수준 캐시

**어디서 왔나** — `re` 모듈은 정규식 문자열을 매번 파싱하지 않으려고 **처음부터** 내부 캐시를 갖고 있었습니다. `re.match(pattern, s)` 같은 모듈 함수는 전부 `_compile(pattern, flags)` 를 거치고, 그 함수가 캐시를 조회합니다.

**내부에서 무슨 일이 일어나나** — 3.13.1 의 `re._compile` 은 **2단 캐시**입니다.

```python
def _compile(pattern, flags):
    ...
    try:
        return _cache2[type(pattern), pattern, flags]   # 1차: 빠른 dict
    except KeyError:
        pass
    key = (type(pattern), pattern, flags)
    p = _cache.pop(key, None)                           # 2차: LRU
    if p is None:
        ...
        p = _compiler.compile(pattern, flags)
        if len(_cache) >= _MAXCACHE:
            del _cache[next(iter(_cache))]              # 가장 오래된 것 축출
    _cache[key] = p
    ...
    _cache2[key] = p
    return p
```

세 가지를 확인해 둡니다(3.13.1 실측).

- 캐시 키는 문자열이 아니라 **`(type(pattern), pattern, flags)` 세 원소 튜플**입니다. `str` 패턴과 `bytes` 패턴이 섞여도 충돌하지 않게 타입까지 넣습니다.
- 크기 상한은 `_MAXCACHE = 512`, `_MAXCACHE2 = 256` 이고, 넘치면 오래된 항목을 버립니다. **캐시는 무한하지 않으므로 "한 번 컴파일하면 영원히 남는다"는 보장이 아닙니다.**
- `re.compile()` 도 같은 `_compile` 을 거치므로 캐시를 채우고, 같은 패턴을 두 번 `compile` 하면 **같은 객체**가 돌아옵니다.

```
re.purge() 직후 len(re._cache) == 0
re.match(r'^ab$', 'ab') 후    len(re._cache) == 1
캐시 키                       (<class 'str'>, '^ab$', 0)
re.compile(r'zz(\d+)qq') is re.compile(r'zz(\d+)qq')  → True
```

`re.purge()` 는 `_cache`, `_cache2`, `_compile_template` 의 캐시를 전부 비웁니다. 실무에서 쓸 일은 거의 없고, 정규식 컴파일 비용을 측정하거나 메모리를 회수할 때 쓰는 도구입니다.

**그러면 미리 컴파일하는 것이 의미가 있나** — 있습니다. 캐시가 있어도 **호출마다 튜플을 만들고 해시하고 dict 를 조회하는 비용**은 남습니다. 실측(`python -m timeit`, 3.13.1)입니다.

```
p = re.compile(r'^TX-(\d+)$');  p.match('TX-000001')     →  156 ns
re.match(r'^TX-(\d+)$', 'TX-000001')                     →  392 ns
```

2.5배 차이입니다. 절대값은 작지만, 뒤에서 보듯 이 패턴은 정렬의 안쪽 루프에 있습니다.

**이 소스에서** — 세 개의 정규식이 전부 **모듈이 import 되는 순간 한 번** 컴파일됩니다.

budget_app/domain/tx_id.py:44-48
```python
#: 전체가 이 형식이어야 한다 — 검증용
_EXACT = re.compile(config.TX_ID_PATTERN)

#: 줄 어딘가에 있으면 된다 — JSON 이 깨진 줄에서 id 만 건져낼 때
_SCAN = re.compile(config.TX_ID_SCAN_PATTERN)
```

budget_app/domain/validators.py:36-37
```python
#: 금액으로 받아들일 표기 — ``\d`` 가 아니라 ``[0-9]`` 인 것이 중요하다(아래 참조)
_INTEGER = re.compile(r"^[+-]?[0-9]+$")
```

패턴 문자열 자체는 도메인 설정에 있습니다.

budget_app/domain/config.py:24-27
```python
# 거래 ID — 형식·검증·발굴 세 패턴이 값 객체(tx_id.TransactionId)와 짝을 이룬다
TX_ID_PATTERN = r"^TX-(\d+)$"
TX_ID_FORMAT = "TX-{:06d}"
TX_ID_SCAN_PATTERN = r'"id"\s*:\s*"(TX-\d+)"'
```

**`_EXACT` 가 실제로 얼마나 자주 불리는지**를 보면 미리 컴파일한 이유가 분명해집니다.

budget_app/domain/tx_id.py:121-124
```python
    @property
    def number(self) -> int:
        """``TX-000007`` → ``7``."""
        return int(_EXACT.match(self.value).group(1))
```

budget_app/domain/tx_id.py:91-95
```python
    def __lt__(self, other: Any) -> Any:
        """번호 순서로 비교한다. ``total_ordering`` 이 나머지 셋을 채운다."""
        if not isinstance(other, TransactionId):
            return NotImplemented
        return self.number < other.number
```

budget_app/services/transactions.py:85-86
```python
        items = [tx for tx in self.txs.stream() if flt is None or flt.matches(tx)]
        items.sort(key=lambda t: (t.date, t.id), reverse=True)
```

`sort` 가 날짜가 같은 두 거래를 만나면 튜플 비교가 `t.id` 로 내려가고 → `__lt__` → `number` → `_EXACT.match` 입니다. **정렬 비교 한 번에 정규식 매칭이 두 번**이고, n 개를 정렬하면 O(n log n) 번 불립니다. 모듈 함수 `re.match(...)` 를 썼다면 그 자리마다 튜플 해시와 dict 조회가 얹혔을 것입니다.

**없으면 어떻게 되나** — 기능은 똑같이 동작합니다. `re` 의 캐시가 있으니 재컴파일도 일어나지 않습니다. 잃는 것은 두 가지입니다. 첫째는 위의 정렬 경로 성능이고, 둘째가 더 중요한데 — **패턴 문자열이 코드 여기저기에 흩어집니다.** 지금은 `_EXACT`, `_SCAN` 이라는 이름 하나로 "무엇을 검사하는 패턴인가"가 드러나고, 실제 문자열은 `domain/config.py` 한 곳에만 있습니다. ID 형식을 바꿀 때 고칠 자리가 한 줄이라는 것이 이 값 객체의 설계 목표였습니다.

---

### `match` / `search` / `fullmatch` — `_EXACT` 와 `_SCAN` 의 역할 분담

**어디서 왔나** — `match` 와 `search` 는 `re` 모듈 초창기부터 있었습니다. `match` 는 **문자열 시작 위치에 고정**해서 맞춰 보고, `search` 는 **어디서든** 맞는 곳을 찾습니다. 나중에 "처음부터 끝까지 정확히 전부"를 뜻하는 `fullmatch` 가 추가됐는데, 그 전에는 `match` + 패턴 끝의 `$` 나 `\Z` 로 흉내 냈습니다.

**세 함수의 차이를 실측으로** — 패턴 `^TX-(\d+)$` 입니다.

| 입력 | `match` | `fullmatch` | `search` |
|---|---|---|---|
| `'TX-000001'` | ✅ | ✅ | ✅ |
| `'TX-000001\n'` | **✅** | ❌ | **✅** |
| `'TX-000001\n\n'` | ❌ | ❌ | ❌ |
| `'xxTX-1'` | ❌ | ❌ | ❌ |
| `'TX-1yy'` | ❌ | ❌ | ❌ |

굵게 표시한 칸이 **`$` 의 함정**입니다. `$` 는 "문자열의 끝"만이 아니라 "**문자열 끝에 있는 개행 바로 앞**"에도 맞습니다. 그래서 `'TX-000001\n'` 은 `^...$` + `match` 를 통과합니다. 개행이 둘이면 통과하지 못합니다 — `$` 가 봐주는 것은 마지막 개행 하나뿐이기 때문입니다.

"진짜 끝"을 뜻하는 앵커는 `\Z` 이고, 아예 `fullmatch` 를 쓰면 앵커 없이도 같은 효과가 납니다. *(일반론 예시 — 이 소스에는 `\Z` 도 `fullmatch` 도 없습니다.)*

**이 소스에서** — 이 프로젝트는 두 패턴에 **정확히 반대되는 역할**을 맡깁니다.

budget_app/domain/tx_id.py:83-89
```python
    def __post_init__(self) -> None:
        # frozen dataclass 라 object.__setattr__ 로 정규화한다.
        v = str(self.value or "").strip()
        m = _EXACT.match(v)
        if not m:
            raise ValidationError(messages.ERR_TX_ID_INVALID.format(value=v))
        object.__setattr__(self, "value", config.TX_ID_FORMAT.format(int(m.group(1))))
```

budget_app/domain/tx_id.py:109-117
```python
    @classmethod
    def scan(cls, raw_text: str) -> TransactionId | None:
        """줄 원문에서 id 를 발굴한다 — 찾지 못하면 ``None``.

        JSON 파싱조차 실패한 줄에도 id 는 들어 있을 수 있고, 그 번호는 **이미 쓰인
        번호**다. 놓치면 재발급으로 중복 id 가 생긴다.
        """
        m = _SCAN.search(raw_text)
        return cls(m.group(1)) if m else None
```

정리하면 이렇습니다.

| | 패턴 | 함수 | 묻는 것 |
|---|---|---|---|
| `_EXACT` | `^TX-(\d+)$` | `.match()` | "이 문자열 **전체**가 거래 ID 인가" |
| `_SCAN` | `"id"\s*:\s*"(TX-\d+)"` | `.search()` | "이 줄 **어딘가**에 id 필드가 있는가" |

`_EXACT` 는 검증기이므로 앞뒤에 뭐가 붙으면 안 되고, 그래서 `^`/`$` 앵커 + `match` 입니다. `_SCAN` 은 **JSON 파싱이 실패한 줄에서 id 만 건져내는** 것이 목적이므로 앵커가 없어야 하고 `search` 여야 합니다 — 그 줄에는 다른 깨진 내용이 잔뜩 붙어 있기 때문입니다. `_SCAN` 이 앵커 대신 `"id"\s*:\s*"..."` 라는 **문맥**으로 정밀도를 확보하는 점도 보세요. 메모 안의 `TX-000123` 같은 문자열을 id 로 오인하지 않기 위해서입니다.

앞의 `$` 함정을 이 소스가 어떻게 피하는지도 명확합니다. `__post_init__` 이 `_EXACT.match(v)` 전에 **`.strip()`** 을 합니다. 개행이든 공백이든 먼저 떨어져 나가므로 `'TX-000001\n'` 이 통과하는 문제가 애초에 생기지 않습니다. `is_valid` 도 같은 구조입니다.

budget_app/domain/tx_id.py:130-132
```python
def is_valid(value: Any) -> bool:
    """예외 없이 형식만 확인한다 — 분기가 필요한 곳에서 쓴다."""
    return bool(_EXACT.match(str(value or "").strip()))
```

**없으면 어떻게 되나** — `_EXACT` 를 `search` 로 바꾸면 앵커가 있으니 결과는 거의 같지만, `_SCAN` 을 `match` 로 바꾸면 **손상 줄의 id 발굴이 통째로 실패합니다.** 그 결과는 성능 저하가 아니라 데이터 손상입니다. `IdWatermark`/`IdAllocator` 가 이미 쓰인 번호를 모르게 되어 같은 번호를 다시 발급하고, 그 중복 id 는 나중에 백업 복원이나 CSV 가져오기에서 "이미 있는 id" 로 판정돼 거래 한 건이 조용히 사라집니다.

---

### `\d` 는 유니코드 숫자 전체다 — `[0-9]` 를 택한 이유

**어디서 왔나** — 파이썬 2 에서 `str` 패턴의 `\d` 는 ASCII `[0-9]` 였고, 유니코드로 넓히려면 `re.UNICODE` 를 켜야 했습니다. 파이썬 3 은 문자열이 곧 유니코드가 되면서 **기본값이 뒤집혔습니다** — `str` 패턴의 `\d`, `\w`, `\s` 는 기본으로 유니코드 전체를 봅니다. 되돌리는 스위치가 `re.ASCII`(`(?a)`)입니다. `bytes` 패턴은 반대로 언제나 ASCII 입니다.

**실측으로 증명** — 아랍-인도 숫자 `١٢٣`(U+0661~0663, ARABIC-INDIC DIGIT ONE/TWO/THREE)입니다.

```
re.match(r'^[+-]?\d+$',   '١٢٣')  → True    ← \d 가 잡는다
re.match(r'^[+-]?[0-9]+$','١٢٣')  → False   ← [0-9] 는 안 잡는다
re.match(r'^\d+$', '١٢٣', re.ASCII) → False ← re.ASCII 로 되돌리면 안 잡는다
int('١٢٣')                        → 123     ← int() 도 받아 준다!
```

데바나가리 숫자 `०१` 도 마찬가지로 `\d` 에 걸리고 `int()` 가 `1` 로 읽습니다. 반면 위첨자 `²` 는 `\d` 에도 안 걸리고 `int()` 도 `ValueError` 입니다(`'²'.isdigit()` 은 `True` 인데도 그렇습니다 — `\d` 는 `isdigit` 이 아니라 유니코드 카테고리 Nd 를 봅니다).

**왜 위험한가** — `\d` + `int()` 조합이 **둘 다 관대해서 서로를 막아 주지 못합니다.** `'١٢٣'` 을 통과시키면 파일에는 `123` 이 저장되고 화면에는 사용자가 입력한 것과 다른 글자가 뜹니다. 오류 없이 데이터가 바뀌는 부류입니다.

**이 소스에서** — 금액 검증기는 `[0-9]` 를 명시적으로 씁니다.

budget_app/domain/validators.py:36-37
```python
#: 금액으로 받아들일 표기 — ``\d`` 가 아니라 ``[0-9]`` 인 것이 중요하다(아래 참조)
_INTEGER = re.compile(r"^[+-]?[0-9]+$")
```

`re.ASCII` 플래그로도 같은 효과를 낼 수 있었을 텐데 `[0-9]` 를 고른 이유는 **범위 차이** 때문입니다. `re.ASCII` 는 패턴 **전체**의 `\d`, `\w`, `\s`, `\b` 를 한꺼번에 ASCII 로 되돌립니다. 여기서 제한하고 싶은 것은 딱 한 문자 클래스뿐이고, `[0-9]` 는 그 의도를 패턴 안에 국소적으로 적습니다. 플래그를 읽으려면 `re.compile` 의 두 번째 인자까지 봐야 하지만, `[0-9]` 는 패턴만 보면 압니다.

`parse_amount` 의 docstring 이 `int()` 를 검증기로 쓰지 않는 이유를 표로 정리해 두었는데, 그중 두 행이 위에서 실측한 내용입니다(`'1_000'` → `int()` 가 `1000` 으로 읽습니다 — **PEP 515**(숫자 리터럴의 밑줄 구분자)가 들어오면서 문자열을 받는 `int()` 도 같이 관대해졌습니다. 3.13.1 실측: `int('1_000') == 1000`, `int('1_0_0') == 100`. 도입 버전은 로컬에서 확인할 수 없어 적지 않습니다).

budget_app/domain/validators.py:64-70
```python
    text = str(value).strip()
    if not _INTEGER.match(text):
        raise ValidationError(messages.ERR_AMOUNT_NOT_INT)
    n = int(text)
    if n <= 0:
        raise ValidationError(messages.ERR_AMOUNT_NOT_POSITIVE)
    return n
```

**여기서 중요한 대조** — 같은 프로젝트인데 **거래 ID 패턴은 `\d` 를 씁니다**(`TX_ID_PATTERN = r"^TX-(\d+)$"`). 일관성이 없어 보이지만, 실제로 돌려 보면 무해합니다(실측).

```
TransactionId.parse('TX-١٢٣').value  → 'TX-000123'
TransactionId.scan('{"id": "TX-١٢٣"}') → TX-000123
```

`__post_init__` 이 `int(m.group(1))` 로 번호를 뽑고 `TX_ID_FORMAT.format(...)` 으로 **다시 찍기** 때문에, 어떤 표기로 들어왔든 결과는 항상 ASCII 정규형입니다. 즉 **정규화가 관대한 패턴을 무해하게 만듭니다.** 금액에는 그런 재직렬화가 없고(정수는 정수일 뿐 표기가 하나가 아닙니다) 그래서 입구에서 막아야 합니다. "어디에 엄격함을 두는가"가 "그 값이 나중에 정규형으로 다시 찍히는가"로 결정되는 셈입니다.

**없으면 어떻게 되나** — `_INTEGER` 를 `\d` 로 바꾸면 `parse_amount('١٢٣')` 이 `123` 을 반환합니다. 사용자가 붙여넣기 한 값이 조용히 다른 숫자로 저장되고, CSV 로 내보냈다 가져오면 그때는 `123` 으로 나옵니다 — 재현하기 매우 어려운 버그입니다.

---

### `datetime.strptime` — 포맷 문자열을 **정규식으로 바꿔** 매칭한다

**어디서 왔나** — `strptime`(string parse time)은 C 표준 라이브러리의 함수 이름을 그대로 가져온 것입니다. 파이썬은 플랫폼 C 라이브러리의 `strptime` 을 부르지 않고 **순수 파이썬으로 다시 구현**했습니다(`Lib/_strptime.py`). 플랫폼마다 동작이 달라지지 않게 하기 위해서입니다. `time.strptime` 이 먼저 있었고 `datetime.strptime` 은 뒤에 datetime 쪽 진입점으로 붙었는데, 내부에서는 둘 다 같은 `_strptime` 모듈을 씁니다.

**내부에서 무슨 일이 일어나나** — `_strptime.TimeRE` 는 **포맷 지시자 → 정규식 조각**의 매핑을 든 dict 입니다. `%Y-%m-%d` 를 넣으면 문자열 치환으로 하나의 정규식을 조립하고, 그것을 `re.compile` 한 뒤 매칭합니다. 3.13.1 에서 실제로 꺼내 본 결과입니다.

```
TimeRE()['Y']  →  (?P<Y>\d\d\d\d)
TimeRE()['m']  →  (?P<m>1[0-2]|0[1-9]|[1-9])
TimeRE()['d']  →  (?P<d>3[0-1]|[1-2]\d|0[1-9]|[1-9]| [1-9])

TimeRE().pattern('%Y-%m-%d')
  →  (?P<Y>\d\d\d\d)-(?P<m>1[0-2]|0[1-9]|[1-9])-(?P<d>3[0-1]|[1-2]\d|0[1-9]|[1-9]| [1-9])
```

조립된 정규식이 모든 것을 설명합니다.

- **`%m` 은 `0[1-9]` 뿐 아니라 `[1-9]` 도 받습니다.** `%d` 도 마찬가지입니다. 그래서 **한 자리 월·일이 통과합니다.** 이것은 버그가 아니라 명세입니다 — `strptime` 은 사람이 친 다양한 표기를 받아 주는 파서이기 때문입니다.
- `%d` 의 마지막 대안 `| [1-9]` 는 **공백 + 한 자리**입니다. `%e` 스타일(`" 5"`)까지 받아 줍니다.
- 이 조립된 정규식은 매칭만 하고 **월별 일수는 모릅니다.** 그 검사는 뒤에서 `datetime(...)` 생성자가 합니다.

실측으로 확인하면 오류 메시지가 두 종류로 갈립니다.

```
'2024-1-5'    → OK  → strftime 하면 '2024-01-05'
'2024-1-05'   → OK
'2024-01-5'   → OK
'2024-13-01'  → ValueError: time data '2024-13-01' does not match format '%Y-%m-%d'   ← 정규식 단계
'2024-02-30'  → ValueError: day is out of range for month                             ← 생성자 단계
' 2024-01-05' → ValueError: ... does not match format ...   ← 앞 공백은 안 봐줍니다
'24-01-05'    → ValueError  ← %Y 는 \d\d\d\d 라 네 자리 고정
```

그리고 `%Y` 의 정규식이 `\d\d\d\d` — 즉 **`[0-9]` 가 아니라 `\d`** 라는 것이 앞 절과 이어집니다. 유니코드 숫자로 쓴 연도도 통과합니다(실측).

```
datetime.strptime('٢٠٢٤-01-05', '%Y-%m-%d')  →  datetime(2024, 1, 5)
```

`%Y` 뒤에 남는 것은 정규식이 아니라 `int()` 로 변환된 **숫자**이므로, 표기가 무엇이든 결과 객체는 동일합니다.

**이 소스에서** — 이 관대함이 `parse_date` 설계의 직접적 원인입니다.

budget_app/domain/validators.py:94-99
```python
    v = str(value or "").strip()
    try:
        dt = datetime.strptime(v, config.DATE_FORMAT)
    except ValueError as exc:
        raise ValidationError(messages.ERR_DATE_INVALID) from exc
    return dt.strftime(config.DATE_FORMAT)
```

마지막 줄이 전부입니다. **검증만 하고 원문을 돌려주지 않고, `strftime` 으로 되찍어 정규형을 강제합니다.** `strptime` → `datetime` → `strftime` 왕복을 거치면 표기의 자유도가 사라집니다. docstring 이 그 이유를 정확히 짚습니다.

budget_app/domain/validators.py:83-88
```python
    ``strptime`` 은 검증기이지 정규화기가 아니다 — ``"2024-1-5"`` 를 오류 없이
    받아 준다. 검증만 하고 원문을 돌려주면 같은 날이 파일에 두 표기로 공존하고,
    이 프로그램은 날짜를 **문자열로 비교**하므로(ISO 8601 이라 문자열 순서 = 날짜
    순서라는 전제) 그 순간 전제가 깨진다::

        "2024-1-5" <= "2024-01-31"   →   False
```

이 부등식을 직접 실행해 보면 정말 `False` 입니다. `'1'` 의 코드포인트가 `'0'` 보다 크기 때문입니다. 이 프로그램은 날짜를 `date` 객체가 아니라 **`str` 로 저장하고 `str` 로 비교**합니다.

budget_app/domain/specs.py:178-179 근처의 `DateFrom`/`DateTo`, `month_range` 가 만든 `('2024-01-01', '2024-01-31')` 문자열 쌍이 전부 이 전제 위에 서 있습니다. `parse_date` 의 `strftime` 한 줄이 그 전제를 보증하는 유일한 지점입니다.

`parse_month` 도 같은 구조이고, 거기서는 결과가 더 직접적입니다.

budget_app/domain/validators.py:108-113
```python
    v = str(value or "").strip()
    try:
        dt = datetime.strptime(v, config.MONTH_FORMAT)
    except ValueError as exc:
        raise ValidationError(messages.ERR_MONTH_INVALID) from exc
    return dt.strftime(config.MONTH_FORMAT)
```

월 문자열은 예산의 **사실상 키**입니다. `'2024-1'` 이 `strptime('%Y-%m')` 을 통과하므로(실측 확인), 정규화가 없으면 `budget set --month 2024-1` 로 넣은 예산을 `summary --month 2024-01` 이 찾지 못합니다.

**없으면 어떻게 되나** — `strftime` 재직렬화를 빼면 `"2024-1-5"` 로 입력한 거래가 파일에 그대로 저장됩니다. 그 거래는 `list` 에는 보이지만 1월 요약·검색·내보내기에서 **조용히 빠집니다**(`'2024-01-01' <= '2024-1-5' <= '2024-01-31'` 이 성립하지 않으므로). 오류도 경고도 없이 합계가 틀리는, 가계부에서 가장 나쁜 종류의 버그입니다.

---

### `strftime` 의 플랫폼 의존성

**어디서 왔나** — `strptime` 과 달리 `strftime` 은 **플랫폼 C 라이브러리에 위임**되는 부분이 있습니다. 파이썬 문서가 보장하는 것은 C89 표준 지시자 집합(`%Y %m %d %H %M %S %j %U %w %W %y %Z %a %A %b %B %c %p %x %X %%` 등)이고, 그 밖의 것은 플랫폼에 달렸습니다.

**실측** — 같은 코드가 Windows 와 glibc 계열에서 다르게 동작합니다.

```
Windows (CPython 3.13.1) 에서:
  now.strftime('%Y%m%d_%H%M%S')  → '20260812_142946'   ✅
  now.strftime('%-d')            → ValueError: Invalid format string
  now.strftime('%#d')            → '12'                ← MSVC 관례
```

`%-d`(0 패딩 제거)는 glibc 확장이라 Linux·macOS 에서는 동작하지만 Windows 에서는 `ValueError` 입니다. 반대로 `%#d` 는 MSVC 확장이라 Windows 에서만 동작합니다. 즉 **"0 을 떼는 표준 방법은 없습니다."** 필요하면 `str(dt.day)` 처럼 파이썬 쪽에서 만드는 것이 유일한 이식 가능한 방법입니다. *(일반론 예시 — 이 소스에는 `%-d` 도 `%#d` 도 없습니다.)*

**이 소스에서** — 이 프로젝트가 쓰는 지시자는 셋뿐이고 전부 표준 집합 안에 있습니다.

budget_app/domain/config.py:20-22
```python
# 날짜/월 형식
DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"
```

budget_app/storage/config.py:30-31
```python
BACKUP_DIR_PREFIX = "backup_"
BACKUP_TS_FORMAT = "%Y%m%d_%H%M%S"
```

`%Y %m %d %H %M %S` — 어느 플랫폼에서도 같은 결과가 나옵니다. 백업 폴더명에 구분자 없이 붙여 쓴 `%Y%m%d` 가 안전한 것도 이 지시자들이 **항상 고정 폭으로 0 패딩**되기 때문입니다. 만약 `%-m` 같은 것을 썼다면 폭이 달라져 `backup_2026812_...` 처럼 파싱 불가능한 이름이 나왔을 것입니다.

---

### `datetime.now()` — naive 시각과 주입 가능한 `now`

**어디서 왔나** — `datetime` 은 **naive(순진한)** 와 **aware(인식하는)** 두 종류가 있습니다. `tzinfo` 가 `None` 이면 naive 이고, 그 값은 "어느 시간대인지 모르는 벽시계 숫자"일 뿐입니다. `datetime.now()` 는 인자가 없으면 **naive** 를 돌려줍니다(실측: `tzinfo is None`). 시간대를 붙이려면 `datetime.now(timezone.utc)` 처럼 명시해야 합니다.

**무엇이 문제가 되나** — naive 와 aware 를 섞어 비교하면 즉시 터집니다(실측).

```
datetime.now() < datetime.now(timezone.utc)
  → TypeError: can't compare offset-naive and offset-aware datetimes
```

이것이 `datetime` 을 다루는 코드에서 가장 흔한 사고입니다. 예방책은 "**프로그램 전체에서 한 종류만 쓴다**"입니다.

**이 소스에서** — budget_app 은 시각을 **딱 한 군데**에서만 씁니다.

budget_app/storage/backup.py:28-29
```python
    ts = (now or datetime.now()).strftime(config.BACKUP_TS_FORMAT)
    dest = src.parent / f"{config.BACKUP_DIR_PREFIX}{ts}"
```

거래의 `date` 는 **문자열**(`"2024-01-05"`)이고, 예산의 `month` 도 문자열입니다. 즉 이 프로그램에서 `datetime` 객체는 두 가지 용도밖에 없습니다.

1. `validators.parse_date`/`parse_month` 의 **검증·정규화 중간 표현** — `strptime` 으로 만들어 `strftime` 으로 곧바로 버립니다. 파일에 저장되지 않습니다.
2. 백업 폴더명의 **타임스탬프** — 여기서만 `now()` 를 부릅니다.

그래서 naive/aware 문제가 애초에 발생하지 않습니다. `datetime` 객체를 저장하지도, 비교하지도, 산술하지도 않기 때문입니다. **"시각"이 아니라 "날짜 문자열"을 도메인 값으로 잡은 설계가 시간대 문제를 통째로 회피한 것**입니다. 백업 폴더명이 로컬 시각인 것은 의도된 결과입니다 — 그 이름은 사용자가 자기 시계로 읽는 표식이지 정렬 키나 비교 대상이 아닙니다.

**`now` 를 인자로 받는 이유** — 시그니처를 보세요.

budget_app/storage/backup.py:17
```python
def backup_data_dir(data_dir: Path, now: datetime | None = None) -> Path:
```

`datetime.now()` 는 **부를 때마다 다른 값을 돌려주는 함수**입니다. 함수 안에서 직접 부르면 그 함수는 결정적(deterministic)이지 않게 되고, 결과 경로를 단언할 수 없습니다.

```
# now 를 못 넣으면 이런 테스트는 불가능합니다
assert backup_data_dir(d, now=datetime(2024, 1, 5, 12, 0, 0)).name == "backup_20240105_120000"
```

`now or datetime.now()` 라는 관용구가 그 둘을 화해시킵니다 — **호출자가 주면 그것을 쓰고, 안 주면 실제 시각을 쓴다**. 프로덕션 코드는 `backup_data_dir(path)` 로 그냥 부르고, 테스트만 시각을 고정합니다. docstring 이 이것을 명시적으로 적어 둡니다.

budget_app/storage/backup.py:21-23
```python
    디렉터리의 파일을 다루는 일이다. ``now`` 를 주입 가능하게 둔 이유: 이전에는
    ``datetime.now()`` 를 직접 불러서 시간을 고정하지 않으면 결과 경로를 검증할
    수 없었다.
```

주의할 함정이 하나 있습니다. 기본값 자리에 `now: datetime = datetime.now()` 라고 쓰면 **함수 정의 시점(모듈 import 시점)에 한 번 평가되어** 프로그램이 도는 내내 같은 시각이 박힙니다. 그래서 기본값은 `None` 으로 두고 본문에서 `or` 로 채워야 합니다. 이 소스가 정확히 그 형태입니다.

**없으면 어떻게 되나** — `now` 주입이 없으면 백업 테스트가 "폴더가 하나 생겼다" 정도밖에 검사하지 못합니다. `BACKUP_TS_FORMAT` 을 잘못 바꿔 폴더명이 깨져도 테스트가 통과합니다. 그리고 `dest.mkdir(parents=True, exist_ok=False)` 이라 **같은 초에 두 번 백업하면 `FileExistsError`** 가 나는데, 이 동작 역시 시각을 고정할 수 있어야 재현 가능한 테스트가 됩니다.

---

### `calendar.monthrange(y, m)` — 튜플의 두 원소

**어디서 왔나** — `calendar` 는 표준 라이브러리에서 가장 오래된 모듈 중 하나이고, `monthrange` 는 "그 달의 1일이 무슨 요일이고 며칠까지 있는가"를 한 번에 답하는 함수입니다. 윤년 규칙(4로 나뉘고, 100 으로 나뉘면 제외, 400 으로 나뉘면 다시 포함)을 직접 구현하지 않기 위한 표준 도구입니다.

**무엇을 돌려주나** — `(첫날의 요일, 그 달의 일수)` 2-튜플입니다. 3.13.1 실측입니다.

```
calendar.monthrange(2024, 2)  → (calendar.THURSDAY, 29)    ← 윤년
calendar.monthrange(2023, 2)  → (calendar.WEDNESDAY, 28)
calendar.monthrange(2024, 1)  → (calendar.MONDAY, 31)
calendar.monthrange(2024, 13) → IllegalMonthError: bad month number 13; must be 1-12
```

세 가지를 짚어 둡니다.

- **`[0]` 은 요일이고 월요일이 0 입니다.** `calendar.MONDAY == 0`, `calendar.day_name[0] == 'Monday'`. 일요일 기준(0=일)인 언어·라이브러리가 많아 흔히 헷갈리는 지점입니다.
- 3.13.1 에서 그 요일은 `int` 가 아니라 **`calendar.Day` IntEnum** 입니다(`type(...)` → `<enum 'Day'>`, `Day → IntEnum → int`). 로컬 `Lib/calendar.py` 에 `class Day(IntEnum)` 과 `class Month(IntEnum)` 이 실제로 정의돼 있습니다. `IntEnum` 이라 `== 0`, 인덱싱, 산술이 전부 int 처럼 동작하므로 기존 코드는 그대로 돌아가고, 표시할 때만 `calendar.THURSDAY` 로 보입니다. (이것은 **3.13.1 에서 확인한 현재 상태**일 뿐이며, 언제부터 enum 이었는지는 로컬 소스로 확인할 수 없어 적지 않습니다.)
- **`IllegalMonthError` 는 `ValueError` 의 자식**입니다(`IllegalMonthError → ValueError → IndexError → LookupError`). `ValueError` 와 `IndexError` 를 **동시에** 상속하는 드문 예외입니다.

**이 소스에서**

budget_app/domain/periods.py:27-30
```python
    normalized = validators.parse_month(month)
    dt = datetime.strptime(normalized, config.MONTH_FORMAT)
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return f"{normalized}-01", f"{normalized}-{last_day:02d}"
```

**`[1]` 만 쓰는 이유는 이 프로그램이 요일을 전혀 다루지 않기 때문입니다.** 필요한 것은 "말일이 며칠인가" 하나뿐이고, `monthrange` 는 그것을 알려주는 표준 함수 중 가장 직접적인 것입니다. `[0]` 을 버리는 것이 낭비처럼 보일 수 있지만, 두 값을 같은 계산에서 함께 얻기 때문에 별도 비용이 없습니다.

`IllegalMonthError` 가 여기서 절대 나오지 않는다는 점도 중요합니다. 바로 앞 두 줄이 `parse_month` → `strptime` 을 통과했으므로 `dt.month` 는 이미 1~12 임이 보장됩니다. 즉 **검증은 도메인 검증기가 하고, `calendar` 는 계산만 합니다.**

마지막 줄의 `{last_day:02d}` 도 필수입니다. `monthrange` 가 돌려주는 것은 `31` 같은 **int** 인데, 이 프로그램의 날짜는 `'2024-01-31'` 형식의 **문자열**이고 그 문자열 비교가 날짜 비교를 대신합니다. `02d` 로 폭을 맞추지 않으면 `'2024-02-9'` 같은 것이 나와 앞 절의 문자열 순서 전제가 깨집니다. (실제로는 말일이 항상 28~31 이라 두 자리가 보장되지만, 형식 지정자가 그 사실에 의존하지 않게 만듭니다.)

**없으면 어떻게 되나** — "모든 달은 31일"로 가정해 `f"{normalized}-31"` 을 돌려줬다고 해 보겠습니다. 문자열 비교만 놓고 보면 `'2024-02-29' <= '2024-02-31'` 이라 필터 결과는 같을 것 같습니다. 그런데 실제로는 그 경계 문자열이 그대로 `SearchFilter` 로 들어가고, `DateTo.__init__` 이 다시 `parse_date` 로 **검증**합니다.

budget_app/domain/specs.py:188-189
```python
    def __init__(self, value: str) -> None:
        self.value = validators.parse_date(value)
```

실측입니다.

```
DateTo('2024-02-31')
  → strptime 은 정규식을 통과시키고 datetime() 생성자가 거부
  → ValueError: day is out of range for month
  → ValidationError: 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
```

즉 `summary --month 2024-02` 가 **날짜 형식 오류로 죽습니다.** 사용자는 올바른 월을 입력했는데 날짜가 틀렸다는 말을 듣게 되고, 그것도 2·4·6·9·11월에만 그러므로 원인을 찾기 어렵습니다. 앞 절의 `strptime` 이 **정규식 단계와 생성자 단계로 나뉘어 검사한다**는 사실이 여기서 직접 드러납니다 — `2024-02-31` 은 형식은 맞지만 존재하지 않는 날입니다.

모듈 docstring 은 그 전의 상태도 기록해 두었습니다: CLI 는 `calendar.monthrange` 로 말일을 구하고, 서비스는 `date.startswith(month + "-")` 로 판정했습니다. 같은 개념을 **두 계층이 서로 다른 알고리즘으로** 구현한 상태였고, 그러면 한쪽만 고쳐도 둘이 어긋납니다. 지금은 `month_range` 하나만 있고, `SearchFilter.for_month` 가 그것을 불러 요약·검색·내보내기가 **같은 경계**를 쓰게 합니다.

---

### `time.perf_counter` vs `time.time` vs `time.monotonic`

**어디서 왔나** — 오래 전부터 있던 것은 `time.time()` 하나였고, 사람들은 경과 시간도 그것으로 쟀습니다. 문제는 `time.time()` 이 **벽시계(wall clock)** 라는 것입니다. NTP 동기화나 사용자의 시계 변경으로 **뒤로 갈 수 있고**, 그러면 경과 시간이 음수가 나옵니다. **PEP 418** 이 이 문제를 정리해 `time.monotonic()` 과 `time.perf_counter()` 를 표준 라이브러리에 추가했습니다.

**세 함수의 차이** — `time.get_clock_info()` 로 성질을 직접 물어볼 수 있습니다(3.13.1, Windows 실측).

| 함수 | `monotonic` | `adjustable` | `resolution` | 기준점(epoch) |
|---|---|---|---|---|
| `time.time` | **False** | **True** | 1e-07 | 1970-01-01 UTC (고정) |
| `time.monotonic` | True | False | 1e-07 | **정의되지 않음** |
| `time.perf_counter` | True | False | 1e-07 | **정의되지 않음** |

같은 순간에 찍어 보면 값의 성격이 드러납니다.

```
time.time()        = 1786512574.2796643   ← 1970년부터의 초. 사람이 해석 가능
time.perf_counter()= 386401.7956798       ← 기준점 불명. 값 자체는 무의미
time.monotonic()   = 386401.7956839
```

읽는 법은 이렇습니다.

- **`adjustable=True`** = "시스템이 이 시계를 조정할 수 있다". `time.time` 만 해당하고, 이것이 뒤로 갈 수 있다는 뜻입니다.
- **`monotonic=True`** = "절대 뒤로 가지 않는다". 그래서 `end - start` 가 음수가 될 수 없습니다.
- **기준점이 정의되지 않았다**는 것은 `perf_counter()` 값 하나만으로는 아무 의미가 없다는 뜻입니다. **오직 두 값의 차이만** 의미가 있습니다. 그래서 이 두 함수는 "시각"이 아니라 "**구간 측정용 눈금**"입니다.
- `monotonic` 과 `perf_counter` 의 차이는 **의도**입니다. `perf_counter` 는 "사용 가능한 가장 해상도 높은 시계"를 약속하고, `monotonic` 은 "시스템 전체에서 일관되게 단조로운 시계"를 약속합니다. 짧은 구간을 잴 때는 `perf_counter`, 타임아웃·스케줄링처럼 시스템 시계와 함께 가야 할 때는 `monotonic` 이 관례입니다. Windows 3.13.1 에서는 해상도가 같게 나오지만, 이것은 플랫폼 사정이지 보장이 아닙니다.

**이 소스에서**

budget_app/decorators.py:57-64
```python
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(LOG_TOOK, func.__name__, elapsed)
```

세 가지가 정확합니다.

1. **`perf_counter` 선택** — 재는 것은 "함수 하나의 실행 시간"이라는 짧은 구간이고, 절대 시각은 필요 없습니다. 기준점이 없어도 되는 대신 해상도가 가장 높은 시계를 고른 것입니다.
2. **`try`/`finally`** — 예외로 빠져나가는 경로에서도 시간이 찍힙니다. docstring 이 이유를 적어 두었습니다: "느려서 타임아웃이 났다"와 "즉시 터졌다"를 구분하기 위해서입니다. `return func(...)` 이 `try` 안에 있고 측정이 `finally` 에 있으므로, 반환값을 만드는 데 든 시간까지 포함됩니다.
3. **`* 1000`** — `perf_counter` 의 단위는 **초(float)** 입니다. 밀리초로 바꿔 로그 포맷 `LOG_TOOK = "%s took %.2fms"` 에 넣습니다.

budget_app/decorators.py:32
```python
LOG_TOOK = "%s took %.2fms"
```

로그가 `%`-스타일 포맷인 것도 함께 봐 둘 만합니다. `logger.debug(LOG_TOOK, func.__name__, elapsed)` 는 **인자를 그대로 넘기고**, 실제 문자열 조립은 그 로그 레벨이 실제로 출력될 때만 일어납니다. `--debug` 없이 실행하면 DEBUG 는 걸러지므로 포맷팅 비용이 0 입니다. 측정 데코레이터가 측정 대상보다 무거워지지 않게 하는 장치입니다.

**없으면 어떻게 되나** — `time.time()` 으로 바꿔도 대부분의 경우 같은 값이 나옵니다. 그러나 측정 중에 NTP 가 시계를 되돌리면 **음수 밀리초**가 로그에 찍힙니다. 더 현실적으로는 서머타임 전환이나 사용자의 수동 시계 변경이 그 순간에 걸릴 수 있습니다. 성능 로그가 가끔 말이 안 되는 값을 뱉으면 로그 자체를 믿을 수 없게 되고, 그러면 이 데코레이터를 둔 이유가 사라집니다. `perf_counter` 는 그 가능성을 **타입 수준이 아니라 시계 수준에서** 제거합니다.

---

## 2-B. 표준 라이브러리 내부 (2) — logging / argparse / pathlib / 기타

> **이 절은 무엇인가** — 프로그램의 겉면을 만드는 기성품들입니다. 무슨 일이 있었는지 기록을 남기는 도구, 사용자가 쳐 넣은 명령줄을 뜯어 읽는 도구, 파일이 놓인 자리(경로)를 다루는 도구가 중심입니다. 명령줄을 읽는 도구의 항목이 유독 여럿인데, `--data-dir` 같은 선택 하나를 명령의 앞에 적든 뒤에 적든 똑같이 통하게 만들려다 보니 그렇게 됐습니다. 프로그램을 직접 써 보다가 "왜 이 순서로 쳐도 되지?"가 궁금해졌다면 이 절입니다.

이 절은 프로그램의 겉면을 만드는 모듈들입니다 — 로그를 찍는 `logging`, 명령줄을 해석하는 `argparse`, 경로를 다루는 `pathlib`, 그리고 `errno`·`typing`·`os.environ`·`frozenset` 같은 조연들. argparse 항목 여섯 개는 `cli/parser.py` 를 옆에 펴 놓고 읽는 것이 가장 좋습니다. `--data-dir` 하나가 왜 세 층의 파서에 모두 달려 있고 그중 두 층은 `SUPPRESS` 인지가 이 절의 하이라이트입니다.

이 절의 CPython 인용은 로컬 **3.13.1**(`Lib/logging/__init__.py`, `Lib/argparse.py`, `Lib/pathlib/`)에서 직접 읽은 것입니다. 이 프로젝트의 요구 버전은 `>=3.10` 이므로, 버전에 따라 구현 코드의 줄 위치나 파일 배치는 다를 수 있습니다. "3.13 에서 확인한 구현"과 "도입 버전 주장"은 문장에서 구분해 적었습니다.

---

### `logging` 의 객체 모델 — Logger / Handler / Formatter / LogRecord

**어디서 왔나** — `logging` 은 PEP 282 가 제안했고 파이썬 2.3 부터 표준 라이브러리에 있습니다. 그 전에는 각자 `print`/`sys.stderr.write` 로 찍었고, "레벨을 나눈다 / 출력 대상을 나중에 바꾼다"는 개념이 언어 차원에 없었습니다.

**내부에서 무슨 일이 일어나나** — 네 객체의 역할이 완전히 갈립니다.

| 객체 | 하는 일 | 모르는 것 |
|---|---|---|
| `Logger` | "이 사건을 기록할 가치가 있는가" 판정(레벨), 계층 탐색 | 어디로 나가는지, 어떻게 생겼는지 |
| `LogRecord` | 사건 하나를 담은 **데이터**(`msg`, `args`, `levelno`, `name`, `lineno`, `exc_info` …) | 아무것도 |
| `Handler` | 어디로 내보낼지(stderr, 파일, 소켓) | 무슨 내용인지 |
| `Formatter` | `LogRecord` → 문자열 한 줄 | 어디로 나가는지 |

`logger.debug(...)` 한 번의 실제 경로는 `Logger.debug` → (레벨 통과 시) `Logger._log` → `LogRecord` 생성 → `Logger.handle` → `Logger.callHandlers` 입니다. `callHandlers`(3.13 기준 `logging/__init__.py:1720-1744`)는 자기 자신부터 부모를 타고 올라가며 각 로거의 핸들러를 호출합니다.

**이 소스에서** — 이 프로젝트는 로거를 **모듈마다 하나씩** 만들되 이름은 두 종류만 씁니다.

budget_app/config.py:25-25
```python
LOGGER_NAME = "budget_app"
```

budget_app/storage/config.py:11-11
```python
LOGGER_NAME = f"{app_config.LOGGER_NAME}.storage"
```

`cli/config.py:10` 은 앱 이름을 그대로 재수출하므로(`LOGGER_NAME = app_config.LOGGER_NAME`), 실제로 존재하는 로거 이름은 `budget_app` 과 `budget_app.storage` 둘입니다. 그리고 이 소스에는 `Handler` 나 `Formatter` 를 **직접 만드는 코드가 한 줄도 없습니다** — 그 둘은 `output.setup_logging` 이 `basicConfig` 에게 대신 만들게 합니다(아래 항목). 역할 분담을 라이브러리에 맡긴 결과입니다.

**없으면 어떻게 되나** — Logger 와 Handler 가 갈라져 있지 않다면, "손상된 JSONL 줄 경고"를 stderr 로 보낼지 파일로 보낼지를 `storage/jsonl.py` 안에서 정해야 합니다. 지금은 저장소 계층이 `logger.warning(...)` 만 부르고, 출력 대상은 CLI 계층의 `setup_logging` 한 곳이 정합니다. 이 절 전체에서 반복되는 계층 분리가 logging 의 객체 모델 덕에 공짜로 얻어진 자리입니다.

---

### `logging.getLogger(name)` — 매니저 캐시와 점(`.`) 계층

**어디서 왔나** — `logging` 도입과 함께 있던 설계입니다. "로거를 변수에 담아 여기저기 전달한다"가 아니라 "필요한 곳에서 이름으로 다시 꺼낸다"가 이 모듈의 사용법입니다.

**내부에서 무슨 일이 일어나나** — `logging.getLogger(name)` 은 모듈 전역 싱글턴 `Logger.manager`(`Manager` 인스턴스)에게 위임하고, `Manager.getLogger` 는 `self.loggerDict` 라는 **딕셔너리 캐시**를 봅니다(3.13 기준 `logging/__init__.py:1361` 이하). 이름이 이미 있으면 그 객체를 그대로 돌려주고, 없으면 만들어 넣습니다.

```
$ python -c "import logging; print(logging.getLogger('budget_app') is logging.getLogger('budget_app'))"
True
```

이름의 점은 계층을 만듭니다. `Manager` 는 `budget_app.storage` 를 만들 때 `budget_app` 을 부모로 연결하고, 부모가 아직 없으면 `PlaceHolder` 를 넣어 두었다가 나중에 진짜 로거로 교체합니다.

```
$ python -c "
import logging
a = logging.getLogger('budget_app'); b = logging.getLogger('budget_app.storage')
print(b.parent is a, a.parent.name, b.propagate)"
True root True
```

`propagate=True`(기본값)이므로 `callHandlers` 는 `budget_app.storage` → `budget_app` → `root` 순으로 올라가며 핸들러를 찾습니다. 이 소스는 자식 로거에 핸들러를 붙이지 않으므로, **모든 로그는 root 에 붙은 단 하나의 핸들러로 모입니다.**

**이 소스에서** — 로거를 만드는 자리는 다섯 곳이고 전부 모듈 최상단의 상수입니다: `decorators.py:34`, `cli/error_handler.py:17`, `storage/jsonl.py:33`, `storage/ids.py:23`, `storage/unit_of_work.py:62`. 앞의 둘은 `budget_app`, 뒤의 셋은 `budget_app.storage` 입니다.

**없으면 어떻게 되나** — 캐시가 없다면 다섯 모듈이 각자 다른 Logger 객체를 갖게 되고, `setup_logging` 이 root 에 붙인 설정이 그중 일부에만 적용되는 상황을 상상해야 합니다. 점 계층이 없다면 "저장소 로그만 따로 조용히 시키기"(`logging.getLogger("budget_app.storage").setLevel(ERROR)`)가 불가능해집니다 — `storage/config.py:11` 의 주석이 노리는 것이 정확히 그 여지입니다.

---

### 지연 포매팅 — `logger.debug(msg, *args)` 가 문자열을 **언제** 만드나

**어디서 왔나** — `logging` 이 처음부터 `%`-스타일 지연 포매팅을 전제로 설계됐기 때문입니다. `str.format` 은 나중(2.6)에, f-string 은 PEP 498 로 3.6 에 왔지만, `Logger.debug` 의 시그니처는 여전히 `(self, msg, *args, **kwargs)` 입니다.

> **💡 쉽게 말하면** — 아무도 읽지 않을 편지는 아예 쓰지 않는 편이 낫습니다. `logger.debug` 도 문장을 미리 완성해 두지 않고 재료(형식과 값)만 받아 두었다가, 그 등급의 로그를 실제로 내보내기로 정해졌을 때에만 문장을 조립합니다.
> 다만 이 비유는 재료를 구해 오는 일까지 미뤄 주지는 않는다는 점에서 깨집니다 — 인자로 넘길 값을 계산하는 코드는 로그를 끄든 켜든 이미 실행된 뒤입니다.

**내부에서 무슨 일이 일어나나** — 3.13 의 구현이 정확히 이렇습니다.

```python
# Lib/logging/__init__.py:1497-1507
def debug(self, msg, *args, **kwargs):
    if self.isEnabledFor(DEBUG):
        self._log(DEBUG, msg, args, **kwargs)
```

세 단계로 나눠 보면 각 단계에서 무엇이 절약되는지가 보입니다.

1. **`isEnabledFor(level)`** (`:1764-1781`) — `self._cache[level]` 딕셔너리 조회 한 번입니다(캐시 미스일 때만 `getEffectiveLevel()` 로 부모를 거슬러 올라갑니다). 여기서 `False` 면 **함수는 즉시 반환합니다.**
2. **`_log`** (`:1640-1664`) — 통과했을 때만 실행됩니다. `findCaller()` 로 **스택을 거슬러 올라가** 파일명·줄번호·함수명을 얻고, `makeRecord` 로 `LogRecord` 를 만듭니다. `msg` 와 `args` 는 이 시점에도 **따로 보관될 뿐 합쳐지지 않습니다.**
3. **`Formatter.format`** — 핸들러가 실제로 내보낼 때 `record.message = record.getMessage()` 를 부릅니다. 그 `getMessage` 가 결합의 유일한 지점입니다.

```python
# Lib/logging/__init__.py:391-401
def getMessage(self):
    msg = str(self.msg)
    if self.args:
        msg = msg % self.args
    return msg
```

즉 `%` 연산은 **핸들러가 부를 때까지 일어나지 않고**, 레벨에서 걸리면 영원히 일어나지 않습니다. 인자의 `__str__` 조차 호출되지 않는다는 것을 직접 확인할 수 있습니다.

```python
import logging
class Loud:
    def __init__(self): self.n = 0
    def __str__(self):
        self.n += 1
        return "EXPANDED"

loud = Loud()
lg = logging.getLogger("proof")          # 유효 레벨 WARNING
lg.debug("call %s", loud)
print("debug 후 __str__ 호출 횟수 =", loud.n)
lg.warning("warn %s", loud)
print("warning 후 __str__ 호출 횟수 =", loud.n)
```

```
warn EXPANDED
debug 후 __str__ 호출 횟수 = 0
warning 후 __str__ 호출 횟수 = 1
```

**f-string 을 쓰면 이 이득이 통째로 사라집니다.** `logger.debug(f"call {func.__name__}")` 라고 쓰면 f-string 은 **인자를 만드는 시점**, 즉 `debug` 가 호출되기 **전에** 이미 문자열이 됩니다. `isEnabledFor` 는 그다음에 검사되므로, 걸러지는 로그에 대해서도 결합 비용을 전부 지불합니다. 문법적으로는 이것이 핵심입니다 — 지연되는 것은 "포매팅"이지 "인자 평가"가 아닙니다.

**이 소스에서** — `decorators.py` 의 세 상수가 `%`-스타일인 이유가 바로 이것이고, 주석도 그렇게 적혀 있습니다.

budget_app/decorators.py:30-34
```python
LOG_CALL = "call %s"
LOG_DONE = "done %s"
LOG_TOOK = "%s took %.2fms"

logger = logging.getLogger(config.LOGGER_NAME)
```

budget_app/decorators.py:41-45
```python
    def wrapper(*args, **kwargs):
        logger.debug(LOG_CALL, func.__name__)
        result = func(*args, **kwargs)
        logger.debug(LOG_DONE, func.__name__)
        return result
```

기본 실행(`--debug` 없음)에서 유효 레벨은 WARNING 이므로, `@log_call` 이 붙은 함수를 아무리 불러도 이 두 줄은 딕셔너리 조회 두 번으로 끝납니다. `cli/messages.py:16-17` 의 로그 포맷이 `%(levelname)s` 처럼 **`%`-스타일 매핑 문법**인 것도 같은 계열입니다 — `Formatter` 의 기본 스타일이 `%` 이고, `formatMessage` 가 `self._fmt % record.__dict__` 를 수행하기 때문입니다.

**정직하게 짚을 것** — `measure_time` 은 이 이득을 절반만 받습니다.

budget_app/decorators.py:63-64
```python
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(LOG_TOOK, func.__name__, elapsed)
```

`elapsed` 계산은 `logger.debug` 의 **인자**이므로 레벨과 무관하게 항상 수행됩니다. 지연되는 것은 `"%s took %.2fms"` 의 결합뿐입니다. (`perf_counter` 두 번과 곱셈 하나라 실제 비용은 무시할 만합니다.)

**없으면 어떻게 되나** — `%`-스타일을 버리고 f-string 으로 바꾸면 기능은 똑같이 동작합니다. 달라지는 것은 성능이 아니라 **약속**입니다. `@log_call` 은 "로그를 끄면 비용이 사라진다"를 전제로 아무 함수에나 붙일 수 있는 데코레이터인데, f-string 으로 쓰면 로그를 끈 상태에서도 데코레이터를 붙인 만큼 문자열이 만들어집니다.

---

### `logging.basicConfig(..., force=True)`

**어디서 왔나** — `basicConfig` 는 `logging` 도입과 함께 있던 "스크립트용 원샷 설정" 함수입니다. `force` 키워드는 **파이썬 3.8 에 추가**됐습니다(3.13 의 docstring 에도 `.. versionchanged:: 3.8 Added the force parameter.` 로 남아 있습니다).

**내부에서 무슨 일이 일어나나** — `basicConfig` 의 원래 성질은 **"root 로거에 핸들러가 하나라도 있으면 아무것도 하지 않는다"** 입니다. `force` 는 그 앞에 제거 단계를 끼워 넣습니다.

```python
# Lib/logging/__init__.py:2074-2081
force = kwargs.pop('force', False)
...
if force:
    for h in root.handlers[:]:
        root.removeHandler(h)
        h.close()
if len(root.handlers) == 0:
    ...
```

두 가지를 봐야 합니다. 첫째, 제거만 하는 게 아니라 **`h.close()` 로 닫습니다**(파일 핸들러였다면 파일 디스크립터가 반납됩니다). 둘째, `root.handlers[:]` 로 **복사본을 순회**합니다 — 순회 중에 원본 리스트를 줄이면 항목을 건너뛰기 때문입니다.

**이 소스에서** — 설정 지점은 이 한 곳뿐입니다.

budget_app/cli/output.py:93-100
```python
    enabled = bool(debug) or _env_debug()
    logging.basicConfig(
        level=logging.DEBUG if enabled else logging.WARNING,
        format=messages.LOG_FORMAT_DEBUG if enabled else messages.LOG_FORMAT,
        stream=sys.stderr,  # 로그는 결과가 아니므로 stdout 을 오염시키지 않는다.
        force=True,  # 이미 설정돼 있어도(재호출·테스트) 이 설정으로 덮어쓴다.
    )
    return enabled
```

`force=True` 가 필요한 이유는 주석대로 **재호출** 때문입니다. 한 프로세스에서 `main()` 을 여러 번 부르는 상황 — 즉 테스트가 `main(["list"])`, `main(["--debug", "list"])` 를 연달아 부르는 상황 — 에서 `force` 가 없으면 **두 번째 호출이 통째로 무시됩니다.** 첫 호출이 이미 root 에 핸들러를 붙였기 때문입니다. 결과는 "테스트가 `--debug` 를 켰는데 레벨이 WARNING 그대로"가 되고, 더 나쁘게는 테스트 실행 순서에 따라 결과가 달라집니다.

**없으면 어떻게 되나 (basicConfig 자체를 부르지 않으면)** — root 에 핸들러가 하나도 없게 되고, `callHandlers` 는 `found == 0` 일 때 `logging.lastResort` 로 떨어집니다.

```python
# Lib/logging/__init__.py:1741-1744
if (found == 0):
    if lastResort:
        if record.levelno >= lastResort.level:
            lastResort.handle(record)
```

`lastResort` 는 **레벨이 WARNING 인 stderr 핸들러**입니다(3.13 에서 `<_StderrHandler <stderr> (WARNING)>` 로 확인). 실행으로 보이면 이렇습니다.

```
$ python -c "
import logging
lg = logging.getLogger('budget_app')
print('handlers:', lg.handlers, '| effective:', logging.getLevelName(lg.getEffectiveLevel()))
lg.debug('call %s', 'cmd_add')
lg.warning('corrupt %s', 'line 3')"
corrupt line 3
handlers: [] | effective: WARNING
```

`warning` 은 나오지만 `debug` 는 **어디에도 남지 않습니다.** 두 겹으로 막히기 때문입니다 — 로거의 유효 레벨이 WARNING 이라 `isEnabledFor(DEBUG)` 에서 걸리고, 설령 통과했더라도 `lastResort` 의 레벨이 WARNING 이라 또 걸립니다. `output.py:82-85` 의 docstring 이 "이 호출이 없으면 `handle_errors` 의 의도가 성립하지 않는다"고 적은 것이 이 사실을 가리킵니다.

---

### `logger.exception(...)` vs `logger.error(..., exc_info=True)`

**어디서 왔나** — `exception` 은 `logging` 이 처음부터 제공한 **편의 메서드**입니다. 새 기능이 아니라 자주 쓰는 조합에 이름을 붙인 것입니다.

**무엇으로 풀리나** — 3.13 의 구현이 두 줄입니다.

```python
# Lib/logging/__init__.py:1550-1554
def exception(self, msg, *args, exc_info=True, **kwargs):
    """Convenience method for logging an ERROR with exception information."""
    self.error(msg, *args, exc_info=exc_info, **kwargs)
```

세 가지가 따라옵니다. (1) `logger.error(msg, exc_info=True)` 와 **완전히 같은 일**을 합니다. (2) 레벨이 ERROR 로 **고정**입니다 — `logger.exception(...)` 을 WARNING 으로 남길 방법은 없습니다. (3) `exc_info` 는 키워드 인자이므로 `logger.exception(msg, exc_info=False)` 로 트레이스백을 끌 수도 있지만, 그러면 `logger.error(msg)` 와 같아져 이름이 거짓말이 됩니다.

`exc_info=True` 가 실제로 하는 일은 `_log` 안에서 `sys.exc_info()` 를 호출해 `(type, value, traceback)` 삼중항을 `LogRecord.exc_info` 에 싣는 것이고, 문자열로 바꾸는 것은 역시 `Formatter.format` 이 `formatException` 을 부를 때입니다(여기서도 지연됩니다). 그래서 **`except` 블록 안에서 불러야 합니다** — 밖에서 부르면 `sys.exc_info()` 가 잡을 예외가 없습니다.

**이 소스에서** — `handle_errors` 의 마지막 `except Exception` 절, 즉 최후 방어선입니다.

budget_app/cli/error_handler.py:118-119
```python
            logger.exception(messages.LOG_UNHANDLED)
            return config.EXIT_ERROR
```

`LOG_UNHANDLED` 는 `cli/messages.py:18` 의 `"unhandled error"` 한 줄이고, 트레이스백은 메시지가 아니라 `exc_info` 로 붙습니다. `error_handler.py:110-113` 의 주석이 "이전에는 DEBUG 였고 기본 레벨이 WARNING 이라 스택트레이스가 아무 데도 남지 않았다"고 적은 그 자리입니다 — ERROR 로 올린 지금은 `setup_logging(debug=False)` 의 WARNING 레벨도 통과합니다.

**없으면 어떻게 되나** — `logger.error(messages.LOG_UNHANDLED)` 로만 쓰면 로그에 `[ERROR] unhandled error` 한 줄만 남습니다. 분류되지 않은 버그에서 **어느 줄에서 터졌는지가 유일한 단서**인데 그것이 사라집니다.

---

### `argparse.ArgumentParser.parse_args` — `parse_known_args` 위의 얇은 껍질

**어디서 왔나** — `argparse` 는 PEP 389 가 제안했고 파이썬 3.2(및 2.7)부터 표준 라이브러리에 있습니다. 그 전에는 C 의 `getopt(3)` 을 그대로 옮긴 `getopt` 모듈과, argparse 가 대체한 `optparse` 가 있었습니다. `optparse` 에는 **위치 인자와 하위 명령 개념이 없었습니다** — 이 프로젝트의 `budget_app category add --name X` 같은 2단 명령은 argparse 없이는 직접 문자열을 잘라 처리해야 합니다.

**내부에서 무슨 일이 일어나나** — `parse_args` 는 실질적으로 아무 파싱도 하지 않습니다.

```python
# Lib/argparse.py:1888-1896
def parse_args(self, args=None, namespace=None):
    args, argv = self.parse_known_args(args, namespace)
    if argv:
        msg = _('unrecognized arguments: %s') % ' '.join(argv)
        if self.exit_on_error:
            self.error(msg)
        else:
            raise ArgumentError(None, msg)
    return args
```

파싱은 전부 `parse_known_args` 가 하고 **인식하지 못한 인자 목록을 함께 돌려줍니다**. `parse_args` 가 더하는 것은 "남은 게 있으면 에러로 끝낸다"는 정책 한 줄뿐입니다. 두 함수가 나뉜 이유는 래퍼 스크립트(자기 인자만 떼고 나머지를 다른 프로그램에 넘기는 도구) 때문이고, 이 소스는 그런 관용을 원하지 않으므로 `parse_args` 를 씁니다.

`parse_known_args` 는 3.13 에서 `_parse_known_args2` 로 위임하고, 그 앞부분이 **기본값을 namespace 에 심는 단계**입니다. 아래 SUPPRESS 항목에서 다시 인용합니다.

**이 소스에서**

budget_app/cli/app.py:84-90
```python
def main(argv: list[str] | None = None) -> int:
    try:
        args = parser_module.build_parser().parse_args(argv)
        # 로거에 핸들러를 붙이는 유일한 지점. 이 호출이 없으면 handle_errors 가
        # exc_info 로 보존한 스택트레이스가 아무 데도 출력되지 않는다.
        output.setup_logging(getattr(args, "debug", False))
        return _dispatch(args)
```

`parse_args(argv)` 의 `argv` 가 `None` 이면 argparse 가 `sys.argv[1:]` 을 씁니다(`_parse_known_args2` 첫머리). 이 소스가 `main(argv=None)` 으로 주입 가능하게 열어 둔 덕에 테스트가 `main(["list", "--limit", "5"])` 로 부를 수 있습니다.

`getattr(args, "debug", False)` 에 기본값이 붙어 있는 것도 우연이 아닙니다 — 아래 SUPPRESS 때문에 `debug` 속성은 **존재하지 않을 수 있는 속성**입니다.

**없으면 어떻게 되나** — `parse_known_args` 를 직접 쓰면 `budget_app list --limt 5`(오타)가 조용히 통과해 `--limt 5` 가 버려지고 기본 20건이 출력됩니다. 사용자는 자기 옵션이 무시된 것을 알 방법이 없습니다.

---

### `add_subparsers` 와 `_SubParsersAction` — 하위 파서 재귀 호출

**어디서 왔나** — argparse 가 `optparse` 대비 내세운 기능 중 하나입니다. `add_subparsers()` 는 `_SubParsersAction` 이라는 **위치 인자 Action** 하나를 파서에 추가하는 것이고, `sub.add_parser("list")` 는 그 Action 의 `_name_parser_map` 딕셔너리에 이름 → 파서를 등록하는 것입니다.

**내부에서 무슨 일이 일어나나** — 하위 명령 이름을 만나면 argparse 는 `_SubParsersAction.__call__` 을 실행하고, 그 안에서 **하위 파서의 `parse_known_args` 를 다시 부릅니다**.

```python
# Lib/argparse.py:1227-1262 (발췌)
def __call__(self, parser, namespace, values, option_string=None):
    parser_name = values[0]
    arg_strings = values[1:]

    if self.dest is not SUPPRESS:
        setattr(namespace, self.dest, parser_name)
    ...
    # In case this subparser defines new defaults, we parse them
    # in a new namespace object and then update the original
    # namespace for the relevant parts.
    subnamespace, arg_strings = subparser.parse_known_args(arg_strings, None)
    for key, value in vars(subnamespace).items():
        setattr(namespace, key, value)
```

이 여섯 줄이 이 절에서 가장 중요한 코드입니다. 순서를 정확히 보면:

1. 상위 파서가 **먼저** 자기 인자를 파싱해 `namespace` 를 채웁니다(`--data-dir X` 를 여기서 읽습니다).
2. 하위 파서는 **빈 namespace(`None`)** 로 자기 인자를 파싱합니다. 이때 하위 파서의 기본값들이 `subnamespace` 에 채워집니다.
3. `subnamespace` 의 **모든 속성**을 `setattr` 로 상위 `namespace` 에 **덮어씁니다**.

3단계에 조건이 없다는 점이 결정적입니다. "사용자가 실제로 준 값만 옮긴다"가 아니라 **`vars(subnamespace)` 에 있는 것 전부**를 옮깁니다. 하위 파서에 기본값이 있으면 그 기본값이 1단계에서 읽은 진짜 값을 덮어씁니다.

`dest="command"` 를 준 이유도 여기 있습니다 — `self.dest is not SUPPRESS` 일 때만 명령 이름이 namespace 에 남습니다.

**이 소스에서** — 이 프로젝트는 하위 파서가 **2단계**까지 있습니다(`budget category add`). 그래서 위 재귀가 두 번 일어납니다.

budget_app/cli/parser.py:91-92
```python
    parser.set_defaults(needs_storage=True)
    sub = parser.add_subparsers(dest="command", required=True)
```

budget_app/cli/parser.py:161-166
```python
    cat = p.add_subparsers(dest="cat_cmd", required=True)

    p_add = cat.add_parser("add", help="카테고리 추가")
    _add_shared_options(p_add)
    p_add.add_argument("--name", help="카테고리명 (생략 시 대화형)")
    p_add.set_defaults(handler="category.add")
```

`required=True` 는 `add_subparsers(**kwargs)` 가 그대로 `_SubParsersAction` 생성자에 넘기는 `Action.required` 속성이 되고, 위치 인자가 하나도 안 나오면 `_parse_known_args` 의 필수 검사에 걸려 "the following arguments are required: command" 로 끝납니다.

**없으면 어떻게 되나** — `required=True` 가 없으면 `budget_app` 을 인자 없이 실행했을 때 파싱이 **성공**하고, `args.handler` 속성이 없는 채로 `_dispatch` 에 들어가 `AttributeError` 로 죽습니다. `parser.py:17-21` 의 docstring 이 말하는 "도달할 수 없는 코드"(예전의 `else: 알 수 없는 하위 명령` 분기)가 도달 가능해지는 것도 이 옵션을 빼는 순간입니다.

---

### `argparse.SUPPRESS` — "값이 없으면 속성 자체를 만들지 않는다"

**어디서 왔나** — argparse 의 센티널 상수(`SUPPRESS = '==SUPPRESS=='`)로, 도입 때부터 있었습니다. `help=SUPPRESS`(도움말에서 감추기)와 `default=SUPPRESS`(namespace 에서 감추기) 두 용도가 있고 이 소스는 후자를 씁니다.

> **💡 쉽게 말하면** — 신청서의 빈 칸을 대하는 두 태도와 같습니다. 보통은 빈 칸에 "해당 없음"을 적어 넣지만(기본값 채우기), `SUPPRESS` 는 **그 칸 자체를 만들지 않습니다.** 그래야 같은 항목이 적힌 신청서 여러 장을 겹쳐 놓았을 때, 앞장에 이미 적어 둔 값이 뒷장의 "해당 없음"에 덮여 사라지지 않습니다.
> 다만 이 비유는 칸을 만들지 않는 것이 "값을 받지 않는다"는 뜻은 아니라는 점에서 깨집니다 — 사용자가 그 자리에 실제로 값을 적어 주면 뒷장에도 정상적으로 값이 들어가고, 비어 있을 때에만 칸이 생기지 않습니다.

**내부에서 무슨 일이 일어나나** — 기본값을 심는 루프에 `is not SUPPRESS` 조건이 박혀 있습니다.

```python
# Lib/argparse.py:1913-1923
# add any action defaults that aren't present
for action in self._actions:
    if action.dest is not SUPPRESS:
        if not hasattr(namespace, action.dest):
            if action.default is not SUPPRESS:
                setattr(namespace, action.dest, action.default)

# add any parser defaults that aren't present
for dest in self._defaults:
    if not hasattr(namespace, dest):
        setattr(namespace, dest, self._defaults[dest])
```

`default is SUPPRESS` 면 `setattr` 이 **실행되지 않습니다.** 결과적으로 그 dest 는 `subnamespace` 의 `vars()` 에 **키로 존재하지 않고**, 앞 항목의 `for key, value in vars(subnamespace).items()` 루프가 그 이름을 옮길 일도 없습니다. 사용자가 `--data-dir Y` 를 실제로 주면 Action 이 호출돼 값이 들어가므로, 그때는 정상적으로 덮어씁니다.

한 문장으로: **SUPPRESS 는 "덮어쓰지 마라"가 아니라 "값이 없으면 아예 속성을 만들지 마라"이고, `hasattr` 검사와 `vars()` 복사가 그것을 "덮어쓰지 않음"으로 바꿔 줍니다.**

**이 소스에서** — 옵션은 최상위·중간·말단 세 층에 모두 붙어 있고, 실제 기본값은 최상위 한 곳에만 있습니다.

budget_app/cli/parser.py:85-88
```python
    parser.add_argument("--debug", action="store_true", help=DEBUG_HELP)
    parser.add_argument(
        "--data-dir", dest="data_dir", default=config.DEFAULT_DATA_DIR, help=DATA_DIR_HELP
    )
```

budget_app/cli/parser.py:75-76
```python
    p.add_argument("--data-dir", dest="data_dir", default=argparse.SUPPRESS, help=DATA_DIR_HELP)
    p.add_argument("--debug", action="store_true", default=argparse.SUPPRESS, help=DEBUG_HELP)
```

**실행으로 재현** — SUPPRESS 를 뺐을 때 무슨 일이 벌어지는지 최소 예제로 확인할 수 있습니다.

```python
import argparse

def build(mode):
    p = argparse.ArgumentParser(prog="demo")
    p.add_argument("--data-dir", dest="data_dir", default="./data")
    p.add_argument("--debug", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("list")
    if mode == "suppress":
        q.add_argument("--data-dir", dest="data_dir", default=argparse.SUPPRESS)
        q.add_argument("--debug", action="store_true", default=argparse.SUPPRESS)
    else:                                    # 이 소스가 피한 쪽
        q.add_argument("--data-dir", dest="data_dir", default="./data")
        q.add_argument("--debug", action="store_true")
    return p

for mode in ("suppress", "plain"):
    for argv in (["--data-dir", "X", "--debug", "list"], ["list", "--data-dir", "Y"]):
        ns = build(mode).parse_args(argv)
        print(f"{mode:9} {str(argv):42} -> data_dir={ns.data_dir!r} debug={ns.debug}")
```

```
suppress  ['--data-dir', 'X', '--debug', 'list']     -> data_dir='X' debug=True
suppress  ['list', '--data-dir', 'Y']                -> data_dir='Y' debug=False
plain     ['--data-dir', 'X', '--debug', 'list']     -> data_dir='./data' debug=False
plain     ['list', '--data-dir', 'Y']                -> data_dir='Y' debug=False
```

`plain` 의 첫 줄이 버그입니다. 사용자가 분명히 `--data-dir X --debug` 를 줬는데 하위 파서의 기본값이 `./data` 와 `False` 로 되돌려 놓았고, **경고 한 줄 없이** 그렇게 됩니다. `--data-dir` 은 이 프로그램에서 "어느 폴더의 데이터를 읽고 쓸 것인가"이므로, 이 조용한 되돌림은 **엉뚱한 폴더에 거래를 저장하는 결과**로 이어집니다. `parser.py:66-69` 의 docstring 이 "여기에 `default=DEFAULT_DATA_DIR` 를 주면 하위 파서가 앞에서 읽어 둔 값을 기본값으로 되돌려 버린다"고 적은 것이 정확히 이 출력입니다.

**없으면 어떻게 되나** — 대안은 하위 파서에서 옵션을 아예 빼는 것인데, 그러면 `budget_app list --data-dir X`(옵션을 뒤에 쓰는, 더 자연스러운 순서)가 "unrecognized arguments" 로 거절됩니다. 두 순서를 모두 받으면서 값을 잃지 않는 방법이 SUPPRESS 입니다. `app.py:89` 의 `getattr(args, "debug", False)` 도 이 설계의 짝입니다 — 어느 파서도 값을 넣지 않았으면 `args.debug` 속성 자체가 없기 때문입니다.

---

### `set_defaults` — namespace 에 값을 심는 두 번째 통로

**어디서 왔나** — argparse 도입 때부터 있는 메서드입니다. "옵션이 아닌데 namespace 에 들어 있어야 하는 값"을 위한 자리입니다.

**내부에서 무슨 일이 일어나나** — 두 가지를 동시에 합니다.

```python
# Lib/argparse.py:1415-1422
def set_defaults(self, **kwargs):
    self._defaults.update(kwargs)

    # if these defaults match any existing arguments, replace
    # the previous default on the object with the new one
    for action in self._actions:
        if action.dest in kwargs:
            action.default = kwargs[action.dest]
```

(1) `self._defaults` 딕셔너리에 넣습니다 — 앞서 본 두 번째 루프(`for dest in self._defaults`)가 이것을 `hasattr` 검사 후 namespace 에 심습니다. **대응하는 `add_argument` 가 없어도 됩니다.** (2) 같은 dest 의 Action 이 이미 있으면 그 Action 의 `default` 도 바꿉니다.

**이 소스에서** — 세 가지 용도로 씁니다.

budget_app/cli/parser.py:110-111
```python
    _add_shared_options(p)
    p.set_defaults(handler="add")
```

budget_app/cli/parser.py:242-243
```python
    # 백업은 기존 폴더를 읽기만 한다 — 없으면 만들지 말고 오류로 알려야 한다.
    p.set_defaults(handler="backup", needs_storage=False)
```

첫째는 **문자열 키 디스패치**입니다. `handler` 는 `add_argument` 로 선언된 적이 없고 명령줄에서 줄 수도 없는, 순수하게 "이 서브파서가 선택됐다"는 표식입니다. 그것을 `app.py` 의 레지스트리가 함수로 바꿉니다.

budget_app/cli/app.py:28-33
```python
HANDLERS: dict[str, Handler] = {
    "add": handlers.cmd_add,
    "list": handlers.cmd_list,
    "search": handlers.cmd_search,
    "summary": handlers.cmd_summary,
    "budget.set": handlers.cmd_budget_set,
```

budget_app/cli/app.py:78-81
```python
    ctx = AppContext(Path(args.data_dir))
    if args.needs_storage:
        ctx.prepare()
    return HANDLERS[args.handler](ctx, args)
```

둘째는 **최상위에서 켜고 말단에서 끄는 플래그**입니다. `parser.py:91` 이 `needs_storage=True` 를 최상위 `_defaults` 에 넣고, `parser.py:243` 이 `backup` 서브파서에서만 `False` 로 덮습니다. 여기서는 SUPPRESS 와 반대 방향으로 `vars(subnamespace)` 복사를 **이용합니다** — 하위 파서의 `_defaults` 가 상위 값을 덮는 성질이 이 경우에는 정확히 원하는 동작입니다.

셋째는 `parser.py:214` 의 `p.set_defaults(handler="export", include_id=True)` 로, `action="store_false"` 옵션의 기본값을 뒤에서 정하는 용법입니다(다음 항목).

**없으면 어떻게 되나** — `set_defaults` 가 없다면 "어떤 명령이 선택됐는가"를 `args.command` 와 `args.cat_cmd` 두 문자열을 조합해 판정해야 합니다. `parser.py:17-21` 의 docstring 이 회고하는 옛 구조(`if sub == "add" ... elif ...`)가 정확히 그 모습이고, 하위 명령이 늘 때마다 분기가 늘어납니다. 지금은 파서에 한 줄, `HANDLERS` 에 한 줄이면 끝이고 `main` 은 변하지 않습니다.

---

### `type=` 콜러블과 `ArgumentTypeError`

**어디서 왔나** — `optparse` 의 `type=` 은 `"int"`, `"string"` 같은 **문자열 이름**만 받았습니다. argparse 는 그것을 **아무 콜러블**로 열었습니다 — `int`, `float`, `open`, 그리고 직접 만든 함수까지.

**내부에서 무슨 일이 일어나나** — 값 하나를 변환하는 자리는 `_get_value` 한 곳이고, 예외 종류에 따라 메시지가 갈립니다.

```python
# Lib/argparse.py:2533-2556
def _get_value(self, action, arg_string):
    type_func = self._registry_get('type', action.type, action.type)
    if not callable(type_func):
        raise ArgumentError(action, _('%r is not callable') % type_func)
    try:
        result = type_func(arg_string)
    except ArgumentTypeError as err:
        msg = str(err)
        raise ArgumentError(action, msg)          # ← 내 메시지가 그대로 쓰인다
    except (TypeError, ValueError):
        name = getattr(action.type, '__name__', repr(action.type))
        msg = _('invalid %(type)s value: %(value)r')
        raise ArgumentError(action, msg % {'type': name, 'value': arg_string})
    return result
```

차이가 분명합니다. `ArgumentTypeError` 면 **내가 쓴 문장이 그대로** 사용자에게 나가고, `ValueError`/`TypeError` 면 argparse 가 `invalid positive_int value: '0'` 처럼 **함수 이름을 노출한** 기계적 문구로 바꿉니다. 어느 쪽이든 `ArgumentError` 로 감싸여 올라가고, `parse_known_args` 가 그것을 잡아 `self.error(str(err))` → `print_usage(stderr)` → `self.exit(2, ...)` → `sys.exit(2)` 로 끝냅니다.

**이 소스에서**

budget_app/cli/parser.py:49-55
```python
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(messages.ERR_ARG_NOT_INT.format(value=raw)) from exc
    if value < 1:
        raise argparse.ArgumentTypeError(messages.ERR_ARG_NOT_POSITIVE.format(value=raw))
    return value
```

`ERR_ARG_NOT_INT` 와 `ERR_ARG_NOT_POSITIVE` 는 `cli/messages.py:68-69` 의 한국어 문장(`"정수여야 합니다: {value}"`, `"1 이상이어야 합니다: {value}"`)입니다. 실제 출력이 이렇습니다.

```
$ python -m budget_app list --limit 0
usage: budget_app list [-h] [--data-dir DATA_DIR] [--debug] [--limit LIMIT]
budget_app list: error: argument --limit: 1 이상이어야 합니다: 0
$ echo $?
2
```

`positive_int` 는 `parser.py:118`(`--limit`)과 `parser.py:141`(`--top`) 두 곳에 붙어 있습니다.

**없으면 어떻게 되나** — `type=int` 만 쓰면 `--limit 0` 이 **통과**합니다. `parser.py:41-44` 가 기록한 그대로, 0건을 출력하고 프레젠터가 "(데이터 없음)" 을 찍어 사용자는 데이터가 사라진 줄 압니다. 반대로 `positive_int` 안에서 `ValueError` 를 그냥 올리면 argparse 가 문구를 갈아치워 한국어 메시지가 사라집니다. **`ArgumentTypeError` 는 "내 문장을 쓰겠다"는 선언입니다.**

---

### `choices`, `action="store_true"`, `action="store_false"` + `dest`

**어디서 왔나** — 셋 다 argparse 도입 때부터 있는 기능입니다. `store_true`/`store_false` 는 `_StoreConstAction` 의 얇은 하위 클래스이고, `optparse` 에도 `store_true` 는 있었지만 `choices` 검증과 `dest` 재지정의 조합은 argparse 에서 더 정돈됐습니다.

**무엇으로 풀리나**

- **`choices`** — 변환(`_get_value`) **후에** `_check_value` 가 `value not in choices` 를 확인합니다. 즉 `type=` 을 먼저 적용하고 그 결과를 검사하므로, `choices=[1,2,3]` 과 `type=int` 를 함께 쓸 수 있습니다. 실패하면 역시 `ArgumentError` → 종료 코드 2 입니다. 부수 효과로 **도움말과 usage 에 선택지가 자동으로 표시**됩니다.
- **`store_true`/`store_false`** — `_StoreConstAction` 의 `__call__` 은 `setattr(namespace, self.dest, self.const)` 한 줄이고, `nargs=0` 입니다. `store_true` 는 `const=True, default=False`, `store_false` 는 `const=False, default=True` 를 미리 채운 것뿐입니다. **`nargs=0` 이라 값을 받지 않는 스위치**가 됩니다.
- **`dest=`** — 옵션 문자열과 namespace 속성 이름을 분리합니다. 지정하지 않으면 `--no-id` → `no_id` 처럼 앞의 `--` 를 떼고 `-` 를 `_` 로 바꾼 이름이 됩니다.

**이 소스에서** — 셋이 한 자리에서 만나는 곳이 `--no-id` 입니다.

budget_app/cli/parser.py:208-214
```python
    p.add_argument(
        "--no-id",
        dest="include_id",
        action="store_false",
        help="id 컬럼을 빼고 내보낸다 (외부 도구용). 기본은 포함 — 다시 import 할 때 중복을 막는다",
    )
    p.set_defaults(handler="export", include_id=True)
```

읽는 순서는 이렇습니다. 사용자가 보는 이름은 **부정형** `--no-id` 이고, 코드가 보는 이름은 **긍정형** `args.include_id` 입니다. `store_false` 가 그 뒤집기를 담당하고, `set_defaults(include_id=True)` 가 "주지 않았으면 포함"을 정합니다(`store_false` 의 기본 `default=True` 와 같은 값이지만, 명시해 두면 `parser.py:214` 한 줄만 읽어도 기본이 무엇인지 압니다).

budget_app/cli/handlers.py:155-155
```python
    count = ctx.io_service.export_csv(Path(args.out), flt, include_id=args.include_id)
```

핸들러 코드에 `not args.no_id` 같은 **이중 부정이 한 번도 나오지 않는 것**이 이 조합의 목적입니다.

`choices` 는 세 곳입니다 — `parser.py:130` 과 `parser.py:186` 의 `choices=list(domain_config.VALID_TYPES)`, 그리고 `parser.py:229` 의 `choices=list(services_config.ON_DUPLICATE_CHOICES)`. 세 값 모두 **다른 계층이 소유한 상수**에서 옵니다(`domain/config.py:15`, `services/config.py:12`). CLI 는 허용 값 목록을 직접 적지 않고 빌려다 씁니다.

`store_true` 는 `--debug`(`parser.py:76`, `:85`)와 `--atomic`(`parser.py:222-225`)입니다.

**없으면 어떻게 되나** — `choices` 를 빼면 `--type incom`(오타)이 파서를 통과해 도메인의 `parse_type` 까지 내려가서야 걸립니다. 종료 코드가 2(인자 오류) 대신 2(검증 오류)로 — 이 소스는 마침 둘 다 2 입니다만 — 오류를 발견하는 **계층**이 달라지고, 무엇보다 usage 에 선택지가 표시되지 않아 사용자가 무엇을 써야 하는지 알 수 없습니다.

---

### argparse 의 `SystemExit(2)` — 오류 방패를 지나지 않는 경로

**어디서 왔나** — `SystemExit` 은 `sys.exit()` 이 던지는 내장 예외이고, 파이썬 2.5 에서 예외 계층이 정리된 이래 **`Exception` 이 아니라 `BaseException` 을 직접 상속**합니다. 그렇게 만든 이유가 정확히 이 목적입니다 — `except Exception:` 이 프로그램 종료 요청까지 삼키지 않게 하는 것.

```
$ python -c "print(SystemExit.__mro__); print(isinstance(SystemExit(2), Exception))"
(<class 'SystemExit'>, <class 'BaseException'>, <class 'object'>)
False
```

**내부에서 무슨 일이 일어나나** — argparse 의 오류 종료는 두 메서드입니다.

```python
# Lib/argparse.py:2629-2645
def exit(self, status=0, message=None):
    if message:
        self._print_message(message, _sys.stderr)
    _sys.exit(status)

def error(self, message):
    self.print_usage(_sys.stderr)
    args = {'prog': self.prog, 'message': message}
    self.exit(2, _('%(prog)s: error: %(message)s\n') % args)
```

`2` 라는 숫자는 argparse 가 하드코딩한 관례입니다(유닉스에서 "사용법 오류"를 뜻하는 관행). `--help` 는 같은 `exit` 을 `status=0` 으로 부릅니다.

**이 소스에서** — `main` 의 구조를 다시 보면 argparse 오류가 어디로 빠져나가는지 보입니다.

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

`@handle_errors` 는 `_dispatch` 에 붙어 있는데(`app.py:61`), argparse 는 그 **한 줄 위**에서 `SystemExit` 을 던집니다. 그러므로 인자 오류는 `handle_errors` 를 **지나지 않습니다.** 설령 그 자리를 감싸더라도 `except Exception` 은 `SystemExit` 을 잡지 못합니다.

그래서 종료 코드 표를 정직하게 읽으면 두 출처가 섞여 있습니다.

종료 코드 여덟 개는 `cli/config.py:21-29` 에 상수로 모여 있습니다(전문은 §1-A 의
`sys.exit` 항목에 인용했습니다).

| 종료 코드 | 누가 정하나 | 어디를 지나나 |
|---|---|---|
| 2 (인자 문법 오류, `--limit 0`, 알 수 없는 명령) | **argparse** 의 `SystemExit(2)` | `handle_errors` 를 **지나지 않음** |
| 2 (`EXIT_VALIDATION`, 도메인 검증 실패) | `handle_errors` 의 `except ValidationError` | 방패 안 |
| 0/1/3/4/6/130 | `handle_errors` 또는 핸들러 | 방패 안 |

**두 개의 2 가 우연히 같은 값**이라는 점을 아는 것이 중요합니다 — 의도된 정합이지 같은 경로가 아닙니다. 실행으로 확인하면 이렇습니다.

```
$ python -m budget_app list --limit 0 > /dev/null 2>&1; echo $?
2
$ python -m budget_app nosuch > /dev/null 2>&1; echo $?
2
```

**없으면 어떻게 되나** — `SystemExit` 이 `Exception` 의 자식이었다면 `error_handler.py:106` 의 `except Exception as exc:` 가 그것을 잡아 "예기치 못한 오류" 메시지 + 종료 코드 1 로 바꿔 버렸을 것입니다. 즉 `--help` 조차 "예기치 못한 오류"로 끝났을 것입니다. 예외 계층에서 `BaseException` 을 분리해 둔 결정이 이 소스의 오류 정책을 **아무 코드도 쓰지 않고** 지켜 주고 있습니다.

---

### `pathlib.Path` — `__new__` 가 고르는 구체 클래스와 `/` 연산자

**어디서 왔나** — `pathlib` 은 PEP 428 이 제안했고 파이썬 3.4 에 들어왔습니다. 그 전에는 `os.path` 의 함수 모음(`os.path.join`, `os.path.exists`, `os.path.splitext` …)으로 **문자열을 다뤘습니다**. 3.6 의 PEP 519 가 `os.PathLike`/`__fspath__` 프로토콜을 추가하면서 `open()`, `os.replace()` 같은 기존 API 들이 `Path` 객체를 그대로 받게 됐고, 그때부터 pathlib 이 실용적으로 쓸 만해졌습니다.

**내부에서 무슨 일이 일어나나** — `Path(...)` 는 절대 `Path` 인스턴스를 만들지 않습니다. `__new__` 가 플랫폼을 보고 구체 클래스로 갈아탑니다.

```python
# Lib/pathlib/_local.py:505-508 (3.13)
def __new__(cls, *args, **kwargs):
    if cls is Path:
        cls = WindowsPath if os.name == 'nt' else PosixPath
    return object.__new__(cls)
```

`if cls is Path` 조건 덕에 `WindowsPath("x")` 를 직접 부르면 그대로 유지됩니다. (3.13 에서 `pathlib` 은 `__init__.py`/`_abc.py`/`_local.py` 로 나뉜 패키지입니다. 3.10 에서는 단일 `pathlib.py` 이고 `__new__` 본문 마지막 줄이 다르지만, **플랫폼으로 구체 클래스를 고른다**는 기제는 같습니다.)

```
$ python -c "from pathlib import Path; print(type(Path('.')).__name__, Path('data')/'a.jsonl')"
WindowsPath data\a.jsonl
```

`/` 는 연산자 오버로딩입니다 — `PurePath.__truediv__` 가 `self.with_segments(self, key)` 를 돌려주고, `__rtruediv__` 도 있어 `"base" / Path("x")` 도 됩니다. 결합은 `os.path.join` 과 같은 규칙(오른쪽이 절대 경로면 왼쪽을 버립니다)을 따릅니다.

**이 소스에서** — 경계에서 문자열을 받아 즉시 `Path` 로 바꾸고, 안쪽은 전부 `Path` 로 다닙니다.

budget_app/cli/app.py:78-78
```python
    ctx = AppContext(Path(args.data_dir))
```

budget_app/context.py:42-43
```python
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
```

`Path(data_dir)` 를 한 번 더 감싸는 것은 실수가 아니라 **방어**입니다 — `Path` 를 `Path` 에 넣어도 비용이 거의 없고, 문자열이 잘못 들어와도 이 줄에서 정규화됩니다. 같은 패턴이 `storage/jsonl.py:146`, `storage/ids.py:55`, `services/maintenance.py:33` 에도 있습니다.

`/` 연산자는 백업에서 두 번 쓰입니다.

budget_app/storage/backup.py:28-33
```python
    ts = (now or datetime.now()).strftime(config.BACKUP_TS_FORMAT)
    dest = src.parent / f"{config.BACKUP_DIR_PREFIX}{ts}"
    dest.mkdir(parents=True, exist_ok=False)
    for p in _files_to_copy(src):
        (dest / p.name).write_bytes(p.read_bytes())
    return dest
```

**없으면 어떻게 되나** — `os.path` 로 쓰면 `os.path.join(os.path.dirname(str(src)), prefix + ts)` 가 되고, 경로가 여전히 `str` 이라 **문자열 연결로 경로를 만드는 실수**(`data_dir + "/" + name`)를 타입이 막지 못합니다. 그 연결은 Windows 에서 구분자가 섞이거나 `data` 와 `transactions.jsonl` 사이에 구분자가 빠지는 형태로 나타납니다. `Path` 는 `/` 하나로 그 계열의 실수를 없앱니다.

---

### `Path.with_suffix` — 왜 `with_suffix(".tmp")` 가 아닌가

**어디서 왔나** — pathlib 도입 때부터 있는 순수 경로 조작 메서드입니다(디스크를 건드리지 않습니다). `os.path` 시절의 대응물은 `os.path.splitext` 였고, 자르고 다시 붙이는 일을 호출자가 했습니다.

**무엇으로 풀리나** — 구현이 짧고, **"추가"가 아니라 "대체"** 라는 것이 그 세 줄에 다 있습니다.

```python
# Lib/pathlib/_abc.py:222-234 (3.13)
def with_suffix(self, suffix):
    """Return a new path with the file suffix changed.  If the path
    has no suffix, add given suffix.  If the given suffix is an empty
    string, remove the suffix from the path.
    """
    stem = self.stem
    if not stem:
        raise ValueError(f"{self!r} has an empty name")
    elif suffix and not (suffix.startswith('.') and len(suffix) > 1):
        raise ValueError(f"Invalid suffix {suffix!r}")
    else:
        return self.with_name(stem + suffix)
```

`self.stem` 은 **마지막 확장자를 뗀 이름**입니다. 그러므로 `with_suffix` 는 `stem + suffix`, 즉 원래 확장자를 **버립니다.** 확장자를 여러 개 가진 경로에서는 마지막 하나만 바뀝니다(`a.tar.gz` → `a.tar.zip`).

**이 소스에서**

budget_app/storage/jsonl.py:59-60
```python
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + config.TMP_SUFFIX)
```

`config.TMP_SUFFIX` 는 `storage/config.py:27` 의 `".tmp"` 입니다. `path.suffix + ".tmp"` 로 **기존 확장자를 앞에 붙여** 넘기는 이유가 위 구현에 있습니다.

```
$ python -c "
from pathlib import Path
p = Path('data/transactions.jsonl')
print('suffix     :', p.suffix)
print('그냥 .tmp  :', p.with_suffix('.tmp'))
print('이 소스 방식:', p.with_suffix(p.suffix + '.tmp'))"
suffix     : .jsonl
그냥 .tmp  : data\transactions.tmp
이 소스 방식: data\transactions.jsonl.tmp
```

**없으면 어떻게 되나** — `with_suffix(".tmp")` 로 썼다면 `transactions.jsonl` 과 `categories.jsonl` 과 `budgets.jsonl` 의 임시 파일이 각각 `transactions.tmp`, `categories.tmp`, `budgets.tmp` 가 됩니다. 이름은 여전히 안 겹치므로 당장은 동작합니다. 문제는 **`id_counter`** 입니다 — `storage/config.py:21` 의 `ID_COUNTER_FILE_NAME` 은 확장자가 없는 파일이고, 확장자가 없으면 `suffix` 가 `""` 이라 두 방식이 같은 결과(`id_counter.tmp`)를 냅니다만, 확장자를 **보존하는** 쪽이 원본과 임시 파일의 대응을 이름만 보고 알 수 있게 합니다. 더 실질적인 이유는 `backup.py:43` 의 `src.glob("*.jsonl")` 입니다 — 임시 파일이 `transactions.jsonl.tmp` 이면 `*.jsonl` 패턴에 **걸리지 않고**, `transactions.tmp` 여도 걸리지 않지만, 만약 임시 접미사 규칙이 바뀌어 확장자를 앞에 둔 형태(`transactions.tmp.jsonl`)가 됐다면 죽다 만 임시 파일이 백업에 섞여 들어갑니다. 확장자를 **뒤에 덧붙이는** 규칙은 "임시 파일은 절대 데이터 파일로 오인되지 않는다"를 이름 규칙만으로 보장합니다.

---

### `Path` 의 파일시스템 메서드 — `mkdir` / `touch` / `exists` / `stat` / `glob` / `read_text` / `write_bytes` / `unlink`

**어디서 왔나** — 전부 `os` 와 `os.path` 함수의 얇은 메서드 래퍼입니다. pathlib 이 새로 구현한 시스템 호출은 없습니다. `unlink(missing_ok=True)` 의 `missing_ok` 키워드만 pathlib 도입 당시에는 없었고 나중에 붙었습니다(3.13 소스에는 버전 주석이 없어 정확한 릴리스는 여기서 단정하지 않습니다 — 이 프로젝트가 요구하는 3.10 에는 이미 있습니다).

**내부에서 무슨 일이 일어나나** — 3.13 의 구현을 보면 "래퍼"라는 말의 두께를 알 수 있습니다.

- **`stat()`** — `return os.stat(self, follow_symlinks=follow_symlinks)` 한 줄입니다. `Path` 를 `os.stat` 에 그대로 넘길 수 있는 것이 PEP 519 의 `__fspath__` 덕입니다. `st_size` 는 그 결과 구조체의 필드입니다.
- **`exists()`/`is_dir()`/`is_file()`** — 내부적으로 `os.stat` 을 부르되, **아무 `OSError` 나 삼키지 않습니다.** `_ignore_error()` 가 허용하는 errno 화이트리스트(`ENOENT`/`ENOTDIR`/`EBADF`/`ELOOP`)와 `ValueError` 만 잡아 `False` 로 바꾸고, 나머지는 그대로 올려보냅니다. 3.13.1 확인: `pathlib._abc._IGNORED_ERRNOS == (2, 20, 9, 10062)` 이고 `errno.EACCES`(13)는 **그 안에 없습니다.** 즉 "경로가 없다"는 `False` 가 되지만 **권한이 없어 확인조차 못 하는 경우는 `PermissionError` 가 그대로 전파됩니다.** 이 구분이 `storage/ids.py` 가 `exists()` 로 미리 묻지 않고 곧바로 읽으면서 `except OSError` 로 받는 선택을 정당화합니다 — `exists()` 로는 걸러지지 않는 권한 오류까지 그 `try` 가 함께 받아 내기 때문입니다.
- **`mkdir(mode, parents, exist_ok)`** (`_local.py:717-732`) — `os.mkdir` 을 부르고, `FileNotFoundError` 가 나면 `parents` 일 때만 `self.parent.mkdir(parents=True, exist_ok=True)` 로 **재귀**한 뒤 자기를 다시 시도합니다. `exist_ok` 는 `except OSError` 안에서 `if not exist_ok or not self.is_dir(): raise` 로 처리되는데, 주석이 밝히듯 **`EEXIST` 를 직접 검사하지 않습니다** — OS 가 `EACCES`/`EROFS` 를 우선 보고할 수 있기 때문에, 에러 번호 대신 "결과적으로 디렉터리인가"를 봅니다.
- **`touch(mode=0o666, exist_ok=True)`** (`:695-715`) — `exist_ok` 면 먼저 `os.utime(self, None)` 으로 **수정 시각만 갱신**해 보고, 그게 성공하면 끝냅니다(파일이 이미 있는 경우). 실패하면 `os.open(self, O_CREAT|O_WRONLY, mode)` 로 만들고 즉시 닫습니다. `exist_ok=False` 면 `O_EXCL` 이 붙어 이미 있으면 `FileExistsError` 가 납니다.
- **`glob(pattern)`** — 제너레이터입니다. 패턴을 컴파일해 디렉터리를 스캔하며 하나씩 yield 합니다. `**` 는 재귀를 뜻하고 `*` 는 경로 구분자를 넘지 않습니다.
- **`read_text` / `read_bytes` / `write_bytes`** — 각각 "열고, 읽거나 쓰고, 닫는다"를 `with` 로 감싼 편의 메서드입니다. `read_text` 는 `io.text_encoding(encoding)` 을 거치므로, 인코딩을 생략하면 로케일 의존 경고 대상이 됩니다.
- **`unlink(missing_ok=False)`** (`:740-749`) — `os.unlink` 를 부르고 `FileNotFoundError` 를 `missing_ok` 일 때만 삼킵니다. **다른 `OSError` 는 그대로 올라갑니다**(Windows 에서 파일이 열려 있으면 `PermissionError`).

**이 소스에서** — 각 메서드가 정확히 한 가지 이유로 쓰입니다.

budget_app/storage/jsonl.py:150-158
```python
    def ensure_ready(self) -> None:
        """파일이 없으면 만든다 — 명시적으로 호출될 때만 디스크를 건드린다."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    @property
    def is_empty(self) -> bool:
        return not self.path.exists() or self.path.stat().st_size == 0
```

`mkdir(parents=True, exist_ok=True)` 는 "이미 있어도 조용히, 중간 폴더도 알아서" 라는 뜻이고, `is_empty` 가 `exists()` 를 먼저 보는 이유는 `stat()` 이 없는 파일에 대해 `FileNotFoundError` 를 던지기 때문입니다.

budget_app/storage/backup.py:43-47
```python
    yield from src.glob(config.BACKUP_GLOB)
    for name in config.BACKUP_EXTRA_FILES:
        extra = src / name
        if extra.is_file():
            yield extra
```

`glob("*.jsonl")` 이 데이터 파일을, `is_file()` 검사가 확장자 없는 `id_counter` 를 건집니다. `is_file()` 을 쓰는 이유는 같은 이름의 **폴더**를 복사 대상으로 삼지 않기 위해서입니다(`exists()` 였다면 폴더도 통과합니다).

budget_app/storage/ids.py:59-62
```python
        try:
            text = self.path.read_text(encoding=config.FILE_ENCODING).strip()
        except OSError:
            return 0  # 없음 — 첫 실행이거나 이전 버전의 데이터 폴더
```

`exists()` 로 먼저 확인하지 않고 **바로 읽고 `OSError` 를 잡는** 쪽을 골랐습니다. "확인 후 사용"(check-then-use) 사이에 파일이 사라질 수 있는 경합을 피하는 관용구이고, 여기서는 파일 없음뿐 아니라 권한 오류까지 한꺼번에 0 으로 떨어뜨리는 효과도 있습니다 — `ids.py:47-51` 의 "안전장치가 고장 나서 본체가 멈추면 안 된다"는 방침 그대로입니다.

budget_app/storage/backup.py:32-32
```python
        (dest / p.name).write_bytes(p.read_bytes())
```

`read_text`/`write_text` 가 아니라 **바이트**입니다. 백업은 내용을 해석할 이유가 없고, `jsonl.py:167-170` 이 말하는 "UTF-8 이 아닌 바이트가 섞인 손상 줄"까지 **원본 그대로** 옮겨야 하기 때문입니다. 텍스트로 복사하면 디코딩·재인코딩을 거치며 바이트가 달라질 수 있습니다.

budget_app/storage/unit_of_work.py:160-165
```python
        for tmp, _ in self._staged:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:  # 지우지 못해도 원본은 무사하다. 다음 실행이 덮어쓴다.
                logger.debug(messages.LOG_TMP_CLEANUP_FAILED, tmp)
        self._staged.clear()
```

여기서 `missing_ok=True` 와 `except OSError` 가 **다른 일**을 한다는 점이 핵심입니다. `missing_ok` 는 "이미 없는 것"만 봐주고, 권한 문제나 잠금은 여전히 예외로 올라오므로 그것을 따로 잡아 로그로 넘깁니다.

**없으면 어떻게 되나** — `missing_ok=True` 없이 `tmp.unlink()` 만 쓰면, `commit()` 이 일부 성공한 뒤 `rollback()` 이 불릴 때 문제가 됩니다. `commit` 은 성공한 항목을 `self._staged` 에서 빼지만(`unit_of_work.py:150`), 그렇지 않은 구현이거나 다른 경로로 이미 사라진 `.tmp` 가 있으면 `FileNotFoundError` 가 나서 **정리 루프가 남은 임시 파일들을 치우지 못한 채 중단**됩니다. 정리 코드가 정리하다 죽는 것이야말로 피해야 할 실패입니다.

---

### `errno.ENOTDIR` 과 `OSError` 의 3인자 생성자

**어디서 왔나** — `errno` 모듈은 C 의 `<errno.h>` 상수를 그대로 노출하는, 파이썬 초창기부터 있던 모듈입니다. `OSError` 가 인자 개수에 따라 `errno`/`strerror`/`filename` 속성을 채우는 특별 규칙도 오래된 것이고, 파이썬 3.3 에서 `IOError`/`OSError`/`WindowsError` 등이 `OSError` 하나로 통합되면서 `FileNotFoundError`, `NotADirectoryError` 같은 **errno 별 하위 클래스**가 생겼습니다.

**내부에서 무슨 일이 일어나나** — `OSError` 의 `__init__` 은 인자가 2~5개일 때 특별 취급합니다. 3개면 `(errno, strerror, filename)` 으로 해석하고, 각각을 동명의 속성에 넣습니다. 인자가 1개면 그냥 일반 예외처럼 `args` 에만 들어가고 **`errno` 와 `filename` 은 `None` 입니다.**

```python
import errno
try:
    raise NotADirectoryError(errno.ENOTDIR, "not a directory", "./data")
except OSError as e:
    print("errno=", e.errno, "| strerror=", e.strerror, "| filename=", e.filename)
    print("str  =", str(e))

try:
    raise NotADirectoryError("./data")          # 1인자
except OSError as e:
    print("errno=", e.errno, "| filename=", e.filename, "| str=", str(e))
```

```
errno= 20 | strerror= not a directory | filename= ./data
str  = [Errno 20] not a directory: './data'
errno= None | filename= None | str= ./data
```

두 줄의 차이가 전부입니다. 3인자로 던지면 `errno`·`strerror`·`filename` 이 채워지고 `str(exc)` 도 `[Errno 20] not a directory: './data'` 라는 표준 형태가 됩니다. 1인자로 던지면 **예외 클래스가 `NotADirectoryError` 인 것과 무관하게** `errno` 도 `filename` 도 `None` 입니다 — 클래스 이름이 속성을 채워 주지는 않습니다. 핵심은 **3인자 형태만이 `exc.filename` 을 채운다**는 것입니다.

**이 소스에서** — 던지는 쪽과 받는 쪽이 짝을 이룹니다.

budget_app/context.py:79-80
```python
        if self.data_dir.exists() and not self.data_dir.is_dir():
            raise NotADirectoryError(errno.ENOTDIR, "not a directory", str(self.data_dir))
```

budget_app/cli/error_handler.py:85-90
```python
        except NotADirectoryError as exc:
            # 주로 `--data-dir` 에 파일 경로를 준 경우. 아래 mkdir 까지 흘려보내면
            # "파일이 이미 있으므로 만들 수 없습니다" 라는 원인 불명의 메시지가 된다.
            output.err(messages.MSG_ERR_NOT_A_DIR.format(name=exc.filename or exc))
            output.err(messages.HINT_NOT_A_DIR)
            return config.EXIT_IO
```

`exc.filename or exc` 라는 표현이 두 출처를 함께 받는 장치입니다. **직접 던진 예외**는 `filename` 이 채워져 있어 경로만 깔끔하게 나오고, **OS 가 던진 예외**(`open()` 이 낸 `FileNotFoundError` 등)도 `filename` 이 채워져 있습니다. 어느 쪽도 아니면 `or` 의 오른쪽으로 떨어져 예외 자체를 문자열화합니다. 같은 관용구가 `error_handler.py:78`, `:82`, `:92` 에도 있습니다.

`errno.ENOTDIR` 을 **숫자 20 대신 이름으로** 쓰는 이유는 두 가지입니다 — 값이 플랫폼마다 다를 수 있고(이 환경에서는 20), 무엇보다 `20` 이라고 적힌 코드는 읽을 수 없습니다.

**없으면 어떻게 되나** — `raise NotADirectoryError(str(self.data_dir))` 로 1인자만 쓰면 `exc.filename` 이 `None` 이 되어 `exc.filename or exc` 가 오른쪽으로 떨어지고, 사용자에게는 `str(exc)` 가 나갑니다. 이 경우 우연히 경로 문자열이라 결과는 비슷합니다만, `strerror` 와 `errno` 를 잃으므로 `--debug` 로그에 남는 정보와 상위 도구의 판단 근거가 사라집니다. `context.py:75-77` 이 밝히듯 **예외의 종류(`NotADirectoryError`)가 종료 코드 3 을 결정**하고, 그 종류를 지탱하는 것이 errno 계열의 하위 클래스 체계입니다.

---

### `typing.Any` 와 `types.TracebackType`

**어디서 왔나** — `typing` 은 PEP 484(파이썬 3.5)가 도입했습니다. `Any` 는 "모든 타입과 호환된다"는 **특수 형태**로, 타입 검사기에게 "여기는 검사하지 마라"고 말하는 탈출구입니다. `types` 모듈은 훨씬 오래됐고, `TracebackType` 은 트레이스백 객체의 **런타임 타입**입니다 — 직접 만들 수 없고 `sys.exc_info()[2]` 로만 얻는 객체라 이름이 별도로 필요합니다.

**이 소스에서** — `from typing import Any` 를 하는 파일은 **일곱** 개입니다: `decorators.py`, `domain/entities.py`, `domain/queries.py`, `domain/tx_id.py`, `domain/validators.py`, `storage/jsonl.py`, `storage/unit_of_work.py`. 용도는 몇 갈래로 뚜렷하게 갈립니다.

budget_app/storage/jsonl.py:103-107
```python
    lineno: int
    text: str
    data: dict | None = None
    entity: Any | None = None
    error: str | None = None
```

`RawLine` 은 어떤 엔티티인지 **모른 채** 동작하는 공통 층의 자료형이므로(`jsonl.py:1` docstring), `entity` 의 타입은 원리적으로 정할 수 없습니다. `JsonlStore[T]` 는 제네릭이지만 `RawLine` 은 그렇지 않아 `Any` 가 정직한 표기입니다.

budget_app/storage/unit_of_work.py:65-70
```python
def _keep(entity: Any) -> Any:
    """"기존 항목은 그대로" — ``plan_rewrite`` 의 항등 변환.

    가져오기처럼 **추가만 하는** 커밋이 기본이라 이것을 기본값으로 둔다.
    """
    return entity
```

항등 함수는 무엇이 들어와도 그대로 돌려주므로 `Any → Any` 가 정확합니다.

budget_app/decorators.py:37-37
```python
def log_call(func: Callable[..., Any]) -> Callable[..., Any]:
```

데코레이터는 **아무 함수에나** 붙어야 하므로 반환 타입을 좁힐 수 없습니다.

나머지 네 파일은 전부 `domain` 쪽이고, 용도가 하나로 모입니다 — **검증 전의 입력**입니다.

budget_app/domain/validators.py:40-40
```python
def parse_amount(value: Any) -> int:
```

`parse_amount`·`parse_date`·`parse_type` 같은 함수의 인자는 JSONL 한 줄에서 갓 꺼낸 값이라 `str` 일 수도, `int` 일 수도, `None` 일 수도 있습니다. **그것을 판정하는 것이 이 함수의 일**이므로 인자 쪽에 좁은 타입을 적으면 함수의 존재 이유와 모순됩니다. `tx_id.py:105` 의 `parse(cls, value: Any)`, `tx_id.py:130` 의 `is_valid(value: Any)` 도 같은 이유이고, `tx_id.py:91` 의 `__lt__(self, other: Any) -> Any` 는 비교 연산 프로토콜이 `NotImplemented` 를 돌려줄 수 있어 반환도 좁힐 수 없는 경우입니다. `entities.py:144` 의 `dict[str, Any]` 와 `queries.py:75` 의 `**extra: Any` 는 값의 타입이 필드마다 다른 자리입니다.

`TracebackType` 은 컨텍스트 매니저 프로토콜 한 곳입니다.

budget_app/storage/unit_of_work.py:172-181
```python
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
```

세 인자의 타입이 `__exit__` 프로토콜을 그대로 옮긴 것입니다 — `BaseException` 이지 `Exception` 이 아니라는 점이 앞의 `SystemExit` 논의와 이어집니다. `with UnitOfWork()` 블록 안에서 `KeyboardInterrupt` 가 나도 `exc_type is None` 이 거짓이 되어 **롤백이 실행됩니다.**

`from types import TracebackType`(`unit_of_work.py:56`)은 **런타임 import** 입니다. 이 소스는 **애너테이션을 쓰는 모듈에는 모두** `from __future__ import annotations` 를 두어 애너테이션이 런타임에 문자열로 남지만(`unit_of_work.py:51`), import 문 자체는 그대로 실행됩니다. (전체 43개 모듈 중 28개에 이 줄이 있습니다. 없는 15개는 상수만 나열하는 `config`·`messages` 계열과 `__init__.py`·`__main__.py` 로, 애초에 애너테이션이 없어 둘 이유가 없는 파일들입니다.)

**없으면 어떻게 되나** — `Any` 를 쓰지 않으면 `object` 를 쓰게 되는데, 그것은 의미가 다릅니다. `object` 는 "아무 타입이나 받되 **아무 속성도 쓸 수 없다**"이고 `Any` 는 "검사하지 않는다"입니다. `RawLine.entity` 를 `object` 로 선언하면 `raw.entity.to_dict()` 같은 호출을 타입 검사기가 거절합니다. `TracebackType` 없이 `__exit__` 을 애너테이션 없이 두어도 **동작은 같습니다** — 이것은 순전히 문서화이자 검사 도구용 정보입니다.

---

### `functools` 모듈의 성격

**어디서 왔나** — 파이썬 2.5 에 들어온 "고차 함수와 콜러블을 다루는 도구 모음" 모듈입니다. 이름 그대로 **함수를 받아 함수를 돌려주는** 것들(`wraps`, `lru_cache`, `partial`), 그리고 클래스를 받아 메서드를 채워 넣는 것들(`total_ordering`)이 모여 있습니다.

**이 소스에서** — `functools` 에서 쓰는 것은 **`wraps` 와 `total_ordering` 둘뿐**입니다. `wraps` 는 `decorators.py:20`(`import functools`)과 `cli/error_handler.py:10` 에서 데코레이터 세 개에 붙어 있고, `total_ordering` 은 `domain/tx_id.py` 의 `TransactionId` 에 붙어 있습니다. 두 항목의 내부 동작은 각각 **1-C(데코레이터)** 와 **1-B(dataclass·비교 연산)** 에서 다루므로 여기서는 생략합니다.

이 소스는 `functools.partial`, `lru_cache`, `reduce` 를 **쓰지 않습니다.**

---

### `os.environ` 과 환경변수 읽기 (`BUDGET_APP_DEBUG`)

**어디서 왔나** — `os` 모듈이 import 될 때 프로세스의 환경 블록을 읽어 만드는 매핑입니다. 클래스는 `os._Environ` 으로, `MutableMapping` 을 구현하되 값을 넣으면 **C 레벨 `putenv`** 까지 함께 호출해 자식 프로세스에 전달되도록 합니다.

```
$ python -c "import os; print(type(os.environ).__name__)"
_Environ
```

중요한 성질 둘. (1) `os.environ` 은 **import 시점의 스냅숏**입니다 — 다른 방법(C 확장 등)으로 환경이 바뀌어도 반영되지 않습니다. (2) Windows 에서는 키가 **대소문자를 구분하지 않습니다**(`_Environ` 이 키를 대문자로 정규화합니다). 값은 어느 플랫폼에서든 항상 `str` 입니다 — 숫자도 불리언도 없습니다.

**이 소스에서**

budget_app/cli/config.py:18-19
```python
DEBUG_ENV_VAR = "BUDGET_APP_DEBUG"
FALSY_ENV_VALUES = frozenset({"", "0", "false", "no", "off"})
```

budget_app/cli/output.py:74-76
```python
def _env_debug() -> bool:
    value = os.environ.get(config.DEBUG_ENV_VAR, "").strip().lower()
    return value not in config.FALSY_ENV_VALUES
```

세 단계가 각각 하나씩 일을 합니다. `.get(name, "")` 은 **미설정과 빈 문자열을 같게** 만들고(`KeyError` 를 피하는 것이 아니라 두 경우를 합치는 것이 목적입니다), `.strip()` 은 셸에서 실수로 붙은 공백을, `.lower()` 는 `False`/`FALSE`/`false` 의 차이를 없앱니다. 그리고 **판정 방향이 뒤집혀 있습니다** — "참인 값 목록에 있으면 켠다"가 아니라 "**거짓인 값 목록에 없으면 켠다**"입니다.

```
$ BUDGET_APP_DEBUG=1 python -c "from budget_app.cli import output; print(output._env_debug())"
True
$ BUDGET_APP_DEBUG=0 python -c "from budget_app.cli import output; print(output._env_debug())"
False
$ python -c "from budget_app.cli import output; print(output._env_debug())"
False
```

`BUDGET_APP_DEBUG=yes`, `=on`, `=true`, `=아무거나` 가 모두 참이 됩니다. 디버그 스위치에는 이쪽이 맞습니다 — 사용자가 뭔가 값을 넣었다는 것 자체가 "켜고 싶다"는 뜻이고, `BUDGET_APP_DEBUG=y` 를 조용히 무시하는 것보다 낫습니다.

이 값이 쓰이는 곳은 `output.py:93` 한 줄입니다: `enabled = bool(debug) or _env_debug()`. `--debug` **또는** 환경변수, 즉 둘 중 하나면 켜집니다.

**없으면 어떻게 되나** — 환경변수 경로가 없다면 `--debug` 를 붙일 수 없는 상황에서 디버그 로그를 켤 방법이 사라집니다. 그런 상황이 실제로 있습니다 — CI 스크립트가 명령줄을 고정으로 조립하는 경우, 또는 `handle_errors` 가 잡아 버려 재현이 어려운 오류를 사용자에게 "환경변수 하나만 세팅하고 다시 실행해 달라"고 부탁하는 경우입니다.

---

### `frozenset` 을 상수로 쓰는 이유

**어디서 왔나** — 집합을 언어에 들이자고 제안한 것은 PEP 218 입니다. 제안이 곧 내장형은 아니었습니다 — 먼저 **순수 파이썬 `sets` 모듈**로 시험되었고, 내장형 `set`/`frozenset` 은 그다음 파이썬 2 계열 릴리스에서 왔습니다(둘의 시점이 다릅니다). 지금은 `sets` 모듈이 사라지고 내장형만 남았습니다.

```
$ python -c "import sets"
ModuleNotFoundError: No module named 'sets'
```

`set` 은 가변, `frozenset` 은 불변이고, **불변이라 해시 가능**하다는 것이 둘의 실질적 차이입니다.

**무엇으로 풀리나** — `in` 연산은 두 자료형 모두 해시 테이블 조회라 원소 수와 무관하게 평균 O(1) 입니다(리스트·튜플의 `in` 은 O(n) 선형 탐색입니다). 그러나 이 소스가 `frozenset` 을 고른 이유는 성능이 아닙니다. 원소가 다섯 개뿐이라 차이가 없습니다.

이유는 **모듈 전역 상수의 불변성**입니다. `FALSY_ENV_VALUES = {"", "0", ...}` 처럼 `set` 으로 두면, 어느 모듈이든 `config.FALSY_ENV_VALUES.add("maybe")` 를 할 수 있고 그 변경은 프로세스 전체에 남습니다. `frozenset` 은 `add`/`remove` 메서드 자체가 없어 그 실수가 **`AttributeError` 로 즉시 드러납니다.** 대문자 이름이 "고치지 마세요"라는 약속인 반면, `frozenset` 은 그것을 타입으로 **강제**합니다.

**이 소스에서** — `frozenset` 은 정확히 한 곳에서만 쓰입니다.

budget_app/cli/config.py:19-19
```python
FALSY_ENV_VALUES = frozenset({"", "0", "false", "no", "off"})
```

`frozenset({...})` 는 집합 리터럴을 만든 다음 얼리는 것이라 표기가 두 겹입니다(집합에는 리터럴 형태의 frozenset 문법이 없습니다).

정직하게 짚어 두면, 이 소스의 다른 "값 목록" 상수들은 **`frozenset` 이 아니라 튜플**입니다.

budget_app/domain/config.py:15-15
```python
VALID_TYPES = (TYPE_INCOME, TYPE_EXPENSE)
```

budget_app/services/config.py:12-12
```python
ON_DUPLICATE_CHOICES = (ON_DUPLICATE_SKIP, ON_DUPLICATE_NEW_ID, ON_DUPLICATE_ERROR)
```

이 둘이 튜플인 이유는 **순서가 의미를 갖기 때문**입니다. `parser.py:130` 과 `:229` 가 `choices=list(...)` 로 argparse 에 넘기고, argparse 는 그 순서대로 usage 와 도움말에 선택지를 표시합니다. `frozenset` 이었다면 도움말에 나오는 순서가 실행마다 달라질 수 있는 — 최소한 소스를 읽어 예측할 수 없는 — 상태가 됩니다. **불변성이 목표면 `frozenset`, 불변성과 순서가 함께 필요하면 튜플**이라는 구분이 이 소스에 일관되게 적용돼 있습니다.

**없으면 어떻게 되나** — `FALSY_ENV_VALUES` 를 리스트로 두어도 `_env_debug` 는 똑같이 동작합니다. 달라지는 것은 실수의 발견 시점뿐입니다 — 리스트라면 누군가 `.append()` 한 뒤 "환경변수를 설정했는데 디버그가 안 켜진다"는 증상을 원인 모듈이 아닌 곳에서 디버깅하게 됩니다.

---

## 3. 운영체제 계층 — 파일 원자성, 스트림, 파이프, 인코딩

> **이 절은 무엇인가** — 파이썬보다 한 층 아래, 컴퓨터를 돌리는 운영체제가 하는 일입니다. 이 프로그램은 사용자에게 세 가지를 약속합니다 — 저장하는 중에 멈춰도 파일이 반쯤 망가진 채 남지는 않는다, 읽을 수 없게 깨진 줄도 지우지 않고 원래 모습대로 둔다, 출력을 받아 가던 상대가 먼저 끊어도 요란한 오류 없이 조용히 끝난다. 그 세 약속이 실제로 무엇에 기대고 있는지, 그리고 **무엇까지는 약속하지 못하는지**를 같은 무게로 적었습니다. 문법을 몰라도 따라 읽히는 편이라, 이 문서에서 비전공자에게 가장 권할 만한 절입니다.

마지막 절은 파이썬 아래층입니다. 이 프로그램이 내세우는 내구성 약속 — 원자적 교체, 손상 줄 원문 보존, 파이프가 끊겨도 조용한 종료 — 은 파이썬 문법이 아니라 전부 운영체제 호출에 기대고 있습니다. 그래서 이 절은 그 호출들이 무엇을 보장하는지와 **무엇을 보장하지 않는지**를 같은 무게로 적었습니다. 로컬이 Windows 라 재현할 수 없었던 유닉스 동작은 그렇다고 명시했습니다.

budget_app 이 내세우는 내구성 약속은 셋입니다. **원자적 교체**(중간 상태가 보이지 않는다), **손상 줄 원문 보존**(깨진 바이트도 잃지 않는다), **파이프가 끊겨도 조용히 끝난다**. 이 셋은 파이썬 문법이 아니라 전부 운영체제 호출에 기대고 있습니다. 이 절은 그 호출들이 실제로 무엇을 하는지, 그리고 **무엇을 하지 않는지**를 봅니다.

> 아래에서 "3.13 확인"이라고 적은 것은 이 문서를 쓰면서 로컬 CPython 3.13.1(Windows 11)에서 직접 실행해 확인한 결과입니다. 로컬에서 근거를 댈 수 없는 "이 기능은 파이썬 N.N 에 추가됐다" 류의 도입 버전 숫자는 **의도적으로 적지 않았습니다** — 설계 출처(PEP 번호)만 남겼습니다. 또 로컬이 Windows 라 재현할 수 없는 유닉스 동작은 그렇다고 명시했습니다.

---

### `open()` — 파이썬이 실제로 만드는 3층 구조

**어디서 왔나** — 파이썬 3 의 `open()` 은 `io` 모듈의 `io.open` 이 그대로 내장 함수가 된 것입니다. 이 I/O 스택 자체는 PEP 3116(New I/O)이 설계했고 파이썬 3 에서 표준이 됐습니다(로컬 `Lib/io.py` 첫머리에 `# New I/O library conforming to PEP 3116.` 이라고 그대로 적혀 있습니다). 파이썬 2 의 `file` 객체는 C 의 `FILE*` 을 얇게 감싼 한 겹이었고, 바이트와 문자열의 구분도, 버퍼 층의 분리도 없었습니다.

**내부에서 무슨 일이 일어나나** — `open()` 은 하나의 객체를 주는 것처럼 보이지만 실제로는 **세 개의 객체를 겹쳐 쌓아** 맨 위 것만 돌려줍니다.

```
f = open(path, "w", encoding="utf-8")

  f                    TextIOWrapper   ← 문자열 ↔ 바이트 (인코딩, 줄바꿈 변환)
  f.buffer             BufferedWriter  ← 바이트 버퍼 (기본 8192바이트)
  f.buffer.raw         FileIO          ← 운영체제 파일 디스크립터 (fd)
  f.fileno()           3               ← 실제 fd 번호
```

3.13 에서 확인한 그대로입니다.

```
text  : <class '_io.TextIOWrapper'>
buffer: <class '_io.BufferedWriter'>
raw   : <class '_io.FileIO'>
fileno: 3 raw.fileno: 3
io.DEFAULT_BUFFER_SIZE = 8192
```

읽기로 열면 가운데 층만 `BufferedReader` 로 바뀝니다. `open(path, "rb")` 처럼 바이너리로 열면 **맨 위 층이 없어져** `BufferedReader` 가 곧 `f` 입니다 — 그래서 바이너리 모드에서는 `f.read(1)` 이 `bytes` 를 주고 인코딩 인자를 받지 않습니다.

이 3층이 중요한 이유는 `f.write(...)` 가 **맨 위 층까지밖에 도달하지 않기** 때문입니다.

```python
with open("buf.txt", "w", encoding="utf-8", newline="\n") as f:
    f.write("hello\n")
    print(os.stat("buf.txt").st_size)   # 0   ← 아직 파이썬 안에 있다
    f.flush()
    print(os.stat("buf.txt").st_size)   # 6   ← 이제 OS 가 안다
```

버퍼가 차면 파이썬이 알아서 내려보냅니다. 4000자를 쓴 시점의 파일 크기는 여전히 0 이었고, 10000자를 더 써 8192바이트를 넘긴 순간 14000바이트가 한꺼번에 나타났습니다(3.13 확인).

**이 소스에서** — `stage_lines` 가 이 세 층을 순서대로 밀어내립니다.

budget_app/storage/jsonl.py:59-72
```python
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

`f.write` 는 파이썬 버퍼까지, `f.flush()` 는 OS 까지, `os.fsync(f.fileno())` 는 디스크까지 — **한 줄씩 정확히 한 층을 내려갑니다.** `f.fileno()` 가 필요한 이유도 여기서 드러납니다. `os.fsync` 는 파이썬 객체를 모르고 fd 번호만 받으므로, 3층 구조를 뚫고 맨 아래 `FileIO` 의 fd 를 꺼내 넘겨야 합니다.

**없으면 어떻게 되나** — `with` 블록을 나가면 `close()` 가 자동으로 `flush` 를 하므로 평상시에는 `f.flush()` 없이도 파일 내용은 맞습니다. 문제는 그다음 줄인 `os.fsync` 입니다. `flush` 없이 `fsync` 를 부르면 **아직 파이썬 버퍼 안에 있는 데이터는 fsync 대상이 아닙니다.** OS 가 모르는 바이트를 OS 에게 "디스크에 내려라"고 시킬 수는 없으니까요. 즉 `flush` 를 빼면 `fsync` 는 조용히 빈 파일을 동기화하고 성공을 돌려줍니다 — 방어가 있는 것처럼 보이는데 없는 상태입니다.

### `f.flush()` 와 `os.fsync()` — 왜 flush 만으로는 부족한가

**무엇이 다른가** — `flush()` 는 파이썬 버퍼를 비워 `write(2)` 시스템 콜을 부릅니다. 여기까지 오면 **커널의 페이지 캐시**에 데이터가 있습니다. 같은 프로그램이 다시 읽어도, 다른 프로세스가 읽어도, 프로그램이 죽어도 내용은 보입니다 — 커널이 살아 있으니까요. `os.fsync(fd)` 는 그 페이지 캐시를 **물리 저장 장치까지** 내려보내라고 커널에게 요구하고, 장치가 완료를 알릴 때까지 돌아오지 않습니다.

> **💡 쉽게 말하면** — 편지를 부치는 세 단계와 같습니다. 편지를 다 썼다(`write`), 봉투에 넣어 현관에 내놓았다(`flush`), 우체통에 실제로 넣었다(`os.fsync`). 책상 위 편지는 나 혼자 넘어져도 흩어지지만 현관에 둔 것은 남고, 동네가 통째로 정전되면 현관에 둔 편지까지 위태로워집니다.
> 다만 이 비유는 우체통에 넣은 것이 **편지지의 내용뿐**이라는 점에서 깨집니다 — 봉투에 적은 주소, 즉 그 내용이 어느 파일 이름에 걸려 있는가는 부모 폴더를 한 번 더 내려보내야 같은 수준으로 안전해지고, 이 소스는 거기까지 하지 않습니다(다음 항목).

전원 차단 시나리오로 세 단계를 나눠 보면 이렇습니다.

| 어디까지 갔나 | 프로세스가 죽으면 | 커널이 죽거나 전원이 끊기면 |
|---|---|---|
| `f.write` 만 (파이썬 버퍼) | **잃는다** | 잃는다 |
| `f.flush()` 까지 (페이지 캐시) | 살아남는다 | **잃을 수 있다** |
| `os.fsync()` 까지 (디스크) | 살아남는다 | 살아남는다 |

**이 소스에서** — 원자적 쓰기 경로(`stage_lines`, jsonl.py:70-71)와 이어 쓰기 경로(`_append_lines`, jsonl.py:246-247)가 **둘 다** `flush` + `fsync` 를 합니다. 후자의 docstring 이 그 이유를 "내구성 비대칭"이라고 부릅니다 — 같은 프로그램의 두 쓰기 경로가 서로 다른 내구성을 약속할 이유가 없다는 것입니다.

**없으면 어떻게 되나** — `stage_lines` 의 docstring 이 정확히 적어 두었습니다. `os.replace` 가 보장하는 것은 "이름이 가리키는 대상이 순간적으로 바뀐다"이지 "내용이 디스크에 도달했다"가 아닙니다. fsync 없이 전원이 끊기면 **새 이름이 내용 없는(또는 절반만 찬) 파일을 가리킬 수** 있습니다. 원자성은 지켜졌는데 데이터는 사라진, 최악의 조합입니다.

> fsync 는 공짜가 아닙니다(디스크 왕복을 기다립니다). 이 소스가 부담 없이 쓰는 것은 CLI 라서 명령 하나에 파일을 한두 번만 쓰고 끝나기 때문입니다 — `_append_lines` 의 docstring 이 그 판단을 밝혀 두었습니다.

### `os.replace` — 이름 교체의 원자성이 보장하는 것과 아닌 것

**어디서 왔나** — `os.replace` 는 `os.rename` 보다 **나중에 추가된** 함수입니다. 그전에는 `os.rename` 밖에 없었고, 뒤에서 볼 이유로 그것은 플랫폼마다 다르게 동작했습니다.

> **💡 쉽게 말하면** — 벽에 붙은 안내문을 고치는 일과 같습니다. 붙어 있는 종이 위에 그대로 덧쓰면 지나가던 사람이 지우다 만 상태를 보게 됩니다. 새 종이에 전부 다시 쓴 뒤 압정을 뽑아 한 번에 갈아 끼우면, 보는 사람은 옛것 아니면 새것만 봅니다. `os.replace` 가 하는 일이 그 마지막 동작입니다.
> 다만 이 비유는 **같은 벽에서만** 통한다는 점에서 깨집니다 — 새 종이를 다른 방 벽에 써 두었다면 갈아 끼우기가 아니라 옮기기가 되고(다른 파일시스템), 그 순간 이 보장은 사라집니다. 그리고 **Windows 에서는 같은 벽에서도 완전하지 않습니다** — 누군가 그 안내문을 보고 있는 중(다른 프로그램이 그 파일을 열어 둔 중)이면 갈아 끼우기 자체가 거부됩니다(아래 비보장 3번).

**내부에서 무슨 일이 일어나나** — POSIX 에서는 `rename(2)` 시스템 콜입니다. POSIX 는 이 호출이 **다른 프로세스에 대해 원자적**이라고 규정합니다. 즉 새 이름을 열려는 다른 프로세스는 **옛 파일 아니면 새 파일**을 보고, 그 사이의 "없음"이나 "절반"은 결코 보지 못합니다. 실제로 일어나는 일은 디렉터리 엔트리 하나가 다른 inode 를 가리키게 바뀌는 것뿐이라 파일 크기와 무관하게 빠릅니다.

여기서 **보장되지 않는 것 세 가지**를 분명히 해야 합니다.

1. **같은 파일시스템 안에서만** 됩니다. 다른 파일시스템으로 옮기면 `EXDEV` 오류입니다. 이 소스가 임시 파일을 `path.with_suffix(path.suffix + ".tmp")` 로 **대상과 같은 폴더에** 만드는 이유가 이것입니다. `/tmp` 에 만들었다면 다른 마운트일 수 있고, 그러면 `os.replace` 자체가 실패합니다.
2. **디렉터리 엔트리의 내구성은 별개**입니다. rename 자체는 원자적이지만 "그 rename 이 디스크에 기록됐는가"는 부모 디렉터리를 따로 fsync 해야 보장됩니다. 이 소스는 그것을 하지 않습니다. POSIX 에서는 `fd = os.open(dir_path, os.O_RDONLY)` 로 디렉터리 fd 를 얻어 `os.fsync(fd)` 를 부르는 것이 그 방어입니다. **Windows 에서는 그 방어를 시도조차 할 수 없습니다** — 3.13 확인: `os.fsync` 가 거부되는 것이 아니라 그 앞 단계인 `os.open('.', os.O_RDONLY)` **자체가** 실패해 디렉터리 fd 를 아예 손에 넣지 못합니다.

```
os.open fail: PermissionError [Errno 13] Permission denied: '.'
```
3. **Windows 에서는 POSIX 와 같은 문서상의 원자성 보장이 없습니다.** POSIX `rename(2)` 처럼 "다른 프로세스에 대해 원자적"이라고 규정한 문구가 없고, 결정적으로 **대상 파일이 다른 프로세스에 열려 있으면 그냥 실패합니다.**

3.13(Windows)에서 대상 파일을 연 채로 시도한 결과입니다.

```
replace while target open -> PermissionError errno 13 winerror 5 액세스가 거부되었습니다
```

**이 소스에서** — 교체는 한 곳에만 있습니다.

budget_app/storage/jsonl.py:75-77
```python
def commit_staged(tmp: Path, target: Path) -> None:
    """준비된 임시 파일을 대상 이름으로 교체한다 — 같은 파일시스템에서 원자적."""
    os.replace(tmp, target)
```

그리고 위 `PermissionError` 가 "흔한 실패"라는 사실이 `UnitOfWork.commit` 의 설계 전체를 결정합니다.

budget_app/storage/unit_of_work.py:145-156
```python
        done: list[str] = []
        try:
            while self._staged:
                tmp, target = self._staged[0]
                commit_staged(tmp, target)
                self._staged.pop(0)  # 성공한 것만 목록에서 뺀다 — 나머지는 rollback 대상
                done.append(target.name)
        except OSError:
            pending = [target.name for _, target in self._staged]
            logger.warning(messages.LOG_UOW_PARTIAL, done or "없음", pending)
            self.rollback()
            raise
```

`self._staged[0]` 를 보고 **성공한 뒤에야** `pop(0)` 하는 것이 핵심입니다. 두 번째 `os.replace` 가 `PermissionError` 로 죽으면 `_staged` 에는 아직 커밋되지 않은 항목만 남아 있고, `rollback()` 이 그것들의 `.tmp` 만 정확히 지웁니다. 만약 반복 전에 목록을 통째로 비웠다면 어느 `.tmp` 를 치워야 할지 알 수 없었을 것입니다.

### `os.replace` vs `os.rename` — 왜 둘 다 있나

**어디서 왔나** — `os.rename` 은 유닉스 `rename(2)` 를 그대로 노출한 오래된 함수입니다. 문제는 POSIX 와 Windows 의 동작이 **대상이 이미 있을 때 갈라진다**는 것입니다. POSIX 는 조용히 덮어쓰고, Windows 는 오류를 냅니다. 그래서 "어느 플랫폼에서든 덮어쓴다"를 약속하는 `os.replace` 가 뒤늦게 추가됐습니다(3.13 의 `os.replace.__doc__` 첫 줄이 "Rename a file or directory, overwriting the destination." 입니다).

3.13(Windows)에서 나란히 실행한 결과입니다.

```
os.rename  onto existing -> FileExistsError 17 파일이 이미 있으므로 만들 수 없습니다
os.replace onto existing -> OK, content = new
```

**이 소스에서** — `budget_app` 전체에 `os.rename` 은 한 번도 나오지 않고 `os.replace` 만 씁니다(jsonl.py:77).

**없으면 어떻게 되나** — `os.rename` 을 썼다면 이 프로그램은 **리눅스에서만 동작**했을 것입니다. Windows 에서는 첫 저장 이후 모든 재작성이 `FileExistsError` 로 실패합니다. "먼저 `target.unlink()` 하고 rename 하면 되지 않나"는 더 나쁩니다 — unlink 와 rename 사이에 **대상 파일이 존재하지 않는 창**이 생기고, 그것이 바로 원자적 교체가 없애려던 상태입니다.

### 원자적 쓰기 3단계가 막는 고장 — 그리고 정직하게, 못 막는 고장

이 소스의 원자적 쓰기는 세 걸음입니다(`stage_lines` → `commit_staged`, 묶은 것이 `atomic_write_lines`).

budget_app/storage/jsonl.py:80-87
```python
def atomic_write_lines(path: Path, lines: Iterable[str]) -> None:
    """파일 하나를 원자적으로 교체한다 — 준비와 커밋을 연달아 수행.

    이름에 밑줄이 없는 이유: 같은 계층의 ``ids.IdWatermark`` 도 이 함수를 쓴다.
    "JSONL 파일을 다루는 법"이 아니라 "파일 하나를 안전하게 갈아 끼우는 법"이라
    저장소 계층의 공용 도구다.
    """
    commit_staged(stage_lines(path, lines), path)
```

| 단계 | 막는 고장 |
|---|---|
| ① 임시 파일에 쓴다 | 쓰는 도중 죽어도 **원본은 그대로**다. 원본을 직접 열어 덮어쓰면 `open(..., "w")` 하는 순간 원본이 0바이트가 되고, 그 시점에 죽으면 데이터가 전부 사라진다. 동시에 읽고 있는 프로세스가 절반짜리 파일을 보는 일도 없다. |
| ② `flush` + `fsync` | 전원 차단 시 **"새 이름이 빈 파일을 가리키는"** 상태를 막는다. rename 은 순서를 보장하지 않으므로, 내용보다 이름 교체가 먼저 디스크에 도달할 수 있다. |
| ③ `os.replace` | 교체 순간의 **중간 상태를 없앤다**. 읽는 쪽은 옛 파일 전체 아니면 새 파일 전체만 본다. |

못 막는 것도 같은 무게로 적어 둡니다.

- **디렉터리 fsync 가 없습니다.** ②가 파일 *내용* 의 내구성을 보장해도, ③이 만든 디렉터리 엔트리 변경 자체는 아직 디스크에 없을 수 있습니다. 그 순간 전원이 끊기면 파일 이름이 옛 상태로 되돌아갈 수 있습니다. (앞서 봤듯 Windows 에서는 애초에 시도할 수 없는 방어입니다.)
- **rename 2회 사이의 창이 남습니다.** `UnitOfWork` 는 파일 두 개를 바꾸므로 `os.replace` 를 두 번 부릅니다. 그 사이에 전원이 끊기면 한쪽만 반영된 상태가 남습니다. `unit_of_work.py` 의 모듈 docstring 이 이것을 "창을 밀리초 단위로 줄이는 것이지 없애는 것이 아니다"라고 스스로 밝혀 두었습니다. 진짜 다중 파일 원자성은 저널이나 SQLite 가 필요합니다.
- **`.tmp` 찌꺼기가 남을 수 있습니다.** 준비 도중 프로세스가 강제 종료되면 `rollback()` 이 돌지 못합니다. 원본은 무사하지만 파일이 하나 남습니다.

### 텍스트 모드의 줄바꿈 변환 — `newline=` 이 없으면 JSONL 이 오염된다

**어디서 왔나** — "읽을 때 `\n`/`\r\n`/`\r` 을 전부 `\n` 으로 통일해 준다"는 유니버설 개행(universal newlines)은 PEP 278 이 파이썬 2 시절에 들여온 것입니다(당시에는 `open(path, "U")` 모드). 파이썬 3 의 `io` 스택에서는 그것이 `open()` 의 `newline=` 매개변수로 정리됐고, **쓰기 방향의 변환**까지 같은 매개변수가 제어하게 됐습니다.

**내부에서 무슨 일이 일어나나** — 변환은 `TextIOWrapper`(3층 중 맨 위)가 합니다. 아래 두 층은 바이트만 다루므로 이 변환을 모릅니다.

| `newline=` | 읽기 | 쓰기 |
|---|---|---|
| `None` (기본) | `\n`, `\r\n`, `\r` → 전부 `\n` | `\n` → **`os.linesep`** (Windows 에서 `\r\n`) |
| `""` | 변환 없음 (`\r\n` 이 그대로 옴) | 변환 없음 |
| `"\n"` / `"\r\n"` | 그 문자열만 줄 끝으로 인정 | `\n` → 지정한 문자열 |

3.13(Windows, `os.linesep == '\r\n'`)에서 같은 `"a\nb\n"` 을 네 가지로 써 본 결과입니다.

```
newline=None  -> b'a\r\nb\r\n'      ← \n 이 조용히 \r\n 으로 바뀌었다
newline=""    -> b'a\nb\n'
newline="\n"  -> b'a\nb\n'
newline="\r\n"-> b'a\r\nb\r\n'
```

**이 소스에서** — 저장소 계층이 줄 종결자를 상수로 못 박고, 파일을 여는 모든 곳에 그것을 넘깁니다.

budget_app/storage/config.py:22-27
```python
FILE_ENCODING = "utf-8"
#: 디코딩 불가 바이트를 예외 대신 대리 문자로 받아 **무손실 왕복**시킨다.
#: 읽기와 쓰기가 같은 정책을 쓰므로 손상된 줄이 원문 바이트 그대로 보존된다.
FILE_ERRORS = "surrogateescape"
LINE_TERMINATOR = "\n"
TMP_SUFFIX = ".tmp"
```

`stage_lines`(jsonl.py:66)와 `_append_lines`(jsonl.py:239)가 둘 다 `newline=config.LINE_TERMINATOR` 로 엽니다.

**없으면 어떻게 되나** — Windows 에서 `newline=` 을 빼면 코드가 쓴 `"\n"` 이 전부 `"\r\n"` 이 됩니다. 결과가 두 갈래로 번집니다.

- **JSONL 파일이 플랫폼마다 달라집니다.** 리눅스에서 만든 데이터 폴더와 Windows 에서 만든 데이터 폴더의 바이트가 달라지고, 같은 내용인데 파일 해시가 다릅니다.
- **`_has_torn_tail` 이 무너집니다.** 그 함수는 마지막 바이트를 `config.LINE_TERMINATOR.encode(...)` 즉 `b"\n"` 과 비교하는데, 파일 끝이 `\r\n` 이면 마지막 바이트는 여전히 `b"\n"` 이라 우연히 통과합니다. 반대로 `newline="\r"` 같은 설정이었다면 매번 "찢어진 꼬리"로 오판해 빈 줄을 계속 추가했을 것입니다. **쓰기 정책과 검사 기준이 같은 상수를 보고 있어야** 이 검사가 성립합니다.

> **CSV 는 정반대로 `newline=""` 입니다** — `csv` 모듈이 줄 끝을 **직접** 쓰므로, 텍스트 층이 또 변환하면 `\r` 이 두 번 들어갑니다. 이 소스는 읽기(csv_io.py:82)와 쓰기(csv_io.py:142) 양쪽 모두 `newline=""` 로 열어 그 요구를 지킵니다. 오염된 바이트열 실측과 "여러 줄 메모가 조용히 바뀐다"는 결과는 §2-A 의 「`open(..., newline="")`」 항목에 있습니다.

### 읽기 쪽의 비대칭 — `iter_raw` 는 왜 `newline=` 을 지정하지 않아도 안전한가

**이 소스에서** — 쓰기는 `newline` 을 못 박는데 읽기는 지정하지 않습니다.

budget_app/storage/jsonl.py:172-179
```python
        if not self.path.exists():
            return
        with open(self.path, encoding=config.FILE_ENCODING, errors=config.FILE_ERRORS) as f:
            for lineno, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line:
                    continue
                yield self._parse_line(lineno, line)
```

**왜 안전한가** — 비대칭이 오히려 정답입니다. 이유가 두 겹입니다.

1. **읽기의 기본값 `newline=None` 은 유니버설 개행**이라, `\n` 으로 끝나든 `\r\n` 으로 끝나든 파이썬이 알아서 `\n` 으로 통일해 줍니다. 다른 OS 에서 만들어진 파일, 에디터가 CRLF 로 저장해 버린 파일도 그대로 읽힙니다. 여기서 `newline="\n"` 으로 못 박으면 **읽는 능력만 좁아집니다** — CRLF 파일의 각 줄 끝에 `\r` 이 남고 `json.loads` 는 그것을 견디지만, 원문 보존 경로가 그 `\r` 을 계속 나릅니다.
2. **`raw.strip()` 이 마지막 방어**입니다. `str.strip()` 은 인자가 없으면 양끝의 모든 공백 문자를 떼어내는데, 여기에 `\n` 과 `\r` 이 포함됩니다. 3.13 확인: `newline=""` 로 CRLF 파일을 읽어 `\r\n` 이 그대로 온 줄에 `.strip()` 을 걸면 결과는 `'a'`, `'b'` 입니다.

정리하면 **쓰기는 좁게, 읽기는 넓게**입니다. 우리가 만드는 바이트는 한 가지로 고정하고(재현 가능성), 남이 준 바이트는 최대한 받아들입니다(관용). 그리고 `strip()` 덕분에 두 정책이 만나는 지점에서 `\r` 이 도메인 층까지 새어 나가지 않습니다.

**없으면 어떻게 되나** — `strip()` 없이 `json.loads(raw)` 를 했다면 JSON 파싱 자체는 통과합니다(JSON 은 끝의 공백을 허용). 그러나 `plan_rewrite` 가 **해석 실패한 줄을 `raw.text` 로 원문 보존**할 때, 그 `text` 에 `\r\n` 이 붙은 채로 저장되고 `_encode` 결과와 비교하는 `encoded != raw.text` 판정이 항상 참이 되어 **바뀐 것이 없는데도 매번 파일을 다시 씁니다**.

### `errors="surrogateescape"` — 깨진 바이트를 잃지 않고 왕복시키는 법

**어디서 왔나** — **PEP 383**(Non-decodable Bytes in System Character Interfaces)이 정의한 오류 처리기입니다. 원래 목적은 파일 이름·환경변수처럼 "OS 가 바이트로 주는데 파이썬은 문자열로 다루고 싶은" 경계였습니다.

> **💡 쉽게 말하면** — 물에 젖어 글씨를 알아볼 수 없는 줄이 섞인 장부를 옮겨 적는 상황입니다. 못 읽겠다고 그 줄을 빼 버리면 증거가 사라지고, 짐작으로 고쳐 적으면 없던 사실이 생깁니다. 그래서 못 읽는 부분에는 봉인 딱지를 붙여 그대로 옮겨 두었다가, 나중에 원본으로 되돌릴 때 딱지를 떼면 원래의 얼룩이 한 점도 다르지 않게 돌아옵니다.
> 다만 이 비유는 딱지 붙인 줄을 아무 데나 옮겨 적을 수는 없다는 점에서 깨집니다 — 같은 봉인 규칙을 아는 곳으로 되돌릴 때만 원문이 살아나고, `errors` 를 지정하지 않은(기본 strict) 인코딩 경로로 내보내려 하면 그 자리에서 `UnicodeEncodeError` 가 납니다(아래 「없으면 어떻게 되나」 2번). 화면 출력은 오히려 같은 규칙을 쓰고 있어 그냥 통과합니다 — 다만 통과한다고 안전한 것은 아니고, 그쪽에는 아래 주의 상자의 cp949 사례라는 별개의 구멍이 있습니다.

**내부에서 무슨 일이 일어나나** — 규칙이 대단히 단순합니다. 디코딩할 수 없는 바이트 `b`(0x80~0xFF)를 **`U+DC00 + b`** 라는 코드포인트로 바꿉니다. 즉 사용 가능한 범위는 **U+DC80 ~ U+DCFF** 이고, 이 구간은 유니코드의 하위 서로게이트 영역이라 정상적인 텍스트에는 절대 나타나지 않습니다. 인코딩할 때 같은 처리기를 쓰면 그 코드포인트에서 하위 8비트를 도로 꺼내 **원래 바이트를 그대로 복원**합니다.

3.13 에서 증명한 결과입니다. 정상 JSON 두 줄 사이에 UTF-8 이 아닌 바이트 `\xff\xfe ... \x80` 을 끼워 넣은 파일로 실험했습니다.

```
strict  -> UnicodeDecodeError : 'utf-8' codec can't decode byte 0xff in position 20: invalid start byte
                                ← 첫 줄은 멀쩡한데 파일 전체 읽기가 여기서 죽는다

surrogate lines: ['{"id": "TX-000001"}', '\udcff\udcfe broken \udc80 line', '{"id": "TX-000002"}']
re-encoded    : b'\xff\xfe broken \x80 line'
roundtrip ok  : True                        ← 원래 바이트가 정확히 복원됐다
```

`0xff` → `\udcff`, `0x80` → `\udc80`. 규칙이 눈에 그대로 보입니다.

**이 소스에서** — `FILE_ERRORS = "surrogateescape"`(storage/config.py:25)가 **읽기와 쓰기 양쪽에** 넘어갑니다 — `iter_raw`(jsonl.py:174), `stage_lines`(jsonl.py:65), `_append_lines`(jsonl.py:238). 양쪽이 같아야 왕복이 성립하므로, 이 상수가 한 곳에 있다는 사실 자체가 방어입니다.

`iter_raw` 의 docstring 이 이것을 "약속의 구멍을 메운 것"이라고 설명합니다 — JSON 이 깨진 줄은 `RawLine` 으로 격리해 원문 보존하면서, 바이트가 깨진 줄만 격리하지 못하는 것은 같은 정책의 예외였다는 것입니다.

**없으면 어떻게 되나** — 두 지점이 동시에 깨집니다.

1. **읽기**: 기본값 `errors="strict"` 로 돌아가면 위 실행 결과대로 `UnicodeDecodeError` 가 나고, `iter_raw` 는 제너레이터라 **그 예외가 호출자에게 전파**됩니다. 손상된 줄 하나 때문에 `list`, `summary`, `delete` 가 전부 죽습니다. `handle_errors` 가 잡아 종료 코드 6(`EXIT_ENCODING`)으로 끝내 주긴 하지만, 사용자는 정상적인 나머지 거래에도 접근할 수 없게 됩니다.
2. **쓰기**: 읽기만 `surrogateescape` 로 바꾸고 쓰기를 놔뒀다면 더 나쁩니다. `plan_rewrite` 가 보존한 `\udcff...` 문자열을 다시 쓰는 순간 `UnicodeEncodeError` 가 납니다(3.13 확인: `'utf-8' codec can't encode characters in position 0-1: surrogates not allowed`). **읽기는 성공했는데 재작성이 죽는** — 즉 손상 줄이 있는 파일에서는 어떤 수정도 불가능해지는 상태가 됩니다.

> **주의: 만능이 아닙니다.** `surrogateescape` 는 "그 처리기로 디코딩되어 들어온 바이트"만 되돌립니다. 정상적인 문자인데 대상 인코딩에 없는 경우는 구제하지 못합니다. 이 프로젝트에서 실제로 확인한 사례가 있습니다 — Windows 기본 콘솔 인코딩(cp949) 아래에서 `python -m budget_app --help` 를 실행하면 도움말 안의 em dash(`—`, U+2014)에서 `UnicodeEncodeError: 'cp949' codec can't encode character '—'` 로 죽습니다. `sys.stdout.errors` 가 `surrogateescape` 인데도 그렇습니다(3.13 확인). `PYTHONIOENCODING=utf-8` 을 주면 정상 출력됩니다. 이것은 파일 인코딩 정책과 무관한 **표준 출력 인코딩** 문제라 `FILE_ERRORS` 로는 막을 수 없습니다.

### `"rb"` + `f.seek(-1, os.SEEK_END)` — 왜 바이너리 모드여야 하나

**어디서 왔나** — `seek(offset, whence)` 의 3인자 형태는 C 의 `fseek` 를 그대로 물려받은 것이고, `os.SEEK_SET`(0) / `os.SEEK_CUR`(1) / `os.SEEK_END`(2) 상수도 마찬가지입니다.

**내부에서 무슨 일이 일어나나** — 텍스트 모드에서는 **임의 위치로 seek 할 수 없습니다.** `TextIOWrapper` 는 바이트 위치와 문자 위치의 대응을 모르기 때문입니다. UTF-8 은 문자당 1~4바이트고, 게다가 이 소스처럼 줄바꿈 변환까지 켜져 있으면 "끝에서 1문자 앞"이 몇 바이트 앞인지 계산할 방법이 없습니다. 그래서 `TextIOWrapper.seek` 는 `SEEK_END` 에 대해 오프셋 0 만 허용하고 나머지는 거부합니다.

3.13 확인 결과입니다.

```
text  seek(-1, END) -> io.UnsupportedOperation : can't do nonzero end-relative seeks
text  seek( 0, END) -> 4        ← 오프셋 0 은 허용
binary last byte    -> b'\n'    ← 바이너리에서는 문제없다
```

(참고: 텍스트 모드에서 `f.tell()` 이 돌려주는 값도 바이트 오프셋이 아니라 **`seek()` 에 되돌려 넣을 수 있는 불투명한 쿠키**입니다. 산술 연산의 대상이 아닙니다.)

**이 소스에서** —

budget_app/storage/jsonl.py:249-262
```python
    def _has_torn_tail(self) -> bool:
        """마지막 바이트가 개행이 아닌가 — 바이트로 직접 확인한다.

        텍스트 모드로 끝을 보려면 파일을 통째로 읽어야 한다. ``rb`` + ``seek`` 이면
        1바이트만 읽으면 되고, 인코딩이 깨진 파일에서도 안전하다.
        """
        try:
            if self.path.stat().st_size == 0:
                return False
            with open(self.path, "rb") as f:
                f.seek(-1, os.SEEK_END)
                return f.read(1) != config.LINE_TERMINATOR.encode(config.FILE_ENCODING)
        except OSError:
            return False  # 파일이 없다 — 이어 쓰기가 새로 만든다
```

docstring 이 이유를 둘 댑니다. **비용**(텍스트 모드로 끝을 보려면 파일 전체를 읽어야 하는데, 여기서는 10만 줄짜리 파일에서도 1바이트만 읽습니다)과 **안전성**(이 검사는 인코딩이 깨진 파일에서도 동작해야 하는데, 바이트 층에는 디코딩이라는 개념이 없어 절대 실패하지 않습니다).

`st_size == 0` 을 먼저 보는 것도 필수입니다. 빈 파일에서 `seek(-1, SEEK_END)` 는 파일 시작보다 앞을 가리키게 되어 `OSError`(`EINVAL`)입니다.

**없으면 어떻게 되나** — 텍스트 모드로 같은 일을 하려 하면 `io.UnsupportedOperation` 이 나는데, **여기서 실패 양상이 즉사보다 나쁩니다.** 이 예외의 MRO 를 보면 `OSError` 와 `ValueError` 를 **동시에** 상속합니다(3.13 확인).

```
io.UnsupportedOperation.__mro__
 -> (io.UnsupportedOperation, OSError, ValueError, Exception, BaseException, object)
```

즉 이 예외는 위 코드의 `except OSError: return False` 에 **그대로 걸립니다.** 텍스트 모드로 바꿔 놓고 실제로 돌려 본 결과입니다 — 파일 내용은 `'a\nb'` 라 마지막 바이트가 개행이 아니므로 정답은 `True` 여야 하는데,

```
   caught by except OSError: UnsupportedOperation can't do nonzero end-relative seeks
text-mode result -> False        ← 찢어진 꼬리인데 아니라고 답한다
```

시끄럽게 죽는 것이 아니라 **조용히 `False` 를 돌려주어 찢어진 꼬리를 영영 감지하지 못합니다.** 그러면 `_append_lines` 는 개행 보정을 건너뛰고, 뒤 절에서 볼 "레코드 두 개가 동시에 죽는" 상태가 아무 경고 없이 만들어집니다. 예외로 죽었다면 최소한 누군가 알아챘을 텐데, 이쪽은 방어가 살아 있는 것처럼 보이면서 매번 틀린 답을 냅니다. 대안인 "전체를 읽어 마지막 문자 확인"은 두 가지 이유로 나쁩니다 — 이어 쓰기 한 번마다 파일 전체를 읽는 O(n) 비용이 생기고, 손상 바이트가 있는 파일에서는 그 읽기가 예외로 죽어 **이어 쓰기 자체가 불가능해집니다.**

### 이어 쓰기 모드 `"a"` 와 "찢어진 꼬리"

**어디서 왔나** — `"a"` 는 C 표준 라이브러리 `fopen` 의 append 모드이자 POSIX 의 `O_APPEND` 플래그입니다. 의미가 "파일 끝으로 한 번 이동한다"가 아니라 **"매 write 마다 커널이 원자적으로 파일 끝으로 이동한 뒤 쓴다"**라는 점이 중요합니다.

3.13 확인 — append 로 연 뒤 명시적으로 `seek(0)` 을 해도 쓰기는 여전히 끝에 붙습니다.

```
append tell after open -> 4    ← 열자마자 위치가 끝
after seek(0), tell    -> 0    ← 위치는 실제로 앞으로 갔는데
file after append+write -> b'abc\nX'    ← 쓰기는 끝에 붙었다
```

**이 소스에서** — `_append_lines` 가 이어 쓰기 전에 개행을 먼저 씁니다.

budget_app/storage/jsonl.py:232-247
```python
        self.path.parent.mkdir(parents=True, exist_ok=True)
        needs_newline = self._has_torn_tail()
        with open(
            self.path,
            "a",
            encoding=config.FILE_ENCODING,
            errors=config.FILE_ERRORS,
            newline=config.LINE_TERMINATOR,
        ) as f:
            if needs_newline:
                f.write(config.LINE_TERMINATOR)
                logger.warning(messages.LOG_TORN_TAIL, self.path.name)
            for line in lines:
                f.write(line + config.LINE_TERMINATOR)
            f.flush()
            os.fsync(f.fileno())
```

`needs_newline` 을 **`open` 전에** 계산하는 것도 의도된 순서입니다. `_has_torn_tail` 은 파일을 따로 `"rb"` 로 열므로, 같은 파일을 두 핸들로 동시에 여는 상황을 만들지 않습니다.

**없으면 어떻게 되나** — JSONL 은 "한 줄 = 한 레코드"라는 규약 위에 서 있고, 그 규약을 깨는 유일한 방법이 개행 누락입니다. 3.13 에서 실제로 재현했습니다. 마지막 줄에 개행이 없는 파일에 개행 보정 없이 이어 쓰면,

```
1 OK   {"id": "TX-000001"}
2 FAIL {"id": "TX-000002"{"id": "TX-000003"} <- Expecting ',' delimiter: line 1 column 19
```

**레코드 두 개가 동시에 죽습니다.** 그리고 피해가 대칭이 아닙니다. 기존 줄(`TX-000002`)은 그래도 `RawLine` 으로 원문 보존되지만, 방금 사용자에게 "저장했습니다"라고 알린 `TX-000003` 은 목록 어디에도 나타나지 않습니다. 프로그램이 성공을 보고한 쓰기가 사라지는 것 — `_append_lines` 의 docstring 이 이 비대칭을 지적하고 있습니다.

### stdout / stderr 버퍼링 정책 — `output.err` 가 stdout 을 먼저 비우는 이유

**어디서 왔나** — 파이썬은 시작할 때 세 표준 스트림을 만들면서 버퍼링 정책을 정합니다. 규칙이 **스트림마다 다르고, 상대가 터미널이냐 아니냐에 따라 또 다릅니다.**

- **stdout**: 터미널이면 라인 버퍼(`line_buffering=True`), 파일이나 파이프면 **블록 버퍼**(8192바이트가 차야 나감).
- **stderr**: 터미널이 아니어도 **라인 버퍼**입니다. 3.13 에서 확인했습니다.

```
stdout isatty: False  line_buffering: False   ← 파이프. 블록 버퍼링
stderr isatty: False  line_buffering: True    ← 파이프인데도 줄마다 나간다
```

stderr 가 언제부터 이렇게 됐는지는 로컬에서 확인할 방법이 없으므로 도입 버전은 적지 않습니다. **지금(3.13.1) 관찰되는 사실만 남깁니다 — stderr 는 파이프로 연결돼도 라인 버퍼입니다.** 결론에는 영향이 없습니다. 두 스트림의 버퍼링이 다르므로, 다시 합치면 순서가 어긋납니다.

**무슨 일이 일어나나** — `cmd 2>&1 | less` 처럼 두 채널을 하나로 합치면, stderr 는 즉시 나가고 stdout 은 버퍼에 쌓여 있다가 프로그램 종료 시점에 한꺼번에 나옵니다. 3.13 에서 재현했습니다.

```
=== flush 없이 (2>&1 | cat) ===
[ERROR] something went wrong     ← 진단이 결과보다 앞으로 튀어나왔다
RESULT line 1
RESULT line 2
RESULT line 3

=== stderr 쓰기 전에 sys.stdout.flush() (2>&1 | cat) ===
RESULT line 1
RESULT line 2
[ERROR] something went wrong     ← 제자리
RESULT line 3
```

**이 소스에서** —

budget_app/cli/output.py:60-66
```python
    try:
        sys.stdout.flush()
    except (BrokenPipeError, ValueError):
        # 하류 파이프가 이미 닫혔거나 stdout 이 닫힌 상태.
        # 그래도 stderr 는 살아 있으므로 진단 출력은 계속한다(이게 채널 분리의 이점).
        pass
    print(message, file=sys.stderr)
```

`try`/`except` 로 감싼 것도 필요합니다. `flush` 는 하류가 이미 닫혔으면 `BrokenPipeError` 를, 스트림이 닫혔으면 `ValueError` 를 던집니다. 그런데 `err()` 는 **오류를 알리려고 불린 함수**입니다. 여기서 예외가 나가면 원래 알리려던 오류가 묻힙니다.

> **문서와 코드의 어긋남 하나** — 이 함수의 docstring 은 "stderr 는 버퍼링 없음"이라고 적고 있습니다. 3.13 에서 확인한 실제 값은 `line_buffering=True` 이지 언버퍼가 아닙니다. **판단 자체는 그대로 옳습니다** — 문제를 만드는 것은 "stderr 가 언버퍼"라서가 아니라 **"stdout 이 블록 버퍼"**라서이고, 그 부분은 docstring 도 정확히 적고 있습니다. 괄호 안 한 구절만 낡았습니다.

**없으면 어떻게 되나** — 터미널에서 직접 실행하면 stdout 도 라인 버퍼라 아무 문제가 없어서, **이 버그는 리다이렉트하거나 파이프에 물릴 때만 나타납니다.** `budget_app import bad.csv 2>&1 | less` 로 오류를 살펴보려는 사용자는 "무슨 오류가 있었는지"를 맨 위에서 보고 "어느 행에서 났는지"를 저 아래에서 보게 됩니다. 즉 **디버깅하려고 쓴 명령에서만 출력이 뒤엉킵니다.**

### `BrokenPipeError` 의 발생 경로와 `os.dup2` 라는 근본 해결

**어디서 왔나 (유닉스 기준 — 로컬이 Windows 라 이 경로는 재현하지 못했습니다)** — 유닉스에서 닫힌 파이프에 쓰면 커널이 `SIGPIPE` 시그널을 보내고, 기본 동작은 **프로세스 즉시 종료**입니다. `cat huge | head` 에서 `cat` 이 조용히 끝나는 것이 그 덕분입니다. 그런데 파이썬은 시작할 때 **`SIGPIPE` 의 처리를 `SIG_IGN`(무시)로 바꿔 둡니다.** 시그널로 갑자기 죽으면 `finally` 블록도, 소멸자도, `atexit` 도 돌지 못하기 때문입니다. 무시로 바꿔 두었으므로 유닉스에서는 쓰기가 시그널 대신 `EPIPE` 로 실패하고, 그것이 `BrokenPipeError` 가 됩니다. **PEP 3151** 이 errno 별 예외 계층을 도입하면서 생긴 대응입니다.

여기서 로컬(Windows)로 확인할 수 있는 조각은 딱 하나 — errno 에서 예외 클래스로의 매핑입니다. 파이프 자체를 끊어 본 것이 아니라 예외 객체를 만들어 본 것입니다(3.13 확인).

```
type(OSError(errno.EPIPE, 'x')).__name__  ->  BrokenPipeError
```

반대로 Windows 에는 `SIGPIPE` 가 아예 없어서(3.13 확인: `'SIGPIPE' in dir(signal)` 이 `False`) 위 유닉스 경로 자체가 성립하지 않습니다. 실제로 파이프를 끊었을 때 로컬에서 무엇이 오는지는 이 절 끝의 "Windows 에서의 정직한 단서"에 따로 적었습니다.

**무엇이 문제인가** — `except BrokenPipeError` 로 잡고 정상 종료하는 것만으로는 부족합니다. **인터프리터가 종료하면서 `sys.stdout` 을 flush 하는데, 버퍼에 남은 바이트가 다시 같은 깨진 파이프로 나가면서 예외가 한 번 더 납니다.** 그 시점에는 잡아 줄 코드가 없어 파이썬이 `Exception ignored in: <_io.TextIOWrapper ...>` 를 stderr 로 찍습니다(이 두 번째 단계는 유닉스에서 보고되는 증상이고, 로컬 Windows 재현에서는 첫 단계인 `print` 자체의 트레이스백까지만 관찰됐습니다 — 아래 실행 결과). `head` 로 앞 몇 줄만 본 사용자가 잘못한 것이 없는데 오류 메시지를 받게 됩니다.

공식 해법은 **stdout 의 fd 자체를 `/dev/null` 로 갈아 끼우는 것**입니다(파이썬 `signal` 모듈 문서의 "Note on SIGPIPE" 레시피). `os.dup2(devnull, sys.stdout.fileno())` 는 커널의 fd 테이블에서 1번 항목이 devnull 을 가리키게 바꿉니다. 파이썬 객체는 그대로라 종료 시 flush 도 그대로 일어나지만, 그 바이트는 이제 깨진 파이프가 아니라 **아무 데도 가지 않는 곳**으로 갑니다.

**이 소스에서** —

budget_app/cli/app.py:50-58
```python
def _silence_broken_pipe() -> None:
    """하류 파이프(``list | head``)가 먼저 닫혔을 때 남은 출력을 os.devnull 로 돌려,
    인터프리터 종료 시 BrokenPipeError 재발과 'Exception ignored' 출력을 막는다
    (파이썬 공식 권장 레시피)."""
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
    except OSError:
        pass
```

호출 지점은 `main` 의 최상위 한 곳입니다.

budget_app/cli/app.py:91-94
```python
    except BrokenPipeError:
        # 예: `budget_app list | head` — head 가 먼저 닫음. 오류가 아니므로 조용히 종료.
        _silence_broken_pipe()
        return config.EXIT_OK
```

`handle_errors` 는 `BrokenPipeError` 를 **잡자마자 다시 던집니다**(error_handler.py:57-60). "여기서 출력하면 또 깨지므로" — 예외 처리 자체가 stderr 출력을 시도하는데, 그 앞에 있는 `output.err` 의 `sys.stdout.flush()` 가 다시 터질 자리이기 때문입니다. 그래서 이 예외만은 `main` 까지 그대로 올려보냅니다.

3.13(Windows)에서 두 방식을 비교한 결과입니다.

```
=== 처리 없이 (200000줄 출력 | head -3) ===
0
1
2
Traceback (most recent call last):
  File "pipe_raw.py", line 2, in <module>
    print(i)
OSError: [Errno 22] Invalid argument       ← 사용자는 잘못한 것이 없는데 트레이스백

=== dup2(devnull) 처리 후 ===
0
1
2
(stderr 출력 0바이트)
```

**Windows 에서의 정직한 단서** — 위 트레이스백을 보면 예외가 `BrokenPipeError` 가 아니라 `OSError [Errno 22] Invalid argument`(EINVAL)입니다. Windows 에는 `SIGPIPE` 자체가 없고(3.13 확인: `hasattr(signal, 'SIGPIPE')` 는 `False`), 닫힌 파이프에 쓸 때 나는 오류가 `EPIPE` 로 매핑되지 않는 경우가 있습니다. 그러면 `main` 의 `except BrokenPipeError` 에 걸리지 않고 `handle_errors` 의 마지막 `except OSError`(error_handler.py:99-103)에 걸려 **"[오류] 입출력 문제" 메시지와 종료 코드 3** 으로 끝납니다. 유닉스에서는 조용히 0 으로 끝나는 같은 명령이 Windows 에서는 오류로 보이는 것 — 이 소스가 아직 다루지 않는 플랫폼 차이입니다.

### `os.open(os.devnull, os.O_WRONLY)` — 저수준 fd 와 `open()` 의 차이

**어디서 왔나** — `os.open` 은 POSIX `open(2)` 시스템 콜을 거의 그대로 노출합니다. 내장 `open()` 과 이름만 비슷하고 하는 일이 다릅니다.

| | 돌려주는 것 | 버퍼링 | 인코딩 | 닫는 법 |
|---|---|---|---|---|
| `open(path, "w")` | `TextIOWrapper` 객체 | 3층 | 있음 | `f.close()` / `with` |
| `os.open(path, os.O_WRONLY)` | **정수** fd | 없음 | 없음(바이트) | `os.close(fd)` |

`_silence_broken_pipe` 가 저수준을 쓰는 이유는 **`os.dup2` 가 fd 번호만 받기 때문**입니다. 파이썬 객체 층은 필요 없고, 오히려 여기서 또 하나의 버퍼를 만들 이유가 없습니다.

`os.devnull` 은 "아무것도 저장하지 않고 쓰기를 항상 성공시키는 장치"의 **플랫폼별 경로 문자열**입니다. POSIX 에서는 `'/dev/null'`, Windows 에서는 `'nul'` 입니다(3.13 확인). 경로를 하드코딩하면 한쪽 플랫폼에서 `FileNotFoundError` 가 납니다.

**없으면 어떻게 되나** — 이 함수 전체가 `try/except OSError: pass` 로 감싸여 있는 것도 의도적입니다. 이 함수는 **이미 오류가 난 뒤의 뒷정리**입니다. 여기서 실패해도 사용자에게 알릴 것이 없고, 알리려다 또 실패하면 원래 목적(조용한 종료)이 무너집니다.

### `sys.exit(n)` → `SystemExit` → 셸 종료 코드

**어디서 왔나** — `sys.exit(n)` 은 프로세스를 즉시 끝내는 것이 **아니라** `SystemExit` 예외를 던지는 것입니다. `SystemExit` 은 `Exception` 이 아니라 **`BaseException` 을 직접 상속**합니다(3.13 확인: MRO 가 `SystemExit → BaseException → object`). 이 상속 관계 하나가 실무적 의미를 갖습니다 — 흔한 `except Exception:` 에 걸리지 않으므로, 프로그램 종료 의도가 광범위한 예외 처리에 삼켜지지 않습니다.

예외이므로 **잡을 수 있습니다.** 3.13 확인:

```
SystemExit caught, code = 3
after catch exit=0        ← 잡아 버리면 프로세스는 정상 종료한다
```

아무도 잡지 않으면 인터프리터가 최상위에서 받아 `e.code` 를 프로세스 종료 상태로 삼습니다. `None` 이나 인자 없음은 0, 정수는 그 값, 그 밖의 객체는 stderr 로 출력하고 1 입니다.

**이 소스에서** — 종료 코드의 흐름이 세 파일에 나뉘어 있습니다. 정책은 상수로
(`cli/config.py:21-29` 의 `EXIT_*` 여덟 개 — 전문은 §1-A 의 `sys.exit` 항목에
인용했습니다), 변환은 `handle_errors` 가(예외를 잡아 이 상수 중 하나를 **반환**), 전달은 진입점이 합니다.

budget_app/__main__.py:1-8
```python
"""python -m budget_app 진입점."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
```

**`EXIT_INTERRUPT = 130` 의 출처** — 유닉스 셸은 시그널로 죽은 프로세스를 **`128 + 시그널번호`** 로 보고합니다. `SIGINT`(Ctrl+C)가 2번이므로 `128 + 2 = 130` 입니다. 파이썬 프로그램이 `KeyboardInterrupt` 를 잡아서 정상 종료하면 셸에서는 그냥 0 이나 1 로 보이므로, "사용자가 중단시켰다"는 사실이 사라집니다. 이 소스는 `KeyboardInterrupt` 를 잡아 메시지를 낸 뒤(error_handler.py:61-63) **일부러 130 을 돌려주어** 셸 관례에 맞춥니다. 스크립트가 `if [ $? -eq 130 ]` 로 "사용자 취소"를 구별할 수 있게 하기 위해서입니다.

**셸에서 읽는 법** —

```
POSIX 셸 (bash/zsh)   : budget_app list ; echo $?
PowerShell            : budget_app list ; $LASTEXITCODE
cmd.exe               : budget_app list & echo %ERRORLEVEL%
```

> PowerShell 의 `$?` 는 **불리언**(직전 명령의 성공 여부)이라 종료 코드가 아닙니다. 네이티브 실행 파일의 숫자 코드는 `$LASTEXITCODE` 에 있습니다. 이 문서의 실행 예를 PowerShell 로 재현할 때 자주 걸리는 부분입니다.

**없으면 어떻게 되나** — `main()` 이 정수를 돌려주는데 `sys.exit` 로 감싸지 않고 그냥 부르면, 반환값이 버려지고 종료 코드는 **항상 0** 이 됩니다. CI 스크립트나 `&&` 로 이어 붙인 셸 파이프라인이 실패를 성공으로 읽습니다. `handle_errors` 가 예외를 정성껏 분류해 6가지 코드로 나눈 노력이 이 한 줄이 없으면 전부 무의미해집니다.

### `Path.stat().st_size` 와 `Path.touch()` — 빈 파일 판정과 생성

**어디서 왔나** — `pathlib` 은 **PEP 428** 이 설계한 모듈입니다. `Path.stat()` 은 `os.stat()` 을 그대로 부르고, 그 결과는 유닉스 `stat(2)` 구조체의 필드를 그대로 갖습니다 — `st_size`(바이트 크기), `st_mtime_ns`(수정 시각) 등.

**내부에서 무슨 일이 일어나나** — `Path.touch()` 는 이름과 달리 두 가지 다른 일을 조건에 따라 골라 합니다. 로컬 CPython 3.13.1 의 실제 구현(`Lib/pathlib/_local.py:695`)을 그대로 옮기면 분명합니다.

```python
def touch(self, mode=0o666, exist_ok=True):
    if exist_ok:
        # First try to bump modification time
        try:
            os.utime(self, None)
        except OSError:
            pass
        else:
            return
    flags = os.O_CREAT | os.O_WRONLY
    if not exist_ok:
        flags |= os.O_EXCL
    fd = os.open(self, flags, mode)
    os.close(fd)
```

즉 **파일이 이미 있으면 수정 시각만 갱신하고 내용은 건드리지 않습니다**(`os.utime`). 없으면 `os.open` 으로 만들고 곧바로 닫습니다 — 그래서 결과는 항상 0바이트입니다. 3.13 확인:

```
touch new      -> exists True, size 0
touch existing -> size stays 5, mtime changed: True
```

**이 소스에서** —

budget_app/storage/jsonl.py:150-158
```python
    def ensure_ready(self) -> None:
        """파일이 없으면 만든다 — 명시적으로 호출될 때만 디스크를 건드린다."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    @property
    def is_empty(self) -> bool:
        return not self.path.exists() or self.path.stat().st_size == 0
```

`if not self.path.exists()` 로 감싼 것이 중요합니다. `touch()` 는 기존 파일의 **내용**은 지키지만 **mtime 은 바꿉니다.** 조회만 하는 명령이 데이터 파일의 수정 시각을 바꾸면 백업 도구와 파일 감시가 헛돕니다 — `rewrite()` 가 "바뀐 것이 없으면 파일을 건드리지 않는다"(jsonl.py:326-327)로 지키려는 것과 같은 원칙입니다.

`is_empty` 는 파일을 **열지 않고** 크기만 봅니다. `CategoryStore.seed_defaults` 가 "빈 파일이면 기본 카테고리를 심는다"를 판정할 때 쓰는데, 여기서 파일을 읽어 줄 수를 세면 손상된 줄에서 예외가 날 수 있고 무엇보다 불필요합니다. `st_size` 는 이미 디렉터리 엔트리에 있는 메타데이터라 내용 읽기가 없습니다.

`_has_torn_tail` 도 같은 판정을 다른 목적으로 씁니다(jsonl.py:256) — 빈 파일에서 `seek(-1, SEEK_END)` 가 `OSError` 로 죽는 것을 미리 막는 가드입니다.

**없으면 어떻게 되나** — `st_size` 대신 `path.read_text()` 로 빈 파일을 판정했다면, 카테고리 파일에 손상 바이트가 섞이는 순간 **프로그램 부팅(`AppContext.prepare`)이 통째로 실패**합니다. 데이터 한 줄이 깨졌다고 프로그램이 시작조차 못 하는 것은 이 소스가 저장소 계층 전체에서 피하려는 실패 방식입니다.

> **관련 — 백업이 바이트로 복사하는 이유**: `backup_data_dir` 은 `(dest / p.name).write_bytes(p.read_bytes())` 로 복사합니다(storage/backup.py:32). 텍스트로 읽어 텍스트로 쓰면 인코딩·줄바꿈 변환이 두 번 개입해 **백업본이 원본과 바이트가 달라질 수 있습니다.** 손상된 줄을 원문 그대로 보존한다는 이 프로젝트의 약속은 백업 경로에서도 지켜져야 하고, 그것을 보장하는 가장 단순한 방법이 텍스트 층을 아예 거치지 않는 것입니다.

---

## 4. 역색인 — 소스 파일에서 이 문서로

> **이 절은 무엇인가** — 이 문서를 실제로 쓰게 되는 자리입니다. 앞의 세 절이 "표기에서 소스로" 내려가는 방향이었다면, 여기는 반대로 올라오는 방향입니다 — 소스를 읽다 막혔을 때 지금 열어 둔 파일의 이름을 짚어, 설명이 있는 곳으로 찾아 들어가는 표입니다. 프로그램을 이루는 파이썬 파일 43개가 하나도 빠짐없이 들어 있습니다.

앞의 세 절은 "문법에서 소스로" 내려가는 순서였습니다. 이 절은 반대 방향입니다 — **소스를 읽다 막혔을 때 그 파일에서 이 문서로 올라오는 표**입니다. `budget_app/` 아래 파이썬 파일 **43개 전부**가 들어 있고, 각 행은 "그 파일을 처음 읽을 때 걸릴 만한 표기"와 그 설명이 있는 절을 짝지어 둡니다. 어느 파일이 어떤 책임을 지는지는 [01 §2](./01-overview.md)의 파일 표에, 계층 사이의 의존 방향은 [04. 아키텍처](./04-architecture.md)에 있습니다.

**쓰는 법** — 소스를 읽다 막히면, 먼저 아래 표에서 **지금 열어 둔 파일의 이름**을 찾으세요. 그 행의 가운데 칸이 "그 파일에서 걸릴 만한 표기"이고, 오른쪽 칸이 그 설명이 있는 절입니다. 파일이 아니라 특정한 표기(`@dataclass`, `yield` 같은)가 걸린 것이라면 바로 아래의 「문법·API 이름으로 찾기」 표를 보시고, 두 표 어디에도 없으면 브라우저의 페이지 내 검색(Ctrl+F)이 가장 빠릅니다.

### 파일 이름으로 찾기

| 소스 파일 | 이 파일에서 만나는 항목 | 절 |
| --- | --- | --- |
| `__init__.py` | 일반 패키지 vs 네임스페이스 패키지, `__path__` 의 타입, `__version__` 이라는 관례 | §1-A |
| `__main__.py` | `python -m` 과 runpy, `__name__ == "__main__"` 이 성립하는 진짜 이유, `__package__` 와 상대 임포트, `sys.exit(main())` | §1-A, §3 |
| `config.py` | 모듈 상수 관례, 로거 이름과 점(`.`) 계층의 뿌리 | §2-B |
| `context.py` | `Path()` 로 한 번 더 감싸는 방어, `errno.ENOTDIR` 과 `OSError` 3인자 생성자(`exc.filename`) | §2-B |
| `decorators.py` | `*args`/`**kwargs`, 클로저와 `__closure__`, `functools.wraps`, `try/finally`, `%`-스타일 지연 포매팅, `time.perf_counter`, `Callable[..., Any]` | §1-A, §1-C, §2-A, §2-B |
| `errors.py` | `super().__init__()` 과 `args`, `ValidationError → ValueError` 상속 위치 | §1-B, §1-C |
| `cli/__init__.py` | 재수출 한 줄과 `__all__` 의 실제 효력 범위 | §1-A |
| `cli/app.py` | 상대 임포트와 `import as`, `from __future__ import annotations`, `X \| None`·`dict[str, Handler]` 타입 별칭, `parse_args`, argparse 의 `SystemExit(2)`, `os.dup2`/`os.devnull`, `BrokenPipeError`, `sys.exit` | §1-A, §1-C, §2-B, §3 |
| `cli/config.py` | `EXIT_*` 종료 코드 상수, `frozenset` 을 상수로 쓰는 이유, 환경변수 이름 | §1-A, §2-B, §3 |
| `cli/error_handler.py` | 데코레이터와 `wraps`, `except` 체인의 순서 규칙, 인자 없는 `raise`, `BaseException` vs `Exception`, `logger.exception`, `exc.filename or exc` | §1-C, §2-B |
| `cli/handlers.py` | 문자열 키 디스패치의 소비 지점, `store_false`+`dest` 로 뒤집힌 플래그를 읽는 자리 | §2-B |
| `cli/messages.py` | `str.format` 템플릿을 상수로 두는 이유, 포맷 스펙 미니 언어(`{:<7}`), `%`-스타일 로그 포맷 | §1-A, §2-B |
| `cli/output.py` | `logging.basicConfig(force=True)`, `lastResort` 핸들러, `os.environ` 과 `.strip().lower()`, stdout/stderr 버퍼링과 `flush` 순서 | §1-A, §2-B, §3 |
| `cli/parser.py` | `import as`, `argparse.SUPPRESS`, `add_subparsers`/`_SubParsersAction`, `set_defaults`, `type=` 콜러블과 `ArgumentTypeError`, `choices`/`store_true`/`store_false` | §1-A, §2-B |
| `cli/presenter.py` | `yield` 제너레이터와 `limit` 의 조기 종료, `str.format`, `collections.abc` 에서 가져오는 `Iterable`/`Iterator` | §1-A, §1-C |
| `cli/prompts.py` | 클로저로 검증기를 만들어 내보내기, `TypeVar` 로 표현한 "검증기의 반환 타입 = 함수의 반환 타입", `raise ... from exc`, `super().__init__()`, `", ".join(...)` | §1-A, §1-B, §1-C |
| `domain/__init__.py` | 일반 패키지 표식(내용 없음) | §1-A |
| `domain/config.py` | raw 문자열 `r"..."` 과 정규식 패턴 상수, `{:06d}` 포맷, `strftime` 지시자, 순서가 의미를 갖는 튜플 상수 | §1-A, §2-A, §2-B |
| `domain/entities.py` | `@dataclass`, `frozen=True`, `object.__setattr__`, `__post_init__`, `fields()`, `**{**a, **b}`, `@classmethod` 대체 생성자, 내장 제네릭과 `X \| Y` | §1-A, §1-B, §1-C |
| `domain/messages.py` | 문구 상수와 `str.format` 자리표시자 | §1-A |
| `domain/periods.py` | `calendar.monthrange` 의 두 원소, `strptime`/`strftime` 왕복, f-string `{last_day:02d}` | §1-A, §2-A |
| `domain/queries.py` | `field(init=False)` 와 `__post_init__` 의 상호작용, `**extra` 로 나머지 조건 전달, `@classmethod` | §1-A, §1-B |
| `domain/results.py` | `@property` 로 계산하는 파생값, frozen dataclass 와 property 의 이중 방어 | §1-B |
| `domain/specs.py` | `abc.ABC`/`@abstractmethod` 와 `__abstractmethods__`, 본문 `...`(Ellipsis), `__and__`/`__or__`/`__invert__`, `any`/`all` + 제너레이터 표현식, `{!r}` | §1-A, §1-B, §1-C |
| `domain/tx_id.py` | `@functools.total_ordering` + `@dataclass(frozen=True)` 중첩 순서, `__lt__` 와 `NotImplemented`, `frozen`+`eq` 가 만드는 `__hash__`, `re.compile` 과 `match` vs `search`, `{:06d}`, `@property` | §1-A, §1-B, §1-C, §2-A |
| `domain/validators.py` | `strip`/`lower`/`split`, `str(value or "")` 관용구, `raise ... from exc`, `[0-9]` 를 택한 이유, `strptime`→`strftime` 정규화, `isinstance(x, Iterable)`, `Any` | §1-A, §1-C, §2-A, §2-B |
| `services/__init__.py` | 일반 패키지 표식(내용 없음) | §1-A |
| `services/budgets.py` | `@measure_time` 과 `try/finally`, docstring 에만 남은 `startswith` 의 흔적 | §1-A, §1-C |
| `services/categories.py` | 정규화 시점과 `strip()` — 가드가 우회되는 사고의 기록 | §1-A |
| `services/config.py` | 순서가 의미를 갖는 튜플 상수(argparse `choices` 로 넘어감) | §2-B |
| `services/importexport.py` | 키워드 전용 인자 `*`, `field(default_factory=...)`, `with UnitOfWork()`, `raise ... from exc`, 제너레이터를 중간에 버릴 때 파일이 닫히는 경로 | §1-A, §1-B, §1-C |
| `services/maintenance.py` | `Path()` 재감싸기, 얇은 위임 계층 | §2-B |
| `services/messages.py` | `AppError` 의 message/hint 문구 상수 | §1-A |
| `services/transactions.py` | `@log_call`, 키워드 전용 `hint`, `None` 센티널 기본값, `stream_sorted` 의 `yield from` 과 정렬의 한계, 정렬 키 튜플이 `TransactionId.__lt__` 를 부르는 경로 | §1-A, §1-C, §2-A |
| `storage/__init__.py` | 일반 패키지 표식(내용 없음) | §1-A |
| `storage/backup.py` | f-string 으로 만드는 경로, `Path` 의 `/`·`glob`·`write_bytes`, `now` 주입과 `datetime.now()`, `strftime` 의 플랫폼 의존성 | §1-A, §2-A, §2-B, §3 |
| `storage/config.py` | `utf-8` vs `utf-8-sig` 비대칭, `surrogateescape`, `LINE_TERMINATOR`, `TMP_SUFFIX` | §2-A, §3 |
| `storage/csv_io.py` | `csv.DictReader` 의 지연 `fieldnames`, `DictWriter._dict_to_list`, `newline=""`, BOM 흡수, `yield from` 과 `with` 의 수명, 키워드 전용 인자 | §1-A, §1-C, §2-A, §3 |
| `storage/ids.py` | `set[TransactionId]` 가 요구하는 해시 가능성, `read_text` + `except OSError`("확인 후 사용" 대신 "그냥 하고 잡기") | §1-B, §2-B |
| `storage/jsonl.py` | `Generic[T]`/`TypeVar`, `iter_raw`/`stream` 제너레이터, `json.loads`/`dumps(ensure_ascii=False)`, 예외 튜플 `_LINE_ERRORS`, `with open`, `flush`+`fsync`, `os.replace`, `"rb"`+`seek(-1, SEEK_END)`, 이어 쓰기 `"a"`, `with_suffix`, `mkdir`/`touch`/`stat` | §1-C, §2-A, §2-B, §3 |
| `storage/messages.py` | 손상 줄 로그 문구 상수(`%`-스타일 자리표시자) | §2-B |
| `storage/repositories.py` | `super().__init__()` 과 MRO, 클래스 변수 vs 인스턴스 변수, `@staticmethod`, `nonlocal` 과 클로저, `any(...)` 의 단축 평가 | §1-B, §1-C |
| `storage/unit_of_work.py` | `__enter__`/`__exit__` 프로토콜과 `-> None` 의 의미, `TracebackType`, 인자 없는 `raise`, `unlink(missing_ok=True)`, `os.replace` 가 중간에 실패할 때 | §1-C, §2-B, §3 |

### 문법·API 이름으로 찾기

기호 → 알파벳 → 가나다 순입니다. 같은 항목이 두 절에 걸치면 **주 설명이 있는 절을 앞에** 적었습니다.

| 이름 | 절 |
| --- | --- |
| `*` (키워드 전용 인자, PEP 3102) | §1-A |
| `*args` / `**kwargs` | §1-A |
| `**{**a, **b}` (언패킹 일반화, PEP 448) | §1-A |
| `@` 데코레이터 문법의 전개 (PEP 318) | §1-C |
| `...` (Ellipsis)를 본문으로 쓰기 | §1-B |
| `\d` vs `[0-9]` | §2-A, §1-A |
| `"a"` (이어 쓰기 모드)와 찢어진 꼬리 | §3 |
| `"rb"` + `f.seek(-1, os.SEEK_END)` | §3 |
| `__all__` / `__version__` | §1-A |
| `__and__` / `__or__` / `__invert__` | §1-B |
| `__cause__` / `__context__` (`raise ... from`) | §1-C |
| `__closure__` / `nonlocal` (PEP 227, 3104) | §1-C |
| `__enter__` / `__exit__` | §1-C |
| `__format__` / `__str__` / `__repr__` | §1-A |
| `__hash__` (`frozen`+`eq` 조합) | §1-B |
| `__init__.py` (PEP 420) | §1-A |
| `__main__.py` / `python -m` / `runpy` (PEP 338, 366) | §1-A |
| `__post_init__` | §1-B |
| `abc.ABC` / `@abstractmethod` (PEP 3119) | §1-B |
| `add_subparsers` / `_SubParsersAction` | §2-B |
| `argparse.SUPPRESS` | §2-B |
| `ArgumentTypeError` / `type=` 콜러블 | §2-B |
| `BaseException` vs `Exception` | §1-C, §2-B, §3 |
| `BrokenPipeError` / `os.dup2` / `os.devnull` | §3, §1-C |
| `calendar.monthrange` | §2-A |
| `choices` / `store_true` / `store_false` / `dest` | §2-B |
| `collections.abc` vs `typing` | §1-C |
| `csv.DictReader` / `csv.DictWriter` (PEP 305) | §2-A |
| `@dataclass` (PEP 557) | §1-B |
| `datetime.now()` — naive vs aware, 주입 | §2-A |
| `errno.ENOTDIR` / `OSError` 3인자 생성자 | §2-B |
| `f.flush()` vs `os.fsync()` | §3 |
| `field(default_factory=...)` / 가변 기본값 금지 | §1-B |
| `fields()` | §1-B |
| `from __future__ import annotations` (PEP 563) | §1-C |
| `frozen=True` | §1-B |
| `frozenset` 을 상수로 | §2-B |
| `functools.total_ordering` | §1-B, §1-C |
| `functools.wraps` | §1-C |
| `Generic` / `TypeVar` (PEP 484) | §1-C |
| `json.dumps(..., ensure_ascii=False)` | §2-A |
| `json.loads` / `JSONDecodeError` / `TypeError` | §2-A |
| `logging.basicConfig(..., force=True)` | §2-B |
| `logging.getLogger(name)` — 캐시와 점 계층 | §2-B |
| `logger.exception(...)` vs `error(..., exc_info=True)` | §2-B |
| `match` / `search` / `fullmatch` | §2-A |
| `newline=""` / `newline="\n"` | §2-A, §3 |
| `NotImplemented` (PEP 207) | §1-B |
| `open()` — 3층 구조와 컨텍스트 매니저 | §3, §1-C |
| `os.environ` / `_Environ` | §2-B |
| `os.replace` vs `os.rename` | §3 |
| `parse_args` / `parse_known_args` | §2-B |
| `pathlib.Path` — `__new__` 와 `/` 연산자 (PEP 428, 519) | §2-B |
| `Path.stat().st_size` / `Path.touch()` | §3, §2-B |
| `Path.with_suffix` | §2-B |
| `@property` / `@classmethod` / `@staticmethod` | §1-B |
| `raise` (인자 없는 재전파) | §1-C |
| `raise ... from exc` (PEP 3134) | §1-C |
| `re.compile` 과 모듈 수준 캐시 | §2-A |
| `set_defaults` | §2-B |
| `str.format` / f-string / `%`-포맷 (PEP 3101, 498) | §1-A |
| `strftime` 의 플랫폼 의존성 | §2-A |
| `strptime` — 포맷을 정규식으로 바꾸는 파서 | §2-A |
| `super().__init__(...)` / MRO (PEP 3135) | §1-B |
| `surrogateescape` (PEP 383) | §3 |
| `sys.exit` / `SystemExit` | §1-A, §2-B, §3 |
| `time.perf_counter` vs `time.time` vs `monotonic` (PEP 418) | §2-A |
| `try/finally` | §1-C |
| `typing.Any` / `types.TracebackType` | §2-B |
| `utf-8-sig` vs `utf-8` (BOM) | §2-A |
| `with` — 컨텍스트 매니저 프로토콜 (PEP 343) | §1-C |
| `X \| Y` (PEP 604) / `list[str]` (PEP 585) | §1-C |
| `yield` (PEP 255) | §1-C |
| `yield from` (PEP 380) | §1-C |
| 기본값 인자의 평가 시점 | §1-A |
| 상대 임포트 `from . import x` (PEP 328) | §1-A |
| 예외 계층과 `except` 매칭 순서 (PEP 3151) | §1-C |
| 예외 튜플로 잡기 (`_LINE_ERRORS`) | §1-C, §2-A |
| 원자적 쓰기 3단계 | §3 |
| 제너레이터 표현식 vs 리스트 컴프리헨션 (PEP 289) | §1-C |
| 종료 코드와 셸(`$?` / `$LASTEXITCODE`) | §3 |
| 지연 포매팅(`logger.debug(msg, *args)`) | §2-B, §1-A |
| 클래스 변수 vs 인스턴스 변수 | §1-B |
| 포맷 스펙 미니 언어(`{:06d}`, `{:<7}`, `{!r}`) | §1-A |
| raw 문자열 `r"..."` | §1-A |

---

여기까지가 이 시리즈의 마지막 문서입니다. 이 문서는 처음부터 끝까지 "언어와 라이브러리가 실제로 무엇을 하는가"만 다뤘습니다. 같은 코드를 **왜 그렇게 배치했는가**로 다시 보고 싶으면 [04. 아키텍처](./04-architecture.md)와 [10. 고급 설계 주제](./10-advanced-design.md)로, 짧은 문답 형태로 확인하고 싶으면 [11. 설계 FAQ & 용어집](./11-faq-and-glossary.md)로 돌아가시면 됩니다.

**다음 문서**: [00. 목차](./00-INDEX.md) — 시리즈 전체 지도로 돌아갑니다.
