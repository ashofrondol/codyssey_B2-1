"""횡단 관심사 데코레이터 — 관측(로그/실행시간)만 담당한다.

## 왜 ``handle_errors`` 가 여기 없나

예외를 사용자 메시지와 종료 코드로 바꾸는 일은 **CLI 의 표현 정책**이다. 그것이
이 파일에 함께 있으면 ``decorators`` 가 출력 모듈(``output``)을 import 해야 하고,
서비스 계층은 ``@log_call`` 하나를 쓰려다 **화면 출력 모듈까지 끌고 들어오게** 된다:

    services → decorators → output      ← 서비스가 프레젠테이션에 전이 의존

그래서 ``handle_errors`` 는 ``error_handler.py`` (CLI 계층)로 옮겼다. 지금 이 모듈이
아는 것은 ``logging`` 과 문자열 템플릿뿐이고, 어느 계층에서 써도 아래로만 의존한다.

남은 둘은 진짜 횡단 관심사다. "무엇을 계산하는가"와 무관하게 "언제 불렸고 얼마나
걸렸는가"를 기록하는 일이라, 함수 본문에 섞이면 본래 로직을 가린다.
"""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import Any

from . import config

#: 이 세 문구는 이 모듈만 쓴다. 별도 messages 파일로 빼면 3줄짜리 파일이 생기고
#: 오히려 찾기 어려워진다. %-스타일인 이유는 logging 의 지연 포맷팅 때문이다.
LOG_CALL = "call %s"
LOG_DONE = "done %s"
LOG_TOOK = "%s took %.2fms"

logger = logging.getLogger(config.LOGGER_NAME)


def log_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """함수 호출/반환을 DEBUG 로그로 남긴다."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(LOG_CALL, func.__name__)
        result = func(*args, **kwargs)
        logger.debug(LOG_DONE, func.__name__)
        return result

    return wrapper


def measure_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """함수 실행 시간을 DEBUG 로그로 남긴다.

    ``try/finally`` 인 이유: 예외로 빠져나가는 경로에서도 시간이 찍혀야 "느려서
    타임아웃이 났다"와 "즉시 터졌다"를 구분할 수 있다.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(LOG_TOOK, func.__name__, elapsed)

    return wrapper
