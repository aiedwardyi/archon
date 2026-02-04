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
**Status:** Planned

- Extend `ExecutionResult` to include:
  - `agent_role` (e.g. `"planner"`, `"engineer"`)
- Agent role must be:
  - explicitly written into artifacts
  - validated by schema
  - visible in UI artifacts panel
- No behavior change yet — metadata only

---

### 2. Deterministic Agent Handoff Contract
**Status:** Planned

- Define a rule:
  - one agent consumes the **previous agent’s artifact**
- Example:
  - Planner produces a Plan artifact
  - Engineer consumes that Plan via an ExecutionRequest
- Handoff must be:
  - file-based
  - deterministic
  - replayable

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

- Execution and evaluation artifacts clearly identify the producing agent
- Agent-to-agent handoffs are explicit and file-based
- Multi-agent executions are replayable
- No hidden state or implicit memory
- All tests passing
- ROADMAP.md remains accurate
