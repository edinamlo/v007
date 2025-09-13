import re
import logging
from datetime import datetime
import sys
import os

# Set up logging for debugging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# A conservative list of typical release-group-like bracket tokens
KNOWN_ANIME_RELEASE_GROUPS = [
    r"SubsPlease", r"Erai-raws", r"Exiled-Destiny",
    r"HorribleSubs", r"CR", r"Funimation",
    r"ANiDL", r"UTW", r"Nekomoe kissaten",
]

# Precompiled regexes with refined logic
RE_WEBSITE_CLEANER = re.compile(r"\b(?:www\.[^\s]+\.com|www\.com|www\.[^\s]+)\b", flags=re.I)
RE_RESOLUTION = re.compile(r"\b(\d{3,4}x\d{3,4}|[4-8]K|720p|1080p|2160p)\b", flags=re.I)
RE_MEDIA_SOURCE = re.compile(r"\b(?:WEB-DL|BluRay|HDTV|WEBRip|AMZN)\b", flags=re.I)
RE_SEASON_EP = re.compile(r"\bS(\d{1,2})E(\d{1,3})\b", flags=re.I)
# Anime episode regex now requires a clear prefix for four-digit numbers
RE_ANIME_EPISODE = re.compile(r"\b(?:ep\.?|episode)?\s*(\d{2,4})\b", flags=re.I)
RE_ANIME_EPISODE_SINGLE = re.compile(r" - (\d{1,2})\b", flags=re.I)
RE_ANIME_RANGE = re.compile(r"\((\d{3,4}-\d{3,4})\)")
RE_SEASON_ONLY = re.compile(r"\bS(\d{1,2})\b", flags=re.I)
RE_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
RE_BRACKET_GROUP = re.compile(r"\[([^\]]+)\]")
RE_KNOWN_ANIME_GROUP_PATTERNS = [re.compile(pattern, flags=re.I) for pattern in KNOWN_ANIME_RELEASE_GROUPS]

# The prioritized list of extractors
CLUE_PATTERNS = [
    ('resolution', RE_RESOLUTION),
    ('media_source', RE_MEDIA_SOURCE),
    ('season_ep', RE_SEASON_EP),
    ('anime_range', RE_ANIME_RANGE),
    ('anime_episode', RE_ANIME_EPISODE),
    ('season_only', RE_SEASON_ONLY),
    ('year', RE_YEAR),
    ('anime_episode_single', RE_ANIME_EPISODE_SINGLE),
]

