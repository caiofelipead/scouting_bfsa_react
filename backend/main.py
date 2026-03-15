"""
main.py — FastAPI Scouting API for Botafogo-SP
===============================================
Replaces the Streamlit monolith with async REST endpoints.
"""

import os
import time
import hashlib
import logging
import threading
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

import numpy as np
import pandas as pd
import aiohttp
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from auth import (
    authenticate_user,
    create_access_token,
    create_user,
    delete_user,
    get_current_user,
    init_db,
    list_users,
    require_admin,
)
from schemas.models import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserOut,
    PlayerProfile,
    PlayerSummary,
    RankingEntry,
    RankingRequest,
    RankingResponse,
    SimilarityRequest,
    SimilarityResponse,
    SimilarPlayer,
    SimilarityBreakdown,
    RadarData,
    PositionConfig,
    TrajectoryRequest,
    TrajectoryResponse,
    MarketOpportunitiesRequest,
    MarketOpportunitiesResponse,
    MarketOpportunityEntry,
    ReplacementRequest,
    ReplacementEntry,
    ReplacementResponse,
    ContractImpactRequest,
    ContractImpactResponse,
)
from services.similarity import (
    INVERTED_METRICS,
    POSITION_WEIGHTS,
    calculate_all_indices,
    calculate_metric_percentiles,
    calculate_overall_score,
    compute_weighted_cosine_similarity,
    get_similarity_breakdown,
    get_top_metrics_for_position,
    rank_players_weighted,
)
from services.calibration import (
    SSP_LAMBDAS,
    classify_performance,
    get_calibrated_wp_weights,
)
from services.predictive_engine import ContractSuccessPredictor
from services.scouting_intelligence import (
    ScoutingIntelligenceEngine,
    PlayerTrajectoryModel,
    MarketOpportunityDetector,
    PlayerReplacementEngine,
    TemporalPerformanceTrend,
    LeagueStrengthAdjuster,
)
from services.league_power_model import get_opta_league_power, get_all_league_powers
from services.fuzzy_match import build_skillcorner_index, find_skillcorner_player
from services.player_assets import load_player_assets_csv, get_player_assets
from services.database import init_scouting_tables, load_sheet_dataframe, has_data, get_sync_status
from services.sync_sheets import sync_all_sheets
from config.mappings import (
    CLUB_LEAGUE_MAP,
    CLUB_LOGOS,
    COUNTRY_FLAGS,
    INDICES_CONFIG,
    LEAGUE_LOGOS,
    POSICAO_MAP,
    POSICOES_DISPLAY,
    SKILLCORNER_INDICES,
    WYSCOUT_LEAGUE_MAP,
    _CLUB_LEAGUE_MAP_NORM,
    get_posicao_categoria,
    padronizar_string,
    resolve_league_to_tier,
)

logger = logging.getLogger(__name__)


_unmapped_clubs: set = set()  # Track clubs not found in CLUB_LEAGUE_MAP


def resolve_actual_league(team_name: str, fallback_liga_tier: str = None) -> str:
    """Resolve a player's actual current league based on their club name.

    The WyScout data often has the scouting pool league (e.g. 'Brasil | 2')
    in the Liga column, which is the same for all players in the dataset.
    For GAP calculation we need the player's REAL current league.

    Priority: CLUB_LEAGUE_MAP (exact) → normalized → fallback_liga_tier → default.
    """
    if team_name and pd.notna(team_name):
        team_str = str(team_name).strip()
        # Exact match
        if team_str in CLUB_LEAGUE_MAP:
            return CLUB_LEAGUE_MAP[team_str]
        # Normalized match
        team_norm = padronizar_string(team_str)
        if team_norm in _CLUB_LEAGUE_MAP_NORM:
            return _CLUB_LEAGUE_MAP_NORM[team_norm]
        # Track unmapped club
        if team_str not in _unmapped_clubs:
            _unmapped_clubs.add(team_str)
            logger.warning("Unmapped club '%s' — using fallback league", team_str)
    # Fallback to the liga_tier column (scouting pool league)
    if fallback_liga_tier and pd.notna(fallback_liga_tier):
        return str(fallback_liga_tier)
    return None


# ── Simple TTL cache for heavy endpoint results ──────────────────────

class _TTLCache:
    """Minimal in-memory cache with time-based expiry (no dependencies)."""

    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._store: Dict[str, tuple] = {}  # key -> (timestamp, value)

    def get(self, key: str):
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, val = entry
        if time.time() - ts > self.ttl:
            del self._store[key]
            return None
        return val

    def set(self, key: str, value):
        self._store[key] = (time.time(), value)

    def make_key(self, *args) -> str:
        raw = "|".join(str(a) for a in args)
        return hashlib.md5(raw.encode()).hexdigest()

    def clear(self):
        self._store.clear()


_endpoint_cache = _TTLCache(ttl_seconds=300)  # 5 min cache


# ── In-memory data store (loaded on startup) ─────────────────────────

_data: Dict[str, pd.DataFrame] = {}

SHEET_KEYS = ["analises", "oferecidos", "skillcorner", "wyscout"]


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, float) and np.isnan(val):
        return None
    try:
        if isinstance(val, str):
            val = val.replace(",", ".")
        return float(val)
    except (ValueError, TypeError):
        return None


def _coerce_numeric_columns(df: pd.DataFrame, exclude_cols: set) -> pd.DataFrame:
    """Convert string columns to numeric where possible."""
    for col in df.columns:
        if col in exclude_cols:
            continue
        try:
            cleaned = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace(",", ".", regex=False)
                .str.replace(r"[^\d.\-]", "", regex=True)
            )
            numeric = pd.to_numeric(cleaned, errors="coerce")
            if numeric.notna().sum() > len(df) * 0.3:
                df[col] = numeric
        except Exception:
            pass
    return df


