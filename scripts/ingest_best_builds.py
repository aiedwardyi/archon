"""One-time ingestion of top eval builds into Watson Discovery."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.watson_discovery import DiscoveryClient
from utils.reference_build_registry import get_reference_build_registry, load_reference_build_content


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_document(entry: dict) -> dict:
    project_id = int(entry["project_id"])
    version = int(entry.get("version", 1))
    base = ROOT / "generated" / str(project_id) / f"v{version}"
    factsheet = _read_json(base / "last_factsheet.json")
    plan = _read_json(base / "last_plan.json")
    loaded = load_reference_build_content(entry)
    if loaded is None:
        raise FileNotFoundError(f"Missing benchmark files for project {project_id} v{version}")

    factsheet_archetype = factsheet.get("pipeline", {}).get("ui_archetype") or ""
    archetype = entry.get("archetype") or factsheet_archetype
    prompt_summary = factsheet.get("prompt_summary", "")
    eval_score = entry.get("eval_score")

    return {
        "archetype": archetype,
        "prompt": prompt_summary,
        "plan_json": json.dumps(plan, ensure_ascii=False),
        "html_code": loaded["html_code"],
        "css_code": loaded["css_code"],
        "base_css": loaded["base_css"],
        "eval_score": eval_score,
        "dimension_scores": factsheet.get("scoring", {}),
        "factsheet_archetype": factsheet_archetype,
        "project_id": project_id,
        "version": version,
        "created_at": factsheet.get("generated_at"),
    }


def main() -> int:
    load_dotenv(ROOT / "backend" / ".env")

    client = DiscoveryClient()
    if not client.enabled:
        print("[Discovery] Credentials missing. Nothing ingested.")
        return 0

    discovery_entries = [
        entry for entry in get_reference_build_registry()
        if entry.get("discovery_ingest")
    ]
    if not discovery_entries:
        print("[Discovery] No registry entries marked discovery_ingest=true. Nothing ingested.")
        return 0

    successes = 0
    for entry in discovery_entries:
        project_id = int(entry["project_id"])
        arch = entry["archetype"]
        score = entry.get("eval_score")

        try:
            doc = _build_document(entry)
        except Exception as exc:
            print(f"[Discovery] Failed to load project {project_id}: {exc}")
            print(f"  [FAIL] project {project_id} failed")
            continue

        if doc.get("factsheet_archetype") and doc["factsheet_archetype"] != doc["archetype"]:
            print(
                f"[Discovery] Archetype override for project {project_id}: "
                f"factsheet='{doc['factsheet_archetype']}' -> ingest='{doc['archetype']}'"
            )

        print(f"[Discovery] Ingesting project {project_id} ({doc['archetype']}, score {score})...")
        ok = client.ingest_build(doc)
        if ok:
            successes += 1
            print(f"  [OK] project {project_id} ingested")
        else:
            print(f"  [FAIL] project {project_id} failed")

    print(f"[Discovery] Ingested {successes}/{len(discovery_entries)} builds")

    # Test query
    print("\nWaiting 10s for Discovery indexing...")
    time.sleep(10)
    for arch in ["ecommerce", "game", "portfolio", "dashboard", "saas_landing"]:
        result = client.query_best_build(arch)
        if result:
            print(f"  [OK] {arch}: found document")
        else:
            print(f"  [MISS] {arch}: no results")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
