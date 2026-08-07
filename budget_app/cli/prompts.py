"""대화형 입력 — 표준입력에서 값을 받아 내는 일만 담당한다.

핸들러에서 떼어낸 이유: ``cmd_add`` 가 "무엇을 물어보고, 틀리면 몇 번까지 다시
받고, EOF 면 어떻게 끝낼지"까지 알고 있으면 한 함수가 입력 정책과 유스케이스
호출을 겸하게 된다. 지금 ``cmd_add`` 는 ``ask_transaction()`` 한 줄로 값을 받고
서비스에 넘기기만 한다.

정책 통일도 함께 이뤄졌다. 이전에는 ``category add`` 만 ``ask()`` 를 한 번 부르고
끝나서, 빈 이름을 넣으면 재입력 없이 종료 코드 2 로 죽었다. 같은 "대화형 입력"인데
거래 추가와 규칙이 달랐다. 지금은 모든 대화형 입력이 ``ask_until`` 을 지난다.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from ..domain import validators
from ..errors import AppError, ValidationError
from ..services import messages as service_messages
from ..services.categories import CategoryService
from . import config, messages, output

T = TypeVar("T")


class InputAborted(AppError):
    """대화형 입력이 EOF(Ctrl+D)/스트림 종료로 중단됨.

    ``handle_errors`` 가 ``AppError`` 로 처리하므로 스택트레이스 없이 깔끔히 끝난다.
    이 예외가 없으면 파이프로 입력을 주다가 EOF 가 나는 순간 ``ask`` 가 빈 문자열을
    돌려주고, 검증기가 이를 거부하며 루프가 영원히 돈다.
    """

    def __init__(self) -> None:
        super().__init__(messages.ERR_INPUT_ABORTED, hint=messages.HINT_INPUT_ABORTED)


@dataclass(frozen=True)
class TransactionInput:
    """대화형으로 받은 거래 입력 — 서비스에 그대로 펼쳐 넘긴다."""

    date: str
    type: str
    category: str
    amount: int
    memo: str
    tags: list[str]


def ask(prompt: str) -> str:
    """대화형 한 줄 입력. EOF 는 무한 대기/무한 루프 대신 즉시 중단으로 처리한다."""
    try:
        return input(prompt)
    except EOFError as exc:
        raise InputAborted() from exc


def ask_until(prompt: str, validator: Callable[[str], T]) -> T:
    """``validator(raw)`` 가 정상값을 반환할 때까지 재입력을 요구한다.

    - EOF → ``InputAborted`` 로 즉시 종료(무한 루프 방지).
    - 유효하지 않은 값이 계속 들어오면 ``MAX_INPUT_RETRIES`` 회에서 중단한다.
    """
    for _ in range(config.MAX_INPUT_RETRIES):
        raw = ask(prompt)
        try:
            return validator(raw)
        except ValidationError as exc:
            # 재입력 안내는 결과가 아니라 진단이므로 stderr 로 보낸다.
            output.err(messages.MSG_ERROR_LINE.format(msg=exc))
            output.err(messages.MSG_HINT_RETRY)
    raise AppError(messages.ERR_MAX_RETRIES, hint=messages.HINT_MAX_RETRIES)


def registered_category_validator(cat_service: CategoryService) -> Callable[[str], str]:
    """등록된 카테고리만 통과시키는 검증기 (미등록이면 ``ValidationError`` → 재입력).

    ``validators`` 의 함수들과 달리 **저장된 상태를 봐야** 판단되므로 여기서 만든다.
    필드 규칙(``parse_category``)은 그대로 재사용하고 '등록 여부'만 덧댄다.

    ## 왜 ``CategoryStore`` 가 아니라 ``CategoryService`` 인가

    이전에는 저장소를 직접 받았다. CLI 가 서비스를 건너뛰고 저장소를 부르는
    유일한 자리였고, 그래서 "CLI 는 서비스와만 말한다"가 규칙이 아니라 관습이었다.

    ## 왜 예외 종류가 서비스와 다른가

    같은 상황을 ``TransactionService`` 는 ``AppError`` 로, 여기서는
    ``ValidationError`` 로 던진다. 모순이 아니라 **대화형이라는 맥락의 차이**다.
    ``ask_until`` 은 ``ValidationError`` 를 잡아 다시 묻는데, 사용자가 카테고리
    이름을 다시 칠 수 있는 자리에서는 그것이 맞는 처리다. 옵션으로 한 번에 넘기는
    경로에는 다시 물을 기회가 없으므로 그대로 끝내야 한다.

    문장은 하나만 존재한다 — 상황의 이름은 서비스가 소유하고(``서비스 messages``),
    CLI 는 대화형에서만 의미 있는 "사용 가능 목록"을 덧붙인다.
    """

    def _validate(raw: str) -> str:
        name = validators.parse_category(raw)
        if cat_service.exists(name):
            return name
        raise ValidationError(
            service_messages.ERR_CATEGORY_NOT_REGISTERED.format(name=name)
            + messages.FMT_AVAILABLE_SUFFIX.format(available=", ".join(cat_service.list_names()))
        )

    return _validate


def ask_transaction(cat_service: CategoryService) -> TransactionInput:
    """거래 한 건에 필요한 값을 순서대로 받아 온다."""
    return TransactionInput(
        date=ask_until(messages.PROMPT_DATE, validators.parse_date),
        type=ask_until(messages.PROMPT_TYPE, validators.parse_type),
        category=ask_until(messages.PROMPT_CATEGORY, registered_category_validator(cat_service)),
        amount=ask_until(messages.PROMPT_AMOUNT, validators.parse_amount),
        memo=validators.parse_memo(ask(messages.PROMPT_MEMO)),
        tags=validators.parse_tags(ask(messages.PROMPT_TAGS)),
    )


def ask_category_name(given: str | None) -> str:
    """``--name`` 이 있으면 검증만, 없으면 물어본다."""
    if given is not None:
        return validators.parse_category(given)
    return ask_until(messages.PROMPT_CATEGORY_NAME, validators.parse_category)
