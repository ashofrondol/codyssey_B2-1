"""도메인 계층 — 데이터의 모양과 규칙.

- ``models``     : 저장 엔티티(Transaction/Budget/Category) + 질의·결과 모델 + 기간 규칙
- ``validators`` : 필드 규칙의 단일 정의처 (규칙 하나 = 함수 하나)

이 패키지는 I/O 를 전혀 모른다. ``open``·``print``·``input`` 이 하나도 없으므로
파일 없이 단독으로 테스트할 수 있다.

**재수출하지 않는다.** ``from ..domain.models import Transaction`` 처럼 소유 모듈을
명시해 "어느 파일이 무엇을 정의하는가"가 import 문에서 보이게 한다.
"""
