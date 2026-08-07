"""애플리케이션 정체성 — 어느 계층에도 속하지 않는 앱 전역 이름.

## 진입 기준

여기 남는 것은 **"이 프로그램이 무엇으로 불리는가"** 뿐이다. 계층 하나만 쓰는 값은
그 계층의 ``config.py`` 로 내려갔다.

측정 결과가 그 분할을 뒷받침한다 — 이전 ``config.py`` 의 상수 46개 중 39개가
**단일 계층에서만** 쓰였고, ``messages.py`` 는 105개 중 104개가 그랬다. 한 파일에
모아 두면 도메인 검증기가 CLI 프롬프트 71개와 같은 모듈에 묶인다.

계층을 넘나드는 값은 **아래 계층이 소유하고 위 계층이 가져다 쓴다**.

| 값 | 소유 | 소비 |
|---|---|---|
| ``VALID_TYPES`` | ``domain.config`` | domain, cli(argparse choices) |
| ``TAG_SEPARATOR`` | ``domain.config`` | domain, storage(CSV join) |
| ``ON_DUPLICATE_*`` | ``services.config`` | services, cli(argparse choices) |
| ``DEFAULT_TOP_N`` | ``services.config`` | services, cli(기본값) |
"""

#: 앱 이름 하나만 소유한다. 계층별 자식 로거는 각 계층 config 가 여기서 **파생**시킨다
#: (이전에는 여기에 LOGGER_NAME_STORAGE 를 따로 두고 storage/config 가 그것을
#:  이름만 바꿔 재수출했다 — 값 하나가 세 곳을 거치는 순수 보일러플레이트였다).
LOGGER_NAME = "budget_app"
