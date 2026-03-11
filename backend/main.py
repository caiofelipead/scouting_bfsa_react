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
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

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
from services.fuzzy_match import build_skillcorner_index, find_skillcorner_player
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

GOOGLE_SHEET_ID = os.environ.get(
    "GOOGLE_SHEET_ID", "1aRjJAxYHJED4FyPnq4PfcrzhhRhzw-vNQ9Vg1pIlak0"
)

SHEET_NAMES = {
    "analises": "Análises",
    "oferecidos": "Oferecidos",
    "skillcorner": "SkillCorner",
    "wyscout": "WyScout",
}


def _load_google_sheet(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    """Load a single sheet from Google Sheets as CSV export (with timeout)."""
    import urllib.parse
    import io

    encoded = urllib.parse.quote(sheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded}"
    try:
        import urllib.request

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(raw), dtype=str, na_values=["", "-", "N/A", "nan"])
        logger.info("Loaded sheet '%s': %d rows x %d cols", sheet_name, len(df), len(df.columns))
        return df
    except Exception as e:
        logger.error("Failed to load sheet '%s': %s", sheet_name, e)
        return pd.DataFrame()


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
    """Load all sheets into memory — sequential with per-sheet timeout."""
    global _data, _data_loading

    for key, sheet_name in SHEET_NAMES.items():
        try:
            df = _load_google_sheet(GOOGLE_SHEET_ID, sheet_name)
            _data[key] = df
        except Exception as e:
            logger.error("Failed to load sheet '%s': %s", sheet_name, e)
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
    return {
        "status": "ready" if ready else "loading",
        "data_loaded": ready,
        "counts": counts,
    }


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
    _data_ready.clear()
    _load_all_data()
    return {
        "message": "Dados recarregados",
        "counts": {k: len(v) for k, v in _data.items()},
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

    players = []
    for idx, row in df.iterrows():
        pos_raw = str(row.get("Posição", "")) if pd.notna(row.get("Posição")) else None
        pos_cat = get_posicao_categoria(pos_raw) if pos_raw else None
        score = calculate_overall_score(row, pos_cat, df_all) if pos_cat else None

        players.append({
            "id": int(idx) if isinstance(idx, (int, np.integer)) else hash(str(idx)) % 10**8,
            "name": str(row.get("Jogador", "")),
            "display_name": str(row.get("JogadorDisplay", row.get("Jogador", ""))),
            "team": str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None,
            "position": pos_raw,
            "age": _safe_float(row.get("Idade")),
            "nationality": str(row.get("Naturalidade", "")) if pd.notna(row.get("Naturalidade")) else None,
            "league": resolve_actual_league(
                row.get("Equipa"),
                fallback_liga_tier=str(row.get("liga_tier", "")) if pd.notna(row.get("liga_tier")) else None,
            ),
            "minutes_played": _safe_float(row.get("Minutos jogados:")),
            "score": round(score, 1) if score else None,
        })

    return {"total": total, "players": players}


@app.get("/api/players/{player_display_name}/profile")
async def get_player_profile(
    player_display_name: str,
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
    sc_df = _data.get("skillcorner")
    if sc_df is not None and len(sc_df) > 0:
        sc_match = find_skillcorner_player(
            str(row.get("Jogador", "")),
            sc_df,
            team_name=str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None,
        )
        if sc_match is not None:
            sc_indices = SKILLCORNER_INDICES.get(position, [])
            sc_data = {}
            for idx_name in sc_indices:
                val = _safe_float(sc_match.get(idx_name))
                if val is not None:
                    sc_data[idx_name] = round(val, 2)

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
            league_target="Serie A Brasil",  # Botafogo-SP target league
            minutes=minutes_val,
        )

    return {
        "summary": {
            "id": idx_val,
            "name": str(row.get("Jogador", "")),
            "display_name": str(row.get("JogadorDisplay", "")),
            "team": str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None,
            "position": position,
            "age": age,
            "nationality": str(row.get("Naturalidade", "")) if pd.notna(row.get("Naturalidade")) else None,
            "league": league_actual or (str(row.get("liga_tier", "")) if pd.notna(row.get("liga_tier")) else None),
            "minutes_played": _safe_float(row.get("Minutos jogados:")),
            "score": round(score, 1) if score else None,
        },
        "metrics": metrics,
        "percentiles": percentiles,
        "indices": indices,
        "scout_score": round(score, 1) if score else None,
        "performance_class": perf_class,
        "skillcorner": sc_data,
        "projection_score": projection_score,
        "ssp_lambdas": SSP_LAMBDAS,
        "prediction": prediction,
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

        entries.append(RankingEntry(
            rank=rank,
            name=str(row.get("Jogador", "")),
            display_name=str(row.get("JogadorDisplay", row.get("Jogador", ""))),
            team=str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None,
            age=_safe_float(row.get("Idade")),
            league=resolve_actual_league(
                row.get("Equipa"),
                fallback_liga_tier=str(row.get("liga_tier", "")) if pd.notna(row.get("liga_tier")) else None,
            ),
            minutes=_safe_float(row.get("Minutos jogados:")),
            score=round(float(row.get("Score", 0)), 1),
            indices=idx_values,
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

        results.append({
            "name": str(row.get("Jogador", "")),
            "display_name": str(row.get("JogadorDisplay", row.get("Jogador", ""))),
            "team": str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None,
            "age": age,
            "league": league_origin,
            "minutes": minutes,
            "ssp": round(ssp, 1),
            "p_success": round(pred["success_probability"], 3),
            "risk_level": pred["risk_level"],
            "league_gap": round(pred["league_gap"], 1),
            "tier_origin": pred["tier_origin"],
            "tier_target": pred["tier_target"],
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


# ── Run ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
