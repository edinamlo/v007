"""
Core parser module.

Provides parse_filename(name, quiet=False) -> dict
"""

import re
import unicodedata
from typing import List, Optional, Tuple, Dict, Any
from config import CLUES
from utils import clean_title

# Patterns (search inside tokens)
EPISODE_RE    = re.compile(r"(?i)(?<![A-Za-z0-9])(s\d{2}e\d{2,4})(?![A-Za-z0-9])")
TV_CLUE_RE    = re.compile(r"(?i)(?<![A-Za-z0-9])(s\d{2}(?:-s\d{2})?)(?![A-Za-z0-9])")
SEASON_RE     = re.compile(r"(?i)(?<![A-Za-z0-9])(season \d{1,2})(?![A-Za-z0-9])")
# supports both 1080p and 1080px
RESOLUTION_RE = re.compile(r"(?i)(?<!\d)(\d{3,4}(?:p|px))(?![A-Za-z0-9])")
H264_RE       = re.compile(r"(?i)(h\.?264)")
X265_RE       = re.compile(r"(?i)(x265)")
AAC_RE        = re.compile(r"(?i)(aac(?:2\.0|2|\.0)?)")
BLURAY_RE     = re.compile(r"(?i)(?:blu[- ]?ray|bluray|bdrip|bdremux|bdr)")
EP_RANGE_RE   = re.compile(r"(?i)\((\d{3,4}-\d{3,4})\)")
ANIME_EP_RE   = re.compile(r"(?i)(?<![A-Za-z0-9])(ep?\.?\d{1,4})(?![A-Za-z0-9])")
YEAR_RE       = re.compile(r"(?i)(?<![A-Za-z0-9])(\d{4})(?![A-Za-z0-9])")
CHAPTER_RE    = re.compile(r"(?i)(?<![A-Za-z0-9])(chapter[\s._-]?\d+)(?![A-Za-z0-9])")

_RIGHT_SEP_TRIM = re.compile(r"[.\-\s_\(\)\[\]]+$")


def _trim_right_separators(s: str) -> str:
    return _RIGHT_SEP_TRIM.sub("", s)


def _collect_matches(token: str) -> List[Tuple[int, int, str, str]]:
    """
    Collect regex matches for known patterns inside a token.

    Returns:
        List of (start, end, clue_type, text).
    """
    matches: List[Tuple[int, int, str, str]] = []

    PATTERNS = [
        (EPISODE_RE, "episode"),
        (TV_CLUE_RE, "tvclue"),
        (SEASON_RE, "tvseason"),
        (RESOLUTION_RE, "resolution"),
        (H264_RE, "h264"),
        (X265_RE, "x265"),
        (AAC_RE, "aac"),
        (BLURAY_RE, "bluray"),
        (EP_RANGE_RE, "animerange"),
        (ANIME_EP_RE, "animeep"),
        (YEAR_RE, "movieyear"),
        (CHAPTER_RE, "chapter"),
    ]

    for regex, clue_type in PATTERNS:
        for m in regex.finditer(token):
            # Use group(1) if available, otherwise group(0)
            text = m.group(1) if m.lastindex else m.group(0)

            if clue_type == "movieyear":
                try:
                    year = int(text)
                    if not (1900 <= year <= 2100):
                        continue
                except ValueError:
                    continue

            matches.append((m.start(), m.end(), clue_type, text))

    matches.sort(key=lambda x: x[0])
    return matches


def _token_in_clues(token: str, clue_lists: Dict[str, List[str]]) -> Optional[str]:
    """
    Check if token (case-insensitive) is in any clue list.
    Returns the category name if found (e.g., 'quality_clues') else None.
    """
    up = token.upper()
    for cat, lst in clue_lists.items():
        # compare case-insensitively and allow small separators
        for v in lst:
            if up == v.upper():
                return cat
    return None


def write_concise_log(result: dict, expected: str, log_dir: str = None) -> None:
    """Write concise parsing results to txt file."""
    from pathlib import Path
    from datetime import datetime
    
    if log_dir is None:
        log_dir = Path(__file__).parent / "logs"
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"parse_results_{timestamp}.txt"
    
    # Get non-empty clues
    clues = []
    if result.get("tv_clues"):
        clues.append(f"TV: {', '.join(result['tv_clues'])}")
    if result.get("anime_clues"):
        clues.append(f"ANIME: {', '.join(result['anime_clues'])}")
    if result.get("movie_clues"):
        clues.append(f"MOVIE: {', '.join(result['movie_clues'])}")
    
    # Format output line
    line = (
        f"Original: {result['original']}\n"
        f"Expected: {expected}\n"
        f"Possible: {result['possible_title']}\n"
        f"Clean: {result['clean_title']}\n"
        f"Type: {result['media_type']}\n"
        f"Clues: {' | '.join(clues) if clues else 'None'}\n"
        f"{'-'*80}\n"
    )
    
    # Append to log file
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(line)

