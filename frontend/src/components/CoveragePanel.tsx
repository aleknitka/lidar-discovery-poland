import type { Coverage } from '../api/types';

export default function CoveragePanel({
  coverage,
  loading,
}: {
  coverage: Coverage[] | undefined;
  loading?: boolean;
}) {
  if (loading) return <p className="muted">Loading coverage...</p>;
  if (!coverage || coverage.length === 0) return <p className="muted">No coverage reported.</p>;
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Source</th>
          <th>Year</th>
          <th>Tiles</th>
          <th>Density</th>
        </tr>
      </thead>
      <tbody>
        {[...coverage]
          .sort((a, b) => b.year - a.year)
          .map((c) => (
            <tr key={`${c.source_id}-${c.year}`}>
              <td>{c.source_id}</td>
              <td>{c.year}</td>
              <td>{c.tiles}</td>
              <td>{c.nominal_density ?? 'n/a'}</td>
            </tr>
          ))}
      </tbody>
    </table>
  );
}
