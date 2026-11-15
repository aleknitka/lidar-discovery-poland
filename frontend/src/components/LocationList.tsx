import { useMemo, useState } from 'react';
import type { Location } from '../api/types';
import { locationName } from '../lib/geo';
import { DisclosureBadge } from './Badges';

interface Props {
  locations: Location[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  loading?: boolean;
  error?: string | null;
}

export function matchesQuery(loc: Location, q: string): boolean {
  const needle = q.trim().toLowerCase();
  if (!needle) return true;
  const n = loc.properties.names;
  return [loc.properties.id, n.pl, n.uk, n.other].some((s) => s?.toLowerCase().includes(needle));
}

/** The "Places" tab: search, then two collapsed groups (seed villages, fetched areas). */
export default function LocationList({ locations, selectedId, onSelect, loading, error }: Props) {
  const [q, setQ] = useState('');
  const searching = q.trim() !== '';
  const shown = useMemo(() => locations.filter((l) => matchesQuery(l, q)), [locations, q]);
  const villages = shown.filter((l) => l.properties.kind !== 'area');
  const areas = shown.filter((l) => l.properties.kind === 'area');
  const row = (l: Location) => (
    <li key={l.properties.id}>
      <button
        className={`list-item ${l.properties.id === selectedId ? 'active' : ''}`}
        aria-current={l.properties.id === selectedId ? 'true' : undefined}
        onClick={() => onSelect(l.properties.id)}
      >
        <span>{locationName(l)}</span>
        <span className="row-gap">
          {!l.properties.has_products && <span className="badge">no layers</span>}
          {l.properties.disclosure && <DisclosureBadge value={l.properties.disclosure} />}
        </span>
      </button>
    </li>
  );
  return (
    <div>
      <input
        type="search"
        placeholder="Search places..."
        value={q}
        onChange={(e) => setQ(e.target.value)}
        aria-label="Search places"
      />
      <p className="muted small">
        Places are only a list: nothing is drawn on the map until you choose one.
      </p>
      {loading && <p className="muted">Loading...</p>}
      {error && <p className="error">{error}</p>}

      <details
        className="group"
        open={searching || areas.some((a) => a.properties.id === selectedId)}
      >
        <summary>Fetched areas ({areas.length})</summary>
        {areas.length === 0 ? (
          <p className="muted small">
            {searching
              ? 'No matches.'
              : 'None yet. Use "Get data for this view" on the map to create one.'}
          </p>
        ) : (
          <ul className="list" aria-label="Fetched areas">
            {areas.map(row)}
          </ul>
        )}
      </details>

      <details
        className="group"
        open={searching || villages.some((v) => v.properties.id === selectedId)}
      >
        <summary>Seed villages ({villages.length})</summary>
        <ul className="list" aria-label="Seed villages">
          {villages.map(row)}
          {!loading && villages.length === 0 && <li className="muted">No matches.</li>}
        </ul>
      </details>
    </div>
  );
}
