import type { Layer } from '../api/types';
import { displayName, kindRank, layerHint, layerInfo, shortName } from '../content/layers';
import { COLOUR_MODES, type BasemapId, type ColourMode } from '../lib/display';

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

/** Compare choices that are not LiDAR layers: the street map and the aerial photo. */
export const BASEMAP = 'basemap';
export const PHOTO = 'photo';

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
  colourMode: ColourMode;
  onColourMode: (m: ColourMode) => void;
  basemap: BasemapId;
  onBasemap: (b: BasemapId) => void;
  outlines: boolean;
  onOutlines: (on: boolean) => void;
}

function Segmented<T extends string>({
  label,
  value,
  options,
  onChange,
  disabled,
}: {
  label: string;
  value: T;
  options: { value: T; label: string; title?: string }[];
  onChange: (v: T) => void;
  disabled?: boolean;
}) {
  return (
    <div className="seg-row">
      <span className="seg-label">{label}</span>
      <div className="seg" role="group" aria-label={label}>
        {options.map((o) => (
          <button
            key={o.value}
            type="button"
            className={o.value === value ? 'active' : ''}
            aria-pressed={o.value === value}
            title={o.title}
            disabled={disabled}
            onClick={() => onChange(o.value)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
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
  colourMode,
  onColourMode,
  basemap,
  onBasemap,
  outlines,
  onOutlines,
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
      <option value={BASEMAP}>Street map</option>
      <option value={PHOTO}>Aerial photo</option>
      {layers.map((l) => (
        <option key={l.id} value={l.id}>
          {layerLabel(l)} ({l.source_id})
        </option>
      ))}
    </>
  );
  return (
    <div className="layer-control">
      <fieldset className="display-opts">
        <Segmented
          label="Colours"
          value={colourMode}
          options={COLOUR_MODES}
          onChange={onColourMode}
        />
        <Segmented
          label="Background"
          value={basemap}
          options={[
            { value: 'osm', label: 'Map', title: 'Street map (OpenStreetMap)' },
            { value: 'photo', label: 'Photo', title: 'Aerial photo (GUGiK orthophoto)' },
          ]}
          onChange={onBasemap}
          disabled={compare.enabled}
        />
        <label className="outline-toggle" title="Sheet edges and labels from the last download">
          <input
            type="checkbox"
            checked={outlines}
            onChange={(e) => onOutlines(e.target.checked)}
          />{' '}
          Show download outlines and labels
        </label>
      </fieldset>
      {groupByEpoch(layers).map(([epoch, ls]) => (
        <fieldset key={epoch}>
          <legend>
            {epoch} <span className="muted">{ls[0].source_id}</span>
          </legend>
          {ls.map((l) => {
            const st = states[l.id] ?? { visible: false, opacity: 1 };
            const known = layerInfo(l.kind);
            const hint = layerHint(l.kind) || 'No description yet.';
            const tip = `${hint}${l.resolution_m ? ` ${l.resolution_m} m grid.` : ''}`;
            const hintId = `hint-${l.id}`;
            return (
              <div className="layer-row" key={l.id} title={tip}>
                <label className="layer-name">
                  <input
                    type="checkbox"
                    checked={st.visible}
                    disabled={compare.enabled}
                    aria-describedby={hintId}
                    onChange={(e) => onChange(l.id, { visible: e.target.checked })}
                  />
                  <span>{known?.shortName ?? displayName(l.kind)}</span>
                </label>
                <span id={hintId} className="sr-only">
                  {tip}
                </span>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={st.opacity}
                  title="Opacity"
                  aria-label={`Opacity of ${layerLabel(l)}`}
                  onChange={(e) => onChange(l.id, { opacity: Number(e.target.value) })}
                />
                <button
                  type="button"
                  className="info-btn"
                  onClick={() => onInfo(l)}
                  aria-label={`About ${displayName(l.kind)}`}
                  title={`${displayName(l.kind)}: ${tip} Click for more.`}
                >
                  <span aria-hidden="true">i</span>
                </button>
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
          Compare two views with a slider
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
