"""예외 → 사용자 메시지 → 종료 코드 변환 — CLI 계층의 표현 정책.

``decorators.py`` 에서 떼어낸 이유는 그 파일 첫머리에 적어 두었다. 요약하면,
이것은 "어떤 예외를 사용자에게 어떤 문구로 보여 주고 셸에 어떤 숫자를 돌려줄까"를
정하는 **화면 정책**이라 서비스 계층이 알 필요가 없다.
"""

from __future__ import annotations

import functools
import logging
from typing import Callable

from . import config, messages, output
from .errors import AppError, ValidationError

logger = logging.getLogger(config.LOGGER_NAME)


def handle_errors(func: Callable[..., int]) -> Callable[..., int]:
    """CLI 핸들러 공용 — 예외를 잡아 [오류]/[힌트] 를 **stderr** 로 내보내고 종료 코드를 반환한다.

    여기서 잡는 예외는 성격이 네 부류로 갈리고, except 절도 그 순서대로 묶여 있다.
    파이썬은 '먼저 일치하는 절'을 실행하므로 except 순서가 곧 정책이고, 그래서
    같은 부류끼리 붙여 두어야 "왜 이 순서인가"가 코드에서 읽힌다.

    1. **종료 신호** — 오류가 아니다. 사용자나 하류 프로세스가 "그만"이라고 알린 것.
       ``BrokenPipeError`` / ``KeyboardInterrupt``
    2. **입력 오류** — 사용자가 값을 고치면 해결된다.
       ``ValidationError`` / ``AppError``
    3. **환경 상태** — 프로그램 밖(파일·권한·디스크·인코딩)의 상태 문제.
       ``FileNotFoundError`` / ``IsADirectoryError`` / ``PermissionError`` /
       ``UnicodeDecodeError`` / ``OSError``
    4. **최후 방어선** — 위 어디에도 속하지 않는 버그.
       ``Exception`` — 사용자에겐 스택트레이스를 감추고 로그에만 남긴다.

    부류를 나눠도 지켜야 하는 상속 제약이 둘 있고, 지금 순서가 둘 다 만족한다:

    - ``BrokenPipeError`` 는 ``OSError`` 의 자식이라 (3) 의 ``OSError`` 보다 위여야 한다.
      → (1) 이 맨 앞이므로 자동으로 만족한다.
    - (3) 안에서도 ``FileNotFoundError``·``IsADirectoryError``·``PermissionError`` 는
      ``OSError`` 의 자식이므로 마지막 ``OSError`` 보다 위에 둔다.

    반환값 규약: 핸들러가 ``None`` 을 반환하면 ``EXIT_OK`` 로 본다.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> int:
        try:
            result = func(*args, **kwargs)
            # `func(...) or EXIT_OK` 로 쓰면 0/""/[]/False 같은 falsy 반환값까지
            # 전부 EXIT_OK 로 바뀐다. 규약은 "None 이면 EXIT_OK" 이므로 None 만
            # 정확히 검사한다 (EXIT_OK 가 0 이 아니게 되어도 의미가 흔들리지 않는다).
            return config.EXIT_OK if result is None else result

        # ---------- (1) 종료 신호 — 오류가 아님 ----------
        except BrokenPipeError:
            # 하류 파이프(`list | head`)가 먼저 닫힘. 여기서 출력하면 또 깨지므로
            # 최상위(main)로 넘겨 조용히 처리하게 한다.
            raise
        except KeyboardInterrupt:
            output.err(messages.MSG_INTERRUPTED)
            return config.EXIT_INTERRUPT

        # ---------- (2) 입력 오류 — 사용자가 값을 고치면 해결됨 ----------
        except ValidationError as exc:
            output.err(messages.MSG_ERROR_LINE.format(msg=exc))
            output.err(messages.HINT_VALIDATION)
            return config.EXIT_VALIDATION
        except AppError as exc:
            output.err(messages.MSG_ERROR_LINE.format(msg=exc.message))
            if exc.hint:
                output.err(messages.MSG_HINT_LINE.format(msg=exc.hint))
            return config.EXIT_APP

        # ---------- (3) 환경 상태 — 파일/권한/인코딩/디스크 ----------
        except FileNotFoundError as exc:
            output.err(messages.MSG_ERR_FILE_NOT_FOUND.format(name=exc.filename or exc))
            output.err(messages.HINT_FILE_NOT_FOUND)
            return config.EXIT_IO
        except IsADirectoryError as exc:
            output.err(messages.MSG_ERR_IS_A_DIR.format(name=exc.filename or exc))
            output.err(messages.HINT_IS_A_DIR)
            return config.EXIT_IO
        except PermissionError as exc:
            output.err(messages.MSG_ERR_PERMISSION.format(name=exc.filename or exc))
            output.err(messages.HINT_PERMISSION)
            return config.EXIT_IO
        except UnicodeDecodeError:
            output.err(messages.MSG_ERR_ENCODING)
            output.err(messages.HINT_ENCODING)
            return config.EXIT_ENCODING
        except OSError as exc:
            # 디스크 가득 참(ENOSPC), 파일 잠금 등 위에서 못 잡은 입출력 오류.
            output.err(messages.MSG_ERR_IO.format(error=exc))
            output.err(messages.HINT_IO)
            return config.EXIT_IO

        # ---------- (4) 최후 방어선 — 분류 밖의 버그 ----------
        except Exception as exc:  # noqa: BLE001 — 사용자에게 스택트레이스를 노출하지 않기 위함
            # 사용자에겐 한 줄 요약만, 원인 추적용 스택트레이스는 로그로 보존한다.
            # 이 로그가 실제로 보이려면 output.setup_logging() 이 핸들러를 붙여야
            # 하고, DEBUG 레벨은 `--debug`(또는 BUDGET_APP_DEBUG)로만 켜진다.
            logger.debug(messages.LOG_UNHANDLED, exc_info=True)
            output.err(messages.MSG_ERR_UNEXPECTED.format(error=exc))
            output.err(messages.HINT_UNEXPECTED)
            return config.EXIT_ERROR

    return wrapper
