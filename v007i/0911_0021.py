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
        return int(match.group(1)), f"found movie year: {match.group(1)}", match.group(0)
    return None, None, None


def extract_anime_group(name):
    match = re.match(r"^\[(.*?)\]", name)
    if match:
        print(f"[AnimeGroupExtractor] Matched: {match.group(1)}")
        return match.group(1), f"found release group: {match.group(1)}", match.group(0)
    return None, None, None


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
        return ep_str, f"found anime episode: {ep_str}", last_match.group(0)
    return None, None, None

def extract_tv(name):
    # Match season range format first (like s02-s03)
    match = re.search(r"s(\d{2})-s(\d{2})", name, re.I)
    if match:
        season_start, season_end = int(match.group(1)), int(match.group(2))
        print(f"[TVExtractor] Matched season range {season_start}-{season_end}")
        return (f"{season_start}-{season_end}", None), f"found tv season range: s{season_start}-s{season_end}", match.group(0)
    
    # Match SXXEYY format (more restrictive to avoid matching long numbers)
    # Use lookahead to ensure we don't match too many digits
    match = re.search(r"S(\d{1,2})E(\d{1,2})(?=\D|$)", name, re.I)
    if match:
        season, episode = int(match.group(1)), int(match.group(2))
        print(f"[TVExtractor] Matched season {season}, episode {episode}")
        return (season, episode), f"found tv match: S{season:02d}E{episode:02d}", match.group(0)
    
    # Match XXxYY format (like 4x13)
    match = re.search(r"(\d{1,2})x(\d{1,2})", name, re.I)
    if match:
        season, episode = int(match.group(1)), int(match.group(2))
        print(f"[TVExtractor] Matched season {season}, episode {episode} (x format)")
        return (season, episode), f"found tv match: {season}x{episode}", match.group(0)
    
    # Match season XX format (single season)
    match = re.search(r"(?:season|s)(\d{2})(?!-s\d{2})", name, re.I)
    if match:
        season = int(match.group(1))
        print(f"[TVExtractor] Matched season {season}")
        return (season, None), f"found tv season: {season}", match.group(0)
    
    return None, None, None

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
    anime_group, note, anime_group_pattern = extract_anime_group(left)
    if not anime_group:
        anime_group, note, anime_group_pattern = extract_anime_group(right)
    
    if note:
        notes.append(note)
        # Clean anime group from left side if found
        if anime_group and anime_group_pattern and left.startswith(anime_group_pattern):
            left = re.sub(re.escape(anime_group_pattern), "", left, 1).strip()
            print(f"SPLIT_LEFT after anime group removal: {left}")

    # 3. TV show extraction (before episode extraction to prioritize TV format)
    tv_match, tv_note, tv_pattern = extract_tv(left)
    if tv_note:
        notes.append(tv_note)
        # Move everything after TV match to SPLIT_RIGHT
        if tv_match and tv_pattern:
            tv_pos = left.find(tv_pattern)
            if tv_pos != -1:
                content_after_tv = left[tv_pos + len(tv_pattern):].strip()
                if content_after_tv:
                    right = content_after_tv + (' ' + right if right else '')
                    left = left[:tv_pos].strip()

    # 4. Year extraction from SPLIT_LEFT
    year, year_note, year_pattern = extract_year(left)
    if year_note:
        notes.append(year_note)
        # Move everything after year to SPLIT_RIGHT
        if year and year_pattern:
            year_pos = left.find(year_pattern)
            if year_pos != -1:
                content_after_year = left[year_pos + len(year_pattern):].strip()
                if content_after_year:
                    right = content_after_year + (' ' + right if right else '')
                    left = left[:year_pos].strip()

    # 5. Episode extraction (right-to-left search) from SPLIT_LEFT
    # Only extract anime episodes if no TV match was found and it's not a year
    anime_ep, note, anime_ep_pattern = None, None, None
    if not tv_match:
        anime_ep, note, anime_ep_pattern = extract_anime_episode(left)
        # Don't extract anime episode if it matches a year pattern
        if anime_ep_pattern and year_pattern and anime_ep_pattern == year_pattern:
            anime_ep, note, anime_ep_pattern = None, None, None
        
        if note:
            notes.append(note)
            # Move everything after episode to SPLIT_RIGHT
            if anime_ep and anime_ep_pattern:
                ep_pos = left.find(anime_ep_pattern)
                if ep_pos != -1:
                    # Move content after episode to SPLIT_RIGHT
                    content_after_ep = left[ep_pos + len(anime_ep_pattern):].strip()
                    if content_after_ep:
                        right = content_after_ep + (' ' + right if right else '')
                        left = left[:ep_pos].strip()

    # 6. Clean title extraction
    title = left.strip()
    
    # Remove episode number if found
    if anime_ep and anime_ep_pattern:
        title = re.sub(re.escape(anime_ep_pattern), "", title, flags=re.I)
        # Clean up any remaining dashes or separators
        title = re.sub(r"\s*-\s*$", "", title)
    
    # Remove TV season/episode if found
    if tv_match and tv_pattern:
        title = re.sub(re.escape(tv_pattern), "", title, flags=re.I)
    
    # Remove year if found
    if year and year_pattern:
        title = re.sub(re.escape(year_pattern), "", title)
    
    # Final title cleaning - remove website URLs, common prefixes, and unwanted text
    title = re.sub(r"(www\.|https?://)[^\s]+", "", title, flags=re.I)
    title = re.sub(r"\b(?:download|torrent|free|full|movie|series|episode|season)\b", "", title, flags=re.I)
    
    # Preserve acronyms (S.H.I.E.L.D., 9-1-1, etc.)
    # Don't break acronyms - instead, clean them properly
    title = re.sub(r"([A-Z])\.([A-Z])", r"\1.\2", title)  # Keep dots between uppercase letters
    title = re.sub(r"(\d)-(\d)", r"\1-\2", title)  # Keep hyphens between numbers
    
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
        "S.W.A.T.2017.S08E01.720p.HDTV.x264-SYNCOPY[TGx]",
        "S.H.I.E.L.D.s01",
        "9-1-1 s02-s03",
        "Pawn Stars -- 4x13 -- Broadsiding Lincoln.mkv",
        "One.Piece.S01E1116.Lets.Go.Get.It!.Buggys.Big.Declaration.2160p.B-Global.WEB-DL.JPN.AAC2.0.H.264.MSubs-ToonsHub.mkv",
        "Stranger Things S04 2160p",
        "One-piece-ep.1080-v2-1080p-raws",
        "www.Torrenting.com   -    14.Peaks.Nothing.Is.Impossible.2021.1080p.WEB.h264-RUMOUR",
        "www.SceneTime.com - Taken 3 2014 1080p DSNP WEB-DL DDP 5 1 H 264-PiRaTeS",
        "[SubsPlease] Tearmoon Teikoku Monogatari - 01 (1080p) [15ADAE00].mkv",
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