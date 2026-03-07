"""
A/B Comparison: Design Kit vs No Design Kit

Runs N builds per archetype, scores each, and outputs a comparison table.
Designed to be run TWICE — once on each branch — then compared.

Usage:
  # On branch with design kits:
  python eval/run_ab_comparison.py --label with-kits --builds-per-archetype 3

  # On branch without design kits:
  python eval/run_ab_comparison.py --label no-kits --builds-per-archetype 3

  # Compare results:
  python eval/run_ab_comparison.py --compare with-kits no-kits
"""

import sys
import json
import time
import asyncio
import argparse
import logging
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ab_comparison")

# ── Load env ────────────────────────────────────────────────────
env_path = Path(__file__).parent.parent / "backend" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())

# ── Config ──────────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).parent / "eval_config.json"
RESULTS_BASE = Path(__file__).parent / "results" / "ab_comparison"

ARCHETYPES = ["dashboard", "saas_landing", "ecommerce", "portfolio"]

SCORE_RUNS = 3           # Scorer runs per screenshot (averaged)
BUILD_TIMEOUT = 600      # Max seconds per build
SLEEP_BETWEEN_BUILDS = 5 # Seconds between sequential builds


def load_test_prompts() -> dict:
    """Load test prompts from eval_config.json."""
    config = json.loads(CONFIG_PATH.read_text())
    return config["test_prompts"]


