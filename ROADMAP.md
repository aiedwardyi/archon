# Archon — Execution Roadmap

## Purpose

Archon is a deterministic multi-agent platform that converts product ideas into
structured, auditable web applications. Target market: digital agencies and dev
shops delivering client web applications to non-technical clients.

**Core value proposition:**
- AI builds client apps fast with full pipeline transparency
- Complete audit trail of every prompt, decision, and iteration
- Client-presentable version history at every stage
- Restore any previous version instantly
- PDF export of full build history as client deliverable

---

## Target User

Non-technical agency owner or project lead who:
- Cannot read code — needs to SEE the app running
- Needs to show clients every decision made during development
- Needs business language, not developer jargon

**Competitive positioning:** Not "build apps with AI faster" —
instead "Build client apps with AI. Show them everything."

---

## High-Level Architecture
```
User Input (Chat Panel)
    ↓
Prompt History (context continuation)
    ↓
PM Agent (OpenAI) → Requirements artifact (versioned)
    ↓
Planner Agent (Gemini) → Build Plan artifact (versioned)
    ↓
Engineer Agent (Gemini) → Code files (versioned)
    ↓
Execution Result → Database + UI + Version Timeline
```

**Key principle:** Every step emits structured artifacts that can be
inspected, validated, and replayed. Full audit trail across every iteration.

---

## Design Principles

- **Determinism first** — identical inputs produce identical artifacts
- **Explicit contracts** — JSON schemas at every agent boundary
- **Observable state** — all artifacts written as inspectable files
- **Failure visibility** — errors surface as artifacts, not silent failures
- **Full audit trail** — every execution traceable end-to-end
- **Business language** — non-technical users understand every screen

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
- Deterministic execution result artifacts
- Evaluation harness producing pass/fail artifacts
- Canonical hashing for semantic identity
- Golden snapshot regression tests

### Phase 4 — Production Hardening (✅ Completed)
- Read-only UI for last execution/evaluation artifacts
- Strict schema enforcement at system boundaries
- Deterministic replay runner for past executions

### Phase 5 — Multi-Agent Coordination (✅ Completed)
- Multi-agent workflow: PM (OpenAI) → Planner (Gemini) → Engineer (Gemini)
- Flask API backend: async execution with threading, state tracking
- React UI integration: task execution with polling
- Agent sequence tracking: metadata preserved throughout chain
- File-based handoffs: PRD → Plan → Execution Request → Result

### Phase 6.1 — Project History & Persistence (✅ Completed)
- SQLite with SQLAlchemy ORM
- Project management: create, view, organize projects
- Execution tracking linked to projects
- React Router multi-page navigation

### Phase 6.2 — Enhanced UI/UX (✅ Completed)
- Polished UI with Tailwind
- Sidebar navigation with smooth transitions
- ArtifactViewer: PRD, Plan, Code tabs with real backend data
- ProjectDetailPage with full agent workflow visualization
- Mobile-responsive layout
- Monorepo consolidation

### Phase 6.3 — Differentiator Features & Polish (✅ Completed)
- Agent chain badge in ArtifactViewer (pm → planner → engineer)
- Raw JSON toggle with syntax highlighting and line numbers
- VS Code-style folder tree explorer in Code artifact view
- Sidebar status dots: blue pulsing=running, green=completed, red=failed
- Clear All Projects with confirmation modal
- Engineer prompt: max 1 README, 6 file cap
- safe_write.py: expanded allowlist
- Duplicate file dedup

### Phase 6.4 — Enterprise UI Design (✅ Completed)
**Goal:** Redesign Archon's UI for non-technical agency owners.
Approved enterprise design (Linear/Vercel aesthetic) across 10 screens.

**Accomplished:**
- Full enterprise UI designed in Lovable — light + dark mode
- Business language replacing all technical terms:
  - pm→planner→engineer → Requirements→Architecture→Code
  - REPLAYABLE → REPRODUCIBLE, SCHEMA VALIDATED → VERIFIED
  - PRD → Brief, Implementation Plan → Build Plan
  - Generated Tasks → Build Tasks, LOC removed entirely
  - Plain English logs — no DEBUG/WARN/INFO labels
  - JSON → Raw Data
