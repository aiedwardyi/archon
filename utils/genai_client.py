"""Centralized Gemini client factory — Vertex AI or AI Studio."""
import os
from google import genai


def get_genai_client() -> genai.Client:
    project = os.getenv("VERTEX_AI_PROJECT")
    location = os.getenv("VERTEX_AI_LOCATION", "us-central1")

    if project:
        # Vertex AI mode — uses GCP credit via Application Default Credentials
        return genai.Client(vertexai=True, project=project, location=location)

    # Fallback: AI Studio API key mode
    api_key = os.getenv("GENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set VERTEX_AI_PROJECT for Vertex AI, or GENAI_API_KEY for AI Studio")
    return genai.Client(api_key=api_key)
