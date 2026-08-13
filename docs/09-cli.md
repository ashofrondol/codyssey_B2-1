# 09. CLI 계층 — cli/ 패키지 여섯 모듈

## 쉬운 말로 먼저

이 문서는 프로그램에서 사람과 직접 맞닿는 부분을 다룹니다. 이 가계부는 창이 뜨는 프로그램이 아니라 검은 화면에 `python -m budget_app list` 처럼 글자를 쳐서 쓰는 프로그램이라, 사람이 친 글자를 알아듣는 일부터 시작합니다. 이 저장소에는 `budget_app` 이라는 명령이 따로 설치되지 않으므로 실제로 치는 것은 늘 `python -m budget_app …` 이고, 짧은 `budget_app` 은 도움말의 usage 줄에만 나오는 이름입니다. 빠진 값을 되묻고, 계산 결과를 읽을 만한 줄로 바꾸고, 그 줄을 어디로 내보낼지 정하는 일까지가 전부 여기 모여 있습니다. 까다로운 이유는 이 부분이 상대하는 것이 사람만이 아니기 때문입니다. 사람은 오타를 내고, 도중에 그만두고, 조건을 엉뚱한 자리에 적습니다. 반대편에는 결과만 파일로 받아 가거나 앞의 세 줄만 읽고 떠나 버리는 다른 프로그램이 있습니다. 어느 쪽을 상대하든 이상한 메시지를 흘리거나 도중에 멈추지 않아야 하고, 그러기 위해 코드를 여섯 덩어리로 나눈 이야기가 이 문서입니다.

**이 문서에 자주 나오는 말**

| 말 | 쉬운 뜻 |
| --- | --- |
| 명령줄 | 검은 화면에 프로그램 이름과 조건을 한 줄로 쳐서 실행하는 방식 |
| argparse | 그 한 줄을 어떤 칸으로 나눠 읽을지 미리 정해 두는 파이썬 기본 도구 |
| 하위 명령 | `python -m budget_app add` 의 `add` 처럼, 프로그램 안에서 다시 한 번 고르는 작은 메뉴 |
| 핸들러 | 고른 메뉴 하나를 실제로 처리하는 담당 함수 |
| 프레젠터 | 계산 결과를 사람이 읽을 문장으로 바꿔 주는 담당. 화면에 내보내지는 않습니다 |
| stdout / stderr | 프로그램이 글자를 내보내는 두 개의 출구. 앞은 결과, 뒤는 오류·안내 |
| 버퍼링 | 글자를 한 자씩 내보내지 않고 어느 정도 모았다가 한꺼번에 내보내는 것 |
| 종료 코드 | 프로그램이 끝나면서 남기는 숫자 한 개. 0 이면 정상, 그 밖의 숫자는 문제의 종류 |

**바쁘면 여기만**

- **§1 여섯 모듈의 분업** — 무엇을 왜 여섯 덩어리로 나눴는지가 표 하나에 들어 있습니다. 이 문서의 나머지는 그 표의 각 칸을 펼친 것입니다.
- **§2.4 `--debug` 와 `argparse.SUPPRESS`** — 사용자가 분명히 친 옵션이 조용히 사라지는 버그와 그 방어입니다. 이 문서에서 가장 값나가는 한 절입니다.
- **§7 정리** — 나머지 내용을 질문·답변 일곱 쌍으로 압축해 두었습니다. 시간이 없으면 여기부터 읽고 궁금한 절로 거슬러 올라가면 됩니다.

---

사용자와 만나는 계층입니다. 리팩터 전 512줄짜리 `cli.py` 하나였던 것이 `cli/` 패키지 안의 **여섯 모듈**로 나뉘었습니다. 각각이 무엇을 담당하고 왜 나뉘었는지를 먼저 보고, 그다음 세 가지 상세로 들어갑니다 — argparse(명령줄 한 줄을 칸으로 나눠 읽는 파이썬 기본 도구), 대화형 입력, BrokenPipe(결과를 받아 가던 상대가 먼저 가 버려 출력할 곳이 없어진 상황) 처리입니다.

> **난이도**: 🟡 중급
>
> **먼저 읽으면 좋은 문서**: [04. 아키텍처](./04-architecture.md), [06. 횡단 관심사와 예외 처리](./06-decorators.md)
>
> **문법·표준 라이브러리 참조**: 본문 곳곳의 🔎/⚙️ 상자는 "이 관용구가 어느 PEP 에서 왔고 라이브러리 안에서 무슨 일을 하는가"를 압축한 것입니다. 더 깊은 설명은 [12. 문법과 표준 라이브러리](./12-syntax-and-stdlib.md)에 있습니다. 이 문서에서 특히 중요한 절은 argparse·logging 을 다루는 [12 §2-B](./12-syntax-and-stdlib.md)와 버퍼링·파이프를 다루는 [12 §3](./12-syntax-and-stdlib.md)입니다.

---

## 1. 여섯 모듈의 분업

나눈 기준은 "이 파일을 고쳐야 할 이유"입니다. 이유가 다르면 파일도 다릅니다. 표에서 특히 볼 것은 마지막 칸입니다 — 각 모듈이 **하지 않기로 한 일**이 경계를 만듭니다.

| 모듈 | 줄 | 담당 | 절대 하지 않는 것 |
|---|---|---|---|
| `cli/parser.py` | 243 | argparse 문법 정의 | 핸들러 함수 참조 |
| `cli/prompts.py` | 128 | 표준입력에서 값 받기 | 서비스 호출 |
| `cli/presenter.py` | 141 | 도메인 → 문자열 | **출력** (반환만) |
| `cli/output.py` | 100 | 채널 결정(stdout/stderr/log) | 문자열 조립 |
| `cli/error_handler.py` | 121 | 예외 → 메시지 + 종료 코드 | 도메인 판단 |
| `cli/app.py` | 98 | 오케스트레이션 + 진입점 | 문자열 조립, `print` |
| `cli/__init__.py` | 24 | `main` 재수출 | 그 외 재수출 |

위 표는 **책임의 분업**을 보여 주는 여섯 축입니다. 실제 `cli/` 패키지에는 이 밖에 `handlers.py`(190줄, 명령 하나당 함수 하나 — §6.1), `messages.py`(121줄, 사용자에게 보이는 문장 상수), `config.py`(29줄, 기본값·한도·종료 코드)도 있습니다. 뒤 둘은 "값만 있는 모듈"이라 축으로 세지 않았습니다.

**`cli/__init__.py` 만 재수출을 합니다.** `__main__.py` 의 `from .cli import main` 이 그대로 동작해야 하고, `main` 은 이 패키지가 밖에 내보이는 **유일한 공개 심볼**이기 때문입니다. `domain/` 과 `storage/` 의 `__init__.py` 는 docstring 만 두어, `from ..domain.entities import Transaction` 처럼 **어느 파일이 무엇을 소유하는지** 계속 보이게 합니다.

> **🔎 문법의 출처** — `from .cli import main` 의 앞점(`.`)은 **명시적 상대 import** 로, PEP 328 이 도입하고 파이썬 3 에서 유일한 상대 import 문법이 되었습니다(암묵적 상대 import 는 3.0 에서 제거). 점 하나는 "현재 패키지", 두 개(`from ..domain ...`)는 "부모 패키지"를 뜻하며, 이 계산은 실행 시 모듈의 `__package__` 값을 기준으로 이뤄집니다. 그래서 상대 import 가 있는 파일은 **스크립트로 직접 실행할 수 없고**(`__package__` 가 비어 있음) `python -m budget_app` 처럼 패키지로 실행해야 합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

**`output.py` 가 이 패키지 안에 있는 것은 실측 결과입니다.** 이 모듈을 import 하는 곳은 `app`·`error_handler`·`prompts` 셋뿐이고 전부 CLI 계층입니다([04 §1.2](./04-architecture.md)).

### 1.1 왜 나눴나 — 고칠 이유가 넷이었다

리팩터 전 `cli.py` 는 512줄이었고, 이 파일을 고칠 이유가 네 개였습니다.

```
[리팩터 전 cli.py 512줄]
  ├─ argparse 파서 구성          약 120줄  ← 명령줄 문법이 바뀔 때
  ├─ 대화형 입력 헬퍼             약 55줄  ← 입력 정책이 바뀔 때
  ├─ 출력 포맷 + print 26곳       약 60줄  ← 화면 표시가 바뀔 때
  ├─ cmd_* 핸들러 10개           약 190줄  ← 처리 순서가 바뀔 때
  └─ main + BrokenPipe            약 40줄
```

지금은 파일마다 이유가 하나입니다. 그 효과가 가장 잘 드러나는 곳이 `cmd_summary` 입니다.

```python
# 리팩터 전 — 25줄 (렌더링이 핸들러에 섞임)
@handle_errors
def cmd_summary(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    result = ctx.budget_service.monthly_summary(args.month, top_n=args.top)
    if not result["has_data"] and result["budget"] is None:
        print(config.MSG_SUMMARY_NO_DATA.format(month=result["month"]))
        return 0
    print(config.MSG_SUMMARY_INCOME.format(income=result["income"]))
    print(config.MSG_SUMMARY_EXPENSE.format(expense=result["expense"]))
    print(config.MSG_SUMMARY_BALANCE.format(balance=result["balance"]))
    budget = result["budget"]
    if budget is not None:
        usage = result["usage_pct"]
        usage_str = config.FMT_USAGE_PCT.format(usage=usage) if usage is not None else config.MSG_USAGE_NA
        print(config.MSG_SUMMARY_BUDGET.format(amount=budget.amount, usage=usage_str))
        if result["over_budget"]:
            print(config.MSG_OVER_BUDGET)
    if result["top_expense"]:
        n = len(result["top_expense"])
        print(config.MSG_TOP_EXPENSE_HEADER.format(n=n))
        for i, (cat, amt) in enumerate(result["top_expense"], start=1):
            print(config.FMT_TOP_EXPENSE_ITEM.format(rank=i, category=cat, amount=amt))
    return 0
```

budget_app/cli/handlers.py:72-75

```python
def cmd_summary(ctx: AppContext, args: argparse.Namespace) -> int:
    summary = ctx.budget_service.monthly_summary(args.month, top_n=args.top)
    output.out_lines(presenter.summary_lines(summary))
    return config.EXIT_OK
```

**세 줄에 세 계층이 한 번씩** — 서비스가 계산하고, 프레젠터가 문자열로 바꾸고, 출력 모듈이 채널을 고릅니다.

---

## 2. `parser.py` — argparse 문법만

이 파일은 사람이 친 한 줄을 프로그램이 쓸 수 있는 값으로 바꾸는 일만 합니다. 무엇을 할지 고르거나 실제로 실행하는 일은 하지 않습니다.

> **💡 쉽게 말하면** — argparse 는 **주문서 양식**입니다. 어떤 칸이 있고, 어느 칸이 필수이고, 어느 칸에는 정해진 몇 가지만 적을 수 있는지를 미리 인쇄해 두는 일입니다. 손님이 필수 칸을 비우거나 없는 메뉴를 적으면 창구가 양식을 그 자리에서 되돌려 주므로, 주방은 그 두 종류의 잘못된 주문서는 볼 일이 없습니다. 첫 칸에서 대분류를 고르면 그에 맞는 뒷장이 딸려 나오는 것이 하위 명령입니다 — `python -m budget_app category add` 의 `category` 가 대분류, `add` 가 그 뒷장의 소분류입니다.
> 다만 이 비유는 **창구가 보는 범위**에서 깨집니다 — 창구가 되돌려 보내는 것은 빈 필수 칸, 목록에 없는 값, 그리고 숫자 칸에 숫자가 아닌 글자를 적은 경우까지입니다. 적힌 날짜가 실제로 있는 날인지, 금액이 양수인지는 창구가 아예 보지 않고 그대로 주방으로 넘어가며, 그것을 보는 것은 도메인 검증기와 서비스입니다(그래서 §2.8 처럼 종료 코드 2 에 이르는 길이 두 갈래입니다). 덧붙여 이 양식은 종이가 아니라 실행되는 코드라, 칸을 늘리는 일도 되돌려 보낼 때 찍히는 문구도 전부 파이썬 함수 호출로 만들어집니다.

### 2.1 왜 핸들러 함수 대신 문자열 키인가

budget_app/cli/parser.py:1-2

```python
"""argparse 구성 — 명령줄 문법 정의만 담당한다.

```

