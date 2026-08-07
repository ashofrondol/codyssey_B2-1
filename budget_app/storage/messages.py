"""저장소 계층의 문자열 — 손상 줄 로그와 CSV 헤더 오류.

로그만 %-스타일인 이유: ``logging`` 에 템플릿과 인자를 따로 넘겨야 레벨이 꺼져
있을 때 포매팅 비용이 발생하지 않는다.
"""

# 로그 (%-스타일 — logging 에 그대로 전달)
LOG_CORRUPT_LINE = "%s:%d 손상된 줄을 건너뜁니다: %s"
LOG_CORRUPT_PRESERVED = "%s: 손상된 줄 %d개를 해석하지 않고 원문 그대로 보존했습니다."
LOG_WATERMARK_CORRUPT = "%s 의 내용을 숫자로 읽을 수 없습니다(%r) — 파일 스캔 값만 사용합니다."

# CSV 헤더 오류 (AppError message / hint)
ERR_CSV_MISSING = "CSV 헤더에 필수 컬럼이 없습니다: {missing}"
HINT_CSV_REQUIRED = "필수 컬럼: {columns}"
ERR_CSV_NO_HEADER = "CSV 에 헤더 행이 없습니다: {path}"
HINT_CSV_NO_HEADER = "첫 줄에 `{columns}` 형태의 헤더를 넣어 주세요."
