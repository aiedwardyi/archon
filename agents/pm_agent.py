from __future__ import annotations
import os
import re
import json as _json
from datetime import datetime, timezone
from utils.genai_client import get_genai_client
from schemas.prd_schema import PRD, PRDArtifact


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return _json.loads(text[start:end + 1])
    return _json.loads(text)


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
    "CHAT -- reply with advice for ANY of these:\n"
    "- Any question (what, how, which, should, can, is, why, where, do you think, would you, could you help)\n"
    "- Asks for opinion, recommendation, or feedback\n"
    "- Greetings or general conversation\n"
    "- Hypothetical or exploratory (what if, would it be better, do you think X would...)\n\n"
    "BUILD -- ONLY if the message is a direct imperative instruction with no question mark:\n"
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
        self.client = get_genai_client()

    def classify_intent(self, user_message: str, project_context: str = None) -> dict:
        """
        Decides if the user wants to build something or just have a conversation.
        Returns {"type": "build"} or {"type": "chat", "message": "..."}
        """
        system = CLASSIFY_SYSTEM
        if project_context:
            system += f"\n\nCURRENT PROJECT CONTEXT (use this to give specific advice):\n{project_context}"
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config={
                "system_instruction": system,
                "response_mime_type": "application/json",
                "temperature": 0.1,
                "max_output_tokens": 300,
            },
        )
        raw = (getattr(response, "text", "") or "").strip()

        print(f"[CLASSIFY] Input: {user_message[:80]!r}", flush=True)
        print(f"[CLASSIFY] Raw response: {raw}", flush=True)

        try:
            return _parse_json(raw)
        except Exception:
            print("[CLASSIFY] JSON parse failed, defaulting to chat", flush=True)
            return {
                "type": "chat",
                "message": "I'm not sure I understood that - could you rephrase?"
            }

    def generate_prd(self, user_requirements: str) -> PRDArtifact:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Client requirements:\n\n{user_requirements}",
            config={
                "system_instruction": SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "response_schema": PRD,
                "temperature": 0.2,
                "max_output_tokens": 4000,
            },
        )
        if response.parsed is not None:
            prd = response.parsed
        else:
            raw = (getattr(response, "text", "") or "").strip()
            data = _parse_json(raw)
            prd = PRD.model_validate(data)
        return PRDArtifact(
            prd=prd,
            created_at=_utc_now_iso(),
        )




