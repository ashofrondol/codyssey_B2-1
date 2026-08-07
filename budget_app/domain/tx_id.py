"""거래 ID 값 객체 — 형식·검증·생성·발굴이 한곳에.

## 왜 값 객체로 모았나

리팩터 전에는 "거래 ID"라는 **하나의 개념이 네 곳**에 나뉘어 있었다.

| 조각 | 있던 곳 |
|---|---|
| 형식 문자열 3종 (`TX_ID_FORMAT`/`PATTERN`/`SCAN_PATTERN`) | ``config.py`` |
| ``parse_tx_id`` / ``tx_id_number`` | ``domain/validators.py`` |
| ``Transaction.id_number`` property | ``domain/models.py`` |
| 번호 발급 | ``storage/repository.py`` |

ID 형식을 바꾸려면 네 파일을 열어야 했다. 값 객체(Value Object)는 "값 + 그 값에
대한 규칙"을 한 타입으로 묶는 패턴이고, 이 개념이 정확히 그 대상이다.

## 무엇이 여기 있고 무엇이 없나

**여기 있는 것**: 형식이 무엇인가, 유효한가, 번호로 어떻게 바꾸는가,
손상된 줄에서 어떻게 건져내는가.

**여기 없는 것**: "다음 번호가 몇인가". 그건 **저장된 내용을 봐야** 정해지므로
도메인이 아니라 저장소(``storage.ids.IdAllocator``)의 일이다. 값 객체는 파일을
모른다.

## 왜 문자열이 아니라 타입인가

``str`` 로 두면 ``tx.id`` 와 ``tx.category`` 가 타입상 구분되지 않는다. 값 객체는
"이 문자열은 아무 문자열이 아니라 거래 ID 다"를 타입으로 말한다. ``frozen`` 이라
만들어진 뒤 바뀌지 않고, 그래서 set/dict 키로도 쓸 수 있다(``IdAllocator`` 가
``taken`` 집합에 담는다).
"""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass
from typing import Any

from ..errors import ValidationError
from . import config, messages

#: 전체가 이 형식이어야 한다 — 검증용
_EXACT = re.compile(config.TX_ID_PATTERN)

#: 줄 어딘가에 있으면 된다 — JSON 이 깨진 줄에서 id 만 건져낼 때
_SCAN = re.compile(config.TX_ID_SCAN_PATTERN)


@functools.total_ordering
@dataclass(frozen=True)
class TransactionId:
    """``TX-000001`` 형식의 거래 식별자 — 만들어지는 순간 **정규형**이 된다.

    ## 정규화가 왜 필수인가

    형식 검사만 하면 ``TX-1`` 과 ``TX-000001`` 이 **다른 값으로 공존**한다. 정규식
    ``^TX-(\\d+)$`` 는 둘 다 통과시키기 때문이다. 그러면 같은 거래를 가리키는 두
    표기가 서로 다른 dict 키·set 원소가 되고, 무엇보다:

    - ``IdAllocator`` 의 ``taken`` 집합이 중복을 거르지 못해 같은 번호가 두 번 발급된다.
    - ``get("TX-1")`` 이 ``TX-000001`` 을 찾지 못한다.
    - 문자열 정렬이 자릿수 순서가 되어 ``TX-10`` 이 ``TX-9`` 앞에 온다.

    그래서 ``__post_init__`` 이 번호를 뽑아 ``TX_ID_FORMAT`` 으로 **다시 찍는다**.
    기존 파일의 비정규 id 도 읽는 순간 이 생성자를 지나므로 자동으로 치유된다.

    ## 순서 비교는 번호로 한다

    ``stream_sorted`` 가 ``(date, id)`` 튜플로 정렬하는데, 날짜가 같은 거래가 둘
    이상이면 튜플 비교가 id 까지 내려온다. 비교 연산이 없으면 그 순간 ``TypeError``
    가 난다 — 날짜가 전부 다르면 드러나지 않는 잠재 버그다.

    ``dataclass(order=True)`` 대신 ``__lt__`` 를 직접 쓴 이유: 그쪽은 ``value``
    문자열을 비교하는데, 그것이 숫자 순서와 일치하려면 "폭이 항상 같다"는 전제가
    필요하다. 100만 건을 넘기면 ``TX-1000000``(7자리)이 ``TX-999999``(6자리)보다
    **작다**고 판정된다. 번호로 비교하면 그 전제 자체가 사라진다.
    """

    value: str

    def __post_init__(self) -> None:
        # frozen dataclass 라 object.__setattr__ 로 정규화한다.
        v = str(self.value or "").strip()
        m = _EXACT.match(v)
        if not m:
            raise ValidationError(messages.ERR_TX_ID_INVALID.format(value=v))
        object.__setattr__(self, "value", config.TX_ID_FORMAT.format(int(m.group(1))))

    def __lt__(self, other: Any) -> Any:
        """번호 순서로 비교한다. ``total_ordering`` 이 나머지 셋을 채운다."""
        if not isinstance(other, TransactionId):
            return NotImplemented
        return self.number < other.number

    # ---------- 생성 ----------

    @classmethod
    def of(cls, number: int) -> TransactionId:
        """번호로부터 만든다 — ``7`` → ``TX-000007``."""
        return cls(config.TX_ID_FORMAT.format(number))

    @classmethod
    def parse(cls, value: Any) -> TransactionId:
        """검증하며 만든다. 실패는 ``ValidationError``."""
        return cls(str(value or "").strip())

    @classmethod
    def scan(cls, raw_text: str) -> TransactionId | None:
        """줄 원문에서 id 를 발굴한다 — 찾지 못하면 ``None``.

        JSON 파싱조차 실패한 줄에도 id 는 들어 있을 수 있고, 그 번호는 **이미 쓰인
        번호**다. 놓치면 재발급으로 중복 id 가 생긴다.
        """
        m = _SCAN.search(raw_text)
        return cls(m.group(1)) if m else None

    # ---------- 조회 ----------

    @property
    def number(self) -> int:
        """``TX-000007`` → ``7``."""
        return int(_EXACT.match(self.value).group(1))

    def __str__(self) -> str:
        return self.value


def is_valid(value: Any) -> bool:
    """예외 없이 형식만 확인한다 — 분기가 필요한 곳에서 쓴다."""
    return bool(_EXACT.match(str(value or "").strip()))
