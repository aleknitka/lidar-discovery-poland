import { useEffect, useMemo, useRef, useState } from 'react';
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { FeatureCollection } from 'geojson';
import { api, ApiError } from '../api/client';
import { isActiveJob, useActiveJobs, useJob } from '../api/hooks';
import type { AreaEstimate, BBox, Job } from '../api/areaTypes';
import type { Bounds } from '../lib/geo';
import { polygonShareInside, viewAreaKm2 } from '../lib/geo';
import {
  formatBytes,
  formatDuration,
  formatEta,
  formatKm2,
  formatShare,
  formatSpeed,
  percentOf,
} from '../lib/format';
import {
  AREA_COLORS,
  estimateOverlay,
  jobOverlay,
  stateColour,
  statusView,
  type SheetState,
} from '../lib/areaStyle';
import { usePersistentState } from '../lib/usePersistentState';
import {
  DEFAULT_LAYERS,
  LAYER_CHOICES,
  displayName,
  layerInfo,
  layersParam,
} from '../content/layers';

/** The button is enabled from this zoom level (a viewport must be small enough to be fetched). */
export const MIN_FETCH_ZOOM = 13;
/** Mirrors the server default LDP_MAX_FETCH_AREA_KM2; the server stays the authority. */
export const VIEW_AREA_HINT_KM2 = 6;

type Epoch = { source_id: string; year: number } | null;

const PHASES: Record<string, string> = {
  queued: 'Queued',
  listing: 'Finding LiDAR sheets',
  downloading: 'Downloading LiDAR',
  processing: 'Processing',
  done: 'Done',
  failed: 'Failed',
  cancelled: 'Cancelled',
};

export function jobPercent(j: Job): number | null {
  if (j.state === 'downloading') return j.bytes_total ? (100 * j.bytes_done) / j.bytes_total : 0;
  if (j.state === 'processing') return j.steps ? (100 * j.step) / j.steps : 0;
  if (j.state === 'done') return 100;
  return null; // indeterminate
}

function estimateOf(q: { data?: AreaEstimate; error: Error | null }): AreaEstimate | null {
  if (q.data) return q.data;
  if (q.error instanceof ApiError && q.error.body?.estimate)
    return q.error.body.estimate as AreaEstimate;
  return null;
}

const isLayerSet = (v: unknown): v is string[] =>
  Array.isArray(v) && v.every((x) => typeof x === 'string');

// ------------------------------------------------------------------------------ the state hook
export interface AreaFetchState {
  view: { bounds: Bounds; zoom: number } | null;
  zoomOk: boolean;
  /** Approximate area of the visible map window, km2 (null before the map has loaded). */
  areaKm2: number | null;
  /** True when the visible window fits the default fetch limit; the server still decides. */
  areaOk: boolean;
  frozen: BBox | null;
  epoch: Epoch;
  setEpoch: (e: Epoch) => void;
  layers: string[];
  setLayers: (l: string[]) => void;
  jobId: string | null;
  job: Job | undefined;
  open: () => void;
  close: () => void;
  start: (est: AreaEstimate) => void;
  starting: boolean;
  startError: string | null;
  cancel: () => void;
  cancelling: boolean;
  dismiss: () => void;
  /** Ask the map to frame this box (the frozen view) so the outline is visible. */
  focus: { bounds: Bounds; key: string } | null;
  /** Draw (or clear) sheet footprints and the view outline on the map. */
  setOverlay: (fc: FeatureCollection | null) => void;
}

