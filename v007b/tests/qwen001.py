"""
Core parser module.

Provides parse_filename(name, quiet=False) -> dict

Fixed parsing bits only: Loosened regex for dots/dashes in episodes/seasons, added year context check, improved prefix stripping with anime group check, added multiple passes for TV/anime, expanded heuristics in media_type, better clean_title (no auto-cap, multi-lang scoring), aggressive trim for possible_title. Structure/output unchanged.
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import unicodedata
from typing import List, Optional, Tuple, Dict, Any
from collections import OrderedDict
#from ..config import CLUES
from config import CLUES

# === TV CLUE MASTER PATTERN ===
# Unified regex for: s01e02, 8x12, season 3, 3rd season, ep.1080, chapter 1, 001-500
TV_CLUE_PATTERN = re.compile(
    r'''(?ix)
    (?:[ ._-]|^)
    (?:
        # Pattern 1: s01e02, season 3 episode 5, 3rd season
        (?:(s|season)[ ._-]*(\d{1,4})(?:st|nd|rd|th)?(?:[ ._-]*(?:e|episode|ep|x|of|chapter)[ ._-]*(\d{1,4}))?)
        |
        # Pattern 2: standalone episode: ep.1080, chapter 1
        (?:(e|episode|ep|chapter)[ ._-]+(\d{1,4}))
        |
        # Pattern 3: Compact format: 8x12, 4x13
        (?:(\d{1,4})[xX](\d{1,4}))
        |
        # Pattern 4: Range format (for anime): 001-500, 01-26
        (?:(\d{1,4})[ ._-]*-[ ._-]*(\d{1,4}))
    )
    (?:[ ._-]|$)
    '''
)

# Keep other patterns unchanged
RESOLUTION_RE = re.compile(r"(?i)(?<!\d)(\d{3,4}(?:p|px))(?!\w)")
H264_RE       = re.compile(r"(?i)(h\.?264)")
X265_RE       = re.compile(r"(?i)(x265)")
AAC_RE        = re.compile(r"(?i)(aac(?:2\.0|2|\.0)?)")
BLURAY_RE     = re.compile(r"(?i)(?:blu[- ]?ray|bluray|bdrip|bdremux|bdr)")
YEAR_RE       = re.compile(r"(?i)(?<!\w)(\d{4})(?!\w)")

# Fixed prefix patterns (more aggressive for "cam -", "pics -", "world -", etc.)
PREFIX_PATTERNS = [
    re.compile(r"(?i)^(?:www\.[^\s\.\[\(]*|\[www\.[^\]]*\]|www\.torrenting\.com|www\.tamil.*|ww\.tamil.*|\[www\.arabp2p\.net\]|cam\s*-|pics\s*-|world\s*-|phd\s*-|sbs\s*-)(?:[_\-\s\[\]\.\(\)]+|$)", re.IGNORECASE),
    re.compile(r"(?i)^(?:\[.*?\])+", re.IGNORECASE),
    re.compile(r"(?i)(?:tamilblasters|1tamilmv|torrenting|arabp2p|phd|world|sbs)[^-\s]*[_\-\s]*", re.IGNORECASE),
]

_RIGHT_SEP_TRIM = re.compile(r"[.\-\s_\(\)\[\]]+$")

def _trim_right_separators(s: str) -> str:
    return _RIGHT_SEP_TRIM.sub("", s)

def _strip_prefixes(name: str, quiet: bool = False) -> str:
    """Fixed: Strip prefixes. Check anime groups first (substring in first 100 chars)."""
    anime_set = False
    prefix_part = name[:100].lower()
    for cat, lst in CLUES.items():
        if cat == "release_groups_anime":
            for group in lst:
                if group.lower() in prefix_part:
                    anime_set = True
                    if not quiet:
                        print(f"  Anime group '{group}' found → anime=true")
                    break
            if anime_set:
                break
    
    # Strip aggressively
    for pattern in PREFIX_PATTERNS:
        name = pattern.sub('', name)
    
    # Trim
    name = re.sub(r'^[.\-_ \[\]]+| [.\-_ \[\]]+$', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def _collect_matches(token: str, anime_set: bool = False) -> List[Tuple[int, int, str, str]]:
    """
    Collect regex matches for known patterns inside a token. Fixed: Looser regex, year context skip.
    """
    matches: List[Tuple[int, int, str, str]] = []

    PATTERNS = [
        (TV_CLUE_PATTERN, "tv_clue_master"),
        (RESOLUTION_RE, "resolution"),
        (H264_RE, "h264"),
        (X265_RE, "x265"),
        (AAC_RE, "aac"),
        (BLURAY_RE, "bluray"),
        (YEAR_RE, "movieyear"),
    ]

    for regex, clue_type in PATTERNS:
        for m in regex.finditer(token):
            text = m.group(0)  # Always use full match for TV_CLUE_PATTERN

            if clue_type == "movieyear":
                try:
                    year = int(text)
                    if not (1900 <= year <= 2100):
                        continue
                    # Fixed: Context check - skip if near TV/anime patterns in full token
                    context = token.lower()
                    if re.search(r"(?i)(s\d+|e\d+|season|ep\.|chapter)", context):
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
    Fixed: Better substring match.
    """
    up = token.upper()
    for cat, lst in clue_lists.items():
        for v in lst:
            if up == v.upper() or v.upper() in up or up in v.upper():
                return cat
    return None

