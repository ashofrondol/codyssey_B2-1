# budget_app — 파일 기반 가계부 콘솔 프로그램

Python 표준 라이브러리만으로 만든 콘솔 가계부입니다. JSONL 영구 저장, 제너레이터 스트리밍, 데코레이터 분리, 생성자 불변식 검증, 설정·문자열 중앙화(config), 타입 힌트, 모듈화 구조를 갖췄습니다.

## 1. 실행 환경

- Python 3.10 이상 (표준 라이브러리만 사용)
- 외부 의존성 없음 (`pip install` 불필요)

## 2. 실행 방법

프로젝트 루트(`codyssey_B2-1/`)에서 실행합니다.

```bash
python -m budget_app <command> [options]
python -m budget_app --help
python -m budget_app <command> --help
```

데이터 폴더는 `--data-dir` 로 변경할 수 있습니다(기본 `./data`).

```bash
python -m budget_app list --data-dir ./mydata
```

## 3. 저장 파일 위치 / 형식

기본 저장 폴더: `./data/`

| 파일 | 내용 | 형식 |
| --- | --- | --- |
| `data/transactions.jsonl` | 거래 내역 | JSON Lines (한 줄에 거래 1건) |
| `data/categories.jsonl` | 카테고리 목록 | JSON Lines |
| `data/budgets.jsonl` | 월별 예산 | JSON Lines |

폴더가 없으면 첫 실행 시 자동 생성되며, 카테고리 파일이 비어 있으면 기본 카테고리(`food`, `transport`, `rent`, `salary`, `etc`)가 자동으로 등록됩니다.

### transactions.jsonl 한 줄 예시

```json
{"id":"TX-000001","type":"expense","date":"2024-01-15","amount":15000,"category":"food","memo":"점심","tags":["meal"]}
```

### categories.jsonl 한 줄 예시

```json
{"name":"food"}
```

### budgets.jsonl 한 줄 예시

```json
{"month":"2024-01","amount":500000}
```

## 4. 명령 요약

| 명령 | 설명 |
| --- | --- |
| `add` | 거래 추가 (대화형) |
| `list` | 최신순 거래 목록 |
| `search` | 조건 검색 |
| `summary` | 월별 요약 (예산 사용률 포함) |
| `budget set` | 월 예산 설정 |
| `category add/list/remove` | 카테고리 관리 |
| `update` | 거래 수정 (옵션 방식 — 후술) |
| `delete` | 거래 삭제 |
| `import` | CSV 일괄 가져오기 (`--atomic` 로 전수 롤백) |
| `export` | CSV 내보내기 |
| `backup` | data 폴더 백업 (보너스) |

> `update` 는 **옵션 방식으로 고정**합니다. 대화형이 아니라 `--id` 와 변경할 필드 옵션으로만 동작합니다.

