"""Viewport areas ("Get data for this view"): bbox -> sheets -> sizes/cache state -> estimate.

Reuses the source adapters (`list_tiles`), the WFS response cache (inside the adapters), the
`TileCache` table (HEAD results) and the raw-file layout `data/raw/<source>/<year>/<file>`.
"""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pyproj import Transformer
from shapely import wkt
from shapely.geometry import Polygon, box, mapping

from lidar_discovery.catalog import repo
from lidar_discovery.catalog.db import session_scope
from lidar_discovery.catalog.models import Location, Product, dumps
from lidar_discovery.config import Settings
from lidar_discovery.locations.aoi import to_4326
from lidar_discovery.processing.pipeline import (
    PIPELINE_VERSION,
    ProcessParams,
    estimate_processing_s,
    normalise_layers,
)
from lidar_discovery.sources import download
from lidar_discovery.sources.base import TileRef, get_source

# Sources searched for area fetches (a module variable so tests can swap it).
AREA_SOURCES: tuple[str, ...] = ("gugik-kron86", "gugik-evrf2007")
SIZE_TTL_S = 30 * 86400

_to_2180 = Transformer.from_crs(4326, 2180, always_xy=True)
_to_4326 = Transformer.from_crs(2180, 4326, always_xy=True)

BBox = tuple[float, float, float, float]


class AreaError(ValueError):
    """Invalid request (HTTP 422)."""

    def __init__(self, message: str, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.payload = payload or {}


def parse_bbox(text: str | list[float] | tuple[float, ...]) -> BBox:
    try:
        vals = [float(v) for v in (text.split(",") if isinstance(text, str) else text)]
    except ValueError:
        raise AreaError("bbox must be four numbers: west,south,east,north") from None
    if len(vals) != 4:
        raise AreaError("bbox must be four numbers: west,south,east,north")
    w, s, e, n = vals
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
        raise AreaError("bbox must satisfy west < east and south < north (WGS84 degrees)")
    return w, s, e, n


def aoi_2180(bbox: BBox) -> Polygon:
    """Viewport bbox (WGS84) -> axis-aligned rectangle in EPSG:2180, rounded to 1 m."""
    w, s, e, n = bbox
    xs, ys = [], []
    for lon, lat in ((w, s), (e, s), (e, n), (w, n)):
        x, y = _to_2180.transform(lon, lat)
        xs.append(x)
        ys.append(y)
    return box(round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys)))


def area_km2(aoi: Polygon) -> float:
    return aoi.area / 1e6


def location_id_for(aoi: Polygon) -> str:
    return "area-" + hashlib.sha256(repr(tuple(aoi.bounds)).encode()).hexdigest()[:8]


def cache_key(source_id: str, year: int, aoi: Polygon, params: ProcessParams | None = None) -> str:
    """Processing cache key of an area: hash(source, year, bbox at 1 m in EPSG:2180, params,
    version). It identifies the DTM and everything derived from it, so it does NOT depend on
    which layers were requested (see `layers_key` for that): a later request for more layers
    reuses the DTM of the same key."""
    p = asdict(replace(params or ProcessParams(), kinds=ProcessParams().kinds))
    blob = json.dumps(
        [source_id, year, [round(v) for v in aoi.bounds], p, PIPELINE_VERSION],
        sort_keys=True,
        default=list,
    )
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def layers_key(key: str, layers: tuple[str, ...]) -> str:
    """Key of one request: the area key plus the (normalised) layer set."""
    blob = json.dumps([key, sorted(layers)])
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def area_name(bbox: BBox) -> str:
    w, s, e, n = bbox
    lat, lon = (s + n) / 2, (w + e) / 2
    return f"Area {lat:.3f}{'N' if lat >= 0 else 'S'} {lon:.3f}{'E' if lon >= 0 else 'W'}"


def bbox_polygon_geojson(bbox: BBox) -> dict[str, Any]:
    w, s, e, n = bbox
    return {"type": "Polygon", "coordinates": [[[w, s], [e, s], [e, n], [w, n], [w, s]]]}


def ensure_area_location(settings: Settings, bbox: BBox, aoi: Polygon, key_ref: str) -> Location:
    """Create (or fetch) the `kind='area'` Location for a viewport."""
    lid = location_id_for(aoi)
    with session_scope(settings) as session:
        existing = repo.get_location(session, lid)
        if existing:
            return existing
        w, s, e, n = bbox
        loc = Location(
            id=lid,
            names=dumps({"other": area_name(bbox)}),
            lon=(w + e) / 2,
            lat=(s + n) / 2,
            polygon=dumps(bbox_polygon_geojson(bbox)),
            depopulation=dumps({"year": None, "cause": None, "source_url": None}),
            provenance=dumps([{"provider": "viewport", "ref": key_ref}]),
            disclosure="restricted",
            kind="area",
            notes="Created by 'Get data for this view'.",
        )
        return repo.upsert_location(session, loc)


