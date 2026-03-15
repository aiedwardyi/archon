from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from utils.offline_engineer_scaffold import build_vite_react_ts_scaffold


TEXT_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".mjs",
    ".ts",
    ".tsx",
    ".txt",
    ".yml",
    ".yaml",
}

TEXT_FILENAMES = {
    ".gitignore",
    "index.html",
    "package.json",
    "README.md",
    "tsconfig.json",
    "tsconfig.node.json",
    "vite.config.ts",
}

NON_EDITABLE_COMPONENTIZED_FILENAMES = {
    "package-lock.json",
}

SKIP_DIRS = {
    ".git",
    ".npm-cache",
    ".vite",
    "__pycache__",
    "assets",
    "dist",
    "node_modules",
}

API_ASSET_URL_RE = re.compile(r"/api/assets/\d+/\d+/([^\"'()\s>]+)")
LOCAL_CODE_IMPORT_RE = re.compile(r'((?:from\s+|import\s*\(\s*|import\s+)[\"\'])(\.\.?/[^\"\']+?)\.(tsx|ts|jsx|js)([\"\'])')
BASE_CSS_IMPORT_LINE_RE = re.compile(r'^\s*import\s+[\"\'][^\"\']*base\.css[\"\'];?\s*$\n?', re.MULTILINE)
BASE_CSS_IMPORT_ANY_RE = re.compile(r'import\s+[\"\'][^\"\']*base\.css[\"\'];?\s*')
MAIN_BASE_CSS_IMPORT_RE = re.compile(
    r'^\s*import\s+[\"\'][^\"\']*base\.css[\"\'];?\s*(?:(?:/\*.*\*/)|(?://.*))?\s*$',
    re.MULTILINE,
)
MAIN_ENTRY_INVALID_IMPORT_NOTE_RE = re.compile(r"^\s*import\s+it(?:\b|[.])", re.IGNORECASE)
INLINE_COMMENT_RUNON_RE = re.compile(
    r"//\s*([^\n]*?)(?=(?:import\b|const|let|var|function|export\b|return\b|interface\b|type\b|class\b|use[A-Z]\w*|[A-Z][A-Za-z0-9_]*\s*[.(<]))"
)
INLINE_BLOCK_COMMENT_CODE_BLEED_RE = re.compile(
    r"/\*\s*(?P<comment>[^*]*?)\s{2,}(?P<prop>[A-Za-z_$][\w$]*)\s*:\s*(?P<prefix>[^*]*?)\*/\s*\n\s*",
    re.MULTILINE,
)
BLOCK_COMMENT_CONTROL_FLOW_BLEED_RE = re.compile(
    r"/\*\s*(?P<comment>[^*]*?)\s+(?P<code>(?:if\s*\([^*]+\)\s*\{|for\s*\([^*]+\)\s*\{|while\s*\([^*]+\)\s*\{|return\b[^*;{}]*[;{]|const\s+[A-Za-z_$][\w$]*\s*=|let\s+[A-Za-z_$][\w$]*\s*=|var\s+[A-Za-z_$][\w$]*\s*=|set[A-Z]\w*\s*\([^*]*\)))\s*\*/",
    re.MULTILINE,
)
UNTERMINATED_BLOCK_COMMENT_LINE_NOTE_RE = re.compile(
    r"(?P<indent>[ \t]*)/\*\s*(?P<comment>[^*\n]{2,240}?)\s*//\s*(?P<tail>[^*\n]{2,240}?)\s+(?P<code>(?:console\.[A-Za-z_$][\w$]*\s*\(|return\b|const\b|let\b|var\b|if\s*\(|for\s*\(|while\s*\(|switch\s*\(|set[A-Z]\w*\s*\(|[A-Za-z_$][\w$]*\s*=|[A-Za-z_$][\w$]*\s*\())(?P<rest>[^\n]*)",
    re.MULTILINE,
)
INLINE_BLOCK_COMMENT_CONTINUATION_RE = re.compile(
    r"(?m)^(?P<prefix>[^\n]*?)/\*\s*(?P<comment>[^*\n]{2,240}?)\s{2,}(?P<code>(?:[)}\]],?\s*[^\n]*|[A-Za-z_:][-A-Za-z0-9_:.]*=\s*[^\n]*|[A-Za-z_$][\w$]*\s*:\s*[^\n]*|(?:const|let|var|return|if|for|while|switch)\b[^\n]*|set[A-Z]\w*\s*\([^\n]*))(?:\s*//\s*(?P<label>[^*\n]{2,200}?))?\s*(?:\*/)?\s*$",
    re.MULTILINE,
)
INTERFACE_FIELD_COMMENT_BLEED_RE = re.compile(
    r"(?P<field>[A-Za-z_$][\w$]*\??\s*:\s*[^;{}\n]+;)\s*/\*\s*(?P<comment>[^*]*?)\}\s*\*/\s*\n(?=\s*(?:interface|type)\b)",
    re.MULTILINE,
)
RUNON_NATURAL_LANGUAGE_NOTE_RE = re.compile(
    r"(?:(?<=;)|(?<=\n)|^)\s*(?:Return|Note|Explanation|Data)\s*\((?P<note>[^)\n]{2,160})\)\s*(?=(?:const\b|let\b|var\b|return\b|set[A-Z]\w*\b|[A-Za-z_$][\w$]*\s*=))",
    re.MULTILINE,
)
RUNON_EXPLANATORY_LABEL_RE = re.compile(
    r"(?m)^(?P<label>[A-Za-z][A-Za-z0-9/&,\- ':]+(?:\([^)\n]{1,120}\))?)\s{2,}(?=(?:[)}]\s*)*(?:const\b|let\b|var\b|function\b|return\b|set[A-Z]\w*\b|[A-Za-z_$][\w$]*\s*=|[)}]))"
)
LOWERCASE_OBJECT_FIELD_LABEL_RE = re.compile(
    r"(?m)^(?P<indent>[ \t]*)(?P<label>[a-z][A-Za-z0-9/&,\- ']{2,120}?)\s{2,}(?P<field>[A-Za-z_$][\w$]*\s*:\s*[^\n]+)$"
)
BARE_SECTION_LABEL_RE = re.compile(
    r"(?m)^(?P<label>[A-Za-z][A-Za-z0-9/&,\- ':]+(?:\([^)\n]{1,120}\))?)\s*$\n(?=\s*(?:/\*|//|const|let|var|function|export|type|interface|class|return|if|for|while|switch|set[A-Z]\w*\(|[A-Za-z_$][\w$]*\(|[)}]))"
)
URL_PROTOCOL_COMMENT_BLEED_RE = re.compile(r"(?P<scheme>https?):/\*\s*")
ATTR_VALUE_ORPHAN_COMMENT_CLOSE_RE = re.compile(
    r"(?P<attr>[A-Za-z_:][-A-Za-z0-9_:.]*)=(?P<quote>[\"'])\s*\*/\s*"
)
TRAILING_SECTION_LINE_COMMENT_RE = re.compile(
    r"(?P<stmt>(?:\)\s*;|}\s*;))\s*//\s*(?P<label>[^*\n]{2,120}?)\s*\*/\s*(?=\r?\n\s*(?:const|function|export|type|interface|class))",
    re.MULTILINE,
)
ORPHAN_COMMENT_CLOSE_AFTER_STATEMENT_RE = re.compile(
    r"(?P<stmt>(?:\)\s*;|}\s*;))\s*\*/(?=\s*(?:\r?\n\s*)?(?:const|function|export|type|interface|class|return|$))",
    re.MULTILINE,
)
CONTROL_FLOW_ORPHAN_COMMENT_CLOSE_RE = re.compile(
    r"(?P<prefix>\b(?:if|for|while|switch)\s*\()\s*\*/\s*(?:\r?\n\s*)?",
    re.MULTILINE,
)
BLOCK_COMMENT_SWALLOWED_ARRAY_CLOSE_RE = re.compile(
    r"/\*\s*(?P<comment>[\s\S]{0,600}?)\];\s*\*/\s*(?=\r?\n\s*(?:export|const|let|var|function|interface|type|class)\b)",
    re.MULTILINE,
)
COMMENT_SPLIT_IDENTIFIER_RE = re.compile(
    r"/\*\s*(?P<comment>[^*]*?)\s{2,}(?P<prefix>[a-z][A-Za-z0-9_$]{1,32})\s*\*/\s*\n(?P<suffix>[A-Z][A-Za-z0-9_$]{1,64})(?P<rest>[^\n]*)",
    re.MULTILINE,
)
ORPHAN_COMMENT_SPLIT_IDENTIFIER_RE = re.compile(
    r"(?<![A-Za-z0-9_$])(?P<prefix>[a-z][A-Za-z0-9_$]{1,32})\s*\*/\s*\n(?P<indent>[ \t]*)(?P<suffix>[A-Z][A-Za-z0-9_$]{1,64})(?P<rest>[^\n]*)",
    re.MULTILINE,
)
ORPHAN_COMMENT_SPLIT_STRING_LITERAL_RE = re.compile(
    r"(?P<prefix>(?:\?|:|=|\(|,|\{)\s*)(?P<quote>['\"])\s*\*/\s*\n(?P<indent>[ \t]*)(?P<content>[^'\"\n]{1,120})(?P=quote)",
    re.MULTILINE,
)
JSX_BLOCK_COMMENT_BLEED_RE = re.compile(
    r"(?P<open>\(\s*)/\*\s*(?P<comment>[^*]*?)\s{2,}(?P<jsx><[A-Za-z][\s\S]*?)\{(?P<prefix>[a-z][A-Za-z0-9_$]{1,32})\s*\*/\s*\n(?P<indent>[ \t]*)(?P<suffix>[A-Z][A-Za-z0-9_$]{1,64})(?P<rest>[^\n]*)",
    re.MULTILINE,
)
JSX_TEXT_COMMENT_CLOSE_BLEED_RE = re.compile(
    r">(?P<prefix>[^<>{\n]{1,120}?)\s*\*/\s*(?:\r?\n\s*(?:\d+\s*\|\s*)?)?(?P<suffix>[A-Za-z][^<>{\n]{0,120}?)<",
    re.MULTILINE,
)
VOID_JSX_ELEMENT_RE = re.compile(
    r"(?<![A-Za-z0-9_\"'])<(?P<tag>area|base|br|col|embed|hr|img|input|link|meta|param|source|track|wbr)\b(?P<attrs>[^<>]*?)(?<!/)>",
    re.IGNORECASE,
)
JSX_EVENT_HANDLER_ARROW_BLEED_RE = re.compile(
    r"(?P<prefix>\bon[A-Z][A-Za-z0-9_]*=\{\s*)(?P<param>\(?\s*[A-Za-z_$][\w$]*\s*\)?)\s*=\s*/>"
)
CSS_DATA_URI_ESCAPED_QUOTE_BLEED_RE = re.compile(
    r"\\'\\''(?=\s+[A-Za-z-]+=)"
)
DECLARATION_BOUNDARY_RE = re.compile(
    r"(?<=})(?=(?:interface\b|type\b|const\b|let\b|var\b|function\b|export\b|class\b|return\b))"
)
PACKAGE_IMPORT_RE = re.compile(
    r'^\s*(?:import(?:.+?\sfrom\s+)?|export.+?\sfrom\s+)[\"\']([^\"\']+)[\"\']',
    re.MULTILINE,
)
LOCAL_CSS_IMPORT_RE = re.compile(r'^\s*import\s+[\"\'](\.?\.?/[^\"\']+\.css)[\"\'];?', re.MULTILINE)
LOCAL_REL_IMPORT_RE = re.compile(
    r'(?:from\s+[\"\'](?P<from>\.{1,2}/[^\"\']+)[\"\']|import\s*\(\s*[\"\'](?P<dynamic>\.{1,2}/[^\"\']+)[\"\']\s*\)|import\s+[\"\'](?P<bare>\.{1,2}/[^\"\']+)[\"\'])'
)
EMPTY_CURRENCY_FORMAT_ARG_RE = re.compile(
    r"formatCurrency\(\s*(?P<value>[^,\n]+?)\s*,\s*['\"]\s*['\"]\s*\)"
)
FORMAT_CURRENCY_GUARD_RE = re.compile(r"currency\s*:\s*currency\b")
GOOGLE_FONT_IMPORT_RE = re.compile(r"https://fonts\.googleapis\.com/[^\s\"')]+")
CSS_VARIABLE_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;}{]+);")
HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
KEYFRAME_RE = re.compile(r"@keyframes\s+([A-Za-z_][\w-]*)")
JSON_ESCAPE_NOISE_RE = re.compile(r"\\[nrt]")
GENERATED_ASSET_REFERENCE_RE = re.compile(
    r"(?:^|[\"'(\s=])(?:\./)?generated-assets/(?P<filename>[^\"')\s]+)",
    re.IGNORECASE,
)
RUNTIME_GENERATED_ASSET_REFERENCE_RE = re.compile(
    r'(?P<prefix>^|["\'(\s=,:])(?P<path>(?:\./)?/?generated-assets/(?P<subpath>[^"\'\s)]+))',
    re.IGNORECASE,
)
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;}{]+);")
BORDER_RADIUS_RE = re.compile(r"border-radius\s*:\s*([^;}{]+);")
BOX_SHADOW_RE = re.compile(r"box-shadow\s*:\s*([^;}{]+);")
MEDIA_QUERY_RE = re.compile(r"@media[^{]*?(?:max|min)-width\s*:\s*([0-9]+px)", re.IGNORECASE)
JS_EVENT_HANDLER_RE = re.compile(r"\bon(Click|Change|Submit|Input|KeyDown|KeyUp|MouseEnter|MouseLeave|Focus|Blur)\s*=")
DOM_EVENT_LISTENER_RE = re.compile(r"addEventListener\(\s*['\"]([a-z]+)['\"]")
CSS_BLOCK_RE = re.compile(r"(?P<selector>[^{}]+)\{(?P<body>[^{}]*)\}", re.MULTILINE)
GOOGLE_FONT_IMPORT_LINE_RE = re.compile(r"^\s*@import\s+url\([^)]+fonts\.googleapis\.com[^)]*\)\s*;\s*$", re.MULTILINE)

