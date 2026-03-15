from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from eval.api_client import BuilderAPI, BuildError
from eval.screenshotter import Screenshotter
from utils.componentized_runtime import infer_scaffold_mode

PROMPTS: dict[str, str] = {
    "dashboard": "Build a crypto portfolio tracker with real-time prices, holdings table, and activity feed",
    "game": "Build a Final Fantasy VIII fan page with character profiles for Squall, Rinoa, and Zell, weapons gallery, and world map",
    "ecommerce": "Build a premium streetwear store with product grid, cart drawer, and featured collection",
    "fintech": "Build a stock trading dashboard with candlestick chart, watchlist, and portfolio breakdown",
    "portfolio": "Build a creative developer portfolio with project showcase, skills section, and contact form",
}

BASELINES: dict[str, dict[str, Any]] = {
    "dashboard": {
        "previous_best_score": 81.0,
        "previous_best_score_source": str(ROOT / "eval" / "results" / "dashboard" / "iter_2" / "scores.json"),
        "previous_site_path": str(ROOT / "generated" / "155" / "v1" / "code" / "src" / "index.html"),
    },
    "game": {
        "previous_best_score": 84.5,
        "previous_best_score_source": "benchmark:eval-best-game",
        "previous_site_path": str(ROOT / "generated" / "161" / "v1" / "code" / "src" / "index.html"),
    },
    "ecommerce": {
        "previous_best_score": 88.5,
        "previous_best_score_source": "benchmark:eval-best-ecommerce",
        "previous_site_path": str(ROOT / "generated" / "163" / "v1" / "code" / "src" / "index.html"),
    },
    "fintech": {
        "previous_best_score": 83.5,
        "previous_best_score_source": str(ROOT / "eval" / "results" / "fintech" / "iter_0" / "scores.json"),
        "previous_site_path": str(ROOT / "generated" / "190" / "v1" / "code" / "src" / "index.html"),
    },
    "portfolio": {
        "previous_best_score": 83.5,
        "previous_best_score_source": "benchmark:eval-best-portfolio",
        "previous_site_path": str(ROOT / "generated" / "147" / "v1" / "code" / "src" / "index.html"),
    },
}

DEFAULT_RESULTS_DIR = ROOT / "eval" / "results" / "componentized_validation_parallel"
logger = logging.getLogger(__name__)


def _read_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_preview_build(version_dir: Path) -> dict | None:
    execution = _read_json(version_dir / "last_execution_result.json") or {}
    outputs = execution.get("outputs", {}) if isinstance(execution, dict) else {}
    preview_build = outputs.get("preview_build")
    if isinstance(preview_build, dict):
        return preview_build
    fallback = _read_json(version_dir / "last_preview_build.json")
    return fallback if isinstance(fallback, dict) else None


def _load_plan_data(version_dir: Path) -> dict | None:
    data = _read_json(version_dir / "last_plan.json")
    return data if isinstance(data, dict) else None


