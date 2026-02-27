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

**The MOAT:** The Versions page. Competitors show current state only.
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
- ✅ 7D.4 Avatar dropdown (email, dark mode, credits, sign out)
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

| Feature | Competitors | Archon |
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
- ✅ Phase 15.5 — Enterprise UI polish complete — Pipeline chat UI, delete modal, build details, JSON repair, all state bugs fixed
- 🔧 Phase 15.6 — Frontend cleanup & tab sync in progress — Studio/Enterprise switcher, tab sync via URL query params, deprecated frontend-consumer removed
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
- Enables stable iteration while maintaining audit trail moat.

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
- This is the main quality gap vs Competitors

### Phase 12.1 — Domain Personality Upgrade (✅ Completed Feb 2026)
- Injected Tailwind CDN + Alpine.js for visual pages
- 18 archetypes with domain-specific palettes, fonts, and components
- pollinations.ai for fictional character/game asset generation
- Anti-patterns list to prevent generic AI output
- Result: FF7 fan page output matches premium quality

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
- Copied Enterprise design (archon-v4) to frontend-v4/
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

## Phase 15.5 - Enterprise UI Polish (✅ Completed)
- Checkbox UX fix, Stats bar, Activity feed, Avg build time wired
- Publish and Download buttons wired to real endpoints
- Pipeline tab — full chat UI, /chat + /iterate endpoints, chat history, live output log
- Zap icon branding, i18n keys, New Project modal, "What Was Built" summary
- images_generated + files_generated counts from backend
- ArtifactsView Code tab — fixed height, independent scroll
- WelcomeBanner — live backend health check (green/red dot)
- Artifact cards navigate to Artifacts tab with sub-tab pre-selection
- Code tab scrollbars fixed, "Running" → "Building" rename
- Pipeline header status badges (colored pills)
- Agent pipeline status persists after reload from DB
- Search filter on Projects page, red dot pulse on offline indicator
- Pipeline tab scroll-to-top, no auto-scroll on initial load
- Pipeline state resets on project switch (no bleed)
- Chat messages persist via sessionStorage keyed by project ID
- JSON repair bug fixed — _repair_json strips fences, fixes bare backslashes
- Delete modal — type "DELETE" to confirm + shutil.rmtree disk cleanup
- Build Details card — tokens_used, estimated_cost, duration, model wired from DB

## Phase 15.6 — Frontend Cleanup & Tab Sync (🔧 In Progress Feb 2026)
- ✅ Wire Studio button in frontend-v4 navbar (opens Studio in same tab)
- ✅ Add Enterprise/Studio design switcher to frontend/ navbar
- ✅ Sync active tab between Enterprise and Studio on switch (URL query param approach)
- ✅ Remove deprecated frontend-consumer/ folder
- 🔴 Studio Tasks tab empty — wire real task data same way as frontend-v4
- 🔴 Minor Studio polish touches
- 🔴 Retire frontend-consumer2/ once consumer features confirmed complete (future)
- 🔴 Next.js → Vite migration for frontend/ (deferred to end of all phases)
