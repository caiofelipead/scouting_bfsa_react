"""Image proxy route with SSRF protection."""

from typing import Dict
from urllib.parse import urlparse

import aiohttp
from cachetools import TTLCache
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


router = APIRouter(prefix="/api", tags=["proxy"])
limiter = Limiter(key_func=get_remote_address)

# TTL cache for proxied images (URL -> (content_type, bytes))
_image_cache: TTLCache = TTLCache(maxsize=2000, ttl=3600)  # 1 hour TTL

# SSRF protection: only allow known image hosting domains
_ALLOWED_IMAGE_DOMAINS = {
    "media.api-sports.io",
    "apiv3.apifootball.com",
    "api.sofascore.app",
    "www.sofascore.com",
    "sofascore.com",
    "img.api.sofascore.app",
    "api-football-v1.p.rapidapi.com",
    "cdn.sofifa.net",
    "cdn.futbin.com",
    "tmssl.akamaized.net",
    "img.sofascore.com",
    "flagcdn.com",
    "flagsapi.com",
    "logodetimes.com",
    "www.logodetimes.com",
    "upload.wikimedia.org",
}


@router.get("/image-proxy")
@limiter.limit("30/minute")
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

    # Build domain-specific header strategies
    is_sofascore = "sofascore" in (parsed.hostname or "")

    if is_sofascore:
        header_strategies = [
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
                "Referer": "https://www.sofascore.com/",
                "Origin": "https://www.sofascore.com",
                "Sec-Fetch-Dest": "image",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131"',
                "Sec-Ch-Ua-Platform": '"Windows"',
            },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
                "Accept": "image/*,*/*;q=0.8",
                "Referer": "https://www.sofascore.com/",
            },
            {
                "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                "Accept": "*/*",
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

    raise HTTPException(status_code=last_status, detail="Upstream image fetch failed")
