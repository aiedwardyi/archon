from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class FileArtifact(BaseModel):
    path: str = Field(..., description="Repo-relative path like README.md or src/__init__.py")
    content: str = Field(..., description="Full file contents")


class EngineeringSelfReviewScores(BaseModel):
    spacing_layout: int = Field(..., ge=1, le=10)
    typography: int = Field(..., ge=1, le=10)
    color_depth: int = Field(..., ge=1, le=10)
    interactivity: int = Field(..., ge=1, le=10)
    content_authenticity: int = Field(..., ge=1, le=10)
    polish_flow: int = Field(..., ge=1, le=10)


class EngineeringSelfReview(BaseModel):
    scores: EngineeringSelfReviewScores
    weak_dimensions: List[str] = Field(default_factory=list)
    next_pass: str = Field(..., description="Short note describing the highest-leverage follow-up fix")


class EngineeringChangeManifest(BaseModel):
    preserved: List[str] = Field(default_factory=list)
    modified: List[str] = Field(default_factory=list)
    added: List[str] = Field(default_factory=list)
    regression_checks: List[str] = Field(default_factory=list)


class EngineeringResult(BaseModel):
    task_id: str = Field(..., description="Planner task id this corresponds to")
    summary: str = Field(..., description="Short summary of what was generated")
    files: List[FileArtifact] = Field(default_factory=list, description="Files to write to disk")
    self_review: Optional[EngineeringSelfReview] = Field(
        default=None,
        description="Model-reported quality review for componentized app outputs",
    )
    change_manifest: Optional[EngineeringChangeManifest] = Field(
        default=None,
        description="Iteration-only record of what was preserved, modified, added, and regression-checked",
    )
    usage: Optional[dict] = Field(default=None, exclude=True)
