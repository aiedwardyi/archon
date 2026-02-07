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
**Status:** 🔄 IN PROGRESS

**Completed:**
- ✅ Created PRD schema with 14 validated sections
- ✅ Implemented PM agent using OpenAI structured outputs
- ✅ PM agent generates PRD artifacts with `agent_role: "pm"`
- ✅ PRD artifacts written to `artifacts/last_prd.json`
- ✅ Validation example: Todo List PRD generated

**Remaining:**
- [ ] Planner agent consumes PRD artifact (currently reads from old location)
- [ ] Update planner to read from `artifacts/last_prd.json`
- [ ] Engineer consumes Plan artifact (verify existing flow)
- [ ] End-to-end test: PM → Planner → Engineer handoff
- [ ] UI displays PRD artifacts

**Handoff definition:**
- PM produces PRD artifact → `artifacts/last_prd.json`
- Planner consumes PRD → produces Plan artifact
- Engineer consumes Plan → produces code artifacts

All handoffs must be:
- File-based (no in-memory passing)
- Deterministic (same input = same output)
- Replayable (can re-run from any artifact)

---

### 3. Multi-Agent Replay Support
**Status:** Planned

- Replay runner must:
  - preserve agent role metadata
  - replay agent handoffs deterministically
- UI must show:
  - agent role per execution
  - sequence of agent actions

---

## Definition of Done (Sprint)

- ✅ Execution and evaluation artifacts clearly identify the producing agent
- 🔄 Agent-to-agent handoffs are explicit and file-based (in progress)
- ⏳ Multi-agent executions are replayable
- ✅ No hidden state or implicit memory
- ✅ All tests passing
- 🔄 ROADMAP.md remains accurate

---