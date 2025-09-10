import re
import os
from typing import List, Optional, Tuple, Dict, Any

# --- Configuration ---
# For a real application, you might move this to a separate JSON or Python file.
KNOWN_CLUES = {
    'release_groups': ['fov', 'syncopy', 'erai-raws', 'megusta', 'beechyboy', 'nc-raws', 'sweetssub'],
    'quality_clues': ['hdtv', 'bluray', 'bdrip', 'web-dl', 'webrip', 'dvdrip', 'bdremux', 'brrip'],
    'audio_clues': ['aac', 'ac3', 'dd5.1', 'dts-hd', 'dts'],
    'resolution_clues': ['480p', '720p', '1080p', '2160p', '4k'],
}

# --- Combined & Prioritized Regex Patterns ---
# Patterns are checked in this order. Word boundaries (\b) are used for accuracy.
TOKEN_PATTERNS = [
    # Highest priority: TV Episode/Season formats
    ('tv_clues', re.compile(r'^\b(s\d{2}e\d{2,4})\b$', re.IGNORECASE)),
    ('tv_clues', re.compile(r'^\b(\d{1,2}x\d{2,4})\b$', re.IGNORECASE)),  # Format: 4x13
    ('tv_clues', re.compile(r'^\b(s\d{2}(?:-s\d{2})?)\b$', re.IGNORECASE)),
    ('tv_clues', re.compile(r'^\b(season[\s.]?\d{1,2})\b$', re.IGNORECASE)),
    ('tv_clues', re.compile(r'^\b(chapter[\s.]?\d+)\b$', re.IGNORECASE)),

    # Anime specific formats
    ('anime_clues', re.compile(r'^\b(ep?\.?\d{1,4})\b$', re.IGNORECASE)),
    # Match ranges like (001-500) or just the numbers
    ('anime_clues', re.compile(r'^\b(\(?\d{3,4}-\d{3,4}\)?)\b$', re.IGNORECASE)),

    # Movie Year (must be a 4-digit number between 1900-2099)
    ('movie_clues', re.compile(r'^\b(19\d{2}|20\d{2})\b$')),

    # Technical metadata
    ('resolution_clues', re.compile(r'^\b(\d{3,4}p)\b$', re.IGNORECASE)),
    ('extras_bits', re.compile(r'^\b(h\.?264|x264)\b$', re.IGNORECASE)),
    ('extras_bits', re.compile(r'^\b(x265|hevc)\b$', re.IGNORECASE)),
    ('audio_clues', re.compile(r'^\b(aac|ac3|dts|dd5\.1)\b$', re.IGNORECASE)),
    ('quality_clues', re.compile(r'^\b(bluray|bdrip|web-dl|hdtv|dvdrip|brrip|bdremux)\b$', re.IGNORECASE)),

    # Misc clues
    ('misc_clues', re.compile(r'^\b(complete|extended|remastered|integral|multi)\b$', re.IGNORECASE)),
]


def _preprocess(filename: str) -> List[str]:
    """Pre-processes the filename and splits it into tokens."""
    # Remove file extension
    name, _ = os.path.splitext(filename)
    # Normalize separators to spaces
    name = re.sub(r'[\s._\[\](){}-]+', ' ', name)
    # Remove common website prefixes aggressively
    name = re.sub(r'(?i)^\s*(www\s\w+\s\w+\s*|\[\s*\w+\s*\]|tamilblasters|1tamilmv)', '', name).strip()
    return name.split()


def _classify_token(token: str) -> Optional[Tuple[str, str]]:
    """Classifies a single token based on predefined regex patterns and known lists."""
    # First, check regex patterns for structured data (episodes, years, etc.)
    for category, pattern in TOKEN_PATTERNS:
        match = pattern.match(token)
        if match:
            # Normalize specific clues
            value = match.group(1).upper()
            if category == 'tv_clues' and 'X' in value:
                s, e = value.split('X')
                value = f"S{s.zfill(2)}E{e.zfill(2)}"
            return category, value

    # If no regex matches, check against simple keyword lists (release groups, etc.)
    for category, clues in KNOWN_CLUES.items():
        if token.lower() in clues:
            return category, token

    return None


def parse_filename(filename: str) -> dict:
    """
    Parses a media filename using a right-to-left token-based scan.
    """
    tokens = _preprocess(filename)

    title_parts = []
    clues = {
        'tv_clues': [], 'anime_clues': [], 'movie_clues': [],
        'resolution_clues': [], 'audio_clues': [], 'quality_clues': [],
        'release_groups': [], 'misc_clues': [], 'extras_bits': [],
        'extras_bits_unknown': []
    }

    # --- Right-to-Left Scan ---
    # The first token from the right that is NOT a clue marks the end of the title.
    title_boundary_found = False
    for token in reversed(tokens):
        if title_boundary_found:
            title_parts.insert(0, token)
            continue

        classification = _classify_token(token)

        if classification:
            category, value = classification
            if value not in clues[category]:
                clues[category].insert(0, value)  # Prepend to keep original order
        else:
            # This is the first non-clue token, so it must be part of the title.
            title_boundary_found = True
            title_parts.insert(0, token)

    # --- Post-processing ---
    clean_title = ' '.join(title_parts)
    # A simple rule: if no title was found, use the original filename without extension.
    if not clean_title and tokens:
        clean_title, _ = os.path.splitext(filename)
        # Attempt a basic cleanup of the fallback title
        clean_title = re.sub(r'[\._]', ' ', clean_title).strip()
        
    # Determine media type based on the clues found
    media_type = 'unknown'
    if clues['tv_clues']:
        media_type = 'tv'
    # Prioritize anime if anime clues or known anime release groups are present
    elif clues['anime_clues'] or any(rg.lower() in KNOWN_CLUES['release_groups'] for rg in clues['release_groups']):
        media_type = 'anime'
    elif clues['movie_clues']:
        media_type = 'movie'

    # Final result assembly
    result = {
        "original": filename,
        "clean_title": clean_title,
        "media_type": media_type,
    }
    result.update(clues)

    return result


# --- Test Cases ---
if __name__ == "__main__":
    test_cases = [
        "www.TamilBlasters.cam - Titanic (1997)[1080p BDRip].mkv",
        "doctor_who_2005.8x12.death_in_heaven.720p_hdtv_x264-fov.mkv",
        "Game of Thrones - S02E07 - A Man Without Honor [2160p].mkv",
        "【喵萌奶茶屋】★01月新番★[別對映像研出手！/Eizouken ni wa Te wo Dasu na！][01].mkv",
        "Голубая волна / Blue Crush (2002) DVDRip.mkv",
        "[Erai-raws] Kingdom 3rd Season - 02 [1080p].mkv",
        "Friends.1994.INTEGRALE.MULTI.1080p.WEB-DL.mkv",
        "One-piece-ep.1080-v2-1080p-raws.mkv",
        "S.W.A.T.2017.S08E01.720p.HDTV.x264-SYNCOPY.mkv"
    ]

    print("✅ Corrected Parser Test Results (Right-to-Left Token-Based Logic):\n")
    for filename in test_cases:
        parsed = parse_filename(filename)
        print(f"ORIG: {filename}")
        print(f"  CLEAN: {parsed['clean_title']} | TYPE: {parsed['media_type']}")
        clue_str = " | ".join(f"{k.replace('_clues', '')}:{v}" for k, v in parsed.items() if ('_clues' in k or 'extras' in k) and v)
        if clue_str:
            print(f"  CLUES: {clue_str}")
        print("-" * 20)