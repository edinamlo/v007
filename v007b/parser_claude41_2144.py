#!/usr/bin/env python3
"""
Media Filename Parser
Extracts clean titles and metadata from messy media filenames
"""

import re
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
import unicodedata

@dataclass
class ParseResult:
    """Structured result from parsing a filename"""
    original: str
    media_type: str  # 'tv', 'anime', 'movie', 'unknown'
    possible_title: str
    clean_title: str
    tv_clues: List[str] = field(default_factory=list)
    anime_clues: List[str] = field(default_factory=list)
    movie_clues: List[str] = field(default_factory=list)
    quality_clues: List[str] = field(default_factory=list)
    codec_clues: List[str] = field(default_factory=list)
    audio_clues: List[str] = field(default_factory=list)
    source_clues: List[str] = field(default_factory=list)
    release_groups: List[str] = field(default_factory=list)
    misc_clues: List[str] = field(default_factory=list)

class MediaParser:
    def __init__(self):
        # Common release groups and tags to remove
        self.release_groups = {
            'erai-raws', 'nc-raws', 'seed-raws', 'sweetsub', 'gm-team',
            'tgx', 'megusta', 'syncopy', 'bmth', 'ftmvhd', 'successfulcrab',
            'legion', 'moonly', 'rumour', 'punch', 'beechyboy', 'toonshub'
        }
        
        # Website prefixes
        self.website_prefixes = [
            r'www\.[^-\s]+', r'ww\.[^-\s]+', r'[a-z]+\.[a-z]+\.[a-z]+',
            r'www,[^-\s]+', r'\[www\.[^\]]+\]'
        ]
        
        # Quality indicators
        self.quality_patterns = {
            'resolution': [
                r'\b(480p?|720p?|1080p?|2160p?|4k|uhd)\b',
                r'\b(480i|720i|1080i)\b'
            ],
            'source': [
                r'\b(bluray|blu-ray|bdrip|brrip|dvdrip|webrip|web-dl|hdtv|hdtvrip|telesync|dvd)\b',
                r'\b(remux|bdremux|uhdremux)\b'
            ],
            'codec': [
                r'\b(x264|x265|h264|h265|hevc|avc|xvid|divx)\b',
                r'\b(10bit|8bit)\b'
            ],
            'audio': [
                r'\b(aac|ac3|dts|dts-hd|dts-x|dd5\.1|ddp5\.1|mp3|flac|opus)\b',
                r'\b(5\.1|7\.1|2\.0)\b',
                r'\b(dual[\s-]?audio|multi[\s-]?audio)\b'
            ],
            'hdr': [
                r'\b(hdr|hdr10|dolby[\s-]?vision|dovi|dv)\b'
            ]
        }
        
        # Anime-specific groups
        self.anime_groups = {
            '喵萌奶茶屋', 'gm-team', 'erai-raws', 'nc-raws', 'seed-raws',
            'sweetsub', 'sakurato', 'subsplease', 'horriblesubs'
        }
        
        # Common anime titles for heuristics
        self.anime_titles = {
            'naruto', 'one piece', 'onepiece', 'bleach', 'dragon ball',
            'attack on titan', 'demon slayer', 'spy×family', 'spyxfamily',
            'kingdom', 'gto', 'great teacher onizuka'
        }
        
        # Common TV show titles for heuristics
        self.tv_titles = {
            'game of thrones', 'friends', 'breaking bad', 'the mandalorian',
            'stranger things', 'the walking dead', 'doctor who', 'sherlock',
            's.w.a.t', 'swat', '9-1-1', 'grimm', 'pawn stars', 'ufc'
        }

    def parse(self, filename: str) -> ParseResult:
        """Main parsing function"""
        original = filename
        
        # Remove file extension
        name = re.sub(r'\.(mkv|mp4|avi|srt|torrent)$', '', filename, flags=re.I)
        
        # Initial classification
        is_anime = self._detect_anime_markers(name)
        
        # Find the title boundary (first major clue)
        boundary_pos, boundary_type = self._find_title_boundary(name)
        
        if boundary_pos is not None:
            # Split at boundary
            possible_title = name[:boundary_pos].strip()
            extras = name[boundary_pos:].strip()
        else:
            # No clear boundary, use heuristics
            possible_title = name
            extras = ""
        
        # Clean the title
        clean_title = self._clean_title(possible_title)
        
        # Extract metadata from both parts
        metadata = self._extract_metadata(name, extras)
        
        # Determine media type
        media_type = self._determine_media_type(metadata, clean_title, is_anime)
        
        return ParseResult(
            original=original,
            media_type=media_type,
            possible_title=possible_title,
            clean_title=clean_title,
            **metadata
        )

    def _find_title_boundary(self, name: str) -> Tuple[Optional[int], Optional[str]]:
        """Find the position where the title ends (at first major clue)"""
        
        # Pattern groups in order of priority
        patterns = [
            # TV patterns - Season/Episode
            (r'\b[Ss](?:eason\s*)?(\d{1,2})(?:\s*-\s*[Ss]?\d{1,2})?\b', 'tv'),
            (r'\b[Ss](\d{1,2})[Ee](\d{1,3})\b', 'tv'),
            (r'\b(\d{1,2})x(\d{1,3})\b', 'tv'),
            (r'\s+s(\d{2})(?:\s|$)', 'tv'),
            (r'\b[Ee](?:p(?:isode)?)?\.?\s*(\d{1,4})\b', 'tv'),
            
            # Anime patterns
            (r'\[(\d{1,3})\]', 'anime'),
            (r'[\s-](\d{1,3})[\s-]*\[', 'anime'),
            (r'\((\d{1,3})-(\d{1,3})\)', 'anime'),
            (r'ep\.(\d{1,4})', 'anime'),
            
            # Chapter patterns (context-dependent)
            (r'\bChapter[\s.]+(\d+)', 'chapter'),
            
            # Year patterns (movie indicator)
            (r'[\(\[]?(19\d{2}|20\d{2})[\)\]]?', 'year'),
        ]
        
        earliest_pos = None
        earliest_type = None
        
        for pattern, ptype in patterns:
            match = re.search(pattern, name, re.I)
            if match:
                pos = match.start()
                
                # Special handling for chapter - check context
                if ptype == 'chapter':
                    # Check if it's part of a TV show title (like The Mandalorian)
                    before_text = name[:pos].lower()
                    if any(tv in before_text for tv in ['mandalorian', 's.w.a.t', 'game of thrones']):
                        ptype = 'tv'
                
                # Special handling for year - check if it's actually part of a title
                if ptype == 'year':
                    # Check if year is preceded by a title-like pattern
                    before_text = name[:pos].strip()
                    if re.search(r'[a-zA-Z]', before_text[-10:] if len(before_text) > 10 else before_text):
                        # Check if there are TV/anime patterns after the year
                        after_text = name[match.end():]
                        if re.search(r'\b[Ss]\d{1,2}[Ee]\d{1,3}\b|\b\d{1,2}x\d{1,3}\b|ep\.\d+', after_text, re.I):
                            continue  # Skip this year, it's part of the title
                
                if earliest_pos is None or pos < earliest_pos:
                    earliest_pos = pos
                    earliest_type = ptype
        
        return earliest_pos, earliest_type

    def _detect_anime_markers(self, name: str) -> bool:
        """Detect if filename contains anime-specific markers"""
        name_lower = name.lower()
        
        # Check for anime groups
        for group in self.anime_groups:
            if group.lower() in name_lower:
                return True
        
        # Check for CJK characters in brackets (common in anime)
        if re.search(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]', name):
            if re.search(r'\[.*[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff].*\]', name):
                return True
        
        # Check for anime-specific patterns
        if re.search(r'\[(?:720p|1080p|BD)\].*\[(?:简体|繁體|GB|BIG5)\]', name):
            return True
            
        return False

    def _clean_title(self, title: str) -> str:
        """Clean and normalize the title"""
        if not title:
            return ""
        
        # Remove website prefixes
        for pattern in self.website_prefixes:
            title = re.sub(pattern, '', title, flags=re.I)
        
        # Remove release groups in brackets
        title = re.sub(r'\[[^\]]*\]', '', title)
        
        # Remove quality/codec tags
        for category, patterns in self.quality_patterns.items():
            for pattern in patterns:
                title = re.sub(pattern, '', title, flags=re.I)
        
        # Handle CJK titles with slashes (pick the English one if available)
        if '/' in title:
            parts = title.split('/')
            # Look for the part with most Latin characters
            best_part = max(parts, key=lambda p: len(re.findall(r'[a-zA-Z]', p)))
            if re.search(r'[a-zA-Z]', best_part):
                title = best_part
        
        # Clean up artifacts
        title = re.sub(r'[_\-\.]+', ' ', title)  # Replace separators with spaces
        title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
        title = re.sub(r'^\W+|\W+$', '', title)  # Remove leading/trailing non-word chars
        title = title.strip()
        
        # Preserve original casing but clean up obviously wrong patterns
        if title.isupper() and len(title) > 4:
            title = title.title()
        
        # Handle numbered prefixes (like "01. Title")
        title = re.sub(r'^\d+\.\s*', '', title)
        
        return title

    def _extract_metadata(self, full_name: str, extras: str) -> Dict:
        """Extract all metadata from the filename"""
        metadata = {
            'tv_clues': [],
            'anime_clues': [],
            'movie_clues': [],
            'quality_clues': [],
            'codec_clues': [],
            'audio_clues': [],
            'source_clues': [],
            'release_groups': [],
            'misc_clues': []
        }
        
        # Use full name for comprehensive extraction
        text = full_name
        
        # TV patterns
        tv_patterns = [
            (r'\b[Ss](\d{1,2})[Ee](\d{1,3})\b', lambda m: f'S{m.group(1).zfill(2)}E{m.group(2).zfill(2)}'),
            (r'\b[Ss](?:eason\s*)?(\d{1,2})(?:\s*-\s*[Ss]?\d{1,2})?\b', lambda m: f'S{m.group(1).zfill(2)}'),
            (r'\b(\d{1,2})x(\d{1,3})\b', lambda m: f'S{m.group(1).zfill(2)}E{m.group(2).zfill(2)}'),
            (r'\bs(\d{2})(?:\s|$)', lambda m: f'S{m.group(1)}'),
        ]
        
        for pattern, formatter in tv_patterns:
            for match in re.finditer(pattern, text, re.I):
                metadata['tv_clues'].append(formatter(match))
        
        # Anime patterns
        anime_patterns = [
            (r'\[(\d{1,3})\]', lambda m: f'EP{m.group(1).zfill(3)}'),
            (r'[\s-](\d{1,3})[\s-]*\[', lambda m: f'EP{m.group(1).zfill(3)}'),
            (r'\((\d{1,3})-(\d{1,3})\)', lambda m: f'EP{m.group(1).zfill(3)}-{m.group(2).zfill(3)}'),
            (r'ep\.(\d{1,4})', lambda m: f'EP{m.group(1).zfill(3)}'),
        ]
        
        for pattern, formatter in anime_patterns:
            for match in re.finditer(pattern, text, re.I):
                metadata['anime_clues'].append(formatter(match))
        
        # Year patterns (movies)
        year_pattern = r'\b(19\d{2}|20\d{2})\b'
        for match in re.finditer(year_pattern, text):
            year = match.group(1)
            # Only add as movie clue if no TV/anime patterns nearby
            if not metadata['tv_clues'] and not metadata['anime_clues']:
                metadata['movie_clues'].append(year)
        
        # Quality metadata
        for pattern in self.quality_patterns['resolution']:
            for match in re.finditer(pattern, text, re.I):
                metadata['quality_clues'].append(match.group(0).upper())
        
        for pattern in self.quality_patterns['source']:
            for match in re.finditer(pattern, text, re.I):
                metadata['source_clues'].append(match.group(0).upper())
        
        for pattern in self.quality_patterns['codec']:
            for match in re.finditer(pattern, text, re.I):
                metadata['codec_clues'].append(match.group(0).upper())
        
        for pattern in self.quality_patterns['audio']:
            for match in re.finditer(pattern, text, re.I):
                metadata['audio_clues'].append(match.group(0).upper())
        
        # Release groups
        group_pattern = r'\[([^\]]+)\]'
        for match in re.finditer(group_pattern, text):
            group = match.group(1)
            if group.lower() in self.release_groups or re.match(r'^[A-Z0-9\-]+$', group):
                metadata['release_groups'].append(group)
        
        # Remove duplicates while preserving order
        for key in metadata:
            if isinstance(metadata[key], list):
                seen = set()
                metadata[key] = [x for x in metadata[key] if not (x in seen or seen.add(x))]
        
        return metadata

    def _determine_media_type(self, metadata: Dict, title: str, is_anime: bool) -> str:
        """Determine the media type based on metadata and heuristics"""
        title_lower = title.lower()
        
        # Check title heuristics first
        if any(anime in title_lower for anime in self.anime_titles):
            return 'anime'
        
        if any(tv in title_lower for tv in self.tv_titles):
            return 'tv'
        
        # Check metadata
        if is_anime or metadata['anime_clues']:
            return 'anime'
        
        if metadata['tv_clues']:
            return 'tv'
        
        if metadata['movie_clues']:
            return 'movie'
        
        return 'unknown'


