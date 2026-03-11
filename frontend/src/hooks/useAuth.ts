import { useState, useCallback, useEffect } from 'react';
import api from '../lib/api';
import type { User, TokenResponse } from '../types/api';

export function useAuth() {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = !!user && !!localStorage.getItem('access_token');

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<TokenResponse>('/auth/login', { email, password });
      const token = res.data.access_token;
      console.log('[useAuth] login success, saving token');
      localStorage.setItem('access_token', token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setUser(res.data.user);
      return true;
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Erro ao fazer login';
      console.error('[useAuth] login failed', msg);
      setError(msg);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token && !user) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      api.get('/auth/me')
        .then((res) => {
          setUser(res.data);
          localStorage.setItem('user', JSON.stringify(res.data));
        })
        .catch(() => {
          console.warn('[useAuth] /auth/me failed – clearing session');
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
          delete api.defaults.headers.common['Authorization'];
          setUser(null);
        });
    }
  }, []);

  return { user, isAuthenticated, loading, error, login, logout };
}
