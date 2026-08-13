# 07. 저장소 계층 — `storage/` 패키지 (jsonl · ids · repositories · csv_io · backup · unit_of_work)

파일을 읽고 쓰는 모든 코드가 모여 있는 계층입니다. 스트리밍 읽기, 원자적 교체, **손상된 줄 보존**, **ID 발급 충돌 방지**, CSV 경계 어댑터를 다룹니다.

> **난이도**: 🟡 중급 ~ 🔴 고급
>
> **먼저 읽으면 좋은 문서**: [03. 파이썬 중·고급 기법](./03-python-advanced.md) §3(제너레이터)·§6(제네릭), [05. 설정·검증·모델](./05-config-and-models.md)
>
> **문법·표준 라이브러리 상세**: [12. 문법과 표준 라이브러리](./12-syntax-and-stdlib.md) — 이 문서에 나오는 🔎/⚙️ 노트의 원본 설명이 있습니다. 특히 §3(운영체제 계층: 버퍼링·fsync·`os.replace`·인코딩)이 이 문서와 직접 짝을 이룹니다.

---

## 1. 이 계층의 계약

budget_app/storage/__init__.py:1-17
```python
"""저장소 계층 — 파일을 읽고 쓰는 코드가 전부 여기 있다.

- ``jsonl``        : JSONL 포맷 공통 처리 (JsonlStore / RawLine / 원자적 쓰기)
- ``ids``          : 거래 ID 발급기 (파일 상태에 의존하는 부분)
- ``repositories`` : 엔티티별 저장소 3종
- ``csv_io``       : CSV 경계 어댑터 (외부 교환 포맷 ↔ 도메인)
- ``backup``       : 데이터 폴더 백업

리팩터 전에는 JSONL 은 저장소, CSV 는 서비스에서 열어 규칙이 일관되지 않았다.
지금은 ``open()`` 이 이 패키지 밖에 없다(서비스 계층에는 0개).

이 계층은 **도메인 판단을 하지 않는다.** 완성된 객체를 받아 쓰고 저장된 객체를
돌려줄 뿐이며, "무엇으로 바꿀지"는 서비스와 도메인이 정한다.

**재수출하지 않는다** — ``from ..storage.repositories import CategoryStore`` 처럼
소유 모듈을 명시해 "어느 파일이 무엇을 정의하는가"가 import 문에서 보이게 한다.
"""
```

리팩터로 예전의 `storage/repository.py` 한 파일이 `jsonl` · `ids` · `repositories` · `backup` 넷으로 쪼개졌습니다. 지금의 구성 요소와 위치는 이렇습니다.

| 요소 | 파일 | 줄 | 역할 |
|---|---|---|---|
| `stage_lines` | `storage/jsonl.py` | 48-72 | 임시 파일 작성 + flush + fsync (교체는 안 함) |
| `commit_staged` | `storage/jsonl.py` | 75-77 | `os.replace` 한 줄 |
| `atomic_write_lines` | `storage/jsonl.py` | 80-87 | 위 둘을 연달아 — 파일 하나를 원자적으로 교체 |
| `RawLine` | `storage/jsonl.py` | 95-111 | 한 줄의 세 가지 상태를 담는 값 |
| `RewritePlan` | `storage/jsonl.py` | 114-123 | 재작성 계획(쓸 줄 + 바뀌었는가) |
| `JsonlStore` | `storage/jsonl.py` | 131-329 | JSONL 파일을 다루는 공통 동작 (제네릭) |
| `IdWatermark` | `storage/ids.py` | 26-78 | 발급된 적 있는 최대 번호를 파일에 남김 |
| `IdAllocator` | `storage/ids.py` | 81-116 | 거래 ID 발급기 |
| `TransactionRepository` | `storage/repositories.py` | 27-214 | 거래 저장소 (ID 발급·카테고리 재지정) |
| `CategoryStore` | `storage/repositories.py` | 217-280 | 카테고리 저장소 (이름 중복·기본값 시딩) |
| `BudgetStore` | `storage/repositories.py` | 283-308 | 예산 저장소 (같은 달은 덮어쓰기) |
| `backup_data_dir` | `storage/backup.py` | 17-33 | 데이터 폴더 백업 |
| `UnitOfWork` | `storage/unit_of_work.py` | 73-181 | 여러 파일을 한 단위로 커밋 |

여기에 CSV 경계 어댑터 `storage/csv_io.py` 가 같은 폴더에 있습니다(§8). **내장 `open()` 을 부르는 곳은 `storage/jsonl.py`(4곳: 61·174·234·258)와 `storage/csv_io.py`(2곳: 82·142) 뿐입니다.**

> **⚙️ 내부 동작** — "`open()` 이 두 파일에만 있다"는 말에는 작은 예외가 있습니다. `storage/ids.py:60` 의 `Path.read_text` 와 `storage/backup.py:32` 의 `Path.read_bytes`/`Path.write_bytes` 는 내부에서 `io.open` 을 부르는 **얇은 래퍼**입니다(CPython `Lib/pathlib` 구현이 `with self.open(...) as f: return f.read()` 형태). 계층 규칙("파일을 여는 코드는 저장소 계층 안에만")은 그대로 지켜지는 셈입니다. 또 `cli/app.py:55` 의 `os.open(os.devnull, ...)` 은 내장 `open()` 이 아니라 **파일 디스크립터를 직접 여는 저수준 시스템 호출**이라 성격이 다릅니다. → [12 §3](./12-syntax-and-stdlib.md)

---

## 2. 이 문서의 핵심 — 읽기 경로가 왜 둘인가

리팩터 이전과 이후를 먼저 대조합니다. 이 하나가 이 문서 내용의 절반입니다.

budget_app/storage/jsonl.py:9-18 (모듈 docstring 이어서)

```python
"""...
## 읽기 경로가 둘인 이유

이전에는 읽기 진입점이 ``stream()`` 하나였고 그것이 파싱 실패 줄을 **건너뛰었다**.
그런데 ``delete``/``update``/``reassign`` 이 파일을 다시 쓸 때도 같은 ``stream()`` 을
재료로 썼다. 결과적으로 무관한 거래 하나를 지우면 **손상된 줄이 디스크에서 영구
삭제**됐다. 또 같은 원인으로 ID 스캔이 검증 실패 줄의 id 를 놓쳐 번호가 재발급됐다.

- ``iter_raw()`` — 모든 줄을 원문과 함께 준다. 재작성 경로와 ID 스캔이 쓴다.
- ``stream()``   — 검증을 통과한 도메인 객체만 준다. 조회 경로가 쓴다.
"""
```

두 가지가 이 문단에 함께 적혀 있는 것이 중요합니다. **손상 줄 유실**과 **ID 재발급**은
증상이 전혀 다르지만 원인이 하나입니다 — 읽기 경로 하나가 조회와 재작성·스캔을
겸하고 있었던 것. 경고 로그는 "읽을 때 건너뛴다"는 뜻이었지 "파일에서 지웠다"는
뜻이 아니라서 사용자는 유실을 알 수조차 없었습니다.

### 2.1 버그 재현 — 손상 줄 영구 삭제

리팩터 전 코드로 실제로 재현했던 시나리오입니다.

```
$ cat data/transactions.jsonl
{"id":"TX-000001", ... "amount":1000 ...}
{ BROKEN LINE }                              ← JSON 이 아닌 줄
{"id":"TX-000002", ... "amount":2000 ...}

$ python -m budget_app delete --id TX-000001     ← TX-000001 만 지우려 했는데
[WARNING] transactions.jsonl:2 손상된 줄을 건너뜁니다: ...
[삭제 완료] id=TX-000001

$ cat data/transactions.jsonl
{"id": "TX-000002", ... }                    ← 손상 줄까지 사라짐!
```

**경고 로그가 오해를 부릅니다.** "건너뜁니다"는 읽기에 대한 말이었는데, 사용자는 그것이 파일에서 지워졌다는 뜻인 줄 모릅니다.

### 2.2 버그 재현 — ID 발급 충돌

```
$ cat data/transactions.jsonl
{"id":"TX-000009", "amount":0, ...}          ← amount=0 → 검증 실패
{"id":"TX-000010", "date":"2024-13-99", ...} ← 날짜 불량 → 검증 실패

$ python -m budget_app import --from new.csv
$ tail -1 data/transactions.jsonl
{"id": "TX-000001", ...}                     ← TX-000009/10 을 못 봐서 1번부터 재발급
```

`stream()` 이 두 줄을 건너뛰므로 `max_id_num()` 이 0 을 반환하고, 다음 번호가 1이 됩니다. 파일에 이미 있는 번호와 언제든 충돌할 수 있는 상태가 됩니다.

### 2.3 해결 — `RawLine` 이라는 중간 표현

두 문제의 뿌리가 같습니다. **"읽기"라는 하나의 진입점이 두 가지 용도(조회 / 재작성·스캔)를 겸하고 있었던 것**입니다. 용도마다 필요한 것이 다릅니다.

| 용도 | 필요한 것 |
|---|---|
| 조회(list/search/summary) | 유효한 도메인 객체만 |
| 재작성(delete/update) | **모든 줄** — 못 읽는 줄도 원문 그대로 보존해야 |
| ID 스캔 | 검증 실패 줄에서도 **id 만은** 건져야 |

한 타입으로 세 요구를 만족시키는 것이 `RawLine` 입니다.

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

> **🔎 문법의 출처** — `@dataclass` 는 PEP 557 로 파이썬 3.7 에 들어온 표준 라이브러리 데코레이터입니다. `data: dict | None = None` 의 `|` 표기는 PEP 604(3.10)이고, 파일 첫머리의 `from __future__ import annotations`(PEP 563) 덕분에 **어노테이션이 평가되지 않고 문자열로만 저장**되므로 더 낮은 버전에서도 문법 오류가 나지 않습니다. → [12 §1-B](./12-syntax-and-stdlib.md)
>
> **⚙️ 내부 동작** — `dataclasses` 는 클래스 본문의 `__annotations__` 를 훑어 필드 목록을 만든 뒤, `__init__`/`__repr__`/`__eq__` 의 **소스 문자열을 만들어 `exec` 로 컴파일**해 클래스에 붙입니다(마법이 아니라 코드 생성입니다). `frozen=True` 는 여기에 더해 `__setattr__`/`__delattr__` 를 "**그 클래스 자신의 인스턴스이거나 이름이 필드이면** `FrozenInstanceError`, 그 외에는 `super().__setattr__` 으로 위임" 하는 함수로 덮고, `eq=True`(기본) + `frozen=True` 조합일 때만 `__hash__` 를 필드 튜플의 해시로 생성합니다. `frozen` 없이 `eq=True` 면 `__hash__` 가 `None` 이 되어 **해시 불가**가 됩니다 — 그래서 `TransactionId` 가 `set` 에 들어갈 수 있는 것이 `frozen=True` 덕분입니다(§4.2). → [12 §1-B](./12-syntax-and-stdlib.md)

세 상태를 표로 정리하면:

