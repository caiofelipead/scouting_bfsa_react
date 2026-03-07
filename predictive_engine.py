"""
predictive_engine.py — Motor Preditivo de Scouting v3.0
========================================================
Substitui a lógica descritiva de similarity.py por inferência estatística.

Pipeline:
    1. Feature Selection por posição (PCA + Mutual Information)
    2. Win-Probability Model (Logistic Regression com coeficientes como pesos)
    3. Scout Score Preditivo (ensemble: WP-weights + xG-residual + cluster-fit)
    4. Clusterização Tática (K-Means + Gaussian Mixture para perfis)
    5. Similaridade Avançada (Mahalanobis + Random Forest proximity)

Ref. Acadêmica:
    - Eduardo Baptista / PIBITI João Vitor: feature selection por posição
    - Felipe Nunes (Doutorado): predição de sucesso de contratação
    - Victor Schimidt (TCC): regressão logística win-probability
    - Gabriel Buso (TCC): modelagem xG / xGOT / gols prevenidos
    - Frederico Ferra / Tiago Pinto: clusterização tática multivariada
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')

# Imports condicionais — fallback gracioso se libs não instaladas
try:
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.decomposition import PCA
    from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.cluster import KMeans
    from sklearn.mixture import GaussianMixture
    from sklearn.metrics import silhouette_score
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import statsmodels.api as sm
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


# ================================================================
# CONSTANTES E CONFIGURAÇÃO
# ================================================================

@dataclass
class PositionProfile:
    """Perfil de features por posição com domínios funcionais."""
    name: str
    offensive_features: List[str] = field(default_factory=list)
    defensive_features: List[str] = field(default_factory=list)
    passing_features: List[str] = field(default_factory=list)
    physical_features: List[str] = field(default_factory=list)
    efficiency_features: List[str] = field(default_factory=list)
    domain_weights: Dict[str, float] = field(default_factory=dict)


# Taxonomia de features por domínio funcional (base: Eduardo Baptista / PIBITI)
POSITION_PROFILES = {
    'Atacante': PositionProfile(
        name='Atacante',
        offensive_features=[
            'Golos/90', 'Golos esperados/90', 'Golos sem ser por penalti/90',
            'Remates/90', 'Remates a baliza, %', 'Golos marcados, %',
            'Toques na area/90', 'Golos de cabeca/90',
        ],
        defensive_features=[
            'Acoes defensivas com exito/90',
        ],
        passing_features=[
            'Assistencias/90', 'Assistencias esperadas/90',
            'Passes chave/90', 'Segundas assistencias/90',
            'Passes recebidos/90', 'Recesao de passes em profundidade/90',
        ],
        physical_features=[
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
            'Aceleracoes/90', 'Corridas progressivas/90',
        ],
        efficiency_features=[
            'Golos/90', 'Golos esperados/90', 'Remates a baliza, %',
            'Golos marcados, %',
        ],
        domain_weights={
            'offensive': 0.40, 'passing': 0.20,
            'physical': 0.20, 'defensive': 0.05, 'efficiency': 0.15,
        },
    ),
    'Extremo': PositionProfile(
        name='Extremo',
        offensive_features=[
            'Golos/90', 'Golos esperados/90', 'Remates/90',
            'Toques na area/90',
        ],
        defensive_features=[
            'Acoes defensivas com exito/90',
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
        ],
        passing_features=[
            'Assistencias/90', 'Assistencias esperadas/90',
            'Passes chave/90', 'Passes inteligentes/90',
            'Passes para a area de penalti/90',
            'Cruzamentos/90', 'Cruzamentos certos, %',
        ],
        physical_features=[
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Aceleracoes/90', 'Corridas progressivas/90',
        ],
        efficiency_features=[
            'Dribles com sucesso, %', 'Cruzamentos certos, %',
            'Passes chave/90',
        ],
        domain_weights={
            'offensive': 0.25, 'passing': 0.30,
            'physical': 0.25, 'defensive': 0.05, 'efficiency': 0.15,
        },
    ),
    'Meia': PositionProfile(
        name='Meia',
        offensive_features=[
            'Golos/90', 'Golos esperados/90', 'Remates/90',
            'Toques na area/90',
        ],
        defensive_features=[
            'Acoes defensivas com exito/90',
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Intersecoes/90',
        ],
        passing_features=[
            'Assistencias/90', 'Assistencias esperadas/90',
            'Passes chave/90', 'Passes inteligentes/90',
            'Passes inteligentes certos, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terco final/90',
            'Passes em profundidade/90', 'Passes em profundidade certos, %',
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
        ],
        physical_features=[
            'Dribles/90', 'Dribles com sucesso, %',
            'Corridas progressivas/90',
        ],
        efficiency_features=[
            'Passes certos, %', 'Passes inteligentes certos, %',
            'Passes progressivos certos, %',
        ],
        domain_weights={
            'offensive': 0.15, 'passing': 0.40,
            'physical': 0.10, 'defensive': 0.15, 'efficiency': 0.20,
        },
    ),
    'Volante': PositionProfile(
        name='Volante',
        offensive_features=[
            'Passes progressivos/90', 'Corridas progressivas/90',
            'Passes em profundidade/90',
        ],
        defensive_features=[
            'Acoes defensivas com exito/90', 'Intersecoes/90',
            'Intercecoes ajust. a posse',
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Cortes/90', 'Cortes de carrinho ajust. a posse',
            'Remates intercetados/90',
        ],
        passing_features=[
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terco final/90',
        ],
        physical_features=[
            'Duelos/90', 'Duelos ganhos, %',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
        ],
        efficiency_features=[
            'Passes certos, %', 'Duelos defensivos ganhos, %',
            'Duelos ganhos, %',
        ],
        domain_weights={
            'offensive': 0.10, 'passing': 0.25,
            'physical': 0.15, 'defensive': 0.35, 'efficiency': 0.15,
        },
    ),
    'Lateral': PositionProfile(
        name='Lateral',
        offensive_features=[
            'Cruzamentos/90', 'Cruzamentos certos, %',
            'Cruzamentos para a area de baliza/90',
            'Toques na area/90', 'Passes para a area de penalti/90',
            'Assistencias/90', 'Assistencias esperadas/90',
        ],
        defensive_features=[
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Intersecoes/90', 'Cortes/90',
            'Acoes defensivas com exito/90', 'Remates intercetados/90',
        ],
        passing_features=[
            'Passes para terco final/90', 'Passes certos para terco final, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes em profundidade/90', 'Passes chave/90',
        ],
        physical_features=[
            'Corridas progressivas/90', 'Aceleracoes/90',
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos/90', 'Duelos ganhos, %',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
        ],
        efficiency_features=[
            'Cruzamentos certos, %', 'Duelos defensivos ganhos, %',
            'Dribles com sucesso, %',
        ],
        domain_weights={
            'offensive': 0.25, 'passing': 0.20,
            'physical': 0.20, 'defensive': 0.25, 'efficiency': 0.10,
        },
    ),
    'Zagueiro': PositionProfile(
        name='Zagueiro',
        offensive_features=[
            'Golos de cabeca/90',
            'Passes progressivos/90', 'Corridas progressivas/90',
        ],
        defensive_features=[
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Cortes/90', 'Cortes de carrinho ajust. a posse',
            'Acoes defensivas com exito/90',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
            'Intersecoes/90', 'Intercecoes ajust. a posse',
            'Remates intercetados/90',
        ],
        passing_features=[
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terco final/90',
        ],
        physical_features=[
            'Duelos/90', 'Duelos ganhos, %',
        ],
        efficiency_features=[
            'Passes certos, %', 'Duelos defensivos ganhos, %',
            'Duelos aereos ganhos, %',
        ],
        domain_weights={
            'offensive': 0.05, 'passing': 0.20,
            'physical': 0.10, 'defensive': 0.50, 'efficiency': 0.15,
        },
    ),
    'Goleiro': PositionProfile(
        name='Goleiro',
        offensive_features=[],
        defensive_features=[
            'Defesas, %', 'Golos sofridos/90',
            'Remates sofridos/90', 'Golos sofridos esperados/90',
            'Golos expectaveis defendidos por 90',
        ],
        passing_features=[
            'Passes longos certos, %',
            'Passes para tras recebidos pelo guarda-redes/90',
        ],
        physical_features=[
            'Duelos aerios/90.1', 'Saidas/90',
        ],
        efficiency_features=[
            'Defesas, %', 'Golos expectaveis defendidos por 90',
        ],
        domain_weights={
            'offensive': 0.0, 'passing': 0.10,
            'physical': 0.10, 'defensive': 0.60, 'efficiency': 0.20,
        },
    ),
}

INVERTED_METRICS = frozenset({
    'Faltas/90', 'Cartoes amarelos/90', 'Cartoes vermelhos/90',
    'Golos sofridos/90', 'Remates sofridos/90', 'Golos sofridos esperados/90',
})


# ================================================================
# MÓDULO 1: PREPROCESSAMENTO
# ================================================================

class DataPreprocessor:
    """Pipeline de limpeza e normalização dos dados Wyscout/SkillCorner."""

    def __init__(self, scaler_type: str = 'robust'):
        self.scaler_type = scaler_type
        self.scaler = None
        self.imputer = SimpleImputer(strategy='median') if HAS_SKLEARN else None
        self._fitted = False

    @staticmethod
    def safe_float(val):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return np.nan
        try:
            if isinstance(val, str):
                val = val.replace(',', '.')
            return float(val)
        except (ValueError, TypeError):
            return np.nan

    def resolve_metric(self, metric: str, columns) -> Optional[str]:
        if metric in columns:
            return metric
        import unicodedata
        def strip_acc(s):
            return ''.join(
                c for c in unicodedata.normalize('NFD', s)
                if unicodedata.category(c) != 'Mn'
            )
        m_stripped = strip_acc(metric)
        for col in columns:
            if strip_acc(col) == m_stripped:
                return col
        return None

    def get_available_features(self, df: pd.DataFrame, position: str) -> List[str]:
        """Resolve quais features do perfil existem no DataFrame."""
        profile = POSITION_PROFILES.get(position)
        if not profile:
            return []
        all_features = set()
        for domain in ['offensive', 'defensive', 'passing', 'physical', 'efficiency']:
            features = getattr(profile, f'{domain}_features', [])
            all_features.update(features)
        resolved = []
        for f in all_features:
            r = self.resolve_metric(f, df.columns)
            if r is not None:
                resolved.append(r)
        return sorted(set(resolved))

    def prepare_matrix(self, df: pd.DataFrame, features: List[str],
                       min_minutes: int = 500,
                       minutes_col: str = 'Minutos jogados:') -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Retorna (df_filtrado, X_scaled).
        Filtra por minutos mínimos, imputa NaNs, escala.
        """
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário para prepare_matrix")

        df_work = df.copy()
        df_work[minutes_col] = df_work[minutes_col].apply(self.safe_float)
        df_work = df_work[df_work[minutes_col] >= min_minutes].copy()

        available = [f for f in features if f in df_work.columns]
        if len(available) < 3:
            raise ValueError(f"Features insuficientes: {len(available)} < 3")

        for col in available:
            df_work[col] = df_work[col].apply(self.safe_float)

        X_raw = df_work[available].values
        X_imputed = self.imputer.fit_transform(X_raw)

        if self.scaler_type == 'robust':
            self.scaler = RobustScaler()
        else:
            self.scaler = StandardScaler()

        X_scaled = self.scaler.fit_transform(X_imputed)
        self._fitted = True

        # Inverter métricas negativas
        for i, col in enumerate(available):
            if col in INVERTED_METRICS or self._is_inverted(col):
                X_scaled[:, i] *= -1

        df_out = df_work.copy()
        return df_out, X_scaled, available

    @staticmethod
    def _is_inverted(metric_name: str) -> bool:
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

    def percentile_rank(self, value: float, series: pd.Series) -> float:
        valid = pd.to_numeric(series, errors='coerce').dropna()
        if len(valid) == 0:
            return 50.0
        return float((valid < value).sum() / len(valid) * 100)


# ================================================================
# MÓDULO 2: FEATURE SELECTION (Ref: Eduardo Baptista / PIBITI)
# ================================================================

class PositionFeatureSelector:
    """
    Seleção de features por posição usando:
    1. Mutual Information para ranking de relevância
    2. PCA para redução de dimensionalidade
    3. Variância explicada acumulada como critério de corte

    Equação do score de relevância:
        relevance_i = α * MI(x_i, y) + β * |loading_i^PC1| + γ * domain_weight_i

    onde:
        α = 0.4 (peso da mutual information)
        β = 0.3 (peso do loading no PC1)
        γ = 0.3 (peso do domínio funcional da posição)
    """

    ALPHA = 0.4  # MI weight
    BETA = 0.3   # PCA loading weight
    GAMMA = 0.3  # Domain weight

    def __init__(self, n_components: float = 0.90):
        """n_components: variância explicada acumulada alvo para PCA."""
        self.n_components = n_components
        self.pca = None
        self.mi_scores = None
        self.feature_relevance = None

    def fit(self, X: np.ndarray, features: List[str], position: str,
            y: Optional[np.ndarray] = None) -> 'PositionFeatureSelector':
        """
        Calcula relevância de cada feature.
        y: target opcional (ex: score global, resultado de jogo). Se None, usa PCA unsupervised.
        """
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        n_samples, n_features = X.shape
        profile = POSITION_PROFILES.get(position)
        if not profile:
            raise ValueError(f"Posição desconhecida: {position}")

        # 1. PCA
        max_components = min(n_samples, n_features)
        self.pca = PCA(n_components=min(self.n_components, max_components))
        self.pca.fit(X)

        # Loading absoluto no PC1 (normalizado)
        if self.pca.components_.shape[0] > 0:
            pc1_loadings = np.abs(self.pca.components_[0])
            pc1_norm = pc1_loadings / (pc1_loadings.max() + 1e-10)
        else:
            pc1_norm = np.ones(n_features) / n_features

        # 2. Mutual Information
        if y is not None and len(np.unique(y)) > 1:
            if np.issubdtype(y.dtype, np.integer) or len(np.unique(y)) < 10:
                mi = mutual_info_classif(X, y, random_state=42)
            else:
                mi = mutual_info_regression(X, y, random_state=42)
            mi_norm = mi / (mi.max() + 1e-10)
        else:
            # Sem target: usar variância como proxy
            variances = np.var(X, axis=0)
            mi_norm = variances / (variances.max() + 1e-10)

        self.mi_scores = mi_norm

        # 3. Domain weights
        domain_scores = np.zeros(n_features)
        for i, feat in enumerate(features):
            domain_scores[i] = self._get_domain_weight(feat, profile)

        # Composite relevance score
        self.feature_relevance = (
            self.ALPHA * mi_norm +
            self.BETA * pc1_norm +
            self.GAMMA * domain_scores
        )

        return self

    def select(self, features: List[str], top_k: int = 15) -> List[Tuple[str, float]]:
        """Retorna top_k features ordenadas por relevância."""
        if self.feature_relevance is None:
            raise RuntimeError("Chame .fit() primeiro")
        indices = np.argsort(self.feature_relevance)[::-1][:top_k]
        return [(features[i], float(self.feature_relevance[i])) for i in indices]

    def get_weights_dict(self, features: List[str], top_k: int = 20) -> Dict[str, float]:
        """Retorna dict {feature: peso_normalizado} para integração com score."""
        selected = self.select(features, top_k)
        total = sum(s for _, s in selected)
        if total == 0:
            return {f: 1.0 / len(selected) for f, _ in selected}
        return {f: s / total for f, s in selected}

    @staticmethod
    def _get_domain_weight(feature: str, profile: PositionProfile) -> float:
        """Retorna o peso do domínio funcional a que a feature pertence."""
        for domain in ['offensive', 'defensive', 'passing', 'physical', 'efficiency']:
            domain_features = getattr(profile, f'{domain}_features', [])
            if feature in domain_features:
                return profile.domain_weights.get(domain, 0.1)
        return 0.05  # feature não mapeada


# ================================================================
# MÓDULO 3: WIN-PROBABILITY MODEL (Ref: Victor Schimidt TCC)
# ================================================================

