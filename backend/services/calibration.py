"""
calibration.py — Coeficientes Reais Calibrados pela Literatura Acadêmica
=========================================================================

Fonte dos coeficientes (Motor Original — predictive_engine.py):

1. PIBITI João Vitor Oliveira (Insper, 2025)
   → Regressão Linear Múltipla sobre dados SofaScore
   → 80 jogadores, 12.688 registros, R² > 0.97 (in-position)
   → Coeficientes β por posição: impacto no rating

2. Victor Valvano Schimidt (UNESP Rio Claro, 2021)
   → Regressão Logística para win-probability
   → 5.396 jogadores, 10 ligas, 7 posições × 10 ligas = 70 grupos
   → Coeficientes [-1, +1]: impacto na probabilidade de vitória
   → Escala: |0–0.333| baixo, |0.334–0.666| moderado, |0.667–1| alto

3. Eduardo Baptista dos Santos (MBA USP/ICMC, 2024)
   → Classificação de jogadores por posição + características físicas
   → Melhores modelos: RF (Volante F1=83%), XGBoost (Zagueiro F1=80%)
   → Features mais relevantes por posição

4. Frederico Ferra (NOVA IMS, 2025)
   → PCA + K-Means + RF para clustering tático
   → xG models com regressão logística + tracking
   → RF: 93.3% balanced accuracy para classificação tática

5. Tiago Pinto (ISEP Porto, 2024)
   → Gradient Boosting para predição de GoalRatio
   → RMSE = 0.016 (melhor resultado com z-score normalization)
   → Classificação de desempenho em 5 classes

Base científica complementar (Scouting Intelligence Engine — scouting_intelligence.py):
  - Decroos et al. (KDD 2019): VAEP — Valuing Actions by Estimating Probabilities
  - Khalife et al. (MDPI 2025): Dynamic Financial Valuation, R² > 0.91
  - Bhatt et al. (AIMV 2025): KickClone — Cosine Similarity + PCA
  - Age Curves 2.0 (TransferLab): Curvas de decaimento por habilidade
  - Opta Power Rankings (Stats Perform 2025): Elo modificado, +13.500 clubes
  - SciSkill Forecasting (MDPI 2025): 86 features, RF + XGBoost
  - Brighton / Brentford / Midtjylland: Validação empírica do opportunity score
  Ver docstring completa em scouting_intelligence.py para mapeamento detalhado.
"""

import numpy as np
from typing import Dict, List, Tuple

# ================================================================
# 1. COEFICIENTES DE RATING POR POSIÇÃO (PIBITI João Vitor, 2025)
# ================================================================
# Coeficientes β da regressão linear múltipla OLS
# Variável dependente: rating SofaScore
# R² in-position: Goleiros=0.98, Defensores=0.99, Meias=0.99, Atacantes=0.98

