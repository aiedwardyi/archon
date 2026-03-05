"""
Scoring rubric definitions — 8 dimensions with weights.
"""

from dataclasses import dataclass, field


@dataclass
class Dimension:
    name: str
    weight: float
    description: str
    evaluation_guide: str


DIMENSIONS = [
    Dimension(
        name="visual_hierarchy",
        weight=0.15,
        description="Visual Hierarchy",
        evaluation_guide=(
            "Clear focal points on each section. Size contrast between headings "
            "and body text (hero heading should be 3-5x larger). Intentional whitespace "
            "distribution — generous, never cramped. Eye flow guides the user naturally. "
            "One element per section demands attention; everything else supports it."
        ),
    ),
    Dimension(
        name="typography",
        weight=0.15,
        description="Typography",
        evaluation_guide=(
            "Custom fonts loaded (not system defaults like Arial/Times). Two distinct fonts: "
            "display font for headings + body font for content. Heading/body pairing feels "
            "intentional. Consistent type scale. Hero heading uses dramatic sizing "
            "(clamp or responsive). Letter-spacing on headings is tight. Line-height is "
            "comfortable for body text."
        ),
    ),
    Dimension(
        name="color_system",
        weight=0.15,
        description="Color System",
        evaluation_guide=(
            "Intentional palette — not random purple/blue (the AI default). Max 5 colors: "
            "background, surface, text, muted-text, accent. Accent used sparingly (max 10% "
            "of surface). Borders are subtle (not harsh). Gradients are purposeful, not "
            "rainbow. Background is never pure white or pure black. Colors match the domain "
            "(green for finance, blue for SaaS, etc)."
        ),
    ),
    Dimension(
        name="layout_precision",
        weight=0.15,
        description="Layout Precision",
        evaluation_guide=(
            "Grid alignment is consistent — elements line up vertically and horizontally. "
            "Spacing follows a scale (4/8/12/16/24/32/48px). Card grids have consistent gaps. "
            "Sidebar width is appropriate (200-260px for dashboards). Content density matches "
            "the archetype (compact for dashboards, spacious for landing pages). No overflow "
            "or layout breaks visible."
        ),
    ),
    Dimension(
        name="depth_polish",
        weight=0.10,
        description="Depth & Polish",
        evaluation_guide=(
            "Visual layers are apparent (background, surface, elevated elements). Glass/blur "
            "effects used where appropriate. Subtle shadows on elevated elements. Gradient "
            "borders on featured cards. Glow effects restrained (not neon everywhere). "
            "Noise/texture overlays for immersion (gaming). Overall feeling of craftsmanship "
            "rather than flatness."
        ),
    ),
    Dimension(
        name="data_completeness",
        weight=0.10,
        description="Data Completeness",
        evaluation_guide=(
            "Charts render with actual data (not empty SVGs or blank canvases). Tables have "
            "populated rows with realistic data. KPI cards show real numbers (not 0 or N/A). "
            "Lists have items. No blank/empty sections visible. The app looks like it has "
            "real data, not a skeleton or placeholder state. At least 5 rows in tables, "
            "6+ data points in charts."
        ),
    ),
    Dimension(
        name="interactivity_cues",
        weight=0.05,
        description="Interactivity Cues",
        evaluation_guide=(
            "Buttons have visible hover/active states. Navigation has an active indicator. "
            "Interactive elements look clickable (cursor, color, elevation). Form inputs "
            "have focus styles. Cards suggest clickability through hover effects. At least "
            "one working interaction visible (modal, toast, tab switch)."
        ),
    ),
    Dimension(
        name="overall_impression",
        weight=0.15,
        description="Overall Impression",
        evaluation_guide=(
            "Does this look like a shipped product or an AI-generated template? Would a "
            "designer be proud of this output? Does it feel cohesive and intentional? "
            "Is it distinct from generic AI output (no cookie-cutter sidebar+cards)? "
            "Compare against the reference images — does it reach that quality bar?"
        ),
    ),
]

