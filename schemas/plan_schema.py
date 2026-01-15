from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Task(BaseModel):
    id: str = Field(..., description="Unique task id like PLAN-1, BE-1, FE-3")
    description: str = Field(..., description="Concrete, executable task in one sentence")
    depends_on: List[str] = Field(default_factory=list, description="List of task ids this task depends on")
    outputs: List[str] = Field(..., description="Artifacts produced, e.g., 'FastAPI scaffold', 'DB schema draft'")

    execution_hint: Literal["engineer", "defer"] = Field(
        default="defer",
        description="If 'engineer', orchestrator may route this task to Engineer Agent. Otherwise it is skipped for now."
    )
    task_type: Optional[Literal["scaffold", "single_file", "doc"]] = Field(
        default=None,
        description="Execution mode for Engineer Agent when execution_hint='engineer'."
    )
    output_files: Optional[List[str]] = Field(
        default=None,
        description="Optional list of file paths Engineer should produce (constraints/testing)."
    )

    def model_post_init(self, __context) -> None:
        # Safety rail: executable tasks must declare a type
        if self.execution_hint == "engineer" and self.task_type is None:
            raise ValueError("task_type must be set when execution_hint='engineer'")



class Milestone(BaseModel):
    name: str = Field(..., description="Milestone name, e.g., 'Backend scaffold'")
    tasks: List[Task]


class Plan(BaseModel):
    milestones: List[Milestone]
    assumptions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
