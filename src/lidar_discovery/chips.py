"""Image chips per Candidate (11 §3, §9): 96px (48m) + 256px (128m) PNGs per layer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from lidar_discovery.processing.dtm import Grid

_RANGES: dict[str, tuple[float, float]] = {
    "hillshade": (0.0, 1.0),
    "svf": (0.75, 1.0),
    "lrm": (-0.6, 0.6),
    "lrm5": (-0.6, 0.6),
    "slope": (0.0, 30.0),
    "dtm": (-1.0, 1.0),
    "dtm_shaded": (0.0, 1.0),
    "fill_depth": (0.0, 1.2),
}

KINDS_FOR_CHIPS: tuple[str, ...] = ("hillshade", "svf", "lrm", "slope", "dtm")


def _norm(arr: np.ndarray, kind: str) -> np.ndarray:
    lo, hi = _RANGES.get(kind, (float(np.nanmin(arr)), float(np.nanmax(arr))))
    if kind == "dtm":
        vals = arr[np.isfinite(arr)]
        if len(vals):
            lo, hi = float(np.percentile(vals, 2)), float(np.percentile(vals, 98))
            if hi <= lo:
                hi = lo + 1
        else:
            lo, hi = 0, 1
    t = np.clip((arr - lo) / max(hi - lo, 1e-6), 0, 1)
    if kind == "slope":
        t = 1 - t
    return (t * 255).astype(np.uint8)


def _extract_chip(arr: np.ndarray, rc: tuple[float, float], size: int) -> np.ndarray:
    h, w = arr.shape
    r, c = int(round(rc[0])), int(round(rc[1]))
    half = size // 2
    r0, c0 = r - half, c - half
    r1, c1 = r0 + size, c0 + size
    chip = np.full((size, size), np.nan, dtype=np.float32)
    sr0, sc0 = max(0, r0), max(0, c0)
    sr1, sc1 = min(h, r1), min(w, c1)
    dr0, dc0 = sr0 - r0, sc0 - c0
    dr1, dc1 = dr0 + (sr1 - sr0), dc0 + (sc1 - sc0)
    if sr1 > sr0 and sc1 > sc0:
        chip[dr0:dr1, dc0:dc1] = arr[sr0:sr1, sc0:sc1]
    return chip


def export_chips(
    location_id: str,
    candidate_id: str,
    candidate: dict[str, Any],
    arrays: dict[str, np.ndarray],
    grid: Grid,
    data_dir: Path,
    sizes: tuple[int, ...] = (96, 256),
) -> dict[str, str]:
    """Write PNG chips for each kind and size. Returns {kind_size: relative_path}."""
    rc = candidate.get("centroid_rc")
    if rc is None:
        h, w = next(iter(arrays.values())).shape
        rc = (h // 2, w // 2)
    out_base = data_dir / "chips" / location_id / candidate_id
    out_base.mkdir(parents=True, exist_ok=True)
    rel: dict[str, str] = {}
    for kind in KINDS_FOR_CHIPS:
        arr = arrays.get(kind)
        if arr is None:
            if kind == "lrm":
                arr = arrays.get("lrm20", arrays.get("lrm"))
            if arr is None:
                continue
        for sz in sizes:
            chip = _extract_chip(arr, (float(rc[0]), float(rc[1])), sz)
            img = Image.fromarray(_norm(chip, kind), mode="L")
            path = out_base / f"{kind}_{sz}.png"
            img.save(path, "PNG")
            rel[f"{kind}_{sz}"] = str(path.relative_to(data_dir))
    # tiny manifest
    manifest = {"candidate": candidate_id, "kinds": rel}
    meta = out_base / "meta.json"
    meta.write_text(json.dumps(manifest, indent=2))
    return rel


# ------------------------------------------------------------------- helpers
def export_chips_for_candidate(
    settings: Any,
    candidate: Any,
    arrays: dict[str, np.ndarray] | None = None,
    grid: Any | None = None,
) -> dict[str, str]:
    """Wrapper used by jobs.on_job_done: reads COGs if arrays not supplied."""
    cand_id = getattr(candidate, "id", None) or getattr(candidate, "candidate_id", "unknown")
    loc_id = getattr(candidate, "location_id", "")
    geom_text = getattr(candidate, "geometry", "{}")
    try:
        geom = json.loads(geom_text) if isinstance(geom_text, str) else geom_text
    except Exception:
        geom = {"type": "Point", "coordinates": [0, 0]}

    if arrays is None and loc_id and grid is None:
        # fallback: read per-kind chips via rasterio windows
        try:
            from lidar_discovery.catalog.db import session_scope
            from lidar_discovery.catalog.repo import list_products

            product_paths: dict[str, Path] = {}
            with session_scope(settings) as s:
                for p in list_products(s, loc_id):
                    if p.kind in KINDS_FOR_CHIPS:
                        product_paths[p.kind] = settings.data_dir / p.path
            if product_paths:
                return _export_via_windows(settings, loc_id, cand_id, geom, product_paths)
        except Exception:
            pass
        return {}

    # arrays+grid path -> use export_chips directly
    if arrays is None or grid is None:
        return {}
    # derive centroid rc from geometry
    try:
        from pyproj import Transformer

        to_2180 = Transformer.from_crs(4326, 2180, always_xy=True)
        coords = geom.get("coordinates") if isinstance(geom, dict) else None
        if geom.get("type") == "Point" and coords:
            x, y = to_2180.transform(float(coords[0]), float(coords[1]))
        elif geom.get("type") == "Polygon" and coords:
            xs = [c[0] for c in coords[0]]
            ys = [c[1] for c in coords[0]]
            x, y = to_2180.transform(sum(xs) / len(xs), sum(ys) / len(ys))
        else:
            x, y = float(coords[0][0]), float(coords[0][1])  # type: ignore
        # grid -> rc
        tr = grid.transform
        col_f = (x - tr.c) / tr.a if tr.a else 0
        row_f = (tr.f - y) / (-tr.e) if tr.e else 0
        rc = (row_f, col_f)
        candidate_dict: dict[str, Any] = {"centroid_rc": rc}
        return export_chips(loc_id, cand_id, candidate_dict, arrays, grid, settings.data_dir)
    except Exception:
        return {}


def _export_via_windows(
    settings: Any,
    location_id: str,
    candidate_id: str,
    geometry: dict[str, Any],
    product_paths: dict[str, Path],
) -> dict[str, str]:
    """Windowed read fallback when arrays not in memory."""
    try:
        coords = geometry.get("coordinates") if isinstance(geometry, dict) else None
        if geometry.get("type") == "Point" and coords:
            lon, lat = float(coords[0]), float(coords[1])
        elif geometry.get("type") == "Polygon" and coords:
            xs = [c[0] for c in coords[0]]
            ys = [c[1] for c in coords[0]]
            lon, lat = sum(xs) / len(xs), sum(ys) / len(ys)
        else:
            lon, lat = float(coords[0][0]), float(coords[0][1])  # type: ignore
    except Exception:
        return {}

    out: dict[str, str] = {}
    for sz in (96, 256):
        for kind, pth in product_paths.items():
            try:
                import rasterio

                with rasterio.open(pth) as ds:
                    from pyproj import Transformer

                    to_2180 = Transformer.from_crs(4326, 2180, always_xy=True)
                    x, y = to_2180.transform(lon, lat)
                    tr = ds.transform
                    col_f = (x - tr.c) / tr.a if tr.a else 0
                    row_f = (tr.f - y) / (-tr.e) if tr.e else 0
                    r, c = int(round(row_f)), int(round(col_f))
                    half = sz // 2
                    r0, r1 = r - half, r + half
                    c0, c1 = c - half, c + half
                    chip = np.full((sz, sz), np.nan, dtype=np.float32)
                    sr0, sr1 = max(0, r0), min(ds.height, r1)
                    sc0, sc1 = max(0, c0), min(ds.width, c1)
                    if sr0 < sr1 and sc0 < sc1:
                        data = ds.read(1, window=((sr0, sr1), (sc0, sc1)))
                        if ds.nodata is not None:
                            data = np.where(data == ds.nodata, np.nan, data).astype(np.float32)
                        chip[sr0 - r0 : sr0 - r0 + data.shape[0], sc0 - c0 : sc0 - c0 + data.shape[1]] = data
                    img = Image.fromarray(_norm(chip, kind), mode="L")
                    rel = Path("chips") / location_id / candidate_id / f"{kind}_{sz}.png"
                    abs_p = settings.data_dir / rel
                    abs_p.parent.mkdir(parents=True, exist_ok=True)
                    img.save(abs_p, "PNG")
                    out[f"{kind}_{sz}"] = rel.as_posix()
            except Exception:
                continue
    return out
