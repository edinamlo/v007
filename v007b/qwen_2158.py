import re
from typing import List, Tuple, Optional

def extract_title_and_year(filename: str) -> Tuple[str, Optional[int]]:
    """
    Extract title and year from filename with improved boundary detection.
    """
    # Remove file extension
    filename = re.sub(r'\.[^.]+$', '', filename)
    
    # Try to find year first
    year = None
    year_pos = -1
    
    # Look for year patterns
    year_matches = list(re.finditer(r'(?:^|[-._\s()])(\d{4})(?:[-._\s()]|$)', filename))
    
    # Filter valid years (1900-2030)
    valid_years = []
    for match in year_matches:
        year_val = int(match.group(1))
        if 1900 <= year_val <= 2030:
            valid_years.append((match.start(1), match.end(1), year_val))
    
    # Use the last valid year (usually the actual release year)
    if valid_years:
        year_pos, year_end, year = valid_years[-1]
        # Remove the year and everything after from title processing
        title_candidate = filename[:year_pos].strip()
        # But keep the part before the year for acronym detection
        if year_pos > 0 and filename[year_pos-1:year_pos] in '._- ':
            title_candidate = filename[:year_pos-1].strip()
    else:
        title_candidate = filename
    
    # Improved title cleaning
    title = clean_title(title_candidate, filename)
    
    return title, year

def clean_title(title: str, original_filename: str) -> str:
    """
    Clean title with more sophisticated boundary detection.
    """
    # Handle acronym patterns specifically (like S.W.A.T.2017)
    # Look for patterns like A.B.C. or A.B.C.Year
    acronym_pattern = r'^([A-Z](?:\.[A-Z])+)\.?$'
    acronym_match = re.match(acronym_pattern, title)
    
    if acronym_match:
        # This looks like an acronym, preserve the dots
        return acronym_match.group(1)
    
    # Handle cases where acronym runs into year
    acronym_year_pattern = r'^([A-Z](?:\.[A-Z])+)(\d{4})'
    acronym_year_match = re.match(acronym_year_pattern, title)
    
    if acronym_year_match:
        return acronym_year_match.group(1)
    
    # Remove common prefixes but be more careful
    # Remove brackets and parentheses at start
    title = re.sub(r'^[\[\(].*?[\]\)]\s*', '', title)
    
    # Remove common suffixes that might be stuck to the title
    suffixes = [
        r'[-._\s]*(HDRip|BRRip|BluRay|WEBRip|HDTV|x264|AAC|HDR|DVDRip|HD|SD|4K|1080p|720p|480p).*$', 
        r'[-._\s]*(EXTENDED|DIRECTORS|UNRATED|REMASTERED|THEATRICAL|FINAL|EDITION).*$', 
    ]
    
    for suffix_pattern in suffixes:
        title = re.sub(suffix_pattern, '', title, flags=re.IGNORECASE)
    
    # Handle standard separators
    title = re.sub(r'[-._\s]+', ' ', title)
    
    # Clean up extra whitespace
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title

# Test with your example
test_filename = "S.W.A.T.2017.1080p.BluRay.x264.AAC.HDR"
title, year = extract_title_and_year(test_filename)
print(f"Title: '{title}', Year: {year}")

# Test a few more cases
test_cases = [
    "The.Movie.2020.1080p.BluRay.x264",
    "Movie.Title.2019.HDRip",
    "[GROUP] Some.Film.2021.720p.WEBRip",
    "A.B.C.1999.DVDRip"
]

for test in test_cases:
    title, year = extract_title_and_year(test)
    print(f"'{test}' -> Title: '{title}', Year: {year}")