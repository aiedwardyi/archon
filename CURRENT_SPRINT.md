# Current Sprint — Phase 7A: Iterative Pipeline & Version History

## Sprint Goal

Transform Archon from a single-shot generator into a true iterative build tool.
Every prompt submission runs the full PM → Planner → Engineer pipeline and
creates a complete versioned snapshot — leaving a full audit trail across the
entire build history.

This is Archon's core differentiator: not just "generate once" but
**full artifact trail across every iteration**, with context continuation
and version restore.

---

## Previous Sprint Complete ✅

### Phase 6.4 — Enterprise UI Design (Complete)
- Full enterprise UI designed in Lovable (10 screens)
- Business-friendly language across all screens
- Enterprise dark mode (Linear/GitHub aesthetic)
- Dark mode toggle in navbar
- Preview tab with desktop/mobile viewport toggle
- Download Report on Versions page + Projects table
- enterprise-ui branch: ready for frontend rebuild

---

## Context: What Makes This Different

| Feature | Lovable/Bolt | Archon |
|---------|-------------|--------|
| Context continuation | ✅ | ✅ |
| Full chain on every edit | ❌ | ✅ |
| Artifact trail per version | ❌ | ✅ |
| Restore previous version | ✅ | ✅ |
| Restore forward after revert | ❌ | ✅ |
| Auditable Brief per iteration | ❌ | ✅ |

---

## Current State (Phase 6.3 + 6.4 Complete ✅)

- Agent chain badge, JSON→Raw Data toggle, Replay button working
- VS Code-style folder tree in Code explorer
- Sidebar status dots, Clear All Projects
- Engineer prompt capped (1 README, 6 files max)
- Enterprise UI design approved (Lovable, 10 screens)
- Flask backend on port 5000, Vite frontend on port 3000
- Repo clean and committed
- enterprise-ui branch created and pushed

---

## How Iteration Works

### Context Continuation
The PM agent receives the full conversation history on every run:
```
Turn 1: "Build a surfboard landing page"
Turn 2: "Change colors to ocean blues and sunset oranges"
Turn 3: "Add a login page with email/password"
```

PM agent sees all 3 turns → writes a Brief reflecting cumulative intent.
Planner and Engineer build from that complete Brief.

### Versioned Storage
Each execution is a complete snapshot — nothing is overwritten:
```
project/
  v1/  ← "Build a surfboard landing page"
    brief.json, plan.json, code_files/, execution_result.json
  v2/  ← "Change colors to ocean blues..."
    brief.json, plan.json, code_files/, execution_result.json
  v3/  ← "Add login page with email/password"
    ...
```

### Restore Model
- Clicking a past version previews its artifacts (read-only)
- "Restore to this version" sets that version as the active HEAD
- Past versions after a branch point remain accessible (forward-restore)
- New prompt from a restored version creates a new branch (v4+)

---

## Phase 7A Work Items

### 7A.1 — Backend: Versioned Execution Storage
**Status:** ⬜ TODO

**What:**
- Add `version` (int), `prompt_history` (JSON array), `is_active_head` (bool),
  `parent_execution_id` (nullable FK) to executions table
- Migration script for existing DB
- Each new execution auto-increments version per project

**Files:**
- `backend/models.py`
- `backend/database.py` (migration)

---

### 7A.2 — Backend: /iterate and /restore Endpoints
**Status:** ⬜ TODO

**What:**
- `POST /api/projects/:id/iterate` — accepts `{ prompt, prompt_history }`,
  runs full pipeline, stores as new version
- `POST /api/executions/:id/restore` — sets `is_active_head=true` for this
  execution, false for all others in the project
- `GET /api/projects/:id/versions` — returns all versions with metadata

**Files:**
- `backend/app.py`

---

### 7A.3 — Frontend: Enterprise UI Rebuild
**Status:** ⬜ TODO

**What:**
- Rebuild frontend on enterprise-ui branch matching approved Lovable designs
- Light mode default, dark mode toggle in navbar
- Top navbar: Projects | Pipeline | Versions | Artifacts
- All business language (Brief, Build Plan, Build Tasks, etc.)
- Responsive preview toggle (desktop/mobile) in Preview tab

**Reference:** Approved Lovable screenshots (10 screens)

**Files:**
- `frontend/` — full rebuild on enterprise-ui branch

---

### 7A.4 — Frontend: Continuous Chat Panel
**Status:** ⬜ TODO

**What:**
- Replace current single input box with continuous chat panel
- Always visible at bottom of main panel
- Shows conversation history (user prompts + agent status)
- Submitting calls /iterate with full prompt_history
- Input placeholder: "What would you like to change?"

**Files:**
- `frontend/components/ChatPanel.tsx` (new)
- `frontend/pages/ProjectDetailPage.tsx` (integrate)

---

### 7A.5 — Frontend: Version Timeline + Restore Flow
**Status:** ⬜ TODO

**What:**
- Versions page: left timeline + right detail panel
- Each version shows: prompt, What Was Built, Build Artifacts cards
- "Restore to this version" button on past versions
- "Download Report" button (outline style, top right)
- Forward-restore: v2/v3 remain accessible after restoring v1

**Files:**
- `frontend/pages/VersionsPage.tsx` (new or rebuild)
- `frontend/components/ArtifactViewer.tsx` (read-only mode)

---

## Definition of Done (Sprint)

- ⬜ DB schema updated with version, prompt_history, is_active_head
- ⬜ /iterate endpoint runs full pipeline with context continuation
- ⬜ /restore endpoint sets active HEAD correctly
- ⬜ /versions endpoint returns full version list
- ⬜ Enterprise UI rebuilt on enterprise-ui branch
- ⬜ Chat panel renders history and submits new prompts
- ⬜ Versions page shows timeline + detail + restore
- ⬜ Download Report button present on Versions page
- ⬜ Dark mode toggle working across all pages
- ⬜ All changes committed on enterprise-ui branch

---

## Files In Scope
```
backend/
  models.py              ← DB schema changes
  database.py            ← migration
  app.py                 ← new endpoints

frontend/                ← full rebuild on enterprise-ui branch
  components/
    ChatPanel.tsx         ← new: continuous chat input
    ArtifactViewer.tsx    ← read-only mode + Preview tab
  pages/
    ProjectsPage.tsx      ← enterprise design
    ProjectDetailPage.tsx ← chat panel + pipeline view
    VersionsPage.tsx      ← timeline + restore flow
```

## Files NOT to touch
```
agents/                         (no agent changes this phase)
frontend/services/orchestrator.ts  (working, don't break)
prompts/                        (no prompt changes this phase)
```