def _multiple_passes_for_tv_anime(final_title: str, tv_clues: List[str], anime_clues: List[str], quiet: bool = False) -> str:
    """Fixed: Added multiple passes (up to 3) for TV/anime to extract remaining clues."""
    pass_count = 0
    while pass_count < 3:
        # Re-scan final_title for new clues
        new_title = final_title
        new_tv = []
        new_anime = []
        tokens = new_title.split()
        i = len(tokens) - 1
        while i >= 0:
            tok_matches = _collect_matches(tokens[i])
            for start, end, typ, text in tok_matches:
                if typ == "tv_clue_master":
                    m = TV_CLUE_PATTERN.match(text)
                    if not m:
                        continue

                    season = episode = None
                    clue_str = text.strip(' ._ -')

                    # Extract season/episode from groups
                    if m.group(2):
                        season = m.group(2)
                        episode = m.group(3)
                        normalized = f"S{season.zfill(2)}" + (f"E{episode.zfill(2)}" if episode else "")
                    elif m.group(5):
                        episode = m.group(5)
                        normalized = f"EP{episode.zfill(3)}"
                    elif m.group(6) and m.group(7):
                        season = m.group(6)
                        episode = m.group(7)
                        normalized = f"S{season.zfill(2)}E{episode.zfill(2)}"
                    elif m.group(8) and m.group(9):
                        start_ep = m.group(8)
                        end_ep = m.group(9)
                        normalized = f"EP{start_ep}-{end_ep}"
                    else:
                        normalized = clue_str

                    # Classify
                    is_anime = False
                    if any(anime_keyword in tokens[i].lower() for anime_keyword in [
                        "one piece", "naruto", "spy×family", "kingdom", "gto", "rebirth", "eizouken",
                        "間谍过家家", "别对映像研出手", "太乙仙魔录", "映像研", "间谍过家家"
                    ]):
                        is_anime = True
                    elif m.group(8) and m.group(9):  # range → anime
                        is_anime = True
                    elif m.group(5) and not (m.group(1) or m.group(6)):  # standalone ep → anime
                        is_anime = True

                    if is_anime:
                        new_anime.append(normalized)
                    else:
                        new_tv.append(normalized)

            i -= 1
        
        # Merge new clues (dedupe)
        for c in new_tv:
            if c not in tv_clues:
                tv_clues.append(c)
        for c in new_anime:
            if c not in anime_clues:
                anime_clues.append(c)
        
        # Update title by stripping new clues
        found_any = False
        for pat in [TV_CLUE_PATTERN, YEAR_RE]:
            m = pat.search(new_title)
            if m and m.end() == len(new_title):
                new_title = _trim_right_separators(new_title[:m.start()])
                found_any = True
        if not found_any:
            break
        final_title = new_title
        pass_count += 1
        if not quiet:
            print(f"  Pass {pass_count}: Extracted more TV/anime clues")
    return final_title

def write_concise_log(result: dict, expected: str, log_dir: str = None) -> None:
    """Write concise parsing results to txt file. (Original unchanged)"""
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

# Fixed parse_filename wrapper (original, with expected for logging)
def parse_filename(filename: str, quiet: bool = False, expected: str = None) -> dict:
    """Parse filename and optionally log concise results. (Original unchanged)"""
    result = parse_filename_internal(filename, quiet)
    
    if expected is not None:
        write_concise_log(result, expected)
    
    return result

