import { useMemo, useState } from 'react';
import { useCandidates, useLocations } from '../api/hooks';
import MapView from '../components/MapView';
import { DisclosureBadge, StatusBadge } from '../components/Badges';
import { locationName } from '../lib/geo';
import { visibleInPublic } from '../lib/disclosure';

export default function Catalog() {
  const locations = useLocations();
  const candidates = useCandidates({});
  const [selected, setSelected] = useState<string | null>(null);

  // Read-only view. Until the API's public mode is wired in, restricted items are also hidden here.
  const publicCandidates = useMemo(
    () =>
      candidates.data
        ? {
            ...candidates.data,
            features: candidates.data.features.filter((c) =>
              visibleInPublic(c.properties.disclosure),
            ),
          }
        : null,
    [candidates.data],
  );

  return (
    <div className="catalog">
      <div className="wip-banner" role="note">
        Work in progress: placeholder for the public catalogue. Read-only; positions will be
        generalised according to each item&apos;s disclosure level.
      </div>
      <div className="catalog-body">
        <div className="catalog-map">
          <MapView
            bounds={[22.4, 49.05, 22.8, 49.25]}
            candidates={publicCandidates}
            selectedId={selected}
            onClick={(_, id) => setSelected(id)}
          />
        </div>
        <div className="catalog-lists">
          <h2>Locations</h2>
          <ul className="list">
            {locations.data?.features.map((l) => (
              <li key={l.properties.id} className="list-row">
                <span>{locationName(l)}</span>
                <DisclosureBadge value={l.properties.disclosure} />
              </li>
            ))}
          </ul>
          <h2>Candidates</h2>
          <ul className="list">
            {publicCandidates?.features.map((c) => (
              <li key={c.properties.id}>
                <button
                  className={`list-item ${c.properties.id === selected ? 'active' : ''}`}
                  onClick={() => setSelected(c.properties.id)}
                >
                  <span>{c.properties.morph_class.replace(/_/g, ' ')}</span>
                  <span className="row-gap">
                    <StatusBadge value={c.properties.review_status} />
                    <DisclosureBadge value={c.properties.disclosure} />
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
