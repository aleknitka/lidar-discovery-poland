import { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import type { Map as MlMap, StyleSpecification } from 'maplibre-gl';
// MapLibre 6 looks for its worker next to its own script. Vite bundles that script elsewhere, so
// the worker 404s ("Worker failed to load") and every GeoJSON overlay (sheet footprints, candidate
// markers) silently disappears. Give it the real file instead; Vite emits it in dev and in build.
import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import type { FeatureCollection } from 'geojson';
import 'maplibre-gl/dist/maplibre-gl.css';

maplibregl.setWorkerUrl(maplibreWorkerUrl);
import type { CandidateCollection } from '../api/types';
import { polygonCentre, type Bounds } from '../lib/geo';
import { AREA_COLORS } from '../lib/areaStyle';

export interface RasterSpec {
  id: string;
  tileUrl: string;
  opacity: number;
  bounds?: Bounds;
}

export interface MapViewProps {
  /** Fit the map to these bounds whenever they change. */
  bounds?: Bounds | null;
  rasters?: RasterSpec[];
  candidates?: CandidateCollection | null;
  selectedId?: string | null;
  /** Drawing-in-progress geometry (points / line / polygon). */
  draft?: FeatureCollection | null;
  /** When false the map ignores input (used for the clipped overlay in swipe mode). */
  interactive?: boolean;
  /** Show the attribution control (only one map should). */
  attribution?: boolean;
  crosshair?: boolean;
  /** Viewport rectangle + sheet footprints; each feature has properties.state (see AREA_COLORS). */
  area?: FeatureCollection | null;
  /** Fit the map to these bounds (with extra padding) once per `key`, e.g. to frame the view. */
  focus?: { bounds: Bounds; key: string } | null;
  /** Fired on load and after every pan/zoom. */
  onViewChange?: (view: { bounds: Bounds; zoom: number }) => void;
  onClick?: (lngLat: [number, number], candidateId: string | null) => void;
  onMapReady?: (map: MlMap) => void;
  className?: string;
}

export const ATTRIBUTION = ['© OpenStreetMap contributors', 'LiDAR: GUGiK (Geoportal.gov.pl)'];

const STYLE: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      maxzoom: 19,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
};

export const STATUS_COLORS: Record<string, string> = {
  proposed: '#e0a100',
  accepted: '#2e9d4f',
  rejected: '#b23b3b',
  needs_second_opinion: '#7a4fd1',
};

const statusColor = [
  'match',
  ['get', 'review_status'],
  'proposed',
  STATUS_COLORS.proposed,
  'accepted',
  STATUS_COLORS.accepted,
  'rejected',
  STATUS_COLORS.rejected,
  'needs_second_opinion',
  STATUS_COLORS.needs_second_opinion,
  '#888888',
] as unknown as string;

const stateIs = (...states: string[]) =>
  ['in', ['get', 'state'], ['literal', states]] as unknown as maplibregl.FilterSpecification;
const areaColor = [
  'match',
  ['get', 'state'],
  ['cached', 'done'],
  AREA_COLORS.cached,
  'downloading',
  AREA_COLORS.downloading,
  'failed',
  AREA_COLORS.failed,
  AREA_COLORS.todo,
] as unknown as string;

/** Whole Bieszczady region: the first view when no place is selected. */
export const BIESZCZADY_BOUNDS: Bounds = [21.9, 48.9, 23.1, 49.45];

const CAND_LAYERS = ['cand-fill', 'cand-line', 'cand-point'];
const EMPTY: FeatureCollection = { type: 'FeatureCollection', features: [] };
const rasterLayerId = (id: string) => `r-${id}`;

