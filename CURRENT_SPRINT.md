# Current Sprint — Phase 6.3: Differentiator Features & Polish

## Sprint Goal

Surface the platform's **key competitive advantages** visually in the UI:
determinism, replayability, schema validation, and agent chain transparency.

This phase makes the architecture *visible* — not just functional.
These are the features that differentiate us from Lovable, Bolt, and other
chat-based tools that produce opaque, non-replayable outputs.

---

## Context: What Makes Us Different

| Feature | Lovable/Bolt | AI Dev Team |
|---------|-------------|-------------|
| Agent chain visibility | ❌ Hidden | ✅ Shown on every artifact |
| Replayability | ❌ No | ✅ Replay button re-runs full pipeline |
| Schema validation | ❌ No | ✅ Badge on every artifact |
| Raw artifact inspection | ❌ No | ✅ JSON toggle in viewer |
| Deterministic outputs | ❌ No | ✅ Same input = same output |

---

## Current State (Verified ✅)

- Phase 6.2 complete: Polished UI/UX with full backend wiring
- All artifact tabs working (PRD, Plan, Code, Tasks, Logs)
- Dark/light mode, mobile layout, sidebar navigation
- Flask backend on port 5000, Vite frontend on port 3000
- Repo clean and committed

---

## Phase 6.3 Work Items

### 1. Update Documentation
**Status:** ✅ COMPLETED

- ✅ ROADMAP.md updated to mark Phase 6.2 complete, 6.3 in progress
- ✅ CURRENT_SPRINT.md rewritten for Phase 6.3

---

### 2. Agent Chain Badge in ArtifactViewer
**Status:** ⬜ TODO

**What:** A banner strip inside `ArtifactViewer.tsx` that shows:
```
🔗 pm → planner → engineer   |   ♻️ Replayable   |   ✅ Schema Validated
                                                    [↺ Replay]  [{ } JSON]
```

**Design (from screenshots):**
- Pill/badge strip between the artifact header and the content area
- Left side: agent chain with arrows (`pm → planner → engineer`)
- Middle badges: green "REPLAYABLE" pill, green "SCHEMA VALIDATED" pill
- Right side: "REPLAY" button (purple/indigo filled), "{ } JSON" button (outlined)
- Shows on: PRD, Plan, and Code artifact types

**Technical:**
- Agent sequence comes from `artifact.agent` field
- Map agent name → sequence: PM Agent → "pm", Planner Agent → "pm → planner", Engineer Agent → "pm → planner → engineer"
- Replay button calls `backend.startExecution(artifact.projectId)` 
- JSON toggle is local state (`showJson: boolean`) in ArtifactViewer
- When JSON is active, render raw `<pre>` instead of rich view

**Files to modify:**
- `frontend/components/ArtifactViewer.tsx`

---

### 3. Raw JSON Toggle
**Status:** ⬜ TODO (bundled with item 2 above)

**What:** `{ }` button next to "Copy Artifact" that toggles between rendered view and raw JSON

**Design (from screenshots):**
- Outlined button with `{ }` icon text
- When active: shows formatted JSON with line numbers
- When inactive: shows normal rich render (PRD/Plan/Code view)
- State lives in ArtifactViewer component (`showRawJson` boolean)

**Files to modify:**
- `frontend/components/ArtifactViewer.tsx`

---

### 4. Replay Button in ProjectDetailPage Header
**Status:** ⬜ TODO

**What:** An "↺ Replay" button in the ProjectDetailPage header that re-runs the full PM → Planner → Engineer pipeline for the current project

**Design:**
- Only visible when `project.status === 'COMPLETED'`
- Label: "↺ Replay" 
- Style: outlined/secondary (not the primary Deploy button style)
- Calls `backend.startExecution(projectId)`
- Reinforces the determinism/replayability story

**Files to modify:**
- `frontend/pages/ProjectDetailPage.tsx`

---

## Definition of Done (Sprint)

- ✅ ROADMAP.md and CURRENT_SPRINT.md updated
- ⬜ Agent chain badge visible on all artifact tabs (PRD, Plan, Code)
- ⬜ Replay button visible in header when project.status === 'COMPLETED'
- ⬜ JSON toggle works — switches between rich view and raw JSON
- ⬜ Agent sequence correctly mapped from artifact.agent field
- ⬜ All changes committed and pushed

---

## Files In Scope
```
frontend/
  components/
    ArtifactViewer.tsx     ← Main work: badge + JSON toggle
  pages/
    ProjectDetailPage.tsx  ← Add Replay button to header
```

## Files NOT to touch
```
frontend/services/orchestrator.ts   (working, don't break)
frontend/types.ts                   (no schema changes needed)
backend/                            (no backend changes for this phase)
```

---

## Screenshot Reference

The UI design targets match the screenshots shared at session start:
- `pm.png` / `pm-json.png` — PRD tab with agent badge
- `plan.png` / `plan-json.png` — Plan tab with agent badge  
- `code.png` / `code-json.png` — Code tab with agent badge
- JSON toggle shows raw artifact data in a clean pre/code block
