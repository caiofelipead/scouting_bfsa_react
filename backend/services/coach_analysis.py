"""
coach_analysis.py — Coach evaluation and analysis service.
Loads coach profile and history data from PostgreSQL (synced from Google Sheets),
computes tactical scores, historical metrics, and composite rankings.
"""

import logging
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np

from services.database import load_sheet_dataframe

logger = logging.getLogger(__name__)

# ── Tactical dimensions (scores 1-10 from spreadsheet) ──────────────

TACTICAL_DIMENSIONS = [
    "Construção", "Pressing", "Trans_Ofensiva", "Trans_Defensiva",
    "Altura_Bloco", "Org_Ofensiva", "Flexibilidade", "Uso_Base", "Gestão",
]

TACTICAL_KEY_MAP = {
    "Construção": "construcao",
    "Pressing": "pressing",
    "Trans_Ofensiva": "trans_ofensiva",
    "Trans_Defensiva": "trans_defensiva",
    "Altura_Bloco": "altura_bloco",
    "Org_Ofensiva": "org_ofensiva",
    "Flexibilidade": "flexibilidade",
    "Uso_Base": "uso_base",
    "Gestão": "gestao",
}

# ── Division weights for weighted aproveitamento ─────────────────────

DIVISION_WEIGHTS = {
    "Serie A": 3.0,
    "Série A": 3.0,
    "Serie B": 2.0,
    "Série B": 2.0,
    "Serie C": 1.0,
    "Série C": 1.0,
    "Estadual": 0.5,
}

# ── Default composite score weights ─────────────────────────────────

DEFAULT_WEIGHTS = {
    "aproveitamento_ponderado": 0.30,
    "perfil_tatico": 0.25,
    "gestao": 0.15,
    "uso_base": 0.10,
    "estabilidade": 0.10,
    "flexibilidade": 0.10,
}


def _safe_float(val) -> Optional[float]:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    try:
        if isinstance(val, str):
            val = val.replace(",", ".").replace("%", "").strip()
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> Optional[int]:
    f = _safe_float(val)
    return int(f) if f is not None else None


# ── Data loading ────────────────────────────────────────────────────

_coaches_data: Dict[str, pd.DataFrame] = {}


def load_coaches_data(force: bool = False) -> Dict[str, pd.DataFrame]:
    """Load coach profile and history data from PostgreSQL."""
    global _coaches_data

    if not force and _coaches_data.get("perfil") is not None and len(_coaches_data["perfil"]) > 0:
        return _coaches_data

    try:
        perfil = load_sheet_dataframe("treinadores_perfil")
        historico = load_sheet_dataframe("treinadores_historico")
        _coaches_data["perfil"] = perfil
        _coaches_data["historico"] = historico
        logger.info(
            "Loaded coaches data: %d profiles, %d history rows",
            len(perfil), len(historico),
        )
    except Exception as e:
        logger.error("Failed to load coaches data: %s", e)
        _coaches_data["perfil"] = pd.DataFrame()
        _coaches_data["historico"] = pd.DataFrame()

    return _coaches_data


# ── Tactical radar extraction ────────────────────────────────────────

def extract_tactical(row: pd.Series) -> Dict[str, Optional[float]]:
    """Extract tactical radar scores from a profile row."""
    result = {}
    for sheet_col, key in TACTICAL_KEY_MAP.items():
        result[key] = _safe_float(row.get(sheet_col))
    return result


# ── Historical metrics computation ──────────────────────────────────

