import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { Feature, FeatureCollection } from 'geojson';
import { useCandidates, useCoverage, useLayers, useLocation, useLocations } from '../api/hooks';
import type { Layer } from '../api/types';
import MapView, { type RasterSpec } from '../components/MapView';
import SwipeCompare from '../components/SwipeCompare';
import LayerControl, {
  BASEMAP,
  layerLabel,
  type CompareState,
  type LayerState,
  type LayerStates,
} from '../components/LayerControl';
import LocationList from '../components/LocationList';
import CoveragePanel from '../components/CoveragePanel';
import CandidatePanel, { type DrawMode, type DrawState } from '../components/CandidatePanel';
import { StatusBadge } from '../components/Badges';
import { locationAoi, locationName } from '../lib/geo';

const NO_DRAW: DrawState = { mode: 'none', vertices: [] };

function toRaster(l: Layer, st: LayerState | undefined): RasterSpec {
  return { id: l.id, tileUrl: l.tile_url, opacity: st?.opacity ?? 1, bounds: l.bounds };
}

function draftCollection(d: DrawState): FeatureCollection {
  const features: Feature[] = d.vertices.map((c) => ({
    type: 'Feature',
    properties: {},
    geometry: { type: 'Point', coordinates: c },
  }));
  if (d.mode === 'polygon' && d.vertices.length >= 2) {
    features.push({
      type: 'Feature',
      properties: {},
      geometry:
        d.vertices.length >= 3
          ? { type: 'Polygon', coordinates: [[...d.vertices, d.vertices[0]]] }
          : { type: 'LineString', coordinates: d.vertices },
    });
  }
  return { type: 'FeatureCollection', features };
}

