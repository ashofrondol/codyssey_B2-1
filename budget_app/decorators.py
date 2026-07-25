"""공통 관심사 데코레이터: 로그/예외/실행 시간 측정."""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable

from . import config
from .models import ValidationError


logger = logging.getLogger(config.LOGGER_NAME)


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
        logger.debug(config.LOG_CALL, func.__name__)
        result = func(*args, **kwargs)
        logger.debug(config.LOG_DONE, func.__name__)
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
            logger.debug(config.LOG_TOOK, func.__name__, elapsed)

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
            return func(*args, **kwargs) or config.EXIT_OK
        except ValidationError as exc:
            print(config.MSG_ERROR_LINE.format(msg=exc))
            print(config.HINT_VALIDATION)
            return config.EXIT_VALIDATION
        except BrokenPipeError:
            # 하류 파이프(`list | head`)가 먼저 닫힘. 여기서 print 하면 또 깨지므로
            # 최상위(main)로 넘겨 조용히 처리하게 한다.
            raise
        except FileNotFoundError as exc:
            print(config.MSG_ERR_FILE_NOT_FOUND.format(name=exc.filename or exc))
            print(config.HINT_FILE_NOT_FOUND)
            return config.EXIT_IO
        except IsADirectoryError as exc:
            print(config.MSG_ERR_IS_A_DIR.format(name=exc.filename or exc))
            print(config.HINT_IS_A_DIR)
            return config.EXIT_IO
        except PermissionError as exc:
            print(config.MSG_ERR_PERMISSION.format(name=exc.filename or exc))
            print(config.HINT_PERMISSION)
            return config.EXIT_IO
        except UnicodeDecodeError:
            print(config.MSG_ERR_ENCODING)
            print(config.HINT_ENCODING)
            return config.EXIT_ENCODING
        except AppError as exc:
            print(config.MSG_ERROR_LINE.format(msg=exc.message))
            if exc.hint:
                print(config.MSG_HINT_LINE.format(msg=exc.hint))
            return config.EXIT_APP
        except KeyboardInterrupt:
            print(config.MSG_INTERRUPTED)
            return config.EXIT_INTERRUPT
        except OSError as exc:
            # 디스크 가득 참(ENOSPC), 파일 잠금 등 위에서 못 잡은 입출력 오류.
            print(config.MSG_ERR_IO.format(error=exc))
            print(config.HINT_IO)
            return config.EXIT_IO
        except Exception as exc:  # noqa: BLE001 — 사용자에게 스택트레이스를 노출하지 않기 위함
            logger.debug(config.LOG_UNHANDLED, exc_info=True)
            print(config.MSG_ERR_UNEXPECTED.format(error=exc))
            print(config.HINT_UNEXPECTED)
            return config.EXIT_ERROR

    return wrapper
