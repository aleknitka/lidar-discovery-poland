// Types for "Get data for this view" (estimate + fetch jobs); see docs/08-architecture-contract.md.
import type { Polygon } from 'geojson';

export type BBox = [number, number, number, number]; // w, s, e, n

export interface EpochOption {
  source_id: string;
  year: number;
  tiles: number;
  nominal_density?: string;
  crs_h?: string | null;
}

export interface EstimateTile {
  godlo: string;
  name: string;
  size_bytes: number | null;
  cached: boolean;
  partial_bytes: number;
  nominal_density?: string | null;
  footprint: Polygon;
}

export interface AreaLimits {
  max_area_km2: number;
  max_bytes: number;
}

export interface AreaEstimate {
  bbox: BBox;
  area_km2: number;
  source_id?: string | null;
  year?: number | null;
  epochs?: EpochOption[];
  tiles: EstimateTile[];
  sheets?: number;
  bytes_total: number;
  bytes_cached?: number;
  bytes_to_download?: number;
  location_id?: string;
  processed?: boolean;
  limits: AreaLimits;
  over_limit?: 'area' | 'bytes';
}

export type JobState =
  'queued' | 'listing' | 'downloading' | 'processing' | 'done' | 'failed' | 'cancelled';
export const ACTIVE_JOB_STATES: JobState[] = ['queued', 'listing', 'downloading', 'processing'];

export interface JobTile {
  godlo: string;
  name: string;
  status: 'pending' | 'cached' | 'downloading' | 'done' | 'failed';
  bytes: number;
  size_bytes: number;
  footprint?: Polygon;
}

export interface Job {
  id: string;
  kind: string;
  params: { bbox: BBox; source_id?: string | null; year?: number | null };
  state: JobState;
  bytes_done: number;
  bytes_total: number;
  tiles_done: number;
  tiles_total: number;
  current_item: string | null;
  tiles: JobTile[];
  step: number;
  steps: number;
  step_name: string | null;
  speed_bps: number | null;
  eta_s: number | null;
  progress: number;
  message: string | null;
  error: string | null;
  location_id: string | null;
  created_at: string;
  updated_at: string;
  finished_at: string | null;
}

export interface FetchRequest {
  bbox: BBox;
  source_id?: string | null;
  year?: number | null;
}
