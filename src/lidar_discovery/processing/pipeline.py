"""End-to-end: ground points -> DTM -> visualisations -> COGs -> Product rows."""

from __future__ import annotations

import contextlib
import hashlib
import json
import subprocess
import time
from collections.abc import Callable, Iterable
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
from lidar_discovery.processing.dtm import Grid, grid_dtm, ground_density, point_counts
from lidar_discovery.processing.points import read_ground

PIPELINE_VERSION = "1"  # bump when outputs change; part of the area processing cache key

DISPLAY_RANGES = {
    "hillshade": [0.0, 1.0],
    "slope": [0.0, 45.0],
    "svf": [0.7, 1.0],
    "lrm": [-1.0, 1.0],
    "ground_density": [0.0, 8.0],
}


# Every product kind the pipeline can build, in processing order. The DTM is the input of all
# the others, so it is always built (or reused).
ALL_KINDS: tuple[str, ...] = ("dtm", "hillshade", "slope", "svf", "lrm", "ground_density")
DEFAULT_LAYERS: tuple[str, ...] = ("dtm", "hillshade", "svf", "ground_density")
VIS_KINDS: tuple[str, ...] = ("hillshade", "slope", "svf", "lrm")


# Measured on this laptop (Windows, 2026-11), 1 sheet of ~4.4 M ground points per 2 km2:
#   2.0 km2: read points 1.3 s, DTM 40.7 s, hillshade 1.2 s, slope 0.7 s, SVF 4.4 s, LRM 1.2 s,
#            each COG write 1.0-1.5 s
#   0.48 km2 (2 sheets): read points 2.1 s, DTM 23.4 s, SVF 0.9 s, hillshade 0.2 s, LRM 0.3 s,
#            each COG write 0.3-0.5 s
# The DTM has a large fixed cost (Delaunay set-up), so it is modelled as fixed + per km2; the other
# kinds scale with area. Used only for the UI estimate; real times vary with density and CPU.
SECONDS_PER_KM2 = {
    "dtm": 11.3,
    "hillshade": 0.6,
    "slope": 0.35,
    "svf": 2.2,
    "lrm": 0.6,
    "ground_density": 0.15,
}
FIXED_S = {"dtm": 18.0}
WRITE_S_PER_KM2 = 0.55
WRITE_S_FIXED = 0.2
READ_S_PER_SHEET = 1.5


def estimate_processing_s(
    area_km2: float, kinds: Iterable[str], sheets: int, from_dtm: bool = False
) -> dict[str, float]:
    """Estimated processing seconds per kind (compute + COG write), plus "points" (reading the
    LAZ) and "total". LAZ download time is NOT included. With `from_dtm` the DTM is not rebuilt."""
    out: dict[str, float] = {}
    for k in kinds:
        if k == "dtm" and from_dtm:
            continue
        out[k] = round(
            FIXED_S.get(k, 0.0)
            + SECONDS_PER_KM2[k] * area_km2
            + WRITE_S_PER_KM2 * area_km2
            + WRITE_S_FIXED,
            1,
        )
    needs_points = (not from_dtm) or "ground_density" in out
    out["points"] = round(READ_S_PER_SHEET * sheets, 1) if needs_points and out else 0.0
    out["total"] = round(sum(out.values()), 1)
    return out


class LayerError(ValueError):
    """Unknown product kind requested (HTTP 422)."""


def normalise_layers(layers: str | Iterable[str] | None) -> tuple[str, ...]:
    """Validate a layer selection ("dtm,svf" or a list). The DTM is always included; the result
    is de-duplicated and in canonical order. None or empty means DEFAULT_LAYERS."""
    if layers is None:
        return DEFAULT_LAYERS
    items = [x.strip() for x in layers.split(",")] if isinstance(layers, str) else list(layers)
    items = [x for x in items if x]
    if not items:
        return DEFAULT_LAYERS
    bad = sorted({x for x in items if x not in ALL_KINDS})
    if bad:
        raise LayerError(f"unknown layer kind(s) {bad}; allowed: {list(ALL_KINDS)}")
    return tuple(k for k in ALL_KINDS if k == "dtm" or k in items)


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


def step_names(params: ProcessParams, from_dtm: bool = False) -> list[str]:
    """Names of the progress steps reported by `process_aoi` (in order)."""
    if from_dtm:
        names = ["ground points"] if "ground_density" in params.kinds else []
    else:
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


def _vis_jobs(dtm: np.ndarray, params: ProcessParams) -> dict[str, Callable[[], np.ndarray]]:
    return {
        "hillshade": lambda: vis.hillshade_multi(
            dtm, params.res, params.hillshade_dirs, params.sun_elevation_deg
        ),
        "slope": lambda: vis.slope_deg(dtm, params.res),
        "svf": lambda: vis.sky_view_factor(dtm, params.res, params.svf_radius_m, params.svf_dirs),
        "lrm": lambda: vis.local_relief_model(dtm, params.res, params.lrm_sigma_m),
    }


def _crop_and_mask(
    full: dict[str, np.ndarray],
    params: ProcessParams,
    aoi_grid: Grid,
    big: Grid,
    aoi_2180: Polygon,
) -> dict[str, np.ndarray]:
    """Crop arrays computed on the margin grid `big` to the AOI and mask outside the polygon."""
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
    return out


def _margin_grid(aoi_grid: Grid, params: ProcessParams) -> Grid:
    m = params.margin_m()
    minx, miny, maxx, maxy = aoi_grid.bounds
    return Grid.from_bounds((minx - m, miny - m, maxx + m, maxy + m), params.res)