RATING_COEFFICIENTS = {
    'Goleiro': {
        # Top 5 por magnitude de β
        'penaltySave': 0.66,
        'aerialLost': 0.33,     # GK-specific: duelos aéreos perdidos
        'totalContest': 0.14,
        'saves': 0.14,
        'duelWon': 0.11,
        # Correlações altas com rating (matrizes de correlação)
        'minutesPlayed': 0.97,  # r com rating
        'touches': 0.82,
        'totalPass': 0.77,
        'accuratePass': 0.69,
        'totalLongBalls': 0.62,
        'savedShotsFromInsideTheBox': 0.53,
    },
    'Zagueiro': {
        # Top 5 — nota: ações ofensivas dominam mesmo para defensores
        'goals': 0.52,
        'goalAssist': 0.33,
        'penaltyWon': 0.17,
        'onTargetScoringAttempt': 0.14,
        'hitWoodwork': 0.12,
        # Correlações com rating
        'minutesPlayed': 0.89,
        'touches': 0.80,
        'accuratePass': 0.71,
        'duelWon': 0.62,
        'totalLongBalls': 0.60,
        'totalClearance': 0.49,
    },
    'Lateral direito': {
        'goals': 0.52, 'goalAssist': 0.33, 'penaltyWon': 0.17,
        'onTargetScoringAttempt': 0.14, 'hitWoodwork': 0.12, 'totalCross': 0.10,
    },
    'Lateral esquerdo': {
        'goals': 0.52, 'goalAssist': 0.33, 'penaltyWon': 0.17,
        'onTargetScoringAttempt': 0.14, 'hitWoodwork': 0.12, 'totalCross': 0.10,
    },
    'Volante': {
        # Meio-campistas
        'goals': 0.54,
        'goalAssist': 0.25,
        'bigChanceCreated': 0.24,
        'penaltyWon': 0.16,
        'hitWoodwork': 0.15,
        # Correlações
        'minutesPlayed': 0.74,
        'touches': 0.65,
        'totalPass': 0.57,
        'duelWon': 0.52,
        'keyPass': 0.45,
    },
    'Meia': {
        'goals': 0.54,
        'goalAssist': 0.25,
        'bigChanceCreated': 0.24,
        'penaltyWon': 0.16,
        'hitWoodwork': 0.15,
        'keyPass': 0.45,
        'accuratePass': 0.54,
    },
    'Atacante': {
        # Top 5
        'goals': 0.60,
        'goalAssist': 0.37,
        'onTargetScoringAttempt': 0.16,
        'penaltyWon': 0.16,
        'hitWoodwork': 0.15,
        # Correlações
        'minutesPlayed': 0.74,
        'touches': 0.63,
        'totalPass': 0.57,
        'duelWon': 0.50,
        'keyPass': 0.47,
        'bigChanceCreated': 0.34,
    },
    'Extremo': {
        # Pontas (Schimidt) — mescla atacante + meia
        'goals': 0.57,
        'goalAssist': 0.31,
        'onTargetScoringAttempt': 0.16,
        'penaltyWon': 0.16,
        'hitWoodwork': 0.15,
        'keyPass': 0.46,
        'bigChanceCreated': 0.29,
    },
}


# ================================================================
# 2. COEFICIENTES WIN-PROBABILITY (Victor Schimidt, 2021)
# ================================================================
# Coeficientes da regressão logística: P(vitória) = σ(Σ βᵢ·xᵢ)
# Escala: [-1, +1]. Positivo = contribui para vitória.
# Valores representam MÉDIA ponderada das 10 ligas analisadas.
# Posições conforme taxonomia do estudo: Lat, Zag, Vol, Mca, Mat, Pta, Cav

WP_COEFFICIENTS = {
    'Lateral direito': {
        'local': 0.45, 'goals': 0.35, 'goalAssist': 0.40,
        'accuratePass': 0.30, 'totalCross': -0.25, 'accurateCross': 0.10,
    },
    'Lateral esquerdo': {
        'local': 0.45, 'goals': 0.35, 'goalAssist': 0.40,
        'accuratePass': 0.30, 'totalCross': -0.25, 'accurateCross': 0.10,
    },
    'Zagueiro': {
        'local': 0.40,
        'goals': 0.32,              # max 0.316 no Brasileirão
        'goalAssist': 0.20,
        'duelsTotal': -0.30,        # NEGATIVO — muitos duelos = pressão sofrida
        'accuratePass': 0.15,
    },
    'Volante': {
        'local': 0.42,
        'goals': 0.20,              # baixo para volantes
        'goalAssist': 0.18,
        'accuratePass': 0.22,
        'possessionLostCtrl': -0.30, # perda de posse negativa (Col=moderado)
        'duelWon': 0.15,            # destaque em FRA e NED
        'interception': 0.12,
    },
    'Meia': {
        'local': 0.38,
        'goals': 0.50,              # moderado-alto
        'goalAssist': 0.42,
        'accuratePass': 0.35,       # moderado (ITA, COL)
        'interception': 0.12,       # destaque entre meias
        'keyPass': 0.20,
    },
    'Extremo': {
        'local': 0.40,
        'goals': 0.55,
        'goalAssist': 0.45,
        'accuratePass': 0.30,
        'onTargetScoringAttempt': 0.25,  # remate à baliza voltou com destaque
        'totalCross': -0.20,         # negativo também para pontas
        'accurateCross': 0.08,
    },
    'Atacante': {
        'local': 0.38,
        'goals': 0.65,              # próximo a alto
        'goalAssist': 0.50,
        'onTargetScoringAttempt': 0.30,  # destaque FRA, GER
        'accuratePass': 0.20,
        'totalCross': -0.15,
    },
    'Goleiro': {
        # Schimidt excluiu goleiros (dados insuficientes para ações analisadas)
        # Coeficientes derivados do PIBITI João Vitor
        'saves': 0.60,
        'penaltySave': 0.55,
        'goalsConceded': -0.50,     # negativo: gols sofridos
    },
}


