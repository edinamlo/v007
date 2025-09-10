"""
Enhanced core parser module - Hybrid Token + Smart Anime Detection.

Combines the proven token-based approach (22 passes) with smart anime prefix detection
and iterative clue stripping for maximum accuracy.
"""

import re
import unicodedata
from typing import List, Optional, Tuple, Dict, Any
from collections import OrderedDict
from config import CLUES
from utils import clean_title

# Patterns (search inside tokens) - Proven from 22-pass version
EPISODE_RE    = re.compile(r"(?i)(?<![A-Za-z0-9])(s\d{2}e\d{2,4})(?![A-Za-z0-9])")
TV_CLUE_RE    = re.compile(r"(?i)(?<![A-Za-z0-9])(s\d{2}(?:-s\d{2})?)(?![A-Za-z0-9])")
SEASON_RE     = re.compile(r"(?i)(?<![A-Za-z0-9])(season \d{1,2})(?![A-Za-z0-9])")
RESOLUTION_RE = re.compile(r"(?i)(?<!\d)(\d{3,4}(?:p|px))(?![A-Za-z0-9])")
H264_RE       = re.compile(r"(?i)(h\.?264)")
X265_RE       = re.compile(r"(?i)(x265)")
AAC_RE        = re.compile(r"(?i)(aac(?:2\.0|2|\.0)?)")
BLURAY_RE     = re.compile(r"(?i)(?:blu[- ]?ray|bluray|bdrip|bdremux|bdr)")
EP_RANGE_RE   = re.compile(r"(?i)\((\d{3,4}-\d{3,4})\)")
ANIME_EP_RE   = re.compile(r"(?i)(?<![A-Za-z0-9])(ep?\.?\d{1,4})(?![A-Za-z0-9])")
YEAR_RE       = re.compile(r"(?i)(?<![A-Za-z0-9])(\d{4})(?![A-Za-z0-9])")
CHAPTER_RE    = re.compile(r"(?i)(?<![A-Za-z0-9])(chapter[\s._-]?\d+)(?![A-Za-z0-9])")

# Anime movie patterns
MOVIE_KEYWORDS = re.compile(r"(?i)(?:movie|film|theater|劇場版)", re.IGNORECASE)

# Smart prefix detection patterns
ANIME_PREFIX_PATTERNS = [
    re.compile(r"^\[(.*?)\](?:[_\-\s\[\]\.\(\)]+|$)", re.IGNORECASE),  # [Erai-raws], [NC-Raws]
    re.compile(r"^【(.*?)】(?:[★\s]+|$)", re.IGNORECASE),  # 【喵萌奶茶屋】
    re.compile(r"^\[(.*?)\]\s*\*?01月新番\*?(?:\[|$)", re.IGNORECASE),  # Anime seasonal patterns
]

WEBSITE_PREFIX_PATTERNS = [
    re.compile(r"^(?:www\.[^\s\.\[\(]*|\[www\.[^\]]*\]|www\.torrenting\.com|www\.tamil.*|ww\.tamil.*|\[www\.arabp2p\.net\])(?:[_\-\s\[\]\.\(\)]+|$)", re.IGNORECASE),
    re.compile(r"^(?:\[.*?\])+(?:[_\-\s]+|$)", re.IGNORECASE),  # Generic bracketed prefixes
]

_RIGHT_SEP_TRIM = re.compile(r"[.\-\s_\(\)\[\]]+$")

def _trim_right_separators(s: str) -> str:
    return _RIGHT_SEP_TRIM.sub("", s)

