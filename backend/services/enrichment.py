"""
enrichment.py — Enrich player photos and club logos
====================================================
Provides bulk and on-demand enrichment of player assets (photos, club logos)
by matching WyScout player/team names against TheSportsDB.

Uses the `player_assets_cache` and `team_assets_cache` tables in PostgreSQL
for persistent caching to avoid wasting API quota.
"""

import asyncio
import base64
import logging
import os
import unicodedata
import re
from typing import Dict, List, Optional, Tuple, Any

import aiohttp
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


# ── Name normalization ──────────────────────────────────────────────────

def _normalize(name: str) -> str:
    """Remove accents, lowercase, strip extra spaces and punctuation."""
    if not name:
        return ""
    name = unicodedata.normalize("NFD", str(name))
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^a-z0-9\s]", "", name.lower())
    return " ".join(name.split())


def _fuzzy_score(s1: str, s2: str) -> float:
    """Similarity score 0–100 using rapidfuzz (handles name order differences)."""
    if not s1 or not s2:
        return 0.0
    return max(
        fuzz.ratio(s1, s2),
        fuzz.token_sort_ratio(s1, s2),
    )


# ── Database helpers ────────────────────────────────────────────────────

_CREATE_ASSET_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS team_assets_cache (
    id SERIAL PRIMARY KEY,
    team_name TEXT NOT NULL,
    team_name_norm TEXT NOT NULL UNIQUE,
    api_football_team_id INTEGER,
    club_logo TEXT,
    logo_bytes BYTEA,
    logo_content_type TEXT DEFAULT 'image/png',
    match_quality TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS player_assets_cache (
    id SERIAL PRIMARY KEY,
    player_name TEXT NOT NULL,
    team_name TEXT,
    player_name_norm TEXT NOT NULL,
    team_name_norm TEXT,
    photo_url TEXT,
    club_logo TEXT,
    api_football_player_id INTEGER,
    api_football_team_id INTEGER,
    match_quality TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (player_name_norm, team_name_norm)
);

CREATE INDEX IF NOT EXISTS idx_pac_name ON player_assets_cache (player_name_norm);
CREATE INDEX IF NOT EXISTS idx_pac_team ON player_assets_cache (team_name_norm);
"""


def init_asset_tables():
    """Create asset cache tables if they don't exist."""
    from services.database import get_connection, release_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(_CREATE_ASSET_TABLES_SQL)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)

    # Migration: add logo_bytes columns if table existed before this change
    conn = get_connection()
    for col, col_type in [("logo_bytes", "BYTEA"), ("logo_content_type", "TEXT DEFAULT 'image/png'")]:
        try:
            with conn.cursor() as cur:
                cur.execute(f"ALTER TABLE team_assets_cache ADD COLUMN IF NOT EXISTS {col} {col_type}")
            conn.commit()
        except Exception:
            conn.rollback()
    release_connection(conn)
    logger.info("Asset cache tables initialized")


async def _download_image(url: str) -> Optional[Tuple[bytes, str]]:
    """Download an image from TheSportsDB or cached CDN URLs.

    Returns (bytes, content_type) or None if download fails.
    """
    if not url:
        return None
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    ct = resp.content_type or "image/png"
                    if len(data) > 0:
                        return (data, ct)
                logger.debug("Image download failed for %s: status %d", url, resp.status)
    except Exception as e:
        logger.debug("Image download error for %s: %s", url, e)
    return None


def _get_team_asset(team_name_norm: str) -> Optional[dict]:
    """Check if a team was already resolved."""
    from services.database import get_connection, release_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT api_football_team_id, club_logo, match_quality FROM team_assets_cache WHERE team_name_norm = %s",
                (team_name_norm,),
            )
            row = cur.fetchone()
            if row:
                return {"api_football_team_id": row[0], "club_logo": row[1], "match_quality": row[2]}
        return None
    finally:
        release_connection(conn)


