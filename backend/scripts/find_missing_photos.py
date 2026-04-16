#!/usr/bin/env python3
"""
find_missing_photos.py — Report players whose photo lookup chain returns nothing.

Runs the same FM sortitoutsi → graphics pack → CSV resolution used at request
time and lists every CSV entry that still has no usable photo URL. Useful as
input to build_fmref_mapping.py or to manually populate graphics_packs/faces/.

Usage:
    python backend/scripts/find_missing_photos.py            # print report
    python backend/scripts/find_missing_photos.py -o out.csv # also write CSV
"""

import argparse
import csv
import os
import sys
from collections import Counter

# Make `services` importable when running the script directly.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_SCRIPT_DIR)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", help="Write missing players to this CSV path")
    parser.add_argument(
        "--limit", type=int, default=30,
        help="How many rows to print to stdout (default 30)",
    )
    args = parser.parse_args()

    from services.player_assets import list_players_without_photos
    from services.fm_sortitoutsi import get_stats as fm_stats

    stats = fm_stats()
    print(f"FM sortitoutsi index: {stats['faces']} faces "
          f"({stats['faces_with_team']} with team), {stats['logos']} logos, "
          f"fuzzy={stats['fuzzy_enabled']}")

    missing = list_players_without_photos()
    quality_counts = Counter(r["quality"] for r in missing)
    by_team = Counter(r["equipa"] for r in missing if r["equipa"])

    print(f"\nPlayers without a usable photo: {len(missing)}")
    print("  By CSV match quality:", dict(quality_counts))
    print("\n  Top teams missing photos:")
    for team, count in by_team.most_common(10):
        print(f"    {count:3d}  {team}")

    print(f"\n  First {args.limit} entries:")
    for row in missing[:args.limit]:
        alt = f" (sofa: {row['sofascore_name']})" if row["sofascore_name"] else ""
        print(f"    - [{row['quality']:>15s}] {row['jogador']} / {row['equipa']}{alt}")

    if args.output:
        fields = ["jogador", "equipa", "sofascore_name", "quality"]
        with open(args.output, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in missing:
                writer.writerow({k: row.get(k, "") for k in fields})
        print(f"\nWrote {len(missing)} rows to {args.output}")


if __name__ == "__main__":
    main()
