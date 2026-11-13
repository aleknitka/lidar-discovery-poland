"""Cloud-optimised GeoTIFF writer (rasterio COG driver, tiled GTiff + overviews fallback)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.shutil import copy as rio_copy
from rasterio.transform import Affine

CRS_PL = "EPSG:2180"


def write_cog(
    path: Path,
    array: np.ndarray,
    transform: Affine,
    nodata: float = -9999.0,
    resampling: str = "average",
    crs: str = CRS_PL,
) -> Path:
    """Write a single-band float32 raster; NaN in `array` becomes `nodata`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.where(np.isnan(array), nodata, array).astype(np.float32)
    profile = {
        "driver": "GTiff",
        "height": data.shape[0],
        "width": data.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "nodata": nodata,
    }
    tmp = path.with_name(path.name + ".tmp")
    with MemoryFile() as mem:
        with mem.open(**profile) as ds:
            ds.write(data, 1)
        try:
            rio_copy(
                mem.name,
                str(tmp),
                driver="COG",
                COMPRESS="DEFLATE",
                PREDICTOR="3",
                BLOCKSIZE="512",
                OVERVIEW_RESAMPLING=resampling.upper(),
            )
        except Exception:  # COG driver unavailable -> tiled GTiff + overviews
            with rasterio.open(
                tmp,
                "w",
                **profile,
                tiled=True,
                blockxsize=256,
                blockysize=256,
                compress="deflate",
                predictor=3,
            ) as ds:
                ds.write(data, 1)
                ds.build_overviews([2, 4, 8, 16], Resampling[resampling])
    tmp.replace(path)
    return path
