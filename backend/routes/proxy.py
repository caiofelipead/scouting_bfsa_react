"""Image proxy route with SSRF protection."""

import base64
import logging
import os
from typing import Dict
from urllib.parse import quote, urlparse

logger = logging.getLogger(__name__)

# 1×1 transparent PNG returned for failed upstream images (avoids browser
# console "Failed to load resource" errors which spam the DevTools console).
_TRANSPARENT_1PX_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQAB"
    "Nl7BcQAAAABJRU5ErkJggg=="
)

import aiohttp
from cachetools import TTLCache
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


router = APIRouter(prefix="/api", tags=["proxy"])
limiter = Limiter(key_func=get_remote_address)

# TTL cache for proxied images (URL -> (content_type, bytes))
_image_cache: TTLCache = TTLCache(maxsize=2000, ttl=3600)  # 1 hour TTL

# Cache failed URLs to avoid repeated upstream requests (URL -> True)
_failed_cache: TTLCache = TTLCache(maxsize=5000, ttl=1800)  # 30 min TTL

# SSRF protection: only allow known image hosting domains
_ALLOWED_IMAGE_DOMAINS = {
    "media.api-sports.io",
    "apiv3.apifootball.com",
    "api-football-v1.p.rapidapi.com",
    "cdn.sofifa.net",
    "cdn.futbin.com",
    "tmssl.akamaized.net",
    "flagcdn.com",
    "flagsapi.com",
    "logodetimes.com",
    "www.logodetimes.com",
    "upload.wikimedia.org",
    "images.fotmob.com",
    "www.thesportsdb.com",
    "thesportsdb.com",
    "sortitoutsi.b-cdn.net",
    "sortitoutsidospaces.b-cdn.net",
}


