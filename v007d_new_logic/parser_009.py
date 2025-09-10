import re
import sys
import io
from contextlib import contextmanager
from typing import Tuple, Dict, List, Optional, Any

# Simplified known clues for anime release groups
KNOWN_CLUES = {
    "release_groups_anime": [
        "HorribleSubs", "Erai-raws", "Nyaa", "Commie", "Shinzou-Narana", 
        "AnimeRG", "SubsPlease", "Doki", "Punished", "Hoodlum", "Funi", 
        "Crunchyroll", "GM-Team", "SweetSub", "NC-Raws", "Seed-Raws", "Moozzi2"
    ]
}

# Resolution patterns
RESOLUTION_PATTERNS = {
    'standard': re.compile(r'\b(\d{3,4}p)\b', re.IGNORECASE),
    'dimensions': re.compile(r'\b(\d{3,4}x\d{3,4})\b', re.IGNORECASE),
    'custom_dimensions': re.compile(r'\b(\d{4}x\d{4})\b', re.IGNORECASE),
    'uhd': re.compile(r'\b(4K|UHD|2160p|Ultra\.?HD)\b', re.IGNORECASE),
    'hd': re.compile(r'\b(1080p|720p|480p|1080i|720i)\b', re.IGNORECASE),
    'sd': re.compile(r'\b(480p|360p|240p|SD)\b', re.IGNORECASE),
}

def is_website_pattern(text: str) -> bool:
    """Check if text matches a website pattern (www.word.word)."""
    pattern = r'^www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,6}(?:\.[a-zA-Z]{2,})?$'
    return bool(re.match(pattern, text, re.IGNORECASE))

def cleaner_1_square_brackets_and_media_type_clues_for_anime(
    filename: str, 
    debug: bool = True
) -> Tuple[str, bool, Dict[str, Any]]:
    """
    First stage: Process square brackets at the start of the filename.
    """
    original = filename
    metadata = {
        "found_at_start": [],
        "anime_clue": False,
        "clue": None,
        "removed": []
    }
    
    if debug:
        print(f"\n=== Stage 1: Processing square brackets at start ===")
        print(f"Input: '{filename}'")
    
    # Remove file extension first
    common_extensions = ['mkv', 'mp4', 'avi', 'mov', 'mpg', 'mpeg', 'srt', 'torrent', 'wav', 'flac', 'm4v']
    filename_no_ext = filename
    if '.' in filename:
        parts = filename.split('.')
        if len(parts) > 1 and parts[-1].lower() in common_extensions:
            filename_no_ext = '.'.join(parts[:-1])
            if debug:
                print(f"  Removed extension: {parts[-1]}")
    
    # Find only the FIRST square bracket at the very beginning
    start_bracket_pattern = r'^\[[^\]]*\]\s*'
    match = re.match(start_bracket_pattern, filename_no_ext)
    
    if match:
        bracket_content = match.group(0)
        bracket_text = bracket_content[1:bracket_content.find(']')]
        
        metadata["found_at_start"] = [bracket_text]
        
        if debug:
            print(f"  Found FIRST bracket at start: '{bracket_content}'")
        
        # Check if it's a website pattern
        if is_website_pattern(bracket_text):
            if debug:
                print(f"  Detected website: '{bracket_text}'")
            filename_no_ext = filename_no_ext[len(bracket_content):].strip()
            metadata["removed"].append(bracket_content)
        else:
            if debug:
                print(f"  Not a website: '{bracket_text}' - keeping in filename for now")
    
    # Check entire filename for anime release groups (anywhere)
    for group in KNOWN_CLUES["release_groups_anime"]:
        if group.lower() in filename_no_ext.lower():
            metadata["anime_clue"] = True
            metadata["clue"] = group
            if debug:
                print(f"  Anime release group found: '{group}'")
            break
    
    # Clean up multiple spaces
    filename_no_ext = re.sub(r'\s+', ' ', filename_no_ext).strip()
    
    if debug:
        print(f"  Anime clue: {metadata['anime_clue']}")
        if metadata["clue"]:
            print(f"  Clue: {metadata['clue']}")
        print(f"  Removed: {', '.join(metadata['removed']) if metadata['removed'] else 'None'}")
        print(f"  Output: '{filename_no_ext}'")
    
    return filename_no_ext, metadata["anime_clue"], metadata

