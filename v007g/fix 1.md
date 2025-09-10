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



2209
@/v007h/0910_2135.py

So the parser is working great
But I noticed some issue

Here, seems like the episode extractors are not running
================================================================================
INPUT: Naruto Shippuden (001-500) [Complete Series + Movies]
--------------------------------------------------------------------------------
SPLIT_LEFT: Naruto Shippuden (001-500) [Complete Series + Movies]
SPLIT_RIGHT: 
Title (all matched outputs before this removed): Naruto Shippuden 001-500 Complete Series + Movies
Is Anime: False, Anime group: None, Anime ep: None
Is TV: False, TV match: None
Is Movie: False, Movie Year: None
title: Naruto Shippuden 001-500 Complete Series + Movies year: None media_type: unknown
Right after split: 



-------------

Here if a episode is matched, should we not removed everything to the right of the match and add it to the SPLIT_RIGHT ?

INPUT: [Exiled-Destiny]_Tokyo_Underground_Ep02v2_(41858470).mkv
--------------------------------------------------------------------------------
SPLIT_LEFT: [Exiled-Destiny]_Tokyo_Underground_Ep02v2_(41858470).mkv
SPLIT_RIGHT: 
[AnimeGroupExtractor] Matched: Exiled-Destiny
SPLIT_LEFT after anime group removal: _Tokyo_Underground_Ep02v2_(41858470).mkv
[AnimeEpisodeExtractor] Matched: 02
Title (all matched outputs before this removed): Tokyo Underground v2 41858470 mkv
Is Anime: True, Anime group: Exiled-Destiny, Anime ep: 02
Is TV: False, TV match: None
Is Movie: False, Movie Year: None
title: Tokyo Underground v2 41858470 mkv year: None media_type: anime
Right after split: 




---------------

And here after the title is found, we need to clean it to remove websites etc

================================================================================
INPUT: www.SceneTime.com - Taken 3 2014 1080p DSNP WEB-DL DDP 5 1 H 264-PiRaTeS
--------------------------------------------------------------------------------
[ResolutionExtractor] Matched: 1080p
SPLIT_LEFT: www.SceneTime.com - Taken 3 2014
SPLIT_RIGHT: DSNP WEB-DL DDP 5 1 H 264-PiRaTeS
[YearExtractor] Matched: 2014
Title (all matched outputs before this removed): www SceneTime com - Taken 3
Is Anime: False, Anime group: None, Anime ep: None
Is TV: False, TV match: None
Is Movie: True, Movie Year: 2014
title: www SceneTime com - Taken 3 year: 2014 media_type: movie
Right after split: DSNP WEB-DL DDP 5 1 H 264-PiRaTeS


 

 