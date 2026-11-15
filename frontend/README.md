# LiDAR review frontend

React 18 + TypeScript (strict) + Vite, MapLibre GL JS, TanStack Query, react-router.
Routes: `/explore` (internal review workspace) and `/catalog` (public-catalogue placeholder, WIP).
Contract: `../docs/08-architecture-contract.md`; types live in `src/api/types.ts`.

## Run

    npm install
    npm run dev:mock     # mock mode: in-browser fixtures, no backend needed (also: VITE_MOCK=1 npm run dev)
    npm run dev          # real backend: start `ldp serve` on 127.0.0.1:8000; Vite proxies /api

Mock mode shims `fetch` for `/api/*` and renders synthetic tiles through a `mock://` MapLibre
protocol (`src/api/mock.ts`). Fixtures are illustrative only. Created/edited candidates live in memory.

## Explore layout

The map fills the screen. Controls are in a right-hand panel with five tabs: **Layers** (switch
layers on, opacity, swipe compare, an (i) button per layer), **Info** (what each layer is, how it is
computed, how to read it, pitfalls, glossary, and the layer's real metadata), **Candidates**,
**Places** (search, collapsed groups for seed villages and fetched areas; nothing is drawn on the
map until you pick one) and **Data** (get LiDAR for the view, coverage). The panel collapses
(open/tab state is kept in `localStorage`, tabs support arrow keys) and is a bottom sheet below
720 px. The first view is the whole Bieszczady with no markers.

Layer names, hints and all explanatory text live in `src/content/layers.ts` (typed, one entry per
kind). To add a layer kind: add it to `ALL_KINDS` in `processing/pipeline.py`, add an entry to
`LAYER_INFO` (the completeness test in `layers.test.ts` reads `pipeline.py` and fails otherwise)
and to `LAYER_CHOICES` if it can be picked when fetching.

## Get data for this view

`components/AreaFetch.tsx` (`useAreaFetch` state hook, map button, Data-tab estimate card and
progress card). The button is disabled below zoom 13. Estimate: `GET /api/areas/estimate?...&layers=`;
confirm: `POST /api/areas/fetch` with `layers`; progress: `useJob` polls `GET /api/jobs/{id}` every
second; `useActiveJobs` re-attaches after a reload. The card shows a legend (your view, cached
sheet, sheet to download), a stacked cached/to-download bar, the view area against the limit, a
per-sheet table (size, share of the sheet your view covers, status chip with icon and text) and
the layer checkboxes (DTM always on; choice affects processing time and disk, not the download).
On the map `MapView` draws the view outline and sheet footprints (fill + outline, labels at the
centre as HTML markers) from `src/lib/areaStyle.ts`; statuses update live while the job runs. The
overlay layers are added on the map's `style.load` event, not `load` (which waits for basemap
tiles). When a job finishes the new area is selected with its DTM layer on. Mock mode simulates
cache states, layer selection and a ~10 s job (`src/api/mock.ts`).

## Checks

    npm run build && npm run lint && npx tsc --noEmit && npm test

## Layout

- `src/api/` typed client, TanStack hooks, mock
- `src/components/` `MapView`, `LayerControl`, `SwipeCompare`, `CandidatePanel`, badges, lists
- `src/routes/` Explore, Catalog
- `src/presentation/` stub for 3D / profiles / story modes (see its README)

UI copy uses "candidate" / "feature", never "discovery".
