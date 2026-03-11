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
      // Let React re-render instead of forcing a hard reload loop
    }
    return Promise.reject(err);
  }
);

export default api;
