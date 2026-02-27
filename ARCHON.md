# ARCHON — Architectural Memory Summary

## Product Vision

Archon is a multi-agent AI development platform designed for:

- Non-technical development agencies
- Enterprise founders
- Client-facing workflows

Primary goals:

- Generate production-quality applications through AI orchestration.
- Maintain full version history and auditability.
- Enable easy client communication via version snapshots and PDF exports.

---

## Core UX Model

One user prompt = ONE VERSION.

Each version contains artifact tabs:

- Brief (PRD / Requirements)
- Build Plan (Architecture JSON)
- Code (File tree + implementation)
- Tasks
- Logs
- Live Preview

Requirements:

- Users must compare versions visually.
- Users must restore any version.
- No internal pipeline steps should create visible intermediate versions.
- Internal refinement (QA, patching) occurs inside same version.

---

## Current Agent Pipeline

PM Agent:
- Generates structured PRD.

Planner / Architecture Agent:
- Outputs Build Plan JSON.
- Contains milestones and tasks.
- Exactly one scaffold task executed by Engineer.
- Includes ui_archetype classification and archetype_rules.
- Includes layout_contract, content_contract, style_contract per archetype.

Design Agent (GPT-4o-mini + DALL-E 3):
- Runs in parallel with Architecture Agent.
- Generates hero backgrounds and character portraits.
- Skips image generation for dashboards and tool apps (cost saving).
- Images downloaded to disk, served via /api/assets/ route.

Engineer Agent (Claude Sonnet):
- Generates application scaffold and UI implementation.
- Outputs two files: src/index.html (structure + JS) + src/style.css (design).
- MUST obey ui_archetype, archetype_rules, and layout_contract.
- Does NOT invent layout or design system — implements spec only.

Live Preview:
- Flask stitches index.html + style.css into single srcdoc blob.
- Renders in iframe with desktop/mobile toggle.

---

## Key Architectural Principles

### Determinism Philosophy
Determinism = controlled structure, not identical token output.

Achieved via:
- ui_archetype enforcement (enum, not freeform)
- Structured schemas (Pydantic models)
- Anchor-based layout contracts
- Pinned model configurations
- Stored artifacts for replay

### Model Role Separation
- OpenAI GPT-4o: PM Agent (requirements, PRD)
- Google Gemini 2.5 Flash: Architecture/Planner Agent
- GPT-4o-mini + DALL-E 3: Design Agent
- Claude Sonnet 4.5: Engineer Agent (primary builder)

### One Version Per Prompt
- No intermediate versions from internal pipeline steps
- QA/patch passes happen inside same version
- Every version has full artifact set: Brief + Plan + Code + Preview

---

## UI Archetype System

Engineer MUST classify and enforce one of these archetypes:

| Archetype | Primary Action | Shell |
|-----------|---------------|-------|
| dashboard | monitor/analyze | sidebar + topbar + data grid |
| landing | promote/convert | hero + sections + footer |
| ecommerce | buy/browse | header + product grid + cart |
| kanban | manage tasks | columns + cards |
| chat | send/read messages | 3-panel layout |
| editor | create/edit content | toolbar + canvas |
| feed | discover content | grid/masonry cards |
| form | submit information | centered card + steps |
| game | play/interact | full-viewport canvas |
| portfolio | showcase work | hero band + sections |

Each archetype has:
- layout_contract: regions, grid geometry, component sizes
- content_contract: data entities, KPI definitions, seed data rules
- style_contract: density, spacing scale, typography scale

---

## Competitive Moat

**The Versions page is Archon's #1 differentiator.**

Competitors show current state only.
Archon shows complete decision history:
- Every prompt creates a full artifact set
- Every version has live preview
- Agencies can show clients exactly what was built and why
- Full audit trail is a client deliverable, not just a dev tool

---

## Future Roadmap (High Level)

- Phase 7F: Chatbox upgrades (file upload, drag-and-drop, agent replies)
- Phase 7G: Design QA agent (draft → QA patch → final, same version)
- Phase 8: Client deliverables (PDF export, shareable read-only link, white-label)

---

## Tech Stack

- Backend: Flask + SQLAlchemy + SQLite
- Frontend: Next.js + TypeScript
- Package manager: pnpm
- APIs: OpenAI, Google Gemini, Anthropic
- Dev: localhost:5000 (backend), localhost:3000 (frontend)
- Branch: enterprise-ui
- Working directory: C:\Users\mredw\Desktop\ai-dev-team\
