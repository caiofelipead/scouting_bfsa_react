import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000, // 30s timeout for slow cold starts
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const config = err.config;

    // Retry on network errors (not 4xx/5xx) up to 2 times
    if (!err.response && config && !config._retryCount) {
      config._retryCount = (config._retryCount || 0) + 1;
      if (config._retryCount <= 2) {
        const delay = config._retryCount * 1000;
        await new Promise((r) => setTimeout(r, delay));
        return api(config);
      }
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
  }
);

export default api;
