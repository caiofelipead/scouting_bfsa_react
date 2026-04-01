"""Image proxy route with SSRF protection."""

import logging
import os
from typing import Dict
from urllib.parse import quote, urlparse

logger = logging.getLogger(__name__)

import aiohttp
from cachetools import TTLCache
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


router = APIRouter(prefix="/api", tags=["proxy"])
limiter = Limiter(key_func=get_remote_address)

# API-Football key for media.api-sports.io images
_API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
if not _API_FOOTBALL_KEY:
    logger.warning("API_FOOTBALL_KEY not set — media.api-sports.io images may fail")

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
}


@router.get("/image-proxy")
@limiter.limit("300/minute")
async def image_proxy(request: Request, url: str):
    """Proxy external image URLs to avoid CORS/hotlink 403 errors."""
    parsed = urlparse(url)
    if not parsed.hostname or not parsed.scheme.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL")

    hostname = parsed.hostname.lower()
    if not any(hostname == d or hostname.endswith("." + d) for d in _ALLOWED_IMAGE_DOMAINS):
        raise HTTPException(status_code=403, detail="Domain not allowed")

    # Check cache
    if url in _image_cache:
        content_type, data = _image_cache[url]
        return Response(content=data, media_type=content_type,
                        headers={"Cache-Control": "public, max-age=86400",
                                 "Access-Control-Allow-Origin": "*"})

    # Skip URLs known to be broken (avoids spamming upstream)
    if url in _failed_cache:
        raise HTTPException(status_code=404, detail="Image not available (cached failure)")

    # Build domain-specific header strategies
    is_api_sports = "api-sports.io" in (parsed.hostname or "") or "api-football-v1" in (parsed.hostname or "")
    is_wikimedia = "wikimedia.org" in (parsed.hostname or "")

    if is_api_sports:
        header_strategies = []
        # Strategy 1: API key auth (most reliable when key is available)
        if _API_FOOTBALL_KEY:
            header_strategies.append({
                "x-apisports-key": _API_FOOTBALL_KEY,
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            })
        # Strategy 2: Browser-like with api-football.com Referer
        header_strategies.append({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": "https://www.api-football.com/",
            "Origin": "https://www.api-football.com",
        })
        # Strategy 3: Simple request without Referer/Origin
        header_strategies.append({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "image/*,*/*;q=0.8",
        })
        # Strategy 4: Dashboard Referer (alternative referrer some CDNs accept)
        header_strategies.append({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "image/*,*/*;q=0.8",
            "Referer": "https://dashboard.api-football.com/",
        })
    elif is_wikimedia:
        # Wikimedia requires a proper User-Agent with contact info per their policy
        header_strategies = [
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
        header_strategies = [
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
                        # Cache the result (TTLCache handles maxsize & eviction)
                        _image_cache[url] = (content_type, data)
                        return Response(
                            content=data,
                            media_type=content_type,
                            headers={
                                "Cache-Control": "public, max-age=86400",
                                "Access-Control-Allow-Origin": "*",
                            },
                        )
                    last_status = resp.status
        except aiohttp.ClientError:
            continue

    # Cache the failure so we don't keep spamming upstream
    _failed_cache[url] = True

    # Never forward 401/403 from upstream — these are internal auth issues, not
    # client auth failures.  Map them to 502 so the frontend's 401 interceptor
    # doesn't mistakenly clear the user session.
    if last_status in (401, 403):
        logger.warning("Image proxy: upstream returned %d for %s (mapped to 502)", last_status, url)
        last_status = 502
    else:
        logger.warning("Image proxy: all strategies failed for %s (last status: %d)", url, last_status)
    raise HTTPException(status_code=last_status, detail="Upstream image fetch failed")


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


@router.get("/team-logo/{team_name_norm}")
async def get_team_logo(team_name_norm: str):
    """Serve locally cached team logo (avoids CDN 403 issues)."""
    # Check memory cache (pre-warmed at startup)
    if team_name_norm in _logo_bytes_cache:
        data, ct = _logo_bytes_cache[team_name_norm]
        return Response(
            content=data, media_type=ct,
            headers={"Cache-Control": "public, max-age=604800", "Access-Control-Allow-Origin": "*"},
        )

    # Already checked and not found
    if team_name_norm in _logo_miss_cache:
        raise HTTPException(status_code=404, detail="Logo not found")

    # Load from DB (in case bytes were added after startup)
    try:
        from services.enrichment import get_team_logo_bytes
        result = get_team_logo_bytes(team_name_norm)
        if result:
            data, ct = result
            _logo_bytes_cache[team_name_norm] = (data, ct)
            return Response(
                content=data, media_type=ct,
                headers={"Cache-Control": "public, max-age=604800", "Access-Control-Allow-Origin": "*"},
            )
    except Exception as e:
        logger.warning("Failed to load cached logo for %s: %s", team_name_norm, e)

    # Fallback: redirect to CDN URL via image-proxy (if available)
    try:
        from services.enrichment import get_team_cdn_url
        cdn_url = get_team_cdn_url(team_name_norm)
        if cdn_url:
            from starlette.responses import RedirectResponse
            proxy_url = f"/api/image-proxy?url={quote(cdn_url, safe='')}"
            return RedirectResponse(url=proxy_url, status_code=307)
    except Exception as e:
        logger.debug("CDN fallback failed for %s: %s", team_name_norm, e)

    # Fallback: try hardcoded CLUB_LOGOS mapping
    try:
        from config.mappings import CLUB_LOGOS
        # Check if any CLUB_LOGOS key normalizes to this team_name_norm
        for team_key, logo_url in CLUB_LOGOS.items():
            import unicodedata
            import re
            norm_key = unicodedata.normalize("NFD", team_key.lower())
            norm_key = "".join(c for c in norm_key if unicodedata.category(c) != "Mn")
            norm_key = re.sub(r"[^a-z0-9\s]", "", norm_key)
            norm_key = " ".join(norm_key.split())
            if norm_key == team_name_norm:
                from starlette.responses import RedirectResponse
                proxy_url = f"/api/image-proxy?url={quote(logo_url, safe='')}"
                return RedirectResponse(url=proxy_url, status_code=307)
    except Exception:
        pass

    _logo_miss_cache[team_name_norm] = True
    raise HTTPException(status_code=404, detail="Logo not found")
