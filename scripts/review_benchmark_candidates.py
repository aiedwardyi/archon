from __future__ import annotations

import argparse
import asyncio
import html
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "ai-dev-team.db"
GENERATED_DIR = ROOT / "generated"
PUBLISHED_DIR = ROOT / "published"
BENCHMARKS_PATH = ROOT / "eval" / "archetype_benchmarks.json"
OUTPUT_DIR = ROOT / "eval" / "results" / "benchmark_review"

sys.path.insert(0, str(ROOT / "eval"))
from screenshotter import Screenshotter  # noqa: E402


@dataclass
class Candidate:
    project_id: int
    version: int
    name: str
    archetype: str
    prompt_summary: str
    published_slug: str
    generated_src_dir: Path
    published_src_dir: Path | None
    preview_uri: str
    source_uri: str
    benchmark_label: str
    benchmark_priority: int | None
    has_benchmark: bool
    is_active_head: bool
    shortlist_score: tuple[int, int, int, int]
    screenshot_relpath: str = ""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_benchmarks() -> list[dict[str, Any]]:
    if not BENCHMARKS_PATH.exists():
        return []
    return _read_json(BENCHMARKS_PATH).get("benchmarks", [])


def _build_benchmark_maps(
    benchmarks: list[dict[str, Any]],
) -> tuple[dict[tuple[int, int], dict[str, Any]], dict[str, dict[str, Any]]]:
    by_project_version: dict[tuple[int, int], dict[str, Any]] = {}
    by_slug: dict[str, dict[str, Any]] = {}
    for item in benchmarks:
        if not isinstance(item, dict):
            continue
        try:
            project_id = int(item.get("project_id"))
            version = int(item.get("version", 1))
        except (TypeError, ValueError):
            continue
        by_project_version[(project_id, version)] = item
        slug = str(item.get("published_slug", "")).strip()
        if slug:
            by_slug[slug] = item
    return by_project_version, by_slug


def _prompt_from_history(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:280].strip()
    if not isinstance(items, list):
        return ""
    for item in items:
        if not isinstance(item, dict):
            continue
        if str(item.get("role", "")).strip().lower() != "user":
            continue
        content = str(item.get("content", "")).strip()
        if content:
            return content
    return ""


def _factsheet_for(project_id: int, version: int) -> dict[str, Any]:
    factsheet = GENERATED_DIR / str(project_id) / f"v{version}" / "last_factsheet.json"
    if not factsheet.exists():
        return {}
    try:
        return _read_json(factsheet)
    except Exception:
        return {}


def _choose_preview_uri(generated_src_dir: Path, published_src_dir: Path | None) -> str:
    if published_src_dir and (published_src_dir / "index.html").exists():
        return (published_src_dir / "index.html").resolve().as_uri()
    return (generated_src_dir / "index.html").resolve().as_uri()


def _shortlist_score(
    *,
    has_benchmark: bool,
    published_slug: str,
    prompt_summary: str,
    project_id: int,
    archetype: str,
) -> tuple[int, int, int, int]:
    prompt_lower = prompt_summary.lower()
    quality_terms = (
        "premium",
        "cinematic",
        "polished",
        "landing page",
        "dashboard",
        "pricing",
        "portfolio",
        "ecommerce",
        "fan page",
        "tribute",
        "editorial",
        "interactive",
    )
    prompt_bonus = 1 if any(term in prompt_lower for term in quality_terms) else 0
    archetype_bonus = 1 if archetype in {
        "saas_landing",
        "dashboard",
        "portfolio",
        "ecommerce",
        "game",
        "editor",
        "form",
    } else 0
    return (
        0 if has_benchmark else 1,
        1 if published_slug else 0,
        prompt_bonus + archetype_bonus,
        project_id,
    )