# ================================================================
# 3. MELHORES MODELOS POR POSIÇÃO (Eduardo Baptista, 2024)
# ================================================================

BEST_MODELS_PER_POSITION = {
    'Goleiro':  {'model': 'LightGBM',    'precision': 0.80, 'recall': 0.80, 'f1': 0.79, 'accuracy': 0.73},
    'Zagueiro': {'model': 'XGBoost',     'precision': 0.78, 'recall': 0.83, 'f1': 0.80, 'accuracy': 0.72},
    'Lateral direito':  {'model': 'ExtraTrees',  'precision': 0.80, 'recall': 0.77, 'f1': 0.77, 'accuracy': 0.75},
    'Lateral esquerdo': {'model': 'ExtraTrees',  'precision': 0.80, 'recall': 0.77, 'f1': 0.77, 'accuracy': 0.75},
    'Volante':  {'model': 'RandomForest','precision': 0.79, 'recall': 0.89, 'f1': 0.83, 'accuracy': 0.78},
    'Meia':     {'model': 'ExtraTrees',  'precision': 0.76, 'recall': 0.77, 'f1': 0.76, 'accuracy': 0.72},
    'Atacante': {'model': 'RandomForest','precision': 0.74, 'recall': 0.83, 'f1': 0.78, 'accuracy': 0.71},
    'Extremo':  {'model': 'RandomForest','precision': 0.74, 'recall': 0.83, 'f1': 0.78, 'accuracy': 0.71},
}

# Features mais relevantes por posição (Eduardo Baptista — feature importance)
TOP_FEATURES_PER_POSITION = {
    'Goleiro': ['saves', 'goalsConceded', 'penaltySave', 'minutesPlayed', 'totalLongBalls', 'cleanSheet'],
    'Zagueiro': ['duelsWon', 'totalClearance', 'interception', 'accuratePass', 'aerialWon', 'goals'],
    'Lateral direito': ['totalCross', 'accurateCross', 'keyPass', 'duelWon', 'accuratePass', 'interception'],
    'Lateral esquerdo': ['totalCross', 'accurateCross', 'keyPass', 'duelWon', 'accuratePass', 'interception'],
    'Volante': ['accuratePass', 'interception', 'duelWon', 'possessionLostCtrl', 'keyPass', 'totalContest'],
    'Meia': ['keyPass', 'bigChanceCreated', 'goalAssist', 'accuratePass', 'goals', 'dribbleWon'],
    'Atacante': ['goals', 'onTargetScoringAttempt', 'bigChanceCreated', 'goalAssist', 'dribbleWon', 'age'],
    'Extremo': ['goals', 'goalAssist', 'dribbleWon', 'keyPass', 'onTargetScoringAttempt', 'totalCross'],
}

# Features onde idade e físico são relevantes (Eduardo Baptista)
PHYSICAL_FEATURES_IMPACT = {
    'Atacante': {'age': 'negative_when_young', 'height': 'negative_when_tall', 'mp': 'negative_when_high'},
    'Goleiro': {'height': 'positive_when_tall'},
    'Zagueiro': {'height': 'positive_when_tall', 'age': 'positive_moderate'},
}


# ================================================================
# 4. PARÂMETROS DE CLUSTERING TÁTICO (Frederico Ferra, 2025)
# ================================================================

CLUSTERING_CONFIG = {
    'pca_variance_target': 0.85,        # 85% variância explicada
    'k_range': (3, 8),                   # K-Means silhouette optimization
    'rf_balanced_accuracy': 0.933,       # RF para interpretabilidade (Ferra)
    'n_estimators_rf': 200,              # árvores para RF interpreter
    'gmm_covariance_type': 'full',       # GMM para probabilidades soft
    'xg_model': 'logistic_regression',   # xG base model (Ferra + Tiago)
}


# ================================================================
# 5. PARÂMETROS DE REGRESSÃO/CLASSIFICAÇÃO (Tiago Pinto, 2024)
# ================================================================

REGRESSION_CONFIG = {
    'best_model': 'GradientBoosting',
    'best_rmse': 0.016,
    'best_mae': 0.009,
    'normalization': 'z-score',
    'hyperparams': {
        'learning_rate': 0.5,
        'max_depth': 3,
        'n_estimators': 150,
    },
    'second_best_model': 'DecisionTree',
    'second_rmse': 0.027,
    'second_hyperparams': {
        'max_depth': 10,
        'min_samples_split': 2,
    },
}

