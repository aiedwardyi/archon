from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationResultMeta(BaseModel):
    produced_at: Optional[str] = None
    evaluator_version: Optional[str] = None


class EvaluationResult(BaseModel):
    kind: str = Field(default="evaluation_result")

    # pass | fail
    status: str

    # Reference to the execution result being evaluated.
    request_hash: str

    # Machine-checkable explanation strings (no LLM judgment).
    reasons: List[str] = Field(default_factory=list)

    # Structured check signals (booleans and small scalars only).
    checks: Dict[str, Any] = Field(default_factory=dict)

    # Non-deterministic / informational metadata lives here.
    _meta: Optional[EvaluationResultMeta] = None