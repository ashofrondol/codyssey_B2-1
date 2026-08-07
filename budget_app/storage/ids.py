"""거래 ID 발급 — "무엇이 이미 쓰였는가"를 아는 곳.

ID 의 *형식* 은 도메인 값 객체(``domain.tx_id.TransactionId``)가 알고, 이 모듈은
**파일 상태에 의존하는 부분**만 담당한다. 발급이 도메인이 아닌 이유가 그것이다 —
"다음 번호"는 저장된 내용을 봐야 정해진다.
"""

from __future__ import annotations

from typing import Iterable, Optional, Set

from ..domain.tx_id import TransactionId


class IdAllocator:
    """거래 ID 발급기 — 이미 쓰인 번호를 건너뛰며 순차 발급한다.

    이전에는 발급 규칙이 두 곳에 있었다. 저장소의 ``next_id()`` 와, 성능 때문에
    그것을 흉내 낸 ``import_csv`` 안의 ``next_num += 1``. 서비스가 저장소의 ID
    포맷을 알아야 했고, 두 경로가 어긋날 여지가 있었다. 발급기를 객체로 만들어
    한 번 받아 여러 번 쓰면, 파일 재스캔 없이도 규칙은 한 곳에 남는다.

    ``taken`` 을 들고 다니는 이유: CSV 가 명시한 id 를 그대로 쓰는 경우가 생기면서,
    "자동 발급 번호가 나중에 그 id 와 부딪치지 않는다"를 보장해야 한다.
    """

    def __init__(self, start: int = 0, taken: Optional[Iterable[TransactionId]] = None) -> None:
        self._counter = start
        self._taken: Set[TransactionId] = set(taken or ())

    def is_taken(self, tx_id: TransactionId) -> bool:
        return tx_id in self._taken

    def reserve(self, tx_id: TransactionId) -> None:
        """외부에서 지정한 id 를 점유 처리한다(CSV 가 실어 온 id 등)."""
        self._taken.add(tx_id)
        self._counter = max(self._counter, tx_id.number)

    def next(self) -> TransactionId:
        """아직 쓰이지 않은 다음 번호를 발급한다.

        ``while`` 인 이유: CSV 가 큰 번호를 먼저 실어 오면 ``reserve`` 가 카운터를
        끌어올리지만, 순서가 뒤죽박죽이면 이미 점유된 번호에 부딪칠 수 있다.
        """
        while True:
            self._counter += 1
            candidate = TransactionId.of(self._counter)
            if candidate not in self._taken:
                self._taken.add(candidate)
                return candidate
