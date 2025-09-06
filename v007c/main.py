"""
main.py

The main entry point to run the media scanner.
It processes a target directory, saves the grouped results to an SQLite
database, and reports any unknown words found during the scan.
"""

from processor import parse_directory
from database_manager import save_groups_to_db
from clue_manager import collect_unknown_words
import json
from pathlib import Path
from parser import parse_filename

# --- Configuration ---
# IMPORTANT: Change this to the directory you want to scan.
SOURCE_DIRECTORY = "/workspaces/v007/sample_media/"
# The database file that will be created in the same folder as the script.
DATABASE_FILE = "data/media_library.sqlite"

def run_scan():
    """Performs the full scan and database save operation."""
    print(f"Starting scan of '{SOURCE_DIRECTORY}'...")
    
    # 1. Parse the directory to get raw data and grouped items
    # Mode can be "dirs" to scan folders or "files" to scan individual files.
    parsed_data = parse_directory(SOURCE_DIRECTORY, mode="dirs")
    
    if not parsed_data.get("grouped"):
        print("No items were found or parsed. Exiting.")
        return

    # 2. Save the grouped results to the database
    save_groups_to_db(parsed_data["grouped"], DATABASE_FILE)

    # 3. (Optional) Collect and report any unknown words
    unknowns = collect_unknown_words(parsed_data)
    if unknowns:
        print("\nFound unknown words! Consider adding them to 'clues_overrides.json':")
        # Pretty-print the dictionary of unknown words and their frequencies
        print(json.dumps(unknowns, indent=2))

def main(input_path: str, output_db: str = "media.db", output_json: str = "results.json"):
    """
    Process media files and save results to both SQLite and JSON.
    
    Args:
        input_path: Path to scan for media files
        output_db: SQLite database filename
        output_json: JSON output filename
    """
    results = []
    
    # Process files
    for filepath in Path(input_path).rglob("*"):
        if filepath.is_file():
            parsed = parse_filename(str(filepath))
            results.append(parsed)
    
    # Save to JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    # Original SQLite saving logic
    # ...existing SQLite code...

if __name__ == "__main__":
    import sys
    input_path = sys.argv[1] if len(sys.argv) > 1 else "."
    main(input_path)
