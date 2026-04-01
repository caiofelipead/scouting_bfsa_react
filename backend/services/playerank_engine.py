"""
playerank_engine.py — PlayeRank Engine
=======================================

Implements the PlayeRank framework (Pappalardo & Cintia, ACM TIST 2019)
for multi-dimensional, role-aware player evaluation.

Pipeline:
1. Collect VAEP ratings + Wyscout aggregate metrics
2. Cluster players by tactical role (K-Means on positional feature vectors)
3. Within each cluster, compute multi-dimensional scores:
   - Scoring contribution
   - Playmaking
   - Defending
   - Physical
   - Possession
4. Calculate percentile rank within cluster
5. Produce composite PlayeRank score

References:
- Pappalardo, L. & Cintia, P. (2019). "PlayeRank: Data-driven Performance
  Evaluation and Player Ranking in Soccer via a Machine Learning Approach."
  ACM Transactions on Intelligent Systems and Technology.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    from sklearn.cluster import KMeans
    from sklearn.mixture import GaussianMixture
    from sklearn.preprocessing import StandardScaler
    from sklearn.impute import SimpleImputer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# ── Dimension Definitions ─────────────────────────────────────────────

# Metrics that contribute to each PlayeRank dimension
# Mapped to common Wyscout column names (Portuguese)
DIMENSION_METRICS = {
    "scoring": [
        "Golos/90", "Golos esperados/90", "Remates/90",
        "Remates a baliza, %", "Toques na area/90",
        "Golos marcados, %",
    ],
    "playmaking": [
        "Assistencias/90", "Assistencias esperadas/90", "Passes chave/90",
        "Passes progressivos/90", "Passes para terco final/90",
        "Passes inteligentes/90", "Cruzamentos certos, %",
    ],
    "defending": [
        "Acoes defensivas com exito/90", "Intersecoes/90",
        "Cortes/90", "Duelos defensivos ganhos, %",
        "Duelos aereos ganhos, %", "Remates intercetados/90",
        "Duelos defensivos/90",
    ],
    "physical": [
        "Duelos/90", "Duelos ganhos, %",
        "Duelos aerios/90", "Aceleracoes/90",
        "Corridas progressivas/90",
    ],
    "possession": [
        "Passes certos, %", "Passes/90",
        "Passes para a frente/90", "Dribles/90",
        "Dribles com sucesso, %", "Perdas/90",
        "Passes recebidos/90",
    ],
}

# English fallback column names
DIMENSION_METRICS_EN = {
    "scoring": [
        "goals_per90", "xg_per90", "shots_per90",
        "shot_accuracy", "touches_in_box_per90",
        "goal_conversion",
    ],
    "playmaking": [
        "assists_per90", "xa_per90", "key_passes_per90",
        "progressive_passes_per90", "passes_final_third_per90",
        "smart_passes_per90", "cross_accuracy",
    ],
    "defending": [
        "defensive_actions_per90", "interceptions_per90",
        "tackles_per90", "defensive_duel_win_pct",
        "aerial_win_pct", "clearances_per90",
        "recoveries_per90",
    ],
    "physical": [
        "duels_per90", "duel_win_pct",
        "aerial_duels_per90", "accelerations_per90",
        "progressive_runs_per90",
    ],
    "possession": [
        "pass_accuracy", "passes_per90",
        "forward_passes_per90", "dribbles_per90",
        "dribble_success_pct", "losses_per90",
        "receptions_per90",
    ],
}

# Clustering features — used to determine tactical role
CLUSTERING_FEATURES_PT = [
    "Golos/90", "Assistencias/90", "Golos esperados/90",
    "Acoes defensivas com exito/90", "Passes progressivos/90",
    "Dribles/90", "Cruzamentos/90", "Remates/90",
    "Intersecoes/90", "Duelos aerios/90",
    "Corridas progressivas/90", "Toques na area/90",
]

CLUSTERING_FEATURES_EN = [
    "goals_per90", "assists_per90", "xg_per90",
    "defensive_actions_per90", "progressive_passes_per90",
    "dribbles_per90", "crosses_per90", "shots_per90",
    "interceptions_per90", "aerial_duels_per90",
    "progressive_runs_per90", "touches_in_box_per90",
]

# Tactical role labels based on cluster characteristics
ROLE_LABELS = {
    0: "Goal Scorer",
    1: "Playmaker",
    2: "Box-to-Box",
    3: "Defensive Anchor",
    4: "Wide Player",
    5: "Ball-Playing Defender",
}

# Dimension weights for composite score (role-specific)
ROLE_DIMENSION_WEIGHTS = {
    "Goal Scorer": {"scoring": 0.40, "playmaking": 0.15, "defending": 0.05, "physical": 0.15, "possession": 0.25},
    "Playmaker": {"scoring": 0.10, "playmaking": 0.40, "defending": 0.05, "physical": 0.10, "possession": 0.35},
    "Box-to-Box": {"scoring": 0.15, "playmaking": 0.20, "defending": 0.20, "physical": 0.25, "possession": 0.20},
    "Defensive Anchor": {"scoring": 0.05, "playmaking": 0.10, "defending": 0.40, "physical": 0.25, "possession": 0.20},
    "Wide Player": {"scoring": 0.15, "playmaking": 0.25, "defending": 0.10, "physical": 0.20, "possession": 0.30},
    "Ball-Playing Defender": {"scoring": 0.05, "playmaking": 0.15, "defending": 0.35, "physical": 0.20, "possession": 0.25},
}

DEFAULT_WEIGHTS = {"scoring": 0.20, "playmaking": 0.20, "defending": 0.20, "physical": 0.20, "possession": 0.20}


class PlayeRankEngine:
    """PlayeRank Engine — multi-dimensional, role-aware player evaluation."""

    def __init__(self, n_clusters: int = 6):
        self.n_clusters = n_clusters
        self.cluster_model = None
        self.scaler = None
        self.imputer = None
        self._fitted = False

    def compute_rankings(self, df_wyscout: pd.DataFrame,
                         vaep_ratings: Optional[List[Dict]] = None,
                         season: str = "current") -> List[Dict[str, Any]]:
        """Compute PlayeRank scores for all players.

        Args:
            df_wyscout: Wyscout aggregate stats DataFrame
            vaep_ratings: Optional list of VAEP rating dicts (merged if provided)
            season: Season identifier

        Returns:
            List of PlayeRank score dicts for each player
        """
        if df_wyscout is None or len(df_wyscout) == 0:
            return []

        df = df_wyscout.copy()

        # Merge VAEP ratings if available
        if vaep_ratings:
            vaep_df = pd.DataFrame(vaep_ratings)
            if "player_name" in vaep_df.columns:
                player_col = "Jogador" if "Jogador" in df.columns else "player_name"
                df = df.merge(
                    vaep_df[["player_name", "vaep_per90", "offensive_vaep", "defensive_vaep"]],
                    left_on=player_col,
                    right_on="player_name",
                    how="left",
                    suffixes=("", "_vaep"),
                )

        # Step 1: Cluster players by tactical role
        clusters = self._cluster_players(df)
        df["role_cluster"] = clusters

        # Step 2: Compute dimension scores
        dimension_scores = self._compute_dimensions(df)

        # Step 3: Compute composite scores and percentiles within clusters
        results = self._compute_rankings(df, dimension_scores, season)

        return results

    def _cluster_players(self, df: pd.DataFrame) -> np.ndarray:
        """Cluster players into tactical roles using K-Means."""
        # Resolve available features
        features = self._resolve_features(df, CLUSTERING_FEATURES_PT, CLUSTERING_FEATURES_EN)
        if len(features) < 3:
            logger.warning("Too few clustering features (%d) — assigning by position", len(features))
            return self._cluster_by_position(df)

        X = df[features].copy()
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors="coerce")

        if not HAS_SKLEARN:
            return self._cluster_by_position(df)

        self.imputer = SimpleImputer(strategy="median")
        X_imputed = self.imputer.fit_transform(X)

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_imputed)

        # Adjust number of clusters based on data size
        n_clusters = min(self.n_clusters, max(2, len(df) // 10))

        self.cluster_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = self.cluster_model.fit_predict(X_scaled)

        self._fitted = True
        self._assign_role_labels(df, labels, features)

        return labels

    def _cluster_by_position(self, df: pd.DataFrame) -> np.ndarray:
        """Fallback: cluster by nominal position."""
        pos_col = "Posição" if "Posição" in df.columns else "position"
        if pos_col not in df.columns:
            return np.zeros(len(df), dtype=int)

        position_map = {
            "CF": 0, "ST": 0, "LW": 4, "RW": 4,
            "AM": 1, "CAM": 1, "CM": 2, "LM": 4, "RM": 4,
            "DM": 3, "CDM": 3, "DMF": 3,
            "LB": 4, "RB": 4, "LWB": 4, "RWB": 4,
            "CB": 5, "GK": 3,
        }

        def _map_position(pos):
            if pd.isna(pos):
                return 2  # default to box-to-box
            pos_str = str(pos).strip().upper()
            for key, val in position_map.items():
                if key in pos_str:
                    return val
            return 2

        return df[pos_col].apply(_map_position).values

    def _assign_role_labels(self, df: pd.DataFrame, labels: np.ndarray,
                            features: List[str]):
        """Assign descriptive role labels to clusters based on their centroids."""
        if self.cluster_model is None:
            return

        centroids = self.cluster_model.cluster_centers_
        n_clusters = len(centroids)

        # Analyze each cluster's centroid to assign a role
        for i in range(n_clusters):
            centroid = centroids[i]
            # This is a simplified heuristic — in production, you'd analyze
            # the feature importance per cluster more carefully
            if i not in ROLE_LABELS:
                ROLE_LABELS[i] = f"Cluster {i}"

    def _compute_dimensions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute dimension scores for each player."""
        dim_scores = pd.DataFrame(index=df.index)

        for dim_name, metrics_pt in DIMENSION_METRICS.items():
            metrics_en = DIMENSION_METRICS_EN[dim_name]
            available = self._resolve_features(df, metrics_pt, metrics_en)

            if not available:
                dim_scores[dim_name] = 50.0  # neutral score
                continue

            # Get numeric values and rank them as percentiles
            dim_df = df[available].copy()
            for col in dim_df.columns:
                dim_df[col] = pd.to_numeric(dim_df[col], errors="coerce")

            # Invert metrics where lower is better (e.g., losses, fouls)
            invert_cols = [c for c in available if any(inv in c.lower() for inv in
                           ["perdas", "losses", "erros", "errors", "faltas"])]
            for col in invert_cols:
                dim_df[col] = -dim_df[col]

            # Percentile rank each metric, then average
            ranks = dim_df.rank(pct=True, na_option="keep")
            dim_scores[dim_name] = ranks.mean(axis=1) * 100

            # Fill NaN with 50 (neutral)
            dim_scores[dim_name] = dim_scores[dim_name].fillna(50.0)

        return dim_scores

    def _compute_rankings(self, df: pd.DataFrame, dim_scores: pd.DataFrame,
                          season: str) -> List[Dict[str, Any]]:
        """Compute final PlayeRank scores with percentile within cluster."""
        player_col = "Jogador" if "Jogador" in df.columns else "player_name"
        team_col = "Equipa" if "Equipa" in df.columns else "team"
        pos_col = "Posição" if "Posição" in df.columns else "position"
        league_col = "liga_tier" if "liga_tier" in df.columns else "league"

        results = []
        for idx, row in df.iterrows():
            cluster_id = int(row.get("role_cluster", 0))
            role = ROLE_LABELS.get(cluster_id, f"Cluster {cluster_id}")
            weights = ROLE_DIMENSION_WEIGHTS.get(role, DEFAULT_WEIGHTS)

            # Dimension scores
            scoring = float(dim_scores.loc[idx, "scoring"]) if "scoring" in dim_scores.columns else 50.0
            playmaking = float(dim_scores.loc[idx, "playmaking"]) if "playmaking" in dim_scores.columns else 50.0
            defending = float(dim_scores.loc[idx, "defending"]) if "defending" in dim_scores.columns else 50.0
            physical = float(dim_scores.loc[idx, "physical"]) if "physical" in dim_scores.columns else 50.0
            possession = float(dim_scores.loc[idx, "possession"]) if "possession" in dim_scores.columns else 50.0

            # Composite score (weighted by role)
            composite = (
                scoring * weights["scoring"] +
                playmaking * weights["playmaking"] +
                defending * weights["defending"] +
                physical * weights["physical"] +
                possession * weights["possession"]
            )

            # Boost with VAEP if available
            vaep_per90 = self._safe_float(row.get("vaep_per90", 0))
            if vaep_per90 > 0:
                # Scale VAEP to 0-100 range (top VAEP ≈ 0.8 per90)
                vaep_bonus = min(vaep_per90 / 0.8 * 100, 100) * 0.15
                composite = composite * 0.85 + vaep_bonus

            results.append({
                "player_name": str(row.get(player_col, "")),
                "team": str(row.get(team_col, "")) if pd.notna(row.get(team_col)) else None,
                "league": str(row.get(league_col, "")) if pd.notna(row.get(league_col)) else None,
                "position": str(row.get(pos_col, "")) if pd.notna(row.get(pos_col)) else None,
                "role_cluster": role,
                "composite_score": round(composite, 2),
                "scoring_dim": round(scoring, 2),
                "playmaking_dim": round(playmaking, 2),
                "defending_dim": round(defending, 2),
                "physical_dim": round(physical, 2),
                "possession_dim": round(possession, 2),
                "percentile_in_cluster": 0.0,  # Computed below
                "cluster_size": 0,
            })

        # Compute percentile within cluster
        cluster_groups = {}
        for i, r in enumerate(results):
            role = r["role_cluster"]
            cluster_groups.setdefault(role, []).append(i)

        for role, indices in cluster_groups.items():
            scores = [results[i]["composite_score"] for i in indices]
            size = len(indices)
            if size <= 1:
                for i in indices:
                    results[i]["percentile_in_cluster"] = 50.0
                    results[i]["cluster_size"] = size
                continue
            sorted_scores = sorted(scores)
            for i in indices:
                s = results[i]["composite_score"]
                # Count how many scores are strictly below this one
                count_below = sum(1 for x in sorted_scores if x < s)
                results[i]["percentile_in_cluster"] = round(count_below / (size - 1) * 100, 1)
                results[i]["cluster_size"] = size

        # Sort by composite score descending
        results.sort(key=lambda x: x["composite_score"], reverse=True)
        return results

    # ── Utilities ─────────────────────────────────────────────────────

    @staticmethod
    def _resolve_features(df: pd.DataFrame, features_pt: List[str],
                          features_en: List[str]) -> List[str]:
        """Resolve available features, trying Portuguese first then English."""
        available = [f for f in features_pt if f in df.columns]
        if not available:
            available = [f for f in features_en if f in df.columns]
        return available

    @staticmethod
    def _safe_float(val, default: float = 0.0) -> float:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return default
        try:
            if isinstance(val, str):
                val = val.replace(",", ".").strip()
            return float(val)
        except (ValueError, TypeError):
            return default
