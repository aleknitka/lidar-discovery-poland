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
