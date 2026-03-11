"""
jobs/run_pipeline.py — Pipeline offline de ETL e treinamento de modelos.

Execução: python -m jobs.run_pipeline [--output-dir data/]

Etapas:
    1. Pull dados do Google Sheets (Análises, Oferecidos, SkillCorner, WyScout)
    2. Validação com pandera (schemas/data_schemas.py)
    3. Pré-processamento: limpeza, normalização, conversão numérica
    4. Mapeamento de ligas (CLUB_LEAGUE_MAP + WYSCOUT_LEAGUE_MAP)
    5. Fuzzy match WyScout ↔ SkillCorner
    6. Treinamento por posição: SSP (PCA + KMeans + RF)
    7. Clusterização tática (KMeans + GMM)
    8. Exportação em .parquet para consumo pelo app.py
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from urllib.parse import quote

import pandas as pd

# Adicionar raiz do projeto ao path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from config.mappings import (
    CLUB_LEAGUE_MAP,
    POSICAO_MAP,
    WYSCOUT_LEAGUE_MAP,
    normalize_name,
    padronizar_string,
    resolve_league_to_tier,
)
from fuzzy_match import build_skillcorner_index, find_skillcorner_player

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline")

# Google Sheet ID padrão
_DEFAULT_SHEET_ID = "1aRjJAxYHJED4FyPnq4PfcrzhhRhzw-vNQ9Vg1pIlak0"


# ============================================
# 1. EXTRAÇÃO (Google Sheets)
# ============================================

def pull_google_sheets(sheet_id: str | None = None) -> dict[str, pd.DataFrame]:
    """Baixa as 4 abas do Google Sheets como DataFrames."""
    sid = sheet_id or os.environ.get("GOOGLE_SHEET_ID", _DEFAULT_SHEET_ID)
    names = ["Análises", "Oferecidos", "SkillCorner", "WyScout"]
    frames = {}

    for name in names:
        url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={quote(name)}"
        logger.info("Baixando aba '%s'...", name)
        try:
            frames[name] = pd.read_csv(url)
            logger.info("  → %d linhas, %d colunas", *frames[name].shape)
        except Exception as e:
            logger.error("Falha ao baixar '%s': %s", name, e)
            raise

    return frames


# ============================================
# 2. PRÉ-PROCESSAMENTO
# ============================================

def _coerce_numeric(df: pd.DataFrame, exclude_cols: list[str]) -> pd.DataFrame:
    """Converte todas as colunas exceto `exclude_cols` para numérico."""
    for col in df.columns:
        if col not in exclude_cols:
            df[col] = (
                df[col]
                .apply(lambda x: str(x).replace(",", ".") if pd.notna(x) and isinstance(x, str) else x)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def preprocess(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Limpeza e conversão numérica dos 4 DataFrames."""
    wyscout = frames["WyScout"].copy()
    skillcorner = frames["SkillCorner"].copy()
    analises = frames["Análises"].copy()
    oferecidos = frames["Oferecidos"].copy()

    # --- WyScout ---
    ws_text = [
        "Jogador", "Equipa", "Equipa dentro de um período de tempo seleccionado",
        "Posição", "Naturalidade", "País de nacionalidade", "Pé", "Emprestado",
        "JogadorDisplay", "Liga", "Competição", "Competition", "League", "Comp",
    ]
    wyscout = _coerce_numeric(wyscout, ws_text)

    # Display names
    wyscout["JogadorDisplay"] = wyscout.apply(
        lambda r: f"{r['Jogador']} ({r['Equipa']})" if pd.notna(r.get("Equipa")) else r["Jogador"],
        axis=1,
    )
    dup = wyscout["JogadorDisplay"].duplicated(keep=False)
    if dup.any():
        wyscout.loc[dup, "JogadorDisplay"] = wyscout.loc[dup].apply(
            lambda r: f"{r['Jogador']} ({r['Equipa']}, {int(r['Idade'])}a)"
            if pd.notna(r.get("Idade")) else f"{r['Jogador']} ({r['Equipa']}, {r['Posição']})",
            axis=1,
        )

    # --- SkillCorner ---
    sc_text = [
        "player_id", "player_name", "short_name", "birthday",
        "team_id", "team_name", "competition_edition_id", "competition_edition_name",
        "competition_id", "competition_name", "season_id", "season_name",
        "position_group", "position_group_detailed", "data_point_id", "PlayerDisplay",
    ]
    skillcorner = _coerce_numeric(skillcorner, sc_text)
    skillcorner["PlayerDisplay"] = skillcorner.apply(
        lambda r: f"{r['player_name']} ({r['team_name']})"
        if pd.notna(r.get("team_name")) else r["player_name"],
        axis=1,
    )

    # --- Análises ---
    num_an = ["Idade", "Ano", "Técnica", "Físico", "Tática", "Mental", "Nota_Desempenho", "Potencial"]
    for col in num_an:
        if col in analises.columns:
            analises[col] = analises[col].apply(
                lambda x: str(x).replace(",", ".") if pd.notna(x) and isinstance(x, str) else x
            )
            analises[col] = pd.to_numeric(analises[col], errors="coerce")

    return {
        "WyScout": wyscout,
        "SkillCorner": skillcorner,
        "Análises": analises,
        "Oferecidos": oferecidos,
    }


# ============================================
# 3. MAPEAMENTO DE LIGAS
# ============================================

