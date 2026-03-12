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


POSITION_PROFILES = {
    'Atacante': PositionProfile(
        name='Atacante',
        offensive_features=[
            'Golos/90', 'Golos esperados/90', 'Golos sem ser por penalti/90',
            'Remates/90', 'Remates a baliza, %', 'Golos marcados, %',
            'Toques na area/90', 'Golos de cabeca/90',
        ],
        defensive_features=['Acoes defensivas com exito/90'],
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
        domain_weights={'offensive': 0.40, 'passing': 0.20, 'physical': 0.20, 'defensive': 0.05, 'efficiency': 0.15},
    ),
    'Extremo': PositionProfile(
        name='Extremo',
        offensive_features=['Golos/90', 'Golos esperados/90', 'Remates/90', 'Toques na area/90'],
        defensive_features=['Acoes defensivas com exito/90', 'Duelos defensivos/90', 'Duelos defensivos ganhos, %'],
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
        efficiency_features=['Dribles com sucesso, %', 'Cruzamentos certos, %', 'Passes chave/90'],
        domain_weights={'offensive': 0.25, 'passing': 0.30, 'physical': 0.25, 'defensive': 0.05, 'efficiency': 0.15},
    ),
    'Meia': PositionProfile(
        name='Meia',
        offensive_features=['Golos/90', 'Golos esperados/90', 'Remates/90', 'Toques na area/90'],
        defensive_features=['Acoes defensivas com exito/90', 'Duelos defensivos/90', 'Duelos defensivos ganhos, %', 'Intersecoes/90'],
        passing_features=[
            'Assistencias/90', 'Assistencias esperadas/90',
            'Passes chave/90', 'Passes inteligentes/90', 'Passes inteligentes certos, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terco final/90',
            'Passes em profundidade/90', 'Passes em profundidade certos, %',
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
        ],
        physical_features=['Dribles/90', 'Dribles com sucesso, %', 'Corridas progressivas/90'],
        efficiency_features=['Passes certos, %', 'Passes inteligentes certos, %', 'Passes progressivos certos, %'],
        domain_weights={'offensive': 0.15, 'passing': 0.40, 'physical': 0.10, 'defensive': 0.15, 'efficiency': 0.20},
    ),
    'Volante': PositionProfile(
        name='Volante',
        offensive_features=['Passes progressivos/90', 'Corridas progressivas/90', 'Passes em profundidade/90'],
        defensive_features=[
            'Acoes defensivas com exito/90', 'Intersecoes/90', 'Intercecoes ajust. a posse',
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Cortes/90', 'Cortes de carrinho ajust. a posse', 'Remates intercetados/90',
        ],
        passing_features=[
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terco final/90',
        ],
        physical_features=['Duelos/90', 'Duelos ganhos, %', 'Duelos aerios/90', 'Duelos aereos ganhos, %'],
        efficiency_features=['Passes certos, %', 'Duelos defensivos ganhos, %', 'Duelos ganhos, %'],
        domain_weights={'offensive': 0.10, 'passing': 0.25, 'physical': 0.15, 'defensive': 0.35, 'efficiency': 0.15},
    ),
    'Lateral': PositionProfile(
        name='Lateral',
        offensive_features=[
            'Cruzamentos/90', 'Cruzamentos certos, %', 'Cruzamentos para a area de baliza/90',
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
        efficiency_features=['Cruzamentos certos, %', 'Duelos defensivos ganhos, %', 'Dribles com sucesso, %'],
        domain_weights={'offensive': 0.25, 'passing': 0.20, 'physical': 0.20, 'defensive': 0.25, 'efficiency': 0.10},
    ),
    'Zagueiro': PositionProfile(
        name='Zagueiro',
        offensive_features=['Golos de cabeca/90', 'Passes progressivos/90', 'Corridas progressivas/90'],
        defensive_features=[
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Cortes/90', 'Cortes de carrinho ajust. a posse',
            'Acoes defensivas com exito/90',
            'Duelos aerios/90', 'Duelos aereos ganhos, %',
            'Intersecoes/90', 'Intercecoes ajust. a posse', 'Remates intercetados/90',
        ],
        passing_features=[
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terco final/90',
        ],
        physical_features=['Duelos/90', 'Duelos ganhos, %'],
        efficiency_features=['Passes certos, %', 'Duelos defensivos ganhos, %', 'Duelos aereos ganhos, %'],
        domain_weights={'offensive': 0.05, 'passing': 0.20, 'physical': 0.10, 'defensive': 0.50, 'efficiency': 0.15},
    ),
    'Goleiro': PositionProfile(
        name='Goleiro',
        offensive_features=[],
        defensive_features=[
            'Defesas, %', 'Golos sofridos/90',
            'Remates sofridos/90', 'Golos sofridos esperados/90',
            'Golos expectaveis defendidos por 90',
        ],
        passing_features=['Passes longos certos, %', 'Passes para tras recebidos pelo guarda-redes/90'],
        physical_features=['Duelos aerios/90.1', 'Saidas/90'],
        efficiency_features=['Defesas, %', 'Golos expectaveis defendidos por 90'],
        domain_weights={'offensive': 0.0, 'passing': 0.10, 'physical': 0.10, 'defensive': 0.60, 'efficiency': 0.20},
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

        for i, col in enumerate(available):
            if col in INVERTED_METRICS or self._is_inverted(col):
                X_scaled[:, i] *= -1

        df_out = df_work.copy()
        return df_out, X_scaled, available

    @staticmethod
    def _is_inverted(metric_name: str) -> bool:
        m_lower = metric_name.lower()
        if 'faltas/90' in m_lower and 'sofridas' not in m_lower: return True
        if 'cart' in m_lower and '/90' in m_lower: return True
        if 'sofridos' in m_lower and 'golos' in m_lower: return True
        if 'remates sofridos' in m_lower: return True
        return False

    def percentile_rank(self, value: float, series: pd.Series) -> float:
        valid = pd.to_numeric(series, errors='coerce').dropna()
        if len(valid) == 0: return 50.0
        return float((valid < value).sum() / len(valid) * 100)


# ================================================================
# MÓDULO 2: FEATURE SELECTION
# ================================================================

class PositionFeatureSelector:
    ALPHA = 0.4
    BETA = 0.3
    GAMMA = 0.3

    def __init__(self, n_components: float = 0.90):
        self.n_components = n_components
        self.pca = None
        self.mi_scores = None
        self.feature_relevance = None

    def fit(self, X: np.ndarray, features: List[str], position: str,
            y: Optional[np.ndarray] = None) -> 'PositionFeatureSelector':
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")

        n_samples, n_features = X.shape
        profile = POSITION_PROFILES.get(position)
        if not profile:
            raise ValueError(f"Posição desconhecida: {position}")

        max_components = min(n_samples, n_features)
        self.pca = PCA(n_components=min(self.n_components, max_components))
        self.pca.fit(X)

        if self.pca.components_.shape[0] > 0:
            pc1_loadings = np.abs(self.pca.components_[0])
            pc1_norm = pc1_loadings / (pc1_loadings.max() + 1e-10)
        else:
            pc1_norm = np.ones(n_features) / n_features

        if y is not None and len(np.unique(y)) > 1:
            if np.issubdtype(y.dtype, np.integer) or len(np.unique(y)) < 10:
                mi = mutual_info_classif(X, y, random_state=42)
            else:
                mi = mutual_info_regression(X, y, random_state=42)
            mi_norm = mi / (mi.max() + 1e-10)
        else:
            variances = np.var(X, axis=0)
            mi_norm = variances / (variances.max() + 1e-10)

        self.mi_scores = mi_norm
        domain_scores = np.zeros(n_features)
        for i, feat in enumerate(features):
            domain_scores[i] = self._get_domain_weight(feat, profile)

        self.feature_relevance = (self.ALPHA * mi_norm + self.BETA * pc1_norm + self.GAMMA * domain_scores)
        return self

    def select(self, features: List[str], top_k: int = 15) -> List[Tuple[str, float]]:
        if self.feature_relevance is None:
            raise RuntimeError("Chame .fit() primeiro")
        indices = np.argsort(self.feature_relevance)[::-1][:top_k]
        return [(features[i], float(self.feature_relevance[i])) for i in indices]

    def get_weights_dict(self, features: List[str], top_k: int = 20) -> Dict[str, float]:
        selected = self.select(features, top_k)
        total = sum(s for _, s in selected)
        if total == 0:
            return {f: 1.0 / len(selected) for f, _ in selected}
        return {f: s / total for f, s in selected}

    @staticmethod
    def _get_domain_weight(feature: str, profile: PositionProfile) -> float:
        for domain in ['offensive', 'defensive', 'passing', 'physical', 'efficiency']:
            domain_features = getattr(profile, f'{domain}_features', [])
            if feature in domain_features:
                return profile.domain_weights.get(domain, 0.1)
        return 0.05


# ================================================================
# MÓDULO 3: WIN-PROBABILITY MODEL
# ================================================================

class WinProbabilityModel:
    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level
        self.model = None
        self.coefficients = None
        self.p_values = None
        self.significant_features = None
        self._feature_names = None

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> 'WinProbabilityModel':
        self._feature_names = feature_names

        if HAS_STATSMODELS:
            X_const = sm.add_constant(X)
            try:
                logit_model = sm.Logit(y, X_const).fit(disp=0, maxiter=200, method='bfgs')
                self.coefficients = logit_model.params[1:]
                self.p_values = logit_model.pvalues[1:]
            except Exception:
                self._fit_sklearn(X, y)
        else:
            self._fit_sklearn(X, y)

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
            median_coef = np.median(np.abs(self.coefficients))
            self.significant_features = {
                feature_names[i]: {
                    'coefficient': float(self.coefficients[i]),
                    'p_value': None,
                    'abs_impact': float(np.abs(self.coefficients[i])),
                }
                for i in range(len(feature_names)) if np.abs(self.coefficients[i]) > median_coef
            }
        return self

    def _fit_sklearn(self, X: np.ndarray, y: np.ndarray):
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn necessário")
        self.model = LogisticRegression(penalty='l2', C=1.0, max_iter=500, random_state=42)
        self.model.fit(X, y)
        self.coefficients = self.model.coef_[0]
        self.p_values = None

    def get_wp_weights(self, normalize: bool = True) -> Dict[str, float]:
        if not self.significant_features: return {}
        weights = {f: info['abs_impact'] for f, info in self.significant_features.items()}
        if normalize:
            total = sum(weights.values())
            if total > 0:
                weights = {f: w / total for f, w in weights.items()}
        return weights

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.model is not None:
            return self.model.predict_proba(X)[:, 1]
        elif self.coefficients is not None:
            z = X @ self.coefficients
            return 1.0 / (1.0 + np.exp(-z))
        raise RuntimeError("Modelo não treinado")

    def get_coefficient_matrix(self) -> pd.DataFrame:
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
                    self.p_values[i] < self.significance_level if self.p_values is not None
                    else np.abs(self.coefficients[i]) > np.median(np.abs(self.coefficients))
                ),
            })
        return pd.DataFrame(rows).sort_values('|Impacto|', ascending=False)


