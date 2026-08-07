"""질의 모델 — 거래를 어떻게 고를 것인가.

``SearchFilter`` 는 ``list``/``search``/``summary``/``export`` 네 명령이 공유하는 단
하나의 필터다. **조건 판정은 하지 않는다** — 그건 ``specs`` 의 Specification 조합이
하고, 이 모듈은 **CLI 인자를 명세로 조립하는 어댑터**다.

## 왜 어댑터를 남겨 두나

명세만으로 충분해 보이지만, CLI 인자는 "지정 안 하면 조건 없음"이라는 규칙을 갖는
**평평한 옵션 묶음**이다. 그 모양을 명세 트리로 번역하는 자리가 필요하다.

    SearchFilter(category="food", tag="meal")
        → InCategory('food') & HasTag('meal')

    SearchFilter()          # 조건 하나도 없음
        → Always()

어댑터가 없으면 CLI 핸들러마다 "None 이면 건너뛰고 아니면 명세를 만들어 & 로 잇는"
코드가 반복된다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from . import specs
from .entities import Transaction
from .periods import month_range


@dataclass
class SearchFilter:
    """거래 검색 조건 — CLI 옵션 묶음을 명세로 번역한다.

    각 필드는 "지정 안 하면 조건 없음"을 뜻하는 ``Optional`` 이다. 값 정규화는
    각 명세의 생성자가 수행하므로(``InCategory`` 가 ``parse_category`` 를 부른다)
    여기서는 조립만 한다 — **규칙은 한 곳에만** 있어야 하기 때문이다.

    잘못된 값을 주면 명세를 만드는 시점에 ``ValidationError`` 가 난다. 그래서 CLI
    핸들러는 날짜를 미리 검증할 필요가 없다.
    """

    date_from: Optional[str] = None  # YYYY-MM-DD
    date_to: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None  # income/expense
    query: Optional[str] = None  # memo 부분 일치
    tag: Optional[str] = None

    #: 조립된 명세 — 생성 시 한 번만 만든다(거래마다 다시 만들지 않는다)
    spec: specs.Spec = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.spec = self._build_spec()

    def _build_spec(self) -> specs.Spec:
        """지정된 조건만 골라 AND 로 잇는다. 하나도 없으면 ``Always``."""
        parts: List[specs.Spec] = []
        if self.date_from:
            parts.append(specs.DateFrom(self.date_from))
        if self.date_to:
            parts.append(specs.DateTo(self.date_to))
        if self.category:
            parts.append(specs.InCategory(self.category))
        if self.type:
            parts.append(specs.OfType(self.type))
        if self.query:
            parts.append(specs.MemoContains(self.query))
        if self.tag:
            parts.append(specs.HasTag(self.tag))
        return specs.And(*parts) if parts else specs.Always()

    @classmethod
    def for_month(cls, month: str, **extra: Any) -> "SearchFilter":
        """월 전체를 덮는 필터 — 요약과 내보내기가 같은 경계를 쓰게 한다."""
        start, end = month_range(month)
        return cls(date_from=start, date_to=end, **extra)

    def matches(self, tx: Transaction) -> bool:
        """조립해 둔 명세에 판정을 위임한다."""
        return self.spec.is_satisfied_by(tx)
