"""Area estimate + fetch jobs. All HTTP goes through a mock transport; no network."""

from __future__ import annotations

import io
import sqlite3
import threading
import time

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pyproj import Transformer
from shapely.geometry import Polygon

from conftest import synthetic_ground, write_laz
from lidar_discovery import areas, jobs
from lidar_discovery.api.app import create_app
from lidar_discovery.catalog.db import get_engine
from lidar_discovery.config import Settings
from lidar_discovery.sources import download
from lidar_discovery.sources.base import TileRef, register_source

HOST = "https://files.example.test/laz/"
_to_4326 = Transformer.from_crs(2180, 4326, always_xy=True)


class _Chunks(httpx.SyncByteStream):
    def __init__(self, data: bytes, size: int = 16384) -> None:
        self.data, self.size = data, size

    def __iter__(self):
        for i in range(0, len(self.data), self.size):
            yield self.data[i : i + self.size]


class FakeServer:
    """HEAD + GET with Range support, like opendata.geoportal.gov.pl."""

    def __init__(self, files: dict[str, bytes]) -> None:
        self.files = files
        self.gets: list[tuple[str, str | None]] = []
        self.heads = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        name = request.url.path.rsplit("/", 1)[-1]
        data = self.files.get(name)
        if data is None:
            return httpx.Response(404)
        if request.method == "HEAD":
            self.heads += 1
            return httpx.Response(200, headers={"content-length": str(len(data)), "etag": '"e1"'})
        rng = request.headers.get("range")
        self.gets.append((name, rng))
        if rng:
            start = int(rng.split("=")[1].split("-")[0])
            body = data[start:]
            return httpx.Response(
                206,
                headers={
                    "content-range": f"bytes {start}-{len(data) - 1}/{len(data)}",
                    "content-length": str(len(body)),
                },
                stream=_Chunks(body),
            )
        return httpx.Response(200, headers={"content-length": str(len(data))}, stream=_Chunks(data))


@pytest.fixture
def world(settings, centre, monkeypatch, tmp_path):
    """Fake source with two sheets (A west, B east of the centre) in two epochs."""
    cx, cy = centre
    sheet_a = (cx - 300, cy - 300, cx, cy + 300)
    sheet_b = (cx, cy - 300, cx + 300, cy + 300)
    files = {}
    for name, (x0, y0, x1, y1), seed in (("A", sheet_a, 1), ("B", sheet_b, 2)):
        pts = synthetic_ground(
            (x0 + x1) / 2, (y0 + y1) / 2, half=150, density=2, pit=None, seed=seed
        )
        p = write_laz(tmp_path / f"{name}.laz", pts)
        files[f"{name}-2020.laz"] = p.read_bytes()
        files[f"{name}-2012.laz"] = p.read_bytes()
    server = FakeServer(files)

    @register_source("fake-src")
    class Fake:
        id = "fake-src"
        name = "fake"
        description = "fake"
        crs_h = "TEST-H"

        def __init__(self, settings: Settings) -> None:
            pass

        def list_tiles(self, aoi, years=None):
            out = []
            for year in (2012, 2020):
                for name, bb in (("A", sheet_a), ("B", sheet_b)):
                    if Polygon(
                        [(bb[0], bb[1]), (bb[2], bb[1]), (bb[2], bb[3]), (bb[0], bb[3])]
                    ).intersects(aoi):
                        out.append(
                            TileRef(
                                source_id="fake-src", tile_id=name, godlo=f"{name}-{year}",
                                year=year, nominal_density="4 p/m2", bbox_2180=bb,
                                url=f"{HOST}{name}-{year}.laz", crs_h="TEST-H",
                            )
                        )  # fmt: skip
            return out

        def download(self, tile, dest_dir):  # pragma: no cover
            raise NotImplementedError

    monkeypatch.setattr(areas, "AREA_SOURCES", ("fake-src",))
    monkeypatch.setattr(
        download,
        "make_client",
        lambda timeout=60.0: httpx.Client(transport=httpx.MockTransport(server)),
    )
    monkeypatch.setattr(jobs, "PROGRESS_INTERVAL_S", 0.0)
    monkeypatch.setattr(jobs, "CHUNK", 65536)
    x0, y0 = _to_4326.transform(cx - 60, cy - 60)
    x1, y1 = _to_4326.transform(cx + 60, cy + 60)
    bbox = (x0, y0, x1, y1)
    return {"settings": settings, "server": server, "bbox": bbox, "files": files}


