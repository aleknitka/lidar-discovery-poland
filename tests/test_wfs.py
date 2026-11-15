from __future__ import annotations

import httpx
import pytest
from shapely.geometry import box

from conftest import FIXTURES
from lidar_discovery.config import Settings
from lidar_discovery.sources import get_source, source_ids
from lidar_discovery.sources.gugik import GugikKron86Source, feature_to_tile
from lidar_discovery.sources.wfs import (
    WfsClient,
    parse_capabilities,
    parse_feature_collection,
    year_from_type_name,
)

CAPS = """<?xml version="1.0"?>
<WFS_Capabilities xmlns="http://www.opengis.net/wfs/2.0">
 <FeatureTypeList>
  <FeatureType><Name>gugik:SkorowidzDanychPomiarowychLIDAR2012</Name></FeatureType>
  <FeatureType><Name>gugik:SkorowidzDanychPomiarowychLIDAR2023</Name></FeatureType>
 </FeatureTypeList>
</WFS_Capabilities>"""


def test_parse_capabilities_and_year():
    names = parse_capabilities(CAPS)
    assert names == [
        "gugik:SkorowidzDanychPomiarowychLIDAR2012",
        "gugik:SkorowidzDanychPomiarowychLIDAR2023",
    ]
    assert [year_from_type_name(n) for n in names] == [2012, 2023]


def test_parse_feature_collection_fixture():
    feats, nxt = parse_feature_collection((FIXTURES / "kron86_2012_sample.xml").read_text("utf8"))
    assert len(feats) == 3
    assert nxt and "STARTINDEX=3" in nxt
    f = feats[0]
    assert f.attrs["godlo"] == "M-34-106-A-d-3-1-1"
    assert f.attrs["akt_rok"] == "2012"
    assert f.attrs["char_przestrz"] == "4 p/m2"
    assert f.attrs["akt_data"] == "2012-10-15"  # nested gml:timePosition
    assert f.attrs["url_do_pobrania"].endswith("5063_353884_M-34-106-A-d-3-1-1.laz")
    # EPSG:2180 URN axis order is (northing, easting): parsed to (E, N)
    minx, miny, maxx, maxy = f.bbox
    assert 700_000 < minx < 800_000 and 100_000 < miny < 200_000
    assert maxx > minx and maxy > miny
    assert len(f.rings[0]) == 9


def test_feature_to_tile():
    feats, _ = parse_feature_collection((FIXTURES / "kron86_2012_sample.xml").read_text("utf8"))
    t = feature_to_tile("gugik-kron86", feats[0])
    assert t.year == 2012 and t.tile_id == "353884"
    assert t.crs_h == "PL-KRON86-NH"
    assert t.nominal_density == "4 p/m2"
    assert t.url.startswith("https://opendata.geoportal.gov.pl/")


def test_exception_report_raises():
    xml = (
        '<ows:ExceptionReport xmlns:ows="http://www.opengis.net/ows/1.1">'
        "<ows:Exception><ows:ExceptionText>boom</ows:ExceptionText></ows:Exception>"
        "</ows:ExceptionReport>"
    )
    with pytest.raises(RuntimeError, match="boom"):
        parse_feature_collection(xml)


def test_registry():
    assert {"gugik-kron86", "gugik-evrf2007", "local-laz", "sk-zbgis"} <= set(source_ids())
    with pytest.raises(KeyError):
        get_source("nope", Settings())


def test_list_tiles_with_paging_and_cache(tmp_path):
    sample = (FIXTURES / "kron86_2012_sample.xml").read_text("utf8")
    last_page = sample.replace('next="', 'nextx="')  # no next link -> stops
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        q = dict(request.url.params)
        if q.get("request") == "GetCapabilities":
            return httpx.Response(200, text=CAPS)
        if "STARTINDEX" in q or "startindex" in {k.lower() for k in q}:
            return httpx.Response(200, text=last_page)
        return httpx.Response(200, text=sample)

    # page_size=3 in the sample: first page is "full", so the client follows `next`
    client = WfsClient(
        "https://example.invalid/wfs",
        cache_dir=tmp_path / "c",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    feats = client.get_features("gugik:x", bbox="1,2,3,4", page_size=3)
    assert len(feats) == 6
    n_calls = len(calls)
    assert len(client.get_features("gugik:x", bbox="1,2,3,4", page_size=3)) == 6
    assert len(calls) == n_calls  # served from the on-disk cache

    # adapter-level: whole-AOI filter on the footprint
    settings = Settings(data_dir=tmp_path / "d")
    src = GugikKron86Source(settings, client=client)
    f0 = feats[0]
    aoi = box(*f0.bbox).centroid.buffer(10)
    tiles = src.list_tiles(aoi, years=[2012])
    assert tiles
    assert all(t.year == 2012 for t in tiles)
    assert "M-34-106-A-d-3-1-1" in {t.godlo for t in tiles}


@pytest.mark.network
def test_live_coverage_carynskie(tmp_path):
    from conftest import _E, _N

    settings = Settings(data_dir=tmp_path / "d")
    src = get_source("gugik-kron86", settings)
    tiles = src.list_tiles(box(_E - 500, _N - 500, _E + 500, _N + 500))
    assert tiles and all(t.url.startswith("http") for t in tiles)
