from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class FileArtifact(BaseModel):
    path: str = Field(..., description="Repo-relative path like README.md or src/__init__.py")
    content: str = Field(..., description="Full file contents")


class EngineeringResult(BaseModel):
    task_id: str = Field(..., description="Planner task id this corresponds to")
    summary: str = Field(..., description="Short summary of what was generated")
    files: List[FileArtifact] = Field(default_factory=list, description="Files to write to disk")
