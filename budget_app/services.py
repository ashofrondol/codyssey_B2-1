"""서비스 계층 — 유스케이스와 정책.

저장소(파일 I/O)와 CLI(화면) 사이에서 **판단**만 담당한다. 이 파일에는
``open()`` 이 하나도 없다. 파일을 여는 일은 ``repository`` 와 ``csv_io`` 가,
글자를 내는 일은 ``presenter`` 가 한다.

조회는 가능한 한 제너레이터를 그대로 흘려보내 스트리밍 특성을 유지한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from . import config, messages
from .decorators import log_call, measure_time
from .domain import validators
from .domain.models import (
    Budget,
    ImportReport,
    MonthlySummary,
    SearchFilter,
    Transaction,
    TransactionPatch,
)
from .errors import AppError, ValidationError
from .storage import csv_io
from .storage.repository import BudgetStore, CategoryStore, IdAllocator, TransactionRepository


class TransactionService:
    """거래 추가/수정/삭제/조회 — 카테고리 등록 여부 검증 포함."""

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
        self._require_registered_category(category, hint=messages.HINT_CATEGORY_ADD_OR_LIST)
        # 검증·정규화는 Transaction.__post_init__ 이 일괄 수행한다(생성자가 유일한
        # 강제 지점). 여기서는 원값을 그대로 넘긴다.
        tx = Transaction(
            id=self.txs.next_id(),
            type=type_,
            date=date,
            amount=amount,
            category=category,
            memo=memo,
            tags=tags,
        )
        self.txs.append(tx)
        return tx

    @log_call
    def update(self, tx_id: str, patch: TransactionPatch) -> Transaction:
        """부분 수정 — 도메인이 새 객체를 만들고, 저장소는 그것을 쓰기만 한다.

        이전에는 저장소가 ``to_dict → dict.update → from_dict`` 로 변경을 해석했다.
        지금 순서는 조회 → ``with_patch`` (도메인) → ``replace`` (저장)다.
        """
        if patch.category is not None:
            self._require_registered_category(patch.category, hint=messages.HINT_CATEGORY_ADD)

        current = self.txs.get(tx_id)
        if current is None:
            raise AppError(messages.ERR_TX_NOT_FOUND.format(tx_id=tx_id), hint=messages.HINT_LIST_ID)

        updated = current.with_patch(patch)
        self.txs.replace(tx_id, updated)
        return updated

    @log_call
    def delete(self, tx_id: str) -> None:
        if not self.txs.delete(tx_id):
            raise AppError(messages.ERR_TX_NOT_FOUND.format(tx_id=tx_id), hint=messages.HINT_LIST_ID)

    def stream_sorted(self, flt: Optional[SearchFilter] = None) -> Iterator[Transaction]:
        """최신순 정렬된 거래를 yield 한다.

        주의: 정렬을 위해 한 번은 전체를 읽어야 한다(파일이 정렬되어 있지 않으므로).
        그러나 메모리 사용량은 '필터 통과 항목'으로 제한된다.
        """
        items = [tx for tx in self.txs.stream() if flt is None or flt.matches(tx)]
        items.sort(key=lambda t: (t.date, t.id), reverse=True)
        yield from items

    def _require_registered_category(self, name: str, *, hint: str) -> None:
        if not self.cats.exists(name):
            raise AppError(messages.ERR_CATEGORY_NOT_REGISTERED.format(name=name), hint=hint)


class BudgetService:
    """예산 설정/조회 + 월별 요약."""

    def __init__(self, txs: TransactionRepository, budgets: BudgetStore):
        self.txs = txs
        self.budgets = budgets

    def set_budget(self, month: str, amount: int) -> Budget:
        return self.budgets.set(month, amount)

    @measure_time
    def monthly_summary(self, month: str, top_n: int = config.DEFAULT_TOP_N) -> MonthlySummary:
        """월별 요약을 계산해 ``MonthlySummary`` 로 돌려준다.

        "이 달에 속하는가"의 판정을 ``SearchFilter.for_month`` 에 위임한 것이 핵심이다.
        이전에는 요약은 ``date.startswith(month + "-")``, 내보내기는 CLI 가 계산한
        말일 범위를 써서 **같은 개념이 두 알고리즘으로** 구현돼 있었다.
        """
        target = validators.parse_month(month)
        flt = SearchFilter.for_month(target)

        income_total = 0
        expense_total = 0
        per_category: Dict[str, int] = {}
        has_data = False

        for tx in self.txs.stream():
            if not flt.matches(tx):
                continue
            has_data = True
            if tx.type == config.TYPE_INCOME:
                income_total += tx.amount
            else:
                expense_total += tx.amount
                per_category[tx.category] = per_category.get(tx.category, 0) + tx.amount

        top_expense = tuple(
            sorted(per_category.items(), key=lambda kv: kv[1], reverse=True)[: max(0, top_n)]
        )
        return MonthlySummary(
            month=target,
            income=income_total,
            expense=expense_total,
            top_expense=top_expense,
            has_data=has_data,
            budget=self.budgets.get(target),
        )


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

        - ``replace_with`` 지정 시 → 해당 카테고리로 일괄 재지정 후 삭제
        - 미지정 시 → ``AppError`` 로 차단

        반환: 재지정된 거래 건수 (사용 중이 아니었으면 0).
        """
        if not self.cats.exists(name):
            raise AppError(
                messages.ERR_CATEGORY_NOT_EXIST.format(name=name),
                hint=messages.HINT_CATEGORY_LIST,
            )
        reassigned = 0
        if self.txs.category_in_use(name):
            reassigned = self._reassign_before_remove(name, replace_with)
        self.cats.remove(name)
        return reassigned

    def _reassign_before_remove(self, name: str, replace_with: Optional[str]) -> int:
        if not replace_with:
            raise AppError(
                messages.ERR_CATEGORY_IN_USE.format(name=name),
                hint=messages.HINT_REPLACE_WITH,
            )
        if replace_with == name:
            raise AppError(messages.ERR_REPLACE_SELF)
        if not self.cats.exists(replace_with):
            raise AppError(
                messages.ERR_REPLACE_NOT_REGISTERED.format(name=replace_with),
                hint=messages.HINT_ADD_FIRST,
            )
        return self.txs.reassign_category(name, replace_with)


