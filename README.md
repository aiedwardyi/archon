# AI Dev Team (MVP #2)

Schema-driven multi-agent system that converts product ideas into structured implementation plans and executable code.

## 🎯 Current Capabilities

**Multi-Agent Workflow:**
- **PM Agent** (OpenAI) → Generates structured Product Requirement Documents
- **Planner Agent** (Gemini) → Creates schema-validated execution plans with milestones and tasks
- **Engineer Agent** (Gemini) → Executes tasks and generates code files

**Production Features:**
- Flask API backend with async execution
- React UI with automated task execution
- Real-time status polling and toast notifications
- Complete observability with agent sequence tracking
- Deterministic, replayable workflows

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key
- Google Gemini API key

### Setup

1. **Clone and install dependencies:**
```powershell
# Clone repository
git clone <your-repo-url>
cd ai-dev-team

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
cd apps/offline-vite-react
npm install
cd ../..
```

2. **Set API keys (required for each session):**
```powershell
$env:OPENAI_API_KEY = "sk-proj-..."
$env:GENAI_API_KEY = "your_gemini_key"
```

3. **Start the servers:**
```powershell
# Terminal 1: Flask backend
python backend/app.py

# Terminal 2: React frontend
cd apps/offline-vite-react
npm run dev
```

4. **Open browser:**
Navigate to `http://localhost:5173`

---

## 📋 Multi-Agent Workflow

### How It Works
```
User Input (React UI)
    ↓
PM Agent (OpenAI)
    ↓ generates
PRD Artifact (JSON)
    ↓ consumed by
Planner Agent (Gemini)
    ↓ generates
Plan Artifact (milestones + tasks)
    ↓ consumed by
Engineer Agent (Gemini)
    ↓ generates
Code Files (HTML, CSS, JS, etc.)
    ↓
Execution Result → UI Notification
```

### Example Workflow

**1. Generate a project plan:**
```powershell
# Run multi-agent orchestrator
python -m scripts.orchestrate_multi_agent @idea.txt
```

Where `idea.txt` contains:
```
Build a simple calculator web app
```

**Output:**
- `artifacts/last_prd.json` - PRD with requirements, goals, features
- `public/last_plan.json` - Plan with milestones and tasks

**2. Execute tasks via UI:**
- Open `http://localhost:5173`
- Click on a task in the sidebar
- Click "Execute task" button
- Watch the progress:
  - 🔵 Blue toast: "Task execution started..."
  - ⏳ Polling every 2 seconds
  - 🟢 Green toast: "Task execution completed!" (after ~10-15 seconds)

**3. View generated artifacts:**
- Click "Artifacts" tab
- See `last_execution_result.json` with agent sequence: `pm → planner → engineer`
- Check `public/generated/` directory for code files

### Agent Roles

**PM Agent (Product Manager):**
- Input: User idea (plain text)
- Output: Structured PRD with 14 sections
- Model: OpenAI GPT-4 with structured outputs
- Artifact: `artifacts/last_prd.json`

**Planner Agent:**
- Input: PRD artifact
- Output: Execution plan with milestones and tasks
- Model: Google Gemini
- Artifact: `public/last_plan.json`

**Engineer Agent:**
- Input: Task snapshot from plan
- Output: Code files (HTML, CSS, JS, etc.)
- Model: Google Gemini
- Artifact: `public/last_execution_result.json`

### Agent Sequence Tracking

Every artifact includes `_agent_sequence` metadata:
```json
{
  "_agent_sequence": ["pm", "planner", "engineer"],
  ...
}
```

This provides full observability of which agents contributed to each artifact.

---

## 🏗️ Architecture

### Backend (Flask)
- **Async execution:** Consumer runs in background thread
- **State tracking:** Knows when execution is running vs complete
- **REST API:**
  - `POST /api/execute-task` - Start task execution
  - `GET /api/execution-status` - Check execution status
  - `GET /api/plan` - Get current plan
  - `GET /api/prd` - Get current PRD

### Frontend (React + Vite)
- **Task execution:** Click button → automated workflow
- **Polling:** Checks status every 2 seconds
- **Toast notifications:** Real-time feedback
- **Artifacts panel:** View all generated artifacts
- **Agent sequence display:** See which agents produced each artifact

### File Structure
```
ai-dev-team/
├── agents/                    # Agent implementations
│   ├── pm_agent.py           # PM (OpenAI)
│   ├── planner_agent.py      # Planner (Gemini)
│   └── engineer_agent.py     # Engineer (Gemini)
├── backend/
│   └── app.py                # Flask API server
├── apps/offline-vite-react/  # React UI
│   ├── src/
│   │   └── components/
│   │       ├── TaskPanel.tsx # Task execution UI
│   │       └── ToastContainer.tsx # Notifications
│   └── public/               # Runtime artifacts
│       ├── last_plan.json
│       ├── last_execution_result.json
│       └── generated/        # Code files
├── scripts/
│   ├── orchestrate_multi_agent.py  # PM → Planner orchestrator
│   └── consume_execution_request.py # Engineer executor
└── schemas/                  # JSON schemas for validation
```

---

## ✅ Determinism & Execution Guarantees

This system is designed to be **replayable and deterministic**.

### What determinism means here
- Identical *semantic* execution requests produce identical execution results
- Allowed non-deterministic fields (timestamps, transport metadata) are excluded from hashing
- Execution is fully file-based and observable

### How determinism is enforced
- Canonical request hashing (ignores `created_at`, `_meta`)
- Schema-validated execution requests and results
- Regression tests that re-run the same request and assert identical outputs

### Run determinism tests (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_tests.ps1
```

Expected result:
- All tests pass
- Exit code `0`

These tests act as a regression guard against hidden state, schema drift, or non-deterministic behavior.

---

## 📊 Status

**Phase 5 Complete:** Multi-agent coordination with Flask API integration

**Next:**
- Additional features (progress indicators, execution history)
- Performance optimization
- Production deployment considerations

---

## 🎯 Design Principles

- **Determinism first:** Identical inputs produce identical artifacts
- **Explicit contracts:** JSON schemas define all agent boundaries
- **Observable state:** All artifacts written as files
- **Failure visibility:** Errors surface as artifacts, not hidden logs
- **No hidden state:** All agent interactions through explicit file handoffs

---

## 📝 License

This project is proprietary software. All rights reserved.
