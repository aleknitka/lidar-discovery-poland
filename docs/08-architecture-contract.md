# 08 - Architecture contract (framework v0)

Binding interface between the backend and frontend work. Change it only by editing this file and saying so in your report. Background: 05-synthesis.md, 06-critique.md, 07-decisions.md (desk-only scope).

## Stack
- **Backend:** Python 3.12 via `uv` (`uv python pin 3.12`; `requires-python = ">=3.12,<3.14"`), `ruff` (lint + format), `pytest`. FastAPI + uvicorn, Typer CLI, pydantic v2 / pydantic-settings, SQLModel on SQLite, httpx, laspy[lazrs], numpy, scipy, rasterio, pyproj, shapely, rio-tiler. No PDAL or GDAL-from-conda: everything must install from PyPI wheels on Windows. Raster visualisations (hillshade, slope, SVF, LRM) are implemented in numpy/scipy (rvt-py cannot install on 3.12; its algorithms are the reference).
- **Frontend:** `frontend/`, React 18 + TypeScript + Vite, MapLibre GL JS, TanStack Query, react-router. ESLint + Prettier. The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

## Repository layout
```
pyproject.toml, uv.lock, .python-version (3.12), ruff config in pyproject
src/lidar_discovery/
  config.py            # Settings (env prefix LDP_), data_dir, public_mode
  sources/             # LiDAR source adapters (plugin registry)
  locations/           # location providers (seed YAML, PRG precincts, Wikidata)
  processing/          # ground filter -> DTM -> visualisations -> COG
  catalog/             # SQLModel models + repository functions
  api/                 # FastAPI app, routers
  cli.py               # `ldp` entry point
data/                  # gitignored: raw/, derived/, catalog.sqlite
seeds/locations.yaml   # hand-curated seed locations with provenance
tests/
frontend/
```

## Core concepts
- **Source** (`LidarSource` protocol): `id`, `name`, `crs_h`, `list_tiles(aoi_2180: Polygon) -> list[TileRef]`, `download(tile, dest_dir) -> Path`. Registered in a registry so new sources plug in. v0 sources:
  - `gugik-kron86`: WFS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarKRON86/WFS/Skorowidze`, layers `gugik:SkorowidzDanychPomiarowychLIDAR{2010..2019}`
  - `gugik-evrf2007`: WFS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarEVRF2007/WFS/Skorowidze` (enumerate layers from GetCapabilities; 2023 and 2025 exist in the study area)
  - `local-laz`: a folder of LAS/LAZ files
  - `sk-zbgis`: stub with a TODO (Slovak open ALS, CC BY 4.0)
  - WFS facts: WFS 2.0.0, GetFeature with `BBOX=minlat,minlon,maxlat,maxlon,urn:ogc:def:crs:EPSG::4326`, or a bbox in EPSG:2180. Attributes: `godlo`, `akt_rok`, `akt_data`, `char_przestrz` (e.g. "4 p/m2"), `format`, `blad_sr_wys`, `uklad_xy`, `uklad_h`, `url_do_pobrania`.
