# 체크리스트 검증 보고서 — budget_app

`checklists_md/python_cli_budget_app.md` 의 16개 항목을 이 프로젝트에 대해 검증한 결과다.

| 항목 | 값 |
| --- | --- |
| 검증 대상 | `codyssey_B2-1` (파일 기반 가계부 콘솔 프로그램) |
| 검증일 | 2026-07-16 |
| 검증 방법 | 자동화 테스트 46건 + 스모크 테스트 1건 + 코드·문서 확인 |
| 실행 환경 | Python 3.13.1 / pytest 9.1.1 / uv 0.5.12 / Windows 11 |
| 결과 | **16/16 통과** |

> 근거의 `→ 테스트명` 은 [tests/](tests/) 의 자동화 테스트를 가리킨다. 실행 결과와
> 테스트 설계 근거는 [TEST_REPORT.md](TEST_REPORT.md) 를 참고할 것.

---

## 요약

| 절 | 항목 수 | 통과 | 검증 방식 |
| --- | --- | --- | --- |
| §1 기능 동작 검증 | 7 | 7 | 자동화 테스트 (블랙박스 CLI) |
| §2 구현 구조 설명 | 3 | 3 | 자동화 테스트 (AST) + 문서 확인 |
| §3 핵심 개념 이해 | 3 | 3 | 자동화 테스트 (AST) + 문서 확인 |
| §4 확장 사고 및 트러블슈팅 | 3 | 3 | 문서 확인 + 자동화 테스트 |
| **합계** | **16** | **16** | |

---

## §1. 기능 동작 검증

### 1.1 add/list/search/summary/export/import/update/delete 가 요구사항대로 동작하는가? ✅

8개 명령이 모두 구현·노출되고 실제로 동작한다.

- 핸들러: [budget_app/cli.py](budget_app/cli.py) 의 `cmd_add` / `cmd_list` / `cmd_search` /
  `cmd_summary` / `cmd_export` / `cmd_import` / `cmd_update` / `cmd_delete`
- `update` 는 명세대로 **옵션 방식 고정**(`--id` + 변경 필드), `add` 는 대화형
- → `test_help_lists_required_commands` (8개 명령 노출)
- → `test_list_runs_and_shows_seeded_data`, `test_search_filters_by_category`,
  `test_summary_reports_income_and_expense`, `test_add_interactive_persists_transaction`,
  `test_update_changes_field_and_persists`, `test_delete_removes_transaction`,
  `test_import_export_roundtrip_preserves_rows`

### 1.2 프로그램 재실행 후에도 데이터가 유지되는가? (저장 파일 3개 이상) ✅

저장 파일이 도메인별로 **3개** 분리되어 있고, 별개 프로세스로 재실행해도 유지된다.

| 파일 | 내용 |
| --- | --- |
| `data/transactions.jsonl` | 거래 |
| `data/categories.jsonl` | 카테고리 |
| `data/budgets.jsonl` | 월별 예산 |

- 폴더/파일 자동 생성: [budget_app/repository.py](budget_app/repository.py) `_ensure_parent`, `__init__`
- → `test_data_persists_across_process_restarts` — import(프로세스 1) 후 list(프로세스 2)에서
  데이터가 보이고 저장 파일이 3개 이상임을 확인

### 1.3 category add/list/remove 가 정상 동작하는가? (사용 중 카테고리 처리 포함) ✅

사용 중 카테고리는 `--replace-with` 없이 삭제할 수 없고, 지정 시 일괄 재지정 후 삭제한다.

- 정책 구현: [budget_app/services.py](budget_app/services.py) `CategoryService.remove`
  (미사용 → 삭제 / 사용 중 + 대체 지정 → 재지정 후 삭제 / 사용 중 + 미지정 → `AppError` 차단)
- → `test_category_add_list_remove`
- → `test_category_remove_in_use_never_loses_data` — **거래가 조용히 사라지지 않는지**를 검증
  (차단이든 재지정이든 데이터 유실은 불허)

### 1.4 budget set 이 저장되며, summary 에서 예산 사용률/초과 여부가 출력되는가? ✅

- 저장: [budget_app/repository.py](budget_app/repository.py) `BudgetStore.set` (월별 단일 값 유지)
- 사용률·초과 계산: [budget_app/services.py](budget_app/services.py) `BudgetService.monthly_summary`
  (`usage_pct`, `over_budget`)
- 초과 경고 출력: [budget_app/cli.py](budget_app/cli.py) `cmd_summary` → `[경고] 예산을 초과했습니다!`
- → `test_budget_set_and_summary_shows_usage` (지출 165,000 / 예산 500,000 = 33% 표시 확인)
- → `test_summary_warns_when_over_budget` (지출 165,000 > 예산 100,000 → 초과 표시 확인)

