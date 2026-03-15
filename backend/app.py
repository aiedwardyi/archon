from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import json
import os
import shutil
import sys
import warnings
import re
import mimetypes
from pathlib import Path
from typing import Any, Dict
import threading
import time
from datetime import datetime, timezone

# Suppress SQLAlchemy legacy Query.get() deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlalchemy")

from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request
from models import Project, Execution, User, get_session, init_db, get_next_version
from auth import auth_bp, claim_guest_project_for_user, init_jwt

# NLU Agent — sentiment + keyword analysis before pipeline routing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.nlu_agent import NLUAgent
from agents.engineer_agent import DESIGN_KIT_ALIASES
from utils.reference_build_registry import (
    get_archetype_benchmark_guidance,
    load_local_reference_build,
    suggest_reference_archetype,
)
from utils.watson_discovery import DiscoveryClient
from utils.image_asset_catalog import catalog_design_assets
from utils.asset_filler import fill_missing_assets
from utils.offline_engineer_scaffold import build_vite_react_ts_scaffold
from utils.componentized_runtime import (
    build_componentized_preview,
    collect_componentized_direct_dependencies,
    collect_componentized_editable_files,
    collect_componentized_reverse_dependents,
    collect_existing_code_context,
    collect_selected_code_context,
    ensure_componentized_workspace_support,
    extract_feature_inventory,
    extract_visual_dna,
    infer_scaffold_mode,
    is_componentized_workspace,
    relative_mount_root,
    rewrite_componentized_asset_api_urls,
    rewrite_preview_file_references,
    rewrite_preview_runtime_asset_references,
    stage_componentized_design_assets,
    summarize_componentized_build_error,
)
from utils.componentized_quality import (
    classify_componentized_content_file,
    collect_quality_issue_codes,
    evaluate_componentized_density,
    evaluate_componentized_multi_file_completeness,
    evaluate_componentized_semantic_completeness,
    group_componentized_build_errors_by_file,
    parse_componentized_build_errors,
)
nlu_agent = NLUAgent()
discovery_client = DiscoveryClient()

app = Flask(__name__)

