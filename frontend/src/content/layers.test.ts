import { describe, expect, it } from 'vitest';
import {
  DEFAULT_LAYERS,
  FEATURE_GUIDE,
  GLOSSARY,
  KIND_ORDER,
  LAYER_CHOICES,
  LAYER_INFO,
  LIDAR_PRIMER,
  displayName,
  kindRank,
  layerHint,
  layerInfo,
  layersParam,
  metadataRows,
} from './layers';

const pipelineSources = import.meta.glob('../../../src/lidar_discovery/processing/pipeline.py', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/** The kinds the backend can produce, read from the Python source so the two cannot drift. */
function backendKinds(): string[] {
  const src = Object.values(pipelineSources)[0];
  if (!src) throw new Error('pipeline.py not found');
  const m = src.match(/ALL_KINDS:[^=]*=\s*\(([^)]*)\)/);
  if (!m) throw new Error('ALL_KINDS not found in pipeline.py');
  return [...m[1].matchAll(/"([a-z_]+)"/g)].map((x) => x[1]);
}

describe('layer descriptions', () => {
  it('has an entry for every kind the backend can produce', () => {
    const kinds = backendKinds();
    expect(kinds.length).toBeGreaterThanOrEqual(6);
    for (const k of kinds) expect(layerInfo(k), `missing LAYER_INFO.${k}`).not.toBeNull();
  });

  it('does not describe kinds the backend does not have', () => {
    expect(Object.keys(LAYER_INFO).sort()).toEqual([...backendKinds()].sort());
    expect([...KIND_ORDER].sort()).toEqual([...backendKinds()].sort());
  });

  it('is complete for each kind', () => {
    for (const info of Object.values(LAYER_INFO)) {
      expect(info.technical).toBe(info.kind);
      for (const text of [info.name, info.shortName, info.hint, info.what])
        expect(text.length).toBeGreaterThan(3);
      expect(info.computed.length).toBeGreaterThan(0);
      expect(info.read.bright && info.read.dark && info.read.ramp).toBeTruthy();
      expect(info.lookFor.length).toBeGreaterThan(0);
      expect(info.pitfalls.length).toBeGreaterThan(0);
      expect(info.tuning.join(' ')).toMatch(/fixed in the backend/);
    }
  });

  it('quotes the real default parameters', () => {
    const text = (k: keyof typeof LAYER_INFO) => LAYER_INFO[k].computed.join(' ');
    expect(text('dtm')).toMatch(/0\.5 m/);
    expect(text('svf')).toMatch(/16 directions/);
    expect(text('svf')).toMatch(/10 m radius/);
    expect(text('hillshade')).toMatch(/16 equally spaced/);
    expect(text('hillshade')).toMatch(/35 degrees/);
    expect(text('lrm')).toMatch(/sigma of 10 m/);
    expect(text('ground_density')).toMatch(/4 m/);
  });

  it('never uses the word "discovery" in UI text', () => {
    const all = JSON.stringify([LAYER_INFO, GLOSSARY, LIDAR_PRIMER, FEATURE_GUIDE, LAYER_CHOICES]);
    expect(all.toLowerCase()).not.toContain('discover');
  });

  it('gives human names and falls back for unknown kinds', () => {
    expect(displayName('dtm')).toBe('Bare-earth height (DTM)');
    expect(displayName('svf')).toBe('Sky-view factor');
    expect(displayName('ground_density')).toBe('Ground-point density');
    expect(displayName('brand_new_kind')).toBe('brand_new_kind');
    expect(layerHint('brand_new_kind')).toBe('');
    expect(layerInfo('brand_new_kind')).toBeNull();
  });

  it('explains the glossary terms the owner asked about', () => {
    const terms = GLOSSARY.map((g) => g.term).join(' | ');
    for (const t of [
      'DTM',
      'DSM',
      'SVF',
      'LRM',
      'Hillshade',
      'Point density',
      'Epoch',
      'EPSG:2180',
    ])
      expect(terms).toContain(t);
  });

  it('points every feature guide entry at a described layer', () => {
    for (const g of FEATURE_GUIDE) for (const k of g.layers) expect(layerInfo(k)).not.toBeNull();
  });
});

describe('layer choices', () => {
  it('lists every kind once, with the DTM required', () => {
    expect(LAYER_CHOICES.map((c) => c.kind).sort()).toEqual([...backendKinds()].sort());
    const dtm = LAYER_CHOICES.find((c) => c.kind === 'dtm');
    expect(dtm?.required).toBe(true);
  });

  it('defaults to DTM, shaded relief, sky-view factor and ground-point density', () => {
    expect([...DEFAULT_LAYERS].sort()).toEqual([
      'dtm',
      'ground_density',
      'hillshade',
      'lrm',
      'slope',
      'svf',
    ]);
  });

  it('builds the layers parameter in canonical order and always with the DTM', () => {
    expect(layersParam(['svf', 'hillshade'])).toBe('dtm,hillshade,svf');
    expect(layersParam([])).toBe('dtm');
    expect(layersParam(['ground_density', 'dtm', 'lrm', 'slope'])).toBe(
      'dtm,slope,lrm,ground_density',
    );
    expect(kindRank('dtm')).toBeLessThan(kindRank('svf'));
    expect(kindRank('mystery')).toBe(KIND_ORDER.length);
  });
});

describe('metadataRows', () => {
  it('shows epoch, source, resolution and provenance', () => {
    const rows = metadataRows({
      epoch: 2012,
      source_id: 'gugik-kron86',
      resolution_m: 0.5,
      provenance: {
        crs_xy: 'EPSG:2180',
        crs_h: 'PL-KRON86-NH',
        display_range: [412.345, 688.9],
        valid_fraction: 0.973,
        point_stats: { points_total: 5200000, points_ground: 1850000 },
        inputs: [{ file: 'a.laz' }],
        created_at: '2026-11-13T10:00:00+00:00',
      },
    });
    const get = (l: string) => rows.find((r) => r.label === l)?.value;
    expect(get('Epoch')).toBe('2012');
    expect(get('Source')).toBe('gugik-kron86');
    expect(get('Resolution')).toBe('0.5 m');
    expect(get('Grid')).toBe('EPSG:2180');
    expect(get('Colour range')).toBe('412.35 to 688.90');
    expect(get('Cells with data')).toBe('97 %');
    expect(get('Ground points used')).toContain('1,850,000');
    expect(get('Input sheets')).toBe('1');
  });

  it('copes with missing provenance', () => {
    const rows = metadataRows({ epoch: 2023, source_id: 's' });
    expect(rows.map((r) => r.label)).toEqual(['Epoch', 'Source']);
  });
});
