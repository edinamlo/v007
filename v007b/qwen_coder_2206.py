import re
from typing import Tuple, Optional

def extract_title_and_year(filename: str) -> Tuple[str, Optional[int]]:
    """
    Extract title and year from filename with comprehensive pattern handling.
    """
    original_filename = filename
    
    # Remove file extension
    filename = re.sub(r'\.[^.]+$', '', filename)
    
    # Extract year first
    year = None
    year_pos = len(filename)
    
    # Multiple year patterns to try
    year_patterns = [
        r'(?:^|[-._\s\[\(])(\d{4})(?:[-._\s\]\)]|$)',  # Standard year patterns
        r'\((\d{4})\)',  # Year in parentheses
        r'\[(\d{4})\]',  # Year in brackets
    ]
    
    for pattern in year_patterns:
        matches = list(re.finditer(pattern, filename))
        for match in matches:
            year_val = int(match.group(1))
            if 1900 <= year_val <= 2030:
                # Use the first valid year found (not necessarily the earliest)
                if year is None or match.start(1) < year_pos:
                    year = year_val
                    year_pos = match.start(1)
                break
        if year:
            break
    
    # Extract title portion
    if year_pos < len(filename):
        title_candidate = filename[:year_pos].strip()
        # Remove trailing separators
        title_candidate = re.sub(r'[-._\s]+$', '', title_candidate)
    else:
        title_candidate = filename
    
    # Clean the title
    title = clean_title(title_candidate, original_filename)
    
    return title, year

def clean_title(title: str, original_filename: str) -> str:
    """
    Comprehensive title cleaning with multiple pattern handling.
    """
    # Store original for reference
    original = title
    
    # Handle specific patterns first
    
    # Handle acronym patterns like S.W.A.T.2017
    acronym_year_pattern = r'^([A-Z](?:\.[A-Z])+)(\d{4})'
    acronym_year_match = re.match(acronym_year_pattern, title)
    if acronym_year_match:
        return acronym_year_match.group(1)
    
    # Handle pure acronym at start
    pure_acronym_pattern = r'^([A-Z](?:\.[A-Z])+)\.?$'
    pure_acronym_match = re.match(pure_acronym_pattern, title)
    if pure_acronym_match:
        return pure_acronym_match.group(1)
    
    # Remove website prefixes
    title = re.sub(r'^(?:www\.)?[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)+\s*[-_]*\s*', '', title, flags=re.IGNORECASE)
    
    # Remove group tags and brackets at start
    title = re.sub(r'^[\[\(][^\]\)]*[\]\)]\s*', '', title)
    
    # Remove Chinese/Korean/Japanese group tags
    title = re.sub(r'^【[^】]*】\s*', '', title)
    title = re.sub(r'^★[^★]*★\s*', '', title)
    
    # Handle multi-language titles separated by slashes
    slash_titles = re.split(r'\s*/\s*', title)
    if len(slash_titles) > 1:
        # Prefer English titles or the first non-Chinese title
        for t in slash_titles:
            # Check if it contains mostly Latin characters
            latin_chars = len(re.findall(r'[a-zA-Z]', t))
            total_chars = len(re.findall(r'[^\s]', t))
            if total_chars > 0 and latin_chars / total_chars > 0.5:
                title = t.strip()
                break
        else:
            # If no clear English title, use the first one
            title = slash_titles[0].strip()
    
    # Remove episode/season info
    title = re.sub(r'[-._\s]*(?:S\d{1,2}E\d{1,2}|Season\s*\d+|Episode\s*\d+|Ep\.\s*\d+|E\d{1,2})[-._\s]*', '', title, flags=re.IGNORECASE)
    
    # Remove quality/encoding info
    quality_patterns = [
        r'[-._\s]*(?:HDRip|BRRip|BluRay|WEBRip|HDTV|x264|x265|HEVC|AAC|HDR|DVDRip|HD|SD|4K|1080p|720p|480p|2160p|WEB-DL|H264|H265|AVC|DTS|AC3|DDP|DD).*$', 
        r'[-._\s]*(?:EXTENDED|DIRECTORS|UNRATED|REMASTERED|THEATRICAL|FINAL|EDITION|COMPLETE|INTEGRAL|MULTI|DUAL|AUDIO|SUB|SUBS|ESUB|VOSTFR|TRUE|HQ|CUSTOM).*$', 
        r'[-._\s]*(?:REMUX|UHD|DoVi|P8|DTSHD|MA|LEGi0N|BMTH|FTMVHD|MeGusta|SYNCOPY|TGx|RUMOUR|ToonsHub|SuccessfullCrab).*$', 
    ]
    
    for pattern in quality_patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    
    # Remove torrent/site specific tags
    title = re.sub(r'[-._\s]*\[?[TGx|TGz]+\]?$', '', title, flags=re.IGNORECASE)
    
    # Handle special characters and spacing
    title = re.sub(r'[-._\s]+', ' ', title)
    
    # Handle common title patterns
    title = re.sub(r'\s*\(\s*[^)]*\)\s*$', '', title)  # Remove trailing parentheses
    title = re.sub(r'\s*\[\s*[^\]]*\]\s*$', '', title)  # Remove trailing brackets
    
    # Handle numbered titles
    title = re.sub(r'^(\d+)[._-]', r'\1 ', title)  # Handle numbered episodes like "01.Movie"
    
    # Clean up extra whitespace
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Handle special cases
    if title.lower().startswith('ufc'):
        # UFC titles often have specific format
        title = re.sub(r'[-._\s]+', ' ', title)
    
    # Final cleanup
    title = title.strip(' .-_')
    
    return title

