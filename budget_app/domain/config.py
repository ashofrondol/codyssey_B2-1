"""도메인 계층의 값·정책 — 필드 형식과 거래 ID 규칙.

``VALID_TYPES`` 와 ``TAG_SEPARATOR`` 는 위 계층(cli/storage)도 쓰지만 **소유는 여기**다.
"수입/지출이 무엇인가", "태그를 무엇으로 나누는가"는 도메인 규칙이고, argparse 의
``choices`` 나 CSV 의 join 은 그 규칙을 **빌려 쓰는** 것이다.
"""

# 도메인 정책 — 거래 타입 어휘
TYPE_INCOME = "income"
TYPE_EXPENSE = "expense"

#: 허용 타입 목록은 위 둘에서 **파생**시킨다. 리터럴을 두 번 적으면 하나만 고치는
#: 사고가 난다(이전에는 VALID_TYPES 가 문자열을 직접 갖고 TYPE_EXPENSE 는 아무도
#: 쓰지 않는 죽은 상수였다).
VALID_TYPES = (TYPE_INCOME, TYPE_EXPENSE)

#: 태그 구분자 — 도메인 규칙이고 CSV 는 이것을 빌려 쓴다(이전 이름: CSV_TAG_SEPARATOR)
TAG_SEPARATOR = ","

# 날짜/월 형식
DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"

# 거래 ID — 형식·검증·발굴 세 패턴이 값 객체(tx_id.TransactionId)와 짝을 이룬다
TX_ID_PATTERN = r"^TX-(\d+)$"
TX_ID_FORMAT = "TX-{:06d}"
TX_ID_SCAN_PATTERN = r'"id"\s*:\s*"(TX-\d+)"'
