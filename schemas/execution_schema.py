from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ExecutionRequestMeta(BaseModel):
    source_ip: Optional[str] = None
    received_at: Optional[str] = None


class ExecutionRequest(BaseModel):
    kind: str = Field(default="execution_request")
    task_id: str
    milestone_id: Optional[str] = None
    title: Optional[str] = None
    created_at: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    _meta: Optional[ExecutionRequestMeta] = None


class ExecutionResultMeta(BaseModel):
    produced_at: Optional[str] = None
    consumer_version: Optional[str] = None


class ExecutionResult(BaseModel):
    kind: str = Field(default="execution_result")
    status: str  # "success" | "error"
    request_hash: str

    # Keep a copy of the original request for audit/debugging.
    request: ExecutionRequest

    # Minimal deterministic outputs for now.
    outputs: Dict[str, Any] = Field(default_factory=dict)

    # Optional error details (artifact-visible failures)
    error: Optional[Dict[str, Any]] = None

    # Non-deterministic / informational metadata lives here.
    _meta: Optional[ExecutionResultMeta] = None
