import { describe, expect, it } from 'vitest';
import { PHOTO_TILES, isBasemapId, isColourMode, styledTileUrl } from './display';

describe('styledTileUrl', () => {
  const u = '/api/layers/a/tiles/{z}/{x}/{y}.png';
  it('leaves auto alone and adds the style otherwise', () => {
    expect(styledTileUrl(u, 'default')).toBe(u);
    expect(styledTileUrl(u, 'colour')).toBe(`${u}?style=colour`);
    expect(styledTileUrl(`${u}?shade=0.5`, 'bw')).toBe(`${u}?shade=0.5&style=bw`);
  });
  it('validates stored values', () => {
    expect(isColourMode('bw') && !isColourMode('neon')).toBe(true);
    expect(isBasemapId('photo') && !isBasemapId('sat')).toBe(true);
  });
  it('keeps the tile placeholders MapLibre needs', () => {
    for (const p of ['{z}', '{x}', '{y}']) expect(PHOTO_TILES).toContain(p);
  });
});
