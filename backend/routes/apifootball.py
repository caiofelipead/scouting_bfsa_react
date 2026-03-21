"""API-Football v3 proxy routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from auth import get_current_user
from services.api_football import (
    get_countries as apif_get_countries,
    get_leagues as apif_get_leagues,
    get_league_seasons as apif_get_league_seasons,
    get_teams as apif_get_teams,
    get_team_info as apif_get_team_info,
    get_players as apif_get_players,
    get_squads as apif_get_squads,
    get_top_scorers as apif_get_top_scorers,
    get_top_assists as apif_get_top_assists,
    get_standings as apif_get_standings,
    get_fixtures as apif_get_fixtures,
    get_fixture_statistics as apif_get_fixture_statistics,
    get_fixture_events as apif_get_fixture_events,
    get_fixture_lineups as apif_get_fixture_lineups,
    get_fixture_player_stats as apif_get_fixture_player_stats,
    get_transfers as apif_get_transfers,
    get_coaches as apif_get_coaches,
    get_injuries as apif_get_injuries,
    get_trophies as apif_get_trophies,
)

router = APIRouter(prefix="/api/apifootball", tags=["apifootball"])


@router.get("/countries")
async def countries(_=Depends(get_current_user)):
    return await apif_get_countries()


@router.get("/leagues")
async def leagues(
    country: Optional[str] = Query(None),
    season: Optional[int] = Query(None),
    _=Depends(get_current_user),
):
    return await apif_get_leagues(country=country, season=season)


@router.get("/leagues/{league_id}/seasons")
async def league_seasons(league_id: int, _=Depends(get_current_user)):
    return await apif_get_league_seasons(league_id)


@router.get("/teams")
async def teams(
    league: int = Query(...),
    season: int = Query(...),
    _=Depends(get_current_user),
):
    return await apif_get_teams(league, season)


@router.get("/teams/{team_id}")
async def team_info(team_id: int, _=Depends(get_current_user)):
    info = await apif_get_team_info(team_id)
    if not info:
        raise HTTPException(status_code=404, detail="Team not found")
    return info


@router.get("/players")
async def players(
    league: Optional[int] = Query(None),
    season: Optional[int] = Query(None),
    team: Optional[int] = Query(None),
    player_id: Optional[int] = Query(None, alias="id"),
    search: Optional[str] = Query(None),
    page: int = Query(1),
    _=Depends(get_current_user),
):
    return await apif_get_players(
        league_id=league, season=season, team_id=team,
        player_id=player_id, search=search, page=page,
    )


@router.get("/squads/{team_id}")
async def squads(team_id: int, _=Depends(get_current_user)):
    return await apif_get_squads(team_id)


@router.get("/topscorers")
async def top_scorers(
    league: int = Query(...),
    season: int = Query(...),
    _=Depends(get_current_user),
):
    return await apif_get_top_scorers(league, season)


@router.get("/topassists")
async def top_assists(
    league: int = Query(...),
    season: int = Query(...),
    _=Depends(get_current_user),
):
    return await apif_get_top_assists(league, season)


@router.get("/standings")
async def standings(
    league: int = Query(...),
    season: int = Query(...),
    _=Depends(get_current_user),
):
    return await apif_get_standings(league, season)


@router.get("/fixtures")
async def fixtures(
    league: Optional[int] = Query(None),
    season: Optional[int] = Query(None),
    team: Optional[int] = Query(None),
    date: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    status: Optional[str] = Query(None),
    last: Optional[int] = Query(None),
    next_n: Optional[int] = Query(None, alias="next"),
    fixture_id: Optional[int] = Query(None, alias="id"),
    round_name: Optional[str] = Query(None, alias="round"),
    _=Depends(get_current_user),
):
    return await apif_get_fixtures(
        league_id=league, season=season, team_id=team,
        date=date, from_date=from_date, to_date=to_date,
        status=status, last=last, next_n=next_n,
        fixture_id=fixture_id, round_name=round_name,
    )


@router.get("/fixtures/{fixture_id}/statistics")
async def fixture_stats(fixture_id: int, _=Depends(get_current_user)):
    return await apif_get_fixture_statistics(fixture_id)


@router.get("/fixtures/{fixture_id}/events")
async def fixture_events(fixture_id: int, _=Depends(get_current_user)):
    return await apif_get_fixture_events(fixture_id)


@router.get("/fixtures/{fixture_id}/lineups")
async def fixture_lineups(fixture_id: int, _=Depends(get_current_user)):
    return await apif_get_fixture_lineups(fixture_id)


@router.get("/fixtures/{fixture_id}/players")
async def fixture_players(fixture_id: int, _=Depends(get_current_user)):
    return await apif_get_fixture_player_stats(fixture_id)


@router.get("/transfers")
async def transfers(
    player: Optional[int] = Query(None),
    team: Optional[int] = Query(None),
    _=Depends(get_current_user),
):
    return await apif_get_transfers(player_id=player, team_id=team)


@router.get("/coaches")
async def coaches(
    team: Optional[int] = Query(None),
    coach_id: Optional[int] = Query(None, alias="id"),
    _=Depends(get_current_user),
):
    return await apif_get_coaches(team_id=team, coach_id=coach_id)


@router.get("/injuries")
async def injuries(
    league: Optional[int] = Query(None),
    season: Optional[int] = Query(None),
    fixture: Optional[int] = Query(None),
    team: Optional[int] = Query(None),
    _=Depends(get_current_user),
):
    return await apif_get_injuries(
        league_id=league, season=season,
        fixture_id=fixture, team_id=team,
    )


@router.get("/trophies")
async def trophies(
    player: Optional[int] = Query(None),
    coach: Optional[int] = Query(None),
    _=Depends(get_current_user),
):
    return await apif_get_trophies(player_id=player, coach_id=coach)
