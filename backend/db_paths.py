import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PRIMARY_DB_PATH = REPO_ROOT / "archon.db"
LEGACY_DB_PATH = REPO_ROOT / "ai-dev-team.db"


def resolve_db_path() -> Path:
    """Prefer the Archon filename, but keep existing local legacy DBs working."""
    configured_path = os.getenv("DATABASE_PATH", "").strip()
    if configured_path:
        path = Path(configured_path).expanduser()
        return path if path.is_absolute() else REPO_ROOT / path
    if PRIMARY_DB_PATH.exists():
        return PRIMARY_DB_PATH
    if LEGACY_DB_PATH.exists():
        return LEGACY_DB_PATH
    return PRIMARY_DB_PATH


DB_PATH = resolve_db_path()
