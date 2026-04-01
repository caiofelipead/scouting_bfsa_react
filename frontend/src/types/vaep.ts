export interface VAEPRating {
  player_name: string;
  team: string | null;
  league: string | null;
  position: string | null;
  minutes_played: number;
  total_vaep: number;
  vaep_per90: number;
  offensive_vaep: number;
  defensive_vaep: number;
  actions_count: number;
  season: string | null;
}

export interface VAEPPipelineResponse {
  season: string;
  method: string;
  total_players: number;
  total_actions: number;
  total_games: number;
  top_players: VAEPRating[];
}

export interface VAEPRatingsResponse {
  total: number;
  season: string | null;
  ratings: VAEPRating[];
}

export interface VAEPActionDetail {
  action_type: string;
  vaep_value: number;
  offensive_value: number;
  defensive_value: number;
  x_start: number | null;
  y_start: number | null;
  x_end: number | null;
  y_end: number | null;
  minute: number | null;
  second: number | null;
}

export interface VAEPPlayerDetail extends VAEPRating {
  top_actions: VAEPActionDetail[];
}

export interface VAEPComparisonResponse {
  players: VAEPRating[];
}

export interface PlayeRankScore {
  player_name: string;
  team: string | null;
  league: string | null;
  position: string | null;
  role_cluster: string;
  composite_score: number;
  dimensions: Record<string, number>;
  percentile_in_cluster: number;
  cluster_size: number;
  season: string | null;
}

export interface PlayeRankRankingsResponse {
  total: number;
  role_cluster: string | null;
  season: string | null;
  rankings: PlayeRankScore[];
}
