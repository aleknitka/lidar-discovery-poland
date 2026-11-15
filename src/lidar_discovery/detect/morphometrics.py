"""Per-candidate handcrafted features (09 §4.1 B, 11 Track B1).

Feature vector ~60 dims per candidate, computed from the 6-channel stack
inside the footprint + a ring. Used by LightGBM re-ranker.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import ndimage

from lidar_discovery.processing.dtm import Grid


def _stats(a: np.ndarray) -> dict[str, float]:
    vals = a[np.isfinite(a)]
    if not len(vals):
        return {"mean": 0, "max": 0, "min": 0, "std": 0, "p95": 0}
    return {
        "mean": float(np.mean(vals)),
        "max": float(np.max(vals)),
        "min": float(np.min(vals)),
        "std": float(np.std(vals)),
        "p95": float(np.percentile(vals, 95)),
    }


def _ring(mask: np.ndarray, width: int = 3) -> np.ndarray:
    dilated = ndimage.binary_dilation(mask, iterations=width)
    return dilated & ~mask


def _footprint_mask(
    shape: tuple[int, int], cand: dict[str, Any], grid: Grid
) -> np.ndarray:
    """Build a boolean footprint mask for one candidate."""
    h, w = shape
    mask = np.zeros((h, w), dtype=bool)
    rc = cand.get("centroid_rc")
    if rc is None:
        return mask
    # area -> radius estimate if regionprops not stored
    area_m2 = float(cand.get("area_m2", 10))
    r_m = math.sqrt(area_m2 / math.pi)
    r_px = max(2, round(r_m / grid.res))
    rr, cc = int(round(rc[0])), int(round(rc[1]))
    # draw disk
    y, x = np.ogrid[:h, :w]
    mask |= (y - rr) ** 2 + (x - cc) ** 2 <= r_px * r_px
    # prefer bbox if available
    bbox = cand.get("bbox_rc")
    if bbox is not None and len(bbox) == 4:
        r0, c0, r1, c1 = (int(v) for v in bbox)
        r0, c0 = max(0, r0), max(0, c0)
        r1, c1 = min(h, r1), min(w, c1)
        if r1 > r0 and c1 > c0:
            bmask = np.zeros_like(mask)
            bmask[r0:r1, c0:c1] = True
            # intersection of disk and bbox keeps shape realistic
            mask &= bmask
            if not mask.any():
                mask[r0:r1, c0:c1] = True
    # polyline candidates: dilate line
    poly = cand.get("polyline_rc")
    if poly:
        pl_mask = np.zeros_like(mask)
        for pr, pc in poly:
            pr, pc = int(pr), int(pc)
            if 0 <= pr < h and 0 <= pc < w:
                pl_mask[pr, pc] = True
        pl_mask = ndimage.binary_dilation(pl_mask, iterations=2)
        mask |= pl_mask
    return mask


def features_for_candidate(
    arrays: dict[str, np.ndarray], cand: dict[str, Any], grid: Grid
) -> dict[str, float]:
    """Feature dict for one candidate."""
    h, w = next(iter(arrays.values())).shape
    mask = _footprint_mask((h, w), cand, grid)
    ring = _ring(mask, width=3)
    feats: dict[str, float] = {}
    # geometry
    feats["area_m2"] = float(cand.get("area_m2", 0))
    feats["circularity"] = float(cand.get("circularity", 0))
    feats["rectangularity"] = float(cand.get("rectangularity", 0))
    feats["eccentricity"] = float(cand.get("eccentricity", 0))
    feats["length_m"] = float(cand.get("length_m", 0))
    feats["depth_max"] = float(cand.get("depth_max", 0))
    feats["depth_mean"] = float(cand.get("depth_mean", 0))
    feats["lrm_mean"] = float(cand.get("lrm_mean", 0))
    feats["support_fraction"] = float(cand.get("support_fraction", 1))
    feats["low_support"] = float(1 if cand.get("low_support") else 0)
    # per-channel stats inside footprint and ring
    for key in ("lrm", "lrm5", "lrm20", "svf", "slope", "fill_depth", "hillshade"):
        arr = arrays.get(key)
        if arr is None:
            continue
        s_in = _stats(arr[mask] if mask.any() else np.array([], np.float32))
        s_ring = _stats(arr[ring] if ring.any() else np.array([], np.float32))
        pfx = key.replace(" ", "_")
        feats[f"{pfx}_in_mean"] = s_in["mean"]
        feats[f"{pfx}_in_max"] = s_in["max"]
        feats[f"{pfx}_in_std"] = s_in["std"]
        feats[f"{pfx}_ring_mean"] = s_ring["mean"]
        feats[f"{pfx}_contrast"] = float(s_in["mean"] - s_ring["mean"])
    # fill_depth profile extras
    fd = arrays.get("fill_depth")
    if fd is not None and mask.any():
        vals = fd[mask]
        vals = vals[np.isfinite(vals)]
        if len(vals):
            feats["fill_volume_proxy"] = float(np.sum(vals) * grid.res * grid.res)
            feats["fill_p95"] = float(np.percentile(vals, 95))
    # neighbourhood: count of other candidates not needed here (per-patch feature)
    return feats


def features_for_candidates(
    arrays: dict[str, np.ndarray], cands: list[dict[str, Any]], grid: Grid
) -> list[dict[str, float]]:
    return [features_for_candidate(arrays, c, grid) for c in cands]


def feature_names() -> list[str]:
    """Canonical feature name order (for GBM). Built from a dummy call."""
    dummy_grid = Grid(0, 10, 0.5, 20, 20)
    dummy_arrays = {
        "lrm": np.zeros((20, 20), np.float32),
        "lrm5": np.zeros((20, 20), np.float32),
        "svf": np.full((20, 20), 0.9, np.float32),
        "slope": np.zeros((20, 20), np.float32),
        "fill_depth": np.zeros((20, 20), np.float32),
        "hillshade": np.full((20, 20), 0.5, np.float32),
    }
    dummy_cand = {
        "area_m2": 10,
        "circularity": 0.5,
        "rectangularity": 0.7,
        "centroid_rc": (10, 10),
        "bbox_rc": (8, 8, 12, 12),
    }
    feats = features_for_candidate(dummy_arrays, dummy_cand, dummy_grid)
    return sorted(feats.keys())
