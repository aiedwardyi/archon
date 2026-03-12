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
- ✅ Phase C: Auth + Seed Projects (Complete Mar 9, 2026)
- 🔴 Phase D: Add Versions page (moat feature)
- ✅ Phase E: Build Insights slide-up card (Complete Mar 9, 2026)
- 🔴 Phase F: Mobile polish pass
- ✅ Wire Restore Version in Enterprise + Studio (Complete Mar 9, 2026)

### Phase C: Auth + Seed Projects (✅ Complete Mar 9, 2026)

**Part 1: Consumer Auth (✅ Complete Mar 9, 2026)**
- Guest build flow, login/register pages, Sign Out, post-build register modal
- Google OAuth button, account claiming via POST /api/projects/<id>/claim
- Backend guest mode: unauthenticated project creation, linked to account on register

**Part 2: Seed Projects (✅ Complete Mar 9, 2026)**
- POST /api/seed endpoint — seeds 2 demo projects from peak-quality FF7 output (projects 71 + 38)
- Real Imagen-generated character art (Cloud, Tifa, Barret) committed to backend/seed_data/
- Seed A: "FF7 — Avalanche Archive" (project 71, scored 83/100, Outfit font, hero + character cards + world map)
- Seed B: "FF7 — Midgar Archives" (project 38, search/filter/grid-list views, character detail modals)
- Asset URL rewriting at seed time: /api/assets/{old_id}/1/ → /api/assets/{new_id}/1/
- Auto-seeds on first login when user has 0 projects — Consumer, Enterprise, Studio
- No pipeline runs, no API cost — static file copy from committed seed_data
- Regression test: backend/tests/test_seed_projects.py
- Verified across all 3 frontends with working previews + character art
- Seed projects are swappable: replace backend/seed_data/{folder}/ contents + update original_project_id

**Implementation status:**
1. ✅ Consumer auth pages + guest build flow
2. ✅ Backend: guest project creation + account linking
3. ✅ Seed project system (all 3 frontends)
4. 🔴 Enterprise + Studio: try-before-register flow (deferred — lower priority)

## Consumer UX Declutter Pass (Queued)

**Problem:** Project detail page is too dense. New users don't know where to look — conversation, preview, tabs, AND Build Insights card all compete for attention in one view.

**User feedback:** Eddie's friend took a while to understand what he was looking at. Too many words and elements crammed into one page.

**Root cause:** Two-column layout (conversation left + preview/insights right) tries to show everything simultaneously. No visual hierarchy telling the user what matters most.

**Possible fixes (decide during implementation):**
1. **Progressive disclosure:** Hide insights card by default, show a small "View build tips" button that expands it. Don't auto-show on page load.
2. **Tab the right panel:** Preview is its own tab view. Insights could live as a tab instead of stacking below preview.
3. **Collapse conversation by default:** After build completes, conversation is less important than preview. Auto-collapse or minimize the chat column.
4. **Full-width preview:** Make preview the hero of the page. Move conversation to a slide-out drawer or collapsible panel.
5. **Reduce text density:** Shorter insight suggestions, bigger score number, fewer labels.
6. **Mobile-first rethink:** Stack vertically — preview on top, tabs below, insights as expandable accordion.

**Priority:** High — first impressions matter for conversion. Do this before showing to more friends/beta users.

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

## Eval Loop Results (Mar 10, 2026)

### Overnight Run (5 iterations, all 5 archetypes)
Branch: eval/loops, commit 58f7fcc
- Auth blocker fixed in eval/api_client.py (JWT auto-register/login)
- Playwright permission issue resolved
- Manual kit improvements applied post-run to dashboard, game, saas_landing (.css + .txt)

| Archetype | Baseline (Mar 6) | Best (Mar 10) | Delta |
|-----------|-------------------|---------------|-------|
| Ecommerce | 87.0 | 88.5 | +1.5 |
| Game (FF8) | 83.2 | 84.5 | +1.3 |
| Portfolio | 81.8 | 83.5 | +1.7 |
| Dashboard | 79.0 | 81.0 | +2.0 |
| SaaS Landing | 78.2 | 76.0 | -2.2 |