def compute_history_metrics(history_rows: List[Dict]) -> Dict[str, Any]:
    """Compute aggregate metrics from a coach's season history."""
    if not history_rows:
        return {}

    total_jogos = 0
    total_v = 0
    total_e = 0
    total_d = 0
    weighted_aprov_sum = 0.0
    weighted_aprov_weight = 0.0
    aproveitamentos = []
    clubs = {}
    demissoes = 0
    total_saidas = 0

    for row in history_rows:
        jogos = _safe_int(row.get("Jogos")) or 0
        v = _safe_int(row.get("V")) or 0
        e = _safe_int(row.get("E")) or 0
        d = _safe_int(row.get("D")) or 0
        divisao = str(row.get("Divisão") or row.get("Divisao") or "").strip()
        clube = str(row.get("Clube") or "").strip()
        temporada = str(row.get("Temporada") or "").strip()
        motivo = str(row.get("Motivo_Saída") or row.get("Motivo_Saida") or "").strip().lower()

        total_jogos += jogos
        total_v += v
        total_e += e
        total_d += d

        # Per-passage aproveitamento
        if jogos > 0:
            aprov = (v * 3 + e) / (jogos * 3) * 100
            aproveitamentos.append(aprov)

            # Weighted by division
            div_weight = DIVISION_WEIGHTS.get(divisao, 1.0)
            weighted_aprov_sum += aprov * div_weight * jogos
            weighted_aprov_weight += div_weight * jogos

        # Track clubs and seasons for stability
        if clube:
            if clube not in clubs:
                clubs[clube] = set()
            if temporada:
                clubs[clube].add(temporada)

        # Dismissal tracking
        if motivo:
            total_saidas += 1
            if "demitido" in motivo or "demissão" in motivo or "demissao" in motivo:
                demissoes += 1

    # Compute aggregates
    metrics: Dict[str, Any] = {}

    # Overall aproveitamento
    if total_jogos > 0:
        metrics["aproveitamento_geral"] = round((total_v * 3 + total_e) / (total_jogos * 3) * 100, 1)
    else:
        metrics["aproveitamento_geral"] = None

    # Weighted aproveitamento
    if weighted_aprov_weight > 0:
        metrics["aproveitamento_ponderado"] = round(weighted_aprov_sum / weighted_aprov_weight, 1)
    else:
        metrics["aproveitamento_ponderado"] = metrics.get("aproveitamento_geral")

    # Stability: average seasons per club
    if clubs:
        total_seasons = sum(len(seasons) for seasons in clubs.values())
        metrics["estabilidade"] = round(total_seasons / len(clubs), 2)
    else:
        metrics["estabilidade"] = None

    # Dismissal rate
    if total_saidas > 0:
        metrics["taxa_demissao"] = round(demissoes / total_saidas * 100, 1)
    else:
        metrics["taxa_demissao"] = 0.0

    # Best/worst aproveitamento
    if aproveitamentos:
        metrics["melhor_aproveitamento"] = round(max(aproveitamentos), 1)
        metrics["pior_aproveitamento"] = round(min(aproveitamentos), 1)
    else:
        metrics["melhor_aproveitamento"] = None
        metrics["pior_aproveitamento"] = None

    metrics["total_jogos"] = total_jogos
    metrics["total_vitorias"] = total_v
    metrics["total_empates"] = total_e
    metrics["total_derrotas"] = total_d
    metrics["clubes_count"] = len(clubs)

    return metrics


# ── Composite score ──────────────────────────────────────────────────

