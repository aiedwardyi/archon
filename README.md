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
- IBM Watson governance — every build is scored, audited, and factsheet-certified

**The MOAT:** The Versions page. Competitors show current state only.
Archon shows complete decision history with artifacts and live preview per version.

---

## Architecture
```
User Input (Chat Panel)
    ↓
Watson NLU Pre-Analyzer (IBM Watson NLU — sentiment routing, keyword extraction)
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
Governance Agent (IBM Watson NLU)   → AI Factsheet (scored, versioned, exportable)
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
cd ../frontend-v4
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

# Terminal 2 — Studio UI (port 3000)
cd frontend
npm run dev

# Terminal 3 — Consumer UI (port 3002)
cd frontend-consumer2
npm run dev

# Terminal 4 — Enterprise UI (port 8080)
cd frontend-v4
npm run dev
```

### 4. Open the app
```
Studio UI:      http://localhost:3000
Consumer UI:    http://localhost:3002
Enterprise UI:  http://localhost:8080
```

---

## Frontends

| Frontend | Port | Description |
|----------|------|-------------|
| `frontend/` | 3000 | Studio UI — full admin dashboard, 10 screens, light + dark mode |
| `frontend-consumer2/` | 3002 | Consumer UI — chat-first interface, Versions page, Korean/English toggle |
| `frontend-v4/` | 8080 | Enterprise UI — Vite + React + shadcn/ui, 4-theme system, governance dashboard |

All three connect to the same Flask backend on port 5000.

---

