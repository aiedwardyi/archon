# Current Sprint — Phase 15.4-15.5: Enterprise UI (frontend)

## Sprint Goal
Ship enterprise frontend with real API wiring, Pipeline tab chat UI, and full project management features.

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
- Copied and wired Projects/frontend to repo as `frontend-consumer/` (port 3002)
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

### Phase 15.4 — Enterprise UI (frontend) ✅
- Copied Lovable-generated Enterprise design (archon-v4) to `frontend/`
- Vite + React + TypeScript + Tailwind + shadcn/ui running on port 8080
- 4-theme system foundation (Enterprise Light/Dark, Studio Light/Dark)
- Korean/English language toggle with localStorage persistence
- Projects page connected to real Flask API with 3s polling
- Fixed N+1 query — added `version_count` to `Project.to_dict()` in `models.py`
- VersionsView: real versions list + real iframe preview per version
- ArtifactsView: real Brief (PRD), Plan, Code, Tasks, Logs
- Navbar: real project name + version in breadcrumb
- Favicon: lightning bolt SVG + "Archon - Enterprise Build" title

### Phase 15.5.S — Studio Dashboard Review (✅ Completed Feb 28)
- Stats bar and Recent Activity feed were added then reverted — not shipping
- Studio Projects page intentionally kept minimal: project count cards (Total/Running/Completed/Failed) + search + table only

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

## Current Sprint — Phase 16: UI Parity, Auth & Polish (🔧 In Progress Feb 2026)

### Phase 16.2 — Branding & Tab Titles (✅ Complete Feb 28, 2026)
- ✅ Chrome tab title: "Archon - Studio Build" (frontend-studio/)
- ✅ Chrome tab title: "Archon - Consumer Build" (frontend-consumer/)
- ✅ Hexagon logo in frontend navbar (replaced lightning bolt)
- ✅ Hexagon logo in frontend-consumer sidebar (replaced Zap icon)
- ✅ Inline SVG hexagon favicon in frontend
- ✅ Inline SVG hexagon favicon in frontend-consumer
- ✅ Fixed load_dotenv to resolve backend/.env path correctly

### Phase 16.4 — Watson STT/TTS for Enterprise (✅ Complete Feb 28, 2026)
- ✅ Mic button (STT) in frontend pipeline chat input
- ✅ Speaker button (TTS) on Archon reply bubbles in frontend
- ✅ Fixed WATSON_TTS_API_KEY / WATSON_STT_API_KEY env var mismatch in backend/app.py

### Phase 16.3 — Studio Feature Parity (✅ Complete Feb 28, 2026)
- ✅ Studio Projects page — intentionally kept minimal (no stats bar, no activity feed)
- ✅ Korean/English toggle in Studio navbar (i18n.ts + LanguageContext + KO/EN pill toggle + t() wired in navbar + project-dashboard)
- ✅ Studio Projects table column sort — clickable headers, ↑/↓ active indicator, faded ↑↓ inactive (Feb 28, 2026)
- ✅ Watson TTS voice updated to en-US_EmilyV3Voice (neural, less robotic) (Feb 28, 2026)
- ✅ Build Details card in Studio Pipeline page — enterprise stat row (Lucide icons, Vercel-style, no emojis) (Feb 28, 2026)
- ✅ Full Korean i18n — Studio: all static strings translated (pipeline, agents, versions, artifacts, delete modal) (Feb 28, 2026)
- ✅ Full Korean i18n — Enterprise: all static strings translated (artifacts, versions, pipeline, delete modal) (Feb 28, 2026)

### Phase 16.6 — Planner Archetype Expansion (✅ Complete Feb 28, 2026)
- ✅ planner.txt expanded from 10 → 25 archetypes
- ✅ render_path A/B field added for Tailwind vs Raw CSS routing
- ✅ Layout + content contracts for all 15 new archetypes (restaurant, medical, crypto, fitness, etc.)
- ✅ Existing 10 archetypes untouched

