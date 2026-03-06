"""
Main orchestrator — entry point for the automated design eval loop.

Usage:
    cd eval && python eval_runner.py
    python eval_runner.py --config eval_config.json
    python eval_runner.py --archetypes dashboard game --max-iterations 3
"""

import asyncio
import json
import sys
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Ensure eval/ is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from api_client import BuilderAPI, BuildError
from screenshotter import Screenshotter
from eval_scorer import DesignScorer
from eval_improver import PromptImprover
from prompt_parser import PromptParser
from reference_loader import ReferenceLoader
from scoring_rubric import ScoringResult
from report_generator import generate_iteration_report, generate_final_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("eval_runner")

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def load_config(config_path: str = "eval_config.json") -> dict:
    """Load eval configuration."""
    p = Path(__file__).resolve().parent / config_path
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_backend_env():
    """Load env vars from backend/.env if not already set."""
    import os
    env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = val


def get_genai_client():
    """Create a Gemini client using the centralized genai_client utility."""
    _load_backend_env()
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.genai_client import get_genai_client as _get_client
    return _get_client()


async def run_eval_loop(config: dict = None):
    """Main eval loop."""
    if config is None:
        config = load_config()

    # Initialize components
    api = BuilderAPI(base_url=config.get("backend_url", "http://localhost:5000"))
    viewport = config.get("screenshot_viewport", [1440, 900])
    screenshotter = Screenshotter(viewport_width=viewport[0], viewport_height=viewport[1])
    parser = PromptParser()
    refs = ReferenceLoader()

    # Check backend health
    if not api.health_check():
        logger.error("Backend not reachable at %s. Is the Flask server running?", config["backend_url"])
        sys.exit(1)

    # Initialize Gemini client + scorers
    client = get_genai_client()
    scorer = DesignScorer(client, model=config.get("scorer_model", "gemini-2.5-flash"))
    improver = PromptImprover(client, model=config.get("improver_model", "gemini-2.5-flash"))

    archetypes = config.get("archetypes", ["dashboard"])
    test_prompts = config.get("test_prompts", {})
    max_iterations = config.get("max_iterations", 5)
    target_score = config.get("target_score", 80)
    score_only = config.get("score_only", False)
    convergence_threshold = config.get("convergence_threshold", 2)
    build_timeout = config.get("build_timeout_seconds", 300)
    wait_seconds = config.get("screenshot_wait_seconds", 3.0)

    # Track scores across iterations
    all_iterations: list[dict[str, dict]] = []
    best_scores: dict[str, float] = {}       # archetype -> best weighted score
    best_prompts: dict[str, str] = {}        # archetype -> prompt text at best score
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 60)
    logger.info("DESIGN EVAL LOOP STARTING")
    logger.info(f"Archetypes: {archetypes}")
    logger.info(f"Max iterations: {max_iterations}, Target: {target_score}")
    logger.info("=" * 60)

    # Backup prompt files before we start
    backups = parser.backup_all_prompt_files()
    logger.info(f"Backed up prompt files: {[str(b) for b in backups]}")

    for iteration in range(max_iterations):
        logger.info(f"\n{'='*60}")
        logger.info(f"ITERATION {iteration}")
        logger.info(f"{'='*60}")

        iteration_scores: dict[str, dict] = {}
        any_improved = False

        for archetype in archetypes:
            logger.info(f"\n--- {archetype} (iter {iteration}) ---")

            output_dir = RESULTS_DIR / archetype / f"iter_{iteration}"
            output_dir.mkdir(parents=True, exist_ok=True)

            # 1. Get test prompt for this archetype
            prompt = test_prompts.get(archetype)
            if not prompt:
                logger.warning(f"No test prompt for '{archetype}', skipping")
                continue

            # 2. Create project and trigger build (with up to 5 attempts)
            build_result = None
            max_build_attempts = 5
            for attempt in range(max_build_attempts):
                project_name = f"eval_{archetype}_iter{iteration}_{run_timestamp}"
                if attempt > 0:
                    project_name += f"_retry{attempt}"
                    logger.info(f"Retrying build for {archetype} (attempt {attempt + 1})")
                try:
                    logger.info(f"Creating project and building: {project_name}")
                    build_result = api.create_and_build(
                        name=project_name,
                        description=prompt,
                        timeout=build_timeout,
                    )
                    preview_url = build_result["preview_url"]
                    logger.info(f"Build complete: {preview_url}")
                    break
                except BuildError as e:
                    logger.error(f"Build failed for {archetype} (attempt {attempt + 1}): {e}")
                    if attempt == max_build_attempts - 1:
                        save_json({"error": str(e)}, output_dir / "build_error.json")
                except Exception as e:
                    logger.error(f"Unexpected error building {archetype} (attempt {attempt + 1}): {e}")
                    if attempt == max_build_attempts - 1:
                        save_json({"error": str(e)}, output_dir / "build_error.json")
            if build_result is None:
                continue

            # 3. Screenshot the preview
            try:
                screenshots = await screenshotter.capture_both(
                    url=preview_url,
                    output_dir=output_dir,
                    wait_seconds=wait_seconds,
                )
                # Use full-page screenshot for scoring so the scorer can see
                # ALL sections (hero, features, pricing, footer, etc.), not just
                # the above-fold viewport. This is critical for data_completeness.
                screenshot_path = screenshots.get("full_page", screenshots["viewport"])
                logger.info(f"Screenshots captured: {list(screenshots.keys())} — scoring with {'full_page' if 'full_page' in screenshots else 'viewport'}")
            except Exception as e:
                logger.error(f"Screenshot failed for {archetype}: {e}")
                save_json({"error": f"Screenshot failed: {e}"}, output_dir / "screenshot_error.json")
                continue

            # 4. Score the screenshot
            good_refs = refs.get_good_examples(archetype)
            bad_refs = refs.get_bad_examples(archetype)

            try:
                scores = scorer.score(
                    screenshot_path=screenshot_path,
                    archetype=archetype,
                    good_references=good_refs,
                    bad_references=bad_refs,
                )
                scores_dict = scores.to_dict()
                save_json(scores_dict, output_dir / "scores.json")
                iteration_scores[archetype] = scores_dict
                logger.info(f"Score: {scores.weighted_total}/100")
            except Exception as e:
                logger.error(f"Scoring failed for {archetype}: {e}")
                save_json({"error": f"Scoring failed: {e}"}, output_dir / "scoring_error.json")
                continue

            # 5. Rollback check — if score dropped, revert to best prompt
            prev_best = best_scores.get(archetype)
            rolled_back = False
            if prev_best is not None and scores.weighted_total < prev_best - 2:
                logger.warning(
                    f"{archetype}: Score DROPPED {prev_best} -> {scores.weighted_total}. "
                    f"Rolling back to best prompt."
                )
                if archetype in best_prompts:
                    parser.replace_section(archetype, best_prompts[archetype])
                    save_text(best_prompts[archetype], output_dir / "prompt_rollback.txt")
                    logger.info(f"Rolled back {archetype} prompt to best version (score {prev_best})")
                    rolled_back = True
                # Skip improvement after rollback — re-improving the same prompt
                # tends to produce the same destabilizing changes that caused
                # the regression in the first place.

            # Track best score and prompt
            if prev_best is None or scores.weighted_total > prev_best:
                best_scores[archetype] = scores.weighted_total
                best_prompts[archetype] = parser.extract_section(archetype)
                logger.info(f"New best score for {archetype}: {scores.weighted_total}")

            # 6. Check if improvement is needed
            if score_only:
                logger.info(f"{archetype}: Score-only mode, skipping improvement")
                continue

            if scores.weighted_total >= target_score:
                logger.info(
                    f"{archetype}: Score {scores.weighted_total} >= target {target_score}, "
                    f"skipping improvement"
                )
                continue

            # 6b. Skip improvement if we just rolled back
            if rolled_back:
                logger.info(
                    f"{archetype}: Skipping improvement after rollback — "
                    f"will retry with best prompt next iteration"
                )
                continue

            # 7. Extract current prompt and improve it
            try:
                current_prompt = parser.extract_section(archetype)
                save_text(current_prompt, output_dir / "prompt_before.txt")

                new_prompt = improver.improve(
                    archetype=archetype,
                    current_prompt=current_prompt,
                    scores=scores_dict,
                    screenshot_path=screenshot_path,
                    good_references=good_refs,
                )
                save_text(new_prompt, output_dir / "prompt_after.txt")

                # 8. Update engineer.txt
                parser.replace_section(archetype, new_prompt)
                logger.info(f"Updated engineer.txt with improved {archetype} prompt")
                any_improved = True

            except Exception as e:
                logger.error(f"Prompt improvement failed for {archetype}: {e}")
                save_json({"error": f"Improvement failed: {e}"}, output_dir / "improve_error.json")
                continue

        # 9. Save iteration scores
        all_iterations.append(iteration_scores)

        # 10. Generate iteration report
        prev_scores = all_iterations[-2] if len(all_iterations) >= 2 else None
        report = generate_iteration_report(
            iteration=iteration,
            scores_by_archetype=iteration_scores,
            prev_scores_by_archetype=prev_scores,
            output_dir=RESULTS_DIR,
        )
        logger.info(f"\n{report}")

        # 11. Check for convergence (need 3+ iterations to detect plateau)
        if len(all_iterations) >= 3 and not _any_significant_improvement(
            all_iterations[-2], all_iterations[-1], convergence_threshold
        ):
            logger.info(
                f"Convergence reached — no archetype improved by more than "
                f"{convergence_threshold} points. Stopping."
            )
            break

        if not any_improved:
            logger.info("No archetypes needed improvement this iteration.")
            break

    # Final report
    final_report = generate_final_report(all_iterations, output_dir=RESULTS_DIR)
    logger.info(f"\n{'='*60}")
    logger.info("FINAL REPORT")
    logger.info(f"{'='*60}")
    logger.info(f"\n{final_report}")

    return all_iterations