class WinProbabilityModel:
    """
    Regressão Logística para identificar ações com significância
    estatística na probabilidade de vitória.

    Modelo:
        P(win) = σ(β₀ + Σ βᵢ·xᵢ)

    onde:
        σ = função sigmoide
        βᵢ = coeficiente da feature i
        xᵢ = valor padronizado da feature i

    Os coeficientes βᵢ com p-value < 0.05 são usados como pesos
    na nota do atleta (quanto maior |βᵢ|, mais a ação impacta vitória).
    """

    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level
        self.model = None
        self.coefficients = None
        self.p_values = None
        self.significant_features = None
        self._feature_names = None

    def fit(self, X: np.ndarray, y: np.ndarray,
            feature_names: List[str]) -> 'WinProbabilityModel':
        """
        Treina o modelo de win-probability.
        X: matriz de features padronizadas
        y: vetor binário (1=vitória, 0=não-vitória)
        """
        self._feature_names = feature_names

        if HAS_STATSMODELS:
            # Statsmodels para p-values
            X_const = sm.add_constant(X)
            try:
                logit_model = sm.Logit(y, X_const).fit(
                    disp=0, maxiter=200, method='bfgs'
                )
                self.coefficients = logit_model.params[1:]  # exclui constante
                self.p_values = logit_model.pvalues[1:]
            except Exception:
                # Fallback para sklearn se statsmodels falhar na convergência
                self._fit_sklearn(X, y)
        else:
            self._fit_sklearn(X, y)

        # Filtrar features significativas
        if self.p_values is not None:
            mask = self.p_values < self.significance_level
            self.significant_features = {
                feature_names[i]: {
                    'coefficient': float(self.coefficients[i]),
                    'p_value': float(self.p_values[i]),
                    'abs_impact': float(np.abs(self.coefficients[i])),
                }
                for i in range(len(feature_names)) if mask[i]
            }
        else:
            # Sem p-values, usar magnitude do coeficiente
            median_coef = np.median(np.abs(self.coefficients))
            self.significant_features = {
                feature_names[i]: {
                    'coefficient': float(self.coefficients[i]),
                    'p_value': None,
                    'abs_impact': float(np.abs(self.coefficients[i])),
                }
                for i in range(len(feature_names))
                if np.abs(self.coefficients[i]) > median_coef
            }

        return self

    def _fit_sklearn(self, X: np.ndarray, y: np.ndarray):
        """Fallback com sklearn LogisticRegression."""
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")
        self.model = LogisticRegression(
            penalty='l2', C=1.0, max_iter=500, random_state=42
        )
        self.model.fit(X, y)
        self.coefficients = self.model.coef_[0]
        self.p_values = None

    def get_wp_weights(self, normalize: bool = True) -> Dict[str, float]:
        """
        Retorna pesos baseados nos coeficientes significativos.
        Pesos são |βᵢ| normalizados.
        """
        if not self.significant_features:
            return {}
        weights = {
            f: info['abs_impact']
            for f, info in self.significant_features.items()
        }
        if normalize:
            total = sum(weights.values())
            if total > 0:
                weights = {f: w / total for f, w in weights.items()}
        return weights

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Probabilidade de vitória para cada observação."""
        if self.model is not None:
            return self.model.predict_proba(X)[:, 1]
        elif self.coefficients is not None:
            # Manual sigmoid
            z = X @ self.coefficients
            return 1.0 / (1.0 + np.exp(-z))
        raise RuntimeError("Modelo não treinado")

    def get_coefficient_matrix(self) -> pd.DataFrame:
        """Retorna DataFrame formatado com coeficientes e significância."""
        if self._feature_names is None or self.coefficients is None:
            return pd.DataFrame()
        rows = []
        for i, feat in enumerate(self._feature_names):
            rows.append({
                'Feature': feat,
                'Coeficiente_β': round(float(self.coefficients[i]), 4),
                'p_value': round(float(self.p_values[i]), 4) if self.p_values is not None else None,
                '|Impacto|': round(float(np.abs(self.coefficients[i])), 4),
                'Significativo': (
                    self.p_values[i] < self.significance_level
                    if self.p_values is not None
                    else np.abs(self.coefficients[i]) > np.median(np.abs(self.coefficients))
                ),
            })
        return pd.DataFrame(rows).sort_values('|Impacto|', ascending=False)


# ================================================================
# MÓDULO 4: xG RESIDUAL MODEL (Ref: Gabriel Buso TCC)
# ================================================================

class xGResidualModel:
    """
    Avaliação de eficiência ofensiva/defensiva via resíduos xG.

    Atacantes/Extremos:
        xG_overperformance = (Gols_reais - xG) / max(xG, 0.01)
        shot_quality = xGOT / max(Remates, 1)

    Goleiros:
        goals_prevented = xGA - Gols_sofridos_reais
        save_efficiency = Defesas% - xSave%_estimado

    Equação do score de eficiência:
        E_atk = 0.5 * z(xG_overperf) + 0.3 * z(shot_quality) + 0.2 * z(conversion_rate)
        E_gk  = 0.6 * z(goals_prevented) + 0.4 * z(save_efficiency)
    """

    # Mapeamento de colunas Wyscout (português)
    COL_MAP = {
        'goals': 'Golos/90',
        'xg': 'Golos esperados/90',
        'npg': 'Golos sem ser por penalti/90',
        'shots': 'Remates/90',
        'shots_on_target_pct': 'Remates a baliza, %',
        'conversion_rate': 'Golos marcados, %',
        'xga': 'Golos sofridos esperados/90',
        'goals_conceded': 'Golos sofridos/90',
        'save_pct': 'Defesas, %',
        'xg_prevented': 'Golos expectaveis defendidos por 90',
    }

    @classmethod
    def calculate_attacker_efficiency(cls, player_row, df_all,
                                       preprocessor: DataPreprocessor) -> Dict[str, float]:
        """Calcula score de eficiência ofensiva."""
        goals = preprocessor.safe_float(player_row.get(cls.COL_MAP['goals'], np.nan))
        xg = preprocessor.safe_float(player_row.get(cls.COL_MAP['xg'], np.nan))
        shots = preprocessor.safe_float(player_row.get(cls.COL_MAP['shots'], np.nan))
        sot_pct = preprocessor.safe_float(player_row.get(cls.COL_MAP['shots_on_target_pct'], np.nan))
        conv = preprocessor.safe_float(player_row.get(cls.COL_MAP['conversion_rate'], np.nan))

        result = {}

        # xG overperformance
        if not np.isnan(goals) and not np.isnan(xg) and xg > 0:
            result['xg_overperformance'] = (goals - xg) / max(xg, 0.01)
        else:
            result['xg_overperformance'] = 0.0

        # Shot quality (SOT% como proxy de xGOT quando não disponível)
        if not np.isnan(sot_pct):
            col = cls.COL_MAP['shots_on_target_pct']
            result['shot_quality_z'] = _z_score(sot_pct, df_all, col)
        else:
            result['shot_quality_z'] = 0.0

        # Conversion rate z-score
        if not np.isnan(conv):
            col = cls.COL_MAP['conversion_rate']
            result['conversion_z'] = _z_score(conv, df_all, col)
        else:
            result['conversion_z'] = 0.0

        # xG overperformance z-score
        xg_col = cls.COL_MAP['xg']
        goals_col = cls.COL_MAP['goals']
        if xg_col in df_all.columns and goals_col in df_all.columns:
            xg_series = pd.to_numeric(df_all[xg_col], errors='coerce')
            goals_series = pd.to_numeric(df_all[goals_col], errors='coerce')
            diff_series = goals_series - xg_series
            valid = diff_series.dropna()
            if len(valid) > 1:
                overperf_raw = goals - xg if not np.isnan(goals) and not np.isnan(xg) else 0.0
                result['xg_overperf_z'] = (overperf_raw - valid.mean()) / (valid.std() + 1e-10)
            else:
                result['xg_overperf_z'] = 0.0
        else:
            result['xg_overperf_z'] = 0.0

        # Score composto
        result['efficiency_score'] = (
            0.50 * result['xg_overperf_z'] +
            0.30 * result['shot_quality_z'] +
            0.20 * result['conversion_z']
        )
        return result

    @classmethod
    def calculate_goalkeeper_efficiency(cls, player_row, df_all,
                                         preprocessor: DataPreprocessor) -> Dict[str, float]:
        """Calcula score de eficiência de goleiro (gols prevenidos)."""
        xga = preprocessor.safe_float(player_row.get(cls.COL_MAP['xga'], np.nan))
        gc = preprocessor.safe_float(player_row.get(cls.COL_MAP['goals_conceded'], np.nan))
        save_pct = preprocessor.safe_float(player_row.get(cls.COL_MAP['save_pct'], np.nan))
        xg_prev = preprocessor.safe_float(player_row.get(cls.COL_MAP['xg_prevented'], np.nan))

        result = {}

        # Goals prevented (positivo = bom)
        if not np.isnan(xga) and not np.isnan(gc):
            result['goals_prevented_per90'] = xga - gc
        elif not np.isnan(xg_prev):
            result['goals_prevented_per90'] = xg_prev
        else:
            result['goals_prevented_per90'] = 0.0

        # Save efficiency z-score
        if not np.isnan(save_pct):
            col = cls.COL_MAP['save_pct']
            result['save_efficiency_z'] = _z_score(save_pct, df_all, col)
        else:
            result['save_efficiency_z'] = 0.0

        # Goals prevented z-score
        xg_prev_col = cls.COL_MAP['xg_prevented']
        if xg_prev_col in df_all.columns:
            result['gp_z'] = _z_score(
                result['goals_prevented_per90'], df_all, xg_prev_col
            )
        else:
            result['gp_z'] = 0.0

        result['efficiency_score'] = (
            0.60 * result['gp_z'] +
            0.40 * result['save_efficiency_z']
        )
        return result


# ================================================================
# MÓDULO 5: CLUSTERIZAÇÃO TÁTICA (Ref: Frederico Ferra / Tiago Pinto)
# ================================================================

class TacticalClusterer:
    """
    Clusterização multivariada para identificação de perfis táticos.

    Pipeline:
        1. PCA para redução (80-90% variância explicada)
        2. K-Means com silhouette optimization para k ∈ [3, 8]
        3. Gaussian Mixture Model para probabilidades de pertencimento
        4. Random Forest para interpretabilidade dos clusters

    Output: cluster labels + probabilidades + feature importance por cluster
    """

    def __init__(self, k_range: Tuple[int, int] = (3, 8),
                 pca_variance: float = 0.85):
        self.k_range = k_range
        self.pca_variance = pca_variance
        self.pca = None
        self.kmeans = None
        self.gmm = None
        self.rf_interpreter = None
        self.optimal_k = None
        self.cluster_profiles = None

    def fit(self, X: np.ndarray, feature_names: List[str]) -> 'TacticalClusterer':
        """Treina pipeline completo de clusterização."""
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        n_samples = X.shape[0]
        if n_samples < 10:
            raise ValueError(f"Amostra insuficiente para clustering: {n_samples}")

        # PCA
        max_comp = min(n_samples, X.shape[1])
        self.pca = PCA(n_components=min(self.pca_variance, max_comp))
        X_pca = self.pca.fit_transform(X)

        # K-Means com silhouette optimization
        k_min, k_max = self.k_range
        k_max = min(k_max, n_samples - 1)
        if k_min >= k_max:
            k_min = max(2, k_max - 1)

        best_score = -1
        best_k = k_min

        for k in range(k_min, k_max + 1):
            km = KMeans(n_clusters=k, n_init=10, random_state=42)
            labels = km.fit_predict(X_pca)
            if len(set(labels)) < 2:
                continue
            score = silhouette_score(X_pca, labels)
            if score > best_score:
                best_score = score
                best_k = k

        self.optimal_k = best_k
        self.kmeans = KMeans(n_clusters=best_k, n_init=20, random_state=42)
        labels = self.kmeans.fit_predict(X_pca)

        # GMM com mesmo k para probabilidades soft
        self.gmm = GaussianMixture(
            n_components=best_k, covariance_type='full',
            n_init=5, random_state=42
        )
        self.gmm.fit(X_pca)

        # Random Forest para interpretabilidade
        self.rf_interpreter = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )
        self.rf_interpreter.fit(X, labels)

        # Perfis dos clusters
        self.cluster_profiles = self._build_profiles(X, labels, feature_names)

        return self

    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        """Prediz cluster e probabilidades para novas observações."""
        X_pca = self.pca.transform(X)
        labels = self.kmeans.predict(X_pca)
        probas = self.gmm.predict_proba(X_pca)
        return {
            'labels': labels,
            'probabilities': probas,
            'dominant_cluster': labels,
        }

    def get_cluster_fit_score(self, X_single: np.ndarray) -> float:
        """
        Score de aderência ao cluster (0-1).
        Quanto maior a probabilidade do cluster dominante, melhor o fit.
        """
        X_pca = self.pca.transform(X_single.reshape(1, -1))
        probas = self.gmm.predict_proba(X_pca)[0]
        return float(np.max(probas))

    def get_feature_importance(self) -> Dict[str, float]:
        """Feature importance do RF interpreter."""
        if self.rf_interpreter is None:
            return {}
        return dict(zip(
            range(self.rf_interpreter.n_features_in_),
            self.rf_interpreter.feature_importances_
        ))

    def _build_profiles(self, X: np.ndarray, labels: np.ndarray,
                        features: List[str]) -> Dict[int, Dict]:
        """Constrói perfil estatístico de cada cluster."""
        profiles = {}
        for k in range(self.optimal_k):
            mask = labels == k
            X_cluster = X[mask]
            if len(X_cluster) == 0:
                continue
            profiles[k] = {
                'size': int(mask.sum()),
                'centroid': {features[i]: float(X_cluster[:, i].mean())
                             for i in range(len(features))},
                'std': {features[i]: float(X_cluster[:, i].std())
                        for i in range(len(features))},
            }
        return profiles


# ================================================================
# MÓDULO 6: SIMILARIDADE AVANÇADA (substitui compute_weighted_cosine_similarity)
# ================================================================

class AdvancedSimilarity:
    """
    Substituição da similaridade cosseno ponderada por:
    1. Distância de Mahalanobis (considera correlações entre features)
    2. Random Forest Proximity (co-ocorrência em folhas)
    3. Peso do cluster como componente

    Score final:
        S = α * (1 - d_mahal_norm) + β * rf_proximity + γ * cluster_fit
        α=0.40, β=0.35, γ=0.25
    """

    ALPHA = 0.40  # Mahalanobis weight
    BETA = 0.35   # RF proximity weight
    GAMMA = 0.25  # Cluster fit weight

    def __init__(self):
        self.rf_model = None
        self.X_pool = None
        self.cov_inv = None

    def fit(self, X_pool: np.ndarray):
        """Prepara a base de comparação."""
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        self.X_pool = X_pool

        # Inversa da covariância para Mahalanobis
        cov = np.cov(X_pool, rowvar=False)
        try:
            self.cov_inv = np.linalg.inv(cov + np.eye(cov.shape[0]) * 1e-6)
        except np.linalg.LinAlgError:
            self.cov_inv = np.eye(cov.shape[0])

        # RF para proximity matrix
        # Treina RF para distinguir cada jogador (self-supervised)
        n = X_pool.shape[0]
        if n > 5:
            # Criar target sintético via clustering rápido
            k = min(max(3, n // 10), 10)
            quick_labels = KMeans(n_clusters=k, n_init=5, random_state=42).fit_predict(X_pool)
            self.rf_model = RandomForestClassifier(
                n_estimators=200, max_depth=None, random_state=42
            )
            self.rf_model.fit(X_pool, quick_labels)

        return self

    def compute_similarity(self, target_vec: np.ndarray, pool_indices: np.ndarray = None,
                           clusterer: Optional[TacticalClusterer] = None,
                           top_n: int = 20) -> List[Dict]:
        """
        Calcula similaridade do target contra o pool.
        Retorna lista ordenada de {index, similarity_pct, components}.
        """
        if self.X_pool is None:
            raise RuntimeError("Chame .fit() primeiro")

        X_pool = self.X_pool
        n_pool = X_pool.shape[0]
        target = target_vec.reshape(1, -1)

        # 1. Mahalanobis distances
        diffs = X_pool - target
        mahal_dists = np.sqrt(np.sum(diffs @ self.cov_inv * diffs, axis=1))
        mahal_max = mahal_dists.max() + 1e-10
        mahal_sim = 1.0 - (mahal_dists / mahal_max)

        # 2. RF Proximity
        if self.rf_model is not None:
            leaves_target = self.rf_model.apply(target)[0]  # shape: (n_trees,)
            leaves_pool = self.rf_model.apply(X_pool)        # shape: (n_pool, n_trees)
            rf_prox = np.mean(leaves_pool == leaves_target, axis=1)
        else:
            rf_prox = np.zeros(n_pool)

        # 3. Cluster fit
        if clusterer is not None:
            target_cluster = clusterer.predict(target)['labels'][0]
            pool_clusters = clusterer.predict(X_pool)['labels']
            cluster_sim = (pool_clusters == target_cluster).astype(float)
        else:
            cluster_sim = np.zeros(n_pool)

        # Composite score
        similarity = (
            self.ALPHA * mahal_sim +
            self.BETA * rf_prox +
            self.GAMMA * cluster_sim
        ) * 100.0

        # Rank
        indices = np.argsort(similarity)[::-1][:top_n]
        results = []
        for idx in indices:
            results.append({
                'pool_index': int(idx),
                'similarity_pct': round(float(similarity[idx]), 1),
                'mahalanobis_component': round(float(mahal_sim[idx] * 100), 1),
                'rf_proximity_component': round(float(rf_prox[idx] * 100), 1),
                'cluster_component': round(float(cluster_sim[idx] * 100), 1),
            })

        return results


# ================================================================
# MÓDULO 7: SCOUT SCORE PREDITIVO (Score Global Integrado)
# ================================================================

class ScoutScorePreditivo:
    """
    Índice global integrado que substitui calculate_overall_score().

    Equação:
        SSP = λ₁·WP_Score + λ₂·Efficiency_Score + λ₃·Cluster_Fit + λ₄·Percentile_Score

    onde:
        λ₁ = 0.30 (contribuição do modelo de win-probability)
        λ₂ = 0.25 (contribuição da eficiência xG-residual)
        λ₃ = 0.15 (aderência ao perfil tático ideal)
        λ₄ = 0.30 (percentil ponderado por feature selection — backward compat)

    Range: 0-100
    """

    LAMBDA_WP = 0.25
    LAMBDA_EFF = 0.25
    LAMBDA_CLUSTER = 0.15
    LAMBDA_PERC = 0.35

    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.feature_selector = None
        self.wp_model = None
        self.clusterer = None
        self.selected_weights = None
        self._fitted = False
        # Usar lambdas calibrados se calibration.py disponível
        if HAS_CALIBRATION:
            self.LAMBDA_WP = _CALIBRATED_LAMBDAS.get('wp', 0.25)
            self.LAMBDA_EFF = _CALIBRATED_LAMBDAS.get('efficiency', 0.25)
            self.LAMBDA_CLUSTER = _CALIBRATED_LAMBDAS.get('cluster', 0.15)
            self.LAMBDA_PERC = _CALIBRATED_LAMBDAS.get('percentile', 0.35)

    def fit(self, df: pd.DataFrame, position: str,
            result_col: Optional[str] = None,
            min_minutes: int = 500,
            minutes_col: str = 'Minutos jogados:') -> 'ScoutScorePreditivo':
        """
        Treina todos os sub-modelos.
        result_col: coluna com resultado do jogo (win/loss) se disponível.
        """
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        features = self.preprocessor.get_available_features(df, position)
        if len(features) < 5:
            raise ValueError(f"Features insuficientes: {len(features)}")

        df_filtered, X_scaled, available = self.preprocessor.prepare_matrix(
            df, features, min_minutes, minutes_col
        )

        # Feature Selection
        self.feature_selector = PositionFeatureSelector()
        y_target = None
        if result_col and result_col in df_filtered.columns:
            y_target = pd.to_numeric(df_filtered[result_col], errors='coerce').fillna(0).values

        self.feature_selector.fit(X_scaled, available, position, y_target)
        self.selected_weights = self.feature_selector.get_weights_dict(available, top_k=15)

        # Win-Probability (se target disponível)
        if y_target is not None and len(np.unique(y_target)) > 1:
            self.wp_model = WinProbabilityModel()
            self.wp_model.fit(X_scaled, (y_target > 0).astype(int), available)

        # Clusterização
        if len(df_filtered) >= 15:
            self.clusterer = TacticalClusterer()
            try:
                self.clusterer.fit(X_scaled, available)
            except Exception:
                self.clusterer = None

        self._fitted = True
        self._position = position
        self._available = available
        self._df_base = df_filtered
        self._X_base = X_scaled

        return self

    def score_player(self, player_row, df_all: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula o Scout Score Preditivo para um jogador.

        Returns:
            {
                'ssp': float (0-100),
                'wp_component': float,
                'efficiency_component': float,
                'cluster_component': float,
                'percentile_component': float,
                'details': {...}
            }
        """
        position = self._position if self._fitted else None
        if position is None:
            return {'ssp': None, 'error': 'Modelo não treinado'}

        # Componente 1: Percentil ponderado (backward compatible)
        perc_score = self._percentile_component(player_row, df_all)

        # Componente 2: Win-Probability
        wp_score = self._wp_component(player_row, df_all)

        # Componente 3: Eficiência xG
        eff_score = self._efficiency_component(player_row, df_all)

        # Componente 4: Cluster fit
        cluster_score = self._cluster_component(player_row, df_all)

        # Composite SSP
        ssp = (
            self.LAMBDA_WP * wp_score +
            self.LAMBDA_EFF * eff_score +
            self.LAMBDA_CLUSTER * cluster_score +
            self.LAMBDA_PERC * perc_score
        )

        return {
            'ssp': round(max(0, min(100, ssp)), 1),
            'wp_component': round(wp_score, 1),
            'efficiency_component': round(eff_score, 1),
            'cluster_component': round(cluster_score, 1),
            'percentile_component': round(perc_score, 1),
            'position': position,
            'classification': classify_performance(max(0, min(100, ssp))) if HAS_CALIBRATION else None,
        }

    def rank_players(self, df_players: pd.DataFrame, df_all: pd.DataFrame,
                     min_minutes: int = 500,
                     minutes_col: str = 'Minutos jogados:') -> pd.DataFrame:
        """Ranking batch de jogadores por SSP."""
        pool = df_players.copy()
        pool[minutes_col] = pool[minutes_col].apply(self.preprocessor.safe_float)
        pool = pool[pool[minutes_col] >= min_minutes]

        scores = []
        for idx, row in pool.iterrows():
            result = self.score_player(row, df_all)
            if result.get('ssp') is not None:
                scores.append({
                    '_idx': idx,
                    'SSP': result['ssp'],
                    'WP': result['wp_component'],
                    'Efficiency': result['efficiency_component'],
                    'Cluster': result['cluster_component'],
                    'Percentile': result['percentile_component'],
                })

        if not scores:
            return pd.DataFrame()

        df_scores = pd.DataFrame(scores).sort_values('SSP', ascending=False)
        out = pool.loc[df_scores['_idx']].copy()
        for col in ['SSP', 'WP', 'Efficiency', 'Cluster', 'Percentile']:
            out[col] = df_scores.set_index('_idx')[col]
        return out.sort_values('SSP', ascending=False)

    # --- Componentes internos ---

    def _percentile_component(self, player_row, df_all) -> float:
        """Percentil ponderado pelos pesos calibrados (PIBITI 2025 quando disponível)."""
        # Priorizar pesos calibrados do PIBITI
        weights = self.selected_weights or {}
        if HAS_CALIBRATION and self._position and not weights:
            weights = get_calibrated_rating_weights(self._position)
        if not weights:
            return 50.0

        weighted_sum = 0.0
        total_weight = 0.0

        for feature, w in weights.items():
            resolved = self.preprocessor.resolve_metric(feature, player_row.index)
            if resolved is None:
                continue
            val = self.preprocessor.safe_float(player_row[resolved])
            if np.isnan(val):
                continue
            perc = self.preprocessor.percentile_rank(val, df_all[resolved])
            if feature in INVERTED_METRICS or self.preprocessor._is_inverted(feature):
                perc = 100.0 - perc
            weighted_sum += perc * w
            total_weight += w

        if total_weight == 0:
            return 50.0
        return weighted_sum / total_weight

    def _wp_component(self, player_row, df_all) -> float:
        """Componente de win-probability (calibrado por Schimidt 2021 quando disponível)."""
        # Tentar usar pesos calibrados (Schimidt)
        if HAS_CALIBRATION and self._position:
            wp_weights = get_calibrated_wp_weights(self._position)
            if wp_weights:
                weighted_sum = 0.0
                total_weight = 0.0
                for feature, w in wp_weights.items():
                    resolved = self.preprocessor.resolve_metric(feature, player_row.index)
                    if resolved is None:
                        continue
                    val = self.preprocessor.safe_float(player_row[resolved])
                    if np.isnan(val):
                        continue
                    perc = self.preprocessor.percentile_rank(val, df_all[resolved])
                    if feature in INVERTED_METRICS:
                        perc = 100.0 - perc
                    weighted_sum += perc * w
                    total_weight += w
                if total_weight > 0:
                    return weighted_sum / total_weight

        if self.wp_model is None or not self.wp_model.significant_features:
            # Fallback: usar percentil das features significativas padrão
            return self._percentile_component(player_row, df_all)

        wp_weights = self.wp_model.get_wp_weights()
        weighted_sum = 0.0
        total_weight = 0.0

        for feature, w in wp_weights.items():
            resolved = self.preprocessor.resolve_metric(feature, player_row.index)
            if resolved is None:
                continue
            val = self.preprocessor.safe_float(player_row[resolved])
            if np.isnan(val):
                continue
            perc = self.preprocessor.percentile_rank(val, df_all[resolved])
            if feature in INVERTED_METRICS:
                perc = 100.0 - perc
            weighted_sum += perc * w
            total_weight += w

        if total_weight == 0:
            return 50.0
        return weighted_sum / total_weight

    def _efficiency_component(self, player_row, df_all) -> float:
        """Componente de eficiência xG."""
        position = self._position
        if position == 'Goleiro':
            eff = xGResidualModel.calculate_goalkeeper_efficiency(
                player_row, df_all, self.preprocessor
            )
        elif position in ('Atacante', 'Extremo', 'Meia'):
            eff = xGResidualModel.calculate_attacker_efficiency(
                player_row, df_all, self.preprocessor
            )
        else:
            return 50.0  # Posições sem modelo xG direto

        raw = eff.get('efficiency_score', 0.0)
        # Converter z-score para escala 0-100 (CDF da normal)
        from scipy.stats import norm
        try:
            return float(norm.cdf(raw) * 100)
        except Exception:
            # Fallback sigmoid
            return float(1.0 / (1.0 + np.exp(-raw)) * 100)

    def _cluster_component(self, player_row, df_all) -> float:
        """Componente de aderência ao cluster tático."""
        if self.clusterer is None:
            return 50.0

        try:
            features = self._available
            vals = []
            for f in features:
                resolved = self.preprocessor.resolve_metric(f, player_row.index)
                if resolved:
                    v = self.preprocessor.safe_float(player_row[resolved])
                    vals.append(v if not np.isnan(v) else 0.0)
                else:
                    vals.append(0.0)

            X_single = np.array(vals).reshape(1, -1)
            if self.preprocessor.scaler is not None:
                X_single = self.preprocessor.scaler.transform(
                    self.preprocessor.imputer.transform(X_single)
                )
            fit_score = self.clusterer.get_cluster_fit_score(X_single[0])
            return fit_score * 100
        except Exception:
            return 50.0


