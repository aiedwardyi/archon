from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path
from typing import Any

try:
    from json_repair import repair_json
    _JSON_REPAIR_AVAILABLE = True
except ImportError:
    _JSON_REPAIR_AVAILABLE = False

from google import genai
from pydantic import ValidationError

from schemas.plan_schema import Task
from schemas.engineering_schema import EngineeringResult, FileArtifact
from utils.design_families import (
    DESIGN_KIT_ALIASES,
    build_componentized_design_family_guidance,
    should_apply_componentized_global_family_layer,
)
from utils.offline_engineer_scaffold import build_vite_react_ts_scaffold
from utils.reference_build_registry import get_style_family_context

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

STYLE_FAMILY_CONTRACTS: dict[str, tuple[str, ...]] = {
    "operator_console_workspace": (
        "Use a dense operator-facing desktop shell with one dominant work surface and a support rail for alerts, queues, or active tasks.",
        "Avoid symmetrical KPI-card grids as the main experience; the product should feel like a live console with decisions happening inside it.",
        "Keep the layout serious, compact, and action-oriented rather than turning it into a polished but generic admin dashboard.",
    ),
    "editorial_workspace": (
        "Keep a visible desktop workspace with a real topbar, a dominant center canvas, and both side rails populated.",
        "Make collaboration and publishing states obvious through save state, comments, outline state, or inspector modules instead of KPI filler.",
        "Keep side rails useful with specific outline items, comments, review notes, or publish settings instead of generic lane titles like `Workspace`, `Notes`, or `Inspector`.",
        "Do not collapse this family into a centered article, generic dashboard, or thin landing-page shell.",
    ),
    "product_builder_workspace": (
        "Use a builder-grade workspace shell with a real top toolbar, a dominant primary work area, and dense supporting control surfaces.",
        "Builder-style prompts should usually read as a three-part desktop shell: context/navigation, dominant canvas, and a visible preview, QA, or launch-status rail.",
        "Blend setup, controls, status, and preview or review context into one cohesive product experience instead of separating them into disconnected cards.",
        "Keep builder rails populated with specific layers, prompts, runs, launch blockers, or QA notes instead of empty generic side chrome.",
        "Make the builder artifact or preview surface the main focal point. Do not lead with a KPI deck when the product is supposed to feel like an active studio or startup builder.",
        "If prompt layers are part of the brief, render them as structured rows, chips, cards, or modules with clear purpose labels instead of three bare textareas.",
        "If the brief mentions live preview, show a real browser, device, or page-preview surface rather than a monospaced text dump.",
        "A code block, quote, or plain paragraph does not count as the live preview. The preview should look like a rendered artifact with browser chrome, device framing, or visible UI composition.",
        "Favor app-builder framing over brochure sections or generic admin chrome.",
    ),
    "guided_setup_wizard": (
        "Keep the desktop layout split between progress/context and the active configuration flow.",
        "Show grouped step content plus at least one visible validation, readiness, or result-preview surface in the same flow.",
        "Keep a compact review, blocker, or readiness card visible beside the active step so the flow feels like a product sequence, not a plain form stack.",
        "Enterprise onboarding or compliance flows should keep a strong top bar and a visible snapshot or status lane instead of turning into a full-width form slab.",
        "When the brief mentions approvals, documents, blockers, or submission gating, keep those counts and statuses visible at first paint rather than burying them in helper text.",
        "Avoid generic startup onboarding language when the flow is really about requirements, approvals, or compliance checks.",
        "Use concrete setup states like validating, blocked, pending approval, ready to launch, or confirmed instead of generic helper copy.",
        "Avoid long flat form stacks, narrow floating cards, or disconnected success panels.",
    ),
    "market_terminal_workspace": (
        "Lead with a chart-first or market-control-first shell and keep the support rail useful with watchlist, tape, or market context modules.",
        "Use disciplined mono-friendly numeric treatment for prices, deltas, and tables so the workspace feels precise.",
        "Do not soften this family into a generic analytics dashboard with oversized decorative cards.",
    ),
}

