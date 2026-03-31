"""
sync_sheets.py — Sync Google Sheets → Neon PostgreSQL.
Pulls data from Google Sheets (via Service Account API or public CSV fallback)
and upserts into the database.
Can be run as a standalone script (cron) or triggered via API endpoint.
"""

import os
import io
import json
import base64
import logging
import urllib.parse
import urllib.request
from typing import Dict, Optional

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
    "treinadores_perfil": "Treinadores_Perfil",
    "treinadores_historico": "Treinadores_Histórico",
}

# ---------- Google Sheets API (Service Account) ----------

_sheets_service = None


def _get_sheets_service():
    """Build and cache an authenticated Google Sheets API service."""
    global _sheets_service
    if _sheets_service is not None:
        return _sheets_service

    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    creds_raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not creds_raw:
        return None

    # Accept raw JSON or base64-encoded JSON
    try:
        creds_info = json.loads(creds_raw)
    except json.JSONDecodeError:
        creds_info = json.loads(base64.b64decode(creds_raw))

    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    _sheets_service = build("sheets", "v4", credentials=creds)
    logger.info("Google Sheets API service initialized with Service Account")
    return _sheets_service


def _download_sheet_api(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    """Download a sheet tab via Google Sheets API (authenticated)."""
    service = _get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=sheet_name,
    ).execute()

    values = result.get("values", [])
    if not values:
        return pd.DataFrame()

    # First row = headers, rest = data
    headers = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)
    df = df.astype(str)
    df = df.replace({"": pd.NA, "-": pd.NA, "N/A": pd.NA, "nan": pd.NA})
    logger.info("Downloaded sheet '%s' via API: %d rows x %d cols", sheet_name, len(df), len(df.columns))
    return df


def _download_sheet_csv(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    """Download a single Google Sheet tab as CSV (public, no auth)."""
    encoded = urllib.parse.quote(sheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(raw), dtype=str, na_values=["", "-", "N/A", "nan"])
        logger.info("Downloaded sheet '%s' via public CSV: %d rows x %d cols", sheet_name, len(df), len(df.columns))
        return df
    except Exception as e:
        logger.error("Failed to download sheet '%s': %s", sheet_name, e)
        return pd.DataFrame()


def _download_sheet(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    """Download a sheet tab — uses API if Service Account is configured, else public CSV."""
    if _get_sheets_service() is not None:
        return _download_sheet_api(sheet_id, sheet_name)
    logger.warning("GOOGLE_SERVICE_ACCOUNT_JSON not set — falling back to public CSV export")
    return _download_sheet_csv(sheet_id, sheet_name)


def sync_all_sheets() -> Dict[str, int]:
    """Sync all sheets from Google Sheets → Neon PostgreSQL.
    Returns dict of {sheet_key: row_count}.
    """
    init_scouting_tables()

    results = {}
    for key, sheet_name in SHEET_NAMES.items():
        try:
            df = _download_sheet(GOOGLE_SHEET_ID, sheet_name)
            count = upsert_sheet_data(key, df)
            results[key] = count
        except Exception as e:
            logger.error("Sync failed for '%s': %s", key, e)
            results[key] = -1

    logger.info("Sync complete: %s", results)
    return results


def sync_coach_sheets() -> Dict[str, int]:
    """Sync coach-related sheets from Google Sheets → Neon PostgreSQL."""
    init_scouting_tables()

    coach_keys = ["treinadores_perfil", "treinadores_historico"]
    results = {}
    for key in coach_keys:
        try:
            sheet_name = SHEET_NAMES[key]
            df = _download_sheet(GOOGLE_SHEET_ID, sheet_name)
            count = upsert_sheet_data(key, df)
            results[key] = count
        except Exception as e:
            logger.error("Sync failed for '%s': %s", key, e)
            results[key] = -1

    logger.info("Coach sync complete: %s", results)
    return results


def sync_single_sheet(sheet_key: str) -> int:
    """Sync a single sheet by key."""
    init_scouting_tables()

    sheet_name = SHEET_NAMES.get(sheet_key)
    if not sheet_name:
        raise ValueError(f"Unknown sheet key: {sheet_key}")

    df = _download_sheet(GOOGLE_SHEET_ID, sheet_name)
    return upsert_sheet_data(sheet_key, df)


# Allow running as standalone: python -m services.sync_sheets
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = sync_all_sheets()
    print(f"Sync results: {results}")
    status = get_sync_status()
    print(f"Sync status: {status}")
