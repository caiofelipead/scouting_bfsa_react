"""
api_football.py — API-Football v3 integration service
======================================================
Provides async helpers to query the API-Football REST API.
Base URL: https://v3.football.api-sports.io
Auth: x-apisports-key header
All endpoints are GET-only.
"""

import os
import logging
from typing import Optional, Dict, Any, List

import aiohttp

logger = logging.getLogger(__name__)

API_FOOTBALL_BASE = "https://v3.football.api-sports.io"
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")


async def _request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make a GET request to API-Football v3."""
    if not API_FOOTBALL_KEY:
        raise ValueError("API_FOOTBALL_KEY environment variable is not set")

    url = f"{API_FOOTBALL_BASE}/{endpoint.lstrip('/')}"
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY,
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error("API-Football %s returned %d: %s", endpoint, resp.status, text[:500])
                raise ValueError(f"API-Football error {resp.status}: {text[:200]}")
            data = await resp.json()
            if data.get("errors") and len(data["errors"]) > 0:
                logger.warning("API-Football %s errors: %s", endpoint, data["errors"])
            return data


# ── Countries ──

async def get_countries() -> List[Dict[str, Any]]:
    data = await _request("/countries")
    return data.get("response", [])


# ── Leagues / Seasons ──

async def get_leagues(country: Optional[str] = None, season: Optional[int] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if country:
        params["country"] = country
    if season:
        params["season"] = season
    data = await _request("/leagues", params or None)
    return data.get("response", [])


async def get_league_seasons(league_id: int) -> List[int]:
    data = await _request("/leagues", {"id": league_id})
    items = data.get("response", [])
    if items:
        return [s["year"] for s in items[0].get("seasons", [])]
    return []


# ── Teams ──

async def get_teams(league_id: int, season: int) -> List[Dict[str, Any]]:
    data = await _request("/teams", {"league": league_id, "season": season})
    return data.get("response", [])


async def get_team_info(team_id: int) -> Optional[Dict[str, Any]]:
    data = await _request("/teams", {"id": team_id})
    items = data.get("response", [])
    return items[0] if items else None


# ── Players ──

async def get_players(
    league_id: Optional[int] = None,
    season: Optional[int] = None,
    team_id: Optional[int] = None,
    player_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"page": page}
    if league_id:
        params["league"] = league_id
    if season:
        params["season"] = season
    if team_id:
        params["team"] = team_id
    if player_id:
        params["id"] = player_id
    if search:
        params["search"] = search
    data = await _request("/players", params)
    return {
        "players": data.get("response", []),
        "paging": data.get("paging", {"current": 1, "total": 1}),
    }


async def get_squads(team_id: int) -> List[Dict[str, Any]]:
    data = await _request("/players/squads", {"team": team_id})
    return data.get("response", [])


async def get_top_scorers(league_id: int, season: int) -> List[Dict[str, Any]]:
    data = await _request("/players/topscorers", {"league": league_id, "season": season})
    return data.get("response", [])


async def get_top_assists(league_id: int, season: int) -> List[Dict[str, Any]]:
    data = await _request("/players/topassists", {"league": league_id, "season": season})
    return data.get("response", [])


# ── Standings ──

async def get_standings(league_id: int, season: int) -> List[Dict[str, Any]]:
    data = await _request("/standings", {"league": league_id, "season": season})
    items = data.get("response", [])
    if items:
        return items[0].get("league", {}).get("standings", [])
    return []


# ── Fixtures ──

async def get_fixtures(
    league_id: Optional[int] = None,
    season: Optional[int] = None,
    team_id: Optional[int] = None,
    date: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    status: Optional[str] = None,
    last: Optional[int] = None,
    next_n: Optional[int] = None,
    fixture_id: Optional[int] = None,
    round_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if league_id:
        params["league"] = league_id
    if season:
        params["season"] = season
    if team_id:
        params["team"] = team_id
    if date:
        params["date"] = date
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    if status:
        params["status"] = status
    if last:
        params["last"] = last
    if next_n:
        params["next"] = next_n
    if fixture_id:
        params["id"] = fixture_id
    if round_name:
        params["round"] = round_name
    data = await _request("/fixtures", params or None)
    return data.get("response", [])


async def get_fixture_statistics(fixture_id: int) -> List[Dict[str, Any]]:
    data = await _request("/fixtures/statistics", {"fixture": fixture_id})
    return data.get("response", [])


async def get_fixture_events(fixture_id: int) -> List[Dict[str, Any]]:
    data = await _request("/fixtures/events", {"fixture": fixture_id})
    return data.get("response", [])


async def get_fixture_lineups(fixture_id: int) -> List[Dict[str, Any]]:
    data = await _request("/fixtures/lineups", {"fixture": fixture_id})
    return data.get("response", [])


async def get_fixture_player_stats(fixture_id: int) -> List[Dict[str, Any]]:
    data = await _request("/fixtures/players", {"fixture": fixture_id})
    return data.get("response", [])


# ── Transfers ──

async def get_transfers(player_id: Optional[int] = None, team_id: Optional[int] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if player_id:
        params["player"] = player_id
    if team_id:
        params["team"] = team_id
    data = await _request("/transfers", params or None)
    return data.get("response", [])


# ── Coaches ──

async def get_coaches(team_id: Optional[int] = None, coach_id: Optional[int] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if team_id:
        params["team"] = team_id
    if coach_id:
        params["id"] = coach_id
    data = await _request("/coachs", params or None)
    return data.get("response", [])


# ── Injuries ──

async def get_injuries(
    league_id: Optional[int] = None,
    season: Optional[int] = None,
    fixture_id: Optional[int] = None,
    team_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if league_id:
        params["league"] = league_id
    if season:
        params["season"] = season
    if fixture_id:
        params["fixture"] = fixture_id
    if team_id:
        params["team"] = team_id
    data = await _request("/injuries", params or None)
    return data.get("response", [])


# ── Trophies ──

async def get_trophies(player_id: Optional[int] = None, coach_id: Optional[int] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if player_id:
        params["player"] = player_id
    if coach_id:
        params["coach"] = coach_id
    data = await _request("/trophies", params or None)
    return data.get("response", [])