**순환 import 문제**(두 파일이 서로를 import 해서, 먼저 읽히기 시작한 쪽이 아직 반쯤만 만들어진 상대를 보게 되는 상태)**를 그림으로:**

```
[방법 A — 함수 객체를 직접]        [방법 B — 문자열 키 (채택)]

parser.py                          parser.py
  set_defaults(func=cmd_add)         set_defaults(handler="add")
       │ import 필요                      (app 을 모름)
       ▼
cli.py (분리 전 단일 모듈)          app.py
  def cmd_add(...)                   HANDLERS = {"add": handlers.cmd_add}
       │ import 필요                      │
       ▼                                 ▼ import
parser.build_parser()              parser.build_parser()
       │
   ✗ 순환!                            ✅ 한 방향
```

> **⚙️ 내부 동작** — `parser.set_defaults(handler="add")` 는 마법이 아니라 딕셔너리 갱신입니다. CPython 의 `argparse._ActionsContainer.set_defaults` 는 본문이 두 줄뿐입니다 — 넘긴 키워드를 파서의 `self._defaults` 딕셔너리에 `update` 하고, 같은 `dest` 를 가진 기존 액션이 있으면 그 액션의 `.default` 도 갈아 끼웁니다. 파싱이 끝날 때 `_defaults` 의 항목들이 아직 없는 속성만 골라 namespace 에 `setattr` 됩니다. 즉 `args.handler` 는 **명령줄에 대응하는 문자열이 하나도 없는데도** namespace 에 존재하는 값이고, 그 위에 `HANDLERS[args.handler]` 라는 **딕셔너리 해시 조회**가 얹혀 `if/elif` 사슬을 대신합니다. → [12 §2-B](./12-syntax-and-stdlib.md)

### 2.2 죽은 코드가 사라진 과정

```python
# 리팩터 전 — 하위 명령 3개가 한 핸들러
@handle_errors
def cmd_category(args: argparse.Namespace) -> int:
    ctx = AppContext(args.data_dir)
    sub = args.cat_cmd
    if sub == "add":
        ...
        return 0
    if sub == "list":
        ...
        return 0
    if sub == "remove":
        ...
        return 0
    raise AppError(config.ERR_UNKNOWN_CATEGORY_CMD, hint=config.HINT_CATEGORY_SUBCMD)
    #     ↑ 도달 불가능한 코드
```

마지막 줄은 **절대 실행되지 않습니다.** `add_subparsers(dest="cat_cmd", required=True)` 가 `sub` 를 세 값 중 하나로 제한하기 때문입니다. 그런데 코드에 있으니 메시지 상수(`ERR_UNKNOWN_CATEGORY_CMD`, `HINT_CATEGORY_SUBCMD`)까지 정의돼 있었습니다.

지금은 하위 명령마다 핸들러가 하나씩 대응하므로 분기도 죽은 코드도 없습니다. **메시지 상수 4개도 함께 삭제됐습니다**(`budget` 쪽도 같았습니다).

### 2.3 파서 구성 — 함수 분리

budget_app/cli/parser.py:79-105

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=config.PROG_NAME,
        description=messages.PROG_DESCRIPTION,
    )
    # 실제 기본값은 여기 한 곳에만 있다 — 아래 파서들은 전부 SUPPRESS 다.
    parser.add_argument("--debug", action="store_true", help=DEBUG_HELP)
    parser.add_argument(
        "--data-dir", dest="data_dir", default=config.DEFAULT_DATA_DIR, help=DATA_DIR_HELP
    )
    # 저장소 준비가 필요한지의 기본값. backup 만 끈다(없는 폴더를 만들어 버리면
    # "백업할 데이터가 없다"는 오류 대신 빈 백업이 생긴다).
    parser.set_defaults(needs_storage=True)
    sub = parser.add_subparsers(dest="command", required=True)

    _add_add(sub)
    _add_list(sub)
    _add_search(sub)
    _add_summary(sub)
    _add_budget(sub)
    _add_category(sub)
    _add_update(sub)
    _add_delete(sub)
    _add_export(sub)
    _add_import(sub)
    _add_backup(sub)
    return parser
```

명령마다 함수를 나눈 이유는 **한 함수가 120줄이 되는 것을 막기 위해서**입니다. `build_parser` 본문만 보면 "이 프로그램에 명령이 11개 있다"가 한눈에 보입니다.

> **⚙️ 내부 동작** — `add_subparsers()` 가 돌려주는 `sub` 는 파서가 아니라 **`argparse._SubParsersAction` 이라는 액션 객체 하나**입니다(로컬 3.13.1 에서 `type(sub).__name__` 으로 확인). 이 액션은 `nargs=argparse.PARSER`(문자열 `'A...'`)를 가진 **위치 인자**로 등록되므로 "첫 낱말 하나 + 그 뒤 전부"를 한 번에 삼킵니다. `sub.add_parser("list")` 는 완전히 새로운 `ArgumentParser` 를 만들어 액션 내부의 `_name_parser_map` 딕셔너리에 이름으로 등록하고 그 파서를 돌려줍니다. 그래서 `_add_list(sub)` 안에서 하는 일은 전부 **그 하위 파서 객체**에 대한 설정이고, 최상위 파서는 하위 명령의 옵션을 하나도 알지 못합니다. → [12 §2-B](./12-syntax-and-stdlib.md)

### 2.4 `--debug` 와 `argparse.SUPPRESS`

> **💡 쉽게 말하면** — 같은 항목이 있는 양식을 두 장 겹쳐 쓴다고 생각해 보세요. 첫 장(모든 명령이 공유하는 양식)에 "데이터 폴더: ./mydata" 라고 적었는데, 둘째 장(명령별 양식)의 같은 칸을 담당자가 "비어 있으니 기본값이라도 적어 두자"며 "./data" 로 채워 버리면, 두 장을 겹쳐 읽는 사람은 첫 장에 적힌 답을 못 봅니다. `argparse.SUPPRESS` 는 그 담당자에게 **"그 칸은 둘째 장에서 아예 지우라"** 고 이르는 표시입니다. 칸 자체가 없어야 첫 장에 적힌 답이 살아남습니다.
> 다만 이 비유는 **"빈 칸"이라는 말**에서 깨집니다 — 칸이 그대로 남아 있고 값만 비어 있으면(예: `default=None`) 그 빈 값이 첫 장의 답을 덮어 지웁니다. 겹쳐 읽는 규칙에 "비어 있으면 넘어간다"는 조건이 없기 때문인데, `SUPPRESS` 는 칸을 비우는 쪽이 아니라 칸을 만들지 않는 쪽이라 그 규칙에 걸릴 것 자체가 없습니다. 그리고 종이라면 위에 놓인 장이 이기겠지만, 여기서는 나중에 처리되는 하위 명령 쪽이 언제나 위에 놓입니다. 그 기계장치가 §2.4.1 입니다.

budget_app/cli/parser.py:84-88 (실제 기본값은 최상위 파서 한 곳에만)

```python
    # 실제 기본값은 여기 한 곳에만 있다 — 아래 파서들은 전부 SUPPRESS 다.
    parser.add_argument("--debug", action="store_true", help=DEBUG_HELP)
    parser.add_argument(
        "--data-dir", dest="data_dir", default=config.DEFAULT_DATA_DIR, help=DATA_DIR_HELP
    )
```

budget_app/cli/parser.py:75-76 (하위·말단 파서는 값을 받을 때만 덮어쓴다)

```python
    p.add_argument("--data-dir", dest="data_dir", default=argparse.SUPPRESS, help=DATA_DIR_HELP)
    p.add_argument("--debug", action="store_true", default=argparse.SUPPRESS, help=DEBUG_HELP)
```

**`argparse.SUPPRESS` 의 동작.** argparse 는 파싱이 끝나면 각 인자의 기본값을 namespace(파싱 결과를 담아 두는 값 보관함)에 채웁니다. 하위 파서는 상위 파서보다 나중에 처리됩니다. 그래서 하위 파서 쪽 기본값이 상위에서 이미 읽어 둔 값을 **덮어씁니다**.

```
budget_app --debug list
    │
    ├─ 최상위 파서: --debug 를 봄 → args.debug = True
    └─ list 파서:   --debug 없음  → 기본값을 채움
                                    default=False 라면 → args.debug = False  ❌
                                    default=SUPPRESS 라면 → 아무것도 안 함 → True 유지 ✅
```

`SUPPRESS` 는 "값이 명시되지 않으면 namespace 에 속성 자체를 만들지 마라"는 뜻입니다. 그래서 `main` 이 `getattr(args, "debug", False)` 로 읽습니다.

#### 2.4.1 왜 하위 파서가 상위 값을 덮어쓰나 — argparse 내부

이 문서에서 **가장 중요한 내부 동작**입니다. 위 그림의 "하위 파서 쪽 기본값이 덮어쓴다"는 서술은 결과만 말한 것이고, 실제 기계장치는 CPython `argparse` 안의 함수 **두 개**로 이뤄져 있습니다.

**(1) 하위 명령을 만나면 하위 파서를 재귀 호출합니다.** `_SubParsersAction.__call__`(파싱 도중 하위 명령 이름을 만났을 때 불리는 함수)의 끝부분은 이렇습니다.

```python
# CPython 3.13.1 Lib/argparse.py — _SubParsersAction.__call__ 의 마지막 부분
subnamespace, arg_strings = subparser.parse_known_args(arg_strings, None)
for key, value in vars(subnamespace).items():
    setattr(namespace, key, value)
```

하위 파서가 **자기만의 빈 namespace(`subnamespace`)** 에 파싱한 뒤, 그 안에 들어 있는 **모든 키**를 상위 namespace 위에 `setattr` 로 복사합니다. 조건이 없습니다 — `subnamespace` 에 키가 있으면 무조건 덮어씁니다.

**(2) 그 빈 namespace 를 채우는 규칙이 `SUPPRESS` 를 봅니다.** `parse_known_args` 는 실제 파싱을 시작하기 전에 기본값부터 채워 넣는데, 그 루프가 정확히 이렇습니다.

```python
# CPython 3.13.1 Lib/argparse.py — ArgumentParser._parse_known_args2
for action in self._actions:
    if action.dest is not SUPPRESS:
        if not hasattr(namespace, action.dest):
            if action.default is not SUPPRESS:
                setattr(namespace, action.dest, action.default)
```

`default` 가 `SUPPRESS` 면 마지막 `setattr` 을 건너뜁니다. 명령줄에 `--debug` 가 실제로 나오지 않는 한 `subnamespace` 에는 `debug` 키가 **아예 생기지 않고**, 따라서 (1) 의 복사 루프가 그 키를 만지지 않으며, 최상위에서 읽어 둔 값이 살아남습니다.

`argparse.SUPPRESS` 자체는 특별한 타입이 아니라 **`'==SUPPRESS=='` 라는 그냥 문자열 상수**입니다(`repr(argparse.SUPPRESS)` 로 확인). argparse 는 `is not SUPPRESS` 로 동일 객체인지만 봅니다.

**실행으로 재현.** 같은 인자(`--debug --data-dir ./mydata list`)를 SUPPRESS 없는 파서와 있는 파서에 각각 넣어 봅니다.

```python
# 일반론 재현 코드 — 이 소스에는 없습니다(budget_app 구조만 흉내 낸 것)
def build(sup):
    p = argparse.ArgumentParser(prog="demo")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--data-dir", dest="data_dir", default="./data")
    s = p.add_subparsers(dest="command", required=True)
    q = s.add_parser("list")
    if sup:
        q.add_argument("--data-dir", dest="data_dir", default=argparse.SUPPRESS)
        q.add_argument("--debug", action="store_true", default=argparse.SUPPRESS)
    else:
        q.add_argument("--data-dir", dest="data_dir", default="./data")
        q.add_argument("--debug", action="store_true", default=False)
    return p