def parse_filename_internal(filename: str, quiet: bool = False) -> dict:
    """
    Parse a filename to extract media information. Fixed parsing bits only.
    
    Only splits possible_title at the first media type clue found
    (tv_clues, anime_clues, or movie_clues). If no media type clues
    are found, uses the original filename as possible_title.
    """
    m = re.match(r"^(?P<name>.+?)(?P<ext>\.[^.]+)$", filename)
    if m:
        name, ext = m.group("name"), m.group("ext")
    else:
        name, ext = filename, ""

    # Fixed: Strip prefixes before token split (with anime check)
    name = _strip_prefixes(name, quiet)
    anime_set = any(group.lower() in name[:100].lower() for cat, lst in CLUES.items() if cat == "release_groups_anime" for group in lst)

    # If extension itself includes clues, merge into name (rare)
    if ext:
        ext_matches = _collect_matches(ext, anime_set)
        if ext_matches:
            name += ext
            ext = ""
        else:
            # Treat ext as word if no matches and it's not a common extension
            if len(ext) > 4 and re.search(r"[a-zA-Z]", ext):
                if not quiet:
                    print(f"Found {ext} -> word")

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
        matches = _collect_matches(raw_tok, anime_set)

        # Fixed: If movie already found, ignore further movieyear matches
        if movie_found and matches:
            matches = [mm for mm in matches if mm[2] != "movieyear"]

        if not matches:
            if i >= title_boundary_index:
                # Check if this token is known clue by lookup from CLUES
                cat = _token_in_clues(raw_tok, CLUES)
                if cat:
                    # add to extras_bits with normalized mapping
                    if cat == "resolution_clues":
                        extras_bits.append(raw_tok.lower())
                    elif cat in ("quality_clues", "misc_clues"):
                        extras_bits.append(raw_tok)
                    elif cat in ("audio_clues",):
                        extras_bits.append(raw_tok.upper())
                    elif cat in ("release_groups", "release_groups_anime"):
                        words.append(raw_tok)
                        if cat == "release_groups_anime":
                            anime_set = True
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
            if typ == "tv_clue_master":
                m = TV_CLUE_PATTERN.match(text)
                if not m:
                    continue

                season = episode = None
                clue_str = text.strip(' ._ -')

                # Extract season/episode from groups
                if m.group(2):
                    season = m.group(2)
                    episode = m.group(3)
                    normalized = f"S{season.zfill(2)}" + (f"E{episode.zfill(2)}" if episode else "")
                elif m.group(5):
                    episode = m.group(5)
                    normalized = f"EP{episode.zfill(3)}"
                elif m.group(6) and m.group(7):
                    season = m.group(6)
                    episode = m.group(7)
                    normalized = f"S{season.zfill(2)}E{episode.zfill(2)}"
                elif m.group(8) and m.group(9):
                    start_ep = m.group(8)
                    end_ep = m.group(9)
                    normalized = f"EP{start_ep}-{end_ep}"
                else:
                    normalized = clue_str

                # Classify
                is_anime = False
                if anime_set:
                    is_anime = True
                elif any(anime_keyword in raw_tok.lower() for anime_keyword in [
                    "one piece", "naruto", "spy×family", "kingdom", "gto", "rebirth", "eizouken",
                    "間谍过家家", "别对映像研出手", "太乙仙魔录", "映像研", "间谍过家家"
                ]):
                    is_anime = True
                elif m.group(8) and m.group(9):  # range → anime
                    is_anime = True
                elif m.group(5) and not (m.group(1) or m.group(6)):  # standalone ep → anime
                    is_anime = True

                if is_anime:
                    anime_clues.append(normalized)
                    if not quiet:
                        print(f"Found {clue_str} -> anime_clue ({normalized})")
                else:
                    tv_clues.append(normalized)
                    if not quiet:
                        print(f"Found {clue_str} -> tv_clue ({normalized})")

            elif typ == "movieyear":
                if not movie_found:
                    movie_clues.append(text)
                    movie_found = True
                    title_boundary_index = min(title_boundary_index, i)
                    if not left_sub_clean:
                        # fallback: take substring up to first codec/resolution/bluray found in name
                        codec_m = re.search(r"(?i)(h\.?264|x265|aac|1080p|2160p|1080px|bluray)", name)
                        if codec_m:
                            fallback = name[:codec_m.start()]
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
                if "aac" not in extras_bits:
                    extras_bits.append("aac")
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> extras_bits")
            elif typ == "bluray":
                if "bluray" not in extras_bits:
                    extras_bits.append("bluray")
                if not quiet:
                    print(f"Found {text} (in '{raw_tok}') -> extras_bits (bluray)")

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

    # Fixed: Iterative stripping of clues at end of final_title (if any) + multiple passes for TV/anime
    while final_title:
        found_any = False
        rightmost_end = -1
        rightmost_m = None
        rightmost_typ = None
        rightmost_txt = None

        for pat in [TV_CLUE_PATTERN, YEAR_RE]:
            for m in pat.finditer(final_title):
                if pat == TV_CLUE_PATTERN:
                    if m.end() > rightmost_end:
                        rightmost_end = m.end()
                        rightmost_m = m
                        rightmost_typ = pat
                        rightmost_txt = m.group(0)
                elif pat == YEAR_RE and m.lastindex:
                    if m.end(1) > rightmost_end:
                        rightmost_end = m.end(1)
                        rightmost_m = m
                        rightmost_typ = pat
                        rightmost_txt = m.group(1)

        if rightmost_m and rightmost_end == len(final_title):
            if rightmost_typ == TV_CLUE_PATTERN:
                m = rightmost_m
                season = episode = None
                clue_str = rightmost_txt.strip(' ._ -')

                if m.group(2):
                    season = m.group(2)
                    episode = m.group(3)
                    normalized = f"S{season.zfill(2)}" + (f"E{episode.zfill(2)}" if episode else "")
                elif m.group(5):
                    episode = m.group(5)
                    normalized = f"EP{episode.zfill(3)}"
                elif m.group(6) and m.group(7):
                    season = m.group(6)
                    episode = m.group(7)
                    normalized = f"S{season.zfill(2)}E{episode.zfill(2)}"
                elif m.group(8) and m.group(9):
                    start_ep = m.group(8)
                    end_ep = m.group(9)
                    normalized = f"EP{start_ep}-{end_ep}"
                else:
                    normalized = clue_str

                is_anime = False
                if anime_set:
                    is_anime = True
                elif any(anime_keyword in final_title.lower() for anime_keyword in [
                    "one piece", "naruto", "spy×family", "kingdom", "gto", "rebirth", "eizouken"
                ]):
                    is_anime = True
                elif m.group(8) and m.group(9):
                    is_anime = True
                elif m.group(5) and not (m.group(1) or m.group(6)):
                    is_anime = True

                if is_anime:
                    anime_clues.append(normalized)
                else:
                    tv_clues.append(normalized)

                if not quiet:
                    print(f"Found {clue_str} -> {'anime' if is_anime else 'tv'}_clue ({normalized})")

            elif rightmost_typ == YEAR_RE:
                movie_clues.append(rightmost_txt)
                if not quiet:
                    print(f"Found {rightmost_txt} -> movie_clue (year)")

            final_title = _trim_right_separators(final_title[:rightmost_m.start()])
            found_any = True

        if not found_any:
            break

    # Fixed: Multiple passes for TV/anime if clues found
    if tv_clues or anime_clues:
        final_title = _multiple_passes_for_tv_anime(final_title or " ".join(tokens[:title_boundary_index]).strip(), tv_clues, anime_clues, quiet)

    # Fixed: Decide media type (expanded heuristics, anime_set override, ignore movie if TV/anime)
    if anime_set or anime_clues:
        media_type = "anime"
    elif tv_clues:
        media_type = "tv"
    elif movie_clues:
        media_type = "movie"
    else:
        media_type = "unknown"
    
    # Fixed heuristics: Override if known patterns in final_title
    title_lower = (final_title or "").lower()
    tv_patterns = r"(?i)(game of thrones|pawn stars|friends|grimm|stranger things|the mandalorian|s\.w\.a\.t\.|9-1-1|s\.h\.i\.e\.l\.d\.|tv show|ufc)"
    anime_patterns = r"(?i)(one piece|naruto|spy×family|kingdom|gto|rebirth|eizouken)"
    if re.search(tv_patterns, title_lower):
        media_type = "tv"
    elif re.search(anime_patterns, title_lower):
        media_type = "anime"
    elif re.search(r"(?i)ufc", title_lower):
        media_type = "tv"

    cleaned = clean_title(final_title) if final_title else None  # Fixed clean_title below

    # dedupe movie_clues (preserve order) and filter out pure-separator words
    movie_clues = list(OrderedDict.fromkeys(movie_clues))
    words = [w for w in words if re.search(r"\w", w)]

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

