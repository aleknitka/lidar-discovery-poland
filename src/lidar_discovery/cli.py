"""`ldp` command line interface."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Annotated

import typer
from shapely.geometry import box

from lidar_discovery import sources as _sources  # noqa: F401  (registers built-in sources)
from lidar_discovery.catalog import repo
from lidar_discovery.catalog.db import session_scope
from lidar_discovery.catalog.models import Location, dumps
from lidar_discovery.config import Settings, get_settings
from lidar_discovery.locations.aoi import aoi_for
from lidar_discovery.sources.base import get_source, source_ids
from lidar_discovery.sources.coverage import compute_coverage, group_tiles

app = typer.Typer(help="Desk-only LiDAR processing framework.", no_args_is_help=True)
locations_app = typer.Typer(help="Manage locations.", no_args_is_help=True)
app.add_typer(locations_app, name="locations")
ml_app = typer.Typer(help="ML detection commands.", no_args_is_help=True)
app.add_typer(ml_app, name="ml")

AoiOpt = Annotated[
    str, typer.Option("--aoi", help="auto = precinct polygon if present, else point buffer; point")
]
BufOpt = Annotated[float | None, typer.Option("--aoi-buffer-m", help="Point buffer radius (m).")]


def _settings() -> Settings:
    s = get_settings()
    s.ensure_dirs()
    return s


def _need_location(session, loc_id: str) -> Location:
    loc = repo.get_location(session, loc_id)
    if loc is None:
        typer.echo(f"unknown location {loc_id!r}; try `ldp locations list`", err=True)
        raise typer.Exit(2)
    return loc


def _parse_interval_to_s(text: str) -> int:
    s = text.strip()
    if s.isdigit():
        return int(s)
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([smhd])$", s.lower())
    if m:
        mul = {"s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(2)]
        return int(float(m.group(1)) * mul)
    try:
        return int(float(s))
    except ValueError:
        raise typer.BadParameter(f"invalid interval {text!r} (examples: 24h, 3600, 1d)") from None


class _Progress:
    """Print download progress at most every 5 s."""

    def __init__(self) -> None:
        self.last = 0.0

    def __call__(self, done: int, total: int | None) -> None:
        if time.perf_counter() - self.last > 5:
            self.last = time.perf_counter()
            typer.echo(f"  {done / 1e6:.0f}/{(total or 0) / 1e6:.0f} MB")


# ------------------------------------------------------------------ locations
@locations_app.command("import-seed")
def import_seed(
    file: Annotated[Path | None, typer.Option(help="Seed YAML.")] = None,
) -> None:
    """Import seeds/locations.yaml into the catalog."""
    from lidar_discovery.locations.seed import import_seed as do_import

    s = _settings()
    path = file or s.seeds_dir / "locations.yaml"
    with session_scope(s) as session:
        locs = do_import(session, path)
    typer.echo(f"imported {len(locs)} locations from {path}: {', '.join(loc.id for loc in locs)}")


@locations_app.command("list")
def list_locations() -> None:
    s = _settings()
    with session_scope(s) as session:
        for loc in repo.list_locations(session):
            poly = "polygon" if loc.polygon else "point"
            typer.echo(f"{loc.id:14} {loc.lon:.5f} {loc.lat:.5f}  {poly}  {loc.names}")


@locations_app.command("fetch-prg")
def fetch_prg(
    location: Annotated[str | None, typer.Argument(help="Location id to update.")] = None,
    name: Annotated[str | None, typer.Option(help="Precinct name (default: names.pl).")] = None,
    bbox: Annotated[
        str | None, typer.Option(help="minlon,minlat,maxlon,maxlat (default: point +-0.12 deg).")
    ] = None,
) -> None:
    """Fetch a PRG cadastral precinct polygon by name inside a bbox and attach it."""
    from lidar_discovery.locations.prg import fetch_precinct

    s = _settings()
    loc = None
    session_ctx = session_scope(s)
    with session_ctx as session:
        if location:
            loc = _need_location(session, location)
        if bbox:
            box_t = tuple(float(v) for v in bbox.split(","))
            if len(box_t) != 4:
                raise typer.BadParameter("bbox needs 4 numbers")
        elif loc:
            d = 0.12
            box_t = (loc.lon - d, loc.lat - d, loc.lon + d, loc.lat + d)
        else:
            raise typer.BadParameter("give a location or --bbox")
        pname = name or (json.loads(loc.names).get("pl") if loc else None)
        if not pname:
            raise typer.BadParameter("give --name")
        try:
            geom, prov = fetch_precinct(pname, box_t, cache_dir=s.cache_dir / "wfs" / "prg")
        except LookupError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(1) from None
        if loc:
            loc.polygon = dumps(geom)
            loc.provenance = dumps(
                [p for p in json.loads(loc.provenance) if p.get("provider") != "prg-wfs"] + [prov]
            )
            repo.upsert_location(session, loc)
            typer.echo(
                f"{loc.id}: precinct {prov['ref']} saved ({len(geom['coordinates'][0])} pts)"
            )
        else:
            typer.echo(json.dumps({"type": "Feature", "geometry": geom, "properties": prov}))


@locations_app.command("wikidata")
def wikidata(name: str) -> None:
    """Search Wikidata for places by name (prints QIDs and coordinates)."""
    from lidar_discovery.locations.wikidata import search_places

    for r in search_places(name):
        typer.echo(
            f"{r['qid']:10} {r['lat']:.5f} {r['lon']:.5f} prec={r['precision_deg']} "
            f"{r['label']} | {r['description']}"
        )


# --------------------------------------------------------------------- sources
@app.command("sources")
def list_sources() -> None:
    """List registered LiDAR sources."""
    s = _settings()
    for sid in source_ids():
        src = get_source(sid, s)
        typer.echo(f"{src.id:16} {src.name} - {src.description}")


@app.command()
def coverage(
    location: str,
    source: Annotated[list[str] | None, typer.Option(help="Source id (repeatable).")] = None,
    year: Annotated[list[int] | None, typer.Option(help="Restrict to year(s).")] = None,
    aoi: AoiOpt = "auto",
    aoi_buffer_m: BufOpt = None,
) -> None:
    """List tiles per source and year (density, no download)."""
    s = _settings()
    with session_scope(s) as session:
        loc = _need_location(session, location)
    area = aoi_for(loc, aoi, aoi_buffer_m)
    t0 = time.perf_counter()
    tiles, errors = compute_coverage(s, area, source, year)
    typer.echo(
        f"AOI {area.area / 1e6:.2f} km2; {len(tiles)} tiles ({time.perf_counter() - t0:.1f}s)"
    )
    typer.echo(f"{'source':16} {'year':>5} {'tiles':>5}  density          crs_h")
    for g in group_tiles(tiles):
        typer.echo(
            f"{g['source_id']:16} {g['year']!s:>5} {g['tiles']:>5}  "
            f"{g['nominal_density']:16} {g['crs_h']}"
        )
    for e in errors:
        typer.echo(f"error: {e}", err=True)


@app.command()
def ingest(
    location: str,
    source: Annotated[str, typer.Option(help="Source id.")],
    year: Annotated[int | None, typer.Option(help="Acquisition year.")] = None,
    max_mb: Annotated[float, typer.Option(help="Skip tiles larger than this (MB).")] = 400.0,
    limit: Annotated[int | None, typer.Option(help="Download at most N tiles.")] = None,
    godlo: Annotated[list[str] | None, typer.Option(help="Only these map sheet ids.")] = None,
    dry_run: Annotated[bool, typer.Option(help="Only list tiles and sizes.")] = False,
    aoi: AoiOpt = "auto",
    aoi_buffer_m: BufOpt = None,
) -> None:
    """Download the tiles covering a location into data/raw/<source>/<year>/ (resumable)."""
    from lidar_discovery.sources.download import download_file, remote_size

    s = _settings()
    with session_scope(s) as session:
        loc = _need_location(session, location)
    src = get_source(source, s)
    tiles = src.list_tiles(aoi_for(loc, aoi, aoi_buffer_m), [year] if year else None)
    if godlo:
        tiles = [t for t in tiles if t.godlo in godlo]
    if limit:
        tiles = tiles[:limit]
    if not tiles:
        typer.echo("no tiles found", err=True)
        raise typer.Exit(1)
    for t in tiles:
        if t.url.startswith("http"):
            t.size_bytes = remote_size(t.url)
        mb = (t.size_bytes or 0) / 1e6
        typer.echo(f"{t.year} {t.godlo} {t.nominal_density} {mb:.0f} MB")
        if dry_run:
            continue
        if mb > max_mb:
            typer.echo(f"  skipped: larger than --max-mb {max_mb:.0f}", err=True)
            continue
        dest = s.raw_dir / source / str(t.year)
        t0 = time.perf_counter()
        progress = _Progress()

        if t.url.startswith("http"):
            path = download_file(
                t.url, dest / Path(t.url.split("?")[0]).name, t.size_bytes, progress
            )
        else:
            path = src.download(t, dest)
        typer.echo(f"  ok {path} ({time.perf_counter() - t0:.1f}s)")


@app.command()
def process(
    location: str,
    source: Annotated[str, typer.Option(help="Source id.")],
    year: Annotated[int, typer.Option(help="Acquisition year (epoch).")],
    res: Annotated[float, typer.Option(help="DTM resolution (m).")] = 0.5,
    svf_radius_m: Annotated[float, typer.Option()] = 10.0,
    input_dir: Annotated[
        Path | None, typer.Option(help="LAS/LAZ folder (default raw dir).")
    ] = None,
    aoi: AoiOpt = "auto",
    aoi_buffer_m: BufOpt = None,
) -> None:
    """Ground points -> DTM -> hillshade/slope/SVF/LRM/density COGs + Product rows."""
    from lidar_discovery.processing.pipeline import ProcessParams, process_aoi
    from lidar_discovery.processing.points import las_bounds

    s = _settings()
    with session_scope(s) as session:
        loc = _need_location(session, location)
    area = aoi_for(loc, aoi, aoi_buffer_m)
    folder = input_dir or s.raw_dir / source / str(year)
    files = sorted([*folder.glob("*.laz"), *folder.glob("*.las")])
    files = [f for f in files if box(*las_bounds(f)).intersects(area)]
    if not files:
        typer.echo(f"no LAS/LAZ files intersecting the AOI in {folder}; run `ldp ingest`", err=True)
        raise typer.Exit(1)
    crs_h = get_source(source, s).crs_h
    t0 = time.perf_counter()
    result = process_aoi(
        s,
        loc.id,
        area,
        source,
        year,
        files,
        crs_h,
        ProcessParams(res=res, svf_radius_m=svf_radius_m),
    )
    with session_scope(s) as session:
        for p in result.products:
            repo.add_product(session, p)
    typer.echo(
        f"{len(result.products)} products in {time.perf_counter() - t0:.1f}s "
        f"(AOI {area.area / 1e6:.2f} km2)"
    )
    for k, v in result.timings.items():
        typer.echo(f"  {k:16} {v:6.1f}s")


@app.command("fetch-bbox")
def fetch_bbox(
    west: float,
    south: float,
    east: float,
    north: float,
    source: Annotated[str | None, typer.Option(help="Source id (default: newest epoch).")] = None,
    year: Annotated[int | None, typer.Option(help="Acquisition year (default: newest).")] = None,
    estimate_only: Annotated[bool, typer.Option(help="Print the estimate and stop.")] = False,
    layers: Annotated[
        str | None,
        typer.Option(
            help="Comma-separated products to build: dtm,hillshade,slope,svf,lrm,ground_density "
            "(dtm is always included). Default: dtm,hillshade,svf,ground_density. Affects "
            "processing time and disk, not the LAZ download size."
        ),
    ] = None,
    auto_detect: Annotated[
        bool,
        typer.Option(
            "--auto-detect",
            help="After processing, run channels derive + rules/anomaly -> Candidate chips.",
        ),
    ] = False,
) -> None:
    """Download only the sheets covering a WGS84 bbox, then process it (same code as the UI)."""
    import threading

    from rich.progress import (
        BarColumn,
        DownloadColumn,
        Progress,
        TextColumn,
        TimeRemainingColumn,
        TransferSpeedColumn,
    )

    from lidar_discovery import areas, jobs

    s = _settings()
    try:
        bbox = areas.parse_bbox([west, south, east, north])
        est = areas.estimate_area(s, bbox, source, year, layers)
    except areas.AreaError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(2) from None
    typer.echo(
        f"{est['area_km2']:.3f} km2, {est.get('source_id')} {est.get('year')}: "
        f"{est['sheets']} sheets, {est['bytes_total'] / 1e6:.0f} MB total, "
        f"{est['bytes_cached'] / 1e6:.0f} MB cached, "
        f"{est['bytes_to_download'] / 1e6:.0f} MB to download"
        + (" (all requested layers already processed)" if est["processed"] else "")
    )
    typer.echo(
        f"layers: {','.join(est['layers'])}; on disk: {','.join(est['layers_existing']) or '-'}; "
        f"to build: {','.join(est['layers_missing']) or '-'}"
        + (" (reusing the existing DTM)" if est["from_existing_dtm"] else "")
    )
    if est["processing_s"]:
        parts = ", ".join(
            f"{k} {v:.0f}s" for k, v in est["processing_s"].items() if k != "total" and v
        )
        typer.echo(f"estimated processing: ~{est['processing_s']['total']:.0f} s ({parts})")
    for t in est["tiles"]:
        state = "cached" if t["cached"] else "to download"
        typer.echo(f"  {t['godlo']:28} {(t['size_bytes'] or 0) / 1e6:7.0f} MB  {state}")
    if estimate_only or not est["tiles"]:
        raise typer.Exit(0 if est["tiles"] or estimate_only else 1)
    job, _ = jobs.create_fetch_job(s, bbox, est["source_id"], est["year"], layers, auto_detect)
    cancel = threading.Event()
    th = threading.Thread(target=jobs.run_fetch_job, args=(s, job.id, cancel), daemon=True)
    th.start()
    with Progress(
        TextColumn("{task.description:28}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as bar:
        task = bar.add_task("starting", total=None)
        try:
            while th.is_alive():
                j = jobs.job_to_dict(jobs.get_job(s, job.id))  # type: ignore[arg-type]
                if j["state"] == "processing":
                    bar.update(
                        task, description=f"processing {j['step_name'] or ''}",
                        total=j["steps"], completed=j["step"],
                    )  # fmt: skip
                else:
                    bar.update(
                        task, description=f"{j['state']} {j['current_item'] or ''}"[:28],
                        total=j["bytes_total"] or None, completed=j["bytes_done"],
                    )  # fmt: skip
                time.sleep(0.5)
        except KeyboardInterrupt:
            cancel.set()
            th.join()
    j = jobs.job_to_dict(jobs.get_job(s, job.id))  # type: ignore[arg-type]
    typer.echo(
        f"{j['state']}: {j['message'] or ''} {j['error'] or ''} (location {j['location_id']})"
    )
    raise typer.Exit(0 if j["state"] == "done" else 1)


# ------------------------------------------------------------------- watch
@app.command("watch")
def watch_cmd(
    bbox: Annotated[
        str | None,
        typer.Option(
            "--bbox",
            help="W,S,E,N bbox in WGS84 (default: Bieszczady 22.10,49.00,22.95,49.70).",
        ),
    ] = None,
    interval: Annotated[
        str,
        typer.Option("--interval", help="Poll interval (e.g. 24h, 1h, 3600s)."),
    ] = "24h",
    once: Annotated[bool, typer.Option("--once", help="Run one poll and exit.")] = False,
) -> None:
    """Poll seeds + PRG precincts, diff WFS caps + provenance freshness (30d), enqueue fetch-area jobs."""
    from lidar_discovery.watch import WatchScheduler

    s = _settings()
    interval_s = _parse_interval_to_s(interval)
    bbox_t: tuple[float, float, float, float] | None = None
    if bbox:
        try:
            parts = [float(x.strip()) for x in bbox.split(",")]
            if len(parts) != 4:
                raise ValueError
            bbox_t = (parts[0], parts[1], parts[2], parts[3])
        except Exception:
            typer.echo("invalid --bbox, expected W,S,E,N", err=True)
            raise typer.Exit(2) from None
    sched = WatchScheduler(settings=s, interval_s=interval_s, bbox=bbox_t)
    if once:
        res = sched.poll_once()
        typer.echo(json.dumps(res, indent=2))
        raise typer.Exit(0)
    sched.start()
    typer.echo(f"watch running: bbox={sched.bbox} interval={interval_s}s (Ctrl-C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sched.stop()
        typer.echo("watch stopped")


# ---------------------------------------------------------------------- ml
@ml_app.command("channels")
def ml_channels(
    location: str,
    epoch: Annotated[int | None, typer.Option("--epoch", help="Epoch year (default: newest).")] = None,
) -> None:
    """Derive lrm5 / fill_depth / support COGs and register Products."""
    s = _settings()
    with session_scope(s) as session:
        _need_location(session, location)
    try:
        from lidar_discovery.ml.channels import derive_channels
    except Exception as e:
        typer.echo(f"channels module not available: {e}", err=True)
        typer.echo("Install ml extras or check src/lidar_discovery/ml/channels.py", err=True)
        raise typer.Exit(1) from None
    try:
        if epoch is not None:
            res = derive_channels(s, location, epoch)
        else:
            res = derive_channels(s, location)
    except Exception as e:
        typer.echo(f"channels failed: {e}", err=True)
        raise typer.Exit(1) from None
    typer.echo(json.dumps(res if isinstance(res, dict) else {"result": str(res)}, indent=2))


@ml_app.command("train-ae")
def ml_train_ae(
    locations: Annotated[str | None, typer.Option("--locations", help="Comma-separated location ids.")] = None,
    epochs: Annotated[int, typer.Option("--epochs", help="Training epochs.")] = 10,
    out: Annotated[str | None, typer.Option("--out", help="Output model dir.")] = None,
) -> None:
    """Train unsupervised autoencoder on random forest-floor patches."""
    try:
        from lidar_discovery.ml.models.autoencoder import train as train_ae  # type: ignore[import-not-found]
    except Exception as e:
        typer.echo(f"autoencoder not available (install ml extras): {e}", err=True)
        raise typer.Exit(1) from None
    s = _settings()
    locs = [x.strip() for x in locations.split(",")] if locations else None
    try:
        res = train_ae(s, locations=locs, epochs=epochs, out_dir=Path(out) if out else None)
    except TypeError:
        # fallback signature
        res = train_ae(s)
    typer.echo(json.dumps(res if isinstance(res, dict) else {"result": str(res)}, indent=2))


@ml_app.command("predict")
def ml_predict(
    location: str,
    model: Annotated[str | None, typer.Option("--model", help="Model version.")] = None,
    budget: Annotated[int | None, typer.Option("--budget", help="Candidates per km².")] = None,
) -> None:
    """Score candidates / sliding window -> Candidates."""
    try:
        from lidar_discovery.ml.predict import predict as do_predict  # type: ignore[import-not-found]
    except Exception as e:
        typer.echo(f"predict not available: {e}", err=True)
        raise typer.Exit(1) from None
    s = _settings()
    try:
        res = do_predict(s, location, model_version=model, budget=budget)
    except TypeError:
        res = do_predict(s, location)
    typer.echo(json.dumps(res if isinstance(res, dict) else {"result": str(res)}, indent=2))


@ml_app.command("evaluate")
def ml_evaluate(
    model: Annotated[str | None, typer.Option("--model", help="Model version.")] = None,
    villages: Annotated[str | None, typer.Option("--villages", help="Comma-separated village ids.")] = None,
    redteam: Annotated[str | None, typer.Option("--redteam", help="Red-team suite (all).")] = None,
) -> None:
    """Evaluate model metrics + intervals + markdown report."""
    try:
        from lidar_discovery.ml.evaluate import evaluate as do_evaluate  # type: ignore[import-not-found]
    except Exception as e:
        typer.echo(f"evaluate not available: {e}", err=True)
        raise typer.Exit(1) from None
    s = _settings()
    vlist = [x.strip() for x in villages.split(",")] if villages else None
    try:
        res = do_evaluate(s, model_version=model, villages=vlist, redteam=redteam)
    except TypeError:
        res = do_evaluate(s, model_version=model)
    if isinstance(res, dict):
        typer.echo(json.dumps(res, indent=2))
    elif isinstance(res, str):
        typer.echo(res)
    else:
        typer.echo(str(res))


@ml_app.command("card")
def ml_card(
    version: Annotated[str, typer.Argument(help="Model version.")],
) -> None:
    """Render model card (intended use, training villages, metrics, etc.)."""
    try:
        from lidar_discovery.ml.registry import render_card  # type: ignore[import-not-found]
    except Exception as e:
        typer.echo(f"registry not available: {e}", err=True)
        raise typer.Exit(1) from None
    s = _settings()
    try:
        out = render_card(s, version)
    except TypeError:
        out = render_card(version)
    if isinstance(out, dict):
        typer.echo(json.dumps(out, indent=2))
    else:
        typer.echo(str(out))


@app.command()
def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
) -> None:
    """Run the API (uvicorn)."""
    import uvicorn

    uvicorn.run(
        "lidar_discovery.api.app:create_app", factory=True, host=host, port=port, reload=reload
    )


@app.command()
def dev(
    api_port: Annotated[int, typer.Option(help="API port.")] = 8000,
    web_port: Annotated[int, typer.Option(help="Web app port.")] = 5173,
    no_browser: Annotated[bool, typer.Option("--no-browser", help="Don't open a browser.")] = False,
    mock: Annotated[bool, typer.Option(help="Web app only, with fixture data (no API).")] = False,
) -> None:
    """Start the API and the web app together (one command) and open the browser."""
    from lidar_discovery.devserver import run_dev

    raise typer.Exit(
        run_dev(api_port=api_port, web_port=web_port, open_browser=not no_browser, mock=mock)
    )


if __name__ == "__main__":
    app()
