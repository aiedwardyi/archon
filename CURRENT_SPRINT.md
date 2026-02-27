# Current Sprint — Phase 15.4-15.5: Enterprise UI (frontend-v4)

## Sprint Goal
Ship enterprise frontend-v4 with real API wiring, Pipeline tab chat UI, and full project management features.

## Working Directory
C:\Users\mredw\OneDrive\Desktop\ai-dev-team\

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
- Copied Lovable-generated Enterprise design (archon-v4) to `frontend-v4/`
- Vite + React + TypeScript + Tailwind + shadcn/ui running on port 8080
- 4-theme system foundation (Enterprise Light/Dark, Studio Light/Dark)
- Korean/English language toggle with localStorage persistence
- Projects page connected to real Flask API with 3s polling
- Fixed N+1 query — added `version_count` to `Project.to_dict()` in `models.py`
- VersionsView: real versions list + real iframe preview per version
- ArtifactsView: real Brief (PRD), Plan, Code, Tasks, Logs
- Navbar: real project name + version in breadcrumb
- Favicon: lightning bolt SVG + "Archon - Enterprise Build" title

### Phase 15.5 — Enterprise UI Polish (🔧 In Progress)
- ✅ Checkbox UX fix — no longer triggers row navigation
- ✅ Stats bar wired to real project counts (total/running/completed/failed)
- ✅ Activity feed wired to real recent executions with collapse/expand
- ✅ Avg build time stat with fallback for missing data
- ✅ Publish and Download buttons wired to real endpoints
- ✅ Pipeline tab — full chat UI with conversation panel, input bar, agent status cards
- ✅ Pipeline tab — `/chat` and `/iterate` endpoints wired
- ✅ Pipeline tab — chat history loaded from DB on project switch
- ✅ Pipeline tab — live output log panel with auto-scroll
- ✅ Replaced Sparkles icon with Zap (lightning bolt) for Archon branding
- ✅ Added missing i18n keys for pipeline UI
- ✅ New Project modal (Name + Description → POST /api/projects, auto-selects project and opens Pipeline tab)
- ✅ "What Was Built" summary — real file + image counts from backend (e.g. "2 code files · 3 images generated")
- ✅ Backend returns `images_generated` count from `last_design_assets.json` per version
- ✅ VersionsView files changed count uses real `files_generated` from API
- ✅ ArtifactsView Code tab — fixed height with independent scroll for file tree and code viewer
- ✅ WelcomeBanner — live backend health check (green/red dot with 10s polling)
- ✅ i18n keys added: backendOffline, projectName, projectDescription, creating, create, cancel
- ✅ Artifact cards (Brief/Plan/Code) in VersionsView navigate to Artifacts tab with correct sub-tab pre-selected
- ✅ Code tab scrollbars fixed — outer grid overflow:hidden with calc height, `<pre>` overflow:auto, minWidth:0 on right panel
- ✅ Renamed "Running" → "Building" (EN) / "빌딩 중" (KO) across i18n and ProjectTable
- ✅ Pipeline header status badge — colored rounded-full pills (blue/building, emerald/completed, red/failed, gray/idle)
- ✅ Agent pipeline status persists after reload — reads DB status (success/failed/running)
- ✅ Logs saved for successful builds (backend app.py)
- ✅ "What Was Built" summary — shows "2 code files · 2 images generated"
- ✅ Backend health indicator — red dot + "Backend offline" when Flask unreachable
- ✅ Status badge colors — green/red/blue pills in Pipeline header and Projects table
- ✅ Search filter on Projects page — client-side case-insensitive name filtering
- ✅ Red dot pulse animation on "Backend offline" indicator (WelcomeBanner)
- ✅ Removed Description field from New Project modal (name only, sends empty string)
- ✅ Pipeline tab no longer auto-scrolls to bottom on initial load (guarded by ref + timer)
- ✅ Pipeline tab scrolls to top on load — `window.scrollTo(0, 0)` when activeTab === "pipeline"

---

## What's Next

### Phase 15.5 — Remaining
- ✅ Live output + agent pipeline no longer bleeds across projects (pipeline state resets on project switch)
- ✅ Chat messages persist via sessionStorage keyed by project ID (survives tab/project switching)
- ✅ Pipeline tab scroll-to-top fixed (container ref + triple scroll target)
- ✅ JSON repair bug — _repair_json strips fences, fixes bare backslashes, logs on failure
- ✅ Delete modal — type "DELETE" to confirm + shutil.rmtree disk cleanup
- ✅ Build Details card — tokens_used, estimated_cost, duration, model wired from DB
- 🔴 Studio theme CSS variables in frontend-v4

### Phase 15.6 — Frontend Cleanup
- Retire `frontend/` and `frontend-consumer2/` once frontend-v4 is feature-complete
- Studio button in avatar dropdown → switch to `frontend/` (Next.js, port 3000) design
- Enterprise button → frontend-v4

### Phase 8.3 — Client Share Link
- Read-only shareable URL for client deliverables
- No login required
- Shows all versions, artifacts, and previews

### Watson STT/TTS in Consumer Frontend
- Wire mic button + speaker button into `frontend-consumer2`
- Same Watson endpoints already working in enterprise frontend

### Image Generation Fix
- Character portrait blending in hero section
- DALL-E content filter edge cases

### Korean Translation — Remaining
- Delete confirmation modal strings
- Error messages and edge case strings
- Dynamic project names (leave untranslated)
