import re
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# A conservative list of typical release-group-like bracket tokens
KNOWN_ANIME_RELEASE_GROUPS = [
    r"SubsPlease", r"Erai-raws", r"Exiled-Destiny",
    r"HorribleSubs", r"CR", r"Funimation",
    r"ANiDL", r"UTW", r"Nekomoe kissaten",
]

# Precompiled regexes (expand and improve these as needed)
RE_RESOLUTION = re.compile(r"\b(\d{3,4}x\d{3,4}|[4-8]K|720p|1080p|2160p)\b", flags=re.I)
RE_MEDIA_SOURCE = re.compile(r"\b(?:WEB-DL|BluRay|HDTV|WEBRip|AMZN)\b", flags=re.I)
RE_SEASON_EP = re.compile(r"\bS(\d{1,2})E(\d{1,3})\b", flags=re.I)
RE_ANIME_EPISODE = re.compile(r"\b(?:ep\.?|episode)?\s*(\d{2,4})\b", flags=re.I)
RE_SEASON_ONLY = re.compile(r"\bS(\d{1,2})\b", flags=re.I)
RE_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
RE_BRACKET_GROUP = re.compile(r"\[([^\]]+)\]")
RE_KNOWN_ANIME_GROUP_PATTERNS = [re.compile(pattern) for pattern in KNOWN_ANIME_RELEASE_GROUPS]

# Define a prioritized list of regexes for right-to-left scanning
CLUE_PATTERNS = [
    ('resolution', RE_RESOLUTION),
    ('media_source', RE_MEDIA_SOURCE),
    ('season_ep', RE_SEASON_EP),
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
    
    leftsplit = filename
    matched = None
    rightsplit = ""
    
    # 1. Core Parsing Logic: The "First Match" Split (Right-to-Left)
    for key, pattern in CLUE_PATTERNS:
        matches = list(pattern.finditer(filename))
        if matches:
            match = matches[-1] # Find the right-most match
            matched = match.group(0)
            
            leftsplit = filename[:match.start()].strip()
            rightsplit = filename[match.end():].strip()
            
            if key == 'resolution':
                result['folder_resolution'] = matched
            elif key == 'year':
                result['folder_year'] = matched
            elif key == 'season_ep':
                result['folder_media_type'] = 'TV'
                result['folder_is_anime'] = True
                result['folder_anime_episode'] = f"S{match.group(1)}E{match.group(2)}"
            elif key == 'anime_episode':
                result['folder_is_anime'] = True
                result['folder_media_type'] = 'TV'
                result['folder_anime_episode'] = matched
            elif key == 'season_only':
                result['folder_is_anime'] = True
                result['folder_media_type'] = 'TV'
            
            break # Exit the loop after the first match is found
            
    # 2. Anime Release Group Parsing (Directional Search)
    anime_group_found = None
    
    # Search leftsplit from left-to-right
    bracket_matches = RE_BRACKET_GROUP.findall(leftsplit)
    for group_name in bracket_matches:
        for group_pattern in RE_KNOWN_ANIME_GROUP_PATTERNS:
            if group_pattern.search(group_name):
                anime_group_found = group_name
                break
        if anime_group_found:
            break
            
    # If not found, search rightsplit from right-to-left
    if not anime_group_found:
        bracket_matches = RE_BRACKET_GROUP.findall(rightsplit)
        for group_name in reversed(bracket_matches):
            for group_pattern in RE_KNOWN_ANIME_GROUP_PATTERNS:
                if group_pattern.search(group_name):
                    anime_group_found = group_name
                    break
            if anime_group_found:
                break

    if anime_group_found:
        result['folder_anime_group'] = anime_group_found
        result['folder_is_anime'] = True
        
    # 3. Final Output Structure
    # Correct the title cleanup logic
    if matched:
        title_from_leftsplit = leftsplit.replace(matched, '').strip()
    else:
        title_from_leftsplit = leftsplit

    # Remove the anime group from the title
    if result['folder_anime_group']:
        title_from_leftsplit = title_from_leftsplit.replace(f"[{result['folder_anime_group']}]", '').strip()
        
    result['folder_title'] = re.sub(r'[._-]', ' ', title_from_leftsplit).strip()
    
    # Heuristic for media type
    if result['folder_media_type'] is None:
        if result['folder_year'] and not result['folder_is_anime']:
            result['folder_media_type'] = 'Movie'
        elif result['folder_is_anime'] or result['folder_anime_episode']:
            result['folder_media_type'] = 'TV'

    # The rest is "extra bits"
    extra_bits_parts = [
        s for s in [leftsplit.replace(result['folder_title'], '').strip(), rightsplit]
        if s and s != result['folder_anime_group']
    ]
    result['folder_extra_bits'] = ' '.join(extra_bits_parts).strip()
    result['folder_extra_bits'] = re.sub(r'\[\s*\]|\(|\)', '', result['folder_extra_bits']).strip()

    result['folder_title'] = re.sub(r'\s{2,}', ' ', result['folder_title']).strip()
    result['folder_extra_bits'] = re.sub(r'\s{2,}', ' ', result['folder_extra_bits']).strip()

    return result

if __name__ == '__main__':
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

    for test_filename in tests:
        parsed_data = parse_filename(test_filename)
        print(f"--- Parsing: {test_filename} ---")
        for key, value in parsed_data.items():
            print(f"  {key:<20}: {value}")
        print("\n")