### 1.5 import/export 가 명시된 CSV 스키마(UTF-8, 헤더, 컬럼)로 동작하는가? ✅

- 고정 스키마: [budget_app/services.py](budget_app/services.py)
  `CSV_FIELDS = ("date", "type", "category", "amount", "memo", "tags")`
- UTF-8 + 헤더: `open(..., encoding="utf-8")` + `writer.writeheader()`
- 인코딩/BOM 방침 문서화: [README.md](README.md) §6
- → `test_export_csv_is_utf8_with_header_and_columns` — 바이트를 UTF-8로 디코드하고
  필수 컬럼(`date`/`type`/`category`/`amount`) 존재를 확인
- → `test_import_export_roundtrip_preserves_rows` — import 3건 → export 3건, 금액 보존 확인

### 1.6 잘못된 입력/파일 오류에서 스택트레이스 없이 오류 메시지와 해결 힌트를 출력하는가? ✅

- [budget_app/decorators.py](budget_app/decorators.py) `handle_errors` 가 모든 핸들러를 감싸
  `[오류] 원인` + `[힌트] 해결책` 형식으로 출력하고, 트레이스는 `logger.debug(exc_info=True)` 로만 남긴다.
- → `test_error_output_gives_a_hint` — 힌트성 안내 존재 확인
- → 전 테스트 공통 `assert_no_traceback` — 어떤 오류 경로에서도 `Traceback` 문자열이
  사용자 출력에 나오지 않음을 확인 (46건 전부에 적용)

### 1.7 오류 상황에서 종료 코드가 0이 아님을 확인할 수 있는가? ✅

종료 코드 규칙이 `handle_errors` 에 매핑되어 있고 문서화되어 있다([README.md](README.md) §11).

| 코드 | 의미 |
| --- | --- |
| `0` | 정상 |
| `1` | 예기치 못한 오류 |
| `2` | 입력 검증 실패 |
| `3` | 파일 없음 |
| `4` | 애플리케이션 오류 (없는 id, 미등록 카테고리, `--atomic` 롤백) |
| `5` | 카테고리 미등록 상태의 add |
| `130` | Ctrl+C |

- → [TestCase.txt](TestCase.txt) 의 오류 케이스 7건 (`=> !0`) + `test_invalid_argument_exits_nonzero_without_traceback`,
  `test_missing_file_exits_nonzero_without_traceback`, `test_delete_unknown_id_exits_nonzero`

---

## §2. 구현 구조 설명

### 2.1 3개 이상 모듈로 분리되어 있고, 책임을 “어떻게” 나눴는지 설명할 수 있는가? ✅

**책임 모듈 5개**로 계층 분리되어 있다(측정치: `test_package_is_split_into_at_least_3_modules`).

| 모듈 | 책임 |
| --- | --- |
| [cli.py](budget_app/cli.py) | CLI 계층 — argparse, 대화형 입력, 출력 포맷 |
| [services.py](budget_app/services.py) | 서비스 계층 — 검색/요약/예산/CSV I/O 비즈니스 로직 |
| [repository.py](budget_app/repository.py) | 저장소 계층 — JSONL 입출력 (스트리밍 + 원자적 교체) |
| [models.py](budget_app/models.py) | 모델 — dataclass + 검증 규칙 |
| [decorators.py](budget_app/decorators.py) | 공통 관심사 — 로그/시간측정/예외처리 |

- 분리 기준 설명: [README.md](README.md) §10 "아키텍처"
- 의존 방향은 `cli → services → repository → models` 단방향이며, `decorators` 는 전 계층이 공용한다.

### 2.2 최소 2개 이상의 클래스에 부여한 책임 경계를 “어떻게” 정했는지 설명할 수 있는가? ✅

**클래스 14개**가 역할별로 나뉘어 있다(측정치: `test_has_at_least_2_classes`).

| 역할 | 클래스 | 책임 경계 |
| --- | --- | --- |
| 모델 | `Transaction`, `Budget`, `Category` | **검증(validation)** 만 담당 — 저장 방법은 모른다 |
| 저장소 | `TransactionRepository`, `CategoryStore`, `BudgetStore` | **영속화(persistence)** 만 담당 — 도메인 규칙은 모른다 |
| 서비스 | `TransactionService`, `BudgetService`, `CategoryService`, `ImportExportService` | **도메인 규칙** 담당 (예: "미등록 카테고리로는 거래 추가 불가") |
| 지원 | `SearchFilter`, `AppContext`, `AppError`, `ValidationError` | 필터 조건 / 의존성 조립 / 오류 표현 |

