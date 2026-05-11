"""데이터 모델 정의 (dataclass 기반)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date as _date, datetime
from typing import Any, List, Optional


VALID_TYPES = ("income", "expense")


class ValidationError(ValueError):
    """입력 검증 오류 — CLI 단에서 사용자 친화 메시지로 변환된다."""


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
        try:
            n = int(str(value).strip())
        except (TypeError, ValueError) as exc:
            raise ValidationError("금액은 정수여야 합니다.") from exc
        if n <= 0:
            raise ValidationError("금액은 양의 정수여야 합니다 (0 또는 음수 불가).")
        return n

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
        tags = data.get("tags") or []
        if isinstance(tags, str):
            tags = cls.parse_tags(tags)
        return cls(
            id=str(data["id"]),
            type=cls.validate_type(data["type"]),
            date=cls.validate_date(data["date"]),
            amount=cls.validate_amount(data["amount"]),
            category=str(data["category"]).strip(),
            memo=str(data.get("memo") or ""),
            tags=list(tags),
        )


@dataclass
class Budget:
    """월별 예산. month 는 'YYYY-MM' 문자열."""

    month: str
    amount: int

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
        return cls(
            month=cls.validate_month(data["month"]),
            amount=Transaction.validate_amount(data["amount"]),
        )


@dataclass
class Category:
    """카테고리. 이름은 고유하게 관리된다."""

    name: str

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
        return cls(name=cls.normalize(data["name"]))
