"""
thesportsdb.py — TheSportsDB API Client for player photos & team badges
========================================================================

Free API for football player photos (cutouts/thumbs) and team badges/logos.
No API key required for free tier (uses test key "3").
Rate limit: 30 requests/minute.

Key image fields:
  Team:   strTeamBadge, strTeamLogo, strTeamBanner, strTeamThumb
  Player: strCutout, strThumb, strRender

Docs: https://www.thesportsdb.com/free_sports_api
"""

import logging
from typing import Any, Dict, List, Optional

import aiohttp
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────

# Free tier uses test key "3"; paid key can be set via env
import os
API_KEY = os.environ.get("THESPORTSDB_API_KEY", "3")
BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"

# Brazilian league IDs in TheSportsDB
LEAGUE_IDS = {
    "serie_a": "4351",
    "serie_b": "4404",
}

# Cache team/player lookups for 1 hour to respect rate limits
_team_cache = TTLCache(maxsize=500, ttl=3600)
_player_cache = TTLCache(maxsize=2000, ttl=3600)


async def _get(endpoint: str, params: Optional[Dict[str, str]] = None) -> Any:
    """Make a GET request to TheSportsDB API."""
    url = f"{BASE_URL}/{endpoint}"
    logger.debug("TheSportsDB request: %s params=%s", endpoint, params)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 429:
                logger.warning("TheSportsDB rate limited (429)")
                return None
            if resp.status != 200:
                logger.warning("TheSportsDB error %d for %s", resp.status, endpoint)
                return None
            return await resp.json()


# ══════════════════════════════════════════════════════════════════════
# TEAM endpoints
# ══════════════════════════════════════════════════════════════════════

async def search_team(team_name: str) -> Optional[Dict[str, Any]]:
    """Search for a team by name. Returns the first match or None.

    Response fields of interest:
      idTeam, strTeam, strTeamBadge, strTeamLogo, strTeamBanner, strTeamThumb
    """
    cache_key = f"team:{team_name.lower().strip()}"
    if cache_key in _team_cache:
        return _team_cache[cache_key]

    data = await _get("searchteams.php", {"t": team_name})
    if not data or not data.get("teams"):
        _team_cache[cache_key] = None
        return None

    team = data["teams"][0]
    _team_cache[cache_key] = team
    return team


async def get_teams_in_league(league_id: str) -> List[Dict[str, Any]]:
    """Get all teams in a league by league ID.

    Use LEAGUE_IDS['serie_a'] = '4351' or LEAGUE_IDS['serie_b'] = '4404'.
    """
    cache_key = f"league_teams:{league_id}"
    if cache_key in _team_cache:
        return _team_cache[cache_key]

    data = await _get("lookup_all_teams.php", {"id": league_id})
    if not data or not data.get("teams"):
        return []

    teams = data["teams"]
    _team_cache[cache_key] = teams
    return teams


async def get_team_badge(team_name: str) -> Optional[str]:
    """Get team badge URL by searching team name.

    Returns the strTeamBadge URL or None.
    """
    team = await search_team(team_name)
    if team:
        return team.get("strTeamBadge")
    return None


# ══════════════════════════════════════════════════════════════════════
# PLAYER endpoints
# ══════════════════════════════════════════════════════════════════════

async def search_player(player_name: str) -> Optional[Dict[str, Any]]:
    """Search for a player by name. Returns first match or None.

    Response fields of interest:
      idPlayer, strPlayer, strTeam, strCutout, strThumb, strRender,
      strPosition, strNationality, dateBorn
    """
    cache_key = f"player:{player_name.lower().strip()}"
    if cache_key in _player_cache:
        return _player_cache[cache_key]

    data = await _get("searchplayers.php", {"p": player_name})
    if not data or not data.get("player"):
        _player_cache[cache_key] = None
        return None

    player = data["player"][0]
    _player_cache[cache_key] = player
    return player


async def get_players_in_team(team_id: str) -> List[Dict[str, Any]]:
    """Get all players in a team by TheSportsDB team ID.

    Returns list of player dicts with photo fields.
    """
    cache_key = f"team_players:{team_id}"
    if cache_key in _player_cache:
        return _player_cache[cache_key]

    data = await _get("lookup_all_players.php", {"id": team_id})
    if not data or not data.get("player"):
        return []

    players = data["player"]
    _player_cache[cache_key] = players
    return players


async def get_players_by_team_name(team_name: str) -> List[Dict[str, Any]]:
    """Search players by team name.

    Note: on free tier this may be limited to 2 searches.
    """
    cache_key = f"team_players_name:{team_name.lower().strip()}"
    if cache_key in _player_cache:
        return _player_cache[cache_key]

    data = await _get("searchplayers.php", {"t": team_name})
    if not data or not data.get("player"):
        return []

    players = data["player"]
    _player_cache[cache_key] = players
    return players


# ══════════════════════════════════════════════════════════════════════
# HIGH-LEVEL HELPERS (for enrichment integration)
# ══════════════════════════════════════════════════════════════════════

def extract_team_badge(team_data: Dict[str, Any]) -> Optional[str]:
    """Extract the best badge/logo URL from a team response."""
    return (
        team_data.get("strTeamBadge")
        or team_data.get("strTeamLogo")
        or team_data.get("strTeamThumb")
    )


def extract_player_photo(player_data: Dict[str, Any]) -> Optional[str]:
    """Extract the best photo URL from a player response."""
    return (
        player_data.get("strCutout")
        or player_data.get("strThumb")
        or player_data.get("strRender")
    )


async def get_team_badge_and_players(
    team_name: str,
) -> Dict[str, Any]:
    """Get team badge + all squad player photos in one go.

    Returns:
        {
            "team_id": str or None,
            "team_name": str,
            "badge_url": str or None,
            "players": {player_name_lower: photo_url, ...},
            "api_calls": int,
        }
    """
    result: Dict[str, Any] = {
        "team_id": None,
        "team_name": team_name,
        "badge_url": None,
        "players": {},
        "api_calls": 0,
    }

    # 1. Search for the team
    team = await search_team(team_name)
    result["api_calls"] += 1

    if not team:
        return result

    team_id = team.get("idTeam")
    result["team_id"] = team_id
    result["badge_url"] = extract_team_badge(team)

    if not team_id:
        return result

    # 2. Get all players for this team
    players = await get_players_in_team(team_id)
    result["api_calls"] += 1

    for p in players:
        name = p.get("strPlayer", "")
        photo = extract_player_photo(p)
        if name and photo:
            result["players"][name.lower().strip()] = photo

    return result


def clear_cache():
    """Clear in-memory caches."""
    _team_cache.clear()
    _player_cache.clear()
