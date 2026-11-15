"""XYZ tile rendering from COGs (rio-tiler), greyscale ramp per kind + viridis heatmap."""

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
DEFAULT_RANGES: dict[str, tuple[float, float]] = {
    "hillshade": (0.0, 1.0),
    "slope": (0.0, 45.0),
    "svf": (0.7, 1.0),
    "lrm": (-1.0, 1.0),
    "ground_density": (0.0, 8.0),
    "dtm": (0.0, 1000.0),
    "anomaly": (0.0, 1.0),
    "heatmap": (0.0, 1.0),
    "preview": (0.0, 1.0),
}
# Elevation (DTM) is drawn with a muted hypsometric ramp, stretched over the area's own 1st-99th
# percentile (provenance.display_range) so relief is visible whatever the absolute height is.
DTM_RAMP = np.array(
    [
        [0.00, 52, 78, 96],
        [0.25, 96, 140, 110],
        [0.50, 198, 190, 130],
        [0.75, 168, 124, 84],
        [1.00, 245, 240, 235],
    ],
    dtype="float32",
)
# Viridis-ish ramp for anomaly heatmaps: 0=dark purple -> 1=yellow.
VIRIDIS_RAMP = np.array(
    [
        [0.00, 68, 1, 84],
        [0.25, 59, 82, 139],
        [0.50, 33, 145, 140],
        [0.75, 94, 201, 98],
        [1.00, 253, 231, 37],
    ],
    dtype="float32",
)
ANOMALY_KINDS = {"anomaly", "heatmap", "preview"}
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


def _viridis(t: np.ndarray) -> np.ndarray:
    r = np.interp(t, VIRIDIS_RAMP[:, 0], VIRIDIS_RAMP[:, 1])
    g = np.interp(t, VIRIDIS_RAMP[:, 0], VIRIDIS_RAMP[:, 2])
    b = np.interp(t, VIRIDIS_RAMP[:, 0], VIRIDIS_RAMP[:, 3])
    return np.dstack([r, g, b]).astype("uint8")


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
    colormap: str | None = None,
) -> bytes:
    """Return PNG bytes for tile z/x/y; a fully transparent tile outside the raster.

    `shade` (0..1, DTM only) blends a hillshade into the elevation colours.
    `colormap` forces a ramp for anomaly heatmaps: viridis (default), grey.
    """
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
    # heatmap / anomaly: viridis with alpha fading in from 0, transparent below 0.06
    if kind in ANOMALY_KINDS or colormap in ("viridis", "grey", "gray", "inferno"):
        if kind in ANOMALY_KINDS:
            if colormap in (None, "viridis"):
                rgb = _viridis(scaled)
            elif colormap in ("grey", "gray"):
                grey = (scaled * 255).astype("uint8")
                rgb = np.dstack([grey, grey, grey])
            else:
                rgb = _colour_ramp(scaled, DTM_RAMP)
            a = np.where(valid, (np.clip((scaled - 0.04) / 0.96, 0, 1) * 220).astype("uint8"), 0)
            a = np.where(scaled < 0.06, 0, a).astype("uint8")
            buf = io.BytesIO()
            Image.fromarray(np.dstack([rgb, a]), "RGBA").save(buf, "PNG")
            return buf.getvalue()
    if kind == "dtm":
        rgb = _colour_ramp(scaled, DTM_RAMP).astype("float32")
        if shade > 0:
            b = img.bounds
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
