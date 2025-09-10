# Parser Fixes Summary

## Overview
This document summarizes the improvements made to the filename parser to fix various issues and ensure proper functionality.

## Original Issues Identified

1. **Hunter x Hunter (2011) - 01** was incorrectly identified as a movie instead of anime
2. **Title cleaning** was leaving brackets and parentheses in the title
3. **Split logic** was flawed - splitting at wrong places leaving incomplete text
4. **Anime episode detection** wasn't working for some cases like "Ep02v2"

## Fixes Implemented

### 1. Improved Anime Episode Extraction
```python
def extract_anime_episode(name):
    # Match various episode formats: 01, 02, Ep02, Ep.20, Ep02v2, etc.
    match = re.search(r"(?:\b|_)(?:EP\.?\s?)(\d{2,3})(?:v\d+)?(?:\b|_)", name, re.I)
    if not match:
        match = re.search(r"[\s\-_.](\d{2,3})(?:v\d+)?(?=\s|\[|\(|$|\.)", name)
    if match:
        ep = int(match.group(1))
        print(f"[AnimeEpisodeExtractor] Matched: {ep}")
        return ep, f"found anime episode: {ep}"
    return None, None
```

### 2. Enhanced Anime Detection Logic
```python
# Determine if it's anime (more accurate logic)
is_anime = anime_group is not None or anime_ep is not None
```

### 3. Improved Title Cleaning
```python
# Title cleaning (improved)
title = re.sub(r"[._]+", " ", left).strip()
# Remove brackets and parentheses from title
title = re.sub(r"[\[\]\(\)]", "", title).strip()
```

### 4. Better Split Logic
```python
# Resolution (split point) - improved split logic
if resolution:
    # Find the position of resolution and split more intelligently
    resolution_pos = name.find(resolution)
    if resolution_pos != -1:
        left = name[:resolution_pos].strip()
        right = name[resolution_pos + len(resolution):].strip()
        
        # Clean up the split - remove trailing/leading punctuation from left/right
        left = re.sub(r'[\s\-_.\(\)\[\]]+$', '', left)
        right = re.sub(r'^[\s\-_.\(\)\[\]]+', '', right)
```

## Results Achieved

### Before Fixes:
- Hunter x Hunter (2011) - 01 was incorrectly identified as Movie
- Titles had incomplete brackets/parentheses
- Split left incomplete text like "[SubsPlease] Tearmoon Teikoku Monogatari - 01 ("
- Ep02v2 wasn't detected properly

### After Fixes:
- ✅ Hunter x Hunter (2011) - 01 correctly identified as Anime
- ✅ Clean titles: "SubsPlease Tearmoon Teikoku Monogatari - 01"
- ✅ Proper split: "[SubsPlease] Tearmoon Teikoku Monogatari - 01"
- ✅ Ep02v2 correctly extracts episode 2

## Test Cases Verified

The parser now correctly handles all test cases:

1. **Movies**: Taken 3 2014, Some.Movie.2023
2. **Anime with groups**: [SubsPlease], [Erai-raws], [Exiled-Destiny]
3. **Anime episodes**: 01, 05, 10, 100, Ep02v2
4. **Mixed content**: Hunter x Hunter (2011) - 01 (year + episode)
5. **No metadata**: Naruto Shippuden (001-500) [Complete Series + Movies]

## Key Improvements

1. **Accurate media type detection**: Properly distinguishes between anime, movies, and TV shows
2. **Complete metadata extraction**: Extracts resolution, year, anime group, episode numbers
3. **Clean output**: Removes unnecessary punctuation and formatting artifacts
4. **Robust parsing**: Handles various filename formats and edge cases

The parser now works as intended, splitting filenames at resolution points and parsing the left side right-to-left to extract title and media type information.
