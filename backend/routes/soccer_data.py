"""
Soccer Data API routes.

Exposes the Soccer Data RapidAPI endpoints for the frontend,
providing access to xG, player predictions, team data, fixtures,
rankings, and advanced analytics.

The API uses Opta-style IDs and a `tmcl` (tournament calendar) parameter
for most team/tournament-scoped queries.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/soccer-data", tags=["soccer-data"])


# ── Response Models ──────────────────────────────────────────────────

class SoccerDataResponse(BaseModel):
    """Generic wrapper for Soccer Data API responses."""
    status: str = "ok"
    endpoint: str = ""
    data: Any = None
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    configured: bool = False
    status: str = "unknown"
    message: str = ""


# ── Helper ───────────────────────────────────────────────────────────

def _get_service():
    from services.soccer_data_api import is_configured
    if not is_configured():
        raise HTTPException(
            status_code=503,
            detail="RAPIDAPI_SOCCER_DATA_KEY não configurada. Adicione a chave nas variáveis de ambiente."
        )
    import services.soccer_data_api as svc
    return svc


# ── Health Check ─────────────────────────────────────────────────────

@router.get("/health", response_model=HealthCheckResponse)
async def soccer_data_health(_=Depends(get_current_user)):
    """Check if Soccer Data API is configured and reachable."""
    from services.soccer_data_api import is_configured, health_check
    result = await health_check()
    return HealthCheckResponse(
        configured=is_configured(),
        status=result.get("status", "unknown"),
        message=result.get("message", ""),
    )


# ══════════════════════════════════════════════════════════════════════
# TEAMS
# ══════════════════════════════════════════════════════════════════════

@router.get("/squads/{contestant_id}")
async def get_squads(
    contestant_id: str,
    tmcl: Optional[str] = Query(None, description="Tournament calendar ID"),
    detailed: bool = Query(True),
    _=Depends(get_current_user),
):
    """Get squad/roster for a team. Pass tmcl for tournament-specific squad."""
    svc = _get_service()
    data = await svc.get_squads(contestant_id, tmcl=tmcl, detailed=detailed)
    return SoccerDataResponse(endpoint="squads", data=data)


@router.get("/team/{team_id}")
async def get_team(team_id: str, _=Depends(get_current_user)):
    """Get team information."""
    svc = _get_service()
    data = await svc.get_team(team_id)
    return SoccerDataResponse(endpoint="team", data=data)


@router.get("/season-playtime/{contestant_id}")
async def get_season_playtime(
    contestant_id: str,
    tmcl: Optional[str] = Query(None, description="Tournament calendar ID"),
    _=Depends(get_current_user),
):
    """Get season playtime data for a team."""
    svc = _get_service()
    data = await svc.get_season_playtime(contestant_id, tmcl=tmcl)
    return SoccerDataResponse(endpoint="season-playtime", data=data)


@router.get("/manager-preview/{contestant_id}")
async def get_manager_preview(contestant_id: str, _=Depends(get_current_user)):
    """Get manager/coach preview for a team."""
    svc = _get_service()
    data = await svc.get_manager_preview(contestant_id)
    return SoccerDataResponse(endpoint="manager-preview", data=data)


@router.get("/contestant-participation/{contestant_id}")
async def get_contestant_participation(
    contestant_id: str,
    tmcl: Optional[str] = Query(None, description="Tournament calendar ID"),
    _=Depends(get_current_user),
):
    """Get team's participation in a tournament."""
    svc = _get_service()
    data = await svc.get_contestant_participation(contestant_id, tmcl=tmcl)
    return SoccerDataResponse(endpoint="contestant-participation", data=data)


# ══════════════════════════════════════════════════════════════════════
# PLAYERS
# ══════════════════════════════════════════════════════════════════════

@router.get("/player/{player_id}")
async def get_player(player_id: str, _=Depends(get_current_user)):
    """Get detailed player information."""
    svc = _get_service()
    data = await svc.get_player(player_id)
    return SoccerDataResponse(endpoint="player", data=data)


@router.get("/player-stats/{player_id}")
async def get_player_stats(
    player_id: str,
    tmcl: Optional[str] = Query(None, description="Tournament calendar ID"),
    _=Depends(get_current_user),
):
    """Get player statistics for a tournament."""
    svc = _get_service()
    data = await svc.get_player_stats(player_id, tmcl=tmcl)
    return SoccerDataResponse(endpoint="player-stats", data=data)


# ══════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════

