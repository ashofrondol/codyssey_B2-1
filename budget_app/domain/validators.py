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

import re
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from ..errors import ValidationError
from . import config, messages

#: 금액으로 받아들일 표기 — ``\d`` 가 아니라 ``[0-9]`` 인 것이 중요하다(아래 참조)
_INTEGER = re.compile(r"^[+-]?[0-9]+$")


def _require_utf8(text: str) -> str:
    """UTF-8 로 저장할 수 있는 문자열인가 — 아니면 ``ValidationError``.

    **왜 경계에서 막는가**: 파이썬은 비-UTF-8 바이트를 ``surrogateescape`` 로 읽으면
    대리 문자(U+DC80~U+DCFF)로 들고 있는다. 그 값이 그대로 저장되면 파일은 더 이상
    유효한 UTF-8 이 아니고, 나중에 엄격한 UTF-8 로 쓰는 경로(``export``)가
    ``UnicodeEncodeError`` 로 죽는다. **저장은 성공했다고 안내받은 거래를 영원히
    내보낼 수 없는 상태**가 된다(요구사항 F9).

    막을 자리는 입력 시점이다. 대화형 입력은 ``ask_until`` 이 ``ValidationError`` 를
    잡아 그 자리에서 다시 묻고, CSV 가져오기는 그 줄만 ``skipped`` 로 떨어진다.

    검사는 ``encode`` 한 번으로 한다. 문자별로 대리 영역을 훑는 것보다 빠르고
    (C 레벨), "우리가 실제로 쓸 코덱이 이 문자열을 받아 주는가"라는 질문 자체와
    같은 검사라 규칙이 어긋날 여지가 없다.
    """
    try:
        text.encode(config.TEXT_ENCODING)
    except UnicodeEncodeError as exc:
        raise ValidationError(messages.ERR_NOT_UTF8) from exc
    return text


def parse_amount(value: Any) -> int:
    """금액을 양의 정수로 검증·정규화한다.

    문자열을 거쳐 파싱하는 이유: CSV 는 문자열 ``"1000"``, 대화형 입력도 문자열,
    argparse ``type=int`` 는 이미 int 로 온다. 세 경로를 한 규칙으로 받으려면
    문자열로 정규화한 뒤 한 번에 파싱하는 편이 분기가 없다.

    **``int()`` 에 곧바로 맡기지 않는 이유**: 그 함수는 검증기로 쓰기에는 너무
    관대하다. 아래 셋을 전부 오류 없이 받아 준다.

    ==============  =======  ==========================================
    입력            ``int``  왜 문제인가
    ==============  =======  ==========================================
    ``"1_000"``     1000     파이썬 소스 문법이지 사용자가 친 금액이 아니다.
                             오타 ``1_00`` 이 100 으로 조용히 통과한다.
    ``"١٢٣"``       123      ``\\d`` 는 유니코드 숫자를 전부 포함한다. 저장된
                             값과 화면에 보이는 글자가 달라진다.
    ``"+100"``      100      부호를 붙인 표기가 CSV 마다 섞이면 왕복이 흔들린다.
    ==============  =======  ==========================================

    그래서 ``[0-9]`` 만으로 이뤄진 표기인지 먼저 본다. 부호는 통과시키되 값 검사
    (``n <= 0``)에서 걸리게 두는데, 그래야 음수에 "정수가 아니다" 대신
    "양수여야 한다"는 **맞는 이유**가 나간다.
    """
    text = str(value).strip()
    if not _INTEGER.match(text):
        raise ValidationError(messages.ERR_AMOUNT_NOT_INT)
    n = int(text)
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
    return _require_utf8(v)


def parse_memo(value: Any) -> str:
    """메모는 빈 값이 허용된다 — 정규화와 인코딩 검사만 한다."""
    return _require_utf8(str(value or "").strip())


def parse_tags(value: Any) -> list[str]:
    """리스트 또는 쉼표 구분 문자열을 태그 리스트로 정규화한다.

    빈 항목은 버린다(``"a,,b"`` → ``["a", "b"]``). 태그 없음은 오류가 아니다.

    **구분자를 품은 태그는 거부한다.** CSV 는 태그를 ``",".join(tags)`` 한 칸에
    담으므로, 태그 자체에 쉼표가 있으면 내보냈다가 다시 가져올 때 두 개로 쪼개진다.
    오류 없이 데이터가 바뀌는 부류라 **만들어지는 시점에 막는 것**이 맞다.
    이스케이프를 도입하는 길도 있지만 교환 포맷이 복잡해지고, 태그에 쉼표를 넣을
    실익이 그만한 값을 하지 않는다.

    **중복은 순서를 지키며 제거한다.** ``"a,b,a"`` → ``["a", "b"]``. 같은 태그가
    두 번 붙어 있으면 ``HasTag`` 판정은 같은데 표시만 지저분해진다.

    입력은 세 모양으로 들어온다 — CSV/대화형의 **쉼표 문자열**, JSON 의 **리스트**,
    그리고 엔티티가 이미 정규화해 둔 **튜플**(``Transaction.tags``). 앞의 둘만
    처리하고 "리스트가 아니면 문자열" 로 떨어뜨리면, 튜플이 ``str(("a","b"))`` 로
    찍혀 ``["('a'", "'b')"]`` 같은 것이 된다. 기본값 ``()`` 도 마찬가지로
    ``["()"]`` 가 된다 — 오류 없이 데이터가 바뀌는 부류라 특히 위험하다.
    그래서 **문자열만 나누고, 나머지 순회 가능한 것은 그대로** 받는다.

    **UTF-8 로 쓸 수 없는 태그도 거부한다** — 이유는 ``_require_utf8`` 참조.
    """
    if value is None:
        return []
    if isinstance(value, str):
        items: Iterable[Any] = value.split(config.TAG_SEPARATOR)
    elif isinstance(value, Iterable):
        items = value
    else:
        items = [value]

    seen: list[str] = []
    for item in items:
        tag = str(item).strip()
        if not tag:
            continue
        if config.TAG_SEPARATOR in tag:
            raise ValidationError(
                messages.ERR_TAG_HAS_SEPARATOR.format(tag=tag, sep=config.TAG_SEPARATOR)
            )
        _require_utf8(tag)
        if tag not in seen:
            seen.append(tag)
    return seen
