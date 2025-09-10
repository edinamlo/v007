import re
from dataclasses import dataclass, field
from typing import Optional, List, Set

# --- Configuration (Simulating your known_clues.json) ---
KNOWN_ANIME_RELEASE_GROUPS: Set[str] = {
    "HorribleSubs", "Erai-raws", "SubsPlease", "EMBER",
    "Judas", "Cleo", "EMBE", "ToonsHub", "NC-Raws", "Seed-Raws", "SweetSub"
}

# --- Data Structure for Results ---
@dataclass
class ParseResult:
    """Stores the results of the parsing process."""
    original_filename: str
    title: str
    cleaned_filename: str = ""
    year: Optional[int] = None
    is_anime_clue_found: bool = False
    release_group: Optional[str] = None
    episode_number: Optional[int] = None
    season_number: Optional[int] = None
    removed_prefixes: List[str] = field(default_factory=list)
    removed_suffixes: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.cleaned_filename = self.title # Set cleaned_filename initially

# --- The Main Parser Function ---
def parse_filename(filename: str) -> ParseResult:
    """
    Parses a filename in a series of cleaning stages to extract title, year, and other info.
    """
    original = filename
    
    # --- Preliminary Step: Pre-normalize and remove extension ---
    clean_name, _, _ = original.rpartition('.')
    # Normalize special brackets used by some release groups
    clean_name = re.sub(r'[【】]', ' ', clean_name)

    # --- Stage 1: Handle Website Prefixes ---
    # Matches patterns like 'www.Torrenting.com -' or '[www.site.com]_'
    website_match = re.match(r'^(?:\[?www\..*?\]?_?-?\s*)+', clean_name, re.IGNORECASE)
    if website_match:
        clean_name = clean_name[website_match.end():]

    # --- Stage 2: Process Group Prefixes (e.g., [HorribleSubs]) ---
    # Loop to remove all bracketed groups from the start.
    prefixes_removed = []
    while True:
        prefix_match = re.match(r'^[\[\(](.+?)[\]\)]\s*', clean_name)
        if prefix_match:
            group_content = prefix_match.group(1)
            prefixes_removed.append(prefix_match.group(0).strip())
            # Check for anime release group clue
            if group_content in KNOWN_ANIME_RELEASE_GROUPS:
                result_kwargs = {'is_anime_clue_found': True, 'release_group': group_content}
            clean_name = clean_name[prefix_match.end():]
        else:
            break

    # --- Stage 3: Extract Year ---
    # Look for a 4-digit year (19xx or 20xx) surrounded by common delimiters.
    year_match = re.search(r'([\(\s._\[])(19\d{2}|20\d{2})([\)\s._\]])', clean_name)
    year = None
    if year_match:
        year = int(year_match.group(2))
        # Remove the year from the string to prevent it being part of the title
        clean_name = clean_name.replace(year_match.group(0), ' ')

    # --- Stage 4: Aggressively parse TV Show patterns first ---
    # This is key to separating TV shows from movies/anime.
    # Pattern looks for S01E01, 1x01, Season 1, etc.
    tv_pattern = r'(.+?)[._\s-](S(\d{1,2})E(\d{1,2})|(\d{1,2})x(\d{1,2})|S(\d{1,2})|Season\s(\d{1,2}))'
    tv_match = re.search(tv_pattern, clean_name, re.IGNORECASE)
    title = clean_name
    season, episode = None, None

    if tv_match:
        title = tv_match.group(1) # Everything before the season/episode marker
        # Extract season/episode numbers from the matched groups
        season = tv_match.group(3) or tv_match.group(8) or tv_match.group(9)
        episode = tv_match.group(4) or tv_match.group(7)
        if season: season = int(season)
        if episode: episode = int(episode)
    
    # --- Stage 5: Fallback for Anime/Movie episode numbers (if no TV pattern found) ---
    elif not tv_match:
        # Looks for a title followed by a dash or space and a 1-4 digit number at the end
        episode_match = re.search(r'^(.*?)[_.\s-]+(\d{1,4})([vV]\d)?\s*$', title)
        if episode_match and (len(episode_match.group(2)) < 4 or int(episode_match.group(2)) < 1900):
            title = episode_match.group(1)
            episode = int(episode_match.group(2))

    # --- Stage 6: Final Cleanup and Normalization ---
    # Remove everything after common quality/metadata keywords
    stop_words = ['1080p', '720p', '2160p', '4K', 'UHD', 'BDRip', 'BluRay', 'WEB-DL', 'WEBRip', 'HDTV', 'DVDRip',
                  'x264', 'x265', 'HEVC', 'REMASTERED', 'CUSTOM', 'EXTENDED', 'COMPLETE', 'INTEGRAL', 'REMUX']
    for word in stop_words:
        stop_match = re.search(r'\b' + re.escape(word) + r'\b', title, re.IGNORECASE)
        if stop_match:
            title = title[:stop_match.start()]
            
    # Handle multiple titles separated by '/'
    if '/' in title:
        # A simple heuristic: prefer the longer, likely more descriptive title
        parts = [p.strip() for p in title.split('/')]
        title = max(parts, key=len)

    # Remove trailing metadata in parentheses, e.g., (1992) if missed, or (Director's Cut)
    title = re.sub(r'\s*\([^)]*\)$', '', title)
    
    # Final character replacement and whitespace cleanup
    title = re.sub(r'[._]', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Remove leading numbers that are likely disc/episode numbers, e.g., "01. Movie Title"
    title = re.sub(r'^\d{1,3}\s', '', title)

    result = ParseResult(
        original_filename=original,
        title=title,
        year=year,
        season_number=season,
        episode_number=episode,
        removed_prefixes=prefixes_removed
    )
    # Add any detected anime clues
    if 'result_kwargs' in locals():
        result.is_anime_clue_found = result_kwargs.get('is_anime_clue_found', False)
        result.release_group = result_kwargs.get('release_group', None)

    return result

# --- Test Cases ---# --- Comprehensive Test Cases ---
test_cases = [
    ("La famille bélier", "La famille bélier"),
    ("La.famille.bélier", "La famille bélier"),
    ("Mr. Nobody", "Mr. Nobody"),
    ("doctor_who_2005.8x12.death_in_heaven.720p_hdtv_x264-fov", "doctor who 2005"),
    ("[GM-Team][国漫][太乙仙魔录 灵飞纪 第3季][Magical Legend of Rise to immortality Ⅲ][01-26][AVC][GB][1080P]", "Magical Legend of Rise to immortality Ⅲ"),
    ("【喵萌奶茶屋】★01月新番★[Rebirth][01][720p][简体][招募翻译]", "Rebirth"),
    ("【喵萌奶茶屋】★01月新番★[別對映像研出手！/Eizouken ni wa Te wo Dasu na！/映像研には手を出すな！][01][1080p][繁體]", "Eizouken ni wa Te wo Dasu na！"),
    ("[Seed-Raws] 劇場版 ペンギン・ハイウェイ Penguin Highway The Movie (BD 1280x720 AVC AACx4 [5.1+2.0+2.0+2.0]).mp4", "Penguin Highway The Movie"),
    ("[SweetSub][Mutafukaz / MFKZ][Movie][BDRip][1080P][AVC 8bit][简体内嵌]", "Mutafukaz MFKZ"),
    ("[Erai-raws] Kingdom 3rd Season - 02 [1080p].mkv", "Kingdom 3rd Season"),
    ("Голубая волна / Blue Crush (2002) DVDRip", "Blue Crush"),
    ("Жихарка (2007) DVDRip", "Жихарка"),
    ("Американские животные / American Animals (Барт Лэйтон / Bart Layton) [2018, Великобритания, США, драма, криминал, BDRip] MVO (СВ Студия)", "American Animals"),
    ("www.1TamilMV.world - Ayalaan (2024) Tamil PreDVD - 1080p - x264 - HQ Clean Aud - 2.5GB.mkv", "Ayalaan"),
    ("www.Torrenting.com   -    Anatomy Of A Fall (2023)", "Anatomy Of A Fall"),
    ("Despicable.Me.4.2024.D.TELESYNC_14OOMB.avi", "Despicable Me 4"),
    ("UFC.247.PPV.Jones.vs.Reyes.HDTV.x264-PUNCH[TGx]", "UFC 247 PPV Jones vs Reyes"),
    ("Game of Thrones - S02E07 - A Man Without Honor [2160p] [HDR] [5.1, 7.1, 5.1] [ger, eng, eng] [Vio].mkv", "Game of Thrones"),
    ("Pawn.Stars.S09E13.1080p.HEVC.x265-MeGusta", "Pawn Stars"),
    ("Jurassic.World.Dominion.CUSTOM.EXTENDED.2022.2160p.MULTi.VF2.UHD.Blu-ray.REMUX.HDR.DoVi.HEVC.DTS-X.DTS-HDHRA.7.1-MOONLY.mkv", "Jurassic World Dominion"),
    ("S.W.A.T.2017.S08E01.720p.HDTV.x264-SYNCOPY[TGx]", "S W A T"),
    ("Friends.1994.INTEGRALE.MULTI.1080p.WEB-DL.H265-FTMVHD", "Friends"),
    ("STEVE.martin.a.documentary.in.2.pieces.S01.COMPLETE.1080p.WEB.H264-SuccessfulCrab[TGx]", "STEVE martin a documentary in 2 pieces"),
    ("The.Mandalorian.S01E01.Chapter.1.1080p.Web-DL.mkv", "The Mandalorian"),
    ("9-1-1.s02", "9-1-1"),
    ("One-piece-ep.1080-v2-1080p-raws", "One-piece-ep"),
    ("Naruto Shippuden (001-500) [Complete Series + Movies] (Dual Audio)", "Naruto Shippuden"),
    ("Stranger Things S04 2160p", "Stranger Things"),
]

# Run the tests
for filename, expected_title in test_cases:
    result = parse_filename(filename)
    status = "✅" if result.title == expected_title else "❌"
    print(f"{status} | Original: '{filename}'\n      | Parsed:   '{result.title}' (Expected: '{expected_title}')")
    # Uncomment below to see full details
    # print(f"      | Details: S{result.season_number} E{result.episode_number}, Year: {result.year}\n")

