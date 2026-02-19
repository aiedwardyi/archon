from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict
import threading
import time
from datetime import datetime, timezone

from models import Project, Execution, get_session, init_db, get_next_version

app = Flask(__name__)

CORS(app, origins=["http://localhost:5173", "http://localhost:3000"])

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = REPO_ROOT / "apps" / "offline-vite-react" / "public"

execution_state = {
    "running": False,
    "started_at": None,
    "current_project_id": None,
    "current_execution_id": None,
    "logs": [],
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


def add_log(message: str, log_type: str = "info"):
    """Add a log entry to the current execution state."""
    execution_state["logs"].append({
        "id": f"log-{int(time.time() * 1000)}",
        "timestamp": int(time.time() * 1000),
        "message": message,
        "type": log_type,
    })
    print(f"[LOG] {message}")


def run_full_pipeline_async(task_description: str, prompt_history: list = None):
    """
    Run the full Requirements -> Architecture -> Build pipeline in a background thread.
    prompt_history: full conversation array for context continuation across versions.
    """
    global execution_state

    sys.path.insert(0, str(REPO_ROOT))

    session = get_session()
    execution_id = execution_state.get("current_execution_id")

    try:
        # Mark execution as running
        if execution_id:
            execution = session.query(Execution).get(execution_id)
            if execution:
                execution.status = "running"
                session.commit()

        # =====================================================================
        # STEP 1: Requirements Agent → Brief
        # =====================================================================
        add_log("Starting pipeline...")
        add_log("Requirements Agent: Analyzing your request...")

        from agents.pm_agent import PMAgent
        pm_agent = PMAgent()

        # Pass full prompt history to PM agent for context continuation.
        # On v1 this is just the single prompt; on v2+ it includes all prior turns.
        context_input = task_description
        if prompt_history and len(prompt_history) > 1:
            history_text = "\n".join(
                f"{turn['role'].upper()}: {turn['content']}"
                for turn in prompt_history
            )
            context_input = f"Full conversation history:\n{history_text}\n\nLatest request: {task_description}"

        prd_artifact = pm_agent.generate_prd(context_input)

        prd_dict = prd_artifact.model_dump()
        prd_dict["_agent_sequence"] = ["pm"]
        write_json_file(PUBLIC_DIR / "last_prd.json", prd_dict)

        add_log("Requirements Agent: Brief created.")
        print(f"PRD saved: {prd_artifact.prd.document_title}")

        # =====================================================================
        # STEP 2: Architecture Agent → Build Plan
        # =====================================================================
        add_log("Architecture Agent: Planning the build...")

        from google import genai
        from agents.planner_agent import PlannerAgent

        genai_key = os.getenv("GENAI_API_KEY")
        if not genai_key:
            raise ValueError("GENAI_API_KEY environment variable not set")

        genai_client = genai.Client(api_key=genai_key)
        planner = PlannerAgent(genai_client)
        plan = planner.run_from_prd_artifact(PUBLIC_DIR / "last_prd.json")

        plan_dict = {
            "kind": "plan_artifact",
            "agent_role": "planner",
            "plan": plan.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "_agent_sequence": ["pm", "planner"],
        }
        flat_plan = plan.model_dump()
        write_json_file(PUBLIC_DIR / "last_plan.json", flat_plan)
        write_json_file(PUBLIC_DIR / "last_plan_artifact.json", plan_dict)

        add_log("Architecture Agent: Build plan ready.")
        milestone_count = len(plan.milestones)
        task_count = sum(len(m.tasks) for m in plan.milestones)
        print(f"Plan saved: {milestone_count} milestones, {task_count} tasks")

        # =====================================================================
        # STEP 3: Build Agent → Code
        # =====================================================================
        add_log("Build Agent: Writing your code...")

        engineer_task = None
        for milestone in plan.milestones:
            for task in milestone.tasks:
                if task.execution_hint == "engineer":
                    engineer_task = task
                    break
            if engineer_task:
                break

        if not engineer_task:
            raise ValueError("No engineer tasks found in plan")

        from agents.engineer_agent import EngineerAgent
        engineer = EngineerAgent(genai_client)
        result = engineer.run(engineer_task)

        from scripts.safe_write import safe_write_text
        allow_dir = PUBLIC_DIR / "generated"
        writes = []
        for file_artifact in result.files:
            rec = safe_write_text(
                allowlist_dir=allow_dir,
                relative_path=file_artifact.path,
                content=file_artifact.content,
            )
            writes.append(rec)
            add_log(f"Build Agent: Created {file_artifact.path}")

        add_log("Build complete.")

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
            "_meta": {
                "produced_at": datetime.now(timezone.utc).isoformat(),
                "consumer_version": "v4",
            },
        }
        write_json_file(PUBLIC_DIR / "last_execution_result.json", execution_result)

        print(f"Execution result saved: {len(writes)} files generated")

        # Update database — mark success and store result path
        if execution_id:
            execution = session.query(Execution).get(execution_id)
            if execution:
                execution.status = "success"
                execution.result_path = "last_execution_result.json"
                execution.prd_path = "last_prd.json"
                execution.plan_path = "last_plan.json"
                session.commit()
                project = execution.project
                if project:
                    project.status = "completed"
                    project.updated_at = datetime.utcnow()
                    session.commit()

    except Exception as e:
        error_msg = str(e)
        add_log(f"Something went wrong: {error_msg}")
        print(f"Pipeline error: {error_msg}")

        if execution_id:
            try:
                execution = session.query(Execution).get(execution_id)
                if execution:
                    execution.status = "error"
                    execution.error_message = error_msg
                    session.commit()
                    project = execution.project
                    if project:
                        project.status = "failed"
                        project.updated_at = datetime.utcnow()
                        session.commit()
            except Exception:
                pass

        write_json_file(PUBLIC_DIR / "last_execution_result.json", {
            "kind": "execution_result",
            "agent_role": "engineer",
            "status": "error",
            "error": {"message": error_msg, "type": type(e).__name__},
            "outputs": {},
            "_agent_sequence": [],
        })

    finally:
        execution_state["running"] = False
        execution_state["current_execution_id"] = None
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
        project = session.query(Project).get(project_id)
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
        project = session.query(Project).get(project_id)
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
    """
    Return all versions for a project, newest first.
    Used by the Versions page timeline.
    """
    session = get_session()
    try:
        project = session.query(Project).get(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        executions = (
            session.query(Execution)
            .filter(Execution.project_id == project_id)
            .order_by(Execution.version.desc())
            .all()
        )
        return jsonify({
            "project_id": project_id,
            "project_name": project.name,
            "versions": [e.to_dict() for e in executions],
        }), 200
    finally:
        session.close()


@app.route("/api/projects/<int:project_id>/iterate", methods=["POST"])
def iterate_project(project_id: int):
    """
    Run a new pipeline iteration for an existing project.
    Creates a new versioned execution — nothing is overwritten.

    Request body:
        {
            "prompt": "Add a login page with email/password",
            "prompt_history": [
                {"role": "user", "content": "Build a surfboard landing page"},
                {"role": "user", "content": "Change colors to ocean blues"}
            ]
        }
    """
    global execution_state

    if execution_state["running"]:
        return jsonify({"error": "A pipeline is already running"}), 409

    session = get_session()
    try:
        data = request.get_json()
        if not data or not data.get("prompt"):
            return jsonify({"error": "prompt is required"}), 400

        project = session.query(Project).get(project_id)
        if not project:
            return jsonify({"error": f"Project {project_id} not found"}), 404

        prompt = data["prompt"]
        # Full conversation history including this new prompt
        prompt_history = data.get("prompt_history", [])
        if not prompt_history:
            prompt_history = [{"role": "user", "content": prompt}]

        # Find the current active head to use as parent
        current_head = (
            session.query(Execution)
            .filter(
                Execution.project_id == project_id,
                Execution.is_active_head == True,
            )
            .first()
        )

        # Deactivate the current head — the new version becomes the head
        if current_head:
            current_head.is_active_head = False
            session.commit()

        # Create new versioned execution
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

        # Update project status
        project.status = "in_progress"
        project.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(execution)

        # Clear previous result file
        result_file = PUBLIC_DIR / "last_execution_result.json"
        if result_file.exists():
            result_file.unlink()

        execution_state["running"] = True
        execution_state["started_at"] = time.time()
        execution_state["current_project_id"] = project_id
        execution_state["current_execution_id"] = execution.id
        execution_state["logs"] = []

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
    """
    Restore a past version by setting it as the active HEAD.

    - Sets is_active_head=True for this execution
    - Sets is_active_head=False for all other executions in the same project
    - Does NOT delete any versions (forward-restore stays possible)
    """
    session = get_session()
    try:
        execution = session.query(Execution).get(execution_id)
        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        project_id = execution.project_id

        # Deactivate all versions in this project
        session.query(Execution).filter(
            Execution.project_id == project_id
        ).update({"is_active_head": False})

        # Set this version as the active head
        execution.is_active_head = True

        # Update project updated_at so the Projects list reflects the restore
        project = session.query(Project).get(project_id)
        if project:
            project.updated_at = datetime.utcnow()

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
    """
    Start a brand-new project execution (first run / v1).
    For subsequent iterations use POST /api/projects/:id/iterate instead.
    """
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
            project = session.query(Project).get(project_id)
            if not project:
                return jsonify({"error": f"Project {project_id} not found"}), 404
            project.status = "in_progress"
            project.updated_at = datetime.utcnow()
            session.commit()

        # First execution for this project is always v1
        next_version = get_next_version(session, project_id)
        task_description = project.description or project.name
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

        result_file = PUBLIC_DIR / "last_execution_result.json"
        if result_file.exists():
            result_file.unlink()

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
    result_file = PUBLIC_DIR / "last_execution_result.json"
    data = read_json_file(result_file)

    STATUS_MAP = {
        "success": "COMPLETED", "error": "FAILED",
        "completed": "COMPLETED", "failed": "FAILED",
        "pending": "RUNNING", "running": "RUNNING",
    }

    logs = execution_state.get("logs", [])
    current_stage = "pm"
    for log in reversed(logs):
        msg = log.get("message", "")
        if "Build Agent" in msg:
            current_stage = "engineer"
            break
        if "Architecture Agent" in msg:
            current_stage = "planner"
            break

    if data is not None:
        raw_status = str(data.get("status", "success")).lower()
        frontend_status = STATUS_MAP.get(raw_status, "COMPLETED")
        return jsonify({
            "status": frontend_status,
            "currentStage": "complete",
            "logs": logs,
            "engineerTasks": [],
            "execution_id": execution_state.get("current_execution_id"),
        }), 200

    if execution_state["running"]:
        return jsonify({
            "status": "RUNNING",
            "currentStage": current_stage,
            "logs": logs,
            "engineerTasks": [],
            "project_id": execution_state.get("current_project_id"),
            "execution_id": execution_state.get("current_execution_id"),
        }), 200

    return jsonify({
        "status": "FAILED",
        "currentStage": "complete",
        "logs": logs,
        "engineerTasks": [],
        "message": "No execution result available",
    }), 200


@app.route("/api/code", methods=["GET"])
def get_code():
    result_file = PUBLIC_DIR / "last_execution_result.json"
    data = read_json_file(result_file)
    if data is None:
        return jsonify({"error": "No execution result available"}), 404
    return jsonify(data), 200


@app.route("/api/plan", methods=["GET"])
def get_plan():
    plan_file = PUBLIC_DIR / "last_plan.json"
    data = read_json_file(plan_file)
    if data is None:
        return jsonify({"error": "Plan not found"}), 404
    return jsonify(data), 200


@app.route("/api/prd", methods=["GET"])
def get_prd():
    prd_file = PUBLIC_DIR / "last_prd.json"
    data = read_json_file(prd_file)
    if data is None:
        return jsonify({"error": "PRD not found"}), 404
    return jsonify(data), 200


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    init_db()
    print(f"Flask server starting...")
    print(f"REPO_ROOT: {REPO_ROOT}")
    print(f"PUBLIC_DIR: {PUBLIC_DIR}")
    print(f"CORS enabled for: http://localhost:5173, http://localhost:3000")
    app.run(debug=True, port=5000)
