import sys
sys.path.insert(0, '.')

from pathlib import Path
from google import genai
from agents.planner_agent import PlannerAgent
import json
import os

# Check Gemini API key
api_key = os.getenv("GENAI_API_KEY")
if not api_key:
    print("❌ GENAI_API_KEY not set!")
    print("Set it with: $env:GENAI_API_KEY='your_key_here'")
    sys.exit(1)

# Initialize planner with Gemini client
client = genai.Client(api_key=api_key)
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