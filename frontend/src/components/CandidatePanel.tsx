import { useState } from 'react';
import type { Geometry, Position } from 'geojson';
import {
  DISCLOSURES,
  MORPH_CLASSES,
  REALITIES,
  REVIEW_STATUSES,
  type Candidate,
  type CandidateProperties,
  type Disclosure,
  type MorphClass,
} from '../api/types';
import { useCreateCandidate, useUpdateCandidate } from '../api/hooks';
import { defaultDisclosure, disclosureInfo } from '../lib/disclosure';
import { DisclosureBadge, StatusBadge } from './Badges';

export type DrawMode = 'none' | 'point' | 'polygon';
export interface DrawState {
  mode: DrawMode;
  vertices: Position[];
}

/** Geometry produced by the current drawing, or null when incomplete. */
export function drawnGeometry(d: DrawState): Geometry | null {
  if (d.mode === 'point' && d.vertices.length >= 1) {
    return { type: 'Point', coordinates: d.vertices[0] };
  }
  if (d.mode === 'polygon' && d.vertices.length >= 3) {
    return { type: 'Polygon', coordinates: [[...d.vertices, d.vertices[0]]] };
  }
  return null;
}

interface Props {
  selected: Candidate | null;
  locationId: string | null;
  draw: DrawState;
  onDrawMode: (m: DrawMode) => void;
  onUndoVertex: () => void;
  onDone: (savedId?: string) => void;
}

export default function CandidatePanel({
  selected,
  locationId,
  draw,
  onDrawMode,
  onUndoVertex,
  onDone,
}: Props) {
  const geometry = drawnGeometry(draw);
  const creating = !selected && geometry !== null;

  return (
    <div className="candidate-panel">
      {!selected && !creating && (
        <div>
          <p className="muted">
            Select a candidate on the map, or create one. Point: click once. Polygon: click vertices
            (at least 3), then finish.
          </p>
          <div className="row-gap">
            <button disabled={!locationId} onClick={() => onDrawMode('point')}>
              {draw.mode === 'point' ? 'Click the map...' : 'Add point'}
            </button>
            <button disabled={!locationId} onClick={() => onDrawMode('polygon')}>
              {draw.mode === 'polygon' ? `Vertices: ${draw.vertices.length}` : 'Draw polygon'}
            </button>
            {draw.mode !== 'none' && (
              <>
                {draw.mode === 'polygon' && draw.vertices.length > 0 && (
                  <button onClick={onUndoVertex}>Undo vertex</button>
                )}
                <button onClick={() => onDrawMode('none')}>Cancel</button>
              </>
            )}
          </div>
          {!locationId && <p className="muted">Select a location first.</p>}
        </div>
      )}
      {(selected || creating) && (
        <CandidateForm
          key={selected?.properties.id ?? 'new'}
          selected={selected}
          geometry={geometry}
          locationId={locationId}
          onDone={onDone}
        />
      )}
    </div>
  );
}

function CandidateForm({
  selected,
  geometry,
  locationId,
  onDone,
}: {
  selected: Candidate | null;
  geometry: Geometry | null;
  locationId: string | null;
  onDone: (savedId?: string) => void;
}) {
  const create = useCreateCandidate();
  const update = useUpdateCandidate();
  const p = selected?.properties;
  const [morph, setMorph] = useState<MorphClass>(p?.morph_class ?? 'house_platform');
  const [reality, setReality] = useState(p?.reality ?? 'unassessed');
  const [confidence, setConfidence] = useState(p?.confidence ?? 0.5);
  const [status, setStatus] = useState(p?.review_status ?? 'proposed');
  const [notes, setNotes] = useState(p?.reviewer_notes ?? '');
  const [dating, setDating] = useState(p?.dating_evidence ?? '');
  const [disclosure, setDisclosure] = useState<Disclosure>(
    p?.disclosure ?? defaultDisclosure('house_platform'),
  );
  const busy = create.isPending || update.isPending;
  const error = (create.error ?? update.error) as Error | null;

  const fields = (): Partial<CandidateProperties> => ({
    morph_class: morph,
    reality,
    confidence,
    review_status: status,
    reviewer_notes: notes,
    dating_evidence: dating,
    disclosure,
  });

  const save = async () => {
    if (selected) {
      const saved = await update.mutateAsync({
        id: selected.properties.id,
        patch: { properties: fields() },
      });
      onDone(saved.properties.id);
    } else if (geometry) {
      const saved = await create.mutateAsync({
        type: 'Feature',
        geometry,
        properties: { ...fields(), location_id: locationId, origin: 'manual' },
      });
      onDone(saved.properties.id);
    }
  };

  return (
    <form
      className="form"
      onSubmit={(e) => {
        e.preventDefault();
        void save().catch(() => undefined);
      }}
    >
      <h3>
        {selected ? 'Edit candidate' : 'New candidate'}
        {selected && (
          <>
            {' '}
            <StatusBadge value={selected.properties.review_status} />{' '}
            <DisclosureBadge value={selected.properties.disclosure} />
          </>
        )}
      </h3>
      {selected && (
        <p className="muted">
          {selected.properties.id} · origin {selected.properties.origin}
          {selected.properties.updated_at &&
            ` · updated ${selected.properties.updated_at.slice(0, 10)}`}
        </p>
      )}
      <label className="field">
        Morphology
        <select
          value={morph}
          onChange={(e) => {
            const v = e.target.value as MorphClass;
            setMorph(v);
            if (!selected) setDisclosure(defaultDisclosure(v));
          }}
        >
          {MORPH_CLASSES.map((m) => (
            <option key={m}>{m}</option>
          ))}
        </select>
      </label>
      <label className="field">
        Reality
        <select value={reality} onChange={(e) => setReality(e.target.value as typeof reality)}>
          {REALITIES.map((m) => (
            <option key={m}>{m}</option>
          ))}
        </select>
      </label>
      <label className="field">
        Confidence: {confidence.toFixed(2)}
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={confidence}
          onChange={(e) => setConfidence(Number(e.target.value))}
        />
      </label>
      <label className="field">
        Review status
        <select value={status} onChange={(e) => setStatus(e.target.value as typeof status)}>
          {REVIEW_STATUSES.map((m) => (
            <option key={m} value={m}>
              {m.replace(/_/g, ' ')}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        Disclosure
        <select value={disclosure} onChange={(e) => setDisclosure(e.target.value as Disclosure)}>
          {DISCLOSURES.map((m) => (
            <option key={m}>{m}</option>
          ))}
        </select>
        <small className="muted">{disclosureInfo(disclosure).description}</small>
      </label>
      <label className="field">
        Dating evidence
        <textarea rows={2} value={dating} onChange={(e) => setDating(e.target.value)} />
      </label>
      <label className="field">
        Reviewer notes
        <textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
      </label>
      {error && <p className="error">{error.message}</p>}
      <div className="row-gap">
        <button type="submit" className="primary" disabled={busy}>
          {busy ? 'Saving...' : selected ? 'Save changes' : 'Create candidate'}
        </button>
        <button type="button" onClick={() => onDone()}>
          {selected ? 'Close' : 'Cancel'}
        </button>
      </div>
    </form>
  );
}
