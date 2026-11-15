from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from shapely.geometry import box
from sqlmodel import Session

from conftest import LAT, LON, synthetic_ground, write_laz
from lidar_discovery.api.app import create_app
from lidar_discovery.catalog import repo
from lidar_discovery.catalog.db import get_engine
from lidar_discovery.catalog.models import Location, dumps
from lidar_discovery.processing.pipeline import ProcessParams, process_aoi

PT = {"type": "Point", "coordinates": [LON, LAT]}


def tile_xy(lon: float, lat: float, z: int) -> tuple[int, int]:
    import math

    n = 2**z
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


@pytest.fixture
def seeded(settings, centre):
    e, n = centre
    with Session(get_engine(settings)) as s:
        repo.upsert_location(
            s,
            Location(
                id="carynskie",
                names=dumps({"pl": "Caryńskie"}),
                lon=LON,
                lat=LAT,
                aoi_buffer_m=50,
                depopulation=dumps({"year": None, "cause": None, "source_url": None}),
                provenance=dumps([{"provider": "wikidata", "ref": "Q302781"}]),
            ),
        )
        repo.upsert_location(
            s, Location(id="secret", names="{}", lon=LON + 0.01, lat=LAT, disclosure="restricted")
        )
        repo.upsert_location(
            s, Location(id="fuzzy", names="{}", lon=LON + 0.02, lat=LAT, disclosure="generalised")
        )
    pts = synthetic_ground(e, n, half=100, density=3)
    laz = write_laz(settings.raw_dir / "local-laz" / "2020" / "t.laz", pts)
    res = process_aoi(
        settings, "carynskie", box(e - 50, n - 50, e + 50, n + 50), "local-laz", 2020, [laz],
        "PL-EVRF2007-NH", ProcessParams(kinds=("dtm", "svf", "lrm")),
    )  # fmt: skip
    with Session(get_engine(settings)) as s:
        for p in res.products:
            repo.add_product(s, p)
    return settings


def test_health_sources_empty(settings):
    c = TestClient(create_app(settings))
    assert c.get("/api/health").json()["status"] == "ok"
    ids = {s["id"] for s in c.get("/api/sources").json()}
    assert {"gugik-kron86", "gugik-evrf2007", "local-laz"} <= ids
    assert c.get("/api/locations").json() == {"type": "FeatureCollection", "features": []}
    assert c.get("/api/locations/nope").status_code == 404
    assert c.get("/api/locations/nope").json()["detail"]


def test_locations_and_layers(seeded):
    c = TestClient(create_app(seeded))
    fc = c.get("/api/locations").json()
    by_id = {f["properties"]["id"]: f for f in fc["features"]}
    assert by_id["carynskie"]["properties"]["has_products"] is True
    assert by_id["carynskie"]["properties"]["names"]["pl"] == "Caryńskie"
    assert by_id["secret"]["properties"]["has_products"] is False
    assert by_id["carynskie"]["geometry"]["coordinates"] == [LON, LAT]
    one = c.get("/api/locations/carynskie").json()
    assert one["properties"]["provenance"][0]["ref"] == "Q302781"
    layers = c.get("/api/locations/carynskie/layers").json()
    assert {lay["kind"] for lay in layers} == {"dtm", "svf", "lrm"}
    lay = layers[0]
    assert lay["epoch"] == 2020 and lay["source_id"] == "local-laz" and lay["resolution_m"] == 0.5
    assert len(lay["bounds"]) == 4 and lay["bounds"][0] < LON < lay["bounds"][2]
    assert lay["tile_url"] == f"/api/layers/{lay['id']}/tiles/{{z}}/{{x}}/{{y}}.png"
    assert "inputs" in lay["provenance"]


def test_tiles(seeded):
    c = TestClient(create_app(seeded))
    lid = "carynskie-local-laz-2020-svf"
    for z in (14, 17):
        x, y = tile_xy(LON, LAT, z)
        r = c.get(f"/api/layers/{lid}/tiles/{z}/{x}/{y}.png")
        assert r.status_code == 200 and r.headers["content-type"] == "image/png"
        img = Image.open(io.BytesIO(r.content))
        assert img.size == (256, 256) and img.mode == "LA"
        alpha = img.getchannel("A")
        assert alpha.getextrema()[1] == 255  # some data at the location
    # far outside bounds -> fully transparent
    x, y = tile_xy(LON + 1, LAT, 14)
    r = c.get(f"/api/layers/{lid}/tiles/14/{x}/{y}.png")
    assert r.status_code == 200
    assert Image.open(io.BytesIO(r.content)).getchannel("A").getextrema() == (0, 0)
    assert c.get("/api/layers/missing/tiles/1/0/0.png").status_code == 404
    assert c.get(f"/api/layers/{lid}/tiles/1/9/9.png").status_code == 400


