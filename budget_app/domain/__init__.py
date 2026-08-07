"""도메인 계층 — 데이터의 모양과 규칙.

- ``validators`` : 필드 규칙의 단일 정의처 (규칙 하나 = 함수 하나)
- ``tx_id``      : 거래 ID 값 객체 — 형식·파싱·생성이 한곳에
- ``entities``   : 저장 엔티티(Transaction/Budget/Category) + TransactionPatch
- ``specs``      : 검색 명세(Specification) — 조합 가능한 조건
- ``queries``    : ``SearchFilter`` — CLI 인자를 명세로 조립하는 어댑터
- ``results``    : 계산 결과 모델(MonthlySummary/ImportReport)
- ``periods``    : 기간 규칙 — "이 달에 속하는가"의 정의처

이 패키지는 I/O 를 전혀 모른다. ``open``·``print``·``input`` 이 하나도 없으므로
파일 없이 단독으로 테스트할 수 있다.

**재수출하지 않는다.** ``from ..domain.entities import Transaction`` 처럼 소유 모듈을
명시해 "어느 파일이 무엇을 정의하는가"가 import 문에서 보이게 한다.
"""
