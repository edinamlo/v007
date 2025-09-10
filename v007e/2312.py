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
    # Match various episode formats: 01, 02, Ep02, Ep.20, Ep02v2, etc.
    match = re.search(r"(?:\b|_)(?:EP\.?\s?)(\d{2,3})(?:v\d+)?(?:\b|_)", name, re.I)
    if not match:
        match = re.search(r"[\s\-_.](\d{2,3})(?:v\d+)?(?=\s|\[|\(|$|\.)", name)
    if match:
        ep = int(match.group(1))
        print(f"[AnimeEpisodeExtractor] Matched: {ep}")
        return ep, f"found anime episode: {ep}"
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

    # Resolution (split point) - improved split logic
    resolution, note = extract_resolution(name)
    if note:
        notes.append(note)

    left, right = name, ''
    if resolution:
        # Find the position of resolution and split more intelligently
        resolution_pos = name.find(resolution)
        if resolution_pos != -1:
            left = name[:resolution_pos].strip()
            right = name[resolution_pos + len(resolution):].strip()
            
            # Clean up the split - remove trailing/leading punctuation from left/right
            left = re.sub(r'[\s\-_.\(\)\[\]]+$', '', left)
            right = re.sub(r'^[\s\-_.\(\)\[\]]+', '', right)

    # --- LEFT SIDE PARSING ---

    # Anime group extraction (should be done first)
    anime_group, note = extract_anime_group(left)
    if note:
        notes.append(note)

    # Year
    year, note = extract_year(left)
    if note:
        notes.append(note)

    # TV
    tv_match, note = extract_tv(left)
    if note:
        notes.append(note)

    # Anime episode
    anime_ep, note = extract_anime_episode(left)
    if note:
        notes.append(note)

    # Title cleaning (improved)
    title = re.sub(r"[._]+", " ", left).strip()
    # Remove brackets and parentheses from title
    title = re.sub(r"[\[\]\(\)]", "", title).strip()

    # --- ANIME GROUP EXTRACTION FROM RIGHT SIDE (if not found in left) ---
    if not anime_group:
        anime_group, note = extract_anime_group(right)
        if note:
            notes.append(note)

    print(f"Title: {title}")
    print(f"Resolution: {resolution}")
    # Determine if it's anime (more accurate logic)
    is_anime = anime_group is not None or anime_ep is not None
    
    print(f"Is Anime: {is_anime}, Anime group: {anime_group}, Anime ep: {anime_ep}")
    print(f"Is TV: {tv_match is not None}, TV match: {tv_match}")
    print(f"Is Movie: {year is not None and not is_anime and tv_match is None}, Movie Year: {year}")
    print(f"Left after split: {left.strip()}")
    print(f"Right after split: {right.strip()}")
    print("Notes: " + "; ".join(notes))
    print("=" * 80)

    return {
        "original": name,
        "title": title,
        "resolution": resolution,
        "anime_group": anime_group,
        "anime_ep": anime_ep,
        "tv_match": tv_match,
        "year": year,
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

    for s in samples:
        parse_filename(s)
