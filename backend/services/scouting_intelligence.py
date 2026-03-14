"""
scouting_intelligence.py — Scouting Intelligence Engine v1.0
=============================================================

Expande o predictive_engine existente com 6 modelos de ML para scouting avançado:

1. PlayerTrajectoryModel   — prever evolução de carreira (Gradient Boosting)
2. MarketValueModel        — estimar valor de mercado (XGBoost)
3. MarketOpportunityDetector — identificar oportunidades de mercado
4. PlayerReplacementEngine — sugerir substitutos com similaridade multi-método
5. TemporalPerformanceTrend — detectar tendências de performance
6. LeagueStrengthAdjuster  — ajuste por nível de liga

Base científica:
- Bhatt et al. (2025): KickClone — Cosine Similarity + PCA para substituição
- FPSRec (IEEE BigData 2024): Recomendação com similaridade + IA generativa
- Khalife et al. (MDPI 2025): Valuation com XGBoost, R² > 0.90
- Gyarmati & Stanojevic (2016): Análise temporal de performance
- Decroos et al. (2019), Pappalardo et al. (2019): Trajectory prediction
- Bransen & Van Haaren (2020): Player trajectory models
- MDPI 2025 Systematic Review: RF, XGBoost, GBM, SVM mais utilizados

Integra-se ao predictive_engine.py sem alterar pipeline existente.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')

# Imports condicionais — fallback gracioso
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.feature_selection import mutual_info_regression
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.model_selection import cross_val_score
    from sklearn.impute import SimpleImputer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

from services.league_power_model import (
    get_opta_league_power,
    get_league_strength_factor,
    get_combined_league_adjustment,
    OPTA_LEAGUE_POWER,
    DEFAULT_OPTA_POWER,
)


# ================================================================
# CONSTANTES
# ================================================================

# Features sugeridas por modelo (mapeadas para nomes Wyscout PT)
TRAJECTORY_FEATURES = [
    'Idade', 'Minutos jogados:', 'Golos/90', 'Assistencias/90',
    'Golos esperados/90', 'Assistencias esperadas/90',
    'Passes progressivos/90', 'Acoes defensivas com exito/90',
    'Duelos ganhos, %', 'Passes certos, %',
    'Corridas progressivas/90', 'Dribles com sucesso, %',
]

MARKET_VALUE_FEATURES = [
    'Idade', 'Minutos jogados:', 'Golos/90', 'Assistencias/90',
    'Golos esperados/90', 'Passes certos, %', 'Duelos ganhos, %',
    'Passes progressivos/90', 'Acoes defensivas com exito/90',
    'Remates a baliza, %', 'Passes chave/90',
]

# Features por posição para replacement engine (profiles mais amplos)
REPLACEMENT_FEATURES = {
    'Atacante': [
        'Golos/90', 'Golos esperados/90', 'Remates/90', 'Remates a baliza, %',
        'Assistencias/90', 'Passes chave/90', 'Toques na area/90',
        'Dribles/90', 'Dribles com sucesso, %',
        'Duelos ofensivos/90', 'Duelos aereos ganhos, %',
    ],
    'Extremo': [
        'Golos/90', 'Assistencias/90', 'Passes chave/90',
        'Cruzamentos/90', 'Cruzamentos certos, %',
        'Dribles/90', 'Dribles com sucesso, %',
        'Corridas progressivas/90', 'Aceleracoes/90',
        'Duelos ofensivos/90',
    ],
    'Meia': [
        'Assistencias/90', 'Passes chave/90', 'Passes progressivos/90',
        'Passes certos, %', 'Passes inteligentes/90',
        'Passes em profundidade/90', 'Golos/90',
        'Dribles/90', 'Corridas progressivas/90',
        'Acoes defensivas com exito/90',
    ],
    'Volante': [
        'Acoes defensivas com exito/90', 'Intersecoes/90',
        'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
        'Passes certos, %', 'Passes progressivos/90',
        'Passes longos/90', 'Passes longos certos, %',
        'Duelos ganhos, %', 'Cortes/90',
    ],
    'Lateral': [
        'Cruzamentos/90', 'Cruzamentos certos, %',
        'Assistencias/90', 'Passes progressivos/90',
        'Corridas progressivas/90', 'Aceleracoes/90',
        'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
        'Intersecoes/90', 'Dribles/90',
    ],
    'Zagueiro': [
        'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
        'Duelos aereos ganhos, %', 'Cortes/90',
        'Intersecoes/90', 'Acoes defensivas com exito/90',
        'Passes certos, %', 'Passes longos certos, %',
        'Passes progressivos/90', 'Duelos ganhos, %',
    ],
    'Goleiro': [
        'Defesas, %', 'Golos sofridos/90',
        'Golos expectaveis defendidos por 90',
        'Passes longos certos, %',
    ],
}


def _safe_float(val) -> float:
    """Convert value to float safely, returning NaN on failure."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return np.nan
    try:
        if isinstance(val, str):
            val = val.replace(',', '.')
        return float(val)
    except (ValueError, TypeError):
        return np.nan


def _resolve_features(df: pd.DataFrame, features: List[str]) -> List[str]:
    """Resolve feature names against DataFrame columns (with accent tolerance)."""
    import unicodedata

    def strip_acc(s):
        return ''.join(
            c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) != 'Mn'
        )

    resolved = []
    for feat in features:
        if feat in df.columns:
            resolved.append(feat)
            continue
        feat_stripped = strip_acc(feat)
        for col in df.columns:
            if strip_acc(col) == feat_stripped:
                resolved.append(col)
                break
    return resolved


def _prepare_feature_matrix(df: pd.DataFrame, features: List[str],
                             min_minutes: int = 400) -> Tuple[pd.DataFrame, np.ndarray, List[str]]:
    """Prepare scaled feature matrix from DataFrame."""
    if not HAS_SKLEARN:
        raise RuntimeError("scikit-learn necessário")

    available = _resolve_features(df, features)
    if len(available) < 3:
        raise ValueError(f"Features insuficientes: {len(available)}")

    df_work = df.copy()
    min_col = None
    for c in ['Minutos jogados:', 'Minutos jogados']:
        if c in df_work.columns:
            min_col = c
            break

    if min_col and min_minutes > 0:
        df_work[min_col] = df_work[min_col].apply(_safe_float)
        df_work = df_work[df_work[min_col] >= min_minutes].copy()

    for col in available:
        df_work[col] = df_work[col].apply(_safe_float)

    X_raw = df_work[available].values
    imputer = SimpleImputer(strategy='median')
    X_imputed = imputer.fit_transform(X_raw)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_imputed)

    return df_work, X_scaled, available, imputer, scaler


