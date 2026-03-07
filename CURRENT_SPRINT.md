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

## Eval Loop System (eval/)

Automated design quality optimization pipeline:
- Build app, screenshot, score via Claude Vision, rewrite prompts, repeat
- Rollback logic prevents score regression
- Current best scores: Dashboard 82/100, Game 75/100, SaaS Landing 72/100

## Phase 20.1 — Visual Reference Input (🔧 Planned)

Attach images (screenshots, mockups, inspiration) to prompts so AI agents can reference them during builds.
Upload UI exists (Phase 7F.1) but pipeline currently ignores attachments.

- 🔴 Backend: Accept uploaded images via /iterate endpoint, store in project assets folder
- 🔴 Orchestrator: Pass reference_images list through pipeline context to all agents
- 🔴 Planner Agent: Use Gemini vision to describe reference images, include in plan context
- 🔴 Engineer Agent: Pass reference images as Gemini vision input, match style/layout/palette
- 🔴 Design Agent: Analyze reference images via Gemini vision to influence Imagen prompts
- 🔴 Frontend (all 3): Wire existing drag-and-drop to send files as multipart/form-data with build request
- 🔴 Chat UI: Show image thumbnails inline in conversation thread

## Up Next

| Phase | Description |
|-------|-------------|
| 18 | Unified Auth + Plan-Based UI Routing |
| 19 | Product Tour + Onboarding Walkthrough |
| 20.1 | Visual Reference Input — image attachments forwarded to pipeline agents |
