import sys
sys.path.insert(0, '.')

from pathlib import Path
from google import genai
from openai import OpenAI
from agents.pm_agent import PMAgent
from agents.planner_agent import PlannerAgent
from agents.engineer_agent import EngineerAgent
import json
import os

# Check API keys
openai_key = os.getenv("OPENAI_API_KEY")
gemini_key = os.getenv("GENAI_API_KEY")

if not openai_key:
    print("❌ OPENAI_API_KEY not set!")
    sys.exit(1)

if not gemini_key:
    print("❌ GENAI_API_KEY not set!")
    sys.exit(1)

print("=" * 60)
print("FULL AGENT CHAIN TEST: PM → Planner → Engineer")
print("=" * 60)

# Step 1: PM Agent generates PRD
print("\n[1/3] PM AGENT: Generating PRD...")
pm_agent = PMAgent(api_key=openai_key)

requirements = """
Build a simple calculator app that:
- Supports basic operations: add, subtract, multiply, divide
- Has a clean web interface
- Shows calculation history
- Works on mobile devices
"""

prd_artifact = pm_agent.generate_prd(requirements)
prd_path = Path("artifacts/test_prd.json")
prd_path.write_text(json.dumps(prd_artifact.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")

print(f"✅ PRD generated: {prd_artifact.prd.document_title}")
print(f"   Saved to: {prd_path}")

# Step 2: Planner consumes PRD, generates Plan
print("\n[2/3] PLANNER AGENT: Generating Plan from PRD...")
gemini_client = genai.Client(api_key=gemini_key)
planner = PlannerAgent(gemini_client)

plan = planner.run_from_prd_artifact(prd_path)
plan_path = Path("artifacts/test_plan.json")
plan_path.write_text(json.dumps(plan.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")

print(f"✅ Plan generated: {len(plan.milestones)} milestones, {sum(len(m.tasks) for m in plan.milestones)} tasks")
print(f"   Saved to: {plan_path}")

# Step 3: Engineer consumes Plan, generates code
print("\n[3/3] ENGINEER AGENT: Executing first task...")

# Find first executable task
first_task = None
for milestone in plan.milestones:
    for task in milestone.tasks:
        if task.execution_hint == "engineer":
            first_task = task
            break
    if first_task:
        break

if not first_task:
    print("⚠️  No executable tasks found (all deferred)")
else:
    engineer = EngineerAgent(client=gemini_client)
    
    # Set OFFLINE_MODE to use deterministic scaffold
    os.environ["OFFLINE_MODE"] = "1"
    
    result = engineer.run(first_task)
    
    print(f"✅ Engineer executed task: {first_task.id}")
    print(f"   Summary: {result.summary}")
    print(f"   Files generated: {len(result.files)}")

print("\n" + "=" * 60)
print("FULL CHAIN TEST COMPLETE!")
print("=" * 60)
print("\nArtifact chain:")
print(f"  1. PRD:  {prd_path}")
print(f"  2. Plan: {plan_path}")
print(f"  3. Code: {result.files[0].path if first_task and result.files else '(none)'}")