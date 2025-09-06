"""
ClueManager

Collects unknown words from parsed results and lets you persist them
and manage known clues.
"""

import json
from pathlib import Path
from typing import Dict, List
from config import CLUES, UNKNOWN_FILE


class ClueManager:
    """
    Manage known/unknown clue lists.

    Attributes:
        known (dict): loaded known clues (from config.CLUES)
        unknown_file (Path): path where unknown tokens are stored
        unknown (list): collected unknown tokens
    """

    def __init__(self, unknown_file: Path = UNKNOWN_FILE):
        self.known: Dict[str, List[str]] = CLUES
        self.unknown_file = Path(unknown_file)
        self.unknown: List[str] = []
        self.load_unknowns()

    def load_unknowns(self):
        """Load unknowns from disk (if present)."""
        if self.unknown_file.exists():
            try:
                with self.unknown_file.open("r", encoding="utf-8") as fh:
                    self.unknown = json.load(fh)
            except Exception:
                self.unknown = []

    def save_unknowns(self):
        """Persist unknown tokens to disk."""
        self.unknown_file.parent.mkdir(parents=True, exist_ok=True)
        with self.unknown_file.open("w", encoding="utf-8") as fh:
            json.dump(self.unknown, fh, indent=2, ensure_ascii=False)

    def collect_from_parsed(self, parsed_raw: Dict[str, Dict]):
        """
        Scan the parsed results and collect unique unknown words (frequency-aware).

        Args:
            parsed_raw: output from dir processor 'raw'
        """
        freq = {}
        for meta in parsed_raw.values():
            for w in meta.get("words", []):
                freq[w] = freq.get(w, 0) + 1
        # sort by frequency desc and add new ones to unknown list
        for w, _count in sorted(freq.items(), key=lambda kv: -kv[1]):
            if w not in self.unknown and not self._is_known(w):
                self.unknown.append(w)

    def _is_known(self, token: str) -> bool:
        """Check if token exists in any known clue category (case-insensitive)."""
        up = token.upper()
        for lst in self.known.values():
            for v in lst:
                if up == v.upper():
                    return True
        return False

    def classify_unknown(self, token: str, category: str):
        """
        Move token from unknown list to a known category.

        Args:
            token: token to classify
            category: one of known CLUES keys (e.g., "quality_clues")
        """
        token = token.strip()
        if token in self.unknown:
            self.unknown.remove(token)
        self.known.setdefault(category, [])
        if token not in self.known[category]:
            self.known[category].append(token)

    def export_known_to_file(self, path: Path):
        """Dump current known clues to a JSON file (path)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(self.known, fh, indent=2, ensure_ascii=False)
