"""검색 명세(Specification) — 조합 가능한 거래 선택 조건.

## 이 패턴이 푸는 문제

리팩터 전 ``SearchFilter.matches`` 는 조건 6개를 **하드코딩된 AND** 로 검사했다::

    if self.date_from and tx.date < self.date_from: return False
    if self.category  and tx.category != self.category: return False
    ...
    return True

이 구조에서는 조건을 추가할 때마다 dataclass 필드와 ``matches`` 를 **동시에** 고쳐야
하고, "카테고리 A 또는 B", "이 태그는 제외" 같은 요구가 오면 if 사다리가 곱해진다.
AND 말고는 표현할 방법이 없기 때문이다.

Specification 패턴은 **조건 하나를 객체 하나로** 만들고, 객체끼리 ``&``·``|``·``~``
로 조합한다.

    spec = date_from & date_to & (InCategory("food") | InCategory("cafe")) & ~HasTag("정기")

## 무엇이 실제로 좋아졌나 — 그리고 무엇은 아닌가

**좋아진 것**: 판정 로직이 조건별로 분리돼 각각 따로 읽고 시험할 수 있다. 그리고
값 정규화가 각 명세 생성자로 들어갔다(아래 참조) — 이것이 실제 버그를 고쳤다.

**좋아지지 않은 것**: "조건을 추가하는 일이 클래스 하나 추가로 끝나고 기존 코드는
그대로"는 **사실이 아니다.** 예를 들어 ``--min-amount`` 를 붙이려면 지금도 네 곳을
고쳐야 한다.

===========================  ===============================
고쳐야 하는 곳               무엇을
===========================  ===============================
``specs.py``                 명세 클래스 추가
``queries.SearchFilter``     필드 추가
``queries._build_spec``      조립 분기 한 줄 추가
``cli/parser.py``            argparse 옵션 추가
===========================  ===============================

"기존 코드 무변경"이 성립하려면 조건이 **데이터로 들어오는** 구조여야 한다(예:
``{"min_amount": 5000}`` 를 명세로 번역하는 레지스트리). 이 프로그램의 조건은
argparse 옵션이라 어차피 CLI 를 고쳐야 하고, 그러면 위 표의 절반은 남는다.

## 조합 대수는 선행 투자다

``Or``/``Not``/연산자 오버로딩은 **지금 소비자가 없다.** ``SearchFilter`` 가 조립하는
것은 언제나 AND 하나뿐이다(``_build_spec``). 그 사실을 감추지 않고 적어 둔다.

그래도 남겨 두는 이유는 이 패턴의 가치가 "AND 를 객체로 만든 것"이 아니라
**"카테고리 A 또는 B", "이 태그는 제외" 같은 요구가 왔을 때 if 사다리를 곱하지
않아도 되는 것**에 있기 때문이다. 그때 필요한 것이 이미 있는 것과, 그때 가서
조합자를 설계하는 것은 다르다. 다만 지금 이득을 보고 있다고 말하면 거짓말이다.

## 연산자를 쓰는 이유

``And(Or(a, b), Not(c))`` 보다 ``(a | b) & ~c`` 가 읽기 쉽다. 파이썬은
``__and__``/``__or__``/``__invert__`` 를 오버로딩할 수 있어 명세 조합이 불리언 식과
같은 모양이 된다. 파이썬 관례상 ``and``/``or`` 키워드는 오버로딩할 수 없어서
비트 연산자를 빌려 쓰는 것이 이 패턴의 표준 관용구다.

## 정규화는 명세가 한다

각 명세가 생성자에서 ``validators`` 로 조건값을 정규화한다. 저장할 때와 찾을 때의
규칙이 어긋나면 검색은 **오류 없이 조용히** 틀린다(``--category " food"`` 가 아무것도
못 찾던 버그).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence

from . import validators
from .entities import Transaction


class Spec(ABC):
    """거래 하나가 조건을 만족하는지 판단하는 명세."""

    @abstractmethod
    def is_satisfied_by(self, tx: Transaction) -> bool: ...

    # ---------- 조합 ----------

    def __and__(self, other: "Spec") -> "Spec":
        return And(self, other)

    def __or__(self, other: "Spec") -> "Spec":
        return Or(self, other)

    def __invert__(self) -> "Spec":
        return Not(self)


# ============================================================
# 조합자
# ============================================================


class And(Spec):
    """전부 만족해야 참. 항이 없으면 참(항등원)."""

    def __init__(self, *specs: Spec) -> None:
        self.specs: Sequence[Spec] = _flatten(specs, And)

    def is_satisfied_by(self, tx: Transaction) -> bool:
        return all(s.is_satisfied_by(tx) for s in self.specs)

    def __repr__(self) -> str:
        return f"({' & '.join(repr(s) for s in self.specs)})" if self.specs else "Always()"


class Or(Spec):
    """하나라도 만족하면 참. 항이 없으면 거짓."""

    def __init__(self, *specs: Spec) -> None:
        self.specs: Sequence[Spec] = _flatten(specs, Or)

    def is_satisfied_by(self, tx: Transaction) -> bool:
        return any(s.is_satisfied_by(tx) for s in self.specs)

    def __repr__(self) -> str:
        return f"({' | '.join(repr(s) for s in self.specs)})"


class Not(Spec):
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def is_satisfied_by(self, tx: Transaction) -> bool:
        return not self.spec.is_satisfied_by(tx)

    def __repr__(self) -> str:
        return f"~{self.spec!r}"


class Always(Spec):
    """조건 없음 — 전부 통과.

    Null Object 다. ``list`` 처럼 조건이 하나도 없는 경우를 ``None`` 검사 없이
    같은 코드로 처리하려고 둔다. ``And()`` 의 항등원이기도 하다.
    """

    def is_satisfied_by(self, tx: Transaction) -> bool:
        return True

    def __repr__(self) -> str:
        return "Always()"


def _flatten(specs: Iterable[Spec], kind: type) -> Sequence[Spec]:
    """중첩된 같은 조합자를 편다 — ``(a & b) & c`` → ``And(a, b, c)``.

    조합을 왼쪽부터 이어 붙이면 ``And(And(a, b), c)`` 처럼 깊어진다. 결과는 같지만
    ``repr`` 이 읽기 어려워지고 평가가 한 겹 더 들어간다.
    """
    out = []
    for s in specs:
        if isinstance(s, kind):
            out.extend(s.specs)
        elif isinstance(s, Always) and kind is And:
            continue  # And 의 항등원은 버려도 된다
        else:
            out.append(s)
    return tuple(out)


# ============================================================
# 필드 명세
# ============================================================


class DateFrom(Spec):
    """``date >= value`` — ISO 8601 이라 문자열 비교가 곧 날짜 비교."""

    def __init__(self, value: str) -> None:
        self.value = validators.parse_date(value)

    def is_satisfied_by(self, tx: Transaction) -> bool:
        return tx.date >= self.value

    def __repr__(self) -> str:
        return f"DateFrom({self.value!r})"


class DateTo(Spec):
    """``date <= value``."""

    def __init__(self, value: str) -> None:
        self.value = validators.parse_date(value)

    def is_satisfied_by(self, tx: Transaction) -> bool:
        return tx.date <= self.value

    def __repr__(self) -> str:
        return f"DateTo({self.value!r})"


class InCategory(Spec):
    def __init__(self, name: str) -> None:
        self.name = validators.parse_category(name)

    def is_satisfied_by(self, tx: Transaction) -> bool:
        return tx.category == self.name

    def __repr__(self) -> str:
        return f"InCategory({self.name!r})"


class OfType(Spec):
    def __init__(self, type_: str) -> None:
        self.type = validators.parse_type(type_)

    def is_satisfied_by(self, tx: Transaction) -> bool:
        return tx.type == self.type

    def __repr__(self) -> str:
        return f"OfType({self.type!r})"


class MemoContains(Spec):
    """메모 부분 일치."""

    def __init__(self, query: str) -> None:
        self.query = str(query).strip()

    def is_satisfied_by(self, tx: Transaction) -> bool:
        return self.query in tx.memo

    def __repr__(self) -> str:
        return f"MemoContains({self.query!r})"


class HasTag(Spec):
    """태그 정확 일치."""

    def __init__(self, tag: str) -> None:
        self.tag = str(tag).strip()

    def is_satisfied_by(self, tx: Transaction) -> bool:
        return self.tag in tx.tags

    def __repr__(self) -> str:
        return f"HasTag({self.tag!r})"
