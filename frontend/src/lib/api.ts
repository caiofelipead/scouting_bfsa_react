import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 60_000, // 60s timeout — backend may need time to load Google Sheets on cold start
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Status codes that indicate cold start / transient backend issues
const RETRYABLE_STATUSES = new Set([502, 503, 504]);

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const config = err.config;
    if (!config) return Promise.reject(err);

    // Initialize retry state
    config._retryCount = config._retryCount || 0;

    // Retry on network errors OR 502/503/504 (cold start) up to 3 times
    const isNetworkError = !err.response;
    const isColdStartError = RETRYABLE_STATUSES.has(err.response?.status);

    if ((isNetworkError || isColdStartError) && config._retryCount < 6) {
      config._retryCount += 1;
      // Exponential backoff: 3s, 6s, 12s, 24s, 30s, 30s (total ~105s)
      const delay = Math.min(3000 * Math.pow(2, config._retryCount - 1), 30000);
      console.warn(
        `[api] ${isNetworkError ? 'Network error' : err.response?.status} on ${config.url} — retry ${config._retryCount}/6 in ${delay}ms`,
      );
      await new Promise((r) => setTimeout(r, delay));
      return api(config);
    }

    if (
      err.response?.status === 401 &&
      !config?.url?.includes('/auth/login') &&
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
 * Route external image URLs through the backend proxy to avoid CORS/hotlink 403 errors.
 * Proxies all absolute http(s) URLs; local/relative URLs pass through unchanged.
 */
export function proxyImageUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return `/api/image-proxy?url=${encodeURIComponent(url)}`;
  }
  // Encode path segments for local URLs (e.g. /api/team-logo/ldu quito → /api/team-logo/ldu%20quito)
  if (url.startsWith('/api/team-logo/')) {
    const teamName = url.slice('/api/team-logo/'.length);
    return `/api/team-logo/${encodeURIComponent(teamName)}`;
  }
  return url;
}

export default api;