@router.get("/fixtures/{tmcl}")
async def get_fixtures(tmcl: str, _=Depends(get_current_user)):
    """Get fixtures for a tournament calendar."""
    svc = _get_service()
    data = await svc.get_fixtures(tmcl)
    return SoccerDataResponse(endpoint="fixtures", data=data)


@router.get("/fixture/{match_id}")
async def get_fixture_details(match_id: str, _=Depends(get_current_user)):
    """Get detailed match information."""
    svc = _get_service()
    data = await svc.get_fixture_details(match_id)
    return SoccerDataResponse(endpoint="fixture", data=data)


# ══════════════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════════════

@router.get("/team-stats/{contestant_id}")
async def get_team_stats(
    contestant_id: str,
    tmcl: Optional[str] = Query(None, description="Tournament calendar ID"),
    _=Depends(get_current_user),
):
    """Get team statistics for a tournament."""
    svc = _get_service()
    data = await svc.get_team_stats(contestant_id, tmcl=tmcl)
    return SoccerDataResponse(endpoint="team-stats", data=data)


# ══════════════════════════════════════════════════════════════════════
# RANKINGS
# ══════════════════════════════════════════════════════════════════════

@router.get("/rankings/{tmcl}")
async def get_rankings(tmcl: str, _=Depends(get_current_user)):
    """Get rankings/standings for a tournament calendar."""
    svc = _get_service()
    data = await svc.get_rankings(tmcl)
    return SoccerDataResponse(endpoint="rankings", data=data)


# ══════════════════════════════════════════════════════════════════════
# TOURNAMENT
# ══════════════════════════════════════════════════════════════════════

@router.get("/tournament/{tournament_id}")
async def get_tournament(tournament_id: str, _=Depends(get_current_user)):
    """Get tournament information."""
    svc = _get_service()
    data = await svc.get_tournament(tournament_id)
    return SoccerDataResponse(endpoint="tournament", data=data)


# ══════════════════════════════════════════════════════════════════════
# ADVANCED ANALYTICS
# ══════════════════════════════════════════════════════════════════════

@router.get("/season-xg/{tmcl}")
async def get_season_expected_goals(tmcl: str, _=Depends(get_current_user)):
    """Get Season Expected Goals (xG) data for a tournament calendar."""
    svc = _get_service()
    data = await svc.get_season_expected_goals(tmcl)
    return SoccerDataResponse(endpoint="season-xg", data=data)


@router.get("/player-predictions/{contestant_id}")
async def get_player_predictions(
    contestant_id: str,
    tmcl: Optional[str] = Query(None, description="Tournament calendar ID"),
    _=Depends(get_current_user),
):
    """Get ML-based player performance predictions."""
    svc = _get_service()
    data = await svc.get_team_player_predictions(contestant_id, tmcl=tmcl)
    return SoccerDataResponse(endpoint="player-predictions", data=data)


@router.get("/season-simulation/{tmcl}")
async def get_season_simulation(tmcl: str, _=Depends(get_current_user)):
    """Get season/tournament simulation results."""
    svc = _get_service()
    data = await svc.get_season_simulation(tmcl)
    return SoccerDataResponse(endpoint="season-simulation", data=data)


@router.get("/match-facts/{match_id}")
async def get_match_facts(match_id: str, _=Depends(get_current_user)):
    """Get match facts and statistics."""
    svc = _get_service()
    data = await svc.get_match_facts(match_id)
    return SoccerDataResponse(endpoint="match-facts", data=data)


@router.get("/match-win-probability/{match_id}")
async def get_match_win_probability(match_id: str, _=Depends(get_current_user)):
    """Get match win probability predictions."""
    svc = _get_service()
    data = await svc.get_match_win_probability(match_id)
    return SoccerDataResponse(endpoint="match-win-probability", data=data)


# ══════════════════════════════════════════════════════════════════════
# GENERIC EXPLORER (for testing any endpoint)
# ══════════════════════════════════════════════════════════════════════

@router.get("/explore")
async def explore_endpoint(
    path: str = Query(..., description="API path after /soccerdata/ (supports inline ?params)"),
    _=Depends(get_current_user),
):
    """Generic endpoint explorer for testing any Soccer Data API path.

    Pass the full path after /soccerdata/ as query parameter.
    Supports inline query params: path=squads/abc123?tmcl=xyz&detailed=yes

    Example: /api/soccer-data/explore?path=squads/abc?tmcl=xyz%26detailed=yes
    """
    svc = _get_service()
    data = await svc.explore(path)
    return SoccerDataResponse(endpoint=f"explore/{path.split('?')[0]}", data=data)