# Modify parse_filename to accept expected title parameter
def parse_filename(filename: str, quiet: bool = False, expected: str = None) -> dict:
    """Parse filename and optionally log concise results."""
    result = parse_filename_internal(filename, quiet)
    
    if expected is not None:
        write_concise_log(result, expected)
    
    return result

# Rename existing parse_filename function
def parse_filename_internal(filename: str, quiet: bool = False) -> dict:
    """
    Parse a filename to extract media information.
    
    Only splits possible_title at the first media type clue found
    (tv_clues, anime_clues, or movie_clues). If no media type clues
    are found, uses the original filename as possible_title.
    """
    m = re.match(r"^(?P<name>.+?)(?P<ext>\.[^.]+)$", filename)
    if m:
        name, ext = m.group("name"), m.group("ext")
    else:
        name, ext = filename, ""

    # If extension itself includes clues, merge into name (rare)
    if ext:
        ext_matches = _collect_matches(ext)
        if ext_matches:
            name += ext
            ext = ""

    tokens = name.split()  # only whitespace split; keep punctuation inside tokens

    extras_bits: List[str] = []
    words: List[str] = []
    tv_clues: List[str] = []
    anime_clues: List[str] = []
    movie_clues: List[str] = []
    possible_title: Optional[str] = None
    title_boundary_index = len(tokens)
    movie_found = False

    if not quiet:
        print("Parsing")
        print(filename)
    if ext:
        if not quiet:
            print(f"Found {ext} -> word")
        words.append(ext)

    i = len(tokens) - 1
    while i >= 0:
        raw_tok = tokens[i]
        matches = _collect_matches(raw_tok)

        # If movie already found, ignore further movieyear matches
        if movie_found and matches:
            matches = [mm for mm in matches if mm[2] != "movieyear"]

        if not matches:
            if i >= title_boundary_index:
                # Check if this token is known clue by lookup from CLUES
                cat = _token_in_clues(raw_tok, CLUES)
                if cat:
                    # add to extras_bits with normalized mapping
                    if cat == "resolution_clues":
                        extras_bits.append(raw_tok)
                    elif cat in ("quality_clues", "misc_clues"):
                        extras_bits.append(raw_tok)
                    elif cat in ("audio_clues",):
                        extras_bits.append(raw_tok.upper())
                    elif cat in ("release_groups", "release_groups_anime"):
                        words.append(raw_tok)
                    else:
                        words.append(raw_tok)
                    if not quiet:
                        print(f"Found {raw_tok} -> {cat}")
                else:
                    if not quiet:
                        print(f"Found {raw_tok} -> word")
                    words.append(raw_tok)
            i -= 1
            continue

        # There are matches inside this raw token
        left_start = matches[0][0]
        left_sub = raw_tok[:left_start]
        left_sub_clean = _trim_right_separators(left_sub)
        if left_sub_clean:
            left_tokens = tokens[:i]
            candidate = " ".join(left_tokens) + " " + left_sub_clean if left_tokens else left_sub_clean
            possible_title = candidate.strip()
            if not quiet:
                print(f"Found {possible_title} -> possible_title")

        title_boundary_index = min(title_boundary_index, i)

        for start, end, typ, text in matches:
            typ = typ.lower()
            if typ == "episode":
                tv_clues.append(text.upper())
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> tv_clue (episode)")
            elif typ == "tvclue":
                pieces = [p.upper() for p in text.split("-")]
                tv_clues.extend(pieces)
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> tv_clue")
            elif typ == "tvseason":
                tv_clues.append(text.upper())
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> tv_clue (season)")
            elif typ == "animerange":
                anime_clues.append(text.upper())
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> anime_clue (range)")
            elif typ == "animeep":
                anime_clues.append(text.upper())
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> anime_clue (ep)")
            elif typ == "movieyear":
                if not movie_found:
                    movie_clues.append(text)
                    movie_found = True
                    title_boundary_index = min(title_boundary_index, i)
                    if not left_sub_clean:
                        # fallback: take substring up to first codec/resolution/bluray found in name
                        codec_m = re.search(r"(?i)(h\.?264|x265|aac|1080p|2160p|1080px|bluray)", name)
                        if codec_m:
                            fallback = name[:codec_m.start(1)]
                        else:
                            fallback = name
                        fallback = _trim_right_separators(fallback)
                        if fallback:
                            possible_title = fallback.strip()
                            if not quiet:
                                print(f"Found {possible_title} -> possible_title (fallback due to movie year)")
                    if not quiet:
                        print(f"Found {text} (in '{raw_tok}') -> movie_clue (year)")
                else:
                    if not quiet:
                        print(f"Skipping extra movie year {text}")
            elif typ == "resolution":
                norm = text.lower()
                if norm not in extras_bits:
                    extras_bits.append(norm)
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> resolution")
            elif typ == "h264":
                if "h.264" not in extras_bits:
                    extras_bits.append("h.264")
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> codec (h.264)")
            elif typ == "x265":
                if "x265" not in extras_bits:
                    extras_bits.append("x265")
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> extras_bits")
            elif typ == "aac":
                if "AAC" not in extras_bits:
                    extras_bits.append("AAC")
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> extras_bits")
            elif typ == "bluray":
                if "BluRay" not in extras_bits:
                    extras_bits.append("BluRay")
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> extras_bits (BluRay)")
            elif typ == "chapter":
                tv_clues.append(text.upper())
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> tv_clue (chapter)")

        # Add unrecognized substrings between/after matches to words
        prev_end = matches[0][0]
        for j in range(len(matches)):
            start, end, typ, text = matches[j]
            if start > prev_end:
                between = raw_tok[prev_end:start]
                if between.strip():
                    if not quiet:
                        print(f"Found {between} (in '{raw_tok}') -> word")
                    words.append(between)
            prev_end = end
        if prev_end < len(raw_tok):
            after = raw_tok[prev_end:]
            if after.strip():
                if not quiet:
                    print(f"Found {after} (in '{raw_tok}') -> word")
                words.append(after)

        i -= 1

    final_title = possible_title or " ".join(tokens[:title_boundary_index]).strip() or None

    # Iterative stripping of clues at end of final_title (if any)
    clue_patterns = [EPISODE_RE, TV_CLUE_RE, SEASON_RE, EP_RANGE_RE, ANIME_EP_RE, YEAR_RE]
    while final_title:
        found_any = False
        rightmost_end = -1
        rightmost_m = None
        rightmost_typ = None
        rightmost_txt = None
        for pat in clue_patterns:
            for m in pat.finditer(final_title):
                if m.end(1) > rightmost_end:
                    rightmost_end = m.end(1)
                    rightmost_m = m
                    rightmost_typ = pat
                    rightmost_txt = m.group(1)
        if rightmost_m and rightmost_end == len(final_title):
            # strip it and add to proper list
            if rightmost_typ == EPISODE_RE:
                tv_clues.append(rightmost_txt.upper())
            elif rightmost_typ == TV_CLUE_RE:
                tv_clues.extend([p.upper() for p in rightmost_txt.split("-")])
            elif rightmost_typ == SEASON_RE:
                tv_clues.append(rightmost_txt.upper())
            elif rightmost_typ == EP_RANGE_RE:
                anime_clues.append(rightmost_txt.upper())
            elif rightmost_typ == ANIME_EP_RE:
                anime_clues.append(rightmost_txt.upper())
            elif rightmost_typ == YEAR_RE:
                movie_clues.append(rightmost_txt)
            final_title = _trim_right_separators(final_title[:rightmost_m.start(1)])
            found_any = True
        if not found_any:
            break

    # Decide media type
    if tv_clues:
        media_type = "tv"
    elif anime_clues:
        media_type = "anime"
    elif movie_clues:
        media_type = "movie"
    else:
        media_type = "unknown"

    cleaned = clean_title(final_title) if final_title else None

    # dedupe movie_clues (preserve order) and filter out pure-separator words
    from collections import OrderedDict
    movie_clues = list(OrderedDict.fromkeys(movie_clues))
    # keep only words that contain at least one alphanumeric character
    import re as _re
    words = [w for w in words if _re.search(r"\w", w)]

    # after computing extras_bits, words, tv_clues, anime_clues, movie_clues etc.
    # build matched clue lists from CLUES (config.CLUES)
    matched_clues: Dict[str, List[str]] = {}
    # categories present in config.CLUES (adjust names to your CLUES file keys)
    clue_keys = [
        "resolution_clues",
        "audio_clues",
        "quality_clues",
        "release_groups",
        "release_groups_anime",
        "misc_clues"
    ]
    search_space = [filename] + extras_bits + words + ([final_title] if final_title else [])
    for key in clue_keys:
        candidates = CLUES.get(key, []) if isinstance(CLUES, dict) else []
        found = []
        for c in candidates:
            # case-insensitive substring match against tokens
            low = c.lower()
            for token in search_space:
                if token and low in token.lower():
                    found.append(c)
                    break
        if found:
            # preserve order and dedupe
            seen = []
            for f in found:
                if f not in seen:
                    seen.append(f)
            matched_clues[key] = seen

    # include individual convenience fields (if present) plus full matched_clues map
    result: Dict[str, Any] = {
        "original": filename,
        "tv_clues": tv_clues,
        "anime_clues": anime_clues,
        "movie_clues": movie_clues,
        "possible_title": final_title,
        "clean_title": cleaned,
        "extras_bits": extras_bits,
        "words": words,
        "media_type": media_type,
        "matched_clues": matched_clues,
        # also expose top-level aliases for common categories for easier consumption
        "resolution_clues": matched_clues.get("resolution_clues", []),
        "audio_clues": matched_clues.get("audio_clues", []),
        "quality_clues": matched_clues.get("quality_clues", []),
        "release_groups": matched_clues.get("release_groups", []),
        "misc_clues": matched_clues.get("misc_clues", [])
    }

    if not quiet:
        print("\nSummary:")
        print("TV clues:", ", ".join(tv_clues) if tv_clues else "None")
        print("Anime clues:", ", ".join(anime_clues) if anime_clues else "None")
        print("Movie clues:", ", ".join(movie_clues) if movie_clues else "None")
        print("Possible title:", final_title if final_title else "None")
        print("Clean title:", cleaned if cleaned else "None")
        print("Extras bits:", ", ".join(extras_bits) if extras_bits else "None")
        print("Words:", ", ".join(words) if words else "None")

    return result


