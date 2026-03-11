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

    if ((isNetworkError || isColdStartError) && config._retryCount < 3) {
      config._retryCount += 1;
      const delay = config._retryCount * 2000; // 2s, 4s, 6s
      console.warn(
        `[api] ${isNetworkError ? 'Network error' : err.response?.status} on ${config.url} — retry ${config._retryCount}/3 in ${delay}ms`,
      );
      await new Promise((r) => setTimeout(r, delay));
      return api(config);
    }

    if (
      err.response?.status === 401 &&
      !config?.url?.includes('/auth/login')
    ) {
      console.warn('[api] 401 received – clearing session', config?.url);
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.reload();
    }
    return Promise.reject(err);
  },
);

export default api;
