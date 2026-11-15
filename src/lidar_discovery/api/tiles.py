"""XYZ tile rendering from COGs (rio-tiler), greyscale ramp per kind."""

from __future__ import annotations

import io
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image
from rio_tiler.errors import TileOutsideBounds
from rio_tiler.io import Reader

TILE = 256
DEFAULT_RANGES = {
    "hillshade": (0.0, 1.0),
    "slope": (0.0, 45.0),
    "svf": (0.7, 1.0),
    "lrm": (-1.0, 1.0),
    "ground_density": (0.0, 8.0),
    "dtm": (0.0, 1000.0),
}
# Elevation (DTM) is drawn with a muted hypsometric ramp, stretched over the area's own 1st-99th
# percentile (provenance.display_range) so relief is visible whatever the absolute height is.
DTM_RAMP = np.array(
    [
        [0.00, 52, 78, 96],  # low: deep blue-green
        [0.25, 96, 140, 110],  # green
        [0.50, 198, 190, 130],  # sand
        [0.75, 168, 124, 84],  # brown
        [1.00, 245, 240, 235],  # high: near white
    ],
    dtype="float32",
)
# SVF reads best dark = enclosed; slope dark = flat is conventionally inverted (steep = dark).
INVERT = {"slope"}


@lru_cache(maxsize=1)
def transparent_tile() -> bytes:
    buf = io.BytesIO()
    Image.new("LA", (TILE, TILE), (0, 0)).save(buf, "PNG")
    return buf.getvalue()


def _colour_ramp(t: np.ndarray, ramp: np.ndarray) -> np.ndarray:
    """Map 0..1 values to an (h, w, 3) uint8 image by linear interpolation along `ramp`."""
    return np.dstack(
        [np.interp(t, ramp[:, 0], ramp[:, c]) for c in (1, 2, 3)],
    ).astype("uint8")


def _shade(elev: np.ndarray, cell_m: float, azimuth_deg: float = 315.0, sun_deg: float = 40.0):
    """Single-direction hillshade (0..1) of a tile; edges use the nearest valid gradient."""
    e = np.where(np.isfinite(elev), elev, np.nanmean(elev) if np.isfinite(elev).any() else 0.0)
    dzdy, dzdx = np.gradient(e, cell_m)
    nx, ny, nz = -dzdx, dzdy, np.ones_like(dzdx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    az, el = math.radians(azimuth_deg), math.radians(sun_deg)
    lx, ly, lz = math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el)
    return np.clip((nx * lx + ny * ly + nz * lz) / norm, 0, 1)


def render_tile(
    path: Path,
    kind: str,
    display_range: tuple[float, float] | None,
    z: int,
    x: int,
    y: int,
    shade: float = 0.0,
) -> bytes:
    """Return PNG bytes for tile z/x/y; a fully transparent tile outside the raster.

    `shade` (0..1, DTM only) blends a hillshade into the elevation colours as a preview aid; the
    default 0 is plain elevation."""
    lo, hi = display_range or DEFAULT_RANGES.get(kind, (0.0, 1.0))
    if hi <= lo:
        hi = lo + 1e-6
    try:
        with Reader(str(path)) as src:
            img = src.tile(x, y, z, tilesize=TILE, resampling_method="bilinear")
    except TileOutsideBounds:
        return transparent_tile()
    data = np.ma.getdata(img.array[0]).astype("float32")
    valid = (np.ma.getmaskarray(img.array[0]) == 0) & np.isfinite(data) & (img.mask > 0)
    if not valid.any():
        return transparent_tile()
    scaled = np.clip((data - lo) / (hi - lo), 0.0, 1.0)
    alpha = np.where(valid, 255, 0).astype("uint8")
    if kind == "dtm":
        rgb = _colour_ramp(scaled, DTM_RAMP).astype("float32")
        if shade > 0:
            b = img.bounds  # Web Mercator metres; ground distance = mercator * cos(latitude)
            lat = math.atan(math.sinh(math.pi * (1 - 2 * (y + 0.5) / 2**z)))
            cell = (b[2] - b[0]) / TILE * math.cos(lat)
            lit = _shade(np.where(valid, data, np.nan), cell)
            k = 1.0 - min(max(shade, 0.0), 1.0) * (1.0 - lit / max(float(lit.max()), 1e-6))
            rgb = rgb * k[..., None]
        buf = io.BytesIO()
        Image.fromarray(np.dstack([rgb.clip(0, 255).astype("uint8"), alpha]), "RGBA").save(
            buf, "PNG"
        )
        return buf.getvalue()
    if kind in INVERT:
        scaled = 1.0 - scaled
    grey = (scaled * 255).astype("uint8")
    buf = io.BytesIO()
    Image.fromarray(np.dstack([grey, alpha]), "LA").save(buf, "PNG")
    return buf.getvalue()
