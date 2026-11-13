from __future__ import annotations

import json
from pathlib import Path

import pytest
from shapely.geometry import shape
from sqlmodel import Session

from lidar_discovery.catalog import repo
from lidar_discovery.catalog.db import get_engine
from lidar_discovery.catalog.models import Location
from lidar_discovery.locations.aoi import aoi_for, to_2180
from lidar_discovery.locations.prg import norm_name, precinct_to_geojson, select_precinct
from lidar_discovery.locations.seed import import_seed
from lidar_discovery.sources.wfs import WfsFeature

SEEDS = Path(__file__).parent.parent / "seeds" / "locations.yaml"


def test_seed_import(settings):
    with Session(get_engine(settings)) as s:
        locs = import_seed(s, SEEDS)
        assert {loc.id for loc in locs} == {"carynskie", "krywe", "tworylne", "jaworzec", "zawoj"}
        for loc in repo.list_locations(s):
            dep = json.loads(loc.depopulation)
            assert dep["cause"] is None  # never assumed without a source
            prov = json.loads(loc.provenance)
            assert prov[0]["provider"] == "wikidata" and prov[0]["ref"].startswith("Q")
            assert 48.5 < loc.lat < 49.6 and 22 < loc.lon < 23
        import_seed(s, SEEDS)  # idempotent
        assert len(repo.list_locations(s)) == 5


def test_aoi_point_vs_polygon():
    loc = Location(id="a", lon=22.618, lat=49.166, aoi_buffer_m=500)
    aoi = aoi_for(loc)
    assert aoi.area == pytest.approx(3.14159 * 500**2, rel=0.01)
    poly = {
        "type": "Polygon",
        "coordinates": [
            [[22.61, 49.16], [22.62, 49.16], [22.62, 49.17], [22.61, 49.17], [22.61, 49.16]]
        ],
    }
    loc.polygon = json.dumps(poly)
    assert aoi_for(loc).area == pytest.approx(to_2180(shape(poly)).area, rel=1e-6)
    assert aoi_for(loc, "point").area == pytest.approx(3.14159 * 500**2, rel=0.01)


def test_prg_selection_and_geojson():
    ring = [(764000.0, 150000.0), (764500.0, 150000.0), (764500.0, 150500.0), (764000.0, 150000.0)]
    f1 = WfsFeature("1", {"JPT_NAZWA_": "Caryńskie"}, [ring])
    f2 = WfsFeature("2", {"JPT_NAZWA_": "Wetlina"}, [ring])
    assert norm_name("Zawój") == norm_name("zawoj") and norm_name("Łopienka") == "lopienka"
    assert select_precinct([f2, f1], "Carynskie") is f1
    assert select_precinct([f2], "Carynskie") is None
    g = precinct_to_geojson(f1)
    assert g["type"] == "Polygon" and 22 < g["coordinates"][0][0][0] < 23
