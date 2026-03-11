export interface User {
  id: number;
  email: string;
  name: string;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface PlayerSummary {
  id: number;
  name: string;
  display_name: string | null;
  team: string | null;
  position: string | null;
  age: number | null;
  nationality: string | null;
  league: string | null;
  minutes_played: number | null;
  photo_url: string | null;
  score: number | null;
}

export interface PlayerProfile {
  summary: PlayerSummary;
  metrics: Record<string, number>;
  percentiles: Record<string, number>;
  indices: Record<string, number>;
  scout_score: number | null;
  performance_class: string | null;
  skillcorner: Record<string, number> | null;
  projection_score: number | null;
}

export interface RankingEntry {
  rank: number;
  name: string;
  display_name: string | null;
  team: string | null;
  age: number | null;
  league: string | null;
  minutes: number | null;
  score: number;
  indices: Record<string, number>;
}

export interface RankingResponse {
  position: string;
  total: number;
  players: RankingEntry[];
}

export interface SimilarPlayer {
  name: string;
  display_name: string | null;
  team: string | null;
  similarity_pct: number;
  matched_metrics: number;
}

export interface SimilarityResponse {
  reference_player: string;
  position: string;
  similar_players: SimilarPlayer[];
}

export interface RadarData {
  labels: string[];
  values: number[];
  position: string;
  player_name: string;
}

export interface ComparisonData {
  labels: string[];
  player1: { name: string; values: number[] };
  player2: { name: string; values: number[] };
  position: string;
}

export interface BreakdownEntry {
  Metrica: string;
  Peso: number;
  Referencia: number;
  Similar: number;
  Diferenca: number;
  Invertida: string;
}

// Query parameter types
export interface PlayersQueryParams {
  position?: string;
  league?: string;
  search?: string;
  min_minutes?: number;
  min_age?: number;
  max_age?: number;
  limit?: number;
  offset?: number;
}

export interface RankingsQueryParams {
  position: string;
  min_minutes?: number;
  league?: string;
  top_n?: number;
}

export interface SimilarityQueryParams {
  player_name: string;
  position: string;
  top_n?: number;
  min_minutes?: number;
}
