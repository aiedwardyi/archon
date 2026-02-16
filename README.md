# Archon — AI Dev Team Platform

A deterministic multi-agent platform that converts product ideas into structured,
auditable code. Describe what you want to build — Archon runs a full PM → Planner
→ Engineer pipeline and generates code with a complete artifact trail.

**What makes Archon different from Lovable/Bolt:**
- Full pipeline re-run on every iteration (not patching)
- Every artifact versioned and inspectable
- Agent chain visible on every output
- Schema-validated at every boundary
- Deterministic: same input = same output

---

## Architecture
```
User Input
    ↓
PM Agent (OpenAI GPT-4)     → PRD artifact
    ↓
Planner Agent (Gemini)      → Plan artifact (milestones + tasks)
    ↓
Engineer Agent (Gemini)     → Code files
    ↓
Execution Result            → Database + UI
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
│   ├── pm_agent.py           # PM Agent (OpenAI) — generates PRDs
│   ├── planner_agent.py      # Planner Agent (Gemini) — generates plans
│   └── engineer_agent.py     # Engineer Agent (Gemini) — generates code
├── backend/
│   ├── app.py                # Flask API (port 5000)
│   ├── models.py             # SQLAlchemy models
│   └── database.py           # DB init and session
├── frontend/                 # React + TypeScript + Vite (port 3000)
│   ├── components/
│   │   ├── ArtifactViewer.tsx
│   │   └── Sidebar.tsx
│   ├── pages/
│   │   ├── ProjectDetailPage.tsx
│   │   └── ProjectsPage.tsx
│   └── services/
│       └── orchestrator.ts
├── prompts/
│   └── engineer.txt          # Engineer agent system prompt
├── schemas/                  # JSON schemas for artifact validation
├── scripts/
│   └── safe_write.py         # Allowlisted file write guard
├── apps/offline-vite-react/
│   └── public/               # Runtime artifact storage (gitignored)
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
| GET | `/api/prd` | Get latest PRD artifact |
| GET | `/api/plan` | Get latest plan artifact |
| GET | `/api/code` | Get latest execution result |

---

## Agent Artifacts

Every pipeline run produces three artifacts with full agent sequence tracking:
```json
{
  "_agent_sequence": ["pm", "planner", "engineer"]
}
```

| Artifact | Producer | Contains |
|----------|----------|----------|
| `last_prd.json` | PM Agent | Requirements, goals, features, tech stack |
| `last_plan.json` | Planner Agent | Milestones, tasks, execution hints |
| `last_execution_result.json` | Engineer Agent | Generated code files, write records |

---

## Design Principles

- **Determinism first** — identical inputs produce identical artifacts
- **Explicit contracts** — JSON schemas at every agent boundary
- **Observable state** — all artifacts written as inspectable files
- **Failure visibility** — errors surface as artifacts, not silent failures
- **Full audit trail** — every execution traceable end-to-end

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 1–5 | ✅ Complete | Core pipeline, schemas, multi-agent coordination |
| 6.1 | ✅ Complete | SQLite persistence, project management |
| 6.2 | ✅ Complete | Polished React UI, full backend wiring |
| 6.3 | ✅ Complete | Differentiator features, VS Code explorer, audit trail UI |
| 7A | 🚧 Next | Iterative pipeline, version history, context continuation |
| 7B | ⬜ Planned | Live iframe preview of generated apps |

---

## License

Proprietary. All rights reserved.
