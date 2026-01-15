from __future__ import annotations
from typing import Dict, Any

def offline_prd_from_idea(idea: str) -> str:
    idea = idea.strip()
    return f"""# PRD (OFFLINE STUB)

## Idea
{idea}

## Goal
Create a simple, presentable MVP that matches the idea and can be deployed.

## Users
- Visitors
- Potential customers

## Key pages
- Home / Landing
- Product/Services
- About
- Contact

## MVP features
- Responsive layout
- Clear CTA
- Basic content sections
- Simple contact form (frontend-only or placeholder)

## Non-goals (for MVP)
- Payments
- Auth
- Admin dashboards
"""

def offline_plan_dict_for_idea(idea: str) -> Dict[str, Any]:
    # Minimal plan that passes typical Plan schema patterns:
    # one milestone with one scaffold task.
    return {
        "milestones": [
            {
                "name": "Milestone 1: Scaffold MVP",
                "tasks": [
                    {
                        "id": "OFFLINE-1",
                        "description": f"Scaffold a minimal project for: {idea.strip()}",
                        "depends_on": [],
                        "outputs": [
                            "Project scaffold",
                            "Basic README",
                            "Basic config files"
                        ],
                        "execution_hint": "engineer",
                        "task_type": "scaffold",
                        "output_files": [
                            "README.md",
                            ".gitignore"
                        ],
                    }
                ],
            }
        ],
        "assumptions": [
            "Offline stub used (no API calls).",
            "We will refine requirements when quota is available."
        ],
        "risks": [
            "Stub plan may not match final product direction until online planning runs."
        ],
    }
