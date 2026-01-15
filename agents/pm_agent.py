from __future__ import annotations

from google import genai


class PMAgent:
    """
    Week 1 stub.
    Replace with your real MVP #1 PRD generator in Week 1/Week 2,
    but keep the interface the same: run(user_input) -> prd_text (string).
    """

    def __init__(self, client: genai.Client):
        self.client = client

    def run(self, user_input: str) -> str:
        prompt = (
            "You are a product manager. Convert the user's idea into a concise PRD.\n"
            "Include: Goal, Users, Key features, Non-goals, Risks, Open questions.\n\n"
            f"User idea:\n{user_input}\n"
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"temperature": 0.2},
        )
        return response.text
