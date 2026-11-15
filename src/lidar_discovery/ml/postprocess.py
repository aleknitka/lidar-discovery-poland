"""Post-processing: pixel probabilities -> polygons/lines, NMS, support flags."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import ndimage

from lidar_discovery.processing.dtm import Grid


def prob_to_candidates(
    prob: np.ndarray,
    grid: Grid,
    thresh: float = 0.5,
    min_area_m2: float = 10.0,
    support: np.ndarray | None = None,
    to_wgs84=None,
) -> list[dict[str, Any]]:
    """Threshold probability map -> connected components -> candidates."""
    valid = np.isfinite(prob)
    mask = valid & (prob >= thresh)
    mask = ndimage.binary_opening(mask, structure=np.ones((3, 3)))
    # label
    try:
        from skimage.measure import label as sk_label  # type: ignore[import-not-found]
        from skimage.measure import regionprops

        lab = sk_label(mask.astype(np.int32), connectivity=2)
        regs = regionprops(lab, intensity_image=np.where(valid, prob, 0))
        out: list[dict[str, Any]] = []
        pix_m2 = grid.res * grid.res
        for reg in regs:
            area_m2 = reg.area * pix_m2
            if area_m2 < min_area_m2:
                continue
            rc = reg.centroid
            lon, lat = _rc_to_wgs84(rc[0], rc[1], grid, to_wgs84)
            frac = _support_frac(support, reg.bbox) if support is not None else 1.0
            out.append(
                {
                    "kind": "other",
                    "centroid_rc": (float(rc[0]), float(rc[1])),
                    "centroid_wgs84": (lon, lat),
                    "area_m2": float(area_m2),
                    "prob_mean": float(np.mean(prob[reg.coords[:, 0], reg.coords[:, 1]])),
                    "low_support": frac < 0.7,
                    "support_fraction": frac,
                    "score": float(np.mean(prob[reg.coords[:, 0], reg.coords[:, 1]])),
                }
            )
        return out
    except Exception:
        lab, _ = ndimage.label(mask, structure=np.ones((3, 3)))
        out2: list[dict[str, Any]] = []
        pix_m2 = grid.res * grid.res
        for lid in range(1, int(lab.max()) + 1):
            idx = np.where(lab == lid)
            area_m2 = len(idx[0]) * pix_m2
            if area_m2 < min_area_m2:
                continue
            rc = (float(np.mean(idx[0])), float(np.mean(idx[1])))
            lon, lat = _rc_to_wgs84(rc[0], rc[1], grid, to_wgs84)
            out2.append({"kind": "other", "centroid_rc": rc, "centroid_wgs84": (lon, lat), "area_m2": float(area_m2), "score": float(np.mean(prob[idx]))})
        return out2


def _rc_to_wgs84(r: float, c: float, grid: Grid, to_wgs84) -> tuple[float, float]:
    x = grid.x0 + (c + 0.5) * grid.res
    y = grid.y1 - (r + 0.5) * grid.res
    if to_wgs84 is not None:
        lon, lat = to_wgs84(x, y)
        return float(lon), float(lat)
    return float(x), float(y)


def _support_frac(support: np.ndarray, bbox: Any) -> float:
    r0, c0, r1, c1 = (int(v) for v in bbox)
    patch = support[r0:r1, c0:c1]
    valid = np.isfinite(patch)
    if not valid.any():
        return 0.0
    return float(np.mean(patch[valid] > 0.05))


def nms(cands: list[dict[str, Any]], dist_m: float, grid: Grid) -> list[dict[str, Any]]:
    """Non-maximum suppression by centroid distance (6 m default). Keeps higher score."""
    cands = sorted(cands, key=lambda c: c.get("score", c.get("model_score", 0)), reverse=True)
    kept: list[dict[str, Any]] = []
    for c in cands:
        rc = c.get("centroid_rc")
        if rc is None:
            kept.append(c)
            continue
        too_close = False
        for k in kept:
            krc = k.get("centroid_rc")
            if krc is None:
                continue
            if math.hypot(rc[0] - krc[0], rc[1] - krc[1]) * grid.res < dist_m:
                too_close = True
                break
        if not too_close:
            kept.append(c)
    return kept
