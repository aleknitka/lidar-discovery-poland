# lidar-discovery-poland

Desk-only detection of traces of villages emptied in 1944-1951 in SE Poland from public airborne
LiDAR (GUGiK). This repository is the backend framework: source adapters, DTM/visualisation
processing, a catalogue (SQLite) and a REST API for the React frontend in `frontend/`.
It re-uses public data only; nothing here involves fieldwork. Use "candidate" or "feature",
never "discovery", for findings. See `docs/08-architecture-contract.md` for the binding spec.

## Setup

Requires [uv](https://docs.astral.sh/uv/). Everything installs from PyPI wheels (Windows ok).

```
uv sync                                  # Python 3.12, creates .venv
uv run ldp --help
uv run pytest                            # network tests are skipped (-m network to run them)
uv run ruff check && uv run ruff format --check
```

## Typical run

```
uv run ldp locations import-seed                         # seeds/locations.yaml -> data/catalog.sqlite
uv run ldp locations fetch-prg carynskie                 # optional: PRG cadastral precinct polygon
uv run ldp coverage carynskie --aoi point                # tiles per source/year, density; no download
uv run ldp ingest carynskie --source gugik-kron86 --year 2012 --aoi point --aoi-buffer-m 150 --dry-run
uv run ldp ingest carynskie --source gugik-kron86 --year 2012 --aoi point --aoi-buffer-m 150 --godlo <sheet>
uv run ldp process carynskie --source gugik-kron86 --year 2012 --aoi point --aoi-buffer-m 800
uv run ldp serve                                         # http://127.0.0.1:8000/docs
```

### Get data for this view (viewport fetch)

In the Explore view zoom in (13+), pan to an area and press "Get data for this view": you see an
estimate (sheets, MB to download vs cached), confirm, and the app downloads only the whole map
sheets (~1.2 km) intersecting the view, processes the viewport and shows its layers. Everything is
cached: sheets by size in `data/raw/<source>/<year>/`, results by a processing cache key. Limits:
`LDP_MAX_FETCH_AREA_KM2` (6) and `LDP_MAX_FETCH_BYTES` (4 GB). The CLI equivalent:

```
uv run ldp fetch-bbox 22.612 49.163 22.620 49.168 --source gugik-kron86 --year 2012 --estimate-only
uv run ldp fetch-bbox 22.612 49.163 22.620 49.168 --source gugik-kron86 --year 2012
```

Endpoints: `GET /api/areas/estimate`, `POST /api/areas/fetch`, `GET /api/jobs`, `GET /api/jobs/{id}`,
`POST /api/jobs/{id}/cancel` (see `docs/08-architecture-contract.md`). A killed server marks running
jobs `failed: interrupted`; start the fetch again to resume from the `.part` files.

Use `127.0.0.1` rather than `localhost` on Windows: resolving `localhost` via IPv6 first adds ~2 s per request.
Tiles are ~100 MB (2012 KRON86) to ~600 MB (2023 EVRF2007); `ingest` skips tiles above `--max-mb` (400).
Downloads are streamed to `*.part` and resumed; downloaded files are untrusted data, kept in
`data/raw/` and only ever read by laspy. Settings come from `LDP_*` env vars or `.env`:
`LDP_DATA_DIR` (default `./data`), `LDP_PUBLIC_MODE` (hide restricted items, generalise others,
read-only API).

## Architecture

```
src/lidar_discovery/
  config.py          Settings (LDP_ prefix)
  catalog/           SQLModel tables (Location, Product, Candidate, TileCache; geometry = GeoJSON text),
                     repo.py (row <-> GeoJSON), disclosure.py (public / generalised / restricted)
  locations/         seed YAML import, PRG precinct WFS provider, Wikidata lookup, AOI helpers
  sources/           LidarSource protocol + registry; GUGiK WFS adapters, local-laz, sk-zbgis stub,
                     resumable downloader, coverage
  processing/        points.py (laspy, class 2) -> dtm.py (blockwise TIN, density) -> vis.py
                     (hillshade, slope, SVF, LRM) -> cog.py -> pipeline.py (provenance, Product rows)
  areas.py, jobs.py  viewport estimate + background fetch/process jobs (shared by API and CLI)
  api/               FastAPI app (app.py) and COG -> XYZ PNG rendering (tiles.py, rio-tiler)
  cli.py             `ldp`
```

Data flow: WFS tile index -> `TileRef`s -> LAZ in `data/raw/<source>/<year>/` -> class-2 ground
points -> 0.5 m DTM in EPSG:2180 (cells >6 m from a ground point masked) + ground-density raster ->
multi-direction hillshade, slope, SVF (16 dirs, 10 m), LRM -> COGs in
`data/derived/<location>/<source>-<year>/` + `provenance.json` + `Product` rows -> API.

Caveats: vertical datums differ (KRON86 vs EVRF2007) and epochs are not co-registered; do not
difference them. The DTM quality depends on the ground classification delivered by GUGiK.

## Adding a new LiDAR source

1. Create `src/lidar_discovery/sources/mysource.py` with a class that has `id`, `name`,
   `description`, `crs_h`, `__init__(self, settings)`, `list_tiles(aoi_2180, years=None) -> list[TileRef]`
   and `download(tile, dest_dir) -> Path`, decorated with `@register_source("my-source-id")`.
   (For a GUGiK-style WFS index subclass `GugikWfsSource` in `sources/gugik.py` and set `wfs_url`.)
2. Import the module in `sources/__init__.py` so it registers.
3. Return `TileRef`s with EPSG:2180 bounding boxes (reproject if the source uses another CRS);
   LAS/LAZ must carry or be reprojected to EPSG:2180 before `ldp process`.
4. Add a parser test with a saved fixture (see `tests/test_wfs.py`).

## Seeds

`seeds/locations.yaml` holds hand-curated locations with provenance (Wikidata QIDs). Depopulation
year/cause/source are null until a citation is recorded; do not assume a cause.
Coordinates in `docs/bieszczady-lidar-handoff.md` are wrong and unused.
Wikidata points for Tworylne, Jaworzec and Zawoj are low precision (~0.14 deg): verify via `fetch-prg`.
