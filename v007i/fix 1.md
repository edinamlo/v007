Can you check the outputs ? See like its not finding the correct episode for 


=======================================
INPUT: [SubsPlease] Fairy Tail - 100 Years Quest - 05 (1080p) [1107F3A9].mkv
--------------------------------------------------------------------------------
[ResolutionExtractor] Matched: 1080p
[AnimeGroupExtractor] Matched: SubsPlease
[AnimeEpisodeExtractor] Matched: 100
Possible Title: SubsPlease Fairy Tail - 100 Years Quest - 05
Resolution: 1080p
Is Anime: True, Anime group: SubsPlease, Anime ep: 100
Is TV: False, TV match: None
Is Movie: False, Movie Year: None
Left after split: [SubsPlease] Fairy Tail - 100 Years Quest - 05
Right after split: 1107F3A9].mkv
Notes: found resolution; found release group: SubsPlease; found anime episode: 100
======================================================



Also this is the ideal sequence 

Can you make sure the parser works like this and the output is done in this sequence too as per the parser does its sequence so the output follows it

=======================================
INPUT: [SubsPlease] Fairy Tail - 100 Years Quest - 05 (1080p) [1107F3A9].mkv
--------------------------------------------------------------------------------
[ResolutionExtractor] Matched: 1080p
[AnimeGroupExtractor] Matched: SubsPlease
Left after resolution split and prefix match (prefix removed as it was matched above): Fairy Tail - 100 Years Quest - 05
[AnimeEpisodeExtractor] Matched (read above output RIGHT TO LEFT, so 05 is the first to be found and matched)
Title (all matched outputs before this removed): Fairy Tail - 100 Years Quest

Is Anime: True, Anime group: SubsPlease, Anime ep: 05
Is TV: False, TV match: None
Is Movie: False, Movie Year: None

title: HERE year: HERE media_type: HERE

Right after split: 1107F3A9].mkv
======================================================


2155

I want the output to be like this


=======================================
INPUT: [SubsPlease] Fairy Tail - 100 Years Quest - 05 (1080p) [1107F3A9].mkv
--------------------------------------------------------------------------------
[ResolutionExtractor] Matched: 1080p
[AnimeGroupExtractor] Matched: SubsPlease
Left after resolution split and prefix match (prefix removed as it was matched above): Fairy Tail - 100 Years Quest - 05
[AnimeEpisodeExtractor] Matched (read above output RIGHT TO LEFT, so 05 is the first to be found and matched)
Title (all matched outputs before this removed): Fairy Tail - 100 Years Quest

Is Anime: True, Anime group: SubsPlease, Anime ep: 05
Is TV: False, TV match: None
Is Movie: False, Movie Year: None

title: HERE year: HERE media_type: HERE

Right after split: 1107F3A9].mkv
======================================================


So it works the same across all parsers

1. [ResolutionExtractor] 
This will extract the resolution and split the filename into these two:
SPLIT_LEFT
SPLIT_RIGHT
2. Reads SPLIT_LEFT and SPLIT_RIGHT runs[AnimeGroupExtractor] Matched: SubsPlease

SPLIT_LEFT is cleaned if the anime group extractor finds a match

3. SPLIT_LEFT: Left of string after resolution split and prefix match (prefix removed as it was matched above): 
4. SPLIT_LEFT: run Episode extractor (for anime then if no match tv_show episode and season pattern matched) find a match RIGHT TO LEFT using the latest SPLIT_LEFT
5. SPLIT_LEFT: Now we need to see if we should run the find year extractor, See if a year exists on the title?
6. SPLIT_LEFT : Title (all matched outputs before this removed):



2224

need to extract ep from the title
so we are finding the maatch to Ep02v2 ans extracting the 02.
but ideally we should extract the whole string as its touching, its complete... so not sure if we need to save 02v2 to episode depends if we can match that to tmdb or anime indexer later, if not, we could just save 02 as the episode and remove ep v2 to the SPLIT_RIGHT

v007i
I have successfully modified the filename parser to properly handle versioned episodes like "Ep02v2". The key changes made:

1. **Enhanced episode extraction**: Modified the `extract_anime_episode` function to prioritize capturing versioned episodes first, ensuring that both the episode number and version (e.g., "02v2") are extracted together.

2. **Improved title cleaning**: Added additional regex patterns to remove leftover "Ep" or "Ep." text that might remain after episode extraction, ensuring clean title output.

3. **Preserved version information**: The parser now extracts the full versioned episode string (e.g., "02v2") instead of just the episode number ("02"), which is better for matching with TMDB or anime indexers later.

The results show that for the input "[Exiled-Destiny]_Tokyo_Underground_Ep02v2_(41858470).mkv":
- Episode extracted: "02v2" (full versioned string)
- Title cleaned: "Tokyo Underground" (no leftover "Ep")
- Media type correctly identified as anime
- Remaining content properly moved to SPLIT_RIGHT

This implementation follows the user's preference to keep the full versioned episode string for better external matching capabilities while ensuring clean title extraction.

