"""운영 유스케이스 — 데이터 폴더 자체를 다루는 일.

엔티티 단위가 아니라 **폴더 단위**의 작업이라 다른 세 서비스 어디에도 속하지
않는다. 백업이 거래 서비스에 있으면 "거래를 다루는 곳"이 아니게 되고, 카테고리
서비스에 있으면 더 이상하다.

## 이 클래스가 얇은 것에 대하여

``create()`` 는 저장소 함수 한 줄을 부를 뿐이다. 그래도 두는 이유는 둘이다.

1. **의존 방향**. 이것이 없으면 CLI 핸들러가 ``from ..storage.backup import ...``
   으로 저장소를 직접 부른다. 다른 열두 명령이 전부 서비스를 거치는데 하나만
   질러가면, "CLI 는 서비스와만 말한다"는 규칙이 **규칙이 아니라 관습**이 된다.
   규칙은 예외가 하나 생기는 순간 검증할 수 없는 것이 된다.
2. **자랄 자리**. 보관 개수 제한, 백업 전 무결성 검사, 복원 같은 것이 생기면
   전부 여기로 온다. 지금 그것들이 없다는 사실이 나중에도 없을 것을 뜻하지 않는다.

얇은 위임을 감추지 않고 이렇게 적어 두는 편이, 나중에 "이 클래스 왜 있지?" 라는
질문에 답이 없는 것보다 낫다.
"""

from __future__ import annotations

from pathlib import Path

from ..storage.backup import backup_data_dir


class BackupService:
    """데이터 폴더를 타임스탬프 폴더로 복사한다."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

    def create(self) -> Path:
        """백업을 만들고 만들어진 폴더 경로를 돌려준다."""
        return backup_data_dir(self.data_dir)
