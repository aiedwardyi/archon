from __future__ import annotations

from pathlib import Path
from google import genai

from schemas.plan_schema import Task
from schemas.engineering_schema import EngineeringResult


class EngineerAgent:
    def __init__(self, client: genai.Client):
        self.client = client

    def run(self, task: Task) -> EngineeringResult:
        # Safety gates (WHY: prevent accidental or unsupported execution)
        if task.execution_hint != "engineer":
            raise ValueError("EngineerAgent.run called with a task not marked execution_hint='engineer'.")

        if task.task_type != "scaffold":
            raise ValueError(f"EngineerAgent currently supports only task_type='scaffold' (got {task.task_type}).")

        prompt = Path("prompts/engineer.txt").read_text(encoding="utf-8")

        # We include the task in a structured way (WHY: reduces model ambiguity)
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

        if response.parsed is None:
            raw = getattr(response, "text", None)
            raise RuntimeError(
                "EngineerAgent: schema parse failed (response.parsed is None).\n\n"
                f"Raw model output:\n{raw}"
            )

        return response.parsed
