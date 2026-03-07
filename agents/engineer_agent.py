from __future__ import annotations

import base64
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

# Map similar archetypes to a shared design kit
DESIGN_KIT_ALIASES = {
    "ai_product": "saas_landing",
    "dev_tool": "saas_landing",
    "productivity_app": "saas_landing",
    "game_companion": "game",
    "fan_page": "game",
    "game_ff7": "game",
    "game_ff8": "game",
    "game_ff9": "game",
    "interactive_experience": "game",
    "admin_panel": "dashboard",
    "analytics": "dashboard",
    "crm": "dashboard",
    "online_store": "ecommerce",
    "marketplace": "ecommerce",
    "shop": "ecommerce",
    "agency": "portfolio",
    "personal_site": "portfolio",
    "freelancer": "portfolio",
}


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

_IMG_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _load_reference_images(kit_archetype: str) -> list[tuple[str, bytes, str]]:
    """Load reference images for an archetype.
    Returns list of (filename, raw_bytes, mime_type)."""
    refs_dir = PROMPTS_DIR / "archetypes" / "references" / kit_archetype
    if not refs_dir.exists():
        return []
    images = []
    for img_path in sorted(refs_dir.iterdir()):
        if img_path.suffix.lower() in _IMG_EXTENSIONS:
            mime = {
                ".png": "image/png", ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg", ".webp": "image/webp",
                ".gif": "image/gif",
            }[img_path.suffix.lower()]
            images.append((img_path.name, img_path.read_bytes(), mime))
    return images


def _run_claude(contents: str, ref_images: list[tuple[str, bytes, str]] | None = None) -> EngineeringResult:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Build multimodal content if reference images provided
    message_content: list | str = contents
    if ref_images:
        message_content = []
        message_content.append({"type": "text", "text": contents})
        message_content.append({"type": "text", "text": "\n\n--- REFERENCE SCREENSHOTS (match this quality and layout) ---"})
        for filename, img_bytes, mime in ref_images:
            message_content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": mime, "data": base64.b64encode(img_bytes).decode()},
            })
            message_content.append({"type": "text", "text": f"[Reference: {filename}]"})
        message_content.append({"type": "text", "text": "--- END REFERENCE SCREENSHOTS ---\nStudy these references carefully. Match the layout structure, visual density, and polish level shown above."})

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
                messages=[{"role": "user", "content": message_content}],
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


def _run_gemini(client: genai.Client, contents: str, ref_images: list[tuple[str, bytes, str]] | None = None) -> EngineeringResult:
    last_err = None
    for attempt in range(_ENGINEER_MAX_RETRIES):
        if attempt > 0:
            # Fresh client on retry (picks up Vertex AI or AI Studio from env)
            from utils.genai_client import get_genai_client
            client = get_genai_client()
            print(f"EngineerAgent: retry {attempt}/{_ENGINEER_MAX_RETRIES}")

        try:
            # Build multimodal content if reference images provided
            gemini_contents = contents
            if ref_images:
                from google.genai import types
                parts = [types.Part.from_text(text=contents)]
                parts.append(types.Part.from_text(text="\n\n--- REFERENCE SCREENSHOTS (match this quality and layout) ---"))
                for filename, img_bytes, mime in ref_images:
                    parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))
                    parts.append(types.Part.from_text(text=f"[Reference: {filename}]"))
                parts.append(types.Part.from_text(text="--- END REFERENCE SCREENSHOTS ---\nStudy these references carefully. Match the layout structure, visual density, and polish level shown above."))
                gemini_contents = parts

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=gemini_contents,
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


