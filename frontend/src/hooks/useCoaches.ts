import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import type {
  Coach,
  CoachListResponse,
  CoachHistoryResponse,
  CoachCompareResponse,
  CoachRankingResponse,
  CoachFilters,
  CoachRankingWeights,
} from '../types/coaches';

// ── Query key factories ──

export const coachKeys = {
  all: ['coaches'] as const,
  list: (filters: CoachFilters) => ['coaches', 'list', filters] as const,
  detail: (id: string) => ['coaches', 'detail', id] as const,
  history: (id: string) => ['coaches', 'history', id] as const,
  compare: (ids: string[]) => ['coaches', 'compare', ids] as const,
  ranking: (weights: CoachRankingWeights, filters: CoachFilters) =>
    ['coaches', 'ranking', weights, filters] as const,
};

const STALE_TIME = 10 * 60 * 1000;   // 10 minutes
const GC_TIME = 30 * 60 * 1000;      // 30 minutes

// ── List all coaches ──

export function useCoaches(filters: CoachFilters = {}) {
  return useQuery({
    queryKey: coachKeys.list(filters),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (filters.status) params.status = filters.status;
      if (filters.nacionalidade) params.nacionalidade = filters.nacionalidade;
      if (filters.licenca) params.licenca = filters.licenca;
      if (filters.formacao) params.formacao = filters.formacao;
      const res = await api.get('/coaches', { params });
      return res.data as CoachListResponse;
    },
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    placeholderData: (prev) => prev,
  });
}

// ── Single coach profile ──

export function useCoachProfile(coachId: string | null) {
  return useQuery({
    queryKey: coachKeys.detail(coachId ?? ''),
    queryFn: async () => {
      const res = await api.get(`/coaches/${encodeURIComponent(coachId!)}`);
      return res.data as Coach;
    },
    enabled: !!coachId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Coach history ──

export function useCoachHistory(coachId: string | null) {
  return useQuery({
    queryKey: coachKeys.history(coachId ?? ''),
    queryFn: async () => {
      const res = await api.get(`/coaches/${encodeURIComponent(coachId!)}/history`);
      return res.data as CoachHistoryResponse;
    },
    enabled: !!coachId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Compare coaches ──

export function useCoachCompare(ids: string[]) {
  return useQuery({
    queryKey: coachKeys.compare(ids),
    queryFn: async () => {
      const res = await api.get('/coaches/compare', {
        params: { ids: ids.join(',') },
      });
      return res.data as CoachCompareResponse;
    },
    enabled: ids.length >= 2,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Coach ranking ──

export function useCoachRanking(
  weights: CoachRankingWeights = {},
  filters: CoachFilters = {},
) {
  return useQuery({
    queryKey: coachKeys.ranking(weights, filters),
    queryFn: async () => {
      const params: Record<string, string | number> = {};
      if (weights.w_aproveitamento !== undefined) params.w_aproveitamento = weights.w_aproveitamento;
      if (weights.w_tatico !== undefined) params.w_tatico = weights.w_tatico;
      if (weights.w_gestao !== undefined) params.w_gestao = weights.w_gestao;
      if (weights.w_uso_base !== undefined) params.w_uso_base = weights.w_uso_base;
      if (weights.w_estabilidade !== undefined) params.w_estabilidade = weights.w_estabilidade;
      if (weights.w_flexibilidade !== undefined) params.w_flexibilidade = weights.w_flexibilidade;
      if (filters.status) params.status = filters.status;
      if (filters.nacionalidade) params.nacionalidade = filters.nacionalidade;
      if (filters.licenca) params.licenca = filters.licenca;
      if (filters.formacao) params.formacao = filters.formacao;
      const res = await api.get('/coaches/ranking', { params });
      return res.data as CoachRankingResponse;
    },
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    placeholderData: (prev) => prev,
  });
}
