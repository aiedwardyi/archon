"""
Initialize the database.

Run this script once to create the database tables:
    python scripts/init_db.py
"""
import sys
from pathlib import Path

# Add backend to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.models import init_db, DB_PATH

if __name__ == "__main__":
    print(f"🔧 Initializing database at: {DB_PATH}")
    init_db()
    print(f"✅ Database ready!")
    print(f"   Location: {DB_PATH}")
    print(f"   Tables: projects, executions")
