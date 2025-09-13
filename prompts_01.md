This revised parsing strategy requires a more sophisticated, iterative approach. The core idea is to process the string with multiple passes, where each pass targets a specific type of information and removes it from the string. This ensures that a pattern like a year is not mistaken for an episode number because the episode pattern has already been extracted.

Here's the plan:

1.  **Initial Pass (Right-to-Left)**: The primary split still happens right-to-left based on a prioritized list. This identifies the most prominent clue (e.g., resolution or a year) and divides the string into `left_split` and `right_split`. The `matched` part is extracted and stored.

2.  **Iterative Extraction**: Subsequent extraction should operate on the `left_split` and a copy of the `right_split`. Each extractor will:
    * Search its designated split for a clue.
    * If found, it will extract the data and update the corresponding dictionary field (e.g., `folder_year`).
    * It will then **clean** the split it just parsed by removing the matched string.
    * The process continues until no more clues can be found.

3.  **Final Cleanup**: After all passes, the remaining parts of the string are used to create the final `folder_title` and `folder_extra_bits`. This guarantees a clean separation and prevents mixing.

### Main Media Clue Extractors (Refined)

Here are the primary extractors and their planned operations:

1.  **Resolution Extractor**:
    * **Parser**: Finds `1080p`, `720p`, `1920x1080`, etc.
    * **Action**: Searches the full string right-to-left. The first match performs the primary split, populating `folder_resolution`.
    * **Output**: `left_split`, `right_split`, `folder_resolution`.

2.  **Anime Group Extractor**:
    * **Parser**: Finds groups like `[SubsPlease]`, `[Erai-raws]`.
    * **Action**: Searches both the `left_split` (left-to-right) and `right_split` (right-to-left) for a match. The matched group is stored in `folder_anime_group`.
    * **Output**: The extractor cleans the split where it found the group, removing the bracketed text.

3.  **Anime/Episode Extractor**:
    * **Parser**: Finds patterns like `S01E02`, `01`, `Ep02`.
    * **Action**: Searches the `left_split` for these patterns. If a pattern is found, it extracts the episode number and stores it in `folder_anime_episode`.
    * **Output**: The extractor cleans the `left_split` by removing the matched episode part.

4.  **Year Extractor**:
    * **Parser**: Finds four-digit years `(19xx` or `20xx)`.
    * **Action**: Searches the `left_split` for a year. This is done after the episode number extraction to avoid conflicts.
    * **Output**: Extracts the year and cleans the `left_split`.

5.  **Final String Assembly**:
    * After all the above extractions, any remaining parts in the `left_split` and `right_split` are combined.
    * Common junk strings (websites, file extensions, etc.) are removed.
    * The cleaned string becomes `folder_title`, and any remaining unparsed parts are put in `folder_extra_bits`.

This refined approach ensures that each piece of information is handled by a dedicated extractor in a specific order, which minimizes conflicts and produces a more accurate and cleaner output.