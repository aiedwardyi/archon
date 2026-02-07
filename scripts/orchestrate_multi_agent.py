from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Add repo root to Python path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from agents.pm_agent import PMAgent
from agents.planner_agent import PlannerAgent
from google import genai
from schemas.plan_schema import Plan
from schemas.prd_schema import PRDArtifact


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    """Atomically write JSON to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def create_plan_artifact(plan: Plan, agent_sequence: List[str]) -> Dict[str, Any]:
    """
    Create Plan artifact with multi-agent metadata.
    Matches PRDArtifact pattern for consistency.
    """
    return {
        "kind": "plan_artifact",
        "agent_role": "planner",
        "plan": plan.model_dump(),
        "created_at": _utc_now_iso(),
        "_agent_sequence": agent_sequence,
    }


def orchestrate_multi_agent(
    *,
    user_requirements: str,
    artifacts_dir: Path,
    openai_api_key: str | None = None,
    genai_api_key: str | None = None,
) -> Dict[str, Any]:
    """
    Production multi-agent orchestrator.
    
    Executes: PM → Planner → Engineer
    
    Args:
        user_requirements: Raw user input describing what to build
        artifacts_dir: Path to artifacts directory (e.g., apps/offline-vite-react/public)
        openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        genai_api_key: Google GenAI API key (defaults to GENAI_API_KEY env var)
    
    Returns:
        Summary dict with paths to all generated artifacts
    """
    artifacts_dir = artifacts_dir.resolve()
    agent_sequence: List[str] = []
    
    print("=" * 60)
    print("MULTI-AGENT ORCHESTRATOR")
    print("=" * 60)
    print(f"Artifacts dir: {artifacts_dir}")
    print(f"User requirements length: {len(user_requirements)} chars")
    print()
    
    # =========================================================================
    # STEP 1: PM Agent → PRD
    # =========================================================================
    print("[1/3] PM Agent: Generating PRD...")
    agent_sequence.append("pm")
    
    pm_agent = PMAgent(api_key=openai_api_key)
    prd_artifact = pm_agent.generate_prd(user_requirements)
    
    # Add agent sequence metadata
    prd_dict = prd_artifact.model_dump()
    prd_dict["_agent_sequence"] = agent_sequence.copy()
    
    prd_path = artifacts_dir / "last_prd.json"
    atomic_write_json(prd_path, prd_dict)
    
    print(f"✓ PRD generated: {prd_artifact.prd.document_title}")
    print(f"✓ Saved to: {prd_path}")
    print()
    
    # =========================================================================
    # STEP 2: Planner Agent → Plan
    # =========================================================================
    print("[2/3] Planner Agent: Generating Plan from PRD...")
    agent_sequence.append("planner")
    
    genai_key = genai_api_key or os.getenv("GENAI_API_KEY")
    if not genai_key:
        raise ValueError(
            "Google GenAI API key required. Set GENAI_API_KEY environment variable "
            "or pass genai_api_key parameter."
        )
    
    genai_client = genai.Client(api_key=genai_key)
    planner_agent = PlannerAgent(genai_client)
    
    plan = planner_agent.run_from_prd_artifact(prd_path)
    
    plan_artifact = create_plan_artifact(plan, agent_sequence.copy())
    plan_path = artifacts_dir / "last_plan.json"
    atomic_write_json(plan_path, plan_artifact)
    
    milestone_count = len(plan.milestones)
    task_count = sum(len(m.tasks) for m in plan.milestones)
    
    print(f"✓ Plan generated: {milestone_count} milestones, {task_count} tasks")
    print(f"✓ Saved to: {plan_path}")
    print()
    
    # =========================================================================
    # STEP 3: Engineer Agent → Code (via existing consumer)
    # =========================================================================
    print("[3/3] Engineer Agent: Ready for execution...")
    print("NOTE: Engineer agent executes via execution_request flow.")
    print("      Use the UI to select tasks and trigger code generation.")
    print()
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 60)
    print("ORCHESTRATION COMPLETE")
    print("=" * 60)
    print(f"✓ PM → PRD: {prd_path}")
    print(f"✓ Planner → Plan: {plan_path}")
    print(f"✓ Agent sequence: {' → '.join(agent_sequence)}")
    print()
    print("Next steps:")
    print("1. Open the UI to view PRD and Plan artifacts")
    print("2. Select tasks from the Plan to execute")
    print("3. Engineer agent will generate code based on the Plan")
    print()
    
    return {
        "status": "success",
        "prd_path": str(prd_path),
        "plan_path": str(plan_path),
        "agent_sequence": agent_sequence,
        "milestone_count": milestone_count,
        "task_count": task_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Multi-agent orchestrator: PM → Planner → Engineer"
    )
    parser.add_argument(
        "--requirements",
        "-r",
        required=True,
        help="User requirements (use @file.txt to read from file)",
    )
    parser.add_argument(
        "--artifacts",
        default="apps/offline-vite-react/public",
        help="Path to artifacts directory (default: apps/offline-vite-react/public)",
    )
    
    args = parser.parse_args()
    
    # Handle @file.txt syntax
    if args.requirements.startswith("@"):
        req_file = Path(args.requirements[1:])
        if not req_file.exists():
            print(f"Error: Requirements file not found: {req_file}")
            return 1
        user_requirements = req_file.read_text(encoding="utf-8")
    else:
        user_requirements = args.requirements
    
    repo_root = Path(__file__).resolve().parent.parent
    artifacts_dir = (repo_root / args.artifacts).resolve()
    
    try:
        result = orchestrate_multi_agent(
            user_requirements=user_requirements,
            artifacts_dir=artifacts_dir,
        )
        return 0 if result["status"] == "success" else 1
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
