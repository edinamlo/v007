"""
Utility helpers for parser project.
"""

import re
from typing import Optional


def clean_title(possible_title: Optional[str]) -> Optional[str]:
    """
    Clean a possible_title according to rules:
      - Dot-separated single-letter acronyms (e.g. s.h.i.e.l.d) should remain as-is.
      - Hyphen-separated numeric like 9-1-1 remain as-is.
      - Otherwise, replace dots/hyphens with spaces and Title Case the words.
    """
    if not possible_title:
        return None

    # Keep dot-acronyms (S.H.I.E.L.D) intact
    if re.fullmatch(r"(?:[A-Za-z]\.){2,}[A-Za-z]?", possible_title):
        return possible_title

    # Keep numeric hyphen sequences like 9-1-1 intact
    if re.fullmatch(r"\d+(?:-\d+)+", possible_title):
        return possible_title

    # Replace . and - with spaces and Title Case
    out = re.sub(r"[._\-]+", " ", possible_title).strip()
    out = " ".join(word.capitalize() if word.isalpha() else word for word in out.split())
    return out
