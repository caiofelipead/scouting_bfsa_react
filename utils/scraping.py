"""
utils/scraping.py — Scraping assíncrono de dados de jogadores (OGol / Transfermarkt).

Usa aiohttp para I/O não-bloqueante. Fallback síncrono com requests para
compatibilidade com Streamlit (que não suporta asyncio nativamente).
"""

import asyncio
import logging
import re
from typing import Optional

import aiohttp
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

_TIMEOUT = aiohttp.ClientTimeout(total=10)


# ============================================
# ASYNC CORE
# ============================================

async def _fetch_html(url: str, session: aiohttp.ClientSession | None = None) -> str | None:
    """Busca HTML de uma URL via aiohttp."""
    try:
        if session:
            async with session.get(url, headers=_DEFAULT_HEADERS, timeout=_TIMEOUT) as resp:
                resp.raise_for_status()
                return await resp.text(encoding="utf-8", errors="replace")
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=_DEFAULT_HEADERS, timeout=_TIMEOUT) as resp:
                resp.raise_for_status()
                return await resp.text(encoding="utf-8", errors="replace")
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.warning("Erro ao buscar %s: %s", url, e)
        return None


def _fetch_html_sync(url: str) -> str | None:
    """Fallback síncrono com requests."""
    try:
        resp = requests.get(url, headers=_DEFAULT_HEADERS, timeout=10)
        resp.encoding = "utf-8"
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.warning("Erro ao buscar %s: %s", url, e)
        return None


# ============================================
# PARSERS (independentes de I/O)
# ============================================

def _parse_ogol(html: str, base_url: str = "https://www.ogol.com.br") -> dict:
    """Extrai foto e carreira do HTML do OGol."""
    soup = BeautifulSoup(html, "html.parser")
    data = {"foto": None, "carreira": [], "info": {}}

    # Foto do jogador
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "jogadores" in src.lower() and ".jpg" in src:
            if not src.startswith("http"):
                src = base_url + src
            data["foto"] = src
            break

    # Carreira (tabela TEMPORADA/EQUIPE)
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True).upper() for th in table.find_all("th")]
        if "TEMPORADA" in headers or "EQUIPE" in headers:
            rows = table.find_all("tr")[1:]
            for row in rows[:5]:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    data["carreira"].append({
                        "temporada": cols[1].get_text(strip=True) if len(cols) > 1 else "",
                        "equipe": cols[2].get_text(strip=True) if len(cols) > 2 else "",
                        "jogos": cols[3].get_text(strip=True) if len(cols) > 3 else "",
                        "gols": cols[4].get_text(strip=True) if len(cols) > 4 else "",
                        "assists": cols[5].get_text(strip=True) if len(cols) > 5 else "",
                    })
            break

    return data


def _parse_transfermarkt(html: str) -> dict:
    """Extrai foto, escudos, contrato e valor do HTML do Transfermarkt."""
    soup = BeautifulSoup(html, "html.parser")
    data = {
        "foto": None,
        "contrato": None,
        "valor": None,
        "clube": None,
        "clube_escudo": None,
        "liga": None,
        "liga_escudo": None,
    }

    # Foto portrait
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "portrait" in src.lower() and "transfermarkt" in src.lower():
            data["foto"] = src
            break

    # Escudo do clube
    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "")
        title = img.get("title", "")
        if "wappen" in src.lower() and any(
            k in src.lower() for k in ("kaderquad", "small", "medium")
        ):
            data["clube_escudo"] = src
            data["clube"] = alt or title or None
            break

    # Escudo da liga
    for img in soup.find_all("img"):
        src = img.get("src", "")
        title = img.get("title", "")
        if (
            "/logo/" in src.lower()
            and "tiny" in src.lower()
            and title
            and title not in ("Transfermarkt", "")
        ):
            if "verytiny" in src:
                src = src.replace("verytiny", "medium")
            elif "tiny" in src:
                src = src.replace("tiny", "medium")
            data["liga_escudo"] = src
            data["liga"] = title
            break

    # Contrato
    for el in soup.find_all(["span", "div", "li"]):
        text = el.get_text(strip=True)
        if "contrato até" in text.lower() or "contract until" in text.lower():
            match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
            if match:
                data["contrato"] = match.group(1)
            break

    # Valor de mercado
    for el in soup.find_all(["span", "div"]):
        text = el.get_text(strip=True)
        if "€" in text and any(k in text.lower() for k in ("mi.", "mil", "M")):
            data["valor"] = text
            break

    return data


# ============================================
# API PÚBLICA — ASYNC
# ============================================

async def scrape_ogol_async(
    url: str, session: aiohttp.ClientSession | None = None
) -> Optional[dict]:
    """Scraping assíncrono do OGol."""
    if not url or not str(url).startswith("http"):
        return None
    html = await _fetch_html(url, session)
    if not html:
        return None
    try:
        return _parse_ogol(html)
    except Exception as e:
        logger.error("Erro ao parsear OGol: %s", e)
        return None


async def scrape_transfermarkt_async(
    url: str, session: aiohttp.ClientSession | None = None
) -> Optional[dict]:
    """Scraping assíncrono do Transfermarkt."""
    if not url or not str(url).startswith("http"):
        return None
    html = await _fetch_html(url, session)
    if not html:
        return None
    try:
        return _parse_transfermarkt(html)
    except Exception as e:
        logger.error("Erro ao parsear Transfermarkt: %s", e)
        return None


async def scrape_player_external_async(
    ogol_url: str | None = None,
    tm_url: str | None = None,
) -> tuple[Optional[dict], Optional[dict]]:
    """Busca dados de OGol e Transfermarkt em paralelo."""
    async def _noop():
        return None

    async with aiohttp.ClientSession() as session:
        tasks = [
            scrape_ogol_async(ogol_url, session) if ogol_url else _noop(),
            scrape_transfermarkt_async(tm_url, session) if tm_url else _noop(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    ogol_data = results[0] if not isinstance(results[0], Exception) else None
    tm_data = results[1] if not isinstance(results[1], Exception) else None
    return ogol_data, tm_data


# ============================================
# API PÚBLICA — SYNC (compatibilidade Streamlit)
# ============================================

def scrape_ogol(url: str) -> Optional[dict]:
    """Scraping síncrono do OGol (compatível com Streamlit cache)."""
    if not url or not str(url).startswith("http"):
        return None
    html = _fetch_html_sync(url)
    if not html:
        return None
    try:
        return _parse_ogol(html)
    except Exception as e:
        logger.error("Erro ao parsear OGol: %s", e)
        return None


def scrape_transfermarkt(url: str) -> Optional[dict]:
    """Scraping síncrono do Transfermarkt (compatível com Streamlit cache)."""
    if not url or not str(url).startswith("http"):
        return None
    html = _fetch_html_sync(url)
    if not html:
        return None
    try:
        return _parse_transfermarkt(html)
    except Exception as e:
        logger.error("Erro ao parsear Transfermarkt: %s", e)
        return None
