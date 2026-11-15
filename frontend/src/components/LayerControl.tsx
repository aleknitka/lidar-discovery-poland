import type { Layer } from '../api/types';

export interface LayerState {
  visible: boolean;
  opacity: number;
}
export type LayerStates = Record<string, LayerState>;

export interface CompareState {
  enabled: boolean;
  /** Layer id, or 'basemap' for OSM only. */
  leftId: string;
  rightId: string;
}

export const BASEMAP = 'basemap';

export const layerLabel = (l: Layer) => `${l.epoch} ${l.kind.toUpperCase()}`;

interface Props {
  layers: Layer[];
  states: LayerStates;
  onChange: (id: string, patch: Partial<LayerState>) => void;
  compare: CompareState;
  onCompareChange: (c: CompareState) => void;
}

function groupByEpoch(layers: Layer[]): [number, Layer[]][] {
  const m = new Map<number, Layer[]>();
  for (const l of layers) m.set(l.epoch, [...(m.get(l.epoch) ?? []), l]);
  return [...m.entries()]
    .sort((a, b) => b[0] - a[0])
    .map(([e, ls]) => [e, ls.sort((a, b) => a.kind.localeCompare(b.kind))]);
}

export default function LayerControl({
  layers,
  states,
  onChange,
  compare,
  onCompareChange,
}: Props) {
  if (layers.length === 0) {
    return <p className="muted">No derived layers for this location yet.</p>;
  }
  const options = (
    <>
      <option value={BASEMAP}>Basemap only</option>
      {layers.map((l) => (
        <option key={l.id} value={l.id}>
          {layerLabel(l)} ({l.source_id})
        </option>
      ))}
    </>
  );
  return (
    <div className="layer-control">
      {groupByEpoch(layers).map(([epoch, ls]) => (
        <fieldset key={epoch}>
          <legend>{epoch}</legend>
          {ls.map((l) => {
            const st = states[l.id] ?? { visible: false, opacity: 1 };
            return (
              <div className="layer-row" key={l.id}>
                <label>
                  <input
                    type="checkbox"
                    checked={st.visible}
                    disabled={compare.enabled}
                    onChange={(e) => onChange(l.id, { visible: e.target.checked })}
                  />{' '}
                  {l.kind.toUpperCase()}
                  {l.resolution_m ? <span className="muted"> {l.resolution_m} m</span> : null}
                </label>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={st.opacity}
                  aria-label={`Opacity ${layerLabel(l)}`}
                  onChange={(e) => onChange(l.id, { opacity: Number(e.target.value) })}
                />
              </div>
            );
          })}
        </fieldset>
      ))}
      <fieldset>
        <legend>Swipe compare</legend>
        <label>
          <input
            type="checkbox"
            checked={compare.enabled}
            onChange={(e) => onCompareChange({ ...compare, enabled: e.target.checked })}
          />{' '}
          Enable
        </label>
        {compare.enabled && (
          <>
            <label className="field">
              Left
              <select
                value={compare.leftId}
                onChange={(e) => onCompareChange({ ...compare, leftId: e.target.value })}
              >
                {options}
              </select>
            </label>
            <label className="field">
              Right
              <select
                value={compare.rightId}
                onChange={(e) => onCompareChange({ ...compare, rightId: e.target.value })}
              >
                {options}
              </select>
            </label>
          </>
        )}
      </fieldset>
    </div>
  );
}
