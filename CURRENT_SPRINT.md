# Current Sprint — Phase 4: Observable UI + Hardening

## Sprint Goal

Make the system **operationally observable** and **contract-enforced** by adding read-only UI surfaces for execution and evaluation artifacts, and by hardening schema boundaries — without introducing hidden state or network dependency.

---

## Current State (Verified)

- Offline-first frontend (Vite + React + TypeScript)
- Lovable-style milestone/task board
- Deterministic task selection + execution request emission
- Local backend persistence with offline fallback
- Orchestrator consumer produces deterministic execution result artifacts
- Determinism enforced via canonical hashing + regression tests
- Golden snapshot regression guard in place
- Deterministic task execution with safe allow-listed writes
- Deterministic evaluation harness producing pass/fail artifacts
- Observable UI for runtime artifacts and histories (Phase 4)

---

## Phase 4 Work Items (Executable)

### 1. Read-only “Artifacts” UI Panel
**Status:** Done

- UI renders:
  - `last_execution_request.json`
  - `last_execution_result.json`
  - `last_evaluation_result.json`
- Files are loaded directly from `public/`
- Missing files and parse errors are surfaced as visible UI state
- UI performs **no writes or mutations**

---

### 2. Read-only “History” UI Panel (NDJSON)
**Status:** Done

- UI renders append-only histories:
  - `execution_requests.ndjson`
  - `execution_results.ndjson`
  - `evaluation_results.ndjson`
- Robust line-by-line NDJSON parsing
- Malformed lines are ignored and counted (visible in UI)
- Client-side filtering by:
  - `task_id`
  - `request_hash`
- UI is strictly read-only and offline-safe

---

### 3. Strict Schema Enforcement at Boundaries
**Status:** Done

- Enforce schema validation for:
  - ExecutionRequest input
  - ExecutionResult output
  - EvaluationResult output
- Validation failures must produce visible artifacts
- No silent exceptions or hidden failure paths

---

### 4. Deterministic Replay Runner
**Status:** Done

- Script to replay a selected request from `execution_requests.ndjson`
- Offline-only execution (no network calls)
- Deterministic reproduction of:
  - execution result
  - evaluation result
- Covered by regression tests

---

## Definition of Done (Sprint)

- Observable UI surfaces for last artifacts and full histories
- Robust handling of missing or malformed runtime data
- Strict schema enforcement at all system boundaries
- Deterministic replay capability for past executions
- No hidden state introduced
- All tests passing
- `ROADMAP.md` reflects accurate phase status