Average: 82.7/100. Target: 90+.

### Score-Only Kit Test (commit 70f376d)
All archetypes dropped due to build variance (untouched archetypes also dropped 3-4 pts).
Dimension-level signal: Game interactivity 6→7, SaaS visual_hierarchy 7→8, layout 7→8.
Conclusion: Manual kit changes show targeted dimension improvements but prompt/kit tweaking alone has hit diminishing returns.

### Next lever: Watson Discovery feedback loop
Instead of prompt rewriting, feed actual high-scoring HTML/CSS as reference templates into the engineer agent. See Phase 23 below.

## Phase 23 — Watson Discovery Integration (✅ Complete Mar 10, 2026)

IBM Cloud Credit Usage ($200, expires in ~34 days)

### 23.1 — Expanded NLU (✅ Mar 10, 2026)
- ✅ Added ConceptsOptions + EntitiesOptions to NLU agent (agents/nlu_agent.py)
- ✅ New fields: concepts, entities, prompt_richness (rich/moderate/sparse)
- ✅ Richer NLU context passed to PM Agent classify_intent, Planner, and Design Agent
- ✅ Graceful fallback when credentials missing

### 23.2 — Watson Discovery Client + Best Builds Ingestion (✅ Mar 10, 2026)
- ✅ DiscoveryClient wrapper (utils/watson_discovery.py) — graceful fallback, lazy collection resolution, idempotent ingest
- ✅ Ingestion script (scripts/ingest_best_builds.py) — 5/5 best builds ingested
- ✅ Best builds: Ecommerce 88.5 (pid 163), Game 84.5 (161), Portfolio 83.5 (169), Dashboard 81.0 (155), SaaS Landing 76.0 (162)
- ✅ Query test confirmed all 5 archetypes retrievable

### 23.3 — Pipeline Integration + Eval Auto-Ingest (✅ Mar 10, 2026)
- ✅ EngineerAgent.run() accepts reference_code (dict) — injects Discovery HTML/CSS as reference context for initial builds only
- ✅ Pipeline queries Discovery before Engineer Agent runs, resolves archetype aliases via DESIGN_KIT_ALIASES
- ✅ Eval loop auto-ingests builds scoring >=85 into Discovery (lazy import, canonical archetype, non-fatal)
- ✅ Complete learning loop: build → score → if 85+, ingest → next build retrieves best reference

Branch: feat/watson-discovery (4 commits: 09dce26, da95bd8, 8b38ebe) → merged to main

## Phase 24 — Asset Reuse Library (✅ Complete Mar 10, 2026)

Eliminates broken images by filling missing `<img>` slots from a library of previously generated Imagen assets.

- ✅ 24.1 ImageAsset SQLite table + bulk ingestion script (scripts/ingest_image_library.py) + auto-ingest hook after Design Agent
- ✅ 24.2 Post-build missing image scanner + library lookup + file copy (utils/asset_filler.py)
- ✅ 24.3 Category detection: key-based heuristic (hero, product, character, lifestyle, collection, icon, pattern, abstract, other) + prompt text fallback
- 🔴 24.4 Admin UI (deferred)

Bulk ingestion: 872 images across 9 categories from 205 projects. Idempotent (0 on second run).

Branch: `feat/asset-reuse-library`

**New files:**
- backend/models.py (ImageAsset model)
- utils/image_asset_catalog.py (shared cataloging helper)
- scripts/ingest_image_library.py (bulk ingester)
- utils/asset_filler.py (post-build missing image scanner + filler)

**Modified:**
- backend/app.py (auto-catalog after Design Agent + fill_missing_assets after Engineer Agent)
- agents/design_agent.py (base64→PNG decode fix — Imagen API returns base64 string, not raw bytes)