- **TileRef**: `source_id, tile_id, godlo, year, acq_date, nominal_density, bbox_2180, url, crs_h, size_bytes?`
- **Location**: a former village (or any area of interest). Fields: `id` (slug), `names` {pl, uk, other}, `point` (WGS84 lon/lat), `polygon?` (WGS84, e.g. the PRG cadastral precinct from WFS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries`, layer `ms:A06_Granice_obrebow_ewidencyjnych`), `depopulation` {year?, cause?, source_url?} (nullable; never assume "Operation Vistula"), `provenance` [ {provider, ref, fetched_at} ], `disclosure` (see below). AOI = polygon if present, else a point buffer (default 1000 m).
- **Product (layer)**: a derived raster for a location and epoch. Fields: `id, location_id, source_id, epoch (year), kind (dtm|hillshade|slope|svf|lrm|ground_density|...), path (COG, EPSG:2180), resolution_m, bounds_wgs84, provenance` (input tiles, parameters, code version, created_at).
- **Candidate (finding)**: `id, location_id?, geometry (GeoJSON WGS84), morph_class (house_platform|cellar_pit|terrace|holloway|field_boundary|cemetery|church_site|other), reality (unassessed|artefact|natural|anthropogenic) + confidence 0-1, dating_evidence (free text + sources), documentation_status (list of {source, ref, found: bool}), origin (manual|rule|ml|vlm) + model_version?, review_status (proposed|accepted|rejected|needs_second_opinion), reviewer_notes, disclosure, created_at, updated_at`. Never use the word "discovery" in field names or UI copy. Use "candidate" or "feature".
- **Disclosure**: `public | generalised | restricted`. When `LDP_PUBLIC_MODE=true` the API hides restricted items and snaps the geometry of generalised items to the centroid of a 1 km grid cell. Cemeteries and graves default to `restricted`. This is the foundation of the later public catalogue.

## Pipeline (CLI `ldp`)
- `ldp locations import-seed` / `ldp locations fetch-prg --bbox ...`
- `ldp coverage <location>`: list tiles per source and year, nominal density, no download
- `ldp ingest <location> --source gugik-evrf2007 [--year 2023]`: download tiles into `data/raw/<source>/<year>/`. Idempotent and resumable (skip if size matches; .part files).
- `ldp process <location> --source ... --year ...`: class-2 ground points -> DTM 0.5 m (TIN/linear via scipy griddata or a nearest + fill fallback) -> ground-density raster -> hillshade (multi-direction), slope, SVF (16 directions, radius 10 m), LRM (lowpass ~ 20 m) -> COG under `data/derived/<location>/<source>-<year>/`. Clipped to the AOI. Record provenance.
- `ldp serve`: run the API.

## REST API (prefix /api, JSON; GeoJSON in WGS84)
- `GET /api/health`
- `GET /api/sources` -> [{id, name, description}]
- `GET /api/locations` -> FeatureCollection (properties: id, names, depopulation, has_products)
- `GET /api/locations/{id}` -> Feature with full properties
- `GET /api/locations/{id}/coverage` -> [{source_id, year, tiles, nominal_density, bbox}]
- `GET /api/locations/{id}/layers` -> [{id, kind, epoch, source_id, resolution_m, bounds: [w,s,e,n], tile_url: "/api/layers/{id}/tiles/{z}/{x}/{y}.png", provenance}]
- `GET /api/layers/{layer_id}/tiles/{z}/{x}/{y}.png`: XYZ Web Mercator tiles rendered from the COG (rio-tiler). Greyscale ramp per kind, transparent outside data. 204 or a transparent tile outside bounds.
- `GET /api/areas/estimate?bbox=w,s,e,n&source_id=&year=&layers=`: "Get data for this view". bbox is the viewport (WGS84). Returns `{bbox, area_km2, source_id, year, epochs: [{source_id, year, tiles, nominal_density, crs_h}] (newest first; the default epoch is the newest), tiles: [{godlo, name, size_bytes, cached, partial_bytes, nominal_density, footprint (GeoJSON Polygon)}], sheets, bytes_total, bytes_cached, bytes_to_download, location_id, processed, limits, layers, layers_existing, layers_missing, from_existing_dtm, needs_laz, processing_s}`. Sheet size = Content-Length from a HEAD (cached in `TileCache`, 30 d); `cached` = `data/raw/<source>/<year>/<file>` exists with that size. 422 `{detail, estimate: {..., over_limit: "area"|"bytes", limits}}` when the area exceeds `LDP_MAX_FETCH_AREA_KM2` (6) or the sheets exceed `LDP_MAX_FETCH_BYTES` (4 GB); 502 if every source index fails.
- `POST /api/areas/fetch {bbox, source_id?, year?, layers?}` -> 202 Job (see below). An identical active job is returned instead of a duplicate. 403 in public mode, 422 over the area limit.
- `GET /api/jobs?active=true`, `GET /api/jobs/{id}`, `POST /api/jobs/{id}/cancel`.
- `GET /api/candidates?location_id=&review_status=` -> FeatureCollection
- `POST /api/candidates` (Feature in) -> created; `PATCH /api/candidates/{id}` (partial)
- Errors: `{"detail": "..."}` with proper status codes. CORS on for localhost dev.

## Layer selection (`layers`)
- `layers` = comma-separated (or JSON list on POST) product kinds from `dtm, hillshade, slope, svf, lrm, ground_density`. Default `dtm,hillshade,svf,ground_density`. The DTM is always included; the order is canonical. An unknown kind gives 422 on both endpoints. CLI: `ldp fetch-bbox ... --layers dtm,svf`.
- The estimate adds: `layers` (normalised), `layers_existing` (already built for this area, epoch and cache key), `layers_missing`, `from_existing_dtm` (missing kinds are derived from the DTM on disk), `needs_laz` (false when nothing needs the LAZ sheets; `bytes_to_download` is then 0), `processing_s` (`{kind: seconds, points, total}`, estimated from measured times; null when nothing to build), `processed` (all requested layers exist).
- **Layer selection saves processing time and disk only. The LAZ sheet download (100-600 MB per sheet) is the same whichever layers are picked.**
- Cache key: `cache_key(source, year, bbox, params, PIPELINE_VERSION)` identifies the area and its DTM and does not include the layer set (it is stored in each Product's `provenance.cache_key`). `layers_key(cache_key, layers)` identifies one request. Job `params` carry `layers`; identical active jobs are de-duplicated on them. If products with the key exist, only the missing kinds are built: from the stored DTM (edge-padded by the processing margin, so SVF/LRM within ~30 m of the area edge differ slightly from a full run; `provenance.computed_from = "existing-dtm (edge-padded)"`), reading the LAZ points only for `ground_density`. If everything requested exists the job finishes at once with message `cached`.
- Tiles: `GET /api/layers/{id}/tiles/{z}/{x}/{y}.png?shade=0..1`. The DTM is drawn as a hypsometric colour ramp stretched over the area's 1st-99th percentile (`provenance.display_range`); `shade` (default 0 = plain elevation) blends a hillshade into it as a preview aid.
- Processing time model (`processing/pipeline.py`, measured): DTM about 18 s + 11 s/km2, SVF 2.2 s/km2, hillshade 0.6, LRM 0.6, slope 0.35, ground density 0.15, each COG write about 0.2 s + 0.55 s/km2, reading a sheet's points about 1.5 s.

## Jobs and viewport areas
- **Job** (SQLModel table `job`, persisted in SQLite): `id, kind ('fetch-area'), params {bbox, source_id, year}, state (queued|listing|downloading|processing|done|failed|cancelled), bytes_done, bytes_total, tiles_done, tiles_total, current_item, tiles [{godlo, name, status (pending|cached|downloading|done|failed), bytes, size_bytes, footprint}], step, steps, step_name, message, error, location_id, created_at, updated_at, finished_at`. The API adds `speed_bps` (moving average over 10 s), `eta_s` and `progress` (0..1). `bytes_*` count only the selected epoch's sheets (cached sheets included, so a fully cached job starts at 100 %).
- Runner: in-process, owned by the FastAPI lifespan (`ThreadPoolExecutor(1)`: one job at a time, 2 parallel sheet downloads). Progress is persisted at most every 0.5 s. On startup jobs left in a running state become `failed` with error `interrupted`; a re-run resumes from the `.part` files (HTTP Range). Cancel is cooperative (checked between chunks and processing steps) and keeps `.part` files.
- Processing steps reported as `step/steps`: ground points, dtm, density, hillshade, slope, svf, lrm, write. The pipeline runs on the viewport rectangle (EPSG:2180, rounded to 1 m) with an internal margin of max(SVF radius, 3 x LRM sigma) + 1 m (31 m by default) and clips outputs to it.
- **Area Location**: `Location.kind` is `'village'` (default) or `'area'`. A fetched area has `id = area-<hash8 of the 1 m EPSG:2180 bbox>` (so several epochs of one viewport share a location), `names.other = "Area 49.165N 22.612E"`, the bbox as `polygon`, `disclosure = restricted`. `kind` is in `GET /api/locations` properties. Older databases get the column added automatically.
- **Processing cache key** = hash(source, year, bbox at 1 m, processing params, `PIPELINE_VERSION`), stored in each Product's `provenance.cache_key`. If products with that key exist the job completes at once (`message: "cached"`). Raw sheets are never refetched while the file size equals Content-Length. No per-sheet size cap for these jobs (the totals limit applies).
- CLI: `ldp fetch-bbox W S E N [--source ID] [--year Y] [--estimate-only]` runs the same job code with a rich progress bar.

## Frontend (v0 scope)
Routes: `/explore` (internal review workspace) and `/catalog` (public-catalogue placeholder that reads the same API; later uses public mode).
Explore: map fills the screen with a collapsible right-hand panel (tabs Layers, Info, Candidates, Places, Data; bottom sheet on phones; state in localStorage); first view = whole Bieszczady with no markers; Places tab = search + collapsed groups of seed villages and fetched areas; Info tab = layer explanations from `frontend/src/content/layers.ts`; a layer switcher for our products (kind x epoch); an opacity slider; a swipe-compare between two layers (e.g. 2012 vs 2023 SVF, or SVF vs basemap); OSM basemap; a coverage panel; candidate markers and a side panel to create, edit and review candidates (draw a point or polygon). Explore also has a "Get data for this view" button (enabled from zoom 13): estimate card (epoch selector, area, sheets, MB to download / cached, limit warnings, sheet footprints on the map), then a progress panel polling `/api/jobs/{id}` every second; the panel re-attaches to active jobs after a reload, and on completion the new area is selected with its DTM layer on. The estimate card shows cache state per sheet (legend, table, stacked bar), the view area against the limit and the layer checkboxes. Fetched areas are listed in a separate "Fetched areas" group. Keep map logic in reusable components so later presentation modes (3D, profiles, story view; see 10-presentation-plan.md) can plug in.

## Implementation notes (backend v0, deviations and additions)
- Tile requests outside a raster return a fully transparent 256x256 LA PNG (status 200), not 204. Tiles are greyscale + alpha. Display range per kind is stored in `provenance.display_range`; `slope` is inverted (steep = dark).
- Layer objects additionally carry `location_id`, `crs_h`, `created_at`. `/api/sources` additionally carries `crs_h`. `GET /api/candidates/{id}` exists.
- Coverage items additionally carry `crs_h`; `nominal_density` is a comma-joined string of the distinct `char_przestrz` values.
- `LDP_PUBLIC_MODE=true`: restricted locations and candidates are hidden (404 / omitted), generalised ones are snapped to the 1 km EPSG:2180 cell centre (always as a Point; the precinct polygon is dropped), layers and tiles of non-public locations are not served, and `POST`/`PATCH` return 403 (read-only).
- CLI additions: `--aoi auto|point` and `--aoi-buffer-m` on `coverage`, `ingest`, `process` (default `auto` = precinct polygon if present, else buffered point; a PRG precinct can be 10+ km2, so use `--aoi point` for quick runs); `ldp ingest --max-mb/--godlo/--limit/--dry-run`; `ldp process --input-dir`; `ldp sources`; `ldp locations list|wikidata|fetch-prg <id>`.
- Products are stored as `data/derived/<location>/<source>-<year>/<kind>.tif` plus `provenance.json`; `Product.id = <location>-<source>-<year>-<kind>`; `Product.path` is relative to `data_dir`.
- The DTM is a blockwise Delaunay-linear TIN built from all class-2 points of all intersecting tiles (so no tile seams), cells farther than 6 m from a ground point are masked. SVF samples integer-cell offsets along 16 directions (radius 10 m); LRM = DTM minus a Gaussian low-pass (sigma 10 m).
- Vertical datums are NOT harmonised: `crs_h` is only recorded (KRON86 vs EVRF2007). Never difference epochs without co-registration.
