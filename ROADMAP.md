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
- **Multi-agent workflow:** PM (OpenAI) → Planner (Gemini) → Engineer (Gemini)
- **Flask API backend:** Async execution with threading, state tracking
- **React UI integration:** Task execution with polling and toast notifications
- **Agent sequence tracking:** Metadata preserved throughout entire chain (`_agent_sequence`)
- **File-based handoffs:** PRD → Plan → Execution Request → Execution Result
- **Automated workflow:** No manual script execution required
- **Production-ready patterns:** Async processing, proper error handling, user feedback

**Technical Implementation:**
- PM agent generates structured PRDs using OpenAI structured outputs
- Planner consumes PRDs, generates plans with milestones and tasks
- Engineer executes tasks, generates code files deterministically
- Flask backend manages async execution with background threading
- React frontend polls for completion, shows toast notifications
- All artifacts schema-validated at boundaries
- Agent metadata tracked end-to-end for observability

**UI Features:**
- Click "Execute task" → automated PM → Planner → Engineer flow
- Real-time status polling (every 2 seconds)
- Visual feedback with toast notifications (blue start, green success, red error)
- Artifacts panel shows agent sequence for each execution
- No page refreshes interrupt workflow

---

### Phase 6.1 — Project History & Persistence (✅ Completed)

**Accomplished:**
- **Database persistence:** SQLite with SQLAlchemy ORM
- **Project management:** Create, view, organize projects
- **Execution tracking:** Link executions to projects with full history
- **React Router:** Multi-page navigation (Board, Projects, Project Detail)
- **Project selection:** Choose project before task execution

**Technical Implementation:**
- Database models: Project and Execution tables with relationships
- Flask API endpoints: CRUD operations for projects
- Project-linked executions: Each execution record tied to a project
- React UI: Projects list view, project detail view with execution history
- Project selection modal: Dropdown + quick project creation during execution

**Database Schema:**
- `projects` table: id, name, description, status, timestamps
- `executions` table: id, project_id, status, artifact paths, timestamps
- One-to-many relationship: project → executions

**UI Features:**
- Projects page with grid view of all projects
- Click project → view execution history
- Create projects with name and description
- Select project before executing tasks
- Status indicators (pending, in_progress, completed, failed)
- Execution count per project

---

### Phase 6.2 — Enhanced UI/UX (✅ Completed)

**Accomplished:**
- **Polished dark/light mode UI** with Tailwind design system
- **Sidebar navigation** with smooth transitions
- **ArtifactViewer component** rendering PRD, Plan, and Code artifacts
- **ProjectDetailPage** with full agent workflow visualization
- **Live code preview** with syntax highlighting
- **Real backend wiring** — all artifact tabs connected to Flask API
- **Data normalization** between backend schemas and frontend types
- **Error handling** with backend connection overlay
- **Mobile-responsive** layout with chat/preview toggle
- **Fault monitor** with simulated error injection and fix flow
- **Agent status messages** with animated progress indicators
- **Monorepo consolidation** — frontend moved into ai-dev-team repo

**Technical Implementation:**
- React + TypeScript + Vite + Tailwind CSS
- Vite dev server on port 3000, Flask API on port 5000
- orchestrator.ts: BackendService class with normalizePrd/Plan/Code
- ArtifactViewer: Renders PRD (document), Plan (timeline), Code (editor)
- ProjectDetailPage: Tabs for Preview/Brief/PRD/Plan/Code/Tasks/Logs
- Custom syntax highlighter for TypeScript/Python/JSON
- File explorer sidebar in code view
- Polling-based execution status with 2-second intervals

---

### Phase 6.3 — Differentiator Features & Polish (🚧 In Progress)

**Goal:** Surface the platform's key competitive advantages in the UI —
determinism, replayability, schema validation, and agent chain transparency.

**Work Items:**
1. ✅ ROADMAP.md and CURRENT_SPRINT.md updated
2. ⬜ Agent chain badge in ArtifactViewer (pm → planner → engineer | Replayable | Schema Validated)
3. ⬜ Replay button in ProjectDetailPage header (re-runs full pipeline)
4. ⬜ Raw JSON toggle in ArtifactViewer ({ } button next to Copy Artifact)

**Differentiator Story:**
These features make the platform's architecture visible to users and evaluators.
Unlike Lovable and Bolt (chat-based, opaque), our system shows:
- Which agents produced each artifact
- That outputs are replayable (deterministic)
- That every artifact passes schema validation
- The full agent sequence for audit/debug purposes

---

## Current State

**Production-ready multi-agent system with polished UI and project management:**
- ✅ Three-agent coordination (PM, Planner, Engineer)
- ✅ Flask API backend with async execution
- ✅ SQLite database with full persistence
- ✅ Project management and execution history
- ✅ React UI with multi-page navigation and dark/light mode
- ✅ Complete observability (all artifacts visible)
- ✅ Deterministic, replayable workflows
- ✅ Schema validation at all boundaries
- ✅ Polished UI/UX with mobile support
- 🚧 Differentiator features (agent chain badge, replay, JSON toggle)

**Architecture:**
```
User Input (UI)
    ↓
Project Selection
    ↓
PM Agent (OpenAI) → PRD artifact
    ↓
Planner Agent (Gemini) → Plan artifact
    ↓
Flask API → Execution Record (Database)
    ↓
Engineer Agent (Gemini) → Code files
    ↓
Execution Result → Database + UI notification
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