def cleaner_2_replace_square_brackets_at_end(
    filename: str, 
    is_anime: bool,
    debug: bool = True
) -> Tuple[str, Dict[str, Any]]:
    """
    Second stage: Replace ALL square brackets with spaces, but remove anime release groups.
    """
    original = filename
    metadata = {
        "found": [],
        "replaced": [],
        "anime_groups_removed": [],
        "other_brackets_processed": []
    }
    
    if debug:
        print(f"\n=== Stage 2: Processing ALL square brackets ===")
        print(f"Input: '{filename}'")
    
    # Find all bracket contents
    bracket_items = re.findall(r'\[([^\]]*)\]', filename)
    metadata["found"] = bracket_items
    
    if bracket_items:
        if debug:
            print(f"  Found brackets: {', '.join(bracket_items)}")
        
        # Process each bracket item
        for item in bracket_items:
            # Check if it's an anime release group
            is_anime_group = False
            for group in KNOWN_CLUES["release_groups_anime"]:
                if group.lower() == item.lower():
                    is_anime_group = True
                    break
            
            if is_anime_group:
                # Remove anime release groups completely
                filename = filename.replace(f"[{item}]", "", 1)
                metadata["replaced"].append(f"[{item}] -> removed (anime group)")
                metadata["anime_groups_removed"].append(item)
                if debug:
                    print(f"  Removing anime release group: '[{item}]'")
            else:
                # Replace other brackets with spaces, keeping content
                filename = filename.replace(f"[{item}]", f" {item} ", 1)
                metadata["replaced"].append(f"[{item}] -> '{item}'")
                metadata["other_brackets_processed"].append(item)
        
        # Clean up extra spaces
        filename = re.sub(r'\s+', ' ', filename).strip()
        
        if debug:
            print(f"  Replaced: {', '.join(metadata['replaced'])}")
            print(f"  Output: '{filename}'")
    
    return filename, metadata

def cleaner_3_extract_resolution(
    filename: str,
    debug: bool = True
) -> Tuple[str, Dict[str, Any]]:
    """
    Third stage: Extract resolution information from the filename.
    """
    original = filename
    metadata = {
        "found_resolutions": [],
        "resolution_type": None,
        "resolution_value": None
    }
    
    if debug:
        print(f"\n=== Stage 3: Extracting resolution ===")
        print(f"Input: '{filename}'")
    
    # Search for resolution patterns in order of specificity
    resolution_found = None
    resolution_type = None
    
    # Check each pattern type
    for pattern_type, pattern in RESOLUTION_PATTERNS.items():
        matches = pattern.findall(filename)
        if matches:
            # Take the first match
            resolution_found = matches[0]
            resolution_type = pattern_type
            metadata["found_resolutions"].append({
                "value": resolution_found,
                "type": pattern_type
            })
            if debug:
                print(f"  Found {pattern_type} resolution: '{resolution_found}'")
            break
    
    # Store the results
    metadata["resolution_type"] = resolution_type
    metadata["resolution_value"] = resolution_found
    
    if debug:
        if resolution_found:
            print(f"  Resolution: {resolution_found} ({resolution_type})")
        else:
            print("  No resolution found")
        print(f"  Output: '{filename}'")
    
    return filename, metadata

