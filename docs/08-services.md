# 08. 서비스 계층 — `services/` 패키지

## 쉬운 말로 먼저

가계부 프로그램은 하는 일을 크게 넷으로 나눠 맡깁니다. 파일에 적고 읽는 일, 화면에 보여 주는 일, 값 자체가 말이 되는지 보는 일, 그리고 "지금 이걸 해도 되는가"를 정하는 일입니다. 이 문서가 다루는 부분은 마지막 것, 정하는 일만 맡습니다. 셋째와 넷째가 비슷해 보이지만 다릅니다 — 값만 들여다보면 답이 나오는 판단은 셋째가 맡고, 저장된 것을 뒤져 봐야 답이 나오는 판단은 넷째가 맡습니다(§2에서 이 경계를 다시 봅니다). 이를테면 거래를 하나 적을 때 "이 분류가 등록되어 있는가"를 확인하고, 분류를 지울 때 "그 분류를 쓰고 있는 거래가 있는데 지워도 되는가"를 따집니다. 가장 까다로운 일은 남이 만들어 준 표 파일(CSV)을 통째로 받아들이는 일입니다. 수천 줄 가운데 몇 줄이 깨져 있거나 이미 들어 있는 거래가 섞여 있을 때, 어디까지 받아들이고 어디서 멈출지를 사람 대신 정해 두어야 하기 때문입니다.

**이 문서에 자주 나오는 말**

| 말 | 쉬운 뜻 |
| --- | --- |
| 서비스 계층 | 파일도 화면도 직접 건드리지 않고 "이걸 해도 되는가"만 정하는 부분 |
| 정책 | 상황마다 어떻게 할지 미리 정해 둔 방침. 코드로는 "이럴 땐 이렇게"라는 갈림길 |
| 저장소 | 파일을 실제로 읽고 쓰는 부분. 서비스는 저장소에 시키기만 합니다 |
| 준비 → 커밋 | 파일에 손대기 전에 전부 따져 두고(준비), 그다음 한 번에 반영하는(커밋) 두 단계. 준비 중 오류가 나왔을 때 커밋을 아예 건너뛸지, 통과한 것만 반영할지는 `--atomic` 이 정합니다 |
| 원자적(`--atomic`) | 전부 되거나 전혀 안 되거나를 지향하는 모드. 절반만 반영된 상태를 거의 남기지 않습니다(완전히 없애지는 못하며, 그 한계는 §5.6 에 적어 두었습니다) |
| 중복(`--on-duplicate`) | 이미 저장된 것과 **같은 id** 를 가진 행이 또 들어오는 일, 그리고 그것을 어떻게 할지. 내용이 같은지는 보지 않습니다 |
| 참조 무결성 | 누군가 가리키고 있는 것을 함부로 없애지 않는다는 규칙 |
| 스트리밍 | 파일 전체를 한꺼번에 메모리에 올리지 않고 한 건씩 꺼내 처리하는 것 |

**바쁘면 여기만**