SAFE_COMPONENTIZED_DEPENDENCIES = {
    "@heroicons/react": "^2.2.0",
    "clsx": "^2.1.1",
    "lucide-react": "^0.564.0",
    "recharts": "2.15.0",
}

DISPLAY_SELECTOR_HINTS = (
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    ".page-title",
    ".section-title",
    ".chart-title",
    ".panel-title",
    ".topbar-brand",
    ".logo-text",
    ".feed-header",
)

OVERRIDE_DISPLAY_FONT_RE = re.compile(r"(--font-display\s*:\s*)'Inter'[^;]*;", re.IGNORECASE)
NUMERIC_SELECTOR_HINTS = (
    ".kpi-value",
    ".kpi-delta",
    ".ticker-price",
    ".ticker-delta",
    ".watch-price",
    ".watch-delta",
    ".feed-time",
    ".asset-table td",
    ".table-number",
    ".numeric",
    ".price",
    ".delta",
)
MAIN_CSS_IMPORT_LINE_RE = re.compile(r'^\s*import\s+["\'](?P<path>\./[^"\']+\.css)["\'];?\s*(?:(?:/\*.*\*/)|(?://.*))?\s*$')
MAIN_ENTRY_PREFERRED_CSS_ORDER = ("./base.css", "./index.css", "./style.css", "./styles.css")
POLISH_GUARD_IMPORT = "./polish-guard.css"
POLISH_GUARD_RUNTIME_IMPORT = "./polish-guard"
POLISH_GUARD_ARCHETYPES = {"dashboard", "fintech"}
COMPONENTIZED_UTILITY_FALLBACKS: dict[str, str] = {
    "font-display": "font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif); letter-spacing: -0.02em;",
    "font-body": "font-family: var(--font-body, 'Inter', sans-serif);",
    "font-mono": "font-family: var(--font-mono, 'JetBrains Mono', monospace); font-variant-numeric: tabular-nums;",
    "text-color-primary-text": "color: var(--color-primary-text, var(--text, #f4f8fc));",
    "text-color-secondary-text": "color: var(--color-secondary-text, var(--text-secondary, #b8c6d8));",
    "text-color-muted-text": "color: var(--color-muted-text, var(--text-muted, #6f7f95));",
    "text-color-primary-accent": "color: var(--color-primary-accent, var(--accent, #10b981));",
    "text-color-success": "color: var(--color-success, var(--accent, #10b981));",
    "text-color-danger": "color: var(--color-danger, #f87171);",
    "text-h1": "font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif); font-size: var(--font-size-h1, clamp(2.5rem, 4vw, 3.5rem)); line-height: 1.05;",
    "text-h2": "font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif); font-size: var(--font-size-h2, clamp(1.875rem, 3vw, 2.5rem)); line-height: 1.1;",
    "text-h3": "font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif); font-size: var(--font-size-h3, clamp(1.25rem, 2vw, 1.75rem)); line-height: 1.2;",
    "top-1/2": "top: 50%;",
    "-translate-y-1/2": "transform: translateY(-50%);",
}
COMPONENTIZED_UTILITY_FALLBACK_MARKER = "/* Generated componentized utility fallbacks */"
COMPONENTIZED_FIELD_ALIAS_GROUPS: tuple[tuple[str, ...], ...] = (
    ("changePercent", "change24hPercent", "dayChangePercent"),
    ("change", "change24h", "dayChange"),
    ("price", "priceUsd", "assetPrice"),
    ("value", "valueUsd", "totalValueUsd"),
)


def infer_scaffold_mode(code_dir: Path, plan_data: dict[str, Any] | None = None) -> str:
    if plan_data:
        for milestone in plan_data.get("milestones", []):
            for task in milestone.get("tasks", []):
                if task.get("execution_hint") == "engineer":
                    mode = str(task.get("scaffold_mode") or "").strip()
                    if mode:
                        return mode

    package_json = code_dir / "package.json"
    if package_json.exists():
        return "componentized_app"
    return "legacy_single_page"


def is_componentized_workspace(code_dir: Path, plan_data: dict[str, Any] | None = None) -> bool:
    return infer_scaffold_mode(code_dir, plan_data=plan_data) == "componentized_app"


