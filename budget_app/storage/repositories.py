"""엔티티별 저장소 — JSONL 공통 처리는 ``jsonl.JsonlStore`` 가 맡는다.

각 클래스는 **그 엔티티 고유의 규칙**만 갖는다.

- ``TransactionRepository`` : ID 발급, 카테고리 재지정
- ``CategoryStore``         : 이름 중복 검사, 기본값 시딩
- ``BudgetStore``           : 같은 달은 덮어쓰기

저장소는 **도메인 판단을 하지 않는다.** 완성된 객체를 받아 쓰고 저장된 객체를
돌려줄 뿐이며, "무엇으로 바꿀지"는 서비스와 도메인이 정한다.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ..domain import tx_id as tx_id_module
from ..domain import validators
from ..domain.entities import Budget, Category, Transaction, TransactionPatch
from ..domain.tx_id import TransactionId
from . import config
from .ids import IdAllocator, IdWatermark
from .jsonl import JsonlStore, RawLine


class TransactionRepository(JsonlStore[Transaction]):
    """transactions.jsonl 의 CRUD + 스트리밍 조회."""

    entity_cls = Transaction
    FILE_NAME = config.TX_FILE_NAME

    def __init__(self, data_dir: Path) -> None:
        super().__init__(Path(data_dir) / self.FILE_NAME)
        self._watermark = IdWatermark(Path(data_dir) / config.ID_COUNTER_FILE_NAME)

    # ---------- ID ----------

    @staticmethod
    def _scan_id(raw: RawLine) -> TransactionId | None:
        """한 줄에서 거래 id 를 최대한 건져낸다.

        검증에 실패한 줄에도 id 는 들어 있을 수 있고, 그 번호는 **이미 쓰인 번호**다.
        놓치면 재발급으로 중복 id 가 생긴다. dict 까지 해석된 줄은 키에서, JSON 조차
        아닌 줄은 원문 정규식으로 찾는다(``TransactionId.scan``).
        """
        if raw.data is not None:
            candidate = raw.data.get("id")
            if isinstance(candidate, str) and tx_id_module.is_valid(candidate):
                return TransactionId(candidate.strip())
        return TransactionId.scan(raw.text)

    def id_state(self) -> tuple[int, set[TransactionId]]:
        """(최대 번호, 사용 중인 id 집합) — 파일을 한 번만 훑는다."""
        max_n = 0
        taken: set[TransactionId] = set()
        for raw in self.iter_raw():
            found = self._scan_id(raw)
            if found is None:
                continue
            taken.add(found)
            max_n = max(max_n, found.number)
        return max_n, taken

    def id_allocator(self) -> IdAllocator:
        """이 파일 상태에 맞춘 발급기를 만든다. 배치 작업은 이걸 한 번만 받아 쓴다.

        시작점이 **두 값의 최대**인 것이 핵심이다.

        - 파일 스캔 최대값 — 지금 무엇이 있는가(삭제하면 줄어든다)
        - 워터마크        — 무엇을 발급한 적이 있는가(줄어들지 않는다)

        워터마크만 믿지 않는 이유: 파일이 손으로 편집되거나 다른 폴더에서 복사돼
        올 수 있다. 스캔만 믿지 않는 이유는 ``IdWatermark`` 문서에 있다.
        """
        max_n, taken = self.id_state()
        return IdAllocator(start=max(max_n, self._watermark.read()), taken=taken)

    def next_id(self) -> TransactionId:
        """단건 추가용 — 발급기를 한 번 쓰고 버린다."""
        return self.id_allocator().next()

    def remember_ids(self, txs: Iterable[Transaction]) -> None:
        """이 거래들의 번호를 워터마크에 반영한다.

        저장소 밖에서 파일을 쓰는 경로(``UnitOfWork`` 커밋)를 위한 공개 지점이다.
        ``append``/``append_many`` 는 스스로 부르므로 호출자가 신경 쓸 필요가 없다.
        """
        numbers = [tx.id.number for tx in txs]
        if numbers:
            self._watermark.remember(max(numbers))

    @staticmethod
    def _as_id(value: object) -> TransactionId | None:
        """조회 인자를 값 객체로 정규화한다 — 형식이 아니면 ``None``.

        예외를 던지지 않는 이유: "형식이 틀린 id 로 조회"는 **찾지 못한 것**과 같다.
        여기서 ``ValidationError`` 를 던지면 ``delete --id abc`` 의 종료 코드가
        4(대상 없음)에서 2(값 오류)로 바뀌어 기존 계약이 깨진다.
        """
        return TransactionId(str(value).strip()) if tx_id_module.is_valid(value) else None

    def exists(self, tx_id: object) -> bool:
        target = self._as_id(tx_id)
        if target is None:
            return False
        _, taken = self.id_state()
        return target in taken

    # ---------- 조회 ----------

    def get(self, tx_id: object) -> Transaction | None:
        target = self._as_id(tx_id)
        if target is None:
            return None
        for tx in self.stream():
            if tx.id == target:
                return tx
        return None

    def category_in_use(self, name: str) -> bool:
        """저장된 카테고리는 정규형이므로 **묻는 쪽도 정규화**해야 판정이 맞는다."""
        target = validators.parse_category(name)
        return any(tx.category == target for tx in self.stream())

    # ---------- 쓰기 ----------

    def append(self, tx: Transaction) -> None:
        """한 건을 이어 쓰고 워터마크를 갱신한다.

        워터마크를 **쓰기 전에** 올린다. 그래야 "발급된 번호는 어느 순간에도
        기준선 아래로 내려가지 않는다"가 항상 성립한다. 쓰기가 실패하면 번호가
        하나 건너뛰지만, 빈 번호는 아무 문제도 일으키지 않는다.
        """
        self._watermark.remember(tx.id.number)
        super().append(tx)

    def append_many(self, txs: Iterable[Transaction]) -> int:
        """여러 거래를 파일 끝에 이어 쓰고 추가된 건수를 반환한다 — O(1) 경로.

        ``atomic=True`` 분기가 있었지만 ``UnitOfWork`` 도입 후 **원자적 커밋 수단이
        둘**이 됐고, 이쪽은 아무도 쓰지 않게 됐다. 같은 일을 하는 길이 둘이면 어느
        쪽이 정답인지 매번 판단해야 하고 한쪽만 고치는 사고가 난다.
        여러 파일을 한 단위로 묶는 것은 ``UnitOfWork`` 의 일이다.
        """
        txs = list(txs)
        self.remember_ids(txs)
        return self.append_all(txs)

    def delete(self, tx_id: object) -> bool:
        """삭제 성공 시 True, 대상 없으면 False — **파일을 한 번만 읽는다**.

        이전에는 ``exists()`` 로 확인한 뒤 재작성하며 또 훑었다. 두 스캔의 판정
        기준이 서로 달랐던 것이 더 문제였다 — ``exists()`` 는 손상 줄에서 건져낸
        id 까지 "있다"고 했지만, 재작성은 해석된 엔티티만 훑으므로 그 줄은 지울 수
        없었다. 지금은 훑으면서 만나는 것이 곧 판정이라 어긋날 수가 없다.
        """
        target = self._as_id(tx_id)
        if target is None:
            return False
        found = False

        def _drop(tx: Transaction) -> Transaction | None:
            nonlocal found
            if tx.id == target:
                found = True
                return None
            return tx

        self.rewrite(_drop)
        return found

    def replace(self, tx_id: object, new_tx: Transaction) -> bool:
        """``tx_id`` 인 거래를 완성된 ``new_tx`` 로 통째 교체한다 — 한 번만 읽는다.

        저장소는 "무엇이 어떻게 바뀌는지" 모른다. 부분 변경 해석은 서비스가
        ``Transaction.with_patch`` 로 끝내고 완성품만 여기로 온다.
        """
        target = self._as_id(tx_id)
        if target is None:
            return False
        found = False

        def _swap(tx: Transaction) -> Transaction:
            nonlocal found
            if tx.id == target:
                found = True
                return new_tx
            return tx

        self.rewrite(_swap)
        return found

    def reassign_category(self, old: str, new: str) -> int:
        """old → new 카테고리 일괄 재지정. 변경된 건수 반환.

        두 이름 모두 정규화한다. ``old`` 는 비교 대상이라(저장된 값은 정규형),
        ``new`` 는 "바뀐 게 없는데 바뀌었다고 세는" 일을 막기 위해서다.
        """
        source = validators.parse_category(old)
        destination = validators.parse_category(new)
        changed = 0

        patch = TransactionPatch(category=destination)

        def _reassign(tx: Transaction) -> Transaction:
            nonlocal changed
            if tx.category != source:
                return tx
            changed += 1
            return tx.with_patch(patch)

        self.rewrite(_reassign)
        return changed


class CategoryStore(JsonlStore[Category]):
    """categories.jsonl — 카테고리 이름 집합 관리."""

    entity_cls = Category
    FILE_NAME = config.CATEGORY_FILE_NAME

    def __init__(self, data_dir: Path) -> None:
        super().__init__(Path(data_dir) / self.FILE_NAME)

    def seed_defaults(self) -> int:
        """비어 있을 때만 기본 카테고리를 심는다. 심은 개수를 반환.

        "파일을 만드는 일"(``ensure_ready``)과 "초기 데이터를 넣는 일"은 다른 작업이라
        메서드를 나눴다. 둘 다 생성자가 아니라 명시적 호출인 이유는 부트스트랩이
        *한 번* 일어나야 하는 일이지 객체를 만들 때마다 일어날 일이 아니기 때문이다.
        """
        if not self.is_empty:
            return 0
        return self.append_all(Category(name=name) for name in config.DEFAULT_CATEGORIES)

    def list_names(self) -> list[str]:
        return [c.name for c in self.stream()]

    def name_set(self) -> set[str]:
        """존재 확인을 반복할 때 쓰는 스냅숏 — 매번 파일을 훑지 않기 위해."""
        return {c.name for c in self.stream()}

    def exists(self, name: str) -> bool:
        target = validators.parse_category(name)
        return any(c.name == target for c in self.stream())

    def add(self, name: str) -> bool:
        """추가 성공 시 True, 이미 존재하면 False."""
        cat = Category(name=name)
        if self.exists(cat.name):
            return False
        self.append(cat)
        return True

    def add_many(self, names: Iterable[str]) -> int:
        """여러 이름을 한 번에 추가한다 — 존재 확인을 위해 파일을 한 번만 훑는다."""
        known = self.name_set()
        fresh: list[Category] = []
        for name in names:
            cat = Category(name=name)
            if cat.name in known:
                continue
            known.add(cat.name)
            fresh.append(cat)
        return self.append_all(fresh)

    def remove(self, name: str) -> bool:
        target = validators.parse_category(name)
        found = False

        def _drop(cat: Category) -> Category | None:
            nonlocal found
            if cat.name == target:
                found = True
                return None
            return cat

        self.rewrite(_drop)
        return found


class BudgetStore(JsonlStore[Budget]):
    """budgets.jsonl — 월별 예산 저장. 같은 월은 덮어쓴다."""

    entity_cls = Budget
    FILE_NAME = config.BUDGET_FILE_NAME

    def __init__(self, data_dir: Path) -> None:
        super().__init__(Path(data_dir) / self.FILE_NAME)

    def get(self, month: str) -> Budget | None:
        target = validators.parse_month(month)
        result: Budget | None = None
        for b in self.stream():
            if b.month == target:
                result = b  # 같은 월의 마지막 값을 유효값으로 본다
        return result

    def set(self, month: str, amount: int) -> Budget:
        budget = Budget(month=month, amount=amount)

        # month 별 단일 값 유지 — 같은 달의 기존 항목은 지우고 새 값을 끝에 붙인다.
        def _drop_same_month(existing: Budget) -> Budget | None:
            return None if existing.month == budget.month else existing

        self.rewrite(_drop_same_month, extra=[budget])
        return budget
