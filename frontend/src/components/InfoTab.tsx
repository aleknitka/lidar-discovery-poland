import type { ReactNode } from 'react';
import type { Layer } from '../api/types';
import {
  FEATURE_GUIDE,
  GLOSSARY,
  KIND_ORDER,
  LIDAR_PRIMER,
  displayName,
  layerInfo,
  metadataRows,
  type Suitability,
} from '../content/layers';

interface Props {
  /** The kind being explained. */
  kind: string;
  onKind: (kind: string) => void;
  /** Layers of the selected place, for the live metadata block. */
  layers: Layer[];
  /** A specific layer to list first (from an (i) button). */
  layerId?: string | null;
}

const SUIT_TEXT: Record<Suitability, string> = {
  best: 'Best',
  good: 'Good',
  weak: 'Weak',
};
const SUIT_ICON: Record<Suitability, string> = { best: '★', good: '✓', weak: '–' };

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="info-section">
      <h4>{title}</h4>
      {children}
    </section>
  );
}

export default function InfoTab({ kind, onKind, layers, layerId }: Props) {
  const info = layerInfo(kind);
  const mine = layers
    .filter((l) => l.kind === kind)
    .sort((a, b) => (a.id === layerId ? -1 : b.id === layerId ? 1 : b.epoch - a.epoch));
  const kinds = [
    ...KIND_ORDER,
    ...layers.map((l) => l.kind).filter((k) => !KIND_ORDER.includes(k as never)),
  ].filter((k, i, a) => a.indexOf(k) === i);

  return (
    <div className="info-tab">
      <label className="field">
        Layer
        <select value={kind} onChange={(e) => onKind(e.target.value)}>
          {kinds.map((k) => (
            <option key={k} value={k}>
              {displayName(k)}
              {layerInfo(k) ? ` (${k})` : ''}
            </option>
          ))}
        </select>
      </label>

      {info ? (
        <article aria-labelledby="info-title">
          <h3 id="info-title">
            {info.name} <small className="tech">{info.technical}</small>
          </h3>
          <p className="lead">{info.what}</p>

          <Section title="How it is computed here">
            <ul>
              {info.computed.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          </Section>

          <Section title="How to read it">
            <dl className="kv">
              <dt>Bright</dt>
              <dd>{info.read.bright}</dd>
              <dt>Dark</dt>
              <dd>{info.read.dark}</dd>
              <dt>Colours</dt>
              <dd>{info.read.ramp}</dd>
            </dl>
          </Section>

          <Section title="What to look for">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Feature</th>
                  <th scope="col">This layer</th>
                </tr>
              </thead>
              <tbody>
                {info.lookFor.map((f) => (
                  <tr key={f.feature}>
                    <th scope="row">{f.feature}</th>
                    <td>
                      <span className={`suit suit-${f.suitability}`}>
                        <span aria-hidden="true">{SUIT_ICON[f.suitability]}</span>{' '}
                        {SUIT_TEXT[f.suitability]}
                      </span>{' '}
                      {f.note}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Section>

          <Section title="Pitfalls and false positives">
            <ul>
              {info.pitfalls.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          </Section>

          <Section title="Tuning">
            <ul>
              {info.tuning.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          </Section>
        </article>
      ) : (
        <p className="muted">
          No description has been written for the layer kind &ldquo;{kind}&rdquo; yet.
        </p>
      )}

      <Section title="This layer in your data">
        {mine.length === 0 ? (
          <p className="muted">
            The selected place has no {displayName(kind)} layer. Pick a place in the Places tab, or
            get data for the current view in the Data tab.
          </p>
        ) : (
          mine.map((l) => (
            <details key={l.id} open={l.id === layerId || mine.length === 1}>
              <summary>
                {l.epoch} · {l.source_id}
              </summary>
              <dl className="kv meta">
                {metadataRows(l).map((r) => (
                  <div key={r.label} className="kv-row">
                    <dt>{r.label}</dt>
                    <dd>{r.value}</dd>
                  </div>
                ))}
              </dl>
            </details>
          ))
        )}
      </Section>

      <hr />
      <h3>Which layer for which feature?</h3>
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Look for</th>
            <th scope="col">Use</th>
          </tr>
        </thead>
        <tbody>
          {FEATURE_GUIDE.map((g) => (
            <tr key={g.feature}>
              <th scope="row">{g.feature}</th>
              <td>
                {g.layers.map((k, i) => (
                  <span key={k}>
                    {i > 0 && ', '}
                    <button type="button" className="link" onClick={() => onKind(k)}>
                      {displayName(k)}
                    </button>
                  </span>
                ))}
                <br />
                <span className="muted">{g.why}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <details className="info-general">
        <summary>{LIDAR_PRIMER.title}</summary>
        {LIDAR_PRIMER.paragraphs.map((p) => (
          <p key={p}>{p}</p>
        ))}
      </details>

      <details className="info-general">
        <summary>Glossary</summary>
        <dl className="glossary">
          {GLOSSARY.map((g) => (
            <div key={g.term}>
              <dt>{g.term}</dt>
              <dd>{g.definition}</dd>
            </div>
          ))}
        </dl>
      </details>
    </div>
  );
}
