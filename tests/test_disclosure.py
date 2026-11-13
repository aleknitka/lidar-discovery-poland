from __future__ import annotations

import math

import pytest

from lidar_discovery.catalog.disclosure import (
    _to_2180,
    apply_to_feature,
    default_disclosure,
    generalise_geometry,
    snap_point_to_grid,
    visible,
)
from lidar_discovery.catalog.repo import ValidationError, candidate_from_feature


def feat(disclosure, geom=None):
    return {
        "type": "Feature",
        "geometry": geom or {"type": "Point", "coordinates": [22.6191, 49.1669]},
        "properties": {"id": "x", "disclosure": disclosure},
    }


def test_defaults():
    assert default_disclosure("cemetery") == "restricted"
    assert default_disclosure("house_platform") == "public"
    assert default_disclosure(None) == "public"


def test_visibility():
    assert visible("restricted", False)
    assert not visible("restricted", True)
    assert visible("generalised", True)


def test_public_mode_filters():
    assert apply_to_feature(feat("restricted"), True) is None
    assert apply_to_feature(feat("restricted"), False) is not None
    assert apply_to_feature(feat("public"), True)["geometry"]["coordinates"] == [22.6191, 49.1669]


def test_generalised_snaps_to_1km_cell_centre():
    f = apply_to_feature(feat("generalised"), True)
    lon, lat = f["geometry"]["coordinates"]
    assert f["properties"]["generalised"] is True
    x, y = _to_2180.transform(lon, lat)
    assert math.isclose(x % 1000, 500, abs_tol=1e-3)
    assert math.isclose(y % 1000, 500, abs_tol=1e-3)
    # points inside the same cell snap to the same place; original is within ~0.71 km
    x0, y0 = _to_2180.transform(22.6191, 49.1669)
    assert math.hypot(x - x0, y - y0) < 710
    assert snap_point_to_grid(22.6191, 49.1669) == snap_point_to_grid(22.6192, 49.1670)


def test_generalise_polygon_becomes_point():
    poly = {
        "type": "Polygon",
        "coordinates": [
            [[22.61, 49.16], [22.62, 49.16], [22.62, 49.17], [22.61, 49.17], [22.61, 49.16]]
        ],
    }
    g = generalise_geometry(poly)
    assert g["type"] == "Point"


def test_candidate_default_disclosure_and_validation():
    pt = {"type": "Point", "coordinates": [22.6, 49.1]}
    c = candidate_from_feature({"geometry": pt, "properties": {"morph_class": "cemetery"}})
    assert c.disclosure == "restricted"
    c = candidate_from_feature(
        {"geometry": pt, "properties": {"morph_class": "cemetery", "disclosure": "generalised"}}
    )
    assert c.disclosure == "generalised"
    with pytest.raises(ValidationError):
        candidate_from_feature({"geometry": pt, "properties": {"morph_class": "dinosaur"}})
    with pytest.raises(ValidationError):
        candidate_from_feature({"geometry": pt, "properties": {"reality_confidence": 1.5}})
    with pytest.raises(ValidationError):
        candidate_from_feature({"properties": {}})