def _load_env() -> None:
    env_path = ROOT / "backend" / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _make_summary(results: list[dict[str, Any]]) -> str:
    lines = [f"# Componentized Validation {datetime.now().strftime('%Y-%m-%d')}", ""]
    for item in results:
        lines.append(f"## {item['archetype']}")
        lines.append(f"- Project: {item.get('project_id')} v{item.get('version')}")
        lines.append(f"- Scaffold mode: {item.get('scaffold_mode')}")
        preview_build = item.get("preview_build") or {}
        lines.append(f"- Preview build: {preview_build.get('status')}")
        lines.append(f"- New site: {item.get('preview_path')}")
        lines.append(f"- Previous site: {item.get('previous_site_path')}")
        if item.get("score"):
            lines.append(f"- New score: {item['score'].get('weighted_total')}")
        else:
            lines.append(f"- New score: {item.get('score_error') or 'None'}")
        lines.append(
            f"- Previous best: {item.get('previous_best_score')} ({item.get('previous_best_score_source')})"
        )
        lines.append(f"- Delta: {item.get('delta_vs_previous_best')}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _ensure_backend_available(base_url: str) -> None:
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/health", timeout=5)
    except requests.RequestException as exc:
        raise SystemExit(f"Backend not reachable at {base_url}: {exc}") from exc

    if response.status_code not in (200, 401):
        raise SystemExit(f"Backend not reachable at {base_url}")


def _create_and_build_sync(
    *,
    base_url: str,
    name: str,
    description: str,
    timeout: int,
    enqueue_on_limit: bool,
) -> dict[str, Any]:
    api = BuilderAPI(base_url=base_url)
    return api.create_and_build(
        name=name,
        description=description,
        timeout=timeout,
        enqueue_on_limit=enqueue_on_limit,
    )


def _score_sync(*, screenshot_path: Path, archetype: str, scorer_model: str) -> dict[str, Any]:
    from eval.eval_scorer import DesignScorer
    from eval.reference_loader import ReferenceLoader
    from utils.genai_client import get_genai_client

    scorer = DesignScorer(get_genai_client(), model=scorer_model)
    refs = ReferenceLoader()
    score = scorer.score(
        screenshot_path=screenshot_path,
        archetype=archetype,
        good_references=refs.get_good_examples(archetype),
        bad_references=refs.get_bad_examples(archetype),
    )
    return score.to_dict()


async def _run_archetype(
    *,
    archetype: str,
    prompt: str,
    results_dir: Path,
    base_url: str,
    build_timeout: int,
    enqueue_on_limit: bool,
    wait_seconds: float,
    scorer_model: str,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    async with semaphore:
        item: dict[str, Any] = {
            "archetype": archetype,
            "prompt": prompt,
            **BASELINES[archetype],
            "started_at": datetime.now().isoformat(timespec="seconds"),
        }
        outdir = results_dir / archetype
        outdir.mkdir(parents=True, exist_ok=True)
        start_time = time.perf_counter()
        logger.info("Starting %s validation", archetype)

        try:
            build_result = await asyncio.to_thread(
                _create_and_build_sync,
                base_url=base_url,
                name=f"componentized_{archetype}_{datetime.now().strftime('%H%M%S_%f')}",
                description=prompt,
                timeout=build_timeout,
                enqueue_on_limit=enqueue_on_limit,
            )
            item["project_id"] = build_result["project_id"]
            item["version"] = build_result["version"]

            version_dir = ROOT / "generated" / str(build_result["project_id"]) / f"v{build_result['version']}"
            plan_data = _load_plan_data(version_dir) or {}
            item["scaffold_mode"] = infer_scaffold_mode(version_dir / "code", plan_data=plan_data)
            item["pipeline_result"] = {"result": None}

            preview_build = _load_preview_build(version_dir) or {}
            item["preview_build"] = preview_build
            item["preview_path"] = preview_build.get("dist_index")

            if preview_build.get("status") == "success":
                logger.info(
                    "Preview build succeeded for %s (project=%s v%s)",
                    archetype,
                    item["project_id"],
                    item["version"],
                )
                screenshotter = Screenshotter(viewport_width=1440, viewport_height=900)
                screenshots = await screenshotter.capture_both(
                    url=build_result["preview_url"],
                    output_dir=outdir,
                    wait_seconds=wait_seconds,
                )
                item["screenshots"] = {key: str(value) for key, value in screenshots.items()}
                screenshot_path = screenshots.get("full_page", screenshots["viewport"])
                score_dict = await asyncio.to_thread(
                    _score_sync,
                    screenshot_path=screenshot_path,
                    archetype=archetype,
                    scorer_model=scorer_model,
                )
                item["score"] = score_dict
                item["delta_vs_previous_best"] = round(
                    float(score_dict["weighted_total"]) - float(item["previous_best_score"]),
                    1,
                )
                (outdir / "scores.json").write_text(
                    json.dumps(score_dict, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                logger.info(
                    "Completed %s validation with score %.1f",
                    archetype,
                    float(score_dict["weighted_total"]),
                )
            else:
                item["score_error"] = "preview_unavailable"
                item["delta_vs_previous_best"] = None
                logger.warning(
                    "Preview unavailable for %s (project=%s v%s)",
                    archetype,
                    item.get("project_id"),
                    item.get("version"),
                )
        except BuildError as exc:
            item["build_error"] = str(exc)
            item["score_error"] = "build_failed"
            item["delta_vs_previous_best"] = None
            logger.warning("Build failed for %s: %s", archetype, exc)
        except Exception as exc:
            item["error"] = repr(exc)
            item["score_error"] = "unexpected_error"
            item["delta_vs_previous_best"] = None
            logger.exception("Unexpected error for %s", archetype)

        item["finished_at"] = datetime.now().isoformat(timespec="seconds")
        item["duration_seconds"] = round(time.perf_counter() - start_time, 1)
        (outdir / "result.json").write_text(
            json.dumps(item, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        return item


async def run() -> None:
    _load_env()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="Run componentized validation with bounded parallelism.")
    parser.add_argument("--archetypes", nargs="*")
    parser.add_argument("--label", default="")
    parser.add_argument("--max-parallel", type=int, default=1)
    parser.add_argument("--backend-url", default="http://127.0.0.1:5000")
    parser.add_argument("--build-timeout", type=int, default=900)
    parser.add_argument("--enqueue-on-limit", action="store_true")
    parser.add_argument("--wait-seconds", type=float, default=3.0)
    parser.add_argument("--scorer-model", default="gemini-2.5-flash")
    args = parser.parse_args()

    await asyncio.to_thread(_ensure_backend_available, args.backend_url)

    selected = set(args.archetypes or PROMPTS.keys())
    ordered_archetypes = [name for name in PROMPTS if name in selected]
    results_dir = DEFAULT_RESULTS_DIR if not args.label else ROOT / "eval" / "results" / args.label
    results_dir.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(max(1, args.max_parallel))
    tasks = [
        asyncio.create_task(
            _run_archetype(
                archetype=archetype,
                prompt=PROMPTS[archetype],
                results_dir=results_dir,
                base_url=args.backend_url,
                build_timeout=args.build_timeout,
                enqueue_on_limit=args.enqueue_on_limit,
                wait_seconds=args.wait_seconds,
                scorer_model=args.scorer_model,
                semaphore=semaphore,
            )
        )
        for archetype in ordered_archetypes
    ]

    results = await asyncio.gather(*tasks)

    (results_dir / "results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (results_dir / "summary.md").write_text(_make_summary(results), encoding="utf-8")
    print((results_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    asyncio.run(run())
