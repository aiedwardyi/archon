"""
Claude-based prompt rewriter — takes scoring results and rewrites archetype sections.
"""

import json
import base64
import logging
from pathlib import Path

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
    def __init__(self, anthropic_client, model: str = "claude-sonnet-4-6"):
        self.client = anthropic_client
        self.model = model

    def _encode_image(self, image_path: Path, max_bytes: int = 4_500_000) -> dict:
        """Encode an image for the Anthropic API, compressing if over 5MB."""
        data = Path(image_path).read_bytes()

        if len(data) <= max_bytes:
            b64 = base64.standard_b64encode(data).decode("utf-8")
            suffix = Path(image_path).suffix.lower()
            media_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
            }.get(suffix, "image/png")
            return {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": b64},
            }

        from PIL import Image
        import io

        logger.info(f"Compressing {image_path.name} ({len(data)} bytes)")
        img = Image.open(io.BytesIO(data))
        if img.width > 1920:
            ratio = 1920 / img.width
            img = img.resize((1920, int(img.height * ratio)), Image.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        for quality in [85, 70, 55, 40]:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            if len(buf.getvalue()) <= max_bytes:
                b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
                return {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
                }

        img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=60)
        b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
        return {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
        }

    def improve(
        self,
        archetype: str,
        current_prompt: str,
        scores: dict,
        screenshot_path: Path = None,
        good_references: list[tuple[str, Path]] = None,
    ) -> str:
        """Rewrite an archetype prompt section to fix identified issues.

        Args:
            archetype: Archetype name.
            current_prompt: Current archetype section text from engineer.txt.
            scores: Scoring results dict (from ScoringResult.to_dict()).
            screenshot_path: Path to the screenshot that was scored.
            good_references: List of (label, path) for good example images.

        Returns:
            Rewritten archetype section text.
        """
        content = []

        # Show the current prompt
        content.append({
            "type": "text",
            "text": (
                f"CURRENT ARCHETYPE PROMPT SECTION (for '{archetype}'):\n"
                f"```\n{current_prompt}\n```"
            ),
        })

        # Show scoring results
        scores_text = json.dumps(scores, indent=2)
        content.append({
            "type": "text",
            "text": f"\nSCORING RESULTS FROM LATEST BUILD:\n{scores_text}",
        })

        # Show the screenshot that was scored
        if screenshot_path and Path(screenshot_path).exists():
            content.append({
                "type": "text",
                "text": "\nSCREENSHOT OF CURRENT OUTPUT (this is what the current prompt produces):",
            })
            content.append(self._encode_image(screenshot_path))

        # Show good reference images
        if good_references:
            content.append({
                "type": "text",
                "text": f"\nTARGET QUALITY — these are what GOOD {archetype} apps look like:",
            })
            for label, path in good_references[:3]:
                content.append({"type": "text", "text": f"Reference: {label}"})
                content.append(self._encode_image(path))

        # Instructions
        content.append({
            "type": "text",
            "text": (
                f"\nREWRITE the archetype prompt section above to fix the identified issues "
                f"and improve scores toward 80+. Focus especially on dimensions scoring below 7.\n\n"
                f"Key constraints:\n"
                f"- Keep the EXACT same header format (# ═══... / # ARCHETYPE N: NAME / # ═══...)\n"
                f"- Keep PATH designation (A or B) the same\n"
                f"- Be MORE specific with CSS values, data requirements, and layout geometry\n"
                f"- Add explicit anti-patterns to avoid\n"
                f"- Add explicit data seeding instructions (chart data points, table rows, KPI values)\n"
                f"- Reference the good examples when adding visual requirements\n"
                f"- Output ONLY the rewritten section text, nothing else"
            ),
        })

        logger.info(f"Improving prompt for '{archetype}' (current weighted score: {scores.get('weighted_total', '?')})")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            system=IMPROVER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )

        new_prompt = response.content[0].text.strip()

        # Strip markdown fences if the model wrapped them
        if new_prompt.startswith("```"):
            new_prompt = new_prompt.split("\n", 1)[1]
            if new_prompt.endswith("```"):
                new_prompt = new_prompt[:-3]
            new_prompt = new_prompt.strip()

        # Validate that it still has the header
        if "═══" not in new_prompt:
            logger.warning("Improved prompt missing header delimiters — prepending original header")
            # Extract header from current prompt
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
