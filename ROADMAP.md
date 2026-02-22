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

### Phase 7E — Output Quality (✅ Completed)
- Design Agent built: GPT-4o-mini plans images → DALL-E 3 generates them
- Images downloaded to disk, served via /api/assets/<project_id>/<version>/<file>
- Design Agent skips image generation for dashboards/tools (cost saving)
- Keyword check uses PRD title + overview only to avoid false positives
- Engineer prompt: 10-shell layout intelligence system
- Engineer prompt: DESIGN ASSETS section forces asset usage in HTML
- JSON repair fix: backtick-wrapped hex colors stripped before parse
- Engineer agent no longer produces landing pages for dashboard prompts

---

### Phase 7D — UI Polish & Quick Wins (🟡 In Progress)

- ✅ 7D.1 Navbar: real project name + version (live from sessionStorage)
- ✅ 7D.2 Projects table: Project ID column added
- ✅ 7D.3 Delete project + delete all with type-to-confirm modal
- ✅ 7D.6 Artifacts + Navbar version sync fixed (custom event bus)
- 🔴 7D.4 Avatar dropdown (v0-style: email, dark mode, credits, sign out)
- 🔴 7D.5 Versions page live preview height increase

---

### Phase 7F — Chatbox Upgrades (🔴 Current Sprint)

- File and media upload with drag-and-drop
- Agent reply for unsupported inputs (URLs, videos)
- Master log accumulation across versions
- Image upload → agent uses as design reference

---

### Phase 7G — Output Quality v2 (🟡 In Progress)

- ✅ UI archetype lock: Planner classifies archetype, Engineer enforces as hard constraint
- ✅ ArchetypeRules typed model: layout_contract + content_contract
- ✅ layout_contract: deterministic geometry per archetype (all 10 archetypes)
- ✅ Two-file split: src/index.html (structure+JS) + src/style.css (design)
- 🔴 Preview inline CSS stitching (replace base tag with srcdoc approach)
- 🔴 CSS design seed: mandatory glow/glass/shimmer patterns in engineer.txt
- 🔴 Pipeline real-time update bug fix

---

### Phase 8 — Client Deliverables (⬜ Planned)

- PDF export of full build history (client audit trail)
- Client shareable read-only link
- White-label option (agency branding)

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
| File/media upload in chat | ✅ | 🚧 7F |
| Client PDF export | ❌ | 🚧 8 |
| Non-technical agency UI | ❌ | ✅ |

---

## Current State (Feb 2026)

- ✅ Four-agent pipeline (Requirements → Architecture → Design → Build)
- ✅ Build Agent: Claude Sonnet 4.5 (primary), Gemini fallback
- ✅ Flask backend, SQLite, full persistence
- ✅ Enterprise UI — 10 screens, light + dark mode
- ✅ Iterative pipeline with full version history
- ✅ Live preview iframe (Versions + Artifacts pages)
- ✅ State bugs fixed (refresh, completion signal, prompt history)
- ✅ Design Agent — DALL-E 3 images, locally served, smart skip for dashboards
- ✅ Engineer prompt — 10-shell layout intelligence, mandatory asset usage
- ✅ JSON repair — backtick hex color fix
- 🟡 UI polish — 7D.1-7D.3 + 7D.6 done; avatar dropdown + preview height remain (Phase 7D)
- ⬜ Chatbox upgrades (Phase 7F)
- ⬜ Client deliverables (Phase 8)



