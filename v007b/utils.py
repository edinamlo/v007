"""
Utility helpers for parser project.
"""

import re


def clean_title(title: str) -> str:
    """Make a readable title while preserving short all-caps tokens (US, UK, TV, etc.)."""
    if not title:
        return title
    # split on common separators (dots, underscores, hyphens and whitespace)
    parts = re.split(r"[._\-\s]+", title.strip())
    out_parts = []
    for p in parts:
        if not p:
            continue
        # keep short acronyms intact (all upper, length <= 3)
        if p.isupper() and len(p) <= 3:
            out_parts.append(p)
        else:
            # Capitalize first letter, lowercase the rest for readability
            out_parts.append(p.capitalize())
    return " ".join(out_parts)