# ================================================================
# MODELO 1: PLAYER TRAJECTORY MODEL
# ================================================================

class PlayerTrajectoryModel:
    """Prevê evolução de performance de jogadores.

    Base científica:
    - Decroos et al. (2019): Actions Speak Louder than Goals
    - Pappalardo et al. (2019): PlayeRank
    - Bransen & Van Haaren (2020): Player trajectory analysis

    Pipeline:
    1. Normalização z-score
    2. Feature selection via mutual information
    3. Gradient Boosting Regression
    4. Cross-validation
    """

    def __init__(self):
        self.model = None
        self.scaler = None
        self.imputer = None
        self.feature_names = None
        self.feature_importances = None
        self._fitted = False

    def fit(self, df: pd.DataFrame, score_col: str = 'SSP',
            features: Optional[List[str]] = None) -> 'PlayerTrajectoryModel':
        """Treina modelo de trajetória sobre dados históricos.

        Se score_col não existir, cria score sintético baseado em percentis.
        """
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário para PlayerTrajectoryModel")

        feat_list = features or TRAJECTORY_FEATURES
        available = _resolve_features(df, feat_list)
        if len(available) < 3:
            raise ValueError(f"Features insuficientes: {len(available)}")

        df_work = df.copy()
        for col in available:
            df_work[col] = df_work[col].apply(_safe_float)

        # Target: score existente ou sintético
        if score_col in df_work.columns:
            df_work['_target'] = pd.to_numeric(df_work[score_col], errors='coerce')
        else:
            # Criar score sintético: média dos percentis das features disponíveis
            numeric_cols = [c for c in available if c != 'Idade']
            if numeric_cols:
                ranks = df_work[numeric_cols].rank(pct=True, na_option='keep')
                df_work['_target'] = ranks.mean(axis=1) * 100
            else:
                raise ValueError("Sem features numéricas para score sintético")

        df_work = df_work.dropna(subset=['_target'] + available[:3])

        X = df_work[available].values
        y = df_work['_target'].values

        self.imputer = SimpleImputer(strategy='median')
        X = self.imputer.fit_transform(X)
        self.scaler = StandardScaler()
        X = self.scaler.fit_transform(X)

        # Feature selection via mutual information
        mi_scores = mutual_info_regression(X, y, random_state=42)
        mi_norm = mi_scores / (mi_scores.max() + 1e-10)

        # Gradient Boosting Regressor (calibração Tiago Pinto, 2024)
        self.model = GradientBoostingRegressor(
            learning_rate=0.1,
            max_depth=4,
            n_estimators=200,
            subsample=0.8,
            random_state=42,
        )
        self.model.fit(X, y)

        # Cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=min(5, len(y) // 3 + 1),
                                     scoring='r2')

        self.feature_names = available
        self.feature_importances = dict(zip(available, self.model.feature_importances_))
        self._fitted = True
        self._cv_r2 = float(np.mean(cv_scores))
        self._mi_scores = dict(zip(available, mi_norm))

        return self

    def predict_trajectory(self, player_row, league: Optional[str] = None) -> Dict[str, Any]:
        """Prevê rating futuro de um jogador.

        Returns:
            predicted_rating_next_season, trajectory_score, confidence, etc.
        """
        if not self._fitted:
            return self._fallback_trajectory(player_row, league)

        vals = []
        for feat in self.feature_names:
            v = _safe_float(player_row.get(feat, np.nan))
            vals.append(v)

        X = np.array(vals).reshape(1, -1)
        X = self.imputer.transform(X)
        X = self.scaler.transform(X)

        predicted = float(self.model.predict(X)[0])
        predicted = max(0, min(100, predicted))

        # Ajuste por liga (Opta Power)
        if league:
            league_factor = get_opta_league_power(league)
            predicted_adjusted = predicted * league_factor
        else:
            league_factor = 1.0
            predicted_adjusted = predicted

        # Current score estimate
        age = _safe_float(player_row.get('Idade', 25))
        current_estimate = predicted * 0.95  # proxy

        # Trajectory score: diferença projetada
        trajectory_score = predicted_adjusted - current_estimate

        return {
            'predicted_rating_next_season': round(predicted_adjusted, 1),
            'current_rating_estimate': round(current_estimate, 1),
            'trajectory_score': round(trajectory_score, 2),
            'league_adjustment_factor': round(league_factor, 3),
            'model_r2': round(self._cv_r2, 3),
            'top_features': dict(sorted(
                self.feature_importances.items(),
                key=lambda x: -x[1]
            )[:5]),
        }

    def _fallback_trajectory(self, player_row, league: Optional[str] = None) -> Dict[str, Any]:
        """Fallback heurístico quando modelo não está treinado."""
        age = _safe_float(player_row.get('Idade', 25))
        minutes = _safe_float(player_row.get('Minutos jogados:', 0))

        # Heurística baseada em idade (curva de carreira padrão)
        if np.isnan(age):
            age = 25
        if np.isnan(minutes):
            minutes = 0

        # Peak age range: 25-29
        if age < 23:
            trajectory = 5.0 + (23 - age) * 1.5  # jovem = tendência positiva
        elif age <= 29:
            trajectory = 2.0  # pico = estável/leve crescimento
        elif age <= 32:
            trajectory = -2.0  # início do declínio
        else:
            trajectory = -5.0 - (age - 32) * 1.0  # declínio acentuado

        # Ajuste por minutos (regularidade)
        if minutes > 2000:
            trajectory += 1.0
        elif minutes < 500:
            trajectory -= 2.0

        league_factor = get_opta_league_power(league) if league else 1.0
        base_score = 50.0 + trajectory
        adjusted = base_score * league_factor

        return {
            'predicted_rating_next_season': round(max(0, min(100, adjusted)), 1),
            'current_rating_estimate': round(max(0, min(100, base_score - trajectory)), 1),
            'trajectory_score': round(trajectory, 2),
            'league_adjustment_factor': round(league_factor, 3),
            'model_r2': None,
            'method': 'heuristic_fallback',
        }


