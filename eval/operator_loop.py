"""
Manual-style eval operator loop with one-change baseline/B-test experiments.

This script keeps the existing build/screenshot/score stack, but replaces the
old multi-iteration auto-rewriter flow with a single-cycle operator workflow:

1. Determine weakest archetype from current artifacts or a fresh score-only pass.
2. Run 3 baseline builds for that archetype.
3. Pick the weakest dimensions and one edit lever.
4. Apply one targeted prompt/kit change.
5. Run 3 B-test builds.
6. Keep the change only if the average improves by > 1.0.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.genai import types as genai_types

# Ensure eval/ and repo root are on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api_client import BuilderAPI, BuildError
from eval_improver import PromptImprover
from eval_runner import get_genai_client, load_config, save_json
from eval_scorer import DesignScorer
from prompt_parser import PromptParser
from reference_loader import ReferenceLoader
from utils.model_provider import create_scorer_provider, create_improver_provider
from screenshotter import Screenshotter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("operator_loop")

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = Path(__file__).resolve().parent / "results"
OPERATOR_RESULTS_DIR = RESULTS_DIR / "operator_loop"
LOG_PATH = RESULTS_DIR / "operator_improvements.md"
OVERNIGHT_SUMMARY_PATH = RESULTS_DIR / "overnight_summary.md"
CHECKPOINT_PATH = RESULTS_DIR / "checkpoint.md"

DEFAULT_TRACKED_ARCHETYPES = [
    "dashboard",
    "game",
    "saas_landing",
    "ecommerce",
    "portfolio",
    "fintech",
    "editor",
    "form",
]
DIMENSION_PRIORITY = [
    "data_completeness",
    "layout_precision",
    "visual_hierarchy",
    "typography",
    "depth_polish",
    "interactivity_cues",
    "color_system",
    "overall_impression",
]

KIT_EDITOR_SYSTEM_PROMPT = """\
You edit one prompt-kit file for a web UI generator.

Your task is to make ONE surgical improvement aimed at the weakest scoring
dimension(s), while preserving the file's existing structure and voice.

