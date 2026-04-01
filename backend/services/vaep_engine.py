"""
vaep_engine.py — VAEP (Valuing Actions by Estimating Probabilities) Engine
==========================================================================

Implements the VAEP framework (Decroos et al., KDD 2019) for the BFSA
scouting pipeline. Converts Wyscout event data → SPADL → features/labels →
XGBoost model → action values → per-player ratings.

Pipeline:
1. Load Wyscout events from PostgreSQL (or in-memory DataFrame)
2. Convert to SPADL format via socceraction
3. Generate features (action + game state) and labels (scoring/conceding)
4. Train or load XGBoost model
5. Predict scoring/conceding probabilities per game state
6. Compute VAEP value per action: ΔP(scoring) − ΔP(conceding)
7. Aggregate per player per 90 minutes
8. Persist ratings to PostgreSQL

References:
- Decroos et al. (KDD 2019): "Actions Speak Louder than Goals"
- Bransen & Van Haaren (2020): "On-the-Ball Contributions from Passes"
- socceraction library: https://socceraction.readthedocs.io/
"""

import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Conditional imports — graceful fallback
try:
    import socceraction.spadl as spadl
    import socceraction.vaep.features as features_module
    import socceraction.vaep.labels as labels_module
    import socceraction.vaep.formula as vaep_formula
    HAS_SOCCERACTION = True
except ImportError:
    HAS_SOCCERACTION = False
    logger.warning("socceraction not installed — VAEP engine will use heuristic fallback")

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logger.warning("xgboost not installed — falling back to sklearn GradientBoosting")

try:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import brier_score_loss, log_loss
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# ── Constants ─────────────────────────────────────────────────────────

MODEL_DIR = Path(os.environ.get("VAEP_MODEL_DIR", "models/vaep"))
NB_PREV_ACTIONS = 3  # Number of previous actions for game state features
MIN_MINUTES_STABLE = 900  # Minimum minutes for stable ratings

# SPADL action types for offensive/defensive classification
OFFENSIVE_ACTIONS = {"pass", "cross", "dribble", "shot", "freekick_short",
                     "freekick_crossed", "corner_short", "corner_crossed",
                     "take_on", "throw_in"}
DEFENSIVE_ACTIONS = {"tackle", "interception", "clearance", "keeper_save",
                     "keeper_claim", "keeper_punch", "keeper_pick_up"}

# ── Wyscout → SPADL Column Mapping ────────────────────────────────────

WYSCOUT_TO_SPADL_MAP = {
    "Pass": "pass",
    "Cross": "cross",
    "Shot": "shot",
    "Duel": "tackle",
    "Foul": "foul",
    "Free Kick": "freekick_short",
    "Goal Kick": "goalkick",
    "Throw-in": "throw_in",
    "Corner": "corner_short",
    "Offside": "non_action",
    "Acceleration": "dribble",
    "Touch": "touch",
    "Others on the ball": "non_action",
    "Clearance": "clearance",
    "Interception": "interception",
    "Save attempt": "keeper_save",
}


