import type {
  Candidate,
  CandidateCollection,
  CandidateInput,
  CandidatePatch,
  Coverage,
  Health,
  Layer,
  Location,
  LocationCollection,
  Source,
} from './types';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

const BASE = '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (init?.body) headers['Content-Type'] = 'application/json';
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body && typeof body.detail === 'string') detail = body.detail;
      else if (body?.detail) detail = JSON.stringify(body.detail);
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail || `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export function qs(params: Record<string, string | undefined>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v) sp.set(k, v);
  const s = sp.toString();
  return s ? `?${s}` : '';
}

export const api = {
  health: () => request<Health>('/health'),
  sources: () => request<Source[]>('/sources'),
  locations: () => request<LocationCollection>('/locations'),
  location: (id: string) => request<Location>(`/locations/${encodeURIComponent(id)}`),
  coverage: (id: string) => request<Coverage[]>(`/locations/${encodeURIComponent(id)}/coverage`),
  layers: (id: string) => request<Layer[]>(`/locations/${encodeURIComponent(id)}/layers`),
  candidates: (filter: { location_id?: string; review_status?: string } = {}) =>
    request<CandidateCollection>(`/candidates${qs(filter)}`),
  createCandidate: (body: CandidateInput) =>
    request<Candidate>('/candidates', { method: 'POST', body: JSON.stringify(body) }),
  updateCandidate: (id: string, patch: CandidatePatch) =>
    request<Candidate>(`/candidates/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),
};
