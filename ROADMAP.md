# AI Dev Team — Execution Roadmap

## Purpose

This repository implements a deterministic, offline-first **AI Dev Team system** inspired by Lovable-style workflows.

The goal is to demonstrate production-grade applied AI engineering:
- explicit agent roles
- schema-based contracts
- deterministic orchestration
- observable execution artifacts
- safe, auditable file writes

This is not a demo generator. It is designed to behave like a real internal AI-assisted development system.

---

## High-Level Architecture

**Flow**

User idea
→ Product Manager (PRD)
→ Planner (Plan schema: milestones + tasks)
→ Deterministic Orchestrator
→ Engineer agent
→ Safe file writes
→ Observable artifacts

**Key principle:**
Every step emits structured artifacts that can be inspected, validated, and replayed.

---

## Design Principles

- **Determinism first**
  Identical inputs produce identical artifacts.

- **Explicit contracts**
  JSON schemas define all agent boundaries.

- **Offline-first**
  The system operates without network calls.

- **Observable state**
  Execution requests, plans, results, and evaluations are written as files.

- **Failure visibility**
  Errors surface as artifacts, not hidden logs.

---

## Phased Execution Plan

### Phase 1 — Foundations (✅ Completed)
- Schema-validated PRD generation
- Planner producing milestone/task plans
- Deterministic offline regeneration
- Safe file write allowlists
- Frontend rendering PRD + Plan artifacts

---

### Phase 2 — Interactive Execution (✅ Completed)
- Lovable-style milestone/task UI
- Deterministic execution request emission
- UI → backend artifact handoff
- Append-only execution logs
- Offline fallback behavior

---

### Phase 3 — Orchestration & Evaluation (✅ Completed)
- Orchestrator consumes execution request artifacts
- Deterministic execution result artifacts
- Evaluation harness producing pass/fail artifacts
- Canonical hashing for semantic identity
- Golden snapshot regression tests
- All tests passing

---

### Phase 4 — Production Hardening (✅ Completed)
- Read-only UI for last execution/evaluation artifacts
- Read-only UI for NDJSON execution/evaluation histories
- Strict schema enforcement at system boundaries
- Deterministic replay runner for past executions
- Replay metadata surfaced in UI artifacts

---

### Phase 5 — Multi-Agent Coordination (✅ Completed)

**Accomplished:**
- Multi-agent workflow: PM (OpenAI) → Planner (Gemini) → Engineer (Gemini)
- Flask API backend: Async execution with threading, state tracking
- React UI integration: Task execution with polling and toast notifications
- Agent sequence tracking: Metadata preserved throughout entire chain
- File-based handoffs: PRD → Plan → Execution Request → Execution Result
- Automated workflow: No manual script execution required

---

### Phase 6.1 — Project History & Persistence (✅ Completed)

- SQLite with SQLAlchemy ORM
- Project management: create, view, organize projects
- Execution tracking linked to projects
- React Router multi-page navigation
- Project selection modal during execution

---

### Phase 6.2 — Enhanced UI/UX (✅ Completed)

- Polished dark/light mode UI with Tailwind
- Sidebar navigation with smooth transitions
- ArtifactViewer: PRD, Plan, Code tabs with real backend data
- ProjectDetailPage with full agent workflow visualization
- Mobile-responsive layout
- Monorepo consolidation: frontend moved into ai-dev-team repo

---

### Phase 6.3 — Differentiator Features & Polish (✅ Completed)

**Accomplished:**
- Agent chain badge in ArtifactViewer (pm → planner → engineer)
- Replay + JSON + Copy buttons moved to artifact title row
- Raw JSON toggle with syntax highlighting and line numbers
- VS Code-style folder tree explorer in Code artifact view
- Terminal log colors, chat filter, tech map category detection
- Sidebar status dots: blue pulsing=running, green=completed, red=failed
- Clear All Projects with DELETE ALL confirmation modal
- Engineer prompt: max 1 README, 6 file cap, functional files focus
- safe_write.py: expanded allowlist (.sql, .prisma, .graphql, .env.example)
- Duplicate file dedup in engineer_agent.py and orchestrator.ts
- Tasks view shows full relative paths (src/frontend/package.json)
- GitHub SOURCE link on landing page
- All changes committed

