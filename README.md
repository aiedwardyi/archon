# AI Dev Team (MVP #2)

Schema-driven multi-agent system that converts product ideas into structured implementation plans.

## Current Capabilities
- PM agent → PRD generation
- Planner agent → schema-validated execution plan
- Deterministic orchestrator
- Run logging for reproducibility

## Status
Month 2, Week 1 — Planning & orchestration complete.

## Determinism & Execution Guarantees

This system is designed to be **replayable and deterministic**.

### What determinism means here
- Identical *semantic* execution requests produce identical execution results
- Allowed non-deterministic fields (timestamps, transport metadata) are excluded from hashing
- Execution is fully file-based and observable

### How determinism is enforced
- Canonical request hashing (ignores `created_at`, `_meta`)
- Schema-validated execution requests and results
- Regression tests that re-run the same request and assert identical outputs

### Run determinism tests (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_tests.ps1
```
Expected result:
- All tests pass
- Exit code `0`

These tests act as a regression guard against hidden state, schema drift, or non-deterministic behavior.
