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

### 2. Execution Artifact Consumption (Next)
**Status:** Not started

Planned:
- Orchestrator polls or watches `last_execution_request.json`
- Validates against schema
- Executes task deterministically
- Writes `last_execution_result.json`
- Appends execution results to NDJSON log

---

### 3. Determinism Tests
**Status:** Planned

Planned:
- Re-run identical execution requests
- Assert identical outputs
- Detect schema drift regressions
- Snapshot-based verification

---

## Immediate Next Steps

1. Implement orchestrator consumer for execution requests
2. Define execution result schema
3. Write first end-to-end execution test
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
