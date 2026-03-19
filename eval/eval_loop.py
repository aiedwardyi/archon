"""
Simple eval loop — build one archetype, screenshot, score, report.

Usage:
    cd eval && python eval_loop.py --archetype dashboard
    python eval_loop.py --archetype dashboard --runs 3
    python eval_loop.py --archetype dashboard fintech portfolio --runs 3
"""

import argparse
import asyncio
import json
import os
import sys
import time
import logging
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api_client import BuilderAPI, BuildError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("eval_loop")

RESULTS_DIR = Path(__file__).resolve().parent / "results"

PROMPTS = {
    "dashboard": "Build a crypto portfolio tracker with real-time prices, holdings table, and activity feed",
    "fintech": "Build a stock trading dashboard with candlestick chart, watchlist, and portfolio breakdown",
    "portfolio": "Build a creative developer portfolio with project showcase, skills section, and contact form",
    "ecommerce": "Build a premium streetwear store with product grid, cart drawer, and featured collection",
    "saas_landing": "Build a landing page for an AI-powered writing assistant called WriteFlow",
    "editor": "Build a collaborative product brief editor with formatting toolbar, document outline, inline comments, and publish controls",
    "form": "Build a premium multi-step onboarding wizard for an AI automation platform with plan selection, workspace details, integrations, validation, and success state",
    "game": "Build a Final Fantasy VIII fan page with character profiles for Squall, Rinoa, and Zell, weapons gallery, and world map",
}

BASELINES = {
    "dashboard": 81.0,
    "fintech": 83.5,
    "portfolio": 83.5,
    "ecommerce": 88.5,
    "saas_landing": 76.0,
    "editor": 78.5,
    "form": 75.0,
    "game": 88.0,
}


def get_genai_client():
    env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = val
    from utils.genai_client import get_genai_client as _factory
    return _factory()


