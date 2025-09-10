"""
media_parser_pipeline.py

Enhanced media filename parser with:
- resolution-based split (unchanged)
- right->left parsing on the res_right side
- strict anime episode matching (two-digit formats: "01", "ep02", "ep.20")
- extractor-named notes for traceability (e.g. "AnimeExtractor: matched episode 02")
- logging for debug (logger.debug/info)
- careful heuristics to avoid misclassifying large numbers or years as episodes
- test harness using your example filenames

Keep iterating — this file prints detailed notes for each extractor that matches.
"""

import re
import logging
from dataclasses import dataclass, asdict, field
from typing import Optional, Tuple, List

# -------------------- Logging Setup --------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)  # change to DEBUG for more verbose output

# -------------------- Configuration / Constants --------------------
KNOWN_RESOLUTIONS = [
    "2160p", "1080p", "720p", "480p", "360p",
    "4k", "8k", "1920x1080", "1280x720", "1024x768",
]

# A conservative list of typical release-group-like bracket tokens (extend as needed)
KNOWN_ANIME_RELEASE_GROUPS = [
    r"SubsPlease", r"Erai-raws", r"Exiled-Destiny",
    r"HorribleSubs", r"CR", r"Funimation",
    r"ANiDL", r"UTW", r"Nekomoe kissaten",
]

# Junk tokens used when cleaning titles/extras (not exhaustive)
JUNK_WORDS = set([
    '1080p', '720p', '480p', 'hdtv', 'web-dl', 'webrip', 'bluray', 'dvd', 'x264', 'x265',
    'aac', 'ac3', 'hevc', 'dts', 'truehd', 'dolby', 'dual', 'audio', 'eng', 'multi',
    'sub', 'subs', 'raws', 'hd', 'fhd', 'uhd', '4k', 'v2', 'bit', 'lpcm', 'mkv', 'mp4',
    'jpn', 'eac3', 'aac2.0', 'h264', 'h.264', 'msubs-toonshub', 'complete', 'series',
    'movies', 'subtitle', 'multiple', 'years', 'quest', 'web', 'ddp', 'web-dl', 'webdl'
])

# Precompiled regexes
RE_RES_WxH = re.compile(r"\b(\d{3,4})x(\d{3,4})\b")
RE_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
RE_SEASON_EP = re.compile(r"\bS(\d{1,2})E(\d{1,3})\b", flags=re.I)
RE_SEASON_EP_ALT = re.compile(r"\b(\d{1,2})x(\\d{1,3})\b")
# Strict anime episode markers: ep02, ep.02, Episode 02, or plain two-digit numbers when anchored
RE_EP_MARKER_STRICT = re.compile(r"\b(?:ep\.?|episode)\s*(\d{2})\b", flags=re.I)
# Plain two-digit token that we will accept if heuristics allow (e.g., '- 05' or at end)
RE_PLAIN_TWO_DIGIT = re.compile(r"(?<!\d)(\d{2})(?!\d)")
RE_PAREN_RANGE = re.compile(r"\((\d{1,4})-(\d{1,4})\)")
RE_DASH_NUM = re.compile(r"[-\s]+(\d{2})(?!\d)")  # specifically 2 digits after dash/space
RE_BRACKET_GROUP = re.compile(r"\[([^\]]+)\]")

# -------------------- Data Model --------------------

@dataclass
class ParseResult:
    original: str
    resolution: Optional[str] = None
    res_left: str = ""
    res_right: str = ""
    is_anime: bool = False
    anime_group: Optional[str] = None
    anime_episode: Optional[str] = None
    is_tv: bool = False
    tv_match: Optional[str] = None
    is_movie: bool = False
    movie_year: Optional[str] = None
    possible_title: str = ""
    notes: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

# -------------------- Helpers --------------------