CLASSIFICATION_CLASSES = {
    # Classificação de desempenho em 5 classes (Tiago Pinto)
    'Muito Baixo': (0.00, 0.20),
    'Baixo':       (0.20, 0.40),
    'Médio':       (0.40, 0.60),
    'Alto':        (0.60, 0.80),
    'Muito Alto':  (0.80, 1.00),
}


# ================================================================
# 6. MAPEAMENTO SOFASCORE → WYSCOUT (para compatibilidade)
# ================================================================
# O PIBITI usa métricas SofaScore, o dashboard usa Wyscout (português PT)
# Este mapeamento permite usar os coeficientes reais do PIBITI no Wyscout

SOFASCORE_TO_WYSCOUT = {
    'goals': 'Golos/90',
    'goalAssist': 'Assistencias/90',
    'onTargetScoringAttempt': 'Remates a baliza, %',
    'bigChanceCreated': 'Passes chave/90',
    'keyPass': 'Passes chave/90',
    'accuratePass': 'Passes certos, %',
    'totalPass': 'Passes/90',
    'totalLongBalls': 'Passes longos/90',
    'accurateLongBalls': 'Passes longos certos, %',
    'totalCross': 'Cruzamentos/90',
    'accurateCross': 'Cruzamentos certos, %',
    'duelWon': 'Duelos ganhos, %',
    'duelsTotal': 'Duelos/90',
    'totalClearance': 'Cortes/90',
    'interception': 'Intersecoes/90',
    'saves': 'Defesas, %',
    'goalsConceded': 'Golos sofridos/90',
    'penaltySave': 'Defesas, %',  # proxy — Wyscout não separa defesas de pênalti
    'aerialWon': 'Duelos aereos ganhos, %',
    'aerialLost': 'Duelos aerios/90',
    'totalContest': 'Duelos/90',
    'dribbleWon': 'Dribles com sucesso, %',
    'touches': 'Passes recebidos/90',
    'minutesPlayed': 'Minutos jogados:',
    'possessionLostCtrl': 'Faltas/90',  # proxy
    'hitWoodwork': 'Remates/90',  # proxy
    'penaltyWon': 'Faltas sofridas/90',  # proxy
    'totalCross': 'Cruzamentos/90',
}


# ================================================================
# 7. PESOS CALIBRADOS PARA O SSP (Scout Score Preditivo)
# ================================================================

def get_calibrated_wp_weights(position: str) -> Dict[str, float]:
    """
    Retorna pesos de win-probability calibrados por Schimidt (2021),
    mapeados para métricas Wyscout.
    """
    wp_coefs = WP_COEFFICIENTS.get(position, {})
    if not wp_coefs:
        return {}

    wyscout_weights = {}
    for sofascore_key, coef in wp_coefs.items():
        if sofascore_key == 'local':
            continue  # fator de campo não é feature do jogador
        wyscout_key = SOFASCORE_TO_WYSCOUT.get(sofascore_key)
        if wyscout_key:
            wyscout_weights[wyscout_key] = abs(coef)  # magnitude como peso

    # Normalizar
    total = sum(wyscout_weights.values())
    if total > 0:
        wyscout_weights = {k: v / total for k, v in wyscout_weights.items()}

    return wyscout_weights


def get_calibrated_rating_weights(position: str) -> Dict[str, float]:
    """
    Retorna pesos de rating calibrados por PIBITI João Vitor (2025),
    mapeados para métricas Wyscout.
    """
    rating_coefs = RATING_COEFFICIENTS.get(position, {})
    if not rating_coefs:
        return {}

    wyscout_weights = {}
    for sofascore_key, coef in rating_coefs.items():
        wyscout_key = SOFASCORE_TO_WYSCOUT.get(sofascore_key)
        if wyscout_key:
            wyscout_weights[wyscout_key] = abs(coef)

    total = sum(wyscout_weights.values())
    if total > 0:
        wyscout_weights = {k: v / total for k, v in wyscout_weights.items()}

    return wyscout_weights


def get_negative_impact_features() -> Dict[str, float]:
    """
    Features com impacto NEGATIVO na vitória (Schimidt, 2021).
    Cruzamentos ruins, perdas de posse, duelos excessivos de zagueiros.
    """
    return {
        'Cruzamentos/90': -0.25,        # universal: cruzamentos = negativo
        'Faltas/90': -0.15,             # perda de posse
        'Golos sofridos/90': -0.50,     # goleiros
    }


