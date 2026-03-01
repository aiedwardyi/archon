"""
GovernanceAgent — generates AI Factsheets per pipeline execution.
Inspired by IBM Watson OpenScale / AI Factsheets concept.
Produces a structured, auditable record of every build.
"""
from datetime import datetime, timezone
from typing import Optional


class GovernanceAgent:
    """
    Runs after every successful pipeline completion.
    Writes a structured Factsheet capturing:
    - Models used and their roles
    - Token usage and estimated cost
    - Build duration and version info
    - UI archetype detected/locked
    - Quality indicators
    - Agent sequence
    """

    def generate_factsheet(
        self,
        project_id: int,
        project_name: str,
        version: int,
        execution_id: int,
        prompt: str,
        ui_archetype: Optional[str],
        models_used: dict,
        tokens_used: Optional[int],
        estimated_cost: Optional[float],
        credits_used: Optional[int],
        duration_seconds: Optional[float],
        files_generated: int,
        images_generated: int,
        agent_sequence: list,
        status: str = "success",
    ) -> dict:
        """Returns a structured Factsheet dict."""

        # Quality indicators
        quality_indicators = []
        if files_generated > 0:
            quality_indicators.append({"indicator": "Code generated", "status": "pass", "value": f"{files_generated} file(s)"})
        if images_generated > 0:
            quality_indicators.append({"indicator": "Design assets", "status": "pass", "value": f"{images_generated} image(s)"})
        if tokens_used and tokens_used > 0:
            quality_indicators.append({"indicator": "Token usage", "status": "pass", "value": f"{tokens_used:,} tokens"})
        if duration_seconds and duration_seconds < 120:
            quality_indicators.append({"indicator": "Build speed", "status": "pass", "value": f"{duration_seconds:.1f}s"})
        elif duration_seconds:
            quality_indicators.append({"indicator": "Build speed", "status": "warn", "value": f"{duration_seconds:.1f}s (slow)"})

        # Model registry
        model_registry = []
        for role, model_name in models_used.items():
            model_registry.append({
                "agent_role": role,
                "model": model_name,
                "provider": self._get_provider(model_name),
            })

        factsheet = {
            "factsheet_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project": {
                "id": project_id,
                "name": project_name,
                "version": version,
                "execution_id": execution_id,
            },
            "prompt_summary": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "pipeline": {
                "status": status,
                "agent_sequence": agent_sequence,
                "duration_seconds": duration_seconds,
                "ui_archetype": ui_archetype,
            },
            "model_registry": model_registry,
            "usage": {
                "tokens_used": tokens_used,
                "estimated_cost_usd": estimated_cost,
                "credits_used": credits_used,
            },
            "outputs": {
                "files_generated": files_generated,
                "images_generated": images_generated,
            },
            "quality_indicators": quality_indicators,
            "compliance": {
                "audit_trail": True,
                "version_history": True,
                "artifact_retention": True,
                "human_review_required": False,
            },
        }
        return factsheet

    def _get_provider(self, model_name: str) -> str:
        if not model_name:
            return "Unknown"
        m = model_name.lower()
        if "claude" in m:
            return "Anthropic"
        if "gemini" in m or "flash" in m:
            return "Google"
        if "gpt" in m or "dall-e" in m or "openai" in m:
            return "OpenAI"
        if "watson" in m or "ibm" in m:
            return "IBM"
        return "Unknown"