def collect_existing_code_context(
    code_dir: Path,
    *,
    max_files: int = 48,
    max_chars_per_file: int = 24_000,
) -> str | None:
    if not code_dir.exists():
        return None

    rendered: list[str] = []
    file_count = 0

    for path in sorted(code_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(code_dir).as_posix()
        if any(part in SKIP_DIRS for part in path.relative_to(code_dir).parts[:-1]):
            continue
        if rel.startswith("assets/"):
            continue

        name = path.name
        if name in NON_EDITABLE_COMPONENTIZED_FILENAMES:
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS and name not in TEXT_FILENAMES:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if len(content) > max_chars_per_file:
            content = content[:max_chars_per_file] + "\n/* TRUNCATED FOR CONTEXT */\n"

        rendered.append(f"--- FILE: {rel} ---\n{content}\n--- END FILE ---")
        file_count += 1
        if file_count >= max_files:
            rendered.append("--- NOTE: Additional files omitted for context size. ---")
            break

    if not rendered:
        return None
    return "\n\n".join(rendered)


def collect_selected_code_context(
    code_dir: Path,
    rel_paths: list[str],
    *,
    max_chars_per_file: int = 24_000,
) -> str | None:
    rendered: list[str] = []
    for rel_path in rel_paths:
        normalized = rel_path.replace("\\", "/").strip("/")
        if not normalized:
            continue
        path = code_dir / normalized
        if not path.exists() or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(content) > max_chars_per_file:
            content = content[:max_chars_per_file] + "\n/* TRUNCATED FOR CONTEXT */\n"
        rendered.append(f"--- FILE: {normalized} ---\n{content}\n--- END FILE ---")
    if not rendered:
        return None
    return "\n\n".join(rendered)


def _collect_workspace_text_blob(code_dir: Path, *, max_chars_per_file: int = 24_000) -> str:
    if not code_dir.exists():
        return ""

    chunks: list[str] = []
    for rel_path in collect_componentized_editable_files(code_dir):
        path = code_dir / rel_path
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(content) > max_chars_per_file:
            content = content[:max_chars_per_file]
        chunks.append(content)
    return "\n".join(chunks)


def _limited_sorted_set(values: Any, *, limit: int) -> list[str]:
    seen: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.append(normalized)
        if len(seen) >= limit:
            break
    return sorted(seen)


def extract_visual_dna(code_dir: Path) -> dict[str, Any]:
    combined = _collect_workspace_text_blob(code_dir)
    if not combined:
        return {
            "google_font_imports": [],
            "font_families": [],
            "css_variables": {},
            "hex_colors": [],
            "keyframes": [],
            "radius_values": [],
            "shadow_values": [],
        }

    css_variables: dict[str, str] = {}
    for name, value in CSS_VARIABLE_RE.findall(combined):
        if name not in css_variables and len(css_variables) < 48:
            css_variables[name] = " ".join(value.strip().split())

    return {
        "google_font_imports": _limited_sorted_set(GOOGLE_FONT_IMPORT_RE.findall(combined), limit=8),
        "font_families": _limited_sorted_set(
            (" ".join(match.strip().split()) for match in FONT_FAMILY_RE.findall(combined)),
            limit=16,
        ),
        "css_variables": css_variables,
        "hex_colors": _limited_sorted_set((value.lower() for value in HEX_COLOR_RE.findall(combined)), limit=32),
        "keyframes": _limited_sorted_set(KEYFRAME_RE.findall(combined), limit=24),
        "radius_values": _limited_sorted_set(
            (" ".join(match.strip().split()) for match in BORDER_RADIUS_RE.findall(combined)),
            limit=16,
        ),
        "shadow_values": _limited_sorted_set(
            (" ".join(match.strip().split()) for match in BOX_SHADOW_RE.findall(combined)),
            limit=16,
        ),
    }


def extract_feature_inventory(code_dir: Path) -> dict[str, Any]:
    combined = _collect_workspace_text_blob(code_dir)
    normalized = combined.lower()
    if not combined:
        return {
            "event_handlers": [],
            "responsive_breakpoints": [],
            "detected_features": [],
            "polish_features": [],
        }

    event_handlers = {
        event.lower()
        for event in JS_EVENT_HANDLER_RE.findall(combined)
    }
    event_handlers.update(DOM_EVENT_LISTENER_RE.findall(normalized))

    feature_patterns = {
        "tabs": ("data-tab", "activetab", "role=\"tab\"", "tablist"),
        "filters": ("filtered", "setfilter", "categoryfilter", "filterpill"),
        "search": ("searchquery", "setsearch", "searchterm", "searchinput", 'aria-label="search', 'placeholder="search'),
        "cart": ("addtocart", "cartitems", "setcart", "subtotal"),
        "wishlist": ("wishlist", "saveditems"),
        "loyalty": ("loyalty", "reward points", "rewards tier", "points balance"),
        "modal_or_dialog": ("modal", "dialog", "aria-modal"),
        "drawer_or_sheet": ("drawer", "sheet", "slideover"),
        "accordion": ("accordion", "expandedindex", "faq-item"),
        "carousel": ("carousel", "current slide", "setcurrentslide"),
        "toast_notifications": ("toast", "notification", "showtoast"),
        "form_validation": ("onsubmit", "seterrors", "validation", "error message"),
        "mobile_nav": ("mobilemenu", "nav-open", "setismenuopen", "hamburger"),
        "scroll_reveal": ("intersectionobserver", "scrollreveal", "reveal-on-scroll"),
        "chart_state": ("recharts", "chart", "selectedrange", "sparkline", "tooltip"),
        "table_sorting": ("sortconfig", "sortkey", "sortdirection", "sortable"),
        "table_filtering": ("filteredrows", "filteredtransactions", "filteredcustomers"),
        "range_selector": ("7d", "30d", "90d", "1y", "selectedrange"),
        "watchlist": ("watchlist", "watch list"),
        "game_loop": ("streak", "score", "nextquestion", "difficulty"),
    }

    detected_features = [
        feature
        for feature, signals in feature_patterns.items()
        if any(signal in normalized for signal in signals)
    ]

    polish_patterns = {
        "custom_scrollbar": ("::-webkit-scrollbar", "scrollbar-width"),
        "selection_styling": ("::selection",),
        "sticky_header": ("position: sticky", "sticky top"),
        "count_up_numbers": ("countup", "requestanimationframe", "animatevalue"),
        "animated_gradients": ("linear-gradient", "radial-gradient", "background-size"),
    }
    polish_features = [
        feature
        for feature, signals in polish_patterns.items()
        if any(signal in normalized for signal in signals)
    ]

    return {
        "event_handlers": _limited_sorted_set(event_handlers, limit=16),
        "responsive_breakpoints": _limited_sorted_set(MEDIA_QUERY_RE.findall(combined), limit=12),
        "detected_features": detected_features[:24],
        "polish_features": polish_features[:16],
    }


def build_componentized_preview(
    code_dir: Path,
    *,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    package_json = code_dir / "package.json"
    if not package_json.exists():
        return {
            "status": "skipped",
            "reason": "package.json not found",
            "dist_index": None,
        }

    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    env = os.environ.copy()
    env.setdefault("CI", "1")
    npm_cache_dir = code_dir / ".npm-cache"
    npm_cache_dir.mkdir(parents=True, exist_ok=True)
    env.setdefault("npm_config_cache", str(npm_cache_dir))
    env.setdefault("NPM_CONFIG_CACHE", str(npm_cache_dir))

    commands: list[list[str]] = []
    install_required = not (code_dir / "node_modules").exists()
    if install_required:
        commands.append([npm_cmd, "install"])
    commands.append([npm_cmd, "run", "build"])

    logs: list[dict[str, Any]] = []
    try:
        for command in commands:
            completed = subprocess.run(
                command,
                cwd=code_dir,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=env,
                check=False,
            )
            logs.append(
                {
                    "command": command,
                    "returncode": completed.returncode,
                    "stdout": completed.stdout[-12_000:],
                    "stderr": completed.stderr[-12_000:],
                }
            )
            if completed.returncode != 0:
                if install_required and command[:2] == [npm_cmd, "install"] and "ERESOLVE" in (completed.stderr or ""):
                    retry_command = [npm_cmd, "install", "--legacy-peer-deps"]
                    retry = subprocess.run(
                        retry_command,
                        cwd=code_dir,
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds,
                        env=env,
                        check=False,
                    )
                    logs.append(
                        {
                            "command": retry_command,
                            "returncode": retry.returncode,
                            "stdout": retry.stdout[-12_000:],
                            "stderr": retry.stderr[-12_000:],
                        }
                    )
                    if retry.returncode == 0:
                        continue
                if command[:3] == [npm_cmd, "run", "build"] and _should_retry_with_vite_build(completed, code_dir):
                    retry_command = [npm_cmd, "exec", "vite", "build"]
                    retry = subprocess.run(
                        retry_command,
                        cwd=code_dir,
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds,
                        env=env,
                        check=False,
                    )
                    logs.append(
                        {
                            "command": retry_command,
                            "returncode": retry.returncode,
                            "stdout": retry.stdout[-12_000:],
                            "stderr": retry.stderr[-12_000:],
                        }
                    )
                    if retry.returncode == 0:
                        continue
                return {
                    "status": "error",
                    "reason": f"{' '.join(command)} failed",
                    "dist_index": None,
                    "logs": logs,
                }
    except FileNotFoundError:
        return {
            "status": "error",
            "reason": f"{npm_cmd} not found",
            "dist_index": None,
            "logs": logs,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "error",
            "reason": f"Build timed out after {timeout_seconds}s",
            "dist_index": None,
            "logs": logs + [{"command": exc.cmd, "returncode": None, "stdout": "", "stderr": "timeout"}],
        }

    dist_index = code_dir / "dist" / "index.html"
    if dist_index.exists():
        _make_dist_index_portable(dist_index)
    return {
        "status": "success" if dist_index.exists() else "error",
        "reason": None if dist_index.exists() else "dist/index.html not found after build",
        "dist_index": str(dist_index) if dist_index.exists() else None,
        "logs": logs,
    }


def _should_retry_with_vite_build(completed: subprocess.CompletedProcess[str], code_dir: Path) -> bool:
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    combined = f"{stdout}\n{stderr}"
    if "The TypeScript Compiler - Version" not in combined:
        return False
    if (code_dir / "tsconfig.json").exists():
        return False
    return True


def collect_componentized_editable_files(code_dir: Path) -> list[str]:
    editable_files: list[str] = []
    if not code_dir.exists():
        return editable_files

    for path in sorted(code_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(code_dir)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        name = path.name
        if name in NON_EDITABLE_COMPONENTIZED_FILENAMES:
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS and name not in TEXT_FILENAMES:
            continue
        editable_files.append(rel.as_posix())
    return editable_files


def collect_componentized_direct_dependencies(
    code_dir: Path,
    rel_paths: list[str],
    *,
    max_depth: int = 1,
) -> list[str]:
    root = code_dir.resolve()
    discovered: set[str] = set()
    pending: list[tuple[str, int]] = [
        (path.replace("\\", "/").strip("/"), 0) for path in rel_paths if path
    ]
    seen: set[str] = set()

    while pending:
        rel_path, depth = pending.pop(0)
        if rel_path in seen or depth >= max_depth:
            seen.add(rel_path)
            continue
        seen.add(rel_path)

        source_path = code_dir / rel_path
        if not source_path.exists() or not source_path.is_file():
            continue
        try:
            source = source_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for raw_import in _iter_local_import_specifiers(source):
            resolved_rel = _resolve_local_import_path(code_dir, rel_path, raw_import)
            if not resolved_rel or resolved_rel in seen:
                continue
            discovered.add(resolved_rel)
            pending.append((resolved_rel, depth + 1))

    return sorted(discovered)


def collect_componentized_reverse_dependents(
    code_dir: Path,
    rel_paths: list[str],
    *,
    max_depth: int = 1,
) -> list[str]:
    editable_files = collect_componentized_editable_files(code_dir)
    if not editable_files:
        return []

    frontier = {
        path.replace("\\", "/").strip("/")
        for path in rel_paths
        if path
    }
    discovered: set[str] = set()
    root = code_dir.resolve()

    depth = 0
    while frontier and depth < max_depth:
        next_frontier: set[str] = set()
        for rel_path in editable_files:
            normalized = rel_path.replace("\\", "/").strip("/")
            if normalized in frontier or normalized in discovered:
                continue
            source_path = code_dir / normalized
            if not source_path.exists() or not source_path.is_file():
                continue
            try:
                source = source_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            imported_paths: set[str] = set()
            for raw_import in _iter_local_import_specifiers(source):
                resolved_rel = _resolve_local_import_path(code_dir, normalized, raw_import)
                if not resolved_rel:
                    continue
                try:
                    (code_dir / resolved_rel).resolve().relative_to(root)
                except ValueError:
                    continue
                imported_paths.add(resolved_rel)

            if imported_paths.intersection(frontier):
                discovered.add(normalized)
                next_frontier.add(normalized)
        frontier = next_frontier
        depth += 1

    return sorted(discovered)


def _backfill_componentized_utility_classes(code_dir: Path) -> list[str]:
    base_css_path = code_dir / "src" / "base.css"
    if not base_css_path.exists():
        return []

    referenced_tokens: set[str] = set()
    for rel_path in collect_componentized_editable_files(code_dir):
        if not rel_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            continue
        path = code_dir / rel_path
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for token in COMPONENTIZED_UTILITY_FALLBACKS:
            if token in source:
                referenced_tokens.add(token)

    if not referenced_tokens:
        return []

    try:
        existing_css = base_css_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    block_lines: list[str] = []
    for token in sorted(referenced_tokens):
        selector = "." + token.replace("/", "\\/")
        if selector in existing_css:
            continue
        block_lines.append(f"{selector} {{ {COMPONENTIZED_UTILITY_FALLBACKS[token]} }}")

    if not block_lines:
        return []

    append_block = COMPONENTIZED_UTILITY_FALLBACK_MARKER + "\n" + "\n".join(block_lines) + "\n"
    updated_css = existing_css.rstrip() + "\n\n" + append_block
    base_css_path.write_text(updated_css, encoding="utf-8")
    return ["src/base.css"]


def rewrite_componentized_asset_api_urls(text: str) -> str:
    rewritten = API_ASSET_URL_RE.sub(lambda m: f"generated-assets/{Path(m.group(1)).name}", text)
    return _normalize_componentized_generated_asset_paths(rewritten)


def _normalize_componentized_generated_asset_paths(source: str) -> str:
    return re.sub(r'([("\'=\s])\/generated-assets\/', r"\1generated-assets/", source)


def _sync_componentized_generated_asset_references(code_dir: Path) -> list[str]:
    public_dir = code_dir / "public" / "generated-assets"
    if not public_dir.exists():
        return []

    existing_files = {
        path.name.lower(): path
        for path in public_dir.iterdir()
        if path.is_file()
    }
    if not existing_files:
        return []

    referenced: set[str] = set()
    for rel_path in collect_componentized_editable_files(code_dir):
        path = code_dir / rel_path
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        normalized = _normalize_componentized_generated_asset_paths(source)
        if normalized != source:
            path.write_text(normalized, encoding="utf-8")
        for match in GENERATED_ASSET_REFERENCE_RE.finditer(normalized):
            referenced.add(match.group("filename").strip())

    created_aliases: list[str] = []
    for filename in sorted(referenced):
        lowered = filename.lower()
        if lowered in existing_files:
            continue
        alias_source = _select_componentized_generated_asset_alias(filename, existing_files)
        if not alias_source:
            continue
        dest = public_dir / filename
        shutil.copy2(alias_source, dest)
        existing_files[lowered] = dest
        created_aliases.append(f"public/generated-assets/{filename}")
    return created_aliases


def _select_componentized_generated_asset_alias(
    filename: str,
    existing_files: dict[str, Path],
) -> Path | None:
    lowered = filename.lower()
    priority_groups = [
        ("map", "world", "atlas", "realm", "landscape", "background"),
        ("hero", "background", "banner"),
        ("portrait", "character", "monster", "tamer"),
        ("weapon", "device", "artifact", "gear"),
    ]
    for group in priority_groups:
        if not any(token in lowered for token in group):
            continue
        for existing_name, path in existing_files.items():
            if any(token in existing_name for token in group):
                return path
    return next(iter(existing_files.values()), None)


def _iter_local_import_specifiers(source: str) -> list[str]:
    imports: list[str] = []
    for match in LOCAL_REL_IMPORT_RE.finditer(source):
        specifier = (
            match.group("from")
            or match.group("dynamic")
            or match.group("bare")
            or ""
        ).strip()
        if specifier:
            imports.append(specifier.replace("\\", "/"))
    return imports


def _resolve_local_import_path(code_dir: Path, rel_path: str, specifier: str) -> str | None:
    source_dir = (code_dir / rel_path).parent
    raw_target = (source_dir / specifier).resolve()
    try:
        raw_target.relative_to(code_dir.resolve())
    except ValueError:
        return None

    candidates: list[Path] = [raw_target]
    if raw_target.suffix:
        if raw_target.suffix in TEXT_EXTENSIONS and raw_target.exists():
            return raw_target.relative_to(code_dir).as_posix()
    else:
        for suffix in (".ts", ".tsx", ".js", ".jsx", ".css"):
            candidates.append(raw_target.with_suffix(suffix))
        if raw_target.is_dir() or not raw_target.exists():
            for index_name in ("index.ts", "index.tsx", "index.js", "index.jsx", "index.css"):
                candidates.append(raw_target / index_name)

    root = code_dir.resolve()
    for candidate in candidates:
        try:
            candidate.resolve().relative_to(root)
        except ValueError:
            continue
        if candidate.exists() and candidate.is_file():
            return candidate.relative_to(code_dir).as_posix()
    return None


def stage_componentized_design_assets(version_dir: Path, design_assets: list[dict[str, Any]]) -> list[dict[str, str]]:
    public_dir = version_dir / "code" / "public" / "generated-assets"
    public_dir.mkdir(parents=True, exist_ok=True)

    staged_assets: list[dict[str, str]] = []
    for asset in design_assets:
        key = str(asset.get("key") or "asset").strip() or "asset"
        purpose = str(asset.get("purpose") or "Design asset").strip() or "Design asset"
        local_path = asset.get("local_path")
        if local_path:
            src = Path(local_path)
            if not src.is_absolute():
                src = (version_dir.parent.parent.parent / src).resolve()
            if src.exists() and src.is_file():
                suffix = src.suffix or ".png"
                filename = f"{key}{suffix.lower()}"
                dest = public_dir / filename
                shutil.copy2(src, dest)
                staged_assets.append({
                    "key": key,
                    "purpose": purpose,
                    "path": f"generated-assets/{filename}",
                })
                continue

        url = str(asset.get("url") or "").strip()
        if url:
            staged_assets.append({
                "key": key,
                "purpose": purpose,
                "path": url,
            })
    return staged_assets


def ensure_componentized_workspace_support(
    code_dir: Path,
    *,
    base_css_content: str | None = None,
    ui_archetype: str | None = None,
) -> dict[str, list[str]]:
    code_dir.mkdir(parents=True, exist_ok=True)

    created_files: list[str] = []
    rewritten_files: list[str] = []
    extracted_css_chunks: list[str] = []

    for rel_path, content in _componentized_support_files().items():
        target = code_dir / rel_path
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            created_files.append(rel_path)

    polish_created, polish_rewritten = _sync_componentized_polish_guard(
        code_dir,
        ui_archetype=ui_archetype,
    )
    created_files.extend(polish_created)
    rewritten_files.extend(polish_rewritten)

    if base_css_content:
        base_css_path = code_dir / "src" / "base.css"
        if not base_css_path.exists():
            base_css_path.parent.mkdir(parents=True, exist_ok=True)
            base_css_path.write_text(base_css_content, encoding="utf-8")
            created_files.append("src/base.css")
        else:
            original_base = base_css_path.read_text(encoding="utf-8", errors="replace")
            updated_base = _normalize_componentized_base_css(original_base, reference_css=base_css_content)
            if updated_base != original_base:
                base_css_path.write_text(updated_base, encoding="utf-8")
                rewritten_files.append("src/base.css")

        main_path = code_dir / "src" / "main.tsx"
        if main_path.exists():
            original_main = main_path.read_text(encoding="utf-8", errors="replace")
            updated_main = _normalize_componentized_main_entry(
                _ensure_css_import(original_main, './base.css')
            )
            if updated_main != original_main:
                main_path.write_text(updated_main, encoding="utf-8")
                rewritten_files.append("src/main.tsx")

    for rel_path in collect_componentized_editable_files(code_dir):
        path = code_dir / rel_path
        original = path.read_text(encoding="utf-8", errors="replace")
        updated = _normalize_componentized_file(rel_path, original)
        if rel_path.endswith((".tsx", ".jsx")):
            updated, extracted_css = _extract_componentized_css_tail(updated)
            if extracted_css:
                extracted_css_chunks.append(extracted_css)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            rewritten_files.append(rel_path)

    if extracted_css_chunks:
        index_css_path = code_dir / "src" / "index.css"
        index_css_path.parent.mkdir(parents=True, exist_ok=True)
        existing_css = index_css_path.read_text(encoding="utf-8", errors="replace") if index_css_path.exists() else ""
        appended_css = "\n\n".join(chunk.strip() for chunk in extracted_css_chunks if chunk.strip()).strip()
        if appended_css:
            combined_css = existing_css.rstrip() + ("\n\n" if existing_css.strip() else "") + appended_css + "\n"
            index_css_path.write_text(combined_css, encoding="utf-8")
            if "src/index.css" not in rewritten_files:
                rewritten_files.append("src/index.css")

    created_files.extend(_backfill_missing_local_css_imports(code_dir))
    created_files.extend(_sync_componentized_generated_asset_references(code_dir))
    rewritten_files.extend(_normalize_componentized_design_overrides(code_dir))
    rewritten_files.extend(_backfill_componentized_utility_classes(code_dir))

    synced_dependencies = _sync_componentized_package_dependencies(code_dir)
    if synced_dependencies:
        rewritten_files.append("package.json")

    return {
        "created_files": created_files,
        "rewritten_files": rewritten_files,
    }


def summarize_componentized_build_error(build_result: dict[str, Any], *, max_chars: int = 4000) -> str:
    if not build_result:
        return "No build logs were captured."

    chunks: list[str] = []
    reason = str(build_result.get("reason") or "").strip()
    if reason:
        chunks.append(f"Reason: {reason}")

    for log in (build_result.get("logs") or [])[-3:]:
        command = " ".join(log.get("command") or [])
        stdout = str(log.get("stdout") or "").strip()
        stderr = str(log.get("stderr") or "").strip()
        block = [f"$ {command}"]
        if stdout:
            block.append(stdout[-1500:])
        if stderr:
            block.append(stderr[-1500:])
        chunks.append("\n".join(block))

    summary = "\n\n".join(chunks).strip()
    if len(summary) > max_chars:
        summary = summary[-max_chars:]
    return summary or "No build logs were captured."


def relative_mount_root(code_dir: Path, target: Path) -> str:
    rel_parent = target.relative_to(code_dir).parent.as_posix()
    return "" if rel_parent == "." else rel_parent


def rewrite_preview_file_references(
    html: str,
    *,
    mount_prefix: str,
    root_dir: str,
) -> str:
    def _src_href_repl(match: re.Match[str]) -> str:
        prefix, raw_path, suffix = match.groups()
        value = raw_path.strip()
        lower = value.lower()
        if lower.startswith(("http://", "https://", "data:", "mailto:", "tel:", "#", "/api/", "/published/")):
            return match.group(0)
        if lower.endswith((".css", ".js", ".mjs", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
            normalized = _normalize_asset_path(value, root_dir)
            return f"{prefix}{mount_prefix}/{normalized}{suffix}"
        return match.group(0)

    html = re.sub(r'((?:src|href)=["\'])([^"\']+)(["\'])', _src_href_repl, html, flags=re.IGNORECASE)

    html = re.sub(
        r'(url\(["\']?)(/assets/[^)"\']+)(["\']?\))',
        lambda m: f"{m.group(1)}{mount_prefix}/{_normalize_asset_path(m.group(2), root_dir)}{m.group(3)}",
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r'(url\(["\']?)(?:\./|\.\./)?([^)"\']+\.(?:png|jpg|jpeg|gif|webp|svg|ico|css|js|mjs))(["\']?\))',
        lambda m: f"{m.group(1)}{mount_prefix}/{_normalize_asset_path(m.group(2), root_dir)}{m.group(3)}",
        html,
        flags=re.IGNORECASE,
    )
    return html


def rewrite_preview_runtime_asset_references(
    content: str,
    *,
    mount_prefix: str,
    root_dir: str,
) -> str:
    normalized_root = f"{mount_prefix}/{root_dir}".strip("/")
    if not normalized_root:
        return content

    def _repl(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        subpath = match.group("subpath").lstrip("/")
        return f"{prefix}/{normalized_root}/generated-assets/{subpath}"

    return RUNTIME_GENERATED_ASSET_REFERENCE_RE.sub(_repl, content)


def _normalize_asset_path(raw_path: str, root_dir: str) -> str:
    value = raw_path.split("?", 1)[0].split("#", 1)[0]
    if value.startswith("/assets/"):
        prefix = f"{root_dir}/" if root_dir else ""
        return f"{prefix}{value.lstrip('/')}".strip("/")
    if value.startswith("/"):
        prefix = f"{root_dir}/" if root_dir else ""
        return f"{prefix}{value.lstrip('/')}".strip("/")

    value = value.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    while value.startswith("../"):
        value = value[3:]

    if root_dir:
        return f"{root_dir}/{value}".strip("/")
    return value.strip("/")


def write_preview_build_manifest(version_dir: Path, data: dict[str, Any]) -> None:
    path = version_dir / "last_preview_build.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _componentized_support_files() -> dict[str, str]:
    scaffold = build_vite_react_ts_scaffold(app_dir="componentized-support").files
    prefix = "componentized-support/"
    keep = {
        "package.json",
        "index.html",
        "vite.config.ts",
        "tsconfig.json",
        "tsconfig.node.json",
        "src/main.tsx",
        "src/App.tsx",
        "src/vite-env.d.ts",
        "src/index.css",
    }
    files: dict[str, str] = {}
    for path, content in scaffold.items():
        normalized = path.replace("\\", "/")
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
        if normalized in keep:
            files[normalized] = content

    files["src/index.css"] = "/* App-specific overrides live here. Keep this file intentionally minimal. */\n"

    files["public/vite.svg"] = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">'
        '<rect width="64" height="64" rx="16" fill="#111827"/>'
        '<path d="M18 44L32 14L46 44H38L32 30L26 44H18Z" fill="#10B981"/>'
        "</svg>\n"
    )
    return files


def _backfill_missing_local_css_imports(code_dir: Path) -> list[str]:
    created: list[str] = []
    for rel_path in collect_componentized_editable_files(code_dir):
        if not rel_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            continue
        source_path = code_dir / rel_path
        try:
            source = source_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for raw_import in LOCAL_CSS_IMPORT_RE.findall(source):
            import_path = raw_import.replace("\\", "/")
            target = (source_path.parent / import_path).resolve()
            try:
                target.relative_to(code_dir.resolve())
            except ValueError:
                continue
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("/* Generated fallback stylesheet to satisfy a referenced local CSS import. */\n", encoding="utf-8")
            created.append(target.relative_to(code_dir).as_posix())
    return created


def _ensure_css_import(source: str, import_path: str) -> str:
    return _ensure_main_side_effect_import(source, import_path)


def _ensure_main_side_effect_import(source: str, import_path: str) -> str:
    import_line_variants = {f'import "{import_path}";', f"import '{import_path}';"}
    if any(line.strip() in import_line_variants for line in source.splitlines()):
        return source
    lines = source.splitlines()
    import_line = f'import "{import_path}";'
    insert_at = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import "):
            insert_at = idx + 1
    lines.insert(insert_at, import_line)
    return "\n".join(lines) + ("\n" if source.endswith("\n") else "")


def _remove_css_import(source: str, import_path: str) -> str:
    return _remove_main_side_effect_import(source, import_path)


def _remove_main_side_effect_import(source: str, import_path: str) -> str:
    lines = source.splitlines()
    filtered = [
        line
        for line in lines
        if line.strip() not in {f'import "{import_path}";', f"import '{import_path}';"}
    ]
    if filtered == lines:
        return source
    return "\n".join(filtered).rstrip() + "\n"


def _normalize_componentized_file(rel_path: str, source: str) -> str:
    updated = rewrite_componentized_asset_api_urls(source)

    if rel_path == "index.html":
        updated = _normalize_componentized_index_html(updated)
    elif rel_path == "package.json":
        updated = _normalize_componentized_package_json(updated)
    elif rel_path in {"tsconfig.json", "tsconfig.node.json"}:
        updated = _normalize_componentized_tsconfig(updated)
    elif rel_path == "src/index.css":
        updated = _normalize_componentized_index_css(updated)
        updated = _repair_componentized_css_data_uri_quote_bleed(updated)
    elif rel_path.endswith(".css"):
        updated = _repair_componentized_css_data_uri_quote_bleed(updated)
    elif rel_path.endswith((".ts", ".tsx", ".js", ".jsx")):
        updated = LOCAL_CODE_IMPORT_RE.sub(r"\1\2\4", updated)
        updated = _normalize_componentized_field_aliases(updated)
        updated = _repair_interface_field_comment_bleed(updated)
        updated = _repair_inline_block_comment_code_bleed(updated)
        updated = _repair_block_comment_control_flow_bleed(updated)
        updated = _repair_unterminated_block_comment_line_notes(updated)
        updated = _repair_inline_block_comment_continuations(updated)
        updated = _normalize_run_on_inline_comments(updated)
        updated = _repair_componentized_comment_split_identifiers(updated)
        updated = _repair_componentized_jsx_block_comment_bleed(updated)
        updated = _repair_componentized_jsx_text_comment_bleed(updated)
        updated = _repair_componentized_orphan_comment_split_identifiers(updated)
        updated = _repair_componentized_orphan_comment_split_string_literals(updated)
        updated = _normalize_componentized_void_jsx_elements(updated)
        updated = _normalize_componentized_declaration_boundaries(updated)
        updated = _hoist_componentized_chart_helper_declarations(updated)
        updated = _normalize_run_on_natural_language_notes(updated)
        updated = _normalize_lowercase_object_field_labels(updated)
        updated = _normalize_run_on_explanatory_labels(updated)
        updated = _normalize_bare_section_labels(updated)
        updated = _repair_componentized_jsx_event_handler_arrow_bleed(updated)
        updated = _repair_componentized_comment_url_bleed(updated)
        updated = _normalize_run_on_imports(updated)
        updated = _normalize_componentized_currency_formatting(updated)
        if rel_path.replace("\\", "/") == "src/main.tsx":
            updated = _normalize_componentized_main_entry(updated)
            updated = _ensure_css_import(updated, "./base.css")
            updated = _normalize_componentized_main_entry(updated)
        elif "base.css" in updated:
            updated = BASE_CSS_IMPORT_ANY_RE.sub("", updated)
            updated = BASE_CSS_IMPORT_LINE_RE.sub("", updated)

    return updated


def _normalize_componentized_package_json(source: str) -> str:
    candidate = _repair_json_escape_noise(source)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return candidate

    if not isinstance(data, dict):
        return candidate

    scripts = data.setdefault("scripts", {})
    if isinstance(scripts, dict):
        build_value = str(scripts.get("build") or "").strip()
        if not build_value or "tsc" in build_value:
            scripts["build"] = "vite build"
        scripts.setdefault("dev", "vite")
        scripts.setdefault("preview", "vite preview")

    normalized = json.dumps(data, indent=2, ensure_ascii=False)
    return normalized + "\n"


def _repair_json_escape_noise(source: str) -> str:
    if "\\n" not in source and "\\r" not in source and "\\t" not in source:
        return source

    repaired: list[str] = []
    in_string = False
    escaped = False
    idx = 0
    while idx < len(source):
        char = source[idx]
        if in_string:
            repaired.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            idx += 1
            continue

        if char == '"':
            in_string = True
            repaired.append(char)
            idx += 1
            continue

        if char == "\\" and idx + 1 < len(source):
            next_char = source[idx + 1]
            if next_char in {"n", "r"}:
                repaired.append("\n")
                idx += 2
                continue
            if next_char == "t":
                repaired.append("\t")
                idx += 2
                continue

        repaired.append(char)
        idx += 1

    repaired_source = "".join(repaired)
    if repaired_source == source and JSON_ESCAPE_NOISE_RE.search(source):
        return source.replace("\\n", "\n").replace("\\r", "\n").replace("\\t", "\t")
    return repaired_source


def _sync_componentized_package_dependencies(code_dir: Path) -> list[str]:
    package_json_path = code_dir / "package.json"
    if not package_json_path.exists():
        return []

    try:
        data = json.loads(package_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, dict):
        return []

    dependencies = data.setdefault("dependencies", {})
    dev_dependencies = data.setdefault("devDependencies", {})
    if not isinstance(dependencies, dict) or not isinstance(dev_dependencies, dict):
        return []

    detected_packages: set[str] = set()
    for rel_path in collect_componentized_editable_files(code_dir):
        if not rel_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            continue
        path = code_dir / rel_path
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in PACKAGE_IMPORT_RE.finditer(source):
            specifier = match.group(1).strip()
            if not specifier or specifier.startswith((".", "/", "node:")):
                continue
            package_name = _root_package_name(specifier)
            if package_name in SAFE_COMPONENTIZED_DEPENDENCIES:
                detected_packages.add(package_name)

    added: list[str] = []
    for package_name in sorted(detected_packages):
        if package_name in dependencies or package_name in dev_dependencies:
            continue
        dependencies[package_name] = SAFE_COMPONENTIZED_DEPENDENCIES[package_name]
        added.append(package_name)

    if not added:
        return []

    normalized = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    package_json_path.write_text(normalized, encoding="utf-8")
    return added


def _normalize_componentized_tsconfig(source: str) -> str:
    try:
        data = json.loads(source)
    except json.JSONDecodeError:
        return source

    if not isinstance(data, dict):
        return source

    compiler_options = data.setdefault("compilerOptions", {})
    if isinstance(compiler_options, dict):
        compiler_options["noUnusedLocals"] = False
        compiler_options["noUnusedParameters"] = False
        compiler_options.setdefault("allowImportingTsExtensions", True)

    normalized = json.dumps(data, indent=2, ensure_ascii=False)
    return normalized + "\n"


def _normalize_componentized_index_css(source: str) -> str:
    stripped = source.strip()
    if (
        "font-family: system-ui" in stripped
        and ".page {" in stripped
        and ".card {" in stripped
    ):
        return "/* App-specific overrides live here. Keep this file intentionally minimal. */\n"
    updated = re.sub(r"^\s*@extend\s+[^;]+;\s*$\n?", "", source, flags=re.MULTILINE)
    return updated


def _normalize_componentized_design_overrides(code_dir: Path) -> list[str]:
    base_css_path = code_dir / "src" / "base.css"
    if not base_css_path.exists():
        return []

    try:
        base_css = base_css_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    base_lower = base_css.lower()
    has_display_font = "space grotesk" in base_lower or "outfit" in base_lower
    has_mono_font = "jetbrains mono" in base_lower
    if not has_display_font and not has_mono_font:
        return []

    rewritten: list[str] = []
    for rel_path in collect_componentized_editable_files(code_dir):
        normalized = rel_path.replace("\\", "/")
        if not normalized.endswith(".css") or normalized == "src/base.css":
            continue
        if normalized not in {"src/index.css", "src/style.css", "src/styles.css"} and not normalized.startswith("src/styles/"):
            continue

        path = code_dir / normalized
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        updated = _normalize_componentized_override_css(
            source,
            has_display_font=has_display_font,
            has_mono_font=has_mono_font,
        )
        if updated != source:
            path.write_text(updated, encoding="utf-8")
            rewritten.append(normalized)

    return rewritten


def _sync_componentized_polish_guard(
    code_dir: Path,
    *,
    ui_archetype: str | None,
) -> tuple[list[str], list[str]]:
    normalized_archetype = (ui_archetype or "").strip().lower()
    guard_path = code_dir / "src" / "polish-guard.css"
    runtime_path = code_dir / "src" / "polish-guard.ts"
    main_path = code_dir / "src" / "main.tsx"
    target_css = _build_componentized_polish_guard_css(normalized_archetype)
    target_runtime = _build_componentized_polish_guard_runtime(normalized_archetype)
    created_files: list[str] = []
    rewritten_files: list[str] = []

    if target_css is None:
        if guard_path.exists():
            guard_path.unlink()
            rewritten_files.append("src/polish-guard.css")
        if runtime_path.exists():
            runtime_path.unlink()
            rewritten_files.append("src/polish-guard.ts")
        if main_path.exists():
            original_main = main_path.read_text(encoding="utf-8", errors="replace")
            updated_main = _normalize_componentized_main_entry(
                _remove_main_side_effect_import(
                    _remove_css_import(original_main, POLISH_GUARD_IMPORT),
                    POLISH_GUARD_RUNTIME_IMPORT,
                )
            )
            if updated_main != original_main:
                main_path.write_text(updated_main, encoding="utf-8")
                rewritten_files.append("src/main.tsx")
        return created_files, rewritten_files

    guard_path.parent.mkdir(parents=True, exist_ok=True)
    if not guard_path.exists():
        guard_path.write_text(target_css, encoding="utf-8")
        created_files.append("src/polish-guard.css")
    else:
        original_css = guard_path.read_text(encoding="utf-8", errors="replace")
        if original_css != target_css:
            guard_path.write_text(target_css, encoding="utf-8")
            rewritten_files.append("src/polish-guard.css")

    if target_runtime is not None:
        if not runtime_path.exists():
            runtime_path.write_text(target_runtime, encoding="utf-8")
            created_files.append("src/polish-guard.ts")
        else:
            original_runtime = runtime_path.read_text(encoding="utf-8", errors="replace")
            if original_runtime != target_runtime:
                runtime_path.write_text(target_runtime, encoding="utf-8")
                rewritten_files.append("src/polish-guard.ts")

    if main_path.exists():
        original_main = main_path.read_text(encoding="utf-8", errors="replace")
        updated_main = _normalize_componentized_main_entry(
            _ensure_css_import(
                _ensure_main_side_effect_import(original_main, POLISH_GUARD_RUNTIME_IMPORT),
                POLISH_GUARD_IMPORT,
            )
        )
        if updated_main != original_main:
            main_path.write_text(updated_main, encoding="utf-8")
            rewritten_files.append("src/main.tsx")

    return created_files, rewritten_files


def _build_componentized_polish_guard_css(ui_archetype: str) -> str | None:
    if ui_archetype not in POLISH_GUARD_ARCHETYPES:
        return None

    if ui_archetype == "fintech":
        accent_glow = "rgba(24, 144, 255, 0.32)"
        accent_soft = "rgba(78, 168, 255, 0.16)"
        topbar_tint = "rgba(8, 14, 24, 0.82)"
        body_gradient = (
            "radial-gradient(circle at top right, rgba(0, 122, 255, 0.16), transparent 28%),\n"
            "    radial-gradient(circle at bottom left, rgba(26, 188, 156, 0.1), transparent 22%),"
        )
    else:
        accent_glow = "rgba(79, 144, 255, 0.28)"
        accent_soft = "rgba(79, 144, 255, 0.14)"
        topbar_tint = "rgba(7, 12, 20, 0.78)"
        body_gradient = (
            "radial-gradient(circle at top right, rgba(61, 117, 255, 0.16), transparent 26%),\n"
            "    radial-gradient(circle at bottom left, rgba(15, 193, 132, 0.08), transparent 24%),"
        )

    return (
        f"/* Runtime shell polish guard for {ui_archetype} app shells. */\n"
        ":root {\n"
        "  color-scheme: dark;\n"
        "  --guard-surface: rgba(255, 255, 255, 0.02);\n"
        "  --guard-border-strong: rgba(255, 255, 255, 0.09);\n"
        f"  --guard-accent-soft: {accent_soft};\n"
        f"  --guard-accent-glow: {accent_glow};\n"
        "  --guard-shadow-card: 0 18px 40px rgba(3, 8, 18, 0.34), 0 4px 14px rgba(3, 8, 18, 0.22);\n"
        "  --guard-shadow-elevated: 0 22px 50px rgba(2, 6, 23, 0.42), 0 8px 18px rgba(2, 6, 23, 0.24);\n"
        "  --guard-kpi-accent-a: rgba(79, 144, 255, 0.82);\n"
        "  --guard-kpi-accent-b: rgba(16, 185, 129, 0.8);\n"
        "  --guard-kpi-accent-c: rgba(255, 191, 87, 0.8);\n"
        "  --guard-kpi-accent-d: rgba(248, 113, 113, 0.76);\n"
        "  --guard-chart-accent: rgba(79, 144, 255, 0.82);\n"
        "  --guard-activity-accent: rgba(16, 185, 129, 0.8);\n"
        "  --guard-table-accent: rgba(255, 191, 87, 0.78);\n"
        "}\n\n"
        "body {\n"
        f"  background: {body_gradient}\n"
        "    var(--bg, #0a1018) !important;\n"
        "}\n\n"
        ".fintech-shell,\n"
        ".dashboard-shell,\n"
        ".main-content,\n"
        ".content-area {\n"
        "  position: relative;\n"
        "}\n\n"
        ".guard-fixed-sidebar-shell {\n"
        "  display: grid !important;\n"
        "  grid-template-columns: var(--guard-sidebar-offset, 240px) minmax(0, 1fr) !important;\n"
        "  align-items: start !important;\n"
        "}\n\n"
        ".guard-fixed-sidebar-shell > .main-content,\n"
        ".guard-fixed-sidebar-shell > .content-area,\n"
        ".guard-fixed-sidebar-shell > .dashboard-main,\n"
        ".guard-fixed-sidebar-shell > .workspace-main,\n"
        ".guard-fixed-sidebar-shell > main {\n"
        "  grid-column: 2 / -1 !important;\n"
        "  min-width: 0 !important;\n"
        "  width: auto !important;\n"
        "}\n\n"
        ".guard-fixed-sidebar-shell > .main-content {\n"
        "  margin-left: 0 !important;\n"
        "}\n\n"
        ".guard-fixed-sidebar-shell .content-area,\n"
        ".guard-fixed-sidebar-shell .dashboard-main,\n"
        ".guard-fixed-sidebar-shell .workspace-main,\n"
        ".guard-fixed-sidebar-shell .kpi-grid,\n"
        ".guard-fixed-sidebar-shell .data-table-wrapper,\n"
        ".guard-fixed-sidebar-shell .chart-card {\n"
        "  min-width: 0 !important;\n"
        "  width: 100% !important;\n"
        "}\n\n"
        ".guard-fixed-sidebar-shell .kpi-grid {\n"
        "  grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr)) !important;\n"
        "}\n\n"
        ".guard-fixed-sidebar-shell .grid-2col,\n"
        ".guard-fixed-sidebar-shell .content-grid,\n"
        ".guard-fixed-sidebar-shell .dashboard-grid {\n"
        "  grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.96fr) !important;\n"
        "  align-items: start !important;\n"
        "}\n\n"
        "@media (max-width: 1080px) {\n"
        "  .guard-fixed-sidebar-shell .grid-2col,\n"
        "  .guard-fixed-sidebar-shell .content-grid,\n"
        "  .guard-fixed-sidebar-shell .dashboard-grid {\n"
        "    grid-template-columns: 1fr !important;\n"
        "  }\n"
        "}\n\n"
        ".topbar,\n"
        ".header-bar,\n"
        ".sidebar {\n"
        f"  background: linear-gradient(180deg, {topbar_tint}, rgba(8, 12, 18, 0.9)) !important;\n"
        "  backdrop-filter: blur(18px);\n"
        "  border-color: var(--guard-border-strong) !important;\n"
        "}\n\n"
        "h1,\n"
        ".h1,\n"
        "h2,\n"
        ".h2,\n"
        "h3,\n"
        ".h3,\n"
        ".page-title,\n"
        ".panel-title,\n"
        ".chart-title,\n"
        ".topbar-brand,\n"
        ".logo-text,\n"
        ".sidebar-group-label,\n"
        ".feed-header {\n"
        "  font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif) !important;\n"
        "}\n\n"
        "h1,\n"
        ".h1,\n"
        ".page-title,\n"
        ".topbar-brand,\n"
        ".logo-text {\n"
        "  letter-spacing: -0.04em;\n"
        "}\n\n"
        "h1,\n"
        ".h1,\n"
        ".page-title {\n"
        "  font-size: clamp(2.45rem, 2.25vw + 1.32rem, 3.45rem) !important;\n"
        "  line-height: 1.04 !important;\n"
        "}\n\n"
        ".page-title,\n"
        ".feed-header {\n"
        "  font-weight: 700 !important;\n"
        "}\n\n"
        "h2,\n"
        ".h2 {\n"
        "  font-size: clamp(1.45rem, 1vw + 1.05rem, 2.05rem) !important;\n"
        "  line-height: 1.14 !important;\n"
        "}\n\n"
        "h3,\n"
        ".h3,\n"
        ".panel-title {\n"
        "  font-size: clamp(1.02rem, 0.52vw + 0.96rem, 1.34rem) !important;\n"
        "  line-height: 1.24 !important;\n"
        "}\n\n"
        ".topbar-brand,\n"
        ".logo-text {\n"
        "  font-size: clamp(1.1rem, 0.7vw + 0.95rem, 1.45rem) !important;\n"
        "  font-weight: 700 !important;\n"
        "}\n\n"
        ".kpi-value,\n"
        ".kpi-delta,\n"
        ".ticker-price,\n"
        ".ticker-delta,\n"
        ".watchlist-price,\n"
        ".watchlist-delta,\n"
        ".watch-price,\n"
        ".watch-delta,\n"
        ".news-feed-time,\n"
        ".text-mono,\n"
        ".table-cell,\n"
        ".guard-mono-count,\n"
        ".portfolio-value .value-amount,\n"
        ".chart-axis-label,\n"
        ".candlestick-chart-svg text,\n"
        "svg text.text-mono,\n"
        ".feed-time,\n"
        ".asset-table td,\n"
        ".data-table td,\n"
        ".table-number,\n"
        ".numeric,\n"
        ".numeric-value,\n"
        ".price,\n"
        ".delta {\n"
        "  font-family: var(--font-mono, 'JetBrains Mono', monospace) !important;\n"
        "  font-variant-numeric: tabular-nums !important;\n"
        "}\n\n"
        ".kpi-card,\n"
        ".panel,\n"
        ".card,\n"
        ".chart-card,\n"
        ".ticker-card,\n"
        ".watchlist-feed-panel,\n"
        ".watchlist-panel,\n"
        ".news-feed-panel,\n"
        ".news-feed-section,\n"
        ".news-feed-item,\n"
        ".activity-feed,\n"
        ".asset-table-panel,\n"
        ".data-table-wrapper,\n"
        ".data-table,\n"
        ".sidebar-item.active {\n"
        "  border-color: var(--guard-border-strong) !important;\n"
        "  box-shadow: var(--guard-shadow-card) !important;\n"
        "}\n\n"
        ".kpi-card,\n"
        ".panel,\n"
        ".chart-card,\n"
        ".ticker-card,\n"
        ".watchlist-feed-panel,\n"
        ".watchlist-panel,\n"
        ".news-feed-panel,\n"
        ".news-feed-section,\n"
        ".news-feed-item,\n"
        ".asset-table-panel,\n"
        ".data-table-wrapper,\n"
        ".data-table {\n"
        "  background: linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.012)),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".kpi-card:nth-child(4n + 1) {\n"
        "  --guard-panel-accent: var(--guard-kpi-accent-a);\n"
        "  background: linear-gradient(160deg, rgba(79, 144, 255, 0.13), rgba(255, 255, 255, 0.012) 44%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".kpi-card:nth-child(4n + 2) {\n"
        "  --guard-panel-accent: var(--guard-kpi-accent-b);\n"
        "  background: linear-gradient(160deg, rgba(16, 185, 129, 0.12), rgba(255, 255, 255, 0.012) 46%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".kpi-card:nth-child(4n + 3) {\n"
        "  --guard-panel-accent: var(--guard-kpi-accent-c);\n"
        "  background: linear-gradient(160deg, rgba(255, 191, 87, 0.12), rgba(255, 255, 255, 0.012) 46%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".kpi-card:nth-child(4n) {\n"
        "  --guard-panel-accent: var(--guard-kpi-accent-d);\n"
        "  background: linear-gradient(160deg, rgba(248, 113, 113, 0.1), rgba(255, 255, 255, 0.012) 44%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".kpi-card.elevated {\n"
        "  box-shadow: var(--guard-shadow-elevated) !important;\n"
        "}\n\n"
        ".chart-card,\n"
        ".chart-panel,\n"
        ".performance-panel,\n"
        ".hero-chart {\n"
        "  --guard-panel-accent: var(--guard-chart-accent);\n"
        "  background: linear-gradient(158deg, rgba(79, 144, 255, 0.13), rgba(255, 255, 255, 0.014) 46%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".activity-feed,\n"
        ".activity-panel,\n"
        ".activity-feed-card,\n"
        ".timeline-panel {\n"
        "  --guard-panel-accent: var(--guard-activity-accent);\n"
        "  background: linear-gradient(162deg, rgba(16, 185, 129, 0.13), rgba(255, 255, 255, 0.016) 46%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".data-table-wrapper,\n"
        ".asset-table-panel,\n"
        ".table-panel,\n"
        ".holdings-panel,\n"
        ".positions-panel {\n"
        "  --guard-panel-accent: var(--guard-table-accent);\n"
        "  background: linear-gradient(166deg, rgba(255, 191, 87, 0.13), rgba(255, 255, 255, 0.014) 45%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".watchlist-feed-panel,\n"
        ".watchlist-panel,\n"
        ".watchlist-card,\n"
        ".activity-feed,\n"
        ".activity-panel,\n"
        ".alerts-panel,\n"
        ".alert-panel {\n"
        "  background: linear-gradient(160deg, rgba(87, 153, 255, 0.12), rgba(255, 255, 255, 0.016) 42%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".news-feed-panel,\n"
        ".news-feed-section,\n"
        ".news-panel,\n"
        ".briefing-panel {\n"
        "  background: linear-gradient(160deg, rgba(255, 191, 87, 0.12), rgba(255, 255, 255, 0.016) 44%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".kpi-card:hover,\n"
        ".panel:hover,\n"
        ".chart-card:hover,\n"
        ".ticker-card:hover,\n"
        ".news-feed-item:hover,\n"
        ".card:hover {\n"
        "  transform: translateY(-3px);\n"
        "  box-shadow: var(--guard-shadow-elevated) !important;\n"
        "}\n\n"
        ".kpi-card::before,\n"
        ".panel::before,\n"
        ".news-feed-item::before,\n"
        ".chart-card::before {\n"
        "  content: \"\";\n"
        "  position: absolute;\n"
        "  inset: 0;\n"
        "  border-radius: inherit;\n"
        "  pointer-events: none;\n"
        "  background: linear-gradient(180deg, rgba(255, 255, 255, 0.045), transparent 30%);\n"
        "  opacity: 0.55;\n"
        "}\n\n"
        ".kpi-card,\n"
        ".panel,\n"
        ".news-feed-item,\n"
        ".chart-card,\n"
        ".activity-feed,\n"
        ".activity-panel,\n"
        ".activity-feed-card,\n"
        ".data-table-wrapper,\n"
        ".asset-table-panel,\n"
        ".table-panel,\n"
        ".holdings-panel,\n"
        ".positions-panel {\n"
        "  position: relative;\n"
        "  overflow: hidden;\n"
        "  isolation: isolate;\n"
        "}\n\n"
        ".kpi-card::after,\n"
        ".chart-card::after,\n"
        ".chart-panel::after,\n"
        ".performance-panel::after,\n"
        ".hero-chart::after,\n"
        ".activity-feed::after,\n"
        ".activity-panel::after,\n"
        ".activity-feed-card::after,\n"
        ".timeline-panel::after,\n"
        ".data-table-wrapper::after,\n"
        ".asset-table-panel::after,\n"
        ".table-panel::after,\n"
        ".holdings-panel::after,\n"
        ".positions-panel::after {\n"
        "  content: \"\";\n"
        "  position: absolute;\n"
        "  inset: 0 0 auto 0;\n"
        "  height: 3px;\n"
        "  background: linear-gradient(90deg, var(--guard-panel-accent, rgba(255, 255, 255, 0.38)), transparent 82%);\n"
        "  opacity: 0.98;\n"
        "  pointer-events: none;\n"
        "}\n\n"
        ".kpi-value {\n"
        "  font-size: clamp(2rem, 1vw + 1.6rem, 2.9rem) !important;\n"
        "  letter-spacing: -0.05em !important;\n"
        "}\n\n"
        ".kpi-label,\n"
        ".data-table th,\n"
        ".asset-table th,\n"
        ".sidebar-group-label,\n"
        ".value-label {\n"
        "  text-transform: uppercase;\n"
        "  letter-spacing: 0.09em !important;\n"
        "}\n\n"
        ".asset-table thead th,\n"
        ".data-table thead th {\n"
        "  background: rgba(255, 255, 255, 0.02);\n"
        "}\n\n"
        ".asset-table tbody tr:hover,\n"
        ".data-table tbody tr:hover,\n"
        ".watch-item:hover,\n"
        ".feed-item:hover {\n"
        "  background: rgba(255, 255, 255, 0.025);\n"
        "}\n\n"
        ".primary-btn,\n"
        ".chart-period-btn.active,\n"
        ".range-pill.active,\n"
        ".interactive-chip,\n"
        ".chart-action-btn,\n"
        ".asset-table-action-btn,\n"
        ".guard-accent-action,\n"
        ".guard-tonal-action,\n"
        ".sidebar-item.active,\n"
        ".status-chip,\n"
        ".market-pill {\n"
        "  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.04), 0 10px 20px rgba(2, 6, 23, 0.22);\n"
        "}\n\n"
        ".primary-btn,\n"
        ".chart-period-btn.active,\n"
        ".range-pill.active,\n"
        ".interactive-chip,\n"
        ".chart-action-btn,\n"
        ".asset-table-action-btn,\n"
        ".guard-accent-action {\n"
        "  background: linear-gradient(135deg, rgba(var(--accent-rgb, 16, 185, 129), 0.24), var(--guard-accent-soft)) !important;\n"
        "  border-color: rgba(var(--accent-rgb, 16, 185, 129), 0.32) !important;\n"
        "  color: var(--text, #f8fafc) !important;\n"
        "}\n\n"
        ".guard-tonal-action {\n"
        "  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.028)) !important;\n"
        "  border-color: rgba(255, 255, 255, 0.12) !important;\n"
        "  color: var(--text, #f8fafc) !important;\n"
        "}\n\n"
        ".activity-feed,\n"
        ".watchlist-card,\n"
        ".watchlist-panel {\n"
        "  overflow: hidden;\n"
        "}\n\n"
        ".activity-feed .feed-header,\n"
        ".watchlist-card .feed-header,\n"
        ".watchlist-panel .feed-header {\n"
        "  background: linear-gradient(180deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));\n"
        "  border-bottom-color: rgba(255, 255, 255, 0.08) !important;\n"
        "}\n\n"
        ".activity-feed {\n"
        "  display: grid;\n"
        "  gap: 0.95rem;\n"
        "}\n\n"
        ".activity-feed > div {\n"
        "  display: grid;\n"
        "  gap: 0.78rem;\n"
        "}\n\n"
        ".activity-item,\n"
        ".watchlist-item,\n"
        ".feed-item {\n"
        "  position: relative;\n"
        "  transition: transform 160ms ease, background 160ms ease, box-shadow 160ms ease !important;\n"
        "}\n\n"
        ".activity-item {\n"
        "  display: grid;\n"
        "  grid-template-columns: auto minmax(0, 1fr);\n"
        "  gap: 0.85rem;\n"
        "  align-items: start;\n"
        "  padding: 1rem 1.05rem;\n"
        "  border-radius: 18px;\n"
        "  background: linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.012));\n"
        "}\n\n"
        ".activity-item > div:last-child {\n"
        "  min-width: 0;\n"
        "  display: grid;\n"
        "  gap: 0.34rem;\n"
        "}\n\n"
        ".activity-item:hover,\n"
        ".watchlist-item:hover,\n"
        ".feed-item:hover {\n"
        "  transform: translateX(2px);\n"
        "  box-shadow: inset 2px 0 0 rgba(var(--accent-rgb, 16, 185, 129), 0.55);\n"
        "}\n\n"
        ".activity-item .activity-text {\n"
        "  line-height: 1.58 !important;\n"
        "  font-size: 0.95rem !important;\n"
        "}\n\n"
        ".watchlist-price,\n"
        ".activity-time,\n"
        ".cell-action,\n"
        ".table-action,\n"
        ".action-link {\n"
        "  font-family: var(--font-mono, 'JetBrains Mono', monospace) !important;\n"
        "}\n\n"
        ".activity-item .activity-time {\n"
        "  font-size: 0.82rem !important;\n"
        "  letter-spacing: 0.02em;\n"
        "  opacity: 0.78;\n"
        "}\n\n"
        ".cell-action,\n"
        ".table-action,\n"
        ".action-link,\n"
        ".trade-btn {\n"
        "  color: rgba(var(--accent-rgb, 16, 185, 129), 0.92) !important;\n"
        "  text-decoration: none;\n"
        "}\n\n"
        ".cell-action:hover,\n"
        ".table-action:hover,\n"
        ".action-link:hover,\n"
        ".trade-btn:hover {\n"
        "  color: var(--text, #f8fafc) !important;\n"
        "  text-shadow: 0 0 14px rgba(var(--accent-rgb, 16, 185, 129), 0.24);\n"
        "}\n\n"
        ".chart-action-btn,\n"
        ".chart-timeframe-btn,\n"
        ".chart-period-btn,\n"
        ".interactive-chip,\n"
        ".asset-table-action-btn,\n"
        ".guard-accent-action,\n"
        ".guard-tonal-action {\n"
        "  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease, background 160ms ease, color 160ms ease !important;\n"
        "}\n\n"
        ".chart-action-btn:hover,\n"
        ".chart-timeframe-btn:hover,\n"
        ".chart-period-btn:hover,\n"
        ".interactive-chip:hover,\n"
        ".asset-table-action-btn:hover,\n"
        ".guard-accent-action:hover,\n"
        ".guard-tonal-action:hover {\n"
        "  transform: translateY(-1px);\n"
        "  box-shadow: 0 16px 28px rgba(2, 6, 23, 0.28), 0 0 0 1px rgba(255, 255, 255, 0.08);\n"
        "}\n\n"
        ".chart-action-btn:active,\n"
        ".chart-timeframe-btn:active,\n"
        ".chart-period-btn:active,\n"
        ".interactive-chip:active,\n"
        ".asset-table-action-btn:active,\n"
        ".guard-accent-action:active,\n"
        ".guard-tonal-action:active {\n"
        "  transform: translateY(0);\n"
        "}\n\n"
        "button:focus-visible,\n"
        ".interactive-chip:focus-visible,\n"
        ".chart-period-btn:focus-visible,\n"
        ".chart-action-btn:focus-visible,\n"
        ".asset-table-action-btn:focus-visible,\n"
        ".sidebar-item:focus-visible,\n"
        ".cell-action:focus-visible,\n"
        ".table-action:focus-visible,\n"
        ".action-link:focus-visible {\n"
        "  outline: 2px solid rgba(var(--accent-rgb, 16, 185, 129), 0.72);\n"
        "  outline-offset: 2px;\n"
        "  box-shadow: 0 0 0 4px rgba(var(--accent-rgb, 16, 185, 129), 0.16), 0 12px 24px rgba(2, 6, 23, 0.22) !important;\n"
        "}\n\n"
        ".news-feed-panel .news-items,\n"
        ".watchlist-feed-panel .news-feed,\n"
        ".news-feed-section .news-feed,\n"
        ".news-panel .news-items,\n"
        ".briefing-panel .news-items {\n"
        "  display: grid;\n"
        "  gap: 0.9rem;\n"
        "}\n\n"
        ".news-feed-panel .news-item,\n"
        ".watchlist-feed-panel .news-feed-item,\n"
        ".news-feed-section .news-feed-item,\n"
        ".news-panel .news-item,\n"
        ".briefing-panel .news-item,\n"
        ".guard-news-secondary {\n"
        "  position: relative;\n"
        "  padding: 0.95rem 1rem;\n"
        "  border: 1px solid rgba(255, 255, 255, 0.06);\n"
        "  border-radius: 18px;\n"
        "  background: linear-gradient(180deg, rgba(255, 255, 255, 0.028), rgba(255, 255, 255, 0.012));\n"
        "}\n\n"
        ".news-feed-panel .news-item:first-child,\n"
        ".watchlist-feed-panel .news-feed-item:first-child,\n"
        ".news-feed-section .news-feed-item:first-child,\n"
        ".news-panel .news-item:first-child,\n"
        ".briefing-panel .news-item:first-child,\n"
        ".guard-news-lead {\n"
        "  padding: 1.2rem 1.25rem;\n"
        "  border-color: rgba(255, 255, 255, 0.12);\n"
        "  background: linear-gradient(145deg, rgba(255, 255, 255, 0.065), rgba(255, 255, 255, 0.02) 62%), rgba(18, 24, 38, 0.92) !important;\n"
        "  box-shadow: 0 18px 34px rgba(2, 6, 23, 0.22);\n"
        "}\n\n"
        ".news-item-title,\n"
        ".news-feed-title,\n"
        ".feed-title {\n"
        "  font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif) !important;\n"
        "  letter-spacing: -0.02em;\n"
        "}\n\n"
        ".news-feed-panel .news-item:first-child .news-item-title,\n"
        ".watchlist-feed-panel .news-feed-item:first-child .news-feed-title,\n"
        ".news-feed-section .news-feed-item:first-child .news-feed-title,\n"
        ".news-panel .news-item:first-child .news-item-title,\n"
        ".briefing-panel .news-item:first-child .news-item-title,\n"
        ".guard-news-lead .news-item-title,\n"
        ".guard-news-lead .news-feed-title,\n"
        ".guard-news-lead .feed-title {\n"
        "  font-size: clamp(1.05rem, 0.55vw + 0.96rem, 1.38rem) !important;\n"
        "  line-height: 1.22 !important;\n"
        "  font-weight: 600 !important;\n"
        "}\n\n"
        ".news-item-meta,\n"
        ".news-feed-meta,\n"
        ".feed-meta {\n"
        "  display: flex;\n"
        "  flex-wrap: wrap;\n"
        "  align-items: center;\n"
        "  gap: 0.45rem 0.7rem;\n"
        "}\n\n"
        ".news-item-source,\n"
        ".news-feed-source,\n"
        ".feed-source,\n"
        ".news-tag,\n"
        ".news-feed-tag,\n"
        ".badge {\n"
        "  text-transform: uppercase;\n"
        "  letter-spacing: 0.08em;\n"
        "  font-size: 0.7rem !important;\n"
        "}\n\n"
        ".news-item-time,\n"
        ".news-feed-time,\n"
        ".feed-time {\n"
        "  opacity: 0.82;\n"
        "}\n\n"
        ".hero-chart svg,\n"
        ".chart-card svg,\n"
        ".chart-content svg {\n"
        "  filter: drop-shadow(0 10px 26px rgba(2, 6, 23, 0.24));\n"
        "}\n\n"
        ".chart-card,\n"
        ".hero-chart,\n"
        ".asset-table-panel {\n"
        "  outline: 1px solid rgba(255, 255, 255, 0.02);\n"
        "}\n"
    )


def _build_componentized_polish_guard_runtime(ui_archetype: str) -> str | None:
    if ui_archetype not in POLISH_GUARD_ARCHETYPES:
        return None

    return (
        f"// Runtime numeric polish guard for {ui_archetype} shells.\n"
        "// Keep text mutations opt-in so React-managed dashboards do not reconcile against rewritten numeric nodes.\n"
        "const COUNT_SELECTORS = [\n"
        '  "[data-countup]"\n'
        "] as const;\n\n"
        "const MONO_SELECTORS = [\n"
        '  ...COUNT_SELECTORS,\n'
        '  ".kpi-value",\n'
        '  ".kpi-delta",\n'
        '  ".portfolio-value .value-amount",\n'
        '  ".stat-value",\n'
        '  ".numeric-value",\n'
        '  ".ticker-price",\n'
        '  ".ticker-delta",\n'
        '  ".watchlist-price",\n'
        '  ".watchlist-delta",\n'
        '  ".news-feed-time",\n'
        '  ".price",\n'
        '  ".delta",\n'
        '  ".text-mono",\n'
        '  ".table-cell",\n'
        '  ".candlestick-chart-svg text"\n'
        "] as const;\n\n"
        "const NEWS_PANEL_SELECTORS = [\n"
        '  ".watchlist-feed-panel",\n'
        '  ".news-feed-section",\n'
        '  ".news-feed",\n'
        '  ".news-feed-panel",\n'
        '  ".news-panel",\n'
        '  ".briefing-panel"\n'
        "] as const;\n\n"
        "const ACTION_SELECTORS = [\n"
        '  ".chart-action-btn",\n'
        '  ".interactive-chip",\n'
        '  ".asset-table-action-btn",\n'
        '  ".primary-btn",\n'
        '  "button"\n'
        "] as const;\n\n"
        "const SHELL_LAYOUT_SELECTORS = [\n"
        '  ".dashboard-layout",\n'
        '  ".fintech-shell"\n'
        "] as const;\n\n"
        "const NEWS_ITEM_SELECTOR = '.news-feed-item, .news-item, .feed-item, article, li';\n"
        "const SHELL_MAIN_SELECTOR = '.main-content, .content-area, .dashboard-main, .workspace-main, main';\n"
        "const SHELL_SIDEBAR_SELECTOR = '.sidebar, .app-sidebar, .left-rail, .side-rail';\n"
        "const PRIMARY_ACTION_RE = /\\b(buy|trade|deposit|rebalance|review|add position|open)\\b/i;\n"
        "const SECONDARY_ACTION_RE = /\\b(sell|withdraw|trim|hedge|close|reduce)\\b/i;\n\n"
        "function parseCountValue(text: string): { value: number; prefix: string; suffix: string; decimals: number } | null {\n"
        "  const trimmed = text.trim();\n"
        "  if (!trimmed || /[A-Za-z]{3,}/.test(trimmed)) {\n"
        "    return null;\n"
        "  }\n"
        "  const match = trimmed.match(/^([^\\d+-]*)([+-]?[\\d,]+(?:\\.\\d+)?)(.*)$/);\n"
        "  if (!match) {\n"
        "    return null;\n"
        "  }\n"
        "  const numeric = Number(match[2].replace(/,/g, ''));\n"
        "  if (!Number.isFinite(numeric) || Math.abs(numeric) < 1) {\n"
        "    return null;\n"
        "  }\n"
        "  const decimals = (match[2].split('.')[1] || '').length;\n"
        "  return { value: numeric, prefix: match[1], suffix: match[3], decimals };\n"
        "}\n\n"
        "function formatCountValue(value: number, prefix: string, suffix: string, decimals: number): string {\n"
        "  return `${prefix}${value.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${suffix}`;\n"
        "}\n\n"
        "function animateCount(node: HTMLElement): void {\n"
        "  if (node.dataset.guardCountAnimated === '1') {\n"
        "    return;\n"
        "  }\n"
        "  const parsed = parseCountValue(node.textContent || '');\n"
        "  if (!parsed) {\n"
        "    return;\n"
        "  }\n"
        "  node.dataset.guardCountAnimated = '1';\n"
        "  const target = parsed.value;\n"
        "  const duration = 900;\n"
        "  const start = performance.now();\n"
        "  const initial = Math.max(0, target * 0.2);\n"
        "  const step = (now: number) => {\n"
        "    const progress = Math.min((now - start) / duration, 1);\n"
        "    const eased = 1 - Math.pow(1 - progress, 3);\n"
        "    const current = initial + (target - initial) * eased;\n"
        "    node.textContent = formatCountValue(current, parsed.prefix, parsed.suffix, parsed.decimals);\n"
        "    if (progress < 1) {\n"
        "      window.requestAnimationFrame(step);\n"
        "    } else {\n"
        "      node.textContent = formatCountValue(target, parsed.prefix, parsed.suffix, parsed.decimals);\n"
        "    }\n"
        "  };\n"
        "  window.requestAnimationFrame(step);\n"
        "}\n\n"
        "function shouldAnimateCount(node: HTMLElement): boolean {\n"
        "  return node.childElementCount === 0 && Boolean(parseCountValue(node.textContent || ''));\n"
        "}\n\n"
        "function applyCountGuard(root: ParentNode = document): void {\n"
        "  const monoSelector = MONO_SELECTORS.join(',');\n"
        "  root.querySelectorAll<Element>(monoSelector).forEach((node) => {\n"
        "    node.classList.add('guard-mono-count');\n"
        "  });\n"
        "  const countSelector = COUNT_SELECTORS.join(',');\n"
        "  root.querySelectorAll<HTMLElement>(countSelector).forEach((node) => {\n"
        "    if (shouldAnimateCount(node)) {\n"
        "      animateCount(node);\n"
        "    }\n"
        "  });\n"
        "}\n\n"
        "function applyNewsHierarchyGuard(root: ParentNode = document): void {\n"
        "  NEWS_PANEL_SELECTORS.forEach((selector) => {\n"
        "    root.querySelectorAll<HTMLElement>(selector).forEach((panel) => {\n"
        "      const items = Array.from(panel.querySelectorAll<HTMLElement>(NEWS_ITEM_SELECTOR)).filter((item) => {\n"
        "        return Boolean((item.textContent || '').trim());\n"
        "      });\n"
        "      items.forEach((item, index) => {\n"
        "        item.classList.toggle('guard-news-lead', index === 0);\n"
        "        item.classList.toggle('guard-news-secondary', index > 0);\n"
        "      });\n"
        "    });\n"
        "  });\n"
        "}\n\n"
        "function applyActionGuard(root: ParentNode = document): void {\n"
        "  const selector = ACTION_SELECTORS.join(',');\n"
        "  root.querySelectorAll<HTMLElement>(selector).forEach((node) => {\n"
        "    const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();\n"
        "    if (!text) {\n"
        "      return;\n"
        "    }\n"
        "    if (PRIMARY_ACTION_RE.test(text)) {\n"
        "      node.classList.add('guard-accent-action');\n"
        "      node.classList.remove('guard-tonal-action');\n"
        "      return;\n"
        "    }\n"
        "    if (SECONDARY_ACTION_RE.test(text)) {\n"
        "      node.classList.add('guard-tonal-action');\n"
        "    }\n"
        "  });\n"
        "}\n\n"
        "function applyShellLayoutGuard(root: ParentNode = document): void {\n"
        "  if (typeof window === 'undefined' || window.innerWidth < 960) {\n"
        "    return;\n"
        "  }\n"
        "  SHELL_LAYOUT_SELECTORS.forEach((selector) => {\n"
        "    root.querySelectorAll<HTMLElement>(selector).forEach((shell) => {\n"
        "      const sidebar = shell.querySelector<HTMLElement>(SHELL_SIDEBAR_SELECTOR);\n"
        "      const main = shell.querySelector<HTMLElement>(SHELL_MAIN_SELECTOR);\n"
        "      if (!sidebar || !main) {\n"
        "        shell.classList.remove('guard-fixed-sidebar-shell');\n"
        "        shell.style.removeProperty('--guard-sidebar-offset');\n"
        "        return;\n"
        "      }\n"
        "      const shellStyle = window.getComputedStyle(shell);\n"
        "      const sidebarStyle = window.getComputedStyle(sidebar);\n"
        "      const sidebarWidth = Math.round(sidebar.getBoundingClientRect().width);\n"
        "      const mainRect = main.getBoundingClientRect();\n"
        "      const fixedSidebarGrid = shellStyle.display.includes('grid') && sidebarStyle.position === 'fixed';\n"
        "      const contentCollapsed = sidebarWidth > 0 && mainRect.width > 0 && mainRect.width <= Math.max(sidebarWidth + 80, window.innerWidth * 0.42);\n"
        "      const contentPinnedLeft = sidebarWidth > 0 && mainRect.x < Math.max(16, sidebarWidth - 12);\n"
        "      if (fixedSidebarGrid && (contentCollapsed || contentPinnedLeft)) {\n"
        "        shell.classList.add('guard-fixed-sidebar-shell');\n"
        "        shell.style.setProperty('--guard-sidebar-offset', `${Math.max(64, sidebarWidth)}px`);\n"
        "      } else {\n"
        "        shell.classList.remove('guard-fixed-sidebar-shell');\n"
        "        shell.style.removeProperty('--guard-sidebar-offset');\n"
        "      }\n"
        "    });\n"
        "  });\n"
        "}\n\n"
        "function applyPolishGuard(root: ParentNode = document): void {\n"
        "  applyCountGuard(root);\n"
        "  applyNewsHierarchyGuard(root);\n"
        "  applyActionGuard(root);\n"
        "  applyShellLayoutGuard(root);\n"
        "}\n\n"
        "let polishGuardFrame = 0;\n\n"
        "function schedulePolishGuard(): void {\n"
        "  if (typeof window === 'undefined' || polishGuardFrame) {\n"
        "    return;\n"
        "  }\n"
        "  polishGuardFrame = window.requestAnimationFrame(() => {\n"
        "    polishGuardFrame = 0;\n"
        "    applyPolishGuard(document);\n"
        "  });\n"
        "}\n\n"
        "if (typeof window !== 'undefined') {\n"
        "  window.addEventListener('load', () => {\n"
        "    applyPolishGuard(document);\n"
        "    const observer = new MutationObserver(() => schedulePolishGuard());\n"
        "    observer.observe(document.body, { childList: true, subtree: true });\n"
        "  }, { once: true });\n"
        "}\n"
    )


def _normalize_componentized_base_css(source: str, *, reference_css: str) -> str:
    updated = source
    reference_lines = GOOGLE_FONT_IMPORT_LINE_RE.findall(reference_css)
    if reference_lines:
        reference_import_block = "\n".join(line.strip() for line in reference_lines if line.strip())
        if reference_import_block:
            updated = GOOGLE_FONT_IMPORT_LINE_RE.sub("", updated).lstrip()
            updated = f"{reference_import_block}\n\n{updated}".lstrip()

    reference_lower = reference_css.lower()
    has_display_font = "space grotesk" in reference_lower or "outfit" in reference_lower
    has_mono_font = "jetbrains mono" in reference_lower

    updated = _normalize_componentized_override_css(
        updated,
        has_display_font=has_display_font,
        has_mono_font=has_mono_font,
    )

    updated_lower = updated.lower()
    appended_rules: list[str] = []
    if has_display_font and "space grotesk" not in updated_lower:
        appended_rules.append(
            ".page-title, .topbar-brand, .panel-title, .chart-title, .section-title, .feed-header, h1, h2, h3 {\n"
            "  font-family: 'Space Grotesk', 'Inter', sans-serif;\n"
            "}\n"
        )
    if has_mono_font and "jetbrains mono" not in updated_lower:
        appended_rules.append(
            ".kpi-value, .kpi-delta, .ticker-price, .ticker-delta, .watch-price, .watch-delta, .feed-time, .asset-table td, .table-number, .numeric-value {\n"
            "  font-family: 'JetBrains Mono', monospace;\n"
            "  font-variant-numeric: tabular-nums;\n"
            "}\n"
        )
    if appended_rules:
        updated = updated.rstrip() + "\n\n" + "\n".join(rule.rstrip() for rule in appended_rules) + "\n"

    return updated


def _normalize_componentized_override_css(
    source: str,
    *,
    has_display_font: bool,
    has_mono_font: bool,
) -> str:
    updated = source

    if has_mono_font:
        updated = updated.replace("Roboto Mono", "JetBrains Mono")
        updated = updated.replace("Fira Code", "JetBrains Mono")

    if has_display_font:
        updated = OVERRIDE_DISPLAY_FONT_RE.sub(r"\1'Space Grotesk', 'Inter', sans-serif;", updated)
        updated = _rewrite_override_selector_font_family(
            updated,
            selector_hints=DISPLAY_SELECTOR_HINTS,
            font_family="'Space Grotesk', 'Inter', sans-serif",
        )
    if has_mono_font:
        updated = _rewrite_override_selector_font_family(
            updated,
            selector_hints=NUMERIC_SELECTOR_HINTS,
            font_family="'JetBrains Mono', monospace",
        )

    return updated


def _rewrite_override_selector_font_family(
    source: str,
    *,
    selector_hints: tuple[str, ...],
    font_family: str,
) -> str:
    def _repl(match: re.Match[str]) -> str:
        selector = match.group("selector")
        selector_lower = selector.lower()
        if not any(hint in selector_lower for hint in selector_hints):
            return match.group(0)

        body = match.group("body")
        if "font-family" in body.lower():
            body = re.sub(r"font-family\s*:\s*[^;]+;", f"font-family: {font_family};", body, flags=re.IGNORECASE)
        else:
            stripped = body.rstrip()
            joiner = "\n" if stripped else ""
            body = f"{stripped}{joiner}  font-family: {font_family};\n"
        return f"{selector}{{{body}}}"

    return CSS_BLOCK_RE.sub(_repl, source)


def _normalize_componentized_index_html(source: str) -> str:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", source, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else "App"
    if not title:
        title = "App"
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "  <head>\n"
        '    <meta charset="UTF-8" />\n'
        '    <link rel="icon" type="image/svg+xml" href="/vite.svg" />\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
        f"    <title>{title}</title>\n"
        "  </head>\n"
        "  <body>\n"
        '    <div id="root"></div>\n'
        '    <script type="module" src="/src/main.tsx"></script>\n'
        "  </body>\n"
        "</html>\n"
    )


def _normalize_run_on_inline_comments(source: str) -> str:
    if "//" not in source:
        return source
    return INLINE_COMMENT_RUNON_RE.sub(lambda m: f"/* {m.group(1).strip()} */\n", source)


def _repair_interface_field_comment_bleed(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        comment = " ".join(match.group("comment").replace("}", " ").split()).strip()
        comment_block = f" /* {comment} */" if comment else ""
        return f"{match.group('field')}{comment_block}\n}}\n"

    return INTERFACE_FIELD_COMMENT_BLEED_RE.sub(_repl, source)


def _repair_inline_block_comment_code_bleed(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        comment = " ".join(match.group("comment").split()).strip()
        prop = match.group("prop").strip()
        prefix = " ".join(match.group("prefix").split()).strip()
        comment_block = f"/* {comment} */\n" if comment else ""
        if prefix:
            return f"{comment_block}{prop}: {prefix}"
        return f"{comment_block}{prop}: "

    return INLINE_BLOCK_COMMENT_CODE_BLEED_RE.sub(_repl, source)


def _repair_block_comment_control_flow_bleed(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        comment = " ".join(match.group("comment").split()).strip()
        code = " ".join(match.group("code").split()).strip()
        comment_block = f"/* {comment} */\n" if comment else ""
        return f"{comment_block}{code}"

    return BLOCK_COMMENT_CONTROL_FLOW_BLEED_RE.sub(_repl, source)


def _repair_unterminated_block_comment_line_notes(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        comment = " ".join(
            " ".join(part.split()).strip()
            for part in (match.group("comment"), match.group("tail"))
            if part and part.strip()
        ).strip()
        indent = match.group("indent")
        code = f"{match.group('code')}{match.group('rest')}".lstrip()
        comment_block = f"{indent}/* {comment} */\n" if comment else ""
        return f"{comment_block}{indent}{code}"

    return UNTERMINATED_BLOCK_COMMENT_LINE_NOTE_RE.sub(_repl, source)


def _repair_inline_block_comment_continuations(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        prefix = match.group("prefix").rstrip()
        comment = " ".join(
            " ".join(part.split()).strip()
            for part in (match.group("comment"), match.group("label"))
            if part and part.strip()
        ).strip()
        code = match.group("code").strip()
        indent_match = re.match(r"[ \t]*", match.group("prefix"))
        indent = indent_match.group(0) if indent_match else ""
        comment_block = f"{prefix} /* {comment} */" if prefix else f"{indent}/* {comment} */"
        return f"{comment_block}\n{indent}{code}"

    return INLINE_BLOCK_COMMENT_CONTINUATION_RE.sub(_repl, source)


def _normalize_run_on_natural_language_notes(source: str) -> str:
    return RUNON_NATURAL_LANGUAGE_NOTE_RE.sub(
        lambda match: f"/* {match.group('note').strip()} */\n",
        source,
    )


def _normalize_run_on_explanatory_labels(source: str) -> str:
    return RUNON_EXPLANATORY_LABEL_RE.sub(
        lambda match: f"/* {match.group('label').strip()} */\n",
        source,
    )


def _normalize_lowercase_object_field_labels(source: str) -> str:
    return LOWERCASE_OBJECT_FIELD_LABEL_RE.sub(
        lambda match: f"{match.group('indent')}/* {match.group('label').strip()} */\n{match.group('indent')}{match.group('field').strip()}",
        source,
    )


def _normalize_bare_section_labels(source: str) -> str:
    return BARE_SECTION_LABEL_RE.sub(
        lambda match: f"/* {match.group('label').strip()} */\n",
        source,
    )


def _repair_componentized_comment_url_bleed(source: str) -> str:
    updated = URL_PROTOCOL_COMMENT_BLEED_RE.sub(
        lambda match: f"{match.group('scheme')}://",
        source,
    )
    updated = ATTR_VALUE_ORPHAN_COMMENT_CLOSE_RE.sub(
        lambda match: f"{match.group('attr')}={match.group('quote')}",
        updated,
    )

    def _rewrite_section_comment(match: re.Match[str]) -> str:
        label = " ".join(match.group("label").split()).strip()
        if not label:
            return match.group("stmt") + "\n"
        return f"{match.group('stmt')}\n/* {label} */\n"

    updated = TRAILING_SECTION_LINE_COMMENT_RE.sub(_rewrite_section_comment, updated)
    updated = ORPHAN_COMMENT_CLOSE_AFTER_STATEMENT_RE.sub(
        lambda match: match.group("stmt"),
        updated,
    )
    updated = CONTROL_FLOW_ORPHAN_COMMENT_CLOSE_RE.sub(
        lambda match: match.group("prefix"),
        updated,
    )
    updated = BLOCK_COMMENT_SWALLOWED_ARRAY_CLOSE_RE.sub(
        lambda match: f"/* {' '.join(match.group('comment').split()).strip()} */\n];",
        updated,
    )
    return updated


def _repair_componentized_comment_split_identifiers(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        comment = " ".join(match.group("comment").split()).strip()
        prefix = match.group("prefix").strip()
        suffix = match.group("suffix").strip()
        rest = match.group("rest") or ""
        comment_block = f"/* {comment} */\n" if comment else ""
        return f"{comment_block}{prefix}{suffix}{rest}"

    return COMMENT_SPLIT_IDENTIFIER_RE.sub(_repl, source)


def _repair_componentized_orphan_comment_split_identifiers(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        prefix = match.group("prefix").strip()
        suffix = match.group("suffix").strip()
        rest = match.group("rest") or ""
        return f"{prefix}{suffix}{rest}"

    return ORPHAN_COMMENT_SPLIT_IDENTIFIER_RE.sub(_repl, source)


def _repair_componentized_orphan_comment_split_string_literals(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        quote = match.group("quote")
        content = match.group("content").strip()
        return f"{prefix}{quote}{content}{quote}"

    return ORPHAN_COMMENT_SPLIT_STRING_LITERAL_RE.sub(_repl, source)


def _repair_componentized_jsx_block_comment_bleed(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        comment = " ".join(match.group("comment").split()).strip()
        jsx = match.group("jsx").strip()
        prefix = match.group("prefix").strip()
        suffix = match.group("suffix").strip()
        rest = match.group("rest") or ""
        indent = match.group("indent") or ""
        comment_block = f"{indent}/* {comment} */\n" if comment else ""
        return f"(\n{comment_block}{indent}{jsx}{{{prefix}{suffix}{rest}"

    return JSX_BLOCK_COMMENT_BLEED_RE.sub(_repl, source)


def _repair_componentized_jsx_text_comment_bleed(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        prefix = " ".join(match.group("prefix").split()).strip()
        suffix = " ".join(match.group("suffix").split()).strip()
        if not prefix or not suffix:
            return match.group(0)
        return f">{prefix} {suffix}<"

    return JSX_TEXT_COMMENT_CLOSE_BLEED_RE.sub(_repl, source)


def _normalize_componentized_void_jsx_elements(source: str) -> str:
    return VOID_JSX_ELEMENT_RE.sub(
        lambda match: f"<{match.group('tag')}{match.group('attrs').rstrip()} />",
        source,
    )


def _repair_componentized_css_data_uri_quote_bleed(source: str) -> str:
    return CSS_DATA_URI_ESCAPED_QUOTE_BLEED_RE.sub(r"\\'", source)


def _repair_componentized_jsx_event_handler_arrow_bleed(source: str) -> str:
    return JSX_EVENT_HANDLER_ARROW_BLEED_RE.sub(
        lambda match: f"{match.group('prefix')}{match.group('param').strip()} =>",
        source,
    )


def _normalize_componentized_declaration_boundaries(source: str) -> str:
    return DECLARATION_BOUNDARY_RE.sub("\n", source)


def _hoist_componentized_chart_helper_declarations(source: str) -> str:
    lines = source.splitlines()
    if not lines or ".map(" not in source or "return (" not in source:
        return source

    helper_candidates: list[tuple[int, int, str]] = []
    for idx, line in enumerate(lines):
        match = re.match(
            r"^(?P<indent>\s*)const (?P<name>(?:scale|map)[XY]|[xy]Scale)\s*=\s*.+;\s*(?://.*)?$",
            line,
        )
        if not match:
            continue
        helper_name = match.group("name")
        if source.count(f"{helper_name}(") < 2:
            continue

        previous_window = "\n".join(lines[max(0, idx - 8):idx + 1])
        next_window = "\n".join(lines[idx:min(len(lines), idx + 12)])
        if ".map(" not in previous_window or "return" not in next_window:
            continue

        return_idx = None
        for search_idx in range(idx - 1, -1, -1):
            if re.match(r"^\s*return\s*\(\s*$", lines[search_idx]):
                return_idx = search_idx
                break
        if return_idx is None:
            continue

        helper_candidates.append((idx, return_idx, line.strip()))

    if not helper_candidates:
        return source

    removed_indexes = {candidate[0] for candidate in helper_candidates}
    insertions: dict[int, list[str]] = {}
    for _, return_idx, helper_line in helper_candidates:
        return_indent = re.match(r"^(\s*)", lines[return_idx]).group(1)
        insertions.setdefault(return_idx, [])
        hoisted_line = f"{return_indent}{helper_line}"
        if hoisted_line not in insertions[return_idx]:
            insertions[return_idx].append(hoisted_line)

    rebuilt: list[str] = []
    for idx, line in enumerate(lines):
        if idx in insertions:
            rebuilt.extend(insertions[idx])
        if idx in removed_indexes:
            continue
        rebuilt.append(line)

    updated = "\n".join(rebuilt)
    if source.endswith("\n"):
        updated += "\n"
    return updated


def _normalize_componentized_field_aliases(source: str) -> str:
    updated = source
    for alias_group in COMPONENTIZED_FIELD_ALIAS_GROUPS:
        canonical, *aliases = alias_group
        if canonical not in updated:
            continue
        for alias in aliases:
            updated = re.sub(rf"\b{re.escape(alias)}\b", canonical, updated)
    return updated


def _normalize_componentized_currency_formatting(source: str) -> str:
    updated = EMPTY_CURRENCY_FORMAT_ARG_RE.sub(
        lambda match: f"formatCurrency({match.group('value').strip()})",
        source,
    )
    return FORMAT_CURRENCY_GUARD_RE.sub(
        "currency: /^[A-Za-z]{3}$/.test(currency) ? currency.toUpperCase() : 'USD'",
        updated,
    )


def _normalize_run_on_imports(source: str) -> str:
    updated = re.sub(
        r";\s*(?=(?:import\b|const\b|let\b|var\b|function\b|export\b|return\b|if\b|for\b|while\b|switch\b|type\b|interface\b|class\b|use[A-Z]\w*\b|ReactDOM\b|createRoot\b))",
        ";\n",
        source,
    )
    updated = re.sub(r"(?<=['\"])\s*(?=import\b)", "\n", updated)
    updated = re.sub(
        r"\*/\s*(?=(?:const\b|let\b|var\b|function\b|export\b|return\b|if\b|for\b|while\b|switch\b|type\b|interface\b|class\b|use[A-Z]\w*\b|ReactDOM\b|createRoot\b))",
        "*/\n",
        updated,
    )
    updated = re.sub(r"}\s+(?=return\b)", "}\n", updated)
    return updated


CSS_TAIL_SELECTOR_RE = re.compile(
    r"(?m)^(?:\.[A-Za-z_][\w-]*|#[A-Za-z_][\w-]*|:root|body|html|@media\b[^{]*)\s*\{"
)


def _extract_componentized_css_tail(source: str) -> tuple[str, str]:
    if "{" not in source or ("return" not in source and "export default" not in source):
        return source, ""

    search_start = max(
        source.rfind("return ("),
        source.rfind("return("),
        source.rfind("export default function"),
        source.rfind("const App"),
        0,
    )
    match = CSS_TAIL_SELECTOR_RE.search(source, pos=max(search_start, 0))
    if not match:
        return source, ""

    css_start = match.start()
    tail = source[css_start:]
    export_tail = ""
    export_match = re.search(r"export default\s+[A-Za-z0-9_$.]+\s*;\s*$", tail, flags=re.DOTALL)
    if export_match:
        export_tail = export_match.group(0).strip()
        tail = tail[:export_match.start()]

    css_tail = tail.strip()
    if not css_tail:
        return source, ""

    cleaned = source[:css_start].rstrip()
    if export_tail:
        cleaned = cleaned + "\n\n" + export_tail
    cleaned = cleaned.rstrip() + "\n"
    return cleaned, css_tail


def _normalize_componentized_main_entry(source: str) -> str:
    updated = re.sub(
        r"//\s*([^\n]*?)(?=(?:import\b|ReactDOM\b|createRoot\b|root\.render\b|const\b|let\b|var\b))",
        lambda m: f"/* {m.group(1).strip()} */\n",
        source,
    )
    updated = re.sub(r";\s*(?=import\b)", ";\n", updated)
    updated = re.sub(r";\s*(?=(?:ReactDOM\b|createRoot\b|root\.render\b|const\b|let\b|var\b))", ";\n", updated)
    updated = MAIN_BASE_CSS_IMPORT_RE.sub('import "./base.css";', updated)
    return _normalize_componentized_main_css_order(updated)


def _normalize_componentized_main_css_order(source: str) -> str:
    lines = source.splitlines()
    js_imports: list[str] = []
    css_imports: list[str] = []
    other_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        css_match = MAIN_CSS_IMPORT_LINE_RE.match(line)
        if css_match:
            css_imports.append(css_match.group("path"))
        elif MAIN_ENTRY_INVALID_IMPORT_NOTE_RE.match(stripped):
            continue
        elif stripped.startswith("import "):
            js_imports.append(line.rstrip())
        else:
            other_lines.append(line)

    if not css_imports:
        return source

    ordered_css_imports: list[str] = []
    seen_css: set[str] = set()
    has_polish_guard = POLISH_GUARD_IMPORT in css_imports
    filtered_css_imports = [path for path in css_imports if path != POLISH_GUARD_IMPORT]
    for import_path in MAIN_ENTRY_PREFERRED_CSS_ORDER:
        if import_path in filtered_css_imports and import_path not in seen_css:
            ordered_css_imports.append(f'import "{import_path}";')
            seen_css.add(import_path)
    for import_path in filtered_css_imports:
        if import_path not in seen_css:
            ordered_css_imports.append(f'import "{import_path}";')
            seen_css.add(import_path)
    if has_polish_guard:
        ordered_css_imports.append(f'import "{POLISH_GUARD_IMPORT}";')

    rebuilt_lines = [*js_imports, *ordered_css_imports]
    if other_lines:
        if rebuilt_lines and any(line.strip() for line in other_lines):
            rebuilt_lines.append("")
        rebuilt_lines.extend(other_lines)

    rebuilt = "\n".join(rebuilt_lines).rstrip() + "\n"
    return rebuilt


def _make_dist_index_portable(dist_index: Path) -> None:
    html = dist_index.read_text(encoding="utf-8", errors="replace")
    updated = re.sub(r'((?:src|href)=["\'])/assets/', r"\1./assets/", html, flags=re.IGNORECASE)
    updated = re.sub(r'((?:src|href)=["\'])/generated-assets/', r"\1./generated-assets/", updated, flags=re.IGNORECASE)
    updated = re.sub(r'((?:src|href)=["\'])/vite\.svg', r"\1./vite.svg", updated, flags=re.IGNORECASE)
    if updated != html:
        dist_index.write_text(updated, encoding="utf-8")


def _root_package_name(specifier: str) -> str:
    if specifier.startswith("@"):
        parts = specifier.split("/")
        return "/".join(parts[:2]) if len(parts) >= 2 else specifier
    return specifier.split("/", 1)[0]
