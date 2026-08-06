"""사용자에게 노출되는 모든 문자열 — 프롬프트·오류·힌트·출력·로그 템플릿.

원칙:

- 화면에 글자를 내는 모듈만 이 파일을 import 한다. 정책 값만 필요한 모듈
  (``validators``, ``models`` 의 계산부 등)은 ``config`` 만 보면 된다.
- 동적 부분이 있는 메시지는 ``str.format`` 자리표시자를 쓰는 템플릿으로 둔다.
  (예: ``messages.MSG_SAVED_TX.format(id=...)``)
- **로그 메시지만 %-스타일**이다. ``logging`` 에 인자를 그대로 넘겨야 레벨이
  꺼져 있을 때 포매팅 비용이 발생하지 않기 때문이다.
- argparse 의 인자별 ``help`` 문자열은 인자 정의 옆에 두는 편이 읽기 좋아
  ``parser.py`` 에 남겼다.
"""

# ============================================================
# 프로그램 메타
# ============================================================

PROG_DESCRIPTION = "파일 기반 가계부 콘솔 프로그램"


# ============================================================
# 로그 메시지 (%-스타일 — logging 에 그대로 전달)
# ============================================================

# 핸들러 포맷 — 평상시엔 짧게, --debug 에선 어디서 나온 로그인지까지.
LOG_FORMAT = "[%(levelname)s] %(message)s"
LOG_FORMAT_DEBUG = "[%(levelname)s] %(asctime)s %(name)s:%(lineno)d %(message)s"

LOG_CALL = "call %s"
LOG_DONE = "done %s"
LOG_TOOK = "%s took %.2fms"
LOG_UNHANDLED = "unhandled error"
LOG_CORRUPT_LINE = "%s:%d 손상된 줄을 건너뜁니다: %s"
LOG_CORRUPT_PRESERVED = "%s: 손상된 줄 %d개를 해석하지 않고 원문 그대로 보존했습니다."


# ============================================================
# 필드 검증 오류 (ValidationError 메시지)
# ============================================================

ERR_AMOUNT_NOT_INT = "금액은 정수여야 합니다."
ERR_AMOUNT_NOT_POSITIVE = "금액은 양의 정수여야 합니다 (0 또는 음수 불가)."
ERR_TYPE_INVALID = "type 은 {types} 중 하나여야 합니다."
ERR_DATE_INVALID = "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)."
ERR_MONTH_INVALID = "월 형식이 올바르지 않습니다 (YYYY-MM)."
ERR_CATEGORY_EMPTY = "카테고리명은 비어있을 수 없습니다."
ERR_TX_ID_INVALID = "거래 id 형식이 올바르지 않습니다 (TX-000001 형식): {value}"


# ============================================================
# 서비스 오류/힌트 (AppError message / hint)
# ============================================================

ERR_CATEGORY_NOT_REGISTERED = "등록되지 않은 카테고리입니다: {name}"
HINT_CATEGORY_ADD_OR_LIST = "`category add` 로 먼저 등록하거나 `category list` 로 목록을 확인하세요."
HINT_CATEGORY_ADD = "`category add` 로 먼저 등록하세요."
ERR_TX_NOT_FOUND = "해당 id 의 거래를 찾을 수 없습니다: {tx_id}"
HINT_LIST_ID = "`list` 로 id 를 확인하세요."
ERR_CATEGORY_NOT_EXIST = "존재하지 않는 카테고리입니다: {name}"
HINT_CATEGORY_LIST = "`category list` 로 목록을 확인하세요."
ERR_CATEGORY_IN_USE = "카테고리 '{name}' 는 거래에서 사용 중입니다."
HINT_REPLACE_WITH = "`--replace-with <카테고리>` 로 대체 카테고리를 지정하세요."
ERR_REPLACE_NOT_REGISTERED = "대체 카테고리가 등록되어 있지 않습니다: {name}"
HINT_ADD_FIRST = "먼저 `category add` 로 등록하세요."
ERR_REPLACE_SELF = "대체 카테고리는 자기 자신일 수 없습니다."


