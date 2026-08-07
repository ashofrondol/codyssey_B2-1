"""저장 엔티티 — 파일에 기록되는 도메인 객체.

``__post_init__`` 이 ``validators`` 를 호출해 **생성자가 유일한 불변식 강제 지점**이
되게 한다. 서비스·CLI·``from_dict``·``with_patch`` 어느 경로로 만들어져도 객체가
존재하는 순간 이미 검증·정규화가 끝나 있다.

``TransactionPatch`` 도 여기 있다 — 저장되지는 않지만 엔티티의 **변경 요청**이라
엔티티와 함께 읽히는 편이 자연스럽다.

결과 모델(``MonthlySummary``/``ImportReport``)은 저장되지 않고 생명주기가 달라
``results.py`` 로 분리했다.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Dict, List, Optional, Tuple

from . import validators
from .tx_id import TransactionId


# ============================================================
# 저장 엔티티
# ============================================================


@dataclass(frozen=True)
class Transaction:
    """단일 거래 내역.

    필드 계약:
        id       : ``TransactionId`` 값 객체 (``TX-000001`` 형식)
        type     : "income" 또는 "expense"
        date     : "YYYY-MM-DD"
        amount   : 양의 정수
        category : 카테고리명(공백 정규화됨)
        memo     : 자유 문자열 (없으면 빈 문자열)
        tags     : 태그 튜플 (없으면 빈 튜플)

    ``id`` 만 값 객체이고 나머지는 원시 타입인 이유: id 는 형식 규칙(``TX-`` + 6자리),
    번호 변환, 손상 줄 발굴이라는 **고유 행동**이 붙어 있어 타입이 값을 한다.
    ``date``/``category`` 는 규칙이 ``validators`` 함수 하나로 끝나 값 객체를 만들면
    직렬화만 복잡해진다.

    ## ``frozen=True`` 인 이유

    이 클래스의 docstring 은 오래전부터 "생성자가 유일한 불변식 강제 지점"이라고
    말해 왔는데, 정작 만들어진 뒤에 ``tx.amount = -1`` 이 그냥 됐다. 생성자가
    유일한 강제 지점이 되려면 **생성자 이후에 바꿀 수 없어야** 한다.

    수정은 이미 ``with_patch`` 가 새 객체를 만드는 방식이라 제자리 수정 코드는
    한 곳도 없었다 — 즉 이 전환은 이미 지키고 있던 규약을 타입으로 굳힌 것이다.

    ``tags`` 가 리스트가 아니라 **튜플**인 것도 같은 이유다. ``frozen`` 은 필드를
    다시 묶는 것만 막지 리스트 안을 바꾸는 것(``tx.tags.append(...)``)은 막지
    못한다. 튜플이면 그 구멍이 닫히고, 덤으로 ``Transaction`` 이 해시 가능해진다
    (``frozen`` 이 만들어 주는 ``__hash__`` 는 필드가 전부 해시 가능해야 동작한다).
    """

    id: TransactionId
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # TransactionId 를 받든 문자열을 받든 같은 결과가 되게 한다
        # (JSONL 은 문자열로, 서비스는 값 객체로 넘긴다).
        # frozen 이라 대입 대신 object.__setattr__ 로 정규화한다 — 생성자가 끝나는
        # 순간 객체는 검증·정규화가 끝난 상태로 굳는다.
        _set = object.__setattr__
        _set(self, "id", TransactionId.parse(self.id))
        _set(self, "type", validators.parse_type(self.type))
        _set(self, "date", validators.parse_date(self.date))
        _set(self, "amount", validators.parse_amount(self.amount))
        _set(self, "category", validators.parse_category(self.category))
        _set(self, "memo", validators.parse_memo(self.memo))
        _set(self, "tags", tuple(validators.parse_tags(self.tags)))

    @property
    def id_number(self) -> int:
        return self.id.number

    def to_dict(self) -> dict:
        """JSONL 한 줄이 될 dict.

        ``asdict()`` 를 쓸 수 없다 — ``TransactionId`` 가 dataclass 라
        ``{"id": {"value": "TX-000001"}}`` 처럼 중첩돼 저장 형식이 깨진다.
        값 객체는 **경계에서 원시 값으로 풀어** 내보낸다.
        """
        return {
            "id": self.id.value,
            "type": self.type,
            "date": self.date,
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        # 필수 키는 하드 접근(누락 시 KeyError → 저장소가 손상 줄로 처리).
        # 검증·정규화는 __post_init__ 이 일괄 수행하므로 여기서는 형태만 넘긴다.
        return cls(
            id=data["id"],
            type=data["type"],
            date=data["date"],
            amount=data["amount"],
            category=data["category"],
            memo=data.get("memo"),
            tags=data.get("tags"),
        )

    def with_patch(self, patch: "TransactionPatch") -> "Transaction":
        """부분 변경을 적용한 **새 Transaction** 을 만든다.

        수정이 도메인 연산인 이유: 이전에는 저장소가
        ``to_dict() → dict.update(changes) → from_dict()`` 를 수행했다. 즉
        "무엇으로 바꿀지 해석하고 규칙을 다시 적용하는" 도메인 작업이 파일 계층에
        있었다. 이제 저장소는 완성된 객체를 받아 쓰기만 한다.

        새 객체를 만드는(제자리 수정이 아닌) 이유: ``__post_init__`` 을 다시 통과
        시켜 변경 후에도 불변식이 성립함을 생성자가 보장하게 하기 위해서다.
        """
        return Transaction(**{**self.to_dict(), **patch.changed_fields()})


@dataclass(frozen=True)
class TransactionPatch:
    """거래 부분 수정 요청 — ``None`` 인 필드는 "변경 없음"을 뜻한다.

    이전의 ``changes: Dict[str, object]`` 를 대체한다. 문자열 키 dict 는
    CLI→서비스→저장소 세 계층을 그대로 통과했고, 키를 잘못 쓰면 오류도 없이
    **조용히 무시**됐다(``from_dict`` 가 정해진 키만 읽으므로). 필드가 선언된
    dataclass 로 바꾸면 오타가 ``TypeError`` 로 즉시 드러나고 타입체커도 잡는다.
    """

    date: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[int] = None
    memo: Optional[str] = None
    tags: Optional[List[str]] = None

    def changed_fields(self) -> Dict[str, Any]:
        """``None`` 이 아닌 필드만 골라 dict 로 준다."""
        return {f.name: getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}

    @property
    def is_empty(self) -> bool:
        return not self.changed_fields()


@dataclass(frozen=True)
class Budget:
    """월별 예산. month 는 'YYYY-MM' 문자열."""

    month: str
    amount: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "month", validators.parse_month(self.month))
        object.__setattr__(self, "amount", validators.parse_amount(self.amount))

    def to_dict(self) -> dict:
        return {"month": self.month, "amount": self.amount}

    @classmethod
    def from_dict(cls, data: dict) -> "Budget":
        return cls(month=data["month"], amount=data["amount"])


@dataclass(frozen=True)
class Category:
    """카테고리. 이름은 고유하게 관리된다."""

    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", validators.parse_category(self.name))

    def to_dict(self) -> dict:
        return {"name": self.name}

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        return cls(name=data["name"])
