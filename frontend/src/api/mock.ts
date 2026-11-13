// Mock mode (VITE_MOCK=1): a fetch shim for /api/* with illustrative fixtures, plus a MapLibre
// "mock://" tile protocol that renders synthetic greyscale tiles. Fixture names/coordinates are
// illustrative only and are not real survey data.
import * as maplibregl from 'maplibre-gl';
import type { Polygon } from 'geojson';
import type {
  Candidate,
  CandidateCollection,
  Coverage,
  Layer,
  Location,
  LocationCollection,
} from './types';

const box = (lon: number, lat: number, dLon: number, dLat: number) =>
  [lon - dLon, lat - dLat, lon + dLon, lat + dLat] as [number, number, number, number];

const locations: Location[] = [
  {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [22.5965, 49.148] },
    properties: {
      id: 'mock-lopienka',
      names: { pl: 'Łopienka (mock)', uk: 'Лопенка' },
      depopulation: { year: 1946, cause: 'resettlement (mock)', source_url: null },
      has_products: true,
      disclosure: 'generalised',
      polygon: {
        type: 'Polygon',
        coordinates: [
          [
            [22.588, 49.142],
            [22.605, 49.142],
            [22.605, 49.154],
            [22.588, 49.154],
            [22.588, 49.142],
          ],
        ],
      },
      provenance: [{ provider: 'seed', ref: 'mock', fetched_at: '2026-11-13T00:00:00Z' }],
    },
  },
  {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [22.642, 49.162] },
    properties: {
      id: 'mock-terka',
      names: { pl: 'Terka (mock)', uk: 'Терка' },
      depopulation: { year: null, cause: null, source_url: null },
      has_products: true,
      disclosure: 'generalised',
      provenance: [{ provider: 'seed', ref: 'mock', fetched_at: '2026-11-13T00:00:00Z' }],
    },
  },
  {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [22.552, 49.126] },
    properties: {
      id: 'mock-krywe',
      names: { pl: 'Krywe (mock)' },
      depopulation: null,
      has_products: false,
      disclosure: 'restricted',
      provenance: [],
    },
  },
];

const KINDS = ['hillshade', 'svf', 'lrm'] as const;
const EPOCHS: [number, string][] = [
  [2012, 'gugik-kron86'],
  [2023, 'gugik-evrf2007'],
];

function layersFor(loc: Location): Layer[] {
  if (!loc.properties.has_products) return [];
  const [lon, lat] = (loc.geometry as unknown as { coordinates: [number, number] }).coordinates;
  const bounds = box(lon, lat, 0.012, 0.008);
  return EPOCHS.flatMap(([epoch, source_id]) =>
    KINDS.map((kind) => {
      const id = `${loc.properties.id}-${source_id}-${epoch}-${kind}`;
      return {
        id,
        location_id: loc.properties.id,
        kind,
        epoch,
        source_id,
        resolution_m: epoch === 2023 ? 0.5 : 1,
        bounds,
        tile_url: `mock://${id}/{z}/{x}/{y}`,
        provenance: { input_tiles: 4, code_version: 'mock', created_at: '2026-11-13T00:00:00Z' },
      };
    }),
  );
}

const coverageFor = (loc: Location): Coverage[] => {
  const [lon, lat] = (loc.geometry as unknown as { coordinates: [number, number] }).coordinates;
  const bbox = box(lon, lat, 0.012, 0.008);
  if (loc.properties.id === 'mock-krywe')
    return [{ source_id: 'gugik-kron86', year: 2012, tiles: 1, nominal_density: '4 p/m2', bbox }];
  return [
    { source_id: 'gugik-kron86', year: 2012, tiles: 4, nominal_density: '4 p/m2', bbox },
    { source_id: 'gugik-evrf2007', year: 2023, tiles: 4, nominal_density: '12 p/m2', bbox },
  ];
};

let seq = 3;
const poly = (lon: number, lat: number, r: number) =>
  ({
    type: 'Polygon',
    coordinates: [
      [
        [lon - r, lat - r],
        [lon + r, lat - r],
        [lon + r, lat + r],
        [lon - r, lat + r],
        [lon - r, lat - r],
      ],
    ],
  }) as Polygon;

const candidates: Candidate[] = [
  {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [22.5958, 49.1476] },
    properties: {
      id: 'c-1',
      location_id: 'mock-lopienka',
      morph_class: 'house_platform',
      reality: 'anthropogenic',
      confidence: 0.7,
      dating_evidence:
        'Platform outline visible in 2023 SVF; absent from 1850s cadastre check (pending).',
      documentation_status: [{ source: '1944 aerial photo', ref: 'tbd', found: false }],
      origin: 'manual',
      review_status: 'accepted',
      reviewer_notes: 'Clear rectangular platform.',
      disclosure: 'generalised',
      created_at: '2026-11-12T10:00:00Z',
      updated_at: '2026-11-12T10:00:00Z',
    },
  },
  {
    type: 'Feature',
    geometry: poly(22.5985, 49.1495, 0.0006),
    properties: {
      id: 'c-2',
      location_id: 'mock-lopienka',
      morph_class: 'terrace',
      reality: 'unassessed',
      confidence: 0.4,
      origin: 'rule',
      review_status: 'proposed',
      reviewer_notes: '',
      disclosure: 'generalised',
      created_at: '2026-11-12T11:00:00Z',
      updated_at: '2026-11-12T11:00:00Z',
    },
  },
  {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [22.6405, 49.1615] },
    properties: {
      id: 'c-3',
      location_id: 'mock-terka',
      morph_class: 'cemetery',
      reality: 'anthropogenic',
      confidence: 0.55,
      origin: 'manual',
      review_status: 'needs_second_opinion',
      reviewer_notes: 'Possible burial ground; keep restricted.',
      disclosure: 'restricted',
      created_at: '2026-11-12T12:00:00Z',
      updated_at: '2026-11-12T12:00:00Z',
    },
  },
];

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
const err = (status: number, detail: string) => json({ detail }, status);

