from pathlib import Path
import sys
import re
import logging
from datetime import datetime

# Get the script's path as a Path object
script_path = Path(__file__).resolve()

# Get the directory and script name
script_dir = script_path.parent
script_name = script_path.stem

# Generate the output filename with a timestamp
now = datetime.now()
output_filename = script_dir / f"{script_name}_output_{now.strftime('%m%d_%H%M')}.txt"

# Configure logging to write directly to the output file
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    filename=output_filename,
    filemode='w'
)

# A conservative list of typical release-group-like bracket tokens
KNOWN_ANIME_RELEASE_GROUPS = [
    r"SubsPlease", r"Erai-raws", r"Exiled-Destiny",
    r"HorribleSubs", r"CR", r"Funimation",
    r"ANiDL", r"UTW", r"Nekomoe kissaten",
]

# Precompiled regexes with refined logic
RE_WEBSITE_CLEANER = re.compile(r"\b(?:www\.[^\s]+\.com|www\.com|www\.[^\s]+)\b", flags=re.I)
RE_RESOLUTION = re.compile(r"\b(\d{3,4}x\d{3,4}|[4-8]K|720p|1080p|2160p)", flags=re.I)
RE_MEDIA_SOURCE = re.compile(r"\b(?:WEB-DL|BluRay|HDTV|WEBRip|AMZN)", flags=re.I)
RE_SEASON_EP = re.compile(r"\bS(\d{1,2})E(\d{1,3})", flags=re.I)
RE_ANIME_EPISODE = re.compile(r"\b(?:ep\.?|episode)(?:[.\s]*)(\d{2,3})", flags=re.I)
RE_ANIME_EPISODE_4DIGIT = re.compile(r"(?:- (\d{4}) -|ep\.?(\d{4}))", flags=re.I)
RE_ANIME_EPISODE_SINGLE = re.compile(r" - (\d{1,3})(?=\(|\)|\[|\]|\.mkv|\.mp4|\.avi|\s|$)", flags=re.I)
RE_ANIME_RANGE = re.compile(r"\((\d{3,4}-\d{3,4})\)")
RE_SEASON_ONLY = re.compile(r"\bS(\d{1,2})", flags=re.I)
RE_YEAR = re.compile(r"\b(19\d{2}|20\d{2})")
RE_BRACKET_GROUP = re.compile(r"\[([^\]]+)\]")
RE_KNOWN_ANIME_GROUP_PATTERNS = [re.compile(pattern, flags=re.I) for pattern in KNOWN_ANIME_RELEASE_GROUPS]

# The prioritized list of extractors - year should be last
CLUE_PATTERNS = [
    ('resolution', RE_RESOLUTION),
    ('media_source', RE_MEDIA_SOURCE),
    ('season_ep', RE_SEASON_EP),
    ('anime_range', RE_ANIME_RANGE),
    ('anime_episode', RE_ANIME_EPISODE),
    ('anime_episode_4digit', RE_ANIME_EPISODE_4DIGIT),
    ('season_only', RE_SEASON_ONLY),
    ('anime_episode_single', RE_ANIME_EPISODE_SINGLE),
    ('year', RE_YEAR),  # Year should be last in the order
]