# ================================================================
# MÓDULO 4: xG RESIDUAL MODEL
# ================================================================

class xGResidualModel:
    COL_MAP = {
        'goals': 'Golos/90', 'xg': 'Golos esperados/90', 'npg': 'Golos sem ser por penalti/90',
        'shots': 'Remates/90', 'shots_on_target_pct': 'Remates a baliza, %', 'conversion_rate': 'Golos marcados, %',
        'xga': 'Golos sofridos esperados/90', 'goals_conceded': 'Golos sofridos/90',
        'save_pct': 'Defesas, %', 'xg_prevented': 'Golos expectaveis defendidos por 90',
    }

    @classmethod
    def calculate_attacker_efficiency(cls, player_row, df_all, preprocessor: DataPreprocessor) -> Dict[str, float]:
        goals = preprocessor.safe_float(player_row.get(cls.COL_MAP['goals'], np.nan))
        xg = preprocessor.safe_float(player_row.get(cls.COL_MAP['xg'], np.nan))
        sot_pct = preprocessor.safe_float(player_row.get(cls.COL_MAP['shots_on_target_pct'], np.nan))
        conv = preprocessor.safe_float(player_row.get(cls.COL_MAP['conversion_rate'], np.nan))

        result = {}
        if not np.isnan(goals) and not np.isnan(xg) and xg > 0:
            result['xg_overperformance'] = (goals - xg) / max(xg, 0.01)
        else:
            result['xg_overperformance'] = 0.0

        result['shot_quality_z'] = _z_score(sot_pct, df_all, cls.COL_MAP['shots_on_target_pct']) if not np.isnan(sot_pct) else 0.0
        result['conversion_z'] = _z_score(conv, df_all, cls.COL_MAP['conversion_rate']) if not np.isnan(conv) else 0.0

        if cls.COL_MAP['xg'] in df_all.columns and cls.COL_MAP['goals'] in df_all.columns:
            xg_series = pd.to_numeric(df_all[cls.COL_MAP['xg']], errors='coerce')
            goals_series = pd.to_numeric(df_all[cls.COL_MAP['goals']], errors='coerce')
            diff_series = goals_series - xg_series
            valid = diff_series.dropna()
            if len(valid) > 1:
                overperf_raw = goals - xg if not np.isnan(goals) and not np.isnan(xg) else 0.0
                result['xg_overperf_z'] = (overperf_raw - valid.mean()) / (valid.std() + 1e-10)
            else:
                result['xg_overperf_z'] = 0.0
        else:
            result['xg_overperf_z'] = 0.0

        result['efficiency_score'] = 0.50 * result['xg_overperf_z'] + 0.30 * result['shot_quality_z'] + 0.20 * result['conversion_z']
        return result

    @classmethod
    def calculate_goalkeeper_efficiency(cls, player_row, df_all, preprocessor: DataPreprocessor) -> Dict[str, float]:
        xga = preprocessor.safe_float(player_row.get(cls.COL_MAP['xga'], np.nan))
        gc = preprocessor.safe_float(player_row.get(cls.COL_MAP['goals_conceded'], np.nan))
        save_pct = preprocessor.safe_float(player_row.get(cls.COL_MAP['save_pct'], np.nan))
        xg_prev = preprocessor.safe_float(player_row.get(cls.COL_MAP['xg_prevented'], np.nan))

        result = {}
        if not np.isnan(xga) and not np.isnan(gc): result['goals_prevented_per90'] = xga - gc
        elif not np.isnan(xg_prev): result['goals_prevented_per90'] = xg_prev
        else: result['goals_prevented_per90'] = 0.0

        result['save_efficiency_z'] = _z_score(save_pct, df_all, cls.COL_MAP['save_pct']) if not np.isnan(save_pct) else 0.0
        
        if cls.COL_MAP['xg_prevented'] in df_all.columns:
            result['gp_z'] = _z_score(result['goals_prevented_per90'], df_all, cls.COL_MAP['xg_prevented'])
        else:
            result['gp_z'] = 0.0

        result['efficiency_score'] = 0.60 * result['gp_z'] + 0.40 * result['save_efficiency_z']
        return result


