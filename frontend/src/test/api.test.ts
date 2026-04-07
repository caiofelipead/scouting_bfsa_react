import { describe, it, expect } from 'vitest';
import { proxyImageUrl, isProxyFallback } from '../lib/api';

describe('proxyImageUrl', () => {
  it('proxies absolute http URLs', () => {
    const url = 'http://example.com/photo.png';
    const result = proxyImageUrl(url);
    expect(result).toBe(`/api/image-proxy?url=${encodeURIComponent(url)}`);
  });

  it('proxies absolute https URLs', () => {
    const url = 'https://media.api-sports.io/football/players/123.png';
    const result = proxyImageUrl(url);
    expect(result).toContain('/api/image-proxy?url=');
    expect(result).toContain(encodeURIComponent(url));
  });

  it('passes through relative URLs unchanged', () => {
    expect(proxyImageUrl('/images/local.png')).toBe('/images/local.png');
  });

  it('returns null for null input', () => {
    expect(proxyImageUrl(null)).toBeNull();
  });

  it('returns null for undefined input', () => {
    expect(proxyImageUrl(undefined)).toBeNull();
  });

  it('returns null for empty string', () => {
    expect(proxyImageUrl('')).toBeNull();
  });

  it('encodes team-logo URLs with spaces', () => {
    expect(proxyImageUrl('/api/team-logo/ldu quito')).toBe('/api/team-logo/ldu%20quito');
  });

  it('passes through team-logo URLs without spaces', () => {
    expect(proxyImageUrl('/api/team-logo/millonarios')).toBe('/api/team-logo/millonarios');
  });
});

describe('isProxyFallback', () => {
  it('detects 1×1 transparent fallback pixel', () => {
    const img = { naturalWidth: 1, naturalHeight: 1 } as HTMLImageElement;
    expect(isProxyFallback(img)).toBe(true);
  });

  it('returns false for normal images', () => {
    const img = { naturalWidth: 100, naturalHeight: 100 } as HTMLImageElement;
    expect(isProxyFallback(img)).toBe(false);
  });

  it('detects 0×0 images as fallback', () => {
    const img = { naturalWidth: 0, naturalHeight: 0 } as HTMLImageElement;
    expect(isProxyFallback(img)).toBe(true);
  });
});
