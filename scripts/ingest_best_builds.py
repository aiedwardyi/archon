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


TOP_BUILDS = [
    {"project_id": 163, "archetype": "ecommerce", "eval_score": 88.5},
    {"project_id": 161, "archetype": "game", "eval_score": 84.5},
    {"project_id": 169, "archetype": "portfolio", "eval_score": 83.5},
    {"project_id": 155, "archetype": "dashboard", "eval_score": 81.0},
    {"project_id": 162, "archetype": "saas_landing", "eval_score": 76.0},
]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_document(project_id: int, fallback_archetype: str, eval_score: float) -> dict:
    base = ROOT / "generated" / str(project_id) / "v1"
    factsheet = _read_json(base / "last_factsheet.json")
    plan = _read_json(base / "last_plan.json")

    html_code = (base / "code" / "src" / "index.html").read_text(encoding="utf-8")
    style_css_path = base / "code" / "src" / "style.css"
    style_css = style_css_path.read_text(encoding="utf-8") if style_css_path.exists() else ""

    base_css_path = base / "code" / "src" / "base.css"
    base_css = base_css_path.read_text(encoding="utf-8") if base_css_path.exists() else ""

    factsheet_archetype = factsheet.get("pipeline", {}).get("ui_archetype") or ""
    archetype = fallback_archetype or factsheet_archetype
    prompt_summary = factsheet.get("prompt_summary", "")

    return {
        "archetype": archetype,
        "prompt": prompt_summary,
        "plan_json": json.dumps(plan, ensure_ascii=False),
        "html_code": html_code,
        "css_code": style_css,
        "base_css": base_css,
        "eval_score": eval_score,
        "dimension_scores": factsheet.get("scoring", {}),
        "factsheet_archetype": factsheet_archetype,
        "project_id": project_id,
        "version": int(factsheet.get("project", {}).get("version", 1)),
        "created_at": factsheet.get("generated_at"),
    }


def main() -> int:
    load_dotenv(ROOT / "backend" / ".env")

    client = DiscoveryClient()
    if not client.enabled:
        print("[Discovery] Credentials missing. Nothing ingested.")
        return 0

    successes = 0
    for item in TOP_BUILDS:
        project_id = item["project_id"]
        arch = item["archetype"]
        score = item["eval_score"]

        try:
            doc = _build_document(project_id=project_id, fallback_archetype=arch, eval_score=score)
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

    print(f"[Discovery] Ingested {successes}/{len(TOP_BUILDS)} builds")

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