# ============================================================
# 가져오기 / 내보내기
# ============================================================


@dataclass
class _Batch:
    """가져오기 준비 단계의 누적 상태.

    준비(prepare)와 커밋(commit)을 나누는 것이 원자성의 뼈대다. 파일에 손대기
    전에 모든 행의 판정이 끝나 있어야 "전혀 반영 안 됨"이 가능하다.
    """

    transactions: List[Transaction] = field(default_factory=list)
    new_categories: List[str] = field(default_factory=list)
    skipped: int = 0
    duplicated: int = 0
    errors: List[str] = field(default_factory=list)
    duplicate_notes: List[str] = field(default_factory=list)

    def note_error(self, lineno: int, reason: object) -> None:
        self.skipped += 1
        if len(self.errors) < config.MAX_IMPORT_ERRORS:
            self.errors.append(messages.FMT_IMPORT_ERROR.format(lineno=lineno, reason=reason))

    def note_duplicate(self, lineno: int, tx_id: str) -> None:
        self.duplicated += 1
        if len(self.duplicate_notes) < config.MAX_IMPORT_ERRORS:
            self.duplicate_notes.append(
                messages.FMT_IMPORT_DUPLICATE.format(lineno=lineno, tx_id=tx_id)
            )


class ImportExportService:
    """CSV 가져오기/내보내기 정책.

    스키마는 ``csv_io`` 가 안다. 이 클래스가 아는 것은 **정책** 셋이다.

    1. 실패 정책   — 부분 성공(기본) vs 원자적 전수 롤백(``--atomic``)
    2. 중복 정책   — 이미 있는 id 를 만나면 건너뛸까/새로 발급할까/막을까
    3. 부수 효과   — 처음 보는 카테고리는 자동 등록한다
    """

    def __init__(self, txs: TransactionRepository, cats: CategoryStore):
        self.txs = txs
        self.cats = cats

    # ---------- 내보내기 ----------

    def export_csv(self, out_path: Path, flt: SearchFilter, *, include_id: bool = True) -> int:
        """필터를 통과한 거래를 CSV 로 저장하고 작성 건수를 반환한다.

        ``include_id=True`` 가 기본인 이유는 **왕복 안전성**이다. id 가 없으면 내보낸
        파일을 다시 가져올 때 같은 거래가 새 id 로 한 번 더 저장된다.
        """
        rows = (tx for tx in self.txs.stream() if flt.matches(tx))
        return csv_io.write_transactions(out_path, rows, include_id=include_id)

    # ---------- 가져오기 ----------

    def import_csv(
        self,
        in_path: Path,
        *,
        atomic: bool = False,
        on_duplicate: str = config.DEFAULT_ON_DUPLICATE,
    ) -> ImportReport:
        """CSV 거래 일괄 등록.

        준비 단계에서 모든 행을 검증·판정한 뒤에만 커밋 단계로 넘어간다.
        카테고리 자동 등록과 ID 발급도 커밋 단계에서 한 번에 일어나므로, 원자
        모드에서 준비 중 중단되면 카테고리·거래 어느 쪽도 남지 않는다.
        """
        batch = self._prepare(Path(in_path), atomic=atomic, on_duplicate=on_duplicate)
        return self._commit(batch, atomic=atomic)

    def _prepare(self, in_path: Path, *, atomic: bool, on_duplicate: str) -> _Batch:
        batch = _Batch()
        allocator = self.txs.id_allocator()
        known_categories = self.cats.name_set()

        for lineno, row in csv_io.read_rows(in_path):
            try:
                parsed = csv_io.parse_row(lineno, row)
            except (ValidationError, KeyError) as exc:
                if atomic:
                    # 전수 롤백: 준비 단계에서 즉시 중단, 파일은 손대지 않는다.
                    raise AppError(
                        messages.ERR_ATOMIC_IMPORT_FAILED.format(lineno=lineno, reason=exc),
                        hint=messages.HINT_ATOMIC_IMPORT,
                    ) from exc
                batch.note_error(lineno, exc)
                continue

            tx_id = self._resolve_id(parsed.tx_id, lineno, allocator, on_duplicate, batch)
            if tx_id is None:
                continue  # 중복 — 건너뛰기 정책

            batch.transactions.append(parsed.to_transaction(tx_id))
            if parsed.category not in known_categories:
                known_categories.add(parsed.category)
                batch.new_categories.append(parsed.category)

        return batch

    def _resolve_id(
        self,
        csv_id: Optional[str],
        lineno: int,
        allocator: IdAllocator,
        on_duplicate: str,
        batch: _Batch,
    ) -> Optional[str]:
        """이 행이 쓸 id 를 정한다. ``None`` 이면 "이 행은 저장하지 않는다".

        ``allocator`` 가 이미 파일에 있는 id 와 **이번 CSV 에서 앞서 소비한 id** 를
        모두 알고 있으므로, 파일 간 중복과 파일 내 중복이 같은 규칙으로 걸린다.
        """
        if csv_id is None:
            return allocator.next()  # id 컬럼이 없거나 비어 있음 → 새로 발급
        if not allocator.is_taken(csv_id):
            allocator.reserve(csv_id)  # 원본 id 복원 — 왕복이 무손실이 된다
            return csv_id

        if on_duplicate == config.ON_DUPLICATE_NEW_ID:
            return allocator.next()
        if on_duplicate == config.ON_DUPLICATE_ERROR:
            raise AppError(
                messages.ERR_DUPLICATE_ID.format(tx_id=csv_id),
                hint=messages.HINT_DUPLICATE_ID,
            )
        batch.note_duplicate(lineno, csv_id)
        return None

    def _commit(self, batch: _Batch, *, atomic: bool) -> ImportReport:
        self.cats.add_many(batch.new_categories)
        imported = self.txs.append_many(batch.transactions, atomic=atomic)
        return ImportReport(
            imported=imported,
            skipped=batch.skipped,
            duplicated=batch.duplicated,
            errors=tuple(batch.errors),
            duplicate_notes=tuple(batch.duplicate_notes),
        )
