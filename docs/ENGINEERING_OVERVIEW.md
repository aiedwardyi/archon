# Engineering Overview

Archon is best understood as a systems-heavy application generation platform rather than a thin prompt-to-page shell.

## What The System Emphasizes

- multi-agent orchestration across requirements, planning, design, build, evaluation, and governance stages
- versioned artifact generation with brief, plan, code, factsheet, and preview surfaces
- persisted prompt history and restoreable execution lineage
- runtime repair and build-recovery work for brittle generated React/TypeScript/Vite outputs
- automated evaluation loops and benchmark-driven quality comparisons
- governed delivery framing for client-facing agency and enterprise work

## Where The Differentiation Lives

The highest-signal engineering work in this repository is:

- reliability under brittle multi-file generation
- repair coverage for malformed outputs
- evaluation and scoring loops
- artifact lineage and restore flow
- auditability and governance surfaces
- benchmark-guided iteration instead of blind prompt tweaking
- separation of premium showcase runs from cheaper repeated evaluation work

## Practical Product Lessons

The repository keeps a few concrete lessons from benchmarking other app-generation tools:

- prompt lineage should remain visible, not just the latest prompt
- preview refresh and warm-up behavior should be explicit
- first-render preview failures and final artifact quality can diverge
- image-driven archetypes are useful visual benchmarks

## Provider Strategy

Archon is intentionally model-agnostic.

Depending on configuration, the system can route across:

- Anthropic Claude
- Google Gemini / Vertex AI
- IBM Watson
- OpenAI
- local Ollama-backed models

The architectural goal is stable artifacts, lineage, and governance surfaces even when provider choices change.

## Recommended Walkthrough Surfaces

The clearest short walkthrough is:

1. one generated example
2. the Versions / lineage view
3. the Governance / Factsheet screen

That sequence shows generation, iteration history, and governed delivery without requiring a long explanation.
