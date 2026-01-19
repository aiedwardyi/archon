# Current Sprint — Interactive Execution Loop

## Sprint Goal

Complete the UI → backend → file artifact loop so that user-triggered tasks become deterministic, observable execution requests that the orchestrator can later consume.

---

## Current State (Verified)

- Offline-first frontend (Vite + React + TypeScript)
- Lovable-style milestone/task board
- Task selection updates detail panel deterministically
- PRD + Plan rendered from static artifacts in `public/`
- Execution request emitted from UI
- Local backend endpoint persists execution artifacts to disk
- Fallback to localStorage when backend unavailable
- Orchestrator consumer reads request artifacts and writes deterministic result artifacts

---

## Active Work

### 1. UI → Backend Execution Request Handoff
**Status:** Completed

- POST `/execution-request` endpoint
- Overwrites `public/last_execution_request.json`
- Appends to `public/execution_requests.ndjson`
- CORS configured for local dev
- Timeout + offline fallback in frontend

---

### 2. Execution Artifact Consumption
**Status:** Completed

Implemented:
- Orchestrator consumer reads `public/last_execution_request.json`
- Validates minimum required fields
- Writes `public/last_execution_result.json` (overwrite)
- Appends `public/execution_results.ndjson` (append-only)

---

### 3. Determinism Tests
**Status:** Next

Planned:
- Re-run identical execution requests
- Assert identical outputs (excluding permitted non-deterministic fields)
- Detect schema drift regressions
- Snapshot-based verification

---

## Immediate Next Steps

1. Define execution result schema (explicit contract)
2. Add first determinism regression test (same request → same result)
3. Wire an optional backend endpoint to trigger the consumer (nice-to-have)
4. Add README architecture diagram

---

## Definition of Done (Sprint)

- Execution request → result loop fully file-based
- No hidden state between UI and orchestrator
- All artifacts human-readable and replayable
- Failures produce explicit error artifacts

---

## Notes

This sprint intentionally prioritizes:
- correctness over speed
- observability over autonomy
- determinism over novelty
