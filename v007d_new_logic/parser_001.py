import re
from typing import Tuple, Dict, List, Optional, Any

# Simplified known clues for anime release groups
KNOWN_CLUES = {
    "release_groups_anime": [
        "HorribleSubs", "Erai-raws", "Nyaa", "Commie", "Shinzou-Narana", 
        "AnimeRG", "SubsPlease", "Doki", "Punished", "Hoodlum", "Funi", 
        "Crunchyroll", "GM-Team", "SweetSub", "NC-Raws", "Seed-Raws", "Moozzi2"
    ]
}

def is_website_pattern(text: str) -> bool:
    """
    Check if text matches a website pattern (www.word.word).
    Handles patterns like www.example.com or www.example.co.uk
    """
    # Pattern: www.something.something (with 2-3 char TLD, possibly with additional 2-char country code)
    pattern = r'^www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,6}(?:\.[a-zA-Z]{2,})?$'
    return bool(re.match(pattern, text, re.IGNORECASE))

def cleaner_1_square_brackets_and_media_type_clues_for_anime(
    filename: str, 
    debug: bool = True
) -> Tuple[str, bool, Dict[str, Any]]:
    """
    First stage: Process square brackets at the start of the filename.
    
    Rules:
    1. Extract all square brackets at the beginning of the string
    2. Check if they contain website patterns (www.word.word)
    3. If not a website, check against known anime release groups
    4. Mark as possible anime if matches are found
    
    Returns:
        (cleaned_filename, is_anime, metadata)
    """
    original = filename
    metadata = {
        "found": [],
        "anime_clue": False,
        "clue": None,
        "removed": []
    }
    
    # Find all square brackets at the very beginning of the string
    start_bracket_pattern = r'^(\[[^\]]*\]\s*)+'
    match = re.match(start_bracket_pattern, filename)
    
    if debug:
        print(f"\n=== Stage 1: Processing square brackets at start ===")
        print(f"Input: '{filename}'")
    
    if match:
        bracket_content = match.group(0)
        if debug:
            print(f"  Found brackets at start: '{bracket_content}'")
        
        # Extract individual bracket contents
        bracket_items = re.findall(r'\[([^\]]*)\]', bracket_content)
        metadata["found"] = bracket_items
        
        # Process each bracket item
        for item in bracket_items:
            # Check if it's a website pattern
            if is_website_pattern(item):
                if debug:
                    print(f"  Detected website: '{item}'")
                # Keep it as part of the filename
                continue
            
            # Check against known anime release groups
            anime_group_found = None
            for group in KNOWN_CLUES["release_groups_anime"]:
                if group.lower() in item.lower():
                    anime_group_found = group
                    break
            
            if anime_group_found:
                metadata["anime_clue"] = True
                metadata["clue"] = f"[{item}]"
                if debug:
                    print(f"  Anime release group found: '{item}' (matches '{anime_group_found}')")
            elif not is_website_pattern(item):
                # Not a website and not a known release group - still mark as potential anime
                metadata["anime_clue"] = True
                metadata["clue"] = f"[{item}]"
                if debug:
                    print(f"  Potential anime clue (not in known list): '{item}'")
            
            # Remove the bracket from the filename
            filename = filename.replace(f"[{item}]", "", 1).strip()
            metadata["removed"].append(f"[{item}]")
    
    # Clean up multiple spaces
    filename = re.sub(r'\s+', ' ', filename).strip()
    
    if debug:
        print(f"  Anime clue: {metadata['anime_clue']}")
        if metadata["clue"]:
            print(f"  Clue: {metadata['clue']}")
        print(f"  Removed: {', '.join(metadata['removed']) if metadata['removed'] else 'None'}")
        print(f"  Output: '{filename}'")
    
    return filename, metadata["anime_clue"], metadata

def cleaner_2_replace_square_brackets_at_end(
    filename: str, 
    debug: bool = True
) -> Tuple[str, Dict[str, Any]]:
    """
    Second stage: Process square brackets at the end of the filename.
    
    Rules:
    1. Find square brackets at the end of the string
    2. Replace [02] style brackets with just the number (for episode numbers)
    3. Replace other brackets with spaces
    
    Returns:
        (cleaned_filename, metadata)
    """
    original = filename
    metadata = {
        "found": [],
        "replaced": []
    }
    
    if debug:
        print(f"\n=== Stage 2: Processing square brackets at end ===")
        print(f"Input: '{filename}'")
    
    # Find all square brackets at the end of the string
    end_bracket_pattern = r'(\s*\[[^\]]*\])+$'
    match = re.search(end_bracket_pattern, filename)
    
    if match:
        bracket_content = match.group(0)
        if debug:
            print(f"  Found brackets at end: '{bracket_content}'")
        
        # Extract individual bracket contents
        bracket_items = re.findall(r'\[([^\]]*)\]', bracket_content)
        metadata["found"] = bracket_items
        
        # Process each bracket item from the end
        for item in bracket_items:
            # Check if it looks like an episode number (just digits)
            if re.match(r'^\d{1,4}$', item):
                # Keep episode numbers as part of the title
                replacement = f" {item} "
                metadata["replaced"].append(f"[{item}] -> '{item}'")
            # Check if it's a quality/resolution indicator
            elif re.match(r'^(1080p|720p|480p|2160p|BD|BluRay|WEB-DL|WEBRip|HDTV|x264|x265|HEVC)$', item, re.IGNORECASE):
                # Remove quality indicators completely
                replacement = " "
                metadata["replaced"].append(f"[{item}] -> removed")
            else:
                # Replace other brackets with spaces
                replacement = " "
                metadata["replaced"].append(f"[{item}] -> space")
            
            # Replace only the specific bracket
            filename = filename.replace(f"[{item}]", replacement, 1)
        
        # Clean up extra spaces
        filename = re.sub(r'\s+', ' ', filename).strip()
    
    if debug:
        print(f"  Found: {', '.join(metadata['found']) if metadata['found'] else 'None'}")
        print(f"  Replaced: {', '.join(metadata['replaced']) if metadata['replaced'] else 'None'}")
        print(f"  Output: '{filename}'")
    
    return filename, metadata

def process_filename(filename: str, debug: bool = True):
    """Process a filename through both cleaning stages."""
    if debug:
        print(f"\n{'='*50}")
        print(f"Processing filename: '{filename}'")
        print(f"{'='*50}")
    
    # Stage 1
    cleaned1, is_anime, metadata1 = cleaner_1_square_brackets_and_media_type_clues_for_anime(filename, debug)
    
    # Stage 2
    cleaned2, metadata2 = cleaner_2_replace_square_brackets_at_end(cleaned1, debug)
    
    # Final results
    if debug:
        print(f"\n{'='*50}")
        print(f"Final results for '{filename}':")
        print(f"  Cleaned filename: '{cleaned2}'")
        print(f"  Is anime: {is_anime}")
        print(f"{'='*50}\n")
    
    return cleaned2, is_anime

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
        "[Seed-Raws] 劇場版 ペンギン・ハイウェイ Penguin Highway The Movie (BD 1280x720 AVC AACx4 [5.1+2.0+2.0+2.0]).mp4"
    ]
    
    print("\n" + "="*60)
    print("TESTING MEDIA FILENAME PARSER - FIRST TWO STAGES")
    print("="*60)
    
    for test in test_cases:
        process_filename(test)

if __name__ == "__main__":
    test_parser()