def _prepare_wyscout(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare WyScout DataFrame with display names and numeric coercion."""
    text_cols = {"Jogador", "Equipa", "Posição", "Naturalidade", "Pé", "Liga", "Competição", "JogadorDisplay"}
    df = _coerce_numeric_columns(df, text_cols)

    if "Jogador" in df.columns and "Equipa" in df.columns:
        df["JogadorDisplay"] = df.apply(
            lambda r: f"{r['Jogador']} ({r['Equipa']})" if pd.notna(r.get("Equipa")) else str(r["Jogador"]),
            axis=1,
        )

    if "Liga" in df.columns:
        df["liga_tier"] = df.apply(
            lambda r: resolve_league_to_tier(r.get("Liga"), r.get("Equipa")),
            axis=1,
        )
    return df


_data_ready = threading.Event()
_data_loading = False
_data_lock = threading.Lock()


def _load_all_data():
    """Load all data into memory — tries PostgreSQL first, syncs from Sheets if empty."""
    global _data, _data_loading

    # Ensure scouting tables exist
    try:
        init_scouting_tables()
    except Exception as e:
        logger.warning("Could not init scouting tables: %s", e)

    # Check if PostgreSQL has data
    pg_has_data = False
    try:
        pg_has_data = has_data()
    except Exception as e:
        logger.warning("Could not check PostgreSQL for data: %s", e)

    if not pg_has_data:
        # First run or empty DB — sync from Google Sheets → PostgreSQL
        logger.info("No data in PostgreSQL — syncing from Google Sheets...")
        try:
            sync_results = sync_all_sheets()
            logger.info("Initial sync results: %s", sync_results)
        except Exception as e:
            logger.error("Initial sync from Google Sheets failed: %s", e)

    # Load from PostgreSQL (fast ~50-200ms per table)
    for key in SHEET_KEYS:
        try:
            df = load_sheet_dataframe(key)
            _data[key] = df
            logger.info("Loaded '%s' from PostgreSQL: %d rows", key, len(df))
        except Exception as e:
            logger.error("Failed to load '%s' from PostgreSQL: %s", key, e)
            _data[key] = pd.DataFrame()

    if "wyscout" in _data and len(_data["wyscout"]) > 0:
        _data["wyscout"] = _prepare_wyscout(_data["wyscout"])

    if "skillcorner" in _data and len(_data["skillcorner"]) > 0:
        sc_text = {"player_name", "short_name", "team_name", "position_group"}
        _data["skillcorner"] = _coerce_numeric_columns(_data["skillcorner"], sc_text)
        build_skillcorner_index(_data["skillcorner"])

    # Pre-warm percentile cache for wyscout (biggest dataset)
    if "wyscout" in _data and len(_data["wyscout"]) > 0:
        from services.similarity import _get_percentile_matrix
        _get_percentile_matrix(_data["wyscout"])

    # Load player assets CSV (photos, club logos, league logos)
    try:
        load_player_assets_csv()
    except Exception as e:
        logger.warning("Could not load player assets CSV: %s", e)

    _data_ready.set()
    _data_loading = False
    logger.info("All data loaded successfully: %s", {k: len(v) for k, v in _data.items()})


def _ensure_data_loaded():
    """Trigger background loading if not started, wait up to 55s for data."""
    global _data_loading

    if _data_ready.is_set():
        return  # data already loaded

    with _data_lock:
        if not _data_loading:
            _data_loading = True
            t = threading.Thread(target=_load_all_data, daemon=True)
            t.start()

    # Wait for data with a timeout (Render free tier has 60s request limit)
    if not _data_ready.wait(timeout=55):
        raise HTTPException(
            status_code=503,
            detail="Dados ainda carregando. Tente novamente em alguns segundos.",
        )


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Start data loading in background — don't block app startup
    # Now loads from PostgreSQL (fast) with auto-sync from Sheets if DB is empty
    global _data_loading
    with _data_lock:
        _data_loading = True
        t = threading.Thread(target=_load_all_data, daemon=True)
        t.start()
    yield


# ── App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Scouting BFSA API",
    description="Backend API for the Botafogo-SP Scouting Dashboard",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    """Health check — returns quickly even during cold start."""
    ready = _data_ready.is_set()
    counts = {k: len(v) for k, v in _data.items()} if ready else {}

    # Database diagnostics
    db_diag = {}
    from services.database import DATABASE_URL
    db_diag["database_url_set"] = bool(DATABASE_URL)
    db_diag["database_url_preview"] = (DATABASE_URL[:30] + "...") if DATABASE_URL else "(empty)"
    try:
        from services.database import get_connection
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM scouting_rows")
            db_diag["scouting_rows_count"] = cur.fetchone()[0]
            cur.execute("SELECT sheet_key, COUNT(*) FROM scouting_rows GROUP BY sheet_key")
            db_diag["rows_per_sheet"] = {r[0]: r[1] for r in cur.fetchall()}
        conn.close()
        db_diag["connection"] = "ok"
    except Exception as e:
        db_diag["connection"] = f"error: {e}"

    sc_diag = None
    if ready:
        sc_df = _data.get("skillcorner")
        ws_df = _data.get("wyscout")
        if sc_df is not None and len(sc_df) > 0:
            sc_diag = {
                "columns": list(sc_df.columns),
                "sample_players": [
                    {col: (str(row[col]) if pd.notna(row.get(col)) else None) for col in ["player_name", "short_name", "team_name"] if col in sc_df.columns}
                    for _, row in sc_df.head(5).iterrows()
                ],
            }
            if ws_df is not None and len(ws_df) > 0:
                ws_sample = [
                    str(r.get("Jogador", "")) for _, r in ws_df.head(5).iterrows()
                ]
                sc_diag["wyscout_sample_names"] = ws_sample
                # Try matching first wyscout player
                try:
                    test_name = str(ws_df.iloc[0].get("Jogador", ""))
                    test_team = str(ws_df.iloc[0].get("Equipa", "")) if pd.notna(ws_df.iloc[0].get("Equipa")) else None
                    test_match = find_skillcorner_player(test_name, sc_df, team_name=test_team)
                    sc_diag["test_match"] = {
                        "searched": test_name,
                        "team": test_team,
                        "found": test_match is not None,
                        "matched_name": str(test_match.get("player_name", "")) if test_match is not None else None,
                    }
                except Exception as e:
                    sc_diag["test_match_error"] = str(e)
    return {
        "status": "ready" if ready else "loading",
        "data_loaded": ready,
        "counts": counts,
        "database": db_diag,
        "skillcorner_diagnostic": sc_diag,
    }


@app.post("/api/admin/resync")
async def admin_resync(current_user: dict = Depends(require_admin)):
    """Force re-sync all sheets from Google Sheets → PostgreSQL and reload into memory."""
    global _data

    # Step 1: Sync from Google Sheets → PostgreSQL
    sync_results = sync_all_sheets()

    # Step 2: Reload from PostgreSQL into memory
    for key in SHEET_KEYS:
        try:
            df = load_sheet_dataframe(key)
            _data[key] = df
        except Exception as e:
            logger.error("Failed to reload '%s': %s", key, e)
            _data[key] = pd.DataFrame()

    if "wyscout" in _data and len(_data["wyscout"]) > 0:
        _data["wyscout"] = _prepare_wyscout(_data["wyscout"])

    if "skillcorner" in _data and len(_data["skillcorner"]) > 0:
        sc_text = {"player_name", "short_name", "team_name", "position_group"}
        _data["skillcorner"] = _coerce_numeric_columns(_data["skillcorner"], sc_text)
        build_skillcorner_index(_data["skillcorner"])

    _data_ready.set()

    counts = {k: len(v) for k, v in _data.items()}
    return {"sync_results": sync_results, "memory_counts": counts}


# ══════════════════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
    token = create_access_token({"sub": user["email"], "role": user["role"], "name": user["name"]})
    return TokenResponse(
        access_token=token,
        user=UserOut(**user),
    )


@app.get("/api/auth/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(id=0, **current_user)


@app.get("/api/admin/users")
async def admin_list_users(admin: dict = Depends(require_admin)):
    return list_users()


@app.post("/api/admin/users")
async def admin_create_user(req: UserCreate, admin: dict = Depends(require_admin)):
    err = create_user(req.email, req.password, req.name, req.role)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"message": f"Usuário {req.email} cadastrado com sucesso"}


@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: int, admin: dict = Depends(require_admin)):
    err = delete_user(user_id)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"message": "Usuário removido"}


# ══════════════════════════════════════════════════════════════════════
# CONFIG / MAPPINGS ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/config/positions")
async def get_positions(current_user: dict = Depends(get_current_user)):
    return {
        "positions": POSICOES_DISPLAY,
        "position_map": POSICAO_MAP,
        "indices": {k: {ik: iv for ik, iv in v.items()} for k, v in INDICES_CONFIG.items()},
        "skillcorner_indices": SKILLCORNER_INDICES,
    }


@app.get("/api/config/leagues")
async def get_leagues(current_user: dict = Depends(get_current_user)):
    _ensure_data_loaded()
    leagues = set()
    if "wyscout" in _data and "liga_tier" in _data["wyscout"].columns:
        leagues = set(_data["wyscout"]["liga_tier"].dropna().unique())
    return {
        "leagues": sorted(leagues),
        "league_logos": LEAGUE_LOGOS,
    }


@app.get("/api/config/analises-debug")
async def analises_debug(current_user: dict = Depends(get_current_user)):
    """Debug endpoint: show análises columns and first few player names."""
    _ensure_data_loaded()
    df = _data.get("analises")
    if df is None:
        return {"status": "no_data", "columns": [], "names": [], "rows": 0}
    cols = list(df.columns)
    names = []
    if "Nome" in df.columns:
        names = [str(v) for v in df["Nome"].dropna().head(20).tolist()]
    return {"status": "ok", "columns": cols, "names": names, "rows": len(df)}


@app.get("/api/config/mappings")
async def get_mappings(current_user: dict = Depends(get_current_user)):
    return {
        "country_flags": COUNTRY_FLAGS,
        "club_logos": CLUB_LOGOS,
        "league_logos": LEAGUE_LOGOS,
        "position_weights": POSITION_WEIGHTS,
        "ssp_lambdas": SSP_LAMBDAS,
    }


# ══════════════════════════════════════════════════════════════════════
# DATA RELOAD
# ══════════════════════════════════════════════════════════════════════

@app.post("/api/data/reload")
async def reload_data(admin: dict = Depends(require_admin)):
    """Reload data: sync Google Sheets → PostgreSQL, then reload into memory."""
    _data_ready.clear()
    _endpoint_cache.clear()
    # Sync fresh data from Sheets → PG
    try:
        sync_results = sync_all_sheets()
    except Exception as e:
        logger.error("Sync failed during reload: %s", e)
        sync_results = {}
    # Reload from PG into memory
    _load_all_data()
    return {
        "message": "Dados sincronizados e recarregados",
        "sync_results": sync_results,
        "counts": {k: len(v) for k, v in _data.items()},
    }


@app.get("/api/skillcorner/search")
async def search_skillcorner_players(
    q: str = "",
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """Search SkillCorner players by name for manual selection."""
    _ensure_data_loaded()
    sc_df = _data.get("skillcorner")
    if sc_df is None or len(sc_df) == 0:
        return {"results": []}

    results = []
    if q.strip():
        q_lower = q.strip().lower()
        for _, row in sc_df.iterrows():
            pname = str(row.get("player_name", "")) if pd.notna(row.get("player_name")) else ""
            sname = str(row.get("short_name", "")) if pd.notna(row.get("short_name")) else ""
            tname = str(row.get("team_name", "")) if pd.notna(row.get("team_name")) else ""
            if q_lower in pname.lower() or q_lower in sname.lower():
                results.append({
                    "player_name": pname,
                    "short_name": sname,
                    "team_name": tname,
                    "position_group": str(row.get("position_group", "")) if pd.notna(row.get("position_group")) else None,
                })
                if len(results) >= limit:
                    break

    return {"results": results}


@app.post("/api/data/sync")
async def sync_data(admin: dict = Depends(require_admin)):
    """Sync Google Sheets → PostgreSQL without reloading memory."""
    try:
        sync_results = sync_all_sheets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}")
    return {
        "message": "Dados sincronizados no banco",
        "sync_results": sync_results,
    }


@app.get("/api/data/sync-status")
async def data_sync_status(admin: dict = Depends(require_admin)):
    """Return the last sync timestamps for each sheet."""
    try:
        status = get_sync_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not get sync status: {e}")
    return {"sync_status": status}


@app.get("/api/data/unmapped-clubs")
async def get_unmapped_clubs(admin: dict = Depends(require_admin)):
    """Return clubs found in data that aren't in CLUB_LEAGUE_MAP."""
    _ensure_data_loaded()
    # Also scan full wyscout dataset for comprehensive list
    df = _data.get("wyscout")
    all_unmapped = set(_unmapped_clubs)
    if df is not None and "Equipa" in df.columns:
        for team in df["Equipa"].dropna().unique():
            team_str = str(team).strip()
            team_norm = padronizar_string(team_str)
            if team_str not in CLUB_LEAGUE_MAP and team_norm not in _CLUB_LEAGUE_MAP_NORM:
                all_unmapped.add(team_str)
    return {
        "unmapped_clubs": sorted(all_unmapped),
        "count": len(all_unmapped),
        "total_mapped": len(CLUB_LEAGUE_MAP),
    }


# ══════════════════════════════════════════════════════════════════════
# PLAYER ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

def _get_wyscout() -> pd.DataFrame:
    _ensure_data_loaded()
    df = _data.get("wyscout")
    if df is None or len(df) == 0:
        raise HTTPException(status_code=503, detail="Dados WyScout não carregados")
    return df


@app.get("/api/players")
async def list_players(
    position: Optional[str] = None,
    league: Optional[str] = None,
    search: Optional[str] = None,
    min_minutes: int = 0,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    df = _get_wyscout()
    df_all = df  # keep full df for score calculation

    if position:
        cat = get_posicao_categoria(position)
        if "Posição" in df.columns:
            df = df[df["Posição"].apply(lambda p: get_posicao_categoria(p) == cat if pd.notna(p) else False)]

    if league and "liga_tier" in df.columns:
        df = df[df["liga_tier"] == league]

    if min_minutes > 0 and "Minutos jogados:" in df.columns:
        df["_min"] = df["Minutos jogados:"].apply(_safe_float)
        df = df[df["_min"] >= min_minutes]

    if min_age is not None and "Idade" in df.columns:
        df = df[df["Idade"].apply(lambda a: _safe_float(a) is not None and _safe_float(a) >= min_age)]

    if max_age is not None and "Idade" in df.columns:
        df = df[df["Idade"].apply(lambda a: _safe_float(a) is not None and _safe_float(a) <= max_age)]

    if search and "JogadorDisplay" in df.columns:
        search_lower = search.lower()
        df = df[df["JogadorDisplay"].str.lower().str.contains(search_lower, na=False)]

    total = len(df)
    df = df.iloc[offset: offset + limit]

    # Pre-compute percentile matrix for fast scoring
    from services.similarity import _get_percentile_matrix
    perc_matrix = _get_percentile_matrix(df_all)

    players = []
    for idx, row in df.iterrows():
        pos_raw = str(row.get("Posição", "")) if pd.notna(row.get("Posição")) else None
        pos_cat = get_posicao_categoria(pos_raw) if pos_raw else None
        score = calculate_overall_score(row, pos_cat, df_all, _perc_matrix=perc_matrix) if pos_cat else None

        # Get photo, club logo, and league logo from asset service
        player_name = str(row.get("Jogador", ""))
        team_name = str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None
        assets = get_player_assets(player_name, team_name)

        # Fallback: try DataFrame columns for photo_url
        photo_url = assets.get("photo_url")
        if not photo_url:
            for photo_col in ("photo_url", "Foto", "ImageDataURL", "image_url"):
                val = row.get(photo_col)
                if val is not None and pd.notna(val) and str(val).strip():
                    photo_url = str(val).strip()
                    break

        # Fallback: hardcoded CLUB_LOGOS for club_logo
        club_logo = assets.get("club_logo")
        if not club_logo and team_name:
            club_logo = CLUB_LOGOS.get(team_name)

        players.append({
            "id": int(idx) if isinstance(idx, (int, np.integer)) else hash(str(idx)) % 10**8,
            "name": player_name,
            "display_name": str(row.get("JogadorDisplay", row.get("Jogador", ""))),
            "team": team_name,
            "club_logo": club_logo,
            "league_logo": assets.get("league_logo"),
            "position": pos_raw,
            "age": _safe_float(row.get("Idade")),
            "nationality": str(row.get("Naturalidade", "")) if pd.notna(row.get("Naturalidade")) else None,
            "league": resolve_actual_league(
                row.get("Equipa"),
                fallback_liga_tier=str(row.get("liga_tier", "")) if pd.notna(row.get("liga_tier")) else None,
            ),
            "minutes_played": _safe_float(row.get("Minutos jogados:")),
            "photo_url": photo_url,
            "score": round(score, 1) if score else None,
        })

    return {"total": total, "players": players}


@app.get("/api/players/{player_display_name}/profile")
async def get_player_profile(
    player_display_name: str,
    sc_override: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    df = _get_wyscout()
    if "JogadorDisplay" not in df.columns:
        raise HTTPException(status_code=404, detail="Coluna JogadorDisplay não encontrada")

    mask = df["JogadorDisplay"] == player_display_name
    if mask.sum() == 0:
        mask = df["JogadorDisplay"].str.lower() == player_display_name.lower()
    if mask.sum() == 0:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    row = df[mask].iloc[0]
    position_raw = str(row.get("Posição", "")) if pd.notna(row.get("Posição")) else "Meia"
    position = get_posicao_categoria(position_raw)

    # Percentiles for radar
    percentiles = calculate_metric_percentiles(row, position, df, top_n=12)

    # Composite indices
    pos_indices = INDICES_CONFIG.get(position, {})
    indices = calculate_all_indices(row, pos_indices, df, position)
    indices = {k: round(v, 1) for k, v in indices.items()}

    # Overall score
    score = calculate_overall_score(row, position, df)
    perf_class = classify_performance(score) if score else None

    # SkillCorner match
    sc_data = None
    sc_physical = None
    sc_debug = None
    sc_df = _data.get("skillcorner")
    jogador_name = str(row.get("Jogador", ""))
    team_name_sc = str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None
    sc_rows = len(sc_df) if sc_df is not None else 0
    if sc_df is not None and sc_rows > 0:
        # Manual override: user selected a SkillCorner player by name
        if sc_override and "player_name" in sc_df.columns:
            override_mask = sc_df["player_name"] == sc_override
            if override_mask.sum() > 0:
                sc_match = sc_df[override_mask].iloc[0]
            else:
                sc_match = find_skillcorner_player(jogador_name, sc_df, team_name=team_name_sc)
        else:
            sc_match = find_skillcorner_player(jogador_name, sc_df, team_name=team_name_sc)
        if sc_match is not None:
            sc_matched_name = str(sc_match.get("player_name", ""))
            sc_indices = SKILLCORNER_INDICES.get(position, [])
            sc_data = {}
            for idx_name in sc_indices:
                val = _safe_float(sc_match.get(idx_name))
                if val is not None:
                    sc_data[idx_name] = round(val, 2)
            # Physical performance columns
            _SC_PHYSICAL_COLS = {
                "sprint_count_per_90": "Sprints/90",
                "hi_count_per_90": "High Intensity Runs/90",
                "distance_per_90": "Distance/90",
                "avg_psv99": "Avg PSV-99",
                "avg_top_5_psv99": "Avg Top 5 PSV-99",
            }
            sc_physical = {}
            for col, label in _SC_PHYSICAL_COLS.items():
                val = _safe_float(sc_match.get(col))
                if val is not None:
                    sc_physical[label] = round(val, 2)
            sc_debug = {
                "sc_total_rows": sc_rows,
                "match_found": True,
                "matched_name": sc_matched_name,
                "indices_found": len(sc_data),
                "physical_found": len(sc_physical),
            }
        else:
            sc_debug = {
                "sc_total_rows": sc_rows,
                "match_found": False,
                "searched_name": jogador_name,
                "searched_team": team_name_sc,
            }
    else:
        sc_debug = {
            "sc_total_rows": sc_rows,
            "match_found": False,
            "reason": "skillcorner_dataframe_empty",
        }

    # Collect numeric metrics
    metrics = {}
    for col in df.columns:
        val = _safe_float(row.get(col))
        if val is not None and col not in {"Idade"}:
            metrics[col] = round(val, 2)

    idx_val = int(row.name) if isinstance(row.name, (int, np.integer)) else hash(str(row.name)) % 10**8

    # Projection score (PDI) — young + high score = high resale potential
    age = _safe_float(row.get("Idade"))
    projection_score = None
    if score is not None and age is not None and age > 0:
        # Age factor: peaks at 19, linear decay until 35
        age_factor = max(0, min(1.0, (35 - age) / 16))
        projection_score = round(score * 0.6 + score * age_factor * 0.4, 1)

    # P(Sucesso) prediction using ContractSuccessPredictor + LEAGUE_TIERS
    prediction = None
    liga_tier_raw = str(row.get("liga_tier", "")) if pd.notna(row.get("liga_tier")) else None
    league_actual = resolve_actual_league(row.get("Equipa"), fallback_liga_tier=liga_tier_raw)
    minutes_val = _safe_float(row.get("Minutos jogados:")) or 0
    if score is not None and age is not None and league_actual:
        predictor = ContractSuccessPredictor()
        prediction = predictor.predict_success_unsupervised(
            ssp_score=score,
            age=age,
            league_origin=league_actual,
            league_target="Serie B Brasil",  # Botafogo-SP target league
            minutes=minutes_val,
        )

    # ── Análises match ──
    analises_data = None
    ana_match = None  # define at top scope so photo fallback can use it
    analises_df = _data.get("analises")
    if analises_df is not None and len(analises_df) > 0 and "Nome" in analises_df.columns:
        from rapidfuzz import fuzz as _fuzz

        # Names to try matching against (display name, raw name, the URL param)
        _names_to_try = list(dict.fromkeys(filter(None, [
            player_display_name,
            jogador_name,
            str(row.get("JogadorDisplay", "")),
        ])))

        # 1) Try exact match on any candidate name
        for _candidate in _names_to_try:
            ana_mask = analises_df["Nome"].str.strip().str.lower() == _candidate.strip().lower()
            if ana_mask.sum() > 0:
                ana_match = analises_df[ana_mask].iloc[0]
                break

        # 2) Fuzzy match if no exact match found
        if ana_match is None:
            # Get player team from WyScout row for disambiguation
            _player_team = str(row.get("Equipa", "")).strip().lower() if pd.notna(row.get("Equipa")) else ""

            best_score = 0.0
            best_idx = None
            for _candidate in _names_to_try:
                name_norm = _candidate.strip().lower()
                if not name_norm:
                    continue
                for aidx, arow in analises_df.iterrows():
                    aname = str(arow.get("Nome", "")).strip().lower()
                    if not aname:
                        continue
                    sim = max(
                        _fuzz.ratio(name_norm, aname) / 100.0,
                        _fuzz.token_sort_ratio(name_norm, aname) / 100.0,
                    )
                    # Containment bonus — only when one name fully contains the other
                    # and the shorter name has at least 4 chars (avoid partial matches)
                    shorter = min(len(name_norm), len(aname))
                    if shorter >= 4 and (name_norm in aname or aname in name_norm):
                        sim = max(sim, 0.85)
                    # Team boost: if análises row has a team column matching WyScout team
                    if _player_team:
                        _ana_team = ""
                        for _tc in ("Equipe", "equipe", "Clube", "clube", "Time", "time"):
                            _tv = arow.get(_tc)
                            if _tv is not None and pd.notna(_tv) and str(_tv).strip():
                                _ana_team = str(_tv).strip().lower()
                                break
                        if _ana_team and (_ana_team in _player_team or _player_team in _ana_team):
                            sim += 0.10
                    if sim > best_score:
                        best_score = sim
                        best_idx = aidx
            if best_idx is not None and best_score >= 0.78:
                ana_match = analises_df.loc[best_idx]
                logger.info(
                    "Análises fuzzy match for '%s': matched '%s' (score=%.2f)",
                    player_display_name,
                    ana_match.get("Nome", "?"),
                    best_score,
                )

        if ana_match is not None:
            # Score columns
            _SCORE_COLS = ["Técnica", "Físico", "Tática", "Mental", "Nota_Desempenho", "Potencial"]
            scores = {}
            for col in _SCORE_COLS:
                val = _safe_float(ana_match.get(col))
                if val is not None:
                    scores[col] = round(val, 2)

            # Link columns
            _LINK_COLS = ["ogol", "TM", "Vídeo", "Relatório"]
            links = {}
            for col in _LINK_COLS:
                val = ana_match.get(col)
                if val is not None and pd.notna(val) and str(val).strip():
                    links[col] = str(val).strip()

            # Text/metadata columns
            analysis_text = None
            val = ana_match.get("Análise")
            if val is not None and pd.notna(val) and str(val).strip():
                analysis_text = str(val).strip()

            modelo = None
            val = ana_match.get("Modelo")
            if val is not None and pd.notna(val) and str(val).strip():
                modelo = str(val).strip()

            faixa_salarial = None
            for _faixa_col in ("Faixa salarial", "faixa salarial", "Faixa Salarial"):
                val = ana_match.get(_faixa_col)
                if val is not None and pd.notna(val) and str(val).strip():
                    faixa_salarial = str(val).strip()
                    break

            transfer_luvas = None
            val = ana_match.get("Transfer/Luvas")
            if val is not None and pd.notna(val) and str(val).strip():
                transfer_luvas = str(val).strip()

            analises_data = {
                "nome": str(ana_match.get("Nome", "")),
                "scores": scores,
                "links": links,
                "analysis_text": analysis_text,
                "modelo": modelo,
                "faixa_salarial": faixa_salarial,
                "transfer_luvas": transfer_luvas,
            }
            logger.debug("Análises match for '%s': found '%s'", player_display_name, ana_match.get("Nome"))

    # Get photo, club logo, and league logo from asset service (CSV with SofaScore data)
    assets = get_player_assets(jogador_name, team_name_sc)
    photo_url = assets.get("photo_url")
    club_logo_url = assets.get("club_logo")

    # Fallback: try WyScout DataFrame columns for photo_url
    if not photo_url:
        for photo_col in ("photo_url", "Foto", "ImageDataURL", "image_url"):
            val = row.get(photo_col)
            if val is not None and pd.notna(val) and str(val).strip():
                photo_url = str(val).strip()
                break
    # Fallback: get photo from análises sheet
    if not photo_url and ana_match is not None:
        foto_val = ana_match.get("Foto")
        if foto_val is not None and pd.notna(foto_val) and str(foto_val).strip():
            photo_url = str(foto_val).strip()

    return {
        "summary": {
            "id": idx_val,
            "name": str(row.get("Jogador", "")),
            "display_name": str(row.get("JogadorDisplay", "")),
            "team": str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None,
            "club_logo": club_logo_url or (CLUB_LOGOS.get(str(row.get("Equipa", ""))) if pd.notna(row.get("Equipa")) else None),
            "position": position,
            "age": age,
            "nationality": str(row.get("Naturalidade", "")) if pd.notna(row.get("Naturalidade")) else None,
            "league": league_actual or (str(row.get("liga_tier", "")) if pd.notna(row.get("liga_tier")) else None),
            "minutes_played": _safe_float(row.get("Minutos jogados:")),
            "photo_url": photo_url,
            "score": round(score, 1) if score else None,
        },
        "metrics": metrics,
        "percentiles": percentiles,
        "indices": indices,
        "scout_score": round(score, 1) if score else None,
        "performance_class": perf_class,
        "skillcorner": sc_data,
        "skillcorner_physical": sc_physical,
        "skillcorner_debug": sc_debug,
        "projection_score": projection_score,
        "ssp_lambdas": SSP_LAMBDAS,
        "prediction": prediction,
        "analises": analises_data,
    }


# ══════════════════════════════════════════════════════════════════════
# RANKING ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.post("/api/rankings", response_model=RankingResponse)
async def get_rankings(
    req: RankingRequest,
    current_user: dict = Depends(get_current_user),
):
    # TTL cache for ranking results (5 min)
    cache_key = _endpoint_cache.make_key("ranking", req.position, req.min_minutes, req.league or "", req.top_n)
    cached = _endpoint_cache.get(cache_key)
    if cached is not None:
        return cached

    df = _get_wyscout()
    position = get_posicao_categoria(req.position)

    if "Posição" in df.columns:
        pool = df[df["Posição"].apply(lambda p: get_posicao_categoria(p) == position if pd.notna(p) else False)]
    else:
        pool = df

    if req.league and "liga_tier" in pool.columns:
        pool = pool[pool["liga_tier"] == req.league]

    pos_indices = INDICES_CONFIG.get(position, {})
    ranked = rank_players_weighted(
        pool,
        position,
        df,
        indices_config=pos_indices,
        min_minutes=req.min_minutes,
    )

    if len(ranked) == 0:
        result = RankingResponse(position=position, total=0, players=[])
        _endpoint_cache.set(cache_key, result)
        return result

    ranked = ranked.head(req.top_n)
    entries = []
    for rank, (idx, row) in enumerate(ranked.iterrows(), 1):
        idx_values = {}
        for idx_name in pos_indices:
            val = _safe_float(row.get(idx_name))
            if val is not None:
                idx_values[idx_name] = round(val, 1)

        player_name = str(row.get("Jogador", ""))
        team_name = str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None
        assets = get_player_assets(player_name, team_name)

        entries.append(RankingEntry(
            rank=rank,
            name=player_name,
            display_name=str(row.get("JogadorDisplay", row.get("Jogador", ""))),
            team=team_name,
            age=_safe_float(row.get("Idade")),
            league=resolve_actual_league(
                row.get("Equipa"),
                fallback_liga_tier=str(row.get("liga_tier", "")) if pd.notna(row.get("liga_tier")) else None,
            ),
            minutes=_safe_float(row.get("Minutos jogados:")),
            score=round(float(row.get("Score", 0)), 1),
            indices=idx_values,
            photo_url=assets.get("photo_url"),
            club_logo=assets.get("club_logo"),
            league_logo=assets.get("league_logo"),
        ))

    result = RankingResponse(position=position, total=len(entries), players=entries)
    _endpoint_cache.set(cache_key, result)
    return result


@app.post("/api/rankings/prediction")
async def get_prediction_rankings(
    req: dict,
    current_user: dict = Depends(get_current_user),
):
    """Ranking by P(Sucesso) prediction — includes SSP, risk, probability."""
    # TTL cache for prediction ranking (5 min)
    cache_key = _endpoint_cache.make_key(
        "pred_rank", req.get("position"), req.get("min_minutes"),
        req.get("league"), req.get("top_n"), req.get("league_target"),
    )
    cached = _endpoint_cache.get(cache_key)
    if cached is not None:
        return cached

    df = _get_wyscout()
    position = get_posicao_categoria(req.get("position", "Atacante"))
    min_minutes = req.get("min_minutes", 500)
    league_filter = req.get("league", None)
    league_target = req.get("league_target", "Serie B Brasil")
    top_n = req.get("top_n", 50)

    if "Posição" in df.columns:
        pool = df[df["Posição"].apply(lambda p: get_posicao_categoria(p) == position if pd.notna(p) else False)].copy()
    else:
        pool = df.copy()

    if league_filter and "liga_tier" in pool.columns:
        pool = pool[pool["liga_tier"] == league_filter]

    # Filter by min minutes
    pool["_min"] = pool.get("Minutos jogados:", pd.Series(dtype=float)).apply(_safe_float)
    pool = pool[pool["_min"] >= min_minutes]
    pool = pool.drop(columns=["_min"])

    if len(pool) == 0:
        return {"position": position, "league_target": league_target, "total": 0, "players": []}

    predictor = ContractSuccessPredictor()
    results = []

    # Pre-compute percentile matrix once for the entire pool (vectorized)
    from services.similarity import _get_percentile_matrix
    perc_matrix = _get_percentile_matrix(df)

    for idx, row in pool.iterrows():
        ssp = calculate_overall_score(row, position, df, _perc_matrix=perc_matrix)
        if ssp is None:
            continue
        age = _safe_float(row.get("Idade")) or 24
        minutes = _safe_float(row.get("Minutos jogados:")) or 0
        # Resolve actual current league by club name (not scouting pool league)
        liga_tier_raw = str(row.get("liga_tier", "")) if pd.notna(row.get("liga_tier")) else None
        league_origin = resolve_actual_league(
            row.get("Equipa"), fallback_liga_tier=liga_tier_raw
        ) or league_target  # last resort: assume same as target

        pred = predictor.predict_success_unsupervised(
            ssp_score=ssp, age=age,
            league_origin=league_origin, league_target=league_target,
            minutes=minutes,
        )

        pred_player_name = str(row.get("Jogador", ""))
        pred_team_name = str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None
        pred_assets = get_player_assets(pred_player_name, pred_team_name)

        results.append({
            "name": pred_player_name,
            "display_name": str(row.get("JogadorDisplay", row.get("Jogador", ""))),
            "team": pred_team_name,
            "age": age,
            "league": league_origin,
            "minutes": minutes,
            "ssp": round(ssp, 1),
            "p_success": round(pred["success_probability"], 3),
            "risk_level": pred["risk_level"],
            "league_gap": round(pred["league_gap"], 1),
            "tier_origin": pred["tier_origin"],
            "tier_target": pred["tier_target"],
            "photo_url": pred_assets.get("photo_url"),
            "club_logo": pred_assets.get("club_logo"),
            "league_logo": pred_assets.get("league_logo"),
        })

    # Sort by P(Sucesso) descending
    results.sort(key=lambda x: -x["p_success"])
    results = results[:top_n]

    # Add rank
    for i, r in enumerate(results, 1):
        r["rank"] = i

    result = {
        "position": position,
        "league_target": league_target,
        "total": len(results),
        "players": results,
    }
    _endpoint_cache.set(cache_key, result)
    return result


# ══════════════════════════════════════════════════════════════════════
# SIMILARITY ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.post("/api/similarity")
async def find_similar_players(
    req: SimilarityRequest,
    current_user: dict = Depends(get_current_user),
):
    df = _get_wyscout()
    position = get_posicao_categoria(req.position)

    if "JogadorDisplay" not in df.columns:
        raise HTTPException(status_code=400, detail="Coluna JogadorDisplay não encontrada")

    mask = df["JogadorDisplay"] == req.player_name
    if mask.sum() == 0:
        mask = df["JogadorDisplay"].str.lower() == req.player_name.lower()
    if mask.sum() == 0:
        raise HTTPException(status_code=404, detail="Jogador de referência não encontrado")

    target = df[mask].iloc[0]

    pool = df.copy()
    if "Posição" in pool.columns:
        pool = pool[pool["Posição"].apply(lambda p: get_posicao_categoria(p) == position if pd.notna(p) else False)]

    similar_df = compute_weighted_cosine_similarity(
        target,
        pool,
        position,
        top_n=req.top_n,
        min_minutes=req.min_minutes,
        percentile_base=df,
    )

    if len(similar_df) == 0:
        return {
            "reference_player": req.player_name,
            "position": position,
            "similar_players": [],
        }

    similar_players = []
    for idx, row in similar_df.iterrows():
        similar_players.append({
            "name": str(row.get("Jogador", "")),
            "display_name": str(row.get("JogadorDisplay", row.get("Jogador", ""))),
            "team": str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None,
            "similarity_pct": float(row.get("similarity_pct", 0)),
            "matched_metrics": int(row.get("matched_metrics", 0)),
        })

    return {
        "reference_player": req.player_name,
        "position": position,
        "similar_players": similar_players,
    }


@app.get("/api/similarity/breakdown")
async def similarity_breakdown(
    reference: str = Query(...),
    similar: str = Query(...),
    position: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    df = _get_wyscout()
    pos = get_posicao_categoria(position)

    ref_mask = df["JogadorDisplay"] == reference
    sim_mask = df["JogadorDisplay"] == similar
    if ref_mask.sum() == 0 or sim_mask.sum() == 0:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    ref_row = df[ref_mask].iloc[0]
    sim_row = df[sim_mask].iloc[0]

    breakdown_df = get_similarity_breakdown(ref_row, sim_row, pos)
    if len(breakdown_df) == 0:
        return []

    return breakdown_df.to_dict(orient="records")


# ══════════════════════════════════════════════════════════════════════
# RADAR / CHART DATA ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/players/{player_display_name}/radar")
async def get_radar_data(
    player_display_name: str,
    top_n: int = 12,
    current_user: dict = Depends(get_current_user),
):
    df = _get_wyscout()
    mask = df["JogadorDisplay"] == player_display_name
    if mask.sum() == 0:
        mask = df["JogadorDisplay"].str.lower() == player_display_name.lower()
    if mask.sum() == 0:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    row = df[mask].iloc[0]
    pos_raw = str(row.get("Posição", "")) if pd.notna(row.get("Posição")) else "Meia"
    position = get_posicao_categoria(pos_raw)

    percentiles = calculate_metric_percentiles(row, position, df, top_n=top_n)

    return {
        "labels": list(percentiles.keys()),
        "values": list(percentiles.values()),
        "position": position,
        "player_name": player_display_name,
    }


@app.get("/api/players/{player_display_name}/comparison")
async def compare_players(
    player_display_name: str,
    compare_with: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    df = _get_wyscout()

    mask1 = df["JogadorDisplay"] == player_display_name
    mask2 = df["JogadorDisplay"] == compare_with
    if mask1.sum() == 0 or mask2.sum() == 0:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    row1 = df[mask1].iloc[0]
    row2 = df[mask2].iloc[0]

    pos1 = get_posicao_categoria(str(row1.get("Posição", "Meia")))
    pos2 = get_posicao_categoria(str(row2.get("Posição", "Meia")))
    position = pos1

    p1_perc = calculate_metric_percentiles(row1, position, df, top_n=12)
    p2_perc = calculate_metric_percentiles(row2, position, df, top_n=12)

    all_labels = list(dict.fromkeys(list(p1_perc.keys()) + list(p2_perc.keys())))

    return {
        "labels": all_labels,
        "player1": {
            "name": player_display_name,
            "values": [p1_perc.get(l, 0) for l in all_labels],
        },
        "player2": {
            "name": compare_with,
            "values": [p2_perc.get(l, 0) for l in all_labels],
        },
        "position": position,
    }


# ══════════════════════════════════════════════════════════════════════
# OFFERED PLAYERS
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/offered")
async def list_offered_players(current_user: dict = Depends(get_current_user)):
    _ensure_data_loaded()
    df = _data.get("oferecidos")
    if df is None or len(df) == 0:
        return {"players": []}

    players = []
    for idx, row in df.iterrows():
        player = {}
        for col in df.columns:
            val = row.get(col)
            if pd.notna(val):
                player[col] = str(val)
        players.append(player)

    return {"players": players}


# ══════════════════════════════════════════════════════════════════════
# ANALYSES (Análises sheet)
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/analyses")
async def list_analyses(current_user: dict = Depends(get_current_user)):
    _ensure_data_loaded()
    df = _data.get("analises")
    if df is None or len(df) == 0:
        return {"analyses": []}

    analyses = []
    for idx, row in df.iterrows():
        entry = {}
        for col in df.columns:
            val = row.get(col)
            if pd.notna(val):
                entry[col] = str(val)
        analyses.append(entry)

    return {"analyses": analyses}


@app.get("/api/analyses/players")
async def analyses_players(
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Return structured list of analyzed players from the análises sheet."""
    try:
        _ensure_data_loaded()
        df = _data.get("analises")
        if df is None or len(df) == 0:
            return {"players": [], "total": 0}

        _SCORE_COLS = ["Técnica", "Físico", "Tática", "Mental", "Nota_Desempenho", "Potencial"]
        _LINK_COLS = ["ogol", "TM", "Vídeo", "Relatório"]

        # Pre-compute WyScout name lookup for fast matching
        # Store ALL candidates per name so we can disambiguate duplicates
        ws_candidates: Dict[str, list] = {}  # lowercase name → [{display, team, position, age, minutes}, ...]
        ws_names_list: list = []  # [(lowercase_name, display_name, team, position, minutes), ...]
        ws_df = _data.get("wyscout")
        if ws_df is not None and len(ws_df) > 0:
            search_col = "JogadorDisplay" if "JogadorDisplay" in ws_df.columns else "Jogador"
            fallback_col = "Jogador" if search_col == "JogadorDisplay" else None
            for _, ws_row in ws_df.iterrows():
                display = None
                raw = ws_row.get(search_col)
                if raw is not None and pd.notna(raw) and str(raw).strip():
                    display = str(raw).strip()
                elif fallback_col:
                    raw = ws_row.get(fallback_col)
                    if raw is not None and pd.notna(raw) and str(raw).strip():
                        display = str(raw).strip()
                if display:
                    ws_team = str(ws_row.get("Equipa", "")).strip() if pd.notna(ws_row.get("Equipa")) else ""
                    ws_pos = str(ws_row.get("Posição", "")).strip() if pd.notna(ws_row.get("Posição")) else ""
                    ws_age = _safe_float(ws_row.get("Idade"))
                    ws_min = _safe_float(ws_row.get("Minutos")) or _safe_float(ws_row.get("Min"))
                    entry = {"display": display, "team": ws_team, "position": ws_pos, "age": ws_age, "minutes": ws_min or 0}
                    ws_candidates.setdefault(display.lower(), []).append(entry)
                    ws_names_list.append((display.lower(), display, ws_team, ws_pos, ws_min or 0))
            # Also index by Jogador (without team) for exact match
            if "Jogador" in ws_df.columns and search_col != "Jogador":
                for _, ws_row in ws_df.iterrows():
                    jog = ws_row.get("Jogador")
                    if jog is not None and pd.notna(jog) and str(jog).strip():
                        jog_str = str(jog).strip()
                        disp = ws_row.get("JogadorDisplay")
                        disp_str = str(disp).strip() if disp is not None and pd.notna(disp) and str(disp).strip() else jog_str
                        ws_team = str(ws_row.get("Equipa", "")).strip() if pd.notna(ws_row.get("Equipa")) else ""
                        ws_pos = str(ws_row.get("Posição", "")).strip() if pd.notna(ws_row.get("Posição")) else ""
                        ws_age = _safe_float(ws_row.get("Idade"))
                        ws_min = _safe_float(ws_row.get("Minutos")) or _safe_float(ws_row.get("Min"))
                        entry = {"display": disp_str, "team": ws_team, "position": ws_pos, "age": ws_age, "minutes": ws_min or 0}
                        ws_candidates.setdefault(jog_str.lower(), []).append(entry)

        def _pick_best_candidate(candidates: list, player_team: str | None, player_pos: str | None, player_age: int | None) -> str:
            """Pick best WyScout candidate using team, position, age matching and minutes played."""
            if len(candidates) == 1:
                return candidates[0]["display"]
            # Score each candidate
            scored = []
            pt = (player_team or "").lower()
            pp = (player_pos or "").lower()
            for c in candidates:
                score = 0.0
                ct = c["team"].lower()
                cp = c["position"].lower()
                # Team match is strongest signal
                if pt and ct:
                    from rapidfuzz import fuzz as _fuzz2
                    team_sim = _fuzz2.ratio(pt, ct) / 100.0
                    if team_sim > 0.7:
                        score += 30 * team_sim
                # Position match
                if pp and cp:
                    if pp in cp or cp in pp:
                        score += 15
                # Age proximity (within 2 years is good)
                if player_age and c["age"]:
                    age_diff = abs(player_age - c["age"])
                    if age_diff <= 1:
                        score += 10
                    elif age_diff <= 3:
                        score += 5
                # More minutes = more likely the right player (tiebreaker)
                score += min(c["minutes"] / 500, 5)
                scored.append((score, c["display"]))
            scored.sort(key=lambda x: -x[0])
            return scored[0][1]

        players = []
        for _, row in df.iterrows():
            try:
                nome = str(row.get("Nome", "")).strip() if pd.notna(row.get("Nome")) else ""
                if not nome:
                    continue

                # Search filter
                if search and search.strip():
                    if search.strip().lower() not in nome.lower():
                        continue

                # Scores
                scores = {}
                for col in _SCORE_COLS:
                    val = _safe_float(row.get(col))
                    if val is not None:
                        scores[col] = round(val, 2)

                # Links
                links = {}
                for col in _LINK_COLS:
                    val = row.get(col)
                    if val is not None and pd.notna(val) and str(val).strip():
                        links[col] = str(val).strip()

                # Text fields
                analysis_text = None
                val = row.get("Análise")
                if val is not None and pd.notna(val) and str(val).strip():
                    analysis_text = str(val).strip()

                modelo = None
                val = row.get("Modelo")
                if val is not None and pd.notna(val) and str(val).strip():
                    modelo = str(val).strip()

                faixa_salarial = None
                for fc in ("Faixa salarial", "faixa salarial", "Faixa Salarial"):
                    val = row.get(fc)
                    if val is not None and pd.notna(val) and str(val).strip():
                        faixa_salarial = str(val).strip()
                        break

                transfer_luvas = None
                val = row.get("Transfer/Luvas")
                if val is not None and pd.notna(val) and str(val).strip():
                    transfer_luvas = str(val).strip()

                foto = None
                val = row.get("Foto")
                if val is not None and pd.notna(val) and str(val).strip():
                    foto = str(val).strip()

                # Extra fields from the sheet
                posicao = None
                for pc in ("Posição", "Posicao", "posição", "posicao"):
                    val = row.get(pc)
                    if val is not None and pd.notna(val) and str(val).strip():
                        posicao = str(val).strip()
                        break

                idade = None
                for ac in ("Idade", "idade"):
                    val = _safe_float(row.get(ac))
                    if val is not None:
                        idade = int(val)
                        break

                equipe = None
                for tc in ("Equipe", "equipe", "Clube", "clube", "Time", "time"):
                    val = row.get(tc)
                    if val is not None and pd.notna(val) and str(val).strip():
                        equipe = str(val).strip()
                        break

                liga = None
                for lc in ("Liga", "liga", "Campeonato", "campeonato"):
                    val = row.get(lc)
                    if val is not None and pd.notna(val) and str(val).strip():
                        liga = str(val).strip()
                        break

                perfil = None
                for pfc in ("Perfil", "perfil"):
                    val = row.get(pfc)
                    if val is not None and pd.notna(val) and str(val).strip():
                        perfil = str(val).strip()
                        break

                # WyScout match using pre-computed lookup with disambiguation
                wyscout_match = None
                if ws_names_list:
                    nome_lower = nome.strip().lower()
                    # Exact match first — use candidates for disambiguation
                    if nome_lower in ws_candidates:
                        candidates = ws_candidates[nome_lower]
                        wyscout_match = _pick_best_candidate(candidates, equipe, posicao, idade)
                    else:
                        # Fuzzy fallback using pre-computed list (no iterrows)
                        try:
                            from rapidfuzz import fuzz as _fuzz
                            best_score = 0.0
                            best_candidates: list = []
                            for ws_lower, ws_display, ws_team, ws_pos, ws_min in ws_names_list:
                                sim = max(
                                    _fuzz.ratio(nome_lower, ws_lower) / 100.0,
                                    _fuzz.token_sort_ratio(nome_lower, ws_lower) / 100.0,
                                )
                                if nome_lower in ws_lower or ws_lower in nome_lower:
                                    sim = max(sim, 0.85)
                                if sim >= 0.70:
                                    if sim > best_score:
                                        best_score = sim
                                        best_candidates = [{"display": ws_display, "team": ws_team, "position": ws_pos, "age": None, "minutes": ws_min}]
                                    elif sim == best_score:
                                        best_candidates.append({"display": ws_display, "team": ws_team, "position": ws_pos, "age": None, "minutes": ws_min})
                            if best_candidates:
                                wyscout_match = _pick_best_candidate(best_candidates, equipe, posicao, idade)
                        except Exception as e:
                            logger.warning("Fuzzy match failed for '%s': %s", nome, e)

                players.append({
                    "nome": nome,
                    "foto": foto,
                    "posicao": posicao,
                    "idade": idade,
                    "equipe": equipe,
                    "liga": liga,
                    "modelo": modelo,
                    "perfil": perfil,
                    "scores": scores,
                    "links": links,
                    "analysis_text": analysis_text,
                    "faixa_salarial": faixa_salarial,
                    "transfer_luvas": transfer_luvas,
                    "wyscout_match": wyscout_match,
                })
            except Exception as e:
                logger.warning("Skipping analyses row due to error: %s", e)
                continue

        return {"players": players, "total": len(players)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("analyses_players endpoint failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar análises: {str(e)}")


# ══════════════════════════════════════════════════════════════════════
# INDICES (detailed index breakdown for a player)
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/players/{player_display_name}/indices")
async def get_player_indices(
    player_display_name: str,
    position: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Return composite indices + per-metric breakdown for a player."""
    df = _get_wyscout()
    mask = df["JogadorDisplay"] == player_display_name
    if mask.sum() == 0:
        mask = df["JogadorDisplay"].str.lower() == player_display_name.lower()
    if mask.sum() == 0:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    row = df[mask].iloc[0]
    pos_raw = position or (str(row.get("Posição", "")) if pd.notna(row.get("Posição")) else "Meia")
    pos = get_posicao_categoria(pos_raw)

    pos_indices = INDICES_CONFIG.get(pos, {})
    indices = calculate_all_indices(row, pos_indices, df, pos)
    indices = {k: round(v, 1) for k, v in indices.items()}

    # Per-index metric breakdown
    breakdown = {}
    for idx_name, metrics in pos_indices.items():
        metric_details = []
        for m in metrics:
            if m in row.index:
                val = _safe_float(row.get(m))
                col_vals = df[m].apply(_safe_float).dropna()
                perc = 0.0
                if val is not None and len(col_vals) > 0:
                    perc = float((col_vals < val).sum() / len(col_vals) * 100)
                metric_details.append({
                    "metric": m,
                    "value": round(val, 2) if val is not None else None,
                    "percentile": round(perc, 1),
                })
        breakdown[idx_name] = metric_details

    return {
        "player": player_display_name,
        "position": pos,
        "indices": indices,
        "breakdown": breakdown,
        "summary": {
            "name": str(row.get("Jogador", "")),
            "team": str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None,
            "age": _safe_float(row.get("Idade")),
            "minutes": _safe_float(row.get("Minutos jogados:")),
            "position_raw": str(row.get("Posição", "")) if pd.notna(row.get("Posição")) else None,
        },
    }


# ══════════════════════════════════════════════════════════════════════
# COMPARISON (detailed comparison with indices)
# ══════════════════════════════════════════════════════════════════════

@app.post("/api/comparison")
async def compare_players_indices(
    req: dict,
    current_user: dict = Depends(get_current_user),
):
    """Compare two players' indices for a given position."""
    df = _get_wyscout()
    p1_name = req.get("player1", "")
    p2_name = req.get("player2", "")
    pos = get_posicao_categoria(req.get("position", "Meia"))

    mask1 = df["JogadorDisplay"] == p1_name
    mask2 = df["JogadorDisplay"] == p2_name
    if mask1.sum() == 0 or mask2.sum() == 0:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    row1 = df[mask1].iloc[0]
    row2 = df[mask2].iloc[0]

    pos_indices = INDICES_CONFIG.get(pos, {})
    idx1 = calculate_all_indices(row1, pos_indices, df, pos)
    idx2 = calculate_all_indices(row2, pos_indices, df, pos)

    comparison = []
    for name in pos_indices.keys():
        v1 = round(idx1.get(name, 0), 1)
        v2 = round(idx2.get(name, 0), 1)
        comparison.append({
            "index": name,
            "player1_value": v1,
            "player2_value": v2,
            "diff": round(v1 - v2, 1),
        })

    def _player_info(row):
        return {
            "name": str(row.get("Jogador", "")),
            "team": str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None,
            "age": _safe_float(row.get("Idade")),
            "position_raw": str(row.get("Posição", "")) if pd.notna(row.get("Posição")) else None,
        }

    return {
        "position": pos,
        "player1": _player_info(row1),
        "player2": _player_info(row2),
        "comparison": comparison,
        "indices1": {k: round(v, 1) for k, v in idx1.items()},
        "indices2": {k: round(v, 1) for k, v in idx2.items()},
    }


# ══════════════════════════════════════════════════════════════════════
# DATA BROWSER (raw data tables for all sources)
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/data/{source}")
async def get_data_table(
    source: str,
    search: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    """Return raw data table for a source (wyscout, analises, oferecidos, skillcorner)."""
    _ensure_data_loaded()
    source_map = {
        "wyscout": "wyscout",
        "analises": "analises",
        "oferecidos": "oferecidos",
        "skillcorner": "skillcorner",
    }
    key = source_map.get(source)
    if not key:
        raise HTTPException(status_code=400, detail=f"Fonte inválida: {source}")

    raw_df = _data.get(key)
    if raw_df is None or len(raw_df) == 0:
        return {"source": source, "total": 0, "columns": [], "rows": []}

    df = raw_df.copy()

    # Column selection per source
    col_map = {
        "wyscout": ["Jogador", "Equipa", "Posição", "Idade", "Partidas jogadas", "Minutos jogados:", "Golos", "Assistências", "Golos esperados/90", "Assistências esperadas/90", "Liga", "liga_tier"],
        "analises": None,  # all columns
        "oferecidos": None,
        "skillcorner": ["player_name", "short_name", "team_name", "position_group", "age", "count_match"],
    }
    selected_cols = col_map.get(source)
    if selected_cols:
        selected_cols = [c for c in selected_cols if c in df.columns]
        if selected_cols:
            df = df[selected_cols]

    # Search
    if search:
        search_lower = search.lower()
        text_cols = df.select_dtypes(include=["object"]).columns
        mask = pd.Series(False, index=df.index)
        for col in text_cols[:5]:
            mask |= df[col].astype(str).str.lower().str.contains(search_lower, na=False)
        df = df[mask]

    total = len(df)
    df = df.iloc[offset:offset + limit]

    rows = []
    for _, row in df.iterrows():
        r = {}
        for col in df.columns:
            val = row.get(col)
            if pd.notna(val):
                r[col] = str(val) if not isinstance(val, (int, float, np.integer, np.floating)) else val
                if isinstance(r[col], (float, np.floating)) and np.isnan(r[col]):
                    r[col] = None
            else:
                r[col] = None
        rows.append(r)

    return {
        "source": source,
        "total": total,
        "columns": list(df.columns),
        "rows": rows,
    }


# ══════════════════════════════════════════════════════════════════════
# PREDICTION (contract success prediction)
# ══════════════════════════════════════════════════════════════════════

@app.post("/api/prediction")
async def predict_contract_success(
    req: dict,
    current_user: dict = Depends(get_current_user),
):
    """Predict contract success probability for a player at a target league."""
    df = _get_wyscout()
    player_name = req.get("player_name", "")
    league_origin = req.get("league_origin", "")
    league_target = req.get("league_target", "Serie B Brasil")

    mask = df["JogadorDisplay"] == player_name
    if mask.sum() == 0:
        mask = df["JogadorDisplay"].str.lower() == player_name.lower()
    if mask.sum() == 0:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    row = mask.idxmax()
    row_data = df.loc[row]
    pos_raw = str(row_data.get("Posição", "")) if pd.notna(row_data.get("Posição")) else "Meia"
    pos = get_posicao_categoria(pos_raw)

    ssp = calculate_overall_score(row_data, pos, df) or 50.0
    age = _safe_float(row_data.get("Idade")) or 24
    minutes = _safe_float(row_data.get("Minutos jogados:")) or 0

    # Use provided league_origin or detect from club → actual league
    if not league_origin:
        liga_tier_raw = str(row_data.get("liga_tier", "")) if pd.notna(row_data.get("liga_tier")) else None
        league_origin = resolve_actual_league(
            row_data.get("Equipa"), fallback_liga_tier=liga_tier_raw
        ) or league_target

    predictor = ContractSuccessPredictor()
    pred = predictor.predict_success_unsupervised(
        ssp_score=ssp,
        age=age,
        league_origin=league_origin,
        league_target=league_target,
        minutes=minutes,
    )

    return {
        "player": {
            "name": str(row_data.get("Jogador", "")),
            "display_name": player_name,
            "team": str(row_data.get("Equipa", "")) if pd.notna(row_data.get("Equipa")) else None,
            "position": pos,
            "age": age,
            "minutes": minutes,
            "league": league_origin,
        },
        "ssp_score": round(ssp, 1),
        "prediction": pred,
    }


# ══════════════════════════════════════════════════════════════════════
# CLUSTERS (tactical clustering)
# ══════════════════════════════════════════════════════════════════════

# Metric-to-label mapping for cluster naming
_METRIC_LABELS = {
    # Offensive
    "Golos esperados/90": "Finalizador",
    "Golos/90": "Goleador",
    "xG/Chute": "Eficiente",
    "Assistências esperadas/90": "Criador",
    "Assistências/90": "Assistente",
    "Passes decisivos/90": "Decisivo",
    "Dribles/90": "Driblador",
    "Dribles com sucesso, %": "Habilidoso",
    "Toques na área/90": "Presenca de Area",
    "Chutes/90": "Artilheiro",
    # Passing
    "Passes progressivos/90": "Progressivo",
    "Passes para frente/90": "Vertical",
    "Passes para terço final/90": "Ofensivo",
    "Passes longos/90": "Lancador",
    "Precisão passes longos, %": "Preciso",
    "Precisão passes, %": "Seguro",
    "Passes inteligentes/90": "Criativo",
    # Defensive
    "Duelos defensivos/90": "Combativo",
    "Duelos defensivos ganhos, %": "Robusto",
    "Interceptações/90": "Interceptador",
    "Recuperações de bola/90": "Recuperador",
    "Duelos aéreos/90": "Aereo",
    "Duelos aéreos ganhos, %": "Dominante Aereo",
    "Faltas/90": "Aggressivo",
    # Physical / Progression
    "Corridas progressivas/90": "Dinamico",
    "Acelerações/90": "Explosivo",
    "Cruzamentos/90": "Cruzador",
    "Cruzamentos precisos, %": "Cruzador Preciso",
}


def _generate_cluster_name(centroid: dict, position: str, cluster_id: int) -> str:
    """Generate a descriptive name for a cluster based on its top centroid features."""
    if not centroid:
        return f"Perfil {cluster_id + 1}"

    # Get top 3 positive (dominant) features
    sorted_feats = sorted(centroid.items(), key=lambda x: -x[1])
    top_positive = [(m, z) for m, z in sorted_feats if z > 0.3][:3]

    if not top_positive:
        return f"Equilibrado ({position})"

    # Map metrics to labels
    labels = []
    for metric, zscore in top_positive:
        label = _METRIC_LABELS.get(metric)
        if not label:
            # Try partial match
            metric_lower = metric.lower()
            if "gol" in metric_lower or "chute" in metric_lower:
                label = "Finalizador"
            elif "assist" in metric_lower or "decisiv" in metric_lower:
                label = "Criador"
            elif "drible" in metric_lower:
                label = "Driblador"
            elif "duel" in metric_lower and "defens" in metric_lower:
                label = "Combativo"
            elif "intercep" in metric_lower or "recuper" in metric_lower:
                label = "Recuperador"
            elif "pass" in metric_lower and "progress" in metric_lower:
                label = "Progressivo"
            elif "corrid" in metric_lower or "progress" in metric_lower:
                label = "Dinamico"
            elif "cruz" in metric_lower:
                label = "Cruzador"
            elif "aere" in metric_lower:
                label = "Aereo"
            elif "pass" in metric_lower:
                label = "Passador"
            else:
                label = metric.split("/")[0].split(",")[0][:15]
        if label not in labels:
            labels.append(label)

    if len(labels) >= 2:
        return f"{labels[0]}-{labels[1]}"
    return labels[0] if labels else f"Perfil {cluster_id + 1}"




@app.post("/api/clusters")
async def get_clusters(
    req: dict,
    current_user: dict = Depends(get_current_user),
):
    """Run tactical clustering for a position."""
    from services.predictive_engine import TacticalClusterer, DataPreprocessor

    df = _get_wyscout()
    position = get_posicao_categoria(req.get("position", "Meia"))
    min_minutes = req.get("min_minutes", 500)

    # Filter by position
    pool = df[df["Posição"].apply(lambda p: get_posicao_categoria(p) == position if pd.notna(p) else False)].copy()

    pp = DataPreprocessor()
    features = pp.get_available_features(pool, position)
    if len(features) < 5:
        return {"position": position, "clusters": [], "error": "Features insuficientes"}

    try:
        df_f, X, available = pp.prepare_matrix(pool, features, min_minutes=min_minutes)
    except Exception as e:
        return {"position": position, "clusters": [], "error": str(e)}

    if len(df_f) < 15:
        return {"position": position, "clusters": [], "error": f"Jogadores insuficientes: {len(df_f)}"}

    tc = TacticalClusterer()
    tc.fit(X, available)
    result = tc.predict(X)

    df_f["Cluster"] = result["labels"]
    df_f["Prob_Cluster"] = (result["probabilities"].max(axis=1) * 100).round(1)

    clusters = []
    for k in range(tc.optimal_k):
        mask = df_f["Cluster"] == k
        df_cluster = df_f[mask].sort_values("Prob_Cluster", ascending=False)
        profile = tc.cluster_profiles.get(k, {})

        top_players = []
        for _, r in df_cluster.head(10).iterrows():
            top_players.append({
                "name": str(r.get("Jogador", "")),
                "team": str(r.get("Equipa", "")) if pd.notna(r.get("Equipa")) else None,
                "probability": float(r.get("Prob_Cluster", 0)),
                "age": _safe_float(r.get("Idade")),
                "minutes": _safe_float(r.get("Minutos jogados:")),
            })

        centroid = profile.get("centroid", {})
        top_features = sorted(centroid.items(), key=lambda x: -abs(x[1]))[:8]

        # Auto-name the cluster profile based on top centroid features
        profile_name = _generate_cluster_name(centroid, position, k)

        clusters.append({
            "id": k,
            "name": profile_name,
            "size": int(profile.get("size", mask.sum())),
            "players": top_players,
            "features": [{"metric": m, "zscore": round(v, 2)} for m, v in top_features],
        })

    return {
        "position": position,
        "n_clusters": tc.optimal_k,
        "total_players": len(df_f),
        "clusters": clusters,
    }


# ══════════════════════════════════════════════════════════════════════
# LEAGUE MAPPINGS
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/config/league-mappings")
async def get_league_mappings(current_user: dict = Depends(get_current_user)):
    """Return full league mapping for prediction dropdown and display."""
    return {
        "wyscout_league_map": WYSCOUT_LEAGUE_MAP,
        "league_logos": LEAGUE_LOGOS,
    }


# ══════════════════════════════════════════════════════════════════════
# SKILLCORNER — DEDICATED ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

# Leagues covered by SkillCorner in this dataset (South America + Portugal)
SKILLCORNER_COVERED_LEAGUES = {
    # Brazil
    "Serie A Brasil", "Serie B Brasil", "Serie C Brasil",
    "Paulista A1", "Paulista A2", "Carioca A1", "Gaucho A1",
    "Mineiro A1", "Paranaense A1", "Copa do Brasil",
    # Argentina
    "Liga Argentina",
    # Other South America
    "Liga Colombia", "Liga Chile", "Copa Libertadores", "Copa Sudamericana",
    # Portugal
    "Liga Portugal", "Portugal | 1",
}


def _is_skillcorner_covered(league: str | None, team: str | None = None) -> bool:
    """Check if a player's league is within SkillCorner coverage."""
    if league and any(covered.lower() in league.lower() for covered in SKILLCORNER_COVERED_LEAGUES):
        return True
    # Fallback: check team's resolved league
    if team:
        resolved = resolve_actual_league(team)
        if resolved and any(covered.lower() in resolved.lower() for covered in SKILLCORNER_COVERED_LEAGUES):
            return True
    return False


@app.get("/api/skillcorner/player/{player_name}")
async def get_skillcorner_player_profile(
    player_name: str,
    sc_override: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Full SkillCorner profile for a player — indices + physical + coverage status."""
    _ensure_data_loaded()
    sc_df = _data.get("skillcorner")
    if sc_df is None or len(sc_df) == 0:
        return {"found": False, "reason": "no_skillcorner_data", "covered": False}

    # Resolve WyScout player for context
    df = _get_wyscout()
    mask = df["JogadorDisplay"] == player_name
    if mask.sum() == 0:
        mask = df["JogadorDisplay"].str.lower() == player_name.lower()

    league = None
    team = None
    position = "Meia"
    jogador_name = player_name

    if mask.sum() > 0:
        row = df[mask].iloc[0]
        jogador_name = str(row.get("Jogador", ""))
        team = str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None
        position_raw = str(row.get("Posição", "")) if pd.notna(row.get("Posição")) else "Meia"
        position = get_posicao_categoria(position_raw)
        liga_tier_raw = str(row.get("liga_tier", "")) if pd.notna(row.get("liga_tier")) else None
        league = resolve_actual_league(team, fallback_liga_tier=liga_tier_raw)

    covered = _is_skillcorner_covered(league, team)

    # Find SkillCorner match
    sc_match = None
    if sc_override and "player_name" in sc_df.columns:
        override_mask = sc_df["player_name"] == sc_override
        if override_mask.sum() > 0:
            sc_match = sc_df[override_mask].iloc[0]
    if sc_match is None:
        sc_match = find_skillcorner_player(jogador_name, sc_df, team_name=team)

    if sc_match is None:
        return {
            "found": False,
            "covered": covered,
            "league": league,
            "reason": "no_match",
            "searched_name": jogador_name,
            "searched_team": team,
        }

    # Extract all SkillCorner indices for position
    sc_indices_keys = SKILLCORNER_INDICES.get(position, [])
    sc_indices = {}
    for idx_name in sc_indices_keys:
        val = _safe_float(sc_match.get(idx_name))
        if val is not None:
            sc_indices[idx_name] = round(val, 2)

    # Extract ALL numeric columns for full data view
    all_metrics = {}
    for col in sc_df.columns:
        if col in {"player_name", "short_name", "team_name", "position_group"}:
            continue
        val = _safe_float(sc_match.get(col))
        if val is not None:
            all_metrics[col] = round(val, 2)

    # Physical subset
    _SC_PHYSICAL_COLS = {
        "sprint_count_per_90": "Sprints/90",
        "hi_count_per_90": "High Intensity Runs/90",
        "distance_per_90": "Distance/90",
        "high_speed_running_distance_per_90": "High Speed Running Dist/90",
        "accelerations_per_90": "Accelerations/90",
        "decelerations_per_90": "Decelerations/90",
        "max_speed": "Max Speed (km/h)",
        "avg_speed": "Avg Speed (km/h)",
        "pressing_index_per_90": "Pressing Index/90",
        "avg_psv99": "Avg PSV-99",
        "avg_top_5_psv99": "Avg Top 5 PSV-99",
    }
    physical = {}
    for col, label in _SC_PHYSICAL_COLS.items():
        val = _safe_float(sc_match.get(col))
        if val is not None:
            physical[label] = round(val, 2)

    # Compute percentiles relative to the full SkillCorner dataset
    physical_percentiles = {}
    for col, label in _SC_PHYSICAL_COLS.items():
        val = _safe_float(sc_match.get(col))
        if val is not None and col in sc_df.columns:
            col_data = pd.to_numeric(sc_df[col], errors="coerce").dropna()
            if len(col_data) > 0:
                pct = (col_data < val).sum() / len(col_data) * 100
                physical_percentiles[label] = round(pct, 1)

    indices_percentiles = {}
    for idx_name in sc_indices_keys:
        val = _safe_float(sc_match.get(idx_name))
        if val is not None and idx_name in sc_df.columns:
            col_data = pd.to_numeric(sc_df[idx_name], errors="coerce").dropna()
            if len(col_data) > 0:
                pct = (col_data < val).sum() / len(col_data) * 100
                indices_percentiles[idx_name] = round(pct, 1)

    return {
        "found": True,
        "covered": covered,
        "league": league,
        "position": position,
        "matched_name": str(sc_match.get("player_name", "")),
        "matched_team": str(sc_match.get("team_name", "")) if pd.notna(sc_match.get("team_name")) else None,
        "matched_position": str(sc_match.get("position_group", "")) if pd.notna(sc_match.get("position_group")) else None,
        "indices": sc_indices,
        "indices_percentiles": indices_percentiles,
        "physical": physical,
        "physical_percentiles": physical_percentiles,
        "all_metrics": all_metrics,
    }


@app.post("/api/skillcorner/comparison")
async def compare_skillcorner_players(
    req: dict,
    current_user: dict = Depends(get_current_user),
):
    """Compare SkillCorner data for two players."""
    _ensure_data_loaded()
    sc_df = _data.get("skillcorner")
    if sc_df is None or len(sc_df) == 0:
        raise HTTPException(status_code=404, detail="SkillCorner data not available")

    df = _get_wyscout()
    p1_name = req.get("player1", "")
    p2_name = req.get("player2", "")
    sc1_override = req.get("sc1_override")
    sc2_override = req.get("sc2_override")
    pos = get_posicao_categoria(req.get("position", "Meia"))

    def _resolve_sc(display_name, sc_override_name):
        if sc_override_name and "player_name" in sc_df.columns:
            m = sc_df["player_name"] == sc_override_name
            if m.sum() > 0:
                return sc_df[m].iloc[0]
        mask = df["JogadorDisplay"] == display_name
        if mask.sum() == 0:
            mask = df["JogadorDisplay"].str.lower() == display_name.lower()
        if mask.sum() == 0:
            return None
        row = df[mask].iloc[0]
        jn = str(row.get("Jogador", ""))
        tn = str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None
        return find_skillcorner_player(jn, sc_df, team_name=tn)

    sc1 = _resolve_sc(p1_name, sc1_override)
    sc2 = _resolve_sc(p2_name, sc2_override)

    if sc1 is None and sc2 is None:
        raise HTTPException(status_code=404, detail="No SkillCorner data for either player")

    # Collect metrics for comparison
    sc_indices_keys = SKILLCORNER_INDICES.get(pos, [])
    _SC_PHYSICAL_COLS = [
        "sprint_count_per_90", "hi_count_per_90", "distance_per_90",
        "avg_psv99", "avg_top_5_psv99",
    ]
    compare_cols = sc_indices_keys + _SC_PHYSICAL_COLS

    comparison = []
    for col in compare_cols:
        v1 = round(_safe_float(sc1.get(col)) or 0, 2) if sc1 is not None else None
        v2 = round(_safe_float(sc2.get(col)) or 0, 2) if sc2 is not None else None
        comparison.append({
            "metric": col,
            "player1_value": v1,
            "player2_value": v2,
            "diff": round((v1 or 0) - (v2 or 0), 2) if v1 is not None and v2 is not None else None,
        })

    return {
        "position": pos,
        "player1": {
            "name": p1_name,
            "sc_name": str(sc1.get("player_name", "")) if sc1 is not None else None,
            "sc_team": str(sc1.get("team_name", "")) if sc1 is not None else None,
            "found": sc1 is not None,
        },
        "player2": {
            "name": p2_name,
            "sc_name": str(sc2.get("player_name", "")) if sc2 is not None else None,
            "sc_team": str(sc2.get("team_name", "")) if sc2 is not None else None,
            "found": sc2 is not None,
        },
        "comparison": comparison,
    }


@app.get("/api/skillcorner/coverage")
async def get_skillcorner_coverage(current_user: dict = Depends(get_current_user)):
    """Return the list of leagues covered by SkillCorner."""
    return {
        "covered_leagues": sorted(SKILLCORNER_COVERED_LEAGUES),
        "description": "Dados SkillCorner disponíveis apenas para ligas sul-americanas e Liga Portugal.",
    }


# ══════════════════════════════════════════════════════════════════════
# SCOUTING INTELLIGENCE ENGINE
# ══════════════════════════════════════════════════════════════════════

_scouting_engine: Optional[ScoutingIntelligenceEngine] = None


def _get_scouting_engine() -> ScoutingIntelligenceEngine:
    """Get or initialize the Scouting Intelligence Engine."""
    global _scouting_engine
    if _scouting_engine is not None and _scouting_engine._fitted:
        return _scouting_engine

    df = _get_wyscout()
    _scouting_engine = ScoutingIntelligenceEngine()
    try:
        _scouting_engine.fit(df)
    except Exception as e:
        logger.warning("Scouting engine fit failed (will use fallbacks): %s", e)
        _scouting_engine._fitted = True  # allow fallback methods
    return _scouting_engine


@app.post("/api/trajectory", response_model=TrajectoryResponse)
async def predict_trajectory(
    req: TrajectoryRequest,
    current_user: dict = Depends(get_current_user),
):
    """Predict player career trajectory — predicted rating for next season.

    Scientific basis: Decroos et al. (2019), Pappalardo et al. (2019),
    Bransen & Van Haaren (2020). Model: Gradient Boosting Regressor.
    """
    df = _get_wyscout()
    player_name = req.player_name

    mask = df["JogadorDisplay"] == player_name
    if mask.sum() == 0:
        mask = df["JogadorDisplay"].str.lower() == player_name.lower()
    if mask.sum() == 0:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    row_data = df.loc[mask.idxmax()]
    pos_raw = str(row_data.get("Posição", "")) if pd.notna(row_data.get("Posição")) else "Meia"
    pos = get_posicao_categoria(pos_raw)

    league = req.league
    if not league:
        liga_tier = str(row_data.get("liga_tier", "")) if pd.notna(row_data.get("liga_tier")) else None
        league = resolve_actual_league(row_data.get("Equipa"), fallback_liga_tier=liga_tier)

    engine = _get_scouting_engine()
    traj = engine.trajectory_model.predict_trajectory(row_data, league)

    return TrajectoryResponse(
        player=str(row_data.get("Jogador", "")),
        display_name=player_name,
        position=pos,
        predicted_rating_next_season=traj.get("predicted_rating_next_season"),
        current_rating_estimate=traj.get("current_rating_estimate"),
        trajectory_score=traj.get("trajectory_score"),
        league_adjustment_factor=traj.get("league_adjustment_factor"),
        model_r2=traj.get("model_r2"),
        top_features=traj.get("top_features"),
        method=traj.get("method"),
    )




@app.post("/api/market_opportunities", response_model=MarketOpportunitiesResponse)
async def detect_market_opportunities(
    req: MarketOpportunitiesRequest,
    current_user: dict = Depends(get_current_user),
):
    """Detect undervalued market opportunities using multi-signal scoring.

    Inspired by Brighton, Brentford, FC Midtjylland scouting departments.
    Score: performance × trajectory × value_gap − age_penalty.
    """
    df = _get_wyscout()

    # Filter by minutes
    if req.min_minutes > 0 and "Minutos jogados:" in df.columns:
        df_filtered = df[pd.to_numeric(df["Minutos jogados:"], errors="coerce").fillna(0) >= req.min_minutes]
    else:
        df_filtered = df

    engine = _get_scouting_engine()
    results = engine.detect_opportunities(df_filtered, position=req.position, top_n=req.top_n)

    entries = []
    for r in results:
        entries.append(MarketOpportunityEntry(
            player=r.get("player", ""),
            player_display=r.get("player_display"),
            team=r.get("team") if r.get("team") else None,
            market_opportunity_score=r.get("market_opportunity_score", 0),
            classification=r.get("classification", "below_threshold"),
            is_high_opportunity=r.get("is_high_opportunity", False),
            components=r.get("components"),
        ))

    return MarketOpportunitiesResponse(
        position=req.position,
        total=len(entries),
        opportunities=entries,
    )


@app.post("/api/replacements", response_model=ReplacementResponse)
async def find_replacements(
    req: ReplacementRequest,
    current_user: dict = Depends(get_current_user),
):
    """Find replacement players using multi-method similarity.

    Scientific basis: Bhatt et al. (2025) KickClone — Cosine Similarity + PCA,
    FPSRec (IEEE BigData 2024), Spatial Similarity Index (PMC/NCBI 2025).
    Combines: cosine similarity, Mahalanobis distance, cluster proximity.
    """
    df = _get_wyscout()
    player_name = req.player_name

    mask = df["JogadorDisplay"] == player_name
    if mask.sum() == 0:
        mask = df["JogadorDisplay"].str.lower() == player_name.lower()
    if mask.sum() == 0:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    row_data = df.loc[mask.idxmax()]

    pos = req.position
    if not pos:
        pos_raw = str(row_data.get("Posição", "")) if pd.notna(row_data.get("Posição")) else "Meia"
        pos = get_posicao_categoria(pos_raw)

    age_range = None
    if req.age_min is not None or req.age_max is not None:
        age_range = (req.age_min or 15, req.age_max or 45)

    engine = _get_scouting_engine()
    results = engine.find_replacements(
        target_player_row=row_data,
        df_pool=df,
        position=pos,
        top_n=req.top_n,
        age_range=age_range,
        min_minutes=req.min_minutes,
        league_filter=req.league_filter,
    )

    entries = []
    for r in results:
        entries.append(ReplacementEntry(
            rank=r.get("rank", 0),
            player=r.get("player", ""),
            display_name=r.get("display_name"),
            team=r.get("team"),
            position=pos,
            age=r.get("age"),
            minutes=r.get("minutes"),
            similarity_score=r.get("similarity_score", 0),
            cosine_similarity=r.get("cosine_similarity"),
            mahalanobis_similarity=r.get("mahalanobis_similarity"),
            cluster_proximity=r.get("cluster_proximity"),
            trajectory_score=r.get("trajectory_score"),
            predicted_rating=r.get("predicted_rating"),
            market_value_gap=r.get("market_value_gap"),
            estimated_value=r.get("estimated_value"),
        ))

    return ReplacementResponse(
        reference_player=player_name,
        position=pos,
        total=len(entries),
        replacements=entries,
    )


@app.post("/api/contract_impact", response_model=ContractImpactResponse)
async def analyze_contract_impact(
    req: ContractImpactRequest,
    current_user: dict = Depends(get_current_user),
):
    """Analyze the impact of signing a player on the Botafogo-SP squad.

    Scientific basis: Pappalardo et al. (2019) PlayeRank, Kuper & Szymanski (2009)
    Soccernomics, Poli et al. (CIES 2021), Age Curves 2.0 (TransferLab),
    Frost & Groom (2025) integration challenges.

    Components: positional need, quality uplift, tactical complementarity,
    age profile fit, financial efficiency, risk assessment.
    """
    df = _get_wyscout()
    player_name = req.player_name

    # Exact match
    mask = df["JogadorDisplay"] == player_name
    if mask.sum() == 0:
        mask = df["JogadorDisplay"].str.lower() == player_name.lower()
    # Fallback: contains match (handles partial names, parenthetical disambiguation)
    if mask.sum() == 0:
        mask = df["JogadorDisplay"].str.lower().str.contains(
            player_name.lower().split("(")[0].strip(), na=False
        )
    # Fallback: search in Jogador column too
    if mask.sum() == 0:
        mask = df["Jogador"].str.lower().str.contains(player_name.lower(), na=False)
    if mask.sum() == 0:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    row_data = df.loc[mask.idxmax()]
    pos_raw = str(row_data.get("Posição", "")) if pd.notna(row_data.get("Posição")) else "Meia"
    pos = get_posicao_categoria(pos_raw)

    league = req.league
    if not league:
        liga_tier = str(row_data.get("liga_tier", "")) if pd.notna(row_data.get("liga_tier")) else None
        league = resolve_actual_league(row_data.get("Equipa"), fallback_liga_tier=liga_tier)

    engine = _get_scouting_engine()
    impact = engine.analyze_impact(
        candidate_row=row_data,
        df_all=df,
        position=pos,
        league=league,
        salary=req.salary,
    )

    return ContractImpactResponse(**impact)


@app.get("/api/league_powers")
async def get_league_powers(current_user: dict = Depends(get_current_user)):
    """Return all Opta Power Ranking league coefficients.

    Based on Opta Power Ranking (The Analyst) — global club rating system.
    """
    powers = get_all_league_powers()
    # Also include league tiers from ContractSuccessPredictor for comparison
    predictor = ContractSuccessPredictor()
    tiers = predictor.LEAGUE_TIERS

    combined = {}
    all_leagues = set(list(powers.keys()) + list(tiers.keys()))
    for league in sorted(all_leagues):
        combined[league] = {
            "opta_power": powers.get(league),
            "tier_score": tiers.get(league),
        }

    return {
        "leagues": combined,
        "total": len(combined),
    }


# ── Image Proxy ───────────────────────────────────────────────────────

_ALLOWED_IMAGE_HOSTS = {
    "api.sofascore.com",
    "images.fotmob.com",
    "logodetimes.com",
    "www.logodetimes.com",
    "upload.wikimedia.org",
    "tmssl.akamaized.net",
    "img.a.transfermarkt.technology",
}

# Simple in-memory cache for proxied images (URL → (content_type, bytes))
_image_cache: Dict[str, tuple] = {}
_IMAGE_CACHE_MAX = 2000


@app.get("/api/image-proxy")
async def image_proxy(url: str):
    """Proxy external image URLs to avoid CORS/hotlink 403 errors."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if not parsed.hostname or not parsed.scheme.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL")

    # Allow any image host — the proxy exists to avoid CORS/hotlink issues
    # (restrict to http/https only for safety)

    # Check cache
    if url in _image_cache:
        content_type, data = _image_cache[url]
        return Response(content=data, media_type=content_type,
                        headers={"Cache-Control": "public, max-age=86400"})

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": f"{parsed.scheme}://{parsed.hostname}/",
                    "Origin": f"{parsed.scheme}://{parsed.hostname}",
                    "Sec-Fetch-Dest": "image",
                    "Sec-Fetch-Mode": "no-cors",
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131"',
                    "Sec-Ch-Ua-Platform": '"Windows"',
                },
                allow_redirects=True,
            ) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=resp.status, detail="Upstream image fetch failed")
                data = await resp.read()
                content_type = resp.content_type or "image/png"
    except aiohttp.ClientError:
        raise HTTPException(status_code=502, detail="Failed to fetch image")

    # Cache the result
    if len(_image_cache) < _IMAGE_CACHE_MAX:
        _image_cache[url] = (content_type, data)

    return Response(content=data, media_type=content_type,
                    headers={"Cache-Control": "public, max-age=86400"})


# ── Run ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
