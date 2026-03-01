"""
GovernanceAgent — AI Factsheets with Watson NLU scoring.
Inspired by IBM Watson OpenScale / AI Factsheets.
Uses Watson NLU to score prompt clarity and compute build confidence.
"""
from datetime import datetime, timezone
from typing import Optional


class GovernanceAgent:

    def __init__(self):
        # Reuse NLUAgent for prompt scoring
        try:
            from agents.nlu_agent import NLUAgent
            self.nlu = NLUAgent()
        except Exception:
            self.nlu = None

    def _score_prompt(self, prompt: str) -> dict:
        """
        Uses Watson NLU to score prompt clarity 0-100.
        Returns score + breakdown.
        """
        fallback = {
            "score": None,
            "label": "unavailable",
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "keywords": [],
            "domain": "general",
            "powered_by": "unavailable",
        }

        if not self.nlu or not self.nlu.enabled:
            return fallback

        try:
            result = self.nlu.analyze(prompt)

            # Score logic:
            # Base: 40 points
            # +20 if domain is NOT "general" (specific domain detected)
            # +20 if 2+ keywords found (meaningful content words)
            # +10 if 1 keyword found
            # +20 if prompt is 20+ words (detailed request)
            # +10 if prompt is 10-19 words (moderate detail)
            score = 40
            keywords = result.get("keywords", [])
            domain = result.get("domain", "general")
            sentiment_score = result.get("sentiment_score", 0.0)
            word_count = len(prompt.split())

            if domain != "general":
                score += 20
            if len(keywords) >= 2:
                score += 20
            elif len(keywords) == 1:
                score += 10
            if word_count >= 20:
                score += 20
            elif word_count >= 10:
                score += 10

            score = min(score, 100)

            if score >= 75:
                label = "high"
            elif score >= 50:
                label = "medium"
            else:
                label = "low"

            return {
                "score": score,
                "label": label,
                "sentiment": result.get("sentiment", "neutral"),
                "sentiment_score": round(sentiment_score, 3),
                "keywords": keywords,
                "domain": domain,
                "powered_by": "IBM Watson NLU",
            }
        except Exception as e:
            print(f"[Governance] NLU scoring failed (non-fatal): {e}")
            return fallback

    def _score_build(
        self,
        files_generated: int,
        images_generated: int,
        duration_seconds: Optional[float],
        ui_archetype: Optional[str],
        status: str,
    ) -> dict:
        """
        Computes build confidence score 0-100 based on outputs.
        """
        if status != "success":
            return {"score": 0, "label": "failed", "breakdown": []}

        score = 0
        breakdown = []

        # Files generated (max 50 pts)
        if files_generated >= 2:
            score += 50
            breakdown.append({"factor": "Code files", "points": 50, "note": f"{files_generated} files"})
        elif files_generated == 1:
            score += 30
            breakdown.append({"factor": "Code files", "points": 30, "note": "1 file"})
        else:
            breakdown.append({"factor": "Code files", "points": 0, "note": "No files generated"})

        # Archetype detected (max 30 pts)
        if ui_archetype:
            score += 30
            breakdown.append({"factor": "Archetype detected", "points": 30, "note": ui_archetype})
        else:
            breakdown.append({"factor": "Archetype detected", "points": 0, "note": "Unknown"})

        # Pipeline success (max 20 pts)
        score += 20
        breakdown.append({"factor": "Pipeline success", "points": 20, "note": "Completed without error"})

        score = min(score, 100)

        if score >= 90:
            label = "excellent"
        elif score >= 75:
            label = "good"
        elif score >= 50:
            label = "fair"
        else:
            label = "low"

        return {"score": score, "label": label, "breakdown": breakdown}

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

        # Score the prompt with Watson NLU
        prompt_score = self._score_prompt(prompt)

        # Score the build outputs
        build_score = self._score_build(
            files_generated=files_generated,
            images_generated=images_generated,
            duration_seconds=duration_seconds,
            ui_archetype=ui_archetype,
            status=status,
        )

        # Human review required if either score is low
        human_review_required = (
            (prompt_score["score"] is not None and prompt_score["score"] < 70)
            or build_score["score"] < 80
        )

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
        if prompt_score["score"] is not None:
            status_label = "pass" if prompt_score["score"] >= 75 else "warn" if prompt_score["score"] >= 50 else "fail"
            quality_indicators.append({"indicator": "Prompt clarity", "status": status_label, "value": f"{prompt_score['score']}/100"})

        # Model registry
        model_registry = []
        for role, model_name in models_used.items():
            model_registry.append({
                "agent_role": role,
                "model": model_name,
                "provider": self._get_provider(model_name),
            })

        if self.nlu and self.nlu.enabled:
            model_registry.append({
                "agent_role": "Governance Agent",
                "model": "Watson NLU",
                "provider": "IBM",
            })

        factsheet = {
            "factsheet_version": "1.1",
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
            "scoring": {
                "prompt_quality": prompt_score,
                "build_confidence": build_score,
            },
            "quality_indicators": quality_indicators,
            "compliance": {
                "audit_trail": True,
                "version_history": True,
                "artifact_retention": True,
                "human_review_required": human_review_required,
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