argv = ["--debug", "--data-dir", "./mydata", "list"]
```

실제 출력(CPython 3.13.1):

```
default  {'debug': False, 'data_dir': './data',   'command': 'list'}
SUPPRESS {'debug': True,  'data_dir': './mydata', 'command': 'list'}
```

`--debug` 를 분명히 쳤는데 첫 줄에서는 `False` 이고, `--data-dir ./mydata` 도 `./data` 로 되돌아갔습니다. **`_add_shared_options` 의 `default=argparse.SUPPRESS` 두 글자가 막고 있는 것이 바로 이 조용한 되돌림**입니다. 소스 docstring(`parser.py:66-69`)이 "여기에 `default=DEFAULT_DATA_DIR` 를 주면 하위 파서가 앞에서 읽어 둔 값을 기본값으로 되돌려 버린다"고 적은 것이 이 실험입니다.

> **⚙️ 내부 동작** — 같은 이유로 `main` 은 `args.debug` 가 아니라 `getattr(args, "debug", False)` 로 읽습니다. `argparse.Namespace` 는 `__getattr__` 를 정의하지 않는 평범한 객체라, 속성이 없으면 `AttributeError` 가 납니다. 최상위 파서에 `--debug` 가 있으므로 실제로는 항상 채워지지만, 두 인자 `getattr` 은 "이 값은 없을 수도 있다"는 SUPPRESS 계약을 코드로 적어 두는 표시이기도 합니다. → [12 §1-B](./12-syntax-and-stdlib.md)

### 2.5 2단 명령의 옵션 자리 — 리팩터에서 고친 버그

budget_app/cli/parser.py:58-76

```python
def _add_shared_options(p: argparse.ArgumentParser) -> None:
    """모든 하위 명령이 공유하는 옵션 — 데이터 폴더와 디버그 스위치.
    ...
    """
    p.add_argument("--data-dir", dest="data_dir", default=argparse.SUPPRESS, help=DATA_DIR_HELP)
    p.add_argument("--debug", action="store_true", default=argparse.SUPPRESS, help=DEBUG_HELP)
```

이 함수 하나를 **최상위 하위 파서(`list`, `category` …)와 2단 말단 파서(`category list` …) 양쪽**에 붙입니다. 말단 파서란 `category list` 처럼 두 단계로 골라 들어간 **마지막 단계의 양식**입니다. argparse 는 하위 명령 이름 뒤에 오는 인자를 전부 그 말단 파서에게 넘깁니다. 그래서 말단에도 같은 옵션을 달아 두지 않으면 `category list --data-dir X` 가 "unrecognized arguments" 로 죽습니다. `category --data-dir X list` 처럼 옵션을 **가운데**에 끼워야만 동작하게 되는 것입니다.

> **함수가 하나로 합쳐진 경위** — 이전에는 `_add_common_options`(기본값 있음)와 `_add_leaf_options`(SUPPRESS) 둘로 나뉘어 있었고, 차이는 `--data-dir` 의 기본값 하나뿐이었습니다. 그 기본값을 최상위 파서로 올리자 두 함수가 완전히 같아져 하나로 합쳤습니다. **차이가 사라지면 함수도 사라져야 합니다.**

**버그 재현 (리팩터 전):**

```
$ python -m budget_app list --data-dir ./mydata        ✅ 동작
$ python -m budget_app category list --data-dir ./mydata
usage: budget_app [-h] [--debug] {add,list,...} ...
budget_app: error: unrecognized arguments: --data-dir ./mydata     ❌

$ python -m budget_app category --data-dir ./mydata list   ✅ 이렇게만 동작
```

**원인.** argparse 는 하위 명령 이름(`list`)을 만나면 그 뒤의 모든 인자를 **말단 파서**에게 넘깁니다. 말단 파서에 `--data-dir` 가 정의돼 있지 않으니 "모르는 인자"가 됩니다.

**같은 프로그램인데 명령에 따라 옵션 자리가 다른 것**은 사용성 문제이자 일관성 문제입니다. 말단 파서에도 같은 옵션을 달아 양쪽 다 동작하게 했습니다.

### 2.6 새 옵션 두 개

budget_app/cli/parser.py:201-214

```python
def _add_export(sub) -> None:
    p = sub.add_parser("export", help="CSV 내보내기")
    _add_shared_options(p)
    p.add_argument("--out", required=True, help="출력 CSV 경로")
    p.add_argument("--month", help="대상 월 YYYY-MM")
    p.add_argument("--from", dest="from_", help="시작일 YYYY-MM-DD")
    p.add_argument("--to", dest="to", help="종료일 YYYY-MM-DD")
    p.add_argument(
        "--no-id",
        dest="include_id",
        action="store_false",
        help="id 컬럼을 빼고 내보낸다 (외부 도구용). 기본은 포함 — 다시 import 할 때 중복을 막는다",
    )
    p.set_defaults(handler="export", include_id=True)
```

**`--no-id` 의 `action="store_false"`** 는 "이 플래그가 있으면 `include_id` 를 False 로"라는 뜻입니다. `set_defaults(include_id=True)` 와 짝을 이뤄 "기본 포함, 플래그로 제외"를 표현합니다. `--with-id` 대신 `--no-id` 로 만든 것은 **기본값이 무엇인지 이름에서 드러나게** 하기 위해서입니다.

> **⚙️ 내부 동작** — `action="store_false"` 는 문자열이 아니라 **레지스트리 키**입니다. argparse 는 파서마다 `_registries['action']` 딕셔너리를 두고 `"store_true"`/`"store_false"`/`"append"` 같은 이름을 클래스에 대응시켜 두었습니다. `"store_false"` 는 `_StoreFalseAction` 으로 풀리고, 그 `__init__` 은 `const=False, default=True` 를 넣은 채 `_StoreConstAction` 을 부릅니다. 즉 **`--no-id` 는 그 자체로 이미 `include_id=True` 가 기본**이고, 코드의 `set_defaults(include_id=True)` 는 그 사실을 눈에 보이게 다시 적어 둔 것입니다(중복이지만 "기본이 포함"이라는 계약이 한 줄로 읽힙니다).
>
> 여기서 `dest="include_id"` 가 없으면 어떻게 될까요. argparse 는 긴 옵션 이름의 앞 대시를 떼고 남은 대시를 밑줄로 바꿔 `dest` 를 만들므로 `--no-id` → **`args.no_id`** 가 되고, "id 를 뺄까"라는 이중 부정이 핸들러까지 흘러갑니다. `dest` 하나로 **명령줄의 이름(부정형)과 코드 안의 이름(긍정형)을 분리**한 것입니다. `--from` 이 예약어라 `dest="from_"` 인 것도 같은 도구의 다른 용도입니다. → [12 §2-B](./12-syntax-and-stdlib.md)

**`choices=list(config.ON_DUPLICATE_CHOICES)`** 는 상수를 그대로 씁니다. 정책을 추가하면 config 한 곳만 고치면 CLI 검증까지 따라옵니다.

> **⚙️ 내부 동작** — `choices` 검사는 타입 변환 **뒤에** 일어납니다. argparse 는 `_get_value()` 로 `type=` 을 적용한 다음 `_check_value()` 에서 `value not in choices` 를 봅니다. 그래서 `choices` 에 담기는 값은 명령줄 문자열이 아니라 **변환 결과**여야 합니다. 이 소스에서는 `--type`·`--on-duplicate` 모두 `type=` 이 없어 문자열 그대로이므로 문제가 되지 않습니다. `ON_DUPLICATE_CHOICES`(`services/config.py:12`)와 `VALID_TYPES`(`domain/config.py:15`)는 둘 다 **튜플**이고, `list(...)` 로 감싼 것은 argparse 액션이 공용 상수 객체를 그대로 붙들지 않도록 사본을 넘기는 방어입니다.

### 2.7 `needs_storage` — backup 만 예외

budget_app/cli/parser.py:239-243

```python
def _add_backup(sub) -> None:
    p = sub.add_parser("backup", help="데이터 폴더 백업 (보너스)")
    _add_shared_options(p)
    # 백업은 기존 폴더를 읽기만 한다 — 없으면 만들지 말고 오류로 알려야 한다.
    p.set_defaults(handler="backup", needs_storage=False)
```

최상위에서 `set_defaults(needs_storage=True)` 로 기본을 켜 두고, `backup` 만 끕니다. 이 플래그는 `main()` 이 읽습니다(§6.2).

### 2.8 `type=positive_int` — argparse 가 직접 죽이는 경로

budget_app/cli/parser.py:38-55

```python
def positive_int(raw: str) -> int:
    """1 이상의 정수만 통과시키는 argparse ``type``.

    ``--limit 0`` 은 "데이터가 있는데 (데이터 없음) 이라고 출력"되는 원인이었다.
    ...
    ``ArgumentTypeError`` 를 쓰면 argparse 가 usage 와 함께 종료 코드 2 로 끝낸다 —
    다른 인자 오류와 같은 경로다.
    """
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(messages.ERR_ARG_NOT_INT.format(value=raw)) from exc
    if value < 1:
        raise argparse.ArgumentTypeError(messages.ERR_ARG_NOT_POSITIVE.format(value=raw))
    return value
```

`--limit`(`_add_list`)와 `--top`(`_add_summary`)이 이 함수를 `type=` 으로 씁니다.

> **⚙️ 내부 동작** — argparse 의 `type=` 은 "타입"이 아니라 **문자열 하나를 받는 아무 콜러블**입니다. 값이 들어오면 `ArgumentParser._get_value()` 가 `type_func(arg_string)` 을 부르고, 그 주위를 세 갈래 `except` 로 감쌉니다 — `ArgumentTypeError` 면 **예외 메시지를 그대로** 오류 문구로 쓰고, `TypeError`/`ValueError` 면 `invalid <타입이름> value: <값>` 이라는 argparse 기본 문구로 바꿉니다. 셋 다 결국 `ArgumentError` 로 다시 던져지고, `parse_args` 가 그것을 잡아 `parser.error()` → usage 출력 → `sys.exit(2)` 로 끝납니다.
>
> `int(raw)` 가 던지는 `ValueError` 를 굳이 잡아 `ArgumentTypeError` 로 바꿔 던지는 이유가 여기 있습니다. 그냥 흘려보내면 `invalid positive_int value: 'abc'` 라는 **함수 이름이 노출된 영어 문구**가 나오지만, 잡아서 다시 던지면 `messages.ERR_ARG_NOT_INT` 의 한국어 문장이 그대로 화면에 나옵니다. → [12 §2-B](./12-syntax-and-stdlib.md)

**이 경로는 `@handle_errors` 를 지나지 않습니다.** 종료 코드 표를 정직하게 읽으려면 이 사실이 필요합니다.

```
$ python -m budget_app list --limit 0
usage: budget_app list [-h] [--data-dir DATA_DIR] [--debug] [--limit LIMIT]
budget_app list: error: argument --limit: 1 이상이어야 합니다: 0
   → SystemExit(2)