---

### Phase 7A — Iterative Pipeline & Version History (🚧 Next)

**Goal:** Transform Archon from a single-shot generator into a true iterative
build tool. Every prompt submission runs the full pipeline and creates a
versioned snapshot — making Archon auditable across the entire build history.

**Key differentiator:** Full pipeline re-run on every iteration (PM → Planner
→ Engineer) with complete artifact trail per version. Lovable/Bolt have no
equivalent audit trail.

**Work Items:**
- 7A.1 Backend: versioned execution storage + prompt history in DB
- 7A.2 Backend: /iterate and /restore endpoints
- 7A.3 Frontend: continuous chat panel (always visible, Lovable-style)
- 7A.4 Frontend: clock icon + history drawer (version timeline)
- 7A.5 Frontend: version preview + restore flow (with forward-restore support)

**Architecture:**
- Each execution stores version number + full prompt_history array
- Prompt history passed to PM agent for context continuation
- Restore sets is_active_head flag; past versions remain accessible
- Version labels: truncated prompt snippet (~35 chars) + timestamp

**UI:**
- Chat panel replaces single input box — continuous conversation
- Clock icon in chat header → slides open history drawer
- History drawer: v1/v2/v3 with truncated prompt + timestamp
- Clicking version previews that snapshot's artifacts (read-only)
- Restore button loads version into main panel; forward-restore supported
- New prompt from restored version creates a new branch (v4+)

---

### Phase 7B — Live Preview (⬜ Planned)

**Goal:** Replace the static placeholder preview with a real running iframe
of the engineer's generated output.

**Work Items:**
- 7B.1 Engineer agent: prompt engineering for self-contained runnable output
- 7B.2 Backend: dynamic file serving route (/preview/:projectId/:version)
- 7B.3 Frontend: iframe preview panel loading generated files
- 7B.4 History integration: clicking past version loads that version in iframe

---

## Competitive Positioning

| Feature | Lovable/Bolt | Archon |
|---------|-------------|--------|
| Context continuation | ✅ | ✅ |
| Full chain on every edit | ❌ | ✅ |
| Artifact trail per version | ❌ | ✅ |
| Restore previous version | ✅ | ✅ |
| Restore forward after revert | ❌ | ✅ |
| Auditable PRD per iteration | ❌ | ✅ |
| Agent chain visibility | ❌ | ✅ |
| Schema validation | ❌ | ✅ |

---

## Current State

**Production-ready multi-agent system with full UI polish:**
- ✅ Three-agent coordination (PM, Planner, Engineer)
- ✅ Flask API backend with async execution
- ✅ SQLite database with full persistence
- ✅ Project management and execution history
- ✅ React UI with multi-page navigation and dark/light mode
- ✅ Complete observability (all artifacts visible)
- ✅ Deterministic, replayable workflows
- ✅ Schema validation at all boundaries
- ✅ Polished UI/UX with mobile support
- ✅ Differentiator features visible in UI
- 🚧 Iterative pipeline with version history (Phase 7A)
- ⬜ Live preview (Phase 7B)

**Architecture:**
```
User Input (Chat Panel)
    ↓
Prompt History (context continuation)
    ↓
PM Agent (OpenAI) → PRD artifact (versioned)
    ↓
Planner Agent (Gemini) → Plan artifact (versioned)
    ↓
Flask API → Execution Record (Database, version N)
    ↓
Engineer Agent (Gemini) → Code files (versioned)
    ↓
Execution Result → Database + UI + History Timeline
```

---

## Non-Goals

- Fully autonomous unsupervised code deployment
- "Magic" generation without traceability
- Hidden state or implicit agent behavior

---

## Quality Bar

A change is considered complete only if:
- artifacts are deterministic
- schemas are validated
- failure modes are visible
- outputs can be reasoned about by inspection

---

## Audience

This repository is intended for:
- Applied AI / LLM engineers
- Platform engineers
- Founders building AI-assisted developer tooling
- Teams evaluating deterministic agent orchestration patterns
