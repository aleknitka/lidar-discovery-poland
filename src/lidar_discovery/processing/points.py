"""Read class-2 (ground) points from LAS/LAZ files. Files are treated as untrusted data."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import laspy
import numpy as np

GROUND_CLASS = 2


def las_bounds(path: Path) -> tuple[float, float, float, float]:
    with laspy.open(path) as fh:
        h = fh.header
        return float(h.x_min), float(h.y_min), float(h.x_max), float(h.y_max)


def read_ground(
    paths: Iterable[Path],
    bounds: tuple[float, float, float, float] | None = None,
    chunk_size: int = 4_000_000,
) -> tuple[np.ndarray, dict]:
    """Return (N,3) float64 array of class-2 points inside bounds (minx,miny,maxx,maxy),
    and stats {points_total, points_ground, files}."""
    parts: list[np.ndarray] = []
    total = 0
    n_files = 0
    for p in paths:
        with laspy.open(p) as fh:
            h = fh.header
            if bounds and (
                h.x_max < bounds[0]
                or h.x_min > bounds[2]
                or h.y_max < bounds[1]
                or h.y_min > bounds[3]
            ):
                continue
            n_files += 1
            for chunk in fh.chunk_iterator(chunk_size):
                total += len(chunk)
                sel = np.asarray(chunk.classification) == GROUND_CLASS
                if not sel.any():
                    continue
                x = np.asarray(chunk.x)[sel]
                y = np.asarray(chunk.y)[sel]
                z = np.asarray(chunk.z)[sel]
                if bounds:
                    m = (x >= bounds[0]) & (x <= bounds[2]) & (y >= bounds[1]) & (y <= bounds[3])
                    x, y, z = x[m], y[m], z[m]
                if len(x):
                    parts.append(np.column_stack([x, y, z]))
    pts = np.vstack(parts) if parts else np.empty((0, 3))
    return pts, {"points_total": total, "points_ground": len(pts), "files": n_files}
