from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    """
    Keep this permissive on purpose:
    - The UI may evolve fields (schema drift), but we must keep writing artifacts.
    - We validate the minimum needed to make the artifact useful to the orchestrator.
    """
    kind: str = Field(default="execution_request")
    task_id: str
    milestone_id: str | None = None
    title: str | None = None
    created_at: str | None = None  # ISO string preferred
    payload: Dict[str, Any] = Field(default_factory=dict)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_within_dir(target: Path, base_dir: Path) -> None:
    """
    Hard safety: only allow writes inside the allowlisted public/ directory.
    """
    base = base_dir.resolve()
    t = target.resolve()
    if base not in t.parents and t != base:
        raise HTTPException(status_code=400, detail="Refusing to write outside allowlisted public/ directory")


def atomic_write_text(path: Path, text: str) -> None:
    """
    Deterministic + safe overwrite:
    - write temp file in same dir, fsync, then replace
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def append_ndjson(path: Path, line_obj: Dict[str, Any]) -> None:
    """
    Append-only NDJSON log. Ensures exactly one JSON object per line.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(line_obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def get_public_dir() -> Path:
    # server/ is at apps/offline-vite-react/server, so public/ is one level up
    return (Path(__file__).parent.parent / "public").resolve()


PUBLIC_DIR = get_public_dir()
LAST_REQ_PATH = (PUBLIC_DIR / "last_execution_request.json").resolve()
LOG_PATH = (PUBLIC_DIR / "execution_requests.ndjson").resolve()

app = FastAPI(title="ai-dev-team local artifact server", version="0.1.0")

# Dev-only CORS: allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "service": "artifact-writer",
        "public_dir": str(PUBLIC_DIR),
    }


@app.post("/execution-request")
async def execution_request(req: ExecutionRequest, request: Request) -> Dict[str, Any]:
    # Ensure allowlisted paths
    ensure_within_dir(LAST_REQ_PATH, PUBLIC_DIR)
    ensure_within_dir(LOG_PATH, PUBLIC_DIR)

    # Enrich deterministically (without mutating caller payload in weird ways)
    obj = req.model_dump()
    if not obj.get("created_at"):
        obj["created_at"] = utc_now_iso()

    # Include a minimal request fingerprint for debugging (not security)
    obj["_meta"] = {
        "source_ip": request.client.host if request.client else None,
        "received_at": utc_now_iso(),
    }

    pretty = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    atomic_write_text(LAST_REQ_PATH, pretty)
    append_ndjson(LOG_PATH, obj)

    return {"ok": True, "written": {"last": str(LAST_REQ_PATH), "log": str(LOG_PATH)}}
