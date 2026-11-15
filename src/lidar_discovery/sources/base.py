"""LidarSource protocol, TileRef and the plugin registry."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel
from shapely.geometry import Polygon

from lidar_discovery.config import Settings


class TileRef(BaseModel):
    source_id: str
    tile_id: str
    godlo: str | None = None
    year: int | None = None
    acq_date: str | None = None
    nominal_density: str | None = None  # e.g. "4 p/m2"
    bbox_2180: tuple[float, float, float, float]  # minx(E), miny(N), maxx(E), maxy(N)
    url: str  # remote URL or local path
    crs_h: str | None = None
    size_bytes: int | None = None
    footprint_wkt: str | None = None  # EPSG:2180 footprint when finer than the bbox


@runtime_checkable
class LidarSource(Protocol):
    id: str
    name: str
    description: str
    crs_h: str | None

    def list_tiles(self, aoi_2180: Polygon, years: list[int] | None = None) -> list[TileRef]: ...

    def download(self, tile: TileRef, dest_dir: Path) -> Path: ...


SourceFactory = Callable[[Settings], LidarSource]
_REGISTRY: dict[str, SourceFactory] = {}


def register_source(source_id: str) -> Callable[[SourceFactory], SourceFactory]:
    """Class decorator: register a factory (usually the class itself, called with Settings)."""

    def deco(factory: SourceFactory) -> SourceFactory:
        _REGISTRY[source_id] = factory
        return factory

    return deco


def source_ids() -> list[str]:
    return sorted(_REGISTRY)


def get_source(source_id: str, settings: Settings) -> LidarSource:
    try:
        factory = _REGISTRY[source_id]
    except KeyError:
        raise KeyError(f"unknown source {source_id!r}; available: {source_ids()}") from None
    return factory(settings)