# ================================================================
# MÓDULO 5: CLUSTERIZAÇÃO TÁTICA
# ================================================================

class TacticalClusterer:
    def __init__(self, k_range: Tuple[int, int] = (3, 8), pca_variance: float = 0.85):
        self.k_range = k_range
        self.pca_variance = pca_variance
        self.pca = None
        self.kmeans = None
        self.gmm = None
        self.rf_interpreter = None
        self.optimal_k = None
        self.cluster_profiles = None

    def fit(self, X: np.ndarray, feature_names: List[str]) -> 'TacticalClusterer':
        if not HAS_SKLEARN: raise RuntimeError("scikit-learn necessário")
        n_samples = X.shape[0]
        if n_samples < 10: raise ValueError(f"Amostra insuficiente para clustering: {n_samples}")

        self.pca = PCA(n_components=min(self.pca_variance, min(n_samples, X.shape[1])))
        X_pca = self.pca.fit_transform(X)

        k_min, k_max = self.k_range
        k_max = min(k_max, n_samples - 1)
        if k_min >= k_max: k_min = max(2, k_max - 1)

        best_score, best_k = -1, k_min
        for k in range(k_min, k_max + 1):
            labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X_pca)
            if len(set(labels)) < 2: continue
            score = silhouette_score(X_pca, labels)
            if score > best_score:
                best_score, best_k = score, k

        self.optimal_k = best_k
        self.kmeans = KMeans(n_clusters=best_k, n_init=20, random_state=42)
        labels = self.kmeans.fit_predict(X_pca)

        self.gmm = GaussianMixture(n_components=best_k, covariance_type='full', n_init=5, random_state=42)
        self.gmm.fit(X_pca)

        self.rf_interpreter = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        self.rf_interpreter.fit(X, labels)

        self.cluster_profiles = self._build_profiles(X, labels, feature_names)
        return self

    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        X_pca = self.pca.transform(X)
        labels = self.kmeans.predict(X_pca)
        return {'labels': labels, 'probabilities': self.gmm.predict_proba(X_pca), 'dominant_cluster': labels}

    def get_cluster_fit_score(self, X_single: np.ndarray) -> float:
        X_pca = self.pca.transform(X_single.reshape(1, -1))
        return float(np.max(self.gmm.predict_proba(X_pca)[0]))

    def _build_profiles(self, X: np.ndarray, labels: np.ndarray, features: List[str]) -> Dict[int, Dict]:
        profiles = {}
        for k in range(self.optimal_k):
            mask = labels == k
            if len(X[mask]) == 0: continue
            profiles[k] = {
                'size': int(mask.sum()),
                'centroid': {features[i]: float(X[mask][:, i].mean()) for i in range(len(features))},
                'std': {features[i]: float(X[mask][:, i].std()) for i in range(len(features))},
            }
        return profiles


