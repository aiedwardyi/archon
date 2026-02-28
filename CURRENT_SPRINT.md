# Current Sprint — Phase 16: UI Parity, Auth & Polish

## Sprint Goal
Unify navigation between Enterprise (frontend-v4) and Studio (frontend) designs, clean up deprecated frontends.

## Port Reference
- **backend**: port 5000 (Flask)
- **frontend-v4**: port 8080 (Enterprise, Vite)
- **frontend**: port 3000 (Studio, Next.js)
- **frontend-consumer2**: port 3002 (Consumer, Vite)

## Working Directory
C:\Users\mredw\Desktop\ai-dev-team\

## Branch
main (enterprise-ui merged and deleted)

---

## Completed This Sprint ✅

### Phase 14 — Iteration Mode Fixes ✅
- Scope enforcement path normalization (`safe_write.py` `_tail_after_code()`)
- Archetype lock conversion phrase detection (prevent false positives like "add a mini game")
- Ancestor chain traversal for failed versions (walk up to 5 hops to find last successful code)
- Design asset reuse on iterations (skip DALL-E regeneration, reuse ancestor's `last_design_assets.json`)
- Asset URL version extraction from `local_path` (correct `/api/assets/{pid}/{version}/` URL)
- Planner iteration file constraints (force `output_files` to `src/index.html` + `src/style.css` only)
- Preview endpoint CSS/JS inlining (inline all `*.css` and `*.js` files from `code/src/`)
- Strengthened `iteration_context` in engineer prompt (5 strict surgical edit rules, placed before main prompt)

### Phase 15 — Consumer Frontend v2 ✅
- Copied and wired Projects/frontend to repo as `frontend-consumer2/` (port 3002)
- Connected to Flask backend via `orchestrator.ts` service layer
- Real iframe preview with desktop/mobile viewport toggle
- **Versions page (THE MOAT)** — timeline + split panel + live preview per version
- Restore version functionality from versions timeline
- File viewer (Code tab) wired to real `/api/projects/:id/versions/:v/files`
- Non-technical wording pass (Brief, Build Plan, What Was Built, Publish)
- Korean/English language toggle with `i18n.ts` translation system (30+ keys)
- CORS allowlist updated for ports 3001 and 3002
- Fixed versions preview URL bug (`version` field vs `version_number`)
- Complete Korean translation coverage for all UI strings

### Phase 15.2 — Consumer Frontend Polish ✅
- Renamed all "ai-dev-team" references to "Archon" across 8 files
- Versions timeline displays newest first (matches API DESC order)
- Versions right panel iframe glow effect (indigo shadow + hover)
- Hide restore button on current/latest version (`maxVersion` guard)
- Version card glow/contrast polish (darker bg, indigo ring, gradient overlay)
- Logo split corrected: "Arch" + "on" (violet accent on "on")
- Korean translations wired to Sidebar (9 strings via `t()`)
- Korean translations wired to Logs tab (`runtimeLogs`, `simulateFault`)

### Phase 15.3 — Consumer UX Bug Fixes (🔧 Partially Complete)
- Reset `localPrd`/`localPlan`/`localTasks`/`previewVersion` on `projectId` change (stale data across project switches)
- Removed `opacity-0`/`opacity-100` transition on workspace div (iframe invisible after build completes)
- Progress bar restored to smooth sessionStorage animation (survives navigate-away during builds — still resets on some rapid navigation edge cases, revisit later)
- Expanded `getTechColor` to match 7 keyword categories (frontend/backend/database/state/ml/hosting/styling)
- Tech map rendering handles no-colon entries (natural-language PRD format)
- Engineer prompt: added MOCK DATA REQUIREMENT block (no more empty-state generated apps)
- Failed projects no longer show progress bar overlay ✅
- Code tab now shows real generated files (fixed wrong API key `data.files` → `data.tree`) ✅
- ❌ Preview iframe sometimes reverts to "Live Preview Will Appear Here" after build completes — revisit

### Phase 15.1 — Repo Cleanup ✅
- Removed `apps/offline-vite-react` (unused old frontend)
- Added `node_modules/`, `dist/`, `.venv/`, `.claude/` to `.gitignore`
- Merged `enterprise-ui` branch into `main`
- Deleted `enterprise-ui` local branch

### Previously Completed ✅
- Phase 13.1 — Chat message persistence (DB-backed)
- Phase 13.2 — User model + owner_id foundation
- Phase 10.4 — App type lock (archetype guardrail)
- Phase 10.1-10.2 — Watson STT/TTS integration
- Phase 8.1 — One-click publish
- Phase 8.UI.1-2 — Artifact card linking + account modals

---

### Phase 15.4 — Enterprise UI (frontend-v4) ✅
- Copied Enterprise design (archon-v4) to `frontend-v4/`
- Vite + React + TypeScript + Tailwind + shadcn/ui running on port 8080
- 4-theme system foundation (Enterprise Light/Dark, Studio Light/Dark)
- Korean/English language toggle with localStorage persistence
- Projects page connected to real Flask API with 3s polling
- Fixed N+1 query — added `version_count` to `Project.to_dict()` in `models.py`
- VersionsView: real versions list + real iframe preview per version
- ArtifactsView: real Brief (PRD), Plan, Code, Tasks, Logs
- Navbar: real project name + version in breadcrumb
- Favicon: lightning bolt SVG + "Archon - Enterprise Build" title

### Phase 15.5 — Enterprise UI Polish (✅ Complete)
- ✅ Checkbox UX fix, Stats bar, Activity feed, Avg build time wired
- ✅ Publish and Download buttons wired to real endpoints
- ✅ Pipeline tab — full chat UI, /chat + /iterate endpoints, chat history, live output log
- ✅ Zap icon branding, i18n keys, New Project modal, "What Was Built" summary
- ✅ images_generated + files_generated counts from backend
- ✅ ArtifactsView Code tab — fixed height, independent scroll
- ✅ WelcomeBanner — live backend health check (green/red dot)
- ✅ Artifact cards navigate to Artifacts tab with sub-tab pre-selection
- ✅ Code tab scrollbars fixed, "Running" → "Building" rename
- ✅ Pipeline header status badges (colored pills)
- ✅ Agent pipeline status persists after reload from DB
- ✅ Search filter, red dot pulse, scroll-to-top, no auto-scroll on load
- ✅ Pipeline state resets on project switch (no bleed)
- ✅ Chat messages persist via sessionStorage keyed by project ID
- ✅ JSON repair bug fixed — _repair_json strips fences, fixes bare backslashes
- ✅ Delete modal — type "DELETE" to confirm + shutil.rmtree disk cleanup
- ✅ Build Details card — tokens_used, estimated_cost, duration, model wired from DB

---

### Phase 15.6 — Frontend Cleanup & Tab Sync (✅ Complete Feb 2026)
- ✅ Wire Studio button in frontend-v4 navbar
- ✅ Enterprise/Studio switcher in frontend/ navbar
- ✅ Tab sync via URL query params
- ✅ Removed deprecated frontend-consumer/ folder
- ✅ Studio Tasks tab wired with real plan data
- ✅ Delete modal requires DELETE (uppercase) to match Enterprise

---

## Current Sprint — Phase 16: UI Parity, Auth & Polish

### Sprint Goal
Fix critical bugs, achieve Studio/Enterprise feature parity, add auth.

## Completed This Sprint ✅

### Phase 16.2 — Branding (✅ Complete)
- ✅ Tab title: "Archon - Studio Build" (frontend/)
- ✅ Tab title: "Archon - Consumer Build" (frontend-consumer2/)
- ✅ Hexagon logo in frontend-v4 navbar
- ✅ Hexagon logo in frontend-consumer2 sidebar
- ✅ Hexagon SVG favicon in frontend-v4 and frontend-consumer2

### Phase 16.4 — Watson STT/TTS for Enterprise (✅ Complete)
- ✅ Mic button (STT) in Enterprise pipeline chat input
- ✅ Speaker button (TTS) on Archon reply bubbles
- ✅ Fixed WATSON_TTS_API_KEY / WATSON_STT_API_KEY env var mismatch
- ✅ Fixed load_dotenv to always resolve backend/.env path

## Remaining This Sprint 🔴

### Phase 16.1 — Bug Fixes
- 🔴 Studio + Enterprise chat persistence after Flask restart
- 🔴 Live output logs lost after restart
- 🔴 Build Details tokens/cost showing —

### Phase 16.3 — Studio Feature Parity
- 🔴 Korean/English toggle in Studio navbar
- 🔴 Build Details card in Studio Pipeline page
- 🔴 Stats bar on Studio Projects page
- 🔴 Recent Activity feed on Studio Projects page

### Phase 16.5 — Authentication
- 🔴 Sign up / Login pages
- 🔴 JWT + protected routes
