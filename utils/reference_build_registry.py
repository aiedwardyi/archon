from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS_PATH = ROOT / "eval" / "archetype_benchmarks.json"
GENERATED_DIR = ROOT / "generated"
PUBLISHED_DIR = ROOT / "published"

BENCHMARK_VARIANT_RULES: dict[str, dict[str, Any]] = {
    "game_ff7": {
        "base_archetype": "game",
        "include_any": [
            "final fantasy vii",
            "final fantasy 7",
            "ff7",
            "midgar",
            "avalanche",
            "cloud",
            "tifa",
            "barret",
            "barrett",
            "aerith",
            "sephiroth",
        ],
        "exclude_any": [
            "final fantasy viii",
            "ff8",
            "squall",
            "rinoa",
            "zell",
            "final fantasy ix",
            "ff9",
            "zidane",
            "vivi",
            "garnet",
            "pokemon",
            "digimon",
        ],
    },
    "game_ff8": {
        "base_archetype": "game",
        "include_any": [
            "final fantasy viii",
            "final fantasy 8",
            "ff8",
            "squall",
            "rinoa",
            "zell",
            "seed",
            "balamb",
            "gunblade",
        ],
        "exclude_any": [
            "final fantasy vii",
            "ff7",
            "midgar",
            "cloud",
            "tifa",
            "barret",
            "final fantasy ix",
            "ff9",
            "zidane",
            "vivi",
            "garnet",
            "pokemon",
            "digimon",
        ],
    },
    "game_ff9": {
        "base_archetype": "game",
        "include_any": [
            "final fantasy ix",
            "final fantasy 9",
            "ff9",
            "zidane",
            "vivi",
            "garnet",
            "alexandria",
            "gaia",
            "black mage",
        ],
        "exclude_any": [
            "final fantasy vii",
            "ff7",
            "midgar",
            "cloud",
            "tifa",
            "barret",
            "final fantasy viii",
            "ff8",
            "squall",
            "rinoa",
            "zell",
            "pokemon",
            "digimon",
        ],
    },
}

DEFAULT_STYLE_FAMILY_BY_ARCHETYPE: dict[str, str] = {
    "dashboard": "operator_console_workspace",
    "editor": "editorial_workspace",
    "fintech": "market_terminal_workspace",
    "form": "guided_setup_wizard",
    "crm": "operator_console_workspace",
    "analytics": "operator_console_workspace",
    "admin_panel": "operator_console_workspace",
}

