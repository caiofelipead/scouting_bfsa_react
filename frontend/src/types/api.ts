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
  club_logo: string | null;
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

export interface AnalysisData {
  nome: string;
  scores: Record<string, number>;
  links: Record<string, string>;
  analysis_text: string | null;
  modelo: string | null;
  faixa_salarial: string | null;
  transfer_luvas: string | null;
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
  analises: AnalysisData | null;
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
  photo_url: string | null;
  club_logo: string | null;
  league_logo: string | null;
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

// ── SkillCorner types ──

export interface SkillCornerPlayerProfile {
  found: boolean;
  covered: boolean;
  league: string | null;
  position?: string;
  matched_name?: string;
  matched_team?: string;
  matched_position?: string;
  indices?: Record<string, number>;
  indices_percentiles?: Record<string, number>;
  physical?: Record<string, number>;
  physical_percentiles?: Record<string, number>;
  all_metrics?: Record<string, number>;
  reason?: string;
  searched_name?: string;
  searched_team?: string;
}

export interface SkillCornerComparisonEntry {
  metric: string;
  player1_value: number | null;
  player2_value: number | null;
  diff: number | null;
}

export interface SkillCornerComparisonResponse {
  position: string;
  player1: { name: string; sc_name: string | null; sc_team: string | null; found: boolean };
  player2: { name: string; sc_name: string | null; sc_team: string | null; found: boolean };
  comparison: SkillCornerComparisonEntry[];
}

export interface SkillCornerCoverage {
  covered_leagues: string[];
  description: string;
}

// ── API-Football v3 types ──

export interface ApiFootballCountry {
  name: string;
  code: string | null;
  flag: string | null;
}

export interface ApiFootballLeague {
  league: {
    id: number;
    name: string;
    type: string;
    logo: string;
  };
  country: {
    name: string;
    code: string | null;
    flag: string | null;
  };
  seasons: { year: number; start: string; end: string; current: boolean }[];
}

export interface ApiFootballTeam {
  team: {
    id: number;
    name: string;
    code: string | null;
    country: string;
    founded: number | null;
    national: boolean;
    logo: string;
  };
  venue: {
    id: number | null;
    name: string | null;
    address: string | null;
    city: string | null;
    capacity: number | null;
    surface: string | null;
    image: string | null;
  };
}

export interface ApiFootballStandingEntry {
  rank: number;
  team: { id: number; name: string; logo: string };
  points: number;
  goalsDiff: number;
  group: string;
  form: string | null;
  status: string | null;
  description: string | null;
  all: { played: number; win: number; draw: number; lose: number; goals: { for: number; against: number } };
  home: { played: number; win: number; draw: number; lose: number; goals: { for: number; against: number } };
  away: { played: number; win: number; draw: number; lose: number; goals: { for: number; against: number } };
  update: string;
}

export interface ApiFootballFixture {
  fixture: {
    id: number;
    referee: string | null;
    timezone: string;
    date: string;
    timestamp: number;
    venue: { id: number | null; name: string | null; city: string | null };
    status: { long: string; short: string; elapsed: number | null };
  };
  league: { id: number; name: string; country: string; logo: string; flag: string | null; season: number; round: string };
  teams: {
    home: { id: number; name: string; logo: string; winner: boolean | null };
    away: { id: number; name: string; logo: string; winner: boolean | null };
  };
  goals: { home: number | null; away: number | null };
  score: {
    halftime: { home: number | null; away: number | null };
    fulltime: { home: number | null; away: number | null };
    extratime: { home: number | null; away: number | null };
    penalty: { home: number | null; away: number | null };
  };
}

export interface ApiFootballPlayerEntry {
  player: {
    id: number;
    name: string;
    firstname: string;
    lastname: string;
    age: number;
    birth: { date: string; place: string | null; country: string | null };
    nationality: string;
    height: string | null;
    weight: string | null;
    photo: string;
  };
  statistics: {
    team: { id: number; name: string; logo: string };
    league: { id: number; name: string; country: string; logo: string; flag: string | null; season: number };
    games: { appearences: number | null; lineups: number | null; minutes: number | null; position: string | null; rating: string | null };
    goals: { total: number | null; conceded: number | null; assists: number | null; saves: number | null };
    passes: { total: number | null; key: number | null; accuracy: number | null };
    tackles: { total: number | null; blocks: number | null; interceptions: number | null };
    duels: { total: number | null; won: number | null };
    dribbles: { attempts: number | null; success: number | null; past: number | null };
    fouls: { drawn: number | null; committed: number | null };
    cards: { yellow: number | null; yellowred: number | null; red: number | null };
    penalty: { won: number | null; committed: number | null; scored: number | null; missed: number | null; saved: number | null };
    shots: { total: number | null; on: number | null };
  }[];
}

export interface ApiFootballPlayersResponse {
  players: ApiFootballPlayerEntry[];
  paging: { current: number; total: number };
}

export interface ApiFootballSquad {
  team: { id: number; name: string; logo: string };
  players: {
    id: number;
    name: string;
    age: number | null;
    number: number | null;
    position: string;
    photo: string;
  }[];
}