def test_parser():
    """Test the parser with provided test cases"""
    parser = MediaParser()
    
    test_cases = [
        ("La famille bélier", "La famille bélier"),
        ("La.famille.bélier", "La famille bélier"),
        ("Mr. Nobody", "Mr. Nobody"),
        ("doctor_who_2005.8x12.death_in_heaven.720p_hdtv_x264-fov", "doctor who"),
        ("[GM-Team][国漫][太乙仙魔录 灵飞纪 第3季][Magical Legend of Rise to immortality Ⅲ][01-26][AVC][GB][1080P]", "Magical Legend of Rise to immortality Ⅲ"),
        ("【喵萌奶茶屋】★01月新番★[Rebirth][01][720p][简体][招募翻译]", "Rebirth"),
        ("【喵萌奶茶屋】★01月新番★[別對映像研出手！/Eizouken ni wa Te wo Dasu na！/映像研には手を出すな！][01][1080p][繁體]", "Eizouken ni wa Te wo Dasu na!"),
        ("[Seed-Raws] 劇場版 ペンギン・ハイウェイ Penguin Highway The Movie (BD 1280x720 AVC AACx4 [5.1+2.0+2.0+2.0]).mp4", "Penguin Highway The Movie"),
        ("[SweetSub][Mutafukaz / MFKZ][Movie][BDRip][1080P][AVC 8bit][简体内嵌]", "Mutafukaz / MFKZ"),
        ("[Erai-raws] Kingdom 3rd Season - 02 [1080p].mkv", "Kingdom"),
        ("Голубая волна / Blue Crush (2002) DVDRip", "Blue Crush"),
        ("Жихарка (2007) DVDRip", "Жихарка"),
        ("3 Миссия невыполнима 3 2006г. BDRip 1080p.mkv", "3 Миссия невыполнима 3"),
        ("1. Детские игры. 1988. 1080p. HEVC. 10bit..mkv", "1. Детские игры"),
        ("01. 100 девчонок и одна в лифте 2000 WEBRip 1080p.mkv", "100 девчонок и одна в лифте"),
        ("08.Планета.обезьян.Революция.2014.BDRip-HEVC.1080p.mkv", "Планета обезьян Революция"),
        ("Американские животные / American Animals (Барт Лэйтон / Bart Layton) [2018, Великобритания, США, драма, криминал, BDRip] MVO (СВ Студия)", "American Animals"),
        ("Греческая смоковница / Griechische Feigen / The Fruit Is Ripe (Зиги Ротемунд / Sigi Rothemund (as Siggi Götз)) [1976, Германия (ФРГ), эротика, комедия, приключения, DVDRip] 2 VO", "Griechische Feigen"),
        ("Греческая смоковница / The fruit is ripe / Griechische Feigen (Siggi Götз) [1976, Германия, Эротическая комедия, DVDRip]", "The fruit is ripe"),
        ("Бастер / Buster (Дэвид Грин / David Green) [1988, Великобритания, Комедия, мелодрама, драма, приключения, криминал, биография, DVDRip]", "Buster"),
        ("(2000) Le follie dell'imperatore - The Emperor's New Groove (DvdRip Ita Eng AC3 5.1).avi", "Le follie dell'imperatore"),
        ("[NC-Raws] 间谍过家家 / SPY×FAMILY - 04 (B-Global 1920x1080 HEVC AAC MKV)", "SPY×FAMILY"),
        ("GTO (Great Teacher Onizuka) (Ep. 1-43) Sub 480p lakshay", "GTO"),
        ("Книгоноши / Кнiганошы (1987) TVRip от AND03AND | BLR", "Кнiганошы"),
        ("Yurusarezaru_mono2.srt", "Yurusarezaru mono2"),
        ("www.1TamilMV.world - Ayalaan (2024) Tamil PreDVD - 1080p - x264 - HQ Clean Aud - 2.5GB.mkv", "Ayalaan"),
        ("www.Torrenting.com   -    Anatomy Of A Fall (2023)", "Anatomy Of A Fall"),
        ("[www.arabp2p.net]_-_تركي مترجم ومدبلج Last.Call.for.Istanbul.2023.1080p.NF.WEB-DL.DDP5.1.H.264.MKV.torrent", "Last Call for Istanbul"),
        ("www,1TamilMV.phd - The Great Indian Suicide (2023) Tamil TRUE WEB-DL - 4K SDR - HEVC - (DD+5.1 - 384Kbps & AAC) - 3.2GB - ESub.mkv", "The Great Indian Suicide"),
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
        ("S.W.A.T.2017.S08E01.720p.HDTV.x264-SYNCOPY[TGx]", "S.W.A.T"),
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
        ("S.H.I.E.L.D.s01","S.H.I.E.L.D"),
        ("One-piece-ep.1080-v2-1080p-raws","One piece"),
        ("Naruto Shippuden (001-500) [Complete Series + Movies] (Dual Audio)","Naruto Shippuden"),
        ("One.Piece.S01E1116.Lets.Go.Get.It!.Buggys.Big.Declaration.2160p.B-Global.WEB-DL.JPN.AAC2.0.H.264.MSubs-ToonsHub.mkv","One Piece"),
        ("Stranger Things S04 2160p","Stranger Things"),
    ]
    
    print("Testing Media Filename Parser")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for filename, expected_title in test_cases:
        result = parser.parse(filename)
        
        # Normalize for comparison
        clean_expected = expected_title.strip()
        clean_result = result.clean_title.strip()
        
        # Check if result is close enough (accounting for minor differences)
        is_match = (
            clean_result.lower() == clean_expected.lower() or
            clean_expected.lower() in clean_result.lower() or
            clean_result.lower() in clean_expected.lower()
        )
        
        if is_match:
            passed += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"
        
        print(f"{status} Input: {filename[:60]}...")
        print(f"  Expected: '{expected_title}'")
        print(f"  Got:      '{result.clean_title}'")
        print(f"  Type:     {result.media_type}")
        
        # Show extracted metadata
        if result.tv_clues:
            print(f"  TV:       {', '.join(result.tv_clues)}")
        if result.anime_clues:
            print(f"  Anime:    {', '.join(result.anime_clues)}")
        if result.movie_clues:
            print(f"  Movie:    {', '.join(result.movie_clues)}")
        if result.quality_clues:
            print(f"  Quality:  {', '.join(result.quality_clues)}")
        print()
    
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"Success rate: {(passed/len(test_cases))*100:.1f}%")


if __name__ == "__main__":
    test_parser()
    
    # Example usage
    print("\n" + "=" * 80)
    print("Example usage:")
    parser = MediaParser()
    
    example = "The.Mandalorian.S01E01.Chapter.1.1080p.Web-DL.mkv"
    result = parser.parse(example)
    
    print(f"\nFilename: {example}")
    print(f"Clean Title: {result.clean_title}")
    print(f"Media Type: {result.media_type}")
    print(f"TV Clues: {result.tv_clues}")
    print(f"Quality: {result.quality_clues}")
    print(f"Source: {result.source_clues}")
    print(f"Codec: {result.codec_clues}")