STYLE_FAMILY_LIBRARY: dict[str, dict[str, Any]] = {
    "operator_console_workspace": {
        "archetypes": {"dashboard", "crm", "analytics", "admin_panel", "productivity_app", "ai_product"},
        "keywords": [
            "operations control center",
            "command center",
            "control tower",
            "serious professional workspace",
            "pipeline stages",
            "deal room",
            "revenue workspace",
            "exception queue",
            "dispatch alerts",
            "desktop-first",
            "high-density workspace",
        ],
        "description": (
            "Use an operator-console shell: a serious desktop-first workspace with a dominant primary board/chart/table, "
            "dense status modules, and a support rail for alerts, queues, or actions instead of a soft generic KPI dashboard."
        ),
        "guidance_lines": [
            "Keep one dominant working surface in view, then support it with compact status, alert, and action modules rather than symmetrical card grids.",
            "Make the shell feel operational and hands-on with visible queues, incidents, tasks, or transitions instead of static executive-summary filler.",
            "Use disciplined density, compact labels, and an active support rail so the product reads like a live console rather than a brochure admin page.",
        ],
    },
    "editorial_workspace": {
        "archetypes": {"editor", "productivity_app"},
        "keywords": [
            "document editor",
            "product brief",
            "brief editor",
            "inline comments",
            "publish controls",
            "document outline",
            "editorial workspace",
            "collaborative writing",
            "knowledge base",
        ],
        "description": (
            "Use an editorial workspace shell: a structurally integrated topbar, a visible three-panel layout, "
            "a dominant document canvas, and inspector/comment states that feel like a premium collaborative tool."
        ),
        "guidance_lines": [
            "Keep the desktop shell visibly multi-panel, with the center canvas dominant and both side rails populated.",
            "Anchor the shell with a real topbar that exposes save, publish, review, or collaborator state instead of a floating generic toolbar.",
            "Favor editorial title drama, clear publish/save state, and real collaboration cues over dashboard-style KPI filler.",
            "Use specific outline rows, comment subjects, and inspector cards instead of plain `Workspace`, `Notes`, or `Inspector` filler.",
            "Use layered chrome and restrained accent states so the workspace feels productized instead of like a beige print preview.",
        ],
    },
    "product_builder_workspace": {
        "archetypes": {"editor", "ai_product", "productivity_app", "dashboard"},
        "keywords": [
            "app builder",
            "builder workspace",
            "startup builder",
            "design assistant",
            "product builder",
            "founder workspace",
            "workspace builder",
            "ai web design assistant",
        ],
        "description": (
            "Use a product-builder workspace shell: dense multi-panel control surfaces, a strong central builder area, "
            "integrated onboarding or setup cues, and status modules that make the app feel like a serious product tool."
        ),
        "guidance_lines": [
            "Frame the experience like a premium builder workspace with a real top toolbar and visible control rails, not a flat landing page or generic dashboard.",
            "Blend builder controls, setup progress, status, and preview/review context into one cohesive shell so the UI feels actively usable at first glance.",
            "Keep the main work area dominant, but support it with dense inspector and summary modules rather than empty side chrome.",
            "Populate the side rails with specific layers, prompts, runs, launch blockers, or QA notes instead of generic `Workspace` / `Notes` filler.",
        ],
    },
    "guided_setup_wizard": {
        "archetypes": {"form", "ai_product", "dev_tool", "productivity_app"},
        "keywords": [
            "onboarding wizard",
            "setup wizard",
            "launch wizard",
            "plan selection",
            "workspace details",
            "integrations",
            "validation",
            "success state",
            "configuration flow",
        ],
        "description": (
            "Use a guided setup shell: a substantial split wizard layout, explicit progress states, grouped configuration panels, "
            "and compact validation or success surfaces that make the flow feel alive."
        ),
        "guidance_lines": [
            "Keep the desktop shell split and productized, with a substantial progress rail and a dominant active-step panel.",
            "Use real progression cues like validation, readiness, blocker, or confirmation states instead of a stack of generic form rows.",
            "Group the main step into clear sections and keep any review or result preview connected to the same flow rather than tacked on below.",
            "Keep one compact blocker/readiness/review card visible so the setup state is legible before submission.",
        ],
    },
    "market_terminal_workspace": {
        "archetypes": {"fintech", "dashboard", "crypto"},
        "keywords": [
            "trading terminal",
            "market chart",
            "watchlist",
            "ticker",
            "order actions",
            "order book",
            "portfolio breakdown",
            "brokerage",
            "market overview",
            "recent trades",
            "treasury operations terminal",
            "cash positions",
            "fx exposure",
            "settlement queue",
            "funding windows",
            "liquidity",
        ],
        "description": (
            "Use a market-terminal shell: dense navigation, chart-first composition, disciplined monospace numeric rhythm, "
            "and clearly actionable trading or watchlist surfaces instead of a generic admin dashboard."
        ),
        "guidance_lines": [
            "Lead with a chart-first shell, visible market controls, and compact data density rather than oversized decorative cards.",
            "Make prices, deltas, and table numerics feel precise with a disciplined mono rhythm and clear positive/negative state treatment.",
            "Use a support rail for watchlist, trades, or market context so the workspace feels like a live terminal, not a brochure dashboard.",
        ],
    },
    "cinematic_collector_fanpage": {
        "archetypes": {"game", "game_ff7", "game_ff8", "game_ff9"},
        "keywords": [
            "fan page",
            "fan site",
            "tribute",
            "archive",
            "collector",
            "cinematic",
            "premium",
            "aesthetic",
            "world map",
            "weapons",
            "character profiles",
            "hero art",
            "lore",
            "digimon",
            "final fantasy",
            "anime",
        ],
        "description": (
            "Use a collector-edition fan-page shell: full-bleed hero media, rounded glass-dark cards, "
            "tight uppercase micro-labels, premium button chrome, hover lifts, animated stat bars, "
            "and content sections that feel like a cinematic archive rather than a generic game landing page."
        ),
        "guidance_lines": [
            "Borrow a cinematic collector shell: full-bleed hero art, sparse top chrome, and layered atmospheric overlays.",
            "Use smooth rounded cards and premium button chrome with restrained glow instead of noisy gradients.",
            "Favor dense franchise modules: character dossiers, weapon panels, world maps, lore quotes, and modal detail reveals.",
            "Make motion feel curated: hover lifts, staged reveals, animated stat bars, and spotlight interactions.",
        ],
    },
    "playful_character_showcase": {
        "archetypes": {"game"},
        "keywords": [
            "pokemon",
            "starter",
            "mascot",
            "cute",
            "kids",
            "playful",
            "colorful",
        ],
        "description": (
            "Use a brighter character-showcase shell: playful color blocking, friendly rounded cards, "
            "clean collector-card rhythm, and motion that feels charming rather than cinematic."
        ),
        "guidance_lines": [
            "Use a brighter collector-card shell with strong character color-coding and approachable rounded surfaces.",
            "Keep the layout premium and polished, but let the palette and motion feel warmer and more playful.",
            "Emphasize character cards, evolution ladders, and spotlight interactions over dark lore panels.",
        ],
    },
}