## Project Structure
```
ai-dev-team/
├── agents/
│   ├── pm_agent.py           # Requirements Agent (OpenAI GPT-4o-mini)
│   ├── planner_agent.py      # Architecture Agent (Gemini Flash)
│   ├── design_agent.py       # Design Agent (GPT-4o-mini + DALL-E 3)
│   ├── engineer_agent.py     # Build Agent (Claude Sonnet 4.6, Gemini fallback)
│   ├── nlu_agent.py          # NLU Agent (IBM Watson — sentiment + keyword analysis)
│   └── governance_agent.py   # Governance Agent (IBM Watson NLU — AI Factsheets + scoring)
├── backend/
│   ├── app.py                # Flask API (port 5000)
│   ├── models.py             # SQLAlchemy models (Project, Execution, User)
│   └── database.py           # DB init
├── frontend/                 # Studio UI (port 3000)
│   ├── components/
│   └── pages/
├── frontend-consumer2/       # Consumer UI (port 3002)
│   ├── pages/
│   ├── i18n.ts               # Korean/English translations
│   └── services/
│       └── orchestrator.ts   # Backend API client
├── frontend-v4/              # Enterprise UI (port 8080)
│   ├── src/
│   │   ├── components/
│   │   │   ├── WelcomeBanner.tsx    # Dashboard header — Avg Prompt/Build scores
│   │   │   ├── ArtifactsView.tsx    # Governance sub-tab + Factsheet viewer
│   │   │   └── BuildDetailsCard.tsx # Per-build stats (credits, model, duration)
│   │   └── pages/
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
| GET | `/api/projects/:id/versions/:v/factsheet` | Get AI Factsheet for a version |
| GET | `/api/projects/:id/head` | Get active head version |
| POST | `/api/projects/:id/chat` | Send chat message (NLU pre-analysis + routing) |
| GET | `/api/projects/:id/chat-history` | Get persisted chat messages |
| POST | `/api/executions/:id/restore` | Restore version as active HEAD |
| GET | `/api/execution-status` | Poll live execution status |
| GET | `/api/preview/:project_id/:version` | Serve generated HTML preview |
| POST | `/api/projects/:id/versions/:v/publish` | Publish version to shareable URL |
| GET | `/api/dashboard/stats` | Avg prompt + build scores across all executions |
| GET | `/api/credits/balance` | Current credit balance |
| GET | `/api/prd` | Latest Brief artifact |
| GET | `/api/plan` | Latest Build Plan artifact |
| GET | `/api/code` | Latest execution result |
| GET | `/api/assets/:pid/:version/:file` | Serve design assets |
| POST | `/api/watson/stt` | Speech to text (IBM Watson) |
| POST | `/api/watson/tts` | Text to speech (IBM Watson) |

---

## Key Features

| Feature | Description |
|---------|-------------|
| Versions Page (MOAT) | Timeline + split panel with live preview per version |
| Iteration Mode | Surgical edits with scope enforcement, ancestor chain walk |
| Design Assets | DALL-E 3 images, reused on iterations (no regeneration) |
| Archetype Lock | App type locked after v1, prevents unintended mutations |
| Korean/English | Full i18n support with KO/EN toggle across all UIs |
| Chat Persistence | Messages saved to DB, survive refresh and machine changes |
| One-Click Publish | Shareable hosted URL for any version |
| Watson STT/TTS | Voice input and audio playback in enterprise UI |
| Watson NLU | Pre-pipeline sentiment analysis — frustrated users routed to chat, not build |
| Credit System | 1 credit = 2,500 tokens, usage shown per build and in navbar |
| **AI Factsheets** | **Governance Agent scores every build (prompt quality + build confidence, 0–100)** |
| **Model Registry** | **Factsheet logs every AI model used per version: OpenAI, Anthropic, Gemini, IBM Watson** |
| **Human Review Flag** | **Auto-triggers when prompt or build score < 50** |
| **Dashboard Governance** | **Enterprise header shows live Avg Prompt Score and Avg Build Score across all builds** |

---

## IBM Watson Governance

Archon includes an enterprise-grade AI governance layer powered by IBM Watson NLU.

**How it works:**
1. Every successful build triggers the Governance Agent automatically
2. Watson NLU analyzes the original user prompt — returns a clarity/intent score (0–100)
3. Build confidence is computed from output quality signals: files generated, archetype match, images, code length
4. A structured AI Factsheet is saved per version — to disk and to the database

**What's in a Factsheet:**
- Prompt Quality Score (IBM Watson NLU)
- Build Confidence Score (output quality signals)
- Human Review Required flag (auto-triggered when either score < 50)
- Model Registry — every AI model used: OpenAI (PM Agent), Google Gemini (Architecture), Anthropic Claude (Build), IBM Watson NLU (Governance)
- Compliance flags: data_privacy, bias_check, content_moderation
- Archetype, token usage, build duration

**Dashboard integration:**
The Enterprise dashboard header shows live averages across all builds:
- Avg Prompt Score (purple Sparkles icon)
- Avg Build Score (blue Shield icon)
- Pre-governance builds show "—" (not zero)

**Resume/portfolio value:** Governed, auditable AI pipelines with IBM Watson scoring — rare even among senior IBM AI Engineers.

---

## Roadmap Summary

| Phase | Status | Description |
|-------|--------|-------------|
| 1–6.4 | ✅ | Core pipeline, UI, enterprise design |
| 7A-7H | ✅ | Iterative pipeline, live preview, stability, output quality, chatbox |
| 8.1 | ✅ | One-click publish |
| 10.1-10.2 | ✅ | Watson STT/TTS |
| 10.4 | ✅ | App type lock (archetype guardrail) |
| 12.1 | ✅ | Domain personality upgrade (25 archetypes) |
| 13 | ✅ | Chat persistence + user model |
| 14 | ✅ | Iteration mode fixes |
| 15 | ✅ | Consumer frontend v2 |
| 15.4 | ✅ | Enterprise UI (frontend-v4, shadcn/ui) |
| 16.1 | ✅ | Bug fixes — chat persistence, JSON repair, build lock |
| 16.2 | ✅ | Branding — hexagon logo + favicon across all UIs |
| 16.3 | ✅ | Studio feature parity — sort, i18n, build details |
| 16.4 | ✅ | Watson STT/TTS for Enterprise UI |
| 17.1 | ✅ | Watson NLU pre-pipeline analyzer |
| 17.2 | ✅ | Governance Agent — AI Factsheets + Watson NLU scoring |
| 17.3 | ✅ | Dashboard governance metrics (Avg Prompt + Build scores) |
| 17.4 | 🔴 | Dual PDF export — Client PDF + Internal PDF |
| 17.5 | 🔴 | Delivery Readiness Gate — configurable score threshold |
| 16.5 | 🔴 | Authentication (JWT + protected routes) |
| 18 | 🔴 | Unified auth + plan-based UI routing |
| 8.2 | 🔴 | PDF export of full build history |
| 8.3 | 🔴 | Client shareable read-only link |

---

## License

Proprietary. All rights reserved.