def _upsert_team_asset(
    team_name: str,
    api_football_team_id: Optional[int],
    club_logo: Optional[str],
    match_quality: str,
    logo_bytes: Optional[bytes] = None,
    logo_content_type: str = "image/png",
) -> bool:
    """Upsert team asset. Returns True if logo_bytes were persisted to DB."""
    from services.database import get_connection, release_connection
    bytes_saved = False
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO team_assets_cache (team_name, team_name_norm, api_football_team_id, club_logo, logo_bytes, logo_content_type, match_quality)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (team_name_norm)
                    DO UPDATE SET api_football_team_id = EXCLUDED.api_football_team_id,
                                  club_logo = EXCLUDED.club_logo,
                                  logo_bytes = COALESCE(EXCLUDED.logo_bytes, team_assets_cache.logo_bytes),
                                  logo_content_type = COALESCE(EXCLUDED.logo_content_type, team_assets_cache.logo_content_type),
                                  match_quality = EXCLUDED.match_quality
                """, (team_name, _normalize(team_name), api_football_team_id, club_logo, logo_bytes, logo_content_type, match_quality))
                bytes_saved = logo_bytes is not None and len(logo_bytes) > 0
            except Exception:
                # Fallback: logo_bytes columns might not exist yet
                conn.rollback()
                cur.execute("""
                    INSERT INTO team_assets_cache (team_name, team_name_norm, api_football_team_id, club_logo, match_quality)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (team_name_norm)
                    DO UPDATE SET api_football_team_id = EXCLUDED.api_football_team_id,
                                  club_logo = EXCLUDED.club_logo,
                                  match_quality = EXCLUDED.match_quality
                """, (team_name, _normalize(team_name), api_football_team_id, club_logo, match_quality))
                bytes_saved = False
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)
    return bytes_saved


def _get_player_asset(player_name_norm: str, team_name_norm: str) -> Optional[dict]:
    from services.database import get_connection, release_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT photo_url, club_logo, match_quality FROM player_assets_cache WHERE player_name_norm = %s AND team_name_norm = %s",
                (player_name_norm, team_name_norm or ""),
            )
            row = cur.fetchone()
            if row:
                return {"photo_url": row[0], "club_logo": row[1], "match_quality": row[2]}
        return None
    finally:
        release_connection(conn)


def _upsert_player_asset(
    player_name: str,
    team_name: str,
    photo_url: Optional[str],
    club_logo: Optional[str],
    api_football_player_id: Optional[int],
    api_football_team_id: Optional[int],
    match_quality: str,
):
    from services.database import get_connection, release_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO player_assets_cache
                    (player_name, team_name, player_name_norm, team_name_norm,
                     photo_url, club_logo, api_football_player_id, api_football_team_id, match_quality)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_name_norm, team_name_norm)
                DO UPDATE SET photo_url = COALESCE(EXCLUDED.photo_url, player_assets_cache.photo_url),
                              club_logo = COALESCE(EXCLUDED.club_logo, player_assets_cache.club_logo),
                              api_football_player_id = COALESCE(EXCLUDED.api_football_player_id, player_assets_cache.api_football_player_id),
                              api_football_team_id = COALESCE(EXCLUDED.api_football_team_id, player_assets_cache.api_football_team_id),
                              match_quality = EXCLUDED.match_quality,
                              updated_at = NOW()
            """, (
                player_name, team_name or "",
                _normalize(player_name), _normalize(team_name) if team_name else "",
                photo_url, club_logo,
                api_football_player_id, api_football_team_id, match_quality,
            ))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def get_all_cached_assets() -> Dict[Tuple[str, str], dict]:
    """Load all cached player assets into memory (for startup warm-up)."""
    from services.database import get_connection, release_connection
    result: Dict[Tuple[str, str], dict] = {}
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT player_name_norm, team_name_norm, photo_url, club_logo FROM player_assets_cache WHERE photo_url IS NOT NULL")
            for row in cur.fetchall():
                result[(row[0], row[1])] = {"photo_url": row[2], "club_logo": row[3]}
        release_connection(conn)
    except Exception as e:
        logger.warning("Could not load cached assets: %s", e)
    return result


