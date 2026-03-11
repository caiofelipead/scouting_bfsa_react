import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
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
  (err) => {
    if (
      err.response?.status === 401 &&
      !err.config?.url?.includes('/auth/login')
    ) {
      console.warn('[api] 401 received – clearing session', err.config?.url);
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      // Force reload to show login screen and clear stale React state
      window.location.reload();
    }
    return Promise.reject(err);
  }
);

export default api;
