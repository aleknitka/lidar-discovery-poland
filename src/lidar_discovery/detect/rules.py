"""Deterministic candidate generators (Stage 0, 09 §4.1 A, 11 §5 Track A).

Three generators, all pure numpy/scipy (optional skimage for labelling/morph).
Each accepts arrays dict + Grid and returns list[dict] candidates with
pixel-space geometry; `as_candidates()` converts to Candidate-ready dicts.
Handles NaN via fill_nan_nearest and respects a support mask (>30% unsupported
=> low_support flag, never silently dropped).
"""

from __future__ import annotations

import math
import uuid
from typing import Any

import numpy as np
from scipy import ndimage

try:
    from skimage.measure import label as sk_label  # type: ignore[import-not-found]
    from skimage.measure import regionprops
    from skimage.morphology import skeletonize  # type: ignore[import-not-found]

    HAS_SKIMAGE = True
except Exception:
    HAS_SKIMAGE = False
    sk_label = None  # type: ignore[assignment]
    regionprops = None  # type: ignore[assignment]
    skeletonize = None  # type: ignore[assignment]

from lidar_discovery.processing.dtm import Grid


def _support_fraction(support: np.ndarray | None, sl: tuple[slice, slice]) -> float:
    if support is None:
        return 1.0
    patch = support[sl]
    valid = np.isfinite(patch)
    if not valid.any():
        return 0.0
    # support is log-scaled 0..1 or binary 0/1; unsupported = 0 or NaN
    return float(np.mean(patch[valid] > 0.05))


def _pixel_to_wgs84(
    r: float, c: float, grid: Grid, to_wgs84=None
) -> tuple[float, float]:
    x = grid.x0 + (c + 0.5) * grid.res
    y = grid.y1 - (r + 0.5) * grid.res
    if to_wgs84 is not None:
        lon, lat = to_wgs84(x, y)
        return float(lon), float(lat)
    return float(x), float(y)


def _label_components(mask: np.ndarray) -> tuple[np.ndarray, int]:
    if HAS_SKIMAGE and sk_label is not None:
        lab = sk_label(mask.astype(np.int32), connectivity=2)
        return lab, int(lab.max())
    # fallback: scipy
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    return lab.astype(np.int32), int(n)


# ---------------------------------------------------------------- closed depressions (cellars, wells, pits)


