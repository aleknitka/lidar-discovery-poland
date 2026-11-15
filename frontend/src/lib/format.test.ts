import { describe, expect, it } from 'vitest';
import {
  formatBytes,
  formatDuration,
  formatEta,
  formatKm2,
  formatShare,
  formatSpeed,
  percentOf,
} from './format';

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

describe('formatDuration', () => {
  it('formats estimated processing times', () => {
    expect(formatDuration(0.2)).toBe('<1 s');
    expect(formatDuration(45)).toBe('45 s');
    expect(formatDuration(89)).toBe('89 s');
    expect(formatDuration(150)).toBe('3 min');
    expect(formatDuration(3900)).toBe('1 h 05 min');
    expect(formatDuration(null)).toBe('-');
    expect(formatDuration(-3)).toBe('-');
  });
});

describe('formatKm2 / formatShare / percentOf', () => {
  it('formats areas', () => {
    expect(formatKm2(1.8412)).toBe('1.84 km²');
    expect(formatKm2(12.34)).toBe('12.3 km²');
    expect(formatKm2(undefined)).toBe('-');
  });
  it('formats shares', () => {
    expect(formatShare(0.5)).toBe('50 %');
    expect(formatShare(0.001)).toBe('<1 %');
    expect(formatShare(0)).toBe('0 %');
    expect(formatShare(null)).toBe('-');
  });
  it('computes bar widths', () => {
    expect(percentOf(25, 100)).toBe(25);
    expect(percentOf(5, 0)).toBe(0);
    expect(percentOf(300, 100)).toBe(100);
    expect(percentOf(-1, 100)).toBe(0);
  });
});
