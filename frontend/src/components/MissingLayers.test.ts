import { describe, expect, it } from 'vitest';
import { missingKinds } from './MissingLayers';

describe('missingKinds', () => {
  it('lists what an older four-layer area lacks, in canonical order', () => {
    expect(missingKinds(['dtm', 'hillshade', 'svf', 'ground_density'])).toEqual(['slope', 'lrm']);
  });
  it('is empty for a complete area', () => {
    expect(missingKinds(['dtm', 'hillshade', 'slope', 'svf', 'lrm', 'ground_density'])).toEqual([]);
  });
});
