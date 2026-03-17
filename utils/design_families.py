from __future__ import annotations

DESIGN_KIT_ALIASES = {
    "ai_product": "saas_landing",
    "dev_tool": "saas_landing",
    "productivity_app": "saas_landing",
    "game_companion": "game",
    "fan_page": "game",
    "game_ff7": "game",
    "game_ff8": "game",
    "game_ff9": "game",
    "interactive_experience": "game",
    "admin_panel": "dashboard",
    "analytics": "dashboard",
    "crm": "dashboard",
    "online_store": "ecommerce",
    "marketplace": "ecommerce",
    "shop": "ecommerce",
    "agency": "portfolio",
    "personal_site": "portfolio",
    "freelancer": "portfolio",
}

GLOBAL_FAMILY_LAYER_EXEMPT_CANONICAL_ARCHETYPES = {
    "game",
}


def canonicalize_design_archetype(ui_archetype: str | None) -> str | None:
    normalized = (ui_archetype or "").strip().lower()
    if not normalized:
        return None
    return DESIGN_KIT_ALIASES.get(normalized, normalized)


def should_apply_componentized_global_family_layer(ui_archetype: str | None) -> bool:
    canonical = canonicalize_design_archetype(ui_archetype)
    if not canonical:
        return True
    return canonical not in GLOBAL_FAMILY_LAYER_EXEMPT_CANONICAL_ARCHETYPES


def resolve_componentized_design_family(ui_archetype: str | None) -> str:
    canonical = canonicalize_design_archetype(ui_archetype)
    if canonical in {"dashboard", "fintech"}:
        return "data_dense"
    if canonical in {"editor", "kanban", "chat"}:
        return "workspace"
    if canonical == "form":
        return "guided_flow"
    if canonical == "ecommerce":
        return "commerce"
    if canonical in {
        "portfolio",
        "game",
        "photography",
        "travel",
        "wedding",
        "restaurant",
        "music",
        "fitness",
        "real_estate",
    }:
        return "showcase"
    return "marketing"


def build_componentized_design_family_guidance(ui_archetype: str | None) -> str:
    canonical = canonicalize_design_archetype(ui_archetype) or "general"
    if not should_apply_componentized_global_family_layer(canonical):
        return ""
    family = resolve_componentized_design_family(canonical)

    lines = [
        f"design_family: {family}",
        f"canonical_archetype: {canonical}",
        "UNIVERSAL COMPONENTIZED APP CONTRACT:",
        "- Ship a real React app shell with a clear header/nav/main hierarchy, responsive breakpoints, and no dead empty columns.",
        "- Use a small, repeatable surface system. Prefer 3-4 deliberate panel/card treatments over many unrelated wrappers.",
        "- Do not let the whole app collapse into one default sans stack. When the family calls for type roles, make display, UI, and mono treatments explicit from the first render.",
        "- Every primary CTA, tab, filter, or step control must show hover, focus-visible, and active state treatment.",
        "- Do not leak instructions or prose notes into source code. If helper notes are needed, keep them as valid comments only.",
        "- Do not place raw object literals or brace-heavy code samples directly into JSX text nodes. Render code examples as strings or escaped literals.",
        "- Prefer local assets, inline SVG, gradients, initials, or generated placeholders over remote placeholder imagery.",
    ]

    family_rules = {
        "data_dense": [
            "- Organize the desktop layout around one dominant center insight zone plus subordinate support modules, not a flat grid of equivalent cards.",
            "- Treat typography as structural, not decorative: use a display face for page and section headings, a compact UI sans for controls/body copy, and a mono/tabular numeric face for every KPI, price, delta, holding, timestamp, and axis label.",
            "- Support rails need real weight: watchlist, alerts, activity, news, or secondary analysis should occupy a meaningful lane with at least two clearly separated modules instead of one thin afterthought card.",
            "- Reject boilerplate dense-shell copy: do not ship bland headings like `Dashboard Overview` or equally generic panel titles unless the prompt literally asks for that wording.",
            "- Row actions must be domain-specific. Do not repeat the same generic `View` / `Details` verb on every row when the product should offer workflow-specific next actions.",
            "- Support rails need authored language too: avoid thin filler modules named only `Watchlist`, `Activity`, or `Recent Updates` unless their entries, labels, and status cues make them feel product-specific.",
            "- Avoid generic admin defaults such as equal-height card mosaics, flat charcoal panels, or body-copy numerics that make the shell read like a template.",
        ],
        "workspace": [
            "- Default to a three-zone shell: navigation/context rail, primary work surface, and support rail or inspector.",
            "- Toolbars, tabs, composer controls, and side panels should feel like one authored workspace rather than generic stacked cards.",
            "- Keep panel hierarchy legible through depth, tint, border, and typography differences so the workspace does not collapse into one flat canvas.",
        ],
        "guided_flow": [
            "- Default to a wizard or staged flow with clear progress, back/continue controls, validation states, and a meaningful review or success step.",
            "- Keep the active step visually dominant while secondary guidance, summaries, or trust signals live in a side panel or footer band.",
            "- Inputs, toggles, summaries, and validation messages must feel connected to the current step, not scattered across unrelated cards.",
        ],
        "commerce": [
            "- Keep one clear campaign narrative: hero, merch grouping, product grid, and cart or quick-add behavior should feel like the same storefront.",
            "- Emphasize imagery, pricing, availability, and purchase affordances without drifting into SaaS-style dashboard chrome.",
            "- Collection and product cards need purposeful hover states, stable image treatment, and clear quick actions.",
        ],
        "showcase": [
            "- Build around a strong hero or lead story, then alternate supporting sections with noticeably different pacing and scale.",
            "- Prioritize visual identity, memorable section rhythm, and authored transitions over dense enterprise UI patterns.",
            "- Keep supporting modules coherent with the hero art direction instead of mixing unrelated card languages.",
        ],
        "marketing": [
            "- Keep the shell anchored on a strong hero, one or two proof sections, and a clear CTA path instead of many shallow sections.",
            "- Typography, spacing, and accent usage should create a distinct brand voice before adding extra decorative UI.",
            "- Avoid dashboard-style density unless the brief explicitly asks for a tool or data product shell.",
        ],
    }

    lines.append("FAMILY-SPECIFIC TARGETS:")
    lines.extend(family_rules.get(family, family_rules["marketing"]))
    return "\n".join(lines)


