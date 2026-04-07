#!/usr/bin/env python3
"""
setup_sortitoutsi.py — All-in-one setup for sortitoutsi CDN integration.
Run from the root of scouting_bfsa_react:
    python3 setup_sortitoutsi.py
"""
import csv, json, time, urllib.request, unicodedata, os, re, sys
from collections import defaultdict

print("=" * 60)
print("SORTITOUTSI CDN INTEGRATION — SETUP")
print("=" * 60)

# ── 1. Verify we're in the right directory ──
if not os.path.exists("backend/services/player_assets.py"):
    print("ERROR: Run this script from the root of scouting_bfsa_react")
    sys.exit(1)

# ── 2. Create backend/data/ directory ──
os.makedirs("backend/data", exist_ok=True)
print("\n✓ backend/data/ directory ready")

# ── 3. Create backend/services/fm_sortitoutsi.py ──
FM_SORTITOUTSI_PY = '''\
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
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_face_urls: Dict[str, str] = {}
_logo_urls: Dict[str, str] = {}
_face_urls_by_name_team: Dict[tuple, str] = {}
_loaded = False

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)


def _normalize(name: str) -> str:
    if not name:
        return ""
    name = unicodedata.normalize("NFD", str(name))
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^a-z0-9\\s]", "", name.lower())
    return " ".join(name.split())


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
                    wyscout_name = row.get("wyscout_name", "").strip()
                    face_url = row.get("face_url", "").strip()
                    score = int(row.get("match_score", "0"))
                    teams = row.get("wyscout_teams", "")
                    if not wyscout_name or not face_url or score < 70:
                        continue
                    name_key = _normalize(wyscout_name)
                    if not name_key:
                        continue
                    if name_key not in _face_urls:
                        _face_urls[name_key] = face_url
                    for team in teams.split("|"):
                        team = team.strip()
                        if team:
                            pair = (name_key, _normalize(team))
                            if pair not in _face_urls_by_name_team:
                                _face_urls_by_name_team[pair] = face_url
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
                    wyscout_name = row.get("wyscout_name", "").strip()
                    logo_url = row.get("logo_url", "").strip()
                    score = int(row.get("match_score", "0"))
                    if not wyscout_name or not logo_url or score < 70:
                        continue
                    name_key = _normalize(wyscout_name)
                    if name_key and name_key not in _logo_urls:
                        _logo_urls[name_key] = logo_url
            logger.info("FM sortitoutsi: %d logos", len(_logo_urls))
        except Exception as e:
            logger.error("Failed to load FM team mappings: %s", e)

    _loaded = True


def _ensure_loaded():
    if not _loaded:
        load_fm_mappings()


def get_face_url(player_name: str, team: str = None) -> Optional[str]:
    _ensure_loaded()
    name_key = _normalize(player_name)
    if not name_key:
        return None
    if team:
        url = _face_urls_by_name_team.get((name_key, _normalize(team)))
        if url:
            return url
    return _face_urls.get(name_key)


def get_logo_url(team_name: str) -> Optional[str]:
    _ensure_loaded()
    name_key = _normalize(team_name)
    return _logo_urls.get(name_key) if name_key else None


def get_stats() -> dict:
    _ensure_loaded()
    return {
        "faces": len(_face_urls),
        "faces_with_team": len(_face_urls_by_name_team),
        "logos": len(_logo_urls),
    }
'''

with open("backend/services/fm_sortitoutsi.py", "w", encoding="utf-8") as f:
    f.write(FM_SORTITOUTSI_PY)
print("✓ backend/services/fm_sortitoutsi.py created")

# ── 4. Generate CSV mappings from Typesense API ──
API_URL = "https://1r3p0ghdzwktqxu9p-1.a1.typesense.net:443/multi_search?x-typesense-api-key=ItfYDIz1mGDuZVXzvkYj0jYJ4avarL02"
CDN_FACE = "https://sortitoutsi.b-cdn.net/uploads/face/face_{}.png"
CDN_LOGO = "https://sortitoutsi.b-cdn.net/uploads/logo/logo_{}.png"
BATCH = 20


