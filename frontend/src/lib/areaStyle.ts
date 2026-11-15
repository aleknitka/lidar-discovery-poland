// Colours, labels and GeoJSON for the "Get data for this view" overlay. One place, used by the map
// layers, the legend swatches and the sheet table so they always agree. Colours are from the
// Okabe-Ito colour-blind-safe palette; every state also has a non-colour cue (line style, icon and
// text), so colour is never the only signal.
import type { Feature, FeatureCollection, Polygon } from 'geojson';
import type { BBox, EstimateTile, JobTile } from '../api/areaTypes';
import { formatBytes, percentOf } from './format';

export type SheetState = 'cached' | 'todo' | 'pending' | 'downloading' | 'done' | 'failed';
export type OverlayState = 'viewport' | SheetState;

export const AREA_COLORS = {
  cached: '#0072B2', // blue
  todo: '#E69F00', // orange
  downloading: '#D55E00', // vermillion
  failed: '#CC79A7', // reddish purple
  viewport: '#ffffff',
  viewportCasing: '#111111',
} as const;

/** Colour a state is drawn with. */
export function stateColour(state: OverlayState): string {
  switch (state) {
    case 'cached':
    case 'done':
      return AREA_COLORS.cached;
    case 'downloading':
      return AREA_COLORS.downloading;
    case 'failed':
      return AREA_COLORS.failed;
    case 'viewport':
      return AREA_COLORS.viewport;
    default:
      return AREA_COLORS.todo;
  }
}

export interface StatusView {
  /** Short text, always shown together with the colour. */
  text: string;
  /** Non-colour cue. */
  icon: string;
  /** CSS class suffix. */
  tone: 'cached' | 'todo' | 'downloading' | 'failed';
}

/** Chip contents for a sheet state (estimate: cached/todo; running job: all of them). */
export function statusView(state: SheetState): StatusView {
  switch (state) {
    case 'cached':
      return { text: 'cached', icon: '✓', tone: 'cached' };
    case 'done':
      return { text: 'downloaded', icon: '✓', tone: 'cached' };
    case 'downloading':
      return { text: 'downloading', icon: '⇣', tone: 'downloading' };
    case 'failed':
      return { text: 'failed', icon: '✕', tone: 'failed' };
    case 'pending':
      return { text: 'waiting', icon: '↓', tone: 'todo' };
    default:
      return { text: 'to download', icon: '↓', tone: 'todo' };
  }
}

export const rectPolygon = (b: BBox): Polygon => ({
  type: 'Polygon',
  coordinates: [
    [
      [b[0], b[1]],
      [b[2], b[1]],
      [b[2], b[3]],
      [b[0], b[3]],
      [b[0], b[1]],
    ],
  ],
});

const feature = (geometry: Polygon, props: Record<string, string>): Feature => ({
  type: 'Feature',
  geometry,
  properties: props,
});

/** Overlay for the estimate card: the view and every sheet, cached or to download. */
export function estimateOverlay(bbox: BBox, tiles: EstimateTile[]): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: [
      feature(rectPolygon(bbox), { state: 'viewport', label: 'Your view' }),
      ...tiles.map((t) => {
        const state: SheetState = t.cached ? 'cached' : 'todo';
        const v = statusView(state);
        return feature(t.footprint, {
          state,
          label: `${t.godlo} ${v.icon} ${v.text}`,
          title: `${t.godlo}: ${v.text}, ${formatBytes(t.size_bytes)}`,
        });
      }),
    ],
  };
}

/** Overlay for a running job: statuses update live; downloading sheets show their percentage. */
export function jobOverlay(bbox: BBox, tiles: JobTile[]): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: [
      feature(rectPolygon(bbox), { state: 'viewport', label: 'Your view' }),
      ...tiles
        .filter((t) => t.footprint)
        .map((t) => {
          const v = statusView(t.status);
          const pct =
            t.status === 'downloading' ? ` ${Math.round(percentOf(t.bytes, t.size_bytes))} %` : '';
          return feature(t.footprint as Polygon, {
            state: t.status,
            label: `${t.godlo} ${v.icon} ${v.text}${pct}`,
            title: `${t.godlo}: ${v.text}`,
          });
        }),
    ],
  };
}
