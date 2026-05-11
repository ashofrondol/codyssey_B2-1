"""공통 관심사 데코레이터: 로그/예외/실행 시간 측정."""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable

from .models import ValidationError


logger = logging.getLogger("budget_app")


class AppError(Exception):
    """사용자에게 보여줄 메시지를 가진 애플리케이션 오류.

    스택트레이스 대신 message + hint 형태로 출력된다.
    """

    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.message = message
        self.hint = hint


def log_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """함수 호출/반환을 DEBUG 로그로 남긴다."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug("call %s", func.__name__)
        result = func(*args, **kwargs)
        logger.debug("done %s", func.__name__)
        return result

    return wrapper


def measure_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """함수 실행 시간을 DEBUG 로그로 남긴다."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug("%s took %.2fms", func.__name__, elapsed)

    return wrapper


def handle_errors(func: Callable[..., int]) -> Callable[..., int]:
    """CLI 핸들러 공용 — 예외를 잡아 [오류]/[힌트] 형식으로 출력하고 종료 코드를 반환한다.

    - ValidationError → 입력 오류로 안내
    - FileNotFoundError → 파일 경로 안내
    - AppError → message + hint 그대로 출력
    - 기타 Exception → 일반 오류 메시지 (스택트레이스 출력 금지)
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> int:
        try:
            return func(*args, **kwargs) or 0
        except ValidationError as exc:
            print(f"[오류] {exc}")
            print("[힌트] 입력값을 다시 확인해 주세요.")
            return 2
        except FileNotFoundError as exc:
            print(f"[오류] 파일을 찾을 수 없습니다: {exc.filename or exc}")
            print("[힌트] 경로가 올바른지, 파일이 존재하는지 확인해 주세요.")
            return 3
        except AppError as exc:
            print(f"[오류] {exc.message}")
            if exc.hint:
                print(f"[힌트] {exc.hint}")
            return 4
        except KeyboardInterrupt:
            print("\n[중단] 사용자에 의해 종료되었습니다.")
            return 130
        except Exception as exc:  # noqa: BLE001 — 사용자에게 스택트레이스를 노출하지 않기 위함
            logger.debug("unhandled error", exc_info=True)
            print(f"[오류] 예기치 못한 오류가 발생했습니다: {exc}")
            print("[힌트] 동일 증상이 반복되면 데이터 파일과 명령을 확인해 주세요.")
            return 1

    return wrapper
