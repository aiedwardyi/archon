# Current Sprint — Phase 5: Multi-Agent Coordination (Foundations)

## Sprint Goal

Introduce **explicit multi-agent coordination** into the system by adding
role attribution and deterministic handoffs between agents — without
introducing autonomy, hidden state, or new subsystems.

This phase proves that multiple agents can collaborate through
**structured, replayable artifacts**.

---

## Current State (Verified)

- Offline-first frontend (Vite + React + TypeScript)
- Deterministic execution request emission
- Deterministic consumer producing execution results
- Deterministic evaluator producing pass/fail artifacts
- Strict schema enforcement at all boundaries
- Golden snapshot regression tests
- Deterministic replay runner with UI visibility
- All Phase 4 work completed and tagged
- **Multi-agent coordination operational (PM → Planner → Engineer)**

---

## Phase 5 Work Items (Executable)

### 1. Agent Role Attribution in Execution Results
**Status:** ✅ COMPLETED

- Extended `ExecutionResult` schema with `agent_role` field
- Consumer writes `agent_role: "engineer"` into all execution artifacts
- Schema validation enforces agent role presence
- Visible in UI artifacts panel
- Metadata-only change (no behavior modification)

---

### 2. Deterministic Agent Handoff Contract
**Status:** ✅ COMPLETED

**Completed:**
- ✅ Created PRD schema with 14 validated sections
- ✅ Implemented PM agent using OpenAI structured outputs
- ✅ PM agent generates PRD artifacts with `agent_role: "pm"`
- ✅ PRD artifacts written to `artifacts/last_prd.json`
- ✅ Updated PlannerAgent to consume PRD artifacts
- ✅ Planner reads PRD, generates Plan with milestones/tasks
- ✅ Engineer consumes Plan, generates code (verified working)
- ✅ End-to-end test: Calculator app → PRD → Plan (5 milestones, 21 tasks) → Code (3 files)
- ✅ Full chain validated: PM (OpenAI) → Planner (Gemini) → Engineer (Gemini)

**Handoff implementation:**
- PM produces PRD artifact → `artifacts/last_prd.json`
- Planner consumes PRD → produces Plan artifact → `artifacts/last_plan.json`
- Engineer consumes Plan → produces code artifacts

All handoffs are:
- ✅ File-based (no in-memory passing)
- ✅ Deterministic (same input = same output)
- ✅ Replayable (can re-run from any artifact)
- ✅ Schema-validated at each boundary
- ✅ Agent-attributed (each artifact shows producing agent)

---

### 3. Multi-Agent Orchestration & Execution
**Status:** 🔄 IN PROGRESS

**Completed:**
- ✅ Created `scripts/orchestrate_multi_agent.py` - Production orchestrator
  - Runs PM → Planner chain
  - Saves PRD and Plan artifacts with agent sequence metadata
  - CLI interface with `@file.txt` syntax support
- ✅ Updated `App.tsx` to unwrap `plan_artifact` format (backward compatible)
- ✅ Added `last_plan.json` to ArtifactsPanel UI
- ✅ Agent sequence visualization in UI (`pm → planner`)
- ✅ Integrated Engineer agent into `deterministic_executor.py`
  - Consumes task_snapshot from execution requests
  - Generates code files via EngineerAgent
  - Writes to `public/generated/` directory
- ✅ Extended `safe_write.py` to support web development file types
  - Added .html, .css, .js, .jsx, .ts, .tsx, .py, etc.
  - Allows files without extensions (e.g., .gitignore)
- ✅ End-to-end verification: orchestrator → plan → task execution → code generation

**Remaining:**
- ⏳ UI workflow improvements:
  - Auto-save execution requests to file (currently uses localStorage)
  - Add visual feedback when "Execute task" is clicked
  - Consider backend endpoint or sync script for request persistence
- ⏳ Multi-agent replay support:
  - Replay runner must preserve agent role metadata
  - Replay agent handoffs deterministically
  - UI must show agent role per execution and sequence of agent actions

---

## Definition of Done (Sprint)

- ✅ Execution and evaluation artifacts clearly identify the producing agent
- ✅ Agent-to-agent handoffs are explicit and file-based
- 🔄 Multi-agent executions are replayable (UI workflow improvements needed)
- ✅ No hidden state or implicit memory
- ✅ All tests passing
- 🔄 ROADMAP.md needs update to reflect Phase 5 progress

---

## Next Steps

1. Fix UI execution request persistence (localStorage → file)
2. Add user feedback for task execution
3. Complete multi-agent replay runner
4. Update ROADMAP.md to mark Phase 5 progress
5. Tag Phase 5 completion when all items done
