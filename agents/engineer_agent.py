from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

try:
    from json_repair import repair_json
    _JSON_REPAIR_AVAILABLE = True
except ImportError:
    _JSON_REPAIR_AVAILABLE = False

from google import genai
from pydantic import ValidationError

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


def _fix_backslashes_in_strings(candidate: str) -> str:
    """Walk the JSON char-by-char; inside string values, replace invalid
    \\X escapes with \\\\X (literal backslash + char) so json.loads succeeds."""
    _VALID_ESCAPES = set('"\\\/bfnrtu')
    out: list[str] = []
    in_string = False
    i = 0
    n = len(candidate)
    while i < n:
        ch = candidate[i]
        if not in_string:
            out.append(ch)
            if ch == '"':
                in_string = True
            i += 1
            continue
        # inside a JSON string
        if ch == '"':
            out.append(ch)
            in_string = False
            i += 1
            continue
        if ch == '\\' and i + 1 < n:
            nxt = candidate[i + 1]
            if nxt in _VALID_ESCAPES:
                out.append(ch)
                out.append(nxt)
                i += 2
            else:
                # invalid escape like \e \s \p \x \0 — double the backslash
                out.append('\\\\')
                out.append(nxt)
                i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


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
    candidate = re.sub(r"`(#[0-9a-fA-F]{3,8})`", r"\1", candidate)

    # Pass 1: direct parse
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Pass 2: regex strip invalid backslash escapes
    try:
        return json.loads(re.sub(r'\\(?!["\\/bfnrtu])', "", candidate))
    except json.JSONDecodeError:
        pass

    # Pass 3: char-walking backslash fixer (context-aware, only inside strings)
    try:
        return json.loads(_fix_backslashes_in_strings(candidate))
    except json.JSONDecodeError:
        pass

    # Pass 4: json_repair library
    if _JSON_REPAIR_AVAILABLE:
        try:
            repaired = repair_json(candidate, return_objects=True)
            if isinstance(repaired, dict):
                return repaired
        except Exception:
            pass

    # Pass 5: aggressive backslash doubling then retry
    try:
        aggressive = candidate.replace('\\', '\\\\')
        for seq in ['\\"', '\\\\', '\\/', '\\b', '\\f', '\\n', '\\r', '\\t']:
            aggressive = aggressive.replace('\\\\' + seq[1], seq)
        return json.loads(aggressive)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "EngineerAgent: JSON repair failed.\n\n"
            f"Parse error: {e}\n\n"
            f"Candidate JSON (first 2000 chars):\n{candidate[:2000]}"
        ) from e


_ENGINEER_MAX_RETRIES = 5


def _run_claude(contents: str) -> EngineeringResult:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    last_err = None
    for attempt in range(_ENGINEER_MAX_RETRIES):
        if attempt > 0:
            wait = min(4 * (2 ** (attempt - 1)), 30)  # 4s, 8s, 16s, 30s
            print(f"EngineerAgent (Claude): retry {attempt}/{_ENGINEER_MAX_RETRIES} in {wait}s...")
            time.sleep(wait)
        try:
            raw = ""
            usage = None
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=64000,
                messages=[{"role": "user", "content": contents}],
            ) as stream:
                for text in stream.text_stream:
                    raw += text
                final_message = stream.get_final_message()
                usage = final_message.usage if final_message else None
            data = _repair_json(raw)
            result = EngineeringResult.model_validate(data)
            result.files = _deduplicate_files(result.files)
            if usage:
                result.usage = usage
            return result
        except anthropic.APIStatusError as e:
            last_err = e
            if e.status_code in (429, 529, 503):
                print(f"EngineerAgent (Claude): got {e.status_code}, will retry...")
                continue
            raise
        except anthropic.APIConnectionError as e:
            last_err = e
            print(f"EngineerAgent (Claude): connection error, will retry...")
            continue
        except Exception as e:
            # Safety net: catch overloaded errors that may not be APIStatusError
            # (e.g. during streaming, the SDK may wrap differently)
            if "overloaded" in str(e).lower() or "529" in str(e):
                last_err = e
                print(f"EngineerAgent (Claude): overloaded (caught as {type(e).__name__}), will retry...")
                continue
            raise
    raise last_err


def _validate_parsed_result(parsed: object) -> EngineeringResult:
    """Validate that response.parsed has proper FileArtifacts (not raw strings/ints)."""
    if not isinstance(parsed, EngineeringResult):
        raise ValueError(f"Expected EngineeringResult, got {type(parsed)}")
    for i, f in enumerate(parsed.files):
        if not isinstance(f, FileArtifact) or not isinstance(f.path, str) or not isinstance(f.content, str):
            raise ValueError(f"files[{i}] is not a valid FileArtifact: {type(f)}")
    return parsed


