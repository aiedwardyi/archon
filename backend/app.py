from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict
import threading
import time

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
    "started_at": None
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
    
    try:
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
        
        if result.returncode != 0:
            print(f"❌ Consumer failed with exit code {result.returncode}")
        else:
            print(f"✅ Consumer completed successfully")
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ Consumer script timed out")
    except Exception as e:
        print(f"❌ Error running consumer: {e}")
    finally:
        execution_state["running"] = False
        print(f"🏁 Execution state set to: running=False")


@app.route("/api/execute-task", methods=["POST"])
def execute_task():
    """
    Receives execution request from UI, saves to file, triggers consumer script ASYNCHRONOUSLY.
    
    Expected payload includes _agent_sequence from Plan artifact.
    """
    global execution_state
    
    try:
        req_data = request.get_json()
        
        if not req_data:
            return jsonify({"error": "No JSON payload provided"}), 400
        
        # Save execution request to file
        request_file = PUBLIC_DIR / "last_execution_request.json"
        success = write_json_file(request_file, req_data)
        
        if not success:
            return jsonify({"error": "Failed to write execution request file"}), 500
        
        print(f"✅ Saved execution request to: {request_file}")
        
        # Clear previous result to avoid showing stale data
        result_file = PUBLIC_DIR / "last_execution_result.json"
        if result_file.exists():
            result_file.unlink()
            print(f"🗑️ Cleared previous execution result")
        
        # Mark execution as running
        execution_state["running"] = True
        execution_state["started_at"] = time.time()
        print(f"🏁 Execution state set to: running=True")
        
        # Trigger consumer script in background thread
        thread = threading.Thread(target=run_consumer_async, daemon=True)
        thread.start()
        print(f"🔄 Consumer thread started")
        
        # Return immediately - UI will poll for completion
        return jsonify({
            "status": "started",
            "message": "Task execution started in background",
            "request_file": str(request_file.relative_to(REPO_ROOT))
        }), 200
        
    except Exception as e:
        execution_state["running"] = False
        print(f"❌ Error in execute_task: {e}")
        return jsonify({"error": str(e)}), 500


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
            "elapsed_seconds": int(elapsed)
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
    print(f"Flask server starting...")
    print(f"REPO_ROOT: {REPO_ROOT}")
    print(f"PUBLIC_DIR: {PUBLIC_DIR}")
    print(f"CORS enabled for: http://localhost:5173")
    app.run(debug=True, port=5000)
