"""
Load configuration (env + clues JSON).

Prefer .env for simple environment values and config/clues.json for
the evolving list of known clues.
"""
import os
import json
from pathlib import Path

# Try to load .env if python-dotenv is available (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass  # dotenv not installed; rely on environment vars

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_DIR = Path(os.getenv("SOURCE_DIR", PROJECT_ROOT / "sample_media"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", PROJECT_ROOT / "output"))
CLUES_FILE = Path(os.getenv("CLUES_FILE", PROJECT_ROOT / "config" / "clues.json"))
UNKNOWN_FILE = Path(os.getenv("UNKNOWN_FILE", PROJECT_ROOT / "data" / "unknown_clues.json"))

# Token bucket defaults (if needed)
TOKENS_PER_SECOND = float(os.getenv("TOKENS_PER_SECOND", "5"))
TOKEN_BUCKET_CAPACITY = int(os.getenv("TOKEN_BUCKET_CAPACITY", "10"))

# Load clues from CLUES_FILE (fallback to defaults if missing)
if CLUES_FILE.exists():
    with CLUES_FILE.open("r", encoding="utf-8") as fh:
        CLUES = json.load(fh)
else:
    CLUES = {
        "quality_clues": [],
        "release_groups": [],
        "release_groups_anime": [],
        "audio_clues": [],
        "resolution_clues": [],
        "misc_clues": []
    }

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