def _is_anime_release_group(prefix: str, anime_groups: List[str]) -> bool:
    """
    Check if the prefix matches any known anime release group or pattern.
    """
    if not prefix or not anime_groups:
        return False
    
    # Clean prefix for comparison
    prefix_clean = re.sub(r"[_\-\s\.\[\]\(\)★]+", "", prefix).strip().lower()
    
    # Check against known anime groups
    for group in anime_groups:
        group_clean = re.sub(r"[_\-\s\.\[\]\(\)★]+", "", group).strip().lower()
        if (prefix_clean == group_clean or 
            prefix_clean in group_clean or 
            group_clean in prefix_clean or
            len(prefix_clean) > 3 and any(part in prefix_clean for part in ['raws', 'sub', 'fansub', 'encode'])):
            return True
    
    # Check for anime seasonal patterns
    if re.search(r"(?i)(?:新番|raws|sub|fansub|encode|team)", prefix_clean):
        return True
    
    return False

def _smart_prefix_detection(name: str, quiet: bool = False) -> Tuple[str, bool, List[str]]:
    """
    Smart prefix detection that identifies anime release groups.
    
    Returns: (cleaned_name, is_anime_detected, removed_prefixes)
    """
    original_name = name
    removed_prefixes = []
    is_anime_detected = False
    
    # Get anime release groups from config
    anime_groups = CLUES.get("release_groups_anime", [])
    
    # First pass: Check for anime prefixes
    for pattern in ANIME_PREFIX_PATTERNS:
        match = pattern.search(name)
        if match:
            prefix = match.group(1) if match.lastindex else match.group(0)
            
            if _is_anime_release_group(prefix, anime_groups):
                # Found anime release group!
                is_anime_detected = True
                name = name[match.end():].strip()
                removed_prefixes.append(f"[{prefix}]")
                if not quiet:
                    print(f"  Found anime release group: [{prefix}]")
                # Continue checking for more prefixes
                continue
            else:
                # Regular bracketed prefix, remove but don't set anime flag
                name = name[match.end():].strip()
                removed_prefixes.append(f"[{prefix}]")
                if not quiet:
                    print(f"  Removed generic prefix: [{prefix}]")
                continue
    
    # Second pass: Remove website prefixes
    for pattern in WEBSITE_PREFIX_PATTERNS:
        match = pattern.search(name)
        if match:
            prefix = match.group(0)
            name = name[match.end():].strip()
            removed_prefixes.append(prefix)
            if not quiet:
                print(f"  Removed website prefix: {prefix}")
            # Continue checking for more prefixes
    
    # Final cleanup
    name = _trim_right_separators(name).strip()
    
    if not quiet and removed_prefixes:
        print(f"  Prefixes removed: {', '.join(removed_prefixes[:2])}...")
    
    return name, is_anime_detected, removed_prefixes

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

def _iterative_clue_stripping(final_title: str, tv_clues: List[str], anime_clues: List[str], 
                             movie_clues: List[str], extras_bits: List[str], quiet: bool = False) -> str:
    """
    Iteratively strip clues from the end of final_title until no more media clues found.
    This handles cases where multiple passes are needed for TV/anime clues.
    """
    clue_patterns = [EPISODE_RE, TV_CLUE_RE, SEASON_RE, EP_RANGE_RE, ANIME_EP_RE, YEAR_RE]
    
    iterations = 0
    max_iterations = 5  # Prevent infinite loops
    
    while final_title and iterations < max_iterations:
        found_any = False
        rightmost_end = -1
        rightmost_m = None
        rightmost_typ = None
        rightmost_txt = None
        
        # Find rightmost clue in final_title
        for pat, clue_type in [
            (EPISODE_RE, "episode"),
            (TV_CLUE_RE, "tvclue"), 
            (SEASON_RE, "tvseason"),
            (EP_RANGE_RE, "animerange"),
            (ANIME_EP_RE, "animeep"),
            (YEAR_RE, "movieyear")
        ]:
            for m in pat.finditer(final_title):
                end_pos = m.end(1) if m.lastindex else m.end()
                if end_pos > rightmost_end:
                    rightmost_end = end_pos
                    rightmost_m = m
                    rightmost_typ = clue_type
                    rightmost_txt = m.group(1) if m.lastindex else m.group(0)
        
        # If clue found at end of title, strip it
        if rightmost_m and rightmost_end >= len(final_title) - 5:  # Close to end
            norm_txt = rightmost_txt if rightmost_typ == "movieyear" else rightmost_txt.upper()
            
            if rightmost_typ == "episode":
                if norm_txt not in tv_clues:
                    tv_clues.append(norm_txt)
            elif rightmost_typ == "tvclue":
                pieces = [p.upper() for p in norm_txt.split("-") if p]
                for p in pieces:
                    if p not in tv_clues:
                        tv_clues.append(p)
            elif rightmost_typ == "tvseason":
                if norm_txt not in tv_clues:
                    tv_clues.append(norm_txt)
            elif rightmost_typ == "animerange":
                if norm_txt not in anime_clues:
                    anime_clues.append(norm_txt)
            elif rightmost_typ == "animeep":
                if norm_txt not in anime_clues:
                    anime_clues.append(norm_txt)
            elif rightmost_typ == "movieyear":
                if norm_txt not in movie_clues:
                    movie_clues.append(norm_txt)
            
            # Strip the clue from title
            final_title = _trim_right_separators(final_title[:rightmost_m.start(1)])
            found_any = True
            iterations += 1
            
            if not quiet:
                print(f"  Iteration {iterations}: Stripped '{rightmost_txt}' from title end")
        
        if not found_any:
            break
    
    return final_title