def cleaner_4_extract_episode(
    filename: str,
    is_anime: bool,
    debug: bool = True
) -> Tuple[str, Dict[str, Any]]:
    """
    Fourth stage: Extract episode information from the filename.
    Uses different patterns for anime vs TV shows.
    """
    original = filename
    metadata = {
        "episode_found": None,
        "season_found": None,
        "episode_type": None,
        "pattern_matched": None
    }
    
    if debug:
        print(f"\n=== Stage 4: Extracting episode information ===")
        print(f"Input: '{filename}'")
        print(f"Content type: {'Anime' if is_anime else 'TV Show'}")
    
    # Define patterns for both anime and TV shows
    if is_anime:
        # Anime-specific patterns (more flexible, can handle high episode numbers)
        episode_patterns = [
            # Anime dash patterns
            (r'\s-\s(\d{1,4})\s', "anime_dash", "season"),
            (r'\s-\s(\d{1,4})\[', "anime_dash_bracket", "season"),
            (r'\s-\s(\d{1,4})$', "anime_dash_end", "season"),
            (r'\s-(\d{1,4})\.', "anime_dash_dot", "season"),
            (r'\s-(\d{1,4})$', "anime_dash_end2", "season"),
            (r'S(\d{1,2})\s*-\s*(\d{1,4})', "anime_season_episode", "season"),
            
            # Season X - Episode pattern
            (r'Season\s+\d+\s*-\s*(\d{1,4})\s*\[', "anime_season_episode_bracket", "season"),
            (r'Season\s+\d+\s*-\s*(\d{1,4})\s*$', "anime_season_episode_end", "season"),
            (r'Season\s+\d+\s*-\s*(\d{1,4})\s', "anime_season_episode_space", "season"),
            
            # Space-separated patterns
            (r'\]\s+[A-Za-z\s]+\s+(\d{1,4})\s+[-\[]', "anime_group_title_episode", "season"),
            (r'\]\s+[A-Za-z\s]+\s+(\d{1,4})\s+\[', "anime_group_title_episode_bracket", "season"),
            (r'\]\s+[A-Za-z\s]+\s+(\d{1,4})(?:\s|$)', "anime_group_title_episode_end", "season"),
            
            # Episode indicators
            (r'Episode\s+(\d{1,4})', "anime_episode_word", "season"),
            (r'Episode(\d{1,4})', "anime_episode_nospace", "season"),
            (r'EP(\d{1,4})', "anime_ep", "season"),
            (r'S(\d{1,2})E(\d{1,4})', "anime_sxe", "season"),
            
            # Underscore patterns
            (r'_(\d{1,4})_\d{3,4}\.', "anime_underscore_resolution", "season"),
            (r'_(\d{1,4})\.', "anime_underscore", "season"),
            
            # Special anime content
            (r'(?:NCED|NCOP|NCBD|PV|CM|SP|OVA|OAD|SPECIAL|EXTRA)\s*(\d{1,4})', "anime_special", "special"),
            (r'-\s+(?:NCED|NCOP|NCBD|PV|CM|SP|OVA|OAD|SPECIAL|EXTRA)(\d{1,4})', "anime_special_dash", "special"),
        ]
    else:
        # TV show patterns (more structured)
        episode_patterns = [
            # Standard TV patterns
            (r'S(\d{1,2})\.E(\d{1,3})', "tv_sxe_dot", "season"),
            (r'S(\d{1,2})E(\d{1,3})', "tv_sxe", "season"),
            (r'(\d{1,2})x(\d{1,3})', "tv_x", "season"),
            (r'(\d{1,2})x(\d{1,3})-(\d{1,3})', "tv_x_range", "season"),
            
            # Standalone episode patterns
            (r'\bE(\d{1,3})\b(?![A-Z])', "tv_episode", "season"),
            (r'\bEpisode\s+(\d{1,3})', "tv_episode_word", "season"),
            (r'\bEpisode(\d{1,3})', "tv_episode_nospace", "season"),
            (r'\bepisode\.(\d{1,3})', "tv_episode_dot", "season"),
            (r'\bEP(\d{1,3})', "tv_ep", "season"),
            
            # Season patterns
            (r'S(\d{1,2})\s*-\s*E(\d{1,3})', "tv_sxe_hyphen", "season"),
            (r'Season\s+(\d{1,2})', "tv_season", "season_only"),
            (r'[Ss]eason(\d{1,2})', "tv_season_nospace", "season_only"),
            
            # Season ranges
            (r'S(\d{1,2})-S(\d{1,2})', "tv_season_range", "season_range"),
            (r'S(\d{1,2})-(\d{1,2})', "tv_season_episode_range", "season"),
            (r'(\d{1,2})-(\d{1,2})', "tv_number_range", "season"),
        ]
    
    # Try each pattern
    for pattern, pattern_name, episode_type in episode_patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            groups = match.groups()
            
            # Extract season and episode based on pattern
            if len(groups) == 1:
                # Single group - usually just episode number
                episode_num = int(groups[0])
                season_num = None
            elif len(groups) >= 2:
                # Multiple groups - usually season and episode
                try:
                    season_num = int(groups[0])
                    episode_num = int(groups[1])
                except (ValueError, IndexError):
                    # Fallback to just episode if season extraction fails
                    episode_num = int(groups[-1])
                    season_num = None
            
            # Validate episode number
            if episode_num is not None and 1 <= episode_num <= 4999:
                metadata["episode_found"] = episode_num
                metadata["season_found"] = season_num
                metadata["episode_type"] = episode_type
                metadata["pattern_matched"] = pattern_name
                
                if debug:
                    if season_num:
                        print(f"  Found {episode_type} - Season: {season_num}, Episode: {episode_num} (Pattern: {pattern_name})")
                    else:
                        print(f"  Found {episode_type} - Episode: {episode_num} (Pattern: {pattern_name})")
                
                # For TV shows, also check for multi-part patterns
                if not is_anime and season_num is None:
                    parts = filename.split()
                    for i, part in enumerate(parts):
                        if part.lower() == 'season' and i + 2 < len(parts):
                            if (parts[i + 2] == '-' and i + 3 < len(parts) and
                                re.match(r'^\d{1,2}$', parts[i + 1]) and
                                re.match(r'^\d{1,3}$', parts[i + 3])):
                                season_num = int(parts[i + 1])
                                episode_num = int(parts[i + 3])
                                metadata["season_found"] = season_num
                                metadata["episode_found"] = episode_num
                                metadata["pattern_matched"] = "tv_season_episode_fallback"
                                if debug:
                                    print(f"  Found season/episode from parts: Season {season_num}, Episode {episode_num}")
                                break
                
                break
    
    # Additional fallback for anime: check for simple numeric episode after "Season X -"
    if is_anime and metadata["episode_found"] is None:
        parts = filename.split()
        for i, part in enumerate(parts):
            if part.lower() == 'season' and i + 2 < len(parts):
                if (parts[i + 2] == '-' and i + 3 < len(parts) and
                    re.match(r'^\d{1,2}$', parts[i + 1]) and
                    re.match(r'^\d{1,4}$', parts[i + 3])):
                    season_num = int(parts[i + 1])
                    episode_num = int(parts[i + 3])
                    if 1 <= episode_num <= 4999:
                        metadata["episode_found"] = episode_num
                        metadata["season_found"] = season_num
                        metadata["episode_type"] = "season"
                        metadata["pattern_matched"] = "anime_season_episode_fallback"
                        if debug:
                            print(f"  Found anime episode from parts: Season {season_num}, Episode {episode_num}")
                        break
    
    # For TV shows, check ordinal season patterns
    if not is_anime and metadata["episode_found"] is None:
        ordinal_map = {
            'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5, 'sixth': 6,
            'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10, 'eleventh': 11, 'twelfth': 12
        }
        
        # Pattern: "Title Second Season - 02"
        ordinal_anime_pattern = r'\b(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|Eleventh|Twelfth)\s+Season\s*[-–]\s*(\d{1,3})'
        ordinal_match = re.search(ordinal_anime_pattern, filename, re.IGNORECASE)
        if ordinal_match:
            ordinal_word = ordinal_match.group(1).lower()
            season_num = ordinal_map.get(ordinal_word)
            episode_num = int(ordinal_match.group(2))
            if season_num and 1 <= episode_num <= 499:
                metadata["episode_found"] = episode_num
                metadata["season_found"] = season_num
                metadata["episode_type"] = "season"
                metadata["pattern_matched"] = "tv_ordinal_season"
                if debug:
                    print(f"  Found TV episode from ordinal: Season {season_num}, Episode {episode_num}")
    
    if debug:
        if metadata["episode_found"] is None:
            print("  No episode found")
        print(f"  Output: '{filename}'")
    
    return filename, metadata

