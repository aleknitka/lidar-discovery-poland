import { describe, expect, it } from 'vitest';
import { formatBytes, formatEta, formatSpeed } from './format';

describe('formatBytes', () => {
  it('scales units', () => {
    expect(formatBytes(0)).toBe('0 B');
    expect(formatBytes(999)).toBe('999 B');
    expect(formatBytes(1_500)).toBe('1.5 kB');
    expect(formatBytes(102_000_000)).toBe('102 MB');
    expect(formatBytes(1_234_000_000)).toBe('1.2 GB');
  });
  it('handles missing values', () => {
    expect(formatBytes(null)).toBe('-');
    expect(formatBytes(NaN)).toBe('-');
  });
});

describe('formatSpeed', () => {
  it('formats per second', () => {
    expect(formatSpeed(8_400_000)).toBe('8.4 MB/s');
    expect(formatSpeed(0)).toBe('-');
    expect(formatSpeed(null)).toBe('-');
  });
});

describe('formatEta', () => {
  it('formats durations', () => {
    expect(formatEta(2)).toBe('almost done');
    expect(formatEta(45)).toBe('~45 s left');
    expect(formatEta(180)).toBe('~3 min left');
    expect(formatEta(3900)).toBe('~1 h 05 min left');
  });
  it('is empty when unknown', () => {
    expect(formatEta(null)).toBe('');
    expect(formatEta(-1)).toBe('');
  });
});
