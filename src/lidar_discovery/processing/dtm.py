"""Ground points -> DTM (Delaunay-linear, blockwise) + ground-density raster."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from rasterio.transform import Affine, from_origin
from scipy import ndimage
from scipy.spatial import Delaunay

NODATA = -9999.0


@dataclass(frozen=True)
class Grid:
    """A north-up raster grid in a projected CRS (EPSG:2180)."""

    x0: float  # west edge
    y1: float  # north edge
    res: float
    width: int
    height: int

    @property
    def transform(self) -> Affine:
        return from_origin(self.x0, self.y1, self.res, self.res)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (
            self.x0,
            self.y1 - self.height * self.res,
            self.x0 + self.width * self.res,
            self.y1,
        )

    @classmethod
    def from_bounds(
        cls, bounds: tuple[float, float, float, float], res: float, snap: bool = True
    ) -> Grid:
        minx, miny, maxx, maxy = bounds
        if snap:
            minx, miny = np.floor(minx / res) * res, np.floor(miny / res) * res
            maxx, maxy = np.ceil(maxx / res) * res, np.ceil(maxy / res) * res
        w = round((maxx - minx) / res)
        h = round((maxy - miny) / res)
        return cls(float(minx), float(maxy), res, w, h)

    def cell_centres(self, r0: int, r1: int, c0: int, c1: int) -> tuple[np.ndarray, np.ndarray]:
        xs = self.x0 + (np.arange(c0, c1) + 0.5) * self.res
        ys = self.y1 - (np.arange(r0, r1) + 0.5) * self.res
        return np.meshgrid(xs, ys)


def point_counts(pts: np.ndarray, grid: Grid) -> np.ndarray:
    """Number of points per grid cell."""
    col = np.floor((pts[:, 0] - grid.x0) / grid.res).astype(np.int64)
    row = np.floor((grid.y1 - pts[:, 1]) / grid.res).astype(np.int64)
    ok = (col >= 0) & (col < grid.width) & (row >= 0) & (row < grid.height)
    flat = row[ok] * grid.width + col[ok]
    return np.bincount(flat, minlength=grid.width * grid.height).reshape(grid.height, grid.width)


def ground_density(counts: np.ndarray, res: float, window_m: float = 4.0) -> np.ndarray:
    """Ground points per m2, averaged over a window_m x window_m box (float32)."""
    size = max(1, round(window_m / res))
    per_cell = counts.astype(np.float32) / (res * res)
    return ndimage.uniform_filter(per_cell, size=size, mode="nearest").astype(np.float32)


def _fast_transforms(tri: Delaunay) -> None:
    """Pre-fill scipy's lazy barycentric-transform cache with a vectorised computation.

    scipy computes `Delaunay.transform` with one LAPACK call per simplex, which takes ~15 s for
    600k triangles and is triggered by find_simplex. This is the same maths in numpy. Uses the
    private `_transform` attribute; if it is absent the scipy path is used unchanged."""
    if not hasattr(tri, "_transform"):
        return
    p = tri.points[tri.simplices]  # (n, 3, 2)
    a = p[:, 0, 0] - p[:, 2, 0]
    b = p[:, 1, 0] - p[:, 2, 0]
    c = p[:, 0, 1] - p[:, 2, 1]
    d = p[:, 1, 1] - p[:, 2, 1]
    det = a * d - b * c
    with np.errstate(divide="ignore", invalid="ignore"):
        inv = np.empty((len(det), 3, 2))
        inv[:, 0, 0] = d / det
        inv[:, 0, 1] = -b / det
        inv[:, 1, 0] = -c / det
        inv[:, 1, 1] = a / det
    inv[:, 2, :] = p[:, 2, :]
    inv[~np.isfinite(inv).all(axis=(1, 2))] = np.nan  # degenerate triangles never match
    tri._transform = inv


def _tin_interpolate(xy: np.ndarray, z: np.ndarray, query: np.ndarray) -> np.ndarray:
    """Delaunay-linear (barycentric) interpolation; NaN outside the convex hull.

    Equivalent to scipy's LinearNDInterpolator but much faster for large query sets."""
    tri = Delaunay(xy)
    _fast_transforms(tri)
    simplex = tri.find_simplex(query)
    out = np.full(len(query), np.nan)
    ok = simplex >= 0
    s = simplex[ok]
    t = tri.transform[s]
    bary = np.einsum("nij,nj->ni", t[:, :2, :], query[ok] - t[:, 2, :])
    w = np.column_stack([bary, 1.0 - bary.sum(axis=1)])
    out[ok] = np.einsum("ni,ni->n", w, z[tri.simplices[s]])
    return out


def grid_dtm(
    pts: np.ndarray,
    grid: Grid,
    max_gap_m: float = 6.0,
    block: int = 1024,
    buffer_m: float = 15.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Interpolate a DTM with a Delaunay-linear TIN, blockwise with a point buffer so that
    block seams are invisible. Cells farther than max_gap_m from any ground point (or outside
    the TIN hull) are NaN.

    Returns (dtm float32 with NaN, point counts per cell)."""
    dtm = np.full((grid.height, grid.width), np.nan, dtype=np.float32)
    counts = point_counts(pts, grid)
    if len(pts) < 4:
        return dtm, counts
    for r0 in range(0, grid.height, block):
        r1 = min(r0 + block, grid.height)
        for c0 in range(0, grid.width, block):
            c1 = min(c0 + block, grid.width)
            xx, yy = grid.cell_centres(r0, r1, c0, c1)
            xmin, xmax = xx.min() - buffer_m, xx.max() + buffer_m
            ymin, ymax = yy.min() - buffer_m, yy.max() + buffer_m
            m = (
                (pts[:, 0] >= xmin)
                & (pts[:, 0] <= xmax)
                & (pts[:, 1] >= ymin)
                & (pts[:, 1] <= ymax)
            )
            if m.sum() < 4:
                continue
            ox, oy = xx.min(), yy.max()  # local origin for numerical stability
            sub = pts[m]
            try:
                vals = _tin_interpolate(
                    np.column_stack([sub[:, 0] - ox, sub[:, 1] - oy]),
                    sub[:, 2],
                    np.column_stack([(xx - ox).ravel(), (yy - oy).ravel()]),
                )
                dtm[r0:r1, c0:c1] = vals.reshape(xx.shape).astype(np.float32)
            except Exception:  # degenerate (collinear) block: leave NaN
                continue
    # mask cells far from any ground point
    dist = ndimage.distance_transform_edt(counts == 0) * grid.res
    dtm[dist > max_gap_m] = np.nan
    return dtm, counts
