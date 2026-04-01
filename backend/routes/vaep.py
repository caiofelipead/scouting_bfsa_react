"""
VAEP & PlayeRank API routes.

These routes expose the VAEP action-valuation engine and PlayeRank
multi-dimensional player evaluation system.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth import get_current_user
from schemas.vaep import (
    VAEPPipelineRequest,
    VAEPPipelineResponse,
    VAEPRating,
    VAEPRatingsResponse,
    VAEPPlayerDetail,
    VAEPActionDetail,
    VAEPComparisonResponse,
    PlayeRankScore,
    PlayeRankRankingsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["vaep"])

# Lazy-initialized engine singletons
_vaep_engine = None
_playerank_engine = None


def _get_vaep_engine():
    global _vaep_engine
    if _vaep_engine is None:
        from services.vaep_engine import VAEPEngine
        _vaep_engine = VAEPEngine()
    return _vaep_engine


def _get_playerank_engine():
    global _playerank_engine
    if _playerank_engine is None:
        from services.playerank_engine import PlayeRankEngine
        _playerank_engine = PlayeRankEngine()
    return _playerank_engine


def _get_wyscout_data():
    """Access the in-memory Wyscout DataFrame from main module."""
    try:
        from main import _data, _ensure_data_loaded
        _ensure_data_loaded()
        return _data.get("wyscout")
    except Exception as e:
        logger.error("Could not access Wyscout data: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════════
# VAEP ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@router.post("/vaep/run-pipeline", response_model=VAEPPipelineResponse)
async def run_vaep_pipeline(req: VAEPPipelineRequest,
                            _=Depends(get_current_user)):
    """Execute VAEP pipeline. Computes action values and player ratings.

    Uses heuristic VAEP (from aggregate Wyscout stats) when event-level
    data is not available, or full VAEP (via socceraction) when it is.
    """
    df_wyscout = _get_wyscout_data()
    if df_wyscout is None or len(df_wyscout) == 0:
        raise HTTPException(status_code=404, detail="Dados Wyscout não disponíveis")

    engine = _get_vaep_engine()
    try:
        result = engine.run_pipeline(
            df_events=df_wyscout,
            season=req.season,
            competition_id=req.competition_id,
            df_wyscout=df_wyscout,
        )
    except Exception as e:
        logger.error("VAEP pipeline error: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro no pipeline VAEP: {str(e)}")

    # Persist results
    try:
        from services.database import (
            init_vaep_tables, save_vaep_ratings, save_vaep_actions,
        )
        init_vaep_tables()
        save_vaep_ratings(result["player_ratings"], req.season, req.competition_id)
        if result.get("action_records"):
            save_vaep_actions(result["action_records"], req.season, req.competition_id)
    except Exception as e:
        logger.warning("Could not persist VAEP results: %s", e)

    # Build response
    top_players = [
        VAEPRating(
            player_name=r["player_name"],
            team=r.get("team"),
            league=r.get("league"),
            position=r.get("position"),
            minutes_played=r.get("minutes_played", 0),
            total_vaep=r.get("total_vaep", 0),
            vaep_per90=r.get("vaep_per90", 0),
            offensive_vaep=r.get("offensive_vaep", 0),
            defensive_vaep=r.get("defensive_vaep", 0),
            actions_count=r.get("actions_count", 0),
            season=req.season,
        )
        for r in result["player_ratings"][:50]
    ]

    return VAEPPipelineResponse(
        season=req.season,
        method=result.get("method", "unknown"),
        total_players=len(result["player_ratings"]),
        total_actions=result.get("total_actions", 0),
        total_games=result.get("total_games", 0),
        top_players=top_players,
    )


@router.get("/vaep/ratings", response_model=VAEPRatingsResponse)
async def get_vaep_ratings(
    position: Optional[str] = Query(None),
    min_minutes: int = Query(0, ge=0),
    season: Optional[str] = Query(None),
    league: Optional[str] = Query(None),
    _=Depends(get_current_user),
):
    """Get pre-calculated VAEP ratings with optional filters."""
    # Try database first
    try:
        from services.database import load_vaep_ratings, init_vaep_tables
        init_vaep_tables()
        df = load_vaep_ratings(season, position, min_minutes, league)
        if len(df) > 0:
            ratings = [
                VAEPRating(
                    player_name=row["player_name"],
                    team=row.get("team"),
                    league=row.get("league"),
                    position=row.get("position"),
                    minutes_played=int(row.get("minutes_played", 0)),
                    total_vaep=float(row.get("total_vaep", 0)),
                    vaep_per90=float(row.get("vaep_per90", 0)),
                    offensive_vaep=float(row.get("offensive_vaep", 0)),
                    defensive_vaep=float(row.get("defensive_vaep", 0)),
                    actions_count=int(row.get("actions_count", 0)),
                    season=row.get("season"),
                )
                for _, row in df.iterrows()
            ]
            return VAEPRatingsResponse(total=len(ratings), season=season, ratings=ratings)
    except Exception as e:
        logger.debug("No VAEP ratings in DB: %s", e)

    # Compute on-the-fly from Wyscout data
    df_wyscout = _get_wyscout_data()
    if df_wyscout is None or len(df_wyscout) == 0:
        return VAEPRatingsResponse(total=0, season=season, ratings=[])

    engine = _get_vaep_engine()
    try:
        result = engine.run_pipeline(
            df_events=df_wyscout,
            season=season or "current",
            df_wyscout=df_wyscout,
        )
        all_ratings = result["player_ratings"]

        # Apply filters
        if position:
            all_ratings = [r for r in all_ratings
                          if r.get("position") and position.lower() in r["position"].lower()]
        if min_minutes > 0:
            all_ratings = [r for r in all_ratings if r.get("minutes_played", 0) >= min_minutes]
        if league:
            all_ratings = [r for r in all_ratings
                          if r.get("league") and league.lower() in r["league"].lower()]

        ratings = [
            VAEPRating(
                player_name=r["player_name"],
                team=r.get("team"),
                league=r.get("league"),
                position=r.get("position"),
                minutes_played=r.get("minutes_played", 0),
                total_vaep=r.get("total_vaep", 0),
                vaep_per90=r.get("vaep_per90", 0),
                offensive_vaep=r.get("offensive_vaep", 0),
                defensive_vaep=r.get("defensive_vaep", 0),
                season=season,
            )
            for r in all_ratings
        ]
        return VAEPRatingsResponse(total=len(ratings), season=season, ratings=ratings)
    except Exception as e:
        logger.error("Error computing VAEP ratings: %s", e)
        return VAEPRatingsResponse(total=0, season=season, ratings=[])


@router.get("/vaep/player/{player_name}", response_model=VAEPPlayerDetail)
async def get_vaep_player(player_name: str, season: Optional[str] = Query(None),
                          _=Depends(get_current_user)):
    """Get detailed VAEP data for a specific player."""
    df_wyscout = _get_wyscout_data()
    engine = _get_vaep_engine()

    rating = engine.get_player_vaep(player_name, df_wyscout, season)
    if not rating:
        raise HTTPException(status_code=404, detail=f"Jogador '{player_name}' não encontrado")

    # Load action details if available
    top_actions = []
    try:
        from services.database import load_vaep_actions_for_player
        actions_df = load_vaep_actions_for_player(player_name, season)
        if len(actions_df) > 0:
            # Top 20 highest-value actions
            actions_df = actions_df.sort_values("vaep_value", ascending=False).head(20)
            top_actions = [
                VAEPActionDetail(
                    action_type=row.get("action_type", ""),
                    vaep_value=float(row.get("vaep_value", 0)),
                    offensive_value=float(row.get("offensive_value", 0)),
                    defensive_value=float(row.get("defensive_value", 0)),
                    x_start=row.get("x_start"),
                    y_start=row.get("y_start"),
                    x_end=row.get("x_end"),
                    y_end=row.get("y_end"),
                    minute=row.get("minute"),
                    second=row.get("second"),
                )
                for _, row in actions_df.iterrows()
            ]
    except Exception:
        pass

    return VAEPPlayerDetail(
        player_name=rating.get("player_name", player_name),
        team=rating.get("team"),
        league=rating.get("league"),
        position=rating.get("position"),
        minutes_played=int(rating.get("minutes_played", 0)),
        total_vaep=float(rating.get("total_vaep", 0)),
        vaep_per90=float(rating.get("vaep_per90", 0)),
        offensive_vaep=float(rating.get("offensive_vaep", 0)),
        defensive_vaep=float(rating.get("defensive_vaep", 0)),
        actions_count=int(rating.get("actions_count", 0)),
        top_actions=top_actions,
        season=season,
    )


@router.get("/vaep/compare", response_model=VAEPComparisonResponse)
async def compare_vaep_players(
    player_ids: List[str] = Query(..., alias="player_names"),
    season: Optional[str] = Query(None),
    _=Depends(get_current_user),
):
    """Compare VAEP ratings between selected players."""
    if len(player_ids) < 2:
        raise HTTPException(status_code=400, detail="Mínimo 2 jogadores para comparação")
    if len(player_ids) > 10:
        raise HTTPException(status_code=400, detail="Máximo 10 jogadores para comparação")

    df_wyscout = _get_wyscout_data()
    engine = _get_vaep_engine()

    results = engine.get_player_comparison(player_ids, df_wyscout, season)
    players = [
        VAEPRating(
            player_name=r.get("player_name", ""),
            team=r.get("team"),
            league=r.get("league"),
            position=r.get("position"),
            minutes_played=int(r.get("minutes_played", 0)),
            total_vaep=float(r.get("total_vaep", 0)),
            vaep_per90=float(r.get("vaep_per90", 0)),
            offensive_vaep=float(r.get("offensive_vaep", 0)),
            defensive_vaep=float(r.get("defensive_vaep", 0)),
            season=season,
        )
        for r in results
    ]
    return VAEPComparisonResponse(players=players)


# ══════════════════════════════════════════════════════════════════════
# PLAYERANK ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@router.get("/playerank/rankings", response_model=PlayeRankRankingsResponse)
async def get_playerank_rankings(
    role_cluster: Optional[str] = Query(None),
    dimension: Optional[str] = Query(None),
    league: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    _=Depends(get_current_user),
):
    """Get PlayeRank rankings, optionally filtered by role cluster and dimension."""
    # Try database first
    try:
        from services.database import load_playerank_scores_db, init_vaep_tables
        init_vaep_tables()
        df = load_playerank_scores_db(season, role_cluster, dimension, league)
        if len(df) > 0:
            rankings = [
                PlayeRankScore(
                    player_name=row["player_name"],
                    team=row.get("team"),
                    league=row.get("league"),
                    position=row.get("position"),
                    role_cluster=row.get("role_cluster", "unknown"),
                    composite_score=float(row.get("composite_score", 0)),
                    dimensions={
                        "scoring": float(row.get("scoring_dim", 0)),
                        "playmaking": float(row.get("playmaking_dim", 0)),
                        "defending": float(row.get("defending_dim", 0)),
                        "physical": float(row.get("physical_dim", 0)),
                        "possession": float(row.get("possession_dim", 0)),
                    },
                    percentile_in_cluster=float(row.get("percentile_in_cluster", 0)),
                    cluster_size=int(row.get("cluster_size", 0)),
                    season=row.get("season"),
                )
                for _, row in df.iterrows()
            ]
            return PlayeRankRankingsResponse(
                total=len(rankings),
                role_cluster=role_cluster,
                season=season,
                rankings=rankings,
            )
    except Exception as e:
        logger.debug("No PlayeRank scores in DB: %s", e)

    # Compute on-the-fly
    df_wyscout = _get_wyscout_data()
    if df_wyscout is None or len(df_wyscout) == 0:
        return PlayeRankRankingsResponse(total=0, role_cluster=role_cluster,
                                          season=season, rankings=[])

    engine = _get_playerank_engine()

    # Get VAEP ratings if available
    vaep_ratings = None
    try:
        vaep_engine = _get_vaep_engine()
        vaep_result = vaep_engine.run_pipeline(
            df_events=df_wyscout,
            season=season or "current",
            df_wyscout=df_wyscout,
        )
        vaep_ratings = vaep_result.get("player_ratings")
    except Exception:
        pass

    try:
        scores = engine.compute_rankings(df_wyscout, vaep_ratings, season or "current")

        # Apply filters
        if role_cluster:
            scores = [s for s in scores if s["role_cluster"] == role_cluster]
        if league:
            scores = [s for s in scores
                     if s.get("league") and league.lower() in s["league"].lower()]

        # Persist results
        try:
            from services.database import save_playerank_scores, init_vaep_tables
            init_vaep_tables()
            save_playerank_scores(scores, season or "current")
        except Exception as e:
            logger.warning("Could not persist PlayeRank scores: %s", e)

        rankings = [
            PlayeRankScore(
                player_name=s["player_name"],
                team=s.get("team"),
                league=s.get("league"),
                position=s.get("position"),
                role_cluster=s.get("role_cluster", "unknown"),
                composite_score=s.get("composite_score", 0),
                dimensions={
                    "scoring": s.get("scoring_dim", 0),
                    "playmaking": s.get("playmaking_dim", 0),
                    "defending": s.get("defending_dim", 0),
                    "physical": s.get("physical_dim", 0),
                    "possession": s.get("possession_dim", 0),
                },
                percentile_in_cluster=s.get("percentile_in_cluster", 0),
                cluster_size=s.get("cluster_size", 0),
                season=season,
            )
            for s in scores
        ]

        return PlayeRankRankingsResponse(
            total=len(rankings),
            role_cluster=role_cluster,
            season=season,
            rankings=rankings,
        )
    except Exception as e:
        logger.error("Error computing PlayeRank: %s", e)
        return PlayeRankRankingsResponse(total=0, role_cluster=role_cluster,
                                          season=season, rankings=[])


# ══════════════════════════════════════════════════════════════════════
# ENRICHMENT (API-Football photos/logos)
# ══════════════════════════════════════════════════════════════════════

class EnrichmentStatusResponse(BaseModel):
    total_players: int = 0
    players_with_photo: int = 0
    total_teams: int = 0
    teams_with_logo: int = 0
    coverage_pct: float = 0.0


class EnrichmentTriggerResponse(BaseModel):
    message: str
    teams_queued: int = 0
    players_queued: int = 0


@router.get("/vaep/enrichment-status", response_model=EnrichmentStatusResponse)
async def vaep_enrichment_status(_=Depends(get_current_user)):
    """Check how many players/teams have photos from API-Football."""
    try:
        from services.enrichment import get_enrichment_stats
        stats = get_enrichment_stats()
        total_p = stats.get("total_players", 0)
        with_photo = stats.get("players_with_photo", 0)
        return EnrichmentStatusResponse(
            total_players=total_p,
            players_with_photo=with_photo,
            total_teams=stats.get("total_teams", 0),
            teams_with_logo=stats.get("teams_with_logo", 0),
            coverage_pct=round(with_photo / total_p * 100, 1) if total_p > 0 else 0,
        )
    except Exception as e:
        logger.error("Error getting enrichment stats: %s", e)
        return EnrichmentStatusResponse()


@router.post("/vaep/sync-photos", response_model=EnrichmentTriggerResponse)
async def sync_photos(
    max_api_calls: int = Query(default=90, le=100),
    _=Depends(get_current_user),
):
    """Trigger photo/logo enrichment from API-Football for all players in Wyscout data."""
    import asyncio
    df_wyscout = _get_wyscout_data()
    if df_wyscout is None or len(df_wyscout) == 0:
        raise HTTPException(status_code=404, detail="Dados Wyscout não disponíveis")

    # Build teams → players mapping
    teams_with_players: Dict[str, List[str]] = {}
    name_col = None
    team_col = None
    for c in df_wyscout.columns:
        cl = c.lower().strip()
        if cl in ("jogadordisplay", "jogador"):
            name_col = c
        if cl in ("equipa", "equipe", "team"):
            team_col = c

    if not name_col or not team_col:
        raise HTTPException(status_code=400, detail="Colunas de jogador/equipa não encontradas")

    for _, row in df_wyscout.iterrows():
        player = str(row.get(name_col, "")).strip()
        team = str(row.get(team_col, "")).strip()
        if player and team and player != "nan" and team != "nan":
            teams_with_players.setdefault(team, []).append(player)

    total_teams = len(teams_with_players)
    total_players = sum(len(v) for v in teams_with_players.values())

    # Run enrichment in background
    async def _run():
        try:
            from services.enrichment import run_bulk_enrichment
            result = await run_bulk_enrichment(
                teams_with_players, max_api_calls=max_api_calls,
            )
            logger.info("Photo sync complete: %s", result)
        except Exception as e:
            logger.error("Photo sync error: %s", e)

    asyncio.create_task(_run())

    return EnrichmentTriggerResponse(
        message=f"Sincronização de fotos iniciada para {total_teams} equipes e {total_players} jogadores",
        teams_queued=total_teams,
        players_queued=total_players,
    )
