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

# Precompiled regexes
RE_WEBSITE_CLEANER = re.compile(r"\b(?:www\.[^\s]+\.com|www\.com|www\.[^\s]+)\b", flags=re.I)
RE_RESOLUTION = re.compile(r"\b(\d{3,4}x\d{3,4}|[4-8]K|720p|1080p|2160p)\b", flags=re.I)
RE_MEDIA_SOURCE = re.compile(r"\b(?:WEB-DL|BluRay|HDTV|WEBRip|AMZN)\b", flags=re.I)
RE_SEASON_EP = re.compile(r"\bS(\d{1,2})E(\d{1,3})\b", flags=re.I)
RE_ANIME_EPISODE = re.compile(r"\b(?:ep\.?|episode)?\s*(\d{2,4})\b", flags=re.I)
RE_ANIME_EPISODE_SINGLE = re.compile(r" - (\d{1,2})\b", flags=re.I)
RE_ANIME_RANGE = re.compile(r"\((\d{3,4}-\d{3,4})\)")
RE_SEASON_ONLY = re.compile(r"\bS(\d{1,2})\b", flags=re.I)
RE_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
RE_BRACKET_GROUP = re.compile(r"\[([^\]]+)\]")
RE_KNOWN_ANIME_GROUP_PATTERNS = [re.compile(pattern, flags=re.I) for pattern in KNOWN_ANIME_RELEASE_GROUPS]

# A prioritized list of regexes for a single, right-to-left scan
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
    Parses a media filename using a strict right-to-left, single-pass pipeline.
    
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
        'folder_extra_bits': None
    }
    
    working_string = filename
    right_split_parts = []
    
    if debug_output:
        print(f"Initial string: '{filename}'")
        print("\n--- Right-to-Left Parsing and Extraction ---")
    
    # Process the website first, as it's always at the beginning
    website_match = RE_WEBSITE_CLEANER.search(working_string)
    if website_match:
        website_text = website_match.group(0)
        working_string = working_string.replace(website_text, '').strip()
        right_split_parts.append(website_text)
        if debug_output:
            print(f"Extractor 'website_cleaner' matched '{website_text}'")
            print(f"  left_split: '{working_string}'")

    # Main Parsing Loop: Iterate through patterns and extract from right-to-left
    # The left_split becomes the new working string after each successful match.
    for key, pattern in CLUE_PATTERNS:
        match = list(pattern.finditer(working_string))
        if match:
            match = match[-1] # Find the right-most occurrence
            matched_text = match.group(0)
            
            # Contextual checks
            if key == 'year' and result.get('folder_anime_episode') is not None:
                continue
            if key in ['anime_episode', 'anime_episode_single'] and result.get('folder_year') is not None:
                continue

            # This is the key change: create the new left_split by slicing before the match
            new_left_split = working_string[:match.start()].strip()
            
            # This is also a key change: grab the right split part that will be used for extra bits
            right_split_part = working_string[match.start():].strip()
            right_split_parts.append(right_split_part)

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
            
            # The working string for the next iteration is the new left_split
            working_string = new_left_split
            
            if debug_output:
                print(f"Extractor '{key}' matched '{matched_text}'")
                print(f"  left_split: '{working_string}'")

    # Final extraction for anime group, which is often at the very beginning
    bracket_matches = list(RE_BRACKET_GROUP.finditer(working_string))
    if bracket_matches:
        for match in bracket_matches:
            group_content = match.group(1)
            for group_pattern in RE_KNOWN_ANIME_GROUP_PATTERNS:
                if group_pattern.search(group_content):
                    result['folder_anime_group'] = group_content
                    result['folder_is_anime'] = True
                    right_split_parts.append(match.group(0))
                    working_string = working_string.replace(match.group(0), '').strip()
                    if debug_output:
                        print(f"Extractor 'anime_group' matched '{group_content}'")
                        print(f"  left_split: '{working_string}'")
                    break

    # 2. Final String Assembly and Cleanup
    if debug_output:
        print("\n--- Final Assembly ---")

    # The remaining working_string is the title
    result['folder_title'] = re.sub(r'[._-]', ' ', working_string).strip()
    
    # Create extra bits from everything that was not the title
    extra_bits_temp = " ".join(right_split_parts)
    result['folder_extra_bits'] = re.sub(r'[._-]', ' ', extra_bits_temp).strip()
    
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