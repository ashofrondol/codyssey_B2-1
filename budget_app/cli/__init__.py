"""CLI 계층 — 사용자와 만나는 곳.

- ``app``           : 명령 레지스트리 + 오류 방패 + ``main`` (진입점)
- ``handlers``      : 명령 하나당 함수 하나 (인자 → 서비스 호출 → 프레젠터)
- ``parser``        : argparse 문법 정의 (핸들러를 모른다 — 문자열 키만 남긴다)
- ``prompts``       : 대화형 입력 (재입력 루프 / EOF 처리)
- ``presenter``     : 도메인 → 화면 문자열 (**출력하지 않고 반환**)
- ``output``        : 채널 결정 — stdout(결과) / stderr(진단) / logging(개발자)
- ``error_handler`` : 예외 → 사용자 메시지 → 종료 코드

``output`` 이 이 패키지 안에 있는 것은 실측 결과다 — 이 모듈을 import 하는 곳은
``app``·``error_handler``·``prompts`` 셋뿐이고 전부 CLI 계층이다.

## 이 파일만 재수출을 한다

다른 패키지의 ``__init__`` 은 비어 있지만 여기만 ``main`` 을 재수출한다.
``__main__.py`` 의 ``from .cli import main`` 이 그대로 동작해야 하고, ``main`` 은
이 패키지가 밖에 내보이는 **유일한 공개 심볼**이기 때문이다. 나머지 모듈은
``from .cli.presenter import ...`` 처럼 소유 모듈을 명시해서 쓴다.
"""

from .app import main

__all__ = ["main"]
