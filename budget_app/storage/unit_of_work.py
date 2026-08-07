"""Unit of Work — 여러 파일에 걸친 변경을 하나의 커밋으로 묶는다.

## 이름에 대한 정직한 단서

Fowler 가 말한 Unit of Work 는 **변경을 추적**한다. 객체를 등록해 두면 어느 것이
새로 생겼고(new) 어느 것이 바뀌었고(dirty) 어느 것이 지워졌는지(removed)를
스스로 알고, 커밋 시점에 필요한 최소한의 쓰기를 순서대로 수행한다.

이 클래스는 그것을 하지 않는다. 무엇이 바뀌었는지 **호출자가 이미 알고** 있고,
여기서 하는 일은 "여러 파일의 최종 내용을 미리 준비해 두었다가 rename 만 몰아서
실행"하는 것뿐이다. 정확한 이름은 *staged commit* 또는 *배치 커밋* 이다.

그래도 이 이름을 쓰는 이유는 **해결하는 문제가 같기 때문**이다 — 여러 저장소에
걸친 변경이 중간 상태로 남지 않게 하는 것. 다만 "UoW 를 썼습니다"라고만 말하면
변경 추적까지 있는 것처럼 들리므로, 그 경계를 여기 적어 둔다.

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
from collections.abc import Callable, Iterable
from pathlib import Path
from types import TracebackType
from typing import Any

from . import config, messages
from .jsonl import RewritePlan, commit_staged, stage_lines

logger = logging.getLogger(config.LOGGER_NAME)


def _keep(entity: Any) -> Any:
    """"기존 항목은 그대로" — ``plan_rewrite`` 의 항등 변환.

    가져오기처럼 **추가만 하는** 커밋이 기본이라 이것을 기본값으로 둔다.
    """
    return entity


class UnitOfWork:
    """여러 저장소의 재작성을 모아 두었다가 한꺼번에 커밋한다.

    사용법::

        with UnitOfWork() as uow:
            uow.stage(cats, extra=new_cats)
            uow.stage(txs, extra=new_txs)
        # 블록을 정상적으로 빠져나가면 커밋, 예외가 나면 롤백

    ``with`` 를 쓰는 이유: 예외로 빠져나가는 경로에서도 ``.tmp`` 를 반드시 치우기
    위해서다(``finally`` 없이 보장된다).
    """

    def __init__(self) -> None:
        self._staged: list[tuple[Path, Path]] = []

    # ---------- 준비 ----------

    def stage(
        self,
        store,
        transform: Callable[[Any], Any | None] = _keep,
        *,
        extra: Iterable[Any] = (),
    ) -> bool:
        """한 저장소의 최종 내용을 ``.tmp`` 로 준비한다 — 아직 반영하지 않는다.

        준비할 것이 있었으면 ``True``.

        ## 왜 줄 목록이 아니라 변환 함수를 받나

        이전 시그니처는 ``stage(store, lines)`` 였고, 호출자가 이렇게 썼다::

            uow.stage(self.cats, self.cats.plan_rewrite(_keep, extra=new_cats))

        서비스가 **저장소의 줄 목록을 손에 들고 나르는** 모양이다. 서비스는 JSONL
        한 줄이 어떻게 생겼는지 알 이유가 없는데, 그 문자열 리스트가 서비스 코드를
        통과하면서 계층 경계가 새고 있었다. 무엇보다 ``plan_rewrite`` 를 두 번
        부르거나 다른 저장소의 계획을 넘기는 실수를 타입이 막지 못한다.

        지금은 "무엇을 반영할지"만 넘기고 계획은 UoW 가 저장소에게 직접 시킨다.
        """
        plan: RewritePlan = store.plan_rewrite(transform, extra=extra)
        if not plan.changed:
            return False  # 바꿀 것이 없으면 임시 파일도 만들지 않는다
        tmp = stage_lines(store.path, plan.lines)
        self._staged.append((tmp, store.path))
        return True

    # ---------- 마무리 ----------

    def commit(self) -> None:
        """준비된 것을 전부 반영한다 — rename 만 연달아 실행.

        ## 두 번째 rename 이 실패하면

        위 문단이 말한 "rename 두 번 사이"의 창은 전원 차단만 뜻하지 않는다.
        Windows 에서는 다른 프로세스가 파일을 열고 있으면 ``os.replace`` 가
        ``PermissionError`` 로 **그냥 실패**한다. 즉 흔한 실패다.

        그 상황에서 할 수 있는 일과 없는 일을 구분한다.

        - **할 수 없는 것**: 이미 반영된 첫 파일을 되돌리는 것. 원본을 덮어썼으므로
          되돌릴 원본이 없다. 진짜 되돌리려면 저널이 필요하고, 그건 이 패턴의 범위 밖이다.
        - **해야 하는 것**: (1) 어디까지 반영됐는지 **로그로 남기고**, (2) 남은
          ``.tmp`` 를 치우고, (3) 예외를 **그대로 올려** 호출자가 성공으로 착각하지
          않게 하는 것.

        이전에는 셋 다 하지 않았다. 예외가 ``__exit__`` 밖으로 나가면서 ``.tmp`` 가
        남고, 사용자는 "어느 파일이 반영됐는지" 알 방법이 없었다.
        """
        done: list[str] = []
        try:
            while self._staged:
                tmp, target = self._staged[0]
                commit_staged(tmp, target)
                self._staged.pop(0)  # 성공한 것만 목록에서 뺀다 — 나머지는 rollback 대상
                done.append(target.name)
        except OSError:
            pending = [target.name for _, target in self._staged]
            logger.warning(messages.LOG_UOW_PARTIAL, done or "없음", pending)
            self.rollback()
            raise

    def rollback(self) -> None:
        """준비한 ``.tmp`` 를 지운다 — 원본은 손대지 않았으므로 이것으로 끝이다."""
        for tmp, _ in self._staged:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:  # 지우지 못해도 원본은 무사하다. 다음 실행이 덮어쓴다.
                logger.debug(messages.LOG_TMP_CLEANUP_FAILED, tmp)
        self._staged.clear()

    # ---------- 컨텍스트 매니저 ----------

    def __enter__(self) -> UnitOfWork:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
