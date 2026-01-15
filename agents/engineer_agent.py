from __future__ import annotations

import json
from pathlib import Path

from schemas.plan_schema import Task
from schemas.engineering_schema import EngineeringResult


class EngineerAgent:
    """
    Executes a single planner Task into concrete file artifacts (scaffold only for now).
    """

    def __init__(self, client, prompt_path: str = "prompts/engineer.txt", model: str = "gemini-2.5-flash"):
        self.client = client
        self.model = model
        self.system_prompt = Path(prompt_path).read_text(encoding="utf-8")

    def run(self, task: Task) -> EngineeringResult:
        # --- Safety gates (WHY: keep execution deterministic and prevent misuse) ---
        if task.execution_hint != "engineer":
            raise ValueError("EngineerAgent.run called with a task that is not marked execution_hint='engineer'")

        if task.task_type != "scaffold":
            raise ValueError(f"EngineerAgent currently supports only task_type='scaffold' (got {task.task_type})")

        # Provide the task in a stable JSON form (WHY: models follow structure better than prose)
        task_payload = {
            "id": task.id,
            "description": task.description,
            "depends_on": task.depends_on,
            "outputs": task.outputs,
            "output_files": task.output_files,
            "task_type": task.task_type,
        }

        user_prompt = (
            "Generate scaffolding file artifacts for this task.\n"
            "TASK JSON:\n"
            f"{json.dumps(task_payload, ensure_ascii=False, indent=2)}"
        )

        # --- Model call ---
        # This is deliberately simple and mirrors typical google.genai usage.
        # If your PlannerAgent uses a slightly different call signature, we can match it exactly later.
        resp = self.client.models.generate_content(
            model=self.model,
            contents=[
                {"role": "system", "parts": [{"text": self.system_prompt}]},
                {"role": "user", "parts": [{"text": user_prompt}]},
            ],
        )

        text = getattr(resp, "text", None)
        if not text:
            # Some SDK versions store output differently; this makes failure visible.
            raise RuntimeError("EngineerAgent received empty response text from model")

        # --- Parse JSON strictly (WHY: never trust model formatting blindly) ---
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"EngineerAgent output was not valid JSON: {e}\nRaw output:\n{text}") from e

        # --- Validate schema (WHY: enforce contract and prevent extra keys/prose) ---
        return EngineeringResult.model_validate(data)
