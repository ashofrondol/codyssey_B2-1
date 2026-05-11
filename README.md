# budget_app — 파일 기반 가계부 콘솔 프로그램

Python 표준 라이브러리만으로 만든 콘솔 가계부입니다. JSONL 영구 저장, 제너레이터 스트리밍, 데코레이터 분리, 타입 힌트, 모듈화 구조를 갖췄습니다.

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
| `import` | CSV 일괄 가져오기 |
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
python -m budget_app import --from import.csv
```

`export` 는 `--month` 또는 `--from/--to` 중 하나가 **필수**입니다.

## 6. import / export CSV 스키마

- 인코딩: **UTF-8**
- 헤더 포함

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

## 7. 아키텍처

4개 계층으로 책임을 분리했습니다.

```
budget_app/
├── __main__.py        # 엔트리포인트 (python -m budget_app)
├── cli.py             # CLI 계층 — argparse, 대화형 입력, 출력 포맷
├── services.py        # 서비스 계층 — 검색/요약/예산/CSV I/O 비즈니스 로직
├── repository.py      # 저장소 계층 — JSONL 파일 입출력 (스트리밍 + 원자적 교체)
├── models.py          # 모델 — Transaction / Budget / Category dataclass + 검증
└── decorators.py      # 공통 관심사 — 로그 / 시간 측정 / 예외 처리
```

### 설계 포인트

- **제너레이터 스트리밍**: `TransactionRepository.stream()` 등 모든 읽기는 `yield` 기반입니다. 파일을 `json.load()` 로 한 번에 올리지 않으므로 거래가 수십만 건이어도 메모리에 모두 올라가지 않습니다.
- **원자적 쓰기**: `update`/`delete` 는 임시 파일에 전부 쓴 뒤 `os.replace()` 로 교체합니다. 쓰는 도중 프로세스가 죽어도 원본 파일이 깨지지 않습니다.
- **데코레이터로 공통 관심사 분리**: `@handle_errors` 가 모든 CLI 핸들러를 감싸서 스택트레이스 대신 `[오류]` / `[힌트]` 메시지를 출력하고 적절한 종료 코드를 반환합니다. `@log_call`, `@measure_time` 은 디버깅용으로 서비스 계층에 적용되어 있습니다.
- **타입 힌트**: 모든 함수의 입력/출력에 타입을 명시했습니다. `Transaction.from_dict` 처럼 외부 데이터를 받는 지점에서 `ValidationError` 로 계약 위반을 일찍 잡습니다.
- **dataclass 모델**: `Transaction`, `Budget`, `Category` 가 dataclass 로 정의되어 있고, 각 클래스에 `validate_*` 클래스/스태틱 메서드가 모여 있어 검증 규칙이 한 곳에 응집됩니다.

## 8. 종료 코드

| 코드 | 의미 |
| --- | --- |
| `0` | 정상 종료 |
| `1` | 예기치 못한 오류 |
| `2` | 입력 검증 실패 (`ValidationError`) |
| `3` | 파일을 찾을 수 없음 |
| `4` | 애플리케이션 오류 (예: 없는 id, 미등록 카테고리) |
| `5` | 카테고리 미등록 상태에서 add 시도 |
| `130` | 사용자 Ctrl+C 중단 |

## 9. 보너스 — 백업

```bash
python -m budget_app backup
```

`./backup_YYYYMMDD_HHMMSS/` 폴더에 `data/*.jsonl` 가 복사됩니다.