# Archetype-specific evaluation criteria
ARCHETYPE_CRITERIA = {
    "dashboard": (
        "DASHBOARD-SPECIFIC:\n"
        "- Must have dark theme (bg-zinc-950 or similar dark background)\n"
        "- Sidebar should be fixed, ~220px, slightly lighter than main area\n"
        "- KPI cards must show actual numbers with delta badges (up/down indicators)\n"
        "- Chart MUST render with actual SVG paths/data — empty chart = score 1 on data_completeness\n"
        "- Data table must have 5+ rows with realistic data\n"
        "- Activity feed should have timestamped entries\n"
        "- Font should be Inter or similar clean sans-serif\n"
        "- Numbers should use tabular-nums alignment\n"
        "- Accent color should be contextual to domain (green for finance, blue for SaaS)\n"
        "- NO heavy neon glows — dashboards need subtle, professional depth"
    ),
    "game": (
        "GAME/FANPAGE-SPECIFIC:\n"
        "- Must feel cinematic and immersive, not like a generic website\n"
        "- Full-bleed hero with atmospheric background image\n"
        "- Character cards should have large portrait images with stats/info\n"
        "- Weapons/items section with detail art\n"
        "- Consistent neon accent (green for sci-fi, purple for fantasy)\n"
        "- Film grain / noise texture overlay for immersion\n"
        "- Dark theme mandatory (bg-zinc-950 or darker)\n"
        "- Layout should feel like a premium game companion site, NOT a blog\n"
        "- Character images should be recognizable and detailed"
    ),
    "saas_landing": (
        "SAAS LANDING PAGE-SPECIFIC:\n"
        "- Glassmorphism navigation bar\n"
        "- Gradient mesh or animated hero with announcement pill\n"
        "- Logo cloud section (partner/client logos)\n"
        "- Bento grid feature layout (not boring uniform cards)\n"
        "- Testimonials with real-looking avatars and quotes\n"
        "- Pricing section with toggle (monthly/annual)\n"
        "- FAQ accordion\n"
        "- CTA banner before footer\n"
        "- Full footer with 4-5 columns\n"
        "- Hero heading should be massive and compelling"
    ),
    "fintech": (
        "FINTECH/TRADING-SPECIFIC:\n"
        "- Dark theme mandatory (bg-zinc-950)\n"
        "- Green/red for gains/losses with clear semantic meaning\n"
        "- Monospace font on ALL numbers (JetBrains Mono or similar)\n"
        "- Sparkline SVGs in table rows\n"
        "- Candlestick-style or area chart with real data points\n"
        "- Ticker rows with live-feeling price data\n"
        "- Portfolio value prominent with delta\n"
        "- Professional, terminal-like aesthetic"
    ),
    "ecommerce": (
        "E-COMMERCE-SPECIFIC:\n"
        "- Product grid with high-quality images, consistent card sizing\n"
        "- Each product card: image, name, price, quick-add or wishlist action\n"
        "- Navigation: search icon, cart count badge, category links\n"
        "- Hero banner with featured collection or campaign imagery\n"
        "- Category pills or filter bar for browsing\n"
        "- Cart drawer or cart page with item list and totals\n"
        "- Luxury feel: generous whitespace, serif or elegant sans-serif headings\n"
        "- Product images should look premium (not placeholder boxes)\n"
        "- Footer with multiple columns (shop, about, support, social)\n"
        "- Price formatting consistent (currency symbol, decimals)\n"
        "- Hover effects on product cards (zoom, overlay, quick-view)"
    ),
    "portfolio": (
        "PORTFOLIO-SPECIFIC:\n"
        "- Dark theme with bold, distinctive typography (display font for headings)\n"
        "- Asymmetric or editorial layout — NOT a generic centered template\n"
        "- Hero section: large name/title, dramatic sizing (text-6xl to text-8xl)\n"
        "- Project gallery with large thumbnails and hover overlays\n"
        "- At least 3-6 portfolio projects visible with titles/descriptions\n"
        "- Skills or tech stack section with visual treatment\n"
        "- Contact section or CTA\n"
        "- Minimal, intentional color palette (max 2-3 colors)\n"
        "- Feels like a designer's personal site, NOT a resume template\n"
        "- Smooth transitions and micro-interactions on project cards"
    ),
}


@dataclass
class ScoringResult:
    scores: dict[str, float] = field(default_factory=dict)
    weighted_total: float = 0.0
    issues: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    specific_improvements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "scores": self.scores,
            "weighted_total": self.weighted_total,
            "issues": self.issues,
            "strengths": self.strengths,
            "specific_improvements": self.specific_improvements,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ScoringResult":
        return cls(
            scores=d.get("scores", {}),
            weighted_total=d.get("weighted_total", 0.0),
            issues=d.get("issues", []),
            strengths=d.get("strengths", []),
            specific_improvements=d.get("specific_improvements", []),
        )


def compute_weighted_total(scores: dict[str, float]) -> float:
    """Compute weighted total from per-dimension scores (each 1-10)."""
    total = 0.0
    for dim in DIMENSIONS:
        raw = scores.get(dim.name, 0)
        total += (raw / 10.0) * dim.weight * 100
    return round(total, 1)


def build_rubric_text(archetype: str = None) -> str:
    """Build the full rubric text for inclusion in a scoring prompt."""
    lines = ["SCORING RUBRIC — 8 Dimensions (each scored 1-10)\n"]
    for dim in DIMENSIONS:
        lines.append(f"## {dim.description} (weight: {dim.weight})")
        lines.append(dim.evaluation_guide)
        lines.append("")

    if archetype and archetype in ARCHETYPE_CRITERIA:
        lines.append("=" * 40)
        lines.append(ARCHETYPE_CRITERIA[archetype])

    lines.append("\nWEIGHTED SCORE: 0-100 scale. Pass: 70. Target: 80+.")
    return "\n".join(lines)