```

이유가 **둘** 있고 각각 독립적으로 충분합니다.

1. **위치.** 변환은 `main` 의 `parse_args(argv)` 안에서 일어납니다. `@handle_errors` 가 붙은 것은 그다음 줄의 `_dispatch` 이므로, 방패에 닿기 전에 프로세스가 끝납니다.
2. **예외 계보.** argparse 가 마지막에 던지는 것은 `SystemExit` 이고, 이것은 `Exception` 이 **아니라** `BaseException` 의 직속 자식입니다. `handle_errors` 의 마지막 그물인 `except Exception` 은 `SystemExit` 을 잡지 못합니다(로컬에서 `isinstance(SystemExit(2), Exception)` → `False` 로 확인).

> **🔎 문법의 출처** — `SystemExit`·`KeyboardInterrupt` 를 `Exception` 이 아니라 `BaseException` 밑으로 옮긴 것은 PEP 352 이고 파이썬 2.5 에서 들어왔습니다(`GeneratorExit` 도 지금은 같은 자리에 있지만, 그것은 PEP 352 가 한 일이 아니라 파이썬 2.6 의 후속 정리입니다). 목적이 정확히 이것입니다 — `except Exception:` 으로 광범위하게 예외를 삼키는 코드가 **"이제 그만 끝내라"는 신호까지 삼켜 버리는 사고**를 막는 것. 그래서 `sys.exit()` 과 Ctrl+C 는 광범위한 `except` 를 뚫고 나갑니다. 이 소스가 `KeyboardInterrupt` 를 따로 한 줄 적어 잡는 것(`error_handler.py:61-63`)도 같은 이유입니다 — 안 적으면 안 잡힙니다. → [12 §1-C](./12-syntax-and-stdlib.md)

결론적으로 종료 코드 2(`EXIT_VALIDATION`)에 도달하는 길이 **두 개**입니다.

| 길 | 누가 결정 | 예 |
|---|---|---|
| argparse 의 `parser.error()` | argparse 내부 (`sys.exit(2)`) | `--limit 0`, `--type foo`, 필수 옵션 누락, 알 수 없는 하위 명령 |
| `handle_errors` 의 `except ValidationError` | `cli/config.py:24` 의 `EXIT_VALIDATION` | `--date 2024-13-01` 처럼 도메인 검증기가 거른 값 |

두 숫자가 우연히 같은 것이 아니라, **"사용자가 값을 고치면 해결되는 문제"라는 같은 부류를 셸에 같은 숫자로 알리려고** 맞춰 놓은 것입니다.

---

## 3. `prompts.py` — 대화형 입력

명령줄에 값을 다 적지 않았을 때 프로그램이 하나씩 되묻는 부분입니다. 무엇을 물을지, 틀린 값이 오면 몇 번까지 다시 물을지, 사람이 도중에 그만두면 어떻게 끝낼지를 이 파일이 정합니다.

### 3.1 핸들러에서 떼어낸 이유

budget_app/cli/prompts.py:1-11

```python
"""대화형 입력 — 표준입력에서 값을 받아 내는 일만 담당한다.

핸들러에서 떼어낸 이유: ``cmd_add`` 가 "무엇을 물어보고, 틀리면 몇 번까지 다시
받고, EOF 면 어떻게 끝낼지"까지 알고 있으면 한 함수가 입력 정책과 유스케이스
호출을 겸하게 된다. 지금 ``cmd_add`` 는 ``ask_transaction()`` 한 줄로 값을 받고
서비스에 넘기기만 한다.

정책 통일도 함께 이뤄졌다. 이전에는 ``category add`` 만 ``ask()`` 를 한 번 부르고
끝나서, 빈 이름을 넣으면 재입력 없이 종료 코드 2 로 죽었다. 같은 "대화형 입력"인데
거래 추가와 규칙이 달랐다. 지금은 모든 대화형 입력이 ``ask_until`` 을 지난다.
"""
```

**입력 정책 불일치 버그.** 리팩터 전 `cmd_category_add` 는 이랬습니다.

```python
# 리팩터 전
        name = (args.name or _ask(config.PROMPT_CATEGORY_NAME)).strip()
```

`_ask` 는 한 번만 묻습니다. 빈 값을 입력하면 `Category.normalize` 가 `ValidationError` 를 던지고 **종료 코드 2로 죽었습니다.** 반면 `cmd_add` 의 카테고리 입력은 틀리면 최대 10번 다시 물었습니다. 같은 "대화형 입력"인데 정책이 달랐던 것입니다.

budget_app/cli/prompts.py:124-128

```python
def ask_category_name(given: str | None) -> str:
    """``--name`` 이 있으면 검증만, 없으면 물어본다."""
    if given is not None:
        return validators.parse_category(given)
    return ask_until(messages.PROMPT_CATEGORY_NAME, validators.parse_category)
```

지금은 둘 다 `ask_until` 을 지납니다.

### 3.2 EOF 처리 — `InputAborted`

budget_app/cli/prompts.py:28-28

```python
class InputAborted(AppError):
```

**왜 이 예외가 필요한가.** 이런 실행을 생각해 보세요.

```bash
printf '2024-01-15\nexpense\n' | python -m budget_app add
```

가운데의 `|` 는 앞 명령의 출력을 뒤 명령의 입력으로 잇는 연결(파이프)입니다. 즉 사람이 앉아서 답하는 대신 날짜와 타입 두 줄만 미리 밀어 넣은 것이고, 그 두 줄을 다 쓰면 더 읽을 것이 없습니다. 세 번째 프롬프트(카테고리)에서 `input()` 이 `EOFError` 를 던집니다. 이것을 잡지 않으면:

- **처리 안 함** → 스택트레이스(오류가 난 자리를 죽 늘어놓은 개발자용 출력)가 사용자 화면에 노출
- **빈 문자열 반환** → 검증기가 거부 → 다시 물음 → 또 EOF → **무한 루프**

> **💡 쉽게 말하면** — 전화로 설문을 받는 상황입니다. 세 번째 질문을 하려는데 상대가 이미 끊었습니다. 이때 "응답이 비어 있으니 다시 여쭙겠습니다"를 반복하면 끊긴 수화기에 대고 영원히 같은 질문을 하게 됩니다. 그래서 파이썬은 "빈 답"과 "끊겼음"을 **다른 종류의 신호**로 구분해서 알려 주고, 이 프로그램은 끊겼다는 신호를 받으면 되묻기를 그만두고 정리한 뒤 끝냅니다.
> 다만 이 비유는 **누가 끊었는가**에서 깨집니다 — 사람이 직접 Ctrl+D 를 누른 경우도 있지만, 위 예처럼 미리 밀어 넣은 줄을 다 쓴 자동 실행 쪽이 실제로는 더 흔합니다.

`InputAborted` 는 `AppError` 를 상속하므로 `handle_errors` 의 `except AppError` 가 **코드 추가 없이** 처리합니다. 종료 코드 4 로 깔끔히 끝납니다.

> **⚙️ 내부 동작** — `input(prompt)` 는 세 가지 일을 한 번에 합니다. ① `prompt` 를 **stdout 에 쓰고 flush** 합니다(개행 없이). ② stdin 에서 한 줄을 읽습니다. ③ 끝의 개행 문자를 **떼고** 돌려줍니다. 그래서 프롬프트 문자열은 결과 채널인 stdout 으로 나가고, 실제로 `printf 'x\n' | python -c "print('|'+input('PROMPT>')+'|')"` 를 실행하면 `PROMPT>|x|` 가 stdout 한 줄로 찍힙니다.
>
> **EOF 가 왜 빈 문자열이 아니라 예외인가.** 저수준 `sys.stdin.readline()` 은 스트림이 끝나면 `''` 를 돌려주는데, 이것은 "빈 줄을 읽었다"(`'\n'`)와 명확히 구분되는 신호입니다. 그런데 `input()` 은 개행을 떼고 주는 함수라, 그대로 `''` 를 돌려주면 **"사용자가 엔터만 쳤다"와 "스트림이 끝났다"가 똑같은 `''` 로 뭉개집니다.** 그래서 CPython 은 이 자리에서 `EOFError` 를 던집니다. 파이프 입력(`printf '2024-01-15\nexpense\n' | ... add`)에서는 준 줄을 다 소비한 **다음 호출**에서 곧바로 발생하며, 그 뒤 `sys.stdin.read()` 는 계속 `''` 를 돌려줍니다(로컬 3.13.1 에서 확인). 재시도 루프가 `''` 를 "잘못된 값"으로 보고 다시 묻는 한, 예외가 없으면 루프는 영원히 돕니다. → [12 §3](./12-syntax-and-stdlib.md)

> **🔎 문법의 출처** — `raise InputAborted() from exc`(`prompts.py:57`)의 `from` 절은 **예외 연쇄**로 PEP 3134 가 파이썬 3.0 에 넣었습니다. `from exc` 는 새 예외의 `__cause__` 에 원래 예외를 걸어 두고, 트레이스백을 찍을 때 "The above exception was the direct cause of..."로 두 예외를 이어 보여 줍니다. `from` 을 쓰지 않고 `except` 안에서 그냥 `raise` 해도 `__context__` 에는 자동으로 걸리지만(암묵적 연쇄), `from` 은 **"이건 우연히 겹친 게 아니라 내가 의도적으로 번역한 것"** 이라는 표시입니다. 같은 관용구가 `positive_int`(`parser.py:52`)에도 있습니다. → [12 §1-C](./12-syntax-and-stdlib.md)

### 3.3 `ask_until` — 재시도 루프의 뼈대

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

**세 가지 방어가 겹쳐 있습니다.**

| 위험 | 방어 |
|---|---|
| EOF 로 무한 루프 | `ask` 가 `InputAborted` 로 즉시 중단 |
| 잘못된 값 반복으로 무한 루프 | `for _ in range(MAX_INPUT_RETRIES)` |
| 스택트레이스 노출 | `ValidationError` 를 잡아 한 줄 안내 |

**`while True` 가 아니라 `for range(...)` 인 것**이 핵심입니다. 파이프로 잘못된 값을 무한히 흘려보내는 자동화 스크립트가 있어도 10회에서 멈춥니다.

**재입력 안내가 stderr 로 가는 것**도 채널 정책의 일부입니다 — 재입력 요청은 프로그램의 "결과"가 아니라 "진단"입니다.

`Callable[[str], T]` 타입 표기가 계약을 적어 둡니다 — "문자열을 받아 T 를 돌려주는 함수를 주면, 나도 T 를 돌려주겠다".

> **🔎 문법의 출처** — `T = TypeVar("T")`(`prompts.py:25`)로 만드는 **제네릭 함수**는 PEP 484(파이썬 3.5)가 도입한 타입 힌트 체계의 일부입니다. `TypeVar` 를 함수 시그니처에 두 번 이상 쓰면 "그 자리들이 **서로 같은 타입**이어야 한다"는 뜻이 되어, `ask_until(PROMPT_AMOUNT, parse_amount)` 의 반환은 `int`, `ask_until(PROMPT_DATE, parse_date)` 의 반환은 `str` 로 호출마다 다르게 좁혀집니다. 문자열 `"T"` 를 인자로 다시 적는 것은 변수 이름이 실행 시점에 자기 이름을 모르기 때문입니다.
>
> `Callable` 을 `typing` 이 아니라 `collections.abc` 에서 가져오는 것(`prompts.py:15`)은 PEP 585(파이썬 3.9)가 표준 컨테이너에 `[]` 첨자를 허용하면서 `typing.Callable` 등이 **비권장(deprecated)** 이 된 결과입니다. 실행 시점에 `collections.abc.Callable` 은 `isinstance` 검사에 쓰이는 진짜 추상 기반 클래스이고, `[]` 를 붙이면 `types.GenericAlias` 객체를 만들 뿐 아무 검사도 하지 않습니다. **타입 힌트는 실행에 영향을 주지 않습니다** — `ask_until` 에 정수를 넘겨도 파이썬은 막지 않고, 호출하다 `TypeError` 가 날 뿐입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **🔎 문법의 출처** — `for _ in range(...)` 의 밑줄은 **문법이 아니라 관례**입니다. `_` 는 다른 이름과 똑같이 값이 대입되는 평범한 변수이고, "이 값을 쓰지 않겠다"는 사람에게 보내는 신호일 뿐입니다(린터도 이 이름만 미사용 경고에서 빼 줍니다). `range(10)` 은 리스트를 만들지 않고 필요할 때 정수를 만들어 내는 `range` 객체이므로, 횟수가 아무리 커도 메모리는 일정합니다. → [12 §1-A](./12-syntax-and-stdlib.md)

### 3.4 검증기 조립

budget_app/cli/prompts.py:77-107

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
```

**`ask_transaction` 한 함수가 입력 순서와 각 필드의 검증기를 결정합니다.**

- 필수 4개(`date`/`type`/`category`/`amount`)는 `ask_until` — 틀리면 다시 묻습니다.
- 선택 2개(`memo`/`tags`)는 `ask` 한 번 — 빈 값이 정상이라 재입력할 이유가 없습니다.

**카테고리만 클로저 팩토리**(검사에 필요한 도구를 미리 품은 검사 함수를 그때그때 만들어 내는 방식)**인 이유**는 저장소를 봐야 판단되기 때문입니다. 나머지는 값만 보면 되므로 `validators` 모듈 함수를 그대로 넘깁니다. `ValidationError` 를 던지면 `ask_until` 이 잡아 재입력을 요구하므로, "등록 안 된 카테고리"도 **재입력 가능한 오류**가 됩니다.

