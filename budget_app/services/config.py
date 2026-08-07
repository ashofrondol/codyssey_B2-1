"""서비스 계층의 값·정책.

``ON_DUPLICATE_*`` 계열이 여기 통째로 있는 이유: 중복 정책은 **서비스가 판단**하는
것이고, CLI 의 ``--on-duplicate`` 는 그 선택지를 노출할 뿐이다. 열거값을 계층별로
쪼개면 "정책 하나가 두 파일에" 흩어진다.
"""

# 가져오기 — 이미 존재하는 id 를 만났을 때의 정책
ON_DUPLICATE_SKIP = "skip"
ON_DUPLICATE_NEW_ID = "new-id"
ON_DUPLICATE_ERROR = "error"
ON_DUPLICATE_CHOICES = (ON_DUPLICATE_SKIP, ON_DUPLICATE_NEW_ID, ON_DUPLICATE_ERROR)
DEFAULT_ON_DUPLICATE = ON_DUPLICATE_SKIP

# 한도·기본값
MAX_IMPORT_ERRORS = 5
DEFAULT_TOP_N = 5
