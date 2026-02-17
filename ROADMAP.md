# Archon — AI Dev Team Platform

## Vision

Archon is a deterministic multi-agent platform for digital agencies and development
shops that need to build client web applications with full accountability.

An agency describes what they want to build. Archon runs a complete
PM → Planner → Engineer pipeline, generates a runnable web app, and preserves
every prompt, decision, and artifact as a versioned snapshot. Clients can see
exactly what was built, when, and why — across every iteration.

**The agency value proposition:**
- Build faster with AI-generated code
- Show clients a complete auditable history of every decision
- Restore any previous version if the client changes their mind
- Export build history as a client-presentable PDF

---

## High-Level Architecture

**Flow**

Agency types project prompt
→ PM Agent (OpenAI) → Requirements artifact
→ Planner Agent (Gemini) → Architecture artifact
→ Engineer Agent (Gemini) → Runnable web application
→ Versioned snapshot stored
→ Client-facing preview + audit trail

**Key principle:**
Every iteration runs the full pipeline. Nothing is patched.
Every version is a complete, independent, auditable snapshot.

---

## Design Principles

- **Determinism first** — identical inputs produce identical artifacts
- **Full pipeline on every iteration** — no patching, always re-run
- **Client accountability** — every decision traceable and presentable
- **Version integrity** — past versions never deleted, always restorable
- **Observable state** — all artifacts written as inspectable files
- **Failure visibility** — errors surface as artifacts, not hidden logs

---

## Target Audience

**Primary:** Digital agencies and freelance dev shops
- Build client websites, internal tools, and web applications
- Need to show clients exactly what changed and why
- Need to deliver faster without sacrificing accountability

**Secondary:** Non-technical founders and small businesses
- Want to build web apps without coding
- Need to track and manage AI-generated output
- Need a client-presentable audit trail

**Why agencies specifically:**
- Already pay for tools (budget exists)
- Client accountability is an immediate pain point
- Archon becomes infrastructure they can't work without
- Agencies are a wedge into enterprise clients

---

## Competitive Positioning

| Feature | Lovable/Bolt | Archon |
|---------|-------------|--------|
| AI code generation | ✅ | ✅ |
| Context continuation | ✅ | ✅ |
| Live preview | ✅ | ✅ (Phase 7B) |
| Full chain on every edit | ❌ | ✅ |
| Artifact trail per version | ❌ | ✅ |
| Restore previous version | ✅ | ✅ |
| Restore forward after revert | ❌ | ✅ |
| Auditable PRD per iteration | ❌ | ✅ |
| Client-exportable build history | ❌ | ✅ (Phase 7C) |
| Agent chain visibility | ❌ | ✅ |
| Schema validation | ❌ | ✅ |

**Technical moat:** Lovable patches code on iteration. Archon re-runs the full
pipeline every time. Even if competitors add "history" features, they will be
cosmetic — not architectural. Archon's audit trail is genuine because every
artifact is regenerated from scratch on every run.

---

## Phased Execution Plan

### Phase 1 — Foundations (✅ Completed)
- Schema-validated PRD generation
- Planner producing milestone/task plans
- Deterministic offline regeneration
- Safe file write allowlists
- Frontend rendering PRD + Plan artifacts

### Phase 2 — Interactive Execution (✅ Completed)
- Lovable-style milestone/task UI
- Deterministic execution request emission
- UI → backend artifact handoff
- Append-only execution logs

### Phase 3 — Orchestration & Evaluation (✅ Completed)
- Orchestrator consumes execution request artifacts
- Evaluation harness producing pass/fail artifacts
- Canonical hashing for semantic identity
- Golden snapshot regression tests

### Phase 4 — Production Hardening (✅ Completed)
- Read-only UI for execution/evaluation artifacts
- Strict schema enforcement at system boundaries
- Deterministic replay runner for past executions

### Phase 5 — Multi-Agent Coordination (✅ Completed)
- Multi-agent workflow: PM (OpenAI) → Planner (Gemini) → Engineer (Gemini)
- Flask API backend with async execution and threading
- React UI with polling and toast notifications
- Agent sequence tracking end-to-end

### Phase 6.1 — Project History & Persistence (✅ Completed)
- SQLite with SQLAlchemy ORM
- Project management: create, view, organize projects
- Execution tracking linked to projects
- React Router multi-page navigation

### Phase 6.2 — Enhanced UI/UX (✅ Completed)
- Polished dark/light mode UI with Tailwind
- ArtifactViewer: PRD, Plan, Code tabs with real backend data
- ProjectDetailPage with full agent workflow visualization
- Monorepo consolidation: frontend moved into ai-dev-team repo

### Phase 6.3 — Differentiator Features & Polish (✅ Completed)
- Agent chain badge (pm → planner → engineer)
- Raw JSON toggle with syntax highlighting
- VS Code-style folder tree in Code explorer
- Sidebar status dots, Clear All Projects
- Engineer prompt: 1 README max, 6 file cap
- safe_write.py allowlist expanded
- Duplicate file dedup
- All changes committed

---

### Phase 7A — Iterative Pipeline & Version History (🚧 Next)

**Goal:** Transform Archon from single-shot to true iterative build tool.
Every prompt runs the full pipeline and creates a versioned snapshot.

**Work Items:**
- 7A.1 Backend: versioned execution storage + prompt history in DB
- 7A.2 Backend: /iterate and /restore endpoints
- 7A.3 Frontend: complete UI redesign to enterprise design target
- 7A.4 Frontend: continuous chat panel (always visible)
- 7A.5 Frontend: version timeline (Versions page)
- 7A.6 Frontend: version preview + restore flow

**UI Design Target:** Approved Lovable mockups (top navbar, agent timing
cards, version timeline with detail panel, artifact tabs with badge bar)

---

### Phase 7B — Live Preview (⬜ Planned)

**Goal:** Real running iframe of engineer's generated output.
Essential for non-technical agency clients to evaluate results.

**Work Items:**
- 7B.1 Engineer agent: constrain output to self-contained web apps
- 7B.2 Backend: dynamic file serving (/preview/:projectId/:version)
- 7B.3 Frontend: iframe preview panel
- 7B.4 Version preview: clicking past version loads that version in iframe

---

### Phase 7C — Client Deliverables (⬜ Planned)

**Goal:** Features that make Archon a client-facing accountability tool.

**Work Items:**
- 7C.1 PDF export of full build history (prompts, versions, artifacts)
- 7C.2 Version diff viewer (side-by-side comparison between any two versions)
- 7C.3 Shareable read-only project link for client review

---

### Phase 7D — Settings & Team (⬜ Planned)
- Settings page: API keys, model config, default parameters
- Team roles: viewer/editor/admin per project

---

## Current State

- ✅ Three-agent coordination (PM, Planner, Engineer)
- ✅ Flask API backend with async execution
- ✅ SQLite database with full persistence
- ✅ Project management and execution history
- ✅ Differentiator features visible in UI
- 🚧 Iterative pipeline + enterprise UI redesign (Phase 7A)
- ⬜ Live preview (Phase 7B)
- ⬜ Client deliverables: PDF export, diff viewer (Phase 7C)

---

## Quality Bar

A change is considered complete only if:
- artifacts are deterministic
- schemas are validated
- failure modes are visible
- outputs can be reasoned about by inspection