DOMAIN_OVERLAY_CONTRACTS: dict[str, tuple[str, ...]] = {
    "operations_control_tower": (
        "Make the main surfaces about exceptions, dispatch, route health, or network state rather than revenue or generic business KPIs.",
        "Show at least one active operational control surface such as a dispatch queue, route board, incident feed, or shipment exception panel.",
        "Use workflow verbs like reroute, assign, escalate, acknowledge, or resolve instead of generic `View` / `Details` row actions.",
        "Keep the support rail focused on live alerts, SLA risk, depot pressure, or dispatch ownership rather than generic activity filler.",
    ),
    "sales_deal_room": (
        "Make next actions, deal risk, stage movement, and account context visible so the screen feels like active deal execution.",
        "Use pipeline boards, account timelines, stakeholder notes, or forecast pressure modules instead of generic ops widgets.",
        "Support rails should carry champion health, mutual action plans, call prep, or exec-sponsor asks instead of generic activity cards.",
        "Use sales verbs like log call, send recap, pull in exec sponsor, update MAP, or advance stage instead of generic row actions.",
    ),
    "treasury_liquidity_terminal": (
        "Anchor the composition around cash positions, funding windows, settlement pressure, and entity or bank exposure.",
        "Avoid soft SaaS KPI decks or retail trading cues; the UI should read like treasury operations, not a generic dashboard.",
        "Keep a real desktop terminal shell with a visible side rail beside the main treasury surfaces, not stacked underneath them.",
        "Use treasury operator verbs like release, hold, fund, reroute, or hedge on real payment, liquidity, or exposure objects.",
        "Keep the support rail focused on cut-off alerts, counterparty pressure, and funding deadlines rather than generic news filler.",
    ),
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
    _VALID_ESCAPES = {'"', "\\", "/", "b", "f", "n", "r", "t", "u"}
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
        truncation_hint = ""
        if start != -1 and (end == -1 or end <= start):
            truncation_hint = " (output appears truncated — JSON started but never closed)"
        raise RuntimeError(
            f"EngineerAgent: no JSON object found in model output{truncation_hint}.\n\n"
            f"Raw output (first 2000 chars):\n{raw[:2000]}"
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


def _prompt_mentions_any(prompt_text: str | None, tokens: tuple[str, ...]) -> bool:
    normalized = (prompt_text or "").strip().lower()
    if not normalized:
        return False
    return any(token in normalized for token in tokens)


def _looks_like_builder_studio_prompt(prompt_text: str | None) -> bool:
    return _prompt_mentions_any(
        prompt_text,
        (
            "builder",
            "studio",
            "canvas",
            "live preview",
            "preview rail",
            "prompt layers",
            "variant runs",
            "launch blockers",
            "qa notes",
            "design assistant",
            "founder workspace",
            "web design assistant",
        ),
    )


def _looks_like_compliance_wizard_prompt(prompt_text: str | None) -> bool:
    return _prompt_mentions_any(
        prompt_text,
        (
            "wizard",
            "onboarding",
            "approval",
            "approver",
            "compliance",
            "documents",
            "blocker",
            "snapshot",
            "review sidebar",
            "review & submit",
            "requirements summary",
            "application snapshot",
            "vendor",
        ),
    )


def _build_componentized_specialized_contract_block(
    archetype: str | None,
    prompt_text: str | None,
    *,
    existing_code: str | None = None,
    reference_code: dict[str, Any] | None = None,
) -> str:
    if existing_code:
        return ""

    normalized_archetype = str(archetype or "").strip().lower()
    reference_label = str((reference_code or {}).get("label", "")).strip().lower()
    blocks: list[str] = []

    if (
        normalized_archetype in {"editor", "ai_product", "productivity_app", "dev_tool"}
        and _looks_like_builder_studio_prompt(prompt_text)
    ) or reference_label == "legacy-designai-startup-builder":
        blocks.append(
            "\n".join(
                [
                    "--- SPECIALIZED BUILDER / STUDIO CONTRACT ---",
                    "- Treat this as a startup-builder or AI design studio, not a document editor and not a generic KPI dashboard.",
                    "- The default desktop frame should read as one working product shell: top toolbar, persistent left context rail, dominant center builder canvas, and right preview/properties/launch rail.",
                    "- The center stage must show an artifact in progress such as a page composition, selected block, generated homepage, variant output, or browser-style preview. Do not use a KPI row as the main focal point.",
                    "- Do not center the workspace on a paper-like brief, article, or document with a byline or `last edited` meta strip. The middle of the screen should feel like a builder board, staged composition, or live preview workspace.",
                    "- Match the visual tone of `legacy-designai-startup-builder`: darker charcoal product chrome, restrained teal-led accents, and cleaner product-display typography rather than warm beige editorial paper.",
                    "- If onboarding or setup is part of the brief, keep it integrated as a compact first-run strip, progress card, or setup panel inside the workspace instead of splitting into a separate marketing page.",
                    "- If the brief mentions live preview, render a real preview frame, browser shell, or device-like module rather than plain paragraph text.",
                    "- A code snippet, quoted sentence, or generic paragraph card does not count as the live preview. The preview must look like a rendered product surface with visible browser or device chrome.",
                    "- If the brief mentions prompt layers, show them as structured chips, cards, or ordered rows with role labels, status, and controls. Do not solve them with three identical raw textareas.",
                    "- Do not make one large central textarea or rich-text editor slab the primary interaction. Prompt layers should read like compact builder modules with short fields, toggles, chips, run actions, and visible state.",
                    "- If the brief mentions variant runs, keep a dense runs surface with status, score, latency, or selection state that feeds the main preview or builder canvas.",
                    "- If the brief mentions launch blockers or QA notes, keep them in a dedicated status rail with severity, owner, or next action so the workspace feels like a launch tool.",
                    "- When prompt layers, variant runs, launch blockers, or QA notes are part of the brief, keep at least two of those work surfaces visible above the fold.",
                    "- Analytics or performance modules can appear, but they must be subordinate to the builder surface instead of replacing it.",
                    "- Avoid document-editor defaults like outline, comments, slash-command bars, rich-text formatting controls, publish settings, and serif editorial title treatment unless the prompt explicitly asks for them.",
                    "- Match the shell logic of `legacy-designai-startup-builder`: hybrid builder workspace, setup cues, previewable output, and dense control surfaces in one cohesive product frame.",
                    "--- END SPECIALIZED BUILDER / STUDIO CONTRACT ---",
                ]
            )
        )

    if (
        normalized_archetype in {"form", "ai_product", "productivity_app", "dev_tool"}
        and _looks_like_compliance_wizard_prompt(prompt_text)
    ) or reference_label == "legacy-ai-automation-onboarding-wizard":
        blocks.append(
            "\n".join(
                [
                    "--- SPECIALIZED ENTERPRISE WIZARD CONTRACT ---",
                    "- Treat this as an enterprise onboarding or compliance workflow, not a generic signup form.",
                    "- Keep a strong top product bar plus a desktop split shell: visible step rail, dominant active-step panel, and a compact snapshot or status lane that stays useful at first paint.",
                    "- The snapshot lane should surface concrete application context such as company details, requirements progress, blockers, pending approvals, document counts, or readiness state.",
                    "- Use domain step names tied to the brief, such as company details, compliance documents, approver routing, review and submit. Avoid generic `Step 1` labels when the flow is clearly procedural.",
                    "- Show unresolved blockers, pending documents, or pending approvals by default when the brief implies submission gating.",
                    "- Keep review and blocker state visually connected to the active step instead of hiding it as a distant final section.",
                    "- For document or approval flows, use badges, counts, pending labels, approved labels, and status rows instead of plain helper paragraphs.",
                    "- Avoid floating single-card forms, giant empty gutters, and generic startup onboarding language that ignores the review or compliance context.",
                    "- Match the shell logic of `legacy-ai-automation-onboarding-wizard`: stronger enterprise structure, grouped steps, and visible snapshot or blocker surfaces throughout the flow.",
                    "--- END SPECIALIZED ENTERPRISE WIZARD CONTRACT ---",
                ]
            )
        )

    return "\n\n".join(blocks)


def _build_componentized_family_prompt_block(
    archetype: str | None,
    prompt_text: str | None,
    *,
    existing_code: str | None = None,
) -> str:
    if existing_code or not archetype:
        return ""

    family_context = get_style_family_context(archetype, prompt_text)
    if not family_context:
        return ""

    style_family = str(family_context.get("style_family", "")).strip()
    description = str(family_context.get("description", "")).strip()
    guidance_lines = list(family_context.get("guidance_lines", []))
    guidance_lines.extend(STYLE_FAMILY_CONTRACTS.get(style_family, ()))
    domain_overlay = str(family_context.get("domain_overlay", "")).strip()
    overlay_description = str(family_context.get("overlay_description", "")).strip()
    overlay_guidance_lines = list(family_context.get("overlay_guidance_lines", []))
    overlay_guidance_lines.extend(DOMAIN_OVERLAY_CONTRACTS.get(domain_overlay, ()))

    deduped_lines: list[str] = []
    seen: set[str] = set()
    for line in guidance_lines:
        normalized = str(line).strip()
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped_lines.append(normalized)

    deduped_overlay_lines: list[str] = []
    seen_overlay: set[str] = set()
    for line in overlay_guidance_lines:
        normalized = str(line).strip()
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen_overlay:
            continue
        seen_overlay.add(lowered)
        deduped_overlay_lines.append(normalized)

    body_lines = [
        "--- GLOBAL QUALITY FAMILY ---",
    ]
    if style_family:
        body_lines.append(f"style_family: {style_family}")
    if description:
        body_lines.append(f"family_purpose: {description}")
    body_lines.append(
        "Treat this as a reusable product-quality contract that should raise structure, density, and interaction clarity even when the prompt is underspecified."
    )
    body_lines.extend(f"- {line}" for line in deduped_lines)
    if domain_overlay:
        body_lines.append("")
        body_lines.append("--- DOMAIN OVERLAY ---")
        body_lines.append(f"domain_overlay: {domain_overlay}")
        if overlay_description:
            body_lines.append(f"overlay_purpose: {overlay_description}")
        body_lines.extend(f"- {line}" for line in deduped_overlay_lines)
        body_lines.append("--- END DOMAIN OVERLAY ---")
    body_lines.append("--- END GLOBAL QUALITY FAMILY ---")
    return "\n\n" + "\n".join(body_lines)


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

            # Detect truncation: if raw text doesn't end with }, output was cut off
            raw_check = (getattr(response, "text", "") or "").strip()
            raw_check = re.sub(r"\s*```$", "", raw_check).strip()
            if raw_check and not raw_check.endswith("}"):
                if attempt < _ENGINEER_MAX_RETRIES - 1:
                    print("EngineerAgent: output truncated (hit 65k token limit), retrying with compression instruction...")
                    # Add compression instruction and retry with same token limit
                    compress_note = (
                        "\n\nCRITICAL OUTPUT SIZE CONSTRAINT: Your previous attempt was truncated because "
                        "the output exceeded the token limit. You MUST reduce output size:\n"
                        "- Replace ALL inline SVGs with single-character Unicode symbols or HTML entities "
                        "(e.g. ★, →, ●, ✦, ▸, &hearts;, &#9733;)\n"
                        "- Use CSS pseudo-elements (::before) with content: 'symbol' instead of SVG markup\n"
                        "- Keep style.css under 60 lines\n"
                        "- No SVG markup anywhere in index.html\n"
                    )
                    if isinstance(gemini_contents, list):
                        from google.genai import types
                        gemini_contents.append(types.Part.from_text(text=compress_note))
                    else:
                        gemini_contents = gemini_contents + compress_note
                    continue  # Go to next retry attempt with modified prompt

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

    def run(
        self,
        task: Task,
        user_prompt: str = None,
        existing_code: str = None,
        reference_images: list[str] | None = None,
        attach_reference_images: bool = True,
        reference_code: dict[str, Any] | None = None,
        iteration_visual_dna: dict[str, Any] | None = None,
        iteration_feature_inventory: dict[str, Any] | None = None,
    ) -> EngineeringResult:
        if task.execution_hint != "engineer":
            raise ValueError("EngineerAgent called with non-executable task")

        if task.task_type != "scaffold":
            raise ValueError(f"Unsupported task_type: {task.task_type}")

        if _is_offline_mode() or str(task.id).startswith("OFFLINE-"):
            return _build_offline_engineering_result(task_id=str(task.id))

        archetype = task.ui_archetype
        scaffold_mode = task.scaffold_mode or "legacy_single_page"
        kit_archetype = DESIGN_KIT_ALIASES.get(archetype, archetype)
        archetypes_dir = PROMPTS_DIR / "archetypes"
        archetype_txt = archetypes_dir / f"{kit_archetype}.txt" if kit_archetype else None
        archetype_css = archetypes_dir / f"{kit_archetype}.css" if kit_archetype else None

        if scaffold_mode == "componentized_app":
            prompt = (PROMPTS_DIR / "engineer_componentized.txt").read_text(encoding="utf-8")
            family_guidance = ""
            if should_apply_componentized_global_family_layer(archetype):
                family_guidance = build_componentized_design_family_guidance(
                    archetype,
                    user_prompt or task.description,
                )
            if family_guidance:
                prompt += (
                    "\n\n--- DESIGN FAMILY FOUNDATION ---\n"
                    "Apply this shared family contract before archetype-specific flourish.\n"
                    f"{family_guidance}\n"
                    "--- END DESIGN FAMILY FOUNDATION ---"
                )
            prompt += _build_componentized_family_prompt_block(
                archetype,
                user_prompt or task.description,
                existing_code=existing_code,
            )
            if archetype_txt and archetype_txt.exists():
                prompt += (
                    "\n\n--- DESIGN KIT REFERENCE ---\n"
                    "Translate these archetype requirements into a componentized React app.\n"
                    "Reuse the layout rhythm, content density, interaction expectations, and visual direction.\n"
                    "Do NOT revert to single-page HTML, but do preserve the same polish bar.\n"
                    f"{archetype_txt.read_text(encoding='utf-8')}\n"
                    "--- END DESIGN KIT REFERENCE ---"
                )
            if archetype_css and archetype_css.exists():
                prompt += (
                    "\n\n--- BASE CSS REFERENCE ---\n"
                    "A base design-system stylesheet will be available at src/base.css in the workspace.\n"
                    "Use these tokens, classes, and visual primitives as the design language foundation.\n"
                    "Prefer the provided shell and class vocabulary directly in JSX before inventing new wrapper classes.\n"
                    "Import src/base.css from src/main.tsx before app-specific styles.\n"
                    "Do NOT inline this stylesheet into App.tsx or a <style> tag.\n"
                    f"{archetype_css.read_text(encoding='utf-8')}\n"
                    "--- END BASE CSS REFERENCE ---"
                )
            specialized_contract = _build_componentized_specialized_contract_block(
                archetype,
                user_prompt or task.description,
                existing_code=existing_code,
                reference_code=reference_code,
            )
            if specialized_contract:
                prompt += f"\n\n{specialized_contract}"
        elif archetype_txt and archetype_txt.exists():
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
            visual_dna_block = ""
            if iteration_visual_dna:
                visual_dna_block = (
                    "--- VISUAL DNA LOCK (preserve unless the request explicitly asks for a redesign) ---\n"
                    f"{json.dumps(iteration_visual_dna, indent=2, ensure_ascii=False)}\n"
                    "--- END VISUAL DNA LOCK ---\n\n"
                )
            feature_inventory_block = ""
            if iteration_feature_inventory:
                feature_inventory_block = (
                    "--- FEATURE PRESERVATION LOCK (keep these features working unless explicitly replaced) ---\n"
                    f"{json.dumps(iteration_feature_inventory, indent=2, ensure_ascii=False)}\n"
                    "--- END FEATURE PRESERVATION LOCK ---\n\n"
                )
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
                f"{visual_dna_block}"
                f"{feature_inventory_block}"
                f"--- EXISTING CODE (base to iterate on) ---\n"
                f"{existing_code}\n"
                f"--- END EXISTING CODE ---\n\n"
            )

        reference_context = ""
        if reference_code and not existing_code:
            print(
                f"[Discovery] EngineerAgent using reference build "
                f"(score: {reference_code.get('score', 'N/A')})"
            )
            style_family = str(reference_code.get("style_family", "")).strip()
            benchmark_guidance = str(reference_code.get("benchmark_guidance", "")).strip()
            benchmark_guidance_block = ""
            if benchmark_guidance:
                benchmark_guidance_block = (
                    "--- BENCHMARK DESIGN TRAITS (shared patterns across strong legacy examples) ---\n"
                    f"{benchmark_guidance}\n"
                    "--- END BENCHMARK DESIGN TRAITS ---\n"
                )
            style_family_block = ""
            if style_family:
                style_family_block = (
                    "--- STYLE FAMILY ---\n"
                    f"{style_family}\n"
                    "Treat this as reusable visual grammar and interaction language, not literal franchise content.\n"
                    "Preserve the shell quality, card/button language, density, and motion patterns while rewriting all content to match the current brief.\n"
                    "--- END STYLE FAMILY ---\n"
                )
            reference_context = (
                "=== REFERENCE BUILD (high-scoring example for this archetype) ===\n"
                "Study this working example carefully. It scored well on design quality.\n"
                "Use it as INSPIRATION for layout structure, visual patterns, and CSS techniques.\n"
                "Do NOT copy it verbatim — create something original that matches or exceeds its quality.\n"
                f"{style_family_block}"
                f"{benchmark_guidance_block}"
                "--- REFERENCE HTML ---\n"
                f"{reference_code.get('html', '')}\n"
                "--- REFERENCE CSS ---\n"
                f"{reference_code.get('css', '')}\n"
                "=== END REFERENCE BUILD ===\n\n"
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
                f"interactivity: {qt.interactivity}\n"
                f"avoid: {qt.avoid}\n"
                f"--- END QUALITY TARGET ---\n"
            )

        contents = (
            f"{iteration_context}"
            f"{reference_context}"
            f"{prompt}\n\n"
            f"{user_context}"
            f"--- TASK START ---\n"
            f"id: {task.id}\n"
            f"description: {task.description}\n"
            f"depends_on: {task.depends_on}\n"
            f"outputs: {task.outputs}\n"
            f"scaffold_mode: {scaffold_mode}\n"
            f"output_files: {task.output_files}\n"
            f"task_type: {task.task_type}\n"
            f"render_path: {task.render_path}\n"
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

        # Add user-uploaded reference images when this run should remain multimodal.
        if reference_images and attach_reference_images:
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

        # Inject design kit CSS as a file artifact (legacy initial build only)
        if scaffold_mode != "componentized_app" and css_kit_content and not existing_code:
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

        reference_kit_archetype = None
        if reference_code:
            reference_archetype = reference_code.get("archetype")
            if isinstance(reference_archetype, str):
                reference_kit_archetype = DESIGN_KIT_ALIASES.get(reference_archetype, reference_archetype)

        should_strip_saas_images = (
            scaffold_mode != "componentized_app"
            and
            kit_archetype == "saas_landing"
            and (reference_code is None or reference_kit_archetype == "saas_landing")
        )

        if should_strip_saas_images:
            count = 0
            for f in result.files:
                if f.path.endswith(".html"):
                    stripped_count = len(re.findall(r'<img[^>]*/?>', f.content))
                    if stripped_count > 0:
                        f.content = re.sub(r'<img[^>]*/?>', '', f.content)
                        count += stripped_count
            if count > 0:
                print(f"EngineerAgent: stripped {count} <img> tags from saas_landing HTML")

        return result