# ================================================================
# MÓDULO 8: PREDIÇÃO DE SUCESSO DE CONTRATAÇÃO (Ref: Felipe Nunes)
# ================================================================

class ContractSuccessPredictor:
    """
    Modelo preditivo de sucesso de contratação.

    Features de input:
        - Métricas de desempenho (normalizadas por posição)
        - Idade do jogador
        - Nível da liga de origem vs destino
        - Minutagem (proxy de regularidade)
        - Tendência de desempenho (slope das métricas ao longo da temporada)

    Modelo: Gradient Boosting Classifier (ou XGBoost se disponível)

    P(sucesso) = f(performance_vector, age, league_gap, minutes_trend)

    Nota: Requer dados históricos de contratações com label de sucesso/fracasso
    para treino supervisionado. Sem esses dados, opera em modo unsupervised
    usando score composto + heurísticas.
    """

    # Tiers de liga refinados (escala 1-10)
    # Fonte: calibração contextual do futebol brasileiro + europeu
    LEAGUE_TIERS = {
        # Brasil
        'Serie A Brasil': 7, 'Serie B Brasil': 5, 'Serie C Brasil': 3,
        'Serie D Brasil': 1.5, 'Brasileirao Sub-20': 2,
        'Paulista A1': 4, 'Paulista A2': 2.5, 'Paulista A3': 1.5,
        'Carioca A1': 4, 'Carioca A2': 2,
        'Gaucho A1': 3.5, 'Mineiro A1': 3.5,
        'Copa do Brasil': 6, 'Copa do Nordeste': 4,
        # Europa top 5
        'Premier League': 10, 'La Liga': 9.5, 'Serie A Italia': 9,
        'Bundesliga': 9, 'Ligue 1': 8,
        # Europa secundárias
        'Championship': 7, 'La Liga 2': 6, 'Serie B Italia': 6,
        '2. Bundesliga': 6, 'Ligue 2': 5.5,
        'Eredivisie': 7, 'Liga Portugal': 7,
        'Liga Portugal 2': 5, 'Belgian Pro League': 6.5,
        'Scottish Premiership': 5.5, 'Super Lig': 6,
        # Américas
        'MLS': 6, 'Liga MX': 6.5,
        'Liga Argentina': 6, 'Superliga Argentina': 6,
        'Liga Colombiana': 4.5, 'Liga Chilena': 4,
        'Liga Uruguaia': 4.5, 'Liga Paraguaia': 3.5,
        # Outros
        'J1 League': 6, 'K League': 5.5,
        'Saudi Pro League': 6, 'Super League China': 4,
    }

    def __init__(self):
        self.model = None
        self._fitted = False

    def fit_supervised(self, X: np.ndarray, y: np.ndarray,
                       feature_names: List[str]) -> 'ContractSuccessPredictor':
        """Treina com dados históricos de contratações."""
        if HAS_XGB:
            self.model = xgb.XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8,
                random_state=42, eval_metric='logloss'
            )
        elif HAS_SKLEARN:
            self.model = GradientBoostingClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                random_state=42
            )
        else:
            raise RuntimeError("scikit-learn ou xgboost necessário")

        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict_success_unsupervised(self, ssp_score: float, age: float,
                                      league_origin: str, league_target: str,
                                      minutes: float,
                                      max_minutes: float = 3000) -> Dict[str, Any]:
        """
        Estima probabilidade de sucesso via modelo heurístico com
        penalização exponencial por gap de liga.

        Equação:
            P_success = σ(w₁·SSP_adj + w₂·age_f + w₃·league_f + w₄·min_f) × ceiling

        Mudanças vs v1:
            - SSP é descontado pelo nível da liga de origem (SSP em Paulista A2 ≠ SSP em Serie A)
            - League factor usa penalização exponencial por gap (não linear)
            - Hard ceiling para gaps extremos (>5 tiers)
            - Pesos redistribuídos: liga tem 30% de influência

        Gap penalty:
            gap = tier_target - tier_origin
            league_factor = exp(-0.35 * gap)  se gap > 0 (subindo de liga)
            league_factor = 1.0               se gap <= 0 (descendo ou lateral)

        Hard ceiling:
            Se gap >= 6: prob capped em 15%
            Se gap >= 4: prob capped em 35%
        """
        tier_origin = self.LEAGUE_TIERS.get(league_origin, 5)
        tier_target = self.LEAGUE_TIERS.get(league_target, 5)
        gap = tier_target - tier_origin

        # 1. SSP ajustado pelo contexto da liga de origem
        # Desconta o SSP se a liga de origem é fraca (inflar estatísticas em ligas fracas)
        # Liga tier 10 → desconto 0%. Liga tier 2.5 → desconto ~30%.
        league_discount = min(tier_origin / 10.0, 1.0)
        ssp_adj = (ssp_score / 100.0) * (0.7 + 0.3 * league_discount)

        # 2. Age factor (peak = 26, decay quadrático)
        age_factor = max(0, 1 - ((age - 26) ** 2) / (15 ** 2))

        # 3. League factor — exponencial para gaps positivos
        if gap <= 0:
            # Descendo ou lateral: sem penalização
            league_factor = 1.0
        else:
            # Subindo: penalização exponencial
            # gap=1 → 0.70, gap=2 → 0.50, gap=3 → 0.35,
            # gap=4 → 0.25, gap=5 → 0.17, gap=7 → 0.09
            league_factor = np.exp(-0.35 * gap)

        # 4. Minutes factor (regularidade)
        minutes_factor = min(minutes / max_minutes, 1.0)

        # Composite — liga tem peso dominante quando há gap grande
        z = (
            0.30 * ssp_adj +
            0.15 * age_factor +
            0.35 * league_factor +
            0.20 * minutes_factor
        )

        # Sigmoid com amplificação
        z_scaled = (z - 0.5) * 8
        prob = 1.0 / (1.0 + np.exp(-z_scaled))

        # Hard ceiling para gaps extremos
        if gap >= 6:
            prob = min(prob, 0.15)
        elif gap >= 5:
            prob = min(prob, 0.25)
        elif gap >= 4:
            prob = min(prob, 0.35)

        # Risk classification com thresholds ajustados
        if prob >= 0.65:
            risk = 'baixo'
        elif prob >= 0.40:
            risk = 'medio'
        elif prob >= 0.20:
            risk = 'alto'
        else:
            risk = 'muito alto'

        return {
            'success_probability': round(float(prob), 3),
            'ssp_contribution': round(ssp_adj, 3),
            'age_factor': round(age_factor, 3),
            'league_factor': round(league_factor, 3),
            'minutes_factor': round(minutes_factor, 3),
            'league_gap': round(gap, 1),
            'league_discount': round(league_discount, 3),
            'tier_origin': tier_origin,
            'tier_target': tier_target,
            'risk_level': risk,
        }


# ================================================================
# HELPERS
# ================================================================

def _z_score(value: float, df: pd.DataFrame, col: str) -> float:
    """Z-score de um valor em relação à distribuição da coluna."""
    series = pd.to_numeric(df[col], errors='coerce').dropna()
    if len(series) < 2:
        return 0.0
    mean = series.mean()
    std = series.std()
    if std == 0:
        return 0.0
    return (value - mean) / std


# ================================================================
# BACKWARD COMPATIBILITY — Drop-in replacements para similarity.py
# ================================================================

# Re-exportar constantes legadas
try:
    from similarity import POSITION_WEIGHTS as _LEGACY_WEIGHTS
except Exception:
    _LEGACY_WEIGHTS = {}

# Importar coeficientes calibrados (se disponível)
try:
    from calibration import (
        get_calibrated_wp_weights,
        get_calibrated_rating_weights,
        get_negative_impact_features,
        WP_COEFFICIENTS as _CALIBRATED_WP,
        NUNES_MODEL_RESULTS,
        BUSO_XG_MODEL,
        BUSO_XGOT_MODEL,
        SSP_LAMBDAS as _CALIBRATED_LAMBDAS,
        classify_performance,
    )
    HAS_CALIBRATION = True
except Exception:
    HAS_CALIBRATION = False
    def classify_performance(score):
        if score >= 80: return 'Muito Alto'
        if score >= 60: return 'Alto'
        if score >= 40: return 'Médio'
        if score >= 20: return 'Baixo'
        return 'Muito Baixo'

def calculate_overall_score_v3(player_row, position, df_all,
                                 ssp_engine: Optional[ScoutScorePreditivo] = None):
    """
    Drop-in replacement para calculate_overall_score().
    Se ssp_engine fornecido, usa score preditivo. Senão, fallback para v2.
    """
    if ssp_engine is not None and ssp_engine._fitted:
        result = ssp_engine.score_player(player_row, df_all)
        return result.get('ssp')
    # Fallback legacy
    from similarity import calculate_overall_score
    return calculate_overall_score(player_row, position, df_all)


def compute_advanced_similarity(target_player, comparison_pool, position,
                                 top_n=20, min_minutes=500,
                                 minutes_col='Minutos jogados:',
                                 player_display_col='JogadorDisplay',
                                 percentile_base=None):
    """
    Drop-in replacement para compute_weighted_cosine_similarity().
    Usa Mahalanobis + RF proximity quando sklearn disponível.
    Fallback para cosseno ponderado original caso contrário.
    """
    if not HAS_SKLEARN:
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(
            target_player, comparison_pool, position,
            top_n, min_minutes, minutes_col, player_display_col, percentile_base
        )

    preprocessor = DataPreprocessor()
    features = preprocessor.get_available_features(comparison_pool, position)
    if len(features) < 5:
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(
            target_player, comparison_pool, position,
            top_n, min_minutes, minutes_col, player_display_col, percentile_base
        )

    try:
        df_filtered, X_scaled, available = preprocessor.prepare_matrix(
            comparison_pool, features, min_minutes, minutes_col
        )
    except (ValueError, Exception):
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(
            target_player, comparison_pool, position,
            top_n, min_minutes, minutes_col, player_display_col, percentile_base
        )

    if player_display_col in df_filtered.columns and player_display_col in target_player.index:
        mask = df_filtered[player_display_col] != target_player[player_display_col]
        df_filtered = df_filtered[mask]
        X_scaled = X_scaled[mask.values]

    if len(df_filtered) < 5:
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(
            target_player, comparison_pool, position,
            top_n, min_minutes, minutes_col, player_display_col, percentile_base
        )

    # Preparar vetor do target
    target_vals = []
    for f in available:
        resolved = preprocessor.resolve_metric(f, target_player.index)
        if resolved:
            v = preprocessor.safe_float(target_player[resolved])
            target_vals.append(v if not np.isnan(v) else 0.0)
        else:
            target_vals.append(0.0)

    target_vec = np.array(target_vals).reshape(1, -1)
    target_scaled = preprocessor.scaler.transform(
        preprocessor.imputer.transform(target_vec)
    )

    # Similarity engine
    sim_engine = AdvancedSimilarity()
    sim_engine.fit(X_scaled)

    # Opcional: clusterer
    clusterer = None
    if len(df_filtered) >= 15:
        try:
            clusterer = TacticalClusterer()
            clusterer.fit(X_scaled, available)
        except Exception:
            clusterer = None

    results = sim_engine.compute_similarity(
        target_scaled[0], clusterer=clusterer, top_n=top_n
    )

    # Montar DataFrame de saída compatível
    if not results:
        return pd.DataFrame()

    indices = [r['pool_index'] for r in results]
    out = df_filtered.iloc[indices].copy()
    out['similarity_pct'] = [r['similarity_pct'] for r in results]
    out['matched_metrics'] = len(available)
    out['mahalanobis_sim'] = [r['mahalanobis_component'] for r in results]
    out['rf_proximity'] = [r['rf_proximity_component'] for r in results]

    return out.sort_values('similarity_pct', ascending=False)    name: str
    offensive_features: List[str] = field(default_factory=list)
    defensive_features: List[str] = field(default_factory=list)
    passing_features: List[str] = field(default_factory=list)
    physical_features: List[str] = field(default_factory=list)
    efficiency_features: List[str] = field(default_factory=list)
    domain_weights: Dict[str, float] = field(default_factory=dict)


# Taxonomia de features por domínio funcional (base: Eduardo Baptista / PIBITI)
POSITION_PROFILES = {
    'Atacante': PositionProfile(
        name='Atacante',
        offensive_features=[
            'Golos/90', 'Golos esperados/90', 'Golos sem ser por penalti/90',
            'Remates/90', 'Remates a baliza, %', 'Golos marcados, %',
            'Toques na area/90', 'Golos de cabeca/90',
        ],
        defensive_features=[
            'Acoes defensivas com exito/90',
        ],
        passing_features=[
            'Assistencias/90', 'Assistencias esperadas/90',
            'Passes chave/90', 'Segundas assistencias/90',
            'Passes recebidos/90', 'Recesao de passes em profundidade/90',
        ],
        physical_features=[
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
            'Aceleracoes/90', 'Corridas progressivas/90',
        ],
        efficiency_features=[
            'Golos/90', 'Golos esperados/90', 'Remates a baliza, %',
            'Golos marcados, %',
        ],
        domain_weights={
            'offensive': 0.40, 'passing': 0.20,
            'physical': 0.20, 'defensive': 0.05, 'efficiency': 0.15,
        },
    ),
    'Extremo': PositionProfile(
        name='Extremo',
        offensive_features=[
            'Golos/90', 'Golos esperados/90', 'Remates/90',
            'Toques na area/90',
        ],
        defensive_features=[
            'Acoes defensivas com exito/90',
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
        ],
        passing_features=[
            'Assistencias/90', 'Assistencias esperadas/90',
            'Passes chave/90', 'Passes inteligentes/90',
            'Passes para a area de penalti/90',
            'Cruzamentos/90', 'Cruzamentos certos, %',
        ],
        physical_features=[
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Aceleracoes/90', 'Corridas progressivas/90',
        ],
        efficiency_features=[
            'Dribles com sucesso, %', 'Cruzamentos certos, %',
            'Passes chave/90',
        ],
        domain_weights={
            'offensive': 0.25, 'passing': 0.30,
            'physical': 0.25, 'defensive': 0.05, 'efficiency': 0.15,
        },
    ),
    'Meia': PositionProfile(
        name='Meia',
        offensive_features=[
            'Golos/90', 'Golos esperados/90', 'Remates/90',
            'Toques na area/90',
        ],
        defensive_features=[
            'Acoes defensivas com exito/90',
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Intersecoes/90',
        ],
        passing_features=[
            'Assistencias/90', 'Assistencias esperadas/90',
            'Passes chave/90', 'Passes inteligentes/90',
            'Passes inteligentes certos, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terco final/90',
            'Passes em profundidade/90', 'Passes em profundidade certos, %',
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
        ],
        physical_features=[
            'Dribles/90', 'Dribles com sucesso, %',
            'Corridas progressivas/90',
        ],
        efficiency_features=[
            'Passes certos, %', 'Passes inteligentes certos, %',
            'Passes progressivos certos, %',
        ],
        domain_weights={
            'offensive': 0.15, 'passing': 0.40,
            'physical': 0.10, 'defensive': 0.15, 'efficiency': 0.20,
        },
    ),
    'Volante': PositionProfile(
        name='Volante',
        offensive_features=[
            'Passes progressivos/90', 'Corridas progressivas/90',
            'Passes em profundidade/90',
        ],
        defensive_features=[
            'Acoes defensivas com exito/90', 'Intersecoes/90',
            'Intercecoes ajust. a posse',
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Cortes/90', 'Cortes de carrinho ajust. a posse',
            'Remates intercetados/90',
        ],
        passing_features=[
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terco final/90',
        ],
        physical_features=[
            'Duelos/90', 'Duelos ganhos, %',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
        ],
        efficiency_features=[
            'Passes certos, %', 'Duelos defensivos ganhos, %',
            'Duelos ganhos, %',
        ],
        domain_weights={
            'offensive': 0.10, 'passing': 0.25,
            'physical': 0.15, 'defensive': 0.35, 'efficiency': 0.15,
        },
    ),
    'Lateral': PositionProfile(
        name='Lateral',
        offensive_features=[
            'Cruzamentos/90', 'Cruzamentos certos, %',
            'Cruzamentos para a area de baliza/90',
            'Toques na area/90', 'Passes para a area de penalti/90',
            'Assistencias/90', 'Assistencias esperadas/90',
        ],
        defensive_features=[
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Intersecoes/90', 'Cortes/90',
            'Acoes defensivas com exito/90', 'Remates intercetados/90',
        ],
        passing_features=[
            'Passes para terco final/90', 'Passes certos para terco final, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes em profundidade/90', 'Passes chave/90',
        ],
        physical_features=[
            'Corridas progressivas/90', 'Aceleracoes/90',
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos/90', 'Duelos ganhos, %',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
        ],
        efficiency_features=[
            'Cruzamentos certos, %', 'Duelos defensivos ganhos, %',
            'Dribles com sucesso, %',
        ],
        domain_weights={
            'offensive': 0.25, 'passing': 0.20,
            'physical': 0.20, 'defensive': 0.25, 'efficiency': 0.10,
        },
    ),
    'Zagueiro': PositionProfile(
        name='Zagueiro',
        offensive_features=[
            'Golos de cabeca/90',
            'Passes progressivos/90', 'Corridas progressivas/90',
        ],
        defensive_features=[
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Cortes/90', 'Cortes de carrinho ajust. a posse',
            'Acoes defensivas com exito/90',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
            'Intersecoes/90', 'Intercecoes ajust. a posse',
            'Remates intercetados/90',
        ],
        passing_features=[
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terco final/90',
        ],
        physical_features=[
            'Duelos/90', 'Duelos ganhos, %',
        ],
        efficiency_features=[
            'Passes certos, %', 'Duelos defensivos ganhos, %',
            'Duelos aereos ganhos, %',
        ],
        domain_weights={
            'offensive': 0.05, 'passing': 0.20,
            'physical': 0.10, 'defensive': 0.50, 'efficiency': 0.15,
        },
    ),
    'Goleiro': PositionProfile(
        name='Goleiro',
        offensive_features=[],
        defensive_features=[
            'Defesas, %', 'Golos sofridos/90',
            'Remates sofridos/90', 'Golos sofridos esperados/90',
            'Golos expectaveis defendidos por 90',
        ],
        passing_features=[
            'Passes longos certos, %',
            'Passes para tras recebidos pelo guarda-redes/90',
        ],
        physical_features=[
            'Duelos aerios/90.1', 'Saidas/90',
        ],
        efficiency_features=[
            'Defesas, %', 'Golos expectaveis defendidos por 90',
        ],
        domain_weights={
            'offensive': 0.0, 'passing': 0.10,
            'physical': 0.10, 'defensive': 0.60, 'efficiency': 0.20,
        },
    ),
}

