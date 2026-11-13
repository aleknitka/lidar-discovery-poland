"""XYZ tile rendering from COGs (rio-tiler), greyscale ramp per kind."""

from __future__ import annotations

import io
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
# SVF reads best dark = enclosed; slope dark = flat is conventionally inverted (steep = dark).
INVERT = {"slope"}


@lru_cache(maxsize=1)
def transparent_tile() -> bytes:
    buf = io.BytesIO()
    Image.new("LA", (TILE, TILE), (0, 0)).save(buf, "PNG")
    return buf.getvalue()


def render_tile(
    path: Path, kind: str, display_range: tuple[float, float] | None, z: int, x: int, y: int
) -> bytes:
    """Return PNG bytes for tile z/x/y; a fully transparent tile outside the raster."""
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
    if kind in INVERT:
        scaled = 1.0 - scaled
    grey = (scaled * 255).astype("uint8")
    alpha = np.where(valid, 255, 0).astype("uint8")
    buf = io.BytesIO()
    Image.fromarray(np.dstack([grey, alpha]), "LA").save(buf, "PNG")
    return buf.getvalue()
