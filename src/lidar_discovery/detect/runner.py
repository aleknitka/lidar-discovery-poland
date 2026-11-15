"""Run deterministic detection + chip export for a finished area/location."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

from lidar_discovery.catalog import repo
from lidar_discovery.catalog.db import session_scope
from lidar_discovery.catalog.models import Candidate, dumps
from lidar_discovery.config import Settings
from lidar_discovery.detect.rules import candidate_id, detect_all
from lidar_discovery.processing.dtm import Grid
from lidar_discovery.processing.pipeline import PIPELINE_VERSION, code_version

try:
    from lidar_discovery.chips import export_chips

    HAS_CHIPS = True
except Exception:
    HAS_CHIPS = False


def _load_array(path: Path) -> tuple[np.ndarray, Any]:
    with rasterio.open(path) as ds:
        arr = ds.read(1).astype(np.float32)
        nodata = ds.nodata
        if nodata is not None:
            arr = np.where(arr == nodata, np.nan, arr)
        transform = ds.transform
        crs = ds.crs
    return arr, transform


def _grid_from_transform(transform, shape: tuple[int, int]) -> Grid:
    h, w = shape
    x0 = float(transform.c)
    y1 = float(transform.f)
    res = float(transform.a)
    return Grid(x0=x0, y1=y1, res=res, width=w, height=h)


def _git_sha() -> str:
    try:
        import subprocess

        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=Path(__file__).parent,
        ).stdout.strip()
    except Exception:
        return ""


def run_detection_for_location(
    settings: Settings,
    location_id: str,
    source_id: str | None = None,
    year: int | None = None,
    enable_anomaly: bool = False,
) -> list[Candidate]:
    """Load COGs for a location, run rules (+ optional anomaly), write Candidates.

    Returns the created Candidate rows. No-ops if DTM missing.
    Respects LDP_PUBLIC_MODE (caller should guard, but we double-check).
    """
    if settings.public_mode:
        return []
    with session_scope(settings) as s:
        prods = repo.list_products(s, location_id)
    if not prods:
        return []
    # filter by source/year if given
    if source_id is not None:
        prods = [p for p in prods if p.source_id == source_id]
    if year is not None:
        prods = [p for p in prods if p.epoch == year]
    if not prods:
        return []
    # group by epoch, pick newest
    epochs = sorted({p.epoch for p in prods}, reverse=True)
    epoch = epochs[0]
    prods = [p for p in prods if p.epoch == epoch]
    by_kind = {p.kind: p for p in prods}
    dtm_prod = by_kind.get("dtm")
    if dtm_prod is None:
        return []
    # resolve paths relative to data_dir
    def _abs(p: Any) -> Path:
        ap = Path(p.path)
        return ap if ap.is_absolute() else settings.data_dir / ap

    dtm, transform = _load_array(_abs(dtm_prod))
    grid = _grid_from_transform(transform, dtm.shape)
    arrays: dict[str, np.ndarray] = {"dtm": dtm}
    for kind in ("hillshade", "slope", "svf", "lrm", "ground_density"):
        prod = by_kind.get(kind)
        if prod is not None:
            arr, _ = _load_array(_abs(prod))
            arrays[kind] = arr
    # derive channels if missing
    from lidar_discovery.ml.channels import derive_fill_depth, derive_lrm5, derive_support_log

    if "lrm5" not in arrays:
        try:
            arrays["lrm5"] = derive_lrm5(dtm, grid.res)
        except Exception:
            pass
    if "fill_depth" not in arrays:
        try:
            arrays["fill_depth"] = derive_fill_depth(dtm)
        except Exception:
            pass
    if "support" not in arrays:
        gd = arrays.get("ground_density")
        if gd is not None:
            try:
                arrays["support"] = derive_support_log(gd, grid.res)
            except Exception:
                arrays["support"] = np.ones_like(dtm, dtype=np.float32)
        else:
            arrays["support"] = np.ones_like(dtm, dtype=np.float32)
    # CRS transform helper for WGS84
    try:
        from pyproj import Transformer

        t2180_to_4326 = Transformer.from_crs(2180, 4326, always_xy=True).transform
    except Exception:
        t2180_to_4326 = None

    def to_wgs84(x2180: float, y2180: float) -> tuple[float, float]:
        if t2180_to_4326 is not None:
            return t2180_to_4326(x2180, y2180)  # type: ignore[no-any-return]
        return (x2180, y2180)

    support = arrays.get("support")
    raw_cands = detect_all(arrays, grid, support=support, to_wgs84=to_wgs84)
    # optional anomaly
    if enable_anomaly:
        try:
            from lidar_discovery.detect.anomaly import anomaly_map, candidates_from_anomaly

            amap = anomaly_map(arrays, model=None)
            acands = candidates_from_anomaly(amap, grid, support=support, to_wgs84=to_wgs84)
            raw_cands.extend(acands)
        except Exception:
            pass
    # chips + Candidate rows
    created: list[Candidate] = []
    # product provenance for card
    prod_ids = [p.id for p in prods]
    channel_hash = ""
    try:
        from lidar_discovery.ml.channels import channel_spec_hash

        channel_hash = channel_spec_hash()
    except Exception:
        pass
    for rc in raw_cands:
        cid = candidate_id()
        lon, lat = rc.get("centroid_wgs84", (0, 0))
        geom = json.dumps({"type": "Point", "coordinates": [float(lon), float(lat)]})
        chips_rel: dict[str, str] = {}
        if HAS_CHIPS:
            try:
                chips_rel = export_chips(location_id, cid, rc, arrays, grid, settings.data_dir)
            except Exception:
                chips_rel = {}
        prov = {
            "input_products": prod_ids,
            "dtm_recipe": PIPELINE_VERSION,
            "channel_hash": channel_hash,
            "code_version": code_version(),
            "git_sha": _git_sha(),
            "support_fraction": float(rc.get("support_fraction", 1)),
            "low_support": bool(rc.get("low_support", False)),
            "chips": chips_rel,
            "raw": {k: v for k, v in rc.items() if k not in ("centroid_rc", "polyline_rc")},
        }
        cand = Candidate(
            id=cid,
            location_id=location_id,
            geometry=geom,
            morph_class=str(rc.get("kind", "other")),
            reality="unassessed",
            reality_confidence=0.0,
            origin="rule",
            model_version=f"rules-{PIPELINE_VERSION}-{channel_hash[:6]}",
            review_status="proposed",
            disclosure="restricted",
        )
        # store provenance in reviewer_notes as JSON (Candidate has no provenance column;
        # we use documentation_status + reviewer_notes; keep provenance in reviewer_notes)
        cand.reviewer_notes = dumps(prov)
        # also store chip paths in documentation_status for API convenience
        cand.documentation_status = dumps({"chips": chips_rel})
        with session_scope(settings) as s:
            s.add(cand)
            s.commit()
            s.refresh(cand)
        created.append(cand)
    return created
