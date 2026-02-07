from __future__ import annotations
import os
from datetime import datetime, timezone
from openai import OpenAI
from schemas.prd_schema import PRD, PRDArtifact


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


SYSTEM_PROMPT = """You are an expert product manager.
Convert the client's raw requirements into a clean, professional Product Requirement Document (PRD).

Output must include these sections:
- document_title: Clear project name
- version: Use "0.1" for initial draft
- overview: High-level description (2-3 sentences)
- goals: Success criteria (3-5 bullet points)
- non_goals: Explicit exclusions (3-5 bullet points)
- target_users: User personas (2-3 types)
- core_features_mvp: Essential features for first release (5-10 items)
- nice_to_have_features: Optional enhancements (3-7 items)
- user_stories: User-centric requirements (minimum 8 stories)
- acceptance_criteria: Definition of done (5-10 criteria)
- technical_stack_recommendation: Suggested technologies (5-8 items)
- payments_security_compliance: Regulatory considerations (2-5 items)
- assumptions: Development constraints (3-5 items)
- open_questions: Client clarifications needed (5-10 questions)

Be thorough, professional, and specific. Do NOT generate app content (e.g., meal plans). Only write requirements.
"""


class PMAgent:
    """
    Product Manager agent that generates PRDs from user requirements using OpenAI.
    """
    
    def __init__(self, api_key: str | None = None):
        """
        Initialize PM agent with OpenAI client.
        
        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_prd(self, user_requirements: str) -> PRDArtifact:
        """
        Generate a PRD from user requirements.
        
        Args:
            user_requirements: Raw client requirements as text
            
        Returns:
            PRDArtifact with structured PRD data
        """
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # Cheap and fast for PRD generation
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Client requirements:\n\n{user_requirements}"}
            ],
            response_format=PRD,  # Structured output
            temperature=0.2,  # Low temperature for consistency
        )
        
        prd = response.choices[0].message.parsed
        
        return PRDArtifact(
            prd=prd,
            created_at=_utc_now_iso(),
        )