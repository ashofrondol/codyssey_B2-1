# 06. 횡단 관심사와 예외 처리 — decorators / error_handler

## 쉬운 말로 먼저

이 프로그램에는 어느 기능에나 똑같이 따라붙는 잔일이 몇 가지 있습니다. 언제 불렸는지 적어 두기, 얼마나 걸렸는지 재기, 일이 잘못됐을 때 사용자에게 알리기입니다. 이런 잔일을 기능마다 하나하나 적어 넣으면 정작 그 기능이 하려던 일이 잔일에 묻히고, 규칙이 바뀔 때마다 열 몇 군데를 똑같이 고쳐야 합니다. 그래서 이 셋을 따로 떼어, 기능 위에 한 줄만 얹으면 자동으로 따라붙는 장치로 만들었습니다. 문서의 앞쪽 절반이 그 장치 이야기입니다.

뒤쪽 절반은 "일이 잘못됐을 때" 쪽입니다. 파일이 없을 수도, 사용자가 이상한 값을 넣었을 수도, 프로그램 자체에 잘못이 있을 수도 있는데 — 원인이 다르면 건네야 할 말도 다르고, 프로그램이 끝나며 남기는 결과 보고도 달라야 합니다. 이 문서는 그 구분을 어떤 기준으로 지었고 왜 하필 지금의 순서로 적혀 있는지를 다룹니다.

**이 문서에 자주 나오는 말**

| 말 | 쉬운 뜻 |
| --- | --- |
| 데코레이터 | 원래 함수의 코드는 한 글자도 고치지 않은 채, 그 앞뒤에 다른 처리를 끼워 넣는 장치. 소스를 안 건드릴 뿐 동작까지 그대로는 아니어서, 필요하면 결과나 예외까지 바꿔치기합니다(§5 의 `@handle_errors` 가 예외를 종료 코드로 바꿉니다) |
| 횡단 관심사 | 하는 일은 서로 달라도 어디에나 똑같이 필요한 부대 처리(기록 남기기, 시간 재기, 오류 알리기) |
| 예외 | 하던 일을 그 자리에서 멈추고 사정을 위로 올려 보내는 신고. 잘못됐을 때가 대부분이지만, `Ctrl+C` 처럼 "그만하자"는 신호도 같은 길로 올라옵니다(§5.2 의 첫 부류) |
| except 절 | 올라온 신고를 받는 창구. 어떤 종류의 신고를 받을지가 창구마다 정해져 있습니다 |
| 종료 코드 | 프로그램이 끝나며 말 대신 숫자 하나로 남기는 결과 보고. 0 이면 "잘 끝났다"입니다 |
| 트레이스백 | 문제가 어디를 거쳐 어디서 터졌는지 적힌 경로 기록. 개발자가 원인을 찾을 때 봅니다 |
| 상속 | 어떤 종류가 다른 종류를 더 좁게 나눈 것. "파일 없음"은 "입출력 문제"의 한 갈래입니다 |
| stderr | 결과가 아니라 사정을 알리는 별도 출구. 계산 결과는 stdout 이라는 다른 출구로 나갑니다 |

**바쁘면 여기만**

- **§2 횡단 관심사** — 왜 이 세 가지를 기능 본문 밖으로 빼냈는지, 문서 전체의 출발점입니다.
- **§5.2 except 체인** — 오류를 네 부류로 나눈 기준과 "순서가 곧 정책"인 이유가 여기 있습니다.
- **§7 종료 코드 표** — 프로그램이 남기는 숫자 여덟 개의 뜻이 한 표에 정리돼 있습니다.

---

`@log_call`, `@measure_time`, `@handle_errors` 세 데코레이터가 무엇을 하고, **왜 두 파일로 나뉘어 있으며**, 예외가 어떻게 사용자 메시지와 종료 코드로 바뀌는지를 완전히 해설합니다.

> **난이도**: 🟡 중급
>
> **먼저 읽으면 좋은 문서**: [03. 파이썬 중·고급 기법](./03-python-advanced.md) §4(데코레이터)·§5(예외), [05. 설정·검증·모델](./05-config-and-models.md) §1(errors.py)
>
> **함께 보면 좋은 문서**: [12. 문법의 출처와 표준 라이브러리 내부](./12-syntax-and-stdlib.md) — 이 문서 곳곳의 🔎/⚙️ 노트가 가리키는 상세 해설이 그곳에 있습니다. 특히 §1-C(데코레이터·클로저·예외·`try/finally`)와 §2-B(`logging`·`functools`·`errno`)가 짝입니다.

---

## 1. 이 문서에서 배우는 것

1. **횡단 관심사(cross-cutting concern)** 란 무엇이고 왜 데코레이터로 분리하는가
2. 데코레이터 셋이 **두 파일로 나뉜 이유** — 관측 vs 표현
3. `@handle_errors` 의 except 체인 11단과 **순서가 곧 정책**인 이유
4. 예외 하나가 발생해서 셸 종료 코드가 되기까지의 전체 경로

---

## 2. 횡단 관심사 — 데코레이터로 분리하는 것들

**개념.** "어느 함수에나 붙을 수 있고, 그 함수의 본래 목적과는 무관한" 처리를 횡단 관심사라고 합니다. 로깅, 시간 측정, 인증, 트랜잭션, 예외 변환이 대표적입니다.

> **💡 쉽게 말하면** — 부서마다 하는 일은 다르지만, 어느 서류에나 접수 도장은 찍힙니다.
> 도장 찍는 절차를 부서별 업무 설명서마다 적어 두면 같은 문장이 열 몇 번 복사되고,
> 도장 규정이 바뀌는 날 열 몇 곳을 똑같이 고쳐야 합니다. 접수 창구를 하나 두고 서류가
> 거기를 지나게 하면, 업무 설명서에는 본래 일만 남습니다. 데코레이터가 그 창구입니다.
> 다만 이 비유는 시점에서 깨집니다 — 창구는 서류가 들어올 때 한 번이지만, 데코레이터는
> 들어갈 때와 나올 때 양쪽에 끼어들 수 있습니다(§3 의 `call`/`done` 한 쌍이 그 예입니다).

이런 처리를 각 함수 본문에 넣으면 이렇게 됩니다.

```python
# 일반론 예시 — 횡단 관심사가 본문에 섞인 코드
def add(self, date, type_, category, amount, memo="", tags=None):
    logger.debug("call add")                 # ← 관심사 1
    start = time.perf_counter()              # ← 관심사 2
    try:
        if not self.cats.exists(category):   # ← 진짜 로직
            raise AppError(...)              #
        tx = Transaction(...)                #
        self.txs.append(tx)                  #
        return tx                            #
    except Exception as e:                   # ← 관심사 3
        print(f"[오류] {e}")                  #
        return 1                             #
    finally:
        logger.debug("took %.2fms", ...)     # ← 관심사 2
```

진짜 로직 5줄이 부대 처리 8줄에 묻힙니다. 그리고 이 8줄이 **모든 함수에 복사**됩니다. 데코레이터로 분리하면 본문은 로직만 남습니다.

### 2.1 이 프로젝트의 데코레이터 적용 지도

| 데코레이터 | 정의 위치 | 붙는 곳 | 목적 |
| --- | --- | --- | --- |
| `@log_call` | decorators.py:37-47 | `TransactionService.add`(transactions.py:27) / `update`(52) / `delete`(72) | 호출/반환 DEBUG 로그 |
| `@measure_time` | decorators.py:50-66 | `BudgetService.monthly_summary`(budgets.py:30) | 실행 시간 DEBUG 로그 |
| `@handle_errors` | **cli/error_handler.py:20-121** | **`cli/app.py:61` 의 `_dispatch` 단 한 곳** | 예외 → 메시지 + 종료 코드 |

적용 현황을 소스에서 확인하려면:

```bash
grep -rn "@log_call\|@measure_time\|@handle_errors" budget_app/
```

**`@handle_errors` 가 한 곳뿐인 것이 중요합니다.** 이전에는 CLI 핸들러 13개에 각각 붙어 있었지만, 지금은 `_dispatch` 하나에만 붙습니다. 이유는 §5 와 `cli/app.py:63-77` 의 docstring 에 있습니다 — 컨텍스트 조립(`AppContext(...)`, `prepare()`)이 데코레이터 **밖**에 있으면 `--data-dir` 오타 하나로 원시 트레이스백이 새어 나갔기 때문입니다. 방패는 파일을 여는 코드까지 감싸야 방패입니다.

