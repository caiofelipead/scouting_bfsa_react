import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../lib/api';
import type {
  VAEPPipelineResponse,
  VAEPRatingsResponse,
  VAEPPlayerDetail,
  VAEPComparisonResponse,
  PlayeRankRankingsResponse,
} from '../types/vaep';

const STALE_TIME = 10 * 60 * 1000;
const GC_TIME = 30 * 60 * 1000;

export const vaepKeys = {
  ratings: (params: Record<string, unknown>) => ['vaep', 'ratings', params] as const,
  player: (name: string) => ['vaep', 'player', name] as const,
  compare: (names: string[]) => ['vaep', 'compare', names] as const,
  playerank: (params: Record<string, unknown>) => ['playerank', 'rankings', params] as const,
};

export function useRunVaepPipeline() {
  return useMutation({
    mutationFn: async (params?: { season?: string; competition_id?: number }) => {
      const res = await api.post('/vaep/run-pipeline', params ?? {});
      return res.data as VAEPPipelineResponse;
    },
  });
}

export function useVaepRatings(params: {
  position?: string;
  min_minutes?: number;
  season?: string;
  league?: string;
}) {
  return useQuery({
    queryKey: vaepKeys.ratings(params),
    queryFn: async () => {
      const res = await api.get('/vaep/ratings', { params });
      return res.data as VAEPRatingsResponse;
    },
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useVaepPlayer(playerName: string, season?: string) {
  return useQuery({
    queryKey: vaepKeys.player(playerName),
    queryFn: async () => {
      const res = await api.get(`/vaep/player/${encodeURIComponent(playerName)}`, {
        params: { season },
      });
      return res.data as VAEPPlayerDetail;
    },
    enabled: !!playerName,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useVaepComparison(playerNames: string[], season?: string) {
  return useQuery({
    queryKey: vaepKeys.compare(playerNames),
    queryFn: async () => {
      const params = new URLSearchParams();
      playerNames.forEach((n) => params.append('player_names', n));
      if (season) params.append('season', season);
      const res = await api.get(`/vaep/compare?${params.toString()}`);
      return res.data as VAEPComparisonResponse;
    },
    enabled: playerNames.length >= 2,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function usePlayerankRankings(params: {
  role_cluster?: string;
  dimension?: string;
  league?: string;
  season?: string;
}) {
  return useQuery({
    queryKey: vaepKeys.playerank(params),
    queryFn: async () => {
      const res = await api.get('/playerank/rankings', { params });
      return res.data as PlayeRankRankingsResponse;
    },
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}