INVERTED_METRICS = frozenset({
    'Faltas/90', 'Cartoes amarelos/90', 'Cartoes vermelhos/90',
    'Golos sofridos/90', 'Remates sofridos/90', 'Golos sofridos esperados/90',
})


# ================================================================
# MÓDULO 1: PREPROCESSAMENTO
# ================================================================

class DataPreprocessor:
    """Pipeline de limpeza e normalização dos dados Wyscout/SkillCorner."""

    def __init__(self, scaler_type: str = 'robust'):
        self.scaler_type = scaler_type
        self.scaler = None
        self.imputer = SimpleImputer(strategy='median') if HAS_SKLEARN else None
        self._fitted = False

    @staticmethod
    def safe_float(val):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return np.nan
        try:
            if isinstance(val, str):
                val = val.replace(',', '.')
            return float(val)
        except (ValueError, TypeError):
            return np.nan

    def resolve_metric(self, metric: str, columns) -> Optional[str]:
        if metric in columns:
            return metric
        import unicodedata
        def strip_acc(s):
            return ''.join(
                c for c in unicodedata.normalize('NFD', s)
                if unicodedata.category(c) != 'Mn'
            )
        m_stripped = strip_acc(metric)
        for col in columns:
            if strip_acc(col) == m_stripped:
                return col
        return None

    def get_available_features(self, df: pd.DataFrame, position: str) -> List[str]:
        """Resolve quais features do perfil existem no DataFrame."""
        profile = POSITION_PROFILES.get(position)
        if not profile:
            return []
        all_features = set()
        for domain in ['offensive', 'defensive', 'passing', 'physical', 'efficiency']:
            features = getattr(profile, f'{domain}_features', [])
            all_features.update(features)
        resolved = []
        for f in all_features:
            r = self.resolve_metric(f, df.columns)
            if r is not None:
                resolved.append(r)
        return sorted(set(resolved))

    def prepare_matrix(self, df: pd.DataFrame, features: List[str],
                       min_minutes: int = 500,
                       minutes_col: str = 'Minutos jogados:') -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Retorna (df_filtrado, X_scaled).
        Filtra por minutos mínimos, imputa NaNs, escala.
        """
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário para prepare_matrix")

        df_work = df.copy()
        df_work[minutes_col] = df_work[minutes_col].apply(self.safe_float)
        df_work = df_work[df_work[minutes_col] >= min_minutes].copy()

        available = [f for f in features if f in df_work.columns]
        if len(available) < 3:
            raise ValueError(f"Features insuficientes: {len(available)} < 3")

        for col in available:
            df_work[col] = df_work[col].apply(self.safe_float)

        X_raw = df_work[available].values
        X_imputed = self.imputer.fit_transform(X_raw)

        if self.scaler_type == 'robust':
            self.scaler = RobustScaler()
        else:
            self.scaler = StandardScaler()

        X_scaled = self.scaler.fit_transform(X_imputed)
        self._fitted = True

        # Inverter métricas negativas
        for i, col in enumerate(available):
            if col in INVERTED_METRICS or self._is_inverted(col):
                X_scaled[:, i] *= -1

        df_out = df_work.copy()
        return df_out, X_scaled, available

    @staticmethod
    def _is_inverted(metric_name: str) -> bool:
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

    def percentile_rank(self, value: float, series: pd.Series) -> float:
        valid = pd.to_numeric(series, errors='coerce').dropna()
        if len(valid) == 0:
            return 50.0
        return float((valid < value).sum() / len(valid) * 100)


# ================================================================
# MÓDULO 2: FEATURE SELECTION (Ref: Eduardo Baptista / PIBITI)
# ================================================================

class PositionFeatureSelector:
    """
    Seleção de features por posição usando:
    1. Mutual Information para ranking de relevância
    2. PCA para redução de dimensionalidade
    3. Variância explicada acumulada como critério de corte

    Equação do score de relevância:
        relevance_i = α * MI(x_i, y) + β * |loading_i^PC1| + γ * domain_weight_i

    onde:
        α = 0.4 (peso da mutual information)
        β = 0.3 (peso do loading no PC1)
        γ = 0.3 (peso do domínio funcional da posição)
    """

    ALPHA = 0.4  # MI weight
    BETA = 0.3   # PCA loading weight
    GAMMA = 0.3  # Domain weight

    def __init__(self, n_components: float = 0.90):
        """n_components: variância explicada acumulada alvo para PCA."""
        self.n_components = n_components
        self.pca = None
        self.mi_scores = None
        self.feature_relevance = None

    def fit(self, X: np.ndarray, features: List[str], position: str,
            y: Optional[np.ndarray] = None) -> 'PositionFeatureSelector':
        """
        Calcula relevância de cada feature.
        y: target opcional (ex: score global, resultado de jogo). Se None, usa PCA unsupervised.
        """
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        n_samples, n_features = X.shape
        profile = POSITION_PROFILES.get(position)
        if not profile:
            raise ValueError(f"Posição desconhecida: {position}")

        # 1. PCA
        max_components = min(n_samples, n_features)
        self.pca = PCA(n_components=min(self.n_components, max_components))
        self.pca.fit(X)

        # Loading absoluto no PC1 (normalizado)
        if self.pca.components_.shape[0] > 0:
            pc1_loadings = np.abs(self.pca.components_[0])
            pc1_norm = pc1_loadings / (pc1_loadings.max() + 1e-10)
        else:
            pc1_norm = np.ones(n_features) / n_features

        # 2. Mutual Information
        if y is not None and len(np.unique(y)) > 1:
            if np.issubdtype(y.dtype, np.integer) or len(np.unique(y)) < 10:
                mi = mutual_info_classif(X, y, random_state=42)
            else:
                mi = mutual_info_regression(X, y, random_state=42)
            mi_norm = mi / (mi.max() + 1e-10)
        else:
            # Sem target: usar variância como proxy
            variances = np.var(X, axis=0)
            mi_norm = variances / (variances.max() + 1e-10)

        self.mi_scores = mi_norm

        # 3. Domain weights
        domain_scores = np.zeros(n_features)
        for i, feat in enumerate(features):
            domain_scores[i] = self._get_domain_weight(feat, profile)

        # Composite relevance score
        self.feature_relevance = (
            self.ALPHA * mi_norm +
            self.BETA * pc1_norm +
            self.GAMMA * domain_scores
        )

        return self

    def select(self, features: List[str], top_k: int = 15) -> List[Tuple[str, float]]:
        """Retorna top_k features ordenadas por relevância."""
        if self.feature_relevance is None:
            raise RuntimeError("Chame .fit() primeiro")
        indices = np.argsort(self.feature_relevance)[::-1][:top_k]
        return [(features[i], float(self.feature_relevance[i])) for i in indices]

    def get_weights_dict(self, features: List[str], top_k: int = 20) -> Dict[str, float]:
        """Retorna dict {feature: peso_normalizado} para integração com score."""
        selected = self.select(features, top_k)
        total = sum(s for _, s in selected)
        if total == 0:
            return {f: 1.0 / len(selected) for f, _ in selected}
        return {f: s / total for f, s in selected}

    @staticmethod
    def _get_domain_weight(feature: str, profile: PositionProfile) -> float:
        """Retorna o peso do domínio funcional a que a feature pertence."""
        for domain in ['offensive', 'defensive', 'passing', 'physical', 'efficiency']:
            domain_features = getattr(profile, f'{domain}_features', [])
            if feature in domain_features:
                return profile.domain_weights.get(domain, 0.1)
        return 0.05  # feature não mapeada


# ================================================================
# MÓDULO 3: WIN-PROBABILITY MODEL (Ref: Victor Schimidt TCC)
# ================================================================

class WinProbabilityModel:
    """
    Regressão Logística para identificar ações com significância
    estatística na probabilidade de vitória.

    Modelo:
        P(win) = σ(β₀ + Σ βᵢ·xᵢ)

    onde:
        σ = função sigmoide
        βᵢ = coeficiente da feature i
        xᵢ = valor padronizado da feature i

    Os coeficientes βᵢ com p-value < 0.05 são usados como pesos
    na nota do atleta (quanto maior |βᵢ|, mais a ação impacta vitória).
    """

    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level
        self.model = None
        self.coefficients = None
        self.p_values = None
        self.significant_features = None
        self._feature_names = None

    def fit(self, X: np.ndarray, y: np.ndarray,
            feature_names: List[str]) -> 'WinProbabilityModel':
        """
        Treina o modelo de win-probability.
        X: matriz de features padronizadas
        y: vetor binário (1=vitória, 0=não-vitória)
        """
        self._feature_names = feature_names

        if HAS_STATSMODELS:
            # Statsmodels para p-values
            X_const = sm.add_constant(X)
            try:
                logit_model = sm.Logit(y, X_const).fit(
                    disp=0, maxiter=200, method='bfgs'
                )
                self.coefficients = logit_model.params[1:]  # exclui constante
                self.p_values = logit_model.pvalues[1:]
            except Exception:
                # Fallback para sklearn se statsmodels falhar na convergência
                self._fit_sklearn(X, y)
        else:
            self._fit_sklearn(X, y)

        # Filtrar features significativas
        if self.p_values is not None:
            mask = self.p_values < self.significance_level
            self.significant_features = {
                feature_names[i]: {
                    'coefficient': float(self.coefficients[i]),
                    'p_value': float(self.p_values[i]),
                    'abs_impact': float(np.abs(self.coefficients[i])),
                }
                for i in range(len(feature_names)) if mask[i]
            }
        else:
            # Sem p-values, usar magnitude do coeficiente
            median_coef = np.median(np.abs(self.coefficients))
            self.significant_features = {
                feature_names[i]: {
                    'coefficient': float(self.coefficients[i]),
                    'p_value': None,
                    'abs_impact': float(np.abs(self.coefficients[i])),
                }
                for i in range(len(feature_names))
                if np.abs(self.coefficients[i]) > median_coef
            }

        return self

    def _fit_sklearn(self, X: np.ndarray, y: np.ndarray):
        """Fallback com sklearn LogisticRegression."""
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")
        self.model = LogisticRegression(
            penalty='l2', C=1.0, max_iter=500, random_state=42
        )
        self.model.fit(X, y)
        self.coefficients = self.model.coef_[0]
        self.p_values = None

    def get_wp_weights(self, normalize: bool = True) -> Dict[str, float]:
        """
        Retorna pesos baseados nos coeficientes significativos.
        Pesos são |βᵢ| normalizados.
        """
        if not self.significant_features:
            return {}
        weights = {
            f: info['abs_impact']
            for f, info in self.significant_features.items()
        }
        if normalize:
            total = sum(weights.values())
            if total > 0:
                weights = {f: w / total for f, w in weights.items()}
        return weights

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Probabilidade de vitória para cada observação."""
        if self.model is not None:
            return self.model.predict_proba(X)[:, 1]
        elif self.coefficients is not None:
            # Manual sigmoid
            z = X @ self.coefficients
            return 1.0 / (1.0 + np.exp(-z))
        raise RuntimeError("Modelo não treinado")

    def get_coefficient_matrix(self) -> pd.DataFrame:
        """Retorna DataFrame formatado com coeficientes e significância."""
        if self._feature_names is None or self.coefficients is None:
            return pd.DataFrame()
        rows = []
        for i, feat in enumerate(self._feature_names):
            rows.append({
                'Feature': feat,
                'Coeficiente_β': round(float(self.coefficients[i]), 4),
                'p_value': round(float(self.p_values[i]), 4) if self.p_values is not None else None,
                '|Impacto|': round(float(np.abs(self.coefficients[i])), 4),
                'Significativo': (
                    self.p_values[i] < self.significance_level
                    if self.p_values is not None
                    else np.abs(self.coefficients[i]) > np.median(np.abs(self.coefficients))
                ),
            })
        return pd.DataFrame(rows).sort_values('|Impacto|', ascending=False)


# ================================================================
# MÓDULO 4: xG RESIDUAL MODEL (Ref: Gabriel Buso TCC)
# ================================================================

class xGResidualModel:
    """
    Avaliação de eficiência ofensiva/defensiva via resíduos xG.

    Atacantes/Extremos:
        xG_overperformance = (Gols_reais - xG) / max(xG, 0.01)
        shot_quality = xGOT / max(Remates, 1)

    Goleiros:
        goals_prevented = xGA - Gols_sofridos_reais
        save_efficiency = Defesas% - xSave%_estimado

    Equação do score de eficiência:
        E_atk = 0.5 * z(xG_overperf) + 0.3 * z(shot_quality) + 0.2 * z(conversion_rate)
        E_gk  = 0.6 * z(goals_prevented) + 0.4 * z(save_efficiency)
    """

    # Mapeamento de colunas Wyscout (português)
    COL_MAP = {
        'goals': 'Golos/90',
        'xg': 'Golos esperados/90',
        'npg': 'Golos sem ser por penalti/90',
        'shots': 'Remates/90',
        'shots_on_target_pct': 'Remates a baliza, %',
        'conversion_rate': 'Golos marcados, %',
        'xga': 'Golos sofridos esperados/90',
        'goals_conceded': 'Golos sofridos/90',
        'save_pct': 'Defesas, %',
        'xg_prevented': 'Golos expectaveis defendidos por 90',
    }

    @classmethod
    def calculate_attacker_efficiency(cls, player_row, df_all,
                                       preprocessor: DataPreprocessor) -> Dict[str, float]:
        """Calcula score de eficiência ofensiva."""
        goals = preprocessor.safe_float(player_row.get(cls.COL_MAP['goals'], np.nan))
        xg = preprocessor.safe_float(player_row.get(cls.COL_MAP['xg'], np.nan))
        shots = preprocessor.safe_float(player_row.get(cls.COL_MAP['shots'], np.nan))
        sot_pct = preprocessor.safe_float(player_row.get(cls.COL_MAP['shots_on_target_pct'], np.nan))
        conv = preprocessor.safe_float(player_row.get(cls.COL_MAP['conversion_rate'], np.nan))

        result = {}

        # xG overperformance
        if not np.isnan(goals) and not np.isnan(xg) and xg > 0:
            result['xg_overperformance'] = (goals - xg) / max(xg, 0.01)
        else:
            result['xg_overperformance'] = 0.0

        # Shot quality (SOT% como proxy de xGOT quando não disponível)
        if not np.isnan(sot_pct):
            col = cls.COL_MAP['shots_on_target_pct']
            result['shot_quality_z'] = _z_score(sot_pct, df_all, col)
        else:
            result['shot_quality_z'] = 0.0

        # Conversion rate z-score
        if not np.isnan(conv):
            col = cls.COL_MAP['conversion_rate']
            result['conversion_z'] = _z_score(conv, df_all, col)
        else:
            result['conversion_z'] = 0.0

        # xG overperformance z-score
        xg_col = cls.COL_MAP['xg']
        goals_col = cls.COL_MAP['goals']
        if xg_col in df_all.columns and goals_col in df_all.columns:
            xg_series = pd.to_numeric(df_all[xg_col], errors='coerce')
            goals_series = pd.to_numeric(df_all[goals_col], errors='coerce')
            diff_series = goals_series - xg_series
            valid = diff_series.dropna()
            if len(valid) > 1:
                overperf_raw = goals - xg if not np.isnan(goals) and not np.isnan(xg) else 0.0
                result['xg_overperf_z'] = (overperf_raw - valid.mean()) / (valid.std() + 1e-10)
            else:
                result['xg_overperf_z'] = 0.0
        else:
            result['xg_overperf_z'] = 0.0

        # Score composto
        result['efficiency_score'] = (
            0.50 * result['xg_overperf_z'] +
            0.30 * result['shot_quality_z'] +
            0.20 * result['conversion_z']
        )
        return result

    @classmethod
    def calculate_goalkeeper_efficiency(cls, player_row, df_all,
                                         preprocessor: DataPreprocessor) -> Dict[str, float]:
        """Calcula score de eficiência de goleiro (gols prevenidos)."""
        xga = preprocessor.safe_float(player_row.get(cls.COL_MAP['xga'], np.nan))
        gc = preprocessor.safe_float(player_row.get(cls.COL_MAP['goals_conceded'], np.nan))
        save_pct = preprocessor.safe_float(player_row.get(cls.COL_MAP['save_pct'], np.nan))
        xg_prev = preprocessor.safe_float(player_row.get(cls.COL_MAP['xg_prevented'], np.nan))

        result = {}

        # Goals prevented (positivo = bom)
        if not np.isnan(xga) and not np.isnan(gc):
            result['goals_prevented_per90'] = xga - gc
        elif not np.isnan(xg_prev):
            result['goals_prevented_per90'] = xg_prev
        else:
            result['goals_prevented_per90'] = 0.0

        # Save efficiency z-score
        if not np.isnan(save_pct):
            col = cls.COL_MAP['save_pct']
            result['save_efficiency_z'] = _z_score(save_pct, df_all, col)
        else:
            result['save_efficiency_z'] = 0.0

        # Goals prevented z-score
        xg_prev_col = cls.COL_MAP['xg_prevented']
        if xg_prev_col in df_all.columns:
            result['gp_z'] = _z_score(
                result['goals_prevented_per90'], df_all, xg_prev_col
            )
        else:
            result['gp_z'] = 0.0

        result['efficiency_score'] = (
            0.60 * result['gp_z'] +
            0.40 * result['save_efficiency_z']
        )
        return result


# ================================================================
# MÓDULO 5: CLUSTERIZAÇÃO TÁTICA (Ref: Frederico Ferra / Tiago Pinto)
# ================================================================

