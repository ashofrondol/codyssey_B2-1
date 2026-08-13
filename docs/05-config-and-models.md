# 05. 설정·검증·모델 — config / messages / validators / errors / entities

## 쉬운 말로 먼저

이 프로그램은 가계부이고, 가계부를 오래 쓰려면 먼저 **쓰는 말을 정해 두어야** 합니다. 돈이 들어온 것과 나간 것을 각각 뭐라 부를지, 날짜를 어떤 모양으로 적을지, 화면에 띄울 안내 문구는 무엇인지, 잘못 적힌 입력을 어떻게 돌려보낼지 같은 것들입니다. 이 문서는 그 말을 정해 둔 다섯 군데를 하나씩 엽니다 — 값을 모아 둔 곳, 문구를 모아 둔 곳, 들어온 값이 규칙에 맞는지 보는 곳, 데이터가 어떤 모양인지 적어 둔 곳, 실패를 종류별로 나눠 둔 곳입니다.

다섯 군데는 모두 짧고, 파일을 읽지도 화면에 찍지도 않으며, 다른 파일을 거의 참조하지 않습니다. 그래서 코드를 처음 정독해 보려는 분에게는 여기가 가장 들어오기 좋은 자리입니다 — 여기서 익힌 이름들이 나머지 문서에 계속 되돌아옵니다. 다만 쉽다고 해서 사소한 것만 있는 것은 아닙니다. §4 의 날짜 이야기는 표기 하나가 어긋났을 때 거래가 오류 하나 없이 **조용히 사라지는** 사고를 다룹니다.

**이 문서에 자주 나오는 말**

| 말 | 쉬운 뜻 |
| --- | --- |
| 검증 | 들어온 값이 규칙에 맞는지 보는 일. 맞으면 통과시키고, 아니면 그 자리에서 되돌려보냅니다 |
| 정규화 | 뜻은 같은데 모양이 제각각인 것을 한 모양으로 맞추는 일 (`2024-1-5` → `2024-01-05`) |
| 상수 | 프로그램이 도는 동안 바뀌지 않는 값에 이름을 붙여 한 군데 모아 둔 것 |
| 예외 | "여기서부터는 못 하겠다"고 알리며 하던 일을 그 자리에서 멈추는 파이썬의 신고 방식 |
| 종료 코드 | 프로그램이 끝나면서 남기는 숫자 하나. 0이면 정상이고, 나머지는 실패 사유마다 다릅니다 |
| 불변식 | 그 데이터라면 언제나 참이어야 하는 조건 (예: 금액은 늘 0보다 큰 정수) |
| 값 객체 | 값 하나를 감싸서, 그 값이 지켜야 할 규칙까지 함께 지니게 만든 작은 타입 |
| 정규식 | 문자열이 어떤 모양이어야 하는지를 짧은 기호로 적어 둔 규칙 ("`TX-` 뒤에 숫자만" 같은 것) |

**바쁘면 여기만**

- **§1.2 두 예외의 판별 기준** — 이 프로그램이 실패를 왜 두 종류로 나누는지가 표 하나에 있습니다. 이 구분이 그대로 종료 코드까지 이어지므로, 여기만 알아도 나머지 문서의 오류 이야기가 읽힙니다.
- **§4.3 대표 코드** — 날짜 표기 하나 때문에 거래가 조용히 사라지는 이야기입니다. "검증이 왜 필요한가"가 설명이 아니라 사고로 납득되는 자리입니다.
- **§6 핵심 개념** — 다섯 모듈을 한 문장으로 꿰는 결론입니다. 시간이 정말 없으면 여기만 봐도 요지는 남습니다.

---

프로그램의 **어휘**를 정의하는 다섯 모듈을 정독합니다. 값은 무엇이고 문구는 무엇인가. 규칙은 어디에 있고 데이터는 어떤 모양인가. 그리고 실패에는 어떤 타입이 있는가.

> **난이도**: 🟢 초보 ~ 🟡 중급
>
> **먼저 읽으면 좋은 문서**: [02. 파이썬 기초 문법](./02-python-basics.md), [03. 파이썬 중·고급 기법](./03-python-advanced.md) §1(dataclass)

---

## 0. 다섯 모듈의 분업 한눈에

```
루트 (횡단 — 어느 계층에도 속하지 않음)
  errors.py             ValidationError / AppError          ← 실패의 타입
  config.py             LOGGER_NAME                         ← 앱 정체성 (이것 하나만)
     ▲
계층마다 하나씩 놓인 config.py / messages.py
  domain/config.py      VALID_TYPES, DATE_FORMAT, TX_ID_*   ← 값·정책 (동작이 달라지는 것)
  domain/messages.py    "금액은 정수여야 합니다."             ← 문구 (글자만 달라지는 것)
  storage/config.py     파일명·인코딩·CSV 스키마·백업
  services/config.py    ON_DUPLICATE_*, MAX_IMPORT_ERRORS
  cli/config.py         EXIT_*, MAX_INPUT_RETRIES
     ▲
domain/ (도메인 계층 — I/O 를 전혀 모름)
  validators.py         parse_date / parse_amount / ...     ← 규칙 하나 = 함수 하나
  tx_id.py              TransactionId                       ← 거래 id 값 객체
     ▲
  entities.py           Transaction / Budget / Category     ← 데이터 모양 + 불변식
  queries.py            SearchFilter                        ← 질의 조건
  results.py            MonthlySummary / ImportReport       ← 계산 결과
  periods.py            month_range                         ← 기간 규칙
```

의존은 아래에서 위로 **한 방향**입니다. 맨 아래의 `errors.py` 와 루트 `config.py` 는 아무것도 import(다른 파일에 있는 이름을 가져다 쓰는 것) 하지 않습니다. 그 위에서 `validators` 가 `errors` 와 도메인 `config`·`messages` 를 쓰고, 다시 그 위에서 `entities` 가 `validators` 와 `tx_id` 를 씁니다(→ [04 §1.2](./04-architecture.md)).

> **📌 예전 이름이 눈에 익다면** — 리팩터 전에는 도메인 데이터가 전부 `domain/models.py` 한 파일에 있었습니다. 지금은 저장되는 것(`entities.py`), 질의 조건(`queries.py`), 계산 결과(`results.py`), 기간 규칙(`periods.py`)으로 나뉘어 있습니다. 이 문서에서 "리팩터 전에는 …"으로 시작하는 문단은 **지금 없는 코드**를 설명하는 자리입니다.

---

## 1. errors.py — 실패에도 타입이 있다

### 1.1 왜 별도 모듈인가

리팩터 전에는 `ValidationError` 가 `models.py` 에, `AppError` 가 `decorators.py` 에 흩어져 있었습니다. 그 결과 서비스 계층이 `AppError` 하나를 쓰려고 `decorators` 를 가져다 써야 했습니다. 그런데 `decorators` 는 다시 화면 출력 모듈을 가져다 씁니다 — 아래쪽에 있어야 할 서비스가 위쪽의 화면 출력에 매달리는 **역류**입니다.

budget_app/errors.py:1-2

```python
"""예외 계층 — 애플리케이션이 직접 정의하는 오류를 한곳에 모은다.

```

**이 파일은 import 문이 하나도 없습니다.** 계층 그래프의 맨 아래에 있다는 뜻이고, 그래서 어느 모듈이든 안심하고 가져다 쓸 수 있습니다.

### 1.2 두 예외의 판별 기준

> **💡 쉽게 말하면** — 은행 창구에 송금 신청서를 냅니다. 금액 칸에 "만 원쯤"이라고 적혀 있으면 창구 직원은 서류만 보고 그 자리에서 되돌려줍니다 — 장부를 펴 볼 것도 없이 틀렸다는 걸 알 수 있으니까요. 반면 서류는 흠잡을 데가 없는데 받는 사람 계좌번호가 없는 번호라면, 이건 서류를 아무리 들여다봐도 모르고 **장부를 찾아봐야** 압니다. 앞이 `ValidationError`, 뒤가 `AppError` 입니다.
>
> 다만 이 비유는 "한 사람이 둘 다 본다"는 데서 깨집니다 — 이 프로그램에서는 서류 검사를 도메인 계층이, 장부를 봐야 아는 판단을 그 바깥(서비스·저장소·CLI)이 나눠 맡습니다. 어느 쪽 오류가 어디서 나오는지는 아래 표의 "발생 위치" 행에 그대로 적혀 있습니다.

| 질문 | ValidationError | AppError |
|---|---|---|
| 값 하나만 보고 판단되는가 | **예** | 아니오 (저장된 상태를 봐야 함) |
| 예 | `"2024-13-45"` 는 날짜가 아님 | `"food"` 가 등록된 카테고리인지 |
| 발생 위치 | validators, 모델 생성자 | services, csv_io, cli |
| 힌트를 갖는가 | 아니오 | 예 (`hint` 속성) |
| 종료 코드 | 2 (`EXIT_VALIDATION`) | 4 (`EXIT_APP`) |

**구체적으로 비교해 보면 차이가 분명해집니다.**

```python
# 값 문제 — 파일을 안 읽어도 틀렸음을 안다
validators.parse_date("2024-13-45")
# → ValidationError("날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).")

# 상황 문제 — categories.jsonl 을 읽어야 판단된다
service.add(date="2024-01-15", category="없는카테고리", ...)
# → AppError("등록되지 않은 카테고리입니다: 없는카테고리",
#             hint="`category add` 로 먼저 등록하거나 ...")
```

### 1.3 정의 코드

budget_app/errors.py:33-51

```python
class ValidationError(ValueError):
    """입력값이 필드 규칙을 위반했다 — CLI 단에서 사용자 친화 메시지로 변환된다.

    ``ValueError`` 를 상속하는 이유: 의미상 "값이 잘못됨"이 맞고, 이 예외를 모르는
    호출자도 ``except ValueError`` 로 자연스럽게 받을 수 있다.
    """


class AppError(Exception):
    """사용자에게 보여줄 메시지를 가진 애플리케이션 오류.

    스택트레이스 대신 message + hint 형태로 출력된다.
    ``hint`` 는 "그래서 뭘 하면 되는가"를 한 줄로 답하는 자리다.
    """

    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.message = message
        self.hint = hint
```

> **🔎 문법의 출처** — `class ValidationError(ValueError):` 의 괄호는 파이썬 2 시절부터 있는 **상속 문법**이고, 예외 클래스는 반드시 `BaseException` 의 자손이어야 한다는 규칙은 파이썬 3 에서 강제됐습니다(구식 "문자열 예외"는 사라졌습니다). `"""docstring"""` 만 있고 `pass` 가 없는 것도 문법상 정상입니다 — 클래스 본문에 문서화 문자열 하나가 이미 유효한 문장이기 때문입니다.

