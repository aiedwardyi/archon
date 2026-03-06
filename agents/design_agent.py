import concurrent.futures
import json
import re
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from utils.genai_retry import call_with_retry

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


def _generate_one(req, client, save_dir):
    def _call_imagen(prompt):
        result = client.models.generate_images(
            model="imagen-3.0-generate-002",
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
            img_dest.write_bytes(generated.image.image_bytes)
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

    def run(self, prd_dict: dict, max_images: int = 4, save_dir: Path | None = None) -> list[dict[str, Any]]:
        prompt_template = (PROMPTS_DIR / "design_agent.txt").read_text(encoding="utf-8")
        prd_summary = json.dumps(prd_dict, indent=2)[:3000]

        contents = f"{prompt_template}\n\nPRD:\n{prd_summary}"

        def _call():
            return self.client.models.generate_content(
                model="gemini-2.5-flash",
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
