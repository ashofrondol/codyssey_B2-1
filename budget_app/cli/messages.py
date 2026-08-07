"""CLI 계층의 사용자 노출 문자열 — 전체의 3분의 2가 여기 있다.

프롬프트·결과·오류 표시가 전부 이 계층의 것이다. 이전에는 도메인 검증 메시지 7개와
이 71개가 한 파일에 있어서, ``domain/validators.py`` 가 CLI 한국어 문구까지 들어 있는
모듈에 의존했다.

동적 부분은 ``str.format`` 템플릿으로 둔다. **로그 포맷만 %-스타일**인데, ``logging``
에 인자를 그대로 넘겨야 레벨이 꺼져 있을 때 포매팅 비용이 발생하지 않기 때문이다.
argparse 의 인자별 ``help`` 는 인자 정의 옆에 두는 편이 읽기 좋아 ``parser.py`` 에 남겼다.
"""

# 프로그램 메타
PROG_DESCRIPTION = "파일 기반 가계부 콘솔 프로그램"

# 로그 포맷 (%-스타일)
LOG_FORMAT = "[%(levelname)s] %(message)s"
LOG_FORMAT_DEBUG = "[%(levelname)s] %(asctime)s %(name)s:%(lineno)d %(message)s"
LOG_UNHANDLED = "unhandled error"

# 대화형 프롬프트
PROMPT_DATE = "날짜(YYYY-MM-DD): "
PROMPT_TYPE = "타입(income/expense): "
PROMPT_CATEGORY = "카테고리: "
PROMPT_AMOUNT = "금액(양수): "
PROMPT_MEMO = "메모(선택): "
PROMPT_TAGS = "태그(쉼표로 구분, 없으면 엔터): "
PROMPT_CATEGORY_NAME = "카테고리명: "

# 입력/오류 표시 공통 래퍼
MSG_ERROR_LINE = "[오류] {msg}"
MSG_HINT_LINE = "[힌트] {msg}"
MSG_HINT_RETRY = "[힌트] 다시 입력해 주세요."
ERR_INPUT_ABORTED = "입력이 중단되었습니다 (EOF)."
HINT_INPUT_ABORTED = "대화형 명령은 필요한 값을 표준입력으로 끝까지 제공해야 합니다."
ERR_MAX_RETRIES = "재입력 횟수를 초과했습니다."
HINT_MAX_RETRIES = "올바른 형식으로 값을 입력한 뒤 다시 시도해 주세요."
#: 상황의 이름("등록되지 않은 카테고리입니다")은 services.messages 가 소유한다.
#: 여기서는 **대화형에서만 의미 있는** 덧말만 갖는다 — 다시 칠 수 있으니 목록을 보여 준다.
FMT_AVAILABLE_SUFFIX = " (사용 가능: {available})"

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

# budget / category
MSG_SAVED_BUDGET = "[저장 완료] {month} 예산 {amount}원"
MSG_SAVED_CATEGORY = "[저장 완료] category={name}"
MSG_CATEGORY_EXISTS = "[안내] 이미 존재하는 카테고리입니다: {name}"
MSG_NO_CATEGORIES_LISTED = "(등록된 카테고리 없음)"
FMT_CATEGORY_ITEM = "- {name}"
ERR_ARG_NOT_INT = "정수여야 합니다: {value}"
ERR_ARG_NOT_POSITIVE = "1 이상이어야 합니다: {value}"
ERR_NAME_REQUIRED = "--name 이 필요합니다."
HINT_CATEGORY_REMOVE = "`category remove --name <카테고리>`"
MSG_CATEGORY_REMOVED_REASSIGNED = (
    "[완료] '{name}' 삭제, {count}건을 '{replace_with}' 로 재지정했습니다."
)
MSG_CATEGORY_REMOVED = "[완료] '{name}' 삭제"

# update / delete
ERR_NO_UPDATE_FIELDS = "수정할 필드가 없습니다."
HINT_UPDATE_FIELDS = "--date/--type/--category/--amount/--memo/--tags 중 하나 이상 지정하세요."
MSG_UPDATED_TX = "[수정 완료] id={id}"
MSG_DELETED_TX = "[삭제 완료] id={id}"

# export / import
ERR_EXPORT_PERIOD_REQUIRED = "--month 또는 --from/--to 중 하나는 필수입니다."
ERR_EXPORT_PERIOD_CONFLICT = (
    "--month 와 --from/--to 는 함께 쓸 수 없습니다 (기간 정의가 둘이 됩니다)."
)
HINT_EXPORT_PERIOD = "예: `export --out a.csv --month 2024-01`"
MSG_EXPORT_DONE = "[완료] {out} ({count} records)"
MODE_ATOMIC = "원자(전수 롤백)"
MODE_PARTIAL = "부분 성공"
MSG_IMPORT_DONE = (
    "[완료] mode={mode}, imported={imported}, duplicated={duplicated}, skipped={skipped}"
)
MSG_IMPORT_ERROR_HEADER = "[오류 라인 일부]"
FMT_IMPORT_ERROR_ITEM = "  - line {lineno}: {reason}"
FMT_IMPORT_DUPLICATE_ITEM = "  - line {lineno}: 중복 id {tx_id} — 건너뜀"
MSG_IMPORT_DUPLICATE_HINT = (
    "[힌트] 중복은 이미 저장된 거래입니다. 다시 넣으려면 `--on-duplicate new-id` 를 쓰세요."
)

# backup
MSG_BACKUP_DONE = "[백업 완료] {dest}"

# 예외 처리 표시 (error_handler)
HINT_VALIDATION = "[힌트] 입력값을 다시 확인해 주세요."
MSG_ERR_FILE_NOT_FOUND = "[오류] 파일을 찾을 수 없습니다: {name}"
HINT_FILE_NOT_FOUND = "[힌트] 경로가 올바른지, 파일이 존재하는지 확인해 주세요."
MSG_ERR_IS_A_DIR = "[오류] 파일이 아니라 디렉터리입니다: {name}"
HINT_IS_A_DIR = "[힌트] 파일 경로를 지정했는지 확인해 주세요."
MSG_ERR_NOT_A_DIR = "[오류] 디렉터리가 아닙니다: {name}"
HINT_NOT_A_DIR = "[힌트] `--data-dir` 에는 데이터를 담을 **폴더** 경로를 지정해 주세요."
MSG_ERR_PERMISSION = "[오류] 파일 접근 권한이 없습니다: {name}"
HINT_PERMISSION = "[힌트] 읽기/쓰기 권한, 또는 다른 프로그램이 파일을 열고 있는지 확인해 주세요."
MSG_ERR_ENCODING = "[오류] 파일 인코딩을 읽을 수 없습니다 (UTF-8 이 아닙니다)."
HINT_ENCODING = "[힌트] CSV 를 UTF-8 로 다시 저장하세요 (엑셀: '다른 이름으로 저장 > CSV UTF-8')."
MSG_INTERRUPTED = "\n[중단] 사용자에 의해 종료되었습니다."
MSG_ERR_IO = "[오류] 입출력 오류가 발생했습니다: {error}"
HINT_IO = "[힌트] 디스크 여유 공간과 파일 경로/권한을 확인해 주세요."
MSG_ERR_UNEXPECTED = "[오류] 예기치 못한 오류가 발생했습니다: {error}"
HINT_UNEXPECTED = "[힌트] `--debug` 를 붙여 다시 실행하면 stderr 로그에 스택트레이스가 남습니다."
