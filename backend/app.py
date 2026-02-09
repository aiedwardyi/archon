from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict
import threading
import time
from datetime import datetime

# Import database models
from models import Project, Execution, get_session, init_db

app = Flask(__name__)

# Enable CORS for Vite dev server
CORS(app, origins=["http://localhost:5173"])

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = REPO_ROOT / "apps" / "offline-vite-react" / "public"
CONSUMER_SCRIPT = REPO_ROOT / "scripts" / "consume_execution_request.py"

# Track running execution
execution_state = {
    "running": False,
    "started_at": None,
    "current_project_id": None,
    "current_execution_id": None,
}


def read_json_file(filepath: Path) -> Dict[str, Any] | None:
    """Read JSON file, return None if missing or invalid."""
    try:
        if not filepath.exists():
            return None
        return json.loads(filepath.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None


def write_json_file(filepath: Path, data: Dict[str, Any]) -> bool:
    """Write JSON file atomically."""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        tmp = filepath.with_suffix(filepath.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(filepath)
        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}")
        return False


def run_consumer_async():
    """Run consumer script in background thread."""
    global execution_state
    
    session = get_session()
    execution_id = execution_state.get("current_execution_id")
    
    try:
        # Update execution status to running
        if execution_id:
            execution = session.query(Execution).get(execution_id)
            if execution:
                execution.status = "running"
                session.commit()
        
        print(f"🚀 Starting consumer script (async)...")
        result = subprocess.run(
            [sys.executable, "-m", "scripts.consume_execution_request"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        print(f"📤 Consumer stdout: {result.stdout}")
        if result.stderr:
            print(f"⚠️ Consumer stderr: {result.stderr}")
        
        # Update execution status based on result
        if execution_id:
            execution = session.query(Execution).get(execution_id)
            if execution:
                if result.returncode != 0:
                    execution.status = "error"
                    execution.error_message = f"Consumer exit code {result.returncode}: {result.stderr}"
                    print(f"❌ Consumer failed with exit code {result.returncode}")
                else:
                    execution.status = "success"
                    print(f"✅ Consumer completed successfully")
                
                # Update result path
                result_file = PUBLIC_DIR / "last_execution_result.json"
                if result_file.exists():
                    execution.result_path = str(result_file.relative_to(PUBLIC_DIR))
                
                session.commit()
                
                # Update project status
                project = execution.project
                if project:
                    project.status = "completed" if execution.status == "success" else "failed"
                    project.updated_at = datetime.utcnow()
                    session.commit()
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ Consumer script timed out")
        if execution_id:
            execution = session.query(Execution).get(execution_id)
            if execution:
                execution.status = "error"
                execution.error_message = "Execution timed out after 60 seconds"
                session.commit()
    except Exception as e:
        print(f"❌ Error running consumer: {e}")
        if execution_id:
            execution = session.query(Execution).get(execution_id)
            if execution:
                execution.status = "error"
                execution.error_message = str(e)
                session.commit()
    finally:
        execution_state["running"] = False
        execution_state["current_execution_id"] = None
        session.close()
        print(f"🏁 Execution state set to: running=False")


# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

@app.route("/api/projects", methods=["GET"])
def list_projects():
    """List all projects."""
    session = get_session()
    try:
        projects = session.query(Project).order_by(Project.updated_at.desc()).all()
        return jsonify([p.to_dict() for p in projects]), 200
    finally:
        session.close()


@app.route("/api/projects", methods=["POST"])
def create_project():
    """Create a new project."""
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
    """Get project details with execution history."""
    session = get_session()
    try:
        project = session.query(Project).get(project_id)
        
        if not project:
            return jsonify({"error": "Project not found"}), 404
        
        # Include executions
        project_dict = project.to_dict()
        project_dict["executions"] = [e.to_dict() for e in project.executions]
        
        return jsonify(project_dict), 200
    finally:
        session.close()


@app.route("/api/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id: int):
    """Delete a project and all its executions."""
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
# EXECUTION ENDPOINTS (Updated)
# ============================================================================

@app.route("/api/execute-task", methods=["POST"])
def execute_task():
    """
    Receives execution request from UI, creates execution record, saves to file,
    triggers consumer script ASYNCHRONOUSLY.
    
    Expected payload includes _agent_sequence from Plan artifact and project_id.
    """
    global execution_state
    
    session = get_session()
    
    try:
        req_data = request.get_json()
        
        if not req_data:
            return jsonify({"error": "No JSON payload provided"}), 400
        
        # Get or create project
        project_id = req_data.get("project_id")
        
        if not project_id:
            # Auto-create "Untitled Project" if none specified
            project = Project(
                name="Untitled Project",
                description="Auto-created project",
                status="in_progress",
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            project_id = project.id
            print(f"📁 Auto-created project: {project.name} (ID: {project_id})")
        else:
            # Verify project exists
            project = session.query(Project).get(project_id)
            if not project:
                return jsonify({"error": f"Project {project_id} not found"}), 404
            
            # Update project status
            project.status = "in_progress"
            project.updated_at = datetime.utcnow()
            session.commit()
        
        # Create execution record
        execution = Execution(
            project_id=project_id,
            status="pending",
        )
        session.add(execution)
        session.commit()
        session.refresh(execution)
        
        print(f"📝 Created execution record: ID {execution.id} for project {project_id}")
        
        # Save execution request to file
        request_file = PUBLIC_DIR / "last_execution_request.json"
        success = write_json_file(request_file, req_data)
        
        if not success:
            execution.status = "error"
            execution.error_message = "Failed to write execution request file"
            session.commit()
            return jsonify({"error": "Failed to write execution request file"}), 500
        
        # Update execution with request path
        execution.request_path = str(request_file.relative_to(PUBLIC_DIR))
        session.commit()
        
        print(f"✅ Saved execution request to: {request_file}")
        
        # Clear previous result to avoid showing stale data
        result_file = PUBLIC_DIR / "last_execution_result.json"
        if result_file.exists():
            result_file.unlink()
            print(f"🗑️ Cleared previous execution result")
        
        # Mark execution as running
        execution_state["running"] = True
        execution_state["started_at"] = time.time()
        execution_state["current_project_id"] = project_id
        execution_state["current_execution_id"] = execution.id
        print(f"🏁 Execution state set to: running=True, project={project_id}, execution={execution.id}")
        
        # Trigger consumer script in background thread
        thread = threading.Thread(target=run_consumer_async, daemon=True)
        thread.start()
        print(f"🔄 Consumer thread started")
        
        # Return immediately - UI will poll for completion
        return jsonify({
            "status": "started",
            "message": "Task execution started in background",
            "project_id": project_id,
            "execution_id": execution.id,
            "request_file": str(request_file.relative_to(REPO_ROOT))
        }), 200
        
    except Exception as e:
        execution_state["running"] = False
        print(f"❌ Error in execute_task: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/execution-status", methods=["GET"])
def execution_status():
    """Returns latest execution result, with proper handling of pending state."""
    result_file = PUBLIC_DIR / "last_execution_result.json"
    data = read_json_file(result_file)
    
    # If result exists, return it
    if data is not None:
        print(f"📥 Returning execution result with status: {data.get('status')}")
        return jsonify(data), 200
    
    # If no result but execution is running, return pending
    if execution_state["running"]:
        elapsed = time.time() - (execution_state["started_at"] or 0)
        print(f"⏳ Execution still running (elapsed: {elapsed:.1f}s)")
        return jsonify({
            "status": "pending",
            "message": "Execution in progress",
            "elapsed_seconds": int(elapsed),
            "project_id": execution_state.get("current_project_id"),
            "execution_id": execution_state.get("current_execution_id"),
        }), 200
    
    # No result and not running - this shouldn't happen normally
    print(f"❓ No result found and execution not running")
    return jsonify({
        "status": "unknown",
        "message": "No execution result available"
    }), 200


@app.route("/api/plan", methods=["GET"])
def get_plan():
    """Returns current plan artifact."""
    plan_file = PUBLIC_DIR / "last_plan.json"
    data = read_json_file(plan_file)
    
    if data is None:
        return jsonify({"error": "Plan not found"}), 404
    
    return jsonify(data), 200


@app.route("/api/prd", methods=["GET"])
def get_prd():
    """Returns current PRD artifact."""
    prd_file = PUBLIC_DIR / "last_prd.json"
    data = read_json_file(prd_file)
    
    if data is None:
        return jsonify({"error": "PRD not found"}), 404
    
    return jsonify(data), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Initialize database on startup
    init_db()
    
    print(f"Flask server starting...")
    print(f"REPO_ROOT: {REPO_ROOT}")
    print(f"PUBLIC_DIR: {PUBLIC_DIR}")
    print(f"CORS enabled for: http://localhost:5173")
    app.run(debug=True, port=5000)
