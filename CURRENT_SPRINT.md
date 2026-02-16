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

## Context: What Makes This Different

| Feature | Lovable/Bolt | Archon |
|---------|-------------|--------|
| Context continuation | ✅ | ✅ |
| Full chain on every edit | ❌ | ✅ |
| Artifact trail per version | ❌ | ✅ |
| Restore previous version | ✅ | ✅ |
| Restore forward after revert | ❌ | ✅ |
| Auditable PRD per iteration | ❌ | ✅ |

---

## Current State (Phase 6.3 Complete ✅)

- Agent chain badge, JSON toggle, Replay button all working
- VS Code-style folder tree in Code explorer
- Sidebar status dots, Clear All Projects
- Engineer prompt capped (1 README, 6 files max)
- safe_write.py allowlist expanded
- Duplicate file dedup working
- Flask backend on port 5000, Vite frontend on port 3000
- Repo clean and committed

---

## How Iteration Works

### Context Continuation
The PM agent receives the full conversation history on every run:
```
Turn 1: "Build a surfboard landing page"
Turn 2: "Change colors to ocean blues and sunset oranges"
Turn 3: "Add a login page with email/password"
```

PM agent sees all 3 turns → writes a PRD reflecting cumulative intent.
Planner and Engineer build from that complete PRD.

### Versioned Storage
Each execution is a complete snapshot — nothing is overwritten:
```
project/
  v1/  ← "Build a surfboard landing page"
    prd.json, plan.json, code_files/, execution_result.json
  v2/  ← "Change colors to ocean blues..."
    prd.json, plan.json, code_files/, execution_result.json
  v3/  ← "Add login page with email/password"
    ...
```

### Restore Model
- Clicking a past version previews its artifacts (read-only, nothing changes)
- "Restore" sets that version as the active HEAD
- Past versions after a branch point remain accessible (forward-restore supported)
- New prompt from a restored version creates a new branch (v4+)
- This is more powerful than Lovable — forward versions are never deleted

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
  (version number, truncated prompt, timestamp, is_active_head)

**Files:**
- `backend/app.py`

---

### 7A.3 — Frontend: Continuous Chat Panel
**Status:** ⬜ TODO

**What:**
- Replace current single input box with a continuous chat panel
- Always visible at the bottom of the main panel
- Shows conversation history (user prompts + agent responses/status)
- Submitting a new message calls /iterate with full prompt_history
- Like this Claude chat, Lovable, Gemini Build — natural continuous flow

**Files:**
- `frontend/components/ChatPanel.tsx` (new)
- `frontend/pages/ProjectDetailPage.tsx` (integrate ChatPanel)

---

### 7A.4 — Frontend: Clock Icon + History Drawer
**Status:** ⬜ TODO

**What:**
- Clock icon button in the chat panel header (top right)
- Hover tooltip: "View history"
- On click: slides open a history drawer
- History drawer shows version timeline:
```
  v1  "Build a surfboard landing page"        2h ago
  v2  "Change colors to ocean blues..."       1h ago
  v3  "Add login page with email/passw..."    30m ago
```
- Prompt labels truncated at ~35 chars with ellipsis
- Active HEAD version highlighted
- Versions after a branch point shown dimmed but clickable

**Files:**
- `frontend/components/HistoryDrawer.tsx` (new)
- `frontend/pages/ProjectDetailPage.tsx` (integrate)

---

### 7A.5 — Frontend: Version Preview + Restore Flow
**Status:** ⬜ TODO

**What:**
- Clicking a version in history drawer loads that snapshot's artifacts
  in the main artifact panel (read-only, labelled "Viewing v2")
- "Restore to this version" button appears when viewing a past version
- Restore calls /restore endpoint, sets new HEAD, updates UI
- Forward-restore: if user restores v1 from v3, v2 and v3 remain in
  history and can be restored forward again
- New prompt from restored version creates v4 (new branch)

**Files:**
- `frontend/pages/ProjectDetailPage.tsx`
- `frontend/components/ArtifactViewer.tsx` (read-only mode indicator)

---

## Definition of Done (Sprint)

- ⬜ DB schema updated with version, prompt_history, is_active_head
- ⬜ /iterate endpoint runs full pipeline with context continuation
- ⬜ /restore endpoint sets active HEAD correctly
- ⬜ /versions endpoint returns full version list
- ⬜ Chat panel renders conversation history and submits new prompts
- ⬜ Clock icon opens history drawer with version timeline
- ⬜ Clicking version loads that snapshot's artifacts
- ⬜ Restore sets new HEAD; forward-restore works
- ⬜ New prompt from restored version creates new branch
- ⬜ All changes committed

---

## Files In Scope
```
backend/
  models.py              ← DB schema changes
  database.py            ← migration
  app.py                 ← new endpoints

frontend/
  components/
    ChatPanel.tsx         ← new: continuous chat input
    HistoryDrawer.tsx     ← new: version timeline
    ArtifactViewer.tsx    ← read-only mode indicator
  pages/
    ProjectDetailPage.tsx ← integrate ChatPanel + HistoryDrawer
```

## Files NOT to touch
```
frontend/services/orchestrator.ts   (working, don't break)
frontend/types.ts                   (schema changes in separate PR if needed)
prompts/                            (no prompt changes this phase)
```