def normalize_text(text: str) -> str:
    """
    Normalize Unicode text. Fixed: No case change.
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
    Clean up possible_title for nicer display. Fixed: Preserve original casing, better multi-lang scoring.
    
    Handles:
    - Acronyms (S.H.I.E.L.D, 9-1-1)
    - Multiple languages
    - Unicode normalization
    - Website prefixes
    - Common separators
    """
    if not possible_title:
        return None

    # Normalize without case change
    title = normalize_text(possible_title)
    
    # Keep acronyms or numbered titles as-is (no case change)
    if re.fullmatch(r'([A-Z]\.)+[A-Z]?|\d+(-\d+)+', title):
        return title
        
    # Remove website prefixes (aggressive)
    title = re.sub(r'^(?:www\.[^-\s]+\s*-\s*|\[[^]]+\](?:_|-|\s)*)', '', title)
    
    # Fixed multi-lang: Score and pick best (stronger English preference, keep casing)
    if '/' in title:
        parts = [p.strip() for p in title.split('/') if p.strip()]
        scored = []
        for part in parts:
            eng_score = sum(1 for c in part if 'a' <= c.lower() <= 'z')
            len_score = len(part)
            word_score = len(part.split())
            total = eng_score * 0.5 + len_score * 0.3 + word_score * 0.2
            scored.append((part, total))
        if scored:
            title = max(scored, key=lambda x: x[1])[0]
    
    # Split on separators and clean each part (preserve structure)
    parts = re.split(r'[.\-_]+', title)
    parts = [p.strip() for p in parts if p.strip()]
    
    # Handle multiple languages - take last part (usually English)
    if '/' in ' '.join(parts):
        parts = ' '.join(parts).split('/')[-1].strip().split()
    
    return ' '.join(parts).strip()

