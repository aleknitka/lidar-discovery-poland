# lidar-discovery-poland

**Finding the traces of lost villages under the forests of south-eastern Poland with public airborne LiDAR.**

Between 1944 and 1951 more than a hundred villages in the Bieszczady and the neighbouring Carpathian foothills were emptied. The causes included deportations to the Ukrainian SSR (1944-46), forced expulsions (1946), Operation Vistula (1947) and the Polish-Soviet border exchange (1951). Most of those villages were later demolished and swallowed by forest. Their house platforms, cellar pits, terraces, sunken roads, field boundaries, churches and cemeteries often survive as subtle earthworks under the trees, invisible from the air but visible in LiDAR terrain models.

This project builds an open, reproducible, desk-based workflow to:

1. **acquire** public LiDAR point clouds (Polish GUGiK national ALS, with more sources pluggable),
2. **process** them into bare-earth terrain models and archaeological visualisations (hillshade, slope, sky-view factor, local relief),
3. **review and record** candidate man-made features in a web app, with their evidence and documentation status, and later rank them with simple rules and machine learning, and
4. **present** the results responsibly in a public catalogue.

The project was inspired by an [AI-agent "rediscovery" of a Maya site](https://pietromiotti.com/latest/maya-site/) from LiDAR, and by its main lesson: that site turned out to be already published. Checking what is already known is a first-class step here.

> **Scope and ethics.** The project only re-uses existing public data. It involves no fieldwork, metal detecting or digging. Findings are called *candidates* or *features*, never "discoveries", until they are checked against historical sources. Precise locations of sensitive features (cemeteries, graves, conflict sites) are **never** published. See [Disclosure](#disclosure-and-sensitive-data).

## Status

Early-stage research software (v0).

| Area | State |
|---|---|
| Research and planning (`docs/`) | Done: literature, data sources, critique, ML plan, presentation plan |
| LiDAR acquisition (GUGiK 2010-2019 and 2023/2025 epochs, local LAZ) | Working |
| Processing (0.5 m DTM, ground density, hillshade, slope, SVF, LRM, COG output) | Working |
| "Get data for this view": download with progress and caching | Working |
| Review web app (map, layers, swipe compare, candidate editing) | Working, not yet tested by users |
| Rule-based and ML candidate detection | Planned ([docs/09](docs/09-ml-detection-plan.md)) |
| Public catalogue and story pages | Planned ([docs/10](docs/10-presentation-plan.md)) |

## Quick start

**Requirements:** [uv](https://docs.astral.sh/uv/) (installs Python 3.12 for you), [Node.js](https://nodejs.org/) 20 or newer, and Git. Everything installs from prebuilt wheels and packages, so no GDAL or PDAL setup is needed. Tested on Windows 11.

You run two processes: the Python API and the web app.

**Terminal 1: API**

```bash
git clone https://github.com/aleknitka/lidar-discovery-poland.git
cd lidar-discovery-poland
uv sync                              # creates .venv with Python 3.12
uv run ldp locations import-seed     # loads the seed villages into data/catalog.sqlite
uv run ldp serve                     # http://127.0.0.1:8000  (API docs at /docs)
```

**Terminal 2: web app**

```bash
cd lidar-discovery-poland/frontend
npm install
npm run dev                          # http://127.0.0.1:5173
```

Then open **http://127.0.0.1:5173/explore**:

1. Pan and zoom to an area of interest (zoom 13 or closer).
2. Click **Get data for this view**. You get an estimate of the map sheets needed, MB to download and MB already cached. Pick the epoch (2012 sheets are about 100 MB each; 2023 sheets are denser and larger) and confirm.
3. Watch the progress bar. When the job finishes, the area appears under **Fetched areas** with its sky-view-factor layer on. Use the layer switcher, the opacity slider and the swipe compare to inspect it.
4. Mark candidate features on the map and record their type, confidence, evidence and disclosure level.

Use `127.0.0.1` rather than `localhost` on Windows: resolving `localhost` through IPv6 adds about 2 s per request. To try the UI without the API, run `npm run dev:mock`, which uses made-up fixture data.

Downloaded and processed data lives in `data/` (git-ignored). Map sheets are downloaded once and reused; processed views are cached by area, epoch and parameters.

## Command line

All steps are also available through the `ldp` CLI:

```bash
uv run ldp --help
uv run ldp sources                                       # registered LiDAR sources
uv run ldp coverage carynskie --aoi point                # sheets per source/year, density; no download
uv run ldp fetch-bbox 22.612 49.1675 22.620 49.1705 --source gugik-kron86 --year 2012 --estimate-only
uv run ldp fetch-bbox 22.612 49.1675 22.620 49.1705 --source gugik-kron86 --year 2012
uv run ldp locations fetch-prg carynskie                 # official cadastral-precinct boundary
uv run ldp ingest carynskie --source gugik-kron86 --year 2012 --aoi point --aoi-buffer-m 150
uv run ldp process carynskie --source gugik-kron86 --year 2012 --aoi point --aoi-buffer-m 800
```

Fetch limits are set with `LDP_MAX_FETCH_AREA_KM2` (default 6) and `LDP_MAX_FETCH_BYTES` (default 4 GB). Other settings come from `LDP_*` environment variables or `.env`: `LDP_DATA_DIR` (default `./data`) and `LDP_PUBLIC_MODE` (hides restricted items, generalises the others and makes the API read-only).

## How it works

```
GUGiK WFS sheet index ─► LAZ sheets (data/raw, cached, resumable)
        │
        ▼
ground points (class 2) ─► 0.5 m DTM, EPSG:2180 (+ ground-density mask)
        │
        ▼
hillshade · slope · sky-view factor · local relief model ─► Cloud-Optimised GeoTIFFs + provenance
        │
        ▼
SQLite catalogue ─► FastAPI (XYZ tiles, locations, candidates, jobs) ─► React + MapLibre app
```

```
src/lidar_discovery/
  sources/      LiDAR source plug-ins (GUGiK KRON86 + EVRF2007, local LAZ, Slovak ZBGIS stub), downloader
  locations/    seed villages, Wikidata lookup, PRG cadastral precincts, AOI helpers
  processing/   points -> DTM -> visualisations -> COG, with provenance
  catalog/      SQLModel tables (Location, Product, Candidate, Job, ...), disclosure rules
  areas.py      viewport estimate;  jobs.py: background fetch/process jobs
  api/          FastAPI app and tile rendering
  cli.py        the `ldp` command
frontend/       React + TypeScript + Vite + MapLibre GL (/explore review tool, /catalog placeholder)
seeds/          hand-curated seed locations with provenance
tests/          pytest suite (network tests are opt-in: -m network)
docs/           research notes, synthesis, critique, decisions, architecture and plans
```

### Data

| Source | Use | Notes |
|---|---|---|
| [GUGiK](https://www.geoportal.gov.pl/) national ALS point clouds (LAZ) | Primary | Free for any use. 2012 epoch (~4 pts/m², autumn) and 2023 epoch (much denser, spring) in the Bieszczady. EPSG:2180. |
| Wikidata, PRG cadastral precincts | Village locations and boundaries | Former villages survive as cadastral precincts |
| NASA GEDI / ICESat-2, Copernicus DEM | Not used | Too coarse for house-scale earthworks ([docs/research/01](docs/research/01-lidar-data-sources.md)) |

Planned evidence layers: the 1852 Franciscan cadastre, interwar WIG maps and the 1944 aerial orthophoto. They are used to check what is already known, not as model inputs.

The two GUGiK epochs use different vertical datums (KRON86 and EVRF2007) and are not co-registered yet, so don't difference them.

## Disclosure and sensitive data

Every location and candidate carries a disclosure level:

- **public**: shown as is.
- **generalised**: shown snapped to a 1 km grid cell in public mode.
- **restricted**: never served in public mode. This is the default for cemeteries, graves, conflict-era features and all machine-generated candidates.

The public site must run with `LDP_PUBLIC_MODE=true`, so filtering happens on the server, not in the browser. Causes of depopulation are recorded per village with a source, never assumed. Names are shown in Polish and Ukrainian. The background is in [docs/05 §8](docs/05-synthesis.md) and [docs/07](docs/07-decisions.md).

## Documentation

| Doc | Contents |
|---|---|
| [research/00-04](docs/research/) | Source notes: the Maya-site inspiration, data sources, Polish and Carpathian prior art, detection methods, historical sources, law and ethics |
| [05-synthesis](docs/05-synthesis.md) | Comprehensive synthesis of the research |
| [06-critique](docs/06-critique.md) | Independent critique, with a staged plan and stop-or-continue criteria |
| [07-decisions](docs/07-decisions.md) | Project decisions (desk-only scope) |
| [08-architecture-contract](docs/08-architecture-contract.md) | Data model, CLI and REST API spec |
| [09-ml-detection-plan](docs/09-ml-detection-plan.md) | Plan for rule-based and ML detection and its evaluation |
| [10-presentation-plan](docs/10-presentation-plan.md) | How to present scans and findings honestly |

## Development

```bash
uv run ruff check . && uv run ruff format --check .
uv run pytest                                   # add -m network for live-service tests
cd frontend && npm run lint && npx tsc --noEmit && npm test && npm run build
```

### Adding a LiDAR source

1. Create `src/lidar_discovery/sources/mysource.py` with a class that has `id`, `name`, `description`, `crs_h`, `list_tiles(aoi_2180, years=None) -> list[TileRef]` and `download(tile, dest_dir) -> Path`, and decorate it with `@register_source("my-source-id")`. For a GUGiK-style WFS index, subclass `GugikWfsSource` in `sources/gugik.py` and set `wfs_url`.
2. Import the module in `sources/__init__.py` so it registers.
3. Return `TileRef`s with EPSG:2180 bounding boxes. LAS/LAZ data must be in, or reprojected to, EPSG:2180.
4. Add a parser test with a saved fixture (see `tests/test_wfs.py`).

### Known limitations

- LAZ sheets aren't spatially indexed, so the smallest download is a whole map sheet (about 1.2 × 1.2 km). Processing is clipped to the requested view.
- The 2023 epoch has many points in class 12 (unclassified overlap). Re-classifying them could add ground points but isn't implemented yet.
- The DTM interpolation uses a SciPy internal for speed, with a tested fallback. Pin SciPy when upgrading.
- Wikidata points for some seed villages are low precision; prefer `fetch-prg` boundaries.

## Data attribution

LiDAR, orthophoto and boundary data: © [GUGiK](https://www.geoportal.gov.pl/) (Główny Urząd Geodezji i Kartografii), Geoportal.gov.pl. Basemap: © OpenStreetMap contributors. Village identifiers: Wikidata (CC0).

## Licence

No licence has been chosen yet. Until one is added, all rights are reserved.