def classify_performance(score: float) -> str:
    """Classifica desempenho em 5 classes (Tiago Pinto, 2024)."""
    for label, (low, high) in CLASSIFICATION_CLASSES.items():
        if low <= score / 100.0 < high:
            return label
    return 'Muito Alto' if score >= 80 else 'Médio'


def get_wp_significance_threshold() -> Dict[str, str]:
    """
    Classificação qualitativa dos coeficientes (Schimidt, 2021).
    |0–0.333| = baixa, |0.334–0.666| = moderada, |0.667–1| = alta
    """
    return {
        'baixa': (0.0, 0.333),
        'moderada': (0.334, 0.666),
        'alta': (0.667, 1.0),
    }


# ================================================================
# 8. MODELO FUZZY + RANDOM FOREST (Felipe Nunes, UFMG 2025)
# ================================================================
# Tese de Doutorado: "Modelos preditores de contratação de profissionais
# do futebol baseado em IA por mecanismos Machine Learning"
# - Dados: Wyscout (1.263 atletas, 197.469 registros) + Football Manager 2024
# - Pipeline: Regressão Penalizada (LASSO/Ridge/Elastic Net) → Fuzzy (IFR/TFRa/IT2FS) → Random Forest (500 árvores)
# - Variáveis de interesse: gols, assistências, minutos, xG, xA, interceptações, faltas

NUNES_MODEL_RESULTS = {
    # Melhor modelo: IFR (Integrated Fuzzy Relative) com 39 fatores, sem ponderação
    'best_transform': 'IFR',
    'n_factors': 39,
    'n_trees': 500,
    'train_split': 0.70,
    # R² por variável de interesse (Random Forest sobre dados fuzzificados)
    'r2_by_target': {
        'interceptacoes': 0.9312,   # melhor R² — leitura de jogo
        'xG': 0.9283,              # alta capacidade preditiva
        'xA': 0.8881,              # assistências esperadas
        'minutos_jogados': 0.8691,  # regularidade
        'gols': 0.7509,            # finalização
        'faltas_sofridas': 0.6817,  # participação ofensiva
        'faltas_cometidas': 0.5564, # estilo defensivo
        'assistencias': 0.4943,     # mais difícil de prever
    },
    # Para valor de mercado (Transfermarkt)
    'market_value': {
        'best_model': 'TFRa + Elastic Net',
        'r2': 0.2922,
        'rmse': 0.2416,
    },
    # Para valor de transferência
    'transfer_fee': {
        'best_model': 'IFR + Elastic Net',
        'r2': 0.0984,
        'rmse': 0.0943,
    },
    # Conclusão-chave: estatísticas de desempenho explicam bem performance (R²>0.75)
    # mas explicam mal o valor financeiro (R²<0.30) — outros fatores não-estatísticos
    # (lesões, contrato, agentes, contexto tático) dominam a precificação.
}

# 39 fatores estatísticos do modelo final (Quadro 25, Nunes 2025)
NUNES_39_FACTORS = [
    'Remates', 'Remates a baliza', 'Passes', 'Passes certos',
    'Passes longos', 'Passes longos certos', 'Cruzamentos', 'Cruzamentos certos',
    'Dribles', 'Dribles com sucesso', 'Duelos', 'Duelos ganhos',
    'Duelos aereos', 'Duelos aereos ganhos', 'Perdas', 'Perdas meio-campo',
    'Recuperacoes', 'Recuperacoes campo adversario', 'Duelos defensivos',
    'Duelos defensivos ganhos', 'Duelos de bola livre', 'Duelos de bola livre ganhos',
    'Alivios', 'Assistencias para remate', 'Duelos ofensivos', 'Duelos ofensivos ganhos',
    'Toques na area', 'Corridas seguidas', 'Passes para terco final',
    'Passes para terco final certos', 'Passes para a grande area',
    'Passes para a grande area precisos', 'Passes recebidos',
    'Passes para a frente', 'Passes para a frente certos',
    'Passes em profundidade', 'Passes em profundidade certos',
    'Passes para tras', 'Passes para tras certos',
]