# ================================================================
# MODELO 2: MARKET VALUE PREDICTION
# ================================================================

class MarketValueModel:
    """Estima valor de mercado com XGBoost.

    Base científica:
    - Khalife et al. (MDPI 2025): Dynamic Financial Valuation, R² > 0.90
    - Nunes (UFMG 2025): Fuzzy + RF para valuation
    - Bryson et al. (2021): Market value determinants

    Segmentação por posição × faixa etária conforme Khalife et al.
    """

    # Categorias de valor de mercado (em milhões EUR)
    # Calibrado com base em Transfermarkt 2024/2025
    VALUE_THRESHOLDS = {
        'elite': 20.0,       # >= €20M
        'high': 5.0,         # >= €5M
        'medium': 1.0,       # >= €1M
        'low': 0.3,          # >= €300K
        'very_low': 0.0,     # < €300K
    }

    # Valor mediano de mercado por liga (milhões EUR) — calibrado Transfermarkt 2024/25
    # Representa o valor médio de um jogador titular na liga
    LEAGUE_MEDIAN_VALUES = {
        'Premier League': 15.0,
        'La Liga': 8.0,
        'Serie A': 7.0,          # Itália
        'Bundesliga': 7.5,
        'Ligue 1': 5.0,
        'Eredivisie': 3.0,
        'Liga Portugal': 3.5,
        'Championship': 3.0,
        'Serie A Brasil': 2.5,
        'Serie B Brasil': 0.6,
        'Liga MX': 1.5,
        'MLS': 1.5,
        'J1 League': 1.0,
        'Super Lig': 2.0,
        'Saudi Pro League': 3.0,
        'Argentine Primera': 1.0,
        'Belgian Pro League': 2.5,
        'Scottish Premiership': 1.5,
        'Swiss Super League': 2.0,
        'Austrian Bundesliga': 1.5,
        'Danish Superliga': 1.5,
        'Ukrainian Premier League': 1.0,
        'Greek Super League': 1.0,
        'Serie C Brasil': 0.2,
    }
    DEFAULT_MEDIAN = 1.0  # fallback para ligas desconhecidas

    # Multiplicador por posição (atacantes valem mais no mercado)
    POSITION_MULTIPLIER = {
        'Atacante': 1.4,
        'Extremo': 1.3,
        'Meia': 1.1,
        'Volante': 0.95,
        'Lateral': 0.85,
        'Zagueiro': 0.80,
        'Goleiro': 0.70,
    }

    def __init__(self):
        self.model = None
        self.scaler = None
        self.imputer = None
        self.feature_names = None
        self._fitted = False

    def fit(self, df: pd.DataFrame, value_col: Optional[str] = None,
            features: Optional[List[str]] = None) -> 'MarketValueModel':
        """Treina modelo de valuation.

        Se value_col não existir, usa estimativa baseada em métricas.
        """
        feat_list = features or MARKET_VALUE_FEATURES
        available = _resolve_features(df, feat_list)
        if len(available) < 3:
            raise ValueError(f"Features insuficientes: {len(available)}")

        df_work = df.copy()
        for col in available:
            df_work[col] = df_work[col].apply(_safe_float)

        # Target: valor de mercado real ou estimado
        if value_col and value_col in df_work.columns:
            df_work['_mv_target'] = pd.to_numeric(df_work[value_col], errors='coerce')
        else:
            # Synthetic market value based on performance percentiles
            df_work['_mv_target'] = self._synthetic_market_value(df_work, available)

        df_work = df_work.dropna(subset=['_mv_target'] + available[:3])
        if len(df_work) < 10:
            raise ValueError(f"Dados insuficientes para treinar: {len(df_work)}")

        X = df_work[available].values
        y = df_work['_mv_target'].values

        self.imputer = SimpleImputer(strategy='median')
        X = self.imputer.fit_transform(X)
        self.scaler = StandardScaler()
        X = self.scaler.fit_transform(X)

        # XGBoost ou fallback para GradientBoosting
        if HAS_XGB:
            self.model = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbosity=0,
            )
        elif HAS_SKLEARN:
            self.model = GradientBoostingRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            )
        else:
            raise RuntimeError("XGBoost ou scikit-learn necessário")

        self.model.fit(X, y)
        self.feature_names = available
        self._fitted = True
        return self

    def predict_market_value(self, player_row, league: Optional[str] = None,
                              current_value: Optional[float] = None) -> Dict[str, Any]:
        """Estima valor de mercado de um jogador.

        Returns:
            estimated_market_value, market_value_gap, value_category, etc.
        """
        if not self._fitted:
            return self._fallback_valuation(player_row, league, current_value)

        vals = []
        for feat in self.feature_names:
            v = _safe_float(player_row.get(feat, np.nan))
            vals.append(v)

        X = np.array(vals).reshape(1, -1)
        X = self.imputer.transform(X)
        X = self.scaler.transform(X)

        estimated = float(self.model.predict(X)[0])
        estimated = max(0, estimated)

        # Ajuste por liga
        if league:
            league_power = get_opta_league_power(league)
            estimated *= league_power

        # Market value gap
        gap = None
        gap_pct = None
        if current_value and current_value > 0:
            gap = estimated - current_value
            gap_pct = (gap / current_value) * 100

        return {
            'estimated_market_value': round(estimated, 0),
            'market_value_gap': round(gap, 0) if gap is not None else None,
            'market_value_gap_pct': round(gap_pct, 1) if gap_pct is not None else None,
            'value_category': self._categorize_value(estimated),
            'is_undervalued': gap is not None and gap > 0,
            'league_adjustment': league,
        }

    def _synthetic_market_value(self, df: pd.DataFrame, features: List[str]) -> pd.Series:
        """Cria valor de mercado sintético em milhões EUR baseado em percentis, idade e liga.

        Calibrado com base em distribuição real Transfermarkt 2024/25.
        Usa distribuição log-normal pois valores de mercado são altamente assimétricos.
        """
        numeric_feats = [f for f in features if f != 'Idade']
        if not numeric_feats:
            return pd.Series(0.5, index=df.index)

        ranks = df[numeric_feats].rank(pct=True, na_option='keep')
        perf_pct = ranks.mean(axis=1)  # 0 to 1

        age = df['Idade'].apply(_safe_float) if 'Idade' in df.columns else pd.Series(25, index=df.index)

        # Curva de valor por idade — pico entre 24-28, baseado em Age Curves 2.0 (TransferLab)
        # Jogadores jovens (<22) com alta performance ganham prêmio de potencial
        age_factor = pd.Series(1.0, index=df.index)
        age_factor = age_factor.where(True)
        for idx in df.index:
            a = _safe_float(age.get(idx, 25) if hasattr(age, 'get') else age.loc[idx])
            if np.isnan(a):
                a = 25
            if a < 20:
                age_factor.loc[idx] = 1.4   # alto potencial
            elif a < 22:
                age_factor.loc[idx] = 1.25
            elif a < 24:
                age_factor.loc[idx] = 1.15
            elif a <= 28:
                age_factor.loc[idx] = 1.0   # pico
            elif a <= 30:
                age_factor.loc[idx] = 0.80
            elif a <= 32:
                age_factor.loc[idx] = 0.55
            elif a <= 34:
                age_factor.loc[idx] = 0.35
            else:
                age_factor.loc[idx] = 0.20

        # Liga mediana
        league_median = pd.Series(self.DEFAULT_MEDIAN, index=df.index)
        for liga_col in ['liga_tier', 'Liga', 'League']:
            if liga_col in df.columns:
                for idx in df.index:
                    liga = str(df.loc[idx, liga_col]) if pd.notna(df.loc[idx, liga_col]) else ''
                    for league_name, med in self.LEAGUE_MEDIAN_VALUES.items():
                        if league_name.lower() in liga.lower() or liga.lower() in league_name.lower():
                            league_median.loc[idx] = med
                            break
                break

        # Posição multiplicador
        pos_mult = pd.Series(1.0, index=df.index)
        for pos_col in ['Posição', 'Posicao', 'Position']:
            if pos_col in df.columns:
                for idx in df.index:
                    pos_raw = str(df.loc[idx, pos_col]) if pd.notna(df.loc[idx, pos_col]) else ''
                    # Tentar mapear para categoria
                    for pos_key, mult in self.POSITION_MULTIPLIER.items():
                        if pos_key.lower() in pos_raw.lower():
                            pos_mult.loc[idx] = mult
                            break
                break

        # Valor estimado = mediana_liga × performance^2 × age_factor × position_mult
        # performance^2 cria distribuição concentrada (poucos jogadores de alto valor)
        # Multiplicador adicional para top percentis (simula distribuição log-normal)
        perf_multiplier = perf_pct.clip(0.01, 1.0) ** 1.5  # power law
        # Top 5% ganham boost extra (superstars)
        perf_multiplier = perf_multiplier.where(perf_pct < 0.95, perf_multiplier * 2.5)
        # Top 1% ganham boost adicional
        perf_multiplier = perf_multiplier.where(perf_pct < 0.99, perf_multiplier * 1.8)

        value_eur_millions = (
            league_median * perf_multiplier * age_factor * pos_mult * 3.0
        ).clip(0.05, 200.0)

        return value_eur_millions

    def _fallback_valuation(self, player_row, league, current_value) -> Dict[str, Any]:
        """Estimativa heurística de valor de mercado em milhões EUR.

        Calibrado com base em distribuições reais Transfermarkt 2024/25.
        Usa métricas de performance + idade + liga + posição.
        """
        age = _safe_float(player_row.get('Idade', 25))
        minutes = _safe_float(player_row.get('Minutos jogados:', 0))
        goals = _safe_float(player_row.get('Golos/90', 0))
        assists = _safe_float(player_row.get('Assistencias/90', 0))
        xg = _safe_float(player_row.get('Golos esperados/90', 0))
        xa = _safe_float(player_row.get('Assistencias esperadas/90', 0))
        passes_pct = _safe_float(player_row.get('Passes certos, %', 0))
        prog_passes = _safe_float(player_row.get('Passes progressivos/90', 0))
        duels_pct = _safe_float(player_row.get('Duelos ganhos, %', 0))
        prog_runs = _safe_float(player_row.get('Corridas progressivas/90', 0))
        dribbles_pct = _safe_float(player_row.get('Dribles com sucesso, %', 0))
        def_actions = _safe_float(player_row.get('Acoes defensivas com exito/90', 0))

        if np.isnan(age): age = 25
        if np.isnan(minutes): minutes = 0
        if np.isnan(goals): goals = 0
        if np.isnan(assists): assists = 0
        if np.isnan(xg): xg = 0
        if np.isnan(xa): xa = 0
        if np.isnan(passes_pct): passes_pct = 70
        if np.isnan(prog_passes): prog_passes = 3
        if np.isnan(duels_pct): duels_pct = 45
        if np.isnan(prog_runs): prog_runs = 1
        if np.isnan(dribbles_pct): dribbles_pct = 40
        if np.isnan(def_actions): def_actions = 3

        # Performance score composto (0-1) — média ponderada de múltiplas métricas
        # Normalização baseada em referências top-percentil Wyscout
        perf_components = [
            min(1.0, (goals + xg) / 1.2) * 0.20,        # produção ofensiva
            min(1.0, (assists + xa) / 0.8) * 0.15,       # criação
            min(1.0, passes_pct / 90.0) * 0.10,          # precisão
            min(1.0, prog_passes / 10.0) * 0.12,         # progressão passe
            min(1.0, prog_runs / 5.0) * 0.08,            # progressão corrida
            min(1.0, duels_pct / 60.0) * 0.10,           # duelos
            min(1.0, dribbles_pct / 65.0) * 0.08,        # dribles
            min(1.0, def_actions / 8.0) * 0.07,           # defesa
            min(1.0, minutes / 2500.0) * 0.10,           # regularidade
        ]
        perf_score = sum(perf_components)  # 0 to ~1

        # Curva de idade (Age Curves 2.0 — TransferLab)
        if age < 20:
            age_factor = 1.5   # alto potencial, prêmio de juventude
        elif age < 22:
            age_factor = 1.35
        elif age < 24:
            age_factor = 1.2
        elif age <= 28:
            age_factor = 1.0   # pico
        elif age <= 30:
            age_factor = 0.75
        elif age <= 32:
            age_factor = 0.50
        elif age <= 34:
            age_factor = 0.30
        else:
            age_factor = 0.15

        # Mediana da liga
        league_median = self.DEFAULT_MEDIAN
        if league:
            league_median = self.LEAGUE_MEDIAN_VALUES.get(league, self.DEFAULT_MEDIAN)
            # Tentar match parcial
            if league_median == self.DEFAULT_MEDIAN:
                for lg_name, med in self.LEAGUE_MEDIAN_VALUES.items():
                    if lg_name.lower() in league.lower() or league.lower() in lg_name.lower():
                        league_median = med
                        break
            # Fallback: usar Opta power como proxy
            if league_median == self.DEFAULT_MEDIAN:
                opta = get_opta_league_power(league)
                league_median = opta * 8.0  # PL=1.0 → €8M base

        # Posição
        pos_raw = str(player_row.get('Posição', '')) if pd.notna(player_row.get('Posição', None)) else ''
        pos_mult = 1.0
        for pos_key, mult in self.POSITION_MULTIPLIER.items():
            if pos_key.lower() in pos_raw.lower():
                pos_mult = mult
                break

        # Valor estimado (milhões EUR)
        # Performance^1.5 cria power law (poucos jogadores de alto valor)
        estimated = league_median * (perf_score ** 1.5) * age_factor * pos_mult * 3.0
        # Top performers (score > 0.8) ganham boost exponencial
        if perf_score > 0.85:
            estimated *= 2.0
        elif perf_score > 0.75:
            estimated *= 1.5
        estimated = max(0.05, round(estimated, 2))  # mínimo €50K

        # Gap vs valor atual (current_value em milhões EUR)
        gap = None
        gap_pct = None
        if current_value and current_value > 0:
            gap = estimated - current_value
            gap_pct = (gap / current_value) * 100

        return {
            'estimated_market_value': round(estimated, 2),
            'market_value_gap': round(gap, 2) if gap is not None else None,
            'market_value_gap_pct': round(gap_pct, 1) if gap_pct is not None else None,
            'value_category': self._categorize_value(estimated),
            'is_undervalued': gap is not None and gap > 0,
            'method': 'heuristic_fallback',
        }

    @staticmethod
    def _categorize_value(value_millions: float) -> str:
        """Categoriza valor de mercado em milhões EUR."""
        if value_millions >= 20.0: return 'elite'
        if value_millions >= 5.0: return 'high'
        if value_millions >= 1.0: return 'medium'
        if value_millions >= 0.3: return 'low'
        return 'very_low'