def get_all_cached_team_logos() -> Dict[str, str]:
    """Load all cached team logos into memory.

    Returns local endpoint URLs for teams that have cached logo bytes.
    For teams without bytes, returns None (allows CLUB_LOGOS fallback)
    since CDN URLs (media.api-sports.io) are blocked server-side.
    """
    from services.database import get_connection, release_connection
    result: Dict[str, str] = {}
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT team_name_norm, club_logo, (logo_bytes IS NOT NULL AND length(logo_bytes) > 0) AS has_bytes FROM team_assets_cache WHERE club_logo IS NOT NULL")
            for row in cur.fetchall():
                team_norm, club_logo, has_bytes = row
                if has_bytes:
                    # Serve from local endpoint (avoids CDN 403)
                    result[team_norm] = f"/api/team-logo/{team_norm}"
                elif club_logo and "api-sports.io" not in club_logo:
                    # Non-CDN URL (e.g. logodetimes.com) — use directly
                    result[team_norm] = club_logo
                # else: CDN URL without bytes — skip, let CLUB_LOGOS fallback handle it
        release_connection(conn)
    except Exception as e:
        logger.warning("Could not load cached team logos: %s", e)
    return result


def get_team_logo_bytes(team_name_norm: str) -> Optional[Tuple[bytes, str]]:
    """Get cached logo bytes and content type for a team."""
    from services.database import get_connection, release_connection
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT logo_bytes, logo_content_type FROM team_assets_cache WHERE team_name_norm = %s AND logo_bytes IS NOT NULL AND length(logo_bytes) > 0",
                (team_name_norm,),
            )
            row = cur.fetchone()
            if row:
                return (bytes(row[0]), row[1] or "image/png")
    except Exception as e:
        logger.warning("Could not load logo bytes for %s: %s", team_name_norm, e)
    finally:
        if conn:
            release_connection(conn)
    return None


def get_team_cdn_url(team_name_norm: str) -> Optional[str]:
    """Get the CDN logo URL for a team (without bytes). Used as fallback."""
    from services.database import get_connection, release_connection
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT club_logo FROM team_assets_cache WHERE team_name_norm = %s AND club_logo IS NOT NULL",
                (team_name_norm,),
            )
            row = cur.fetchone()
            if row and row[0]:
                return row[0]
    except Exception as e:
        logger.warning("Could not load CDN URL for %s: %s", team_name_norm, e)
    finally:
        if conn:
            release_connection(conn)
    return None


_enrichment_stats_cache: dict = {}
_enrichment_stats_ts: float = 0


def get_enrichment_stats() -> dict:
    """Return counts for enrichment status (cached for 5 minutes)."""
    import time
    global _enrichment_stats_cache, _enrichment_stats_ts

    # Return cached result if fresh (5 min TTL)
    if _enrichment_stats_cache and (time.monotonic() - _enrichment_stats_ts) < 300:
        return _enrichment_stats_cache

    from services.database import get_connection, release_connection
    stats = {"teams_total": 0, "teams_found": 0, "players_total": 0, "players_with_photo": 0, "players_not_found": 0}
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*), COUNT(CASE WHEN api_football_team_id IS NOT NULL THEN 1 END) FROM team_assets_cache")
            row = cur.fetchone()
            stats["teams_total"] = row[0]
            stats["teams_found"] = row[1]
            cur.execute("SELECT COUNT(*), COUNT(CASE WHEN photo_url IS NOT NULL THEN 1 END), COUNT(CASE WHEN match_quality = 'not_found' THEN 1 END) FROM player_assets_cache")
            row = cur.fetchone()
            stats["players_total"] = row[0]
            stats["players_with_photo"] = row[1]
            stats["players_not_found"] = row[2]
        _enrichment_stats_cache = stats
        _enrichment_stats_ts = time.monotonic()
    except Exception as e:
        logger.warning("Could not get enrichment stats: %s", e)
    finally:
        if conn is not None:
            release_connection(conn)
    return stats