# ------------------------------------------------------------------------------ tiles
def tile_filename(tile: TileRef) -> str:
    return Path(urlparse(tile.url).path).name or f"{tile.tile_id}.laz"


def tile_path(settings: Settings, tile: TileRef) -> Path:
    return settings.raw_dir / tile.source_id / str(tile.year) / tile_filename(tile)


def list_area_tiles(settings: Settings, aoi: Polygon) -> tuple[list[TileRef], list[str]]:
    """All sheets of all area sources intersecting `aoi` (any year). WFS responses are cached."""
    tiles: list[TileRef] = []
    errors: list[str] = []
    for sid in AREA_SOURCES:
        try:
            tiles.extend(get_source(sid, settings).list_tiles(aoi, None))
        except Exception as e:  # one source failing must not hide the other
            errors.append(f"{sid}: {e}")
    return tiles, errors


def epochs_of(tiles: list[TileRef]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int], list[TileRef]] = {}
    for t in tiles:
        if t.year:
            groups.setdefault((t.source_id, t.year), []).append(t)
    out = [
        {
            "source_id": sid,
            "year": year,
            "tiles": len(ts),
            "nominal_density": ", ".join(
                sorted({t.nominal_density for t in ts if t.nominal_density})
            ),
            "crs_h": ts[0].crs_h,
        }
        for (sid, year), ts in groups.items()
    ]
    # newest first; on equal years prefer the later source id (EVRF2007)
    out.sort(key=lambda d: (d["year"], d["source_id"]), reverse=True)
    return out


def choose_epoch(
    epochs: list[dict[str, Any]], source_id: str | None, year: int | None
) -> dict[str, Any] | None:
    pool = [
        e
        for e in epochs
        if (not source_id or e["source_id"] == source_id) and (not year or e["year"] == year)
    ]
    return pool[0] if pool else None


def tile_info(settings: Settings, tile: TileRef) -> dict[str, Any]:
    """{size, etag, last_modified} for a sheet. HEAD results are cached in the DB (TileCache)."""
    if not tile.url.startswith("http"):
        p = Path(tile.url)
        return {"size": p.stat().st_size if p.exists() else None, "etag": None}
    key = "head:" + tile.url
    with session_scope(settings) as session:
        hit = repo.cache_get(session, key, SIZE_TTL_S)
    if hit:
        return json.loads(hit)
    head = download.remote_head(tile.url)
    info: dict[str, Any] = head or {"size": tile.size_bytes, "etag": None}
    if head:  # do not cache failures
        with session_scope(settings) as session:
            repo.cache_put(session, key, json.dumps(info))
    return info


def describe_tiles(settings: Settings, tiles: list[TileRef]) -> list[dict[str, Any]]:
    """Per sheet: size, cached?, partial bytes, footprint GeoJSON (WGS84)."""
    with ThreadPoolExecutor(max_workers=4) as pool:
        infos = list(pool.map(lambda t: tile_info(settings, t), tiles))
    out = []
    for t, info in zip(tiles, infos, strict=True):
        path = tile_path(settings, t)
        size = info.get("size")
        have = path.stat().st_size if path.exists() else 0
        cached = have > 0 and (size is None or have == size)
        if cached and size is None:
            size = have
        part = path.with_name(path.name + ".part")
        partial = 0 if cached else (part.stat().st_size if part.exists() else 0)
        fp = wkt.loads(t.footprint_wkt) if t.footprint_wkt else box(*t.bbox_2180)
        out.append(
            {
                "godlo": t.godlo or t.tile_id,
                "name": tile_filename(t),
                "url": t.url,
                "source_id": t.source_id,
                "year": t.year,
                "nominal_density": t.nominal_density,
                "size_bytes": size,
                "etag": info.get("etag"),
                "cached": cached,
                "partial_bytes": min(partial, size) if size else partial,
                "footprint": mapping(to_4326(fp)),
            }
        )
    return out