# ================================================================
# MODELO 3: MARKET OPPORTUNITY DETECTOR
# ================================================================

class MarketOpportunityDetector:
    """Detecta oportunidades de mercado combinando múltiplos sinais.

    Inspirado em departamentos de scouting de:
    - Brighton & Hove Albion
    - Brentford FC
    - FC Midtjylland

    Fórmula:
    market_opportunity = performance_percentile × trajectory_score × value_gap − age_penalty

    Score normalizado entre 0 e 100.
    """

    # Penalidade por idade (peso exponencial após 30 anos)
    AGE_PENALTY_THRESHOLD = 28
    AGE_PENALTY_RATE = 3.0  # pontos por ano acima do threshold

    def calculate_opportunity_score(self,
                                     performance_percentile: float,
                                     trajectory_score: float,
                                     value_gap: Optional[float],
                                     age: float,
                                     minutes: float = 0,
                                     league: Optional[str] = None) -> Dict[str, Any]:
        """Calcula market opportunity score para um jogador.

        Args:
            performance_percentile: Percentil de performance (0-100)
            trajectory_score: Score de trajetória do PlayerTrajectoryModel
            value_gap: Diferença entre valor estimado e real (positivo = subvalorizado)
            age: Idade do jogador
            minutes: Minutos jogados na temporada
            league: Liga atual

        Returns:
            market_opportunity_score (0-100), classification, components
        """
        if np.isnan(age):
            age = 25
        if np.isnan(performance_percentile):
            performance_percentile = 50.0

        # Component 1: Performance (0-1)
        perf_norm = performance_percentile / 100.0

        # Component 2: Trajectory (sigmoid normalization to 0-1)
        traj_norm = 1.0 / (1.0 + np.exp(-trajectory_score * 0.3))

        # Component 3: Value gap (0-1, higher = more undervalued)
        if value_gap is not None and value_gap > 0:
            value_norm = min(1.0, value_gap / 10.0)  # cap at €10M gap (values in EUR millions)
        else:
            value_norm = 0.5  # neutral if no gap data

        # Component 4: Age penalty
        if age > self.AGE_PENALTY_THRESHOLD:
            age_penalty = (age - self.AGE_PENALTY_THRESHOLD) * self.AGE_PENALTY_RATE
        else:
            age_penalty = 0.0
            # Bonus for young players
            if age < 23:
                age_penalty = -(23 - age) * 1.5  # negative penalty = bonus

        # Component 5: Minutes (regularidade)
        minutes_factor = min(1.0, minutes / 2000.0) if not np.isnan(minutes) else 0.5

        # Liga adjustment
        league_factor = get_opta_league_power(league) if league else 0.7

        # Combined score
        raw_score = (
            perf_norm * 35.0
            + traj_norm * 25.0
            + value_norm * 20.0
            + minutes_factor * 10.0
            + league_factor * 10.0
            - age_penalty
        )

        # Normalize to 0-100
        opportunity_score = max(0, min(100, raw_score))

        return {
            'market_opportunity_score': round(opportunity_score, 1),
            'classification': self._classify(opportunity_score),
            'is_high_opportunity': opportunity_score >= 70,
            'components': {
                'performance': round(perf_norm * 100, 1),
                'trajectory': round(traj_norm * 100, 1),
                'value_gap': round(value_norm * 100, 1),
                'minutes_factor': round(minutes_factor * 100, 1),
                'league_factor': round(league_factor * 100, 1),
                'age_penalty': round(age_penalty, 1),
            },
        }

    @staticmethod
    def _classify(score: float) -> str:
        if score >= 80: return 'exceptional_opportunity'
        if score >= 70: return 'high_opportunity'
        if score >= 55: return 'moderate_opportunity'
        if score >= 40: return 'low_opportunity'
        return 'below_threshold'

    def batch_detect(self, players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calcula opportunity score para batch de jogadores e retorna rankeado."""
        results = []
        for p in players:
            score = self.calculate_opportunity_score(
                performance_percentile=p.get('performance_percentile', 50),
                trajectory_score=p.get('trajectory_score', 0),
                value_gap=p.get('value_gap'),
                age=p.get('age', 25),
                minutes=p.get('minutes', 0),
                league=p.get('league'),
            )
            score['player'] = p.get('name', 'Unknown')
            score['player_display'] = p.get('display_name', p.get('name', 'Unknown'))
            results.append(score)

        return sorted(results, key=lambda x: -x['market_opportunity_score'])


# ================================================================
# MODELO 4: PLAYER REPLACEMENT ENGINE
# ================================================================

class PlayerReplacementEngine:
    """Motor de busca de substitutos para jogadores.

    Base científica:
    - Bhatt et al. (2025): KickClone — Cosine Similarity + PCA
    - FPSRec (IEEE BigData 2024): Similarity + AI for scouting
    - Spatial Similarity Index (PMC/NCBI 2025): Lee's Spatial Statistic

    Similaridade multi-método:
    1. Cosine Similarity (Bhatt et al.)
    2. Mahalanobis Distance (distribuição multivariada)
    3. Cluster Proximity (KickClone approach)
    """

    COSINE_WEIGHT = 0.45
    MAHALANOBIS_WEIGHT = 0.35
    CLUSTER_WEIGHT = 0.20

    def __init__(self):
        self.scaler = None
        self.imputer = None
        self.pca = None
        self._fitted = False

    def find_replacement_players(self,
                                   target_player_row,
                                   df_pool: pd.DataFrame,
                                   position: str,
                                   top_n: int = 20,
                                   age_range: Optional[Tuple[float, float]] = None,
                                   max_value: Optional[float] = None,
                                   league_filter: Optional[List[str]] = None,
                                   min_minutes: int = 400,
                                   trajectory_model: Optional[PlayerTrajectoryModel] = None,
                                   market_model: Optional[MarketValueModel] = None,
                                   ) -> List[Dict[str, Any]]:
        """Encontra top-N substitutos para um jogador alvo.

        Args:
            target_player_row: Série/dict com dados do jogador alvo
            df_pool: DataFrame com pool de candidatos
            position: Posição do jogador
            top_n: Número de substitutos (default 20)
            age_range: Filtro de faixa etária (min, max)
            max_value: Filtro de valor máximo
            league_filter: Filtro de ligas aceitas
            min_minutes: Minutos mínimos jogados
            trajectory_model: Modelo de trajetória para enriquecer output
            market_model: Modelo de valuation para enriquecer output

        Returns:
            Lista de top_n substitutos com similarity_score, market_value_gap, etc.
        """
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        # Get position-specific features
        features = REPLACEMENT_FEATURES.get(position, REPLACEMENT_FEATURES.get('Meia', []))
        available = _resolve_features(df_pool, features)
        if len(available) < 3:
            raise ValueError(f"Features insuficientes para posição {position}")

        # Filter pool
        pool = df_pool.copy()

        # Filter by position
        if 'Posição' in pool.columns:
            from config.mappings import get_posicao_categoria
            pool['_pos_cat'] = pool['Posição'].apply(
                lambda x: get_posicao_categoria(str(x)) if pd.notna(x) else ''
            )
            pool = pool[pool['_pos_cat'] == position].copy()

        # Filter by minutes
        min_col = None
        for c in ['Minutos jogados:', 'Minutos jogados']:
            if c in pool.columns:
                min_col = c
                break
        if min_col and min_minutes > 0:
            pool[min_col] = pool[min_col].apply(_safe_float)
            pool = pool[pool[min_col] >= min_minutes]

        # Filter by age
        if age_range and 'Idade' in pool.columns:
            pool['_age'] = pool['Idade'].apply(_safe_float)
            pool = pool[(pool['_age'] >= age_range[0]) & (pool['_age'] <= age_range[1])]

        # Remove target player from pool
        if 'JogadorDisplay' in pool.columns and 'JogadorDisplay' in target_player_row.index:
            pool = pool[pool['JogadorDisplay'] != target_player_row['JogadorDisplay']]

        if len(pool) < 3:
            return []

        # Prepare feature matrices
        for col in available:
            pool[col] = pool[col].apply(_safe_float)

        X_pool = pool[available].values
        self.imputer = SimpleImputer(strategy='median')
        X_pool = self.imputer.fit_transform(X_pool)
        self.scaler = StandardScaler()
        X_pool = self.scaler.fit_transform(X_pool)

        # Target vector
        target_vals = [_safe_float(target_player_row.get(f, np.nan)) for f in available]
        target_vals = [v if not np.isnan(v) else 0.0 for v in target_vals]
        X_target = np.array(target_vals).reshape(1, -1)
        X_target = self.imputer.transform(X_target)
        X_target = self.scaler.transform(X_target)

        # 1. Cosine Similarity (Bhatt et al., KickClone)
        cos_sim = cosine_similarity(X_target, X_pool)[0]
        cos_sim = (cos_sim + 1) / 2  # normalize to [0, 1]

        # 2. Mahalanobis Distance
        cov = np.cov(X_pool, rowvar=False)
        try:
            cov_inv = np.linalg.inv(cov + np.eye(cov.shape[0]) * 1e-6)
        except np.linalg.LinAlgError:
            cov_inv = np.eye(cov.shape[0])

        diffs = X_pool - X_target
        mahal_dists = np.sqrt(np.sum(diffs @ cov_inv * diffs, axis=1))
        mahal_sim = 1.0 - (mahal_dists / (mahal_dists.max() + 1e-10))

        # 3. Cluster Proximity (PCA + KMeans)
        n_components = min(5, X_pool.shape[1], X_pool.shape[0])
        self.pca = PCA(n_components=n_components)
        X_pca_pool = self.pca.fit_transform(X_pool)
        X_pca_target = self.pca.transform(X_target)

        n_clusters = min(5, len(pool) // 3)
        if n_clusters >= 2:
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
            pool_labels = kmeans.fit_predict(X_pca_pool)
            target_label = kmeans.predict(X_pca_target)[0]
            cluster_sim = (pool_labels == target_label).astype(float)
        else:
            cluster_sim = np.ones(len(pool))

        # Combined similarity
        combined = (
            self.COSINE_WEIGHT * cos_sim
            + self.MAHALANOBIS_WEIGHT * mahal_sim
            + self.CLUSTER_WEIGHT * cluster_sim
        ) * 100.0

        # Sort and get top_n
        top_indices = np.argsort(combined)[::-1][:top_n]

        results = []
        for rank, idx in enumerate(top_indices):
            row = pool.iloc[idx]
            result = {
                'rank': rank + 1,
                'player': str(row.get('Jogador', '')),
                'display_name': str(row.get('JogadorDisplay', row.get('Jogador', ''))),
                'team': str(row.get('Equipa', '')) if pd.notna(row.get('Equipa')) else None,
                'position': position,
                'age': _safe_float(row.get('Idade', np.nan)),
                'minutes': _safe_float(row.get(min_col, np.nan)) if min_col else None,
                'similarity_score': round(float(combined[idx]), 1),
                'cosine_similarity': round(float(cos_sim[idx] * 100), 1),
                'mahalanobis_similarity': round(float(mahal_sim[idx] * 100), 1),
                'cluster_proximity': round(float(cluster_sim[idx] * 100), 1),
            }

            # Enrich with trajectory if model available
            if trajectory_model and trajectory_model._fitted:
                traj = trajectory_model.predict_trajectory(row, league=row.get('liga_tier'))
                result['trajectory_score'] = traj.get('trajectory_score', 0)
                result['predicted_rating'] = traj.get('predicted_rating_next_season')
            else:
                # Fallback trajectory
                traj = trajectory_model._fallback_trajectory(row, row.get('liga_tier')) if trajectory_model else {}
                result['trajectory_score'] = traj.get('trajectory_score', 0)

            # Enrich with market value if model available
            if market_model and market_model._fitted:
                mv = market_model.predict_market_value(row, league=row.get('liga_tier'))
                result['market_value_gap'] = mv.get('market_value_gap')
                result['estimated_value'] = mv.get('estimated_market_value')

            results.append(result)

        return results


# ================================================================
# MODELO 5: TEMPORAL PERFORMANCE TREND
# ================================================================

class TemporalPerformanceTrend:
    """Análise temporal de tendência de performance.

    Base científica:
    - Gyarmati & Stanojevic (2016): Analyzing player performance over time

    Calcula:
    performance_trend = rolling_mean(last) - rolling_mean(previous)

    Classifica jogadores como: improving, stable, declining
    """

    IMPROVING_THRESHOLD = 3.0
    DECLINING_THRESHOLD = -3.0

    def calculate_trend(self,
                        current_score: float,
                        previous_score: Optional[float] = None,
                        age: float = 25,
                        minutes_current: float = 0,
                        minutes_previous: Optional[float] = None) -> Dict[str, Any]:
        """Calcula tendência de performance de um jogador.

        Se não houver score anterior, estima tendência baseada em
        idade e minutos (heurística fundamentada em curvas de carreira).
        """
        if np.isnan(current_score):
            current_score = 50.0
        if np.isnan(age):
            age = 25

        if previous_score is not None and not np.isnan(previous_score):
            # Trend real: diferença entre scores
            trend = current_score - previous_score

            # Ajustar por diferença de minutos (se jogou menos, trend menos confiável)
            if minutes_previous and minutes_current:
                min_ratio = minutes_current / max(minutes_previous, 1)
                if min_ratio < 0.5:
                    trend *= 0.7  # discount trend if much less playing time
        else:
            # Estimativa baseada em curva de carreira
            # Dados empíricos: jogadores melhoram até ~27, estabilizam até ~30, declinam depois
            if age < 22:
                trend = 5.0  # strong improvement expected
            elif age < 25:
                trend = 3.0  # moderate improvement
            elif age < 28:
                trend = 1.0  # slight improvement / peak
            elif age < 30:
                trend = 0.0  # stable
            elif age < 33:
                trend = -3.0  # moderate decline
            else:
                trend = -6.0  # strong decline

            # Modulate by minutes
            if not np.isnan(minutes_current):
                if minutes_current > 2500:
                    trend += 1.0  # regular starter bonus
                elif minutes_current < 500:
                    trend -= 2.0  # lack of game time penalty

        classification = self._classify(trend)

        return {
            'performance_trend': round(trend, 2),
            'trend_classification': classification,
            'current_score': round(current_score, 1),
            'previous_score': round(previous_score, 1) if previous_score is not None else None,
            'has_historical_data': previous_score is not None,
        }

    def _classify(self, trend: float) -> str:
        if trend >= self.IMPROVING_THRESHOLD:
            return 'improving'
        elif trend <= self.DECLINING_THRESHOLD:
            return 'declining'
        return 'stable'

    def batch_analyze(self, players_data: List[Dict]) -> List[Dict]:
        """Analisa tendência para batch de jogadores."""
        results = []
        for p in players_data:
            trend = self.calculate_trend(
                current_score=p.get('current_score', 50),
                previous_score=p.get('previous_score'),
                age=p.get('age', 25),
                minutes_current=p.get('minutes_current', 0),
                minutes_previous=p.get('minutes_previous'),
            )
            trend['player'] = p.get('name', 'Unknown')
            trend['display_name'] = p.get('display_name', p.get('name', 'Unknown'))
            results.append(trend)

        return results


# ================================================================
# MODELO 6: LEAGUE STRENGTH ADJUSTER
# ================================================================

class LeagueStrengthAdjuster:
    """Ajuste de métricas por nível de liga.

    Combina:
    - UEFA coefficient logic (hierarquia de ligas)
    - Opta Power Ranking (rating médio dos clubes por liga)
    - ContractSuccessPredictor.LEAGUE_TIERS (escala 0-10)

    adjusted_metric = metric × league_strength_factor × opta_league_power
    """

    def __init__(self, league_tiers: Optional[Dict[str, float]] = None):
        # Import LEAGUE_TIERS from predictive_engine
        if league_tiers is None:
            try:
                from services.predictive_engine import ContractSuccessPredictor
                self.league_tiers = ContractSuccessPredictor.LEAGUE_TIERS
            except ImportError:
                self.league_tiers = {}
        else:
            self.league_tiers = league_tiers

    def adjust_metric(self, value: float, league: str) -> float:
        """Ajusta uma métrica pelo fator combinado de liga."""
        if np.isnan(value):
            return value
        factor = get_combined_league_adjustment(league, self.league_tiers)
        return value * factor

    def adjust_player_metrics(self, player_row, league: str,
                                metrics: List[str]) -> Dict[str, float]:
        """Ajusta múltiplas métricas de um jogador."""
        factor = get_combined_league_adjustment(league, self.league_tiers)
        adjusted = {}
        for metric in metrics:
            val = _safe_float(player_row.get(metric, np.nan))
            if not np.isnan(val):
                adjusted[metric] = round(val * factor, 4)
        return adjusted

    def get_league_info(self, league: str) -> Dict[str, Any]:
        """Retorna informação completa de uma liga."""
        opta = get_opta_league_power(league)
        tier = self.league_tiers.get(league)
        combined = get_combined_league_adjustment(league, self.league_tiers)

        return {
            'league': league,
            'opta_power': round(opta, 3),
            'tier_score': tier,
            'combined_factor': round(combined, 4),
            'strength_category': self._categorize(opta),
        }

    def compare_leagues(self, league_a: str, league_b: str) -> Dict[str, Any]:
        """Compara força de duas ligas."""
        info_a = self.get_league_info(league_a)
        info_b = self.get_league_info(league_b)

        return {
            'league_a': info_a,
            'league_b': info_b,
            'opta_ratio': round(info_a['opta_power'] / max(info_b['opta_power'], 0.01), 3),
            'adjustment_ratio': round(info_a['combined_factor'] / max(info_b['combined_factor'], 0.01), 3),
        }

    @staticmethod
    def _categorize(opta_power: float) -> str:
        if opta_power >= 0.90: return 'world_class'
        if opta_power >= 0.80: return 'top_tier'
        if opta_power >= 0.70: return 'competitive'
        if opta_power >= 0.55: return 'developing'
        return 'lower'


# ================================================================
# SCOUTING INTELLIGENCE ENGINE (integrador)
# ================================================================

class ScoutingIntelligenceEngine:
    """Motor integrador que combina todos os 6 modelos.

    Expõe interface unificada para o backend FastAPI.
    """

    def __init__(self):
        self.trajectory_model = PlayerTrajectoryModel()
        self.market_model = MarketValueModel()
        self.opportunity_detector = MarketOpportunityDetector()
        self.replacement_engine = PlayerReplacementEngine()
        self.trend_analyzer = TemporalPerformanceTrend()
        self.league_adjuster = LeagueStrengthAdjuster()
        self._df_pool = None
        self._fitted = False

    def fit(self, df: pd.DataFrame) -> 'ScoutingIntelligenceEngine':
        """Treina modelos sobre o dataset disponível."""
        self._df_pool = df.copy()

        # Train trajectory model
        try:
            self.trajectory_model.fit(df)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Trajectory model fit failed: %s", e)

        # Train market value model
        try:
            self.market_model.fit(df)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Market value model fit failed: %s", e)

        self._fitted = True
        return self

    def analyze_player(self, player_row, df_all: pd.DataFrame,
                        position: str, league: Optional[str] = None,
                        current_value: Optional[float] = None,
                        previous_score: Optional[float] = None) -> Dict[str, Any]:
        """Análise completa de um jogador com todos os modelos."""
        result = {
            'player': str(player_row.get('Jogador', '')),
            'display_name': str(player_row.get('JogadorDisplay', player_row.get('Jogador', ''))),
            'position': position,
        }

        # 1. Trajectory
        traj = self.trajectory_model.predict_trajectory(player_row, league)
        result['trajectory'] = traj

        # 2. Market Value
        mv = self.market_model.predict_market_value(player_row, league, current_value)
        result['market_value'] = mv

        # 3. Trend
        age = _safe_float(player_row.get('Idade', 25))
        minutes = _safe_float(player_row.get('Minutos jogados:', 0))
        current_score = traj.get('current_rating_estimate', 50)
        trend = self.trend_analyzer.calculate_trend(
            current_score=current_score,
            previous_score=previous_score,
            age=age,
            minutes_current=minutes,
        )
        result['trend'] = trend

        # 4. Market Opportunity
        opportunity = self.opportunity_detector.calculate_opportunity_score(
            performance_percentile=traj.get('predicted_rating_next_season', 50),
            trajectory_score=traj.get('trajectory_score', 0),
            value_gap=mv.get('market_value_gap'),
            age=age,
            minutes=minutes,
            league=league,
        )
        result['opportunity'] = opportunity

        # 5. League adjustment info
        result['league_info'] = self.league_adjuster.get_league_info(league or '')

        return result

    def find_replacements(self, target_player_row, df_pool: pd.DataFrame,
                           position: str, top_n: int = 20,
                           **filters) -> List[Dict[str, Any]]:
        """Busca substitutos para um jogador."""
        return self.replacement_engine.find_replacement_players(
            target_player_row=target_player_row,
            df_pool=df_pool,
            position=position,
            top_n=top_n,
            trajectory_model=self.trajectory_model,
            market_model=self.market_model,
            **filters,
        )

    def detect_opportunities(self, df: pd.DataFrame,
                               position: Optional[str] = None,
                               top_n: int = 50) -> List[Dict[str, Any]]:
        """Detecta oportunidades de mercado no dataset."""
        pool = df.copy()
        if position and 'Posição' in pool.columns:
            from config.mappings import get_posicao_categoria
            pool['_pos'] = pool['Posição'].apply(
                lambda x: get_posicao_categoria(str(x)) if pd.notna(x) else ''
            )
            pool = pool[pool['_pos'] == position]

        players = []
        for _, row in pool.iterrows():
            age = _safe_float(row.get('Idade', 25))
            minutes = _safe_float(row.get('Minutos jogados:', 0))
            league = str(row.get('liga_tier', '')) if pd.notna(row.get('liga_tier')) else None

            # Get trajectory
            traj = self.trajectory_model.predict_trajectory(row, league)
            # Get market value
            mv = self.market_model.predict_market_value(row, league)

            # Calculate percentile approximation from score
            perf_percentile = traj.get('predicted_rating_next_season', 50)

            players.append({
                'name': str(row.get('Jogador', '')),
                'display_name': str(row.get('JogadorDisplay', row.get('Jogador', ''))),
                'team': str(row.get('Equipa', '')) if pd.notna(row.get('Equipa')) else None,
                'performance_percentile': perf_percentile,
                'trajectory_score': traj.get('trajectory_score', 0),
                'value_gap': mv.get('market_value_gap'),
                'age': age,
                'minutes': minutes,
                'league': league,
            })

        results = self.opportunity_detector.batch_detect(players)
        return results[:top_n]
