"""
Pandera data contracts for the Scouting Dashboard.

Validates DataFrames loaded from 4 Google Sheets:
  - Análises
  - Oferecidos
  - SkillCorner
  - WyScout

Uses pandera DataFrameSchema objects for validation and pydantic BaseModel
for application configuration.
"""

from __future__ import annotations

import logging
from typing import Dict

import pandas as pd
import pandera as pa
from pandera import Check, Column, DataFrameSchema
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. Análises
# ---------------------------------------------------------------------------

AnaliseSchema = DataFrameSchema(
    columns={
        "Nome": Column(pa.String, nullable=False, required=True),
        "Posição": Column(pa.String, nullable=False, required=True),
        "Clube": Column(pa.String, nullable=True, required=False),
        "Liga": Column(pa.String, nullable=True, required=False),
        "Idade": Column(
            pa.Int,
            checks=Check.in_range(14, 50),
            nullable=True,
            coerce=True,
            required=False,
        ),
        "Ano": Column(pa.Int, nullable=True, coerce=True, required=False),
        "Nacionalidade": Column(pa.String, nullable=True, required=False),
        # Evaluation scores (0-10)
        "Técnica": Column(
            pa.Float,
            checks=Check.in_range(0, 10),
            nullable=True,
            coerce=True,
            required=False,
        ),
        "Físico": Column(
            pa.Float,
            checks=Check.in_range(0, 10),
            nullable=True,
            coerce=True,
            required=False,
        ),
        "Tática": Column(
            pa.Float,
            checks=Check.in_range(0, 10),
            nullable=True,
            coerce=True,
            required=False,
        ),
        "Mental": Column(
            pa.Float,
            checks=Check.in_range(0, 10),
            nullable=True,
            coerce=True,
            required=False,
        ),
        "Nota_Desempenho": Column(
            pa.Float,
            checks=Check.in_range(0, 10),
            nullable=True,
            coerce=True,
            required=False,
        ),
        "Potencial": Column(
            pa.Float,
            checks=Check.in_range(0, 10),
            nullable=True,
            coerce=True,
            required=False,
        ),
        # URL / link fields
        "ogol": Column(pa.String, nullable=True, required=False),
        "TM": Column(pa.String, nullable=True, required=False),
        # Free-text / optional fields
        "Vídeo": Column(pa.String, nullable=True, required=False),
        "Relatório": Column(pa.String, nullable=True, required=False),
        "Foto": Column(pa.String, nullable=True, required=False),
        "Modelo": Column(pa.String, nullable=True, required=False),
        "Perfil": Column(pa.String, nullable=True, required=False),
        "Contrato": Column(pa.String, nullable=True, required=False),
    },
    # Allow extra columns that are not declared above.
    strict=False,
    coerce=True,
    name="AnaliseSchema",
)

# ---------------------------------------------------------------------------
# 2. WyScout
# ---------------------------------------------------------------------------

# Text columns that must NOT be coerced to numeric.
_WYSCOUT_TEXT_COLUMNS = {
    "Jogador",
    "Equipa",
    "Posição",
    "Naturalidade",
    "Pé",
    "Liga",
    "Competição",
    "JogadorDisplay",
}

WyScoutSchema = DataFrameSchema(
    columns={
        "Jogador": Column(pa.String, nullable=False, required=True),
        "Equipa": Column(pa.String, nullable=True, required=False),
        "Posição": Column(pa.String, nullable=True, required=False),
        "Idade": Column(pa.Float, nullable=True, coerce=True, required=False),
        "Naturalidade": Column(pa.String, nullable=True, required=False),
        "Pé": Column(pa.String, nullable=True, required=False),
        "Liga": Column(pa.String, nullable=True, required=False),
        "Competição": Column(pa.String, nullable=True, required=False),
        "JogadorDisplay": Column(pa.String, nullable=True, required=False),
    },
    # Allow extra (numeric) columns that are not declared above.
    strict=False,
    coerce=True,
    name="WyScoutSchema",
)

