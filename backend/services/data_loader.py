"""
data_loader.py — Carregamento seguro de CSVs do SkillCorner
Botafogo FSA Scouting Pipeline
"""

import pandas as pd
import numpy as np
import re
from typing import List, Optional


NUMERIC_COLS_SKILLCORNER = [
    "sprint_count_per_90",
    "high_speed_running_distance_per_90",
    "psv_99_per_90",
    "distance_per_90",
    "high_intensity_runs_per_90",
    "pressing_index_per_90",
    "deep_completions_per_90",
    "smart_passes_per_90",
    "accelerations_per_90",
    "decelerations_per_90",
    "max_speed",
    "avg_speed",
]

TM_PATTERN = re.compile(
    r'^https://(www\.)?transfermarkt\.(com\.br|com|pt|de)/.+/profil/spieler/\d+$'
)
OGOL_PATTERN = re.compile(
    r'^https://(www\.)?(ogol\.com\.br|zerozero\.pt)/jogador/.+'
)


def load_skillcorner_csv(
    filepath: str,
    extra_numeric_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Carrega CSV do SkillCorner forçando tipagem correta."""
    df = pd.read_csv(filepath, dtype=str, na_values=["", "-", "N/A", "nan"])

    all_numeric = NUMERIC_COLS_SKILLCORNER.copy()
    if extra_numeric_cols:
        all_numeric.extend(extra_numeric_cols)

    for col in all_numeric:
        if col in df.columns:
            df[col] = (
                df[col]
                .str.strip()
                .str.replace(",", ".", regex=False)
                .str.replace(r"[^\d.\-]", "", regex=True)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def safe_numeric_cast(series: pd.Series) -> pd.Series:
    if series.dtype in [np.float64, np.int64, float, int]:
        return series
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(",", ".", regex=False)
        .str.replace(r"[^\d.\-]", "", regex=True)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def downcast_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Convert float64 → float32 and int64 → int32 columns in place.

    Halves the memory footprint of player/event DataFrames (~50% saving on
    the wide WyScout frame) without changing values for typical scouting
    metrics. Returns the same DataFrame for chainable use.
    """
    if df is None or len(df) == 0:
        return df
    float64_cols = df.select_dtypes(include=["float64"]).columns
    if len(float64_cols) > 0:
        df[float64_cols] = df[float64_cols].astype(np.float32)
    int64_cols = df.select_dtypes(include=["int64"]).columns
    if len(int64_cols) > 0:
        df[int64_cols] = df[int64_cols].astype(np.int32)
    return df


def validate_url(url: str, pattern: re.Pattern) -> bool:
    if not url or not isinstance(url, str):
        return False
    return bool(pattern.match(url.strip()))
