import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import type { SoccerDataResponse, SoccerDataHealth } from '../types/soccer_data';

const STALE_TIME = 10 * 60 * 1000; // 10 min
const GC_TIME = 30 * 60 * 1000;    // 30 min

export const soccerDataKeys = {
  health: ['soccer-data', 'health'] as const,
  squads: (contestantId: string, tmcl?: string) =>
    ['soccer-data', 'squads', contestantId, tmcl] as const,
  team: (teamId: string) => ['soccer-data', 'team', teamId] as const,
  seasonPlaytime: (contestantId: string, tmcl?: string) =>
    ['soccer-data', 'season-playtime', contestantId, tmcl] as const,
  managerPreview: (contestantId: string) =>
    ['soccer-data', 'manager', contestantId] as const,
  player: (playerId: string) => ['soccer-data', 'player', playerId] as const,
  playerStats: (playerId: string, tmcl?: string) =>
    ['soccer-data', 'player-stats', playerId, tmcl] as const,
  fixtures: (tmcl: string) => ['soccer-data', 'fixtures', tmcl] as const,
  fixture: (matchId: string) => ['soccer-data', 'fixture', matchId] as const,
  teamStats: (contestantId: string, tmcl?: string) =>
    ['soccer-data', 'team-stats', contestantId, tmcl] as const,
  rankings: (tmcl: string) => ['soccer-data', 'rankings', tmcl] as const,
  tournament: (tournamentId: string) =>
    ['soccer-data', 'tournament', tournamentId] as const,
  seasonXg: (tmcl: string) => ['soccer-data', 'season-xg', tmcl] as const,
  playerPredictions: (contestantId: string, tmcl?: string) =>
    ['soccer-data', 'player-predictions', contestantId, tmcl] as const,
  seasonSimulation: (tmcl: string) =>
    ['soccer-data', 'season-sim', tmcl] as const,
  matchFacts: (matchId: string) => ['soccer-data', 'match-facts', matchId] as const,
  matchWinProb: (matchId: string) =>
    ['soccer-data', 'match-win-prob', matchId] as const,
  explore: (path: string) => ['soccer-data', 'explore', path] as const,
};

// ── Health Check ────────────────────────────────────────────────────

export function useSoccerDataHealth() {
  return useQuery({
    queryKey: soccerDataKeys.health,
    queryFn: async () => {
      const res = await api.get('/soccer-data/health');
      return res.data as SoccerDataHealth;
    },
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Generic Explorer ────────────────────────────────────────────────

export function useSoccerDataExplore(path: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.explore(path),
    queryFn: async () => {
      const res = await api.get('/soccer-data/explore', { params: { path } });
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!path,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Teams ───────────────────────────────────────────────────────────

export function useSquads(contestantId: string, tmcl?: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.squads(contestantId, tmcl),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (tmcl) params.tmcl = tmcl;
      const res = await api.get(`/soccer-data/squads/${contestantId}`, { params });
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!contestantId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useTeam(teamId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.team(teamId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/team/${teamId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!teamId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useSeasonPlaytime(contestantId: string, tmcl?: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.seasonPlaytime(contestantId, tmcl),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (tmcl) params.tmcl = tmcl;
      const res = await api.get(`/soccer-data/season-playtime/${contestantId}`, { params });
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!contestantId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useManagerPreview(contestantId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.managerPreview(contestantId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/manager-preview/${contestantId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!contestantId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Players ─────────────────────────────────────────────────────────

export function usePlayer(playerId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.player(playerId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/player/${playerId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!playerId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function usePlayerStats(playerId: string, tmcl?: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.playerStats(playerId, tmcl),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (tmcl) params.tmcl = tmcl;
      const res = await api.get(`/soccer-data/player-stats/${playerId}`, { params });
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!playerId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Fixtures ────────────────────────────────────────────────────────

export function useFixtures(tmcl: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.fixtures(tmcl),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/fixtures/${tmcl}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!tmcl,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Stats ───────────────────────────────────────────────────────────

export function useTeamStats(contestantId: string, tmcl?: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.teamStats(contestantId, tmcl),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (tmcl) params.tmcl = tmcl;
      const res = await api.get(`/soccer-data/team-stats/${contestantId}`, { params });
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!contestantId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Rankings ────────────────────────────────────────────────────────

export function useRankings(tmcl: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.rankings(tmcl),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/rankings/${tmcl}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!tmcl,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Tournament ──────────────────────────────────────────────────────

export function useTournament(tournamentId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.tournament(tournamentId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/tournament/${tournamentId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!tournamentId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Advanced Analytics ──────────────────────────────────────────────

export function useSeasonXg(tmcl: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.seasonXg(tmcl),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/season-xg/${tmcl}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!tmcl,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function usePlayerPredictions(contestantId: string, tmcl?: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.playerPredictions(contestantId, tmcl),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (tmcl) params.tmcl = tmcl;
      const res = await api.get(`/soccer-data/player-predictions/${contestantId}`, { params });
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!contestantId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useSeasonSimulation(tmcl: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.seasonSimulation(tmcl),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/season-simulation/${tmcl}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!tmcl,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useMatchFacts(matchId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.matchFacts(matchId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/match-facts/${matchId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!matchId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useMatchWinProbability(matchId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.matchWinProb(matchId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/match-win-probability/${matchId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!matchId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}