# ================================================================
# MÓDULO 6: SIMILARIDADE AVANÇADA
# ================================================================

class AdvancedSimilarity:
    ALPHA, BETA, GAMMA = 0.40, 0.35, 0.25

    def __init__(self):
        self.rf_model = None
        self.X_pool = None
        self.cov_inv = None

    def fit(self, X_pool: np.ndarray):
        if not HAS_SKLEARN: raise RuntimeError("scikit-learn necessário")
        self.X_pool = X_pool
        cov = np.cov(X_pool, rowvar=False)
        try: self.cov_inv = np.linalg.inv(cov + np.eye(cov.shape[0]) * 1e-6)
        except np.linalg.LinAlgError: self.cov_inv = np.eye(cov.shape[0])

        if X_pool.shape[0] > 5:
            k = min(max(3, X_pool.shape[0] // 10), 10)
            quick_labels = KMeans(n_clusters=k, n_init=5, random_state=42).fit_predict(X_pool)
            self.rf_model = RandomForestClassifier(n_estimators=200, max_depth=None, random_state=42)
            self.rf_model.fit(X_pool, quick_labels)
        return self

    def compute_similarity(self, target_vec: np.ndarray, pool_indices: np.ndarray = None,
                           clusterer: Optional[TacticalClusterer] = None, top_n: int = 20) -> List[Dict]:
        if self.X_pool is None: raise RuntimeError("Chame .fit() primeiro")
        target = target_vec.reshape(1, -1)
        diffs = self.X_pool - target
        
        mahal_dists = np.sqrt(np.sum(diffs @ self.cov_inv * diffs, axis=1))
        mahal_sim = 1.0 - (mahal_dists / (mahal_dists.max() + 1e-10))

        if self.rf_model is not None:
            rf_prox = np.mean(self.rf_model.apply(self.X_pool) == self.rf_model.apply(target)[0], axis=1)
        else:
            rf_prox = np.zeros(self.X_pool.shape[0])

        if clusterer is not None:
            cluster_sim = (clusterer.predict(self.X_pool)['labels'] == clusterer.predict(target)['labels'][0]).astype(float)
        else:
            cluster_sim = np.zeros(self.X_pool.shape[0])

        similarity = (self.ALPHA * mahal_sim + self.BETA * rf_prox + self.GAMMA * cluster_sim) * 100.0
        
        results = []
        for idx in np.argsort(similarity)[::-1][:top_n]:
            results.append({
                'pool_index': int(idx), 'similarity_pct': round(float(similarity[idx]), 1),
                'mahalanobis_component': round(float(mahal_sim[idx] * 100), 1),
                'rf_proximity_component': round(float(rf_prox[idx] * 100), 1),
                'cluster_component': round(float(cluster_sim[idx] * 100), 1),
            })
        return results


# ================================================================
# MÓDULO 7: SCOUT SCORE PREDITIVO
# ================================================================

class ScoutScorePreditivo:
    LAMBDA_WP, LAMBDA_EFF, LAMBDA_CLUSTER, LAMBDA_PERC = 0.25, 0.25, 0.15, 0.35

    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.feature_selector = None
        self.wp_model = None
        self.clusterer = None
        self.selected_weights = None
        self._fitted = False

    def fit(self, df: pd.DataFrame, position: str, result_col: Optional[str] = None,
            min_minutes: int = 500, minutes_col: str = 'Minutos jogados:', pos_col: str = 'Posição') -> 'ScoutScorePreditivo':
        
        if pos_col in df.columns:
            df = df[df[pos_col] == position].copy()

        if not HAS_SKLEARN: raise RuntimeError("scikit-learn necessário")
        features = self.preprocessor.get_available_features(df, position)
        if len(features) < 5: raise ValueError(f"Features insuficientes: {len(features)}")

        df_filtered, X_scaled, available = self.preprocessor.prepare_matrix(df, features, min_minutes, minutes_col)

        y_target = pd.to_numeric(df_filtered[result_col], errors='coerce').fillna(0).values if result_col and result_col in df_filtered.columns else None
        
        self.feature_selector = PositionFeatureSelector().fit(X_scaled, available, position, y_target)
        self.selected_weights = self.feature_selector.get_weights_dict(available, top_k=15)

        if y_target is not None and len(np.unique(y_target)) > 1:
            self.wp_model = WinProbabilityModel().fit(X_scaled, (y_target > 0).astype(int), available)

        if len(df_filtered) >= 15:
            try: self.clusterer = TacticalClusterer().fit(X_scaled, available)
            except Exception: self.clusterer = None

        self._fitted = True
        self._position = position
        self._available = available
        return self

    def score_player(self, player_row, df_all: pd.DataFrame) -> Dict[str, Any]:
        if not self._fitted: return {'ssp': None, 'error': 'Modelo não treinado'}
        
        perc_score = self._percentile_component(player_row, df_all)
        wp_score = self._wp_component(player_row, df_all)
        eff_score = self._efficiency_component(player_row, df_all)
        cluster_score = self._cluster_component(player_row, df_all)

        ssp = self.LAMBDA_WP * wp_score + self.LAMBDA_EFF * eff_score + self.LAMBDA_CLUSTER * cluster_score + self.LAMBDA_PERC * perc_score
        return {
            'ssp': round(max(0, min(100, ssp)), 1),
            'wp_component': round(wp_score, 1), 'efficiency_component': round(eff_score, 1),
            'cluster_component': round(cluster_score, 1), 'percentile_component': round(perc_score, 1),
            'position': self._position,
        }

    def _percentile_component(self, player_row, df_all) -> float:
        weights = self.selected_weights or {}
        if not weights: return 50.0
        weighted_sum, total_weight = 0.0, 0.0
        for feature, w in weights.items():
            resolved = self.preprocessor.resolve_metric(feature, player_row.index)
            if not resolved: continue
            val = self.preprocessor.safe_float(player_row[resolved])
            if np.isnan(val): continue
            perc = self.preprocessor.percentile_rank(val, df_all[resolved])
            if feature in INVERTED_METRICS or self.preprocessor._is_inverted(feature): perc = 100.0 - perc
            weighted_sum += perc * w
            total_weight += w
        return weighted_sum / total_weight if total_weight > 0 else 50.0

    def _wp_component(self, player_row, df_all) -> float:
        if self.wp_model is None or not self.wp_model.significant_features: return self._percentile_component(player_row, df_all)
        wp_weights = self.wp_model.get_wp_weights()
        weighted_sum, total_weight = 0.0, 0.0
        for feature, w in wp_weights.items():
            resolved = self.preprocessor.resolve_metric(feature, player_row.index)
            if not resolved: continue
            val = self.preprocessor.safe_float(player_row[resolved])
            if np.isnan(val): continue
            perc = self.preprocessor.percentile_rank(val, df_all[resolved])
            if feature in INVERTED_METRICS: perc = 100.0 - perc
            weighted_sum += perc * w
            total_weight += w
        return weighted_sum / total_weight if total_weight > 0 else 50.0

    def _efficiency_component(self, player_row, df_all) -> float:
        if self._position == 'Goleiro': eff = xGResidualModel.calculate_goalkeeper_efficiency(player_row, df_all, self.preprocessor)
        elif self._position in ('Atacante', 'Extremo', 'Meia'): eff = xGResidualModel.calculate_attacker_efficiency(player_row, df_all, self.preprocessor)
        else: return 50.0
        try:
            from scipy.stats import norm
            return float(norm.cdf(eff.get('efficiency_score', 0.0)) * 100)
        except Exception:
            return float(1.0 / (1.0 + np.exp(-eff.get('efficiency_score', 0.0))) * 100)

    def _cluster_component(self, player_row, df_all) -> float:
        if self.clusterer is None: return 50.0
        try:
            vals = [self.preprocessor.safe_float(player_row[self.preprocessor.resolve_metric(f, player_row.index)]) if self.preprocessor.resolve_metric(f, player_row.index) else 0.0 for f in self._available]
            vals = [v if not np.isnan(v) else 0.0 for v in vals]
            X_single = np.array(vals).reshape(1, -1)
            if self.preprocessor.scaler:
                X_single = self.preprocessor.scaler.transform(self.preprocessor.imputer.transform(X_single))
            return self.clusterer.get_cluster_fit_score(X_single[0]) * 100
        except Exception: return 50.0

    def rank_players(self, df: pd.DataFrame, df_percentil: pd.DataFrame, min_minutes: int = 0,
                     minutes_col: str = 'Minutos jogados:') -> pd.DataFrame:
        """Batch scoring: aplica score_player a cada linha e retorna DataFrame rankeado."""
        if not self._fitted:
            return df.copy()

        df_out = df.copy()
        if min_minutes > 0 and minutes_col in df_out.columns:
            df_out = df_out[pd.to_numeric(df_out[minutes_col], errors='coerce').fillna(0) >= min_minutes]

        scores = []
        for idx, row in df_out.iterrows():
            result = self.score_player(row, df_percentil)
            scores.append(result.get('ssp') or 0.0)

        df_out['SSP'] = scores
        df_out['Score'] = df_out['SSP']
        df_out = df_out.sort_values('SSP', ascending=False).reset_index(drop=True)
        return df_out


# ================================================================
# MÓDULO 8: PREDIÇÃO DE SUCESSO DE CONTRATAÇÃO
# ================================================================

class ContractSuccessPredictor:
    # Tiers baseados em Power Rankings calibrados (escala 0-10)
    # Fonte: agregação de rankings Opta/Transfermarkt/WyScout por liga
    LEAGUE_TIERS = {
        # === TOP 5 EUROPEIAS ===
        'Premier League': 9.8,
        'La Liga': 9.8,
        'Serie A Italia': 8.6,
        'Bundesliga': 9.3,
        'Ligue 1': 9.2,
        # === 2ª DIVISÕES TOP 5 ===
        'Championship': 8.9,
        'La Liga 2': 8.0,
        'Serie B Italia': 7.7,
        '2. Bundesliga': 7.5,
        'Ligue 2': 7.0,
        'La Liga 3': 6.4,              # Primera Federación
        'Serie C Italia': 5.5,
        # === EUROPA — TIER 2 (1ª divisão) ===
        'Liga Portugal': 8.5,
        'Belgian Pro League': 8.2,
        'Eredivisie': 8.4,
        'Super Lig': 7.9,
        'Scottish Premiership': 8.4,
        'Russian Premier League': 7.3,
        'Austrian Bundesliga': 7.8,
        'Swiss Super League': 8.0,
        'Danish Superliga': 8.0,
        'Greek Super League': 7.4,
        'Ukrainian Premier League': 6.9,
        'Czech First League': 7.5,
        'Croatian First League': 7.3,
        'Serbian Super Liga': 8.1,
        'Polish Ekstraklasa': 7.3,
        'Romanian Liga I': 7.1,
        'Norwegian Eliteserien': 7.2,
        'Swedish Allsvenskan': 7.6,
        'Israeli Premier League': 7.2,
        'Bulgarian First League': 6.7,
        'Cypriot First Division': 7.2,
        'Hungarian NB I': 7.8,
        'Albanian Superiore': 5.2,
        # === EUROPA — TIER 2 (2ª divisão / inferior) ===
        'Liga Portugal 2': 6.3,
        'Liga Portugal 3': 5.0,
        'Campeonato de Portugal': 3.5,
        'Super Lig 2': 6.4,            # 1. Lig Turquia
        'Swiss Challenge League': 6.2,
        'Belgian Second Division': 6.1,
        'Austrian 2. Liga': 6.2,
        'Romanian Liga II': 5.5,
        'Bosnian Premier League': 6.0,
        'Slovenian PrvaLiga': 6.5,
        'Slovak Super Liga': 6.0,
        'Moldovan National Division': 5.5,
        'Montenegrin First League': 4.0,
        'Maltese Premier League': 4.5,
        'Croatian HNL': 7.5,
        'Czech First League': 7.5,
        'Azerbaijan Premier League': 5.5,
        'Armenian Premier League': 5.5,
        # === AMÉRICAS ===
        'Serie A Brasil': 9.0,
        'Serie B Brasil': 7.5,
        'Serie C Brasil': 6.3,
        'Serie D Brasil': 5.5,
        'Liga Argentina': 8.2,
        'Liga Argentina B': 6.7,       # Primera Nacional
        'MLS': 7.6,
        'Liga MX': 7.7,
        'Liga Colombia': 7.4,
        'Liga Colombia B': 5.8,        # Primera B Col
        'Liga Chile': 7.2,
        'Liga Chile B': 5.9,           # Primera B Chile
        'Liga Uruguai': 6.8,
        'Liga Uruguai B': 4.5,         # Segunda División
        'Liga Peru': 6.0,
        'Liga Equador': 7.2,
        'Liga Paraguai': 7.6,
        'Liga Paraguai B': 5.4,        # División Intermedia
        'Liga Bolivia': 6.3,
        'Liga Venezuela': 5.8,
        # === ÁSIA / ORIENTE MÉDIO ===
        'J1 League': 7.3,
        'J2 League': 6.5,
        'K-League 1': 7.2,
        'K-League 2': 5.8,
        'Saudi Pro League': 7.6,
        'Saudi First Division': 5.7,
        'Qatar Stars League': 6.4,
        'UAE Pro League': 6.4,
        'UAE First Division': 5.1,
        'Chinese Super League': 6.8,
        'Indian Super League': 5.0,
        'Thai League': 5.8,
        'Malaysian Super League': 5.0,
        'Indonesian Liga 1': 5.0,
        'Uzbek Super League': 5.5,
        'Kuwaiti Premier League': 4.0,
        'Bangladesh Premier League': 2.0,
        'Liga Nacional Guatemala': 4.8,
        # === ÁFRICA ===
        'Egyptian Premier League': 7.0,
        'South African Premier': 6.0,
        'Moroccan Botola': 6.5,
        'Tunisian Ligue 1': 6.8,
        # === OCEANIA ===
        'A-League': 7.0,
        # === ESTADUAIS BRASIL ===
        'Paulista A1': 4.5,
        'Paulista A2': 5.2,
        'Paulista A3': 2.0,
        'Carioca A1': 4.5,
        'Gaucho A1': 4.0,
        'Mineiro A1': 4.0,
        'Paranaense A1': 5.0,
        'Catarinense A1': 4.5,
        'Cearense A1': 3.0,
        'Pernambucano A1': 3.0,
        'Baiano A1': 3.0,
        # === COPAS ===
        'Copa do Brasil': 7.0,
        'Copa do Nordeste': 4.0,
        'Copa Libertadores': 9.0,
        'Copa Sudamericana': 7.5,
    }

    def predict_success_unsupervised(self, ssp_score: float, age: float, league_origin: str, league_target: str, minutes: float, max_minutes: float = 3000) -> Dict[str, Any]:
        tier_origin = self.LEAGUE_TIERS.get(league_origin, 5)
        tier_target = self.LEAGUE_TIERS.get(league_target, 5)
        gap = tier_target - tier_origin
        
        league_discount = 0.7 + 0.3 * min(tier_origin / 10.0, 1.0)
        ssp_adj = (ssp_score / 100.0) * league_discount
        age_factor = max(0, 1 - ((age - 26) ** 2) / (15 ** 2))
        league_factor = np.exp(-0.35 * gap) if gap > 0 else 1.0
        minutes_factor = min(minutes / max_minutes, 1.0)
        
        z = 0.30 * ssp_adj + 0.15 * age_factor + 0.35 * league_factor + 0.20 * minutes_factor
        prob = 1.0 / (1.0 + np.exp(-(z - 0.5) * 8))
        
        if gap >= 6: prob = min(prob, 0.15)
        elif gap >= 5: prob = min(prob, 0.25)
        elif gap >= 4: prob = min(prob, 0.35)

        return {
            'success_probability': round(float(prob), 3), 
            'risk_level': 'baixo' if prob >= 0.65 else 'medio' if prob >= 0.40 else 'alto' if prob >= 0.20 else 'muito alto',
            'ssp_contribution': ssp_adj,
            'age_factor': age_factor,
            'league_factor': league_factor,
            'minutes_factor': minutes_factor,
            'league_discount': league_discount,
            'tier_origin': tier_origin,
            'tier_target': tier_target,
            'league_gap': gap
        }

# ================================================================
# HELPERS E BACKWARD COMPATIBILITY
# ================================================================

def _z_score(value: float, df: pd.DataFrame, col: str) -> float:
    series = pd.to_numeric(df[col], errors='coerce').dropna()
    if len(series) < 2 or series.std() == 0: return 0.0
    return (value - series.mean()) / series.std()

def calculate_overall_score_v3(player_row, position, df_all, ssp_engine: Optional[ScoutScorePreditivo] = None):
    if ssp_engine is not None and ssp_engine._fitted:
        return ssp_engine.score_player(player_row, df_all).get('ssp')
    try:
        from similarity import calculate_overall_score
        return calculate_overall_score(player_row, position, df_all)
    except ImportError: return 50.0

def compute_advanced_similarity(target_player, comparison_pool, position,
                                 top_n=20, min_minutes=500, minutes_col='Minutos jogados:',
                                 player_display_col='JogadorDisplay', percentile_base=None,
                                 pos_col='Posição'):
    
    if pos_col in comparison_pool.columns:
        comparison_pool = comparison_pool[comparison_pool[pos_col] == position].copy()

    if not HAS_SKLEARN:
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(target_player, comparison_pool, position, top_n, min_minutes, minutes_col, player_display_col, percentile_base)

    preprocessor = DataPreprocessor()
    features = preprocessor.get_available_features(comparison_pool, position)
    
    try:
        df_filtered, X_scaled, available = preprocessor.prepare_matrix(comparison_pool, features, min_minutes, minutes_col)
    except Exception:
        from similarity import compute_weighted_cosine_similarity
        return compute_weighted_cosine_similarity(target_player, comparison_pool, position, top_n, min_minutes, minutes_col, player_display_col, percentile_base)

    if player_display_col in df_filtered.columns and player_display_col in target_player.index:
        mask = df_filtered[player_display_col] != target_player[player_display_col]
        df_filtered = df_filtered[mask]
        X_scaled = X_scaled[mask.values]

    target_vals = [preprocessor.safe_float(target_player[preprocessor.resolve_metric(f, target_player.index)]) if preprocessor.resolve_metric(f, target_player.index) else 0.0 for f in available]
    target_vals = [v if not np.isnan(v) else 0.0 for v in target_vals]
    target_vec = np.array(target_vals).reshape(1, -1)
    target_scaled = preprocessor.scaler.transform(preprocessor.imputer.transform(target_vec))

    sim_engine = AdvancedSimilarity().fit(X_scaled)
    clusterer = TacticalClusterer().fit(X_scaled, available) if len(df_filtered) >= 15 else None
    results = sim_engine.compute_similarity(target_scaled[0], clusterer=clusterer, top_n=top_n)

    if not results: return pd.DataFrame()

    indices = [r['pool_index'] for r in results]
    out = df_filtered.iloc[indices].copy()
    out['similarity_pct'] = [r['similarity_pct'] for r in results]
    out['matched_metrics'] = len(available)
    out['mahalanobis_sim'] = [r['mahalanobis_component'] for r in results]
    out['rf_proximity'] = [r['rf_proximity_component'] for r in results]

    return out.sort_values('similarity_pct', ascending=False)