def map_leagues(wyscout: pd.DataFrame) -> pd.DataFrame:
    """Adiciona coluna 'liga_tier' com o tier numérico de cada jogador."""
    def _resolve_tier(row):
        # 1) Coluna Liga do WyScout
        liga = row.get("Liga") or row.get("Competição") or row.get("Competition")
        if pd.notna(liga) and str(liga).strip():
            liga_str = str(liga).strip()
            if liga_str in WYSCOUT_LEAGUE_MAP:
                return resolve_league_to_tier(WYSCOUT_LEAGUE_MAP[liga_str])

        # 2) CLUB_LEAGUE_MAP
        equipa = row.get("Equipa")
        if pd.notna(equipa):
            equipa_str = str(equipa).strip()
            if equipa_str in CLUB_LEAGUE_MAP:
                return resolve_league_to_tier(CLUB_LEAGUE_MAP[equipa_str])

        return 5.0  # default

    wyscout["liga_tier"] = wyscout.apply(_resolve_tier, axis=1)
    logger.info("Ligas mapeadas — distribuição de tiers:\n%s", wyscout["liga_tier"].value_counts().to_string())
    return wyscout


# ============================================
# 4. FUZZY MATCH WyScout ↔ SkillCorner
# ============================================

def link_skillcorner(wyscout: pd.DataFrame, skillcorner: pd.DataFrame) -> pd.DataFrame:
    """Adiciona coluna 'sc_player_name' com o match do SkillCorner."""
    logger.info("Construindo índice SkillCorner...")
    build_skillcorner_index(skillcorner)

    matched = 0
    sc_names = []

    for _, row in wyscout.iterrows():
        jogador = row.get("Jogador", "")
        team = row.get("Equipa", "")
        result = find_skillcorner_player(jogador, skillcorner, team_name=team)
        if result is not None:
            sc_names.append(result.get("player_name", ""))
            matched += 1
        else:
            sc_names.append(None)

    wyscout["sc_player_name"] = sc_names
    logger.info("Fuzzy match: %d/%d jogadores linkados (%.1f%%)", matched, len(wyscout), matched / max(len(wyscout), 1) * 100)
    return wyscout


# ============================================
# 5. TREINAMENTO DE MODELOS (SSP + Clusters)
# ============================================

def train_models(wyscout: pd.DataFrame) -> dict:
    """Treina SSP e TacticalClusterer por posição. Retorna artefatos."""
    try:
        from predictive_engine import ScoutScorePreditivo, TacticalClusterer
    except ImportError:
        logger.warning("predictive_engine não disponível — pulando treinamento")
        return {}

    from config.mappings import POSICAO_MAP

    artifacts = {}
    positions = ["Atacante", "Extremo", "Meia", "Volante", "Lateral", "Zagueiro"]

    def _get_cat(pos_str):
        if pd.isna(pos_str):
            return None
        for pos in str(pos_str).replace(" ", "").split(","):
            if pos in POSICAO_MAP:
                return POSICAO_MAP[pos]
        return None

    for position in positions:
        df_pos = wyscout[wyscout["Posição"].apply(_get_cat) == position].copy()
        if len(df_pos) < 15:
            logger.warning("Posição '%s': apenas %d jogadores (mín 15) — pulando", position, len(df_pos))
            continue

        logger.info("Treinando SSP para '%s' (%d jogadores)...", position, len(df_pos))
        try:
            engine = ScoutScorePreditivo()
            engine.fit(df=df_pos, position=position, min_minutes=500, pos_col="_prefiltrado_")
            artifacts[f"ssp_{position}"] = engine
            logger.info("  → SSP '%s' treinado com sucesso", position)
        except Exception as e:
            logger.error("  → Falha no SSP '%s': %s", position, e)

        try:
            clusterer = TacticalClusterer()
            clusterer.fit(df_pos, position=position)
            artifacts[f"cluster_{position}"] = clusterer
            logger.info("  → Clusters '%s' treinados", position)
        except Exception as e:
            logger.error("  → Falha nos clusters '%s': %s", position, e)

    return artifacts


# ============================================
# 6. EXPORTAÇÃO (.parquet)
# ============================================

def export_parquet(frames: dict[str, pd.DataFrame], output_dir: str):
    """Salva DataFrames processados em formato Parquet."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for name, df in frames.items():
        path = out / f"{name.lower().replace(' ', '_')}.parquet"
        df.to_parquet(path, index=False, engine="pyarrow")
        logger.info("Exportado %s → %s (%d linhas)", name, path, len(df))


# ============================================
# MAIN
# ============================================

def run(sheet_id: str | None = None, output_dir: str = "data"):
    """Executa pipeline completo."""
    logger.info("=" * 60)
    logger.info("PIPELINE DE SCOUTING — INÍCIO")
    logger.info("=" * 60)

    # 1. Extração
    raw = pull_google_sheets(sheet_id)

    # 2. Pré-processamento
    processed = preprocess(raw)

    # 3. Validação (opcional — schemas)
    try:
        from schemas.data_schemas import validate_dataframes
        validate_dataframes(
            processed["Análises"],
            processed["Oferecidos"],
            processed["SkillCorner"],
            processed["WyScout"],
        )
    except ImportError:
        logger.info("schemas.data_schemas não disponível — pulando validação")

    # 4. Mapeamento de ligas
    processed["WyScout"] = map_leagues(processed["WyScout"])

    # 5. Fuzzy match
    processed["WyScout"] = link_skillcorner(processed["WyScout"], processed["SkillCorner"])

    # 6. Treinamento
    train_models(processed["WyScout"])

    # 7. Exportação
    export_parquet(processed, output_dir)

    logger.info("=" * 60)
    logger.info("PIPELINE CONCLUÍDO")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline offline de Scouting")
    parser.add_argument("--sheet-id", default=None, help="Google Sheet ID")
    parser.add_argument("--output-dir", default="data", help="Diretório de saída para .parquet")
    args = parser.parse_args()

    run(sheet_id=args.sheet_id, output_dir=args.output_dir)
