import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { Feature, FeatureCollection, Polygon } from 'geojson';
import { api, ApiError } from '../api/client';
import { isActiveJob, useActiveJobs, useJob } from '../api/hooks';
import type { AreaEstimate, BBox, Job } from '../api/areaTypes';
import type { Bounds } from '../lib/geo';
import { formatBytes, formatEta, formatSpeed } from '../lib/format';

/** The button is enabled from this zoom level (a viewport must be small enough to be fetched). */
export const MIN_FETCH_ZOOM = 13;

interface Props {
  view: { bounds: Bounds; zoom: number } | null;
  /** Viewport rectangle + sheet footprints to draw on the map (null = nothing). */
  onOverlay: (fc: FeatureCollection | null) => void;
  /** Called once when a job finishes successfully; select the new area. */
  onDone: (locationId: string) => void;
}

const rect = (b: BBox): Polygon => ({
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

const feat = (geometry: Polygon, state: string, name?: string): Feature => ({
  type: 'Feature',
  geometry,
  properties: { state, name },
});

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

function Legend() {
  return (
    <p className="area-legend muted">
      <span className="chip chip-todo" /> to download <span className="chip chip-cached" /> cached
      <span className="chip chip-viewport" /> your view
    </p>
  );
}

function EstimateCard({
  bbox,
  epoch,
  onEpoch,
  onCancel,
  onConfirm,
  confirming,
  error,
  setOverlay,
}: {
  bbox: BBox;
  epoch: { source_id: string; year: number } | null;
  onEpoch: (e: { source_id: string; year: number } | null) => void;
  onCancel: () => void;
  onConfirm: (est: AreaEstimate) => void;
  confirming: boolean;
  error: string | null;
  setOverlay: (fc: FeatureCollection | null) => void;
}) {
  const q = useQuery({
    queryKey: ['estimate', bbox, epoch],
    queryFn: () => api.estimateArea(bbox, epoch?.source_id, epoch?.year),
    retry: false,
    staleTime: 0,
    gcTime: 0,
  });
  const est = estimateOf(q);
  const blocked = !!est?.over_limit;
  const tiles = useMemo(() => est?.tiles ?? [], [est]);

  useEffect(() => {
    const features: Feature[] = [feat(rect(bbox), 'viewport')];
    for (const t of tiles) features.push(feat(t.footprint, t.cached ? 'cached' : 'todo', t.name));
    setOverlay({ type: 'FeatureCollection', features });
  }, [bbox, tiles, setOverlay]);

  const failure = q.error && !est ? q.error.message : null;
  const toDownload = est?.bytes_to_download ?? 0;
  return (
    <div className="area-card" role="dialog" aria-label="Get data for this view">
      <h3>Get data for this view</h3>
      {q.isLoading && <p className="muted">Estimating...</p>}
      {failure && <p className="error">{failure}</p>}
      {est && (
        <>
          {(est.epochs?.length ?? 0) > 0 && (
            <label className="field">
              Epoch
              <select
                value={`${est.source_id}|${est.year}`}
                onChange={(e) => {
                  const [source_id, year] = e.target.value.split('|');
                  onEpoch({ source_id, year: Number(year) });
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
          <p>
            {est.area_km2.toFixed(2)} km² · {tiles.length} sheet{tiles.length === 1 ? '' : 's'}
          </p>
          {tiles.length > 0 && (
            <p>
              <strong>{formatBytes(toDownload)}</strong> to download,{' '}
              {formatBytes(est.bytes_cached ?? 0)} already cached
              {est.processed ? ' · already processed' : ''}
            </p>
          )}
          {est.over_limit === 'area' && (
            <p className="error">
              Too large: {est.area_km2.toFixed(1)} km² (limit {est.limits.max_area_km2} km²). Zoom
              in.
            </p>
          )}
          {est.over_limit === 'bytes' && (
            <p className="error">
              Too large: {formatBytes(est.bytes_total)} of LiDAR (limit{' '}
              {formatBytes(est.limits.max_bytes)}). Zoom in or pick another epoch.
            </p>
          )}
          {!blocked && toDownload > 1e9 && (
            <p className="warn">Large download: this may take a long time.</p>
          )}
          {!blocked && !q.isLoading && tiles.length === 0 && (
            <p className="warn">No LiDAR coverage for this view.</p>
          )}
          {tiles.length > 0 && <Legend />}
        </>
      )}
      {error && <p className="error">{error}</p>}
      <div className="row-gap">
        <button
          className="primary"
          disabled={!est || blocked || tiles.length === 0 || confirming}
          onClick={() => est && onConfirm(est)}
        >
          {est?.processed ? 'Show layers' : 'Download and process'}
        </button>
        <button onClick={onCancel}>Close</button>
      </div>
    </div>
  );
}

function ProgressPanel({
  job,
  onCancel,
  onDismiss,
  cancelling,
}: {
  job: Job;
  onCancel: () => void;
  onDismiss: () => void;
  cancelling: boolean;
}) {
  const pct = jobPercent(job);
  const active = isActiveJob(job);
  let label = PHASES[job.state] ?? job.state;
  if (job.state === 'processing' && job.steps)
    label = `Processing: step ${job.step}/${job.steps}${job.step_name ? ` (${job.step_name})` : ''}`;
  if (job.state === 'done' && job.message === 'cached') label = 'Done (already cached)';
  const bits: string[] = [];
  if (job.bytes_total)
    bits.push(`${formatBytes(job.bytes_done)} of ${formatBytes(job.bytes_total)}`);
  if (job.tiles_total) bits.push(`${job.tiles_done} of ${job.tiles_total} sheets`);
  if (job.state === 'downloading') {
    if (job.speed_bps) bits.push(formatSpeed(job.speed_bps));
    const eta = formatEta(job.eta_s);
    if (eta) bits.push(eta);
  }
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
      {bits.length > 0 && <p aria-live="off">{bits.join(' · ')}</p>}
      {job.state === 'downloading' && job.current_item && (
        <p className="muted">Sheet: {job.current_item}</p>
      )}
      {job.error && <p className="error">{job.error}</p>}
      {job.state === 'done' && <p className="muted">Layers added; SVF shown.</p>}
      {job.state === 'cancelled' && (
        <p className="muted">Cancelled. Partial downloads are kept and will resume.</p>
      )}
      <div className="row-gap">
        {active ? (
          <button onClick={onCancel} disabled={cancelling}>
            {cancelling ? 'Cancelling...' : 'Cancel'}
          </button>
        ) : (
          <button onClick={onDismiss}>Dismiss</button>
        )}
      </div>
    </div>
  );
}

export default function AreaFetch({ view, onOverlay, onDone }: Props) {
  const qc = useQueryClient();
  const [frozen, setFrozen] = useState<BBox | null>(null);
  const [epoch, setEpoch] = useState<{ source_id: string; year: number } | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const active = useActiveJobs();
  const job = useJob(jobId);
  const handled = useRef<string | null>(null);
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;

  // Re-attach to a job that is still running (survives a page reload).
  useEffect(() => {
    if (!jobId && active.data && active.data.length > 0) setJobId(active.data[0].id);
  }, [active.data, jobId]);

  const start = useMutation({
    mutationFn: (est: AreaEstimate) =>
      api.fetchArea({ bbox: est.bbox, source_id: est.source_id, year: est.year }),
    onSuccess: (j) => {
      setFrozen(null);
      setJobId(j.id);
      qc.setQueryData(['job', j.id], j);
    },
  });
  const cancel = useMutation({
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
    const features: Feature[] = [feat(rect(j.params.bbox), 'viewport')];
    for (const t of j.tiles) if (t.footprint) features.push(feat(t.footprint, t.status, t.name));
    onOverlay({ type: 'FeatureCollection', features });
  }, [j, jobId, frozen, onOverlay]);

  const zoomOk = !!view && view.zoom >= MIN_FETCH_ZOOM;
  const busy = !!jobId;

  if (jobId && j) {
    return (
      <div className="map-action">
        <ProgressPanel
          job={j}
          cancelling={cancel.isPending}
          onCancel={() => cancel.mutate(j.id)}
          onDismiss={() => {
            setJobId(null);
            onOverlay(null);
            void qc.invalidateQueries({ queryKey: ['jobs'] });
          }}
        />
      </div>
    );
  }
  if (frozen) {
    return (
      <div className="map-action">
        <EstimateCard
          bbox={frozen}
          epoch={epoch}
          onEpoch={setEpoch}
          onCancel={() => {
            setFrozen(null);
            setEpoch(null);
            onOverlay(null);
          }}
          onConfirm={(est) => start.mutate(est)}
          confirming={start.isPending}
          error={start.error ? start.error.message : null}
          setOverlay={onOverlay}
        />
      </div>
    );
  }
  return (
    <div className="map-action">
      <button
        className="primary"
        disabled={!zoomOk || busy}
        onClick={() => {
          if (view) {
            setEpoch(null);
            setFrozen([...view.bounds] as BBox);
          }
        }}
        aria-describedby="area-hint"
      >
        Get data for this view
      </button>
      {!zoomOk && (
        <span id="area-hint" className="area-hint">
          Zoom in to fetch LiDAR
        </span>
      )}
    </div>
  );
}
