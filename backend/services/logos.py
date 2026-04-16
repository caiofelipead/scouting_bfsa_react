"""Unified club/league logo resolver.

Primary source is the Football Manager / sortitoutsi CDN (same pipeline as
player faces). When that yields nothing we fall back to caller-supplied URLs
from enrichment/CSV and finally to the `/api/team-logo/` server-side chain.
"""

from __future__ import annotations

from typing import Optional

from config.mappings import WYSCOUT_LEAGUE_MAP
from services.fm_sortitoutsi import get_logo_url, get_league_logo_url

__all__ = ["resolve_club_logo", "resolve_league_logo"]


def resolve_club_logo(team: Optional[str], fallback: Optional[str] = None) -> Optional[str]:
    """Return best-known logo URL for a club.

    Priority: sortitoutsi CDN (FM id) → caller fallback (enrichment/CSV) →
    /api/team-logo/{team} endpoint.
    """
    if team:
        hit = get_logo_url(team)
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

    Priority: sortitoutsi CDN for the canonical league name →
    sortitoutsi CDN for a raw WyScout label (after translation) →
    caller fallback (enrichment/CSV).
    """
    if league_actual:
        hit = get_league_logo_url(league_actual)
        if hit:
            return hit
    if league_raw:
        canonical = WYSCOUT_LEAGUE_MAP.get(league_raw, league_raw)
        hit = get_league_logo_url(canonical)
        if hit:
            return hit
    return fallback
