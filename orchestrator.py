from __future__ import annotations

import os
from google import genai

from agents.pm_agent import PMAgent
from agents.planner_agent import PlannerAgent


class Orchestrator:
    def __init__(self):
        api_key = os.getenv("GENAI_API_KEY")

        if not api_key:
            raise RuntimeError("GENAI_API_KEY not found in environment variables.")

        # Create Gemini client
        self.client = genai.Client(api_key=api_key)

        # Initialize agents
        self.pm = PMAgent(self.client)
        self.planner = PlannerAgent(self.client)

    def run(self, user_input: str):
        prd_text = self.pm.run(user_input)
        plan = self.planner.run(prd_text)
        return prd_text, plan