# ============================================================
# CSV 가져오기/내보내기
# ============================================================

ERR_CSV_MISSING = "CSV 헤더에 필수 컬럼이 없습니다: {missing}"
HINT_CSV_REQUIRED = "필수 컬럼: {columns}"
ERR_CSV_NO_HEADER = "CSV 에 헤더 행이 없습니다: {path}"
HINT_CSV_NO_HEADER = "첫 줄에 `{columns}` 형태의 헤더를 넣어 주세요."
ERR_ATOMIC_IMPORT_FAILED = "원자적 가져오기 실패 — line {lineno}: {reason} (반영된 항목 없음)"
HINT_ATOMIC_IMPORT = "CSV 를 고쳐 다시 시도하거나, --atomic 없이 부분 가져오기를 사용하세요."
ERR_DUPLICATE_ID = "이미 존재하는 거래 id 입니다: {tx_id}"
HINT_DUPLICATE_ID = "`--on-duplicate new-id` 로 새 id 를 발급하거나, CSV 의 id 컬럼을 비우세요."
FMT_IMPORT_ERROR = "line {lineno}: {reason}"
FMT_IMPORT_DUPLICATE = "line {lineno}: 중복 id {tx_id} — 건너뜀"


# ============================================================
# CLI 프롬프트
# ============================================================

PROMPT_DATE = "날짜(YYYY-MM-DD): "
PROMPT_TYPE = "타입(income/expense): "
PROMPT_CATEGORY = "카테고리: "
PROMPT_AMOUNT = "금액(양수): "
PROMPT_MEMO = "메모(선택): "
PROMPT_TAGS = "태그(쉼표로 구분, 없으면 엔터): "
PROMPT_CATEGORY_NAME = "카테고리명: "


# ============================================================
# CLI 입력/에러 표시 (공통 래퍼 + 개별 메시지)
# ============================================================

MSG_ERROR_LINE = "[오류] {msg}"
MSG_HINT_LINE = "[힌트] {msg}"
MSG_HINT_RETRY = "[힌트] 다시 입력해 주세요."

ERR_INPUT_ABORTED = "입력이 중단되었습니다 (EOF)."
HINT_INPUT_ABORTED = "대화형 명령은 필요한 값을 표준입력으로 끝까지 제공해야 합니다."
ERR_MAX_RETRIES = "재입력 횟수를 초과했습니다."
HINT_MAX_RETRIES = "올바른 형식으로 값을 입력한 뒤 다시 시도해 주세요."
ERR_CATEGORY_NOT_REGISTERED_AVAILABLE = "등록되지 않은 카테고리입니다: {name} (사용 가능: {available})"
ERR_MONTH_ARG_INVALID = "--month 형식이 올바르지 않습니다 (YYYY-MM)."


# ============================================================
# CLI 출력 — 표/요약/명령별 결과
# ============================================================

# 공통 표
MSG_NO_DATA = "(데이터 없음)"
FMT_TX_LINE = "{id} | {date} | {type:<7} | {category} | {amount} | {memo}"

# add
MSG_NO_CATEGORIES = "[안내] 등록된 카테고리가 없습니다. 먼저 `category add` 로 추가하세요."
MSG_ADD_INTERACTIVE = "[안내] 거래 추가 - 대화형 입력입니다."
MSG_SAVED_TX = "[저장 완료] id={id}"

# summary
MSG_SUMMARY_NO_DATA = "{month}: 데이터 없음"
MSG_SUMMARY_INCOME = "총 수입: {income}원"
MSG_SUMMARY_EXPENSE = "총 지출: {expense}원"
MSG_SUMMARY_BALANCE = "잔액: {balance}원"
FMT_USAGE_PCT = "{usage}%"
MSG_USAGE_NA = "N/A"
MSG_SUMMARY_BUDGET = "예산: {amount}원 (사용률 {usage})"
MSG_OVER_BUDGET = "[경고] 예산을 초과했습니다!"
MSG_TOP_EXPENSE_HEADER = "\n지출 TOP {n}"
FMT_TOP_EXPENSE_ITEM = "{rank}) {category} {amount}원"

