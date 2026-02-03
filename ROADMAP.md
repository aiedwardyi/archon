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

### Phase 1 — Foundations (Completed)
- Schema-validated PRD generation
- Planner producing milestone/task plans
- Deterministic offline regeneration
- Safe file write allowlists
- Frontend rendering PRD + Plan artifacts

---

### Phase 2 — Interactive Execution (Completed)
- Lovable-style milestone/task UI
- Deterministic execution request emission
- UI → backend artifact handoff
- Append-only execution logs
- Offline fallback behavior

---

### Phase 3 — Orchestration & Evaluation (Completed)
- Orchestrator consumes execution request artifacts
- Deterministic execution result artifacts
- Evaluation harness producing pass/fail artifacts
- Canonical hashing for semantic identity
- Golden snapshot regression tests
- All tests passing

---

### Phase 4 — Production Hardening (Completed)
- Read-only UI for last execution/evaluation artifacts (**Completed**)
- Read-only UI for NDJSON execution/evaluation histories (**Completed**)
- Strict schema enforcement at system boundaries (**Completed**)
- Deterministic replay runner for past executions (**Completed**)
- Replay metadata surfaced in UI artifacts (**Completed**)

---

### Phase 5 — Expansion & Multi-Agent Coordination (Planned)
- Replayable execution history across agents
- Multi-agent task coordination
- Extended agent roles (PM / Planner / Engineer)
- SaaS-ready architectural decisions

---

## Non-Goals

- Fully autonomous unsupervised code deployment
- “Magic” generation without traceability
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