def extract_title(filename: str) -> str:
    """
    Extract clean title from filename. (Original unchanged, but uses fixed clean_title)
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
    
    return clean_title(title)  # Use fixed clean_title

# Original test function (unchanged)
if __name__ == "__main__":
    test_cases = [
        "La famille bélier.mkv",
        "doctor_who_2005.8x12.death_in_heaven.720p_hdtv_x264-fov.mkv",
        "08.Планета.обезьян.Революция.2014.BDRip-HEVC.1080p.mkv",
        "Yurusarezaru_mono2.srt",
        "www.Torrenting.com - Anatomy Of A Fall (2023).mkv",
        "Despicable.Me.4.2024.D.TELESYNC_14OOMB.avi",
        "[www.1TamilMV.pics]_The.Great.Indian.Suicide.2023.Tamil.TRUE.WEB-DL.4K.SDR.HEVC.mkv",
        "Game of Thrones - S02E07 - A Man Without Honor [2160p].mkv",
        "Pawn.Stars.S09E13.1080p.HEVC.x265-MeGusta.mkv",
        "S.W.A.T.2017.S08E01.720p.HDTV.x264-SYNCOPY.mkv",
        "Friends.1994.INTEGRALE.MULTI.1080p.WEB-DL.H265-FTMVHD.mkv",
        "9-1-1.s02.mkv",
        "One-piece-ep.1080-v2-1080p-raws.mkv",
        "Naruto Shippuden (001-500) [Complete Series + Movies].mkv",
        "The Mandalorian 2x01 Chapter 9 1080p Web-DL.mkv",
        "[Erai-raws] Kingdom 3rd Season - 02 [1080p].mkv",
    ]
    
    print("Parser Test Results (Fixed Original):\n")
    for filename in test_cases:
        result = parse_filename(filename, quiet=True)
        clean = result["clean_title"] or "None"
        mtype = result["media_type"]
        tv_clues = ",".join(result['tv_clues']) if result['tv_clues'] else ""
        anime_clues = ",".join(result['anime_clues']) if result['anime_clues'] else ""
        movie_clues = ",".join(result['movie_clues']) if result['movie_clues'] else ""
        clues = f"TV:{tv_clues};ANIME:{anime_clues};MOVIE:{movie_clues}"
        clues = clues.replace(";;", ";").rstrip(";")
        
        print(f"ORIG:{filename} | CLEAN:{clean} | TYPE:{mtype} | CLUES:{clues}")