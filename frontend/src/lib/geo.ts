import type { Geometry, Position } from 'geojson';
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

export function locationCenter(loc: Location): [number, number] | null {
  const b = locationAoi(loc);
  return b ? [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2] : null;
}

export function locationName(loc: Location): string {
  const n = loc.properties.names;
  return n.pl ?? n.uk ?? n.other ?? loc.properties.id;
}