**Critical bug found during testing:**
- Imagen 4 Ultra API returns image_bytes as base64-encoded string, not raw bytes
- All previously generated images on disk are base64 text files (broken in browser)
- Fix: design_agent.py detects `iVBOR` prefix and decodes before writing
- All future builds now produce valid PNG files
- Discovery/Image Catalog log messages removed from frontend Live Output (print-only now)

## Known Bugs

| Bug | Severity | Description |
|-----|----------|-------------|
| ~~AuthGuard token expiry~~ | ✅ Fixed Mar 10 | AuthGuard now validates token via /api/auth/me on mount. Clears stale tokens and redirects to /login on 401. Enterprise + Studio. Cross-origin handoff preserved. Commit d6b5d8d. |
| ~~Double NLU call~~ | ✅ Fixed Mar 10 | /chat returns nlu_result in response, frontend forwards to /iterate, /iterate skips re-analysis if present. Enterprise + Studio both patched. Commit d862863. |
| ~~Quality Recommendations missing~~ | ✅ Fixed Mar 10 | Restored Quality Recommendations section after Compliance in Governance tab (Enterprise + Studio). Added insights fetch with auth header, category icons, priority badges, empty state. Commit 48d27ed. |
| ~~Imagen images not rendering~~ | ✅ Fixed Mar 10 | Resilient asset resolver: checks current assets/, code/src/assets/, last_design_assets.json local_path, and prior version fallback. Preview rewriting normalizes relative asset URLs. Expanded asset route for nested paths + MIME detection. Commit 58a9f8f. |
| ~~Generated apps have no interactivity~~ | ✅ Fixed Mar 10 | Added JS interactivity requirements to engineer_core.txt (Zero Dead Buttons Policy) + planner.txt quality_target. Verified: filters, cart counter, nav scroll all working. Some footer anchors still missing targets. Commit 18f0ce0. |
| ~~Notification sound missing~~ | ✅ Fixed Mar 10 | AudioContext resume + pre-unlock on first user gesture. Transition-based triggers (RUNNING→COMPLETED/FAILED). Shared AudioContext via ref. Studio sound moved to global app-shell so chime plays from any page. Enterprise + Studio. Commits 61ab5b4, 1b10893. |
| PM Agent classify_intent flake | 🟡 Medium | Intermittent false negative: clear build prompts sometimes classified as unclear, returning "I'm not sure I understood that — could you rephrase?" Resubmitting the identical prompt succeeds. Observed on Enterprise Pipeline (Project #656, Mar 10). Same prompt worked on 2 other projects. Root cause likely in PM Agent classify_intent — GPT-4o occasionally misclassifies valid build prompts as ambiguous. Investigate: temperature setting, prompt length sensitivity, or NLU pre-analysis interfering with classification. Repro: "Build a pet adoption website with a hero banner showing happy rescued dogs, a grid of adoptable pet cards with photos and names, filter buttons for dogs cats and rabbits, an adoption application form, and a testimonials section with adopter stories". |
| ~~Testimonials text overlaps background image~~ | ✅ Fixed Mar 10 | Strengthened COMMON SCORE-KILLERS #14 in engineer_core.txt — explicitly requires solid/semi-transparent card backgrounds for text over images, calls out testimonials specifically, added dedicated Testimonials checklist item in QUALITY SELF-CHECK. Commit f429a15. |

## Pending Verification

| Feature | Branch | What to test |
|---------|--------|--------------|
| Smart image count from seed_rows | feat/smart-image-count (merged) | ✅ Verified Mar 11 — Flask log confirmed "targeting 7 images (seed_rows=6, image_item_count=5)". |
| Hide Asset Filler from Live Output | fix/hide-asset-filler-log (merged) | ✅ Verified Mar 11 — only in Flask terminal, not in Live Output panel. |
| Testimonial overlap prompt fix | fix/testimonial-overlap-prompt (merged) | ✅ Verified Mar 11 — semi-transparent cards over background photo, text readable. |

## fix/multi-bug-sprint (✅ Merged Mar 11, 2026)

5 fixes across backend + Enterprise + Studio frontends.

| Commit | Fix | Status |
|--------|-----|--------|
| bfd6910 | Discovery archetype mismatch — only inject reference if archetype matches engineer kit | ✅ Committed |
| 5ac7d09 | "Set as iteration base" UX — renamed Restore button, tooltip, Set ✓ confirmation flash, ↩ branched from vN label | ✅ Verified |
| 657d6c0 | Versions page auto-selects latest version when new build completes | ✅ Verified |
| 97fb517 | Notification sound regression — AudioContext pre-unlock, transition-based RUNNING→COMPLETED/FAILED trigger | ✅ Verified |
| 0b27cc2 | base.css copied forward on iteration builds — fixes CSS loss on v2+ previews | ✅ Verified (v3 fully styled) |

**Versioning strategy confirmed:** Restore to previous version + iterate = next sequential version number (v11, not v2a). Parent chain tracked via `parent_execution_id` in DB. Sidebar shows "↩ branched from vN" for non-sequential parents.

## Phase 22.G — Archetype Shimmer Skeleton (✅ Complete Mar 11, 2026)

During initial builds (no preview yet), the consumer preview panel now shows a fake browser window with shimmer skeleton blocks instead of an empty panel. The skeleton layout matches the detected archetype and updates live as the planner stage resolves `locked_ui_archetype`.

- ✅ `BuildSkeletonScreen` component in `ProjectDetailPage.tsx` — fake browser chrome (traffic-light dots, shimmer URL pill, stage status text) + archetype layout
- ✅ 5 archetype layouts: landing/saas_landing, dashboard, ecommerce, portfolio, game/default
- ✅ CSS shimmer keyframes injected via inline `<style>` — light + dark mode variants
- ✅ Stage text updates: pm → "Understanding your idea..." / planner → "Planning your layout..." / engineer → "Writing your code..."
- ✅ Skeleton disappears and iframe renders on build completion
- ✅ Iteration builds (v2+) never show skeleton — existing iframe continues
- ✅ Backend: `locked_ui_archetype` added to `/api/execution-status` response + `Project.to_dict()`
- ✅ Frontend: `uiArchetype` added to `Project` type, normalized in `orchestrator.ts`, updated live during polling
- ✅ Verified: dashboard build showed skeleton immediately, archetype layout matched, preview replaced skeleton on completion
- Branch: `feat/build-loading-cards`

**Known issues found during testing:**
- 🔴 Generated dashboard CSS has overlapping/broken text on bottom of page (pre-existing quality issue, unrelated to skeleton)
- 🔴 Build Insights returns 401 for guest users — insights endpoint needs optional-auth like preview endpoint

## Phase 22.H — Consumer V3 Animated Redesign (✅ Complete Mar 11, 2026)

Full animated reimagination of consumer frontend (port 3002). Three design branches created, v3 selected and merged to main.

- ✅ Animated gradient mesh background — 3 drifting orbs (indigo, violet, cyan), CSS @keyframes
- ✅ Headline gradient text shimmer animation (4s sweep)
- ✅ Inspiration cards with lift/glow hover animations (replaced suggestion pills)
- ✅ Prompt textarea glowing border pulse on focus
- ✅ Icon-only navigation rail on project detail (6 icons: Preview, Brief, Plan, Code, History, Versions)
- ✅ Neural network loading animation during builds (animated dots + lines)
- ✅ Version cards with scaled iframe thumbnails
- ✅ Live preview fills right panel as hero
- ✅ Sidebar: "WORLDS IN PROGRESS" branding, pulsing backend status dot, gradient Start Building button
- ✅ Branch: design/v3-reimagined → merged to main Mar 11

**Phase 22.I polish items (✅ Complete Mar 12, 2026):**
- ✅ Removed light/dark toggle from SettingsModal (dark-only app)
- ✅ SettingsModal redesigned to match v3 dark theme
- ✅ Language switch now applies instantly on Save (lang prop passed from App.tsx)
- ✅ Enter = submit prompt, Shift+Enter = newline (landing textarea)
- ✅ Menu/nav icon rail repositioned to not overlap chat panel
- ✅ Sign In button (top right) updated to dark glass style
- ✅ "Could not load" replaced with "Building..." message during active builds
- ✅ Tab switches and code file switches now scroll right panel to top
- ✅ Versions page: Restore button hidden when only 1 version or current version selected
- ✅ Recent projects on landing page now show live iframe preview thumbnails
- ✅ Sidebar project list now shows live iframe preview thumbnails
- ✅ Sign In / Register pages redesigned to match v3 dark theme
- ✅ Button hover animation lag fixed (backface-visibility, translateZ, scale reduced to 1.005)

**Phase 22.J — Remaining Polish (queued):**

Found during 22.I review. Next Codex task should address all of these:

1. **Google Sign-In button color** (`LoginPage.tsx`, `RegisterPage.tsx`)
   - The Google OAuth button currently renders with a dark olive/grey-green background color — looks wrong and unpolished
   - Should be: white background with Google logo + dark text (standard Google brand button style), OR match the v3 dark glass style: `border border-white/10 bg-white/[0.05] text-white` with the Google colored `G` logo inline SVG
   - File: wherever the Google sign-in button is rendered in `LoginPage.tsx` and `RegisterPage.tsx`

2. **Thumbnail height inconsistent with long project descriptions** (`ProjectsPage.tsx`, `Sidebar.tsx`)
   - Project cards that have longer description text push the thumbnail area taller/shorter because the description text bleeds into the thumbnail container height
   - The thumbnail iframe section should be a **fixed height** regardless of description length — `h-[140px]` on landing page cards, `h-[72px]` on sidebar cards — with `overflow-hidden` enforced
   - Description text should be clamped (`line-clamp-2`) and sit below the thumbnail in its own fixed-height info section, not affect thumbnail sizing
   - Check that the iframe thumbnail container uses `position: relative` + `overflow: hidden` with explicit `height` in px, not `min-height` or flexible sizing

3. **Thumbnail card edges look off** (`ProjectsPage.tsx`, `Sidebar.tsx`)
   - The rounded corners at the top of the thumbnail iframe don't perfectly match the card's outer rounded corners — there's a slight visual mismatch where the iframe bleeds past the rounded edge or the border radius doesn't line up
   - Fix: ensure the thumbnail container div has `rounded-t-[1.8rem] overflow-hidden` matching the card's outer `rounded-[1.8rem]`. The iframe inside should have no border-radius of its own.
   - On the sidebar, the thumbnail container should use `rounded-[1rem] overflow-hidden` to match the project card's inner radius
   - Also check: is there a visible gap or double-border between the thumbnail bottom edge and the info section? If so, remove the `border-b` from the thumbnail container or merge it with the card border

4. **Nav icon rail placement** (`ProjectDetailPage.tsx`)
   - The icon rail (Preview / Brief / Plan / Code / History / Versions buttons) is positioned between the chat panel and the preview panel but the positioning is still slightly awkward — it floats in an odd z-index layer and on some viewport widths it overlaps the left chat panel's right edge or sits too close to the preview content
   - Desired behavior: the rail should sit in the gap between the two panels, vertically centered, and never overlap either panel's content. It should only be visible on `lg:` breakpoints (hidden on mobile — mobile gets a bottom tab bar in Phase 22.F)
   - Consider: moving the rail to be `position: absolute` on the `<aside>` with `right-[-28px]` so it visually bridges the gap. Or embed it as a narrow column in the grid layout `lg:grid-cols-[260px_48px_minmax(0,1fr)]` so it has its own dedicated column and never overlaps
   - The rail icons should have smooth tooltip labels on hover (already implemented) — verify they still show correctly after repositioning

5. **Mobile layout** (`ProjectsPage.tsx`, `Sidebar.tsx`, `ProjectDetailPage.tsx`) — **Phase 22.F**
   - The entire consumer frontend is not mobile-optimized. This is a separate, significant task and should be done as its own Codex brief after 22.J is complete
   - Key issues:
     - Landing page: hero text too large, textarea cramped, inspiration cards overflow horizontally
     - Sidebar: doesn't open/close properly on mobile, overlaps content
     - Project detail page: two-column grid collapses badly — chat panel and preview panel stack awkwardly
     - Icon nav rail: completely broken on mobile — needs to become a bottom tab bar on small viewports
     - Thumbnail cards: may need to be single-column on mobile
   - Do NOT combine with 22.J — mobile is its own full-day task

**Deferred (bigger features, separate phases):**
- Credit/token system (Phase 25)
- Deploy to GitHub / one-click repo (Phase 26)
- Host on Archon server / "Publish" feature (Phase 27)

## Up Next

| Phase | Description |
|-------|-------------|
| ~~22.I~~ | ~~Consumer V3 Polish Pass~~ ✅ Mar 12 |
| ~~22.J~~ | ~~Consumer V3 Remaining Polish (Google button, thumbnails, nav rail)~~ ✅ Mar 12 |
| 22.K | Build Insights scroll UX — Insights as 7th nav rail tab (Lightbulb icon), removes need to scroll past preview |
| 22.D | Consumer Versions page (THE MOAT — timeline + preview + narrative) |
| 22.F | Consumer mobile polish pass |
| 25 | Credit / token system |
| 26 | GitHub deployment — one-click repo + auto-commit on iterate |
| 27 | Publish to Archon hosting — "Publish" button, hosted preview link |
| — | Fix Build Insights for guest users (insights endpoint → optional-auth) |
| — | Quality Regression Investigation (compare Feb 19-27 peak vs current) |
| 8.3 | Client shareable read-only links (primary moat feature) |
| 18 | Unified Auth + Plan-Based UI Routing |

## Eval Loop Dual-PC Workflow

See `docs/EVAL_WORKFLOW.md` for the full parallel eval loop process.

## Overnight Eval Run — Mar 11→12, 2026

**Result: Harness bug fixed, no winning changes committed.**

### What happened
- Loop started on `eval/loops`, ran partial `saas_landing` cycle
- Baseline scores: 75.0, 82.0, 56.0 — B-test: 75.0 (no improvement, reverted)
- Backend + operator process died overnight — loop stopped early
- After restart, loop resumed on `dashboard` archetype
- Dashboard baselines: 83.0, 77.0, 84.5 — then harness crash before edit
- Root cause: `eval/prompt_parser.py` expected a `dashboard` section in `prompts/engineer.txt` — only `SAAS LANDING PAGE` section exists there
- Loop restarted, ran 63.0 + 76.5 dashboard baselines, then stopped in morning

### Harness fix (Mar 12, 2026)
- ✅ Added `has_section()` to `eval/prompt_parser.py`
- ✅ `eval/operator_loop.py` now checks section exists before targeting `engineer.txt`
- ✅ Fallback: archetypes without engineer.txt sections (dashboard, ecommerce, portfolio, game) now edit kit files in `prompts/archetypes/` instead of crashing
- ✅ Defensive degradation: if engineer-section editing fails mid-cycle, loop falls back to kit editing instead of burning API budget on repeated crashes
- ✅ Verified: full baseline → edit → B-test cycle completed without crash
  - Dashboard baseline: 73.5 → B-test: 52.0 → **correctly reverted**
- ✅ `docs/EVAL_WORKFLOW.md` updated: mission is to improve designs, not observe failures. Operators must fix local blockers, treat API spend as optimization budget, avoid passive repeat-fail cycles

### New files from overnight stabilization (untracked)
- `scripts/launch_operator_loop.py`
- `scripts/operator_supervisor.py`
- `scripts/run_operator_loop_forever.cmd`

### Current scores (unchanged from Mar 10)
| Archetype | Best Score |
|-----------|------------|
| Ecommerce | 88.5 |
| Game (FF8) | 84.5 |
| Portfolio | 83.5 |
| Dashboard | 81.0 |
| SaaS Landing | 76.0 |

**Next eval run:** Harness is now stable. Loop can iterate and reject bad changes. Commit the harness fixes, then restart overnight loop targeting all 5 archetypes.



