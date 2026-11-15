"""FastAPI application factory (REST API per docs/08-architecture-contract.md)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlmodel import Session

from lidar_discovery import __version__, areas, jobs
from lidar_discovery import sources as _sources  # noqa: F401  (registers built-in sources)
from lidar_discovery.api.tiles import render_tile
from lidar_discovery.catalog import repo
from lidar_discovery.catalog.db import get_engine
from lidar_discovery.catalog.disclosure import apply_to_feature, visible
from lidar_discovery.catalog.models import Location
from lidar_discovery.config import Settings, get_settings
from lidar_discovery.locations.aoi import aoi_for
from lidar_discovery.sources.base import get_source, source_ids
from lidar_discovery.sources.coverage import compute_coverage, group_tiles


def get_cfg(request: Request) -> Settings:
    return request.app.state.settings


def get_session(request: Request) -> Iterator[Session]:
    with Session(get_engine(request.app.state.settings), expire_on_commit=False) as s:
        yield s


router = APIRouter(prefix="/api")


def _location_or_404(session: Session, cfg: Settings, loc_id: str) -> Location:
    loc = repo.get_location(session, loc_id)
    if loc is None or not visible(loc.disclosure, cfg.public_mode):
        raise HTTPException(404, f"location {loc_id!r} not found")
    return loc


def _layers_hidden(loc: Location, cfg: Settings) -> bool:
    """In public mode precise rasters of non-public locations are not served."""
    return cfg.public_mode and loc.disclosure != "public"


def _no_writes_in_public(cfg: Settings) -> None:
    if cfg.public_mode:
        raise HTTPException(403, "read-only in public mode")


@router.get("/health")
def health(cfg: Settings = Depends(get_cfg)) -> dict[str, Any]:
    return {"status": "ok", "version": __version__, "public_mode": cfg.public_mode}


@router.get("/sources")
def sources(cfg: Settings = Depends(get_cfg)) -> list[dict[str, Any]]:
    out = []
    for sid in source_ids():
        s = get_source(sid, cfg)
        out.append({"id": s.id, "name": s.name, "description": s.description, "crs_h": s.crs_h})
    return out


@router.get("/locations")
def locations(
    session: Session = Depends(get_session), cfg: Settings = Depends(get_cfg)
) -> dict[str, Any]:
    with_products = {p.location_id for p in repo.list_products(session)}
    feats = []
    for loc in repo.list_locations(session):
        f = apply_to_feature(
            repo.location_to_feature(loc, loc.id in with_products), cfg.public_mode
        )
        if f is not None:
            if f["properties"].get("generalised"):
                f["properties"]["polygon"] = None
            feats.append(f)
    return {"type": "FeatureCollection", "features": feats}


@router.get("/locations/{loc_id}")
def location(
    loc_id: str, session: Session = Depends(get_session), cfg: Settings = Depends(get_cfg)
) -> dict[str, Any]:
    loc = _location_or_404(session, cfg, loc_id)
    has = bool(repo.list_products(session, loc_id))
    f = apply_to_feature(repo.location_to_feature(loc, has), cfg.public_mode)
    if f is None:
        raise HTTPException(404, f"location {loc_id!r} not found")
    if f["properties"].get("generalised"):
        f["properties"]["polygon"] = None
    return f


@router.get("/locations/{loc_id}/coverage")
def coverage(
    loc_id: str,
    source: list[str] | None = Query(default=None),
    session: Session = Depends(get_session),
    cfg: Settings = Depends(get_cfg),
) -> list[dict[str, Any]]:
    loc = _location_or_404(session, cfg, loc_id)
    tiles, errors = compute_coverage(cfg, aoi_for(loc), source)
    if errors and not tiles:
        raise HTTPException(502, "; ".join(errors))
    return group_tiles(tiles)


@router.get("/locations/{loc_id}/layers")
def layers(
    loc_id: str, session: Session = Depends(get_session), cfg: Settings = Depends(get_cfg)
) -> list[dict[str, Any]]:
    loc = _location_or_404(session, cfg, loc_id)
    if _layers_hidden(loc, cfg):
        return []
    return [repo.product_to_layer(p) for p in repo.list_products(session, loc_id)]


@router.get("/layers/{layer_id}/tiles/{z}/{x}/{y}.png")
def layer_tile(
    layer_id: str,
    z: int,
    x: int,
    y: int,
    shade: float = Query(default=0.0, ge=0.0, le=1.0),
    colormap: str | None = Query(default=None, description="viridis|grey for heatmaps"),
    session: Session = Depends(get_session),
    cfg: Settings = Depends(get_cfg),
) -> Response:
    prod = repo.get_product(session, layer_id)
    if prod is None:
        raise HTTPException(404, f"layer {layer_id!r} not found")
    loc = repo.get_location(session, prod.location_id)
    if loc is None or not visible(loc.disclosure, cfg.public_mode) or _layers_hidden(loc, cfg):
        raise HTTPException(404, f"layer {layer_id!r} not found")
    path = cfg.data_dir / prod.path
    if not path.exists():
        raise HTTPException(404, "raster file missing on disk")
    if not (0 <= z <= 24) or not (0 <= x < 2**z) or not (0 <= y < 2**z):
        raise HTTPException(400, "invalid tile coordinates")
    rng = json.loads(prod.provenance).get("display_range")
    png = render_tile(path, prod.kind, tuple(rng) if rng else None, z, x, y, shade, colormap)
    return Response(png, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})


def _area_error(e: areas.AreaError) -> JSONResponse:
    return JSONResponse({"detail": str(e), **e.payload}, status_code=422)


@router.get("/areas/estimate")
def areas_estimate(
    bbox: str,
    source_id: str | None = None,
    year: int | None = None,
    layers: str | None = None,
    cfg: Settings = Depends(get_cfg),
) -> Any:
    try:
        return areas.estimate_area(cfg, areas.parse_bbox(bbox), source_id, year, layers)
    except areas.AreaError as e:
        return _area_error(e)
    except RuntimeError as e:
        raise HTTPException(502, str(e)) from None


@router.post("/areas/fetch", status_code=202)
def areas_fetch(
    request: Request,
    body: dict[str, Any] = Body(...),
    cfg: Settings = Depends(get_cfg),
) -> Any:
    _no_writes_in_public(cfg)
    try:
        bbox = areas.parse_bbox(body.get("bbox") or "")
        year = body.get("year")
        if year is not None and not isinstance(year, int):
            raise areas.AreaError("year must be an integer")
        layers = body.get("layers")
        if layers is not None and not isinstance(layers, str | list):
            raise areas.AreaError("layers must be a comma-separated string or a list")
        auto_detect = bool(body.get("auto_detect"))
        job, created = jobs.create_fetch_job(
            cfg, bbox, body.get("source_id"), year, layers, auto_detect
        )
    except areas.AreaError as e:
        return _area_error(e)
    if created:
        request.app.state.runner.submit(job)
    return jobs.job_to_dict(job)


@router.get("/jobs")
def list_jobs(active: bool | None = None, cfg: Settings = Depends(get_cfg)) -> list[dict[str, Any]]:
    return [jobs.job_to_dict(j) for j in jobs.list_jobs(cfg, active)]


@router.get("/jobs/{job_id}")
def get_job(job_id: str, cfg: Settings = Depends(get_cfg)) -> dict[str, Any]:
    j = jobs.get_job(cfg, job_id)
    if j is None:
        raise HTTPException(404, f"job {job_id!r} not found")
    return jobs.job_to_dict(j)


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, request: Request, cfg: Settings = Depends(get_cfg)) -> dict[str, Any]:
    _no_writes_in_public(cfg)
    j = request.app.state.runner.cancel(job_id)
    if j is None:
        raise HTTPException(404, f"job {job_id!r} not found")
    return jobs.job_to_dict(j)


@router.get("/candidates")
def candidates(
    location_id: str | None = None,
    review_status: str | None = None,
    session: Session = Depends(get_session),
    cfg: Settings = Depends(get_cfg),
) -> dict[str, Any]:
    feats = []
    for c in repo.list_candidates(session, location_id, review_status):
        f = apply_to_feature(repo.candidate_to_feature(c), cfg.public_mode)
        if f is not None:
            feats.append(f)
    return {"type": "FeatureCollection", "features": feats}


@router.post("/candidates", status_code=201)
def create_candidate(
    feature: dict[str, Any] = Body(...),
    session: Session = Depends(get_session),
    cfg: Settings = Depends(get_cfg),
) -> dict[str, Any]:
    _no_writes_in_public(cfg)
    try:
        cand = repo.candidate_from_feature(feature)
    except repo.ValidationError as e:
        raise HTTPException(422, str(e)) from None
    if cand.location_id and repo.get_location(session, cand.location_id) is None:
        raise HTTPException(422, f"unknown location_id {cand.location_id!r}")
    if session.get(type(cand), cand.id):
        raise HTTPException(409, f"candidate {cand.id!r} already exists")
    session.add(cand)
    session.commit()
    session.refresh(cand)
    return repo.candidate_to_feature(cand)


@router.get("/candidates/{cand_id}")
def get_candidate(
    cand_id: str, session: Session = Depends(get_session), cfg: Settings = Depends(get_cfg)
) -> dict[str, Any]:
    from lidar_discovery.catalog.models import Candidate

    c = session.get(Candidate, cand_id)
    f = apply_to_feature(repo.candidate_to_feature(c), cfg.public_mode) if c else None
    if f is None:
        raise HTTPException(404, f"candidate {cand_id!r} not found")
    return f


@router.patch("/candidates/{cand_id}")
def patch_candidate(
    cand_id: str,
    feature: dict[str, Any] = Body(...),
    session: Session = Depends(get_session),
    cfg: Settings = Depends(get_cfg),
) -> dict[str, Any]:
    from lidar_discovery.catalog.models import Candidate

    _no_writes_in_public(cfg)
    c = session.get(Candidate, cand_id)
    if c is None:
        raise HTTPException(404, f"candidate {cand_id!r} not found")
    try:
        c = repo.candidate_from_feature(feature, existing=c, partial=True)
    except repo.ValidationError as e:
        raise HTTPException(422, str(e)) from None
    session.add(c)
    session.commit()
    session.refresh(c)
    return repo.candidate_to_feature(c)


# ---- chips ----
@router.get("/candidates/{cand_id}/chips")
def candidate_chips(
    cand_id: str, session: Session = Depends(get_session), cfg: Settings = Depends(get_cfg)
) -> dict[str, Any]:
    from lidar_discovery.catalog.models import Candidate

    c = session.get(Candidate, cand_id)
    f = apply_to_feature(repo.candidate_to_feature(c), cfg.public_mode) if c else None
    if f is None:
        raise HTTPException(404, f"candidate {cand_id!r} not found")
    prov = {}
    try:
        prov = json.loads(c.provenance) if c.provenance else {}
    except Exception:
        prov = {}
    chips = prov.get("chips") or {}
    # return absolute URLs for convenience
    base = f"/api/candidates/{cand_id}/chips"
    return {
        "candidate_id": cand_id,
        "chips": chips,
        "urls": {k: f"{base}/{k}" for k in chips},
    }


@router.get("/candidates/{cand_id}/chips/{kind}")
def candidate_chip_image(
    cand_id: str,
    kind: str,
    session: Session = Depends(get_session),
    cfg: Settings = Depends(get_cfg),
) -> Any:
    from lidar_discovery.catalog.models import Candidate

    c = session.get(Candidate, cand_id)
    f = apply_to_feature(repo.candidate_to_feature(c), cfg.public_mode) if c else None
    if f is None:
        raise HTTPException(404, f"candidate {cand_id!r} not found")
    prov: dict[str, Any] = {}
    try:
        prov = json.loads(c.provenance) if c.provenance else {}
    except Exception:
        prov = {}
    chips: dict[str, str] = prov.get("chips") or {}
    # allow kind with or without _256 suffix
    rel = chips.get(kind)
    if rel is None:
        # fuzzy match: hillshade vs hillshade_256
        for k, v in chips.items():
            if k == kind or k.startswith(kind):
                rel = v
                break
    if rel is None:
        raise HTTPException(404, f"chip {kind!r} not found for candidate {cand_id!r}")
    p = cfg.data_dir / rel
    if not p.exists():
        raise HTTPException(404, "chip file missing on disk")
    return FileResponse(str(p), media_type="image/png")


@router.get("/chips/{location_id}/{candidate_id}/{filename}")
def chip_direct(
    location_id: str,
    candidate_id: str,
    filename: str,
    cfg: Settings = Depends(get_cfg),
) -> Any:
    # Validate filename to avoid traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "invalid chip filename")
    p = cfg.data_dir / "chips" / location_id / candidate_id / filename
    if not p.exists():
        raise HTTPException(404, "chip not found")
    # disclosure check via candidate if present
    try:
        from sqlmodel import Session as _Session

        from lidar_discovery.catalog.db import get_engine as _get_engine
        from lidar_discovery.catalog.models import Candidate

        with _Session(_get_engine(cfg), expire_on_commit=False) as s:
            c = s.get(Candidate, candidate_id)
            if c is not None:
                f = apply_to_feature(repo.candidate_to_feature(c), cfg.public_mode)
                if f is None:
                    raise HTTPException(404, "chip not found")
    except HTTPException:
        raise
    except Exception:
        pass
    return FileResponse(str(p), media_type="image/png")


# ---- watch ----
@router.get("/watch/status")
def watch_status(request: Request, cfg: Settings = Depends(get_cfg)) -> dict[str, Any]:
    sched = getattr(request.app.state, "watch", None)
    if sched is None:
        return {"running": False, "interval_s": cfg.watch_interval_s, "bbox": None}
    try:
        return sched.status()
    except Exception as e:
        return {"running": False, "error": str(e)}


@router.post("/watch/trigger")
def watch_trigger(request: Request, cfg: Settings = Depends(get_cfg)) -> dict[str, Any]:
    _no_writes_in_public(cfg)
    sched = getattr(request.app.state, "watch", None)
    if sched is None:
        # one-shot without daemon
        try:
            from lidar_discovery.watch import WatchScheduler

            tmp = WatchScheduler(settings=cfg, runner=getattr(request.app.state, "runner", None))
            return tmp.poll_once()
        except Exception as e:
            raise HTTPException(500, str(e)) from None
    try:
        return sched.trigger()
    except Exception as e:
        raise HTTPException(500, str(e)) from None


# ---- ml stubs ----
@router.get("/ml/models")
def ml_models(cfg: Settings = Depends(get_cfg)) -> list[dict[str, Any]]:
    try:
        from lidar_discovery.ml.registry import list_models  # type: ignore[import-not-found]

        return list_models(cfg)  # type: ignore[no-any-return]
    except Exception:
        return []


@router.get("/ml/channels/{location_id}")
def ml_channels_status(
    location_id: str, session: Session = Depends(get_session), cfg: Settings = Depends(get_cfg)
) -> dict[str, Any]:
    _location_or_404(session, cfg, location_id)
    prods = repo.list_products(session, location_id)
    by_kind = {p.kind: p for p in prods}
    return {
        "location_id": location_id,
        "has": {k: (k in by_kind) for k in ("lrm5", "fill_depth", "support")},
        "products": [repo.product_to_layer(p) for p in prods if p.kind in ("lrm5", "fill_depth", "support")],
    }


@router.post("/ml/predict/{location_id}")
def ml_predict_endpoint(
    location_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_session),
    cfg: Settings = Depends(get_cfg),
) -> dict[str, Any]:
    _no_writes_in_public(cfg)
    _location_or_404(session, cfg, location_id)
    try:
        from lidar_discovery.ml.predict import predict  # type: ignore[import-not-found]

        res = predict(cfg, location_id, model_version=body.get("model_version"), budget=body.get("budget"))
        return res if isinstance(res, dict) else {"result": str(res)}
    except Exception as e:
        raise HTTPException(500, str(e)) from None


@router.get("/ml/card/{version}")
def ml_card_endpoint(version: str, cfg: Settings = Depends(get_cfg)) -> Any:
    try:
        from lidar_discovery.ml.registry import render_card  # type: ignore[import-not-found]

        out = render_card(cfg, version)
        return out if isinstance(out, dict) else {"card": str(out)}
    except Exception as e:
        raise HTTPException(404, str(e)) from None


@router.post("/preview")
def preview_area(
    body: dict[str, Any] = Body(...),
    cfg: Settings = Depends(get_cfg),
) -> dict[str, Any]:
    """Synthetic preview for 'Test detection here' (no download, <2s for a 200m window).

    Body: {bbox: [w,s,e,n], seed?: int, synthetic?: bool}
    Uses the viewport bbox you see in /explore and returns a heatmap COG
    (served as viridis tiles), rectangles (GeoJSON polygons) and 96/256 chip
    PNGs, plus Candidate rows under a preview location id. All overlay the same
    way the real pipeline will.
    """
    bbox_raw = body.get("bbox")
    if not bbox_raw or not isinstance(bbox_raw, list) or len(bbox_raw) != 4:
        raise HTTPException(422, "bbox must be [w,s,e,n] (WGS84)")
    try:
        bbox = tuple(float(v) for v in bbox_raw)  # type: ignore[assignment]
    except Exception as exc:
        raise HTTPException(422, "bbox values must be numbers") from exc
    seed = int(body.get("seed", 0)) if body.get("seed") is not None else 0
    synthetic = bool(body.get("synthetic", True))
    # validate bbox size (6 km² server limit, but preview clamps to ~0.09 km² anyway)
    try:
        from lidar_discovery.areas import area_km2, aoi_2180

        aoi = aoi_2180(bbox)  # type: ignore[arg-type]
        km2 = area_km2(aoi)
        if km2 > 2.0:
            raise HTTPException(422, f"preview bbox too large: {km2:.2f} km² (limit 2 km², zoom in)")
    except HTTPException:
        raise
    except Exception:
        pass
    try:
        from lidar_discovery.preview import run_preview_for_bbox

        return run_preview_for_bbox(cfg, bbox, seed=seed, synthetic=synthetic)  # type: ignore[arg-type]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"preview failed: {e}") from e


@router.get("/preview/{preview_id}")
def preview_get(
    preview_id: str,
    cfg: Settings = Depends(get_cfg),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Fetch a previously created preview's layers + candidates (for reload)."""
    from lidar_discovery.catalog import repo as _repo

    loc = _repo.get_location(session, preview_id)
    if loc is None:
        raise HTTPException(404, f"preview {preview_id!r} not found")
    layers = [repo.product_to_layer(p) for p in _repo.list_products(session, preview_id)]
    cands = [_repo.candidate_to_feature(c) for c in _repo.list_candidates(session, preview_id)]
    return {"preview_id": preview_id, "layers": layers, "candidates": {"type": "FeatureCollection", "features": cands}}


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or get_settings()
    cfg.ensure_dirs()
    runner = jobs.JobRunner(cfg)

    # optional watch scheduler (daemon) — start only if explicitly enabled via env
    watch = None
    try:
        import os

        if os.getenv("LDP_WATCH") == "1":
            from lidar_discovery.watch import WatchScheduler

            watch = WatchScheduler(settings=cfg, runner=runner)
    except Exception:
        watch = None

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        jobs.mark_interrupted(cfg)  # jobs of a previous process cannot continue
        if watch is not None:
            try:
                watch.start()
                _app.state.watch = watch
            except Exception:
                pass
        yield
        if watch is not None:
            with suppress(Exception):
                watch.stop()
        runner.shutdown()

    app = FastAPI(title="lidar-discovery-poland", version=__version__, lifespan=lifespan)
    app.state.settings = cfg
    app.state.runner = runner
    if watch is not None:
        app.state.watch = watch
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_methods=["*"],
        allow_headers=["*"],
    )
    get_engine(cfg)  # create tables
    app.include_router(router)
    return app
