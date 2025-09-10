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
    Simply removes the first bracket set if it's a website.
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
    
    # Find only the FIRST square bracket at the very beginning
    start_bracket_pattern = r'^\[[^\]]*\]\s*'
    match = re.match(start_bracket_pattern, filename)
    
    if match:
        bracket_content = match.group(0)
        bracket_text = bracket_content[1:bracket_content.find(']')]
        
        metadata["found_at_start"] = [bracket_text]
        
        if debug:
            print(f"  Found FIRST bracket at start: '{bracket_content}'")
        
        # Remove it if it's a website pattern
        if is_website_pattern(bracket_text):
            if debug:
                print(f"  Detected website: '{bracket_text}'")
            filename = filename[len(bracket_content):].strip()
            metadata["removed"].append(bracket_content)
        else:
            # Keep non-website brackets for later analysis
            if debug:
                print(f"  Not a website: '{bracket_text}' - keeping in filename")
    
    # Check entire filename for anime release groups (anywhere)
    for group in KNOWN_CLUES["release_groups_anime"]:
        if group.lower() in filename.lower():
            metadata["anime_clue"] = True
            metadata["clue"] = group
            if debug:
                print(f"  Anime release group found: '{group}'")
            break
    
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
    Second stage: Replace ALL square brackets with spaces, preserving content.
    This is simpler and preserves all information for later parsing.
    """
    original = filename
    metadata = {
        "found": [],
        "replaced": []
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
        
        # Replace ALL square brackets with spaces, keeping content
        # This preserves the information for later parsing
        filename = re.sub(r'\[|\]', ' ', filename)
        
        # Clean up extra spaces
        filename = re.sub(r'\s+', ' ', filename).strip()
        
        metadata["replaced"] = [f"[{item}] -> '{item}'" for item in bracket_items]
        
        if debug:
            print(f"  Replaced: {', '.join(metadata['replaced'])}")
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
        "[Funi] My Hero Academia [Season 4] [01] [1080p].mkv",
        "[HorribleSubs] Attack on Titan - 01 [1080p].mkv",
        "[www.example.co.uk] Another Anime - 03 [HorribleSubs].mkv"
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
    header += "\nTESTING MEDIA FILENAME PARSER - FIRST TWO STAGES"
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
    print("TESTING MEDIA FILENAME PARSER - FIRST TWO STAGES")
    print("="*60)
    
    for test in test_cases:
        process_filename(test)

if __name__ == "__main__":
    test_parser()