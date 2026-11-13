from __future__ import annotations

from pathlib import Path

import laspy
import numpy as np
import pytest
from pyproj import Transformer

from lidar_discovery.config import Settings

FIXTURES = Path(__file__).parent / "fixtures"
LON, LAT = 22.61833, 49.16639  # Carynskie (Wikidata)
_E, _N = Transformer.from_crs(4326, 2180, always_xy=True).transform(LON, LAT)


def synthetic_ground(
    cx: float,
    cy: float,
    half: float = 100.0,
    density: float = 3.0,
    pit: tuple[float, float, float] | None = (6.0, 8.0, 1.0),
    seed: int = 0,
) -> np.ndarray:
    """Gently sloping plane with an optional rectangular pit (width_x, width_y, depth)."""
    rng = np.random.default_rng(seed)
    n = int((2 * half) ** 2 * density)
    x = rng.uniform(cx - half, cx + half, n)
    y = rng.uniform(cy - half, cy + half, n)
    z = 500.0 + 0.02 * (x - cx)
    if pit:
        wx, wy, d = pit
        inside = (abs(x - cx) < wx / 2) & (abs(y - cy) < wy / 2)
        z = np.where(inside, z - d, z)
    return np.column_stack([x, y, z])


def write_laz(path: Path, pts: np.ndarray, noise_fraction: float = 0.1) -> Path:
    """Write points as LAZ; a fraction is labelled vegetation (class 5) and must be ignored."""
    header = laspy.LasHeader(point_format=6, version="1.4")
    header.scales = (0.01, 0.01, 0.01)
    header.offsets = pts.min(axis=0)
    las = laspy.LasData(header)
    las.x, las.y, las.z = pts[:, 0], pts[:, 1], pts[:, 2]
    cls = np.full(len(pts), 2, dtype=np.uint8)
    rng = np.random.default_rng(1)
    veg = rng.random(len(pts)) < noise_fraction
    cls[veg] = 5
    las.z = np.where(veg, pts[:, 2] + 15.0, pts[:, 2])  # canopy hits float above ground
    las.classification = cls
    path.parent.mkdir(parents=True, exist_ok=True)
    las.write(str(path))
    return path


@pytest.fixture
def centre() -> tuple[float, float]:
    return _E, _N


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    s = Settings(data_dir=tmp_path / "data", seeds_dir=tmp_path / "seeds")
    s.ensure_dirs()
    return s
