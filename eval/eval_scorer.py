"""
Vision-based design scoring using Gemini API.
"""

import json
import logging
from pathlib import Path

from google import genai
from google.genai import types

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
    def __init__(self, genai_client, model: str = "gemini-2.5-flash"):
        self.client = genai_client
        self.model = model

    def _prepare_image(self, image_path: Path, max_dimension: int = 3072) -> types.Part:
        """Prepare an image as a Gemini inline_data Part, resizing if needed."""
        from PIL import Image
        import io

        Image.MAX_IMAGE_PIXELS = None

        img = Image.open(image_path)

        # Resize if too large
        if img.width > max_dimension or img.height > max_dimension:
            scale = min(max_dimension / max(img.width, 1), max_dimension / max(img.height, 1))
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
            logger.info(f"Resized {image_path.name} to {img.width}x{img.height}")

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        image_bytes = buf.getvalue()
        logger.info(f"Image {image_path.name}: {len(image_bytes)} bytes, {img.width}x{img.height}px")

        return types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

    def score(
        self,
        screenshot_path: Path,
        archetype: str,
        good_references: list[tuple[str, Path]] = None,
        bad_references: list[tuple[str, Path]] = None,
    ) -> ScoringResult:
        """Score a screenshot using Gemini vision."""
        contents = []

        # Add the screenshot being evaluated
        contents.append("SCREENSHOT TO EVALUATE:")
        contents.append(self._prepare_image(screenshot_path))

        # Add good reference images
        if good_references:
            contents.append(f"\nGOOD REFERENCE EXAMPLES (this is what {archetype} apps SHOULD look like):")
            for label, path in good_references[:4]:
                contents.append(f"Good example: {label}")
                contents.append(self._prepare_image(path))

        # Add bad reference images
        if bad_references:
            contents.append("\nBAD EXAMPLES (AVOID these patterns — these are what we're trying to fix):")
            for label, path in bad_references[:2]:
                contents.append(f"Bad example: {label}")
                contents.append(self._prepare_image(path))

        # Add rubric
        rubric = build_rubric_text(archetype)
        contents.append(f"\n{rubric}")
        contents.append(
            f"\nScore the FIRST screenshot (the one being evaluated) for the "
            f"'{archetype}' archetype. Compare it against the reference images. "
            f"Output ONLY a JSON object with scores, issues, strengths, and specific_improvements."
        )

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

        raw_text = (response.text or "").strip()

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
