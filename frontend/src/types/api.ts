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

export interface PredictionResult {
  success_probability: number;
  risk_level: string;
  ssp_contribution: number;
  age_factor: number;
  league_factor: number;
  minutes_factor: number;
  league_discount: number;
  tier_origin: number;
  tier_target: number;
  league_gap: number;
}

export interface PlayerProfile {
  summary: PlayerSummary;
  metrics: Record<string, number>;
  percentiles: Record<string, number>;
  indices: Record<string, number>;
  scout_score: number | null;
  performance_class: string | null;
  skillcorner: Record<string, number> | null;
  skillcorner_physical: Record<string, number> | null;
  projection_score: number | null;
  ssp_lambdas: Record<string, number> | null;
  prediction: PredictionResult | null;
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

export interface IndicesResponse {
  player: string;
  position: string;
  indices: Record<string, number>;
  breakdown: Record<string, { metric: string; value: number | null; percentile: number }[]>;
  summary: {
    name: string;
    team: string | null;
    age: number | null;
    minutes: number | null;
    position_raw: string | null;
  };
}

export interface ComparisonResponse {
  position: string;
  player1: { name: string; team: string | null; age: number | null; position_raw: string | null };
  player2: { name: string; team: string | null; age: number | null; position_raw: string | null };
  comparison: { index: string; player1_value: number; player2_value: number; diff: number }[];
  indices1: Record<string, number>;
  indices2: Record<string, number>;
}

export interface DataTableResponse {
  source: string;
  total: number;
  columns: string[];
  rows: Record<string, string | number | null>[];
}

export interface PredictionResponse {
  player: {
    name: string;
    display_name: string;
    team: string | null;
    position: string;
    age: number;
    minutes: number;
    league: string;
  };
  ssp_score: number;
  prediction: PredictionResult;
}

export interface ClusterPlayer {
  name: string;
  team: string | null;
  probability: number;
  age: number | null;
  minutes: number | null;
}

export interface ClusterResult {
  id: number;
  name?: string;
  size: number;
  players: ClusterPlayer[];
  features: { metric: string; zscore: number }[];
}

export interface ClustersResponse {
  position: string;
  n_clusters: number;
  total_players: number;
  clusters: ClusterResult[];
  error?: string;
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
