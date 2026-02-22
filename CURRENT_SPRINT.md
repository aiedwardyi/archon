# Current Sprint — Phase 7D: UI Polish & Quick Wins

## Sprint Goal

Ship the UI polish items that make Archon demo-ready and fix the
remaining version sync issue. All frontend work.

---

## Previous Sprints Complete ✅

### Phase 7C — Stability & State Fixes
- ✅ Pipeline state restores from DB on page refresh
- ✅ Build completion signal uses DB as ground truth
- ✅ Prompt history persisted across iterations (sessionStorage)
- ✅ Logs save by version number — Artifacts logs tab version-correct
- ✅ Polling restarts on nav back to mid-run build
- ✅ Global block prevents concurrent project builds
- ✅ Engineer agent max_tokens raised to 32000

### Phase 7E — Output Quality
- ✅ Design Agent: GPT-4o-mini + DALL-E 3, images served locally via /api/assets/
- ✅ Design Agent skips image gen for dashboards/tools (cost saving)
- ✅ Keyword skip check uses PRD title + overview only (no false positives)
- ✅ JSON repair: backtick hex color strip fix
- ✅ Engineer prompt: 10-shell layout intelligence (dashboard, kanban, chat, e-commerce, etc.)
- ✅ Engineer prompt: DESIGN ASSETS section — engineer must use all injected image URLs
- ✅ Engineer no longer produces landing pages for dashboard/app prompts

---

## Phase 7D Work Items

### 7D.1 — Navbar Real Project Name + Version
**Status:** 🔴 TODO

Replace hardcoded "checkout-service > v14" in top-right navbar with
real current project name and version number from app state.

**Files:** `frontend/components/navbar.tsx`

---

### 7D.2 — Project ID Column on Projects Table
**Status:** 🔴 TODO

Add Project ID column to Projects page table. Currently only visible
on Pipeline page ("Project ID: 8"). Teams need this for communication.

**Files:** `frontend/pages/projects-page.tsx`

---

### 7D.3 — Delete Project + Delete All
**Status:** 🔴 TODO

- Delete individual project with confirmation modal
- Delete all projects with confirmation modal
- Backend DELETE /api/projects/:id already exists

**Files:** `frontend/pages/projects-page.tsx`

---

### 7D.4 — Avatar Dropdown (v0-style)
**Status:** 🔴 TODO

Clickable avatar → dropdown containing:
- Email at top (mock: archon@archon.dev)
- Profile, Settings, Pricing, Documentation, Credits
- Dark/light mode toggle (move from navbar into dropdown)
- Sign Out at bottom

Navbar additions: Upgrade button, Feedback, Refer, Credits count.
Match v0.dev aesthetic — clean, minimal, modern.

**Files:** `frontend/components/navbar.tsx`, new `frontend/components/avatar-dropdown.tsx`

---

### 7D.5 — Versions Page Preview Height
**Status:** 🔴 TODO

Live Preview section in Versions detail panel is too short.
Increase height so the generated app is actually usable/viewable.

**Files:** `frontend/pages/versions-page.tsx`

---

### 7D.6 — Artifacts Version Sync Fix
**Status:** 🔴 TODO

When navigating from Versions page to Artifacts, the Artifacts page
sometimes shows the wrong version.

**Files:** `frontend/components/artifact-viewer.tsx`, `frontend/pages/versions-page.tsx`

---

## Task Order for Worker Chats

1. **Worker 1:** 7D.1 + 7D.2 + 7D.3 (navbar + Projects table — fast wins)
2. **Worker 2:** 7D.4 avatar dropdown (new component, needs care)
3. **Worker 3:** 7D.5 + 7D.6 (preview height + version sync)

---

## Definition of Done

- ⬜ Navbar shows real project name + version
- ⬜ Project ID column visible on Projects table
- ⬜ Delete project works with confirmation
- ⬜ Delete all projects works with confirmation
- ⬜ Avatar dropdown matches v0 aesthetic
- ⬜ Dark mode toggle lives inside avatar dropdown
- ⬜ Upgrade/Feedback/Refer/Credits in navbar
- ⬜ Versions page preview height increased
- ⬜ Artifacts version sync reliable from Versions page nav
- ⬜ All committed on enterprise-ui branch

---

## Files NOT to touch
```
agents/pm_agent.py
agents/planner_agent.py
agents/engineer_agent.py
agents/design_agent.py
backend/models.py
backend/database.py
prompts/engineer.txt
prompts/design_agent.txt
```