Rules:
- Output ONLY the full updated file contents.
- Keep the file ASCII unless it already contains non-ASCII.
- Preserve headings, separators, and most existing instructions.
- Do not shorten the file.
- Make one coherent change cluster, not a broad rewrite.
- Prefer adding or tightening explicit requirements over deleting content.
- If editing CSS, return valid CSS only.
- If editing a .txt kit, keep the instructional format intact.
"""


@dataclass
class SampleRun:
    run_index: int
    archetype: str
    weighted_total: float
    scores: dict[str, float]
    output_dir: Path
    project_id: int | None = None
    version: int | None = None
    preview_url: str | None = None


@dataclass
class SampleSet:
    archetype: str
    phase: str
    runs: list[SampleRun]

    @property
    def average_total(self) -> float:
        if not self.runs:
            return 0.0
        return round(sum(r.weighted_total for r in self.runs) / len(self.runs), 2)

    @property
    def average_scores(self) -> dict[str, float]:
        if not self.runs:
            return {}
        keys = sorted({k for r in self.runs for k in r.scores.keys()})
        averages: dict[str, float] = {}
        for key in keys:
            values = [r.scores.get(key, 0.0) for r in self.runs]
            averages[key] = round(sum(values) / len(values), 2)
        return averages

    @property
    def representative_run(self) -> SampleRun | None:
        if not self.runs:
            return None
        return min(self.runs, key=lambda run: abs(run.weighted_total - self.average_total))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def resolve_tracked_archetypes(
    config: dict[str, Any],
    cli_archetypes: list[str] | None,
) -> list[str]:
    configured = cli_archetypes or config.get("archetypes") or DEFAULT_TRACKED_ARCHETYPES
    seen: set[str] = set()
    ordered: list[str] = []
    for archetype in configured:
        name = str(archetype).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return ordered or list(DEFAULT_TRACKED_ARCHETYPES)


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def verify_branch(expected_branch: str | None) -> str:
    branch = run_git(["branch", "--show-current"]).strip()
    if expected_branch and branch != expected_branch:
        raise RuntimeError(f"Expected branch '{expected_branch}', found '{branch}'")
    return branch


def load_env_from_backend() -> None:
    env_path = REPO_ROOT / "backend" / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


def cycle_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def phase_dir(archetype: str, phase: str, stamp: str) -> Path:
    return OPERATOR_RESULTS_DIR / stamp / archetype / phase


def parse_operator_log_entries() -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []

    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("### Cycle "):
            if current:
                entries.append(current)
            current = {"header": line}
            continue
        if current is None or not line.startswith("- "):
            continue
        if ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        current[key.strip().lower().replace(" ", "_")] = value.strip()

    if current:
        entries.append(current)
    return entries


def parse_float(value: str | None) -> float | None:
    if not value:
        return None
    cleaned = value.strip()
    if cleaned.lower() == "pending":
        return None
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    try:
        return float(cleaned)
    except ValueError:
        return None


def read_latest_operator_log_score(archetype: str) -> float | None:
    entries = parse_operator_log_entries()
    best_committed: float | None = None
    for entry in reversed(entries):
        if entry.get("archetype") != archetype:
            continue

        verdict = (entry.get("verdict") or "").lower()
        test_avg = parse_float(entry.get("test_average_across_3_runs"))
        baseline_avg = parse_float(entry.get("baseline_average_across_3_runs"))

        if verdict in {"committed", "kept"} and test_avg is not None:
            best_committed = max(best_committed, test_avg) if best_committed is not None else test_avg
            continue
        if baseline_avg is not None:
            return best_committed if best_committed is not None else baseline_avg
    return best_committed


def compute_average_from_score_paths(score_paths: list[Path]) -> float | None:
    totals: list[float] = []
    for score_path in score_paths:
        try:
            data = json.loads(score_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        weighted = data.get("weighted_total")
        if weighted is None:
            continue
        totals.append(float(weighted))
    if not totals:
        return None
    return round(sum(totals) / len(totals), 2)


def _normalize_archetype_label(label: str) -> str:
    raw = label.strip().lower()
    mapping = {
        "game (ff8)": "game",
        "saas landing": "saas_landing",
    }
    return mapping.get(raw, raw.replace(" ", "_").replace("-", "_"))


def parse_best_scores_from_markdown(
    path: Path,
    tracked_archetypes: list[str] | None = None,
) -> dict[str, float]:
    if not path.exists():
        return {}

    allowed = set(tracked_archetypes or [])
    scores: dict[str, float] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 2:
            continue
        archetype = _normalize_archetype_label(parts[0])
        if allowed and archetype not in allowed:
            continue

        numeric_values: list[float] = []
        for part in parts[1:]:
            cleaned = part.replace("**", "").replace("+", "").strip()
            try:
                numeric_values.append(float(cleaned))
            except ValueError:
                continue
        if numeric_values:
            scores[archetype] = max(numeric_values)
    return scores


def read_summary_score(
    archetype: str,
    tracked_archetypes: list[str] | None = None,
) -> float | None:
    for path in [OVERNIGHT_SUMMARY_PATH, CHECKPOINT_PATH]:
        scores = parse_best_scores_from_markdown(path, tracked_archetypes=tracked_archetypes)
        if archetype in scores:
            return scores[archetype]
    return None


def read_latest_operator_results_score(archetype: str) -> float | None:
    if not OPERATOR_RESULTS_DIR.exists():
        return None

    latest: tuple[str, float] | None = None
    for cycle_dir in sorted([p for p in OPERATOR_RESULTS_DIR.iterdir() if p.is_dir()]):
        archetype_dir = cycle_dir / archetype
        if not archetype_dir.exists():
            continue

        baseline_paths = sorted((archetype_dir / "baseline").glob("run_*/scores.json"))
        b_test_paths = sorted((archetype_dir / "b_test").glob("run_*/scores.json"))
        baseline_avg = compute_average_from_score_paths(baseline_paths)
        b_test_avg = compute_average_from_score_paths(b_test_paths)

        score = b_test_avg if b_test_avg is not None else baseline_avg
        if score is None:
            continue
        latest = (cycle_dir.name, score)

    if latest is None:
        return None
    return latest[1]


def read_latest_weighted_total(
    archetype: str,
    tracked_archetypes: list[str] | None = None,
) -> float | None:
    operator_log_score = read_latest_operator_log_score(archetype)
    if operator_log_score is not None:
        return operator_log_score

    summary_score = read_summary_score(archetype, tracked_archetypes=tracked_archetypes)
    if summary_score is not None:
        return summary_score

    operator_results_score = read_latest_operator_results_score(archetype)
    if operator_results_score is not None:
        return operator_results_score

    archetype_dir = RESULTS_DIR / archetype
    if not archetype_dir.exists():
        return None
    latest_score: float | None = None
    for score_path in sorted(archetype_dir.glob("iter_*/scores.json")):
        try:
            data = json.loads(score_path.read_text(encoding="utf-8"))
            latest_score = float(data.get("weighted_total", 0.0))
        except Exception:
            continue
    return latest_score


async def run_sample_builds(
    *,
    config: dict[str, Any],
    api: BuilderAPI,
    screenshotter: Screenshotter,
    scorer: DesignScorer,
    refs: ReferenceLoader,
    archetype: str,
    runs: int,
    phase: str,
    stamp: str,
) -> SampleSet:
    prompt = config["test_prompts"][archetype]
    wait_seconds = config.get("screenshot_wait_seconds", 3.0)
    build_timeout = config.get("build_timeout_seconds", 600)
    sample_runs: list[SampleRun] = []

    for run_index in range(runs):
        output_dir = phase_dir(archetype, phase, stamp) / f"run_{run_index}"
        output_dir.mkdir(parents=True, exist_ok=True)
        project_name = f"operator_{archetype}_{phase}_{stamp}_{run_index}"
        log.info("%s %s run %s: build start", archetype, phase, run_index)

        build_result = api.create_and_build(
            name=project_name,
            description=prompt,
            timeout=build_timeout,
        )
        preview_url = build_result["preview_url"]

        screenshots = await screenshotter.capture_both(
            url=preview_url,
            output_dir=output_dir,
            wait_seconds=wait_seconds,
        )
        screenshot_path = screenshots.get("full_page", screenshots["viewport"])

        score_result = scorer.score(
            screenshot_path=screenshot_path,
            archetype=archetype,
            good_references=refs.get_good_examples(archetype),
            bad_references=refs.get_bad_examples(archetype),
        )
        scores_dict = score_result.to_dict()
        save_json(scores_dict, output_dir / "scores.json")
        save_json(build_result, output_dir / "build.json")

        sample_runs.append(
            SampleRun(
                run_index=run_index,
                archetype=archetype,
                weighted_total=score_result.weighted_total,
                scores=scores_dict.get("scores", {}),
                output_dir=output_dir,
                project_id=build_result.get("project_id"),
                version=build_result.get("version"),
                preview_url=preview_url,
            )
        )
        log.info("%s %s run %s: %.1f", archetype, phase, run_index, score_result.weighted_total)

    return SampleSet(archetype=archetype, phase=phase, runs=sample_runs)


async def choose_weakest_archetype(
    *,
    tracked_archetypes: list[str],
    refresh_if_missing: bool,
    config: dict[str, Any],
    api: BuilderAPI,
    screenshotter: Screenshotter,
    scorer: DesignScorer,
    refs: ReferenceLoader,
    stamp: str,
) -> str:
    current_scores = {
        name: read_latest_weighted_total(name, tracked_archetypes=tracked_archetypes)
        for name in tracked_archetypes
    }
    if refresh_if_missing and any(score is None for score in current_scores.values()):
        log.info("Missing comparable scores, running one score-only sample for tracked archetypes")
        refreshed: dict[str, float] = {}
        for archetype in tracked_archetypes:
            sample = await run_sample_builds(
                config=config,
                api=api,
                screenshotter=screenshotter,
                scorer=scorer,
                refs=refs,
                archetype=archetype,
                runs=1,
                phase="refresh",
                stamp=stamp,
            )
            refreshed[archetype] = sample.average_total
        current_scores = refreshed

    missing = [k for k, v in current_scores.items() if v is None]
    if missing:
        raise RuntimeError(f"Missing scores for archetypes: {missing}")

    weakest = min(current_scores.items(), key=lambda item: float(item[1]))[0]
    log.info("Weakest archetype: %s (%s)", weakest, current_scores[weakest])
    return weakest


def pick_weak_dimensions(sample_set: SampleSet) -> list[str]:
    averages = sample_set.average_scores
    weak = [dim for dim, avg in averages.items() if avg < 7.0]
    weak.sort(key=lambda dim: (averages.get(dim, 10.0), DIMENSION_PRIORITY.index(dim) if dim in DIMENSION_PRIORITY else 999))
    return weak[:2]


def choose_edit_target(archetype: str, weak_dimensions: list[str]) -> tuple[str, Path | None]:
    primary = weak_dimensions[0] if weak_dimensions else "overall_impression"
    parser = PromptParser()
    engineer_available = parser.has_section(archetype)

    if primary in {"visual_hierarchy", "layout_precision", "data_completeness", "overall_impression"}:
        if engineer_available:
            return ("engineer", None)
        log.info(
            "No engineer.txt section found for %s; falling back to archetype kit text file",
            archetype,
        )
        return ("kit_txt", REPO_ROOT / "prompts" / "archetypes" / f"{archetype}.txt")
    if primary == "depth_polish":
        return ("kit_css", REPO_ROOT / "prompts" / "archetypes" / f"{archetype}.css")
    return ("kit_txt", REPO_ROOT / "prompts" / "archetypes" / f"{archetype}.txt")


def edit_engineer_section(
    *,
    client: Any,
    config: dict[str, Any],
    archetype: str,
    sample_set: SampleSet,
) -> tuple[Path, str, str]:
    parser = PromptParser()
    current = parser.extract_section(archetype)
    representative = sample_set.representative_run
    if representative is None:
        raise RuntimeError("No representative baseline run available")

    improver_provider = create_improver_provider(config, genai_client=client)
    improver = PromptImprover(client, model=config.get("improver_model", "gemini-2.5-flash"), provider=improver_provider)
    scores_payload = {
        "scores": sample_set.average_scores,
        "weighted_total": sample_set.average_total,
        "issues": [],
        "strengths": [],
        "specific_improvements": [],
    }
    updated = improver.improve(
        archetype=archetype,
        current_prompt=current,
        scores=scores_payload,
        screenshot_path=representative.output_dir / "full_page.png",
        good_references=ReferenceLoader().get_good_examples(archetype),
    )
    parser.replace_section(archetype, updated)
    return (parser.engineer_path, current, read_text(parser.engineer_path))


def edit_kit_file(
    *,
    client: Any,
    config: dict[str, Any],
    archetype: str,
    sample_set: SampleSet,
    target_path: Path,
) -> tuple[Path, str, str]:
    current = read_text(target_path)
    weak_dims = pick_weak_dimensions(sample_set)
    representative = sample_set.representative_run
    screenshot_path = representative.output_dir / "full_page.png" if representative else None

    contents: list[Any] = [
        genai_types.Part.from_text(text=f"ARCHETYPE: {archetype}"),
        genai_types.Part.from_text(text=f"TARGET FILE: {target_path.name}"),
        genai_types.Part.from_text(
            text=(
                "CURRENT FILE CONTENT:\n"
                f"```\n{current}\n```"
            )
        ),
        genai_types.Part.from_text(
            text=(
                f"AVERAGE WEIGHTED TOTAL: {sample_set.average_total}\n"
                f"AVERAGE DIMENSION SCORES:\n{json.dumps(sample_set.average_scores, indent=2)}\n"
                f"WEAKEST DIMENSIONS UNDER 7.0: {', '.join(weak_dims) if weak_dims else 'none'}"
            )
        ),
    ]

    if screenshot_path and screenshot_path.exists():
        image_bytes = screenshot_path.read_bytes()
        contents.append(genai_types.Part.from_text(text="REFERENCE SCREENSHOT OF CURRENT OUTPUT:"))
        contents.append(genai_types.Part.from_bytes(data=image_bytes, mime_type="image/png"))

    contents.append(
        genai_types.Part.from_text(
            text=(
                "Make one targeted improvement cluster in this file that specifically addresses "
                f"{', '.join(weak_dims) if weak_dims else 'the weakest visible quality gap'}. "
                "Preserve the file's structure and return the full updated file."
            )
        )
    )

    response = client.models.generate_content(
        model=config.get("improver_model", "gemini-2.5-flash"),
        contents=contents,
        config={
            "system_instruction": KIT_EDITOR_SYSTEM_PROMPT,
            "temperature": 0.3,
            "max_output_tokens": 16000,
        },
    )
    updated = (getattr(response, "text", "") or "").strip()
    if updated.startswith("```"):
        updated = updated.split("\n", 1)[1]
        if updated.endswith("```"):
            updated = updated[:-3]
        updated = updated.strip()
    if len(updated) < len(current) * 0.5:
        raise RuntimeError(f"Updated {target_path.name} looks truncated")

    write_text(target_path, updated + ("\n" if not updated.endswith("\n") else ""))
    return (target_path, current, read_text(target_path))


def restore_file(path: Path, content: str) -> None:
    write_text(path, content)


def next_cycle_number() -> int:
    if not LOG_PATH.exists():
        return 1
    text = LOG_PATH.read_text(encoding="utf-8")
    numbers: list[int] = []
    for line in text.splitlines():
        if line.startswith("### Cycle "):
            try:
                part = line.split("### Cycle ", 1)[1].split(" - ", 1)[0]
                numbers.append(int(part))
            except Exception:
                continue
    return max(numbers, default=0) + 1


def append_log_entry(
    *,
    cycle_number: int,
    archetype: str,
    baseline: SampleSet,
    weak_dimensions: list[str],
    exact_change: str,
    changed_file: Path,
    b_test: SampleSet,
    verdict: str,
    notes: str,
    next_hypothesis: str,
) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    delta = round(b_test.average_total - baseline.average_total, 2)
    entry = (
        f"\n### Cycle {cycle_number:03d} - {timestamp}\n"
        f"- Archetype: {archetype}\n"
        f"- Baseline average across 3 runs: {baseline.average_total}\n"
        f"- Weakest dimensions: {', '.join(weak_dimensions) if weak_dimensions else 'None below 7.0'}\n"
        f"- Exact change made: {exact_change}\n"
        f"- File changed: {changed_file.as_posix()}\n"
        f"- Test average across 3 runs: {b_test.average_total}\n"
        f"- Delta: {delta:+.2f}\n"
        f"- Verdict: {verdict}\n"
        f"- Notes: {notes}\n"
        f"- Next hypothesis: {next_hypothesis}\n"
    )
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(entry)


def commit_win(paths: list[Path], archetype: str, baseline_avg: float, test_avg: float) -> None:
    rel_paths = [str(path.relative_to(REPO_ROOT)) for path in paths]
    subprocess.run(["git", "add", *rel_paths], cwd=REPO_ROOT, check=True)
    msg = f"eval: tune {archetype} {baseline_avg:.1f} -> {test_avg:.1f}"
    subprocess.run(["git", "commit", "-m", msg], cwd=REPO_ROOT, check=True)


async def run_cycle(args: argparse.Namespace) -> dict[str, Any]:
    branch = verify_branch(args.expected_branch)
    load_env_from_backend()
    config = load_config(args.config)
    if args.archetypes:
        config["archetypes"] = args.archetypes
    tracked_archetypes = resolve_tracked_archetypes(config, args.archetypes)

    api = BuilderAPI(base_url=config.get("backend_url", "http://localhost:5000"))
    if not api.health_check():
        raise RuntimeError(f"Backend not reachable at {config.get('backend_url', 'http://localhost:5000')}")

    viewport = config.get("screenshot_viewport", [1440, 900])
    screenshotter = Screenshotter(viewport_width=viewport[0], viewport_height=viewport[1])
    client = get_genai_client()
    scorer_provider = create_scorer_provider(config, genai_client=client)
    scorer = DesignScorer(client, model=config.get("scorer_model", "gemini-2.5-flash"), provider=scorer_provider)
    refs = ReferenceLoader()
    stamp = cycle_timestamp()

    weakest = args.archetype
    if not weakest:
        weakest = await choose_weakest_archetype(
            tracked_archetypes=tracked_archetypes,
            refresh_if_missing=True,
            config=config,
            api=api,
            screenshotter=screenshotter,
            scorer=scorer,
            refs=refs,
            stamp=stamp,
        )

    baseline = await run_sample_builds(
        config=config,
        api=api,
        screenshotter=screenshotter,
        scorer=scorer,
        refs=refs,
        archetype=weakest,
        runs=args.baseline_runs,
        phase="baseline",
        stamp=stamp,
    )
    weak_dimensions = pick_weak_dimensions(baseline)
    edit_target, edit_path = choose_edit_target(weakest, weak_dimensions)
    log.info("Selected lever: %s", edit_target)

    if edit_target == "engineer":
        try:
            changed_path, original_text, _updated_text = edit_engineer_section(
                client=client,
                config=config,
                archetype=weakest,
                sample_set=baseline,
            )
            exact_change = (
                f"Rewrote the {weakest} archetype section in prompts/engineer.txt to target "
                f"{', '.join(weak_dimensions) if weak_dimensions else 'the weakest baseline dimension'}."
            )
        except ValueError as err:
            fallback_path = REPO_ROOT / "prompts" / "archetypes" / f"{weakest}.txt"
            log.warning(
                "Engineer section edit failed for %s (%s). Falling back to %s.",
                weakest,
                err,
                fallback_path.name,
            )
            changed_path, original_text, _updated_text = edit_kit_file(
                client=client,
                config=config,
                archetype=weakest,
                sample_set=baseline,
                target_path=fallback_path,
            )
            exact_change = (
                f"Engineer section was unavailable for {weakest}; updated {fallback_path.name} "
                f"with one targeted instruction cluster for "
                f"{', '.join(weak_dimensions) if weak_dimensions else 'the weakest baseline dimension'}."
            )
    else:
        if edit_path is None:
            raise RuntimeError("Expected an archetype kit path")
        changed_path, original_text, _updated_text = edit_kit_file(
            client=client,
            config=config,
            archetype=weakest,
            sample_set=baseline,
            target_path=edit_path,
        )
        exact_change = (
            f"Updated {edit_path.name} with one targeted instruction cluster for "
            f"{', '.join(weak_dimensions) if weak_dimensions else 'the weakest baseline dimension'}."
        )

    b_test = await run_sample_builds(
        config=config,
        api=api,
        screenshotter=screenshotter,
        scorer=scorer,
        refs=refs,
        archetype=weakest,
        runs=args.baseline_runs,
        phase="b_test",
        stamp=stamp,
    )

    delta = round(b_test.average_total - baseline.average_total, 2)
    accepted = delta > 1.0
    cycle_number = next_cycle_number()

    if not accepted:
        restore_file(changed_path, original_text)
        verdict = "reverted"
        notes = f"Branch {branch}. Change reverted because delta did not exceed +1.0."
        next_hypothesis = "Try the other editable surface for this archetype or target the next-lowest dimension."
    else:
        verdict = "committed" if args.commit_wins else "kept"
        notes = f"Branch {branch}. Improvement exceeded +1.0."
        next_hypothesis = "Move to the next weakest archetype."

    append_log_entry(
        cycle_number=cycle_number,
        archetype=weakest,
        baseline=baseline,
        weak_dimensions=weak_dimensions,
        exact_change=exact_change,
        changed_file=changed_path,
        b_test=b_test,
        verdict=verdict,
        notes=notes,
        next_hypothesis=next_hypothesis,
    )

    if accepted and args.commit_wins:
        commit_win([changed_path, LOG_PATH], weakest, baseline.average_total, b_test.average_total)

    result = {
        "branch": branch,
        "tracked_archetypes": tracked_archetypes,
        "archetype": weakest,
        "baseline_average": baseline.average_total,
        "b_test_average": b_test.average_total,
        "delta": delta,
        "accepted": accepted,
        "changed_file": str(changed_path.relative_to(REPO_ROOT)),
        "operator_results": str((OPERATOR_RESULTS_DIR / stamp).relative_to(REPO_ROOT)),
    }
    print(json.dumps(result, indent=2))
    return result


async def run_forever(args: argparse.Namespace) -> None:
    cycle_count = 0
    while args.max_cycles == 0 or cycle_count < args.max_cycles:
        cycle_count += 1
        log.info("Starting operator cycle %s", cycle_count)
        try:
            await run_cycle(args)
        except Exception:
            log.exception("Operator cycle %s failed", cycle_count)
            if args.stop_on_error:
                raise
        if args.max_cycles != 0 and cycle_count >= args.max_cycles:
            break
        await asyncio.sleep(args.sleep_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Operator-style eval loop")
    parser.add_argument("--config", default="eval_config.json")
    parser.add_argument("--archetypes", nargs="+", default=list(DEFAULT_TRACKED_ARCHETYPES))
    parser.add_argument("--archetype", help="Force a specific archetype for this cycle")
    parser.add_argument("--baseline-runs", type=int, default=3)
    parser.add_argument("--expected-branch", help="Fail if current branch does not match")
    parser.add_argument("--commit-wins", action="store_true", help="Commit accepted prompt/kit change plus log")
    parser.add_argument("--max-cycles", type=int, default=1, help="0 means run indefinitely")
    parser.add_argument("--sleep-seconds", type=int, default=30)
    parser.add_argument("--stop-on-error", action="store_true")
    args = parser.parse_args()

    asyncio.run(run_forever(args))


if __name__ == "__main__":
    main()