### Phase 16.1 — Bug Fixes (✅ Complete Feb 28, 2026)
- ✅ Enterprise chat persistence after Flask restart — DB-backed via /chat-history + /chat-messages endpoints (Feb 28, 2026)
- ✅ Studio chat persistence after Flask restart — always loads from DB on project switch (Feb 28, 2026)
- ✅ Studio + Enterprise: chat now shared when switching between Studio ↔ Enterprise — both always load from DB (Feb 28, 2026)
- ✅ Live output logs restored after Flask restart — Studio fetches from /versions/<v>/logs on load (Feb 28, 2026)
- ✅ Double timestamp removed from live output logs — Enterprise + Studio (Feb 28, 2026)
- ✅ Chat messages persist across builds, project switches, and Flask restarts (Feb 28, 2026)
- ✅ Stuck "Sending..." state auto-heals on project switch (Feb 28, 2026)
- ✅ Global build lock — friendly banner + chat reply when another project is building (Feb 28, 2026)
- ✅ Enterprise chat scroll to bottom on load (Feb 28, 2026)
- ✅ Studio agent cards restore green correctly on load — stale global execution-status no longer overrides DB (Feb 28, 2026)
- ✅ Studio agent cards restore green on project switch via URL pid param (Feb 28, 2026)
- ✅ Enterprise "Failed" badge suppressed during active build (!sending gate) (Feb 28, 2026)
- ✅ Build-lock banner text fixed — "chat is available while you wait" (Feb 28, 2026)
- ✅ EngineerAgent JSON repair — installed json_repair + char-walking backslash fixer (Feb 28, 2026)
- ✅ Delete modal disk cleanup — already in app.py (Feb 28, 2026)
- ✅ Build Details tokens/cost — Claude stream usage capture working (Feb 28, 2026)
- ✅ Studio build details stat row — displays after build completes (Feb 28, 2026)
- ✅ Enterprise BuildDetailsCard live refresh post-build — refreshKey bumps on COMPLETED (Feb 28, 2026)
- ✅ Tab persistence across page refresh — reads/writes localStorage archon_active_tab (Feb 28, 2026)
- ✅ Studio ↔ Enterprise design switch preserves selected project — ?pid= / ?projectId= passing (Feb 28, 2026)
- ✅ Studio pipeline page project name fix — fetches name from API when arriving via ?pid= (Feb 28, 2026)
- 🔴 Live output logs still global (same across all projects) — execution_state is server-wide, architectural fix needed

### Phase 17 — IBM Governance & NLU Integration (🔴 Planned)

#### 17.1 — Watson NLU Pre-Pipeline Analyzer (✅ Complete Feb 28, 2026)
- ✅ Watson NLU analyzes user prompt before PM Agent
- ✅ Extracts: sentiment, domain keywords, categories
- ✅ Smarter routing: frustrated sentiment (score < -0.5) → chat, not build
- ✅ NLU keyword context appended to project_context for classify_intent
- ✅ Graceful fallback when WATSON_NLU credentials missing (enabled=False)

#### 17.3 — Credit System (✅ Complete Feb 28, 2026)
- ✅ 1 credit = 2,500 tokens formula, minimum 1
- ✅ credits_used column on Execution model
- ✅ Credits calculated and saved on pipeline completion
- ✅ Build Details: shows credits used + model + duration (hides raw tokens/cost)
- ✅ Studio + Enterprise both display credits correctly
- ✅ Build Agent upgraded to claude-sonnet-4-6 (Feb 28, 2026)
- ✅ model_used display updated to "Claude Sonnet 4.6" (Feb 28, 2026)
- ✅ Navbar credit counter wired to real balance via /api/credits/balance (Feb 28, 2026)
- ✅ Build Details: "12 credits · 488 remaining" format (Feb 28, 2026)
- 🔴 Plan tiers: Starter 100/mo, Pro 500/mo, Agency unlimited (post-auth)
- 🔴 /api/credits/balance endpoint (pre-auth mock: 500 Pro credits minus all used)
- 🔴 Enterprise BuildDetailsCard live refresh post-build (UX polish)

#### 17.2 — Governance Agent (AI Factsheets) (✅ Complete Mar 1, 2026)
- ✅ GovernanceAgent wired into pipeline success block (non-fatal try/except)
- ✅ Factsheet: models, tokens, cost, duration, archetype, quality indicators, compliance flags
- ✅ governance_log TEXT column on Execution model + safe migration
- ✅ Governance sub-tab in Artifacts — Enterprise + Studio, with empty state for old builds
- ✅ /api/projects/<id>/versions/<ver>/factsheet endpoint
- ✅ Korean/English i18n keys
- ✅ Watson NLU prompt quality scoring (0-100) — IBM Watson NLU API
- ✅ Build confidence scoring (0-100) — files, archetype, images, speed
- ✅ Human Review Required auto-triggers when score < 50
- ✅ Factsheet v1.1 — scoring UI added non-destructively to existing layout
- ✅ Governance scoring logic fixed — removed gameable metrics (sentiment, design assets, build speed) (Mar 1, 2026)
- ✅ Governance UI polish — capitalization, layout, spacing, font sizes (Mar 1, 2026)
- ✅ Watson NLU added to Model Registry in factsheet (Mar 1, 2026)
- ✅ 17.3 Dashboard governance metrics — Avg Prompt Score (Sparkles/purple) + Avg Build Score (Shield/blue) in header (Mar 1, 2026)
- ✅ /api/dashboard/stats endpoint — averages scores from governance_log across all executions (Mar 1, 2026)
- ✅ Dashboard icon colors — Sparkles text-purple-400, Shield text-blue-400 (Mar 1, 2026)
- ✅ Backend build_confidence key fix in dashboard_stats() (Mar 1, 2026)
- ✅ README updated with Watson Governance section, architecture diagram, full roadmap table (Mar 1, 2026)
- ✅ 17.4 Dual PDF Export — "Download Client PDF" + "Download Internal PDF" buttons on Governance tab (Mar 1, 2026)
- ✅ 17.5 Delivery Readiness Gate — Quality Tier badges (High/Good/Low Quality) on Versions timeline + inline metadata on Governance tab (Mar 1, 2026)
- ✅ 17.5.1 Studio quality tier parity — version-timeline.tsx + artifact-viewer.tsx (Mar 1, 2026)
- ✅ 17.5.2 Quality tier inline metadata — replaced banner with inline line under factsheet title, both Studio + Enterprise (Mar 1, 2026)
- ✅ 17.5.3 Quality tier in PDF exports — Verified/Auditable badges row, overall score shown in both Client + Internal PDF (Mar 1, 2026)
- 🔴 /api/governance/summary cross-run analytics (future)

