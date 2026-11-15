import { describe, expect, it } from 'vitest';
import { viewAreaKm2 } from './geo';

const VIEW_AREA_HINT_KM2 = 6;

describe('viewAreaKm2', () => {
  it('is about 1 km2 for a 1 km square near Caryńskie', () => {
    const lat = 49.17;
    const dLat = 1 / 110.57;
    const dLon = 1 / (111.32 * Math.cos((lat * Math.PI) / 180));
    const km2 = viewAreaKm2([22.6, lat, 22.6 + dLon, lat + dLat]);
    expect(km2).toBeGreaterThan(0.95);
    expect(km2).toBeLessThan(1.05);
  });

  it('puts a typical zoom-13 browser window far over the fetch limit', () => {
    // the whole-Bieszczady start view is hundreds of km2
    expect(viewAreaKm2([22.55, 49.12, 22.7, 49.22])).toBeGreaterThan(VIEW_AREA_HINT_KM2 * 10);
  });
});
