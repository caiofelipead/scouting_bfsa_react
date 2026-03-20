import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import type {
  StatsBombCompetition,
  StatsBombMatch,
  StatsBombMatchSummary,
  StatsBombLineup,
  StatsBombShot,
  StatsBombPlayerStats,
} from '../types/api';

const STALE_TIME = 30 * 60 * 1000;  // 30 min (historical data doesn't change)
const GC_TIME = 60 * 60 * 1000;     // 60 min

export const statsBombKeys = {
  competitions: ['statsbomb', 'competitions'] as const,
  matches: (compId: number, seasonId: number) => ['statsbomb', 'matches', compId, seasonId] as const,
  summary: (matchId: number) => ['statsbomb', 'summary', matchId] as const,
  lineups: (matchId: number) => ['statsbomb', 'lineups', matchId] as const,
  shots: (matchId: number) => ['statsbomb', 'shots', matchId] as const,
  playerStats: (matchId: number, player: string) => ['statsbomb', 'player', matchId, player] as const,
  passNetwork: (matchId: number, team: string) => ['statsbomb', 'passNetwork', matchId, team] as const,
};

export function useStatsBombCompetitions() {
  return useQuery({
    queryKey: statsBombKeys.competitions,
    queryFn: async () => {
      const res = await api.get('/statsbomb/competitions');
      return res.data as { total: number; competitions: StatsBombCompetition[] };
    },
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  });
}

export function useStatsBombMatches(competitionId: number | null, seasonId: number | null) {
  return useQuery({
    queryKey: statsBombKeys.matches(competitionId ?? 0, seasonId ?? 0),
    queryFn: async () => {
      const res = await api.get(`/statsbomb/matches/${competitionId}/${seasonId}`);
      return res.data as { total: number; matches: StatsBombMatch[] };
    },
    enabled: !!competitionId && !!seasonId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useStatsBombMatchSummary(matchId: number | null) {
  return useQuery({
    queryKey: statsBombKeys.summary(matchId ?? 0),
    queryFn: async () => {
      const res = await api.get(`/statsbomb/match/${matchId}/summary`);
      return res.data as StatsBombMatchSummary;
    },
    enabled: !!matchId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useStatsBombLineups(matchId: number | null) {
  return useQuery({
    queryKey: statsBombKeys.lineups(matchId ?? 0),
    queryFn: async () => {
      const res = await api.get(`/statsbomb/match/${matchId}/lineups`);
      return res.data as { match_id: number; lineups: StatsBombLineup[] };
    },
    enabled: !!matchId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useStatsBombShots(matchId: number | null) {
  return useQuery({
    queryKey: statsBombKeys.shots(matchId ?? 0),
    queryFn: async () => {
      const res = await api.get(`/statsbomb/match/${matchId}/shots`);
      return res.data as { match_id: number; total: number; shots: StatsBombShot[] };
    },
    enabled: !!matchId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useStatsBombPlayerStats(matchId: number | null, playerName: string | null) {
  return useQuery({
    queryKey: statsBombKeys.playerStats(matchId ?? 0, playerName ?? ''),
    queryFn: async () => {
      const res = await api.get(`/statsbomb/match/${matchId}/player/${encodeURIComponent(playerName!)}`);
      return res.data as StatsBombPlayerStats;
    },
    enabled: !!matchId && !!playerName,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useStatsBombPassNetwork(matchId: number | null, teamName: string | null) {
  return useQuery({
    queryKey: statsBombKeys.passNetwork(matchId ?? 0, teamName ?? ''),
    queryFn: async () => {
      const res = await api.get(`/statsbomb/match/${matchId}/pass-network/${encodeURIComponent(teamName!)}`);
      return res.data as { team: string; match_id: number; nodes: { player: string; avg_x: number; avg_y: number; total_passes: number }[]; edges: { from: string; to: string; passes: number }[] };
    },
    enabled: !!matchId && !!teamName,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}
