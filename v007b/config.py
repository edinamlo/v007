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

# base dir = folder containing this file (v007b)
BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent

def resolve_env_path(name: str, default):
    raw = os.getenv(name)
    if raw:
        p = Path(raw)
    else:
        p = Path(default)
    if not p.is_absolute():
        return (BASE_DIR / p).resolve()
    return p.resolve()

SOURCE_DIR = resolve_env_path("SOURCE_DIR", BASE_DIR / "sample_media")
OUTPUT_DIR = resolve_env_path("OUTPUT_DIR", BASE_DIR / "output")
CLUES_FILE = resolve_env_path("CLUES_FILE", BASE_DIR / "config" / "clues.json")
UNKNOWN_FILE = resolve_env_path("UNKNOWN_FILE", BASE_DIR / "data" / "unknown_clues.json")

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
