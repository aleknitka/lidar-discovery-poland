import { describe, expect, it } from 'vitest';
import type { Polygon } from 'geojson';
import type { BBox, EstimateTile, JobTile } from '../api/areaTypes';
import { estimateOverlay, jobOverlay, rectPolygon, stateColour, statusView } from './areaStyle';
import { polygonShareInside } from './geo';

const sheet = (x: number, y: number): Polygon => rectPolygon([x, y, x + 0.01, y + 0.01]);
const view: BBox = [22.0, 49.0, 22.01, 49.01];

describe('statusView', () => {
  it('gives every state a text and a non-colour icon', () => {
    for (const s of ['cached', 'todo', 'pending', 'downloading', 'done', 'failed'] as const) {
      const v = statusView(s);
      expect(v.text.length).toBeGreaterThan(2);
      expect(v.icon.length).toBe(1);
    }
    expect(statusView('cached').text).toBe('cached');
    expect(statusView('todo').text).toBe('to download');
    expect(statusView('cached').icon).not.toBe(statusView('todo').icon);
  });

  it('draws cached and to-download in different colours', () => {
    expect(stateColour('cached')).not.toBe(stateColour('todo'));
    expect(stateColour('done')).toBe(stateColour('cached'));
    expect(stateColour('pending')).toBe(stateColour('todo'));
  });
});

describe('overlays', () => {
  const tiles: EstimateTile[] = [
    {
      godlo: 'A',
      name: 'a.laz',
      size_bytes: 100e6,
      cached: true,
      partial_bytes: 0,
      footprint: sheet(22, 49),
    },
    {
      godlo: 'B',
      name: 'b.laz',
      size_bytes: 200e6,
      cached: false,
      partial_bytes: 0,
      footprint: sheet(22.01, 49),
    },
  ];

  it('draws the view plus one feature per sheet with states', () => {
    const fc = estimateOverlay(view, tiles);
    expect(fc.features.map((f) => f.properties?.state)).toEqual(['viewport', 'cached', 'todo']);
    expect(fc.features[1].properties?.label).toContain('A');
    expect(fc.features[2].properties?.label).toContain('to download');
  });

  it('updates live from job tiles, with a percentage while downloading', () => {
    const jt: JobTile[] = [
      {
        godlo: 'A',
        name: 'a',
        status: 'cached',
        bytes: 1,
        size_bytes: 1,
        footprint: sheet(22, 49),
      },
      {
        godlo: 'B',
        name: 'b',
        status: 'downloading',
        bytes: 50,
        size_bytes: 200,
        footprint: sheet(22.01, 49),
      },
      { godlo: 'C', name: 'c', status: 'pending', bytes: 0, size_bytes: 1 },
    ];
    const fc = jobOverlay(view, jt);
    expect(fc.features.length).toBe(3); // C has no footprint
    expect(fc.features[2].properties?.state).toBe('downloading');
    expect(fc.features[2].properties?.label).toContain('25 %');
  });
});

describe('polygonShareInside', () => {
  it('is 1 when the sheet lies inside the view and 0 when disjoint', () => {
    expect(polygonShareInside(sheet(22.002, 49.002), [22, 49, 22.02, 49.02])).toBeCloseTo(1);
    expect(polygonShareInside(sheet(23, 50), view)).toBe(0);
  });
  it('gives the covered fraction for a partial overlap', () => {
    // view covers the west half of a 0.01 x 0.01 sheet
    expect(polygonShareInside(sheet(22, 49), [21.99, 48.99, 22.005, 49.02])).toBeCloseTo(0.5);
    // a quarter
    expect(polygonShareInside(sheet(22, 49), [22.005, 49.005, 22.02, 49.02])).toBeCloseTo(0.25);
  });
  it('handles a view that is inside a big sheet', () => {
    expect(polygonShareInside(sheet(22, 49), [22.002, 49.002, 22.004, 49.004])).toBeCloseTo(0.04);
  });
});