| 줄의 상태 | `text` | `data` | `entity` | 재작성 시 | ID 스캔 시 |
|---|---|---|---|---|---|
| 정상 | 있음 | 있음 | **있음** | 객체를 다시 직렬화 | `data["id"]` |
| JSON 은 맞지만 규칙 위반 | 있음 | 있음 | None | **원문 보존** | `data["id"]` |
| JSON 도 아님 | 있음 | None | None | **원문 보존** | 정규식으로 발굴 |

---

## 3. `JsonlStore` — 파일 포맷을 다루는 법 (제네릭 기반 클래스)

### 3.1 왜 공통 클래스로 올렸나

budget_app/storage/jsonl.py:131-140

```python
class JsonlStore(Generic[T]):
    """JSONL 파일 하나를 다루는 공통 동작.

    세 저장소가 열기/스트리밍/원자적 재작성 코드를 각자 복사해 갖고 있었다.
    "파일 포맷을 다루는 법"은 여기 한 번만 두고, 하위 클래스는 **엔티티별 규칙**
    (어떤 dataclass 인가, 무엇이 유일 키인가)만 갖는다.
    """

    #: 하위 클래스가 지정 — 줄 하나를 세울 dataclass
    entity_cls: type
```

리팩터 전에는 `TransactionRepository.stream`, `CategoryStore.stream`, `BudgetStore.stream` 이 **거의 같은 코드 11줄씩** 있었습니다. 생성자와 `_append` 도 마찬가지였습니다.

`Generic[T]` / `entity_cls` 의 역할 차이는 [03 §6](./03-python-advanced.md)에서 다룹니다. 요약하면 **`T` 는 타입 검사용, `entity_cls` 는 런타임용**입니다.

> **🔎 문법의 출처** — `TypeVar` 와 `Generic` 은 PEP 484(파이썬 3.5)의 `typing` 모듈에서 왔습니다. `T = TypeVar("T")` 에서 이름을 두 번 쓰는 이유는, 대입문의 왼쪽 이름을 객체가 알 방법이 없어 **문자열로 다시 알려 줘야** 하기 때문입니다. 3.12 부터는 `class JsonlStore[T]:` 라는 새 문법(PEP 695)이 있지만 이 소스는 `>=3.10` 을 요구하므로 옛 표기를 씁니다 — **일반론 예시이며 이 소스에는 없습니다.** → [12 §1-C](./12-syntax-and-stdlib.md)
>
> **⚙️ 내부 동작** — `JsonlStore[Transaction]` 은 `type.__getitem__` 이 아니라 클래스의 `__class_getitem__` 을 부르고, 그 결과는 **새 클래스가 아니라 `typing._GenericAlias` 객체**입니다(로컬 3.13.1 확인: `type(S[int])` → `<class 'typing._GenericAlias'>`, `.__origin__` 은 원래 클래스, `.__args__` 는 `(int,)`). 런타임 검사는 **전혀 하지 않습니다** — `JsonlStore[Budget]()` 에 `Transaction` 을 넣어도 아무 일도 일어나지 않습니다. 그래서 "한 줄을 무슨 dataclass 로 세울지"는 타입이 아니라 `entity_cls` 라는 **평범한 클래스 속성**이 들고 있어야 합니다. → [12 §1-C](./12-syntax-and-stdlib.md)

### 3.2 생성자는 경로만 계산합니다

budget_app/storage/jsonl.py:142-158

```python
    def __init__(self, path: Path) -> None:
        # 생성자는 경로 계산만 한다. 파일/폴더를 만드는 것은 ensure_ready() 의 일이다.
        # (이전에는 생성자가 mkdir·touch·기본 카테고리 시딩까지 해서, 객체를 만드는
        #  것만으로 디스크가 바뀌었다. 오타 난 --data-dir 도 조용히 폴더가 생겼다.)
        self.path = Path(path)

    # ---------- 준비 ----------

    def ensure_ready(self) -> None:
        """파일이 없으면 만든다 — 명시적으로 호출될 때만 디스크를 건드린다."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    @property
    def is_empty(self) -> bool:
        return not self.path.exists() or self.path.stat().st_size == 0
```

**"객체를 만드는 것"과 "환경을 준비하는 것"의 분리**입니다. 이 결정의 효과는 [04 §6.2](./04-architecture.md)에서 다뤘습니다 — `backup` 명령이 존재하지 않는 폴더를 만들어 버리는 문제가 여기서 해결됩니다.

`is_empty` 의 `not self.path.exists() or ...` 순서에 주의하세요. 파일이 없으면 `stat()` 이 예외를 내므로 **단락 평가로 앞에서 막습니다.**

> **🔎 문법의 출처** — `or` 의 단락 평가는 파이썬 초기부터 있는 규칙입니다. 바이트코드 수준에서 `A or B` 는 "A 를 계산 → 참이면 **B 를 아예 실행하지 않고** 점프" 로 컴파일됩니다(`JUMP_IF_TRUE_OR_POP` 류). 또 `or` 는 불리언이 아니라 **먼저 참이 된 피연산자 자체**를 돌려줍니다 — `set(taken or ())`(§4.2)가 그 성질을 쓰는 자리입니다. → [12 §1-A](./12-syntax-and-stdlib.md)
>
> **⚙️ 내부 동작** — `pathlib` 은 PEP 428 로 3.4 에 들어왔고, `Path` 는 문자열을 감싼 **불변 객체**라 `Path(path)` 를 이미 `Path` 에 다시 씌워도 안전합니다(방어적 정규화). 각 메서드는 결국 `os` 호출로 내려갑니다 — `exists()`/`stat()` 은 `os.stat`(POSIX `stat(2)`, Windows `GetFileInformationByHandle`), `mkdir(parents=True, exist_ok=True)` 는 `os.mkdir` 을 상위 경로부터 반복하며 `FileExistsError` 를 삼키는 것, `touch()` 는 `os.open(..., O_CREAT | O_WRONLY ...)` 후 즉시 닫기입니다. `st_size` 는 파일을 열지 않고 **메타데이터만** 보므로 "빈 파일인가"를 O(1) 로 답합니다. → [12 §2-B](./12-syntax-and-stdlib.md)

### 3.3 `iter_raw()` — 어떤 줄도 버리지 않는 읽기

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

> **🔎 문법의 출처** — 함수 본문에 `yield` 가 하나라도 있으면 그 함수는 **제너레이터 함수**가 됩니다(PEP 255, 파이썬 2.2). 컴파일러가 코드 객체에 `CO_GENERATOR` 플래그를 세우고, `iter_raw()` 호출은 **본문을 한 줄도 실행하지 않은 채** 제너레이터 객체만 돌려줍니다. 본문은 첫 `next()`(= `for` 문의 첫 회전) 때 비로소 시작됩니다. 로컬 3.13.1 에서 확인한 결과가 그대로입니다 — 호출 시점에는 아무 출력이 없고 첫 `next()` 에서 본문이 실행됐습니다. 그래서 `if not self.path.exists(): return` 의 **파일 없음 검사도 소비 시점까지 미뤄집니다.** 제너레이터 안의 인자 없는 `return` 은 값 반환이 아니라 `StopIteration` 을 일으켜 반복을 끝내라는 뜻입니다(PEP 380 이후 `return v` 도 가능하지만 이 소스에는 없습니다). → [12 §1-C](./12-syntax-and-stdlib.md)
>
> **⚙️ 내부 동작 — `with` 블록이 제너레이터 수명 동안 열려 있습니다.** `with open(...)` 이 `yield` 를 감싸고 있으므로 파일은 **호출자가 마지막 줄을 꺼낼 때까지 닫히지 않습니다.** 소비자가 도중에 그만두면(예: `any()` 의 조기 종료) 제너레이터 객체가 가비지 컬렉션될 때 `close()` 가 호출되고, `yield` 지점에서 `GeneratorExit` 가 던져지면서 `with` 의 `__exit__` 이 파일을 닫습니다. CPython 은 참조 카운트가 0 이 되는 즉시 그 일을 하지만, **"언제 닫히는가"가 호출자에게 달려 있다**는 사실 자체는 알고 있어야 합니다. → [12 §1-C](./12-syntax-and-stdlib.md)

**`_parse_line` 이 예외를 던지지 않는다**는 점이 설계의 핵심입니다. 파일을 읽는 도중 예외가 올라오면 반복이 중단되는데, "손상된 줄 하나"는 나머지 줄을 못 읽을 이유가 되지 않습니다.

### 3.3.1 `errors="surrogateescape"` — 손상 줄 원문 보존의 진짜 근거

인용에서 `...` 로 접힌 docstring 이 사실 이 계층에서 가장 중요한 한 문단입니다.

budget_app/storage/jsonl.py:167-170

```python
        ``errors=surrogateescape`` 가 "손상 줄 격리" 약속을 **인코딩 층까지** 넓힌다.
        이전에는 엄격 디코딩이라 UTF-8 이 아닌 바이트 한 줄이 ``UnicodeDecodeError``
        로 **파일 전체 읽기를 죽였다** — JSON 이 깨진 줄은 격리하면서 바이트가 깨진
        줄은 격리하지 못하는, 같은 약속의 구멍이었다.
```

`FILE_ERRORS` 는 상수 하나로 읽기와 쓰기 양쪽에 같이 걸립니다.

budget_app/storage/config.py:22-26

```python
FILE_ENCODING = "utf-8"
#: 디코딩 불가 바이트를 예외 대신 대리 문자로 받아 **무손실 왕복**시킨다.
#: 읽기와 쓰기가 같은 정책을 쓰므로 손상된 줄이 원문 바이트 그대로 보존된다.
FILE_ERRORS = "surrogateescape"
LINE_TERMINATOR = "\n"
```

> **🔎 문법의 출처** — `surrogateescape` 오류 핸들러는 PEP 383 으로 파이썬 3.1 에 들어왔습니다. 원래 목적은 "OS 가 주는 파일 이름 바이트가 선언된 인코딩을 어길 때 프로그램이 죽지 않게" 하는 것이었습니다. 규칙은 단순합니다 — **디코딩할 수 없는 바이트 `0xNN`(0x80~0xFF) 하나를 코드포인트 `U+DCNN` 하나에 실어 둔다.** U+DC80..U+DCFF 는 유니코드의 "하위 서로게이트" 구역이라 정상 텍스트에는 절대 나타나지 않으므로 충돌하지 않습니다. 인코딩할 때 같은 핸들러를 쓰면 그 구간의 문자를 **원래 바이트로 되돌려** 씁니다. → [12 §3](./12-syntax-and-stdlib.md)

**실행으로 확인한 왕복(로컬 CPython 3.13.1).** UTF-8 이 아닌 바이트가 섞인 파일을 이 정책으로 읽고 같은 정책으로 다시 쓰면 바이트가 **완전히 동일**하게 복원됩니다.

```python
>>> open("se.jsonl","wb").write(b'{"id":"TX-000001"}\n\xff\xfe not utf-8\n')
>>> lines = [l.rstrip("\n") for l in open("se.jsonl", encoding="utf-8", errors="surrogateescape")]
>>> repr(lines[1])
"'\\udcff\\udcfe not utf-8'"        # 0xff → U+DCFF, 0xfe → U+DCFE
>>> with open("out.jsonl","w",encoding="utf-8",errors="surrogateescape",newline="\n") as f:
...     for l in lines: f.write(l + "\n")
>>> open("se.jsonl","rb").read() == open("out.jsonl","rb").read()
True                                # 바이트 단위로 원본과 동일
```

