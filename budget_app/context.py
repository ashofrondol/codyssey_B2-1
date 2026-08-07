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

from pathlib import Path

from .services.budgets import BudgetService
from .services.categories import CategoryService
from .services.importexport import ImportExportService
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
        self.txs = TransactionRepository(self.data_dir)
        self.cats = CategoryStore(self.data_dir)
        self.budgets = BudgetStore(self.data_dir)
        self.tx_service = TransactionService(self.txs, self.cats)
        self.cat_service = CategoryService(self.cats, self.txs)
        self.budget_service = BudgetService(self.txs, self.budgets)
        self.io_service = ImportExportService(self.txs, self.cats)

    def prepare(self) -> None:
        """데이터 폴더와 파일을 준비한다 — 명령 실행 전 한 번만."""
        self.txs.ensure_ready()
        self.budgets.ensure_ready()
        self.cats.ensure_ready()
        self.cats.seed_defaults()
