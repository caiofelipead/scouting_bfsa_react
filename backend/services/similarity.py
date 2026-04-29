"""
similarity.py v2 - Weighted Metrics Engine
===========================================
Modulo unificado de ponderacao para todo o dashboard.

Funcoes:
    - calculate_weighted_index()            -> Tabs 1,2,3 (substitui calculate_index)
    - calculate_all_indices()               -> Tabs 1,2,3 (todos os indices de uma vez)
    - calculate_overall_score()             -> Tab 6 (score unico para ranking)
    - rank_players_weighted()               -> Tab 6 (ranking batch otimizado)
    - get_top_metrics_for_position()        -> Tabs 1,3 (top N metricas por peso)
    - calculate_metric_percentiles()        -> Tabs 1,3 (percentis para radar)
    - compute_weighted_cosine_similarity()  -> Tab 7 (similaridade)
    - get_similarity_breakdown()            -> Tab 7 (detalhamento)

Import no app.py:
    from similarity import (
        compute_weighted_cosine_similarity, get_similarity_breakdown,
        calculate_weighted_index, calculate_all_indices,
        calculate_overall_score, rank_players_weighted,
        get_top_metrics_for_position, calculate_metric_percentiles,
        POSITION_WEIGHTS, INVERTED_METRICS
    )
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Tuple

# ============================================
# POSITION_WEIGHTS
# ============================================
POSITION_WEIGHTS = {
    'Atacante': {
        'Golos/90': 3.0, 'Golos esperados/90': 2.5, 'Golos sem ser por penalti/90': 2.5,
        'Remates/90': 1.5, 'Remates a baliza, %': 2.0, 'Golos marcados, %': 1.5,
        'Toques na area/90': 1.5, 'Golos de cabeca/90': 1.0,
        'Dribles/90': 1.5, 'Dribles com sucesso, %': 1.5,
        'Duelos ofensivos/90': 1.0, 'Duelos ofensivos ganhos, %': 1.0,
        'Aceleracoes/90': 1.0, 'Faltas sofridas/90': 0.5,
        'Duelos aerios/90': 1.5, 'Duelos aereos ganhos, %': 1.5,
        'Corridas progressivas/90': 1.0, 'Recesao de passes em profundidade/90': 1.5,
        'Passes longos recebidos/90': 0.5,
        'Passes recebidos/90': 0.5, 'Passes/90': 0.5, 'Passes certos, %': 0.5,
        'Assistencias/90': 1.5, 'Assistencias esperadas/90': 1.5,
        'Segundas assistencias/90': 0.5, 'Passes chave/90': 1.0,
        'Passes inteligentes/90': 0.5, 'Passes em profundidade/90': 0.5,
        'Acoes defensivas com exito/90': 0.5,
    },
    'Extremo': {
        'Golos/90': 2.0, 'Golos esperados/90': 2.0, 'Remates/90': 1.0,
        'Remates a baliza, %': 1.0, 'Toques na area/90': 1.0, 'Golos marcados, %': 1.0,
        'Assistencias/90': 2.5, 'Assistencias esperadas/90': 2.5,
        'Passes chave/90': 2.0, 'Passes inteligentes/90': 2.0,
        'Segundas assistencias/90': 1.0, 'Terceiras assistencias/90': 0.5,
        'Passes para a area de penalti/90': 1.5,
        'Dribles/90': 2.5, 'Dribles com sucesso, %': 2.0,
        'Duelos ofensivos/90': 1.5, 'Duelos ofensivos ganhos, %': 1.5,
        'Faltas sofridas/90': 0.5, 'Aceleracoes/90': 1.5,
        'Corridas progressivas/90': 2.0, 'Passes progressivos/90': 1.0,
        'Passes progressivos certos, %': 0.5, 'Passes para terco final/90': 1.0,
        'Cruzamentos/90': 1.5, 'Cruzamentos certos, %': 1.0,
        'Cruzamentos para a area de baliza/90': 1.0,
        'Acoes defensivas com exito/90': 0.5,
        'Duelos defensivos/90': 0.5, 'Duelos defensivos ganhos, %': 0.5,
    },
    'Meia': {
        'Assistencias/90': 2.5, 'Assistencias esperadas/90': 2.5,
        'Passes chave/90': 2.5, 'Passes inteligentes/90': 2.5,
        'Passes inteligentes certos, %': 2.0,
        'Segundas assistencias/90': 1.5, 'Terceiras assistencias/90': 1.0,
        'Passes para a area de penalti/90': 2.0,
        'Passes precisos para a area de penalti, %': 1.0,
        'Passes progressivos/90': 2.0, 'Passes progressivos certos, %': 1.5,
        'Corridas progressivas/90': 1.5,
        'Passes para terco final/90': 1.5, 'Passes certos para terco final, %': 1.0,
        'Passes em profundidade/90': 2.0, 'Passes em profundidade certos, %': 1.0,
        'Passes/90': 1.0, 'Passes certos, %': 1.5,
        'Passes longos/90': 1.0, 'Passes longos certos, %': 1.0,
        'Passes para a frente/90': 1.0, 'Passes para a frente certos, %': 0.5,
        'Golos/90': 1.5, 'Golos esperados/90': 1.5, 'Remates/90': 0.5,
        'Toques na area/90': 1.0,
        'Dribles/90': 1.5, 'Dribles com sucesso, %': 1.0, 'Duelos ofensivos/90': 0.5,
        'Acoes defensivas com exito/90': 1.5,
        'Duelos defensivos/90': 0.5, 'Duelos defensivos ganhos, %': 0.5,
        'Intersecoes/90': 0.5,
    },
    'Volante': {
        'Acoes defensivas com exito/90': 2.5, 'Intersecoes/90': 2.5,
        'Intercecoes ajust. a posse': 2.5,
        'Duelos defensivos/90': 2.0, 'Duelos defensivos ganhos, %': 2.0,
        'Cortes/90': 1.5, 'Cortes de carrinho ajust. a posse': 1.5,
        'Remates intercetados/90': 1.0,
        'Duelos/90': 1.5, 'Duelos ganhos, %': 1.5,
        'Duelos aerios/90': 1.5, 'Duelos aereos ganhos, %': 1.5,
        'Passes/90': 1.5, 'Passes certos, %': 2.0,
        'Passes longos/90': 1.5, 'Passes longos certos, %': 1.5,
        'Passes para a frente/90': 1.0, 'Passes para a frente certos, %': 1.0,
        'Passes progressivos/90': 2.0, 'Passes progressivos certos, %': 1.0,
        'Passes para terco final/90': 1.0,
        'Corridas progressivas/90': 0.5, 'Passes em profundidade/90': 0.5,
        'Passes inteligentes/90': 1.5, 'Passes em profundidade certos, %': 0.5,
        'Faltas/90': 1.0, 'Cartoes amarelos/90': 0.5,
    },
    'Lateral direito': {
        'Cruzamentos/90': 1.5, 'Cruzamentos certos, %': 2.0,
        'Cruzamentos para a area de baliza/90': 1.5,
        'Passes para terco final/90': 1.5, 'Passes certos para terco final, %': 1.0,
        'Toques na area/90': 1.0, 'Passes para a area de penalti/90': 1.5,
        'Corridas progressivas/90': 2.5, 'Passes progressivos/90': 1.5,
        'Passes progressivos certos, %': 1.0, 'Aceleracoes/90': 1.5,
        'Passes em profundidade/90': 1.5,
        'Dribles/90': 1.5, 'Dribles com sucesso, %': 1.0,
        'Duelos ofensivos/90': 1.0, 'Duelos ofensivos ganhos, %': 1.0,
        'Faltas sofridas/90': 0.5,
        'Duelos defensivos/90': 2.0, 'Duelos defensivos ganhos, %': 2.0,
        'Intersecoes/90': 1.5, 'Cortes/90': 1.0,
        'Acoes defensivas com exito/90': 1.5, 'Remates intercetados/90': 0.5,
        'Duelos/90': 1.0, 'Duelos ganhos, %': 1.0,
        'Duelos aerios/90': 1.0, 'Duelos aereos ganhos, %': 1.0,
        'Assistencias/90': 1.5, 'Assistencias esperadas/90': 1.5, 'Passes chave/90': 1.0,
        'Passes inteligentes/90': 1.0,
    },
    'Lateral esquerdo': {
        'Cruzamentos/90': 1.5, 'Cruzamentos certos, %': 2.0,
        'Cruzamentos para a area de baliza/90': 1.5,
        'Passes para terco final/90': 1.5, 'Passes certos para terco final, %': 1.0,
        'Toques na area/90': 1.0, 'Passes para a area de penalti/90': 1.5,
        'Corridas progressivas/90': 2.5, 'Passes progressivos/90': 1.5,
        'Passes progressivos certos, %': 1.0, 'Aceleracoes/90': 1.5,
        'Passes em profundidade/90': 1.5,
        'Dribles/90': 1.5, 'Dribles com sucesso, %': 1.0,
        'Duelos ofensivos/90': 1.0, 'Duelos ofensivos ganhos, %': 1.0,
        'Faltas sofridas/90': 0.5,
        'Duelos defensivos/90': 2.0, 'Duelos defensivos ganhos, %': 2.0,
        'Intersecoes/90': 1.5, 'Cortes/90': 1.0,
        'Acoes defensivas com exito/90': 1.5, 'Remates intercetados/90': 0.5,
        'Duelos/90': 1.0, 'Duelos ganhos, %': 1.0,
        'Duelos aerios/90': 1.0, 'Duelos aereos ganhos, %': 1.0,
        'Assistencias/90': 1.5, 'Assistencias esperadas/90': 1.5, 'Passes chave/90': 1.0,
        'Passes inteligentes/90': 1.0,
    },
    'Zagueiro': {
        'Duelos defensivos/90': 2.5, 'Duelos defensivos ganhos, %': 2.5,
        'Cortes/90': 2.0, 'Cortes de carrinho ajust. a posse': 1.5,
        'Acoes defensivas com exito/90': 2.0,
        'Duelos aerios/90': 2.5, 'Duelos aereos ganhos, %': 2.5,
        'Golos de cabeca/90': 0.5,
        'Intersecoes/90': 2.0, 'Intercecoes ajust. a posse': 2.0,
        'Remates intercetados/90': 1.0,
        'Passes/90': 1.5, 'Passes certos, %': 2.0,
        'Passes longos/90': 1.5, 'Passes longos certos, %': 1.5,
        'Passes para a frente/90': 1.0, 'Passes para a frente certos, %': 1.5,
        'Passes progressivos/90': 1.5, 'Passes progressivos certos, %': 0.5,
        'Passes para terco final/90': 0.5, 'Corridas progressivas/90': 0.5,
        'Passes inteligentes/90': 1.0, 'Passes em profundidade/90': 0.5,
        'Faltas/90': 1.0, 'Cartoes amarelos/90': 0.5,
    },
    'Goleiro': {
        'Defesas, %': 2.5,
        'Golos sofridos/90': 2.5,
        'Remates sofridos/90': 1.0,
        'Golos sofridos esperados/90': 2.0,
        'Golos expectaveis defendidos por 90': 3.0,
        'Duelos aerios/90.1': 1.5, 'Saidas/90': 2.0,
        'Passes para tras recebidos pelo guarda-redes/90': 1.0,
        'Passes longos certos, %': 2.0,
    },
}

INVERTED_METRICS = frozenset({
    'Faltas/90', 'Cartoes amarelos/90', 'Cartoes vermelhos/90',
    'Golos sofridos/90', 'Remates sofridos/90', 'Golos sofridos esperados/90',
})


# ============================================
# HELPERS
# ============================================

def _safe_float(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    try:
        if isinstance(val, str):
            val = val.replace(',', '.')
        return float(val)
    except (ValueError, TypeError):
        return None

def _percentile_rank(value, series):
    valid = pd.to_numeric(series, errors='coerce').dropna()
    if len(valid) == 0:
        return 50.0
    return float((valid < value).sum() / len(valid) * 100)


# ============================================
# VECTORIZED PERCENTILE CACHE (Performance)
# ============================================
# Pre-computes percentile ranks for ALL players × ALL numeric columns
# at once using pandas.rank(). Subsequent lookups are O(1) dict access.

_percentile_cache: Dict[int, pd.DataFrame] = {}
_percentile_cache_id: Optional[int] = None


def _get_percentile_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame where each cell = percentile rank (0-100) of that player's value.

    Cached by DataFrame id so it's computed once per data load.
    """
    global _percentile_cache_id, _percentile_cache

    df_id = id(df)
    if df_id in _percentile_cache:
        return _percentile_cache[df_id]

    # Convert all columns to numeric, keep only numeric ones
    numeric_df = df.apply(lambda col: pd.to_numeric(
        col.apply(lambda v: str(v).replace(',', '.') if isinstance(v, str) else v),
        errors='coerce'
    ))

    # Compute percentile ranks using pandas (vectorized, fast)
    # pct=True gives 0-1, multiply by 100 for 0-100
    perc_df = numeric_df.rank(pct=True, na_option='keep') * 100

    # Keep only one cache entry to avoid memory bloat
    _percentile_cache.clear()
    _percentile_cache[df_id] = perc_df
    _percentile_cache_id = df_id
    return perc_df


