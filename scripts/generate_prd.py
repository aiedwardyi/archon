from __future__ import annotations
import argparse
import json
from pathlib import Path
from agents.pm_agent import PMAgent


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate PRD from user requirements")
    parser.add_argument(
        "--requirements",
        required=True,
        help="User requirements (text string or path to .txt file)"
    )
    parser.add_argument(
        "--output",
        default="artifacts/last_prd.json",
        help="Output path for PRD artifact"
    )
    args = parser.parse_args()
    
    # Read requirements
    requirements_path = Path(args.requirements)
    if requirements_path.exists() and requirements_path.suffix == ".txt":
        requirements = requirements_path.read_text(encoding="utf-8")
    else:
        requirements = args.requirements
    
    # Generate PRD
    print("Generating PRD with OpenAI...")
    agent = PMAgent()
    prd_artifact = agent.generate_prd(requirements)
    
    # Write artifact
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    artifact_json = json.dumps(
        prd_artifact.model_dump(),
        indent=2,
        ensure_ascii=False
    )
    output_path.write_text(artifact_json, encoding="utf-8")
    
    print(f"\n✅ PRD generated successfully!")
    print(f"📄 Saved to: {output_path}")
    print(f"\nProject: {prd_artifact.prd.document_title}")
    print(f"Features: {len(prd_artifact.prd.core_features_mvp)} core, {len(prd_artifact.prd.nice_to_have_features)} nice-to-have")
    print(f"User stories: {len(prd_artifact.prd.user_stories)}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())