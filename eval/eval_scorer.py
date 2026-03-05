"""
Vision-based design scoring using Claude API.
"""

import json
import base64
import logging
from pathlib import Path

from scoring_rubric import (
    DIMENSIONS,
    ScoringResult,
    compute_weighted_total,
    build_rubric_text,
)

logger = logging.getLogger(__name__)

SCORER_SYSTEM_PROMPT = """\
You are an elite UI/UX design evaluator working for a company that needs to produce \
THE BEST web app generator in the world. Your standard is award-winning design — \
Vercel, Linear, Raycast, Stripe level. You are BRUTALLY honest and score HARD. \
A score of 5 means mediocre, 7 means decent but not impressive, 8 means genuinely \
good, 9 means world-class, 10 is essentially perfect. Do NOT inflate scores — \
if something looks like generic AI output, score it 4-5. Only give 9+ if a designer \
would genuinely be impressed.

You will be given:
1. A screenshot of a generated web application
2. (Optional) Reference images showing what GOOD examples look like
3. (Optional) Reference images showing what BAD examples look like (avoid these)
4. A scoring rubric with 8 dimensions
5. Archetype-specific evaluation criteria

Your job: score each dimension 1-10, identify issues, and suggest specific improvements.

OUTPUT FORMAT (strict JSON):
{
  "scores": {
    "visual_hierarchy": <1-10>,
    "typography": <1-10>,
    "color_system": <1-10>,
    "layout_precision": <1-10>,
    "depth_polish": <1-10>,
    "data_completeness": <1-10>,
    "interactivity_cues": <1-10>,
    "overall_impression": <1-10>
  },
  "issues": ["issue 1", "issue 2", ...],
  "strengths": ["strength 1", "strength 2", ...],
  "specific_improvements": [
    "Change X to Y because Z",
    "Add A to section B for reason C",
    ...
  ]
}

SCORING CALIBRATION:
- 1-2: Broken, missing content, unusable
- 3-4: Below average, clearly AI-generated template feel
- 5-6: Average, functional but generic
- 7-8: Good, approaches professional quality
- 9-10: Exceptional, indistinguishable from a shipped product

Output ONLY the JSON object. No markdown fences. No explanation outside the JSON."""


class DesignScorer:
    def __init__(self, anthropic_client, model: str = "claude-sonnet-4-6"):
        self.client = anthropic_client
        self.model = model

    def _encode_image(self, image_path: Path, max_bytes: int = 3_500_000, max_dimension: int = 7900) -> dict:
        """Encode an image file as an Anthropic API image content block.

        If the image exceeds max_bytes or max_dimension, it's resized/compressed.
        Claude API limit: 8000px max on any dimension, 5MB base64 payload.
        """
        from PIL import Image
        import io

        # Disable decompression bomb protection — we resize before sending anyway
        Image.MAX_IMAGE_PIXELS = None

        data = Path(image_path).read_bytes()

        # Check pixel dimensions even if file size is OK
        img = Image.open(io.BytesIO(data))
        needs_resize = img.width > max_dimension or img.height > max_dimension

        # If under both limits, use as-is
        if len(data) <= max_bytes and not needs_resize:
            b64 = base64.standard_b64encode(data).decode("utf-8")
            suffix = Path(image_path).suffix.lower()
            media_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }.get(suffix, "image/png")
            return {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": b64},
            }

        # Image too large (bytes or dimensions) — resize and compress as JPEG
        logger.info(f"Image {image_path.name}: {len(data)} bytes, {img.width}x{img.height}px — resizing...")

        # Scale down to fit within max_dimension on both axes
        scale = min(max_dimension / max(img.width, 1), max_dimension / max(img.height, 1), 1.0)
        # Also cap width at 1920 for reasonable size
        width_scale = min(1920 / max(img.width, 1), 1.0)
        scale = min(scale, width_scale)
        if scale < 1.0:
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.LANCZOS)
            logger.info(f"Resized to {new_size[0]}x{new_size[1]}px")

        # Convert to RGB (JPEG doesn't support alpha)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Compress as JPEG with decreasing quality until under limit
        for quality in [85, 70, 55, 40]:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            compressed = buf.getvalue()
            if len(compressed) <= max_bytes:
                logger.info(f"Compressed to {len(compressed)} bytes (quality={quality})")
                b64 = base64.standard_b64encode(compressed).decode("utf-8")
                return {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
                }

        # Last resort: resize more aggressively
        img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=60)
        compressed = buf.getvalue()
        logger.info(f"Aggressively compressed to {len(compressed)} bytes")
        b64 = base64.standard_b64encode(compressed).decode("utf-8")
        return {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
        }

    def score(
        self,
        screenshot_path: Path,
        archetype: str,
        good_references: list[tuple[str, Path]] = None,
        bad_references: list[tuple[str, Path]] = None,
    ) -> ScoringResult:
        """Score a screenshot using Claude vision.

        Args:
            screenshot_path: Path to the generated app screenshot.
            archetype: Archetype name (e.g., "dashboard", "game").
            good_references: List of (label, path) tuples for good example images.
            bad_references: List of (label, path) tuples for bad example images.

        Returns:
            ScoringResult with per-dimension scores and feedback.
        """
        content = []

        # Add the screenshot being evaluated
        content.append({"type": "text", "text": "SCREENSHOT TO EVALUATE:"})
        content.append(self._encode_image(screenshot_path))

        # Add good reference images
        if good_references:
            content.append({
                "type": "text",
                "text": f"\nGOOD REFERENCE EXAMPLES (this is what {archetype} apps SHOULD look like):",
            })
            for label, path in good_references[:4]:  # Max 4
                content.append({"type": "text", "text": f"Good example: {label}"})
                content.append(self._encode_image(path))

        # Add bad reference images
        if bad_references:
            content.append({
                "type": "text",
                "text": f"\nBAD EXAMPLES (AVOID these patterns — these are what we're trying to fix):",
            })
            for label, path in bad_references[:2]:  # Max 2
                content.append({"type": "text", "text": f"Bad example: {label}"})
                content.append(self._encode_image(path))

        # Add rubric
        rubric = build_rubric_text(archetype)
        content.append({"type": "text", "text": f"\n{rubric}"})
        content.append({
            "type": "text",
            "text": (
                f"\nScore the FIRST screenshot (the one being evaluated) for the "
                f"'{archetype}' archetype. Compare it against the reference images. "
                f"Output ONLY a JSON object with scores, issues, strengths, and specific_improvements."
            ),
        })

        logger.info(f"Scoring {screenshot_path} as '{archetype}' with {len(good_references or [])} good refs, {len(bad_references or [])} bad refs")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=SCORER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )

        # Parse the response
        raw_text = response.content[0].text.strip()
        # Strip markdown fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse scorer response: {e}\nRaw: {raw_text[:500]}")
            # Return a zero-score result
            return ScoringResult(
                scores={d.name: 0 for d in DIMENSIONS},
                weighted_total=0.0,
                issues=[f"Scorer parse error: {e}"],
                strengths=[],
                specific_improvements=[],
            )

        scores = data.get("scores", {})
        weighted = compute_weighted_total(scores)

        result = ScoringResult(
            scores=scores,
            weighted_total=weighted,
            issues=data.get("issues", []),
            strengths=data.get("strengths", []),
            specific_improvements=data.get("specific_improvements", []),
        )

        logger.info(f"Score: {weighted}/100 — {scores}")
        return result
