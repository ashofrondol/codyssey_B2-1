"""CSV 가져오기/내보내기 **정책**.

스키마는 ``storage.csv_io`` 가 안다. 이 모듈이 아는 것은 정책 셋이다.

1. 실패 정책   — 부분 성공(기본) vs 원자적 전수 롤백(``--atomic``)
2. 중복 정책   — 이미 있는 id 를 만나면 건너뛸까/새로 발급할까/막을까
3. 부수 효과   — 처음 보는 카테고리는 자동 등록한다

두 정책 축은 **독립**이다. ``--atomic`` 은 데이터가 *잘못된* 줄을, ``--on-duplicate``
는 이미 *저장된* 거래를 다룬다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..domain.entities import Category, Transaction
from ..domain.queries import SearchFilter
from ..domain.results import DuplicateRow, ImportReport, RejectedRow
from ..domain.tx_id import TransactionId
from ..errors import AppError, ValidationError
from ..storage import csv_io
from ..storage.ids import IdAllocator
from ..storage.repositories import CategoryStore, TransactionRepository
from ..storage.unit_of_work import UnitOfWork
from . import config, messages


@dataclass
class _Batch:
    """가져오기 준비 단계의 누적 상태.

    준비(prepare)와 커밋(commit)을 나누는 것이 원자성의 뼈대다. 파일에 손대기
    전에 모든 행의 판정이 끝나 있어야 "전혀 반영 안 됨"이 가능하다.
    """

    transactions: list[Transaction] = field(default_factory=list)
    new_categories: list[str] = field(default_factory=list)
    skipped: int = 0
    duplicated: int = 0
    errors: list[RejectedRow] = field(default_factory=list)
    duplicates: list[DuplicateRow] = field(default_factory=list)

    def note_error(self, lineno: int, reason: object) -> None:
        """세는 것은 전부, 사유를 남기는 것은 앞의 몇 건만.

        수천 줄짜리 CSV 가 통째로 잘못됐을 때 사유를 전부 모으면 메모리와 화면이
        같이 터진다. 숫자(``skipped``)는 정확하고, 목록은 표본이다.
        """
        self.skipped += 1
        if len(self.errors) < config.MAX_IMPORT_ERRORS:
            self.errors.append(RejectedRow(lineno=lineno, reason=str(reason)))

    def note_duplicate(self, lineno: int, tx_id: TransactionId) -> None:
        self.duplicated += 1
        if len(self.duplicates) < config.MAX_IMPORT_ERRORS:
            self.duplicates.append(DuplicateRow(lineno=lineno, tx_id=tx_id.value))


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
                parsed = csv_io.parse_row(row)
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
        csv_id: TransactionId | None,
        lineno: int,
        allocator: IdAllocator,
        on_duplicate: str,
        batch: _Batch,
    ) -> TransactionId | None:
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
        if on_duplicate == config.ON_DUPLICATE_SKIP:
            batch.note_duplicate(lineno, csv_id)
            return None
        # argparse choices 가 이미 값을 제한하지만, 서비스가 CLI 의 검증에 기대지
        # 않도록 방어한다(다른 진입점이 생겨도 정책 누락이 조용히 통과하지 않는다).
        raise AppError(messages.ERR_UNKNOWN_DUPLICATE_POLICY.format(policy=on_duplicate))

    def _commit(self, batch: _Batch, *, atomic: bool) -> ImportReport:
        """준비된 것을 파일에 반영한다 — 여기서 처음 파일이 바뀐다."""
        imported = (
            self._commit_atomic(batch) if atomic else self._commit_appending(batch)
        )
        return ImportReport(
            imported=imported,
            skipped=batch.skipped,
            duplicated=batch.duplicated,
            errors=tuple(batch.errors),
            duplicates=tuple(batch.duplicates),
        )

    def _commit_appending(self, batch: _Batch) -> int:
        """부분 성공 모드 — 파일 끝에 이어 쓴다(O(1)).

        두 파일을 따로 쓰므로 그 사이에 죽으면 카테고리만 남을 수 있다. 이 모드는
        애초에 "가능한 만큼 최대한 넣는다"는 정책이라 그 위험을 감수한다.
        """
        self.cats.add_many(batch.new_categories)
        return self.txs.append_many(batch.transactions)

    def _commit_atomic(self, batch: _Batch) -> int:
        """원자 모드 — 두 파일을 **한 단위로** 커밋한다.

        ``--atomic`` 이 "전부 반영 또는 전혀 반영 안 됨"을 약속하는데, 이전에는 그
        약속이 거래 파일 안에서만 지켜졌다. 카테고리를 먼저 쓰고 거래를 나중에 써서,
        그 사이에 죽으면 **쓰이지 않는 카테고리만 남았다**.

        지금은 둘의 최종 내용을 각각 ``.tmp`` 로 준비한 뒤 ``os.replace`` 두 번을
        연달아 실행한다. 취약 구간이 "파일 쓰기 2회 사이"에서 "rename 2회 사이"로
        줄어든다(완전한 제거는 저널이나 SQLite 가 필요하다).
        """
        fresh_categories = [Category(name=n) for n in batch.new_categories]
        # 파일을 저장소 밖(UoW)에서 쓰므로 id 워터마크는 여기서 명시적으로 알린다.
        self.txs.remember_ids(batch.transactions)
        with UnitOfWork() as uow:
            if fresh_categories:
                uow.stage(self.cats, extra=fresh_categories)
            uow.stage(self.txs, extra=batch.transactions)
        return len(batch.transactions)
