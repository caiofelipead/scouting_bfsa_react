import axios from 'axios';
import { apiUrl, VERCEL_PROXIED_PREFIXES } from '../config/api';

/**
 * Centralized HTTP client.
 *
 * Callers continue to use paths relative to /api (e.g. `api.get('/players')`).
 * The request interceptor below routes each request through `apiUrl()` so
 * analytics endpoints hit Render directly while asset endpoints keep using
 * the Vercel-proxied (edge-cached) relative paths.
 */
const api = axios.create({
  headers: { 'Content-Type': 'application/json' },
  timeout: 120_000, // 120s timeout — backend may need time to load data on cold start
});

/** Resolve a caller-supplied URL to its final absolute or proxied form. */
function resolveRequestUrl(url: string | undefined): string | undefined {
  if (!url) return url;
  if (/^(https?:|data:|blob:)/i.test(url)) return url;
  // Caller already wrote an /api/... path → forward as-is.
  if (url.startsWith('/api/')) return apiUrl(url);
  // Caller wrote a path relative to the legacy /api baseURL (e.g. '/players').
  const path = url.startsWith('/') ? url : `/${url}`;
  return apiUrl(`/api${path}`);
}

// Pre-warm: ping the backend to wake it, then prefetch config endpoints.
axios
  .get(apiUrl('/api/ping'), { timeout: 5_000 })
  .then(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      const headers = { Authorization: `Bearer ${token}` };
      axios.get(apiUrl('/api/config/positions'), { timeout: 10_000, headers }).catch(() => {});
      axios.get(apiUrl('/api/config/leagues'), { timeout: 10_000, headers }).catch(() => {});
    }
  })
  .catch(() => {});

api.interceptors.request.use((config) => {
  config.url = resolveRequestUrl(config.url);
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Status codes that indicate cold start / transient backend issues
const RETRYABLE_STATUSES = new Set([502, 503, 504]);

// Endpoints that should NOT be retried (fire-and-forget or non-critical)
const NO_RETRY_PATHS = ['/image-proxy'];

// Track cold-start state so UI can show a banner
let _coldStartActive = false;
let _coldStartListeners: Array<(active: boolean) => void> = [];

export function onColdStartChange(listener: (active: boolean) => void) {
  _coldStartListeners.push(listener);
  // Immediately notify current state
  listener(_coldStartActive);
  return () => {
    _coldStartListeners = _coldStartListeners.filter((l) => l !== listener);
  };
}

function _setColdStart(active: boolean) {
  if (_coldStartActive !== active) {
    _coldStartActive = active;
    _coldStartListeners.forEach((l) => l(active));
  }
}

api.interceptors.response.use(
  (res) => {
    // Successful response means backend is up — clear cold start
    _setColdStart(false);
    return res;
  },
  async (err) => {
    const config = err.config;
    if (!config) return Promise.reject(err);

    // Initialize retry state
    config._retryCount = config._retryCount || 0;

    const isNetworkError = !err.response;
    const isColdStartError = RETRYABLE_STATUSES.has(err.response?.status);
    const isRetryable = isNetworkError || isColdStartError;
    const shouldSkipRetry = NO_RETRY_PATHS.some((p) => config.url?.includes(p));

    if (isRetryable && !shouldSkipRetry && config._retryCount < 6) {
      config._retryCount += 1;
      // Exponential backoff: 3s, 6s, 12s, 24s, 30s, 30s (total ~105s)
      const delay = Math.min(3000 * Math.pow(2, config._retryCount - 1), 30000);

      // Signal cold start state on first retry
      if (config._retryCount === 1) {
        _setColdStart(true);
      }

      // Only log first and last retries to reduce console noise
      if (config._retryCount === 1 || config._retryCount >= 5) {
        const reason = isNetworkError ? 'Network error' : `HTTP ${err.response?.status}`;
        console.warn(
          `[api] ${reason} on ${config.url} — retry ${config._retryCount}/6 in ${delay}ms`,
        );
      }
      await new Promise((r) => setTimeout(r, delay));
      return api(config);
    }

    // Log final failure (all retries exhausted)
    if (isRetryable && config._retryCount >= 6) {
      console.error(
        `[api] All retries exhausted for ${config.url} — request failed`,
      );
      _setColdStart(false);
    }

    if (
      err.response?.status === 401 &&
      !config?.url?.includes('/auth/login') &&
      !config?.url?.includes('/auth/me') &&
      !config?.url?.includes('/image-proxy')
    ) {
      console.warn('[api] 401 received – clearing session', config?.url);
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.reload();
    }
    return Promise.reject(err);
  },
);

/**
 * Trusted CDN domains that browsers can load directly via <img> tags.
 * Server-side proxying these often fails (CDNs return 403 to non-browser requests),
 * while browsers load them without issues (no CORS needed for <img>).
 */
const DIRECT_IMAGE_DOMAINS = [
  'sortitoutsi.b-cdn.net',
  'sortitoutsidospaces.b-cdn.net',
  'logodetimes.com',
  'www.logodetimes.com',
  'upload.wikimedia.org',
  'images.fotmob.com',
];

/**
 * Route external image URLs through the backend proxy to avoid CORS/hotlink 403 errors.
 * Trusted CDN domains bypass the proxy (browsers load them directly).
 *
 * Image proxy / team-logo / player-face URLs are intentionally returned as
 * relative paths so they go through the Vercel rewrite + edge cache rather
 * than counting against Render bandwidth on every cache miss.
 */
export function proxyImageUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith('http://') || url.startsWith('https://')) {
    try {
      const hostname = new URL(url).hostname.toLowerCase();
      if (DIRECT_IMAGE_DOMAINS.some(d => hostname === d || hostname.endsWith('.' + d))) {
        return url; // Browser loads directly from CDN
      }
    } catch { /* invalid URL, fall through to proxy */ }
    return `/api/image-proxy?url=${encodeURIComponent(url)}`;
  }
  // Encode path segments for local URLs (e.g. /api/team-logo/ldu quito → /api/team-logo/ldu%20quito)
  if (url.startsWith('/api/team-logo/')) {
    const teamName = url.slice('/api/team-logo/'.length);
    return `/api/team-logo/${encodeURIComponent(teamName)}`;
  }
  // Encode path segments for local face URLs from graphics packs
  if (url.startsWith('/api/player-face/')) {
    const playerName = url.slice('/api/player-face/'.length);
    return `/api/player-face/${encodeURIComponent(playerName)}`;
  }
  return url;
}

/**
 * Returns true if an <img> loaded a 1×1 transparent fallback pixel from the
 * image proxy (meaning the upstream image failed).  Use in onLoad handlers:
 *
 *   onLoad={(e) => { if (isProxyFallback(e.target)) hide(); }}
 */
export function isProxyFallback(img: HTMLImageElement): boolean {
  return img.naturalWidth <= 1 && img.naturalHeight <= 1;
}

export { apiUrl, VERCEL_PROXIED_PREFIXES };
export default api;