def _run(w, **kw):
    job, _ = jobs.create_fetch_job(w["settings"], w["bbox"], "fake-src", 2020)
    updates: list[dict] = []
    j = jobs.run_fetch_job(
        w["settings"],
        job.id,
        kw.get("cancel"),
        lambda d: (updates.append(d), kw.get("hook", lambda d: None)(d)),
    )
    return j, updates


def test_estimate_totals_and_cache_detection(world):
    s, bbox = world["settings"], world["bbox"]
    est = areas.estimate_area(s, bbox)
    assert est["year"] == 2020 and est["source_id"] == "fake-src"  # newest epoch by default
    assert [e["year"] for e in est["epochs"]] == [2020, 2012]
    assert est["sheets"] == 2 and 0.01 < est["area_km2"] < 0.02
    total = sum(len(world["files"][f"{n}-2020.laz"]) for n in "AB")
    assert est["bytes_total"] == total and est["bytes_cached"] == 0
    assert est["bytes_to_download"] == total
    assert est["tiles"][0]["footprint"]["type"] == "Polygon" and not est["tiles"][0]["cached"]
    # wrong size on disk is NOT cached; matching size is
    a = s.raw_dir / "fake-src" / "2020" / "A-2020.laz"
    a.parent.mkdir(parents=True)
    a.write_bytes(b"short")
    assert not areas.estimate_area(s, bbox)["tiles"][0]["cached"]
    a.write_bytes(world["files"]["A-2020.laz"])
    est = areas.estimate_area(s, bbox)
    assert est["tiles"][0]["cached"] and est["bytes_cached"] == len(world["files"]["A-2020.laz"])
    assert est["bytes_to_download"] == len(world["files"]["B-2020.laz"])
    assert areas.estimate_area(s, bbox, "fake-src", 2012)["year"] == 2012
    assert world["server"].heads == 4  # HEAD results are cached in the DB


def test_estimate_limits_422(world):
    c = TestClient(create_app(world["settings"]))
    w, s, e, n = world["bbox"]
    q = f"/api/areas/estimate?bbox={w},{s},{e},{n}"
    assert c.get(q).status_code == 200
    r = c.get(f"/api/areas/estimate?bbox={w},{s},{w + 0.1},{s + 0.1}")
    assert r.status_code == 422 and r.json()["estimate"]["area_km2"] > 6
    assert r.json()["estimate"]["limits"]["max_area_km2"] == 6
    small = world["settings"].model_copy(update={"max_fetch_bytes": 1000})
    r = TestClient(create_app(small)).get(q)
    assert r.status_code == 422 and r.json()["estimate"]["bytes_total"] > 1000
    assert c.get("/api/areas/estimate?bbox=1,2,3").status_code == 422
    r = c.post("/api/areas/fetch", json={"bbox": [w, s, w + 0.1, s + 0.1]})
    assert r.status_code == 422


def test_job_lifecycle_progress_and_area_location(world):
    s = world["settings"]
    j, updates = _run(world)
    assert j.state == "done", j.error
    states = [u["state"] for u in updates]
    assert states[0] == "listing" and states[-1] == "done"
    assert "downloading" in states and "processing" in states
    done = [u["bytes_done"] for u in updates if u["state"] == "downloading"]
    assert done == sorted(done) and len(done) > 3 and done[-1] == j.bytes_total
    steps = [u["step_name"] for u in updates if u["state"] == "processing" and u["step_name"]]
    # default layers: DTM, hillshade, SVF, ground density
    assert steps == ["ground points", "dtm", "density", "hillshade", "svf", "write"]
    assert j.tiles_done == j.tiles_total == 2 and j.finished_at
    # area Location
    c = TestClient(create_app(s))
    loc = c.get(f"/api/locations/{j.location_id}").json()["properties"]
    assert j.location_id.startswith("area-") and len(j.location_id) == 13
    assert loc["kind"] == "area" and loc["disclosure"] == "restricted"
    assert loc["names"]["other"].startswith("Area 49.")
    assert loc["has_products"] is True
    layers = c.get(f"/api/locations/{j.location_id}/layers").json()
    assert {lay["kind"] for lay in layers} == {"svf", "hillshade", "dtm", "ground_density"}
    assert all(lay["provenance"]["cache_key"] for lay in layers)
    svf = next(lay for lay in layers if lay["kind"] == "svf")
    lon, lat = (world["bbox"][0] + world["bbox"][2]) / 2, (world["bbox"][1] + world["bbox"][3]) / 2
    import math

    z, n = 17, 2**17
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    r = c.get(svf["tile_url"].format(z=z, x=x, y=y))
    assert Image.open(io.BytesIO(r.content)).getchannel("A").getextrema()[1] == 255