경계 원칙: *검증은 모델, 저장은 저장소, 규칙은 서비스*. 예를 들어 `Transaction.validate_amount`
는 "금액은 양의 정수"만 알고, "카테고리가 등록되어 있어야 한다"는 `TransactionService.add` 가 안다.

### 2.3 파일 기반 update/delete 를 “어떻게” 안전하게 처리했는지 설명할 수 있는가? ✅

**임시 파일 + 원자적 교체** 패턴을 사용한다.

```python
# budget_app/repository.py — _atomic_write_jsonl
tmp = path.with_suffix(path.suffix + ".tmp")
with open(tmp, "w", encoding="utf-8", newline="\n") as f:
    ...                      # 전체를 임시 파일에 먼저 쓴다
os.replace(tmp, path)        # 성공했을 때만 한 번에 교체(원자적)
```

원본을 직접 덮어쓰면 쓰기 도중 프로세스가 죽을 때 파일이 깨지지만, 이 패턴은 교체가
끝나기 전까지 원본이 그대로이므로 **"교체 전" 또는 "교체 후"** 상태만 존재한다.

- → `test_update_delete_uses_atomic_replace` — AST 로 `os.replace` 계열 호출 + 임시 파일 사용을 확인
  (평범한 `str.replace()` 를 오인하지 않도록 호출 대상을 AST 로 판별)

---

## §3. 핵심 개념 이해

### 3.1 list/search 를 제너레이터로 스트리밍 처리한 방식과 “왜” 유리한지 ✅

**제너레이터 함수 6개**가 확인된다(측정치: `test_uses_generator_streaming`).

```python
# budget_app/repository.py — TransactionRepository.stream
with open(self.path, "r", encoding="utf-8") as f:
    for line in f:                       # 파일을 한 줄씩만 읽는다
        yield Transaction.from_dict(json.loads(line))
```

**왜 유리한가**: `json.load()` 로 전체를 올리면 메모리가 파일 크기에 비례해 커지지만,
`yield` 는 한 번에 한 건만 들고 있으므로 거래가 수십만 건이어도 메모리가 일정하다.
`list --limit 3` 처럼 앞부분만 필요한 경우 나머지를 읽지 않고 끊을 수도 있다.

**한계도 문서화됨**: 정렬이 필요한 `stream_sorted` 는 필터 통과분을 한 번은 메모리에
모아야 한다 → [README.md](README.md) §9 에서 병목(B1)으로 식별하고 개선안을 제시했다.

### 3.2 데코레이터로 분리한 공통 기능이 무엇이며, “왜” 분리가 필요했는지 ✅

[budget_app/decorators.py](budget_app/decorators.py) 에 3개를 정의하고 실제 적용했다
(측정치: `test_uses_decorators_for_cross_cutting_concerns` — 정의는 `functools.wraps`,
적용은 `@handle_errors` / `@log_call` / `@measure_time` 확인).

| 데코레이터 | 기능 | 적용처 |
| --- | --- | --- |
| `@handle_errors` | 예외 → `[오류]`/`[힌트]` 출력 + 종료 코드 매핑 | 모든 CLI 핸들러 |
| `@log_call` | 호출/반환 DEBUG 로그 | 서비스 계층 |
| `@measure_time` | 실행 시간 DEBUG 로그 | `monthly_summary` 등 |

**왜 분리했나**: 오류 처리는 8개 핸들러 전부에 필요하지만 각 핸들러의 *본질적 관심사*가
아니다. 데코레이터로 빼지 않으면 모든 핸들러가 동일한 `try/except` 7블록을 복제해야 하고,
종료 코드 규칙이 바뀔 때 8곳을 고쳐야 한다. 지금은 `handle_errors` 한 곳만 고치면 된다.

### 3.3 타입 힌트를 적용해 얻는 이점을 실제 코드 예로 확인했고 “왜” 도움이 되는지 ✅

**타입 힌트 적용률 95% (76/80 함수)** — 하한 70%를 크게 상회
(측정치: `test_type_hints_are_widely_applied`).

```python
def validate_amount(value: Any) -> int:      # 무엇이 들어오든 int 로 나온다는 계약
def main(argv: Optional[List[str]] = None) -> int:
def stream(self) -> Iterator[Transaction]:   # 리스트가 아니라 '흘러나온다'는 사실이 시그니처에 드러남
```

**왜 도움이 되는가**:
1. `stream() -> Iterator[Transaction]` 는 반환값이 리스트가 아님을 호출자에게 알려,
   "두 번 순회하면 비어 있다"는 제너레이터 특성을 시그니처만 보고 알 수 있다.
