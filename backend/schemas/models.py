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
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=200)
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
    position: str = Field(min_length=1, max_length=50)
    min_minutes: int = Field(0, ge=0, le=50000)
    league: Optional[str] = Field(None, max_length=100)
    top_n: int = Field(50, ge=1, le=500)


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
    player_name: str = Field(min_length=1, max_length=200)
    position: str = Field(min_length=1, max_length=50)
    top_n: int = Field(20, ge=1, le=500)
    min_minutes: int = Field(500, ge=0, le=50000)


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
    player_name: str = Field(min_length=1, max_length=200)
    league: Optional[str] = Field(None, max_length=100)


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
    position: Optional[str] = Field(None, max_length=50)
    top_n: int = Field(50, ge=1, le=500)
    min_minutes: int = Field(400, ge=0, le=50000)


class MarketOpportunitiesResponse(BaseModel):
    position: Optional[str] = None
    total: int
    opportunities: List[MarketOpportunityEntry]


class ReplacementRequest(BaseModel):
    player_name: str = Field(min_length=1, max_length=200)
    position: Optional[str] = Field(None, max_length=50)
    top_n: int = Field(20, ge=1, le=500)
    min_minutes: int = Field(400, ge=0, le=50000)
    age_min: Optional[float] = Field(None, ge=14, le=50)
    age_max: Optional[float] = Field(None, ge=14, le=50)
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
    player_name: str = Field(min_length=1, max_length=200)
    league: Optional[str] = Field(None, max_length=100)
    salary: Optional[float] = Field(None, ge=0, le=100_000_000)


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


# Fix forward reference
TokenResponse.model_rebuild()