# ── In-memory cache (loaded at startup) ─────────────────────────────────

_cached_player_assets: Dict[Tuple[str, str], dict] = {}
_cached_team_logos: Dict[str, str] = {}
_cache_loaded = False


def load_asset_cache():
    """Load all cached assets from DB into memory. Call at startup."""
    global _cached_player_assets, _cached_team_logos, _cache_loaded
    _cached_player_assets = get_all_cached_assets()
    _cached_team_logos = get_all_cached_team_logos()
    _cache_loaded = True
    logger.info(
        "Loaded asset cache: %d player photos, %d team logos",
        len(_cached_player_assets), len(_cached_team_logos),
    )


def get_cached_photo(player_name: str, team_name: str = None) -> Optional[str]:
    """Fast in-memory lookup for cached player photo."""
    if not _cache_loaded:
        return None
    key = (_normalize(player_name), _normalize(team_name) if team_name else "")
    entry = _cached_player_assets.get(key)
    return entry.get("photo_url") if entry else None


def get_cached_team_logo(team_name: str) -> Optional[str]:
    """Fast in-memory lookup for cached team logo."""
    if not _cache_loaded:
        return None
    return _cached_team_logos.get(_normalize(team_name))


# ── TheSportsDB matching logic (PRIMARY) ─────────────────────────────────

async def _enrich_team_via_thesportsdb(
    team_name: str,
    wyscout_players: List[str],
) -> Optional[Dict[str, Any]]:
    """Try to enrich a team using TheSportsDB (free API).

    Returns dict with {badge_url, matched_players: {ws_name: photo_url}, api_calls}
    or None if team not found.
    """
    try:
        from services.thesportsdb import (
            search_team_multi_strategy, get_players_in_team,
            extract_team_badge, extract_player_photo,
        )
    except ImportError:
        logger.debug("thesportsdb module not available")
        return None

    api_calls = 0
    try:
        # Use multi-strategy search for better SA club coverage
        team = await search_team_multi_strategy(team_name)
        api_calls += 1
    except Exception as e:
        logger.warning("TheSportsDB lookup failed for '%s': %s", team_name, e)
        return None

    if not team:
        return None

    team_id = team.get("idTeam")
    badge_url = extract_team_badge(team)

    # Fetch squad players if we have a team ID
    tsdb_players: Dict[str, str] = {}
    if team_id:
        try:
            players = await get_players_in_team(team_id)
            api_calls += 1
            for p in players:
                name = p.get("strPlayer", "")
                photo = extract_player_photo(p)
                if name and photo:
                    tsdb_players[name.lower().strip()] = photo
        except Exception as e:
            logger.warning("TheSportsDB player lookup failed for team '%s': %s", team_name, e)

    if not team_id and not badge_url:
        return None

    # Match WyScout player names against TheSportsDB squad
    matched: Dict[str, str] = {}
    for ws_name in wyscout_players:
        ws_norm = _normalize(ws_name)
        if not ws_norm:
            continue

        # 1) Exact normalized match
        for tsdb_name, photo_url in tsdb_players.items():
            if _normalize(tsdb_name) == ws_norm:
                matched[ws_name] = photo_url
                break

        if ws_name in matched:
            continue

        # 2) Fuzzy match
        best_score = 0.0
        best_photo = None
        for tsdb_name, photo_url in tsdb_players.items():
            score = _fuzzy_score(ws_norm, _normalize(tsdb_name))
            if score > best_score:
                best_score = score
                best_photo = photo_url
        if best_photo and best_score >= 68:
            matched[ws_name] = best_photo

    return {
        "badge_url": badge_url,
        "matched_players": matched,
        "api_calls": api_calls,
    }


# ── Bulk enrichment ─────────────────────────────────────────────────────