def compute_products(
    pts: np.ndarray,
    aoi_2180: Polygon,
    params: ProcessParams,
    on_step: Callable[[str], None] | None = None,
) -> tuple[Grid, dict[str, np.ndarray], dict[str, float]]:
    """Pure computation. Returns the AOI grid, {kind: array cropped+masked to the AOI}, timings."""
    t: dict[str, float] = {}
    aoi_grid = Grid.from_bounds(aoi_2180.bounds, params.res)
    big = _margin_grid(aoi_grid, params)

    step = on_step or (lambda _name: None)
    step("dtm")
    t0 = time.perf_counter()
    dtm, counts = grid_dtm(pts, big, max_gap_m=params.max_gap_m, block=params.block)
    t["dtm"] = time.perf_counter() - t0
    full: dict[str, np.ndarray] = {"dtm": dtm}
    if "ground_density" in params.kinds:
        step("density")
        full["ground_density"] = ground_density(counts, params.res, params.density_window_m)
    for kind, fn in _vis_jobs(dtm, params).items():
        if kind in params.kinds:
            step(kind)
            t0 = time.perf_counter()
            full[kind] = fn()
            t[kind] = time.perf_counter() - t0
    return aoi_grid, _crop_and_mask(full, params, aoi_grid, big, aoi_2180), t


def read_cog_array(path: Path) -> np.ndarray:
    """Read band 1 of one of our float32 COGs; nodata becomes NaN."""
    import rasterio

    with rasterio.open(path) as ds:
        a = ds.read(1).astype(np.float32)
        if ds.nodata is not None:
            a[a == np.float32(ds.nodata)] = np.nan
    return a


def compute_from_dtm(
    dtm_aoi: np.ndarray,
    aoi_2180: Polygon,
    params: ProcessParams,
    pts: np.ndarray | None = None,
    on_step: Callable[[str], None] | None = None,
) -> tuple[Grid, dict[str, np.ndarray], dict[str, float]]:
    """Build the requested non-DTM kinds from an already computed DTM (cropped to the AOI).

    The DTM is edge-padded by the processing margin, so SVF/LRM values within ~30 m of the border
    differ slightly from a full run (which has real terrain there). `pts` (ground points) is only
    needed for ground_density, which is a point count and cannot be derived from the DTM."""
    t: dict[str, float] = {}
    step = on_step or (lambda _name: None)
    aoi_grid = Grid.from_bounds(aoi_2180.bounds, params.res)
    if dtm_aoi.shape != (aoi_grid.height, aoi_grid.width):
        raise RuntimeError("existing DTM does not match the requested area; rebuild all layers")
    big = _margin_grid(aoi_grid, params)
    c0 = round((aoi_grid.x0 - big.x0) / params.res)
    r0 = round((big.y1 - aoi_grid.y1) / params.res)
    pad = ((r0, big.height - aoi_grid.height - r0), (c0, big.width - aoi_grid.width - c0))
    dtm = np.pad(dtm_aoi, pad, mode="edge")
    full: dict[str, np.ndarray] = {}
    if "ground_density" in params.kinds:
        if pts is None:
            raise RuntimeError("ground points are required for ground_density")
        step("density")
        counts = point_counts(pts, big)
        full["ground_density"] = ground_density(counts, params.res, params.density_window_m)
    for kind, fn in _vis_jobs(dtm, params).items():
        if kind in params.kinds:
            step(kind)
            t0 = time.perf_counter()
            full[kind] = fn()
            t[kind] = time.perf_counter() - t0
    return aoi_grid, _crop_and_mask(full, params, aoi_grid, big, aoi_2180), t


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
    dtm_path: Path | None = None,
) -> ProcessResult:
    """on_step(name) is called as each stage in `step_names(params, dtm_path is not None)` starts
    (may raise to abort). With `dtm_path` (an existing DTM COG for this AOI, kinds must not include
    "dtm") only the other requested kinds are computed from it; points are read only if
    ground_density is requested."""
    params = params or ProcessParams()
    res = ProcessResult()
    step = on_step or (lambda _name: None)
    from_dtm = dtm_path is not None
    if from_dtm and "dtm" in params.kinds:
        raise ValueError("dtm_path given but 'dtm' is in params.kinds")
    pts = np.empty((0, 3))
    stats: dict[str, Any] = {}
    if not from_dtm or "ground_density" in params.kinds:
        step("ground points")
        t0 = time.perf_counter()
        m = params.margin_m() + 20.0  # margin + interpolation buffer
        minx, miny, maxx, maxy = aoi_2180.bounds
        pts, stats = read_ground(tile_paths, (minx - m, miny - m, maxx + m, maxy + m))
        res.timings["read_points"] = time.perf_counter() - t0
        if len(pts) < 100:
            raise RuntimeError(
                f"only {len(pts)} class-2 ground points inside the AOI from "
                f"{len(tile_paths)} file(s)"
            )
    if dtm_path is not None:
        grid, arrays, timings = compute_from_dtm(
            read_cog_array(dtm_path), aoi_2180, params, pts if len(pts) else None, on_step
        )
    else:
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
            if p.exists()  # incremental runs from an existing DTM may not need the sheets
        ],
        "point_stats": stats,
        "computed_from": "existing-dtm (edge-padded)" if from_dtm else "ground-points",
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
    prov_file = out_dir / "provenance.json"
    if from_dtm and prov_file.exists():  # keep the DTM run's record, append this run
        try:
            doc = json.loads(prov_file.read_text(encoding="utf-8"))
        except ValueError:
            doc = {}
        doc.setdefault("incremental_runs", []).append(
            {**base_prov, "kinds": list(arrays), "timings_s": res.timings}
        )
    else:
        doc = {**base_prov, "timings_s": res.timings}
    prov_file.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return res