> **🔎 문법의 출처** — `@데코레이터` 표기는 PEP 318 로 파이썬 2.4 에 들어왔습니다.
> `@handle_errors` 뒤에 `def _dispatch(...)` 를 쓰면 파이썬은 함수를 정의한 뒤
> `_dispatch = handle_errors(_dispatch)` 를 실행합니다. 즉 데코레이터는 **문법 설탕**(없어도
> 할 수 있는 일을 짧게 쓰게 해 주는 표기)이고,
> 새로운 능력이 아니라 "정의 직후 이름에 재대입"의 짧은 표기입니다.
> 클래스에 붙이는 `@dataclass` 형태는 PEP 3129 로 파이썬 3.0 에 추가된 별개 문법이며,
> 이 소스에서는 `domain/entities.py` 등이 씁니다. → [12 §1-A](./12-syntax-and-stdlib.md)

### 2.2 왜 두 파일인가 — 리팩터의 핵심 결정

리팩터 전에는 셋이 `decorators.py` 한 파일에 있었습니다. 그런데 **의존하는 대상이 다릅니다.**

| 데코레이터 | 필요한 것 | 성격 |
|---|---|---|
| `log_call` / `measure_time` | `logging`, 문자열 템플릿 | 어느 계층에서나 쓸 수 있어야 함 |
| `handle_errors` | `output`(화면 채널), 종료 코드 | **CLI 만의 표현 정책** |

한 파일에 두면 `decorators` 가 `output` 을 import 해야 하고, 그 의존이 **서비스 계층까지 전파**됩니다.

```
[리팩터 전]
services.py ──@log_call 쓰려고 import──▶ decorators.py ──import──▶ output.py
   (L4 서비스)                                                      (L5 프레젠테이션)
   └──────────── 아래 계층이 위 계층에 전이 의존 (역류) ────────────────┘
```

budget_app/decorators.py:1-16

```python
"""횡단 관심사 데코레이터 — 관측(로그/실행시간)만 담당한다.

## 왜 ``handle_errors`` 가 여기 없나

예외를 사용자 메시지와 종료 코드로 바꾸는 일은 **CLI 의 표현 정책**이다. 그것이
이 파일에 함께 있으면 ``decorators`` 가 출력 모듈(``output``)을 import 해야 하고,
서비스 계층은 ``@log_call`` 하나를 쓰려다 **화면 출력 모듈까지 끌고 들어오게** 된다:

    services → decorators → output      ← 서비스가 프레젠테이션에 전이 의존

그래서 ``handle_errors`` 는 ``error_handler.py`` (CLI 계층)로 옮겼다. 지금 이 모듈이
아는 것은 ``logging`` 과 문자열 템플릿뿐이고, 어느 계층에서 써도 아래로만 의존한다.

남은 둘은 진짜 횡단 관심사다. "무엇을 계산하는가"와 무관하게 "언제 불렸고 얼마나
걸렸는가"를 기록하는 일이라, 함수 본문에 섞이면 본래 로직을 가린다.
"""
```

**과제 방어 포인트**: "데코레이터로 분리한 공통 기능이 무엇이며 왜 분리가 필요했나?"에는 두 층으로 답하세요.

1. **함수 본문에서 분리한 이유** — 로직이 부대 처리에 묻히고, 같은 코드가 모든 함수에 복사됩니다.
2. **데코레이터끼리도 분리한 이유** — 관측은 전 계층 공용, 표현은 CLI 전용이라 의존 대상이 다릅니다. 한 파일에 두면 계층 역류가 생깁니다.

---

## 3. `log_call` — 호출/반환 로그

함수가 언제 불렸고 언제 끝났는지를 기록으로 남기는 데코레이터입니다. 본래 하던 일에는 손대지 않고, 그 앞뒤에 로그 한 줄씩만 더합니다. 열한 줄짜리 짧은 코드지만 파이썬 관용구가 셋이나 들어 있어, 하나씩 뜯어볼 값어치가 있습니다.

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

**세 가지 관용구가 들어 있습니다.**

1. `@functools.wraps(func)` — 원본의 `__name__`/`__doc__` 등을 wrapper 로 복사합니다. 이게 없으면 `TransactionService.delete` 의 정체가 밖에서 볼 때 `<function log_call.<locals>.wrapper>` 로 바뀌어, `help()`·트레이스백·`inspect` 가 전부 원본을 놓칩니다.
2. `*args, **kwargs` — 어떤 시그니처의 함수든 그대로 통과시킵니다.
3. `logger.debug(템플릿, 인자)` — %-지연 포맷팅(문장을 미리 완성해 두지 않고, 정말 출력할 때가 되어서야 만드는 방식). DEBUG 가 꺼져 있으면 문자열을 아예 만들지 않습니다.

> **💡 쉽게 말하면** — 선물을 포장하면 겉만 보고는 안에 뭐가 들었는지 모릅니다.
> `functools.wraps` 는 원래 상자에 붙어 있던 이름표를 포장지 겉에 그대로 옮겨 붙이는
> 일입니다. 그래서 포장한 뒤에도 "이건 `delete` 다"라고 읽힙니다.
> 다만 이 비유는 정체에서 깨집니다 — 이름표를 옮겨도 포장지는 여전히 포장지입니다.
> `TransactionService.delete` 로 꺼내지는 것은 원본이 아니라 `wrapper` 이고, 원본은
> `__wrapped__` 라는 별도 자리에 남아 있습니다(바로 아래에서 확인합니다).

> **⚙️ 내부 동작 — `functools.wraps`** — 이것 자체가 데코레이터 팩토리입니다.
> `wraps(func)` 는 `partial(update_wrapper, wrapped=func)` 를 돌려주고, 그것이
> `wrapper` 에 적용되면서 `functools.WRAPPER_ASSIGNMENTS` 에 든 속성들을 **대입**하고
> `WRAPPER_UPDATES`(`('__dict__',)`)에 든 것은 `update()` 로 **병합**한 뒤,
> 마지막으로 `wrapper.__wrapped__ = func` 를 심어 원본으로 되돌아갈 길을 남깁니다.
> → [12 §2-B](./12-syntax-and-stdlib.md)

로컬 CPython 3.13.1 에서 직접 확인한 값입니다.

```python
>>> import functools
>>> functools.WRAPPER_ASSIGNMENTS
('__module__', '__name__', '__qualname__', '__doc__', '__annotations__', '__type_params__')
>>> functools.WRAPPER_UPDATES
('__dict__',)
```

`__type_params__` 는 제네릭 타입 파라미터 문법이 생기면서 나중에 추가된 항목이라, 프로젝트 하한인 3.10 에서는 앞의 다섯 개만 있습니다. 어느 쪽이든 **`__name__` 이 복사된다**는 점이 핵심입니다.

실제로 데코레이터가 붙은 함수를 꺼내 보면 이렇습니다.

```python
>>> from budget_app.services.transactions import TransactionService
>>> d = TransactionService.delete       # @log_call 이 붙은 wrapper
>>> d.__name__, d.__qualname__
('delete', 'TransactionService.delete')
>>> d.__wrapped__                        # wraps 가 남겨 준 원본
<function TransactionService.delete at 0x...>
```

여기서 `d.__name__` 이 `'wrapper'` 가 아니라 `'delete'` 인 것이 요점입니다. 다만 `log_call` 의 로그 문구는 `wrapper.__name__` 이 아니라 **클로저에 잡힌 `func.__name__`** 을 쓰므로 — 클로저란 바깥 함수가 끝난 뒤에도 그 안의 변수를 계속 붙잡고 있는 상태를 말합니다 — `wraps` 가 없어도 로그 자체는 `call delete` 로 정확히 찍힙니다. `wraps` 가 실제로 구해 주는 것은 `help()`, 트레이스백, `inspect`, 그리고 "이 함수 이름이 뭐냐"고 묻는 다른 도구들입니다.

> **⚙️ 내부 동작 — 클로저** — `wrapper` 는 자기 지역변수가 아닌 `func` 를 쓰므로
> 파이썬이 이를 **자유변수**로 분류하고, 바깥 함수의 `func` 를 셀(cell) 객체에 담아
> `wrapper.__closure__` 에 매답니다. 그래서 `log_call` 이 반환된 뒤에도 `func` 가
> 살아 있습니다. → [12 §1-C](./12-syntax-and-stdlib.md)

```python
>>> d.__code__.co_freevars                       # 자유변수 목록
('func',)
>>> [c.cell_contents for c in d.__closure__]     # 셀 안에 붙잡힌 실제 객체
[<function TransactionService.delete at 0x...>]
```