def parse_filename(filename, debug_output=False):
    """
    Parses a media filename using a single-pass, right-to-left pipeline.
    
    Args:
        filename (str): The name of the file to parse.
        debug_output (bool): If True, prints intermediate parsing steps.
        
    Returns:
        dict: A dictionary containing the parsed metadata.
    """
    
    result = {
        'folder_path': filename,
        'folder_title': None,
        'folder_media_type': None,
        'folder_is_anime': False,
        'folder_year': None,
        'folder_resolution': None,
        'folder_anime_group': None,
        'folder_anime_episode': None,
        'folder_extra_bits': "" # Initialize as empty string
    }
    
    working_string = filename
    
    if debug_output:
        print(f"Initial string: '{filename}'")
        print("\n--- Right-to-Left Parsing and Extraction ---")
    
    # 1. Right-to-Left Scan and Extraction
    
    # Use a flag to ensure we only grab one of each type of clue per pass
    clues_found = {clue: False for clue, _ in CLUE_PATTERNS}
    
    # Run a continuous loop until no more clues are found
    while True:
        clue_found_in_pass = False
        
        # Check for website first, as it's always at the beginning
        if not clues_found.get('website_cleaner', False):
            match = RE_WEBSITE_CLEANER.search(working_string)
            if match:
                matched_text = match.group(0)
                result['folder_extra_bits'] += f" {matched_text}"
                working_string = working_string.replace(matched_text, '').strip()
                clues_found['website_cleaner'] = True
                clue_found_in_pass = True
                if debug_output:
                    print(f"Extractor 'website_cleaner' matched '{matched_text}'")
                    print(f"  left_split: '{working_string}'")

        # Prioritize bracket groups as they are strong indicators
        if not clues_found.get('anime_group', False):
            match = list(RE_BRACKET_GROUP.finditer(working_string))
            if match:
                match = match[-1]
                group_content = match.group(1)
                full_match = match.group(0)
                for group_pattern in RE_KNOWN_ANIME_GROUP_PATTERNS:
                    if group_pattern.search(group_content):
                        result['folder_anime_group'] = group_content
                        result['folder_is_anime'] = True
                        result['folder_extra_bits'] += f" {full_match}"
                        working_string = working_string[:match.start()].strip()
                        clues_found['anime_group'] = True
                        clue_found_in_pass = True
                        if debug_output:
                            print(f"Extractor 'anime_group' matched '{full_match}'")
                            print(f"  left_split: '{working_string}'")
                        break

        # Iterate through other patterns, from right-to-left
        for key, pattern in CLUE_PATTERNS:
            if not clues_found[key]:
                match = list(pattern.finditer(working_string))
                if match:
                    match = match[-1]
                    matched_text = match.group(0)
                    
                    # Contextual checks for year/episode conflict
                    is_year = re.match(RE_YEAR, matched_text)
                    is_episode = re.match(RE_ANIME_EPISODE, matched_text)
                    if is_year and result['folder_anime_episode'] is not None:
                        continue
                    if is_episode and result['folder_year'] is not None:
                        continue
                        
                    # Store the data
                    if key == 'resolution':
                        result['folder_resolution'] = matched_text
                    elif key == 'year':
                        result['folder_year'] = matched_text
                    elif key in ['season_ep', 'anime_range', 'anime_episode', 'anime_episode_single', 'season_only']:
                        result['folder_media_type'] = 'TV'
                        result['folder_is_anime'] = True
                        if key == 'season_ep':
                            result['folder_anime_episode'] = f"S{match.group(1)}E{match.group(2)}"
                        elif key == 'anime_range':
                            result['folder_anime_episode'] = match.group(1)
                        else:
                            result['folder_anime_episode'] = match.group(1)

                    result['folder_extra_bits'] += f" {matched_text}"
                    working_string = working_string[:match.start()].strip()
                    clues_found[key] = True
                    clue_found_in_pass = True
                    
                    if debug_output:
                        print(f"Extractor '{key}' matched '{matched_text}'")
                        print(f"  left_split: '{working_string}'")

        if not clue_found_in_pass:
            break

    # 2. Final String Assembly and Cleanup
    if debug_output:
        print("\n--- Final Assembly ---")

    # The remaining working_string is the title
    result['folder_title'] = re.sub(r'\[[^\]]+\]|\([^)]+\)|\s{2,}', ' ', working_string).strip()
    result['folder_extra_bits'] = re.sub(r'[._-]', ' ', result['folder_extra_bits']).strip()
    
    # Final media type heuristic
    if result['folder_media_type'] is None:
        if result['folder_year'] and not result['folder_is_anime'] and not result['folder_anime_episode']:
            result['folder_media_type'] = 'Movie'
        elif result['folder_is_anime'] or result['folder_anime_episode']:
            result['folder_media_type'] = 'TV'

    if debug_output:
        print(f"  Final Title: '{result['folder_title']}'")
        print(f"  Final Extra Bits: '{result['folder_extra_bits']}'")
        
    return result

if __name__ == '__main__':
    samples = [
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
    
    now = datetime.now()
    output_filename = os.path.join(os.getcwd(), f"output_{now.strftime('%m%d_%H%M')}.txt")
    
    original_stdout = sys.stdout
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        sys.stdout = f
        for s in samples:
            parsed_data = parse_filename(s, debug_output=True)
            print("\n--- Final Result ---")
            print(f"--- Parsing: {s} ---")
            for key, value in parsed_data.items():
                print(f"  {key:<20}: {value}")
            print("\n" + "="*80 + "\n")
        sys.stdout = original_stdout
    
    print(f"Output saved to {output_filename}")

    from pathlib import Path
import sys
from datetime import datetime

# Get the script's path as a Path object
script_path = Path(__file__).resolve()

# Get the directory and script name
script_dir = script_path.parent
script_name = script_path.stem

# Generate the output filename
now = datetime.now()
output_filename = script_dir / f"{script_name}_output_{now.strftime('%m%d_%H%M')}.txt"

# Redirect stdout to the file
original_stdout = sys.stdout
with open(output_filename, 'w', encoding='utf-8') as f:
    sys.stdout = f
    
    # Your code that generates output
    samples = ["sample1", "sample2"]
    def parse_filename(s, debug_output=False):
        return {"name": s, "status": "processed"}

    for s in samples:
        parsed_data = parse_filename(s, debug_output=True)
        print("\n--- Final Result ---")
        print(f"--- Parsing: {s} ---")
        for key, value in parsed_data.items():
            print(f" {key:<20}: {value}")
        print("\n" + "="*80 + "\n")

# Restore original stdout
sys.stdout = original_stdout

print(f"Output saved to {output_filename}")
