import { describe, expect, it } from 'vitest';
import { defaultDisclosure, disclosureInfo, visibleInPublic } from './disclosure';

describe('disclosure', () => {
  it('maps levels to tones', () => {
    expect(disclosureInfo('public').tone).toBe('ok');
    expect(disclosureInfo('generalised').tone).toBe('warn');
    expect(disclosureInfo('restricted').tone).toBe('danger');
  });
  it('flags snapping and hiding per the contract', () => {
    expect(disclosureInfo('generalised').snappedInPublicMode).toBe(true);
    expect(visibleInPublic('restricted')).toBe(false);
    expect(visibleInPublic('public')).toBe(true);
  });
  it('fails safe for missing values', () => {
    expect(visibleInPublic(undefined)).toBe(false);
  });
  it('defaults cemeteries to restricted', () => {
    expect(defaultDisclosure('cemetery')).toBe('restricted');
    expect(defaultDisclosure('terrace')).toBe('generalised');
  });
});
