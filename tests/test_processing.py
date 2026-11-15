from __future__ import annotations

import json

import numpy as np
import rasterio
from shapely.geometry import box
from sqlmodel import Session

from conftest import LAT, LON, synthetic_ground, write_laz
from lidar_discovery.catalog.db import get_engine
from lidar_discovery.processing import vis
from lidar_discovery.processing.dtm import Grid, grid_dtm, point_counts
from lidar_discovery.processing.pipeline import ProcessParams, compute_products, process_aoi
from lidar_discovery.processing.points import read_ground

PIT = (6.0, 8.0, 1.0)  # width_x, width_y, depth (m)


def _centre_index(grid: Grid, cx: float, cy: float) -> tuple[int, int]:
    return int((grid.y1 - cy) / grid.res), int((cx - grid.x0) / grid.res)


def test_pit_visible_in_dtm_and_lrm():
    cx, cy = 1000.0, 2000.0
    pts = synthetic_ground(cx, cy, half=100, density=3, pit=PIT)
    aoi = box(cx - 40, cy - 40, cx + 40, cy + 40)
    grid, arrays, _ = compute_products(pts, aoi, ProcessParams())
    r, c = _centre_index(grid, cx, cy)
    dtm, lrm, svf = arrays["dtm"], arrays["lrm"], arrays["svf"]
    # DTM: pit floor ~ 1 m below the rim
    rim = dtm[r, c + int(10 / 0.5)]
    assert rim - dtm[r, c] > 0.8
    # LRM: strongly negative in the pit, ~0 on flat ground far away
    assert lrm[r, c] < -0.7
    assert abs(np.nanmedian(lrm)) < 0.05
    # pit footprint approx 6 x 8 m = 48 m2 -> count cells below -0.4 m
    area = np.nansum(lrm < -0.4) * 0.25
    assert 30 < area < 80
    # SVF is reduced inside the pit
    assert svf[r, c] < np.nanmedian(svf) - 0.05
    # clip: nothing outside the AOI
    assert grid.width == 160 and grid.height == 160
    assert not np.isnan(arrays["hillshade"]).all()


def test_tin_matches_scipy_linear():
    from scipy.interpolate import LinearNDInterpolator

    from lidar_discovery.processing.dtm import _tin_interpolate

    rng = np.random.default_rng(3)
    xy = rng.uniform(0, 50, (3000, 2))
    z = np.sin(xy[:, 0] / 5) + xy[:, 1] * 0.1
    q = rng.uniform(-5, 55, (2000, 2))
    ref = LinearNDInterpolator(xy, z)(q)
    got = _tin_interpolate(xy, z, q)
    assert np.array_equal(np.isnan(ref), np.isnan(got))
    assert np.allclose(ref, got, equal_nan=True, atol=1e-9)


def test_masks_cells_far_from_ground_points():
    cx, cy = 0.0, 0.0
    pts = synthetic_ground(cx, cy, half=30, density=3, pit=None)
    grid = Grid.from_bounds((-30, -30, 80, 30), 0.5)
    dtm, counts = grid_dtm(pts, grid, max_gap_m=6.0)
    assert counts.sum() == len(pts)
    assert not np.isnan(dtm[:, 20]).all()  # covered by points
    assert np.isnan(dtm[:, -5:]).all()  # x > 75 m is > 6 m from any point (points end at x=30)


def test_flat_surface_vis():
    z = np.full((120, 120), 10.0, dtype=np.float32)
    assert np.allclose(vis.slope_deg(z, 0.5), 0.0)
    assert np.allclose(vis.sky_view_factor(z, 0.5, 10.0), 1.0, atol=1e-5)
    assert np.allclose(vis.local_relief_model(z, 0.5), 0.0, atol=1e-5)
    hs = vis.hillshade_multi(z, 0.5)
    assert np.allclose(hs, np.sin(np.radians(35)), atol=1e-4)


def test_slope_and_nan_preserved():
    _y, x = np.mgrid[0:100, 0:100]
    z = (x * 0.5 * np.tan(np.radians(20))).astype(np.float32)  # 20 degrees up eastwards
    z[10:20, 10:20] = np.nan
    s = vis.slope_deg(z, 0.5)
    assert abs(np.nanmedian(s) - 20.0) < 0.5
    assert np.isnan(s[15, 15])
    assert not np.isnan(vis.sky_view_factor(z, 0.5, 5.0)[50, 50])


def test_read_ground_filters_class(tmp_path):
    pts = synthetic_ground(1000, 2000, half=20, density=2, pit=None)
    f = write_laz(tmp_path / "t.laz", pts, noise_fraction=0.25)
    got, stats = read_ground([f])
    assert stats["points_total"] == len(pts)
    assert 0.7 * len(pts) < len(got) < 0.8 * len(pts)
    assert got[:, 2].max() < 505  # canopy hits (class 5, +15 m) are excluded
    sub, _ = read_ground([f], (1000, 2000, 1010, 2010))
    assert 0 < len(sub) < len(got)
    none, st = read_ground([f], (5000, 5000, 6000, 6000))
    assert len(none) == 0 and st["files"] == 0
    assert point_counts(got, Grid.from_bounds((970, 1970, 1030, 2030), 1.0)).sum() == len(got)


def test_process_aoi_writes_cogs(settings, centre):
    e, n = centre
    pts = synthetic_ground(e, n, half=100, density=3, pit=PIT)
    laz = write_laz(settings.raw_dir / "local-laz" / "2020" / "t.laz", pts)
    aoi = box(e - 50, n - 50, e + 50, n + 50)
    res = process_aoi(
        settings, "loc", aoi, "local-laz", 2020, [laz], "PL-EVRF2007-NH", ProcessParams()
    )
    kinds = {p.kind for p in res.products}
    assert kinds == {"dtm", "ground_density", "hillshade", "slope", "svf", "lrm"}
    for p in res.products:
        path = settings.data_dir / p.path
        with rasterio.open(path) as ds:
            assert ds.crs.to_epsg() == 2180
            assert ds.dtypes[0] == "float32"
            assert ds.res == (0.5, 0.5)
            assert ds.profile["tiled"] and ds.profile["compress"] == "deflate"
            assert ds.nodata == -9999.0
        prov = json.loads(p.provenance)
        assert prov["crs_h"] == "PL-EVRF2007-NH"
        assert prov["inputs"][0]["file"] == "t.laz" and len(prov["inputs"][0]["sha256"]) == 64
        w, s, e_, n_ = json.loads(p.bounds_wgs84)
        assert w < LON < e_ and s < LAT < n_
    assert (settings.derived_dir / "loc" / "local-laz-2020" / "provenance.json").exists()
    # products can be stored in the catalog
    from lidar_discovery.catalog import repo

    with Session(get_engine(settings)) as s:
        for p in res.products:
            repo.add_product(s, p)
        assert len(repo.list_products(s, "loc")) == 6