export function useAreaFetch(
  view: { bounds: Bounds; zoom: number } | null,
  onOverlay: (fc: FeatureCollection | null) => void,
  onDone: (locationId: string) => void,
): AreaFetchState {
  const qc = useQueryClient();
  const [frozen, setFrozen] = useState<BBox | null>(null);
  const [epoch, setEpoch] = useState<Epoch>(null);
  const [layers, setLayers] = usePersistentState<string[]>(
    'ldp.fetch.layers',
    [...DEFAULT_LAYERS],
    isLayerSet,
  );
  const [jobId, setJobId] = useState<string | null>(null);
  const [focus, setFocus] = useState<AreaFetchState['focus']>(null);
  const active = useActiveJobs();
  const job = useJob(jobId);
  const handled = useRef<string | null>(null);
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;

  // Re-attach to a job that is still running (survives a page reload).
  useEffect(() => {
    if (!jobId && active.data && active.data.length > 0) setJobId(active.data[0].id);
  }, [active.data, jobId]);

  const startM = useMutation({
    mutationFn: (est: AreaEstimate) =>
      api.fetchArea({
        bbox: est.bbox,
        source_id: est.source_id,
        year: est.year,
        layers: layersParam(layers),
      }),
    onSuccess: (j) => {
      setFrozen(null);
      setJobId(j.id);
      qc.setQueryData(['job', j.id], j);
    },
  });
  const cancelM = useMutation({
    mutationFn: (id: string) => api.cancelJob(id),
    onSuccess: (j) => qc.setQueryData(['job', j.id], j),
  });

  const j = job.data;
  useEffect(() => {
    if (j?.state === 'done' && j.location_id && handled.current !== j.id) {
      handled.current = j.id;
      const loc = j.location_id;
      void Promise.all([
        qc.invalidateQueries({ queryKey: ['locations'] }),
        qc.invalidateQueries({ queryKey: ['layers'] }),
        qc.invalidateQueries({ queryKey: ['jobs'] }),
      ]).then(() => onDoneRef.current(loc));
    }
  }, [j, qc]);

  // Map overlay while a job is shown (the estimate card draws its own).
  useEffect(() => {
    if (frozen) return;
    if (!j || !jobId) {
      onOverlay(null);
      return;
    }
    onOverlay(jobOverlay(j.params.bbox, j.tiles));
  }, [j, jobId, frozen, onOverlay]);

  return {
    view,
    zoomOk: !!view && view.zoom >= MIN_FETCH_ZOOM,
    areaKm2: view ? viewAreaKm2(view.bounds) : null,
    areaOk: !!view && viewAreaKm2(view.bounds) <= VIEW_AREA_HINT_KM2,
    frozen,
    epoch,
    setEpoch,
    layers,
    setLayers,
    jobId,
    job: j,
    open: () => {
      if (!view) return;
      const b = [...view.bounds] as BBox;
      setEpoch(null);
      setFrozen(b);
      setFocus({ bounds: b, key: `${b.join(',')}@${Date.now()}` });
    },
    close: () => {
      setFrozen(null);
      setEpoch(null);
      onOverlay(null);
    },
    start: (est) => startM.mutate(est),
    starting: startM.isPending,
    startError: startM.error ? startM.error.message : null,
    cancel: () => j && cancelM.mutate(j.id),
    cancelling: cancelM.isPending,
    dismiss: () => {
      setJobId(null);
      onOverlay(null);
      void qc.invalidateQueries({ queryKey: ['jobs'] });
    },
    focus,
    setOverlay: onOverlay,
  };
}

// ------------------------------------------------------------------------ map button
/** Floating button on the map. */
export function FetchButton({ fetch, onOpened }: { fetch: AreaFetchState; onOpened: () => void }) {
  const busy = !!fetch.jobId || !!fetch.frozen;
  return (
    <div className="map-action">
      <button
        className="primary"
        disabled={!fetch.zoomOk || !fetch.areaOk || busy}
        onClick={() => {
          fetch.open();
          onOpened();
        }}
        aria-describedby={!fetch.zoomOk || !fetch.areaOk ? 'area-hint' : undefined}
      >
        Get data for this view
      </button>
      {!fetch.zoomOk ? (
        <span id="area-hint" className="area-hint">
          Zoom in to fetch LiDAR
        </span>
      ) : (
        !fetch.areaOk &&
        fetch.areaKm2 !== null && (
          <span id="area-hint" className="area-hint">
            View is {fetch.areaKm2 < 10 ? fetch.areaKm2.toFixed(1) : Math.round(fetch.areaKm2)} km².
            Zoom in to under {VIEW_AREA_HINT_KM2} km².
          </span>
        )
      )}
    </div>
  );
}

// ------------------------------------------------------------------------ pieces
function Swatch({ kind }: { kind: 'viewport' | 'cached' | 'todo' }) {
  return <span className={`swatch swatch-${kind}`} aria-hidden="true" />;
}

export function AreaLegend() {
  return (
    <ul className="area-legend" aria-label="Map legend">
      <li>
        <Swatch kind="viewport" /> Your view
      </li>
      <li>
        <Swatch kind="cached" /> Sheet already downloaded (cached)
      </li>
      <li>
        <Swatch kind="todo" /> Sheet to download
      </li>
    </ul>
  );
}

interface Row {
  godlo: string;
  size: number | null;
  state: SheetState;
  share?: number;
  bytes?: number;
}