# Test function
def test_cases():
    TEST_CASES = [
        ("La famille bélier", "La famille bélier"),
        ("La.famille.bélier", "La famille bélier"),
        ("Mr. Nobody", "Mr. Nobody"),
        ("doctor_who_2005.8x12.death_in_heaven.720p_hdtv_x264-fov", "doctor who"),
        ("[GM-Team][国漫][太乙仙魔录 灵飞纪 第3季][Magical Legend of Rise to immortality Ⅲ][01-26][AVC][GB][1080P]", "Magical Legend of Rise to immortality Ⅲ"),
        ("【喵萌奶茶屋】★01月新番★[Rebirth][01][720p][简体][招募翻译]", "Rebirth"),
        ("【喵萌奶茶屋】★01月新番★[別對映像研出手！/Eizouken ni wa Te wo Dasu na！/映像研には手を出すな！][01][1080p][繁體]", "Eizouken ni wa Te wo Dasu na！"),
        ("【喵萌奶茶屋】★01月新番★[別對映像研出手！/Eizouken ni wa Te wo Dasu na！/映像研には手を出すな！][01][1080p][繁體]", "Eizouken ni wa Te wo Dasu na！"),
        ("[Seed-Raws] 劇場版 ペンギン・ハイウェイ Penguin Highway The Movie (BD 1280x720 AVC AACx4 [5.1+2.0+2.0+2.0]).mp4", "Penguin Highway The Movie"),
        ("[SweetSub][Mutafukaz / MFKZ][Movie][BDRip][1080P][AVC 8bit][简体内嵌]", "Mutafukaz / MFKZ"),
        ("[Erai-raws] Kingdom 3rd Season - 02 [1080p].mkv", "Kingdom"),
        ("Голубая волна / Blue Crush (2002) DVDRip", "Blue Crush"),
        ("Жихарка (2007) DVDRip", "Жихарка"),
        ("3 Миссия невыполнима 3 2006г. BDRip 1080p.mkv", "3 Миссия невыполнима 3"),
        ("1. Детские игры. 1988. 1080p. HEVC. 10bit..mkv", "1 Детские игры"),
        ("01. 100 девчонок и одна в лифте 2000 WEBRip 1080p.mkv", "01 100 девчонок и одна в лифте"),
        ("08.Планета.обезьян.Революция.2014.BDRip-HEVC.1080p.mkv", "08 Планета обезьян Революция"),
        ("Американские животные / American Animals (Барт Лэйтон / Bart Layton) [2018, Великобритания, США, драма, криминал, BDRip] MVO (СВ Студия)", "American Animals"),
        ("Греческая смоковница / Griechische Feigen / The Fruit Is Ripe (Зиги Ротемунд / Sigi Rothemund (as Siggi Götз)) [1976, Германия (ФРГ), эротика, комедия, приключения, DVDRip] 2 VO", "Griechische Feigen / The Fruit Is Ripe"),
        ("Греческая смоковница / The fruit is ripe / Griechische Feigen (Siggi Götз) [1976, Германия, Эротическая комедия, DVDRip]", "The fruit is ripe / Griechische Feigen"),
        ("Бастер / Buster (Дэвид Грин / David Green) [1988, Великобритания, Комедия, мелодрама, драма, приключения, криминал, биография, DVDRip]", "Buster"),
        ("(2000) Le follie dell'imperatore - The Emperor's New Groove (DvdRip Ita Eng AC3 5.1).avi", "Le follie dell'imperatore - The Emperor's New Groove"),
        ("[NC-Raws] 间谍过家家 / SPY×FAMILY - 04 (B-Global 1920x1080 HEVC AAC MKV)", "SPY×FAMILY"),
        ("GTO (Great Teacher Onizuka) (Ep. 1-43) Sub 480p lakshay", "GTO (Great Teacher Onizuka)"),
        ("Книгоноши / Кнiганошы (1987) TVRip от AND03AND | BLR", "Кнiганошы"),
        ("Yurusarezaru_mono2.srt", "Yurusarezaru mono2"),
        ("www.1TamilMV.world - Ayalaan (2024) Tamil PreDVD - 1080p - x264 - HQ Clean Aud - 2.5GB.mkv", "Ayalaan"),
        ("www.Torrenting.com   -    Anatomy Of A Fall (2023)", "Anatomy Of A Fall"),
        ("[www.arabp2p.net]_-_تركي مترجم ومدبلج Last.Call.for.Istanbul.2023.1080p.NF.WEB-DL.DDP5.1.H.264.MKV.torrent", "Last Call for Istanbul"),
        ("www.Tamilblasters.sbs - The Great Indian Suicide (2023) Tamil TRUE WEB-DL - 4K SDR - HEVC - (DD+5.1 - 384Kbps & AAC) - 3.2GB - ESub.mkv", "The Great Indian Suicide"),
        ("ww.Tamilblasters.sbs - 8 Bit Christmas (2021) HQ HDRip - x264 - Telugu (Fan Dub) - 400MB].mkv", "8 Bit Christmas"),
        ("www.1TamilMV.pics - 777 Charlie (2022) Tamil HDRip - 720p - x264 - HQ Clean Aud - 1.4GB.mkv", "777 Charlie"),
        ("Despicable.Me.4.2024.D.TELESYNC_14OOMB.avi", "Despicable Me 4"),
        ("UFC.247.PPV.Jones.vs.Reyes.HDTV.x264-PUNCH[TGx]", "UFC 247 Jones vs Reyes"),
        ("[www.1TamilMV.pics]_The.Great.Indian.Suicide.2023.Tamil.TRUE.WEB-DL.4K.SDR.HEVC.(DD+5.1.384Kbps.&.AAC).3.2GB.ESub.mkv", "The Great Indian Suicide"),
        ("Game of Thrones - S02E07 - A Man Without Honor [2160p] [HDR] [5.1, 7.1, 5.1] [ger, eng, eng] [Vio].mkv", "Game of Thrones"),
        ("Pawn.Stars.S09E13.1080p.HEVC.x265-MeGusta", "Pawn Stars"),
        ("Pawn Stars -- 4x13 -- Broadsiding Lincoln.mkv", "Pawn Stars"),
        ("Pawn Stars S04E19 720p WEB H264-BeechyBoy mp4", "Pawn Stars"),
        ("Jurassic.World.Dominion.CUSTOM.EXTENDED.2022.2160p.MULTi.VF2.UHD.Blu-ray.REMUX.HDR.DoVi.HEVC.DTS-X.DTS-HDHRA.7.1-MOONLY.mkv", "Jurassic World Dominion"),
        ("www.Torrenting.com   -    14.Peaks.Nothing.Is.Impossible.2021.1080p.WEB.h264-RUMOUR", "14 Peaks Nothing Is Impossible"),
        ("Too Many Cooks _ Adult Swim.mp4", "Too Many Cooks"),
        ("О мышах и людях (Of Mice and Men) 1992 BDRip 1080p.mkv", "Of Mice and Men"),
        ("Wonder Woman 1984 (2020) [UHDRemux 2160p DoVi P8 Es-DTSHD AC3 En-AC3].mkv", "Wonder Woman 1984"),
        ("www.TamilBlasters.cam - Titanic (1997)[1080p BDRip - Org Auds - [Tamil + Telugu + Hindi + Eng] - x264 - DD5.1 (448 Kbps) - 4.7GB - ESubs].mkv", "Titanic"),
        ("S.W.A.T.2017.S08E01.720p.HDTV.x264-SYNCOPY[TGx]", "S.W.A.T."),
        ("Grimm.INTEGRAL.MULTI.COMPLETE.BLURAY-BMTH", "Grimm"),
        ("Friends.1994.INTEGRALE.MULTI.1080p.WEB-DL.H265-FTMVHD", "Friends"),
        ("STEVE.martin.a.documentary.in.2.pieces.S01.COMPLETE.1080p.WEB.H264-SuccessfulCrab[TGx]", "STEVE martin a documentary in 2 pieces"),
        ("The Lockerbie Bombing (2013) Documentary HDTVRIP", "The Lockerbie Bombing"),
        ("The French Connection 1971 Remastered BluRay 1080p REMUX AVC DTS-HD MA 5 1-LEGi0N", "The French Connection"),
        ("The.Mandalorian.S01E01.Chapter.1.1080p.Web-DL.mkv","The Mandalorian"),
        ("The Mandalorian S02E01 - Chapter 9 (1080p Web-DL).mkv","The Mandalorian"),
        ("TV Show season 1 s01 1080p x265 DVD extr","TV Show"),
        ("9-1-1.s02","9-1-1"),
        ("9-1-1 s02-s03","9-1-1"),
        ("S.H.I.E.L.D.s01","S.H.I.E.L.D."),
        ("One-piece-ep.1080-v2-1080p-raws","One piece"),
        ("Naruto Shippuden (001-500) [Complete Series + Movies] (Dual Audio)","Naruto Shippuden"),
        ("One.Piece.S01E1116.Lets.Go.Get.It!.Buggys.Big.Declaration.2160p.B-Global.WEB-DL.JPN.AAC2.0.H.264.MSubs-ToonsHub.mkv","One Piece"),
        ("Stranger Things S04 2160p","Stranger Things"),
    ]
    
    passed = 0
    failed = 0
    
    for filename, expected_title in TEST_CASES:
        title, year = extract_title_and_year(filename)
        if title == expected_title:
            print(f"✓ '{filename}' -> '{title}'")
            passed += 1
        else:
            print(f"✗ '{filename}' -> Expected: '{expected_title}', Got: '{title}'")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")

# Run tests
test_cases()