> **⚙️ 내부 동작** — `_validate` 가 바깥 함수의 인자 `cat_service` 를 읽는 것을 **클로저**라고 합니다. 컴파일 시점에 파이썬은 `cat_service` 가 안쪽 함수에서도 쓰인다는 것을 알아채고 그 변수를 **셀(cell)** 객체에 담습니다. `return _validate` 로 바깥 함수가 끝나도 셀이 살아 있어 `registered_category_validator(cat_service).__closure__[0].cell_contents` 로 붙잡힌 서비스를 직접 꺼내 볼 수 있습니다. 즉 `ask_until` 이 받는 것은 **함수 하나**지만 그 안에는 저장소가 함께 실려 있습니다. `functools.partial` 이나 `__call__` 을 가진 클래스로도 같은 일을 할 수 있고, 셋 다 "상태를 가진 호출 가능 객체"라는 같은 것의 다른 표기입니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **🔎 문법의 출처** — `TransactionInput`(`prompts.py:40-49`)의 `@dataclass(frozen=True)` 는 PEP 557 로 파이썬 3.7 에 들어왔습니다. 클래스 본문의 **어노테이션이 붙은 이름들**(`__annotations__`)을 읽어 `__init__`·`__repr__`·`__eq__` 소스 코드를 **문자열로 만들어 `exec`** 한 뒤 클래스에 붙입니다. `frozen=True` 는 추가로 `__setattr__`/`__delattr__` 을 정의해 대입을 `FrozenInstanceError` 로 막습니다 — 언어 차원의 상수가 아니라 **덮어쓴 특수 메서드**이므로 `object.__setattr__` 로는 여전히 뚫립니다. → [12 §1-B](./12-syntax-and-stdlib.md)

미등록 시 사용 가능한 목록을 보여 주는 것도 UX 배려입니다.

```
카테고리: 커피
[오류] 등록되지 않은 카테고리입니다: 커피 (사용 가능: food, transport, rent, salary, etc)
[힌트] 다시 입력해 주세요.
카테고리:
```

---

## 4. `presenter.py` — 출력하지 않고 반환한다

계산이 끝난 값을 사람이 읽을 문장으로 바꾸는 부분입니다. 바꾸기만 하고 화면에 내보내지는 않습니다.

> **💡 쉽게 말하면** — 주방의 요리사는 접시에 담기까지만 하고, 손님 자리로 가져가는 일은 홀 직원이 합니다. 이렇게 나눠 두면 모양이 제대로 나왔는지 확인하려고 손님 자리까지 따라갈 필요가 없습니다. 주방 안에서 접시만 보면 됩니다. 프레젠터가 만든 문장을 화면에 찍지 않고 돌려주는 것도 같은 이유입니다 — "이 문장이 제대로 만들어졌나"를 확인할 때 프로그램을 실제로 띄우고 화면에 나온 글자를 긁어모을 필요가 없습니다.
> 다만 이 비유는 **접시가 한 번에 하나씩 나온다**는 점에서 깨집니다 — 프레젠터는 완성된 상을 통째로 내주는 것이 아니라 줄을 한 줄씩 내주고, 받는 쪽이 그만 받겠다고 하면 그 자리에서 멈춥니다(§4.2).

### 4.1 유일한 규칙

budget_app/cli/presenter.py:1-16

```python
"""프레젠터 — 도메인 객체를 사람이 읽을 줄로 바꾼다.

**출력하지 않고 문자열을 돌려준다.** 이것이 이 모듈의 유일한 규칙이다.

왜 그런가:

- 채널 결정(stdout/stderr)은 ``output`` 의 책임이다. 프레젠터가 ``print`` 를 하면
  두 모듈이 같은 책임을 나눠 갖게 된다.
- 반환값이 문자열이면 화면 없이 검증할 수 있다. 이전에는 요약 출력이
  ``cmd_summary`` 안에서 곧바로 ``print`` 되어, 형식을 확인하려면 프로세스를 띄우고
  stdout 을 캡처하는 수밖에 없었다.

프레젠터는 도메인 모델을 읽기만 하고 계산하지 않는다. "예산 미설정이면 N/A" 같은
판단은 ``MonthlySummary`` 의 property 가 이미 끝내 놓았고, 여기서는 ``None`` 인지만
본다.
"""
```

`grep -c "print(" budget_app/cli/presenter.py` 의 결과는 **0** 입니다.

### 4.2 제너레이터로 반환하는 이유

> **💡 쉽게 말하면** — 도서관에서 두꺼운 책의 내용을 확인하는 방법은 둘입니다. 전권을 복사해 가방에 넣고 나와서 보거나, 열람실에서 필요한 만큼만 한 장씩 넘겨 보거나. 뒤쪽이 제너레이터입니다 — 스무 줄만 필요하면 스물한 장째는 넘기지 않고, 가방(메모리)이 무거워지지도 않습니다.
> 다만 이 비유는 **중간에 정렬이 끼는 순간** 깨집니다 — 최신순으로 보려면 어차피 전권을 한 번은 훑어야 하고, 훑은 것을 다 손에 든 채로 첫 줄을 내놓게 됩니다. 즉 조건에 걸러진 항목 전체가 메모리에 쌓이고, `--limit 20` 을 붙여도 그 양은 줄지 않습니다. 이 프로그램의 `list` 가 정확히 그 경우라, 두 가지 이득 중 어느 쪽도 여기서는 얻지 못합니다. 그래서 이 절 뒤쪽에 "정직하게" 라는 단서가 붙습니다.

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

**`break` 가 상류까지 전파됩니다.**

```
저장소 iter_raw()  ──▶ stream()  ──▶ stream_sorted()  ──▶ tx_table(limit=20)  ──▶ out_lines
                                                              │
                                            20건 출력 후 break │
                                                              ▼
                                         상류 제너레이터도 더 이상 값을 요구받지 않음
```

> **🔎 문법의 출처** — 함수 본문에 `yield` 가 하나라도 있으면 그 함수는 **호출해도 본문이 실행되지 않고** 제너레이터 객체를 돌려주는 함수가 됩니다(PEP 255, 파이썬 2.2). 컴파일러가 코드 객체에 `CO_GENERATOR` 플래그를 세우기 때문이고, 그래서 `tx_table(...)` 을 부르는 것만으로는 저장소를 한 줄도 읽지 않습니다. 본문은 `next()` 가 불릴 때마다 **다음 `yield` 까지만** 실행되고 거기서 지역 변수(`count`, `tx`)와 실행 위치를 프레임에 남긴 채 멈춥니다. → [12 §1-C](./12-syntax-and-stdlib.md)

> **⚙️ `break` 가 상류까지 전파되는 실제 경로.** 제너레이터는 값을 **밀어내지(push) 않고 당겨집니다(pull)**. `for line in tx_table(...)` 이 도는 동안에만 `tx_table` 이 깨어나고, `tx_table` 이 깨어난 동안에만 `for tx in rows` 가 상류에 `next()` 를 겁니다. `break` 로 `tx_table` 이 멈추면 상류에 `next()` 를 거는 코드가 아무 데도 없으므로 상류는 **그 자리에 멈춘 채 그대로 남습니다** — 취소 신호를 보내는 것이 아니라 **아무도 부르지 않아서** 멈추는 것입니다. 이후 제너레이터 객체의 참조가 사라지면 파이썬이 `close()` 를 불러 멈춘 지점에 `GeneratorExit` 를 던지고, 그때 상류의 `with open(...)`(`storage/jsonl.py:174`)이 `finally` 를 타며 파일이 닫힙니다.

**정직하게 — `list` 경로에서는 파일 읽기까지 줄어들지는 않습니다.**

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

`stream_sorted` 는 **정렬 때문에** 파일을 끝까지 읽어 리스트로 모은 뒤에야 첫 값을 내놓습니다(docstring 이 직접 그렇게 적어 두었습니다). 그러므로 `--limit 20` 에서 `break` 가 실제로 아끼는 것은 **디스크 읽기가 아니라 나머지 항목의 `tx_line()` 문자열 조립과 그 줄들의 `print`** 입니다. `break` 가 끊는 상류는 `stream_sorted` 안의 `yield from items` 이지 파일을 읽는 `iter_raw` 가 아닙니다 — 그쪽은 이미 다 돌고 파일도 닫힌 뒤입니다.

"당기는 만큼만 읽는다"가 **파일 읽기까지 그대로 성립하는 경로**는 정렬이 없는 곳입니다. 예를 들어 `TransactionRepository.get`(`storage/repositories.py:112-119`)이 `stream()` 을 돌다 원하는 id 를 찾는 순간 `return` 하면 그 뒤의 줄은 디스크에서 읽지도 않습니다. 제너레이터 사슬의 이득은 "사슬 전체가 게으를 때"만 끝까지 전달되고, **중간에 `sort` 같은 전량 소비자가 하나 끼면 거기서 끊긴다** — 이것이 이 구조를 읽을 때 가장 흔히 오해하는 지점입니다([10 §4](./10-advanced-design.md)의 성능 분석과 이어집니다).

**빈 결과 처리가 여기 있는 것**도 눈여겨보세요. `count == 0` 이면 `(데이터 없음)` 한 줄을 내보냅니다. "비어 있을 때 무엇을 보여줄지"는 **표시의 문제**이므로 서비스가 아니라 프레젠터의 일입니다.

### 4.3 계산하지 않고 묻기만 한다

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

`summary.is_empty`, `summary.balance`, `summary.over_budget` — **전부 묻기만** 합니다. `income - expense` 를 여기서 계산하지 않습니다.

**`yield from _budget_lines(summary)`** 는 다른 제너레이터에 반복을 위임합니다. 예산 관련 두 줄을 별도 함수로 뺀 이유는 `summary_lines` 의 흐름(수입→지출→잔액→예산→TOP)이 한눈에 읽히게 하기 위해서입니다.

> **🔎 문법의 출처** — `yield from` 은 PEP 380 으로 파이썬 3.3 에 들어왔습니다. 그 전에는 `for x in gen(): yield x` 라고 손으로 풀어 써야 했고, 여기서는 그것과 결과가 같습니다. 다만 `yield from` 이 단순한 축약이 아닌 이유는 **`send()`·`throw()`·`close()`·반환값(`StopIteration.value`)까지 하위 제너레이터에 그대로 통과시키기** 때문입니다. 이 소스는 값만 흘려보내므로 축약으로 봐도 무방하지만, 같은 문법이 `stream_sorted` 의 `yield from items` 처럼 **리스트에도** 쓰입니다 — 대상은 제너레이터가 아니라 아무 이터러블이면 됩니다.
>
> `summary_lines` 안의 `return`(`presenter.py:66`)에 값이 없는 것도 문법의 결과입니다. 제너레이터 함수에서 `return` 은 "값을 하나 돌려준다"가 아니라 **`StopIteration` 을 일으켜 반복을 끝낸다**는 뜻이고, 그래서 `is_empty` 일 때 한 줄만 내고 그 자리에서 끝납니다(파이썬 3.3 부터는 `return 값` 도 문법상 허용되지만 그 값은 `yield` 되지 않고 `StopIteration.value` 에 실립니다). → [12 §1-C](./12-syntax-and-stdlib.md)

### 4.4 진단 줄도 프레젠터가 만든다

budget_app/cli/presenter.py:109-115

```python
def import_result_line(report: ImportReport, mode: str) -> str:
    return messages.MSG_IMPORT_DONE.format(
        mode=mode,
        imported=report.imported,
        duplicated=report.duplicated,
        skipped=report.skipped,
    )
```

> **🔎 문법의 출처** — `"...{mode}...".format(mode=..., imported=...)` 의 중괄호 서식은 PEP 3101 이 파이썬 2.6/3.0 에 넣은 것으로, 그 전에는 `"%s개" % n` 같은 `%` 연산자를 썼습니다. `str.format` 은 서식 문자열을 파싱해 `{이름}` 자리마다 인자를 꺼내 각 값의 `__format__` 을 부릅니다. **이 소스가 f-string 대신 `.format` 을 쓰는 것은 취향이 아니라 구조 때문입니다** — 문장은 `cli/messages.py` 에 상수로 먼저 정의되어 있고 값은 나중에 다른 파일에서 채워집니다. f-string 은 리터럴이 놓인 자리에서 즉시 평가되므로 "문장을 한곳에 모아 둔다"는 이 설계와 애초에 양립하지 않습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

**프레젠터는 문자열만 만들고, 어느 채널로 보낼지는 호출자가 정합니다.** docstring 이 그 계약을 명시합니다("호출자가 stderr 로 보낸다").

`import_problem_lines` 만 리스트를 반환하는데(다른 함수는 제너레이터), 호출자가 "비었는지" 먼저 확인할 수 있어야 하기 때문입니다. 제너레이터는 소비하기 전에는 비었는지 알 수 없습니다.

---

## 5. `output.py` — 채널 결정

만들어진 문장을 어느 출구로 내보낼지 이 파일에서만 정합니다. 문장을 조립하는 일은 하지 않습니다.

