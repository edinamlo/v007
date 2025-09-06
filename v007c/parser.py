"""
parser.py

Core filename/folder parser for media items.
Supports detection of TV, anime, and movie clues,
plus extras (resolution, codecs, etc.).

This version uses a single, efficient, combined regex for matching and is
designed to accept pre-loaded clue "overrides" to correctly categorize
tokens that would otherwise be considered unknown.
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Dict

# --- Consolidated Regex Patterns ---
REGEX_DEFINITIONS = {
    'episode': r'(?P<episode>s\d{2}e\d{2,4})',
    'episode_alt': r'(?P<episode_alt>\d{1,2}x\d{1,3})',
    'tvclue': r'(?P<tvclue>s\d{2}(?:-s\d{2})?)',
    'tvseason': r'(?P<tvseason>season \d{1,2})',
    'chapter': r'(?P<chapter>chapter[\s._-]?\d+)',
    'animerange': r'(?P<animerange>\(\d{3,4}-\d{3,4}\))',
    'animeep': r'(?P<animeep>ep?\.?\d{1,4})',
    'movieyear': r'(?P<movieyear>(?:19[89]\d|20\d{2}))', # Year range 1980-2099
    'resolution': r'(?P<resolution>\d{3,4}p)',
    'bluray': r'(?P<bluray>blu[- ]?ray|bluray|bdrip|bdremux|bdr)',
    'h264': r'(?P<h264>h\.?264)',
    'x265': r'(?P<x265>x265)',
    'aac': r'(?P<aac>aac(?:2\.0|2|\.0)?)',
}

COMBINED_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9])(" + "|".join(REGEX_DEFINITIONS.values()) + r")(?![A-Za-z0-9])"
)

# --- Prefix and Separator Patterns ---
_PREFIX_RE = re.compile(r'^(?:\[[^]]+\]\s*|www\.[^.]+\.[^ ]+\s*-\s*)', re.IGNORECASE)
_TOKENIZE_RE = re.compile(r'[\s._-]+') # Split on space, dot, underscore, or hyphen

def clean_title(title: str) -> Optional[str]:
    """
    Cleans a raw title by replacing separators with spaces.
    Preserves existing capitalization (e.g., S.W.A.T., The Mandalorian).
    """
    if not title:
        return None
    # Just replace common separators with a single space and trim.
    return ' '.join(title.split('.')).replace('_', ' ').strip()


def _collect_matches(token: str) -> List[Dict]:
    """Return list of match dictionaries for a given token."""
    matches = []
    for m in COMBINED_RE.finditer(token):
        if m.lastgroup:
            matches.append({
                "start": m.start(1),
                "end": m.end(1),
                "type": m.lastgroup,
                "text": m.group(1)
            })
    matches.sort(key=lambda x: x['start'])
    return matches

def load_known_clues(data_path: str = "./data/known_clues.json") -> Dict:
    """Load known clue overrides from a JSON file."""
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Make lookup case-insensitive for robustness
            return {k.lower(): v for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

KNOWN_CLUES = load_known_clues()

def parse_filename(filename: str, quiet: bool = False, overrides: Optional[Dict] = None) -> Dict:
    """
    Parse a filename or folder name into structured metadata.
    """
    overrides = overrides if overrides is not None else KNOWN_CLUES

    # 1. --- PREPARATION ---
    # Strip extension and common prefixes
    name_no_ext = Path(filename).stem
    clean_name = _PREFIX_RE.sub("", name_no_ext)
    tokens = [t for t in _TOKENIZE_RE.split(clean_name) if t]

    # 2. --- INITIAL MEDIA TYPE DETECTION ---
    is_tv = False
    for tok in tokens:
        if any(m['type'] in ('episode', 'episode_alt', 'tvclue', 'tvseason', 'chapter') for m in _collect_matches(tok)):
            is_tv = True
            break

    # 3. --- TOKEN CLASSIFICATION (RIGHT-TO-LEFT) ---
    tv_clues, anime_clues, movie_clues, extras, words = [], [], [], [], []
    title_boundary_index = len(tokens)
    movie_found = False

    for i in range(len(tokens) - 1, -1, -1):
        tok = tokens[i]
        tok_lower = tok.lower()
        matches = _collect_matches(tok)
        
        # Use the overrides dictionary to classify known tokens
        if tok_lower in overrides:
            clue_type = overrides[tok_lower]
            if clue_type == "quality" or clue_type == "audio":
                extras.append(tok)
            # Words like "COMPLETE" can be ignored or added to a specific list
            title_boundary_index = min(title_boundary_index, i)
            continue # Move to the next token

        # Skip movie year matches if we already know it's a TV show
        if is_tv and matches:
            matches = [m for m in matches if m['type'] != 'movieyear']
        
        if not matches:
            if i >= title_boundary_index:
                words.append(tok)
            continue
        
        title_boundary_index = min(title_boundary_index, i)

        # Simplified loop for processing matches
        for match in matches:
            typ, text = match['type'], match['text']
            
            if typ in ('episode', 'episode_alt', 'tvclue', 'tvseason', 'chapter'):
                tv_clues.extend([p.upper() for p in text.split("-")])
            elif typ in ('animerange', 'animeep'):
                anime_clues.append(text.upper())
            elif typ == 'movieyear' and not is_tv and not movie_found:
                movie_clues.append(text)
                movie_found = True
            else: # All other technical clues go into extras
                extras.append(text)

    # 4. --- FINALIZATION ---
    # Title is now determined cleanly *after* the loop
    title_tokens = tokens[:title_boundary_index]
    final_title = ".".join(title_tokens) if title_tokens else None
    
    media_type = "unknown"
    if is_tv or tv_clues:
        media_type = "tv"
    elif anime_clues:
        media_type = "anime"
    elif movie_found:
        media_type = "movie"
        
    result = {
        "original": filename,
        "media_type": media_type,
        "title": final_title,
        "clean_title": clean_title(final_title),
        "tv_clues": sorted(list(set(tv_clues))),
        "anime_clues": sorted(list(set(anime_clues))),
        "movie_clues": sorted(list(set(movie_clues))),
        "extras": sorted(list(set(extras))),
        "unmatched_words": words
    }
    
    if not quiet:
        print(json.dumps(result, indent=2))
        
    return result