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


# Fix forward reference
TokenResponse.model_rebuild()
