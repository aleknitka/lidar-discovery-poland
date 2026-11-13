import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError, qs } from './client';

afterEach(() => vi.unstubAllGlobals());

describe('api client', () => {
  it('builds query strings, skipping empty values', () => {
    expect(qs({ location_id: 'a', review_status: undefined })).toBe('?location_id=a');
    expect(qs({})).toBe('');
  });

  it('requests candidates with filters', async () => {
    const f = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ type: 'FeatureCollection', features: [] })));
    vi.stubGlobal('fetch', f);
    await api.candidates({ location_id: 'x' });
    expect(f.mock.calls[0][0]).toBe('/api/candidates?location_id=x');
  });

  it('sends PATCH bodies as JSON', async () => {
    const f = vi.fn().mockResolvedValue(new Response('{}'));
    vi.stubGlobal('fetch', f);
    await api.updateCandidate('c-1', { properties: { review_status: 'accepted' } });
    const [url, init] = f.mock.calls[0];
    expect(url).toBe('/api/candidates/c-1');
    expect(init.method).toBe('PATCH');
    expect(JSON.parse(init.body)).toEqual({ properties: { review_status: 'accepted' } });
  });

  it('surfaces {detail} errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'nope' }), { status: 404 })),
    );
    await expect(api.location('zzz')).rejects.toMatchObject({ status: 404, message: 'nope' });
    await expect(api.location('zzz')).rejects.toBeInstanceOf(ApiError);
  });
});