이것이 `plan_rewrite` 의 "**원문 보존**"(`lines.append(raw.text)`)이 **바이트 수준에서** 성립하는 이유입니다. 정책이 한쪽만 `surrogateescape` 였다면 보존된 줄이 `U+FFFD`(대체 문자)로 뭉개지거나 `UnicodeEncodeError` 로 쓰기가 죽었을 것입니다.

**참고 — 정책이 아니었다면:**

| `errors=` | 읽기 시 깨진 바이트 | 다시 쓸 때 |
|---|---|---|
| `"strict"`(기본) | `UnicodeDecodeError` — **파일 전체 읽기 중단** | (도달 못 함) |
| `"replace"` | `U+FFFD` 로 치환 | 원문이 `?`/`�` 로 **영구 훼손** |
| `"surrogateescape"` | `U+DCNN` 으로 보관 | **원래 바이트 복원** ✅ |

**두 단계 `try` 의 의미.**

```
line ──json.loads──▶ ┬─ 실패: RawLine(text만)          ← JSON 조차 아님
                     └─ 성공: data
                          │
                          ├─from_dict──▶ ┬─ 실패: RawLine(text, data)  ← 규칙 위반
                          │              └─ 성공: RawLine(text, data, entity)
```

두 번째 실패 시 `data` 를 담아 두는 것이 **ID 스캔을 살립니다** — 값이 규칙에 안 맞아도 `data["id"]` 는 읽을 수 있기 때문입니다.

`_LINE_ERRORS` 튜플이 잡는 네 가지:

budget_app/storage/jsonl.py:37-40

```python
# 한 줄을 도메인 객체로 세우다 실패할 수 있는 경우들.
# JSONDecodeError: JSON 이 아님 / KeyError: 필수 키 없음 / ValidationError: 규칙 위반
# TypeError: JSON 은 맞지만 객체가 아님(예: 최상위가 리스트)
_LINE_ERRORS = (json.JSONDecodeError, ValidationError, KeyError, TypeError)
```

`TypeError` 가 포함된 이유가 재미있습니다. `[1, 2, 3]` 같은 JSON 배열이 한 줄에 있으면 `json.loads` 는 성공하고 리스트를 돌려주는데, `from_dict` 에서 `data["id"]` 가 `TypeError: list indices must be integers` 를 냅니다.

> **🔎 문법의 출처** — 잡을 예외 목록을 모듈 상수 `_LINE_ERRORS` 로 빼 둘 수 있는 이유는, `except` 절이 **런타임에 평가되는 식**을 받기 때문입니다(`except (A, B) as e:` 의 튜플 형태는 파이썬 1.x 부터, `as` 표기는 PEP 3110/3.0). 예외 클래스를 문법이 아니라 **값**으로 다룰 수 있다는 뜻입니다. → [12 §1-C](./12-syntax-and-stdlib.md)
>
> **⚙️ 내부 동작** — `json.JSONDecodeError` 는 `ValueError` 의 하위 클래스입니다(로컬 확인: MRO 가 `JSONDecodeError → ValueError → Exception → BaseException`). `json.loads` 는 C 로 짜인 스캐너(`_json` 확장 모듈)로 파싱하고, 실패하면 **그 스캐너가** 위치·줄·열 정보를 붙인 `JSONDecodeError` 를 직접 던집니다(값 자체가 없는 경우만 `json/decoder.py` 의 `raw_decode` 가 스캐너의 `StopIteration` 을 받아 같은 예외로 바꿉니다). `str(exc)` 는 `"Expecting value: line 1 column 3 (char 2)"` 같은 사람이 읽을 문자열이 됩니다. 그 문자열이 그대로 `RawLine.error` 에 담겨 나중에 경고 로그로 나갑니다. → [12 §2-A](./12-syntax-and-stdlib.md)

### 3.4 `stream()` — 조회 전용, 유효한 것만

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

**docstring 의 마지막 문장이 중요합니다** — "파일 자체는 손대지 않는다". 리팩터 전에는 이 말이 성립하지 않았습니다.

`stream()` 이 자기 파일을 열지 않고 `iter_raw()` 를 소비한다는 점도 눈여겨보세요. **제너레이터를 층층이 쌓은** 구조라 둘 다 한 번에 한 줄만 메모리에 둡니다.

> **⚙️ 내부 동작** — `logger.warning(messages.LOG_CORRUPT_LINE, self.path.name, raw.lineno, raw.error)` 에서 f-string 이 아니라 **`%s` 서식과 인자를 따로** 넘기는 것은 취향이 아닙니다. `logging` 은 인자를 `LogRecord.args` 에 그대로 보관해 두었다가, 그 레벨이 실제로 출력될 때 핸들러가 `record.getMessage()` 안에서 `msg % args` 를 수행합니다. 즉 **필터링으로 버려질 로그는 문자열 조립 비용이 0** 입니다. f-string 은 호출 전에 이미 만들어지므로 이 최적화가 사라집니다. 이 프로젝트의 로거는 `budget_app.storage`(`storage/config.py:11` 의 `LOGGER_NAME = f"{app_config.LOGGER_NAME}.storage"`)이고, 점(`.`)으로 이어진 이름이 곧 **부모-자식 트리**라 레코드는 `budget_app` 루트까지 전파(propagate)됩니다. → [12 §2-B](./12-syntax-and-stdlib.md)

### 3.5 `rewrite()` — 손상 줄을 보존하는 재작성

budget_app/storage/jsonl.py:264-268

```python
    def plan_rewrite(
        self,
        transform: Callable[[T], T | None],
        *,
        extra: Iterable[T] = (),
```

**한 함수가 다섯 가지 쓰기 연산을 전부 담당합니다.**

| 호출자 | `transform` | `extra` |
|---|---|---|
| `delete` | 대상이면 `None`, 아니면 그대로 | — |
| `replace` | 대상이면 새 객체, 아니면 그대로 | — |
| `reassign_category` | 카테고리 일치 시 `with_patch`, 아니면 그대로 | — |
| `CategoryStore.remove` | 이름이 같으면 `None`, 아니면 그대로 | — |
| `BudgetStore.set` | 같은 달이면 `None`, 아니면 그대로 | 새 예산 |

`Callable[[T], T | None]` 이라는 타입 하나가 "바꾼 것 / 그대로 / 삭제" 세 의도를 전부 표현합니다.

> **🔎 문법의 출처** — 시그니처 가운데의 홀로 선 `*` 는 **키워드 전용 인자** 표시로, PEP 3102(파이썬 3.0)에서 왔습니다. `*` 뒤의 `extra` 는 `plan_rewrite(f, [b])` 처럼 위치로 넘길 수 없고 반드시 `extra=[b]` 라고 써야 합니다 — 호출부에서 두 번째 인자가 무슨 뜻인지 읽히게 강제하는 장치입니다. (`/` 로 표시하는 위치 전용 인자는 PEP 570, 3.8 이며 **이 소스에는 없습니다.**) → [12 §1-A](./12-syntax-and-stdlib.md)
>
> **⚙️ 내부 동작** — `Callable[[T], T | None]` 은 `collections.abc.Callable` 의 `__class_getitem__` 이 만드는 별칭일 뿐이라 **런타임 검사가 없습니다.** 실제로 `transform(raw.entity)` 이 동작하는 근거는 타입이 아니라 "그 객체에 `__call__` 이 있다"는 사실입니다 — 그래서 `def _drop(...)`(중첩 함수), `lambda tx: tx`, 모듈 수준 `_keep` 이 전부 같은 자리에 들어갈 수 있습니다. `collections.abc.Callable` 에 **대괄호 첨자**를 붙여 `Callable[[T], T | None]` 로 쓸 수 있게 된 것이 PEP 585(3.9)이고(`from collections.abc import Callable` 이라는 import 자체는 그 전부터 됩니다 — `collections.abc` 모듈은 파이썬 3.3 부터 있습니다), 같은 PEP 이후 `typing.Callable` 은 비권장 별칭이 되었습니다. → [12 §1-C](./12-syntax-and-stdlib.md)

**보존 로그가 별도인 것도 의도적입니다.**

budget_app/storage/messages.py:8-9

```python
LOG_CORRUPT_LINE = "%s:%d 손상된 줄을 건너뜁니다: %s"
LOG_CORRUPT_PRESERVED = "%s: 손상된 줄 %d개를 해석하지 않고 원문 그대로 보존했습니다."
```

읽을 때(`stream`)는 "건너뜁니다", 쓸 때(`rewrite`)는 "보존했습니다" — 두 상황에서 사용자가 알아야 할 것이 다릅니다.

### 3.6 원자적 교체 — `stage_lines` / `commit_staged` / `atomic_write_lines`

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

교체를 담당하는 나머지 둘은 이렇게 짧습니다.

budget_app/storage/jsonl.py:75-87

```python
def commit_staged(tmp: Path, target: Path) -> None:
    """준비된 임시 파일을 대상 이름으로 교체한다 — 같은 파일시스템에서 원자적."""
    os.replace(tmp, target)


def atomic_write_lines(path: Path, lines: Iterable[str]) -> None:
    """파일 하나를 원자적으로 교체한다 — 준비와 커밋을 연달아 수행.

    이름에 밑줄이 없는 이유: 같은 계층의 ``ids.IdWatermark`` 도 이 함수를 쓴다.
    "JSONL 파일을 다루는 법"이 아니라 "파일 하나를 안전하게 갈아 끼우는 법"이라
    저장소 계층의 공용 도구다.
    """
    commit_staged(stage_lines(path, lines), path)
```

**이름에 밑줄이 없다**는 점을 그냥 넘기지 마세요. 파이썬에는 접근 제한자가 없고, 앞의 밑줄 하나는 **"이 모듈 밖에서는 쓰지 말라"는 관례**(PEP 8)일 뿐입니다. `atomic_write_lines` 는 `storage/ids.py:21` 이 `from .jsonl import atomic_write_lines` 로 실제로 가져다 쓰므로 밑줄을 붙이면 그 관례를 스스로 어기는 이름이 됩니다. 반대로 `_parse_line`·`_append_lines`·`_has_torn_tail` 은 `JsonlStore` 안에서만 쓰이므로 밑줄이 있습니다.

**쓰기가 두 단계로 나뉜 것**이 Unit of Work 패턴을 위한 준비입니다. 이전에는
`atomic_write_lines` 하나가 "tmp 작성 → fsync → replace"를 통째로 했는데, 그러면
**여러 파일을 함께 커밋할 수 없습니다.** 지금은 `stage_lines` 가 준비만 하고
`commit_staged` 가 교체만 하므로, 호출자가 "전부 준비 → replace 만 연달아"를
구성할 수 있습니다(→ [07 §9](./07-repository.md)).

