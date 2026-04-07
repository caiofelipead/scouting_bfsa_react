"""
fm_sortitoutsi.py -- CDN lookup for sortitoutsi cut-out faces and logos.

Loads pre-built FM UID mapping CSVs (generated via Typesense/fmref.com)
and returns direct CDN URLs for player faces and team logos.

CDN pattern:
  Faces: https://sortitoutsi.b-cdn.net/uploads/face/face_{fm_id}.png
  Logos: https://sortitoutsi.b-cdn.net/uploads/logo/logo_{fm_id}.png
"""

import csv
import logging
import os
import re
import unicodedata
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_face_urls: Dict[str, str] = {}
_logo_urls: Dict[str, str] = {}
_face_urls_by_name_team: Dict[tuple, str] = {}
_loaded = False

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)


def _normalize(name: str) -> str:
    if not name:
        return ""
    name = unicodedata.normalize("NFD", str(name))
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^a-z0-9\s]", "", name.lower())
    return " ".join(name.split())


def load_fm_mappings():
    global _loaded
    if _loaded:
        return

    players_csv = os.path.join(_DATA_DIR, "fm_mapping_jogadores.csv")
    teams_csv = os.path.join(_DATA_DIR, "fm_mapping_times.csv")

    if os.path.exists(players_csv):
        try:
            with open(players_csv, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    wyscout_name = row.get("wyscout_name", "").strip()
                    face_url = row.get("face_url", "").strip()
                    score = int(row.get("match_score", "0"))
                    teams = row.get("wyscout_teams", "")
                    if not wyscout_name or not face_url or score < 70:
                        continue
                    name_key = _normalize(wyscout_name)
                    if not name_key:
                        continue
                    if name_key not in _face_urls:
                        _face_urls[name_key] = face_url
                    for team in teams.split("|"):
                        team = team.strip()
                        if team:
                            pair = (name_key, _normalize(team))
                            if pair not in _face_urls_by_name_team:
                                _face_urls_by_name_team[pair] = face_url
            logger.info(
                "FM sortitoutsi: %d faces (%d with team)",
                len(_face_urls), len(_face_urls_by_name_team),
            )
        except Exception as e:
            logger.error("Failed to load FM player mappings: %s", e)

    if os.path.exists(teams_csv):
        try:
            with open(teams_csv, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    wyscout_name = row.get("wyscout_name", "").strip()
                    logo_url = row.get("logo_url", "").strip()
                    score = int(row.get("match_score", "0"))
                    if not wyscout_name or not logo_url or score < 70:
                        continue
                    name_key = _normalize(wyscout_name)
                    if name_key and name_key not in _logo_urls:
                        _logo_urls[name_key] = logo_url
            logger.info("FM sortitoutsi: %d logos", len(_logo_urls))
        except Exception as e:
            logger.error("Failed to load FM team mappings: %s", e)

    _loaded = True


def _ensure_loaded():
    if not _loaded:
        load_fm_mappings()


def get_face_url(player_name: str, team: str = None) -> Optional[str]:
    _ensure_loaded()
    name_key = _normalize(player_name)
    if not name_key:
        return None
    if team:
        url = _face_urls_by_name_team.get((name_key, _normalize(team)))
        if url:
            return url
    return _face_urls.get(name_key)


def get_logo_url(team_name: str) -> Optional[str]:
    _ensure_loaded()
    name_key = _normalize(team_name)
    return _logo_urls.get(name_key) if name_key else None


def get_stats() -> dict:
    _ensure_loaded()
    return {
        "faces": len(_face_urls),
        "faces_with_team": len(_face_urls_by_name_team),
        "logos": len(_logo_urls),
    }
