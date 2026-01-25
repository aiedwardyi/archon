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
  The system operates without network calls when required.

- **Observable state**  
  Execution requests, plans, and results are written as files.

- **Failure visibility**  
  Errors are surfaced as artifacts, not hidden in logs.

---

## Phased Execution Plan

### Phase 1 — Foundations (Completed)
- Schema-validated PRD generation
- Planner producing milestone/task plans
- Deterministic offline regeneration
- Safe file write allowlists (foundation)
- Frontend rendering PRD + Plan artifacts

### Phase 2 — Interactive Execution (Completed)
- Lovable-style milestone/task UI
- Deterministic execution request emission
- UI → backend artifact handoff
- Append-only execution logs
- Offline fallback behavior

### Phase 3 — Orchestration & Evaluation (Completed)
- Orchestrator consumes execution request artifacts (Completed)
- Execution result artifacts (Completed)
- Regression tests for determinism (Completed; includes golden snapshot guard)
- Deterministic task execution (Completed)
- Evaluation harness for output quality (Completed)

### Phase 4 — Production Hardening (Planned; executable scope defined)
**Goal:** Make the system operationally observable and enforce contracts strictly without introducing hidden state.

**Deliverables**
1. **Observable UI for Execution + Evaluation (read-only)**
   - UI displays:
     - `public/last_execution_request.json`
     - `public/last_execution_result.json`
     - `public/last_evaluation_result.json`
     - Append-only NDJSON histories:
       - `public/execution_requests.ndjson`
       - `public/execution_results.ndjson`
       - `public/evaluation_results.ndjson`
   - No mutation of artifacts from UI (read-only)
   - Offline-first behavior preserved

2. **Strict schema enforcement in consumer pipeline**
   - Requests/results/evaluation artifacts are schema-validated at boundaries
   - Failures surfaced as artifacts (no silent failure)

3. **Replayable execution history (deterministic)**
   - Script to replay a chosen request from history into deterministic execution
   - No network calls
   - Produces deterministic artifacts identical to original given same inputs

4. **Regression coverage extension**
   - Tests cover observable UI parsing logic (pure functions) and replay runner determinism
   - Golden snapshots expanded only when required

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