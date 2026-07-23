"""파일 입출력 계층 — JSONL 기반 영구 저장소.

설계 메모:
- 모든 읽기는 yield 기반 제너레이터로 한 줄씩 스트리밍 처리한다.
  → 대용량 파일도 메모리에 모두 올리지 않는다.
- update/delete 처럼 파일 전체를 다시 써야 하는 작업은
  '임시 파일 + os.replace' 의 원자적 교체 패턴을 사용한다.
  → 쓰는 도중 프로세스가 죽어도 원본 파일이 깨지지 않는다.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from .models import Budget, Category, Transaction, ValidationError

logger = logging.getLogger("budget_app.repository")


DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "etc")


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _atomic_write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    """임시 파일에 모두 쓴 뒤 os.replace 로 원자적 교체."""
    _ensure_parent(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


class TransactionRepository:
    """transactions.jsonl 의 CRUD + 스트리밍 조회를 담당한다."""

    FILE_NAME = "transactions.jsonl"
    ID_PATTERN = re.compile(r"^TX-(\d+)$")

    def __init__(self, data_dir: Path):
        self.path = Path(data_dir) / self.FILE_NAME
        _ensure_parent(self.path)
        if not self.path.exists():
            self.path.touch()

    # ---------- 스트리밍 조회 ----------

    def stream(self) -> Iterator[Transaction]:
        """파일을 한 줄씩 읽으며 Transaction 객체로 yield 한다.

        잘못된 줄은 건너뛰되, 조용히 버리지 않고 경고 로그로 남긴다
        (데이터 유실을 사용자가 인지할 수 있도록). 빈 줄은 정상이므로 무시한다.
        """
        with open(self.path, "r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    yield Transaction.from_dict(data)
                except (json.JSONDecodeError, ValidationError, KeyError) as exc:
                    logger.warning("%s:%d 손상된 줄을 건너뜁니다: %s", self.path.name, lineno, exc)
                    continue

    # ---------- ID 발급 ----------

    def max_id_num(self) -> int:
        """현재 파일에서 발급된 최대 거래 번호를 반환한다(없으면 0).

        배치 삽입(import) 시 매 행마다 파일을 다시 훑지 않고, 이 값을 한 번만
        읽어 이후 ID를 메모리에서 연속 발급하기 위한 진입점이다.
        """
        max_n = 0
        for tx in self.stream():
            m = self.ID_PATTERN.match(tx.id)
            if m:
                n = int(m.group(1))
                if n > max_n:
                    max_n = n
        return max_n

    def next_id(self) -> str:
        """기존 최대 번호 + 1 로 'TX-000001' 형식 ID 생성."""
        return f"TX-{self.max_id_num() + 1:06d}"

    # ---------- 쓰기 ----------

    def append(self, tx: Transaction) -> None:
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n")

    def append_many(self, txs: Iterable[Transaction], *, atomic: bool = False) -> int:
        """여러 거래를 한 번에 추가하고 추가된 건수를 반환한다.

        - atomic=False: 일반 append(파일 끝에 이어 쓰기). 중간에 프로세스가 죽으면
          일부만 기록될 수 있다(부분 성공 정책과 짝을 이룸).
        - atomic=True: 기존 내용 + 신규 전부를 임시 파일에 쓴 뒤 os.replace 로
          교체한다. 원본은 교체가 끝나기 전까지 그대로이므로 '전부 반영' 또는
          '전혀 반영 안 됨' 만 존재한다(전수 롤백 = 원자적 가져오기).
        """
        txs = list(txs)
        if atomic:
            def _rows() -> Iterator[dict]:
                for existing in self.stream():
                    yield existing.to_dict()
                for tx in txs:
                    yield tx.to_dict()

            _atomic_write_jsonl(self.path, _rows())
        else:
            with open(self.path, "a", encoding="utf-8", newline="\n") as f:
                for tx in txs:
                    f.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n")
        return len(txs)

    def delete(self, tx_id: str) -> bool:
        """삭제 성공 시 True, 대상 없으면 False."""
        found = False
        rows: List[dict] = []
        for tx in self.stream():
            if tx.id == tx_id:
                found = True
                continue
            rows.append(tx.to_dict())
        if found:
            _atomic_write_jsonl(self.path, rows)
        return found

    def update(self, tx_id: str, changes: Dict[str, object]) -> Optional[Transaction]:
        """변경 적용 후 갱신된 Transaction 반환. 대상 없으면 None."""
        updated: Optional[Transaction] = None
        rows: List[dict] = []
        for tx in self.stream():
            if tx.id == tx_id:
                data = tx.to_dict()
                data.update(changes)
                # from_dict 가 검증을 다시 수행
                new_tx = Transaction.from_dict(data)
                updated = new_tx
                rows.append(new_tx.to_dict())
            else:
                rows.append(tx.to_dict())
        if updated is not None:
            _atomic_write_jsonl(self.path, rows)
        return updated

    def category_in_use(self, name: str) -> bool:
        for tx in self.stream():
            if tx.category == name:
                return True
        return False

    def reassign_category(self, old: str, new: str) -> int:
        """old → new 카테고리 일괄 재지정. 변경된 건수 반환."""
        changed = 0
        rows: List[dict] = []
        for tx in self.stream():
            d = tx.to_dict()
            if d["category"] == old:
                d["category"] = new
                changed += 1
            rows.append(d)
        if changed:
            _atomic_write_jsonl(self.path, rows)
        return changed


class CategoryStore:
    """categories.jsonl — 카테고리 이름 집합 관리."""

    FILE_NAME = "categories.jsonl"

    def __init__(self, data_dir: Path, seed_defaults: bool = True):
        self.path = Path(data_dir) / self.FILE_NAME
        _ensure_parent(self.path)
        created = not self.path.exists()
        if created:
            self.path.touch()
        # 빈 파일이고 seed 가 켜져 있으면 기본 카테고리 자동 생성
        if seed_defaults and self._is_empty():
            for name in DEFAULT_CATEGORIES:
                self._append(Category(name=name))

    def _is_empty(self) -> bool:
        return self.path.stat().st_size == 0

    def _append(self, cat: Category) -> None:
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(cat.to_dict(), ensure_ascii=False) + "\n")

    def stream(self) -> Iterator[Category]:
        with open(self.path, "r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    yield Category.from_dict(json.loads(line))
                except (json.JSONDecodeError, ValidationError, KeyError) as exc:
                    logger.warning("%s:%d 손상된 줄을 건너뜁니다: %s", self.path.name, lineno, exc)
                    continue

    def list_names(self) -> List[str]:
        return [c.name for c in self.stream()]

    def exists(self, name: str) -> bool:
        target = Category.normalize(name)
        return any(c.name == target for c in self.stream())

    def add(self, name: str) -> bool:
        """추가 성공 시 True, 이미 존재하면 False."""
        cat = Category(name=Category.normalize(name))
        if self.exists(cat.name):
            return False
        self._append(cat)
        return True

    def remove(self, name: str) -> bool:
        target = Category.normalize(name)
        rows: List[dict] = []
        found = False
        for c in self.stream():
            if c.name == target:
                found = True
                continue
            rows.append(c.to_dict())
        if found:
            _atomic_write_jsonl(self.path, rows)
        return found


class BudgetStore:
    """budgets.jsonl — 월별 예산 저장. 같은 월은 덮어쓴다."""

    FILE_NAME = "budgets.jsonl"

    def __init__(self, data_dir: Path):
        self.path = Path(data_dir) / self.FILE_NAME
        _ensure_parent(self.path)
        if not self.path.exists():
            self.path.touch()

    def stream(self) -> Iterator[Budget]:
        with open(self.path, "r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    yield Budget.from_dict(json.loads(line))
                except (json.JSONDecodeError, ValidationError, KeyError) as exc:
                    logger.warning("%s:%d 손상된 줄을 건너뜁니다: %s", self.path.name, lineno, exc)
                    continue

    def get(self, month: str) -> Optional[Budget]:
        target = Budget.validate_month(month)
        result: Optional[Budget] = None
        for b in self.stream():
            if b.month == target:
                result = b  # 같은 월의 마지막 값을 유효값으로 본다
        return result

    def set(self, month: str, amount: int) -> Budget:
        # 검증은 Budget.__post_init__ 이 수행한다(Transaction 참조 제거).
        b = Budget(month=month, amount=amount)
        # month 별 단일 값 유지 — 기존 항목은 제거 후 새 값 추가
        rows: List[dict] = []
        for existing in self.stream():
            if existing.month != b.month:
                rows.append(existing.to_dict())
        rows.append(b.to_dict())
        _atomic_write_jsonl(self.path, rows)
        return b
