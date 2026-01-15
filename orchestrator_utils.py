from __future__ import annotations

from pathlib import Path
from typing import List

from schemas.plan_schema import Plan, Task
from schemas.engineering_schema import EngineeringResult


ALLOWED_PREFIXES = (
    "README.md",
    "LICENSE",
    ".gitignore",
    "package.json",
    "tsconfig.json",
    "webpack.config.js",
    "docs/",
    "src/",
    "public/",
    "requirements.txt",
    "pyproject.toml",
)

OUTPUT_SUFFIX_IF_EXISTS = ".generated"


def _is_allowed_path(rel_path: str) -> bool:
    norm = rel_path.replace("\\", "/")
    return any(
        norm == p.rstrip("/") or norm.startswith(p)
        for p in ALLOWED_PREFIXES
    )


def write_engineering_result(
    result: EngineeringResult,
    repo_root: Path,
    force: bool = False,
) -> List[str]:
    """
    Writes files to disk with allowlist + safety checks.
    Returns list of written file paths.
    """
    written: List[str] = []

    for f in result.files:
        rel = f.path.strip()
        if not rel:
            raise ValueError("Empty file path in engineering result")

        # Block absolute paths
        if Path(rel).is_absolute():
            raise ValueError(f"Absolute paths are not allowed: {rel}")

        # Block path traversal (../)
        norm = rel.replace("\\", "/")
        if ".." in norm.split("/"):
            raise ValueError(f"Path traversal is not allowed: {rel}")

        # Allowlist enforcement
        if not _is_allowed_path(rel):
            raise ValueError(f"Disallowed path from EngineerAgent: {rel}")

        dest = repo_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists() and not force:
            dest = repo_root / (rel + OUTPUT_SUFFIX_IF_EXISTS)

        dest.write_text(f.content, encoding="utf-8")
        written.append(str(dest))

    return written


def select_executable_task(plan: Plan) -> Task | None:
    """
    Returns the single engineer-executable task, or None.
    """
    executable: List[Task] = []

    for ms in plan.milestones:
        for t in ms.tasks:
            if getattr(t, "execution_hint", "defer") == "engineer":
                executable.append(t)

    if not executable:
        return None

    if len(executable) != 1:
        raise ValueError(
            f"Expected exactly 1 executable task, found {len(executable)}"
        )

    return executable[0]
