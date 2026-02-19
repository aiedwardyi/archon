"""
Database migration script for Archon.

Run this once after updating models.py to add new columns
to an existing SQLite database without destroying data.

Usage:
    cd backend
    python database.py
"""
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "ai-dev-team.db"


def column_exists(cursor, table: str, column: str) -> bool:
    """Check if a column already exists in a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def run_migration():
    """
    Add Phase 7A columns to the executions table.
    
    New columns:
    - version (INTEGER, default 1) — version number per project
    - prompt_history (TEXT) — full conversation history as JSON string
    - is_active_head (INTEGER/BOOLEAN, default 1) — marks the current version
    - parent_execution_id (INTEGER) — FK to previous execution version
    
    SQLite uses ALTER TABLE ADD COLUMN — safe, existing rows get the default value.
    """
    if not DB_PATH.exists():
        print(f"No database found at {DB_PATH}")
        print("Run the app first to create the database, then run this migration.")
        return

    print(f"Running migration on: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    migrations = [
        {
            "column": "version",
            "sql": "ALTER TABLE executions ADD COLUMN version INTEGER NOT NULL DEFAULT 1",
            "description": "version number per project",
        },
        {
            "column": "prompt_history",
            "sql": "ALTER TABLE executions ADD COLUMN prompt_history TEXT",
            "description": "full conversation history as JSON",
        },
        {
            "column": "is_active_head",
            "sql": "ALTER TABLE executions ADD COLUMN is_active_head INTEGER NOT NULL DEFAULT 1",
            "description": "marks the current active version",
        },
        {
            "column": "parent_execution_id",
            "sql": "ALTER TABLE executions ADD COLUMN parent_execution_id INTEGER REFERENCES executions(id)",
            "description": "points to the previous version",
        },
    ]

    for migration in migrations:
        col = migration["column"]
        if column_exists(cursor, "executions", col):
            print(f"  Column '{col}' already exists — skipping")
        else:
            cursor.execute(migration["sql"])
            print(f"  Added column '{col}': {migration['description']}")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    run_migration()
