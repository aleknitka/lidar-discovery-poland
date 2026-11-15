import type { Layer } from '../api/types';
import { displayName, kindRank, layerHint, layerInfo, shortName } from '../content/layers';

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

/** Short label for map titles, compare menus and aria text: "2012 Sky-view factor". */
export const layerLabel = (l: Layer) => `${l.epoch} ${shortName(l.kind)}`;

interface Props {
  layers: Layer[];
  states: LayerStates;
  onChange: (id: string, patch: Partial<LayerState>) => void;
  compare: CompareState;
  onCompareChange: (c: CompareState) => void;
  /** Open the Info tab for this layer. */
  onInfo: (layer: Layer) => void;
}

function groupByEpoch(layers: Layer[]): [number, Layer[]][] {
  const m = new Map<number, Layer[]>();
  for (const l of layers) m.set(l.epoch, [...(m.get(l.epoch) ?? []), l]);
  return [...m.entries()]
    .sort((a, b) => b[0] - a[0])
    .map(([e, ls]) => [e, ls.sort((a, b) => kindRank(a.kind) - kindRank(b.kind))]);
}

export default function LayerControl({
  layers,
  states,
  onChange,
  compare,
  onCompareChange,
  onInfo,
}: Props) {
  if (layers.length === 0) {
    return (
      <p className="muted">
        No layers for this place yet. Open the Data tab to get LiDAR for the current map view.
      </p>
    );
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
          <legend>
            {epoch} <span className="muted">{ls[0].source_id}</span>
          </legend>
          {ls.map((l) => {
            const st = states[l.id] ?? { visible: false, opacity: 1 };
            const known = layerInfo(l.kind);
            const hintId = `hint-${l.id}`;
            return (
              <div className="layer-row" key={l.id}>
                <div className="layer-main">
                  <label className="layer-name">
                    <input
                      type="checkbox"
                      checked={st.visible}
                      disabled={compare.enabled}
                      aria-describedby={hintId}
                      onChange={(e) => onChange(l.id, { visible: e.target.checked })}
                    />
                    <span>
                      {displayName(l.kind)}{' '}
                      {known && <small className="tech">{known.technical}</small>}
                    </span>
                  </label>
                  <button
                    type="button"
                    className="info-btn"
                    onClick={() => onInfo(l)}
                    aria-label={`About ${displayName(l.kind)}`}
                    title={`What is ${displayName(l.kind)}?`}
                  >
                    <span aria-hidden="true">i</span>
                  </button>
                </div>
                <p id={hintId} className="layer-hint">
                  {layerHint(l.kind) || 'No description yet.'}
                  {l.resolution_m ? ` ${l.resolution_m} m grid.` : ''}
                </p>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={st.opacity}
                  aria-label={`Opacity of ${layerLabel(l)}`}
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
          Compare two layers side by side
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
