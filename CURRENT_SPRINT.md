# Current Sprint â€” Phase 7D: UI Polish & Quick Wins

## Sprint Goal

Ship the UI polish items that make Archon demo-ready and fix the remaining
version sync issue. No backend changes needed â€” all frontend work.

---

## Previous Sprint Complete âœ…

### Phase 7C â€” Stability & State Fixes

- âœ… Pipeline state restores from DB on page refresh
- âœ… Build completion signal uses DB as ground truth
- âœ… Prompt history persisted across iterations (sessionStorage)
- âœ… Logs save by version number â€” Artifacts logs tab version-correct
- âœ… Polling restarts on nav back to mid-run build
- âœ… Global block prevents concurrent project builds
- âœ… Engineer agent max_tokens raised to 32000

---

## Phase 7D Work Items

### 7D.1 â€” Navbar Real Project Name + Version
**Status:** ðŸ”´ TODO

Replace hardcoded "checkout-service > v14" in top-right navbar with
real current project name and version number from app state.

**Files:** `frontend/components/navbar.tsx`

---

### 7D.2 â€” Project ID Column on Projects Table
**Status:** ðŸ”´ TODO

Add Project ID column to Projects page table. Currently only visible
on Pipeline page ("Project ID: 8"). Teams need this for communication.

**Files:** `frontend/pages/projects-page.tsx`

---

### 7D.3 â€” Delete Project + Delete All
**Status:** ðŸ”´ TODO

- Delete individual project with confirmation modal
- Delete all projects with confirmation modal
- Backend DELETE /api/projects/:id already exists

**Files:** `frontend/pages/projects-page.tsx`, `backend/app.py` (verify)

---

### 7D.4 â€” Avatar Dropdown (v0-style)
**Status:** ðŸ”´ TODO

Clickable avatar â†’ dropdown containing:
- Email at top (mock: archon@archon.dev)
- Profile, Settings, Pricing, Documentation, Credits
- Dark/light mode toggle (move from navbar into dropdown)
- Sign Out at bottom

Navbar additions: Upgrade button, Feedback, Refer, Credits count.
Match v0.dev aesthetic â€” clean, minimal, modern.

**Files:** `frontend/components/navbar.tsx`, new `frontend/components/avatar-dropdown.tsx`

---

### 7D.5 â€” Versions Page Preview Height
**Status:** ðŸ”´ TODO

Live Preview section in Versions detail panel is too short.
Increase height so the generated app is actually usable/viewable.

**Files:** `frontend/pages/versions-page.tsx`

---

### 7D.6 â€” Artifacts Version Sync Fix
**Status:** ðŸ”´ TODO

When navigating from Versions page to Artifacts, the Artifacts page
sometimes shows the wrong version. Need to verify the version param
is correctly passed and the artifact-viewer re-fetches on change.

**Files:** `frontend/components/artifact-viewer.tsx`, `frontend/pages/versions-page.tsx`

---

## Task Order for Worker Chats

1. **Worker 1:** 7D.1 + 7D.2 + 7D.3 (navbar + Projects table â€” fast wins)
2. **Worker 2:** 7D.4 avatar dropdown (new component, needs care)
3. **Worker 3:** 7D.5 + 7D.6 (preview height + version sync)

---

## Definition of Done

- â¬œ Navbar shows real project name + version
- â¬œ Project ID column visible on Projects table
- â¬œ Delete project works with confirmation
- â¬œ Delete all projects works with confirmation
- â¬œ Avatar dropdown matches v0 aesthetic
- â¬œ Dark mode toggle lives inside avatar dropdown
- â¬œ Upgrade/Feedback/Refer/Credits in navbar
- â¬œ Versions page preview height increased
- â¬œ Artifacts version sync reliable from Versions page nav
- â¬œ All committed on enterprise-ui branch

## Phase 7E Progress (Started This Session)

### Design Agent ✅ Built
- `agents/design_agent.py` — calls GPT-4o-mini to plan images, then DALL-E 3
- `prompts/design_agent.txt` — image planning prompt
- Injected into pipeline in `backend/app.py` between Architecture and Build
- Max 6 images per build, character portrait priority rule applied

### Engineer Agent Upgrades ✅
- Streaming enabled in `agents/engineer_agent.py` (required for 32k tokens)
- `prompts/engineer.txt` updated: Unsplash URLs + Google Fonts allowed
- 500-line hard limit fix applied (JSON truncation bug)

### Still TODO for 7E
- ⬜ Add visual guardrails to engineer.txt (ban mascot blobs, enforce product hero)
- ⬜ Test crypto dashboard prompt (500-line fix verification)
- ⬜ Test FF7 prompt (confirm Barret portrait fix)
- ⬜ Consider Design Assets tab in Artifacts page

---

## Files NOT to touch
```
agents/pm_agent.py
agents/planner_agent.py
agents/engineer_agent.py
backend/models.py
backend/database.py
prompts/engineer.txt
```

