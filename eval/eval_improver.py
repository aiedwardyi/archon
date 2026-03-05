"""
Gemini-based prompt rewriter — takes scoring results and rewrites archetype sections.
"""

import json
import logging
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

IMPROVER_SYSTEM_PROMPT = """\
You are an expert frontend design prompt engineer. You rewrite archetype prompt \
sections for a code-generation AI to produce higher-quality web application UIs.

You are working for a company that needs to be THE BEST web app generator in the world. \
Every prompt you write must produce output that a professional designer would be proud of. \
Your goal is to reach 90+/100 on our scoring rubric.

You understand:
- Award-winning web design principles (hierarchy, typography, color, micro-interactions)
- Modern SaaS dashboard patterns (Vercel, Linear, Raycast, Stripe level quality)
- Game/fan page patterns (immersive heroes, character showcases, cinematic feel)
- What separates AI-template output from shipped-product quality
- How to write prompts that produce SPECIFIC, DETAILED, UNIQUE output rather than generic templates

ANTI-PATTERNS TO ELIMINATE:
- Generic purple/blue gradients on every app
- Same sidebar+cards template regardless of domain
- Empty SVG charts / 0-value KPIs
- Light theme forced on dashboards (dark is standard for modern dashboards)
- Flat, lifeless layouts without depth or visual interest
- Cookie-cutter card grids with no variation

WHAT MAKES GREAT PROMPTS:
- Specific CSS values (exact colors, spacing, font sizes)
- Explicit data requirements ("chart MUST have 12 data points")
- Concrete layout geometry ("sidebar 220px, main gap-6")
- Named design patterns ("glassmorphism nav", "bento grid")
- Anti-instructions ("NEVER use X", "NO heavy glows")
- Reference to specific CSS techniques (gradient borders, backdrop-filter)

FORMAT REQUIREMENT:
Your output MUST follow the EXACT same format as the existing archetype sections:
```
# ═══════════════════════════════════════
# ARCHETYPE N: NAME
# ═══════════════════════════════════════

PATH: A or B (Tailwind or Raw CSS)
Use for: ...
Theme: ...
Fonts: ... (if applicable)
Rules: ... (if applicable)
MUST include: ...
```

Keep the archetype number and name header EXACTLY as provided.
Only modify the content BELOW the header delimiters.
Output ONLY the rewritten section. No explanation. No markdown fences."""


class PromptImprover:
    def __init__(self, genai_client, model: str = "gemini-2.5-flash"):
        self.client = genai_client
        self.model = model

    def _prepare_image(self, image_path: Path, max_dimension: int = 3072) -> types.Part:
        """Prepare an image as a Gemini inline_data Part, resizing if needed."""
        from PIL import Image
        import io

        Image.MAX_IMAGE_PIXELS = None

        img = Image.open(image_path)

        if img.width > max_dimension or img.height > max_dimension:
            scale = min(max_dimension / max(img.width, 1), max_dimension / max(img.height, 1))
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")

    def improve(
        self,
        archetype: str,
        current_prompt: str,
        scores: dict,
        screenshot_path: Path = None,
        good_references: list[tuple[str, Path]] = None,
    ) -> str:
        """Rewrite an archetype prompt section to fix identified issues."""
        contents = []

        # Show the current prompt
        contents.append(
            f"CURRENT ARCHETYPE PROMPT SECTION (for '{archetype}'):\n"
            f"```\n{current_prompt}\n```"
        )

        # Show scoring results
        scores_text = json.dumps(scores, indent=2)
        contents.append(f"\nSCORING RESULTS FROM LATEST BUILD:\n{scores_text}")

        # Show the screenshot that was scored
        if screenshot_path and Path(screenshot_path).exists():
            contents.append("\nSCREENSHOT OF CURRENT OUTPUT (this is what the current prompt produces):")
            contents.append(self._prepare_image(screenshot_path))

        # Show good reference images
        if good_references:
            contents.append(f"\nTARGET QUALITY — these are what GOOD {archetype} apps look like:")
            for label, path in good_references[:3]:
                contents.append(f"Reference: {label}")
                contents.append(self._prepare_image(path))

        # Identify weak and strong dimensions
        dim_scores = scores.get("scores", {})
        weak_dims = [d for d, s in dim_scores.items() if s <= 6]
        strong_dims = [d for d, s in dim_scores.items() if s >= 8]

        contents.append(
            f"\nREWRITE the archetype prompt section above to fix the identified issues "
            f"and improve scores toward 90+. Focus especially on dimensions scoring below 7.\n\n"
            f"WEAK dimensions (score <= 6, MUST improve): {', '.join(weak_dims) if weak_dims else 'none'}\n"
            f"STRONG dimensions (score >= 8, PRESERVE these): {', '.join(strong_dims) if strong_dims else 'none'}\n\n"
            f"CRITICAL RULES:\n"
            f"- PRESERVE instructions that produce high-scoring dimensions (8+) — do NOT remove or weaken them\n"
            f"- Make SURGICAL additions for weak dimensions — add 2-3 specific new instructions per weak dimension\n"
            f"- Do NOT rewrite instructions that are already producing good results\n"
            f"- Keep the EXACT same header format (# ═══... / # ARCHETYPE N: NAME / # ═══...)\n"
            f"- Keep PATH designation (A or B) the same\n"
            f"- Be MORE specific with CSS values, data requirements, and layout geometry\n"
            f"- Add explicit anti-patterns to avoid\n"
            f"- Add explicit data seeding instructions (chart data points, table rows, KPI values)\n"
            f"- Reference the good examples when adding visual requirements\n"
            f"- Output ONLY the rewritten section text, nothing else"
        )

        logger.info(f"Improving prompt for '{archetype}' (current weighted score: {scores.get('weighted_total', '?')})")

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config={
                "system_instruction": IMPROVER_SYSTEM_PROMPT,
                "temperature": 0.7,
                "max_output_tokens": 3000,
            },
        )

        new_prompt = (response.text or "").strip()

        # Strip markdown fences if the model wrapped them
        if new_prompt.startswith("```"):
            new_prompt = new_prompt.split("\n", 1)[1]
            if new_prompt.endswith("```"):
                new_prompt = new_prompt[:-3]
            new_prompt = new_prompt.strip()

        # Validate that it still has the header
        if "═══" not in new_prompt:
            logger.warning("Improved prompt missing header delimiters — prepending original header")
            lines = current_prompt.split("\n")
            header_lines = []
            for line in lines:
                header_lines.append(line)
                if line.startswith("# ═") and len(header_lines) >= 3:
                    break
            header = "\n".join(header_lines)
            new_prompt = header + "\n\n" + new_prompt

        logger.info(f"Improved prompt generated ({len(new_prompt)} chars)")
        return new_prompt