def detect_closed_depressions(
    arrays: dict[str, np.ndarray],
    grid: Grid,
    *,
    depth_min: float = 0.30,
    depth_max: float = 2.5,
    area_min_m2: float = 3.0,
    area_max_m2: float = 80.0,
    support: np.ndarray | None = None,
    to_wgs84=None,
) -> list[dict[str, Any]]:
    """Fill-depth threshold -> labelled components -> filtered candidates.

    Returns list of dicts with keys: centroid_rc, area_m2, depth_max, depth_mean,
    circularity, low_support, bbox, kind='cellar_pit'.
    """
    filld = arrays.get("fill_depth")
    if filld is None:
        return []
    # depth band
    valid = np.isfinite(filld)
    mask = valid & (filld >= depth_min) & (filld <= depth_max)
    if not mask.any():
        return []
    lab, _ = _label_components(mask)
    out: list[dict[str, Any]] = []
    res = grid.res
    pix_m2 = res * res
    if HAS_SKIMAGE and regionprops is not None:
        for reg in regionprops(lab, intensity_image=np.where(valid, filld, 0)):
            area_m2 = reg.area * pix_m2
            if not (area_min_m2 <= area_m2 <= area_max_m2):
                continue
            # depth stats within region
            coords = reg.coords
            vals = filld[coords[:, 0], coords[:, 1]]
            vals = vals[np.isfinite(vals)]
            if not len(vals):
                continue
            dmax = float(np.max(vals))
            dmean = float(np.mean(vals))
            # circularity 4πA/P², compactness via eccentricity
            perim = float(reg.perimeter) if reg.perimeter else 1.0
            circ = float(4 * math.pi * reg.area / max(perim * perim, 1))
            sl = (slice(reg.bbox[0], reg.bbox[2]), slice(reg.bbox[1], reg.bbox[3]))
            frac = _support_fraction(support, sl)
            low_support = frac < 0.7
            rc = reg.centroid  # (row, col)
            lon, lat = _pixel_to_wgs84(rc[0], rc[1], grid, to_wgs84)
            out.append(
                {
                    "kind": "cellar_pit",
                    "centroid_rc": (float(rc[0]), float(rc[1])),
                    "centroid_xy2180": (
                        float(grid.x0 + (rc[1] + 0.5) * res),
                        float(grid.y1 - (rc[0] + 0.5) * res),
                    ),
                    "centroid_wgs84": (lon, lat),
                    "area_m2": float(area_m2),
                    "depth_max": dmax,
                    "depth_mean": dmean,
                    "circularity": circ,
                    "eccentricity": float(getattr(reg, "eccentricity", 0)),
                    "bbox_rc": reg.bbox,
                    "low_support": low_support,
                    "support_fraction": frac,
                    "score": float(np.clip(dmean / 1.0, 0, 1) * 0.6 + 0.2),
                }
            )
    else:
        # scipy fallback: iterate labels with ndimage
        for lab_id in range(1, int(lab.max()) + 1):
            idx = np.where(lab == lab_id)
            area_m2 = len(idx[0]) * pix_m2
            if not (area_min_m2 <= area_m2 <= area_max_m2):
                continue
            vals = filld[idx]
            vals = vals[np.isfinite(vals)]
            if not len(vals):
                continue
            dmax = float(np.max(vals))
            dmean = float(np.mean(vals))
            r0, r1 = int(np.min(idx[0])), int(np.max(idx[0]))
            c0, c1 = int(np.min(idx[1])), int(np.max(idx[1]))
            sl = (slice(r0, r1 + 1), slice(c0, c1 + 1))
            frac = _support_fraction(support, sl)
            low_support = frac < 0.7
            rc = (float(np.mean(idx[0])), float(np.mean(idx[1])))
            lon, lat = _pixel_to_wgs84(rc[0], rc[1], grid, to_wgs84)
            out.append(
                {
                    "kind": "cellar_pit",
                    "centroid_rc": rc,
                    "centroid_wgs84": (lon, lat),
                    "area_m2": float(area_m2),
                    "depth_max": dmax,
                    "depth_mean": dmean,
                    "circularity": 0.0,
                    "low_support": low_support,
                    "support_fraction": frac,
                    "score": float(np.clip(dmean / 1.0, 0, 1) * 0.6 + 0.2),
                }
            )
    return out


# -------------------------------------------------------------- positive LRM blobs (platforms, mounds)