function handle(method: string, url: URL, body: unknown): Response {
  const p = url.pathname.replace(/^\/api/, '');
  let m: RegExpMatchArray | null;
  if (p === '/health') return json({ status: 'ok', mock: true });
  if (p === '/sources')
    return json([
      { id: 'gugik-kron86', name: 'GUGiK KRON86', description: 'Mock source' },
      { id: 'gugik-evrf2007', name: 'GUGiK EVRF2007', description: 'Mock source' },
    ]);
  if (p === '/locations') {
    const fc: LocationCollection = { type: 'FeatureCollection', features: locations };
    return json(fc);
  }
  if ((m = p.match(/^\/locations\/([^/]+)(\/coverage|\/layers)?$/))) {
    const loc = locations.find((l) => l.properties.id === decodeURIComponent(m![1]));
    if (!loc) return err(404, 'Location not found');
    if (m[2] === '/coverage') return json(coverageFor(loc));
    if (m[2] === '/layers') return json(layersFor(loc));
    return json(loc);
  }
  if (p === '/candidates' && method === 'GET') {
    const loc = url.searchParams.get('location_id');
    const st = url.searchParams.get('review_status');
    const fc: CandidateCollection = {
      type: 'FeatureCollection',
      features: candidates.filter(
        (c) =>
          (!loc || c.properties.location_id === loc) && (!st || c.properties.review_status === st),
      ),
    };
    return json(fc);
  }
  if (p === '/candidates' && method === 'POST') {
    const b = body as Partial<Candidate> | undefined;
    if (!b?.geometry || !b.properties)
      return err(422, 'Feature with geometry and properties required');
    const now = new Date().toISOString();
    const c = {
      type: 'Feature',
      geometry: b.geometry,
      properties: {
        ...({
          morph_class: 'other',
          reality: 'unassessed',
          confidence: 0.5,
          origin: 'manual',
          review_status: 'proposed',
          disclosure: 'generalised',
        } as Partial<Candidate['properties']>),
        ...b.properties,
        id: `c-${++seq}`,
        created_at: now,
        updated_at: now,
      },
    } as Candidate;
    candidates.push(c);
    return json(c, 201);
  }
  if ((m = p.match(/^\/candidates\/([^/]+)$/)) && method === 'PATCH') {
    const c = candidates.find((x) => x.properties.id === decodeURIComponent(m![1]));
    if (!c) return err(404, 'Candidate not found');
    const b = body as { geometry?: Candidate['geometry']; properties?: object };
    if (b.geometry) c.geometry = b.geometry;
    Object.assign(c.properties, b.properties, { updated_at: new Date().toISOString() });
    return json(c);
  }
  return err(404, `No mock route for ${method} ${p}`);
}

// --- Synthetic tiles -------------------------------------------------------------------------

function lonLatOfPixel(z: number, x: number, y: number, px: number, py: number) {
  const n = 2 ** z;
  const fx = (x + px / 256) / n;
  const fy = (y + py / 256) / n;
  const lon = fx * 360 - 180;
  const lat = (Math.atan(Math.sinh(Math.PI * (1 - 2 * fy))) * 180) / Math.PI;
  return [lon, lat] as const;
}

async function renderTile(id: string, z: number, x: number, y: number): Promise<ArrayBuffer> {
  const layer = locations.flatMap(layersFor).find((l) => l.id === id);
  const canvas = new OffscreenCanvas(256, 256);
  const ctx = canvas.getContext('2d')!;
  if (layer) {
    const [w, s, e, n] = layer.bounds;
    const phase = layer.epoch === 2023 ? 1.7 : 0;
    const k = layer.kind === 'svf' ? 1.3 : layer.kind === 'lrm' ? 0.8 : 1;
    const cell = 4;
    for (let py = 0; py < 256; py += cell) {
      for (let px = 0; px < 256; px += cell) {
        const [lon, lat] = lonLatOfPixel(z, x, y, px, py);
        if (lon < w || lon > e || lat < s || lat > n) continue;
        const v =
          0.5 +
          0.25 * Math.sin(lon * 4000 * k + phase) * Math.cos(lat * 5200 * k) +
          0.15 * Math.sin((lon + lat) * 9000 + phase * 2) +
          (layer.epoch === 2023 ? 0.08 : 0);
        const g = Math.max(0, Math.min(255, Math.round(v * 255)));
        ctx.fillStyle = `rgba(${g},${g},${g},0.9)`;
        ctx.fillRect(px, py, cell, cell);
      }
    }
  }
  const blob = await canvas.convertToBlob({ type: 'image/png' });
  return blob.arrayBuffer();
}

export function installMock(): void {
  const realFetch = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const raw = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
    const url = new URL(raw, window.location.origin);
    if (!url.pathname.startsWith('/api/')) return realFetch(input, init);
    await new Promise((r) => setTimeout(r, 120));
    const method = (
      init?.method ?? (input instanceof Request ? input.method : 'GET')
    ).toUpperCase();
    const body = typeof init?.body === 'string' ? JSON.parse(init.body) : undefined;
    return handle(method, url, body);
  };
  maplibregl.addProtocol('mock', async (params: { url: string }) => {
    const m = params.url.match(/^mock:\/\/([^/]+)\/(\d+)\/(\d+)\/(\d+)/);
    if (!m) throw new Error('bad mock tile url');
    return { data: await renderTile(m[1], +m[2], +m[3], +m[4]) };
  });
}