DOMAIN_OVERLAY_LIBRARY: dict[str, dict[str, Any]] = {
    "operations_control_tower": {
        "archetypes": {"dashboard", "analytics", "admin_panel", "productivity_app", "ai_product"},
        "style_families": {"operator_console_workspace"},
        "keywords": [
            "logistics",
            "fleet status",
            "route delays",
            "shipment exceptions",
            "dispatch alerts",
            "control tower",
            "dispatch",
            "warehouse",
            "delivery",
            "sla breach",
            "incident feed",
        ],
        "description": (
            "Shape the workspace like an operations control tower: route health, exception queues, dispatch decisions, and live network status "
            "should be more prominent than generic business KPIs."
        ),
        "guidance_lines": [
            "Use route health, shipment exceptions, depot or fleet state, and dispatch actions as first-class modules.",
            "Favor incident urgency, SLA risk, and operational feeds over revenue or generic admin summaries.",
            "Include at least one operational control surface such as a dispatch queue, route board, lane table, or exception panel.",
            "Use workflow verbs like reroute, assign, escalate, acknowledge, or resolve instead of generic `View` / `Details` row actions.",
            "Keep the support rail centered on live alerts, SLA pressure, depot load, or dispatch ownership rather than generic activity filler.",
        ],
    },
    "sales_deal_room": {
        "archetypes": {"dashboard", "crm", "analytics", "productivity_app", "ai_product"},
        "style_families": {"operator_console_workspace"},
        "keywords": [
            "sales workspace",
            "deal room",
            "account executive",
            "pipeline stages",
            "call notes",
            "next actions",
            "deal risks",
            "revenue workspace",
            "forecast",
            "opportunity",
            "renewal",
        ],
        "description": (
            "Shape the workspace like a live deal room: stage movement, next steps, stakeholder notes, and risk/champion context "
            "should feel central instead of buried under generic dashboard chrome."
        ),
        "guidance_lines": [
            "Keep pipeline state, forecast pressure, and deal-level next actions visibly connected in one workspace.",
            "Use call notes, stakeholder context, mutual action plans, or risk flags so the UI feels like active deal execution.",
            "Favor stage boards, account timelines, and opportunity tables over generic operations or finance widgets.",
            "Use verbs like log call, send recap, pull in exec sponsor, update MAP, or advance stage instead of generic row actions.",
            "Support rails should carry champion health, renewal risk, or next-meeting prep rather than generic activity cards.",
        ],
    },
    "treasury_liquidity_terminal": {
        "archetypes": {"dashboard", "fintech", "analytics", "crypto"},
        "style_families": {"market_terminal_workspace"},
        "keywords": [
            "treasury",
            "cash positions",
            "fx exposure",
            "settlement queues",
            "settlement queue",
            "funding windows",
            "liquidity",
            "bank balances",
            "counterparty",
            "wire queue",
        ],
        "description": (
            "Shape the workspace like a treasury terminal: liquidity, settlement pressure, funding windows, and bank exposures "
            "should drive the composition instead of a generic market or SaaS dashboard."
        ),
        "guidance_lines": [
            "Lead with cash positions, funding readiness, settlement queues, and bank or counterparty exposure surfaces.",
            "Use treasury artifacts like ladders, cut-off windows, entity balances, and exception queues rather than simple watchlists.",
            "Keep the numeric treatment disciplined and finance-native, but tie it to treasury operations instead of retail trading cues.",
            "On desktop, keep a true multi-zone terminal shell with navigation, a dominant treasury work area, and a visible support rail rather than stacking everything into one narrow column.",
            "Use treasury operator verbs like release, hold, fund, reroute, or hedge on real payment, liquidity, or exposure objects.",
            "Keep the support rail focused on cut-off alerts, counterparty pressure, and funding deadlines rather than generic news filler.",
        ],
    },
}

