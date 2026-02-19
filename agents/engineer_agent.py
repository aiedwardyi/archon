from __future__ import annotations

import json
import os
import re
from pathlib import Path

from google import genai

from schemas.plan_schema import Task
from schemas.engineering_schema import EngineeringResult, FileArtifact
from utils.offline_engineer_scaffold import build_vite_react_ts_scaffold

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _is_offline_mode() -> bool:
    return os.getenv("OFFLINE_MODE", "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _build_offline_engineering_result(task_id: str) -> EngineeringResult:
    scaffold = build_vite_react_ts_scaffold(app_dir="apps/offline-vite-react")
    files = [
        FileArtifact(path=path, content=content)
        for path, content in sorted(scaffold.files.items())
    ]
    return EngineeringResult(
        task_id=task_id,
        summary="OFFLINE: Generated deterministic Vite + React + TypeScript scaffold in apps/offline-vite-react/",
        files=files,
    )


def _deduplicate_files(files: list[FileArtifact]) -> list[FileArtifact]:
    """
    Remove duplicate paths — keep the LAST occurrence (last-write wins).
    Gemini sometimes emits the same filename multiple times.
    We normalise paths to forward-slash before comparing.
    """
    seen: dict[str, FileArtifact] = {}
    for f in files:
        normalised = f.path.replace("\\", "/").strip("/")
        seen[normalised] = f
    return list(seen.values())


def _repair_json(raw: str) -> dict:
    """
    Attempt to repair and parse JSON that Gemini returned outside the
    structured-output path. Handles common Gemini failure modes:
      - Wrapped in ```json ... ``` fences
      - Stray backslash-whitespace sequences (e.g. \<newline> or \  before a key)
      - Multiple top-level objects concatenated
    """
    text = raw.strip()

    # Strip markdown fences
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # Find outermost JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(
            "EngineerAgent: no JSON object found in model output.\n\n"
            f"Raw output:\n{raw}"
        )

    candidate = text[start : end + 1]

    # Fix concatenated objects: }{ -> },{ 
    candidate = re.sub(r"}\s*\n\s*{", "},\n{", candidate)

    # Fix stray backslashes before whitespace or quotes that Gemini sometimes emits.
    # e.g.  "ISC",\  "dependencies"  ->  "ISC", "dependencies"
    # This removes backslashes that are NOT valid JSON escape sequences.
    # Valid JSON escapes: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
    candidate = re.sub(r'\\(?!["\\/bfnrtu])', "", candidate)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "EngineerAgent: JSON repair failed.\n\n"
            f"Parse error: {e}\n\n"
            f"Candidate JSON (first 2000 chars):\n{candidate[:2000]}"
        ) from e


class EngineerAgent:
    def __init__(self, client: genai.Client | None):
        self.client = client

    def run(self, task: Task) -> EngineeringResult:
        if task.execution_hint != "engineer":
            raise ValueError("EngineerAgent called with non-executable task")

        if task.task_type != "scaffold":
            raise ValueError(f"Unsupported task_type: {task.task_type}")

        if _is_offline_mode() or str(task.id).startswith("OFFLINE-"):
            return _build_offline_engineering_result(task_id=str(task.id))

        if self.client is None:
            raise RuntimeError("EngineerAgent: client is None in ONLINE mode")

        prompt = (PROMPTS_DIR / "engineer.txt").read_text(encoding="utf-8")

        contents = (
            f"{prompt}\n\n"
            f"--- TASK START ---\n"
            f"id: {task.id}\n"
            f"description: {task.description}\n"
            f"depends_on: {task.depends_on}\n"
            f"outputs: {task.outputs}\n"
            f"output_files: {task.output_files}\n"
            f"task_type: {task.task_type}\n"
            f"--- TASK END ---"
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config={
                "response_schema": EngineeringResult,
                "temperature": 0.2,
            },
        )

        # Primary path: structured output parsed cleanly
        if response.parsed is not None:
            result = response.parsed
            result.files = _deduplicate_files(result.files)
            return result

        # Fallback: attempt JSON repair on raw text
        raw = getattr(response, "text", "") or ""
        data = _repair_json(raw)
        result = EngineeringResult.model_validate(data)
        result.files = _deduplicate_files(result.files)
        return result
