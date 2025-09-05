"""
Core parser module.

Provides parse_filename(name, quiet=False) -> dict
"""

import re
from typing import List, Optional, Tuple, Dict, Any
from .config import CLUES
from .utils import clean_title

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

_RIGHT_SEP_TRIM = re.compile(r"[.\-\s_\(\)\[\]]+$")


def _trim_right_separators(s: str) -> str:
    return _RIGHT_SEP_TRIM.sub("", s)


def _collect_matches(token: str) -> List[Tuple[int,int,str,str]]:
    """Collect matches inside the token and return sorted list of (start,end,type,text)."""
    matches: List[Tuple[int,int,str,str]] = []
    for m in EPISODE_RE.finditer(token):
        matches.append((m.start(1), m.end(1), "episode", m.group(1)))
    for m in TV_CLUE_RE.finditer(token):
        matches.append((m.start(1), m.end(1), "tvclue", m.group(1)))
    for m in SEASON_RE.finditer(token):
        matches.append((m.start(1), m.end(1), "tvseason", m.group(1)))
    for m in RESOLUTION_RE.finditer(token):
        matches.append((m.start(1), m.end(1), "resolution", m.group(1)))
    for m in H264_RE.finditer(token):
        matches.append((m.start(1), m.end(1), "h264", m.group(1)))
    for m in X265_RE.finditer(token):
        matches.append((m.start(1), m.end(1), "x265", m.group(1)))
    for m in AAC_RE.finditer(token):
        matches.append((m.start(1), m.end(1), "aac", m.group(1)))
    for m in BLURAY_RE.finditer(token):
        matches.append((m.start(1), m.end(1), "bluray", m.group(1)))
    for m in EP_RANGE_RE.finditer(token):
        matches.append((m.start(1), m.end(1), "animerange", m.group(1)))
    for m in ANIME_EP_RE.finditer(token):
        matches.append((m.start(1), m.end(1), "animeep", m.group(1)))
    for m in YEAR_RE.finditer(token):
        year = int(m.group(1))
        if 1900 <= year <= 2100:
            matches.append((m.start(1), m.end(1), "movieyear", m.group(1)))
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


def parse_filename(filename: str, quiet: bool = False) -> Dict[str, Any]:
    """
    Parse a filename/foldername.

    Args:
        filename: raw name (not path)
        quiet: if True, no console printing (returns dict only)

    Returns:
        dict with fields:
         original, tv_clues, anime_clues, movie_clues,
         possible_title, clean_title, extras_bits, words, media_type
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

    result: Dict[str, Any] = {
        "original": filename,
        "tv_clues": tv_clues,
        "anime_clues": anime_clues,
        "movie_clues": movie_clues,
        "possible_title": final_title,
        "clean_title": cleaned,
        "extras_bits": extras_bits,
        "words": words,
        "media_type": media_type
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
