# Current Sprint

## Completed Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 14 | Iteration Mode — scope enforcement, archetype lock, ancestor chain traversal | Done |
| 15 | Consumer Frontend v2 — Versions page, i18n, live preview | Done |
| 15.4 | Enterprise UI — Vite + React + shadcn/ui, 4-theme system, full API wiring | Done |
| 16.1 | Bug Fixes — chat persistence, JSON repair, build lock, agent state recovery | Done |
| 16.2 | Branding — hexagon logo + favicon across all 3 frontends | Done |
| 16.3 | Studio Feature Parity — sort, i18n, build details, Watson TTS | Done |
| 16.4 | Watson STT/TTS — Enterprise pipeline chat (mic + speaker) | Done |
| 16.5 | Authentication — JWT, Google OAuth, blacklist logout, concurrent pipeline | Done |
| 16.6 | Planner Archetype Expansion — 10 to 32 archetypes with layout/content contracts | Done |
| 17.1 | Watson NLU Pre-Pipeline — sentiment routing, keyword extraction | Done |
| 17.2 | Governance Agent — AI Factsheets, Watson NLU scoring, human review flag | Done |
| 17.3 | Dashboard Governance — Avg Prompt Score + Avg Build Score in header | Done |
| 17.4 | Dual PDF Export — Client PDF + Internal PDF from Governance tab | Done |
| 17.5 | Delivery Readiness Gate — Quality Tier badges (High/Good/Low) on Versions timeline | Done |
| 20.1 | Visual Reference Input — attach images to guide AI builds | Done |

## Eval Loop System (eval/)

Automated design quality optimization pipeline:
- Build app, screenshot, score via Claude Vision, rewrite prompts, repeat
- Rollback logic prevents score regression
- Current best scores: Dashboard 82/100, Game 75/100, SaaS Landing 72/100

## Phase 20.1 — Visual Reference Input (✅ Complete Mar 7, 2026)

Attach images (screenshots, mockups, inspiration) to prompts so AI agents can reference them during builds.