> **⚙️ 내부 동작 — 상속이 `except` 를 어떻게 통과시키나** — `ValidationError.__mro__` 는 `(ValidationError, ValueError, Exception, BaseException, object)` 입니다(직접 실행해 확인할 수 있습니다). `except ValueError:` 는 CPython 이 던져진 예외 객체와 절의 클래스를 `issubclass` 규칙으로 맞춰 보는데, 그 판정이 이 `__mro__` 를 따라 올라갑니다. 그래서 `ValidationError` 를 **한 번도 본 적 없는 코드**도 `except ValueError` 하나로 받아 냅니다.
>
>     :::python
>     try:
>         raise ValidationError("x")
>     except ValueError as e:
>         type(e).__name__   # 'ValidationError' — 잡히되 타입은 그대로 남는다

> **⚙️ 내부 동작 — `super().__init__(message)` 가 무엇을 하나** — `BaseException.__init__` 은 받은 위치 인자를 그대로 **`self.args` 튜플**에 넣습니다. 그리고 `BaseException.__str__` 은 "args 가 한 개면 그 하나를 `str()` 한 값"을 돌려주도록 정의돼 있습니다. 그래서 `str(AppError("메시지", hint="힌트"))` 는 `'메시지'` 이고, `repr` 은 `AppError('메시지')` 입니다 — **`hint` 는 `args` 에 들어가지 않습니다**(위치 인자로 넘기지 않았으므로). 이 한 줄을 빼먹으면 `args` 가 비어 `str(exc)` 가 `''` 가 되고, 로그의 `%s` 자리가 통째로 사라집니다.
>
> 덧붙이면, 인자 없는 `super()` 는 파이썬 3.0 에 들어온 축약형입니다(파이썬 2 에서는 `super(AppError, self)` 라고 적어야 했습니다). 컴파일러가 메서드 본문에서 `super` 라는 이름을 보면 숨은 변수 `__class__` 를 함께 만들어 주기 때문에 **클래스 본문 안의 메서드에서만** 인자를 생략할 수 있습니다. → [12 §1-B](./12-syntax-and-stdlib.md)

`hint` 를 예외 객체가 들고 다니는 설계가 실용적입니다. 오류를 던지는 쪽이 "그래서 뭘 하면 되는지"를 가장 잘 알기 때문입니다. 잡는 쪽(`handle_errors`)은 그저 있으면 출력합니다.

자세한 처리 흐름은 [06. 횡단 관심사와 예외 처리](./06-decorators.md)에 있습니다.

---

## 2. config.py — 값과 정책

### 2.1 "바꾸면 동작이 달라지는 것"만

> **💡 쉽게 말하면** — 가게 물건마다 가격을 손으로 적어 붙여 두면, 값을 올릴 때 스무 군데를 돌아다녀야 하고 꼭 한 장을 빠뜨립니다. 값은 계산대 뒤 표 한 장에만 적고 나머지는 전부 그 표를 보게 하면, 고칠 곳이 한 군데로 줄어듭니다. `config.py` 가 그 표입니다.
>
> 다만 이 비유는 **표를 몇 장 둘 것인가**에서 깨집니다 — 이 프로젝트는 표를 하나로 두지 않고 계층마다 하나씩 둡니다. 가게 전체가 쓰는 값(가게 이름)만 맨 위 표에 남기고, 주방에서만 쓰는 값은 주방 표로 내려보냈습니다. 아래 docstring 이 그 판단의 근거를 숫자로 적어 둔 자리입니다.

budget_app/config.py:1-20
```python
"""애플리케이션 정체성 — 어느 계층에도 속하지 않는 앱 전역 이름.

## 진입 기준

여기 남는 것은 **"이 프로그램이 무엇으로 불리는가"** 뿐이다. 계층 하나만 쓰는 값은
그 계층의 ``config.py`` 로 내려갔다.

측정 결과가 그 분할을 뒷받침한다 — 이전 ``config.py`` 의 상수 46개 중 39개가
**단일 계층에서만** 쓰였고, ``messages.py`` 는 105개 중 104개가 그랬다. 한 파일에
모아 두면 도메인 검증기가 CLI 프롬프트 71개와 같은 모듈에 묶인다.

계층을 넘나드는 값은 **아래 계층이 소유하고 위 계층이 가져다 쓴다**.

| 값 | 소유 | 소비 |
|---|---|---|
| ``VALID_TYPES`` | ``domain.config`` | domain, cli(argparse choices) |
| ``TAG_SEPARATOR`` | ``domain.config`` | domain, storage(CSV join) |
| ``ON_DUPLICATE_*`` | ``services.config`` | services, cli(argparse choices) |
| ``DEFAULT_TOP_N`` | ``services.config`` | services, cli(기본값) |
"""
```

**판별 테스트**: "이 값을 바꾸면 프로그램이 다르게 *동작*하는가, 다르게 *보이기만* 하는가?"

- `MAX_INPUT_RETRIES = 10` → 5로 바꾸면 재입력 횟수가 달라짐 = **동작** = config
- `PROMPT_DATE = "날짜(YYYY-MM-DD): "` → 영어로 바꿔도 동작 동일 = **표시** = messages

### 2.2 섹션별 정독

**도메인 정책**

budget_app/domain/config.py:8-22

```python
# 도메인 정책 — 거래 타입 어휘
TYPE_INCOME = "income"
TYPE_EXPENSE = "expense"

#: 허용 타입 목록은 위 둘에서 **파생**시킨다. 리터럴을 두 번 적으면 하나만 고치는
#: 사고가 난다(이전에는 VALID_TYPES 가 문자열을 직접 갖고 TYPE_EXPENSE 는 아무도
#: 쓰지 않는 죽은 상수였다).
VALID_TYPES = (TYPE_INCOME, TYPE_EXPENSE)

#: 태그 구분자 — 도메인 규칙이고 CSV 는 이것을 빌려 쓴다(이전 이름: CSV_TAG_SEPARATOR)
TAG_SEPARATOR = ","

# 날짜/월 형식
DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"
```

`TYPE_INCOME` / `TYPE_EXPENSE` 는 리팩터에서 추가됐습니다. 이전에는 `if tx.type == "income":` 처럼 **문자열 리터럴이 로직에 박혀** 있었습니다 — 리터럴이란 코드 안에 값을 그대로 타이핑해 넣은 것을 말합니다. 상수로 뽑으면 오타가 즉시 `AttributeError` 로 드러납니다. `VALID_TYPES` 가 리터럴을 다시 적지 않고 **위 둘에서 파생**되는 것도 같은 이유입니다.

> **🔎 문법의 출처 — 파이썬에는 상수 키워드가 없습니다** — C 의 `const`, 자바의 `final` 에 해당하는 문법이 파이썬에는 없습니다. `TYPE_INCOME = "income"` 은 그냥 **모듈 전역 변수 대입**이고, "상수"라는 것은 전적으로 **PEP 8 의 명명 관례**(모듈 수준 상수는 `UPPER_CASE_WITH_UNDERSCORES`)입니다. 실제로 `domain.config.TYPE_INCOME = "x"` 를 실행하면 그냥 바뀝니다. 대문자는 사람에게 보내는 신호이지 인터프리터에게 보내는 신호가 아닙니다. 그래서 이 프로젝트는 값 자체를 **불변 타입**(`str`/`tuple`/`frozenset`)으로 골라 두 번째 방어선을 만듭니다.

> **🔎 문법의 출처 — `#:` 은 파이썬 문법이 아닙니다** — 파이썬 인터프리터에게 `#:` 은 그냥 주석입니다(`#` 뒤는 전부 무시). 이 표기는 **Sphinx autodoc 의 관례**로, "바로 아래 줄에 오는 이름의 문서화 주석"을 뜻합니다. 변수에는 docstring 을 붙일 문법이 없어서(함수·클래스·모듈만 `__doc__` 을 가집니다) 생긴 우회로입니다. 이 프로젝트는 Sphinx 를 돌리지 않지만, **"이 주석은 아래 상수 하나에 대한 설명"이라는 뜻을 `#:` 이 일반 `#` 주석과 구분해 준다**는 이유로 관례만 빌려 씁니다.

> **⚙️ 내부 동작 — `VALID_TYPES` 가 튜플인 이유** — `parse_type` 은 `v not in config.VALID_TYPES` 로 검사합니다. 튜플의 `in` 은 앞에서부터 훑는 **O(n)** 이지만 원소가 둘이라 문제가 되지 않고, 대신 **불변**이라 누가 실수로 `VALID_TYPES.append(...)` 를 할 수 없습니다(튜플에는 그 메서드 자체가 없습니다). 원소가 많고 `in` 이 잦은 자리에는 같은 이유로 `frozenset` 을 씁니다 — `cli/config.py:19` 의 `FALSY_ENV_VALUES = frozenset({"", "0", "false", "no", "off"})` 가 그 예로, 해시 기반이라 `in` 이 **O(1)** 이고 `frozenset` 자신도 해시 가능해 dict 키·집합 원소로 다시 쓸 수 있습니다(`set` 은 `hash({"a"})` 가 `TypeError` 입니다). → [12 §1-B](./12-syntax-and-stdlib.md)

budget_app/services/budgets.py:50-52

```python
            if tx.type == domain_config.TYPE_INCOME:
                income_total += tx.amount
            else:
```

**저장소/파일** — 파일을 아는 계층이 소유합니다.

budget_app/storage/config.py:16-27

```python
# 파일
TX_FILE_NAME = "transactions.jsonl"
CATEGORY_FILE_NAME = "categories.jsonl"
BUDGET_FILE_NAME = "budgets.jsonl"
#: 발급된 최대 거래 번호를 남기는 파일 — JSONL 이 아니라 숫자 한 줄이다
ID_COUNTER_FILE_NAME = "id_counter"
FILE_ENCODING = "utf-8"
#: 디코딩 불가 바이트를 예외 대신 대리 문자로 받아 **무손실 왕복**시킨다.
#: 읽기와 쓰기가 같은 정책을 쓰므로 손상된 줄이 원문 바이트 그대로 보존된다.
FILE_ERRORS = "surrogateescape"
LINE_TERMINATOR = "\n"
TMP_SUFFIX = ".tmp"
```

`FILE_ENCODING` / `LINE_TERMINATOR` / `TMP_SUFFIX` 도 리팩터에서 뽑았습니다. 이전에는 `open(..., encoding="utf-8", newline="\n")` 처럼 리터럴이 6곳에 흩어져 있었습니다.

**거래 ID 형식**은 파일이 아니라 **도메인 규칙**이라 도메인이 소유합니다.

budget_app/domain/config.py:24-27

```python
# 거래 ID — 형식·검증·발굴 세 패턴이 값 객체(tx_id.TransactionId)와 짝을 이룬다
TX_ID_PATTERN = r"^TX-(\d+)$"
TX_ID_FORMAT = "TX-{:06d}"
TX_ID_SCAN_PATTERN = r'"id"\s*:\s*"(TX-\d+)"'
```

