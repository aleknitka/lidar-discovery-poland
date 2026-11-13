"""local-laz: a folder of LAS/LAZ files (header bounds are read, nothing is executed)."""

from __future__ import annotations

import os
from pathlib import Path

import laspy
from shapely.geometry import Polygon, box

from lidar_discovery.config import Settings
from lidar_discovery.sources.base import TileRef, register_source


@register_source("local-laz")
class LocalLazSource:
    id = "local-laz"
    name = "Local LAS/LAZ folder"
    description = "Files in $LDP_LOCAL_LAZ_DIR (default <data_dir>/local). CRS assumed EPSG:2180."
    crs_h = None

    def __init__(self, settings: Settings, folder: Path | None = None) -> None:
        self.settings = settings
        env = os.environ.get("LDP_LOCAL_LAZ_DIR")
        self.folder = Path(folder or env or settings.data_dir / "local")

    def list_tiles(self, aoi_2180: Polygon, years: list[int] | None = None) -> list[TileRef]:
        tiles: list[TileRef] = []
        if not self.folder.is_dir():
            return tiles
        for p in sorted([*self.folder.glob("*.laz"), *self.folder.glob("*.las")]):
            with laspy.open(p) as fh:
                h = fh.header
                bbox = (float(h.x_min), float(h.y_min), float(h.x_max), float(h.y_max))
                year = h.creation_date.year if h.creation_date else None
                npts = h.point_count
            if years and year not in years:
                continue
            if not box(*bbox).intersects(aoi_2180):
                continue
            area = max((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]), 1.0)
            tiles.append(
                TileRef(
                    source_id=self.id,
                    tile_id=p.stem,
                    godlo=p.stem,
                    year=year,
                    nominal_density=f"{npts / area:.1f} p/m2",
                    bbox_2180=bbox,
                    url=str(p),
                    crs_h=self.crs_h,
                    size_bytes=p.stat().st_size,
                )
            )
        return tiles

    def download(self, tile: TileRef, dest_dir: Path) -> Path:
        return Path(tile.url)  # already local; processing reads it in place
