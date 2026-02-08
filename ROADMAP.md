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

## Current State

**Production-ready multi-agent system with:**
- ✅ Three-agent coordination (PM, Planner, Engineer)
- ✅ Flask API backend with async execution
- ✅ React UI with automated task execution
- ✅ Complete observability (all artifacts visible)
- ✅ Deterministic, replayable workflows
- ✅ Schema validation at all boundaries

**Architecture:**
```
User Input (UI)
    ↓
PM Agent (OpenAI) → PRD artifact
    ↓
Planner Agent (Gemini) → Plan artifact
    ↓
Flask API → Execution Request
    ↓
Engineer Agent (Gemini) → Code files
    ↓
Execution Result → UI notification
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

---
