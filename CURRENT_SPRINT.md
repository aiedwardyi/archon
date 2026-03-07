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

## Up Next

| Phase | Description |
|-------|-------------|
| 18 | Unified Auth + Plan-Based UI Routing |
| 19 | Product Tour + Onboarding Walkthrough |

