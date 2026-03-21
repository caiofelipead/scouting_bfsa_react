import { describe, it, expect } from 'vitest';
import { proxyImageUrl } from '../lib/api';

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
});