BENCHMARK_STYLE_FAMILIES: dict[str, tuple[str, ...]] = {
    "legacy-briefai-product-brief-editor": ("editorial_workspace",),
    "legacy-designai-startup-builder": ("product_builder_workspace",),
    "legacy-ai-automation-onboarding-wizard": ("guided_setup_wizard",),
    "legacy-pyrunner-python-configurator": ("guided_setup_wizard",),
    "legacy-tradeflow-terminal-fintech": ("market_terminal_workspace",),
    "legacy-stocktrack-live-terminal": ("market_terminal_workspace",),
    "branch-ff8-garden-archive-20260316": ("cinematic_collector_fanpage",),
    "legacy-pokemon-starters-fan-page": ("playful_character_showcase",),
    "legacy-digimon-agumon-fan-page": ("cinematic_collector_fanpage",),
    "legacy-zell-dincht-fan-page": ("cinematic_collector_fanpage",),
    "legacy-ff8-seed-operatives-fan-page": ("cinematic_collector_fanpage",),
    "legacy-return-to-midgar-archive": ("cinematic_collector_fanpage",),
    "legacy-ff7-avalanche-archive": ("cinematic_collector_fanpage",),
    "legacy-ff7-midgar-archives": ("cinematic_collector_fanpage",),
    "legacy-ff7-legends-of-midgar": ("cinematic_collector_fanpage",),
    "legacy-ff9-zidane-vivi-tribute": ("cinematic_collector_fanpage",),
}

