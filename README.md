# Archon — AI-Powered Development Platform for Agencies

Archon helps digital agencies and development shops build client web applications
faster — with a complete, auditable record of every decision made.

Describe what you want to build. Archon runs a full AI pipeline and generates
a runnable web app. Iterate with follow-up prompts. Every version is preserved,
inspectable, and restorable. Show clients exactly what was built and why.

---

## Why Archon

**The agency problem:** Clients ask "why did you build it this way?" or
"can we go back to the previous version?" Agencies have no good answer.

**The Archon answer:** Every prompt, every iteration, every generated file
is stored as a versioned snapshot. Walk clients through the complete build
history. Restore any previous version in one click.

| Feature | Lovable/Bolt | Archon |
|---------|-------------|--------|
| AI code generation | ✅ | ✅ |
| Context continuation | ✅ | ✅ |
| Full pipeline on every edit | ❌ | ✅ |
| Artifact trail per version | ❌ | ✅ |
| Restore previous version | ✅ | ✅ |
| Restore forward after revert | ❌ | ✅ |
| Client-exportable build history | ❌ | ✅ |

---

## How It Works
```
Agency types: "Build a restaurant booking website"
    ↓
PM Agent (OpenAI)      → Requirements document (v1)
    ↓
Planner Agent (Gemini) → Architecture plan (v1)
    ↓
Engineer Agent (Gemini)→ Complete web application (v1)
    ↓
Agency iterates: "Add online payments with Stripe"
    ↓
Full pipeline re-runs  → New complete snapshot (v2)
    ↓
Every version preserved, restorable, client-presentable
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
│   ├── pm_agent.py           # PM Agent (OpenAI) — generates requirements
│   ├── planner_agent.py      # Planner Agent (Gemini) — generates architecture
│   └── engineer_agent.py     # Engineer Agent (Gemini) — generates code
├── backend/
│   ├── app.py                # Flask API (port 5000)
│   ├── models.py             # SQLAlchemy models
│   └── database.py           # DB init and session
├── frontend/                 # React + TypeScript + Vite (port 3000)
│   ├── components/
│   ├── pages/
│   └── services/
├── prompts/
│   └── engineer.txt          # Engineer agent system prompt
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
| GET | `/api/prd` | Get latest PRD artifact |
| GET | `/api/plan` | Get latest plan artifact |
| GET | `/api/code` | Get latest execution result |

---

## Design Principles

- **Full pipeline on every iteration** — no patching, always re-run from scratch
- **Complete version snapshots** — every run produces independent artifacts
- **Client accountability** — every decision traceable and presentable
- **Determinism** — identical inputs produce identical outputs
- **Observable state** — all artifacts written as inspectable files
- **Failure visibility** — errors surface as artifacts, not silent failures

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 1–5 | ✅ Complete | Core pipeline, schemas, multi-agent coordination |
| 6.1 | ✅ Complete | SQLite persistence, project management |
| 6.2 | ✅ Complete | Polished React UI, full backend wiring |
| 6.3 | ✅ Complete | Differentiator features, audit trail UI |
| 7A | 🚧 Next | Iterative pipeline, version history, enterprise UI redesign |
| 7B | ⬜ Planned | Live iframe preview of generated apps |
| 7C | ⬜ Planned | PDF export, version diff viewer, shareable client links |

---

## License

Proprietary. All rights reserved.
