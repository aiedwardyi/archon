from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import json
import os
import sys
import warnings
import re
from pathlib import Path
from typing import Any, Dict
import threading
import time
from datetime import datetime, timezone

# Suppress SQLAlchemy legacy Query.get() deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlalchemy")

from models import Project, Execution, get_session, init_db, get_next_version

app = Flask(__name__)

CORS(app, origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:8080"])

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = REPO_ROOT / "generated"

execution_state = {
    "running": False,
    "started_at": None,
    "current_project_id": None,
    "current_execution_id": None,
    "logs": [],
    "result_ready": False,
}


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

def add_log(message: str, log_type: str = "info"):
    global _log_counter
    _log_counter += 1
    ts = int(time.time() * 1000)
    execution_state["logs"].append({
        "id": f"log-{ts}-{_log_counter}",
        "timestamp": ts,
        "message": message,
        "type": log_type,
    })
    print(f"[LOG] {message}")


def get_version_dir(project_id: int, version: int) -> Path:
    return PUBLIC_DIR / str(project_id) / f"v{version}"


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
        project_id = execution_state.get("current_project_id")

    if not version:
        execution_id = execution_state.get("current_execution_id")
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


def run_full_pipeline_async(task_description: str, prompt_history: list = None):
    global execution_state

    sys.path.insert(0, str(REPO_ROOT))

    session = get_session()
    execution_id = execution_state.get("current_execution_id")
    locked_ui_archetype = None
    pipeline_start_time = time.time()

    try:
        if execution_id:
            execution = session.get(Execution, execution_id)
            if execution:
                execution.status = "running"
                session.commit()

        project_id = execution_state.get("current_project_id")
        version = None
        if execution_id:
            execution = session.get(Execution, execution_id)
            if execution:
                version = execution.version
                if execution.project_id:
                    project = session.get(Project, execution.project_id)
                    if project:
                        locked_ui_archetype = project.locked_ui_archetype
        is_iteration = bool(version and version > 1)

        if project_id and version:
            version_dir = get_version_dir(project_id, version)
        else:
            version_dir = PUBLIC_DIR / "shared"
        version_dir.mkdir(parents=True, exist_ok=True)

        # Load existing code from nearest ancestor that has code on disk
        existing_code = None
        ancestor_version_dir = None
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
                candidate = ancestor_dir / "src" / "index.html"
                if not candidate.exists():
                    html_files = list(ancestor_dir.rglob("*.html"))
                    candidate = html_files[0] if html_files else None
                if candidate and Path(candidate).exists():
                    html_content = Path(candidate).read_text(encoding="utf-8", errors="replace")
                    css_candidate = ancestor_dir / "src" / "style.css"
                    if css_candidate.exists():
                        css_content = css_candidate.read_text(encoding="utf-8", errors="replace")
                        existing_code = f"<!-- src/index.html -->\n{html_content}\n\n/* src/style.css */\n{css_content}"
                    else:
                        existing_code = html_content
                    ancestor_version_dir = get_version_dir(project_id, ancestor_exec.version)
                    add_log(f"Build Agent: Loading v{ancestor_exec.version} for context...")
                    break
                ancestor_id = ancestor_exec.parent_execution_id
                hops += 1
        finally:
            session_check.close()

        add_log("Starting pipeline...")
        add_log("Requirements Agent: Analyzing your request...")
        sys.path.insert(0, str(REPO_ROOT))
        from agents.pm_agent import PMAgent
        pm_agent = PMAgent()

        context_input = task_description
        if prompt_history and len(prompt_history) > 1:
            history_text = "\n".join(
                f"{turn['role'].upper()}: {turn['content']}"
                for turn in prompt_history
            )
            context_input = f"Full conversation history:\n{history_text}\n\nLatest request: {task_description}"
        if existing_code:
            # Extract app title from previous HTML to preserve it
            import re as _re
            title_match = _re.search(r"<title[^>]*>(.*?)</title>", existing_code, _re.IGNORECASE)
            prev_title = title_match.group(1).strip() if title_match else None
            title_note = f" The app is currently named \"{prev_title}\" Ã¢â‚¬â€ preserve this name unless the user explicitly asks to change it." if prev_title else ""
            context_input += f"\n\nNOTE: This is an iteration on an existing app. The current HTML is provided to the engineer. The PRD should reflect ONLY the changes requested, not rebuild from scratch.{title_note}"

        prd_artifact = pm_agent.generate_prd(context_input)

        prd_dict = prd_artifact.model_dump()
        prd_dict["_agent_sequence"] = ["pm"]
        write_json_file(version_dir / "last_prd.json", prd_dict)

        add_log("Requirements Agent: Brief created.")
        print(f"PRD saved: {prd_artifact.prd.document_title}")

        add_log("Architecture Agent: Planning the build...")

        from google import genai
        from agents.planner_agent import PlannerAgent

        genai_key = os.getenv("GENAI_API_KEY")
        if not genai_key:
            raise ValueError("GENAI_API_KEY environment variable not set")

        genai_client = genai.Client(api_key=genai_key)
        planner = PlannerAgent(genai_client)
        plan = planner.run_from_prd_artifact(
            version_dir / "last_prd.json",
            locked_ui_archetype=locked_ui_archetype,
            is_iteration=is_iteration,
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

        add_log("Architecture Agent: Build plan ready.")
        milestone_count = len(plan.milestones)
        task_count = sum(len(m.tasks) for m in plan.milestones)
        print(f"Plan saved: {milestone_count} milestones, {task_count} tasks")

        design_assets = []
        if is_iteration and ancestor_version_dir:
            ancestor_assets_file = ancestor_version_dir / "last_design_assets.json"
            if ancestor_assets_file.exists():
                try:
                    ancestor_assets_data = read_json_file(ancestor_assets_file) or {}
                    design_assets = ancestor_assets_data.get("assets", [])
                    write_json_file(version_dir / "last_design_assets.json", {"assets": design_assets})
                    add_log(f"Design Agent: Reusing {len(design_assets)} images from previous version.")
                except Exception as e:
                    print(f"Failed to load ancestor design assets (non-fatal): {e}")
                    add_log("Design Agent: Could not load previous images, continuing...")
            else:
                add_log("Design Agent: No previous images found, skipping.")
        else:
            add_log("Design Agent: Generating visuals...")
            try:
                from agents.design_agent import DesignAgent
                prd_data = read_json_file(version_dir / "last_prd.json") or {}
                design_agent = DesignAgent()
                assets_dir = version_dir / "assets"
                design_assets = design_agent.run(prd_data, max_images=6, save_dir=assets_dir)
                if design_assets:
                    write_json_file(version_dir / "last_design_assets.json", {"assets": design_assets})
                    add_log(f"Design Agent: {len(design_assets)} images ready.")
                else:
                    add_log("Design Agent: No images generated, continuing...")
            except Exception as design_err:
                print(f"DesignAgent failed (non-fatal): {design_err}")
                add_log("Design Agent: Skipped, continuing with build...")

        add_log("Build Agent: Writing your code...")

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

        from agents.engineer_agent import EngineerAgent
        engineer = EngineerAgent(genai_client)
        # Inject design assets into engineer prompt if available
        design_context = ""
        if design_assets:
            asset_lines = []
            for a in design_assets:
                # Use local served path if downloaded; fall back to Azure URL
                # Extract actual version from local_path (may point to ancestor)
                asset_version = version
                if a.get("local_path"):
                    lp = a["local_path"].replace("\\", "/")
                    parts = lp.split("/")
                    for i, part in enumerate(parts):
                        if part.startswith("v") and part[1:].isdigit():
                            asset_version = int(part[1:])
                            break
                img_url = f"/api/assets/{project_id}/{asset_version}/{a['key']}.png" if a.get("local_path") else a["url"]
                line = "  - " + a["key"] + " (" + a["purpose"] + "): " + img_url
                asset_lines.append(line)
            design_context = "\n\nDESIGN ASSETS - USE THESE IMAGE URLs IN THE HTML:\n" + "\n".join(asset_lines) + "\nIMPORTANT: Use these exact URLs in <img> tags or CSS background-image. Do not use placeholder images.\n"
            task_description_with_assets = task_description + design_context
        else:
            task_description_with_assets = task_description

        result = engineer.run(engineer_task, user_prompt=task_description_with_assets, existing_code=existing_code)

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
                add_log(f"Build Agent: Created {file_artifact.path}")
            except ValueError as skip_err:
                # In iteration mode, fail hard to keep behavior deterministic and auditable.
                if is_iteration:
                    raise
                print(f"Build Agent: Skipped {file_artifact.path} ({skip_err})")
                print(f"Skipped file: {skip_err}")
        add_log("Build complete.")
        execution_state["result_ready"] = True
        execution_state["result_ready"] = True

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
                "files_generated": len(result.files),
                "writes": [
                    {"path": str(rec.path), "sha256": rec.sha256, "bytes": rec.bytes}
                    for rec in writes
                ],
            },
            "error": None,
            "_agent_sequence": ["pm", "planner", "engineer"],
            "logs": list(execution_state.get("logs", [])),
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
                execution.model_used = "Claude Sonnet 4.5"
                if hasattr(result, "usage") and result.usage:
                    execution.tokens_used = getattr(result.usage, "total_tokens", None)
                    if execution.tokens_used:
                        execution.estimated_cost = round(execution.tokens_used * 0.000003, 4)
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

    except Exception as e:
        error_msg = str(e)
        short_msg = error_msg.split("\n")[0][:200]
        add_log(f"Something went wrong: {short_msg}")
        execution_state["result_ready"] = True
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
        execution_state["running"] = False
        session.close()
        print("Pipeline complete")


# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

@app.route("/api/projects", methods=["GET"])
def list_projects():
    session = get_session()
    try:
        projects = session.query(Project).order_by(Project.updated_at.desc()).all()
        return jsonify([p.to_dict() for p in projects]), 200
    finally:
        session.close()


@app.route("/api/stats", methods=["GET"])
def get_stats():
    from sqlalchemy import func
    session = get_session()
    try:
        # versions_shipped: sum of max version per project
        version_counts = (
            session.query(Execution.project_id, func.max(Execution.version))
            .group_by(Execution.project_id)
            .all()
        )
        versions_shipped = sum(v for _, v in version_counts)

        # avg_build_time_seconds from completed executions that have duration
        avg_row = (
            session.query(func.avg(Execution.duration_seconds))
            .filter(Execution.status == "success", Execution.duration_seconds.isnot(None))
            .scalar()
        )
        avg_build_time_seconds = round(avg_row, 1) if avg_row else None

        # lines_generated: walk all version code dirs and count lines
        total_lines = 0
        all_execs = session.query(Execution.project_id, Execution.version).filter(Execution.status == "success").all()
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
        pipelines_today = (
            session.query(func.count(Execution.id))
            .filter(Execution.created_at >= today_start)
            .scalar() or 0
        )

        return jsonify({
            "versions_shipped": versions_shipped,
            "avg_build_time_seconds": avg_build_time_seconds,
            "lines_generated": total_lines,
            "pipelines_today": pipelines_today,
        }), 200
    finally:
        session.close()


@app.route("/api/activity", methods=["GET"])
def get_activity():
    session = get_session()
    try:
        recent = (
            session.query(Execution)
            .order_by(Execution.created_at.desc())
            .limit(6)
            .all()
        )
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
        project = Project(
            name=data["name"],
            description=data.get("description", ""),
            status="pending",
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        return jsonify(project.to_dict()), 201
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


@app.route("/api/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id: int):
    session = get_session()
    try:
        project = session.get(Project, project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        session.delete(project)
        session.commit()
        return jsonify({"message": "Project deleted"}), 200
    finally:
        session.close()


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
    global execution_state

    if execution_state["running"]:
        return jsonify({"error": "A pipeline is already running"}), 409

    session = get_session()
    try:
        data = request.get_json()
        if not data or not data.get("prompt"):
            return jsonify({"error": "prompt is required"}), 400

        project = session.get(Project, project_id)
        if not project:
            return jsonify({"error": f"Project {project_id} not found"}), 404

        prompt = data["prompt"]
        prompt_history = data.get("prompt_history", [])
        if not prompt_history:
            prompt_history = [{"role": "user", "content": prompt}]

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

        execution_state["running"] = True
        execution_state["started_at"] = time.time()
        execution_state["current_project_id"] = project_id
        execution_state["current_execution_id"] = execution.id
        execution_state["logs"] = []
        execution_state["result_ready"] = False

        print(f"Starting iteration v{next_version} for project {project_id}: {prompt}")
        thread = threading.Thread(
            target=run_full_pipeline_async,
            args=(prompt, prompt_history),
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
        execution_state["running"] = False
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
    global execution_state

    session = get_session()
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({"error": "No JSON payload provided"}), 400

        project_id = req_data.get("project_id")

        if not project_id:
            project = Project(name="Untitled Project", description="", status="in_progress")
            session.add(project)
            session.commit()
            session.refresh(project)
            project_id = project.id
        else:
            project = session.get(Project, project_id)
            if not project:
                return jsonify({"error": f"Project {project_id} not found"}), 404
            project.status = "in_progress"
            project.updated_at = datetime.now(timezone.utc)
            session.commit()

        next_version = get_next_version(session, project_id)
        task_description = project.description or project.name
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
            status="pending",
            version=next_version,
            prompt_history=json.dumps(initial_history),
            is_active_head=True,
            parent_execution_id=None,
        )
        session.add(execution)
        session.commit()
        session.refresh(execution)

        execution_state["running"] = True
        execution_state["started_at"] = time.time()
        execution_state["current_project_id"] = project_id
        execution_state["current_execution_id"] = execution.id
        execution_state["logs"] = []

        print(f"Starting v{next_version} for project {project_id}: {task_description}")
        thread = threading.Thread(
            target=run_full_pipeline_async,
            args=(task_description, initial_history),
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
        execution_state["running"] = False
        print(f"Error in execute_task: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/execution-status", methods=["GET"])
def execution_status():
    project_id = execution_state.get("current_project_id")
    version = None
    execution_id = execution_state.get("current_execution_id")

    if execution_id:
        session = get_session()
        try:
            execution = session.get(Execution, execution_id)
            if execution:
                version = execution.version
                # 7C.2: DB is ground truth when pipeline not actively running
                if not execution_state["running"] and execution.status in ("success", "error"):
                    db_status = "COMPLETED" if execution.status == "success" else "FAILED"
                    return jsonify({
                        "status": db_status,
                        "currentStage": "engineer",
                        "logs": execution_state.get("logs", []),
                        "engineerTasks": [],
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

    logs = execution_state.get("logs", [])
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

    if data is not None and execution_state.get("result_ready", True):
        raw_status = str(data.get("status", "success")).lower()
        frontend_status = STATUS_MAP.get(raw_status, "COMPLETED")
        return jsonify({
            "status": frontend_status,
            "currentStage": "engineer",
            "logs": logs,
            "engineerTasks": [],
            "project_id": project_id,
            "execution_id": execution_id,
        }), 200

    if execution_state["running"]:
        return jsonify({
            "status": "RUNNING",
            "currentStage": current_stage,
            "logs": logs,
            "engineerTasks": [],
            "project_id": project_id,
            "execution_id": execution_id,
        }), 200

    return jsonify({
        "status": "FAILED",
        "currentStage": "complete",
        "logs": logs,
        "engineerTasks": [],
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
    html_file = code_dir / "src" / "index.html"

    target = None
    if html_file.exists():
        target = html_file
    elif code_dir.exists():
        html_files = list(code_dir.rglob("*.html"))
        if html_files:
            target = html_files[0]

    if target:
        html = target.read_text(encoding="utf-8", errors="replace")
        src_dir = code_dir / "src"
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
        return Response(html, mimetype="text/html")

    return Response(PREVIEW_PLACEHOLDER, mimetype="text/html", status=200)


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
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/assets/<int:project_id>/<int:version>/<filename>", methods=["GET"])
def get_asset(project_id: int, version: int, filename: str):
    asset_path = get_version_dir(project_id, version) / "assets" / filename
    if not asset_path.exists():
        return jsonify({"error": "Asset not found"}), 404
    return send_file(asset_path, mimetype="image/png")


@app.route("/api/projects/<int:project_id>/chat", methods=["POST"])
def project_chat(project_id: int):
    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "message is required"}), 400
    try:
        requested_archetype = detect_requested_archetype(data["message"])
        # Load PRD from active head version for context-aware replies
        project_context = None
        db = get_session()
        try:
            project = db.get(Project, project_id)
            if (
                project
                and project.locked_ui_archetype
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
            if head:
                prd_path = get_version_dir(project_id, head.version) / "last_prd.json"
                prd_data = read_json_file(prd_path)
                if prd_data:
                    prd = prd_data.get("prd", prd_data)
                    title = prd.get("document_title", "Unknown")
                    overview = prd.get("overview", "")
                    features = ", ".join(prd.get("core_features_mvp", []))
                    stack = ", ".join(prd.get("technical_stack_recommendation", []))
                    project_context = f"Project: {title}\nOverview: {overview}\nFeatures: {features}\nStack: {stack}"
        finally:
            db.close()

        sys.path.insert(0, str(REPO_ROOT))

        from agents.pm_agent import PMAgent
        pm = PMAgent()
        intent = pm.classify_intent(data["message"], project_context=project_context)
        if intent.get("type") == "chat":
            return jsonify({"response_type": "chat", "message": intent["message"]}), 200
        return jsonify({"response_type": "build"}), 200
    except Exception as e:
        print(f"Chat classify error: {e}")
        return jsonify({
            "response_type": "chat",
            "message": "I'm having trouble connecting right now. Could you rephrase that or try again?"
        }), 200



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
    html_file = published_dir / "src" / "index.html"

    if not html_file.exists():
        html_files = list(published_dir.rglob("*.html"))
        html_file = html_files[0] if html_files else None

    if not html_file:
        return "Published app not found", 404

    html = Path(html_file).read_text(encoding="utf-8", errors="replace")
    css_file = Path(html_file).parent / "style.css"
    if css_file.exists():
        css = css_file.read_text(encoding="utf-8", errors="replace")
        html = html.replace(
            '<link rel="stylesheet" href="./style.css">',
            f"<style>{css}</style>"
        )
    return Response(html, mimetype="text/html")




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
    watson_key = os.getenv("WATSON_STT_APIKEY")

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
    watson_key = os.getenv("WATSON_TTS_APIKEY")
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
            voice="en-US_AllisonExpressive",
            accept="audio/mp3",
        ).get_result()
        audio_bytes = response.content
        return Response(audio_bytes, mimetype="audio/mp3")
    except Exception as e:
        print(f"Watson TTS error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    print(f"Flask server starting...")
    print(f"REPO_ROOT: {REPO_ROOT}")
    print(f"PUBLIC_DIR: {PUBLIC_DIR}")
    print(f"CORS enabled for: http://localhost:5173, http://localhost:3000")
    app.run(debug=True, port=5000)