ID 관련 상수가 **셋**인 것이 리팩터의 흔적입니다. 셋을 쓰는 코드는 전부 값 객체(값 하나를 감싸서 그 값이 지켜야 할 규칙까지 함께 지니게 만든 작은 타입) `TransactionId` 안에 있습니다([§4.4](#44-transactionid--값-객체로-모은-거래-id)).

| 상수 | 역할 |
|---|---|
| `TX_ID_FORMAT` | 만들 때 — `"TX-{:06d}".format(7)` → `"TX-000007"` |
| `TX_ID_PATTERN` | 검증할 때 — 전체가 이 형식인가 (`^...$`) |
| `TX_ID_SCAN_PATTERN` | 발굴할 때 — 깨진 줄에서도 id 를 찾아냄 |

> **🔎 문법의 출처 — `r"..."`** — 앞에 붙은 `r` 은 **raw string literal** 표기로, 파이썬 1.5 부터 있는 오래된 문법입니다. `\` 를 이스케이프 시작으로 해석하지 않고 글자 그대로 둡니다. 정규식은 `\d`·`\s` 처럼 백슬래시를 쓰는데, `r` 없이 `"^TX-(\d+)$"` 라고 적으면 **파이썬 문자열 단계**에서 `\d` 를 먼저 해석하려 듭니다(현재는 경고, 미래 버전에서는 오류). `re` 모듈 문서가 정규식 패턴에 항상 raw string 을 쓰라고 권하는 이유입니다. `TX_ID_SCAN_PATTERN` 이 바깥을 작은따옴표로 감싼 것도 패턴 안에 `"` 가 들어 있어 이스케이프를 피하려는 것입니다.

> **🔎 문법의 출처 — `"TX-{:06d}"`** — `str.format` 과 그 안의 `{:06d}` 형식 지정 미니 언어는 PEP 3101 로 파이썬 2.6 에 들어왔습니다. 그 전에는 `"TX-%06d" % n` 이 유일한 방법이었습니다. `:` 뒤가 형식 지정자이고 `0`=0으로 채우기, `6`=최소 폭, `d`=10진 정수라는 뜻입니다. 이 프로젝트가 여기서 f-string 을 못 쓰는 이유는 명확합니다 — **f-string 은 정의되는 자리에서 즉시 값을 채우는 문법**이라 "나중에 채울 템플릿"을 상수로 보관할 수 없습니다. 그래서 템플릿 상수는 전부 `str.format` 스타일입니다. → [12 §1-A](./12-syntax-and-stdlib.md)

**CSV 교환 스키마** — 파일 형식이므로 저장소가 소유합니다.

budget_app/storage/config.py:36-45

```python
# CSV 교환 스키마 — `id` 는 **선택** 컬럼이다(왕복 시 중복 방지, 외부 CSV 호환 유지)
#: 쓰기는 BOM 없는 UTF-8 고정(왕복 안전성). 읽기만 utf-8-sig 로 BOM 을 흡수한다 —
#: 엑셀이 저장한 CSV 는 BOM 이 붙고, 그러면 첫 컬럼명이 깨져 헤더 검증이 실패한다.
CSV_ENCODING = "utf-8"
CSV_READ_ENCODING = "utf-8-sig"
CSV_ID_COLUMN = "id"
CSV_FIELDS = ("id", "date", "type", "category", "amount", "memo", "tags")
CSV_FIELDS_WITHOUT_ID = ("date", "type", "category", "amount", "memo", "tags")
CSV_REQUIRED_COLUMNS = ("date", "type", "category", "amount")
CSV_DATA_START_LINE = 2  # 1행은 헤더
```

**`CSV_FIELDS` 와 `CSV_REQUIRED_COLUMNS` 가 다르다**는 점이 스키마 설계의 핵심입니다. 내보낼 때는 7컬럼을 쓰지만, 가져올 때 **요구하는 것은 4개**뿐입니다. 그래서 `id` 를 추가해도 기존 CSV 가 그대로 들어옵니다.

태그 구분자는 이 목록에 없습니다 — 예전 `CSV_TAG_SEPARATOR` 는 `domain/config.py:18` 의 `TAG_SEPARATOR` 로 내려갔습니다. "태그를 무엇으로 나누는가"는 CSV 사정이 아니라 **도메인 규칙**이고, CSV 는 그것을 빌려 쓸 뿐입니다.

**중복 정책**은 서비스가 판단하므로 서비스가 소유합니다.

budget_app/services/config.py:8-13

```python
# 가져오기 — 이미 존재하는 id 를 만났을 때의 정책
ON_DUPLICATE_SKIP = "skip"
ON_DUPLICATE_NEW_ID = "new-id"
ON_DUPLICATE_ERROR = "error"
ON_DUPLICATE_CHOICES = (ON_DUPLICATE_SKIP, ON_DUPLICATE_NEW_ID, ON_DUPLICATE_ERROR)
DEFAULT_ON_DUPLICATE = ON_DUPLICATE_SKIP
```

`ON_DUPLICATE_CHOICES` 는 argparse(파이썬이 기본으로 갖고 있는 명령줄 옵션 해석기)의 `choices=` 에 그대로 넘어갑니다(budget_app/cli/parser.py:226-231). **선택지 목록과 상수가 같은 자리에 있으므로** 정책을 추가할 때 한 곳만 고치면 됩니다.

argparse 는 값을 변환한 뒤 `value not in choices` 를 검사해 걸리면 그 자리에서 프로그램을 끝냅니다(종료 코드 2). 즉 잘못된 `--on-duplicate` 는 서비스에 도달하지 않습니다 — 서비스 쪽 `ERR_UNKNOWN_DUPLICATE_POLICY` 방어는 CLI 가 아닌 경로로 직접 호출됐을 때를 위한 것입니다(→ [09 §2](./09-cli.md)).

**CLI 한도**

budget_app/cli/config.py:12-15

```python
# 기본값 / 한도
DEFAULT_DATA_DIR = "./data"
MAX_INPUT_RETRIES = 10
DEFAULT_LIST_LIMIT = 20
```

budget_app/services/config.py:15-17

```python
# 한도·기본값
MAX_IMPORT_ERRORS = 5
DEFAULT_TOP_N = 5
```

`MAX_IMPORT_ERRORS = 5` 는 "오류 메시지를 앞에서 5개까지만 모은다"는 뜻입니다. 1만 줄짜리 CSV 가 전부 깨졌을 때 오류 목록으로 화면을 도배하지 않기 위한 상한입니다. 다만 **개수는 전부 세되 메시지만 자릅니다**(budget_app/services/importexport.py:45-53).

**종료 코드** — 셸에게 무엇을 말할지는 CLI 가 바깥 세계와 맺은 **계약**(반드시 이렇게 하기로 정해 둔 약속)입니다.

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

### 2.3 함수도 클래스도 없습니다

다섯 개의 `config.py` 어디에도 `def` 나 `class` 가 없습니다. 루트 `config.py` 는 상수 하나(25줄)뿐이고, 나머지 넷도 값 선언과 주석뿐입니다(`domain` 27줄, `storage` 45줄, `cli` 29줄, `services` 17줄). 이 제약 덕분에 어느 모듈이 import 해도 **순환 참조가 원리적으로 불가능**합니다.

> **💡 쉽게 말하면** — 두 사람이 서로에게 "네 준비가 끝나면 알려 줘, 그때 시작할게"라고 말하면 아무도 시작하지 못합니다. 파일끼리도 비슷한 일이 벌어집니다 — A 가 B 를 가져다 쓰려는데 B 가 다시 A 를 가져다 쓰려 하면, 뒤늦게 A 를 붙잡는 B 쪽이 아직 다 만들어지지 않은 A 를 보게 됩니다. 반쯤 만들어진 것을 보는 쪽은 나중에 도는 한쪽뿐입니다 — B 는 자기 할 일을 끝까지 마치므로, A 가 나중에 보는 B 는 멀쩡합니다. 계층별 `config.py` 는 많아야 **아무것도 import 하지 않는 루트 `config.py`** 하나만 물어보는 파일이라(`domain`·`services` 는 그마저도 없습니다) 이렇게 되돌아올 일이 없습니다.
>
> 다만 이 비유는 **결말**에서 깨집니다 — 파이썬은 두 사람처럼 영원히 기다리지 않고, 반쯤 만들어진 파일을 그대로 넘겨줍니다. 그래서 "그런 이름이 없다"는 `AttributeError` 나 `ImportError` 로 터지는데, 하필 그 이름을 실제로 꺼내 쓰는 순간까지 조용할 수도 있어 더 성가십니다.

> **⚙️ 내부 동작 — import 가 실제로 무슨 일을 하나** — `import budget_app.domain.config` 는 (1) `sys.modules` 에 이미 있으면 그것을 그대로 돌려주고, (2) 없으면 파일을 찾아 컴파일한 뒤 **모듈 본문을 위에서 아래로 한 번 실행**합니다. 그 실행 결과 만들어진 전역 이름들이 모듈 객체의 속성이 됩니다. 즉 `TYPE_INCOME = "income"` 은 "선언"이 아니라 **import 시점에 실제로 실행되는 대입문**입니다.
>
> 순환 참조는 이 "본문 실행" 도중에 A 가 B 를, B 가 다시 A 를 import 하려 할 때 생깁니다(반쯤 만들어진 모듈을 보게 됩니다). 계층별 `config.py` 는 본문이 **값 대입뿐**이고, import 하는 것도 많아야 "아무것도 import 하지 않는 루트 `config.py`" 하나라(`domain`·`services` 는 그마저도 없습니다) 그런 되돌아옴이 구조적으로 불가능합니다. 참고로 `.pyc` 캐시는 (2)의 컴파일만 건너뛸 뿐 **본문 실행은 매 프로세스마다** 다시 일어납니다. → [12 §1-A](./12-syntax-and-stdlib.md)

---

## 3. messages.py — 사용자에게 보이는 모든 글자

### 3.1 원칙

budget_app/cli/messages.py:1-10
```python
"""CLI 계층의 사용자 노출 문자열 — 전체의 3분의 2가 여기 있다.

프롬프트·결과·오류 표시가 전부 이 계층의 것이다. 이전에는 도메인 검증 메시지 7개와
이 71개가 한 파일에 있어서, ``domain/validators.py`` 가 CLI 한국어 문구까지 들어 있는
모듈에 의존했다.

동적 부분은 ``str.format`` 템플릿으로 둔다. **로그 포맷만 %-스타일**인데, ``logging``
에 인자를 그대로 넘겨야 레벨이 꺼져 있을 때 포매팅 비용이 발생하지 않기 때문이다.
argparse 의 인자별 ``help`` 는 인자 정의 옆에 두는 편이 읽기 좋아 ``parser.py`` 에 남겼다.
"""
```

> **💡 쉽게 말하면** — 손님이 올지 안 올지 모르는데 상을 미리 차려 두면, 안 오면 그 수고가 통째로 버려집니다. `logger.debug(f"...")` 는 상을 먼저 차리는 쪽입니다 — 로그를 꺼 두었어도 문장은 이미 완성돼 있습니다. `logger.debug("...%s", line)` 은 재료만 건네 두고, 정말 내가야 할 때에야 차립니다.
>
> 다만 이 비유는 **수고의 크기**에서 깨집니다 — 문자열 하나 만드는 비용은 아주 작아서 한두 번으로는 티가 나지 않습니다. 파일을 줄 단위로 훑는 반복문처럼 같은 자리를 수만 번 지날 때라야 차이가 드러납니다.

> **⚙️ 내부 동작 — 왜 로그만 `%`-스타일인가** — `logger.debug("깨진 줄: %s", line)` 은 문자열을 **미리 만들지 않습니다.** `logging` 은 먼저 `isEnabledFor(DEBUG)` 로 레벨을 확인해 꺼져 있으면 그 자리에서 돌아갑니다. 통과했을 때만 `LogRecord` 를 만들어 `msg` 와 `args` 를 따로 보관하고, 실제 문자열 결합은 핸들러가 `record.getMessage()`(내부적으로 `msg % self.args`)를 부르는 **출력 직전**에 일어납니다. 그래서 `logger.debug(f"깨진 줄: {line}")` 로 적으면 레벨이 꺼져 있어도 f-string 이 이미 평가돼 이 이득이 통째로 사라집니다. 사용자 메시지는 반드시 화면에 나가므로 지연시킬 이유가 없어 `str.format` 스타일을 씁니다. → [12 §2-B](./12-syntax-and-stdlib.md)

### 3.2 접두사가 곧 용도

| 접두사 | 의미 | 예 |
| --- | --- | --- |
| `MSG_` | 사용자에게 보여줄 완성 문장 | `MSG_SAVED_TX` |
| `ERR_` | 오류 메시지 (예외에 실림) | `ERR_TX_NOT_FOUND` |
| `HINT_` | 해결 힌트 (오류와 짝) | `HINT_LIST_ID` |
| `PROMPT_` | 대화형 입력 프롬프트 | `PROMPT_DATE` |
| `FMT_` | 반복 출력용 한 줄 템플릿 | `FMT_TX_LINE` |
| `LOG_` | 로그 메시지 (%-스타일) | `LOG_CORRUPT_LINE` |
| `MODE_` | 모드 표시 문자열 | `MODE_ATOMIC` |

**`ERR_` 과 `HINT_` 가 짝을 이룬다**는 점이 이 프로젝트 오류 UX 의 뼈대입니다.

budget_app/services/messages.py:9-9

```python
ERR_CATEGORY_NOT_REGISTERED = "등록되지 않은 카테고리입니다: {name}"
```

같은 오류라도 **문맥에 따라 힌트가 다릅니다.** `ERR_CATEGORY_NOT_REGISTERED` 는 두 곳에서 쓰이는데, `add` 에서는 `HINT_CATEGORY_ADD_OR_LIST`(목록 확인도 안내), `update` 에서는 `HINT_CATEGORY_ADD`(등록만 안내)를 씁니다. 사용자가 이미 목록을 봤을 가능성이 다르기 때문입니다.

### 3.3 리팩터에서 추가된 메시지

| 상수 | 왜 필요해졌나 |
|---|---|
| `ERR_TX_ID_INVALID` | CSV 가 `id` 컬럼을 실어 오면서 id 형식 검증이 생김 |
| `ERR_DUPLICATE_ID` / `HINT_DUPLICATE_ID` | `--on-duplicate error` 정책 |
| `FMT_IMPORT_DUPLICATE` | 중복 사유를 오류와 **구분해서** 보여주기 위해 |
| `MSG_IMPORT_DUPLICATE_HINT` | "중복은 고칠 필요 없다"를 명시 |
| `ERR_CSV_NO_HEADER` / `HINT_CSV_NO_HEADER` | 빈 CSV 를 "필수 컬럼 없음"이 아니라 정확히 안내 |
| `LOG_CORRUPT_PRESERVED` | 손상 줄을 보존했음을 알림 |

`MSG_IMPORT_DONE` 도 바뀌었습니다.

budget_app/cli/messages.py:92-94

```python
MSG_IMPORT_DONE = (
    "[완료] mode={mode}, imported={imported}, duplicated={duplicated}, skipped={skipped}"
)
```

`duplicated` 가 추가된 이유는 **사용자가 해야 할 일이 다르기** 때문입니다. `skipped` 는 CSV 를 고쳐야 하고, `duplicated` 는 아무것도 안 해도 됩니다. 한 숫자로 합치면 정상 왕복이 실패처럼 읽힙니다.

---

## 4. validators.py — 규칙 하나 = 함수 하나

### 4.1 리팩터 배경

budget_app/domain/validators.py:1-2

```python
"""필드 규칙 — "이 값이 유효한가"를 판단하는 단 하나의 정의처.

```

### 4.2 일곱 개의 규칙

> **💡 쉽게 말하면** — 공연장 입구의 검표원을 떠올리면 됩니다. 표에 적힌 날짜가 날짜 모양을 갖췄는지, 좌석 번호가 있을 법한 모양인지를 봅니다. 그 날짜가 오늘인지 지난 공연인지까지는 보지 않습니다 — 표 한 장만 보고 알 수 있는 것이 아니니까요(그래서 `parse_date` 도 `1899-01-01` 이나 `2999-12-31` 을 그대로 통과시킵니다). 그 좌석에 이미 누가 앉아 있는지도 검표원이 알 수 없고, 그건 안에 들어가 봐야 압니다(그것이 §1.2 의 "상황 오류"입니다). 그리고 이 검표원은 확인하는 김에 접힌 귀퉁이를 펴 주기까지 합니다 — 앞뒤 공백을 떼고 대문자를 소문자로 바꾸는 **정규화**가 그것입니다.
>
> 다만 이 비유는 **표를 돌려주는 방식**에서 깨집니다 — 검표원은 받은 표를 그대로 돌려주지만, 이 함수들은 받은 값 대신 **다듬어 만든 새 값**을 돌려줍니다. 그래서 "통과했으니 됐다"며 반환값을 버리고 원래 값을 그대로 쓰면 정규화가 통째로 사라집니다.

| 함수 | 검증하는 것 | 정규화하는 것 | 빈 값 |
|---|---|---|---|
| `parse_amount` | 양의 정수 | 문자열 → int | 오류 |
| `parse_type` | `income`/`expense` | strip + lower | 오류 |
| `parse_date` | `YYYY-MM-DD` | strip | 오류 |
| `parse_month` | `YYYY-MM` | strip | 오류 |
| `parse_category` | 비어 있지 않음 | strip | 오류 |
| `parse_memo` | (없음) | strip, None → `""` | **허용** |
| `parse_tags` | 구분자 미포함 | 쉼표 분리, 빈 항목 제거, 순서 보존 중복 제거 | **허용** |

> **거래 id 규칙은 이 표에 없습니다.** 예전에는 `validators.parse_tx_id` / `validators.tx_id_number` 두 함수가 여기 있었지만, 형식 검증뿐 아니라 번호 변환·생성·손상 줄 발굴이라는 **고유 행동**이 붙어 있어 값 객체 `TransactionId` 로 옮겼습니다([§4.4](#44-transactionid--값-객체로-모은-거래-id)). **지금 소스에 그 두 이름은 없습니다** — 각각 `domain/tx_id.py` 의 `TransactionId.parse`(클래스메서드)와 `TransactionId.number`(property)가 그 자리를 대신합니다. "규칙이 함수 하나로 끝나는" 필드만 이 표에 남습니다.

**빈 값 허용 여부가 필드마다 다르다**는 점을 눈여겨보세요. 메모와 태그는 없어도 되는 정보라 오류가 아니고, 나머지는 필수입니다. 이 정책이 함수 안에 들어 있어서 호출부는 신경 쓸 필요가 없습니다.

### 4.3 대표 코드

검증기가 쓰는 정규식(문자열이 어떤 모양이어야 하는지를 짧은 기호로 적어 둔 규칙)은 **모듈 최상위에서 한 번** 컴파일합니다 — 컴파일이란 그 기호 규칙을 미리 해석해 두는 준비 작업입니다.

budget_app/domain/validators.py:36-37

```python
#: 금액으로 받아들일 표기 — ``\d`` 가 아니라 ``[0-9]`` 인 것이 중요하다(아래 참조)
_INTEGER = re.compile(r"^[+-]?[0-9]+$")
```

> **⚙️ 내부 동작 — `re.compile` 을 왜 최상위에서 하나** — `re.compile(pattern)` 은 패턴 문자열을 파싱해 바이트코드로 바꾸고 `re.Pattern` 객체로 돌려줍니다. 사실 `re.match(패턴, 문자열)` 처럼 매번 문자열을 넘겨도 CPython 은 `re._compile` 안의 **내부 캐시**(딕셔너리 `re._cache`, 키는 `(타입, 패턴, 플래그)`)에 컴파일 결과를 넣어 두고 재사용합니다 — 로컬 3.13.1 에서 상한은 `re._MAXCACHE = 512` 이고, 가득 차면 가장 오래 안 쓴 항목부터 버립니다(LRU). 그래도 최상위에서 미리 컴파일하는 편이 나은 이유는 셋입니다. (1) 캐시 조회(패턴 문자열 해시 계산)조차 생략됩니다. (2) **패턴 오타가 import 시점에 즉시 터집니다** — 검증 함수가 처음 불리는 런타임까지 숨지 않습니다. (3) 패턴에 이름을 붙일 수 있어 `_INTEGER.match(...)` 가 정규식 문자열보다 읽기 쉽습니다. `domain/tx_id.py:45,48` 의 `_EXACT`/`_SCAN` 도 같은 이유로 최상위에 있습니다. → [12 §2-A](./12-syntax-and-stdlib.md)

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

**두 종류의 실패를 구분**합니다 — "정수가 아님"과 "정수지만 0 이하". 메시지가 다르므로 사용자가 무엇을 고쳐야 하는지 정확히 압니다.

> **⚙️ 내부 동작 — `\d` 는 아스키 숫자가 아닙니다 (실행으로 확인)** — 파이썬 3 의 정규식은 **기본이 유니코드 모드**라 `\d` 가 `Nd`(십진 숫자) 범주 전체와 맞습니다. 아랍-인도 숫자 `١٢٣` 도 여기 포함되고, `int()` 는 그것을 군말 없이 `123` 으로 바꿉니다.
>
>     :::python
>     >>> import re
>     >>> re.match(r"^[+-]?\d+$", "١٢٣") is not None
>     True
>     >>> re.match(r"^[+-]?[0-9]+$", "١٢٣") is not None
>     False
>     >>> int("١٢٣")
>     123
>
> 그래서 `_INTEGER` 는 `\d` 가 아니라 `[0-9]` 를 씁니다. `re.compile(r"^[+-]?\d+$", re.ASCII)` 로 플래그를 주는 길도 있지만, **패턴만 읽어도 의도가 드러나는** 쪽을 골랐습니다. 한편 `int()` 를 그냥 쓰지 않는 또 다른 이유는 `int("1_000") == 1000` 입니다 — 밑줄 숫자 리터럴은 파이썬 **소스 문법**이지 사용자가 친 금액이 아닌데, `int()` 는 문자열에서도 그것을 받아 줍니다. → [12 §2-A](./12-syntax-and-stdlib.md)

> **🔎 문법의 출처 — `value: Any` 와 `-> int`** — 함수 시그니처의 타입 표기는 PEP 3107(파이썬 3.0, 임의의 어노테이션)과 PEP 484(파이썬 3.5, 타입 힌트로서의 의미 확정)에서 왔습니다. **런타임에는 아무 검사도 하지 않습니다** — `parse_amount("가")` 를 부르면 어노테이션은 조용하고 `_INTEGER.match` 가 걸러 냅니다. 즉 이 프로젝트에서 어노테이션은 사람과 타입체커를 위한 것이고, **실제 강제는 전부 `validators` 함수 본문**이 합니다. 이 둘을 혼동하는 것이 구술 시험에서 가장 흔한 함정입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

**`parse_date` — 이 문서에서 가장 중요한 여섯 줄.**

> **💡 쉽게 말하면** — 주소록에 "서울시 강남구"와 "서울특별시 강남구"가 섞여 있다고 해 봅시다. 사람 눈에는 같은 곳이지만, 기계가 "서울특별시로 시작하는 것"만 골라 세면 앞의 것은 빠집니다. 접수하는 순간 정식 표기로 고쳐 적어 두면 이 일이 생기지 않습니다. `parse_date` 가 하는 일이 정확히 그것입니다 — `"2024-1-5"` 로 들어와도 `"2024-01-05"` 로 고쳐 적은 뒤에야 저장됩니다.
>
> 다만 이 비유는 **잘못 적혔을 때의 결말**에서 깨집니다 — 주소는 틀리게 적혀도 집배원이 알아서 찾아가 주지만, 여기서는 아무도 알아채지 못합니다. 오류 메시지 한 줄 없이 1월 요약의 합계만 조용히 틀립니다.

budget_app/domain/validators.py:80-99

```python
def parse_date(value: Any) -> str:
    """날짜를 검증하고 **정규형 ``YYYY-MM-DD`` 로 재직렬화**한다.
    ...
    """
    v = str(value or "").strip()
    try:
        dt = datetime.strptime(v, config.DATE_FORMAT)
    except ValueError as exc:
        raise ValidationError(messages.ERR_DATE_INVALID) from exc
    return dt.strftime(config.DATE_FORMAT)
```

마지막 줄이 핵심입니다. **파싱한 `datetime` 을 버리고 원문을 돌려주는 것이 아니라, 파싱 결과를 다시 찍어서 돌려줍니다.** 왜 그래야 하는지는 `strptime` 이 무엇을 통과시키는지 보면 드러납니다.

> **⚙️ 내부 동작 — `strptime` 은 검증기이지 정규화기가 아닙니다 (실행으로 확인)** — `datetime.strptime` 은 `_strptime` 모듈로 넘어가고, 그곳에서 형식 문자열을 **정규식으로 번역**한 뒤 매칭합니다(번역 결과는 `_strptime._regex_cache` 에 최대 5개까지 캐시됩니다). `"%Y-%m-%d"` 가 실제로 무엇이 되는지 꺼내 볼 수 있습니다.
>
>     :::python
>     >>> import _strptime, datetime
>     >>> datetime.datetime.strptime("2024-01-05", "%Y-%m-%d")   # 캐시를 채우려고 한 번 호출
>     datetime.datetime(2024, 1, 5, 0, 0)
>     >>> _strptime._regex_cache["%Y-%m-%d"].pattern
>     '(?P<Y>\\d\\d\\d\\d)-(?P<m>1[0-2]|0[1-9]|[1-9])-(?P<d>3[0-1]|[1-2]\\d|0[1-9]|[1-9]| [1-9])'
>
> `%m` 이 `1[0-2]|0[1-9]|[1-9]` 입니다 — **마지막 갈래 `[1-9]` 가 한 자리 월을 허용합니다.** `%d` 는 한술 더 떠 `| [1-9]`(공백+한 자리)까지 받습니다. 그래서 이렇게 됩니다.
>
>     :::python
>     >>> datetime.datetime.strptime("2024-1-5", "%Y-%m-%d")
>     datetime.datetime(2024, 1, 5, 0, 0)          # 오류가 아니다
>     >>> datetime.datetime.strptime("2024-01- 5", "%Y-%m-%d")
>     datetime.datetime(2024, 1, 5, 0, 0)          # 이것도 통과한다

이것을 그대로 저장하면 어떤 일이 벌어지는지가 이 프로젝트의 설계 근거입니다. 이 프로그램은 날짜를 **문자열로 비교**합니다(ISO 8601 이라 사전순 = 날짜순이라는 전제).

```python
>>> "2024-1-5" <= "2024-01-31"
False        # 1월 5일이 1월 31일보다 "크다"고 판정된다
```

즉 `2024-1-5` 로 들어온 거래가 1월 요약·검색·내보내기에서 **오류 하나 없이 조용히 사라집니다.** `strftime` 이 그것을 막는 방식은 단순합니다 — `%m`/`%d` 는 **출력할 때는 언제나 2자리 0채움**이라, 어떤 표기로 들어왔든 나갈 때는 하나로 수렴합니다.

```python
>>> datetime.datetime.strptime("2024-1-5", "%Y-%m-%d").strftime("%Y-%m-%d")
'2024-01-05'
```

`strptime` → `strftime` 왕복이 **정규화 장치**인 것이지, `strftime` 이 추가 검증을 하는 것은 아닙니다. 검증은 `strptime` 이 하고(달의 실제 일수까지 봅니다 — `2024-02-30` 은 `ValueError`), 표기 통일은 `strftime` 이 합니다. 기존 파일에 남아 있던 비정규 표기도 읽는 순간 `__post_init__` → `parse_date` 를 다시 지나므로 **자동으로 치유**됩니다. `parse_month` 도 같은 구조이고, 예산은 월 문자열이 사실상 키라 영향이 더 직접적입니다(`budget set --month 2024-1` 로 넣은 값을 `summary --month 2024-01` 이 못 찾던 버그).

> **🔎 문법의 출처 — `raise ... from exc`** — 명시적 예외 연쇄는 PEP 3134 로 파이썬 3.0 에 들어왔습니다. `from exc` 는 새 예외의 `__cause__` 속성에 원래 예외를 매답니다. 그러면 트레이스백이 "The above exception was the direct cause of the following exception" 으로 두 예외를 이어서 보여 줍니다. `from` 을 생략해도 `except` 블록 안에서 raise 하면 `__context__` 에 자동으로 매달리지만(암묵적 연쇄), 그때는 "During handling of the above exception, another exception occurred" 로 표시돼 **의도한 변환인지 예외 처리 중 사고인지 구분되지 않습니다.** `--debug` 로 트레이스백을 볼 때 이 차이가 드러납니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `str(value or "")` 관용구, 함정까지** — `or` 는 불리언이 아니라 **피연산자 중 하나를 그대로 돌려주는 연산자**입니다(`a or b` 는 `a` 가 참 같으면 `a`, 아니면 `b`). 그래서 `str(value or "")` 는 "`None` 이면 빈 문자열로, 아니면 그 값을 문자열로" 라는 뜻이 됩니다. `str(None)` 이 `'None'` 이라는 **문자열 네 글자**가 되는 사고를 막는 것이 목적입니다.
>
> 함정은 `or` 가 `None` 만이 아니라 **모든 거짓 같은 값**을 걸러 낸다는 점입니다.
>
>     :::python
>     >>> [str(v or "") for v in (None, 0, "", False, [], "0")]
>     ['', '', '', '', '', '0']
>
> `0` 과 `False` 와 `[]` 가 전부 `""` 가 됩니다. 날짜·카테고리·메모에서는 "빈 값"이 맞는 처리라 문제가 없지만, **금액에서는 치명적입니다** — 그래서 `parse_amount` 만 `str(value or "")` 가 아니라 **`str(value)`** 를 씁니다(validators.py:64). 만약 여기도 `or ""` 를 썼다면 `parse_amount(0)` 이 `""` 가 되어 "금액은 정수여야 합니다"라는 **틀린 이유**가 나갔을 것입니다. 지금은 `"0"` 이 정규식을 통과하고 `n <= 0` 에서 걸려 "양의 정수여야 합니다"라는 맞는 이유가 나갑니다. 같은 관용구를 어디에 쓰고 어디에 쓰지 않았는지가 의도적이라는 점을 보여 주는 자리입니다.

budget_app/domain/validators.py:128-158

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

**입력 형태가 셋**입니다 — CSV·대화형에서 오는 **쉼표 문자열**, JSON 에서 읽은 **리스트**, 그리고 엔티티(파일에 저장되는 데이터 한 건을 나타내는 객체)가 이미 정규화해 둔 **튜플**(`Transaction.tags`). `isinstance` 로 갈라 한 함수가 셋 다 받습니다. 이 덕분에 호출부(엔티티의 `__post_init__`)는 어디서 온 값인지 몰라도 됩니다.

세 번째 갈래가 빠지면 조용히 데이터가 망가집니다. "리스트가 아니면 문자열"로 떨어뜨렸다면 튜플 `("a","b")` 가 `str(...)` 을 거쳐 `"('a', 'b')"` 가 되고, 쉼표로 쪼개져 `["('a'", "'b')"]` 가 됩니다. 기본값 `()` 는 `["()"]` 가 되고요. **오류가 나지 않고 값만 바뀌는** 부류라 특히 위험합니다.

> **⚙️ 내부 동작 — `isinstance(value, Iterable)` 은 상속을 보지 않습니다** — 여기서 `Iterable` 은 `collections.abc.Iterable` 이고, 보통의 클래스가 아니라 **추상 베이스 클래스(ABC)** 입니다(PEP 3119). ABC 는 `__subclasshook__` 을 정의해 `isinstance` 판정을 가로챌 수 있고, `Iterable` 의 훅은 "이 타입에 `__iter__` 가 있는가"만 봅니다. 그래서 `Iterable` 을 **상속한 적 없는** `list`·`tuple`·`set`·제너레이터가 전부 참이 됩니다 — 이것이 파이썬의 덕 타이핑을 `isinstance` 로 물어보는 표준적인 방법입니다.
>
> 중요한 함정: **`str` 도 `__iter__` 를 가지므로 `Iterable` 입니다.** 그래서 코드가 `isinstance(value, str)` 을 **먼저** 검사합니다 — 순서가 반대였다면 `"a,b"` 가 문자열 분리 대신 한 글자씩 순회돼 `["a", ",", "b"]` 가 됐을 것입니다. `if`/`elif` 의 순서 자체가 버그 방지 장치입니다. → [12 §1-B](./12-syntax-and-stdlib.md)

### 4.4 `TransactionId` — 값 객체로 모은 거래 id

> **💡 쉽게 말하면** — 도서관에서 책마다 번호를 손으로 적으면 "7번", "007", "제7번"이 뒤섞입니다. 대신 번호를 기계에 넣고 스티커를 뽑아 붙이면, 정해진 투입구에 넣기만 하면 나오는 스티커는 늘 같은 규격입니다. `TransactionId` 가 그 스티커 기계입니다 — 번호 `7` 로 만들든(`TransactionId.of(7)`) 문자열 `"TX-7"` 로 만들든(`TransactionId.parse("TX-7")`) 결과는 `TX-000007` 하나뿐이고, 한 번 만들어진 것은 고쳐 쓸 수 없습니다. 다만 투입구는 넣는 것에 따라 다릅니다 — 정수는 `of` 로만 들어갑니다. 생성자에 `TransactionId(7)` 처럼 숫자를 그냥 넣으면 형식이 틀렸다며 거절당합니다.
>
> 다만 이 비유는 **떼어낼 수 없다**는 데서 깨집니다 — 파이썬의 "고칠 수 없음"에는 `object.__setattr__` 이라는 뒷문이 있고, 이 클래스 자신도 처음 값을 채울 때 그 문을 씁니다(아래 상자). 실수로 바꾸는 것을 막는 장치이지, 작정하고 바꾸는 것까지 막는 장치는 아닙니다.

budget_app/domain/tx_id.py:51-127
```python
@functools.total_ordering
@dataclass(frozen=True)
class TransactionId:
    """``TX-000001`` 형식의 거래 식별자 — 만들어지는 순간 **정규형**이 된다.
    ...
    """

    value: str

    def __post_init__(self) -> None:
        # frozen dataclass 라 object.__setattr__ 로 정규화한다.
        v = str(self.value or "").strip()
        m = _EXACT.match(v)
        if not m:
            raise ValidationError(messages.ERR_TX_ID_INVALID.format(value=v))
        object.__setattr__(self, "value", config.TX_ID_FORMAT.format(int(m.group(1))))

    def __lt__(self, other: Any) -> Any:
        """번호 순서로 비교한다. ``total_ordering`` 이 나머지 셋을 채운다."""
        if not isinstance(other, TransactionId):
            return NotImplemented
        return self.number < other.number

    # ---------- 생성 ----------

    @classmethod
    def of(cls, number: int) -> TransactionId:
        """번호로부터 만든다 — ``7`` → ``TX-000007``."""
        return cls(config.TX_ID_FORMAT.format(number))

    @classmethod
    def parse(cls, value: Any) -> TransactionId:
        """검증하며 만든다. 실패는 ``ValidationError``."""
        return cls(str(value or "").strip())

    @classmethod
    def scan(cls, raw_text: str) -> TransactionId | None:
        """줄 원문에서 id 를 발굴한다 — 찾지 못하면 ``None``.

        JSON 파싱조차 실패한 줄에도 id 는 들어 있을 수 있고, 그 번호는 **이미 쓰인
        번호**다. 놓치면 재발급으로 중복 id 가 생긴다.
        """
        m = _SCAN.search(raw_text)
        return cls(m.group(1)) if m else None

    # ---------- 조회 ----------

    @property
    def number(self) -> int:
        """``TX-000007`` → ``7``."""
        return int(_EXACT.match(self.value).group(1))

    def __str__(self) -> str:
        return self.value
```

> **🔎 문법의 출처 — 데코레이터 두 개가 쌓인 순서** — `@A` `@B` `class C` 는 파이썬이 `C = A(B(C))` 로 **desugar** 합니다(아래에서 위로 적용). 그래서 `@dataclass(frozen=True)` 가 먼저 `__init__`·`__eq__`·`__hash__`·`__setattr__` 을 만들어 붙이고, 그 결과 클래스를 `@functools.total_ordering` 이 받습니다. 순서가 반대였다면 `total_ordering` 이 `__lt__` 밖에 없는 클래스를 보게 되는데 — 이 경우에는 `__lt__` 를 우리가 직접 썼으므로 결과가 같지만, `dataclass(order=True)` 를 썼다면 순서가 결과를 바꿉니다. 클래스 데코레이터 문법은 파이썬 2.6(함수용은 2.4)부터 있습니다.

> **⚙️ 내부 동작 — `functools.total_ordering` 이 실제로 하는 일** — 이 데코레이터는 클래스에 정의된 비교 메서드(`__lt__`/`__le__`/`__gt__`/`__ge__`) 중 **있는 것 하나**를 찾아, 나머지 셋을 그것으로 조합한 함수로 채워 넣습니다. 여기서는 `__lt__` 하나로 나머지 셋이 생깁니다 — 예컨대 `__gt__` 는 `not (self < other) and self != other` 로 조립됩니다. `__eq__` 는 채워 주지 않는데, 그건 `dataclass` 가 이미 필드 비교로 만들어 두었습니다(그래서 `total_ordering` 과 `dataclass` 는 서로의 빈자리를 메웁니다).
>
> `__lt__` 가 타입이 다르면 `NotImplemented` 를 **돌려주는**(raise 가 아닙니다) 것도 프로토콜입니다. 파이썬은 `a < b` 에서 `a.__lt__(b)` 가 `NotImplemented` 를 반환하면 **반사 연산** `b.__gt__(a)` 를 시도하고, 그것도 실패해야 비로소 `TypeError` 를 냅니다. 여기서 `TypeError` 를 직접 던졌다면 상대 타입이 비교를 처리할 기회를 빼앗게 됩니다. → [12 §1-B](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `object.__setattr__` 이 왜 필요한가** — `@dataclass(frozen=True)` 는 클래스에 `__setattr__` 을 **생성해 덮어씁니다**. 그 구현은 **대입 대상이 그 클래스 자신의 인스턴스이거나 이름이 필드일 때** `FrozenInstanceError` 를 던지고(`dataclasses.FrozenInstanceError` 는 `AttributeError` 의 하위 클래스입니다), 그 외에는 `super().__setattr__` 으로 넘깁니다 — 그래서 frozen 클래스를 **상속한** 하위 클래스 인스턴스에 필드가 아닌 이름을 붙이는 것은 막히지 않습니다. `TransactionId` 자신은 두 조건에 모두 걸리므로, `__post_init__` 안에서 `self.value = ...` 를 하면 **자기 생성자 안에서도** 막힙니다.
>
>     :::python
>     >>> t = TransactionId("TX-1")
>     >>> t.value = "x"
>     dataclasses.FrozenInstanceError: cannot assign to field 'value'
>
> `object.__setattr__(self, "value", ...)` 은 그 덮어쓴 메서드를 **건너뛰고** 기본 구현(인스턴스 `__dict__` 에 직접 쓰기)을 호출하는 우회로입니다. dataclass 가 만든 `__init__` 자신도 frozen 일 때는 정확히 이 방식으로 필드를 채웁니다. 즉 우리가 쓰는 것은 편법이 아니라 **표준 라이브러리가 쓰는 것과 같은 문**이고, `__post_init__` 은 "생성자가 아직 끝나지 않은 구간"이라 이 문을 쓰는 것이 정당합니다.

> **🔎 문법의 출처 — 자기 자신을 반환 타입으로 쓸 수 있는 이유** — `def parse(cls, value: Any) -> TransactionId:` 는 **클래스 본문이 실행되는 시점에는 `TransactionId` 라는 이름이 아직 존재하지 않으므로** 원래대로라면 `NameError` 입니다. 파일 첫머리의 `from __future__ import annotations`(PEP 563)가 어노테이션을 **평가하지 않고 문자열로만 보관**하게 만들어 이 문제를 없앱니다. 그 전에는 `-> "TransactionId"` 처럼 따옴표로 감싸야 했고, 이 소스에는 그런 따옴표 표기가 **한 곳도 없습니다.** 같은 import 덕분에 `TransactionId | None`(PEP 604, 파이썬 3.10) 과 `list[str]`(PEP 585, 파이썬 3.9) 같은 표기도 안전하게 쓰입니다 — `pyproject.toml` 의 `requires-python = ">=3.10"` 이 그 하한입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

리팩터 전에는 `Transaction.__post_init__` 이 `self.id = str(self.id)` 로 **형식을 검사하지 않았습니다.** CSV 가 id 를 실어 오게 되면서 이것이 문제가 됐습니다 — `id=abc` 같은 값이 파일에 들어가면 ID 발급기가 그 줄을 무시하고 번호를 재사용할 수 있기 때문입니다.

**만드는 경로마다 실패 처리가 다른 것도 의도적입니다.** `TransactionId.parse` 는 예외를 던지지만(검증), `TransactionId.scan` 은 `None` 을 돌려줍니다(발굴). 후자는 "이 줄에서 번호를 못 찾았다"가 오류가 아니라 정상 상황이기 때문입니다. 조회 인자를 정규화하는 `TransactionRepository._as_id` 도 같은 이유로 `None` 을 돌려줍니다 — "형식이 틀린 id 로 조회"는 **찾지 못한 것**과 같아야 종료 코드가 흔들리지 않습니다.

---

## 5. entities.py — 데이터의 모양과 불변식

### 5.1 이 파일에 들어 있는 것

budget_app/domain/entities.py:1-12
```python
"""저장 엔티티 — 파일에 기록되는 도메인 객체.

``__post_init__`` 이 ``validators`` 를 호출해 **생성자가 유일한 불변식 강제 지점**이
되게 한다. 서비스·CLI·``from_dict``·``with_patch`` 어느 경로로 만들어져도 객체가
존재하는 순간 이미 검증·정규화가 끝나 있다.

``TransactionPatch`` 도 여기 있다 — 저장되지는 않지만 엔티티의 **변경 요청**이라
엔티티와 함께 읽히는 편이 자연스럽다.

결과 모델(``MonthlySummary``/``ImportReport``)은 저장되지 않고 생명주기가 달라
``results.py`` 로 분리했다.
"""
```

> **💡 쉽게 말하면** — 출입구가 넷인 건물은 검색대도 넷이어야 하고, 그중 하나만 꺼져 있어도 뚫립니다. 출입구를 하나로 좁히고 거기에만 검색대를 두면 "검사를 깜빡한 통로"라는 것이 아예 존재할 수 없습니다. 거래 데이터는 대화형 입력·파일 읽기·CSV 가져오기·수정, 네 갈래로 만들어지지만 전부 같은 생성자 하나를 지납니다.
>
> 다만 이 비유는 **담을 넘는 길**에서 깨집니다 — 파이썬에는 생성자를 건너뛰고 객체를 만드는 방법이 따로 있습니다. 언어가 막아 주는 것이 아니라, 이 프로젝트가 그 길을 쓰지 않기로 정하고 만드는 경로를 전부 생성자로 모아 둔 것입니다.

위 docstring 이 말하는 분할이 실제로 어떻게 끝났는지를 표로 봅니다. 옛 `domain/models.py` 한 파일에 있던 것들이 지금 어느 파일에 있는지의 목록입니다. **이 절은 `entities.py` 를 중심에 두되, 함께 갈라져 나간 세 파일도 같이 봅니다.**

| 구분 | 이름 | 지금 있는 파일 | 줄 |
|---|---|---|---|
| 기간 규칙 | `month_range` | `domain/periods.py` | 20-30 |
| 저장 엔티티 | `Transaction` | `domain/entities.py` | 27-124 |
| 변경 요청 | `TransactionPatch` | `domain/entities.py` | 127-154 |
| 저장 엔티티 | `Budget` | `domain/entities.py` | 157-173 |
| 저장 엔티티 | `Category` | `domain/entities.py` | 176-190 |
| 질의 모델 | `SearchFilter` | `domain/queries.py` | 32-82 |
| 결과 모델 | `MonthlySummary` | `domain/results.py` | 22-55 |
| 결과 모델 | `ImportReport` | `domain/results.py` | 74-97 |

거래 id 값 객체 `TransactionId`(`domain/tx_id.py:51-127`)까지 더하면 옛 `models.py` 의 조각은 다섯 파일에 나뉘어 있습니다. 나누는 기준은 **생명주기**(그 데이터가 언제 만들어져 언제까지 살아 있는가)였습니다 — 파일에 기록되는 것(`entities`), 질의 한 번 동안만 사는 것(`queries`), 계산 결과로 만들어져 화면까지만 가는 것(`results`), 그리고 순수 함수(`periods`).

### 5.2 `month_range` — 기간 규칙이 도메인에 있는 이유

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

**달력 계산은 화면 처리가 아니라 도메인 규칙**입니다. 리팩터 전에는 이 함수가 `cli.py` 에 `_month_bounds` 라는 이름으로 있었습니다. 서비스 계층은 CLI 를 가져다 쓸 수 없으니 같은 계산을 문자열 접두 비교로 따로 구현했고, 그래서 "이 달에 속하는가"의 정의가 프로그램 안에 둘이 됐습니다. 도메인으로 내리자 두 경로가 하나로 합쳐졌습니다.

> **⚙️ 내부 동작 — `calendar.monthrange(...)[1]` 의 `[1]` 은 무엇인가** — `calendar.monthrange(year, month)` 는 숫자 하나가 아니라 **두 값짜리 튜플 `(그 달 1일의 요일, 그 달의 일수)`** 를 돌려줍니다. 우리가 필요한 것은 일수뿐이라 `[1]` 로 두 번째를 꺼냅니다.
>
>     :::python
>     >>> import calendar
>     >>> calendar.monthrange(2024, 2)
>     (3, 29)      # 3 = 목요일, 29 = 2024년 2월의 일수(윤년)
>     >>> calendar.monthrange(2023, 2)
>     (2, 28)
>
> 윤년 판정은 `calendar.isleap`(내부적으로 `year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)`)이 하고, `calendar` 는 순수 계산 모듈이라 **파일도 시계도 건드리지 않습니다.** 도메인 계층이 이 모듈을 import 해도 "도메인은 I/O 를 모른다"는 규칙이 깨지지 않는 이유입니다. 마지막 줄의 `f"{normalized}-{last_day:02d}"` 에서 `:02d` 는 `TX_ID_FORMAT` 의 `:06d` 와 같은 형식 지정 미니 언어로, `9` 를 `"09"` 로 만들어 **문자열 날짜 비교 전제를 지킵니다**. → [12 §2-A](./12-syntax-and-stdlib.md)

동작 확인:

```python
month_range("2024-02")   # ('2024-02-01', '2024-02-29')   윤년
month_range("2023-02")   # ('2023-02-01', '2023-02-28')
month_range("2024-04")   # ('2024-04-01', '2024-04-30')   30일 달
month_range("2024-13")   # ValidationError
```

### 5.3 `Transaction` — 거래 모델 정독

budget_app/domain/entities.py:28-68

```python
class Transaction:
    """단일 거래 내역.
    ...
    """

    id: TransactionId
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
```

**`__post_init__` 이 규칙을 담고 있지 않다**는 점이 리팩터 전후의 결정적 차이입니다. 일곱 줄 전부 `validators` 로 위임합니다. 모델의 역할은 "**어떤 규칙을 어떤 필드에 적용할지**" 를 선언하는 것이고, 규칙 자체는 다른 곳에 있습니다.

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
        _set(self, "date", validators.parse_date(self.date))
        _set(self, "amount", validators.parse_amount(self.amount))
        _set(self, "category", validators.parse_category(self.category))
        _set(self, "memo", validators.parse_memo(self.memo))
        _set(self, "tags", tuple(validators.parse_tags(self.tags)))
```

> **⚙️ 내부 동작 — `__post_init__` 은 누가 언제 부르나** — 특별한 훅처럼 보이지만 사실은 아주 단순합니다. `@dataclass` 는 클래스 본문의 **어노테이션이 붙은 이름들**(`id: TransactionId` 등, PEP 526 변수 어노테이션)을 `__dataclass_fields__` 로 모은 뒤, 그것을 그대로 대입하는 `__init__` 의 **소스 코드를 문자열로 조립해 `exec` 로 실행**해 붙입니다. 그리고 클래스에 `__post_init__` 이 정의돼 있으면 그 생성된 `__init__` 의 **맨 마지막 줄**에 `self.__post_init__()` 호출을 덧붙입니다. 즉 "필드를 전부 채운 직후"라는 위치가 보장됩니다.
>
> 이 조립 시점이 중요합니다 — dataclass 가 하는 일은 **클래스가 정의되는 순간(import 시점)에 한 번** 끝나고, 그 뒤로는 손으로 쓴 `__init__` 과 성능이 같습니다. 어노테이션이 없는 `x = 3` 같은 줄은 필드로 잡히지 않는다는 것도 같은 기제에서 나오는 규칙입니다.
>
> `_set = object.__setattr__` 로 이름을 한 번 묶어 둔 것은 순수한 가독성 목적입니다 — 파이썬에서 메서드도 그냥 객체라 지역 변수에 담아 쓸 수 있고, 일곱 줄이 `object.__setattr__(self, ...)` 로 시작하는 것보다 훨씬 읽힙니다. → [12 §1-B](./12-syntax-and-stdlib.md)

**부가 메서드들.**

budget_app/domain/entities.py:82

```python
    def to_dict(self) -> dict:
```

> 이전에는 여기에 `id_number` property 가 있었습니다. `TransactionId.number` 를 한 겹 더 감싸기만 했고 아무도 부르지 않아 제거했습니다 — 값 객체가 생긴 뒤로는 `tx.id.number` 가 더 짧고 정확합니다. **지금 소스에 `id_number` 라는 이름은 없습니다**(`domain/tx_id.py:121-124` 의 `TransactionId.number` 하나뿐입니다).

**날짜를 문자열로 저장하는 이유.** `date: str` 이지 `datetime.date` 가 아닙니다. `YYYY-MM-DD` 형식은 **사전순 비교가 날짜순 비교와 일치**하므로, 문자열 그대로 비교·정렬·JSON 저장이 전부 가능합니다. `datetime` 객체로 들고 있으면 저장할 때마다 문자열로 바꾸고 읽을 때마다 파싱해야 하는데, 얻는 게 없습니다.

```python
"2024-01-15" < "2024-02-01"   # True — 문자열 비교인데 날짜 순서와 같다
```

### 5.4 `with_patch` — 수정은 도메인 연산

budget_app/domain/entities.py:113-124

```python
    def with_patch(self, patch: TransactionPatch) -> Transaction:
        """부분 변경을 적용한 **새 Transaction** 을 만든다.
        ...
        """
        return Transaction(**{**self.to_dict(), **patch.changed_fields()})
```

동작 예:

```python
tx = Transaction(id="TX-000001", type="expense", date="2024-01-15",
                 amount=15000, category="food", memo="점심", tags=["meal"])

patch = TransactionPatch(amount=16000, memo="점심 수정")
new_tx = tx.with_patch(patch)

# new_tx.amount   → 16000       (변경됨)
# new_tx.memo     → "점심 수정"  (변경됨)
# new_tx.date     → "2024-01-15" (유지)
# new_tx.tags     → ["meal"]     (유지)
# tx              → 원본 그대로  (변경 안 됨)
```

`patch = TransactionPatch(amount=-5)` 를 넘기면? `with_patch` 안의 `Transaction(...)` 이 `__post_init__` 을 태우고 `parse_amount` 가 `ValidationError` 를 던집니다. **수정 경로에도 불변식이 그대로 적용됩니다.**

> **🔎 문법의 출처 — `Transaction(**{**a, **b})` 의 별 세 종류** — 한 줄에 서로 다른 `**` 가 두 가지 뜻으로 섞여 있어 처음 보면 읽기 어렵습니다.
>
> - `{**a, **b}` — **딕셔너리 리터럴 안의 언팩.** PEP 448 로 파이썬 3.5 에 들어왔습니다. 그 전에는 `d = dict(a); d.update(b)` 두 줄이었습니다. **뒤에 오는 것이 이깁니다** — 그래서 패치가 원본을 덮어씁니다. 파이썬 3.9 부터는 `a | b` 로도 쓸 수 있지만 의미는 같습니다.
> - 바깥의 `Transaction(**…)` — **호출 인자 언팩.** 파이썬 2 시절부터 있는 문법으로, dict 의 키를 **키워드 인자 이름**으로 풀어 넣습니다. 그래서 `to_dict()` 의 키 이름이 `Transaction` 의 필드 이름과 정확히 같아야 하고, 하나라도 어긋나면 `TypeError: unexpected keyword argument` 로 **즉시** 터집니다.
>
> 결과적으로 이 한 줄은 "원본을 dict 로 펼치고 → 바뀐 필드만 덮어쓰고 → 생성자로 다시 밀어 넣는다"가 됩니다. 마지막 단계가 생성자이기 때문에 검증을 건너뛸 수 없습니다.

### 5.5 `TransactionPatch` — dict 를 대체한 이유

budget_app/domain/entities.py:127-154

```python
@dataclass(frozen=True)
class TransactionPatch:
    """거래 부분 수정 요청 — ``None`` 인 필드는 "변경 없음"을 뜻한다.
    ...
    """

    date: str | None = None
    type: str | None = None
    category: str | None = None
    amount: int | None = None
    memo: str | None = None
    tags: list[str] | None = None

    def changed_fields(self) -> dict[str, Any]:
        """``None`` 이 아닌 필드만 골라 dict 로 준다."""
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if getattr(self, f.name) is not None
        }

    @property
    def is_empty(self) -> bool:
        return not self.changed_fields()
```

**리팩터 전후 비교.**

```python
# 리팩터 전 — 조용히 실패
changes = {"catgeory": "food"}      # 오타!
repo.update("TX-000001", changes)   # 오류 없음. 아무것도 안 바뀜.

# 리팩터 후 — 즉시 실패
patch = TransactionPatch(catgeory="food")
# TypeError: __init__() got an unexpected keyword argument 'catgeory'
```

> **⚙️ 내부 동작 — `fields(self)` 는 어디서 목록을 얻나** — `dataclasses.fields()` 는 마법이 아니라 객체(또는 클래스)의 **`__dataclass_fields__` 딕셔너리를 읽어** `Field` 객체들의 튜플로 돌려주는 함수입니다. 그 딕셔너리는 `@dataclass` 가 클래스를 만들 때 어노테이션에서 채워 둔 것이고, 그래서 **필드를 하나 추가하면 `changed_fields` 는 고칠 필요가 없습니다.** 여섯 개 필드를 손으로 나열했다면 새 필드를 추가할 때마다 이 함수도 같이 고쳐야 하고, 잊으면 "지정했는데 반영되지 않는" 조용한 버그가 됩니다.
>
> `{f.name: getattr(self, f.name) for f in fields(self) if ...}` 는 **딕셔너리 컴프리헨션**으로, 파이썬 2.7/3.0 부터 있는 문법입니다(리스트 컴프리헨션이 먼저 있었고 dict/set 이 나중에 합류했습니다). `getattr(self, "amount")` 는 `self.amount` 와 완전히 같은 동작이고, **속성 이름이 문자열 변수로 들어올 때** 쓰는 형태입니다. → [12 §1-B](./12-syntax-and-stdlib.md)

`is_empty` property 덕분에 CLI 의 "수정할 필드가 없습니다" 검사도 한 줄이 됩니다.

budget_app/cli/handlers.py:135-144

```python
def cmd_update(ctx: AppContext, args: argparse.Namespace) -> int:
    # 값 검증은 Transaction.__post_init__ 이 수행하므로 여기서는 조립만 한다.
    patch = _build_patch(args)
    if patch.is_empty:
        raise AppError(messages.ERR_NO_UPDATE_FIELDS, hint=messages.HINT_UPDATE_FIELDS)

    updated = ctx.tx_service.update(args.id, patch)
    output.out(messages.MSG_UPDATED_TX.format(id=updated.id))
    output.out(presenter.tx_line(updated))
    return config.EXIT_OK
```

리팩터 전에는 `if args.date is not None: changes["date"] = ...` 를 여섯 번 반복했고, 각 줄에서 검증까지 호출했습니다. 지금은 **조립만** 합니다.

### 5.6 `Budget` 과 `Category`

budget_app/domain/entities.py:158-173

```python
class Budget:
    """월별 예산. month 는 'YYYY-MM' 문자열."""

    month: str
    amount: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "month", validators.parse_month(self.month))
        object.__setattr__(self, "amount", validators.parse_amount(self.amount))

    def to_dict(self) -> dict:
        return {"month": self.month, "amount": self.amount}

    @classmethod
    def from_dict(cls, data: dict) -> Budget:
        return cls(month=data["month"], amount=data["amount"])
```

**세 엔티티가 같은 계약을 따릅니다** — `__post_init__`(불변식), `to_dict`, `from_dict`. 이 세 메서드가 있기 때문에 `JsonlStore` 가 셋을 구분하지 않고 다룰 수 있습니다([03 §2.1](./03-python-advanced.md)).

`Budget` 은 금액 규칙을 `Transaction` 과 **공유**합니다. 리팩터 전에는 `Budget.__post_init__` 이 모듈 함수 `validate_amount` 를, `Transaction` 은 자기 staticmethod 를 부르는 비대칭이 있었습니다. 지금은 둘 다 `validators.parse_amount` 입니다.

### 5.7 결과 모델 — `MonthlySummary` 와 `ImportReport`

`MonthlySummary` 는 [03 §1.6](./03-python-advanced.md)과 [04 §4](./04-architecture.md)에서 다뤘으므로, 여기서는 `ImportReport` 를 봅니다.

budget_app/domain/results.py:74-97

```python
@dataclass(frozen=True)
class ImportReport:
    """CSV 가져오기 결과.
    ...
    """

    imported: int = 0
    skipped: int = 0
    duplicated: int = 0
    errors: tuple[RejectedRow, ...] = ()
    duplicates: tuple[DuplicateRow, ...] = ()
```

**모든 필드에 기본값이 있습니다.** `ImportReport()` 만으로 "아무 일도 없었음"을 표현할 수 있습니다.

**`tuple[RejectedRow, ...]` 인 이유**는 `frozen=True` 와 짝을 이룹니다. 리스트를 담으면 frozen 이어도 `report.errors.append(...)` 가 가능해서 불변성이 반쪽이 됩니다. 튜플이면 진짜로 못 바꿉니다.

> **🔎 문법의 출처 — `tuple[X, ...]` 의 소문자와 말줄임표** — 내장 타입을 그대로 첨자에 쓰는 표기(`tuple[...]`, `list[str]`, `dict[str, Any]`)는 PEP 585 로 파이썬 3.9 에 들어왔습니다. 그 전에는 `from typing import Tuple, List` 를 해서 **대문자** `Tuple[str, ...]` 로 써야 했고, 이 문서 아래 "리팩터 전" 코드에 그 흔적이 남아 있습니다. 여기 쓰인 `...`(Ellipsis)는 생략 부호가 아니라 **진짜 문법 토큰**으로, `tuple[X, ...]` 은 "X 가 몇 개든 들어 있는 튜플"을 뜻합니다. `tuple[X]` 라고 쓰면 뜻이 완전히 달라집니다 — "원소가 정확히 하나인 튜플"입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

리팩터 전에는 이 자리에 `Tuple[int, int, List[str]]` 이 있었습니다.

```python
# 리팩터 전
imported, skipped, errors = service.import_csv(path, atomic=True)
#   ↑ 세 값의 순서를 외워야 하고, 값을 추가하려면 모든 호출부를 고쳐야 함

# 리팩터 후
report = service.import_csv(path, atomic=True, on_duplicate="skip")
report.imported, report.duplicated, report.has_problems
#   ↑ 이름으로 접근, 필드를 추가해도 기존 호출부는 그대로
```

실제로 `duplicated` 를 추가할 때 이 차이가 드러났습니다 — 튜플이었다면 반환 위치를 세는 모든 코드를 고쳐야 했을 것입니다.

---

## 6. 핵심 개념 — "생성자가 유일한 강제 지점"

이 다섯 모듈을 관통하는 하나의 아이디어입니다.

```
              ┌─────────────────────────────────────┐
              │  validators.py — 규칙 하나 = 함수 하나 │
              └──────────────────┬──────────────────┘
                                 │ 호출
     ┌───────────────────────────┼───────────────────────────┐
     │                           │                           │
     ▼                           ▼                           ▼
[모델 __post_init__]     [prompts.ask_until]        [csv_io.parse_row]
     │                           │                           │
     │  ← 어떤 경로로 만들어져도 반드시 여기를 지난다 →         │
     ▼                           ▼                           ▼
              ┌─────────────────────────────────────┐
              │  Transaction — 존재하면 반드시 유효    │
              └─────────────────────────────────────┘
```

거래 객체가 만들어지는 경로는 네 가지입니다.

| # | 경로 | 진입점 |
|---|---|---|
| 1 | CLI 대화형 입력 | `TransactionService.add` |
| 2 | JSONL 파일 읽기 | `Transaction.from_dict` |
| 3 | CSV 가져오기 | `ParsedRow.to_transaction` |
| 4 | 수정 | `Transaction.with_patch` |

**네 경로 전부 `Transaction(...)` 생성자를 통과합니다.** 그러므로 검증을 "깜빡한 경로"라는 것이 존재할 수 없습니다.

이 불변식이 성립하면 **하류 코드가 단순해집니다.**

| 성립하는 것 | 그래서 생략 가능한 방어 코드 |
|---|---|
| `tx.memo` 는 항상 문자열 | `(tx.memo or "")` 불필요 → `MemoContains.is_satisfied_by` 가 `self.query in tx.memo` 한 줄 (`domain/specs.py:226-227`) |
| `tx.tags` 는 항상 튜플 | `(tx.tags or [])` 불필요 → `HasTag.is_satisfied_by` (`domain/specs.py:239-240`) |
| `tx.amount` 는 항상 양의 정수 | 합산 전 `if tx.amount > 0` 불필요 |
| `tx.id` 는 항상 `TransactionId` 값 객체이고 `TX-` + 6자리 정규형 | ID 발급기가 형식을 가정할 수 있음 (`TX-1` 과 `TX-000001` 이 공존하지 않으므로) |
| `tx.category` 는 공백 정규화됨 | 비교 전 `.strip()` 불필요 |

**과제 방어 포인트**: "입력 검증은 어디서 하나요?"라는 질문에는 두 층으로 답합니다.

1. **필드 규칙**(형식·범위)은 `validators.py` 에 함수로 정의되고, 모델 생성자가 강제합니다. 어떤 경로로 만들어도 통과합니다.
2. **상황 규칙**(등록된 카테고리인가, 그 id 가 존재하는가)은 저장된 상태를 봐야 하므로 서비스 계층에 있고 `AppError` 를 던집니다.

그리고 이 구분이 종료 코드 2 와 4 로 이어집니다.

---

## 정리

- **errors.py** — 실패의 타입을 정의합니다. `ValidationError`(값) vs `AppError`(상황)의 구분이 종료 코드까지 이어집니다. import 가 0개라 어느 계층이든 안전하게 씁니다. `ValueError` 상속 덕분에 이 타입을 모르는 호출자도 `except ValueError` 로 받습니다(`__mro__` 를 따라 판정되기 때문).
- **config.py** — 바꾸면 **동작**이 달라지는 값. 함수도 클래스도 없는 순수 상수 파일이고, 계층마다 하나씩(루트 + domain/storage/services/cli) 있습니다.
- **messages.py** — 바꿔도 **글자만** 달라지는 문구. `ERR_`/`HINT_` 짝 구조가 오류 UX 의 뼈대입니다. 사용자 문구는 `str.format` 템플릿, 로그만 `%`-스타일입니다(포매팅을 출력 직전까지 미루기 위해).
- **validators.py** — 규칙 하나 = 함수 하나. 엔티티·CSV·대화형 입력이 전부 같은 함수를 부릅니다. `parse_date` 가 `strptime` 으로 **검증**하고 `strftime` 으로 **재직렬화**하는 것이 이 모듈의 핵심 동작입니다 — `strptime` 만으로는 `"2024-1-5"` 가 통과해 문자열 날짜 비교가 깨집니다.
- **entities.py** — 데이터 모양(엔티티). 함께 갈라져 나온 `queries.py`(질의 조건 `SearchFilter`), `results.py`(계산 결과 `MonthlySummary`/`ImportReport`), `periods.py`(기간 규칙 `month_range`), `tx_id.py`(거래 id 값 객체)까지가 옛 `models.py` 의 자리입니다.
- 다섯을 관통하는 원칙은 **"생성자가 유일한 강제 지점"** 이고, 그것을 물리적으로 떠받치는 것이 `frozen=True` + `__post_init__` + `object.__setattr__` 세 장치입니다.

**다음 문서**: [06. 횡단 관심사와 예외 처리](./06-decorators.md) — 여기서 정의한 예외가 어떻게 사용자 메시지와 종료 코드로 바뀌는지 봅니다.
