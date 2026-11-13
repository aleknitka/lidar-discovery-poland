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
- `GET /api/candidates?location_id=&review_status=` -> FeatureCollection
- `POST /api/candidates` (Feature in) -> created; `PATCH /api/candidates/{id}` (partial)
- Errors: `{"detail": "..."}` with proper status codes. CORS on for localhost dev.

## Frontend (v0 scope)
Routes: `/explore` (internal review workspace) and `/catalog` (public-catalogue placeholder that reads the same API; later uses public mode).
Explore: location list with search -> map fits AOI; a layer switcher for our products (kind x epoch); an opacity slider; a swipe-compare between two layers (e.g. 2012 vs 2023 SVF, or SVF vs basemap); OSM basemap; a coverage panel; candidate markers and a side panel to create, edit and review candidates (draw a point or polygon). Keep map logic in reusable components so later presentation modes (3D, profiles, story view; see 10-presentation-plan.md) can plug in.

## Implementation notes (backend v0, deviations and additions)
- Tile requests outside a raster return a fully transparent 256x256 LA PNG (status 200), not 204. Tiles are greyscale + alpha. Display range per kind is stored in `provenance.display_range`; `slope` is inverted (steep = dark).
- Layer objects additionally carry `location_id`, `crs_h`, `created_at`. `/api/sources` additionally carries `crs_h`. `GET /api/candidates/{id}` exists.
- Coverage items additionally carry `crs_h`; `nominal_density` is a comma-joined string of the distinct `char_przestrz` values.
- `LDP_PUBLIC_MODE=true`: restricted locations and candidates are hidden (404 / omitted), generalised ones are snapped to the 1 km EPSG:2180 cell centre (always as a Point; the precinct polygon is dropped), layers and tiles of non-public locations are not served, and `POST`/`PATCH` return 403 (read-only).
- CLI additions: `--aoi auto|point` and `--aoi-buffer-m` on `coverage`, `ingest`, `process` (default `auto` = precinct polygon if present, else buffered point; a PRG precinct can be 10+ km2, so use `--aoi point` for quick runs); `ldp ingest --max-mb/--godlo/--limit/--dry-run`; `ldp process --input-dir`; `ldp sources`; `ldp locations list|wikidata|fetch-prg <id>`.
- Products are stored as `data/derived/<location>/<source>-<year>/<kind>.tif` plus `provenance.json`; `Product.id = <location>-<source>-<year>-<kind>`; `Product.path` is relative to `data_dir`.
- The DTM is a blockwise Delaunay-linear TIN built from all class-2 points of all intersecting tiles (so no tile seams), cells farther than 6 m from a ground point are masked. SVF samples integer-cell offsets along 16 directions (radius 10 m); LRM = DTM minus a Gaussian low-pass (sigma 10 m).
- Vertical datums are NOT harmonised: `crs_h` is only recorded (KRON86 vs EVRF2007). Never difference epochs without co-registration.
