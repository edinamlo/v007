How It Works
Stage 1: Square Brackets at Start
Finds all square brackets at the beginning of the filename
Checks for website patterns (www.word.word format)
Compares against known anime release groups from a simplified list
Marks as potential anime if:
It contains a known anime release group
It contains non-website brackets that aren't in the known list (potential new release group)
Removes all brackets from the start (keeping website brackets is optional based on your needs)
Stage 2: Square Brackets at End
Finds all square brackets at the end of the filename
Handles different bracket types differently:
[01], [24] → Keeps just the number (treats as episode number)
[1080p], [WEB-DL] → Removes completely (treats as quality info)
Other brackets → Replaces with spaces
Output Format
For each test case, it shows:

What brackets were found at the start
Whether an anime clue was detected and what it was
What was removed
What brackets were found at the end
How they were replaced
The final cleaned filename and whether it's marked as anime
Why This Is Better
Small and focused - Only 150 lines of core code
Clear separation of concerns - Each stage does one specific task
Configurable - Easy to modify the known clues list
Debug-friendly - Shows exactly what's happening at each step
Handles edge cases - Properly identifies website patterns and episode numbers
Try running this with your test cases to see how it handles different filename patterns. You can easily extend it with additional stages once you're satisfied with these first two.

Key Changes Made:
1. First Bracket Only Processing
Now only processes the FIRST bracket at the start of the filename
Only removes it if it's a website pattern
Does NOT remove non-website brackets at the start
2. Full Filename Anime Detection
Scans the ENTIRE filename for known anime release groups
Uses re.search() to find any occurrence of anime release groups anywhere in the filename
Sets is_anime = True if ANY match is found
3. Fixed Website Removal
Properly removes website patterns from the start of the filename
Keeps non-website brackets for further processing
Expected Output for Your Test Cases:
For [SweetSub][Mutafukaz / MFKZ][Movie][BDRip][1080P][AVC 8bit][简体内嵌]:

Only the first bracket [SweetSub] is processed
Since it's a known anime release group, is_anime = True
The rest of the filename remains intact for further processing
For [www.example.co.uk] Another Anime - 03 [HorribleSubs].mkv:

The website pattern is correctly detected and removed
[HorribleSubs] is found later in the filename, so is_anime = True
This implementation now correctly handles your requirements:

Only removes the first bracket if it's a website
Scans the entire filename for anime release groups
Keeps subsequent brackets for title extraction
Try running this revised version with your test cases to see the improved behavior.