def test_candidate_crud(seeded):
    c = TestClient(create_app(seeded))
    body = {
        "type": "Feature",
        "geometry": PT,
        "properties": {"location_id": "carynskie", "morph_class": "cellar_pit"},
    }
    r = c.post("/api/candidates", json=body)
    assert r.status_code == 201
    cand = r.json()
    cid = cand["id"]
    assert cand["properties"]["review_status"] == "proposed"
    assert cand["properties"]["reality"] == "unassessed"
    assert cand["properties"]["origin"] == "manual"
    patch = {
        "review_status": "accepted",
        "reality": "anthropogenic",
        "reality_confidence": 0.7,
        "reviewer_notes": "LRM + 1850s map",
        "documentation_status": [{"source": "cadastre-1850s", "ref": "x", "found": True}],
    }
    r = c.patch(f"/api/candidates/{cid}", json={"properties": patch})
    assert r.status_code == 200
    p = r.json()["properties"]
    assert p["review_status"] == "accepted" and p["reality_confidence"] == 0.7
    assert p["documentation_status"][0]["found"] is True
    assert r.json()["geometry"] == PT  # untouched by a partial patch
    assert len(c.get("/api/candidates?review_status=accepted").json()["features"]) == 1
    assert len(c.get("/api/candidates?review_status=rejected").json()["features"]) == 0
    assert len(c.get("/api/candidates?location_id=carynskie").json()["features"]) == 1
    # validation errors
    assert c.post("/api/candidates", json={"type": "Feature", "properties": {}}).status_code == 422
    bad = {**body, "properties": {"morph_class": "dinosaur"}}
    r = c.post("/api/candidates", json=bad)
    assert r.status_code == 422 and "morph_class" in r.json()["detail"]
    assert c.patch("/api/candidates/zzz", json={"properties": {}}).status_code == 404
    bad_loc = {**body, "properties": {"location_id": "nowhere"}}
    assert c.post("/api/candidates", json=bad_loc).status_code == 422
    assert (
        c.patch(f"/api/candidates/{cid}", json={"properties": {"review_status": "x"}}).status_code
        == 422
    )


def test_public_mode(seeded):
    seeded_public = seeded.model_copy(update={"public_mode": True})
    c = TestClient(create_app(seeded_public))
    assert c.get("/api/health").json()["public_mode"] is True
    ids = {f["properties"]["id"] for f in c.get("/api/locations").json()["features"]}
    assert ids == {"carynskie", "fuzzy"}  # restricted hidden
    assert c.get("/api/locations/secret").status_code == 404
    fuzzy = c.get("/api/locations/fuzzy").json()
    lon, lat = fuzzy["geometry"]["coordinates"]
    assert (lon, lat) != (LON + 0.02, LAT) and fuzzy["properties"]["generalised"] is True
    assert c.get("/api/locations/fuzzy/layers").json() == []
    # writes are refused in public mode
    assert c.post("/api/candidates", json={"geometry": PT, "properties": {}}).status_code == 403

    # candidates: seed via internal mode, then read via public mode
    internal = TestClient(create_app(seeded))
    for disc, mc in (("public", "terrace"), ("generalised", "house_platform"), (None, "cemetery")):
        props = {"morph_class": mc, **({"disclosure": disc} if disc else {})}
        assert (
            internal.post("/api/candidates", json={"geometry": PT, "properties": props}).status_code
            == 201
        )
    assert len(internal.get("/api/candidates").json()["features"]) == 3
    feats = c.get("/api/candidates").json()["features"]
    by_class = {f["properties"]["morph_class"]: f for f in feats}
    assert set(by_class) == {"terrace", "house_platform"}  # cemetery defaults to restricted
    assert by_class["terrace"]["geometry"] == PT
    assert by_class["house_platform"]["geometry"] != PT
    assert by_class["house_platform"]["properties"]["generalised"] is True


def test_cors_headers(settings):
    c = TestClient(create_app(settings))
    r = c.options(
        "/api/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