파일 하나만 바꾸는 경로(`rewrite`, `jsonl.py:328`)는 여전히 `atomic_write_lines` 한 줄로 둘을
연달아 부릅니다 — 기존 사용처는 아무것도 달라지지 않았습니다.

**세 호출이 각각 다른 것을 보장합니다.**

| 호출 | 보장 | 보장하지 않는 것 |
|---|---|---|
| `f.flush()` | 파이썬 버퍼 → OS 버퍼 | OS 버퍼가 디스크에 도달했는지 |
| `os.fsync(fd)` | OS 버퍼 → 물리 디스크 | 이름이 바뀌었는지 |
| `os.replace()` | 이름 교체가 **원자적** | 내용이 디스크에 도달했는지 |

셋을 이 순서로 조합해야 "새 이름이 가리키는 파일에 완전한 내용이 들어 있다"가 성립합니다. `fsync` 는 리팩터에서 추가됐습니다.

#### `open()` 의 3층 구조 — 위 표를 이해하는 열쇠

위 표의 "파이썬 버퍼"와 "OS 버퍼"가 무엇인지 알아야 세 줄이 왜 셋인지 설명할 수 있습니다. 텍스트 모드 `open()` 이 돌려주는 것은 **세 겹으로 포개진 객체**입니다(로컬 3.13.1 확인).

```
f            = <_io.TextIOWrapper>   ← str 을 받아 인코딩(utf-8) + 개행 변환
f.buffer     = <_io.BufferedWriter>  ← bytes 를 모아 두는 파이썬 버퍼(기본 8 KiB)
f.buffer.raw = <_io.FileIO>          ← 실제 파일 디스크립터. write(2) 를 직접 호출
```

| 호출 | 어디까지 밀어 넣는가 |
|---|---|
| `f.write(line + "\n")` | `str` → utf-8 바이트 → **BufferedWriter 안(= 아직 프로세스 메모리)** |
| `f.flush()` | BufferedWriter → `FileIO.write` → `write(2)` 시스템 호출 → **커널 페이지 캐시** |
| `os.fsync(f.fileno())` | 커널 페이지 캐시 → **물리 저장 장치**(POSIX `fsync(2)`, Windows `FlushFileBuffers`) |

> **⚙️ 내부 동작** — `f.fileno()` 는 세 층을 뚫고 내려가 `FileIO` 가 들고 있는 **정수 파일 디스크립터**를 돌려줍니다. `os.fsync` 는 이 정수만 받는 저수준 함수라 파이썬 버퍼의 존재를 모릅니다. 그래서 `flush()` 를 먼저 부르지 않고 `fsync` 만 하면 **아직 파이썬 버퍼에 있는 바이트는 그대로 유실**됩니다 — 이 순서가 관례가 아니라 필연인 이유입니다. 참고로 `with` 블록이 끝날 때의 `close()` 는 `flush()` 까지만 하고 `fsync` 는 하지 않으므로, 내구성이 필요하면 **명시적으로 불러야 합니다.** (`with` 문이 어떤 코드로 풀리는지는 §9.2 노트에서 다룹니다.) → [12 §3](./12-syntax-and-stdlib.md)

#### `newline="\n"` — Windows 에서 이것이 없으면 파일이 달라집니다

`stage_lines`/`_append_lines` 는 `newline=config.LINE_TERMINATOR`(= `"\n"`)로 열고, CSV 쪽은 `newline=""` 로 엽니다. **다른 값인 데는 이유가 있습니다.**

> **🔎 문법의 출처** — `newline=` 은 파이썬 3 의 새 I/O 스택(PEP 3116)이 `TextIOWrapper` 에 도입한 인자입니다. 쓰기 모드에서 `None`(기본)이면 문자열 안의 `"\n"` 을 **`os.linesep` 으로 치환**하고, `""` 또는 `"\n"` 이면 아무 변환도 하지 않습니다. 읽기 모드에서 `None` 이면 `\n`/`\r\n`/`\r` 을 모두 `"\n"` 으로 바꿔 주는 **범용 개행(universal newlines)** 이 켜집니다. → [12 §3](./12-syntax-and-stdlib.md)

로컬 Windows(`os.linesep == "\r\n"`)에서 실행한 결과입니다.

```python
>>> open("a.txt","w",encoding="utf-8").write("a\nb\n")                 # 기본값
>>> open("a.txt","rb").read()
b'a\r\nb\r\n'                       # ← \n 이 \r\n 으로 바뀌었다
>>> open("b.txt","w",encoding="utf-8",newline="\n").write("a\nb\n")    # 지금 코드
>>> open("b.txt","rb").read()
b'a\nb\n'                           # ← 그대로
```

이 차이가 왜 치명적인가 하면, `_has_torn_tail`(§3.7)이 마지막 **바이트**를 `"\n".encode("utf-8")` = `b"\n"` 과 비교하기 때문입니다. 기본값으로 열어 `\r\n` 이 쓰였다면 마지막 바이트는 `b"\n"` 이 맞아 통과하지만, 파일 안에는 JSONL 표준이 아닌 `\r` 이 섞이고 플랫폼마다 파일 내용이 달라집니다. **데이터 파일 포맷을 OS 에 맡기지 않겠다**는 선언이 `newline="\n"` 한 줄입니다.

#### `path.with_suffix(path.suffix + ".tmp")` — 왜 이렇게 겹쳐 쓰나

> **⚙️ 내부 동작** — `Path.with_suffix(s)` 는 확장자를 **덧붙이는 게 아니라 대체**합니다. 그래서 `Path("data/transactions.jsonl").with_suffix(".tmp")` 는 `data/transactions.tmp` 가 되어 **원래 확장자가 사라집니다.** 현재 확장자를 앞에 이어 붙이면(`p.suffix + ".tmp"`) 의도한 `data/transactions.jsonl.tmp` 가 나옵니다(로컬 확인). 확장자가 없는 파일에서도 안전합니다 — `Path("data/id_counter").suffix` 는 빈 문자열이라 결과가 `data/id_counter.tmp` 입니다. `IdWatermark` 가 쓰는 파일이 정확히 그 경우입니다. 임시 파일을 `tempfile` 이 아니라 **같은 폴더에 만드는 것도 필수**입니다 — `os.replace` 의 원자성이 같은 파일시스템 안에서만 성립하기 때문입니다. → [12 §2-B](./12-syntax-and-stdlib.md)

#### `os.replace` 가 보장하는 것과 보장하지 않는 것

> **🔎 문법의 출처** — `os.replace` 는 파이썬 3.3 에 추가됐습니다. 그 전에는 `os.rename` 을 썼는데, `os.rename` 은 **POSIX 에서는 대상을 덮어쓰고 Windows 에서는 `FileExistsError`** 를 내는 식으로 플랫폼마다 동작이 달랐습니다. `os.replace` 는 "있으면 덮어쓴다"로 **양쪽 동작을 통일**한 것입니다. 그래서 이 코드는 Windows 에서도 그대로 돕니다. → [12 §3](./12-syntax-and-stdlib.md)
>
> **⚙️ 내부 동작** — POSIX 에서는 `rename(2)`, Windows 에서는 `MoveFileExW(..., MOVEFILE_REPLACE_EXISTING)` 로 내려갑니다. 원자성의 범위를 정확히 말하면 **"같은 파일시스템 안에서, 디렉터리 엔트리가 가리키는 대상이 바뀌는 순간이 쪼개지지 않는다"** 뿐입니다. 세 가지는 보장하지 않습니다. (1) **다른 파일시스템**으로 옮기면 원자적이지 않고 `OSError(EXDEV)` 가 납니다. (2) **디렉터리 엔트리 자체의 내구성**은 별개라, 완벽을 기하려면 부모 디렉터리를 열어 `os.fsync` 해야 합니다(이 소스는 거기까지는 하지 않습니다 — CLI 도구의 합리적 절충입니다). (3) **Windows 에서는 대상 파일을 다른 프로세스(또는 자기 자신)가 열고 있으면 `PermissionError` 로 그냥 실패합니다** — POSIX 에는 없는 실패 모드이고, `UnitOfWork.commit` 이 그것을 명시적으로 다루는 이유입니다(§9.2 참조). → [12 §3](./12-syntax-and-stdlib.md)

**시나리오별 결과:**

```
정상:      임시 파일 작성 → fsync → replace → 완료
           ✅ 새 내용

쓰기 중 죽음:  임시 파일 일부 작성 → 프로세스 종료
           ✅ 원본 무사, .tmp 찌꺼기만 남음

replace 중 전원 차단:  원자적이므로 "이전" 또는 "이후"만 존재
           ✅ 원본 또는 새 내용 (중간 상태 없음)

fsync 가 없었다면 + 전원 차단:
           ❌ 새 이름이 빈 파일을 가리킬 수 있음  ← 이걸 막은 것
```

자세한 crash 시나리오 분석은 [10. 고급 설계 주제](./10-advanced-design.md)에 있습니다 — 요약하면 **"원본은 `os.replace` 가 성공하는 그 순간까지 한 번도 수정되지 않는다"** 가 위 네 시나리오를 모두 설명하는 한 문장입니다.

### 3.7 이어 쓰기 — `_append_lines` 와 `_has_torn_tail`

`rewrite` 가 파일 전체를 갈아 끼우는 경로라면, `append` 계열은 **파일 끝에 붙이는 O(1) 경로**입니다. 여기에도 두 가지 방어가 들어 있습니다.

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

"찢어진 꼬리"는 마지막 줄에 개행이 없는 파일입니다. 그냥 이어 쓰면 새 JSON 이 그 줄 뒤에 붙어 **한 줄**이 되고, 기존 줄과 방금 "저장 완료"라고 알린 레코드가 **동시에** 죽습니다. 그래서 마지막 바이트를 먼저 확인합니다.

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

> **⚙️ 내부 동작 — 왜 `'rb'` 여야만 하는가.** 텍스트 모드(`TextIOWrapper`)에서는 **음수 오프셋 seek 이 아예 금지**돼 있습니다. 디코딩과 개행 변환 때문에 "문자 위치"와 "바이트 위치"가 일치하지 않아, 파일 끝에서 1을 뺀 지점이 어느 문자인지 계산할 수 없기 때문입니다. 로컬 3.13.1 에서 실제로 확인했습니다.
>
> ```python
> >>> open("x.txt","r",encoding="utf-8").seek(-1, os.SEEK_END)
> io.UnsupportedOperation: can't do nonzero end-relative seeks
> ```
>
> 바이너리 모드는 `BufferedReader` → `FileIO` 두 겹뿐이고 `seek` 이 그대로 `lseek(2)` 로 내려가므로 **파일 크기와 무관하게 1바이트만** 읽습니다. 텍스트 모드로 같은 일을 하려면 파일 전체를 디코딩해야 하고, 애초에 인코딩이 깨진 파일에서는 그 디코딩이 실패합니다. → [12 §3](./12-syntax-and-stdlib.md)
>
> **⚙️ `st_size == 0` 선검사가 장식이 아닌 이유.** 빈 파일에서 `seek(-1, os.SEEK_END)` 를 하면 오프셋이 음수가 되어 바이너리 모드에서도 실패합니다(로컬 확인: `OSError: [Errno 22] Invalid argument`). 물론 아래 `except OSError` 가 잡아 주지만, **예외를 흐름 제어로 쓰지 않겠다**는 뜻으로 크기를 먼저 봅니다. `stat()` 은 파일을 열지도 않으므로 더 싸기도 합니다.

