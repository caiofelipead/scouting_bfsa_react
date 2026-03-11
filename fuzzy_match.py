"""
fuzzy_match.py — Match WyScout ↔ SkillCorner
==============================================
Drop-in replacement para find_skillcorner_player() do app.py.
Usa indice invertido + rapidfuzz para O(1) lookup ao inves de O(n) por query.

Import ja presente no app.py (linha 3):
    from fuzzy_match import build_skillcorner_index, find_skillcorner_player
"""

import unicodedata
import re
from typing import Optional, Dict, Tuple
import pandas as pd
from rapidfuzz import fuzz, process

# ============================================
# NORMALIZACAO
# ============================================

def _normalize(name: str) -> str:
    """Remove acentos, lowercase, strip extra spaces."""
    if not name or pd.isna(name):
        return ""
    name = unicodedata.normalize('NFD', str(name))
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = re.sub(r'[^a-z0-9\s]', '', name.lower())
    return ' '.join(name.split())


def _tokenize(name: str) -> set:
    """Retorna set de tokens do nome normalizado."""
    return set(_normalize(name).split())


def _rapidfuzz_score(s1: str, s2: str) -> float:
    """
    Similarity score 0-1 using rapidfuzz.
    Returns the max of fuzz.ratio and fuzz.token_sort_ratio, normalized to 0-1.
    """
    if not s1 or not s2:
        return 0.0
    ratio = fuzz.ratio(s1, s2) / 100.0
    token_sort = fuzz.token_sort_ratio(s1, s2) / 100.0
    return max(ratio, token_sort)


# ============================================
# INDICE INVERTIDO
# ============================================

class SkillCornerIndex:
    """Indice invertido token->rows para busca O(1)."""

    def __init__(self):
        self.token_to_indices: Dict[str, set] = {}
        self.exact_map: Dict[str, int] = {}        # nome_normalizado -> idx
        self.short_map: Dict[str, int] = {}         # short_name_normalizado -> idx
        self.df: Optional[pd.DataFrame] = None

    def build(self, df: pd.DataFrame, name_col: str = 'player_name',
              short_col: str = 'short_name', team_col: str = 'team_name'):
        """Constroi indice a partir do DataFrame SkillCorner."""
        self.df = df
        self.token_to_indices = {}
        self.exact_map = {}
        self.short_map = {}

        for idx, row in df.iterrows():
            # Index por player_name
            pname = _normalize(str(row.get(name_col, '')))
            if pname:
                self.exact_map[pname] = idx
                for token in pname.split():
                    if len(token) >= 2:
                        self.token_to_indices.setdefault(token, set()).add(idx)

            # Index por short_name
            if short_col in df.columns:
                sname = _normalize(str(row.get(short_col, '')))
                if sname and sname != pname:
                    self.short_map[sname] = idx
                    for token in sname.split():
                        if len(token) >= 2:
                            self.token_to_indices.setdefault(token, set()).add(idx)

            # Index por team_name (boost de confianca)
            if team_col in df.columns:
                tname = _normalize(str(row.get(team_col, '')))
                if tname:
                    for token in tname.split():
                        if len(token) >= 3:
                            self.token_to_indices.setdefault(f'_team_{token}', set()).add(idx)

    def query(self, name: str, team: str = None,
              name_col: str = 'player_name',
              threshold: float = 0.70) -> Optional[pd.Series]:
        """
        Busca jogador no indice.

        Returns:
            pd.Series da melhor match ou None
        """
        if self.df is None or not name:
            return None

        name_norm = _normalize(name)
        if not name_norm:
            return None

        # 1) Match exato no player_name
        if name_norm in self.exact_map:
            return self.df.loc[self.exact_map[name_norm]]

        # 2) Match exato no short_name
        if name_norm in self.short_map:
            return self.df.loc[self.short_map[name_norm]]

        # 3) Busca por tokens — reunir candidatos
        tokens = name_norm.split()
        candidate_counts: Dict[int, int] = {}

        for token in tokens:
            if token in self.token_to_indices:
                for idx in self.token_to_indices[token]:
                    candidate_counts[idx] = candidate_counts.get(idx, 0) + 1

        # Boost por team match
        team_indices = set()
        if team:
            team_norm = _normalize(team)
            for token in team_norm.split():
                key = f'_team_{token}'
                if key in self.token_to_indices:
                    team_indices.update(self.token_to_indices[key])

        if not candidate_counts:
            return None

        # 4) Scoring dos candidatos
        best_score = 0.0
        best_idx = None

        # Ordenar por contagem de tokens (mais tokens em comum -> prioridade)
        sorted_candidates = sorted(candidate_counts.items(), key=lambda x: -x[1])

        # Limitar a top 30 candidatos para performance
        for idx, token_count in sorted_candidates[:30]:
            row = self.df.loc[idx]
            player_name_norm = _normalize(str(row.get(name_col, '')))

            # Similaridade no nome completo (rapidfuzz)
            sim_full = _rapidfuzz_score(name_norm, player_name_norm)

            # Similaridade no short_name (se existir)
            sim_short = 0.0
            if 'short_name' in row.index:
                short_norm = _normalize(str(row.get('short_name', '')))
                if short_norm:
                    sim_short = _rapidfuzz_score(name_norm, short_norm)

            # Score base = melhor entre full e short
            score = max(sim_full, sim_short)

            # Containment bonus: se um nome contem o outro
            if name_norm in player_name_norm or player_name_norm in name_norm:
                score = max(score, 0.80)

            # Token overlap bonus
            name_tokens = set(name_norm.split())
            player_tokens = set(player_name_norm.split())
            if name_tokens and player_tokens:
                overlap = len(name_tokens & player_tokens) / max(len(name_tokens), len(player_tokens))
                if overlap >= 0.5:
                    score = max(score, 0.65 + overlap * 0.25)

            # Team bonus (+0.10 se mesmo time)
            if idx in team_indices:
                score += 0.10

            if score > best_score:
                best_score = score
                best_idx = idx

        if best_idx is not None and best_score >= threshold:
            return self.df.loc[best_idx]

        return None