export default function Explore() {
  const [params, setParams] = useSearchParams();
  const locationId = params.get('loc');
  const selectLocation = (id: string) => {
    setParams({ loc: id });
    setSelectedId(null);
    setDraw(NO_DRAW);
  };

  const locations = useLocations();
  const location = useLocation(locationId);
  const coverage = useCoverage(locationId);
  const layersQ = useLayers(locationId);
  const candidatesQ = useCandidates(locationId ? { location_id: locationId } : {});

  const [layerStates, setLayerStates] = useState<LayerStates>({});
  const [compare, setCompare] = useState<CompareState>({
    enabled: false,
    leftId: BASEMAP,
    rightId: BASEMAP,
  });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draw, setDraw] = useState<DrawState>(NO_DRAW);
  const [panelOpen, setPanelOpen] = useState(true);

  const layers = useMemo(() => layersQ.data ?? [], [layersQ.data]);

  // Initialise layer state / compare choices when a location's layers arrive.
  useEffect(() => {
    const states: LayerStates = {};
    for (const l of layers) states[l.id] = { visible: false, opacity: 1 };
    const svf = layers.filter((l) => l.kind === 'svf').sort((a, b) => a.epoch - b.epoch);
    const first = svf[0] ?? layers[0];
    const last = svf[svf.length - 1] ?? layers[layers.length - 1];
    if (last) states[last.id].visible = true;
    setLayerStates(states);
    setCompare({ enabled: false, leftId: first?.id ?? BASEMAP, rightId: last?.id ?? BASEMAP });
  }, [layers]);

  const feature =
    location.data ?? locations.data?.features.find((f) => f.properties.id === locationId);
  const bounds = useMemo(() => (feature ? locationAoi(feature) : null), [feature]);

  const byId = useMemo(() => new Map(layers.map((l) => [l.id, l])), [layers]);
  const stackRasters = layers
    .filter((l) => layerStates[l.id]?.visible)
    .sort((a, b) => a.epoch - b.epoch)
    .map((l) => toRaster(l, layerStates[l.id]));
  const sideRasters = (id: string): RasterSpec[] => {
    const l = byId.get(id);
    return l ? [toRaster(l, layerStates[l.id])] : [];
  };
  const labelOf = (id: string) => {
    const l = byId.get(id);
    return l ? layerLabel(l) : 'Basemap';
  };

  const selected = candidatesQ.data?.features.find((c) => c.properties.id === selectedId) ?? null;

  const onMapClick = (lngLat: [number, number], candidateId: string | null) => {
    if (draw.mode === 'point') {
      setSelectedId(null);
      setDraw({ mode: 'point', vertices: [lngLat] });
    } else if (draw.mode === 'polygon') {
      setSelectedId(null);
      setDraw({ mode: 'polygon', vertices: [...draw.vertices, lngLat] });
    } else {
      setSelectedId(candidateId);
      if (candidateId) setPanelOpen(true);
    }
  };

  const setMode = (mode: DrawMode) => {
    setSelectedId(null);
    setDraw(mode === 'none' ? NO_DRAW : { mode, vertices: [] });
  };

  const common = {
    bounds,
    candidates: candidatesQ.data ?? null,
    selectedId,
    draft: draw.mode === 'none' ? null : draftCollection(draw),
    crosshair: draw.mode !== 'none',
    onClick: onMapClick,
  };

  return (
    <div className="explore">
      <aside className="sidebar">
        <section>
          <h2>Locations</h2>
          <LocationList
            locations={locations.data?.features ?? []}
            selectedId={locationId}
            onSelect={selectLocation}
            loading={locations.isLoading}
            error={locations.error?.message}
          />
        </section>
        <section>
          <h2>Layers</h2>
          {!locationId ? (
            <p className="muted">Select a location.</p>
          ) : layersQ.isLoading ? (
            <p className="muted">Loading layers...</p>
          ) : (
            <LayerControl
              layers={layers}
              states={layerStates}
              onChange={(id, patch) =>
                setLayerStates((s) => ({ ...s, [id]: { ...s[id], ...patch } }))
              }
              compare={compare}
              onCompareChange={setCompare}
            />
          )}
        </section>
        <section>
          <h2>Coverage</h2>
          {locationId ? (
            <CoveragePanel coverage={coverage.data} loading={coverage.isLoading} />
          ) : (
            <p className="muted">Select a location.</p>
          )}
        </section>
      </aside>

      <main className="map-area">
        {compare.enabled && layers.length > 0 ? (
          <SwipeCompare
            {...common}
            left={sideRasters(compare.leftId)}
            right={sideRasters(compare.rightId)}
            leftLabel={labelOf(compare.leftId)}
            rightLabel={labelOf(compare.rightId)}
          />
        ) : (
          <MapView {...common} rasters={stackRasters} />
        )}
        <div className="map-title">{feature ? locationName(feature) : 'Select a location'}</div>
      </main>

      <aside className="sidebar right">
        <section>
          <h2 onClick={() => setPanelOpen((o) => !o)} className="collapsible">
            Candidates {panelOpen ? '▾' : '▸'}
          </h2>
          {panelOpen && (
            <>
              <CandidatePanel
                selected={selected}
                locationId={locationId}
                draw={draw}
                onDrawMode={setMode}
                onUndoVertex={() => setDraw((d) => ({ ...d, vertices: d.vertices.slice(0, -1) }))}
                onDone={(id) => {
                  setDraw(NO_DRAW);
                  setSelectedId(id ?? null);
                }}
              />
              <ul className="list">
                {candidatesQ.data?.features.map((c) => (
                  <li key={c.properties.id}>
                    <button
                      className={`list-item ${c.properties.id === selectedId ? 'active' : ''}`}
                      onClick={() => {
                        setDraw(NO_DRAW);
                        setSelectedId(c.properties.id);
                      }}
                    >
                      <span>
                        {c.properties.morph_class.replace(/_/g, ' ')} · {c.properties.id}
                      </span>
                      <StatusBadge value={c.properties.review_status} />
                    </button>
                  </li>
                ))}
                {candidatesQ.data?.features.length === 0 && (
                  <li className="muted">No candidates yet.</li>
                )}
              </ul>
            </>
          )}
        </section>
      </aside>
    </div>
  );
}
