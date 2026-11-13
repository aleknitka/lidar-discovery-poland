"""Disclosure logic: hide restricted items, snap generalised geometry to a 1 km grid cell."""

from __future__ import annotations

import math
from typing import Any

from pyproj import Transformer
from shapely.geometry import shape

GRID_M = 1000.0
_to_2180 = Transformer.from_crs(4326, 2180, always_xy=True)
_to_4326 = Transformer.from_crs(2180, 4326, always_xy=True)

# Morphological classes whose default disclosure is "restricted".
RESTRICTED_BY_DEFAULT = {"cemetery"}


def default_disclosure(morph_class: str | None) -> str:
    return "restricted" if morph_class in RESTRICTED_BY_DEFAULT else "public"


def snap_point_to_grid(lon: float, lat: float, grid_m: float = GRID_M) -> tuple[float, float]:
    """Return the WGS84 centre of the grid cell (EPSG:2180) containing the point."""
    x, y = _to_2180.transform(lon, lat)
    cx = (math.floor(x / grid_m) + 0.5) * grid_m
    cy = (math.floor(y / grid_m) + 0.5) * grid_m
    return _to_4326.transform(cx, cy)


def generalise_geometry(geom: dict[str, Any], grid_m: float = GRID_M) -> dict[str, Any]:
    """Replace any geometry with a Point at the centre of the 1 km cell holding its centroid."""
    c = shape(geom).centroid
    lon, lat = snap_point_to_grid(c.x, c.y, grid_m)
    return {"type": "Point", "coordinates": [lon, lat]}


def visible(disclosure: str, public_mode: bool) -> bool:
    return not (public_mode and disclosure == "restricted")


def apply_to_feature(feature: dict[str, Any], public_mode: bool) -> dict[str, Any] | None:
    """Filter / generalise a GeoJSON Feature carrying properties.disclosure."""
    if not public_mode:
        return feature
    level = (feature.get("properties") or {}).get("disclosure", "public")
    if level == "restricted":
        return None
    if level == "generalised" and feature.get("geometry"):
        out = dict(feature)
        out["geometry"] = generalise_geometry(feature["geometry"])
        props = dict(out["properties"])
        props["generalised"] = True
        out["properties"] = props
        return out
    return feature
