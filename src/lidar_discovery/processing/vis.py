"""Terrain visualisations in numpy/scipy (algorithms follow RVT; see docs/08).

All functions take a float32 DTM with NaN for no data and return float32 with NaN preserved.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import ndimage


def fill_nan_nearest(a: np.ndarray) -> np.ndarray:
    """Fill NaN with the nearest valid value (so filters do not propagate NaN)."""
    bad = np.isnan(a)
    if not bad.any():
        return a
    if bad.all():
        return np.zeros_like(a)
    idx = ndimage.distance_transform_edt(bad, return_distances=False, return_indices=True)
    return a[tuple(idx)]


def slope_aspect(dtm: np.ndarray, res: float) -> tuple[np.ndarray, np.ndarray]:
    """Slope (radians) and aspect (radians, direction the slope faces, clockwise from north)."""
    z = fill_nan_nearest(dtm).astype(np.float32)
    dzdy, dzdx = np.gradient(z, res)  # rows increase southwards
    slope = np.arctan(np.hypot(dzdx, dzdy))
    aspect = np.arctan2(-dzdx, dzdy)  # downhill direction, from north, clockwise
    aspect = np.mod(aspect, 2 * np.pi)
    return slope.astype(np.float32), aspect.astype(np.float32)


def slope_deg(dtm: np.ndarray, res: float) -> np.ndarray:
    s, _ = slope_aspect(dtm, res)
    out = np.degrees(s).astype(np.float32)
    out[np.isnan(dtm)] = np.nan
    return out


def hillshade_multi(
    dtm: np.ndarray,
    res: float,
    n_dir: int = 16,
    sun_elevation_deg: float = 35.0,
    vert_exag: float = 1.0,
) -> np.ndarray:
    """Mean of n_dir single-azimuth hillshades, values 0..1."""
    z = fill_nan_nearest(dtm).astype(np.float32) * vert_exag
    dzdy, dzdx = np.gradient(z, res)
    # surface normal (nx, ny, nz) pointing up; x east, y north (dzdy is per row = southwards)
    nx, ny, nz = -dzdx, dzdy, np.ones_like(dzdx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / norm, ny / norm, nz / norm
    el = math.radians(sun_elevation_deg)
    acc = np.zeros_like(z)
    for k in range(n_dir):
        az = 2 * math.pi * k / n_dir  # clockwise from north
        lx, ly, lz = math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el)
        acc += np.clip(nx * lx + ny * ly + nz * lz, 0, 1)
    out = (acc / n_dir).astype(np.float32)
    out[np.isnan(dtm)] = np.nan
    return out


def _radial_steps(max_cells: int) -> list[int]:
    """Dense steps near the cell, sparser further out (keeps cost low)."""
    steps = list(range(1, min(max_cells, 8) + 1))
    s = steps[-1]
    while s < max_cells:
        s = min(max_cells, math.ceil(s * 1.25) + 1)
        steps.append(s)
    return steps


def sky_view_factor(
    dtm: np.ndarray,
    res: float,
    radius_m: float = 10.0,
    n_dir: int = 16,
    chunk_rows: int = 512,
) -> np.ndarray:
    """Sky-view factor: 1 - mean over directions of sin(max horizon elevation angle >= 0).

    Neighbours are sampled at integer-cell offsets (rounded along each direction). Processing
    is chunked in row bands with a halo so memory stays bounded for large AOIs."""
    z = fill_nan_nearest(dtm).astype(np.float32)
    h, w = z.shape
    r = max(1, round(radius_m / res))
    steps = _radial_steps(r)
    pad = r
    zp = np.pad(z, pad, mode="constant", constant_values=-1e4)  # outside: no horizon
    out = np.empty((h, w), dtype=np.float32)
    dirs = [
        (math.sin(2 * math.pi * k / n_dir), -math.cos(2 * math.pi * k / n_dir))
        for k in range(n_dir)
    ]
    for r0 in range(0, h, chunk_rows):
        r1 = min(r0 + chunk_rows, h)
        centre = z[r0:r1]
        acc = np.zeros_like(centre)
        for dx, dy in dirs:  # dx east (cols), dy south (rows)
            best = np.full_like(centre, -np.inf)
            seen: set[tuple[int, int]] = set()
            for s in steps:
                dj, di = round(dx * s), round(dy * s)
                if (di, dj) in seen or (di == 0 and dj == 0):
                    continue
                seen.add((di, dj))
                dist = math.hypot(di, dj) * res
                nb = zp[pad + r0 + di : pad + r1 + di, pad + dj : pad + w + dj]
                np.maximum(best, (nb - centre) / dist, out=best)
            acc += np.sin(np.arctan(np.maximum(best, 0.0)))
        out[r0:r1] = 1.0 - acc / n_dir
    out[np.isnan(dtm)] = np.nan
    return out


def local_relief_model(dtm: np.ndarray, res: float, sigma_m: float = 10.0) -> np.ndarray:
    """DTM minus a NaN-aware Gaussian low-pass (sigma 10 m, i.e. ~20 m wavelengths removed)."""
    valid = (~np.isnan(dtm)).astype(np.float32)
    z0 = np.where(np.isnan(dtm), 0.0, dtm).astype(np.float32)
    sigma = sigma_m / res
    num = ndimage.gaussian_filter(z0, sigma, mode="nearest", truncate=3.0)
    den = ndimage.gaussian_filter(valid, sigma, mode="nearest", truncate=3.0)
    low = num / np.maximum(den, 1e-6)
    out = (dtm - low).astype(np.float32)
    out[np.isnan(dtm)] = np.nan
    return out