def products_for_key(
    settings: Settings, loc_id: str, source_id: str, year: int, key: str
) -> dict[str, Product]:
    """{kind: Product} of this area+epoch already computed with this exact cache key and whose
    raster file is still on disk."""
    with session_scope(settings) as session:
        prods: list[Product] = [
            p
            for p in repo.list_products(session, loc_id)
            if p.source_id == source_id and p.epoch == year
        ]
    return {
        p.kind: p
        for p in prods
        if json.loads(p.provenance).get("cache_key") == key
        and (settings.data_dir / p.path).exists()
    }


def layer_plan(
    existing: dict[str, Product], layers: tuple[str, ...], km2: float, sheets: int
) -> dict[str, Any]:
    """What a request for `layers` needs: kinds on disk, kinds to build, estimated seconds."""
    have = [k for k in layers if k in existing]
    missing = [k for k in layers if k not in existing]
    from_dtm = "dtm" in existing
    return {
        "layers": list(layers),
        "layers_existing": have,
        "layers_missing": missing,
        "from_existing_dtm": from_dtm and bool(missing),
        "processing_s": estimate_processing_s(km2, missing, sheets, from_dtm) if missing else None,
    }


def estimate_area(
    settings: Settings,
    bbox: BBox,
    source_id: str | None = None,
    year: int | None = None,
    layers: str | list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Estimate for a viewport. Raises AreaError (payload carries the numbers) over the limits
    and for unknown layer kinds."""
    try:
        want = normalise_layers(layers)
    except ValueError as e:
        raise AreaError(str(e)) from None
    aoi = aoi_2180(bbox)
    km2 = area_km2(aoi)
    limits = {
        "max_area_km2": settings.max_fetch_area_km2,
        "max_bytes": settings.max_fetch_bytes,
    }
    base: dict[str, Any] = {
        "bbox": list(bbox),
        "area_km2": round(km2, 4),
        "limits": limits,
        "layers": list(want),
    }
    if km2 > settings.max_fetch_area_km2:
        raise AreaError(
            f"area {km2:.2f} km2 exceeds the limit of {settings.max_fetch_area_km2:g} km2; zoom in",
            {"estimate": {**base, "tiles": 0, "bytes_total": 0, "over_limit": "area"}},
        )
    tiles, errors = list_area_tiles(settings, aoi)
    if errors and not tiles:
        raise RuntimeError("; ".join(errors))
    epochs = epochs_of(tiles)
    chosen = choose_epoch(epochs, source_id, year)
    base["epochs"] = epochs
    if chosen is None:
        return {
            **base,
            "source_id": source_id,
            "year": year,
            "tiles": [],
            "sheets": 0,
            "bytes_total": 0,
            "bytes_cached": 0,
            "bytes_to_download": 0,
            "location_id": location_id_for(aoi),
            "processed": False,
            "errors": errors,
            **layer_plan({}, want, km2, 0),
        }
    sid, yr = chosen["source_id"], chosen["year"]
    sel = sorted(
        (t for t in tiles if t.source_id == sid and t.year == yr), key=lambda t: t.godlo or ""
    )
    described = describe_tiles(settings, sel)
    total = sum(d["size_bytes"] or 0 for d in described)
    cached = sum(d["size_bytes"] or 0 for d in described if d["cached"])
    todo = sum(
        max((d["size_bytes"] or 0) - d["partial_bytes"], 0) for d in described if not d["cached"]
    )
    key = cache_key(sid, yr, aoi)
    lid = location_id_for(aoi)
    existing = products_for_key(settings, lid, sid, yr, key)
    plan = layer_plan(existing, want, km2, len(described))
    # With a DTM on disk, only ground_density needs the LAZ points; otherwise nothing is fetched
    # when every requested layer exists, or when the only missing ones derive from the DTM.
    needs_laz = bool(plan["layers_missing"]) and (
        not plan["from_existing_dtm"] or "ground_density" in plan["layers_missing"]
    )
    if not needs_laz:
        todo = 0
    result = {
        **base,
        "source_id": sid,
        "year": yr,
        "tiles": described,
        "sheets": len(described),
        "bytes_total": total,
        "bytes_cached": cached,
        "bytes_to_download": todo,
        "location_id": lid,
        "processed": not plan["layers_missing"],
        "needs_laz": needs_laz,
        "errors": errors,
        **plan,
    }
    if total > settings.max_fetch_bytes:
        raise AreaError(
            f"{total / 1e9:.2f} GB of LiDAR exceeds the limit of "
            f"{settings.max_fetch_bytes / 1e9:.2f} GB; zoom in",
            {"estimate": {**result, "over_limit": "bytes"}},
        )
    return result