def _determine_media_type_enhanced(tv_clues: List[str], anime_clues: List[str], movie_clues: List[str], 
                                  final_title: str, is_anime_detected: bool, matched_clues: Dict[str, List[str]]) -> str:
    """
    Enhanced media type determination with anime priority and multiple passes.
    """
    # Priority 1: Anime detection from prefix takes precedence
    if is_anime_detected:
        return "anime"
    
    # Priority 2: Check clues (TV > Anime > Movie)
    if tv_clues:
        return "tv"
    elif anime_clues:
        return "anime"
    elif movie_clues:
        return "movie"
    
    # Priority 3: Check anime release groups in matched clues
    if matched_clues.get("release_groups_anime"):
        return "anime"
    
    # Priority 4: Heuristic analysis of title
    title_lower = final_title.lower()
    
    # TV patterns
    tv_patterns = [
        r"season", r"s\d+", r"e\d+", r"episode", 
        r"friends", r"game\s+of\s+thrones", r"pawn\s+stars", r"grimm", 
        r"stranger\s+things", r"the\s+mandalorian", r"9-1-1"
    ]
    if any(re.search(pattern, title_lower) for pattern in tv_patterns):
        return "tv"
    
    # Anime patterns
    anime_patterns = [
        r"one\s+piece", r"naruto", r"spy\s*×\s*family", r"kingdom", 
        r"gto", r"great\s+teacher\s+onizuka", r"eizouken"
    ]
    if any(re.search(pattern, title_lower) for pattern in anime_patterns):
        return "anime"
    
    # Movie patterns (year but no TV indicators)
    if re.search(r"\d{4}", final_title) and not re.search(r"(?i)(s\d+|e\d+)", title_lower):
        return "movie"
    
    return "unknown"

