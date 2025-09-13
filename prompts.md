Your task is to generate a single, self-contained Python script to parse media filenames. The script must only use standard Python libraries (like re); do not use external libraries such as pandas.

The core of the script will be a parsing function that processes a filename according to a strict, prioritized pipeline.

1. Core Parsing Logic: The "First Match" Split (Right-to-Left)

The script must scan each filename for a series of "media clues." Crucially, the search for these clues must be performed from the end of the filename string, moving backwards (right-to-left). The first match found during this reverse search will trigger the split.

The search follows a strict priority order. For example, it should only search for a media source if a resolution clue is not found first (from right-to-left). When the first clue is found, the filename string must be split into: leftsplit (everything before the clue), matched (the clue itself), and rightsplit (everything after the clue).

The strict priority order for clues is:

* Resolution: Use a flexible regex pattern to find common resolutions like 1080p, 720p, 2160p, or dimensional formats like 1920x1080.

* Media Source: (e.g., WEB-DL, BluRay, HDTV).

* Season/Episode Pattern: (e.g., S01E02, s01e02).

* Anime Episode Pattern: Use a robust regex to find anime episode markers, which can have variations like ep287, ep.10, - 05, or even high numbers like ep 1080.

* Season Only Pattern: (e.g., S01, Season 1).

* Year: (e.g., 2014, 2023).

2. Anime Release Group Parsing (Directional Search)

After the primary split occurs, the script should parse for a known anime release group using a specific directional search:

* First, search the leftsplit from left-to-right.

* If not found, then search the rightsplit from right-to-left.

3. Final Output Structure

The parser must return a dictionary for each filename. This dictionary must always contain all of the following keys, with None or a default value (e.g., False for booleans) if the corresponding information was not found.

* folder_path: The original input filename string.

* folder_title: The cleaned title, derived primarily from the leftsplit.

* folder_media_type: Set to 'TV' or 'Movie'. This should be determined based on the patterns found (e.g., S/E patterns imply 'TV', a year often implies 'Movie').

* folder_is_anime: A separate boolean (True/False) indicating if anime-specific patterns were detected.

* folder_year: The 4-digit year, if found.

* folder_resolution: The resolution string, if found.

* folder_anime_group: The anime release group, if found.

* folder_anime_episode: The anime episode number, if found.

* folder_extra_bits: A string containing all remaining, unparsed parts of the filename to ensure no data is lost.

4. Required Code Components

The script must incorporate and use the following components. You should create more robust regex patterns based on the logic described above.

import re

import logging



# A conservative list of typical release-group-like bracket tokens

KNOWN_ANIME_RELEASE_GROUPS = [

r"SubsPlease", r"Erai-raws", r"Exiled-Destiny",

r"HorribleSubs", r"CR", r"Funimation",

r"ANiDL", r"UTW", r"Nekomoe kissaten",

]



# Precompiled regexes (expand and improve these as needed)

RE_RESOLUTION = re.compile(r"\b(\d{3,4}x\d{3,4}|720p|1080p|2160p)\b", flags=re.I)

RE_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")

RE_SEASON_EP = re.compile(r"\bS(\d{1,2})E(\d{1,3})\b", flags=re.I)

# A more robust regex for various anime episode formats

RE_ANIME_EPISODE = re.compile(r"\b(?:ep\.?|episode)?\s*(\d{2,4})\b", flags=re.I)

RE_BRACKET_GROUP = re.compile(r"\[([^\]]+)\]")

# ... add other necessary patterns for media source, season only, etc.



5. Test Harness

The script must be executable. Include a if __name__ == '__main__': block that runs the parser on the following list of test cases and prints the resulting dictionary for each one.

# Test cases

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