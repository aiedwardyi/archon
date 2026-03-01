# Archon — Execution Roadmap

## Purpose

Archon is a multi-agent platform that converts product ideas into auditable
web applications with full version history. Target market: digital agencies
and enterprises delivering client apps to non-technical clients.

**Core value proposition:**
- Every prompt creates a full artifact set: Brief + Plan + Code + live preview
- Complete version history — every decision is auditable and reversible
- Agencies can show clients exactly what was built and why, version by version
- Business language UI — no developer jargon anywhere

**The MOAT:** The Versions page. Lovable/v0 show current state only.
Archon shows complete decision history with artifacts and live preview per version.

---

## Target User

Non-technical agency owner or project lead who:
- Cannot read code — needs to SEE the app running
- Needs to show clients every decision made during development
- Needs business language, not developer jargon

**Competitive positioning:** "Build client apps with AI. Show them everything."

---

## Architecture
```
User Input (Chat Panel)
    ↓
Prompt History (context continuation)
    ↓
Requirements Agent (OpenAI GPT-4o-mini) → Brief artifact (versioned)
    ↓
Architecture Agent (Gemini Flash)        → Build Plan artifact (versioned)
    ↓
Design Agent (GPT-4o-mini + DALL-E 3)   → Image assets (versioned, served locally)
    ↓
Build Agent (Claude Sonnet 4.5)          → Code files (versioned)
    ↓
Execution Result → Database + UI + Version Timeline + Live Preview
```

---

## Phased Execution Plan

### Phase 1-6.4 (✅ Completed)
Core pipeline, schemas, multi-agent coordination, SQLite persistence,
enterprise UI (10 screens, light + dark mode, business language throughout).

### Phase 7A — Iterative Pipeline & Version History (✅ Completed)
- Every prompt runs full pipeline → versioned DB record
- Prompt history continuation across iterations
- /iterate, /restore, /versions endpoints
- sessionStorage caching, real log persistence per execution

### Phase 7B — Live Preview (✅ Completed)
- Build Agent: Claude Sonnet 4.5 (primary), Gemini fallback
- Engineer prompt: self-contained HTML, 500-line limit, max_tokens 32000
- /api/preview/<project_id>/<version> serving generated HTML
- Live preview iframe in Versions + Artifacts pages
- Desktop/mobile viewport toggle working
- Agent card flash bug fixed

### Phase 7C — Stability & State Fixes (✅ Completed)
- Pipeline state restores from DB on page refresh
- Build completion uses DB as ground truth
- Prompt history persisted to sessionStorage across iterations
- Logs save by version number — Artifacts logs tab version-correct
- Pipeline polling restarts when navigating back to mid-run build
- Global block prevents concurrent project builds

### Phase 7D — UI Polish & Quick Wins (✅ Completed)
- ✅ 7D.1 Navbar real project name + version
- ✅ 7D.2 Projects table: Project ID column added
- ✅ 7D.3 Delete project + delete all with type-to-confirm modal
- ✅ 7D.4 Avatar dropdown (v0-style: email, dark mode, credits, sign out)
- ✅ 7D.5 Versions page live preview height increase
- ✅ 7D.6 Artifacts + Navbar version sync fixed (custom event bus)

### Phase 7E — Output Quality (✅ Completed)
- Design Agent built: GPT-4o-mini plans images → DALL-E 3 generates them
- Images downloaded to disk, served via /api/assets/<project_id>/<version>/<file>
- Design Agent skips image generation for dashboards/tools (cost saving)
- Engineer prompt: 10-shell layout intelligence system
- JSON repair fix: backtick-wrapped hex colors stripped before parse

### Phase 7F — Chatbox Upgrades (✅ Completed)
- ✅ 7F.1 File + media upload with drag-and-drop
- ✅ 7F.2 Graceful agent reply for unsupported inputs
- ✅ 7F.3 Master log accumulation across versions

### Phase 7G — Output Quality v2 (✅ Completed)
- ✅ UI archetype lock: Planner classifies, Engineer enforces as hard constraint
- ✅ Layout + content contracts for all 10 archetypes
- ✅ Two-file split: src/index.html + src/style.css
- ✅ Preview inline CSS stitching
- ✅ CSS design seed: glow/glass/shimmer in engineer.txt
- ✅ Pipeline real-time update bug fix
- ✅ Parallel pipeline (~30-40% faster)
- ✅ DALL-E content filter fix