> **🔎 문법의 출처 — `*args, **kwargs`** — 함수 정의에서 `*이름` 은 남은 위치 인자를
> **튜플**로, `**이름` 은 남은 키워드 인자를 **dict** 로 묶습니다(데코레이터보다 훨씬
> 오래된 초창기 문법). 호출부의 `func(*args, **kwargs)` 는 반대로 **푸는(unpack)** 동작입니다.
> 데코레이터가 어떤 시그니처든 통과시킬 수 있는 이유가 이 한 쌍이고, 동시에 **정적으로
> 시그니처를 알 수 없는 이유**이기도 합니다. 그래서 타입 힌트가
> `Callable[..., Any]` — `...`(Ellipsis 객체)가 "인자 목록은 검사하지 않음"을 뜻합니다.
> → [12 §2-B](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `logger.debug(템플릿, 인자)`** — `Logger.debug` 는 먼저
> `isEnabledFor(DEBUG)` 로 레벨을 확인하고, 통과할 때만 `LogRecord` 를 만들어 인자를
> `record.args` 에 **그대로 보관**합니다. `템플릿 % args` 가 실행되는 시점은 포매터가
> `record.getMessage()` 를 부를 때, 즉 실제로 출력이 확정된 뒤입니다. 그래서 DEBUG 가
> 꺼져 있으면 문자열 조립 비용이 0 입니다 — f-string 으로 쓰면 이 이점이 사라집니다.
> → [12 §2-B](./12-syntax-and-stdlib.md)

**"call" 과 "done" 이 짝인 이유**는 예외 감지입니다. `add` 가 중간에 예외를 던지면 `call add` 만 찍히고 `done add` 는 안 찍힙니다. 로그만 보고도 "어디서 끊겼는지"를 알 수 있습니다.

실제 동작:

```bash
$ printf '2024-01-15\nexpense\nfood\n15000\n\n\n' | python -m budget_app add --debug
[DEBUG] 2026-08-06 10:30:00 budget_app:42 call add
[DEBUG] 2026-08-06 10:30:00 budget_app:44 done add
[저장 완료] id=TX-000001
```

로그가 stderr 로 나가므로 `2>/dev/null` 로 걸러낼 수 있습니다.

앞의 `budget_app` 은 `%(name)s`(= `config.LOGGER_NAME`)이고, `42`/`44` 는 `%(lineno)d` 입니다. **`logger.debug` 를 호출한 줄 번호**이지 `add` 의 줄 번호가 아닙니다 — decorators.py:42 와 :44 가 그 두 자리입니다. 로그의 출처가 데코레이터라는 사실이 포맷에 그대로 드러납니다(포맷 정의는 `cli/messages.py:17` 의 `LOG_FORMAT_DEBUG`).

---

## 4. `measure_time` — 실패해도 시간은 기록한다

함수가 몇 밀리초 걸렸는지를 재서 로그로 남기는 데코레이터입니다. 여기서 눈여겨볼 것은 두 가지입니다. 하나는 **중간에 실패해도 시간이 찍힌다**는 점이고, 다른 하나는 시간을 재는 데 쓰는 시계를 **일부러 골랐다**는 점입니다.

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

**`try/finally` 가 핵심입니다.** `finally` 는 `try` 에서 return 을 하든 예외가 나든 반드시 실행됩니다. docstring 이 밝히듯, 실패한 호출의 소요 시간을 알아야 "느려서 문제"와 "즉시 터짐"을 구분할 수 있습니다.

> **💡 쉽게 말하면** — 건물에 출구가 하나뿐이라고 해 봅시다. 일을 잘 마치고 나가든
> 사고가 나서 뛰쳐나가든 그 문을 지나야 하고, 문 옆에 시계가 있으니 어느 쪽이든
> 나간 시각이 적힙니다. `finally` 가 그 출구입니다.
> 다만 이 비유는 손을 대는 순간 깨집니다 — 출구에서 들고 나가던 짐을 바꿔치기하면
> 결과가 달라지듯, `finally` 안에 `return` 이나 `raise` 를 쓰면 원래 나가던 값이나
> 예외가 삼켜집니다. 그래서 이 코드는 출구에서 기록만 하고 아무것도 건드리지 않습니다.

> **🔎 문법의 출처 — `return` 과 `finally`** — `try` 안의 `return func(...)` 는
> ① 오른쪽 식을 먼저 **평가해 반환값을 확정**하고, ② `finally` 블록을 실행한 뒤,
> ③ 그제야 프레임을 빠져나갑니다. 그래서 `finally` 안에서 `elapsed` 를 계산해도
> 이미 확정된 반환값은 바뀌지 않습니다. 반대로 `finally` 안에 `return` 이나 `raise`
> 를 쓰면 **원래 나가던 값/예외를 삼켜 버리므로** 이 코드는 로그만 남깁니다.
> → [12 §1-C](./12-syntax-and-stdlib.md)

**`time.perf_counter()` 를 쓰는 이유**는 `time.time()` 과 달리 **단조 증가**(값이 뒤로 가는 일 없이 늘 앞으로만 감)**가 보장**되기 때문입니다. NTP 동기화로 시스템 시각이 뒤로 가면 `time.time()` 차이는 음수가 될 수 있습니다.

> **💡 쉽게 말하면** — 벽시계와 스톱워치의 차이입니다. 벽시계는 "지금 몇 시"를 알려
> 주지만 누가 바늘을 맞추면 시각이 뒤로 갈 수 있고, 그러면 그 사이에 잰 소요 시간이
> 음수로 나올 수도 있습니다 — 되돌린 폭이 실제로 걸린 시간보다 클 때 그렇습니다.
> 스톱워치는 지금이 몇 시인지는 모르는 대신 누르고 나면 뒤로 가지 않습니다.
> 소요 시간을 재는 데는 스톱워치가 맞습니다.
> 다만 이 비유는 기준점에서 깨집니다 — 스톱워치는 0 에서 시작하지만 `perf_counter()`
> 는 시작값이 아예 정의돼 있지 않아, 값 하나만 봐서는 아무 뜻도 없고 오직 두 값의
> 차이만 뜻이 있습니다.

> **⚙️ 내부 동작 — 두 시계의 차이** — `time.time()` 은 **벽시계**(1970-01-01 기준
> 유닉스 시각)라 값 자체에 의미가 있지만 시스템이 조정하면 뒤로 갈 수 있습니다.
> `time.perf_counter()` 는 **기준점이 정의되지 않은** 고해상도 카운터라 절대값은
> 무의미하고 오직 **차이만** 뜻이 있으며, 대신 단조성이 보장됩니다. 파이썬이
> 이 성질을 실행 시점에 알려 줍니다. → [12 §2-A](./12-syntax-and-stdlib.md)

```python
>>> import time
>>> time.get_clock_info("perf_counter")   # Windows / CPython 3.13.1
namespace(implementation='QueryPerformanceCounter()', monotonic=True, adjustable=False, resolution=1e-07)
>>> time.get_clock_info("time")
namespace(implementation='GetSystemTimePreciseAsFileTime()', monotonic=False, adjustable=True, resolution=1e-07)
```

`monotonic=True`/`adjustable=False` 가 곧 "뒤로 가지 않고 관리자가 바꿀 수도 없다"는 보장입니다. 리눅스에서는 `implementation` 이 `clock_gettime(CLOCK_MONOTONIC)` 으로 바뀌지만 두 플래그의 값은 같습니다.

사용처는 요약 계산 하나입니다.

budget_app/services/budgets.py:30-31

```python
    @measure_time
    def monthly_summary(self, month: str, top_n: int = config.DEFAULT_TOP_N) -> MonthlySummary:
```

거래 파일 전체를 훑는 유일한 집계 연산이라, 데이터가 커졌을 때 병목이 될 후보이기 때문입니다.

```bash
$ python -m budget_app summary --month 2024-01 --debug
[DEBUG] ... budget_app:64 monthly_summary took 1.83ms
총 수입: 3000000원
...
```

---

## 5. `handle_errors` — 예외 → 종료 코드 변환기 (완전 해설)

세 데코레이터 중 가장 길고, 프로그램 전체에서 단 한 곳에만 붙습니다. 하는 일은 한 문장으로 요약됩니다 — 아래에서 올라온 신고를 종류별로 받아, 사용자에게 건넬 한두 줄과 셸에 남길 숫자로 바꿉니다. 아래에서 반환값 규약(§5.1), 창구를 세우는 순서(§5.2), 부류별 처리(§5.3~§5.6) 순으로 봅니다.

### 5.1 시그니처와 반환값 규약

budget_app/cli/error_handler.py:20-21 / 45-54

```python
def handle_errors(func: Callable[..., int]) -> Callable[..., int]:
    """CLI 핸들러 공용 — 예외를 잡아 [오류]/[힌트] 를 **stderr** 로 내보내고 종료 코드를 반환한다.
    ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> int:
        try:
            result = func(*args, **kwargs)
            # `func(...) or EXIT_OK` 로 쓰면 0/""/[]/False 같은 falsy 반환값까지
            # 전부 EXIT_OK 로 바뀐다. 규약은 "None 이면 EXIT_OK" 이므로 None 만
            # 정확히 검사한다 (EXIT_OK 가 0 이 아니게 되어도 의미가 흔들리지 않는다).
            return config.EXIT_OK if result is None else result
```

`Callable[..., int]` 는 "인자는 뭐든, 반환은 int" 라는 계약입니다.

**`or` 대신 `is None` 을 쓰는 이유**가 주석에 있습니다. 만약 `return func(...) or config.EXIT_OK` 라고 쓰면:

```python
# 핸들러가 EXIT_NO_CATEGORY(5)를 반환 → 5 는 truthy → 5 그대로 ✅
# 핸들러가 EXIT_OK(0)를 반환        → 0 은 falsy  → EXIT_OK 로 대체 (우연히 맞음)
# 만약 EXIT_OK 가 0 이 아니게 바뀐다면? → 0 을 반환하려던 의도가 뭉개짐 ❌
```

`is None` 은 **의도를 정확히** 표현합니다 — "아무것도 반환하지 않았으면 성공".

> **🔎 문법의 출처 — `A if 조건 else B`** — 조건식(conditional expression)은 PEP 308 로
> 파이썬 2.5 에 들어왔습니다. `if` **문**과 달리 **값을 만드는 식**이라 `return` 뒤에
> 바로 올 수 있습니다. 읽는 순서가 가운데(`조건`)부터라 낯설지만,
> `config.EXIT_OK if result is None else result` 는 "result 가 None 이면 EXIT_OK,
> 아니면 result" 그대로입니다. → [12 §1-A](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `is None` 과 `== None` 의 차이** — `is` 는 **객체 동일성**(주소 비교)
> 이라 오버로딩이 불가능합니다. `None` 은 인터프리터에 단 하나만 존재하는 싱글턴이므로
> `x is None` 은 항상 정확하고, `__eq__` 를 정의한 객체가 끼어들어 결과를 바꿀 수
> 없습니다. `== None` 은 상대 객체의 `__eq__` 를 부르므로 그 보장이 없습니다.
> → [12 §1-B](./12-syntax-and-stdlib.md)

### 5.2 except 체인 — 네 부류로 묶인 11단

`handle_errors` 의 docstring 이 순서 정책을 스스로 설명합니다.

budget_app/cli/error_handler.py:23-42

```python
    여기서 잡는 예외는 성격이 네 부류로 갈리고, except 절도 그 순서대로 묶여 있다.
    파이썬은 '먼저 일치하는 절'을 실행하므로 except 순서가 곧 정책이고, 그래서
    같은 부류끼리 붙여 두어야 "왜 이 순서인가"가 코드에서 읽힌다.

    1. **종료 신호** — 오류가 아니다. 사용자나 하류 프로세스가 "그만"이라고 알린 것.
       ``BrokenPipeError`` / ``KeyboardInterrupt``
    2. **입력 오류** — 사용자가 값을 고치면 해결된다.
       ``ValidationError`` / ``AppError``
    3. **환경 상태** — 프로그램 밖(파일·권한·디스크·인코딩)의 상태 문제.
       ``FileNotFoundError`` / ``IsADirectoryError`` / ``NotADirectoryError`` /
       ``PermissionError`` / ``UnicodeDecodeError`` / ``OSError``
    4. **최후 방어선** — 위 어디에도 속하지 않는 버그.
       ``Exception`` — 사용자에겐 스택트레이스를 감추고 로그에만 남긴다.

    부류를 나눠도 지켜야 하는 상속 제약이 둘 있고, 지금 순서가 둘 다 만족한다:

    - ``BrokenPipeError`` 는 ``OSError`` 의 자식이라 (3) 의 ``OSError`` 보다 위여야 한다.
      → (1) 이 맨 앞이므로 자동으로 만족한다.
    - (3) 안에서도 ``FileNotFoundError``·``IsADirectoryError``·``PermissionError`` 는
      ``OSError`` 의 자식이므로 마지막 ``OSError`` 보다 위에 둔다.
```

> **💡 쉽게 말하면** — 민원실에 창구를 여럿 두었는데, 들어온 사람이 앞에서부터 훑어
> 처음 "여기 해당됩니다" 하는 창구로 들어간다고 해 봅시다. 이때 "무엇이든 받습니다"
> 창구를 맨 앞에 세우면 뒤쪽의 전문 창구에는 영원히 아무도 오지 않습니다. 좁은 창구가
> 앞, 넓은 창구가 뒤여야 합니다. except 절을 세우는 순서가 정확히 이것입니다.
> 단, 넓고 좁음이 갈리는 것은 한쪽이 다른 쪽의 갈래일 때뿐입니다 — 서로 남남인 창구끼리는
> 순서를 바꿔도 결과가 같습니다(아래 표의 "상속 제약"과 "의미적 분류"가 그 둘입니다).
> 다만 이 비유는 고르는 주체에서 깨집니다 — 실제 민원인은 자기에게 맞는 창구를 보고
> 갈 수 있지만, 파이썬은 위에서부터 처음 맞는 창구에 무조건 넣습니다. "가장 알맞은
> 창구"를 대신 찾아 주지 않습니다.

**이 docstring 이 왜 중요한가.** except 순서에는 두 종류의 제약이 섞여 있습니다.

| 제약 | 어기면 | 예 |
|---|---|---|
| **상속 제약** (필수) | 아래 절이 죽은 코드가 됨 | `OSError` 를 `FileNotFoundError` 위에 두면 안 됨 |
| **의미적 분류** (선택) | 읽기 어려워질 뿐 | "종료 신호"를 맨 앞에 모은 것 |

둘을 구분해 적어 두면, 나중에 절을 추가할 사람이 **무엇을 어겨선 안 되고 무엇이 취향인지** 알 수 있습니다.

> **⚙️ 내부 동작 — 왜 "순서가 곧 정책"인가** — `try` 본문에서 예외가 나면 인터프리터는
> except 절을 **위에서 아래로 한 번씩** 훑으며, 각 절의 예외 클래스에 대해
> `issubclass(발생한_예외의_타입, 절의_타입)` 에 해당하는 판정을 합니다. 그리고
> **처음 참이 되는 절 하나만** 실행하고 나머지는 건너뜁니다 — "가장 구체적인 절"을
> 골라 주는 것이 아닙니다. 그래서 `OSError` 를 `FileNotFoundError` 위에 두면 아래 절이
> 영원히 도달 불가능한 죽은 코드가 됩니다. 검증법은 §6 에 있습니다.
> → [12 §1-C](./12-syntax-and-stdlib.md)

지금 이 체인은 except 절이 모두 **11개**입니다(`grep -c "^        except" budget_app/cli/error_handler.py` → 11). 부류별로 2 + 2 + 6 + 1 입니다.

### 5.3 부류 1 — 종료 신호 (오류가 아님)

budget_app/cli/error_handler.py:56-63

```python
        # ---------- (1) 종료 신호 — 오류가 아님 ----------
        except BrokenPipeError:
            # 하류 파이프(`list | head`)가 먼저 닫힘. 여기서 출력하면 또 깨지므로
            # 최상위(main)로 넘겨 조용히 처리하게 한다.
            raise
        except KeyboardInterrupt:
            output.err(messages.MSG_INTERRUPTED)
            return config.EXIT_INTERRUPT
```

**`BrokenPipeError` 는 유일하게 "처리하지 않는" 절입니다.** 인자 없는 `raise` 는 "지금 잡은 예외를 그대로 재전파"입니다.

> **💡 쉽게 말하면** — 상대가 전화를 먼저 끊었는데 이쪽은 아직 할 말이 남은 상황입니다.
> 여기서 "여보세요? 안 들리세요?"라고 더 말해 봐야 같은 일이 한 번 더 벌어질 뿐입니다.
> 그래서 이 절만은 아무 말도 보태지 않고 상황을 그대로 위로 넘깁니다. 할 일은 말을
> 잇는 게 아니라 수화기를 내려놓는 것이고, 그 일은 맨 위의 `main()` 이 합니다.
> 다만 이 비유는 뒷정리에서 깨집니다 — 전화는 끊으면 그만이지만, 프로그램은 끝나는
> 순간 아직 내보내지 못한 출력을 한 번 더 밀어내려 하므로 그 몫까지 막아 줘야 합니다.
> 아래 `_silence_broken_pipe()` 가 하는 일이 그것입니다.

> **🔎 문법의 출처 — 인자 없는 `raise`** — 이 형태는 인터프리터가 들고 있는
> **현재 처리 중인 예외**(`sys.exc_info()` 가 돌려주는 그 3-튜플)를 다시 던집니다.
> `raise BrokenPipeError()` 라고 새로 만들어 던지는 것과 결정적으로 다른 점은
> **원래의 트레이스백이 그대로 이어진다**는 것입니다 — 어디서 처음 터졌는지가
> 보존됩니다. 처리 중인 예외가 없는 자리에서 쓰면 `RuntimeError: No active exception
> to re-raise` 가 납니다. → [12 §1-C](./12-syntax-and-stdlib.md)

```python
>>> import sys
>>> try:
...     1 / 0
... except ZeroDivisionError:
...     print(sys.exc_info()[0].__name__)   # 인자 없는 raise 가 다시 던질 대상
...
ZeroDivisionError
>>> raise                                    # 처리 중인 예외가 없는 자리에서
Traceback (most recent call last):
  ...
RuntimeError: No active exception to reraise
```

왜 여기서 처리하지 않는가 — `list | head`(가운데 `|` 는 앞 명령의 출력을 뒤 명령의 입력으로 잇는 파이프입니다)에서 `head` 가 먼저 닫히면 stdout 이 깨진 상태입니다. 이 상황에서 `output.err(...)` 를 부르면 `err()` 안의 `sys.stdout.flush()` 가 또 `BrokenPipeError` 를 냅니다(그래서 `output.err` 도 그 예외를 삼키도록 되어 있습니다 — cli/output.py:60-65). 근본 해결은 **stdout 을 통째로 블랙홀로 갈아끼우는 것**이고, 그 일은 `main()` 이 합니다.

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

**`KeyboardInterrupt` 는 명시적으로 잡아야 합니다.** `BaseException` 직계라 마지막 `except Exception` 이 못 잡습니다. 종료 코드 130 은 유닉스 관례(128 + SIGINT 신호 번호 2)입니다.

> **⚙️ 내부 동작 — 130 이라는 숫자의 출처** — 유닉스 셸(bash 등)은 자식 프로세스가
> **신호에 의해 죽었을 때** 그 사실을 `128 + 신호번호` 로 보고합니다. `Ctrl+C` 가
> 보내는 SIGINT 의 번호가 2 이므로 128 + 2 = 130 입니다. 이 프로그램은 실제로 신호에
> 죽는 대신 `KeyboardInterrupt` 를 잡아 **직접 130 을 반환**하지만, 숫자를 관례에
> 맞춰 두면 셸 스크립트가 `if [ $? -eq 130 ]` 로 "사용자가 취소했다"를 평소처럼
> 판별할 수 있습니다. 참고로 `os.open`/신호 번호처럼 이 관례는 유닉스의 것이고,
> Windows 에는 신호로 죽는 개념이 없어 이 값은 순수한 약속입니다.
> → [12 §3](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `Ctrl+C` 가 예외가 되는 경로** — OS 가 SIGINT 를 보내면 CPython 의
> C 레벨 신호 핸들러가 플래그만 세우고 즉시 돌아옵니다. 인터프리터는 바이트코드
> 사이의 안전한 지점에서 그 플래그를 확인해 그때 `KeyboardInterrupt` 를 **일으킵니다**.
> 그래서 `input()` 으로 대기 중이든 계산 중이든 결국 파이썬 예외로 나타나고,
> `try/except` 로 잡을 수 있습니다. → [12 §3](./12-syntax-and-stdlib.md)

### 5.4 부류 2 — 입력 오류 (사용자가 고치면 해결)

budget_app/cli/error_handler.py:65-74

```python
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

**두 절의 힌트 처리가 다릅니다.**

- `ValidationError` — 고정 힌트(`HINT_VALIDATION` = "입력값을 다시 확인해 주세요"). 값 하나가 형식에 안 맞는다는 것 외에 더 안내할 게 없기 때문입니다.
- `AppError` — 예외가 들고 온 `exc.hint` 를 씁니다. "카테고리가 사용 중"에는 "`--replace-with` 를 쓰세요", "id 를 못 찾음"에는 "`list` 로 확인하세요" 처럼 상황별 안내가 가능합니다.

`if exc.hint:` 검사가 있으므로 힌트 없는 `AppError`(예: `ERR_REPLACE_SELF`)도 정상 동작합니다.

**순서 제약**: `ValidationError` 는 `ValueError` 의 자식, `AppError` 는 `Exception` 직계로 **서로 상속 관계가 없습니다.** 따라서 이 둘의 순서는 바꿔도 동작이 같습니다 — 의미적 분류상 "더 구체적인 것 먼저"로 배치했을 뿐입니다.

> **🔎 문법의 출처 — `except E as exc:`** — 예전에는 `except E, exc:` 라고 콤마로 썼는데,
> `except (A, B):` 와 헷갈려 "A 를 잡고 B 에 대입"으로 오해하는 사고가 잦았습니다.
> 그래서 PEP 3110 이 `as` 키워드 형태로 바꿨습니다(파이썬 3 에서는 `as` 만 유효).
> 함께 바뀐 규칙이 하나 더 있습니다 — **`exc` 는 except 절이 끝나는 순간 자동으로
> `del` 됩니다.** 예외 객체가 트레이스백을 통해 프레임을 참조하고 그 프레임이 다시
> 예외를 참조하는 순환을 끊기 위해서입니다. 그래서 `except AppError as exc:` 블록
> 바깥에서 `exc` 를 쓰면 `NameError` 가 납니다. 이 코드가 값을 절 안에서 전부
> 소비하고 나가는 이유이기도 합니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `MSG_ERROR_LINE.format(msg=exc)`** — `str.format` 은 `{msg}` 자리에
> 넣을 때 `format(값, "")` 을 부르고, 포맷 스펙이 비어 있으면 그것은 결국 `str(값)`
> 입니다. 예외 객체의 `str()` 은 `BaseException.args` 를 문자열로 만든 것이라,
> `ValidationError("금액은 정수여야 합니다")` 는 그 메시지 하나만 남습니다.
> `AppError` 쪽이 `exc` 대신 `exc.message` 를 쓰는 것은 취향이 아니라, `hint` 를
> 따로 들고 있는 클래스라 **메시지 부분만 명시적으로 꺼내려는** 것입니다
> (`errors.py:48-51` 에서 `self.message` 를 따로 저장합니다).
> → [12 §1-A](./12-syntax-and-stdlib.md)

### 5.5 부류 3 — 환경 상태 (파일·권한·인코딩·디스크)

budget_app/cli/error_handler.py:76-76

```python
        # ---------- (3) 환경 상태 — 파일/권한/인코딩/디스크 ----------
```

이 부류에는 절이 여섯 개 있습니다 — `FileNotFoundError` / `IsADirectoryError` / `NotADirectoryError` / `PermissionError` / `UnicodeDecodeError` / `OSError`. 앞의 넷은 전부 `OSError` 의 자식이라 **마지막 `OSError` 보다 위에 있어야** 합니다. 이것이 상속 제약입니다.

> **🔎 문법의 출처 — `FileNotFoundError` 라는 이름 자체** — 예전에는 이런 구분이
> 없어서 `except IOError as e:` 로 잡은 다음 `if e.errno == errno.ENOENT:` 로 직접
> 갈라야 했습니다(`errno` 는 운영체제가 실패 원인을 숫자로 알려 주는 값입니다).
> PEP 3151 이 이 `errno` 검사를 **예외 계층으로 승격**시켜,
> OS 가 돌려준 errno 값에 따라 파이썬이 알아서 `FileNotFoundError`(ENOENT),
> `PermissionError`(EACCES/EPERM), `IsADirectoryError`(EISDIR),
> `NotADirectoryError`(ENOTDIR) 를 만들어 줍니다. 그래서 이 except 체인이
> errno 상수를 한 번도 언급하지 않고도 원인별로 다른 힌트를 낼 수 있습니다.
> 잡힌 예외에는 여전히 `exc.errno` 가 들어 있습니다.
> → [12 §2-B](./12-syntax-and-stdlib.md)

**`exc.filename or exc` 관용구.** 파이썬의 파일 관련 예외는 `filename` 속성에 경로를 담아 주지만, 항상 채워지는 것은 아닙니다. 없으면 예외 객체 자체를 문자열로 씁니다.

> **🔎 문법의 출처 — `A or B` 가 불리언이 아니다** — 파이썬의 `or` 는 참/거짓을
> 돌려주는 것이 아니라 **평가한 피연산자 자체**를 돌려줍니다. `A` 가 truthy 면 `A`,
> 아니면 `B` 입니다. `exc.filename` 이 `None` 이거나 빈 문자열이면 falsy 라
> `exc` 로 넘어갑니다. 같은 성질을 §5.1 의 반환값 규약에서는 **일부러 피했다**는
> 점을 나란히 보면 좋습니다 — 거기서는 `0` 이 falsy 라는 것이 함정이었고,
> 여기서는 falsy 를 대체하는 것이 정확히 원하는 동작입니다.
> → [12 §1-A](./12-syntax-and-stdlib.md)

**`UnicodeDecodeError` 는 왜 여기 있나.** 이것은 `ValueError` 의 자손이지만, "사용자가 값을 고치면 되는 문제"가 아니라 **파일 자체의 상태 문제**입니다. 그래서 부류 3 에 넣고 전용 종료 코드(6)를 줍니다. 힌트도 구체적입니다.

budget_app/cli/messages.py:115-116

```python
MSG_ERR_ENCODING = "[오류] 파일 인코딩을 읽을 수 없습니다 (UTF-8 이 아닙니다)."
HINT_ENCODING = "[힌트] CSV 를 UTF-8 로 다시 저장하세요 (엑셀: '다른 이름으로 저장 > CSV UTF-8')."
```

한국 사용자의 CSV 가 CP949 로 저장되는 일이 흔하다는 현실을 반영한 안내입니다.

> **⚙️ 내부 동작 — `UnicodeDecodeError` 는 어디서 나오나** — 이 예외를 던지는 것은
> `open(..., encoding="utf-8")` 이 만든 텍스트 래퍼의 **디코딩 단계**입니다. 바이트를
> 문자로 옮기다 UTF-8 규칙에 맞지 않는 바이트열을 만나면 코덱이 실패를 알리고,
> 오류 처리 방식이 기본값(`strict`)이면 그대로 예외가 됩니다. 예외 객체는 원인을
> 정확히 들고 있습니다.
> → [12 §3](./12-syntax-and-stdlib.md)

```python
>>> b"\xc7\xd1".decode("utf-8")          # CP949 로 저장된 "한" 의 바이트
Traceback (most recent call last):
  ...
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc7 in position 0: invalid continuation byte
```

`exc.encoding`(`'utf-8'`) / `exc.object`(문제의 바이트열) / `exc.start`·`exc.end`(위치) / `exc.reason`(사유)이 전부 채워져 있습니다. 이 코드가 그 값들을 화면에 노출하지 않는 이유는 **사용자가 할 일이 "UTF-8 로 다시 저장"뿐**이기 때문입니다 — 바이트 오프셋을 알려 줘도 행동이 달라지지 않습니다.

**`OSError` 포괄 절**은 디스크 가득 참(ENOSPC), 파일 잠금 같은 나머지를 받습니다. 원자적 쓰기(임시 파일에 다 쓴 뒤 이름만 갈아 끼워, **대상 파일 하나가 반쯤 쓰인 모습으로는 보이지 않게** 하는 저장 방식 — 여기까지가 이 방식이 지켜 주는 범위이고, 남는 한계는 [07 문서](./07-repository.md)에 있습니다) 중 디스크가 차면 여기로 옵니다 — 그리고 임시 파일에 쓰던 중이므로 **원본은 무사합니다**.

### 5.6 부류 4 — 최후 방어선

budget_app/cli/error_handler.py:105-109

```python
        # ---------- (4) 최후 방어선 — 분류 밖의 버그 ----------
        except Exception as exc:  # noqa: BLE001 — 어떤 예외도 트레이스백으로 끝내지 않기 위함
            # 사용자용 한 줄 요약을 먼저 내고, 그다음에 원인 추적용 기록을 남긴다.
            output.err(messages.MSG_ERR_UNEXPECTED.format(error=exc))
            output.err(messages.HINT_UNEXPECTED)
```

budget_app/cli/error_handler.py:118-119

```python
            logger.exception(messages.LOG_UNHANDLED)
            return config.EXIT_ERROR
```

**`# noqa: BLE001`** 은 린터(Ruff)의 "blind except" 경고를 끄는 표기입니다. 보통 `except Exception` 은 나쁜 습관이지만, **CLI 최상위에서는 정당합니다** — 사용자에게 원시 트레이스백만 던지고 끝내는 것보다 한 줄 요약과 종료 코드를 주는 편이 낫기 때문입니다. 그 의도를 주석으로 명시해 두었습니다.

> **🔎 문법의 출처 — `# noqa: 코드`** — `noqa`("no quality assurance")는 flake8 이
> 정착시킨 **줄 단위 억제 주석**이고 Ruff 가 그대로 이어받았습니다. 코드를 붙이면
> 그 규칙 하나만, 안 붙이면 그 줄의 모든 경고가 꺼집니다. `BLE` 접두사는
> flake8-blind-except 플러그인에서 온 것이고 `BLE001` 이 "구체적이지 않은 예외를
> 잡았다(`blind-except`)"입니다. 이 프로젝트의 `pyproject.toml` 은
> `select = ["E", "F", "I", "UP", "B"]` 를 쓰므로, 이 주석은 규칙을 끄는 효과보다
> **"이건 실수가 아니라 의도"라는 표시**로 읽는 편이 정확합니다.

**`logger.exception(...)` 이 이 절의 핵심입니다.** 스택트레이스를 버리는 게 아니라 **로그로 옮깁니다.**

> **⚙️ 내부 동작 — `logger.exception(msg)`** — 이것은 `logger.error(msg, exc_info=True)`
> 와 정확히 같습니다(`logging/__init__.py` 의 `Logger.exception` 이 한 줄로 그렇게
> 위임합니다). `exc_info=True` 를 주면 로깅이 `sys.exc_info()` 를 읽어 그 3-튜플을
> `LogRecord.exc_info` 에 담고, 포매터가 `formatException()` 에서 `traceback` 모듈로
> **문자열화해 메시지 뒤에 덧붙입니다**(결과는 `record.exc_text` 에 캐시됩니다).
> 그래서 반드시 **except 블록 안에서** 불러야 하며, 밖에서 부르면 붙일 예외가 없습니다.
> → [12 §2-B](./12-syntax-and-stdlib.md)

**여기서 중요한 것은 레벨이 DEBUG 가 아니라 ERROR 라는 점입니다.** 소스 주석(error_handler.py:110-117)이 그 변경 이유를 직접 설명합니다 — 이전에는 `logger.debug(..., exc_info=True)` 였는데, 기본 로그 레벨이 WARNING 이라 **`--debug` 없이 실행하면 스택트레이스가 아무 데도 남지 않았습니다.** 여기까지 온 예외는 분류되지 않은 버그이고, 그 스택이 원인을 찾을 유일한 단서인데 말입니다.

`logger.exception` 은 ERROR 로 기록하므로 WARNING 문턱을 넘습니다. 즉 **평소 실행에서도** 트레이스백이 stderr 에 남습니다. 실제 출력입니다.

```
$ python -m budget_app <버그를 밟는 명령>          # --debug 없이
[오류] 예기치 못한 오류가 발생했습니다: 'nope'
[힌트] `--debug` 를 붙여 다시 실행하면 stderr 로그에 스택트레이스가 남습니다.
[ERROR] unhandled error
Traceback (most recent call last):
  File ".../budget_app/cli/error_handler.py", line 50, in wrapper
    result = func(*args, **kwargs)
  ...
KeyError: 'nope'
```

**정책이 부류마다 다르다**는 것이 요점입니다. 사용자가 고칠 수 있는 앞의 세 부류(§5.3~§5.5)는 여전히 한두 줄로 끝나고 트레이스백이 없습니다. 마지막 부류만 "프로그램이 예상하지 못한 상태"이므로, 감추는 것보다 **신고할 수 있게 하는 편**을 택했습니다. 힌트 문구가 `--debug` 를 안내하는 것은 그때 `%(asctime)s %(name)s:%(lineno)d` 까지 붙은 상세 포맷(`LOG_FORMAT_DEBUG`)으로 바뀌고 다른 DEBUG 로그도 함께 보이기 때문입니다.

**그리고 `setup_logging` 이 로그를 화면에 얹는 유일한 지점입니다.** `cli/app.py:87-88` 의 주석이 그 의존을 명시합니다 — `main()` 이 `output.setup_logging()` 을 부르지 않으면 로거에 핸들러가 하나도 붙지 않습니다.

> **⚙️ 내부 동작 — 핸들러가 없으면 어떻게 되나(주의: 소스 주석보다 이쪽이 현재 사실)**
> — `logging.getLogger("budget_app")` 로 만든 로거는 처리를 부모(루트)에게 전파하는데,
> 루트에도 핸들러가 없으면 `logging.lastResort` 라는 **최후 수단 핸들러**가 대신
> 받습니다. 이것은 stderr 로 쓰는 핸들러이고 레벨이 WARNING 이라, ERROR 로 찍는
> `logger.exception(...)` 은 `setup_logging` 없이도 (포맷 없이 맨 메시지 + 트레이스백
> 형태로) 출력됩니다. 반면 DEBUG 레코드는 문턱을 못 넘어 사라집니다 —
> `@log_call`/`@measure_time` 의 로그가 `--debug` 없이는 보이지 않는 이유가 이것입니다.
> → [12 §2-B](./12-syntax-and-stdlib.md)

```python
>>> import logging
>>> logging.lastResort
<_StderrHandler <stderr> (WARNING)>
```

`cli/output.py:82-85` 와 `cli/app.py:87-88` 의 주석은 "`setup_logging` 이 없으면 스택트레이스가 어디에도 남지 않는다"고 적고 있는데, 이것은 이 절이 **`logger.debug(..., exc_info=True)` 였던 시절의 설명**입니다. ERROR 로 올린 지금은 `lastResort` 덕분에 살아남습니다. 그래도 `setup_logging` 이 하는 일은 그대로 남습니다 — 레벨을 정하고(`--debug` → DEBUG), 포맷을 붙이고, `force=True` 로 재호출 시에도 설정을 확정합니다(`cli/output.py:94-99`).

---

## 6. except 순서를 검증하는 법

앞 절의 순서가 정말 맞는지는 눈대중 대신 파이썬에게 직접 물어 확인할 수 있습니다. 물어볼 것은 하나뿐입니다 — "이 예외가 저 예외의 한 갈래인가". 한 갈래라면 좁은 쪽이 반드시 위에 와야 합니다.

예외 상속 계층을 그림으로 정리합니다.

```
BaseException
├── KeyboardInterrupt                (Ctrl+C — Exception 이 아님!)
└── Exception
    ├── OSError                      (입출력 오류의 부모)
    │   ├── FileNotFoundError        ← OSError 보다 먼저 잡아야 함
    │   ├── IsADirectoryError        ←
    │   ├── NotADirectoryError       ←
    │   ├── PermissionError          ←
    │   └── ConnectionError
    │       └── BrokenPipeError      ← OSError 보다 먼저 잡아야 함
    ├── ValueError
    │   ├── ValidationError          (errors.py 정의)
    │   └── UnicodeError
    │       └── UnicodeDecodeError
    ├── AppError                     (errors.py 정의)
    │   └── InputAborted             (prompts.py 정의)
    └── KeyError, TypeError, ...
```

파이썬으로 직접 확인할 수 있습니다.

```python
>>> BrokenPipeError.__mro__
(BrokenPipeError, ConnectionError, OSError, Exception, BaseException, object)
>>> issubclass(BrokenPipeError, OSError)
True
>>> issubclass(KeyboardInterrupt, Exception)
False                                    # ← 그래서 명시적으로 잡아야 한다
```

> **⚙️ 내부 동작 — `__mro__` 가 정확히 무엇인가** — MRO(Method Resolution Order)는
> 클래스가 이름을 찾을 때 훑는 **순서가 확정된 클래스 목록**이며, 파이썬은 이를 C3
> 선형화 알고리즘으로 계산해 클래스 생성 시점에 `__mro__` 튜플로 저장합니다.
> `issubclass(A, B)` 는 대체로 "`B` 가 `A.__mro__` 안에 있는가"이므로, `__mro__` 를
> 눈으로 읽는 것이 곧 except 순서 제약을 읽는 것입니다. 예외 클래스는 다중 상속을
> 쓰지 않아 목록이 일직선이고, 그래서 `BrokenPipeError.__mro__` 에 `OSError` 가
> 보이는 순간 "`OSError` 절보다 위에 둬야 한다"가 확정됩니다.
> → [12 §1-B](./12-syntax-and-stdlib.md)

이 소스에서 자주 잊히는 세 가지를 확인해 두면 좋습니다.

```python
>>> issubclass(ValidationError, ValueError)        # errors.py:33 — 일부러 ValueError 상속
True
>>> issubclass(UnicodeDecodeError, ValueError)     # 같은 ValueError 계열이지만 부류 3
True
>>> issubclass(InputAborted, AppError)             # prompts.py:28 — 그래서 종료 코드가 4
True
```

`ValidationError` 와 `UnicodeDecodeError` 가 **둘 다 `ValueError` 자손인데 서로 상속 관계는 아니라는 것**이 핵심입니다. 그래서 앞뒤 어디에 두어도 서로를 가리지 않고, 지금의 배치(하나는 부류 2, 하나는 부류 3)는 순전히 의미적 판단입니다.

현재 코드의 순서가 제약을 만족하는지 검증하는 코드:

```python
ORDER = [BrokenPipeError, KeyboardInterrupt, ValidationError, AppError,
         FileNotFoundError, IsADirectoryError, NotADirectoryError, PermissionError,
         UnicodeDecodeError, OSError, Exception]   # 소스와 같은 11개, 같은 순서

for i, a in enumerate(ORDER):
    for b in ORDER[i + 1:]:
        if issubclass(b, a):
            print(f"문제: {b.__name__} 가 {a.__name__} 뒤에 있어 도달 불가")
print("검증 완료")
```

### 6.1 예외 하나의 여행 — `AppError` 를 예로

`python -m budget_app delete --id TX-999999` 를 실행했을 때의 전체 경로입니다.

```
1) cli.cmd_delete(ctx, args)
       │  ctx.tx_service.delete("TX-999999")
       ▼
2) services.TransactionService.delete                          [services/transactions.py:72-77]
       │  if not self.txs.delete(tx_id):
       ▼
3) repository.TransactionRepository.delete → False             [storage/repositories.py:150-171]
       │  (exists() 가 False → 파일을 건드리지 않고 False 반환)
       ▼
4) services 가 False 를 받아 AppError 로 승격
       raise AppError(messages.ERR_TX_NOT_FOUND.format(tx_id=tx_id),
                      hint=messages.HINT_LIST_ID)
       │
       ▼  (예외가 콜스택을 거슬러 올라감)
5) @handle_errors 의 wrapper 가 except AppError 로 포착         [cli/error_handler.py:70]
       │  (핸들러가 아니라 app.py:61 의 _dispatch 를 감싼 wrapper 다)
       │
       ├─▶ output.err("[오류] 해당 id 의 거래를 찾을 수 없습니다: TX-999999")
       ├─▶ output.err("[힌트] `list` 로 id 를 확인하세요.")
       └─▶ return config.EXIT_APP   (= 4)
       │
       ▼
6) cli.main 이 그 값을 반환 → __main__.py 의 sys.exit(4)
       │
       ▼
7) 셸:  $?  또는  $LASTEXITCODE  →  4
```

**3~4단계가 계층 분리의 압축된 예입니다.**

budget_app/storage/repositories.py:159-168

```python
        if target is None:
            return False
        found = False

        def _drop(tx: Transaction) -> Transaction | None:
            nonlocal found
            if tx.id == target:
                found = True
                return None
            return tx
```

budget_app/services/transactions.py:72-76

```python
    @log_call
    def delete(self, tx_id: str) -> None:
        if not self.txs.delete(tx_id):
            raise AppError(
                messages.ERR_TX_NOT_FOUND.format(tx_id=tx_id), hint=messages.HINT_LIST_ID
```

**저장소는 "없었다"는 사실만 보고**(`False`), **서비스가 그것을 "오류"로 판정**합니다(`AppError`). 왜 이렇게 나누는가 — "id 가 없다"가 항상 오류인 것은 아니기 때문입니다. 예를 들어 "있으면 지우고 없으면 넘어가는" 멱등 삭제(같은 명령을 몇 번 반복해도 결과가 달라지지 않는 삭제)를 나중에 추가한다면, 저장소는 그대로 두고 서비스만 바꾸면 됩니다.

---

## 7. 종료 코드 표

프로그램이 끝나면서 셸에 남기는 숫자를 모아 둔 표입니다. 화면 메시지와 달리 이 숫자를 읽는 것은 사람이 아니라 다른 프로그램입니다. 셸 스크립트가 "방금 그 명령이 성공했나"를 판단할 근거가 이것뿐이라, 값마다 뜻을 정해 두었습니다.

> **💡 쉽게 말하면** — 심부름을 보냈더니 돌아와서 말 대신 숫자 하나만 적어 내는 것과
> 같습니다. 0 은 "잘 다녀왔습니다"이고, 나머지 숫자는 각각 다른 사정입니다. 하필 숫자인
> 이유는 이 보고를 받는 쪽이 사람이 아니라 다른 프로그램이라, 문장은 읽을 줄 몰라도
> 숫자는 곧바로 견줄 수 있기 때문입니다.
> 다만 이 비유는 담을 수 있는 양에서 깨집니다 — 숫자 한 개로는 사정을 자세히 전할 수
> 없고, 셸이 탈 없이 받아 주는 폭도 좁습니다(유닉스에서는 0~255 를 넘으면 잘립니다 —
> 자세한 조건은 아래 ⚙️ 상자에 있습니다). 그래서 자세한 이야기는 §5 에서 본 대로
> stderr 로 따로 내보냅니다.

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

| 코드 | 상수 | 발생 경로 | 실제 재현 방법 |
| --- | --- | --- | --- |
| 0 | `EXIT_OK` | 정상 | `python -m budget_app list` |
| 1 | `EXIT_ERROR` | 분류 밖의 버그 (`except Exception`) | (정상 상황에서는 발생하지 않음) |
| 2 | `EXIT_VALIDATION` | `ValidationError` | `export --out a.csv --month 2024-13` |
| 3 | `EXIT_IO` | 파일 없음/디렉터리/권한/디스크 | `import --from nope.csv` |
| 4 | `EXIT_APP` | `AppError` (+ `InputAborted`) | `delete --id TX-999999` |
| 5 | `EXIT_NO_CATEGORY` | 카테고리 0개에서 `add` | 카테고리 파일을 비우고 `add` |
| 6 | `EXIT_ENCODING` | `UnicodeDecodeError` | CP949 로 저장한 CSV 를 import |
| 130 | `EXIT_INTERRUPT` | `KeyboardInterrupt` | 대화형 입력 중 Ctrl+C |

**`EXIT_NO_CATEGORY`(5)만 예외 경로가 아닙니다.** 핸들러가 직접 반환합니다.

budget_app/cli/handlers.py:33-37

```python
def cmd_add(ctx: AppContext, args: argparse.Namespace) -> int:
    if not ctx.cat_service.list_names():
        # 0 이 아닌 종료 코드로 끝나는 실패 경로 → 진단 채널(stderr).
        output.err(messages.MSG_NO_CATEGORIES)
        return config.EXIT_NO_CATEGORY
```

"카테고리가 없다"는 오류라기보다 **안내가 필요한 상태**입니다. 예외를 던질 만한 일이 아니지만 종료 코드는 0이 아니어야 하므로, 직접 반환하는 편이 정직합니다. 다만 메시지는 stderr(`output.err`)로 보냅니다 — **0이 아닌 종료 코드로 끝나는 경로의 출력은 "결과"가 아니라 "진단"** 이기 때문입니다.

셸에서 확인:

```bash
python -m budget_app delete --id TX-999999
echo $?          # bash → 4
$LASTEXITCODE    # PowerShell → 4
```

> **⚙️ 내부 동작 — 반환값이 셸의 숫자가 되기까지** — 이 프로그램의 함수들은 종료 코드를
> **반환만** 하고, 실제로 프로세스를 끝내는 것은 `budget_app/__main__.py:8` 의
> `sys.exit(main())` 한 줄뿐입니다. `sys.exit(n)` 은 즉시 죽는 것이 아니라
> `SystemExit(n)` 예외를 던지고, 아무도 잡지 않으면 인터프리터가 정리 작업(버퍼
> 플러시 등)을 마친 뒤 그 값을 OS 의 **프로세스 종료 상태**로 넘깁니다. 유닉스는
> 하위 8비트만 쓰므로 0~255 범위를 벗어나면 잘립니다(그래서 130 까지가 안전한 범위).
> `SystemExit` 는 `BaseException` 직계라 `except Exception` 에 걸리지 않습니다 —
> `handle_errors` 안에서 `sys.exit` 를 불러도 삼켜지지 않는다는 뜻입니다.
> → [12 §3](./12-syntax-and-stdlib.md)

`main()` 을 함수로 두고 `sys.exit` 를 바깥 한 곳으로 몰아 둔 덕분에, 테스트는 `main(["list"]) == 0` 처럼 **프로세스를 죽이지 않고** 종료 코드를 검사할 수 있습니다.

---

## 8. 정리 — 과제 방어용 요약

**Q. 데코레이터로 분리한 공통 기능이 무엇이며, 왜 분리가 필요했나요?**

세 개입니다. `@log_call`(호출 로그), `@measure_time`(시간 측정), `@handle_errors`(예외→종료코드). 분리 이유는 두 층입니다. 함수 본문에서 분리한 이유는 로직이 부대 처리에 묻히고 같은 코드가 모든 함수에 복사되기 때문이고, **데코레이터끼리도 두 파일로 나눈 이유**는 관측(전 계층 공용)과 표현(CLI 전용)이 의존하는 대상이 다르기 때문입니다. 한 파일에 두면 서비스 계층이 출력 모듈에 전이 의존하는 역류가 생깁니다.

**Q. 예외 처리 정책이 어떻게 되나요?**

예외를 네 부류로 나눕니다 — 종료 신호(오류 아님), 입력 오류(사용자가 고치면 됨), 환경 상태(프로그램 밖의 문제), 최후 방어선(버그). except 절이 그 순서로 묶여 있고, 부류 안에서는 상속 제약(자식이 부모보다 위)을 지킵니다. 이 두 종류의 제약을 docstring 에 구분해서 적어 두었습니다.

**Q. 스택트레이스를 감추면 디버깅은 어떻게 하나요?**

부류를 나눠 답이 다릅니다. 사용자가 고칠 수 있는 앞의 세 부류는 한두 줄 메시지로 끝냅니다. 마지막 `except Exception` 절만은 `logger.exception(...)`(= `logger.error(..., exc_info=True)`)으로 트레이스백을 **ERROR 레벨로 남깁니다.** 기본 로그 레벨이 WARNING 이므로 이 기록은 `--debug` 없이도 stderr 에 나옵니다 — 이전 버전이 DEBUG 레벨을 써서 기본 실행에서는 스택이 아무 데도 남지 않던 것을 고친 자리입니다(error_handler.py:110-117 주석). `--debug`(또는 `BUDGET_APP_DEBUG` 환경변수)를 켜면 시각·모듈·줄 번호가 붙은 상세 포맷과 다른 DEBUG 로그까지 함께 보입니다.

**Q. 왜 오류를 stdout 이 아니라 stderr 로 보내나요?**

`list > out.txt` 같은 리다이렉트에서 데이터 파일이 오류 문자열로 오염되지 않게 하기 위해서입니다. 또 파이프가 끊겨 stdout 이 깨진 상황에서도 stderr 는 살아 있어 원인을 전할 수 있습니다.

**Q. `BrokenPipeError` 는 왜 처리하지 않고 다시 던지나요?**

`list | head` 에서 `head` 가 먼저 닫히면 stdout 이 이미 깨진 상태입니다. 이때 오류 메시지를 출력하려 하면 또 파이프가 깨지는 2차 사고가 납니다. 근본 해결은 stdout 을 `os.devnull` 로 갈아끼우는 것이고, 그 일은 최상위 `main()` 이 합니다.

---

**다음 문서**: [07. 저장소 계층](./07-repository.md) — 스트리밍 읽기, 원자적 교체, 손상 줄 보존, ID 발급.