function addOverlays(map: MlMap) {
  map.addSource('cands', { type: 'geojson', data: EMPTY });
  map.addSource('draft', { type: 'geojson', data: EMPTY });
  map.addLayer({
    id: 'cand-fill',
    type: 'fill',
    source: 'cands',
    filter: ['==', ['geometry-type'], 'Polygon'],
    paint: { 'fill-color': statusColor, 'fill-opacity': 0.25 },
  });
  map.addLayer({
    id: 'cand-line',
    type: 'line',
    source: 'cands',
    filter: ['==', ['geometry-type'], 'Polygon'],
    paint: { 'line-color': statusColor, 'line-width': 2 },
  });
  map.addLayer({
    id: 'cand-point',
    type: 'circle',
    source: 'cands',
    filter: ['==', ['geometry-type'], 'Point'],
    paint: {
      'circle-radius': 7,
      'circle-color': statusColor,
      'circle-stroke-color': '#ffffff',
      'circle-stroke-width': 2,
    },
  });
  map.addLayer({
    id: 'cand-selected',
    type: 'circle',
    source: 'cands',
    filter: ['==', ['get', 'id'], ''],
    paint: {
      'circle-radius': 12,
      'circle-color': 'rgba(0,0,0,0)',
      'circle-stroke-color': '#00b4d8',
      'circle-stroke-width': 3,
    },
  });
  map.addLayer({
    id: 'cand-selected-line',
    type: 'line',
    source: 'cands',
    filter: ['==', ['get', 'id'], ''],
    paint: { 'line-color': '#00b4d8', 'line-width': 4 },
  });
  map.addLayer({
    id: 'draft-fill',
    type: 'fill',
    source: 'draft',
    filter: ['==', ['geometry-type'], 'Polygon'],
    paint: { 'fill-color': '#00b4d8', 'fill-opacity': 0.2 },
  });
  map.addLayer({
    id: 'draft-line',
    type: 'line',
    source: 'draft',
    filter: ['in', ['geometry-type'], ['literal', ['LineString', 'Polygon']]],
    paint: { 'line-color': '#00b4d8', 'line-width': 2, 'line-dasharray': [2, 1] },
  });
  // View outline and sheet footprints. Added once the style has loaded, on top of the LiDAR
  // rasters (those are inserted below 'cand-fill'). Cached = solid blue, to download = dashed
  // orange, so the two differ without colour as well.
  map.addSource('area', { type: 'geojson', data: EMPTY });
  map.addLayer({
    id: 'area-fill',
    type: 'fill',
    source: 'area',
    filter: ['!=', ['get', 'state'], 'viewport'],
    paint: {
      'fill-color': areaColor,
      'fill-opacity': ['match', ['get', 'state'], 'downloading', 0.42, 0.28],
    },
  });
  map.addLayer({
    id: 'area-line-cached',
    type: 'line',
    source: 'area',
    filter: stateIs('cached', 'done', 'failed'),
    paint: { 'line-color': areaColor, 'line-width': 3 },
  });
  map.addLayer({
    id: 'area-line-todo',
    type: 'line',
    source: 'area',
    filter: stateIs('todo', 'pending', 'downloading'),
    paint: { 'line-color': areaColor, 'line-width': 3, 'line-dasharray': [2, 1.5] },
  });
  map.addLayer({
    id: 'area-view-casing',
    type: 'line',
    source: 'area',
    filter: stateIs('viewport'),
    paint: { 'line-color': AREA_COLORS.viewportCasing, 'line-width': 6, 'line-opacity': 0.7 },
  });
  map.addLayer({
    id: 'area-view',
    type: 'line',
    source: 'area',
    filter: stateIs('viewport'),
    paint: { 'line-color': AREA_COLORS.viewport, 'line-width': 2.5 },
  });
  map.addLayer({
    id: 'draft-pts',
    type: 'circle',
    source: 'draft',
    filter: ['==', ['geometry-type'], 'Point'],
    paint: {
      'circle-radius': 5,
      'circle-color': '#00b4d8',
      'circle-stroke-color': '#ffffff',
      'circle-stroke-width': 2,
    },
  });
}