class TacticalClusterer:
    """
    Clusterização multivariada para identificação de perfis táticos.

    Pipeline:
        1. PCA para redução (80-90% variância explicada)
        2. K-Means com silhouette optimization para k ∈ [3, 8]
        3. Gaussian Mixture Model para probabilidades de pertencimento
        4. Random Forest para interpretabilidade dos clusters

    Output: cluster labels + probabilidades + feature importance por cluster
    """

    def __init__(self, k_range: Tuple[int, int] = (3, 8),
                 pca_variance: float = 0.85):
        self.k_range = k_range
        self.pca_variance = pca_variance
        self.pca = None
        self.kmeans = None
        self.gmm = None
        self.rf_interpreter = None
        self.optimal_k = None
        self.cluster_profiles = None

    def fit(self, X: np.ndarray, feature_names: List[str]) -> 'TacticalClusterer':
        """Treina pipeline completo de clusterização."""
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        n_samples = X.shape[0]
        if n_samples < 10:
            raise ValueError(f"Amostra insuficiente para clustering: {n_samples}")

        # PCA
        max_comp = min(n_samples, X.shape[1])
        self.pca = PCA(n_components=min(self.pca_variance, max_comp))
        X_pca = self.pca.fit_transform(X)

        # K-Means com silhouette optimization
        k_min, k_max = self.k_range
        k_max = min(k_max, n_samples - 1)
        if k_min >= k_max:
            k_min = max(2, k_max - 1)

        best_score = -1
        best_k = k_min

        for k in range(k_min, k_max + 1):
            km = KMeans(n_clusters=k, n_init=10, random_state=42)
            labels = km.fit_predict(X_pca)
            if len(set(labels)) < 2:
                continue
            score = silhouette_score(X_pca, labels)
            if score > best_score:
                best_score = score
                best_k = k

        self.optimal_k = best_k
        self.kmeans = KMeans(n_clusters=best_k, n_init=20, random_state=42)
        labels = self.kmeans.fit_predict(X_pca)

        # GMM com mesmo k para probabilidades soft
        self.gmm = GaussianMixture(
            n_components=best_k, covariance_type='full',
            n_init=5, random_state=42
        )
        self.gmm.fit(X_pca)

        # Random Forest para interpretabilidade
        self.rf_interpreter = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )
        self.rf_interpreter.fit(X, labels)

        # Perfis dos clusters
        self.cluster_profiles = self._build_profiles(X, labels, feature_names)

        return self

    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        """Prediz cluster e probabilidades para novas observações."""
        X_pca = self.pca.transform(X)
        labels = self.kmeans.predict(X_pca)
        probas = self.gmm.predict_proba(X_pca)
        return {
            'labels': labels,
            'probabilities': probas,
            'dominant_cluster': labels,
        }

    def get_cluster_fit_score(self, X_single: np.ndarray) -> float:
        """
        Score de aderência ao cluster (0-1).
        Quanto maior a probabilidade do cluster dominante, melhor o fit.
        """
        X_pca = self.pca.transform(X_single.reshape(1, -1))
        probas = self.gmm.predict_proba(X_pca)[0]
        return float(np.max(probas))

    def get_feature_importance(self) -> Dict[str, float]:
        """Feature importance do RF interpreter."""
        if self.rf_interpreter is None:
            return {}
        return dict(zip(
            range(self.rf_interpreter.n_features_in_),
            self.rf_interpreter.feature_importances_
        ))

    def _build_profiles(self, X: np.ndarray, labels: np.ndarray,
                        features: List[str]) -> Dict[int, Dict]:
        """Constrói perfil estatístico de cada cluster."""
        profiles = {}
        for k in range(self.optimal_k):
            mask = labels == k
            X_cluster = X[mask]
            if len(X_cluster) == 0:
                continue
            profiles[k] = {
                'size': int(mask.sum()),
                'centroid': {features[i]: float(X_cluster[:, i].mean())
                             for i in range(len(features))},
                'std': {features[i]: float(X_cluster[:, i].std())
                        for i in range(len(features))},
            }
        return profiles


# ================================================================
# MÓDULO 6: SIMILARIDADE AVANÇADA (substitui compute_weighted_cosine_similarity)
# ================================================================

