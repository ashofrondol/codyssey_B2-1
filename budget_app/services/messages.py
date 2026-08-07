"""서비스 계층의 문자열 — ``AppError`` 의 message / hint.

``ERR_`` 과 ``HINT_`` 가 **짝을 이루는** 것이 이 앱 오류 UX 의 뼈대다. 같은 오류라도
문맥에 따라 힌트가 다르다 — ``ERR_CATEGORY_NOT_REGISTERED`` 는 ``add`` 에서
"등록하거나 목록을 확인하세요", ``update`` 에서 "등록하세요"를 쓴다.
"""

# 카테고리 / 거래
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

# 가져오기
ERR_ATOMIC_IMPORT_FAILED = "원자적 가져오기 실패 — line {lineno}: {reason} (반영된 항목 없음)"
HINT_ATOMIC_IMPORT = "CSV 를 고쳐 다시 시도하거나, --atomic 없이 부분 가져오기를 사용하세요."
ERR_DUPLICATE_ID = "이미 존재하는 거래 id 입니다: {tx_id}"
HINT_DUPLICATE_ID = "`--on-duplicate new-id` 로 새 id 를 발급하거나, CSV 의 id 컬럼을 비우세요."
FMT_IMPORT_ERROR = "line {lineno}: {reason}"
FMT_IMPORT_DUPLICATE = "line {lineno}: 중복 id {tx_id} — 건너뜀"
ERR_UNKNOWN_DUPLICATE_POLICY = "알 수 없는 중복 정책입니다: {policy}"
