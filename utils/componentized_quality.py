from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from utils.componentized_runtime import collect_componentized_editable_files


APP_LIKE_ARCHETYPES = {"dashboard", "fintech", "editor", "kanban", "chat"}
STRICT_APP_ARCHETYPES = {"dashboard", "fintech"}
FANPAGE_ARCHETYPE_PREFIXES = ("game", "fan_page")
CONTENT_BEARING_ROLES = {"kpi", "chart", "table", "feed", "data", "page"}
KPI_ROLES = {"kpi", "page", "data"}
CHART_ROLES = {"chart", "page", "data"}
TABLE_ROLES = {"table", "page", "data"}
FEED_ROLES = {"feed", "page", "data"}
FANPAGE_CATEGORY_HINTS: dict[str, tuple[str, ...]] = {
    "characters": ("character", "characters", "party", "roster", "operatives", "companions"),
    "arsenal": ("weapon", "weapons", "arsenal", "materia", "abilities", "summon"),
    "world": ("world map", "map", "location", "region", "atlas", "gaia", "midgar"),
    "lore": ("lore", "story", "history", "tribute", "archive", "timeline", "legend"),
    "collection": ("collector", "gallery", "cards", "card", "evolution", "digivolve"),
}
FANPAGE_STAT_HINTS = (
    "hp", "atk", "attack", "def", "defense", "mag", "magic", "spd", "speed",
    "strength", "agility", "rarity", "type", "role",
)
FANPAGE_HERO_HINTS = (
    "hero", "full-bleed", "masthead", "featured", "spotlight", "scroll-indicator",
)
SUPPORT_MODULE_HINTS: dict[str, tuple[str, ...]] = {
    "watchlist": ("watchlist", "market movers", "movers", "top movers", "ticker tape"),
    "activity": ("activity", "recent activity", "recent transactions", "recent trades", "execution log"),
    "alerts": ("alerts", "alert center", "notifications", "risk alert", "triggered"),
    "news": ("news", "headlines", "market brief", "briefing", "top stories"),
    "allocation": ("allocation", "sector allocation", "exposure", "portfolio mix", "breakdown"),
    "comparison": ("benchmark", "comparison", "heatmap", "winners", "losers", "top performers"),
    "orders": ("open orders", "order flow", "trade ideas", "rebalance"),
}

PLACEHOLDER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bmetric\s+\d+\b", re.IGNORECASE), "generic metric label"),
    (re.compile(r"\bchart title\b", re.IGNORECASE), "generic chart title"),
    (re.compile(r"\buser\s+\d+\b", re.IGNORECASE), "generic user label"),
    (re.compile(r"\bproduct\s+\d+\b", re.IGNORECASE), "generic product label"),
    (re.compile(r"\bitem\s+(?:[A-Z]\b|[A-Z]\d+\b|\d+\b)\b"), "generic item label"),
    (re.compile(r"\bsample\s+(?:data|item|text|content|value|name)\b", re.IGNORECASE), "sample placeholder"),
    (re.compile(r"\blorem ipsum\b", re.IGNORECASE), "lorem ipsum"),
    (re.compile(r"\bplaceholder\b", re.IGNORECASE), "placeholder text"),
    (re.compile(r"\byour tagline here\b", re.IGNORECASE), "tagline placeholder"),
    (re.compile(r"\bcoming soon\b", re.IGNORECASE), "coming soon placeholder"),
    (re.compile(r"\bfeature\s+[A-Z0-9]+\b", re.IGNORECASE), "generic feature label"),
]

ROLE_SIGNAL_PATTERNS: dict[str, tuple[str, ...]] = {
    "kpi": (
        "kpi",
        "metric",
        "portfolio value",
        "revenue",
        "arr",
        "mrr",
        "day p&l",
        "day p/l",
        "open positions",
        "active users",
        "conversion rate",
        "win rate",
    ),
    "chart": (
        "chart",
        "sparkline",
        "candlestick",
        "polyline",
        "areapathdata",
        "linechart",
        "recharts",
        "tooltip",
        "y-axis",
    ),
    "table": (
        "<table",
        "<thead",
        "<tbody",
        "<tr",
        "<th",
        "<td",
        "data-table",
        "sortable",
        "holdings",
        "transactions",
    ),
    "feed": (
        "activity",
        "watchlist",
        "feed",
        "recent transactions",
        "recent activity",
        "alerts",
        "notifications",
        "hours ago",
        "minutes ago",
    ),
    "data": (
        "const initial",
        "export const",
        "mock data",
        "seed data",
        "transactions",
        "holdings",
        "watchlist",
        "metrics",
        "series",
    ),
    "page": (
        "<main",
        "<section",
        "return (",
        "page",
        "dashboard",
        "overview",
        "layout",
    ),
}

KPI_LABEL_HINTS = (
    "portfolio value",
    "day p&l",
    "day p/l",
    "day change",
    "ytd return",
    "dividend income",
    "monthly active users",
    "revenue",
    "churn rate",
    "avg. session",
    "avg session",
    "open positions",
    "win rate",
    "net cash",
    "burn multiple",
    "conversion rate",
    "total return",
    "best performer",
    "cash balance",
    "watchlist value",
    "market movers",
)

COMPANY_SUFFIX_RE = re.compile(r"\b(?:Inc\.?|Corp\.?|Corporation|Holdings|Group|Capital|Partners|Technologies|Systems|Labs|Bank|Motors)\b")
TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")
STATUS_RE = re.compile(r"\b(active|pending|completed|cancelled|filled|buy|sell|hold|open|closed|positive|negative|success|warning|error)\b", re.IGNORECASE)
DATE_RE = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+20\d{2}\b")
RELATIVE_TIME_RE = re.compile(r"\b\d+\s+(?:minutes?|hours?|days?|weeks?)\s+ago\b", re.IGNORECASE)
STRING_LITERAL_RE = re.compile(r'"([^"\n]{1,240})"|\'([^\'\n]{1,240})\'|`([^`\n]{1,240})`')
JSX_TEXT_RE = re.compile(r">([^<>{][^<>]{0,240})<")
DISPLAY_NUMBER_RE = re.compile(r"\$-?\d[\d,]*(?:\.\d+)?|-?\d[\d,]*(?:\.\d+)?%")
DATA_NUMBER_RE = re.compile(
    r"\b(?:value|amount|price|total|delta|change|pnl|return|allocation|yield|shares|volume|count|balance|revenue)\s*:\s*['\"]?(-?\$?\d[\d,]*(?:\.\d+)?%?)",
    re.IGNORECASE,
)
OBJECT_ENTRY_RE = re.compile(r"\{[^{}]{0,400}?\}", re.DOTALL)
INLINE_DATA_ARRAY_RE = re.compile(
    r"(?:const|let|var)\s+[A-Za-z0-9_]+\s*(?::[^=]+)?=\s*\[(?:.|\n){0,4000}?\]",
    re.IGNORECASE,
)
ENTITY_NAME_RE = re.compile(r"\bname\s*:\s*['\"]([A-Z][A-Za-z0-9' -]{2,40})['\"]")
BUILD_ERROR_PATH_RE = re.compile(
    r"(?P<path>(?:[A-Za-z]:)?[^:\n]+?\.(?:tsx|ts|jsx|js|css|html)):(?P<line>\d+)(?::(?P<column>\d+))?",
    re.IGNORECASE,
)
PACKAGE_JSON_PARSE_RE = re.compile(
    r"(?:npm error\s+code\s+ejsonparse|invalid package\.json|jsonparseerror)",
    re.IGNORECASE,
)


