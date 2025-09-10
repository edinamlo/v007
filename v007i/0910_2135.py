import re

# --- Extractors ---

def extract_resolution(name):
    match = re.search(r"(\d{3,4}p|\d{3,4}x\d{3,4})", name, re.I)
    if match:
        print(f"[ResolutionExtractor] Matched: {match.group(1)}")
        return match.group(1), "found resolution"
    return None, None


def extract_year(name):
    match = re.search(r"(19\d{2}|20\d{2})", name)
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
    
    # If still no matches, try standalone episode numbers
    if not matches:
        matches = list(re.finditer(r"[\s\-_.](\d{2,3})(?:v\d+)?(?=\s|\[|\(|$|\.)", name))
    
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
    match = re.search(r"S(\d{2})E(\d{2})", name, re.I)
    if match:
        print(f"[TVExtractor] Matched season {match.group(1)}, episode {match.group(2)}")
        return (int(match.group(1)), int(match.group(2))), f"found tv match: S{match.group(1)}E{match.group(2)}"
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

    # 4. Episode extraction (right-to-left search) from SPLIT_LEFT
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
    
    # TV show extraction if no anime episode found
    tv_match, tv_note = None, None
    if not anime_ep:
        tv_match, tv_note = extract_tv(left)
        if tv_note:
            notes.append(tv_note)
            # Move everything after TV match to SPLIT_RIGHT
            if tv_match:
                tv_str = f"S{tv_match[0]:02d}E{tv_match[1]:02d}"
                tv_pos = left.find(tv_str)
                if tv_pos != -1:
                    content_after_tv = left[tv_pos + len(tv_str):].strip()
                    if content_after_tv:
                        right = content_after_tv + (' ' + right if right else '')
                        left = left[:tv_pos].strip()

    # 5. Clean title extraction
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
        season, episode = tv_match
        title = re.sub(rf"\s*S{season:02d}E{episode:02d}\s*", "", title, flags=re.I)
    
    # Remove year if found
    if year:
        title = re.sub(rf"\s*{year}\s*", "", title)
    
    # Final title cleaning - remove website URLs, common prefixes, and unwanted text
    title = re.sub(r"(www\.|https?://)[^\s]+", "", title, flags=re.I)
    title = re.sub(r"\b(?:download|torrent|free|full|movie|series|episode|season)\b", "", title, flags=re.I)
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
