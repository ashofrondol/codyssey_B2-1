"""CLI 계층의 값·정책 — 한도, 기본값, 종료 코드.

종료 코드가 여기 있는 이유: **셸에게 무엇을 말할 것인가**는 CLI 의 계약이다.
서비스는 ``AppError`` 를 던질 뿐 그것이 4번인지 모른다.
"""

from .. import config as app_config

PROG_NAME = "budget_app"
LOGGER_NAME = app_config.LOGGER_NAME

# 기본값 / 한도
DEFAULT_DATA_DIR = "./data"
MAX_INPUT_RETRIES = 10
DEFAULT_LIST_LIMIT = 20

# 디버그 스위치 — `--debug` 와 동등한 환경변수
DEBUG_ENV_VAR = "BUDGET_APP_DEBUG"
FALSY_ENV_VALUES = frozenset({"", "0", "false", "no", "off"})

# 종료 코드
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_VALIDATION = 2
EXIT_IO = 3
EXIT_APP = 4
EXIT_NO_CATEGORY = 5
EXIT_ENCODING = 6
EXIT_INTERRUPT = 130
