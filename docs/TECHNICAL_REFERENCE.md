# Technical Reference

This document holds the deeper repo reference that used to crowd the main README.

## Frontends

| Frontend | Port | Description |
|----------|------|-------------|
| `frontend-studio/` | 3000 | Studio UI with dashboard and project management surfaces |
| `frontend-consumer/` | 3002 | Chat-first interface with versions and i18n |
| `frontend/` | 8080 | Enterprise UI with governance and delivery surfaces |

All three connect to the Flask backend on port `5000`.

## Project Structure

```text
ai-dev-team/
├── agents/
├── backend/
├── frontend-studio/
├── frontend-consumer/
├── frontend/
├── prompts/
├── schemas/
├── scripts/
├── eval/
├── docs/
├── ROADMAP.md
└── CURRENT_SPRINT.md
```

High-signal areas:

- `agents/` for provider-backed orchestration
- `backend/` for the main pipeline and persistence layer
- `frontend/` for the enterprise governance surface
- `frontend-consumer/` for the user-facing prompt/versions flow
- `eval/` for screenshot scoring, prompt improvement, and benchmark tooling

## Reference Build Registry

Legacy strong builds are tracked in [eval/archetype_benchmarks.json](../eval/archetype_benchmarks.json).

The registry is used for:

- local fallback references when discovery-style matching is unavailable
- portable benchmark ingestion across machines
- cross-archetype guidance and quality-floor experiments

Portable benchmark sources live under `eval/benchmark_builds/`.

## API Surface

Primary endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/:id/versions` | Version timeline |
| GET | `/api/projects/:id/versions/:v/files` | Code for a version |
| GET | `/api/projects/:id/versions/:v/factsheet` | Governance factsheet |
| POST | `/api/projects/:id/iterate` | Run pipeline iteration |
| POST | `/api/executions/:id/restore` | Restore a version |
| GET | `/api/preview/:project_id/:version` | Generated preview |
| POST | `/api/projects/:id/versions/:v/publish` | Publish a version |
| GET | `/api/dashboard/stats` | Governance metrics |
| POST | `/api/watson/stt` | Watson speech-to-text |
| POST | `/api/watson/tts` | Watson text-to-speech |

## Key System Features

- version timeline with preview and restore flow
- persisted prompt lineage
- artifact set per execution: brief, plan, code, factsheet, preview
- iteration mode with scoped write enforcement
- governance scoring and quality-tier gating
- eval loop with screenshot-based scoring and prompt improvement
- cross-provider model registry per version

## Governance

The governance layer is backed by IBM Watson NLU and attaches a structured factsheet to each successful build.

Each factsheet can include:

- prompt quality score
- build confidence score
- model registry
- human-review flag
- compliance-oriented metadata
- execution duration and token usage

That surface is especially useful for enterprise audiences because it makes AI delivery visible and reviewable instead of opaque.

## Notes On Models

The repo is intentionally model-agnostic. Depending on config and profile, it can route across:

- Anthropic Claude
- Google Gemini / Vertex AI
- IBM Watson
- OpenAI
- local Ollama-backed models

The important engineering idea is not one fixed provider choice. It is the ability to change providers while keeping the artifact, lineage, and governance surfaces stable.
