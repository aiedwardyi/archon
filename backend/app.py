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

from models import Project, Execution, get_session, init_db

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


def run_full_pipeline_async(task_description: str):
    """
    Run the full PM → Planner → Engineer pipeline in a background thread.
    This replaces the old consumer-only approach with the real multi-agent flow.
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
        # STEP 1: PM Agent → PRD
        # =====================================================================
        add_log("Starting execution pipeline...", "system")
        add_log("PM Agent: Analyzing requirements...", "info")

        from agents.pm_agent import PMAgent
        pm_agent = PMAgent()
        prd_artifact = pm_agent.generate_prd(task_description)

        prd_dict = prd_artifact.model_dump()
        prd_dict["_agent_sequence"] = ["pm"]
        write_json_file(PUBLIC_DIR / "last_prd.json", prd_dict)

        add_log("PM Agent: PRD generated successfully.", "success")
        print(f"✅ PRD saved: {prd_artifact.prd.document_title}")

        # =====================================================================
        # STEP 2: Planner Agent → Plan
        # =====================================================================
        add_log("Planner Agent: Architecting solution...", "info")

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
        # Also write the flat plan format the consumer expects
        flat_plan = plan.model_dump()
        write_json_file(PUBLIC_DIR / "last_plan.json", flat_plan)
        write_json_file(PUBLIC_DIR / "last_plan_artifact.json", plan_dict)

        add_log("Planner Agent: Execution plan created.", "success")
        milestone_count = len(plan.milestones)
        task_count = sum(len(m.tasks) for m in plan.milestones)
        print(f"✅ Plan saved: {milestone_count} milestones, {task_count} tasks")

        # =====================================================================
        # STEP 3: Engineer Agent → Code
        # Pick the first engineer task from the plan
        # =====================================================================
        add_log("Engineer Agent: Writing code...", "info")

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

        # Write generated files
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
            add_log(f"Engineer Agent: Completed {file_artifact.path}", "success")

        add_log("Engineer Agent: Code generation complete.", "success")

        # Build and save execution result
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

        add_log("Workflow completed successfully.", "success")
        print(f"✅ Execution result saved: {len(writes)} files generated")

        # Update database
        if execution_id:
            execution = session.query(Execution).get(execution_id)
            if execution:
                execution.status = "success"
                execution.result_path = "last_execution_result.json"
                session.commit()
                project = execution.project
                if project:
                    project.status = "completed"
                    project.updated_at = datetime.utcnow()
                    session.commit()

    except Exception as e:
        error_msg = str(e)
        add_log(f"Error: {error_msg}", "error")
        print(f"❌ Pipeline error: {error_msg}")

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

        # Write error result so frontend stops polling
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
        print(f"🏁 Pipeline complete")


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
            project = session.query(Project).get(project_id)
            if not project:
                return jsonify({"error": f"Project {project_id} not found"}), 404
            project.status = "in_progress"
            project.updated_at = datetime.utcnow()
            session.commit()

        execution = Execution(project_id=project_id, status="pending")
        session.add(execution)
        session.commit()
        session.refresh(execution)

        # Clear previous result and logs
        result_file = PUBLIC_DIR / "last_execution_result.json"
        if result_file.exists():
            result_file.unlink()

        execution_state["running"] = True
        execution_state["started_at"] = time.time()
        execution_state["current_project_id"] = project_id
        execution_state["current_execution_id"] = execution.id
        execution_state["logs"] = []

        # Use full project description as task description if available
        task_description = project.description or project.name

        print(f"🚀 Starting full pipeline for: {task_description}")
        thread = threading.Thread(
            target=run_full_pipeline_async,
            args=(task_description,),
            daemon=True
        )
        thread.start()

        return jsonify({
            "status": "started",
            "project_id": project_id,
            "execution_id": execution.id,
        }), 200

    except Exception as e:
        execution_state["running"] = False
        print(f"❌ Error in execute_task: {e}")
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

    # Derive current stage from live logs
    logs = execution_state.get("logs", [])
    current_stage = "pm"
    for log in reversed(logs):
        msg = log.get("message", "")
        if "Engineer" in msg:
            current_stage = "engineer"
            break
        if "Planner" in msg:
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
        elapsed = time.time() - (execution_state["started_at"] or 0)
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
