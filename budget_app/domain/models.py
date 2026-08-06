"""도메인 모델 — 저장 엔티티와 계산 결과 모델.

두 종류가 들어 있다.

1. **저장 엔티티** — ``Transaction`` / ``Budget`` / ``Category``.
   ``__post_init__`` 이 ``validators`` 를 호출해 **생성자가 유일한 불변식 강제
   지점**이 되게 한다. 서비스·CLI·``from_dict``·직접 호출 어느 경로로 만들어져도
   객체가 존재하는 순간 이미 검증·정규화가 끝나 있다.

2. **결과 모델** — ``MonthlySummary`` / ``ImportReport``.
   이전에는 서비스가 문자열 키 dict 를 돌려주고 CLI 가 ``result["usage_pct"]``
   처럼 꺼내 썼다. 오타는 런타임 ``KeyError`` 였고, "예산이 없으면 N/A" 같은
   *상태 해석* 이 화면 코드에 섞여 있었다. 파생값을 ``@property`` 로 모델에
   두면 서비스·프레젠터·테스트가 같은 정의 하나를 공유한다.

캘린더 규칙(``month_range``)도 여기 있다. 이전에는 CLI 가 ``calendar.monthrange``
로 말일을 구하고, 서비스는 ``date.startswith(month + "-")`` 로 판정해서 **같은
개념이 두 계층에 서로 다른 알고리즘으로** 구현돼 있었다.
"""

from __future__ import annotations

import calendar
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .. import config
from . import validators

__all__ = [
    "Budget",
    "Category",
    "ImportReport",
    "MonthlySummary",
    "SearchFilter",
    "Transaction",
    "TransactionPatch",
    "month_range",
]


# ============================================================
# 기간 규칙
# ============================================================


def month_range(month: str) -> Tuple[str, str]:
    """``'YYYY-MM'`` → ``('YYYY-MM-01', 'YYYY-MM-<그 달의 말일>')``.

    모든 달을 31일로 가정하면 2월·30일 달에서 범위가 어긋난다. ``calendar`` 로
    실제 말일을 구한다. 검색·요약·내보내기가 모두 이 함수 하나를 쓰므로
    "이 달에 속하는가"의 정의가 프로그램 전체에서 하나다.
    """
    normalized = validators.parse_month(month)
    dt = datetime.strptime(normalized, config.MONTH_FORMAT)
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return f"{normalized}-01", f"{normalized}-{last_day:02d}"


# ============================================================
# 저장 엔티티
# ============================================================