def _any_significant_improvement(
    prev_scores: dict[str, dict],
    curr_scores: dict[str, dict],
    threshold: float,
) -> bool:
    """Check if any archetype improved by more than threshold points."""
    for archetype in curr_scores:
        if archetype not in prev_scores:
            continue
        prev_total = prev_scores[archetype].get("weighted_total", 0)
        curr_total = curr_scores[archetype].get("weighted_total", 0)
        if curr_total - prev_total > threshold:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Automated Design Eval Loop")
    parser.add_argument("--config", default="eval_config.json", help="Config file path")
    parser.add_argument("--archetypes", nargs="+", help="Override archetypes to eval")
    parser.add_argument("--max-iterations", type=int, help="Override max iterations")
    parser.add_argument("--target-score", type=float, help="Override target score")
    parser.add_argument("--dry-run", action="store_true", help="Print config and exit")
    parser.add_argument("--score-only", action="store_true", help="Score only, skip prompt improvement")
    args = parser.parse_args()

    config = load_config(args.config)

    # Apply CLI overrides
    if args.archetypes:
        config["archetypes"] = args.archetypes
    if args.max_iterations:
        config["max_iterations"] = args.max_iterations
    if args.target_score:
        config["target_score"] = args.target_score
    if args.score_only:
        config["score_only"] = True

    if args.dry_run:
        print(json.dumps(config, indent=2))
        return

    asyncio.run(run_eval_loop(config))


if __name__ == "__main__":
    main()
