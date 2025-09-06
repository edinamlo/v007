"""
processor.py

Directory scanning and grouping for parsed items.
Uses parser.parse_filename() to extract metadata and groups
items by their core identifiers (clean_title, media_type, year).
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Tuple, Any
from parser import parse_filename
from clue_manager import load_clue_mapping

def parse_directory(source_dir: str, mode: str = "dirs", quiet: bool = True) -> Dict:
    """
    Parse items in a directory (folders or files only, no recursion).

    Args:
        source_dir (str): Base directory to scan.
        mode (str): "dirs" or "files".
        quiet (bool): If True, parser runs without console output.

    Returns:
        dict: Contains "raw" (per-path results) and "grouped" (by media item).
    """
    source = Path(source_dir)
    if not source.is_dir():
        print(f"Error: Directory not found at '{source_dir}'")
        return {"raw": {}, "grouped": {}}

    results = {}
    # Load custom clues once before the loop for efficiency
    custom_clues = load_clue_mapping("clues_overrides.json")

    if mode == "dirs":
        items = [p for p in source.iterdir() if p.is_dir()]
    elif mode == "files":
        items = [p for p in source.iterdir() if p.is_file()]
    else:
        raise ValueError("mode must be 'dirs' or 'files'")

    for p in items:
        # Pass the loaded clues to the parser
        results[str(p.resolve())] = parse_filename(p.name, quiet=quiet, overrides=custom_clues)

    # Grouping logic: the key is what defines a unique media item.
    # e.g., "Movie 12 (2009) [1080p]" and "Movie 12 (2009) [4k]"
    # should belong to the same group: ("Movie 12", "movie", "2009").
    grouped: Dict[Tuple[str, str, Any], Dict[str, Any]] = defaultdict(lambda: {"paths": []})

    for path, meta in results.items():
        media_type = (
            "tv" if meta["tv_clues"] else
            "anime" if meta["anime_clues"] else
            "movie" if meta["movie_clues"] else
            "unknown"
        )
        year = meta["movie_clues"][0] if meta["movie_clues"] else None

        # A clean title is required for a valid group
        if not meta["clean_title"]:
            continue

        key = (meta["clean_title"], media_type, year)
        grouped[key]["paths"].append(path)
        # Store useful metadata with the group
        grouped[key].update({
            "media_type": media_type,
            "year": year,
            "clean_title": meta["clean_title"]
        })

    return {"raw": results, "grouped": dict(grouped)}
