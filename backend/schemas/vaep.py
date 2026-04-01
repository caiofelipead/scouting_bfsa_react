"""
Pydantic schemas for VAEP and PlayeRank endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── VAEP Schemas ─────────────────────────────────────────────────────

class VAEPPipelineRequest(BaseModel):
    competition_id: Optional[int] = None
    season: str = Field(default="current", max_length=20)


class VAEPRating(BaseModel):
    player_name: str
    team: Optional[str] = None
    league: Optional[str] = None
    position: Optional[str] = None
    minutes_played: int = 0
    total_vaep: float = 0.0
    vaep_per90: float = 0.0
    offensive_vaep: float = 0.0
    defensive_vaep: float = 0.0
    actions_count: int = 0
    season: Optional[str] = None


class VAEPPipelineResponse(BaseModel):
    season: str
    method: str
    total_players: int
    total_actions: int
    total_games: int
    top_players: List[VAEPRating]


class VAEPRatingsResponse(BaseModel):
    total: int
    season: Optional[str] = None
    ratings: List[VAEPRating]


class VAEPActionDetail(BaseModel):
    action_type: str
    vaep_value: float
    offensive_value: float = 0.0
    defensive_value: float = 0.0
    x_start: Optional[float] = None
    y_start: Optional[float] = None
    x_end: Optional[float] = None
    y_end: Optional[float] = None
    minute: Optional[int] = None
    second: Optional[int] = None


class VAEPPlayerDetail(BaseModel):
    player_name: str
    team: Optional[str] = None
    league: Optional[str] = None
    position: Optional[str] = None
    minutes_played: int = 0
    total_vaep: float = 0.0
    vaep_per90: float = 0.0
    offensive_vaep: float = 0.0
    defensive_vaep: float = 0.0
    actions_count: int = 0
    top_actions: List[VAEPActionDetail] = []
    season: Optional[str] = None


class VAEPComparisonResponse(BaseModel):
    players: List[VAEPRating]


# ── PlayeRank Schemas ────────────────────────────────────────────────

class PlayeRankScore(BaseModel):
    player_name: str
    team: Optional[str] = None
    league: Optional[str] = None
    position: Optional[str] = None
    role_cluster: str = "unknown"
    composite_score: float = 0.0
    dimensions: Dict[str, float] = {}
    percentile_in_cluster: float = 0.0
    cluster_size: int = 0
    season: Optional[str] = None


class PlayeRankRankingsResponse(BaseModel):
    total: int
    role_cluster: Optional[str] = None
    season: Optional[str] = None
    rankings: List[PlayeRankScore]