def parse_filename(filename: str, quiet: bool = False) -> dict:
    """
    Enhanced parser combining token-based approach with smart anime detection.
    Follows the proven logic from the 22-pass version with improvements.
    """
    if not quiet:
        print(f"Parsing: {filename}")
    
    # Step 1: Smart prefix detection
    name, is_anime_detected, removed_prefixes = _smart_prefix_detection(filename, quiet)
    
    # Remove extension
    m = re.match(r"^(?P<name>.+?)(?P<ext>\.[^.]+)$", name)
    if m:
        name, ext = m.group("name"), m.group("ext")
    else:
        name, ext = name, ""
    
    # If extension itself includes clues, merge into name (rare)
    if ext and len(ext) > 4:
        ext_matches = _collect_matches(ext)
        if ext_matches:
            name += ext
            ext = ""
        else:
            # Treat ext as word if no matches and it's not a common extension
            if _is_likely_title_word(ext):
                if not quiet:
                    print(f"  Found {ext} -> word")
    
    if not quiet and name != filename:
        print(f"  Cleaned name: {name}")
        if removed_prefixes:
            print(f"  Removed prefixes: {', '.join(removed_prefixes)}")
        if is_anime_detected:
            print(f"  Anime detection: {is_anime_detected}")
    
    # Step 2: Token-based processing (proven 22-pass logic)
    tokens = name.split()  # only whitespace split; keep punctuation inside tokens

    extras_bits: List[str] = []
    words: List[str] = []
    tv_clues: List[str] = []
    anime_clues: List[str] = []
    movie_clues: List[str] = []
    possible_title: Optional[str] = None
    title_boundary_index = len(tokens)
    movie_found = False

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
                        extras_bits.append(raw_tok.lower())
                    elif cat in ("quality_clues", "misc_clues"):
                        extras_bits.append(raw_tok)
                    elif cat == "audio_clues":
                        extras_bits.append(raw_tok.upper())
                    elif cat in ("release_groups", "release_groups_anime"):
                        words.append(raw_tok)
                    else:
                        words.append(raw_tok)
                    if not quiet:
                        print(f"  Found {raw_tok} -> {cat}")
                else:
                    # Use enhanced title word detection
                    if _is_likely_title_word(raw_tok):
                        if not quiet:
                            print(f"  Found {raw_tok} -> title_word")
                        words.append(raw_tok)
                    else:
                        # Treat as potential technical metadata
                        norm_tok = raw_tok.lower()
                        if norm_tok not in extras_bits:
                            extras_bits.append(norm_tok)
                        if not quiet:
                            print(f"  Found {raw_tok} -> metadata")
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
                print(f"  Found possible title: {possible_title}")

        title_boundary_index = min(title_boundary_index, i)

        for start, end, typ, text in matches:
            typ = typ.lower()
            
            # Enhanced movie year detection with anime context
            if typ == "movieyear" and is_anime_detected:
                # If anime detected, treat year as regular metadata unless "movie" keyword found
                if MOVIE_KEYWORDS.search(raw_tok):
                    if not movie_found:
                        movie_clues.append(text)
                        movie_found = True
                        if not quiet:
                            print(f"  Found {text} (in '{raw_tok}') -> movie_clue (year with movie keyword)")
                else:
                    # Treat as anime metadata
                    norm_year = text.lower()
                    if norm_year not in extras_bits:
                        extras_bits.append(norm_year)
                    if not quiet:
                        print(f"  Found {text} (in '{raw_tok}') -> anime metadata (year)")
                    continue
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
                                print(f"  Found {possible_title} -> possible_title (fallback due to movie year)")
                    if not quiet:
                        print(f"  Found {text} (in '{raw_tok}') -> movie_clue (year)")
                else:
                    if not quiet:
                        print(f"  Skipping extra movie year {text}")
            
            elif typ == "episode":
                tv_clues.append(text.upper())
                title_boundary_index = min(title_boundary_index, i)
                if not quiet:
                    print(f"  Found {text} (in '{raw_tok}') -> tv_clue (episode)")
            elif typ == "tvclue":
                pieces = [p.upper() for p in text.split("-")]
                tv_clues.extend(pieces)
                title_boundary_index = min(title_boundary_index, i)
                if not quiet:
                    print(f"  Found {text} (in '{raw_tok}') -> tv_clue")
            elif typ == "tvseason":
                tv_clues.append(text.upper())
                title_boundary_index = min(title_boundary_index, i)
                if not quiet:
                    print(f"  Found {text} (in '{raw_tok}') -> tv_clue (season)")
            elif typ == "animerange":
                anime_clues.append(text.upper())
                title_boundary_index = min(title_boundary_index, i)
                if not quiet:
                    print(f"  Found {text} (in '{raw_tok}') -> anime_clue (range)")
            elif typ == "animeep":
                anime_clues.append(text.upper())
                title_boundary_index = min(title_boundary_index, i)
                if not quiet:
                    print(f"  Found {text} (in '{raw_tok}') -> anime_clue (ep)")
            elif typ == "chapter":
                # For chapters, prefer anime if anime detected, otherwise TV
                if is_anime_detected and not tv_clues:
                    anime_clues.append(text.upper())
                else:
                    tv_clues.append(text.upper())
                title_boundary_index = min(title_boundary_index, i)
                if not quiet:
                    print(f"  Found {text} (in '{raw_tok}') -> {'anime' if is_anime_detected else 'tv'}_clue (chapter)")
            elif typ == "resolution":
                norm = text.lower()
                if norm not in extras_bits:
                    extras_bits.append(norm)
                if not quiet:
                    print(f"  Found {text} (in '{raw_tok}') -> resolution")
            elif typ == "h264":
                if "h.264" not in extras_bits:
                    extras_bits.append("h.264")
                if not quiet:
                    print(f"  Found {text} (in '{raw_tok}') -> codec (h.264)")
            elif typ == "x265":
                if "x265" not in extras_bits:
                    extras_bits.append("x265")
                if not quiet:
                    print(f"  Found {text} (in '{raw_tok}') -> extras_bits")
            elif typ == "aac":
                if "aac" not in extras_bits:
                    extras_bits.append("aac")
                if not quiet:
                    print(f"  Found {text} (in '{raw_tok}') -> extras_bits")
            elif typ == "bluray":
                if "bluray" not in extras_bits:
                    extras_bits.append("bluray")
                if not quiet:
                    print(f"  Found {text} (in '{raw_tok}') -> extras_bits (bluray)")

        # Add unrecognized substrings between/after matches to words
        prev_end = 0
        for j in range(len(matches)):
            start, end, typ, text = matches[j]
            if start > prev_end:
                between = raw_tok[prev_end:start]
                between_clean = _trim_right_separators(between)
                if between_clean and _is_likely_title_word(between_clean):
                    if not quiet:
                        print(f"  Found {between_clean} (in '{raw_tok}') -> title_word")
                    words.append(between_clean)
            prev_end = end
        
        if prev_end < len(raw_tok):
            after = raw_tok[prev_end:]
            after_clean = _trim_right_separators(after)
            if after_clean and _is_likely_title_word(after_clean):
                if not quiet:
                    print(f"  Found {after_clean} (in '{raw_tok}') -> title_word")
                words.append(after_clean)

        i -= 1

    # Step 3: Set initial possible title
    final_title = possible_title or " ".join(tokens[:title_boundary_index]).strip() or None
    
    if not quiet and final_title:
        print(f"  Initial possible title: {final_title}")

    # Step 4: Iterative clue stripping for TV/Anime (multiple passes)
    final_title = _iterative_clue_stripping(final_title, tv_clues, anime_clues, movie_clues, extras_bits, quiet)

    # Step 5: Enhanced media type determination
    media_type = _determine_media_type_enhanced(tv_clues, anime_clues, movie_clues, final_title or "", 
                                              is_anime_detected, {})

    # Step 6: Clean title
    cleaned = clean_title(final_title) if final_title else None

    # Step 7: Build matched clues from CLUES config
    matched_clues: Dict[str, List[str]] = {}
    clue_keys = [
        "resolution_clues", "audio_clues", "quality_clues", 
        "release_groups", "release_groups_anime", "misc_clues"
    ]
    
    search_space = [filename, final_title or ""] + extras_bits + words
    for key in clue_keys:
        candidates = CLUES.get(key, []) if isinstance(CLUES, dict) else []
        found = []
        for c in candidates:
            low = c.lower()
            for token in search_space:
                if token and (low in token.lower() or token.lower() in low):
                    found.append(c)
                    break
        if found:
            # Deduplicate preserving order
            seen = []
            for f in found:
                if f not in seen:
                    seen.append(f)
            matched_clues[key] = seen
    
    # If anime detected, add removed prefixes to anime groups
    if is_anime_detected and removed_prefixes:
        for prefix in removed_prefixes:
            if prefix.startswith("[") and prefix.endswith("]"):
                group_name = prefix[1:-1].strip()
                if group_name not in matched_clues.get("release_groups_anime", []):
                    matched_clues.setdefault("release_groups_anime", []).append(group_name)

    # Step 8: Post-process and deduplicate
    movie_clues = list(OrderedDict.fromkeys(movie_clues))
    tv_clues = list(OrderedDict.fromkeys(tv_clues))
    anime_clues = list(OrderedDict.fromkeys(anime_clues))
    
    # Normalize extras_bits
    normalized_extras = [eb.lower() if isinstance(eb, str) and not eb.isupper() else eb for eb in extras_bits]
    extras_bits = list(OrderedDict.fromkeys(normalized_extras))
    
    # Filter words
    words = [w for w in words if re.search(r"\w", w) and _is_likely_title_word(w)]

    # Step 9: Final media type adjustment
    # If anime detected but classified as TV, reclassify
    if is_anime_detected and media_type == "tv":
        media_type = "anime"
        # Move TV episode-like clues to anime
        anime_clues.extend([c for c in tv_clues if re.match(r"(?i)(?:s\d+e?\d+|e\d+|chapter\s+\d+)", c)])
        tv_clues = [c for c in tv_clues if not re.match(r"(?i)(?:s\d+e?\d+|e\d+|chapter\s+\d+)", c)]
        if not quiet:
            print(f"  Reclassified as anime due to prefix detection")

    # Step 10: Build result
    result: Dict[str, Any] = {
        "original": filename,
        "possible_title": final_title or "",
        "clean_title": cleaned,
        "media_type": media_type,
        "tv_clues": tv_clues,
        "anime_clues": anime_clues,
        "movie_clues": movie_clues,
        "extras_bits": extras_bits,
        "extras_bits_unknown": [],  # Will be populated by ClueManager
        "words": words,
        "matched_clues": matched_clues,
        "resolution_clues": matched_clues.get("resolution_clues", []),
        "audio_clues": matched_clues.get("audio_clues", []),
        "quality_clues": matched_clues.get("quality_clues", []),
        "release_groups": matched_clues.get("release_groups", []),
        "release_groups_anime": matched_clues.get("release_groups_anime", []),
        "misc_clues": matched_clues.get("misc_clues", []),
        "is_anime_detected": is_anime_detected,
        "removed_prefixes": removed_prefixes
    }

    if not quiet:
        print("\nSummary:")
        print(f"  Media Type: {result['media_type']} (anime detected: {is_anime_detected})")
        print(f"  Possible Title: {result['possible_title'] or 'None'}")
        print(f"  Clean Title: {result['clean_title'] or 'None'}")
        if tv_clues:
            print(f"  TV Clues: {', '.join(tv_clues)}")
        if anime_clues:
            print(f"  Anime Clues: {', '.join(anime_clues)}")
        if movie_clues:
            print(f"  Movie Clues: {', '.join(movie_clues)}")
        if extras_bits:
            print(f"  Technical: {', '.join(extras_bits[:3])}...")
        if words:
            print(f"  Words: {', '.join(words[:5])}...")
        if matched_clues.get("release_groups_anime"):
            print(f"  Anime Groups: {', '.join(matched_clues['release_groups_anime'])}")

    return result

