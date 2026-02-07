from __future__ import annotations
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add repo root to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from google import genai
from agents.engineer_agent import EngineerAgent
from schemas.plan_schema import Task
from scripts.safe_write import WriteRecord, safe_write_text


def execute(
    *,
    public_dir: Path,
    request_hash: str,
    task_id: str,
    payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[WriteRecord]]:
    """
    Deterministic task execution.
    
    Supports:
    - task_snapshot: Execute Engineer agent with Task from Plan
    - action: "write_public_note" (legacy simple note writing)
    
    All writes are allow-listed under: <public_dir>/generated/
    """
    writes: List[WriteRecord] = []
    allow_dir = public_dir / "generated"
    
    # NEW: Handle task execution via Engineer agent
    if "task_snapshot" in payload:
        task_data = payload["task_snapshot"]
        
        # Validate it's an engineer task
        if task_data.get("execution_hint") != "engineer":
            raise ValueError(
                f"Task {task_id} has execution_hint='{task_data.get('execution_hint')}', "
                "but only 'engineer' tasks can be executed"
            )
        
        # Create Task object
        task = Task.model_validate(task_data)
        
        # Initialize Engineer agent
        import os
        genai_key = os.getenv("GENAI_API_KEY")
        if not genai_key:
            raise ValueError("GENAI_API_KEY environment variable not set")
        
        genai_client = genai.Client(api_key=genai_key)
        engineer = EngineerAgent(genai_client)
        
        # Execute task
        result = engineer.run(task)
        
        # Write generated files
        for file_artifact in result.files:
            rec = safe_write_text(
                allowlist_dir=allow_dir,
                relative_path=file_artifact.path,
                content=file_artifact.content,
            )
            writes.append(rec)
        
        # Build outputs
        outputs = {
            "action": "engineer_execution",
            "task_id": task_id,
            "summary": result.summary,
            "files_generated": len(result.files),
            "writes": [
                {"path": rec.path, "sha256": rec.sha256, "bytes": rec.bytes}
                for rec in writes
            ],
        }
        
        return outputs, writes
    
    # LEGACY: Simple note writing
    action = payload.get("action") or "write_public_note"
    
    if action == "write_public_note":
        content = payload.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("payload.content must be a non-empty string for action=write_public_note")
        
        filename = payload.get("filename")
        if not isinstance(filename, str) or not filename.strip():
            filename = f"{task_id}-{request_hash[:12]}.md"
        
        rec = safe_write_text(
            allowlist_dir=allow_dir,
            relative_path=filename,
            content=content,
        )
        writes.append(rec)
        
        outputs = {
            "action": action,
            "note_path": rec.path,
            "note_sha256": rec.sha256,
            "note_bytes": rec.bytes,
            "writes": [{"path": rec.path, "sha256": rec.sha256, "bytes": rec.bytes}],
        }
        
        return outputs, writes
    
    raise ValueError(f"Unsupported action: {action}")
