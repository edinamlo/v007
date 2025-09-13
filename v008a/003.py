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
RE_ANIME_EPISODE = re.compile(r"\b(?:ep\.?|episode)?\s*(\d{2,4})\b", flags=re.I)
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

def parse_filename(filename):
    """
    Parses a media filename based on a prioritized, right-to-left scanning pipeline.
    
    Args:
        filename (str): The name of the file to parse.
        
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

    # Pre-process: Clean up filename and store for later comparison
    clean_filename = RE_WEBSITE_CLEANER.sub('', filename)
    clean_filename = re.sub(r'[._-]', ' ', clean_filename).strip()
    
    # Track which parts of the string are "known"
    known_parts = []
    
    leftsplit = clean_filename
    rightsplit = ""
    
    # 1. Core Parsing Logic: The "First Match" Split (Right-to-Left)
    temp_filename = clean_filename
    for key, pattern in CLUE_PATTERNS:
        matches = list(pattern.finditer(temp_filename))
        if matches:
            match = matches[-1] # Find the right-most match
            matched_text = match.group(0)
            
            # Store the matched clue and its value
            known_parts.append(matched_text)
            
            # Split the string and update temp_filename for subsequent searches
            leftsplit = temp_filename[:match.start()].strip()
            rightsplit = temp_filename[match.end():].strip()
            temp_filename = leftsplit + " " + rightsplit
            
            # Populate the result dictionary
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
            elif key == 'media_source':
                # Media source is a strong indicator of a file type, but not necessarily a primary splitter
                pass
            
    # 2. Anime Release Group Parsing (Directional Search)
    anime_group_found = None
    
    # First, search leftsplit from left-to-right
    bracket_matches_left = RE_BRACKET_GROUP.findall(leftsplit)
    for group_name in bracket_matches_left:
        for group_pattern in RE_KNOWN_ANIME_GROUP_PATTERNS:
            if group_pattern.search(group_name):
                anime_group_found = group_name
                break
        if anime_group_found:
            break
            
    # If not found, search rightsplit from right-to-left
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
        
    # Add anime group to known parts for cleanup
    if result['folder_anime_group']:
        known_parts.append(f"[{result['folder_anime_group']}]")
        
    # 3. Final Output Structure
    # Create folder_title by removing all known parts from the original clean string
    final_title = clean_filename
    for part in known_parts:
        final_title = final_title.replace(part, '')
    
    # Remove bracketed groups and redundant spaces
    final_title = re.sub(r'\[[^\]]+\]|\([^)]+\)', '', final_title)
    final_title = re.sub(r'\s{2,}', ' ', final_title).strip()
    result['folder_title'] = final_title
    
    # The rest is "extra bits"
    # Find all known parts in the original filename to create the extra_bits string
    extra_bits_temp = filename
    for key, value in result.items():
        if value and key not in ['folder_path', 'folder_title', 'folder_extra_bits']:
            extra_bits_temp = extra_bits_temp.replace(str(value), '')
    
    # Remove the final cleaned title from the string
    extra_bits_temp = extra_bits_temp.replace(result['folder_title'], '').strip()
    
    # Final cleanup of extra bits
    extra_bits_temp = RE_WEBSITE_CLEANER.sub('', extra_bits_temp)
    extra_bits_temp = re.sub(r'\[\s*\]|\(|\)', '', extra_bits_temp)
    extra_bits_temp = re.sub(r'[._-]', ' ', extra_bits_temp)
    extra_bits_temp = re.sub(r'\s{2,}', ' ', extra_bits_temp).strip()
    result['folder_extra_bits'] = extra_bits_temp

    # Heuristic for media type
    if result['folder_media_type'] is None:
        if result['folder_year'] and not result['folder_is_anime']:
            result['folder_media_type'] = 'Movie'
        elif result['folder_is_anime'] or result['folder_anime_episode']:
            result['folder_media_type'] = 'TV'
    
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
    
    # Create output filename in the current directory
    now = datetime.now()
    output_filename = os.path.join(os.getcwd(), f"output_{now.strftime('%m%d_%H%M')}.txt")
    
    # Redirect output to file
    original_stdout = sys.stdout
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        sys.stdout = f
        for s in samples:
            parsed_data = parse_filename(s)
            print(f"--- Parsing: {s} ---")
            for key, value in parsed_data.items():
                print(f"  {key:<20}: {value}")
            print("\n")
        sys.stdout = original_stdout
    
    print(f"Output saved to {output_filename}")