def batch_search(queries, filter_by="", per_page=5):
    searches = [{"query_by": "name, fm_id, search_terms", "query_by_weights": "2,4,1",
        "sort_by": "_text_match:desc,reputation:desc", "collection": "detailed_game_items",
        "q": q, "page": 1, "per_page": per_page, "filter_by": filter_by} for q in queries]
    body = json.dumps({"searches": searches}).encode()
    req = urllib.request.Request(API_URL, data=body, headers={"Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return [r.get("hits", []) for r in json.loads(resp.read()).get("results", [])]
        except Exception:
            time.sleep(1)
    return [[] for _ in queries]


def norm(name):
    name = unicodedata.normalize('NFD', name.lower())
    return ''.join(c for c in name if unicodedata.category(c) != 'Mn').strip()


def match_score(query, doc, team_hints=None):
    q, r = norm(query), norm(doc.get("name", ""))
    if q == r:
        return 100
    for t in doc.get("search_terms", []):
        if q == norm(t):
            return 95
    qp, rp = q.split(), r.split()
    if all(x in r for x in qp):
        return 90
    qp_clean = [x.rstrip('.') for x in qp if len(x.rstrip('.')) > 1]
    if qp_clean:
        if all(x in r for x in qp_clean):
            return 85
        if qp_clean[-1] in rp:
            return 70
    elif len(qp) >= 2 and qp[-1] in rp:
        return 70
    m = sum(1 for x in (qp_clean or qp) if any(x in y for y in rp))
    base = 50 * m / len(qp_clean or qp) if m else 0
    if team_hints and base > 0:
        ht = norm(doc.get("team", {}).get("name", ""))
        for th in team_hints:
            if norm(th) in ht or ht in norm(th):
                base += 10
                break
    return base


# Load players and teams from fotos CSV
players = set()
teams = set()
p2t = defaultdict(set)

csv_file = "fotos_jogadores_clubes_ligas.csv"
if os.path.exists(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            n = row.get('Jogador', '').strip()
            t = row.get('Equipa_CSV', '').strip()
            if n:
                players.add(n)
            if t:
                teams.add(t)
            if n and t:
                p2t[n].add(t)

print(f"\nSource CSV: {len(players)} players, {len(teams)} teams")

# Search players
all_names = sorted(players)
matched_p = []

print(f"\n--- Searching {len(all_names)} players via Typesense ---")
for i in range(0, len(all_names), BATCH):
    batch = all_names[i:i+BATCH]
    results = batch_search(batch, "type_id:person", 5)
    for name, hits in zip(batch, results):
        ts = p2t.get(name, set())
        best, bs = None, 0
        for h in hits:
            d = h.get("document", {})
            s = match_score(name, d, ts)
            if s > bs:
                bs, best = s, d
        if best and bs >= 50:
            fid = best.get("fm_id", "")
            matched_p.append({
                "wyscout_name": name, "search_name": name,
                "fm_name": best.get("name", ""),
                "fm_id": fid,
                "fm_team": best.get("team", {}).get("name", ""),
                "match_score": int(bs),
                "face_url": CDN_FACE.format(fid),
                "wyscout_teams": "|".join(ts),
            })
    done = min(i + BATCH, len(all_names))
    if done % 500 == 0 or done == len(all_names):
        print(f"  {done}/{len(all_names)} ({done*100//len(all_names)}%) - matched: {len(matched_p)}")
    time.sleep(0.15)

# Search teams
TEAM_OVERRIDES = {"ASA": "Agremiacao Sportiva Arapiraquense"}
team_list = sorted(teams)
matched_t = []

print(f"\n--- Searching {len(team_list)} teams via Typesense ---")
for i in range(0, len(team_list), BATCH):
    batch = team_list[i:i+BATCH]
    queries = [TEAM_OVERRIDES.get(t, t) for t in batch]
    results = batch_search(queries, "type_id:team", 5)
    for name, query, hits in zip(batch, queries, results):
        best, bs = None, 0
        for h in hits:
            d = h.get("document", {})
            s = match_score(query, d)
            if query != name:
                s = max(s, match_score(name, d) + 5)
            if s > bs:
                bs, best = s, d
        if best and bs >= 50:
            fid = best.get("fm_id", "")
            matched_t.append({
                "wyscout_name": name,
                "fm_name": best.get("name", ""),
                "fm_id": fid,
                "fm_nation": best.get("nation", {}).get("name", ""),
                "match_score": int(bs),
                "logo_url": CDN_LOGO.format(fid),
            })
    done = min(i + BATCH, len(team_list))
    if done % 200 == 0 or done == len(team_list):
        print(f"  {done}/{len(team_list)} ({done*100//len(team_list)}%) - matched: {len(matched_t)}")
    time.sleep(0.15)

# Write CSVs
with open("backend/data/fm_mapping_jogadores.csv", 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, ["wyscout_name", "search_name", "fm_name", "fm_id", "fm_team",
                           "match_score", "face_url", "wyscout_teams"])
    w.writeheader()
    w.writerows(sorted(matched_p, key=lambda x: -x["match_score"]))

with open("backend/data/fm_mapping_times.csv", 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, ["wyscout_name", "fm_name", "fm_id", "fm_nation", "match_score", "logo_url"])
    w.writeheader()
    w.writerows(sorted(matched_t, key=lambda x: -x["match_score"]))

print(f"\n✓ Players matched: {len(matched_p)}")
print(f"✓ Teams matched: {len(matched_t)}")
print(f"✓ CSVs saved to backend/data/")

# ── 5. Edit backend/services/player_assets.py ──
PA_FILE = "backend/services/player_assets.py"
with open(PA_FILE, "r", encoding="utf-8") as f:
    pa_content = f.read()

OLD_PA = """    # 0) Local graphics packs (sortitoutsi / manual) — highest priority
    try:
        from services.graphics_packs import has_local_face, has_local_logo
        if name_norm and has_local_face(player_name):
            result["photo_url"] = f"/api/player-face/{player_name}"
        if team_norm and has_local_logo(team):
            result["club_logo"] = f"/api/team-logo/{team_norm}"
    except Exception:
        pass"""

NEW_PA = """    # 0a) FM sortitoutsi CDN (cut-out faces & logos) — highest priority
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
        pass"""

if OLD_PA in pa_content:
    pa_content = pa_content.replace(OLD_PA, NEW_PA)
    with open(PA_FILE, "w", encoding="utf-8") as f:
        f.write(pa_content)
    print("\n✓ backend/services/player_assets.py updated")
else:
    print("\n⚠ player_assets.py: pattern not found (may already be updated)")

# ── 6. Edit backend/routes/proxy.py ──
PX_FILE = "backend/routes/proxy.py"
with open(PX_FILE, "r", encoding="utf-8") as f:
    px_content = f.read()

OLD_PX = """    # Priority 0: Check local graphics pack (sortitoutsi / manual)
    try:
        from services.graphics_packs import get_local_logo
        local = get_local_logo(team_name_norm)
        if local:
            data, ct = local
            return Response(
                content=data, media_type=ct,
                headers={"Cache-Control": "public, max-age=604800", "Access-Control-Allow-Origin": "*"},
            )
    except Exception:
        pass"""

NEW_PX = """    # Priority 0a: FM sortitoutsi CDN logo
    try:
        from services.fm_sortitoutsi import get_logo_url
        fm_logo = get_logo_url(team_name_norm)
        if fm_logo:
            from starlette.responses import RedirectResponse
            proxy_url = f"/api/image-proxy?url={quote(fm_logo, safe='')}"
            return RedirectResponse(url=proxy_url, status_code=307)
    except Exception:
        pass

    # Priority 0b: Check local graphics pack (manual overrides)
    try:
        from services.graphics_packs import get_local_logo
        local = get_local_logo(team_name_norm)
        if local:
            data, ct = local
            return Response(
                content=data, media_type=ct,
                headers={"Cache-Control": "public, max-age=604800", "Access-Control-Allow-Origin": "*"},
            )
    except Exception:
        pass"""

if OLD_PX in px_content:
    px_content = px_content.replace(OLD_PX, NEW_PX)
    with open(PX_FILE, "w", encoding="utf-8") as f:
        f.write(px_content)
    print("✓ backend/routes/proxy.py updated")
else:
    print("⚠ proxy.py: pattern not found (may already be updated)")

# ── 7. Edit backend/main.py ──
MN_FILE = "backend/main.py"
with open(MN_FILE, "r", encoding="utf-8") as f:
    mn_content = f.read()

OLD_MN = """        # Load local graphics packs (sortitoutsi faces & logos)
        try:
            from services.graphics_packs import load_graphics_packs
            load_graphics_packs()
        except Exception as e:
            logger.warning("Could not load graphics packs: %s", e)"""

NEW_MN = """        # Load FM sortitoutsi CDN mappings (faces & logos from fmref.com)
        try:
            from services.fm_sortitoutsi import load_fm_mappings, get_stats
            load_fm_mappings()
            fm_stats = get_stats()
            logger.info("FM sortitoutsi CDN: %d faces, %d logos", fm_stats["faces"], fm_stats["logos"])
        except Exception as e:
            logger.warning("Could not load FM sortitoutsi mappings: %s", e)

        # Load local graphics packs (manual overrides)
        try:
            from services.graphics_packs import load_graphics_packs
            load_graphics_packs()
        except Exception as e:
            logger.warning("Could not load graphics packs: %s", e)"""

if OLD_MN in mn_content:
    mn_content = mn_content.replace(OLD_MN, NEW_MN)
    with open(MN_FILE, "w", encoding="utf-8") as f:
        f.write(mn_content)
    print("✓ backend/main.py updated")
else:
    print("⚠ main.py: pattern not found (may already be updated)")

# ── Done ──
print("\n" + "=" * 60)
print("SETUP COMPLETE")
print("=" * 60)
print(f"\nFiles created/updated:")
print(f"  NEW: backend/services/fm_sortitoutsi.py")
print(f"  NEW: backend/data/fm_mapping_jogadores.csv ({len(matched_p)} faces)")
print(f"  NEW: backend/data/fm_mapping_times.csv ({len(matched_t)} logos)")
print(f"  MOD: backend/services/player_assets.py")
print(f"  MOD: backend/routes/proxy.py")
print(f"  MOD: backend/main.py")
print(f"\nPriority chain:")
print(f"  FM sortitoutsi CDN > Local packs > API-Football > CSV > Fallback")
print(f"\nNext steps:")
print(f"  git add -A && git commit -m 'feat: integrate sortitoutsi CDN faces and logos'")
print(f"  git push origin HEAD")
