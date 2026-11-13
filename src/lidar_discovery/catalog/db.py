"""Engine + session helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from lidar_discovery.catalog import models  # noqa: F401  (register tables)
from lidar_discovery.config import Settings

_engines: dict[str, Engine] = {}


def get_engine(settings: Settings) -> Engine:
    key = str(settings.db_path.resolve())
    eng = _engines.get(key)
    if eng is None:
        settings.ensure_dirs()
        eng = create_engine(
            f"sqlite:///{settings.db_path}", connect_args={"check_same_thread": False}
        )
        SQLModel.metadata.create_all(eng)
        _engines[key] = eng
    return eng


@contextmanager
def session_scope(settings: Settings) -> Iterator[Session]:
    with Session(get_engine(settings), expire_on_commit=False) as s:
        yield s
