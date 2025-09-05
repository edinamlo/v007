"""
Entry point for running scans and saving JSON outputs.
"""

import argparse
import json
from pathlib import Path
from .config import SOURCE_DIR, OUTPUT_DIR
from .dir_processor import parse_directory
from .clue_manager import ClueManager


def main():
    parser = argparse.ArgumentParser(description="Media parser runner")
    parser.add_argument("--scan-dir", "-s", default=str(SOURCE_DIR), help="Directory to scan (root folders)")
    parser.add_argument("--mode", "-m", default="dirs", choices=["dirs", "files"], help="Scan mode")
    parser.add_argument("--out", "-o", default=None, help="Output JSON file path")
    parser.add_argument("--quiet", action="store_true", help="Run in quiet mode")
    args = parser.parse_args()

    source = Path(args.scan_dir)
    out_path = Path(args.out) if args.out else Path(OUTPUT_DIR) / f"scan_{source.name}.json"
    result = parse_directory(str(source), mode=args.mode, quiet=args.quiet)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump({"scanned_dir": str(source.resolve()),
                   "generated_at": __import__("datetime").datetime.now().isoformat(),
                   "results": result}, fh, indent=2, ensure_ascii=False)

    print(f"Saved scan results to {out_path}")

    # Collect unknowns and persist them
    cm = ClueManager()
    cm.collect_from_parsed(result["raw"])
    cm.save_unknowns()
    print(f"Collected {len(cm.unknown)} unknown tokens (saved to {cm.unknown_file})")


if __name__ == "__main__":
    main()
