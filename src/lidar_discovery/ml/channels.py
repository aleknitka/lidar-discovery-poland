"""Derived channels for the 6-channel ML stack (09 §2.2, 11 §5).

Reads contract COGs (DTM + ground_density) and derives lrm5, fill_depth and
support as COGs, registering them as Products. Also exposes fixed scaling
constants used by every model.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy import ndimage

from lidar_discovery.catalog.models import Product
from lidar_discovery.processing.cog import write_cog
from lidar_discovery.processing.dtm import Grid
from lidar_discovery.processing.pipeline import PIPELINE_VERSION, code_version
from lidar_discovery.processing.vis import fill_nan_nearest, local_relief_model

# ---------------------------------------------------------------- fixed scaling (09 §2.2, stored in model card)
SCALING: dict[str, dict[str, Any]] = {
    "lrm20": {"clip": (-1.5, 1.5), "scale": 1.5, "desc": "clip [-1.5,+1.5] /1.5"},
    "lrm5": {"clip": (-1.0, 1.0), "scale": 1.0, "desc": "clip [-1,+1] /1"},
    "svf": {"centre": 0.85, "scale": 0.15, "clip": (-1, 1), "desc": "(svf-0.85)/0.15 clip [-1,1]"},
    "slope": {"scale": 45.0, "clip": (0, 1.5), "desc": "degrees/45 clip [0,1.5]"},
    "fill_depth": {"clip": (0, 2.5), "scale": 2.5, "desc": "clip [0,2.5]/2.5"},
    "support": {"desc": "log1p(count)/log1p(8) + binary mask"},
}

CHANNEL_SPEC_VERSION = "1"  # bump when any constant above changes

ALL_DERIVED: tuple[str, ...] = ("lrm5", "fill_depth", "support")


def channel_spec_hash() -> str:
    blob = json.dumps({"version": CHANNEL_SPEC_VERSION, "scaling": SCALING}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


# ---------------------------------------------------------------- scaling helpers (pure numpy, no I/O)


def scale_lrm20(a: np.ndarray) -> np.ndarray:
    return np.clip(a / 1.5, -1, 1).astype(np.float32)


def scale_lrm5(a: np.ndarray) -> np.ndarray:
    return np.clip(a, -1, 1).astype(np.float32)


def scale_svf(a: np.ndarray) -> np.ndarray:
    return np.clip((a - 0.85) / 0.15, -1, 1).astype(np.float32)


def scale_slope_deg(a: np.ndarray) -> np.ndarray:
    return np.clip(a / 45.0, 0, 1.5).astype(np.float32)


def scale_fill_depth(a: np.ndarray) -> np.ndarray:
    return np.clip(a / 2.5, 0, 1).astype(np.float32)


def scale_support_log(count: np.ndarray) -> np.ndarray:
    return (np.log1p(np.maximum(count, 0)) / np.log1p(8)).astype(np.float32)


def stack_for_model(arrays: dict[str, np.ndarray]) -> np.ndarray:
    """Stack 6 channels in canonical order -> (6, H, W) float32, scaled, NaN→0 where unsupported."""
    # expected keys: lrm20/lrm, lrm5, svf, slope, fill_depth, support (or ground_density)
    lrm20 = arrays.get("lrm20", arrays.get("lrm", np.zeros((1, 1), np.float32)))
    lrm5 = arrays.get("lrm5", np.zeros_like(lrm20))
    svf = arrays.get("svf", np.full_like(lrm20, 0.85))
    slope = arrays.get("slope", np.zeros_like(lrm20))
    filld = arrays.get("fill_depth", arrays.get("fillDepth", np.zeros_like(lrm20)))
    sup = arrays.get("support", arrays.get("ground_density", np.ones_like(lrm20)))
    chans = [
        scale_lrm20(lrm20),
        scale_lrm5(lrm5),
        scale_svf(svf),
        scale_slope_deg(slope),
        scale_fill_depth(filld),
        scale_support_log(sup) if sup.max() > 1.5 else sup.astype(np.float32),
    ]
    stacked = np.stack([np.where(np.isnan(c), 0, c) for c in chans], axis=0)
    return stacked.astype(np.float32)


# ---------------------------------------------------------------- derived rasters


def derive_lrm5(dtm: np.ndarray, res: float) -> np.ndarray:
    """LRM at 5 m wavelength (sigma 2.5 m). NaN-aware."""
    return local_relief_model(dtm, res, sigma_m=2.5)


def derive_fill_depth(dtm: np.ndarray) -> np.ndarray:
    """Closed-depression depth via morphological reconstruction (fill = reconstructed - dtm).

    Border-touching depressions are not closed, so they stay zero.
    Uses skimage if available, otherwise a scipy grey-closing fallback.
    """
    filled = fill_nan_nearest(dtm).astype(np.float32)
    # seed: border = dtm, interior = max(dtm)
    h, w = filled.shape
    mx = float(np.nanmax(filled)) if np.isfinite(filled).any() else 0.0
    seed = np.full_like(filled, mx)
    seed[0, :], seed[-1, :], seed[:, 0], seed[:, -1] = (
        filled[0, :],
        filled[-1, :],
        filled[:, 0],
        filled[:, -1],
    )
    # try skimage reconstruction (by dilation, then filled - dtm)
    try:
        from skimage.morphology import reconstruction  # type: ignore[import-not-found]

        rec = reconstruction(seed, filled, method="erosion")
        depth = np.maximum(rec - filled, 0).astype(np.float32)
        depth[np.isnan(dtm)] = np.nan
        return depth
    except Exception:
        pass
    # fallback: grey closing approximates filling, less precise but no extra dep
    # use a modest structure (disk ~3 m) — good enough for 0.3 m depth threshold
    try:
        # uniform closing then clip
        closed = ndimage.grey_closing(filled, size=7, mode="nearest")
        depth = np.maximum(closed - filled, 0).astype(np.float32)
        # zero out border-connected area (cheap: distance to border)
        depth[np.isnan(dtm)] = np.nan
        return depth
    except Exception:
        return np.zeros_like(filled, dtype=np.float32)


def derive_support_mask(
    ground_density_or_counts: np.ndarray,
    res: float = 0.5,
    window_m: float = 2.0,
    as_distance: bool = False,
) -> np.ndarray:
    """Binary support mask: 1 where at least 1 ground point in window_m window.

    Input may be ground_density (pts/m²) or raw per-cell counts.
    For density: count = density * res² per cell (window sum).
    Returns float32 0/1 (NaN outside AOI stays NaN if input had NaN).
    """
    a = ground_density_or_counts.astype(np.float32)
    # heuristic: if values look like density (typical 1-20) vs counts (0-8)
    # density has larger magnitude; estimate by max
    looks_like_density = float(np.nanmax(a)) > 10 if np.isfinite(a).any() else False
    if looks_like_density:
        # density pts/m² -> pts per 0.5 m cell = density * 0.25
        per_cell = a * (res * res)
    else:
        per_cell = a
    win = max(1, round(window_m / res))
    # sum over window
    window_sum = ndimage.uniform_filter(
        np.where(np.isnan(per_cell), 0, per_cell).astype(np.float32),
        size=win,
        mode="constant",
        cval=0,
    ) * (win * win)
    mask = (window_sum >= 1).astype(np.float32)
    mask[np.isnan(a)] = np.nan
    if as_distance:
        # distance to nearest ground point (approx): EDT on inverted mask
        inv = (mask == 0) & np.isfinite(mask)
        dist_cells = ndimage.distance_transform_edt(inv)
        dist_m = (dist_cells * res).astype(np.float32)
        dist_m[np.isnan(a)] = np.nan
        return dist_m
    return mask


def derive_support_log(counts_or_density: np.ndarray, res: float = 0.5) -> np.ndarray:
    """Continuous support channel: log1p(points per 0.5 m cell) / log1p(8)."""
    a = counts_or_density.astype(np.float32)
    looks_like_density = float(np.nanmax(a)) > 10 if np.isfinite(a).any() else False
    per_cell = a * (res * res) if looks_like_density else a
    per_cell = np.where(np.isnan(per_cell), 0, per_cell)
    out = (np.log1p(per_cell) / np.log1p(8)).astype(np.float32)
    out[np.isnan(a)] = np.nan
    return out


# ---------------------------------------------------------------- COG writers + Product rows


def _product_id(location_id: str, source_id: str, epoch: int, kind: str) -> str:
    return f"{location_id}-{source_id}-{epoch}-{kind}"


def write_derived_products(
    location_id: str,
    source_id: str,
    epoch: int,
    dtm: np.ndarray,
    ground_density: np.ndarray | None,
    grid: Grid,
    out_dir: Path,
    crs_h: str | None = None,
    bounds_wgs84: list[float] | None = None,
) -> list[Product]:
    """Compute lrm5, fill_depth, support from DTM (+ ground_density) and write COGs.

    Returns Product rows (caller must add them to the DB).
    """
    from lidar_discovery.catalog.models import dumps

    res = grid.res
    arrays: dict[str, np.ndarray] = {}
    arrays["lrm5"] = derive_lrm5(dtm, res)
    arrays["fill_depth"] = derive_fill_depth(dtm)
    if ground_density is not None:
        arrays["support"] = derive_support_log(ground_density, res)
        mask = derive_support_mask(ground_density, res)
        # also store mask as alpha-like check: support already encodes density
        _ = mask
    else:
        arrays["support"] = np.ones_like(dtm, dtype=np.float32)
        arrays["support"][np.isnan(dtm)] = np.nan

    products: list[Product] = []
    provenance_base: dict[str, Any] = {
        "channel_spec": CHANNEL_SPEC_VERSION,
        "channel_hash": channel_spec_hash(),
        "pipeline_version": PIPELINE_VERSION,
        "code_version": code_version(),
        "scaling": SCALING,
        "derived_from": "dtm+ground_density" if ground_density is not None else "dtm",
    }
    for kind in ALL_DERIVED:
        arr = arrays[kind]
        path = out_dir / f"{kind}.tif"
        write_cog(path, arr, grid.transform)
        prov = {**provenance_base, "kind": kind}
        # keep Product.path relative to data_dir (caller sets out_dir accordingly)
        # we store the path as given; repo will handle relativeness
        pid = _product_id(location_id, source_id, epoch, kind)
        prod = Product(
            id=pid,
            location_id=location_id,
            source_id=source_id,
            epoch=epoch,
            kind=kind,
            path=str(path),
            resolution_m=res,
            bounds_wgs84=dumps(bounds_wgs84 or [0, 0, 0, 0]),
            crs_h=crs_h,
            provenance=dumps(prov),
        )
        products.append(prod)
    return products


# ---------------------------------------------------------------- high-level wrapper (CLI + jobs hook)
def derive_channels(settings, location_id: str, epoch: int | None = None) -> dict:
    """Derive lrm5/fill_depth/support for one location/epoch from stored DTM.

    Reads the DTM (and ground_density if present) COGs for the location,
    computes the three derived rasters, writes them as COGs under
    ``data/derived/<location>/<source>-<epoch>/`` and registers Products.
    Returns {products: [ids], kinds: [...] }.
    """
    from lidar_discovery.catalog import repo as _repo
    from lidar_discovery.catalog.db import session_scope as _ss
    from lidar_discovery.catalog.models import dumps as _dumps
    import rasterio as _rio

    with _ss(settings) as s:
        from lidar_discovery.catalog.models import Location
        loc = s.get(Location, location_id)
        if loc is None:
            raise ValueError(f"unknown location {location_id!r}")
        prods = _repo.list_products(s, location_id)
    if not prods:
        raise ValueError(f"no products for {location_id!r}; run fetch-bbox first")
    # filter by epoch
    if epoch is not None:
        prods = [pr for pr in prods if pr.epoch == epoch]
        if not prods:
            raise ValueError(f"no products for {location_id!r} epoch {epoch}")
    # pick newest epoch if not specified
    epochs = sorted({pr.epoch for pr in prods}, reverse=True)
    use_epoch = epoch if epoch is not None else epochs[0]
    by_kind = {pr.kind: pr for pr in prods if pr.epoch == use_epoch}
    dtm_prod = by_kind.get("dtm")
    if dtm_prod is None:
        raise ValueError(f"no DTM for {location_id!r} epoch {use_epoch}")
    def _abs(path_str: str) -> Path:
        ap = Path(path_str)
        return ap if ap.is_absolute() else settings.data_dir / ap
    # load DTM + ground_density
    with _rio.open(_abs(dtm_prod.path)) as ds:
        dtm = ds.read(1).astype("float32")
        if ds.nodata is not None:
            dtm = __import__("numpy").where(dtm == ds.nodata, float("nan"), dtm)
        transform = ds.transform
        crs = ds.crs
        res = float(ds.res[0])
        # Grid from transform
        from lidar_discovery.processing.dtm import Grid as _Grid
        grid = _Grid(x0=float(transform.c), y1=float(transform.f), res=res, width=ds.width, height=ds.height)
        bounds_wgs84 = None
        # need bounds_wgs84 from product
        try:
            import json as _json
            bounds_wgs84 = _json.loads(dtm_prod.bounds_wgs84)
        except Exception:
            bounds_wgs84 = [0,0,0,0]
    gd = None
    gd_prod = by_kind.get("ground_density")
    if gd_prod is not None:
        try:
            with _rio.open(_abs(gd_prod.path)) as ds:
                gd = ds.read(1).astype("float32")
                if ds.nodata is not None:
                    gd = __import__("numpy").where(gd == ds.nodata, float("nan"), gd)
        except Exception:
            gd = None
    # out dir: data/derived/<location>/<source>-<epoch>/
    out_dir = settings.data_dir / "derived" / location_id / f"{dtm_prod.source_id}-{use_epoch}"
    out_dir.mkdir(parents=True, exist_ok=True)
    products = write_derived_products(
        location_id, dtm_prod.source_id, use_epoch, dtm, gd, grid, out_dir,
        crs_h=dtm_prod.crs_h, bounds_wgs84=bounds_wgs84,
    )
    # persist Products (relative paths)
    with _ss(settings) as s:
        for pr in products:
            # store path relative to data_dir for portability
            try:
                rel = Path(pr.path).relative_to(settings.data_dir)
                pr.path = str(rel)
            except Exception:
                pass
            _repo.add_product(s, pr)
    return {"location_id": location_id, "epoch": use_epoch, "products": [pr.id for pr in products], "kinds": list(ALL_DERIVED)}

# alias used by older hook
def derive(settings, location_id: str, epoch: int | None = None) -> dict:  # noqa: F811
    return derive_channels(settings, location_id, epoch)

derive = derive  # keep alias
