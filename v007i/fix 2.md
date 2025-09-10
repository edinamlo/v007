Looking at the issues in your code, I need to implement several fixes. Here's the updated version:

```python
import re

# --- Extractors ---

def extract_resolution(name):
    match = re.search(r"(\d{3,4}p|\d{3,4}x\d{3,4})", name, re.I)
    if match:
        print(f"[ResolutionExtractor] Matched: {match.group(1)}")
        return match.group(1), "found resolution"
    return None, None


def extract_year(name):
    # More restrictive year matching to avoid false positives
    match = re.search(r"\b(19\d{2}|20\d{2})\b", name)
    if match:
        print(f"[YearExtractor] Matched: {match.group(1)}")
        return int(match.group(1)), f"found movie year: {match.group(1)}"
    return None, None


def extract_anime_group(name):
    match = re.match(r"^\[(.*?)\]", name)
    if match:
        print(f"[AnimeGroupExtractor] Matched: {match.group(1)}")
        return match.group(1), f"found release group: {match.group(1)}"
    return None, None


def extract_anime_episode(name):
    # Match various episode formats: 01, 02, Ep02, Ep.20, Ep02v2, 001-500, etc.
    # Use right-to-left search to find the last episode number
    
    # First try to match versioned episodes like Ep02v2 (capture both episode and version)
    matches = list(re.finditer(r"(?:\b|_)(?:EP\.?\s?)(\d{2,3})(v\d+)(?:\b|_)", name, re.I))
    
    # If no versioned episodes found, try regular episodes with optional version
    if not matches:
        matches = list(re.finditer(r"(?:\b|_)(?:EP\.?\s?)(\d{2,3})(?:v\d+)?(?:\b|_)", name, re.I))
    
    # If still no matches, try standalone episode numbers (but not at the very beginning)
    if not matches:
        matches = list(re.finditer(r"(?<!^)(?:\b|_)(\d{2,4})(?:v\d+)?(?=\s|\[|\(|$|\.|\-|_)", name))
    
    # Also check for episode ranges like 001-500
    if not matches:
        matches = list(re.finditer(r"(\d{2,3}-\d{2,3})", name))
    
    # Also check for versioned episodes without Ep prefix
    if not matches:
        matches = list(re.finditer(r"(?:\b|_)(\d{2,3})(v\d+)(?:\b|_)", name, re.I))
    
    if matches:
        # Get the last match (rightmost episode)
        last_match = matches[-1]
        # Handle versioned episodes (like Ep02v2 or 02v2)
        if len(last_match.groups()) > 1 and last_match.group(2):
            ep_str = last_match.group(1) + last_match.group(2)  # Include version (02v2)
        else:
            ep_str = last_match.group(1)  # Keep original string format (02)
        print(f"[AnimeEpisodeExtractor] Matched: {ep_str}")
        return ep_str, f"found anime episode: {ep_str}"
    return None, None


def extract_tv(name):
    # Match SXXEYY format
    match = re.search(r"S(\d{1,2})E(\d{1,3})", name, re.I)
    if match:
        print(f"[TVExtractor] Matched season {match.group(1)}, episode {match.group(2)}")
        return (int(match.group(1)), int(match.group(2))), f"found tv match: S{match.group(1)}E{match.group(2)}"
    
    # Match XXxYY format (like 4x13)
    match = re.search(r"(\d{1,2})x(\d{1,3})", name, re.I)
    if match:
        print(f"[TVExtractor] Matched season {match.group(1)}, episode {match.group(2)} (x format)")
        return (int(match.group(1)), int(match.group(2))), f"found tv match: {match.group(1)}x{match.group(2)}"
    
    # Match season XX format
    match = re.search(r"(?:season|s)\s*(\d{1,2})", name, re.I)
    if match:
        print(f"[TVExtractor] Matched season {match.group(1)}")
        return (int(match.group(1)), None), f"found tv season: {match.group(1)}"
    
    # Match season range format
    match = re.search(r"s(\d{2})-s(\d{2})", name, re.I)
    if match:
        print(f"[TVExtractor] Matched season range {match.group(1)}-{match.group(2)}")
        return (f"{match.group(1)}-{match.group(2)}", None), f"found tv season range: s{match.group(1)}-s{match.group(2)}"
    
    return None, None


# --- Main Parser ---

def parse_filename(name):
    print("=" * 80)
    print(f"INPUT: {name}")
    print("-" * 80)

    notes = []
    original_left = name
    original_right = ''

    # 1. Resolution extraction and split
    resolution, note = extract_resolution(name)
    if note:
        notes.append(note)

    left, right = name, ''
    if resolution:
        resolution_pos = name.find(resolution)
        if resolution_pos != -1:
            left = name[:resolution_pos].strip()
            right = name[resolution_pos + len(resolution):].strip()
            # Clean up split boundaries
            left = re.sub(r'[\s\-_.\(\)\[\]]+$', '', left)
            right = re.sub(r'^[\s\-_.\(\)\[\]]+', '', right)
    
    print(f"SPLIT_LEFT: {left}")
    print(f"SPLIT_RIGHT: {right}")

    # 2. Anime group extraction from both sides
    anime_group, note = extract_anime_group(left)
    if not anime_group:
        anime_group, note = extract_anime_group(right)
    
    if note:
        notes.append(note)
        # Clean anime group from left side if found
        if anime_group and left.startswith(f"[{anime_group}]"):
            left = re.sub(rf"^\[{re.escape(anime_group)}\]\s*", "", left).strip()
            print(f"SPLIT_LEFT after anime group removal: {left}")

    # 3. Year extraction from SPLIT_LEFT (do this before episode extraction to avoid conflicts)
    year, year_note = extract_year(left)
    if year_note:
        notes.append(year_note)
        # Move everything after year to SPLIT_RIGHT
        if year:
            year_str = str(year)
            year_pos = left.find(year_str)
            if year_pos != -1:
                content_after_year = left[year_pos + len(year_str):].strip()
                if content_after_year:
                    right = content_after_year + (' ' + right if right else '')
                    left = left[:year_pos].strip()

    # 4. TV show extraction (before episode extraction to prioritize TV format)
    tv_match, tv_note = extract_tv(left)
    if tv_note:
        notes.append(tv_note)
        # Move everything after TV match to SPLIT_RIGHT
        if tv_match:
            if isinstance(tv_match[0], int) and isinstance(tv_match[1], int):
                # SXXEYY format
                tv_str = f"S{tv_match[0]:02d}E{tv_match[1]:02d}"
            elif isinstance(tv_match[0], int):
                # Season only format
                tv_str = f"S{tv_match[0]:02d}"
            else:
                # Season range format
                tv_str = f"s{tv_match[0]}"
            
            tv_pos = left.find(tv_str)
            if tv_pos != -1:
                content_after_tv = left[tv_pos + len(tv_str):].strip()
                if content_after_tv:
                    right = content_after_tv + (' ' + right if right else '')
                    left = left[:tv_pos].strip()

    # 5. Episode extraction (right-to-left search) from SPLIT_LEFT
    # Only extract anime episodes if no TV match was found
    anime_ep, note = None, None
    if not tv_match:
        anime_ep, note = extract_anime_episode(left)
        if note:
            notes.append(note)
            # Move everything after episode to SPLIT_RIGHT
            if anime_ep:
                ep_pos = left.find(anime_ep)
                if ep_pos != -1:
                    # Move content after episode to SPLIT_RIGHT
                    content_after_ep = left[ep_pos + len(anime_ep):].strip()
                    if content_after_ep:
                        right = content_after_ep + (' ' + right if right else '')
                        left = left[:ep_pos].strip()

    # 6. Clean title extraction
    title = left.strip()
    
    # Remove episode number if found
    if anime_ep:
        # Use the original episode string format
        title = re.sub(rf"\s*-\s*{anime_ep}\s*$", "", title)
        title = re.sub(rf"\s*{anime_ep}\s*$", "", title)
        # Remove "Ep" or "Ep." followed by the episode number (with optional space)
        title = re.sub(rf"\s*Ep\.?\s*{anime_ep}\s*", "", title, flags=re.I)
        # Also remove standalone "Ep" that might be left behind
        title = re.sub(r"\s*Ep\s*$", "", title, flags=re.I)
        title = re.sub(r"\s*Ep\.\s*$", "", title, flags=re.I)
    
    # Remove TV season/episode if found
    if tv_match:
        if isinstance(tv_match[0], int) and isinstance(tv_match[1], int):
            # SXXEYY format
            season, episode = tv_match
            title = re.sub(rf"\s*S{season:02d}E{episode:02d}\s*", "", title, flags=re.I)
            title = re.sub(rf"\s*{season}x{episode}\s*", "", title, flags=re.I)
        elif isinstance(tv_match[0], int):
            # Season only format
            season = tv_match[0]
            title = re.sub(rf"\s*S{season:02d}\s*", "", title, flags=re.I)
            title = re.sub(rf"\s*season\s*{season}\s*", "", title, flags=re.I)
        else:
            # Season range format
            season_range = tv_match[0]
            title = re.sub(rf"\s*s{season_range}\s*", "", title, flags=re.I)
    
    # Remove year if found
    if year:
        title = re.sub(rf"\s*{year}\s*", "", title)
    
    # Final title cleaning - remove website URLs, common prefixes, and unwanted text
    title = re.sub(r"(www\.|https?://)[^\s]+", "", title, flags=re.I)
    title = re.sub(r"\b(?:download|torrent|free|full|movie|series|episode|season)\b", "", title, flags=re.I)
    
    # Preserve acronyms (S.H.I.E.L.D., 9-1-1, etc.)
    title = re.sub(r"([A-Z])\.([A-Z])", r"\1\2", title)  # Remove dots between uppercase letters
    title = re.sub(r"(\d)-(\d)", r"\1\2", title)  # Remove hyphens between numbers
    
    title = re.sub(r"[._]+", " ", title).strip()
    title = re.sub(r"[\[\]\(\)]", "", title).strip()
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"^\s*[-_]\s*", "", title).strip()  # Remove leading dashes/underscores

    # Determine media type
    media_type = "unknown"
    if anime_group or anime_ep:
        media_type = "anime"
    elif tv_match:
        media_type = "tv_show"
    elif year:
        media_type = "movie"

    print(f"Title (all matched outputs before this removed): {title}")
    print(f"Is Anime: {anime_group is not None or anime_ep is not None}, Anime group: {anime_group}, Anime ep: {anime_ep}")
    print(f"Is TV: {tv_match is not None}, TV match: {tv_match}")
    print(f"Is Movie: {year is not None and media_type == 'movie'}, Movie Year: {year}")
    print(f"title: {title} year: {year} media_type: {media_type}")
    print(f"Right after split: {right}")
    print("=" * 80)

    return {
        "original": name,
        "title": title,
        "resolution": resolution,
        "anime_group": anime_group,
        "anime_ep": anime_ep,
        "tv_match": tv_match,
        "year": year,
        "media_type": media_type,
        "notes": notes,
    }


# --- Test harness ---
if __name__ == "__main__":
    samples = [
        "One.Piece.S01E1116.Lets.Go.Get.It!.Buggys.Big.Declaration.2160p.B-Global.WEB-DL.JPN.AAC2.0.H.264.MSubs-ToonsHub.mkv",
        "Stranger Things S04 2160p",
        "One-piece-ep.1080-v2-1080p-raws",
        "S.W.A.T.2017.S08E01.720p.HDTV.x264-SYNCOPY[TGx]",
        "S.H.I.E.L.D.s01",
        "9-1-1 s02-s03",
        "TV Show season 1 s01 1080p x265 DVD extr",
        "Pawn Stars -- 4x13 -- Broadsiding Lincoln.mkv",
        "www.Torrenting.com   -    14.Peaks.Nothing.Is.Impossible.2021.1080p.WEB.h264-RUMOUR",
        "www.SceneTime.com - Taken 3 2014 1080p DSNP WEB-DL DDP 5 1 H 264-PiRaTeS",
        "[SubsPlease] Tearmoon Teikoku Monogatari - 01 (1080p) [15ADAE00].mkv",
        "[SubsPlease] Fairy Tail - 100 Years Quest - 05 (1080p) [1107F3A9].mkv",
        "[Erai-raws] Tearmoon Teikoku Monogatari - 01 [1080p][ENG][POR-BR].mkv",
        "Hunter x Hunter (2011) - 01 [1080p][ENG][FRE]",
        "Naruto Shippuden (001-500) [Complete Series + Movies]",
        "[Erai-raws] Sword Art Online - 10 [720p][Multiple Subtitle].mkv",
        "[Exiled-Destiny]_Tokyo_Underground_Ep02v2_(41858470).mkv",
        "Some.Movie.2023.1920x1080.WEB.mkv",
    ]

    # Create output filename with current date and time
    from datetime import datetime
    now = datetime.now()
    output_filename = f"output_{now.strftime('%m%d_%H%M')}.txt"
    
    # Redirect output to file
    import sys
    original_stdout = sys.stdout
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        sys.stdout = f
        for s in samples:
            parse_filename(s)
        sys.stdout = original_stdout
    
    print(f"Output saved to {output_filename}")
    
    # Also print to console
    for s in samples:
        parse_filename(s)
```

Key changes made:

1. **TV Show Detection Improvements**:
   - Added support for `XXxYY` format (like `4x13`)
   - Added support for `season X` format
   - Added support for season ranges like `s02-s03`
   - TV extraction now happens before anime episode extraction to prioritize TV format

2. **Acronym Preservation**:
   - Added logic to preserve acronyms like `S.H.I.E.L.D.` and `9-1-1` by removing dots between uppercase letters and hyphens between numbers

3. **Anime Episode Extraction Fix**:
   - Made episode matching more restrictive to avoid false positives (added negative lookbehind to prevent matching numbers at the very beginning)
   - Added priority for TV format over anime format

4. **Year Extraction Improvement**:
   - Made year matching more restrictive with word boundaries to avoid false positives

5. **Better Title Cleaning**:
   - Improved the title cleaning process to handle various TV show formats
   - Added specific handling for different TV match types

These changes should address the issues you identified with TV show detection, acronym preservation, and false positive episode matching.