def load_candidates(
    *,
    only_active_heads: bool,
    only_unbenchmarked: bool,
    archetype_filter: str,
) -> list[Candidate]:
    benchmarks = _load_benchmarks()
    by_project_version, by_slug = _build_benchmark_maps(benchmarks)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
    SELECT
        p.id AS project_id,
        p.name AS project_name,
        p.locked_ui_archetype AS locked_ui_archetype,
        e.version AS version,
        e.published_slug AS published_slug,
        e.prompt_history AS prompt_history,
        e.is_active_head AS is_active_head
    FROM projects p
    JOIN executions e ON e.project_id = p.id
    """
    where = []
    params: list[Any] = []
    if only_active_heads:
        where.append("e.is_active_head = 1")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY p.id DESC, e.version DESC"

    rows = cur.execute(sql, params).fetchall()
    conn.close()

    candidates: list[Candidate] = []
    seen: set[tuple[int, int]] = set()
    for row in rows:
        project_id = int(row["project_id"])
        version = int(row["version"])
        key = (project_id, version)
        if key in seen:
            continue
        seen.add(key)

        generated_src_dir = GENERATED_DIR / str(project_id) / f"v{version}" / "code" / "src"
        if not generated_src_dir.exists():
            continue

        published_slug = str(row["published_slug"] or "").strip()
        published_src_dir = None
        if published_slug:
            candidate_published_dir = PUBLISHED_DIR / published_slug / "src"
            if candidate_published_dir.exists():
                published_src_dir = candidate_published_dir

        factsheet = _factsheet_for(project_id, version)
        prompt_summary = str(factsheet.get("prompt_summary", "")).strip()
        if not prompt_summary:
            prompt_summary = _prompt_from_history(row["prompt_history"])

        archetype = str(
            factsheet.get("pipeline", {}).get("ui_archetype")
            or row["locked_ui_archetype"]
            or ""
        ).strip()
        if archetype_filter and archetype != archetype_filter:
            continue

        benchmark = by_project_version.get(key) or (by_slug.get(published_slug) if published_slug else None)
        has_benchmark = benchmark is not None
        if only_unbenchmarked and has_benchmark:
            continue

        preview_uri = _choose_preview_uri(generated_src_dir, published_src_dir)
        source_uri = generated_src_dir.resolve().as_uri()
        benchmark_label = str(benchmark.get("label", "")).strip() if benchmark else ""
        benchmark_priority = int(benchmark["priority"]) if benchmark and benchmark.get("priority") is not None else None

        candidates.append(
            Candidate(
                project_id=project_id,
                version=version,
                name=str(row["project_name"] or "").strip(),
                archetype=archetype,
                prompt_summary=prompt_summary,
                published_slug=published_slug,
                generated_src_dir=generated_src_dir,
                published_src_dir=published_src_dir,
                preview_uri=preview_uri,
                source_uri=source_uri,
                benchmark_label=benchmark_label,
                benchmark_priority=benchmark_priority,
                has_benchmark=has_benchmark,
                is_active_head=bool(row["is_active_head"]),
                shortlist_score=_shortlist_score(
                    has_benchmark=has_benchmark,
                    published_slug=published_slug,
                    prompt_summary=prompt_summary,
                    project_id=project_id,
                    archetype=archetype,
                ),
            )
        )

    candidates.sort(key=lambda item: item.shortlist_score, reverse=True)
    return candidates


async def capture_shortlist_screenshots(
    candidates: list[Candidate],
    *,
    limit: int,
    refresh: bool,
    wait_seconds: float,
) -> None:
    screenshotter = Screenshotter(viewport_width=1440, viewport_height=900)
    screenshots_dir = OUTPUT_DIR / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    for candidate in candidates[:limit]:
        rel = f"screenshots/{candidate.project_id}_v{candidate.version}.png"
        out_path = OUTPUT_DIR / rel
        candidate.screenshot_relpath = rel
        if out_path.exists() and not refresh:
            continue
        await screenshotter.capture(
            candidate.preview_uri,
            out_path,
            wait_seconds=wait_seconds,
            full_page=False,
        )


def _render_candidate_card(candidate: Candidate) -> str:
    screenshot_block = ""
    if candidate.screenshot_relpath:
        screenshot_block = (
            f'<a class="thumb-link" href="{html.escape(candidate.preview_uri)}">'
            f'<img class="thumb" src="{html.escape(candidate.screenshot_relpath)}" alt="Project {candidate.project_id} preview"></a>'
        )

    benchmark_text = "No benchmark yet"
    benchmark_class = "badge badge-missing"
    if candidate.has_benchmark:
        benchmark_text = f"Benchmark: {candidate.benchmark_label}"
        if candidate.benchmark_priority is not None:
            benchmark_text += f" (priority {candidate.benchmark_priority})"
        benchmark_class = "badge badge-present"

    published_block = ""
    if candidate.published_slug:
        published_block = (
            f'<span class="meta"><strong>Published:</strong> {html.escape(candidate.published_slug)}</span>'
        )

    return f"""
    <article class="card">
      <div class="card-top">
        <div>
          <h3>#{candidate.project_id} v{candidate.version} · {html.escape(candidate.name or 'Untitled')}</h3>
          <p class="prompt">{html.escape(candidate.prompt_summary or 'No prompt summary found.')}</p>
        </div>
        <div class="{benchmark_class}">{html.escape(benchmark_text)}</div>
      </div>
      {screenshot_block}
      <div class="meta-row">
        <span class="meta"><strong>Archetype:</strong> {html.escape(candidate.archetype or 'unknown')}</span>
        {published_block}
      </div>
      <div class="link-row">
        <a href="{html.escape(candidate.preview_uri)}">Open Preview</a>
        <a href="{html.escape(candidate.source_uri)}">Open Source Dir</a>
      </div>
    </article>
    """


def write_inventory_html(candidates: list[Candidate], screenshot_limit: int) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    shortlist_items = candidates[:screenshot_limit]
    remaining_items = candidates[screenshot_limit:]
    shortlist_cards = "\n".join(_render_candidate_card(item) for item in shortlist_items)
    full_cards = "\n".join(_render_candidate_card(item) for item in remaining_items)

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Benchmark Candidate Review</title>
  <style>
    :root {{
      --bg: #0b1020;
      --panel: #121932;
      --panel-2: #182242;
      --text: #f4f7fb;
      --muted: #9fb0d1;
      --accent: #6ee7b7;
      --warn: #fbbf24;
      --danger: #fb7185;
      --border: rgba(255, 255, 255, 0.08);
      --shadow: 0 18px 60px rgba(0, 0, 0, 0.28);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      background:
        radial-gradient(circle at top right, rgba(110, 231, 183, 0.10), transparent 26%),
        radial-gradient(circle at top left, rgba(96, 165, 250, 0.12), transparent 24%),
        var(--bg);
      color: var(--text);
    }}
    .wrap {{ max-width: 1600px; margin: 0 auto; padding: 32px 24px 72px; }}
    h1 {{ margin: 0 0 10px; font-size: 36px; }}
    .lede {{ margin: 0; color: var(--muted); max-width: 900px; line-height: 1.6; }}
    .stats {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin: 24px 0 36px;
    }}
    .stat {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px 16px;
      box-shadow: var(--shadow);
      min-width: 160px;
    }}
    .stat strong {{ display: block; font-size: 24px; margin-top: 4px; }}
    h2 {{ margin: 40px 0 16px; font-size: 24px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 18px;
    }}
    .card {{
      background: linear-gradient(180deg, var(--panel), var(--panel-2));
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 18px;
      box-shadow: var(--shadow);
    }}
    .card-top {{
      display: flex;
      gap: 16px;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
    }}
    h3 {{ margin: 0 0 10px; font-size: 18px; line-height: 1.35; }}
    .prompt {{ margin: 0; color: var(--muted); line-height: 1.55; }}
    .badge {{
      white-space: nowrap;
      font-size: 12px;
      font-weight: 700;
      padding: 8px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
    }}
    .badge-present {{ background: rgba(110, 231, 183, 0.12); color: var(--accent); }}
    .badge-missing {{ background: rgba(251, 191, 36, 0.12); color: var(--warn); }}
    .thumb-link {{ display: block; margin: 12px 0 14px; }}
    .thumb {{
      width: 100%;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: #09101f;
    }}
    .meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 14px;
      margin-top: 8px;
    }}
    .meta {{ color: var(--muted); font-size: 14px; }}
    .link-row {{
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
      margin-top: 16px;
    }}
    a {{
      color: #9fd0ff;
      text-decoration: none;
      font-weight: 700;
    }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Benchmark Candidate Review</h1>
    <p class="lede">Use this page to triage legacy generated and published projects for benchmark inclusion. The shortlist is sorted toward unbenchmarked, previewable, recent projects. Open Preview uses local file-backed HTML, so you do not need the backend running just to inspect candidates.</p>
    <div class="stats">
      <div class="stat">Candidates<strong>{len(candidates)}</strong></div>
      <div class="stat">Unbenchmarked<strong>{sum(1 for item in candidates if not item.has_benchmark)}</strong></div>
      <div class="stat">Published<strong>{sum(1 for item in candidates if item.published_slug)}</strong></div>
      <div class="stat">Shortlist With Screenshots<strong>{min(screenshot_limit, len(candidates))}</strong></div>
    </div>
    <h2>Shortlist</h2>
    <div class="grid">{shortlist_cards}</div>
    <h2>Remaining Candidates</h2>
    <div class="grid">{full_cards}</div>
  </div>
</body>
</html>
"""

    out = OUTPUT_DIR / "index.html"
    out.write_text(html_body, encoding="utf-8")
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a local benchmark-review inventory page and optional screenshots."
    )
    parser.add_argument("--limit", type=int, default=48, help="Number of candidates in the shortlist.")
    parser.add_argument(
        "--screenshot-limit",
        type=int,
        default=24,
        help="How many shortlist entries to capture screenshots for.",
    )
    parser.add_argument(
        "--capture-screenshots",
        action="store_true",
        help="Capture viewport screenshots for the shortlist.",
    )
    parser.add_argument(
        "--refresh-screenshots",
        action="store_true",
        help="Re-render screenshots even when files already exist.",
    )
    parser.add_argument(
        "--wait-seconds",
        type=float,
        default=1.5,
        help="Extra wait before each screenshot to let the page settle.",
    )
    parser.add_argument(
        "--all-executions",
        action="store_true",
        help="Include non-head executions instead of only active heads.",
    )
    parser.add_argument(
        "--include-benchmarked",
        action="store_true",
        help="Include projects already represented in the benchmark registry.",
    )
    parser.add_argument("--archetype", default="", help="Filter to one archetype.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = load_candidates(
        only_active_heads=not args.all_executions,
        only_unbenchmarked=not args.include_benchmarked,
        archetype_filter=args.archetype.strip(),
    )
    if args.limit > 0:
        candidates = candidates[: args.limit]

    screenshot_limit = min(args.screenshot_limit, len(candidates))
    if args.capture_screenshots and screenshot_limit > 0:
        asyncio.run(
            capture_shortlist_screenshots(
                candidates,
                limit=screenshot_limit,
                refresh=args.refresh_screenshots,
                wait_seconds=args.wait_seconds,
            )
        )

    out = write_inventory_html(candidates, screenshot_limit)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
