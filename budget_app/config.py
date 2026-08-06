"""값·정책 상수 — "프로그램이 무엇을 허용하는가"를 정하는 숫자와 이름.

``messages.py`` 와의 분업:

- **config.py** (이 파일) — *정책*. 유효한 타입 목록, 날짜 형식, 파일명, 한도,
  종료 코드처럼 **동작이 달라지는 값**. 바꾸면 프로그램이 다르게 동작한다.
- **messages.py**        — *문구*. 프롬프트·오류·힌트·출력 템플릿. 바꿔도 동작은
  같고 화면 글자만 바뀐다.

왜 나눴나: 이전에는 한 파일에 둘 다 있어서 ``models.py`` 가 CLI 한국어 문구까지
들어 있는 모듈에 의존했다. 도메인 계층이 화면 문구의 변경에 묶이는 구조였다.
지금은 정책만 필요한 모듈은 ``config`` 만, 화면에 글자를 내는 모듈만 ``messages``
를 import 한다.
"""

# ============================================================
# 도메인 정책
# ============================================================

VALID_TYPES = ("income", "expense")
DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "etc")

TYPE_INCOME = "income"
TYPE_EXPENSE = "expense"

# 날짜/월 형식
DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"


# ============================================================
# 저장소 / 파일
# ============================================================

DEFAULT_DATA_DIR = "./data"
TX_FILE_NAME = "transactions.jsonl"
CATEGORY_FILE_NAME = "categories.jsonl"
BUDGET_FILE_NAME = "budgets.jsonl"

TX_ID_PREFIX = "TX-"
TX_ID_PATTERN = r"^TX-(\d+)$"
TX_ID_FORMAT = "TX-{:06d}"
# 손상된 줄에서도 id 만은 건져내기 위한 완화된 패턴(JSON 파싱이 실패한 줄에 적용).
TX_ID_SCAN_PATTERN = r'"id"\s*:\s*"(TX-\d+)"'

FILE_ENCODING = "utf-8"
LINE_TERMINATOR = "\n"
TMP_SUFFIX = ".tmp"


# ============================================================
# 백업
# ============================================================

BACKUP_DIR_PREFIX = "backup_"
BACKUP_TS_FORMAT = "%Y%m%d_%H%M%S"
BACKUP_GLOB = "*.jsonl"


# ============================================================
# CSV 교환 스키마
# ============================================================

CSV_ENCODING = "utf-8"

# `id` 는 **선택** 컬럼이다. 내보내기는 기본으로 포함하고(왕복 시 중복 방지),
# 가져오기는 있으면 쓰고 없으면 새로 발급한다. 필수 컬럼은 예전과 동일하므로
# id 없는 외부 CSV 도 그대로 들어온다.
CSV_ID_COLUMN = "id"
CSV_FIELDS = ("id", "date", "type", "category", "amount", "memo", "tags")
CSV_FIELDS_WITHOUT_ID = ("date", "type", "category", "amount", "memo", "tags")
CSV_REQUIRED_COLUMNS = ("date", "type", "category", "amount")
CSV_TAG_SEPARATOR = ","
CSV_DATA_START_LINE = 2  # 1행은 헤더

# import 시 이미 존재하는 id 를 만났을 때의 정책
ON_DUPLICATE_SKIP = "skip"
ON_DUPLICATE_NEW_ID = "new-id"
ON_DUPLICATE_ERROR = "error"
ON_DUPLICATE_CHOICES = (ON_DUPLICATE_SKIP, ON_DUPLICATE_NEW_ID, ON_DUPLICATE_ERROR)
DEFAULT_ON_DUPLICATE = ON_DUPLICATE_SKIP


# ============================================================
# CLI 기본값 / 한도
# ============================================================

MAX_INPUT_RETRIES = 10
MAX_IMPORT_ERRORS = 5
DEFAULT_LIST_LIMIT = 20
DEFAULT_TOP_N = 5


# ============================================================
# 로거 이름 / 프로그램 메타
# ============================================================

LOGGER_NAME = "budget_app"
LOGGER_NAME_REPOSITORY = "budget_app.repository"
PROG_NAME = "budget_app"

# 디버그 스위치 — `--debug` 플래그와 동등한 환경변수 이름
DEBUG_ENV_VAR = "BUDGET_APP_DEBUG"
# 이 값들이면 '꺼짐'으로 본다. (단순히 "값이 있으면 켜짐"으로 하면
# BUDGET_APP_DEBUG=0 이 오히려 켜지는 사고가 난다.)
FALSY_ENV_VALUES = frozenset({"", "0", "false", "no", "off"})


# ============================================================
# 종료 코드
# ============================================================

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_VALIDATION = 2
EXIT_IO = 3
EXIT_APP = 4
EXIT_NO_CATEGORY = 5
EXIT_ENCODING = 6
EXIT_INTERRUPT = 130
