"""
player_assets.py — Lookup service for player photos, club logos, and league logos.

Loads data from fotos_jogadores_clubes_ligas.csv (SofaScore-enriched)
and provides fast lookups by player name + team.
"""

import os
import csv
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Key: (normalized_player_name, normalized_team) → dict with asset URLs
_player_assets: Dict[Tuple[str, str], dict] = {}

# Fallback: player_name only (first high-quality match)
_player_assets_by_name: Dict[str, dict] = {}

# Club logo cache: normalized_team → logo_url
_club_logos: Dict[str, str] = {}

# League logo cache: league_name → logo_url
_league_logos: Dict[str, str] = {}

_loaded = False


def _normalize(s: str) -> str:
    """Normalize a string for fuzzy matching."""
    if not s:
        return ""
    return s.strip().lower()


def load_player_assets_csv(csv_path: str = None):
    """Load the CSV file and build lookup indices."""
    global _loaded

    if _loaded:
        return

    if csv_path is None:
        # Look for CSV in project root
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(base, "fotos_jogadores_clubes_ligas.csv")

    if not os.path.exists(csv_path):
        logger.warning("Player assets CSV not found at %s", csv_path)
        _loaded = True
        return

    count = 0
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                quality = row.get("Qualidade_Match", "").strip().upper()
                jogador = row.get("Jogador", "").strip()
                equipa = row.get("Equipa_CSV", "").strip()
                foto_url = row.get("Foto_Jogador_URL", "").strip()
                escudo_url = row.get("Escudo_Clube_URL", "").strip()
                liga = row.get("Liga", "").strip()
                pais_liga = row.get("Pais_Liga", "").strip()
                logo_liga_url = row.get("Logo_Liga_URL", "").strip()

                if not jogador:
                    continue

                # Only use photo_url from reliable matches (ALTA or MEDIA)
                # BAIXA_REVISAR and NAO_ENCONTRADO photos are likely wrong
                reliable_photo = quality in ("ALTA", "MEDIA")

                entry = {
                    "photo_url": (foto_url or None) if reliable_photo else None,
                    "club_logo": escudo_url or None,
                    "league_name": liga or None,
                    "league_country": pais_liga or None,
                    "league_logo": logo_liga_url or None,
                    "quality": quality,
                }

                key = (_normalize(jogador), _normalize(equipa))
                # Prefer ALTA quality matches
                existing = _player_assets.get(key)
                if existing is None or (quality == "ALTA" and existing.get("quality") != "ALTA"):
                    _player_assets[key] = entry

                # Name-only index (prefer ALTA)
                name_key = _normalize(jogador)
                existing_name = _player_assets_by_name.get(name_key)
                if existing_name is None or (quality == "ALTA" and existing_name.get("quality") != "ALTA"):
                    _player_assets_by_name[name_key] = entry

                # Club logo index
                if escudo_url:
                    team_key = _normalize(equipa)
                    if team_key and team_key not in _club_logos:
                        _club_logos[team_key] = escudo_url

                # League logo index
                if logo_liga_url and liga:
                    league_key = _normalize(liga)
                    if league_key not in _league_logos:
                        _league_logos[league_key] = logo_liga_url

                count += 1

    except Exception as e:
        logger.error("Failed to load player assets CSV: %s", e)

    _loaded = True
    logger.info("Loaded %d player asset entries from CSV (%d unique players, %d clubs, %d leagues)",
                count, len(_player_assets_by_name), len(_club_logos), len(_league_logos))


def _is_sofascore_url(url: str) -> bool:
    """Check if a URL is from SofaScore (which blocks server-side requests with 403)."""
    if not url:
        return False
    return "sofascore" in url.lower()


def _usable_url(url: str) -> str:
    """Return the URL only if it's not from a blocked source."""
    if not url or _is_sofascore_url(url):
        return None
    return url


def get_player_assets(player_name: str, team: str = None) -> dict:
    """Look up player photo, club logo, and league logo.

    Priority: API-Football enrichment cache first (reliable media.api-sports.io URLs),
    then CSV as fallback (filtering out blocked SofaScore URLs).

    Returns dict with keys: photo_url, club_logo, league_logo, league_name
    All values may be None if not found.
    """
    if not _loaded:
        load_player_assets_csv()

    result = {"photo_url": None, "club_logo": None, "league_logo": None, "league_name": None}

    name_norm = _normalize(player_name) if player_name else ""
    team_norm = _normalize(team) if team else ""

    # 0a) FM sortitoutsi CDN (cut-out faces & logos) — highest priority
    try:
        from services.fm_sortitoutsi import get_face_url, get_logo_url
        if name_norm:
            fm_face = get_face_url(player_name, team)
            if fm_face:
                result["photo_url"] = fm_face
        if team_norm:
            fm_logo = get_logo_url(team)
            if fm_logo:
                result["club_logo"] = fm_logo
    except Exception:
        pass

    # 0b) Local graphics packs (manual overrides) — second priority
    try:
        from services.graphics_packs import has_local_face, has_local_logo
        if name_norm and not result["photo_url"] and has_local_face(player_name):
            result["photo_url"] = f"/api/player-face/{player_name}"
        if team_norm and not result["club_logo"] and has_local_logo(team):
            result["club_logo"] = f"/api/team-logo/{team_norm}"
    except Exception:
        pass

    # 1) API-Football enrichment cache (in-memory) — fallback if no local pack
    if name_norm:
        try:
            from services.enrichment import get_cached_photo, get_cached_team_logo
            if not result["photo_url"]:
                cached_photo = get_cached_photo(player_name, team)
                if cached_photo:
                    result["photo_url"] = cached_photo
            if team and not result["club_logo"]:
                cached_logo = get_cached_team_logo(team)
                if cached_logo:
                    result["club_logo"] = cached_logo
        except Exception:
            pass  # enrichment module not loaded yet

    # 2) CSV lookup for metadata and fallback URLs (filter out SofaScore)
    csv_entry = None
    if name_norm and team_norm:
        csv_entry = _player_assets.get((name_norm, team_norm))
    if not csv_entry and name_norm:
        csv_entry = _player_assets_by_name.get(name_norm)

    if csv_entry:
        if not result["photo_url"]:
            result["photo_url"] = _usable_url(csv_entry.get("photo_url"))
        if not result["club_logo"]:
            result["club_logo"] = _usable_url(csv_entry.get("club_logo"))
        if not result["league_logo"]:
            result["league_logo"] = _usable_url(csv_entry.get("league_logo"))
        if not result["league_name"]:
            result["league_name"] = csv_entry.get("league_name")

    # 3) Club logo fallback from CSV index
    if not result["club_logo"] and team_norm and team_norm in _club_logos:
        result["club_logo"] = _usable_url(_club_logos[team_norm])

    return result


def get_club_logo(team: str) -> Optional[str]:
    """Get club logo URL by team name."""
    if not _loaded:
        load_player_assets_csv()
    url = _club_logos.get(_normalize(team)) if team else None
    return _usable_url(url)


def get_league_logo(league: str) -> Optional[str]:
    """Get league logo URL by league name."""
    if not _loaded:
        load_player_assets_csv()
    url = _league_logos.get(_normalize(league)) if league else None
    return _usable_url(url)
