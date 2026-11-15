"""PRG cadastral-precinct provider (WFS ms:A06_Granice_obrebow_ewidencyjnych)."""

from __future__ import annotations

import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shapely.geometry import Point, Polygon, mapping

from lidar_discovery.locations.aoi import to_4326
from lidar_discovery.sources.wfs import WfsClient, WfsFeature

PRG_URL = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries"
PRG_LAYER = "ms:A06_Granice_obrebow_ewidencyjnych"


def norm_name(s: str) -> str:
    s = s.casefold().replace("ł", "l")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def precinct_name(f: WfsFeature) -> str:
    return f.attrs.get("JPT_NAZWA_", "")


def select_precinct(
    feats: list[WfsFeature], name: str, near_2180: tuple[float, float] | None = None
) -> WfsFeature | None:
    want = norm_name(name)
    hits = [f for f in feats if f.rings and norm_name(precinct_name(f)) == want]
    if not hits:
        return None
    if len(hits) > 1 and near_2180:
        p = Point(near_2180)
        hits.sort(key=lambda f: Polygon(f.rings[0]).distance(p))
    return hits[0]


def precinct_to_geojson(f: WfsFeature, simplify_m: float = 1.0) -> dict[str, Any]:
    poly = Polygon(f.rings[0])
    if not poly.is_valid:
        poly = poly.buffer(0)
    poly = poly.simplify(simplify_m)
    g = to_4326(poly)
    return mapping(g)


def fetch_precinct(
    name: str,
    bbox_wgs84: tuple[float, float, float, float],
    cache_dir: Path | None = None,
    client: WfsClient | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fetch the precinct called `name` inside bbox (minlon, minlat, maxlon, maxlat).

    Returns (GeoJSON geometry in WGS84, provenance entry). Raises LookupError if not found.
    """
    client = client or WfsClient(PRG_URL, cache_dir=cache_dir)
    minlon, minlat, maxlon, maxlat = bbox_wgs84
    bbox = f"{minlat},{minlon},{maxlat},{maxlon},urn:ogc:def:crs:EPSG::4326"
    feats = client.get_features(PRG_LAYER, bbox=bbox, page_size=1000)
    centre = None
    f = select_precinct(feats, name, centre)
    if f is None:
        found = sorted({precinct_name(x) for x in feats})
        raise LookupError(f"no precinct named {name!r} in bbox; found: {found}")
    prov = {
        "provider": "prg-wfs",
        "ref": f"{PRG_LAYER}:{f.attrs.get('JPT_KOD_JE', '')}",
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "name": precinct_name(f),
    }
    return precinct_to_geojson(f), prov
