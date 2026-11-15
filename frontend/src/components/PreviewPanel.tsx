import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { FeatureCollection } from 'geojson';
import { api } from '../api/client';
import type { Bounds } from '../lib/geo';
import { viewAreaKm2 } from '../lib/geo';
import { formatKm2 } from '../lib/format';
import type { PreviewCandidateRaw, PreviewResult } from '../api/types';

export function previewCandidatesToFC(cands: PreviewCandidateRaw[]): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: cands.map((c) => {
      const isLine = Boolean((c as unknown as { _is_line?: boolean })._is_line);
      const geometry = isLine
        ? { type: 'LineString' as const, coordinates: c.poly_wgs84 as unknown as [number, number][] }
        : c.poly_wgs84 && c.poly_wgs84.length >= 4
          ? { type: 'Polygon' as const, coordinates: [c.poly_wgs84] }
          : { type: 'Point' as const, coordinates: c.centroid_wgs84 };
      return {
        type: 'Feature' as const,
        properties: {
          id: c.candidate_id,
          location_id: 'preview',
          morph_class: c.kind,
          review_status: 'proposed' as const,
          origin: 'rule' as const,
          confidence: c.score,
          disclosure: 'public' as const,
        },
        geometry,
      };
    }),
  } as unknown as FeatureCollection;
}

interface PreviewPanelProps {
  view: { bounds: Bounds; zoom: number } | null;
  preview: PreviewResult | null;
  previewOpacity: number;
  selectedId: string | null;
  onPreview: (res: PreviewResult) => void;
  onClear: () => void;
  onOpacityChange: (v: number) => void;
  onSelect: (id: string | null) => void;
}

export default function PreviewPanel({
  view,
  preview,
  previewOpacity,
  selectedId,
  onPreview,
  onClear,
  onOpacityChange,
  onSelect,
}: PreviewPanelProps) {
  const [seed, setSeed] = useState(0);
  const [synthetic, setSynthetic] = useState(true);
  const qc = useQueryClient();

  const mut = useMutation({
    mutationFn: () => {
      if (!view) throw new Error('no view');
      const bbox: [number, number, number, number] = [...view.bounds];
      return api.preview(bbox, seed, synthetic);
    },
    onSuccess: (res) => {
      onPreview(res);
      qc.invalidateQueries({ queryKey: ['candidates'] });
      qc.invalidateQueries({ queryKey: ['layers'] });
    },
  });

  const km2 = view ? viewAreaKm2(view.bounds) : null;
  const tooBig = km2 !== null && km2 > 2.0;
  const zoomOk = !!view && view.zoom >= 13;
  const canRun = !!view && zoomOk && !tooBig && !mut.isPending;

  const errorMessage = (() => {
    if (!mut.error) return null;
    if (mut.error instanceof Error) return mut.error.message;
    return String(mut.error);
  })();

  return (
    <div className="area-card preview-card" style={{ borderLeft: '3px solid var(--accent)', paddingLeft: 10 }}>
      <h4 style={{ margin: '8px 0 4px' }}>Test detection here</h4>
      <p className="muted" style={{ margin: '4px 0 8px', fontSize: 13 }}>
        Runs rules + anomaly on exactly what you see. <strong>Viridis heatmap</strong> + <strong>white rectangles</strong> go on the map —
        same overlay the real pipeline uses. No download.
      </p>
      {!view ? (
        <p className="muted">Pan / zoom the map to a viewport (zoom 13+).</p>
      ) : (
        <div className="kv small">
          <div className="kv-row">
            <dt>View</dt>
            <dd>
              {view.bounds.map((v) => v.toFixed(4)).join(', ')} · {zoomOk ? `${formatKm2(km2 ?? 0)}` : 'zoom in'} · z
              {view.zoom.toFixed(1)}
            </dd>
          </div>
          <div className="kv-row" style={{ alignItems: 'center' }}>
            <dt>Seed</dt>
            <dd style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value) || 0)}
                style={{ width: 72 }}
                min={0}
                max={99999}
              />
              <label style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                <input type="checkbox" checked={synthetic} onChange={(e) => setSynthetic(e.target.checked)} /> synthetic
              </label>
              <span className="muted">off = reuse real DTM if present</span>
            </dd>
          </div>
        </div>
      )}
      <div className="row-gap" style={{ marginTop: 8 }}>
        <button className="primary" disabled={!canRun} onClick={() => mut.mutate()}>
          {mut.isPending ? 'Running…' : 'Test detection here'}
        </button>
        {preview && (
          <button onClick={onClear} disabled={mut.isPending}>
            Clear preview
          </button>
        )}
      </div>
      {!zoomOk && view && <p className="error">Zoom in to 13 for a preview (current {view.zoom.toFixed(1)}).</p>}
      {tooBig && <p className="error">Viewport too large ({formatKm2(km2 ?? 0)} — max 2 km², zoom in).</p>}
      {errorMessage && <p className="error">{errorMessage}</p>}

      {preview && (
        <div style={{ marginTop: 12 }}>
          <p className="small muted" style={{ margin: '6px 0' }}>
            {preview.id} · {preview.candidates.length} rectangles · seed {preview.seed} · {preview.elapsed_s}s ·{' '}
            {preview.synthetic ? 'synthetic fractal terrain' : 'real DTM'} — {preview.note}
          </p>

          <label className="field" style={{ margin: '6px 0' }}>
            Heatmap opacity: {previewOpacity.toFixed(2)}
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={previewOpacity}
              onChange={(e) => onOpacityChange(Number(e.target.value))}
            />
          </label>
          <div className="small" style={{ display: 'flex', gap: 8, alignItems: 'center', margin: '4px 0 8px' }}>
            <span
              style={{
                display: 'inline-block',
                width: 54,
                height: 12,
                borderRadius: 6,
                background: 'linear-gradient(90deg,#440154,#3b528b,#21918c,#5ec962,#fde725)',
                border: '1px solid var(--border)',
              }}
              aria-hidden
            />
            <span>viridis 0→1 · low heat transparent so hillshade shows</span>
          </div>

          <table className="table">
            <thead>
              <tr>
                <th>Score</th>
                <th>Kind</th>
                <th>Area / len</th>
                <th>Support</th>
              </tr>
            </thead>
            <tbody>
              {[...preview.candidates]
                .sort((a, b) => b.score - a.score)
                .map((c) => {
                  const isActive = c.candidate_id === selectedId;
                  const areaText = c.area_m2 ? `${c.area_m2.toFixed(0)} m²` : c.length_m ? `${c.length_m.toFixed(0)} m` : '—';
                  const supportText = c.low_support ? '⚠ low' : `${(c.support_fraction * 100).toFixed(0)}%`;
                  return (
                    <tr key={c.candidate_id} style={isActive ? { background: 'var(--surface)' } : undefined}>
                      <td>
                        <button className="link" onClick={() => onSelect(c.candidate_id)}>
                          {c.score.toFixed(2)}
                        </button>
                      </td>
                      <td>{c.kind.replace(/_/g, ' ')}</td>
                      <td>{areaText}</td>
                      <td>{supportText}</td>
                    </tr>
                  );
                })}
            </tbody>
          </table>

          {selectedId && <ChipGallery candidateId={selectedId} preview={preview} />}
          {!selectedId && <p className="small muted">Click a score to open its 96px + 256px chips.</p>}
        </div>
      )}
    </div>
  );
}