def detect_lrm_blobs(
    arrays: dict[str, np.ndarray],
    grid: Grid,
    *,
    lrm_key: str = "lrm",
    thresh_m: float = 0.15,
    area_min_m2: float = 20.0,
    area_max_m2: float = 250.0,
    rectangularity_min: float = 0.0,
    support: np.ndarray | None = None,
    to_wgs84=None,
) -> list[dict[str, Any]]:
    """Positive LRM threshold -> blobs. Tuned for platforms/terraces.

    If `lrm_key` missing, tries lrm20/lrm5/lrm in order.
    """
    lrm = arrays.get(lrm_key)
    if lrm is None:
        for k in ("lrm20", "lrm", "lrm5"):
            if k in arrays:
                lrm = arrays[k]
                break
    if lrm is None:
        return []
    valid = np.isfinite(lrm)
    mask = valid & (lrm >= thresh_m)
    if not mask.any():
        return []
    # small opening to remove speckle
    mask = ndimage.binary_opening(mask, structure=np.ones((3, 3)))
    lab, _ = _label_components(mask)
    out: list[dict[str, Any]] = []
    res = grid.res
    pix_m2 = res * res
    if HAS_SKIMAGE and regionprops is not None:
        for reg in regionprops(lab, intensity_image=np.where(valid, lrm, 0)):
            area_m2 = reg.area * pix_m2
            if not (area_min_m2 <= area_m2 <= area_max_m2):
                continue
            # rectangularity = area / bbox_area
            r0, c0, r1, c1 = reg.bbox
            bbox_area = max((r1 - r0) * (c1 - c0), 1)
            rect = float(reg.area / bbox_area)
            if rect < rectangularity_min:
                continue
            coords = reg.coords
            vals = lrm[coords[:, 0], coords[:, 1]]
            vals = vals[np.isfinite(vals)]
            lmean = float(np.mean(vals)) if len(vals) else 0.0
            sl = (slice(r0, r1), slice(c0, c1))
            frac = _support_fraction(support, sl)
            low_support = frac < 0.7
            rc = reg.centroid
            lon, lat = _pixel_to_wgs84(rc[0], rc[1], grid, to_wgs84)
            out.append(
                {
                    "kind": "house_platform",
                    "centroid_rc": (float(rc[0]), float(rc[1])),
                    "centroid_wgs84": (lon, lat),
                    "area_m2": float(area_m2),
                    "lrm_mean": lmean,
                    "rectangularity": rect,
                    "eccentricity": float(getattr(reg, "eccentricity", 0)),
                    "bbox_rc": reg.bbox,
                    "low_support": low_support,
                    "support_fraction": frac,
                    "score": float(np.clip(lmean / 0.4, 0, 1) * 0.5 + rect * 0.3 + 0.1),
                }
            )
    else:
        for lab_id in range(1, int(lab.max()) + 1):
            idx = np.where(lab == lab_id)
            area_m2 = len(idx[0]) * pix_m2
            if not (area_min_m2 <= area_m2 <= area_max_m2):
                continue
            vals = lrm[idx]
            vals = vals[np.isfinite(vals)]
            lmean = float(np.mean(vals)) if len(vals) else 0.0
            r0, r1 = int(np.min(idx[0])), int(np.max(idx[0]))
            c0, c1 = int(np.min(idx[1])), int(np.max(idx[1]))
            sl = (slice(r0, r1 + 1), slice(c0, c1 + 1))
            frac = _support_fraction(support, sl)
            low_support = frac < 0.7
            rc = (float(np.mean(idx[0])), float(np.mean(idx[1])))
            lon, lat = _pixel_to_wgs84(rc[0], rc[1], grid, to_wgs84)
            out.append(
                {
                    "kind": "house_platform",
                    "centroid_rc": rc,
                    "centroid_wgs84": (lon, lat),
                    "area_m2": float(area_m2),
                    "lrm_mean": lmean,
                    "rectangularity": 0.0,
                    "low_support": low_support,
                    "support_fraction": frac,
                    "score": float(np.clip(lmean / 0.4, 0, 1) * 0.5 + 0.1),
                }
            )
    return out


# -------------------------------------------------------------- linear features (holloways, terraces)


