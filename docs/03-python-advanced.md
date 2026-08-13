# 03. 이 코드에 쓰인 파이썬 중·고급 기법

## 쉬운 말로 먼저

이 문서는 프로그램의 특정 기능을 설명하지 않습니다. 대신 **코드 전체에 되풀이해서 나타나는 글쓰기 습관 열 가지**를 모아 놓았습니다. 가계부 프로그램이 하는 일 자체는 단순합니다 — 거래를 받아 적고, 파일에 넣고, 필요할 때 꺼내 보여 줍니다. 그런데 같은 일을 하는 코드도 쓰는 방식은 여럿이고, 어느 방식을 골랐는지가 나중에 고치기 쉬운 코드와 손댈 수 없는 코드를 가릅니다. 여기서 다루는 것이 그 선택들입니다 — 같은 검사를 여러 군데 베껴 두지 않으려면 어떻게 하는지, 10만 건짜리 파일을 통째로 들지 않고 훑는 방법은 무엇인지, 모든 명령에 똑같이 붙어야 하는 잡일(기록 남기기, 오류 처리)을 본문에 섞지 않고 떼어 두는 방법은 무엇인지.

마지막 절에는 **쓰지 않기로 한 방식**들도 나옵니다. 어떤 기법을 알면서도 "이 프로그램에는 아직 필요 없다"고 판단해 넣지 않은 것 역시 설계이고, 그 근거를 말할 수 있는 것이 기법을 하나 더 아는 것보다 낫습니다. 미리 알아 두면 그 절이 덜 뜬금없습니다.

**이 문서에 자주 나오는 말**

| 말 | 쉬운 뜻 |
| --- | --- |
| dataclass | 담을 칸의 이름만 적어 두면, 나머지 뻔한 작업(칸 채우기 · 내용 찍어 보기 · 두 개가 같은지 대조하기)을 파이썬이 대신 만들어 주는 클래스 선언법 |
| frozen(불변) | 만든 뒤에는 값을 바꿀 수 없는 상태. 고치려면 고친 값으로 새것을 하나 더 만듭니다 |
| 정규화 | 같은 뜻의 값이 여러 표기로 갈리지 않게 하나로 통일하는 일. `2024-1-5` 와 `2024-01-05` 를 늘 뒤쪽 표기로 맞추는 것 |
| 제너레이터 | 결과를 한꺼번에 다 만들어 주지 않고, 달라고 할 때마다 하나씩 내주는 함수 |
| 데코레이터 | 원래 함수는 그대로 두고 그 앞뒤에 할 일을 덧씌우는 표기(`@이름`) |
| 클로저 | 함수가 만들어질 때 곁에 있던 **변수**를 붙잡은 채로 돌아다니는 것. 값을 베껴 두는 것이 아니라 그 변수를 계속 같이 보는 것이라, 나중에 값이 바뀌면 바뀐 값이 보입니다 |
| 제네릭 | 안에 무엇이 담기는지를 나중에 정하는 상자 표기(`JsonlStore[Transaction]`) |
| 불변식 | 객체가 살아 있는 동안 절대 깨지면 안 되는 약속. 예를 들어 "금액은 언제나 양의 정수" |

**바쁘면 여기만**

