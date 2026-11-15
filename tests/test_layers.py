"""Layer selection: validation, cache keys, incremental computation from an existing DTM."""

from __future__ import annotations

import shutil

import numpy as np
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import box

from lidar_discovery import areas, jobs
from lidar_discovery.api.app import create_app
from lidar_discovery.processing.pipeline import (
    ALL_KINDS,
    DEFAULT_LAYERS,
    LayerError,
    ProcessParams,
    compute_from_dtm,
    compute_products,
    estimate_processing_s,
    normalise_layers,
    step_names,
)
from lidar_discovery.processing.points import read_ground
from test_areas import world  # noqa: F401  (fixture)


def _run_layers(w, layers):
    job, _ = jobs.create_fetch_job(w["settings"], w["bbox"], "fake-src", 2020, layers)
    updates: list[dict] = []
    j = jobs.run_fetch_job(w["settings"], job.id, None, updates.append)
    return j, updates


def _steps(updates):
    return [u["step_name"] for u in updates if u["state"] == "processing" and u["step_name"]]


def _kinds(client, location_id):
    return {lay["kind"] for lay in client.get(f"/api/locations/{location_id}/layers").json()}


def test_normalise_layers():
    assert normalise_layers(None) == DEFAULT_LAYERS
    assert normalise_layers("") == DEFAULT_LAYERS
    assert normalise_layers("svf") == ("dtm", "svf")  # the DTM is always included
    assert normalise_layers(["lrm", "slope", "dtm", "slope"]) == ("dtm", "slope", "lrm")
    assert normalise_layers("ground_density, hillshade") == ("dtm", "hillshade", "ground_density")
    assert set(normalise_layers(",".join(ALL_KINDS))) == set(ALL_KINDS)
    with pytest.raises(LayerError, match="bogus"):
        normalise_layers("dtm,bogus")


def test_cache_key_ignores_layers_but_layers_key_does_not():
    aoi = box(500000, 400000, 500300, 400300)
    full = ProcessParams()
    few = ProcessParams(kinds=("dtm", "svf"))
    assert areas.cache_key("s", 2020, aoi, full) == areas.cache_key("s", 2020, aoi, few)
    assert areas.cache_key("s", 2020, aoi) != areas.cache_key("s", 2021, aoi)
    assert areas.cache_key("s", 2020, aoi) != areas.cache_key("s", 2020, aoi, ProcessParams(res=1))
    k = areas.cache_key("s", 2020, aoi)
    assert areas.layers_key(k, ("dtm", "svf")) != areas.layers_key(k, ("dtm", "slope"))
    assert areas.layers_key(k, ("dtm", "svf")) == areas.layers_key(k, ("svf", "dtm"))


def test_step_names_incremental():
    p = ProcessParams(kinds=("slope", "lrm"))
    assert step_names(p, from_dtm=True) == ["slope", "lrm", "write"]
    p = ProcessParams(kinds=("svf", "ground_density"))
    assert step_names(p, from_dtm=True) == ["ground points", "density", "svf", "write"]
    p = ProcessParams(kinds=("dtm", "slope"))
    assert step_names(p) == ["ground points", "dtm", "slope", "write"]


def test_processing_estimate_scales_and_skips_dtm():
    full = estimate_processing_s(2.0, ["dtm", "svf", "hillshade"], sheets=1)
    assert full["dtm"] > 5 * full["svf"] > 0
    assert full["total"] == pytest.approx(sum(v for k, v in full.items() if k != "total"), abs=0.2)
    inc = estimate_processing_s(2.0, ["dtm", "svf"], sheets=1, from_dtm=True)
    assert "dtm" not in inc and inc["points"] == 0
    assert estimate_processing_s(2.0, ["ground_density"], 2, from_dtm=True)["points"] > 0
    assert (
        estimate_processing_s(4.0, ["svf"], 1)["svf"]
        > estimate_processing_s(2.0, ["svf"], 1)["svf"]
    )


def test_api_rejects_unknown_kinds_with_422(world):  # noqa: F811
    c = TestClient(create_app(world["settings"]))
    w, s, e, n = world["bbox"]
    r = c.get(f"/api/areas/estimate?bbox={w},{s},{e},{n}&layers=dtm,nope")
    assert r.status_code == 422 and "nope" in r.json()["detail"]
    r = c.post("/api/areas/fetch", json={"bbox": [w, s, e, n], "layers": "svf,nope"})
    assert r.status_code == 422
    r = c.post("/api/areas/fetch", json={"bbox": [w, s, e, n], "layers": 5})
    assert r.status_code == 422
    assert c.get("/api/jobs").json() == []  # nothing was queued


def test_estimate_reports_layer_plan(world):  # noqa: F811
    s, bbox = world["settings"], world["bbox"]
    est = areas.estimate_area(s, bbox, layers="svf")
    assert est["layers"] == ["dtm", "svf"] and est["layers_missing"] == ["dtm", "svf"]
    assert est["layers_existing"] == [] and not est["from_existing_dtm"] and est["needs_laz"]
    assert est["processing_s"]["dtm"] > est["processing_s"]["svf"]
    assert areas.estimate_area(s, bbox)["layers"] == list(DEFAULT_LAYERS)


