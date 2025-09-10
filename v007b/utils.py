"""
Utility helpers for parser project.
"""

import re


def remove_asian_chars(text: str) -> str:
    """Remove CJK characters (Chinese, Japanese, Korean) from text."""
    return "".join(ch for ch in text if not _is_cjk(ch))

def _is_cjk(ch: str) -> bool:
    """Check if a char is in CJK unicode blocks."""
    codepoint = ord(ch)
    return (
        0x4E00 <= codepoint <= 0x9FFF   # CJK Unified Ideographs
        or 0x3400 <= codepoint <= 0x4DBF  # CJK Extension A
        or 0x20000 <= codepoint <= 0x2A6DF  # Extension B
        or 0x2A700 <= codepoint <= 0x2B73F  # Extension C
        or 0x2B740 <= codepoint <= 0x2B81F  # Extension D
        or 0x2B820 <= codepoint <= 0x2CEAF  # Extension E
        or 0xF900 <= codepoint <= 0xFAFF   # CJK Compatibility Ideographs
        or 0x2F800 <= codepoint <= 0x2FA1F # Compatibility Supplement
    )

def clean_title(title: str) -> str:
    """Make a readable title while preserving short all-caps tokens (US, UK, TV, etc.)."""
    if not title:
        return title
    # First remove Asian characters
    title = remove_asian_chars(title)
    # split on common separators
    parts = re.split(r"[._\-\s]+", title.strip())
    out_parts = []
    for p in parts:
        if not p:
            continue
        if p.isupper() and len(p) <= 3:
            out_parts.append(p)
        else:
            out_parts.append(p.capitalize())
    return " ".join(out_parts)