### Phase 7H — Conversational Chatbox (✅ Completed)
- ✅ PM Agent classify_intent: routes build vs chat
- ✅ /chat endpoint — no DB record, no version created for questions
- ✅ Archon reply bubbles in chatbox UI
- ✅ Chat history passed into build context
- ✅ Context-aware replies using project PRD
- ✅ Download project as zip (with assets)

### Phase 8 — Publish + Client Deliverables (🔧 In Progress)
- ✅ 8.1 One-click Publish — shareable hosted URL
- ✅ 8.UI.1 Artifact cards link to Artifacts page with tab pre-selection
- ✅ 8.UI.2 Account modals — Profile, Settings, Pricing, Documentation
- 🔴 8.2 PDF export of full build history (client audit trail)
- 🔴 8.3 Client shareable read-only link
- 🔴 8.4 White-label option (agency branding)

---

## Competitive Positioning

| Feature | Lovable/v0 | Archon |
|---------|-----------|--------|
| Context continuation | ✅ | ✅ |
| Full chain on every edit | ❌ | ✅ |
| Artifact trail per version | ❌ | ✅ |
| Restore previous version | ✅ | ✅ |
| Live preview | ✅ | ✅ |
| Version history with preview | ❌ | ✅ |
| Auditable Brief per iteration | ❌ | ✅ |
| AI-generated design assets | ❌ | ✅ |
| Smart layout detection (10 shells) | ❌ | ✅ |
| Conversational chatbox | ✅ | ✅ |
| Download project as zip | ❌ | ✅ |
| One-click publish | ✅ | ✅ |
| Persistent chat history (DB) | ❌ | ✅ |
| Artifact cards → tab navigation | ❌ | ✅ |
| Account modals (Profile/Settings/Pricing) | ✅ | ✅ |
| Client PDF export | ❌ | 🚧 8 |
| Non-technical agency UI | ❌ | ✅ |
| Korean/English i18n | ❌ | ✅ |

---

## Current State (Feb 2026)

- ✅ Four-agent pipeline (Requirements → Architecture → Design → Build)
- ✅ Build Agent: Claude Sonnet 4.5 (primary), Gemini fallback
- ✅ Flask backend (port 5000), SQLite, full persistence
- ✅ Enterprise UI — frontend/ (port 3000), light + dark mode
- ✅ Consumer UI — frontend-consumer2/ (port 3002), Korean/English i18n
- ✅ Iterative pipeline with full version history
- ✅ Iteration mode hardened (scope enforcement, ancestor chain walk, asset reuse)
- ✅ Live preview iframe (Versions + Artifacts pages)
- ✅ Conversational chatbox — Archon talks back, advises, routes build vs chat
- ✅ Download project as zip with assets
- ✅ Design Agent — DALL-E 3 images, locally served, reused on iterations
- ✅ Engineer prompt — 10-shell layout intelligence, CSS design seed
- ✅ One-click publish — shareable hosted URL
- ✅ Artifact cards link to Artifacts page with tab pre-selection
- ✅ Account modals — Profile, Settings, Pricing, Documentation
- ✅ Chat message persistence (DB-backed, survives refresh)
- ✅ Consumer Versions page — timeline + split panel + preview per version (THE MOAT)
- ✅ Consumer frontend polished — Archon branding, newest-first timeline, glow effects, full Korean i18n
- 🔧 Consumer UX bug fixes — stale state, code tab fixed, failed overlay fixed, progress bar restored (smooth animation, minor edge cases remain), preview iframe regression pending fix
- ✅ Phase 15.4 — Enterprise UI (frontend-v4) — Vite + React + shadcn/ui on port 8080, real API wiring, 4-theme foundation
- ✅ Phase 15.5.S — Studio dashboard reviewed — kept minimal (no stats bar, no activity feed)
- 🔧 Phase 15.5 — Enterprise UI polish — Pipeline tab chat UI done, stats/activity/publish wired, modals still needed
- 🔴 PDF Export + Client Read-Only Link (Phase 8 remaining)

### Phase 9 — Pipeline Page & Classifier Improvements (⬜ Planned)
- ✅ Classifier too sensitive — opinion questions triggering builds
- Chat panel needs max-height + scrollable container
- Consider split layout: agent pipeline fixed top, chat scrollable below

