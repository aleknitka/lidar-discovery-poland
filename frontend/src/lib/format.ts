/** Human-readable sizes, speeds and durations for the fetch progress panel. */

export function formatBytes(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n) || n < 0) return '-';
  if (n < 1e3) return `${Math.round(n)} B`;
  const units = ['kB', 'MB', 'GB', 'TB'];
  let v = n;
  let i = -1;
  do {
    v /= 1000;
    i++;
  } while (v >= 1000 && i < units.length - 1);
  return `${v >= 100 ? v.toFixed(0) : v.toFixed(1).replace(/\.0$/, '')} ${units[i]}`;
}

export function formatSpeed(bps: number | null | undefined): string {
  if (bps == null || !Number.isFinite(bps) || bps <= 0) return '-';
  return `${formatBytes(bps)}/s`;
}

/** "~3 min left", "~45 s left", "~1 h 05 min left"; empty string when unknown. */
export function formatEta(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds) || seconds < 0) return '';
  const s = Math.round(seconds);
  if (s < 5) return 'almost done';
  if (s < 60) return `~${s} s left`;
  if (s < 3600) return `~${Math.round(s / 60)} min left`;
  const h = Math.floor(s / 3600);
  const m = Math.round((s % 3600) / 60);
  return `~${h} h ${String(m).padStart(2, '0')} min left`;
}

/** "45 s", "3 min", "1 h 05 min"; "-" when unknown. For estimated processing times. */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds) || seconds < 0) return '-';
  const s = Math.round(seconds);
  if (s < 1) return '<1 s';
  if (s < 90) return `${s} s`;
  if (s < 3600) return `${Math.round(s / 60)} min`;
  const h = Math.floor(s / 3600);
  const m = Math.round((s % 3600) / 60);
  return `${h} h ${String(m).padStart(2, '0')} min`;
}

/** "1.84 km²"; two decimals below 10 km², one above. */
export function formatKm2(km2: number | null | undefined): string {
  if (km2 == null || !Number.isFinite(km2) || km2 < 0) return '-';
  return `${km2 >= 10 ? km2.toFixed(1) : km2.toFixed(2)} km²`;
}

/** A 0..1 share as a whole percent, "<1 %" for tiny non-zero shares. */
export function formatShare(share: number | null | undefined): string {
  if (share == null || !Number.isFinite(share) || share < 0) return '-';
  if (share > 0 && share < 0.005) return '<1 %';
  return `${Math.round(share * 100)} %`;
}

/** Part of a total as a percentage clamped to 0..100 (for bar widths); 0 when the total is 0. */
export function percentOf(part: number, total: number): number {
  if (!(total > 0) || !Number.isFinite(part)) return 0;
  return Math.max(0, Math.min(100, (100 * part) / total));
}
