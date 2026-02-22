from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

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
    """
    Generates images via DALL-E 3 based on PRD content.
    Returns a list of {key, url, purpose} dicts for the Build Agent.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required for DesignAgent")

    def run(self, prd_dict: dict, max_images: int = 4) -> list[dict[str, Any]]:
        """
        Analyze PRD and generate images.
        Returns list of {key, url, purpose, prompt} dicts.
        """
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        # Step 1: Ask GPT-4o-mini what images to generate
        prompt_template = (PROMPTS_DIR / "design_agent.txt").read_text(encoding="utf-8")

        prd_summary = json.dumps(prd_dict, indent=2)[:3000]  # Trim to avoid token waste

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_template},
                {"role": "user", "content": f"PRD:\n{prd_summary}"}
            ],
            temperature=0.7,
        )

        raw = response.choices[0].message.content
        image_requests = _repair_json_array(raw)
        image_requests = image_requests[:max_images]  # Enforce limit

        print(f"DesignAgent: Generating {len(image_requests)} images...")

        # Step 2: Generate each image via DALL-E 3
        results = []
        for req in image_requests:
            try:
                print(f"  → Generating: {req.get('key', 'unknown')} ({req.get('style', '')})")
                img_response = client.images.generate(
                    model="dall-e-3",
                    prompt=req["prompt"],
                    size="1792x1024",
                    quality="standard",
                    n=1,
                )
                url = img_response.data[0].url
                results.append({
                    "key": req["key"],
                    "url": url,
                    "purpose": req.get("purpose", ""),
                    "prompt": req["prompt"],
                    "style": req.get("style", ""),
                })
                print(f"  ✓ {req['key']}: {url[:60]}...")
            except Exception as e:
                print(f"  ✗ Failed to generate {req.get('key')}: {e}")
                continue

        print(f"DesignAgent: {len(results)}/{len(image_requests)} images generated.")
        return results
