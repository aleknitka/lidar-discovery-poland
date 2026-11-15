"""End-to-end: ground points -> DTM -> visualisations -> COGs -> Product rows."""

from __future__ import annotations

import contextlib
import hashlib
import json
import subprocess
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from rasterio import features
from shapely.geometry import Polygon, box

from lidar_discovery import __version__
from lidar_discovery.catalog.models import Product, dumps
from lidar_discovery.config import Settings
from lidar_discovery.locations.aoi import to_4326
from lidar_discovery.processing import vis
from lidar_discovery.processing.cog import write_cog
from lidar_discovery.processing.dtm import Grid, grid_dtm, ground_density
from lidar_discovery.processing.points import read_ground

PIPELINE_VERSION = "1"  # bump when outputs change; part of the area processing cache key

DISPLAY_RANGES = {
    "hillshade": [0.0, 1.0],
    "slope": [0.0, 45.0],
    "svf": [0.7, 1.0],
    "lrm": [-1.0, 1.0],
    "ground_density": [0.0, 8.0],
}


@dataclass
class ProcessParams:
    res: float = 0.5
    max_gap_m: float = 6.0
    hillshade_dirs: int = 16
    sun_elevation_deg: float = 35.0
    svf_dirs: int = 16
    svf_radius_m: float = 10.0
    lrm_sigma_m: float = 10.0
    density_window_m: float = 4.0
    block: int = 1024
    kinds: tuple[str, ...] = ("dtm", "ground_density", "hillshade", "slope", "svf", "lrm")

    def margin_m(self) -> float:
        return max(self.svf_radius_m, 3 * self.lrm_sigma_m) + 2 * self.res


def step_names(params: ProcessParams) -> list[str]:
    """Names of the progress steps reported by `process_aoi` (in order)."""
    names = ["ground points", "dtm"]
    if "ground_density" in params.kinds:
        names.append("density")
    names += [k for k in ("hillshade", "slope", "svf", "lrm") if k in params.kinds]
    names.append("write")
    return names


@dataclass
class ProcessResult:
    products: list[Product] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)
    arrays: dict[str, np.ndarray] = field(default_factory=dict)  # populated if keep_arrays


def code_version() -> str:
    sha = ""
    with contextlib.suppress(Exception):
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=Path(__file__).parent,
        ).stdout.strip()
    return f"lidar_discovery {__version__}" + (f"+{sha}" if sha else "")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_products(
    pts: np.ndarray,
    aoi_2180: Polygon,
    params: ProcessParams,
    on_step: Callable[[str], None] | None = None,
) -> tuple[Grid, dict[str, np.ndarray], dict[str, float]]:
    """Pure computation. Returns the AOI grid, {kind: array cropped+masked to the AOI}, timings."""
    t: dict[str, float] = {}
    aoi_grid = Grid.from_bounds(aoi_2180.bounds, params.res)
    m = params.margin_m()
    minx, miny, maxx, maxy = aoi_grid.bounds
    big = Grid.from_bounds((minx - m, miny - m, maxx + m, maxy + m), params.res)

    step = on_step or (lambda _name: None)
    step("dtm")
    t0 = time.perf_counter()
    dtm, counts = grid_dtm(pts, big, max_gap_m=params.max_gap_m, block=params.block)
    t["dtm"] = time.perf_counter() - t0
    full: dict[str, np.ndarray] = {"dtm": dtm}
    if "ground_density" in params.kinds:
        step("density")
        full["ground_density"] = ground_density(counts, params.res, params.density_window_m)
    jobs = {
        "hillshade": lambda: vis.hillshade_multi(
            dtm, params.res, params.hillshade_dirs, params.sun_elevation_deg
        ),
        "slope": lambda: vis.slope_deg(dtm, params.res),
        "svf": lambda: vis.sky_view_factor(dtm, params.res, params.svf_radius_m, params.svf_dirs),
        "lrm": lambda: vis.local_relief_model(dtm, params.res, params.lrm_sigma_m),
    }
    for kind, fn in jobs.items():
        if kind in params.kinds:
            step(kind)
            t0 = time.perf_counter()
            full[kind] = fn()
            t[kind] = time.perf_counter() - t0

    # crop to the AOI grid and mask outside the AOI polygon
    c0 = round((aoi_grid.x0 - big.x0) / params.res)
    r0 = round((big.y1 - aoi_grid.y1) / params.res)
    sl = (slice(r0, r0 + aoi_grid.height), slice(c0, c0 + aoi_grid.width))
    inside = features.geometry_mask(
        [aoi_2180],
        out_shape=(aoi_grid.height, aoi_grid.width),
        transform=aoi_grid.transform,
        invert=True,
    )
    out: dict[str, np.ndarray] = {}
    for kind, arr in full.items():
        if kind not in params.kinds:
            continue
        a = arr[sl].astype(np.float32).copy()
        a[~inside] = np.nan
        out[kind] = a
    return aoi_grid, out, t