> **💡 쉽게 말하면** — 관공서에 창구가 둘 있다고 생각해 보세요. 하나는 **서류를 내주는 창구**, 다른 하나는 **문제를 알려 주는 창구**입니다. 나눠 두면 받은 서류만 봉투에 담아 그대로 다음 기관에 낼 수 있습니다. 안내문이 서류 사이에 섞여 있으면 일일이 골라내야 하고, 골라낼 방법도 마땅치 않습니다. 결과를 파일로 받아 두거나(`list > out.txt`) 다음 프로그램에 넘길 때(`list | head`) 필요한 것이 정확히 이 구분입니다.
> 다만 이 비유는 **두 창구가 같은 화면을 쓴다**는 점에서 깨집니다 — 터미널에서 그냥 실행하면 두 출구의 글자가 한 화면에 섞여 보이고, 나뉘어 있다는 사실은 파일로 받거나 한쪽을 버릴 때에야 드러납니다.

### 5.1 세 채널

budget_app/cli/output.py:1-2

```python
"""출력 채널 — 어떤 메시지가 어느 스트림으로 나가는지 이 모듈에서만 정한다.

```

### 5.2 `out()` 을 추가한 이유

budget_app/cli/output.py:19-21

```python

## ``out()`` 을 추가한 이유 (리팩터)

```

**"선언과 코드의 불일치"를 고친 사례**입니다. 문서가 규칙을 말하는데 코드가 지키지 않으면, 그 문서를 믿고 코드를 읽는 사람이 오해합니다.

### 5.3 `err()` 의 flush

> **💡 쉽게 말하면** — 같은 사무실에서 두 사람이 편지를 부칩니다. 결과를 담당하는 사람은 우편물을 상자에 모아 두었다가 상자가 차면 한꺼번에 부치고, 문제를 알리는 사람은 쓰는 즉시 한 통씩 부칩니다. 각자에게는 합리적이지만 받는 쪽에서는 나중에 쓴 항의 편지가 먼저 쓴 결과 편지보다 앞서 도착합니다. `flush` 는 "지금 상자에 든 것부터 다 부쳐라"라고 이르는 일이고, 그래서 항의 편지를 쓰기 직전에 한 번 이릅니다.
> 다만 이 비유는 **상자가 늘 쓰인다**는 점에서 깨집니다 — 결과를 터미널에 바로 찍을 때는 결과 쪽도 한 줄씩 곧바로 부치므로 순서가 뒤집히지 않고, 파일이나 파이프로 보낼 때만 상자가 생깁니다.

budget_app/cli/output.py:53-66

```python
def err(message: str = "") -> None:
    """사용자용 진단 한 줄을 stderr 로 출력한다.

    stderr 로 쓰기 전에 stdout 을 먼저 비운다. stdout 은 터미널이 아니면 블록
    버퍼링이라(stderr 는 버퍼링 없음), 비우지 않으면 ``cmd 2>&1 | less`` 처럼 두
    채널을 다시 합쳤을 때 진단이 결과보다 앞으로 튀어나온다.
    """
    try:
        sys.stdout.flush()
    except (BrokenPipeError, ValueError):
        # 하류 파이프가 이미 닫혔거나 stdout 이 닫힌 상태.
        # 그래도 stderr 는 살아 있으므로 진단 출력은 계속한다(이게 채널 분리의 이점).
        pass
    print(message, file=sys.stderr)
```

**버퍼링 차이가 순서를 뒤집는 문제.**

```
[flush 없으면]
  프로그램:  out("결과 1")   → stdout 버퍼에 쌓임 (터미널이 아니면 4KB 모아서 씀)
             err("[오류] ...") → stderr 즉시 출력
  화면:      [오류] ...
             결과 1              ← 순서가 뒤집힘!
```

**말이 아니라 실행으로.** 아래 다섯 줄을 파일로 저장해 `2>&1 | cat` 으로 돌립니다(두 채널을 다시 합치고, stdout 을 터미널이 아닌 파이프에 붙이는 것이 핵심입니다).

```python
# 일반론 재현 코드 — 이 소스에는 없습니다
import sys
print("stdout line_buffering =", sys.stdout.line_buffering, file=sys.stderr)
print("stderr line_buffering =", sys.stderr.line_buffering, file=sys.stderr)
print("RESULT 1")
print("[ERR] diagnostic", file=sys.stderr)
print("RESULT 2")
```

실제 출력(CPython 3.13.1):

```
stdout line_buffering = False      ← 파이프에 붙으면 블록 버퍼
stderr line_buffering = True       ← 언제나 라인 버퍼
[ERR] diagnostic
RESULT 1
RESULT 2
```

프로그램이 낸 순서는 `RESULT 1` → `[ERR]` → `RESULT 2` 인데 화면 순서가 뒤집혔습니다. `RESULT 1` 은 stdout 버퍼에 앉아 있다가 **프로세스가 끝날 때** 한꺼번에 나갔기 때문입니다. 같은 코드에서 `print("RESULT 1")` 바로 뒤에 `sys.stdout.flush()` 한 줄만 넣으면:

```
RESULT 1
[ERR] diagnostic
RESULT 2
```

순서가 복구됩니다. **`output.err` 가 맨 앞에서 하는 일이 정확히 이 한 줄**입니다.

> **⚙️ 내부 동작** — 왜 stdout 만 그런가. CPython 은 시작할 때 `sys.stdout`/`sys.stderr` 를 `io.TextIOWrapper` 로 만드는데, 정책이 서로 다릅니다. **stdout** 은 `isatty()` 가 참이면 라인 버퍼, 거짓(파일·파이프)이면 아래 `BufferedWriter` 의 블록 버퍼(기본 8192바이트)에 모았다가 씁니다. **stderr** 는 대상이 무엇이든 `line_buffering=True` 로 만들어져 개행마다 곧바로 흘러나갑니다(둘 다 아래는 같은 `BufferedWriter` 이고, 차이는 텍스트 층의 이 플래그 하나입니다 — 로컬 3.13.1 에서 `sys.stderr.line_buffering` → `True`, 파이프에 붙은 `sys.stdout.line_buffering` → `False` 로 확인). 소스 주석이 "stderr 는 버퍼링 없음"이라고 적은 것은 이 **줄 단위 즉시 방출**을 줄여 말한 것입니다. 터미널에서 직접 실행할 때 이 버그가 안 보이는 이유도 여기 있습니다 — 터미널이면 stdout 도 라인 버퍼라 순서가 맞습니다. **리다이렉트/파이프에서만 드러나는 버그**인 것입니다. → [12 §3](./12-syntax-and-stdlib.md)

> **🔎 문법의 출처** — `print(message, file=sys.stderr)` 의 `file=` 키워드는 `print` 가 **문장에서 함수로 바뀌면서** 생겼습니다(PEP 3105, 파이썬 3.0). 파이썬 2 의 `print >>sys.stderr, message` 라는 특수 문법이 그냥 키워드 인자가 된 것입니다. `print` 가 하는 일은 단순합니다 — 각 인자를 `str()` 로 바꿔 `sep`(기본 `' '`)으로 잇고 `end`(기본 `'\n'`)를 붙여 `file.write()` 를 부릅니다. `file` 의 기본값은 `sys.stderr` 처럼 미리 굳어 있지 않고 **호출할 때마다 `sys.stdout` 을 다시 조회**하므로, 테스트에서 `sys.stdout` 을 갈아 끼우면 이미 정의된 `out()` 도 따라옵니다. → [12 §1-A](./12-syntax-and-stdlib.md)

`try/except` 로 감싼 이유는 **이미 파이프가 끊긴 상태**에서 `flush()` 가 또 `BrokenPipeError` 를 낼 수 있기 때문입니다. 그래도 stderr 는 살아 있으므로 진단은 계속 출력합니다 — 주석이 지적하듯 이것이 **채널 분리의 이점**입니다.

`except` 에 `ValueError` 가 함께 적힌 것도 이유가 있습니다. 파일 객체가 **닫힌 뒤**에 `flush()` 를 부르면 파이썬은 `OSError` 가 아니라 `ValueError: I/O operation on closed file` 을 던집니다. 두 실패는 원인이 다르지만(끊김 / 닫힘) 여기서의 대응은 같으므로 튜플 하나로 묶었습니다.

### 5.4 `setup_logging` — 로거를 붙이는 유일한 지점

budget_app/cli/output.py:74-100

```python
def _env_debug() -> bool:
    value = os.environ.get(config.DEBUG_ENV_VAR, "").strip().lower()
    return value not in config.FALSY_ENV_VALUES


def setup_logging(debug: bool = False) -> bool:
    """루트 로거에 핸들러를 붙인다 — ``main()`` 에서 한 번만 호출한다.

    이 호출이 없으면 ``logging.getLogger(...)`` 로 만든 로거에는 핸들러가 하나도
    없고 유효 레벨도 WARNING 이라, ``logger.debug(..., exc_info=True)`` 로 보존한
    스택트레이스가 **어디에도 남지 않는다**. "사용자에게는 감추고 로그로 보존한다"는
    ``handle_errors`` 의 의도는 이 함수가 있어야 비로소 성립한다.

    - ``debug=False`` → WARNING. 손상된 JSONL 줄 경고 등만 stderr 로 나온다.
    - ``debug=True``  → DEBUG. ``@log_call``/``@measure_time`` 의 호출 로그와
      예기치 못한 예외의 스택트레이스까지 stderr 로 나온다.

    반환: 실제로 디버그 모드가 켜졌는지 여부(플래그 또는 환경변수).
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

> **⚙️ 내부 동작** — `logging.basicConfig` 는 **루트 로거 하나**를 설정하는 편의 함수입니다. 원래 규칙은 "루트에 핸들러가 이미 있으면 아무것도 하지 않고 조용히 돌아간다"인데, 그래서 라이브러리 하나가 먼저 `basicConfig` 를 불러 버리면 뒤에 오는 설정이 **경고도 없이 무시**됩니다. `force=True`(파이썬 3.8 추가)는 그 앞에 정리 단계를 끼워 넣습니다. → [12 §2-B](./12-syntax-and-stdlib.md)

`force=True` 가 실제로 실행하는 코드는 네 줄입니다.

```python
# CPython 3.13.1 Lib/logging/__init__.py — basicConfig 안
if force:
    for h in root.handlers[:]:
        root.removeHandler(h)
        h.close()
```

단순히 떼는 것이 아니라 **`close()` 까지** 부릅니다 — 파일 핸들러였다면 파일 디스크립터가 반납되고, 버퍼가 있었다면 비워집니다. `root.handlers[:]` 라는 슬라이스 사본을 도는 것도 필수입니다. `removeHandler` 가 원본 리스트를 줄이는데 그 리스트를 그대로 순회하면 항목을 건너뛰기 때문입니다.

이 소스에서 `force=True` 가 필요한 이유는 주석대로 **재호출·테스트**입니다 — 한 프로세스 안에서 `main(["list"])`, `main(["--debug", "list"])` 를 연달아 부르는 테스트에서 두 번째 `--debug` 가 먹히려면 첫 번째 설정을 걷어내야 합니다. 또 `setup_logging` 이 붙이는 것은 **루트 로거**의 핸들러이고, `budget_app.*` 자식 로거들은 자기 핸들러 없이 레코드를 부모로 올려 보내(propagate) 여기서 처리됩니다. 그래서 "로거를 붙이는 지점이 하나"라는 말이 성립합니다.

**환경변수 처리의 함정.**

budget_app/cli/config.py:16-19

```python

