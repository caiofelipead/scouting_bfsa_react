import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import type {
  ApiFootballCountry,
  ApiFootballLeague,
  ApiFootballTeam,
  ApiFootballStandingEntry,
  ApiFootballFixture,
  ApiFootballPlayersResponse,
  ApiFootballPlayerEntry,
  ApiFootballSquad,
} from '../types/api';

const STALE = 10 * 60 * 1000;  // 10 min
const GC = 30 * 60 * 1000;     // 30 min
const LONG_STALE = 60 * 60 * 1000; // 1 hour (reference data)

export const apiFootballKeys = {
  countries: ['apifootball', 'countries'] as const,
  leagues: (country?: string) => ['apifootball', 'leagues', country ?? ''] as const,
  teams: (league: number, season: number) => ['apifootball', 'teams', league, season] as const,
  standings: (league: number, season: number) => ['apifootball', 'standings', league, season] as const,
  fixtures: (params: Record<string, unknown>) => ['apifootball', 'fixtures', params] as const,
  topScorers: (league: number, season: number) => ['apifootball', 'topscorers', league, season] as const,
  topAssists: (league: number, season: number) => ['apifootball', 'topassists', league, season] as const,
  players: (params: Record<string, unknown>) => ['apifootball', 'players', params] as const,
  squads: (teamId: number) => ['apifootball', 'squads', teamId] as const,
};

// ── Countries ──

export function useApiFootballCountries() {
  return useQuery({
    queryKey: apiFootballKeys.countries,
    queryFn: async () => {
      const res = await api.get('/apifootball/countries');
      return res.data as ApiFootballCountry[];
    },
    staleTime: LONG_STALE,
    gcTime: GC,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  });
}

// ── Leagues ──

export function useApiFootballLeagues(country?: string) {
  return useQuery({
    queryKey: apiFootballKeys.leagues(country),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (country) params.country = country;
      const res = await api.get('/apifootball/leagues', { params });
      return res.data as ApiFootballLeague[];
    },
    enabled: !!country,
    staleTime: LONG_STALE,
    gcTime: GC,
  });
}

// ── Teams ──

export function useApiFootballTeams(leagueId: number, season: number) {
  return useQuery({
    queryKey: apiFootballKeys.teams(leagueId, season),
    queryFn: async () => {
      const res = await api.get('/apifootball/teams', { params: { league: leagueId, season } });
      return res.data as ApiFootballTeam[];
    },
    enabled: leagueId > 0 && season > 0,
    staleTime: STALE,
    gcTime: GC,
  });
}

// ── Standings ──

export function useApiFootballStandings(leagueId: number, season: number) {
  return useQuery({
    queryKey: apiFootballKeys.standings(leagueId, season),
    queryFn: async () => {
      const res = await api.get('/apifootball/standings', { params: { league: leagueId, season } });
      return res.data as ApiFootballStandingEntry[][];
    },
    enabled: leagueId > 0 && season > 0,
    staleTime: STALE,
    gcTime: GC,
  });
}

// ── Fixtures ──

export function useApiFootballFixtures(params: {
  league?: number;
  season?: number;
  team?: number;
  last?: number;
  next?: number;
}) {
  return useQuery({
    queryKey: apiFootballKeys.fixtures(params),
    queryFn: async () => {
      const res = await api.get('/apifootball/fixtures', { params });
      return res.data as ApiFootballFixture[];
    },
    enabled: !!(params.league || params.team),
    staleTime: STALE,
    gcTime: GC,
  });
}

// ── Top Scorers ──

export function useApiFootballTopScorers(leagueId: number, season: number) {
  return useQuery({
    queryKey: apiFootballKeys.topScorers(leagueId, season),
    queryFn: async () => {
      const res = await api.get('/apifootball/topscorers', { params: { league: leagueId, season } });
      return res.data as ApiFootballPlayerEntry[];
    },
    enabled: leagueId > 0 && season > 0,
    staleTime: STALE,
    gcTime: GC,
  });
}

// ── Top Assists ──

export function useApiFootballTopAssists(leagueId: number, season: number) {
  return useQuery({
    queryKey: apiFootballKeys.topAssists(leagueId, season),
    queryFn: async () => {
      const res = await api.get('/apifootball/topassists', { params: { league: leagueId, season } });
      return res.data as ApiFootballPlayerEntry[];
    },
    enabled: leagueId > 0 && season > 0,
    staleTime: STALE,
    gcTime: GC,
  });
}

// ── Players Search ──

export function useApiFootballPlayers(params: {
  league?: number;
  season?: number;
  team?: number;
  search?: string;
  page?: number;
}) {
  return useQuery({
    queryKey: apiFootballKeys.players(params),
    queryFn: async () => {
      const res = await api.get('/apifootball/players', { params });
      return res.data as ApiFootballPlayersResponse;
    },
    enabled: !!(params.league || params.team || (params.search && params.search.length >= 3)),
    staleTime: STALE,
    gcTime: GC,
    placeholderData: (prev: ApiFootballPlayersResponse | undefined) => prev,
  });
}

// ── Squads ──

export function useApiFootballSquads(teamId: number) {
  return useQuery({
    queryKey: apiFootballKeys.squads(teamId),
    queryFn: async () => {
      const res = await api.get(`/apifootball/squads/${teamId}`);
      return res.data as ApiFootballSquad[];
    },
    enabled: teamId > 0,
    staleTime: STALE,
    gcTime: GC,
  });
}