class VAEPEngine:
    """VAEP Engine — computes action values and player ratings.

    Supports two modes:
    1. Full mode (socceraction installed): proper SPADL conversion + ML model
    2. Heuristic mode (fallback): estimates VAEP from Wyscout aggregate stats
    """

    def __init__(self):
        self.scoring_model = None
        self.conceding_model = None
        self._fitted = False
        self._model_path = MODEL_DIR

    # ── Full Pipeline ─────────────────────────────────────────────────

    def run_pipeline(self, df_events: pd.DataFrame, season: str,
                     competition_id: int = None,
                     df_wyscout: pd.DataFrame = None) -> Dict[str, Any]:
        """Run the complete VAEP pipeline.

        Args:
            df_events: Event-level data (Wyscout format or SPADL-ready)
            season: Season identifier (e.g., "2024/25")
            competition_id: Optional competition ID
            df_wyscout: Aggregate Wyscout stats (for heuristic fallback)

        Returns:
            dict with player_ratings (list of dicts), summary stats
        """
        if HAS_SOCCERACTION and self._has_event_data(df_events):
            return self._run_full_pipeline(df_events, season, competition_id)
        elif df_wyscout is not None and len(df_wyscout) > 0:
            return self._run_heuristic_pipeline(df_wyscout, season, competition_id)
        else:
            raise ValueError(
                "No usable data: need either event-level data (with socceraction) "
                "or aggregate Wyscout stats for heuristic VAEP"
            )

    def _has_event_data(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame contains event-level data (not aggregates)."""
        event_cols = {"type_id", "action_type", "event_type", "type"}
        return bool(event_cols & set(df.columns))

    # ── Full VAEP Pipeline (socceraction) ─────────────────────────────

    def _run_full_pipeline(self, df_events: pd.DataFrame, season: str,
                           competition_id: int = None) -> Dict[str, Any]:
        """Full VAEP pipeline using socceraction library."""
        logger.info("Running full VAEP pipeline for season %s", season)

        # Step 1: Convert to SPADL
        spadl_actions = self._convert_to_spadl(df_events)
        logger.info("Converted %d events to %d SPADL actions",
                     len(df_events), len(spadl_actions))

        # Step 2: Generate features
        game_ids = spadl_actions["game_id"].unique()
        all_features = []
        all_labels_scoring = []
        all_labels_conceding = []
        all_actions = []

        for game_id in game_ids:
            game_actions = spadl_actions[spadl_actions["game_id"] == game_id].copy()
            game_actions = game_actions.sort_values(["period_id", "time_seconds"])
            game_actions = game_actions.reset_index(drop=True)

            if len(game_actions) < NB_PREV_ACTIONS + 1:
                continue

            # Features
            gamestates = features_module.gamestates(game_actions, nb_prev_actions=NB_PREV_ACTIONS)
            game_features = pd.concat([
                features_module.actiontype(gamestates),
                features_module.result(gamestates),
                features_module.bodypart(gamestates),
                features_module.startlocation(gamestates),
                features_module.endlocation(gamestates),
                features_module.movement(gamestates),
                features_module.space(gamestates),
                features_module.time(gamestates),
                features_module.team(gamestates),
                features_module.time_delta(gamestates),
            ], axis=1)

            # Labels
            scoring = labels_module.scores(game_actions, nr_actions=10)
            conceding = labels_module.concedes(game_actions, nr_actions=10)

            all_features.append(game_features)
            all_labels_scoring.append(scoring)
            all_labels_conceding.append(conceding)
            all_actions.append(game_actions)

        if not all_features:
            raise ValueError("No valid game data after SPADL conversion")

        X = pd.concat(all_features, ignore_index=True)
        y_scoring = pd.concat(all_labels_scoring, ignore_index=True)
        y_conceding = pd.concat(all_labels_conceding, ignore_index=True)
        actions_df = pd.concat(all_actions, ignore_index=True)

        # Step 3: Train or load model
        self._train_models(X, y_scoring, y_conceding)

        # Step 4: Predict
        p_scoring = self.scoring_model.predict_proba(X)[:, 1]
        p_conceding = self.conceding_model.predict_proba(X)[:, 1]

        # Step 5: Compute VAEP values
        actions_df["vaep_offensive"] = np.concatenate([
            [0], p_scoring[1:] - p_scoring[:-1]
        ])
        actions_df["vaep_defensive"] = np.concatenate([
            [0], -(p_conceding[1:] - p_conceding[:-1])
        ])
        actions_df["vaep_value"] = actions_df["vaep_offensive"] + actions_df["vaep_defensive"]

        # Step 6: Aggregate per player
        player_ratings = self._aggregate_ratings(actions_df, season, competition_id)

        # Build action-level output
        action_records = self._build_action_records(actions_df, season, competition_id)

        return {
            "player_ratings": player_ratings,
            "action_records": action_records,
            "total_actions": len(actions_df),
            "total_games": len(game_ids),
            "season": season,
            "method": "full_vaep",
        }

    def _convert_to_spadl(self, df_events: pd.DataFrame) -> pd.DataFrame:
        """Convert Wyscout events to SPADL format."""
        # If already in SPADL format, return as-is
        spadl_required = {"game_id", "period_id", "time_seconds",
                          "type_id", "team_id", "player_id"}
        if spadl_required.issubset(set(df_events.columns)):
            return df_events

        # Manual conversion from Wyscout-like format
        actions = []
        for _, row in df_events.iterrows():
            action_type = WYSCOUT_TO_SPADL_MAP.get(
                str(row.get("type", row.get("event_type", ""))),
                "non_action"
            )
            actions.append({
                "game_id": row.get("match_id", row.get("game_id", 0)),
                "period_id": row.get("period", row.get("period_id", 1)),
                "time_seconds": row.get("time_seconds",
                                        row.get("minute", 0) * 60 + row.get("second", 0)),
                "type_id": spadl.actiontypes.index(action_type)
                if action_type in spadl.actiontypes else 0,
                "type_name": action_type,
                "team_id": row.get("team_id", 0),
                "player_id": row.get("player_id", 0),
                "player_name": row.get("player_name", row.get("Jogador", "")),
                "start_x": float(row.get("x_start", row.get("start_x", 50))),
                "start_y": float(row.get("y_start", row.get("start_y", 50))),
                "end_x": float(row.get("x_end", row.get("end_x", 50))),
                "end_y": float(row.get("y_end", row.get("end_y", 50))),
                "result_id": 1 if row.get("result", row.get("outcome", "")) == "success" else 0,
                "bodypart_id": 0,
            })
        return pd.DataFrame(actions)

    def _train_models(self, X: pd.DataFrame,
                      y_scoring: pd.DataFrame,
                      y_conceding: pd.DataFrame):
        """Train scoring and conceding probability models."""
        # Try to load cached models
        if self._load_models():
            logger.info("Loaded cached VAEP models")
            return

        X_clean = X.fillna(0)

        if HAS_XGBOOST:
            self.scoring_model = XGBClassifier(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                eval_metric="logloss",
                use_label_encoder=False,
                random_state=42,
                n_jobs=-1,
            )
            self.conceding_model = XGBClassifier(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                eval_metric="logloss",
                use_label_encoder=False,
                random_state=42,
                n_jobs=-1,
            )
        elif HAS_SKLEARN:
            self.scoring_model = GradientBoostingClassifier(
                n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42
            )
            self.conceding_model = GradientBoostingClassifier(
                n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42
            )
        else:
            raise RuntimeError("Neither xgboost nor sklearn available for VAEP training")

        y_score_arr = y_scoring.values.ravel() if hasattr(y_scoring, 'values') else y_scoring
        y_conc_arr = y_conceding.values.ravel() if hasattr(y_conceding, 'values') else y_conceding

        logger.info("Training VAEP scoring model on %d samples...", len(X_clean))
        self.scoring_model.fit(X_clean, y_score_arr)

        logger.info("Training VAEP conceding model on %d samples...", len(X_clean))
        self.conceding_model.fit(X_clean, y_conc_arr)

        self._fitted = True
        self._save_models()
        logger.info("VAEP models trained and saved")

    def _save_models(self):
        """Save trained models to disk."""
        try:
            self._model_path.mkdir(parents=True, exist_ok=True)
            with open(self._model_path / "scoring_model.pkl", "wb") as f:
                pickle.dump(self.scoring_model, f)
            with open(self._model_path / "conceding_model.pkl", "wb") as f:
                pickle.dump(self.conceding_model, f)
            logger.info("VAEP models saved to %s", self._model_path)
        except Exception as e:
            logger.warning("Could not save VAEP models: %s", e)

    def _load_models(self) -> bool:
        """Load cached models from disk."""
        try:
            scoring_path = self._model_path / "scoring_model.pkl"
            conceding_path = self._model_path / "conceding_model.pkl"
            if scoring_path.exists() and conceding_path.exists():
                with open(scoring_path, "rb") as f:
                    self.scoring_model = pickle.load(f)
                with open(conceding_path, "rb") as f:
                    self.conceding_model = pickle.load(f)
                self._fitted = True
                return True
        except Exception as e:
            logger.warning("Could not load cached VAEP models: %s", e)
        return False

    # ── Heuristic VAEP (fallback without event data) ──────────────────

    def _run_heuristic_pipeline(self, df_wyscout: pd.DataFrame, season: str,
                                competition_id: int = None) -> Dict[str, Any]:
        """Estimate VAEP ratings from aggregate Wyscout statistics.

        Uses a weighted combination of offensive and defensive metrics
        to approximate VAEP per 90 minutes, calibrated against published
        VAEP distributions from Decroos et al. (2019).
        """
        logger.info("Running heuristic VAEP pipeline for season %s (%d players)",
                     season, len(df_wyscout))

        player_ratings = []
        for _, row in df_wyscout.iterrows():
            player_name = str(row.get("Jogador", row.get("player_name", "Unknown")))
            team = str(row.get("Equipa", row.get("team", "")))
            position = str(row.get("Posição", row.get("position", "")))
            league = str(row.get("liga_tier", row.get("league", "")))
            minutes = self._safe_float(row.get("Minutos jogados", row.get("minutes_played", 0)))

            if minutes < 1:
                continue

            # Offensive VAEP approximation
            goals_p90 = self._safe_float(row.get("Golos per 90", row.get("goals_per90", 0)))
            xg_p90 = self._safe_float(row.get("xG per 90", row.get("xg_per90", 0)))
            assists_p90 = self._safe_float(row.get("Assistências per 90", row.get("assists_per90", 0)))
            xa_p90 = self._safe_float(row.get("xA per 90", row.get("xa_per90", 0)))
            key_passes = self._safe_float(row.get("Passes decisivos per 90",
                                                    row.get("key_passes_per90", 0)))
            prog_passes = self._safe_float(row.get("Passes progressivos per 90",
                                                     row.get("progressive_passes_per90", 0)))
            dribbles = self._safe_float(row.get("Dribles per 90",
                                                  row.get("dribbles_per90", 0)))
            shots_p90 = self._safe_float(row.get("Remates per 90",
                                                   row.get("shots_per90", 0)))
            crosses_p90 = self._safe_float(row.get("Cruzamentos per 90",
                                                     row.get("crosses_per90", 0)))
            touches_box = self._safe_float(row.get("Toques na área per 90",
                                                     row.get("touches_in_box_per90", 0)))

            # Defensive VAEP approximation
            def_actions = self._safe_float(row.get("Ações defensivas per 90",
                                                     row.get("defensive_actions_per90", 0)))
            interceptions = self._safe_float(row.get("Interceções per 90",
                                                       row.get("interceptions_per90", 0)))
            tackles = self._safe_float(row.get("Tackles deslizantes per 90",
                                                 row.get("tackles_per90", 0)))
            aerial_wins = self._safe_float(row.get("Duelos aéreos ganhos, %",
                                                     row.get("aerial_win_pct", 0))) / 100.0
            clearances = self._safe_float(row.get("Cortes per 90",
                                                    row.get("clearances_per90", 0)))

            # VAEP approximation formula
            # Offensive value: weighted sum of goal-contributing actions
            offensive_vaep = (
                goals_p90 * 0.30 +          # Direct goal contribution
                xg_p90 * 0.15 +             # Expected goal quality
                assists_p90 * 0.15 +         # Direct assist contribution
                xa_p90 * 0.10 +             # Expected assist quality
                key_passes * 0.08 +          # Chance creation
                prog_passes * 0.06 +         # Progressive play
                dribbles * 0.04 +            # Ball carrying
                shots_p90 * 0.04 +           # Shot volume
                crosses_p90 * 0.04 +         # Crossing contribution
                touches_box * 0.04           # Presence in danger zone
            )

            # Defensive value: weighted sum of defensive actions
            defensive_vaep = (
                def_actions * 0.25 +
                interceptions * 0.25 +
                tackles * 0.20 +
                aerial_wins * 0.15 +
                clearances * 0.15
            )

            # Scale to approximate real VAEP range (~0.0 to ~1.0 per90 for top players)
            # Calibrated from Decroos et al. (2019): top 10 players ≈ 0.5-0.8 VAEP/90
            offensive_vaep_scaled = offensive_vaep * 0.35
            defensive_vaep_scaled = defensive_vaep * 0.08

            total_vaep_per90 = offensive_vaep_scaled + defensive_vaep_scaled
            total_vaep = total_vaep_per90 * (minutes / 90.0)

            player_ratings.append({
                "player_name": player_name,
                "team": team if team and team != "nan" else None,
                "league": league if league and league != "nan" else None,
                "position": position if position and position != "nan" else None,
                "minutes_played": int(minutes),
                "total_vaep": round(total_vaep, 4),
                "vaep_per90": round(total_vaep_per90, 4),
                "offensive_vaep": round(offensive_vaep_scaled, 4),
                "defensive_vaep": round(defensive_vaep_scaled, 4),
                "actions_count": 0,  # Not available in aggregate data
            })

        # Sort by vaep_per90 descending
        player_ratings.sort(key=lambda x: x["vaep_per90"], reverse=True)

        return {
            "player_ratings": player_ratings,
            "action_records": [],  # No action-level data in heuristic mode
            "total_actions": 0,
            "total_games": 0,
            "season": season,
            "method": "heuristic_vaep",
        }

    # ── Aggregation ───────────────────────────────────────────────────

    def _aggregate_ratings(self, actions_df: pd.DataFrame, season: str,
                           competition_id: int = None) -> List[Dict[str, Any]]:
        """Aggregate VAEP action values to per-player per-90 ratings."""
        if "player_name" not in actions_df.columns:
            actions_df["player_name"] = actions_df.get("player_id", "unknown").astype(str)

        grouped = actions_df.groupby("player_name").agg(
            total_vaep=("vaep_value", "sum"),
            offensive_vaep=("vaep_offensive", "sum"),
            defensive_vaep=("vaep_defensive", "sum"),
            actions_count=("vaep_value", "count"),
        ).reset_index()

        # Estimate minutes from action count (rough: ~1 action per minute on average)
        grouped["minutes_played"] = (grouped["actions_count"] * 1.2).astype(int)
        grouped["vaep_per90"] = np.where(
            grouped["minutes_played"] > 0,
            grouped["total_vaep"] / grouped["minutes_played"] * 90,
            0,
        )

        ratings = []
        for _, row in grouped.iterrows():
            ratings.append({
                "player_name": row["player_name"],
                "team": None,
                "league": None,
                "position": None,
                "minutes_played": int(row["minutes_played"]),
                "total_vaep": round(float(row["total_vaep"]), 4),
                "vaep_per90": round(float(row["vaep_per90"]), 4),
                "offensive_vaep": round(float(row["offensive_vaep"]), 4),
                "defensive_vaep": round(float(row["defensive_vaep"]), 4),
                "actions_count": int(row["actions_count"]),
            })

        ratings.sort(key=lambda x: x["vaep_per90"], reverse=True)
        return ratings

    def _build_action_records(self, actions_df: pd.DataFrame, season: str,
                              competition_id: int = None) -> List[Dict[str, Any]]:
        """Build action-level records for persistence."""
        records = []
        for _, row in actions_df.iterrows():
            records.append({
                "player_name": str(row.get("player_name", "")),
                "match_id": int(row.get("game_id", 0)),
                "action_type": str(row.get("type_name", "")),
                "vaep_value": round(float(row.get("vaep_value", 0)), 6),
                "offensive_value": round(float(row.get("vaep_offensive", 0)), 6),
                "defensive_value": round(float(row.get("vaep_defensive", 0)), 6),
                "x_start": float(row.get("start_x", 0)),
                "y_start": float(row.get("start_y", 0)),
                "x_end": float(row.get("end_x", 0)),
                "y_end": float(row.get("end_y", 0)),
                "minute": int(row.get("time_seconds", 0)) // 60,
                "second": int(row.get("time_seconds", 0)) % 60,
            })
        return records

    # ── Player Lookup ─────────────────────────────────────────────────

    def get_player_vaep(self, player_name: str, df_wyscout: pd.DataFrame,
                        season: str = None) -> Optional[Dict[str, Any]]:
        """Get VAEP data for a specific player.

        Tries database first, falls back to heuristic calculation.
        """
        # Try database
        try:
            from services.database import load_vaep_player
            db_data = load_vaep_player(player_name, season)
            if db_data:
                return db_data
        except Exception as e:
            logger.debug("Could not load VAEP from DB for %s: %s", player_name, e)

        # Heuristic fallback from Wyscout data
        if df_wyscout is None or len(df_wyscout) == 0:
            return None

        # Find player in Wyscout data
        player_col = "Jogador" if "Jogador" in df_wyscout.columns else "player_name"
        mask = df_wyscout[player_col].str.strip().str.lower() == player_name.strip().lower()
        if not mask.any():
            return None

        player_df = df_wyscout[mask].head(1)
        result = self._run_heuristic_pipeline(player_df, season or "current")
        if result["player_ratings"]:
            return result["player_ratings"][0]
        return None

    def get_player_comparison(self, player_names: List[str],
                              df_wyscout: pd.DataFrame,
                              season: str = None) -> List[Dict[str, Any]]:
        """Get VAEP comparison data for multiple players."""
        results = []
        for name in player_names:
            data = self.get_player_vaep(name, df_wyscout, season)
            if data:
                results.append(data)
        return results

    # ── Utilities ─────────────────────────────────────────────────────

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
