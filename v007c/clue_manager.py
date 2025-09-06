"""
clue_manager.py

Manage unrecognized tokens ("words") and user-defined clue mappings.
Allows extraction of unknowns, saving them to `clues_overrides.json`,
and loading them for parser enrichment.
"""

import json
from collections import defaultdict

def collect_unknown_words(parsed_data):
    """
    Extract unique unknown words from parsed_data["raw"].

    Args:
        parsed_data (dict): Output of processor.parse_directory().

    Returns:
        dict: Unknown word -> frequency.
    """
    counter = defaultdict(int)
    for meta in parsed_data["raw"].values():
        for word in meta.get("words", []):
            counter[word.lower()] += 1
    return dict(sorted(counter.items(), key=lambda x: -x[1]))


def save_clue_mapping(mapping, filepath="clues_overrides.json"):
    """
    Save user-defined clue mapping to file.

    Args:
        mapping (dict): Custom mapping of categories -> tokens.
        filepath (str): Output JSON path.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


def load_clue_mapping(filepath="clues_overrides.json"):
    """
    Load user-defined clue mapping from file.

    Args:
        filepath (str): JSON file path.

    Returns:
        dict: Loaded mapping or an empty default structure.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Return a default structure so the parser doesn't fail
        return {
            "quality_clues": [],
            "release_groups": [],
            "audio_clues": [],
            "resolution_clues": [],
            "misc_clues": []
        }
