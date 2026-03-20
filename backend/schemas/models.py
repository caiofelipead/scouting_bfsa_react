"""
Pydantic models for the Scouting API request/response schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────

class TokenPayload(BaseModel):
    sub: str
    role: str
    name: str
    exp: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=6)
    name: str
    role: str = "analyst"


# ── Players ───────────────────────────────────────────────────────────

class PlayerSummary(BaseModel):
    id: int
    name: str
    display_name: Optional[str] = None
    team: Optional[str] = None
    position: Optional[str] = None
    age: Optional[float] = None
    nationality: Optional[str] = None
    league: Optional[str] = None
    minutes_played: Optional[float] = None
    photo_url: Optional[str] = None
    club_logo: Optional[str] = None
    league_logo: Optional[str] = None
    score: Optional[float] = None


class PlayerMetrics(BaseModel):
    name: str
    position: Optional[str] = None
    metrics: Dict[str, float] = {}


class PlayerProfile(BaseModel):
    summary: PlayerSummary
    metrics: Dict[str, float] = {}
    percentiles: Dict[str, float] = {}
    indices: Dict[str, float] = {}
    scout_score: Optional[float] = None
    performance_class: Optional[str] = None
    skillcorner: Optional[Dict[str, Any]] = None
    skillcorner_physical: Optional[Dict[str, Any]] = None


# ── Rankings ──────────────────────────────────────────────────────────

class RankingRequest(BaseModel):
    position: str
    min_minutes: int = 0
    league: Optional[str] = None
    top_n: int = 50


class RankingEntry(BaseModel):
    rank: int
    name: str
    display_name: Optional[str] = None
    team: Optional[str] = None
    age: Optional[float] = None
    league: Optional[str] = None
    minutes: Optional[float] = None
    score: float
    indices: Dict[str, float] = {}
    photo_url: Optional[str] = None
    club_logo: Optional[str] = None
    league_logo: Optional[str] = None


class RankingResponse(BaseModel):
    position: str
    total: int
    players: List[RankingEntry]


# ── Similarity ────────────────────────────────────────────────────────

class SimilarityRequest(BaseModel):
    player_name: str
    position: str
    top_n: int = 20
    min_minutes: int = 500


class SimilarPlayer(BaseModel):
    name: str
    display_name: Optional[str] = None
    team: Optional[str] = None
    similarity_pct: float
    matched_metrics: int


class SimilarityResponse(BaseModel):
    reference_player: str
    position: str
    similar_players: List[SimilarPlayer]


class SimilarityBreakdown(BaseModel):
    metric: str
    weight: float
    reference_value: float
    similar_value: float
    difference: float
    inverted: bool = False


# ── Radar / Charts ────────────────────────────────────────────────────

class RadarData(BaseModel):
    labels: List[str]
    values: List[float]
    position: str
    player_name: str


# ── Mappings / Config ─────────────────────────────────────────────────

class PositionConfig(BaseModel):
    positions: List[str]
    indices: Dict[str, Dict[str, List[str]]]
    skillcorner_indices: Dict[str, List[str]]


class LeagueSummary(BaseModel):
    leagues: List[str]
    league_logos: Dict[str, str]


# ── Scouting Intelligence ─────────────────────────────────────────────

class TrajectoryRequest(BaseModel):
    player_name: str
    league: Optional[str] = None


class TrajectoryResponse(BaseModel):
    player: str
    display_name: Optional[str] = None
    position: Optional[str] = None
    predicted_rating_next_season: Optional[float] = None
    current_rating_estimate: Optional[float] = None
    trajectory_score: Optional[float] = None
    league_adjustment_factor: Optional[float] = None
    model_r2: Optional[float] = None
    top_features: Optional[Dict[str, float]] = None
    method: Optional[str] = None


class MarketValueRequest(BaseModel):
    player_name: str
    league: Optional[str] = None
    current_value: Optional[float] = None


class MarketValueResponse(BaseModel):
    player: str
    display_name: Optional[str] = None
    position: Optional[str] = None
    team: Optional[str] = None
    league: Optional[str] = None
    age: Optional[float] = None
    estimated_market_value: Optional[float] = None
    market_value_gap: Optional[float] = None
    market_value_gap_pct: Optional[float] = None
    value_category: Optional[str] = None
    is_undervalued: Optional[bool] = None


class MarketOpportunityEntry(BaseModel):
    player: str
    player_display: Optional[str] = None
    team: Optional[str] = None
    market_opportunity_score: float
    classification: str
    is_high_opportunity: bool
    components: Optional[Dict[str, float]] = None


class MarketOpportunitiesRequest(BaseModel):
    position: Optional[str] = None
    top_n: int = 50
    min_minutes: int = 400


class MarketOpportunitiesResponse(BaseModel):
    position: Optional[str] = None
    total: int
    opportunities: List[MarketOpportunityEntry]


class ReplacementRequest(BaseModel):
    player_name: str
    position: Optional[str] = None
    top_n: int = 20
    min_minutes: int = 400
    age_min: Optional[float] = None
    age_max: Optional[float] = None
    league_filter: Optional[List[str]] = None


class ReplacementEntry(BaseModel):
    rank: int
    player: str
    display_name: Optional[str] = None
    team: Optional[str] = None
    position: Optional[str] = None
    age: Optional[float] = None
    minutes: Optional[float] = None
    similarity_score: float
    cosine_similarity: Optional[float] = None
    mahalanobis_similarity: Optional[float] = None
    cluster_proximity: Optional[float] = None
    trajectory_score: Optional[float] = None
    predicted_rating: Optional[float] = None
    market_value_gap: Optional[float] = None
    estimated_value: Optional[float] = None


class ReplacementResponse(BaseModel):
    reference_player: str
    position: str
    total: int
    replacements: List[ReplacementEntry]


# ── Contract Impact ───────────────────────────────────────────────

class ContractImpactRequest(BaseModel):
    player_name: str
    league: Optional[str] = None
    salary: Optional[float] = None


class ContractImpactSquadPlayer(BaseModel):
    name: str
    age: Optional[float] = None


class ContractImpactSquadContext(BaseModel):
    current_players_at_position: List[ContractImpactSquadPlayer] = []
    squad_size: int = 0
    position_depth: int = 0
    ideal_depth: int = 0


class ContractImpactResponse(BaseModel):
    candidate: Dict[str, Any] = {}
    impact_score: float
    classification: str
    recommendation: str
    component_scores: Dict[str, float] = {}
    component_weights: Dict[str, float] = {}
    positional_need: Dict[str, Any] = {}
    quality_uplift: Dict[str, Any] = {}
    tactical_complementarity: Dict[str, Any] = {}
    age_profile_fit: Dict[str, Any] = {}
    salary_efficiency: Dict[str, Any] = {}
    risk_assessment: Dict[str, Any] = {}
    squad_context: Dict[str, Any] = {}


# ── StatsBomb Open Data ──────────────────────────────────────────────

class StatsBombCompetitionSeason(BaseModel):
    season_id: int
    season_name: str


class StatsBombCompetition(BaseModel):
    competition_id: int
    competition_name: str
    country_name: str
    seasons: List[StatsBombCompetitionSeason]


class StatsBombMatch(BaseModel):
    match_id: int
    match_date: Optional[str] = None
    kick_off: Optional[str] = None
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    competition_stage: Optional[str] = None
    stadium: Optional[str] = None
    referee: Optional[str] = None


class StatsBombTeamStats(BaseModel):
    team: str
    goals: int = 0
    shots: int = 0
    shots_on_target: int = 0
    passes: int = 0
    passes_completed: int = 0
    pass_accuracy: float = 0.0
    tackles: int = 0
    interceptions: int = 0
    fouls: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    corners: int = 0
    dribbles: int = 0
    dribbles_completed: int = 0
    xg_total: float = 0.0


class StatsBombMatchSummary(BaseModel):
    match_id: int
    teams: List[StatsBombTeamStats]


class StatsBombLineupPlayer(BaseModel):
    player_id: Optional[int] = None
    player_name: str
    player_nickname: Optional[str] = None
    jersey_number: Optional[int] = None
    position: Optional[str] = None
    country: Optional[str] = None


class StatsBombLineup(BaseModel):
    team: str
    players: List[StatsBombLineupPlayer]


class StatsBombPlayerStats(BaseModel):
    player: str
    team: str
    match_id: int
    passes: int = 0
    passes_completed: int = 0
    pass_accuracy: float = 0.0
    shots: int = 0
    shots_on_target: int = 0
    goals: int = 0
    assists: int = 0
    xg: float = 0.0
    xa: float = 0.0
    tackles: int = 0
    interceptions: int = 0
    dribbles: int = 0
    dribbles_completed: int = 0
    dribble_success: float = 0.0
    fouls_committed: int = 0
    fouls_won: int = 0
    ball_recoveries: int = 0
    duels_won: int = 0
    aerial_won: int = 0
    touches: int = 0
    key_passes: int = 0
    crosses: int = 0
    long_balls: int = 0
    through_balls: int = 0


class StatsBombShot(BaseModel):
    player: str
    team: str
    minute: int = 0
    second: int = 0
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    end_x: Optional[float] = None
    end_y: Optional[float] = None
    xg: float = 0.0
    outcome: str = ""
    technique: Optional[str] = None
    body_part: Optional[str] = None
    shot_type: Optional[str] = None


class StatsBombPassNode(BaseModel):
    player: str
    avg_x: float
    avg_y: float
    total_passes: int


class StatsBombPassEdge(BaseModel):
    from_player: str = Field(alias="from")
    to_player: str = Field(alias="to")
    passes: int

    model_config = {"populate_by_name": True}


class StatsBombPassNetwork(BaseModel):
    team: str
    match_id: int
    nodes: List[StatsBombPassNode]
    edges: List[StatsBombPassEdge]


# Fix forward reference
TokenResponse.model_rebuild()