- ✅ Backend: /iterate accepts multipart/form-data, saves images to output/<pid>/v<ver>/references/
- ✅ Orchestrator: Passes reference_images list through pipeline context to all agents
- ✅ Planner Agent: Uses Gemini vision to describe reference images, includes in plan context
- ✅ Engineer Agent: Passes reference images as Gemini inline_data parts, matches style/layout/palette
- ✅ Design Agent: Analyzes reference images via Gemini vision before generating Imagen prompts
- ✅ Enterprise + Studio: Paperclip button, file input, thumbnail strip, FormData on send
- ✅ Chat UI: Image thumbnails rendered inline in sent messages (base64 data URLs)
- ✅ Fix: Replaced blob URLs with base64 data URLs so images survive sessionStorage round-trip
- Consumer frontend skipped (read-only, doesn't call /iterate)

## QA Visual Pass (✅ Complete Mar 8, 2026)

Full visual QA of Enterprise + Studio frontends. Two fix branches merged into feat/quality-target-tuning.

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | Version mismatch v0 (Enterprise) vs v1 (Studio) | 🔴 Critical | ✅ Fixed |
| 2 | Versions vs Artifacts state contradiction | 🔴 Critical | ✅ Fixed |
| 3 | "Good afternoon, Jane" hardcoded greeting | 🟡 Medium | ✅ Fixed |
| 4 | Enterprise Profile modal: Jane Doe hardcoded | 🟡 Medium | ✅ Fixed |
| 5 | Studio Profile modal: Jane Doe hardcoded | 🟡 Medium | ✅ Fixed |
| 6 | Deep link /versions returns 404 | 🟡 Medium | ✅ Fixed |
| 7 | Studio Artifacts blank (no empty state) | 🟡 Medium | ✅ Fixed |
| 8 | Enterprise Zap icon on Upgrade to Pro | 🟢 Low | ✅ Fixed |
| 9 | Studio Zap icon on Upgrade to Pro | 🟢 Low | ✅ Fixed |

Files changed: WelcomeBanner.tsx, ProfileModal.tsx, Navbar.tsx, account-modals.tsx, avatar-dropdown.tsx, project-dashboard.tsx, App.tsx, Index.tsx, ArtifactsView.tsx, artifacts/page.tsx

### Backend API QA (Codex, Mar 8, 2026)
- 14/17 tests passed
- ✅ GET /api/projects auth guard fixed (Mar 8, 2026) — all 5 optional-auth endpoints now require JWT
- 10/10 regression tests passing (backend/tests/test_auth_guard.py)
- Register 409 and credits/balance object format were false positives

### Additional QA Fixes (Mar 8, 2026)
- ✅ Removed 💬 emoji from Enterprise Pipeline "Conversation" heading (Index.tsx)
- ✅ Removed emoji from ForgotPassword.tsx (found by Codex repo-wide scan)

## Phase 21 — Build Insights (🔧 In Progress Mar 8, 2026)

- ✅ 21.1 Backend: InsightsAgent generates 2-4 actionable prompt suggestions (agents/insights_agent.py)
- ✅ 21.2 Backend: /api/projects/<id>/versions/<ver>/insights endpoint (app.py)
- ✅ 21.3 Enterprise UI: "Quality Recommendations" section in Governance tab (ArtifactsView.tsx)
- ✅ 21.4 Studio UI: Matching insights section in Governance tab (artifact-viewer.tsx)
- ✅ 21.5 i18n: 12 Korean translation keys added (i18n.ts)
- 🔴 Studio font regression: Geist Sans replaced by IBM Plex Sans during Phase 16.5 auth work — Codex fixing (globals.css, layout.tsx, project-dashboard.tsx)

## Light Mode Contrast Fixes (✅ Complete Mar 9, 2026)

### Enterprise (`fix/enterprise-lightmode-icons`)
- ✅ All hexagon icons changed from `text-primary`/`text-blue-500` → `text-blue-600 dark:text-blue-500`
- Files: Navbar.tsx, ProjectTable.tsx, PipelineStatus.tsx, Index.tsx (pipeline header + chat bubbles)
- Visually verified: Projects, Pipeline, Versions pages in both light + dark mode

### Studio (`fix/studio-lightmode-contrast`)
- ✅ Navbar hexagon → `text-blue-600 dark:text-blue-500`, hover bg → `hover:bg-accent`
- ✅ Project row hexagon → `text-blue-600 dark:text-blue-500`
- ✅ Versions panel selected state → `bg-primary/10` (was `bg-accent`)
- ✅ Darkened `--muted-foreground` from `oklch(0.45)` → `oklch(0.40)` for better text contrast
- Files: navbar.tsx, project-dashboard.tsx, version-timeline.tsx, globals.css
- Visually verified: Projects, Versions, navbar hover in light + dark mode

### Google OAuth origin fix
- ✅ Added `http://localhost:8080` to Google Cloud Console authorized origins + redirect URIs
- Enterprise Google Sign-In now works on port 8080

## Phase 22 — Consumer Frontend Overhaul (🔧 In Progress Mar 9, 2026)

### Phase A: Audit (✅ Complete Mar 9, 2026)
Full audit of `frontend-consumer/` by Codex. Key findings:

**Critical:**
- No authentication — never reads/writes `archon_token`, never sends Authorization headers. All project flows dead against JWT-protected backend
- "Ask for changes" composer is fake — submits only append local log, never calls `/iterate` or `/chat` backend APIs

**High:**
- Connection state mis-modeled — any non-OK fetch = "backend offline" overlay, even for auth errors
- API base hardcoded to `http://localhost:5000` with no env abstraction
- TypeScript health broken — `tsc --noEmit` fails extensively despite strict config
- Multiple no-op controls: Publish, Browse, Source, Pro Features, most Settings fields
- Developer-oriented IA/copy: dark mode default, "Next-Gen Multi-Agent Swarm", PRDs, Runtime Logs, Simulate Fault, Reasoning Engine, Vibe coding level

**Medium:**
- i18n partial — large sections hardcoded English despite KO/EN toggle
- Settings modal mostly fake (profile, password, model selection don't hit backend)
- Error/empty states misleading — failures collapse to "build in progress"
- Dead/duplicated code: LivePreview, ProjectCard, StageStepper, mock gemini.ts unused
- index.html drifted: Tailwind CDN, Google font CDN, importmap remnants, missing /index.css

**Feature gaps vs Enterprise/Studio:**
- Auth (blocks everything else)
- Versions page (THE MOAT — no dedicated route, no comparison narrative)
- Build Insights / Prompt Coach (backend exists, consumer missing)
- Credit balance display
- Voice input (Watson STT/TTS)
- Visual reference image attachments
- Governance / quality summaries

**Recommended approach:**
- Add: auth → versions page → build insights → credits chip
- Simplify: remove dev chrome (logs, fault injection, reasoning engine, vibe coding, fake settings)
- Simplify copy: rename to client language, default light mode, core flow = Describe → Build → Review → Revise
- Mobile-first: reduce sidebar weight, responsive project detail, collapsible tabs

### Phase B: Implementation (✅ Complete Mar 9, 2026)
Codex rewrote consumer as indie-maker AI app builder (Lovable/v0 positioning):
- ✅ Landing page: prompt-first hero, "What can I build for you?", founder-friendly suggestions (Landing Page, Portfolio Site, Dashboard, Online Store)
- ✅ Copy rewrite: removed all developer jargon (Multi-Agent Swarm, PRD, Architecture, Pipeline, Vibe coding, Reasoning Engine)
- ✅ API layer: auth headers via `archon_token`, configurable API base, real `/chat` + `/iterate` calls
- ✅ Fake composer fixed: now calls real backend chat/iterate APIs
- ✅ Connection state: only shows "Backend Offline" for network errors, not 401/403
- ✅ Settings modal: simplified to theme + language only
- ✅ Dead code removed: LivePreview, ProjectCard, StageStepper, gemini.ts
- ✅ index.html cleaned: removed CDN scripts, importmap, duplicate tags
- ✅ Recent projects grid below hero on landing page
- ✅ "Every version saved. Undo anything." differentiator copy
- ✅ Tabs renamed: Preview, Brief, Build Plan, Code, What changed, Versions

**Bugs found during live testing (✅ All fixed Mar 9, 2026):**
- ✅ Preview iframe auto-refreshes after build completes
- ✅ Brief tab loads real brief data
- ✅ Build Plan tab loads real plan data
- ✅ "What changed" tab loads real file data
- ✅ Brief/Plan data no longer swapped on second build
- ✅ Light mode defaults correctly
- ✅ Iteration produces properly styled preview

**Discovered during testing:**
- ✅ Consumer has working Restore Version button — Enterprise + Studio restore buttons are static/unwired. Wire them up as a follow-up task.

### Remaining phases:
- ✅ Phase B bug fixes (Complete Mar 9, 2026)
- 🔧 Phase C: "Try Before Register" auth flow + seed projects (In Progress)
- 🔴 Phase D: Add Versions page (moat feature)
- 🔧 Phase E: Build Insights slide-up card (In Progress)
- 🔴 Phase F: Mobile polish pass
- ✅ Wire Restore Version in Enterprise + Studio (Complete Mar 9, 2026)

### Phase C: "Try Before Register" + Seed Projects (🔧 In Progress Mar 9, 2026)

**Concept:** Let users experience a full build BEFORE being asked to register. Conversion funnel play — show value first, capture after.

**Consumer (frontend-consumer):**
- Guest build: user types prompt → app builds → preview shown → THEN modal: "Create a free account to save & iterate"
- Backend guest mode: unauthenticated project creation, linked to account on register
- Login + Register pages (light mode, minimal, indie-maker aesthetic)
- Google OAuth button
- After auth → stay on consumer (no redirect to Enterprise)

**Enterprise + Studio (frontend + frontend-studio):**
- Same try-before-register flow
- Seed projects: pre-built demo projects so new users see populated Projects page, can explore Versions/Artifacts/Preview
- Seed data created at register time (or on first login if empty)
- Seeds: 1-2 projects with 2-3 versions each, real brief/plan/code/preview artifacts

**Implementation order:**
1. Consumer auth pages + guest build flow (first)
2. Backend: guest project creation + account linking
3. Enterprise + Studio: seed project system
4. Enterprise + Studio: try-before-register flow

## Quality Regression Investigation (Queued)

**Goal:** Find the commit that produced peak design quality and identify what changed.

**Reference projects (peak output):**
| Project | ID | Created | Versions | Notes |
|---|---|---|---|---|
| Pokemon Site | 3 | Feb 19 | 2 | |
| Pokemon 2 | 9 | Feb 20 | 1 | |
| v2-pokemon | 20 | Feb 22 | 4 | |
| ff7-fanpage-v3 | 38 | Feb 23 | 3 | Character animations — best example |
| ff7 | 68 | Feb 27 | 2 | |
| ff7-v2 | 71 | Feb 27 | 2 | |
| build-details-test | TBD | ~Feb 27 | — | |

**What made them great:** Character art, Apple-like bubbly cards, animations, nice fonts.

**Peak quality window:** Feb 19–27, 2026.

**Investigation steps:**
1. `git log --oneline --after="2026-02-18" --before="2026-02-28"` — list all commits in peak window
2. Read `output/38/v1/code/src/index.html` (ff7-fanpage-v3 v1) — inspect the actual generated HTML/CSS
3. Read `output/71/v1/code/src/index.html` (ff7-v2 v1) — compare
4. Diff `prompts/engineer.txt` at peak commit vs current HEAD — find what changed
5. Diff `prompts/planner.txt` at peak commit vs current HEAD
6. Diff `agents/engineer_agent.py` at peak commit vs current HEAD
7. Check if design kit system (base.css) replaced the raw CSS generation that produced peak quality
8. Identify specific regressions and create a fix plan

**Key question:** Did the design kit CSS class assembly system lose the raw creative CSS generation that produced the Apple-like aesthetic?

## Up Next

| Phase | Description |
|-------|-------------|
| 22.B-F | Consumer frontend bug fixes, auth, versions, insights, mobile |
| — | Re-run eval after planner fix, decide merge of feat/quality-target-tuning |
| 8.3 | Client shareable read-only links (primary moat feature) |
| 18 | Unified Auth + Plan-Based UI Routing |
| 19 | Product Tour + Onboarding Walkthrough |



