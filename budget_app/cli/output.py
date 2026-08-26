"""출력 채널 — 어떤 메시지가 어느 스트림으로 나가는지 이 모듈에서만 정한다.

채널은 셋이다.

- **stdout** : 프로그램의 *결과*. 목록/요약/저장 완료 등. ``out()`` 으로 낸다.
  리다이렉트(``list > out.txt``)와 파이프(``list | head``)가 가져가는 것이 이 채널이다.
- **stderr** : 사용자용 *진단*. ``[오류]``/``[힌트]`` 처럼 결과가 아닌 안내. ``err()``.
- **logging**: 개발자용 *진단*. 스택트레이스, 호출/시간 로그. 기본은 꺼져 있고
  ``--debug`` (또는 ``BUDGET_APP_DEBUG`` 환경변수)로만 켠다. 출력 대상은 역시 stderr.

왜 stdout 과 stderr 를 나누나:

1. **리다이렉트 오염 방지** — 오류가 stdout 으로 나가면 ``list > out.txt`` 의 데이터
   파일에 오류 문자열이 섞인다. 파이프라인에서 쓰는 도구로서는 버그다.
2. **파이프가 끊겨도 살아남음** — 하류가 먼저 닫혀 stdout 이 ``BrokenPipeError`` 로
   깨진 상황에서도 stderr 는 열려 있어 사용자에게 원인을 전할 수 있다.
3. **셸에서 골라 버릴 수 있음** — ``2>/dev/null`` 은 진단만, ``1>/dev/null`` 은 결과만
   버린다. 두 채널이 섞여 있으면 둘 다 불가능하다.

## ``out()`` 을 추가한 이유 (리팩터)

이전에는 stdout 쪽에 래퍼를 두지 않았다. "``print()`` 가 이미 stdout 이 기본이니
관례에서 벗어나는 쪽에만 이름을 붙인다"는 논리였는데, 그 결과 **이 모듈의 첫 줄이
선언한 규칙("채널은 여기서만 정한다")이 실제로는 지켜지지 않았다.** 결과 출력
``print()`` 26곳이 분리 전의 단일 CLI 모듈에 흩어져 있었기 때문이다.

지금은 두 채널 모두 이름이 있다. ``grep 'output\\.'`` 한 번이면 프로그램이 밖으로
내보내는 모든 글자의 목록이 나오고, 테스트에서 채널을 갈아 끼우는 것도 한 곳에서
끝난다.
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Iterable

from . import config, messages


def out(message: str = "") -> None:
    """프로그램의 결과 한 줄을 stdout 으로 출력한다."""
    print(message)


def out_lines(lines: Iterable[str]) -> None:
    """여러 줄을 stdout 으로 출력한다 — 프레젠터가 만든 줄을 그대로 흘려보낸다."""
    for line in lines:
        print(line)


def err(message: str = "") -> None:
    """사용자용 진단 한 줄을 stderr 로 출력한다.

    stderr 로 쓰기 전에 stdout 을 먼저 비운다. stdout 은 터미널이 아니면 블록
    버퍼링이라(stderr 는 버퍼링 없음), 비우지 않으면 ``cmd 2>&1 | less`` 처럼 두
    채널을 다시 합쳤을 때 진단이 결과보다 앞으로 튀어나온다.
    """
    try:
        sys.stdout.flush()
    except (BrokenPipeError, ValueError):
        # 하류 파이프가 이미 닫혔거나 stdout 이 닫힌 상태.
        # 그래도 stderr 는 살아 있으므로 진단 출력은 계속한다(이게 채널 분리의 이점).
        pass
    print(message, file=sys.stderr)


def err_lines(lines: Iterable[str]) -> None:
    for line in lines:
        err(line)


def _env_debug() -> bool:
    value = os.environ.get(config.DEBUG_ENV_VAR, "").strip().lower()
    return value not in config.FALSY_ENV_VALUES


#: ``setup_logging`` 이 확정한 디버그 여부(``--debug`` 플래그 + 환경변수).
#: ``handle_errors`` 가 "스택트레이스를 기록에 실을까"를 이 값 하나로 판단한다.
_debug_enabled = False


def debug_enabled() -> bool:
    """디버그 모드가 켜져 있는가 — ``setup_logging`` 이 확정한 값.

    ``handle_errors`` 는 로깅 설정을 직접 읽지 않는다. "디버그인가"의 정의가
    ``--debug`` 와 환경변수 둘로 나뉘어 있어서, 그 합성을 아는 곳(여기)이
    한 곳뿐이어야 두 경로의 동작이 갈라지지 않는다.
    """
    return _debug_enabled


def setup_logging(debug: bool = False) -> bool:
    """루트 로거에 핸들러를 붙인다 — ``main()`` 에서 한 번만 호출한다.

    이 호출은 두 가지를 확정한다 — **레벨/포맷**과 **디버그 여부**(``debug_enabled``).
    호출되지 않으면 로그 레벨이 기본값 WARNING 에 머무르고 디버그도 꺼진 것으로 간주되어,
    ``--debug`` 로 요청한 스택트레이스가 어디에도 남지 않는다. "사용자에게는 감추고
    ``--debug`` 일 때만 남긴다"는 ``handle_errors`` 의 정책은 이 함수가 있어야 성립한다.

    - ``debug=False`` → WARNING. 손상된 JSONL 줄 경고 등만 stderr 로 나온다.
      예기치 못한 예외는 "unhandled error" 한 줄만 남고 **스택트레이스는 붙지 않는다**
      (요구사항 Q2: 사용자 화면에는 스택트레이스 대신 원인 + 힌트).
    - ``debug=True``  → DEBUG. ``@log_call``/``@measure_time`` 의 호출 로그와
      예기치 못한 예외의 스택트레이스까지 stderr 로 나온다.

    반환: 실제로 디버그 모드가 켜졌는지 여부(플래그 또는 환경변수).
    """
    global _debug_enabled
    enabled = bool(debug) or _env_debug()
    _debug_enabled = enabled
    logging.basicConfig(
        level=logging.DEBUG if enabled else logging.WARNING,
        format=messages.LOG_FORMAT_DEBUG if enabled else messages.LOG_FORMAT,
        stream=sys.stderr,  # 로그는 결과가 아니므로 stdout 을 오염시키지 않는다.
        force=True,  # 이미 설정돼 있어도(재호출·테스트) 이 설정으로 덮어쓴다.
    )
    return enabled