# 디버그 스위치 — `--debug` 와 동등한 환경변수
DEBUG_ENV_VAR = "BUDGET_APP_DEBUG"
FALSY_ENV_VALUES = frozenset({"", "0", "false", "no", "off"})
```

`if os.environ.get("BUDGET_APP_DEBUG"):` 라고만 쓰면 `BUDGET_APP_DEBUG=0` 이 **켜집니다**(빈 문자열이 아니므로 truthy). 흔한 실수를 상수로 방어했습니다.

> **⚙️ 내부 동작** — `os.environ` 은 호출할 때마다 OS 에 묻는 함수가 아니라, **파이썬이 시작할 때 프로세스 환경을 통째로 복사해 만든 `os._Environ` 매핑**입니다. 그래서 프로그램이 도는 도중 바깥 셸에서 값을 바꿔도 반영되지 않습니다. 반대로 `os.environ["X"] = "1"` 로 쓰면 `__setitem__` 이 파이썬 딕셔너리와 함께 C 층의 `putenv` 도 부르므로, 이후 `subprocess` 로 띄우는 자식 프로세스는 그 값을 물려받습니다. `os.environ.get(name, "")` 의 두 번째 인자는 **키가 없을 때의 기본값**이라 `.strip().lower()` 가 `None` 에 대해 터지지 않게 해 줍니다.
>
> `value not in config.FALSY_ENV_VALUES` 의 `FALSY_ENV_VALUES` 가 `frozenset` 인 것도 이유가 있습니다. `in` 은 자료형마다 다른 연산으로 풀립니다 — 리스트/튜플이면 앞에서부터 하나씩 `==` 비교(O(n)), 집합이면 **해시 한 번**(O(1))입니다. 항목이 다섯 개뿐이라 속도 차이는 무의미하지만, `frozenset` 은 **불변**이라 모듈 상수가 실수로 변경되는 일을 막아 줍니다. → [12 §3](./12-syntax-and-stdlib.md)

**로그 포맷이 두 가지인 이유.**

budget_app/cli/messages.py:16-17

```python
LOG_FORMAT = "[%(levelname)s] %(message)s"
LOG_FORMAT_DEBUG = "[%(levelname)s] %(asctime)s %(name)s:%(lineno)d %(message)s"
```

평상시(WARNING)에는 짧게, `--debug` 에서는 "어디서 나온 로그인지"(모듈:줄번호)까지 보여 줍니다.

---

## 6. `app.py` — 오케스트레이션과 진입점

프로그램이 시작해서 끝날 때까지의 **순서**를 정하는 파일입니다. 오케스트레이션이란 직접 일하지 않고 누가 할 차례인지만 정해 주는 일을 말합니다.

(리팩터 전 단일 모듈의 이름이 `cli.py` 였습니다. 그 역할 중 "레지스트리(이름과 담당 함수를 짝지어 적어 둔 명부) + 진입점"만 남은 것이 지금의 `cli/app.py` 이고, 명령별 함수는 `cli/handlers.py` 로 갔습니다.)

### 6.1 핸들러는 3~6줄

budget_app/cli/app.py:1-13

```python
"""CLI 진입점 — 명령 레지스트리와 ``main``.

## 명령 → 핸들러 대응

``parser`` 가 남긴 문자열 키(``"category.add"``)를 ``HANDLERS`` 가 함수로 바꾼다.
파서가 함수 객체를 들고 있던 이전 방식과 달리 두 모듈이 서로를 import 하지 않으므로
순환이 없고, 하위 명령마다 핸들러가 하나씩 대응해 ``if/elif`` 분기가 사라졌다.

명령을 추가하는 절차는 셋이다 — ``parser`` 에 문법, ``handlers`` 에 함수,
여기 ``HANDLERS`` 에 한 줄. ``main`` 은 영원히 그대로다.
"""

from __future__ import annotations
```

핸들러 13개는 `cli/handlers.py`(190줄)에 있고, 줄 수는 이렇습니다:

| 핸들러 | 줄 | 핸들러 | 줄 |
|---|---|---|---|
| `cmd_list` | 3 | `cmd_delete` | 4 |
| `cmd_summary` | 4 | `cmd_budget_set` | 4 |
| `cmd_backup` | 4 | `cmd_category_list` | 3 |
| `cmd_export` | 5 | `cmd_category_add` | 7 |
| `cmd_search` | 12 | `cmd_import` | 9 |
| `cmd_add` | 18 | `cmd_category_remove` | 14 |
| `cmd_update` | 17 | | |

가장 긴 `cmd_add`(18줄)도 대부분이 서비스에 넘길 인자 나열입니다.

### 6.2 `main` — 다섯 단계

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

```
1) 파싱          parser.build_parser().parse_args(argv)
2) 로깅 준비      output.setup_logging(...)      ← 로거를 붙이는 유일한 지점
3) 조립          AppContext(data_dir)           ← 합성 루트
4) 저장소 준비    ctx.prepare()                  ← needs_storage 일 때만
5) 디스패치       HANDLERS[args.handler](ctx, args)
```

**순서가 중요합니다.** `setup_logging` 이 3번보다 앞에 있어야 저장소 초기화 중 발생하는 경고 로그도 보입니다. 3·4·5 번은 `main` 이 아니라 `@handle_errors` 가 붙은 `_dispatch`(`app.py:61-81`) 안에 있습니다 — 파일을 여는 코드를 방패 밖에 두지 않기 위해서입니다.

**`argv: list[str] | None = None`** 은 테스트를 위한 설계입니다. `None` 이면 argparse 가 `sys.argv[1:]` 를 쓰고, 리스트를 주면 그것을 파싱합니다. 프로세스를 띄우지 않고 `main(["list", "--limit", "5"])` 로 호출할 수 있습니다.

> **🔎 문법의 출처** — 타입 표기가 `Optional[List[str]]` 이 아니라 `list[str] | None` 인 것은 두 PEP 이 겹친 결과입니다. 소문자 `list[str]` 은 PEP 585(3.9)가 표준 컨테이너에 첨자를 허용하면서, `X | None` 은 PEP 604(3.10)가 `|` 를 타입 합집합으로 쓰게 하면서 가능해졌습니다. 그 위에 파일 첫머리의 `from __future__ import annotations`(PEP 563)가 **모든 어노테이션을 문자열로만 보관**하게 만들어, 실행 시점에 평가되지 않으니 3.10 미만에서도 구문 오류가 나지 않습니다. 이 프로젝트의 요구 버전이 `>=3.10` 이므로 실제로는 future import 없이도 동작하지만, 어노테이션 평가 비용을 없애고 따옴표 표기를 영구히 불필요하게 만드는 효과는 그대로 남습니다. → [12 §1-A](./12-syntax-and-stdlib.md)

> **⚙️ 내부 동작** — `parse_args(argv)` 에 `None` 을 주면 argparse 가 내부에서 `args = sys.argv[1:]` 로 바꿔치기합니다(`_parse_known_args2` 의 첫 세 줄). `sys.argv[0]` 은 프로그램 이름이라 잘라 내는 것이고, 그래서 usage 에 찍히는 이름은 `sys.argv[0]` 이 아니라 `ArgumentParser(prog=config.PROG_NAME)` 으로 **직접 지정한** `"budget_app"` 입니다. 지정하지 않으면 argparse 는 `os.path.basename(sys.argv[0])` 을 쓰는데, `python -m budget_app` 으로 실행하면 그 값이 `__main__.py` 라서 사용자에게 낯선 이름이 나옵니다.

### 6.3 `HANDLERS` — 문자열 키 레지스트리

budget_app/cli/app.py:26-27
```python
Handler = Callable[[AppContext, argparse.Namespace], int]

```

**`Handler` 타입 별칭이 계약을 한 줄로 적어 둡니다** — "컨텍스트와 파싱 결과를 받아 종료 코드를 돌려주는 함수". 새 핸들러를 추가할 때 이 모양만 맞추면 됩니다.

> **🔎 문법의 출처** — `Handler = Callable[[AppContext, argparse.Namespace], int]` 는 특별한 선언 문법이 아니라 **평범한 대입문**입니다. 오른쪽은 실행 시점에 `types.GenericAlias` 객체 하나를 만들고, `Handler` 는 그 객체를 가리키는 모듈 전역 변수가 됩니다. 그래서 아래 `dict[str, Handler]` 처럼 다른 타입 표기 안에서 그대로 쓸 수 있습니다. `Callable[[A, B], R]` 의 대괄호 두 겹은 "인자 목록 / 반환 타입"을 뜻합니다 — 안쪽 리스트가 인자, 뒤가 반환입니다. 파이썬 3.12 는 `type Handler = ...`(PEP 695)라는 전용 문법도 추가했지만 **이 소스는 쓰지 않습니다**(요구 버전이 `>=3.10`). → [12 §1-C](./12-syntax-and-stdlib.md)

**키 이름 규칙**: 1단 명령은 `"add"`, 2단은 `"category.add"`. 점 표기가 계층을 드러냅니다.

**명령을 추가하는 절차:**

1. `parser.py` 에 `_add_xxx(sub)` 함수 작성 → `set_defaults(handler="xxx")`
2. `build_parser()` 에서 호출
3. `handlers.py` 에 `cmd_xxx(ctx, args)` 작성
4. `app.py` 의 `HANDLERS` 에 한 줄 추가

`main()` 은 영원히 그대로입니다. **3번에 `@handle_errors` 를 붙이는 단계가 없다는 점**을 눈여겨보세요. 예전에는 핸들러 13개에 각각 붙였지만 지금은 `_dispatch` 한 곳에만 붙습니다(`app.py:61`). 정책이 한 곳에서 적용되면 "새 핸들러에 데코레이터를 빠뜨리는" 실수 자체가 생길 수 없습니다 — `handlers.py` 전체에 `@handle_errors` 는 **한 개도 없습니다**.

> **🔎 문법의 출처** — `@handle_errors` 같은 데코레이터 표기는 PEP 318 로 파이썬 2.4 에 들어왔습니다. `@deco` 를 함수 정의 위에 얹은 것은 `def f(): ...` 뒤에 `f = deco(f)` 를 쓴 것과 **정확히 같은 코드로 풀립니다**(desugar). 그래서 `_dispatch` 라는 이름이 실제로 가리키는 것은 원래 함수가 아니라 `handle_errors` 가 돌려준 `wrapper` 이고, 안쪽에서 `functools.wraps` 로 이름·docstring 을 옮겨 심어야 정체가 유지됩니다. 자세한 것은 [06. 횡단 관심사와 예외 처리](./06-decorators.md), 문법 계보는 [12 §1-C](./12-syntax-and-stdlib.md).

### 6.4 `AppContext` — 합성 루트

합성 루트란 프로그램에 필요한 부품들을 한 곳에서 한 번에 조립하는 자리입니다. [04 §6](./04-architecture.md)에서 다뤘으므로 여기서는 요점만 짚습니다.

budget_app/context.py:42-57

```python
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
```

**리팩터 전에는 핸들러마다 `AppContext(args.data_dir)` 를 만들었습니다**(10곳). 지금은 `_dispatch` 가 한 번 만들어 핸들러에 넘깁니다(`app.py:78`). 그래서 핸들러 시그니처가 `(ctx, args)` 두 인자입니다.

### 6.5 기간 조건 조립

budget_app/cli/handlers.py:153-157

```python
def cmd_export(ctx: AppContext, args: argparse.Namespace) -> int:
    flt = _export_filter(args)
    count = ctx.io_service.export_csv(Path(args.out), flt, include_id=args.include_id)
    output.out(messages.MSG_EXPORT_DONE.format(out=args.out, count=count))
    return config.EXIT_OK
```

**날짜 검증이 없습니다.** `SearchFilter.__post_init__` 이 `parse_date` 를 호출하므로, 잘못된 날짜는 필터를 만드는 순간 `ValidationError` 가 됩니다.

리팩터 전에는 이랬습니다.

```python
# 리팩터 전 — CLI 가 직접 검증
    if date_from:
        Transaction.validate_date(date_from)
    if date_to:
        Transaction.validate_date(date_to)
    flt = SearchFilter(date_from=date_from, date_to=date_to)