def smart_clean_title(title):
    """
    Smart cleaning of titles that preserves punctuation in acronyms like S.W.A.T.
    Only removes/replaces punctuation when adjacent to strings longer than 1 character.
    
    Args:
        title (str): The title to clean
        
    Returns:
        str: The cleaned title
    """
    # First, handle brackets and parentheses (always remove these)
    title = re.sub(r'\[[^\]]+\]|\([^)]+\)', ' ', title)
    
    # Split the title into tokens to process each part
    result = []
    i = 0
    while i < len(title):
        char = title[i]
        
        if char in '._-':
            # Look at characters before and after
            before_len = 0
            after_len = 0
            
            # Check length of alphanumeric string before
            j = i - 1
            while j >= 0 and title[j].isalnum():
                before_len += 1
                j -= 1
            
            # Check length of alphanumeric string after
            j = i + 1
            while j < len(title) and title[j].isalnum():
                after_len += 1
                j += 1
            
            # Only replace if either side has more than 1 character
            if before_len > 1 or after_len > 1:
                result.append(' ')
            else:
                result.append(char)
        else:
            result.append(char)
        
        i += 1
    
    # Join and clean up multiple spaces
    cleaned = ''.join(result)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    
    return cleaned

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
        'folder_season': None,
        'folder_extra_bits': ""
    }
    
    working_string = filename
    
    if debug_output:
        logging.info(f"Initial string: '{filename}'")
        logging.info("\n--- Right-to-Left Parsing and Extraction ---")
    
    # Run a continuous loop until no more clues are found
    while True:
        clue_found_in_pass = False
        
        # Check for website first, as it's always at the beginning
        match = RE_WEBSITE_CLEANER.search(working_string)
        if match:
            matched_text = match.group(0)
            result['folder_extra_bits'] += f" {matched_text}"
            working_string = working_string.replace(matched_text, '').strip()
            clue_found_in_pass = True
            if debug_output:
                logging.info(f"Extractor 'website_cleaner' matched '{matched_text}'")
                logging.info(f"  left_split: '{working_string}'")
            continue

        # Prioritize bracket groups as they are strong indicators
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
                    working_string = working_string.replace(full_match, '').strip()
                    clue_found_in_pass = True
                    if debug_output:
                        logging.info(f"Extractor 'anime_group' matched '{full_match}'")
                        logging.info(f"  left_split: '{working_string}'")
                    break
            if clue_found_in_pass:
                continue

        # Iterate through other patterns, from right-to-left
        for key, pattern in CLUE_PATTERNS:
            if debug_output:
                logging.info(f"Checking extractor: '{key}'")
            match = list(pattern.finditer(working_string))
            if match:
                if debug_output:
                    logging.info(f"Extractor '{key}' found matches: {[m.group(0) for m in match]}")
                match = match[-1]
                matched_text = match.group(0)
                
                is_year = re.match(RE_YEAR, matched_text)
                is_episode = re.match(RE_ANIME_EPISODE, matched_text)
                
                # Contextual checks to avoid year/episode conflicts
                # Allow anime episodes even if year is found, but not vice versa
                if is_year and result['folder_anime_episode'] is not None:
                    continue
                    
                # Limit anime episode detection to only run once if anime is already detected
                if key.startswith('anime_episode') and result['folder_anime_episode'] is not None:
                    continue
                    
                # Extract anything to the right of the match and add to folder_extra_bits
                right_text = working_string[match.end():].strip()
                if right_text:
                    result['folder_extra_bits'] += f" {right_text}"
                
                if key == 'resolution':
                    result['folder_resolution'] = matched_text
                elif key == 'year':
                    result['folder_year'] = matched_text
                elif key in ['season_ep', 'anime_range', 'anime_episode', 'anime_episode_4digit', 'season_only']:
                    result['folder_media_type'] = 'tv_show'
                    if key.startswith('anime_'):
                        result['folder_is_anime'] = True
                    if key == 'season_ep':
                        result['folder_season'] = match.group(1)
                        result['folder_anime_episode'] = match.group(2)
                    elif key == 'anime_range':
                        result['folder_anime_episode'] = match.group(1)
                    elif key == 'anime_episode_4digit':
                        # Handle both patterns: - XXXX - and ep.XXXX
                        if match.group(1):  # - XXXX - pattern
                            result['folder_anime_episode'] = match.group(1)
                        else:  # ep.XXXX pattern
                            result['folder_anime_episode'] = match.group(2)
                    elif key == 'season_only':
                        if result.get('folder_season') is None:
                            result['folder_season'] = []
                        result['folder_season'].append(match.group(1))
                    else:
                        result['folder_anime_episode'] = match.group(1)
                else:
                    # Only add non-field-specific clues to extra_bits
                    result['folder_extra_bits'] += f" {matched_text}"
                working_string = working_string[:match.start()].strip()
                clue_found_in_pass = True
                
                if debug_output:
                    logging.info(f"Extractor '{key}' matched '{matched_text}'")
                    logging.info(f"  right_text: '{right_text}'")
                    logging.info(f"  left_split: '{working_string}'")
                break
        
        if not clue_found_in_pass:
            break

    # Final String Assembly and Cleanup
    if debug_output:
        logging.info("\n--- Final Assembly ---")

    # Use smart cleaning for the title
    result['folder_title'] = smart_clean_title(working_string)
    result['folder_extra_bits'] = re.sub(r'[._-]', ' ', result['folder_extra_bits']).strip()
    
    # Format folder_season if it's a list or string
    if result['folder_season']:
        if isinstance(result['folder_season'], list):
            seasons = sorted(result['folder_season'], key=int)
            result['folder_season'] = ','.join(s.lstrip('0') or '0' for s in seasons)
        elif isinstance(result['folder_season'], str):
            result['folder_season'] = result['folder_season'].lstrip('0') or '0'
    
    if result['folder_media_type'] is None:
        if result['folder_year'] and not result['folder_is_anime'] and not result['folder_anime_episode']:
            result['folder_media_type'] = 'movie'
        elif result['folder_is_anime'] or result['folder_anime_episode'] or result['folder_season']:
            result['folder_media_type'] = 'tv_show'

    if debug_output:
        logging.info(f"  Final Title: '{result['folder_title']}'")
        logging.info(f"  Final Extra Bits: '{result['folder_extra_bits']}'")
        
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
        "S.W.A.T.2017.S08E05.1080p.WEB.h264-EDITH",
        "The_Walking_Dead_S11E24_1080p.mkv",
        "one.piece.S1E1093.1080p.WEB-DL",
        "Breaking.Bad.S01-S05.Complete.Series.BluRay",
        "Game.of.Thrones.S01 S08.4K.UHD.BluRay",
    ]
    
    for s in samples:
        parsed_data = parse_filename(s, debug_output=True)
        logging.info("\n--- Final Result ---")
        logging.info(f"--- Parsing: {s} ---")
        for key, value in parsed_data.items():
            logging.info(f"  {key:<20}: {value}")
        logging.info("\n" + "="*80 + "\n")

    print(f"Output saved to {output_filename}")