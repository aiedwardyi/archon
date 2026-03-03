import sys
sys.path.insert(0, '.')

from pathlib import Path
from agents.planner_agent import PlannerAgent
from utils.genai_client import get_genai_client
import json
import os

# Initialize planner with Gemini client (Vertex AI or AI Studio)
client = get_genai_client()
planner = PlannerAgent(client)

# Read PRD artifact from PM agent
prd_artifact_path = Path("artifacts/last_prd.json")

print("Testing PM → Planner handoff...")
print(f"Reading PRD from: {prd_artifact_path}")

# Generate plan from PRD artifact
plan = planner.run_from_prd_artifact(prd_artifact_path)

# Save plan artifact
plan_output = Path("artifacts/last_plan.json")
plan_output.write_text(json.dumps(plan.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\n✅ Plan generated successfully!")
print(f"📄 Saved to: {plan_output}")
print(f"\nMilestones: {len(plan.milestones)}")
print(f"Total tasks: {sum(len(m.tasks) for m in plan.milestones)}")

# Show first milestone
if plan.milestones:
    first = plan.milestones[0]
    print(f"\nFirst milestone: {first.title}")
    print(f"  Tasks: {len(first.tasks)}")