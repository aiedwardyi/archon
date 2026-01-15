from __future__ import annotations

from pathlib import Path
from google import genai

from schemas.plan_schema import Plan
from utils.genai_retry import call_with_retry


class PlannerAgent:
    def __init__(self, client: genai.Client):
        self.client = client

    def run(self, prd_text: str) -> Plan:
        prompt = Path("prompts/planner.txt").read_text(encoding="utf-8")
        contents = f"{prompt}\n\n--- PRD START ---\n{prd_text}\n--- PRD END ---"

        def _call():
            return self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config={
                    "response_schema": Plan,
                    "temperature": 0.2,
                },
            )

        response = call_with_retry(_call, max_retries=2)

        if response.parsed is None:
            raw = getattr(response, "text", None)
            raise RuntimeError(
                "PlannerAgent: schema parse failed (response.parsed is None).\n\n"
                f"Raw model output:\n{raw}"
            )

        return response.parsed
