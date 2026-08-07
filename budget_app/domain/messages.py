"""도메인 계층의 사용자 노출 문자열 — 필드 검증 실패 메시지.

전부 ``ValidationError`` 에 실려 나간다. **값 하나만 보고 판단되는** 오류라
저장된 상태를 언급하지 않는다(그건 서비스 계층의 ``AppError`` 몫이다).
"""

ERR_AMOUNT_NOT_INT = "금액은 정수여야 합니다."
ERR_AMOUNT_NOT_POSITIVE = "금액은 양의 정수여야 합니다 (0 또는 음수 불가)."
ERR_TYPE_INVALID = "type 은 {types} 중 하나여야 합니다."
ERR_DATE_INVALID = "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)."
ERR_MONTH_INVALID = "월 형식이 올바르지 않습니다 (YYYY-MM)."
ERR_CATEGORY_EMPTY = "카테고리명은 비어있을 수 없습니다."
ERR_TAG_HAS_SEPARATOR = "태그에 구분자 '{sep}' 를 쓸 수 없습니다 (CSV 왕복 시 쪼개집니다): {tag}"
ERR_TX_ID_INVALID = "거래 id 형식이 올바르지 않습니다 (TX-000001 형식): {value}"