### Phase 10 — IBM Watson Integration (🔧 In Progress)
- ✅ Speech to Text: user speaks prompts instead of typing
- ✅ Text to Speech: Archon reads replies aloud
- Watson Assistant: power conversational chatbox natively
- AI Factsheets / governance: model monitoring for enterprise credibility
- Natural Language Understanding: analyze prompt intent before pipeline routing
- Goal: IBM AI Engineer application showcase + $200 cloud credit usage

### 10.4 App Type Lock (Archetype Guardrail) ✅
- Added `locked_ui_archetype` at the Project level.
- First successful build persists the detected `ui_archetype`.
- All subsequent iterations must reuse the locked archetype.
- Planner receives locked archetype context and cannot reclassify.
- Backend overrides planner output if archetype differs.
- Explicit app-type change requests return a chat response suggesting a new project.
- Preserves full Brief / Plan / Code artifact trail per version.
Impact:
- Prevents unintended app-type mutation (e.g., landing → dashboard).
- Enables stable, Lovable-style iteration while maintaining audit trail moat.

### Phase 11 — Pipeline Page Redesign (⬜ Planned)
- Three-panel layout for large screens:
  Left: conversation/chat (scrollable)
  Top right: agent pipeline status cards
  Bottom right: live preview iframe
- Enterprise/agency target — assumes large monitor
- Classifier sensitivity fix: opinion questions never trigger builds
- Chat panel max-height with internal scroll

### Phase 12 — Output Domain Personality (⬜ Planned)
- Generated apps reuse same shell structure regardless of domain
- "Uber clone" produces generic dashboard instead of ride-sharing UI
- Root cause: archetype lock picks shell correctly but injects no domain aesthetics
- Fix: engineer prompt needs domain context injection — color palette, component vocabulary, visual metaphors per industry
- Examples: ride-sharing = map tiles, driver cards, live ping aesthetic
-           fintech = green/red tickers, candlestick feel, data density
-           gaming = dark immersive, HUD elements, particle effects
- Approach: planner agent injects domain_personality block into engineer task
- This is the main quality gap vs Lovable/v0

### Phase 12.1 — Domain Personality Upgrade (✅ Completed Feb 2026)
- Injected Tailwind CDN + Alpine.js for visual pages
- 18 archetypes with domain-specific palettes, fonts, and components
- pollinations.ai for fictional character/game asset generation
- Anti-patterns list to prevent generic AI output
- Result: FF7 fan page output matches Lovable quality

### Phase 13.1 — Chat Message Persistence (✅ Completed)
- chat_messages TEXT column on executions table (JSON array)
- POST /api/projects/:id/chat saves user + Archon messages to active head
- GET /api/projects/:id/chat-history returns full conversation
- Frontend restores chat across refreshes and machines

