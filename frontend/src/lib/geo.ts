import type { Geometry, Polygon, Position } from 'geojson';
import type { Location } from '../api/types';

export type Bounds = [number, number, number, number]; // w, s, e, n

function visit(coords: unknown, fn: (p: Position) => void): void {
  if (!Array.isArray(coords)) return;
  if (typeof coords[0] === 'number') fn(coords as Position);
  else for (const c of coords) visit(c, fn);
}

export function geometryBounds(g: Geometry): Bounds | null {
  let w = Infinity,
    s = Infinity,
    e = -Infinity,
    n = -Infinity;
  if (g.type === 'GeometryCollection') {
    for (const sub of g.geometries) {
      const b = geometryBounds(sub);
      if (b) {
        w = Math.min(w, b[0]);
        s = Math.min(s, b[1]);
        e = Math.max(e, b[2]);
        n = Math.max(n, b[3]);
      }
    }
  } else {
    visit(g.coordinates, ([x, y]) => {
      w = Math.min(w, x);
      s = Math.min(s, y);
      e = Math.max(e, x);
      n = Math.max(n, y);
    });
  }
  return Number.isFinite(w) ? [w, s, e, n] : null;
}

/** Bounding box of a point buffered by `radiusM` metres. */
export function pointBuffer(lon: number, lat: number, radiusM = 1000): Bounds {
  const dLat = radiusM / 111_320;
  const dLon = radiusM / (111_320 * Math.cos((lat * Math.PI) / 180));
  return [lon - dLon, lat - dLat, lon + dLon, lat + dLat];
}

/** AOI = polygon if present, else a 1 km point buffer (contract). */
export function locationAoi(loc: Location): Bounds | null {
  const poly = loc.properties.polygon;
  if (poly) return geometryBounds(poly);
  const g = loc.geometry;
  if (!g) return null;
  if (g.type === 'Point') return pointBuffer(g.coordinates[0], g.coordinates[1]);
  return geometryBounds(g);
}

type Pt = [number, number];

function ringArea(r: Pt[]): number {
  let a = 0;
  for (let i = 0; i < r.length; i++) {
    const [x1, y1] = r[i];
    const [x2, y2] = r[(i + 1) % r.length];
    a += x1 * y2 - x2 * y1;
  }
  return Math.abs(a) / 2;
}

/** Clip a polygon ring to an axis-aligned rectangle (Sutherland-Hodgman). */
function clipRing(ring: Pt[], [w, s, e, n]: Bounds): Pt[] {
  const edges: [(p: Pt) => boolean, (a: Pt, b: Pt) => Pt][] = [
    [(p) => p[0] >= w, (a, b) => [w, a[1] + ((b[1] - a[1]) * (w - a[0])) / (b[0] - a[0])]],
    [(p) => p[0] <= e, (a, b) => [e, a[1] + ((b[1] - a[1]) * (e - a[0])) / (b[0] - a[0])]],
    [(p) => p[1] >= s, (a, b) => [a[0] + ((b[0] - a[0]) * (s - a[1])) / (b[1] - a[1]), s]],
    [(p) => p[1] <= n, (a, b) => [a[0] + ((b[0] - a[0]) * (n - a[1])) / (b[1] - a[1]), n]],
  ];
  let out = ring;
  for (const [inside, cross] of edges) {
    const input = out;
    out = [];
    for (let i = 0; i < input.length; i++) {
      const cur = input[i];
      const prev = input[(i + input.length - 1) % input.length];
      if (inside(cur)) {
        if (!inside(prev)) out.push(cross(prev, cur));
        out.push(cur);
      } else if (inside(prev)) out.push(cross(prev, cur));
    }
    if (out.length === 0) break;
  }
  return out;
}

/**
 * Share (0..1) of a polygon's area that lies inside the bounding box. Areas are computed in
 * degrees; the ratio is accurate for small areas (a map sheet is about 1 km across).
 */
export function polygonShareInside(poly: Polygon, box: Bounds): number {
  const ring = poly.coordinates[0] as Pt[] | undefined;
  if (!ring || ring.length < 4) return 0;
  const open = ring.slice(0, -1);
  const total = ringArea(open);
  if (total <= 0) return 0;
  const clipped = clipRing(open, box);
  return clipped.length < 3 ? 0 : Math.min(1, ringArea(clipped) / total);
}

/** Centre of a geometry's bounding box, for labels. */
export function polygonCentre(g: Geometry): [number, number] | null {
  const b = geometryBounds(g);
  return b ? [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2] : null;
}

export function locationCenter(loc: Location): [number, number] | null {
  const b = locationAoi(loc);
  return b ? [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2] : null;
}

export function locationName(loc: Location): string {
  const n = loc.properties.names;
  return n.pl ?? n.uk ?? n.other ?? loc.properties.id;
}