def _is_likely_title_word(token: str) -> bool:
    """Enhanced heuristic to determine if token is likely part of title."""
    if not token or len(token) < 2:
        return False
    
    # Remove common metadata patterns but preserve title-like content
    cleaned = re.sub(r"(?i)(?:s\d{2}e?\d*|season\s+\d+|ep?\d+|bluray|h\.?264|x265|aac|\d{4}|\d{3,4}p|web|bd|complete|part|cd\d+|team|raws|sub|encode|group)", "", token)
    cleaned = cleaned.strip("._- ")
    
    # Has letters (including international) and reasonable length
    has_letters = bool(re.search(r"[a-zA-Zα-ωΑ-Ωа-яА-Я]", cleaned))
    has_length = len(cleaned) > 1
    not_pure_numeric = not re.fullmatch(r'^\d+[a-z]?$', token, re.IGNORECASE)
    
    # Not common technical terms
    not_technical = not re.match(r"(?i)(?:hdtv|webdl|pdtv|dsrip|dvdrip|custom|extended|integral|multi)", token)
    
    return has_letters and has_length and not_pure_numeric and not_technical

# Keep the extract_title function for backward compatibility
def extract_title(filename: str) -> str:
    """
    Simple title extraction for backward compatibility.
    """
    result = parse_filename(filename, quiet=True)
    return result.get("clean_title", "") or result.get("possible_title", filename)

