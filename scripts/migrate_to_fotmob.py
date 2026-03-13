#!/usr/bin/env python3
"""
Migrate player/club/league photos from SofaScore to FotMob.

Usage:
    python scripts/migrate_to_fotmob.py

Requires:
    pip install aiohttp tqdm

This script:
1. Reads fotos_jogadores_clubes_ligas.csv
2. For each player, searches FotMob API by name
3. Picks best match using team/position matching
4. Updates photo URLs to FotMob format
5. Also migrates club logos and league logos
6. Writes updated CSV (backup created first)
"""

import asyncio
import csv
import os
import sys
import json
import shutil
from datetime import datetime
from typing import Optional

try:
    import aiohttp
except ImportError:
    print("Install aiohttp: pip install aiohttp")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("Install tqdm: pip install tqdm")
    sys.exit(1)

# ── Config ──

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fotos_jogadores_clubes_ligas.csv")
FOTMOB_SEARCH_URL = "https://www.fotmob.com/api/search/suggest"
FOTMOB_PLAYER_IMG = "https://images.fotmob.com/image_resources/playerimages/{id}.png"
FOTMOB_TEAM_IMG = "https://images.fotmob.com/image_resources/logo/teamlogo/{id}.png"
FOTMOB_LEAGUE_IMG = "https://images.fotmob.com/image_resources/logo/leaguelogo/{id}.png"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

MAX_CONCURRENT = 5  # Be polite to FotMob
RATE_LIMIT_DELAY = 0.3  # seconds between requests

# ── Normalization ──

def _normalize(s: str) -> str:
    import unicodedata
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return stripped.strip().lower()


