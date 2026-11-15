import type { Disclosure, ReviewStatus } from '../api/types';
import { disclosureInfo } from '../lib/disclosure';

export function DisclosureBadge({ value }: { value: Disclosure | undefined }) {
  const info = disclosureInfo(value);
  return (
    <span className={`badge badge-${info.tone}`} title={info.description}>
      {info.label}
    </span>
  );
}

export function StatusBadge({ value }: { value: ReviewStatus }) {
  return <span className={`badge status-${value}`}>{value.replace(/_/g, ' ')}</span>;
}
