from __future__ import annotations
import json as _json
import re
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
- detected_intent: One sentence describing the true product intent
- archetype_hint: Best-fit product archetype (dashboard, ecommerce, portfolio, editor, game, fintech, etc.)
- primary_user_action: The main thing users do in this product
- visual_direction: A specific visual direction for this build (materials, palette bias, typography personality, mood)
- tone_keywords: 3-5 concise style words
- prompt_quality_score: integer 0-100 for request specificity and ambition
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
Infer missing product identity details when the user is vague, but keep them plausible.
The visual_direction should be concrete enough that a planner can derive a strong UI quality target from it.

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


_BUILD_VERBS = (
    "build",
    "create",
    "make",
    "add",
    "fix",
    "update",
    "redesign",
    "generate",
    "convert",
    "turn",
    "polish",
    "improve",
)
_BUILD_OBJECT_HINTS = (
    "app",
    "site",
    "website",
    "webpage",
    "landing page",
    "fanpage",
    "page",
    "dashboard",
    "portal",
    "workspace",
    "admin",
    "hero",
    "navbar",
    "section",
    "form",
    "checkout",
    "map",
    "gallery",
)
_QUESTION_OR_OPINION_PATTERNS = (
    "do you think",
    "what do you think",
    "would it be better",
    "should i",
    "should we",
    "can you help me decide",
    "which is better",
    "recommend",
)
_GREETING_PREFIXES = (
    "hi",
    "hello",
    "hey",
    "yo",
    "thanks",
    "thank you",
)
_BUILD_VERB_PATTERN = "|".join(_BUILD_VERBS)
_LEADING_FILLER_RE = re.compile(r"^(?:(?:ok|okay|alright|well|so|just)\s+)+", re.IGNORECASE)
_BUILD_COMMAND_RE = re.compile(
    rf"^(?:please\s+)?(?:{_BUILD_VERB_PATTERN})\b",
    re.IGNORECASE,
)
_BUILD_REQUEST_RE = re.compile(
    r"^(?:please\s+)?(?:can you|could you|would you|i want you to|i need you to|help me)\s+"
    rf"(?:{_BUILD_VERB_PATTERN})\b",
    re.IGNORECASE,
)
_QUESTION_LEAD_RE = re.compile(
    r"^(?:what|how|why|where|when|which|who|should|can|could|would|is|are|do|does|did)\b",
    re.IGNORECASE,
)


def _default_chat_message(project_context: str | None = None) -> str:
    if project_context:
        return "Tell me exactly what you want changed in this project, and I’ll turn it into a concrete build step."
    return "Tell me exactly what you want built or changed, and I’ll turn it into a concrete build request."


def _normalize_message(user_message: str) -> str:
    normalized = " ".join((user_message or "").strip().split())
    return _LEADING_FILLER_RE.sub("", normalized).strip().lower()


def _looks_like_build_command(normalized: str) -> bool:
    if not normalized:
        return False
    if _BUILD_COMMAND_RE.match(normalized) or _BUILD_REQUEST_RE.match(normalized):
        return True
    return any(verb in normalized for verb in ("build me", "create me", "make me")) and any(
        hint in normalized for hint in _BUILD_OBJECT_HINTS
    )


def fallback_classify_intent(user_message: str, project_context: str | None = None) -> dict:
    normalized = _normalize_message(user_message)
    if not normalized:
        return {"type": "chat", "message": _default_chat_message(project_context)}

    if "?" in (user_message or ""):
        return {"type": "chat", "message": _default_chat_message(project_context)}

    if _looks_like_build_command(normalized):
        return {"type": "build"}

    if any(pattern in normalized for pattern in _QUESTION_OR_OPINION_PATTERNS):
        return {"type": "chat", "message": _default_chat_message(project_context)}

    if _QUESTION_LEAD_RE.match(normalized):
        return {"type": "chat", "message": _default_chat_message(project_context)}

    if any(normalized == prefix or normalized.startswith(f"{prefix} ") for prefix in _GREETING_PREFIXES):
        return {"type": "chat", "message": _default_chat_message(project_context)}

    return {"type": "chat", "message": _default_chat_message(project_context)}


def _normalize_classify_result(result: dict, user_message: str, project_context: str | None = None) -> dict:
    if not isinstance(result, dict):
        return fallback_classify_intent(user_message, project_context=project_context)

    result_type = str(result.get("type", "")).strip().lower()
    if result_type == "build":
        return {"type": "build"}
    if result_type == "chat":
        return {
            "type": "chat",
            "message": str(result.get("message") or _default_chat_message(project_context)),
        }
    return fallback_classify_intent(user_message, project_context=project_context)


class PMAgent:
    def __init__(self, client: genai.Client | None = None, api_key: str | None = None):
        self._client_init_error: Exception | None = None
        if client is not None:
            self.client = client
        else:
            # Auto-create client from env vars
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from utils.genai_client import get_genai_client
            try:
                self.client = get_genai_client()
            except Exception as exc:
                self.client = None
                self._client_init_error = exc

    def classify_intent(self, user_message: str, project_context: str = None) -> dict:
        """
        Decides if the user wants to build something or just have a conversation.
        Returns {"type": "build"} or {"type": "chat", "message": "..."}
        """
        if self.client is None:
            print(f"[CLASSIFY] Client unavailable, using heuristic fallback: {self._client_init_error}", flush=True)
            return fallback_classify_intent(user_message, project_context=project_context)

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

        try:
            response = call_with_retry(_call, max_retries=2)
        except Exception as exc:
            print(f"[CLASSIFY] Model call failed, using heuristic fallback: {exc}", flush=True)
            return fallback_classify_intent(user_message, project_context=project_context)

        print(f"[CLASSIFY] Input: {user_message[:80]!r}", flush=True)

        if response.parsed is not None:
            result = _normalize_classify_result(
                response.parsed.model_dump(),
                user_message,
                project_context=project_context,
            )
            print(f"[CLASSIFY] Result: {result}", flush=True)
            return result

        # Fallback: try parsing raw text
        raw = response.text.strip() if response.text else ""
        print(f"[CLASSIFY] Raw response: {raw}", flush=True)
        try:
            result = _normalize_classify_result(
                _json.loads(raw),
                user_message,
                project_context=project_context,
            )
            print(f"[CLASSIFY] Parsed raw result: {result}", flush=True)
            return result
        except Exception:
            print("[CLASSIFY] JSON parse failed, using heuristic fallback", flush=True)
            return fallback_classify_intent(user_message, project_context=project_context)

    def generate_prd(self, user_requirements: str) -> PRDArtifact:
        if self.client is None:
            raise RuntimeError(
                "PM Agent client is unavailable. Set VERTEX_AI_PROJECT or GENAI_API_KEY."
            ) from self._client_init_error
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
