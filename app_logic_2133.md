Absolutely! Here’s a **clear, concise summary** of what your parser **needs to do** and **what it finds** — perfect for documentation, onboarding, or your own reference.

---

# 🎯 FILENAME PARSER — SUMMARY

## ✅ WHAT IT NEEDS TO DO

Parse messy, real-world media filenames (TV, anime, movies) and extract:

1. **Clean, human-readable title**  
   → Strip junk: websites, groups, codecs, resolutions, years, episode tags.  
   → Preserve casing, handle multi-language titles (e.g., `Russian / English` → pick best).  
   → Normalize Unicode, full-width chars, separators.

2. **Detect media type**  
   → Classify as: `"tv"`, `"anime"`, `"movie"`, or `"unknown"`.

3. **Extract structured metadata clues**  
   → TV: Season/episode codes (`S01E02`, `3x12`, `season 3`)  
   → Anime: Episode/range codes (`ep.1080`, `[01]`, `001-500`, `chapter 1`)  
   → Movie: Release year (`2023`, `1997`) — only if no TV/anime clues nearby  
   → Extras: Resolution (`1080p`), codec (`x265`), audio (`aac`), source (`bluray`)

4. **Respect context & boundaries**  
   → Right-to-left parsing: Use the **rightmost** TV/anime clue as boundary for title.  
   → Ignore years if TV/anime patterns are nearby.  
   → Anime groups (e.g., `[Erai-raws]`) force anime classification.

5. **Handle edge cases**  
   → Ordinal seasons: `3rd Season`, `1st season` → `S03`, `S01`  
   → Compact formats: `8x12`, `4x13` → `S08E12`  
   → Ranges: `001-500` → `EP001-500` (anime)  
   → Multi-pass cleaning: Strip clues, then re-scan for more.

6. **Output consistent structure**  
   → Always return same dict keys, even if empty.

---

## 🔍 WHAT IT FINDS (OUTPUT STRUCTURE)

```python
{
    "original": str,          # Original filename
    "media_type": str,        # "tv" | "anime" | "movie" | "unknown"
    "possible_title": str,    # Raw title before final cleaning
    "clean_title": str,       # Final cleaned, display-ready title
    "tv_clues": List[str],    # e.g., ["S01E02", "S03", "S08E12"]
    "anime_clues": List[str], # e.g., ["EP1080", "EP001-500", "EP02"]
    "movie_clues": List[str], # e.g., ["2023", "1997"]
    "extras_bits": List[str], # e.g., ["1080p", "x265", "bluray", "aac"]
    "words": List[str],       # Leftover tokens (release groups, misc)
    "matched_clues": Dict,    # Structured matched keywords from config.CLUES
    "resolution_clues": List[str],  # Convenience alias
    "audio_clues": List[str],       # Convenience alias
    "quality_clues": List[str],     # Convenience alias
    "release_groups": List[str],    # Convenience alias
    "misc_clues": List[str],        # Convenience alias
}
```

---

## 🧩 DETECTION RULES (SIMPLIFIED)

| Pattern Example             | Detected As      | Clue Output        | Media Type |
|-----------------------------|------------------|--------------------|------------|
| `S01E02`, `s1e2`            | TV Episode       | `S01E02`           | tv         |
| `season 3`, `3rd season`    | TV Season        | `S03`              | tv         |
| `8x12`, `4x13`              | TV Compact       | `S08E12`           | tv         |
| `ep.1080`, `e12`, `episode 5` | Anime Episode  | `EP1080`, `EP012`  | anime      |
| `chapter 1`                 | Context-Based    | `EP001`            | anime*     |
| `001-500`, `01-26`          | Anime Range      | `EP001-500`        | anime      |
| `(2023)`                    | Movie Year       | `2023`             | movie      |
| `[Erai-raws] ... - 02`      | Forces Anime     | `EP002`            | anime      |
| `One Piece`, `Naruto`       | Heuristic Anime  | —                  | anime      |
| `Game of Thrones`, `UFC`    | Heuristic TV     | —                  | tv         |

> *`chapter` → anime if from anime group or standalone; else → tv

---

## 🧠 LOGIC FLOW (SIMPLIFIED)

1. **Strip prefixes** (websites, groups) → detect if anime group → set `anime_set`.
2. **Scan tokens right-to-left** → find TV/anime/year patterns.
3. **Classify matches**:
   - Range? Standalone `ep.`? → likely anime.
   - Has `season` or `sxx`? → likely TV.
   - Near `anime_set` or anime keyword? → anime.
4. **Set boundary** at rightmost TV/anime clue → everything left = title.
5. **Multi-pass**: Strip found clues → re-scan → extract more.
6. **Final clean**: Normalize, split languages, remove separators.
7. **Set media_type**:
   - `anime` if `anime_set` or `anime_clues`
   - `tv` if `tv_clues`
   - `movie` if `movie_clues`
   - Override with heuristics (`"One Piece" → anime`, `"UFC" → tv`)

---

## 🧪 EXAMPLES

| Filename                                                  | Clean Title             | Media Type | Clues                     |
|-----------------------------------------------------------|--------------------------|------------|---------------------------|
| `doctor_who_2005.8x12.death_in_heaven...`                 | `doctor who`             | tv         | `S08E12`                  |
| `[Erai-raws] Kingdom 3rd Season - 02 [1080p].mkv`         | `Kingdom`                | anime      | `S03E02`                  |
| `One-piece-ep.1080-v2-1080p-raws.mkv`                     | `One piece`              | anime      | `EP1080`                  |
| `Naruto Shippuden (001-500) [Complete...]`                | `Naruto Shippuden`       | anime      | `EP001-500`               |
| `The.Mandalorian.S01E01.Chapter.1.1080p...`               | `The Mandalorian`        | tv         | `S01E01`                  |
| `www.Torrenting.com - Anatomy Of A Fall (2023).mkv`        | `Anatomy Of A Fall`      | movie      | `2023`                    |
| `S.W.A.T.2017.S08E01.720p...`                             | `S.W.A.T`                | tv         | `S08E01`                  |
| `9-1-1 s02-s03`                                           | `9-1-1`                  | tv         | `S02`, `S03`              |

---

## 📌 KEY STRENGTHS

- ✅ **Robust TV/anime detection** — handles ordinals, compact, ranges, chapters.
- ✅ **Context-aware** — ignores years near TV tags, respects anime groups.
- ✅ **Right-to-left boundary** — picks latest (rightmost) clue for accurate title split.
- ✅ **Multi-language & Unicode safe** — no unwanted case changes.
- ✅ **Extensible** — easy to add new keywords, patterns, or media types.

---

## 🚀 USE CASES

- Media library organization
- File renaming tools
- Torrent/P2P metadata extraction
- Database ingestion pipelines
- Frontend display title generation

---

Let me know if you’d like this as a **Markdown doc**, **PDF**, or want to add **unit test cases** or **logging hooks**! You’ve got a production-grade parser now. 🏆