### Phase 16.5 — Authentication (🔴 Planned)
- 🔴 Sign up / Login pages
- 🔴 JWT + protected routes
- 🔴 User-scoped projects (owner_id already in DB schema)

### Phase 19 — Product Tour & Onboarding Walkthrough (🔴 Deferred — post beta testing)
- Scope and pattern TBD after recruiting 3-5 beta users
- See ROADMAP.md Phase 19 memo for full context

### Phase 18 — Unified Auth + Plan-Based UI Routing (🔴 Planned)
- 🔴 18.1 Landing/pricing page — Consumer vs Enterprise plan selector
- 🔴 18.2 Auth gates: Consumer login → frontend-consumer, Enterprise login → frontend
- 🔴 18.3 Enterprise design switcher (Studio ↔ Enterprise toggle in navbar)
- 🔴 18.4 Plan-aware credit limits (Consumer: 100/mo, Enterprise: 500/mo)
- 🔴 18.5 Upgrade flow: Consumer → Enterprise upsell modal

**Plan breakdown:**
- Consumer plan: frontend-consumer — simplified UI, light theme only
- Enterprise plan: frontend (default) + optional Studio (frontend-studio/) toggle — dark/light mode, full pipeline controls

---

## ✅ Parallel DALL-E Image Generation (Mar 1, 2026)
- Replaced sequential for loop in `agents/design_agent.py` with `concurrent.futures.ThreadPoolExecutor(max_workers=4)`
- All images now generate simultaneously — confirmed in Flask terminal (all 4 `-> Generating:` lines appear at once)
- Build time for image-heavy projects reduced significantly
- Tested: FF8 build generated 3/4 images in parallel (character_zell blocked by DALL-E content filter — see bug below)

## ✅ Stuck Build Reset Button (Mar 1, 2026)
- POST `/api/projects/<id>/reset-build` endpoint — marks stuck running execution as failed in DB
- Reset button appears in Enterprise (frontend) and Studio (frontend-studio/) pipeline chat after 8 min of no completion
- Red filled button matching Send button style, hidden during normal builds
- On click: calls reset endpoint, stops polling, clears sending state, resets agent cards

## ✅ UI Polish — Governance Shield Blue (Mar 1, 2026)
- Shield icon blue (text-blue-500) in Governance tab bar, factsheet header — Enterprise + Studio, light + dark mode
- Hexagon logo blue in light mode (text-blue-500), keeps primary color in dark mode — Enterprise + Studio

## ✅ UI Polish — Hexagon Icons + Emoji Cleanup (Mar 1, 2026)
- All Zap/lightning bolt icons replaced with Archon hexagon SVG — Studio + Enterprise
- Bot icon in agent chat bubbles replaced with hexagon SVG — Studio + Enterprise
- ⚡ emoji removed from agent build reply text — Studio + Enterprise
- Hexagon SVG uses text-primary (blue) in all themes

## ✅ Korean i18n Polish (Mar 1, 2026)
- Studio: status badges now in Korean in KO mode
- Enterprise + Studio: date format yyyy.mm.dd when language = KO
- Merged via PR from feat/ko-i18n-polish

