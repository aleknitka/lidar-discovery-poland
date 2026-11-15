"""Synthetic preview for \"Test detection here\" — bbox → DTM → heatmap + rectangles + chips.

No LAZ download. Generates a fractal DTM on the fly (or reuses real DTM if present),
derives the 6-channel stack, runs deterministic rules + anomaly, writes a heatmap
COG and candidate chips, all in <2s for a 200m window. GPU paths use torch when
available, otherwise numpy/scipy fallback (CI).
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy import ndimage

from lidar_discovery.config import Settings
from lidar_discovery.processing.dtm import Grid
from lidar_discovery.processing.vis import hillshade_multi, local_relief_model, slope_deg, sky_view_factor

try:
    from lidar_discovery.processing.cog import write_cog
except Exception:  # pragma: no cover
    write_cog = None  # type: ignore[assignment]

PREVIEW_KIND = "anomaly"  # product kind for the heatmap COG (served with viridis ramp)
HEATMAP_RANGE: tuple[float, float] = (0.0, 1.0)


def _hash_bbox(bbox: tuple[float, float, float, float], seed: int, res: float) -> str:
    raw = f"{bbox[0]:.6f},{bbox[1]:.6f},{bbox[2]:.6f},{bbox[3]:.6f}@{seed}@{res}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _preview_id(bbox: tuple[float, float, float, float], seed: int) -> str:
    return f"preview-{_hash_bbox(bbox, seed, 0.5)}"


def synthetic_dtm(
    grid: Grid,
    seed: int = 0,
    base_m: float = 260.0,
    n_platforms: int = 2,
    n_pits: int = 2,
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    """Fractal terrain + pasted synthetic structures. Returns (dtm, truth_rects).

    truth_rects are axis-aligned boxes in grid pixel coords for reference.
    Terrain amplitude is ~8 m; structures are 0.25-0.55 m (platforms) and
    0.35-0.9 m (pits), blurred 0.6 px to look like a TIN DTM.
    """
    rng = np.random.default_rng(seed)
    h, w = grid.height, grid.width
    raw = rng.standard_normal((h, w)).astype(np.float32)
    # two-scale fractal: broad hills + fine texture
    dtm = (
        ndimage.gaussian_filter(raw, 6) * 4.0
        + ndimage.gaussian_filter(raw, 2) * 1.2
        + ndimage.gaussian_filter(raw, 0.8) * 0.25
        + raw * 0.05
    ).astype(np.float32)
    # scale to ~ base + terrain
    dtm = base_m + dtm
    truth: list[dict[str, Any]] = []
    # paste platforms
    for _i in range(n_platforms):
        rh = int(rng.integers(12, 30))  # 6-15 m at 0.5 m
        rw = int(rng.integers(14, 36))
        r0 = int(rng.integers(8, max(9, h - rh - 8)))
        c0 = int(rng.integers(8, max(9, w - rw - 8)))
        amp = float(rng.uniform(0.28, 0.55))
        dtm[r0 : r0 + rh, c0 : c0 + rw] += amp
        dtm = ndimage.gaussian_filter(dtm, 0.6)
        truth.append({"kind": "house_platform", "bbox_rc": [r0, c0, r0 + rh, c0 + rw], "amp": amp})
    # paste pits
    for _i in range(n_pits):
        rh = int(rng.integers(8, 18))
        rw = int(rng.integers(8, 18))
        r0 = int(rng.integers(8, max(9, h - rh - 8)))
        c0 = int(rng.integers(8, max(9, w - rw - 8)))
        amp = float(rng.uniform(0.35, 0.9))
        dtm[r0 : r0 + rh, c0 : c0 + rw] -= amp
        # keep crisp rim
        rim = np.zeros_like(dtm, dtype=bool)
        rim[r0 : r0 + rh, c0 : c0 + rw] = True
        rim[r0 + 1 : r0 + rh - 1, c0 + 1 : c0 + rw - 1] = False
        dtm[rim] += amp * 0.15
        truth.append({"kind": "cellar_pit", "bbox_rc": [r0, c0, r0 + rh, c0 + rw], "amp": -amp})
    # add subtle line (holloway) as shallow trough
    if h > 40 and w > 40 and rng.random() < 0.7:
        c_mid = w // 2 + int(rng.integers(-w // 6, w // 6))
        width = int(rng.integers(3, 6))
        depth = float(rng.uniform(0.18, 0.35))
        for r in range(h):
            wobble = int(round(2 * np.sin(r * 0.08 + seed)))
            cc = c_mid + wobble
            c1, c2 = max(0, cc - width), min(w, cc + width)
            dtm[r, c1:c2] -= depth * (1 - abs(np.arange(c1, c2) - (c1 + c2) / 2) / max(width, 1))
        truth.append({"kind": "holloway", "polyline": True})
    return dtm.astype(np.float32), truth


def _derive_arrays(dtm: np.ndarray, grid: Grid) -> dict[str, np.ndarray]:
    """Derive the visualisation + channel stack from a DTM."""
    res = grid.res
    hill = hillshade_multi(dtm, res, n_dir=16, sun_elevation_deg=35.0)
    slope = slope_deg(dtm, res)
    svf = sky_view_factor(dtm, res, radius_m=10.0, n_dir=16)
    lrm = local_relief_model(dtm, res, sigma_m=10.0)
    # channels
    from lidar_discovery.ml.channels import derive_fill_depth, derive_lrm5, derive_support_log

    lrm5 = derive_lrm5(dtm, res)
    fill_depth = derive_fill_depth(dtm)
    # synthetic has perfect support
    support = np.ones_like(dtm, dtype=np.float32)
    support[np.isnan(dtm)] = np.nan
    support_log = derive_support_log(np.where(np.isnan(support), 0, (support > 0).astype(np.float32) * 4), res)
    return {
        "dtm": dtm,
        "hillshade": hill,
        "slope": slope,
        "svf": svf,
        "lrm": lrm,
        "lrm5": lrm5,
        "fill_depth": fill_depth,
        "support": support_log,
        "ground_density": support,
    }


def _heatmap_from_arrays(arrays: dict[str, np.ndarray], grid: Grid) -> np.ndarray:
    """Anomaly heatmap 0..1 from the channel stack. GPU-aware if torch available."""
    # try torch AE first, then residual
    try:
        from lidar_discovery.detect.anomaly import anomaly_map

        amap = anomaly_map(arrays, model=None)
        # normalise 0..1 via robust percentile
        vals = amap[np.isfinite(amap)]
        if len(vals):
            lo, hi = float(np.percentile(vals, 5)), float(np.percentile(vals, 98))
            if hi > lo:
                amap = np.clip((amap - lo) / (hi - lo), 0, 1).astype(np.float32)
            else:
                amap = np.zeros_like(amap, dtype=np.float32)
        amap[np.isnan(amap)] = 0
        # blend with prob from rules where available (max)
        return amap.astype(np.float32)
    except Exception:
        lrm = arrays.get("lrm", arrays.get("lrm5", np.zeros((10, 10), np.float32)))
        filld = arrays.get("fill_depth", np.zeros_like(lrm))
        vals = np.nan_to_num(np.abs(lrm) * 0.6 + np.clip(filld / 1.2, 0, 1) * 0.7, nan=0).astype(np.float32)
        vals = np.clip(vals / max(float(np.percentile(vals, 98)) if vals.size else 1, 1e-6), 0, 1)
        return vals.astype(np.float32)


def run_preview_for_bbox(
    settings: Settings,
    bbox: tuple[float, float, float, float],
    seed: int = 0,
    synthetic: bool = True,
) -> dict[str, Any]:
    """Entry point for POST /api/preview. Returns preview payload.

    Uses synthetic terrain when `synthetic=True` or when no real DTM product exists
    for the bbox. When a real DTM exists it is reused (and synthetic structures are NOT
    pasted — the terrain is truth).
    """
    t0 = time.perf_counter()
    from lidar_discovery.areas import aoi_2180, cache_key, location_id_for

    from lidar_discovery.catalog import repo
    from lidar_discovery.catalog.db import session_scope
    from lidar_discovery.catalog.models import Location, Product, dumps
    from lidar_discovery.processing.pipeline import PIPELINE_VERSION, code_version

    # aoi in EPSG:2180, rounded to 1 m
    aoi = aoi_2180(bbox)
    pid = _preview_id(bbox, seed)
    # check for real DTM reuse
    real_dtm: np.ndarray | None = None
    real_grid: Grid | None = None
    real_source: str | None = None
    real_epoch: int | None = None
    real_bounds_wgs84: Any = None
    if not synthetic:
        # try find an area-* location covering this bbox with a DTM
        from lidar_discovery.areas import estimate_area

        try:
            est = estimate_area(settings, bbox, None, None, None)
            lid_real = est.get("location_id")
            if lid_real and est.get("processed"):
                with session_scope(settings) as s:
                    prods = {p.kind: p for p in repo.list_products(s, lid_real)}
                if "dtm" in prods:
                    import rasterio as _rio

                    p = prods["dtm"]
                    path = settings.data_dir / p.path if not Path(p.path).is_absolute() else Path(p.path)
                    with _rio.open(path) as ds:
                        arr = ds.read(1).astype(np.float32)
                        if ds.nodata is not None:
                            arr = np.where(arr == ds.nodata, np.nan, arr)
                        real_grid = Grid(x0=float(ds.transform.c), y1=float(ds.transform.f), res=float(ds.res[0]), width=ds.width, height=ds.height)
                        real_dtm = arr
                        real_source = p.source_id
                        real_epoch = p.epoch
                        try:
                            real_bounds_wgs84 = json.loads(p.bounds_wgs84)
                        except Exception:
                            real_bounds_wgs84 = list(bbox)
        except Exception:
            pass

    # build grid + dtm
    if real_dtm is not None and real_grid is not None:
        grid = real_grid
        dtm = real_dtm
        truth: list[dict[str, Any]] = []
        source_id = real_source or "preview-real"
        epoch = real_epoch or 2023
        note = "real DTM reused"
    else:
        # synthetic grid exactly covering the aoi
        from lidar_discovery.processing.dtm import Grid as _Grid

        minx, miny, maxx, maxy = aoi.bounds
        grid = _Grid.from_bounds((minx, miny, maxx, maxy), 0.5, snap=True)
        # clamp huge previews (limit 6 km² server, but preview should stay snappy)
        if grid.width * grid.height > 600 * 600:  # >300 m square fallback
            # downsample bbox for preview only
            grid = _Grid.from_bounds((minx, miny, maxx, maxy), 1.0, snap=True)
        dtm, truth = synthetic_dtm(grid, seed=seed)
        source_id = "synthetic"
        epoch = 9999
        note = "synthetic fractal terrain + 2 platforms + 2 pits + occasional holloway"
        real_bounds_wgs84 = list(bbox)

    arrays = _derive_arrays(dtm, grid)
    heatmap = _heatmap_from_arrays(arrays, grid)

    # run rules → rectangles
    try:
        from pyproj import Transformer

        to_4326 = Transformer.from_crs(2180, 4326, always_xy=True).transform
    except Exception:
        to_4326 = None  # type: ignore[assignment]

    def _to_wgs84(x: float, y: float) -> tuple[float, float]:
        if to_4326 is not None:
            lon, lat = to_4326(x, y)  # type: ignore[arg-type]
            return float(lon), float(lat)
        return float(x), float(y)

    try:
        from lidar_discovery.detect.rules import detect_all

        raw_all = detect_all(arrays, grid, support=arrays.get("support"), to_wgs84=_to_wgs84, enable_linear=True)
        # keep only best 12 per kind + score >= 0.35 so preview stays readable (real map will rank by budget)
        from collections import defaultdict as _dd

        _by_kind: dict[str, list[dict]] = _dd(list)  # type: ignore[type-arg]
        for _c in raw_all:
            _by_kind[str(_c.get("kind", "other"))].append(_c)
        raw_cands: list[dict] = []  # type: ignore[type-arg]
        for _kind, _lst in _by_kind.items():
            _lst.sort(key=lambda _x: float(_x.get("score", 0)), reverse=True)
            raw_cands.extend([c for c in _lst[:12] if float(c.get("score", 0)) >= 0.35])
        raw_cands.sort(key=lambda _x: float(_x.get("score", 0)), reverse=True)
        if not raw_cands and raw_all:
            raw_cands = sorted(raw_all, key=lambda _x: float(_x.get("score", 0)), reverse=True)[:6]
    except Exception as _e:  # noqa: BLE001
        raw_cands = []  # type: ignore[no-redef]
        note += f" | rules failed: {_e}"

    # ensure at least one candidate for demo when synthetic and rules found nothing
    if not raw_cands and truth:
        # promote first truth rect
        t = truth[0]
        rc = t.get("bbox_rc")
        if rc:
            r0, c0, r1, c1 = rc
            rc_centre = ((r0 + r1) / 2, (c0 + c1) / 2)
            x0 = grid.x0 + (c0 + 0.5) * grid.res
            y0 = grid.y1 - (r0 + 0.5) * grid.res
            x1 = grid.x0 + (c1 + 0.5) * grid.res
            y1 = grid.y1 - (r1 + 0.5) * grid.res
            # polygon in WGS84
            poly_wgs: list[list[float]] = []
            for px, py in [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]:
                lon, lat = _to_wgs84(px, py)
                poly_wgs.append([lon, lat])
            lon_c, lat_c = _to_wgs84(grid.x0 + (rc_centre[1] + 0.5) * grid.res, grid.y1 - (rc_centre[0] + 0.5) * grid.res)
            raw_cands = [
                {
                    "kind": t.get("kind", "house_platform"),
                    "centroid_rc": rc_centre,
                    "centroid_wgs84": (lon_c, lat_c),
                    "bbox_rc": rc,
                    "poly_wgs84": poly_wgs,
                    "area_m2": float((r1 - r0) * (c1 - c0) * grid.res * grid.res),
                    "score": 0.88,
                    "low_support": False,
                    "support_fraction": 1.0,
                }
            ]

    # enrich with polygon/line where missing
    for c in raw_cands:
        # holloway: polyline_rc -> LineString (stored as poly_wgs84 line)
        if "poly_wgs84" not in c and "polyline_rc" in c:
            pts = c["polyline_rc"]  # type: ignore[assignment]
            line: list[list[float]] = []
            for r, cc in pts:
                x, y = grid.x0 + (cc + 0.5) * grid.res, grid.y1 - (r + 0.5) * grid.res
                lon, lat = _to_wgs84(x, y)
                line.append([lon, lat])
            c["poly_wgs84"] = line
            c["_is_line"] = True
        if "poly_wgs84" not in c and "bbox_rc" in c:
            r0, c0, r1, c1 = c["bbox_rc"]  # type: ignore[misc]
            x0, y0 = grid.x0 + (c0 + 0.5) * grid.res, grid.y1 - (r0 + 0.5) * grid.res
            x1, y1 = grid.x0 + (c1 + 0.5) * grid.res, grid.y1 - (r1 + 0.5) * grid.res
            poly: list[list[float]] = []
            for px, py in [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]:
                lon, lat = _to_wgs84(px, py)
                poly.append([lon, lat])
            c["poly_wgs84"] = poly
            if "centroid_wgs84" not in c:
                rc = c.get("centroid_rc") or ((r0 + r1) / 2, (c0 + c1) / 2)
                lon, lat = _to_wgs84(grid.x0 + (rc[1] + 0.5) * grid.res, grid.y1 - (rc[0] + 0.5) * grid.res)
                c["centroid_wgs84"] = (lon, lat)

    # write heatmap COG under data/preview/<id>/
    preview_dir = settings.data_dir / "preview" / pid
    preview_dir.mkdir(parents=True, exist_ok=True)
    heat_path = preview_dir / "heatmap.tif"
    dtm_path = preview_dir / "dtm.tif"
    if write_cog is not None:
        write_cog(heat_path, heatmap, grid.transform, nodata=-9999.0, resampling="bilinear")
        write_cog(dtm_path, dtm, grid.transform, nodata=-9999.0, resampling="bilinear")
    else:
        # fallback: numpy save (tiles will 404, but preview still returns candidates)
        np.save(preview_dir / "heatmap.npy", heatmap)

    # upsert preview Location + Products for tile serving
    loc_id = pid
    heat_prod_id = f"{loc_id}-{source_id}-{epoch}-{PREVIEW_KIND}"
    dtm_prod_id = f"{loc_id}-{source_id}-{epoch}-dtm"
    try:
        with session_scope(settings) as s:
            # location
            existing = s.get(Location, loc_id)
            prov_loc = [{"provider": "preview", "bbox": list(bbox), "seed": seed, "note": note, "synthetic": synthetic}]
            if existing is None:
                loc = Location(
                    id=loc_id,
                    names=json.dumps({"other": f"Preview {bbox[0]:.3f},{bbox[1]:.3f}"}),
                    lon=float((bbox[0] + bbox[2]) / 2),
                    lat=float((bbox[1] + bbox[3]) / 2),
                    polygon=json.dumps({"type": "Polygon", "coordinates": [[[bbox[0], bbox[1]], [bbox[2], bbox[1]], [bbox[2], bbox[3]], [bbox[0], bbox[3]], [bbox[0], bbox[1]]]]}),
                    disclosure="public",
                    kind="area",
                    provenance=json.dumps(prov_loc),
                )
                s.add(loc)
            # heatmap product
            if heat_path.exists():
                rel_heat = str(heat_path.relative_to(settings.data_dir)) if heat_path.is_absolute() or str(heat_path).startswith(str(settings.data_dir)) else str(heat_path)
                # ensure relative
                try:
                    rel_heat = str(heat_path.relative_to(settings.data_dir))
                except Exception:
                    rel_heat = str(heat_path)
                heat_prov = {
                    "display_range": list(HEATMAP_RANGE),
                    "preview": True,
                    "seed": seed,
                    "synthetic": synthetic,
                    "code_version": code_version(),
                    "pipeline_version": PIPELINE_VERSION,
                }
                heat_prod = Product(
                    id=heat_prod_id,
                    location_id=loc_id,
                    source_id=source_id,
                    epoch=epoch,
                    kind=PREVIEW_KIND,
                    path=rel_heat,
                    resolution_m=grid.res,
                    bounds_wgs84=json.dumps(list(bbox)),
                    crs_h="EPSG:2180",
                    provenance=json.dumps(heat_prov),
                )
                # upsert
                ex = s.get(Product, heat_prod_id)
                if ex is not None:
                    s.delete(ex)
                s.add(heat_prod)
                # also DTM preview product for swipe
                rel_dtm = str(dtm_path.relative_to(settings.data_dir)) if dtm_path.exists() else rel_heat
                try:
                    rel_dtm = str(dtm_path.relative_to(settings.data_dir))
                except Exception:
                    pass
                dtm_prov = {"display_range": [float(np.nanpercentile(dtm, 5)), float(np.nanpercentile(dtm, 95))], "preview": True}
                dtm_prod = Product(
                    id=dtm_prod_id,
                    location_id=loc_id,
                    source_id=source_id,
                    epoch=epoch,
                    kind="dtm",
                    path=rel_dtm,
                    resolution_m=grid.res,
                    bounds_wgs84=json.dumps(list(bbox)),
                    crs_h="EPSG:2180",
                    provenance=json.dumps(dtm_prov),
                )
                ex2 = s.get(Product, dtm_prod_id)
                if ex2 is not None:
                    s.delete(ex2)
                s.add(dtm_prod)
            s.commit()
    except Exception:
        # preview still usable without DB (direct file path)
        pass

    # persist candidates as real Candidate rows under the preview location (so /candidates works)
    preview_candidate_ids: list[str] = []
    try:
        from lidar_discovery.catalog.models import Candidate, dumps as _dumps

        from lidar_discovery.catalog.db import session_scope as _ss2

        import uuid as _uuid

        for c in raw_cands[:40]:
            lon, lat = c.get("centroid_wgs84", (bbox[0], bbox[1]))
            # geometry: Polygon if poly_wgs84 else Point
            poly = c.get("poly_wgs84")
            if poly and len(poly) >= 4:
                geom = {"type": "Polygon", "coordinates": [poly]}
            else:
                geom = {"type": "Point", "coordinates": [float(lon), float(lat)]}
            prov_cand = {
                "preview": True,
                "seed": seed,
                "score": float(c.get("score", 0.5)),
                "low_support": bool(c.get("low_support", False)),
                "support_fraction": float(c.get("support_fraction", 1.0)),
                "kind_raw": c.get("kind"),
                "area_m2": float(c.get("area_m2", 0)),
            }
            cand = Candidate(
                id=_uuid.uuid4().hex[:12],
                location_id=loc_id,
                geometry=json.dumps(geom),
                morph_class=str(c.get("kind", "other")) if str(c.get("kind", "other")) in ("house_platform", "cellar_pit", "terrace", "holloway", "field_boundary", "cemetery", "church_site", "other") else "other",
                reality="unassessed",
                reality_confidence=float(np.clip(float(c.get("score", 0.5)), 0, 1)),
                origin="rule",
                model_version=f"preview-{PIPELINE_VERSION}",
                review_status="proposed",
                disclosure="public",
                provenance=_dumps(prov_cand),
            )
            with _ss2(settings) as s:
                # dedup by id already random
                s.add(cand)
                s.commit()
            preview_candidate_ids.append(cand.id)
            c["candidate_id"] = cand.id
            # chips for this preview candidate
            try:
                from lidar_discovery.chips import export_chips

                # export 96 + 256 per kind using the derived arrays
                rels = export_chips(loc_id, cand.id, {"centroid_rc": c.get("centroid_rc", (grid.height / 2, grid.width / 2))}, arrays, grid, settings.data_dir)
                c["chips"] = rels
                # patch provenance with chips
                with _ss2(settings) as s:
                    row = s.get(Candidate, cand.id)
                    if row is not None:
                        prov2 = json.loads(row.provenance) if row.provenance else {}
                        prov2["chips"] = rels
                        row.provenance = _dumps(prov2)
                        s.add(row)
                        s.commit()
            except Exception:
                c["chips"] = {}
    except Exception:
        pass

    # heatmap tile url (uses existing product tile endpoint)
    tile_url = f"/api/layers/{heat_prod_id}/tiles/{{z}}/{{x}}/{{y}}.png"

    return {
        "id": pid,
        "location_id": loc_id,
        "bbox": list(bbox),
        "grid": {"width": grid.width, "height": grid.height, "res": grid.res},
        "heatmap_layer_id": heat_prod_id,
        "heatmap_tile_url": tile_url,
        "dtm_layer_id": dtm_prod_id,
        "candidates": raw_cands,
        "candidate_ids": preview_candidate_ids,
        "seed": seed,
        "synthetic": synthetic,
        "note": note,
        "elapsed_s": round(time.perf_counter() - t0, 3),
    }
