import { useMemo } from 'react';
import type { Layer, Location } from '../api/types';
import { LAYER_CHOICES, displayName } from '../content/layers';
import { locationAoi } from '../lib/geo';
import type { AreaFetchState } from './AreaFetch';

const ALL_KINDS = LAYER_CHOICES.map((c) => c.kind as string);

/** Which of the known layer kinds an epoch of an area does not have yet. */
export function missingKinds(present: Iterable<string>): string[] {
  const have = new Set(present);
  return ALL_KINDS.filter((k) => !have.has(k));
}

/**
 * For an area made with "Get data for this view": if some layers were not built (an earlier
 * version skipped Slope and Local relief by default), offer to build them. The stored data is
 * reused, so there is no new download.
 */
export default function MissingLayers({
  location,
  layers,
  fetch,
  onStarted,
}: {
  location: Location | undefined;
  layers: Layer[];
  fetch: AreaFetchState;
  onStarted: () => void;
}) {
  const groups = useMemo(() => {
    const by = new Map<string, { source_id: string; epoch: number; kinds: string[] }>();
    for (const l of layers) {
      const key = `${l.source_id}|${l.epoch}`;
      const g = by.get(key) ?? { source_id: l.source_id, epoch: l.epoch, kinds: [] };
      g.kinds.push(l.kind);
      by.set(key, g);
    }
    return [...by.values()]
      .map((g) => ({ ...g, missing: missingKinds(g.kinds) }))
      .filter((g) => g.missing.length > 0)
      .sort((a, b) => b.epoch - a.epoch);
  }, [layers]);

  if (!location || location.properties.kind !== 'area' || groups.length === 0) return null;
  const bounds = locationAoi(location);
  if (!bounds) return null;

  return (
    <div className="area-card" role="group" aria-label="Layers not built yet">
      <h3>Not built yet</h3>
      {groups.map((g) => (
        <div key={`${g.source_id}|${g.epoch}`}>
          <p>
            <strong>{g.epoch}</strong> <span className="muted">({g.source_id})</span>:{' '}
            {g.missing.map((k) => displayName(k)).join(', ')}
          </p>
          <button
            disabled={fetch.running || fetch.starting}
            onClick={() => {
              fetch.buildLayers({
                bbox: bounds,
                source_id: g.source_id,
                year: g.epoch,
                layers: ALL_KINDS,
              });
              onStarted();
            }}
          >
            Build the missing layers
          </button>
        </div>
      ))}
      <p className="muted small">
        Uses the LiDAR already on disk, so nothing is downloaded again. Takes about a minute.
      </p>
    </div>
  );
}
