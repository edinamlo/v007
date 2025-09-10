import re
from typing import Tuple, Optional

def extract_title_and_year(filename: str) -> Tuple[str, Optional[int]]:
    """
    Extract title and year from filename - preserve original structure when no clear patterns.
    """
    # Remove file extension if it looks like one
    common_extensions = ['mkv', 'mp4', 'avi', 'mov', 'mpg', 'mpeg', 'srt', 'torrent', 'wav', 'flac', 'mkv', 'm4v']
    if '.' in filename:
        ext = filename.rsplit('.', 1)[-1].lower()
        if ext in common_extensions:
            filename = '.'.join(filename.rsplit('.', 1)[:-1])
    
    # Extract year with multiple patterns
    year = None
    year_pos = len(filename)
    
    # Try different year patterns
    year_patterns = [
        (r'(?:^|[-._\s\(])(\d{4})(?:[-._\s\)\[\]]|$)', 1),  # Standard
        (r'\((\d{4})\)', 1),  # Parentheses  
        (r'\[(\d{4})\]', 1),  # Brackets
    ]
    
    for pattern, group in year_patterns:
        matches = list(re.finditer(pattern, filename))
        for match in matches:
            try:
                year_val = int(match.group(group))
                if 1900 <= year_val <= 2030 and match.start(group) < year_pos:
                    year = year_val
                    year_pos = match.start(group)
            except (ValueError, IndexError):
                continue
    
    # Extract title portion - everything before the year
    if year is not None and year_pos < len(filename):
        title_part = filename[:year_pos]
        # Remove trailing separators
        title_part = re.sub(r'[-._\s]+$', '', title_part)
    else:
        title_part = filename
    
    # Print the possible title before cleaning (for debugging)
    # print(f"Possible title before cleaning: '{title_part}'")
    
    # Clean title only when clear patterns are found
    title = clean_title_selective(title_part, year is not None)
    
    return title, year

def clean_title_selective(title: str, has_year: bool) -> str:
    """
    Selective cleaning - only clean when we find clear patterns.
    """
    original = title
    
    # Handle S.W.A.T.2017 specifically
    swat_match = re.match(r'^([A-Z](?:\.[A-Z])+)(\d{4})', title)
    if swat_match:
        return swat_match.group(1) + "."
    
    # Handle pure acronyms that look complete
    acronym_match = re.match(r'^([A-Z](?:\.[A-Z])+)\.?$', title)
    if acronym_match:
        return acronym_match.group(1) + "."
    
    # Work with a copy for cleaning
    cleaned_title = title
    
    # Only do aggressive cleaning if we detected a year (metadata likely present)
    if has_year:
        # Remove website prefixes
        cleaned_title = re.sub(r'^(?:www\.)?[a-zA-Z0-9.-]+\s*[-_.]*\s*', '', cleaned_title, count=1, flags=re.IGNORECASE)
        
        # Remove group tags at start
        cleaned_title = re.sub(r'^[\[\(][^\]\)]*[\]\)]\s*', '', cleaned_title, count=1)
        cleaned_title = re.sub(r'^【[^】]*】\s*', '', cleaned_title, count=1)
        cleaned_title = re.sub(r'^★[^★]*★\s*', '', cleaned_title, count=1)
        
        # Remove season/episode patterns more carefully - only at the end
        cleaned_title = re.sub(r'[-._\s]+(?:S\d{1,2}E\d{1,2}|s\d{1,2}e\d{1,2}|Season\s*\d+|season\s*\d+|Episode\s*\d+|Ep\.?\s*\d+)[\s\S]*$', '', cleaned_title, flags=re.IGNORECASE)
        
        # Remove common metadata tags more carefully - only at the end
        metadata_pattern = r'[-._\s]*(?:1080p|720p|2160p|4K|HDRip|BRRip|BluRay|WEBRip|HDTV|x264|x265|HEVC|AAC|HDR|DVDRip|WEB-DL|H264|DTS|AC3|PPV|YIFY|RARBG)[\s\S]*$'
        cleaned_title = re.sub(metadata_pattern, '', cleaned_title, flags=re.IGNORECASE)
        
        # Convert separators but preserve structure
        cleaned_title = re.sub(r'[-_]+', ' ', cleaned_title)  # Convert dashes/underscores to spaces
        
        # Handle meaningful dots (like Mr. Nobody) - but be careful
        cleaned_title = re.sub(r'([a-zA-Z])\.([A-Z])', r'\1. \2', cleaned_title)  # Mr.Nobody -> Mr. Nobody
        cleaned_title = re.sub(r'\.{2,}', '.', cleaned_title)  # Multiple dots to single
        
        # Clean up multiple spaces
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title)
        
        # Clean edges
        cleaned_title = cleaned_title.strip(' .-')
        
        # If we over-cleaned, fall back to more conservative approach
        if len(cleaned_title) < 3 and len(original) > 3:
            cleaned_title = re.sub(r'[-._]+', ' ', original)
            cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()
    else:
        # No year detected - do minimal cleaning
        # Only convert obvious separators, preserve original structure
        cleaned_title = re.sub(r'[-_]+', ' ', cleaned_title)  # Convert dashes/underscores to spaces
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title)    # Clean up multiple spaces
        
        # Handle meaningful dots (like Mr. Nobody)
        cleaned_title = re.sub(r'([a-zA-Z])\.([A-Z])', r'\1. \2', cleaned_title)  # Mr.Nobody -> Mr. Nobody
        
        cleaned_title = cleaned_title.strip()
    
    return cleaned_title

    


