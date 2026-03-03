"""
Generate markdown summary reports for eval runs.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_iteration_report(
    iteration: int,
    scores_by_archetype: dict[str, dict],
    prev_scores_by_archetype: dict[str, dict] = None,
    output_dir: Path = None,
) -> str:
    """Generate a markdown report for a single iteration.

    Args:
        iteration: Iteration number (0-based).
        scores_by_archetype: {archetype: ScoringResult.to_dict()} for this iteration.
        prev_scores_by_archetype: Same dict for previous iteration (for deltas).
        output_dir: Where to save the report markdown.

    Returns:
        The markdown report string.
    """
    lines = [
        f"# Eval Report — Iteration {iteration}",
        f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
    ]

    for archetype, scores in scores_by_archetype.items():
        weighted = scores.get("weighted_total", 0)
        prev_weighted = 0
        if prev_scores_by_archetype and archetype in prev_scores_by_archetype:
            prev_weighted = prev_scores_by_archetype[archetype].get("weighted_total", 0)

        delta = weighted - prev_weighted
        delta_str = f" ({'+' if delta >= 0 else ''}{delta:.1f})" if prev_weighted > 0 else ""

        lines.append(f"## {archetype.replace('_', ' ').title()}")
        lines.append(f"- **Weighted Score**: {weighted:.1f}/100{delta_str}")

        # Per-dimension scores
        dim_scores = scores.get("scores", {})
        if dim_scores:
            lines.append("- **Dimension Scores**:")
            for dim_name, dim_score in dim_scores.items():
                label = dim_name.replace("_", " ").title()
                lines.append(f"  - {label}: {dim_score}/10")

        # Strengths
        strengths = scores.get("strengths", [])
        if strengths:
            lines.append(f"- **Strengths**: {'; '.join(strengths[:3])}")

        # Issues
        issues = scores.get("issues", [])
        if issues:
            lines.append(f"- **Issues**: {'; '.join(issues[:3])}")

        # Improvements applied
        improvements = scores.get("specific_improvements", [])
        if improvements:
            lines.append("- **Suggested Improvements**:")
            for imp in improvements[:5]:
                lines.append(f"  - {imp}")

        lines.append("")

    report = "\n".join(lines)

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"report_iter_{iteration}.md"
        report_path.write_text(report, encoding="utf-8")
        logger.info(f"Iteration report saved: {report_path}")

    return report


def generate_final_report(
    all_iterations: list[dict[str, dict]],
    output_dir: Path = None,
) -> str:
    """Generate a final summary report across all iterations.

    Args:
        all_iterations: List of {archetype: ScoringResult.to_dict()} per iteration.
        output_dir: Where to save the report.

    Returns:
        The markdown report string.
    """
    lines = [
        "# Eval Final Report",
        f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        f"*Total iterations: {len(all_iterations)}*\n",
    ]

    if not all_iterations:
        lines.append("No iterations completed.")
        return "\n".join(lines)

    # Collect all archetypes
    all_archetypes = set()
    for iteration_scores in all_iterations:
        all_archetypes.update(iteration_scores.keys())

    for archetype in sorted(all_archetypes):
        lines.append(f"## {archetype.replace('_', ' ').title()}")

        # Score progression
        progression = []
        for i, iteration_scores in enumerate(all_iterations):
            if archetype in iteration_scores:
                score = iteration_scores[archetype].get("weighted_total", 0)
                progression.append((i, score))

        if progression:
            first_score = progression[0][1]
            last_score = progression[-1][1]
            total_delta = last_score - first_score
            lines.append(
                f"- **Score progression**: {first_score:.1f} → {last_score:.1f} "
                f"({'+' if total_delta >= 0 else ''}{total_delta:.1f})"
            )
            lines.append(f"- **Iterations**: {' → '.join(f'{s:.0f}' for _, s in progression)}")

            # Best dimension and worst dimension in final iteration
            final_scores = all_iterations[-1].get(archetype, {}).get("scores", {})
            if final_scores:
                best_dim = max(final_scores, key=final_scores.get)
                worst_dim = min(final_scores, key=final_scores.get)
                lines.append(
                    f"- **Strongest**: {best_dim.replace('_', ' ').title()} ({final_scores[best_dim]}/10)"
                )
                lines.append(
                    f"- **Weakest**: {worst_dim.replace('_', ' ').title()} ({final_scores[worst_dim]}/10)"
                )

            # Final issues
            final_issues = all_iterations[-1].get(archetype, {}).get("issues", [])
            if final_issues:
                lines.append(f"- **Remaining issues**: {'; '.join(final_issues[:3])}")

        passed = last_score >= 80 if progression else False
        status = "PASSED" if passed else "NEEDS WORK"
        lines.append(f"- **Status**: {status}")
        lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("| Archetype | Start | End | Delta | Status |")
    lines.append("|-----------|-------|-----|-------|--------|")
    for archetype in sorted(all_archetypes):
        progression = []
        for i, iteration_scores in enumerate(all_iterations):
            if archetype in iteration_scores:
                score = iteration_scores[archetype].get("weighted_total", 0)
                progression.append(score)
        if progression:
            start = progression[0]
            end = progression[-1]
            delta = end - start
            status = "Pass" if end >= 80 else "Fail"
            name = archetype.replace("_", " ").title()
            lines.append(
                f"| {name} | {start:.1f} | {end:.1f} | "
                f"{'+' if delta >= 0 else ''}{delta:.1f} | {status} |"
            )
    lines.append("")

    report = "\n".join(lines)

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "report_final.md"
        report_path.write_text(report, encoding="utf-8")
        logger.info(f"Final report saved: {report_path}")

    return report
