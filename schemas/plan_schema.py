from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class ArchetypeRules(BaseModel):
    required_blocks: List[str] = Field(default_factory=list)
    required_interactions: List[str] = Field(default_factory=list)
    avoid: List[str] = Field(default_factory=list)


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
    ui_archetype: Optional[Literal["dashboard", "landing", "ecommerce", "kanban", "chat", "editor", "feed", "form", "game", "portfolio"]] = Field(
        default=None,
        description="UI shell the Engineer MUST use. Set by Planner on scaffold tasks only."
    )
    archetype_rules: Optional[ArchetypeRules] = Field(
        default=None,
        description="Required blocks, interactions, and elements to avoid. Enforced by Engineer."
    )

    def model_post_init(self, __context) -> None:
        if self.execution_hint == "engineer" and self.task_type is None:
            raise ValueError("task_type must be set when execution_hint='engineer'")


class Milestone(BaseModel):
    name: str = Field(..., description="Milestone name, e.g., 'Backend scaffold'")
    tasks: List[Task]


class Plan(BaseModel):
    milestones: List[Milestone]
    assumptions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
