"""Coverage: which tiles exist per source and year for an AOI (no download)."""

from __future__ import annotations

from typing import Any

from shapely.geometry import Polygon, box

from lidar_discovery.config import Settings
from lidar_discovery.locations.aoi import to_4326
from lidar_discovery.sources.base import TileRef, get_source


def group_tiles(tiles: list[TileRef]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int | None], list[TileRef]] = {}
    for t in tiles:
        groups.setdefault((t.source_id, t.year), []).append(t)
    out = []
    for (sid, year), ts in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        minx = min(t.bbox_2180[0] for t in ts)
        miny = min(t.bbox_2180[1] for t in ts)
        maxx = max(t.bbox_2180[2] for t in ts)
        maxy = max(t.bbox_2180[3] for t in ts)
        w, s, e, n = to_4326(box(minx, miny, maxx, maxy)).bounds
        out.append(
            {
                "source_id": sid,
                "year": year,
                "tiles": len(ts),
                "nominal_density": ", ".join(
                    sorted({t.nominal_density for t in ts if t.nominal_density})
                ),
                "crs_h": ts[0].crs_h,
                "bbox": [w, s, e, n],
            }
        )
    return out


def compute_coverage(
    settings: Settings,
    aoi_2180: Polygon,
    source_ids: list[str] | None = None,
    years: list[int] | None = None,
) -> tuple[list[TileRef], list[str]]:
    """Returns (tiles, errors). Per-source failures are reported, not raised."""
    tiles: list[TileRef] = []
    errors: list[str] = []
    for sid in source_ids or ["gugik-kron86", "gugik-evrf2007"]:
        try:
            tiles.extend(get_source(sid, settings).list_tiles(aoi_2180, years))
        except Exception as e:
            errors.append(f"{sid}: {e}")
    return tiles, errors
