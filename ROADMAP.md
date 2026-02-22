# Archon — Execution Roadmap

## Purpose

Archon is a multi-agent platform that converts product ideas into
auditable web applications with full version history. Target market:
digital agencies and enterprises delivering client apps to non-technical clients.

**Core value proposition:**
- AI builds client apps with full pipeline transparency
- Every prompt creates a complete artifact set (Brief + Plan + Code) + live preview
- Complete version history — every decision is auditable and reversible
- Business language UI — non-technical users understand every screen
- Agencies can show clients exactly what was built and why

**Competitive MOAT:** The Versions page.
Every prompt creates Brief + Plan + Code artifacts + live preview per version.
Lovable/v0 show current state only. Archon shows complete decision history.
This is what agencies need for client accountability.

---

## Target User

Non-technical agency owner or project lead who:
- Cannot read code — needs to SEE the app running
- Needs to show clients every decision made during development
- Needs business language, not developer jargon

**Competitive positioning:** "Build client apps with AI. Show them everything."

---

## High-Level Architecture
```
User Input (Chat Panel)
    ↓
Prompt History (context continuation)
    ↓
Requirements Agent (OpenAI GPT-4o) → Brief artifact (versioned)
    ↓
Architecture Agent (Gemini)        → Build Plan artifact (versioned)
    ↓
Build Agent (Claude Sonnet 4.5)    → Code files (versioned)
    ↓
Execution Result → Database + UI + Version Timeline + Live Preview
```

**Key principle:** Every prompt runs the full pipeline and creates a versioned
snapshot. Every version has Brief + Plan + Code + live preview. Full audit trail.

---

## Design Principles

- **Audit trail first** — every version is inspectable, every decision is traceable
- **Explicit contracts** — JSON schemas at every agent boundary
- **Observable state** — all artifacts written as inspectable files
- **Failure visibility** — errors surface as artifacts, not silent failures
- **Business language** — non-technical users understand every screen
- **Lovable-quality output** — generated apps are visually polished and functional

---

## Phased Execution Plan

### Phase 1–5 (✅ Completed)
Core pipeline, schema validation, multi-agent coordination, Flask backend,
SQLite persistence, project management, React UI, agent observability.

### Phase 6.1–6.3 (✅ Completed)
SQLite + SQLAlchemy ORM, polished React UI, VS Code-style file explorer,
agent chain badges, Raw Data toggle, differentiator features.

### Phase 6.4 — Enterprise UI Design (✅ Completed)
Full enterprise UI redesign (Linear/Vercel aesthetic), light + dark mode,
business language throughout, 10 screens approved and built.

### Phase 7A — Iterative Pipeline & Version History (✅ Completed)
- Iterative pipeline: every prompt → full PM → Planner → Engineer chain
- Versioned executions stored in DB with prompt history continuation
- /iterate, /restore, /versions endpoints
- sessionStorage caching for instant nav-back
- Real log persistence keyed by execution ID
- Versions page: timeline + detail panel + restore

### Phase 7B — Live Preview (✅ Completed)
- Engineer agent switched to Claude Sonnet 4.5 (primary)
- Engineer prompt: self-contained HTML output, 600-line limit
- /api/preview/<project_id>/<version> backend route
- Live preview iframe wired in Versions page + Artifacts page
- Desktop/mobile viewport toggle
- Agent card flash bug fixed

---

### Phase 7C — Stability & Polish (🔴 Current Sprint)

**Goal:** Fix critical state bugs, polish UI, improve reliability.

**Critical bugs:**
- 7C.1 Pipeline state lost on refresh — no DB fallback when sessionStorage misses
- 7C.2 Silent build complete — Build Agent stays "Building..." after finish;
  Artifacts page shows wrong version until manual nav
- 7C.3 3rd+ prompt iteration context loss — engineer erases previous site,
  prompt history not feeding correctly into Build Agent

**UI polish:**
- 7C.4 Navbar shows mock "checkout-service > v14" → real project name + version
- 7C.5 Add Project ID column to Projects table
- 7C.6 Delete project + delete all projects
- 7C.7 Avatar dropdown (v0-style: email, dark mode, credits, sign out)
  + Upgrade/Feedback/Refer/Credits in navbar
- 7C.8 Versions page live preview height too small

---

### Phase 7D — Output Quality (⬜ Planned)

**Goal:** Lovable/v0 parity on generated app quality.

- Engineer prompt: default to faux dashboard hero, ban mascot SVGs
- Improve visual polish of generated output
- Multi-file output support (CSS/JS separation where needed)
- Design QA agent (optional 4th step for CSS polish)

---

### Phase 7E — Chatbox Upgrades (⬜ Planned)

**Goal:** Match Lovable/v0 chatbox UX.

- File and media upload (drag-and-drop support)
- Agent reply for unsupported inputs (URLs, videos):
  "I can't access that URL — describe what you'd like and I'll build it"
- Image upload → agent uses as design reference

---

### Phase 8 — Client Deliverables (⬜ Planned)

- PDF export of full build history (audit trail for client presentations)
- Client shareable read-only link
- White-label option (agency branding)
- Project handoff export

---

## Competitive Positioning

| Feature | Lovable/v0 | Archon |
|---------|-----------|--------|
| Context continuation | ✅ | ✅ |
| Full chain on every edit | ❌ | ✅ |
| Artifact trail per version | ❌ | ✅ |
| Restore previous version | ✅ | ✅ |
| Auditable Brief per iteration | ❌ | ✅ |
| Agent chain visibility | ❌ | ✅ |
| Live preview | ✅ | ✅ |
| Version history with preview | ❌ | ✅ |
| File/media upload in chat | ✅ | 🚧 7E |
| Client PDF export | ❌ | 🚧 8 |
| Non-technical agency UI | ❌ | ✅ |

---

## Current State (Feb 2026)

- ✅ Three-agent pipeline (Requirements/Architecture/Build)
- ✅ Build Agent: Claude Sonnet 4.5 (primary), Gemini fallback
- ✅ Flask backend, SQLite, full persistence
- ✅ Enterprise UI — 10 screens, light + dark mode
- ✅ Iterative pipeline with full version history
- ✅ Live preview iframe wired (Versions + Artifacts pages)
- ✅ Agent card real-time updates working
- 🔴 State bugs: refresh clears pipeline, silent build complete, context loss on 3rd prompt
- ⬜ Output quality improvements (Phase 7D)
- ⬜ Chatbox file upload + agent replies (Phase 7E)
- ⬜ Client deliverables — PDF, sharing (Phase 8)

---

## Non-Goals

- Fully autonomous unsupervised code deployment
- Hidden state or implicit agent behavior
- Targeting developers (Archon is for non-technical agency owners)