def compute_composite_score(
    tactical: Dict[str, Optional[float]],
    metrics: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """Compute a composite score (0-100) from tactical and historical metrics."""
    w = weights or DEFAULT_WEIGHTS

    components = {}

    # Aproveitamento ponderado (already 0-100)
    aprov = metrics.get("aproveitamento_ponderado")
    if aprov is not None:
        components["aproveitamento_ponderado"] = min(aprov, 100.0)
    else:
        components["aproveitamento_ponderado"] = 0.0

    # Tactical profile average (1-10 → 0-100)
    tac_values = [v for v in tactical.values() if v is not None and v > 0]
    if tac_values:
        components["perfil_tatico"] = (sum(tac_values) / len(tac_values)) * 10
    else:
        components["perfil_tatico"] = 0.0

    # Gestão (1-10 → 0-100)
    gestao = tactical.get("gestao")
    components["gestao"] = (gestao * 10) if gestao else 0.0

    # Uso base (1-10 → 0-100)
    uso_base = tactical.get("uso_base")
    components["uso_base"] = (uso_base * 10) if uso_base else 0.0

    # Estabilidade (seasons per club, normalize: 3+ is max)
    estab = metrics.get("estabilidade")
    if estab is not None:
        components["estabilidade"] = min(estab / 3.0, 1.0) * 100
    else:
        components["estabilidade"] = 0.0

    # Flexibilidade (1-10 → 0-100)
    flex = tactical.get("flexibilidade")
    components["flexibilidade"] = (flex * 10) if flex else 0.0

    # Penalize dismissal rate
    taxa = metrics.get("taxa_demissao", 0)
    if taxa and taxa > 50:
        components["aproveitamento_ponderado"] *= 0.85

    # Weighted sum
    score = 0.0
    total_weight = 0.0
    for key, weight in w.items():
        if key in components:
            score += components[key] * weight
            total_weight += weight

    if total_weight > 0:
        score = score / total_weight * (sum(w.values()) / 1.0)
        # Normalize to ensure 0-100
        score = max(0.0, min(100.0, score))

    return round(score, 1)


# ── High-level API functions ────────────────────────────────────────

def get_all_coaches(
    status: Optional[str] = None,
    nacionalidade: Optional[str] = None,
    licenca: Optional[str] = None,
    formacao: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return all coaches with optional filters."""
    data = load_coaches_data()
    perfil = data.get("perfil", pd.DataFrame())
    historico = data.get("historico", pd.DataFrame())

    if perfil.empty:
        return []

    # Build history index by ID_Treinador
    hist_by_id: Dict[str, List[Dict]] = {}
    if not historico.empty:
        for _, row in historico.iterrows():
            tid = str(row.get("ID_Treinador") or "").strip()
            if tid:
                hist_by_id.setdefault(tid, []).append(row.to_dict())

    results = []
    for _, row in perfil.iterrows():
        tid = str(row.get("ID_Treinador") or "").strip()
        if not tid:
            continue

        nome = str(row.get("Nome") or "").strip()
        s = str(row.get("Status") or "").strip()
        nac = str(row.get("Nacionalidade") or "").strip()
        lic = str(row.get("Licença") or row.get("Licenca") or "").strip()
        form_pref = str(row.get("Formação_Pref") or row.get("Formacao_Pref") or "").strip()

        # Apply filters
        if status and s.lower() != status.lower():
            continue
        if nacionalidade and nac.lower() != nacionalidade.lower():
            continue
        if licenca and lic.lower() != licenca.lower():
            continue
        if formacao and formacao.lower() not in form_pref.lower():
            continue

        tactical = extract_tactical(row)
        history = hist_by_id.get(tid, [])
        metrics = compute_history_metrics(history)
        score = compute_composite_score(tactical, metrics)

        results.append({
            "id_treinador": tid,
            "nome": nome,
            "nascimento": str(row.get("Nascimento") or "") or None,
            "nacionalidade": nac or None,
            "licenca": lic or None,
            "status": s or None,
            "faixa_salarial": str(row.get("Faixa_Salarial") or "") or None,
            "formacao_pref": form_pref or None,
            "formacao_alt": str(row.get("Formação_Alt") or row.get("Formacao_Alt") or "") or None,
            "clube_atual": str(row.get("Clube_Atual") or "") or None,
            "observacoes": str(row.get("Observações") or row.get("Observacoes") or "") or None,
            "tactical": tactical,
            "metricas": metrics,
            "score": score,
        })

    return results


def get_coach_by_id(coach_id: str) -> Optional[Dict[str, Any]]:
    """Return a single coach profile with full history."""
    coaches = get_all_coaches()
    for c in coaches:
        if c["id_treinador"] == coach_id:
            # Attach detailed history
            data = load_coaches_data()
            historico = data.get("historico", pd.DataFrame())
            seasons = []
            if not historico.empty:
                for _, row in historico.iterrows():
                    tid = str(row.get("ID_Treinador") or "").strip()
                    if tid == coach_id:
                        seasons.append({
                            "id_treinador": tid,
                            "clube": str(row.get("Clube") or "") or None,
                            "temporada": str(row.get("Temporada") or "") or None,
                            "divisao": str(row.get("Divisão") or row.get("Divisao") or "") or None,
                            "competicao": str(row.get("Competição") or row.get("Competicao") or "") or None,
                            "jogos": _safe_int(row.get("Jogos")),
                            "vitorias": _safe_int(row.get("V")),
                            "empates": _safe_int(row.get("E")),
                            "derrotas": _safe_int(row.get("D")),
                            "aproveitamento": _safe_float(row.get("Aproveitamento")),
                            "posicao_final": str(row.get("Posição_Final") or row.get("Posicao_Final") or "") or None,
                            "motivo_saida": str(row.get("Motivo_Saída") or row.get("Motivo_Saida") or "") or None,
                        })
            c["historico"] = seasons
            return c
    return None


def get_coach_history(coach_id: str) -> List[Dict[str, Any]]:
    """Return detailed season history for a coach."""
    data = load_coaches_data()
    historico = data.get("historico", pd.DataFrame())
    seasons = []
    if not historico.empty:
        for _, row in historico.iterrows():
            tid = str(row.get("ID_Treinador") or "").strip()
            if tid == coach_id:
                seasons.append({
                    "id_treinador": tid,
                    "clube": str(row.get("Clube") or "") or None,
                    "temporada": str(row.get("Temporada") or "") or None,
                    "divisao": str(row.get("Divisão") or row.get("Divisao") or "") or None,
                    "competicao": str(row.get("Competição") or row.get("Competicao") or "") or None,
                    "jogos": _safe_int(row.get("Jogos")),
                    "vitorias": _safe_int(row.get("V")),
                    "empates": _safe_int(row.get("E")),
                    "derrotas": _safe_int(row.get("D")),
                    "aproveitamento": _safe_float(row.get("Aproveitamento")),
                    "posicao_final": str(row.get("Posição_Final") or row.get("Posicao_Final") or "") or None,
                    "motivo_saida": str(row.get("Motivo_Saída") or row.get("Motivo_Saida") or "") or None,
                })
    return seasons


def compare_coaches(ids: List[str]) -> List[Dict[str, Any]]:
    """Compare up to 3 coaches side by side."""
    results = []
    for cid in ids[:3]:
        coach = get_coach_by_id(cid)
        if coach:
            results.append(coach)
    return results


def get_coach_ranking(
    weights: Optional[Dict[str, float]] = None,
    status: Optional[str] = None,
    nacionalidade: Optional[str] = None,
    licenca: Optional[str] = None,
    formacao: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return coaches ranked by composite score with configurable weights."""
    coaches = get_all_coaches(
        status=status,
        nacionalidade=nacionalidade,
        licenca=licenca,
        formacao=formacao,
    )

    # Recompute scores with custom weights if provided
    if weights:
        for c in coaches:
            c["score"] = compute_composite_score(c["tactical"], c["metricas"], weights)

    # Sort by score descending
    coaches.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Add rank
    for i, c in enumerate(coaches):
        c["rank"] = i + 1

    return coaches
