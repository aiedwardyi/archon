from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "generated"
PUBLISHED_DIR = ROOT / "published"
BENCHMARK_DIR = ROOT / "eval" / "benchmark_builds"


def _copy_source(src_dir: Path, dest_dir: Path) -> None:
    dest_src = dest_dir / "src"
    dest_src.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "style.css", "base.css"):
        src = src_dir / name
        if src.exists():
            shutil.copy2(src, dest_src / name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a legacy build into eval/benchmark_builds/")
    parser.add_argument("--label", required=True, help="Benchmark label/folder name")
    parser.add_argument("--project-id", type=int, required=True)
    parser.add_argument("--version", type=int, default=1)
    parser.add_argument("--archetype", required=True)
    parser.add_argument("--priority", type=int, default=100)
    parser.add_argument("--generated", action="store_true", help="Import from generated/<project_id>/v<version>/code/src")
    parser.add_argument("--published-slug", help="Import from published/<slug>/src")
    parser.add_argument("--prompt-summary", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--prompt-hint", action="append", default=[])
    args = parser.parse_args()

    if not args.generated and not args.published_slug:
        parser.error("Use --generated or --published-slug")

    if args.generated:
        src_dir = GENERATED_DIR / str(args.project_id) / f"v{args.version}" / "code" / "src"
    else:
        src_dir = PUBLISHED_DIR / str(args.published_slug) / "src"

    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")

    dest_dir = BENCHMARK_DIR / args.label
    _copy_source(src_dir, dest_dir)

    entry = {
        "project_id": args.project_id,
        "version": args.version,
        "archetype": args.archetype,
        "benchmark_path": f"eval/benchmark_builds/{args.label}",
        "priority": args.priority,
        "label": args.label,
        "prompt_summary": args.prompt_summary,
        "prompt_hints": args.prompt_hint,
        "notes": args.notes,
        "discovery_ingest": False,
    }
    if args.published_slug:
        entry["published_slug"] = args.published_slug

    print(json.dumps(entry, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
