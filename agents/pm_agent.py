from __future__ import annotations
import os
import json as _json
from datetime import datetime, timezone
from openai import OpenAI
from schemas.prd_schema import PRD, PRDArtifact


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


SYSTEM_PROMPT = """You are an expert product manager.
Convert the client's raw requirements into a clean, professional Product Requirement Document (PRD).

Output must include these sections:
- document_title: Clear project name
- version: Use "0.1" for initial draft
- overview: High-level description (2-3 sentences)
- goals: Success criteria (3-5 bullet points)
- non_goals: Explicit exclusions (3-5 bullet points)
- target_users: User personas (2-3 types)
- core_features_mvp: Essential features for first release (5-10 items)
- nice_to_have_features: Optional enhancements (3-7 items)
- user_stories: User-centric requirements (minimum 8 stories)
- acceptance_criteria: Definition of done (5-10 criteria)
- technical_stack_recommendation: Suggested technologies (5-8 items)
- payments_security_compliance: Regulatory considerations (2-5 items)
- assumptions: Development constraints (3-5 items)
- open_questions: Client clarifications needed (5-10 questions)

Be thorough, professional, and specific. Do NOT generate app content (e.g., meal plans). Only write requirements.

For regenerate_images: set False when the request is about layout, text, spacing, functionality, or code only, or when the user says not to generate images. Set True when new visuals, new image sections, or a different visual theme are requested, or for first builds. Default to False on iterations unless visual changes are clearly needed.
"""

CLASSIFY_SYSTEM = (
    "You are Archon, an AI app-building assistant. Classify the user message as BUILD or CHAT.\n\n"
    "CHAT â€” reply with advice for ANY of these:\n"
    "- Any question (what, how, which, should, can, is, why, where, do you think, would you, could you help)\n"
    "- Asks for opinion, recommendation, or feedback\n"
    "- Greetings or general conversation\n"
    "- Hypothetical or exploratory (what if, would it be better, do you think X would...)\n\n"
    "BUILD â€” ONLY if the message is a direct imperative instruction with no question mark:\n"
    "- Starts with or is clearly a command: build, create, make, add, fix, update, redesign\n"
    "- Example BUILD: 'add a login page', 'build me a dashboard', 'fix the navbar'\n"
    "- Example CHAT: 'do you think adding a chatbox would help?', 'should I add dark mode?', 'would a sidebar be better?'\n\n"
    "KEY RULE: If the message contains a question mark OR asks for your opinion, it is ALWAYS CHAT.\n"
    "KEY RULE: Imperative commands with no question mark = BUILD.\n\n"
    "Reply ONLY with valid JSON. No markdown. No explanation. No code fences.\n"
    "CHAT: {\"type\": \"chat\", \"message\": \"<2-4 sentence reply as product consultant>\"}\n"
    "BUILD: {\"type\": \"build\"}\n\n"
    "IMPORTANT: When in doubt, default to CHAT. Only BUILD when you are 100% certain it is a direct imperative command."
)


class PMAgent:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.client = OpenAI(api_key=self.api_key)

    def classify_intent(self, user_message: str, project_context: str = None) -> dict:
        """
        Decides if the user wants to build something or just have a conversation.
        Returns {"type": "build"} or {"type": "chat", "message": "..."}
        """
        system = CLASSIFY_SYSTEM
        if project_context:
            system += f"\n\nCURRENT PROJECT CONTEXT (use this to give specific advice):\n{project_context}"
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()

        print(f"[CLASSIFY] Input: {user_message[:80]!r}", flush=True)
        print(f"[CLASSIFY] Raw response: {raw}", flush=True)

        try:
            return _json.loads(raw)
        except Exception:
            print("[CLASSIFY] JSON parse failed, defaulting to chat", flush=True)
            return {
                "type": "chat",
                "message": "I'm not sure I understood that â€” could you rephrase?"
            }

    def generate_prd(self, user_requirements: str) -> PRDArtifact:
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Client requirements:\n\n{user_requirements}"}
            ],
            response_format=PRD,
            temperature=0.2,
        )
        prd = response.choices[0].message.parsed
        return PRDArtifact(
            prd=prd,
            created_at=_utc_now_iso(),
        )




