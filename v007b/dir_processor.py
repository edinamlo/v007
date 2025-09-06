"""
Directory processing: scan root folders or files and group parsed results.
"""

from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List
from parser import parse_filename


def parse_directory(source_dir: str, mode: str = "dirs", quiet: bool = True) -> Dict[str, Any]:
    """
    Parse the immediate children of source_dir.

    Args:
        source_dir: path to scan
        mode: "dirs" (default) or "files"
        quiet: if True, parser runs without console prints

    Returns:
        dict with:
          - raw: mapping absolute_path -> parse result dict
          - grouped: mapping (clean_title, media_type, year) -> dict(paths: [...], meta: {...})
    """
    root = Path(source_dir)
    raw: Dict[str, Dict] = {}
    if mode == "dirs":
        items = [p for p in root.iterdir() if p.is_dir()]
    elif mode == "files":
        items = [p for p in root.iterdir() if p.is_file()]
    else:
        raise ValueError("mode must be 'dirs' or 'files'")

    for p in items:
        result = parse_filename(p.name, quiet=quiet)
        result["path"] = str(p.resolve())
        raw[str(p.resolve())] = result

    grouped: Dict[tuple, Dict[str, Any]] = {}
    buckets = defaultdict(lambda: {"paths": [], "media_type": None, "year": None})
    for path, meta in raw.items():
        media_type = ("tv" if meta["tv_clues"] else
                      "anime" if meta["anime_clues"] else
                      "movie" if meta["movie_clues"] else "unknown")
        year = meta["movie_clues"][0] if meta["movie_clues"] else None
        key = (meta["clean_title"], media_type, year)
        buckets[key]["paths"].append(path)
        buckets[key]["media_type"] = media_type
        buckets[key]["year"] = year

    grouped = {k: v for k, v in buckets.items()}
    return {"raw": raw, "grouped": grouped}
