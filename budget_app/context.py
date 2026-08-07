"""합성 루트 — 저장소와 서비스를 조립하는 단 하나의 지점.

## 왜 ``cli/`` 밖에 있나

``AppContext`` 는 저장소 3개와 서비스 4개를 엮을 뿐 **CLI 모듈을 하나도 참조하지
않는다.** 그런데 ``cli/app.py`` 안에 있으면, 나중에 웹 UI 를 붙일 때 웹이
``from .cli.app import AppContext`` 를 해야 한다 — 프레젠테이션이 다른 프레젠테이션을
import 하는 모양이 된다.

조립은 어느 계층의 일도 아니므로 루트에 둔다. CLI 든 웹이든 각자 이것을 받아 쓴다.

## 생성자와 ``prepare()`` 를 나눈 이유

"객체를 만드는 것"과 "환경을 준비하는 것"은 다른 일이다. 이전에는 저장소 생성자가
mkdir·touch·기본 카테고리 시딩까지 해서, 핸들러마다 컨텍스트를 새로 만드는 것만으로
부작용이 10번 일어났고 오타 난 ``--data-dir`` 도 조용히 폴더가 생겼다.
지금은 진입점이 한 번만 ``prepare()`` 를 호출한다.
"""

from __future__ import annotations

import errno
from pathlib import Path

from .services.budgets import BudgetService
from .services.categories import CategoryService
from .services.importexport import ImportExportService
from .services.maintenance import BackupService
from .services.transactions import TransactionService
from .storage.repositories import BudgetStore, CategoryStore, TransactionRepository


class AppContext:
    """저장소/서비스를 한 번에 조립해 핸들러로 전달한다.

    생성자는 **객체만 만든다.** 디스크를 건드리는 것은 ``prepare()`` 의 일이다.
    이전에는 저장소 생성자가 mkdir·touch·기본 카테고리 시딩까지 해서, 핸들러마다
    ``AppContext(...)`` 를 새로 만드는 것만으로 부작용이 10번 일어났고 오타 난
    ``--data-dir`` 도 조용히 폴더가 생겼다. 지금은 ``main()`` 이 한 번만 준비한다.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

        # 저장소는 비공개다 — 조립하는 데만 쓰고 밖으로 내보이지 않는다.
        # 공개해 두면 핸들러가 서비스를 건너뛰어 `ctx.cats.list_names()` 처럼
        # 부를 수 있고, 실제로 그런 자리가 있었다. 이름 앞의 밑줄 하나가
        # "이 계층은 서비스와만 말한다"를 코드로 강제한다.
        self._txs = TransactionRepository(self.data_dir)
        self._cats = CategoryStore(self.data_dir)
        self._budgets = BudgetStore(self.data_dir)

        self.tx_service = TransactionService(self._txs, self._cats)
        self.cat_service = CategoryService(self._cats, self._txs)
        self.budget_service = BudgetService(self._txs, self._budgets)
        self.io_service = ImportExportService(self._txs, self._cats)
        self.backup_service = BackupService(self.data_dir)

    def prepare(self) -> None:
        """데이터 폴더와 파일을 준비한다 — 명령 실행 전 한 번만."""
        self._require_usable_data_dir()
        self._txs.ensure_ready()
        self._budgets.ensure_ready()
        self._cats.ensure_ready()
        self._cats.seed_defaults()

    def _require_usable_data_dir(self) -> None:
        """``--data-dir`` 가 폴더가 아니면 **여기서** 원인을 말하고 멈춘다.

        이 검사가 없으면 저 아래 ``mkdir`` 이 ``FileExistsError`` 를 던지고, 사용자는
        "파일이 이미 있으므로 만들 수 없습니다" 라는 — 무엇을 잘못했는지 알 수 없는 —
        메시지를 받는다. 오류는 **원인을 아는 자리**에서 만들어야 한다. 여기가
        "이 경로는 데이터 폴더여야 한다"를 아는 유일한 자리다.

        ``NotADirectoryError`` 를 쓰는 이유: 이것은 값 오류가 아니라 환경 상태
        문제이므로 ``handle_errors`` 의 (3)번 부류로 흘러 종료 코드 3 이 된다.
        ``AppError`` 로 던지면 4번이 되어 "대상 없음"과 같은 코드가 돼 버린다.
        """
        if self.data_dir.exists() and not self.data_dir.is_dir():
            raise NotADirectoryError(errno.ENOTDIR, "not a directory", str(self.data_dir))