def _get_header_strategies(parsed) -> list:
    """Return domain-specific header strategies for fetching an image URL."""
    is_api_sports = "api-sports.io" in (parsed.hostname or "") or "api-football-v1" in (parsed.hostname or "")
    is_wikimedia = "wikimedia.org" in (parsed.hostname or "")

    if is_api_sports:
        return [
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "image/*,*/*;q=0.8",
            },
        ]
    elif is_wikimedia:
        return [
            {
                "User-Agent": "ScoutingBFSA/1.0 (https://scouting-bfsa-react.vercel.app; bot) Python/aiohttp",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Referer": "https://en.wikipedia.org/",
            },
        ]
    else:
        return [
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": f"{parsed.scheme}://{parsed.hostname}/",
                "Sec-Fetch-Dest": "image",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131"',
                "Sec-Ch-Ua-Platform": '"Windows"',
            },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
                "Accept": "image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
                "Referer": f"{parsed.scheme}://{parsed.hostname}/",
            },
            {
                "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                "Accept": "*/*",
            },
        ]


async def _fetch_image(url: str) -> tuple | None:
    """Fetch an image URL using domain-specific strategies.

    Returns (content_type, bytes) on success, or None on failure.
    Uses and populates the shared _image_cache / _failed_cache.
    """
    # Check caches first
    if url in _image_cache:
        return _image_cache[url]
    if url in _failed_cache:
        return None

    parsed = urlparse(url)
    if not parsed.hostname or not parsed.scheme.startswith("http"):
        return None

    hostname = parsed.hostname.lower()
    if not any(hostname == d or hostname.endswith("." + d) for d in _ALLOWED_IMAGE_DOMAINS):
        _failed_cache[url] = True
        return None

    header_strategies = _get_header_strategies(parsed)

    last_status = 502
    for headers in header_strategies:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=15),
                    headers=headers,
                    allow_redirects=True,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        content_type = resp.content_type or "image/png"
                        _image_cache[url] = (content_type, data)
                        return (content_type, data)
                    last_status = resp.status
        except aiohttp.ClientError:
            continue

    _failed_cache[url] = True
    if last_status in (401, 403):
        logger.info("Image proxy: upstream %d for %s", last_status, parsed.hostname)
    elif last_status == 404:
        logger.debug("Image proxy: 404 for %s%s", parsed.hostname, parsed.path)
    else:
        logger.warning("Image proxy: all strategies failed for %s (status: %d)", parsed.hostname, last_status)
    return None


def _image_response(content_type: str, data: bytes, max_age: int = 86400) -> Response:
    """Return a successful image response with standard headers."""
    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Cache-Control": f"public, max-age={max_age}",
            "Access-Control-Allow-Origin": "*",
        },
    )


def _fallback_response(reason: str = "upstream-error", max_age: int = 3600) -> Response:
    """Return a 1×1 transparent PNG placeholder (200 status, no console errors)."""
    return Response(
        content=_TRANSPARENT_1PX_PNG,
        media_type="image/png",
        headers={
            "Cache-Control": f"public, max-age={max_age}",
            "Access-Control-Allow-Origin": "*",
            "X-Image-Fallback": reason,
        },
    )


@router.get("/image-proxy")
@limiter.limit("300/minute")
async def image_proxy(request: Request, url: str):
    """Proxy external image URLs to avoid CORS/hotlink 403 errors."""
    result = await _fetch_image(url)
    if result:
        content_type, data = result
        return _image_response(content_type, data)
    return _fallback_response()


# ── Cached team logo endpoint ──────────────────────────────────────────

# In-memory cache for logo bytes: team_name_norm → (bytes, content_type)
_logo_bytes_cache: Dict[str, tuple] = {}
# Teams known to have no logo (avoid repeated DB lookups)
_logo_miss_cache: TTLCache = TTLCache(maxsize=5000, ttl=3600)


def prewarm_logo_bytes_cache():
    """Load all team logo bytes from DB at startup to avoid per-request DB hits."""
    try:
        from services.database import get_connection, release_connection
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT team_name_norm, logo_bytes, logo_content_type "
                    "FROM team_assets_cache "
                    "WHERE logo_bytes IS NOT NULL AND length(logo_bytes) > 0"
                )
                count = 0
                for row in cur.fetchall():
                    _logo_bytes_cache[row[0]] = (bytes(row[1]), row[2] or "image/png")
                    count += 1
            logger.info("Pre-warmed logo bytes cache with %d teams", count)
        finally:
            release_connection(conn)
    except Exception as e:
        logger.warning("Failed to pre-warm logo bytes cache: %s", e)


@router.get("/player-face/{player_name}")
async def get_player_face(player_name: str):
    """Serve player face from local graphics pack."""
    from services.graphics_packs import get_local_face
    result = get_local_face(player_name)
    if result:
        data, ct = result
        return Response(
            content=data, media_type=ct,
            headers={"Cache-Control": "public, max-age=604800", "Access-Control-Allow-Origin": "*"},
        )
    raise HTTPException(status_code=404, detail="Face not found in local graphics pack")


@router.get("/team-logo/{team_name_norm}")
async def get_team_logo(team_name_norm: str):
    """Serve team logo with multi-source fallback chain.

    Instead of 307 redirects (which bypass remaining fallbacks on failure),
    this endpoint fetches images inline so every source is tried in order.
    """
    # Priority 0a: FM sortitoutsi CDN logo — redirect to CDN (browser loads directly).
    # Server-side fetches get 403 from the CDN, but browsers load <img> fine.
    try:
        from services.fm_sortitoutsi import get_logo_url
        fm_logo = get_logo_url(team_name_norm)
        if fm_logo:
            return RedirectResponse(url=fm_logo, status_code=302)
    except Exception:
        pass

    # Priority 0b: Check local graphics pack (manual overrides)
    try:
        from services.graphics_packs import get_local_logo
        local = get_local_logo(team_name_norm)
        if local:
            data, ct = local
            return _image_response(ct, data, max_age=604800)
    except Exception:
        pass

    # Check memory cache (pre-warmed at startup)
    if team_name_norm in _logo_bytes_cache:
        data, ct = _logo_bytes_cache[team_name_norm]
        return _image_response(ct, data, max_age=604800)

    # Already checked and not found
    if team_name_norm in _logo_miss_cache:
        return _fallback_response("logo-not-found")

    # Load from DB (in case bytes were added after startup)
    try:
        from services.enrichment import get_team_logo_bytes
        result = get_team_logo_bytes(team_name_norm)
        if result:
            data, ct = result
            _logo_bytes_cache[team_name_norm] = (data, ct)
            return _image_response(ct, data, max_age=604800)
    except Exception as e:
        logger.warning("Failed to load cached logo for %s: %s", team_name_norm, e)

    # Fallback: CDN URL via inline fetch (not redirect)
    try:
        from services.enrichment import get_team_cdn_url
        cdn_url = get_team_cdn_url(team_name_norm)
        if cdn_url:
            result = await _fetch_image(cdn_url)
            if result:
                ct, data = result
                _logo_bytes_cache[team_name_norm] = (data, ct)
                return _image_response(ct, data, max_age=604800)
    except Exception as e:
        logger.debug("CDN fallback failed for %s: %s", team_name_norm, e)

    # Fallback: try hardcoded CLUB_LOGOS mapping
    try:
        from config.mappings import CLUB_LOGOS
        import re
        import unicodedata
        # Normalize input the same way we normalize dict keys (strip accents)
        input_norm = unicodedata.normalize("NFD", team_name_norm.lower())
        input_norm = "".join(c for c in input_norm if unicodedata.category(c) != "Mn")
        input_norm = re.sub(r"[^a-z0-9\s]", "", input_norm)
        input_norm = " ".join(input_norm.split())
        for team_key, logo_url in CLUB_LOGOS.items():
            norm_key = unicodedata.normalize("NFD", team_key.lower())
            norm_key = "".join(c for c in norm_key if unicodedata.category(c) != "Mn")
            norm_key = re.sub(r"[^a-z0-9\s]", "", norm_key)
            norm_key = " ".join(norm_key.split())
            if norm_key == input_norm:
                result = await _fetch_image(logo_url)
                if result:
                    ct, data = result
                    _logo_bytes_cache[team_name_norm] = (data, ct)
                    return _image_response(ct, data, max_age=604800)
                break
    except Exception:
        pass

    _logo_miss_cache[team_name_norm] = True
    return _fallback_response("logo-not-found")
