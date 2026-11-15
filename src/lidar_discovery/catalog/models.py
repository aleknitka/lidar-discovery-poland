"""SQLModel tables. Geometry is stored as GeoJSON text (WGS84)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Field, SQLModel

MORPH_CLASSES = (
    "house_platform",
    "cellar_pit",
    "terrace",
    "holloway",
    "field_boundary",
    "cemetery",
    "church_site",
    "other",
)
REALITY = ("unassessed", "artefact", "natural", "anthropogenic")
ORIGINS = ("manual", "rule", "ml", "vlm")
REVIEW_STATUSES = ("proposed", "accepted", "rejected", "needs_second_opinion")
DISCLOSURES = ("public", "generalised", "restricted")
LOCATION_KINDS = ("village", "area")
JOB_STATES = (
    "queued",
    "listing",
    "downloading",
    "processing",
    "done",
    "failed",
    "cancelled",
)
ACTIVE_JOB_STATES = ("queued", "listing", "downloading", "processing")
PRODUCT_KINDS = ("dtm", "hillshade", "slope", "svf", "lrm", "ground_density")


def utcnow() -> datetime:
    return datetime.now(UTC)


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


class Location(SQLModel, table=True):
    id: str = Field(primary_key=True)  # slug
    names: str = "{}"  # JSON {pl, uk, other}
    lon: float
    lat: float
    polygon: str | None = None  # GeoJSON geometry text (WGS84)
    aoi_buffer_m: float = 1000.0
    depopulation: str = "{}"  # JSON {year, cause, source_url}
    provenance: str = "[]"  # JSON list of {provider, ref, fetched_at}
    disclosure: str = "public"
    notes: str | None = None
    kind: str = "village"  # 'village' | 'area' (areas are created by "Get data for this view")


class Product(SQLModel, table=True):
    id: str = Field(primary_key=True)
    location_id: str = Field(index=True)
    source_id: str
    epoch: int
    kind: str
    path: str  # COG path relative to data_dir
    resolution_m: float
    bounds_wgs84: str  # JSON [w, s, e, n]
    crs_h: str | None = None
    provenance: str = "{}"
    created_at: datetime = Field(default_factory=utcnow)


class Candidate(SQLModel, table=True):
    id: str = Field(primary_key=True)
    location_id: str | None = Field(default=None, index=True)
    geometry: str  # GeoJSON geometry text (WGS84)
    morph_class: str = "other"
    reality: str = "unassessed"
    reality_confidence: float = 0.0
    dating_evidence: str = "{}"  # JSON {text, sources[]}
    documentation_status: str = "[]"  # JSON list of {source, ref, found}
    origin: str = "manual"
    model_version: str | None = None
    review_status: str = "proposed"
    reviewer_notes: str = ""
    disclosure: str = "public"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class TileCache(SQLModel, table=True):
    """Cache of remote (WFS) responses keyed by request signature."""

    key: str = Field(primary_key=True)
    payload: str
    fetched_at: datetime = Field(default_factory=utcnow)


class Job(SQLModel, table=True):
    """A background job (v0: `fetch-area`). Progress is persisted so the UI survives reloads."""

    id: str = Field(primary_key=True)
    kind: str = "fetch-area"
    params: str = "{}"  # JSON
    state: str = Field(default="queued", index=True)
    bytes_done: int = 0
    bytes_total: int = 0
    tiles_done: int = 0
    tiles_total: int = 0
    current_item: str | None = None
    tiles: str = "[]"  # JSON list of {godlo, name, status, bytes, size_bytes, footprint}
    step: int = 0
    steps: int = 0
    step_name: str | None = None
    speed_bps: float | None = None
    message: str | None = None
    error: str | None = None
    location_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None
