#!/usr/bin/env python3
"""
build_fmref_mapping.py — Build FM UID→name mapping for sortitoutsi graphics packs.

This script automates the mapping between the scouting dashboard players/teams
and Football Manager unique IDs (used by sortitoutsi.net packs).

== WORKFLOW ==

Option A — Using fmref.com data export (recommended):
  1. Export the FM database to CSV using FM Editor or fmref.com data files
     The CSV should have columns: uid, name (and optionally: team, nation)
  2. Run this script to auto-match against dashboard players:

     python scripts/build_fmref_mapping.py faces \
         --fm-data fm_people.csv \
         --min-score 85

Option B — Using sortitoutsi config.xml + FM Editor export:
  1. Extract sortitoutsi pack, locate config.xml (lists all UIDs in the pack)
  2. Export FM data with names from FM Editor
  3. Run this script to cross-reference

Option C — Manual quick-paste mode:
  1. Search players on fmref.com, press "c" to copy UID
  2. Add lines to a simple text file: uid,player_name
  3. Use import_graphics_pack.py --mapping with that file

Output: a mapping CSV ready for import_graphics_pack.py
"""

import argparse
import csv
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Try to import rapidfuzz for better matching; fall back to basic matching
try:
    from rapidfuzz import fuzz, process

    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False
    print("WARN: rapidfuzz not installed. Install with: pip install rapidfuzz")
    print("      Falling back to basic exact matching.\n")


def normalize_name(name: str) -> str:
    """Normalize name: remove accents, lowercase, strip punctuation."""
    if not name:
        return ""
    name = unicodedata.normalize("NFD", str(name))
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^a-z0-9\s]", "", name.lower())
    return " ".join(name.split())


def load_dashboard_players(csv_path: str) -> List[dict]:
    """Load player names and teams from the dashboard CSV."""
    players = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Jogador", "").strip()
            team = row.get("Equipa_CSV", "").strip()
            sofascore_name = row.get("Jogador_Sofascore", "").strip()
            if name:
                players.append({
                    "name": name,
                    "team": team,
                    "sofascore_name": sofascore_name,
                    "name_norm": normalize_name(sofascore_name or name),
                })
    return players


def load_dashboard_teams(csv_path: str) -> List[str]:
    """Load unique team names from the dashboard CSV."""
    teams = set()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = row.get("Equipa_CSV", "").strip()
            sofascore_team = row.get("Equipa_Sofascore", "").strip()
            if team:
                teams.add(team)
            if sofascore_team:
                teams.add(sofascore_team)
    return sorted(teams)


