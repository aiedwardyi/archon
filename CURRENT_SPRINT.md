# Current Sprint — Interactive Execution Loop

## Sprint Goal

Complete the UI → backend → file artifact loop so that user-triggered tasks become deterministic, observable execution requests that the orchestrator can consume, execute deterministically, and regress safely.

---

## Current State (Verified)

- Offline-first frontend (Vite + React + TypeScript)
- Lovable-style milestone/task board
- Deterministic task selection + execution request emission
- Local backend persistence with offline fallback
- Orchestrator consumer produces result artifacts
- Determinism enforced by canonical hashing + tests
- Golden snapshot regression guard in place
- Deterministic task execution with safe allow-listed writes
- Deterministic evaluation harness producing pass/fail artifacts

---

## Completed Work

### 1. UI → Backend Execution Request Handoff
**Status:** Completed

- POST `/execution-request`
- Overwrite `public/last_execution_request.json`
- Append `public/execution_requests.ndjson`
- Offline-first fallback

---

### 2. Execution Artifact Consumption
**Status:** Completed

- Consumer reads last request
- Schema-validated processing
- Writes `public/last_execution_result.json`
- Appends `public/execution_results.ndjson`

---

### 3. Determinism Tests
**Status:** Completed

- Canonical request hashing (semantic identity)
- Consumer determinism regression tests
- Golden snapshot stored under `tests/snapshots/`
- Snapshot-based regression test compares canonicalized results
- All tests passing

---

### 4. Deterministic Task Execution
**Status:** Completed

- Deterministic executor implemented (offline-first)
- Allow-listed file writes only (no path traversal, restricted extensions)
- Outputs include observable write records (path / sha256 / bytes)
- Runtime-generated outputs ignored by git

---

### 5. Evaluation Harness
**Status:** Completed

- Deterministic, machine-checkable evaluation (no LLM judgment)
- Runs automatically after every successful execution
- File-based and decoupled from execution
- Writes `public/last_evaluation_result.json`
- Appends `public/evaluation_results.ndjson`
- Pass/fail status with structured failure reasons
- Windows-safe JSON handling (`utf-8` / `utf-8-sig`)
- Covered by golden snapshot regression tests

---

## Definition of Done (Sprint)

- Execution request → deterministic execution → result artifacts
- Deterministic hashing for semantic identity
- Snapshot-based regression protection
- Deterministic evaluation with machine-checkable rules
- No hidden state between UI and orchestrator
- Safe, allow-listed file writes
- All artifacts human-readable and replayable

---

## Notes

This sprint prioritized:
- Determinism over novelty
- Observability over autonomy
- Reproducibility across machines
- Safety over convenience
