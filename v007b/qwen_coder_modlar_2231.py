import re
from typing import Tuple, Optional, List

def debug_print(message: str, debug: bool = True):
    """Print debug messages"""
    if debug:
        print(message)

def extract_extension(filename: str, debug: bool = True) -> str:
    """Step 1: Remove file extension"""
    original = filename
    common_extensions = ['mkv', 'mp4', 'avi', 'mov', 'mpg', 'mpeg', 'srt', 'torrent', 'wav', 'flac', 'm4v']
    
    # Better extension detection - look at the actual extension
    if '.' in filename:
        parts = filename.split('.')
        if len(parts) > 1:
            ext = parts[-1].lower()
            if ext in common_extensions:
                # Reconstruct without the last part
                filename = '.'.join(parts[:-1])
                debug_print(f"  1. Extension removed: '{original}' -> '{filename}' (.{ext})")
            else:
                debug_print(f"  1. No extension removed (.{ext} not in common list): '{filename}'")
        else:
            debug_print(f"  1. No extension to remove: '{filename}'")
    else:
        debug_print(f"  1. No extension to remove: '{filename}'")
    
    return filename

def find_clues(filename: str, debug: bool = True) -> List[Tuple[str, int, int]]:
    """Step 2: Find all potential clues in the filename"""
    debug_print(f"  2. Finding clues in: '{filename}'")
    
    clues = []
    
    # Year patterns
    year_patterns = [
        (r'(?:^|[-._\s\(])(\d{4})(?:[-._\s\)\[\]]|$)', 1, "YEAR"),
        (r'\((\d{4})\)', 1, "YEAR_PAREN"),
        (r'\[(\d{4})\]', 1, "YEAR_BRACKET"),
    ]
    
    for pattern, group, clue_type in year_patterns:
        matches = list(re.finditer(pattern, filename))
        for match in matches:
            try:
                year_val = int(match.group(group))
                if 1900 <= year_val <= 2030:
                    start_pos = match.start(group)
                    end_pos = match.end(group)
                    clues.append((clue_type, start_pos, end_pos))
                    debug_print(f"     Found {clue_type} ({year_val}): positions {start_pos}-{end_pos}")
            except (ValueError, IndexError):
                continue
    
    # Quality patterns
    quality_patterns = [
        (r'[-._\s](1080p|720p|2160p|4K|HDRip|BRRip|BluRay|WEBRip|HDTV|x264|x265|HEVC|AAC|HDR|DVDRip|WEB-DL|H264|DTS|AC3|PPV|YIFY|RARBG|AMIABLE|LOST|ROVERS|DIMENSION)[-._\s]', "QUALITY"),
    ]
    
    for pattern, clue_type in quality_patterns:
        matches = list(re.finditer(pattern, filename))
        for match in matches:
            start_pos = match.start(1)
            end_pos = match.end(1)
            clues.append((clue_type, start_pos, end_pos))
            debug_print(f"     Found {clue_type} ({match.group(1)}): positions {start_pos}-{end_pos}")
    
    # Season/episode patterns
    season_patterns = [
        (r'[-._\s](S\d{1,2}E\d{1,2}|s\d{1,2}e\d{1,2}|Season\s*\d+|season\s*\d+|Episode\s*\d+|Ep\.?\s*\d+)[-._\s]', "SEASON_EPISODE"),
    ]
    
    for pattern, clue_type in season_patterns:
        matches = list(re.finditer(pattern, filename))
        for match in matches:
            start_pos = match.start(1)
            end_pos = match.end(1)
            clues.append((clue_type, start_pos, end_pos))
            debug_print(f"     Found {clue_type} ({match.group(1)}): positions {start_pos}-{end_pos}")
    
    # Group tags
    group_patterns = [
        (r'^[\[\(]([^\]\)]*)[\]\)]', "GROUP_TAG"),
        (r'^【([^】]*)】', "GROUP_TAG"),
        (r'^★([^★]*)★', "GROUP_TAG"),
    ]
    
    for pattern, clue_type in group_patterns:
        match = re.search(pattern, filename)
        if match:
            start_pos = match.start(1)
            end_pos = match.end(1)
            clues.append((clue_type, start_pos, end_pos))
            debug_print(f"     Found {clue_type} ({match.group(1)}): positions {start_pos}-{end_pos}")
    
    # Website prefixes
    website_patterns = [
        (r'^(?:www\.)?[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*\.[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*', "WEBSITE"),
    ]
    
    for pattern, clue_type in website_patterns:
        match = re.search(pattern, filename)
        if match:
            start_pos = match.start()
            end_pos = match.end()
            clues.append((clue_type, start_pos, end_pos))
            debug_print(f"     Found {clue_type} ({match.group()}): positions {start_pos}-{end_pos}")
    
    # Sort clues by start position
    clues.sort(key=lambda x: x[1])
    
    return clues

