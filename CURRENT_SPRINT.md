# Current Sprint — Phase 7A: Iterative Pipeline, Version History & UI Redesign

## Sprint Goal

Two parallel objectives:
1. Transform Archon into a true iterative build tool with full version history
2. Redesign the frontend to match the approved enterprise design target

Together these make Archon production-ready for agency clients.

---

## Target Audience Context

**Primary user:** Digital agency owner or project lead
**Their pain:** Need to build client web apps fast AND show clients every decision
**Archon's answer:** AI builds it + full audit trail + client-presentable history

---

## What Makes This Different

| Feature | Lovable/Bolt | Archon |
|---------|-------------|--------|
| Context continuation | ✅ | ✅ |
| Full chain on every edit | ❌ | ✅ |
| Artifact trail per version | ❌ | ✅ |
| Restore previous version | ✅ | ✅ |
| Restore forward after revert | ❌ | ✅ |
| Client-presentable build history | ❌ | ✅ |

---

## Current State (Phase 6.3 Complete ✅)

- Agent chain badge, JSON toggle, Replay button working
- VS Code-style folder tree in Code explorer
- Sidebar status dots, Clear All Projects
- Flask backend port 5000, Vite frontend port 3000
- enterprise-ui branch created for redesign work
- Approved design target: Lovable mockups (top navbar, agent cards,
  version timeline, artifact tabs)
- Repo clean and committed

---

## How Iteration Works

### Context Continuation
PM agent receives full conversation history on every run:
```
Turn 1: "Build a restaurant booking website"
Turn 2: "Add online payments with Stripe"
Turn 3: "Change the color scheme to match our brand"
```
PM sees all turns → PRD reflects cumulative intent → complete new version built.

### Versioned Storage
Each run is a complete independent snapshot:
```
project/
  v1/  ← "Build a restaurant booking website"
    prd.json, plan.json, code_files/, execution_result.json
  v2/  ← "Add online payments with Stripe"
    prd.json, plan.json, code_files/, execution_result.json
```

### Restore Model
- Clicking past version previews artifacts (read-only)
- Restore sets new HEAD; forward versions preserved
- New prompt from restored version creates new branch

---

## Phase 7A Work Items

### 7A.1 — Backend: Versioned Execution Storage
**Status:** ⬜ TODO
- Add `version`, `prompt_history`, `is_active_head`, `parent_execution_id`
  to executions table
- Migration script for existing DB
- Files: `backend/models.py`, `backend/database.py`

### 7A.2 — Backend: /iterate and /restore Endpoints
**Status:** ⬜ TODO
- `POST /api/projects/:id/iterate` — full pipeline with prompt history
- `POST /api/executions/:id/restore` — set active HEAD
- `GET /api/projects/:id/versions` — version list with metadata
- Files: `backend/app.py`

### 7A.3 — Frontend: Enterprise UI Redesign
**Status:** ⬜ TODO
- Rebuild frontend on enterprise-ui branch to match approved Lovable mockups
- Top navbar (Projects / Pipeline / Versions / Artifacts)
- Breadcrumb showing current project + version
- All pages redesigned: Projects, Pipeline, Versions, Artifacts
- Business-friendly language (not developer jargon)
- Files: full frontend rebuild

### 7A.4 — Frontend: Continuous Chat Panel
**Status:** ⬜ TODO
- Always visible at bottom of Pipeline page
- Shows conversation history
- Submits to /iterate with full prompt_history
- Files: `frontend/components/ChatPanel.tsx` (new)

### 7A.5 — Frontend: Version Timeline Page
**Status:** ⬜ TODO
- Left panel: version list (v1-vN, truncated prompt, timestamp)
- Right panel: version detail (prompt, pipeline result, artifact cards)
- Artifact cards clickable → navigate to Artifacts page
- Files: `frontend/pages/VersionsPage.tsx` (new)

### 7A.6 — Frontend: Version Preview + Restore Flow
**Status:** ⬜ TODO
- Clicking version loads that snapshot read-only
- Restore button sets new HEAD
- Forward-restore supported
- Files: `frontend/pages/VersionsPage.tsx`, `frontend/pages/ArtifactsPage.tsx`

---

## Definition of Done

- ⬜ DB schema: version, prompt_history, is_active_head fields added
- ⬜ /iterate runs full pipeline with context continuation
- ⬜ /restore sets active HEAD; forward versions preserved
- ⬜ /versions returns full version list
- ⬜ Enterprise UI matches approved Lovable mockups
- ⬜ Chat panel submits iterations with full history
- ⬜ Versions page shows timeline + detail panel
- ⬜ Restore flow works including forward-restore
- ⬜ All changes committed on enterprise-ui branch

---

## UI Design Reference
Approved Lovable mockups show:
- Projects: table with status, last run, version count, created date
- Pipeline: agent cards with timing + live output log + chat input
- Versions: left timeline + right detail (prompt, tasks, artifact cards)
- Artifacts: badge bar (pm→planner→engineer, REPLAYABLE, SCHEMA VALIDATED,
  V14) + PRD/Plan/Code/Tasks/Logs tabs

## Files In Scope
```
backend/
  models.py, database.py, app.py

frontend/ (full redesign on enterprise-ui branch)
  pages/
    ProjectsPage.tsx
    PipelinePage.tsx
    VersionsPage.tsx    ← new
    ArtifactsPage.tsx   ← new
  components/
    ChatPanel.tsx       ← new
    ArtifactViewer.tsx
    Navbar.tsx          ← new
```

## Files NOT to touch
```
agents/          (no agent changes this phase)
prompts/         (no prompt changes this phase)
scripts/         (no script changes this phase)
```
