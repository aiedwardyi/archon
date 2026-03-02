# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Directory
- `C:\Users\mredw\OneDrive\Desktop\ai-dev-team\`
- `C:\Users\mredw\Desktop\ai-dev-team\`

## Ports
- **Backend (Flask):** http://localhost:5000
- **Studio (frontend-studio/):** http://localhost:3000
- **Enterprise (frontend/):** http://localhost:8080
- **Consumer (frontend-consumer/):** http://localhost:3002

## Starting Servers
```bash
# Backend
cd backend && python app.py

# Studio (Next.js)
cd frontend-studio && pnpm dev

# Enterprise (Vite)
cd frontend && pnpm dev

# Consumer (Vite)
cd frontend-consumer && pnpm dev
```

## Environment
- All API keys live in `backend/.env` — never commit this file
- Key names: `WATSON_STT_API_KEY`, `WATSON_TTS_API_KEY`, `WATSON_STT_URL`, `WATSON_TTS_URL`
- Virtual env: `.\venv\Scripts\Activate`

## Frontend Stack
- **Studio (frontend-studio/)** — Next.js + Tailwind, uses pnpm
- **Enterprise (frontend/)** — Vite + React + shadcn/ui, uses pnpm
- **Consumer (frontend-consumer/)** — Vite + React, uses pnpm

## Key Conventions
- UI vocab: "Brief" not "PRD", "Build Plan" not "Implementation Plan"
- Git commits: short, no AI attribution
- Code delivery: snippets only unless new file or under 50 lines
- Never write to `backend/.env` directly — Eddie manages keys manually

## Git
- **NEVER** run any git commands (commit, branch, push, checkout, etc.) — Eddie handles all git operations manually.
- **NEVER** add `Co-Authored-By: Claude` (or any Co-Authored-By line) to commit messages.

## Notifications
- **Bell + taskbar flash**: Run `powershell -NoProfile -ExecutionPolicy Bypass -File "C:/Users/mredw/OneDrive/Desktop/ai-dev-team/scripts/notify.ps1"` whenever you need user approval for a tool call or when you have completed a task/set of tasks. This alerts the user audibly (3-tone chime) and visually (taskbar flashes orange until focused).