### Phase 14 — Iteration Mode Fixes (✅ Completed Feb 2026)
- Scope enforcement path normalization (safe_write.py `_tail_after_code()`)
- Archetype lock conversion phrase detection (prevent false positives like "add a mini game")
- Ancestor chain traversal for failed versions (walk up to 5 hops to find last successful code)
- Design asset reuse on iterations (skip DALL-E regeneration, reuse ancestor's last_design_assets.json)
- Asset URL version extraction from local_path (correct /api/assets/{pid}/{version}/ URL)
- Planner iteration file constraints (force output_files to src/index.html + src/style.css only)
- Preview endpoint CSS/JS inlining (inline all *.css and *.js files from code/src/)
- Strengthen iteration_context in engineer prompt (5 strict surgical edit rules, placed before main prompt)

### Phase 15 — Consumer Frontend v2 (✅ Completed Feb 2026)
- Copied and wired Projects/frontend to repo as frontend-consumer2 (port 3002)
- Connected to Flask backend via orchestrator.ts service layer
- Real iframe preview with desktop/mobile viewport toggle
- **Versions page (THE MOAT)** — timeline + split panel + live preview per version
- Restore version functionality from versions timeline
- File viewer (Code tab) wired to real /api/projects/:id/versions/:v/files
- Non-technical wording pass (Brief, Build Plan, What Was Built, Publish)
- Korean/English language toggle with i18n.ts translation system (30+ keys)
- CORS allowlist updated for ports 3001 and 3002

### Phase 15.1 — Repo Cleanup (✅ Completed Feb 2026)
- Removed apps/offline-vite-react (unused old frontend)
- Added node_modules/, dist/, .venv/, .claude/ to .gitignore
- Merged enterprise-ui branch into main
- Deleted enterprise-ui local branch

### Phase 15.2 — Consumer Frontend Polish (✅ Completed Feb 2026)
- Renamed all "ai-dev-team" references to "Archon" (package.json, metadata, HTML, overlays)
- Versions timeline newest first (removed incorrect reverse, matching API DESC order)
- Versions right panel glow effect on iframe container
- Hide restore button on current/latest version (maxVersion guard)
- Version card glow/contrast polish (darker bg, indigo ring, gradient overlay on selected)
- Logo split corrected: "Arch" + "on" with violet accent
- Full Korean i18n coverage: sidebar (9 strings), logs tab, status badges, agent messages, chat suggestions
- Fixed versions preview URL bug (version field vs version_number mismatch with API)

### Phase 15.3 — Consumer UX Bug Fixes (🔧 Partially Complete Feb 2026)
- Reset localPrd/localPlan/localTasks/previewVersion on projectId change (stale data across project switches)
- Removed opacity-0/opacity-100 transition on workspace div (iframe invisible after build completes)
- Progress bar restored to smooth sessionStorage animation (minor rapid-navigation edge cases remain)
- Expanded getTechColor to match 7 keyword categories (frontend/backend/database/state/ml/hosting/styling)
- Tech map rendering handles no-colon entries (natural-language PRD format)
- Engineer prompt: added MOCK DATA REQUIREMENT block (no more empty-state generated apps)
- Failed projects no longer show progress bar overlay
- Code tab fixed: reads data.tree from /files endpoint (was reading data.files)
- Preview iframe regression: sometimes reverts to placeholder after build — pending fix


## Phase 15.4 - Enterprise UI (frontend-v4) COMPLETED Feb 27, 2026

### What was built
- Copied Lovable-generated Enterprise design (archon-v4) to frontend-v4/
- Vite + React + TypeScript + Tailwind + shadcn/ui running on port 8080
- 4-theme system foundation (Enterprise Light/Dark, Studio Light/Dark)
- Korean/English language toggle with localStorage persistence

### API Wiring Completed
- Projects page connected to real Flask API with 3s polling
- Fixed N+1 query - added version_count to Project.to_dict() in models.py
- Project row selection with shared selectedProjectId state
- Shared selectedVersion state flows between Versions, Artifacts, Navbar
- VersionsView: real versions list + real iframe preview per version
- ArtifactsView: real Brief (PRD), Plan, Code, Tasks, Logs
- Navbar: real project name + version in breadcrumb
- Favicon: lightning bolt SVG + Archon - Enterprise Build title

## Phase 15.5.S - Studio Dashboard Review (✅ Feb 28, 2026)
- Stats bar and Recent Activity feed were prototyped then reverted — not shipping
- Studio Projects page intentionally kept minimal: project count cards (Total/Running/Completed/Failed) + search/filter + full-width table
- Enterprise (frontend-v4) retains its own stats bar and activity feed via `/api/stats` and `/api/activity` endpoints

## Phase 16 — UI Parity, Auth & Polish (🔧 In Progress Feb 2026)

### 16.2 — Branding (✅ Complete Feb 28, 2026)
- ✅ Tab titles: "Archon - Studio Build", "Archon - Consumer Build"
- ✅ Hexagon logo in frontend-v4 and frontend-consumer2
- ✅ Hexagon SVG favicon in frontend-v4 and frontend-consumer2
- ✅ load_dotenv fixed to always load backend/.env

### 16.4 — Watson STT/TTS for Enterprise (✅ Complete Feb 28, 2026)
- ✅ Mic (STT) + speaker (TTS) buttons in frontend-v4 pipeline
- ✅ Fixed WATSON_TTS_API_KEY / WATSON_STT_API_KEY env var mismatch

## Phase 15.5 - Enterprise UI Polish (🔧 IN PROGRESS)

### Completed
- ✅ Checkbox UX fix — no longer triggers row navigation
- ✅ Stats bar wired to real project counts (total/running/completed/failed)
- ✅ Activity feed wired to real recent executions with collapse/expand
- ✅ Avg build time stat with fallback for missing data
- ✅ Publish and Download buttons wired to real endpoints
- ✅ Pipeline tab — full chat UI with conversation panel, input bar, agent status cards
- ✅ Pipeline tab — /chat (conversational) and /iterate (build) endpoints wired
- ✅ Pipeline tab — chat history loaded from DB on project switch
- ✅ Pipeline tab — live output log panel with auto-scroll
- ✅ Replaced Sparkles icon with Zap (lightning bolt) to match Archon branding
- ✅ Added missing i18n keys for pipeline UI (designAgent, send, noMessages, etc.)
- ✅ New Project modal (Name + Description → POST /api/projects, auto-selects and opens Pipeline tab)
- ✅ "What Was Built" summary — real file + image counts from backend (e.g. "2 code files · 3 images generated")
- ✅ Backend returns images_generated count from last_design_assets.json per version
- ✅ VersionsView files changed count uses real files_generated from API
- ✅ ArtifactsView Code tab — fixed height, independent scroll for file tree and code viewer
- ✅ WelcomeBanner — live backend health check (green/red dot with 10s polling)
- ✅ i18n keys added: backendOffline, projectName, projectDescription, creating, create, cancel
- ✅ Artifact cards (Brief/Plan/Code) in VersionsView navigate to Artifacts tab with correct sub-tab pre-selected
- ✅ Code tab scrollbars fixed — outer grid overflow:hidden with calc height, pre overflow:auto, minWidth:0
- ✅ Renamed "Running" → "Building" (EN) / "빌딩 중" (KO) across i18n and ProjectTable
- ✅ Pipeline header status badge — colored rounded-full pills (blue/building, emerald/completed, red/failed, gray/idle)
- ✅ Agent pipeline status persists after reload — reads DB status (success/failed/running)
- ✅ Logs saved for successful builds (backend app.py)
- ✅ Backend health indicator — red dot + "Backend offline" when Flask unreachable
- ✅ Status badge colors — green/red/blue pills in Pipeline header and Projects table
- ✅ Search filter on Projects page — client-side case-insensitive name filtering
- ✅ Red dot pulse animation on "Backend offline" indicator (WelcomeBanner)
- ✅ Removed Description field from New Project modal (name only, sends empty string)
- ✅ Pipeline tab no longer auto-scrolls to bottom on initial load (guarded by ref + timer)

### Remaining work
- ✅ Live output + agent pipeline no longer bleeds across projects (pipeline state resets on project switch)
- ✅ Chat messages persist via sessionStorage keyed by project ID (survives tab/project switching)
- ✅ Pipeline tab scroll-to-top fixed (container ref + triple scroll target)
- 🔴 JSON repair bug — intermittent EngineerAgent \escape error (prompts/engineer.txt fix)

## Phase 16 — UI Parity, Auth & Polish (🔧 In Progress Feb 2026)

### 16.2 — Branding (✅ Complete Feb 28, 2026)
- ✅ Tab titles: "Archon - Studio Build", "Archon - Consumer Build"
- ✅ Hexagon logo in frontend-v4 and frontend-consumer2
- ✅ Hexagon SVG favicon in frontend-v4 and frontend-consumer2
- ✅ load_dotenv fixed to always load backend/.env

### 16.4 — Watson STT/TTS for Enterprise (✅ Complete Feb 28, 2026)
- ✅ Mic (STT) + speaker (TTS) buttons in frontend-v4 pipeline
- ✅ Fixed WATSON_TTS_API_KEY / WATSON_STT_API_KEY env var mismatch

### 16.3 — Studio Feature Parity (✅ Complete Feb 28, 2026)
- ✅ Projects page kept minimal by design
- ✅ Korean/English toggle in Studio navbar (i18n.ts + LanguageContext + KO/EN pills)
- ✅ Studio Projects table column sort — clickable headers, ↑/↓ active indicator (Feb 28, 2026)
- ✅ Build Details card in Studio Pipeline page — enterprise stat row (Lucide icons, Vercel-style, no emojis) (Feb 28, 2026)
- ✅ Full Korean i18n — Studio + Enterprise all static strings translated (Feb 28, 2026)

### 16.1 — Bug Fixes (✅ Complete Feb 28, 2026)
- ✅ Enterprise chat persistence after Flask restart (Feb 28, 2026)
- ✅ Studio + Enterprise chat shared when switching design modes (Feb 28, 2026)
- ✅ Global build lock — friendly banner + chat reply, correct text (Feb 28, 2026)
- ✅ Enterprise chat scroll to bottom on load (Feb 28, 2026)
- ✅ Studio agent cards restore green on load + on project switch (Feb 28, 2026)
- ✅ Enterprise "Failed" badge suppressed during active build (Feb 28, 2026)
- ✅ EngineerAgent JSON repair — json_repair + char-walking backslash fixer (Feb 28, 2026)
- ✅ Live output logs restored after Flask restart (Feb 28, 2026)
- ✅ Build Details tokens/cost working (Feb 28, 2026)
- ✅ Studio build details stat row displays after build completes (Feb 28, 2026)
- 🔴 Live output logs still global (execution_state is server-wide — architectural fix needed)

### 16.5 — Authentication (🔴 Planned)
- 🔴 Sign up / Login pages
- 🔴 JWT + protected routes
- 🔴 User-scoped projects (owner_id already in DB schema)

### 16.6 — Planner Archetype Expansion (✅ Complete Feb 28, 2026)

### Phase 17 — IBM Governance & NLU Integration (🔧 In Progress)

#### 17.1 — Watson NLU Pre-Pipeline Analyzer (✅ Complete Feb 28, 2026)
- ✅ Watson NLU analyzes user prompt before PM Agent
- ✅ Extracts: sentiment, domain keywords, categories
- ✅ Smarter routing: frustrated sentiment (score < -0.5) → empathetic chat, not build
- ✅ NLU keyword context appended to project_context for classify_intent
- ✅ Graceful fallback when WATSON_NLU credentials missing (enabled=False, no crashes)
- IBM credential: WATSON_NLU_URL + WATSON_NLU_API_KEY in backend/.env ✅

#### 17.3 — Credit System (✅ Complete Feb 28, 2026)
- ✅ 1 credit = 2,500 tokens, minimum 1
- ✅ credits_used column on Execution model
- ✅ Credits calculated + saved on pipeline completion
- ✅ Build Details: credits used + model + duration (hides raw cost)
- ✅ Studio + Enterprise both display credits correctly
- ✅ Build Agent upgraded to claude-sonnet-4-6 (Feb 28, 2026)
- ✅ model_used display updated to "Claude Sonnet 4.6" (Feb 28, 2026)
- ✅ Navbar credit counter wired to real balance via /api/credits/balance (Feb 28, 2026)
- ✅ Build Details: "12 credits · 488 remaining" format (Feb 28, 2026)
- 🔴 Plan tiers: Starter 100/mo, Pro 500/mo, Agency unlimited (post-auth)
- 🔴 /api/credits/balance endpoint (pre-auth mock: 500 Pro credits minus all used)
- ✅ Enterprise BuildDetailsCard live refresh post-build (Feb 28, 2026)

#### 17.2 — Governance Agent (AI Factsheets) (✅ Complete Mar 1, 2026)
- ✅ GovernanceAgent runs after every successful pipeline completion
- ✅ Structured Factsheet per version: models used, tokens, cost, duration, archetype, quality indicators, compliance flags
- ✅ governance_log TEXT column on Execution model (safe ALTER TABLE migration)
- ✅ Factsheet saved to disk (last_factsheet.json) + DB (governance_log JSON)
- ✅ Governance sub-tab in Artifacts page — Enterprise (frontend-v4) + Studio (frontend/)
- ✅ Empty state message for old builds pre-dating GovernanceAgent
- ✅ /api/projects/<id>/versions/<ver>/factsheet endpoint (disk-first, DB fallback, 404 graceful)
- ✅ Korean/English i18n keys added in both frontends
- ✅ Watson NLU prompt quality scoring (0-100) — powered by IBM Watson NLU API (Mar 1, 2026)
- ✅ Build confidence scoring (0-100) — computed from files, archetype, images, speed (Mar 1, 2026)
- ✅ Human Review Required flag auto-triggers when prompt or build score < 50 (Mar 1, 2026)
- ✅ Factsheet v1.1 — scoring section added to existing layout (non-destructive)
- ✅ Governance scoring logic fixed — removed sentiment, design assets, build speed as gameable metrics (Mar 1, 2026)
- ✅ Governance UI polish — capitalization, layout, spacing, font sizes throughout factsheet (Mar 1, 2026)
- ✅ Watson NLU added to Model Registry in factsheet (Mar 1, 2026)
- ✅ Dashboard icon colors — Sparkles text-purple-400, Shield text-blue-400 (Mar 1, 2026)
- ✅ Backend build_confidence key fix in dashboard_stats() (Mar 1, 2026)
- 🔴 PDF export — two variants: Client PDF (clean certificate) + Internal PDF (full metrics) (Phase 17.4)
- 🔴 Delivery Readiness Gate — configurable score threshold (default 85/100), flags version as client-ready (Phase 17.5)
- 🔴 Cross-run analytics endpoint: /api/governance/summary (future)
- Resume value: governed, auditable AI pipeline with IBM Watson scoring — rare even among senior IBM AEs

#### 17.3 — Dashboard Governance Metrics (✅ Mar 1, 2026)
- ✅ Replaced "Pipelines Today" with Avg Prompt Score (Sparkles icon, purple, /100 suffix)
- ✅ Replaced "Lines Generated" with Avg Build Score (Shield icon, blue, /100 suffix)
- ✅ GET /api/dashboard/stats endpoint — averages prompt + build scores from governance_log
- ✅ Nulls skipped — pre-v1.1 builds show "—" not 0
- ✅ Enterprise dashboard (frontend-v4 WelcomeBanner) updated
- ✅ Studio had no equivalent header cards — no changes needed

#### 17.4 — Dual PDF Export (🔴 Planned)
- 🔴 Two buttons on Governance tab: "Download Client PDF" + "Download Internal PDF"
- 🔴 Client PDF: project name, AI models used, compliance badges, files/images generated. No scores, no cost, no tokens.
- 🔴 Internal PDF: full factsheet — scores, tokens, cost, duration, iteration history, pass/fail indicators
- 🔴 Each version's artifacts + factsheet printable per version (Brief + Plan + Code + Factsheet)
- 🔴 Solves Phase 8.2 client audit trail requirement

#### 17.3 — Dashboard Governance Metrics (🔴 Planned)
- 🔴 Replace "Pipelines Today" header stat with **Avg Prompt Score** (Sparkles icon, /100 suffix)
- 🔴 Replace "Lines Generated" header stat with **Avg Build Score** (Shield icon, /100 suffix)
- 🔴 New backend endpoint: GET /api/dashboard/stats — queries all executions, parses governance_log JSON, averages prompt + build scores
- 🔴 Nulls skipped in average (pre-v1.1 builds without factsheet show "—" not 0)
- 🔴 Frontend header pulls from endpoint and displays live averages
- 🔴 Both Enterprise (frontend-v4) and Studio (frontend/) dashboards updated

#### 17.4 — Dual PDF Export (🔴 Planned)
- 🔴 Configurable quality threshold per project (default 85/100)
- 🔴 Version flagged as "Client Ready" or "Needs Iteration" based on combined score
- 🔴 Visible indicator on Versions timeline (green checkmark vs yellow flag)
- 🔴 Requires output evaluation agent to score how well build matched intent
- 🔴 Note: current scores (prompt clarity + build quality) are good signals but not perfect pass/fail gates
  — output evaluation (send prompt + HTML to AI for match scoring) needed for full accuracy
- ✅ Expanded planner.txt from 10 → 25 archetypes
- ✅ Added render_path A/B field for Tailwind vs Raw CSS routing
- ✅ Layout + content contracts for all 15 new archetypes
- ✅ Existing 10 archetypes untouched

---

## Phase 19 — Product Tour & Onboarding Walkthrough (🔴 Deferred)

First-time user guidance system. Pattern and scope TBD after beta user testing.

**Memo (Mar 1, 2026):** Deferring implementation until after initial user testing.
Will recruit 3-5 beta users to identify where they actually get stuck — rather than
guessing. Tour design will be driven by real friction points, not assumptions.

- Enterprise users may only need a minimal welcome modal + "?" help button
- Consumer users may need a full spotlight tour with Korean i18n
- Pattern choice (modal overlay vs spotlight tooltip) decided post-testing

### Planned sub-phases (scope pending user research)
- 🔴 19.1 Enterprise (frontend-v4) — welcome moment + optional per-page tips
- 🔴 19.2 Studio (frontend/) — minimal, same pattern as Enterprise
- 🔴 19.3 Consumer (frontend-consumer2) — fuller guidance + Korean i18n

**Tech candidate:** Shepherd.js (spotlight tooltips, React-compatible, free)
**Revisit:** After first round of beta user sessions

---

## Phase 18 — Unified Auth + Plan-Based UI Routing (🔴 Planned)

**Business model:** Two plans, two UI experiences. One login, one backend.

| Plan | UI | Features |
|------|----|---------|
| Consumer | frontend-consumer2 (simplified) | Light theme only, standard builds, version history |
| Enterprise | frontend-v4 or frontend/ (power) | Light + Dark mode, Studio or Enterprise design toggle, advanced pipeline controls |

**Flow:**
- User signs up → picks Consumer or Enterprise plan
- Routed to correct UI automatically based on plan
- Enterprise users can toggle between Studio (frontend/) and Enterprise (frontend-v4) designs
- Upgrade path: Consumer → Enterprise unlocks full UI switcher
- Same Flask backend serves both

**Key principle:** Consumer UI is simplified for non-technical clients. Enterprise UI is for agencies and power users who need full audit trail, pipeline controls, and theme flexibility.

- 🔴 18.1 Landing/pricing page with plan selector (Consumer vs Enterprise)
- 🔴 18.2 Auth gates: Consumer login → frontend-consumer2, Enterprise login → frontend-v4
- 🔴 18.3 Enterprise design switcher (Studio ↔ Enterprise toggle in navbar)
- 🔴 18.4 Plan-aware credit limits (Consumer: 100/mo, Enterprise: 500/mo)
- 🔴 18.5 Upgrade flow: Consumer → Enterprise upsell modal

---

## ✅ Parallel DALL-E Image Generation (Mar 1, 2026)
- `agents/design_agent.py` — replaced sequential for loop with `concurrent.futures.ThreadPoolExecutor(max_workers=4)`
- All images generate simultaneously — confirmed in Flask terminal
- Significant build time reduction for image-heavy projects
- Merged via PR from `feat/parallel-image-generation`

## ✅ Stuck Build Reset Button (Mar 1, 2026)
- `POST /api/projects/<id>/reset-build` — marks stuck running execution as failed in DB
- Reset button in Enterprise + Studio pipeline chat — appears after 8 min build with no completion
- Red filled button, hidden during normal operation
- Merged via PR from `feat/reset-button`

## ✅ UI Polish — Governance Shield Blue (Mar 1, 2026)
- Shield icon `text-blue-500` in Governance tab + factsheet header — Enterprise + Studio, light + dark mode
- Hexagon logo `text-blue-500` in light mode, `text-primary` in dark mode — Enterprise + Studio

## 🔴 Known Bug — DALL-E Content Filter on Character Names
- Certain character names (e.g. "Zell" from FF8) trigger DALL-E content policy error 400
- Other characters in the same build generate fine (Squall, Rinoa passed)
- Root cause: DALL-E flags specific proper nouns unpredictably as policy violations
- **Fix:** Add fallback in `_generate_one()` — on content_policy_violation error, retry with description-only prompt (strip character name)
- **Test:** FF8 character page build — Zell image should generate via fallback

## 🔴 Known Bug — Chat Messages Disappear During Build When Switching UIs
- Messages sent during an active build disappear when switching Studio ↔ Enterprise
- Messages reappear after build completes (save to DB on pipeline completion, not on send)
- **Fix:** Save chat messages to DB immediately on send, not after pipeline completes
- Affects: messages sent to actively building projects only

## Known Quality Bug — Image Generation Regression (🔴 Active)

**Problem:** DALL-E character images stopped matching character descriptions accurately after scoped iteration enforcement was added (Phase 14). Previously generated highly accurate character likenesses (e.g. FF7 Cloud/Barrett). Now produces generic mid-tier outputs.

**Root cause hypothesis:** Iteration enforcement rules placed BEFORE the main prompt in `engineer.txt` are interfering with the Design Agent's image prompt generation path, or the Design Agent's prompt context is being compressed/truncated.

**Fix needed:**
- Audit Design Agent prompt construction — ensure character names + descriptions flow in fully
- Separate iteration_context injection so it only affects EngineerAgent, not DesignAgent
- Consider restoring the exact DALL-E prompt format that produced high-quality results pre-Phase 14
- Test: prompt "Final Fantasy 7 character selection page with Cloud Strife and Barrett" and verify image accuracy
