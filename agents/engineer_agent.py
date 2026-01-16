from __future__ import annotations

import json
import os
import re
from pathlib import Path

from google import genai

from schemas.plan_schema import Task
from schemas.engineering_schema import EngineeringResult, FileArtifact
from utils.offline_engineer_scaffold import build_vite_react_ts_scaffold


def _is_offline_mode() -> bool:
    """
    OFFLINE_MODE triggers deterministic behavior with zero model calls.
    Accepts: 1, true, yes, y, on (case-insensitive)
    """
    return os.getenv("OFFLINE_MODE", "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _build_offline_engineering_result(task_id: str) -> EngineeringResult:
    """
    Convert deterministic offline scaffold into EngineeringResult.
    """
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


class EngineerAgent:
    def __init__(self, client: genai.Client | None):
        self.client = client

    def run(self, task: Task) -> EngineeringResult:
        # Safety gates
        if task.execution_hint != "engineer":
            raise ValueError("EngineerAgent called with non-executable task")

        if task.task_type != "scaffold":
            raise ValueError(f"Unsupported task_type: {task.task_type}")

        # OFFLINE branch
        if _is_offline_mode() or str(task.id).startswith("OFFLINE-"):
            return _build_offline_engineering_result(task_id=str(task.id))

        if self.client is None:
            raise RuntimeError("EngineerAgent: client is None in ONLINE mode")

        # ONLINE branch
        prompt = Path("prompts/engineer.txt").read_text(encoding="utf-8")

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

        # Primary path
        if response.parsed is not None:
            return response.parsed

        # -------- FALLBACK REPAIR PATH --------

        raw = getattr(response, "text", "") or ""
        text = raw.strip()

        # Strip markdown fences
        text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        # Extract JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise RuntimeError(
                "EngineerAgent: no JSON object found in model output.\n\n"
                f"Raw output:\n{raw}"
            )

        candidate = text[start : end + 1]

        # Fix missing commas between objects
        candidate = re.sub(r"}\s*\n\s*{", "},\n{", candidate)

        try:
            data = json.loads(candidate)
        except Exception as e:
            raise RuntimeError(
                "EngineerAgent: JSON repair failed.\n\n"
                f"Raw output:\n{raw}\n\n"
                f"Candidate JSON:\n{candidate}"
            ) from e

        return EngineeringResult.model_validate(data)
