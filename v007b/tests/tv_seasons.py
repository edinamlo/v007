import sys
import pytest
from pathlib import Path
import json
from datetime import datetime

# make sure v007b is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from parser import parse_filename

SEASON_TEST_CASES = [
    ("2 сезон 24 серия.avi", [2]),
    ("2-06. Девичья сила.mkv", [2]),
    ("2. Discovery-Kak_ustroena_Vselennaya.(2.sezon_8.serii.iz.8).2012.XviD.HDTVRip.Krasnodarka", [2]),
    ("3 сезон", [3]),
    ("3Âº Temporada Bob esponja Pt-Br", [3]),
    ("4-13 Cursed (HD).m4v", [4]),
    ("13-13-13 2013 DVDrip x264 AAC-MiLLENiUM", []),
    ("24 Season 1-8 Complete with Subtitles", [1, 2, 3, 4, 5, 6, 7, 8]),
    ("30 M0N3D4S ESP T01XE08.mkv", [1]),
    ("Ace of the Diamond: 1st Season", [1]),
    ("Ace of the Diamond: 2nd Season", [2]),
    ("Adventure Time 10 th season", [10]),
    ("All of Us Are Dead . 2022 . S01 EP #1.2.mkv", [1]),
    ("Beavis and Butt-Head - 1a. Temporada", [1]),
    ("Boondocks, The - Seasons 1 + 2", [1, 2]),
    ("breaking.bad.s01e01.720p.bluray.x264-reward", [1]),
    ("Breaking Bad Complete Season 1 , 2 , 3, 4 ,5 ,1080p HEVC", [1, 2, 3, 4, 5]),
    ("Bron - S4 - 720P - SweSub.mp4", [4]),
    ("clny.3x11m720p.es[www.planetatorrent.com].mkv", [3]),
    ("Coupling Season 1 - 4 Complete DVDRip - x264 - MKV by RiddlerA", [1, 2, 3, 4]),
    # ... add remaining test cases ...
]

def write_results(raw, expected_seasons, result, success):
    """Write test results to a timestamped file."""
    # Generate timestamp filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'test_tv_seasons_{timestamp}.txt'
    
    # Ensure tests directory exists
    output_dir = Path(__file__).parent / 'test_output'
    output_dir.mkdir(exist_ok=True)
    
    # Full path to results file
    output_file = output_dir / filename
    
    # Append results
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write('\n' + '-'*80 + '\n')
        f.write(f'Test Run: {datetime.now().isoformat()}\n')
        f.write(f'Input: {raw}\n')
        f.write(f'Expected Seasons: {expected_seasons}\n')
        f.write(f'Got: {json.dumps(result, indent=2, ensure_ascii=False)}\n')
        f.write(f'Success: {success}\n')
    
    return output_file

@pytest.mark.parametrize("filename,expected_seasons", SEASON_TEST_CASES)
def test_season_detection(filename, expected_seasons):
    """Test season number detection from filenames."""
    try:
        res = parse_filename(filename, quiet=True)
        
        # Extract season numbers from tv_clues
        detected_seasons = set()
        for clue in res.get("tv_clues", []):
            # Look for season numbers in various formats
            season_patterns = [
                r"s(\d{1,2})e\d{1,3}",  # S01E02
                r"season[s]?\s*(\d{1,2})",  # Season 1
                r"[\s._-](\d{1,2})[aº]?\s*(?:st|nd|rd|th)?\s*(?:season|temporada|sezon)",  # 1st season, 2ª temporada
                r"(?:сезон|sezon)[:\s._-]*(\d{1,2})",  # сезон 2, sezon 3
                r"T(\d{1,2})(?:[Ex]|XE)\d{1,3}",  # T01E01, T01XE01
                r"(\d{1,2})x\d{1,3}",  # 1x01
            ]
            
            for pattern in season_patterns:
                match = re.search(pattern, clue, re.IGNORECASE)
                if match:
                    try:
                        season_num = int(match.group(1))
                        detected_seasons.add(season_num)
                    except ValueError:
                        continue
        
        # Convert to sorted list for comparison
        detected = sorted(list(detected_seasons))
        success = detected == expected_seasons
        output_file = write_results(filename, expected_seasons, res, success)
        
        # Print path to results file on first test
        if filename == SEASON_TEST_CASES[0][0]:
            print(f"\nTest results written to: {output_file}")
        
        assert detected == expected_seasons, \
            f"Expected seasons {expected_seasons} but got {detected} for {filename!r}"
            
    except Exception as e:
        write_results(filename, expected_seasons, str(e), False)
        raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"])