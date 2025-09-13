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

# Precompiled regexes (expand and improve these as needed)
RE_WEBSITE_CLEANER = re.compile(r"\b(?:www\.[^\s]+\.com|www\.com|www\.[^\s]+)\b", flags=re.I)
RE_RESOLUTION = re.compile(r"\b(\d{3,4}x\d{3,4}|[4-8]K|720p|1080p|2160p)\b", flags=re.I)
RE_MEDIA_SOURCE = re.compile(r"\b(?:WEB-DL|BluRay|HDTV|WEBRip|AMZN)\b", flags=re.I)
RE_SEASON_EP = re.compile(r"\bS(\d{1,2})E(\d{1,3})\b", flags=re.I)
RE_ANIME_EPISODE = re.compile(r"\b(?:ep\.?|episode)?\s*(\d{1,4})\b", flags=re.I)
RE_ANIME_RANGE = re.compile(r"\((\d{3,4}-\d{3,4})\)")
RE_SEASON_ONLY = re.compile(r"\bS(\d{1,2})\b", flags=re.I)
RE_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
RE_BRACKET_GROUP = re.compile(r"\[([^\]]+)\]")
RE_KNOWN_ANIME_GROUP_PATTERNS = [re.compile(pattern, flags=re.I) for pattern in KNOWN_ANIME_RELEASE_GROUPS]

# Define a prioritized list of regexes for right-to-left scanning
CLUE_PATTERNS = [
    ('resolution', RE_RESOLUTION),
    ('media_source', RE_MEDIA_SOURCE),
    ('season_ep', RE_SEASON_EP),
    ('anime_range', RE_ANIME_RANGE),
    ('anime_episode', RE_ANIME_EPISODE),
    ('season_only', RE_SEASON_ONLY),
    ('year', RE_YEAR),
]

def parse_filename(filename, debug_output=False):
    """
    Parses a media filename based on a prioritized, multi-pass pipeline.
    
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
    
    # Track the portions of the string that are not part of the core title
    extracted_parts = []
    
    # 1. Primary Right-to-Left Split
    leftsplit = filename
    rightsplit = ""
    
    if debug_output:
        print(f"Initial string: '{filename}'")
        print("--- Primary Right-to-Left Split ---")
    
    for key, pattern in CLUE_PATTERNS:
        match = list(pattern.finditer(filename))
        if match:
            match = match[-1]  # Right-most match
            matched_text = match.group(0)
            extracted_parts.append(matched_text)
            
            leftsplit = filename[:match.start()].strip()
            rightsplit = filename[match.end():].strip()

            if key == 'resolution':
                result['folder_resolution'] = matched_text
            elif key == 'year':
                result['folder_year'] = matched_text
            elif key == 'season_ep':
                result['folder_media_type'] = 'TV'
                result['folder_is_anime'] = True
                result['folder_anime_episode'] = f"S{match.group(1)}E{match.group(2)}"
            elif key == 'anime_episode':
                result['folder_is_anime'] = True
                result['folder_media_type'] = 'TV'
                result['folder_anime_episode'] = match.group(1)
            elif key == 'anime_range':
                result['folder_is_anime'] = True
                result['folder_media_type'] = 'TV'
                result['folder_anime_episode'] = match.group(1)
            elif key == 'season_only':
                result['folder_is_anime'] = True
                result['folder_media_type'] = 'TV'
            
            if debug_output:
                print(f"Extractor '{key}' matched '{matched_text}'")
                print(f"  left_split:  '{leftsplit}'")
                print(f"  right_split: '{rightsplit}'")
                
            break
    
    if not extracted_parts:
        leftsplit = filename

    # 2. Iterative leftsplit Extraction and Cleanup
    working_title_string = leftsplit
    
    if debug_output:
        print("\n--- Iterative left_split Cleanup ---")
    
    # Website cleaner
    website_match = RE_WEBSITE_CLEANER.search(working_title_string)
    if website_match:
        website_text = website_match.group(0)
        working_title_string = working_title_string.replace(website_text, '').strip()
        extracted_parts.append(website_text)
        if debug_output:
            print(f"Extractor 'website_cleaner' matched '{website_text}'")
            print(f"  working_title_string: '{working_title_string}'")
    
    # Remaining clue extraction from leftsplit
    for key, pattern in CLUE_PATTERNS:
        if result.get(f'folder_{key}') is None:
            match = pattern.search(working_title_string)
            if match:
                matched_text = match.group(0)
                extracted_parts.append(matched_text)
                
                if key == 'year':
                    result['folder_year'] = matched_text
                elif key == 'season_ep':
                    result['folder_media_type'] = 'TV'
                    result['folder_is_anime'] = True
                    result['folder_anime_episode'] = f"S{match.group(1)}E{match.group(2)}"
                elif key == 'anime_episode':
                    result['folder_is_anime'] = True
                    result['folder_media_type'] = 'TV'
                    result['folder_anime_episode'] = match.group(1)
                elif key == 'anime_range':
                    result['folder_is_anime'] = True
                    result['folder_media_type'] = 'TV'
                    result['folder_anime_episode'] = match.group(1)
                elif key == 'season_only':
                    result['folder_is_anime'] = True
                    result['folder_media_type'] = 'TV'
                
                working_title_string = working_title_string.replace(matched_text, '').strip()
                
                if debug_output:
                    print(f"Extractor '{key}' matched '{matched_text}'")
                    print(f"  working_title_string: '{working_title_string}'")

    # 3. Anime Group Parsing (Bidirectional Search)
    anime_group_found = None
    
    if debug_output:
        print("\n--- Anime Group Search ---")
    
    bracket_matches_left = RE_BRACKET_GROUP.findall(working_title_string)
    for group_name in bracket_matches_left:
        for group_pattern in RE_KNOWN_ANIME_GROUP_PATTERNS:
            if group_pattern.search(group_name):
                anime_group_found = group_name
                break
        if anime_group_found:
            break
            
    if not anime_group_found:
        bracket_matches_right = RE_BRACKET_GROUP.findall(rightsplit)
        for group_name in reversed(bracket_matches_right):
            for group_pattern in RE_KNOWN_ANIME_GROUP_PATTERNS:
                if group_pattern.search(group_name):
                    anime_group_found = group_name
                    break
            if anime_group_found:
                break
    
    if anime_group_found:
        result['folder_anime_group'] = anime_group_found
        result['folder_is_anime'] = True
        extracted_parts.append(f"[{anime_group_found}]")
        if debug_output:
            print(f"Extractor 'anime_group' matched '{anime_group_found}'")
            print(f"  Final left_split for title: '{working_title_string}'")

    # 4. Final String Assembly
    if debug_output:
        print("\n--- Final Assembly ---")
    
    final_title = re.sub(r'\[[^\]]+\]|\([^)]+\)', '', working_title_string)
    result['folder_title'] = re.sub(r'[._-]', ' ', final_title).strip()
    
    extra_bits_temp = filename
    for bit in extracted_parts:
        extra_bits_temp = extra_bits_temp.replace(str(bit), '').strip()
    
    extra_bits_temp = extra_bits_temp.replace(result['folder_title'], '').strip()
    
    extra_bits_temp = re.sub(r'\[\s*\]|\(|\)', '', extra_bits_temp)
    extra_bits_temp = re.sub(r'[._-]', ' ', extra_bits_temp)
    extra_bits_temp = re.sub(r'\s{2,}', ' ', extra_bits_temp).strip()
    result['folder_extra_bits'] = extra_bits_temp
    
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
            print("\n" + "="*80 + "\n") # Separator for clarity
        sys.stdout = original_stdout
    
    print(f"Output saved to {output_filename}")