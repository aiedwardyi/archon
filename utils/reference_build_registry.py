from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS_PATH = ROOT / "eval" / "archetype_benchmarks.json"
GENERATED_DIR = ROOT / "generated"
PUBLISHED_DIR = ROOT / "published"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_reference_build_registry() -> list[dict[str, Any]]:
    if not BENCHMARKS_PATH.exists():
        return []
    data = _read_json(BENCHMARKS_PATH)
    items = data.get("benchmarks", [])
    return [item for item in items if isinstance(item, dict)]


def get_reference_build_entries(archetype: str | None = None) -> list[dict[str, Any]]:
    entries = get_reference_build_registry()
    if archetype is None:
        return entries
    return [item for item in entries if item.get("archetype") == archetype]


def _get_guidance_lines(entries: list[dict[str, Any]], limit: int) -> list[str]:
    entries.sort(key=lambda item: int(item.get("priority", 0)), reverse=True)
    lines: list[str] = []
    seen: set[str] = set()
    for entry in entries[:limit]:
        note = str(entry.get("notes", "")).strip()
        label = str(entry.get("label", "")).strip()
        if not note:
            continue
        normalized = note.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        prefix = f"{label}: " if label else ""
        lines.append(f"- {prefix}{note}")
    return lines


def get_archetype_benchmark_guidance(
    archetype: str,
    limit: int = 4,
    global_limit: int = 2,
) -> str:
    if not archetype:
        return ""

    archetype_lines = _get_guidance_lines(get_reference_build_entries(archetype), limit)
    global_entries = [
        item for item in get_reference_build_registry()
        if bool(item.get("global_guidance"))
    ]
    global_lines = _get_guidance_lines(global_entries, global_limit)
    lines = archetype_lines + [line for line in global_lines if line not in archetype_lines]
    return "\n".join(lines)


def suggest_reference_archetype(prompt_text: str) -> dict[str, Any] | None:
    if not prompt_text:
        return None

    prompt_lower = prompt_text.lower()
    matches: list[dict[str, Any]] = []
    for entry in get_reference_build_registry():
        hints = entry.get("prompt_hints", []) or []
        if not isinstance(hints, list):
            continue
        normalized_hints = [
            hint.strip().lower()
            for hint in hints
            if isinstance(hint, str) and hint.strip()
        ]
        if any(hint in prompt_lower for hint in normalized_hints):
            matches.append(entry)

    if not matches:
        return None

    matches.sort(key=lambda item: int(item.get("priority", 0)), reverse=True)
    return matches[0]


def load_reference_build_content(entry: dict[str, Any]) -> dict[str, Any] | None:
    project_id = int(entry["project_id"])
    version = int(entry.get("version", 1))
    archetype = entry.get("archetype", "")
    benchmark_path = entry.get("benchmark_path")
    published_slug = entry.get("published_slug")

    base = GENERATED_DIR / str(project_id) / f"v{version}"
    html_path = base / "code" / "src" / "index.html"
    css_path = base / "code" / "src" / "style.css"
    factsheet_path = base / "last_factsheet.json"
    factsheet: dict[str, Any] = {}

    if benchmark_path:
        benchmark_base = ROOT / str(benchmark_path)
        benchmark_html = benchmark_base / "src" / "index.html"
        benchmark_css = benchmark_base / "src" / "style.css"
        if benchmark_html.exists() and benchmark_css.exists():
            html_path = benchmark_html
            css_path = benchmark_css
        benchmark_base_css = benchmark_base / "src" / "base.css"
    else:
        benchmark_base_css = Path()

    if not html_path.exists() or not css_path.exists():
        if not published_slug:
            return None
        published_base = PUBLISHED_DIR / str(published_slug) / "src"
        html_path = published_base / "index.html"
        css_path = published_base / "style.css"
        if not html_path.exists() or not css_path.exists():
            return None
    elif factsheet_path.exists():
        factsheet = _read_json(factsheet_path)

    base_css_path = base / "code" / "src" / "base.css"
    if benchmark_base_css.exists():
        base_css_path = benchmark_base_css
    elif not base_css_path.exists() and published_slug:
        published_base_css = PUBLISHED_DIR / str(published_slug) / "src" / "base.css"
        if published_base_css.exists():
            base_css_path = published_base_css

    return {
        "project_id": project_id,
        "version": version,
        "archetype": archetype,
        "label": entry.get("label", f"project-{project_id}"),
        "notes": entry.get("notes", ""),
        "prompt": factsheet.get("prompt_summary", "") or entry.get("prompt_summary", ""),
        "html_code": html_path.read_text(encoding="utf-8"),
        "css_code": css_path.read_text(encoding="utf-8"),
        "base_css": base_css_path.read_text(encoding="utf-8") if base_css_path.exists() else "",
        "eval_score": entry.get("eval_score"),
        "priority": int(entry.get("priority", 0)),
        "discovery_ingest": bool(entry.get("discovery_ingest", False)),
        "source": "local_benchmark",
    }


def load_local_reference_build(archetype: str) -> dict[str, Any] | None:
    """Load the highest-priority local benchmark build for an archetype."""
    if not archetype:
        return None

    matches = get_reference_build_entries(archetype)
    if not matches:
        return None

    matches.sort(key=lambda item: int(item.get("priority", 0)), reverse=True)
    build = load_reference_build_content(matches[0])
    if build:
        build["benchmark_guidance"] = get_archetype_benchmark_guidance(archetype)
    return build