STYLE_FAMILY_ENTRY_BOOSTS: dict[str, dict[str, int]] = {
    "editorial_workspace": {
        "legacy-briefai-product-brief-editor": 12,
    },
    "product_builder_workspace": {
        "legacy-designai-startup-builder": 14,
    },
    "guided_setup_wizard": {
        "legacy-ai-automation-onboarding-wizard": 12,
        "legacy-pyrunner-python-configurator": 6,
    },
    "market_terminal_workspace": {
        "legacy-tradeflow-terminal-fintech": 12,
        "legacy-stocktrack-live-terminal": 6,
    },
    "cinematic_collector_fanpage": {
        "branch-ff8-garden-archive-20260316": 14,
        "legacy-ff7-legends-of-midgar": 12,
        "legacy-ff7-avalanche-archive": 10,
        "legacy-ff8-seed-operatives-fan-page": 9,
        "legacy-return-to-midgar-archive": 8,
        "legacy-digimon-agumon-fan-page": 7,
        "legacy-ff9-zidane-vivi-tribute": 6,
        "legacy-zell-dincht-fan-page": 5,
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_archetype_name(archetype: str | None) -> str:
    return str(archetype or "").strip().lower()


def _entry_search_text(entry: dict[str, Any]) -> str:
    parts: list[str] = [
        str(entry.get("label", "")),
        str(entry.get("benchmark_path", "")),
        str(entry.get("prompt_summary", "")),
        str(entry.get("notes", "")),
    ]
    hints = entry.get("prompt_hints", [])
    if isinstance(hints, list):
        parts.extend(str(hint) for hint in hints if isinstance(hint, str))
    return " ".join(parts).strip().lower()


def _contains_registry_token(haystack: str, token: str) -> bool:
    normalized_haystack = str(haystack or "").strip().lower()
    normalized_token = str(token or "").strip().lower()
    if not normalized_haystack or not normalized_token:
        return False
    pattern = re.compile(rf"(?<![a-z0-9]){re.escape(normalized_token)}(?![a-z0-9])")
    return bool(pattern.search(normalized_haystack))


def _entry_matches_variant(entry: dict[str, Any], archetype: str) -> bool:
    variant = BENCHMARK_VARIANT_RULES.get(_normalize_archetype_name(archetype))
    if not variant:
        return False
    if _normalize_archetype_name(entry.get("archetype")) != variant["base_archetype"]:
        return False

    haystack = _entry_search_text(entry)
    include_any = variant.get("include_any", [])
    exclude_any = variant.get("exclude_any", [])
    if include_any and not any(_contains_registry_token(haystack, token) for token in include_any):
        return False
    if exclude_any and any(_contains_registry_token(haystack, token) for token in exclude_any):
        return False
    return True


def _entry_style_families(entry: dict[str, Any]) -> tuple[str, ...]:
    label = str(entry.get("label", "")).strip().lower()
    families = list(BENCHMARK_STYLE_FAMILIES.get(label, ()))
    archetype = _normalize_archetype_name(entry.get("archetype"))
    if archetype in {"game_ff7", "game_ff8", "game_ff9"} and "cinematic_collector_fanpage" not in families:
        families.append("cinematic_collector_fanpage")
    return tuple(dict.fromkeys(families))


def _entry_matches_style_family(entry: dict[str, Any], family: str, archetype: str | None = None) -> bool:
    normalized_family = str(family or "").strip().lower()
    if not normalized_family:
        return False
    family_meta = STYLE_FAMILY_LIBRARY.get(normalized_family)
    if not family_meta:
        return False
    normalized_archetype = _normalize_archetype_name(archetype)
    base_archetype = _normalize_archetype_name(entry.get("archetype"))
    allowed_archetypes = {str(item).strip().lower() for item in family_meta.get("archetypes", set())}
    if normalized_archetype:
        if normalized_archetype not in allowed_archetypes and base_archetype not in allowed_archetypes:
            return False
    elif base_archetype not in allowed_archetypes:
        return False
    return normalized_family in _entry_style_families(entry)


def _infer_variant_archetype(prompt_text: str, entry: dict[str, Any] | None = None) -> str | None:
    haystacks = [prompt_text.strip().lower()]
    if entry:
        haystacks.append(_entry_search_text(entry))
    for archetype in BENCHMARK_VARIANT_RULES:
        for haystack in haystacks:
            if not haystack:
                continue
            if _entry_matches_variant(
                {
                    "archetype": BENCHMARK_VARIANT_RULES[archetype]["base_archetype"],
                    "prompt_summary": haystack,
                },
                archetype,
            ):
                return archetype
    return None


def infer_style_family(archetype: str | None, prompt_text: str | None = None) -> str | None:
    normalized_archetype = _normalize_archetype_name(archetype)
    prompt_lower = str(prompt_text or "").strip().lower()
    if not normalized_archetype:
        return None

    if normalized_archetype in {"game_ff7", "game_ff8", "game_ff9"}:
        return "cinematic_collector_fanpage"

    candidate_families: list[str] = []
    for family, meta in STYLE_FAMILY_LIBRARY.items():
        allowed_archetypes = {str(item).strip().lower() for item in meta.get("archetypes", set())}
        if normalized_archetype in allowed_archetypes:
            candidate_families.append(family)
    if not candidate_families:
        return None

    scored: list[tuple[int, str]] = []
    for family in candidate_families:
        keywords = [str(token).strip().lower() for token in STYLE_FAMILY_LIBRARY[family].get("keywords", [])]
        score = sum(1 for token in keywords if token and token in prompt_lower)
        if score > 0:
            scored.append((score, family))

    if scored:
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1]

    default_family = DEFAULT_STYLE_FAMILY_BY_ARCHETYPE.get(normalized_archetype)
    if default_family:
        return default_family

    if normalized_archetype == "game" and prompt_lower:
        return "cinematic_collector_fanpage"
    return None


def infer_domain_overlay(
    archetype: str | None,
    prompt_text: str | None = None,
    *,
    style_family: str | None = None,
) -> str | None:
    normalized_archetype = _normalize_archetype_name(archetype)
    prompt_lower = str(prompt_text or "").strip().lower()
    if not normalized_archetype or not prompt_lower:
        return None

    scored: list[tuple[int, str]] = []
    for overlay, meta in DOMAIN_OVERLAY_LIBRARY.items():
        allowed_archetypes = {str(item).strip().lower() for item in meta.get("archetypes", set())}
        if allowed_archetypes and normalized_archetype not in allowed_archetypes:
            continue
        allowed_families = {str(item).strip().lower() for item in meta.get("style_families", set())}
        if style_family and allowed_families and str(style_family).strip().lower() not in allowed_families:
            continue
        keywords = [str(token).strip().lower() for token in meta.get("keywords", [])]
        score = sum(1 for token in keywords if token and token in prompt_lower)
        if score > 0:
            scored.append((score, overlay))

    if not scored:
        return None

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def get_style_family_context(archetype: str | None, prompt_text: str | None = None) -> dict[str, Any] | None:
    style_family = infer_style_family(archetype, prompt_text)
    domain_overlay = infer_domain_overlay(archetype, prompt_text, style_family=style_family)
    if not style_family and not domain_overlay:
        return None
    family_meta = STYLE_FAMILY_LIBRARY.get(style_family, {}) if style_family else {}
    overlay_meta = DOMAIN_OVERLAY_LIBRARY.get(domain_overlay, {}) if domain_overlay else {}
    return {
        "style_family": style_family,
        "description": str(family_meta.get("description", "")).strip(),
        "guidance_lines": [
            str(line).strip()
            for line in family_meta.get("guidance_lines", [])
            if str(line).strip()
        ],
        "domain_overlay": domain_overlay,
        "overlay_description": str(overlay_meta.get("description", "")).strip(),
        "overlay_guidance_lines": [
            str(line).strip()
            for line in overlay_meta.get("guidance_lines", [])
            if str(line).strip()
        ],
    }


def get_reference_build_registry() -> list[dict[str, Any]]:
    if not BENCHMARKS_PATH.exists():
        return []
    data = _read_json(BENCHMARKS_PATH)
    items = data.get("benchmarks", [])
    return [item for item in items if isinstance(item, dict)]


def get_reference_build_entries(archetype: str | None = None) -> list[dict[str, Any]]:
    entries = get_reference_build_registry()
    if archetype is None:
        return entries
    normalized = _normalize_archetype_name(archetype)
    direct = [
        item for item in entries
        if _normalize_archetype_name(item.get("archetype")) == normalized
    ]
    if normalized not in BENCHMARK_VARIANT_RULES:
        return direct

    variant_matches = [item for item in entries if _entry_matches_variant(item, normalized)]
    seen: set[tuple[int, int]] = set()
    merged: list[dict[str, Any]] = []
    for item in direct + variant_matches:
        key = (
            int(item.get("project_id", 0)),
            int(item.get("version", 1)),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def get_style_family_reference_build_entries(
    archetype: str,
    style_family: str,
) -> list[dict[str, Any]]:
    normalized_archetype = _normalize_archetype_name(archetype)
    if not normalized_archetype or not style_family:
        return []
    entries = get_reference_build_registry()
    matches = [
        item
        for item in entries
        if _entry_matches_style_family(item, style_family, archetype=normalized_archetype)
    ]
    if normalized_archetype in BENCHMARK_VARIANT_RULES:
        variant_matches = [
            item for item in matches
            if _entry_matches_variant(item, normalized_archetype)
        ]
        if variant_matches:
            matches = variant_matches
    boosts = STYLE_FAMILY_ENTRY_BOOSTS.get(str(style_family or "").strip().lower(), {})
    return sorted(
        matches,
        key=lambda item: (
            int(item.get("priority", 0)) + int(boosts.get(str(item.get("label", "")).strip().lower(), 0)),
            int(item.get("priority", 0)),
        ),
        reverse=True,
    )


def get_sorted_reference_build_entries(archetype: str | None = None) -> list[dict[str, Any]]:
    entries = get_reference_build_entries(archetype)
    return sorted(entries, key=lambda item: int(item.get("priority", 0)), reverse=True)


def resolve_reference_build_source_paths(entry: dict[str, Any]) -> dict[str, Any] | None:
    project_id = int(entry["project_id"])
    version = int(entry.get("version", 1))
    benchmark_path = entry.get("benchmark_path")
    published_slug = entry.get("published_slug")

    base = GENERATED_DIR / str(project_id) / f"v{version}"
    html_path = base / "code" / "src" / "index.html"
    css_path = base / "code" / "src" / "style.css"
    base_css_path = base / "code" / "src" / "base.css"
    componentized_html_path = base / "code" / "src" / "App.tsx"
    componentized_css_paths = [
        path
        for path in (
            base / "code" / "src" / "style.css",
            base / "code" / "src" / "index.css",
        )
        if path.exists()
    ]

    if benchmark_path:
        benchmark_base = ROOT / str(benchmark_path)
        benchmark_html = benchmark_base / "src" / "index.html"
        benchmark_css = benchmark_base / "src" / "style.css"
        if benchmark_html.exists() and benchmark_css.exists():
            html_path = benchmark_html
            css_path = benchmark_css
        benchmark_base_css = benchmark_base / "src" / "base.css"
        if benchmark_base_css.exists():
            base_css_path = benchmark_base_css

    if (not html_path.exists() or not css_path.exists()) and published_slug:
        published_base = PUBLISHED_DIR / str(published_slug) / "src"
        published_html = published_base / "index.html"
        published_css = published_base / "style.css"
        if published_html.exists() and published_css.exists():
            html_path = published_html
            css_path = published_css
        published_base_css = published_base / "base.css"
        if published_base_css.exists():
            base_css_path = published_base_css

    if not html_path.exists() or not css_path.exists():
        if componentized_html_path.exists() and componentized_css_paths:
            return {
                "html_path": componentized_html_path,
                "css_path": componentized_css_paths[0],
                "base_css_path": base_css_path,
                "render_mode": "componentized",
            }
        return None

    return {
        "html_path": html_path,
        "css_path": css_path,
        "base_css_path": base_css_path,
        "render_mode": "legacy",
    }


def _get_guidance_lines(entries: list[dict[str, Any]], limit: int) -> list[str]:
    entries.sort(key=lambda item: int(item.get("priority", 0)), reverse=True)
    lines: list[str] = []
    seen: set[str] = set()
    for entry in entries[:limit]:
        note = str(entry.get("notes", "")).strip()
        label = str(entry.get("label", "")).strip()
        if not note:
            continue
        normalized = note.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        prefix = f"{label}: " if label else ""
        lines.append(f"- {prefix}{note}")
    return lines


def get_archetype_benchmark_guidance(
    archetype: str,
    prompt_text: str | None = None,
    limit: int = 4,
    global_limit: int = 2,
) -> str:
    if not archetype:
        return ""

    style_family = infer_style_family(archetype, prompt_text)
    family_lines: list[str] = []
    if style_family:
        family_meta = STYLE_FAMILY_LIBRARY.get(style_family, {})
        description = str(family_meta.get("description", "")).strip()
        if description:
            family_lines.append(f"- STYLE FAMILY ({style_family}): {description}")
        for line in family_meta.get("guidance_lines", [])[:4]:
            text = str(line).strip()
            if text:
                family_lines.append(f"- {text}")

    domain_overlay = infer_domain_overlay(archetype, prompt_text, style_family=style_family)
    overlay_lines: list[str] = []
    if domain_overlay:
        overlay_meta = DOMAIN_OVERLAY_LIBRARY.get(domain_overlay, {})
        description = str(overlay_meta.get("description", "")).strip()
        if description:
            overlay_lines.append(f"- DOMAIN OVERLAY ({domain_overlay}): {description}")
        for line in overlay_meta.get("guidance_lines", [])[:5]:
            text = str(line).strip()
            if text:
                overlay_lines.append(f"- {text}")

    style_entries = get_style_family_reference_build_entries(archetype, style_family) if style_family else []
    archetype_entries = get_reference_build_entries(archetype)
    preferred_entries = style_entries or archetype_entries
    archetype_lines = _get_guidance_lines(preferred_entries, limit)
    global_entries = [
        item for item in get_reference_build_registry()
        if bool(item.get("global_guidance"))
    ]
    global_lines = _get_guidance_lines(global_entries, global_limit)
    lines = family_lines + overlay_lines + archetype_lines + [line for line in global_lines if line not in archetype_lines]
    return "\n".join(lines)


def suggest_reference_archetype(prompt_text: str) -> dict[str, Any] | None:
    if not prompt_text:
        return None

    prompt_lower = prompt_text.lower()
    matches: list[dict[str, Any]] = []
    for entry in get_reference_build_registry():
        hints = entry.get("prompt_hints", []) or []
        if not isinstance(hints, list):
            continue
        normalized_hints = [
            hint.strip().lower()
            for hint in hints
            if isinstance(hint, str) and hint.strip()
        ]
        if any(hint in prompt_lower for hint in normalized_hints):
            matches.append(entry)

    if not matches:
        return None

    matches.sort(key=lambda item: int(item.get("priority", 0)), reverse=True)
    selected = dict(matches[0])
    variant_archetype = _infer_variant_archetype(prompt_lower, selected)
    if variant_archetype:
        selected["archetype"] = variant_archetype
    style_family = infer_style_family(selected.get("archetype"), prompt_lower)
    if style_family:
        selected["style_family"] = style_family
    domain_overlay = infer_domain_overlay(selected.get("archetype"), prompt_lower, style_family=style_family)
    if domain_overlay:
        selected["domain_overlay"] = domain_overlay
    return selected


def load_reference_build_content(entry: dict[str, Any]) -> dict[str, Any] | None:
    project_id = int(entry["project_id"])
    version = int(entry.get("version", 1))
    archetype = entry.get("archetype", "")
    source_paths = resolve_reference_build_source_paths(entry)
    if source_paths is None:
        return None

    base = GENERATED_DIR / str(project_id) / f"v{version}"
    html_path = source_paths["html_path"]
    css_path = source_paths["css_path"]
    base_css_path = source_paths["base_css_path"]
    render_mode = str(source_paths.get("render_mode", "legacy"))
    factsheet_path = base / "last_factsheet.json"
    factsheet: dict[str, Any] = {}

    if factsheet_path.exists():
        factsheet = _read_json(factsheet_path)

    html_code = html_path.read_text(encoding="utf-8")
    css_parts = [css_path.read_text(encoding="utf-8")]
    if render_mode == "componentized":
        componentized_index_css = base / "code" / "src" / "index.css"
        if componentized_index_css.exists() and componentized_index_css != css_path:
            css_parts.append(componentized_index_css.read_text(encoding="utf-8"))
    css_code = "\n\n".join(part for part in css_parts if part.strip())

    return {
        "project_id": project_id,
        "version": version,
        "archetype": archetype,
        "label": entry.get("label", f"project-{project_id}"),
        "notes": entry.get("notes", ""),
        "prompt": factsheet.get("prompt_summary", "") or entry.get("prompt_summary", ""),
        "html_code": html_code,
        "css_code": css_code,
        "base_css": base_css_path.read_text(encoding="utf-8") if base_css_path.exists() else "",
        "eval_score": entry.get("eval_score"),
        "priority": int(entry.get("priority", 0)),
        "discovery_ingest": bool(entry.get("discovery_ingest", False)),
        "source": "local_benchmark",
        "render_mode": render_mode,
    }


def load_local_reference_build(archetype: str, prompt_text: str | None = None) -> dict[str, Any] | None:
    """Load the highest-priority local benchmark build for an archetype."""
    if not archetype:
        return None

    style_family = infer_style_family(archetype, prompt_text)
    matches = get_style_family_reference_build_entries(archetype, style_family) if style_family else []
    selection_reason = "style_family" if matches else "archetype"
    if not matches:
        matches = get_sorted_reference_build_entries(archetype)
    if not matches:
        return None
    build = None
    for entry in matches:
        build = load_reference_build_content(entry)
        if build is not None:
            break
    if build:
        build["archetype"] = _normalize_archetype_name(archetype)
        build["style_family"] = style_family
        build["domain_overlay"] = infer_domain_overlay(archetype, prompt_text, style_family=style_family)
        build["selection_reason"] = selection_reason
        build["benchmark_guidance"] = get_archetype_benchmark_guidance(archetype, prompt_text=prompt_text)
    return build
