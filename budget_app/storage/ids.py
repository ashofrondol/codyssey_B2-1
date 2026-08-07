"""거래 ID 발급 — "무엇이 이미 쓰였는가"를 아는 곳.

ID 의 *형식* 은 도메인 값 객체(``domain.tx_id.TransactionId``)가 알고, 이 모듈은
**파일 상태에 의존하는 부분**만 담당한다. 발급이 도메인이 아닌 이유가 그것이다 —
"다음 번호"는 저장된 내용을 봐야 정해진다.

여기 있는 것 둘:

- ``IdWatermark`` — 발급된 적 있는 최대 번호를 **파일에 남긴다**(삭제해도 안 줄어듦)
- ``IdAllocator`` — 그 기준선 위에서 실제 번호를 발급한다
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from ..domain.tx_id import TransactionId
from . import config, messages
from .jsonl import atomic_write_lines

logger = logging.getLogger(config.LOGGER_NAME)


class IdWatermark:
    """발급된 적 있는 최대 번호를 파일 하나에 기록한다 — **줄어들지 않는 기준선**.

    ## 왜 파일 스캔만으로는 부족한가

    이전에는 시작점을 "현재 파일에 있는 id 중 최대값"으로 잡았다. 그런데 그 값은
    **삭제하면 줄어든다**::

        add → TX-000001, TX-000002        (최대 2)
        delete TX-000002                  (최대 1 로 되돌아감)
        add → TX-000002                   ← 지운 번호가 부활

    같은 번호가 다른 거래에 다시 붙는 것 자체는 "id 는 유일하다"를 지키므로 파일만
    보면 정상으로 보인다. 문제는 **밖으로 나간 id** 다. 먼저 내보낸 CSV 에는 옛
    ``TX-000002``(다른 거래)가 들어 있고, 그것을 기본 정책(``skip``)으로 다시
    가져오면 "이미 있는 id" 로 판정돼 **조용히 버려진다**. 사용자에게는 백업에서
    복원한 거래 한 건이 이유 없이 사라진 것으로 보인다.

    그래서 "지금 무엇이 있는가"(파일 스캔)와 "무엇을 발급한 적이 있는가"(이 워터마크)를
    **분리해서** 둘 다 본다.

    ## 왜 이렇게 단순한가

    숫자 한 줄짜리 파일이고, 읽기 실패는 전부 0 으로 떨어뜨린다. 이 파일이 없거나
    깨져도 프로그램은 리팩터 이전과 똑같이 동작해야 하기 때문이다 — 안전장치가
    고장 나서 본체가 멈추면 안 된다.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def read(self) -> int:
        """기록된 최대 번호. 파일이 없거나 내용이 이상하면 0."""
        try:
            text = self.path.read_text(encoding=config.FILE_ENCODING).strip()
        except OSError:
            return 0  # 없음 — 첫 실행이거나 이전 버전의 데이터 폴더
        if not text:
            return 0
        try:
            return max(0, int(text))
        except ValueError:
            logger.warning(messages.LOG_WATERMARK_CORRUPT, self.path.name, text)
            return 0

    def remember(self, number: int) -> None:
        """``number`` 가 지금 기록보다 크면 갱신한다 — 작으면 아무것도 하지 않는다.

        원자적 교체로 쓰는 이유: 이 파일이 반쯤 쓰인 상태로 남으면 ``read`` 가 0 을
        돌려주고 방어가 통째로 사라진다.
        """
        if number > self.read():
            atomic_write_lines(self.path, [str(number)])


class IdAllocator:
    """거래 ID 발급기 — 이미 쓰인 번호를 건너뛰며 순차 발급한다.

    이전에는 발급 규칙이 두 곳에 있었다. 저장소의 ``next_id()`` 와, 성능 때문에
    그것을 흉내 낸 ``import_csv`` 안의 ``next_num += 1``. 서비스가 저장소의 ID
    포맷을 알아야 했고, 두 경로가 어긋날 여지가 있었다. 발급기를 객체로 만들어
    한 번 받아 여러 번 쓰면, 파일 재스캔 없이도 규칙은 한 곳에 남는다.

    ``taken`` 을 들고 다니는 이유: CSV 가 명시한 id 를 그대로 쓰는 경우가 생기면서,
    "자동 발급 번호가 나중에 그 id 와 부딪치지 않는다"를 보장해야 한다.
    """

    def __init__(self, start: int = 0, taken: Iterable[TransactionId] | None = None) -> None:
        self._counter = start
        self._taken: set[TransactionId] = set(taken or ())

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