- **[§1.1 ~ §1.4](#1-dataclass-완전-해설)** — 거래·예산·카테고리가 어떤 모양으로 만들어지고, 왜 **만들어지는 순간에** 검사를 받는지. 이 프로그램에 잘못된 데이터가 들어가지 않는 이유가 여기 있습니다.
- **[§3.2](#32-읽기-경로가-둘--iter_raw-와-stream)** — 실제로 났던 사고 이야기입니다. 무관한 거래 하나를 지웠더니 깨진 줄이 파일에서 영구히 사라졌고, 그것을 어떻게 갈라 고쳤는지. 기법보다 판단이 보이는 절입니다.
- **[§10.4](#104-쓰지-않기로-한-패턴)** — 표 하나로 끝납니다. "왜 안 썼나"만 읽어도 이 프로젝트가 무엇을 경계했는지 보입니다.

budget_app 코드에 실제로 등장하는 dataclass, 제네릭, 데코레이터, 제너레이터, 사용자 정의 예외 등 중·고급 파이썬 기법을 "개념 원리 → 실제 코드 → 설계 의도" 순서로 완전히 해설합니다.

> **난이도**: 🟡 중급
>
> **먼저 읽으면 좋은 문서**: [02. 이 코드에 쓰인 파이썬 기초 문법](./02-python-basics.md), [04. 아키텍처](./04-architecture.md)

---

## 목차

1. [dataclass 완전 해설](#1-dataclass-완전-해설)
2. [메서드 3종과 "클래스에 둘 것 / 모듈에 둘 것"](#2-메서드-3종과-클래스에-둘-것--모듈에-둘-것)
3. [제너레이터 심화](#3-제너레이터-심화)
4. [데코레이터와 클로저 심화](#4-데코레이터와-클로저-심화)
5. [예외 심화](#5-예외-심화)
6. [제네릭 — TypeVar 와 Generic](#6-제네릭--typevar-와-generic)
7. [from __future__ import annotations](#7-from-__future__-import-annotations)
8. [표준 라이브러리 활용](#8-표준-라이브러리-활용)
9. [콜러블을 값으로 전달하는 패턴](#9-콜러블을-값으로-전달하는-패턴)
10. [적용된 디자인 패턴 2종](#10-적용된-디자인-패턴-2종)

> **이 문서의 두 종류 보강 노트.** 본문 곳곳에 인용문으로 붙은
> **🔎 문법의 출처**(이 표기가 어느 PEP·어느 버전에서 왔고 그 전에는 무엇으로 썼는가)와
> **⚙️ 내부 동작**(이 호출이 CPython 안에서 실제로 무슨 일을 하는가)이 그것입니다.
> 더 깊은 설명은 [12. 문법·표준 라이브러리 레퍼런스](./12-syntax-and-stdlib.md)에 절 번호별로 모아 두었습니다.

---

## 1. dataclass 완전 해설

이 프로젝트는 dataclass 를 **네 가지 목적**으로 씁니다. 목적마다 옵션(`frozen`)과 구성이 달라지므로, 그 대응 관계를 아는 것이 이 장의 핵심입니다.

| 목적 | 예 | `frozen` | 특징 |
|---|---|---|---|
| 저장 엔티티 | `Transaction`, `Budget`, `Category` | 예 | `__post_init__` 이 `object.__setattr__` 로 **정규화하며 덮어씀** |
| 값 객체(규칙이 딸린 작은 타입) | `TransactionId` | 예 | 형식 규칙 + `total_ordering` 비교 |
| 변경 요청 | `TransactionPatch` | 예 | 만들어진 뒤 바뀌면 안 되는 "명령서" |
| 질의 조건 | `SearchFilter` | 아니오 | `__post_init__` 이 파생 필드 `spec` 을 대입 |
| 계산 결과 | `MonthlySummary`, `ImportReport`, `RawLine`, `ParsedRow` | 예 | 파생값은 `@property` |
| 누적 상태 | `_Batch` | 아니오 | 행을 훑으며 값이 쌓임 |

### 1.1 @dataclass 가 자동으로 만들어 주는 것

**개념.** 파이썬에서 "데이터를 담는 클래스"를 손으로 쓰면 `__init__` 에서 인자를 받아 `self.x = x` 를 반복하고, 디버깅용 `__repr__`, 비교용 `__eq__` 까지 전부 직접 구현해야 합니다. `@dataclass` 데코레이터(표준 라이브러리 `dataclasses` 모듈)는 **클래스 본문의 "필드 이름: 타입 어노테이션" 선언만 보고** 다음 세 가지를 자동 생성합니다.

- `__init__` — 필드 순서대로 인자를 받아 대입하는 생성자
- `__repr__` — `Transaction(id='TX-000001', type='expense', ...)` 형태의 표현 문자열
- `__eq__` — 모든 필드 값이 같으면 두 인스턴스를 같다고 판정

> **💡 쉽게 말하면** — 양식지를 새로 만드는 일과 비슷합니다. "이름 칸, 날짜 칸, 금액 칸이 필요하다"고 칸 이름만 적어 내면, 인쇄소가 빈 양식지에 더해 "작성된 내용을 그대로 읽어 주는 사본"과 "두 장이 같은 내용인지 대조하는 방법"까지 딸려 만들어 줍니다. 그 셋이 각각 `__init__`, `__repr__`, `__eq__` 입니다.
> 다만 이 비유는 인쇄소가 칸의 **이름과 순서만** 볼 뿐 내용 규칙은 모른다는 데서 깨집니다 — "금액 칸에 음수가 오면 안 된다" 같은 것은 딸려 오지 않고, §1.4 의 `__post_init__` 이 따로 붙입니다.

일반론 예시로, 아래 두 코드는 사실상 같습니다(이 프로젝트 코드가 아니라 개념 설명용 예시입니다).

```python
# 일반론 예시 — 손으로 쓴 버전
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __repr__(self):
        return f"Point(x={self.x!r}, y={self.y!r})"
    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

# 일반론 예시 — dataclass 버전 (위와 동등)
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
```

**실제 코드.** 이 프로젝트의 핵심 모델 `Transaction` 이 정확히 이 방식으로 선언되어 있습니다.

budget_app/domain/entities.py:28-54

```python
class Transaction:
    """단일 거래 내역.

    필드 계약:
        id       : ``TransactionId`` 값 객체 (``TX-000001`` 형식)
        type     : "income" 또는 "expense"
        date     : "YYYY-MM-DD"
        amount   : 양의 정수
        category : 카테고리명(공백 정규화됨)
        memo     : 자유 문자열 (없으면 빈 문자열)
        tags     : 태그 튜플 (없으면 빈 튜플)

    ``id`` 만 값 객체이고 나머지는 원시 타입인 이유: id 는 형식 규칙(``TX-`` + 6자리),
    번호 변환, 손상 줄 발굴이라는 **고유 행동**이 붙어 있어 타입이 값을 한다.
    ``date``/``category`` 는 규칙이 ``validators`` 함수 하나로 끝나 값 객체를 만들면
    직렬화만 복잡해진다.

    ## ``frozen=True`` 인 이유

    이 클래스의 docstring 은 오래전부터 "생성자가 유일한 불변식 강제 지점"이라고
    말해 왔는데, 정작 만들어진 뒤에 ``tx.amount = -1`` 이 그냥 됐다. 생성자가
    유일한 강제 지점이 되려면 **생성자 이후에 바꿀 수 없어야** 한다.

    수정은 이미 ``with_patch`` 가 새 객체를 만드는 방식이라 제자리 수정 코드는
    한 곳도 없었다 — 즉 이 전환은 이미 지키고 있던 규약을 타입으로 굳힌 것이다.

    ``tags`` 가 리스트가 아니라 **튜플**인 것도 같은 이유다. ``frozen`` 은 필드를
```

`@dataclass` 가 실제로 읽는 것은 이 docstring 아래의 **어노테이션 선언 7줄**입니다.

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

이 선언 하나로 생성자, 필드 전체를 보여주는 `__repr__`, 필드 단위 `==` 비교가 전부 생깁니다. `memo` 와 `tags` 는 기본값이 있으므로 생략 가능한 선택 인자가 됩니다.

> **🔎 문법의 출처** — `dataclasses` 는 PEP 557 로 파이썬 3.7 에 표준 라이브러리로 들어왔습니다.
> 그 전에는 `collections.namedtuple`(불변·인덱스 접근) 이나 외부 패키지 `attrs`, 아니면 위의
> "손으로 쓴 버전"을 그대로 썼습니다. → [12 §1-B](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — `@dataclass` 는 클래스의 `__annotations__` 를 순서대로 읽어
> `def __init__(self, id, type, ..., memo='', tags=()):` 라는 **파이썬 소스 문자열을 조립한 뒤
> `exec` 로 컴파일**해 클래스에 붙입니다. 그래서 생성된 `__init__` 의
> `__code__.co_filename` 은 파일 경로가 아니라 `<string>` 입니다(3.13 에서 직접 확인).
> 이 "소스를 만들어 exec 한다"는 사실이 §1.3 의 `frozen` 과 §1.4 의 `object.__setattr__`
> 을 설명하는 열쇠입니다. → [12 §1-B](./12-syntax-and-stdlib.md)

**설계 의도.** 이 앱의 엔티티는 전부 "필드 묶음 + 검증"이 본질입니다. dataclass 를 쓰면 보일러플레이트(어느 클래스에나 똑같이 되풀이되는 상투적인 코드)가 사라져 **필드 계약(docstring)과 검증 로직만 남고**, `__eq__` 자동 생성 덕분에 테스트에서 `assert tx1 == tx2` 같은 비교도 공짜로 얻습니다.

### 1.2 field(default_factory=list) 와 가변 기본값 함정

**개념.** 파이썬에서 함수(그리고 생성자)의 기본값은 **함수가 정의되는 순간 딱 한 번** 평가되어 함수 객체에 저장됩니다. 그래서 기본값으로 리스트 같은 **가변(mutable) 객체**를 쓰면, 모든 호출이 **같은 리스트 하나를 공유**하게 됩니다.

```python
# 일반론 예시 — 가변 기본값 버그
def add_tag(tag, tags=[]):      # 이 [] 는 단 한 번만 만들어진다
    tags.append(tag)
    return tags

add_tag("a")   # ['a']
add_tag("b")   # ['a', 'b']  ← 새 리스트가 아니라 아까 그 리스트!
```

dataclass 에서 `tags: List[str] = []` 라고 쓰면 모든 인스턴스가 태그 리스트 하나를 공유하는 대형 버그가 되므로, **dataclass 는 이 표기 자체를 `ValueError: mutable default ... use default_factory` 로 거부**합니다. 대신 `field(default_factory=list)` 를 쓰면 "인스턴스가 만들어질 때마다 `list()` 를 호출해 **새 리스트**를 만들어라"는 의미가 됩니다.

`_Batch`(services/importexport.py:30-58)가 이 패턴을 가장 많이 쓰는 곳입니다.

budget_app/services/importexport.py:30-39

```python
@dataclass
class _Batch:
    """가져오기 준비 단계의 누적 상태.

    준비(prepare)와 커밋(commit)을 나누는 것이 원자성의 뼈대다. 파일에 손대기
    전에 모든 행의 판정이 끝나 있어야 "전혀 반영 안 됨"이 가능하다.
    """

    transactions: list[Transaction] = field(default_factory=list)
    new_categories: list[str] = field(default_factory=list)
```

리스트 4개는 전부 `default_factory`, 정수 2개는 불변이라 `= 0` 으로 충분합니다. **가변이면 factory, 불변이면 직접 대입**이 판단 기준입니다.

> **⚙️ 내부 동작** — dataclass 가 "가변 기본값"을 판정하는 기준은 타입 이름이 아니라
> **해시 가능성**입니다. 기본값 객체의 클래스가 `__hash__ is None` 이면
> `ValueError: mutable default ... use default_factory` 를 냅니다(리스트·딕트·집합이 여기 해당).
> `field(default_factory=list)` 를 쓰면 생성된 `__init__` 소스에 `self.x = list()` 대신
> **매개변수 기본값을 센티넬로 두고 "안 넘어왔으면 팩토리를 호출"** 하는 코드가 들어가므로,
> 인스턴스마다 새 리스트가 만들어집니다. → [12 §1-B](./12-syntax-and-stdlib.md)

### 1.3 `frozen=True` — 만들어진 뒤 바뀌지 않는 dataclass

**개념.** `@dataclass(frozen=True)` 는 필드 대입을 막습니다. 대입하려 하면 `FrozenInstanceError` 가 나고, 부수 효과로 `__hash__` 가 자동 생성되어 set/dict 키로 쓸 수 있게 됩니다.

> **💡 쉽게 말하면** — 코팅해서 발급한 증명서 같은 것입니다. 발급이 끝나면 글자를 고칠 수 없고, 내용을 바꾸려면 고친 내용으로 새로 발급받아야 합니다. 그 대신 "이 증명서는 발급 시점의 검사를 통과한 것"이라는 사실이 손에 들고 있는 내내 참으로 남습니다.
> 다만 이 비유는 코팅되는 것이 **겉장뿐**이라는 데서 깨집니다 — 증명서에 서류철이 끼워져 있으면 그 안의 종이는 여전히 빼고 넣을 수 있습니다. `Transaction.tags` 가 리스트가 아니라 튜플인 이유가 그것입니다.

> **⚙️ 내부 동작 — `frozen` 은 어떻게 대입을 막는가** — 마법이 아니라 **메서드 두 개를
> 덮어쓰는 것**입니다. `frozen=True` 면 dataclass 가 `__setattr__` 과 `__delattr__` 를
> "**그 클래스 자신의 인스턴스이거나 대입 대상 이름이 필드일 때** `FrozenInstanceError` 를
> 던지는 함수"로 만들어 클래스에 붙입니다(그 두 조건에 걸리지 않으면 `super().__setattr__`
> 로 넘겨 정상 대입합니다 — 그래서 frozen dataclass 를 **상속한** 하위 클래스의 인스턴스에
> 필드가 아닌 이름을 대입하면 통과합니다).
> (`FrozenInstanceError` 는 `AttributeError` 의 자식입니다).
> 그래서 막히는 것은 **속성 재대입뿐**입니다 — `tx.tags` 가 리스트였다면
> `tx.tags.append("x")` 는 `__setattr__` 를 전혀 거치지 않으므로 그대로 통과합니다.
> `Transaction.tags` 가 `tuple[str, ...]` 인 이유가 정확히 이것이고, 소스 docstring 도
> "``frozen`` 은 필드를 다시 묶는 것만 막지 리스트 안을 바꾸는 것은 막지 못한다"고
> 같은 말을 합니다(domain/entities.py:54-57). → [12 §1-B](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `__hash__` 는 공짜가 아닙니다** — 파이썬은 `__eq__` 를 정의한 클래스의
> `__hash__` 를 자동으로 `None` 으로 만듭니다(변경 가능한 값이 dict 키가 되는 것을 막으려고).
> dataclass 는 `eq=True`(기본) **와** `frozen=True` 가 **동시에** 참일 때만 `__hash__` 를
> 다시 만들어 줍니다 — 내용은 "필드 전부를 튜플로 묶어 `hash()`". 그래서 **필드 중 하나라도
> 해시 불가능하면** 클래스 정의는 통과하되 `hash(obj)` 호출 시점에
> `TypeError: unhashable type: 'list'` 가 납니다. 위 docstring 의 "필드가 전부 해시 가능해야
> 동작한다"가 이 뜻입니다. → [12 §1-B](./12-syntax-and-stdlib.md)

**실제 코드.**

budget_app/domain/entities.py:127-142

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
```

**설계 의도.** `TransactionPatch` 는 "이 필드들을 이 값으로 바꿔라"라는 **명령서**입니다. 명령서가 전달 도중에 바뀌면 CLI 가 만든 것과 저장소가 받는 것이 달라질 수 있습니다. `frozen=True` 는 그 가능성을 언어 차원에서 없앱니다.

같은 이유로 결과 모델도 전부 frozen 입니다 — `MonthlySummary`(domain/results.py:22-55), `ImportReport`(domain/results.py:74-97), `RawLine`(storage/jsonl.py:95-111), `ParsedRow`(storage/csv_io.py:39-64), `TransactionInput`(cli/prompts.py:40-49). **"이미 계산이 끝난 값"과 "아직 확정되지 않은 값"을 타입 선언만으로 구분**할 수 있게 됩니다.

**엔티티도 지금은 frozen 입니다.** `Transaction`/`Budget`/`Category`, 그리고 값 객체 `TransactionId` 까지 전부 `@dataclass(frozen=True)` 이고(domain/entities.py:27, 157, 176 / domain/tx_id.py:52), `__post_init__` 은 대입 대신 `object.__setattr__` 로 정규화합니다(§1.4).

frozen 이 **아닌** dataclass 는 둘뿐입니다 — 질의 조건 `SearchFilter`(domain/queries.py:32)와 가져오기 누적 상태 `_Batch`(services/importexport.py:30). `_Batch` 는 행을 훑으며 값이 계속 쌓이는 객체라 당연합니다. `SearchFilter` 는 `spec: specs.Spec = field(init=False, repr=False)`(domain/queries.py:52)라는 **생성자 인자가 아닌 파생 필드**를 두고 `__post_init__` 에서 `self.spec = self._build_spec()` 로 평범하게 대입하는데, frozen 이면 이 대입도 `FrozenInstanceError` 가 되어 `object.__setattr__` 로 우회해야 합니다.

> **frozen 인데 어떻게 수정하나요?** `TransactionPatch` 는 수정 대상이 아니라 수정 *요청*이고, 실제 수정은 `Transaction.with_patch` 가 **새 객체를 만들어** 수행합니다(§1.6). 불변 객체를 다루는 표준 방식입니다.

### 1.4 `__post_init__` — 자동 생성 `__init__` 직후에 실행되는 검증 훅

**개념.** dataclass 가 만들어 주는 `__init__` 은 "받은 값을 필드에 대입"까지만 합니다. 값 검증·정규화를 끼워 넣고 싶을 때를 위해 dataclass 는 특별한 훅을 제공합니다. 클래스에 `__post_init__` 메서드를 정의해 두면, **자동 생성된 `__init__` 이 모든 필드 대입을 끝낸 직후** 이 메서드를 자동으로 호출합니다.

```
Transaction(id=..., type=..., ...)
        │
        ▼
자동 생성된 __init__     ← 필드에 값 대입만 수행
        │
        ▼
__post_init__            ← 검증·정규화 (여기서 실패하면 객체 생성 자체가 실패)
        │
        ▼
완성된(= 항상 유효한) 인스턴스
```

**실제 코드.**

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

각 줄은 "검증하며 정규화한 값으로 필드를 덮어쓰기" 합니다.

> **⚙️ 내부 동작 — 왜 `self.type = ...` 이 아니라 `object.__setattr__(self, ...)` 인가**
> `frozen=True` 가 `Transaction.__setattr__` 를 "무조건 예외"로 덮어썼기 때문입니다(§1.3).
> `self.type = x` 는 `type(self).__setattr__(self, "type", x)` 로 풀리므로 그 덮어쓴 함수에
> 걸립니다. `object.__setattr__(self, "type", x)` 는 **덮어쓰기 전의 원래 구현을 직접 호출**하는
> 것이라 검사를 지나쳐 인스턴스 `__dict__` 에 바로 씁니다.
> dataclass 자신도 `frozen` 클래스의 생성된 `__init__` 안에서 정확히 같은 수법을 씁니다 —
> 즉 이 코드는 우회로가 아니라 **표준이 정한 정규 통로**입니다.
> `_set = object.__setattr__` 은 그 긴 이름을 지역 변수에 한 번만 담아 둔 것뿐입니다.
> → [12 §1-B](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `__post_init__` 은 어떻게 불리나** — 특별한 훅 등록 같은 것이 아닙니다.
> `@dataclass` 는 클래스에 `__post_init__` 이라는 이름이 있으면
> **생성된 `__init__` 소스의 마지막 줄에 `self.__post_init__()` 호출문을 덧붙일 뿐**입니다.
> 없으면 그 줄을 아예 만들지 않습니다. 그래서 (1) 모든 필드 대입이 끝난 뒤에 불리고,
> (2) 여기서 예외가 나면 `__init__` 이 예외로 끝나므로 **객체가 호출자에게 도달하지 못합니다**.
> "생성자 불변식"이 성립하는 기계적 근거가 이것입니다. → [12 §1-B](./12-syntax-and-stdlib.md) 예를 들어 `parse_type` 은 `"  Income "` 을 `"income"` 으로 소문자·공백 정규화하고, 허용 목록에 없으면 `ValidationError` 를 던집니다. 즉 **예외 없이 생성이 끝난 `Transaction` 은 언제나 유효한 상태**입니다.

`Budget` 과 `Category` 도 같은 패턴입니다.

budget_app/domain/entities.py:164-166

```python
    def __post_init__(self) -> None:
        object.__setattr__(self, "month", validators.parse_month(self.month))
        object.__setattr__(self, "amount", validators.parse_amount(self.amount))
```

**설계 의도.** 이것이 이 프로젝트의 핵심 설계인 **"생성자 불변식(constructor invariant)"** 입니다. 거래 객체가 만들어지는 경로는 최소 네 가지입니다 — (1) CLI 대화형 입력 → 서비스의 `add`, (2) JSONL 파일에서 읽는 `from_dict`, (3) CSV import, (4) 수정 시 `with_patch`. 검증을 각 경로에 흩어 놓으면 한 경로를 빠뜨리는 순간 불량 데이터가 들어옵니다. `__post_init__` 하나에 모아 두면 **어떤 경로로 만들어져도 반드시 이 지점을 통과**하므로, "검증을 깜빡한 경로"라는 것이 존재할 수 없습니다.

> **💡 쉽게 말하면** — 출입구가 하나뿐인 건물입니다. 어느 길로 왔든 그 문을 지나야 안으로 들어올 수 있고, 문에는 검사대가 있습니다. 거래 객체가 만들어지는 길은 위의 네 갈래인데 문은 `__post_init__` 하나뿐이라, "검사를 안 받고 들어온 거래"가 원리적으로 있을 수 없습니다.
> 다만 이 비유는 검사가 **들어올 때 한 번**이라는 데서 깨집니다 — 이미 파일에 적혀 있는 잘못된 줄이 그 자리에서 걸러지는 것은 아니고, 그 줄을 다시 읽어 객체로 세우는 순간에야 걸립니다(§8.4 는 그 성질을 이용해 옛 날짜 표기를 읽으면서 고쳐 나갑니다).

**리팩터 포인트 — 규칙 자체는 여기 없습니다.** 위 코드의 각 줄이 `validators.parse_*` 를 호출할 뿐 규칙을 담고 있지 않다는 점에 주목하세요. 이전에는 `validate_type`/`validate_date` 가 클래스 안 staticmethod 였는데, 그 이유가 "CLI 의 재입력 루프가 검증기를 콜러블로 넘겨야 해서"였습니다. 즉 **하위 계층(모델)의 공개 API 모양이 상위 계층(CLI)의 편의로 정해진** 상태였습니다. 지금은 규칙이 `validators.py` 모듈 함수이고, 모델·CSV 어댑터·대화형 입력이 모두 같은 함수를 호출합니다(§2.2).

### 1.5 `SearchFilter` — 조건에도 같은 규칙을 적용

`__post_init__` 은 저장 엔티티만의 것이 아닙니다. 질의 조건도 정규화가 필요합니다.

budget_app/domain/queries.py:32-55

```python
@dataclass
class SearchFilter:
    """거래 검색 조건 — CLI 옵션 묶음을 명세로 번역한다.
    ...
    """

    date_from: str | None = None  # YYYY-MM-DD
    date_to: str | None = None
    category: str | None = None
    type: str | None = None  # income/expense
    query: str | None = None  # memo 부분 일치
    tag: str | None = None

    #: 조립된 명세 — 생성 시 한 번만 만든다(거래마다 다시 만들지 않는다)
    spec: specs.Spec = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.spec = self._build_spec()
```

모든 필드가 `X | None = None` 이므로 "지정 안 한 조건은 통과"라는 의미가 자연스럽게 표현됩니다. 판정 자체는 `matches` 안에 없습니다 — `__post_init__` 이 지정된 조건만 골라 명세(`specs`)로 조립해 두고, `matches` 는 그 명세에 물어보기만 합니다([§10.1](#101-specification--검색-조건이-and-로-고정돼-있던-문제)).

budget_app/domain/queries.py:80-82

```python
    def matches(self, tx: Transaction) -> bool:
        """조립해 둔 명세에 판정을 위임한다."""
        return self.spec.is_satisfied_by(tx)
```

세 가지를 눈여겨보세요.

1. **정규화는 명세의 생성자가 합니다.** `SearchFilter` 자신은 값을 손대지 않고 `_build_spec` 이 `specs.DateFrom(self.date_from)` 처럼 넘기는데, `DateFrom.__init__` 이 `validators.parse_date` 를 부릅니다(domain/specs.py:175-176). 그래서 잘못된 날짜를 주면 **`SearchFilter` 를 만드는 순간** `ValidationError` 가 나고, CLI 는 날짜를 미리 검증할 필요가 없습니다(cli/handlers.py:58-69 의 `cmd_search` 가 인자를 그대로 넘기기만 하는 이유).
2. **`for_month` 는 대체 생성자(classmethod)입니다.** "월 전체"라는 자주 쓰는 조건을 이름 있는 생성 방법으로 제공합니다. `summary` 와 `export` 가 이 하나를 공유하므로 "이 달에 속하는가"의 정의가 프로그램 전체에 하나뿐입니다.
3. **명세는 거래마다 다시 만들지 않습니다.** `spec` 이 `field(init=False)` 인 파생 필드라 조립은 필터 생성 시 딱 한 번이고, 10만 건을 훑는 동안에는 이미 만들어진 객체 트리에 `is_satisfied_by` 만 반복해서 묻습니다.

> **🔎 문법의 출처** — `date_from: str | None = None` 의 `|` 는 PEP 604 로 파이썬 3.10 에
> 들어온 유니온 표기입니다. 그 전에는 `typing.Optional[str]` 또는 `typing.Union[str, None]`
> 을 썼습니다. 이 프로젝트의 `requires-python = ">=3.10"` 이 이 표기를 어노테이션 밖
> (예: `isinstance` 인자)에서도 쓸 수 있게 하는 하한선입니다.
> → [12 §1-C](./12-syntax-and-stdlib.md)

**설계 의도.** 검색 조건 6개를 함수 인자로 일일이 넘기면 시그니처가 비대해지고, 조건이 하나 늘 때마다 호출부 전체를 고쳐야 합니다. `SearchFilter` 하나로 묶으면 시그니처는 `stream_sorted(flt)` 로 고정되고, "이 거래가 조건에 맞는가"라는 판정 로직도 조건 데이터 바로 옆에 응집됩니다.

### 1.6 `@property` — 저장하지 않고 계산하는 필드

**개념.** `@property` 는 메서드를 **속성처럼** 읽게 만듭니다. `summary.usage_pct` 처럼 괄호 없이 씁니다.

> **⚙️ 내부 동작** — `property` 는 문법이 아니라 **내장 클래스**이고, `@property` 는
> `usage_pct = property(usage_pct)` 로 풀립니다(§4.2 의 데코레이터 해체와 같은 규칙).
> 이렇게 만들어진 객체는 `__get__` 을 가진 **디스크립터**라, 속성 조회가
> "인스턴스 `__dict__` → 클래스" 순서로 이름을 찾다가 클래스에서 디스크립터를 만나면
> 값을 돌려주는 대신 `__get__` 을 호출합니다. 그래서 `summary.usage_pct` 라고 쓰면
> 그 자리에서 함수가 실행됩니다 — **저장된 값이 아니라 매번 계산된 값**입니다.
> `setter` 를 정의하지 않았으므로 셋 다 읽기 전용이고, 대입하면 `AttributeError` 입니다.
> → [12 §1-B](./12-syntax-and-stdlib.md)

**실제 코드.**

budget_app/domain/results.py:22-55

```python
@dataclass(frozen=True)
class MonthlySummary:
    """월별 요약 — 집계 원자료만 담고 파생값은 property 로 계산한다.

    ``usage_pct`` 가 ``None`` 인 경우가 둘("예산 미설정" / "예산이 0")인데,
    화면에서는 둘 다 ``N/A`` 로 같게 보인다. 그 판단 근거를 모델에 두면
    프레젠터는 ``None`` 여부만 보면 되고 규칙을 몰라도 된다.
    """
    ...
        """보여줄 것이 아무것도 없는가 — 거래도 예산도 없을 때만 참."""
        return not self.has_data and self.budget is None
```

**설계 의도.** `balance` 는 `income - expense` 이므로 저장하면 **같은 정보를 두 번 갖게 되고, 둘이 어긋날 수 있습니다**. property 로 두면 언제 읽어도 일관됩니다.

더 중요한 것은 **계산 규칙의 소속**입니다. 리팩터 전에는 서비스가 문자열 키 dict 를 만들어 `result["usage_pct"]` 를 채웠고, "예산이 없으면 N/A" 같은 해석을 CLI 가 했습니다. 지금은 서비스가 **원자료만** 담아 넘기고, 파생값은 모델이 계산하며, 프레젠터는 `None` 인지만 봅니다.

budget_app/cli/presenter.py:81-88

```python
def _budget_lines(summary: MonthlySummary) -> Iterator[str]:
    usage = summary.usage_pct
    usage_str = (
        messages.FMT_USAGE_PCT.format(usage=usage) if usage is not None else messages.MSG_USAGE_NA
    )
    yield messages.MSG_SUMMARY_BUDGET.format(amount=summary.budget.amount, usage=usage_str)
    if summary.over_budget:
        yield messages.MSG_OVER_BUDGET
```

프레젠터는 "예산이 0이면 사용률이 무의미하다"는 도메인 규칙을 **모릅니다**. 그건 `usage_pct` 가 이미 알고 있습니다.

### 1.7 `fields` 와 `asdict` — dataclass 를 다루는 두 도구, 그중 하나만 씀

**`asdict` 는 이 코드에 없습니다 — 그것이 요점입니다.** `dataclasses.asdict` 는 인스턴스의 모든 필드를 `{필드명: 값}` dict 로 바꿔 주는 편의 함수인데, **중첩된 dataclass 를 만나면 그것까지 재귀적으로 dict 로 풉니다.** 그래서 `Transaction` 에는 쓸 수 없습니다.

budget_app/domain/entities.py:82-97

```python
    def to_dict(self) -> dict:
        """JSONL 한 줄이 될 dict.

        ``asdict()`` 를 쓸 수 없다 — ``TransactionId`` 가 dataclass 라
        ``{"id": {"value": "TX-000001"}}`` 처럼 중첩돼 저장 형식이 깨진다.
        값 객체는 **경계에서 원시 값으로 풀어** 내보낸다.
        """
        return {
            "id": self.id.value,
            "type": self.type,
            "date": self.date,
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo,
            "tags": list(self.tags),
        }
```

`id` 는 `TransactionId` 값 객체이고 그것 역시 `@dataclass(frozen=True)` 입니다(domain/tx_id.py:52). `asdict(tx)` 를 부르면 `{"id": {"value": "TX-000001"}, ...}` 가 나와 파일 형식이 통째로 달라집니다. 그래서 손으로 씁니다 — `self.id.value` 로 **경계에서 원시 문자열로 풀고**, `tags` 는 튜플을 `list()` 로 바꿉니다(JSON 에 튜플 타입이 없어 `json.dumps` 가 어차피 배열로 쓰지만, 왕복 시 형태가 흔들리지 않도록 여기서 확정합니다). `Budget.to_dict`(domain/entities.py:168-169)와 `Category.to_dict`(domain/entities.py:185-186)는 필드가 1~2개라 애초에 손으로 쓰는 편이 짧습니다.

> **⚙️ 내부 동작** — `asdict` 는 필드를 훑으며 값이 dataclass 면 자기 자신을 재귀 호출하고,
> list/tuple/dict 면 원소마다 같은 처리를 한 뒤 **`copy.deepcopy` 로 나머지 값을 복사**합니다.
> "얕게 한 겹만 풀기"라는 옵션이 없다는 점이 여기서 결정적이었습니다.
> 한 겹만 필요하면 `dataclasses.fields` 로 직접 도는 편이 정확합니다.
> → [12 §1-B](./12-syntax-and-stdlib.md)

**`fields`** 는 dataclass 의 필드 메타데이터 목록을 돌려줍니다.

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

`fields(self)` 로 필드를 순회하고 `getattr` 로 값을 꺼냅니다. **필드 이름을 코드에 나열하지 않으므로, `TransactionPatch` 에 필드를 추가해도 이 함수는 고칠 필요가 없습니다.** 손으로 나열했다면 필드 추가 시 여기를 빠뜨려 "그 필드만 수정이 안 되는" 버그가 났을 것입니다.

> **⚙️ 내부 동작** — `@dataclass` 는 처리한 필드 정보를 클래스 속성
> `__dataclass_fields__`(이름 → `Field` 객체 dict)에 저장해 둡니다. `fields(obj)` 는 그 dict 를
> 꺼내 `ClassVar`/`InitVar` 같은 의사(pseudo) 필드를 걸러 튜플로 돌려줄 뿐이고
> (`field(init=False)` 로 선언한 필드는 걸러지지 않고 그대로 나옵니다), `Field` 객체에는
> `.name`, `.type`, `.default`, `.metadata` 가 들어 있습니다. 이 함수가 dataclass 가 아닌
> 객체를 받으면 `TypeError` 를 내는 것도 이 속성이 없기 때문입니다.
> `isinstance(x, dataclass)` 같은 검사가 불가능한(`@dataclass` 는 클래스를 만들지 않으므로)
> 대신 `dataclasses.is_dataclass(x)` 가 바로 이 속성의 유무를 봅니다.
> → [12 §1-B](./12-syntax-and-stdlib.md)

### 1.8 `with_patch` — 불변 갱신 관용구

budget_app/domain/entities.py:113-124

```python
    def with_patch(self, patch: TransactionPatch) -> Transaction:
        """부분 변경을 적용한 **새 Transaction** 을 만든다.
        ...
        """
        return Transaction(**{**self.to_dict(), **patch.changed_fields()})
```

세 가지 기법이 한 줄에 겹칩니다.

1. `{**A, **B}` — 딕셔너리 병합. 겹치는 키는 **B 가 이깁니다**(변경분이 원본을 덮어씀).
2. `Transaction(**{...})` — 완성된 dict 를 키워드 인자로 펼침.
3. **새 객체 생성** — 그래서 `__post_init__` 이 다시 돌고, 변경된 값도 검증을 통과합니다.

이름의 `with_` 접두사는 "이 객체를 바탕으로 ~을 바꾼 새 객체"를 뜻하는 함수형 프로그래밍 관례입니다(`dataclasses.replace` 와 같은 계열).

> **🔎 문법의 출처** — `{**A, **B}` 로 딕셔너리를 병합하는 표기는 PEP 448
> (Additional Unpacking Generalizations)로 파이썬 3.5 에 들어왔습니다. 그 전에는
> `d = dict(A); d.update(B)` 두 줄이거나 `dict(A, **B)`(키가 문자열일 때만) 였습니다.
> 참고로 3.9 에는 `A | B` 라는 더 짧은 표기도 생겼지만 이 코드는 `{**A, **B}` 를 씁니다 —
> 같은 줄에서 `Transaction(**...)` 언패킹과 표기를 맞추기 위해서입니다.
> → [12 §1-A](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — `Transaction(**d)` 의 `**` 는 dict 를 **키워드 인자로 펼치는** 호출
> 문법입니다. 인터프리터가 dict 의 키를 매개변수 이름과 맞춰 보므로, 키가 하나라도
> 매개변수에 없으면 `TypeError: got an unexpected keyword argument` 가 즉시 납니다.
> 즉 `to_dict()` 의 키 집합과 `__init__` 의 매개변수 이름이 어긋나는 순간 조용히 넘어가지
> 않고 그 자리에서 터집니다 — 왕복(round-trip)이 깨졌는지 알려 주는 안전장치입니다.
> → [12 §1-A](./12-syntax-and-stdlib.md)

---

## 2. 메서드 3종과 "클래스에 둘 것 / 모듈에 둘 것"

**개념.** 파이썬 클래스의 메서드는 첫 인자가 무엇이냐에 따라 세 종류로 나뉩니다.

| 종류 | 첫 인자 | 접근 가능 대상 | 이 프로젝트의 예 |
|---|---|---|---|
| 인스턴스 메서드 | `self` | 인스턴스 필드 + 클래스 | `tx.to_dict()`, `flt.matches(tx)` |
| `@classmethod` | `cls` (클래스 자체) | 클래스(생성자 포함) | `Transaction.from_dict(d)`, `SearchFilter.for_month(m)` |
| `@staticmethod` | 없음 | 둘 다 접근 불가 (그냥 함수) | **이 프로젝트에는 남아 있지 않습니다** |

- **인스턴스 메서드**는 "이 객체의 데이터"가 필요할 때 씁니다.
- **classmethod** 는 인스턴스가 아직 없는 상태에서 클래스 자체가 필요할 때, 특히 **대체 생성자(alternative constructor)** 를 만들 때 씁니다.
- **staticmethod** 는 클래스와 논리적으로 관련은 있지만 `self` 도 `cls` 도 필요 없는 순수 함수를, 이름공간 정리 목적으로 클래스 안에 두는 것입니다.

> **⚙️ 내부 동작 — 세 종류를 가르는 것은 디스크립터입니다** — 클래스 본문의 `def` 는
> 그냥 함수 객체이고, 함수는 `__get__` 을 가진 디스크립터입니다. `tx.to_dict` 로 꺼낼 때
> 그 `__get__` 이 **인스턴스를 첫 인자로 미리 채운 바운드 메서드**를 만들어 돌려주기
> 때문에 `self` 가 자동으로 넘어갑니다. `@classmethod` / `@staticmethod` 는 그 `__get__`
> 동작만 바꾸는 래퍼 객체입니다 — 전자는 **클래스**를 첫 인자로 채우고, 후자는 아무것도
> 채우지 않고 원래 함수를 그대로 돌려줍니다. 그래서 `staticmethod` 로 감싼 함수는
> "클래스 안에 넣어 둔 모듈 함수"와 실행 의미가 완전히 같고, §2.2 에서 그것을 모듈 함수로
> 되돌릴 때 호출부가 한 글자도 달라지지 않았던 이유가 이것입니다.
> → [12 §1-B](./12-syntax-and-stdlib.md)

### 2.1 `from_dict`(classmethod) / `to_dict` — 직렬화 왕복 패턴

budget_app/domain/entities.py:99-111

```python
    @classmethod
    def from_dict(cls, data: dict) -> Transaction:
        # 필수 키는 하드 접근(누락 시 KeyError → 저장소가 손상 줄로 처리).
        # 검증·정규화는 __post_init__ 이 일괄 수행하므로 여기서는 형태만 넘긴다.
        return cls(
            id=data["id"],
            type=data["type"],
            date=data["date"],
            amount=data["amount"],
            category=data["category"],
            memo=data.get("memo"),
            tags=data.get("tags"),
        )
```

`to_dict` 와 짝을 이루어 다음의 **직렬화 왕복(round-trip)** 을 구성합니다. 직렬화란 객체를 파일에 적을 수 있는 형태로 펴는 일이고, 왕복이란 폈다가 되돌렸을 때 같은 것이 나오는가입니다.

```
Transaction 객체 ──to_dict()──▶ dict ──json.dumps──▶ 파일의 한 줄(JSONL)
       ▲                                                    │
       └──__post_init__ 재검증◀──from_dict()◀──json.loads──┘
```

**설계 의도.** `from_dict` 가 인스턴스 메서드일 수는 없습니다 — 객체를 **만들기 전**이니 `self` 가 없기 때문입니다. 모듈 함수로 둘 수도 있지만, classmethod 로 클래스에 붙이면 "Transaction 을 만드는 방법"이 클래스 안에 응집되고 `cls(...)` 호출이 `__post_init__` 검증까지 자동으로 태웁니다.

필수 키(`data["id"]` 등)는 대괄호 하드 접근이라 누락 시 `KeyError` 가 나는데, 이는 버그가 아니라 **의도된 신호**입니다 — 저장소의 `_parse_line`(storage/jsonl.py:181-191)이 `_LINE_ERRORS` 튜플로 그 `KeyError` 를 "손상된 줄"로 잡기 때문입니다(storage/jsonl.py:38-40). 선택 키(`memo`, `tags`)는 `.get()` 으로 `None` 을 허용하고, `parse_memo(None) → ""`, `parse_tags(None) → []` 가 이를 정상값으로 정규화합니다.

**`cls` 라서 얻는 것 — 제네릭 저장소.** `JsonlStore` 는 어떤 엔티티를 다루는지 모른 채 한 줄을 세웁니다.

budget_app/storage/jsonl.py:186-187

```python
        try:
            entity = self.entity_cls.from_dict(data)
```

`self.entity_cls` 는 하위 클래스가 지정한 dataclass(`Transaction`/`Category`/`Budget`)입니다. 세 클래스가 **같은 이름의 classmethod 를 갖고 있기 때문에** 이 한 줄이 셋 모두에 동작합니다. 이것이 파이썬의 덕 타이핑(duck typing — 타입이 무엇인지 묻지 않고, 필요한 메서드가 있으면 그냥 부르는 방식)이며, 공통 조상 클래스를 만들지 않고도 다형성(같은 호출이 대상에 따라 알아서 다르게 동작하는 성질)을 얻는 방법입니다.

### 2.2 왜 `@staticmethod` 검증기를 없앴는가 (리팩터 핵심)

리팩터 전 `models.py` 에는 이런 코드가 있었습니다.

```python
# (리팩터 전 — 지금은 없는 코드)
    @staticmethod
    def validate_amount(value: Any) -> int:
        # 공용 규칙은 모듈 함수에 있다(Budget 도 같은 규칙을 쓴다). CLI 의 _ask_until
        # 이 이 staticmethod 를 callable 로 넘겨 쓰므로 얇은 위임으로 남겨 둔다.
        return validate_amount(value)
```

주석이 스스로 문제를 고백하고 있습니다. **실질이 없는 위임 메서드가 존재하는 유일한 이유가 "CLI 가 이런 모양으로 부르고 싶어서"** 였습니다. 같은 규칙이 세 형태(모듈 함수 / staticmethod 위임 / 클래스별 staticmethod)로 존재했고, 어느 것을 불러야 하는지 코드만 봐서는 알 수 없었습니다.

지금은 규칙이 전부 `validators.py` 의 모듈 함수입니다.

budget_app/domain/validators.py:1-2 (모듈 docstring)

```python
"""필드 규칙 — "이 값이 유효한가"를 판단하는 단 하나의 정의처.

```

**모듈 함수도 콜러블(괄호를 붙여 부를 수 있는 것)입니다.** staticmethod 가 제공하던 "인스턴스 없이 참조해서 넘길 수 있다"는 성질은 모듈 함수가 더 잘 만족합니다.

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

`Transaction.validate_date` 대신 `validators.parse_date` 를 넘길 뿐, 형태는 똑같습니다. **staticmethod 를 유지할 이유가 애초에 없었던 것**입니다.

**교훈**: "이 메서드가 클래스 안에 있어야 하는가?"를 물을 때, 기준은 *`self`/`cls` 를 쓰는가* 이지 *호출부가 어떻게 보이고 싶은가* 가 아닙니다. 과제 방어에서 나오기 좋은 질문입니다.

### 2.3 classmethod 를 대체 생성자로 쓰기

`from_dict` 외에 하나가 더 있습니다.

budget_app/domain/queries.py:74-78

```python
    @classmethod
    def for_month(cls, month: str, **extra: Any) -> SearchFilter:
        """월 전체를 덮는 필터 — 요약과 내보내기가 같은 경계를 쓰게 한다."""
        start, end = month_range(month)
        return cls(date_from=start, date_to=end, **extra)
```

`SearchFilter(date_from=..., date_to=...)` 를 직접 부르는 대신 `SearchFilter.for_month("2024-01")` 라고 쓰면 **의도가 이름에 드러납니다.** `**extra` 덕분에 `SearchFilter.for_month("2024-01", type="expense")` 처럼 조건을 덧붙일 수도 있습니다.

---

## 3. 제너레이터 심화

### 3.1 yield 의 원리 — 지연 평가, 상태 보존, 1회성 소진

**개념.** 함수 본문에 `yield` 가 하나라도 있으면 그 함수는 **제너레이터 함수**가 됩니다. 이 함수는 호출해도 본문이 실행되지 않고, **제너레이터 객체**를 하나 돌려줄 뿐입니다. 실제 실행은 소비자(예: `for` 루프)가 다음 값을 요구할 때 시작되며, 그때마다 본문이 **다음 `yield` 까지만** 나아갑니다. 핵심 성질은 세 가지입니다.

1. **지연 평가(lazy)**: 값은 요구되는 순간에 하나씩 만들어집니다. 소비자가 중간에 `break` 하면 나머지는 아예 계산되지 않습니다.
2. **상태 보존**: `yield` 에서 멈출 때 지역 변수·파일 위치·루프 진행 상태가 그대로 얼어붙었다가, 다음 요청 때 그 지점부터 재개됩니다.
3. **1회성 소진**: 한 번 끝까지 소비한 제너레이터는 재사용할 수 없습니다. 다시 순회하려면 제너레이터 함수를 다시 호출해 새 객체를 만들어야 합니다.

> **💡 쉽게 말하면** — 책을 통째로 복사해 가방에 넣는 대신, 열람실에서 한 장씩 넘겨 보는 것입니다. 찾던 대목이 나오면 거기서 덮고 나오면 되고, 뒷장은 아예 펼치지도 않습니다. 그래서 거래가 10만 건이어도 `stream()` 이 한 번에 손에 들고 있는 것은 한 줄뿐입니다(전체 정렬이 필요한 `stream_sorted` 와 파일을 다시 쓰는 `rewrite` 는 예외라 모아 두는 부분이 있습니다 — §3.3·§3.5).
> 다만 이 비유는 책이라면 앞으로 되돌려 다시 볼 수 있다는 데서 깨집니다 — 제너레이터는 한 번 끝까지 넘기면 그것으로 끝이라, 다시 보려면 처음부터 새로 빌려 와야 합니다(위의 세 번째 성질).

타입 표기 `Iterator[T]` 는 "T 를 하나씩 내놓는 반복자"라는 뜻으로, 제너레이터 함수의 반환 타입 표기로 관례처럼 쓰입니다.

> **⚙️ 내부 동작 — "호출해도 본문이 안 돈다"는 컴파일 시점에 결정됩니다** — 실행 중에
> `yield` 를 만나서 그렇게 되는 것이 아닙니다. 컴파일러가 함수 본문을 훑어 `yield` 를
> 발견하면 그 코드 객체에 **`CO_GENERATOR`(값 32) 플래그**를 켭니다. 호출 시점에는
> 인터프리터가 그 플래그만 보고 프레임을 실행하는 대신 **제너레이터 객체를 만들어
> 즉시 반환**합니다(3.13 에서 `f.__code__.co_flags & inspect.CO_GENERATOR` 로 확인 가능).
> 그래서 `iter_raw()` 를 불러 놓고 소비하지 않으면 `open()` 조차 실행되지 않습니다 —
> §3.2 의 "첫 값을 요구하는 순간에야 파일이 열린다"가 바로 이 결과입니다.
> → [12 §1-C](./12-syntax-and-stdlib.md)

> **🔎 문법의 출처** — 기본 제너레이터(`yield` 문)는 PEP 255 로 파이썬 2.2 에 들어왔고,
> `yield` 를 **식**으로 만들어 값을 보낼 수 있게 한 것이 PEP 342(2.5),
> 다른 반복자에 위임하는 `yield from` 이 PEP 380(3.3)입니다.
> 이 프로젝트는 셋 중 **문으로서의 `yield`** 와 **`yield from`** 만 씁니다 —
> `send()`/코루틴 용법은 한 곳도 없습니다. → [12 §1-C](./12-syntax-and-stdlib.md)

### 3.2 읽기 경로가 둘 — `iter_raw()` 와 `stream()`

리팩터의 가장 중요한 변화가 여기 있습니다. 이전에는 읽기 제너레이터가 `stream()` 하나였고, 그것이 파싱 실패 줄을 건너뛰었습니다. 그런데 **파일을 다시 쓰는 작업도 같은 `stream()` 을 재료로 썼기 때문에**, 무관한 거래 하나를 지우면 손상된 줄이 디스크에서 영구 삭제됐습니다.

지금은 둘로 나뉘어 있습니다.

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

동작을 줄 단위로 추적하면 다음과 같습니다.

- `if not self.path.exists(): return` — **제너레이터 함수 안의 인자 없는 `return` 은 "여기서 끝"** 이라는 뜻입니다. 값을 하나도 내놓지 않고 즉시 `StopIteration` 이 됩니다. 파일이 없으면 "빈 반복"이 되므로 호출부가 예외 처리를 하지 않아도 됩니다.
- `with open(...)` — 소비자가 **첫 값을 요구하는 순간**에야 파일이 열립니다(지연 평가). 제너레이터가 끝까지 소비되거나 버려지면 `with` 가 파일을 닫습니다.
- `for lineno, raw in enumerate(f, start=1)` — 파일 객체 자체가 "한 줄씩" 내놓는 반복자이므로, 전체 파일을 메모리에 올리지 않습니다.
- `yield self._parse_line(lineno, line)` — **여기서 실행이 멈춥니다.**

`_parse_line` 은 예외를 던지지 않고 **상태를 담은 값**을 돌려줍니다.

budget_app/storage/jsonl.py:95-111

```python
@dataclass(frozen=True)
class RawLine:
    """파일의 한 줄 — 원문과 해석 결과를 함께 들고 다닌다.

    상태가 셋이다: 원문만 있음(JSON 아님) / dict 까지 됨(도메인 규칙 위반) /
    도메인 객체까지 됨(정상). 재작성 시 앞의 둘은 ``text`` 를 그대로 다시 쓴다.
    """

    lineno: int
    text: str
    data: dict | None = None
    entity: Any | None = None
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.entity is not None
```

그 위에 얹힌 `stream()` 은 "유효한 것만" 걸러 내보내는 얇은 층입니다.

budget_app/storage/jsonl.py:193-203

```python
    def stream(self) -> Iterator[T]:
        """검증을 통과한 도메인 객체만 yield 한다 — 조회 전용 경로.

        손상된 줄은 건너뛰되 조용히 버리지 않고 경고 로그로 남긴다(사용자가
        데이터 이상을 인지할 수 있도록). 파일 자체는 손대지 않는다.
        """
        for raw in self.iter_raw():
            if raw.is_valid:
                yield raw.entity
            else:
                logger.warning(messages.LOG_CORRUPT_LINE, self.path.name, raw.lineno, raw.error)
```

**이것이 제너레이터를 층층이 쌓는(stacking) 전형입니다.** `stream()` 은 자기 파일을 열지 않고 `iter_raw()` 를 소비할 뿐이며, 둘 다 한 번에 한 줄만 메모리에 둡니다.

> **⚙️ 내부 동작 — 인자 없는 `return` 과 `with` 의 수명** — 제너레이터 안의 `return` 은
> 값을 반환하는 것이 아니라 `StopIteration` 을 일으키는 것입니다(`return v` 를 쓰면
> `StopIteration.value` 에 `v` 가 실립니다 — PEP 380 이 정한 규칙이고 여기서는 쓰지 않습니다).
> `for` 문은 그 `StopIteration` 을 잡아 루프를 정상 종료시키므로 호출부에는 "빈 반복"으로만
> 보입니다. `with open(...)` 이 언제 닫히는가도 같은 기계에서 나옵니다 — 제너레이터가
> 끝까지 소비되면 `__exit__` 가 정상 실행되고, 중간에 버려지면 GC 가 `gen.close()` 를 불러
> 정지 지점에 `GeneratorExit` 를 던지며, 그 예외가 `with` 블록을 빠져나가면서 파일이
> 닫힙니다. **즉 파일이 닫히는 시점을 정하는 것은 이 함수가 아니라 소비자입니다.**
> → [12 §1-C](./12-syntax-and-stdlib.md)

### 3.3 제너레이터 체인: stream → SearchFilter → 정렬 → yield

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

데이터가 흐르는 전체 사슬을 그리면 다음과 같습니다.

```
transactions.jsonl (디스크)
      │  한 줄씩 (파일 전체를 올리지 않음)
      ▼
JsonlStore.iter_raw()        ── 제너레이터: 줄 → RawLine (모든 줄 보존)
      │  한 줄씩
      ▼
JsonlStore.stream()          ── 제너레이터: 유효한 것만 통과, 나머지는 경고 로그
      │  한 건씩
      ▼
SearchFilter.matches(tx)     ── 통과한 것만 items 리스트에 축적
      │
      ▼
items.sort(...)              ── (date, id) 역순 = 최신순 정렬
      │  한 건씩 (yield from)
      ▼
presenter.tx_table           ── limit 건수에 도달하면 break
      │
      ▼
output.out_lines             ── stdout 으로 출력
```

**정렬은 본질적으로 전체를 봐야 하는 연산**이라 이 함수는 리스트를 한 번 만듭니다. 그러나 리스트에 들어가는 것은 "필터를 통과한 항목뿐"이므로, 조건이 좁은 검색일수록 메모리 사용이 줄어듭니다. 정렬이 끝난 뒤 다시 `yield from` 으로 내보내는 이유는 소비자가 `limit` 에 도달하면 `break` 할 수 있도록 **출구를 다시 스트림 형태로 유지**하기 위해서입니다.

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

정렬 키 `lambda t: (t.date, t.id)` 는 튜플 비교를 이용합니다 — 날짜가 같으면 id 로 순서가 정해지므로 정렬이 항상 결정적(deterministic)입니다. `t.id` 는 문자열이 아니라 `TransactionId` 값 객체인데, 그 클래스가 `@functools.total_ordering` + `__lt__`(domain/tx_id.py:91-95)를 갖고 있어서 튜플 비교의 두 번째 원소로 그대로 쓸 수 있습니다.

> **⚙️ 내부 동작 — `functools.total_ordering`** — `TransactionId` 는 `__lt__` 하나만
> 정의합니다(비교 기준은 `self.number < other.number`). `total_ordering` 은 클래스에
> 정의된 비교 메서드 중 하나를 찾아 **미리 정해진 변환표**대로 나머지 셋을 채워 넣습니다.
> `__lt__` 를 준 경우 `__gt__`, `__le__`, `__ge__` 가 생기고, 각각은 `__lt__` 를 호출한 뒤
> 결과를 뒤집거나 `not` 을 취하는 함수입니다(`NotImplemented` 는 그대로 전달합니다).
> `__eq__` 는 채워 주지 않는데, 여기서는 `@dataclass` 가 이미 만들어 줍니다.
> 그래서 "메서드 하나 + 데코레이터 한 줄"로 6종 비교가 완성됩니다.
> → [12 §1-B](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — 튜플 비교** — `(a1, b1) < (a2, b2)` 는 사전식(lexicographic)입니다:
> 먼저 `a1 == a2` 인지 보고, 다르면 `a1 < a2` 의 결과가 곧 답이며, 같을 때만 `b` 를 봅니다.
> 그래서 `id` 비교는 **날짜가 같은 거래들 사이에서만** 실제로 일어납니다.
> `list.sort` 는 안정 정렬(Timsort)이지만, 키를 (날짜, id) 로 완전히 결정해 두면
> 안정성에 기대지 않아도 결과가 하나로 정해집니다.
> → [12 §1-A](./12-syntax-and-stdlib.md)

### 3.4 제너레이터를 인자로 넘기기 — `rewrite` 와 `append_all`

리팩터 전에는 `append_many` 안에 중첩 제너레이터 함수 `_rows` 를 정의해 "기존 행 + 신규 행"을 이어 붙였습니다. 지금은 그 역할이 `rewrite(transform, *, extra=...)` 로 일반화되었습니다.

budget_app/storage/jsonl.py:264-268

```python
    def plan_rewrite(
        self,
        transform: Callable[[T], T | None],
        *,
        extra: Iterable[T] = (),
```

`transform` 이 **콜백**, `extra` 가 `Iterable[T]` 라는 것이 요점입니다. `Iterable` 로 받으므로 호출자는 리스트를 줘도 되고 제너레이터를 줘도 됩니다.

다만 `plan_rewrite` 본문은 `extra` 를 의도적으로 **리스트로 한 번에 펼칩니다.**

budget_app/storage/jsonl.py:304-307

```python
        extra_lines = [self._encode(e) for e in extra]
        if extra_lines:
            changed = True
        lines.extend(extra_lines)
```

여기서 제너레이터 식(소괄호)을 쓸 수 없는 이유가 분명합니다 — **"추가할 것이 하나라도 있는가"(`if extra_lines`)를 먼저 알아야** `changed` 를 정할 수 있는데, 제너레이터는 소비하기 전에는 비었는지 알 수 없고 한 번 소비하면 다시 못 씁니다(§3.1 의 1회성 소진). 이 자리는 "지연 평가가 늘 옳지는 않다"는 실제 사례입니다.

`append_all` 은 반대로 `Iterable` 을 그대로 흘려보내므로 제너레이터 식을 그냥 넘길 수 있습니다.

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

마지막 줄의 인자가 제너레이터 식입니다 — 함수 호출의 **유일한 인자**일 때는 소괄호를 생략할 수 있습니다. (`append_all` 자신은 첫 줄에서 `entities = list(entities)` 로 즉시 펼칩니다(storage/jsonl.py:213-218) — 여기서도 "비었는가"와 "몇 건인가"를 둘 다 알아야 하기 때문입니다.)

> **🔎 문법의 출처** — 제너레이터 식은 PEP 289 로 파이썬 2.4 에 들어왔습니다.
> 리스트 컴프리헨션(PEP 202, 2.0)이 먼저 있었고, 그 대괄호를 소괄호로 바꾸면
> **리스트를 만들지 않고 하나씩 흘려보내는** 형태가 됩니다. "유일한 인자면 괄호 생략"은
> 문법 자체에 들어 있는 규칙이라 `f(x for x in y)` 는 유효하지만 `f(x for x in y, 1)` 은
> 문법 오류입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

### 3.5 왜 제너레이터인가 — 메모리 O(1) 스트리밍

budget_app/storage/jsonl.py:1-18 (모듈 docstring)

```python
"""JSONL 파일 포맷을 다루는 공통 층 — 어떤 엔티티인지 모른 채 동작한다.

여기 있는 것 셋:

- ``atomic_write_lines``  : 임시 파일 + fsync + ``os.replace``
- ``RawLine``             : 한 줄의 세 가지 상태(원문만 / dict 까지 / 객체까지)
- ``JsonlStore``          : 열기·스트리밍·원자적 재작성 (제네릭)

## 읽기 경로가 둘인 이유

이전에는 읽기 진입점이 ``stream()`` 하나였고 그것이 파싱 실패 줄을 **건너뛰었다**.
그런데 ``delete``/``update``/``reassign`` 이 파일을 다시 쓸 때도 같은 ``stream()`` 을
재료로 썼다. 결과적으로 무관한 거래 하나를 지우면 **손상된 줄이 디스크에서 영구
삭제**됐다. 또 같은 원인으로 ID 스캔이 검증 실패 줄의 id 를 놓쳐 번호가 재발급됐다.

- ``iter_raw()`` — 모든 줄을 원문과 함께 준다. 재작성 경로와 ID 스캔이 쓴다.
- ``stream()``   — 검증을 통과한 도메인 객체만 준다. 조회 경로가 쓴다.
"""
```

**설계 의도 정리.** 거래가 10만 건이어도 `stream()` 이 동시에 들고 있는 것은 "현재 줄 하나 + 객체 하나" 뿐이므로 읽기 자체는 메모리 O(1)입니다.

- `monthly_summary`(services/budgets.py:30-66)처럼 합계만 누적하는 소비자는 끝까지 O(1)
- `category_in_use`(storage/repositories.py:121-124)처럼 `any(tx.category == target for tx in self.stream())` 로 조기 종료하는 소비자는 지연 평가 덕분에 파일 뒷부분을 아예 읽지 않음
- 전체 정렬이 필요한 `stream_sorted` 만 예외적으로 필터 통과분을 모음
- `rewrite` 는 재작성이 목적이라 줄들을 모을 수밖에 없지만, **문자열 상태**로만 들고 있습니다(객체가 아니라)

---

## 4. 데코레이터와 클로저 심화

### 4.1 바탕 개념: 고차 함수와 클로저

**개념.** 파이썬에서 함수는 **일급 객체**(숫자나 문자열처럼 값으로 다룰 수 있는 대상)입니다 — 변수에 담고, 인자로 넘기고, 반환값으로 돌려줄 수 있습니다. 함수를 받거나 돌려주는 함수를 **고차 함수(higher-order function)** 라고 합니다. 여기에 성질이 하나 더 얹힙니다. 안쪽 함수가 바깥 함수의 지역 변수를 참조한 채로 바깥 함수 밖으로 반환되는 경우입니다. 이때 그 변수는 바깥 함수가 끝나도 사라지지 않고, 안쪽 함수에 **캡처**(붙잡혀 따라감)되어 살아남습니다. 이것이 **클로저(closure)** 입니다.

> **💡 쉽게 말하면** — 심부름 쪽지에 가깝습니다. "3을 더해서 가져와"라고 적어 건네면, 쪽지를 쓴 사람이 자리를 떠난 뒤에도 쪽지에 적힌 3은 그대로 남아 있습니다. 아래 예시의 `add3` 이 정확히 그 쪽지입니다.
> 다만 이 비유는 쪽지에 값을 **베껴 적는** 것처럼 들린다는 데서 깨집니다 — 실제로는 값이 든 서랍을 함께 넘기는 쪽에 가까워서, 바깥 함수가 그 뒤에 서랍 속을 바꾸면 안쪽 함수도 바뀐 값을 봅니다. 반대 방향 — 안쪽 함수가 서랍 속을 바꾸는 것 — 은 그냥은 안 되고 `nonlocal` 이라고 따로 선언해야 하는데, §4.6 의 `reassign_category` 가 그 방식으로 바뀐 건수를 세어 옵니다.

```python
# 일반론 예시 — 클로저
def make_adder(n):
    def add(x):
        return x + n      # 바깥의 n 을 캡처
    return add

add3 = make_adder(3)
add3(10)                  # 13 — make_adder 는 이미 끝났지만 n=3 이 살아 있다
```

데코레이터는 이 두 개념의 조합입니다: **"함수를 받아 → 감싼 새 함수를 돌려주는" 고차 함수**이고, 감싼 함수(wrapper)는 원본 `func` 를 클로저로 캡처합니다.

> **💡 쉽게 말하면** — 선물 포장입니다. 안의 물건은 손대지 않고 겉에 포장지와 리본만 더합니다. `@log_call` 이 붙은 함수를 부르면 "불렀다"는 기록 → 원래 함수 → "끝냈다"는 기록 순서로 진행되고, 돌려받는 것은 원래 함수의 결과 그대로입니다.
> 다만 이 비유는 포장이 내용물을 절대 바꾸지 않는다는 데서 깨집니다 — 데코레이터는 결과를 가로챌 수도, 원본을 아예 부르지 않을 수도 있습니다. 실제로 `handle_errors` 는 자기가 잡아 내는 예외를 원본의 반환값 대신 종료 코드로 바꿔 돌려줍니다(`BrokenPipeError` 만은 잡지 않고 그대로 다시 던집니다 — §5.3).

### 4.2 `@log_call` == `func = log_call(func)` 해체

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

`@` 문법은 순전히 설탕(syntactic sugar — 의미는 그대로 두고 표기만 짧고 읽기 좋게 만든 문법)입니다. `@log_call` 이 붙은 `TransactionService.add`(services/transactions.py:27-28)는 클래스 본문이 실행될 때 다음과 **완전히 동일**합니다.

```python
# 일반론 예시 — @ 없이 풀어 쓴 동등 코드
def add(self, ...):
    ...
add = log_call(add)     # add 라는 이름이 이제 wrapper 를 가리킨다
```

즉 `TransactionService.add` 를 호출하면 실제로는 `wrapper` 가 실행되고, wrapper 는 (1) "call add" 디버그 로그 → (2) 캡처해 둔 원본 `func` 호출 → (3) "done add" 로그 → (4) 원본의 반환값 그대로 반환, 순서로 동작합니다.

> **🔎 문법의 출처** — `@데코레이터` 표기는 PEP 318 로 파이썬 2.4 에 들어왔습니다
> (클래스에 붙이는 형태는 PEP 3129, 3.0). 그 전에는 예시 코드처럼 `add = log_call(add)` 를
> `def` 아래에 직접 써야 했고, 이름이 세 번 반복되는 데다 함수가 길면 "이 함수가 감싸져
> 있다"는 사실이 본문 끝에 가서야 드러났습니다. `@` 는 그 정보를 `def` 위로 끌어올린 것뿐이고
> **의미는 완전히 동일**합니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — 겹쳐 쓰면 순서는 아래에서 위로** — 데코레이터를 두 개 쌓으면
> `f = A(B(f))` 로 풀립니다. **적용은 `def` 에 가장 가까운(아래) 것부터, 실행은 가장 바깥(위)
> 것부터**입니다. *(일반론 예시 — 이 소스에는 겹쳐 쓴 자리가 없습니다. 서비스 메서드는
> `@log_call` 셋(services/transactions.py:27, 52, 72)과 `@measure_time` 하나
> (services/budgets.py:30)로 전부 단독 사용이고, `@handle_errors` 도 `cli/app.py:61` 의
> `_dispatch` 한 곳에만 붙습니다.)* 그래서 이 프로젝트에서는 순서 문제를 고민할 필요가
> 없는데, **그 자체가 설계 결과**입니다 — 관측과 오류 처리를 서로 다른 계층에 두었기
> 때문에 한 함수에 둘이 겹칠 일이 생기지 않았습니다(§4.4).
> → [12 §1-C](./12-syntax-and-stdlib.md)

### 4.3 `functools.wraps` 가 없으면 생기는 문제

`wrapper` 는 원본과 다른 별개의 함수 객체이므로, 그냥 반환하면 함수의 **메타데이터가 wrapper 의 것으로 바뀝니다**.

```python
# 일반론 예시 — wraps 가 없을 때
add.__name__      # 'wrapper'   ← 'add' 가 아니다!
add.__doc__       # wrapper 의 docstring (None)
```

`@functools.wraps(func)` 는 `func` 의 `__name__`, `__doc__`, `__module__` 등을 wrapper 로 복사해 이 문제를 막습니다. 이 프로젝트에서 이것이 실질적으로 중요한 이유가 두 가지 있습니다.

1. `log_call` 과 `measure_time` 은 로그에 `func.__name__` 을 찍습니다. `wraps` 가 없으면 로그가 전부 `wrapper` 로 찍혀 무의미해집니다.
2. `handle_errors` 로 감싼 `_dispatch`(cli/app.py:61-81)도 `wraps` 덕분에 디버깅·트레이스에서 원래 이름으로 보입니다.

> **⚙️ 내부 동작 — `wraps` 가 정확히 무엇을 복사하나** — `functools.wraps(f)` 는
> `functools.partial(update_wrapper, wrapped=f)` 이고, `update_wrapper` 가 하는 일은 셋입니다.
> (1) `WRAPPER_ASSIGNMENTS` 에 나열된 이름을 하나씩 **대입**합니다 — 3.13 기준
> `__module__`, `__name__`, `__qualname__`, `__doc__`, `__annotations__`, `__type_params__`.
> (2) `WRAPPER_UPDATES`(= `('__dict__',)`)에 따라 wrapper 의 `__dict__` 를 원본 것으로
> **갱신(update)** 합니다 — 덮어쓰기가 아니라 병합입니다.
> (3) 마지막으로 `wrapper.__wrapped__ = f` 를 심습니다. 이 마지막 하나 덕분에
> `inspect.signature(wrapper)` 가 래퍼의 `(*args, **kwargs)` 가 아니라 **원본의 진짜
> 시그니처**를 되찾아 오고, 필요하면 `func.__wrapped__` 로 원본 함수 자체에 손이 닿습니다.
> 주의할 점은 (1) 이 **얕은 대입**이라는 것입니다 — 원본을 나중에 바꿔도 wrapper 에는
> 반영되지 않습니다. → [12 §2-B](./12-syntax-and-stdlib.md)

### 4.4 데코레이터 3종 비교 — 그리고 **왜 두 파일로 나뉘었나**

이 프로젝트의 데코레이터는 세 개이며 골격은 같고 wrapper 안의 관심사만 다릅니다.

| 데코레이터 | 위치 | wrapper 가 하는 일 | 핵심 구문 | 붙는 곳 |
|---|---|---|---|---|
| `log_call` | decorators.py:37-47 | 호출 전/후 DEBUG 로그 | 순차 실행 | 서비스 3곳 (transactions.py:27, 52, 72) |
| `measure_time` | decorators.py:50-66 | 실행 시간 측정 로그 | `try/finally` | 서비스 1곳 (budgets.py:30) |
| `handle_errors` | **cli/error_handler.py:20-121** | 예외 → 메시지 + 종료 코드 | 다단 `except` | CLI 진입점 1곳 (app.py:61 `_dispatch`) |

**세 개가 한 파일에 있다가 두 파일로 나뉜 것이 리팩터의 핵심 중 하나입니다.**

budget_app/decorators.py:1-2 (모듈 docstring)

```python
"""횡단 관심사 데코레이터 — 관측(로그/실행시간)만 담당한다.

```

**과제 방어 포인트**: "데코레이터로 분리한 공통 기능이 무엇이며, 왜 분리가 필요했는가"라는 질문에는 두 층으로 답할 수 있습니다.

1. **함수 본문에서 분리한 이유** — 로깅·시간 측정·예외 변환은 "어느 함수에나 붙을 수 있는 공통 관심사"라 각 함수에 복사해 넣으면 비즈니스 로직이 묻힙니다.
2. **데코레이터끼리도 분리한 이유** — 관측(어느 계층에서나 쓸 수 있어야 함)과 표현(CLI 만의 정책)은 의존하는 대상이 다릅니다. 한 파일에 두면 계층 역류가 생깁니다.

### 4.5 클로저 팩토리 패턴 — `registered_category_validator`

데코레이터가 아니어도 "함수를 만들어 돌려주는 함수"는 유용합니다.

budget_app/cli/prompts.py:77-109

```python
def registered_category_validator(cat_service: CategoryService) -> Callable[[str], str]:
    """등록된 카테고리만 통과시키는 검증기 (미등록이면 ``ValidationError`` → 재입력).
    ...
    """

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

**왜 팩토리가 필요한가.** `ask_until` 이 기대하는 검증기는 `validator(raw)` — **인자 1개짜리** 콜러블입니다(§9.1). 그런데 카테고리 검증은 입력 문자열 외에 "지금 등록된 카테고리를 아는 서비스(`cat_service`)"라는 문맥이 추가로 필요합니다. `registered_category_validator(ctx.cat_service)` 를 호출하면 그 서비스를 **클로저로 캡처한** 1인자 함수가 만들어지고, 이것을 `validators.parse_date` 같은 모듈 함수들과 **같은 자리에 같은 모양으로** 끼울 수 있습니다.

즉 클로저 팩토리는 "n 인자 함수를 문맥을 미리 채워 1인자 함수로 변환"하는 어댑터입니다. **왜 이 함수가 `validators.py` 가 아니라 `prompts.py` 에 있는지**도 docstring 이 답합니다 — 저장소를 봐야 하므로 순수 필드 규칙이 아니기 때문입니다.

### 4.6 클로저로 상태를 모으는 패턴 — `nonlocal`

`rewrite` 는 `transform` 콜백을 받습니다(§3.4). 그런데 호출자는 "몇 건이 바뀌었는지" 같은 정보도 알아야 합니다. 그 다리 역할을 클로저와 `nonlocal` 이 합니다.

budget_app/storage/repositories.py:194-214

```python
    def reassign_category(self, old: str, new: str) -> int:
        """old → new 카테고리 일괄 재지정. 변경된 건수 반환.

        두 이름 모두 정규화한다. ``old`` 는 비교 대상이라(저장된 값은 정규형),
        ``new`` 는 "바뀐 게 없는데 바뀌었다고 세는" 일을 막기 위해서다.
        """
        source = validators.parse_category(old)
        destination = validators.parse_category(new)
        changed = 0

        patch = TransactionPatch(category=destination)

        def _reassign(tx: Transaction) -> Transaction:
            nonlocal changed
            if tx.category != source:
                return tx
            changed += 1
            return tx.with_patch(patch)

        self.rewrite(_reassign)
        return changed
```

**`nonlocal changed` 가 핵심입니다.** 이것이 없으면 `changed += 1` 은 "`_reassign` 안의 **새 지역 변수** `changed` 를 만들려는 시도"로 해석되어 `UnboundLocalError` 가 납니다. `nonlocal` 은 "이 이름은 바깥 함수의 지역 변수다"라고 선언해 대입이 바깥으로 전달되게 합니다.

(읽기만 할 때는 `nonlocal` 이 필요 없습니다 — 위 코드에서 `source`, `patch` 는 선언 없이 그냥 읽습니다. **대입할 때만** 필요합니다.)

`delete`(storage/repositories.py:150-171)와 `replace`(storage/repositories.py:173-192)도 `nonlocal found` 로 같은 일을 합니다. 이 패턴 덕분에 `rewrite` 는 "무엇을 세는지" 전혀 모른 채 재작성이라는 뼈대만 제공할 수 있습니다.

> **🔎 문법의 출처** — `nonlocal` 은 PEP 3104 로 파이썬 3.0 에 들어온 **예약어**입니다.
> 파이썬 2 에는 없었고, 같은 일을 하려면 `changed = [0]` 처럼 **가변 컨테이너에 담아
> 안쪽에서 원소를 바꾸는** 우회법(`changed[0] += 1`)을 썼습니다. `nonlocal` 은 그 우회를
> 불필요하게 만든 문법입니다. (`global` 과 달리 모듈 전역이 아니라 **가장 가까운 바깥
> 함수 스코프**를 가리킵니다.) → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `UnboundLocalError` 가 나는 진짜 이유** — 파이썬 컴파일러는 함수 본문을
> 훑어 **대입되는 이름은 그 함수의 지역 변수로 확정**합니다. 실행 전에, 정적으로 정해집니다.
> 그래서 `nonlocal` 이 없으면 `changed += 1` 의 `changed` 는 `_reassign` 의 지역 변수가
> 되고, `+=` 는 읽기부터 하는데 아직 값이 없으니 `UnboundLocalError` 입니다.
> `nonlocal changed` 를 쓰면 컴파일러는 바깥 함수의 그 변수를 **cell 객체**에 담고,
> 안쪽 함수는 자기 `__closure__` 튜플로 그 cell 을 공유합니다 — 두 함수가 같은 상자를
> 들여다보는 구조라 안에서 쓴 값이 밖에서 보입니다.
> `reassign_category._reassign.__closure__` 를 찍어 보면 cell 들이 그대로 나옵니다.
> → [12 §1-C](./12-syntax-and-stdlib.md)

---

## 5. 예외 심화

### 5.1 사용자 정의 예외 설계

리팩터에서 두 예외가 `errors.py` 한 곳으로 모였습니다. 그 이유가 모듈 docstring 에 있습니다.

budget_app/errors.py:1-2 (발췌)

```python
"""예외 계층 — 애플리케이션이 직접 정의하는 오류를 한곳에 모은다.

```

**ValidationError — 왜 ValueError 를 상속하는가.**

budget_app/errors.py:33-38

```python
class ValidationError(ValueError):
    """입력값이 필드 규칙을 위반했다 — CLI 단에서 사용자 친화 메시지로 변환된다.

    ``ValueError`` 를 상속하는 이유: 의미상 "값이 잘못됨"이 맞고, 이 예외를 모르는
    호출자도 ``except ValueError`` 로 자연스럽게 받을 수 있다.
    """
```

의미상 "값이 잘못됨"은 파이썬 내장 `ValueError` 의 관할입니다. 이를 상속하면 (1) **is-a 관계가 정확**해지고, (2) 이 앱의 예외를 모르는 외부 코드가 `except ValueError` 로 잡아도 자연스럽게 포섭되며, (3) 앱 내부에서는 `except ValidationError` 로 **내장 ValueError 와 구분해서** 더 정밀하게 잡을 수 있습니다. 본문이 docstring 뿐인 "빈 서브클래스"지만, 예외에서는 **타입 자체가 정보**이므로 이것으로 충분합니다.

**AppError — message + hint 구조.**

budget_app/errors.py:41-51

```python
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

`super().__init__(message)` 로 일반 예외처럼 `str(exc)` 가 메시지를 돌려주게 하면서, `message` 와 `hint` 를 **속성으로도** 보관합니다. 잡는 쪽(`handle_errors`)은 `exc.message` 를 `[오류]` 줄로, `exc.hint` 가 있으면 `[힌트]` 줄로 출력합니다.

> **⚙️ 내부 동작 — `super().__init__(message)` 가 왜 필요한가** — `BaseException.__init__`
> 은 받은 위치 인자를 그대로 `self.args` 튜플에 저장하고, `BaseException.__str__` 은
> `args` 가 한 개면 그 원소를, 비었으면 빈 문자열을, 여럿이면 튜플 표현을 돌려줍니다.
> 그래서 이 한 줄을 빠뜨리면 `str(exc)` 가 `""` 가 되고, `f"[오류] {exc}"` 로 찍는 곳이 전부
> 빈칸이 됩니다. `args` 는 예외를 `pickle` 로 복원할 때도 쓰이는 정규 통로입니다.
> `self.message`/`self.hint` 는 그와 **별개로** 붙인 평범한 인스턴스 속성이라,
> 잡는 쪽이 문자열을 파싱하지 않고 두 조각을 따로 꺼내 쓸 수 있습니다.
> → [12 §1-C](./12-syntax-and-stdlib.md)

**InputAborted — 상속만으로 처리 경로를 얻는다.**

budget_app/cli/prompts.py:28-37

```python
class InputAborted(AppError):
    """대화형 입력이 EOF(Ctrl+D)/스트림 종료로 중단됨.

    ``handle_errors`` 가 ``AppError`` 로 처리하므로 스택트레이스 없이 깔끔히 끝난다.
    이 예외가 없으면 파이프로 입력을 주다가 EOF 가 나는 순간 ``ask`` 가 빈 문자열을
    돌려주고, 검증기가 이를 거부하며 루프가 영원히 돈다.
    """

    def __init__(self) -> None:
        super().__init__(messages.ERR_INPUT_ABORTED, hint=messages.HINT_INPUT_ABORTED)
```

`InputAborted` 는 `AppError` 를 상속하므로 `handle_errors` 의 `except AppError` 절이 **코드 한 줄 추가 없이** 이 예외까지 처리합니다. 예외 계층 설계의 이점 — "새 오류 종류를 추가할 때 잡는 쪽을 고칠 필요가 없다" — 를 그대로 보여주는 예입니다.

**정의 위치도 설계입니다.** `InputAborted` 가 `errors.py` 가 아니라 `prompts.py` 에 있는 이유는, 이 예외가 **대화형 입력이라는 특정 상황에서만** 발생하기 때문입니다. 전 계층이 공유하는 어휘(`ValidationError`/`AppError`)만 `errors.py` 에 둡니다.

### 5.2 raise ... from exc 와 `__cause__`

**개념.** `except` 블록 안에서 다른 예외를 던지면, 파이썬은 원래 예외를 자동으로 `__context__` 에 연결합니다. `raise 새예외 from 원인예외` 라고 명시하면 원인이 `__cause__` 속성에 기록되고, 트레이스백에 "The above exception was the direct cause of the following exception" 으로 표시됩니다. **저수준 예외를 도메인 예외로 번역하면서 원인 사슬을 보존**하는 표준 관용구입니다.

**실제 코드.** EOF(저수준 입력 이벤트)를 앱 도메인 예외로 번역하는 `ask`:

budget_app/cli/prompts.py:52-57

```python
def ask(prompt: str) -> str:
    """대화형 한 줄 입력. EOF 는 무한 대기/무한 루프 대신 즉시 중단으로 처리한다."""
    try:
        return input(prompt)
    except EOFError as exc:
        raise InputAborted() from exc
```

날짜 파싱 실패(`ValueError`)를 검증 오류로 번역하는 `parse_date`:

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

같은 패턴이 `parse_month`(domain/validators.py:112 — 역시 `strptime` 의 `ValueError` 를 번역)와 원자 모드 가져오기 실패(services/importexport.py:115-118 — `ValidationError`/`KeyError` 를 `AppError` 로 번역)에도 반복됩니다.

반면 `parse_amount` 는 `from` 을 쓰지 **않습니다** — 그 함수는 잡을 하부 예외가 애초에 없기 때문입니다. `int()` 에 맡기는 대신 정규식 `_INTEGER` 로 먼저 판정하고 스스로 `raise ValidationError(...)` 하므로(domain/validators.py:65-69), 연결할 원인 예외가 존재하지 않습니다. **`from` 은 "번역"할 때만 쓰는 것**이지 예외를 던질 때마다 붙이는 장식이 아니라는 대비가 여기서 보입니다.

**설계 의도**: 바깥 계층은 `ValidationError`/`AppError` 라는 도메인 어휘만 다루면 되고, 디버깅할 때는 `__cause__` 사슬을 따라 "실제로는 strptime 이 실패했다"는 근본 원인까지 추적할 수 있습니다.

> **🔎 문법의 출처** — 예외 연쇄(`raise B from A`, `__cause__`/`__context__`)는 PEP 3134 로
> 파이썬 3.0 에 들어왔습니다. 파이썬 2 에는 연쇄 자체가 없어서, 저수준 예외를 도메인
> 예외로 바꾸면 **원래 트레이스백이 통째로 사라졌습니다.** 그래서 원인을 남기려면
> 메시지 문자열에 `str(exc)` 를 이어 붙이는 수밖에 없었습니다.
> → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `__cause__` 와 `__context__` 는 다릅니다** — `except` 블록 안에서 예외를
> 던지면 인터프리터가 **자동으로** 원래 예외를 `__context__` 에 넣습니다(`from` 을 안 써도).
> `from exc` 를 명시하면 거기에 더해 `__cause__ = exc` 와 `__suppress_context__ = True` 가
> 설정됩니다. 트레이스백 출력이 갈리는 지점이 이것입니다 —
> `__cause__` 가 있으면 **"직접적 원인(direct cause)"**, 없고 `__context__` 만 있으면
> **"처리 도중 또 다른 예외 발생(During handling ...)"** 으로 표시됩니다.
> 앞은 "의도적으로 번역했다", 뒤는 "핸들러 안에서 사고가 났다"는 뜻이라 디버깅 시
> 읽는 방향이 달라집니다. `ask` 와 `parse_date` 가 `from` 을 붙이는 이유가 이 구분입니다.
> → [12 §1-C](./12-syntax-and-stdlib.md)

### 5.3 except 절의 순서 규칙 — 그리고 "부류별 묶기"

**개념.** `except` 절은 **위에서부터 차례로** 검사되고, 예외 타입이 **처음 매치되는 절 하나**만 실행됩니다. 매치 판정은 `isinstance` 이므로 부모 클래스 절은 자식 예외도 잡습니다. 따라서 **넓은(부모) 타입을 먼저 쓰면 아래의 좁은(자식) 절은 영원히 실행되지 않는 죽은 코드**가 됩니다.

이 프로젝트와 관련된 예외 상속 관계는 다음과 같습니다.

```
BaseException
├── KeyboardInterrupt                (Ctrl+C — Exception 이 아님!)
└── Exception
    ├── OSError                      (입출력 오류의 부모)
    │   ├── FileNotFoundError        ← OSError 보다 먼저 잡아야 함
    │   ├── IsADirectoryError
    │   ├── PermissionError
    │   └── ConnectionError
    │       └── BrokenPipeError
    ├── ValueError
    │   ├── ValidationError          (errors.py 정의)
    │   └── UnicodeError
    │       └── UnicodeDecodeError
    ├── AppError                     (errors.py 정의)
    │   └── InputAborted             (prompts.py 정의)
    └── KeyError, TypeError, ...
```

**실제 코드.** `handle_errors` 의 docstring 이 순서 정책을 직접 설명합니다.

budget_app/cli/error_handler.py:20-40 (docstring)

```python
def handle_errors(func: Callable[..., int]) -> Callable[..., int]:
    """CLI 핸들러 공용 — 예외를 잡아 [오류]/[힌트] 를 **stderr** 로 내보내고 종료 코드를 반환한다.

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
```

**이 docstring 이 중요한 이유**: except 순서는 코드만 봐서는 "왜 이 순서인가"를 알 수 없습니다. 상속 제약(반드시 지켜야 함)과 의미적 분류(읽기 좋으라고 정한 것)가 섞여 있기 때문입니다. 둘을 구분해서 적어 두면, 나중에 절을 추가할 사람이 **어떤 제약은 어겨선 안 되고 어떤 것은 취향인지** 알 수 있습니다.

전체 구조와 각 절의 상세 해설은 [06. 횡단 관심사와 예외 처리](./06-decorators.md)에 있습니다. 여기서는 두 지점만 짚습니다.

**(1) `BrokenPipeError` 는 처리하지 않고 다시 던집니다.**

budget_app/cli/error_handler.py:57-60

```python
        except BrokenPipeError:
            # 하류 파이프(`list | head`)가 먼저 닫힘. 여기서 출력하면 또 깨지므로
            # 최상위(main)로 넘겨 조용히 처리하게 한다.
            raise
```

인자 없는 `raise` 는 "지금 잡은 예외를 그대로 재전파"입니다. 이 절이 없으면 아래의 `except OSError` 가 삼켜서 `[오류] 입출력 오류...` 를 출력하려다 **또 파이프가 깨지는 2차 사고**가 납니다.

**(2) `KeyboardInterrupt` 는 명시적으로 잡아야 합니다.**

`KeyboardInterrupt` 는 `Exception` 이 아니라 `BaseException` 직계이므로, 마지막 `except Exception` 은 이것을 **못 잡습니다**. Ctrl+C 를 관례적 종료 코드 130 으로 처리하려면 별도 절이 필요합니다.

> **⚙️ 내부 동작 — `except` 는 어떻게 절을 고르나** — 인터프리터는 위에서부터 각 절의
> 타입과 던져진 예외를 `issubclass` 로 비교해(`PyErr_GivenExceptionMatches`)
> **처음 참이 되는 절 하나만** 실행하고 나머지는 건너뜁니다. 그래서 순서가 곧 정책입니다.
> `BaseException` 이 계층 꼭대기에 따로 있는 이유도 여기서 나옵니다 —
> `KeyboardInterrupt`/`SystemExit`/`GeneratorExit` 는 "프로그램을 끝내라는 지시"라
> `except Exception:` 이라는 흔한 안전망에 **일부러 걸리지 않도록** 설계된 것입니다.
> 이 코드가 그 셋 중 `KeyboardInterrupt` 만 따로 잡는 것은, 잡아서 무시하려는 것이 아니라
> **종료 코드를 130 으로 정해 주기 위해서**입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

### 5.4 `logger.exception` — 스택트레이스를 어디에 남길 것인가

마지막 안전망에서 스택트레이스를 **버리는 것이 아니라 로그로 옮겨 둡니다**.

budget_app/cli/error_handler.py:106-119

```python
        except Exception as exc:  # noqa: BLE001 — 어떤 예외도 트레이스백으로 끝내지 않기 위함
            # 사용자용 한 줄 요약을 먼저 내고, 그다음에 원인 추적용 기록을 남긴다.
            output.err(messages.MSG_ERR_UNEXPECTED.format(error=exc))
            output.err(messages.HINT_UNEXPECTED)
            # ERROR 인 이유: 이전에는 DEBUG 였고, 기본 로그 레벨이 WARNING 이라
            # **기본 실행에서는 스택트레이스가 아무 데도 남지 않았다.** 여기까지 온
            # 예외는 분류되지 않은 버그이고, 그 스택은 나중에 원인을 찾을 유일한
            # 단서다. `--debug` 를 켜고 재현할 수 있는 상황이 아닐 수도 있다.
            #
            # 트레이스백이 화면에 보이게 되는 것은 감수한다. 이 자리는 "프로그램이
            # 예상하지 못한 상태"이고, 그때는 감추는 것보다 신고할 수 있게 하는 편이
            # 낫다 — 앞선 세 부류(사용자가 고칠 수 있는 오류)는 여전히 한 줄로 끝난다.
            logger.exception(messages.LOG_UNHANDLED)
            return config.EXIT_ERROR
```

`logger.exception(...)` 은 `logger.error(..., exc_info=True)` 의 축약으로, "현재 처리 중인 예외의 전체 트레이스백을 이 로그 레코드에 첨부하라"는 뜻입니다.

> **⚙️ 내부 동작** — `exc_info=True` 를 만나면 logging 은 `sys.exc_info()` 를 불러
> **지금 처리 중인 예외 3종 세트**(타입/값/트레이스백)를 가져와 `LogRecord.exc_info` 에
> 담습니다. 문자열 변환은 그때가 아니라 포매터가 `Formatter.formatException` 을 부를 때
> (내부적으로 `traceback.print_exception`) 일어납니다. 두 가지가 따라옵니다 —
> (1) `except` 블록 **밖**에서 부르면 `sys.exc_info()` 가 `(None, None, None)` 이라
> 트레이스백이 안 붙고, (2) 이 로거가 그 레벨에서 꺼져 있으면 트레이스백 포매팅 비용
> 자체가 발생하지 않습니다. → [12 §2-B](./12-syntax-and-stdlib.md)

**레벨이 DEBUG 에서 ERROR 로 올라간 것이 이 자리의 리팩터입니다.** 이전에는 `logger.debug(..., exc_info=True)` 였는데, 기본 로그 레벨이 WARNING 이라 **평소 실행에서는 스택트레이스가 아무 데도 남지 않았습니다.** "감춘 것"이 아니라 "없앤 것"이었던 셈입니다.

트레이스백이 화면에 보이게 되는 것은 감수합니다. 여기까지 온 예외는 앞의 세 부류 어디에도 속하지 않는 **분류되지 않은 버그**이고, 그때는 감추는 것보다 신고할 수 있게 하는 편이 낫습니다. 사용자가 고칠 수 있는 오류(값 오류·상황 오류·입출력 오류)는 여전히 한 줄로 끝납니다.

### 5.5 예외를 "값"으로 바꾸기 — 오류가 흐름 제어가 아닐 때

예외가 항상 정답은 아닙니다. **한 줄이 깨졌다고 전체를 멈출 이유가 없을 때**는 예외 대신 값으로 표현하는 편이 낫습니다.

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

이 함수는 **예외를 던지지 않습니다.** 세 가지 결과(원문만/dict 까지/객체까지)를 전부 `RawLine` 이라는 한 타입으로 돌려주고, 호출자가 `raw.is_valid` 로 분기합니다.

**왜 이렇게 하는가**: 파일을 읽는 도중 예외가 올라오면 반복이 중단됩니다. 그런데 "손상된 줄 하나"는 나머지 줄을 못 읽을 이유가 되지 않습니다. 예외를 값으로 바꾸면 반복이 계속되면서도 정보(줄 번호, 원문, 오류 내용)를 잃지 않습니다.

같은 판단이 `_resolve_id` 에도 있습니다(services/importexport.py:133-164) — 중복 id 는 정책에 따라 예외일 수도(`error`), 값(`None` = 건너뜀)일 수도 있습니다.

---

## 6. 제네릭 — TypeVar 와 Generic

**개념.** "리스트든 집합이든, 담긴 것의 타입을 그대로 유지하는" 표기를 직접 만들 수 있게 해 주는 것이 제네릭입니다. `TypeVar` 는 "아직 정해지지 않은 타입"을 가리키는 자리표시자입니다. 클래스가 `Generic[T]` 를 상속하면, 그 자리표시자를 밖에서 받아 쓰겠다고 선언하는 것이 됩니다.

> **💡 쉽게 말하면** — 이삿짐 상자에 "내용물: ____" 라벨을 붙여 두는 것과 같습니다. 상자를 접고 테이프를 붙이는 방법은 무엇을 담든 하나면 충분하고, 무엇을 담을지는 쓰는 사람이 그때 적습니다. `JsonlStore` 가 "JSONL 파일 다루는 법"이라는 상자이고, `JsonlStore[Transaction]` 이 라벨을 채운 것입니다.
> 다만 이 비유는 파이썬에서 그 라벨을 **사람과 검사 도구만 읽는다**는 데서 깨집니다 — "그릇"이라고 적은 상자에 책을 넣어도 프로그램은 아무 불평 없이 돌아갑니다. 그래서 실행 중에 실제로 쓸 클래스는 `entity_cls` 라는 평범한 값으로 한 번 더 적어 둡니다(아래 표).

**실제 코드.**

budget_app/cli/prompts.py:25

```python
T = TypeVar("T")
```

budget_app/storage/jsonl.py:131-146

```python
class JsonlStore(Generic[T]):
    """JSONL 파일 하나를 다루는 공통 동작.

    세 저장소가 열기/스트리밍/원자적 재작성 코드를 각자 복사해 갖고 있었다.
    "파일 포맷을 다루는 법"은 여기 한 번만 두고, 하위 클래스는 **엔티티별 규칙**
    (어떤 dataclass 인가, 무엇이 유일 키인가)만 갖는다.
    """

    #: 하위 클래스가 지정 — 줄 하나를 세울 dataclass
    entity_cls: type

    def __init__(self, path: Path) -> None:
        # 생성자는 경로 계산만 한다. 파일/폴더를 만드는 것은 ensure_ready() 의 일이다.
        # (이전에는 생성자가 mkdir·touch·기본 카테고리 시딩까지 해서, 객체를 만드는
        #  것만으로 디스크가 바뀌었다. 오타 난 --data-dir 도 조용히 폴더가 생겼다.)
        self.path = Path(path)
```

하위 클래스는 대괄호로 T 를 채웁니다.

budget_app/storage/repositories.py:27-34

```python
class TransactionRepository(JsonlStore[Transaction]):
    """transactions.jsonl 의 CRUD + 스트리밍 조회."""

    entity_cls = Transaction
    FILE_NAME = config.TX_FILE_NAME

    def __init__(self, data_dir: Path) -> None:
        super().__init__(Path(data_dir) / self.FILE_NAME)
```

`JsonlStore[Transaction]` 이라고 쓰면 부모의 `stream() -> Iterator[T]` 가 이 클래스에서는 `Iterator[Transaction]` 으로 읽힙니다. `CategoryStore(JsonlStore[Category])`, `BudgetStore(JsonlStore[Budget])` 도 같은 방식입니다.

**중요한 구분 — 두 개의 T 가 있습니다.**

| 이름 | 무엇인가 | 언제 쓰이는가 |
|---|---|---|
| `Generic[T]` 의 `T` | **타입 검사 전용** 자리표시자 | mypy/IDE 가 읽음. 런타임에는 아무 일도 안 함 |
| `entity_cls` | **런타임에 실제로 쓰는** 클래스 객체 | `self.entity_cls.from_dict(data)` 로 호출 |

파이썬 제네릭은 **런타임에 지워집니다**(type erasure). `JsonlStore[Transaction]` 을 상속했다고 해서 실행 중에 "T 가 Transaction 이다"를 알 수 있는 게 아닙니다. 그래서 실제 파싱에 쓸 클래스는 `entity_cls` 라는 **평범한 클래스 속성**으로 따로 지정합니다.

> **🔎 문법의 출처** — `TypeVar`/`Generic` 은 PEP 484(파이썬 3.5)가 `typing` 모듈과 함께
> 들여왔습니다. 핵심은 그 PEP 가 스스로 밝힌 원칙입니다 — **"파이썬은 여전히 동적 타입
> 언어이며, 런타임에 타입을 강제하지 않는다."** 그래서 `JsonlStore[Transaction]` 에
> `Category` 를 넣어도 실행은 아무 불평 없이 됩니다. 검사는 mypy 같은 **별도 도구**의 일입니다.
> (3.12 의 PEP 695 는 `class JsonlStore[T]:` 라는 더 짧은 표기를 추가했지만, 이 프로젝트는
> `>=3.10` 이 하한선이라 쓰지 않습니다.) → [12 §2-B](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `JsonlStore[Transaction]` 이라는 표기는 무엇이 되는가** — 대괄호는
> 클래스에 정의된 `__class_getitem__` 을 부릅니다(`Generic` 이 제공합니다).
> 결과는 클래스가 아니라 **`typing._GenericAlias` 객체**로, `__origin__`(원래 클래스)과
> `__args__`(채워 넣은 타입 튜플)를 들고 있습니다. 이것을 상속하면 파이썬은 실제 MRO 에는
> `__origin__`(=`JsonlStore`)만 넣고, 원래 표기는 `TransactionRepository.__orig_bases__`
> 에 기록만 해 둡니다. 즉 **실행에 쓰이는 것은 `JsonlStore` 뿐이고 `Transaction` 은 기록으로만
> 남습니다.** "런타임에 지워진다"의 정확한 의미가 이것이고, `entity_cls` 를 따로 두어야 하는
> 이유이기도 합니다. → [12 §2-B](./12-syntax-and-stdlib.md)

두 가지를 다 두는 것이 중복처럼 보이지만 역할이 다릅니다 — 하나는 **개발 도구를 위한 선언**, 다른 하나는 **실행을 위한 값**입니다. [02 §10.3](./02-python-basics.md)에서 본 "힌트는 개발 시점 도구, 검증은 실행 시점 코드"와 정확히 같은 구조입니다.

**설계 의도.** 리팩터 전에는 세 저장소가 각자 `stream()`, `__init__`, 원자적(중간 상태가 남지 않는 통째 바꿔치기) 쓰기 코드를 복사해 갖고 있었습니다(약 60줄 중복). `JsonlStore` 로 올리면 "JSONL 파일을 다루는 법"이 한 번만 정의되고, 하위 클래스는 **엔티티 고유의 것만** 갖습니다 — `TransactionRepository` 는 ID 발급과 카테고리 재지정, `CategoryStore` 는 이름 중복 검사와 기본값 시딩, `BudgetStore` 는 "같은 달은 덮어쓰기".

---

## 7. from __future__ import annotations

**개념.** `__future__` 는 "미래 버전의 동작을 미리 켜는" 특수 모듈입니다. `from __future__ import annotations`(PEP 563)를 모듈 최상단에 쓰면, 그 모듈의 **모든 타입 어노테이션이 실행 시점에 평가되지 않고 문자열로만 저장**됩니다. 효과는 두 가지입니다.

1. **전방 참조(forward reference) 허용**: 아직 정의가 끝나지 않은 이름을 어노테이션에 쓸 수 있습니다.
2. **신 문법의 하위 호환**: `tuple[int, dict[str, str]]` 같은 내장 제네릭 표기(storage/csv_io.py:72)를 어노테이션 자리에 써도 런타임에 평가되지 않으므로 구버전 파이썬에서도 import 가 실패하지 않습니다.

**실제 코드.** 이 프로젝트의 모든 구현 모듈이 첫 import 로 이것을 둡니다.

budget_app/context.py:20

```python
from __future__ import annotations
```

전방 참조와의 관계는 `with_patch` 에서 가장 잘 보입니다.

budget_app/domain/entities.py:113

```python
    def with_patch(self, patch: TransactionPatch) -> Transaction:
```

이 시점(`Transaction` 클래스 본문 실행 중)에는 `Transaction` 도 `TransactionPatch` 도 아직 완성되지 않았습니다 — `TransactionPatch` 는 파일에서 이 줄보다 **아래에** 정의되어 있습니다(domain/entities.py:127-128). 전통적 해법이 `"TransactionPatch"` 처럼 **따옴표로 감싼 문자열 어노테이션**이었습니다.

**이 코드에는 따옴표 어노테이션이 한 곳도 없습니다.** `from __future__ import annotations` 가 타입 힌트를 쓰는 모듈 28개(43개 중) 맨 위에 있어서 어노테이션이 어차피 전부 문자열로 남기 때문에, 따옴표를 손으로 붙일 이유가 사라진 것입니다. 이 줄이 없는 나머지 15개는 `__init__.py`·`config.py`·`messages.py` 처럼 어노테이션이 아예 없는 재수출·상수 모듈이라 켤 이유가 없습니다. future import 를 켜 놓고도 따옴표를 병용하면 같은 일을 두 번 표기하는 셈이라 오히려 편차가 생깁니다 — 이 프로젝트는 **표기법을 하나로 통일하는 쪽**을 택했습니다.

**설계 의도.** 어노테이션이 런타임에 평가되지 않으면 (1) import 시 타입 표현식 평가 비용이 사라지고, (2) 전방 참조·순환 참조 문제에서 자유로워지며, (3) 어노테이션을 쓰는 모듈이 모두 같은 규칙을 따르므로 편차가 없습니다.

> **🔎 문법의 출처 — 이 한 줄에 세 개의 PEP 가 얽혀 있습니다**
> `from __future__ import annotations` 자체는 **PEP 563**(3.7 에서 선택 가능).
> 이것이 켜져 있어야 `dict[str, str]` 같은 **내장 제네릭 표기**(PEP 585, 정식으로는 3.9)와
> `str | None` **유니온 표기**(PEP 604, 3.10)를 어노테이션 자리에 마음 놓고 쓸 수 있습니다.
> 이 프로젝트는 `requires-python = ">=3.10"` 이라 뒤의 둘은 사실 future import 없이도
> 되지만, 세 표기를 한 규칙으로 묶어 두면 "어느 버전부터 되는지"를 매번 따질 필요가 없어집니다.
> → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — future import 는 평범한 import 가 아니라 **컴파일러 지시문**입니다.
> 그래서 모듈의 docstring 다음, 다른 모든 문장보다 **먼저** 와야 하고 아니면 `SyntaxError`
> 입니다. 켜지면 컴파일러는 어노테이션 표현식을 평가하는 바이트코드를 만들지 않고
> **소스 텍스트를 문자열 그대로** `__annotations__` 에 넣습니다. 부작용도 명확합니다 —
> 문자열을 실제 타입으로 되돌리려면 `typing.get_type_hints()` 로 다시 평가해야 하고,
> 그때는 그 이름들이 해당 모듈에서 보여야 합니다. 이 프로젝트는 어노테이션을 런타임에
> 읽는 코드가 없으므로(dataclass 는 **이름만** 보면 되지 값을 평가하지 않습니다) 이 부작용에
> 걸리지 않습니다. → [12 §1-C](./12-syntax-and-stdlib.md)

---

## 8. 표준 라이브러리 활용

이 프로젝트는 과제 제약상 **표준 라이브러리만** 사용합니다.

### 8.1 re — 정규식 컴파일과, "두 가지 패턴이 필요한 이유"

거래 ID 형식은 config 에 정규식 문자열로 정의되어 있습니다.

budget_app/domain/config.py:24-27

```python
# 거래 ID — 형식·검증·발굴 세 패턴이 값 객체(tx_id.TransactionId)와 짝을 이룬다
TX_ID_PATTERN = r"^TX-(\d+)$"
TX_ID_FORMAT = "TX-{:06d}"
TX_ID_SCAN_PATTERN = r'"id"\s*:\s*"(TX-\d+)"'
```

패턴이 **둘**인 것이 리팩터의 산물입니다.

| 패턴 | 앵커 | 쓰이는 곳 | 목적 |
|---|---|---|---|
| `^TX-(\d+)$` | 문자열 전체 | `TransactionId.__post_init__`(domain/tx_id.py:83-89) 과 `.number`(121-124) | "이 값이 올바른 id 인가" 검증 + 번호 추출 |
| `"id"\s*:\s*"(TX-\d+)"` | 부분 일치 | `TransactionId.scan`(domain/tx_id.py:109-117), 이것을 `TransactionRepository._scan_id`(storage/repositories.py:39-51)가 부름 | JSON 이 깨진 줄에서도 id 를 발굴 |

세 상수 모두 `r"..."`(raw 문자열)인 것은 백슬래시를 파이썬이 아니라 `re` 에게 넘기기 위해서이고, `TX_ID_SCAN_PATTERN` 만 작은따옴표 `r'...'` 인 것은 패턴 **안에** 큰따옴표(`"id"`)가 들어 있기 때문입니다. 문자열 리터럴 표기는 [02 §4](./02-python-basics.md)에서 다룹니다.

컴파일은 모듈 로드 시 한 번만 합니다.

budget_app/domain/tx_id.py:44-48

```python
#: 전체가 이 형식이어야 한다 — 검증용
_EXACT = re.compile(config.TX_ID_PATTERN)

#: 줄 어딘가에 있으면 된다 — JSON 이 깨진 줄에서 id 만 건져낼 때
_SCAN = re.compile(config.TX_ID_SCAN_PATTERN)
```

두 패턴이 **한 파일에** 있는 것이 값 객체 리팩터의 결과입니다. 이전에는 검증용이 `validators.py`, 스캔용이 `repository.py` 에 따로 있었고, 그래서 "거래 id 형식"을 바꾸려면 두 파일을 열어야 했습니다.

사용처는 검증과 스캔입니다.

budget_app/domain/tx_id.py:104-107
```python
    @classmethod
    def parse(cls, value: Any) -> TransactionId:
        """검증하며 만든다. 실패는 ``ValidationError``."""
        return cls(str(value or "").strip())
```

budget_app/storage/repositories.py:36-48

```python

    # ---------- ID ----------

    @staticmethod
    def _scan_id(raw: RawLine) -> TransactionId | None:
        """한 줄에서 거래 id 를 최대한 건져낸다.

        검증에 실패한 줄에도 id 는 들어 있을 수 있고, 그 번호는 **이미 쓰인 번호**다.
        놓치면 재발급으로 중복 id 가 생긴다. dict 까지 해석된 줄은 키에서, JSON 조차
        아닌 줄은 원문 정규식으로 찾는다(``TransactionId.scan``).
        """
        if raw.data is not None:
            candidate = raw.data.get("id")
```

**`match` 와 `search` 의 차이**가 여기서 실질적입니다. `match` 는 문자열 **시작부터** 매칭을 시도하고, `search` 는 **어디서든** 찾습니다. 검증은 "전체가 이 형식이어야" 하므로 `match` + `^...$`, 발굴은 "줄 어딘가에 있으면 됨"이므로 `search` 입니다. `m.group(1)` 이 괄호로 잡은 캡처 그룹을 꺼냅니다.

> **⚙️ 내부 동작 — `re.compile` 이 실제로 하는 일** — `re` 는 패턴 문자열을 파싱해
> 내부 옵코드 열로 **컴파일**한 `Pattern` 객체를 만듭니다. `re.match(패턴문자열, 값)` 처럼
> 매번 부르면 `re` 가 내부 캐시(`_cache`, 기본 512개)에서 찾아 주기는 하지만,
> 그래도 문자열을 키로 딕셔너리를 조회하는 비용은 남고, 캐시가 가득 차면 가장 오래 안 쓴
> 항목부터 하나씩 버립니다(LRU, 상한 `re._MAXCACHE = 512`).
> 모듈 로드 시 `_EXACT = re.compile(...)` 로 한 번 만들어 두면 그 조회조차 사라지고,
> 무엇보다 **패턴 오타가 import 시점에 즉시 `re.error` 로 드러납니다** —
> 처음 검증이 일어나는 실행 중이 아니라.
> 덧붙여, 이 코드가 `match` + `^...$` 를 쓰는 자리는 `fullmatch` 로도 쓸 수 있지만,
> 패턴 문자열 자체가 config 에 "전체 형식"으로 문서화돼 있어 `^`/`$` 를 남겨 둔 것입니다.
> → [12 §2-A](./12-syntax-and-stdlib.md)

### 8.2 logging — %-지연 포맷팅과 로거 계층

**로거 계층.** 로거 이름의 점(`.`)은 부모-자식 관계를 만듭니다.

budget_app/config.py:25

```python
LOGGER_NAME = "budget_app"
```

budget_app/storage/config.py:11

```python
LOGGER_NAME = f"{app_config.LOGGER_NAME}.storage"
```

이 프로젝트에 로거는 **두 이름**만 있고, 만들어지는 곳은 다섯 군데입니다.

| 로거 이름 | 상수 | `logging.getLogger(...)` 호출 위치 |
|---|---|---|
| `budget_app` | `config.LOGGER_NAME`(config.py:25) | `decorators.py:34`, `cli/error_handler.py:17` |
| `budget_app.storage` | `storage/config.py:11` | `storage/jsonl.py:33`, `storage/ids.py:23`, `storage/unit_of_work.py:62` |

`domain/` 패키지에는 로거가 **하나도 없습니다** — 도메인은 화면도 파일도 로그도 모르는 순수 계층이라 `logging` 을 import 조차 하지 않습니다 — [04. 아키텍처](./04-architecture.md)의 계층 규칙이 코드로 지켜지는 자리입니다.

이름의 점(`.`)이 만드는 부모-자식 관계 덕분에 `budget_app.storage` 로거의 레코드는 부모 `budget_app` 로 전파(propagate)됩니다. 그래서 `setup_logging` 이 루트 하나만 설정해도 저장소 로그가 함께 나오고, 필요하면 `logging.getLogger("budget_app.storage").setLevel(...)` 로 **저장소 로그만** 따로 조일 수 있습니다.

> **⚙️ 내부 동작 — 로거 계층은 문자열 하나로 만들어집니다** — `logging.getLogger(name)` 은
> 모듈 전역의 `Logger.manager.loggerDict` 라는 dict 에서 그 이름을 찾고, 없으면 만들어
> **캐시**합니다(그래서 같은 이름으로 몇 번을 불러도 항상 같은 객체입니다).
> 부모는 이름을 마지막 `.` 에서 잘라 거슬러 올라가며 찾습니다 —
> `budget_app.storage` 의 부모는 `budget_app`, 그 부모는 루트 로거입니다.
> 중간 이름이 아직 만들어지지 않았으면 `PlaceHolder` 를 넣어 두었다가 나중에 실제 로거로
> 바꿔 끼웁니다. 로그 한 건은 자기 로거에서 **레벨 검사만** 받고, 핸들러는
> `propagate=True`(기본)인 조상들의 것을 차례로 거쳐 갑니다. 이 프로젝트가 핸들러를
> `setup_logging` 한 곳에서만 붙일 수 있는 근거가 이것입니다.
> → [12 §2-B](./12-syntax-and-stdlib.md)

**%-지연 포맷팅.** [02 §4.2](./02-python-basics.md)에서 다룬 내용이 그대로 적용됩니다. `logger.debug(config.LOG_CALL, func.__name__)` 처럼 **템플릿과 인자를 분리해서** 넘기면 문자열 결합이 **그 로그가 실제로 출력될 때만** 수행됩니다.

> **⚙️ 내부 동작 — "출력될 때만"의 정확한 경로** — `logger.debug(msg, *args)` 는 가장 먼저
> `self.isEnabledFor(DEBUG)` 를 확인하고, **거짓이면 그 자리에서 반환**합니다.
> 참일 때만 `LogRecord` 를 만드는데, 이때도 `record.msg = msg`, `record.args = args` 로
> **따로 보관할 뿐 결합하지 않습니다.** 실제 `msg % args` 는 핸들러가 포매팅 단계에서
> `record.getMessage()` 를 부르는 순간 일어납니다.
> 그래서 기본 레벨(WARNING)로 도는 평소 실행에서 `@log_call` 의 DEBUG 로그는
> **문자열 하나 만들지 않습니다.** 반대로 `logger.debug(f"call {name}")` 이라고 쓰면
> f-string 이 **인자로 넘기기 전에** 이미 결합되므로 이 이득이 통째로 사라집니다 —
> `decorators.py:28-29` 의 주석이 "%-스타일인 이유는 logging 의 지연 포맷팅 때문"이라고
> 적어 둔 것이 이 뜻입니다. → [12 §2-B](./12-syntax-and-stdlib.md)

**핸들러는 한 곳에서만 붙입니다.**

budget_app/cli/output.py:79-100

```python
def setup_logging(debug: bool = False) -> bool:
    """루트 로거에 핸들러를 붙인다 — ``main()`` 에서 한 번만 호출한다.
    ...
    """
    enabled = bool(debug) or _env_debug()
    logging.basicConfig(
        level=logging.DEBUG if enabled else logging.WARNING,
        format=messages.LOG_FORMAT_DEBUG if enabled else messages.LOG_FORMAT,
        stream=sys.stderr,  # 로그는 결과가 아니므로 stdout 을 오염시키지 않는다.
        force=True,  # 이미 설정돼 있어도(재호출·테스트) 이 설정으로 덮어쓴다.
    )
    return enabled
```

`force=True` 는 3.8+ 옵션으로 "이미 핸들러가 붙어 있어도 제거하고 다시 설정하라"는 뜻입니다. 테스트에서 `main()` 을 여러 번 부를 때 핸들러가 중복 등록되어 로그가 두 번씩 찍히는 문제를 막습니다.

### 8.3 time.perf_counter — 구간 시간 측정

`measure_time`(decorators.py:50-66)은 `time.time()` 이 아니라 `time.perf_counter()` 를 씁니다. `perf_counter` 는 **경과 시간 측정 전용 고해상도 시계**로, 시스템 시각 변경(NTP 동기화 등)의 영향을 받지 않고 단조 증가가 보장됩니다. 두 번 읽어 뺀 차이(초 단위)를 `* 1000` 으로 밀리초로 바꿔 `%.2fms`(decorators.py:32 의 `LOG_TOOK`)로 기록합니다.

> **⚙️ 내부 동작 — 세 시계의 차이** — `time.time()` 은 **벽시계(wall clock)** 로,
> 1970년 기준 초를 돌려주며 NTP 보정이나 사용자의 시각 변경으로 **거꾸로 갈 수 있습니다.**
> 구간 측정에 쓰면 음수 시간이 나올 수 있다는 뜻입니다. `time.monotonic()` 은 되감기지
> 않는 것을 보장하고, `time.perf_counter()` 는 거기에 더해 **그 플랫폼에서 구할 수 있는
> 가장 높은 분해능**을 약속합니다(Windows 에서는 `QueryPerformanceCounter`).
> `monotonic`·`perf_counter` 두 개는 기준점(epoch)이 정의돼 있지 않아
> **두 값의 차이만 의미가 있습니다**(기준점이 정해진 것은 `time.time()` 뿐입니다) —
> 그래서 `measure_time` 은 `start` 를 따로 두고 `finally` 에서 빼는 형태일 수밖에 없습니다.
> 실제 분해능은 `time.get_clock_info("perf_counter")` 로 확인할 수 있습니다.
> → [12 §2-A](./12-syntax-and-stdlib.md)

### 8.4 datetime.strptime + strftime — "파싱이 곧 검증"이되, 정규형으로 되찍는다

`datetime.strptime(문자열, 형식)` 은 형식에 맞지 않으면 `ValueError` 를 던집니다. 이 프로젝트는 그 성질을 이용해 **파싱 성공 여부 자체를 검증으로** 씁니다.

그런데 **검증만 하고 원문을 돌려주면 안 됩니다.** `parse_date`(domain/validators.py:80-99)의 마지막 줄이 `return dt.strftime(config.DATE_FORMAT)` 인 것 — 즉 파싱한 datetime 으로 **다시 찍어서** 돌려주는 것 — 이 이 함수의 핵심입니다.

이유를 소스 docstring 이 직접 설명합니다. `strptime` 은 **검증기이지 정규화기가 아닙니다.** `%Y-%m-%d` 로 `"2024-1-5"` 를 오류 없이 받아 줍니다. 검증만 하고 원문을 그대로 저장하면 같은 날이 파일에 `"2024-1-5"` 와 `"2024-01-05"` 두 표기로 공존하게 되고, 이 프로그램은 날짜를 **문자열로 비교**하므로 그 순간 전제가 깨집니다.

```
"2024-1-5" <= "2024-01-31"   →   False
```

즉 1월 5일 거래가 1월 요약·검색·내보내기에서 **조용히 사라집니다.** `strftime` 으로 되찍으면 표기가 하나로 강제되고, 기존 파일에 남아 있던 비정규 표기도 **읽는 순간 `__post_init__` 을 다시 지나므로 자동으로 치유**됩니다(§1.4).

문자열 날짜 비교가 실제로 일어나는 곳은 `SearchFilter.matches` 안이 아니라 명세 객체입니다 — `matches` 는 `self.spec.is_satisfied_by(tx)` 로 위임만 하고(domain/queries.py:80-82), 비교는 `DateFrom.is_satisfied_by`(domain/specs.py:178-179)의 `tx.date >= self.value` 입니다. `DateFrom.__init__` 역시 `validators.parse_date` 로 **비교 상대편도 정규화**하므로(domain/specs.py:175-176), 비교의 양쪽이 같은 표기임이 보장됩니다.

> **⚙️ 내부 동작 — `strptime` 은 정규식으로 돕니다** — `datetime.strptime` 은 C 라이브러리
> 호출이 아니라 순수 파이썬 모듈 `_strptime` 의 일입니다. 형식 문자열의 `%Y`·`%m`·`%d` 를
> 대응하는 정규식 조각(`(?P<Y>\d\d\d\d)` 같은)으로 치환해 **패턴 하나를 만들어 컴파일**한 뒤
> (그 결과를 형식별로 캐시합니다) 값에 `match` 를 겁니다. 그래서 실패 메시지가
> `time data '...' does not match format '...'` 형태의 `ValueError` 입니다.
> `%m` 의 조각이 `(?P<m>1[0-2]|0[1-9]|[1-9])` 라서 **한 자리 월도 허용**하는 것이
> `"2024-1-5"` 가 통과하는 이유이고(`%d` 도 같은 모양입니다),
> 반대로 `strftime("%Y-%m-%d")` 는 항상 0 을 채워 찍습니다. **한쪽은 느슨하고 다른 쪽은
> 엄격한 이 비대칭이 곧 "왕복시키면 정규화가 된다"는 성질**입니다.
> → [12 §2-A](./12-syntax-and-stdlib.md)

형식 상수는 config 에 있습니다.

budget_app/domain/config.py:21-22

```python
DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"
```

출력 방향으로는 백업 폴더명 타임스탬프가 `strftime` 을 씁니다 — `(now or datetime.now()).strftime(config.BACKUP_TS_FORMAT)`(storage/backup.py:28).

### 8.5 calendar.monthrange — 그 달의 실제 말일

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

`calendar.monthrange(연, 월)` 은 `(그 달 1일의 요일, 그 달의 일수)` 튜플을 반환하며 `[1]` 로 일수만 취합니다. 윤년 2월(29일)까지 정확히 처리됩니다.

내부적으로 `monthrange` 는 표를 찾는 것이 아니라 `mdays[month] + (month == 2 and isleap(year))` 를 계산하며, `isleap(y)` 는 `y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)` 그 자체입니다. 즉 이 한 줄이 대신해 주는 것은 "2월이 며칠인가"를 손으로 분기하는 코드입니다 — 자세한 것은 [12 §2-A](./12-syntax-and-stdlib.md).

**리팩터 포인트 — 위치가 바뀌었습니다.** 이전에는 이 함수가 `cli.py` 에 `_month_bounds` 라는 이름으로 있었습니다. 달력 계산은 **도메인 규칙**이지 화면 처리가 아니므로 도메인 계층으로 내렸고(지금은 `domain/periods.py` 단독 모듈), 그 결과 요약(`summary`)과 내보내기(`export`)가 같은 정의를 공유하게 됐습니다.

### 8.6 csv.DictReader / DictWriter — 헤더 기반 CSV 입출력

가져오기는 `DictReader` 로 각 행을 `{헤더명: 값}` dict 로 받고, 시작 전에 필수 컬럼 존재를 검사합니다.

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

인덱스(`row[3]`) 대신 이름(`row["amount"]`)으로 접근하므로 **컬럼 순서가 달라도 동작**하고, 그래서 `id` 컬럼을 **선택**으로 추가할 수 있었습니다. `_check_header`(storage/csv_io.py:90-104)의 `reader.fieldnames or []` 는 빈 파일(fieldnames 가 `None`)에서도 안전하게 검사하기 위한 방어 표현입니다.

> **⚙️ 내부 동작 — `yield from` 이 넘기는 것은 값만이 아닙니다** — `read_rows` 의 마지막 줄
> `yield from enumerate(reader, ...)` 는 "그 반복자가 끝날 때까지 값을 그대로 통과시켜라"라는
> **위임(delegation)** 입니다(PEP 380, 3.3). `for x in it: yield x` 와 값 흐름은 같지만,
> 여기서 실제로 중요한 것은 **`with` 블록이 이 `yield from` 위에서 계속 살아 있다**는
> 사실입니다. 제너레이터는 값을 하나 내놓을 때마다 멈춰 있고 프레임이 보존되므로,
> `with open(...)` 의 `__exit__` 는 소비자가 마지막 행을 꺼내거나 제너레이터를 버릴 때까지
> 실행되지 않습니다. **즉 파일의 수명이 호출자에게 넘어갑니다** — 소스 주석이 바로 그 말을
> 하고 있고, 그래서 `read_rows` 의 결과를 저장해 두었다가 나중에 소비하면
> 그동안 파일 핸들이 열려 있게 됩니다. → [12 §1-C](./12-syntax-and-stdlib.md)

내보내기는 `DictWriter` 로 필드명 순서를 config 상수에 고정합니다.

budget_app/storage/csv_io.py:131-148

```python
def write_transactions(path: Path, txs: Iterable[Transaction], *, include_id: bool = True) -> int:
    """거래를 CSV 로 저장하고 작성 건수를 반환한다.

    인코딩은 BOM 없는 UTF-8 로 고정한다. BOM 을 넣으면 다시 ``import`` 할 때 헤더
    첫 컬럼명이 ``﻿id`` 로 깨져 왕복이 실패한다(왕복 안전성 우선).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
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

`include_id` 에 따라 필드 목록 자체를 바꿉니다 — `DictWriter` 는 `fieldnames` 에 없는 키를 dict 에 담아 넘기면 `ValueError` 를 내므로, `_to_row` 도 같은 플래그를 받아 `id` 키를 넣을지 결정합니다(storage/csv_io.py:151-163).

> **⚙️ 내부 동작 — `newline=""` 이 왜 붙어 있나** — `csv` 모듈이 **직접 요구하는 규약**입니다.
> `csv.writer` 는 줄 끝을 스스로 `\r\n` 으로 씁니다(RFC 4180). 그런데 텍스트 파일을
> 기본 모드로 열면 파이썬의 줄바꿈 변환기가 Windows 에서 `\n` 을 다시 `\r\n` 으로 바꿔
> **`\r\r\n` 이라는 빈 줄 섞인 파일**이 나옵니다. `newline=""` 은 그 변환을 끄는 것이고,
> 읽을 때도 같은 이유로 필요합니다 — 따옴표로 감싼 셀 안에 줄바꿈이 들어 있을 때
> `csv` 가 스스로 판단해야 하기 때문입니다. `open()` 의 다른 옵션이 아니라
> **`csv` 를 쓸 때 반드시 따라오는 짝**으로 외워 두는 편이 안전합니다.
> → [12 §3](./12-syntax-and-stdlib.md)

### 8.7 os.replace / os.fsync — 원자적 파일 교체

budget_app/storage/jsonl.py:48-72 (`stage_lines`) 와 80-87 (`atomic_write_lines`) — 전문은 [02 §8.1](./02-python-basics.md) 에 인용돼 있습니다. 이름에 밑줄이 없는 것(`_atomic_write_lines` 가 아님)은 의도적이며, 소스 docstring 이 그 이유를 따로 설명합니다.

`os.replace(src, dst)` 는 대상이 이미 있어도 덮어쓰는 이름 교체이며, 같은 파일시스템 안에서는 **원자적(atomic)** — 즉 외부에서 볼 때 "교체 전" 아니면 "교체 후"만 존재하고 중간 상태가 없습니다.

`os.fsync(f.fileno())` 가 함께 필요한 이유는 둘이 보장하는 것이 다르기 때문입니다.

| 호출 | 보장하는 것 | 보장하지 않는 것 |
|---|---|---|
| `f.flush()` | 파이썬 버퍼 → OS 버퍼 | OS 버퍼가 디스크에 도달했는지 |
| `os.fsync(fd)` | OS 버퍼 → 물리 디스크 | 이름이 바뀌었는지 |
| `os.replace()` | 이름 교체가 원자적 | 내용이 디스크에 도달했는지 |

셋을 이 순서로 조합해야 "새 이름이 가리키는 파일에 완전한 내용이 들어 있다"가 성립합니다. 자세한 crash 시나리오 분석은 [10. 고급 설계 주제](./10-advanced-design.md)에 있습니다.

### 8.8 os.dup2 / os.devnull — BrokenPipe 공식 레시피

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

`os.devnull` 은 OS 별 "블랙홀" 장치 경로(Windows `nul`, Unix `/dev/null`)이고, `os.dup2(a, b)` 는 파일 디스크립터 b 가 a 와 같은 곳을 가리키게 복제합니다. 즉 **stdout 을 블랙홀로 갈아끼워** 인터프리터 종료 시 남은 버퍼를 비우다 BrokenPipeError 가 재발하는 것을 막습니다.

`handle_errors` 가 BrokenPipeError 만은 `raise` 로 위로 넘기고(§5.3), `main`(cli/app.py:84-94)이 이 함수를 호출한 뒤 `EXIT_OK` 를 반환하는 협업 구조입니다. 전말은 [09. CLI 계층](./09-cli.md)에서 상세히 다룹니다.

---

## 9. 콜러블을 값으로 전달하는 패턴

함수를 값으로 다루는 능력(일급 객체)은 4장의 데코레이터 외에도 이 코드에서 세 군데 더 핵심적으로 쓰입니다.

### 9.1 validator 인자 — `ask_until` 의 전략 주입

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

`ask_until` 은 "무엇이 유효한가"를 전혀 모릅니다. **재시도 루프라는 뼈대만 제공**하고, 판정은 인자로 받은 `validator` 콜러블에 위임합니다. 계약은 단순합니다 — `validator(raw)` 는 정규화된 값을 반환하거나 `ValidationError` 를 던진다.

이 계약 덕분에 모듈 함수(`validators.parse_date`)든 클로저 팩토리 산출물(`registered_category_validator(cats)`)이든 **같은 자리에 꽂아** 쓸 수 있습니다. 일반론으로 말하면 이는 전략(strategy) 패턴을 클래스 없이 함수 값으로 구현한 것입니다.

`Callable[[str], T]` 라는 타입 표기가 그 계약을 코드로 적어 둡니다 — 반환 타입이 `T` 이고 함수 전체의 반환도 `T` 이므로, "넘긴 검증기가 돌려주는 타입이 그대로 나온다"가 표현됩니다.

### 9.2 transform 콜백 — `rewrite` 의 뼈대/알맹이 분리

§3.4 와 §4.6 에서 본 `rewrite(transform)` 이 같은 구조입니다. `rewrite` 는 "모든 줄을 순회하며 손상 줄은 보존하고 임시 파일에 원자적으로 쓴다"는 **뼈대**만 알고, "각 엔티티를 어떻게 바꿀 것인가"는 콜백이 정합니다.

| 호출자 | transform 이 하는 일 |
|---|---|
| `delete` | 대상이면 `None`(삭제), 아니면 그대로 |
| `replace` | 대상이면 새 객체, 아니면 그대로 |
| `reassign_category` | 카테고리가 일치하면 `with_patch`, 아니면 그대로 |
| `BudgetStore.set` | 같은 달이면 `None`, 아니면 그대로 + `extra` 로 새 값 |

`Callable[[T], T | None]` 이라는 타입 하나가 "바꾼 것 / 그대로 / 삭제" 세 가지 의도를 모두 표현합니다.

### 9.3 문자열 키 디스패치 — `HANDLERS` 딕셔너리

리팩터 전에는 argparse 의 `set_defaults(func=cmd_add)` 로 **함수 객체**를 파서에 직접 심었습니다. 지금은 문자열을 심고 표에서 찾습니다.

budget_app/cli/parser.py:108-111

```python
def _add_add(sub) -> None:
    p = sub.add_parser("add", help="거래 추가 (대화형)")
    _add_shared_options(p)
    p.set_defaults(handler="add")
```

budget_app/cli/app.py:26-27
```python
Handler = Callable[[AppContext, argparse.Namespace], int]

```

budget_app/cli/app.py:81

```python
    return HANDLERS[args.handler](ctx, args)
```

**왜 함수 객체 대신 문자열인가.** 함수를 직접 심으려면 파서 정의와 핸들러 구현이 **같은 파일에 있거나 한쪽이 다른 쪽을 import** 해야 합니다. 전자는 512줄짜리 단일 CLI 모듈을 만들었습니다.

후자를 "순환 import" 라고 부르는 것은 정확하지 않습니다 — `parser → handlers` 한 방향이면 순환이 아닙니다. 진짜 문제는 **방향이 생긴다**는 것입니다. 문법 한 줄을 고치려고 여는 파일이 핸들러 구현 전체를 끌고 들어오고, 핸들러가 나중에 파서의 상수 하나라도 필요해지는 순간 그때 순환이 됩니다. 문자열 키를 경유하면 두 모듈이 서로를 모른 채 연결되므로 그 가능성 자체가 사라집니다.

`Handler = Callable[[AppContext, argparse.Namespace], int]` 라는 **타입 별칭**이 계약을 한 줄로 적어 둡니다 — "컨텍스트와 파싱 결과를 받아 종료 코드를 돌려주는 함수". 새 핸들러를 추가할 때 이 모양만 맞추면 됩니다.

부수 효과로 죽은 코드가 사라졌습니다. 이전에는 `category` 의 세 하위 명령이 한 핸들러로 들어와 `if/elif` 로 갈라졌고 맨 끝에 "알 수 없는 하위 명령" 분기가 있었는데, `add_subparsers(required=True)` 가 값을 이미 제한하므로 **도달할 수 없는 코드**였습니다.

---

## 10. 적용된 디자인 패턴 2종

리팩터 마지막 단계에서 **문제가 실재하는 곳에만** 패턴을 도입했습니다. "패턴을 써 봤다"가 아니라 "이 문제를 이렇게 풀었다"로 설명할 수 있어야 합니다.

### 10.1 Specification — 검색 조건이 AND 로 고정돼 있던 문제

**적용 전.** `SearchFilter.matches` 가 조건 6개를 하드코딩된 AND 로 검사했습니다.

```python
# 리팩터 전 — 지금은 없는 코드
    def matches(self, tx: Transaction) -> bool:
        if self.date_from and tx.date < self.date_from: return False
        if self.category  and tx.category != self.category: return False
        ...
        return True
```

이 구조에서는 **AND 말고는 표현할 방법이 없습니다.** `--category food --category cafe`(둘 중 하나)나 "이 태그는 제외" 같은 요구가 오면 dataclass 필드와 `matches` 를 동시에 고쳐야 하고, 조합이 늘수록 if 가 곱해집니다.

**적용 후.** 조건 하나를 객체 하나로 만들고 연산자로 조합합니다.

> **💡 쉽게 말하면** — 체(거름망)를 겹쳐 놓고 거래를 부어 통과한 것만 받는 구조입니다. 체 한 장이 조건 하나이고, 조건이 늘면 if 문을 고치는 대신 체를 한 장 더 얹습니다. `&` 는 두 체를 위아래로 겹치는 것, `|` 는 둘 중 아무 쪽이나 통과하면 되게 나란히 두는 것, `~` 는 체를 뒤집어 걸린 쪽만 받는 것입니다.
> 다만 이 비유는 지금 실제로 겹쳐 쓰는 체가 **AND(전부 통과) 하나뿐**이라는 데서 깨집니다 — 아래의 `_build_spec` 은 조건이 하나라도 있으면 `And` 만 조립하고(하나도 없으면 `Always`), `|` 와 `~` 는 "카테고리 A 또는 B" 같은 요구가 왔을 때 if 사다리를 곱하지 않으려고 미리 마련해 둔 것입니다.

budget_app/domain/specs.py:76-91

```python
class Spec(ABC):
    """거래 하나가 조건을 만족하는지 판단하는 명세."""

    @abstractmethod
    def is_satisfied_by(self, tx: Transaction) -> bool: ...

    # ---------- 조합 ----------

    def __and__(self, other: Spec) -> Spec:
        return And(self, other)

    def __or__(self, other: Spec) -> Spec:
        return Or(self, other)

    def __invert__(self) -> Spec:
        return Not(self)
```

`__and__`/`__or__`/`__invert__` 를 오버로딩하면 명세 조합이 불리언 식과 같은 모양이 됩니다. 파이썬은 `and`/`or` **키워드**를 오버로딩할 수 없어서 비트 연산자를 빌려 쓰는 것이 이 패턴의 표준 관용구입니다.

> **⚙️ 내부 동작 — `and` 는 왜 오버로딩할 수 없나** — 훅이 없어서가 아니라 **연산자가 아니기
> 때문**입니다. `a & b` 는 바이트코드 `BINARY_OP` 하나로 컴파일되고, 인터프리터가
> `type(a).__and__(a, b)` 를 부릅니다(`NotImplemented` 면 `type(b).__rand__` 로 넘어갑니다).
> 반면 `a and b` 는 **점프 명령**으로 컴파일됩니다 — `a` 의 진릿값을 보고 거짓이면 `b` 를
> 아예 평가하지 않고 건너뜁니다(단축 평가). 함수 호출이 일어나지 않으니 가로챌 자리가
> 없습니다. 3.13 에서 `dis.dis(lambda a,b: a and b)` 를 찍으면 `TO_BOOL` 과
> `POP_JUMP_IF_FALSE` 만 보이고 어떤 특수 메서드 호출도 없습니다.
> `~`(단항)는 `__invert__` 로 갑니다. **연산자 우선순위까지 그대로 빌려 온다**는 점도
> 중요합니다 — `&` 가 `|` 보다 강하므로 `A | B & C` 는 `A | (B & C)` 이고,
> 예시 코드가 `(InCategory("food") | InCategory("cafe"))` 를 괄호로 감싼 이유가 이것입니다.
> → [12 §1-B](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `ABC` + `@abstractmethod` 가 인스턴스화를 막는 기제**
> `abc.ABC` 는 `metaclass=ABCMeta` 를 달아 둔 빈 클래스일 뿐입니다. `@abstractmethod` 는
> 함수에 `__isabstractmethod__ = True` 라는 **표시만** 붙이고, 실제 일은 `ABCMeta` 가 합니다 —
> 클래스를 만들 때 본문과 조상들을 훑어 아직 구현되지 않은 추상 메서드 이름을 모아
> `cls.__abstractmethods__`(frozenset)에 넣습니다. 그리고 `object.__new__` 가 객체를 만들기
> 직전 그 집합이 비어 있는지 확인해, 비어 있지 않으면
> `TypeError: Can't instantiate abstract class Spec without an implementation for abstract
> method 'is_satisfied_by'` 를 냅니다. 그래서 **`Spec()` 은 실패하지만
> `is_satisfied_by` 를 구현한 `DateFrom()` 은 성공**합니다.
> 검사 시점이 "클래스 정의 때"가 아니라 **"인스턴스를 만들 때"** 라는 점이 핵심입니다 —
> `And`/`Or`/`Not` 처럼 중간 단계 클래스를 만들어도 정의 자체는 막히지 않습니다.
> → [12 §1-B](./12-syntax-and-stdlib.md)

```python
spec = DateFrom("2024-01-01") & DateTo("2024-01-31") & (InCategory("food") | InCategory("cafe")) & ~HasTag("정기")
```

**`SearchFilter` 는 판정을 하지 않고 조립만 합니다.**

budget_app/domain/queries.py:57-72

```python
    def _build_spec(self) -> specs.Spec:
        """지정된 조건만 골라 AND 로 잇는다. 하나도 없으면 ``Always``."""
        parts: list[specs.Spec] = []
        if self.date_from:
            parts.append(specs.DateFrom(self.date_from))
        if self.date_to:
            parts.append(specs.DateTo(self.date_to))
        if self.category:
            parts.append(specs.InCategory(self.category))
        if self.type:
            parts.append(specs.OfType(self.type))
        if self.query:
            parts.append(specs.MemoContains(self.query))
        if self.tag:
            parts.append(specs.HasTag(self.tag))
        return specs.And(*parts) if parts else specs.Always()
```

**얻은 것**: 조건 추가가 **클래스 하나 추가**가 되고 기존 코드는 그대로입니다. `list`/`search`/`summary`/`export` 넷이 `SearchFilter` 를 공유하므로 표현력이 한 번 늘면 네 명령이 동시에 강해집니다.

**Null Object 도 함께 들어왔습니다.** 조건이 하나도 없는 `list` 는 `Always()` 를 받아 `None` 검사 없이 같은 코드로 처리됩니다.

### 10.2 Unit of Work — 두 파일 쓰기 사이의 빈틈

**적용 전.** 가져오기 커밋이 파일 둘을 따로 바꿨습니다.

```python
# 리팩터 전 — 지금은 없는 코드
        self.cats.add_many(batch.new_categories)      # 쓰기 1 — categories.jsonl
        imported = self.txs.append_many(...)          # 쓰기 2 — transactions.jsonl
```

두 줄 사이에 죽으면 **카테고리만 늘어난 고아 상태**가 남습니다. `--atomic` 이 "전부 또는 전무"를 약속하는데 그 약속이 파일 하나 안에서만 지켜지고 있었습니다.

**적용 후.** 쓰기를 준비와 커밋으로 나눕니다.

budget_app/storage/unit_of_work.py:73-181

```python
class UnitOfWork:
    """여러 저장소의 재작성을 모아 두었다가 한꺼번에 커밋한다.
    ...
    """

    def __init__(self) -> None:
        self._staged: list[tuple[Path, Path]] = []

    # ---------- 준비 ----------

    def stage(
        self,
        store,
        transform: Callable[[Any], Any | None] = _keep,
        *,
        extra: Iterable[Any] = (),
    ) -> bool:
        """한 저장소의 최종 내용을 ``.tmp`` 로 준비한다 — 아직 반영하지 않는다.
        ...
        """
        plan: RewritePlan = store.plan_rewrite(transform, extra=extra)
        if not plan.changed:
            return False  # 바꿀 것이 없으면 임시 파일도 만들지 않는다
        tmp = stage_lines(store.path, plan.lines)
        self._staged.append((tmp, store.path))
        return True

    # ---------- 마무리 ----------

    def commit(self) -> None:
        """준비된 것을 전부 반영한다 — rename 만 연달아 실행.
        ...
        """
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

    def rollback(self) -> None:
        """준비한 ``.tmp`` 를 지운다 — 원본은 손대지 않았으므로 이것으로 끝이다."""
        for tmp, _ in self._staged:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:  # 지우지 못해도 원본은 무사하다. 다음 실행이 덮어쓴다.
                logger.debug(messages.LOG_TMP_CLEANUP_FAILED, tmp)
        self._staged.clear()

    # ---------- 컨텍스트 매니저 ----------

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

`with` 를 쓰는 이유는 예외로 빠져나가는 경로에서도 `.tmp` 를 반드시 치우기 위해서입니다.

> **🔎 문법의 출처 / ⚙️ 내부 동작 — `with` 는 `__enter__`/`__exit__` 두 메서드로 풀립니다**
> `with` 문은 PEP 343 으로 파이썬 2.5 에 들어왔고, `with UnitOfWork() as uow:` 는 대략
> "객체를 만들고 → `__enter__()` 의 **반환값**을 `uow` 에 담고 → 본문을 `try` 로 감싸
> → 어떻게 끝나든 `__exit__(예외타입, 예외값, 트레이스백)` 를 부른다"로 풀립니다.
> 여기서 두 가지가 이 코드의 설계를 설명합니다.
> (1) `as uow` 가 받는 것은 `UnitOfWork` 인스턴스가 아니라 **`__enter__` 가 돌려준 값**입니다
> — 그래서 `__enter__` 가 `return self` 라고 명시해야 합니다(unit_of_work.py:169-170).
> (2) `__exit__` 는 예외 정보 3개를 받으므로 **정상 종료와 예외 종료를 구분**할 수 있습니다.
> `exc_type is None` 이면 커밋, 아니면 롤백이라는 분기가 여기서 나옵니다.
> `__exit__` 가 `True` 를 돌려주면 예외가 삼켜지는데, 이 코드는 `None`(= 거짓)을 돌려주므로
> **롤백한 뒤 예외는 그대로 위로 올라갑니다** — 조용히 실패하지 않겠다는 뜻입니다.
> → [12 §1-C](./12-syntax-and-stdlib.md)

**호출부.**

budget_app/services/importexport.py:188-206

```python
    def _commit_atomic(self, batch: _Batch) -> int:
        """원자 모드 — 두 파일을 **한 단위로** 커밋한다.
        ...
        """
        fresh_categories = [Category(name=n) for n in batch.new_categories]
        # 파일을 저장소 밖(UoW)에서 쓰므로 id 워터마크는 여기서 명시적으로 알린다.
        self.txs.remember_ids(batch.transactions)
        with UnitOfWork() as uow:
            if fresh_categories:
                uow.stage(self.cats, extra=fresh_categories)
            uow.stage(self.txs, extra=batch.transactions)
        return len(batch.transactions)
```

**얻은 것**: 취약 구간이 "파일 쓰기 2회 사이"에서 "rename 2회 사이"로 줄어듭니다. 준비 도중 죽으면 원본 둘 다 무사하고 `.tmp` 찌꺼기만 남습니다.

**정직하게 — 완전한 원자성은 아닙니다.** rename 두 번 사이에 전원이 끊기면 여전히 한쪽만 반영될 수 있습니다. 진짜 다중 파일 원자성은 저널이나 SQLite 가 필요합니다. 이 패턴이 하는 일은 **창을 밀리초 단위로 줄이는 것**이지 없애는 것이 아닙니다.

**부분 성공 모드에는 적용하지 않았습니다.** `--atomic` 없는 가져오기는 append 라 O(1)인데, UoW 를 쓰려면 전체 재작성이 필요해 10만 건 파일에 10건을 넣는 데 10만 줄을 다시 써야 합니다. **원자성을 약속한 모드에만** 비용을 지불하는 것이 맞습니다.

### 10.3 이미 들어 있던 패턴

새로 도입한 둘 외에, 리팩터 과정에서 자연히 자리 잡은 것들입니다. 이름을 알아 두면 구술에서 그대로 쓸 수 있습니다.

| 패턴 | 어디에 | 무엇을 해결하나 |
|---|---|---|
| **Repository** | `storage/repositories.py` | 도메인이 파일 형식을 모르게 |
| **Template Method + Strategy** | `JsonlStore.rewrite(transform)` | 골격은 고정, 알맹이는 주입 |
| **Adapter** | `storage/csv_io.py` | 외부 포맷 ↔ 도메인 번역 |
| **Value Object** | `domain/tx_id.TransactionId` | 흩어진 개념을 타입 하나로 |
| **Decorator** | `@log_call` / `@handle_errors` | 횡단 관심사 분리 |
| **Factory Method** | `from_dict`, `SearchFilter.for_month` | 대체 생성 경로 |
| **Composition Root** | `context.AppContext` | 조립을 한 곳에 |
| **Registry** | `cli.app.HANDLERS` | 파서와 핸들러 분리 |
| **Iterator** | `iter_raw()` / `stream()` | 메모리 O(1) |

### 10.4 **쓰지 않기로** 한 패턴

판단 근거를 말할 수 있는 것이 적용만큼 중요합니다.

| 패턴 | 왜 쓰지 않았나 |
|---|---|
| **Chain of Responsibility** (예외) | `handle_errors` 의 except 체인이 사실상 이 패턴인데, **파이썬 `except` 가 더 읽기 쉽고 상속 관계로 우선순위가 자동 결정**됩니다. 핸들러 객체로 바꾸면 순서를 손으로 관리해야 합니다 |
| **Abstract Factory** (저장 백엔드) | 구현이 **하나뿐**입니다. 두 번째가 생기기 전의 추상 팩토리는 비용만 냅니다 |
| **Visitor** | 도메인 타입이 3개이고 **안정적**입니다. Visitor 는 "타입 고정, 연산 추가"일 때 값을 하는데 여기는 반대입니다 |
| **Builder** (`SearchFilter`) | 필드 전부가 선택적인 dataclass 는 이미 빌더의 이점을 가집니다 |
| **Singleton** (`AppContext`) | 테스트에서 `--data-dir` 를 바꿔 여러 컨텍스트를 동시에 쓰는 이점을 잃습니다 |
| **Command + Memento** (undo) | 되돌리기 기능이 **아직 없습니다.** 필요해지는 순간 정당화됩니다 — 지금 넣으면 쓰이지 않는 추상화입니다 |

---

## 정리 — 기법 간의 연결 관계

이 문서의 기법들은 따로 노는 것이 아니라 하나의 사슬로 맞물려 있습니다.

```
[validators 모듈 함수]  ── 규칙 하나 = 함수 하나 = 한 곳
        │                        │
        │ __post_init__ 이 호출    └─▶ [콜러블 전달 ask_until] ── 재시도 루프 뼈대
        ▼                                     │
[dataclass 생성자 불변식] ── 어떤 경로든 생성 = 검증
        ▲                                     │
        │ cls(...) 호출                        │
[classmethod from_dict] ◀── [제너레이터 iter_raw] ── 모든 줄 보존(RawLine)
        │                             │
        │                             ├─▶ [stream()] ── 유효한 것만, 경고 로그
        │                             └─▶ [rewrite(transform)] ── 손상 줄 원문 보존
        ▼                                     │ 클로저 + nonlocal 로 집계
[ValidationError / AppError] ──▶ [handle_errors] ── 예외 → 메시지/종료코드
   (errors.py — 계층 공통 어휘)              ▲
                                             │ HANDLERS[문자열 키]
                                        [argparse 디스패치 main]
```

과제 방어 때는 이 그림 순서대로 — "규칙은 한 곳에 정의되고(§2.2), 모델이 생성자에서 그것을 강제하며(§1.4), 데이터는 제너레이터로 흐르되 읽기 경로가 목적에 따라 둘로 나뉘고(§3.2), 공통 관심사는 데코레이터로 분리되며 그 데코레이터끼리도 의존 방향에 따라 갈라지고(§4.4), 실패는 계층 공통 예외로 수렴한다(§5.1)" — 설명하면 코드 전체의 설계 의도를 일관된 이야기로 전달할 수 있습니다.

계층(도메인/저장소/서비스/CLI) 관점의 큰 그림은 [04. 아키텍처](./04-architecture.md)에서 이어집니다.
