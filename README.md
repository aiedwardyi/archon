# Archon — AI Dev Team Platform

A multi-agent platform that converts product ideas into auditable web applications
with full version history. Built for digital agencies and enterprises delivering
client apps to non-technical clients.

**What makes Archon different:**
- Every prompt creates a full artifact set: Brief + Plan + Code + live preview
- Complete version history — every decision is auditable and reversible
- Agencies can show clients exactly what was built and why, version by version
- Business language UI — no developer jargon anywhere
- Korean/English language support

**The MOAT:** The Versions page. Competitors show current state only.
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
Design Agent (GPT-4o-mini + DALL-E) → Image assets (versioned, reused on iterations)
    ↓
Build Agent (Claude Sonnet 4.6)     → Code files (versioned)
    ↓
Execution Result → Database + UI + Version Timeline + Live Preview
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key
- Anthropic API key (Build Agent — Claude Sonnet 4.6)
- IBM Watson API keys (STT, TTS, NLU — optional, degrades gracefully)
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
cd ../frontend-consumer2
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
$env:WATSON_NLU_URL = "https://..."
$env:WATSON_NLU_APIKEY = "your_api_key"
```

### 3. Start the servers
```powershell
# Terminal 1 — Flask backend (port 5000)
.\venv\Scripts\Activate
python backend/app.py

# Terminal 2 — Enterprise frontend (port 3000)
cd frontend
npm run dev

# Terminal 3 — Consumer frontend (port 3002)
cd frontend-consumer2
npm run dev
```

### 4. Open the app
```
Enterprise UI:  http://localhost:3000
Consumer UI:    http://localhost:3002
```

---

## Frontends

| Frontend | Port | Description |
|----------|------|-------------|
| `frontend/` | 3000 | Enterprise UI — full admin dashboard, 10 screens, light + dark mode |
| `frontend-consumer2/` | 3002 | Consumer UI — chat-first interface, Versions page, Korean/English toggle |

Both connect to the same Flask backend on port 5000.

---

## Project Structure
```
ai-dev-team/
├── agents/
│   ├── pm_agent.py           # Requirements Agent (OpenAI GPT-4o-mini)
│   ├── planner_agent.py      # Architecture Agent (Gemini Flash)
│   ├── design_agent.py       # Design Agent (GPT-4o-mini + DALL-E 3)
│   ├── engineer_agent.py     # Build Agent (Claude Sonnet 4.6, Gemini fallback)
│   └── nlu_agent.py          # NLU Agent (IBM Watson — sentiment + keyword analysis)
├── backend/
│   ├── app.py                # Flask API (port 5000)
│   ├── models.py             # SQLAlchemy models (Project, Execution, User)
│   └── database.py           # DB init
├── frontend/                 # Enterprise UI (port 3000)
│   ├── components/
│   │   ├── pipeline-run.tsx
│   │   ├── artifact-viewer.tsx
│   │   ├── account-modals.tsx
│   │   └── navbar.tsx
│   └── pages/
│       ├── projects-page.tsx
│       ├── versions-page.tsx
│       └── artifacts-page.tsx
├── frontend-consumer2/       # Consumer UI (port 3002)
│   ├── pages/
│   │   ├── ProjectsPage.tsx  # Chat-first project creation
│   │   └── ProjectDetailPage.tsx  # Preview, Versions, Code, Brief, Logs
│   ├── i18n.ts               # Korean/English translations
│   └── services/
│       └── orchestrator.ts   # Backend API client
├── prompts/
│   └── engineer.txt          # Build Agent system prompt
├── schemas/
├── scripts/
│   └── safe_write.py         # Iteration scope enforcement
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
| GET | `/api/projects/:id/versions/:v/files` | Get code files for a version |
| GET | `/api/projects/:id/head` | Get active head version |
| POST | `/api/projects/:id/chat` | Send chat message (no build) |
| GET | `/api/projects/:id/chat-history` | Get persisted chat messages |
| POST | `/api/executions/:id/restore` | Restore version as active HEAD |
| GET | `/api/execution-status` | Poll live execution status |
| GET | `/api/preview/:project_id/:version` | Serve generated HTML preview |
| POST | `/api/projects/:id/versions/:v/publish` | Publish version to shareable URL |
| GET | `/api/prd` | Latest Brief artifact |
| GET | `/api/plan` | Latest Build Plan artifact |
| GET | `/api/code` | Latest execution result |
| GET | `/api/assets/:pid/:version/:file` | Serve design assets |
| POST | `/api/watson/stt` | Speech to text (IBM Watson) |
| POST | `/api/watson/tts` | Text to speech (IBM Watson) |
| POST | `/api/projects/:id/chat` | Chat + NLU pre-analysis (sentiment routing) |

---

## Key Features

| Feature | Description |
|---------|-------------|
| Versions Page (MOAT) | Timeline + split panel with live preview per version |
| Iteration Mode | Surgical edits with scope enforcement, ancestor chain walk |
| Design Assets | DALL-E 3 images, reused on iterations (no regeneration) |
| Archetype Lock | App type locked after v1, prevents unintended mutations |
| Korean/English | Full i18n support with KO/EN toggle in consumer UI |
| Chat Persistence | Messages saved to DB, survive refresh and machine changes |
| One-Click Publish | Shareable hosted URL for any version |
| Watson STT/TTS | Voice input and audio playback in enterprise UI |
| Watson NLU | Pre-pipeline sentiment analysis — frustrated users routed to chat, not build |

---

## Roadmap Summary

| Phase | Status | Description |
|-------|--------|-------------|
| 1–6.4 | ✅ | Core pipeline, UI, enterprise design |
| 7A-7H | ✅ | Iterative pipeline, live preview, stability, output quality, chatbox |
| 8.1 | ✅ | One-click publish |
| 10.1-10.2 | ✅ | Watson STT/TTS |
| 17.1 | ✅ | Watson NLU pre-pipeline analyzer |
| 10.4 | ✅ | App type lock (archetype guardrail) |
| 12.1 | ✅ | Domain personality upgrade |
| 13 | ✅ | Chat persistence + user model |
| 14 | ✅ | Iteration mode fixes |
| 15 | ✅ | Consumer frontend v2 |
| 8.3 | 🔴 | Client shareable read-only link |
| 8.2 | 🔴 | PDF export |

---

## License

Proprietary. All rights reserved.