`f.write(...)` 뒤에 `flush()` + `fsync()` 가 또 나오는 것을 눈여겨보세요. docstring 이 "**내구성 비대칭**"이라고 부른 문제입니다 — 재작성 경로만 `fsync` 를 하고 이어 쓰기 경로는 하지 않으면, **같은 프로그램의 두 쓰기가 서로 다른 내구성을 약속**하게 됩니다. CLI 는 명령 하나에 한 번 쓰고 끝나므로 `fsync` 비용도 문제가 되지 않습니다.

---

## 4. `IdAllocator` — ID 발급 규칙의 단일 정의처

### 4.1 리팩터 전의 문제

ID 발급 규칙이 **두 곳**에 있었습니다.

```python
# 리팩터 전 — repository.py
    def next_id(self) -> str:
        return config.TX_ID_FORMAT.format(self.max_id_num() + 1)

# 리팩터 전 — services.py (성능 때문에 흉내낸 코드)
            next_num = self.txs.max_id_num()
            for lineno, row in enumerate(reader, start=2):
                ...
                next_num += 1
                prepared.append(Transaction(id=config.TX_ID_FORMAT.format(next_num), ...))
```

**서비스가 저장소의 ID 포맷(`TX_ID_FORMAT`)을 알아야 했습니다.** 매 행마다 파일을 다시 훑지 않으려는 성능 최적화가 계층 경계를 넘은 것입니다.

### 4.2 발급기를 객체로

budget_app/storage/ids.py:81-111

```python
class IdAllocator:
    """거래 ID 발급기 — 이미 쓰인 번호를 건너뛰며 순차 발급한다.
    ...
    """

    def __init__(self, start: int = 0, taken: Iterable[TransactionId] | None = None) -> None:
        self._counter = start
        self._taken: set[TransactionId] = set(taken or ())

    def is_taken(self, tx_id: TransactionId) -> bool:
        return tx_id in self._taken

    def reserve(self, tx_id: TransactionId) -> None:
        """외부에서 지정한 id 를 점유 처리한다(CSV 가 실어 온 id 등)."""
        self._taken.add(tx_id)
        self._counter = max(self._counter, tx_id.number)

    def next(self) -> TransactionId:
        """아직 쓰이지 않은 다음 번호를 발급한다.

        ``while`` 인 이유: CSV 가 큰 번호를 먼저 실어 오면 ``reserve`` 가 카운터를
        끌어올리지만, 순서가 뒤죽박죽이면 이미 점유된 번호에 부딪칠 수 있다.
        """
        while True:
```

**`next()` 가 `while True` 인 이유.** 단순히 `counter += 1` 만 하면 CSV 가 실어 온 id 와 부딪칠 수 있습니다.

```
파일 상태: TX-000001, TX-000005 존재  →  start=5, taken={TX-000001, TX-000005}

CSV 행 1: id 없음     → next() → counter=6 → TX-000006 (taken 에 없음) ✅
CSV 행 2: id=TX-000007 → reserve() → taken 에 추가, counter=max(6,7)=7
CSV 행 3: id 없음     → next() → counter=8 → TX-000008 ✅  (7 과 충돌 안 함)
```

`reserve` 가 `counter` 도 갱신하기 때문에 대부분의 경우 루프는 한 번만 돕니다. `while` 은 CSV 가 id 를 뒤죽박죽 순서로 실어 왔을 때를 위한 안전장치입니다.

> **⚙️ 내부 동작 — `_taken` 이 `set` 인 것이 성능의 전부입니다.** `candidate not in self._taken` 은 `set.__contains__` 이고, CPython 의 `set` 은 **열린 주소법 해시 테이블**이라 `hash(x)` 로 슬롯을 찾은 뒤 그 자리의 원소와 `==` 를 한 번 비교하는 것으로 끝납니다 — 평균 O(1) 입니다. 같은 코드를 `list` 로 바꾸면 `in` 이 앞에서부터 전부 비교하는 O(n) 이 되어, 10만 건 가져오기가 O(n²) 로 무너집니다. `x in s` 가 성립하려면 `x` 가 **해시 가능**해야 하는데, `TransactionId` 가 `@dataclass(frozen=True)` 라 `dataclasses` 가 `__hash__` 를 자동 생성해 준 덕분입니다(`frozen` 없이 `eq=True` 면 `__hash__` 가 `None` 이라 `TypeError: unhashable type` 이 납니다 — §2.3 노트 참조). 게다가 `TransactionId.__post_init__` 이 값을 **정규형으로 다시 찍기** 때문에 `TX-1` 과 `TX-000001` 이 같은 해시·같은 원소가 되고, 그래서 집합이 중복을 실제로 거릅니다. → [12 §1-B](./12-syntax-and-stdlib.md)
>
> **🔎 문법의 출처** — `set(taken or ())` 는 §3.2 노트의 단락 평가를 **기본값 관용구**로 쓴 것입니다. `taken=None` 이면 빈 튜플이 대신 들어갑니다. `def __init__(self, taken=set())` 이라고 쓰지 않은 이유가 중요합니다 — 파이썬의 기본 인자는 **함수 정의 때 한 번만** 평가되므로, 그렇게 썼다면 집합 하나를 모든 인스턴스가 공유했을 것입니다. → [12 §1-A](./12-syntax-and-stdlib.md)

### 4.3 ID 스캔 — 검증 실패 줄에서도 id 를 건진다

budget_app/storage/repositories.py:39-51

```python
    @staticmethod
    def _scan_id(raw: RawLine) -> TransactionId | None:
        """한 줄에서 거래 id 를 최대한 건져낸다.

        검증에 실패한 줄에도 id 는 들어 있을 수 있고, 그 번호는 **이미 쓰인 번호**다.
        놓치면 재발급으로 중복 id 가 생긴다. dict 까지 해석된 줄은 키에서, JSON 조차
        아닌 줄은 원문 정규식으로 찾는다(``TransactionId.scan``).
        """
        if raw.data is not None:
            candidate = raw.data.get("id")
            if isinstance(candidate, str) and tx_id_module.is_valid(candidate):
                return TransactionId(candidate.strip())
        return TransactionId.scan(raw.text)
```

> **⚙️ 내부 동작** — 정규식 두 개가 서로 다른 메서드를 씁니다. 검증용 `_EXACT`(`domain/tx_id.py:45`)는 `re.match` 로 **문자열 처음부터**만 맞춰 보고, 발굴용 `_SCAN`(`:48`)은 `re.search` 로 **줄 어디서든** 찾습니다. `re.compile` 로 미리 컴파일해 모듈 상수로 둔 것은, 컴파일 결과가 정규식 전용 바이트코드를 담은 `Pattern` 객체이고 그 컴파일이 한 번만 일어나면 되기 때문입니다(`re` 모듈에도 내부 캐시가 있지만 크기 제한이 있고, 상수로 두면 의도가 드러납니다). 패턴은 `TX_ID_SCAN_PATTERN = r'"id"\s*:\s*"(TX-\d+)"'`(`domain/config.py:27`)라 **JSON 이 깨진 줄에서도 `"id": "TX-000010"` 조각만 있으면** 번호를 건집니다. → [12 §2-A](./12-syntax-and-stdlib.md)

**`_scan_id` 의 2단 전략**이 이 계층의 방어력을 결정합니다.

```
줄 상태                          경로                       결과
────────────────────────────────────────────────────────────────
정상                             raw.data["id"]             TX-000001
amount=0 (검증 실패)              raw.data["id"]             TX-000009  ← 건짐!
{"id":"TX-000010", 뒤가 깨짐      정규식 search              TX-000010  ← 건짐!
완전히 다른 텍스트                 정규식 실패 → ""           건너뜀
```

`id_state()` 가 **최대 번호와 사용 중 집합을 한 번의 순회로** 구하는 것도 눈여겨보세요. 두 값을 따로 구하면 파일을 두 번 읽어야 합니다.

**시작점은 두 값의 최대입니다.** `id_allocator()` 는 파일 스캔 결과만 믿지 않습니다.

budget_app/storage/repositories.py:76-77

```python
        max_n, taken = self.id_state()
        return IdAllocator(start=max(max_n, self._watermark.read()), taken=taken)
```

`IdWatermark`(`storage/ids.py:26-78`)는 **발급된 적 있는 최대 번호를 숫자 한 줄짜리 파일(`id_counter`)에 남깁니다.** 파일 스캔 최대값은 "지금 무엇이 있는가"라 삭제하면 줄어들고, 그러면 지운 번호가 부활해 예전에 내보낸 CSV 를 다시 가져올 때 서로 다른 거래가 "이미 있는 id"로 판정돼 조용히 버려집니다. 워터마크는 줄어들지 않는 기준선이라 그 경로를 막습니다. 이 파일이 없거나 깨져도 `read()` 가 0 을 돌려주므로 **안전장치가 고장 나도 본체는 멈추지 않습니다.**

> **⚙️ 내부 동작** — `remember` 가 `atomic_write_lines` 를 쓰는 것이 핵심입니다. 이 파일이 반쯤 쓰인 채로 남으면 `int(text)` 가 `ValueError` 를 내고 `read()` 가 0 으로 떨어져 **방어가 통째로 사라집니다.** 그래서 JSONL 이 아닌 파일인데도 §3.6 의 "tmp + fsync + replace" 를 똑같이 탑니다 — `atomic_write_lines` 에 밑줄이 없는 이유가 바로 이 사용처입니다. 참고로 `int("  12\n")` 처럼 앞뒤 공백은 `int()` 가 알아서 무시하지만 `int("12.0")` 은 `ValueError` 입니다(정수 리터럴 문법만 받습니다). → [12 §2-B](./12-syntax-and-stdlib.md)

**단건 `add` 와 배치 `import` 의 차이:**

| 경로 | 호출 | 파일 스캔 횟수 |
|---|---|---|
| `add` (1건) | `next_id()` | 1회 |
| `import` (N건) | `id_allocator()` 로 받아 `next()` N번 | **1회** |

배치가 성능상 유리한 이유가 바로 이것입니다. 그리고 두 경로가 **같은 `IdAllocator` 클래스**를 쓰므로 규칙이 어긋날 수 없습니다.

---

## 5. `TransactionRepository` — 거래 저장소

`JsonlStore` 를 상속하고 거래 고유의 것만 추가합니다.

### 5.1 쓰기 연산 넷

budget_app/storage/repositories.py:138-148

```python
    def append_many(self, txs: Iterable[Transaction]) -> int:
        """여러 거래를 파일 끝에 이어 쓰고 추가된 건수를 반환한다 — O(1) 경로.
        ...
        """
        txs = list(txs)
        self.remember_ids(txs)
        return self.append_all(txs)
```

