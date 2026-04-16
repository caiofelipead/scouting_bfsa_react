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
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from rapidfuzz import fuzz, process  # type: ignore
    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False

_face_urls: Dict[str, str] = {}
_logo_urls: Dict[str, str] = {}
_face_urls_by_name_team: Dict[tuple, str] = {}
# Fuzzy search index: list of (normalized_name, face_url). Populated alongside _face_urls.
_face_name_choices: List[str] = []
_logo_name_choices: List[str] = []
_loaded = False

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)

# Minimum rapidfuzz score (0-100) for fuzzy lookups. Tight enough to avoid
# false positives on short names like single surnames.
_FUZZY_MIN_SCORE = 88


def _normalize(name: str) -> str:
    if not name:
        return ""
    name = unicodedata.normalize("NFD", str(name))
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^a-z0-9\s]", "", name.lower())
    return " ".join(name.split())


def _index_face(name: str, face_url: str, team: Optional[str] = None) -> None:
    """Add a name→face entry to the primary index (first write wins)."""
    key = _normalize(name)
    if not key or not face_url:
        return
    if key not in _face_urls:
        _face_urls[key] = face_url
    if team:
        pair = (key, _normalize(team))
        if pair[1] and pair not in _face_urls_by_name_team:
            _face_urls_by_name_team[pair] = face_url


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
                    face_url = row.get("face_url", "").strip()
                    score = int(row.get("match_score", "0") or 0)
                    if not face_url or score < 70:
                        continue
                    wyscout_name = row.get("wyscout_name", "").strip()
                    search_name = row.get("search_name", "").strip()
                    fm_name = row.get("fm_name", "").strip()
                    teams = row.get("wyscout_teams", "") or ""
                    fm_team = row.get("fm_team", "").strip()

                    # Index under every known alias so a lookup by the WyScout
                    # short name, the SofaScore full name, or the FM database
                    # name all resolve to the same CDN URL.
                    team_list = [t.strip() for t in teams.split("|") if t.strip()]
                    if fm_team:
                        team_list.append(fm_team)

                    for alias in (wyscout_name, search_name, fm_name):
                        if not alias:
                            continue
                        if team_list:
                            for team in team_list:
                                _index_face(alias, face_url, team)
                        else:
                            _index_face(alias, face_url)

            _face_name_choices[:] = list(_face_urls.keys())
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
                    logo_url = row.get("logo_url", "").strip()
                    score = int(row.get("match_score", "0") or 0)
                    if not logo_url or score < 70:
                        continue
                    for alias in (row.get("wyscout_name", ""), row.get("fm_name", "")):
                        alias = alias.strip()
                        key = _normalize(alias)
                        if key and key not in _logo_urls:
                            _logo_urls[key] = logo_url
            _logo_name_choices[:] = list(_logo_urls.keys())
            logger.info("FM sortitoutsi: %d logos", len(_logo_urls))
        except Exception as e:
            logger.error("Failed to load FM team mappings: %s", e)

    _loaded = True


def _ensure_loaded():
    if not _loaded:
        load_fm_mappings()


def _fuzzy_lookup(name_key: str, choices: List[str], table: Dict[str, str]) -> Optional[str]:
    """Fuzzy fallback: used when no exact/normalized match exists."""
    if not _HAS_RAPIDFUZZ or not name_key or not choices:
        return None
    # Skip fuzzy for very short names (single surname) to avoid false positives.
    if len(name_key) < 6 or " " not in name_key:
        return None
    result = process.extractOne(name_key, choices, scorer=fuzz.token_sort_ratio)
    if result and result[1] >= _FUZZY_MIN_SCORE:
        return table.get(result[0])
    return None


def get_face_url(
    player_name: str,
    team: Optional[str] = None,
    alt_names: Optional[Iterable[str]] = None,
) -> Optional[str]:
    """Look up the sortitoutsi face URL for a player.

    Tries, in order:
      1. (name, team) pair match for the primary name and any alt_names.
      2. Name-only match for the primary name and any alt_names.
      3. Fuzzy token-sort match against the full index (multi-word names only).

    `alt_names` lets callers supply alternative names for the same player
    (e.g. the SofaScore full name when the primary is an abbreviated
    WyScout name). The first match wins.
    """
    _ensure_loaded()
    names = [player_name]
    if alt_names:
        names.extend(n for n in alt_names if n)

    team_norm = _normalize(team) if team else ""
    primary_key = _normalize(player_name) if player_name else ""

    if team_norm:
        for n in names:
            key = _normalize(n)
            if not key:
                continue
            url = _face_urls_by_name_team.get((key, team_norm))
            if url:
                return url

    for n in names:
        key = _normalize(n)
        if not key:
            continue
        url = _face_urls.get(key)
        if url:
            return url

    # Fuzzy fallback — use the primary name (avoid running fuzzy twice).
    return _fuzzy_lookup(primary_key, _face_name_choices, _face_urls)


def get_logo_url(team_name: str) -> Optional[str]:
    _ensure_loaded()
    name_key = _normalize(team_name)
    if not name_key:
        return None
    url = _logo_urls.get(name_key)
    if url:
        return url
    return _fuzzy_lookup(name_key, _logo_name_choices, _logo_urls)


def get_stats() -> dict:
    _ensure_loaded()
    return {
        "faces": len(_face_urls),
        "faces_with_team": len(_face_urls_by_name_team),
        "logos": len(_logo_urls),
        "fuzzy_enabled": _HAS_RAPIDFUZZ,
    }