async def take_screenshot(url: str, output_path: Path, retries: int = 3) -> Path:
    """Take screenshot with retry logic for WinError 5."""
    from playwright.async_api import async_playwright

    output_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(retries):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1440, "height": 900},
                    device_scale_factor=2,
                )
                page = await context.new_page()

                # Collect console errors
                errors = []
                page.on("pageerror", lambda err: errors.append(str(err)))

                try:
                    await page.goto(url, wait_until="networkidle", timeout=60000)
                except Exception as e:
                    logger.warning(f"Navigation issue (proceeding): {e}")

                # Wait for React to render
                await asyncio.sleep(5)

                # Check if the page rendered (not just placeholder)
                root_html = await page.evaluate(
                    "document.getElementById('root')?.innerHTML?.length || 0"
                )
                if root_html < 100:
                    logger.warning(f"Root element has only {root_html} chars — may be placeholder")
                    # Extra wait
                    await asyncio.sleep(5)

                if errors:
                    logger.warning(f"Page errors: {errors[:3]}")

                # Write to temp file first, then move (avoids WinError 5)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = tmp.name
                try:
                    # Full page screenshot
                    page_height = await page.evaluate("document.documentElement.scrollHeight")
                    if page_height > 15000:
                        await page.screenshot(
                            path=tmp_path, full_page=False, type="png",
                            clip={"x": 0, "y": 0, "width": 1440, "height": 15000},
                        )
                    else:
                        await page.screenshot(path=tmp_path, full_page=True, type="png")

                    await browser.close()
                    shutil.move(tmp_path, str(output_path))
                    logger.info(f"Screenshot saved: {output_path}")
                    return output_path
                except Exception as e:
                    await browser.close()
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    raise

        except Exception as e:
            logger.warning(f"Screenshot attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                raise
            await asyncio.sleep(2)

    raise RuntimeError("Screenshot failed after all retries")


def score_screenshot(scorer, screenshot_path: Path, archetype: str, refs_loader) -> dict:
    """Score a screenshot using Gemini vision."""
    good_refs = refs_loader.get_good_examples(archetype)
    bad_refs = refs_loader.get_bad_examples(archetype)
    result = scorer.score(
        screenshot_path=screenshot_path,
        archetype=archetype,
        good_references=good_refs,
        bad_references=bad_refs,
    )
    return result.to_dict()


async def run_single(api, archetype: str, prompt: str, build_timeout: int = 600, max_build_attempts: int = 5, skip_image_gen: bool = False) -> dict:
    """Build one project, screenshot, return result. Retries if preview build fails."""
    repo_root = Path(__file__).resolve().parent.parent

    for attempt in range(max_build_attempts):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = f"eval_{archetype}_{timestamp}"
        if attempt > 0:
            project_name += f"_retry{attempt}"
            logger.info(f"Retry {attempt + 1}/{max_build_attempts} after 30s cooldown...")
            await asyncio.sleep(30)

        logger.info(f"Building: {project_name}")
        try:
            build_result = api.create_and_build(
                name=project_name,
                description=prompt,
                timeout=build_timeout,
                skip_image_gen=skip_image_gen,
            )
        except BuildError as e:
            logger.error(f"Build failed: {e}")
            if attempt == max_build_attempts - 1:
                return {"archetype": archetype, "status": "build_failed", "error": str(e)}
            continue
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "TOO MANY" in error_str:
                logger.warning("429 Too Many Requests — waiting 60s before retry...")
                await asyncio.sleep(60)
            else:
                logger.error(f"Unexpected error: {e}")
            if attempt == max_build_attempts - 1:
                return {"archetype": archetype, "status": "error", "error": error_str}
            continue

        project_id = build_result["project_id"]
        version = build_result.get("version", 1)
        preview_url = build_result["preview_url"]

        # Check if the componentized build produced dist/
        dist_dir = repo_root / "generated" / str(project_id) / f"v{version}" / "code" / "dist"
        if not dist_dir.exists():
            # Try triggering preview endpoint which may rebuild
            logger.info(f"Build {project_id} has no dist/ — triggering preview rebuild...")
            try:
                import requests as req
                req.get(preview_url, timeout=120)
            except Exception:
                pass
            if not dist_dir.exists():
                logger.warning(f"Build {project_id} still has no dist/ after rebuild attempt, retrying...")
                if attempt == max_build_attempts - 1:
                    return {
                        "archetype": archetype,
                        "project_id": project_id,
                        "status": "preview_build_failed",
                        "error": "No dist/ directory after build — componentized preview failed",
                    }
                continue

        logger.info(f"Build complete: project {project_id}, preview: {preview_url}")
        break

    # Screenshot
    output_dir = RESULTS_DIR / f"eval_loop_{timestamp}" / archetype
    screenshot_path = output_dir / "screenshot_full.png"
    try:
        await take_screenshot(preview_url, screenshot_path)
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return {
            "archetype": archetype,
            "project_id": project_id,
            "version": version,
            "status": "screenshot_failed",
            "error": str(e),
        }

    return {
        "archetype": archetype,
        "project_id": project_id,
        "version": version,
        "preview_url": preview_url,
        "screenshot_path": str(screenshot_path),
        "output_dir": str(output_dir),
        "status": "success",
    }


async def eval_archetype(archetype: str, runs: int = 3, build_timeout: int = 600, skip_image_gen: bool = False) -> dict:
    """Run N builds of an archetype, score each, return averaged results."""
    prompt = PROMPTS.get(archetype)
    if not prompt:
        logger.error(f"No prompt for archetype '{archetype}'")
        return {"archetype": archetype, "error": "no prompt"}

    api = BuilderAPI(base_url="http://localhost:5000")
    client = get_genai_client()

    from eval_scorer import DesignScorer
    from reference_loader import ReferenceLoader

    scorer = DesignScorer(client, model="gemini-2.5-flash")
    refs_loader = ReferenceLoader()

    all_scores = []
    all_results = []

    for run_idx in range(runs):
        logger.info(f"\n{'='*40}")
        logger.info(f"{archetype} — Run {run_idx + 1}/{runs}")
        logger.info(f"{'='*40}")

        result = await run_single(api, archetype, prompt, build_timeout, skip_image_gen=skip_image_gen)
        if result["status"] != "success":
            logger.warning(f"Run {run_idx + 1} failed: {result.get('error')}")
            all_results.append(result)
            # Cool down before retry
            if run_idx < runs - 1:
                logger.info("Cooling down 30s before next run...")
                await asyncio.sleep(30)
            continue

        # Score it
        screenshot_path = Path(result["screenshot_path"])
        try:
            scores = score_screenshot(scorer, screenshot_path, archetype, refs_loader)
            result["scores"] = scores
            weighted = scores.get("weighted_total", 0)
            result["weighted_total"] = weighted
            all_scores.append(weighted)
            logger.info(f"Score: {weighted}/100")
            logger.info(f"Dimensions: {scores.get('scores', {})}")

            # Save individual result
            output_dir = Path(result["output_dir"])
            with open(output_dir / "result.json", "w") as f:
                json.dump(result, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            result["scoring_error"] = str(e)

        all_results.append(result)

        # Cool down between runs
        if run_idx < runs - 1:
            logger.info("Cooling down 30s before next run...")
            await asyncio.sleep(30)

    # Compute summary
    baseline = BASELINES.get(archetype, 0)
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    summary = {
        "archetype": archetype,
        "runs": runs,
        "successful_runs": len(all_scores),
        "individual_scores": all_scores,
        "average_score": round(avg_score, 1),
        "baseline": baseline,
        "delta_vs_baseline": round(avg_score - baseline, 1),
        "results": all_results,
        "timestamp": datetime.now().isoformat(),
    }

    logger.info(f"\n{'='*50}")
    logger.info(f"SUMMARY: {archetype}")
    logger.info(f"Average: {avg_score:.1f} / Baseline: {baseline} / Delta: {avg_score - baseline:+.1f}")
    logger.info(f"Individual: {all_scores}")
    logger.info(f"{'='*50}")

    return summary


async def main():
    parser = argparse.ArgumentParser(description="Simple eval loop")
    parser.add_argument("--archetype", "-a", nargs="+", default=["dashboard"],
                        help="Archetype(s) to eval")
    parser.add_argument("--runs", "-r", type=int, default=3,
                        help="Number of scoring runs per archetype")
    parser.add_argument("--timeout", "-t", type=int, default=900,
                        help="Build timeout in seconds")
    parser.add_argument("--skip-image-gen", action="store_true",
                        help="Skip Design Agent image generation (saves ~$0.05 + ~30s per build)")
    args = parser.parse_args()

    all_summaries = {}
    for arch in args.archetype:
        summary = await eval_archetype(arch, runs=args.runs, build_timeout=args.timeout, skip_image_gen=args.skip_image_gen)
        all_summaries[arch] = summary

    # Print final table
    print("\n" + "=" * 70)
    print("EVAL LOOP RESULTS")
    print("=" * 70)
    print(f"{'Archetype':<15} {'Avg':>6} {'Baseline':>8} {'Delta':>7} {'Runs':>5} {'Scores'}")
    print("-" * 70)
    for arch, s in all_summaries.items():
        scores_str = ", ".join(f"{x:.0f}" for x in s.get("individual_scores", []))
        print(f"{arch:<15} {s['average_score']:>6.1f} {s['baseline']:>8.1f} {s['delta_vs_baseline']:>+7.1f} {s['successful_runs']:>5} [{scores_str}]")

    # Save combined results
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = RESULTS_DIR / f"eval_loop_{ts}_summary.json"
    with open(summary_path, "w") as f:
        json.dump(all_summaries, f, indent=2, default=str)
    logger.info(f"Summary saved: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