export default function MapView({
  bounds,
  rasters = [],
  candidates,
  selectedId,
  draft,
  interactive = true,
  attribution = true,
  crosshair,
  area,
  focus,
  onViewChange,
  onClick,
  onMapReady,
  className,
}: MapViewProps) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const [loaded, setLoaded] = useState(false);
  const onClickRef = useRef(onClick);
  onClickRef.current = onClick;
  const onReadyRef = useRef(onMapReady);
  onReadyRef.current = onMapReady;
  const onViewRef = useRef(onViewChange);
  onViewRef.current = onViewChange;
  const initialBounds = useRef(bounds);

  // Create the map once.
  useEffect(() => {
    if (!container.current) return;
    const map = new maplibregl.Map({
      container: container.current,
      style: STYLE,
      bounds: initialBounds.current ?? BIESZCZADY_BOUNDS,
      fitBoundsOptions: { padding: 20 },
      interactive,
      attributionControl: attribution ? { customAttribution: ATTRIBUTION.slice(1) } : false,
    });
    mapRef.current = map;
    // 'style.load' (not 'load'): 'load' waits for the first basemap tiles, so with a slow or
    // blocked tile server the overlays below would never be added.
    map.once('style.load', () => {
      addOverlays(map);
      setLoaded(true);
      onReadyRef.current?.(map);
      emitView();
    });
    const emitView = () => {
      const b = map.getBounds();
      onViewRef.current?.({
        bounds: [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()],
        zoom: map.getZoom(),
      });
    };
    map.on('moveend', emitView);
    map.on('click', (e: maplibregl.MapMouseEvent) => {
      const hit = map.queryRenderedFeatures(e.point, { layers: CAND_LAYERS })[0];
      const id = (hit?.properties?.id as string | undefined) ?? null;
      onClickRef.current?.([e.lngLat.lng, e.lngLat.lat], id);
    });
    return () => {
      map.remove();
      mapRef.current = null;
      setLoaded(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fit to bounds.
  const boundsKey = bounds ? bounds.join(',') : '';
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !bounds) return;
    map.fitBounds(bounds, { padding: 30, duration: 600, maxZoom: 17 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [boundsKey, loaded]);

  // Raster layers (kept above basemap, below candidate overlays).
  const rasterKey = rasters.map((r) => `${r.id}:${r.tileUrl}`).join('|');
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !loaded) return;
    const wanted = new Set(rasters.map((r) => rasterLayerId(r.id)));
    for (const l of map.getStyle().layers) {
      if (l.id.startsWith('r-') && !wanted.has(l.id)) {
        map.removeLayer(l.id);
        if (map.getSource(l.id)) map.removeSource(l.id);
      }
    }
    for (const r of rasters) {
      const id = rasterLayerId(r.id);
      if (!map.getSource(id)) {
        map.addSource(id, {
          type: 'raster',
          tiles: [r.tileUrl],
          tileSize: 256,
          bounds: r.bounds,
          attribution: 'LiDAR: GUGiK (Geoportal.gov.pl)',
        });
      }
      if (!map.getLayer(id)) {
        map.addLayer(
          { id, type: 'raster', source: id, paint: { 'raster-opacity': r.opacity } },
          'cand-fill',
        );
      }
    }
    // keep order as given
    for (const r of rasters) map.moveLayer(rasterLayerId(r.id), 'cand-fill');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rasterKey, loaded]);

  // Opacity updates without re-adding layers.
  const opacityKey = rasters.map((r) => `${r.id}:${r.opacity}`).join('|');
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !loaded) return;
    for (const r of rasters) {
      const id = rasterLayerId(r.id);
      if (map.getLayer(id)) map.setPaintProperty(id, 'raster-opacity', r.opacity);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opacityKey, rasterKey, loaded]);

  useEffect(() => {
    const src = mapRef.current?.getSource('cands') as maplibregl.GeoJSONSource | undefined;
    src?.setData((candidates as FeatureCollection | null | undefined) ?? EMPTY);
  }, [candidates, loaded]);

  useEffect(() => {
    const src = mapRef.current?.getSource('area') as maplibregl.GeoJSONSource | undefined;
    src?.setData(area ?? EMPTY);
  }, [area, loaded]);

  // Sheet labels: HTML markers at the centre of each footprint (no font server needed).
  const markers = useRef<Map<string, maplibregl.Marker>>(new Map());
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !loaded) return;
    const wanted = new Map<string, { at: [number, number]; text: string; title: string }>();
    for (const f of area?.features ?? []) {
      const p = f.properties ?? {};
      if (p.state === 'viewport' || !p.label || f.geometry.type !== 'Polygon') continue;
      const at = polygonCentre(f.geometry);
      if (at)
        wanted.set(`${at[0].toFixed(5)},${at[1].toFixed(5)}`, {
          at,
          text: String(p.label),
          title: String(p.title ?? p.label),
        });
    }
    for (const [k, m] of markers.current) {
      if (!wanted.has(k)) {
        m.remove();
        markers.current.delete(k);
      }
    }
    for (const [k, w] of wanted) {
      const existing = markers.current.get(k);
      if (existing) {
        existing.getElement().textContent = w.text;
        continue;
      }
      const el = document.createElement('div');
      el.className = 'sheet-label';
      el.textContent = w.text;
      el.title = w.title;
      markers.current.set(k, new maplibregl.Marker({ element: el }).setLngLat(w.at).addTo(map));
    }
  }, [area, loaded]);
  useEffect(() => {
    const live = markers.current;
    return () => {
      for (const m of live.values()) m.remove();
      live.clear();
    };
  }, []);

  // Frame the (frozen) view with some room around it so its outline is visible.
  const focusKey = focus?.key ?? '';
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !loaded || !focus) return;
    const narrow = window.matchMedia('(max-width: 720px)').matches;
    map.fitBounds(focus.bounds, {
      padding: narrow
        ? { top: 56, left: 24, right: 24, bottom: Math.round(window.innerHeight * 0.55) }
        : 70,
      duration: 400,
      maxZoom: 17,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusKey, loaded]);

  useEffect(() => {
    const src = mapRef.current?.getSource('draft') as maplibregl.GeoJSONSource | undefined;
    src?.setData(draft ?? EMPTY);
  }, [draft, loaded]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !loaded) return;
    const f: maplibregl.FilterSpecification = ['==', ['get', 'id'], selectedId ?? ''];
    map.setFilter('cand-selected', ['all', ['==', ['geometry-type'], 'Point'], f]);
    map.setFilter('cand-selected-line', ['all', ['==', ['geometry-type'], 'Polygon'], f]);
  }, [selectedId, loaded, candidates]);

  return (
    <div
      ref={container}
      className={`map-view ${crosshair ? 'crosshair' : ''} ${className ?? ''}`}
      data-testid="map"
    />
  );
}