- Dark mode: enterprise-grade neutral palette (Linear/GitHub style)
  No gradients, no glow effects, subdued #0d0d0d backgrounds
- Dark mode toggle in navbar (sun/moon icon)
- Preview tab added: desktop/mobile viewport toggle, placeholder state
- Download Report button on Versions page + Projects table
- All 10 screens approved: Projects, Pipeline, Versions,
  Brief, Plan, Code, Tasks, Logs, Preview (desktop + mobile)

**enterprise-ui branch:** Full frontend rebuild complete

---

### Phase 7A — Iterative Pipeline & Version History (✅ Completed)

**Goal:** Transform Archon from single-shot generator into a true iterative
build tool. Every prompt runs the full pipeline and creates a versioned
snapshot — full audit trail across the entire build history.

**Work Items:**
- ✅ 7A.1 Backend: versioned execution storage + prompt history in DB
- ✅ 7A.2 Backend: /iterate and /restore endpoints
- ✅ 7A.3 Frontend: enterprise UI rebuild on enterprise-ui branch
- ✅ 7A.4 Frontend: continuous chat panel + log persistence + navigation polish

**What was built:**
- Iterative pipeline: every prompt submission runs the full PM → Planner →
  Engineer chain and creates a new versioned execution in the DB
- Prompt history continuation: PM agent sees all previous turns on every run
- sessionStorage caching: project name, real logs (keyed by execution ID),
  and agent card state all cached for instant navigation-back experience
- Real log persistence: logs saved on run completion, restored on return —
  no more fake reconstructed summaries
- Agent card state restored instantly from cache — no settling/flash on nav back
- Versions page: timeline + detail panel + restore flow
- ArtifactViewer: Brief, Build Plan, Code tabs wired to real backend data

**Known remaining items:**
- ArtifactViewer Code tab uses mock data (real file tree wiring: Phase 7B scope)
- Live preview iframe: Phase 7B

---

### Phase 7B — Live Preview (🔴 Elevated Priority)

**Goal:** Real running iframe of the engineer's generated output.
Essential for non-technical users who cannot evaluate raw code.

**Work Items:**
- 7B.1 Engineer agent: prompt engineering for self-contained runnable output
- 7B.2 Backend: dynamic file serving route (/preview/:projectId/:version)
- 7B.3 Frontend: iframe preview panel (desktop + mobile toggle already designed)
- 7B.4 History integration: clicking past version loads that version in iframe
- 7B.5 ArtifactViewer: wire Code tab to real generated file tree

---

### Phase 7C — Client Deliverables (⬜ Planned)

**Goal:** Agency-facing export and sharing features.

**Work Items:**
- PDF export of full build history (audit trail for client presentations)
- Client shareable read-only link
- White-label option (agency branding)
- Project handoff export

---

## Competitive Positioning

| Feature | Lovable/Bolt | Archon |
|---------|-------------|--------|
| Context continuation | ✅ | ✅ |
| Full chain on every edit | ❌ | ✅ |
| Artifact trail per version | ❌ | ✅ |
| Restore previous version | ✅ | ✅ |
| Restore forward after revert | ❌ | ✅ |
| Auditable Brief per iteration | ❌ | ✅ |
| Agent chain visibility | ❌ | ✅ |
| Schema validation | ❌ | ✅ |
| Live preview | ✅ | 🚧 7B |
| Client PDF export | ❌ | 🚧 7C |
| Non-technical agency UI | ❌ | ✅ |

---

## Current State

- ✅ Three-agent coordination (PM, Planner, Engineer)
- ✅ Flask API backend with async execution
- ✅ SQLite database with full persistence
- ✅ Project management and execution history
- ✅ Complete observability (all artifacts visible)
- ✅ Deterministic, replayable workflows
- ✅ Schema validation at all boundaries
- ✅ Enterprise UI live on enterprise-ui branch (10 screens, light + dark)
- ✅ Iterative pipeline with version history (Phase 7A complete)
- ✅ Real log persistence + instant navigation-back (sessionStorage caching)
- 🔴 Live preview — elevated priority (Phase 7B)
- ⬜ Client deliverables — PDF export, sharing (Phase 7C)

---

## Non-Goals

- Fully autonomous unsupervised code deployment
- Magic generation without traceability
- Hidden state or implicit agent behavior
