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

export default function LocationList({ locations, selectedId, onSelect, loading, error }: Props) {
  const [q, setQ] = useState('');
  const shown = useMemo(() => locations.filter((l) => matchesQuery(l, q)), [locations, q]);
  return (
    <div>
      <input
        type="search"
        placeholder="Search locations..."
        value={q}
        onChange={(e) => setQ(e.target.value)}
        aria-label="Search locations"
      />
      {loading && <p className="muted">Loading...</p>}
      {error && <p className="error">{error}</p>}
      <ul className="list">
        {shown.map((l) => (
          <li key={l.properties.id}>
            <button
              className={`list-item ${l.properties.id === selectedId ? 'active' : ''}`}
              onClick={() => onSelect(l.properties.id)}
            >
              <span>{locationName(l)}</span>
              <span className="row-gap">
                {!l.properties.has_products && <span className="badge">no layers</span>}
                {l.properties.disclosure && <DisclosureBadge value={l.properties.disclosure} />}
              </span>
            </button>
          </li>
        ))}
        {!loading && shown.length === 0 && <li className="muted">No matches.</li>}
      </ul>
    </div>
  );
}