def _name_similarity(a: str, b: str) -> float:
    """Simple token overlap similarity."""
    a_tokens = set(_normalize(a).split())
    b_tokens = set(_normalize(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    overlap = len(a_tokens & b_tokens)
    return overlap / max(len(a_tokens), len(b_tokens))


# ── FotMob API ──

async def search_fotmob_player(
    session: aiohttp.ClientSession,
    player_name: str,
    team_name: str = "",
    semaphore: asyncio.Semaphore = None,
) -> Optional[dict]:
    """Search FotMob for a player. Returns {id, name, team_id, team_name} or None."""
    if semaphore:
        async with semaphore:
            return await _do_search(session, player_name, team_name)
    return await _do_search(session, player_name, team_name)


async def _do_search(session: aiohttp.ClientSession, player_name: str, team_name: str) -> Optional[dict]:
    await asyncio.sleep(RATE_LIMIT_DELAY)
    try:
        async with session.get(
            FOTMOB_SEARCH_URL,
            params={"term": player_name, "lang": "pt"},
            headers=HEADERS,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

        # FotMob search returns: { squadMember: [...], teams: [...], leagues: [...] }
        players = data.get("squadMember") or data.get("players") or []
        if not players:
            return None

        # Score each result
        best = None
        best_score = -1.0
        team_norm = _normalize(team_name)

        for p in players:
            name = p.get("name") or p.get("title") or ""
            pid = p.get("id")
            p_team = p.get("teamName") or ""

            if not pid:
                continue

            score = _name_similarity(player_name, name)

            # Team match bonus
            if team_norm and _normalize(p_team):
                team_sim = _name_similarity(team_name, p_team)
                score += team_sim * 0.5

            if score > best_score:
                best_score = score
                best = {
                    "id": pid,
                    "name": name,
                    "team_id": p.get("teamId"),
                    "team_name": p_team,
                }

        # Threshold
        if best and best_score >= 0.3:
            return best
        return None

    except Exception as e:
        return None


async def search_fotmob_team(
    session: aiohttp.ClientSession,
    team_name: str,
    semaphore: asyncio.Semaphore = None,
) -> Optional[dict]:
    """Search FotMob for a team. Returns {id, name} or None."""
    if semaphore:
        async with semaphore:
            return await _do_team_search(session, team_name)
    return await _do_team_search(session, team_name)


async def _do_team_search(session: aiohttp.ClientSession, team_name: str) -> Optional[dict]:
    await asyncio.sleep(RATE_LIMIT_DELAY)
    try:
        async with session.get(
            FOTMOB_SEARCH_URL,
            params={"term": team_name, "lang": "pt"},
            headers=HEADERS,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

        teams = data.get("teams") or []
        if not teams:
            return None

        best = None
        best_score = -1.0
        for t in teams:
            name = t.get("name") or t.get("title") or ""
            tid = t.get("id")
            if not tid:
                continue
            score = _name_similarity(team_name, name)
            if score > best_score:
                best_score = score
                best = {"id": tid, "name": name}

        if best and best_score >= 0.4:
            return best
        return None

    except Exception:
        return None


# ── Main migration ──

async def migrate():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}")
        sys.exit(1)

    # Read CSV
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    print(f"Loaded {len(rows)} entries from CSV")

    # Backup
    backup_path = CSV_PATH + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(CSV_PATH, backup_path)
    print(f"Backup created: {backup_path}")

    # Collect unique players and teams
    unique_players = {}  # (player_name, team) -> row indices
    unique_teams = {}    # team_name -> row indices

    for i, row in enumerate(rows):
        player = row.get("Jogador", "").strip()
        team = row.get("Equipa_CSV", "").strip()
        if player:
            key = (player, team)
            unique_players.setdefault(key, []).append(i)
        if team:
            unique_teams.setdefault(team, []).append(i)

    print(f"Unique players: {len(unique_players)}, Unique teams: {len(unique_teams)}")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    stats = {"player_found": 0, "player_not_found": 0, "team_found": 0, "team_not_found": 0}

    # Cache for team lookups
    team_cache: dict[str, Optional[dict]] = {}

    async with aiohttp.ClientSession() as session:
        # 1. Search for teams first (fewer unique)
        print("\n── Searching teams on FotMob ──")
        for team_name in tqdm(list(unique_teams.keys()), desc="Teams"):
            result = await search_fotmob_team(session, team_name, semaphore)
            team_cache[team_name] = result
            if result:
                stats["team_found"] += 1
                # Update club logo for all rows with this team
                logo_url = FOTMOB_TEAM_IMG.format(id=result["id"])
                for idx in unique_teams[team_name]:
                    rows[idx]["Escudo_Clube_URL"] = logo_url
            else:
                stats["team_not_found"] += 1

        # 2. Search for players
        print("\n── Searching players on FotMob ──")
        for (player_name, team_name), indices in tqdm(unique_players.items(), desc="Players"):
            result = await search_fotmob_player(session, player_name, team_name, semaphore)
            if result:
                stats["player_found"] += 1
                photo_url = FOTMOB_PLAYER_IMG.format(id=result["id"])
                for idx in indices:
                    rows[idx]["Foto_Jogador_URL"] = photo_url
                    rows[idx]["Jogador_Sofascore"] = result["name"]  # Update matched name
                    # If team was also found via player search, update team logo too
                    if result.get("team_id") and not team_cache.get(team_name):
                        team_logo = FOTMOB_TEAM_IMG.format(id=result["team_id"])
                        for idx2 in indices:
                            rows[idx2]["Escudo_Clube_URL"] = team_logo
            else:
                stats["player_not_found"] += 1

    # Add FotMob columns if not present
    if "Foto_Jogador_URL" not in fieldnames:
        fieldnames.append("Foto_Jogador_URL")

    # Write updated CSV
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n── Migration complete ──")
    print(f"Players found: {stats['player_found']} / {len(unique_players)}")
    print(f"Teams found:   {stats['team_found']} / {len(unique_teams)}")
    print(f"Updated CSV:   {CSV_PATH}")
    print(f"Backup at:     {backup_path}")


if __name__ == "__main__":
    asyncio.run(migrate())