def build_componentized_shell_family_guidance(ui_archetype: str | None) -> str:
    if not should_apply_componentized_global_family_layer(ui_archetype):
        return ""
    family = resolve_componentized_design_family(ui_archetype)
    guidance = {
        "data_dense": (
            "- Structure the shell around one dominant insight zone plus clearly subordinate support modules.\n"
            "- Treat display-vs-UI-vs-mono typography roles as mandatory and keep tabular/mono numerics consistent across KPIs, prices, table cells, delta chips, timestamps, and chart labels.\n"
            "- Keep the center insight surface visibly larger than the support rail so the page does not collapse into equal-width panels.\n"
            "- Reject lazy dense-shell copy such as `Dashboard Overview`, repeated `View` / `Details` row actions, and thin generic `Watchlist` / `Activity` rails that do not feel authored for the product.\n"
            "- Preserve visible hover/focus treatment on rails, pills, rows, and actions. Dense shells should still feel touchable.\n"
        ),
        "workspace": (
            "- Keep the desktop shell legible as a workspace: left context rail, primary working surface, and one support rail or inspector.\n"
            "- Differentiate toolbars, sidebars, canvases, and inspectors with meaningful surface depth instead of one flat panel color.\n"
            "- The main work surface should visually dominate while support panels still feel intentional and populated.\n"
        ),
        "guided_flow": (
            "- Keep the flow visibly step-based with clear progression, current-step emphasis, and believable back/continue/review controls.\n"
            "- Pair the active form area with contextual guidance, summary, trust, or validation feedback so the page does not read like a plain form stack.\n"
            "- Inputs, option cards, and status messaging need one cohesive hierarchy with strong focus and error states.\n"
        ),
        "commerce": (
            "- Keep the storefront editorial and product-led rather than collapsing into generic marketing panels.\n"
            "- Collection cards and product cards should have clear depth, consistent imagery treatment, and polished quick actions.\n"
            "- Pricing, badges, and cart controls need immediate visual hierarchy and interaction feedback.\n"
        ),
        "showcase": (
            "- Preserve a strong hero-to-supporting-section rhythm with obvious scale changes and authored transitions.\n"
            "- Use surface, typography, and motion restraint so the shell feels branded rather than template-generic.\n"
            "- Supporting sections should inherit the hero art direction instead of switching to default dashboard card language.\n"
        ),
        "marketing": (
            "- Keep a decisive hero, a short proof path, and a clear CTA hierarchy.\n"
            "- Use typography, spacing, and accent depth to create a brand voice before adding more sections.\n"
            "- Avoid empty decorative panels or placeholder modules that do not support the conversion narrative.\n"
        ),
    }
    return guidance.get(family, guidance["marketing"])
