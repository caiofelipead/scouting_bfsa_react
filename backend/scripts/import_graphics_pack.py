#!/usr/bin/env python3
"""
import_graphics_pack.py — Import sortitoutsi.net graphics packs into the scouting dashboard.

Usage:
    # Import faces with FM ID mapping
    python scripts/import_graphics_pack.py faces \
        --pack-dir /path/to/sortitoutsi/faces \
        --mapping fm_faces_mapping.csv

    # Import logos with FM ID mapping
    python scripts/import_graphics_pack.py logos \
        --pack-dir /path/to/sortitoutsi/logos \
        --mapping fm_logos_mapping.csv

    # Import faces/logos by name (files already named correctly)
    python scripts/import_graphics_pack.py faces \
        --pack-dir /path/to/named-faces

The mapping CSV format:
    Faces: uid,player_name,team_name  (team_name is optional)
    Logos: uid,team_name
"""

import argparse
import csv
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path


def normalize_name(name: str) -> str:
    """Normalize name: remove accents, lowercase, strip punctuation."""
    if not name:
        return ""
    name = unicodedata.normalize("NFD", str(name))
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^a-z0-9\s]", "", name.lower())
    return " ".join(name.split())


def find_image_files(pack_dir: str) -> dict:
    """Find all image files in the pack directory, returning {stem: full_path}."""
    extensions = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
    files = {}
    pack_path = Path(pack_dir)

    if not pack_path.exists():
        print(f"ERROR: Pack directory not found: {pack_dir}")
        sys.exit(1)

    for f in pack_path.rglob("*"):
        if f.suffix.lower() in extensions and f.is_file():
            # Use stem (filename without extension) as the key
            files[f.stem] = f
    return files


def import_with_mapping(pack_dir: str, mapping_path: str, output_dir: str, pack_type: str):
    """Import images using a UID→name mapping CSV."""
    image_files = find_image_files(pack_dir)
    print(f"Found {len(image_files)} image files in pack directory")

    if not os.path.exists(mapping_path):
        print(f"ERROR: Mapping file not found: {mapping_path}")
        sys.exit(1)

    imported = 0
    skipped = 0

    with open(mapping_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row.get("uid", "").strip()
            if not uid:
                continue

            if pack_type == "faces":
                name = row.get("player_name", "").strip()
            else:
                name = row.get("team_name", "").strip()

            if not name:
                skipped += 1
                continue

            # Find the image file by UID
            if uid not in image_files:
                skipped += 1
                continue

            source = image_files[uid]
            normalized = normalize_name(name)
            if not normalized:
                skipped += 1
                continue

            dest = os.path.join(output_dir, f"{normalized}{source.suffix.lower()}")

            # Don't overwrite existing (first match wins)
            if os.path.exists(dest):
                skipped += 1
                continue

            shutil.copy2(source, dest)
            imported += 1

            if imported % 500 == 0:
                print(f"  ... imported {imported} images")

    print(f"\nDone! Imported: {imported}, Skipped: {skipped}")


def import_by_name(pack_dir: str, output_dir: str):
    """Import images that are already named (no UID mapping needed)."""
    image_files = find_image_files(pack_dir)
    print(f"Found {len(image_files)} image files in pack directory")

    imported = 0
    for stem, source in image_files.items():
        # Skip numeric-only filenames (these are FM UIDs, need mapping)
        if stem.isdigit():
            print(f"  WARN: Skipping {source.name} (numeric UID — needs --mapping)")
            continue

        normalized = normalize_name(stem)
        if not normalized:
            continue

        dest = os.path.join(output_dir, f"{normalized}{source.suffix.lower()}")
        if not os.path.exists(dest):
            shutil.copy2(source, dest)
            imported += 1

    print(f"\nDone! Imported: {imported} images")


def main():
    parser = argparse.ArgumentParser(
        description="Import sortitoutsi.net graphics packs into scouting dashboard"
    )
    parser.add_argument(
        "type", choices=["faces", "logos"],
        help="Type of graphics pack to import"
    )
    parser.add_argument(
        "--pack-dir", required=True,
        help="Path to extracted graphics pack directory"
    )
    parser.add_argument(
        "--mapping",
        help="Path to UID→name mapping CSV (required for sortitoutsi packs with numeric filenames)"
    )

    args = parser.parse_args()

    # Determine output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    output_dir = os.path.join(backend_dir, "graphics_packs", args.type)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Importing {args.type} from: {args.pack_dir}")
    print(f"Output directory: {output_dir}")

    if args.mapping:
        import_with_mapping(args.pack_dir, args.mapping, output_dir, args.type)
    else:
        import_by_name(args.pack_dir, output_dir)


if __name__ == "__main__":
    main()
