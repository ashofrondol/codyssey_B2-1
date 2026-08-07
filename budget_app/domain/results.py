"""결과 모델 — 계산으로 만들어지고 저장되지 않는 값.

이전에는 서비스가 문자열 키 dict 를 돌려주고 CLI 가 ``result["usage_pct"]`` 처럼
꺼내 썼다. 오타는 런타임 ``KeyError`` 였고, "예산이 없으면 N/A" 같은 *상태 해석* 이
화면 코드에 섞여 있었다.

파생값을 ``@property`` 로 두면 서비스·프레젠터·테스트가 같은 정의 하나를 공유한다.
전부 ``frozen`` 인 이유: 이미 계산이 끝난 값이라 바뀌면 안 된다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .entities import Budget


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
class RejectedRow:
    """데이터가 잘못돼 가져오지 못한 CSV 한 행 — 줄 번호와 사유."""

    lineno: int
    reason: str


@dataclass(frozen=True)
class DuplicateRow:
    """이미 저장된 id 라 건너뛴 CSV 한 행 — 줄 번호와 그 id."""

    lineno: int
    tx_id: str


@dataclass(frozen=True)
class ImportReport:
    """CSV 가져오기 결과.

    ``skipped`` 와 ``duplicated`` 를 나눈 이유: 둘 다 "저장되지 않음"이지만
    사용자가 해야 할 일이 정반대다. ``skipped`` 는 데이터가 잘못돼 **고쳐야**
    하고, ``duplicated`` 는 이미 저장돼 있어서 **아무것도 안 해도 된다**.
    한 숫자로 합치면 정상 왕복인데 실패처럼 읽힌다.

    ## 왜 문자열이 아니라 구조체를 담나

    이전에는 ``errors`` 가 ``"line 3: 금액은 양의 정수여야 합니다"`` 처럼 **포맷이
    끝난 사용자 문장**이었다. 그러면 서비스가 화면 문구를 결정하게 되고,
    "3번 줄만 다시 보여 줘" 같은 요구가 오면 문자열을 되파싱해야 한다.

    같은 파일의 ``MonthlySummary`` 는 이미 반대로 하고 있었다 — 원자료만 담고
    표시는 프레젠터가 만든다. 두 결과 모델이 서로 다른 규칙을 따를 이유가 없다.
    """

    imported: int = 0
    skipped: int = 0
    duplicated: int = 0
    errors: Tuple[RejectedRow, ...] = ()
    duplicates: Tuple[DuplicateRow, ...] = ()

    @property
    def has_problems(self) -> bool:
        return bool(self.errors or self.duplicates)
