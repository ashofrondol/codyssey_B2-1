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
python -m budget_app import --from import.csv            # 부분 성공(기본)
python -m budget_app import --from import.csv --atomic   # 전수 롤백
```

`export` 는 `--month` 또는 `--from/--to` 중 하나가 **필수**입니다.
`import` 의 실패 정책(부분 성공 vs 원자적)은 [7. 가져오기 실패 정책](#7-가져오기-실패-정책--부분-성공-vs-원자적전수-롤백) 을 참고하세요.

## 6. import / export CSV 스키마

- 인코딩: **UTF-8 (BOM 없음)**
- 헤더 포함

> **인코딩/BOM 방침**: 내보내기는 `encoding="utf-8"`(BOM 없음)로 고정한다. 한글이 그대로 보존되고, 다시 `import` 할 때 헤더 첫 컬럼명이 `﻿date` 로 깨지지 않도록 하기 위함이다(왕복 안전성 우선). 구형 Excel 에서 한글이 깨져 보이면 Excel 의 *데이터 → 텍스트/CSV 가져오기* 에서 원본 인코딩을 **UTF-8** 로 지정하면 된다. Excel 더블클릭 호환을 위해 BOM(`utf-8-sig`)이 필요하면 `export_csv` 의 `encoding` 만 바꾸면 되지만, 그 경우 자체 `import` 왕복 시 헤더 처리를 함께 조정해야 한다.

| column | required | 설명 |
| --- | --- | --- |
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` / `expense` |
| `category` | Y | 등록된 카테고리 (가져오기 시 미등록이면 자동 등록) |
| `amount` | Y | 양의 정수 |
| `memo` | N | 자유 문자열 |
| `tags` | N | 쉼표(`,`) 구분 문자열 |

### CSV 예시

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,점심,meal
2024-01-14,income,salary,3000000,월급,
2024-01-20,expense,rent,150000,공과금,
```

## 7. 가져오기 실패 정책 — 부분 성공 vs 원자적(전수 롤백)

CSV `import` 는 일부 줄이 손상됐을 때의 처리 방식을 **옵션으로 선택**할 수 있습니다.

| 모드 | 옵션 | 손상된 줄이 있을 때 | 결과 파일 | 종료 코드 |
| --- | --- | --- | --- | --- |
| 부분 성공 (기본) | *(없음)* | 그 줄만 건너뛰고(skip) 나머지는 저장 | 유효한 줄만 반영 | `0` |
| 원자적(전수 롤백) | `--atomic` | 첫 오류에서 중단, **아무것도 저장하지 않음** | 변화 없음(원본 유지) | `4` |

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

4개 계층으로 책임을 분리했습니다.

```
budget_app/
├── __main__.py        # 엔트리포인트 (python -m budget_app)
├── cli.py             # CLI 계층 — argparse, 대화형 입력, 출력 포맷
├── services.py        # 서비스 계층 — 검색/요약/예산/CSV I/O 비즈니스 로직
├── repository.py      # 저장소 계층 — JSONL 파일 입출력 (스트리밍 + 원자적 교체)
├── models.py          # 모델 — Transaction / Budget / Category dataclass + 생성자 불변식 검증
├── decorators.py      # 공통 관심사 — 로그 / 시간 측정 / 예외 처리
└── config.py          # 설정 — 상수 + 출력 문자열 중앙화(단일 출처)
```

### 설계 포인트

- **제너레이터 스트리밍**: `TransactionRepository.stream()` 등 모든 읽기는 `yield` 기반입니다. 파일을 `json.load()` 로 한 번에 올리지 않으므로 거래가 수십만 건이어도 메모리에 모두 올라가지 않습니다.
- **원자적 쓰기**: `update`/`delete` 는 임시 파일에 전부 쓴 뒤 `os.replace()` 로 교체합니다. 쓰는 도중 프로세스가 죽어도 원본 파일이 깨지지 않습니다.
- **데코레이터로 공통 관심사 분리**: `@handle_errors` 가 모든 CLI 핸들러를 감싸서 스택트레이스 대신 `[오류]` / `[힌트]` 메시지를 출력하고 적절한 종료 코드를 반환합니다. `@log_call`, `@measure_time` 은 디버깅용으로 서비스 계층에 적용되어 있습니다.
- **타입 힌트**: 모든 함수의 입력/출력에 타입을 명시했습니다. `Transaction.from_dict` 처럼 외부 데이터를 받는 지점은 생성자를 거치므로 `ValidationError` 로 계약 위반을 일찍 잡습니다.
- **생성자 불변식 검증**: `Transaction`, `Budget`, `Category` dataclass 는 `__post_init__` 에서 필드를 검증·정규화합니다. 즉 **생성자가 유일한 강제 지점**이라, 서비스/CLI/`from_dict`/직접 호출 등 어떤 경로로 만들어져도 잘못된 객체가 존재할 수 없습니다. 개별 규칙은 `validate_type`/`validate_date`/`validate_month`(각 모델)와 `Category.normalize`, 공용 규칙은 모듈 함수 `validate_amount` 로 단일 정의됩니다.
- **설정·문자열 중앙화**: 모든 값 상수(카테고리·파일명·형식·한도·종료 코드)와 사용자 노출 문자열(프롬프트·메시지·오류/힌트·로그)을 `config.py` 한 곳에 모았습니다. 다른 모듈은 `config.X` 로 참조하므로 문구·정책 변경이 한 파일에서 끝납니다.

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

## 12. 보너스 — 백업

```bash
python -m budget_app backup
```

`./backup_YYYYMMDD_HHMMSS/` 폴더에 `data/*.jsonl` 가 복사됩니다.
