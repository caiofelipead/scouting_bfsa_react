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

// ── StatsBomb Open Data types ──

export interface StatsBombSeason {
  season_id: number;
  season_name: string;
}

export interface StatsBombCompetition {
  competition_id: number;
  competition_name: string;
  country_name: string;
  seasons: StatsBombSeason[];
}

export interface StatsBombMatch {
  match_id: number;
  match_date: string | null;
  kick_off: string | null;
  home_team: string;
  away_team: string;
  home_score: number | null;
  away_score: number | null;
  competition_stage: string | null;
  stadium: string | null;
  referee: string | null;
}

export interface StatsBombTeamStats {
  team: string;
  goals: number;
  shots: number;
  shots_on_target: number;
  passes: number;
  passes_completed: number;
  pass_accuracy: number;
  tackles: number;
  interceptions: number;
  fouls: number;
  yellow_cards: number;
  red_cards: number;
  corners: number;
  dribbles: number;
  dribbles_completed: number;
  xg_total: number;
}

export interface StatsBombMatchSummary {
  match_id: number;
  teams: StatsBombTeamStats[];
}

export interface StatsBombLineupPlayer {
  player_id: number | null;
  player_name: string;
  player_nickname: string | null;
  jersey_number: number | null;
  position: string | null;
  country: string | null;
}

export interface StatsBombLineup {
  team: string;
  players: StatsBombLineupPlayer[];
}

export interface StatsBombShot {
  player: string;
  team: string;
  minute: number;
  second: number;
  location_x: number | null;
  location_y: number | null;
  end_x: number | null;
  end_y: number | null;
  xg: number;
  outcome: string;
  technique: string | null;
  body_part: string | null;
  shot_type: string | null;
}

export interface StatsBombPlayerStats {
  player: string;
  team: string;
  match_id: number;
  passes: number;
  passes_completed: number;
  pass_accuracy: number;
  shots: number;
  shots_on_target: number;
  goals: number;
  assists: number;
  xg: number;
  xa: number;
  tackles: number;
  interceptions: number;
  dribbles: number;
  dribbles_completed: number;
  dribble_success: number;
  fouls_committed: number;
  fouls_won: number;
  ball_recoveries: number;
  duels_won: number;
  aerial_won: number;
  touches: number;
  key_passes: number;
  crosses: number;
  long_balls: number;
  through_balls: number;
}

// ── StatsBomb Season Insights ──

export interface StatsBombSeasonTeam {
  team: string;
  matches: number;
  goals: number;
  goals_against: number;
  xg_total: number;
  xg_against: number;
  xg_diff: number;
  shots: number;
  shots_on_target: number;
  shot_accuracy: number;
  passes: number;
  passes_completed: number;
  pass_accuracy: number;
  tackles: number;
  interceptions: number;
  fouls: number;
  yellow_cards: number;
  red_cards: number;
  corners: number;
  dribbles: number;
  dribbles_completed: number;
  wins: number;
  draws: number;
  losses: number;
  points: number;
  goal_diff: number;
  avg_goals: number;
  avg_xg: number;
  defensive_actions: number;
  avg_defensive: number;
}

export interface StatsBombTopScorer {
  player: string;
  team: string;
  goals: number;
  xg: number;
  xg_diff: number;
}

export interface StatsBombTopXg {
  player: string;
  team: string;
  xg: number;
  shots: number;
  goals: number;
  xg_diff: number;
}

export interface StatsBombXgAnalysis {
  team: string;
  goals: number;
  xg: number;
  diff: number;
  goals_against: number;
  xg_against: number;
}

export interface StatsBombTacticalEntry {
  team: string;
  value: number;
  matches: number;
}

export interface StatsBombSeasonInsights {
  competition_id: number;
  season_id: number;
  matches_total: number;
  matches_processed: number;
  total_goals: number;
  total_xg: number;
  avg_goals_per_match: number;
  avg_xg_per_match: number;
  teams: StatsBombSeasonTeam[];
  top_scorers: StatsBombTopScorer[];
  top_xg: StatsBombTopXg[];
  xg_analysis: StatsBombXgAnalysis[];
  tactical: {
    most_possession: StatsBombTacticalEntry[];
    most_pressing: StatsBombTacticalEntry[];
    best_passing: StatsBombTacticalEntry[];
    most_shots: StatsBombTacticalEntry[];
  };
}
