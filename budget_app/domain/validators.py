"""필드 규칙 — "이 값이 유효한가"를 판단하는 단 하나의 정의처.

리팩터 배경:

이전에는 같은 규칙이 세 형태로 존재했다. 모듈 함수 ``validate_amount``,
그것을 감싸기만 하는 ``Transaction.validate_amount`` staticmethod, 그리고
``Transaction.validate_type`` 처럼 클래스에 붙은 것들. staticmethod 들이 남아
있던 이유는 **CLI 의 재입력 루프가 검증기를 callable 로 넘겨야 했기 때문**이었다.
즉 하위 계층(모델)의 공개 API 모양이 상위 계층(CLI)의 구현 편의로 정해진,
의존 방향이 거꾸로 샌 상태였다.

지금은 규칙이 전부 이 모듈의 모듈 함수다.

- 모델 ``__post_init__`` 이 호출한다 → 생성자가 여전히 유일한 강제 지점이다.
- CLI 재입력 루프는 이 함수를 그대로 넘긴다 → 모델을 거치지 않는다.
- CSV 어댑터도 이 함수를 쓴다 → 경로가 달라도 규칙은 하나다.

규칙 = 함수 하나 = 파일 한 곳. 모든 함수는 **검증과 정규화를 함께** 수행하고
(공백 제거·소문자화 등) 정규화된 값을 돌려준다. 실패는 ``ValidationError``.

**거래 id 는 여기 없다.** 형식 검증뿐 아니라 번호 변환·생성·손상 줄 발굴이라는
고유 행동이 붙어 있어 값 객체(``tx_id.TransactionId``)로 따로 뺐다. 여기 남은 것은
"규칙이 함수 하나로 끝나는" 필드들이다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List

from . import config, messages
from ..errors import ValidationError


def parse_amount(value: Any) -> int:
    """금액을 양의 정수로 검증·정규화한다.

    ``int(str(value).strip())`` 인 이유: CSV 는 문자열 ``"1000"``, 대화형 입력도
    문자열, argparse ``type=int`` 는 이미 int 로 온다. 세 경로를 한 규칙으로
    받으려면 문자열로 정규화한 뒤 한 번에 파싱하는 편이 분기가 없다.
    """
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValidationError(messages.ERR_AMOUNT_NOT_INT) from exc
    if n <= 0:
        raise ValidationError(messages.ERR_AMOUNT_NOT_POSITIVE)
    return n


def parse_type(value: Any) -> str:
    v = str(value or "").strip().lower()
    if v not in config.VALID_TYPES:
        raise ValidationError(messages.ERR_TYPE_INVALID.format(types=config.VALID_TYPES))
    return v


def parse_date(value: Any) -> str:
    """날짜를 검증하고 **정규형 ``YYYY-MM-DD`` 로 재직렬화**한다.

    ``strptime`` 은 검증기이지 정규화기가 아니다 — ``"2024-1-5"`` 를 오류 없이
    받아 준다. 검증만 하고 원문을 돌려주면 같은 날이 파일에 두 표기로 공존하고,
    이 프로그램은 날짜를 **문자열로 비교**하므로(ISO 8601 이라 문자열 순서 = 날짜
    순서라는 전제) 그 순간 전제가 깨진다::

        "2024-1-5" <= "2024-01-31"   →   False

    즉 1월 5일 거래가 1월 요약·검색·내보내기에서 조용히 사라진다. 그래서
    ``strftime`` 으로 다시 찍어 **표기를 하나로 강제**한다. 기존 파일의 비정규
    표기도 읽는 순간 ``__post_init__`` 을 다시 지나므로 자동으로 치유된다.
    """
    v = str(value or "").strip()
    try:
        dt = datetime.strptime(v, config.DATE_FORMAT)
    except ValueError as exc:
        raise ValidationError(messages.ERR_DATE_INVALID) from exc
    return dt.strftime(config.DATE_FORMAT)


def parse_month(value: Any) -> str:
    """월을 검증하고 정규형 ``YYYY-MM`` 으로 재직렬화한다 — 이유는 ``parse_date`` 와 같다.

    예산은 월 문자열이 **사실상 키**라 영향이 더 직접적이다. ``budget set --month
    2024-1`` 로 넣은 값을 ``summary --month 2024-01`` 이 찾지 못했다.
    """
    v = str(value or "").strip()
    try:
        dt = datetime.strptime(v, config.MONTH_FORMAT)
    except ValueError as exc:
        raise ValidationError(messages.ERR_MONTH_INVALID) from exc
    return dt.strftime(config.MONTH_FORMAT)


def parse_category(value: Any) -> str:
    v = str(value or "").strip()
    if not v:
        raise ValidationError(messages.ERR_CATEGORY_EMPTY)
    return v


def parse_memo(value: Any) -> str:
    """메모는 빈 값이 허용된다 — 정규화만 한다."""
    return str(value or "").strip()


def parse_tags(value: Any) -> List[str]:
    """리스트 또는 쉼표 구분 문자열을 태그 리스트로 정규화한다.

    빈 항목은 버린다(``"a,,b"`` → ``["a", "b"]``). 태그 없음은 오류가 아니다.
    """
    if value is None:
        return []
    items = value if isinstance(value, list) else str(value).split(config.TAG_SEPARATOR)
    return [str(t).strip() for t in items if str(t).strip()]