def get_genai_client():
    """Create Gemini client (Vertex AI preferred)."""
    from google import genai
    project = os.environ.get("VERTEX_AI_PROJECT")
    if project:
        return genai.Client(
            vertexai=True,
            project=project,
            location=os.environ.get("VERTEX_AI_LOCATION", "us-central1"),
        )
    api_key = os.environ.get("GENAI_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)
    raise RuntimeError("No VERTEX_AI_PROJECT or GENAI_API_KEY found in env")


def build_one(api, name: str, description: str) -> dict | None:
    """Build a single project. Returns build info or None on failure."""
    try:
        result = api.create_and_build(name, description, timeout=BUILD_TIMEOUT)
        log.info(f"  Built project {result['project_id']} -> {result['preview_url']}")
        return result
    except Exception as e:
        log.error(f"  Build failed: {e}")
        return None


def screenshot_one(preview_url: str, output_dir: Path) -> Path | None:
    """Take full-page screenshot. Returns path or None."""
    try:
        from screenshotter import Screenshotter
        s = Screenshotter()
        asyncio.run(s.capture_both(preview_url, str(output_dir)))
        full = output_dir / "screenshot_full.png"
        if full.exists():
            return full
    except Exception as e:
        log.error(f"  Screenshot failed: {e}")
    return None


def score_one(client, screenshot_path: Path, archetype: str, num_runs: int = 3) -> dict | None:
    """Score a screenshot N times, return averaged result dict."""
    from eval_scorer import DesignScorer
    from scoring_rubric import compute_weighted_total, DIMENSIONS

    scorer = DesignScorer(genai_client=client, model="gemini-2.5-flash")
    results = []

    for i in range(num_runs):
        for attempt in range(3):
            try:
                result = scorer.score(screenshot_path, archetype)
                results.append(result)
                break
            except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    wait = 10 * (attempt + 1)
                    log.warning(f"  Scorer 503, waiting {wait}s (attempt {attempt+1}/3)")
                    time.sleep(wait)
                else:
                    log.error(f"  Scorer error: {e}")
                    break
        if i < num_runs - 1:
            time.sleep(3)

    if not results:
        return None

    # Average
    avg_scores = {}
    for dim in DIMENSIONS:
        vals = [r.scores.get(dim.name, 0) for r in results]
        avg_scores[dim.name] = round(sum(vals) / len(vals), 1)

    avg_total = compute_weighted_total(avg_scores)

    return {
        "archetype": archetype,
        "num_runs": len(results),
        "individual_totals": [r.weighted_total for r in results],
        "averaged_scores": avg_scores,
        "averaged_total": avg_total,
    }


def run_eval(label: str, archetypes: list, builds_per_archetype: int, score_runs: int):
    """Run full eval: N builds per archetype, score each, save results."""
    from api_client import BuilderAPI

    api = BuilderAPI("http://localhost:5000")
    if not api.health_check():
        log.error("Backend not running at http://localhost:5000")
        sys.exit(1)

    client = get_genai_client()
    prompts = load_test_prompts()

    results_dir = RESULTS_BASE / label
    results_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}
    start_time = time.time()

    for arch in archetypes:
        prompt = prompts.get(arch)
        if not prompt:
            log.warning(f"No test prompt for '{arch}', skipping")
            continue

        log.info(f"\n{'='*60}")
        log.info(f"ARCHETYPE: {arch} ({builds_per_archetype} builds)")
        log.info(f"{'='*60}")

        arch_scores = []
        arch_dir = results_dir / arch
        arch_dir.mkdir(parents=True, exist_ok=True)

        for b in range(builds_per_archetype):
            build_label = f"{label}_{arch}_build{b+1}"
            build_dir = arch_dir / f"build_{b+1}"
            build_dir.mkdir(parents=True, exist_ok=True)

            log.info(f"\n--- {arch} build {b+1}/{builds_per_archetype} ---")

            # Build
            build_info = build_one(api, build_label, prompt)
            if not build_info:
                arch_scores.append({"build": b+1, "score": None, "error": "build_failed"})
                continue

            # Save build info
            (build_dir / "build_info.json").write_text(json.dumps(build_info, indent=2))

            # Screenshot
            log.info(f"  Taking screenshot...")
            screenshot = screenshot_one(build_info["preview_url"], build_dir)
            if not screenshot:
                arch_scores.append({"build": b+1, "score": None, "error": "screenshot_failed"})
                continue

            # Score
            log.info(f"  Scoring ({score_runs} runs)...")
            score_result = score_one(client, screenshot, arch, score_runs)
            if not score_result:
                arch_scores.append({"build": b+1, "score": None, "error": "scoring_failed"})
                continue

            score_result["build"] = b + 1
            score_result["project_id"] = build_info["project_id"]
            arch_scores.append(score_result)

            # Save individual score
            (build_dir / "scores.json").write_text(json.dumps(score_result, indent=2))
            log.info(f"  Score: {score_result['averaged_total']}/100")

            # Brief pause between builds
            if b < builds_per_archetype - 1:
                time.sleep(SLEEP_BETWEEN_BUILDS)

        # Summarize archetype
        valid_scores = [s["averaged_total"] for s in arch_scores if s.get("averaged_total")]
        summary = {
            "archetype": arch,
            "builds_attempted": builds_per_archetype,
            "builds_succeeded": len(valid_scores),
            "scores": valid_scores,
            "average": round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else None,
            "best": max(valid_scores) if valid_scores else None,
            "worst": min(valid_scores) if valid_scores else None,
            "all_builds": arch_scores,
        }
        all_results[arch] = summary
        (arch_dir / "summary.json").write_text(json.dumps(summary, indent=2))

        if valid_scores:
            log.info(f"\n  {arch} summary: avg={summary['average']}, best={summary['best']}, worst={summary['worst']}")

    # Save overall results
    elapsed = time.time() - start_time
    overall = {
        "label": label,
        "timestamp": datetime.now().isoformat(),
        "elapsed_seconds": round(elapsed),
        "archetypes": all_results,
    }
    (results_dir / "overall.json").write_text(json.dumps(overall, indent=2))

    # Print summary table
    print(f"\n{'='*60}")
    print(f"RESULTS: {label}")
    print(f"{'='*60}")
    print(f"{'Archetype':<16} {'Avg':>6} {'Best':>6} {'Worst':>6} {'N':>3}")
    print("-" * 42)
    for arch, data in all_results.items():
        avg = f"{data['average']:.1f}" if data["average"] else "FAIL"
        best = f"{data['best']:.1f}" if data["best"] else "-"
        worst = f"{data['worst']:.1f}" if data["worst"] else "-"
        n = data["builds_succeeded"]
        print(f"{arch:<16} {avg:>6} {best:>6} {worst:>6} {n:>3}")
    print(f"\nElapsed: {elapsed/60:.1f} minutes")
    print(f"Results saved to: {results_dir}")