원자 모드는 `rewrite(lambda tx: tx, extra=txs)` 한 줄입니다 — "모든 기존 항목은 그대로 두고, 뒤에 신규를 붙인 파일을 원자적으로 만들어라".

budget_app/storage/repositories.py:159-167

```python
        if target is None:
            return False
        found = False

        def _drop(tx: Transaction) -> Transaction | None:
            nonlocal found
            if tx.id == target:
                found = True
                return None
```

**`delete` 는 파일을 한 번만 읽습니다.** 이전에는 `exists()` 로 먼저 확인하고 재작성하며 또 훑었는데, 더 나쁜 것은 두 스캔의 **판정 기준이 서로 달랐다**는 점입니다 — `exists()` 는 손상 줄에서 건져낸 id 까지 "있다"고 했지만, 재작성은 해석된 엔티티만 훑으므로 정작 그 줄은 지울 수 없었습니다. 지금은 훑으면서 만나는 것이 곧 판정(`found`)이라 어긋날 수가 없습니다.

그러면 "없는 id 를 지우려 했을 때 파일이 헛되이 다시 쓰이는 것"은 누가 막을까요? `rewrite` 입니다.

budget_app/storage/jsonl.py:325-329

```python
        plan = self.plan_rewrite(transform, extra=extra)
        if not plan.changed:
            return False
        atomic_write_lines(self.path, plan.lines)
        return True
```

내용이 같은데 수정 시각(mtime)만 바뀌면 백업 도구나 파일 감시가 "변경됐다"고 오해합니다. 무엇보다 **쓰지 않았는데 쓰기 실패로 죽을 이유가 없습니다.**

> **🔎 문법의 출처** — `nonlocal` 은 PEP 3104 로 파이썬 3.0 에 들어왔습니다. 파이썬에서 함수 안의 **대입문은 그 이름을 지역 변수로 만듭니다.** `nonlocal found` 가 없으면 `found = True` 는 `_drop` 안에서만 사는 새 변수를 만들고, 바깥 `delete` 의 `found` 는 영영 `False` 로 남습니다(읽기만 한다면 선언이 필요 없지만, **쓰기에는 필요합니다**). 파이썬 2 에는 이 키워드가 없어 `found = [False]` 처럼 **리스트에 담아 우회**하는 관용구를 썼습니다. → [12 §1-C](./12-syntax-and-stdlib.md)
>
> **⚙️ 내부 동작** — `nonlocal` 로 표시된 이름은 컴파일 시점에 바깥 함수의 지역 변수에서 **셀(cell) 변수**로 승격되고, 안쪽 함수는 `__closure__` 에 그 셀의 참조를 들고 다닙니다(전용 바이트코드 `LOAD_DEREF`/`STORE_DEREF`). 즉 두 함수가 **같은 상자 하나를 공유**합니다. 그래서 `self.rewrite(_drop)` 이 파일을 훑는 동안 `_drop` 이 기록한 결과를 `delete` 가 그대로 읽을 수 있고, "찾았는가"를 위해 파일을 다시 읽을 필요가 없습니다. `_swap`(§5.2)과 `_reassign` 의 `changed += 1` 도 완전히 같은 구조입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

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

**`patch` 를 루프 밖에서 한 번만 만드는 것**이 작은 최적화입니다. `TransactionPatch` 는 frozen 이라 재사용해도 안전합니다.

### 5.2 `replace` — 저장소가 도메인을 모르게

budget_app/storage/repositories.py:184-189

```python
        def _swap(tx: Transaction) -> Transaction:
            nonlocal found
            if tx.id == target:
                found = True
                return new_tx
            return tx
```

리팩터 전 `update` 와 비교하면 차이가 분명합니다.

```python
# 리팩터 전 — 저장소가 도메인 변경을 수행
    def update(self, tx_id: str, changes: Dict[str, object]) -> Optional[Transaction]:
        for tx in self.stream():
            if tx.id == tx_id:
                data = tx.to_dict()
                data.update(changes)          # ← 변경 해석
                new_tx = Transaction.from_dict(data)   # ← 도메인 규칙 재적용
```

지금은 그 두 줄이 `domain/entities.py` 의 `Transaction.with_patch`(113-124)로 올라갔고, 저장소는 **완성된 객체를 받아 교체만** 합니다.

---

## 6. `CategoryStore` — 이름 집합 관리

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

> **🔎 문법의 출처** — 마지막 줄의 `Category(name=name) for name in ...` 은 **제너레이터 식**(PEP 289, 파이썬 2.4)입니다. 보통은 괄호가 필요하지만, **함수의 인자가 그것 하나뿐일 때는 괄호를 생략**할 수 있습니다 — `append_all((...))` 의 바깥 괄호가 곧 제너레이터 식의 괄호 역할을 합니다. `append_all` 의 파라미터 타입이 `Iterable[T]` 라서 게으른 값을 그대로 받을 수 있고, 실제로 `append_all` 첫 줄의 `list(entities)` 가 그 시점에 소비합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

**`add` 와 `add_many` 가 둘 다 있는 이유**는 `IdAllocator` 와 같은 논리입니다.

| 메서드 | 파일 스캔 | 쓰기 |
|---|---|---|
| `add` × N | **N회** (매번 `exists`) | N회 |
| `add_many(N개)` | **1회** (`name_set` 한 번) | 1회 |

리팩터 전 `import_csv` 는 커밋 단계에서 `self.cats.add(name)` 을 반복 호출했습니다. 새 카테고리가 M개면 파일을 M번 훑었습니다.

**`add_many` 안에서 `known.add(cat.name)` 을 하는 것**도 중요합니다. 같은 CSV 안에 같은 카테고리가 두 번 나와도 한 번만 추가됩니다.

> **⚙️ 내부 동작 — `exists` 의 `any(...)` 는 조기 종료합니다.** `any(c.name == target for c in self.stream())` 은 제너레이터를 하나씩 당기다가 **처음 참을 만나는 순간 `True` 를 돌려주고 멈춥니다.** 그러면 `stream()` → `iter_raw()` 도 거기서 멈추고, 열려 있던 파일은 제너레이터가 정리될 때 닫힙니다 — **파일 뒷부분은 읽히지도 않습니다.** 같은 구조가 `TransactionRepository.category_in_use`(`repositories.py:124`)에도 있습니다. 반대로 `add` 를 N 번 부르면 `exists` 가 N 번 파일을 여는 것이라, 배치 경로가 `name_set()` 한 번으로 바꾸는 것이 그래서 중요합니다. → [12 §1-C](./12-syntax-and-stdlib.md)

---

## 7. `BudgetStore` — "같은 달은 덮어쓰기"

budget_app/storage/repositories.py:292-308

```python
    def get(self, month: str) -> Budget | None:
        target = validators.parse_month(month)
        result: Budget | None = None
        for b in self.stream():
            if b.month == target:
                result = b  # 같은 월의 마지막 값을 유효값으로 본다
        return result

    def set(self, month: str, amount: int) -> Budget:
        budget = Budget(month=month, amount=amount)

        # month 별 단일 값 유지 — 같은 달의 기존 항목은 지우고 새 값을 끝에 붙인다.
        def _drop_same_month(existing: Budget) -> Budget | None:
            return None if existing.month == budget.month else existing

        self.rewrite(_drop_same_month, extra=[budget])
        return budget
```

**`get` 이 `break` 하지 않는 이유**를 눈여겨보세요. 같은 달이 여러 줄 있으면 **마지막 값**을 씁니다. `set` 이 항상 중복을 제거하므로 정상 상태에서는 한 줄뿐이지만, 파일을 손으로 편집한 경우를 대비한 규칙입니다. "나중에 쓴 것이 이긴다"는 JSONL 의 자연스러운 의미와도 맞습니다.

**`set` 은 `rewrite` 한 번으로 "지우고 붙이기"를 동시에** 합니다. 삭제와 추가를 따로 하면 그 사이에 프로세스가 죽었을 때 예산이 사라진 상태가 됩니다.

---

## 8. `csv_io.py` — CSV 경계 어댑터

### 8.1 왜 서비스에서 떼어냈나

budget_app/storage/csv_io.py:1-2

```python
"""CSV 경계 어댑터 — 외부 교환 포맷과 도메인 사이의 번역만 담당한다.

```

### 8.2 `id` 컬럼 — 왕복 중복을 막는 열쇠

budget_app/storage/csv_io.py:9-22

```python

## id 컬럼 — 왕복 중복을 막는 열쇠

이전 스키마에는 ``id`` 가 없었다. 그래서 ``export`` → ``import`` 왕복을 하면 같은
거래가 **새 id 를 받아 한 번 더 저장**됐다. 내보낸 CSV 가 원본 거래를 식별할 수단을
갖고 있지 않았기 때문이다.

``id`` 는 **선택** 컬럼으로 추가했다.

- ``export`` 는 기본으로 포함한다 → 자기 파일을 다시 넣어도 중복이 생기지 않는다.
- ``import`` 는 있으면 쓰고, 없거나 비어 있으면 새로 발급한다 → 필수 컬럼만 갖춘
  외부 CSV(엑셀·타 가계부)는 예전 그대로 들어온다.
- 외부 도구에 넘길 때 id 가 거슬리면 ``export --no-id`` 로 뺄 수 있다.
"""
```

**버그 재현:**

```
$ python -m budget_app export --out rt.csv --month 2024-01
[완료] rt.csv (1 records)

$ cat rt.csv
date,type,category,amount,memo,tags          ← id 가 없다
2024-01-05,expense,food,1000,lunch,a

$ python -m budget_app import --from rt.csv   ← 방금 내보낸 파일을 그대로
[완료] mode=부분 성공, imported=1, skipped=0

$ cat data/transactions.jsonl
{"id":"TX-000001", ... "amount":1000 ...}    ← 원본
{"id":"TX-000002", ... "amount":1000 ...}    ← 같은 거래가 복제됨!
```

**수정 후:**

```
$ python -m budget_app export --out rt.csv --month 2024-01
$ head -1 rt.csv
id,date,type,category,amount,memo,tags        ← id 포함

$ python -m budget_app import --from rt.csv
[완료] mode=부분 성공, imported=0, duplicated=1, skipped=0   ← 중복으로 인식
```

### 8.3 `ParsedRow` — 정책과 어댑터의 경계

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

**"거의 다 됐지만 한 조각이 비어 있는 값"을 타입으로 표현**한 것이 이 설계의 핵심입니다. 어댑터는 여기까지, 정책은 여기부터 — 경계가 타입 하나로 그어집니다.

### 8.4 읽기 — 헤더 검증과 행 파싱

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

**빈 파일과 컬럼 누락을 구분**하는 것이 리팩터에서 추가됐습니다. 이전에는 빈 CSV 도 "필수 컬럼이 없습니다: ['date', 'type', ...]" 라고 안내했는데, 실제 문제는 "헤더 행 자체가 없다"입니다.

