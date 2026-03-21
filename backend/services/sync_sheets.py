"""
sync_sheets.py — Sync Google Sheets → Neon PostgreSQL.
Pulls CSV exports from Google Sheets and upserts into the database.
Can be run as a standalone script (cron) or triggered via API endpoint.
"""

import os
import io
import logging
import urllib.parse
import urllib.request
from typing import Dict

import pandas as pd

from services.database import init_scouting_tables, upsert_sheet_data, get_sync_status

logger = logging.getLogger(__name__)

GOOGLE_SHEET_ID = os.environ.get(
    "GOOGLE_SHEET_ID", "1aRjJAxYHJED4FyPnq4PfcrzhhRhzw-vNQ9Vg1pIlak0"
)

SHEET_NAMES = {
    "analises": "Análises",
    "oferecidos": "Oferecidos",
    "skillcorner": "SkillCorner",
    "wyscout": "WyScout",
}


def _download_sheet_csv(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    """Download a single Google Sheet tab as CSV → DataFrame."""
    encoded = urllib.parse.quote(sheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(raw), dtype=str, na_values=["", "-", "N/A", "nan"])
        logger.info("Downloaded sheet '%s': %d rows x %d cols", sheet_name, len(df), len(df.columns))
        return df
    except Exception as e:
        logger.error("Failed to download sheet '%s': %s", sheet_name, e)
        return pd.DataFrame()


def sync_all_sheets() -> Dict[str, int]:
    """Sync all sheets from Google Sheets → Neon PostgreSQL.
    Returns dict of {sheet_key: row_count}.
    """
    init_scouting_tables()

    results = {}
    for key, sheet_name in SHEET_NAMES.items():
        try:
            df = _download_sheet_csv(GOOGLE_SHEET_ID, sheet_name)
            count = upsert_sheet_data(key, df)
            results[key] = count
        except Exception as e:
            logger.error("Sync failed for '%s': %s", key, e)
            results[key] = -1

    logger.info("Sync complete: %s", results)
    return results


def sync_single_sheet(sheet_key: str) -> int:
    """Sync a single sheet by key."""
    init_scouting_tables()

    sheet_name = SHEET_NAMES.get(sheet_key)
    if not sheet_name:
        raise ValueError(f"Unknown sheet key: {sheet_key}")

    df = _download_sheet_csv(GOOGLE_SHEET_ID, sheet_name)
    return upsert_sheet_data(sheet_key, df)


# Allow running as standalone: python -m services.sync_sheets
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = sync_all_sheets()
    print(f"Sync results: {results}")
    status = get_sync_status()
    print(f"Sync status: {status}")