def extract_title_from_clues(filename: str, clues: List[Tuple[str, int, int]], debug: bool = True) -> Tuple[str, Optional[int]]:
    """Step 3: Extract title based on clue positions"""
    debug_print(f"  3. Extracting title from clues in: '{filename}'")
    
    year = None
    
    if not clues:
        debug_print("     No clues found, using full filename as title")
        return filename, None
    
    # Find the first significant clue that marks the end of the title
    # We prioritize certain clue types over others
    priority_order = ["SEASON_EPISODE", "QUALITY", "YEAR", "YEAR_PAREN", "YEAR_BRACKET"]
    
    # Find the earliest position of high-priority clues
    title_end_pos = len(filename)
    found_year = None
    
    for clue_type, start_pos, end_pos in clues:
        # For years, we want to capture the year value
        if "YEAR" in clue_type and found_year is None:
            year_str = filename[start_pos:end_pos]
            try:
                found_year = int(year_str)
            except ValueError:
                pass
        
        # For high-priority clues, they likely mark the end of the title
        if clue_type in priority_order:
            # Don't consider clues that are too early (likely part of title)
            if start_pos > 5:
                title_end_pos = min(title_end_pos, start_pos)
    
    # If we didn't find any high-priority clues, use the first clue
    if title_end_pos == len(filename) and clues:
        title_end_pos = clues[0][1]
    
    # Extract title (everything before the title_end_pos)
    title = filename[:title_end_pos].strip()
    
    # Clean up title - remove trailing separators
    title = re.sub(r'[-._\s]+$', '', title)
    
    debug_print(f"     Title extracted: '{title}' (end position: {title_end_pos})")
    debug_print(f"     Year found: {found_year}")
    
    return title, found_year

def clean_title(title: str, debug: bool = True) -> str:
    """Step 4: Clean title conservatively"""
    debug_print(f"  4. Cleaning title: '{title}'")
    
    # Convert separators to spaces, but preserve meaningful structure
    original = title
    
    # Handle S.W.A.T. pattern
    swat_match = re.match(r'^([A-Z](?:\.[A-Z])+)($|\d)', title)
    if swat_match:
        result = swat_match.group(1) + "."
        if swat_match.group(2).isdigit():
            result += swat_match.group(2)
        debug_print(f"     S.W.A.T. pattern matched: '{title}' -> '{result}'")
        return result
    
    # Convert separators
    title = re.sub(r'[-_]+', ' ', title)
    
    # Handle meaningful dots (like Mr. Nobody)
    title = re.sub(r'([a-zA-Z])\.([A-Z])', r'\1. \2', title)
    
    # Clean up multiple spaces
    title = re.sub(r'\s+', ' ', title)
    
    # Clean edges
    title = title.strip(' .-')
    
    # If over-cleaned, revert to more conservative approach
    if len(title) < 3 and len(original) > 3:
        debug_print("     Over-cleaning detected, falling back")
        title = original
    
    debug_print(f"  4. Final cleaned title: '{title}'")
    return title

def extract_title_and_year(filename: str, debug: bool = True) -> Tuple[str, Optional[int]]:
    """
    Main function: Extract title and year from filename with modular steps.
    """
    if debug:
        print(f"\n=== Processing: '{filename}' ===")
    
    # Step 1: Remove extension
    filename_no_ext = extract_extension(filename, debug)
    
    # Step 2: Find clues
    clues = find_clues(filename_no_ext, debug)
    
    # Step 3: Extract title from clues
    title, year = extract_title_from_clues(filename_no_ext, clues, debug)
    
    # Step 4: Clean title
    final_title = clean_title(title, debug)
    
    if debug:
        print(f"=== Final result: '{final_title}', Year: {year} ===\n")
    
    return final_title, year

# Test function
def test_cases():
    test_key = [
        "La.famille.bélier.1995.FRENCH.1080p.BluRay.x264-LOST",
        "Mr. Nobody (2009) 1080p BluRay x264-AMIABLE",
        "S.W.A.T.2017.S08E01.720p.HDTV.x264-SYNCOPY[TGx]",
        "The.Movie.Title.2020.1080p.BluRay.x264-RARBG",
        "La famille bélier (1995)",
        "[GROUP] Some.Film.2021.720p.WEBRip",
        "A.B.C.1999.DVDRip"
    ]
    
    print("Testing comprehensive cases:")
    for test in test_key:
        title, year = extract_title_and_year(test, debug=True)
        print(f"FINAL RESULT: '{test}' -> '{title}', Year: {year}\n")

# Run tests
if __name__ == "__main__":
    test_cases()