def _run_gemini(client: genai.Client, contents: str) -> EngineeringResult:
    last_err = None
    for attempt in range(_ENGINEER_MAX_RETRIES):
        if attempt > 0:
            # Fresh client on retry (picks up Vertex AI or AI Studio from env)
            from utils.genai_client import get_genai_client
            client = get_genai_client()
            print(f"EngineerAgent: retry {attempt}/{_ENGINEER_MAX_RETRIES}")

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": EngineeringResult,
                    "temperature": 0.7,
                    "max_output_tokens": 65536,
                },
            )

            # Try structured output first, but validate it
            if response.parsed is not None:
                try:
                    result = _validate_parsed_result(response.parsed)
                    result.files = _deduplicate_files(result.files)
                    return result
                except (ValidationError, ValueError, TypeError) as ve:
                    print(f"EngineerAgent: response.parsed malformed ({ve}), falling back to raw text")

            # Fallback: parse raw text
            raw = getattr(response, "text", "") or ""
            if raw.strip():
                data = _repair_json(raw)
                result = EngineeringResult.model_validate(data)
                result.files = _deduplicate_files(result.files)
                return result

            raise RuntimeError("EngineerAgent: empty response from Gemini (no parsed data and no text)")

        except Exception as e:
            last_err = e
            err_str = str(e)
            is_rate_limit = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
            is_validation = "validation error" in err_str.lower() or isinstance(e, (ValidationError, ValueError))

            if is_rate_limit or is_validation:
                wait = 2 ** attempt  # 1s, 2s, 4s
                print(f"EngineerAgent: attempt {attempt + 1} failed ({type(e).__name__}), retrying in {wait}s...")
                time.sleep(wait)
                continue

            # Non-retryable error — raise immediately
            raise

    raise RuntimeError(
        f"EngineerAgent: all {_ENGINEER_MAX_RETRIES} attempts failed. Last error: {last_err}"
    ) from last_err


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
                f"=== ITERATION MODE — STRICT SURGICAL EDIT RULES ===\n"
                f"You are modifying an EXISTING application. Follow these rules:\n"
                f"1. START from the existing code below. Do NOT generate from scratch.\n"
                f"2. PRESERVE everything not explicitly mentioned in the change request.\n"
                f"3. Do NOT redesign layout, colors, fonts, spacing, or structure\n"
                f"   unless the user specifically asked for that change.\n"
                f"4. The output must be RECOGNIZABLY THE SAME APP with only the\n"
                f"   requested changes applied.\n"
                f"5. If the change request is ambiguous, make the smallest edit that\n"
                f"   satisfies the intent.\n"
                f"=== END ITERATION RULES ===\n\n"
                f"--- EXISTING CODE (base to iterate on) ---\n"
                f"{existing_code}\n"
                f"--- END EXISTING CODE ---\n\n"
            )

        archetype_block = ""
        if task.ui_archetype:
            rules = task.archetype_rules
            rules_str = ""
            if rules:
                rules_str = (
                    f"\n  required_blocks: {rules.required_blocks}"
                    f"\n  required_interactions: {rules.required_interactions}"
                    f"\n  avoid: {rules.avoid}"
                    f"\n  layout_contract: {rules.layout_contract}"
                    f"\n  content_contract: {rules.content_contract}"
                )
            archetype_block = f"ui_archetype: {task.ui_archetype}\narchetype_rules:{rules_str}\n"

        quality_target_block = ""
        if task.quality_target:
            qt = task.quality_target
            quality_target_block = (
                f"\n--- QUALITY TARGET (what success looks like for THIS specific build) ---\n"
                f"visual_style: {qt.visual_style}\n"
                f"key_sections: {qt.key_sections}\n"
                f"must_have_content: {qt.must_have_content}\n"
                f"avoid: {qt.avoid}\n"
                f"--- END QUALITY TARGET ---\n"
            )

        contents = (
            f"{iteration_context}"
            f"{prompt}\n\n"
            f"{user_context}"
            f"--- TASK START ---\n"
            f"id: {task.id}\n"
            f"description: {task.description}\n"
            f"depends_on: {task.depends_on}\n"
            f"outputs: {task.outputs}\n"
            f"output_files: {task.output_files}\n"
            f"task_type: {task.task_type}\n"
            f"{archetype_block}"
            f"{quality_target_block}"
            f"--- TASK END ---"
        )

        # Primary: Gemini 2.5 Flash (Vertex AI)
        if self.client is None:
            from utils.genai_client import get_genai_client
            self.client = get_genai_client()

        return _run_gemini(self.client, contents)

