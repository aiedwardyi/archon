from __future__ import annotations

import json
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

STYLE_FAMILY_LIBRARY: dict[str, dict[str, Any]] = {
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

BENCHMARK_STYLE_FAMILIES: dict[str, tuple[str, ...]] = {
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
    "cinematic_collector_fanpage": {
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


def _entry_matches_variant(entry: dict[str, Any], archetype: str) -> bool:
    variant = BENCHMARK_VARIANT_RULES.get(_normalize_archetype_name(archetype))
    if not variant:
        return False
    if _normalize_archetype_name(entry.get("archetype")) != variant["base_archetype"]:
        return False

    haystack = _entry_search_text(entry)
    include_any = variant.get("include_any", [])
    exclude_any = variant.get("exclude_any", [])
    if include_any and not any(token in haystack for token in include_any):
        return False
    if exclude_any and any(token in haystack for token in exclude_any):
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

    if normalized_archetype == "game" and prompt_lower:
        return "cinematic_collector_fanpage"
    return None


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


def resolve_reference_build_source_paths(entry: dict[str, Any]) -> dict[str, Path] | None:
    project_id = int(entry["project_id"])
    version = int(entry.get("version", 1))
    benchmark_path = entry.get("benchmark_path")
    published_slug = entry.get("published_slug")

    base = GENERATED_DIR / str(project_id) / f"v{version}"
    html_path = base / "code" / "src" / "index.html"
    css_path = base / "code" / "src" / "style.css"
    base_css_path = base / "code" / "src" / "base.css"

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
        return None

    return {
        "html_path": html_path,
        "css_path": css_path,
        "base_css_path": base_css_path,
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
        for line in family_meta.get("guidance_lines", [])[:3]:
            text = str(line).strip()
            if text:
                family_lines.append(f"- {text}")

    style_entries = get_style_family_reference_build_entries(archetype, style_family) if style_family else []
    archetype_entries = get_reference_build_entries(archetype)
    preferred_entries = style_entries or archetype_entries
    archetype_lines = _get_guidance_lines(preferred_entries, limit)
    global_entries = [
        item for item in get_reference_build_registry()
        if bool(item.get("global_guidance"))
    ]
    global_lines = _get_guidance_lines(global_entries, global_limit)
    lines = family_lines + archetype_lines + [line for line in global_lines if line not in archetype_lines]
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
    factsheet_path = base / "last_factsheet.json"
    factsheet: dict[str, Any] = {}

    if factsheet_path.exists():
        factsheet = _read_json(factsheet_path)

    return {
        "project_id": project_id,
        "version": version,
        "archetype": archetype,
        "label": entry.get("label", f"project-{project_id}"),
        "notes": entry.get("notes", ""),
        "prompt": factsheet.get("prompt_summary", "") or entry.get("prompt_summary", ""),
        "html_code": html_path.read_text(encoding="utf-8"),
        "css_code": css_path.read_text(encoding="utf-8"),
        "base_css": base_css_path.read_text(encoding="utf-8") if base_css_path.exists() else "",
        "eval_score": entry.get("eval_score"),
        "priority": int(entry.get("priority", 0)),
        "discovery_ingest": bool(entry.get("discovery_ingest", False)),
        "source": "local_benchmark",
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
    build = load_reference_build_content(matches[0])
    if build:
        build["archetype"] = _normalize_archetype_name(archetype)
        build["style_family"] = style_family
        build["selection_reason"] = selection_reason
        build["benchmark_guidance"] = get_archetype_benchmark_guidance(archetype, prompt_text=prompt_text)
    return build