```

같은 검증이 `cmd_search` 에도 중복돼 있었습니다. 필터가 스스로 검증하게 하자 **두 곳의 중복이 함께 사라졌습니다.**

### 6.6 BrokenPipe — 전말

**시나리오.** `python -m budget_app list | head -3` 을 실행하면:

```
1) budget_app 이 거래 100건을 stdout 에 씀
2) head 가 3줄을 읽고 종료 → 파이프의 읽는 쪽이 닫힘
3) budget_app 이 4번째 줄을 쓰려 함 → BrokenPipeError
```

이것은 **오류가 아닙니다.** 하류 프로세스가 "충분히 받았다"고 알린 것입니다. 유닉스 파이프라인에서 완전히 정상적인 상황입니다.

> **💡 쉽게 말하면** — 100줄짜리 명단을 소리 내어 읽어 주는 중인데, 듣던 사람이 앞의 세 줄만 확인하고 자리를 떠났습니다. 읽던 쪽이 놀라 소리를 지를 일은 아닙니다 — 충분히 받았다는 뜻이니 조용히 그만두면 됩니다. 그래서 이 프로그램은 남은 말을 아무 데도 연결되지 않은 곳으로 돌려놓고 "정상 종료" 라는 표시(종료 코드 0)를 남긴 채 끝냅니다.
> 다만 이 비유는 **말을 멈추는 방법**에서 깨집니다 — 입을 다무는 것으로는 부족합니다. 파이썬 쪽 변수만 바꿔서는 안 되고, 운영체제가 "1번 출구"로 알고 있는 자리 자체를 갈아 끼워야 합니다. 아래 (2) 의 `os.dup2` 가 하는 일이 그것입니다.

> **⚙️ 내부 동작 — 왜 시그널이 아니라 예외로 오는가.** POSIX 의 원래 규칙은 예외가 아니라 **시그널**입니다. 읽는 쪽이 닫힌 파이프에 `write(2)` 를 하면 커널이 쓰는 프로세스에 `SIGPIPE` 를 보내고, 기본 처분(default disposition)이 "프로세스 종료"라서 프로그램은 **아무 메시지도 없이 즉시 죽습니다**. `head` 로 잘라도 앞 명령이 조용히 끝나는 셸 도구들이 대개 이 기본 동작을 그대로 씁니다.
>
> 그런데 파이썬은 인터프리터가 시작할 때 `SIGPIPE` 의 처분을 **`SIG_IGN`(무시)로 바꿉니다**. 시그널이 무시되면 커널은 `write(2)` 를 `-1` 로 실패시키고 `errno` 에 **`EPIPE`(32)** 를 세우며, 파이썬의 I/O 층이 그 errno 를 보고 `OSError` 의 자식인 **`BrokenPipeError`** 를 던집니다(errno→예외 클래스 대응은 `errno` 모듈의 값에 따라 인터프리터가 자동으로 고릅니다). 즉 이 소스가 `except BrokenPipeError` 라고 쓸 수 있는 것은 **파이썬이 시그널을 예외로 번역해 주기 때문**이고, 그 대가로 "조용히 죽기"를 스스로 처리해야 하는 것이 아래 세 단계입니다.
>
> (Windows 에는 `SIGPIPE` 자체가 없습니다 — 로컬에서 `hasattr(signal, "SIGPIPE")` → `False`. 이 절의 `PIPESTATUS` 예시를 포함한 서술은 POSIX 셸 기준입니다.) → [12 §3](./12-syntax-and-stdlib.md)

**대응이 세 단계로 나뉩니다.**

**(1) `handle_errors` 는 처리하지 않고 다시 던집니다.**

budget_app/cli/error_handler.py:56-60

```python
        # ---------- (1) 종료 신호 — 오류가 아님 ----------
        except BrokenPipeError:
            # 하류 파이프(`list | head`)가 먼저 닫힘. 여기서 출력하면 또 깨지므로
            # 최상위(main)로 넘겨 조용히 처리하게 한다.
            raise
```

여기서 `output.err(...)` 를 부르면 그 안의 `sys.stdout.flush()` 가 또 `BrokenPipeError` 를 냅니다. **2차 사고**입니다.

**(2) `main` 이 잡아 stdout 을 블랙홀로 갈아끼웁니다.**

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

**왜 이게 필요한가.** 파이썬 인터프리터는 종료 시 stdout 버퍼를 비웁니다. 파이프가 깨진 상태면 그때 또 예외가 나고, 파이썬은 `Exception ignored in: <_io.TextIOWrapper ...>` 라는 메시지를 stderr 에 출력합니다. 사용자에게는 정상 종료였는데 마지막에 이상한 메시지가 뜨는 것입니다.

`os.dup2(devnull, sys.stdout.fileno())` 는 **파일 디스크립터 1번(stdout)이 `/dev/null` 을 가리키게** 만듭니다. 이후의 모든 stdout 쓰기는 조용히 버려집니다.

> **⚙️ 내부 동작 — 왜 `sys.stdout = open(os.devnull, "w")` 로는 안 되는가.** 여기가 이 함수의 핵심이고, 두 층을 구분해야 보입니다.
>
> - **파이썬 층**: `sys.stdout` 은 그냥 모듈 전역 변수입니다. 다른 객체를 대입해도 그 시점 이후 `print()` 가 쓰는 대상만 바뀝니다.
> - **OS 층**: 실제로 커널이 아는 것은 **파일 디스크립터 정수 1번**뿐이고, 원래 `sys.stdout` 객체는 여전히 그 1번을 붙들고 있습니다.
>
> 문제의 마지막 flush 는 **인터프리터가 종료하면서 원래 stdout 객체에 대해** 일으키는 것이므로, 변수만 갈아 끼우면 그 객체가 깨진 파이프에 다시 쓰다가 또 실패합니다. `os.dup2(devnull, 1)` 은 반대로 **1번 자리에 앉은 대상 자체를 바꿉니다** — POSIX `dup2(2)`(Windows 는 CRT 의 `_dup2`)는 "먼저 1번을 닫고, `devnull` 의 복제본을 1번 자리에 놓는" 두 동작을 원자적으로 합니다. 그래서 파이썬 객체는 손대지 않은 채, 그 객체가 쓰는 곳만 블랙홀이 됩니다.
>
> `os.open`(소문자, `os` 모듈)은 내장 `open()` 과 다릅니다 — 파일 객체가 아니라 **정수 fd 를 그대로** 돌려주는 시스템콜 그대로의 얇은 껍질입니다. `os.devnull` 은 플랫폼별 이름 문자열(`'/dev/null'` 또는 `'nul'`)이라 이 코드가 양쪽에서 동작합니다. `except OSError: pass` 인 것은 이미 fd 가 닫혔거나 `/dev/null` 을 열 수 없는 극단적 상황에서 **정리 코드가 새 오류를 만들지 않게** 하려는 것입니다. → [12 §3](./12-syntax-and-stdlib.md)

**(3) 종료 코드는 0.**

```python
        _silence_broken_pipe()
        return config.EXIT_OK
```

`head` 가 먼저 끝난 것은 실패가 아니므로 0을 반환합니다.

**검증:**

```bash
$ python -m budget_app list | head -1
TX-000004 | 2024-02-03 | expense | food | 8000 | 김밥
$ echo ${PIPESTATUS[0]}
0                          ← budget_app 자체는 정상 종료
```

**`output.err` 안의 방어와 짝을 이룹니다.**

budget_app/cli/output.py:60-65

```python
    try:
        sys.stdout.flush()
    except (BrokenPipeError, ValueError):
        # 하류 파이프가 이미 닫혔거나 stdout 이 닫힌 상태.
        # 그래도 stderr 는 살아 있으므로 진단 출력은 계속한다(이게 채널 분리의 이점).
        pass
```

파이프가 깨진 뒤에도 **오류 메시지는 사용자에게 전달됩니다.** 이것이 stdout/stderr 를 나눈 세 번째 이유(§5.1)의 실제 효과입니다.

---

## 7. 정리 — 과제 방어용 요약

**Q. CLI 계층을 왜 여섯 모듈로 나눴나요?**

리팩터 전 `cli.py` 512줄은 고칠 이유가 넷이었습니다 — 명령줄 문법, 입력 정책, 화면 표시, 처리 순서. 각각을 `parser`/`prompts`/`presenter`/`handlers` 로 나눴습니다. `app` 에는 명부와 진입점만 남기고, 채널 결정(`output`)과 오류 표현(`error_handler`)도 따로 뺐습니다. 결과적으로 핸들러가 3~6줄이 됐고, `cmd_summary` 는 25줄에서 3줄이 됐습니다.

**Q. argparse 서브커맨드 디스패치를 어떻게 구현했나요?**

파서는 `set_defaults(handler="category.add")` 로 **문자열 키**만 남기고, `cli/app.py` 의 `HANDLERS` 딕셔너리가 키를 함수로 바꿉니다(함수 본체는 `cli/handlers.py`). 함수 객체를 직접 심으면 파서와 핸들러가 서로를 import 해야 해서 순환이 생기거나 한 파일에 뭉쳐야 합니다. 부수 효과로 하위 명령별 핸들러가 생기면서 `if/elif` 분기와 **도달 불가능한 죽은 코드**가 사라졌습니다.

**Q. 하위 파서에 `default=argparse.SUPPRESS` 를 왜 주나요?**

`add_subparsers` 가 만드는 `_SubParsersAction` 은 하위 명령을 만나면 하위 파서를 **재귀 호출**하고, 하위 파서가 자기 namespace 에 채운 값을 **전부 상위 namespace 위에 덮어씁니다**. 그래서 하위 파서에도 평범한 기본값을 주면 `budget_app --debug list` 에서 `--debug` 가 조용히 `False` 로 되돌아갑니다. `SUPPRESS` 는 "명령줄에 값이 없으면 namespace 에 속성을 아예 만들지 마라"는 뜻이라, 덮어쓸 것 자체가 생기지 않습니다. 실제 기본값은 최상위 파서 한 곳에만 둡니다(§2.4.1 에 실행 재현이 있습니다).

**Q. `--limit 0` 은 어느 종료 코드로 끝나나요? `@handle_errors` 가 처리하나요?**

종료 코드는 2 이지만 **`@handle_errors` 를 지나지 않습니다.** `type=positive_int` 가 `ArgumentTypeError` 를 던지면 argparse 가 그것을 잡아 usage 를 찍고 `sys.exit(2)` 를 부릅니다. 이유가 둘입니다 — ① 그 일이 `parse_args` 안, 즉 방패가 붙은 `_dispatch` **앞**에서 일어나고, ② argparse 가 던지는 `SystemExit` 은 `Exception` 이 아니라 `BaseException` 의 자식이라 `except Exception` 에 걸리지 않습니다. 결과적으로 종료 코드 2 에 이르는 길이 두 개(argparse 경로 / `ValidationError` 경로)인데, "사용자가 값을 고치면 해결되는 문제"라는 같은 부류를 셸에 같은 숫자로 알리려고 일부러 맞춰 둔 것입니다(§2.8).

**Q. 대화형 입력에서 무한 루프를 어떻게 막았나요?**

두 가지입니다. EOF(파이프 입력이 끝남)는 `ask` 가 `InputAborted`(AppError 의 자식)로 즉시 중단합니다. 잘못된 값이 계속 들어오는 경우는 `for _ in range(MAX_INPUT_RETRIES)` 로 10회에서 멈춥니다. `while True` 를 쓰지 않은 것이 핵심입니다.

**Q. `list | head` 에서 왜 오류가 나고 어떻게 처리했나요?**

`head` 가 먼저 종료하면 파이프의 읽는 쪽이 닫혀 `BrokenPipeError` 가 납니다. 원래 POSIX 에서는 커널이 `SIGPIPE` 를 보내 프로세스를 조용히 죽이지만, 파이썬이 시작할 때 그 시그널을 무시로 바꿔 두어 대신 `EPIPE` errno 가 오고 그것이 `BrokenPipeError` 로 올라옵니다. 오류가 아니라 정상적인 종료 신호이므로, `handle_errors` 는 처리하지 않고 다시 던지고(여기서 출력하면 2차 사고), `main` 이 잡아 `os.dup2` 로 **fd 1번 자체**를 `/dev/null` 로 갈아끼운 뒤 종료 코드 0을 반환합니다. `sys.stdout` 변수만 바꾸면 안 되는 이유는, 인터프리터가 종료할 때 flush 하는 대상이 원래 stdout **객체**이고 그 객체는 여전히 fd 1번을 붙들고 있기 때문입니다. 이 처리가 없으면 인터프리터 종료 시 `Exception ignored` 메시지가 뜹니다.

**Q. 왜 프레젠터가 출력하지 않고 반환하나요?**

채널 결정은 `output` 의 책임이라 프레젠터가 `print` 하면 두 모듈이 같은 책임을 나눠 갖게 됩니다. 또 반환값이 문자열이면 프로세스를 띄우지 않고 화면 형식을 검증할 수 있습니다. 제너레이터로 반환하는 것은 상류 스트리밍을 끊지 않기 위해서이며, `--limit` 에서 `break` 하면 상류가 더 이상 `next()` 를 받지 않아 그 자리에서 멈춥니다. 다만 `list` 경로에서 아껴지는 것은 나머지 줄의 문자열 조립·출력이지 파일 읽기가 아닙니다 — `stream_sorted` 가 정렬 때문에 이미 전체를 읽어 리스트로 모으기 때문입니다(§4.2).

---

**다음 문서**: [10. 고급 설계 주제](./10-advanced-design.md) — crash 시나리오, 성능 한계, 트레이드오프.