def process_aoi(
    settings: Settings,
    location_id: str,
    aoi_2180: Polygon,
    source_id: str,
    year: int,
    tile_paths: list[Path],
    crs_h: str | None = None,
    params: ProcessParams | None = None,
    keep_arrays: bool = False,
    on_step: Callable[[str], None] | None = None,
    extra_provenance: dict[str, Any] | None = None,
) -> ProcessResult:
    """on_step(name) is called as each stage in `step_names(params)` starts (may raise to abort)."""
    params = params or ProcessParams()
    res = ProcessResult()
    step = on_step or (lambda _name: None)
    step("ground points")
    t0 = time.perf_counter()
    m = params.margin_m() + 20.0  # margin + interpolation buffer
    minx, miny, maxx, maxy = aoi_2180.bounds
    pts, stats = read_ground(tile_paths, (minx - m, miny - m, maxx + m, maxy + m))
    res.timings["read_points"] = time.perf_counter() - t0
    if len(pts) < 100:
        raise RuntimeError(
            f"only {len(pts)} class-2 ground points inside the AOI from {len(tile_paths)} file(s)"
        )
    grid, arrays, timings = compute_products(pts, aoi_2180, params, on_step)
    res.timings.update(timings)
    if keep_arrays:
        res.arrays = arrays

    out_dir = settings.derived_dir / location_id / f"{source_id}-{year}"
    w, s, e, n = to_4326(box(*grid.bounds)).bounds
    base_prov: dict[str, Any] = {
        "inputs": [
            {"file": p.name, "size_bytes": p.stat().st_size, "sha256": sha256_file(p)}
            for p in tile_paths
        ],
        "point_stats": stats,
        "parameters": {k: v for k, v in asdict(params).items() if k != "kinds"},
        "code_version": code_version(),
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "pipeline_version": PIPELINE_VERSION,
        **(extra_provenance or {}),
        "crs_xy": "EPSG:2180",
        "crs_h": crs_h,
        "note": (
            "Vertical datums differ between sources (KRON86 vs EVRF2007). Epochs are NOT "
            "co-registered and must not be differenced without that step."
        ),
    }
    step("write")
    for kind, arr in arrays.items():
        t1 = time.perf_counter()
        path = write_cog(out_dir / f"{kind}.tif", arr, grid.transform)
        res.timings[f"write_{kind}"] = time.perf_counter() - t1
        prov = dict(base_prov)
        valid = arr[~np.isnan(arr)]
        if kind == "dtm":
            prov["display_range"] = [
                float(np.percentile(valid, 1)),
                float(np.percentile(valid, 99)),
            ]
        else:
            prov["display_range"] = DISPLAY_RANGES[kind]
        prov["valid_fraction"] = float(valid.size / arr.size)
        res.products.append(
            Product(
                id=f"{location_id}-{source_id}-{year}-{kind}",
                location_id=location_id,
                source_id=source_id,
                epoch=year,
                kind=kind,
                path=path.relative_to(settings.data_dir).as_posix(),
                resolution_m=params.res,
                bounds_wgs84=json.dumps([w, s, e, n]),
                crs_h=crs_h,
                provenance=dumps(prov),
            )
        )
    (out_dir / "provenance.json").write_text(
        json.dumps({**base_prov, "timings_s": res.timings}, indent=2), encoding="utf-8"
    )
    return res
