"""데이터 모델 정의 (dataclass 기반)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date as _date, datetime
from typing import Any, List, Optional


VALID_TYPES = ("income", "expense")


class ValidationError(ValueError):
    """입력 검증 오류 — CLI 단에서 사용자 친화 메시지로 변환된다."""


def validate_amount(value: Any) -> int:
    """금액을 양의 정수로 검증·정규화한다.

    Transaction·Budget 공용 규칙이므로 특정 엔티티에 묶지 않고 모듈 함수로 둔다
    (한쪽 클래스가 다른 클래스의 static 메서드로 손을 뻗는 결합을 없앤다).
    """
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValidationError("금액은 정수여야 합니다.") from exc
    if n <= 0:
        raise ValidationError("금액은 양의 정수여야 합니다 (0 또는 음수 불가).")
    return n


@dataclass
class Transaction:
    """단일 거래 내역.

    필드 계약:
        id       : "TX-000001" 형식의 유일 ID
        type     : "income" 또는 "expense"
        date     : "YYYY-MM-DD" (검증 통과된 문자열)
        amount   : 양의 정수
        category : 등록된 카테고리명
        memo     : 자유 문자열 (없으면 빈 문자열)
        tags     : 태그 리스트 (없으면 빈 리스트)
    """

    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # 생성자 자체가 불변식을 강제하는 유일한 지점이다. 서비스/CLI/from_dict/직접
        # 호출 등 어느 경로로 만들어지든 이 시점에 항상 검증·정규화가 끝나 있다.
        self.id = str(self.id)
        self.type = self.validate_type(self.type)
        self.date = self.validate_date(self.date)
        self.amount = self.validate_amount(self.amount)
        self.category = str(self.category).strip()
        self.memo = str(self.memo or "").strip()
        self.tags = self.parse_tags(self.tags)

    @staticmethod
    def validate_type(value: str) -> str:
        v = (value or "").strip().lower()
        if v not in VALID_TYPES:
            raise ValidationError(f"type 은 {VALID_TYPES} 중 하나여야 합니다.")
        return v

    @staticmethod
    def validate_date(value: str) -> str:
        v = (value or "").strip()
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as exc:
            raise ValidationError("날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).") from exc
        return v

    @staticmethod
    def validate_amount(value: Any) -> int:
        # 공용 규칙은 모듈 함수에 있다(Budget 도 같은 규칙을 쓴다). CLI 의 _ask_until
        # 이 이 staticmethod 를 callable 로 넘겨 쓰므로 얇은 위임으로 남겨 둔다.
        return validate_amount(value)

    @staticmethod
    def parse_tags(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            items = value
        else:
            items = [t for t in str(value).split(",")]
        return [t.strip() for t in items if t and t.strip()]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        # 필수 키는 하드 접근(누락 시 KeyError → stream 이 손상 줄로 skip).
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


@dataclass
class Budget:
    """월별 예산. month 는 'YYYY-MM' 문자열."""

    month: str
    amount: int

    def __post_init__(self) -> None:
        self.month = self.validate_month(self.month)
        self.amount = validate_amount(self.amount)  # 모듈 공용 규칙

    @staticmethod
    def validate_month(value: str) -> str:
        v = (value or "").strip()
        try:
            datetime.strptime(v, "%Y-%m")
        except ValueError as exc:
            raise ValidationError("월 형식이 올바르지 않습니다 (YYYY-MM).") from exc
        return v

    def to_dict(self) -> dict:
        return {"month": self.month, "amount": self.amount}

    @classmethod
    def from_dict(cls, data: dict) -> "Budget":
        # 검증은 __post_init__ 이 수행한다(Transaction 참조 제거).
        return cls(month=data["month"], amount=data["amount"])


@dataclass
class Category:
    """카테고리. 이름은 고유하게 관리된다."""

    name: str

    def __post_init__(self) -> None:
        self.name = self.normalize(self.name)

    @staticmethod
    def normalize(value: str) -> str:
        v = (value or "").strip()
        if not v:
            raise ValidationError("카테고리명은 비어있을 수 없습니다.")
        return v

    def to_dict(self) -> dict:
        return {"name": self.name}

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        # 정규화는 __post_init__ 이 수행한다(빈 값이면 ValidationError → stream 이 skip).
        return cls(name=data["name"])
