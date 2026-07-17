"""서비스 계층 — 검색/요약/예산 등 비즈니스 로직.

저장소(파일 I/O)와 CLI 사이에서 도메인 규칙을 담당한다.
모든 조회는 가능한 한 제너레이터를 그대로 흘려보내 스트리밍 특성을 유지한다.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from .decorators import AppError, log_call, measure_time
from .models import Budget, Category, Transaction, ValidationError
from .repository import BudgetStore, CategoryStore, TransactionRepository


# ---------- 검색 필터 ----------


@dataclass
class SearchFilter:
    date_from: Optional[str] = None  # YYYY-MM-DD
    date_to: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None  # income/expense
    query: Optional[str] = None  # memo 부분 일치
    tag: Optional[str] = None

    def matches(self, tx: Transaction) -> bool:
        if self.date_from and tx.date < self.date_from:
            return False
        if self.date_to and tx.date > self.date_to:
            return False
        if self.category and tx.category != self.category:
            return False
        if self.type and tx.type != self.type:
            return False
        if self.query and self.query not in (tx.memo or ""):
            return False
        if self.tag and self.tag not in (tx.tags or []):
            return False
        return True


# ---------- 서비스 ----------


class TransactionService:
    """거래 추가/검색/리스트 — 카테고리 검증 포함."""

    def __init__(self, txs: TransactionRepository, cats: CategoryStore):
        self.txs = txs
        self.cats = cats

    @log_call
    def add(
        self,
        date: str,
        type_: str,
        category: str,
        amount: int,
        memo: str = "",
        tags: Optional[List[str]] = None,
    ) -> Transaction:
        # 카테고리는 등록되어 있어야 한다.
        if not self.cats.exists(category):
            raise AppError(
                f"등록되지 않은 카테고리입니다: {category}",
                hint="`category add` 로 먼저 등록하거나 `category list` 로 목록을 확인하세요.",
            )
        tx = Transaction(
            id=self.txs.next_id(),
            type=Transaction.validate_type(type_),
            date=Transaction.validate_date(date),
            amount=Transaction.validate_amount(amount),
            category=category.strip(),
            memo=(memo or "").strip(),
            tags=Transaction.parse_tags(tags),
        )
        self.txs.append(tx)
        return tx

    @log_call
    def update(self, tx_id: str, changes: Dict[str, object]) -> Transaction:
        # 카테고리 변경 시 등록 여부 확인
        if "category" in changes and changes["category"] is not None:
            if not self.cats.exists(str(changes["category"])):
                raise AppError(
                    f"등록되지 않은 카테고리입니다: {changes['category']}",
                    hint="`category add` 로 먼저 등록하세요.",
                )
        updated = self.txs.update(tx_id, {k: v for k, v in changes.items() if v is not None})
        if updated is None:
            raise AppError(
                f"해당 id 의 거래를 찾을 수 없습니다: {tx_id}",
                hint="`list` 로 id 를 확인하세요.",
            )
        return updated

    @log_call
    def delete(self, tx_id: str) -> None:
        if not self.txs.delete(tx_id):
            raise AppError(
                f"해당 id 의 거래를 찾을 수 없습니다: {tx_id}",
                hint="`list` 로 id 를 확인하세요.",
            )

    def stream_sorted(self, flt: Optional[SearchFilter] = None) -> Iterator[Transaction]:
        """최신순 정렬된 거래를 yield 한다.

        주의: 정렬을 위해 한 번은 전체를 읽어야 한다(파일이 정렬되어 있지 않으므로).
        그러나 메모리 사용량은 '필터 통과 항목'으로 제한된다.
        """
        items: List[Transaction] = []
        for tx in self.txs.stream():
            if flt is None or flt.matches(tx):
                items.append(tx)
        items.sort(key=lambda t: (t.date, t.id), reverse=True)
        for it in items:
            yield it


class BudgetService:
    """예산 설정/조회 + 월별 요약."""

    def __init__(self, txs: TransactionRepository, budgets: BudgetStore):
        self.txs = txs
        self.budgets = budgets

    def set_budget(self, month: str, amount: int) -> Budget:
        return self.budgets.set(month, amount)

    @measure_time
    def monthly_summary(self, month: str, top_n: int = 5) -> dict:
        """월별 요약 계산.

        반환:
            {
              "month": "2024-01",
              "income": 3000000,
              "expense": 215000,
              "balance": 2785000,
              "has_data": True,
              "budget": Budget | None,
              "usage_pct": 43.0,         # 예산 있을 때만
              "over_budget": False,      # 예산 있을 때만
              "top_expense": [(category, amount), ...],
            }
        """
        target = Budget.validate_month(month)
        income_total = 0
        expense_total = 0
        per_category: Dict[str, int] = {}
        has_data = False

        for tx in self.txs.stream():
            if not tx.date.startswith(target + "-"):
                continue
            has_data = True
            if tx.type == "income":
                income_total += tx.amount
            else:
                expense_total += tx.amount
                per_category[tx.category] = per_category.get(tx.category, 0) + tx.amount

        top_expense: List[Tuple[str, int]] = sorted(
            per_category.items(), key=lambda kv: kv[1], reverse=True
        )[: max(0, int(top_n))]

        result = {
            "month": target,
            "income": income_total,
            "expense": expense_total,
            "balance": income_total - expense_total,
            "has_data": has_data,
            "top_expense": top_expense,
            "budget": None,
            "usage_pct": None,
            "over_budget": None,
        }

        budget = self.budgets.get(target)
        if budget is not None:
            result["budget"] = budget
            if budget.amount > 0:
                pct = (expense_total / budget.amount) * 100
                result["usage_pct"] = round(pct, 1)
                result["over_budget"] = expense_total > budget.amount
        return result


class CategoryService:
    """카테고리 추가/조회/삭제 — 사용 중 카테고리 보호."""

    def __init__(self, cats: CategoryStore, txs: TransactionRepository):
        self.cats = cats
        self.txs = txs

    def add(self, name: str) -> bool:
        return self.cats.add(name)

    def list_names(self) -> List[str]:
        return self.cats.list_names()

    def remove(self, name: str, replace_with: Optional[str] = None) -> int:
        """카테고리 삭제. 사용 중이라면:
        - replace_with 지정 시 → 해당 카테고리로 일괄 재지정 후 삭제
        - 미지정 시 → AppError 로 차단

        반환: 재지정된 거래 건수 (사용 중이 아니었으면 0).
        """
        if not self.cats.exists(name):
            raise AppError(
                f"존재하지 않는 카테고리입니다: {name}",
                hint="`category list` 로 목록을 확인하세요.",
            )
        in_use = self.txs.category_in_use(name)
        reassigned = 0
        if in_use:
            if not replace_with:
                raise AppError(
                    f"카테고리 '{name}' 는 거래에서 사용 중입니다.",
                    hint="`--replace-with <카테고리>` 로 대체 카테고리를 지정하세요.",
                )
            if not self.cats.exists(replace_with):
                raise AppError(
                    f"대체 카테고리가 등록되어 있지 않습니다: {replace_with}",
                    hint="먼저 `category add` 로 등록하세요.",
                )
            if replace_with == name:
                raise AppError("대체 카테고리는 자기 자신일 수 없습니다.")
            reassigned = self.txs.reassign_category(name, replace_with)
        self.cats.remove(name)
        return reassigned


# ---------- import / export ----------


CSV_FIELDS = ("date", "type", "category", "amount", "memo", "tags")


class ImportExportService:
    """CSV 가져오기/내보내기.

    스키마(고정):
        date(Y), type(Y), category(Y), amount(Y), memo(N), tags(N, 쉼표 구분)
        UTF-8, 헤더 포함
    """

    def __init__(self, txs: TransactionRepository, cats: CategoryStore):
        self.txs = txs
        self.cats = cats

    def export_csv(self, out_path: Path, flt: SearchFilter) -> int:
        """필터 통과 거래를 CSV 로 저장. 작성 건수 반환."""
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS))
            writer.writeheader()
            for tx in self.txs.stream():
                if not flt.matches(tx):
                    continue
                writer.writerow(
                    {
                        "date": tx.date,
                        "type": tx.type,
                        "category": tx.category,
                        "amount": tx.amount,
                        "memo": tx.memo,
                        "tags": ",".join(tx.tags),
                    }
                )
                count += 1
        return count

    def import_csv(self, in_path: Path, atomic: bool = False) -> Tuple[int, int, List[str]]:
        """CSV 거래 일괄 등록.

        두 가지 실패 정책을 지원한다:

        - atomic=False (기본, 부분 성공): 검증 실패한 행은 건너뛰고(skip) 나머지는
          저장한다. 잘못된 몇 줄 때문에 전체 가져오기가 막히지 않는다.
        - atomic=True (전수 롤백): 한 행이라도 검증에 실패하면 아무것도 저장하지
          않고 AppError 를 던진다. "전부 반영" 또는 "전혀 반영 안 됨" 만 존재한다.

        두 정책 모두 먼저 전체 행을 검증(준비 단계)한 뒤에만 파일에 쓴다(커밋
        단계). 카테고리 자동 등록과 ID 발급도 커밋 단계에서 한 번에 수행하므로
        원자 모드에서 커밋 전에 중단되면 카테고리/거래 어느 쪽도 남지 않는다.

        반환: (imported, skipped, errors)
            - imported: 저장된 건수
            - skipped : 검증 실패로 건너뛴 건수 (원자 모드에서는 항상 0 — 실패 시 예외)
            - errors  : 라인별 오류 메시지 리스트 (앞쪽 일부)
        """
        in_path = Path(in_path)
        if not in_path.exists():
            raise FileNotFoundError(str(in_path))

        skipped = 0
        errors: List[str] = []
        prepared: List[Transaction] = []          # 커밋 대상 거래
        new_categories: List[str] = []            # 자동 등록 예정(순서 유지, 중복 제거)

        with open(in_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            missing = [c for c in ("date", "type", "category", "amount") if c not in (reader.fieldnames or [])]
            if missing:
                raise AppError(
                    f"CSV 헤더에 필수 컬럼이 없습니다: {missing}",
                    hint=f"필수 컬럼: {list(CSV_FIELDS)[:4]}",
                )

            # 파일을 한 번만 훑어 다음 ID 시작점을 잡고, 이후는 메모리에서 연속 발급.
            next_num = self.txs.max_id_num()
            known = {Category.normalize(n) for n in self.cats.list_names()}

            for lineno, row in enumerate(reader, start=2):  # 2행부터 데이터
                try:
                    category = Category.normalize(row.get("category") or "")
                    type_ = Transaction.validate_type(row["type"])
                    date = Transaction.validate_date(row["date"])
                    amount = Transaction.validate_amount(row["amount"])
                    memo = (row.get("memo") or "").strip()
                    tags = Transaction.parse_tags(row.get("tags"))
                except (ValidationError, AppError, KeyError) as exc:
                    if atomic:
                        # 전수 롤백: 준비 단계에서 즉시 중단, 파일은 손대지 않는다.
                        raise AppError(
                            f"원자적 가져오기 실패 — line {lineno}: {exc} (반영된 항목 없음)",
                            hint="CSV 를 고쳐 다시 시도하거나, --atomic 없이 부분 가져오기를 사용하세요.",
                        ) from exc
                    skipped += 1
                    if len(errors) < 5:
                        errors.append(f"line {lineno}: {exc}")
                    continue

                next_num += 1
                prepared.append(
                    Transaction(
                        id=f"TX-{next_num:06d}",
                        type=type_,
                        date=date,
                        amount=amount,
                        category=category,
                        memo=memo,
                        tags=tags,
                    )
                )
                if category not in known:
                    known.add(category)
                    new_categories.append(category)

        # 커밋 단계 — 준비된 모든 항목을 한 번에 반영.
        for name in new_categories:
            self.cats.add(name)
        imported = self.txs.append_many(prepared, atomic=atomic)
        return imported, skipped, errors


# ---------- 백업 (보너스) ----------


def backup_data_dir(data_dir: Path) -> Path:
    """data 폴더의 모든 *.jsonl 파일을 타임스탬프 폴더로 복사한다."""
    src = Path(data_dir)
    if not src.exists():
        raise FileNotFoundError(str(src))
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = src.parent / f"backup_{ts}"
    dest.mkdir(parents=True, exist_ok=False)
    for p in src.glob("*.jsonl"):
        dest_file = dest / p.name
        dest_file.write_bytes(p.read_bytes())
    return dest
