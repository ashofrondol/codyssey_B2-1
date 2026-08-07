"""기간 규칙 — "이 달에 속하는가"의 정의처.

이전에는 CLI 가 ``calendar.monthrange`` 로 말일을 구하고(``_month_bounds``), 서비스는
``date.startswith(month + "-")`` 로 판정해서 **같은 개념이 두 계층에 서로 다른
알고리즘으로** 구현돼 있었다. 도메인으로 내려 하나로 합쳤다.

모듈 이름이 ``calendar`` 가 아닌 이유: 표준 라이브러리 ``calendar`` 와 이름이 겹치면
읽는 사람이 어느 쪽인지 헷갈린다(파이썬 3 의 절대 import 규칙상 동작에는 문제가
없지만, 혼동 자체가 비용이다).
"""

from __future__ import annotations

import calendar
from datetime import datetime

from . import config, validators


def month_range(month: str) -> tuple[str, str]:
    """``'YYYY-MM'`` → ``('YYYY-MM-01', 'YYYY-MM-<그 달의 말일>')``.

    모든 달을 31일로 가정하면 2월·30일 달에서 범위가 어긋난다. ``calendar`` 로
    실제 말일을 구한다. 검색·요약·내보내기가 모두 이 함수 하나를 쓰므로
    "이 달에 속하는가"의 정의가 프로그램 전체에서 하나다.
    """
    normalized = validators.parse_month(month)
    dt = datetime.strptime(normalized, config.MONTH_FORMAT)
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return f"{normalized}-01", f"{normalized}-{last_day:02d}"
