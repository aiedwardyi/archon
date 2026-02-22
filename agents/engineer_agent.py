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
    seen: dict[str, FileArtifact] = {}
    for f in files:
        normalised = f.path.replace("\\", "/").strip("/")
        seen[normalised] = f
    return list(seen.values())


def _repair_json(raw: str) -> dict:
    text = raw.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(
            "EngineerAgent: no JSON object found in model output.\n\n"
            f"Raw output:\n{raw}"
        )
    candidate = text[start : end + 1]
    candidate = re.sub(r"}\s*\n\s*{", "},\n{", candidate)
    # Pass 1: strip invalid escapes
    try:
        return json.loads(re.sub(r'\\(?!["\\/bfnrtu])', "", candidate))
    except json.JSONDecodeError:
        pass
    # Pass 2: double them instead
    try:
        return json.loads(re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", candidate))
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "EngineerAgent: JSON repair failed.\n\n"
            f"Parse error: {e}\n\n"
            f"Candidate JSON (first 2000 chars):\n{candidate[:2000]}"
        ) from e


def _run_claude(contents: str) -> EngineeringResult:
    """Call Claude Sonnet as the build agent."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=32000,
        messages=[{"role": "user", "content": contents}],
    )
    raw = message.content[0].text
    data = _repair_json(raw)
    result = EngineeringResult.model_validate(data)
    result.files = _deduplicate_files(result.files)
    return result


def _run_gemini(client: genai.Client, contents: str) -> EngineeringResult:
    """Call Gemini Flash as the build agent (fallback)."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config={
            "response_schema": EngineeringResult,
            "temperature": 0.7,
            "max_output_tokens": 65536,
        },
    )
    if response.parsed is not None:
        result = response.parsed
        result.files = _deduplicate_files(result.files)
        return result
    raw = getattr(response, "text", "") or ""
    data = _repair_json(raw)
    result = EngineeringResult.model_validate(data)
    result.files = _deduplicate_files(result.files)
    return result


class EngineerAgent:
    def __init__(self, client: genai.Client | None):
        self.client = client

    def run(self, task: Task, user_prompt: str = None, existing_code: str = None) -> EngineeringResult:
        if task.execution_hint != "engineer":
            raise ValueError("EngineerAgent called with non-executable task")

        if task.task_type != "scaffold":
            raise ValueError(f"Unsupported task_type: {task.task_type}")

        if _is_offline_mode() or str(task.id).startswith("OFFLINE-"):
            return _build_offline_engineering_result(task_id=str(task.id))

        prompt = (PROMPTS_DIR / "engineer.txt").read_text(encoding="utf-8")

        user_context = ""
        if user_prompt:
            user_context = (
                f"--- USER REQUEST (what to build) ---\n"
                f"{user_prompt}\n"
                f"--- END USER REQUEST ---\n\n"
            )

        iteration_context = ""
        if existing_code:
            iteration_context = (
                f"--- EXISTING CODE (iterate on this, do not rebuild from scratch) ---\n"
                f"{existing_code}\n"
                f"--- END EXISTING CODE ---\n\n"
            )

        contents = (
            f"{prompt}\n\n"
            f"{user_context}"
            f"{iteration_context}"
            f"--- TASK START ---\n"
            f"id: {task.id}\n"
            f"description: {task.description}\n"
            f"depends_on: {task.depends_on}\n"
            f"outputs: {task.outputs}\n"
            f"output_files: {task.output_files}\n"
            f"task_type: {task.task_type}\n"
            f"--- TASK END ---"
        )

        if os.environ.get("ANTHROPIC_API_KEY"):
            return _run_claude(contents)

        if self.client is None:
            raise RuntimeError("EngineerAgent: no API client available")

        return _run_gemini(self.client, contents)
