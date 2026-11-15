"""Background jobs: "fetch an area" = download needed sheets (resumable) -> process -> Products.

Jobs are rows in the `job` table so progress survives reloads. The API owns a `JobRunner`
(single-worker ThreadPoolExecutor); the CLI calls `run_fetch_job` directly. Both share this code.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable
from concurrent.futures import FIRST_EXCEPTION, ThreadPoolExecutor, wait
from datetime import datetime
from typing import Any

from lidar_discovery.areas import (
    AreaError,
    BBox,
    aoi_2180,
    area_km2,
    cache_key,
    choose_epoch,
    describe_tiles,
    ensure_area_location,
    epochs_of,
    list_area_tiles,
    location_id_for,
    products_for_key,
    tile_path,
)
from lidar_discovery.catalog import repo
from lidar_discovery.catalog.db import session_scope
from lidar_discovery.catalog.models import ACTIVE_JOB_STATES, Job, dumps, utcnow
from lidar_discovery.config import Settings
from lidar_discovery.processing.pipeline import (
    ProcessParams,
    normalise_layers,
    process_aoi,
    step_names,
)
from lidar_discovery.sources import download
from lidar_discovery.sources.base import get_source

PROGRESS_INTERVAL_S = 0.5  # persist progress at most this often
CHUNK = 1 << 20
SPEED_WINDOW_S = 10.0
DOWNLOAD_ATTEMPTS = 3
PARALLEL_TILES = 2


class JobCancelled(Exception):
    pass


# --------------------------------------------------------------------------- persistence
def _iso(d: datetime | None) -> str | None:
    return d.isoformat() if d else None


def job_to_dict(j: Job) -> dict[str, Any]:
    remaining = max(j.bytes_total - j.bytes_done, 0)
    speed = j.speed_bps if j.state == "downloading" else None
    eta = remaining / speed if speed and speed > 0 else None
    if j.state == "downloading":
        progress = j.bytes_done / j.bytes_total if j.bytes_total else 0.0
    elif j.state == "processing":
        progress = j.step / j.steps if j.steps else 0.0
    else:
        progress = (
            1.0 if j.state == "done" else (j.bytes_done / j.bytes_total if j.bytes_total else 0.0)
        )
    return {
        "id": j.id,
        "kind": j.kind,
        "params": json.loads(j.params),
        "state": j.state,
        "bytes_done": j.bytes_done,
        "bytes_total": j.bytes_total,
        "tiles_done": j.tiles_done,
        "tiles_total": j.tiles_total,
        "current_item": j.current_item,
        "tiles": json.loads(j.tiles),
        "step": j.step,
        "steps": j.steps,
        "step_name": j.step_name,
        "speed_bps": speed,
        "eta_s": eta,
        "progress": progress,
        "message": j.message,
        "error": j.error,
        "location_id": j.location_id,
        "created_at": _iso(j.created_at),
        "updated_at": _iso(j.updated_at),
        "finished_at": _iso(j.finished_at),
    }


def get_job(settings: Settings, job_id: str) -> Job | None:
    with session_scope(settings) as s:
        return s.get(Job, job_id)


def list_jobs(settings: Settings, active: bool | None = None, limit: int = 50) -> list[Job]:
    from sqlmodel import select

    with session_scope(settings) as s:
        q = select(Job).order_by(Job.created_at.desc())  # type: ignore[attr-defined]
        if active is True:
            q = q.where(Job.state.in_(ACTIVE_JOB_STATES))  # type: ignore[attr-defined]
        elif active is False:
            q = q.where(Job.state.notin_(ACTIVE_JOB_STATES))  # type: ignore[attr-defined]
        return list(s.exec(q.limit(limit)))


def update_job(settings: Settings, job_id: str, **fields: Any) -> Job:
    with session_scope(settings) as s:
        j = s.get(Job, job_id)
        if j is None:
            raise KeyError(job_id)
        for k, v in fields.items():
            setattr(j, k, dumps(v) if k in ("tiles", "params") and not isinstance(v, str) else v)
        j.updated_at = utcnow()
        if fields.get("state") in ("done", "failed", "cancelled"):
            j.finished_at = utcnow()
        s.add(j)
        s.commit()
        s.refresh(j)
        return j


def mark_interrupted(settings: Settings) -> int:
    """Startup hook: jobs left in a running state by a previous process are failed."""
    n = 0
    for j in list_jobs(settings, active=True, limit=1000):
        update_job(settings, j.id, state="failed", error="interrupted", message="interrupted")
        n += 1
    return n


def create_fetch_job(
    settings: Settings,
    bbox: BBox,
    source_id: str | None,
    year: int | None,
    layers: str | list[str] | tuple[str, ...] | None = None,
    auto_detect: bool = False,
) -> tuple[Job, bool]:
    """Create a queued job. Returns (job, created); an identical active job is reused."""
    try:
        want = normalise_layers(layers)
    except ValueError as e:
        raise AreaError(str(e)) from None
    aoi = aoi_2180(bbox)
    km2 = area_km2(aoi)
    if km2 > settings.max_fetch_area_km2:
        raise AreaError(
            f"area {km2:.2f} km2 exceeds the limit of {settings.max_fetch_area_km2:g} km2; zoom in",
            {
                "estimate": {
                    "bbox": list(bbox),
                    "area_km2": round(km2, 4),
                    "over_limit": "area",
                    "limits": {
                        "max_area_km2": settings.max_fetch_area_km2,
                        "max_bytes": settings.max_fetch_bytes,
                    },
                }
            },
        )
    params: dict[str, Any] = {
        "bbox": list(bbox),
        "source_id": source_id,
        "year": year,
        "layers": list(want),
    }
    if auto_detect:
        params["auto_detect"] = True
    for j in list_jobs(settings, active=True, limit=100):
        if j.kind == "fetch-area" and json.loads(j.params) == params:
            return j, False
    job = Job(id=uuid.uuid4().hex[:12], kind="fetch-area", params=json.dumps(params))
    with session_scope(settings) as s:
        s.add(job)
        s.commit()
        s.refresh(job)
    return job, True


# ------------------------------------------------------------------------------ progress
class Tracker:
    """Aggregates per-sheet byte counts, throttles DB writes, keeps a moving-average speed."""

    def __init__(
        self,
        settings: Settings,
        job_id: str,
        tiles: list[dict[str, Any]],
        cancel: threading.Event,
        on_update: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.settings = settings
        self.job_id = job_id
        self.tiles = tiles
        self.cancel = cancel
        self.on_update = on_update
        self.lock = threading.Lock()
        self.samples: deque[tuple[float, int]] = deque()
        self.last_flush = 0.0
        self.abort = threading.Event()

    def bytes_done(self) -> int:
        return sum(int(t["bytes"]) for t in self.tiles)

    def _speed(self, now: float, done: int) -> float | None:
        self.samples.append((now, done))
        while len(self.samples) > 2 and now - self.samples[0][0] > SPEED_WINDOW_S:
            self.samples.popleft()
        t0, b0 = self.samples[0]
        dt = now - t0
        return (done - b0) / dt if dt > 0.2 and done >= b0 else None

    def flush(self, current: str | None, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self.last_flush < PROGRESS_INTERVAL_S:
            return
        self.last_flush = now
        done = self.bytes_done()
        speed = self._speed(now, done)
        j = update_job(
            self.settings,
            self.job_id,
            bytes_done=done,
            tiles_done=sum(1 for t in self.tiles if t["status"] in ("cached", "done")),
            current_item=current,
            tiles=[{k: v for k, v in t.items() if k != "url"} for t in self.tiles],
            speed_bps=speed,
        )
        if self.on_update:
            self.on_update(job_to_dict(j))

    def check(self) -> None:
        if self.cancel.is_set() or self.abort.is_set():
            raise JobCancelled()

    def tile_progress(self, tile: dict[str, Any]) -> Callable[[int, int | None], None]:
        def cb(done: int, total: int | None) -> None:
            self.check()
            with self.lock:
                tile["bytes"] = done
                self.flush(tile["name"])

        return cb


# ------------------------------------------------------------------------------- the job
def _download_tile(tracker: Tracker, settings: Settings, tile_ref, tile: dict[str, Any]) -> None:
    tracker.check()
    dest = tile_path(settings, tile_ref)
    with tracker.lock:
        tile["status"] = "downloading"
        part = dest.with_name(dest.name + ".part")
        tile["bytes"] = part.stat().st_size if part.exists() else 0
        tracker.flush(tile["name"], force=True)
    last: Exception | None = None
    for _ in range(DOWNLOAD_ATTEMPTS):
        try:
            if tile_ref.url.startswith("http"):
                download.download_file(
                    tile_ref.url,
                    dest,
                    tile["size_bytes"],
                    tracker.tile_progress(tile),
                    chunk=CHUNK,
                )
            else:
                get_source(tile_ref.source_id, settings).download(tile_ref, dest.parent)
            break
        except JobCancelled:
            raise
        except Exception as e:  # transient network error: resume from .part
            last = e
            tracker.check()
            time.sleep(0.2)
    else:
        raise RuntimeError(f"download of {tile['name']} failed: {last}") from last
    with tracker.lock:
        tile["status"] = "done"
        tile["bytes"] = dest.stat().st_size
        tracker.flush(None, force=True)


def on_job_done(settings: Settings, job: Job) -> None:
    """Post-process hook: derive channels -> rule/anomaly -> chips -> Candidate rows.

    Never runs when public_mode is on. Degrades gracefully if ml deps are missing.
    """
    if settings.public_mode:
        return
    if job.state != "done":
        return
    try:
        params = json.loads(job.params)
    except Exception:
        return
    if not params.get("auto_detect"):
        return
    loc_id = job.location_id
    if not loc_id:
        return
    import hashlib as _hashlib
    import logging as _log

    _logger = _log.getLogger(__name__)
    try:
        from lidar_discovery.catalog import repo as _repo
        from lidar_discovery.catalog.db import session_scope as _ss
        from lidar_discovery.catalog.models import Candidate
        from lidar_discovery.catalog.models import dumps as _dumps
        from lidar_discovery.processing.pipeline import PIPELINE_VERSION, code_version

        with _ss(settings) as s:
            products = _repo.list_products(s, loc_id)
        input_ids = [p.id for p in products]
        git_sha = ""
        try:
            git_sha = code_version()
        except Exception:
            git_sha = ""
        base_prov: dict[str, Any] = {
            "input_product_ids": input_ids,
            "pipeline_version": PIPELINE_VERSION,
            "git_sha": git_sha,
            "job_id": job.id,
        }
        try:
            import inspect as _ins

            import lidar_discovery.ml.channels as _ch  # type: ignore[import-not-found]

            spec = _ins.getsource(_ch)
            base_prov["channel_spec_hash"] = _hashlib.sha256(spec.encode()).hexdigest()[:12]
        except Exception:
            base_prov["channel_spec_hash"] = None
        try:
            import lidar_discovery.ml.channels as _ch2  # type: ignore[import-not-found]

            if hasattr(_ch2, "derive_channels"):
                _ch2.derive_channels(settings, loc_id)
            elif hasattr(_ch2, "derive"):
                _ch2.derive(settings, loc_id)
        except Exception as e:
            _logger.debug("derive_channels skipped: %s", e)

        arrays: dict[str, Any] = {}
        grid = None
        try:
            import rasterio as _rio  # type: ignore[import-not-found]

            from lidar_discovery.processing.dtm import Grid as _Grid

            with _ss(settings) as s:
                prods = {p.kind: p for p in _repo.list_products(s, loc_id)}
            if "dtm" in prods:
                dtm_path = settings.data_dir / prods["dtm"].path
                with _rio.open(dtm_path) as ds:
                    grid = _Grid(
                        x0=ds.transform.c,
                        y1=ds.transform.f,
                        res=ds.res[0],
                        width=ds.width,
                        height=ds.height,
                    )
                    dtm = ds.read(1).astype(float)
                    if ds.nodata is not None:
                        dtm[dtm == ds.nodata] = float("nan")
                    arrays["dtm"] = dtm
                for k in (
                    "hillshade",
                    "slope",
                    "svf",
                    "lrm",
                    "ground_density",
                    "lrm5",
                    "fill_depth",
                    "support",
                ):
                    if k in prods:
                        try:
                            pth = settings.data_dir / prods[k].path
                            with _rio.open(pth) as ds:
                                a = ds.read(1).astype(float)
                                if ds.nodata is not None:
                                    a[a == ds.nodata] = float("nan")
                                arrays[k] = a
                        except Exception:
                            continue
        except Exception as e:
            _logger.debug("array load skipped: %s", e)

        candidates_raw: list[dict[str, Any]] = []
        try:
            import lidar_discovery.detect.rules as _rules  # type: ignore[import-not-found]

            if arrays and grid is not None:
                for fn_name in (
                    "detect_closed_depressions",
                    "detect_lrm_blobs",
                    "detect_linears",
                    "detect_all",
                ):
                    fn = getattr(_rules, fn_name, None)
                    if fn is None:
                        continue
                    try:
                        out = fn(arrays, grid)
                        if isinstance(out, list):
                            candidates_raw.extend([c for c in out if isinstance(c, dict)])
                        elif isinstance(out, dict) and "candidates" in out:
                            candidates_raw.extend(out["candidates"])
                    except Exception as e:
                        _logger.debug("rule %s failed: %s", fn_name, e)
                    if fn_name == "detect_all":
                        break
        except Exception as e:
            _logger.debug("rules import skipped: %s", e)

        try:
            import lidar_discovery.detect.anomaly as _anom  # type: ignore[import-not-found]

            if arrays and grid is not None and hasattr(_anom, "detect_anomalies"):
                try:
                    out = _anom.detect_anomalies(arrays, grid)
                    if isinstance(out, list):
                        candidates_raw.extend([c for c in out if isinstance(c, dict)])
                except Exception as e:
                    _logger.debug("anomaly failed: %s", e)
            elif arrays and hasattr(_anom, "anomaly_map"):
                try:
                    amap = _anom.anomaly_map(arrays)
                    if isinstance(amap, dict) and "candidates" in amap:
                        candidates_raw.extend(amap["candidates"])
                except Exception as e:
                    _logger.debug("anomaly_map failed: %s", e)
        except Exception as e:
            _logger.debug("anomaly import skipped: %s", e)

        if not candidates_raw:
            _logger.info("auto-detect: no candidates for %s", loc_id)
            return

        from pyproj import Transformer as _Tr

        _to_4326 = _Tr.from_crs(2180, 4326, always_xy=True)
        import uuid as _uuid

        created = 0
        for raw in candidates_raw[:200]:
            try:
                geom = raw.get("geometry")
                if geom is None:
                    if "lon" in raw and "lat" in raw:
                        geom = {
                            "type": "Point",
                            "coordinates": [float(raw["lon"]), float(raw["lat"])],
                        }
                    elif "x" in raw and "y" in raw and grid is not None:
                        lon, lat = _to_4326.transform(float(raw["x"]), float(raw["y"]))
                        geom = {"type": "Point", "coordinates": [lon, lat]}
                    else:
                        continue
                low_support = bool(raw.get("low_support", False))
                score = raw.get("score", raw.get("model_score", raw.get("confidence", 0.0)))
                try:
                    score_f = float(score)
                except Exception:
                    score_f = 0.0
                prov = dict(base_prov)
                prov["score"] = score_f
                prov["score_sd"] = raw.get("score_sd")
                prov["low_support"] = low_support
                prov["morph_class_raw"] = raw.get("morph_class")
                prov["detector"] = raw.get("origin", raw.get("detector", "rule"))
                if "chips" in raw:
                    prov["chips"] = raw["chips"]
                morph = raw.get("morph_class", "other")
                from lidar_discovery.catalog.models import MORPH_CLASSES as _MC

                if morph not in _MC:
                    morph = "other"
                cand = Candidate(
                    id=_uuid.uuid4().hex[:12],
                    location_id=loc_id,
                    geometry=_dumps(geom),
                    morph_class=morph,
                    reality="unassessed",
                    reality_confidence=max(0.0, min(1.0, score_f)) if 0 <= score_f <= 1 else 0.0,
                    origin=raw.get("origin", "rule"),
                    model_version=raw.get("model_version", PIPELINE_VERSION),
                    review_status="proposed",
                    disclosure="restricted",
                    provenance=_dumps(prov),
                )
                with _ss(settings) as s:
                    s.add(cand)
                    s.commit()
                try:
                    from lidar_discovery.chips import export_chips_for_candidate as _ecc

                    chips = _ecc(settings, cand, arrays, grid)  # type: ignore[arg-type]
                    if chips:
                        with _ss(settings) as s2:
                            row = s2.get(Candidate, cand.id)
                            if row is not None:
                                p2prov = json.loads(row.provenance) if row.provenance else {}
                                p2prov["chips"] = chips
                                row.provenance = _dumps(p2prov)
                                s2.add(row)
                                s2.commit()
                except Exception as e:
                    _logger.debug("chip export failed for %s: %s", cand.id, e)
                created += 1
            except Exception as e:
                _logger.debug("candidate create failed: %s", e)
                continue
        _logger.info("auto-detect: created %d candidates for %s", created, loc_id)
    except Exception as e:
        _log.getLogger(__name__).warning("on_job_done failed: %s", e)


def run_fetch_job(
    settings: Settings,
    job_id: str,
    cancel: threading.Event | None = None,
    on_update: Callable[[dict[str, Any]], None] | None = None,
) -> Job:
    """Run a queued fetch-area job to completion (blocking). Never raises; sets the final state."""
    cancel = cancel or threading.Event()
    job = get_job(settings, job_id)
    if job is None or job.state != "queued":
        return job  # type: ignore[return-value]
    p = json.loads(job.params)
    bbox: BBox = tuple(p["bbox"])  # type: ignore[assignment]
    want = normalise_layers(p.get("layers"))  # jobs created before layer selection: the default

    def notify(**fields: Any) -> Job:
        j = update_job(settings, job_id, **fields)
        if on_update:
            on_update(job_to_dict(j))
        return j

    tracker: Tracker | None = None
    try:
        aoi = aoi_2180(bbox)
        lid = location_id_for(aoi)
        notify(state="listing", message="Finding LiDAR sheets", location_id=lid)
        tiles_all, errors = list_area_tiles(settings, aoi)
        if errors and not tiles_all:
            raise RuntimeError("; ".join(errors))
        chosen = choose_epoch(epochs_of(tiles_all), p.get("source_id"), p.get("year"))
        if chosen is None:
            raise RuntimeError("no LiDAR coverage for this area and epoch")
        sid, year = chosen["source_id"], chosen["year"]
        key = cache_key(sid, year, aoi)
        notify(params=dumps({**p, "source_id": sid, "year": year, "layers": list(want)}))
        if cancel.is_set():
            raise JobCancelled()

        existing = products_for_key(settings, lid, sid, year, key)
        missing = [k for k in want if k not in existing]
        if not missing:  # everything requested exists: instant
            ensure_area_location(settings, bbox, aoi, key)
            j = notify(state="done", message="cached", step=0, steps=0)
            try:
                pj = json.loads(j.params)
                if pj.get("auto_detect"):
                    on_job_done(settings, j)
            except Exception:
                pass
            return j
        # the DTM is the expensive part: reuse it when it exists
        reuse_dtm = "dtm" in existing
        kinds = tuple(missing) if reuse_dtm else want
        # only ground_density needs the points once the DTM exists
        needs_points = (not reuse_dtm) or "ground_density" in kinds

        refs = sorted(
            (t for t in tiles_all if t.source_id == sid and t.year == year),
            key=lambda t: t.godlo or "",
        )
        total = 0
        tiles: list[dict[str, Any]] = []
        if needs_points:
            described = describe_tiles(settings, refs)
            total = sum(d["size_bytes"] or 0 for d in described)
            if total > settings.max_fetch_bytes:
                raise RuntimeError(
                    f"{total / 1e9:.2f} GB of LiDAR exceeds the limit of "
                    f"{settings.max_fetch_bytes / 1e9:.2f} GB"
                )
            tiles = [
                {
                    "godlo": d["godlo"],
                    "name": d["name"],
                    "url": d["url"],
                    "size_bytes": d["size_bytes"] or 0,
                    "status": "cached" if d["cached"] else "pending",
                    "bytes": d["size_bytes"] if d["cached"] else d["partial_bytes"],
                    "footprint": d["footprint"],
                }
                for d in described
            ]
        ensure_area_location(settings, bbox, aoi, key)
        tracker = Tracker(settings, job_id, tiles, cancel, on_update)
        update_job(settings, job_id, bytes_total=total, tiles_total=len(tiles))
        if tiles:
            notify(
                state="downloading",
                message="Downloading LiDAR",
                tiles=[{k: v for k, v in t.items() if k != "url"} for t in tiles],
                bytes_done=tracker.bytes_done(),
                tiles_done=sum(1 for t in tiles if t["status"] == "cached"),
            )

        # (tiles is empty when no LAZ is needed)
        todo = [(r, t) for r, t in zip(refs, tiles, strict=False) if t["status"] != "cached"]
        if todo:
            with ThreadPoolExecutor(max_workers=PARALLEL_TILES) as pool:
                futs = [pool.submit(_download_tile, tracker, settings, r, t) for r, t in todo]
                wait(futs, return_when=FIRST_EXCEPTION)
                for f in futs:
                    if f.done() and f.exception():
                        tracker.abort.set()
                for f in futs:
                    f.result()
        tracker.flush(None, force=True)
        if cancel.is_set():
            raise JobCancelled()

        # ---- processing
        params = ProcessParams(kinds=kinds)
        names = step_names(params, reuse_dtm)
        notify(
            state="processing", message="Processing", steps=len(names), step=0, current_item=None
        )
        counter = {"i": 0}

        def on_step(name: str) -> None:
            if cancel.is_set():
                raise JobCancelled()
            counter["i"] += 1
            notify(step=counter["i"], step_name=name, message=f"Processing: {name}")

        paths = [tile_path(settings, r) for r in refs]
        result = process_aoi(
            settings,
            lid,
            aoi,
            sid,
            year,
            paths,
            chosen.get("crs_h"),
            params,
            on_step=on_step,
            extra_provenance={
                "cache_key": key,
                "bbox_2180": [round(v) for v in aoi.bounds],
                "layers_requested": list(want),
            },
            dtm_path=settings.data_dir / existing["dtm"].path if reuse_dtm else None,
        )  # fmt: skip
        with session_scope(settings) as s:
            for prod in result.products:
                repo.add_product(s, prod)
        done_job = notify(
            state="done",
            message="done",
            step=len(names),
            step_name=None,
            current_item=None,
            bytes_done=total,
        )  # fmt: skip
        try:
            pj2 = json.loads(done_job.params)
            if pj2.get("auto_detect"):
                on_job_done(settings, done_job)
        except Exception:
            pass
        return done_job
    except JobCancelled:
        return notify(state="cancelled", message="cancelled", current_item=None)
    except Exception as e:
        return notify(state="failed", error=str(e) or type(e).__name__, message="failed")
    finally:
        if tracker:
            tracker.abort.set()


# ------------------------------------------------------------------------------- runner
class JobRunner:
    """One job at a time, owned by the app lifespan."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ldp-job")
        self.cancels: dict[str, threading.Event] = {}
        self.lock = threading.Lock()

    def submit(self, job: Job) -> None:
        ev = threading.Event()
        with self.lock:
            self.cancels[job.id] = ev

        def work() -> None:
            try:
                run_fetch_job(self.settings, job.id, ev)
            finally:
                with self.lock:
                    self.cancels.pop(job.id, None)

        self.pool.submit(work)

    def cancel(self, job_id: str) -> Job | None:
        job = get_job(self.settings, job_id)
        if job is None:
            return None
        if job.state not in ACTIVE_JOB_STATES:
            return job
        with self.lock:
            ev = self.cancels.get(job_id)
        if ev is not None:
            ev.set()
        if job.state == "queued" or ev is None:  # not picked up yet / orphaned
            return update_job(self.settings, job_id, state="cancelled", message="cancelled")
        return job

    def shutdown(self) -> None:
        with self.lock:
            for ev in self.cancels.values():
                ev.set()
        self.pool.shutdown(wait=True, cancel_futures=True)
