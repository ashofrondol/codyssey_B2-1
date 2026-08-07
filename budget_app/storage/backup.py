"""데이터 폴더 백업.

서비스가 아니라 저장소 계층에 있는 이유: 도메인 판단이 전혀 없고 데이터
디렉터리의 파일을 다루는 일이다. ``now`` 를 주입 가능하게 둔 것은 테스트에서
결과 경로를 예측할 수 있게 하기 위해서다.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from . import config


def backup_data_dir(data_dir: Path, now: Optional[datetime] = None) -> Path:
    """data 폴더의 모든 ``*.jsonl`` 을 타임스탬프 폴더로 복사한다.

    서비스가 아니라 저장소 계층에 있는 이유: 도메인 판단이 전혀 없고 데이터
    디렉터리의 파일을 다루는 일이다. ``now`` 를 주입 가능하게 둔 이유: 이전에는
    ``datetime.now()`` 를 직접 불러서 시간을 고정하지 않으면 결과 경로를 검증할
    수 없었다.
    """
    src = Path(data_dir)
    if not src.exists():
        raise FileNotFoundError(str(src))
    ts = (now or datetime.now()).strftime(config.BACKUP_TS_FORMAT)
    dest = src.parent / f"{config.BACKUP_DIR_PREFIX}{ts}"
    dest.mkdir(parents=True, exist_ok=False)
    for p in _files_to_copy(src):
        (dest / p.name).write_bytes(p.read_bytes())
    return dest


def _files_to_copy(src: Path) -> Iterator[Path]:
    """백업 대상 — ``*.jsonl`` 과, glob 에 걸리지 않지만 데이터인 파일들.

    ``id_counter`` 를 빠뜨리면 백업을 복원했을 때 "발급한 적 있는 번호" 기록이
    사라져 삭제된 id 재사용 버그가 되살아난다. 확장자가 없다는 이유로 데이터가
    아닌 것은 아니다.
    """
    yield from src.glob(config.BACKUP_GLOB)
    for name in config.BACKUP_EXTRA_FILES:
        extra = src / name
        if extra.is_file():
            yield extra
