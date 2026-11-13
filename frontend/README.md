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

## Checks

    npm run build && npm run lint && npx tsc --noEmit && npm test

## Layout

- `src/api/` typed client, TanStack hooks, mock
- `src/components/` `MapView`, `LayerControl`, `SwipeCompare`, `CandidatePanel`, badges, lists
- `src/routes/` Explore, Catalog
- `src/presentation/` stub for 3D / profiles / story modes (see its README)

UI copy uses "candidate" / "feature", never "discovery".
