# Current Sprint — Phase 7C: Stability & Polish

## Sprint Goal

Fix critical state bugs that break core UX, then polish the UI to
demo-ready quality. Platform is functionally complete — this sprint
makes it reliable and presentable.

---

## Previous Sprint Complete ✅

### Phase 7B — Live Preview (Complete)

**What was built:**
- Build Agent switched from Gemini → Claude Sonnet 4.5 (primary)
- Gemini fallback if ANTHROPIC_API_KEY not set
- Engineer prompt updated: self-contained HTML, 600-line limit
- /api/preview/<project_id>/<version> backend route serving index.html
- Live preview iframe wired in Versions page + Artifacts page
- Desktop/mobile viewport toggle working
- Agent card flash bug fixed (was showing both cards Done on 2nd+ prompt)
- max_tokens bumped to 32000 to prevent Claude truncation

**Known issues carried to 7C:**
- Pipeline state lost on page refresh (sessionStorage only, no DB fallback)
- Silent build complete (Build Agent stays "Building..." after done)
- Artifacts page shows wrong version until manual nav
- 3rd+ prompt erases previous site (prompt history not reaching Build Agent)

---

## Phase 7C Work Items

### 7C.1 — Pipeline State Persistence on Refresh
**Status:** 🔴 TODO (Critical)

**Problem:**
Refreshing the pipeline page or clicking a completed project from Projects
shows empty agent cards + 0 log entries. State only lives in sessionStorage.
No fallback to DB.

**What to fix:**
- On pipeline page mount, if sessionStorage is empty, fetch last execution
  from /api/projects/:id and restore agent card state + logs from DB
- Backend should return logs with the execution record

**Files:**
- `frontend/components/pipeline-run.tsx`
- `backend/app.py` (check if /api/projects/:id returns logs)

---

### 7C.2 — Silent Build Complete + Stale Artifact View
**Status:** 🔴 TODO (Critical)

**Problem:**
After 3rd prompt: Flask terminal shows build complete, but:
- Build Agent card stays "Building..." indefinitely
- Artifacts page shows v2 instead of v3
- User must manually navigate away and back to see correct state

**Root cause suspects:**
- Polling stops or misses the completion signal
- Artifact viewer not re-fetching on version change
- sessionStorage serving stale version number

**Files:**
- `frontend/components/pipeline-run.tsx` (polling logic)
- `frontend/components/artifact-viewer.tsx` (version fetch)
- `backend/app.py` (execution_status endpoint)

---

### 7C.3 — 3rd Prompt Context Loss
**Status:** 🔴 TODO (Critical)

**Problem:**
On 3rd iteration, Build Agent erases the entire previous site and replaces
it. Works correctly on 2nd prompt. Prompt history is not feeding into the
Build Agent correctly on 3rd+ runs.

**Root cause suspects:**
- prompt_history array not being passed to engineer_agent.py
- Engineer agent ignores history and regenerates from scratch
- Context window limit causing history truncation

**Files:**
- `agents/engineer_agent.py`
- `backend/app.py` (/iterate endpoint — how prompt_history is passed)
- `prompts/engineer.txt` (check if iteration instructions are present)

---

### 7C.4 — Navbar Real Project Name + Version
**Status:** ⬜ TODO (Quick win)

**Problem:**
Top-right navbar shows hardcoded "checkout-service > v14" mock data.
Should show real current project name + current version number.

**Files:**
- `frontend/components/navbar.tsx` (or wherever the top-right context is rendered)

---

### 7C.5 — Project ID Column on Projects Table
**Status:** ⬜ TODO (Quick win)

**What:**
Add Project ID column to Projects page table. Currently visible only on
Pipeline page. Useful for team communication ("check project 8").

**Files:**
- `frontend/pages/projects-page.tsx`

---

### 7C.6 — Delete Project + Delete All
**Status:** ⬜ TODO (Quick win)

**What:**
- Delete individual project (with confirmation modal)
- Delete all projects (with confirmation modal)
- Backend DELETE /api/projects/:id already exists per README

**Files:**
- `frontend/pages/projects-page.tsx`
- `backend/app.py` (verify DELETE endpoint exists)

---

### 7C.7 — Avatar Dropdown Menu (v0-style)
**Status:** ⬜ TODO (UI feature)

**What:**
- Clickable avatar in top-right opens dropdown
- Dropdown contains: email (mock: archon@archon.dev), Profile, Settings,
  Pricing, Documentation, Credits count, divider, Sign Out
- Dark/light mode toggle moves INTO dropdown (remove from navbar)
- Navbar gets: Upgrade button, Feedback button, Refer button, Credits count
- Match v0.dev aesthetic — clean, modern, minimal

**Files:**
- `frontend/components/navbar.tsx`
- New: `frontend/components/avatar-dropdown.tsx`

---

### 7C.8 — Versions Page Preview Height
**Status:** ⬜ TODO (UI polish)

**Problem:**
Live Preview section in Versions page detail panel is too short to
contextually view the generated app. Needs more height.

**Files:**
- `frontend/pages/versions-page.tsx`

---

## Definition of Done (Phase 7C)

- ⬜ Pipeline page restores state from DB on refresh
- ⬜ Build Agent card shows Done when build completes (no manual nav needed)
- ⬜ Artifacts page updates to latest version automatically
- ⬜ 3rd+ prompt preserves previous site context
- ⬜ Navbar shows real project name + version
- ⬜ Project ID column on Projects table
- ⬜ Delete project + delete all working
- ⬜ Avatar dropdown with v0-style menu
- ⬜ Versions page preview height increased
- ⬜ All changes committed on enterprise-ui branch

---

## Task Order for Worker Chats

1. **Worker 1:** Fix 7C.1 + 7C.2 + 7C.3 (all state/polling bugs — same files)
2. **Worker 2:** Fix 7C.4 + 7C.5 + 7C.6 (quick wins — UI only)
3. **Worker 3:** 7C.7 avatar dropdown (UI feature, new component)
4. **Worker 4:** 7C.8 preview height (one CSS change)

---

## Files In Scope
```
backend/
  app.py                        ← execution_status, /iterate, DELETE endpoints

agents/
  engineer_agent.py             ← prompt history handling

frontend/
  components/
    pipeline-run.tsx            ← polling, agent card state, DB fallback
    artifact-viewer.tsx         ← version fetch on change
    navbar.tsx                  ← real project name, avatar dropdown
    avatar-dropdown.tsx         ← NEW: v0-style dropdown
  pages/
    projects-page.tsx           ← Project ID column, delete actions
    versions-page.tsx           ← preview height

prompts/
  engineer.txt                  ← iteration context instructions
```

## Files NOT to touch
```
agents/pm_agent.py
agents/planner_agent.py
backend/models.py
backend/database.py
```
