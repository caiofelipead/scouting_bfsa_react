"""
soccer_data_api.py — Soccer Data RapidAPI Client
=================================================

Client for the Soccer Data API (soccer-data6.p.rapidapi.com).
Provides access to xG, player predictions, team squads, fixtures,
season simulations, and more.

Uses Opta-style IDs for teams, tournaments, and players.
Key parameter: `tmcl` = tournament calendar ID (required for many endpoints).

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
from typing import Any, Dict, Optional

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
    """
    if not RAPIDAPI_KEY:
        raise ValueError(
            "RAPIDAPI_SOCCER_DATA_KEY não configurada. "
            "Adicione a chave da API Soccer Data nas variáveis de ambiente."
        )

    url = f"{BASE_URL}{endpoint}"

    # Build stable cache key from sorted params
    sorted_params = sorted((params or {}).items())
    cache_key = f"{endpoint}?{'&'.join(f'{k}={v}' for k, v in sorted_params)}"

    if use_cache and cache_key in _cache:
        logger.debug("Cache hit: %s", cache_key)
        return _cache[cache_key]

    logger.info("Soccer Data API request: GET %s params=%s", endpoint, params)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_headers(), params=params,
                               timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 429:
                logger.warning("Soccer Data API rate limited (429)")
                return {"error": "rate_limited", "message": "Limite de requisições atingido. Tente novamente em alguns minutos."}
            if resp.status == 403:
                logger.error("Soccer Data API forbidden (403) — check API key")
                return {"error": "forbidden", "message": "Chave da API inválida ou sem permissão."}
            if resp.status == 404:
                logger.warning("Soccer Data API 404: %s", endpoint)
                return {"error": "not_found", "message": f"Endpoint não encontrado: {endpoint}"}
            if resp.status != 200:
                text = await resp.text()
                logger.error("Soccer Data API error %d: %s", resp.status, text[:500])
                return {"error": f"http_{resp.status}", "message": text[:500]}

            try:
                data = await resp.json()
            except Exception:
                text = await resp.text()
                data = {"raw_response": text[:2000]}

            if use_cache:
                _cache[cache_key] = data
            return data


# ══════════════════════════════════════════════════════════════════════
# TEAMS endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_squads(contestant_id: str, tmcl: Optional[str] = None,
                     detailed: bool = True) -> Dict[str, Any]:
    """Get squad/roster for a team.

    Args:
        contestant_id: Team/contestant Opta ID
        tmcl: Tournament calendar ID (usually required)
        detailed: Include detailed player info
    """
    params: Dict[str, Any] = {"detailed": "yes" if detailed else "no"}
    if tmcl:
        params["tmcl"] = tmcl
    return await _get(f"/soccerdata/squads/{contestant_id}", params)


async def get_team(team_id: str) -> Dict[str, Any]:
    """Get team information."""
    return await _get(f"/soccerdata/team/{team_id}")


async def get_contestant_participation(contestant_id: str,
                                        tmcl: Optional[str] = None) -> Dict[str, Any]:
    """Get team's participation details in a tournament."""
    params = {}
    if tmcl:
        params["tmcl"] = tmcl
    return await _get(f"/soccerdata/contestant-participation/{contestant_id}", params)


async def get_season_playtime(contestant_id: str,
                              tmcl: Optional[str] = None) -> Dict[str, Any]:
    """Get season playtime data for a team's players."""
    params = {}
    if tmcl:
        params["tmcl"] = tmcl
    return await _get(f"/soccerdata/season-playtime/{contestant_id}", params)


async def get_manager_preview(contestant_id: str) -> Dict[str, Any]:
    """Get manager/coach preview for a team."""
    return await _get(f"/soccerdata/manager-preview/{contestant_id}")


# ══════════════════════════════════════════════════════════════════════
# PLAYERS endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_player(player_id: str) -> Dict[str, Any]:
    """Get detailed player information."""
    return await _get(f"/soccerdata/player/{player_id}")


# ══════════════════════════════════════════════════════════════════════
# FIXTURES endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_fixtures(tmcl: str) -> Dict[str, Any]:
    """Get fixtures for a tournament calendar."""
    return await _get(f"/soccerdata/fixtures/{tmcl}")