2. `validate_amount(value: Any) -> int` 는 **경계에서 타입을 좁히는** 지점임을 명시한다.
   CSV·대화형 입력은 전부 `str` 로 들어오지만 이 함수를 지나면 `int` 임이 보장된다.
3. 에디터가 `tx.` 에서 필드를 자동완성하고, 오타(`tx.amont`)를 실행 전에 잡아준다.

---

## §4. 확장 사고 및 트러블슈팅

### 4.1 JSONL vs CSV 장단점 비교와 “왜” 그 포맷을 택했는지 ✅

[README.md](README.md) **§8 "저장 포맷 선택 — JSONL vs CSV"** 에 6개 축(구조/타입/추가 쓰기/
스트리밍/가독성/상호운용성) 비교표와 선택 근거 4가지가 정리되어 있다.

요지: **내부 저장은 JSONL, 경계에서의 교환은 CSV** 로 역할을 나눴다.
JSONL 선택 이유는 ① 레코드 단위 O(1) append 와 스트리밍 ② 타입·구조(`tags` 리스트) 보존
③ 원자적 교체와의 궁합 ④ 한 줄이 깨져도 손상 격리. 반대로 Excel·타 도구와 주고받는
import/export 는 상호운용성이 가장 좋은 CSV 를 쓴다.

### 4.2 거래가 10만 건으로 늘어나면 병목이 어디이며 “어떻게” 개선할지 ✅

[README.md](README.md) **§9 "대용량(100k+) 성능 — 병목과 개선안"** 에 병목 4곳을 원인·개선안과
함께 표로 식별하고, 규모별(수만 / 10만 / 100만) 임계치 가이드를 제시했다.

| 병목 | 개선안 |
| --- | --- |
| B1 `stream_sorted` 정렬 메모리 O(k) | 정렬 불변식 유지 / `heapq.nlargest(N)` / 외부 정렬 |
| B2 import 시 행마다 `next_id()` 전체 재스캔 → O(N²) | **개선 완료** — `max_id_num()` 1회 + 메모리 연속 발급 → O(N) |
| B3 `--atomic` 커밋의 전량 재작성 | 원자성의 대가로 감수 / 초대용량은 부분 성공 모드 |
| B4 단일 파일 전체 스캔 | 월별 샤딩 / `id→offset` 인덱스 / SQLite 이전 |

### 4.3 import CSV 에 깨진 행이 섞이면 “어떻게” 처리해 사용자 신뢰를 지킬지 ✅

[README.md](README.md) **§7 "가져오기 실패 정책"** 에 **부분 성공 / 전수 롤백** 두 정책을
표로 문서화하고, 선택 기준("일부만 들어가면 안 되는 정산 데이터는 `--atomic`")을 제시했다.

| 모드 | 옵션 | 깨진 행이 있을 때 | 종료 코드 |
| --- | --- | --- | --- |
| 부분 성공 (기본) | *(없음)* | 그 줄만 skip, 나머지 저장 + 오류 라인 리포트 | `0` |
| 전수 롤백 | `--atomic` | 아무것도 저장하지 않음 | `4` |

세 요소(**부분 성공 / 롤백 / 리포트**)가 모두 구현되어 있다:
- 리포트: `[완료] mode=..., imported=N, skipped=M` + `[오류 라인 일부]`
- 롤백: 준비→커밋 2단계 + `os.replace` 원자적 교체 ([budget_app/services.py](budget_app/services.py) `import_csv`)
- → `test_import_with_broken_rows_is_consistent` — **어느 정책이든** "성공이면 유효 행 저장 +
  리포트 / 실패면 아무것도 미저장"의 일관성을 검증하고, 무효 행이 저장되는 것은 불허

---

## 재현 방법

```bash
cd codyssey_B2-1
uv sync --dev          # 가상환경 + pytest 설치
uv run pytest          # 자동화 테스트 46건
uv run python smoke_test.py   # 스모크 테스트
```

자세한 실행 결과·환경·테스트 설계 근거는 [TEST_REPORT.md](TEST_REPORT.md) 참고.

## 부기 — 검증 범위의 한계

- §2·§3 의 "설명할 수 있는가" 항목은 본질적으로 **구두 설명 역량**을 묻는다. 자동화 테스트는
  그 설명의 *근거가 코드·문서에 실재하는지*(모듈 분리, 클래스 경계, yield, 데코레이터, 타입 힌트)
  까지만 검증할 수 있으며, 위 문서의 설명 문단이 그 답변 초안에 해당한다.
- `test_add_interactive_persists_transaction` 은 프롬프트 순서가 명세와 다른 구현에서는
  skip 되도록 설계했다(본 프로젝트에서는 정상 통과).
