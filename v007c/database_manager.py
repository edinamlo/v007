"""
database_manager.py

Handles all SQLite database operations for storing media groups and their paths.
This keeps all SQL logic separate from the parsing and processing logic.
"""

import sqlite3
from typing import Dict, Any

def setup_database(db_path: str) -> sqlite3.Connection:
    """Creates the database and tables if they don't exist and returns a connection."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Table for the media "group" - the unique media item
    # e.g., "The Matrix", "movie", 1999
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS media_groups (
        id INTEGER PRIMARY KEY,
        clean_title TEXT NOT NULL,
        media_type TEXT NOT NULL,
        year INTEGER,
        UNIQUE(clean_title, media_type, year)
    )
    """)

    # Table for the individual file/folder paths associated with a group
    # e.g., "/path/to/The.Matrix.1999.1080p.mkv"
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS media_paths (
        id INTEGER PRIMARY KEY,
        group_id INTEGER NOT NULL,
        full_path TEXT NOT NULL UNIQUE,
        FOREIGN KEY (group_id) REFERENCES media_groups (id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    return conn

def save_groups_to_db(grouped_data: Dict[Any, Dict], db_path: str):
    """
    Saves the grouped media data to the SQLite database.
    It inserts or updates data, ensuring no duplicates.
    """
    conn = setup_database(db_path)
    cursor = conn.cursor()
    
    print(f"Syncing {len(grouped_data)} media groups with the database...")
    
    for group_info in grouped_data.values():
        title = group_info["clean_title"]
        mtype = group_info["media_type"]
        year = group_info["year"]
        paths = group_info["paths"]
        
        # Insert the group if it doesn't exist, then get its ID
        cursor.execute(
            "INSERT OR IGNORE INTO media_groups (clean_title, media_type, year) VALUES (?, ?, ?)",
            (title, mtype, year)
        )
        cursor.execute(
            "SELECT id FROM media_groups WHERE clean_title = ? AND media_type = ? AND (year = ? OR (year IS NULL AND ? IS NULL))",
            (title, mtype, year, year)
        )
        group_id_result = cursor.fetchone()
        if not group_id_result:
            print(f"Warning: Could not find or create group for '{title}'")
            continue
        group_id = group_id_result[0]
        
        # Insert all associated paths for this group
        for path in paths:
            cursor.execute(
                "INSERT OR IGNORE INTO media_paths (group_id, full_path) VALUES (?, ?)",
                (group_id, path)
            )

    conn.commit()
    conn.close()
    print("Database sync complete.")
