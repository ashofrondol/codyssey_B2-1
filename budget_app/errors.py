"""예외 계층 — 애플리케이션이 직접 정의하는 오류를 한곳에 모은다.

왜 별도 모듈인가:

리팩터 전에는 ``ValidationError`` 가 ``models.py``, ``AppError`` 가 ``decorators.py``
에 흩어져 있었다. 그래서 서비스 계층이 ``AppError`` 하나를 쓰려고 ``decorators`` 를
import 했고, ``decorators`` 는 다시 출력 채널 모듈(``output``)을 import 했다.
결과적으로 **서비스 계층이 프레젠테이션 모듈에 전이적으로 의존**하는 역류가 생겼다.

예외는 모든 계층이 공유하는 어휘이므로, 어느 계층에도 속하지 않는 이 모듈에 둔다.
이제 의존 방향은 한 방향으로만 흐른다::

    cli → services → repository → models → validators → errors
                                                        ↑
    decorators / output / presenter ────────────────────┘

두 예외의 차이:

- ``ValidationError`` — *값* 이 규칙을 어겼다. 어떤 값이 왜 틀렸는지만 안다.
  발생 지점은 ``validators`` 와 모델 생성자다.
- ``AppError``       — *상황* 이 규칙을 어겼다. "등록되지 않은 카테고리", "id 없음"
  처럼 값 하나만 봐서는 알 수 없고 저장된 상태를 함께 봐야 판단되는 오류다.
  사용자가 다음에 뭘 하면 되는지(``hint``)를 함께 들고 다닌다.

이 구분이 그대로 종료 코드로 이어진다(``EXIT_VALIDATION`` vs ``EXIT_APP``).
"""

from __future__ import annotations


class ValidationError(ValueError):
    """입력값이 필드 규칙을 위반했다 — CLI 단에서 사용자 친화 메시지로 변환된다.

    ``ValueError`` 를 상속하는 이유: 의미상 "값이 잘못됨"이 맞고, 이 예외를 모르는
    호출자도 ``except ValueError`` 로 자연스럽게 받을 수 있다.
    """


class AppError(Exception):
    """사용자에게 보여줄 메시지를 가진 애플리케이션 오류.

    스택트레이스 대신 message + hint 형태로 출력된다.
    ``hint`` 는 "그래서 뭘 하면 되는가"를 한 줄로 답하는 자리다.
    """

    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.message = message
        self.hint = hint
