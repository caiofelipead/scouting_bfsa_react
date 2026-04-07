"""
graphics_packs.py — Serve local graphics pack images (faces & logos).

Loads images from backend/graphics_packs/faces/ and backend/graphics_packs/logos/
directories. Files are indexed by normalized name for fast lookup.

Supports sortitoutsi.net packs (imported via scripts/import_graphics_pack.py)
or any manually placed PNG/JPG images named after the player/team.
"""

import logging
import os
import re
import unicodedata
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# In-memory index: normalized_name → (file_path, content_type)
_faces_index: Dict[str, Tuple[str, str]] = {}
_logos_index: Dict[str, Tuple[str, str]] = {}

_loaded = False

_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}

# Base directory for graphics packs
_GRAPHICS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "graphics_packs")


def _normalize(name: str) -> str:
    """Normalize name for lookup: remove accents, lowercase, strip punctuation."""
    if not name:
        return ""
    name = unicodedata.normalize("NFD", str(name))
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^a-z0-9\s]", "", name.lower())
    return " ".join(name.split())


def _build_index(directory: str) -> Dict[str, Tuple[str, str]]:
    """Scan a directory and build a name → (path, content_type) index."""
    index = {}
    if not os.path.isdir(directory):
        return index

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext not in _CONTENT_TYPES:
            continue

        # The filename (without extension) is the normalized name
        name_key = os.path.splitext(filename)[0].strip()
        if name_key:
            index[name_key] = (filepath, _CONTENT_TYPES[ext])

    return index


def load_graphics_packs():
    """Load the graphics pack indices from disk."""
    global _faces_index, _logos_index, _loaded

    faces_dir = os.path.join(_GRAPHICS_DIR, "faces")
    logos_dir = os.path.join(_GRAPHICS_DIR, "logos")

    _faces_index = _build_index(faces_dir)
    _logos_index = _build_index(logos_dir)
    _loaded = True

    if _faces_index or _logos_index:
        logger.info(
            "Graphics packs loaded: %d faces, %d logos",
            len(_faces_index), len(_logos_index),
        )


def _ensure_loaded():
    if not _loaded:
        load_graphics_packs()


def get_local_face(player_name: str) -> Optional[Tuple[bytes, str]]:
    """Look up a local face image by player name.

    Returns (image_bytes, content_type) or None.
    """
    _ensure_loaded()
    if not _faces_index:
        return None

    key = _normalize(player_name)
    if not key:
        return None

    entry = _faces_index.get(key)
    if not entry:
        return None

    filepath, content_type = entry
    try:
        with open(filepath, "rb") as f:
            return f.read(), content_type
    except OSError:
        return None


def get_local_logo(team_name: str) -> Optional[Tuple[bytes, str]]:
    """Look up a local logo image by team name.

    Returns (image_bytes, content_type) or None.
    """
    _ensure_loaded()
    if not _logos_index:
        return None

    key = _normalize(team_name)
    if not key:
        return None

    entry = _logos_index.get(key)
    if not entry:
        return None

    filepath, content_type = entry
    try:
        with open(filepath, "rb") as f:
            return f.read(), content_type
    except OSError:
        return None


def has_local_face(player_name: str) -> bool:
    """Check if a local face exists for a player (without reading bytes)."""
    _ensure_loaded()
    return _normalize(player_name) in _faces_index


def has_local_logo(team_name: str) -> bool:
    """Check if a local logo exists for a team (without reading bytes)."""
    _ensure_loaded()
    return _normalize(team_name) in _logos_index


def get_face_count() -> int:
    _ensure_loaded()
    return len(_faces_index)


def get_logo_count() -> int:
    _ensure_loaded()
    return len(_logos_index)