class AdvancedSimilarity:
    """
    Substituição da similaridade cosseno ponderada por:
    1. Distância de Mahalanobis (considera correlações entre features)
    2. Random Forest Proximity (co-ocorrência em folhas)
    3. Peso do cluster como componente

    Score final:
        S = α * (1 - d_mahal_norm) + β * rf_proximity + γ * cluster_fit
        α=0.40, β=0.35, γ=0.25
    """

    ALPHA = 0.40  # Mahalanobis weight
    BETA = 0.35   # RF proximity weight
    GAMMA = 0.25  # Cluster fit weight

    def __init__(self):
        self.rf_model = None
        self.X_pool = None
        self.cov_inv = None

    def fit(self, X_pool: np.ndarray):
        """Prepara a base de comparação."""
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        self.X_pool = X_pool

        # Inversa da covariância para Mahalanobis
        cov = np.cov(X_pool, rowvar=False)
        try:
            self.cov_inv = np.linalg.inv(cov + np.eye(cov.shape[0]) * 1e-6)
        except np.linalg.LinAlgError:
            self.cov_inv = np.eye(cov.shape[0])

        # RF para proximity matrix
        # Treina RF para distinguir cada jogador (self-supervised)
        n = X_pool.shape[0]
        if n > 5:
            # Criar target sintético via clustering rápido
            k = min(max(3, n // 10), 10)
            quick_labels = KMeans(n_clusters=k, n_init=5, random_state=42).fit_predict(X_pool)
            self.rf_model = RandomForestClassifier(
                n_estimators=200, max_depth=None, random_state=42
            )
            self.rf_model.fit(X_pool, quick_labels)

        return self

    def compute_similarity(self, target_vec: np.ndarray, pool_indices: np.ndarray = None,
                           clusterer: Optional[TacticalClusterer] = None,
                           top_n: int = 20) -> List[Dict]:
        """
        Calcula similaridade do target contra o pool.
        Retorna lista ordenada de {index, similarity_pct, components}.
        """
        if self.X_pool is None:
            raise RuntimeError("Chame .fit() primeiro")

        X_pool = self.X_pool
        n_pool = X_pool.shape[0]
        target = target_vec.reshape(1, -1)

        # 1. Mahalanobis distances
        diffs = X_pool - target
        mahal_dists = np.sqrt(np.sum(diffs @ self.cov_inv * diffs, axis=1))
        mahal_max = mahal_dists.max() + 1e-10
        mahal_sim = 1.0 - (mahal_dists / mahal_max)

        # 2. RF Proximity
        if self.rf_model is not None:
            leaves_target = self.rf_model.apply(target)[0]  # shape: (n_trees,)
            leaves_pool = self.rf_model.apply(X_pool)        # shape: (n_pool, n_trees)
            rf_prox = np.mean(leaves_pool == leaves_target, axis=1)
        else:
            rf_prox = np.zeros(n_pool)

        # 3. Cluster fit
        if clusterer is not None:
            target_cluster = clusterer.predict(target)['labels'][0]
            pool_clusters = clusterer.predict(X_pool)['labels']
            cluster_sim = (pool_clusters == target_cluster).astype(float)
        else:
            cluster_sim = np.zeros(n_pool)

        # Composite score
        similarity = (
            self.ALPHA * mahal_sim +
            self.BETA * rf_prox +
            self.GAMMA * cluster_sim
        ) * 100.0

        # Rank
        indices = np.argsort(similarity)[::-1][:top_n]
        results = []
        for idx in indices:
            results.append({
                'pool_index': int(idx),
                'similarity_pct': round(float(similarity[idx]), 1),
                'mahalanobis_component': round(float(mahal_sim[idx] * 100), 1),
                'rf_proximity_component': round(float(rf_prox[idx] * 100), 1),
                'cluster_component': round(float(cluster_sim[idx] * 100), 1),
            })

        return results


# ================================================================
# MÓDULO 7: SCOUT SCORE PREDITIVO (Score Global Integrado)
# ================================================================

class ScoutScorePreditivo:
    """
    Índice global integrado que substitui calculate_overall_score().

    Equação:
        SSP = λ₁·WP_Score + λ₂·Efficiency_Score + λ₃·Cluster_Fit + λ₄·Percentile_Score

    onde:
        λ₁ = 0.30 (contribuição do modelo de win-probability)
        λ₂ = 0.25 (contribuição da eficiência xG-residual)
        λ₃ = 0.15 (aderência ao perfil tático ideal)
        λ₄ = 0.30 (percentil ponderado por feature selection — backward compat)

    Range: 0-100
    """

    LAMBDA_WP = 0.25
    LAMBDA_EFF = 0.25
    LAMBDA_CLUSTER = 0.15
    LAMBDA_PERC = 0.35

    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.feature_selector = None
        self.wp_model = None
        self.clusterer = None
        self.selected_weights = None
        self._fitted = False
        # Usar lambdas calibrados se calibration.py disponível
        if HAS_CALIBRATION:
            self.LAMBDA_WP = _CALIBRATED_LAMBDAS.get('wp', 0.25)
            self.LAMBDA_EFF = _CALIBRATED_LAMBDAS.get('efficiency', 0.25)
            self.LAMBDA_CLUSTER = _CALIBRATED_LAMBDAS.get('cluster', 0.15)
            self.LAMBDA_PERC = _CALIBRATED_LAMBDAS.get('percentile', 0.35)

    def fit(self, df: pd.DataFrame, position: str,
            result_col: Optional[str] = None,
            min_minutes: int = 500,
            minutes_col: str = 'Minutos jogados:') -> 'ScoutScorePreditivo':
        """
        Treina todos os sub-modelos.
        result_col: coluna com resultado do jogo (win/loss) se disponível.
        """
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        features = self.preprocessor.get_available_features(df, position)
        if len(features) < 5:
            raise ValueError(f"Features insuficientes: {len(features)}")

        df_filtered, X_scaled, available = self.preprocessor.prepare_matrix(
            df, features, min_minutes, minutes_col
        )

        # Feature Selection
        self.feature_selector = PositionFeatureSelector()
        y_target = None
        if result_col and result_col in df_filtered.columns:
            y_target = pd.to_numeric(df_filtered[result_col], errors='coerce').fillna(0).values

        self.feature_selector.fit(X_scaled, available, position, y_target)
        self.selected_weights = self.feature_selector.get_weights_dict(available, top_k=15)

        # Win-Probability (se target disponível)
        if y_target is not None and len(np.unique(y_target)) > 1:
            self.wp_model = WinProbabilityModel()
            self.wp_model.fit(X_scaled, (y_target > 0).astype(int), available)

        # Clusterização
        if len(df_filtered) >= 15:
            self.clusterer = TacticalClusterer()
            try:
                self.clusterer.fit(X_scaled, available)
            except Exception:
                self.clusterer = None

        self._fitted = True
        self._position = position
        self._available = available
        self._df_base = df_filtered
        self._X_base = X_scaled

        return self

    def score_player(self, player_row, df_all: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula o Scout Score Preditivo para um jogador.

        Returns:
            {
                'ssp': float (0-100),
                'wp_component': float,
                'efficiency_component': float,
                'cluster_component': float,
                'percentile_component': float,
                'details': {...}
            }
        """
        position = self._position if self._fitted else None
        if position is None:
            return {'ssp': None, 'error': 'Modelo não treinado'}

        # Componente 1: Percentil ponderado (backward compatible)
        perc_score = self._percentile_component(player_row, df_all)

        # Componente 2: Win-Probability
        wp_score = self._wp_component(player_row, df_all)

        # Componente 3: Eficiência xG
        eff_score = self._efficiency_component(player_row, df_all)

        # Componente 4: Cluster fit
        cluster_score = self._cluster_component(player_row, df_all)

        # Composite SSP
        ssp = (
            self.LAMBDA_WP * wp_score +
            self.LAMBDA_EFF * eff_score +
            self.LAMBDA_CLUSTER * cluster_score +
            self.LAMBDA_PERC * perc_score
        )

        return {
            'ssp': round(max(0, min(100, ssp)), 1),
            'wp_component': round(wp_score, 1),
            'efficiency_component': round(eff_score, 1),
            'cluster_component': round(cluster_score, 1),
            'percentile_component': round(perc_score, 1),
            'position': position,
            'classification': classify_performance(max(0, min(100, ssp))) if HAS_CALIBRATION else None,
        }

    def rank_players(self, df_players: pd.DataFrame, df_all: pd.DataFrame,
                     min_minutes: int = 500,
                     minutes_col: str = 'Minutos jogados:') -> pd.DataFrame:
        """Ranking batch de jogadores por SSP."""
        pool = df_players.copy()
        pool[minutes_col] = pool[minutes_col].apply(self.preprocessor.safe_float)
        pool = pool[pool[minutes_col] >= min_minutes]

        scores = []
        for idx, row in pool.iterrows():
            result = self.score_player(row, df_all)
            if result.get('ssp') is not None:
                scores.append({
                    '_idx': idx,
                    'SSP': result['ssp'],
                    'WP': result['wp_component'],
                    'Efficiency': result['efficiency_component'],
                    'Cluster': result['cluster_component'],
                    'Percentile': result['percentile_component'],
                })

        if not scores:
            return pd.DataFrame()

        df_scores = pd.DataFrame(scores).sort_values('SSP', ascending=False)
        out = pool.loc[df_scores['_idx']].copy()
        for col in ['SSP', 'WP', 'Efficiency', 'Cluster', 'Percentile']:
            out[col] = df_scores.set_index('_idx')[col]
        return out.sort_values('SSP', ascending=False)

    # --- Componentes internos ---

    def _percentile_component(self, player_row, df_all) -> float:
        """Percentil ponderado pelos pesos calibrados (PIBITI 2025 quando disponível)."""
        # Priorizar pesos calibrados do PIBITI
        weights = self.selected_weights or {}
        if HAS_CALIBRATION and self._position and not weights:
            weights = get_calibrated_rating_weights(self._position)
        if not weights:
            return 50.0

        weighted_sum = 0.0
        total_weight = 0.0

        for feature, w in weights.items():
            resolved = self.preprocessor.resolve_metric(feature, player_row.index)
            if resolved is None:
                continue
            val = self.preprocessor.safe_float(player_row[resolved])
            if np.isnan(val):
                continue
            perc = self.preprocessor.percentile_rank(val, df_all[resolved])
            if feature in INVERTED_METRICS or self.preprocessor._is_inverted(feature):
                perc = 100.0 - perc
            weighted_sum += perc * w
            total_weight += w

        if total_weight == 0:
            return 50.0
        return weighted_sum / total_weight

    def _wp_component(self, player_row, df_all) -> float:
        """Componente de win-probability (calibrado por Schimidt 2021 quando disponível)."""
        # Tentar usar pesos calibrados (Schimidt)
        if HAS_CALIBRATION and self._position:
            wp_weights = get_calibrated_wp_weights(self._position)
            if wp_weights:
                weighted_sum = 0.0
                total_weight = 0.0
                for feature, w in wp_weights.items():
                    resolved = self.preprocessor.resolve_metric(feature, player_row.index)
                    if resolved is None:
                        continue
                    val = self.preprocessor.safe_float(player_row[resolved])
                    if np.isnan(val):
                        continue
                    perc = self.preprocessor.percentile_rank(val, df_all[resolved])
                    if feature in INVERTED_METRICS:
                        perc = 100.0 - perc
                    weighted_sum += perc * w
                    total_weight += w
                if total_weight > 0:
                    return weighted_sum / total_weight

        if self.wp_model is None or not self.wp_model.significant_features:
            # Fallback: usar percentil das features significativas padrão
            return self._percentile_component(player_row, df_all)

        wp_weights = self.wp_model.get_wp_weights()
        weighted_sum = 0.0
        total_weight = 0.0

        for feature, w in wp_weights.items():
            resolved = self.preprocessor.resolve_metric(feature, player_row.index)
            if resolved is None:
                continue
            val = self.preprocessor.safe_float(player_row[resolved])
            if np.isnan(val):
                continue
            perc = self.preprocessor.percentile_rank(val, df_all[resolved])
            if feature in INVERTED_METRICS:
                perc = 100.0 - perc
            weighted_sum += perc * w
            total_weight += w

        if total_weight == 0:
            return 50.0
        return weighted_sum / total_weight

    def _efficiency_component(self, player_row, df_all) -> float:
        """Componente de eficiência xG."""
        position = self._position
        if position == 'Goleiro':
            eff = xGResidualModel.calculate_goalkeeper_efficiency(
                player_row, df_all, self.preprocessor
            )
        elif position in ('Atacante', 'Extremo', 'Meia'):
            eff = xGResidualModel.calculate_attacker_efficiency(
                player_row, df_all, self.preprocessor
            )
        else:
            return 50.0  # Posições sem modelo xG direto

        raw = eff.get('efficiency_score', 0.0)
        # Converter z-score para escala 0-100 (CDF da normal)
        from scipy.stats import norm
        try:
            return float(norm.cdf(raw) * 100)
        except Exception:
            # Fallback sigmoid
            return float(1.0 / (1.0 + np.exp(-raw)) * 100)

    def _cluster_component(self, player_row, df_all) -> float:
        """Componente de aderência ao cluster tático."""
        if self.clusterer is None:
            return 50.0

        try:
            features = self._available
            vals = []
            for f in features:
                resolved = self.preprocessor.resolve_metric(f, player_row.index)
                if resolved:
                    v = self.preprocessor.safe_float(player_row[resolved])
                    vals.append(v if not np.isnan(v) else 0.0)
                else:
                    vals.append(0.0)

            X_single = np.array(vals).reshape(1, -1)
            if self.preprocessor.scaler is not None:
                X_single = self.preprocessor.scaler.transform(
                    self.preprocessor.imputer.transform(X_single)
                )
            fit_score = self.clusterer.get_cluster_fit_score(X_single[0])
            return fit_score * 100
        except Exception:
            return 50.0


# ================================================================
# MÓDULO 8: PREDIÇÃO DE SUCESSO DE CONTRATAÇÃO (Ref: Felipe Nunes)
# ================================================================

class ContractSuccessPredictor:
    """
    Modelo preditivo de sucesso de contratação.

    Features de input:
        - Métricas de desempenho (normalizadas por posição)
        - Idade do jogador
        - Nível da liga de origem vs destino
        - Minutagem (proxy de regularidade)
        - Tendência de desempenho (slope das métricas ao longo da temporada)

    Modelo: Gradient Boosting Classifier (ou XGBoost se disponível)

    P(sucesso) = f(performance_vector, age, league_gap, minutes_trend)

    Nota: Requer dados históricos de contratações com label de sucesso/fracasso
    para treino supervisionado. Sem esses dados, opera em modo unsupervised
    usando score composto + heurísticas.
    """

    # Tiers de liga refinados (escala 1-10)
    # Fonte: calibração contextual do futebol brasileiro + europeu
    LEAGUE_TIERS = {
        # Brasil
        'Serie A Brasil': 7, 'Serie B Brasil': 5, 'Serie C Brasil': 3,
        'Serie D Brasil': 1.5, 'Brasileirao Sub-20': 2,
        'Paulista A1': 4, 'Paulista A2': 2.5, 'Paulista A3': 1.5,
        'Carioca A1': 4, 'Carioca A2': 2,
        'Gaucho A1': 3.5, 'Mineiro A1': 3.5,
        'Copa do Brasil': 6, 'Copa do Nordeste': 4,
        # Europa top 5
        'Premier League': 10, 'La Liga': 9.5, 'Serie A Italia': 9,
        'Bundesliga': 9, 'Ligue 1': 8,
        # Europa secundárias
        'Championship': 7, 'La Liga 2': 6, 'Serie B Italia': 6,
        '2. Bundesliga': 6, 'Ligue 2': 5.5,
        'Eredivisie': 7, 'Liga Portugal': 7,
        'Liga Portugal 2': 5, 'Belgian Pro League': 6.5,
        'Scottish Premiership': 5.5, 'Super Lig': 6,
        # Américas
        'MLS': 6, 'Liga MX': 6.5,
        'Liga Argentina': 6, 'Superliga Argentina': 6,
        'Liga Colombiana': 4.5, 'Liga Chilena': 4,
        'Liga Uruguaia': 4.5, 'Liga Paraguaia': 3.5,
        # Outros
        'J1 League': 6, 'K League': 5.5,
        'Saudi Pro League': 6, 'Super League China': 4,
    }

    def __init__(self):
        self.model = None
        self._fitted = False

    def fit_supervised(self, X: np.ndarray, y: np.ndarray,
                       feature_names: List[str]) -> 'ContractSuccessPredictor':
        """Treina com dados históricos de contratações."""
        if HAS_XGB:
            self.model = xgb.XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8,
                random_state=42, eval_metric='logloss'
            )
        elif HAS_SKLEARN:
            self.model = GradientBoostingClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                random_state=42
            )
        else:
            raise RuntimeError("scikit-learn ou xgboost necessário")

        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict_success_unsupervised(self, ssp_score: float, age: float,
                                      league_origin: str, league_target: str,
                                      minutes: float,
                                      max_minutes: float = 3000) -> Dict[str, Any]:
        """
        Estima probabilidade de sucesso via modelo heurístico com
        penalização exponencial por gap de liga.

        Equação:
            P_success = σ(w₁·SSP_adj + w₂·age_f + w₃·league_f + w₄·min_f) × ceiling

        Mudanças vs v1:
            - SSP é descontado pelo nível da liga de origem (SSP em Paulista A2 ≠ SSP em Serie A)
            - League factor usa penalização exponencial por gap (não linear)
            - Hard ceiling para gaps extremos (>5 tiers)
            - Pesos redistribuídos: liga tem 30% de influência

        Gap penalty:
            gap = tier_target - tier_origin
            league_factor = exp(-0.35 * gap)  se gap > 0 (subindo de liga)
            league_factor = 1.0               se gap <= 0 (descendo ou lateral)

        Hard ceiling:
            Se gap >= 6: prob capped em 15%
            Se gap >= 4: prob capped em 35%
        """
        tier_origin = self.LEAGUE_TIERS.get(league_origin, 5)
        tier_target = self.LEAGUE_TIERS.get(league_target, 5)
        gap = tier_target - tier_origin

        # 1. SSP ajustado pelo contexto da liga de origem
        # Desconta o SSP se a liga de origem é fraca (inflar estatísticas em ligas fracas)
        # Liga tier 10 → desconto 0%. Liga tier 2.5 → desconto ~30%.
        league_discount = min(tier_origin / 10.0, 1.0)
        ssp_adj = (ssp_score / 100.0) * (0.7 + 0.3 * league_discount)

        # 2. Age factor (peak = 26, decay quadrático)
        age_factor = max(0, 1 - ((age - 26) ** 2) / (15 ** 2))

        # 3. League factor — exponencial para gaps positivos
        if gap <= 0:
            # Descendo ou lateral: sem penalização
            league_factor = 1.0
        else:
            # Subindo: penalização exponencial
            # gap=1 → 0.70, gap=2 → 0.50, gap=3 → 0.35,
            # gap=4 → 0.25, gap=5 → 0.17, gap=7 → 0.09
            league_factor = np.exp(-0.35 * gap)

        # 4. Minutes factor (regularidade)
        minutes_factor = min(minutes / max_minutes, 1.0)

        # Composite — liga tem peso dominante quando há gap grande
        z = (
            0.30 * ssp_adj +
            0.15 * age_factor +
            0.35 * league_factor +
            0.20 * minutes_factor
        )

        # Sigmoid com amplificação
        z_scaled = (z - 0.5) * 8
        prob = 1.0 / (1.0 + np.exp(-z_scaled))

        # Hard ceiling para gaps extremos
        if gap >= 6:
            prob = min(prob, 0.15)
        elif gap >= 5:
            prob = min(prob, 0.25)
        elif gap >= 4:
            prob = min(prob, 0.35)

        # Risk classification com thresholds ajustados
        if prob >= 0.65:
            risk = 'baixo'
        elif prob >= 0.40:
            risk = 'medio'
        elif prob >= 0.20:
            risk = 'alto'
        else:
            risk = 'muito alto'

        return {
            'success_probability': round(float(prob), 3),
            'ssp_contribution': round(ssp_adj, 3),
            'age_factor': round(age_factor, 3),
            'league_factor': round(league_factor, 3),
            'minutes_factor': round(minutes_factor, 3),
            'league_gap': round(gap, 1),
            'league_discount': round(league_discount, 3),
            'tier_origin': tier_origin,
            'tier_target': tier_target,
            'risk_level': risk,
        }


# ================================================================
# HELPERS
# ================================================================

def _z_score(value: float, df: pd.DataFrame, col: str) -> float:
    """Z-score de um valor em relação à distribuição da coluna."""
    series = pd.to_numeric(df[col], errors='coerce').dropna()
    if len(series) < 2:
        return 0.0
    mean = series.mean()
    std = series.std()
    if std == 0:
        return 0.0
    return (value - mean) / std


# ================================================================
# BACKWARD COMPATIBILITY — Drop-in replacements para similarity.py
# ================================================================

# Re-exportar constantes
# Re-exportar constantes legadas
from similarity import POSITION_WEIGHTS as _LEGACY_WEIGHTS

# Importar coeficientes calibrados (se disponível)
try:
    from calibration import (
        get_calibrated_wp_weights,
        get_calibrated_rating_weights,
        get_negative_impact_features,
        WP_COEFFICIENTS as _CALIBRATED_WP,
        NUNES_MODEL_RESULTS,
        BUSO_XG_MODEL,
        BUSO_XGOT_MODEL,
        SSP_LAMBDAS as _CALIBRATED_LAMBDAS,
        classify_performance,
    )
    HAS_CALIBRATION = True
except ImportError:
    HAS_CALIBRATION = False

def calculate_overall_score_v3(player_row, position, df_all,
                                 ssp_engine: Optional[ScoutScorePreditivo] = None):
    """
    Drop-in replacement para calculate_overall_score().
    Se ssp_engine fornecido, usa score preditivo. Senão, fallback para v2.
    """
    if ssp_engine is not None and ssp_engine._fitted:
        result = ssp_engine.score_player(player_row, df_all)
        return result.get('ssp')
    # Fallback legacy
    from similarity import calculate_overall_score
    return calculate_overall_score(player_row, position, df_all)


def compute_advanced_similarity(target_player, comparison_pool, position,
                                 top_n=20, min_minutes=500,
                                 minutes_col='Minutos jogados:',
                                 player_display_col='JogadorDisplay',
                                 percentile_base=None):
    """
    Drop-in replacement para compute_weighted_cosine_similarity().
    Usa Mahalanobis + RF proximity quando sklearn disponível.
    Fallback para cosseno ponderado original caso contrário.
    """
    if not HAS_SKLEARN:
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(
            target_player, comparison_pool, position,
            top_n, min_minutes, minutes_col, player_display_col, percentile_base
        )

    preprocessor = DataPreprocessor()
    features = preprocessor.get_available_features(comparison_pool, position)
    if len(features) < 5:
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(
            target_player, comparison_pool, position,
            top_n, min_minutes, minutes_col, player_display_col, percentile_base
        )

    try:
        df_filtered, X_scaled, available = preprocessor.prepare_matrix(
            comparison_pool, features, min_minutes, minutes_col
        )
    except (ValueError, Exception):
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(
            target_player, comparison_pool, position,
            top_n, min_minutes, minutes_col, player_display_col, percentile_base
        )

    if player_display_col in df_filtered.columns and player_display_col in target_player.index:
        mask = df_filtered[player_display_col] != target_player[player_display_col]
        df_filtered = df_filtered[mask]
        X_scaled = X_scaled[mask.values]

    if len(df_filtered) < 5:
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(
            target_player, comparison_pool, position,
            top_n, min_minutes, minutes_col, player_display_col, percentile_base
        )

    # Preparar vetor do target
    target_vals = []
    for f in available:
        resolved = preprocessor.resolve_metric(f, target_player.index)
        if resolved:
            v = preprocessor.safe_float(target_player[resolved])
            target_vals.append(v if not np.isnan(v) else 0.0)
        else:
            target_vals.append(0.0)

    target_vec = np.array(target_vals).reshape(1, -1)
    target_scaled = preprocessor.scaler.transform(
        preprocessor.imputer.transform(target_vec)
    )

    # Similarity engine
    sim_engine = AdvancedSimilarity()
    sim_engine.fit(X_scaled)

    # Opcional: clusterer
    clusterer = None
    if len(df_filtered) >= 15:
        try:
            clusterer = TacticalClusterer()
            clusterer.fit(X_scaled, available)
        except Exception:
            clusterer = None

    results = sim_engine.compute_similarity(
        target_scaled[0], clusterer=clusterer, top_n=top_n
    )

    # Montar DataFrame de saída compatível
    if not results:
        return pd.DataFrame()

    indices = [r['pool_index'] for r in results]
    out = df_filtered.iloc[indices].copy()
    out['similarity_pct'] = [r['similarity_pct'] for r in results]
    out['matched_metrics'] = len(available)
    out['mahalanobis_sim'] = [r['mahalanobis_component'] for r in results]
    out['rf_proximity'] = [r['rf_proximity_component'] for r in results]

    return out.sort_values('similarity_pct', ascending=False)    name: str
    offensive_features: List[str] = field(default_factory=list)
    defensive_features: List[str] = field(default_factory=list)
    passing_features: List[str] = field(default_factory=list)
    physical_features: List[str] = field(default_factory=list)
    efficiency_features: List[str] = field(default_factory=list)
    domain_weights: Dict[str, float] = field(default_factory=dict)


# Taxonomia de features por domínio funcional (base: Eduardo Baptista / PIBITI)
POSITION_PROFILES = {
    'Atacante': PositionProfile(
        name='Atacante',
        offensive_features=[
            'Golos/90', 'Golos esperados/90', 'Golos sem ser por penalti/90',
            'Remates/90', 'Remates a baliza, %', 'Golos marcados, %',
            'Toques na area/90', 'Golos de cabeca/90',
        ],
        defensive_features=[
            'Acoes defensivas com exito/90',
        ],
        passing_features=[
            'Assistencias/90', 'Assistencias esperadas/90',
            'Passes chave/90', 'Segundas assistencias/90',
            'Passes recebidos/90', 'Recesao de passes em profundidade/90',
        ],
        physical_features=[
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
            'Aceleracoes/90', 'Corridas progressivas/90',
        ],
        efficiency_features=[
            'Golos/90', 'Golos esperados/90', 'Remates a baliza, %',
            'Golos marcados, %',
        ],
        domain_weights={
            'offensive': 0.40, 'passing': 0.20,
            'physical': 0.20, 'defensive': 0.05, 'efficiency': 0.15,
        },
    ),
    'Extremo': PositionProfile(
        name='Extremo',
        offensive_features=[
            'Golos/90', 'Golos esperados/90', 'Remates/90',
            'Toques na area/90',
        ],
        defensive_features=[
            'Acoes defensivas com exito/90',
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
        ],
        passing_features=[
            'Assistencias/90', 'Assistencias esperadas/90',
            'Passes chave/90', 'Passes inteligentes/90',
            'Passes para a area de penalti/90',
            'Cruzamentos/90', 'Cruzamentos certos, %',
        ],
        physical_features=[
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Aceleracoes/90', 'Corridas progressivas/90',
        ],
        efficiency_features=[
            'Dribles com sucesso, %', 'Cruzamentos certos, %',
            'Passes chave/90',
        ],
        domain_weights={
            'offensive': 0.25, 'passing': 0.30,
            'physical': 0.25, 'defensive': 0.05, 'efficiency': 0.15,
        },
    ),
    'Meia': PositionProfile(
        name='Meia',
        offensive_features=[
            'Golos/90', 'Golos esperados/90', 'Remates/90',
            'Toques na area/90',
        ],
        defensive_features=[
            'Acoes defensivas com exito/90',
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Intersecoes/90',
        ],
        passing_features=[
            'Assistencias/90', 'Assistencias esperadas/90',
            'Passes chave/90', 'Passes inteligentes/90',
            'Passes inteligentes certos, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terco final/90',
            'Passes em profundidade/90', 'Passes em profundidade certos, %',
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
        ],
        physical_features=[
            'Dribles/90', 'Dribles com sucesso, %',
            'Corridas progressivas/90',
        ],
        efficiency_features=[
            'Passes certos, %', 'Passes inteligentes certos, %',
            'Passes progressivos certos, %',
        ],
        domain_weights={
            'offensive': 0.15, 'passing': 0.40,
            'physical': 0.10, 'defensive': 0.15, 'efficiency': 0.20,
        },
    ),
    'Volante': PositionProfile(
        name='Volante',
        offensive_features=[
            'Passes progressivos/90', 'Corridas progressivas/90',
            'Passes em profundidade/90',
        ],
        defensive_features=[
            'Acoes defensivas com exito/90', 'Intersecoes/90',
            'Intercecoes ajust. a posse',
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Cortes/90', 'Cortes de carrinho ajust. a posse',
            'Remates intercetados/90',
        ],
        passing_features=[
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terco final/90',
        ],
        physical_features=[
            'Duelos/90', 'Duelos ganhos, %',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
        ],
        efficiency_features=[
            'Passes certos, %', 'Duelos defensivos ganhos, %',
            'Duelos ganhos, %',
        ],
        domain_weights={
            'offensive': 0.10, 'passing': 0.25,
            'physical': 0.15, 'defensive': 0.35, 'efficiency': 0.15,
        },
    ),
    'Lateral': PositionProfile(
        name='Lateral',
        offensive_features=[
            'Cruzamentos/90', 'Cruzamentos certos, %',
            'Cruzamentos para a area de baliza/90',
            'Toques na area/90', 'Passes para a area de penalti/90',
            'Assistencias/90', 'Assistencias esperadas/90',
        ],
        defensive_features=[
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Intersecoes/90', 'Cortes/90',
            'Acoes defensivas com exito/90', 'Remates intercetados/90',
        ],
        passing_features=[
            'Passes para terco final/90', 'Passes certos para terco final, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes em profundidade/90', 'Passes chave/90',
        ],
        physical_features=[
            'Corridas progressivas/90', 'Aceleracoes/90',
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos/90', 'Duelos ganhos, %',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
        ],
        efficiency_features=[
            'Cruzamentos certos, %', 'Duelos defensivos ganhos, %',
            'Dribles com sucesso, %',
        ],
        domain_weights={
            'offensive': 0.25, 'passing': 0.20,
            'physical': 0.20, 'defensive': 0.25, 'efficiency': 0.10,
        },
    ),
    'Zagueiro': PositionProfile(
        name='Zagueiro',
        offensive_features=[
            'Golos de cabeca/90',
            'Passes progressivos/90', 'Corridas progressivas/90',
        ],
        defensive_features=[
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Cortes/90', 'Cortes de carrinho ajust. a posse',
            'Acoes defensivas com exito/90',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
            'Intersecoes/90', 'Intercecoes ajust. a posse',
            'Remates intercetados/90',
        ],
        passing_features=[
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terco final/90',
        ],
        physical_features=[
            'Duelos/90', 'Duelos ganhos, %',
        ],
        efficiency_features=[
            'Passes certos, %', 'Duelos defensivos ganhos, %',
            'Duelos aereos ganhos, %',
        ],
        domain_weights={
            'offensive': 0.05, 'passing': 0.20,
            'physical': 0.10, 'defensive': 0.50, 'efficiency': 0.15,
        },
    ),
    'Goleiro': PositionProfile(
        name='Goleiro',
        offensive_features=[],
        defensive_features=[
            'Defesas, %', 'Golos sofridos/90',
            'Remates sofridos/90', 'Golos sofridos esperados/90',
            'Golos expectaveis defendidos por 90',
        ],
        passing_features=[
            'Passes longos certos, %',
            'Passes para tras recebidos pelo guarda-redes/90',
        ],
        physical_features=[
            'Duelos aerios/90.1', 'Saidas/90',
        ],
        efficiency_features=[
            'Defesas, %', 'Golos expectaveis defendidos por 90',
        ],
        domain_weights={
            'offensive': 0.0, 'passing': 0.10,
            'physical': 0.10, 'defensive': 0.60, 'efficiency': 0.20,
        },
    ),
}

INVERTED_METRICS = frozenset({
    'Faltas/90', 'Cartoes amarelos/90', 'Cartoes vermelhos/90',
    'Golos sofridos/90', 'Remates sofridos/90', 'Golos sofridos esperados/90',
})


# ================================================================
# MÓDULO 1: PREPROCESSAMENTO
# ================================================================

class DataPreprocessor:
    """Pipeline de limpeza e normalização dos dados Wyscout/SkillCorner."""

    def __init__(self, scaler_type: str = 'robust'):
        self.scaler_type = scaler_type
        self.scaler = None
        self.imputer = SimpleImputer(strategy='median') if HAS_SKLEARN else None
        self._fitted = False

    @staticmethod
    def safe_float(val):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return np.nan
        try:
            if isinstance(val, str):
                val = val.replace(',', '.')
            return float(val)
        except (ValueError, TypeError):
            return np.nan

    def resolve_metric(self, metric: str, columns) -> Optional[str]:
        if metric in columns:
            return metric
        import unicodedata
        def strip_acc(s):
            return ''.join(
                c for c in unicodedata.normalize('NFD', s)
                if unicodedata.category(c) != 'Mn'
            )
        m_stripped = strip_acc(metric)
        for col in columns:
            if strip_acc(col) == m_stripped:
                return col
        return None

    def get_available_features(self, df: pd.DataFrame, position: str) -> List[str]:
        """Resolve quais features do perfil existem no DataFrame."""
        profile = POSITION_PROFILES.get(position)
        if not profile:
            return []
        all_features = set()
        for domain in ['offensive', 'defensive', 'passing', 'physical', 'efficiency']:
            features = getattr(profile, f'{domain}_features', [])
            all_features.update(features)
        resolved = []
        for f in all_features:
            r = self.resolve_metric(f, df.columns)
            if r is not None:
                resolved.append(r)
        return sorted(set(resolved))

    def prepare_matrix(self, df: pd.DataFrame, features: List[str],
                       min_minutes: int = 500,
                       minutes_col: str = 'Minutos jogados:') -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Retorna (df_filtrado, X_scaled).
        Filtra por minutos mínimos, imputa NaNs, escala.
        """
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário para prepare_matrix")

        df_work = df.copy()
        df_work[minutes_col] = df_work[minutes_col].apply(self.safe_float)
        df_work = df_work[df_work[minutes_col] >= min_minutes].copy()

        available = [f for f in features if f in df_work.columns]
        if len(available) < 3:
            raise ValueError(f"Features insuficientes: {len(available)} < 3")

        for col in available:
            df_work[col] = df_work[col].apply(self.safe_float)

        X_raw = df_work[available].values
        X_imputed = self.imputer.fit_transform(X_raw)

        if self.scaler_type == 'robust':
            self.scaler = RobustScaler()
        else:
            self.scaler = StandardScaler()

        X_scaled = self.scaler.fit_transform(X_imputed)
        self._fitted = True

        # Inverter métricas negativas
        for i, col in enumerate(available):
            if col in INVERTED_METRICS or self._is_inverted(col):
                X_scaled[:, i] *= -1

        df_out = df_work.copy()
        return df_out, X_scaled, available

    @staticmethod
    def _is_inverted(metric_name: str) -> bool:
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

    def percentile_rank(self, value: float, series: pd.Series) -> float:
        valid = pd.to_numeric(series, errors='coerce').dropna()
        if len(valid) == 0:
            return 50.0
        return float((valid < value).sum() / len(valid) * 100)


# ================================================================
# MÓDULO 2: FEATURE SELECTION (Ref: Eduardo Baptista / PIBITI)
# ================================================================

class PositionFeatureSelector:
    """
    Seleção de features por posição usando:
    1. Mutual Information para ranking de relevância
    2. PCA para redução de dimensionalidade
    3. Variância explicada acumulada como critério de corte

    Equação do score de relevância:
        relevance_i = α * MI(x_i, y) + β * |loading_i^PC1| + γ * domain_weight_i

    onde:
        α = 0.4 (peso da mutual information)
        β = 0.3 (peso do loading no PC1)
        γ = 0.3 (peso do domínio funcional da posição)
    """

    ALPHA = 0.4  # MI weight
    BETA = 0.3   # PCA loading weight
    GAMMA = 0.3  # Domain weight

    def __init__(self, n_components: float = 0.90):
        """n_components: variância explicada acumulada alvo para PCA."""
        self.n_components = n_components
        self.pca = None
        self.mi_scores = None
        self.feature_relevance = None

    def fit(self, X: np.ndarray, features: List[str], position: str,
            y: Optional[np.ndarray] = None) -> 'PositionFeatureSelector':
        """
        Calcula relevância de cada feature.
        y: target opcional (ex: score global, resultado de jogo). Se None, usa PCA unsupervised.
        """
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        n_samples, n_features = X.shape
        profile = POSITION_PROFILES.get(position)
        if not profile:
            raise ValueError(f"Posição desconhecida: {position}")

        # 1. PCA
        max_components = min(n_samples, n_features)
        self.pca = PCA(n_components=min(self.n_components, max_components))
        self.pca.fit(X)

        # Loading absoluto no PC1 (normalizado)
        if self.pca.components_.shape[0] > 0:
            pc1_loadings = np.abs(self.pca.components_[0])
            pc1_norm = pc1_loadings / (pc1_loadings.max() + 1e-10)
        else:
            pc1_norm = np.ones(n_features) / n_features

        # 2. Mutual Information
        if y is not None and len(np.unique(y)) > 1:
            if np.issubdtype(y.dtype, np.integer) or len(np.unique(y)) < 10:
                mi = mutual_info_classif(X, y, random_state=42)
            else:
                mi = mutual_info_regression(X, y, random_state=42)
            mi_norm = mi / (mi.max() + 1e-10)
        else:
            # Sem target: usar variância como proxy
            variances = np.var(X, axis=0)
            mi_norm = variances / (variances.max() + 1e-10)

        self.mi_scores = mi_norm

        # 3. Domain weights
        domain_scores = np.zeros(n_features)
        for i, feat in enumerate(features):
            domain_scores[i] = self._get_domain_weight(feat, profile)

        # Composite relevance score
        self.feature_relevance = (
            self.ALPHA * mi_norm +
            self.BETA * pc1_norm +
            self.GAMMA * domain_scores
        )

        return self

    def select(self, features: List[str], top_k: int = 15) -> List[Tuple[str, float]]:
        """Retorna top_k features ordenadas por relevância."""
        if self.feature_relevance is None:
            raise RuntimeError("Chame .fit() primeiro")
        indices = np.argsort(self.feature_relevance)[::-1][:top_k]
        return [(features[i], float(self.feature_relevance[i])) for i in indices]

    def get_weights_dict(self, features: List[str], top_k: int = 20) -> Dict[str, float]:
        """Retorna dict {feature: peso_normalizado} para integração com score."""
        selected = self.select(features, top_k)
        total = sum(s for _, s in selected)
        if total == 0:
            return {f: 1.0 / len(selected) for f, _ in selected}
        return {f: s / total for f, s in selected}

    @staticmethod
    def _get_domain_weight(feature: str, profile: PositionProfile) -> float:
        """Retorna o peso do domínio funcional a que a feature pertence."""
        for domain in ['offensive', 'defensive', 'passing', 'physical', 'efficiency']:
            domain_features = getattr(profile, f'{domain}_features', [])
            if feature in domain_features:
                return profile.domain_weights.get(domain, 0.1)
        return 0.05  # feature não mapeada


# ================================================================
# MÓDULO 3: WIN-PROBABILITY MODEL (Ref: Victor Schimidt TCC)
# ================================================================

class WinProbabilityModel:
    """
    Regressão Logística para identificar ações com significância
    estatística na probabilidade de vitória.

    Modelo:
        P(win) = σ(β₀ + Σ βᵢ·xᵢ)

    onde:
        σ = função sigmoide
        βᵢ = coeficiente da feature i
        xᵢ = valor padronizado da feature i

    Os coeficientes βᵢ com p-value < 0.05 são usados como pesos
    na nota do atleta (quanto maior |βᵢ|, mais a ação impacta vitória).
    """

    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level
        self.model = None
        self.coefficients = None
        self.p_values = None
        self.significant_features = None
        self._feature_names = None

    def fit(self, X: np.ndarray, y: np.ndarray,
            feature_names: List[str]) -> 'WinProbabilityModel':
        """
        Treina o modelo de win-probability.
        X: matriz de features padronizadas
        y: vetor binário (1=vitória, 0=não-vitória)
        """
        self._feature_names = feature_names

        if HAS_STATSMODELS:
            # Statsmodels para p-values
            X_const = sm.add_constant(X)
            try:
                logit_model = sm.Logit(y, X_const).fit(
                    disp=0, maxiter=200, method='bfgs'
                )
                self.coefficients = logit_model.params[1:]  # exclui constante
                self.p_values = logit_model.pvalues[1:]
            except Exception:
                # Fallback para sklearn se statsmodels falhar na convergência
                self._fit_sklearn(X, y)
        else:
            self._fit_sklearn(X, y)

        # Filtrar features significativas
        if self.p_values is not None:
            mask = self.p_values < self.significance_level
            self.significant_features = {
                feature_names[i]: {
                    'coefficient': float(self.coefficients[i]),
                    'p_value': float(self.p_values[i]),
                    'abs_impact': float(np.abs(self.coefficients[i])),
                }
                for i in range(len(feature_names)) if mask[i]
            }
        else:
            # Sem p-values, usar magnitude do coeficiente
            median_coef = np.median(np.abs(self.coefficients))
            self.significant_features = {
                feature_names[i]: {
                    'coefficient': float(self.coefficients[i]),
                    'p_value': None,
                    'abs_impact': float(np.abs(self.coefficients[i])),
                }
                for i in range(len(feature_names))
                if np.abs(self.coefficients[i]) > median_coef
            }

        return self

    def _fit_sklearn(self, X: np.ndarray, y: np.ndarray):
        """Fallback com sklearn LogisticRegression."""
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")
        self.model = LogisticRegression(
            penalty='l2', C=1.0, max_iter=500, random_state=42
        )
        self.model.fit(X, y)
        self.coefficients = self.model.coef_[0]
        self.p_values = None

    def get_wp_weights(self, normalize: bool = True) -> Dict[str, float]:
        """
        Retorna pesos baseados nos coeficientes significativos.
        Pesos são |βᵢ| normalizados.
        """
        if not self.significant_features:
            return {}
        weights = {
            f: info['abs_impact']
            for f, info in self.significant_features.items()
        }
        if normalize:
            total = sum(weights.values())
            if total > 0:
                weights = {f: w / total for f, w in weights.items()}
        return weights

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Probabilidade de vitória para cada observação."""
        if self.model is not None:
            return self.model.predict_proba(X)[:, 1]
        elif self.coefficients is not None:
            # Manual sigmoid
            z = X @ self.coefficients
            return 1.0 / (1.0 + np.exp(-z))
        raise RuntimeError("Modelo não treinado")

    def get_coefficient_matrix(self) -> pd.DataFrame:
        """Retorna DataFrame formatado com coeficientes e significância."""
        if self._feature_names is None or self.coefficients is None:
            return pd.DataFrame()
        rows = []
        for i, feat in enumerate(self._feature_names):
            rows.append({
                'Feature': feat,
                'Coeficiente_β': round(float(self.coefficients[i]), 4),
                'p_value': round(float(self.p_values[i]), 4) if self.p_values is not None else None,
                '|Impacto|': round(float(np.abs(self.coefficients[i])), 4),
                'Significativo': (
                    self.p_values[i] < self.significance_level
                    if self.p_values is not None
                    else np.abs(self.coefficients[i]) > np.median(np.abs(self.coefficients))
                ),
            })
        return pd.DataFrame(rows).sort_values('|Impacto|', ascending=False)


# ================================================================
# MÓDULO 4: xG RESIDUAL MODEL (Ref: Gabriel Buso TCC)
# ================================================================

class xGResidualModel:
    """
    Avaliação de eficiência ofensiva/defensiva via resíduos xG.

    Atacantes/Extremos:
        xG_overperformance = (Gols_reais - xG) / max(xG, 0.01)
        shot_quality = xGOT / max(Remates, 1)

    Goleiros:
        goals_prevented = xGA - Gols_sofridos_reais
        save_efficiency = Defesas% - xSave%_estimado

    Equação do score de eficiência:
        E_atk = 0.5 * z(xG_overperf) + 0.3 * z(shot_quality) + 0.2 * z(conversion_rate)
        E_gk  = 0.6 * z(goals_prevented) + 0.4 * z(save_efficiency)
    """

    # Mapeamento de colunas Wyscout (português)
    COL_MAP = {
        'goals': 'Golos/90',
        'xg': 'Golos esperados/90',
        'npg': 'Golos sem ser por penalti/90',
        'shots': 'Remates/90',
        'shots_on_target_pct': 'Remates a baliza, %',
        'conversion_rate': 'Golos marcados, %',
        'xga': 'Golos sofridos esperados/90',
        'goals_conceded': 'Golos sofridos/90',
        'save_pct': 'Defesas, %',
        'xg_prevented': 'Golos expectaveis defendidos por 90',
    }

    @classmethod
    def calculate_attacker_efficiency(cls, player_row, df_all,
                                       preprocessor: DataPreprocessor) -> Dict[str, float]:
        """Calcula score de eficiência ofensiva."""
        goals = preprocessor.safe_float(player_row.get(cls.COL_MAP['goals'], np.nan))
        xg = preprocessor.safe_float(player_row.get(cls.COL_MAP['xg'], np.nan))
        shots = preprocessor.safe_float(player_row.get(cls.COL_MAP['shots'], np.nan))
        sot_pct = preprocessor.safe_float(player_row.get(cls.COL_MAP['shots_on_target_pct'], np.nan))
        conv = preprocessor.safe_float(player_row.get(cls.COL_MAP['conversion_rate'], np.nan))

        result = {}

        # xG overperformance
        if not np.isnan(goals) and not np.isnan(xg) and xg > 0:
            result['xg_overperformance'] = (goals - xg) / max(xg, 0.01)
        else:
            result['xg_overperformance'] = 0.0

        # Shot quality (SOT% como proxy de xGOT quando não disponível)
        if not np.isnan(sot_pct):
            col = cls.COL_MAP['shots_on_target_pct']
            result['shot_quality_z'] = _z_score(sot_pct, df_all, col)
        else:
            result['shot_quality_z'] = 0.0

        # Conversion rate z-score
        if not np.isnan(conv):
            col = cls.COL_MAP['conversion_rate']
            result['conversion_z'] = _z_score(conv, df_all, col)
        else:
            result['conversion_z'] = 0.0

        # xG overperformance z-score
        xg_col = cls.COL_MAP['xg']
        goals_col = cls.COL_MAP['goals']
        if xg_col in df_all.columns and goals_col in df_all.columns:
            xg_series = pd.to_numeric(df_all[xg_col], errors='coerce')
            goals_series = pd.to_numeric(df_all[goals_col], errors='coerce')
            diff_series = goals_series - xg_series
            valid = diff_series.dropna()
            if len(valid) > 1:
                overperf_raw = goals - xg if not np.isnan(goals) and not np.isnan(xg) else 0.0
                result['xg_overperf_z'] = (overperf_raw - valid.mean()) / (valid.std() + 1e-10)
            else:
                result['xg_overperf_z'] = 0.0
        else:
            result['xg_overperf_z'] = 0.0

        # Score composto
        result['efficiency_score'] = (
            0.50 * result['xg_overperf_z'] +
            0.30 * result['shot_quality_z'] +
            0.20 * result['conversion_z']
        )
        return result

    @classmethod
    def calculate_goalkeeper_efficiency(cls, player_row, df_all,
                                         preprocessor: DataPreprocessor) -> Dict[str, float]:
        """Calcula score de eficiência de goleiro (gols prevenidos)."""
        xga = preprocessor.safe_float(player_row.get(cls.COL_MAP['xga'], np.nan))
        gc = preprocessor.safe_float(player_row.get(cls.COL_MAP['goals_conceded'], np.nan))
        save_pct = preprocessor.safe_float(player_row.get(cls.COL_MAP['save_pct'], np.nan))
        xg_prev = preprocessor.safe_float(player_row.get(cls.COL_MAP['xg_prevented'], np.nan))

        result = {}

        # Goals prevented (positivo = bom)
        if not np.isnan(xga) and not np.isnan(gc):
            result['goals_prevented_per90'] = xga - gc
        elif not np.isnan(xg_prev):
            result['goals_prevented_per90'] = xg_prev
        else:
            result['goals_prevented_per90'] = 0.0

        # Save efficiency z-score
        if not np.isnan(save_pct):
            col = cls.COL_MAP['save_pct']
            result['save_efficiency_z'] = _z_score(save_pct, df_all, col)
        else:
            result['save_efficiency_z'] = 0.0

        # Goals prevented z-score
        xg_prev_col = cls.COL_MAP['xg_prevented']
        if xg_prev_col in df_all.columns:
            result['gp_z'] = _z_score(
                result['goals_prevented_per90'], df_all, xg_prev_col
            )
        else:
            result['gp_z'] = 0.0

        result['efficiency_score'] = (
            0.60 * result['gp_z'] +
            0.40 * result['save_efficiency_z']
        )
        return result


# ================================================================
# MÓDULO 5: CLUSTERIZAÇÃO TÁTICA (Ref: Frederico Ferra / Tiago Pinto)
# ================================================================

class TacticalClusterer:
    """
    Clusterização multivariada para identificação de perfis táticos.

    Pipeline:
        1. PCA para redução (80-90% variância explicada)
        2. K-Means com silhouette optimization para k ∈ [3, 8]
        3. Gaussian Mixture Model para probabilidades de pertencimento
        4. Random Forest para interpretabilidade dos clusters

    Output: cluster labels + probabilidades + feature importance por cluster
    """

    def __init__(self, k_range: Tuple[int, int] = (3, 8),
                 pca_variance: float = 0.85):
        self.k_range = k_range
        self.pca_variance = pca_variance
        self.pca = None
        self.kmeans = None
        self.gmm = None
        self.rf_interpreter = None
        self.optimal_k = None
        self.cluster_profiles = None

    def fit(self, X: np.ndarray, feature_names: List[str]) -> 'TacticalClusterer':
        """Treina pipeline completo de clusterização."""
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        n_samples = X.shape[0]
        if n_samples < 10:
            raise ValueError(f"Amostra insuficiente para clustering: {n_samples}")

        # PCA
        max_comp = min(n_samples, X.shape[1])
        self.pca = PCA(n_components=min(self.pca_variance, max_comp))
        X_pca = self.pca.fit_transform(X)

        # K-Means com silhouette optimization
        k_min, k_max = self.k_range
        k_max = min(k_max, n_samples - 1)
        if k_min >= k_max:
            k_min = max(2, k_max - 1)

        best_score = -1
        best_k = k_min

        for k in range(k_min, k_max + 1):
            km = KMeans(n_clusters=k, n_init=10, random_state=42)
            labels = km.fit_predict(X_pca)
            if len(set(labels)) < 2:
                continue
            score = silhouette_score(X_pca, labels)
            if score > best_score:
                best_score = score
                best_k = k

        self.optimal_k = best_k
        self.kmeans = KMeans(n_clusters=best_k, n_init=20, random_state=42)
        labels = self.kmeans.fit_predict(X_pca)

        # GMM com mesmo k para probabilidades soft
        self.gmm = GaussianMixture(
            n_components=best_k, covariance_type='full',
            n_init=5, random_state=42
        )
        self.gmm.fit(X_pca)

        # Random Forest para interpretabilidade
        self.rf_interpreter = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )
        self.rf_interpreter.fit(X, labels)

        # Perfis dos clusters
        self.cluster_profiles = self._build_profiles(X, labels, feature_names)

        return self

    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        """Prediz cluster e probabilidades para novas observações."""
        X_pca = self.pca.transform(X)
        labels = self.kmeans.predict(X_pca)
        probas = self.gmm.predict_proba(X_pca)
        return {
            'labels': labels,
            'probabilities': probas,
            'dominant_cluster': labels,
        }

    def get_cluster_fit_score(self, X_single: np.ndarray) -> float:
        """
        Score de aderência ao cluster (0-1).
        Quanto maior a probabilidade do cluster dominante, melhor o fit.
        """
        X_pca = self.pca.transform(X_single.reshape(1, -1))
        probas = self.gmm.predict_proba(X_pca)[0]
        return float(np.max(probas))

    def get_feature_importance(self) -> Dict[str, float]:
        """Feature importance do RF interpreter."""
        if self.rf_interpreter is None:
            return {}
        return dict(zip(
            range(self.rf_interpreter.n_features_in_),
            self.rf_interpreter.feature_importances_
        ))

    def _build_profiles(self, X: np.ndarray, labels: np.ndarray,
                        features: List[str]) -> Dict[int, Dict]:
        """Constrói perfil estatístico de cada cluster."""
        profiles = {}
        for k in range(self.optimal_k):
            mask = labels == k
            X_cluster = X[mask]
            if len(X_cluster) == 0:
                continue
            profiles[k] = {
                'size': int(mask.sum()),
                'centroid': {features[i]: float(X_cluster[:, i].mean())
                             for i in range(len(features))},
                'std': {features[i]: float(X_cluster[:, i].std())
                        for i in range(len(features))},
            }
        return profiles


# ================================================================
# MÓDULO 6: SIMILARIDADE AVANÇADA (substitui compute_weighted_cosine_similarity)
# ================================================================

class AdvancedSimilarity:
    """
    Substituição da similaridade cosseno ponderada por:
    1. Distância de Mahalanobis (considera correlações entre features)
    2. Random Forest Proximity (co-ocorrência em folhas)
    3. Peso do cluster como componente

    Score final:
        S = α * (1 - d_mahal_norm) + β * rf_proximity + γ * cluster_fit
        α=0.40, β=0.35, γ=0.25
    """

    ALPHA = 0.40  # Mahalanobis weight
    BETA = 0.35   # RF proximity weight
    GAMMA = 0.25  # Cluster fit weight

    def __init__(self):
        self.rf_model = None
        self.X_pool = None
        self.cov_inv = None

    def fit(self, X_pool: np.ndarray):
        """Prepara a base de comparação."""
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        self.X_pool = X_pool

        # Inversa da covariância para Mahalanobis
        cov = np.cov(X_pool, rowvar=False)
        try:
            self.cov_inv = np.linalg.inv(cov + np.eye(cov.shape[0]) * 1e-6)
        except np.linalg.LinAlgError:
            self.cov_inv = np.eye(cov.shape[0])

        # RF para proximity matrix
        # Treina RF para distinguir cada jogador (self-supervised)
        n = X_pool.shape[0]
        if n > 5:
            # Criar target sintético via clustering rápido
            k = min(max(3, n // 10), 10)
            quick_labels = KMeans(n_clusters=k, n_init=5, random_state=42).fit_predict(X_pool)
            self.rf_model = RandomForestClassifier(
                n_estimators=200, max_depth=None, random_state=42
            )
            self.rf_model.fit(X_pool, quick_labels)

        return self

    def compute_similarity(self, target_vec: np.ndarray, pool_indices: np.ndarray = None,
                           clusterer: Optional[TacticalClusterer] = None,
                           top_n: int = 20) -> List[Dict]:
        """
        Calcula similaridade do target contra o pool.
        Retorna lista ordenada de {index, similarity_pct, components}.
        """
        if self.X_pool is None:
            raise RuntimeError("Chame .fit() primeiro")

        X_pool = self.X_pool
        n_pool = X_pool.shape[0]
        target = target_vec.reshape(1, -1)

        # 1. Mahalanobis distances
        diffs = X_pool - target
        mahal_dists = np.sqrt(np.sum(diffs @ self.cov_inv * diffs, axis=1))
        mahal_max = mahal_dists.max() + 1e-10
        mahal_sim = 1.0 - (mahal_dists / mahal_max)

        # 2. RF Proximity
        if self.rf_model is not None:
            leaves_target = self.rf_model.apply(target)[0]  # shape: (n_trees,)
            leaves_pool = self.rf_model.apply(X_pool)        # shape: (n_pool, n_trees)
            rf_prox = np.mean(leaves_pool == leaves_target, axis=1)
        else:
            rf_prox = np.zeros(n_pool)

        # 3. Cluster fit
        if clusterer is not None:
            target_cluster = clusterer.predict(target)['labels'][0]
            pool_clusters = clusterer.predict(X_pool)['labels']
            cluster_sim = (pool_clusters == target_cluster).astype(float)
        else:
            cluster_sim = np.zeros(n_pool)

        # Composite score
        similarity = (
            self.ALPHA * mahal_sim +
            self.BETA * rf_prox +
            self.GAMMA * cluster_sim
        ) * 100.0

        # Rank
        indices = np.argsort(similarity)[::-1][:top_n]
        results = []
        for idx in indices:
            results.append({
                'pool_index': int(idx),
                'similarity_pct': round(float(similarity[idx]), 1),
                'mahalanobis_component': round(float(mahal_sim[idx] * 100), 1),
                'rf_proximity_component': round(float(rf_prox[idx] * 100), 1),
                'cluster_component': round(float(cluster_sim[idx] * 100), 1),
            })

        return results


# ================================================================
# MÓDULO 7: SCOUT SCORE PREDITIVO (Score Global Integrado)
# ================================================================

class ScoutScorePreditivo:
    """
    Índice global integrado que substitui calculate_overall_score().

    Equação:
        SSP = λ₁·WP_Score + λ₂·Efficiency_Score + λ₃·Cluster_Fit + λ₄·Percentile_Score

    onde:
        λ₁ = 0.30 (contribuição do modelo de win-probability)
        λ₂ = 0.25 (contribuição da eficiência xG-residual)
        λ₃ = 0.15 (aderência ao perfil tático ideal)
        λ₄ = 0.30 (percentil ponderado por feature selection — backward compat)

    Range: 0-100
    """

    LAMBDA_WP = 0.25
    LAMBDA_EFF = 0.25
    LAMBDA_CLUSTER = 0.15
    LAMBDA_PERC = 0.35

    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.feature_selector = None
        self.wp_model = None
        self.clusterer = None
        self.selected_weights = None
        self._fitted = False
        # Usar lambdas calibrados se calibration.py disponível
        if HAS_CALIBRATION:
            self.LAMBDA_WP = _CALIBRATED_LAMBDAS.get('wp', 0.25)
            self.LAMBDA_EFF = _CALIBRATED_LAMBDAS.get('efficiency', 0.25)
            self.LAMBDA_CLUSTER = _CALIBRATED_LAMBDAS.get('cluster', 0.15)
            self.LAMBDA_PERC = _CALIBRATED_LAMBDAS.get('percentile', 0.35)

    def fit(self, df: pd.DataFrame, position: str,
            result_col: Optional[str] = None,
            min_minutes: int = 500,
            minutes_col: str = 'Minutos jogados:') -> 'ScoutScorePreditivo':
        """
        Treina todos os sub-modelos.
        result_col: coluna com resultado do jogo (win/loss) se disponível.
        """
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        features = self.preprocessor.get_available_features(df, position)
        if len(features) < 5:
            raise ValueError(f"Features insuficientes: {len(features)}")

        df_filtered, X_scaled, available = self.preprocessor.prepare_matrix(
            df, features, min_minutes, minutes_col
        )

        # Feature Selection
        self.feature_selector = PositionFeatureSelector()
        y_target = None
        if result_col and result_col in df_filtered.columns:
            y_target = pd.to_numeric(df_filtered[result_col], errors='coerce').fillna(0).values

        self.feature_selector.fit(X_scaled, available, position, y_target)
        self.selected_weights = self.feature_selector.get_weights_dict(available, top_k=15)

        # Win-Probability (se target disponível)
        if y_target is not None and len(np.unique(y_target)) > 1:
            self.wp_model = WinProbabilityModel()
            self.wp_model.fit(X_scaled, (y_target > 0).astype(int), available)

        # Clusterização
        if len(df_filtered) >= 15:
            self.clusterer = TacticalClusterer()
            try:
                self.clusterer.fit(X_scaled, available)
            except Exception:
                self.clusterer = None

        self._fitted = True
        self._position = position
        self._available = available
        self._df_base = df_filtered
        self._X_base = X_scaled

        return self

    def score_player(self, player_row, df_all: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula o Scout Score Preditivo para um jogador.

        Returns:
            {
                'ssp': float (0-100),
                'wp_component': float,
                'efficiency_component': float,
                'cluster_component': float,
                'percentile_component': float,
                'details': {...}
            }
        """
        position = self._position if self._fitted else None
        if position is None:
            return {'ssp': None, 'error': 'Modelo não treinado'}

        # Componente 1: Percentil ponderado (backward compatible)
        perc_score = self._percentile_component(player_row, df_all)

        # Componente 2: Win-Probability
        wp_score = self._wp_component(player_row, df_all)

        # Componente 3: Eficiência xG
        eff_score = self._efficiency_component(player_row, df_all)

        # Componente 4: Cluster fit
        cluster_score = self._cluster_component(player_row, df_all)

        # Composite SSP
        ssp = (
            self.LAMBDA_WP * wp_score +
            self.LAMBDA_EFF * eff_score +
            self.LAMBDA_CLUSTER * cluster_score +
            self.LAMBDA_PERC * perc_score
        )

        return {
            'ssp': round(max(0, min(100, ssp)), 1),
            'wp_component': round(wp_score, 1),
            'efficiency_component': round(eff_score, 1),
            'cluster_component': round(cluster_score, 1),
            'percentile_component': round(perc_score, 1),
            'position': position,
            'classification': classify_performance(max(0, min(100, ssp))) if HAS_CALIBRATION else None,
        }

    def rank_players(self, df_players: pd.DataFrame, df_all: pd.DataFrame,
                     min_minutes: int = 500,
                     minutes_col: str = 'Minutos jogados:') -> pd.DataFrame:
        """Ranking batch de jogadores por SSP."""
        pool = df_players.copy()
        pool[minutes_col] = pool[minutes_col].apply(self.preprocessor.safe_float)
        pool = pool[pool[minutes_col] >= min_minutes]

        scores = []
        for idx, row in pool.iterrows():
            result = self.score_player(row, df_all)
            if result.get('ssp') is not None:
                scores.append({
                    '_idx': idx,
                    'SSP': result['ssp'],
                    'WP': result['wp_component'],
                    'Efficiency': result['efficiency_component'],
                    'Cluster': result['cluster_component'],
                    'Percentile': result['percentile_component'],
                })

        if not scores:
            return pd.DataFrame()

        df_scores = pd.DataFrame(scores).sort_values('SSP', ascending=False)
        out = pool.loc[df_scores['_idx']].copy()
        for col in ['SSP', 'WP', 'Efficiency', 'Cluster', 'Percentile']:
            out[col] = df_scores.set_index('_idx')[col]
        return out.sort_values('SSP', ascending=False)

    # --- Componentes internos ---

    def _percentile_component(self, player_row, df_all) -> float:
        """Percentil ponderado pelos pesos calibrados (PIBITI 2025 quando disponível)."""
        # Priorizar pesos calibrados do PIBITI
        weights = self.selected_weights or {}
        if HAS_CALIBRATION and self._position and not weights:
            weights = get_calibrated_rating_weights(self._position)
        if not weights:
            return 50.0

        weighted_sum = 0.0
        total_weight = 0.0

        for feature, w in weights.items():
            resolved = self.preprocessor.resolve_metric(feature, player_row.index)
            if resolved is None:
                continue
            val = self.preprocessor.safe_float(player_row[resolved])
            if np.isnan(val):
                continue
            perc = self.preprocessor.percentile_rank(val, df_all[resolved])
            if feature in INVERTED_METRICS or self.preprocessor._is_inverted(feature):
                perc = 100.0 - perc
            weighted_sum += perc * w
            total_weight += w

        if total_weight == 0:
            return 50.0
        return weighted_sum / total_weight

    def _wp_component(self, player_row, df_all) -> float:
        """Componente de win-probability (calibrado por Schimidt 2021 quando disponível)."""
        # Tentar usar pesos calibrados (Schimidt)
        if HAS_CALIBRATION and self._position:
            wp_weights = get_calibrated_wp_weights(self._position)
            if wp_weights:
                weighted_sum = 0.0
                total_weight = 0.0
                for feature, w in wp_weights.items():
                    resolved = self.preprocessor.resolve_metric(feature, player_row.index)
                    if resolved is None:
                        continue
                    val = self.preprocessor.safe_float(player_row[resolved])
                    if np.isnan(val):
                        continue
                    perc = self.preprocessor.percentile_rank(val, df_all[resolved])
                    if feature in INVERTED_METRICS:
                        perc = 100.0 - perc
                    weighted_sum += perc * w
                    total_weight += w
                if total_weight > 0:
                    return weighted_sum / total_weight

        if self.wp_model is None or not self.wp_model.significant_features:
            # Fallback: usar percentil das features significativas padrão
            return self._percentile_component(player_row, df_all)

        wp_weights = self.wp_model.get_wp_weights()
        weighted_sum = 0.0
        total_weight = 0.0

        for feature, w in wp_weights.items():
            resolved = self.preprocessor.resolve_metric(feature, player_row.index)
            if resolved is None:
                continue
            val = self.preprocessor.safe_float(player_row[resolved])
            if np.isnan(val):
                continue
            perc = self.preprocessor.percentile_rank(val, df_all[resolved])
            if feature in INVERTED_METRICS:
                perc = 100.0 - perc
            weighted_sum += perc * w
            total_weight += w

        if total_weight == 0:
            return 50.0
        return weighted_sum / total_weight

    def _efficiency_component(self, player_row, df_all) -> float:
        """Componente de eficiência xG."""
        position = self._position
        if position == 'Goleiro':
            eff = xGResidualModel.calculate_goalkeeper_efficiency(
                player_row, df_all, self.preprocessor
            )
        elif position in ('Atacante', 'Extremo', 'Meia'):
            eff = xGResidualModel.calculate_attacker_efficiency(
                player_row, df_all, self.preprocessor
            )
        else:
            return 50.0  # Posições sem modelo xG direto

        raw = eff.get('efficiency_score', 0.0)
        # Converter z-score para escala 0-100 (CDF da normal)
        from scipy.stats import norm
        try:
            return float(norm.cdf(raw) * 100)
        except Exception:
            # Fallback sigmoid
            return float(1.0 / (1.0 + np.exp(-raw)) * 100)

    def _cluster_component(self, player_row, df_all) -> float:
        """Componente de aderência ao cluster tático."""
        if self.clusterer is None:
            return 50.0

        try:
            features = self._available
            vals = []
            for f in features:
                resolved = self.preprocessor.resolve_metric(f, player_row.index)
                if resolved:
                    v = self.preprocessor.safe_float(player_row[resolved])
                    vals.append(v if not np.isnan(v) else 0.0)
                else:
                    vals.append(0.0)

            X_single = np.array(vals).reshape(1, -1)
            if self.preprocessor.scaler is not None:
                X_single = self.preprocessor.scaler.transform(
                    self.preprocessor.imputer.transform(X_single)
                )
            fit_score = self.clusterer.get_cluster_fit_score(X_single[0])
            return fit_score * 100
        except Exception:
            return 50.0


# ================================================================
# MÓDULO 8: PREDIÇÃO DE SUCESSO DE CONTRATAÇÃO (Ref: Felipe Nunes)
# ================================================================

class ContractSuccessPredictor:
    """
    Modelo preditivo de sucesso de contratação.

    Features de input:
        - Métricas de desempenho (normalizadas por posição)
        - Idade do jogador
        - Nível da liga de origem vs destino
        - Minutagem (proxy de regularidade)
        - Tendência de desempenho (slope das métricas ao longo da temporada)

    Modelo: Gradient Boosting Classifier (ou XGBoost se disponível)

    P(sucesso) = f(performance_vector, age, league_gap, minutes_trend)

    Nota: Requer dados históricos de contratações com label de sucesso/fracasso
    para treino supervisionado. Sem esses dados, opera em modo unsupervised
    usando score composto + heurísticas.
    """

    # Heurísticas de nível de liga (escala 1-10)
    LEAGUE_TIERS = {
        'Serie A Brasil': 7, 'Serie B Brasil': 5, 'Serie C Brasil': 3,
        'Serie D Brasil': 2, 'Paulista A1': 4, 'Paulista A2': 3,
        'Premier League': 10, 'La Liga': 9, 'Serie A Italia': 9,
        'Bundesliga': 9, 'Ligue 1': 8, 'Eredivisie': 7,
        'Liga Portugal': 7, 'MLS': 6, 'Liga MX': 6,
        'Championship': 7, 'Liga Argentina': 6,
        'Superliga Argentina': 6,
    }

    def __init__(self):
        self.model = None
        self._fitted = False

    def fit_supervised(self, X: np.ndarray, y: np.ndarray,
                       feature_names: List[str]) -> 'ContractSuccessPredictor':
        """Treina com dados históricos de contratações."""
        if HAS_XGB:
            self.model = xgb.XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8,
                random_state=42, eval_metric='logloss'
            )
        elif HAS_SKLEARN:
            self.model = GradientBoostingClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                random_state=42
            )
        else:
            raise RuntimeError("scikit-learn ou xgboost necessário")

        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict_success_unsupervised(self, ssp_score: float, age: float,
                                      league_origin: str, league_target: str,
                                      minutes: float,
                                      max_minutes: float = 3000) -> Dict[str, Any]:
        """
        Modo unsupervised: estima probabilidade de sucesso via heurísticas.

        Equação:
            P_success = σ(w₁·SSP_norm + w₂·age_factor + w₃·league_factor + w₄·minutes_factor)

        onde:
            SSP_norm = SSP / 100
            age_factor = 1 - |age - 26| / 15 (peak age = 26)
            league_factor = tier_origin / tier_target (adaptabilidade)
            minutes_factor = minutes / max_minutes (regularidade)
        """
        # SSP normalizado
        ssp_norm = ssp_score / 100.0

        # Age factor (peak = 26, decay quadrático)
        age_factor = max(0, 1 - ((age - 26) ** 2) / (15 ** 2))

        # League factor
        tier_origin = self.LEAGUE_TIERS.get(league_origin, 5)
        tier_target = self.LEAGUE_TIERS.get(league_target, 5)
        league_factor = min(tier_origin / max(tier_target, 1), 1.5) / 1.5

        # Minutes factor
        minutes_factor = min(minutes / max_minutes, 1.0)

        # Weighted composite → sigmoid
        z = (
            0.40 * ssp_norm +
            0.20 * age_factor +
            0.20 * league_factor +
            0.20 * minutes_factor
        )
        # Escalar para range razoável antes do sigmoid
        z_scaled = (z - 0.5) * 6  # centra em 0, amplifica
        prob = 1.0 / (1.0 + np.exp(-z_scaled))

        return {
            'success_probability': round(float(prob), 3),
            'ssp_contribution': round(ssp_norm, 3),
            'age_factor': round(age_factor, 3),
            'league_factor': round(league_factor, 3),
            'minutes_factor': round(minutes_factor, 3),
            'risk_level': 'baixo' if prob > 0.65 else 'medio' if prob > 0.40 else 'alto',
        }


# ================================================================
# HELPERS
# ================================================================

def _z_score(value: float, df: pd.DataFrame, col: str) -> float:
    """Z-score de um valor em relação à distribuição da coluna."""
    series = pd.to_numeric(df[col], errors='coerce').dropna()
    if len(series) < 2:
        return 0.0
    mean = series.mean()
    std = series.std()
    if std == 0:
        return 0.0
    return (value - mean) / std


# ================================================================
# BACKWARD COMPATIBILITY — Drop-in replacements para similarity.py
# ================================================================

# Re-exportar constantes
# Re-exportar constantes legadas
from similarity import POSITION_WEIGHTS as _LEGACY_WEIGHTS

# Importar coeficientes calibrados (se disponível)
try:
    from calibration import (
        get_calibrated_wp_weights,
        get_calibrated_rating_weights,
        get_negative_impact_features,
        WP_COEFFICIENTS as _CALIBRATED_WP,
        NUNES_MODEL_RESULTS,
        BUSO_XG_MODEL,
        BUSO_XGOT_MODEL,
        SSP_LAMBDAS as _CALIBRATED_LAMBDAS,
        classify_performance,
    )
    HAS_CALIBRATION = True
except ImportError:
    HAS_CALIBRATION = False

def calculate_overall_score_v3(player_row, position, df_all,
                                 ssp_engine: Optional[ScoutScorePreditivo] = None):
    """
    Drop-in replacement para calculate_overall_score().
    Se ssp_engine fornecido, usa score preditivo. Senão, fallback para v2.
    """
    if ssp_engine is not None and ssp_engine._fitted:
        result = ssp_engine.score_player(player_row, df_all)
        return result.get('ssp')
    # Fallback legacy
    from similarity import calculate_overall_score
    return calculate_overall_score(player_row, position, df_all)


def compute_advanced_similarity(target_player, comparison_pool, position,
                                 top_n=20, min_minutes=500,
                                 minutes_col='Minutos jogados:',
                                 player_display_col='JogadorDisplay',
                                 percentile_base=None):
    """
    Drop-in replacement para compute_weighted_cosine_similarity().
    Usa Mahalanobis + RF proximity quando sklearn disponível.
    Fallback para cosseno ponderado original caso contrário.
    """
    if not HAS_SKLEARN:
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(
            target_player, comparison_pool, position,
            top_n, min_minutes, minutes_col, player_display_col, percentile_base
        )

    preprocessor = DataPreprocessor()
    features = preprocessor.get_available_features(comparison_pool, position)
    if len(features) < 5:
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(
            target_player, comparison_pool, position,
            top_n, min_minutes, minutes_col, player_display_col, percentile_base
        )

    try:
        df_filtered, X_scaled, available = preprocessor.prepare_matrix(
            comparison_pool, features, min_minutes, minutes_col
        )
    except (ValueError, Exception):
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(
            target_player, comparison_pool, position,
            top_n, min_minutes, minutes_col, player_display_col, percentile_base
        )

    if player_display_col in df_filtered.columns and player_display_col in target_player.index:
        mask = df_filtered[player_display_col] != target_player[player_display_col]
        df_filtered = df_filtered[mask]
        X_scaled = X_scaled[mask.values]

    if len(df_filtered) < 5:
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(
            target_player, comparison_pool, position,
            top_n, min_minutes, minutes_col, player_display_col, percentile_base
        )

    # Preparar vetor do target
    target_vals = []
    for f in available:
        resolved = preprocessor.resolve_metric(f, target_player.index)
        if resolved:
            v = preprocessor.safe_float(target_player[resolved])
            target_vals.append(v if not np.isnan(v) else 0.0)
        else:
            target_vals.append(0.0)

    target_vec = np.array(target_vals).reshape(1, -1)
    target_scaled = preprocessor.scaler.transform(
        preprocessor.imputer.transform(target_vec)
    )

    # Similarity engine
    sim_engine = AdvancedSimilarity()
    sim_engine.fit(X_scaled)

    # Opcional: clusterer
    clusterer = None
    if len(df_filtered) >= 15:
        try:
            clusterer = TacticalClusterer()
            clusterer.fit(X_scaled, available)
        except Exception:
            clusterer = None

    results = sim_engine.compute_similarity(
        target_scaled[0], clusterer=clusterer, top_n=top_n
    )

    # Montar DataFrame de saída compatível
    if not results:
        return pd.DataFrame()

    indices = [r['pool_index'] for r in results]
    out = df_filtered.iloc[indices].copy()
    out['similarity_pct'] = [r['similarity_pct'] for r in results]
    out['matched_metrics'] = len(available)
    out['mahalanobis_sim'] = [r['mahalanobis_component'] for r in results]
    out['rf_proximity'] = [r['rf_proximity_component'] for r in results]

    return out.sort_values('similarity_pct', ascending=False)