def extract_title(filename: str) -> str:
    """
    Extract clean title from filename, handling:
    - Website prefixes (www.*, [www.*], etc)
    - Year in parentheses
    - Multiple languages (cyrillic, chinese, etc)
    - Release group tags
    - Quality/codec info
    """
    # Remove common website prefixes
    title = re.sub(r'^(?:www\.[^-\s]+\s*-\s*)', '', filename)
    title = re.sub(r'^\[[^]]+\](?:_|-|\s)*', '', title)
    
    # Extract title before year or metadata tags
    match = re.search(r'^(.+?)(?:\s*[\(\[]\d{4}|\s+(?:720p|1080p|2160p|HDTV|BDRip))', title)
    if match:
        title = match.group(1)
        
    # Handle multiple language titles (e.g. "Russian / English")
    if '/' in title:
        # Take the last title (usually English/romanized)
        title = title.split('/')[-1].strip()
        
    # Clean up remaining separators
    title = re.sub(r'[._-]+', ' ', title).strip()
    
    return title


def normalize_text(text: str) -> str:
    """
    Normalize Unicode text:
    - Convert full-width characters to normal
    - Handle combining diacritical marks
    - Normalize special quotes/spaces
    """
    # Normalize Unicode combining characters
    text = unicodedata.normalize('NFKC', text)
    
    # Convert full-width characters to normal width
    text = ''.join([
        c if unicodedata.east_asian_width(c) != 'F' 
        else unicodedata.normalize('NFKC', c)
        for c in text
    ])
    
    return text.strip()


