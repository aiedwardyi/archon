from __future__ import annotations
import json
from pathlib import Path
from google import genai
from schemas.plan_schema import Plan
from schemas.prd_schema import PRDArtifact
from utils.genai_retry import call_with_retry


class PlannerAgent:
    def __init__(self, client: genai.Client):
        self.client = client
    
    def run_from_prd_text(self, prd_text: str) -> Plan:
        """
        Legacy method: Generate plan from PRD text.
        Kept for backward compatibility.
        """
        prompt = Path("prompts/planner.txt").read_text(encoding="utf-8")
        contents = f"{prompt}\n\n--- PRD START ---\n{prd_text}\n--- PRD END ---"
        
        def _call():
            return self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config={
                    "response_schema": Plan,
                    "temperature": 0.2,
                },
            )
        
        response = call_with_retry(_call, max_retries=2)
        
        if response.parsed is None:
            raw = getattr(response, "text", None)
            raise RuntimeError(
                "PlannerAgent: schema parse failed (response.parsed is None).\n\n"
                f"Raw model output:\n{raw}"
            )
        
        return response.parsed
    
    def run_from_prd_artifact(self, prd_artifact_path: Path) -> Plan:
        """
        Phase 5: Generate plan from PRD artifact.
        This is the new multi-agent handoff method.
        
        Args:
            prd_artifact_path: Path to PRD artifact JSON file
            
        Returns:
            Plan schema object
        """
        # Read and validate PRD artifact
        if not prd_artifact_path.exists():
            raise FileNotFoundError(f"PRD artifact not found: {prd_artifact_path}")
        
        prd_artifact_data = json.loads(prd_artifact_path.read_text(encoding="utf-8"))
        prd_artifact = PRDArtifact.model_validate(prd_artifact_data)
        
        # Convert PRD to readable text format for the planner prompt
        prd = prd_artifact.prd
        prd_text = self._format_prd_as_text(prd)
        
        # Use existing planner logic
        return self.run_from_prd_text(prd_text)
    
    def _format_prd_as_text(self, prd) -> str:
        """
        Format PRD object as readable text for planner prompt.
        """
        return f"""# {prd.document_title}

**Version:** {prd.version}

## Overview
{prd.overview}

## Goals
{self._format_list(prd.goals)}

## Non-Goals
{self._format_list(prd.non_goals)}

## Target Users
{self._format_list(prd.target_users)}

## Core Features (MVP)
{self._format_list(prd.core_features_mvp)}

## Nice-to-Have Features
{self._format_list(prd.nice_to_have_features)}

## User Stories
{self._format_list(prd.user_stories)}

## Acceptance Criteria
{self._format_list(prd.acceptance_criteria)}

## Technical Stack Recommendation
{self._format_list(prd.technical_stack_recommendation)}

## Assumptions
{self._format_list(prd.assumptions)}

## Open Questions
{self._format_list(prd.open_questions)}
"""
    
    def _format_list(self, items: list[str]) -> str:
        """Format list items as bullet points."""
        if not items:
            return "- (none)"
        return "\n".join([f"- {item}" for item in items])
    
    # Backward compatibility: make run() default to run_from_prd_text
    def run(self, prd_text: str) -> Plan:
        """Backward compatible method."""
        return self.run_from_prd_text(prd_text)