async def enrich_team(
    team_name: str,
    wyscout_players: List[str],
    retry_not_found: bool = False,
) -> Dict[str, Any]:
    """Enrich a single team: resolve team badge + player photos.

    Strategy:
    1. Check DB cache first
    2. Try TheSportsDB (free, no key needed)
    3. Fall back to API-Football if TheSportsDB didn't find enough

    Returns: {team, logo, matched, unmatched, api_calls, skipped, source}
    """
    team_norm = _normalize(team_name)
    result = {"team": team_name, "logo": None, "matched": 0, "unmatched": 0,
              "api_calls": 0, "skipped": False, "source": None}

    # Check if team already resolved
    cached_team = _get_team_asset(team_norm)
    team_id = None
    club_logo = None

    if cached_team:
        team_id = cached_team.get("api_football_team_id")
        club_logo = cached_team.get("club_logo")
        if cached_team.get("match_quality") == "not_found":
            if retry_not_found:
                cached_team = None
            else:
                for pname in wyscout_players:
                    existing = _get_player_asset(_normalize(pname), team_norm)
                    if not existing:
                        _upsert_player_asset(pname, team_name, None, club_logo, None, None, "team_not_found")
                        result["unmatched"] += 1
                result["skipped"] = True
                return result

    logo_bytes_downloaded = False

    if not cached_team:
        # ── SOURCE 1: TheSportsDB (primary — free) ──────────────────
        tsdb_result = await _enrich_team_via_thesportsdb(team_name, wyscout_players)
        if tsdb_result:
            result["api_calls"] += tsdb_result.get("api_calls", 0)
            badge_url = tsdb_result.get("badge_url")
            matched_players = tsdb_result.get("matched_players", {})

            if badge_url:
                club_logo = badge_url
                # Download badge for local caching
                logo_data = await _download_image(badge_url)
                logo_bytes_downloaded = _upsert_team_asset(
                    team_name, None, badge_url, "found_thesportsdb",
                    logo_bytes=logo_data[0] if logo_data else None,
                    logo_content_type=logo_data[1] if logo_data else "image/png",
                )
                result["source"] = "thesportsdb"

            # Save matched players
            for pname in wyscout_players:
                if pname in matched_players:
                    photo_url = matched_players[pname]
                    _upsert_player_asset(
                        pname, team_name, photo_url=photo_url,
                        club_logo=badge_url, api_football_player_id=None,
                        api_football_team_id=None, match_quality="thesportsdb",
                    )
                    result["matched"] += 1

            # Save remaining as unmatched
            for pname in wyscout_players:
                if pname not in matched_players:
                    existing = _get_player_asset(_normalize(pname), team_norm)
                    if not existing or not existing.get("photo_url"):
                        _upsert_player_asset(pname, team_name, None, badge_url, None, None, "not_found_thesportsdb")
                    result["unmatched"] += 1

            result["logo"] = club_logo
            # Update in-memory caches
            if logo_bytes_downloaded:
                _cached_team_logos[team_norm] = f"/api/team-logo/{team_norm}"
            for pname, photo in matched_players.items():
                if photo:
                    _cached_player_assets[(_normalize(pname), team_norm)] = {
                        "photo_url": photo,
                        "club_logo": f"/api/team-logo/{team_norm}" if logo_bytes_downloaded else badge_url,
                    }
            return result

        # TheSportsDB didn't find the team
        if not club_logo:
            _upsert_team_asset(team_name, None, None, "not_found")
            for pname in wyscout_players:
                if not _get_player_asset(_normalize(pname), team_norm):
                    _upsert_player_asset(pname, team_name, None, None, None, None, "team_not_found")
                    result["unmatched"] += 1
            return result

    result["logo"] = club_logo
    return result


