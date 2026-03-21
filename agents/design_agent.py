import base64
import concurrent.futures
import json
import os
import re
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from utils.genai_retry import call_with_retry

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _design_planning_model() -> str:
    return os.getenv("DESIGN_TEXT_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


def _design_image_model() -> str:
    return os.getenv("DESIGN_IMAGE_MODEL", "imagen-4.0-ultra-generate-001").strip() or "imagen-4.0-ultra-generate-001"


def _repair_json_array(raw: str) -> list:
    text = raw.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise RuntimeError(f"DesignAgent: no JSON array found.\nRaw: {raw[:500]}")
    return json.loads(text[start:end + 1])


def _generate_one(req, client, save_dir):
    def _normalize_image_bytes(raw: Any) -> bytes:
        if isinstance(raw, str):
            if raw.startswith("iVBOR"):
                return base64.b64decode(raw.encode("ascii"))
            return raw.encode("utf-8")
        if isinstance(raw, bytes):
            if raw.startswith(b"iVBOR"):
                return base64.b64decode(raw)
            return raw
        raise TypeError(f"Unexpected image payload type: {type(raw).__name__}")

    def _call_imagen(prompt):
        result = client.models.generate_images(
            model=_design_image_model(),
            prompt=prompt,
            config=types.GenerateImagesConfig(
                numberOfImages=1,
                aspectRatio="16:9",
                outputMimeType="image/png",
                personGeneration=types.PersonGeneration.ALLOW_ALL,
            ),
        )
        if not result.generated_images:
            raise RuntimeError("Imagen returned no images")
        return result.generated_images[0]

    try:
        print(f"  -> Generating: {req.get('key', 'unknown')} ({req.get('style', '')})")
        generated = call_with_retry(lambda: _call_imagen(req["prompt"]), max_retries=2)

        local_path = None
        url = None
        if save_dir:
            save_dir.mkdir(parents=True, exist_ok=True)
            img_filename = f"{req['key']}.png"
            img_dest = save_dir / img_filename
            img_dest.write_bytes(_normalize_image_bytes(generated.image.image_bytes))
            local_path = str(img_dest)
            print(f"  saved -> {img_dest.name}")

        return {
            "key": req["key"],
            "url": url,
            "local_path": local_path,
            "purpose": req.get("purpose", ""),
            "prompt": req["prompt"],
            "style": req.get("style", ""),
        }
    except Exception as e:
        print(f"  x Failed to generate {req.get('key')}: {e}")
        return None


class DesignAgent:
    def __init__(self, client: genai.Client | None = None, api_key: str | None = None):
        if client is not None:
            self.client = client
        else:
            import sys
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from utils.genai_client import get_genai_client
            self.client = get_genai_client()

    def run(
        self,
        prd_dict: dict,
        max_images: int = 4,
        save_dir: Path | None = None,
        reference_images: list[str] | None = None,
        nlu_context: dict | None = None,
        benchmark_style_context: str | None = None,
    ) -> list[dict[str, Any]]:
        prompt_template = (PROMPTS_DIR / "design_agent.txt").read_text(encoding="utf-8")
        prd_summary = json.dumps(prd_dict, indent=2)[:3000]
        nlu_hint = ""
        if nlu_context:
            keywords = nlu_context.get("keywords", []) or []
            entities = nlu_context.get("entities", []) or []
            concepts = nlu_context.get("concepts", []) or []
            entity_terms = [
                f"{e.get('text', '')} ({e.get('type', 'Unknown')})"
                for e in entities
                if e.get("text")
            ]
            nlu_hint = (
                "\n\nNLU CONTEXT FOR IMAGE PROMPTS:\n"
                f"- domain: {nlu_context.get('domain', 'general')}\n"
                f"- prompt_richness: {nlu_context.get('prompt_richness', 'sparse')}\n"
                f"- keywords: {', '.join(keywords) if keywords else '(none)'}\n"
                f"- concepts: {', '.join(concepts) if concepts else '(none)'}\n"
                f"- entities: {', '.join(entity_terms) if entity_terms else '(none)'}\n"
                "- Use relevant terms from these signals when crafting image prompts."
            )
        benchmark_block = ""
        if benchmark_style_context and benchmark_style_context.strip():
            benchmark_block = (
                "\n\nBENCHMARK STYLE CONTEXT:\n"
                f"{benchmark_style_context.strip()}\n"
                "Use this only for shell quality, atmosphere, motion, and image mood. "
                "Do not copy franchise-specific content from it.\n"
            )
        text_content = f"{prompt_template}\n\nPRD:\n{prd_summary}{nlu_hint}{benchmark_block}"

        # Build multimodal content if reference images provided
        if reference_images:
            parts = [types.Part.from_text(text=text_content)]
            parts.append(types.Part.from_text(text="\n\n--- USER REFERENCE IMAGES (analyze style and palette for Imagen prompts) ---"))
            _MIME_MAP = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
            for img_path in reference_images:
                p = Path(img_path)
                if p.exists():
                    mime = _MIME_MAP.get(p.suffix.lower(), "image/png")
                    parts.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=mime))
                    parts.append(types.Part.from_text(text=f"[Reference: {p.name}]"))
            parts.append(types.Part.from_text(text="--- END REFERENCE IMAGES ---\nAnalyze the visual style, color palette, and mood of these references. Generate Imagen prompts that produce images consistent with this style."))
            contents = parts
            print(f"DesignAgent: included {len(reference_images)} reference image(s) in planning call")
        else:
            contents = text_content

        def _call():
            return self.client.models.generate_content(
                model=_design_planning_model(),
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.7,
                },
            )

        response = call_with_retry(_call, max_retries=2)
        raw = response.text
        image_requests = _repair_json_array(raw)
        image_requests = image_requests[:max_images]

        # If no images needed, return early
        if not image_requests:
            print("DesignAgent: No images needed for this project.")
            return []

        print(f"DesignAgent: Generating {len(image_requests)} images with Imagen...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(_generate_one, req, self.client, save_dir) for req in image_requests]
            results = [f.result() for f in concurrent.futures.as_completed(futures) if f.result() is not None]

        print(f"DesignAgent: {len(results)}/{len(image_requests)} images generated.")
        return results

    def generate_visual_direction(
        self,
        prd_dict: dict,
        *,
        plan_dict: dict | None = None,
        existing_visual_direction: str | None = None,
        reference_images: list[str] | None = None,
        nlu_context: dict | None = None,
        benchmark_style_context: str | None = None,
    ) -> str:
        prompt_template = (PROMPTS_DIR / "design_direction.txt").read_text(encoding="utf-8")
        prd_summary = json.dumps(prd_dict, indent=2)[:5000]
        plan_summary = json.dumps(plan_dict or {}, indent=2)[:4000]

        existing_direction_block = ""
        if existing_visual_direction and existing_visual_direction.strip():
            existing_direction_block = (
                "\n\nEXISTING VISUAL DIRECTION TO PRESERVE UNLESS THE NEW BRIEF ASKS FOR A REDESIGN:\n"
                f"{existing_visual_direction.strip()[:4000]}\n"
            )

        nlu_hint = ""
        if nlu_context:
            keywords = nlu_context.get("keywords", []) or []
            concepts = nlu_context.get("concepts", []) or []
            entities = nlu_context.get("entities", []) or []
            entity_terms = [
                f"{e.get('text', '')} ({e.get('type', 'Unknown')})"
                for e in entities
                if e.get("text")
            ]
            nlu_hint = (
                "\n\nNLU CONTEXT:\n"
                f"- domain: {nlu_context.get('domain', 'general')}\n"
                f"- prompt_richness: {nlu_context.get('prompt_richness', 'sparse')}\n"
                f"- keywords: {', '.join(keywords) if keywords else '(none)'}\n"
                f"- concepts: {', '.join(concepts) if concepts else '(none)'}\n"
                f"- entities: {', '.join(entity_terms) if entity_terms else '(none)'}\n"
            )

        text_content = (
            f"{prompt_template}\n\n"
            f"PRODUCT BRIEF:\n{prd_summary}\n\n"
            f"IMPLEMENTATION PLAN:\n{plan_summary}"
            f"{existing_direction_block}"
            f"{nlu_hint}"
        )
        if benchmark_style_context and benchmark_style_context.strip():
            text_content += (
                "\n\nBENCHMARK STYLE CONTEXT:\n"
                f"{benchmark_style_context.strip()}\n"
                "Treat this as reusable visual grammar and quality bar only. "
                "Do not copy franchise-specific content or literal IP cues.\n"
            )

        contents: str | list[types.Part] = text_content
        if reference_images:
            parts: list[types.Part] = [types.Part.from_text(text=text_content)]
            parts.append(types.Part.from_text(text="\n\nREFERENCE IMAGES (use them for palette, density, and mood only):"))
            mime_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
                ".gif": "image/gif",
            }
            for img_path in reference_images:
                path = Path(img_path)
                if path.exists() and path.suffix.lower() in mime_map:
                    parts.append(types.Part.from_bytes(data=path.read_bytes(), mime_type=mime_map[path.suffix.lower()]))
                    parts.append(types.Part.from_text(text=f"[Reference: {path.name}]"))
            contents = parts

        def _call():
            return self.client.models.generate_content(
                model=_design_planning_model(),
                contents=contents,
                config={
                    "temperature": 0.5,
                },
            )

        response = call_with_retry(_call, max_retries=2)
        return (response.text or "").strip()