def _clean_separators(s: str) -> str:
    s = s or ""
    s = re.sub(r"[\._]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _strip_junk_tokens(tokens: List[str]) -> List[str]:
    return [t for t in tokens if t and t.lower() not in JUNK_WORDS]

def _safe_int(s: str) -> Optional[int]:
    try:
        return int(s)
    except Exception:
        return None

# -------------------- Extractors --------------------

def extract_resolution(filename: str) -> Tuple[Optional[str], str, str]:
    logger.debug("ResolutionExtractor: input=%s", filename)
    lowered = filename
    for token in KNOWN_RESOLUTIONS:
        pat = re.compile(r"\b" + re.escape(token) + r"\b", re.I)
        m = pat.search(lowered)
        if m:
            logger.info("ResolutionExtractor: matched %s", m.group(0))
            left = filename[:m.start()].strip()
            right = filename[m.end():].strip()
            return m.group(0), left, right
    m = RE_RES_WxH.search(filename)
    if m:
        logger.info("ResolutionExtractor: matched WxH %s", m.group(0))
        left = filename[:m.start()].strip()
        right = filename[m.end():].strip()
        return m.group(0), left, right
    logger.debug("ResolutionExtractor: no match")
    return None, filename, ""

def extract_release_group(left: str, right: str) -> Tuple[Optional[str], str, str, Optional[str]]:
    """Find release group and return (group, new_left, new_right, extractor_name).

    Looks for known group tokens or heuristics on bracketed tokens.
    """
    logger.debug("ReleaseGroupExtractor: left=%s right=%s", left, right)
    combined = f"{left} {right}".strip()
    # Known groups (case-insensitive)
    for g in KNOWN_ANIME_RELEASE_GROUPS:
        pat = re.compile(re.escape(g), re.I)
        if pat.search(combined):
            m = pat.search(combined)
            group = m.group(0)
            logger.info("ReleaseGroupExtractor: matched known group %s", group)
            # remove from left/right if present
            new_left = re.sub(pat, "", left, flags=re.I).strip()
            new_right = re.sub(pat, "", right, flags=re.I).strip()
            return group, _clean_separators(new_left), _clean_separators(new_right), 'ReleaseGroupExtractor'
    # Bracket heuristics on right
    r_brackets = RE_BRACKET_GROUP.findall(right)
    for b in r_brackets:
        if '-' in b or (len(b) > 3 and not re.fullmatch(r'[A-Z]{2,3}', b)):
            logger.info("ReleaseGroupExtractor: matched bracket on right %s", b)
            new_right = re.sub(re.escape(f"[{b}]"), "", right)
            return b, _clean_separators(left), _clean_separators(new_right), 'ReleaseGroupExtractor'
    # Bracket heuristics on left
    l_brackets = RE_BRACKET_GROUP.findall(left)
    for b in l_brackets:
        if '-' in b or (len(b) > 3 and not re.fullmatch(r'[A-Z]{2,3}', b)):
            logger.info("ReleaseGroupExtractor: matched bracket on left %s", b)
            new_left = re.sub(re.escape(f"[{b}]"), "", left)
            return b, _clean_separators(new_left), _clean_separators(right), 'ReleaseGroupExtractor'
    logger.debug("ReleaseGroupExtractor: no match")
    return None, _clean_separators(left), _clean_separators(right), None

def extract_anime_episode(right_text: str, left_text: str) -> Tuple[Optional[str], str, str, Optional[str]]:
    """Attempt to extract anime episodes from right_text first (right->left).

    Returns (episode_str, new_right_text, new_left_text, extractor_name)
    """
    logger.debug("AnimeExtractor: right=%s left=%s", right_text, left_text)
    rt = right_text or ""
    lt = left_text or ""

    # 1) Parenthesis ranges like (001-500)
    m = RE_PAREN_RANGE.search(rt)
    if m:
        ep = m.group(0).strip()
        new_rt = re.sub(re.escape(ep), "", rt).strip()
        logger.info("AnimeExtractor: matched range %s", ep)
        return ep, new_rt, lt, 'AnimeExtractor(range)'

    # 2) Strict ep markers: ep02, ep.02, Episode 02 (two digits only)
    m = RE_EP_MARKER_STRICT.search(rt)
    if m:
        ep = m.group(1)
        new_rt = re.sub(m.group(0), "", rt).strip()
        logger.info("AnimeExtractor: matched EP marker %s", ep)
        return ep.lstrip('0') or '0', new_rt, lt, 'AnimeExtractor(ep_marker)'

    # 3) Dash followed by two digits on the right (e.g., " - 05")
    m = RE_DASH_NUM.search(rt)
    if m:
        candidate = m.group(1)
        # heuristic: if candidate is two digits it's valid; avoid 19xx/20xx later
        if 10 <= int(candidate) <= 99:
            new_rt = re.sub(RE_DASH_NUM, "", rt).strip()
            logger.info("AnimeExtractor: matched dash two-digit %s", candidate)
            return candidate.lstrip('0') or '0', new_rt, lt, 'AnimeExtractor(dash_two_digit)'

    # 4) Plain two digit on right side but with heuristics
    m = RE_PLAIN_TWO_DIGIT.search(rt)
    if m:
        candidate = m.group(1)
        # avoid matching years
        if 1900 <= int(candidate) <= 2099:
            logger.debug("AnimeExtractor: plain two-digit looks like year: %s", candidate)
        elif int(candidate) > 99:
            logger.debug("AnimeExtractor: plain two-digit too large: %s", candidate)
        else:
            # avoid matching tokens like '100 Years' earlier in left_text
            if re.search(r"\b(years?|quest|anniversary|century)\b", (lt + " " + rt), re.I):
                logger.debug("AnimeExtractor: suppressed plain two-digit due to title keywords")
            else:
                new_rt = rt[:m.start()].strip()
                logger.info("AnimeExtractor: matched plain two-digit %s", candidate)
                return candidate.lstrip('0') or '0', new_rt, lt, 'AnimeExtractor(plain_two_digit)'

    # 5) As a last attempt, look in left_text (useful if right_text was empty)
    m = RE_EP_MARKER_STRICT.search(lt)
    if m:
        ep = m.group(1)
        new_lt = re.sub(m.group(0), "", lt).strip()
        logger.info("AnimeExtractor: matched ep marker in left %s", ep)
        return ep.lstrip('0') or '0', rt, new_lt, 'AnimeExtractor(ep_marker_left)'

    # 6) dash num in left
    m = RE_DASH_NUM.search(lt)
    if m:
        candidate = m.group(1)
        if 10 <= int(candidate) <= 99:
            new_lt = re.sub(RE_DASH_NUM, "", lt).strip()
            logger.info("AnimeExtractor: matched dash two-digit in left %s", candidate)
            return candidate.lstrip('0') or '0', rt, new_lt, 'AnimeExtractor(dash_left)'

    logger.debug("AnimeExtractor: no match")
    return None, rt, lt, None

def extract_tv_show(right_text: str, left_text: str) -> Tuple[Optional[str], str, str, Optional[str]]:
    logger.debug("TVExtractor: right=%s left=%s", right_text, left_text)
    rt = right_text or ""
    lt = left_text or ""

    # Check right side first
    m = RE_SEASON_EP.search(rt)
    if m:
        match = m.group(0)
        new_rt = re.sub(re.escape(match), "", rt, flags=re.I).strip()
        logger.info("TVExtractor: matched %s", match)
        return match, new_rt, lt, 'TVExtractor(SxxEyy_right)'
    m = RE_SEASON_EP_ALT.search(rt)
    if m:
        match = m.group(0)
        new_rt = re.sub(re.escape(match), "", rt).strip()
        logger.info("TVExtractor: matched alt %s", match)
        return match, new_rt, lt, 'TVExtractor(alt_right)'

    # Fallback to left side
    m = RE_SEASON_EP.search(lt)
    if m:
        match = m.group(0)
        new_lt = re.sub(re.escape(match), "", lt, flags=re.I).strip()
        logger.info("TVExtractor: matched %s on left", match)
        return match, rt, new_lt, 'TVExtractor(SxxEyy_left)'
    m = RE_SEASON_EP_ALT.search(lt)
    if m:
        match = m.group(0)
        new_lt = re.sub(re.escape(match), "", lt).strip()
        logger.info("TVExtractor: matched alt %s on left", match)
        return match, rt, new_lt, 'TVExtractor(alt_left)'

    logger.debug("TVExtractor: no match")
    return None, rt, lt, None

def extract_movie_year(right_text: str, left_text: str) -> Tuple[Optional[str], str, str, Optional[str]]:
    logger.debug("MovieYearExtractor: right=%s left=%s", right_text, left_text)
    rt = right_text or ""
    lt = left_text or ""
    m = RE_YEAR.search(rt)
    if m:
        y = m.group(0)
        new_rt = re.sub(re.escape(y), "", rt).strip()
        logger.info("MovieYearExtractor: matched year on right %s", y)
        return y, new_rt, lt, 'MovieYearExtractor(right)'
    m = RE_YEAR.search(lt)
    if m:
        y = m.group(0)
        new_lt = re.sub(re.escape(y), "", lt).strip()
        logger.info("MovieYearExtractor: matched year on left %s", y)
        return y, rt, new_lt, 'MovieYearExtractor(left)'
    logger.debug("MovieYearExtractor: no match")
    return None, rt, lt, None

# -------------------- Main Pipeline --------------------

def extractor_pipeline(filename: str) -> ParseResult:
    logger.info("\n[Pipeline] START parsing: %s", filename)

    res, left, right = extract_resolution(filename)
    result = ParseResult(original=filename, resolution=res, res_left=left, res_right=right)

    # normalize processing variables
    right_text = right
    left_text = left

    # 1) Release group detection (prefer right side groups)
    group, left_text, right_text, extractor_name = extract_release_group(left_text, right_text)
    if group:
        result.anime_group = group
        result.notes.append(f"{extractor_name}: matched group '{group}'")
        # if group matches known anime groups, set is_anime candidate
        if any(g.lower().replace(' ', '') in group.lower().replace(' ', '') for g in KNOWN_ANIME_RELEASE_GROUPS):
            result.is_anime = True

    # 2) Priority parsing on right->left: TV SxxEyy (highest), then anime ranges, then anime episodes
    # TV extractor
    tv_match, right_text, left_text, tv_extractor = extract_tv_show(right_text, left_text)
    if tv_match:
        result.is_tv = True
        result.tv_match = tv_match
        result.notes.append(f"{tv_extractor}: matched '{tv_match}'")
        logger.info("Pipeline: TV confirmed (%s)", tv_match)

    # If TV not found, try anime episode/range
    if not result.is_tv:
        # anime range (001-500) or similar
        ep_range = None
        m_range = RE_PAREN_RANGE.search(right_text or left_text or "")
        if m_range:
            ep_range = m_range.group(0)
            # remove the range
            right_text = (right_text or "").replace(ep_range, "").strip()
            result.is_anime = True
            result.anime_episode = ep_range
            result.notes.append(f"AnimeExtractor(range): matched '{ep_range}'")
            logger.info("Pipeline: Anime range confirmed %s", ep_range)

        # strict anime episode extractor (ep02, ep.02, Episode 02)
        if not ep_range:
            ep, right_text, left_text, ep_extractor = extract_anime_episode(right_text, left_text)
            if ep:
                result.is_anime = True
                result.anime_episode = ep
                result.notes.append(f"{ep_extractor}: matched '{ep}'")
                logger.info("Pipeline: Anime episode confirmed %s", ep)

    # 3) If neither anime nor tv confirmed yet, try movie year
    if not (result.is_anime or result.is_tv):
        y, right_text, left_text, year_extractor = extract_movie_year(right_text, left_text)
        if y:
            result.is_movie = True
            result.movie_year = y
            result.notes.append(f"{year_extractor}: matched '{y}'")
            logger.info("Pipeline: Movie year found %s", y)

    # 4) Final title cleanup: prefer left_text for title
    candidate_title = _clean_separators(left_text or "")
    # strip leftover punctuation
    candidate_title = candidate_title.strip('-_ .[]()')

    # if left is empty, try using cleaned right_text as fall back
    if not candidate_title and right_text:
        candidate_title = _clean_separators(right_text)

    # Remove known junk tokens from title words
    title_words = [w for w in candidate_title.split() if w.lower() not in JUNK_WORDS]
    candidate_title = " ".join(title_words).strip()

    result.possible_title = candidate_title

    # Add a final note if nothing was found
    if not (result.is_anime or result.is_tv or result.is_movie):
        result.notes.append("Pipeline: classified as Misc (no specific markers found)")

    logger.info("[Pipeline] DONE: title='%s' anime=%s tv=%s movie=%s notes=%s",
                result.possible_title, result.is_anime, result.is_tv, result.is_movie, result.notes)

    return result

# -------------------- Test harness --------------------

if __name__ == '__main__':
    # set logger to debug for full trace during tests
    logger.setLevel(logging.DEBUG)

    tests = [
        "www.SceneTime.com - Taken 3 2014 1080p DSNP WEB-DL DDP 5 1 H 264-PiRaTeS",
        "[SubsPlease] Tearmoon Teikoku Monogatari - 01 (1080p) [15ADAE00].mkv",
        "[SubsPlease] Fairy Tail - 100 Years Quest - 05 (1080p) [1107F3A9].mkv",
        "[Erai-raws] Tearmoon Teikoku Monogatari - 01 [1080p][ENG][POR-BR].mkv",
        "Hunter x Hunter (2011) - 01 [1080p][ENG][FRE]",
        "Naruto Shippuden (001-500) [Complete Series + Movies]",
        "[Erai-raws] Sword Art Online - 10 [720p][Multiple Subtitle].mkv",
        "[Exiled-Destiny]_Tokyo_Underground_Ep02v2_(41858470).mkv",
        "Some.Movie.2023.1920x1080.WEB.mkv",
    ]

    for t in tests:
        p = extractor_pipeline(t)
        print('\n' + '=' * 80)
        print(f"INPUT: {t}")
        print('-' * 80)
        d = p.to_dict()
        print(f"Title: {d['possible_title']}")
        print(f"Resolution: {d['resolution']}")
        print(f"Is Anime: {d['is_anime']}, Anime group: {d['anime_group']}, Anime ep: {d['anime_episode']}")
        print(f"Is TV: {d['is_tv']}, TV match: {d['tv_match']}")
        print(f"Is Movie: {d['is_movie']}, Movie Year: {d['movie_year']}")
        print(f"Left after split: {d['res_left']}")
        print(f"Right after split: {d['res_right']}")
        if d['notes']:
            print('Notes: ' + '; '.join(d['notes']))
        print('=' * 80)