def clean_title(possible_title: str) -> Optional[str]:
    """
    Clean up possible_title for nicer display.
    
    Handles:
    - Acronyms (S.H.I.E.L.D, 9-1-1)
    - Multiple languages
    - Unicode normalization
    - Website prefixes
    - Common separators
    """
    if not possible_title:
        return None

    # Normalize Unicode and clean up
    title = normalize_text(possible_title)
    
    # Keep acronyms or numbered titles as-is
    if re.fullmatch(r'([A-Z]\.)+[A-Z]?|\d+(-\d+)+', title):
        return title
        
    # Remove website prefixes
    title = re.sub(r'^(?:www\.[^-\s]+\s*-\s*|\[[^]]+\](?:_|-|\s)*)', '', title)
    
    # Split on separators and clean each part
    parts = re.split(r'[.\-_]+', title)
    parts = [p.strip() for p in parts if p.strip()]
    
    # Handle multiple languages - take last part (usually English)
    if '/' in ' '.join(parts):
        parts = ' '.join(parts).split('/')[-1].strip().split()
    
    return ' '.join(parts).strip()


def extract_possible_title(filename, tv_clues, anime_clues, movie_clues):
    # If any media clue found, split at first occurrence
    for clue in tv_clues + anime_clues + movie_clues:
        idx = filename.lower().find(clue.lower())
        if idx > 0:
            return filename[:idx].strip(" ._-")
    # If no media clue, return original
    return filename
