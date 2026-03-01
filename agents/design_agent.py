import concurrent.futures
import json
import os
import re
import urllib.request
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
    Returns a list of {key, url, local_path, purpose} dicts for the Build Agent.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required for DesignAgent")

    def run(self, prd_dict: dict, max_images: int = 4, save_dir: Path | None = None) -> list[dict[str, Any]]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        prompt_template = (PROMPTS_DIR / "design_agent.txt").read_text(encoding="utf-8")
        prd_summary = json.dumps(prd_dict, indent=2)[:3000]

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
        image_requests = image_requests[:max_images]

        print(f"DesignAgent: Generating {len(image_requests)} images...")

        def _generate_one(req, client, save_dir):
            try:
                print(f"  -> Generating: {req.get('key', 'unknown')} ({req.get('style', '')})")
                img_response = client.images.generate(
                    model="dall-e-3",
                    prompt=req["prompt"],
                    size="1792x1024",
                    quality="standard",
                    n=1,
                )
                url = img_response.data[0].url
                print(f"  + {req['key']}: {url[:60]}...")

                local_path = None
                if save_dir:
                    save_dir.mkdir(parents=True, exist_ok=True)
                    img_filename = f"{req['key']}.png"
                    img_dest = save_dir / img_filename
                    try:
                        urllib.request.urlretrieve(url, img_dest)
                        local_path = str(img_dest)
                        print(f"  saved -> {img_dest.name}")
                    except Exception as dl_err:
                        print(f"  download failed for {req['key']}: {dl_err}")

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

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(_generate_one, req, client, save_dir) for req in image_requests]
            results = [f.result() for f in concurrent.futures.as_completed(futures) if f.result() is not None]

        print(f"DesignAgent: {len(results)}/{len(image_requests)} images generated.")
        return results
