"""Slovak open ALS (ZBGIS, CC BY 4.0) - stub."""

from __future__ import annotations

from pathlib import Path

from shapely.geometry import Polygon

from lidar_discovery.config import Settings
from lidar_discovery.sources.base import TileRef, register_source


@register_source("sk-zbgis")
class SkZbgisSource:
    id = "sk-zbgis"
    name = "Slovak ZBGIS ALS"
    description = "Slovak open airborne LiDAR (CC BY 4.0). Not implemented yet."
    crs_h = "Bpv"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def list_tiles(self, aoi_2180: Polygon, years: list[int] | None = None) -> list[TileRef]:
        # TODO: query the ZBGIS / UGKK SR ALS tile index (EPSG:8353 / S-JTSK), reproject the
        # AOI from EPSG:2180, and return TileRefs. Needs the real index endpoint and licence check.
        raise NotImplementedError("sk-zbgis is a stub; see TODO in sources/zbgis.py")

    def download(self, tile: TileRef, dest_dir: Path) -> Path:
        raise NotImplementedError("sk-zbgis is a stub")
