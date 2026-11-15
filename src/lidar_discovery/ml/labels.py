"""Label table + scan_cells (09 §3) + snapshot hashing."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Field, Session, SQLModel, select


def utcnow() -> datetime:
    return datetime.now(UTC)


class Label(SQLModel, table=True):
    """One labelled candidate (target/confuser/unsure)."""

    id: str = Field(primary_key=True)
    candidate_id: str = Field(index=True)
    morph_class: str = "other"
    label: str = "target"  # target | confuser | unsure
    confuser_class: str | None = None
    certainty: int = 2  # 1 possible, 2 probable, 3 clear
    geometry_kind: str = "point"
    views_used: str = "[]"
    informed_by: str = "none"
    label_source: str = "manual_scan"
    annotator_id: str = "unknown"
    annotated_at: datetime = Field(default_factory=utcnow)
    seconds_spent: float = 0.0
    scan_cell_id: str | None = None
    split_role: str = "train"  # train | dev | lockbox | eval_only
    sensitive: bool = False


class ScanCell(SQLModel, table=True):
    """100 m annotation cell completeness."""

    id: str = Field(primary_key=True)  # e.g. carynskie_500_600
    location_id: str = Field(index=True)
    x0: float  # EPSG:2180 west
    y0: float  # south
    size_m: float = 100.0
    complete: bool = False
    annotator_id: str | None = None
    annotated_at: datetime | None = None
    views: str = "[]"
    minutes_spent: float = 0.0


def label_snapshot_hash(session: Session) -> str:
    rows = list(session.exec(select(Label).order_by(Label.id)))
    blob = json.dumps(
        [{k: str(v) for k, v in r.model_dump().items()} for r in rows],
        sort_keys=True,
    )
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def label_counts(session: Session) -> dict[str, Any]:
    rows = list(session.exec(select(Label)))
    by_class: dict[str, int] = {}
    by_label: dict[str, int] = {}
    for r in rows:
        by_class[r.morph_class] = by_class.get(r.morph_class, 0) + 1
        by_label[r.label] = by_label.get(r.label, 0) + 1
    return {"total": len(rows), "by_class": by_class, "by_label": by_label}