def process_filename(filename: str, debug: bool = True):
    """Process a filename through all cleaning stages."""
    if debug:
        print(f"\n{'='*50}")
        print(f"Processing filename: '{filename}'")
        print(f"{'='*50}")
    
    # Stage 1
    cleaned1, is_anime, metadata1 = cleaner_1_square_brackets_and_media_type_clues_for_anime(filename, debug)
    
    # Stage 2
    cleaned2, metadata2 = cleaner_2_replace_square_brackets_at_end(cleaned1, is_anime, debug)
    
    # Stage 3
    cleaned3, metadata3 = cleaner_3_extract_resolution(cleaned2, debug)
    
    # Stage 4
    cleaned4, metadata4 = cleaner_4_extract_episode(cleaned3, is_anime, debug)
    
    # Final results - combine all metadata
    all_metadata = {
        "stage1": metadata1,
        "stage2": metadata2,
        "stage3": metadata3,
        "stage4": metadata4,
        "is_anime": is_anime,
        "all_clues_found": []
    }
    
    # Collect all clues found
    if metadata1["clue"]:
        all_metadata["all_clues_found"].append(f"anime_release_group: {metadata1['clue']}")
    if metadata1["found_at_start"]:
        all_metadata["all_clues_found"].append(f"start_bracket: {metadata1['found_at_start'][0]}")
    if metadata2["anime_groups_removed"]:
        all_metadata["all_clues_found"].extend([f"anime_group_removed: {group}" for group in metadata2["anime_groups_removed"]])
    if metadata2["other_brackets_processed"]:
        all_metadata["all_clues_found"].extend([f"bracket_content: {content}" for content in metadata2["other_brackets_processed"]])
    if metadata3["resolution_value"]:
        all_metadata["all_clues_found"].append(f"resolution: {metadata3['resolution_value']} ({metadata3['resolution_type']})")
    if metadata4["episode_found"]:
        if metadata4["season_found"]:
            all_metadata["all_clues_found"].append(f"episode: S{metadata4['season_found']}E{metadata4['episode_found']} ({metadata4['episode_type']})")
        else:
            all_metadata["all_clues_found"].append(f"episode: E{metadata4['episode_found']} ({metadata4['episode_type']})")
    
    # Final results
    if debug:
        print(f"\n{'='*50}")
        print(f"Final results for '{filename}':")
        print(f"  Cleaned filename: '{cleaned4}'")
        print(f"  Is anime: {is_anime}")
        print(f"  All clues found:")
        for clue in all_metadata["all_clues_found"]:
            print(f"    - {clue}")
        print(f"{'='*50}\n")
    
    return cleaned4, is_anime, all_metadata

