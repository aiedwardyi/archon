# Current Sprint — Phase 4: Observable UI + Hardening

## Sprint Goal

Make the system **operationally observable** and **contract-enforced** by adding a read-only UI for execution/evaluation artifacts and hardening schema boundaries—without introducing hidden state or network dependency.

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

## Phase 4 Work Items (Executable)

### 1. Read-only “Artifacts” UI Panel
**Status:** Done

- Add a UI section that renders:
  - `last_execution_request.json`
  - `last_execution_result.json`
  - `last_evaluation_result.json`
- Add empty-state handling if files do not exist
- No writes or mutations from the UI

---

### 2. Read-only “History” UI Panel (NDJSON)
**Status:** Next

- Render append-only histories:
  - `execution_requests.ndjson`
  - `execution_results.ndjson`
  - `evaluation_results.ndjson`
- Provide basic filtering by request_hash / task_id (client-side only)
- Robust parsing: ignore malformed lines and surface count of skipped lines

---

### 3. Strict Schema Enforcement at Boundaries
**Status:** Planned

- Ensure consumer validates:
  - ExecutionRequest input
  - ExecutionResult output
  - EvaluationResult output
- Failures become visible artifacts (no silent exceptions)

---

### 4. Deterministic Replay Runner
**Status:** Planned

- Script that replays a request selected from `execution_requests.ndjson`
- Runs offline only (no network calls)
- Produces execution/evaluation artifacts deterministically

---

## Definition of Done (Sprint)

- Read-only UI shows last artifacts reliably (offline-safe)
- Read-only UI shows NDJSON histories with safe parsing and filtering
- Schema boundary enforcement prevents invalid artifacts from silently passing
- Deterministic replay runner exists and is covered by regression tests
- No hidden state introduced
- All tests passing
- ROADMAP.md updated if scope/status changes

---