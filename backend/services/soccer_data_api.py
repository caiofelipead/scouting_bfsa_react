"""
soccer_data_api.py — Soccer Data RapidAPI Client
=================================================

Client for the Soccer Data API (soccer-data6.p.rapidapi.com).
Provides access to xG, player predictions, team squads, fixtures,
season simulations, and more.

Endpoints available:
- Season Expected Goals (xG)
- Team Player Predictions
- Season And Tournament Simulation
- Match Facts Betting
- Match Live Win Probability
- Squads, Team info, Season Playtime
- Fixtures, Rankings, Stats
- Players, Contestant Participation
- Manager Preview
"""

import logging
import os
from typing import Any, Dict, List, Optional

import aiohttp
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_SOCCER_DATA_KEY", "")
RAPIDAPI_HOST = "soccer-data6.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"

# Cache responses for 10 minutes to avoid hitting rate limits
_cache = TTLCache(maxsize=200, ttl=600)


def _headers() -> Dict[str, str]:
    return {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
        "Content-Type": "application/json",
    }


def is_configured() -> bool:
    """Check if the API key is configured."""
    return bool(RAPIDAPI_KEY)


async def _get(endpoint: str, params: Optional[Dict[str, Any]] = None,
               use_cache: bool = True) -> Dict[str, Any]:
    """Make a GET request to the Soccer Data API.

    Args:
        endpoint: API endpoint path (e.g., "/soccerdata/squads/...")
        params: Optional query parameters
        use_cache: Whether to cache the response

    Returns:
        Parsed JSON response

    Raises:
        ValueError: If API key not configured
        aiohttp.ClientError: On network errors
    """
    if not RAPIDAPI_KEY:
        raise ValueError(
            "RAPIDAPI_SOCCER_DATA_KEY não configurada. "
            "Adicione a chave da API Soccer Data nas variáveis de ambiente."
        )

    url = f"{BASE_URL}{endpoint}"
    cache_key = f"{endpoint}:{params}" if params else endpoint

    if use_cache and cache_key in _cache:
        logger.debug("Cache hit: %s", cache_key)
        return _cache[cache_key]

    logger.info("Soccer Data API request: %s params=%s", endpoint, params)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_headers(), params=params,
                               timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 429:
                logger.warning("Soccer Data API rate limited (429)")
                return {"error": "rate_limited", "message": "Limite de requisições atingido. Tente novamente em alguns minutos."}
            if resp.status == 403:
                logger.error("Soccer Data API forbidden (403) — check API key")
                return {"error": "forbidden", "message": "Chave da API inválida ou sem permissão."}
            if resp.status != 200:
                text = await resp.text()
                logger.error("Soccer Data API error %d: %s", resp.status, text[:500])
                return {"error": f"http_{resp.status}", "message": text[:500]}

            data = await resp.json()
            if use_cache:
                _cache[cache_key] = data
            return data


# ══════════════════════════════════════════════════════════════════════
# TEAMS endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_squads(team_id: str, detailed: bool = True) -> Dict[str, Any]:
    """Get squad/roster for a team.

    Args:
        team_id: Team identifier (from the API)
        detailed: Include detailed player info
    """
    params = {"detailed": "yes" if detailed else "no"}
    return await _get(f"/soccerdata/squads/{team_id}", params)


async def get_team(team_id: str) -> Dict[str, Any]:
    """Get team information."""
    return await _get(f"/soccerdata/team/{team_id}")


async def get_contestant_participation(team_id: str, tournament_id: str) -> Dict[str, Any]:
    """Get team's participation in a tournament/league."""
    return await _get(f"/soccerdata/contestant-participation/{team_id}/{tournament_id}")


async def get_season_playtime(team_id: str, tournament_id: str) -> Dict[str, Any]:
    """Get season playtime data for a team's players."""
    return await _get(f"/soccerdata/season-playtime/{team_id}/{tournament_id}")


async def get_manager_preview(team_id: str) -> Dict[str, Any]:
    """Get manager/coach preview for a team."""
    return await _get(f"/soccerdata/manager-preview/{team_id}")


