"""Unit of Work — 여러 파일에 걸친 변경을 하나의 커밋으로 묶는다.

## 이 패턴이 푸는 문제

가져오기 커밋 단계는 파일 **둘**을 바꾼다::

    self.cats.add_many(batch.new_categories)      # 쓰기 1 — categories.jsonl
    self.txs.append_many(batch.transactions)      # 쓰기 2 — transactions.jsonl

두 줄 사이에 프로세스가 죽으면 **카테고리만 늘어난 고아 상태**가 남는다.
``--atomic`` 이 "전부 반영 또는 전혀 반영 안 됨"을 약속하는데, 그 약속이 파일 하나
안에서만 지켜지고 있었던 것이다.

## 어떻게 좁히나

``os.replace`` 는 **이름 교체**라 매우 빠르다. 그래서 순서를 이렇게 바꾼다.

    [준비] 두 파일의 최종 내용을 각각 .tmp 로 작성 + fsync   ← 느린 부분
    [커밋] os.replace 두 번을 연달아 실행                     ← 빠른 부분

취약 구간이 "파일 쓰기 2회 사이"에서 "rename 2회 사이"로 줄어든다. 준비 도중
죽으면 원본 둘 다 무사하고 ``.tmp`` 찌꺼기만 남는다.

## 정직하게: 완전한 원자성은 아니다

rename 두 번 사이에 전원이 끊기면 여전히 한쪽만 반영될 수 있다. 진짜 다중 파일
원자성은 저널이나 SQLite 가 필요하다. 이 패턴이 하는 일은 **창을 밀리초 단위로
줄이는 것**이지 없애는 것이 아니다 — 그 경계를 아는 것이 중요하다.

## 왜 부분 성공 모드에는 쓰지 않나

``--atomic`` 없는 가져오기는 파일 끝에 이어 쓰기(append)라 O(1)이다. UoW 를 쓰려면
전체 재작성이 필요해 10만 건 파일에 10건을 넣는 데 10만 줄을 다시 써야 한다.
**원자성을 약속한 모드에만** 비용을 지불하는 것이 맞다.
"""

from __future__ import annotations

import logging
from pathlib import Path
from types import TracebackType
from typing import List, Optional, Tuple, Type

from . import config
from .jsonl import commit_staged, stage_lines

logger = logging.getLogger(config.LOGGER_NAME)


class UnitOfWork:
    """여러 저장소의 재작성을 모아 두었다가 한꺼번에 커밋한다.

    사용법::

        with UnitOfWork() as uow:
            uow.stage(cats, cats.plan_rewrite(lambda c: c, extra=new_cats))
            uow.stage(txs, txs.plan_rewrite(lambda t: t, extra=new_txs))
        # 블록을 정상적으로 빠져나가면 커밋, 예외가 나면 롤백

    ``with`` 를 쓰는 이유: 예외로 빠져나가는 경로에서도 ``.tmp`` 를 반드시 치우기
    위해서다(``finally`` 없이 보장된다).
    """

    def __init__(self) -> None:
        self._staged: List[Tuple[Path, Path]] = []
        self._committed = False

    # ---------- 준비 ----------

    def stage(self, store, lines: List[str]) -> None:
        """한 저장소의 최종 내용을 ``.tmp`` 로 준비한다 — 아직 반영하지 않는다."""
        tmp = stage_lines(store.path, lines)
        self._staged.append((tmp, store.path))

    # ---------- 마무리 ----------

    def commit(self) -> None:
        """준비된 것을 전부 반영한다 — rename 만 연달아 실행."""
        for tmp, target in self._staged:
            commit_staged(tmp, target)
        self._staged.clear()
        self._committed = True

    def rollback(self) -> None:
        """준비한 ``.tmp`` 를 지운다 — 원본은 손대지 않았으므로 이것으로 끝이다."""
        for tmp, _ in self._staged:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:  # 지우지 못해도 원본은 무사하다. 다음 실행이 덮어쓴다.
                logger.debug("임시 파일 정리 실패: %s", tmp)
        self._staged.clear()

    # ---------- 컨텍스트 매니저 ----------

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