@dataclass
class Transaction:
    """단일 거래 내역.

    필드 계약:
        id       : "TX-000001" 형식의 유일 ID
        type     : "income" 또는 "expense"
        date     : "YYYY-MM-DD"
        amount   : 양의 정수
        category : 카테고리명(공백 정규화됨)
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
        self.id = validators.parse_tx_id(self.id)
        self.type = validators.parse_type(self.type)
        self.date = validators.parse_date(self.date)
        self.amount = validators.parse_amount(self.amount)
        self.category = validators.parse_category(self.category)
        self.memo = validators.parse_memo(self.memo)
        self.tags = validators.parse_tags(self.tags)

    @property
    def id_number(self) -> int:
        return validators.tx_id_number(self.id)

    def to_dict(self) -> dict:
        return asdict(self)

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


@dataclass
class Budget:
    """월별 예산. month 는 'YYYY-MM' 문자열."""

    month: str
    amount: int

    def __post_init__(self) -> None:
        self.month = validators.parse_month(self.month)
        self.amount = validators.parse_amount(self.amount)

    def to_dict(self) -> dict:
        return {"month": self.month, "amount": self.amount}

    @classmethod
    def from_dict(cls, data: dict) -> "Budget":
        return cls(month=data["month"], amount=data["amount"])


@dataclass
class Category:
    """카테고리. 이름은 고유하게 관리된다."""

    name: str

    def __post_init__(self) -> None:
        self.name = validators.parse_category(self.name)

    def to_dict(self) -> dict:
        return {"name": self.name}

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        return cls(name=data["name"])


# ============================================================
# 질의 모델
# ============================================================


@dataclass
class SearchFilter:
    """거래 검색 조건 — 모든 조회 경로가 공유하는 단 하나의 필터.

    ``__post_init__`` 에서 조건값도 **엔티티와 똑같은 규칙으로 정규화**한다.
    이전에는 CLI 가 ``--category`` 를 날것으로 넘겨서, 저장된 값은 공백이 제거돼
    있는데 조건은 그렇지 않아 ``--category " food"`` 가 아무것도 못 찾았다.
    "저장할 때의 규칙"과 "찾을 때의 규칙"이 다르면 검색은 조용히 틀린다.
    """

    date_from: Optional[str] = None  # YYYY-MM-DD
    date_to: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None  # income/expense
    query: Optional[str] = None  # memo 부분 일치
    tag: Optional[str] = None

    def __post_init__(self) -> None:
        self.date_from = validators.parse_date(self.date_from) if self.date_from else None
        self.date_to = validators.parse_date(self.date_to) if self.date_to else None
        self.category = validators.parse_category(self.category) if self.category else None
        self.type = validators.parse_type(self.type) if self.type else None
        self.query = str(self.query).strip() if self.query else None
        self.tag = str(self.tag).strip() if self.tag else None

    @classmethod
    def for_month(cls, month: str, **extra: Any) -> "SearchFilter":
        """월 전체를 덮는 필터 — 요약과 내보내기가 같은 경계를 쓰게 한다."""
        start, end = month_range(month)
        return cls(date_from=start, date_to=end, **extra)

    def matches(self, tx: Transaction) -> bool:
        if self.date_from and tx.date < self.date_from:
            return False
        if self.date_to and tx.date > self.date_to:
            return False
        if self.category and tx.category != self.category:
            return False
        if self.type and tx.type != self.type:
            return False
        if self.query and self.query not in tx.memo:
            return False
        if self.tag and self.tag not in tx.tags:
            return False
        return True


# ============================================================
# 결과 모델 (읽기 전용 계산 결과)
# ============================================================


@dataclass(frozen=True)
class MonthlySummary:
    """월별 요약 — 집계 원자료만 담고 파생값은 property 로 계산한다.

    ``usage_pct`` 가 ``None`` 인 경우가 둘("예산 미설정" / "예산이 0")인데,
    화면에서는 둘 다 ``N/A`` 로 같게 보인다. 그 판단 근거를 모델에 두면
    프레젠터는 ``None`` 여부만 보면 되고 규칙을 몰라도 된다.
    """

    month: str
    income: int
    expense: int
    top_expense: Tuple[Tuple[str, int], ...]
    has_data: bool
    budget: Optional[Budget] = None

    @property
    def balance(self) -> int:
        return self.income - self.expense

    @property
    def usage_pct(self) -> Optional[float]:
        if self.budget is None or self.budget.amount <= 0:
            return None
        return round((self.expense / self.budget.amount) * 100, 1)

    @property
    def over_budget(self) -> bool:
        return self.budget is not None and self.expense > self.budget.amount

    @property
    def is_empty(self) -> bool:
        """보여줄 것이 아무것도 없는가 — 거래도 예산도 없을 때만 참."""
        return not self.has_data and self.budget is None


@dataclass(frozen=True)
class ImportReport:
    """CSV 가져오기 결과.

    ``skipped`` 와 ``duplicated`` 를 나눈 이유: 둘 다 "저장되지 않음"이지만
    사용자가 해야 할 일이 정반대다. ``skipped`` 는 데이터가 잘못돼 **고쳐야**
    하고, ``duplicated`` 는 이미 저장돼 있어서 **아무것도 안 해도 된다**.
    한 숫자로 합치면 정상 왕복인데 실패처럼 읽힌다.
    """

    imported: int = 0
    skipped: int = 0
    duplicated: int = 0
    errors: Tuple[str, ...] = ()
    duplicate_notes: Tuple[str, ...] = ()

    @property
    def has_problems(self) -> bool:
        return bool(self.errors or self.duplicate_notes)
