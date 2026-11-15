"""Area-of-interest helpers: Location -> EPSG:2180 polygon."""

from __future__ import annotations

import json

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import Point, Polygon, shape

from lidar_discovery.catalog.models import Location

_to_2180 = Transformer.from_crs(4326, 2180, always_xy=True)
_to_4326 = Transformer.from_crs(2180, 4326, always_xy=True)


def _reproject(geom, tr: Transformer):
    def fn(coords: np.ndarray) -> np.ndarray:
        x, y = tr.transform(coords[:, 0], coords[:, 1])
        return np.column_stack([x, y])

    return shapely.transform(geom, fn)


def to_2180(geom):
    return _reproject(geom, _to_2180)


def to_4326(geom):
    return _reproject(geom, _to_4326)


def location_aoi_2180(loc: Location, default_buffer_m: float = 1000.0) -> Polygon:
    """AOI = precinct polygon if present, else a point buffer (default 1000 m)."""
    if loc.polygon:
        g = to_2180(shape(json.loads(loc.polygon)))
        return g if g.geom_type == "Polygon" else g.convex_hull
    x, y = _to_2180.transform(loc.lon, loc.lat)
    return Point(x, y).buffer(loc.aoi_buffer_m or default_buffer_m)


def aoi_for(loc: Location, mode: str = "auto", buffer_m: float | None = None) -> Polygon:
    """mode 'auto': polygon if present else point buffer; 'point': always a point buffer."""
    if mode == "point" or not loc.polygon:
        x, y = _to_2180.transform(loc.lon, loc.lat)
        return Point(x, y).buffer(buffer_m or loc.aoi_buffer_m or 1000.0)
    return location_aoi_2180(loc)
