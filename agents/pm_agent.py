from __future__ import annotations
import json as _json
from datetime import datetime, timezone
from google import genai
from schemas.prd_schema import PRD, PRDArtifact
from utils.genai_retry import call_with_retry


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
    "CHAT \u2014 reply with advice for ANY of these:\n"
    "- Any question (what, how, which, should, can, is, why, where, do you think, would you, could you help)\n"
    "- Asks for opinion, recommendation, or feedback\n"
    "- Greetings or general conversation\n"
    "- Hypothetical or exploratory (what if, would it be better, do you think X would...)\n\n"
    "BUILD \u2014 ONLY if the message is a direct imperative instruction with no question mark:\n"
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

# Pydantic model for classify_intent structured output
from pydantic import BaseModel, Field
from typing import Optional

class ClassifyResult(BaseModel):
    type: str = Field(..., description="Either 'build' or 'chat'")
    message: Optional[str] = Field(None, description="Chat response message (only for chat type)")


class PMAgent:
    def __init__(self, client: genai.Client | None = None, api_key: str | None = None):
        if client is not None:
            self.client = client
        else:
            # Auto-create client from env vars
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from utils.genai_client import get_genai_client
            self.client = get_genai_client()

    def classify_intent(self, user_message: str, project_context: str = None) -> dict:
        """
        Decides if the user wants to build something or just have a conversation.
        Returns {"type": "build"} or {"type": "chat", "message": "..."}
        """
        system = CLASSIFY_SYSTEM
        if project_context:
            system += f"\n\nCURRENT PROJECT CONTEXT (use this to give specific advice):\n{project_context}"

        contents = f"{system}\n\nUser message: {user_message}"

        def _call():
            return self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ClassifyResult,
                    "temperature": 0.1,
                    "max_output_tokens": 300,
                },
            )

        response = call_with_retry(_call, max_retries=2)

        print(f"[CLASSIFY] Input: {user_message[:80]!r}", flush=True)

        if response.parsed is not None:
            result = response.parsed.model_dump()
            # Remove None message for build type
            if result.get("message") is None:
                result.pop("message", None)
            print(f"[CLASSIFY] Result: {result}", flush=True)
            return result

        # Fallback: try parsing raw text
        raw = response.text.strip() if response.text else ""
        print(f"[CLASSIFY] Raw response: {raw}", flush=True)
        try:
            return _json.loads(raw)
        except Exception:
            print("[CLASSIFY] JSON parse failed, defaulting to chat", flush=True)
            return {
                "type": "chat",
                "message": "I'm not sure I understood that \u2014 could you rephrase?"
            }

    def generate_prd(self, user_requirements: str) -> PRDArtifact:
        contents = f"{SYSTEM_PROMPT}\n\nClient requirements:\n\n{user_requirements}"

        def _call():
            return self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": PRD,
                    "temperature": 0.2,
                },
            )

        for parse_attempt in range(3):
            response = call_with_retry(_call, max_retries=2)
            if response.parsed is not None:
                prd = response.parsed
                return PRDArtifact(
                    prd=prd,
                    created_at=_utc_now_iso(),
                )
            if parse_attempt < 2:
                print(f"PMAgent: schema parse failed, retrying (attempt {parse_attempt + 1}/3)...")
                import time; time.sleep(1)

        raise RuntimeError("PM Agent could not produce a valid PRD after 3 attempts. Please try rephrasing your request.")
