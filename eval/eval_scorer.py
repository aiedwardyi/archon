"""
Vision-based design scoring using Gemini API.
"""

import json
import logging
from pathlib import Path

from google.genai import types as genai_types

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

OUTPUT FORMAT (strict JSON — scores MUST be integers, no decimals):
{
  "scores": {
    "visual_hierarchy": <integer 1-10>,
    "typography": <integer 1-10>,
    "color_system": <integer 1-10>,
    "layout_precision": <integer 1-10>,
    "depth_polish": <integer 1-10>,
    "data_completeness": <integer 1-10>,
    "interactivity_cues": <integer 1-10>,
    "overall_impression": <integer 1-10>
  },
  "issues": ["issue 1", "issue 2"],
  "strengths": ["strength 1", "strength 2"],
  "specific_improvements": ["improvement 1", "improvement 2"]
}

IMPORTANT: Keep lists SHORT (max 3 items each). Use INTEGER scores only (no 7.5, just 7 or 8).

SCORING CALIBRATION:
- 1-2: Broken, missing content, unusable
- 3-4: Below average, clearly AI-generated template feel
- 5-6: Average, functional but generic
- 7-8: Good, approaches professional quality
- 9-10: Exceptional, indistinguishable from a shipped product

Output ONLY the JSON object. No markdown fences. No explanation outside the JSON."""


class DesignScorer:
    def __init__(self, genai_client, model: str = "gemini-2.5-flash"):
        self.client = genai_client
        self.model = model

    def _prepare_image(self, image_path: Path, max_bytes: int = 3_500_000, max_dimension: int = 7900) -> genai_types.Part:
        """Prepare an image as a Gemini API Part, resizing if needed."""
        from PIL import Image
        import io

        Image.MAX_IMAGE_PIXELS = None

        data = Path(image_path).read_bytes()
        img = Image.open(io.BytesIO(data))
        needs_resize = img.width > max_dimension or img.height > max_dimension

        suffix = Path(image_path).suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }

        if len(data) <= max_bytes and not needs_resize:
            mime_type = mime_map.get(suffix, "image/png")
            return genai_types.Part.from_bytes(data=data, mime_type=mime_type)

        logger.info(f"Image {image_path.name}: {len(data)} bytes, {img.width}x{img.height}px — resizing...")

        scale = min(max_dimension / max(img.width, 1), max_dimension / max(img.height, 1), 1.0)
        width_scale = min(1920 / max(img.width, 1), 1.0)
        scale = min(scale, width_scale)
        if scale < 1.0:
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.LANCZOS)
            logger.info(f"Resized to {new_size[0]}x{new_size[1]}px")

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        for quality in [85, 70, 55, 40]:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            compressed = buf.getvalue()
            if len(compressed) <= max_bytes:
                logger.info(f"Compressed to {len(compressed)} bytes (quality={quality})")
                return genai_types.Part.from_bytes(data=compressed, mime_type="image/jpeg")

        img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=60)
        compressed = buf.getvalue()
        logger.info(f"Aggressively compressed to {len(compressed)} bytes")
        return genai_types.Part.from_bytes(data=compressed, mime_type="image/jpeg")

    def score(
        self,
        screenshot_path: Path,
        archetype: str,
        good_references: list[tuple[str, Path]] = None,
        bad_references: list[tuple[str, Path]] = None,
    ) -> ScoringResult:
        """Score a screenshot using Gemini vision.

        Args:
            screenshot_path: Path to the generated app screenshot.
            archetype: Archetype name (e.g., "dashboard", "game").
            good_references: List of (label, path) tuples for good example images.
            bad_references: List of (label, path) tuples for bad example images.

        Returns:
            ScoringResult with per-dimension scores and feedback.
        """
        contents = []

        contents.append(genai_types.Part.from_text(text="SCREENSHOT TO EVALUATE:"))
        contents.append(self._prepare_image(screenshot_path))

        if good_references:
            contents.append(genai_types.Part.from_text(text=
                f"\nGOOD REFERENCE EXAMPLES (this is what {archetype} apps SHOULD look like):"
            ))
            for label, path in good_references[:4]:
                contents.append(genai_types.Part.from_text(text=f"Good example: {label}"))
                contents.append(self._prepare_image(path))

        if bad_references:
            contents.append(genai_types.Part.from_text(text=
                "\nBAD EXAMPLES (AVOID these patterns — these are what we're trying to fix):"
            ))
            for label, path in bad_references[:2]:
                contents.append(genai_types.Part.from_text(text=f"Bad example: {label}"))
                contents.append(self._prepare_image(path))

        rubric = build_rubric_text(archetype)
        contents.append(genai_types.Part.from_text(text=f"\n{rubric}"))
        contents.append(genai_types.Part.from_text(text=
            f"\nScore the FIRST screenshot (the one being evaluated) for the "
            f"'{archetype}' archetype. Compare it against the reference images. "
            f"Output ONLY a JSON object with scores, issues, strengths, and specific_improvements."
        ))

        logger.info(f"Scoring {screenshot_path} as '{archetype}' with {len(good_references or [])} good refs, {len(bad_references or [])} bad refs")

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config={
                "system_instruction": SCORER_SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "temperature": 0.3,
                "max_output_tokens": 8000,
            },
        )

        raw_text = (getattr(response, "text", "") or "").strip()
        # Strip markdown fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            # Try to recover truncated JSON by extracting scores with regex
            logger.warning(f"JSON parse failed, attempting recovery: {e}")
            import re
            score_pattern = re.compile(r'"(\w+)":\s*([\d.]+)')
            matches = score_pattern.findall(raw_text)
            score_keys = {d.name for d in DIMENSIONS}
            extracted = {k: round(float(v)) for k, v in matches if k in score_keys}
            if len(extracted) >= 4:
                logger.info(f"Recovered {len(extracted)} scores from truncated JSON: {extracted}")
                data = {"scores": extracted, "issues": [], "strengths": [], "specific_improvements": []}
            else:
                logger.error(f"Failed to parse scorer response: {e}\nRaw: {raw_text[:500]}")
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