> **⚙️ 내부 동작 — `reader.fieldnames` 는 그 순간 첫 행을 읽습니다.** `csv.DictReader.fieldnames` 는 평범한 속성이 아니라 **`@property` 로 구현된 지연 속성**입니다. 처음 접근할 때 내부 `csv.reader` 에서 한 행을 꺼내 `self._fieldnames` 에 캐시하고, 그 뒤로는 캐시를 돌려줍니다. 즉 `_check_header(path, reader.fieldnames)` 라고 쓴 이 한 줄이 **헤더 행을 실제로 소비하는 지점**이고, 그래서 뒤이은 `enumerate(reader, ...)` 는 자동으로 2행부터 시작합니다(`CSV_DATA_START_LINE = 2` 와 짝이 맞는 이유). 로컬 3.13.1 에서 스트림 위치로 확인했습니다 — `fieldnames` 접근 전 `tell()` 은 `0`, 접근 후에는 헤더 길이만큼 전진해 있었습니다. 파일이 완전히 비어 있으면 꺼낼 행이 없어 `fieldnames` 가 `None` 이 되고, `_check_header` 의 `list(fieldnames or [])` 가 그 경우를 "헤더 없음"으로 갈라냅니다. → [12 §2-A](./12-syntax-and-stdlib.md)
>
> **🔎 문법의 출처** — `yield from` 은 PEP 380 으로 파이썬 3.3 에 들어왔습니다. `for x in it: yield x` 의 축약처럼 보이지만 그 이상으로, 하위 이터러블에 **`send`/`throw`/`close` 까지 그대로 위임**합니다. 여기서 중요한 것은 위임하는 동안 이 함수의 프레임이 **살아 있다**는 점입니다 — `with open(...)` 블록이 열린 채로 유지되고, 파일은 마지막 행을 꺼낸 뒤(또는 호출자가 중간에 그만둔 뒤)에야 닫힙니다. 소스 주석이 정확히 그 말을 합니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작 — `newline=""` 는 CSV 에서 선택이 아니라 필수입니다.** `csv` 모듈은 **자기가 개행을 직접 다루는** 모듈이라, 파일 객체가 개행을 건드리지 않도록 요구합니다(`csv` 문서가 명시). 읽기에서 `newline=""` 를 빼면 범용 개행이 켜져 **따옴표로 감싼 필드 안의 줄바꿈**(메모에 여러 줄을 적은 경우)이 훼손될 수 있고, 쓰기에서 빼면 Windows 에서 `csv.writer` 가 내보낸 `\r\n` 의 `\n` 이 다시 `\r\n` 으로 변환돼 **`\r\r\n`** 이 됩니다. 로컬에서 확인한 결과입니다.
>
> ```python
> >>> csv.writer(open("a.csv","w",encoding="utf-8")).writerow(["a","b"])
> >>> open("a.csv","rb").read()
> b'a,b\r\r\n'                       # ← 빈 줄이 하나씩 끼어 보이는 그 증상
> >>> csv.writer(open("b.csv","w",encoding="utf-8",newline="")).writerow(["a","b"])
> >>> open("b.csv","rb").read()
> b'a,b\r\n'
> ```
>
> JSONL 은 반대로 **파이썬이 개행을 쓰므로** `newline="\n"` 으로 "변환하지 말고 LF 그대로"를 지시합니다(§3.6). 두 값이 다른 것은 **개행의 주인이 누구인가**가 다르기 때문입니다. → [12 §3](./12-syntax-and-stdlib.md)

budget_app/storage/csv_io.py:107-123

```python
def parse_row(row: dict[str, str]) -> ParsedRow:
    """원시 CSV 행을 검증한다 — 실패 시 ``ValidationError``.

    필드 규칙은 ``validators`` 를 그대로 쓴다. CSV 경로라고 해서 별도의 검증 코드를
    두지 않는 것이 핵심이다(규칙은 한 곳에만 있어야 한다).
    """
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

**필수 컬럼은 `row["type"]`(대괄호), 선택 컬럼은 `row.get(...)`** 로 접근하는 구분이 일관됩니다. 헤더 검증이 필수 컬럼의 존재를 이미 보장하므로 대괄호가 안전합니다.

**빈 `id` 셀의 의미**가 이 함수의 정책 표현입니다 — 오류가 아니라 "발급해 달라". `id` 값이 있으면 형식을 강제합니다.

### 8.5 쓰기 — `include_id` 플래그

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

**`include_id` 가 두 함수에 다 전달되는 이유**: `DictWriter` 는 `fieldnames` 에 없는 키가 dict 에 있으면 `ValueError` 를 냅니다. 헤더와 행 내용이 반드시 일치해야 합니다.

**BOM 방침이 docstring 에 명시된 이유**는 실제로 겪을 수 있는 함정이기 때문입니다. Excel 호환을 위해 `utf-8-sig` 로 바꾸면 헤더 첫 컬럼명이 `﻿id` 가 되어 자기 파일을 다시 읽지 못합니다.

**읽기와 쓰기의 인코딩이 일부러 다릅니다.**

budget_app/storage/config.py:39-40

```python
CSV_ENCODING = "utf-8"
CSV_READ_ENCODING = "utf-8-sig"
```

> **⚙️ 내부 동작 — `utf-8-sig` 는 `utf-8` 과 다른 코덱입니다.** BOM(Byte Order Mark)은 UTF-8 로 인코딩된 U+FEFF, 즉 바이트 `EF BB BF` 입니다. `utf-8` 코덱은 그것을 **평범한 문자 하나**로 디코딩해 문자열 맨 앞에 `﻿` 를 남기고, `utf-8-sig` 코덱은 **읽을 때 앞의 BOM 을 먹어 치우고**(없으면 그냥 넘어감) 쓸 때는 **BOM 을 앞에 붙입니다.** 이 비대칭 정책이 막는 것이 정확히 무엇인지 로컬에서 확인했습니다.
>
> ```python
> >>> # 엑셀이 저장한 CSV (BOM 있음)
> >>> list(csv.DictReader(open("bom.csv", encoding="utf-8", newline="")))[0]
> {'﻿id': 'TX-000001', 'date': '2024-01-05'}     # ← 컬럼명이 'id' 가 아니다!
> >>> list(csv.DictReader(open("bom.csv", encoding="utf-8-sig", newline="")))[0]
> {'id': 'TX-000001', 'date': '2024-01-05'}           # ← 정상
> >>> open("out.csv","w",encoding="utf-8-sig").write("id,date\n")
> >>> open("out.csv","rb").read()
> b'\xef\xbb\xbfid,date\n'                            # ← 쓰면 BOM 이 붙는다
> ```
>
> 헤더 검증(`_check_header`)은 `"id" in names` 같은 **문자열 일치**로 판정하므로, 컬럼명 하나가 `'﻿id'` 가 되는 순간 `id` 컬럼이 "없는" 것이 됩니다. 그래서 **읽기는 `utf-8-sig` 로 관대하게**(엑셀 CSV 를 받아 주고), **쓰기는 `utf-8` 로 엄격하게**(우리가 만든 파일에는 BOM 을 넣지 않아 왕복이 항상 성립하게) — 방향마다 다른 정책이 정답입니다. → [12 §3](./12-syntax-and-stdlib.md)

**`txs` 가 제너레이터여도 동작합니다.** 서비스가 이렇게 넘깁니다.

budget_app/services/importexport.py:77-84

```python
    def export_csv(self, out_path: Path, flt: SearchFilter, *, include_id: bool = True) -> int:
        """필터를 통과한 거래를 CSV 로 저장하고 작성 건수를 반환한다.

        ``include_id=True`` 가 기본인 이유는 **왕복 안전성**이다. id 가 없으면 내보낸
        파일을 다시 가져올 때 같은 거래가 새 id 로 한 번 더 저장된다.
        """
        rows = (tx for tx in self.txs.stream() if flt.matches(tx))
        return csv_io.write_transactions(out_path, rows, include_id=include_id)
```

`(tx for tx in ...)` 는 제너레이터 식이라 **필터를 통과한 거래가 메모리에 모이지 않습니다.** 100만 건을 내보내도 메모리는 일정합니다.

---

## 9. `backup_data_dir` — 서비스에서 저장소로

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

**두 가지가 바뀌었습니다.**

1. **위치** — `services.py` → `storage/backup.py`. 도메인 판단이 전혀 없는 파일 복사입니다.
2. **`now` 주입** — 기본은 현재 시각이지만 테스트에서 고정할 수 있습니다.

> **🔎 문법의 출처** — `now: datetime | None = None` 뒤에서 `(now or datetime.now())` 로 푸는 것은 **가변/비순수 기본값을 피하는 관용구**입니다. `def backup(..., now=datetime.now())` 라고 썼다면 기본값이 **모듈을 import 한 순간에 한 번만** 평가되어, 프로그램이 얼마나 오래 돌든 항상 같은 타임스탬프가 나옵니다. 파이썬의 기본 인자는 호출 때가 아니라 **함수 정의 때** 평가되기 때문입니다. → [12 §1-A](./12-syntax-and-stdlib.md)
>
> **⚙️ 내부 동작** — `datetime.now()` 는 tzinfo 가 없는 **naive** 시각(로컬 시간)이라 백업 폴더 이름도 로컬 시간 기준입니다. `strftime("%Y%m%d_%H%M%S")` 은 C 표준 라이브러리의 `strftime` 으로 내려가며 초 단위까지만 찍으므로, 같은 초에 두 번 실행하거나 서머타임으로 시각이 되돌아가면 **이름이 겹칠 수 있습니다** — 그것을 바로 아래의 `exist_ok=False` 가 잡아 줍니다. → [12 §2-A](./12-syntax-and-stdlib.md)

**`exist_ok=False` 가 의도적**이라는 점도 다시 짚습니다. 타임스탬프 폴더가 이미 있다면 같은 초에 백업이 두 번 실행된 비정상 상황이므로 **일부러 오류를 냅니다**. `exist_ok=True` 였다면 기존 백업을 조용히 덮어썼을 것입니다.

**`write_bytes(read_bytes())`** 는 바이너리 복사입니다. 백업은 내용 해석이 아니라 복제가 목적이므로 인코딩·줄바꿈 변환을 거치지 않아야 정확합니다.

> **⚙️ 내부 동작** — `Path.read_bytes()` 는 `with self.open("rb") as f: return f.read()`, `Path.write_bytes(b)` 는 `with self.open("wb") as f: return f.write(b)` 와 같습니다. 텍스트 층(`TextIOWrapper`)이 아예 끼지 않으므로 **인코딩도 개행 변환도 일어나지 않고**, `surrogateescape` 로 보존한 손상 줄의 바이트까지 그대로 복제됩니다. 다만 파일 전체를 메모리에 올리므로 대용량에는 `shutil.copyfile` 이 맞습니다 — 가계부 JSONL 규모에서는 문제가 되지 않는 선택입니다. → [12 §3](./12-syntax-and-stdlib.md)

**복사 대상은 `*.jsonl` 만이 아닙니다.**

budget_app/storage/backup.py:43-47

```python
    yield from src.glob(config.BACKUP_GLOB)
    for name in config.BACKUP_EXTRA_FILES:
        extra = src / name
        if extra.is_file():
            yield extra
