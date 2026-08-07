"""저장소 계층의 값·정책 — 파일명, 인코딩, CSV 교환 스키마, 백업.

``DEFAULT_CATEGORIES`` 가 여기 있는 이유: 기본 카테고리는 "빈 파일을 만났을 때
무엇을 심을 것인가"라는 **부트스트랩 정책**이고, 그 판단과 실행이 모두
``CategoryStore.seed_defaults`` 에 있다.
"""

from .. import config as app_config

# 로거 — 저장소 로그만 따로 조정할 수 있게 앱 로거의 자식으로 둔다
LOGGER_NAME = app_config.LOGGER_NAME_STORAGE

# 부트스트랩
DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "etc")

# 파일
TX_FILE_NAME = "transactions.jsonl"
CATEGORY_FILE_NAME = "categories.jsonl"
BUDGET_FILE_NAME = "budgets.jsonl"
#: 발급된 최대 거래 번호를 남기는 파일 — JSONL 이 아니라 숫자 한 줄이다
ID_COUNTER_FILE_NAME = "id_counter"
FILE_ENCODING = "utf-8"
LINE_TERMINATOR = "\n"
TMP_SUFFIX = ".tmp"

# 백업
BACKUP_DIR_PREFIX = "backup_"
BACKUP_TS_FORMAT = "%Y%m%d_%H%M%S"
BACKUP_GLOB = "*.jsonl"
#: glob 에 걸리지 않지만 데이터인 파일 — 빠뜨리면 복원 후 id 재사용이 되살아난다
BACKUP_EXTRA_FILES = (ID_COUNTER_FILE_NAME,)

# CSV 교환 스키마 — `id` 는 **선택** 컬럼이다(왕복 시 중복 방지, 외부 CSV 호환 유지)
CSV_ENCODING = "utf-8"
CSV_ID_COLUMN = "id"
CSV_FIELDS = ("id", "date", "type", "category", "amount", "memo", "tags")
CSV_FIELDS_WITHOUT_ID = ("date", "type", "category", "amount", "memo", "tags")
CSV_REQUIRED_COLUMNS = ("date", "type", "category", "amount")
CSV_DATA_START_LINE = 2  # 1행은 헤더
