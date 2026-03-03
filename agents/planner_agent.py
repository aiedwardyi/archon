from __future__ import annotations
import json
from pathlib import Path
from google import genai
from schemas.plan_schema import Plan
from schemas.prd_schema import PRDArtifact
from utils.genai_retry import call_with_retry

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class PlannerAgent:
    def __init__(self, client: genai.Client):
        self.client = client
    
    def run_from_prd_text(
        self,
        prd_text: str,
        locked_ui_archetype: str | None = None,
        is_iteration: bool = False,
    ) -> Plan:
        """
        Legacy method: Generate plan from PRD text.
        Kept for backward compatibility.
        """
        prompt = (PROMPTS_DIR / "planner.txt").read_text(encoding="utf-8")
        lock_note = ""
        if locked_ui_archetype:
            lock_note = (
                "\n\nLOCKED UI ARCHETYPE:\n"
                f"- Use ui_archetype: {locked_ui_archetype} for the scaffold task\n"
                "- Do not choose any other archetype\n"
                "- Ensure archetype_rules match the locked archetype\n"
            )
        iteration_note = ""
        if is_iteration:
            iteration_note = (
                "\n\nITERATION MODE:\n"
                "- This is v2+ (an iteration). The engineer task must include a minimal, non-empty output_files scope\n"
                "- output_files must list ONLY the files to modify (repo-relative, e.g. src/index.html)\n"
                "- Do NOT include unrelated files. Only expand scope if the user explicitly requests a broad refactor\n"
                "- For iterations, all changes must go into src/index.html and src/style.css only. "
                "Do not create new files like game.js or game.css. "
                "New functionality (scripts, extra styles) must be added inline in index.html using <script> and <style> tags\n"
                '- output_files: ["src/index.html", "src/style.css"]\n'
            )
        contents = f"{prompt}{lock_note}{iteration_note}\n\n--- PRD START ---\n{prd_text}\n--- PRD END ---"
        
        def _call():
            return self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": Plan,
                    "temperature": 0.2,
                },
            )
        
        for parse_attempt in range(3):
            response = call_with_retry(_call, max_retries=2)
            if response.parsed is not None:
                return response.parsed
            if parse_attempt < 2:
                print(f"PlannerAgent: schema parse failed, retrying (attempt {parse_attempt + 1}/3)...")
                import time; time.sleep(1)
        raise RuntimeError("Architecture Agent could not produce a valid build plan after 3 attempts. Please try rephrasing your request.")
    
    def run_from_prd_artifact(
        self,
        prd_artifact_path: Path,
        locked_ui_archetype: str | None = None,
        is_iteration: bool = False,
    ) -> Plan:
        """
        Phase 5: Generate plan from PRD artifact.
        This is the new multi-agent handoff method.
        
        Args:
            prd_artifact_path: Path to PRD artifact JSON file
            
        Returns:
            Plan schema object
        """
        if not prd_artifact_path.exists():
            raise FileNotFoundError(f"PRD artifact not found: {prd_artifact_path}")
        
        prd_artifact_data = json.loads(prd_artifact_path.read_text(encoding="utf-8"))
        prd_artifact = PRDArtifact.model_validate(prd_artifact_data)
        
        prd = prd_artifact.prd
        prd_text = self._format_prd_as_text(prd)
        
        return self.run_from_prd_text(
            prd_text,
            locked_ui_archetype=locked_ui_archetype,
            is_iteration=is_iteration,
        )
    
    def _format_prd_as_text(self, prd) -> str:
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
        if not items:
            return "- (none)"
        return "\n".join([f"- {item}" for item in items])
    
    def run(
        self,
        prd_text: str,
        locked_ui_archetype: str | None = None,
        is_iteration: bool = False,
    ) -> Plan:
        """Backward compatible method."""
        return self.run_from_prd_text(
            prd_text,
            locked_ui_archetype=locked_ui_archetype,
            is_iteration=is_iteration,
        )