function ChipGallery({ candidateId, preview }: { candidateId: string; preview: PreviewResult }) {
  const c = preview.candidates.find((x) => x.candidate_id === candidateId);
  if (!c) return null;
  const kinds = ['hillshade', 'svf', 'lrm', 'slope', 'dtm'] as const;
  const sizes: (96 | 256)[] = [96, 256];
  return (
    <div className="chip-gallery" style={{ marginTop: 12 }}>
      <h5 style={{ margin: '6px 0' }}>
        Chips — {c.kind.replace(/_/g, ' ')} · {candidateId.slice(0, 8)} · {c.score.toFixed(2)}
      </h5>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
        {kinds.map((k) => (
          <div key={k} style={{ textAlign: 'center' }}>
            <div className="small muted" style={{ fontWeight: 600 }}>
              {k}
            </div>
            {sizes.map((sz) => {
              const primary = `/api/candidates/${candidateId}/chips/${k}_${sz}`;
              const fallback = `/api/chips/${preview.location_id}/${candidateId}/${k}_${sz}.png`;
              return (
                <div key={`${k}-${sz}`} style={{ margin: '6px 0' }}>
                  <div className="small muted">{sz}px</div>
                  <img
                    src={primary}
                    onError={(e) => {
                      const img = e.currentTarget;
                      if (img.src !== fallback) img.src = fallback;
                    }}
                    alt={`${k} ${sz}px chip`}
                    style={{
                      width: 96,
                      height: 96,
                      imageRendering: 'pixelated',
                      border: '1px solid var(--border)',
                      borderRadius: 4,
                      background: 'var(--surface)',
                    }}
                    loading="lazy"
                  />
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <p className="small muted" style={{ marginTop: 6 }}>
        Each chip is the raster centred on the white rectangle you see on the map. 96 px = 48 m (pits), 256 px = 128 m
        (platforms + neighbourhood).
      </p>
    </div>
  );
}
