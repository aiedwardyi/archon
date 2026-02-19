# Current Sprint — Phase 7B: Live Preview

## Sprint Goal

Wire a real running iframe into the Pipeline page so non-technical users
can SEE the application that was built — not just read code or log entries.
This is the feature that makes Archon's output tangible to agency clients.

---

## Previous Sprint Complete ✅

### Phase 7A — Iterative Pipeline & Version History (Complete)

**What was built:**
- Full iterative pipeline: every prompt runs PM → Planner → Engineer and
  creates a new versioned execution stored in the database
- Prompt history continuation: PM agent receives all previous turns on every run
- /iterate endpoint: accepts prompt + prompt_history, runs full pipeline
- /restore endpoint: sets is_active_head flag for version restore
- /versions endpoint: returns full version timeline per project
- Enterprise UI rebuilt on enterprise-ui branch (10 screens, light + dark)
- Continuous chat panel: conversation history + iterative input at bottom
- Version timeline: left panel timeline + right detail panel
- sessionStorage caching: instant nav-back for project name, agent card state,
  and real logs (keyed by execution ID)
- Real log persistence: logs saved when run completes, restored on return —
  no more fake reconstructed summaries
- Agent card state restored instantly from cache — no flash/settle on nav back

**Definition of Done — Phase 7A:**
- ✅ DB schema updated with version, prompt_history, is_active_head
- ✅ /iterate endpoint runs full pipeline with context continuation
- ✅ /restore endpoint sets active HEAD correctly
- ✅ /versions endpoint returns full version list
- ✅ Enterprise UI rebuilt on enterprise-ui branch
- ✅ Chat panel renders history and submits new prompts
- ✅ Versions page shows timeline + detail + restore
- ✅ Dark mode toggle working across all pages
- ✅ Real log persistence via sessionStorage
- ✅ Instant nav-back (no settling/flash on return to pipeline page)
- ✅ All changes committed on enterprise-ui branch

**Known remaining items (carried to Phase 7B):**
- ArtifactViewer Code tab uses mock file tree data (real wiring deferred)
- Live preview iframe: main focus of Phase 7B

---

## Phase 7B Work Items

### 7B.1 — Engineer Agent: Self-Contained Output
**Status:** ⬜ TODO

**What:**
- Update engineer system prompt to produce a single self-contained HTML file
  when building simple apps (landing pages, forms, calculators, etc.)
- Self-contained = inline CSS + inline JS, no external dependencies
- This makes preview trivial: one file → one iframe src

**Files:**
- `prompts/engineer.txt`
- `agents/engineer_agent.py` (if prompt changes need code support)

---

### 7B.2 — Backend: Preview File Serving
**Status:** ⬜ TODO

**What:**
- Add `GET /api/preview/<project_id>/<version>` route
- Serves the self-contained HTML output from the engineer's output directory
- Falls back to a placeholder if no previewable file exists

**Files:**
- `backend/app.py`

---

### 7B.3 — Frontend: iframe Preview Panel
**Status:** ⬜ TODO

**What:**
- Add Preview tab to PipelineRun page (after the log panel)
- Desktop/mobile viewport toggle (already designed in Lovable mockups)
- iframe src points to `/api/preview/<project_id>/<version>`
- Placeholder state when no preview available yet

**Files:**
- `frontend/src/pages/PipelineRun.tsx`
- Possibly a new `PreviewPanel.tsx` component

---

### 7B.4 — History Integration
**Status:** ⬜ TODO

**What:**
- Versions page: clicking a past version loads that version's preview
- Preview iframe updates when version is selected
- "Restore to this version" still works alongside preview

**Files:**
- `frontend/src/pages/VersionsPage.tsx`

---

### 7B.5 — ArtifactViewer Code Tab: Real File Tree
**Status:** ⬜ TODO

**What:**
- Replace mock file tree data in ArtifactViewer Code tab with real
  files from the execution_result artifact
- Wire to /api/code endpoint or execution-specific artifact path

**Files:**
- `frontend/src/components/ArtifactViewer.tsx`

---

## Definition of Done (Phase 7B Sprint)

- ⬜ Engineer agent produces self-contained HTML for simple apps
- ⬜ /api/preview route serves engineer output files
- ⬜ Preview iframe renders in Pipeline page (desktop + mobile toggle)
- ⬜ Placeholder shown when no preview available
- ⬜ Version history: clicking past version updates preview
- ⬜ ArtifactViewer Code tab wired to real file data
- ⬜ All changes committed on enterprise-ui branch

---

## Files In Scope
```
prompts/
  engineer.txt              ← self-contained output prompt update

backend/
  app.py                    ← /api/preview route

frontend/
  pages/
    PipelineRun.tsx         ← Preview tab + iframe panel
    VersionsPage.tsx        ← version-click updates preview
  components/
    ArtifactViewer.tsx      ← Code tab real file tree
    PreviewPanel.tsx        ← new: iframe + viewport toggle
```

## Files NOT to touch
```
agents/pm_agent.py          (no changes this phase)
agents/planner_agent.py     (no changes this phase)
frontend/services/orchestrator.ts  (working, don't break)
backend/models.py           (schema complete from 7A)
```
