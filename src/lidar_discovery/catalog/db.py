"""Engine + session helpers."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from lidar_discovery.catalog import models  # noqa: F401  (register tables)
from lidar_discovery.config import Settings

_engines: dict[str, Engine] = {}
_lock = threading.Lock()


def _migrate(eng: Engine) -> None:
    """Tiny forward-only migrations for databases created by older versions."""
    loc_cols = {c["name"] for c in inspect(eng).get_columns("location")}
    if "kind" not in loc_cols:
        with eng.begin() as conn:
            conn.execute(
                text("ALTER TABLE location ADD COLUMN kind VARCHAR NOT NULL DEFAULT 'village'")
            )
    cand_cols = {c["name"] for c in inspect(eng).get_columns("candidate")}
    if "provenance" not in cand_cols:
        with eng.begin() as conn:
            conn.execute(text("ALTER TABLE candidate ADD COLUMN provenance VARCHAR DEFAULT '{}'"))


def get_engine(settings: Settings) -> Engine:
    key = str(settings.db_path.resolve())
    with _lock:  # first use may come from several threads at once
        eng = _engines.get(key)
        if eng is None:
            settings.ensure_dirs()
            eng = create_engine(
                f"sqlite:///{settings.db_path}",
                connect_args={"check_same_thread": False, "timeout": 30},
            )
            SQLModel.metadata.create_all(eng)
            _migrate(eng)
            _engines[key] = eng
    return eng


@contextmanager
def session_scope(settings: Settings) -> Iterator[Session]:
    with Session(get_engine(settings), expire_on_commit=False) as s:
        yield s