- **[§6 두 정책 축](#6-두-정책-축--실패와-중복은-독립이다)** — 이 문서의 결론입니다. `--atomic` 과 `--on-duplicate` 가 왜 서로 다른 질문인지가 표 두 개로 정리됩니다.
- **[§5.3 가져오기 — 준비와 커밋](#53-가져오기--준비와-커밋)** — 통과한 것만 넣는 기본 모드와 "전부 아니면 전무"에 가까운 원자 모드가 어떻게 갈리는지가 두 줄짜리 함수 안에 다 들어 있습니다.
- **[§7 정리](#7-정리--과제-방어용-요약)** — 질문과 답 형식이라 앞을 건너뛰고 읽어도 뜻이 통합니다.

---

저장소와 CLI 사이에서 **판단**만 담당하는 계층입니다. 파일을 여는 일도, 화면에 글자를 내는 일도 여기서는 하지 않습니다. 실제로 이 패키지의 어느 파일에도 `open()` 도 `print()` 도 없습니다 — `grep -rn "open(" budget_app/services/` 의 유일한 결과는 `services/__init__.py:4` 의 docstring 한 줄이고, `print(` 는 0건입니다. 이 문서가 다루는 것은 검색·요약·카테고리 보호·CSV 가져오기의 정책입니다.

> **난이도**: 🟡 중급 ~ 🔴 고급
>
> **먼저 읽으면 좋은 문서**: [05. 설정·검증·모델](./05-config-and-models.md), [07. 저장소 계층](./07-repository.md)
>
> **문법·표준 라이브러리 사전**: 아래 🔎/⚙️ 노트는 [12. 문법과 표준 라이브러리](./12-syntax-and-stdlib.md)의 해당 절로 이어집니다.

---

## 1. 계약 — "판단만 한다"

> **💡 쉽게 말하면** — 주문을 받아 "이건 만들 수 있다, 저건 재료가 없으니 안 된다"를 정하는 중간 관리자입니다. 정작 자기가 창고에 들어가 재료를 꺼내 오지도 않고, 손님 앞에 나가 말을 건네지도 않습니다. 창고 일은 저장소가, 손님 응대는 CLI 가 맡습니다.
> 다만 이 비유는 사람 관리자와 달리 이 계층이 한 번의 작업이 끝나면 아무것도 남겨 두지 않는다는 데서 깨집니다 — 상태는 전부 파일에 있고, 다음 호출은 저장소에 처음부터 다시 묻습니다. 작업이 진행되는 **동안에는** 저장소에서 떠 온 스냅숏과 준비 결과를 메모리에 들고 있습니다(§5.4).

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

docstring 이 나열하는 네 개의 유스케이스 서비스에, 폴더 단위 작업을 맡는 `BackupService` 가 하나 더 있습니다. 리팩터로 파일이 쪼개져서 **클래스마다 소유 모듈이 다릅니다** — 아래 표가 "어느 파일을 열어야 하는가"의 지도입니다.

| 클래스 | 위치 | 담당 |
|---|---|---|
| `TransactionService` | `services/transactions.py:20-91` | 거래 추가/수정/삭제/조회 |
| `BudgetService` | `services/budgets.py:20-66` | 예산 설정 + 월별 요약 |
| `CategoryService` | `services/categories.py:15-89` | 카테고리 추가/조회/삭제 (사용 중 보호) |
| `ImportExportService` | `services/importexport.py:61-206` | CSV 가져오기/내보내기 정책 |
| `BackupService` | `services/maintenance.py:29-37` | 데이터 폴더 백업 (얇은 위임) |

여기에 준비 단계 누적 상태를 담는 `_Batch`(`services/importexport.py:30-58`)가 있습니다.

**모든 서비스가 저장소를 생성자로 받습니다** — 서비스가 `TransactionRepository` 를 스스로 만들지 않고 `__init__` 으로 건네받으므로, 테스트에서 가짜 저장소를 끼워 넣을 수 있습니다(의존성 주입 — 필요한 것을 스스로 만들지 않고 밖에서 건네받는 방식. [04 §6](./04-architecture.md)).

> **🔎 문법의 출처** — 위 인용은 `services/__init__.py` 즉 **패키지 초기화 모듈**입니다(`import budget_app.services.budgets` 는 파이썬이 `services/__init__.py` 를 먼저 실행하게 만들며, 여기 docstring 뿐이라는 사실이 곧 "어느 서비스를 쓰든 추가 비용이 없다"는 뜻입니다). 그리고 각 서비스가 쓰는 `from ..storage.repositories import CategoryStore` 의 점 두 개는 **명시적 상대 import**(PEP 328)로, 파이썬 3 에서 `import repositories` 식의 암묵적 상대 import 가 사라지면서 남은 유일한 상대 표기입니다. 점의 개수가 곧 올라갈 단계라서(`.` = `services`, `..` = `budget_app`), `from . import config, messages` 는 **서비스 계층의** config 를 가리키지 루트 `budget_app/config.py` 가 아닙니다. → [12 §1-A](./12-syntax-and-stdlib.md)

---

## 2. `TransactionService` — 거래 유스케이스

### 2.1 `add` — 서비스가 판단하는 것은 하나뿐

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

> **🔎 문법의 출처** — `list[str] | None` 에는 두 개의 새 문법이 겹쳐 있습니다. 내장 타입을 바로 첨자로 쓰는 `list[str]` 는 PEP 585(파이썬 3.9)가 `typing.List[str]` 를 대신하게 한 것이고, `A | None` 은 PEP 604(파이썬 3.10)가 `Optional[str]` 를 대신하게 한 것입니다. 예전 표기로 쓰면 `from typing import List, Optional` 뒤 `Optional[List[str]]` 입니다. 파일 맨 위 `from __future__ import annotations`(PEP 563)가 어노테이션을 **평가하지 않고 문자열로 보관**하므로, 이 표기는 런타임에 해석되지 않고 타입 검사기와 사람만 읽습니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — 기본값 `memo: str = ""` 과 `tags: ... = None` 은 **함수가 정의될 때 한 번** 평가되어 함수 객체의 `__defaults__` 튜플에 박힙니다. 확인해 보면 `TransactionService.add.__wrapped__.__defaults__` → `('', None)` 입니다(`@log_call` 이 감싸고 있어 `__wrapped__` 를 거칩니다). 기본값이 호출마다 새로 만들어지지 않기 때문에 `tags: list[str] = []` 라고 썼다면 **모든 호출이 같은 리스트 하나를 공유**합니다. 그래서 `None` 을 기본값으로 두고 실제 빈 리스트 처리는 `Transaction` 쪽에 맡깁니다. 같은 함정을 dataclass 가 아예 `ValueError` 로 막는 사례는 아래 §5.7 에 있습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

**서비스가 판단하는 것은 "카테고리가 등록되어 있는가" 하나입니다.** 날짜 형식·금액 부호 같은 필드 규칙은 `Transaction.__post_init__` 이 처리하므로 여기서 손대지 않습니다.

이 구분이 [05 §1.2](./05-config-and-models.md)의 `ValidationError` vs `AppError` 와 정확히 대응합니다.

> **💡 쉽게 말하면** — 두 확인은 종류가 다릅니다. `"2024-13-45"` 가 날짜인지는 적힌 글자만 보면 그 자리에서 답이 나오지만, `"food"` 가 등록된 카테고리인지는 카테고리 명부를 펼쳐 봐야 압니다. 앞의 것은 값 자체가 틀린 것이고, 뒤의 것은 값은 멀쩡한데 지금 이 프로그램의 형편에 맞지 않는 것입니다. 그래서 앞의 것은 값만 보는 `validators` 가, 뒤의 것은 저장된 상태를 아는 서비스가 맡습니다.
> 다만 이 비유는 명부가 고정된 것이 아니라는 데서 깨집니다 — 카테고리를 하나 등록하면 방금 거절당한 바로 그 값이 곧바로 통과합니다.

| 판단 | 필요한 것 | 어디서 | 예외 |
|---|---|---|---|
| `"2024-13-45"` 는 날짜인가 | 값 하나 | `validators` | `ValidationError` |
| `"food"` 는 등록된 카테고리인가 | **저장된 상태** | 서비스 | `AppError` |

budget_app/services/transactions.py:89-91

```python
    def _require_registered_category(self, name: str, *, hint: str) -> None:
        if not self.cats.exists(name):
            raise AppError(messages.ERR_CATEGORY_NOT_REGISTERED.format(name=name), hint=hint)
```

> **🔎 문법의 출처** — 시그니처 가운데 홀로 선 `*` 는 **키워드 전용 인자** 표시입니다(PEP 3102, 파이썬 3.0). `*` 뒤의 이름은 위치로 넘길 수 없어서 `self._require_registered_category(category, messages.HINT_CATEGORY_ADD)` 는 `TypeError: ... takes 2 positional arguments but 3 were given` 이 되고, 반드시 `hint=...` 라고 써야 합니다. 두 인자가 모두 `str` 이라 순서를 바꿔도 타입 검사에 걸리지 않는데, `*` 한 글자가 그 사고를 문법 차원에서 막습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — `messages.ERR_CATEGORY_NOT_REGISTERED.format(name=name)` 의 `str.format` 은 PEP 3101 이 들여온 포맷 미니 언어입니다. 문자열을 훑어 `{name}` 같은 치환 필드를 찾고, 각 값에 대해 내장 `format(값, 스펙)` → 값의 `__format__` 을 호출한 결과를 이어 붙입니다. 문구는 `services/messages.py:9` 에 두고 값만 나중에 끼우는 이 구조 덕분에 **문장은 messages 에, 값은 서비스에** 남습니다 — f-문자열로 썼다면 문구와 값이 한 줄에 붙어 이 분리가 불가능합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

**`hint` 를 인자로 받는 것**이 작은 설계입니다. 같은 오류라도 문맥에 따라 안내가 달라야 합니다.

- `add` 에서는 `HINT_CATEGORY_ADD_OR_LIST`("등록하거나 목록을 확인하세요")
- `update` 에서는 `HINT_CATEGORY_ADD`("등록하세요")

`update` 를 하는 사용자는 이미 목록을 봤을 가능성이 높기 때문입니다.

### 2.2 `update` — 조회 → 도메인 변환 → 저장

budget_app/services/transactions.py:52-70

```python
    @log_call
    def update(self, tx_id: str, patch: TransactionPatch) -> Transaction:
        """부분 수정 — 도메인이 새 객체를 만들고, 저장소는 그것을 쓰기만 한다.

        이전에는 저장소가 ``to_dict → dict.update → from_dict`` 로 변경을 해석했다.
        지금 순서는 조회 → ``with_patch`` (도메인) → ``replace`` (저장)다.
        """
        if patch.category is not None:
            self._require_registered_category(patch.category, hint=messages.HINT_CATEGORY_ADD)

        current = self.txs.get(tx_id)
        if current is None:
            raise AppError(
                messages.ERR_TX_NOT_FOUND.format(tx_id=tx_id), hint=messages.HINT_LIST_ID
            )

        updated = current.with_patch(patch)
        self.txs.replace(tx_id, updated)
        return updated
```

**세 단계가 각각 다른 계층의 일입니다.**

```
1) self.txs.get(tx_id)          저장소  — 현재 상태 조회
2) current.with_patch(patch)    도메인  — 변경 적용 + 불변식 재검증
3) self.txs.replace(tx_id, ...) 저장소  — 완성품 저장
```

리팩터 전에는 1~3이 전부 `repository.update` 안에 있었습니다. 저장소가 도메인 변환을 수행한 것입니다([07 §5.2](./07-repository.md)).

**검사 순서도 의도적입니다.** 카테고리 검사가 거래 조회보다 **먼저** 옵니다. 없는 카테고리로 없는 거래를 수정하려 하면 "카테고리가 등록되지 않았습니다"가 먼저 나오는데, 사용자가 고쳐야 할 것이 둘 다이므로 어느 쪽을 먼저 알려도 되지만 **저장소 접근을 줄이는 쪽**이 낫습니다.

### 2.3 `delete` — 저장소의 bool 을 오류로 승격

budget_app/services/transactions.py:72-76

```python
    @log_call
    def delete(self, tx_id: str) -> None:
        if not self.txs.delete(tx_id):
            raise AppError(
                messages.ERR_TX_NOT_FOUND.format(tx_id=tx_id), hint=messages.HINT_LIST_ID
```

**저장소는 "없었다"는 사실만 보고, 서비스가 그것을 "오류"로 판정합니다.** 이 분리가 유용한 이유는 "id 가 없다"가 항상 오류인 것은 아니기 때문입니다 — 멱등 삭제(같은 삭제를 몇 번 반복해도 결과가 같고, 이미 없으면 그냥 넘어가는 방식)를 추가한다면 저장소는 그대로 두고 서비스만 바꾸면 됩니다.

### 2.4 `stream_sorted` — 정렬이 필요한 조회

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

> **🔎 문법의 출처** — 세 줄에 세 시대의 문법이 있습니다. `[tx for tx in ... if ...]` 는 리스트 컴프리헨션(PEP 202, 파이썬 2.0)으로, `items = []` 뒤 `for`/`if`/`append` 세 줄을 한 식으로 접은 것입니다. `lambda t: (...)` 는 이름 없는 함수식이고, `yield from items`(PEP 380, 파이썬 3.3)는 이 자리에서는 `for v in items: yield v` 와 같습니다(PEP 380 이 더한 `send`·예외 위임 기능은 여기서 쓰이지 않습니다). → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — 함수 몸통에 `yield` 가 있으므로 `stream_sorted(...)` 를 **호출해도 한 줄도 실행되지 않습니다.** 파이썬은 컴파일 시점에 이 함수를 제너레이터 함수로 표시하고, 호출은 제너레이터 객체만 돌려줍니다. 정렬은 호출자가 첫 항목을 꺼내는 순간(`for` 문의 첫 `__next__`)에야 시작됩니다. 그래서 "정렬 때문에 전체를 읽는다"는 비용도 실제로 결과를 소비할 때 발생합니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — `items.sort(...)` 는 `sorted(items)` 와 달리 **새 리스트를 만들지 않고 제자리에서** 정렬하고 `None` 을 돌려줍니다. 방금 컴프리헨션으로 만든 리스트라 아무도 공유하지 않으므로 제자리 정렬이 안전하고 사본 하나를 아낍니다. `key` 함수는 비교할 때마다가 아니라 **항목당 정확히 한 번** 호출되어 결과가 따로 보관됩니다. 그리고 `(t.date, t.id)` 튜플 비교는 날짜가 같을 때 `t.id` 까지 내려가므로 `TransactionId` 에 순서 비교가 필요합니다 — 그래서 `domain/tx_id.py:51-52` 가 `@functools.total_ordering` + `@dataclass(frozen=True)` 로 `__lt__` 하나에서 나머지 비교 연산을 자동 생성해 둡니다. → [12 §1-B](./12-syntax-and-stdlib.md)

**정렬은 본질적으로 전체를 봐야 하는 연산**입니다. 스트리밍의 예외이며, docstring 이 그 사실과 완화책(필터 통과분만 모음)을 명시합니다.

`list` 와 `search` 가 이 하나를 공유합니다 — `list` 는 `flt=None`, `search` 는 조건을 넘깁니다. 정렬 규칙(최신순)이 한 곳에만 있습니다.

---

## 3. `BudgetService` — 단일 패스 집계

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

> **⚙️ 내부 동작** — `per_category[tx.category] = per_category.get(tx.category, 0) + tx.amount` 는 "없으면 0부터"를 한 줄로 쓰는 표준 누적 관용구입니다. `dict.get(key, default)` 는 `dict[key]` 와 달리 키가 없어도 `KeyError` 를 던지지 않고 두 번째 인자를 돌려줍니다(내부적으로는 같은 해시 탐색을 하되 실패를 예외 대신 기본값으로 바꿉니다). 표준 라이브러리에는 같은 일을 하는 `collections.defaultdict(int)` 와 `collections.Counter` 가 있지만 **이 소스는 둘 다 쓰지 않습니다.** `defaultdict` 는 나중에 오타 난 키를 읽어도 조용히 0 을 만들어 버리고, `Counter` 는 "개수 세기"라는 이름이 "금액 합계"라는 실제 의미와 어긋납니다. 평범한 `dict` + `get` 이 의존성도 늘리지 않고 의미도 정확합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — `sorted(per_category.items(), key=lambda kv: kv[1], reverse=True)` 에서 `dict.items()` 는 리스트가 아니라 **뷰 객체**(`dict_items`)로, 원본 dict 를 그대로 들여다봅니다. `sorted` 는 그것을 리스트로 받아 **Timsort** 로 정렬하는데 이 정렬은 **안정(stable)** 입니다 — 키가 같은 항목의 원래 순서가 보존되고, `reverse=True` 여도 보존됩니다(결과를 뒤집는 것이 아니라 비교 방향만 뒤집기 때문입니다). 실제로 확인하면:
>
>     >>> sorted([('a',5),('b',5),('c',9)], key=lambda kv: kv[1], reverse=True)
>     [('c', 9), ('a', 5), ('b', 5)]
>     >>> sorted([('b',5),('a',5),('c',9)], key=lambda kv: kv[1], reverse=True)
>     [('c', 9), ('b', 5), ('a', 5)]
>
> 지출 금액이 같은 카테고리 둘의 순서는 곧 **dict 의 삽입 순서**, 즉 그 달에 먼저 등장한 거래의 카테고리 순서가 됩니다(파이썬 3.7부터 dict 는 삽입 순서를 유지합니다). 무작위가 아니라 "먼저 나온 쪽이 앞"이라는 뜻이고, 같은 파일을 두 번 요약하면 결과가 같습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

### 3.1 단일 패스의 의미

> **💡 쉽게 말하면** — 장을 보면서 살 것 목록을 네 갈래로 나눠 따로 확인하면 매장을 네 바퀴 돌게 됩니다. 한 바퀴 도는 동안 집는 물건마다 네 장의 기록지에서 해당하는 칸을 **동시에** 적어 두면 한 바퀴로 끝납니다. 물건 하나가 기록지 한 장에만 들어가는 것이 아니라 여러 장을 한꺼번에 건드립니다 — 지출 거래 한 건은 "거래가 있었다"와 "지출 합계"와 "그 카테고리의 지출"을 함께 갱신합니다. 단일 패스(파일을 한 번만 훑는 것)란 그 한 바퀴입니다.
> 다만 이 비유는 순위 매기기에서 깨집니다 — 합계는 도는 동안 쌓이지만 "지출이 가장 큰 카테고리는 무엇인가"는 한 바퀴를 다 돈 뒤에야 정해지므로, `top_expense` 의 정렬만은 루프 밖에 있습니다.

파일을 **한 번만** 순회하며 네 가지를 동시에 누적합니다.

```
for tx in stream():        ← 파일 1회 순회
    ├─ has_data            (이 달에 거래가 있는가)
    ├─ income_total        (수입 합계)
    ├─ expense_total       (지출 합계)
    └─ per_category[...]   (카테고리별 지출)
```

각각 따로 구했다면 파일을 4번 읽어야 합니다.

### 3.2 파생값을 계산하지 않습니다

`balance`, `usage_pct`, `over_budget` 이 이 함수에 없습니다. 전부 `MonthlySummary` 의 `@property` 입니다([05 §5.7](./05-config-and-models.md)).

**리팩터 전후 대조:**

```python
# 리팩터 전 — 서비스가 파생값까지 계산해 dict 에 담음
        result = {
            "month": target, "income": income_total, "expense": expense_total,
            "balance": income_total - expense_total,       # ← 파생값
            "has_data": has_data, "top_expense": top_expense,
            "budget": None, "usage_pct": None, "over_budget": None,
        }
        budget = self.budgets.get(target)
        if budget is not None:
            result["budget"] = budget
            if budget.amount > 0:
                pct = (expense_total / budget.amount) * 100
                result["usage_pct"] = round(pct, 1)          # ← 파생값
                result["over_budget"] = expense_total > budget.amount   # ← 파생값
        return result

# 리팩터 후 — 원자료만 담고 넘김
        return MonthlySummary(
            month=target, income=income_total, expense=expense_total,
            top_expense=top_expense, has_data=has_data,
            budget=self.budgets.get(target),
        )
```

파생값을 모델로 옮겨서 얻은 것이 셋입니다.

1. **일관성** — `balance` 를 저장하면 `income` 과 어긋날 수 있지만 property 는 항상 맞습니다.
2. **오타 안전** — `result["usage_pct"]` 는 런타임 `KeyError`, `summary.usage_pct` 는 IDE 가 잡습니다.
3. **규칙의 소속** — "예산이 0이면 사용률이 무의미하다"는 도메인 규칙이 화면 코드가 아니라 모델에 있습니다.

### 3.3 `top_n` 방어

`[: max(0, top_n)]` 의 `max(0, ...)` 가 없으면 `--top -3` 이 `[:-3]`(뒤 3개 제외)이라는 전혀 다른 의미가 됩니다.

> **🔎 문법의 출처** — `seq[a:b]` 슬라이스는 파이썬 1.x 부터 있던 문법으로, `seq.__getitem__(slice(a, b))` 로 풀립니다. 인덱스 하나를 꺼내는 `seq[i]` 와 규칙이 정반대라는 점이 핵심입니다 — **슬라이스는 범위를 벗어나도 예외를 내지 않고 조용히 잘립니다.**
>
>     >>> [1,2,3][:99]     # 3개뿐인데 99개를 달라고 해도
>     [1, 2, 3]
>     >>> [1,2,3][:0]
>     []
>     >>> [1,2,3][3]       # 인덱스는 다르다
>     IndexError: list index out of range
>
> 그래서 `--top 1000` 은 방어가 없어도 안전합니다. 위험한 것은 오직 **음수**인데, 음수가 IndexError 가 아니라 "끝에서부터"라는 **정상적이지만 다른 의미**로 해석되기 때문입니다. `max(0, top_n)` 는 그 한 가지 경우만 0 으로 눌러 빈 튜플이 나오게 합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

> **개선안(현재 코드에 없음)**: 이 방어는 사실 CLI 의 입력 정제 책임에 가깝습니다. argparse 에 `type=` 커스텀 함수를 두어 음수를 파싱 단계에서 거부하는 편이 계층상 더 정확합니다. 지금은 서비스가 방어하되, 그 사실을 알고 있는 것이 중요합니다.

---

## 4. `CategoryService` — 사용 중 카테고리 보호

budget_app/services/categories.py:38-73

```python
    def remove(self, name: str, replace_with: str | None = None) -> int:
        """카테고리 삭제. 사용 중이라면:
        ...
        """
        target = validators.parse_category(name)
        replacement = validators.parse_category(replace_with) if replace_with else None

        if not self.cats.exists(target):
            raise AppError(
                messages.ERR_CATEGORY_NOT_EXIST.format(name=target),
                hint=messages.HINT_CATEGORY_LIST,
            )
        reassigned = 0
        if self.txs.category_in_use(target):
            reassigned = self._reassign_before_remove(target, replacement)
        self.cats.remove(target)
        return reassigned
```

> **🔎 문법의 출처** — `validators.parse_category(replace_with) if replace_with else None` 은 **조건 표현식**(PEP 308, 파이썬 2.5)입니다. `if` 문과 달리 값을 낳는 *식*이라 대입 오른쪽에 바로 놓을 수 있습니다. 조건이 `replace_with is not None` 이 아니라 그냥 `replace_with` 인 것도 의도적입니다 — 빈 문자열 `""` 도 거짓이므로 `--replace-with ""` 처럼 빈 값이 와도 `None` 으로 떨어집니다. 파이썬은 `bool` 이 아닌 값에 `__bool__`(없으면 `__len__`)을 물어 참·거짓을 정하고, `str` 은 길이가 0일 때 거짓입니다. → [12 §1-A](./12-syntax-and-stdlib.md)

### 4.1 참조 무결성(referential integrity) 보호

> **💡 쉽게 말하면** — 학교에서 반 하나를 없앤다고 해 봅시다. 그 반에 아무도 없으면 그냥 없애면 됩니다. 학생이 남아 있다면 먼저 어느 반으로 옮길지를 정해야 하고, 정하지 않은 채 반만 없애면 학생들은 소속 없는 이름으로 명단에 남습니다. 카테고리와 거래의 관계가 이와 같아서, 쓰이고 있는 카테고리는 옮겨 갈 곳을 정해 주기 전에는 지워지지 않습니다.
> 다만 이 비유는 옮길 반을 정하는 쪽이 학교가 아니라는 데서 깨집니다 — 프로그램은 대신 골라 주지 않고, `--replace-with` 가 없으면 삭제 자체를 거절합니다.

이 서비스가 지키는 규칙은 **"거래가 참조하는 카테고리는 사라지면 안 된다"**(참조 무결성 — 누군가 가리키고 있는 대상을 함부로 없애지 않는 것) 입니다. 관계형 DB 의 외래 키 제약을 코드로 구현한 것과 같습니다.

```
사용 중이 아님        → 그냥 삭제
사용 중 + 대체 지정   → 일괄 재지정 후 삭제
사용 중 + 대체 없음   → AppError 로 차단  ("카테고리 'food' 는 거래에서 사용 중입니다")
```

### 4.2 검사 순서가 곧 정책

`_reassign_before_remove` 의 세 검사 순서를 보세요.

| 순서 | 검사 | 왜 이 순서인가 |
|---|---|---|
| 1 | `replace_with` 가 있는가 | 없으면 나머지를 볼 필요가 없음 |
| 2 | 자기 자신인가 | **파일을 읽지 않고** 판단 가능 |
| 3 | 등록된 카테고리인가 | 파일을 읽어야 함 |

**싼 검사부터 하는 것**이 원칙입니다. 2번(문자열 비교)이 3번(파일 순회)보다 앞에 있는 이유입니다.

### 4.3 메서드를 나눈 이유

`remove` 본문이 "존재 확인 → 사용 중이면 재지정 → 삭제" 세 줄로 읽힙니다. 재지정 조건 검사 3개를 인라인으로 두면 이 흐름이 묻힙니다. **공개 메서드는 시나리오를, private 메서드는 세부 규칙을** 담당하는 분업입니다.

---

## 5. `ImportExportService` — 세 가지 정책

### 5.1 이 클래스가 아는 것

budget_app/services/importexport.py:61-69

```python
class ImportExportService:
    """CSV 가져오기/내보내기 정책.

    스키마는 ``csv_io`` 가 안다. 이 클래스가 아는 것은 **정책** 셋이다.

    1. 실패 정책   — 부분 성공(기본) vs 원자적 전수 롤백(``--atomic``)
    2. 중복 정책   — 이미 있는 id 를 만나면 건너뛸까/새로 발급할까/막을까
    3. 부수 효과   — 처음 보는 카테고리는 자동 등록한다
    """
```

**"스키마는 csv_io 가 안다"** 는 첫 문장이 경계를 선언합니다(스키마 — 파일에 어떤 이름의 칸이 어떤 순서로 있는가). 이 클래스에는 `"date"`, `"amount"` 같은 컬럼명이 **한 번도 등장하지 않습니다.**

### 5.2 내보내기 — 제너레이터를 그대로 넘김

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

**두 줄입니다.** `(tx for tx in ...)` 는 제너레이터 식이라 필터 통과분이 메모리에 모이지 않습니다.

> **💡 쉽게 말하면** — 책 한 권을 통째로 복사해 가방에 넣어 오는 대신, 열람실에서 한 장 읽고 한 장 옮겨 적기를 되풀이하는 것입니다. 가방 안에는 언제나 한 장뿐이라 책이 열 배 두꺼워져도 가방 무게는 그대로입니다. 거래가 10만 건이어도 메모리에 올라와 있는 거래가 늘 한 건인 것이 이 이유입니다.
> 다만 이 비유는 한 번 넘긴 장으로 되돌아갈 수 없다는 데서 깨집니다 — 제너레이터는 앞으로만 가므로, 같은 내용을 다시 보려면 파일을 처음부터 새로 읽어야 합니다.

> **🔎 문법의 출처** — `(tx for tx in ... if ...)` 는 **제너레이터 표현식**(PEP 289, 파이썬 2.4)입니다. 대괄호를 쓴 리스트 컴프리헨션(`[tx for tx in ...]`)과 글자 하나 차이지만 결과가 다릅니다 — 대괄호는 **리스트를 다 만들어** 돌려주고, 소괄호는 **아직 아무것도 만들지 않은 제너레이터 객체**를 돌려줍니다. 파이썬은 이것을 익명의 제너레이터 함수로 컴파일하며, 첫 `for ... in` 의 대상(`self.txs.stream()`)만 그 자리에서 평가하고 나머지는 소비 시점으로 미룹니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — 그 게으름이 계층을 넘어 유지되는 경로가 이 함수의 요점입니다. `csv_io.write_transactions`(`storage/csv_io.py:131-148`)의 인자 타입은 `Iterable[Transaction]` 이고 본문은 `for tx in txs:` 로 **한 건 꺼내 한 줄 쓰고 다시 꺼냅니다.** 그래서 파일 → `stream()` → 제너레이터 식 필터 → `csv.DictWriter.writerow` 가 한 줄짜리 파이프라인으로 이어지고, 거래가 10만 건이어도 메모리에 있는 `Transaction` 은 항상 한 건입니다. 만약 여기서 `rows = [tx for tx in ...]` 라고 대괄호를 썼다면 `write_transactions` 코드는 한 글자도 바뀌지 않은 채 **전 건이 리스트로 메모리에 올라갑니다** — 스트리밍이 깨지는 지점이 호출부 괄호 한 쌍이라는 뜻입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

`include_id=True` 가 기본인 이유가 이 리팩터의 출발점이었습니다(왕복 안전성 — 내보낸 파일을 그대로 다시 가져와도 원래대로 돌아오는 성질) — id 컬럼이 없으면 내보낸 CSV 를 다시 넣을 때 모든 행이 새 id 를 받아 같은 거래가 두 벌이 됩니다. 자세한 버그 재현은 [07 §8.2](./07-repository.md)에 있습니다.

### 5.3 가져오기 — 준비와 커밋

> **💡 쉽게 말하면** — 장부에 옮겨 적기 전에 연습장에 전부 계산해 보는 것과 같습니다. 장부는 연습장을 다 채운 뒤에야 펴고, 그전까지는 한 글자도 쓰지 않습니다. 준비 단계가 연습장이고 커밋 단계가 장부입니다. 연습장에서 어긋난 줄을 만났을 때 그 줄만 빼고 나머지를 옮길지, 아예 장부를 펴지 않고 그만둘지는 `--atomic` 이 정합니다.
> 다만 이 비유는 두 군데서 깨집니다 — 하나는 연습장이 무한하지 않다는 것으로, 준비 단계의 `_Batch` 는 메모리이므로 가져오는 CSV 가 클수록 커밋할 때까지 그만큼을 들고 있어야 합니다. 다른 하나는 "어긋나면 그만둔다"가 기본 동작이 아니라는 것으로, 아래 코드의 기본값이 `atomic: bool = False` 이고 그 모드에서는 어긋난 줄을 건너뛴 채 나머지가 그대로 장부에 옮겨집니다.

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

> **🔎 문법의 출처** — `in_path` 다음에 홀로 선 `*` 가 `atomic` 과 `on_duplicate` 를 **키워드 전용**으로 만듭니다(PEP 3102). 그래서 호출부는 반드시 `import_csv(path, atomic=True, on_duplicate="new-id")` 라고 씁니다. 여기서 이 강제가 특히 값어치를 하는 이유는 `atomic` 이 **불리언 인자**이기 때문입니다 — `import_csv(path, True, "new-id")` 를 읽는 사람은 그 `True` 가 무엇의 스위치인지 알 수 없고("boolean trap"), 나중에 두 인자의 순서가 바뀌어도 조용히 컴파일됩니다. `*` 는 그 두 위험을 한꺼번에 없애면서, 덤으로 **인자 순서를 나중에 바꿔도 기존 호출부가 깨지지 않게** 만듭니다. 같은 패턴이 `export_csv(..., *, include_id=True)` 와 `_prepare(..., *, atomic, on_duplicate)` 에도 그대로 있습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

**본문이 두 줄**입니다. 리팩터 전 이 메서드는 80줄이었고, 파일 열기·헤더 검증·행 검증·오류 누적·두 실패 정책·카테고리 자동 등록·ID 발급·커밋 8가지를 담고 있었습니다.

이름이 곧 구조 설명이 됩니다 — **준비하고, 커밋한다.**

### 5.4 준비 단계

budget_app/services/importexport.py:104-131

```python
    def _prepare(self, in_path: Path, *, atomic: bool, on_duplicate: str) -> _Batch:
        batch = _Batch()
        allocator = self.txs.id_allocator()
        known_categories = self.cats.name_set()

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
                batch.note_error(lineno, exc)
                continue

            tx_id = self._resolve_id(parsed.tx_id, lineno, allocator, on_duplicate, batch)
            if tx_id is None:
                continue  # 중복 — 건너뛰기 정책

            batch.transactions.append(parsed.to_transaction(tx_id))
            if parsed.category not in known_categories:
                known_categories.add(parsed.category)
                batch.new_categories.append(parsed.category)

        return batch
```

> **🔎 문법의 출처** — `except (ValidationError, KeyError) as exc:` 의 괄호는 **여러 예외 타입을 한 튜플로** 잡는 표기입니다. 그리고 `as exc` 로 묶인 이름은 `except` 블록이 끝나는 순간 파이썬이 **자동으로 `del` 합니다**(PEP 3110). 예외 객체가 트레이스백을 통해 프레임을 참조해 순환 참조가 생기는 것을 막기 위해서인데, 그 결과 `except` 블록 밖에서 `exc` 를 쓰면 `UnboundLocalError`(`NameError` 의 하위 클래스)가 납니다 — 이 코드가 `exc` 를 블록 안에서 `raise ... from exc` 와 `note_error(lineno, exc)` 로 다 소비하는 것이 우연이 아닙니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — `raise AppError(...) from exc` 의 `from` 은 **예외 연쇄**(PEP 3134, 파이썬 3.0)입니다. 파이썬은 새 예외의 `__cause__` 에 `exc` 를 넣고 `__suppress_context__` 를 `True` 로 세워, 트레이스백을 "The above exception was the direct cause of the following exception"으로 출력합니다. `from` 을 빼도 `__context__` 에 자동으로 원인이 들어가지만 그것은 "처리 중에 또 터졌다"는 뉘앙스이고, `from` 은 "번역했다"는 **의도적 승격**을 남깁니다. 실행으로 확인하면 새 예외의 `__cause__` 가 원래 `ValidationError` 객체 그대로이고 `__suppress_context__` 가 `True` 입니다.
>
> 이 자리에서의 뜻: **`atomic` 일 때만** 값 오류(`ValidationError`)가 상황 오류(`AppError`)로 승격되어 `_prepare` 밖으로 빠져나갑니다. 그러면 `import_csv` 의 둘째 줄 `self._commit(...)` 은 **실행 자체가 되지 않고**, 파일은 손대지 않은 상태로 남습니다. 예외가 곧 "여기서 멈춘다"는 정책의 실행 수단입니다. `atomic` 이 아니면 같은 예외를 `batch.note_error` 로 기록하고 `continue` 로 다음 행을 봅니다 — 한 줄의 `if` 가 두 실패 정책을 가릅니다. → [12 §1-C](./12-syntax-and-stdlib.md)

**루프 시작 전에 파일을 두 번 훑습니다** — `id_allocator()`(거래 파일)와 `name_set()`(카테고리 파일). 이 두 스냅숏(그 시점의 목록을 통째로 떠 둔 사본) 덕분에 **행마다 파일을 다시 읽지 않습니다.**

```
[리팩터 전]                        [리팩터 후]
행마다 cats.exists()  → M회 스캔    시작 시 name_set()   → 1회 스캔
커밋 시 cats.add() 반복 → M회 스캔  커밋 시 add_many()   → 1회 스캔
```

**`known_categories` 와 `new_categories` 를 나란히 쓰는 이유**는 자료구조의 성질이 다르기 때문입니다.

| 변수 | 타입 | 역할 |
|---|---|---|
| `known_categories` | `set` | 빠른 소속 검사 (`in`) |
| `batch.new_categories` | `list` | **등록 순서 유지** |

> **⚙️ 내부 동작** — `parsed.category not in known_categories` 의 비용이 이 표의 전부입니다. `set` 은 해시 테이블이라 `in` 이 **평균 O(1)** 입니다 — 파이썬은 `hash(문자열)` 로 버킷을 바로 찾아가고, 후보와 `==` 를 한두 번 해 봅니다. 반면 `list` 에 대한 `in` 은 앞에서부터 하나씩 `==` 를 해 보는 **O(n)** 입니다. CSV 가 N 행이고 카테고리가 M 개일 때, `list` 였다면 N×M 번의 문자열 비교가 되지만 `set` 이면 N 번입니다. `set` 을 만든 `storage/repositories.py:240-242` 의 `{c.name for c in self.stream()}` 도 집합 컴프리헨션 한 줄이며, 여기 들어가는 값은 `str` 이라 이미 불변·해시 가능합니다(같은 이유로 `IdAllocator._taken` 은 `TransactionId` 의 집합인데, 그것이 `@dataclass(frozen=True)` 인 덕분에 파이썬이 `__hash__` 를 자동으로 만들어 줍니다).
>
> 반대로 `new_categories` 가 `list` 인 이유도 같은 성질의 뒷면입니다. `set` 은 **순서를 보관하지 않으므로** 그것으로 커밋하면 카테고리 파일에 쓰이는 줄 순서가 실행마다 달라질 수 있습니다. "빠른 조회"와 "안정된 출력 순서"는 한 자료구조가 동시에 주지 않아서 둘을 나란히 씁니다. → [12 §1-B](./12-syntax-and-stdlib.md)

### 5.5 중복 정책 — `_resolve_id`

budget_app/services/importexport.py:133-140

```python
    def _resolve_id(
        self,
        csv_id: TransactionId | None,
        lineno: int,
        allocator: IdAllocator,
        on_duplicate: str,
        batch: _Batch,
    ) -> TransactionId | None:
```

**결정 트리:**

```
csv_id 가 없다(빈 셀 / 컬럼 없음)
    └─▶ allocator.next()                     새 id 발급

csv_id 가 있고 아직 안 쓰였다
    └─▶ reserve() 후 그대로 사용              원본 id 복원 (왕복 무손실)

csv_id 가 있고 이미 쓰였다  ── on_duplicate ──┬─ "new-id" → allocator.next()
                                              ├─ "error"  → AppError
                                              └─ "skip"   → None (이 행 버림)
```

**`allocator` 하나가 두 종류의 중복을 동시에 잡습니다.**

| 중복 종류 | 어떻게 잡히나 |
|---|---|
| 파일 간 (이미 저장된 거래) | `id_allocator()` 가 파일에서 읽은 `taken` |
| 파일 내 (같은 CSV 에 같은 id 두 번) | 첫 번째 행에서 `reserve()` 한 것 |

두 경우를 따로 처리하는 코드가 필요 없다는 것이 이 설계의 장점입니다.

**`None` 반환이 "이 행은 저장하지 않는다"** 를 뜻한다는 계약이 반환 타입 `TransactionId | None` 과 docstring(`importexport.py:141`)에 명시되어 있습니다. 호출부(`importexport.py:123`)가 `if tx_id is None:` 으로 그 계약을 받습니다.

> **⚙️ 내부 동작** — 여기서 `== None` 이 아니라 `is None` 인 것이 관례가 아니라 정확성입니다. `is` 는 두 이름이 **같은 객체를 가리키는가**(CPython 에서는 주소 비교)를 묻고, `None` 은 인터프리터 전체에 **딱 하나만 존재하는 싱글턴**이라 이 비교가 항상 옳습니다. `==` 는 `__eq__` 를 부르므로 클래스가 그것을 재정의하면 `None` 과 같다고 우길 수 있습니다. `TransactionId` 는 dataclass 라 실제로 `__eq__` 가 자동 생성되어 있으므로, `is` 를 쓰는 편이 그 경로를 아예 지나지 않습니다. → [12 §1-B](./12-syntax-and-stdlib.md)

### 5.6 커밋 단계 — 모드에 따라 갈린다

budget_app/services/importexport.py:168-177

```python
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

**여기서 처음 파일이 바뀝니다.** 준비 단계는 파일을 읽기만 했습니다.

`tuple(batch.errors)` 로 리스트를 튜플로 굳히는 것도 의도적입니다 — `ImportReport` 가 frozen dataclass 라 담기는 값도 불변인 편이 일관됩니다([05 §5.7](./05-config-and-models.md)). `frozen=True` 는 필드 재대입만 막고 담긴 리스트의 내용 변경은 못 막으므로, 굳히는 일은 이렇게 넣는 쪽이 해야 합니다.

> **⚙️ 내부 동작** — `tuple(어떤_이터러블)` 은 인자를 처음부터 끝까지 순회해 **새 튜플을 만듭니다**(리스트를 튜플로 "바꾸는" 것이 아니라 복사입니다). 그래서 이 줄 이후에 `batch.errors` 에 무엇을 더 넣어도 `ImportReport` 안의 튜플은 변하지 않습니다. `ImportReport` 의 기본값이 `errors: tuple[RejectedRow, ...] = ()` 인 것도 같은 맥락입니다 — 빈 튜플은 불변이라 dataclass 가 기본값으로 받아 주지만, 빈 리스트 `[]` 였다면 아래 §5.7 이 보여 주는 `ValueError` 가 납니다. → [12 §1-B](./12-syntax-and-stdlib.md)


**원자 모드는 `UnitOfWork` 로 두 파일을 한 단위로 커밋합니다.** `UnitOfWork` 는 작업 단위, 즉 여러 파일에 걸친 변경을 하나로 묶어 되도록 전부 반영하거나 전부 취소하게 해 주는 장치입니다(되도록인 이유는 §5.6 에 있습니다).

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

> **🔎 문법의 출처** — `with UnitOfWork() as uow:` 는 PEP 343(파이썬 2.5)의 `with` 문입니다. 파이썬은 이것을 대략 이렇게 풉니다.
>
>     :::python
>     _mgr = UnitOfWork()
>     uow = _mgr.__enter__()
>     try:
>         ...본문...
>     except:
>         if not _mgr.__exit__(*sys.exc_info()):
>             raise
>     else:
>         _mgr.__exit__(None, None, None)
>
> 그래서 `as uow` 에 담기는 것은 `UnitOfWork()` 인스턴스 자체가 아니라 **`__enter__` 의 반환값**입니다(`storage/unit_of_work.py:169-170` 이 `return self` 라서 여기서는 결과가 같습니다). `if fresh_categories:` 로 감싼 `stage` 는 준비만 하고, 실제 반영은 블록을 정상적으로 빠져나갈 때 `__exit__` 이 부르는 `commit()` 에서 일어납니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — `__exit__`(`storage/unit_of_work.py:172-181`)의 반환 타입이 `-> None` 인 것이 이 블록의 안전장치입니다. 파이썬은 `__exit__` 의 **반환값이 참일 때만 예외를 삼킵니다.** `None` 은 거짓이므로, `stage` 도중에 `OSError` 가 나면 `__exit__` 이 `rollback()` 으로 `.tmp` 를 치운 뒤 **예외를 그대로 다시 올립니다**. 뒷정리는 하되 실패를 감추지는 않는다는 뜻이고, 호출자인 `_commit_atomic` 의 `return len(...)` 은 실행되지 않으므로 CLI 가 성공으로 착각할 수 없습니다. `try/finally` 로도 뒷정리는 되지만, "정상 종료면 커밋 / 예외면 롤백"이라는 **분기**는 `__exit__` 이 받는 `exc_type` 인자가 있어야 쓸 수 있습니다. → [12 §1-C](./12-syntax-and-stdlib.md)

이전에는 카테고리를 먼저 쓰고 거래를 나중에 써서, 그 사이에 죽으면 **쓰이지 않는 카테고리만 남았습니다**. `UnitOfWork` 는 두 파일의 최종 내용을 각각 `.tmp` 로 먼저 쓴 뒤 `os.replace` 두 번을 연달아 실행해, 취약 구간을 "파일 쓰기 2회 사이"에서 "rename 2회 사이"로 줄입니다. 자세한 동작은 [07 §9](./07-repository.md)에 있습니다.

부분 성공 모드는 append O(1) 특성을 지키려고 그대로 뒀습니다 — "가능한 만큼 최대한 넣는다"는 정책이라 그 위험을 감수합니다.

### 5.7 `_Batch` — 준비 단계의 누적 상태

budget_app/services/importexport.py:30-58

```python
@dataclass
class _Batch:
    """가져오기 준비 단계의 누적 상태.

    준비(prepare)와 커밋(commit)을 나누는 것이 원자성의 뼈대다. 파일에 손대기
    전에 모든 행의 판정이 끝나 있어야 "전혀 반영 안 됨"이 가능하다.
    """

    transactions: list[Transaction] = field(default_factory=list)
    new_categories: list[str] = field(default_factory=list)
    skipped: int = 0
    duplicated: int = 0
    errors: list[RejectedRow] = field(default_factory=list)
    duplicates: list[DuplicateRow] = field(default_factory=list)

    def note_error(self, lineno: int, reason: object) -> None:
        """세는 것은 전부, 사유를 남기는 것은 앞의 몇 건만.

        수천 줄짜리 CSV 가 통째로 잘못됐을 때 사유를 전부 모으면 메모리와 화면이
        같이 터진다. 숫자(``skipped``)는 정확하고, 목록은 표본이다.
        """
        self.skipped += 1
        if len(self.errors) < config.MAX_IMPORT_ERRORS:
            self.errors.append(RejectedRow(lineno=lineno, reason=str(reason)))

    def note_duplicate(self, lineno: int, tx_id: TransactionId) -> None:
        self.duplicated += 1
        if len(self.duplicates) < config.MAX_IMPORT_ERRORS:
            self.duplicates.append(DuplicateRow(lineno=lineno, tx_id=tx_id.value))
```

> **🔎 문법의 출처** — `@dataclass`(PEP 557, 파이썬 3.7)는 **클래스 본문의 어노테이션을 읽어 코드를 생성하는 데코레이터**입니다. 위 여섯 줄만 보고 `__init__`, `__repr__`, `__eq__` 의 소스를 문자열로 조립해 `exec` 로 컴파일한 뒤 클래스에 붙입니다. 그래서 `_Batch()` 라고만 써도 여섯 필드가 전부 초기화됩니다. 실제 생성된 시그니처를 보면 이렇습니다.
>
>     >>> import inspect; from budget_app.services.importexport import _Batch
>     >>> inspect.signature(_Batch)
>     (transactions: 'list[Transaction]' = <factory>, new_categories: 'list[str]' = <factory>,
>      skipped: 'int' = 0, duplicated: 'int' = 0, errors: 'list[RejectedRow]' = <factory>,
>      duplicates: 'list[DuplicateRow]' = <factory>) -> None
>
> → [12 §1-B](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — `field(default_factory=list)` 가 여기 있는 이유는 **`= []` 를 쓸 수 없기 때문**입니다. dataclass 는 기본값이 해시 불가능한 객체(리스트·딕셔너리·집합 등)이면 클래스를 만드는 시점에 아예 거부합니다. 관례가 아니라 실행 시 오류입니다.
>
>     >>> @dataclass
>     ... class Bad:
>     ...     items: list = []
>     ValueError: mutable default <class 'list'> for field items is not allowed: use default_factory
>
> 이유는 위 §2.1 의 함수 기본값과 같습니다 — 클래스 본문의 `[]` 는 **클래스가 정의될 때 한 번만** 만들어지므로, 허용됐다면 모든 `_Batch()` 인스턴스가 같은 리스트 하나를 공유해 이번 가져오기의 오류가 다음 가져오기에 섞여 들어갑니다. `default_factory=list` 는 그 리스트를 만드는 **함수 자체**(내장 `list`)를 넘겨 두는 것이고, 생성된 `__init__` 은 인자가 안 왔을 때만 `list()` 를 새로 호출합니다. 그래서 `a, b = _Batch(), _Batch()` 일 때 `a.transactions is b.transactions` 가 `False` 입니다. `skipped: int = 0` 이 `field()` 없이 그냥 `0` 인 것도 같은 규칙의 뒷면입니다 — `int` 는 불변이라 공유돼도 문제가 없습니다. → [12 §1-B](./12-syntax-and-stdlib.md)

**개수는 전부 세고, 메시지만 자릅니다.** `self.skipped += 1` 은 무조건, `errors.append` 는 `MAX_IMPORT_ERRORS`(`services/config.py:16`, 값 5) 미만일 때만. 1만 줄이 전부 깨져도 화면에는 5줄만 나오지만 `skipped=10000` 은 정확합니다.

**`_` 로 시작하는 이름**은 모듈 내부용이라는 관례 표시입니다. 이 클래스는 `ImportExportService` 의 구현 세부이고 밖에서 알 필요가 없습니다. 다만 이것은 PEP 8 의 **관례일 뿐 접근 제어가 아닙니다** — 파이썬은 `_Batch` 를 밖에서 import 하는 것을 막지 않고, 언어가 실제로 하는 일은 `from module import *` 가 `_` 로 시작하는 이름을 건너뛰는 것뿐입니다(이름을 실제로 뭉개는 것은 밑줄 **두 개**로 시작하는 클래스 속성입니다).

---

## 6. 두 정책 축 — 실패와 중복은 독립이다

`--atomic` 과 `--on-duplicate` 는 **다른 것을 다룹니다.** 하나는 "줄이 깨졌을 때"의 방침이고, 다른 하나는 "이미 저장된 거래를 또 만났을 때"의 방침입니다. 서로 묻는 것이 다르므로 한쪽을 정해도 다른 쪽은 정해지지 않습니다.

> **💡 쉽게 말하면** — 가게에 물건이 한 상자 들어왔다고 해 봅시다. 여기에는 서로 다른 두 질문이 있습니다. 하나는 "깨진 물건이 나오면 어떻게 할까"입니다 — 상자를 통째로 돌려보낼지, 깨진 것만 빼고 받을지. 다른 하나는 "이미 창고에 있는 물건이 또 들어오면 어떻게 할까"입니다 — 그냥 두 개로 둘지, 하나만 남길지, 아예 접수를 멈출지. 앞이 `--atomic`, 뒤가 `--on-duplicate` 이고, 어느 쪽을 어떻게 답하든 다른 쪽 답은 여전히 열려 있습니다. 그래서 조합이 여섯 가지입니다.
> 다만 이 비유는 `--on-duplicate error` 한 칸에서 깨집니다 — 중복을 오류로 보겠다고 정하면 그 순간 중복이 실패 쪽 축을 건드려, `--atomic` 이 없어도 전체가 중단됩니다.

| 축 | 다루는 것 | 옵션 |
|---|---|---|
| 실패 정책 | 데이터가 **잘못된** 줄 | `--atomic` |
| 중복 정책 | 이미 **저장된** 거래 | `--on-duplicate` |

조합이 6가지 가능하고, 전부 의미가 있습니다.

| `--atomic` | `--on-duplicate` | 결과 |
|---|---|---|
| 없음 | `skip`(기본) | 깨진 줄 건너뛰고, 중복도 건너뜀 — **가장 관대** |
| 없음 | `new-id` | 깨진 줄만 건너뛰고, 중복은 새 id 로 복제 |
| 없음 | `error` | 깨진 줄은 건너뛰되, 중복을 만나면 전체 중단 |
| 있음 | `skip` | 깨진 줄이 있으면 전체 중단, 중복은 조용히 건너뜀 |
| 있음 | `new-id` | 깨진 줄이 있으면 중단, 중복은 복제 |
| 있음 | `error` | 깨진 줄도 중복도 허용 안 함 — **가장 엄격** |

### 6.1 왜 `skipped` 와 `duplicated` 를 나누나

budget_app/domain/results.py:74-91

```python
@dataclass(frozen=True)
class ImportReport:
    """CSV 가져오기 결과.
    ...
    """
```

**실제 출력 비교:**

```
# 정상 왕복 (내보낸 파일을 다시 넣음)
[완료] mode=부분 성공, imported=0, duplicated=3, skipped=0
  → "0건 저장, 3건 이미 있음" = 정상

# 만약 합쳤다면
[완료] mode=부분 성공, imported=0, skipped=3
  → "0건 저장, 3건 실패" 처럼 읽힘 = 오해
```

프레젠터도 둘을 구분해 보여 줍니다.

budget_app/cli/presenter.py:118-141

```python
def import_problem_lines(report: ImportReport) -> list[str]:
    """건너뛴 줄의 사유 — 결과가 아니라 진단이므로 호출자가 stderr 로 보낸다.
    ...
    """
    lines: list[str] = []
    if report.errors:
        lines.append(messages.MSG_IMPORT_ERROR_HEADER)
        lines.extend(
            messages.FMT_IMPORT_ERROR_ITEM.format(lineno=e.lineno, reason=e.reason)
            for e in report.errors
        )
    if report.duplicates:
        lines.extend(
            messages.FMT_IMPORT_DUPLICATE_ITEM.format(lineno=d.lineno, tx_id=d.tx_id)
            for d in report.duplicates
        )
        lines.append(messages.MSG_IMPORT_DUPLICATE_HINT)
    return lines
```

여기 `lines.extend(... for e in report.errors)` 는 §5.2 와 같은 제너레이터 표현식입니다 — 인자가 하나뿐일 때는 함수 호출 괄호가 제너레이터 식의 괄호를 겸하므로 `extend((...))` 처럼 겹쳐 쓰지 않아도 되고, `list.extend` 가 그것을 순회하며 밀어 넣으므로 중간 리스트가 생기지 않습니다.

중복 목록 뒤에는 **"고칠 필요 없다"는 안내**가 붙습니다.

budget_app/cli/messages.py:98-100

```python
MSG_IMPORT_DUPLICATE_HINT = (
    "[힌트] 중복은 이미 저장된 거래입니다. 다시 넣으려면 `--on-duplicate new-id` 를 쓰세요."
)
```

### 6.2 원자성은 어떻게 보장되는가

```
원자 모드 (--atomic)

  [준비 단계]  파일을 읽기만 함
      │
      ├─ 행 1 검증 OK → batch 에 적재 (메모리)
      ├─ 행 2 검증 OK → batch 에 적재 (메모리)
      ├─ 행 3 검증 실패 → AppError 발생!
      │                      │
      │                      ▼
      │              함수가 예외로 빠져나감
      │              → _commit 이 실행되지 않음
      │              → 파일은 처음 상태 그대로 ✅
      ▼
  [커밋 단계]  도달하지 않음
```

**"파일에 손대기 전에 모든 판정이 끝나 있다"** 가 원자성의 뼈대입니다. 커밋 단계 자체도 `rewrite` → `os.replace` 라 원자적입니다 — 새 내용을 `.tmp` 에 다 쓰고 `fsync` 로 디스크에 밀어 넣은 뒤 이름만 바꾸므로, 어느 시점에 죽어도 원본 아니면 새 파일이지 반쯤 쓰인 파일은 없습니다([07 §3.6](./07-repository.md)).

> **💡 쉽게 말하면** — 벽에 붙은 안내문을 고칠 때, 붙어 있는 종이에 대고 지우고 고쳐 쓰면 그사이 지나가는 사람은 지우다 만 문장을 봅니다. 새 종이에 전문을 다 쓴 뒤 압정을 뽑아 한 번에 갈아 끼우면, 보는 사람은 옛 안내문 아니면 새 안내문만 봅니다. `os.replace` 가 하는 일이 그 갈아 끼우기입니다.
> 다만 이 비유는 같은 벽에서만 통한다는 데서 깨집니다 — 원자성은 같은 파일시스템 안에서만 보장되고, 새 종이의 잉크가 실제로 말랐는지(내용이 디스크에 닿았는지)는 앞서는 `fsync` 가 따로 책임집니다.

> **⚙️ 내부 동작** — `os.replace` 는 POSIX 에서 `rename(2)`, Windows 에서 `MoveFileExW(MOVEFILE_REPLACE_EXISTING)` 로 내려갑니다. 원자성은 **같은 파일시스템 안에서 디렉터리 엔트리를 교체하는 것**에 대해서만 보장되며, 내용이 디스크에 도달했다는 뜻은 아닙니다(그래서 앞에 `fsync` 가 필요합니다). 서비스 계층 코드에는 이 호출이 한 번도 등장하지 않는다는 점도 같이 보세요 — 원자성의 *정책*(언제 전부/전무인가)은 여기가 정하고, 그것을 실현하는 *기법*은 `storage` 안에 있습니다. → [12 §3](./12-syntax-and-stdlib.md)

**부수 효과(본래 하려던 일에 딸려 함께 일어나는 변경)까지 롤백(했던 것을 없던 일로 되돌리기)됩니다.** 카테고리 자동 등록도 커밋 단계에 있으므로, 준비 중 실패하면 카테고리도 남지 않습니다. 실제로 검증한 결과:

```
$ python -m budget_app import --from mixed.csv --atomic --data-dir ./d5
[오류] 원자적 가져오기 실패 — line 3: ...  (반영된 항목 없음)
$ wc -l < ./d5/transactions.jsonl
0                                              ← 거래 0건
$ python -m budget_app category list --data-dir ./d5 | wc -l
5                                              ← 기본 5개 그대로 (salary 안 늘어남)
```

---

## 7. 정리 — 과제 방어용 요약

**Q. 서비스 계층의 책임이 뭔가요?**

**판단**입니다. 파일을 여는 일은 저장소가 하고, 글자를 내는 일은 프레젠터가 합니다. 서비스에 남는 것은 "카테고리가 등록되어 있는가", "사용 중인 카테고리를 지워도 되는가", "중복 id 를 어떻게 처리할까" 같은 정책 결정뿐입니다. 이 주장은 `budget_app/services/` 전체에 `open(` 이 `__init__.py:4` 의 docstring 한 줄 외에 없고 `print(` 는 0건이라는 것으로 검증됩니다.

**Q. import CSV 에 일부 깨진 행이 섞이면 어떻게 처리하나요?**

**두 축**으로 답합니다. 데이터가 잘못된 줄은 `--atomic` 이 없으면 그 줄만 건너뛰고(`skipped`), 있으면 첫 오류에서 전체를 중단합니다. 이미 저장된 거래(중복 id)는 `--on-duplicate` 로 정하며 기본은 건너뛰기(`duplicated`)입니다. **두 숫자를 나눠 보고하는 이유**는 사용자가 해야 할 일이 정반대이기 때문입니다 — `skipped` 는 CSV 를 고쳐야 하고 `duplicated` 는 아무것도 안 해도 됩니다.

**Q. 원자적 가져오기(`--atomic`)를 어떻게 구현했나요?**

준비와 커밋을 나눴습니다. 준비 단계는 파일을 읽기만 하고 모든 행을 검증·판정해 메모리(`_Batch`)에 모읍니다. 한 행이라도 실패하면 그 자리에서 예외를 던져 커밋 단계에 **도달하지 않습니다**. 커밋 자체도 `os.replace` 라 원자적입니다. 카테고리 자동 등록도 커밋 단계에 있어 부수 효과까지 함께 롤백됩니다.

**Q. export 한 파일을 다시 import 하면 어떻게 되나요?**

중복이 생기지 않습니다. export 가 `id` 컬럼을 포함하고 import 가 그것을 인식해 이미 있는 id 는 건너뛰기 때문입니다. 리팩터 전에는 CSV 에 id 가 없어서 같은 거래가 새 id 를 받아 복제됐습니다.

**Q. 성능상 신경 쓴 부분이 있나요?**

배치 작업에서 파일 재스캔을 없앴습니다. 가져오기는 시작 시 `id_allocator()` 와 `name_set()` 으로 스냅숏을 한 번씩만 만들고, 커밋 시 `add_many()` / `append_many()` 로 한 번에 씁니다. 리팩터 전에는 행마다 `cats.exists()` 를, 커밋 시 카테고리마다 `cats.add()` 를 불러 파일을 여러 번 훑었습니다. 요약도 단일 패스로 네 값을 동시에 누적합니다.

---

**다음 문서**: [09. CLI 계층](./09-cli.md) — argparse, 대화형 입력, 프레젠터, 출력 채널.
