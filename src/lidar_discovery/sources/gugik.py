"""GUGiK (geoportal.gov.pl) WFS tile indexes for airborne LiDAR point clouds."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from pyproj import Transformer
from shapely import wkt
from shapely.geometry import Polygon, box

from lidar_discovery.config import Settings
from lidar_discovery.sources.base import TileRef, register_source
from lidar_discovery.sources.download import download_file
from lidar_discovery.sources.wfs import WfsClient, WfsFeature, year_from_type_name

_to_4326 = Transformer.from_crs(2180, 4326, always_xy=True)


def feature_to_tile(source_id: str, feat: WfsFeature, year_hint: int | None = None) -> TileRef:
    a = feat.attrs
    poly = Polygon(feat.rings[0]) if feat.rings else None
    bbox = feat.bbox or (poly.bounds if poly is not None else (0.0, 0.0, 0.0, 0.0))
    year = int(a["akt_rok"]) if a.get("akt_rok", "").isdigit() else year_hint
    return TileRef(
        source_id=source_id,
        tile_id=feat.gml_id.rsplit(".", 1)[-1] if feat.gml_id else a.get("godlo", ""),
        godlo=a.get("godlo"),
        year=year,
        acq_date=a.get("akt_data") or None,
        nominal_density=a.get("char_przestrz") or None,
        bbox_2180=tuple(bbox),  # type: ignore[arg-type]
        url=a.get("url_do_pobrania", ""),
        crs_h=a.get("uklad_h") or None,
        footprint_wkt=poly.wkt if poly is not None else None,
    )


class GugikWfsSource:
    """Base adapter: one WFS layer per acquisition year."""

    id = ""
    name = ""
    description = ""
    crs_h: str | None = None
    wfs_url = ""
    layer_prefix = "gugik:SkorowidzDanychPomiarowychLIDAR"

    def __init__(self, settings: Settings, client: WfsClient | None = None) -> None:
        self.settings = settings
        self.wfs = client or WfsClient(
            self.wfs_url,
            cache_dir=settings.cache_dir / "wfs" / self.id,
            timeout=settings.http_timeout_s,
        )

    def year_layers(self) -> dict[int, str]:
        out = {}
        for n in self.wfs.feature_types():
            if n.startswith(self.layer_prefix):
                y = year_from_type_name(n)
                if y:
                    out[y] = n
        return dict(sorted(out.items()))

    def list_tiles(self, aoi_2180: Polygon, years: list[int] | None = None) -> list[TileRef]:
        minx, miny, maxx, maxy = aoi_2180.bounds
        lon0, lat0 = _to_4326.transform(minx, miny)
        lon1, lat1 = _to_4326.transform(maxx, maxy)
        bbox = (
            f"{min(lat0, lat1):.6f},{min(lon0, lon1):.6f},"
            f"{max(lat0, lat1):.6f},{max(lon0, lon1):.6f},urn:ogc:def:crs:EPSG::4326"
        )
        layers = {y: n for y, n in self.year_layers().items() if not years or y in years}

        def fetch(item: tuple[int, str]) -> list[TileRef]:
            y, name = item
            try:
                feats = self.wfs.get_features(name, bbox=bbox)
            except RuntimeError:
                return []
            return [feature_to_tile(self.id, f, y) for f in feats if f.attrs.get("url_do_pobrania")]

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(fetch, layers.items()))
        tiles = [t for r in results for t in r]
        out = []
        for t in tiles:  # precise filter on the footprint, not only the bbox query
            fp = wkt.loads(t.footprint_wkt) if t.footprint_wkt else box(*t.bbox_2180)
            if fp.intersects(aoi_2180):
                out.append(t)
        out.sort(key=lambda t: (t.year or 0, t.godlo or ""))
        return out

    def download(self, tile: TileRef, dest_dir: Path) -> Path:
        name = Path(urlparse(tile.url).path).name or f"{tile.tile_id}.laz"
        return download_file(tile.url, dest_dir / name, expected_size=tile.size_bytes)


@register_source("gugik-kron86")
class GugikKron86Source(GugikWfsSource):
    id = "gugik-kron86"
    name = "GUGiK ALS (KRON86)"
    description = "Airborne LiDAR point clouds, vertical datum PL-KRON86-NH, years 2010-2019"
    crs_h = "PL-KRON86-NH"
    wfs_url = (
        "https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarKRON86/WFS/Skorowidze"
    )


@register_source("gugik-evrf2007")
class GugikEvrf2007Source(GugikWfsSource):
    id = "gugik-evrf2007"
    name = "GUGiK ALS (EVRF2007)"
    description = "Airborne LiDAR point clouds, vertical datum PL-EVRF2007-NH, years 2018+"
    crs_h = "PL-EVRF2007-NH"
    wfs_url = (
        "https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarEVRF2007/WFS/Skorowidze"
    )