def _dedup_style_css(base_css: str, style_css: str) -> str:
    """Remove top-level CSS blocks from style_css that duplicate base.css."""
    try:
        # Extract top-level selectors from base.css
        base_selectors: set[str] = set()
        for m in re.finditer(r'^([^{@/\n][^{]*?)\s*\{', base_css, re.MULTILINE):
            sel = m.group(1).strip()
            if sel:
                base_selectors.add(sel)

        # Always-remove patterns (resets / variables that belong in base.css)
        always_remove = re.compile(
            r'^(?:'
            r':root'
            r'|\*\s*,\s*\*::before'
            r'|\*::before'
            r'|\*\s*\{'          # bare * reset
            r'|html\s*[,{]'
            r'|body\s*[,{]'
            r'|a\s*[,{]'
            r'|img\s*[,{]'
            r')',
            re.MULTILINE,
        )

        # Detect fonts already imported in base.css
        base_fonts: set[str] = set()
        for m in re.finditer(r'@import\s+url\(["\']?([^"\')\s]+)', base_css):
            base_fonts.add(m.group(1))

        # Split style_css into top-level blocks (selector { ... })
        # We walk character by character to handle nested braces
        blocks: list[tuple[str, str]] = []  # (raw_block_text, selector)
        i = 0
        length = len(style_css)
        while i < length:
            # Skip whitespace / comments between blocks
            start = i
            while i < length and style_css[i] in ' \t\n\r':
                i += 1
            if i >= length:
                break

            # Check for @import line
            if style_css[i:i+7] == '@import':
                end = style_css.find(';', i)
                if end == -1:
                    end = length
                raw = style_css[start:end+1]
                blocks.append((raw, style_css[i:end+1].strip()))
                i = end + 1
                continue

            # Find opening brace
            brace = style_css.find('{', i)
            if brace == -1:
                # Remaining text (no more blocks)
                blocks.append((style_css[start:], ''))
                break

            selector = style_css[i:brace].strip()
            # Walk to matching closing brace
            depth = 1
            j = brace + 1
            while j < length and depth > 0:
                if style_css[j] == '{':
                    depth += 1
                elif style_css[j] == '}':
                    depth -= 1
                j += 1
            raw = style_css[start:j]
            blocks.append((raw, selector))
            i = j

        # Filter blocks
        kept: list[str] = []
        for raw, selector in blocks:
            if not selector and not raw.strip():
                continue

            # Remove @import for fonts already in base.css
            if selector.startswith('@import'):
                is_dup_font = False
                for font_url in base_fonts:
                    if font_url in selector:
                        is_dup_font = True
                        break
                if is_dup_font:
                    continue

            # Remove always-remove patterns
            if always_remove.match(selector):
                continue

            # Remove blocks whose selector exactly matches a base.css selector
            if selector in base_selectors:
                continue

            kept.append(raw)

        return '\n'.join(kept).strip() + '\n' if kept else style_css
    except Exception:
        return style_css


class EngineerAgent:
    def __init__(self, client: genai.Client | None):
        self.client = client

    def run(self, task: Task, user_prompt: str = None, existing_code: str = None, reference_images: list[str] | None = None) -> EngineeringResult:
        if task.execution_hint != "engineer":
            raise ValueError("EngineerAgent called with non-executable task")

        if task.task_type != "scaffold":
            raise ValueError(f"Unsupported task_type: {task.task_type}")

        if _is_offline_mode() or str(task.id).startswith("OFFLINE-"):
            return _build_offline_engineering_result(task_id=str(task.id))

        archetype = task.ui_archetype
        kit_archetype = DESIGN_KIT_ALIASES.get(archetype, archetype)
        archetypes_dir = PROMPTS_DIR / "archetypes"
        archetype_txt = archetypes_dir / f"{kit_archetype}.txt" if kit_archetype else None
        archetype_css = archetypes_dir / f"{kit_archetype}.css" if kit_archetype else None

        if archetype_txt and archetype_txt.exists():
            prompt = (PROMPTS_DIR / "engineer_core.txt").read_text(encoding="utf-8")
            prompt += "\n\n" + archetype_txt.read_text(encoding="utf-8")
        else:
            prompt = (PROMPTS_DIR / "engineer.txt").read_text(encoding="utf-8")

        css_kit_content = None
        if archetype_css and archetype_css.exists():
            css_kit_content = archetype_css.read_text(encoding="utf-8")

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

        # Load reference images for this archetype (if available, initial build only)
        ref_images = []
        if kit_archetype and not existing_code:
            ref_images = _load_reference_images(kit_archetype)
            if ref_images:
                print(f"EngineerAgent: loaded {len(ref_images)} archetype reference images for '{kit_archetype}'")

        # Add user-uploaded reference images
        if reference_images:
            _MIME_MAP = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
            for img_path in reference_images:
                p = Path(img_path)
                if p.exists() and p.suffix.lower() in _MIME_MAP:
                    mime = _MIME_MAP[p.suffix.lower()]
                    ref_images.append((p.name, p.read_bytes(), mime))
            if reference_images:
                print(f"EngineerAgent: added {len(reference_images)} user reference image(s)")
                # Append instruction to prompt
                contents += "\n\nIMPORTANT: The user has provided visual reference images. Match the visual style, layout structure, and color palette shown in these references as closely as possible."

        # Model selection via ENGINEER_MODEL env var
        # Options: "gemini" (default), "claude", "openai"
        model_choice = os.getenv("ENGINEER_MODEL", "gemini").lower().strip()

        if model_choice == "claude":
            result = _run_claude(contents, ref_images=ref_images or None)
        else:
            # Default: Gemini 2.5 Flash (Vertex AI)
            if self.client is None:
                from utils.genai_client import get_genai_client
                self.client = get_genai_client()
            result = _run_gemini(self.client, contents, ref_images=ref_images or None)

        # Inject design kit CSS as a file artifact (initial build only)
        if css_kit_content and not existing_code:
            result.files.insert(0, FileArtifact(
                path="src/base.css",
                content=css_kit_content,
            ))

            # Deduplicate style.css against base.css
            for f in result.files:
                if f.path == "src/style.css":
                    original_len = len(f.content)
                    f.content = _dedup_style_css(css_kit_content, f.content)
                    new_len = len(f.content)
                    if new_len < original_len:
                        print(f"EngineerAgent: dedup style.css {original_len} -> {new_len} chars (-{original_len - new_len})")
                    break

        return result

