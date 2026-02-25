# Archon — AI Dev Team Platform

A multi-agent platform that converts product ideas into auditable web applications
with full version history. Built for digital agencies and enterprises delivering
client apps to non-technical clients.

**What makes Archon different from Lovable/v0:**
- Every prompt creates a full artifact set: Brief + Plan + Code + live preview
- Complete version history — every decision is auditable and reversible
- Agencies can show clients exactly what was built and why, version by version
- Business language UI — no developer jargon anywhere

**The MOAT:** The Versions page. Lovable/v0 show current state only.
Archon shows complete decision history with artifacts and live preview per version.

---

## Architecture
```
User Input (Chat Panel)
    ↓
Prompt History (context continuation)
    ↓
Requirements Agent (OpenAI GPT-4o)  → Brief artifact (versioned)
    ↓
Architecture Agent (Gemini)         → Build Plan artifact (versioned)
    ↓
Build Agent (Claude Sonnet 4.5)     → Code files (versioned)
    ↓
Execution Result → Database + UI + Version Timeline + Live Preview
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key
- Anthropic API key (Build Agent — Claude Sonnet 4.5)
- Google Gemini API key (fallback)

### 1. Clone and install
```powershell
git clone https://github.com/aiedwardyi/ai-dev-team
cd ai-dev-team

python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt

cd frontend
npm install
cd ..
```

### 2. Set API keys (each session)
```powershell
$env:OPENAI_API_KEY = "sk-proj-..."
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:GENAI_API_KEY = "your_gemini_key"
$env:WATSON_TTS_URL = "https://..."
$env:WATSON_TTS_APIKEY = "your_api_key"
$env:WATSON_STT_URL = "https://..."
$env:WATSON_STT_APIKEY = "your_api_key"
```

### 3. Checkout active branch
```powershell
git checkout enterprise-ui
```

### 4. Start the servers
```powershell
# Terminal 1 — Flask backend (port 5000)
.\venv\Scripts\Activate
python backend/app.py

# Terminal 2 — React frontend (port 3000)
cd frontend
npm run dev
```

### 5. Open the app
```
http://localhost:3000
```

---

## Branches

| Branch | Description |
|--------|-------------|
| `main` | Stable baseline (Phase 6.3) |
| `enterprise-ui` | **Active branch** — all current development |

---

## Project Structure
```
ai-dev-team/
├── agents/
│   ├── pm_agent.py           # Requirements Agent (OpenAI GPT-4o)
│   ├── planner_agent.py      # Architecture Agent (Gemini)
│   └── engineer_agent.py     # Build Agent (Claude Sonnet 4.5, Gemini fallback)
├── backend/
│   ├── app.py                # Flask API (port 5000)
│   ├── models.py             # SQLAlchemy models
│   └── database.py           # DB init
├── frontend/
│   ├── components/
│   │   ├── pipeline-run.tsx  # Agent cards + live logs + chat panel
│   │   ├── artifact-viewer.tsx
│   │   └── navbar.tsx
│   ├── pages/
│   │   ├── projects-page.tsx
│   │   ├── versions-page.tsx
│   │   └── artifacts-page.tsx
├── prompts/
│   └── engineer.txt          # Build Agent system prompt (600-line limit)
├── schemas/
├── scripts/
│   └── safe_write.py
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
| POST | `/api/projects/:id/iterate` | Run pipeline iteration |
| GET | `/api/projects/:id/versions` | Full version history |
| POST | `/api/executions/:id/restore` | Restore version as active HEAD |
| GET | `/api/execution-status` | Poll live execution status |
| GET | `/api/preview/:project_id/:version` | Serve generated HTML preview |
| GET | `/api/prd` | Latest Brief artifact |
| GET | `/api/plan` | Latest Build Plan artifact |
| GET | `/api/code` | Latest execution result |

---

## UI Screens

| Screen | Description |
|--------|-------------|
| Projects | Table with status, versions, last run, Project ID |
| Pipeline | Agent cards + live logs + iterative chat panel |
| Versions | Timeline + detail panel with prompt + artifacts + live preview |
| Artifacts / Brief | Requirements + success criteria |
| Artifacts / Plan | Architecture overview + file list |
| Artifacts / Code | File tree + code viewer |
| Artifacts / Tasks | Build task list |
| Artifacts / Logs | Plain English pipeline log |
| Artifacts / Preview | Live iframe, desktop/mobile toggle |

---

## Roadmap Summary

| Phase | Status | Description |
|-------|--------|-------------|
| 1–6.4 | ✅ | Core pipeline, UI, enterprise design |
| 7A | ✅ | Iterative pipeline, version history |
| 7B | ✅ | Live preview iframe, Claude Build Agent |
| 7C | 🔴 | Stability bugs + UI polish (current) |
| 7D | ⬜ | Output quality — Lovable parity |
| 7E | ⬜ | Chatbox file upload + agent replies |
| 8 | ⬜ | Client deliverables — PDF, sharing |

---

## License

Proprietary. All rights reserved.