def normalize_text(text: str) -> str:
    """
    Normalize Unicode text - kept for backward compatibility.
    """
    if not text:
        return ""
    
    # Normalize Unicode combining characters
    text = unicodedata.normalize('NFKC', text)
    
    # Convert full-width characters to normal width
    text = ''.join([
        unicodedata.normalize('NFKC', c) if unicodedata.east_asian_width(c) == 'F' else c
        for c in text
    ])
    
    # Normalize common special characters and punctuation
    replacements = {
        '–': '-', '—': '-', '‐': '-',  # Dashes
        '´': "'", 'ʻ': "'", '’': "'",  # Apostrophes
        '″': '"', '”': '"', '«': '"', '»': '"',  # Quotes
        '…': '...', '⋯': '...',  # Ellipsis
        '‑': '-',  # Non-breaking hyphen
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text.strip()

# Test function
if __name__ == "__main__":
    test_cases = [
        "www.TamilBlasters.cam - Titanic (1997)[1080p BDRip].mkv",
        "[Erai-raws] Kingdom 3rd Season - 02 [1080p].mkv",
        "[NC-Raws] 间谍过家家 / SPY×FAMILY - 04 (B-Global 1920x1080 HEVC AAC MKV).mkv",
        "【喵萌奶茶屋】★01月新番★[別對映像研出手！/Eizouken ni wa Te wo Dasu na！][01][1080p][繁體].mkv",
        "doctor_who_2005.8x12.death_in_heaven.720p_hdtv_x264-fov.mkv",
        "Game of Thrones - S02E07 - A Man Without Honor [2160p].mkv",
        "Friends.1994.INTEGRALE.MULTI.1080p.WEB-DL.H265-FTMVHD.mkv",
        "S.W.A.T.2017.S08E01.720p.HDTV.x264-SYNCOPY[TGx].mkv",
        "One-piece-ep.1080-v2-1080p-raws.mkv",
        "Голубая волна / Blue Crush (2002) DVDRip.mkv",
        "[SweetSub][Mutafukaz / MFKZ][Movie][BDRip][1080P][AVC 8bit][简体内嵌].mkv"
    ]
    
    print("Hybrid Parser Test Results:\n")
    for filename in test_cases:
        result = parse_filename(filename, quiet=True)
        clean = result["clean_title"] or "None"
        mtype = result["media_type"]
        anime_detected = result["is_anime_detected"]
        tv = ",".join(result['tv_clues']) if result['tv_clues'] else ""
        anime = ",".join(result['anime_clues']) if result['anime_clues'] else ""
        movie = ",".join(result['movie_clues']) if result['movie_clues'] else ""
        clues_str = f"TV:{tv};ANIME:{anime};MOVIE:{movie}"
        clues_str = clues_str.replace(";;", ";").rstrip(";")
        anime_groups = ",".join(result['release_groups_anime']) if result['release_groups_anime'] else ""
        
        print(f"ORIG:{filename}")
        print(f"  CLEAN:{clean} | TYPE:{mtype} | ANIME_DETECTED:{anime_detected} | CLUES:{clues_str}")
        if anime_groups:
            print(f"  ANIME GROUPS:{anime_groups}")
        print()