# Test the key cases
# Test the key cases
test_key = [
    "La.famille.bélier",
    "La.famille.bélier.1995.FRENCH.1080p.BluRay.x264-LOST",
    "Mr. Nobody", 
    "Mr. Nobody (2009) 1080p BluRay x264-AMIABLE",
    "S.W.A.T.2017.S08E01.720p.HDTV.x264-SYNCOPY[TGx]",
    "S.W.A.T.2017.1080p.BluRay.x264.AAC.HDR",
    "Despicable.Me.4.2024.D.TELESYNC_14OOMB.avi",
    "Despicable.Me.4.2024.1080p.WEBRip.x264.AAC.YIFY",
    "La famille bélier",
    "La famille bélier (1995)",
    "The.Movie.Title.2020.1080p.BluRay.x264-RARBG",
    "Movie.Title.2019.HDRip",
    "[GROUP] Some.Film.2021.720p.WEBRip",
    "A.B.C.1999.DVDRip",
    "Game.of.Thrones.S01E01.1080p.BluRay.x264-ROVERS",
    "Friends.S10E12.720p.HDTV.X264-DIMENSION",
    "UFC.247.PPV.Jones.vs.Reyes.HDTV.x264-PUNCH[TGx]",
    "One.Piece.S01E1116.Lets.Go.Get.It!.Buggys.Big.Declaration.2160p.B-Global.WEB-DL.JPN.AAC2.0.H.264.MSubs-ToonsHub.mkv",
    "Stranger.Things.S04.2160p.WEBRip",
    "Doctor.Who.2005.8x12.Death.In.Heaven.720p.HDTV.x264-FOV",
    "[NC-Raws] 间谍过家家 / SPY×FAMILY - 04 (B-Global 1920x1080 HEVC AAC MKV)",
    "www.Torrenting.com   -    Anatomy.Of.A.Fall.2023.1080p.WEB.h264-RUMOUR",
    "The.Great.Indian.Suicide.2023.Tamil.TRUE.WEB-DL.4K.SDR.HEVC.3.2GB.ESub.mkv",
    "Pawn.Stars.S09E13.1080p.HEVC.x265-MeGusta",
    "Jurassic.World.Dominion.CUSTOM.EXTENDED.2022.2160p.MULTi.VF2.UHD.Blu-ray.REMUX.HDR.DoVi.HEVC.DTS-X.DTS-HDHRA.7.1-MOONLY.mkv",
    "GTO.(Great.Teacher.Onizuka).(Ep.1-43).Sub.480p.lakshay",
    "Naruto.Shippuden.(001-500).[Complete.Series.+.Movies].(Dual.Audio)",
    "The.Mandalorian.S01E01.Chapter.1.1080p.Web-DL.mkv",
    "9-1-1.s02",
    "S.H.I.E.L.D.s01",
    "One-piece-ep.1080-v2-1080p-raws",
    "Yurusarezaru_mono2.srt",
    "Too.Many.Cooks._.Adult.Swim.mp4",
    "Wonder.Woman.1984.(2020).[UHDRemux.2160p.DoVi.P8.Es-DTSHD.AC3.En-AC3].mkv",
    "The.French.Connection.1971.Remastered.BluRay.1080p.REMUX.AVC.DTS-HD.MA.5.1-LEGi0N",
    "STEVE.martin.a.documentary.in.2.pieces.S01.COMPLETE.1080p.WEB.H264-SuccessfulCrab[TGx]"
]

print("Testing comprehensive cases:")
for test in test_key:
    title, year = extract_title_and_year(test)
    print(f"'{test}' -> '{title}', Year: {year}")