async def get_fixture_details(match_id: str) -> Dict[str, Any]:
    """Get detailed match/fixture information."""
    return await _get(f"/soccerdata/fixture/{match_id}")


# ══════════════════════════════════════════════════════════════════════
# STATS endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_team_stats(contestant_id: str,
                         tmcl: Optional[str] = None) -> Dict[str, Any]:
    """Get team statistics for a tournament."""
    params = {}
    if tmcl:
        params["tmcl"] = tmcl
    return await _get(f"/soccerdata/team-stats/{contestant_id}", params)


async def get_player_stats(player_id: str,
                           tmcl: Optional[str] = None) -> Dict[str, Any]:
    """Get player statistics for a tournament."""
    params = {}
    if tmcl:
        params["tmcl"] = tmcl
    return await _get(f"/soccerdata/player-stats/{player_id}", params)


# ══════════════════════════════════════════════════════════════════════
# RANKINGS endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_rankings(tmcl: str) -> Dict[str, Any]:
    """Get rankings/standings for a tournament calendar."""
    return await _get(f"/soccerdata/rankings/{tmcl}")


# ══════════════════════════════════════════════════════════════════════
# TOURNAMENT endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_tournament(tournament_id: str) -> Dict[str, Any]:
    """Get tournament information."""
    return await _get(f"/soccerdata/tournament/{tournament_id}")


# ══════════════════════════════════════════════════════════════════════
# ADVANCED ANALYTICS endpoints
# ══════════════════════════════════════════════════════════════════════

async def get_season_expected_goals(tmcl: str) -> Dict[str, Any]:
    """Get Season Expected Goals (xG) data.

    Real xG metrics from the Soccer Data API.
    """
    return await _get(f"/soccerdata/season-expected-goals/{tmcl}")


async def get_team_player_predictions(contestant_id: str,
                                       tmcl: Optional[str] = None) -> Dict[str, Any]:
    """Get ML-based player performance predictions."""
    params = {}
    if tmcl:
        params["tmcl"] = tmcl
    return await _get(f"/soccerdata/team-player-predictions/{contestant_id}", params)


async def get_season_simulation(tmcl: str) -> Dict[str, Any]:
    """Get season/tournament simulation (probability-based)."""
    return await _get(f"/soccerdata/season-simulation/{tmcl}")


async def get_match_facts(match_id: str) -> Dict[str, Any]:
    """Get match facts and betting-relevant statistics."""
    return await _get(f"/soccerdata/match-facts/{match_id}")


async def get_match_win_probability(match_id: str) -> Dict[str, Any]:
    """Get live/pre-match win probability for a match."""
    return await _get(f"/soccerdata/match-win-probability/{match_id}")


# ══════════════════════════════════════════════════════════════════════
# GENERIC (for explorer)
# ══════════════════════════════════════════════════════════════════════

async def explore(path: str, extra_params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Call any endpoint path with optional query params.

    Args:
        path: Path after /soccerdata/ (e.g., "squads/abc123?tmcl=xyz")
        extra_params: Additional query parameters
    """
    clean = path.strip("/")
    # Parse inline query params from the path
    params = dict(extra_params or {})
    if "?" in clean:
        clean, qs = clean.split("?", 1)
        for part in qs.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                params[k] = v
    return await _get(f"/soccerdata/{clean}", params if params else None)


# ══════════════════════════════════════════════════════════════════════
# UTILITY
# ══════════════════════════════════════════════════════════════════════

def clear_cache():
    """Clear the response cache."""
    _cache.clear()
    logger.info("Soccer Data API cache cleared")


async def health_check() -> Dict[str, Any]:
    """Test API connectivity."""
    if not RAPIDAPI_KEY:
        return {
            "status": "not_configured",
            "message": "RAPIDAPI_SOCCER_DATA_KEY não configurada",
        }
    try:
        result = await _get("/soccerdata/tournament/1", use_cache=False)
        if "error" in result:
            return {"status": "error", **result}
        return {"status": "ok", "message": "Conexão com Soccer Data API OK"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