```

`BACKUP_EXTRA_FILES = (ID_COUNTER_FILE_NAME,)` 이라 **확장자 없는 `id_counter` 도 함께** 복사됩니다. 빠뜨리면 백업을 복원했을 때 "발급한 적 있는 번호" 기록이 사라져 §4.3 의 id 재사용 버그가 되살아납니다.

> **⚙️ 내부 동작** — `Path.glob("*.jsonl")` 은 셸이 아니라 파이썬이 직접 하는 일입니다. 디렉터리를 `os.scandir` 로 훑으면서 각 이름을 패턴과 대조하는데, 패턴 문법은 `fnmatch` 계열(`*`, `?`, `[...]`)이라 정규식이 아닙니다. 그래서 `*.jsonl` 은 **확장자가 없는 파일을 절대 잡지 못하고**, 위 코드처럼 따로 이어 붙여야 합니다. 이 함수 자체도 `yield from` 을 쓴 제너레이터라 호출자의 `for` 가 돌 때 비로소 디렉터리를 읽습니다. → [12 §2-B](./12-syntax-and-stdlib.md)

---

## 9. `UnitOfWork` — 여러 파일을 한 단위로 커밋

### 9.1 왜 필요한가

가져오기 커밋은 파일 **둘**을 바꿉니다. 두 쓰기 사이에 프로세스가 죽으면 **카테고리만 늘어난 고아 상태**가 남습니다. `--atomic` 이 "전부 반영 또는 전혀 반영 안 됨"을 약속하는데, 그 약속이 파일 하나 안에서만 지켜지고 있었습니다.

### 9.2 쓰기를 준비와 커밋으로 나누기

§3.6 에서 본 대로 `stage_lines`(tmp 작성 + fsync)와 `commit_staged`(replace)가 분리돼 있습니다. 그래서 순서를 이렇게 바꿀 수 있습니다.

```
[준비] 두 파일의 최종 내용을 각각 .tmp 로 작성 + fsync   ← 느린 부분
[커밋] os.replace 두 번을 연달아 실행                     ← 빠른 부분
```

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

> **🔎 문법의 출처** — `with` 문(PEP 343, 파이썬 2.5)이 요구하는 것은 `__enter__`/`__exit__` 두 메서드뿐입니다. `with UnitOfWork() as uow:` 는 대략 이렇게 풀립니다.
>
> ```python
> _mgr = UnitOfWork()
> uow = _mgr.__enter__()            # ← as 뒤의 이름은 __enter__ 의 반환값이다
> try:
>     ...본문...
> except BaseException as e:
>     if not _mgr.__exit__(type(e), e, e.__traceback__):
>         raise                     # ← __exit__ 이 참을 돌려주지 않으면 예외가 계속 간다
> else:
>     _mgr.__exit__(None, None, None)
> ```
>
> 여기서 두 가지가 중요합니다. (1) `__exit__` 의 세 인자가 정확히 `(예외 타입, 예외 객체, 트레이스백)` 이라 **"정상 종료인가"를 `exc_type is None` 으로 판정**할 수 있습니다. (2) 이 `__exit__` 은 아무것도 `return` 하지 않으므로 `None`(거짓)을 돌려주고, 따라서 **예외를 삼키지 않고 그대로 올려보냅니다** — 롤백은 하되 실패를 감추지는 않겠다는 뜻입니다. → [12 §1-C](./12-syntax-and-stdlib.md)
>
> **🔎 문법의 출처** — `def __enter__(self) -> UnitOfWork:` 에서 **아직 정의가 끝나지 않은 클래스 이름**을 반환 타입으로 쓸 수 있는 것은 파일 첫 줄의 `from __future__ import annotations`(PEP 563) 덕분입니다. 이 스위치가 켜지면 어노테이션이 평가되지 않고 **문자열로만 저장**되므로 전방 참조가 자유롭습니다. 그것이 없던 시절에는 `-> "UnitOfWork"` 처럼 따옴표를 직접 붙였는데, **이 소스에는 따옴표 어노테이션이 한 곳도 없습니다.** 세 번째 인자의 `TracebackType` 은 `types` 모듈에서 가져옵니다 — 트레이스백 객체는 파이썬 문법으로 만들 수 없는 내장 타입이라 이름을 얻으려면 그 모듈이 필요합니다. → [12 §1-C](./12-syntax-and-stdlib.md)
>
> **⚙️ 내부 동작** — `tmp.unlink(missing_ok=True)` 의 `missing_ok` 는 파이썬 3.8 에 추가된 인자로, 내부적으로 `os.unlink` 를 부르고 `FileNotFoundError` 만 삼킵니다(다른 `OSError` 는 통과시킵니다). 그래서 바깥의 `except OSError` 가 잡는 것은 "없어서"가 아니라 **권한 문제나 Windows 의 파일 잠금** 같은 진짜 실패입니다. 그 경우에도 원본은 손대지 않았으므로 `.tmp` 찌꺼기만 남고, 다음 실행이 같은 이름으로 덮어씁니다. → [12 §2-B](./12-syntax-and-stdlib.md)

**`commit` 이 `except OSError` 로 감싸여 있는 것도 이론적 대비가 아닙니다.** §3.6 의 노트에서 본 대로, **Windows 에서는 대상 파일을 누군가 열고 있으면 `os.replace` 가 `PermissionError`(= `OSError` 의 하위 클래스)로 실패**합니다. 첫 rename 은 성공하고 두 번째가 이렇게 실패하는 상황이 실제로 일어나므로, 코드는 (1) 어디까지 반영됐는지 로그로 남기고 (2) 남은 `.tmp` 를 치우고 (3) 예외를 그대로 올립니다. `self._staged.pop(0)` 을 **성공한 뒤에** 하는 것이 그 3단계를 가능하게 하는 장치입니다 — 목록에 남아 있는 것이 곧 "아직 반영되지 않은 것"이 됩니다.

### 9.3 무엇을 보장하고 무엇을 보장하지 않나

| 시나리오 | 결과 |
|---|---|
| 준비 도중 죽음 | ✅ 원본 둘 다 무사, `.tmp` 찌꺼기만 |
| 예외로 블록 탈출 | ✅ `__exit__` 이 `rollback()` → `.tmp` 정리 |
| rename 1회 후 죽음 | ❌ 한쪽만 반영될 수 있음 (창은 밀리초) |

**완전한 원자성은 아닙니다.** 진짜 다중 파일 원자성은 저널이나 SQLite 가 필요합니다. 이 패턴이 하는 일은 **창을 줄이는 것**이지 없애는 것이 아닙니다 — 그 경계를 정확히 말하는 것이 "완벽하다"고 말하는 것보다 낫습니다.

### 9.4 부분 성공 모드에는 쓰지 않는 이유

`--atomic` 없는 가져오기는 파일 끝에 이어 쓰기(append)라 O(1)입니다. UoW 를 쓰려면 전체 재작성이 필요해 10만 건 파일에 10건을 넣는 데 10만 줄을 다시 써야 합니다. **원자성을 약속한 모드에만** 비용을 지불하는 것이 맞습니다.

실제 검증:

```
$ python -m budget_app import --from ok.csv --atomic --data-dir ./d
[완료] mode=원자(전수 롤백), imported=2, duplicated=0, skipped=0
  거래 2줄 / 카테고리 7줄 / tmp 잔여 0

$ python -m budget_app import --from bad.csv --atomic --data-dir ./d
[오류] 원자적 가져오기 실패 — line 3: ... (반영된 항목 없음)
  거래 2 → 2 / 카테고리 7 → 7 / badcat 등록 안 됨 / tmp 잔여 0
```

---

## 10. 정리 — 과제 방어용 요약

**Q. 파일 기반 update/delete 를 어떻게 안전하게 처리했나요?**

임시 파일에 전부 쓰고 `flush` + `fsync` 로 디스크에 내린 뒤 `os.replace` 로 이름을 교체합니다. `os.replace` 는 같은 파일시스템에서 원자적이라 "교체 전" 아니면 "교체 후"만 존재합니다. 쓰는 도중 프로세스가 죽어도 원본은 무사하고 `.tmp` 찌꺼기만 남습니다.

**Q. 데이터가 깨지면 어떻게 되나요?**

읽기 경로가 둘입니다. 조회(`stream`)는 손상된 줄을 건너뛰고 경고 로그를 남기지만 **파일은 손대지 않습니다**. 재작성(`rewrite`)은 `iter_raw()` 를 재료로 쓰므로 해석하지 못한 줄을 **원문 그대로 다시 씁니다**. 리팩터 전에는 이 둘이 하나였고, 그래서 무관한 거래를 지우면 손상 줄이 함께 사라졌습니다.

**Q. ID 는 어떻게 발급하나요? 중복이 나지 않나요?**

`IdAllocator` 가 파일 상태(최대 번호 + 사용 중인 id 집합)를 받아 순차 발급하며, 이미 쓰인 번호는 건너뜁니다. 스캔은 `iter_raw()` 기반이라 **검증에 실패하는 줄에 들어 있던 id 도 인식**합니다. 리팩터 전에는 그 줄들이 보이지 않아 번호를 재사용했고, 실제로 같은 파일에 `TX-000001` 이 두 개 생기는 일이 있었습니다.

**Q. 제너레이터로 스트리밍한 방식과 그 이점은?**

`iter_raw()` 와 `stream()` 이 `yield` 기반이라 한 번에 한 줄만 메모리에 둡니다. `stream()` 은 자기 파일을 열지 않고 `iter_raw()` 를 소비하는 **층층이 쌓은** 구조입니다. 조기 종료가 가능한 소비자(`any()` 를 쓰는 `category_in_use`)는 파일 뒷부분을 아예 읽지 않고, 내보내기는 제너레이터 식을 그대로 CSV writer 에 넘겨 100만 건을 내보내도 메모리가 일정합니다.

**Q. 세 저장소의 공통 코드는 어떻게 정리했나요?**

`JsonlStore(Generic[T])` 에 "JSONL 파일을 다루는 법"(열기·스트리밍·원자적 재작성·추가)을 두고, 하위 클래스는 엔티티 고유의 것만 갖습니다 — `TransactionRepository` 는 ID 발급과 카테고리 재지정, `CategoryStore` 는 이름 중복과 기본값 시딩, `BudgetStore` 는 "같은 달은 덮어쓰기". 한 줄을 세우는 것은 `self.entity_cls.from_dict(data)` 인데, 세 dataclass 가 같은 이름의 classmethod 를 갖고 있어서 가능한 덕 타이핑입니다.

**Q. CSV 처리는 왜 별도 모듈인가요?**

리팩터 전에는 JSONL I/O 는 저장소, CSV I/O 는 서비스에 있어 규칙이 일관되지 않았습니다. 지금은 파일을 여는 코드가 전부 저장소 계층에 있습니다. 또 `csv_io` 는 **정책을 모릅니다** — 중복 id 를 어떻게 처리할지는 서비스가 정하고, 어댑터는 `ParsedRow`(id 가 아직 비어 있을 수 있는 값)까지만 만듭니다.

---

**다음 문서**: [08. 서비스 계층](./08-services.md) — 이 저장소들을 조합해 정책을 구현하는 곳.
