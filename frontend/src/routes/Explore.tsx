import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { Feature, FeatureCollection } from 'geojson';
import { useCandidates, useCoverage, useLayers, useLocation, useLocations } from '../api/hooks';
import { isActiveJob } from '../api/hooks';
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
import AreaFetchPanel, { FetchButton, useAreaFetch } from '../components/AreaFetch';
import InfoTab from '../components/InfoTab';
import MissingLayers from '../components/MissingLayers';
import SidePanel, { PanelOpenButton, isTabId, type TabId } from '../components/SidePanel';
import CoveragePanel from '../components/CoveragePanel';
import CandidatePanel, { type DrawMode, type DrawState } from '../components/CandidatePanel';
import { StatusBadge } from '../components/Badges';
import { kindRank } from '../content/layers';
import { locationAoi, locationName, type Bounds } from '../lib/geo';
import { usePersistentState } from '../lib/usePersistentState';

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

const isBool = (v: unknown): v is boolean => typeof v === 'boolean';
const narrowScreen = () => window.matchMedia('(max-width: 720px)').matches;

/** The layer to switch on when a place is shown: the newest epoch's bare-earth height (DTM). */
export function defaultVisibleLayer(layers: Layer[]): Layer | undefined {
  const byEpoch = [...layers].sort((a, b) => b.epoch - a.epoch);
  return (
    byEpoch.find((l) => l.kind === 'dtm') ??
    byEpoch.find((l) => l.kind === 'hillshade') ??
    [...byEpoch].sort((a, b) => kindRank(a.kind) - kindRank(b.kind))[0]
  );
}

export default function Explore() {
  const [params, setParams] = useSearchParams();
  const locationId = params.get('loc');

  const locations = useLocations();
  const location = useLocation(locationId);
  const coverage = useCoverage(locationId);
  const layersQ = useLayers(locationId);
  const candidatesQ = useCandidates(locationId ? { location_id: locationId } : {});

  const [panelOpen, setPanelOpen] = usePersistentState<boolean>(
    'ldp.panel.open',
    !narrowScreen(),
    isBool,
  );
  const [tab, setTab] = usePersistentState<TabId>('ldp.panel.tab', 'layers', isTabId);
  const [info, setInfo] = useState<{ kind: string; layerId: string | null }>({
    kind: 'dtm',
    layerId: null,
  });
  const [layerStates, setLayerStates] = useState<LayerStates>({});
  const [compare, setCompare] = useState<CompareState>({
    enabled: false,
    leftId: BASEMAP,
    rightId: BASEMAP,
  });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draw, setDraw] = useState<DrawState>(NO_DRAW);
  const [view, setView] = useState<{ bounds: Bounds; zoom: number } | null>(null);
  const [areaFc, setAreaFc] = useState<FeatureCollection | null>(null);

  const selectLocation = (id: string, toLayers = false) => {
    setParams({ loc: id });
    setSelectedId(null);
    setDraw(NO_DRAW);
    if (toLayers) setTab('layers');
  };

  const fetchState = useAreaFetch(view, setAreaFc, (id) => selectLocation(id, true));
  const jobBusy = isActiveJob(fetchState.job);

  const layers = useMemo(() => layersQ.data ?? [], [layersQ.data]);

  // Initialise layer state / compare choices when a place's layers arrive: the bare-earth height
  // (DTM) is switched on first, everything else off.
  useEffect(() => {
    const states: LayerStates = {};
    for (const l of layers) states[l.id] = { visible: false, opacity: 1 };
    const first = defaultVisibleLayer(layers);
    if (first) states[first.id].visible = true;
    const same = layers
      .filter((l) => l.kind === (first?.kind ?? 'dtm'))
      .sort((a, b) => a.epoch - b.epoch);
    setLayerStates(states);
    setCompare({
      enabled: false,
      leftId: same[0]?.id ?? BASEMAP,
      rightId: same[same.length - 1]?.id ?? BASEMAP,
    });
  }, [layers]);

  const feature =
    location.data ?? locations.data?.features.find((f) => f.properties.id === locationId);
  const bounds = useMemo(() => (feature ? locationAoi(feature) : null), [feature]);

  const byId = useMemo(() => new Map(layers.map((l) => [l.id, l])), [layers]);
  const stackRasters = layers
    .filter((l) => layerStates[l.id]?.visible)
    .sort((a, b) => a.epoch - b.epoch || kindRank(b.kind) - kindRank(a.kind))
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

  const openTab = (t: TabId) => {
    setTab(t);
    setPanelOpen(true);
  };

  const onMapClick = (lngLat: [number, number], candidateId: string | null) => {
    if (draw.mode === 'point') {
      setSelectedId(null);
      setDraw({ mode: 'point', vertices: [lngLat] });
    } else if (draw.mode === 'polygon') {
      setSelectedId(null);
      setDraw({ mode: 'polygon', vertices: [...draw.vertices, lngLat] });
    } else {
      setSelectedId(candidateId);
      if (candidateId) openTab('candidates');
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
    area: areaFc,
    focus: fetchState.focus,
    onViewChange: setView,
    onClick: onMapClick,
  };

  return (
    <div className={`explore ${panelOpen ? 'is-panel-open' : 'is-panel-closed'}`}>
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
        <div className="map-title">{feature ? locationName(feature) : 'Bieszczady'}</div>
        <FetchButton fetch={fetchState} onOpened={() => openTab('data')} />
        {!panelOpen && <PanelOpenButton onClick={() => setPanelOpen(true)} />}
      </main>

      <SidePanel
        open={panelOpen}
        onOpenChange={setPanelOpen}
        tab={tab}
        onTabChange={setTab}
        badges={{ data: jobBusy ? '•' : undefined }}
      >
        {tab === 'layers' && (
          <div>
            {!locationId ? (
              <p className="muted">
                Nothing is shown yet. Choose a place in the Places tab, or open the Data tab to get
                LiDAR for the part of the map you are looking at.
              </p>
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
                onInfo={(l) => {
                  setInfo({ kind: l.kind, layerId: l.id });
                  setTab('info');
                }}
              />
            )}
            {locationId && !layersQ.isLoading && (
              <MissingLayers
                location={feature}
                layers={layers}
                fetch={fetchState}
                onStarted={() => openTab('data')}
              />
            )}
          </div>
        )}

        {tab === 'info' && (
          <InfoTab
            kind={info.kind}
            layerId={info.layerId}
            layers={layers}
            onKind={(kind) => setInfo({ kind, layerId: null })}
          />
        )}

        {tab === 'candidates' && (
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

        {tab === 'places' && (
          <LocationList
            locations={locations.data?.features ?? []}
            selectedId={locationId}
            onSelect={(id) => selectLocation(id, true)}
            loading={locations.isLoading}
            error={locations.error?.message}
          />
        )}

        {tab === 'data' && (
          <>
            <AreaFetchPanel fetch={fetchState} />
            <h4 className="subhead">Coverage of the selected place</h4>
            {locationId ? (
              <CoveragePanel coverage={coverage.data} loading={coverage.isLoading} />
            ) : (
              <p className="muted">Select a place to see which surveys cover it.</p>
            )}
          </>
        )}
      </SidePanel>
    </div>
  );
}