def compare_results(label_a: str, label_b: str):
    """Compare two eval runs side by side."""
    dir_a = RESULTS_BASE / label_a
    dir_b = RESULTS_BASE / label_b

    if not dir_a.exists():
        print(f"ERROR: No results found for '{label_a}' at {dir_a}")
        sys.exit(1)
    if not dir_b.exists():
        print(f"ERROR: No results found for '{label_b}' at {dir_b}")
        sys.exit(1)

    data_a = json.loads((dir_a / "overall.json").read_text())
    data_b = json.loads((dir_b / "overall.json").read_text())

    all_archetypes = sorted(set(
        list(data_a["archetypes"].keys()) + list(data_b["archetypes"].keys())
    ))

    print(f"\n{'='*70}")
    print(f"A/B COMPARISON: {label_a} vs {label_b}")
    print(f"{'='*70}")
    print(f"{'Archetype':<16} {'A avg':>7} {'A best':>7} {'B avg':>7} {'B best':>7} {'Delta avg':>10}")
    print("-" * 60)

    a_totals = []
    b_totals = []

    for arch in all_archetypes:
        a = data_a["archetypes"].get(arch, {})
        b = data_b["archetypes"].get(arch, {})

        a_avg = a.get("average")
        a_best = a.get("best")
        b_avg = b.get("average")
        b_best = b.get("best")

        if a_avg: a_totals.append(a_avg)
        if b_avg: b_totals.append(b_avg)

        delta = ""
        if a_avg and b_avg:
            d = a_avg - b_avg
            delta = f"{d:+.1f}"

        print(
            f"{arch:<16} "
            f"{f'{a_avg:.1f}' if a_avg else '-':>7} "
            f"{f'{a_best:.1f}' if a_best else '-':>7} "
            f"{f'{b_avg:.1f}' if b_avg else '-':>7} "
            f"{f'{b_best:.1f}' if b_best else '-':>7} "
            f"{delta:>10}"
        )

    print("-" * 60)
    a_overall = round(sum(a_totals) / len(a_totals), 1) if a_totals else 0
    b_overall = round(sum(b_totals) / len(b_totals), 1) if b_totals else 0
    delta_overall = a_overall - b_overall

    print(f"{'OVERALL':<16} {a_overall:>7.1f} {'':>7} {b_overall:>7.1f} {'':>7} {delta_overall:>+10.1f}")
    print()

    # Generate markdown report
    report_path = RESULTS_BASE / f"comparison_{label_a}_vs_{label_b}.md"
    lines = [
        f"# A/B Comparison: {label_a} vs {label_b}",
        f"",
        f"Generated: {datetime.now().isoformat()}",
        f"",
        f"| Archetype | {label_a} avg | {label_a} best | {label_b} avg | {label_b} best | Delta |",
        f"|-----------|----------:|----------:|----------:|----------:|------:|",
    ]
    for arch in all_archetypes:
        a = data_a["archetypes"].get(arch, {})
        b = data_b["archetypes"].get(arch, {})
        a_avg = a.get("average", "-")
        a_best = a.get("best", "-")
        b_avg = b.get("average", "-")
        b_best = b.get("best", "-")
        delta = ""
        if isinstance(a_avg, (int, float)) and isinstance(b_avg, (int, float)):
            delta = f"{a_avg - b_avg:+.1f}"
        lines.append(f"| {arch} | {a_avg} | {a_best} | {b_avg} | {b_best} | {delta} |")

    lines.extend([
        f"| **OVERALL** | **{a_overall}** | | **{b_overall}** | | **{delta_overall:+.1f}** |",
        "",
        "## Interpretation",
        "",
        f"- Positive delta = {label_a} is better",
        f"- Negative delta = {label_b} is better",
        f"- Expect +/- 5 points of noise per archetype due to build variance",
        f"- Differences > 8 points are likely significant",
    ])

    report_path.write_text("\n".join(lines))
    print(f"Report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="A/B eval comparison")
    sub = parser.add_subparsers(dest="command")

    # Run command
    run_p = sub.add_parser("run", help="Run eval builds and scoring")
    run_p.add_argument("--label", required=True, help="Label for this run (e.g. 'with-kits' or 'no-kits')")
    run_p.add_argument("--builds-per-archetype", type=int, default=3, help="Number of builds per archetype (default: 3)")
    run_p.add_argument("--score-runs", type=int, default=3, help="Scorer runs per screenshot (default: 3)")
    run_p.add_argument("--archetypes", nargs="+", default=ARCHETYPES, help="Archetypes to test")

    # Compare command
    cmp_p = sub.add_parser("compare", help="Compare two eval runs")
    cmp_p.add_argument("label_a", help="First label (shown as column A)")
    cmp_p.add_argument("label_b", help="Second label (shown as column B)")

    args = parser.parse_args()

    if args.command == "run":
        run_eval(args.label, args.archetypes, args.builds_per_archetype, args.score_runs)
    elif args.command == "compare":
        compare_results(args.label_a, args.label_b)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