def load_fm_data(fm_csv_path: str, entity_type: str) -> Dict[str, dict]:
    """Load FM data CSV exported from FM Editor or similar.

    Expected columns vary but common ones:
      - For people: uid (or UID or unique_id), name (or Name), club/team
      - For clubs:  uid, name
    Auto-detects column names.
    """
    entries = {}
    with open(fm_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = [h.lower().strip() for h in reader.fieldnames] if reader.fieldnames else []

        # Auto-detect UID column
        uid_col = None
        for candidate in ["uid", "unique_id", "id", "uniqueid", "person_uid", "club_uid", "team_uid"]:
            for h in reader.fieldnames or []:
                if h.lower().strip() == candidate:
                    uid_col = h
                    break
            if uid_col:
                break

        # Auto-detect name column
        name_col = None
        for candidate in ["name", "full_name", "player_name", "team_name", "club_name", "nome"]:
            for h in reader.fieldnames or []:
                if h.lower().strip() == candidate:
                    name_col = h
                    break
            if name_col:
                break

        if not uid_col or not name_col:
            print(f"ERROR: Could not detect columns. Found: {reader.fieldnames}")
            print(f"  Need a UID column (uid/unique_id/id) and a name column (name/full_name)")
            sys.exit(1)

        print(f"Using columns: UID='{uid_col}', Name='{name_col}'")

        for row in reader:
            uid = row.get(uid_col, "").strip()
            name = row.get(name_col, "").strip()
            if uid and name:
                entries[uid] = {
                    "uid": uid,
                    "name": name,
                    "name_norm": normalize_name(name),
                }

    return entries


def load_sortitoutsi_uids(pack_dir: str) -> set:
    """Get set of UIDs available in the sortitoutsi pack (numeric filenames)."""
    uids = set()
    extensions = {".png", ".jpg", ".jpeg", ".webp"}
    pack_path = Path(pack_dir)
    if not pack_path.exists():
        return uids
    for f in pack_path.rglob("*"):
        if f.suffix.lower() in extensions and f.stem.isdigit():
            uids.add(f.stem)
    return uids


def match_players(
    dashboard_players: List[dict],
    fm_data: Dict[str, dict],
    available_uids: Optional[set],
    min_score: int = 85,
) -> List[dict]:
    """Match dashboard players to FM data using fuzzy matching."""
    if not HAS_RAPIDFUZZ:
        return _match_exact(dashboard_players, fm_data, available_uids)

    # Build search index from FM data
    fm_names = {}  # norm_name → uid
    fm_choices = []  # list of (norm_name, uid) for fuzzy search

    for uid, entry in fm_data.items():
        norm = entry["name_norm"]
        if available_uids and uid not in available_uids:
            continue  # Skip FM entries not in the pack
        if norm not in fm_names:
            fm_names[norm] = uid
            fm_choices.append(norm)

    print(f"FM database: {len(fm_data)} entries, {len(fm_choices)} with images in pack")

    matches = []
    no_match = []

    for player in dashboard_players:
        pname = player["name_norm"]
        if not pname:
            continue

        # Exact match first
        if pname in fm_names:
            uid = fm_names[pname]
            matches.append({
                "uid": uid,
                "player_name": player["sofascore_name"] or player["name"],
                "team_name": player["team"],
                "fm_name": fm_data[uid]["name"],
                "score": 100,
            })
            continue

        # Fuzzy match
        result = process.extractOne(pname, fm_choices, scorer=fuzz.token_sort_ratio)
        if result and result[1] >= min_score:
            matched_norm = result[0]
            uid = fm_names[matched_norm]
            matches.append({
                "uid": uid,
                "player_name": player["sofascore_name"] or player["name"],
                "team_name": player["team"],
                "fm_name": fm_data[uid]["name"],
                "score": result[1],
            })
        else:
            no_match.append(player["name"])

    return matches, no_match


def _match_exact(dashboard_players, fm_data, available_uids):
    """Fallback: exact name matching only (no rapidfuzz)."""
    fm_by_norm = {}
    for uid, entry in fm_data.items():
        if available_uids and uid not in available_uids:
            continue
        fm_by_norm.setdefault(entry["name_norm"], uid)

    matches = []
    no_match = []
    for player in dashboard_players:
        pname = player["name_norm"]
        if pname in fm_by_norm:
            uid = fm_by_norm[pname]
            matches.append({
                "uid": uid,
                "player_name": player["sofascore_name"] or player["name"],
                "team_name": player["team"],
                "fm_name": fm_data[uid]["name"],
                "score": 100,
            })
        else:
            no_match.append(player["name"])

    return matches, no_match


def match_teams(
    dashboard_teams: List[str],
    fm_data: Dict[str, dict],
    available_uids: Optional[set],
    min_score: int = 80,
) -> Tuple[List[dict], List[str]]:
    """Match dashboard teams to FM data using fuzzy matching."""
    if not HAS_RAPIDFUZZ:
        fm_by_norm = {}
        for uid, entry in fm_data.items():
            if available_uids and uid not in available_uids:
                continue
            fm_by_norm.setdefault(entry["name_norm"], uid)

        matches = []
        no_match = []
        for team in dashboard_teams:
            norm = normalize_name(team)
            if norm in fm_by_norm:
                uid = fm_by_norm[norm]
                matches.append({"uid": uid, "team_name": team, "fm_name": fm_data[uid]["name"], "score": 100})
            else:
                no_match.append(team)
        return matches, no_match

    fm_names = {}
    fm_choices = []
    for uid, entry in fm_data.items():
        if available_uids and uid not in available_uids:
            continue
        norm = entry["name_norm"]
        if norm not in fm_names:
            fm_names[norm] = uid
            fm_choices.append(norm)

    matches = []
    no_match = []
    for team in dashboard_teams:
        norm = normalize_name(team)
        if norm in fm_names:
            uid = fm_names[norm]
            matches.append({"uid": uid, "team_name": team, "fm_name": fm_data[uid]["name"], "score": 100})
            continue

        result = process.extractOne(norm, fm_choices, scorer=fuzz.token_sort_ratio)
        if result and result[1] >= min_score:
            uid = fm_names[result[0]]
            matches.append({"uid": uid, "team_name": team, "fm_name": fm_data[uid]["name"], "score": result[1]})
        else:
            no_match.append(team)

    return matches, no_match


def main():
    parser = argparse.ArgumentParser(
        description="Build FM UID mapping for sortitoutsi graphics packs"
    )
    parser.add_argument(
        "type", choices=["faces", "logos"],
        help="Type of mapping to build"
    )
    parser.add_argument(
        "--fm-data", required=True,
        help="Path to FM database CSV (from FM Editor export or fmref.com data)"
    )
    parser.add_argument(
        "--pack-dir",
        help="Path to sortitoutsi pack directory (to filter only UIDs with images)"
    )
    parser.add_argument(
        "--dashboard-csv",
        help="Path to dashboard CSV (default: auto-detect fotos_jogadores_clubes_ligas.csv)"
    )
    parser.add_argument(
        "--min-score", type=int, default=85,
        help="Minimum fuzzy match score 0-100 (default: 85)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output mapping CSV path (default: fm_{type}_mapping.csv)"
    )

    args = parser.parse_args()

    # Find dashboard CSV
    if args.dashboard_csv:
        dashboard_csv = args.dashboard_csv
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        dashboard_csv = os.path.join(project_root, "fotos_jogadores_clubes_ligas.csv")
        if not os.path.exists(dashboard_csv):
            print(f"ERROR: Dashboard CSV not found at {dashboard_csv}")
            print("  Use --dashboard-csv to specify the path")
            sys.exit(1)

    # Output path
    output_path = args.output or f"fm_{args.type}_mapping.csv"

    print(f"=== Building FM {args.type} mapping ===\n")

    # Load FM data
    print(f"Loading FM data from: {args.fm_data}")
    fm_data = load_fm_data(args.fm_data, args.type)
    print(f"  {len(fm_data)} entries loaded\n")

    # Load available UIDs from pack (optional filter)
    available_uids = None
    if args.pack_dir:
        available_uids = load_sortitoutsi_uids(args.pack_dir)
        print(f"Pack directory: {len(available_uids)} images found\n")

    # Load dashboard data and match
    if args.type == "faces":
        print(f"Loading dashboard players from: {dashboard_csv}")
        players = load_dashboard_players(dashboard_csv)
        print(f"  {len(players)} players loaded\n")

        print(f"Matching (min score: {args.min_score})...")
        matches, no_match = match_players(players, fm_data, available_uids, args.min_score)

        # Write output
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["uid", "player_name", "team_name", "fm_name", "score"])
            writer.writeheader()
            for m in sorted(matches, key=lambda x: x["score"], reverse=True):
                writer.writerow(m)

    else:  # logos
        print(f"Loading dashboard teams from: {dashboard_csv}")
        teams = load_dashboard_teams(dashboard_csv)
        print(f"  {len(teams)} unique teams loaded\n")

        print(f"Matching (min score: {args.min_score})...")
        matches, no_match = match_teams(teams, fm_data, available_uids, args.min_score)

        # Write output
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["uid", "team_name", "fm_name", "score"])
            writer.writeheader()
            for m in sorted(matches, key=lambda x: x["score"], reverse=True):
                writer.writerow(m)

    # Summary
    print(f"\n=== Results ===")
    print(f"  Matched: {len(matches)}")
    print(f"  No match: {len(no_match)}")
    print(f"  Output: {output_path}")

    if no_match:
        print(f"\n  Top unmatched (search on fmref.com):")
        for name in no_match[:20]:
            print(f"    - {name}")
        if len(no_match) > 20:
            print(f"    ... and {len(no_match) - 20} more")

    print(f"\n=== Next step ===")
    print(f"  python scripts/import_graphics_pack.py {args.type} \\")
    print(f"      --pack-dir /path/to/sortitoutsi/{args.type} \\")
    print(f"      --mapping {output_path}")


if __name__ == "__main__":
    main()