def detect_linear_features(
    arrays: dict[str, np.ndarray],
    grid: Grid,
    *,
    svf_thresh: float = 0.92,
    slope_thresh_deg: float = 8.0,
    min_length_m: float = 15.0,
    support: np.ndarray | None = None,
    to_wgs84=None,
) -> list[dict[str, Any]]:
    """SVF trough + slope ridge -> skeleton -> line candidates.

    Simple and CPU-cheap; U-Net (stage 3) replaces this for production linears.
    Returns candidates with kind holloway or terrace and a polyline in pixel coords.
    """
    svf = arrays.get("svf")
    slope = arrays.get("slope")
    if svf is None and slope is None:
        return []
    h, w = next(iter(arrays.values())).shape
    # linear depression: low SVF (enclosed) and moderate slope nearby
    mask = np.zeros((h, w), dtype=bool)
    if svf is not None:
        valid = np.isfinite(svf)
        mask |= valid & (svf < svf_thresh)
    if slope is not None and HAS_SKIMAGE:
        # ridge = slope > thresh and is local max across a small window
        # cheap proxy: slope > thresh
        valid_s = np.isfinite(slope)
        mask |= valid_s & (slope > slope_thresh_deg)
    elif slope is not None:
        valid_s = np.isfinite(slope)
        mask |= valid_s & (slope > slope_thresh_deg)
    mask = ndimage.binary_opening(mask, structure=np.ones((3, 3)))
    if not mask.any():
        return []
    # skeletonize to 1-px lines
    if HAS_SKIMAGE and skeletonize is not None:
        try:
            skel = skeletonize(mask)
        except Exception:
            skel = mask
    else:
        skel = mask
    lab, n = _label_components(skel)
    out: list[dict[str, Any]] = []
    res = grid.res
    for lab_id in range(1, n + 1):
        idx = np.where(lab == lab_id)
        length_m = len(idx[0]) * res  # approx (Manhattan); good enough for filter
        if length_m < min_length_m:
            continue
        # support check at centre
        rc = (float(np.mean(idx[0])), float(np.mean(idx[1])))
        r0, r1 = int(np.min(idx[0])), int(np.max(idx[0]))
        c0, c1 = int(np.min(idx[1])), int(np.max(idx[1]))
        sl = (slice(max(0, r0 - 2), r1 + 3), slice(max(0, c0 - 2), c1 + 3))
        frac = _support_fraction(support, sl)
        low_support = frac < 0.7
        lon, lat = _pixel_to_wgs84(rc[0], rc[1], grid, to_wgs84)
        # keep a decimated polyline (every 4th point) for storage
        pts = list(zip(idx[0][::4].tolist(), idx[1][::4].tolist()))
        out.append(
            {
                "kind": "holloway",
                "centroid_rc": rc,
                "centroid_wgs84": (lon, lat),
                "length_m": float(length_m),
                "polyline_rc": pts,
                "low_support": low_support,
                "support_fraction": frac,
                "score": float(np.clip(length_m / 100.0, 0, 1) * 0.5 + 0.2),
            }
        )
    return out


# -------------------------------------------------------------- combined + dedup


def detect_all(
    arrays: dict[str, np.ndarray],
    grid: Grid,
    *,
    support: np.ndarray | None = None,
    to_wgs84=None,
    enable_linear: bool = True,
) -> list[dict[str, Any]]:
    """Run all three generators and return a deduplicated list.

    Dedup: candidates within 6 m of each other keep the higher score.
    """
    # infer support from arrays if not given
    if support is None:
        support = arrays.get("support", arrays.get("ground_density"))
    cands: list[dict[str, Any]] = []
    cands.extend(
        detect_closed_depressions(arrays, grid, support=support, to_wgs84=to_wgs84)
    )
    cands.extend(detect_lrm_blobs(arrays, grid, support=support, to_wgs84=to_wgs84))
    # also try lrm5 with lower threshold if present
    if "lrm5" in arrays:
        cands.extend(
            detect_lrm_blobs(
                arrays, grid, lrm_key="lrm5", thresh_m=0.10, support=support, to_wgs84=to_wgs84
            )
        )
    if enable_linear:
        cands.extend(
            detect_linear_features(arrays, grid, support=support, to_wgs84=to_wgs84)
        )
    # dedup by distance (6 m)
    cands.sort(key=lambda c: c.get("score", 0), reverse=True)
    kept: list[dict[str, Any]] = []
    for cand in cands:
        rc = cand.get("centroid_rc")
        if rc is None:
            kept.append(cand)
            continue
        too_close = False
        for k in kept:
            krc = k.get("centroid_rc")
            if krc is None:
                continue
            dist_m = math.hypot(rc[0] - krc[0], rc[1] - krc[1]) * grid.res
            if dist_m < 6.0 and cand.get("kind") == k.get("kind"):
                too_close = True
                break
        if not too_close:
            kept.append(cand)
    return kept


def candidate_id() -> str:
    return "cand-" + uuid.uuid4().hex[:12]
