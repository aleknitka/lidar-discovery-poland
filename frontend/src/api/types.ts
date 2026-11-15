// Contract types mirroring docs/08-architecture-contract.md. Edit here when the contract changes.
import type { Feature, FeatureCollection, Geometry, MultiPolygon, Point, Polygon } from 'geojson';

export type Disclosure = 'public' | 'generalised' | 'restricted';

export type LayerKind =
  'dtm' | 'hillshade' | 'slope' | 'svf' | 'lrm' | 'ground_density' | (string & {});

export type MorphClass =
  | 'house_platform'
  | 'cellar_pit'
  | 'terrace'
  | 'holloway'
  | 'field_boundary'
  | 'cemetery'
  | 'church_site'
  | 'other';

export type Reality = 'unassessed' | 'artefact' | 'natural' | 'anthropogenic';
export type Origin = 'manual' | 'rule' | 'ml' | 'vlm';
export type ReviewStatus = 'proposed' | 'accepted' | 'rejected' | 'needs_second_opinion';

export const MORPH_CLASSES: MorphClass[] = [
  'house_platform',
  'cellar_pit',
  'terrace',
  'holloway',
  'field_boundary',
  'cemetery',
  'church_site',
  'other',
];
export const REALITIES: Reality[] = ['unassessed', 'artefact', 'natural', 'anthropogenic'];
export const REVIEW_STATUSES: ReviewStatus[] = [
  'proposed',
  'accepted',
  'rejected',
  'needs_second_opinion',
];
export const DISCLOSURES: Disclosure[] = ['public', 'generalised', 'restricted'];

export interface Provenance {
  provider?: string;
  ref?: string;
  fetched_at?: string;
  [k: string]: unknown;
}

export interface LocationProperties {
  id: string;
  names: { pl?: string; uk?: string; other?: string };
  depopulation?: { year?: number | null; cause?: string | null; source_url?: string | null } | null;
  has_products?: boolean;
  provenance?: Provenance[];
  disclosure?: Disclosure;
  polygon?: Polygon | MultiPolygon | null;
  kind?: 'village' | 'area';
}
export type LocationGeometry = Point | Polygon | MultiPolygon;
export type Location = Feature<LocationGeometry, LocationProperties>;
export type LocationCollection = FeatureCollection<LocationGeometry, LocationProperties>;

export interface Layer {
  id: string;
  location_id?: string;
  kind: LayerKind;
  epoch: number;
  source_id: string;
  resolution_m?: number;
  bounds: [number, number, number, number];
  tile_url: string;
  provenance?: Record<string, unknown>;
}

export interface Coverage {
  source_id: string;
  year: number;
  tiles: number;
  nominal_density?: string | number | null;
  bbox?: [number, number, number, number];
}

export interface DocumentationEntry {
  source: string;
  ref?: string;
  found: boolean;
}

export interface CandidateProperties {
  id: string;
  location_id?: string | null;
  morph_class: MorphClass;
  reality: Reality;
  confidence: number;
  dating_evidence?: string;
  documentation_status?: DocumentationEntry[];
  origin: Origin;
  model_version?: string | null;
  review_status: ReviewStatus;
  reviewer_notes?: string;
  disclosure: Disclosure;
  created_at?: string;
  updated_at?: string;
}
export type Candidate = Feature<Geometry, CandidateProperties>;
export type CandidateCollection = FeatureCollection<Geometry, CandidateProperties>;

export type CandidateInput = Feature<Geometry, Partial<CandidateProperties>>;
export interface CandidatePatch {
  geometry?: Geometry;
  properties?: Partial<CandidateProperties>;
}

export interface Source {
  id: string;
  name: string;
  description?: string;
  crs_h?: string | null;
}

export interface Health {
  status: string;
  version?: string;
  public_mode?: boolean;
}

export interface PreviewCandidateRaw {
  kind: string;
  score: number;
  area_m2?: number;
  length_m?: number;
  bbox_rc?: number[];
  poly_wgs84?: number[][];
  centroid_wgs84: [number, number];
  centroid_rc?: [number, number];
  low_support: boolean;
  support_fraction: number;
  candidate_id: string;
  chips: Record<string, string>;
}

export interface PreviewResult {
  id: string;
  location_id: string;
  bbox: [number, number, number, number];
  grid: { width: number; height: number; res: number };
  heatmap_layer_id: string;
  heatmap_tile_url: string;
  dtm_layer_id: string;
  candidates: PreviewCandidateRaw[];
  candidate_ids: string[];
  seed: number;
  synthetic: boolean;
  note: string;
  elapsed_s: number;
}
