# Portfolio Positioning

Archon is best presented as a systems-heavy portfolio project, not as a claim that basic prompt-to-app shells are a durable moat.

## What This Repo Demonstrates

- multi-agent orchestration across requirements, planning, design, build, eval, and governance stages
- model-agnostic orchestration across Anthropic, Google, IBM, OpenAI, and local Ollama-backed workflows
- versioned artifact generation with brief, plan, code, factsheet, and preview surfaces
- persisted prompt history and iterative version lineage
- runtime repair and build-recovery work for malformed generated React/TypeScript/Vite outputs
- automated evaluation loops and benchmark-driven quality comparisons
- governed delivery framing for client-facing agency work

## What Became Commodity

External tools like Lovable proved that a polished:

- prompt box
- preview iframe
- HTML/code toggle
- history list
- refine loop

can be assembled very quickly when the artifact stays simple.

That means the "generate an app from a prompt" shell is no longer the strongest story here.

## What Still Matters In Archon

The higher-signal engineering work in this repo is:

- reliability under brittle multi-file generation
- repair coverage for malformed outputs
- evaluation and scoring loops
- artifact lineage and restore flow
- auditability and governance surfaces
- comparative benchmark analysis instead of blind prompt iteration
- separating premium showcase runs from cheap/local bulk evaluation work

## Lovable Lessons We Intentionally Kept

The project should retain the lessons that clearly improved usability:

- show prompt lineage, not just the latest prompt
- make preview refresh and warm-up behavior explicit
- treat first-render preview failures carefully; artifact quality and preview quality can diverge
- use strong image-driven archetypes as benchmarks for visual quality

## Showcase Strategy

For portfolio purposes, the strongest framing is not "we always used the biggest model."

It is:

- use economical or local providers for repeated evaluation and reliability work
- use premium models selectively for a few hero demos
- keep IBM Watson in the story because governance, scoring, and auditability matter to enterprise audiences
- present the repo as a system that can route across providers rather than one locked stack

Recommended hero archetypes to keep or polish last:

1. `game`
2. `saas_landing`
3. `editor`

If the existing demos for those are already strong, stop there instead of spending more credits.

## Standout Non-Archetype Demo

Beyond generated sites, the governance / factsheet surface is worth showing explicitly.

Why it matters:

- it reads enterprise immediately
- it shows IBM Watson involvement in a concrete UI, not just in architecture text
- it strengthens the "governed, auditable AI workflow" story
- it looks more distinctive to hiring managers than another prompt-to-page demo

If you are picking a short walkthrough, include:

1. one high-style generated example
2. the Versions / lineage view
3. the Governance / Factsheet screen

## Recommended "Done" Standard

For portfolio purposes, this repo is done enough when:

1. the main branches are consolidated cleanly
2. the Versions and Artifacts surfaces are understandable without explanation
3. at least a couple of generated examples look strong and credible
4. the build-reliability work is documented honestly, including limitations
5. the README tells a systems/iteration/governance story rather than a hype story about an unbeatable moat

## Recommended Demo Framing

When walking someone through the repo, emphasize:

1. a prompt becomes a versioned execution with artifacts
2. each version has visible lineage, preview, and restore behavior
3. the backend stores prompt history and build metadata
4. the eval/runtime-repair loop exists because real generation is brittle
5. the repo includes external benchmark analysis that changed product strategy

This framing keeps the project valuable even in a market where prompt-to-UI demos are cheap.
