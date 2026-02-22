from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any


class LayoutRegion(BaseModel):
    row: Optional[int] = None
    component: Optional[str] = None
    count: Optional[int] = None
    aspect_ratio: Optional[str] = None
    left: Optional[str] = None
    right: Optional[str] = None
    ratio: Optional[str] = None


class SidebarSpec(BaseModel):
    width_px: Optional[int] = None
    nav_groups: Optional[int] = None
    icons_required: Optional[bool] = None


class LayoutContract(BaseModel):
    regions: List[str] = Field(default_factory=list)
    sidebar: Optional[SidebarSpec] = None
    topbar: List[str] = Field(default_factory=list)
    main_grid: List[LayoutRegion] = Field(default_factory=list)
    density: Optional[str] = None


class ContentContract(BaseModel):
    kpi_labels: List[str] = Field(default_factory=list)
    table_columns: List[str] = Field(default_factory=list)
    seed_rows: int = 5
    required_states: List[str] = Field(default_factory=list)


class ArchetypeRules(BaseModel):
    required_blocks: List[str] = Field(default_factory=list)
    required_interactions: List[str] = Field(default_factory=list)
    avoid: List[str] = Field(default_factory=list)
    layout_contract: Optional[LayoutContract] = None
    content_contract: Optional[ContentContract] = None


class Task(BaseModel):
    id: str = Field(..., description="Unique task id like PLAN-1, BE-1, FE-3")
    description: str = Field(..., description="Concrete, executable task in one sentence")
    depends_on: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(...)

    execution_hint: Literal["engineer", "defer"] = Field(default="defer")
    task_type: Optional[Literal["scaffold", "single_file", "doc"]] = Field(default=None)
    output_files: Optional[List[str]] = Field(default=None)
    ui_archetype: Optional[Literal["dashboard", "landing", "ecommerce", "kanban", "chat", "editor", "feed", "form", "game", "portfolio"]] = Field(default=None)
    archetype_rules: Optional[ArchetypeRules] = Field(default=None)

    def model_post_init(self, __context) -> None:
        if self.execution_hint == "engineer" and self.task_type is None:
            raise ValueError("task_type must be set when execution_hint='engineer'")


class Milestone(BaseModel):
    name: str
    tasks: List[Task]


class Plan(BaseModel):
    milestones: List[Milestone]
    assumptions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
