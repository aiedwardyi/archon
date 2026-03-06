import json
import os
import re
from pathlib import Path
from typing import Any
from utils.genai_client import get_genai_client

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


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


class DesignAgent:
    def __init__(self, api_key: str | None = None):
        self.client = get_genai_client()

    def run(self, prd_dict: dict, max_images: int = 4, save_dir: Path | None = None) -> list[dict[str, Any]]:
        prompt_template = (PROMPTS_DIR / "design_agent.txt").read_text(encoding="utf-8")
        prd_summary = json.dumps(prd_dict, indent=2)[:3000]

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"PRD:\n{prd_summary}",
            config={
                "system_instruction": prompt_template,
                "temperature": 0.7,
                "max_output_tokens": 2000,
            },
        )

        raw = (getattr(response, "text", "") or "").strip()
        if not raw:
            print("DesignAgent: Empty response, skipping image generation.")
            return []

        image_requests = _repair_json_array(raw)
        image_requests = image_requests[:max_images]

        # Return image prompts as metadata (no DALL-E generation — using Vertex AI)
        print(f"DesignAgent: Generated {len(image_requests)} image prompts (no image generation).")
        results = []
        for req in image_requests:
            results.append({
                "key": req.get("key", "unknown"),
                "url": "",
                "local_path": None,
                "purpose": req.get("purpose", ""),
                "prompt": req.get("prompt", ""),
                "style": req.get("style", ""),
            })
        return results
