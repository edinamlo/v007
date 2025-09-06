"""
Basic parser tests.

Run with: pytest -q
"""

from pathlib import Path
from ..src.parser import parse_filename

def test_simple_movie():
    r = parse_filename("1408.2007.DC.1080p.BluRay.H264.AAC.mp4", quiet=True)
    assert r["movie_clues"] == ["2007"]
    assert "1080p" in [e.lower() for e in r["extras_bits"]]
    assert "BluRay" in r["extras_bits"] or "bluray" in r["extras_bits"]

def test_tv_show():
    r = parse_filename("The.Mandalorian.S01E01.Chapter.1.1080p.Web-DL.mkv", quiet=True)
    assert any("S01E01" in t for t in r["tv_clues"]) or any("S01" in t for t in r["tv_clues"])
