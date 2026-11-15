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
) -> tuple[Job, bool]:
    """Create a queued job. Returns (job, created); an identical active job is reused.
    `layers` = product kinds to build (default: DTM, hillshade, SVF, ground density; the DTM is
    always included). Unknown kinds raise AreaError (HTTP 422)."""
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
    params = {"bbox": list(bbox), "source_id": source_id, "year": year, "layers": list(want)}
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
            return notify(state="done", message="cached", step=0, steps=0)
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
            settings, lid, aoi, sid, year, paths, chosen.get("crs_h"), params,
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
        return notify(
            state="done", message="done", step=len(names), step_name=None, current_item=None,
            bytes_done=total,
        )  # fmt: skip
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
