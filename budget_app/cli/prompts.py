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

from dataclasses import dataclass
from typing import Callable, List, Optional, TypeVar

from ..domain import validators
from ..errors import AppError, ValidationError
from ..storage.repositories import CategoryStore
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
    tags: List[str]


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


def registered_category_validator(cats: CategoryStore) -> Callable[[str], str]:
    """등록된 카테고리만 통과시키는 검증기 (미등록이면 ``ValidationError`` → 재입력).

    ``validators`` 의 함수들과 달리 저장소를 봐야 판단되므로 여기서 만든다.
    필드 규칙(``parse_category``)은 그대로 재사용하고 '등록 여부'만 덧댄다.
    """

    def _validate(raw: str) -> str:
        name = validators.parse_category(raw)
        if cats.exists(name):
            return name
        available = ", ".join(cats.list_names())
        raise ValidationError(
            messages.ERR_CATEGORY_NOT_REGISTERED_AVAILABLE.format(name=name, available=available)
        )

    return _validate


def ask_transaction(cats: CategoryStore) -> TransactionInput:
    """거래 한 건에 필요한 값을 순서대로 받아 온다."""
    return TransactionInput(
        date=ask_until(messages.PROMPT_DATE, validators.parse_date),
        type=ask_until(messages.PROMPT_TYPE, validators.parse_type),
        category=ask_until(messages.PROMPT_CATEGORY, registered_category_validator(cats)),
        amount=ask_until(messages.PROMPT_AMOUNT, validators.parse_amount),
        memo=validators.parse_memo(ask(messages.PROMPT_MEMO)),
        tags=validators.parse_tags(ask(messages.PROMPT_TAGS)),
    )


def ask_category_name(given: Optional[str]) -> str:
    """``--name`` 이 있으면 검증만, 없으면 물어본다."""
    if given is not None:
        return validators.parse_category(given)
    return ask_until(messages.PROMPT_CATEGORY_NAME, validators.parse_category)