# ================================================================
# 9. MODELO xG / xGOT (Gabriel Buso, UFSC 2025)
# ================================================================
# TCC: "Análise Comparativa dos Modelos xG e xGOT para Avaliação
# da Performance de Finalizadores no Futebol"
# - Dados: StatsBomb (2022-2024), comparação com SofaScore comercial
# - Modelo: Regressão Logística (sklearn) com StandardScaler
# - Validação: Stratified K-Fold cross-validation

BUSO_XG_MODEL = {
    # Coeficientes da Regressão Logística xG (Figura 21)
    'xg_coefficients': {
        'angle_degrees': +0.71,          # maior impacto positivo
        'situation_penalty': +0.60,
        'player_position_atacante': +0.19,
        'situation_fast_break': +0.11,
        'distance_to_goal': -0.56,       # maior impacto negativo
        'player_position_zagueiro': -0.10,
        'situation_assisted': -0.09,
        'situation_free_kick': -0.08,
        'situation_corner': -0.06,
    },
    # Performance xG próprio
    'xg_performance': {
        'AUC': 0.7938,
        'Brier_Score': 0.0661,
        'Accuracy': 0.9185,
        'Precision': 0.6496,
        'Recall': 0.1852,
        'F1': 0.2882,
    },
    # Performance xG SofaScore (benchmark)
    'xg_sofascore': {
        'AUC': 0.8313,
        'Brier_Score': 0.0618,
        'F1': 0.3645,
    },
}

BUSO_XGOT_MODEL = {
    # Coeficientes da Regressão Logística xGOT (Figura 22)
    'xgot_coefficients': {
        'angle_degrees': +0.72,
        'situation_penalty': +0.43,
        # Variáveis pós-chute (diferenciais do xGOT)
        'mouth_location_low_centre': +0.40,   # canto baixo centro
        'mouth_location_high_centre': +0.30,  # canto alto centro
        'distance_to_goal': -0.66,             # maior negativo
    },
    # Performance xGOT próprio — SUPERIOR ao xG em discriminação
    'xgot_performance': {
        'AUC': 0.8288,           # > xG (0.7938)
        'Brier_Score': 0.1417,
        'Accuracy': 0.8004,
        'Precision': 0.7182,     # > xG (0.6496)
        'Recall': 0.4377,        # >> xG (0.1852) — 2.4x melhor
        'F1': 0.5439,            # >> xG (0.2882) — 1.9x melhor
    },
    # Performance xGOT SofaScore (benchmark)
    'xgot_sofascore': {
        'AUC': 0.8729,
        'Precision': 0.7046,
        'Recall': 0.5984,
        'F1': 0.6471,
    },
    # Achado-chave: xGOT SUPERA xG em recall (+136%) e F1 (+89%)
    # porque incorpora localização do chute na meta (pós-chute),
    # oferecendo maior sensibilidade na detecção de gols.
}

# Aplicação para avaliação de eficiência ofensiva
BUSO_EFFICIENCY_FRAMEWORK = {
    # Para atacantes/extremos:
    'overperformance': 'Gols_reais - xG_acumulado',  # positivo = acima do esperado
    'shot_quality': 'xGOT / Remates_no_alvo',        # qualidade do chute
    # xGOT > xG indica jogador que coloca bem a bola (finishing quality)
    # Gols > xG indica overperformer (sorte ou habilidade de finalização acima do modelo)
    # Gols < xG indica underperformer (azar ou baixa qualidade de finalização)
}


# ================================================================
# 10. SSP LAMBDAS CALIBRADOS (FINAL)
# ================================================================
# Ajustados com base na confiabilidade relativa de cada componente:
# - WP: Schimidt — logistic regression 10 ligas, bem fundamentado
# - Rating/Percentil: PIBITI R² = 0.97-0.99 → maior confiança
# - Clustering: Ferra RF = 93.3%, Nunes Fuzzy C-Means para perfis táticos
# - Eficiência xG: Buso AUC=0.83 (xGOT) + Nunes R²=0.93 para xG → agora calibrado

SSP_LAMBDAS = {
    'wp': 0.25,          # Win-probability (Schimidt)
    'efficiency': 0.25,  # xG residual — ELEVADO (Buso AUC=0.83 + Nunes R²=0.93)
    'cluster': 0.15,     # Cluster fit (Ferra + Nunes Fuzzy C-Means)
    'percentile': 0.35,  # Percentil calibrado (PIBITI R²=0.99) — ajustado
}