# ---------------------------------------------------------------------------
# 3. SkillCorner
# ---------------------------------------------------------------------------

_SKILLCORNER_INDEX_COLUMNS = [
    "Direct striker index",
    "Link up striker index",
    "Inverted winger index",
    "Wide winger index",
    "Dynamic number 8 index",
    "Box to box midfielder index",
    "Number 6 index",
    "Intense full back index",
    "Technical full back index",
    "Physical & aggressive defender index",
    "Ball playing central defender index",
]

_SKILLCORNER_PHYSICAL_COLUMNS = [
    "sprint_count_per_90",
    "hi_count_per_90",
    "distance_per_90",
    "avg_psv99",
    "avg_top_5_psv99",
]

_skillcorner_columns: Dict[str, Column] = {
    "player_name": Column(pa.String, nullable=False, required=True),
    "short_name": Column(pa.String, nullable=True, required=False),
    "team_name": Column(pa.String, nullable=True, required=False),
    "position_group": Column(pa.String, nullable=True, required=False),
}

for _col in _SKILLCORNER_INDEX_COLUMNS + _SKILLCORNER_PHYSICAL_COLUMNS:
    _skillcorner_columns[_col] = Column(
        pa.Float, nullable=True, coerce=True, required=False
    )

SkillCornerSchema = DataFrameSchema(
    columns=_skillcorner_columns,
    strict=False,
    coerce=True,
    name="SkillCornerSchema",
)

# ---------------------------------------------------------------------------
# 4. Oferecidos
# ---------------------------------------------------------------------------

OferecidosSchema = DataFrameSchema(
    columns={
        "Nome": Column(pa.String, nullable=False, required=True),
    },
    # All other columns are nullable strings; allow them through.
    strict=False,
    coerce=True,
    name="OferecidosSchema",
)

# ---------------------------------------------------------------------------
# 5. Application configuration (pydantic)
# ---------------------------------------------------------------------------


class AppConfig(BaseModel):
    """Runtime configuration for the Scouting Dashboard application."""

    google_sheet_id: str
    admin_default_password: str = "botafogo2024"
    database_url: str | None = None
    auth_db_path: str = "users.db"


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------


def validate_dataframes(
    df_analises: pd.DataFrame,
    df_oferecidos: pd.DataFrame,
    df_skillcorner: pd.DataFrame,
    df_wyscout: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validate the four DataFrames against their schemas.

    Validation is **informational only** -- failures are logged as warnings
    and the original DataFrames are returned unchanged so that downstream
    processing is never blocked by schema mismatches.

    Parameters
    ----------
    df_analises : pd.DataFrame
        Data from the "Análises" sheet.
    df_oferecidos : pd.DataFrame
        Data from the "Oferecidos" sheet.
    df_skillcorner : pd.DataFrame
        Data from the "SkillCorner" sheet.
    df_wyscout : pd.DataFrame
        Data from the "WyScout" sheet.

    Returns
    -------
    tuple of four pd.DataFrame
        The same DataFrames passed in (unmodified).
    """
    schemas = [
        ("Análises", AnaliseSchema, df_analises),
        ("Oferecidos", OferecidosSchema, df_oferecidos),
        ("SkillCorner", SkillCornerSchema, df_skillcorner),
        ("WyScout", WyScoutSchema, df_wyscout),
    ]

    for sheet_name, schema, df in schemas:
        try:
            schema.validate(df, lazy=True)
            logger.info("Schema validation passed for '%s'.", sheet_name)
        except pa.errors.SchemaErrors as exc:
            logger.warning(
                "Schema validation warnings for '%s':\n%s",
                sheet_name,
                exc.failure_cases.to_string(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Unexpected error validating '%s': %s", sheet_name, exc
            )

    return df_analises, df_oferecidos, df_skillcorner, df_wyscout