def test_incremental_layers_reuse_dtm_and_skip_download(world):  # noqa: F811
    s = world["settings"]
    j1, u1 = _run_layers(world, "svf")
    assert j1.state == "done", j1.error
    assert _steps(u1) == ["ground points", "dtm", "svf", "write"]
    c = TestClient(create_app(s))
    assert _kinds(c, j1.location_id) == {"dtm", "svf"}
    dtm = s.derived_dir / j1.location_id / "fake-src-2020" / "dtm.tif"
    mtime = dtm.stat().st_mtime_ns
    gets = len(world["server"].gets)
    shutil.rmtree(s.raw_dir)  # the sheets are gone: slope/LRM must not need them

    w, so, e, n = world["bbox"]
    q = f"/api/areas/estimate?bbox={w},{so},{e},{n}&source_id=fake-src&year=2020"
    q += "&layers=svf,slope,lrm"
    est = c.get(q).json()
    assert est["layers_existing"] == ["dtm", "svf"] and est["layers_missing"] == ["slope", "lrm"]
    assert est["from_existing_dtm"] and not est["needs_laz"] and est["bytes_to_download"] == 0
    assert "dtm" not in est["processing_s"]

    j2, u2 = _run_layers(world, "svf,slope,lrm")
    assert j2.state == "done", j2.error
    assert _steps(u2) == ["slope", "lrm", "write"]
    assert j2.message == "done" and not any(u["state"] == "downloading" for u in u2)
    assert _kinds(c, j1.location_id) == {"dtm", "svf", "slope", "lrm"}
    assert dtm.stat().st_mtime_ns == mtime and len(world["server"].gets) == gets
    layers = c.get(f"/api/locations/{j1.location_id}/layers").json()
    slope = next(lay for lay in layers if lay["kind"] == "slope")["provenance"]
    assert slope["computed_from"].startswith("existing-dtm") and slope["cache_key"]

    j3, u3 = _run_layers(world, "slope,svf")  # everything requested already exists
    assert j3.state == "done" and j3.message == "cached" and _steps(u3) == []


def test_incremental_ground_density_reads_points_only(world):  # noqa: F811
    j1, _ = _run_layers(world, "dtm")
    assert j1.state == "done", j1.error
    j2, u2 = _run_layers(world, "dtm,ground_density")
    assert j2.state == "done", j2.error
    assert _steps(u2) == ["ground points", "density", "write"]
    c = TestClient(create_app(world["settings"]))
    assert _kinds(c, j1.location_id) == {"dtm", "ground_density"}


def test_incremental_matches_full_run_away_from_the_border(world):  # noqa: F811
    s = world["settings"]
    j, _ = _run_layers(world, "svf")
    assert j.state == "done", j.error
    aoi = areas.aoi_2180(world["bbox"])
    files = sorted(s.raw_dir.glob("fake-src/2020/*.laz"))
    b = aoi.bounds
    pts, _ = read_ground(files, (b[0] - 60, b[1] - 60, b[2] + 60, b[3] + 60))
    _, full, _ = compute_products(pts, aoi, ProcessParams(kinds=("dtm", "slope", "svf")))
    _, inc, _ = compute_from_dtm(full["dtm"], aoi, ProcessParams(kinds=("slope", "svf")))
    assert set(inc) == {"slope", "svf"}
    for k in inc:  # identical where no neighbour lies outside the area (> 20 m from the edge)
        diff = np.abs(full[k][60:-60, 60:-60] - inc[k][60:-60, 60:-60])
        assert np.nanmax(diff) < 1e-4


def test_dtm_tile_is_a_stretched_elevation_ramp(world):  # noqa: F811
    import io
    import math

    from PIL import Image

    j, _ = _run_layers(world, "dtm")
    assert j.state == "done", j.error
    c = TestClient(create_app(world["settings"]))
    dtm = next(lay for lay in c.get(f"/api/locations/{j.location_id}/layers").json())
    lo, hi = dtm["provenance"]["display_range"]
    assert hi > lo  # percentile stretch over the area's own heights
    w, s, e, n = world["bbox"]
    lon, lat = (w + e) / 2, (s + n) / 2
    z, k = 17, 2**17
    x = int((lon + 180) / 360 * k)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * k)

    def tile(extra=""):
        r = c.get(dtm["tile_url"].format(z=z, x=x, y=y) + extra)
        assert r.status_code == 200
        return Image.open(io.BytesIO(r.content))

    plain, shaded = tile(), tile("?shade=0.8")
    assert plain.mode == "RGBA" and plain.getchannel("A").getextrema()[1] == 255
    a = np.asarray(plain).reshape(-1, 4)
    assert len({tuple(p[:3]) for p in a[a[:, 3] == 255]}) > 20  # a ramp, not one flat colour
    assert not np.array_equal(np.asarray(plain), np.asarray(shaded))
    assert c.get(dtm["tile_url"].format(z=z, x=x, y=y) + "?shade=3").status_code == 422