@contextmanager
def capture_output():
    """Context manager to capture stdout."""
    new_out = io.StringIO()
    old_out = sys.stdout
    try:
        sys.stdout = new_out
        yield new_out
    finally:
        sys.stdout = old_out

# Test function
def test_parser():
    test_cases = [
        "[HorribleSubs] Attack on Titan - 01 [1080p].mkv",
        "[www.torrentsite.com] Naruto Shippuden - 05 [Crunchyroll].mkv",
        "[Erai-raws] Re:Zero - 12 [1080p].mkv",
        "[Nyaa] One Piece - 950 [720p].mkv",
        "Anime Title [01] [1080p].mkv",
        "[Punished] Demon Slayer - 07 [WEB-DL 1080p].mkv",
        "[Funi] My Hero Academia [Season 4] [01] [1080p].mkv",
        "Regular Movie (2022) [1080p].mkv",
        "[Unknown] Some Anime - 24 [720p].mkv",
        "[www.example.co.uk] Another Anime - 03 [HorribleSubs].mkv",
        "[GM-Team][国漫][太乙仙魔录 灵飞纪 第3季][Magical Legend of Rise to immortality Ⅲ][01-26][AVC][GB][1080P]",
        "[SweetSub][Mutafukaz / MFKZ][Movie][BDRip][1080P][AVC 8bit][简体内嵌]",
        "[Erai-raws] Kingdom 3rd Season - 02 [1080p].mkv",
        "[NC-Raws] 间谍过家家 / SPY×FAMILY - 04 (B-Global 1920x1080 HEVC AAC MKV)",
        "[Seed-Raws] 劇場版 ペンギン・ハイウェイ Penguin Highway The Movie (BD 1280x720 AVC AACx4 [5.1+2.0+2.0+2.0]).mp4",
        # Add TV show test cases
        "Game of Thrones S01E01 1080p.mkv",
        "Friends S10E12 720p HDTV.mkv",
        "The Office Season 3 Episode 5 1080p.mkv",
        "Breaking Bad 1x07 720p.mkv",
        "Stranger Things S04E08 1080p.mkv",
    ]
    
    # Get script name without extension
    script_name = sys.argv[0]
    if script_name.endswith('.py'):
        script_name = script_name[:-3]
    output_filename = f"{script_name}_output.txt"
    
    # Capture all output
    all_output = []
    
    # Add header
    header = "\n" + "="*60
    header += "\nTESTING MEDIA FILENAME PARSER - ALL STAGES"
    header += "\n" + "="*60
    all_output.append(header)
    
    for test in test_cases:
        with capture_output() as captured:
            process_filename(test)
        all_output.append(captured.getvalue())
    
    # Write to file
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_output))
    
    print("\n" + "="*60)
    print("TESTING MEDIA FILENAME PARSER - ALL STAGES")
    print("="*60)
    
    for test in test_cases:
        process_filename(test)

if __name__ == "__main__":
    test_parser()