"""Unified club/league logo resolver.

Prefers stable hardcoded URLs (logodetimes.com / wikimedia) that the frontend
can load directly via DIRECT_IMAGE_DOMAINS. Falls back to enrichment assets,
then to the `/api/team-logo/` endpoint.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from config.mappings import CLUB_LOGOS, LEAGUE_LOGOS, WYSCOUT_LEAGUE_MAP

__all__ = ["resolve_club_logo", "resolve_league_logo"]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return " ".join(s.split())


# Build once: normalized key → URL
_CLUB_LOGOS_NORM = {_norm(k): v for k, v in CLUB_LOGOS.items() if k}
_LEAGUE_LOGOS_NORM = {_norm(k): v for k, v in LEAGUE_LOGOS.items() if k}


def _lookup_club(team: str) -> Optional[str]:
    if not team:
        return None
    key = _norm(team)
    if not key:
        return None
    if key in _CLUB_LOGOS_NORM:
        return _CLUB_LOGOS_NORM[key]
    # Try stripping common suffixes like "FC", "SC", "EC", "AF"
    stripped = re.sub(r"\b(fc|sc|ec|af|cf|cd|ac|sa|ag|fk|bk|if|sk)\b", "", key).strip()
    stripped = " ".join(stripped.split())
    if stripped and stripped in _CLUB_LOGOS_NORM:
        return _CLUB_LOGOS_NORM[stripped]
    return None


def _lookup_league(league: str) -> Optional[str]:
    if not league:
        return None
    key = _norm(league)
    if not key:
        return None
    if key in _LEAGUE_LOGOS_NORM:
        return _LEAGUE_LOGOS_NORM[key]
    # If this is a raw WyScout label, translate to canonical name first.
    canonical = WYSCOUT_LEAGUE_MAP.get(league)
    if canonical:
        ck = _norm(canonical)
        if ck in _LEAGUE_LOGOS_NORM:
            return _LEAGUE_LOGOS_NORM[ck]
    return None


def resolve_club_logo(team: Optional[str], fallback: Optional[str] = None) -> Optional[str]:
    """Return best-known logo URL for a club.

    Priority: hardcoded CLUB_LOGOS → caller-provided fallback (e.g. from
    enrichment/CSV) → /api/team-logo/{team} endpoint (server-side chain).
    """
    hit = _lookup_club(team) if team else None
    if hit:
        return hit
    if fallback:
        return fallback
    if team:
        return f"/api/team-logo/{team}"
    return None


def resolve_league_logo(
    league_actual: Optional[str],
    league_raw: Optional[str] = None,
    fallback: Optional[str] = None,
) -> Optional[str]:
    """Return best-known logo URL for a league.

    Priority: LEAGUE_LOGOS[league_actual] → LEAGUE_LOGOS[league_raw] →
    canonical name lookup → caller fallback.
    """
    hit = _lookup_league(league_actual) if league_actual else None
    if not hit and league_raw:
        hit = _lookup_league(league_raw)
    if hit:
        return hit
    return fallback
