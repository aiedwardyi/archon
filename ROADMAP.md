# Archon â€” Execution Roadmap

## Purpose

Archon is a multi-agent platform that converts product ideas into auditable
web applications with full version history. Target market: digital agencies
and enterprises delivering client apps to non-technical clients.

**Core value proposition:**
- Every prompt creates a full artifact set: Brief + Plan + Code + live preview
- Complete version history â€” every decision is auditable and reversible
- Agencies can show clients exactly what was built and why, version by version
- Business language UI â€” no developer jargon anywhere

**The MOAT:** The Versions page. Lovable/v0 show current state only.
Archon shows complete decision history with artifacts and live preview per version.

---

## Target User

Non-technical agency owner or project lead who:
- Cannot read code â€” needs to SEE the app running
- Needs to show clients every decision made during development
- Needs business language, not developer jargon

**Competitive positioning:** "Build client apps with AI. Show them everything."

---

## Architecture
```
User Input (Chat Panel)
    â†“
Prompt History (context continuation)
    â†“
Requirements Agent (OpenAI GPT-4o) â†’ Brief artifact (versioned)
    â†“
Architecture Agent (Gemini)        â†’ Build Plan artifact (versioned)
    â†“
Build Agent (Claude Sonnet 4.5)    â†’ Code files (versioned)
    â†“
Execution Result â†’ Database + UI + Version Timeline + Live Preview
```

---

## Phased Execution Plan

### Phase 1â€“6.4 (âœ… Completed)
Core pipeline, schemas, multi-agent coordination, SQLite persistence,
enterprise UI (10 screens, light + dark mode, business language throughout).

### Phase 7A â€” Iterative Pipeline & Version History (âœ… Completed)
- Every prompt runs full pipeline â†’ versioned DB record
- Prompt history continuation across iterations
- /iterate, /restore, /versions endpoints
- sessionStorage caching, real log persistence per execution

### Phase 7B â€” Live Preview (âœ… Completed)
- Build Agent: Claude Sonnet 4.5 (primary), Gemini fallback
- Engineer prompt: self-contained HTML, 600-line limit, max_tokens 32000
- /api/preview/<project_id>/<version> serving generated HTML
- Live preview iframe in Versions + Artifacts pages
- Desktop/mobile viewport toggle working
- Agent card flash bug fixed

### Phase 7C â€” Stability & State Fixes (âœ… Completed)
- Pipeline state restores from DB on page refresh
- Build completion uses DB as ground truth (no silent "Building...")
- Prompt history persisted to sessionStorage across iterations
- Logs save by version number â€” Artifacts logs tab version-correct
- Pipeline polling restarts when navigating back to mid-run build
- Global block prevents concurrent project builds
- isRunningRef set synchronously to prevent missed COMPLETED signals

**Carried forward:**
- Artifacts occasionally shows wrong version when nav from Versions page
- Master log accumulation across versions (prep for chatbox)

---

### Phase 7D â€” UI Polish & Quick Wins (ðŸ”´ Current Sprint)

- 7D.1 Navbar: real project name + version (replace mock "checkout-service > v14")
- 7D.2 Projects table: add Project ID column
- 7D.3 Delete project + delete all projects
- 7D.4 Avatar dropdown (v0-style: email, dark mode, credits, sign out)
       + Upgrade/Feedback/Refer/Credits in navbar
- 7D.5 Versions page live preview height increase
- 7D.6 Verify + fix Artifacts version sync from Versions page nav

---

### Phase 7E â€” Output Quality (â¬œ Planned)

- Engineer prompt: default to dashboard/hero layouts, ban mascot SVGs
- Richer visual output â€” real UI patterns, not toy examples
- Design QA agent (optional 4th pipeline step)

---

### Phase 7F â€” Chatbox Upgrades (â¬œ Planned)

- File and media upload with drag-and-drop
- Agent reply for unsupported inputs (URLs, videos)
- Master log accumulation across versions (chatbox history foundation)
- Image upload â†’ agent uses as design reference

---

### Phase 8 â€” Client Deliverables (â¬œ Planned)

- PDF export of full build history (client audit trail)
- Client shareable read-only link
- White-label option (agency branding)

---

## Competitive Positioning

| Feature | Lovable/v0 | Archon |
|---------|-----------|--------|
| Context continuation | âœ… | âœ… |
| Full chain on every edit | âŒ | âœ… |
| Artifact trail per version | âŒ | âœ… |
| Restore previous version | âœ… | âœ… |
| Live preview | âœ… | âœ… |
| Version history with preview | âŒ | âœ… |
| Auditable Brief per iteration | âŒ | âœ… |
| File/media upload in chat | âœ… | ðŸš§ 7F |
| Client PDF export | âŒ | ðŸš§ 8 |
| Non-technical agency UI | âŒ | âœ… |

---

## Current State (Feb 2026)

- âœ… Three-agent pipeline (Requirements â†’ Architecture â†’ Build)
- âœ… Build Agent: Claude Sonnet 4.5 (primary), Gemini fallback
- âœ… Flask backend, SQLite, full persistence
- âœ… Enterprise UI â€” 10 screens, light + dark mode
- âœ… Iterative pipeline with full version history
- âœ… Live preview iframe (Versions + Artifacts pages)
- âœ… State bugs fixed (refresh, completion signal, prompt history)
- ðŸ”´ UI polish â€” navbar, Projects table, avatar dropdown (Phase 7D)
- â¬œ Output quality (Phase 7E)
- â¬œ Chatbox upgrades (Phase 7F)
- â¬œ Client deliverables (Phase 8)



