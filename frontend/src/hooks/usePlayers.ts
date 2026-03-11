import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../lib/api';
import type {
  PlayerSummary,
  PlayerProfile,
  RankingResponse,
  SimilarityResponse,
  PlayersQueryParams,
  RankingsQueryParams,
  SimilarityQueryParams,
} from '../types/api';

// ── Query key factories (consistent keys prevent cache resets on tab switch) ──

export const playerKeys = {
  all: ['players'] as const,
  list: (params: PlayersQueryParams) => ['players', 'list', params] as const,
  profile: (displayName: string) => ['players', 'profile', displayName] as const,
  radar: (displayName: string) => ['players', 'radar', displayName] as const,
};

export const rankingKeys = {
  all: ['rankings'] as const,
  list: (params: RankingsQueryParams) => ['rankings', 'list', params] as const,
};

export const configKeys = {
  positions: ['config', 'positions'] as const,
  leagues: ['config', 'leagues'] as const,
};

// ── Shared staleTime for Wyscout/SkillCorner data (10 minutes) ──
// Prevents cache invalidation when switching tabs via AnimatePresence

const STALE_TIME = 10 * 60 * 1000;

// ── Config hooks ──

export function usePositions() {
  return useQuery({
    queryKey: configKeys.positions,
    queryFn: async () => {
      const res = await api.get('/config/positions');
      // Backend returns { positions: [...], position_map: {...}, indices: {...}, ... }
      const positions = res.data?.positions;
      if (!Array.isArray(positions)) {
        console.warn('[usePositions] Unexpected response:', res.data);
        return [] as string[];
      }
      return positions as string[];
    },
    staleTime: STALE_TIME,
  });
}

export function useLeagues() {
  return useQuery({
    queryKey: configKeys.leagues,
    queryFn: async () => {
      const res = await api.get('/config/leagues');
      // Backend returns { leagues: [...], league_logos: {...} }
      const leagues = res.data?.leagues;
      if (!Array.isArray(leagues)) {
        console.warn('[useLeagues] Unexpected response:', res.data);
        return [] as string[];
      }
      return leagues as string[];
    },
    staleTime: STALE_TIME,
  });
}

// ── Players list ──

export function usePlayers(params: PlayersQueryParams) {
  return useQuery({
    queryKey: playerKeys.list(params),
    queryFn: async () => {
      const res = await api.get('/players', { params });
      return res.data as { total: number; players: PlayerSummary[] };
    },
    staleTime: STALE_TIME,
    placeholderData: (prev) => prev,
  });
}

// ── Player profile ──

export function usePlayerProfile(displayName: string | null) {
  return useQuery({
    queryKey: playerKeys.profile(displayName ?? ''),
    queryFn: async () => {
      const res = await api.get(`/players/${encodeURIComponent(displayName!)}/profile`);
      return res.data as PlayerProfile;
    },
    enabled: !!displayName,
    staleTime: STALE_TIME,
  });
}

// ── Radar data ──

export function useRadarData(displayName: string | null) {
  return useQuery({
    queryKey: playerKeys.radar(displayName ?? ''),
    queryFn: async () => {
      const res = await api.get(`/players/${encodeURIComponent(displayName!)}/radar`);
      return {
        labels: (res.data?.labels ?? []) as string[],
        values: (res.data?.values ?? []) as number[],
      };
    },
    enabled: !!displayName,
    staleTime: STALE_TIME,
  });
}

// ── Rankings ──

export function useRankings(params: RankingsQueryParams) {
  return useQuery({
    queryKey: rankingKeys.list(params),
    queryFn: async () => {
      const res = await api.post('/rankings', {
        position: params.position,
        min_minutes: params.min_minutes ?? 0,
        league: params.league || null,
        top_n: params.top_n ?? 50,
      });
      return res.data as RankingResponse;
    },
    staleTime: STALE_TIME,
  });
}

// ── Similarity (mutation — triggered on-demand) ──

export function useSimilarity() {
  return useMutation({
    mutationFn: async (params: SimilarityQueryParams) => {
      const res = await api.post('/similarity', {
        player_name: params.player_name,
        position: params.position,
        top_n: params.top_n ?? 20,
        min_minutes: params.min_minutes ?? 500,
      });
      return res.data as SimilarityResponse;
    },
  });
}
