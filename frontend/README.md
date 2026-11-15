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

## Get data for this view

`components/AreaFetch.tsx` (button, estimate card, progress panel) is mounted in the Explore map.
The button is disabled below zoom 13. Estimate: `GET /api/areas/estimate`; confirm: `POST
/api/areas/fetch`; progress: `useJob` polls `GET /api/jobs/{id}` every second while the job is
active; `useActiveJobs` re-attaches after a reload. Sheet footprints and the viewport rectangle are
drawn through `MapView`'s `area` prop (colour = state). When a job finishes the `locations` and
`layers` queries are invalidated and the new area is selected (its SVF layer turns on). Fetched
areas (`properties.kind === 'area'`) appear under "Fetched areas". Formatting helpers: `src/lib/format.ts`.
Mock mode simulates estimate + a ~10 s job (`src/api/mock.ts`).

## Checks

    npm run build && npm run lint && npx tsc --noEmit && npm test

## Layout

- `src/api/` typed client, TanStack hooks, mock
- `src/components/` `MapView`, `LayerControl`, `SwipeCompare`, `CandidatePanel`, badges, lists
- `src/routes/` Explore, Catalog
- `src/presentation/` stub for 3D / profiles / story modes (see its README)

UI copy uses "candidate" / "feature", never "discovery".
