# Archon — AI Dev Team Platform

A deterministic multi-agent platform that converts product ideas into structured,
auditable web applications. Designed for digital agencies delivering client apps
to non-technical clients.

**What makes Archon different from Lovable/Bolt:**
- Full pipeline re-run on every iteration (not patching)
- Every artifact versioned and inspectable across all iterations
- Complete audit trail — every prompt, decision, and agent output
- Client-presentable version history with restore
- Business language UI — non-technical users understand every screen
- Schema-validated at every boundary

---

## Architecture
```
User Input (Chat Panel)
    ↓
Prompt History (context continuation)
    ↓
Requirements Agent (OpenAI GPT-4)  → Brief artifact (versioned)
    ↓
Architecture Agent (Gemini)        → Build Plan artifact (versioned)
    ↓
Build Agent (Gemini)               → Code files (versioned)
    ↓
Execution Result → Database + UI + Version Timeline
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key
- Google Gemini API key

### 1. Clone and install
```powershell
git clone https://github.com/aiedwardyi/ai-dev-team
cd ai-dev-team

# Python dependencies
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Set API keys (each session)
```powershell
$env:OPENAI_API_KEY = "sk-proj-..."
$env:GENAI_API_KEY = "your_gemini_key"
```

### 3. Start the servers
```powershell
# Terminal 1 — Flask backend (port 5000)
.\venv\Scripts\Activate
python backend/app.py

# Terminal 2 — React frontend (port 3000)
cd frontend
npm run dev
```

### 4. Open the app
```
http://localhost:3000
```

---

## Project Structure
```
ai-dev-team/
├── agents/
│   ├── pm_agent.py           # Requirements Agent (OpenAI) — generates Briefs
│   ├── planner_agent.py      # Architecture Agent (Gemini) — generates Build Plans
│   └── engineer_agent.py     # Build Agent (Gemini) — generates code
├── backend/
│   ├── app.py                # Flask API (port 5000)
│   ├── models.py             # SQLAlchemy models
│   └── database.py           # DB init and session
├── frontend/                 # React + TypeScript + Vite (port 3000)
│   ├── components/
│   │   ├── ArtifactViewer.tsx
│   │   ├── ChatPanel.tsx
│   │   └── Sidebar.tsx
│   ├── pages/
│   │   ├── ProjectsPage.tsx
│   │   ├── ProjectDetailPage.tsx
│   │   └── VersionsPage.tsx
│   └── services/
│       └── orchestrator.ts
├── prompts/
│   └── engineer.txt          # Build Agent system prompt
├── schemas/                  # JSON schemas for artifact validation
├── scripts/
│   └── safe_write.py         # Allowlisted file write guard
├── ROADMAP.md
└── CURRENT_SPRINT.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/projects` | List all projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/:id` | Get project + executions |
| DELETE | `/api/projects/:id` | Delete project |
| POST | `/api/execute-task` | Run full pipeline |
| GET | `/api/execution-status` | Poll execution status |
| GET | `/api/prd` | Get latest Brief artifact |
| GET | `/api/plan` | Get latest Build Plan artifact |
| GET | `/api/code` | Get latest execution result |
| POST | `/api/projects/:id/iterate` | Run pipeline iteration (new version) |
| POST | `/api/executions/:id/restore` | Restore version as active HEAD |
| GET | `/api/projects/:id/versions` | Get full version history |

---

## Agent Artifacts

Every pipeline run produces three artifacts with full agent sequence tracking:

| Artifact | Producer | Contains |
|----------|----------|----------|
| `brief.json` | Requirements Agent | User stories, success criteria |
| `plan.json` | Architecture Agent | Modules, build tasks, dependencies |
| `execution_result.json` | Build Agent | Generated code files, write records |

---

## UI Screens

| Screen | Description |
|--------|-------------|
| Projects | Table of all projects with status, versions, last run |
| Pipeline | Agent cards (Requirements → Architecture → Build) + live log |
| Versions | Left timeline + right detail panel with prompt + artifacts |
| Brief | What We're Building + Success Criteria |
| Build Plan | Module cards with dependencies |
| Code | VS Code-style file tree + code panel |
| Build Tasks | Task list with T-IDs |
| Logs | Plain English build log |
| Preview | Live iframe with desktop/mobile toggle |

---

## Design Principles

- **Determinism first** — identical inputs produce identical artifacts
- **Explicit contracts** — JSON schemas at every agent boundary
- **Observable state** — all artifacts written as inspectable files
- **Failure visibility** — errors surface as artifacts, not silent failures
- **Full audit trail** — every execution traceable end-to-end
- **Business language** — non-technical agency owners understand every screen

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 1–5 | ✅ Complete | Core pipeline, schemas, multi-agent coordination |
| 6.1 | ✅ Complete | SQLite persistence, project management |
| 6.2 | ✅ Complete | Polished React UI, full backend wiring |
| 6.3 | ✅ Complete | Differentiator features, VS Code explorer, audit trail UI |
| 6.4 | ✅ Complete | Enterprise UI design — 10 screens, light + dark mode |
| 7A | 🚧 Next | Iterative pipeline, version history, enterprise UI rebuild |
| 7B | 🔴 Priority | Live iframe preview (desktop + mobile toggle) |
| 7C | ⬜ Planned | Client deliverables — PDF export, shareable links |

---

## License

Proprietary. All rights reserved.