CORS(app, origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:8080"])

# ── Smart Request Log Filter ──────────────────────────────────
# Suppresses noisy duplicate requests from frontend polling while
# keeping all unique/important requests visible in the console.
import logging as _logging

class _RequestLogFilter(_logging.Filter):
    """Filter werkzeug request logs to reduce noise."""

    # Endpoints that get polled repeatedly — only log every Nth occurrence
    _POLL_ENDPOINTS = {
        "/api/health",
        "/api/stats",
        "/api/activity",
        "/api/projects",
        "/api/execution-status",
    }
    _POLL_LOG_EVERY = 999  # rely on time-based logging instead

    def __init__(self):
        super().__init__()
        self._poll_counts: dict[str, int] = {}
        self._last_logged: dict[str, float] = {}

    def filter(self, record: _logging.LogRecord) -> bool:
        msg = record.getMessage()

        # Always suppress OPTIONS preflight requests
        if '"OPTIONS ' in msg:
            return False

        # Suppress polling endpoints (log every Nth or every 30s)
        for endpoint in self._POLL_ENDPOINTS:
            if endpoint in msg:
                self._poll_counts[endpoint] = self._poll_counts.get(endpoint, 0) + 1
                now = time.time()
                last = self._last_logged.get(endpoint, 0)
                count = self._poll_counts[endpoint]

                # Log once every 3 seconds per polling endpoint
                if count == 1 or (now - last) >= 3:
                    self._last_logged[endpoint] = now
                    # Annotate with count so you know how many were suppressed
                    if count > 1:
                        record.msg = f"{msg}  [×{count}]"
                        record.args = None  # clear args so %s formatting doesn't break
                    return True
                return False

        # Everything else: pass through
        return True

# Attach filter to werkzeug's logger
_logging.getLogger("werkzeug").addFilter(_RequestLogFilter())
# ──────────────────────────────────────────────────────────────

app.register_blueprint(auth_bp)
jwt = init_jwt(app)

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = REPO_ROOT / "generated"
SEED_DATA_DIR = REPO_ROOT / "backend" / "seed_data"
SEED_PROJECTS = [
    {
        "name": "FF7 — Avalanche Archive",
        "description": (
            "A fan tribute site for Final Fantasy VII with character profiles, "
            "weapons gallery, and interactive world map"
        ),
        "archetype": "game",
        "folder": "avalanche",
        "original_project_id": 71,
    },
    {
        "name": "FF7 — Midgar Archives",
        "description": (
            "An interactive Final Fantasy VII database with search, filtering, "
            "grid/list views, and character detail modals"
        ),
        "archetype": "game",
        "folder": "midgar",
        "original_project_id": 38,
    },
]

execution_state: dict = {}  # keyed by project_id (int)

def get_project_state(project_id: int) -> dict:
    if project_id not in execution_state:
        execution_state[project_id] = {
            "running": False,
            "started_at": None,
            "current_execution_id": None,
            "logs": [],
            "result_ready": False,
        }
    return execution_state[project_id]

def any_pipeline_running() -> bool:
    return any(s.get("running") for s in execution_state.values())


def read_json_file(filepath: Path) -> Dict[str, Any] | None:
    try:
        if not filepath.exists():
            return None
        return json.loads(filepath.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None


def write_json_file(filepath: Path, data: Dict[str, Any]) -> bool:
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        tmp = filepath.with_suffix(filepath.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(filepath)
        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}")
        return False


_log_counter = 0

def add_log(message: str, log_type: str = "info", project_id: int = None):
    global _log_counter
    _log_counter += 1
    ts = int(time.time() * 1000)
    print(f"[LOG] {message}")
    if project_id is None:
        return
    get_project_state(project_id)["logs"].append({
        "id": f"log-{ts}-{_log_counter}",
        "timestamp": ts,
        "message": message,
        "type": log_type,
    })


def get_version_dir(project_id: int, version: int) -> Path:
    return PUBLIC_DIR / str(project_id) / f"v{version}"


def get_plan_data_for_version(project_id: int, version: int) -> Dict[str, Any] | None:
    return read_json_file(get_version_dir(project_id, version) / "last_plan.json")


def build_componentized_version(version_dir: Path) -> Dict[str, Any]:
    code_dir = version_dir / "code"
    result = build_componentized_preview(code_dir)
    write_json_file(version_dir / "last_preview_build.json", result)
    return result


def get_preview_target(project_id: int, version: int) -> tuple[Path | None, str]:
    version_dir = get_version_dir(project_id, version)
    code_dir = version_dir / "code"
    plan_data = get_plan_data_for_version(project_id, version)

    if is_componentized_workspace(code_dir, plan_data=plan_data):
        dist_index = code_dir / "dist" / "index.html"
        if not dist_index.exists():
            build_componentized_version(version_dir)
        if dist_index.exists():
            return dist_index, "componentized_app"
        return None, "componentized_app"

    html_file = code_dir / "src" / "index.html"
    if html_file.exists():
        return html_file, "legacy_single_page"
    if code_dir.exists():
        html_files = list(code_dir.rglob("*.html"))
        if html_files:
            return html_files[0], infer_scaffold_mode(code_dir, plan_data=plan_data)
    return None, infer_scaffold_mode(code_dir, plan_data=plan_data)


def inject_preview_base_href(html: str, *, mount_prefix: str, root_dir: str) -> str:
    base_target = f"{mount_prefix}/{root_dir}".strip("/")
    if not base_target or "<base " in html.lower():
        return html

    base_tag = f'<base href="/{base_target}/">'
    if "</head>" in html:
        return html.replace("</head>", f"  {base_tag}\n</head>", 1)
    return base_tag + html


def resolve_version_file(project_id: int, version: int, asset_path: str) -> Path | None:
    code_dir = (get_version_dir(project_id, version) / "code").resolve()
    target = (code_dir / asset_path).resolve()
    try:
        target.relative_to(code_dir)
    except ValueError:
        return None
    if not target.exists() or not target.is_file():
        return None
    return target


def load_componentized_base_css(ui_archetype: str | None) -> str | None:
    if not ui_archetype:
        return None
    kit_archetype = DESIGN_KIT_ALIASES.get(ui_archetype, ui_archetype)
    css_path = REPO_ROOT / "prompts" / "archetypes" / f"{kit_archetype}.css"
    if not css_path.exists():
        return None
    return css_path.read_text(encoding="utf-8")


def build_design_context(
    *,
    version_dir: Path,
    design_assets: list[dict[str, Any]],
    project_id: int,
    version: int,
    scaffold_mode: str,
) -> str:
    if not design_assets:
        return ""

    asset_lines: list[str] = []
    if scaffold_mode == "componentized_app":
        staged_assets = stage_componentized_design_assets(version_dir, design_assets)
        for asset in staged_assets:
            asset_lines.append(f"  - {asset['key']} ({asset['purpose']}): {asset['path']}")
        if not asset_lines:
            return ""
        return (
            "\n\nDESIGN ASSETS - USE THESE LOCAL APP ASSETS:\n"
            + "\n".join(asset_lines)
            + "\nIMPORTANT: Use these exact local paths in <img> tags or CSS background-image. "
              "Do not emit backend API asset URLs in componentized apps.\n"
        )

    for asset in design_assets:
        asset_version = version
        if asset.get("local_path"):
            lp = asset["local_path"].replace("\\", "/")
            parts = lp.split("/")
            for part in parts:
                if part.startswith("v") and part[1:].isdigit():
                    asset_version = int(part[1:])
                    break
        img_url = f"/api/assets/{project_id}/{asset_version}/{asset['key']}.png" if asset.get("local_path") else asset["url"]
        asset_lines.append(f"  - {asset['key']} ({asset['purpose']}): {img_url}")
    return (
        "\n\nDESIGN ASSETS - USE THESE IMAGE URLs IN THE HTML:\n"
        + "\n".join(asset_lines)
        + "\nIMPORTANT: Use these exact URLs in <img> tags or CSS background-image. Do not use placeholder images.\n"
    )


def build_product_brief_context(version_dir: Path) -> str:
    prd_data = read_json_file(version_dir / "last_prd.json") or {}
    prd = prd_data.get("prd", prd_data) if isinstance(prd_data, dict) else {}
    if not isinstance(prd, dict):
        return ""

    lines: list[str] = []
    title = str(prd.get("document_title") or "").strip()
    detected_intent = str(prd.get("detected_intent") or "").strip()
    primary_user_action = str(prd.get("primary_user_action") or "").strip()
    visual_direction = str(prd.get("visual_direction") or "").strip()
    archetype_hint = str(prd.get("archetype_hint") or "").strip()
    overview = str(prd.get("overview") or "").strip()
    tone_keywords = prd.get("tone_keywords") or []
    target_users = prd.get("target_users") or []

    if title:
        lines.append(f"Project: {title}")
    if detected_intent:
        lines.append(f"Detected intent: {detected_intent}")
    if primary_user_action:
        lines.append(f"Primary user action: {primary_user_action}")
    if archetype_hint:
        lines.append(f"Archetype hint: {archetype_hint}")
    if visual_direction:
        lines.append(f"Visual direction: {visual_direction}")
    if tone_keywords:
        lines.append(f"Tone keywords: {', '.join(str(item) for item in tone_keywords[:5])}")
    if target_users:
        lines.append(f"Target users: {', '.join(str(item) for item in target_users[:3])}")
    if overview:
        lines.append(f"Overview: {overview}")

    if not lines:
        return ""

    return "\n\nPRODUCT BRIEF CONTEXT:\n" + "\n".join(lines) + "\n"


def build_visual_direction_context(version_dir: Path) -> str:
    path = version_dir / "last_visual_direction.txt"
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    if not text:
        return ""
    return (
        "\n\nVISUAL DIRECTION - TREAT THIS AS THE BINDING DESIGN SYSTEM:\n"
        f"{text}\n"
    )


def load_or_extract_iteration_artifact(
    version_dir: Path,
    *,
    filename: str,
    extractor,
) -> dict[str, Any]:
    artifact_path = version_dir / filename
    artifact_data = read_json_file(artifact_path)
    if isinstance(artifact_data, dict):
        return artifact_data

    code_dir = version_dir / "code"
    extracted = extractor(code_dir) if code_dir.exists() else {}
    if isinstance(extracted, dict) and extracted:
        write_json_file(artifact_path, extracted)
    return extracted if isinstance(extracted, dict) else {}


QUALITY_PLACEHOLDER_DOMAINS = (
    "api.dicebear.com",
    "ui-avatars.com",
    "placehold.co",
    "via.placeholder.com",
    "picsum.photos",
)

SELF_REVIEW_ISSUE_MAP = {
    "spacing_layout": "spacing_rhythm",
    "typography": "typography_hierarchy",
    "color_depth": "weak_surface_depth",
    "interactivity": "dense_shell_interactivity",
    "content_authenticity": "content_authenticity",
    "polish_flow": "polish_flow",
}


def extract_componentized_self_review_issues(self_review: Any) -> list[str]:
    if not self_review:
        return []

    scores = getattr(self_review, "scores", None)
    weak_dimensions = getattr(self_review, "weak_dimensions", None) or []
    issues: list[str] = []

    for dimension, issue in SELF_REVIEW_ISSUE_MAP.items():
        score = getattr(scores, dimension, None) if scores is not None else None
        if isinstance(score, int) and score < 8:
            issues.append(issue)

    for raw_name in weak_dimensions:
        if not isinstance(raw_name, str):
            continue
        normalized = raw_name.strip().lower().replace("-", "_").replace(" ", "_")
        mapped = SELF_REVIEW_ISSUE_MAP.get(normalized)
        if mapped:
            issues.append(mapped)

    deduped: list[str] = []
    seen: set[str] = set()
    for issue in issues:
        if issue in seen:
            continue
        seen.add(issue)
        deduped.append(issue)
    return deduped


def build_componentized_self_review_context(self_review: Any) -> str:
    if not self_review:
        return ""

    scores = getattr(self_review, "scores", None)
    if scores is None:
        return ""

    weak_dimensions = getattr(self_review, "weak_dimensions", None) or []
    next_pass = getattr(self_review, "next_pass", None) or ""

    score_lines = [
        f"- spacing_layout: {getattr(scores, 'spacing_layout', 'n/a')}/10",
        f"- typography: {getattr(scores, 'typography', 'n/a')}/10",
        f"- color_depth: {getattr(scores, 'color_depth', 'n/a')}/10",
        f"- interactivity: {getattr(scores, 'interactivity', 'n/a')}/10",
        f"- content_authenticity: {getattr(scores, 'content_authenticity', 'n/a')}/10",
        f"- polish_flow: {getattr(scores, 'polish_flow', 'n/a')}/10",
    ]

    weak_line = ", ".join(str(item) for item in weak_dimensions if item) or "none"
    next_pass_line = str(next_pass).strip() or "none"
    return (
        "MODEL SELF-REVIEW FOR THE CURRENT BUILD:\n"
        + "\n".join(score_lines)
        + f"\n- weak_dimensions: {weak_line}\n"
        + f"- next_pass: {next_pass_line}"
    )


def get_missing_componentized_contract_paths(files: list[Any]) -> list[str]:
    required = set(get_componentized_required_contract_paths())
    present = {
        str(getattr(file_artifact, "path", "")).replace("\\", "/").strip("/")
        for file_artifact in files or []
    }
    return sorted(path for path in required if path not in present)


def get_componentized_required_contract_paths() -> list[str]:
    return [
        "package.json",
        "index.html",
        "src/main.tsx",
        "src/App.tsx",
    ]


COMPONENTIZED_CONTRACT_MIN_LENGTHS = {
    "package.json": 60,
    "index.html": 120,
    "src/main.tsx": 80,
    "src/App.tsx": 120,
}


def validate_componentized_contract_outputs(
    files: list[Any],
    *,
    ui_archetype: str | None = None,
) -> dict[str, Any]:
    normalized_files = {
        str(getattr(file_artifact, "path", "")).replace("\\", "/").strip("/"): str(getattr(file_artifact, "content", "") or "")
        for file_artifact in files or []
        if str(getattr(file_artifact, "path", "")).strip()
    }
    workspace_blob = "\n".join(normalized_files.values()).lower()
    workspace_paths = set(normalized_files.keys())
    violations: list[dict[str, str]] = []
    required_paths = get_componentized_required_contract_paths()

    if not normalized_files:
        violations.append(
            {
                "path": "*",
                "code": "empty_output",
                "message": "The response returned no files for the componentized workspace.",
            }
        )

    for rel_path in required_paths:
        content = normalized_files.get(rel_path)
        if content is None:
            violations.append(
                {
                    "path": rel_path,
                    "code": "missing_file",
                    "message": f"The required workspace file `{rel_path}` is missing.",
                }
            )
            continue

        stripped = content.strip()
        if not stripped:
            violations.append(
                {
                    "path": rel_path,
                    "code": "empty_file",
                    "message": f"The required workspace file `{rel_path}` is empty.",
                }
            )
            continue

        min_length = COMPONENTIZED_CONTRACT_MIN_LENGTHS.get(rel_path, 40)
        if len(stripped) < min_length:
            if rel_path == "src/App.tsx" and ui_archetype in {"dashboard", "fintech"}:
                required_markers = ("kpi", "chart", "watch", "watchlist", "table", "portfolio", "activity", "holdings")
                workspace_marker_hits = sum(1 for marker in required_markers if marker in workspace_blob)
                structural_paths = sum(
                    1
                    for path in workspace_paths
                    if path.startswith(("src/pages/", "src/components/"))
                    and any(token in path.lower() for token in ("dashboard", "chart", "kpi", "watch", "table", "activity", "holdings"))
                )
                stripped_lower = stripped.lower()
                delegated_shell = (
                    "./pages/" in stripped_lower
                    and workspace_marker_hits >= 3
                    and structural_paths >= 2
                )
                if delegated_shell:
                    continue
            violations.append(
                {
                    "path": rel_path,
                    "code": "too_short",
                    "message": f"The required workspace file `{rel_path}` is too short to be a real implementation.",
                }
            )

    package_json = normalized_files.get("package.json", "")
    if package_json:
        lowered = package_json.lower()
        if '"build"' not in lowered or "vite build" not in lowered:
            violations.append(
                {
                    "path": "package.json",
                    "code": "missing_build_script",
                    "message": "package.json must include a real build script for the Vite workspace.",
                }
            )

    index_html = normalized_files.get("index.html", "")
    if index_html:
        lowered = index_html.lower()
        if "<!doctype html" not in lowered:
            violations.append(
                {
                    "path": "index.html",
                    "code": "no_doctype",
                    "message": "index.html must declare a doctype.",
                }
            )
        if 'id="root"' not in lowered and "id='root'" not in lowered:
            violations.append(
                {
                    "path": "index.html",
                    "code": "no_root_container",
                    "message": "index.html must include a root mounting container.",
                }
            )

    main_source = normalized_files.get("src/main.tsx", "")
    if main_source:
        lowered = main_source.lower()
        if "import app from" not in lowered and 'from "./app"' not in lowered:
            violations.append(
                {
                    "path": "src/main.tsx",
                    "code": "no_app_import",
                    "message": "src/main.tsx must import App from the local workspace.",
                }
            )
        if "createroot" not in lowered and "reactdom.render" not in lowered:
            violations.append(
                {
                    "path": "src/main.tsx",
                    "code": "no_root_mount",
                    "message": "src/main.tsx must mount the React app into the root container.",
                }
            )
    app_source = normalized_files.get("src/App.tsx", "")
    if app_source:
        lowered = app_source.lower()
        if "export default" not in lowered:
            violations.append(
                {
                    "path": "src/App.tsx",
                    "code": "no_component_export",
                    "message": "src/App.tsx must export a default React component.",
                }
            )
        if "return" not in lowered and "<main" not in lowered and "<div" not in lowered and "<section" not in lowered:
            violations.append(
                {
                    "path": "src/App.tsx",
                    "code": "jsx_stub",
                    "message": "src/App.tsx must render real JSX, not an empty stub.",
                }
            )
        if ui_archetype in {"dashboard", "fintech"}:
            required_markers = ("kpi", "chart", "watch", "watchlist", "table", "portfolio", "activity", "holdings")
            workspace_marker_hits = sum(1 for marker in required_markers if marker in workspace_blob)
            structural_paths = sum(
                1
                for path in workspace_paths
                if path.startswith(("src/pages/", "src/components/"))
                and any(token in path.lower() for token in ("dashboard", "chart", "kpi", "watch", "table", "activity", "holdings"))
            )
            if workspace_marker_hits < 3 and structural_paths < 2:
                violations.append(
                    {
                        "path": "src/App.tsx",
                        "code": "thin_app_shell",
                        "message": "The componentized app shell is too thin for a dense app-like archetype.",
                    }
                )

    missing_paths = sorted(
        {
            violation["path"]
            for violation in violations
            if violation["code"] == "missing_file"
        }
    )
    return {
        "passed": not violations,
        "violations": violations,
        "missing_paths": missing_paths,
        "required_paths": required_paths,
    }


def format_componentized_contract_violations(contract_validation: dict[str, Any] | None) -> str:
    if not contract_validation:
        return ""
    violations = contract_validation.get("violations") or []
    if not violations:
        return ""
    lines = []
    for violation in violations:
        path = violation.get("path") or "*"
        code = violation.get("code") or "contract_violation"
        message = violation.get("message") or "Unknown contract issue."
        lines.append(f"- [{code}] {path}: {message}")
    return "\n".join(lines)


def enforce_componentized_internal_scope(allowed_files: list[str], outputs: list[Any]) -> None:
    from scripts.safe_write import enforce_iteration_scope

    enforce_iteration_scope(allowed_files, outputs)


def detect_componentized_quality_issues(code_dir: Path, *, ui_archetype: str | None) -> list[str]:
    context = collect_existing_code_context(
        code_dir,
        max_files=96,
        max_chars_per_file=16_000,
    ) or ""
    if not context:
        return []

    normalized = context.lower()
    issues: list[str] = []
    display_font_markers = (
        "space grotesk",
        "outfit",
        "manrope",
        "dm sans",
        "plus jakarta",
        "cabinet grotesk",
        "general sans",
        "satoshi",
        "switzer",
        "clash",
    )
    mono_markers = (
        "jetbrains mono",
        "fira code",
        "ibm plex mono",
        "font-variant-numeric",
        "tabular-nums",
        "data-mono",
        "font-mono",
    )

    if (
        ui_archetype in {"dashboard", "fintech", "editor", "kanban", "chat"}
        and ("intersectionobserver" in normalized or "hidden-section" in normalized)
        and ("opacity: 0" in normalized or "visibility: hidden" in normalized)
    ):
        issues.append("first_paint_visibility")

    if any(domain in normalized for domain in QUALITY_PLACEHOLDER_DOMAINS):
        issues.append("external_placeholder_assets")

    hover_count = normalized.count(":hover")
    font_family_count = normalized.count("font-family")
    title_scale_too_small = bool(
        re.search(
            r"\.(?:page-title|brand-name|chart-title)\s*\{[^{}]*font-size:\s*(?:1\.\d+rem|2[0-9]px|30px|31px)\b",
            normalized,
            re.DOTALL,
        )
    )
    elevated_surface_present = bool(
        re.search(
            r"\.(?:card|kpi-card|panel|main-chart-area|hero-chart)\s*\{[^{}]*(?:linear-gradient|radial-gradient)",
            normalized,
            re.DOTALL,
        )
    )
    layered_shadow_present = bool(re.search(r"box-shadow\s*:\s*[^;]+,[^;]+;", normalized))
    if ui_archetype in {"dashboard", "fintech", "editor", "kanban", "chat"}:
        if not any(marker in normalized for marker in display_font_markers) or font_family_count < 2 or title_scale_too_small:
            issues.append("typography_hierarchy")
        if hover_count < 6 or "focus-visible" not in normalized:
            issues.append("polish_flow")

    if ui_archetype in {"dashboard", "fintech"}:
        interaction_signal_count = sum(
            normalized.count(token)
            for token in ("onclick", "onchange", "onsubmit", "usestate(", "setinterval", "settimeout")
        )
        if interaction_signal_count < 6:
            issues.append("dense_shell_interactivity")
        if not any(token in normalized for token in mono_markers):
            issues.append("numeric_data_typography")
        support_rail_signal_count = sum(
            1 for token in ("watchlist", "activity-feed", "news-feed", "alerts", "feed-item", "watch-item") if token in normalized
        )
        if support_rail_signal_count < 2:
            issues.append("panel_stacking")

    if ui_archetype in {"dashboard", "fintech"}:
        gradient_signal_count = normalized.count("linear-gradient") + normalized.count("radial-gradient")
        if gradient_signal_count < 2 or normalized.count("box-shadow") < 5 or not elevated_surface_present or not layered_shadow_present:
            issues.append("weak_surface_depth")
    elif "linear-gradient" not in normalized and "radial-gradient" not in normalized and normalized.count("box-shadow") < 2:
        issues.append("weak_surface_depth")

    return issues


def format_density_audit_context(density_audit: dict[str, Any] | None) -> str:
    if not density_audit:
        return ""

    metric_lines = []
    for key, value in (density_audit.get("metrics") or {}).items():
        metric_lines.append(f"- {key}: {value}")

    weakness_lines = [
        f"- [{item.get('code')}] {item.get('message')}"
        for item in (density_audit.get("weaknesses") or [])
        if item.get("code") or item.get("message")
    ]

    return (
        "LOCAL DENSITY AUDIT:\n"
        f"- score: {density_audit.get('score')}/{density_audit.get('threshold')}\n"
        f"- passed: {density_audit.get('passed')}\n"
        + ("\n".join(metric_lines) + "\n" if metric_lines else "")
        + ("Weaknesses:\n" + "\n".join(weakness_lines) if weakness_lines else "Weaknesses: none")
    ).strip()


def format_semantic_evaluation_context(semantic_evaluation: dict[str, Any] | None) -> str:
    if not semantic_evaluation:
        return ""

    dimension_lines = []
    for key, payload in (semantic_evaluation.get("dimensions") or {}).items():
        issues = payload.get("issues") or []
        issue_text = "; ".join(issues) if issues else "ok"
        dimension_lines.append(f"- {key}: {payload.get('score')}/{payload.get('max')} ({issue_text})")

    return (
        "LOCAL SEMANTIC EVALUATION:\n"
        f"- score: {semantic_evaluation.get('score')}/{semantic_evaluation.get('threshold', 100)}\n"
        f"- grade: {semantic_evaluation.get('grade')}\n"
        f"- passed: {semantic_evaluation.get('passed')}\n"
        + "\n".join(dimension_lines)
    ).strip()


def format_multi_file_evaluation_context(multi_file_evaluation: dict[str, Any] | None) -> str:
    if not multi_file_evaluation:
        return ""

    weak_lines = []
    for report in (multi_file_evaluation.get("weak_files") or [])[:8]:
        weakness_text = "; ".join(report.get("weaknesses") or []) or "no details"
        weak_lines.append(
            f"- {report.get('path')} [{report.get('role')}] {report.get('score')}/100: {weakness_text}"
        )

    strong_lines = []
    for report in (multi_file_evaluation.get("strong_files") or [])[:6]:
        strong_lines.append(
            f"- {report.get('path')} [{report.get('role')}] {report.get('score')}/100"
        )

    body = [
        "LOCAL MULTI-FILE CONTENT EVALUATION:",
        f"- overall_score: {multi_file_evaluation.get('overall_score')}",
        f"- threshold: {multi_file_evaluation.get('threshold')}",
        f"- content_files: {multi_file_evaluation.get('content_files')}",
        f"- passed: {multi_file_evaluation.get('passed')}",
    ]
    if weak_lines:
        body.append("Weak files:")
        body.extend(weak_lines)
    if strong_lines:
        body.append("Strong files (leave untouched unless needed for coherence):")
        body.extend(strong_lines)
    return "\n".join(body).strip()


def build_componentized_shell_polish_guidance(ui_archetype: str | None) -> str:
    if ui_archetype == "dashboard":
        return (
            "APP-SHELL POLISH TARGET FOR DASHBOARD:\n"
            "- Keep the product reading like analytics or operations, not a trading terminal.\n"
            "- Use the display font for the brand, page title, panel titles, and other short high-importance headings. Keep the UI sans for controls/body copy and the mono family for KPI values, chart labels, table numerics, and timestamps.\n"
            "- The desktop page title should land in a real display range, roughly 36-44px, and the KPI row should arrive within about 24-32px of the header. Do not leave a dead vertical gap before the first data cards.\n"
            "- The header bar should feel like a real command surface: title plus status/action cluster, with a subtle tint or blur instead of a flat strip.\n"
            "- Strengthen depth with three surface levels: page backdrop, standard panel, and one clearly elevated highlight card or panel. Prefer layered shadows and soft gradients over flat slabs.\n"
            "- Charts should feel authored, not default library output: use a thicker line or richer area fill, clearer axis treatment, and a more intentional control rail than plain ghost buttons.\n"
            "- The desktop support rail must carry real visual weight. Stack at least two secondary modules or split the right rail into clearly separated subsections instead of leaving one lonely side card.\n"
            "- Nav items, chips, table rows, badges, and action links need visible hover and active states.\n"
            "- Replace any remote avatar placeholders with styled initials, local assets, or inline SVG treatments.\n"
        )
    if ui_archetype == "fintech":
        return (
            "APP-SHELL POLISH TARGET FOR FINTECH:\n"
            "- Keep the shell chart-first and market-focused. It should feel like a brokerage or monitoring workspace, not a generic admin dashboard.\n"
            "- Use the display font for the brand, page title, chart title, and key section headers. Keep the UI sans for controls and JetBrains Mono or equivalent for all prices, deltas, holdings, timestamps, and chart labels.\n"
            "- The desktop page title should read like a headline, roughly 36-44px, with a compact header-to-KPI transition instead of a large blank strip above the first cards.\n"
            "- Push a stronger page-to-panel depth stack with tinted panels, layered shadows, subtle gradients, and at least one elevated hero surface.\n"
            "- Numeric styling must be visually obvious: high-value figures should read with heavier mono weight, tabular numerals, and tight tracking instead of disappearing into the same body texture.\n"
            "- The hero chart should feel premium, not default: richer axis styling, thicker strokes or stronger candlestick bodies, and a clearly differentiated panel treatment from the surrounding cards.\n"
            "- The hero chart should dominate the center, while the desktop right rail should hold at least two stacked support modules such as watchlist plus news/activity or watchlist plus order flow.\n"
            "- Range pills, trade buttons, nav destinations, and table rows need crisp hover and active states that read immediately.\n"
            "- Replace any remote avatar placeholders with styled initials, local assets, or inline SVG treatments.\n"
        )
    if ui_archetype in {"editor", "kanban", "chat"}:
        return (
            "APP-SHELL POLISH TARGET FOR WORKSPACES:\n"
            "- Keep one stronger display treatment for brand and panel titles, a readable UI sans for controls, and a clear mono or tabular style wherever dense data appears.\n"
            "- Multi-panel desktop layouts need differentiated surface depth so the work area, sidebars, and floating controls do not collapse into one flat sheet.\n"
        )
    return ""


CONTENT_REFINEMENT_ISSUES = {
    "dense_shell_interactivity",
    "kpi_sparse",
    "chart_missing",
    "chart_underdeveloped",
    "table_sparse",
    "side_panel_thin",
    "panel_stacking",
    "interactive_controls",
    "text_density",
    "placeholder_text",
    "numeric_authenticity",
    "content_uniqueness",
    "contextual_labeling",
    "data_specificity",
    "semantic_variety",
    "temporal_realism",
    "metric_completeness",
    "content_authenticity",
}

SHELL_REFINEMENT_ISSUES = {
    "first_paint_visibility",
    "external_placeholder_assets",
    "spacing_rhythm",
    "typography_hierarchy",
    "weak_surface_depth",
    "polish_flow",
    "numeric_data_typography",
}

CONTENT_FIX_ISSUES = {
    "placeholder_text",
    "numeric_authenticity",
    "content_uniqueness",
    "contextual_labeling",
    "data_specificity",
    "semantic_variety",
    "temporal_realism",
    "metric_completeness",
    "content_authenticity",
}


def build_componentized_content_fix_prompt(
    *,
    task_description_with_assets: str,
    ui_archetype: str | None = None,
    semantic_evaluation: dict[str, Any] | None = None,
    multi_file_evaluation: dict[str, Any] | None = None,
) -> str:
    semantic_section = format_semantic_evaluation_context(semantic_evaluation)
    multi_file_section = format_multi_file_evaluation_context(multi_file_evaluation)
    audit_sections = "\n\n".join(section for section in (semantic_section, multi_file_section) if section)
    audit_block = f"\n\n{audit_sections}\n" if audit_sections else ""
    archetype_shell_section = build_componentized_shell_polish_guidance(ui_archetype)
    shell_block = f"\n\n{archetype_shell_section}\n" if archetype_shell_section else ""
    return (
        task_description_with_assets
        + "\n\nTARGETED CONTENT FIX PASS:\n"
          "The workspace already builds. Do not redesign the shell.\n"
          "Preserve layout, palette, spacing, imports, exports, component signatures, hooks, and file boundaries.\n"
          "Patch only the weak content-bearing files already identified by local evaluation.\n"
          "Prioritize data-bearing page or data files that seed content. If a component only renders props, keep its structure and only add missing contextual labels or subtitles when needed.\n"
          "Do not rewrite shared CSS unless a direct label, badge, or numeric treatment fix absolutely requires a tiny supporting style edit.\n"
          "Return only the files that changed.\n"
        + audit_block
        + shell_block
        + "TARGETED CONTENT REMEDIATION:\n"
          "- Replace generic labels, duplicate rows, and repeated copy with domain-specific seeded content.\n"
          "- Replace round placeholder numbers with plausible non-round values, mixed deltas, and varied entities.\n"
          "- Add missing context labels such as date ranges, update moments, comparison copy, and table subtitles.\n"
          "- Add realistic timestamps, recency cues, or dated entries where the audit calls for temporal realism.\n"
          "- Strengthen the KPI layer with specific labels and supporting context, but keep the current shell composition intact.\n\n"
          "Hard rules while fixing content:\n"
          "- Do not flatten the app back into a single file.\n"
          "- Do not rewrite unrelated style files or shell layout files unless they are explicitly in scope.\n"
          "- If a weak component receives seeded data from App/page/data files, fix the upstream seeded data first.\n"
          "- Keep the app buildable with `npm run build`.\n"
    )


def build_componentized_refinement_prompt(
    *,
    task_description_with_assets: str,
    issues: list[str],
    ui_archetype: str | None = None,
    self_review: Any = None,
    density_audit: dict[str, Any] | None = None,
    semantic_evaluation: dict[str, Any] | None = None,
    multi_file_evaluation: dict[str, Any] | None = None,
) -> str:
    issue_guidance = {
        "first_paint_visibility": (
            "- First-paint visibility: above-the-fold content must be visible immediately. "
            "Do not keep the primary shell, topbar, hero, KPI row, or initial cards at opacity 0 while waiting for JS or scroll observers."
        ),
        "external_placeholder_assets": (
            "- External placeholder assets: remove avatar/image placeholder services and replace them with styled initials, gradients, local generated assets, or inline SVG treatments."
        ),
        "dense_shell_interactivity": (
            "- Dense-shell interactivity: dashboards and finance shells need working range selectors, filters, sortable data, tab switches, watchlist state, or equivalent real controls."
        ),
        "kpi_sparse": (
            "- KPI density: build out a real four-card KPI row with seeded labels, values, deltas, and supporting sparkline or trend cues."
        ),
        "chart_missing": (
            "- Primary chart region: add or restore a real chart panel with visible axes, seeded values, and a clear chart container."
        ),
        "chart_underdeveloped": (
            "- Chart detail: keep the existing shell, but make the chart region richer with clearer axes, more data points, and supporting labels or tooltips."
        ),
        "table_sparse": (
            "- Table density: expand holdings, transaction, or comparison tables so they feel publishable rather than skeletal."
        ),
        "table_trend_missing": (
            "- Table trend cues: fintech tables should include clear per-row trend context such as sparklines, mini trendlines, or equivalent visual movement indicators in addition to the numeric columns."
        ),
        "side_panel_thin": (
            "- Supporting panel density: strict dashboard and finance shells should carry at least two distinct support modules, such as watchlist plus activity, alerts plus news, or allocation plus movers, each with real entries."
        ),
        "panel_stacking": (
            "- Panel stacking: add enough distinct data regions so the center does not feel like a polished shell with empty space."
        ),
        "interactive_controls": (
            "- Interactive controls: add working filters, tabs, range selectors, or sorting controls that visibly change the UI."
        ),
        "text_density": (
            "- Content density: increase headings, captions, labels, secondary annotations, and seeded supporting copy inside the app shell."
        ),
        "numeric_data_typography": (
            "- Numeric data typography: finance and dashboard shells must use a monospace or tabular numeric treatment for KPI values, prices, deltas, table numbers, and chart labels."
        ),
        "placeholder_text": (
            "- Placeholder cleanup: replace every generic label, user stub, metric placeholder, or synthetic title with domain-specific seeded content."
        ),
        "numeric_authenticity": (
            "- Numeric authenticity: replace round placeholder numbers with plausible non-round values, mixed positive and negative deltas, and richer seeded metrics. For finance shells, avoid repeated trailing .00 values across every KPI and holding unless the domain truly requires it."
        ),
        "content_uniqueness": (
            "- Content uniqueness: make repeated rows, cards, or entries distinct. Avoid duplicated names, values, and timestamps."
        ),
        "contextual_labeling": (
            "- Contextual labeling: add clear chart subtitles, update labels, comparison copy, and table context such as ranges or update moments. KPI bands should include labels like vs. yesterday, net of fees, refreshed 5 min ago, or similar real context."
        ),
        "data_specificity": (
            "- Data specificity: use real-looking entities, names, tickers, IDs, sectors, transaction types, and company labels appropriate to the product."
        ),
        "semantic_variety": (
            "- Semantic variety: introduce more status diversity, category variation, sector spread, or mixed outcomes in the data."
        ),
        "temporal_realism": (
            "- Temporal realism: add believable dates, timestamps, and recency language with varied values instead of repeated placeholders."
        ),
        "metric_completeness": (
            "- Metric completeness: ensure the KPI layer has specific labels, values, deltas, and context that match the app archetype."
        ),
        "spacing_rhythm": (
            "- Spacing rhythm: strengthen section spacing, internal card padding, max-width discipline, and grid balance. "
            "Avoid cramped clusters and repeated centered blocks with identical spacing."
        ),
        "typography_hierarchy": (
            "- Typography hierarchy: introduce a more intentional type system with distinct heading treatment, stronger label styling, and clearer contrast between display, body, and numeric text. Promote the desktop page title or hero heading into a true display scale instead of a small utility heading. For dashboard and fintech shells, panel titles should feel editorial rather than default H3s, and numeric surfaces should use visibly intentional mono/tabular styling with stronger weight."
        ),
        "weak_surface_depth": (
            "- Surface depth: strengthen layering with deliberate page/surface/elevated states, subtle gradients or tints, and more convincing shadows, borders, or soft glows. Cards should not read like flat dark rectangles; add at least one clearly elevated hero surface and richer panel treatments. Give the primary chart panel and support-rail modules their own tone shift or shadow treatment so they do not collapse into one flat sheet."
        ),
        "content_authenticity": (
            "- Content authenticity: replace generic labels or filler with domain-specific names, metrics, microcopy, and section language that fit the product type."
        ),
        "polish_flow": (
            "- Polish and flow: add high-signal finish details such as section rhythm, overlap transitions, sticky sub-bars, badge treatments, selection styling, scrollbar styling, decorative dividers, quote treatments, or richer hover states where appropriate."
        ),
    }
    lines = [issue_guidance[issue] for issue in issues if issue in issue_guidance]
    guidance_block = "\n".join(lines)
    self_review_block = build_componentized_self_review_context(self_review)
    self_review_section = f"\n\n{self_review_block}\n" if self_review_block else ""
    density_section = format_density_audit_context(density_audit)
    semantic_section = format_semantic_evaluation_context(semantic_evaluation)
    multi_file_section = format_multi_file_evaluation_context(multi_file_evaluation)
    archetype_shell_section = build_componentized_shell_polish_guidance(ui_archetype)
    audit_sections = "\n\n".join(section for section in (density_section, semantic_section, multi_file_section) if section)
    audit_block = f"\n\n{audit_sections}\n" if audit_sections else ""
    shell_block = f"\n\n{archetype_shell_section}\n" if archetype_shell_section else ""
    return (
        task_description_with_assets
        + "\n\nQUALITY REFINEMENT PASS:\n"
          "The current componentized workspace builds, but it still has weak quality signals.\n"
          "Preserve the app identity, structure, and seeded content unless a change is required to improve quality.\n"
          "Focus only on the weak areas below and keep the app buildable with `npm run build`.\n"
          "If weak files are listed in the local multi-file evaluation, patch those files first and avoid rewriting strong files.\n\n"
        + self_review_section
        + audit_block
        + shell_block
        + "TARGETED FIXES:\n"
        + guidance_block
        + "\n\nHard rules while refining:\n"
          "- Keep component files valid React modules only.\n"
          "- Do not paste CSS after TypeScript or JSX code.\n"
          "- Keep the first viewport visibly populated on initial load.\n"
          "- Do not introduce external placeholder image/avatar services.\n"
          "- If `src/base.css` exists and the weak areas are typography, depth, or polish related, refine `src/base.css` and the relevant shell CSS first before rewriting unrelated components.\n"
          "- Preserve imports, exports, component signatures, layout structure, and existing file boundaries unless a weak-file fix requires a direct supporting edit.\n"
          "- Improve polish and interactions without flattening the existing shell.\n"
    )


def _normalize_componentized_rel_path(rel_path: str) -> str:
    return rel_path.replace("\\", "/").strip("/")


def _select_componentized_related_files(
    code_dir: Path,
    rel_paths: list[str],
    *,
    dependency_depth: int = 1,
    dependent_depth: int = 1,
) -> set[str]:
    selected = {
        _normalize_componentized_rel_path(rel_path)
        for rel_path in rel_paths
        if _normalize_componentized_rel_path(rel_path)
    }
    if not selected:
        return set()

    dependencies = collect_componentized_direct_dependencies(
        code_dir,
        sorted(selected),
        max_depth=dependency_depth,
    )
    selected.update(dependencies)

    dependents = collect_componentized_reverse_dependents(
        code_dir,
        sorted(selected),
        max_depth=dependent_depth,
    )
    selected.update(dependents)

    # Pull one layer of upstream data/support from parent files so content fixes can
    # patch the source of weak props without reopening the whole workspace.
    parent_dependencies = collect_componentized_direct_dependencies(
        code_dir,
        sorted(dependents),
        max_depth=1,
    )
    for rel_path in parent_dependencies:
        normalized = _normalize_componentized_rel_path(rel_path)
        if (
            normalized.startswith("src/data/")
            or normalized.endswith(".json")
            or any(token in normalized for token in ("metrics", "transactions", "watchlist", "seed", "mock", "series", "dataset"))
        ):
            selected.add(normalized)
    return selected


def select_componentized_content_fix_scope(
    code_dir: Path,
    *,
    weak_file_paths: list[str],
) -> list[str]:
    editable_files = collect_componentized_editable_files(code_dir)
    if not editable_files:
        return []

    selected = _select_componentized_related_files(
        code_dir,
        weak_file_paths,
        dependency_depth=1,
        dependent_depth=2,
    )

    scoped = [path for path in editable_files if path in selected]
    if not scoped:
        scoped = [
            path for path in editable_files
            if path.startswith(("src/pages/", "src/data/", "src/components/")) or path == "src/App.tsx"
        ]
    return extend_componentized_scope(
        code_dir,
        scoped[:12],
        include_style_targets=False,
        include_common_targets=False,
    )


def select_componentized_refinement_scope(
    code_dir: Path,
    issues: list[str],
    *,
    weak_file_paths: list[str] | None = None,
) -> list[str]:
    editable_files = collect_componentized_editable_files(code_dir)
    if not editable_files:
        return []

    shell_sensitive = any(issue in SHELL_REFINEMENT_ISSUES for issue in issues)
    content_focused = bool(weak_file_paths) and not shell_sensitive

    preferred_files = ["index.html", "src/main.tsx", "src/App.tsx"]
    if shell_sensitive:
        preferred_files.extend(
            [
                "src/base.css",
                "src/index.css",
                "src/styles.css",
                "src/styles/style.css",
            ]
        )
    selected: set[str] = set()
    for rel_path in preferred_files:
        if not _componentized_scope_path_exists(code_dir, rel_path):
            continue
        if _is_low_signal_componentized_style_target(code_dir, rel_path):
            continue
        selected.add(rel_path)
    for rel_path in weak_file_paths or []:
        normalized = rel_path.replace("\\", "/").strip("/")
        if normalized:
            selected.add(normalized)

    issue_patterns = {
        "first_paint_visibility": ("intersectionobserver", "hidden-section", "opacity: 0", "visibility: hidden", "fade-in"),
        "external_placeholder_assets": tuple(domain.lower() for domain in QUALITY_PLACEHOLDER_DOMAINS),
        "dense_shell_interactivity": ("onclick", "onchange", "onsubmit", "usestate", "setinterval", "settimeout"),
        "spacing_rhythm": ("padding", "gap", "max-width", "grid-template", "section", "content-area"),
        "typography_hierarchy": ("font-family", "font-size", "letter-spacing", "line-height", "@import", "label", "eyebrow", "space grotesk", "jetbrains mono", "outfit"),
        "weak_surface_depth": ("box-shadow", "linear-gradient", "radial-gradient", "background:", ":root", "backdrop-filter"),
        "content_authenticity": ("title", "subtitle", "description", "headline", "label", "copy", "caption"),
        "polish_flow": ("::selection", "scrollbar", "badge", "divider", "separator", "quote", "border-radius", "box-shadow", "focus-visible", ":hover"),
        "kpi_sparse": ("portfolio value", "revenue", "kpi", "metric", "delta", "sparkline"),
        "chart_missing": ("chart", "recharts", "sparkline", "polyline", "candlestick"),
        "chart_underdeveloped": ("chart", "tooltip", "range", "axis", "grid"),
        "table_sparse": ("table", "holdings", "transactions", "rows", "columns"),
        "table_trend_missing": ("table", "holdings", "sparkline", "trend", "mini-chart", "history"),
        "side_panel_thin": ("watchlist", "activity", "alerts", "notification", "news", "allocation", "movers", "briefing"),
        "panel_stacking": ("section", "panel", "card", "widget"),
        "interactive_controls": ("onclick", "onchange", "filter", "sort", "selectedrange", "tab"),
        "text_density": ("subtitle", "caption", "label", "description", "summary"),
        "placeholder_text": ("metric 1", "user 1", "sample", "placeholder", "chart title"),
        "numeric_authenticity": ("$10,000", "$100,000", "50%", "100%", "round"),
        "content_uniqueness": ("initial", "map(", "transactions", "watchlist", "holdings"),
        "contextual_labeling": ("updated", "showing", "vs.", "last month", "last week"),
        "data_specificity": ("aapl", "msft", "nvda", "transaction", "sector", "status"),
        "semantic_variety": ("active", "pending", "completed", "buy", "sell", "hold"),
        "temporal_realism": ("ago", "mar", "apr", "2026", "timestamp"),
        "metric_completeness": ("portfolio value", "day p&l", "ytd return", "revenue", "arr"),
    }

    for rel_path in editable_files:
        content = _read_componentized_scope_file(code_dir, rel_path)
        if content is None:
            continue
        if _is_low_signal_componentized_style_target(code_dir, rel_path, content=content):
            continue
        classification = classify_componentized_content_file(rel_path, content)
        if classification["role"] == "config":
            continue
        if not classification.get("is_content_bearing") and classification["role"] not in {"style", "layout"}:
            continue

        normalized_content = content.lower()

        for issue in issues:
            patterns = issue_patterns.get(issue, ())
            if any(pattern in normalized_content for pattern in patterns):
                selected.add(rel_path)
                break

    if content_focused:
        for rel_path in editable_files:
            if rel_path == "src/App.tsx" or rel_path.startswith("src/pages/"):
                selected.add(rel_path)
    elif weak_file_paths or "dense_shell_interactivity" in issues or any(
        issue in issues for issue in ("content_authenticity", "spacing_rhythm", "typography_hierarchy", "polish_flow", "text_density")
    ):
        for rel_path in editable_files:
            if rel_path.startswith(("src/components/", "src/pages/", "src/data/")):
                selected.add(rel_path)
            if len(selected) >= 10:
                break

    scoped = [path for path in editable_files if path in selected]
    if not scoped:
        scoped = editable_files[:8]
    if content_focused:
        return extend_componentized_scope(
            code_dir,
            scoped[:12],
            include_style_targets=False,
            include_common_targets=False,
        )
    return extend_componentized_scope(code_dir, scoped[:12])


def select_componentized_build_repair_scope(
    code_dir: Path,
    build_errors: list[dict[str, Any]],
) -> list[str]:
    editable_files = collect_componentized_editable_files(code_dir)
    if not editable_files:
        return []

    support_targets = {
        "package.json",
        "vite.config.ts",
        "tsconfig.json",
        "tsconfig.node.json",
        "src/vite-env.d.ts",
    }
    selected: set[str] = set()
    include_style_targets = False
    include_common_targets = False
    include_direct_support = False

    for error in build_errors:
        rel_path = _normalize_componentized_rel_path(str(error.get("path") or ""))
        if not rel_path:
            continue
        selected.add(rel_path)
        error_class = str(error.get("error_class") or "")
        if rel_path in support_targets:
            include_common_targets = True
            include_direct_support = True
            selected.update(path for path in support_targets if path in editable_files)
        if error_class in {"syntax", "import", "asset"}:
            selected.update(
                _select_componentized_related_files(
                    code_dir,
                    [rel_path],
                    dependency_depth=1,
                    dependent_depth=1,
                )
            )
        elif error_class in {"cross_file", "type"}:
            selected.update(
                _select_componentized_related_files(
                    code_dir,
                    [rel_path],
                    dependency_depth=2,
                    dependent_depth=2,
                )
            )
        else:
            selected.update(
                _select_componentized_related_files(
                    code_dir,
                    [rel_path],
                    dependency_depth=1,
                    dependent_depth=2,
                )
            )

        if rel_path in {"index.html", "src/main.tsx", "src/App.tsx"}:
            include_common_targets = True
        if rel_path.endswith(".css") or error_class == "asset":
            include_style_targets = True

    scoped = [path for path in editable_files if path in selected]
    if not scoped:
        scoped = [path for path in editable_files if path in {"index.html", "src/main.tsx", "src/App.tsx"}]

    return extend_componentized_scope(
        code_dir,
        scoped[:12],
        include_style_targets=include_style_targets,
        include_direct_support=include_style_targets or include_direct_support,
        include_common_targets=include_common_targets,
    )


def extend_componentized_scope(
    code_dir: Path,
    rel_paths: list[str],
    *,
    include_style_targets: bool = True,
    include_direct_support: bool = False,
    include_common_targets: bool = True,
) -> list[str]:
    scoped = {path.replace("\\", "/").strip("/") for path in rel_paths if path}
    if include_common_targets:
        common_targets = ["index.html", "src/main.tsx", "src/App.tsx"]
        for rel_path in common_targets:
            if _componentized_scope_path_exists(code_dir, rel_path):
                scoped.add(rel_path)

    if include_style_targets:
        common_style_targets = [
            "src/base.css",
            "src/index.css",
            "src/style.css",
            "src/styles.css",
        ]
        for rel_path in common_style_targets:
            if not _componentized_scope_path_exists(code_dir, rel_path):
                continue
            if _is_low_signal_componentized_style_target(code_dir, rel_path):
                continue
            scoped.add(rel_path)

        styles_dir = code_dir / "src" / "styles"
        if styles_dir.exists():
            for path in styles_dir.rglob("*"):
                if path.is_file():
                    rel_path = path.relative_to(code_dir).as_posix()
                    if _is_low_signal_componentized_style_target(code_dir, rel_path):
                        continue
                    scoped.add(rel_path)

    if include_direct_support:
        for rel_path in collect_componentized_direct_dependencies(
            code_dir,
            sorted(scoped),
            max_depth=2,
        ):
            scoped.add(rel_path)

    return sorted(scoped)


AUTO_MANAGED_COMPONENTIZED_STYLE_PATHS = {
    "src/polish-guard.css",
}

LOW_SIGNAL_COMPONENTIZED_STYLE_MARKERS = (
    "keep this file intentionally minimal",
    "intentionally left blank. custom overrides are in style.css",
    "generated fallback stylesheet to satisfy a referenced local css import",
)


def _componentized_scope_path_exists(code_dir: Path, rel_path: str) -> bool:
    path = code_dir / rel_path.replace("\\", "/").strip("/")
    return path.exists() and path.is_file()


def _read_componentized_scope_file(code_dir: Path, rel_path: str) -> str | None:
    path = code_dir / rel_path.replace("\\", "/").strip("/")
    if not path.exists() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _is_low_signal_componentized_style_target(
    code_dir: Path,
    rel_path: str,
    *,
    content: str | None = None,
) -> bool:
    normalized = rel_path.replace("\\", "/").strip("/")
    if normalized in AUTO_MANAGED_COMPONENTIZED_STYLE_PATHS:
        return True
    if not normalized.endswith(".css"):
        return False
    if content is None:
        content = _read_componentized_scope_file(code_dir, normalized)
    if content is None:
        return True
    compact = " ".join(content.split()).lower()
    return (
        normalized in {"src/index.css", "src/style.css", "src/styles.css"}
        and any(marker in compact for marker in LOW_SIGNAL_COMPONENTIZED_STYLE_MARKERS)
    )


def build_componentized_build_repair_prompt(
    *,
    task_description_with_assets: str,
    build_errors: list[dict[str, Any]],
) -> str:
    grouped = group_componentized_build_errors_by_file(build_errors)
    error_blocks: list[str] = []
    for rel_path, file_errors in grouped.items():
        bullet_lines = []
        for item in file_errors:
            location = f" line {item.get('line')}" if item.get("line") else ""
            bullet_lines.append(
                f"- [{item.get('error_class')}] {item.get('message')}{location}"
            )
        error_blocks.append(f"{rel_path}\n" + "\n".join(bullet_lines))

    return (
        task_description_with_assets
        + "\n\nBUILD REPAIR PASS:\n"
          "The current componentized workspace must build cleanly with `npm run build`.\n"
          "Use the actual build failures below. Repair only the broken files and any directly affected support files.\n"
          "Do not redesign, refactor, or expand the product.\n\n"
          "Hard rules while repairing:\n"
          "- Classify each fix by the reported error class before you change code.\n"
          "- Keep imports, exports, component signatures, hooks, layout structure, and styling direction intact unless a direct fix requires a local adjustment.\n"
          "- Do not use explicit local import extensions like `./App.tsx` or `./data.ts`.\n"
          "- If base.css is used, import it only from `src/main.tsx` as `import \"./base.css\";`.\n"
          "- Make the minimum coherent fix needed.\n"
          "- If a file depends on another broken local file, return both together.\n"
          "- Re-check each returned file for valid imports, balanced braces, valid JSX, closed comments, and buildable exports before returning JSON.\n\n"
          "BUILD ERRORS BY FILE:\n"
        + "\n\n".join(error_blocks)
    )


def build_componentized_contract_recovery_prompt(
    *,
    task_description_with_assets: str,
    missing_paths: list[str],
    contract_validation: dict[str, Any] | None = None,
) -> str:
    required_lines = "\n".join(f"- {path}" for path in missing_paths)
    violation_block = format_componentized_contract_violations(contract_validation)
    violations_section = (
        "\n\nDetected contract violations:\n" + violation_block
        if violation_block
        else ""
    )
    return (
        task_description_with_assets
        + "\n\nCOMPONENTIZED CONTRACT RECOVERY PASS:\n"
          "The prior response did not satisfy the minimum React + TypeScript app contract.\n"
          "Return a valid multi-file Vite workspace now.\n"
          "Do not return zero files. Do not omit the required entry files.\n"
          "Do not return placeholder scaffolds or analysis.\n"
          "Use real seeded app content that matches the task.\n\n"
          "Required files for this recovery pass:\n"
        + required_lines
        + violations_section
        + "\n\nHard rules while recovering the contract:\n"
          "- Output only real file contents for the requested files.\n"
          "- Keep imports valid and extensionless for local source files.\n"
          "- Ensure src/main.tsx mounts src/App.tsx and imports ./base.css only from src/main.tsx when base.css exists.\n"
          "- Ensure the workspace can proceed to `npm run build` after support-file normalization.\n"
          "- Prefer a dense, app-like shell over a brochure page.\n"
    )


def build_componentized_scaffold_seed_context() -> str:
    scaffold = build_vite_react_ts_scaffold(app_dir="seed-componentized-app")
    lines: list[str] = []
    for path, content in sorted(scaffold.files.items()):
        rel_path = path.replace("\\", "/").split("/", 1)[-1]
        if rel_path.startswith(("README", ".gitignore")):
            continue
        lines.append(f"--- FILE: {rel_path} ---\n{content}")
    return "\n\n".join(lines)


def rewrite_seed_version(version_dir: Path, original_project_id: int, new_project_id: int):
    original_windows_prefix = str(Path("generated") / str(original_project_id) / "v1").replace("/", "\\") + "\\"
    new_windows_prefix = str(Path("generated") / str(new_project_id) / "v1").replace("/", "\\") + "\\"
    original_windows_text_prefix = original_windows_prefix.replace("\\", "\\\\")
    new_windows_text_prefix = new_windows_prefix.replace("\\", "\\\\")
    original_posix_prefix = f"generated/{original_project_id}/v1/"
    new_posix_prefix = f"generated/{new_project_id}/v1/"
    replacements = {
        f"/api/assets/{original_project_id}/1/": f"/api/assets/{new_project_id}/1/",
        original_windows_prefix: new_windows_prefix,
        original_windows_text_prefix: new_windows_text_prefix,
        original_posix_prefix: new_posix_prefix,
    }
    text_suffixes = {".css", ".html", ".js", ".json", ".jsx", ".md", ".py", ".ts", ".tsx", ".txt"}

    for path in version_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        try:
            content = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        updated = content
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != content:
            path.write_text(updated, encoding="utf-8")


def update_seed_factsheet(version_dir: Path, project: Project, execution: Execution) -> Dict[str, Any] | None:
    factsheet_path = version_dir / "last_factsheet.json"
    factsheet = read_json_file(factsheet_path)
    if not factsheet:
        return None

    project_info = factsheet.setdefault("project", {})
    project_info["id"] = project.id
    project_info["name"] = project.name
    project_info["version"] = execution.version
    project_info["execution_id"] = execution.id

    pipeline = factsheet.setdefault("pipeline", {})
    pipeline["status"] = execution.status
    pipeline.setdefault("ui_archetype", project.locked_ui_archetype)
    pipeline.setdefault("duration_seconds", execution.duration_seconds)

    usage = factsheet.setdefault("usage", {})
    usage.setdefault("tokens_used", execution.tokens_used)
    usage.setdefault("credits_used", execution.credits_used)

    write_json_file(factsheet_path, factsheet)
    return factsheet


def build_file_tree(root: Path, base: Path):
    nodes = []
    try:
        items = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        for item in items:
            if item.name.startswith("."):
                continue
            rel = item.relative_to(base)
            if item.is_dir():
                children = build_file_tree(item, base)
                nodes.append({
                    "name": item.name,
                    "type": "folder",
                    "path": str(rel).replace("\\", "/"),
                    "children": children,
                })
            else:
                nodes.append({
                    "name": item.name,
                    "type": "file",
                    "path": str(rel).replace("\\", "/"),
                })
    except Exception:
        pass
    return nodes


def get_language_from_ext(filename: str) -> str:
    ext_map = {
        ".ts": "typescript", ".tsx": "typescript",
        ".js": "javascript", ".jsx": "javascript",
        ".py": "python", ".html": "html",
        ".css": "css", ".json": "json",
        ".md": "markdown", ".sh": "shell",
        ".yaml": "yaml", ".yml": "yaml",
        ".txt": "text",
    }
    ext = Path(filename).suffix.lower()
    return ext_map.get(ext, "text")


ARCHETYPES = [
    "dashboard", "landing", "ecommerce", "kanban", "chat",
    "editor", "feed", "form", "game", "portfolio",
]


_ARCHETYPE_CHANGE_RE = re.compile(
    r"\b(?:turn\s+(?:it\s+)?into|convert\s+(?:it\s+)?(?:to|into)"
    r"|make\s+(?:it\s+)?(?:a|an|into)\s"
    r"|redesign\s+(?:it\s+)?as"
    r"|switch\s+(?:it\s+)?to"
    r"|rebuild\s+(?:it\s+)?as"
    r"|change\s+(?:it\s+)?(?:to|into))\b",
    re.IGNORECASE,
)


def detect_requested_archetype(message: str) -> str | None:
    if not message:
        return None
    text = message.lower()
    match = _ARCHETYPE_CHANGE_RE.search(text)
    if not match:
        return None
    after = text[match.end():]
    for archetype in ARCHETYPES:
        if re.search(rf"\b{re.escape(archetype)}\b", after):
            return archetype
    return None


def get_plan_ui_archetype(plan) -> str | None:
    for ms in plan.milestones:
        for t in ms.tasks:
            if getattr(t, "execution_hint", None) == "engineer" and getattr(t, "task_type", None) == "scaffold":
                return t.ui_archetype
    return None


def get_plan_scaffold_task(plan):
    for milestone in getattr(plan, "milestones", []):
        for task in getattr(milestone, "tasks", []):
            if getattr(task, "execution_hint", None) != "engineer":
                continue
            if getattr(task, "task_type", None) != "scaffold":
                continue
            return task
    return None


def get_plan_scaffold_seed_rows(plan) -> int | None:
    task = get_plan_scaffold_task(plan)
    if not task:
        return None

    archetype_rules = getattr(task, "archetype_rules", None)
    if isinstance(archetype_rules, dict):
        content_contract = archetype_rules.get("content_contract", {}) or {}
        seed_rows = content_contract.get("seed_rows")
    else:
        content_contract = getattr(archetype_rules, "content_contract", None)
        seed_rows = getattr(content_contract, "seed_rows", None) if content_contract else None

    if seed_rows is None:
        return None

    try:
        return int(seed_rows)
    except (TypeError, ValueError):
        return None


def get_plan_scaffold_image_item_count(plan) -> int:
    task = get_plan_scaffold_task(plan)
    if not task:
        return 0

    quality_target = getattr(task, "quality_target", None)
    if isinstance(quality_target, dict):
        must_have_content = quality_target.get("must_have_content", []) or []
    else:
        must_have_content = getattr(quality_target, "must_have_content", []) or []

    image_keywords = [
        "pet",
        "card",
        "photo",
        "product",
        "image",
        "character",
        "profile",
        "item",
        "dish",
        "property",
        "course",
        "job",
        "restaurant",
    ]

    image_item_count = 0
    for item in must_have_content:
        if not isinstance(item, str):
            continue
        text = item.lower()
        if any(keyword in text for keyword in image_keywords):
            image_item_count += 1

    return image_item_count


def get_optional_request_user_id() -> int | None:
    verify_jwt_in_request(optional=True)
    identity = get_jwt_identity()
    return int(identity) if identity is not None else None


def get_project_access_error(project: Project, user_id: int | None):
    if project.owner_id is None:
        return None
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401
    if project.owner_id != user_id:
        return jsonify({"error": "Forbidden"}), 403
    return None


def resolve_project_version(q_project_id=None, q_version=None):
    """
    Resolves (project_id, version) from:
      1. Explicit query params (highest priority Ã¢â‚¬â€ user asked for a specific version)
      2. execution_state in-memory (current running/last run)
      3. DB lookup of active head if only project_id is known
    """
    project_id = None
    version = None

    # Priority 1: explicit query params always win
    if q_project_id:
        try:
            project_id = int(q_project_id)
        except (ValueError, TypeError):
            pass

    if q_version:
        try:
            version = int(q_version)
        except (ValueError, TypeError):
            pass

    # Priority 2: fall back to in-memory state only if params not provided
    if not project_id:
        # Find the most recently launched project from per-project state
        for pid, s in execution_state.items():
            if s.get("current_execution_id"):
                project_id = pid
                break

    if not version:
        execution_id = get_project_state(project_id).get("current_execution_id") if project_id else None
        if execution_id:
            session = get_session()
            try:
                execution = session.get(Execution, execution_id)
                if execution:
                    version = execution.version
            finally:
                session.close()

    # Priority 3: if we have project_id but still no version, look up active head in DB
    if project_id and not version:
        session = get_session()
        try:
            head = (
                session.query(Execution)
                .filter(
                    Execution.project_id == project_id,
                    Execution.is_active_head == True,
                )
                .first()
            )
            if head:
                version = head.version
        finally:
            session.close()

    return project_id, version


def run_full_pipeline_async(
    task_description: str,
    prompt_history: list = None,
    project_id: int = None,
    reference_images: list = None,
    nlu_context: dict | None = None,
):
    state = get_project_state(project_id)

    sys.path.insert(0, str(REPO_ROOT))

    session = get_session()
    execution_id = state.get("current_execution_id")
    locked_ui_archetype = None
    pipeline_start_time = time.time()

    try:
        if execution_id:
            execution = session.get(Execution, execution_id)
            if execution:
                execution.status = "running"
                session.commit()

        version = None
        if execution_id:
            execution = session.get(Execution, execution_id)
            if execution:
                version = execution.version
                if execution.project_id:
                    project = session.get(Project, execution.project_id)
                    if project:
                        locked_ui_archetype = project.locked_ui_archetype
        if not locked_ui_archetype:
            benchmark_match = suggest_reference_archetype(task_description)
            if benchmark_match and benchmark_match.get("archetype"):
                locked_ui_archetype = benchmark_match["archetype"]
                print(
                    f"[Benchmark] Prompt matched registry entry '{benchmark_match.get('label')}', "
                    f"locking archetype to '{locked_ui_archetype}'"
                )
        is_iteration = bool(version and version > 1)

        if project_id and version:
            version_dir = get_version_dir(project_id, version)
        else:
            version_dir = PUBLIC_DIR / "shared"
        version_dir.mkdir(parents=True, exist_ok=True)

        # Load existing code from nearest ancestor that has code on disk
        existing_code = None
        ancestor_version_dir = None
        iteration_visual_dna: dict[str, Any] | None = None
        iteration_feature_inventory: dict[str, Any] | None = None
        session_check = get_session()
        try:
            current_exec = session_check.get(Execution, execution_id)
            ancestor_id = current_exec.parent_execution_id if current_exec else None
            hops = 0
            while ancestor_id and hops < 5:
                ancestor_exec = session_check.get(Execution, ancestor_id)
                if not ancestor_exec:
                    break
                ancestor_dir = get_version_dir(project_id, ancestor_exec.version) / "code"
                existing_code = collect_existing_code_context(ancestor_dir)
                if existing_code:
                    ancestor_version_dir = get_version_dir(project_id, ancestor_exec.version)
                    iteration_visual_dna = load_or_extract_iteration_artifact(
                        ancestor_version_dir,
                        filename="last_visual_dna.json",
                        extractor=extract_visual_dna,
                    )
                    iteration_feature_inventory = load_or_extract_iteration_artifact(
                        ancestor_version_dir,
                        filename="last_feature_inventory.json",
                        extractor=extract_feature_inventory,
                    )
                    add_log(f"Build Agent: Loading v{ancestor_exec.version} for context...", project_id=project_id)
                    break
                ancestor_id = ancestor_exec.parent_execution_id
                hops += 1
        finally:
            session_check.close()

        add_log("Starting pipeline...", project_id=project_id)
        add_log("Requirements Agent: Analyzing your request...", project_id=project_id)
        sys.path.insert(0, str(REPO_ROOT))
        from agents.pm_agent import PMAgent
        pm_agent = PMAgent()

        nlu_context = nlu_context or {
            "keywords": [],
            "concepts": [],
            "entities": [],
            "categories": [],
            "domain": "general",
            "prompt_richness": "sparse",
        }
        entities_context = ", ".join(
            f"{e.get('text', '')} ({e.get('type', 'Unknown')})"
            for e in nlu_context.get("entities", [])
            if e.get("text")
        )
        nlu_context_str = (
            "NLU Analysis: "
            f"keywords=[{', '.join(nlu_context.get('keywords', []))}], "
            f"concepts=[{', '.join(nlu_context.get('concepts', []))}], "
            f"entities=[{entities_context}], "
            f"prompt_richness={nlu_context.get('prompt_richness', 'sparse')}"
        )

        context_input = task_description
        if prompt_history and len(prompt_history) > 1:
            history_text = "\n".join(
                f"{turn['role'].upper()}: {turn['content']}"
                for turn in prompt_history
            )
            context_input = f"Full conversation history:\n{history_text}\n\nLatest request: {task_description}"
        context_input += f"\n\n{nlu_context_str}"
        if existing_code:
            # Extract app title from previous files to preserve it when possible.
            import re as _re
            title_match = _re.search(r"<title[^>]*>(.*?)</title>", existing_code, _re.IGNORECASE)
            prev_title = title_match.group(1).strip() if title_match else None
            title_note = f' The app is currently named "{prev_title}" - preserve this name unless the user explicitly asks to change it.' if prev_title else ""
            context_input += (
                "\n\nNOTE: This is an iteration on an existing app. "
                "The current codebase is provided to the engineer as multi-file context. "
                "The PRD should reflect ONLY the changes requested, not rebuild from scratch."
                f"{title_note}"
            )

        prd_artifact = pm_agent.generate_prd(context_input)

        prd_dict = prd_artifact.model_dump()
        prd_dict["_agent_sequence"] = ["pm"]
        write_json_file(version_dir / "last_prd.json", prd_dict)

        add_log("Requirements Agent: Brief created.", project_id=project_id)
        print(f"PRD saved: {prd_artifact.prd.document_title}")

        add_log("Architecture Agent: Planning the build...", project_id=project_id)

        from agents.planner_agent import PlannerAgent
        from utils.genai_client import get_genai_client

        genai_client = get_genai_client()
        planner = PlannerAgent(genai_client)
        plan = planner.run_from_prd_artifact(
            version_dir / "last_prd.json",
            locked_ui_archetype=locked_ui_archetype,
            is_iteration=is_iteration,
            reference_images=reference_images or [],
            project_context=context_input,
            nlu_context=nlu_context,
        )

        plan_dict = {
            "kind": "plan_artifact",
            "agent_role": "planner",
            "plan": plan.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "_agent_sequence": ["pm", "planner"],
        }
        flat_plan = plan.model_dump()
        write_json_file(version_dir / "last_plan.json", flat_plan)
        write_json_file(version_dir / "last_plan_artifact.json", plan_dict)
        effective_archetype = locked_ui_archetype or get_plan_ui_archetype(plan)
        design_benchmark_style_context = get_archetype_benchmark_guidance(
            effective_archetype or "",
            prompt_text=task_description,
            limit=3,
            global_limit=1,
        )

        add_log("Architecture Agent: Build plan ready.", project_id=project_id)
        milestone_count = len(plan.milestones)
        task_count = sum(len(m.tasks) for m in plan.milestones)
        print(f"Plan saved: {milestone_count} milestones, {task_count} tasks")

        seed_rows = get_plan_scaffold_seed_rows(plan)
        image_item_count = get_plan_scaffold_image_item_count(plan)
        effective_rows = max(seed_rows or 0, image_item_count)
        if effective_rows > 0:
            smart_max_images = max(effective_rows, 5)
            smart_max_images = min(smart_max_images + 1, 12)
        else:
            smart_max_images = 10
        print(
            f"Design Agent: targeting {smart_max_images} images "
            f"(seed_rows={seed_rows}, image_item_count={image_item_count})"
        )

        design_assets = []
        previous_visual_direction = ""
        if ancestor_version_dir:
            previous_visual_direction_path = ancestor_version_dir / "last_visual_direction.txt"
            if previous_visual_direction_path.exists():
                try:
                    previous_visual_direction = previous_visual_direction_path.read_text(encoding="utf-8")
                except OSError:
                    previous_visual_direction = ""

        try:
            from agents.design_agent import DesignAgent

            prd_data = read_json_file(version_dir / "last_prd.json") or {}
            design_agent = DesignAgent()
            visual_direction = design_agent.generate_visual_direction(
                prd_data,
                plan_dict=flat_plan,
                existing_visual_direction=previous_visual_direction if is_iteration else None,
                reference_images=reference_images or None,
                nlu_context=nlu_context,
                benchmark_style_context=design_benchmark_style_context or None,
            )
            if visual_direction:
                (version_dir / "last_visual_direction.txt").write_text(
                    visual_direction.strip() + "\n",
                    encoding="utf-8",
                )
                add_log("Design Agent: Visual direction ready.", project_id=project_id)
        except Exception as design_direction_err:
            print(f"DesignAgent visual direction failed (non-fatal): {design_direction_err}")
            add_log("Design Agent: Visual direction skipped, continuing...", project_id=project_id)

        if is_iteration and ancestor_version_dir:
            ancestor_assets_file = ancestor_version_dir / "last_design_assets.json"
            if ancestor_assets_file.exists():
                try:
                    ancestor_assets_data = read_json_file(ancestor_assets_file) or {}
                    design_assets = ancestor_assets_data.get("assets", [])
                    write_json_file(version_dir / "last_design_assets.json", {"assets": design_assets})
                    add_log(f"Design Agent: Reusing {len(design_assets)} images from previous version.", project_id=project_id)
                except Exception as e:
                    print(f"Failed to load ancestor design assets (non-fatal): {e}")
                    add_log("Design Agent: Could not load previous images, continuing...", project_id=project_id)
            else:
                add_log("Design Agent: No previous images found, skipping.", project_id=project_id)
        else:
            add_log("Design Agent: Generating visuals...", project_id=project_id)
            try:
                prd_data = read_json_file(version_dir / "last_prd.json") or {}
                design_agent = DesignAgent()
                assets_dir = version_dir / "assets"
                design_assets = design_agent.run(
                    prd_data,
                    max_images=smart_max_images,
                    save_dir=assets_dir,
                    reference_images=reference_images or None,
                    nlu_context=nlu_context,
                    benchmark_style_context=design_benchmark_style_context or None,
                )
                if design_assets:
                    write_json_file(version_dir / "last_design_assets.json", {"assets": design_assets})
                    add_log(f"Design Agent: {len(design_assets)} images ready.", project_id=project_id)
                    try:
                        cataloged_count = catalog_design_assets(
                            project_id=project_id,
                            version=version,
                            design_assets=design_assets,
                            archetype=effective_archetype,
                        )
                        if cataloged_count:
                            print(f"Image Catalog: Cataloged {cataloged_count} new images.")
                    except Exception as catalog_err:
                        print(f"Image catalog hook failed (non-fatal): {catalog_err}")
                else:
                    add_log("Design Agent: No images generated, continuing...", project_id=project_id)
            except Exception as design_err:
                print(f"DesignAgent failed (non-fatal): {design_err}")
                add_log("Design Agent: Skipped, continuing with build...", project_id=project_id)

        engineer_task = None
        fallback_task = None
        ui_keywords = ["html", "ui", "frontend", "scaffold", "interface", "web", "page", "app", "component"]
        for milestone in plan.milestones:
            for task in milestone.tasks:
                if task.execution_hint == "engineer" and task.task_type == "scaffold":
                    desc_lower = task.description.lower()
                    if any(kw in desc_lower for kw in ui_keywords):
                        engineer_task = task
                        break
                    elif fallback_task is None:
                        fallback_task = task
            if engineer_task:
                break
        if not engineer_task:
            engineer_task = fallback_task
        if not engineer_task:
            raise ValueError("No engineer tasks found in plan")

        # Query Watson Discovery for best archetype-matched build (initial build only)
        reference_code = None
        benchmark_guidance = ""
        if not is_iteration:
            detected_archetype = get_plan_ui_archetype(plan) or locked_ui_archetype
            engineer_kit_archetype = DESIGN_KIT_ALIASES.get(engineer_task.ui_archetype, engineer_task.ui_archetype)
            if detected_archetype:
                benchmark_archetype = str(detected_archetype).strip()
                benchmark_kit_archetype = DESIGN_KIT_ALIASES.get(benchmark_archetype, benchmark_archetype)
                benchmark_guidance = get_archetype_benchmark_guidance(
                    benchmark_archetype,
                    prompt_text=task_description,
                )
                preferred_local_build = load_local_reference_build(
                    benchmark_archetype,
                    prompt_text=task_description,
                )
                if preferred_local_build and preferred_local_build.get("selection_reason") == "style_family":
                    reference_code = {
                        "html": preferred_local_build.get("html_code", ""),
                        "css": preferred_local_build.get("css_code", ""),
                        "score": preferred_local_build.get("eval_score") or preferred_local_build.get("label", "local-benchmark"),
                        "archetype": benchmark_archetype,
                        "benchmark_guidance": preferred_local_build.get("benchmark_guidance", benchmark_guidance),
                        "style_family": preferred_local_build.get("style_family"),
                    }
                    print(
                        f"[Benchmark] Using style-family local reference build for '{benchmark_archetype}' "
                        f"(project {preferred_local_build.get('project_id')}, label: {preferred_local_build.get('label')})"
                    )
                try:
                    best_build = None if reference_code is not None else discovery_client.query_best_build(benchmark_archetype)
                    if best_build and benchmark_kit_archetype == engineer_kit_archetype:
                        reference_code = {
                            "html": best_build.get("html_code", ""),
                            "css": best_build.get("css_code", ""),
                            "score": best_build.get("eval_score", "N/A"),
                            "archetype": benchmark_archetype,
                            "benchmark_guidance": benchmark_guidance,
                        }
                        msg = (
                            f"[Discovery] Found reference build for '{benchmark_archetype}' "
                            f"(score: {reference_code['score']})"
                        )
                        print(msg)
                    elif best_build:
                        print(
                            "[Discovery] Skipping reference build injection due to archetype mismatch: "
                            f"discovery='{benchmark_archetype}', engineer='{engineer_kit_archetype}'"
                        )
                    else:
                        msg = f"[Discovery] No reference build found for '{benchmark_archetype}'"
                        print(msg)
                except Exception as disc_err:
                    print(f"[Discovery] Query failed (non-fatal): {disc_err}")

                if reference_code is None and benchmark_kit_archetype == engineer_kit_archetype:
                    local_build = preferred_local_build or load_local_reference_build(
                        benchmark_archetype,
                        prompt_text=task_description,
                    )
                    if local_build:
                        reference_code = {
                            "html": local_build.get("html_code", ""),
                            "css": local_build.get("css_code", ""),
                            "score": local_build.get("eval_score") or local_build.get("label", "local-benchmark"),
                            "archetype": benchmark_archetype,
                            "benchmark_guidance": local_build.get("benchmark_guidance", benchmark_guidance),
                            "style_family": local_build.get("style_family"),
                        }
                        print(
                            f"[Benchmark] Using local reference build for '{benchmark_archetype}' "
                            f"(project {local_build.get('project_id')}, label: {local_build.get('label')})"
                        )
            else:
                print("[Discovery] Skipping query: no archetype detected from plan or project lock")

        add_log("Build Agent: Writing your code...", project_id=project_id)

        if is_iteration and ancestor_version_dir and (engineer_task.scaffold_mode or "legacy_single_page") != "componentized_app":
            ancestor_base_css = ancestor_version_dir / "code" / "src" / "base.css"
            current_src_dir = version_dir / "code" / "src"
            current_base_css = current_src_dir / "base.css"
            if ancestor_base_css.exists() and not current_base_css.exists():
                current_src_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ancestor_base_css, current_base_css)
                add_log("Build Agent: Copied base.css from previous version.", project_id=project_id)

        from agents.engineer_agent import EngineerAgent
        engineer = EngineerAgent(genai_client)
        componentized_mode = (engineer_task.scaffold_mode or "legacy_single_page") == "componentized_app"
        base_css_content = load_componentized_base_css(engineer_task.ui_archetype) if componentized_mode else None
        design_context = build_design_context(
            version_dir=version_dir,
            design_assets=design_assets,
            project_id=project_id,
            version=version,
            scaffold_mode="componentized_app" if componentized_mode else "legacy_single_page",
        )
        product_brief_context = build_product_brief_context(version_dir)
        visual_direction_context = build_visual_direction_context(version_dir)
        task_description_with_assets = task_description + product_brief_context + visual_direction_context + design_context

        result = engineer.run(
            engineer_task,
            user_prompt=task_description_with_assets,
            existing_code=existing_code,
            reference_images=reference_images or None,
            reference_code=reference_code,
            iteration_visual_dna=iteration_visual_dna,
            iteration_feature_inventory=iteration_feature_inventory,
        )

        if componentized_mode and not is_iteration:
            contract_validation = validate_componentized_contract_outputs(
                result.files,
                ui_archetype=engineer_task.ui_archetype,
            )
            missing_contract_paths = contract_validation["missing_paths"]
            contract_attempt = 0
            while not contract_validation["passed"] and contract_attempt < 2:
                add_log(
                    "Build Agent: Componentized scaffold contract was incomplete; requesting a repaired workspace.",
                    project_id=project_id,
                )
                attempt_note = (
                    "Your previous response omitted or under-filled required workspace files for a buildable app.\n"
                    if contract_attempt == 0
                    else "Your previous response still returned an incomplete, empty, or stubbed workspace.\n"
                )
                violation_block = format_componentized_contract_violations(contract_validation)
                contract_prompt = (
                    task_description_with_assets
                    + "\n\nCOMPONENTIZED CONTRACT ENFORCEMENT:\n"
                    + attempt_note
                    + "Return a COMPLETE componentized workspace now.\n"
                    + "Do not return an empty or near-empty files array.\n"
                    + f"Missing required files: {missing_contract_paths or 'none'}\n"
                    + ("Contract violations:\n" + violation_block + "\n" if violation_block else "")
                    + "At minimum, include package.json, index.html, src/main.tsx, and src/App.tsx, plus any supporting components/styles needed for the requested product.\n"
                    + "If the product is a dashboard or fintech app, the returned workspace must already mount a populated first screen with real KPIs, a chart region, and at least one supporting data panel.\n"
                )
                contract_result = engineer.run(
                    engineer_task,
                    user_prompt=contract_prompt,
                    existing_code=existing_code,
                    reference_images=reference_images or None,
                    reference_code=reference_code,
                    iteration_visual_dna=iteration_visual_dna,
                    iteration_feature_inventory=iteration_feature_inventory,
                )
                if contract_result.files:
                    result = contract_result
                contract_validation = validate_componentized_contract_outputs(
                    result.files,
                    ui_archetype=engineer_task.ui_archetype,
                )
                missing_contract_paths = contract_validation["missing_paths"]
                contract_attempt += 1
            contract_validation = validate_componentized_contract_outputs(
                result.files,
                ui_archetype=engineer_task.ui_archetype,
            )
            missing_contract_paths = contract_validation["missing_paths"]
            if not result.files or not contract_validation["passed"]:
                recovery_scope = get_componentized_required_contract_paths()
                recovery_task = engineer_task.model_copy(update={"output_files": recovery_scope})
                recovery_existing_code = existing_code
                recovery_result = engineer.run(
                    recovery_task,
                    user_prompt=build_componentized_contract_recovery_prompt(
                        task_description_with_assets=task_description_with_assets,
                        missing_paths=missing_contract_paths or recovery_scope,
                        contract_validation=contract_validation,
                    ),
                    existing_code=recovery_existing_code,
                    reference_images=reference_images or None,
                    reference_code=reference_code,
                    iteration_visual_dna=iteration_visual_dna,
                    iteration_feature_inventory=iteration_feature_inventory,
                )
                recovery_validation = validate_componentized_contract_outputs(
                    recovery_result.files,
                    ui_archetype=engineer_task.ui_archetype,
                )
                if not recovery_result.files or not recovery_validation["passed"]:
                    recovery_existing_code = build_componentized_scaffold_seed_context()
                    recovery_result = engineer.run(
                        recovery_task,
                        user_prompt=build_componentized_contract_recovery_prompt(
                            task_description_with_assets=task_description_with_assets,
                            missing_paths=missing_contract_paths or recovery_scope,
                            contract_validation=contract_validation,
                        )
                        + "\n\nRECOVERY SEED WORKSPACE:\n"
                          "A minimal Vite + React + TypeScript scaffold is provided below. "
                          "Use it as the starting point and replace the generic placeholder screen with the requested product.\n",
                        existing_code=recovery_existing_code,
                        reference_images=reference_images or None,
                        reference_code=reference_code,
                        iteration_visual_dna=iteration_visual_dna,
                        iteration_feature_inventory=iteration_feature_inventory,
                    )
                if recovery_result.files:
                    merged_files: dict[str, Any] = {
                        str(file_artifact.path).replace("\\", "/").strip("/"): file_artifact
                        for file_artifact in result.files
                    }
                    for file_artifact in recovery_result.files:
                        merged_files[str(file_artifact.path).replace("\\", "/").strip("/")] = file_artifact
                    result = recovery_result.model_copy(update={"files": list(merged_files.values())})
                contract_validation = validate_componentized_contract_outputs(
                    result.files,
                    ui_archetype=engineer_task.ui_archetype,
                )
                missing_contract_paths = contract_validation["missing_paths"]
            if not result.files or not contract_validation["passed"]:
                missing_list = ", ".join(missing_contract_paths) if missing_contract_paths else "none"
                violation_block = format_componentized_contract_violations(contract_validation)
                raise ValueError(
                    "Componentized scaffold contract was not satisfied after enforcement "
                    f"(missing: {missing_list}, files_generated: {len(result.files)}, violations: {violation_block or 'none'})."
                )

        if componentized_mode:
            for file_artifact in result.files:
                file_artifact.content = rewrite_componentized_asset_api_urls(file_artifact.content)

        from scripts.safe_write import safe_write_text, enforce_iteration_scope
        allow_dir = version_dir / "code"
        writes = []
        if is_iteration and engineer_task.output_files:
            enforce_iteration_scope(engineer_task.output_files, result.files)
        for file_artifact in result.files:
            try:
                rec = safe_write_text(
                    allowlist_dir=allow_dir,
                    relative_path=file_artifact.path,
                    content=file_artifact.content,
                )
                writes.append(rec)
                add_log(f"Build Agent: Created {file_artifact.path}", project_id=project_id)
            except ValueError as skip_err:
                # In iteration mode, fail hard to keep behavior deterministic and auditable.
                if is_iteration:
                    raise
                print(f"Build Agent: Skipped {file_artifact.path} ({skip_err})")
                print(f"Skipped file: {skip_err}")

        preview_build = None
        build_repair: dict[str, Any] = {
            "triggered": False,
            "status": "skipped",
            "errors": [],
            "scoped_files": [],
        }
        quality_refinement: dict[str, Any] = {
            "triggered": False,
            "issues": [],
            "status": "skipped",
        }
        content_refinement: dict[str, Any] = {
            "triggered": False,
            "issues": [],
            "status": "skipped",
            "weak_files": [],
        }
        if componentized_mode:
            workspace_support = ensure_componentized_workspace_support(
                version_dir / "code",
                base_css_content=base_css_content if not is_iteration else None,
                ui_archetype=engineer_task.ui_archetype,
            )
            if workspace_support["created_files"] or workspace_support["rewritten_files"]:
                add_log(
                    "Build Agent: Normalized componentized workspace support files.",
                    project_id=project_id,
                )
            add_log("Build Agent: Preparing componentized preview...", project_id=project_id)
            preview_build = build_componentized_version(version_dir)
            if preview_build.get("status") == "success":
                build_repair["status"] = "not_needed"
                add_log("Build Agent: Componentized preview build ready.", project_id=project_id)
            else:
                reason = preview_build.get("reason") or "unknown build failure"
                add_log(
                    f"Build Agent: Componentized preview build failed ({reason}).",
                    log_type="warning",
                    project_id=project_id,
                )
                build_errors = parse_componentized_build_errors(preview_build, code_dir=version_dir / "code")
                build_repair["errors"] = build_errors
                narrow_repair_scope = [
                    error["path"]
                    for error in build_errors
                    if (version_dir / "code" / str(error.get("path") or "")).exists()
                ]
                repair_scope = select_componentized_build_repair_scope(
                    version_dir / "code",
                    build_errors,
                )
                if not repair_scope:
                    repair_scope = extend_componentized_scope(
                        version_dir / "code",
                        narrow_repair_scope or collect_componentized_editable_files(version_dir / "code"),
                        include_style_targets=True,
                        include_direct_support=True,
                    )
                build_repair["scoped_files"] = repair_scope
                repair_existing_code = collect_selected_code_context(version_dir / "code", repair_scope) or collect_existing_code_context(version_dir / "code")
                if repair_existing_code and repair_scope:
                    add_log("Build Agent: Running automatic build-repair pass...", project_id=project_id)
                    build_repair["triggered"] = True
                    build_repair["status"] = "started"
                    repair_task = engineer_task.model_copy(update={"output_files": repair_scope})
                    repair_prompt = (
                        build_componentized_build_repair_prompt(
                            task_description_with_assets=task_description_with_assets,
                            build_errors=build_errors,
                        )
                        if build_errors
                        else (
                            task_description_with_assets
                            + "\n\nBUILD REPAIR PASS:\n"
                              "The current componentized workspace must build cleanly with `npm run build`.\n"
                              "Preserve the visual direction, required sections, and seeded content unless a change is required to fix the build.\n"
                              "Fix only the files necessary to resolve these errors.\n\n"
                              "Hard rules while repairing:\n"
                              "- Do not use explicit local import extensions like `./App.tsx` or `./data.ts`.\n"
                              "- If base.css is used, import it only from `src/main.tsx` as `import \"./base.css\";`.\n"
                              "- Do not import base.css from components or nested files.\n"
                              "- Make the minimum fix needed. Do not refactor, redesign, add features, or change behavior unrelated to the failing error.\n"
                              "- If contamination crosses file boundaries, return every affected file together so the workspace is coherent.\n"
                              "- Re-check each repaired file for language containment, imports at top, balanced braces/brackets, closed comments, and valid exports before returning JSON.\n"
                              "- Prefer fixes that keep the app building under Vite without adding unnecessary dependencies.\n\n"
                              "BUILD ERRORS:\n"
                            + summarize_componentized_build_error(preview_build)
                        )
                    )
                    repair_result = engineer.run(
                        repair_task,
                        user_prompt=repair_prompt,
                        existing_code=repair_existing_code,
                        reference_images=reference_images or None,
                        reference_code=reference_code,
                        iteration_visual_dna=iteration_visual_dna,
                        iteration_feature_inventory=iteration_feature_inventory,
                    )
                    for file_artifact in repair_result.files:
                        file_artifact.content = rewrite_componentized_asset_api_urls(file_artifact.content)
                    try:
                        enforce_componentized_internal_scope(repair_scope, repair_result.files)
                    except ValueError as repair_scope_err:
                        build_repair["status"] = "scope_violation"
                        build_repair["error"] = str(repair_scope_err)
                        add_log(
                            f"Build Agent: Automatic repair returned files outside scope ({repair_scope_err}).",
                            log_type="warning",
                            project_id=project_id,
                        )
                    else:
                        for file_artifact in repair_result.files:
                            rec = safe_write_text(
                                allowlist_dir=allow_dir,
                                relative_path=file_artifact.path,
                                content=file_artifact.content,
                            )
                            writes.append(rec)
                            add_log(f"Build Agent: Repaired {file_artifact.path}", project_id=project_id)
                        ensure_componentized_workspace_support(
                            version_dir / "code",
                            base_css_content=base_css_content if not is_iteration else None,
                            ui_archetype=engineer_task.ui_archetype,
                        )
                        preview_build = build_componentized_version(version_dir)
                        if preview_build.get("status") == "success":
                            result = repair_result
                            build_repair["status"] = "success"
                            add_log("Build Agent: Automatic repair restored a working preview.", project_id=project_id)
                        else:
                            build_repair["status"] = "failed"
                            reason = preview_build.get("reason") or "unknown build failure"
                            add_log(
                                f"Build Agent: Automatic repair still failed ({reason}).",
                                log_type="warning",
                                project_id=project_id,
                            )

            if preview_build.get("status") == "success":
                density_audit = evaluate_componentized_density(
                    version_dir / "code",
                    ui_archetype=engineer_task.ui_archetype,
                )
                semantic_evaluation = evaluate_componentized_semantic_completeness(
                    version_dir / "code",
                    ui_archetype=engineer_task.ui_archetype,
                )
                multi_file_evaluation = evaluate_componentized_multi_file_completeness(
                    version_dir / "code",
                    ui_archetype=engineer_task.ui_archetype,
                )
                refinement_issues = detect_componentized_quality_issues(
                    version_dir / "code",
                    ui_archetype=engineer_task.ui_archetype,
                )
                refinement_issues.extend(
                    collect_quality_issue_codes(
                        density_audit=density_audit,
                        semantic_evaluation=semantic_evaluation,
                        multi_file_evaluation=multi_file_evaluation,
                    )
                )
                refinement_issues.extend(extract_componentized_self_review_issues(result.self_review))
                refinement_issues = list(dict.fromkeys(refinement_issues))
                weak_file_paths = [
                    str(report.get("path") or "")
                    for report in (multi_file_evaluation.get("weak_files") or [])
                    if report.get("path")
                ]
                content_fix_issues = [
                    issue
                    for issue in collect_quality_issue_codes(
                        density_audit=density_audit,
                        semantic_evaluation=semantic_evaluation,
                        multi_file_evaluation=multi_file_evaluation,
                    )
                    if issue in CONTENT_FIX_ISSUES
                ]
                if content_fix_issues or weak_file_paths:
                    content_refinement = {
                        "triggered": True,
                        "issues": content_fix_issues,
                        "status": "started",
                        "weak_files": weak_file_paths,
                        "semantic_evaluation": semantic_evaluation,
                        "multi_file_evaluation": multi_file_evaluation,
                    }
                    add_log("Build Agent: Running targeted content-fix pass...", project_id=project_id)
                    content_scope = select_componentized_content_fix_scope(
                        version_dir / "code",
                        weak_file_paths=weak_file_paths,
                    )
                    content_existing_code = collect_selected_code_context(version_dir / "code", content_scope)
                    if content_existing_code and content_scope:
                        backup_dir = version_dir / ".content-refinement-backup"
                        if backup_dir.exists():
                            shutil.rmtree(backup_dir, ignore_errors=True)
                        shutil.copytree(version_dir / "code", backup_dir)
                        content_task = engineer_task.model_copy(update={"output_files": content_scope})
                        content_result = engineer.run(
                            content_task,
                            user_prompt=build_componentized_content_fix_prompt(
                                task_description_with_assets=task_description_with_assets,
                                ui_archetype=engineer_task.ui_archetype,
                                semantic_evaluation=semantic_evaluation,
                                multi_file_evaluation=multi_file_evaluation,
                            ),
                            existing_code=content_existing_code,
                            reference_images=reference_images or None,
                            reference_code=reference_code,
                            iteration_visual_dna=iteration_visual_dna,
                            iteration_feature_inventory=iteration_feature_inventory,
                        )
                        for file_artifact in content_result.files:
                            file_artifact.content = rewrite_componentized_asset_api_urls(file_artifact.content)
                        try:
                            enforce_componentized_internal_scope(content_scope, content_result.files)
                        except ValueError as content_scope_err:
                            content_refinement["status"] = "scope_violation"
                            content_refinement["error"] = str(content_scope_err)
                            add_log(
                                f"Build Agent: Content-fix skipped because it returned files outside scope ({content_scope_err}).",
                                log_type="warning",
                                project_id=project_id,
                            )
                            shutil.rmtree(backup_dir, ignore_errors=True)
                        else:
                            for file_artifact in content_result.files:
                                rec = safe_write_text(
                                    allowlist_dir=allow_dir,
                                    relative_path=file_artifact.path,
                                    content=file_artifact.content,
                                )
                                writes.append(rec)
                                add_log(f"Build Agent: Content-fixed {file_artifact.path}", project_id=project_id)
                            ensure_componentized_workspace_support(
                                version_dir / "code",
                                base_css_content=base_css_content if not is_iteration else None,
                                ui_archetype=engineer_task.ui_archetype,
                            )
                            content_preview_build = build_componentized_version(version_dir)
                            if content_preview_build.get("status") == "success":
                                result = content_result
                                preview_build = content_preview_build
                                content_refinement["status"] = "success"
                                density_audit = evaluate_componentized_density(
                                    version_dir / "code",
                                    ui_archetype=engineer_task.ui_archetype,
                                )
                                semantic_evaluation = evaluate_componentized_semantic_completeness(
                                    version_dir / "code",
                                    ui_archetype=engineer_task.ui_archetype,
                                )
                                multi_file_evaluation = evaluate_componentized_multi_file_completeness(
                                    version_dir / "code",
                                    ui_archetype=engineer_task.ui_archetype,
                                )
                                weak_file_paths = [
                                    str(report.get("path") or "")
                                    for report in (multi_file_evaluation.get("weak_files") or [])
                                    if report.get("path")
                                ]
                                add_log("Build Agent: Content-fix pass applied cleanly.", project_id=project_id)
                                shutil.rmtree(backup_dir, ignore_errors=True)
                            else:
                                content_refinement["status"] = "reverted"
                                reason = content_preview_build.get("reason") or "unknown build failure"
                                add_log(
                                    f"Build Agent: Content-fix pass failed ({reason}); restoring prior workspace.",
                                    log_type="warning",
                                    project_id=project_id,
                                )
                                shutil.rmtree(version_dir / "code", ignore_errors=True)
                                shutil.copytree(backup_dir, version_dir / "code")
                                shutil.rmtree(backup_dir, ignore_errors=True)
                refinement_issues = detect_componentized_quality_issues(
                    version_dir / "code",
                    ui_archetype=engineer_task.ui_archetype,
                )
                refinement_issues.extend(
                    collect_quality_issue_codes(
                        density_audit=density_audit,
                        semantic_evaluation=semantic_evaluation,
                        multi_file_evaluation=multi_file_evaluation,
                    )
                )
                refinement_issues.extend(extract_componentized_self_review_issues(result.self_review))
                refinement_issues = list(dict.fromkeys(refinement_issues))
                if refinement_issues:
                    quality_refinement = {
                        "triggered": True,
                        "issues": refinement_issues,
                        "status": "started",
                        "first_pass_self_review": result.self_review.model_dump() if result.self_review else None,
                        "density_audit": density_audit,
                        "semantic_evaluation": semantic_evaluation,
                        "multi_file_evaluation": multi_file_evaluation,
                        "weak_files": weak_file_paths,
                    }
                    add_log("Build Agent: Running automatic quality-refinement pass...", project_id=project_id)
                    refinement_scope = select_componentized_refinement_scope(
                        version_dir / "code",
                        refinement_issues,
                        weak_file_paths=weak_file_paths,
                    )
                    refinement_existing_code = collect_selected_code_context(version_dir / "code", refinement_scope)
                    if refinement_existing_code and refinement_scope:
                        backup_dir = version_dir / ".quality-refinement-backup"
                        if backup_dir.exists():
                            shutil.rmtree(backup_dir, ignore_errors=True)
                        shutil.copytree(version_dir / "code", backup_dir)

                        refinement_task = engineer_task.model_copy(update={"output_files": refinement_scope})
                        refinement_prompt = build_componentized_refinement_prompt(
                            task_description_with_assets=task_description_with_assets,
                            issues=refinement_issues,
                            ui_archetype=engineer_task.ui_archetype,
                            self_review=result.self_review,
                            density_audit=density_audit,
                            semantic_evaluation=semantic_evaluation,
                            multi_file_evaluation=multi_file_evaluation,
                        )
                        refinement_result = engineer.run(
                            refinement_task,
                            user_prompt=refinement_prompt,
                            existing_code=refinement_existing_code,
                            reference_images=reference_images or None,
                            reference_code=reference_code,
                            iteration_visual_dna=iteration_visual_dna,
                            iteration_feature_inventory=iteration_feature_inventory,
                        )
                        for file_artifact in refinement_result.files:
                            file_artifact.content = rewrite_componentized_asset_api_urls(file_artifact.content)
                        try:
                            enforce_componentized_internal_scope(refinement_scope, refinement_result.files)
                        except ValueError as refinement_scope_err:
                            quality_refinement["status"] = "scope_violation"
                            quality_refinement["error"] = str(refinement_scope_err)
                            add_log(
                                f"Build Agent: Quality-refinement skipped because it returned files outside scope ({refinement_scope_err}).",
                                log_type="warning",
                                project_id=project_id,
                            )
                            shutil.rmtree(backup_dir, ignore_errors=True)
                        else:
                            for file_artifact in refinement_result.files:
                                rec = safe_write_text(
                                    allowlist_dir=allow_dir,
                                    relative_path=file_artifact.path,
                                    content=file_artifact.content,
                                )
                                writes.append(rec)
                                add_log(f"Build Agent: Refined {file_artifact.path}", project_id=project_id)

                            ensure_componentized_workspace_support(
                                version_dir / "code",
                                base_css_content=base_css_content if not is_iteration else None,
                                ui_archetype=engineer_task.ui_archetype,
                            )
                            refined_preview_build = build_componentized_version(version_dir)
                            if refined_preview_build.get("status") == "success":
                                result = refinement_result
                                preview_build = refined_preview_build
                                quality_refinement["status"] = "success"
                                quality_refinement["final_self_review"] = (
                                    refinement_result.self_review.model_dump() if refinement_result.self_review else None
                                )
                                quality_refinement["final_density_audit"] = evaluate_componentized_density(
                                    version_dir / "code",
                                    ui_archetype=engineer_task.ui_archetype,
                                )
                                quality_refinement["final_semantic_evaluation"] = evaluate_componentized_semantic_completeness(
                                    version_dir / "code",
                                    ui_archetype=engineer_task.ui_archetype,
                                )
                                quality_refinement["final_multi_file_evaluation"] = evaluate_componentized_multi_file_completeness(
                                    version_dir / "code",
                                    ui_archetype=engineer_task.ui_archetype,
                                )
                                add_log("Build Agent: Quality-refinement pass applied cleanly.", project_id=project_id)
                                shutil.rmtree(backup_dir, ignore_errors=True)
                            else:
                                quality_refinement["status"] = "reverted"
                                reason = refined_preview_build.get("reason") or "unknown build failure"
                                add_log(
                                    f"Build Agent: Quality-refinement pass failed ({reason}); restoring prior workspace.",
                                    log_type="warning",
                                    project_id=project_id,
                                )
                                shutil.rmtree(version_dir / "code", ignore_errors=True)
                                shutil.copytree(backup_dir, version_dir / "code")
                                shutil.rmtree(backup_dir, ignore_errors=True)
                else:
                    quality_refinement = {
                        "triggered": False,
                        "issues": [],
                        "status": "not_needed",
                        "density_audit": density_audit,
                        "semantic_evaluation": semantic_evaluation,
                        "multi_file_evaluation": multi_file_evaluation,
                    }

        add_log("Build complete.", project_id=project_id)
        state["result_ready"] = True

        filled_assets_count = 0
        try:
            filled_assets_count = fill_missing_assets(
                project_id=project_id,
                version=version,
                archetype=effective_archetype,
            )
            print(
                f"Asset filler: filled {filled_assets_count} missing images from library"
            )
        except Exception as asset_fill_err:
            print(f"Asset filler failed (non-fatal): {asset_fill_err}")

        code_dir = version_dir / "code"
        if code_dir.exists():
            write_json_file(version_dir / "last_visual_dna.json", extract_visual_dna(code_dir))
            write_json_file(version_dir / "last_feature_inventory.json", extract_feature_inventory(code_dir))
            if componentized_mode:
                write_json_file(
                    version_dir / "last_density_audit.json",
                    evaluate_componentized_density(code_dir, ui_archetype=engineer_task.ui_archetype),
                )
                write_json_file(
                    version_dir / "last_semantic_evaluation.json",
                    evaluate_componentized_semantic_completeness(code_dir, ui_archetype=engineer_task.ui_archetype),
                )
                write_json_file(
                    version_dir / "last_multi_file_evaluation.json",
                    evaluate_componentized_multi_file_completeness(code_dir, ui_archetype=engineer_task.ui_archetype),
                )
        if result.change_manifest:
            write_json_file(version_dir / "last_change_manifest.json", result.change_manifest.model_dump())

        execution_result = {
            "kind": "execution_result",
            "agent_role": "engineer",
            "status": "success",
            "request_hash": "",
            "request": {
                "kind": "execution_request",
                "task_id": engineer_task.id,
                "title": task_description,
                "payload": {"task_description": task_description},
            },
            "outputs": {
                "action": "engineer_execution",
                "task_id": engineer_task.id,
                "summary": result.summary,
                "self_review": result.self_review.model_dump() if result.self_review else None,
                "change_manifest": result.change_manifest.model_dump() if result.change_manifest else None,
                "files_generated": len(result.files),
                "preview_build": preview_build,
                "build_repair": build_repair,
                "content_refinement": content_refinement,
                "quality_refinement": quality_refinement,
                "writes": [
                    {"path": str(rec.path), "sha256": rec.sha256, "bytes": rec.bytes}
                    for rec in writes
                ],
            },
            "error": None,
            "_agent_sequence": ["pm", "planner", "engineer"],
            "logs": list(state.get("logs", [])),
            "_meta": {
                "produced_at": datetime.now(timezone.utc).isoformat(),
                "consumer_version": "v4",
            },
        }
        write_json_file(version_dir / "last_execution_result.json", execution_result)

        print(f"Execution result saved: {len(writes)} files generated")

        if execution_id:
            execution = session.get(Execution, execution_id)
            if execution:
                execution.status = "success"
                execution.result_path = str(version_dir / "last_execution_result.json")
                execution.prd_path = str(version_dir / "last_prd.json")
                execution.plan_path = str(version_dir / "last_plan.json")
                # Build metrics
                execution.duration_seconds = round(time.time() - pipeline_start_time, 2)
                execution.model_used = "Claude Opus 4.6"
                if hasattr(result, "usage") and result.usage:
                    input_tokens = getattr(result.usage, "input_tokens", 0) or 0
                    output_tokens = getattr(result.usage, "output_tokens", 0) or 0
                    execution.tokens_used = input_tokens + output_tokens
                    if execution.tokens_used:
                        # Gemini 2.5 Flash pricing: $0.15/M input, $0.60/M output (under 200k context)
                        execution.estimated_cost = round(
                            (input_tokens * 0.00000015) + (output_tokens * 0.0000006), 4
                        )
                    # 1 credit = 2500 tokens, minimum 1
                    execution.credits_used = max(1, round(execution.tokens_used / 2500))
                if (
                    execution.version == 1
                    and not project.locked_ui_archetype
                ):
                    locked = get_plan_ui_archetype(plan)
                    if locked:
                        project.locked_ui_archetype = locked
                session.commit()
                project = execution.project
                if project:
                    project.status = "completed"
                    project.updated_at = datetime.now(timezone.utc)
                    session.commit()

        # Governance Agent — generate AI Factsheet
        try:
            from agents.governance_agent import GovernanceAgent
            gov_agent = GovernanceAgent()

            result_data = read_json_file(version_dir / "last_execution_result.json") or {}
            files_count = result_data.get("outputs", {}).get("files_generated", 0)
            assets_data = read_json_file(version_dir / "last_design_assets.json") or {}
            images_count = len(assets_data.get("assets", []))

            exec_for_gov = session.get(Execution, execution_id)
            prompt_text = task_description

            factsheet = gov_agent.generate_factsheet(
                project_id=project_id,
                project_name=project.name if project else "Unknown",
                version=version,
                execution_id=execution_id,
                prompt=prompt_text,
                ui_archetype=project.locked_ui_archetype if project else None,
                models_used={
                    "Requirements Agent": "Gemini 2.5 Flash",
                    "Architecture Agent": "Gemini 2.5 Flash",
                    "Design Agent": "Imagen 4.0 Ultra + Gemini 2.5 Flash",
                    "Build Agent": "Gemini 2.5 Flash",
                },
                tokens_used=exec_for_gov.tokens_used if exec_for_gov else None,
                estimated_cost=exec_for_gov.estimated_cost if exec_for_gov else None,
                credits_used=exec_for_gov.credits_used if exec_for_gov else None,
                duration_seconds=exec_for_gov.duration_seconds if exec_for_gov else None,
                files_generated=files_count,
                images_generated=images_count,
                agent_sequence=["pm", "planner", "design", "engineer"],
                status="success",
            )

            write_json_file(version_dir / "last_factsheet.json", factsheet)

            exec_for_gov = session.get(Execution, execution_id)
            if exec_for_gov:
                exec_for_gov.governance_log = json.dumps(factsheet)
                readiness = factsheet.get("readiness", {})
                exec_for_gov.readiness_score = readiness.get("combined_score")
                exec_for_gov.quality_tier = readiness.get("quality_tier")
                session.commit()

            add_log("Governance Agent: Factsheet recorded.", project_id=project_id)

            # Build Insights - prompt coaching suggestions
            try:
                from agents.insights_agent import InsightsAgent
                insights_agent = InsightsAgent()

                # Load quality_target from plan
                plan_data = read_json_file(version_dir / "last_plan.json") or {}
                quality_target = None
                for ms in plan_data.get("milestones", []):
                    for task in ms.get("tasks", []):
                        if task.get("execution_hint") == "engineer":
                            quality_target = task.get("quality_target")
                            break
                    if quality_target:
                        break

                scoring = factsheet.get("scoring", {})
                prompt_quality = scoring.get("prompt_quality", {})
                build_conf = scoring.get("build_confidence", {})

                insights = insights_agent.generate_insights(
                    prompt=prompt_text,
                    ui_archetype=project.locked_ui_archetype if project else None,
                    quality_target=quality_target,
                    prompt_score=prompt_quality.get("score"),
                    build_confidence=build_conf.get("score"),
                    files_generated=files_count,
                    images_generated=images_count,
                )

                write_json_file(version_dir / "last_insights.json", {"insights": insights})
                add_log("Build Insights: Generated prompt suggestions.", project_id=project_id)
            except Exception as e:
                print(f"[Insights] Non-fatal error: {e}")
        except Exception as gov_err:
            print(f"GovernanceAgent failed (non-fatal): {gov_err}")

    except Exception as e:
        error_msg = str(e)
        short_msg = error_msg.split("\n")[0][:200]
        add_log(f"Something went wrong: {short_msg}", project_id=project_id)
        state["result_ready"] = True
        print(f"Pipeline error: {error_msg}")

        if execution_id:
            try:
                execution = session.get(Execution, execution_id)
                if execution:
                    execution.status = "error"
                    execution.error_message = error_msg
                    session.commit()
                    project = execution.project
                    if project:
                        project.status = "failed"
                        project.updated_at = datetime.now(timezone.utc)
                        session.commit()
            except Exception:
                pass

        if project_id and version:
            write_json_file(get_version_dir(project_id, version) / "last_execution_result.json", {
                "kind": "execution_result",
                "agent_role": "engineer",
                "status": "error",
                "error": {"message": error_msg, "type": type(e).__name__},
                "outputs": {},
                "_agent_sequence": [],
            })

    finally:
        state["running"] = False
        session.close()
        print("Pipeline complete")


# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

@app.route("/api/projects", methods=["GET"])
@jwt_required()
def list_projects():
    session = get_session()
    try:
        uid = get_jwt_identity()
        query = session.query(Project).filter(Project.owner_id == int(uid)).order_by(Project.updated_at.desc())
        projects = query.all()
        return jsonify([p.to_dict() for p in projects]), 200
    finally:
        session.close()


@app.route("/api/stats", methods=["GET"])
@jwt_required()
def get_stats():
    from sqlalchemy import func
    uid = get_jwt_identity()
    session = get_session()
    try:
        base_q = session.query(Execution.project_id, func.max(Execution.version))
        base_q = base_q.join(Project).filter(Project.owner_id == int(uid))
        version_counts = base_q.group_by(Execution.project_id).all()
        versions_shipped = sum(v for _, v in version_counts)

        # avg_build_time_seconds from completed executions that have duration
        avg_q = session.query(func.avg(Execution.duration_seconds)).filter(
            Execution.status == "success", Execution.duration_seconds.isnot(None)
        )
        avg_q = avg_q.join(Project).filter(Project.owner_id == int(uid))
        avg_row = avg_q.scalar()
        avg_build_time_seconds = round(avg_row, 1) if avg_row else None

        # lines_generated: walk all version code dirs and count lines
        total_lines = 0
        lines_q = session.query(Execution.project_id, Execution.version).filter(Execution.status == "success")
        lines_q = lines_q.join(Project).filter(Project.owner_id == int(uid))
        all_execs = lines_q.all()
        for pid, ver in all_execs:
            code_dir = get_version_dir(pid, ver) / "code"
            if code_dir.exists():
                for f in code_dir.rglob("*"):
                    if f.is_file() and f.suffix in (".html", ".css", ".js", ".ts", ".tsx", ".jsx", ".py", ".json"):
                        try:
                            total_lines += f.read_text(encoding="utf-8", errors="ignore").count("\n") + 1
                        except Exception:
                            pass

        # pipelines_today: executions created today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_q = session.query(func.count(Execution.id)).filter(Execution.created_at >= today_start)
        today_q = today_q.join(Project).filter(Project.owner_id == int(uid))
        pipelines_today = today_q.scalar() or 0

        return jsonify({
            "versions_shipped": versions_shipped,
            "avg_build_time_seconds": avg_build_time_seconds,
            "lines_generated": total_lines,
            "pipelines_today": pipelines_today,
        }), 200
    finally:
        session.close()


@app.route("/api/activity", methods=["GET"])
@jwt_required()
def get_activity():
    session = get_session()
    try:
        uid = get_jwt_identity()
        query = session.query(Execution).join(Project).filter(Project.owner_id == int(uid)).order_by(Execution.created_at.desc())
        recent = query.limit(6).all()
        items = []
        for e in recent:
            project = session.get(Project, e.project_id)
            items.append({
                "project_name": project.name if project else "Unknown",
                "project_id": e.project_id,
                "status": e.status,
                "version": e.version,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            })
        return jsonify(items), 200
    finally:
        session.close()


@app.route("/api/projects", methods=["POST"])
def create_project():
    session = get_session()
    try:
        data = request.get_json()
        if not data or not data.get("name"):
            return jsonify({"error": "Project name is required"}), 400
        uid = get_optional_request_user_id()
        project = Project(
            name=data["name"],
            description=data.get("description", ""),
            status="pending",
            owner_id=uid,
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        return jsonify(project.to_dict()), 201
    finally:
        session.close()


@app.route("/api/projects/<int:project_id>/claim", methods=["POST"])
@jwt_required()
def claim_project(project_id: int):
    session = get_session()
    try:
        uid = int(get_jwt_identity())
        try:
            project = claim_guest_project_for_user(session, project_id, uid)
        except LookupError:
            session.rollback()
            return jsonify({"error": "Project not found"}), 404
        except ValueError:
            session.rollback()
            return jsonify({"error": "Project has already been claimed"}), 409

        session.commit()
        session.refresh(project)
        return jsonify(project.to_dict()), 200
    finally:
        session.close()


@app.route("/api/projects/<int:project_id>", methods=["GET"])
def get_project(project_id: int):
    session = get_session()
    try:
        project = session.get(Project, project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        project_dict = project.to_dict()
        project_dict["executions"] = [e.to_dict() for e in project.executions]
        return jsonify(project_dict), 200
    finally:
        session.close()


@app.route('/api/projects/<int:project_id>', methods=['PATCH'])
@jwt_required()
def rename_project(project_id):
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    session = get_session()
    try:
        project = session.get(Project, project_id)
        if not project:
            return jsonify({'error': 'Not found'}), 404
        project.name = name
        session.commit()
        return jsonify({'id': project_id, 'name': name})
    finally:
        session.close()


@app.route("/api/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id: int):
    session = get_session()
    try:
        project = session.get(Project, project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        session.delete(project)
        session.commit()
        # Clean up generated files on disk
        project_dir = PUBLIC_DIR / str(project_id)
        try:
            import shutil as _shutil
            _shutil.rmtree(project_dir)
        except FileNotFoundError:
            pass
        return jsonify({"message": "Project deleted"}), 200
    finally:
        session.close()


@app.route("/api/seed", methods=["POST"])
@jwt_required()
def seed_projects():
    session = get_session()
    created_dirs: list[Path] = []
    try:
        user_id = int(get_jwt_identity())
        existing_project = (
            session.query(Project.id)
            .filter(Project.owner_id == user_id)
            .first()
        )
        if existing_project:
            return jsonify({"seeded": False}), 200

        seeded_projects: list[Project] = []

        for seed in SEED_PROJECTS:
            source_dir = SEED_DATA_DIR / seed["folder"]
            if not source_dir.exists():
                raise FileNotFoundError(f"Seed data folder not found: {source_dir}")

            project = Project(
                name=seed["name"],
                description=seed["description"],
                status="completed",
                owner_id=user_id,
                locked_ui_archetype=seed["archetype"],
            )
            session.add(project)
            session.flush()

            execution = Execution(
                project_id=project.id,
                owner_id=user_id,
                status="success",
                version=1,
                is_active_head=True,
                model_used="Gemini 2.5 Flash",
                duration_seconds=45.0,
                tokens_used=18000,
                credits_used=7,
            )
            session.add(execution)
            session.flush()

            version_dir = get_version_dir(project.id, execution.version)
            created_dirs.append(version_dir)
            if version_dir.exists():
                shutil.rmtree(version_dir, ignore_errors=True)
            version_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_dir, version_dir)

            rewrite_seed_version(version_dir, seed["original_project_id"], project.id)
            factsheet = update_seed_factsheet(version_dir, project, execution)

            execution.prd_path = str(version_dir / "last_prd.json")
            execution.plan_path = str(version_dir / "last_plan.json")
            execution.result_path = str(version_dir / "last_execution_result.json")

            if factsheet:
                readiness = factsheet.get("readiness") or {}
                execution.governance_log = json.dumps(factsheet)
                execution.readiness_score = readiness.get("combined_score")
                execution.quality_tier = readiness.get("quality_tier")

            seeded_projects.append(project)

        session.commit()
        return jsonify({
            "seeded": True,
            "projects": [project.to_dict() for project in seeded_projects],
        }), 200
    except Exception as e:
        session.rollback()
        for path in reversed(created_dirs):
            shutil.rmtree(path, ignore_errors=True)
        print(f"Failed to seed projects: {e}")
        return jsonify({"error": "Failed to seed starter projects"}), 500
    finally:
        session.close()


@app.route("/api/projects/<int:project_id>/reset-build", methods=["POST"])
def reset_build(project_id):
    db = get_session()
    try:
        stuck = db.query(Execution).filter(
            Execution.project_id == project_id,
            Execution.status == "running"
        ).first()
        if stuck:
            stuck.status = "failed"
            db.commit()
            return jsonify({"reset": True, "execution_id": stuck.id})
        return jsonify({"reset": False, "message": "No running execution found"})
    finally:
        db.close()


# ============================================================================
# VERSION ENDPOINTS (Phase 7A)
# ============================================================================

@app.route("/api/projects/<int:project_id>/versions", methods=["GET"])
def get_versions(project_id: int):
    session = get_session()
    try:
        project = session.get(Project, project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        executions = (
            session.query(Execution)
            .filter(Execution.project_id == project_id)
            .order_by(Execution.version.desc())
            .all()
        )
        versions_list = []
        for e in executions:
            e_dict = e.to_dict()
            if project_id and e.version:
                result_path = get_version_dir(project_id, e.version) / "last_execution_result.json"
                result_data = read_json_file(result_path)
                if result_data:
                    e_dict["files_generated"] = result_data.get("outputs", {}).get("files_generated", 0)
                assets_path = get_version_dir(project_id, e.version) / "last_design_assets.json"
                assets_data = read_json_file(assets_path)
                e_dict["images_generated"] = len(assets_data.get("assets", [])) if assets_data else 0
            versions_list.append(e_dict)
        return jsonify({
            "project_id": project_id,
            "project_name": project.name,
            "versions": versions_list,
        }), 200
    finally:
        session.close()


@app.route("/api/projects/<int:project_id>/versions/<int:version>/logs", methods=["GET"])
def get_version_logs(project_id: int, version: int):
    session = get_session()
    try:
        execution = (
            session.query(Execution)
            .filter(Execution.project_id == project_id, Execution.version == version)
            .first()
        )
        if not execution:
            return jsonify({"error": "Version not found"}), 404

        logs = []

        # Try to read logs from the execution result JSON
        result_path = get_version_dir(project_id, version) / "last_execution_result.json"
        result_data = read_json_file(result_path)
        if result_data and "logs" in result_data and isinstance(result_data["logs"], list):
            logs = result_data["logs"]

        # If no logs in result, check for a dedicated logs file
        if not logs:
            logs_path = get_version_dir(project_id, version) / "execution_logs.json"
            logs_data = read_json_file(logs_path)
            if logs_data and isinstance(logs_data, list):
                logs = logs_data

        # For failed executions with no logs, synthesize a failure entry
        if execution.status in ("error", "failed"):
            if not logs:
                logs = [{"timestamp": int(execution.created_at.timestamp() * 1000) if execution.created_at else None,
                         "message": "Pipeline started."}]
            logs.append({
                "timestamp": int(execution.created_at.timestamp() * 1000) if execution.created_at else None,
                "message": f"Pipeline failed: {execution.error_message or 'Unknown error'}",
                "type": "error",
            })

        return jsonify(logs), 200
    finally:
        session.close()


@app.route("/api/projects/<int:project_id>/iterate", methods=["POST"])
def iterate_project(project_id: int):
    state = get_project_state(project_id)

    if state["running"]:
        return jsonify({"error": "A pipeline is already running for this project"}), 409

    user_id = get_optional_request_user_id()
    session = get_session()
    try:
        # Accept either JSON or multipart/form-data (for file uploads)
        if request.content_type and "multipart/form-data" in request.content_type:
            data = {"prompt": request.form.get("prompt", "").strip()}
            ph = request.form.get("prompt_history")
            if ph:
                try:
                    data["prompt_history"] = json.loads(ph)
                except Exception:
                    data["prompt_history"] = []
            nlu_payload = request.form.get("nlu_result")
            if nlu_payload:
                try:
                    data["nlu_result"] = json.loads(nlu_payload)
                except Exception:
                    data["nlu_result"] = nlu_payload
        else:
            data = request.get_json()

        if not data or not data.get("prompt"):
            return jsonify({"error": "prompt is required"}), 400

        project = session.get(Project, project_id)
        if not project:
            return jsonify({"error": f"Project {project_id} not found"}), 404
        access_error = get_project_access_error(project, user_id)
        if access_error:
            return access_error

        prompt = data["prompt"]
        prompt_history = data.get("prompt_history", [])
        if not prompt_history:
            prompt_history = [{"role": "user", "content": prompt}]
        provided_nlu_result = data.get("nlu_result")
        if isinstance(provided_nlu_result, str):
            try:
                provided_nlu_result = json.loads(provided_nlu_result)
            except Exception:
                provided_nlu_result = None
        if isinstance(provided_nlu_result, dict):
            nlu_result = provided_nlu_result
            print("[NLU] Using provided analysis from /chat")
            print(f"[NLU] Full analysis: {nlu_result}")
        else:
            nlu_result = nlu_agent.analyze(prompt)
            print(f"[NLU] Full analysis: {nlu_result}")

        requested_archetype = detect_requested_archetype(prompt)
        if (
            project.locked_ui_archetype
            and requested_archetype
            and requested_archetype != project.locked_ui_archetype
        ):
            return jsonify({
                "response_type": "chat",
                "message": (
                    f"That would change the app type from {project.locked_ui_archetype} to "
                    f"{requested_archetype}. To switch app types, please start a new project."
                ),
            }), 200

        current_head = (
            session.query(Execution)
            .filter(
                Execution.project_id == project_id,
                Execution.is_active_head == True,
            )
            .first()
        )

        if current_head:
            current_head.is_active_head = False
            session.commit()

        next_version = get_next_version(session, project_id)
        execution = Execution(
            project_id=project_id,
            owner_id=project.owner_id,
            status="pending",
            version=next_version,
            prompt_history=json.dumps(prompt_history),
            is_active_head=True,
            parent_execution_id=current_head.id if current_head else None,
        )
        session.add(execution)

        project.status = "in_progress"
        project.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(execution)

        # Immediately persist the user message to chat_messages
        existing_msgs = []
        if execution.chat_messages:
            try:
                existing_msgs = json.loads(execution.chat_messages)
            except Exception:
                existing_msgs = []
        existing_msgs.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        execution.chat_messages = json.dumps(existing_msgs)
        session.commit()

        state["running"] = True
        state["started_at"] = time.time()
        state["current_execution_id"] = execution.id
        state["logs"] = []
        state["result_ready"] = False

        # Save uploaded reference images (if any)
        reference_images = []
        uploaded_files = request.files.getlist("reference_images") if request.content_type and "multipart/form-data" in request.content_type else []
        if uploaded_files:
            refs_dir = get_version_dir(project_id, next_version) / "references"
            refs_dir.mkdir(parents=True, exist_ok=True)
            for f in uploaded_files:
                if f.filename:
                    safe_name = Path(f.filename).name
                    dest = refs_dir / safe_name
                    f.save(str(dest))
                    reference_images.append(str(dest.resolve()))
            if reference_images:
                print(f"Saved {len(reference_images)} reference image(s) for project {project_id} v{next_version}")

        print(f"Starting iteration v{next_version} for project {project_id}: {prompt}")
        thread = threading.Thread(
            target=run_full_pipeline_async,
            args=(prompt, prompt_history, project_id, reference_images, nlu_result),
            daemon=True,
        )
        thread.start()

        return jsonify({
            "status": "started",
            "project_id": project_id,
            "execution_id": execution.id,
            "version": next_version,
        }), 200

    except Exception as e:
        state["running"] = False
        print(f"Error in iterate_project: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/executions/<int:execution_id>/restore", methods=["POST"])
def restore_execution(execution_id: int):
    session = get_session()
    try:
        execution = session.get(Execution, execution_id)
        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        project_id = execution.project_id

        session.query(Execution).filter(
            Execution.project_id == project_id
        ).update({"is_active_head": False})

        execution.is_active_head = True

        project = session.get(Project, project_id)
        if project:
            project.updated_at = datetime.now(timezone.utc)

        session.commit()

        return jsonify({
            "message": f"Restored to version {execution.version}",
            "project_id": project_id,
            "execution_id": execution_id,
            "version": execution.version,
            "is_active_head": True,
        }), 200

    except Exception as e:
        session.rollback()
        print(f"Error in restore_execution: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# ============================================================================
# EXECUTION ENDPOINTS
# ============================================================================

@app.route("/api/execute-task", methods=["POST"])
def execute_task():
    project_id = None
    user_id = get_optional_request_user_id()
    session = get_session()
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({"error": "No JSON payload provided"}), 400

        project_id = req_data.get("project_id")

        if not project_id:
            project = Project(name="Untitled Project", description="", status="in_progress", owner_id=user_id)
            session.add(project)
            session.commit()
            session.refresh(project)
            project_id = project.id
        else:
            project = session.get(Project, project_id)
            if not project:
                return jsonify({"error": f"Project {project_id} not found"}), 404
            access_error = get_project_access_error(project, user_id)
            if access_error:
                return access_error
            project.status = "in_progress"
            project.updated_at = datetime.now(timezone.utc)
            session.commit()

        next_version = get_next_version(session, project_id)
        task_description = project.description or project.name
        nlu_result = nlu_agent.analyze(task_description)
        print(f"[NLU] Full analysis: {nlu_result}")
        requested_archetype = detect_requested_archetype(task_description)
        if (
            project.locked_ui_archetype
            and requested_archetype
            and requested_archetype != project.locked_ui_archetype
        ):
            return jsonify({
                "response_type": "chat",
                "message": (
                    f"That would change the app type from {project.locked_ui_archetype} to "
                    f"{requested_archetype}. To switch app types, please start a new project."
                ),
            }), 200
        initial_history = [{"role": "user", "content": task_description}]

        execution = Execution(
            project_id=project_id,
            owner_id=project.owner_id,
            status="pending",
            version=next_version,
            prompt_history=json.dumps(initial_history),
            is_active_head=True,
            parent_execution_id=None,
        )
        session.add(execution)
        session.commit()
        session.refresh(execution)

        state = get_project_state(project_id)
        state["running"] = True
        state["started_at"] = time.time()
        state["current_execution_id"] = execution.id
        state["logs"] = []
        state["result_ready"] = False

        print(f"Starting v{next_version} for project {project_id}: {task_description}")
        thread = threading.Thread(
            target=run_full_pipeline_async,
            args=(task_description, initial_history, project_id, None, nlu_result),
            daemon=True,
        )
        thread.start()

        return jsonify({
            "status": "started",
            "project_id": project_id,
            "execution_id": execution.id,
            "version": next_version,
        }), 200

    except Exception as e:
        if project_id:
            get_project_state(project_id)["running"] = False
        print(f"Error in execute_task: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/execution-status", methods=["GET"])
def execution_status():
    project_id = request.args.get("project_id", type=int)

    # No project_id = return idle (prevents cross-user status leaking)
    if not project_id:
        return jsonify({
            "status": "IDLE",
            "currentStage": "pm",
            "logs": [],
            "engineerTasks": [],
            "project_id": None,
            "execution_id": None,
        }), 200

    state = get_project_state(project_id)
    version = None
    execution_id = state.get("current_execution_id")
    project = None

    if execution_id:
        session = get_session()
        try:
            execution = session.get(Execution, execution_id)
            if execution:
                version = execution.version
                project = session.get(Project, execution.project_id)
                # 7C.2: DB is ground truth when pipeline not actively running
                if not state["running"] and execution.status in ("success", "error"):
                    db_status = "COMPLETED" if execution.status == "success" else "FAILED"
                    return jsonify({
                        "status": db_status,
                        "currentStage": "engineer",
                        "logs": state.get("logs", []),
                        "engineerTasks": [],
                        "locked_ui_archetype": project.locked_ui_archetype if project else None,
                        "project_id": project_id,
                        "execution_id": execution_id,
                    }), 200
                # Crash recovery: in-memory says RUNNING but DB was cleaned up on restart
                if state["running"] and execution.status in ("failed", "error"):
                    return jsonify({
                        "status": "FAILED",
                        "currentStage": "engineer",
                        "logs": state.get("logs", []),
                        "engineerTasks": [],
                        "locked_ui_archetype": project.locked_ui_archetype if project else None,
                        "project_id": project_id,
                        "execution_id": execution_id,
                    }), 200
        finally:
            session.close()

    result_file = None
    if project_id and version:
        result_file = get_version_dir(project_id, version) / "last_execution_result.json"

    data = read_json_file(result_file) if result_file else None

    STATUS_MAP = {
        "success": "COMPLETED", "error": "FAILED",
        "completed": "COMPLETED", "failed": "FAILED",
        "pending": "RUNNING", "running": "RUNNING",
    }

    logs = state.get("logs", [])
    current_stage = "pm"
    for log in reversed(logs):
        msg = log.get("message", "")
        if "Loading previous version" in msg:
            continue  # setup log, not a stage transition
        if "Build Agent" in msg:
            current_stage = "engineer"
            break
        if "Architecture Agent" in msg:
            current_stage = "planner"
            break

    if data is not None and state.get("result_ready", True):
        raw_status = str(data.get("status", "success")).lower()
        frontend_status = STATUS_MAP.get(raw_status, "COMPLETED")
        return jsonify({
            "status": frontend_status,
            "currentStage": "engineer",
            "logs": logs,
            "engineerTasks": [],
            "locked_ui_archetype": project.locked_ui_archetype if project else None,
            "project_id": project_id,
            "execution_id": execution_id,
        }), 200

    if state["running"]:
        return jsonify({
            "status": "RUNNING",
            "currentStage": current_stage,
            "logs": logs,
            "engineerTasks": [],
            "locked_ui_archetype": project.locked_ui_archetype if project else None,
            "project_id": project_id,
            "execution_id": execution_id,
        }), 200

    return jsonify({
        "status": "FAILED",
        "currentStage": "complete",
        "logs": logs,
        "engineerTasks": [],
        "locked_ui_archetype": project.locked_ui_archetype if project else None,
        "project_id": project_id,
        "execution_id": execution_id,
    }), 200


@app.route("/api/code", methods=["GET"])
def get_code():
    """
    Returns the execution result / code artifact. Survives backend restarts via query params.
    Priority: in-memory state -> ?project_id&version -> DB active head
    """
    project_id, version = resolve_project_version(
        request.args.get("project_id"),
        request.args.get("version"),
    )

    if project_id and version:
        result_file = get_version_dir(project_id, version) / "last_execution_result.json"
        data = read_json_file(result_file)
        if data:
            return jsonify(data), 200

    return jsonify({"error": "No execution result available"}), 404


@app.route("/api/plan", methods=["GET"])
def get_plan():
    """
    Returns the build plan. Survives backend restarts via query params.
    Priority: in-memory state -> ?project_id&version -> DB active head
    """
    project_id, version = resolve_project_version(
        request.args.get("project_id"),
        request.args.get("version"),
    )

    if project_id and version:
        plan_file = get_version_dir(project_id, version) / "last_plan.json"
        data = read_json_file(plan_file)
        if data:
            return jsonify(data), 200

    return jsonify({"error": "Plan not found"}), 404


@app.route("/api/prd", methods=["GET"])
def get_prd():
    """
    Returns the PRD/Brief. Survives backend restarts via query params.
    Priority: in-memory state -> ?project_id&version -> DB active head
    """
    project_id, version = resolve_project_version(
        request.args.get("project_id"),
        request.args.get("version"),
    )

    if project_id and version:
        prd_file = get_version_dir(project_id, version) / "last_prd.json"
        data = read_json_file(prd_file)
        if data:
            return jsonify(data), 200

    return jsonify({"error": "PRD not found"}), 404


# ============================================================================
# FILE TREE ENDPOINT (Phase 7B.5)
# ============================================================================

@app.route("/api/projects/<int:project_id>/versions/<int:version>/files", methods=["GET"])
def get_version_files(project_id: int, version: int):
    code_dir = get_version_dir(project_id, version) / "code"

    file_path = request.args.get("path")
    if file_path:
        target = code_dir / file_path
        try:
            target.resolve().relative_to(code_dir.resolve())
        except ValueError:
            return jsonify({"error": "Invalid path"}), 400
        if not target.exists() or not target.is_file():
            return jsonify({"error": "File not found"}), 404
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            language = get_language_from_ext(target.name)
            return jsonify({"path": file_path, "content": content, "language": language}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if not code_dir.exists():
        return jsonify({"tree": [], "message": "No files generated yet"}), 200

    tree = build_file_tree(code_dir, code_dir)
    return jsonify({"tree": tree, "code_dir": str(code_dir)}), 200


# ============================================================================
# PREVIEW ENDPOINT (Phase 7B.2)
# ============================================================================

PREVIEW_PLACEHOLDER = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Preview</title>
  <style>
    body {
      margin: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      background: #f5f5f5;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #999;
    }
    .msg { text-align: center; }
    .msg p { margin: 8px 0; font-size: 14px; }
  </style>
</head>
<body>
  <div class="msg">
    <p>Live preview will appear here</p>
    <p>when your build is complete</p>
  </div>
</body>
</html>"""


@app.route("/api/preview/<int:project_id>/<int:version>", methods=["GET"])
def get_preview(project_id: int, version: int):
    code_dir = get_version_dir(project_id, version) / "code"
    target, scaffold_mode = get_preview_target(project_id, version)

    if target:
        html = target.read_text(encoding="utf-8", errors="replace")
        if scaffold_mode == "legacy_single_page":
            src_dir = target.parent
            if src_dir.exists():
                for css_path in sorted(src_dir.glob("*.css")):
                    css = css_path.read_text(encoding="utf-8", errors="replace")
                    link_tag = f'<link rel="stylesheet" href="./{css_path.name}">'
                    if link_tag in html:
                        html = html.replace(link_tag, f"<style>{css}</style>")
                    elif "</head>" in html:
                        html = html.replace("</head>", f"<style>{css}</style>\n</head>")
                for js_path in sorted(src_dir.glob("*.js")):
                    js = js_path.read_text(encoding="utf-8", errors="replace")
                    script_tag = f'<script src="./{js_path.name}">'
                    if script_tag in html:
                        html = html.replace(f'{script_tag}</script>', f"<script>{js}</script>")
                    elif "</body>" in html:
                        html = html.replace("</body>", f"<script>{js}</script>\n</body>")
        else:
            mount_prefix = f"/api/preview-files/{project_id}/{version}"
            html = rewrite_preview_file_references(
                html,
                mount_prefix=mount_prefix,
                root_dir=relative_mount_root(code_dir, target),
            )
            html = inject_preview_base_href(
                html,
                mount_prefix=mount_prefix,
                root_dir=relative_mount_root(code_dir, target),
            )
        # Normalize local asset paths so preview can always resolve them through the backend.
        html = re.sub(
            r'((?:src|href)=["\'])(?:\./|\.\./)?assets/([^"\']+)(["\'])',
            rf'\1/api/assets/{project_id}/{version}/\2\3',
            html,
            flags=re.IGNORECASE,
        )
        html = re.sub(
            r'(url\(["\']?)(?:\./|\.\./)?assets/([^)"\']+)(["\']?\))',
            rf'\1/api/assets/{project_id}/{version}/\2\3',
            html,
            flags=re.IGNORECASE,
        )
        return Response(html, mimetype="text/html")

    return Response(PREVIEW_PLACEHOLDER, mimetype="text/html", status=200)


@app.route("/api/preview-files/<int:project_id>/<int:version>/<path:asset_path>", methods=["GET"])
def get_preview_file(project_id: int, version: int, asset_path: str):
    target = resolve_version_file(project_id, version, asset_path)
    if not target:
        return jsonify({"error": "Preview asset not found"}), 404

    guessed_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
    suffix = target.suffix.lower()
    if suffix in {".js", ".mjs", ".css"}:
        preview_target, scaffold_mode = get_preview_target(project_id, version)
        if scaffold_mode == "componentized_app":
            mount_prefix = f"/api/preview-files/{project_id}/{version}"
            preview_root = (
                relative_mount_root(get_version_dir(project_id, version) / "code", preview_target)
                if preview_target is not None
                else Path(asset_path).parts[0] if Path(asset_path).parts else ""
            )
            try:
                content = target.read_text(encoding="utf-8", errors="replace")
            except OSError:
                content = ""
            if content:
                content = rewrite_preview_runtime_asset_references(
                    content,
                    mount_prefix=mount_prefix,
                    root_dir=preview_root,
                )
                return Response(content, mimetype=guessed_type)

    return send_file(target, mimetype=guessed_type)


@app.route("/api/projects/<int:project_id>/versions/<int:version>/debug-files", methods=["GET"])
def debug_version_files(project_id: int, version: int):
    version_dir = get_version_dir(project_id, version)
    result = {}
    for subdir in ["code", "assets"]:
        d = version_dir / subdir
        result[subdir] = {"exists": d.exists(), "files": []}
        if d.exists():
            for f in sorted(d.rglob("*")):
                if f.is_file():
                    result[subdir]["files"].append({
                        "path": str(f.relative_to(d)).replace("\\", "/"),
                        "size": f.stat().st_size
                    })
    return jsonify({
        "version_dir": str(version_dir),
        "exists": version_dir.exists(),
        "subdirs": result
    }), 200


@app.route("/api/projects/<int:project_id>/head", methods=["GET"])
def get_project_head(project_id: int):
    """Returns the active head execution for a project."""
    session = get_session()
    try:
        head = (
            session.query(Execution)
            .filter(
                Execution.project_id == project_id,
                Execution.is_active_head == True,
            )
            .first()
        )
        if not head:
            # Fallback: latest version
            head = (
                session.query(Execution)
                .filter(Execution.project_id == project_id)
                .order_by(Execution.version.desc())
                .first()
            )
        if not head:
            return jsonify({"error": "No executions found"}), 404
        return jsonify({"project_id": project_id, "version": head.version, "execution_id": head.id}), 200
    finally:
        session.close()
@app.route("/api/credits/balance", methods=["GET"])
def get_credits_balance():
    plan_credits = 500  # Pro plan (pre-auth mock)
    from sqlalchemy import func
    session = get_session()
    try:
        used = session.query(func.sum(Execution.credits_used)).filter(
            Execution.credits_used.isnot(None)
        ).scalar() or 0
        balance = max(0, plan_credits - int(used))
        return jsonify({
            "plan": "Pro",
            "plan_credits": plan_credits,
            "credits_used": int(used),
            "credits_remaining": balance
        })
    finally:
        session.close()


@app.route("/api/projects/<int:project_id>/versions/<int:version>/factsheet", methods=["GET"])
def get_factsheet(project_id: int, version: int):
    """Returns the AI Factsheet for a specific version."""
    factsheet_path = get_version_dir(project_id, version) / "last_factsheet.json"
    data = read_json_file(factsheet_path)
    if data:
        return jsonify(data), 200
    session = get_session()
    try:
        execution = (
            session.query(Execution)
            .filter(Execution.project_id == project_id, Execution.version == version)
            .first()
        )
        if execution and execution.governance_log:
            return jsonify(json.loads(execution.governance_log)), 200
        return jsonify({"error": "Factsheet not available for this version"}), 404
    finally:
        session.close()


@app.route("/api/projects/<int:project_id>/versions/<int:version>/insights", methods=["GET"])
def get_insights(project_id: int, version: int):
    """Return Build Insights (prompt coaching suggestions) for a specific version."""
    get_optional_request_user_id()  # optional auth — guests can read insights
    insights_path = get_version_dir(project_id, version) / "last_insights.json"
    data = read_json_file(insights_path)
    if data:
        return jsonify(data), 200
    return jsonify({"insights": []}), 200


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


def _resolve_asset_path(project_id: int, version: int, filename: str) -> Path | None:
    filename_path = Path(filename)
    if any(part == ".." for part in filename_path.parts):
        return None

    version_dir = get_version_dir(project_id, version)
    candidates = [
        version_dir / "assets" / filename_path,
        version_dir / "code" / "src" / "assets" / filename_path,
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    # Reused design assets may point to a previous version via local_path.
    manifest = read_json_file(version_dir / "last_design_assets.json") or {}
    target_name = filename_path.name
    for asset in manifest.get("assets", []):
        local_path_raw = asset.get("local_path")
        if not local_path_raw:
            continue
        local_path = Path(local_path_raw)
        key = str(asset.get("key", "")).strip()
        expected_name = f"{key}.png" if key else ""
        if target_name not in {local_path.name, expected_name}:
            continue
        if local_path.exists() and local_path.is_file():
            return local_path

    # Last resort: check older versions for the same relative path.
    for prior_version in range(version - 1, 0, -1):
        prior_dir = get_version_dir(project_id, prior_version)
        prior_candidates = [
            prior_dir / "assets" / filename_path,
            prior_dir / "code" / "src" / "assets" / filename_path,
        ]
        for candidate in prior_candidates:
            if candidate.exists() and candidate.is_file():
                return candidate
    return None


@app.route("/api/assets/<int:project_id>/<int:version>/<path:filename>", methods=["GET"])
def get_asset(project_id: int, version: int, filename: str):
    asset_path = _resolve_asset_path(project_id, version, filename)
    if not asset_path:
        return jsonify({"error": "Asset not found"}), 404
    guessed_mime, _ = mimetypes.guess_type(asset_path.name)
    return send_file(asset_path, mimetype=guessed_mime or "application/octet-stream")


@app.route("/api/projects/<int:project_id>/chat", methods=["POST"])
def project_chat(project_id: int):
    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "message is required"}), 400
    user_id = get_optional_request_user_id()
    try:
        requested_archetype = detect_requested_archetype(data["message"])
        # Load PRD from active head version for context-aware replies
        project_context = None
        db = get_session()
        try:
            project = db.get(Project, project_id)
            if not project:
                return jsonify({"error": "Project not found"}), 404
            access_error = get_project_access_error(project, user_id)
            if access_error:
                return access_error
            if (
                project.locked_ui_archetype
                and requested_archetype
                and requested_archetype != project.locked_ui_archetype
            ):
                return jsonify({
                    "response_type": "chat",
                    "message": (
                        f"That would change the app type from {project.locked_ui_archetype} to "
                        f"{requested_archetype}. To switch app types, please start a new project."
                    ),
                }), 200

            head = (
                db.query(Execution)
                .filter(Execution.project_id == project_id, Execution.is_active_head == True)
                .first()
            )
            # Immediately persist the user message to chat_messages
            if head:
                existing_msgs = []
                if head.chat_messages:
                    try:
                        existing_msgs = json.loads(head.chat_messages)
                    except Exception:
                        existing_msgs = []
                existing_msgs.append({
                    "role": "user",
                    "content": data["message"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                head.chat_messages = json.dumps(existing_msgs)
                db.commit()

            if head:
                prd_path = get_version_dir(project_id, head.version) / "last_prd.json"
                prd_data = read_json_file(prd_path)
                if prd_data:
                    prd = prd_data.get("prd", prd_data)
                    title = prd.get("document_title", "Unknown")
                    overview = prd.get("overview", "")
                    features = ", ".join(prd.get("core_features_mvp", []))
                    stack = ", ".join(prd.get("technical_stack_recommendation", []))
                    detected_intent = prd.get("detected_intent", "")
                    visual_direction = prd.get("visual_direction", "")
                    project_context = (
                        f"Project: {title}\n"
                        f"Intent: {detected_intent}\n"
                        f"Visual direction: {visual_direction}\n"
                        f"Overview: {overview}\n"
                        f"Features: {features}\n"
                        f"Stack: {stack}"
                    )
        finally:
            db.close()

        sys.path.insert(0, str(REPO_ROOT))

        # NLU pre-analysis — frustrated sentiment short-circuits to chat
        nlu_result = nlu_agent.analyze(data["message"])
        print(f"[NLU] Full analysis: {nlu_result}")
        print(f"[NLU] sentiment={nlu_result['sentiment']} score={nlu_result['sentiment_score']:.2f} domain={nlu_result['domain']} keywords={nlu_result['keywords']}")
        if nlu_result["frustrated"]:
            print("[NLU] Frustrated sentiment — routing to chat")
            return jsonify({
                "response_type": "chat",
                "message": "I can see you're frustrated — let's work through this. What would you like to change or fix?"
            }), 200

        # Append NLU context to project context for better classify_intent routing
        entity_terms = ", ".join(
            f"{e.get('text', '')} ({e.get('type', 'Unknown')})"
            for e in nlu_result.get("entities", [])
            if e.get("text")
        )
        nlu_context_str = (
            "\nNLU Analysis: "
            f"keywords=[{', '.join(nlu_result.get('keywords', []))}], "
            f"concepts=[{', '.join(nlu_result.get('concepts', []))}], "
            f"entities=[{entity_terms}], "
            f"prompt_richness={nlu_result.get('prompt_richness', 'sparse')}"
        )
        project_context = (project_context or "") + nlu_context_str

        from agents.pm_agent import PMAgent
        pm = PMAgent()
        intent = pm.classify_intent(data["message"], project_context=project_context)
        if intent.get("type") == "chat":
            return jsonify({"response_type": "chat", "message": intent["message"]}), 200
        return jsonify({"response_type": "build", "nlu_result": nlu_result}), 200
    except Exception as e:
        print(f"Chat classify error: {e}")
        return jsonify({
            "response_type": "chat",
            "message": "I'm having trouble connecting right now. Could you rephrase that or try again?"
        }), 200



# ============================================================================
# CHAT HISTORY ENDPOINTS (Phase 16.1)
# ============================================================================

@app.route("/api/projects/<int:project_id>/chat-history", methods=["GET"])
def get_chat_history(project_id: int):
    """Returns saved chat messages for the active head execution."""
    db = get_session()
    try:
        head = (
            db.query(Execution)
            .filter(Execution.project_id == project_id, Execution.is_active_head == True)
            .first()
        )
        if not head:
            head = (
                db.query(Execution)
                .filter(Execution.project_id == project_id)
                .order_by(Execution.id.desc())
                .first()
            )
        if not head or not head.chat_messages:
            return jsonify([]), 200
        try:
            messages = json.loads(head.chat_messages)
        except Exception:
            messages = []
        return jsonify(messages), 200
    finally:
        db.close()


@app.route("/api/projects/<int:project_id>/chat-messages", methods=["POST"])
def save_chat_messages(project_id: int):
    """Saves full chat message array to the active head execution."""
    data = request.get_json()
    if not data or "messages" not in data:
        return jsonify({"error": "messages array required"}), 400
    db = get_session()
    try:
        head = (
            db.query(Execution)
            .filter(Execution.project_id == project_id, Execution.is_active_head == True)
            .first()
        )
        if not head:
            head = (
                db.query(Execution)
                .filter(Execution.project_id == project_id)
                .order_by(Execution.id.desc())
                .first()
            )
        if not head:
            return jsonify({"error": "No execution found for this project"}), 404
        head.chat_messages = json.dumps(data["messages"])
        db.commit()
        return jsonify({"saved": len(data["messages"])}), 200
    finally:
        db.close()


# ============================================================================
# PUBLISH ENDPOINTS (Phase 8.1)
# ============================================================================

import random, string, shutil

def generate_slug(project_name: str, version: int) -> str:
    safe = "".join(c if c.isalnum() else "-" for c in project_name.lower()).strip("-")
    safe = "-".join(p for p in safe.split("-") if p)[:30]
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{safe}-v{version}-{suffix}"


@app.route("/api/projects/<int:project_id>/versions/<int:version>/publish", methods=["POST"])
def publish_version(project_id: int, version: int):
    session = get_session()
    try:
        execution = (
            session.query(Execution)
            .filter(Execution.project_id == project_id, Execution.version == version)
            .first()
        )
        if not execution:
            return jsonify({"error": "Version not found"}), 404

        if execution.published_slug:
            slug = execution.published_slug
        else:
            project = session.get(Project, project_id)
            slug = generate_slug(project.name if project else "app", version)

            code_dir = get_version_dir(project_id, version) / "code"
            if not code_dir.exists():
                return jsonify({"error": "No code generated for this version"}), 404

            published_dir = REPO_ROOT / "published" / slug
            published_dir.mkdir(parents=True, exist_ok=True)
            plan_data = get_plan_data_for_version(project_id, version)
            if is_componentized_workspace(code_dir, plan_data=plan_data):
                build_componentized_version(get_version_dir(project_id, version))
                dist_dir = code_dir / "dist"
                if dist_dir.exists():
                    shutil.copytree(dist_dir, published_dir, dirs_exist_ok=True)
                else:
                    return jsonify({"error": "Componentized app build is not ready for publishing"}), 409
            else:
                shutil.copytree(code_dir, published_dir, dirs_exist_ok=True)

            execution.published_slug = slug
            session.commit()

        return jsonify({"url": f"/published/{slug}", "slug": slug}), 200
    except Exception as e:
        print(f"Publish error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/published/<slug>", methods=["GET"])
def serve_published(slug: str):
    if not all(c.isalnum() or c in "-_" for c in slug):
        return "Invalid slug", 400

    published_dir = REPO_ROOT / "published" / slug
    html_file = published_dir / "index.html"

    if not html_file.exists():
        src_html_file = published_dir / "src" / "index.html"
        if src_html_file.exists():
            html_file = src_html_file
        else:
            html_files = list(published_dir.rglob("*.html"))
            html_file = html_files[0] if html_files else None

    if not html_file:
        return "Published app not found", 404

    html = Path(html_file).read_text(encoding="utf-8", errors="replace")
    src_dir = Path(html_file).parent
    if src_dir.name == "src":
        for css_path in sorted(src_dir.glob("*.css")):
            css = css_path.read_text(encoding="utf-8", errors="replace")
            link_tag = f'<link rel="stylesheet" href="./{css_path.name}">'
            if link_tag in html:
                html = html.replace(link_tag, f"<style>{css}</style>")
            elif "</head>" in html:
                html = html.replace("</head>", f"<style>{css}</style>\n</head>")
        for js_path in sorted(src_dir.glob("*.js")):
            js = js_path.read_text(encoding="utf-8", errors="replace")
            script_tag = f'<script src="./{js_path.name}">'
            if script_tag in html:
                html = html.replace(f'{script_tag}</script>', f"<script>{js}</script>")
            elif "</body>" in html:
                html = html.replace("</body>", f"<script>{js}</script>\n</body>")
    html = rewrite_preview_file_references(
        html,
        mount_prefix=f"/published/{slug}",
        root_dir=relative_mount_root(published_dir, Path(html_file)),
    )
    return Response(html, mimetype="text/html")


@app.route("/published/<slug>/<path:asset_path>", methods=["GET"])
def serve_published_file(slug: str, asset_path: str):
    if not all(c.isalnum() or c in "-_" for c in slug):
        return "Invalid slug", 400

    published_dir = (REPO_ROOT / "published" / slug).resolve()
    target = (published_dir / asset_path).resolve()
    try:
        target.relative_to(published_dir)
    except ValueError:
        return "Invalid asset path", 400

    if not target.exists() or not target.is_file():
        return "Published asset not found", 404

    guessed_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
    return send_file(target, mimetype=guessed_type)




# ============================================================================
# WATSON SPEECH TO TEXT ENDPOINT (Phase 10.1)
# ============================================================================

@app.route("/api/watson/stt", methods=["POST"])
def watson_stt():
    """Accepts audio upload, calls IBM Watson STT, returns transcript."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    watson_url = os.getenv("WATSON_STT_URL")
    watson_key = os.getenv("WATSON_STT_API_KEY")

    if not watson_url or not watson_key:
        return jsonify({"error": "Watson STT credentials not configured"}), 500

    try:
        from ibm_watson import SpeechToTextV1
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

        authenticator = IAMAuthenticator(watson_key)
        stt = SpeechToTextV1(authenticator=authenticator)
        stt.set_service_url(watson_url)

        audio_bytes = audio_file.read()
        content_type = audio_file.content_type or "audio/webm"

        result = stt.recognize(
            audio=audio_bytes,
            content_type=content_type,
            model="en-US_BroadbandModel",
        ).get_result()

        results = result.get("results", [])
        if not results:
            return jsonify({"transcript": ""}), 200

        transcript = " ".join(
            r["alternatives"][0]["transcript"]
            for r in results
            if r.get("alternatives")
        ).strip()

        return jsonify({"transcript": transcript}), 200

    except Exception as e:
        print(f"Watson STT error: {e}")
        return jsonify({"error": str(e)}), 500



# ============================================================================
# DOWNLOAD ENDPOINT (zip code folder)
# ============================================================================

@app.route("/api/projects/<int:project_id>/versions/<int:version>/download", methods=["GET"])
def download_version(project_id: int, version: int):
    import zipfile, io
    code_dir = get_version_dir(project_id, version) / "code"
    if not code_dir.exists():
        return jsonify({"error": "No code found for this version"}), 404

    assets_dir = get_version_dir(project_id, version) / "assets"

    import re as _re

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in code_dir.rglob("*"):
            if file_path.is_file():
                if file_path.suffix.lower() in (".html", ".css"):
                    raw = file_path.read_text(encoding="utf-8", errors="replace")
                    fixed = _re.sub(
                        r"/api/assets/[0-9]+/[0-9]+/([^ \"\'>]+)",
                        r"../assets/\1",
                        raw
                    )
                    zf.writestr(str(file_path.relative_to(code_dir)).replace("\\", "/"), fixed)
                else:
                    zf.write(file_path, file_path.relative_to(code_dir))
        if assets_dir.exists():
            for file_path in assets_dir.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, Path("assets") / file_path.relative_to(assets_dir))
    buf.seek(0)

    filename = f"project-{project_id}-v{version}.zip"
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=filename)
# ============================================================================
# WATSON TEXT TO SPEECH ENDPOINT (Phase 10.2)
# ============================================================================

@app.route("/api/watson/tts", methods=["POST"])
def watson_tts():
    """Accepts JSON text, calls IBM Watson TTS, returns audio/mp3."""
    data = request.get_json()
    if not data or not data.get("text"):
        return jsonify({"error": "No text provided"}), 400
    watson_url = os.getenv("WATSON_TTS_URL")
    watson_key = os.getenv("WATSON_TTS_API_KEY")
    if not watson_url or not watson_key:
        return jsonify({"error": "Watson TTS credentials not configured"}), 500
    try:
        from ibm_watson import TextToSpeechV1
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
        authenticator = IAMAuthenticator(watson_key)
        tts = TextToSpeechV1(authenticator=authenticator)
        tts.set_service_url(watson_url)
        response = tts.synthesize(
            text=data["text"],
            voice="en-US_EmilyV3Voice",
            accept="audio/mp3",
        ).get_result()
        audio_bytes = response.content
        return Response(audio_bytes, mimetype="audio/mp3")
    except Exception as e:
        print(f"Watson TTS error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/dashboard/stats", methods=["GET"])
@jwt_required()
def dashboard_stats():
    """Return average governance scores for the logged-in user's builds."""
    uid = get_jwt_identity()
    session = get_session()
    try:
        q = session.query(Execution)
        q = q.join(Project).filter(Project.owner_id == int(uid))
        executions = q.all()
        prompt_scores = []
        build_scores = []

        for ex in executions:
            if not ex.governance_log:
                continue
            try:
                factsheet = json.loads(ex.governance_log)
                scoring = factsheet.get("scoring", {})
                ps = scoring.get("prompt_quality", {}).get("score")
                bs = scoring.get("build_confidence", {}).get("score")
                if ps is not None:
                    prompt_scores.append(ps)
                if bs is not None:
                    build_scores.append(bs)
            except Exception:
                continue

        avg_prompt = round(sum(prompt_scores) / len(prompt_scores)) if prompt_scores else None
        avg_build = round(sum(build_scores) / len(build_scores)) if build_scores else None

        return jsonify({
            "avg_prompt_score": avg_prompt,
            "avg_build_score": avg_build,
            "scored_builds": len(prompt_scores),
        })
    finally:
        session.close()


@app.route("/api/projects/<int:project_id>/versions/<int:version>/factsheet/pdf", methods=["GET"])
def download_factsheet_pdf(project_id: int, version: int):
    """Generate enterprise-style PDF using WeasyPrint HTML renderer."""
    import io
    from datetime import datetime as _dt
    from weasyprint import HTML, CSS

    pdf_type = request.args.get("type", "internal")

    # Load factsheet
    factsheet_path = get_version_dir(project_id, version) / "last_factsheet.json"
    factsheet = read_json_file(factsheet_path)
    if not factsheet:
        session = get_session()
        try:
            execution = session.query(Execution).filter(
                Execution.project_id == project_id, Execution.version == version
            ).first()
            if execution and execution.governance_log:
                factsheet = json.loads(execution.governance_log)
        finally:
            session.close()
    if not factsheet:
        return jsonify({"error": "Factsheet not available"}), 404

    prd_data  = read_json_file(get_version_dir(project_id, version) / "last_prd.json")
    plan_data = read_json_file(get_version_dir(project_id, version) / "last_plan.json")

    # Extract data
    proj         = factsheet.get("project", {})
    project_name = proj.get("name", "Project")
    ver          = proj.get("version", version)
    gen_at       = factsheet.get("generated_at", "")
    pipeline     = factsheet.get("pipeline", {})
    model_reg    = factsheet.get("model_registry", [])
    usage        = factsheet.get("usage", {})
    outputs      = factsheet.get("outputs", {})
    scoring      = factsheet.get("scoring", {})
    compliance   = factsheet.get("compliance", {})
    human_review = compliance.get("human_review_required", False)
    archetype    = (pipeline.get("ui_archetype") or "Auto-detected").capitalize()
    prd          = (prd_data.get("prd", prd_data) if prd_data else {}) or {}
    milestones   = (plan_data.get("milestones", []) if plan_data else []) or []

    ts = ""
    if gen_at:
        try:
            ts = _dt.fromisoformat(gen_at.replace("Z","")).strftime("%B %d, %Y")
        except Exception:
            ts = gen_at

    pq = scoring.get("prompt_quality", {}) or {}
    bc = scoring.get("build_confidence", {}) or {}
    pq_score = pq.get("score")
    bc_score = bc.get("score")
    pq_label = (pq.get("label") or "").capitalize()
    bc_label = (
        "Excellent" if isinstance(bc_score, (int,float)) and bc_score >= 90 else
        "Good"      if isinstance(bc_score, (int,float)) and bc_score >= 75 else
        "Fair"      if isinstance(bc_score, (int,float)) and bc_score >= 50 else
        "Low"
    )

    def score_color(score):
        if score is None: return "#64748B"
        if score >= 75: return "#059669"
        if score >= 50: return "#D97706"
        return "#DC2626"

    def score_bg(score):
        if score is None: return "#F8FAFC"
        if score >= 75: return "#ECFDF5"
        if score >= 50: return "#FFFBEB"
        return "#FEF2F2"

    def badge_class(label):
        l = label.lower()
        if l in ("high","excellent","good","pass"): return "badge-green"
        if l in ("medium","fair","warn","warning"):  return "badge-amber"
        return "badge-red"

    def compliance_rows():
        items = [
            ("audit_trail",        "Audit Trail"),
            ("version_history",    "Version History"),
            ("artifact_retention", "Artifact Retention"),
        ]
        rows = ""
        for key, label in items:
            val = compliance.get(key, False)
            icon = "\u2713" if val else "\u2717"
            cls  = "check-pass" if val else "check-fail"
            rows += f'<div class="compliance-row"><span class="{cls}">{icon}</span>{label}</div>'
        return rows

    def model_rows():
        rows = ""
        for m in model_reg:
            rows += f"""
            <tr>
              <td>{m.get('agent_role','')}</td>
              <td class="mono">{m.get('model','')}</td>
              <td>{m.get('provider','')}</td>
            </tr>"""
        return rows

    def milestone_rows():
        html = ""
        for m in milestones:
            html += f'<div class="milestone-title">{m.get("name","")}</div>'
            for tk in m.get("tasks", [])[:8]:
                tid  = tk.get("id","")
                desc = tk.get("description", tk.get("title",""))
                html += f'<div class="task-row"><span class="task-id">{tid}</span>{desc}</div>'
        return html

    def breakdown_rows():
        rows = ""
        filtered = [b for b in bc.get("breakdown",[])
                    if b.get("factor","").lower() not in ("build speed","design assets")]
        for b in filtered:
            rows += f"""
            <tr>
              <td>{b.get('factor','').title()}</td>
              <td class="mono center">{b.get('points','')}</td>
              <td>{(b.get('note','') or '').capitalize()}</td>
            </tr>"""
        return rows

    cover_label = "Client Delivery Certificate" if pdf_type == "client" else "Internal Build Report"
    DASH = "\u2014"

    # Quality tier badge for badges row
    quality_tier = (factsheet.get("readiness") or {}).get("quality_tier")
    combined_score = (factsheet.get("readiness") or {}).get("combined_score")
    _tier_colors = {"high": "#3b82f6", "good": "#10b981", "low": "#ef4444"}
    if quality_tier and quality_tier in _tier_colors:
        _tc = _tier_colors[quality_tier]
        _tl = quality_tier.capitalize()
        quality_tier_row = (
            f'<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e2e8f0;'
            f' display: flex; align-items: center; gap: 12px;">'
            f'<span style="color: {_tc}; font-size: 12px; font-weight: 700;'
            f' letter-spacing: 0.05em;">'
            f'\u2726 {_tl} Quality</span>'
            f'<span style="color: #64748b; font-size: 11px;">'
            f'\u2014 Overall Score {combined_score}/100</span></div>'
        )
    else:
        quality_tier_row = ""

    credits_val = usage.get("credits_used") or DASH
    credits_stat = "" if pdf_type == "client" else f'''
      <div class="stat-box">
        <div class="stat-box-label">Credits Used</div>
        <div class="stat-box-value">{credits_val}</div>
      </div>'''

    # Scoring block — shown in both PDFs
    scoring_html = ""
    if scoring:
        scoring_html = f"""
        <div class="section-title">Quality Scores</div>
        <div class="score-grid">
          <div class="score-card" style="border-top: 3px solid #2563EB;">
            <div class="score-label">Prompt Quality
              <span class="watson-badge">Powered by IBM Watson NLU</span>
            </div>
            <div class="score-number" style="color:{score_color(pq_score)};">{pq_score if pq_score is not None else DASH}</div>
            <div class="score-sub">/100</div>
            <span class="badge {badge_class(pq_label)}">{pq_label}</span>
            <div class="score-meta">How clearly your idea was communicated to the AI pipeline</div>
          </div>
          <div class="score-card" style="border-top: 3px solid #2563EB;">
            <div class="score-label">Build Confidence
              <span class="archon-badge">Archon Engine</span>
            </div>
            <div class="score-number" style="color:{score_color(bc_score)};">{bc_score if bc_score is not None else DASH}</div>
            <div class="score-sub">/100</div>
            <span class="badge {badge_class(bc_label)}">{bc_label}</span>
            <div class="score-meta">Based on code output, archetype detection, and pipeline success</div>
          </div>
        </div>
        """
        if pdf_type == "internal" and bc.get("breakdown"):
            scoring_html += f"""
            <div class="sub-section">
              <div class="sub-title">Build Score Breakdown</div>
              <table>
                <thead><tr><th>Factor</th><th>Points</th><th>Note</th></tr></thead>
                <tbody>{breakdown_rows()}</tbody>
              </table>
              <div class="footnote">
                Scoring Methodology: Prompt Quality is measured by IBM Watson NLU \u2014 keyword density,
                domain relevance, and entity extraction from the user\u2019s original prompt (scale 0\u2013100).
                Build Confidence is computed by Archon\u2019s governance engine from pipeline outputs \u2014
                files generated, archetype detection success, and pipeline completion status.
              </div>
            </div>
            """

    # Internal-only pipeline section
    pipeline_html = ""
    if pdf_type == "internal":
        seq = " \u2192 ".join(
            a.upper() if a == "pm" else a.capitalize()
            for a in pipeline.get("agent_sequence", [])
        )
        duration = pipeline.get("duration_seconds")
        dur_str = f"{duration}s" if duration else "\u2014"
        pipeline_html = f"""
        <div class="section-title">Pipeline</div>
        <table>
          <thead><tr><th>Status</th><th>UI Archetype</th><th>Duration</th><th>Agent Sequence</th></tr></thead>
          <tbody>
            <tr>
              <td><span class="badge badge-green">{pipeline.get('status','').capitalize()}</span></td>
              <td>{archetype}</td>
              <td class="mono">{dur_str}</td>
              <td class="mono">{seq}</td>
            </tr>
          </tbody>
        </table>
        <div class="sub-section">
          <div class="sub-title">Usage</div>
          <table>
            <thead><tr><th>Credits Used</th></tr></thead>
            <tbody>
              <tr>
                <td class="mono">{usage.get('credits_used') or DASH}</td>
              </tr>
            </tbody>
          </table>
        </div>
        """

    # Brief section
    brief_html = ""
    if prd:
        overview = prd.get("overview","")
        goals    = prd.get("goals", [])
        features = prd.get("core_features_mvp", prd.get("core_features", []))
        brief_html = f'<div class="section-title">Brief</div>'
        if overview:
            brief_html += f'<p class="overview">{overview}</p>'
        if goals:
            brief_html += '<div class="sub-title">Goals</div><ul>'
            for g in goals[:5]:
                brief_html += f'<li>{g}</li>'
            brief_html += '</ul>'
        if features:
            brief_html += '<div class="sub-title">Core Features</div><ul>'
            for f in features[:6]:
                brief_html += f'<li>{f}</li>'
            brief_html += '</ul>'

    # Plan section
    plan_html = ""
    if milestones:
        plan_html = f'<div class="section-title">Build Plan</div><div class="milestones">{milestone_rows()}</div>'

    # Warning box
    warning_html = ""
    if human_review:
        if pdf_type == "client":
            msg = ("This build\u2019s quality scores indicate that a human review is recommended before "
                   "client delivery. Please have a team member verify the generated output meets "
                   "your quality standards.")
        else:
            msg = (f"Automated scoring flagged this build for review \u2014 "
                   f"Prompt Quality {pq_score}/100 \xb7 Build Confidence {bc_score}/100. "
                   f"Review threshold: 50/100. Verify output quality before delivery.")
        warning_html = f"""
        <div class="warning-box">
          <div class="warning-title">\u26a0 Human Review Recommended</div>
          <div class="warning-body">{msg}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 9pt;
    color: #334155;
    background: white;
    padding: 0;
  }}

  .cover {{
    background: #0F172A;
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }}
  .cover-left {{ display: flex; align-items: center; gap: 0; color: white; font-size: 11pt; font-weight: 600; }}
  .cover-right {{ color: #94A3B8; font-size: 9pt; }}

  .header {{ padding: 16px 24px 12px 24px; margin-bottom: 0; }}
  .divider {{ border: none; border-top: 1px solid #E2E8F0; margin: 0 24px 20px 24px; }}
  .header * {{ max-width: 100%; }}
  .header-top {{ display: flex; align-items: flex-start; gap: 14px; }}
  .shield-icon {{ width: 44px; height: 44px; flex-shrink: 0; margin-top: 4px; }}
  .project-name {{ font-size: 22pt; font-weight: 700; color: #0F172A; margin-bottom: 4px; }}
  .project-sub {{ font-size: 12pt; font-weight: 600; color: #2563EB; margin-bottom: 3px; }}
  .project-meta {{ font-size: 8pt; color: #94A3B8; }}
  .trust-strip {{
    display: flex; gap: 16px; margin-top: 10px;
    padding: 8px 0; border-top: 1px solid #E2E8F0;
    flex-wrap: wrap;
  }}
  .trust-item {{
    font-size: 7.5pt; color: #2563EB; font-weight: 500;
  }}

  .header-badges {{ display: flex; gap: 8px; margin-top: 10px; max-width: fit-content; }}
  .hbadge {{
    font-size: 7.5pt; font-weight: 600;
    padding: 3px 11px; border-radius: 12px;
    display: inline-block; gap: 5px;
  }}
  .hbadge-green {{ color: #059669; background: #ECFDF5; border: 1.5px solid #6EE7B7; }}
  .hbadge-blue  {{ color: #2563EB; background: #EFF6FF; border: 1.5px solid #BFDBFE; }}

  .content {{ padding: 0 24px; }}

  .section {{ margin-bottom: 20px; }}
  .section-title {{
    font-size: 11pt; font-weight: 700; color: #0F172A;
    margin-bottom: 10px; padding-bottom: 5px;
    border-bottom: 1px solid #E2E8F0;
  }}
  .sub-section {{ margin-top: 12px; }}
  .sub-title {{ font-size: 9pt; font-weight: 600; color: #475569; margin-bottom: 6px; margin-top: 8px; }}

  /* Score cards */
  .score-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 14px;
  }}
  .score-card {{
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 14px;
    background: #F8FAFC;
  }}
  .score-label {{
    font-size: 9pt; font-weight: 600; color: #0F172A;
    margin-bottom: 6px;
    display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  }}
  .score-number {{
    font-size: 32pt; font-weight: 700; line-height: 1;
    display: inline;
  }}
  .score-sub {{ font-size: 10pt; color: #94A3B8; display: inline; margin-left: 3px; }}
  .score-meta {{ font-size: 7.5pt; color: #94A3B8; margin-top: 6px; line-height: 1.4; }}

  /* Badges */
  .badge {{
    display: inline-block;
    font-size: 7.5pt; font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    margin-top: 4px;
  }}
  .badge-green {{ background: #ECFDF5; color: #059669; border: 1px solid #6EE7B7; }}
  .badge-amber {{ background: #FFFBEB; color: #D97706; border: 1px solid #FCD34D; }}
  .badge-red   {{ background: #FEF2F2; color: #DC2626; border: 1px solid #FCA5A5; }}
  .badge-blue  {{ background: #EFF6FF; color: #2563EB; border: 1px solid #93C5FD; }}

  .watson-badge {{
    font-size: 7pt; font-weight: 500;
    background: #EFF6FF; color: #2563EB;
    padding: 2px 7px; border-radius: 10px;
    border: none;
  }}
  .archon-badge {{
    font-size: 7pt; font-weight: 500;
    background: #F5F3FF; color: #7C3AED;
    padding: 2px 7px; border-radius: 10px;
    border: none;
  }}

  /* Tables */
  table {{
    width: 100%; border-collapse: collapse;
    font-size: 8.5pt; margin-bottom: 4px;
  }}
  thead tr {{ background: #F8FAFC; }}
  th {{
    text-align: left; font-weight: 600; font-size: 7.5pt;
    color: #94A3B8; text-transform: uppercase; letter-spacing: 0.04em;
    padding: 7px 10px; border-bottom: 1px solid #E2E8F0;
  }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #F1F5F9; color: #334155; }}
  tr:last-child td {{ border-bottom: none; }}
  tbody tr:nth-child(even) {{ background: #F8FAFC; }}
  .mono {{ font-family: 'Courier New', monospace; font-size: 8pt; }}
  .center {{ text-align: center; }}

  table {{ border: 1px solid #E2E8F0; border-radius: 6px; overflow: hidden; }}

  /* Output stat boxes */
  .stat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 8px;
    margin-bottom: 4px;
  }}
  .stat-box {{
    border: 1px solid #E2E8F0; border-radius: 6px;
    padding: 10px 12px; background: #F8FAFC;
  }}
  .stat-box-label {{ font-size: 7.5pt; color: #94A3B8; font-weight: 500; margin-bottom: 4px; }}
  .stat-box-value {{ font-size: 13pt; font-weight: 700; color: #0F172A; }}

  /* Compliance */
  .compliance-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }}
  .compliance-row {{
    display: flex; align-items: center; gap: 8px;
    font-size: 8.5pt; color: #334155;
    padding: 6px 0;
    border-bottom: 1px solid #F1F5F9;
  }}
  .check-pass {{ color: #059669; font-size: 11pt; font-weight: 700; }}
  .check-fail {{ color: #DC2626; font-size: 11pt; font-weight: 700; }}

  /* Brief / Plan */
  .overview {{ color: #475569; line-height: 1.6; margin-bottom: 8px; font-size: 8.5pt; }}
  ul {{ padding-left: 16px; margin-bottom: 6px; }}
  li {{ color: #475569; line-height: 1.7; font-size: 8.5pt; }}

  .milestones {{ margin-top: 4px; }}
  .milestone-title {{
    font-size: 8.5pt; font-weight: 700; color: #0F172A;
    margin: 10px 0 4px 0;
  }}
  .task-row {{
    display: grid;
    grid-template-columns: minmax(68px, auto) 1fr;
    gap: 10px;
    padding: 4px 0;
    font-size: 8pt;
    color: #475569;
    align-items: start;
  }}
  .task-id {{
    font-family: monospace;
    font-size: 7pt;
    font-weight: 600;
    color: #4F46E5;
    background: #EEF2FF;
    padding: 2px 6px;
    border-radius: 3px;
    white-space: nowrap;
    text-align: center;
    display: inline-block;
    width: 100%;
    box-sizing: border-box;
  }}

  /* Warning */
  .warning-box {{
    border: 1px solid #FCA5A5; border-radius: 6px;
    background: #FEF2F2; padding: 12px 14px;
    margin-top: 12px;
  }}
  .warning-title {{ font-size: 9pt; font-weight: 700; color: #DC2626; margin-bottom: 4px; }}
  .warning-body  {{ font-size: 8pt; color: #991B1B; line-height: 1.5; }}

  /* Footnote */
  .footnote {{
    font-size: 7.5pt; color: #94A3B8; line-height: 1.5;
    margin-top: 8px; padding-top: 8px;
    border-top: 1px solid #F1F5F9;
    font-style: italic;
  }}

  /* Footer */
  .footer {{
    margin-top: 28px; padding: 12px 24px;
    border-top: 1px solid #E2E8F0;
    text-align: center;
    font-size: 7.5pt; color: #94A3B8;
  }}
</style>
</head>
<body>

<div class="cover">
  <div class="cover-left">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="display:inline-block; vertical-align:middle; margin-right:8px; flex-shrink:0;">
      <polygon points="12,2 20.66,7 20.66,17 12,22 3.34,17 3.34,7"
               fill="none" stroke="white" stroke-width="2.5" stroke-linejoin="round"/>
    </svg>
    <span style="font-family: Inter, -apple-system, 'Segoe UI', sans-serif; font-weight: 600; letter-spacing: -0.02em; vertical-align: middle; font-size: 11pt;">Archon</span>
  </div>
  <div class="cover-right">{cover_label}</div>
</div>

<div class="header">
  <div class="header-top">
    <svg class="shield-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2L3 7V12C3 16.55 6.84 20.74 12 22C17.16 20.74 21 16.55 21 12V7L12 2Z"
            fill="#EFF6FF" stroke="#2563EB" stroke-width="1.5" stroke-linejoin="round"/>
      <path d="M9 12L11 14L15 10" stroke="#2563EB" stroke-width="1.5"
            stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <div>
      <div class="project-name">{project_name}</div>
      <div class="project-sub">AI Build Factsheet \xb7 Version {ver}</div>
      <div class="project-meta">Generated {ts} \xb7 Archon Governed Pipeline</div>
    </div>
  </div>
  <div class="trust-strip">
    <span class="trust-item">&#10003; Audit Trail</span>
    <span class="trust-item">&#10003; Version Controlled</span>
    <span class="trust-item">&#10003; AI Governed</span>
    <span class="trust-item">&#10003; Immutable Record</span>
  </div>
  <div class="header-badges">
    <span class="hbadge hbadge-green">&#10004; Verified</span>
    <span class="hbadge hbadge-blue">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" style="display:inline;vertical-align:middle;margin-right:3px;">
        <path d="M12 2L3 7V12C3 16.55 6.84 20.74 12 22C17.16 20.74 21 16.55 21 12V7L12 2Z"
              fill="#EFF6FF" stroke="#2563EB" stroke-width="2" stroke-linejoin="round"/>
        <path d="M9 12L11 14L15 10" stroke="#2563EB" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round"/>
      </svg>Auditable
    </span>
  </div>
  {quality_tier_row}
</div>
<hr class="divider">

<div class="content">

  <div class="section">
    {scoring_html}
  </div>

  <div class="section">
    {brief_html}
  </div>

  <div class="section">
    {plan_html}
  </div>

  <div class="section">
    <div class="section-title">AI Models Used</div>
    <table>
      <thead><tr><th>Agent Role</th><th>Model</th><th>Provider</th></tr></thead>
      <tbody>{model_rows()}</tbody>
    </table>
  </div>

  <div class="section">
    <div class="section-title">Build Output</div>
    <div class="stat-grid">
      <div class="stat-box">
        <div class="stat-box-label">UI Archetype</div>
        <div class="stat-box-value" style="font-size:11pt;">{archetype}</div>
      </div>
      <div class="stat-box">
        <div class="stat-box-label">Files Generated</div>
        <div class="stat-box-value">{outputs.get('files_generated', 0)}</div>
      </div>
      <div class="stat-box">
        <div class="stat-box-label">Images Generated</div>
        <div class="stat-box-value">{outputs.get('images_generated', 0)}</div>
      </div>
      {credits_stat}
    </div>
  </div>

  {pipeline_html}

  <div class="section">
    <div class="section-title">Compliance</div>
    <p style="font-size:8pt; color:#64748B; font-style:italic; margin-bottom:10px;">
      This build was generated by a governed, auditable AI pipeline.
      All decisions are version-controlled and available for review.
    </p>
    <div class="compliance-grid">
      {compliance_rows()}
    </div>
    {warning_html}
  </div>

</div>

<div class="footer">
  Archon AI Build Platform \xb7 Version {ver} \xb7 {ts} \xb7 archon.build
</div>

</body>
</html>"""

    pdf_bytes = HTML(string=html).write_pdf()
    buf = io.BytesIO(pdf_bytes)
    buf.seek(0)

    label = "client" if pdf_type == "client" else "internal"
    safe_name = project_name.lower().replace(" ", "-")[:30]
    filename = f"archon-{safe_name}-v{ver}-{label}.pdf"
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)


if __name__ == "__main__":
    init_db()
    print(f"Flask server starting...")
    print(f"REPO_ROOT: {REPO_ROOT}")
    print(f"PUBLIC_DIR: {PUBLIC_DIR}")
    print(f"CORS enabled for: http://localhost:5173, http://localhost:3000")
    app.run(debug=True, port=5000)


