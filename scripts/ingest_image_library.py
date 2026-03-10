from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from utils.image_asset_catalog import ingest_image_library


if __name__ == "__main__":
    ingested, category_count, project_count = ingest_image_library()
    print(f"Ingested {ingested} images across {category_count} categories from {project_count} projects")