# budget
MSG_SAVED_BUDGET = "[저장 완료] {month} 예산 {amount}원"

# category
MSG_SAVED_CATEGORY = "[저장 완료] category={name}"
MSG_CATEGORY_EXISTS = "[안내] 이미 존재하는 카테고리입니다: {name}"
MSG_NO_CATEGORIES_LISTED = "(등록된 카테고리 없음)"
FMT_CATEGORY_ITEM = "- {name}"
ERR_NAME_REQUIRED = "--name 이 필요합니다."
HINT_CATEGORY_REMOVE = "`category remove --name <카테고리>`"
MSG_CATEGORY_REMOVED_REASSIGNED = "[완료] '{name}' 삭제, {count}건을 '{replace_with}' 로 재지정했습니다."
MSG_CATEGORY_REMOVED = "[완료] '{name}' 삭제"

# update
ERR_NO_UPDATE_FIELDS = "수정할 필드가 없습니다."
HINT_UPDATE_FIELDS = "--date/--type/--category/--amount/--memo/--tags 중 하나 이상 지정하세요."
MSG_UPDATED_TX = "[수정 완료] id={id}"

# delete
MSG_DELETED_TX = "[삭제 완료] id={id}"

# export
ERR_EXPORT_PERIOD_REQUIRED = "--month 또는 --from/--to 중 하나는 필수입니다."
HINT_EXPORT_PERIOD = "예: `export --out a.csv --month 2024-01`"
MSG_EXPORT_DONE = "[완료] {out} ({count} records)"

# import
MODE_ATOMIC = "원자(전수 롤백)"
MODE_PARTIAL = "부분 성공"
MSG_IMPORT_DONE = "[완료] mode={mode}, imported={imported}, duplicated={duplicated}, skipped={skipped}"
MSG_IMPORT_ERROR_HEADER = "[오류 라인 일부]"
FMT_IMPORT_ERROR_ITEM = "  - {error}"
MSG_IMPORT_DUPLICATE_HINT = "[힌트] 중복은 이미 저장된 거래입니다. 다시 넣으려면 `--on-duplicate new-id` 를 쓰세요."

# backup
MSG_BACKUP_DONE = "[백업 완료] {dest}"


# ============================================================
# 예외 처리 표시 (decorators.handle_errors)
# ============================================================

HINT_VALIDATION = "[힌트] 입력값을 다시 확인해 주세요."
MSG_ERR_FILE_NOT_FOUND = "[오류] 파일을 찾을 수 없습니다: {name}"
HINT_FILE_NOT_FOUND = "[힌트] 경로가 올바른지, 파일이 존재하는지 확인해 주세요."
MSG_ERR_IS_A_DIR = "[오류] 파일이 아니라 디렉터리입니다: {name}"
HINT_IS_A_DIR = "[힌트] 파일 경로를 지정했는지 확인해 주세요."
MSG_ERR_PERMISSION = "[오류] 파일 접근 권한이 없습니다: {name}"
HINT_PERMISSION = "[힌트] 읽기/쓰기 권한, 또는 다른 프로그램이 파일을 열고 있는지 확인해 주세요."
MSG_ERR_ENCODING = "[오류] 파일 인코딩을 읽을 수 없습니다 (UTF-8 이 아닙니다)."
HINT_ENCODING = "[힌트] CSV 를 UTF-8 로 다시 저장하세요 (엑셀: '다른 이름으로 저장 > CSV UTF-8')."
MSG_INTERRUPTED = "\n[중단] 사용자에 의해 종료되었습니다."
MSG_ERR_IO = "[오류] 입출력 오류가 발생했습니다: {error}"
HINT_IO = "[힌트] 디스크 여유 공간과 파일 경로/권한을 확인해 주세요."
MSG_ERR_UNEXPECTED = "[오류] 예기치 못한 오류가 발생했습니다: {error}"
HINT_UNEXPECTED = "[힌트] `--debug` 를 붙여 다시 실행하면 stderr 로그에 스택트레이스가 남습니다."
