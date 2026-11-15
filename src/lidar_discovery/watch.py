"""Autonomous watcher (docs/11 §10): polls seeds+PRG, diffs freshness, enqueues jobs.

Uses APScheduler BackgroundScheduler if available, otherwise a daemon thread loop.
One job at a time.
"""

from __future__ import annotations

import contextlib
import json
import logging
import threading
from datetime import UTC, datetime, timedelta
from typing import Any

from lidar_discovery.config import Settings, get_settings
from lidar_discovery.jobs import create_fetch_job, list_jobs

log = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore

    HAS_APS = True
except Exception:
    HAS_APS = False

DEFAULT_BIESZCZADY_BBOX: tuple[float, float, float, float] = (
    22.10,
    49.00,
    22.95,
    49.70,
)
FRESHNESS_S = 30 * 86400


def _parse_bbox(text: str | None) -> tuple[float, float, float, float] | None:
    if not text:
        return None
    parts = [p.strip() for p in text.replace(",", " ").split() if p.strip()]
    if len(parts) != 4:
        return None
    try:
        return tuple(float(p) for p in parts)  # type: ignore[return-value]
    except Exception:
        return None


def _load_seed_targets(cfg: Settings) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seed_path = cfg.seeds_dir / "locations.yaml"
    if not seed_path.exists():
        with contextlib.suppress(Exception):
            import pathlib as _pl

            alt = _pl.Path("seeds/locations.yaml")
            if alt.exists():
                seed_path = alt
            else:
                return out
    with contextlib.suppress(Exception):
        import yaml  # type: ignore

        data = yaml.safe_load(seed_path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("locations", [])
        for ent in items:
            if not isinstance(ent, dict):
                continue
            pt = ent.get("point") or {}
            lon = ent.get("lon") or pt.get("lon")
            lat = ent.get("lat") or pt.get("lat")
            if lon is None or lat is None:
                continue
            lon_f, lat_f = float(lon), float(lat)
            # filter to Bieszczady bbox
            w, s, e, n = DEFAULT_BIESZCZADY_BBOX
            if not (w <= lon_f <= e and s <= lat_f <= n):
                continue
            buf = float(ent.get("aoi_buffer_m", cfg.default_aoi_buffer_m))
            dlat = buf / 111000.0
            import math as _m

            dlon = buf / (111000.0 * max(0.3, abs(_m.cos(_m.radians(lat_f)))))
            out.append(
                {
                    "id": ent.get("id", f"seed-{lon_f:.3f}-{lat_f:.3f}"),
                    "bbox": (lon_f - dlon, lat_f - dlat, lon_f + dlon, lat_f + dlat),
                    "kind": "seed",
                }
            )
    return out


def _prg_targets(
    cfg: Settings,
    bbox: tuple[float, float, float, float],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with contextlib.suppress(Exception):
        from lidar_discovery.locations.prg import PRG_LAYER, PRG_URL
        from lidar_discovery.sources.wfs import WfsClient

        client = WfsClient(PRG_URL, cache_dir=cfg.cache_dir / "wfs" / "prg")
        w, s, e, n = bbox
        wfs_bbox = f"{s},{w},{n},{e},urn:ogc:def:crs:EPSG::4326"
        feats = client.get_features(PRG_LAYER, bbox=wfs_bbox, page_size=1000)
        for feat in feats[:400]:
            rings = getattr(feat, "rings", None)
            if not rings or not rings[0]:
                continue
            xs = [c[0] for c in rings[0]]
            ys = [c[1] for c in rings[0]]
            if not xs:
                continue
            out.append(
                {
                    "id": f"prg-{feat.attrs.get('JPT_KOD_JE', feat.attrs.get('JPT_NAZWA_', 'x'))}",
                    "bbox": (min(xs), min(ys), max(xs), max(ys)),
                    "kind": "prg",
                }
            )
    return out


def _is_fresh_product(cfg: Settings, loc_id: str) -> bool:
    with contextlib.suppress(Exception):
        from lidar_discovery.catalog.db import session_scope
        from lidar_discovery.catalog.models import Product
        from sqlmodel import select

        cutoff = datetime.now(UTC) - timedelta(seconds=FRESHNESS_S)
        with session_scope(cfg) as s:
            q = select(Product).where(Product.location_id == loc_id).limit(1)  # type: ignore
            rows = list(s.exec(q))
            if not rows:
                return False
            ts = rows[0].created_at
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            return ts >= cutoff
    return False


def _is_fresh_tilecache(cfg: Settings) -> bool:
    with contextlib.suppress(Exception):
        from lidar_discovery.catalog.db import session_scope
        from lidar_discovery.catalog.models import TileCache
        from sqlmodel import select

        cutoff = datetime.now(UTC) - timedelta(seconds=FRESHNESS_S)
        with session_scope(cfg) as s:
            q = select(TileCache).order_by(TileCache.fetched_at.desc()).limit(1)  # type: ignore
            rows = list(s.exec(q))
            if not rows:
                return False
            ts = rows[0].fetched_at
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            return ts >= cutoff
    return False


class WatchScheduler:
    """Poll loop / APScheduler wrapper."""

    def __init__(
        self,
        settings: Settings | None = None,
        interval_s: int | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        auto_detect: bool = False,
        runner: Any | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.interval_s = interval_s or int(self.settings.watch_interval_s)
        parsed = _parse_bbox(self.settings.watch_bbox)
        self.bbox = bbox or parsed or DEFAULT_BIESZCZADY_BBOX
        self.auto_detect = auto_detect
        self.runner = runner
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._sched: Any | None = None
        self.last_run_at: datetime | None = None
        self.last_result: dict[str, Any] | None = None
        self._lock = threading.Lock()

    def _do_poll(self) -> dict[str, Any]:
        from lidar_discovery.areas import location_id_for

        if list_jobs(self.settings, active=True, limit=1):
            return {"status": "skipped", "reason": "job active"}

        # enumerate targets: seeds + PRG that intersect default bbox
        seeds = _load_seed_targets(self.settings)
        prgs = _prg_targets(self.settings, self.bbox)
        targets = seeds + prgs
        if not targets:
            targets = [{"id": "bieszczady", "bbox": self.bbox, "kind": "bbox"}]

        checked = 0
        for tgt in targets:
            bbox = tgt["bbox"]
            try:
                w, s, e, n = bbox
                if not (-180 <= w <= 180 and -180 <= e <= 180 and -90 <= s <= 90 and -90 <= n <= 90):
                    continue
                # quick degenerate check
                if w >= e or s >= n:
                    continue
                from lidar_discovery.areas import aoi_2180

                aoi = aoi_2180((w, s, e, n))
                loc_id = location_id_for(aoi)
                if _is_fresh_product(self.settings, loc_id) and _is_fresh_tilecache(self.settings):
                    checked += 1
                    continue
                checked += 1
                try:
                    job, created = create_fetch_job(
                        self.settings,
                        (w, s, e, n),
                        None,
                        None,
                        None,
                        auto_detect=self.auto_detect,
                    )
                except Exception as exc:  # over_limit or other gating
                    msg = str(exc)
                    low = msg.lower()
                    if "over_limit" in low or "exceeds" in low or "limit" in low:
                        # keep a queued job so operator sees over_limit reason
                        import uuid

                        from lidar_discovery.catalog.db import session_scope
                        from lidar_discovery.catalog.models import Job, dumps

                        jid = uuid.uuid4().hex[:12]
                        payload = {"bbox": list(bbox), "over_limit": msg}
                        with contextlib.suppress(Exception), session_scope(self.settings) as sess:
                                j = Job(
                                    id=jid,
                                    kind="fetch-area",
                                    params=dumps(payload),
                                    state="queued",
                                    message="over_limit",
                                    error=msg,
                                )
                                sess.add(j)
                                sess.commit()
                        return {
                            "status": "queued_over_limit",
                            "target": tgt["id"],
                            "bbox": list(bbox),
                            "reason": msg,
                            "job_id": jid,
                        }
                    log.debug("watch target %s skip: %s", tgt.get("id"), exc)
                    continue
                if not created:
                    return {"status": "exists", "target": tgt["id"], "job_id": job.id}
                if self.runner is not None:
                    with contextlib.suppress(Exception):
                        self.runner.submit(job)
                return {
                    "status": "queued",
                    "target": tgt["id"],
                    "bbox": list(bbox),
                    "job_id": job.id,
                    "created": created,
                }
            except Exception as exc:  # noqa: PERF203
                log.debug("watch target %s failed: %s", tgt.get("id"), exc)
                continue
        return {"status": "up_to_date", "checked": checked, "targets": len(targets)}

    def poll_once(self) -> dict[str, Any]:
        with self._lock:
            res = self._do_poll()
            self.last_run_at = datetime.now(UTC)
            # keep last_result rich but json-safe
            try:
                json.dumps(res)
                self.last_result = res
            except Exception:
                self.last_result = {"status": str(res)}
            return res

    def trigger(self) -> dict[str, Any]:
        return self.poll_once()

    def start(self) -> None:
        if HAS_APS:
            self._sched = BackgroundScheduler(daemon=True)
            self._sched.add_job(self.poll_once, "interval", seconds=self.interval_s, id="watch")
            self._sched.start()
        else:
            self._stop.clear()

            def loop() -> None:
                while not self._stop.is_set():
                    with contextlib.suppress(Exception):
                        self.poll_once()
                    self._stop.wait(self.interval_s)

            self._thread = threading.Thread(target=loop, daemon=True, name="ldp-watch")
            self._thread.start()

    def stop(self) -> None:
        if self._sched is not None:
            with contextlib.suppress(Exception):
                self._sched.shutdown(wait=False)
            self._sched = None
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def status(self) -> dict[str, Any]:
        return {
            "interval_s": self.interval_s,
            "bbox": list(self.bbox),
            "auto_detect": self.auto_detect,
            "has_apscheduler": HAS_APS,
            "running": bool(self._sched or (self._thread and self._thread.is_alive())),
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_result": self.last_result,
        }
