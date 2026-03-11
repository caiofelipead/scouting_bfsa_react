"""
main.py — FastAPI Scouting API for Botafogo-SP
===============================================
Replaces the Streamlit monolith with async REST endpoints.
"""

import os
import logging
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
from services.fuzzy_match import build_skillcorner_index, find_skillcorner_player
from config.mappings import (
    CLUB_LOGOS,
    COUNTRY_FLAGS,
    INDICES_CONFIG,
    LEAGUE_LOGOS,
    POSICAO_MAP,
    POSICOES_DISPLAY,
    SKILLCORNER_INDICES,
    WYSCOUT_LEAGUE_MAP,
    get_posicao_categoria,
    resolve_league_to_tier,
)

logger = logging.getLogger(__name__)

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
    """Load a single sheet from Google Sheets as CSV export."""
    import urllib.parse

    encoded = urllib.parse.quote(sheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded}"
    try:
        df = pd.read_csv(url, dtype=str, na_values=["", "-", "N/A", "nan"])
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


def _load_all_data():
    """Load all sheets into memory."""
    global _data
    for key, sheet_name in SHEET_NAMES.items():
        _data[key] = _load_google_sheet(GOOGLE_SHEET_ID, sheet_name)

    if "wyscout" in _data and len(_data["wyscout"]) > 0:
        _data["wyscout"] = _prepare_wyscout(_data["wyscout"])

    if "skillcorner" in _data and len(_data["skillcorner"]) > 0:
        sc_text = {"player_name", "short_name", "team_name", "position_group"}
        _data["skillcorner"] = _coerce_numeric_columns(_data["skillcorner"], sc_text)
        build_skillcorner_index(_data["skillcorner"])

    logger.info("All data loaded successfully")


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _load_all_data()
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
    _load_all_data()
    return {
        "message": "Dados recarregados",
        "counts": {k: len(v) for k, v in _data.items()},
    }


# ══════════════════════════════════════════════════════════════════════
# PLAYER ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

def _get_wyscout() -> pd.DataFrame:
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
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    df = _get_wyscout()

    if position:
        cat = get_posicao_categoria(position)
        if "Posição" in df.columns:
            df = df[df["Posição"].apply(lambda p: get_posicao_categoria(p) == cat if pd.notna(p) else False)]

    if league and "liga_tier" in df.columns:
        df = df[df["liga_tier"] == league]

    if min_minutes > 0 and "Minutos jogados:" in df.columns:
        df["_min"] = df["Minutos jogados:"].apply(_safe_float)
        df = df[df["_min"] >= min_minutes]

    if search and "JogadorDisplay" in df.columns:
        search_lower = search.lower()
        df = df[df["JogadorDisplay"].str.lower().str.contains(search_lower, na=False)]

    total = len(df)
    df = df.iloc[offset: offset + limit]

    players = []
    for idx, row in df.iterrows():
        players.append({
            "id": int(idx) if isinstance(idx, (int, np.integer)) else hash(str(idx)) % 10**8,
            "name": str(row.get("Jogador", "")),
            "display_name": str(row.get("JogadorDisplay", row.get("Jogador", ""))),
            "team": str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None,
            "position": str(row.get("Posição", "")) if pd.notna(row.get("Posição")) else None,
            "age": _safe_float(row.get("Idade")),
            "nationality": str(row.get("Naturalidade", "")) if pd.notna(row.get("Naturalidade")) else None,
            "league": str(row.get("liga_tier", "")) if pd.notna(row.get("liga_tier")) else None,
            "minutes_played": _safe_float(row.get("Minutos jogados:")),
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

    return {
        "summary": {
            "id": idx_val,
            "name": str(row.get("Jogador", "")),
            "display_name": str(row.get("JogadorDisplay", "")),
            "team": str(row.get("Equipa", "")) if pd.notna(row.get("Equipa")) else None,
            "position": position,
            "age": _safe_float(row.get("Idade")),
            "nationality": str(row.get("Naturalidade", "")) if pd.notna(row.get("Naturalidade")) else None,
            "league": str(row.get("liga_tier", "")) if pd.notna(row.get("liga_tier")) else None,
            "minutes_played": _safe_float(row.get("Minutos jogados:")),
            "score": round(score, 1) if score else None,
        },
        "metrics": metrics,
        "percentiles": percentiles,
        "indices": indices,
        "scout_score": round(score, 1) if score else None,
        "performance_class": perf_class,
        "skillcorner": sc_data,
    }


# ══════════════════════════════════════════════════════════════════════
# RANKING ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.post("/api/rankings", response_model=RankingResponse)
async def get_rankings(
    req: RankingRequest,
    current_user: dict = Depends(get_current_user),
):
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
        return RankingResponse(position=position, total=0, players=[])

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
            league=str(row.get("liga_tier", "")) if pd.notna(row.get("liga_tier")) else None,
            minutes=_safe_float(row.get("Minutos jogados:")),
            score=round(float(row.get("Score", 0)), 1),
            indices=idx_values,
        ))

    return RankingResponse(position=position, total=len(entries), players=entries)


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
# HEALTH
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "data_loaded": {k: len(v) for k, v in _data.items()},
    }


# ── Run ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