async def run_bulk_enrichment(
    teams_with_players: Dict[str, List[str]],
    max_api_calls: int = 90,
    retry_not_found: bool = False,
) -> Dict[str, Any]:
    """Run bulk enrichment for all teams.

    Args:
        teams_with_players: {team_name: [player_name, ...]}
        max_api_calls: Maximum API calls to make (default 90, safe for 100/day limit)
        retry_not_found: If True, re-search teams previously marked as not_found

    Returns: summary dict with results per team
    """
    total_api_calls = 0
    results = []
    teams_processed = 0
    total_matched = 0
    total_unmatched = 0
    stopped_reason = None

    for team_name, players in teams_with_players.items():
        if total_api_calls >= max_api_calls:
            stopped_reason = "rate_limit"
            break

        try:
            team_result = await enrich_team(team_name, players, retry_not_found=retry_not_found)
            total_api_calls += team_result["api_calls"]
            total_matched += team_result["matched"]
            total_unmatched += team_result["unmatched"]
            teams_processed += 1
            results.append(team_result)

            # Small delay between API calls to be nice
            if team_result["api_calls"] > 0:
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.error("Error enriching team '%s': %s", team_name, e)
            results.append({"team": team_name, "error": str(e)})

    # Reload in-memory cache so subsequent requests see updated photos
    load_asset_cache()

    return {
        "teams_processed": teams_processed,
        "teams_total": len(teams_with_players),
        "players_matched": total_matched,
        "players_unmatched": total_unmatched,
        "api_calls_used": total_api_calls,
        "stopped_reason": stopped_reason,
        "details": results,
    }


# ── On-demand fallback ──────────────────────────────────────────────────

async def enrich_single_player(player_name: str, team_name: str = None) -> Optional[dict]:
    """On-demand enrichment for a single player. Checks DB cache first.

    Returns: {"photo_url": ..., "club_logo": ...} or None
    """
    player_norm = _normalize(player_name)
    team_norm = _normalize(team_name) if team_name else ""

    # Check DB cache
    cached = _get_player_asset(player_norm, team_norm)
    if cached:
        if cached.get("photo_url"):
            return {"photo_url": cached["photo_url"], "club_logo": cached.get("club_logo")}
        # Already searched and not found — don't re-try
        if cached.get("match_quality") in ("not_found", "team_not_found"):
            return None

    if not team_name:
        return None

    # Enrich the whole team (caches all players for that team)
    try:
        # Get all WyScout players for this team (just this one for now)
        result = await enrich_team(team_name, [player_name])
        if result["matched"] > 0:
            entry = _get_player_asset(player_norm, team_norm)
            if entry and entry.get("photo_url"):
                return {"photo_url": entry["photo_url"], "club_logo": entry.get("club_logo")}
    except Exception as e:
        logger.warning("On-demand enrichment failed for %s (%s): %s", player_name, team_name, e)

    return None


async def backfill_logo_bytes():
    """Download logo bytes for teams that have a URL but no cached bytes.

    This handles teams that were enriched before the logo_bytes feature was added.
    Does NOT count against API quota — just downloads from the CDN.
    """
    from services.database import get_connection, release_connection
    conn = get_connection()
    teams_to_backfill = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT team_name_norm, club_logo FROM team_assets_cache "
                "WHERE club_logo IS NOT NULL AND logo_bytes IS NULL AND match_quality = 'found'"
            )
            teams_to_backfill = cur.fetchall()
    finally:
        release_connection(conn)

    if not teams_to_backfill:
        return 0

    logger.info("Backfilling logo bytes for %d teams", len(teams_to_backfill))
    count = 0
    for team_norm, logo_url in teams_to_backfill:
        logo_data = await _download_image(logo_url)
        if logo_data:
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE team_assets_cache SET logo_bytes = %s, logo_content_type = %s WHERE team_name_norm = %s",
                        (logo_data[0], logo_data[1], team_norm),
                    )
                conn.commit()
                count += 1
            except Exception:
                conn.rollback()
            finally:
                release_connection(conn)
        # Small delay to avoid hammering the CDN
        await asyncio.sleep(0.2)

    logger.info("Backfilled %d/%d team logos", count, len(teams_to_backfill))
    return count
