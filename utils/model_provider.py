"""
Model provider abstraction for eval scoring and improvement.
Supports Gemini (cloud) and Ollama (local) backends.
"""

import base64
import json
import logging
import os
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Wraps Ollama's local HTTP API for vision and text generation."""

    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _resize_for_ollama(self, image_path: Path, max_dimension: int = 1920) -> bytes:
        """Resize image to fit Ollama's practical limits and return JPEG bytes."""
        from PIL import Image
        import io

        Image.MAX_IMAGE_PIXELS = None
        img = Image.open(image_path)

        # Downscale if either dimension exceeds max
        if img.width > max_dimension or img.height > max_dimension:
            scale = min(max_dimension / img.width, max_dimension / img.height)
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
            logger.info(f"Resized for Ollama: {img.width}x{img.height}px")

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return buf.getvalue()

    def generate_with_image(self, prompt: str, image_path: Path, temperature: float = 0.3) -> str:
        """Send a vision request to Ollama (for scoring)."""
        image_bytes = self._resize_for_ollama(image_path)
        image_data = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_data],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 4096,
            },
        }
        logger.info(f"Ollama vision request: model={self.model}, image={image_path.name}")
        resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=600)
        resp.raise_for_status()
        return resp.json().get("response", "")

    def generate_text(self, prompt: str, system: str = "", temperature: float = 0.4) -> str:
        """Send a text-only request to Ollama (for improving)."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 8192,
            },
        }
        logger.info(f"Ollama text request: model={self.model}")
        resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json().get("response", "")


def create_scorer_provider(config: dict, genai_client=None) -> dict:
    """Return a dict with 'type' and provider object for scoring.

    Checks env var EVAL_SCORER_PROVIDER first, then config file.
    Returns {'type': 'ollama', 'provider': OllamaProvider} or
            {'type': 'gemini', 'provider': None} (use existing client).
    """
    provider_name = os.getenv("EVAL_SCORER_PROVIDER", config.get("scorer_provider", "gemini")).lower()

    if provider_name == "ollama":
        model = os.getenv("LOCAL_SCORER_MODEL", config.get("local_scorer_model", "qwen2.5vl:7b"))
        base_url = os.getenv("OLLAMA_BASE_URL", config.get("ollama_base_url", "http://localhost:11434"))
        logger.info(f"Scorer provider: Ollama (model={model}, url={base_url})")
        return {"type": "ollama", "provider": OllamaProvider(model=model, base_url=base_url)}

    logger.info("Scorer provider: Gemini (cloud)")
    return {"type": "gemini", "provider": None}


def create_improver_provider(config: dict, genai_client=None) -> dict:
    """Return a dict with 'type' and provider object for improving.

    Same pattern as scorer — checks EVAL_IMPROVER_PROVIDER env var first.
    """
    provider_name = os.getenv("EVAL_IMPROVER_PROVIDER", config.get("improver_provider", "gemini")).lower()

    if provider_name == "ollama":
        model = os.getenv("LOCAL_IMPROVER_MODEL", config.get("local_improver_model", "gemma3:12b"))
        base_url = os.getenv("OLLAMA_BASE_URL", config.get("ollama_base_url", "http://localhost:11434"))
        logger.info(f"Improver provider: Ollama (model={model}, url={base_url})")
        return {"type": "ollama", "provider": OllamaProvider(model=model, base_url=base_url)}

    logger.info("Improver provider: Gemini (cloud)")
    return {"type": "gemini", "provider": None}