# ══════════════════════════════════════════════════════════════════════
# PLAYERS endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_player(player_id: str) -> Dict[str, Any]:
    """Get detailed player information."""
    return await _get(f"/soccerdata/player/{player_id}")


# ══════════════════════════════════════════════════════════════════════
# FIXTURES endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_fixtures(tournament_id: str, season_id: Optional[str] = None) -> Dict[str, Any]:
    """Get fixtures for a tournament."""
    params = {}
    if season_id:
        params["seasonId"] = season_id
    return await _get(f"/soccerdata/fixtures/{tournament_id}", params)


async def get_fixture_details(match_id: str) -> Dict[str, Any]:
    """Get detailed match/fixture information."""
    return await _get(f"/soccerdata/fixture/{match_id}")


# ══════════════════════════════════════════════════════════════════════
# STATS endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_team_stats(team_id: str, tournament_id: str) -> Dict[str, Any]:
    """Get team statistics for a tournament."""
    return await _get(f"/soccerdata/team-stats/{team_id}/{tournament_id}")


async def get_player_stats(player_id: str, tournament_id: str) -> Dict[str, Any]:
    """Get player statistics for a tournament."""
    return await _get(f"/soccerdata/player-stats/{player_id}/{tournament_id}")


# ══════════════════════════════════════════════════════════════════════
# RANKINGS endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_rankings(tournament_id: str) -> Dict[str, Any]:
    """Get rankings/standings for a tournament."""
    return await _get(f"/soccerdata/rankings/{tournament_id}")


# ══════════════════════════════════════════════════════════════════════
# TOURNAMENT endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_tournament(tournament_id: str) -> Dict[str, Any]:
    """Get tournament information."""
    return await _get(f"/soccerdata/tournament/{tournament_id}")


# ══════════════════════════════════════════════════════════════════════
# ADVANCED ANALYTICS endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_season_expected_goals(tournament_id: str, season_id: Optional[str] = None) -> Dict[str, Any]:
    """Get Season Expected Goals (xG) data for a tournament.

    This provides real xG metrics — much more reliable than heuristic
    approximations.
    """
    params = {}
    if season_id:
        params["seasonId"] = season_id
    return await _get(f"/soccerdata/season-expected-goals/{tournament_id}", params)


async def get_team_player_predictions(team_id: str, tournament_id: str) -> Dict[str, Any]:
    """Get player performance predictions for a team.

    ML-based predictions for player performance.
    """
    return await _get(f"/soccerdata/team-player-predictions/{team_id}/{tournament_id}")


async def get_season_simulation(tournament_id: str) -> Dict[str, Any]:
    """Get season/tournament simulation results.

    Probability-based simulation of season outcomes.
    """
    return await _get(f"/soccerdata/season-simulation/{tournament_id}")


async def get_match_facts(match_id: str) -> Dict[str, Any]:
    """Get match facts and betting-relevant statistics."""
    return await _get(f"/soccerdata/match-facts/{match_id}")


async def get_match_win_probability(match_id: str) -> Dict[str, Any]:
    """Get live/pre-match win probability for a match."""
    return await _get(f"/soccerdata/match-win-probability/{match_id}")


# ══════════════════════════════════════════════════════════════════════
# UTILITY
# ══════════════════════════════════════════════════════════════════════

def clear_cache():
    """Clear the response cache."""
    _cache.clear()
    logger.info("Soccer Data API cache cleared")


async def health_check() -> Dict[str, Any]:
    """Test API connectivity with a simple request."""
    if not RAPIDAPI_KEY:
        return {
            "status": "not_configured",
            "message": "RAPIDAPI_SOCCER_DATA_KEY não configurada",
        }
    try:
        # Use a lightweight endpoint to test connectivity
        result = await _get("/soccerdata/tournament/1", use_cache=False)
        if "error" in result:
            return {"status": "error", **result}
        return {"status": "ok", "message": "Conexão com Soccer Data API OK"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