def _fast_percentile(player_idx, col: str, perc_matrix: pd.DataFrame) -> float:
    """O(1) percentile lookup from pre-computed matrix.

    Returns NaN if the player isn't in the percentile base (e.g. a non-Serie B
    player ranked against a Serie B-only matrix). Callers must fall back to the
    value-based slow path so the player is still ranked relative to that base.
    """
    try:
        val = perc_matrix.at[player_idx, col]
        if pd.isna(val):
            return float('nan')
        return float(val)
    except (KeyError, ValueError):
        return float('nan')


def invalidate_percentile_cache():
    """Call when data is reloaded to clear the cache."""
    global _percentile_cache, _percentile_cache_id
    _percentile_cache.clear()
    _percentile_cache_id = None

def _resolve_metric(metric, columns):
    if metric in columns:
        return metric
    import unicodedata
    def strip_acc(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    m_stripped = strip_acc(metric)
    for col in columns:
        if strip_acc(col) == m_stripped:
            return col
    return None

def _is_inverted(metric_name):
    if metric_name in INVERTED_METRICS:
        return True
    m_lower = metric_name.lower()
    if 'faltas/90' in m_lower and 'sofridas' not in m_lower:
        return True
    if 'cart' in m_lower and '/90' in m_lower:
        return True
    if 'sofridos' in m_lower and 'golos' in m_lower:
        return True
    if 'remates sofridos' in m_lower:
        return True
    return False


# ============================================
# WEIGHTED INDEX (substitui calculate_index)
# ============================================

def calculate_weighted_index(player_row, metrics, df_all, position=None, _perc_matrix=None):
    """
    Drop-in replacement para calculate_index().
    Usa POSITION_WEIGHTS para ponderar. Se position=None, media simples.
    Returns float 0-100.
    Accepts optional _perc_matrix for batch optimization (avoids recomputing).
    """
    weights = POSITION_WEIGHTS.get(position, {}) if position else {}
    columns_available = set(player_row.index) & set(df_all.columns)
    weighted_sum = 0.0
    total_weight = 0.0

    # Use pre-computed percentile matrix if available
    use_cache = _perc_matrix is not None and hasattr(player_row, 'name')
    player_idx = player_row.name if use_cache else None

    for metric in metrics:
        resolved = _resolve_metric(metric, columns_available)
        if resolved is None:
            continue
        val = _safe_float(player_row[resolved])
        if val is None:
            continue

        perc = float('nan')
        if use_cache and resolved in _perc_matrix.columns:
            perc = _fast_percentile(player_idx, resolved, _perc_matrix)
        if np.isnan(perc):  # player not in percentile base — rank by value instead
            perc = _percentile_rank(val, df_all[resolved])

        if _is_inverted(metric):
            perc = 100.0 - perc

        w = 1.0
        if weights:
            w = weights.get(metric, 0)
            if w == 0:
                resolved_w = _resolve_metric(metric, set(weights.keys()))
                w = weights.get(resolved_w, 1.0) if resolved_w else 1.0

        weighted_sum += perc * w
        total_weight += w

    if total_weight == 0:
        return 50.0
    return weighted_sum / total_weight


def calculate_all_indices(player_row, indices_config, df_all, position=None):
    """Calcula todos os indices compostos de uma posicao."""
    return {
        idx_name: calculate_weighted_index(player_row, metrics, df_all, position)
        for idx_name, metrics in indices_config.items()
    }


# ============================================
# OVERALL SCORE (Tab 6 ranking)
# ============================================

def calculate_overall_score(player_row, position, df_all, _perc_matrix=None):
    """
    Score unico 0-100 usando TODAS as metricas de POSITION_WEIGHTS.
    Returns float 0-100 ou None.
    Accepts optional _perc_matrix for batch optimization.
    """
    weights = POSITION_WEIGHTS.get(position)
    if not weights:
        return None
    columns_available = set(player_row.index) & set(df_all.columns)
    weighted_sum = 0.0
    total_weight = 0.0
    matched = 0

    use_cache = _perc_matrix is not None and hasattr(player_row, 'name')
    player_idx = player_row.name if use_cache else None

    for metric, w in weights.items():
        resolved = _resolve_metric(metric, columns_available)
        if resolved is None:
            continue
        val = _safe_float(player_row[resolved])
        if val is None:
            continue

        perc = float('nan')
        if use_cache and resolved in _perc_matrix.columns:
            perc = _fast_percentile(player_idx, resolved, _perc_matrix)
        if np.isnan(perc):  # player not in percentile base — rank by value instead
            perc = _percentile_rank(val, df_all[resolved])

        if metric in INVERTED_METRICS:
            perc = 100.0 - perc
        weighted_sum += perc * w
        total_weight += w
        matched += 1

    if matched < 5 or total_weight == 0:
        return None
    return weighted_sum / total_weight


def rank_players_weighted(df_players, position, df_percentile_base,
                          indices_config=None, min_minutes=0,
                          minutes_col='Minutos jogados:',
                          include_indices=True):
    """
    Ranking batch. Calcula Score + indices compostos ponderados.
    Uses vectorized percentile matrix for O(1) lookups (10-50x faster).
    Returns DataFrame ordenado por Score desc com colunas extras.
    """
    pool = df_players.copy()
    pool[minutes_col] = pool[minutes_col].apply(_safe_float)
    pool = pool[pool[minutes_col] >= min_minutes]
    if len(pool) == 0:
        return pd.DataFrame()

    # Pre-compute percentile matrix once (vectorized)
    perc_matrix = _get_percentile_matrix(df_percentile_base)

    scores = []
    for idx, row in pool.iterrows():
        score = calculate_overall_score(row, position, df_percentile_base, _perc_matrix=perc_matrix)
        if score is None:
            continue
        entry = {'_idx': idx, 'Score': round(score, 1)}
        if include_indices and indices_config:
            for idx_name, metrics in indices_config.items():
                val = calculate_weighted_index(row, metrics, df_percentile_base, position, _perc_matrix=perc_matrix)
                entry[idx_name] = round(val, 1)
        scores.append(entry)

    if not scores:
        return pd.DataFrame()

    df_scores = pd.DataFrame(scores).sort_values('Score', ascending=False)
    out = pool.loc[df_scores['_idx']].copy()
    out['Score'] = df_scores.set_index('_idx')['Score']
    if include_indices and indices_config:
        for col in indices_config.keys():
            if col in df_scores.columns:
                out[col] = df_scores.set_index('_idx')[col]
    return out.sort_values('Score', ascending=False)


# ============================================
# TOP METRICS (radares Tabs 1,3)
# ============================================

def get_top_metrics_for_position(position, top_n=12):
    """Top N metricas por peso para uma posicao."""
    weights = POSITION_WEIGHTS.get(position, {})
    return sorted(weights.items(), key=lambda x: -x[1])[:top_n]


def calculate_metric_percentiles(player_row, position, df_all, top_n=12):
    """Percentis das top metricas. Retorna dict {short_name: percentil}."""
    top_metrics = get_top_metrics_for_position(position, top_n)
    columns_available = set(player_row.index) & set(df_all.columns)
    perc_matrix = _get_percentile_matrix(df_all)
    use_cache = hasattr(player_row, 'name')
    player_idx = player_row.name if use_cache else None
    result = {}
    for metric, w in top_metrics:
        resolved = _resolve_metric(metric, columns_available)
        if resolved is None:
            continue
        val = _safe_float(player_row[resolved])
        if val is None:
            continue
        perc = float('nan')
        if use_cache and resolved in perc_matrix.columns:
            perc = _fast_percentile(player_idx, resolved, perc_matrix)
        if np.isnan(perc):  # player not in percentile base — rank by value instead
            perc = _percentile_rank(val, df_all[resolved])
        if metric in INVERTED_METRICS:
            perc = 100.0 - perc
        short = metric.replace('/90', '').replace(', %', '%')
        if len(short) > 20:
            short = short[:20]
        result[short] = round(perc, 1)
    return result


# ============================================
# COSINE SIMILARITY (Tab 7)
# ============================================

def compute_weighted_cosine_similarity(
    target_player, comparison_pool, position, top_n=20,
    min_minutes=500, minutes_col='Minutos jogados:',
    player_display_col='JogadorDisplay', percentile_base=None,
):
    weights = POSITION_WEIGHTS.get(position)
    if weights is None:
        return pd.DataFrame()
    if percentile_base is None:
        percentile_base = comparison_pool

    pool = comparison_pool.copy()
    pool[minutes_col] = pool[minutes_col].apply(_safe_float)
    pool = pool[pool[minutes_col] >= min_minutes]
    if player_display_col in pool.columns and player_display_col in target_player.index:
        pool = pool[pool[player_display_col] != target_player[player_display_col]]
    if len(pool) == 0:
        return pd.DataFrame()

    col_set = set(target_player.index) & set(pool.columns)
    metric_map = {}
    for m in weights:
        resolved = _resolve_metric(m, col_set)
        if resolved:
            metric_map[m] = resolved
    if len(metric_map) < 5:
        return pd.DataFrame()

    target_percs = {}
    for m_key, m_col in metric_map.items():
        val = _safe_float(target_player[m_col])
        if val is not None:
            perc = _percentile_rank(val, percentile_base[m_col])
            if m_key in INVERTED_METRICS:
                perc = 100.0 - perc
            target_percs[m_key] = (perc, m_col)

    metrics_list = list(target_percs.keys())
    if len(metrics_list) < 5:
        return pd.DataFrame()

    t_vec = np.array([target_percs[m][0] for m in metrics_list])
    w_vec = np.array([weights[m] for m in metrics_list])
    wt = t_vec * w_vec
    if np.linalg.norm(wt) == 0:
        return pd.DataFrame()

    results = []
    for idx, row in pool.iterrows():
        cand_percs = {}
        for m_key in metrics_list:
            m_col = target_percs[m_key][1]
            val = _safe_float(row[m_col])
            if val is not None:
                perc = _percentile_rank(val, percentile_base[m_col])
                if m_key in INVERTED_METRICS:
                    perc = 100.0 - perc
                cand_percs[m_key] = perc

        common = [m for m in metrics_list if m in cand_percs]
        if len(common) < 5:
            continue

        tv = np.array([target_percs[m][0] for m in common])
        cv = np.array([cand_percs[m] for m in common])
        wv = np.array([weights[m] for m in common])
        wtv = tv * wv
        wcv = cv * wv
        n_t = np.linalg.norm(wtv)
        n_c = np.linalg.norm(wcv)
        if n_t == 0 or n_c == 0:
            continue

        cosine_sim = np.dot(wtv, wcv) / (n_t * n_c)
        proximity = max(0.0, 1.0 - np.mean(np.abs(tv - cv) * wv) / 100.0)
        similarity = (0.70 * cosine_sim + 0.30 * proximity) * 100.0

        results.append({
            '_idx': idx,
            'similarity_pct': round(similarity, 1),
            'matched_metrics': len(common),
        })

    if not results:
        return pd.DataFrame()

    df_r = pd.DataFrame(results).sort_values('similarity_pct', ascending=False).head(top_n)
    out = pool.loc[df_r['_idx']].copy()
    out['similarity_pct'] = df_r.set_index('_idx')['similarity_pct']
    out['matched_metrics'] = df_r.set_index('_idx')['matched_metrics']
    return out.sort_values('similarity_pct', ascending=False)


def get_similarity_breakdown(target, similar, position, percentile_base=None):
    weights = POSITION_WEIGHTS.get(position, {})
    rows = []
    for metric, weight in weights.items():
        t_val = _safe_float(target.get(metric))
        s_val = _safe_float(similar.get(metric))
        if t_val is not None and s_val is not None:
            rows.append({
                'Metrica': metric, 'Peso': weight,
                'Referencia': round(t_val, 2), 'Similar': round(s_val, 2),
                'Diferenca': round(s_val - t_val, 2),
                'Invertida': 'sim' if metric in INVERTED_METRICS else '',
            })
    return pd.DataFrame(rows)