def test_cache_hit_is_instant_via_api(world):
    s = world["settings"]
    with TestClient(create_app(s)) as c:
        w, so, e, n = world["bbox"]
        body = {"bbox": [w, so, e, n], "source_id": "fake-src", "year": 2020}

        def wait(job_id):
            for _ in range(600):
                j = c.get(f"/api/jobs/{job_id}").json()
                if j["state"] in ("done", "failed", "cancelled"):
                    return j
                time.sleep(0.2)
            raise AssertionError("timeout")

        r = c.post("/api/areas/fetch", json=body)
        assert r.status_code == 202
        j1 = wait(r.json()["id"])
        assert j1["state"] == "done", j1["error"]
        assert j1["message"] == "done"
        gets = len(world["server"].gets)
        t0 = time.perf_counter()
        j2 = wait(c.post("/api/areas/fetch", json=body).json()["id"])
        assert j2["state"] == "done" and j2["message"] == "cached"
        assert time.perf_counter() - t0 < 3
        assert len(world["server"].gets) == gets and j2["location_id"] == j1["location_id"]
        assert c.get("/api/jobs?active=true").json() == []
        assert {j["id"] for j in c.get("/api/jobs").json()} >= {j1["id"], j2["id"]}
        assert c.get("/api/jobs/nope").status_code == 404
        assert c.get(f"/api/areas/estimate?bbox={w},{so},{e},{n}").json()["processed"] is True


def test_cancel_then_resume_from_part_files(world):
    s = world["settings"]
    cancel = threading.Event()

    def hook(d):
        if d["state"] == "downloading" and d["bytes_done"] > 50_000:
            cancel.set()

    j, _ = _run(world, cancel=cancel, hook=hook)
    assert j.state == "cancelled" and j.finished_at
    parts = list((s.raw_dir / "fake-src" / "2020").glob("*.part"))
    assert parts and all(p.stat().st_size > 0 for p in parts)  # kept for resume
    world["server"].gets.clear()
    j2, _ = _run(world)
    assert j2.state == "done", j2.error
    assert any(rng and not rng.endswith("=0-") for _, rng in world["server"].gets)  # Range resume
    assert not list((s.raw_dir / "fake-src" / "2020").glob("*.part"))
    for n in "AB":
        assert (s.raw_dir / "fake-src" / "2020" / f"{n}-2020.laz").read_bytes() == world["files"][
            f"{n}-2020.laz"
        ]


def test_cancel_via_api_when_queued_and_unknown(world):
    s = world["settings"]
    c = TestClient(create_app(s))
    assert c.post("/api/jobs/nope/cancel").status_code == 404
    job, _ = jobs.create_fetch_job(s, world["bbox"], "fake-src", 2020)  # never submitted
    r = c.post(f"/api/jobs/{job.id}/cancel")
    assert r.json()["state"] == "cancelled"


def test_interrupted_jobs_failed_on_startup(world):
    s = world["settings"]
    job, _ = jobs.create_fetch_job(s, world["bbox"], "fake-src", 2020)
    jobs.update_job(s, job.id, state="downloading")
    with TestClient(create_app(s)) as c:  # lifespan startup
        j = c.get(f"/api/jobs/{job.id}").json()
    assert j["state"] == "failed" and j["error"] == "interrupted"


def test_identical_active_job_is_reused(world):
    s = world["settings"]
    a, created_a = jobs.create_fetch_job(s, world["bbox"], "fake-src", 2020)
    b, created_b = jobs.create_fetch_job(s, world["bbox"], "fake-src", 2020)
    assert created_a and not created_b and a.id == b.id


def test_location_kind_migration(tmp_path):
    data = tmp_path / "old"
    data.mkdir()
    con = sqlite3.connect(data / "catalog.sqlite")
    con.execute(
        "CREATE TABLE location (id VARCHAR PRIMARY KEY, names VARCHAR, lon FLOAT, lat FLOAT, "
        "polygon VARCHAR, aoi_buffer_m FLOAT, depopulation VARCHAR, provenance VARCHAR, "
        "disclosure VARCHAR, notes VARCHAR)"
    )
    con.execute("INSERT INTO location (id, names, lon, lat) VALUES ('x', '{}', 1, 2)")
    con.commit()
    con.close()
    eng = get_engine(Settings(data_dir=data))
    with eng.connect() as conn:
        assert conn.exec_driver_sql("SELECT kind FROM location").fetchall() == [("village",)]