공통 옵션: 모든 명령이 `--data-dir`(데이터 폴더)와 `--debug`(디버그 로그, [12장](#12-출력-스트림과-디버그-로그))를 받습니다.

## 5. 주요 명령 예시

### 거래 추가 (add) — 대화형

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

### 목록 (list)

```bash
python -m budget_app list --limit 3
```

```text
TX-000005 | 2024-01-22 | expense | food | 35000 | 회식
TX-000004 | 2024-01-20 | expense | rent | 150000 | 공과금
TX-000001 | 2024-01-15 | expense | food | 15000 | 점심
```

### 검색 (search)

```bash
python -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food
python -m budget_app search --type expense --tag meal
python -m budget_app search --q 점심
```

### 월별 요약 + 예산 (summary, budget)

```bash
python -m budget_app budget set --month 2024-01 --amount 500000
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

예산을 초과하면 `[경고] 예산을 초과했습니다!` 가 함께 출력됩니다.

### 카테고리 관리 (category)

```bash
python -m budget_app category add --name groceries
python -m budget_app category list
python -m budget_app category remove --name food --replace-with etc
```

사용 중인 카테고리는 `--replace-with` 없이는 삭제할 수 없습니다.

### 거래 수정 (update) — **옵션 방식**

```bash
python -m budget_app update --id TX-000005 --amount 35000 --memo "회식"
python -m budget_app update --id TX-000005 --category etc --tags "company,dinner"
```

지원 옵션: `--id`(필수), `--date`, `--type`, `--category`, `--amount`, `--memo`, `--tags`.

### 거래 삭제 (delete)

```bash
python -m budget_app delete --id TX-000005
```

### CSV 내보내기 / 가져오기 (export / import)

```bash
python -m budget_app export --out export.csv --month 2024-01
python -m budget_app export --out range.csv --from 2024-01-01 --to 2024-03-31
python -m budget_app export --out plain.csv --month 2024-01 --no-id   # id 컬럼 제외(외부 도구용)

python -m budget_app import --from import.csv            # 부분 성공 + 중복 skip (기본)
python -m budget_app import --from import.csv --atomic   # 전수 롤백
python -m budget_app import --from import.csv --on-duplicate new-id   # 중복도 새 id 로 추가
python -m budget_app import --from import.csv --on-duplicate error    # 중복이면 중단
```

`export` 는 `--month` 또는 `--from/--to` 중 하나가 **필수**입니다.
`import` 의 실패 정책(부분 성공 vs 원자적)은 [7. 가져오기 실패 정책](#7-가져오기-실패-정책--부분-성공-vs-원자적전수-롤백) 을 참고하세요.

## 6. import / export CSV 스키마

- 인코딩: **UTF-8 (BOM 없음)**
- 헤더 포함

> **인코딩/BOM 방침**: 내보내기는 `encoding="utf-8"`(BOM 없음)로 고정한다. 한글이 그대로 보존되고, 다시 `import` 할 때 헤더 첫 컬럼명이 `﻿date` 로 깨지지 않도록 하기 위함이다(왕복 안전성 우선). 구형 Excel 에서 한글이 깨져 보이면 Excel 의 *데이터 → 텍스트/CSV 가져오기* 에서 원본 인코딩을 **UTF-8** 로 지정하면 된다. Excel 더블클릭 호환을 위해 BOM(`utf-8-sig`)이 필요하면 `export_csv` 의 `encoding` 만 바꾸면 되지만, 그 경우 자체 `import` 왕복 시 헤더 처리를 함께 조정해야 한다.

| column | required | 설명 |
| --- | --- | --- |
| `id` | N | `TX-000001` 형식. **내보내기는 기본 포함**, 가져오기는 있으면 쓰고 없으면 새로 발급 |
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` / `expense` |
| `category` | Y | 등록된 카테고리 (가져오기 시 미등록이면 자동 등록) |
| `amount` | Y | 양의 정수 |
| `memo` | N | 자유 문자열 |
| `tags` | N | 쉼표(`,`) 구분 문자열 |

### `id` 컬럼 — 왕복(round-trip) 안전성

예전 스키마에는 `id` 가 없었습니다. 그래서 `export` 한 파일을 그대로 `import` 하면
**같은 거래가 새 id 를 받아 한 번 더 저장**됐습니다. 내보낸 CSV 가 원본 거래를 식별할
수단을 갖고 있지 않았기 때문입니다.

`id` 는 **선택** 컬럼이라 기존 호환성이 유지됩니다.

- `export` 는 기본으로 포함합니다 → 자기 파일을 다시 넣어도 중복이 생기지 않습니다.
- `import` 는 id 가 있으면 그 id 를 복원하고, 없거나 비어 있으면 새로 발급합니다
  → 필수 컬럼만 갖춘 외부 CSV(엑셀·타 가계부)는 예전 그대로 들어옵니다.
- 외부 도구에 넘길 때 id 가 거슬리면 `export --no-id` 로 뺄 수 있습니다.

### CSV 예시

```csv
id,date,type,category,amount,memo,tags
TX-000001,2024-01-15,expense,food,15000,점심,meal
TX-000002,2024-01-14,income,salary,3000000,월급,
TX-000003,2024-01-20,expense,rent,150000,공과금,
```

`id` 없이도 그대로 가져올 수 있습니다(이 경우 전부 새로 발급).

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,점심,meal
```

## 7. 가져오기 실패 정책 — 부분 성공 vs 원자적(전수 롤백)

CSV `import` 는 일부 줄이 손상됐을 때의 처리 방식을 **옵션으로 선택**할 수 있습니다.

| 모드 | 옵션 | 손상된 줄이 있을 때 | 결과 파일 | 종료 코드 |
| --- | --- | --- | --- | --- |
| 부분 성공 (기본) | *(없음)* | 그 줄만 건너뛰고(skip) 나머지는 저장 | 유효한 줄만 반영 | `0` |
| 원자적(전수 롤백) | `--atomic` | 첫 오류에서 중단, **아무것도 저장하지 않음** | 변화 없음(원본 유지) | `4` |

### 중복 정책 — 이미 있는 `id` 를 만났을 때

`--on-duplicate` 로 고릅니다. 손상 여부와는 **독립된 축**입니다(`--atomic` 과 함께 쓸 수 있음).

| 옵션 | 동작 | 쓰는 상황 |
| --- | --- | --- |
| `skip` (기본) | 건너뛰고 `duplicated` 로 집계 | 내보낸 파일을 다시 넣는 정상 왕복 |
| `new-id` | 새 id 를 발급해 별도 거래로 추가 | 같은 내역을 의도적으로 복제 |
| `error` | `AppError` 로 중단 (아무것도 저장 안 됨) | 중복이 있으면 안 되는 정산 데이터 |

결과 요약에서 `skipped` 와 `duplicated` 를 나눠 보여 주는 이유는 **사용자가 해야 할 일이
정반대**이기 때문입니다. `skipped` 는 데이터가 잘못돼 CSV 를 고쳐야 하고, `duplicated` 는
이미 저장돼 있어서 아무것도 안 해도 됩니다. 한 숫자로 합치면 정상 왕복이 실패처럼 읽힙니다.

```bash
python -m budget_app export --out backup.csv --month 2024-01
python -m budget_app import --from backup.csv
# [완료] mode=부분 성공, imported=0, duplicated=3, skipped=0   ← 중복 생성 없음
```

### 동작 방식(준비 → 커밋 2단계)

두 모드 모두 **먼저 전체 행을 검증(준비 단계)한 뒤에만** 파일에 씁니다(커밋 단계).

- **부분 성공**: 준비 단계에서 검증 실패한 줄은 `skipped` 로 집계하고, 통과한 줄만 모아 마지막에 한 번에 append 합니다. 오류 줄은 앞쪽 일부를 `[오류 라인 일부]` 로 안내합니다.
- **원자적(`--atomic`)**: 준비 단계에서 한 줄이라도 검증에 실패하면 즉시 `AppError` 를 던지고 **파일을 전혀 건드리지 않습니다**. 커밋 단계는 기존 내용 + 신규 전부를 임시 파일에 쓴 뒤 `os.replace()` 로 교체하므로, 커밋 도중 프로세스가 죽어도 원본이 그대로 남습니다(파일 시스템 레벨의 전수 롤백). 카테고리 자동 등록과 ID 발급도 커밋 단계에서 수행되어, 실패 시 카테고리/거래 어느 쪽에도 잔여가 남지 않습니다.

```bash
# 손상된 줄이 하나라도 있으면 전체가 반영되지 않음 → 종료 코드 4
python -m budget_app import --from import.csv --atomic
# [오류] 원자적 가져오기 실패 — line 3: 금액은 양의 정수여야 합니다 ... (반영된 항목 없음)
# [힌트] CSV 를 고쳐 다시 시도하거나, --atomic 없이 부분 가져오기를 사용하세요.
```

> **선택 기준**: 회계·정산처럼 "일부만 들어가면 안 되는" 데이터는 `--atomic`, 로그성 대량 유입처럼 "가능한 만큼 최대한 넣는" 경우는 기본(부분 성공)을 사용하세요.

## 8. 저장 포맷 선택 — JSONL vs CSV

영구 저장은 **JSONL(JSON Lines)**, 외부 교환은 **CSV** 로 역할을 나눴습니다.

| 항목 | JSONL (내부 저장) | CSV (외부 교환) |
| --- | --- | --- |
| 구조 | 중첩/가변 필드 자연스러움 (`tags` 리스트를 그대로 표현) | 평면 표만 가능 (리스트는 `,` 로 인코딩 필요) |
| 타입 | JSON 타입 보존 (숫자/문자/배열 구분) | 모두 문자열 → 매번 재파싱·재검증 |
| 추가 쓰기 | 한 줄 append 로 O(1) 삽입, 원자적 교체 용이 | 헤더·따옴표 규칙 탓에 부분 수정이 번거로움 |
| 스트리밍 | 한 줄 = 레코드 1건 → 제너레이터로 자연스러운 스트리밍 | 따옴표 내 개행 등으로 라인=레코드 보장 안 됨 |
| 사람 가독성 | 보통 | 좋음 (Excel/시트에서 바로 열림) |
| 상호운용성 | 도구가 제한적 | 사실상 표준, 어디서나 열림 |

**JSONL 을 내부 저장 포맷으로 택한 이유**

1. **레코드 단위 추가·스트리밍**: 거래는 계속 쌓이는 append 중심 데이터입니다. JSONL 은 "한 줄 = 거래 1건" 이라 append 가 O(1) 이고, `stream()` 제너레이터가 한 줄씩 흘려보내 대용량에서도 전체를 메모리에 올리지 않습니다.
2. **타입·구조 보존**: `tags`(리스트), `amount`(정수) 를 형 손실 없이 저장합니다. CSV 라면 매 읽기마다 `,` 분해와 정수 파싱을 다시 해야 합니다.
3. **원자적 교체와 궁합**: 수정/삭제는 `임시 파일 + os.replace()` 로 교체하는데, 라인 지향 포맷이라 이 패턴이 단순합니다.
4. **손상 격리**: 한 줄이 깨져도 그 줄만 건너뛰면 되고 나머지는 유효합니다.

반대로 **가져오기/내보내기(import/export)** 는 Excel·구글시트·타 가계부와 주고받는 통로이므로, 상호운용성이 가장 좋은 **CSV** 를 씁니다. 즉 "내부 저장은 JSONL, 경계에서의 교환은 CSV" 라는 역할 분리입니다.

## 9. 대용량(100k+) 성능 — 병목과 개선안

현재 설계는 읽기를 제너레이터로 스트리밍하므로 **단순 조회/합계(summary)** 는 건수가 늘어도 메모리가 일정합니다. 다만 다음 지점은 건수가 커지면 병목이 됩니다.

| # | 병목 지점 | 현재 비용 | 원인 | 개선안 |
| --- | --- | --- | --- | --- |
| B1 | `list`/`search` 정렬 (`stream_sorted`) | 필터 통과분을 메모리에 모아 정렬 → O(k log k) 메모리 O(k) | 파일이 시간순으로 정렬돼 있지 않음 | ① append 시 항상 시간순 유지(정렬 불변식) → 정렬 없이 tail-read ② `--limit` 상위 N 만 필요하면 `heapq.nlargest(N)` 로 메모리 O(N) ③ 그래도 크면 **외부 정렬**(청크 정렬 후 k-way merge) |
| B2 | 대량 `import` 의 ID 발급 | (개선 완료) 과거 행마다 `next_id()` 가 전체를 재스캔 → O(N²) | 매 삽입마다 최대 ID 재계산 | `max_id_num()` 을 **한 번만** 읽고 메모리에서 연속 발급 → O(N). *(이번 수정 반영)* |
| B3 | `--atomic` import 커밋 | 기존 전체 + 신규를 다시 씀 → O(전체) I/O·메모리 | 원자적 교체를 위해 전량 재작성 | 원자성의 대가로 감수. 초대용량은 부분 성공 모드 사용 또는 파일 **샤딩**(아래 B4) |
| B4 | 단일 파일 전체 스캔(모든 조회 공통) | 매 명령이 파일 전체를 읽음 → O(전체) | 인덱스가 없음 | ① **월별 샤딩**(`transactions-YYYY-MM.jsonl`) 으로 조회 범위를 해당 월로 축소 ② `id → offset` **경량 인덱스** 파일로 단건 조회 O(1) ③ 임계 규모를 넘으면 SQLite 로 이전 |

### 구체적 임계치·전략 가이드

- **~ 수만 건**: 현재 구조로 충분. 정렬도 체감 지연이 거의 없습니다.
- **~ 10만 건**: `list`/`search` 정렬(B1)의 메모리·시간이 눈에 띕니다. 상위 N 만 필요하면 `heapq.nlargest`, 전체 정렬이 필요하면 append 정렬 불변식 도입을 권장합니다.
- **100만 건 이상**: 단일 파일 전체 스캔(B4)이 지배적. **월별 샤딩 + 경량 인덱스**, 또는 **SQLite** 등 인덱스 지원 저장소로의 이전을 권장합니다. 정렬은 **외부 정렬**로 전환합니다.

> 요약: 지금은 "스트리밍으로 메모리는 잡되, 정렬과 전체 스캔은 O(N)" 지점에 있습니다. 확장 순서는 **정렬 불변식 → heapq 상위 N → 월별 샤딩/인덱스 → 외부 정렬/SQLite** 입니다.

## 10. 아키텍처

4개 계층으로 책임을 분리했고, **계층을 폴더로 드러냈습니다**. **파일 하나 = 책임 하나**가
원칙이라 어떤 변경이든 고칠 파일이 한눈에 정해집니다.

```
budget_app/
├── __main__.py                # 엔트리포인트 (python -m budget_app)
├── config.py                  # 앱 정체성 (로거 이름) — 계층 아님
├── errors.py                  # 예외 어휘 (ValidationError / AppError) — import 0개
├── decorators.py              # 관측 — @log_call / @measure_time
├── context.py                 # 합성 루트 — 저장소·서비스 조립 (계층 밖)
│
├── domain/                    # ── 도메인 (I/O 를 전혀 모름) ──
│   ├── config.py              #    타입 어휘·날짜 형식·ID 형식
│   ├── messages.py            #    필드 검증 실패 메시지
│   ├── validators.py          #    규칙 하나 = 함수 하나
│   ├── tx_id.py               #    TransactionId 값 객체
│   ├── entities.py            #    Transaction / Budget / Category / TransactionPatch
│   ├── specs.py               #    Specification — 조합 가능한 검색 조건
│   ├── queries.py             #    SearchFilter — CLI 인자를 명세로 조립
│   ├── results.py             #    MonthlySummary / ImportReport
│   └── periods.py             #    month_range — "이 달"의 정의처
│
├── storage/                   # ── 저장소 (open() 은 전부 여기) ──
│   ├── config.py              #    파일명·인코딩·CSV 스키마·백업
│   ├── messages.py            #    손상 줄 로그 / CSV 헤더 오류
│   ├── jsonl.py               #    JsonlStore / RawLine / stage·commit
│   ├── ids.py                 #    IdAllocator
│   ├── repositories.py        #    거래·카테고리·예산 저장소
│   ├── csv_io.py              #    CSV 경계 어댑터
│   ├── unit_of_work.py        #    UnitOfWork — 다중 파일 커밋
│   └── backup.py              #    데이터 폴더 백업
│
├── services/                  # ── 서비스 (판단만) ──
│   ├── config.py              #    중복 정책·한도
│   ├── messages.py            #    AppError message / hint
│   ├── transactions.py        #    거래 유스케이스
│   ├── budgets.py             #    예산 + 월별 요약
│   ├── categories.py          #    카테고리 + 참조 무결성
│   └── importexport.py        #    CSV 정책 (실패 축 × 중복 축)
│
└── cli/                       # ── CLI (사람과 만나는 곳) ──
    ├── __init__.py            #    main 만 재수출
    ├── config.py              #    한도·종료 코드
    ├── messages.py            #    프롬프트·결과·오류 표시 (전체의 3분의 2)
    ├── app.py                 #    HANDLERS 레지스트리 + main
    ├── handlers.py            #    cmd_* 13개
    ├── parser.py              #    argparse 문법
    ├── prompts.py             #    대화형 입력
    ├── presenter.py           #    도메인 → 문자열 (출력 안 함)
    ├── output.py              #    채널 결정
    └── error_handler.py       #    예외 → 종료 코드
```

의존은 **아래로만** 흐릅니다. `services` 는 `open()` 을 호출하지 않고, `storage` 는
화면 문자열을 모르며, `presenter` 는 출력하지 않고 문자열을 돌려줍니다.

**폴더 이름이 곧 계층입니다.** 평평하게 두면 알파벳순이 계층을 흩뜨려서
(`csv_io.py` 와 `decorators.py` 가 나란히 보이는 식) 구조가 코드에는 있는데 파일
트리에는 없는 상태가 됩니다. 횡단 4개만 폴더 없이 루트에 두어 "이들은 계층이 아니다"를
위치로 표현했습니다 — `config` 와 `messages` 는 11개 모듈이, `errors` 는 7개가
import 합니다.

### 설계 포인트

- **제너레이터 스트리밍**: `JsonlStore.stream()` 등 모든 읽기는 `yield` 기반입니다. 파일을 `json.load()` 로 한 번에 올리지 않으므로 거래가 수십만 건이어도 메모리에 모두 올라가지 않습니다.
- **읽기 경로가 둘**: `iter_raw()` 는 **모든 줄을 원문과 함께** 주고, `stream()` 은 **검증을 통과한 객체만** 줍니다. 재작성(update/delete/재지정)은 `iter_raw()` 를 쓰므로 손상된 줄이 원문 그대로 보존됩니다. 하나로 합쳐 두면 무관한 거래를 지울 때 손상된 줄까지 디스크에서 사라집니다. ID 스캔도 `iter_raw()` 기반이라, 검증에 실패하는 줄에 들어 있던 id 도 "이미 쓰인 번호"로 인식되어 재발급 충돌이 생기지 않습니다.
- **원자적 쓰기**: `update`/`delete` 는 임시 파일에 전부 쓴 뒤 `flush` + `fsync` 하고 `os.replace()` 로 교체합니다. 쓰는 도중 프로세스가 죽어도 원본 파일이 깨지지 않습니다. `os.replace` 가 보장하는 것은 "이름이 가리키는 대상이 순간적으로 바뀐다"이지 "내용이 디스크에 도달했다"가 아니라서 `fsync` 가 함께 필요합니다.
- **데코레이터로 공통 관심사 분리**: `@handle_errors` 가 모든 CLI 핸들러를 감싸서 스택트레이스 대신 `[오류]` / `[힌트]` 메시지를 **stderr** 로 출력하고 적절한 종료 코드를 반환합니다. 잡는 예외는 *종료 신호 / 입력 오류 / 환경 상태 / 최후 방어선* 네 부류로 묶여 있고 `except` 순서가 그 분류를 그대로 따릅니다. `@log_call`, `@measure_time` 은 디버깅용으로 서비스 계층에 적용되어 있습니다.
- **관측과 표현을 다른 파일에**: `@log_call`/`@measure_time`(관측)은 `decorators.py`, `@handle_errors`(예외를 화면 문구와 종료 코드로 바꾸는 표현 정책)는 `error_handler.py` 에 있습니다. 한 파일에 두면 서비스 계층이 `@log_call` 하나를 쓰려다 출력 모듈까지 끌고 들어와 `services → decorators → output` 이라는 역방향 의존이 생깁니다. 지금은 모든 화살표가 아래로만 향합니다.
- **출력 채널 분리**: 명령의 *결과*만 stdout 으로, *진단*(오류/힌트/경고)은 stderr 로 나갑니다. 덕분에 `list > out.txt` 의 데이터 파일에 오류 문자열이 섞이지 않고, 파이프가 끊겨 stdout 이 깨진 상황에서도 오류는 사용자에게 전달됩니다. 두 채널 모두 `output.out()` / `output.err()` 라는 이름이 있어서, `grep 'output\.'` 한 번이면 프로그램이 밖으로 내보내는 모든 글자가 나옵니다.
- **프레젠터는 출력하지 않는다**: `presenter` 는 문자열을 **반환**하고 채널 선택은 호출자가 합니다. 덕분에 화면 형식을 프로세스 없이 검증할 수 있고, 채널 결정이 `output` 한 곳에만 남습니다.
- **타입 힌트**: 모든 함수의 입력/출력에 타입을 명시했습니다. 부분 수정은 문자열 키 dict 대신 `TransactionPatch` dataclass 로 받으므로 필드명을 잘못 쓰면 조용히 무시되지 않고 `TypeError` 로 즉시 드러납니다.
- **생성자 불변식 검증**: `Transaction`, `Budget`, `Category` dataclass 는 `__post_init__` 에서 필드를 검증·정규화합니다. 즉 **생성자가 유일한 강제 지점**이라, 서비스/CLI/`from_dict`/직접 호출 등 어떤 경로로 만들어져도 잘못된 객체가 존재할 수 없습니다. 개별 규칙은 전부 `validators.py` 의 모듈 함수(`parse_date`/`parse_amount`/…)로 **규칙 하나 = 함수 하나**로 정의되고, 모델·CSV 어댑터·대화형 입력이 모두 같은 함수를 씁니다.
- **파생값은 모델이 계산**: `MonthlySummary.usage_pct` / `over_budget` 처럼 계산으로 얻는 값은 `@property` 로 모델에 둡니다. 서비스는 집계만, 프레젠터는 표시만 담당합니다.
- **설정·문자열 중앙화**: 값 상수(카테고리·파일명·형식·한도·종료 코드)는 `config.py`, 사용자 노출 문자열(프롬프트·메시지·오류/힌트·로그)은 `messages.py` 에 모았습니다. 나눈 이유는 **바꿨을 때 일어나는 일이 다르기 때문**입니다 — `config` 를 바꾸면 동작이 달라지고, `messages` 를 바꾸면 글자만 달라집니다. 덕분에 도메인 계층(`models`/`validators`)이 CLI 문구 변경에 묶이지 않습니다.

## 11. 종료 코드

| 코드 | 의미 |
| --- | --- |
| `0` | 정상 종료 |
| `1` | 예기치 못한 오류 |
| `2` | 입력 검증 실패 (`ValidationError`) |
| `3` | 파일 입출력 오류 (없음 / 디렉터리 / 권한 / 일반 I/O) |
| `4` | 애플리케이션 오류 (예: 없는 id, 미등록 카테고리, `--atomic` import 전수 롤백) |
| `5` | 카테고리 미등록 상태에서 add 시도 |
| `6` | 파일 인코딩 오류 (UTF-8 아님) |
| `130` | 사용자 Ctrl+C 중단 |

## 12. 출력 스트림과 디버그 로그

명령의 **결과**는 stdout, **진단**(`[오류]`/`[힌트]`/경고/재입력 안내)은 stderr 로 나갑니다. 둘을 셸에서 따로 다룰 수 있습니다.

```bash
python -m budget_app list > out.txt          # out.txt 에는 거래 목록만 (오류가 섞이지 않음)
python -m budget_app import --from nope.csv 2>/dev/null   # 진단만 버리기 → 아무것도 안 보임
python -m budget_app import --from nope.csv 1>/dev/null   # 결과만 버리기 → 오류만 보임
python -m budget_app list | head -3          # 하류가 먼저 닫혀도 조용히 종료 (코드 0)
```

예기치 못한 오류의 스택트레이스는 기본적으로 **숨기고 로그로만 보존**합니다. 그 로그를 보려면 디버그를 켭니다.

```bash
python -m budget_app --debug summary --month 2024-01   # 하위 명령 앞
python -m budget_app summary --month 2024-01 --debug   # 하위 명령 뒤 (둘 다 동작)
BUDGET_APP_DEBUG=1 python -m budget_app summary --month 2024-01   # 환경변수로도 가능
```

디버그를 켜면 로그 레벨이 DEBUG 가 되어 `@log_call`·`@measure_time` 의 호출/시간 로그와 `handle_errors` 가 보존한 스택트레이스가 stderr 로 출력됩니다. 끈 상태에서는 WARNING 이상(예: 손상된 JSONL 줄 경고)만 나옵니다.

> `category` / `budget` 처럼 하위 명령이 또 있는 경우, `--data-dir` 와 마찬가지로 `--debug` 도 그 하위 명령 **앞**에 써야 합니다: `python -m budget_app category --debug list`.

## 13. 보너스 — 백업

```bash
python -m budget_app backup
```

`./backup_YYYYMMDD_HHMMSS/` 폴더에 `data/*.jsonl` 가 복사됩니다.