## 🔧 Phase 16.5 Authentication (In Progress)
- ✅ Backend JWT auth — register, login, me, forgot-password, reset-password (Mar 1, 2026)
- ✅ Google OAuth backend endpoint /api/auth/google (Mar 1, 2026)
- ✅ frontend-studio/lib/auth.ts — authService with localStorage token management (Mar 1, 2026)
- ✅ AuthGuard — redirects unauthenticated users to /login (Mar 1, 2026)
- ✅ Login, Register, Forgot Password pages — Studio (frontend-studio/) (Mar 1, 2026)
- ✅ Sign out wired — closes dropdown + redirects to /login (Mar 1, 2026)
- ✅ Login page redesign — dark split-layout (form left, value props right) (Mar 1, 2026)
- ✅ IBM Plex Sans font applied via next/font/google — enterprise-grade typography (Mar 1, 2026)
- ✅ Right panel: pill badge, headline, bullets, IBM Watson trust badge — vertically centered (Mar 1, 2026)
- ✅ Updated value prop copy to agency-owner language (hours not weeks, certified, sign-off) (Mar 1, 2026)
- ✅ README updated — business case blockquote added at top (Mar 1, 2026)
- ✅ Register page redesign — dark split-layout matching login (Mar 1, 2026)
- ✅ Forgot password page redesign — dark split-layout matching login (Mar 1, 2026)
- ✅ "Forgot password?" link added to login form (Mar 1, 2026)
- ✅ Post-login/register redirect to Enterprise dark mode (Mar 1, 2026)
- ✅ Cross-origin token handoff via ?token= URL param — Studio → Enterprise (Mar 1, 2026)
- ✅ Enterprise defaults to dark mode on first visit (ThemeProvider fallback) (Mar 1, 2026)
- ✅ Enterprise (frontend) auth pages (login, register, forgot-password) — Mar 1, 2026
- ✅ Enterprise AuthGuard — redirects to /login if no token — Mar 1, 2026
- ✅ Enterprise Sign Out wired (authService.logout + redirect to /login) — Mar 1, 2026
- ✅ Studio ↔ Enterprise theme toggle passes token — Mar 1, 2026
- ✅ Folder rename refactor — frontend-v4→frontend, frontend→frontend-studio, frontend-consumer2→frontend-consumer (Mar 2, 2026)
- ✅ backend/requirements.txt updated — flask-jwt-extended and bcrypt added (Mar 2, 2026)
- ✅ Post-login redirect fixed — always lands on Enterprise projects page via ?tab=projects URL param (Mar 2, 2026)
- ✅ First-time login defaults to dark mode, repeat users keep their theme preference (Mar 2, 2026)
- ✅ Cross-origin theme handoff — Studio passes ?theme= to Enterprise on login (Mar 2, 2026)
- ✅ Studio favicon added — hexagon SVG in browser tab (Mar 2, 2026)
- ✅ Enterprise favicon color fixed — blue #3b82f6 (Mar 2, 2026)
- ✅ .vite/ added to .gitignore (Mar 2, 2026)
- 🔴 Google OAuth frontend wiring (needs Google Client ID)

## 🔴 Known Bug — Enterprise Tab Not Restoring on Switch from Studio (Partial)
- Login now correctly lands on projects tab ✅
- Remaining: when switching Studio → Enterprise mid-session, Enterprise loads previously cached tab instead of Studio's current tab
- Root cause: activeTab useState initializer reads localStorage before URL param effect runs

## 🔴 Known Bug — Enterprise Shows "Failed" Status During Active Build
- When a build is running in Studio and user switches to Enterprise, Enterprise shows "Failed" badge on the version card
- Actual status is Running — corrects itself to Completed when build finishes
- Root cause: Enterprise VersionsView reads stale DB status on load; DB version record shows last failed state until pipeline writes COMPLETED
- Fix needed: suppress "Failed" badge if a live build is currently running for that project (check execution-status endpoint on load)

## 🔴 Known Bug — DALL-E Content Filter on Character Names
- Character name "Zell" (FF8) triggers DALL-E content policy violation (error 400)
- Other characters in same build (Squall, Rinoa) generate fine
- Root cause: DALL-E flags certain proper nouns as policy violations unpredictably
- Fix: add fallback prompt that strips character name and uses description only if content filter fires
- Test: FF8 character page build — Zell image should generate with fallback prompt

## ✅ Chat Persistence — Partial Fix (Mar 1, 2026)
- User messages now save to DB immediately on send (before pipeline starts)
- Persists correctly when switching Studio ↔ Enterprise mid-build
- 🔴 Remaining bug: Agent reply disappears during build, returns after completion
- Root cause: agent reply generated at END of /chat — nothing to pre-save
- Fix later: cache agent reply in sessionStorage immediately, sync to DB on completion

## 🔴 Known Quality Bug — Image Generation Regression

DALL-E character images stopped matching character descriptions accurately after Phase 14 (scoped iteration enforcement). Previously generated highly accurate character likenesses (e.g. FF7 Cloud/Barrett). Now produces generic mid-tier outputs.

**Suspected cause:** `iteration_context` injected before main prompt may be bleeding into or compressing the Design Agent's image prompt context.

**To fix:**
- Audit `agents/design_agent.py` — verify character name/description passes in fully
- Ensure `iteration_context` only affects EngineerAgent, not DesignAgent
- Restore DALL-E prompt format that worked pre-Phase 14
- Test with: "Final Fantasy 7 character selection page with Cloud Strife and Barrett"
