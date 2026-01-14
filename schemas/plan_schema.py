from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List


class Task(BaseModel):
    id: str = Field(..., description="Unique task id like PLAN-1, BE-1, FE-3")
    description: str = Field(..., description="Concrete, executable task in one sentence")
    depends_on: List[str] = Field(default_factory=list, description="List of task ids this task depends on")
    outputs: List[str] = Field(..., description="Artifacts produced, e.g., 'FastAPI scaffold', 'DB schema draft'")


class Milestone(BaseModel):
    name: str = Field(..., description="Milestone name, e.g., 'Backend scaffold'")
    tasks: List[Task]


class Plan(BaseModel):
    milestones: List[Milestone]
    assumptions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
