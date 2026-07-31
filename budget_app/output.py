"""출력 채널 — 어떤 메시지가 어느 스트림으로 나가는지 이 모듈에서만 정한다.

채널은 셋이다.

- **stdout** : 프로그램의 *결과*. 목록/요약/저장 완료 등. 그냥 ``print()`` 로 낸다.
  리다이렉트(``list > out.txt``)와 파이프(``list | head``)가 가져가는 것이 이 채널이다.
- **stderr** : 사용자용 *진단*. ``[오류]``/``[힌트]`` 처럼 결과가 아닌 안내. ``err()`` 로 낸다.
- **logging**: 개발자용 *진단*. 스택트레이스, 호출/시간 로그. 기본은 꺼져 있고
  ``--debug`` (또는 ``BUDGET_APP_DEBUG`` 환경변수)로만 켠다. 출력 대상은 역시 stderr.

왜 stdout 과 stderr 를 나누나:

1. **리다이렉트 오염 방지** — 오류가 stdout 으로 나가면 ``list > out.txt`` 의 데이터
   파일에 오류 문자열이 섞인다. 파이프라인에서 쓰는 도구로서는 버그다.
2. **파이프가 끊겨도 살아남음** — 하류가 먼저 닫혀 stdout 이 ``BrokenPipeError`` 로
   깨진 상황에서도 stderr 는 열려 있어 사용자에게 원인을 전할 수 있다.
3. **셸에서 골라 버릴 수 있음** — ``2>/dev/null`` 은 진단만, ``1>/dev/null`` 은 결과만
   버린다. 두 채널이 섞여 있으면 둘 다 불가능하다.

stdout 쪽에 굳이 ``out()`` 래퍼를 두지 않은 이유: ``print()`` 가 이미 stdout 이 기본이라
관례에서 벗어나는 쪽(stderr / logging)에만 이름을 붙이는 편이 규칙을 더 잘 드러낸다.
"""

from __future__ import annotations

import logging
import os
import sys

from . import config


def err(message: str = "") -> None:
    """사용자용 진단 한 줄을 stderr 로 출력한다.

    ``print(...)`` 대신 이 함수를 쓰는 지점이 곧 '결과가 아닌 메시지' 목록이다
    (``grep 'output.err'`` 한 번이면 전부 보인다).

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


# BUDGET_APP_DEBUG 가 이 값들이면 '꺼짐'으로 본다.
# (단순히 "값이 있으면 켜짐"으로 하면 BUDGET_APP_DEBUG=0 이 오히려 켜지는 사고가 난다.)
_FALSY_ENV_VALUES = frozenset({"", "0", "false", "no", "off"})


def _env_debug() -> bool:
    return os.environ.get(config.DEBUG_ENV_VAR, "").strip().lower() not in _FALSY_ENV_VALUES


def setup_logging(debug: bool = False) -> bool:
    """루트 로거에 핸들러를 붙인다 — ``main()`` 에서 한 번만 호출한다.

    이 호출이 없으면 ``logging.getLogger(...)`` 로 만든 로거에는 핸들러가 하나도
    없고 유효 레벨도 WARNING 이라, ``logger.debug(..., exc_info=True)`` 로 보존한
    스택트레이스가 **어디에도 남지 않는다**. "사용자에게는 감추고 로그로 보존한다"는
    ``handle_errors`` 의 의도는 이 함수가 있어야 비로소 성립한다.

    - ``debug=False`` → WARNING. 손상된 JSONL 줄 경고 등만 stderr 로 나온다.
    - ``debug=True``  → DEBUG. ``@log_call``/``@measure_time`` 의 호출 로그와
      예기치 못한 예외의 스택트레이스까지 stderr 로 나온다.

    반환: 실제로 디버그 모드가 켜졌는지 여부(플래그 또는 환경변수).
    """
    enabled = bool(debug) or _env_debug()
    logging.basicConfig(
        level=logging.DEBUG if enabled else logging.WARNING,
        format=config.LOG_FORMAT_DEBUG if enabled else config.LOG_FORMAT,
        stream=sys.stderr,  # 로그는 결과가 아니므로 stdout 을 오염시키지 않는다.
        force=True,  # 이미 설정돼 있어도(재호출·테스트) 이 설정으로 덮어쓴다.
    )
    return enabled