export function SheetTable({ rows, live }: { rows: Row[]; live?: boolean }) {
  return (
    <table className="table sheets">
      <caption className="sr-only">LiDAR sheets covering the view</caption>
      <thead>
        <tr>
          <th scope="col">Sheet</th>
          <th scope="col">Size</th>
          {!live && <th scope="col">Your view covers</th>}
          <th scope="col">Status</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => {
          const v = statusView(r.state);
          return (
            <tr key={r.godlo}>
              <th scope="row" className="mono">
                {r.godlo}
              </th>
              <td>{formatBytes(r.size)}</td>
              {!live && <td>{formatShare(r.share)}</td>}
              <td>
                <span className={`status-chip tone-${v.tone}`}>
                  <span aria-hidden="true">{v.icon}</span> {v.text}
                  {r.state === 'downloading' && r.size
                    ? ` ${Math.round(percentOf(r.bytes ?? 0, r.size))} %`
                    : ''}
                </span>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

/** Cached vs to-download bytes as one stacked bar with totals. */
export function CacheBar({ est }: { est: AreaEstimate }) {
  const cached = est.bytes_cached ?? 0;
  const todo = est.bytes_to_download ?? 0;
  const partial = Math.max(est.bytes_total - cached - todo, 0);
  const total = Math.max(est.bytes_total, 1);
  const summary = `${formatBytes(cached)} cached, ${formatBytes(todo)} to download, ${formatBytes(est.bytes_total)} in total`;
  return (
    <div className="cachebar">
      <div className="bar" role="img" aria-label={summary}>
        <span className="seg seg-cached" style={{ width: `${percentOf(cached, total)}%` }} />
        <span className="seg seg-partial" style={{ width: `${percentOf(partial, total)}%` }} />
        <span className="seg seg-todo" style={{ width: `${percentOf(todo, total)}%` }} />
      </div>
      <ul className="bar-legend">
        <li>
          <Swatch kind="cached" /> Cached <strong>{formatBytes(cached)}</strong>
        </li>
        {partial > 0 && (
          <li>
            <span className="swatch swatch-partial" aria-hidden="true" /> Partly downloaded{' '}
            <strong>{formatBytes(partial)}</strong>
          </li>
        )}
        <li>
          <Swatch kind="todo" /> To download <strong>{formatBytes(todo)}</strong>
        </li>
        <li className="total">
          Total <strong>{formatBytes(est.bytes_total)}</strong>
        </li>
      </ul>
    </div>
  );
}

function AreaMeter({ km2, limit }: { km2: number; limit: number }) {
  const over = km2 > limit;
  return (
    <div className="areameter">
      <div className="row-between">
        <span>Your view</span>
        <strong className={over ? 'error' : ''}>
          {formatKm2(km2)} of {formatKm2(limit)} allowed
        </strong>
      </div>
      <meter
        min={0}
        max={limit}
        low={limit * 0.7}
        high={limit * 0.9}
        optimum={0}
        value={Math.min(km2, limit)}
        aria-label={`View area ${formatKm2(km2)}, limit ${formatKm2(limit)}`}
      />
    </div>
  );
}

function LayerPicker({
  est,
  selected,
  onChange,
}: {
  est: AreaEstimate | null;
  selected: string[];
  onChange: (l: string[]) => void;
}) {
  const sec = est?.processing_s ?? null;
  const have = new Set(est?.layers_existing ?? []);
  return (
    <fieldset className="layer-picker">
      <legend>Layers to build</legend>
      <ul>
        {LAYER_CHOICES.map((c) => {
          const checked = c.required || selected.includes(c.kind);
          const onDisk = have.has(c.kind);
          const secs = sec?.[c.kind];
          const info = layerInfo(c.kind);
          return (
            <li key={c.kind}>
              <label>
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={c.required}
                  onChange={(e) =>
                    onChange(
                      e.target.checked
                        ? [...selected.filter((k) => k !== c.kind), c.kind]
                        : selected.filter((k) => k !== c.kind),
                    )
                  }
                />{' '}
                {displayName(c.kind)} {info && <small className="tech">{info.technical}</small>}
              </label>
              <span className="muted small layer-cost">
                {c.required && 'required by all others'}
                {c.required && (onDisk || secs != null) && ' · '}
                {onDisk
                  ? 'already built'
                  : checked && secs != null
                    ? `~${formatDuration(secs)}`
                    : checked && est
                      ? ''
                      : ''}
              </span>
            </li>
          );
        })}
      </ul>
      {est?.processing_s && (est.layers_missing?.length ?? 0) > 0 && (
        <p className="small">
          Processing estimate: <strong>~{formatDuration(est.processing_s.total)}</strong>
          {est.from_existing_dtm ? ' (reuses the bare-earth height already on disk)' : ''}. Measured
          on a 2 km² area; slower machines and denser data take longer.
        </p>
      )}
      <p className="note small">
        Layer choice affects processing time and disk space, not the download size. The LiDAR sheet
        download is the biggest cost and is the same whichever layers you pick.
      </p>
    </fieldset>
  );
}

// ------------------------------------------------------------------------ estimate card
function EstimateCard({ f }: { f: AreaFetchState }) {
  const bbox = f.frozen as BBox;
  const layersKey = layersParam(f.layers);
  const q = useQuery({
    queryKey: ['estimate', bbox, f.epoch, layersKey],
    queryFn: () => api.estimateArea(bbox, f.epoch?.source_id, f.epoch?.year, layersKey),
    retry: false,
    staleTime: 0,
    gcTime: 0,
    placeholderData: keepPreviousData,
  });
  const est = estimateOf(q);
  const blocked = !!est?.over_limit;
  // Older over-limit responses carried a sheet count here, so only trust a real list.
  const tiles = useMemo(() => (Array.isArray(est?.tiles) ? est.tiles : []), [est]);
  const setOverlay = f.setOverlay;
  // Footprints stay on the map while the card is open; the job overlay takes over afterwards.
  useEffect(() => {
    setOverlay(estimateOverlay(bbox, tiles));
  }, [bbox, tiles, setOverlay]);

  return (
    <div className="area-card" role="group" aria-labelledby="estimate-title">
      <h3 id="estimate-title">Get data for this view</h3>
      {q.isLoading && <p className="muted">Estimating...</p>}
      {q.error && !est && <p className="error">{q.error.message}</p>}
      {est && (
        <>
          {(est.epochs?.length ?? 0) > 0 && (
            <label className="field">
              Epoch (survey year)
              <select
                value={`${est.source_id}|${est.year}`}
                onChange={(e) => {
                  const [source_id, year] = e.target.value.split('|');
                  f.setEpoch({ source_id, year: Number(year) });
                }}
              >
                {est.epochs!.map((o) => (
                  <option key={`${o.source_id}|${o.year}`} value={`${o.source_id}|${o.year}`}>
                    {o.year} · {o.source_id} ({o.tiles} sheets
                    {o.nominal_density ? `, ${o.nominal_density}` : ''})
                  </option>
                ))}
              </select>
            </label>
          )}

          <AreaMeter km2={est.area_km2} limit={est.limits.max_area_km2} />
          <AreaLegend />

          {est.over_limit === 'area' && (
            <p className="error">
              Too large: {formatKm2(est.area_km2)} (limit {formatKm2(est.limits.max_area_km2)}).
              Zoom in.
            </p>
          )}
          {est.over_limit === 'bytes' && (
            <p className="error">
              Too large: {formatBytes(est.bytes_total)} of LiDAR (limit{' '}
              {formatBytes(est.limits.max_bytes)}). Zoom in or pick another epoch.
            </p>
          )}

          {tiles.length > 0 && (
            <>
              {est.processed ? (
                <p className="ok-note" role="status">
                  ✓ Everything is already on disk, and these layers are already built.
                </p>
              ) : (est.bytes_to_download ?? 0) === 0 ? (
                <p className="ok-note" role="status">
                  ✓ Everything is already on disk. Nothing to download
                  {est.needs_laz === false
                    ? '; the missing layers are built from the stored bare-earth height.'
                    : '; only processing is needed.'}
                </p>
              ) : null}
              <CacheBar est={est} />
              <SheetTable
                rows={tiles.map((t) => ({
                  godlo: t.godlo,
                  size: t.size_bytes,
                  state: t.cached ? 'cached' : 'todo',
                  share: polygonShareInside(t.footprint, bbox),
                }))}
              />
              <p className="muted small">
                A download always fetches whole map sheets (about 1.2 x 1.2 km, 100 to 600 MB each),
                however small your view is. Processing is clipped to your view.
              </p>
            </>
          )}
          {!blocked && !q.isLoading && tiles.length === 0 && (
            <p className="warn">No LiDAR coverage for this view.</p>
          )}
          {!blocked && (est.bytes_to_download ?? 0) > 1e9 && (
            <p className="warn">Large download: this may take a long time.</p>
          )}
        </>
      )}

      <LayerPicker est={est} selected={f.layers} onChange={f.setLayers} />

      {f.startError && <p className="error">{f.startError}</p>}
      <div className="row-gap">
        <button
          className="primary"
          disabled={!est || blocked || tiles.length === 0 || f.starting || q.isFetching}
          onClick={() => est && f.start(est)}
        >
          {est?.processed
            ? 'Show layers'
            : (est?.bytes_to_download ?? 0) === 0 && tiles.length > 0
              ? 'Process'
              : 'Download and process'}
        </button>
        <button onClick={f.close}>Close</button>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------ progress card
function ProgressCard({ f }: { f: AreaFetchState }) {
  const job = f.job as Job;
  const pct = jobPercent(job);
  const active = isActiveJob(job);
  let label = PHASES[job.state] ?? job.state;
  if (job.state === 'processing' && job.steps)
    label = `Processing: step ${job.step}/${job.steps}${job.step_name ? ` (${job.step_name})` : ''}`;
  if (job.state === 'done' && job.message === 'cached') label = 'Done (already on disk)';
  const bits: string[] = [];
  if (job.bytes_total)
    bits.push(`${formatBytes(job.bytes_done)} of ${formatBytes(job.bytes_total)}`);
  if (job.tiles_total) bits.push(`${job.tiles_done} of ${job.tiles_total} sheets`);
  if (job.state === 'downloading') {
    if (job.speed_bps) bits.push(formatSpeed(job.speed_bps));
    const eta = formatEta(job.eta_s);
    if (eta) bits.push(eta);
  }
  const layers = job.params.layers ?? [];
  return (
    <div className="area-card" role="region" aria-label="LiDAR fetch progress">
      <h3>{label}</h3>
      <progress
        className="area-progress"
        max={100}
        {...(pct != null ? { value: Math.round(pct) } : {})}
        aria-label={label}
        aria-valuetext={pct != null ? `${Math.round(pct)}%` : 'working'}
      />
      {pct != null && active && <p className="muted">{Math.round(pct)}%</p>}
      {bits.length > 0 && <p>{bits.join(' · ')}</p>}
      {layers.length > 0 && (
        <p className="muted small">Layers: {layers.map((k) => displayName(k)).join(', ')}</p>
      )}
      {job.tiles.length > 0 && (
        <>
          <AreaLegend />
          <SheetTable
            live
            rows={job.tiles.map((t) => ({
              godlo: t.godlo,
              size: t.size_bytes,
              state: t.status,
              bytes: t.bytes,
            }))}
          />
        </>
      )}
      {job.error && <p className="error">{job.error}</p>}
      {job.state === 'done' && (
        <p className="muted">Done. The new area is selected with its bare-earth height shown.</p>
      )}
      {job.state === 'cancelled' && (
        <p className="muted">Cancelled. Partial downloads are kept and will resume.</p>
      )}
      <div className="row-gap">
        {active ? (
          <button onClick={f.cancel} disabled={f.cancelling}>
            {f.cancelling ? 'Cancelling...' : 'Cancel'}
          </button>
        ) : (
          <button onClick={f.dismiss}>Dismiss</button>
        )}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------ the Data tab block
export default function AreaFetchPanel({ fetch: f }: { fetch: AreaFetchState }) {
  if (f.jobId && f.job) return <ProgressCard f={f} />;
  if (f.frozen) return <EstimateCard f={f} />;
  return (
    <div>
      <p>
        Download the LiDAR sheets that cover the part of the map you are looking at, then build
        terrain layers from them.
      </p>
      <ol className="steps">
        <li>Zoom the map to your area of interest ({`zoom ${MIN_FETCH_ZOOM} or closer`}).</li>
        <li>
          Press <strong>Get data for this view</strong> on the map. You will see which sheets are
          needed, which are already on disk, and how much to download.
        </li>
        <li>Choose the layers to build and confirm.</li>
      </ol>
      <p className="muted small">
        Legend on the map once you start: <AreaLegendInline />
      </p>
      {!f.zoomOk && <p className="warn">Zoom in a little more to enable the button.</p>}
      <p className="muted small">
        Colours: <span style={{ color: AREA_COLORS.cached }}>blue</span> cached,{' '}
        <span style={{ color: stateColour('todo') }}>orange</span> to download. The line style and a
        text label differ too.
      </p>
    </div>
  );
}

function AreaLegendInline() {
  return (
    <span>
      <Swatch kind="viewport" /> your view <Swatch kind="cached" /> cached <Swatch kind="todo" /> to
      download
    </span>
  );
}
