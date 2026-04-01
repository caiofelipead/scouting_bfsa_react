import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params?: { season?: string; competition_id?: number }) => {
      const res = await api.post('/vaep/run-pipeline', params ?? {});
      return res.data as VAEPPipelineResponse;
    },
    onSuccess: () => {
      // Pipeline runs in background on the server — poll for results
      const delays = [5000, 10000, 20000, 30000];
      delays.forEach((ms) => {
        setTimeout(() => {
          queryClient.invalidateQueries({ queryKey: ['vaep'] });
          queryClient.invalidateQueries({ queryKey: ['playerank'] });
        }, ms);
      });
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

// ── Enrichment (API-Football photos) ────────────────────────────────

interface EnrichmentStatus {
  total_players: number;
  players_with_photo: number;
  total_teams: number;
  teams_with_logo: number;
  coverage_pct: number;
}

interface EnrichmentTriggerResponse {
  message: string;
  teams_queued: number;
  players_queued: number;
}

export function useEnrichmentStatus() {
  return useQuery({
    queryKey: ['enrichment', 'status'],
    queryFn: async () => {
      const res = await api.get('/vaep/enrichment-status');
      return res.data as EnrichmentStatus;
    },
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useSyncPhotos() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (maxCalls?: number) => {
      const res = await api.post('/vaep/sync-photos', null, {
        params: maxCalls ? { max_api_calls: maxCalls } : {},
      });
      return res.data as EnrichmentTriggerResponse;
    },
    onSuccess: () => {
      // Photo sync runs in background — poll enrichment status to track progress
      const delays = [5000, 15000, 30000, 60000, 120000];
      delays.forEach((ms) => {
        setTimeout(() => {
          queryClient.invalidateQueries({ queryKey: ['enrichment'] });
        }, ms);
      });
    },
  });
}
