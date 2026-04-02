import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import type { SoccerDataResponse, SoccerDataHealth } from '../types/soccer_data';

const STALE_TIME = 10 * 60 * 1000; // 10 min
const GC_TIME = 30 * 60 * 1000;    // 30 min

export const soccerDataKeys = {
  health: ['soccer-data', 'health'] as const,
  squads: (teamId: string) => ['soccer-data', 'squads', teamId] as const,
  team: (teamId: string) => ['soccer-data', 'team', teamId] as const,
  seasonPlaytime: (teamId: string, tournamentId: string) =>
    ['soccer-data', 'season-playtime', teamId, tournamentId] as const,
  managerPreview: (teamId: string) => ['soccer-data', 'manager', teamId] as const,
  player: (playerId: string) => ['soccer-data', 'player', playerId] as const,
  fixtures: (tournamentId: string) => ['soccer-data', 'fixtures', tournamentId] as const,
  fixture: (matchId: string) => ['soccer-data', 'fixture', matchId] as const,
  teamStats: (teamId: string, tournamentId: string) =>
    ['soccer-data', 'team-stats', teamId, tournamentId] as const,
  playerStats: (playerId: string, tournamentId: string) =>
    ['soccer-data', 'player-stats', playerId, tournamentId] as const,
  rankings: (tournamentId: string) => ['soccer-data', 'rankings', tournamentId] as const,
  tournament: (tournamentId: string) => ['soccer-data', 'tournament', tournamentId] as const,
  seasonXg: (tournamentId: string) => ['soccer-data', 'season-xg', tournamentId] as const,
  playerPredictions: (teamId: string, tournamentId: string) =>
    ['soccer-data', 'player-predictions', teamId, tournamentId] as const,
  seasonSimulation: (tournamentId: string) =>
    ['soccer-data', 'season-sim', tournamentId] as const,
  matchFacts: (matchId: string) => ['soccer-data', 'match-facts', matchId] as const,
  matchWinProb: (matchId: string) => ['soccer-data', 'match-win-prob', matchId] as const,
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

export function useSquads(teamId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.squads(teamId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/squads/${teamId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!teamId,
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

export function useSeasonPlaytime(teamId: string, tournamentId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.seasonPlaytime(teamId, tournamentId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/season-playtime/${teamId}/${tournamentId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!teamId && !!tournamentId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useManagerPreview(teamId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.managerPreview(teamId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/manager-preview/${teamId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!teamId,
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

// ── Fixtures ────────────────────────────────────────────────────────

export function useFixtures(tournamentId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.fixtures(tournamentId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/fixtures/${tournamentId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!tournamentId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Stats ───────────────────────────────────────────────────────────

export function useTeamStats(teamId: string, tournamentId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.teamStats(teamId, tournamentId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/team-stats/${teamId}/${tournamentId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!teamId && !!tournamentId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function usePlayerStats(playerId: string, tournamentId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.playerStats(playerId, tournamentId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/player-stats/${playerId}/${tournamentId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!playerId && !!tournamentId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

// ── Rankings ────────────────────────────────────────────────────────

export function useRankings(tournamentId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.rankings(tournamentId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/rankings/${tournamentId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!tournamentId,
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

export function useSeasonXg(tournamentId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.seasonXg(tournamentId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/season-xg/${tournamentId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!tournamentId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function usePlayerPredictions(teamId: string, tournamentId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.playerPredictions(teamId, tournamentId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/player-predictions/${teamId}/${tournamentId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!teamId && !!tournamentId,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useSeasonSimulation(tournamentId: string, enabled = true) {
  return useQuery({
    queryKey: soccerDataKeys.seasonSimulation(tournamentId),
    queryFn: async () => {
      const res = await api.get(`/soccer-data/season-simulation/${tournamentId}`);
      return res.data as SoccerDataResponse;
    },
    enabled: enabled && !!tournamentId,
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
