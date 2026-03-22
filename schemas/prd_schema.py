from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field


class PRD(BaseModel):
    """
    Product Requirement Document schema.
    Matches the structure from ai-requirement-translator but as a Pydantic model.
    """
    document_title: str = Field(..., description="Project name")
    version: str = Field(default="0.1", description="Document version")
    detected_intent: str = Field(default="", description="Short summary of the core product intent")
    archetype_hint: str = Field(default="", description="Most likely UI archetype inferred from the request")
    primary_user_action: str = Field(default="", description="The main action users take in the product")
    visual_direction: str = Field(default="", description="Specific design direction for this build")
    tone_keywords: List[str] = Field(default_factory=list, description="Concise tone/style keywords")
    prompt_quality_score: int = Field(default=0, description="How specific and actionable the request is, 0-100")
    overview: str = Field(..., description="High-level description")
    goals: List[str] = Field(..., description="Success criteria")
    non_goals: List[str] = Field(..., description="Explicit exclusions")
    target_users: List[str] = Field(..., description="User personas")
    core_features_mvp: List[str] = Field(..., description="Essential features")
    nice_to_have_features: List[str] = Field(..., description="Optional enhancements")
    user_stories: List[str] = Field(..., description="User-centric requirements")
    acceptance_criteria: List[str] = Field(..., description="Definition of done")
    technical_stack_recommendation: List[str] = Field(..., description="Suggested technologies")
    payments_security_compliance: List[str] = Field(..., description="Regulatory considerations")
    assumptions: List[str] = Field(..., description="Development constraints")
    open_questions: List[str] = Field(..., description="Client clarifications needed")
    regenerate_images: bool = Field(default=True, description="Whether to generate new images for this build")



class PRDArtifact(BaseModel):
    """
    Wrapper for PRD that matches the Archon artifact pattern.
    """
    kind: str = Field(default="prd_artifact")
    agent_role: str = Field(default="pm")
    prd: PRD
    created_at: str


