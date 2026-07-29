from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict

from schemas.plan_schema import Milestone, Plan, QualityTarget, Task
from schemas.prd_schema import PRD, PRDArtifact


_ARCHETYPE_HINTS = (
    ("dashboard", ("dashboard", "analytics", "report", "metrics")),
    ("ecommerce", ("shop", "store", "commerce", "catalog")),
    ("portfolio", ("portfolio", "resume", "showcase")),
    ("kanban", ("kanban", "task", "project board")),
    ("chat", ("chat", "messaging", "assistant")),
    ("form", ("form", "survey", "application")),
)


def is_offline_mode() -> bool:
    return os.getenv("OFFLINE_MODE", "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _offline_archetype(idea: str) -> str:
    normalized = idea.lower()
    for archetype, hints in _ARCHETYPE_HINTS:
        if any(hint in normalized for hint in hints):
            return archetype
    return "landing"


def _offline_title(idea: str) -> str:
    normalized = " ".join(idea.split())
    lowered = normalized.lower()
    for prefix in ("build a ", "build an ", "create a ", "create an ", "make a ", "make an "):
        if lowered.startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    title = normalized.split(" with ", 1)[0].split(" that ", 1)[0].strip(" .")
    if not title:
        return "Archon Offline Project"
    return title[:1].upper() + title[1:72]


def build_offline_prd_artifact(idea: str) -> PRDArtifact:
    title = _offline_title(idea)
    archetype = _offline_archetype(idea)
    return PRDArtifact(
        prd=PRD(
            document_title=title,
            detected_intent=idea.strip(),
            archetype_hint=archetype,
            primary_user_action="Explore the generated application preview",
            visual_direction="Clean product interface with strong hierarchy, restrained color, and responsive spacing",
            tone_keywords=["clear", "focused", "responsive"],
            prompt_quality_score=min(100, max(40, len(idea.strip()))),
            overview=f"A provider-free preview scaffold for: {idea.strip()}",
            goals=["Produce a buildable application", "Demonstrate the complete local pipeline"],
            non_goals=["Production model output", "External image generation"],
            target_users=["Project owners", "Contributors"],
            core_features_mvp=["Responsive layout", "Visible pipeline status", "Buildable React workspace"],
            nice_to_have_features=["Live provider-backed generation"],
            user_stories=[
                "As a contributor, I can verify the pipeline without provider credentials.",
                "As a project owner, I can open a generated preview after one local run.",
            ],
            acceptance_criteria=[
                "The generated workspace builds successfully.",
                "The preview route returns the generated application.",
            ],
            technical_stack_recommendation=["React", "TypeScript", "Vite"],
            payments_security_compliance=["No external data is transmitted in offline mode"],
            assumptions=["Node.js dependencies are available during the first generated build"],
            open_questions=[],
            regenerate_images=False,
        ),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def build_offline_plan(idea: str, locked_ui_archetype: str | None = None) -> Plan:
    archetype = locked_ui_archetype or _offline_archetype(idea)
    return Plan(
        milestones=[
            Milestone(
                name="Generate local preview",
                tasks=[
                    Task(
                        id="OFFLINE-1",
                        description=f"Build a complete React application scaffold for: {idea.strip()}",
                        outputs=["Buildable Vite, React, and TypeScript workspace"],
                        execution_hint="engineer",
                        task_type="scaffold",
                        scaffold_mode="componentized_app",
                        output_files=["package.json", "index.html", "src/main.tsx", "src/App.tsx"],
                        ui_archetype=archetype,
                        render_path="C",
                        quality_target=QualityTarget(
                            visual_style="Focused application shell with clear hierarchy and polished responsive spacing",
                            key_sections=["status header", "pipeline stages", "next steps"],
                            must_have_content=["provider-free status", "successful pipeline stages"],
                            interactivity=[],
                            avoid=["empty screen", "remote assets"],
                        ),
                    )
                ],
            )
        ],
        assumptions=["Provider calls are disabled"],
        risks=["The deterministic scaffold does not interpret the brief like a live model"],
    )


def offline_prd_from_idea(idea: str) -> str:
    artifact = build_offline_prd_artifact(idea)
    prd = artifact.prd
    return (
        f"# {prd.document_title}\n\n"
        f"## Overview\n{prd.overview}\n\n"
        "## Goals\n"
        + "\n".join(f"- {goal}" for goal in prd.goals)
        + "\n"
    )


def offline_plan_dict_for_idea(idea: str) -> Dict[str, Any]:
    return build_offline_plan(idea).model_dump()