# ============================================
# SINGLETON DO INDICE (session-safe)
# ============================================

_INDEX: Optional[SkillCornerIndex] = None
_INDEX_HASH: Optional[int] = None


def build_skillcorner_index(
    skillcorner_df: pd.DataFrame,
    name_col: str = 'player_name',
    short_col: str = 'short_name',
    team_col: str = 'team_name',
) -> SkillCornerIndex:
    """
    Constroi (ou retorna cached) o indice do SkillCorner.

    Chamar UMA VEZ apos carregar os dados:
        sc_index = build_skillcorner_index(skillcorner)

    Returns:
        SkillCornerIndex pronto para queries
    """
    global _INDEX, _INDEX_HASH

    current_hash = hash(len(skillcorner_df))
    if _INDEX is not None and _INDEX_HASH == current_hash:
        return _INDEX

    idx = SkillCornerIndex()
    idx.build(skillcorner_df, name_col, short_col, team_col)

    _INDEX = idx
    _INDEX_HASH = current_hash

    return idx


def find_skillcorner_player(
    jogador_name: str,
    skillcorner_df: pd.DataFrame,
    team_name: str = None,
    threshold: float = 0.65,
) -> Optional[pd.Series]:
    """
    Drop-in replacement para find_skillcorner_player() do app.py.

    MESMA ASSINATURA: find_skillcorner_player(jogador_name, skillcorner_df)

    Diferenças vs original:
    - Usa indice invertido (O(1) vs O(n))
    - rapidfuzz fuzzy matching (ratio + token_sort_ratio)
    - Suporta team_name para desambiguacao

    Args:
        jogador_name: Nome do jogador (WyScout)
        skillcorner_df: DataFrame SkillCorner completo
        team_name: Nome do time (opcional, melhora precisao)
        threshold: Similaridade minima (0-1)

    Returns:
        pd.Series do jogador ou None
    """
    if pd.isna(jogador_name) or not str(jogador_name).strip():
        return None

    # Garantir que indice existe
    idx = build_skillcorner_index(skillcorner_df)

    return idx.query(
        name=str(jogador_name).strip(),
        team=team_name,
        threshold=threshold,
    )