def collect_componentized_file_records(code_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for rel_path in collect_componentized_editable_files(code_dir):
        path = code_dir / rel_path
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        records.append(
            {
                "path": rel_path,
                "content": content,
                "language": _guess_language(rel_path),
            }
        )
    return records


def classify_componentized_content_file(path: str, content: str) -> dict[str, Any]:
    rel_path = path.replace("\\", "/").strip("/")
    normalized_path = rel_path.lower()
    normalized_content = content.lower()
    signals: list[str] = []

    if "polish-guard" in normalized_path:
        return {
            "path": rel_path,
            "role": "config",
            "is_content_bearing": False,
            "signals": ["runtime polish guard"],
        }

    if (
        normalized_path.endswith(("/icons.ts", "/icons.tsx", "/icons.js", "/icons.jsx"))
        or "/icons/" in f"/{normalized_path}"
    ):
        return {
            "path": rel_path,
            "role": "config",
            "is_content_bearing": False,
            "signals": ["icon library"],
        }

    if normalized_path.endswith((".css", ".scss", ".less")):
        return {
            "path": rel_path,
            "role": "style",
            "is_content_bearing": False,
            "signals": ["style file"],
        }

    if "/styles/" in f"/{normalized_path}" and normalized_path.endswith((".ts", ".tsx", ".js", ".jsx")):
        return {
            "path": rel_path,
            "role": "config",
            "is_content_bearing": False,
            "signals": ["style support file"],
        }

    if (
        normalized_path.endswith((".json", ".lock", ".env"))
        or "tsconfig" in normalized_path
        or "vite.config" in normalized_path
        or "tailwind.config" in normalized_path
        or normalized_path.endswith(".d.ts")
    ):
        return {
            "path": rel_path,
            "role": "config",
            "is_content_bearing": False,
            "signals": ["config file"],
        }

    if any(token in normalized_path for token in ("sidebar", "navbar", "header", "footer", "layout", "shell")):
        if not re.search(r"\b(?:portfolio|revenue|price|value|amount|users|transactions|watchlist)\b", normalized_content):
            return {
                "path": rel_path,
                "role": "layout",
                "is_content_bearing": False,
                "signals": ["layout shell"],
            }
        signals.append("layout file with embedded data")

    if any(token in normalized_path for token in ("utils", "helpers", "hooks", "types", "schema")):
        return {
            "path": rel_path,
            "role": "config",
            "is_content_bearing": False,
            "signals": ["utility file"],
        }

    scores = {role: 0 for role in CONTENT_BEARING_ROLES}

    if "/data/" in f"/{normalized_path}" or any(token in normalized_path for token in ("metrics", "transactions", "seed", "mock", "series", "dataset")):
        scores["data"] += 4
        signals.append("data path")
    if "/pages/" in f"/{normalized_path}" or "/views/" in f"/{normalized_path}" or normalized_path.endswith("/app.tsx"):
        scores["page"] += 4
        signals.append("page path")
    if "chart" in normalized_path or "sparkline" in normalized_path or "candlestick" in normalized_path:
        scores["chart"] += 4
        signals.append("chart path")
    if "table" in normalized_path or "grid" in normalized_path:
        scores["table"] += 4
        signals.append("table path")
    if any(token in normalized_path for token in ("watchlist", "activity", "feed", "alert", "notification")):
        scores["feed"] += 4
        signals.append("feed path")
    if any(token in normalized_path for token in ("kpi", "metric", "stats", "summary")):
        scores["kpi"] += 4
        signals.append("kpi path")

    for role, patterns in ROLE_SIGNAL_PATTERNS.items():
        for pattern in patterns:
            if pattern in normalized_content:
                scores[role] += 1

    role = max(scores.items(), key=lambda item: item[1])[0]
    top_score = scores[role]
    if top_score == 0:
        role = "page" if normalized_path.endswith(("app.tsx", ".tsx", ".jsx")) else "config"

    is_content_bearing = role in CONTENT_BEARING_ROLES
    return {
        "path": rel_path,
        "role": role,
        "is_content_bearing": is_content_bearing,
        "signals": signals or [f"dominant role: {role}"],
    }


def _guess_language(rel_path: str) -> str:
    suffix = Path(rel_path).suffix.lower()
    return {
        ".css": "css",
        ".html": "html",
        ".js": "javascript",
        ".jsx": "jsx",
        ".json": "json",
        ".ts": "typescript",
        ".tsx": "tsx",
    }.get(suffix, "text")


def _extract_visible_strings(source: str) -> list[str]:
    values: list[str] = []
    for match in STRING_LITERAL_RE.finditer(source):
        raw = next(group for group in match.groups() if group)
        text = raw.replace("\\n", " ").replace("\\t", " ").strip()
        if (
            2 <= len(text) <= 180
            and not text.startswith(("./", "../", "/generated-assets/", "http://", "https://"))
            and _looks_like_visible_text(text)
        ):
            values.append(" ".join(text.split()))

    for match in JSX_TEXT_RE.finditer(source):
        text = " ".join(match.group(1).strip().split())
        if 2 <= len(text) <= 180 and not text.startswith("{") and _looks_like_visible_text(text):
            values.append(text)

    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _visible_strings_from_records(records: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for record in records:
        values.extend(_extract_visible_strings(record["content"]))
    return values


def _combined_visible_text(records: list[dict[str, Any]]) -> str:
    return " ".join(_visible_strings_from_records(records))


def _looks_like_visible_text(text: str) -> bool:
    stripped = " ".join(text.split()).strip()
    lower = stripped.lower()
    if lower in {"react", "none", "currentcolor", "round"}:
        return False
    if stripped.startswith(("M", "L")) and re.fullmatch(r"[MLCVHSTQAZmlcvhstqaz0-9 .,-]+", stripped):
        return False
    if any(token in stripped for token in ("=>", "};", "{", "}", "</", "/>", "React.FC", "className", "font-family")):
        return False
    if re.fullmatch(r"[a-z0-9_-]{2,}", stripped) and ("-" in stripped or "_" in stripped):
        return False
    if re.fullmatch(r"var\(--[a-z0-9-]+\)", lower):
        return False
    if re.fullmatch(r"[0-9 .-]{2,}", stripped):
        return False
    return True


def _placeholder_hits(text: str) -> list[str]:
    hits: list[str] = []
    for pattern, label in PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            hits.append(label)
    return hits


def _extract_display_numbers(strings: list[str], source: str) -> list[str]:
    values = DISPLAY_NUMBER_RE.findall(" ".join(strings))
    values.extend(DATA_NUMBER_RE.findall(source))
    return [value for value in values if value]


def _is_suspicious_round_number(raw_value: str) -> bool:
    value = raw_value.replace("$", "").replace(",", "").replace("%", "").strip()
    try:
        numeric = float(value)
    except ValueError:
        return False

    absolute = abs(numeric)
    if absolute < 10:
        return False
    if raw_value.endswith("%"):
        return absolute >= 10 and abs(numeric - round(numeric)) < 1e-6 and int(round(absolute)) % 5 == 0
    if absolute >= 1000:
        return abs(numeric - round(numeric)) < 1e-6 and int(round(absolute)) % 100 == 0
    if absolute >= 100:
        return abs(numeric - round(numeric)) < 1e-6 and int(round(absolute)) % 10 == 0
    return False


def _normalize_archetype(ui_archetype: str | None) -> str:
    return str(ui_archetype or "").strip().lower()


def _quality_family(ui_archetype: str | None) -> str:
    normalized = _normalize_archetype(ui_archetype)
    if normalized in STRICT_APP_ARCHETYPES or normalized in APP_LIKE_ARCHETYPES:
        return "data_app"
    if normalized.startswith(FANPAGE_ARCHETYPE_PREFIXES) or "fan" in normalized:
        return "fanpage"
    return "generic"


def _fanpage_blob(records: list[dict[str, Any]]) -> str:
    return "\n".join(record["content"].lower() for record in records)


def _fanpage_category_count(records: list[dict[str, Any]]) -> int:
    blob = _fanpage_blob(records)
    found = {
        category
        for category, hints in FANPAGE_CATEGORY_HINTS.items()
        if any(hint in blob for hint in hints)
    }
    return len(found)


def _fanpage_entity_names(records: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for record in records:
        for match in ENTITY_NAME_RE.findall(record["content"]):
            normalized = " ".join(match.split()).strip()
            if normalized:
                names.add(normalized)
    return names


def _fanpage_stat_count(records: list[dict[str, Any]]) -> int:
    blob = _fanpage_blob(records)
    return sum(blob.count(hint) for hint in FANPAGE_STAT_HINTS)


def _fanpage_media_count(records: list[dict[str, Any]]) -> int:
    blob = _fanpage_blob(records)
    return blob.count("/generated-assets/") + blob.count("<img") + blob.count("image:")


def _has_fanpage_hero_media(records: list[dict[str, Any]]) -> bool:
    blob = _fanpage_blob(records)
    return any(hint in blob for hint in FANPAGE_HERO_HINTS) and _fanpage_media_count(records) >= 1


def _fanpage_contextual_hits(records: list[dict[str, Any]]) -> int:
    blob = _fanpage_blob(records)
    hits = 0
    if _fanpage_category_count(records) >= 3:
        hits += 1
    if any(token in blob for token in ("section", "chapter", "archive", "dossier", "compendium")):
        hits += 1
    if any(token in blob for token in ("type", "role", "rarity", "evolution", "location", "abilities")):
        hits += 1
    return hits


def evaluate_componentized_density(code_dir: Path, *, ui_archetype: str | None = None) -> dict[str, Any]:
    records = collect_componentized_file_records(code_dir)
    classifications = [classify_componentized_content_file(record["path"], record["content"]) for record in records]
    content_records = [
        record
        for record in records
        if next((item for item in classifications if item["path"] == record["path"]), {}).get("is_content_bearing")
    ]
    if not content_records:
        return {
            "passed": False,
            "score": 0,
            "threshold": 70,
            "metrics": {},
            "weaknesses": [{"code": "empty_content_workspace", "message": "No content-bearing app files were detected."}],
        }

    panel_count = _estimate_panel_count(content_records)
    interactive_controls = _estimate_interactive_control_count(content_records)
    text_density = len(_combined_visible_text(content_records))
    numeric_typography = _has_numeric_typography(records)
    family = _quality_family(ui_archetype)

    score = 0
    weaknesses: list[dict[str, str]] = []

    kpi_count = 0
    chart_regions = 0
    chart_points = 0
    table_rows = 0
    table_columns = 0
    feed_entries = 0
    support_module_count = 0

    if family == "fanpage":
        hero_media = _has_fanpage_hero_media(content_records)
        character_count = len(_fanpage_entity_names(content_records))
        category_count = _fanpage_category_count(content_records)
        stat_block_count = _fanpage_stat_count(content_records)
        media_count = _fanpage_media_count(content_records)

        if hero_media:
            score += 15
        else:
            weaknesses.append({"code": "panel_stacking", "message": "The page needs a stronger hero treatment with clear lead media."})

        if character_count >= 3:
            score += 20
        elif character_count >= 2:
            score += 10
            weaknesses.append({"code": "text_density", "message": "The fan page needs a fuller character showcase with more distinct featured entries."})
        else:
            weaknesses.append({"code": "text_density", "message": "The fan page needs a clearer featured-character showcase."})

        if category_count >= 3:
            score += 20
        elif category_count >= 2:
            score += 10
            weaknesses.append({"code": "panel_stacking", "message": "The fan page needs more worldbuilding sections such as lore, maps, arsenal, or gallery content."})
        else:
            weaknesses.append({"code": "panel_stacking", "message": "The fan page needs richer worldbuilding modules beyond the hero and roster."})

        if stat_block_count >= 8:
            score += 10
        elif stat_block_count >= 4:
            score += 5
            weaknesses.append({"code": "interactive_controls", "message": "Character stat treatments exist but need more density or motion."})
        else:
            weaknesses.append({"code": "interactive_controls", "message": "Featured characters need stronger stat bars, badges, or supporting detail."})

        if media_count >= 4:
            score += 10
        elif media_count >= 2:
            score += 5
            weaknesses.append({"code": "panel_stacking", "message": "The page could use more supporting media treatments across sections."})
        else:
            weaknesses.append({"code": "panel_stacking", "message": "The page needs more visual support media across the archive sections."})

        if panel_count >= 4:
            score += 10
        elif panel_count >= 3:
            score += 5
            weaknesses.append({"code": "panel_stacking", "message": "The fan page needs more distinct stacked content regions."})
        else:
            weaknesses.append({"code": "panel_stacking", "message": "The shell is missing enough distinct content regions for a premium fan page."})

        if interactive_controls >= 1:
            score += 5
        else:
            weaknesses.append({"code": "interactive_controls", "message": "The fan page needs at least one meaningful interactive element beyond anchor navigation."})

        if text_density >= 1400:
            score += 10
        elif text_density >= 800:
            score += 5
            weaknesses.append({"code": "text_density", "message": "The page has the right structure but still needs richer supporting copy and labels."})
        else:
            weaknesses.append({"code": "text_density", "message": "The page still reads too light for a premium archive build."})

        if numeric_typography:
            score += 5
    else:
        kpi_count = _estimate_kpi_count(content_records)
        chart_regions = _estimate_chart_region_count(content_records)
        chart_points = _estimate_chart_data_points(content_records)
        table_rows, table_columns = _estimate_table_shape(content_records)
        feed_entries = _estimate_feed_entries(content_records)
        support_module_count = _estimate_support_module_count(content_records)

        if kpi_count >= 4:
            score += 20
        elif kpi_count >= 2:
            score += 10
            weaknesses.append({"code": "kpi_sparse", "message": "KPI coverage is present but still below a full four-card row."})
        else:
            weaknesses.append({"code": "kpi_sparse", "message": "The app does not yet present a convincing populated KPI row."})

        if chart_regions >= 1 and chart_points >= 7:
            score += 20
        elif chart_regions >= 1:
            score += 10
            weaknesses.append({"code": "chart_underdeveloped", "message": "A chart region exists, but it looks underdeveloped or low-detail."})
        else:
            weaknesses.append({"code": "chart_missing", "message": "The app shell is missing a clear primary chart region."})

        if table_rows >= 6 and table_columns >= 4:
            score += 15
        elif table_rows >= 3 and table_columns >= 3:
            score += 8
            weaknesses.append({"code": "table_sparse", "message": "The data table exists, but it is too shallow for a publishable app shell."})
        else:
            weaknesses.append({"code": "table_sparse", "message": "The app needs a richer holdings or data table with multiple rows and columns."})

        if feed_entries >= 4:
            score += 10
        elif feed_entries >= 1:
            score += 5
            weaknesses.append({"code": "side_panel_thin", "message": "The supporting watchlist or activity panel is present but too thin."})
        else:
            weaknesses.append({"code": "side_panel_thin", "message": "The shell needs a watchlist, activity feed, or supporting panel with real entries."})

        if support_module_count >= 2:
            score += 5
        elif support_module_count == 1:
            score += 2
            weaknesses.append({"code": "side_panel_thin", "message": "Strict app shells need at least two distinct support modules, such as watchlist plus activity or alerts plus news."})
        else:
            weaknesses.append({"code": "side_panel_thin", "message": "The shell needs multiple support modules such as watchlist, activity, alerts, allocation, or news."})

        if panel_count >= 5:
            score += 5
        elif panel_count >= 3:
            score += 2
            weaknesses.append({"code": "panel_stacking", "message": "The app needs more distinct content panels or sections."})
        else:
            weaknesses.append({"code": "panel_stacking", "message": "The shell does not have enough stacked content regions."})

        if interactive_controls >= 3:
            score += 10
        elif interactive_controls >= 1:
            score += 5
            weaknesses.append({"code": "interactive_controls", "message": "Interactive controls exist but feel too limited for this app type."})
        else:
            weaknesses.append({"code": "interactive_controls", "message": "The app needs more real range selectors, filters, tabs, or stateful controls."})

        if numeric_typography:
            score += 5
        else:
            weaknesses.append({"code": "numeric_typography", "message": "Numeric data needs a clearer monospace or tabular treatment."})

        if text_density >= 1800:
            score += 10
        elif text_density >= 900:
            score += 5
            weaknesses.append({"code": "text_density", "message": "The app has some seeded content, but the center still reads thin."})
        else:
            weaknesses.append({"code": "text_density", "message": "The content shell is too light and still reads like a scaffold."})

    threshold = 70 if _normalize_archetype(ui_archetype) in STRICT_APP_ARCHETYPES else 60
    passed = score >= threshold
    if family == "data_app" and _normalize_archetype(ui_archetype) in STRICT_APP_ARCHETYPES and support_module_count < 2:
        passed = False
    return {
        "passed": passed,
        "score": score,
        "threshold": threshold,
        "metrics": {
            "kpi_count": kpi_count,
            "chart_regions": chart_regions,
            "chart_points": chart_points,
            "table_rows": table_rows,
            "table_columns": table_columns,
            "feed_entries": feed_entries,
            "support_module_count": support_module_count,
            "panel_count": panel_count,
            "interactive_controls": interactive_controls,
            "text_density": text_density,
            "numeric_typography": numeric_typography,
        },
        "weaknesses": weaknesses,
    }


def evaluate_componentized_semantic_completeness(code_dir: Path, *, ui_archetype: str | None = None) -> dict[str, Any]:
    records = collect_componentized_file_records(code_dir)
    classifications = [classify_componentized_content_file(record["path"], record["content"]) for record in records]
    content_records = [
        record
        for record in records
        if next((item for item in classifications if item["path"] == record["path"]), {}).get("is_content_bearing")
    ]
    visible_strings = _visible_strings_from_records(content_records)
    visible_blob = " ".join(visible_strings)
    placeholder_hits = _placeholder_hits(visible_blob)

    numbers = _extract_display_numbers(visible_strings, " ".join(record["content"] for record in content_records))
    roundish = [token for token in numbers if _is_suspicious_round_number(token)]
    duplicate_rows = _duplicate_object_count(content_records)
    contextual_hits = sum(
        token in visible_blob.lower()
        for token in ("vs.", "vs ", "last month", "last week", "showing ", "updated ", "today", "this month")
    )
    tickers = {token for token in TICKER_RE.findall(visible_blob) if token not in {"SVG", "API", "USD"}}
    names = _name_hits(visible_strings)
    statuses = {match.lower() for match in STATUS_RE.findall(visible_blob)}
    date_hits = DATE_RE.findall(visible_blob)
    relative_hits = RELATIVE_TIME_RE.findall(visible_blob)
    metric_labels = _metric_labels(content_records)
    family = _quality_family(ui_archetype)

    dimensions = {
        "placeholder_text": {"score": 15, "max": 15, "issues": []},
        "numeric_authenticity": {"score": 15, "max": 15, "issues": []},
        "content_uniqueness": {"score": 15, "max": 15, "issues": []},
        "contextual_labeling": {"score": 10, "max": 10, "issues": []},
        "data_specificity": {"score": 10, "max": 10, "issues": []},
        "semantic_variety": {"score": 10, "max": 10, "issues": []},
        "temporal_realism": {"score": 15, "max": 15, "issues": []},
        "metric_completeness": {"score": 10, "max": 10, "issues": []},
    }

    if placeholder_hits:
        dimensions["placeholder_text"]["score"] = 0 if len(placeholder_hits) >= 3 else 8
        dimensions["placeholder_text"]["issues"].append("Placeholder content is still visible in the app copy.")

    if numbers and family == "data_app":
        ratio = len(roundish) / max(len(numbers), 1)
        if ratio > 0.6:
            dimensions["numeric_authenticity"]["score"] = 0
            dimensions["numeric_authenticity"]["issues"].append("Too many displayed values are suspiciously round.")
        elif ratio > 0.3:
            dimensions["numeric_authenticity"]["score"] = 8
            dimensions["numeric_authenticity"]["issues"].append("Displayed values still feel too round or synthetic.")
    elif _normalize_archetype(ui_archetype) in STRICT_APP_ARCHETYPES:
        dimensions["numeric_authenticity"]["score"] = 0
        dimensions["numeric_authenticity"]["issues"].append("A data-heavy app should surface real seeded numbers.")

    if duplicate_rows >= 2:
        dimensions["content_uniqueness"]["score"] = 7 if duplicate_rows < 4 else 0
        dimensions["content_uniqueness"]["issues"].append("Several data rows or repeated objects look duplicated.")

    if family == "fanpage":
        fanpage_context = _fanpage_contextual_hits(content_records)
        if fanpage_context == 0:
            dimensions["contextual_labeling"]["score"] = 6
            dimensions["contextual_labeling"]["issues"].append("The fan page needs clearer section labels or supporting descriptors.")
        elif fanpage_context == 1:
            dimensions["contextual_labeling"]["score"] = 8
            dimensions["contextual_labeling"]["issues"].append("The archive structure is present, but section labeling could be more deliberate.")
    else:
        if contextual_hits == 0:
            dimensions["contextual_labeling"]["score"] = 3
            dimensions["contextual_labeling"]["issues"].append("Charts, tables, or KPIs lack comparison or update context.")
        elif contextual_hits == 1:
            dimensions["contextual_labeling"]["score"] = 7
            dimensions["contextual_labeling"]["issues"].append("More contextual labeling is needed around charts or tables.")

    entity_names = names | _fanpage_entity_names(content_records)
    if len(tickers) < 2 and len(entity_names) < 3 and _normalize_archetype(ui_archetype) in STRICT_APP_ARCHETYPES:
        dimensions["data_specificity"]["score"] = 2
        dimensions["data_specificity"]["issues"].append("The app needs more real names, entities, or ticker symbols.")
    elif len(tickers) < 2 and len(entity_names) < 2:
        dimensions["data_specificity"]["score"] = 6
        dimensions["data_specificity"]["issues"].append("The app still needs more domain-specific entities.")

    if family == "fanpage":
        if _fanpage_category_count(content_records) < 2:
            dimensions["semantic_variety"]["score"] = 4
            dimensions["semantic_variety"]["issues"].append("Content categories do not vary enough across the page.")
    elif len(statuses) < 2:
        dimensions["semantic_variety"]["score"] = 4
        dimensions["semantic_variety"]["issues"].append("Statuses or semantic categories do not vary enough.")

    if family == "data_app":
        if not date_hits and not relative_hits:
            dimensions["temporal_realism"]["score"] = 5
            dimensions["temporal_realism"]["issues"].append("The app needs real timestamps or dates.")
        elif len(set(date_hits)) < 2 and len(relative_hits) < 2:
            dimensions["temporal_realism"]["score"] = 9
            dimensions["temporal_realism"]["issues"].append("Dates exist, but temporal detail still feels thin.")

    if len(metric_labels) < 4 and _normalize_archetype(ui_archetype) in STRICT_APP_ARCHETYPES:
        dimensions["metric_completeness"]["score"] = 4
        dimensions["metric_completeness"]["issues"].append("The KPI layer still feels incomplete or too generic.")
    elif not metric_labels and family == "data_app":
        dimensions["metric_completeness"]["score"] = 0
        dimensions["metric_completeness"]["issues"].append("The app is missing a convincing KPI layer.")

    score = sum(int(dimension["score"]) for dimension in dimensions.values())
    threshold = 70 if _normalize_archetype(ui_archetype) in STRICT_APP_ARCHETYPES else 60
    findings = [
        issue
        for dimension in dimensions.values()
        for issue in dimension["issues"]
    ]
    grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 60 else "D" if score >= 40 else "F"
    return {
        "passed": score >= threshold,
        "score": score,
        "threshold": threshold,
        "grade": grade,
        "dimensions": dimensions,
        "findings": findings,
    }


def evaluate_componentized_multi_file_completeness(code_dir: Path, *, ui_archetype: str | None = None) -> dict[str, Any]:
    records = collect_componentized_file_records(code_dir)
    classifications = [classify_componentized_content_file(record["path"], record["content"]) for record in records]
    reports: list[dict[str, Any]] = []

    pass_threshold = 70 if (ui_archetype or "").lower() in STRICT_APP_ARCHETYPES else 60
    for record in records:
        classification = next((item for item in classifications if item["path"] == record["path"]), None)
        if not classification or not classification.get("is_content_bearing"):
            continue
        reports.append(
            _evaluate_file_content(
                record,
                classification["role"],
                ui_archetype=ui_archetype,
                pass_threshold=pass_threshold,
            )
        )

    weak_files = [report for report in reports if not report["passed"]]
    strong_files = [report for report in reports if report["passed"]]
    overall_score = round(sum(report["score"] for report in reports) / len(reports)) if reports else 100

    summary_lines = [f"Evaluated {len(reports)} content-bearing files out of {len(records)} total."]
    if weak_files:
        summary_lines.append(f"{len(weak_files)} file(s) scored below threshold:")
        for report in weak_files:
            summary_lines.append(
                f"- {report['path']} [{report['role']}] {report['score']}/100: " + "; ".join(report["weaknesses"])
            )

    return {
        "passed": not weak_files,
        "overall_score": overall_score,
        "threshold": pass_threshold,
        "total_files": len(records),
        "content_files": len(reports),
        "weak_files": weak_files,
        "strong_files": strong_files,
        "classifications": classifications,
        "summary": "\n".join(summary_lines),
    }


def collect_quality_issue_codes(
    *,
    density_audit: dict[str, Any] | None = None,
    semantic_evaluation: dict[str, Any] | None = None,
    multi_file_evaluation: dict[str, Any] | None = None,
) -> list[str]:
    issues: list[str] = []
    if density_audit and not density_audit.get("passed"):
        for weakness in density_audit.get("weaknesses") or []:
            code = str(weakness.get("code") or "").strip()
            if code:
                issues.append(code)

    semantic_map = {
        "placeholder_text": "placeholder_text",
        "numeric_authenticity": "numeric_authenticity",
        "content_uniqueness": "content_uniqueness",
        "contextual_labeling": "contextual_labeling",
        "data_specificity": "data_specificity",
        "semantic_variety": "semantic_variety",
        "temporal_realism": "temporal_realism",
        "metric_completeness": "metric_completeness",
    }
    if semantic_evaluation:
        for key, payload in (semantic_evaluation.get("dimensions") or {}).items():
            score = int(payload.get("score") or 0)
            max_score = int(payload.get("max") or 0)
            has_issues = bool(payload.get("issues"))
            materially_weak = score < max_score and (has_issues or score <= max(0, max_score - 2))
            if materially_weak:
                mapped = semantic_map.get(key)
                if mapped:
                    issues.append(mapped)

    for report in (multi_file_evaluation or {}).get("weak_files") or []:
        for weakness in report.get("weakness_codes") or []:
            issues.append(str(weakness))
    for report in (multi_file_evaluation or {}).get("strong_files") or []:
        role = str(report.get("role") or "")
        score = int(report.get("score") or 0)
        if role not in {"kpi", "chart", "table", "feed"} or score >= 85:
            continue
        for weakness in report.get("weakness_codes") or []:
            issues.append(str(weakness))

    deduped: list[str] = []
    seen: set[str] = set()
    for issue in issues:
        if issue in seen:
            continue
        seen.add(issue)
        deduped.append(issue)
    return deduped


def parse_componentized_build_errors(build_result: dict[str, Any] | None, *, code_dir: Path) -> list[dict[str, Any]]:
    if not build_result:
        return []

    errors: list[dict[str, Any]] = []
    combined_logs = "\n".join(
        str(log.get("stdout") or "") + "\n" + str(log.get("stderr") or "")
        for log in (build_result.get("logs") or [])
    )
    if not combined_logs.strip():
        return []

    for match in BUILD_ERROR_PATH_RE.finditer(combined_logs):
        raw_path = match.group("path").strip()
        rel_path = _normalize_log_path(raw_path, code_dir)
        if not rel_path or rel_path.startswith("node_modules/"):
            continue
        line = int(match.group("line"))
        snippet = _extract_log_snippet(combined_logs, raw_path, line)
        error_class = _classify_build_error(snippet, rel_path)
        errors.append(
            {
                "path": rel_path,
                "line": line,
                "column": int(match.group("column") or 0) or None,
                "error_class": error_class,
                "message": snippet.strip(),
            }
        )

    if PACKAGE_JSON_PARSE_RE.search(combined_logs):
        errors.append(
            {
                "path": "package.json",
                "line": None,
                "column": None,
                "error_class": "syntax",
                "message": _extract_install_error_snippet(combined_logs, "package.json"),
            }
        )

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None, str]] = set()
    for error in errors:
        key = (error["path"], error.get("line"), error["error_class"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(error)
    return deduped


def _extract_install_error_snippet(logs: str, rel_path: str) -> str:
    lines = [line.strip() for line in logs.splitlines() if line.strip()]
    relevant = [
        line
        for line in lines
        if "package.json" in line.lower() or "json.parse" in line.lower() or "ejsonparse" in line.lower()
    ]
    snippet = " ".join(relevant[:3]).strip()
    return snippet or f"Install failed while parsing {rel_path}."


def group_componentized_build_errors_by_file(errors: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for error in errors:
        grouped.setdefault(error["path"], []).append(error)
    return grouped


def _evaluate_file_content(
    record: dict[str, Any],
    role: str,
    *,
    ui_archetype: str | None = None,
    pass_threshold: int = 60,
) -> dict[str, Any]:
    visible_strings = _extract_visible_strings(record["content"])
    visible_blob = " ".join(visible_strings)
    placeholder_hits = _placeholder_hits(visible_blob)
    weakness_codes: list[str] = []
    weaknesses: list[str] = []
    score = 100
    prop_driven_component = _is_prop_driven_component(record["content"])
    has_inline_seed_data = _has_inline_seed_data(record["content"])

    if placeholder_hits:
        score -= 25 if len(placeholder_hits) >= 2 else 12
        weakness_codes.append("placeholder_text")
        weaknesses.append("Placeholder or generic labels are still present.")

    numbers = _extract_display_numbers(visible_strings, record["content"])
    if role in {"kpi", "chart", "table", "data"} and (has_inline_seed_data or not prop_driven_component or role == "data"):
        if numbers:
            roundish = [token for token in numbers if _is_suspicious_round_number(token)]
            ratio = len(roundish) / max(len(numbers), 1)
            if ratio > 0.6:
                score -= 25
                weakness_codes.append("numeric_authenticity")
                weaknesses.append("Most displayed numeric values are too round or synthetic.")
            elif ratio > 0.3:
                score -= 12
                weakness_codes.append("numeric_authenticity")
                weaknesses.append("Several displayed numeric values still look too round.")
        elif (ui_archetype or "").lower() in {"dashboard", "fintech"}:
            score -= 20
            weakness_codes.append("numeric_authenticity")
            weaknesses.append("A data-bearing file is missing seeded numbers.")

    specificity_score = _specificity_signals(visible_strings, record["content"], role)
    if specificity_score == 0:
        score -= 25
        weakness_codes.append("content_specificity")
        weaknesses.append("The file lacks domain-specific names, entities, or labels.")
    elif specificity_score == 1:
        score -= 12
        weakness_codes.append("content_specificity")
        weaknesses.append("The file needs more specific entities, labels, or data variety.")

    if role in {"feed", "table", "data"} and (has_inline_seed_data or not prop_driven_component or role == "data"):
        temporal_score = _temporal_signals(visible_blob)
        if temporal_score == 0:
            score -= 25
            weakness_codes.append("temporal_realism")
            weaknesses.append("The file needs timestamps, dates, or more realistic recency detail.")
        elif temporal_score == 1:
            score -= 12
            weakness_codes.append("temporal_realism")
            weaknesses.append("The file has limited date or timestamp variety.")

    if (
        role == "table"
        and (ui_archetype or "").lower() == "fintech"
        and (has_inline_seed_data or not prop_driven_component)
        and not _has_fintech_table_trend_cues(record["content"])
    ):
        score -= 18
        weakness_codes.append("table_trend_missing")
        weaknesses.append("Fintech tables need explicit row-level trend cues such as sparklines or mini trend markers.")

    score = max(score, 0)
    return {
        "path": record["path"],
        "role": role,
        "score": score,
        "passed": score >= pass_threshold,
        "weaknesses": weaknesses,
        "weakness_codes": weakness_codes,
    }


def _metric_labels(records: list[dict[str, Any]]) -> list[str]:
    labels: list[str] = []
    for record in records:
        classification = classify_componentized_content_file(record["path"], record["content"])
        if classification["role"] not in KPI_ROLES:
            continue
        for value in _extract_visible_strings(record["content"]):
            lower = value.lower()
            if any(hint in lower for hint in KPI_LABEL_HINTS):
                labels.append(value)
    return list(dict.fromkeys(labels))


def _extract_seed_object_entries(source: str) -> list[str]:
    entries: list[str] = []
    for match in OBJECT_ENTRY_RE.findall(source):
        normalized = " ".join(match.split())
        lower = normalized.lower()
        if ";" in normalized or "<" in normalized or "classname" in lower or "font-family" in lower:
            continue
        if not any(token in lower for token in ("label:", "symbol:", "name:", "time:", "date:", "value:", "price:", "delta:", "status:")):
            continue
        if not (re.search(r"['\"]", normalized) and re.search(r"\d", normalized)):
            continue
        entries.append(normalized)
    return entries


def _has_inline_seed_data(source: str) -> bool:
    lower = source.lower()
    return bool(
        INLINE_DATA_ARRAY_RE.search(source)
        or re.search(r"\b(?:const|let|var)\s+initial[a-z0-9_]*\s*=\s*\[", lower)
        or len(_extract_seed_object_entries(source)) >= 2
    )


def _is_prop_driven_component(source: str) -> bool:
    lower = source.lower()
    return (
        ("props" in lower or "react.fc<" in lower or ("interface " in lower and "props" in lower))
        and not _has_inline_seed_data(source)
    )


def _estimate_kpi_count(records: list[dict[str, Any]]) -> int:
    labels = _metric_labels(records)
    label_prop_count = 0
    card_count = 0
    total = 0
    for record in records:
        classification = classify_componentized_content_file(record["path"], record["content"])
        if classification["role"] in KPI_ROLES:
            lower = record["content"].lower()
            total += lower.count("kpi")
            total += lower.count("metric")
            label_prop_count += len(re.findall(r"\blabel\s*=\s*[\{\"']", record["content"]))
            label_prop_count += len(re.findall(r"\blabel\s*:\s*['\"]", record["content"]))
            card_count += lower.count("kpi-card")
    return min(max(len(labels), label_prop_count, card_count, total), 8)


def _estimate_chart_data_points(records: list[dict[str, Any]]) -> int:
    count = 0
    for record in records:
        classification = classify_componentized_content_file(record["path"], record["content"])
        if classification["role"] not in CHART_ROLES:
            continue
        content = record["content"]
        count += len(re.findall(r"\d+\s*,\s*\d+", content))
        count += len(re.findall(r"\b(?:x|y|value|close|open|high|low)\s*:", content, re.IGNORECASE))
    return count


def _estimate_chart_region_count(records: list[dict[str, Any]]) -> int:
    count = 0
    chart_signals = ROLE_SIGNAL_PATTERNS["chart"] + ("<svg", "chart-panel", "chart-title", "axis-label", "candlestick-chart")
    for record in records:
        classification = classify_componentized_content_file(record["path"], record["content"])
        if classification["role"] == "chart":
            count += 1
            continue
        if classification["role"] not in CHART_ROLES:
            continue
        lower = record["content"].lower()
        signal_hits = sum(1 for signal in chart_signals if signal in lower)
        has_svg = "<svg" in lower
        if (has_svg and signal_hits >= 2) or signal_hits >= 3:
            count += 1
    return count


def _estimate_table_shape(records: list[dict[str, Any]]) -> tuple[int, int]:
    rows = 0
    columns: set[str] = set()
    column_re = re.compile(r"\b(?:symbol|asset|name|price|value|amount|shares|allocation|status|date|type|change|sector|volume)\b", re.IGNORECASE)
    for record in records:
        classification = classify_componentized_content_file(record["path"], record["content"])
        if classification["role"] not in TABLE_ROLES:
            continue
        content = record["content"]
        rows += max(len(re.findall(r"\b(?:asset|symbol|id|name)\s*:\s*['\"]", content, re.IGNORECASE)), content.lower().count("<tr"))
        columns.update(match.lower() for match in column_re.findall(content))
    return rows, len(columns)


def _estimate_feed_entries(records: list[dict[str, Any]]) -> int:
    count = 0
    for record in records:
        classification = classify_componentized_content_file(record["path"], record["content"])
        if classification["role"] not in FEED_ROLES:
            continue
        content = record["content"]
        count += len(RELATIVE_TIME_RE.findall(content))
        count += len(DATE_RE.findall(content))
        count += len(re.findall(r"\b(?:watchlist|activity|alert|notification|transaction)\b", content, re.IGNORECASE)) // 2
    return count


def _estimate_support_module_count(records: list[dict[str, Any]]) -> int:
    found: set[str] = set()
    for record in records:
        classification = classify_componentized_content_file(record["path"], record["content"])
        if classification["role"] not in {"feed", "chart", "table", "page", "data"}:
            continue
        haystack = f"{record['path']}\n{record['content']}".lower()
        for category, hints in SUPPORT_MODULE_HINTS.items():
            if any(hint in haystack for hint in hints):
                found.add(category)
    return len(found)


def _estimate_panel_count(records: list[dict[str, Any]]) -> int:
    count = 0
    for record in records:
        content = record["content"].lower()
        count += content.count("<section")
        count += content.count('classname="card')
        count += content.count("classname='card")
    return max(count, len(records))


def _estimate_interactive_control_count(records: list[dict[str, Any]]) -> int:
    count = 0
    for record in records:
        content = record["content"].lower()
        count += content.count("onclick")
        count += content.count("onchange")
        count += content.count("onsubmit")
        count += content.count("selectedrange")
        count += content.count("filter")
        count += content.count("sort")
    return count


def _has_numeric_typography(records: list[dict[str, Any]]) -> bool:
    combined = "\n".join(record["content"].lower() for record in records)
    return any(token in combined for token in ("font-variant-numeric", "tabular-nums", "jetbrains mono", "roboto mono", "dm mono", "space mono", "text-mono"))


def _has_fintech_table_trend_cues(source: str) -> bool:
    normalized = source.lower()
    explicit_tokens = (
        "sparkline",
        "mini-chart",
        "micro-chart",
        "trendline",
        "trend-line",
        "price history",
        "trend path",
    )
    if any(token in normalized for token in explicit_tokens):
        return True
    return bool(
        re.search(r"\b(?:sparkline|trend|history)\s*:", normalized)
        or re.search(r"classname\s*=\s*[\"'][^\"']*(?:sparkline|trend)[^\"']*[\"']", source, re.IGNORECASE)
        or re.search(r"<svg[\s\S]{0,180}(?:sparkline|trend)", source, re.IGNORECASE)
    )


def _duplicate_object_count(records: list[dict[str, Any]]) -> int:
    serialized: list[str] = []
    for record in records:
        if Path(record["path"]).suffix.lower() in {".css", ".json"}:
            continue
        for match in _extract_seed_object_entries(record["content"]):
            normalized = " ".join(match.split())
            if 20 <= len(normalized) <= 220:
                serialized.append(normalized)
    duplicates = 0
    seen: dict[str, int] = {}
    for entry in serialized:
        seen[entry] = seen.get(entry, 0) + 1
    for count in seen.values():
        if count > 1:
            duplicates += count - 1
    return duplicates


def _name_hits(strings: list[str]) -> set[str]:
    names: set[str] = set()
    for value in strings:
        words = value.split()
        if len(words) >= 2 and words[0][:1].isupper() and words[1][:1].isupper():
            names.add(" ".join(words[:2]))
        if COMPANY_SUFFIX_RE.search(value):
            names.add(value)
    return names


def _specificity_signals(strings: list[str], source: str, role: str) -> int:
    blob = " ".join(strings)
    tickers = {token for token in TICKER_RE.findall(blob) if token not in {"SVG", "API", "USD"}}
    names = _name_hits(strings)
    statuses = {match.lower() for match in STATUS_RE.findall(blob)}
    ids = re.findall(r"\b(?:tx|ord|trade|acct|portfolio)[-_ ]?[A-Z0-9]{3,}\b", blob, re.IGNORECASE)

    signal_count = 0
    if names:
        signal_count += 1
    if tickers:
        signal_count += 1
    if len(statuses) >= 2:
        signal_count += 1
    if ids:
        signal_count += 1
    if role == "kpi" and _metric_labels([{"path": "tmp", "content": source}]):
        signal_count += 1
    return min(signal_count, 2)


def _temporal_signals(text: str) -> int:
    has_relative = bool(RELATIVE_TIME_RE.search(text))
    has_dates = bool(DATE_RE.search(text))
    if has_relative and has_dates:
        return 2
    if has_relative or has_dates:
        return 1
    return 0


def _normalize_log_path(raw_path: str, code_dir: Path) -> str:
    cleaned = raw_path.replace("\\", "/").strip()
    path = Path(cleaned)
    try:
        if path.is_absolute():
            return path.relative_to(code_dir).as_posix()
    except ValueError:
        pass

    parts = cleaned.split("/")
    if "src" in parts:
        return "/".join(parts[parts.index("src"):])
    if cleaned.startswith("index.html"):
        return "index.html"
    return cleaned


def _extract_log_snippet(log_text: str, raw_path: str, line: int) -> str:
    target = raw_path.replace("\\", "/")
    for chunk in log_text.splitlines():
        normalized = chunk.replace("\\", "/")
        if target in normalized and f":{line}" in normalized:
            return chunk
    return f"{raw_path}:{line}"


def _classify_build_error(message: str, rel_path: str) -> str:
    lower = message.lower()
    if any(token in lower for token in ("failed to resolve import", "could not resolve", "cannot find module", "does not exist")):
        return "asset" if rel_path.endswith(".css") or any(token in lower for token in (".css", ".png", ".jpg", ".svg", ".woff")) else "import"
    if any(token in lower for token in ("no matching export", "does not provide an export", "export named")):
        return "cross_file"
    if any(token in lower for token in ("property", "is not assignable", "cannot find name", "does not exist on type")):
        return "type"
    if any(token in lower for token in ("unterminated", "unexpected", "expected", "jsx", "parse")):
        return "syntax"
    return "runtime"


def _count_roles(classifications: list[dict[str, Any]], role: str) -> int:
    return sum(1 for classification in classifications if classification.get("role") == role)
