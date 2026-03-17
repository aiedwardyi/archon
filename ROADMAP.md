# Archon — Execution Roadmap

## Purpose

Archon is a multi-agent platform that converts product ideas into auditable
web applications with full version history. Target market: digital agencies
and enterprises delivering client apps to non-technical clients.

**Core value proposition:**
- Every prompt creates a full artifact set: Brief + Plan + Code + live preview
- Complete version history — every decision is auditable and reversible
- Agencies can show clients exactly what was built and why, version by version
- Business language UI — no developer jargon anywhere

**The MOAT:** The Versions page. Lovable/v0 show current state only.
Archon shows complete decision history with artifacts and live preview per version.

---

## Target User

Non-technical agency owner or project lead who:
- Cannot read code — needs to SEE the app running
- Needs to show clients every decision made during development
- Needs business language, not developer jargon

**Competitive positioning:** "Build client apps with AI. Show them everything."

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
Architecture Agent (Gemini 2.5 Flash)    → Build Plan artifact (versioned)
    ↓
Design Agent (GPT-4o-mini + DALL-E 3)   → Image assets (versioned, parallel generation)
    ↓
Build Agent (Gemini 2.5 Flash)          → Code files (versioned)
    ↓
Governance Agent (IBM Watson NLU)        → AI Factsheet (scored, versioned, exportable)
    ↓
Execution Result → Database + UI + Version Timeline + Live Preview
```

---

## Phased Execution Plan

### Phase 1-6.4 (✅ Completed)
Core pipeline, schemas, multi-agent coordination, SQLite persistence,
enterprise UI (10 screens, light + dark mode, business language throughout).

### Phase 7A — Iterative Pipeline & Version History (✅ Completed)
- Every prompt runs full pipeline → versioned DB record
- Prompt history continuation across iterations
- /iterate, /restore, /versions endpoints
- sessionStorage caching, real log persistence per execution

### Phase 7B — Live Preview (✅ Completed)
- Build Agent: Claude Sonnet 4.5 (primary), Gemini fallback
- Engineer prompt: self-contained HTML, 500-line limit, max_tokens 32000
- /api/preview/<project_id>/<version> serving generated HTML
- Live preview iframe in Versions + Artifacts pages
- Desktop/mobile viewport toggle working
- Agent card flash bug fixed

### Phase 7C — Stability & State Fixes (✅ Completed)
- Pipeline state restores from DB on page refresh
- Build completion uses DB as ground truth
- Prompt history persisted to sessionStorage across iterations
- Logs save by version number — Artifacts logs tab version-correct
- Pipeline polling restarts when navigating back to mid-run build
- Global block prevents concurrent project builds

### Phase 7D — UI Polish & Quick Wins (✅ Completed)
- ✅ 7D.1 Navbar real project name + version
- ✅ 7D.2 Projects table: Project ID column added
- ✅ 7D.3 Delete project + delete all with type-to-confirm modal
- ✅ 7D.4 Avatar dropdown (v0-style: email, dark mode, credits, sign out)
- ✅ 7D.5 Versions page live preview height increase
- ✅ 7D.6 Artifacts + Navbar version sync fixed (custom event bus)

### Phase 7E — Output Quality (✅ Completed)
- Design Agent built: GPT-4o-mini plans images → DALL-E 3 generates them
- Images downloaded to disk, served via /api/assets/<project_id>/<version>/<file>
- Design Agent skips image generation for dashboards/tools (cost saving)
- Engineer prompt: 10-shell layout intelligence system
- JSON repair fix: backtick-wrapped hex colors stripped before parse

### Phase 7F — Chatbox Upgrades (✅ Completed)
- ✅ 7F.1 File + media upload with drag-and-drop
- ✅ 7F.2 Graceful agent reply for unsupported inputs
- ✅ 7F.3 Master log accumulation across versions

### Phase 7G — Output Quality v2 (✅ Completed)
- ✅ UI archetype lock: Planner classifies, Engineer enforces as hard constraint
- ✅ Layout + content contracts for all 10 archetypes
- ✅ Two-file split: src/index.html + src/style.css
- ✅ Preview inline CSS stitching
- ✅ CSS design seed: glow/glass/shimmer in engineer.txt
- ✅ Pipeline real-time update bug fix
- ✅ Parallel pipeline (~30-40% faster)
- ✅ DALL-E content filter fix

### Phase 7H — Conversational Chatbox (✅ Completed)
- ✅ PM Agent classify_intent: routes build vs chat
- ✅ /chat endpoint — no DB record, no version created for questions
- ✅ Archon reply bubbles in chatbox UI
- ✅ Chat history passed into build context
- ✅ Context-aware replies using project PRD
- ✅ Download project as zip (with assets)

### Phase 8 — Publish + Client Deliverables (🔧 In Progress)
- ✅ 8.1 One-click Publish — shareable hosted URL
- ✅ 8.UI.1 Artifact cards link to Artifacts page with tab pre-selection
- ✅ 8.UI.2 Account modals — Profile, Settings, Pricing, Documentation
- ✅ 8.2 PDF export — done via Phase 17.4 Dual PDF Export
- 🔴 8.3 Client shareable read-only link
- 🔴 8.4 White-label option (agency branding)

---

## Competitive Positioning

| Feature | Lovable/v0 | Archon |
|---------|-----------|--------|
| Context continuation | ✅ | ✅ |
| Full chain on every edit | ❌ | ✅ |
| Artifact trail per version | ❌ | ✅ |
| Restore previous version | ✅ | ✅ |
| Live preview | ✅ | ✅ |
| Version history with preview | ❌ | ✅ |
| Auditable Brief per iteration | ❌ | ✅ |
| AI-generated design assets | ❌ | ✅ |
| Smart layout detection (10 shells) | ❌ | ✅ |
| Conversational chatbox | ✅ | ✅ |
| Download project as zip | ❌ | ✅ |
| One-click publish | ✅ | ✅ |
| Persistent chat history (DB) | ❌ | ✅ |
| Artifact cards → tab navigation | ❌ | ✅ |
| Account modals (Profile/Settings/Pricing) | ✅ | ✅ |
| Client PDF export | ❌ | 🚧 8 |
| Non-technical agency UI | ❌ | ✅ |
| Korean/English i18n | ❌ | ✅ |
| Visual reference input (image attachments guide AI) | ✅ | ✅ |

---

## Current State (Mar 2026)

- ✅ Five-agent pipeline (Requirements → Architecture → Design → Build → Governance)
- ✅ Build Agent: Gemini 2.5 Flash (primary), Claude Opus path preserved for future re-enable
- ✅ Flask backend (port 5000), SQLite, full persistence
- ✅ Three frontends: Studio (3000), Consumer (3002), Enterprise (8080)
- ✅ JWT authentication — login, register, Google OAuth, JWT blacklist logout
- ✅ User-scoped projects (owner_id) + concurrent pipeline
- ✅ IBM Watson governance — NLU scoring, AI Factsheets, Quality Tier badges
- ✅ Dual PDF export — Client PDF + Internal PDF
- ✅ Iterative pipeline with full version history
- ✅ Live preview iframe (Versions + Artifacts pages)
- ✅ Conversational chatbox — routes build vs chat, DB-persisted
- ✅ Design Agent — DALL-E 3 parallel image generation, content filter fallback
- ✅ 25 archetypes with domain-specific layout + content contracts
- ✅ Credit system — 1 credit = 2,500 tokens, navbar balance display
- ✅ Korean/English i18n across all three frontends
- ✅ Watson STT/TTS voice input/output in Enterprise UI
- ✅ Centralized Gemini client (`utils/genai_client.py`) — supports Vertex AI + AI Studio

### Branch Update — Componentized Builder Pipeline

Current work on `feat/componentized-builder-pipeline`:
- Added dual scaffold routing: simple requests stay on the legacy single-page path, app-like requests can use a componentized React + TypeScript + Vite workspace.
- Extended planner, schema, engineer, and backend contracts for multi-file generation, preview builds, and multi-file iteration context.
- Added persisted visual direction, visual DNA extraction, and feature inventory locks so later iterations preserve identity instead of rewriting the app loosely.
- Added local contract recovery, build repair, density audit, semantic completeness checks, and targeted refinement/content-fix passes for weak app outputs.
- Added curated benchmark routing plus reusable style-family selection so adjacent fan-page prompts can reuse the stronger cinematic collector shell instead of relying only on literal franchise matches.
- Added fan-page-aware quality scoring so cinematic archives are no longer penalized by dashboard KPI/chart/table rules during refinement.
- Added deterministic support-file recovery for malformed componentized workspaces, including `package.json` salvage before install and broader build-repair scope for support/config files.
- Added preview-safe generated-asset routing so componentized fan-page bundles now resolve local design images correctly through preview-served HTML, JS, and CSS.
- Added stricter dashboard/fintech density gates plus runtime normalization for chart-helper scope and safe dependency syncing so fresh componentized previews fail less often and preserve richer shell behavior.
- Added deterministic dashboard/fintech polish guards so preview-time depth, support-module hierarchy, and action affordance can improve without another broad prompt rewrite.
- Added tighter componentized refinement scoping so generated lockfiles, icon libraries, runtime polish guards, and low-signal stub CSS files stop consuming dashboard/fintech repair bandwidth.
- Added a runtime shell layout repair for fixed-sidebar grid dashboards plus broader support-module/button polish guards so collapsed previews recover before scoring.
- Added safer fintech polish-runtime behavior plus broader componentized syntax normalization for JSX handler bleed, main-entry import-note bleed, control-flow comment-close bleed, and swallowed array terminators so delayed preview capture no longer blanks rendered fintech dashboards and malformed support files recover more often.
- Current branch status: build stability is materially improved, fan-page benchmark routing is cleaner, and image-heavy outputs are rendering much closer to target; the best recent scoreable fintech validation still held at 72.5 in `support_module_gate_v16_fintech_typography_feed_guard_safe_retry`, and dashboard no longer times out at 900s, with March 15, 2026 reruns progressing from 73.5 (`support_module_gate_v10_dashboard_layout_guard`) and 73.0 (`support_module_gate_v11_dashboard_support_module_guard`) to 76.0 (`support_module_gate_v18_dashboard_title_activity_guard`) and then 82.0 (`support_module_gate_v20_dashboard_panel_distinction_guard`), which clears the prior 81.0 branch benchmark. The March 15, 2026 `support_module_gate_v34_fintech_table_trend_prompt_retry` black-screen path is now fixed locally by the safer polish runtime, but the follow-up rerun `support_module_gate_v35_fintech_table_trend_prompt_capture_fix` still hit a separate generated syntax family before preview and did not produce a new scoreable fintech checkpoint.
- Proposed branching model: keep `main` as the broad safe baseline, keep `feat/componentized-builder-pipeline` as the validated pipeline checkpoint, and branch the upcoming scheduler work from `feat/componentized-builder-pipeline` so experimental multi-run changes do not destabilize the current builder recovery path.
- Proposed experimental branch: `feat/componentized-multi-run-experiments`.
- Proposed roadmap for that branch:
  Stage 1: parallelize the validation runner with bounded concurrency and one API client per worker.
  Stage 2: add backend protections so the same project cannot run twice concurrently, plus a global worker limit.
  Stage 3: move queued/running job state off process-local memory toward durable coordination suitable for production scaling.

### Branch Update — Componentized Multi-Run Experiments

Current work on `feat/componentized-multi-run-experiments`:
- Branch created from `feat/componentized-builder-pipeline` after the March 15, 2026 documentation checkpoint so the validated builder/runtime recovery path remains a safe fallback.
- Added a tracked Stage 1 multi-run runner at `eval/run_componentized_validation.py` instead of relying on the untracked temp validation script.
- Runner capabilities now include bounded concurrency via `--max-parallel`, one `BuilderAPI` client per worker, lazy scorer imports so CLI help and non-scoring paths do not fail on optional scorer deps, backend health checks that do not require auth bootstrap, and per-archetype result artifacts plus timestamped logs for long-running smoke tests.
- Added targeted regression coverage in `tests/test_run_componentized_validation.py` for preview-build fallback loading, backend health acceptance of 401, and result-file emission on build failure.
- March 15, 2026 local smoke-run evidence: with `--archetypes dashboard portfolio --max-parallel 2`, project 424 / execution 430 and project 425 / execution 431 authenticated independently, created separate projects, and progressed through `pm`, `planner`, and `engineer` concurrently, confirming the eval driver can overlap distinct-project runs on the current backend.
- Extended Stage 2 backend protections in `backend/app.py` into opt-in queue semantics: the same atomic admission path now blocks same-project overlap, enforces `ARCHON_MAX_CONCURRENT_PIPELINES`, allows `/api/execute-task` and `/api/projects/<id>/iterate` to queue with `enqueue_on_limit`, surfaces `queued_pipelines` / `project_queued` / `queue_position`, and automatically dispatches the next queued job when a running slot finishes.
- Extended the tracked eval harness to use that path safely: `eval/api_client.py` can request queue-on-limit and `eval/run_componentized_validation.py` now exposes `--enqueue-on-limit` so bounded-parallel runs can wait for backend capacity instead of failing immediately under saturation.
- Hardened the eval client against healthy queue wait: `eval/api_client.py` now budgets queue wait separately from active build time, and `eval/run_componentized_validation.py` exposes `--queue-timeout` so bounded parallel validation can tolerate backlog without treating a queued job as a backend failure before execution starts.
- Added queue telemetry to eval artifacts: `eval/api_client.py` now preserves trigger queue state, observed queue positions, queue wait seconds, and active run duration in `queue_telemetry`, while `eval/run_componentized_validation.py` writes that telemetry into per-archetype `result.json` files, adds an aggregate `queue_summary.json`, and surfaces both run-level and batch-level queue behavior in `summary.md`.
- Added a build-only smoke path to `eval/run_componentized_validation.py`: `--build-only` keeps project creation, build execution, preview-build inspection, and queue telemetry artifacts, but skips screenshots and scorer calls so queue-focused smoke runs are fast enough to use routinely during scheduler validation.
- March 15, 2026 queue-telemetry smoke evidence: with backend capacity forced to one worker (`ARCHON_MAX_CONCURRENT_PIPELINES=1`) and the runner invoked as `--max-parallel 2 --enqueue-on-limit --build-only`, `dashboard` (project 427 / execution 432) started immediately while `portfolio` (project 426 / execution 433) queued at position 1 for 330.7 seconds. The resulting `queue_summary.json` reported `observed_runs=1`, `average_queue_wait_seconds=330.7`, and `worst_queue_position=1`, confirming that the new artifacts describe real queued load accurately even when preview builds later fail.
- Added preview-failure classification to the validation runner: `eval/run_componentized_validation.py` now records a structured `preview_failure` block in per-archetype results and surfaces it in `summary.md`, so smoke runs can distinguish causes like shared npm-cache `EPERM` from generic preview absence. The March 15, 2026 queue smoke on projects 426 and 427 now maps cleanly to `npm_cache_eperm` because both preview installs failed under `C:\\Users\\mredw\\AppData\\Local\\npm-cache\\_cacache\\tmp\\...`.
- Isolated componentized preview installs to a workspace-local npm cache in `utils/componentized_runtime.py`: `build_componentized_preview()` now points `npm_config_cache` / `NPM_CONFIG_CACHE` at `<code_dir>/.npm-cache`, and `.npm-cache` is excluded from editable-context scans so transient install artifacts never bleed into later prompt-repair context.
- March 15, 2026 direct preview concurrency smoke evidence: two temp componentized workspaces built through `build_componentized_preview()` in parallel both completed successfully after the local-cache change, confirming that the earlier queued-run `npm_cache_eperm` was shared-cache contention rather than a fundamental inability to run multiple preview installs at once.
- Added a minimal durable recovery layer on top of that queue path: persisted `Execution.status == "pending"` records can now be reconstructed into queued jobs on the first real backend request after restart, then re-dispatched up to the worker cap. Recovery is skipped in test mode and can be disabled with `ARCHON_DISABLE_PIPELINE_RECOVERY`.
- Added queue-depth protection in `backend/app.py`: `ARCHON_MAX_QUEUED_PIPELINES` now bounds queued work, scheduler snapshots expose `max_queued_pipelines`, and overload returns an explicit `queue_limit` rejection instead of allowing the in-memory queue to grow without bound.
- Added a Stage 3 ownership checkpoint in `backend/app.py` and `backend/models.py`: executions now persist scheduler claim metadata (`scheduler_worker_id`, `scheduler_claimed_at`, `scheduler_heartbeat_at`), workers atomically claim `pending` executions before doing pipeline work, DB heartbeats refresh during active runs, stale `running` executions can be failed by timeout and released, and success/error completion clears ownership metadata cleanly.
- Removed the old `init_db()` behavior that force-marked all `running` executions as failed at import time. Restart handling is now moving toward explicit heartbeat-based scheduler recovery instead of a blanket DB reset.
- Extended that Stage 3 path so persisted `pending` executions are not only recoverable at boot: when a worker slot is released, the scheduler now re-scans the DB-backed pending set, adopts the oldest eligible job into the local queue, and dispatches it immediately. `/api/execution-status` also clears stale local queued state when the DB shows another worker already claimed the execution, reducing queue drift between processes.
- Added a lightweight background scheduler poller in `backend/app.py`: after the first real request bootstraps the scheduler, each backend process can now periodically run maintenance to dispatch local queued work, fail stale `running` executions by heartbeat timeout, and adopt oldest persisted `pending` executions even when this process did not just release a slot. The poll interval is controlled by `ARCHON_SCHEDULER_POLL_INTERVAL_SECONDS`, and the poller can be disabled with `ARCHON_DISABLE_SCHEDULER_POLLER`.
- Added DB-ground-truth fallback for `/api/execution-status`: when a backend process has no local in-memory state for a project, it now looks up the active-head execution in the database and reports `RUNNING` or `COMPLETED` from that record instead of incorrectly returning `FAILED`. That closes a real cross-process blind spot for status polling after restarts or cross-node routing.
- Moved scheduler snapshots and route admission closer to DB truth: `backend/app.py` now combines local reservations with persisted `Execution.status` rows when reporting `active_pipelines`, `queued_pipelines`, `project_running`, and `project_queued`, and `/api/execute-task` now uses that durable view for same-project overlap, global worker-limit checks, and queue-limit checks. That closes another multi-process hole where a second backend could previously ignore running or queued work owned by a different process.
- Moved execution claiming earlier in the lifecycle: `backend/app.py` now claims the execution before starting a worker thread, and queued/direct starts skip launching a duplicate local thread if another process already claimed that pending execution. `run_full_pipeline_async` now supports a preclaimed path so the worker does not waste time double-claiming work it already owns.
- Reordered scheduler maintenance around durable queue order: `backend/app.py` now adopts persisted `pending` executions before dispatching local queued work, and queued jobs carry `created_at` so recovered older executions are inserted ahead of newer local queue entries. That means the oldest DB-backed pending execution now wins when a worker slot opens, instead of whichever process happened to have a newer local queue item ready first.
- Tightened worker-cap enforcement during dequeue and maintenance: `backend/app.py` now checks DB-aware scheduler snapshots before dispatching local queued jobs or adopting persisted pending work, so one backend will not start extra queued pipelines just because its own process-local running count is low while another backend already occupies the global cap.
- Fixed direct-start rollback when prestart execution claiming fails: `/api/execute-task` and `/api/projects/<id>/iterate` now clean up the just-created pending execution, restore project/head state, and return a scheduler busy response instead of incorrectly reporting `"started"` when no worker thread was actually launched.
- Added durable DB slot leases for actual execution starts: `backend/models.py` now persists `pipeline_slot_leases`, and `backend/app.py` now acquires a unique slot row before flipping an execution from `pending` to `running`. That gives competing backends a real DB-backed contention point for worker slots, and success/error/stale/reset cleanup now releases the lease with the execution claim.
- Extended scheduler snapshots and route admission to trust slot leases too: `backend/app.py` now treats slot-leased pending executions as active capacity instead of queued capacity, so same-project overlap and global worker-limit checks are lease-aware before another route tries to start work.
- Reduced scheduler dependence on local queue bootstrap: `dispatch_queued_pipelines()` can now query the oldest persisted `pending` executions directly from the database and adopt them into worker starts even when the process has no matching in-memory queue entry.
- Reduced scheduler dependence on local queue ordering too: `dispatch_queued_pipelines()` now starts work from the durable oldest-`pending` execution set first, removes any matching in-memory queue entries once selected, and only falls back to purely local queue jobs when there is still spare capacity after the DB-backed picks. That closes another path where a newer local queue entry could otherwise outrank an older persisted pending execution.
- Hardened the scheduler regression fixtures for the shared SQLite test database: `backend/tests/test_execution_limits.py` now prunes stale `limits-%@archon-test.com` users, executions, projects, and slot leases around the suite so orphaned timed-out test runs do not poison durable queue ordering assertions.
- Added backend regression coverage in `backend/tests/test_execution_limits.py` for queued admission, dequeue dispatch, persisted pending-job recovery, direct durable-queue adoption without a local queue seed, recovery from missing local queue entries for a queued execution, direct oldest-pending-first dispatch even when a newer local queue entry exists, exclusive execution claims, durable slot-lease saturation during execution claim, slot-leased pending route admission, stale-running recovery with lease cleanup, durable-queue adoption on slot release, stale queued-status cleanup, background maintenance adoption, DB-backed active-head status fallback, DB-backed route admission/queue limits, prestart execution claiming, oldest-pending-first dispatch ordering, DB-running worker-cap saturation during dispatch/maintenance, and direct-start rollback before thread launch, plus runner coverage in `tests/test_run_componentized_validation.py` for forwarding the queue flag. Focused `py_compile`, `unittest`, and the runner `--help` path passed on March 15, 2026.
- Current branch capacity is still conservative by default: `backend/app.py` defaults `ARCHON_MAX_CONCURRENT_PIPELINES` to `2`, so two pipelines can actively run at once across all accounts unless the environment raises that cap, while `ARCHON_MAX_QUEUED_PIPELINES` defaults to `20`, so additional requests can wait but are not concurrent executions.
- Timeout behavior is now admission-safe but not infinite: the start routes return quickly with `started` or `queued` because actual pipeline work happens on background threads. The eval client now budgets queue wait separately from active build time, and the componentized validation runner defaults `--queue-timeout` to 1800 seconds, but very long queue plus build durations can still surface client-side timeouts if those budgets are exceeded.
- March 16, 2026 runner stability checkpoint: `eval/run_componentized_validation.py` now creates the labeled results directory before managed backend startup and preserves backend stdout/stderr tails when startup fails, which makes `--launch-backend` smoke runs debuggable instead of failing with an opaque connection error. Focused regression coverage was added in `tests/test_run_componentized_validation.py`.
- March 16, 2026 portfolio runtime recovery checkpoint: `utils/componentized_runtime.py` now normalizes malformed support files and comment-bleed families that were still breaking portfolio previews, including leading-comma JSON noise, repeated orphan `currentTarget` splits, orphan comment-close bleed inside string literals, comment-tail split identifiers, and stray filename labels after comments. The resulting validation path moved portfolio from pre-preview failure to preview success in `.tmp-portfolio-build-smoke-20260316c`, then from a `10.0` black-screen baseline in `support_module_gate_v38_portfolio_preview_recovery_baseline` to `51.5` in `support_module_gate_v39_portfolio_runtime_recovery`.
- March 16, 2026 dashboard refresh: `support_module_gate_v37_dashboard_branch_refresh` scored `69.5`, which confirms this branch is not blocked on dashboard preview stability anymore, but it still trails the stronger builder-branch dashboard checkpoint and needs design/prompt work on hierarchy, depth, and sidebar balance.
- March 16, 2026 ecommerce recovery checkpoint: this branch now carries stronger commerce-shell image guidance plus deterministic runtime repairs for swallowed JSX tag boundaries, Alpine-style directive bleed, malformed self-closing `Link` wrappers, orphan `}` lines inside JSX collections, and base-css import precedence. That moved ecommerce from a stable but generic `65.5` in `support_module_gate_v40_ecommerce_branch_refresh`, through two preview-breaking syntax variants, to a recovered `69.5` in `support_module_gate_v43_ecommerce_link_brace_repair`. The remaining gap is now visual polish and brand distinctness rather than preview-build stability.
- March 16, 2026 game branch refresh checkpoint: `support_module_gate_v44_game_branch_refresh` produced a scored preview at `88.0`, which is `+3.5` over the prior game benchmark baseline of `84.5`. Saved preview references for later review: preview URL `http://127.0.0.1:5000/api/preview/440/1`, viewport screenshot `eval/results/support_module_gate_v44_game_branch_refresh/game/screenshot.png`, and full-page screenshot `eval/results/support_module_gate_v44_game_branch_refresh/game/screenshot_full.png`.
- March 16, 2026 game benchmark promotion: the FF8 `88.0` run is now promoted into the benchmark registry as `branch-ff8-garden-archive-20260316`, the game baseline in `eval/run_componentized_validation.py` now compares against that score, and the local reference loader can now read componentized benchmark source from `src/App.tsx` plus combined CSS instead of only legacy `index.html`/`style.css`.
- March 16, 2026 game asset-guard checkpoint: componentized generation now gets a stricter local-asset contract (`backend/app.py`, `prompts/engineer_componentized.txt`, `prompts/archetypes/game.txt`) plus smarter game-aware runtime asset fallback in `utils/componentized_runtime.py`. The important behavior changes are: no invented extra `generated-assets/*` filenames when local assets are already enumerated, deterministic non-broken `.svg` placeholders for missing game icon slots, and small game polish-guard CSS for scroll-indicator stacking and display-font consistency.
- March 16, 2026 Pokemon rerun result: `support_module_gate_v47_game_pokemon_asset_guard` moved the Pokemon fan-page prompt from `77.0` to `83.5` and, more importantly, generated a coherent local asset pack that exactly matched the code references. Saved preview reference: `http://127.0.0.1:5000/api/preview/443/1`; screenshots live under `eval/results/support_module_gate_v47_game_pokemon_asset_guard/game/`.
- March 16, 2026 Zelda caution note: `support_module_gate_v48_game_zelda_asset_guard` is a rejected follow-up, not a checkpoint. It validated the tighter asset path discipline, but the layout/content realization collapsed to `45.5`, so the branch should keep the code changes while treating that rerun as evidence that the remaining gap is prompt/output variance rather than missing-asset breakage.
- March 16, 2026 game follow-up runtime checkpoint: a later FF8 control rerun exposed a componentized import-alias failure family where the generated workspace emitted files such as `HeroSection.tsx`, `CharacterSection.tsx`, and `WeaponShowcase.tsx` but still imported `./components/Hero`, `./components/CharacterCards`, or `./components/WeaponSection`. `utils/componentized_runtime.py` now rewrites those missing local aliases to the discovered component files before preview build, with focused regression coverage in `tests/test_componentized_runtime.py`.
- March 16, 2026 game shell-polish checkpoint: the game prompt/runtime path now rejects remote franchise badge or sprite fetches, rewrites remote badge URLs in badge object literals to local generated badge SVG placeholders, and reserves more vertical room for the hero scroll indicator so it no longer hides behind CTA buttons on game pages. That kept the accepted Pokemon layout intact while removing broken bottom-section image sprawl.
- March 16, 2026 game consistency reruns: the FF8 control rerun held at `86.5` on preview `666/1`, the stronger Zelda follow-up recovered to `80.5` on preview `668/1`, and the preferred Pokemon README demo remains the rebuilt `667/1` shell after the local badge and scroll-indicator fixes were applied to the accepted layout. README showcase screenshots now point at those accepted March 16, 2026 game outputs.
- March 16, 2026 game concurrency-and-interaction checkpoint: the branch now hardens game pages against dead mid-page CTA buttons and literal world-map placeholder text, broadens runtime tsconfig JSON repair, and lets `/api/execution-status` resolve completed artifact state even when a stale running row lingers. A live concurrent Halo + Metroid pair finished cleanly at `http://127.0.0.1:5000/api/preview/678/1` and `http://127.0.0.1:5000/api/preview/679/1`, which is the strongest evidence so far that the secondary branch backend can overlap game runs without regressing the accepted FF8-style shell quality.
- March 16, 2026 dashboard + ecommerce follow-up: the branch now extends componentized recovery to multiline post-comment prose notes, orphan array-statement comment closes, and JSX text-node `*/` bleed while also strengthening `dashboard.txt` and `ecommerce.txt` around real CTA/state behavior, support-rail weight, image fallback quality, and sub-`1024px` layout discipline. A fresh live concurrent rerun pair finished on `688/1` (ecommerce) and `689/1` (dashboard), which is useful scheduler evidence because both overlapped successfully; however, only ecommerce emerged preview-clean, while dashboard still carries generated copy/icon corruption and malformed SVG path data that need another runtime/prompt pass before it is demo-grade.
- March 16, 2026 image-hosting + popup follow-up: componentized runtime support now rewrites remote game/ecommerce image URLs to local generated placeholders so preview stability no longer depends on `via.placeholder.com` or Unsplash availability, and game card CTAs that regress to `alert()` now get converted back into inline detail/log panels. Fresh live proofs: `693/1` (Halo) and `694/1` (ecommerce) are no longer sourcing remote preview imagery, and `695/1` replaced the native Halo `Access Log` browser popup with an in-page expandable detail surface.
- March 16, 2026 code-browser safety checkpoint: version file trees now exclude runtime/install directories such as `node_modules`, `dist`, and `.npm-cache`, which keeps componentized build artifacts from overwhelming the three frontend code tabs while preserving the componentized preview path.
- March 16, 2026 random-archetype validation checkpoint: a score-only eval pass on `editor`, `form`, and `fintech` (`project 454/455/456`) showed that this branch still has major generalization gaps outside the heavily tuned archetypes. `editor` (`11.5`) and `form` (`10.0`) both rendered placeholder-only outputs; `fintech` reached `70.5` in that run but still trailed prior stronger baselines.
- March 16, 2026 three-way concurrent quality checkpoint: bounded parallel validation on `dashboard`, `fintech`, and `portfolio` (`project 457/458/459`) completed with valid queue telemetry (`queue wait 369.8s`, `max_position=1`) and successful preview builds, confirming concurrency path stability. Quality remained below branch baselines in the same run: dashboard `72.5` vs `81.0`, fintech `10.0` vs `83.5`, portfolio `58.5` vs `83.5`.
- March 16, 2026 frontend smoke checkpoint: production builds completed for all three frontend apps (`frontend`, `frontend-studio`, `frontend-consumer`), indicating recent regressions are concentrated in generated app outputs and cross-archetype design quality, not frontend bundle health.
- Managed-backend parallel smoke status on March 16, 2026: the eval runner can now boot its own backend and drive bounded-parallel build-only validation successfully, but same-second contention on `/api/execute-task` still occasionally returns `429` instead of queueing under live load. That race is documented and intentionally deferred while this branch focuses on app-quality polish instead of additional backend rework.
- Current blocker is no longer route-level admission control, the absence of any queue, total loss of queued work on restart, unbounded queue growth, duplicate same-execution startup inside a single database, complete inability for a free worker to adopt persisted pending work after another worker frees a slot, total dependence on incoming requests for maintenance, the status endpoint returning `FAILED` when another backend owns the active execution, route-level worker-limit checks that only saw one process, duplicate local worker threads starting for a pending execution that another process already claimed, or false `"started"` responses when a prestart claim failed. The remaining production-scaling risks are durable multi-process queue coordination and storage: live dispatch state is still partly process-local, direct DB adoption now reduces dependence on rebuilt local queue entries, direct dispatch ordering now prefers the oldest persisted pending execution over newer local queue state, dequeue now respects DB-visible worker saturation, actual execution start now contends on durable slot leases, route admission now sees lease-backed active capacity too, build-only smoke mode now proves the queue telemetry under real backlog, and preview installs now avoid the previously shared user npm cache, but SQLite remains the first likely bottleneck under heavier concurrent writes. The next non-architecture validation target is another full queued smoke through the backend/eval harness so the runtime-level cache fix is confirmed end-to-end on live generated work.
- Production-architecture work remains the next larger branch decision: meaningful scaling beyond the current worker and queue limits will require moving scheduler durability to a stronger backing stack such as Postgres plus a real shared queue/broker and separate worker processes or hosts, rather than only increasing env caps on the current SQLite plus in-process-thread model.
- March 17, 2026 branch-strategy update: keep the globalization work on `feat/componentized-multi-run-experiments` so the same branch can validate family-level quality controls, runtime recovery, and bounded multi-run behavior together instead of splitting those signals across a short-lived child branch.
- March 17, 2026 global-quality foundation checkpoint: `utils/reference_build_registry.py` now routes weaker workspace/tool prompts through reusable families (`editorial_workspace`, `product_builder_workspace`, `guided_setup_wizard`, `market_terminal_workspace`, `operator_console_workspace`), while `agents/engineer_agent.py` injects a `GLOBAL QUALITY FAMILY` contract block and optional domain overlay block into componentized initial-build prompts before the archetype kit reference. Local benchmark loading also now skips stale top entries instead of failing the whole archetype.
- March 17, 2026 runtime-recovery checkpoint: `utils/componentized_runtime.py` now repairs multiline comment/code swallow, generic arrow-token corruption, orphan JSX brace loss, missing sibling closing tags in half-repaired JSX, and preview-router mismatches. Those fixes recovered the failed workspace probes `696/1`, `697/1`, and `698/1` to successful preview builds.
- March 17, 2026 domain-overlay checkpoint: the shared floor now supports business-workspace overlays (`operations_control_tower`, `sales_deal_room`, `treasury_liquidity_terminal`) so high-density logistics, sales, and treasury prompts no longer all resolve to the same generic dashboard shell. Fresh reruns landed at `702/1`, `703/1`, and `705/1`; the main remaining gap is polish/layout execution rather than total shell collapse.
- March 17, 2026 dense-workspace polish checkpoint: the componentized runtime now repairs direct and nested support-rail shell failures during preview, so React workspaces that accidentally allocate too few columns or bury the support rail inside the main wrapper can still present a usable desktop shell. The same pass also tightened dense-table spacing/alignment and added JSX recovery for bare `</React>` fragment closers plus dotted closing tags, which was necessary to rebuild the broken sales workspace source before preview. Live rebuild confirmation remains on `702/1`, `703/1`, and `705/1`, with treasury now holding the intended desktop rail after first paint instead of only after a manual resize.
- March 17, 2026 artifact-surface parity checkpoint: after the live FF10 project probe, the branch now hardens the artifact layer itself instead of only generated app output. `backend/app.py` now treats the code browser as source-only (hiding binary/generated asset files and pruning empty asset folders), normalizes factsheet `files_generated` from the real visible source tree, excludes runtime/install directories from download zips, refreshes publish slugs with copied generated assets, and serves published pages with the correct base path. Enterprise + studio desktop preview panes are taller, and studio logs now come from the same backend per-version log endpoint as enterprise. One follow-up remains open if needed: convert the enterprise code tab to fully lazy file-content loading for very large source trees.
- March 17, 2026 refinement-latency checkpoint: the branch now trims internal post-build refinement cost as well as artifact-surface polish. `agents/engineer_agent.py` accepts an `attach_reference_images` flag, and `backend/app.py` disables image attachment for internal content-fix and quality-refinement reruns while adding explicit scope-size logs before those reruns begin. The goal is to keep initial multimodal generation quality high while preventing scoped follow-up passes from paying unnecessary multimodal latency. A fresh authenticated latency probe on project `710` version `1` completed successfully in `533.59` seconds and showed the new `Quality-refinement scope narrowed to 9 files` trace before the final scoped rewrite completed.
- March 17, 2026 external benchmark handoff: the next investigation step is a clean-room Lovable comparison focused on iteration discipline. Reason: fresh builds are healthier now, but same-project iteration is still fragile, with project `709` reproducing a scope-violation failure when the engineer attempted a broad rewrite instead of a surgical diff. The benchmark plan is to compare initial-export structure first, then compare the round-2 file diff after a focused iteration prompt, using Lovable outputs only as behavioral evidence for scoping, packaging, asset, and shell-preservation patterns.
- March 17, 2026 external benchmark result: the Lovable treasury-terminal comparison confirms that strong iteration discipline can stay narrow without redesigning the shell. The round-2 CHIPS incident enhancement touched only four panel files (`AlertsRail.tsx`, `FundingWindows.tsx`, `PaymentDrawer.tsx`, `SettlementQueue.tsx`) for a `117` insertion / `26` deletion diff, with no churn in root page/router files, package metadata, or shared UI scaffolding. The important lesson for Archon is not the exact source, but the behavioral pattern: preserve the page shell, centralize the ask on the directly affected panels, and avoid whole-app rewrites during scoped operational enhancements.
- March 17, 2026 external benchmark round-3 result: the Lovable scenario-switcher pass broadened scope modestly and in a mostly healthy way. Instead of rewriting the app, it introduced a focused shared `ScenarioContext.tsx`, updated `pages/Index.tsx` to own the active scenario, extended `CommandBar.tsx` with the switcher UI, and then flowed scenario-specific state into the same four operational panels. That is a useful target pattern for Archon iteration: promote shared state exactly one layer when necessary, rather than letting a scenario enhancement trigger root-shell churn. The caveat is that partial centralization still leaked one real consistency bug: FedWire alerts claim `3` impacted payments / `$50.09M`, while the queue-impact logic only flags non-settled `FedWire` rows, so the visible incident math would actually land closer to `2` payments / `$41.17M`.
- March 17, 2026 external benchmark round-4 result: Lovable handled operator actions with better-than-expected scope discipline. The pass did not touch the shell or scenario-switcher UI again; it only updated the shared scenario/action context, the page-level owner of that context, and the three affected panels (`SettlementQueue`, `PaymentDrawer`, `AlertsRail`). That is an important benchmark pattern for Archon: once the shared state layer exists, later interaction enhancements should mostly stay inside that layer plus the surfaces that render it. The remaining weakness is that baseline scenario alerts still live as static text while action alerts are generated dynamically, so the alert rail can contradict the now-updated queue/banner state after a hold/escalate/reroute. In other words, Lovable shows the right architectural direction, but even it still needs deeper recomputation of derived incident narratives when user actions mutate the scenario.
- March 17, 2026 external benchmark round-5 result: Lovable successfully repaired the derived-state inconsistency from round 4 without widening scope again. The fix stayed inside the shared state layer and the three consumers that actually render incident state (`AlertsRail`, `SettlementQueue`, `PaymentDrawer`). It moved base settlement data into the shared context file, added a focused `useIncidentState()` hook that computes still-impacted counts/value/IDs plus acted-upon payments from scenario + operator actions, and then replaced the alert rail’s old static incident copy with fully derived incident messaging. This is the clearest target pattern for Archon so far: once a shared context exists, consistency repairs should usually mean strengthening the derivation layer, not adding more local patches. The only remaining nit is implementation cleanliness rather than behavior: the drawer now imports the new hook without really using it, and the alert component keeps a couple of dead locals, but the core state-consistency problem we were benchmarking is materially solved.
- March 17, 2026 external benchmark wizard round-2 result: the Lovable vendor-onboarding comparison stayed disciplined for a branch-specific workflow enhancement. The international enhanced-due-diligence pass touched `8` files (`224` insertions, `90` deletions): the main wizard owner, five wizard surfaces (`ProgressRail`, `StepBankingTax`, `StepComplianceDocs`, `StepReview`, `SummarySidebar`), plus the shared `vendorDefaults.ts` seed data and `types/vendor.ts`. That is a healthy spread for this feature because the behavior genuinely spans wizard state, branch-specific fields, progress/error rendering, review gating, and sidebar summaries without thrashing the shell. The strongest pattern is that submission gating and step-error derivation still live at the wizard owner level, while the visible international surfaces render from that shared state. The main weakness is architectural duplication: international document IDs and branch requirement rules are still repeated across multiple files instead of being lifted into one shared requirements/derived-state helper, so the behavior is good but the implementation is not yet cleanly centralized.
- Next roadmap on this branch:
  Stage 1a: keep the bounded-parallel runner stable and continue using it as the validation harness.
  Stage 2a: keep the restart-recoverable queue path stable while continuing to use the bounded-parallel runner as the validation harness.
  Stage 3: when resumed, extend the validated scheduler semantics into a production-grade architecture with stronger durable storage and queueing, likely Postgres plus a real shared queue/worker stack, instead of continuing to rely on SQLite and process-local queue bootstrap as the long-term scaling model.

### Phase 9 — Pipeline Page & Classifier Improvements (⬜ Planned)
- ✅ Classifier too sensitive — opinion questions triggering builds
- Chat panel needs max-height + scrollable container
- Consider split layout: agent pipeline fixed top, chat scrollable below

### Phase 10 — IBM Watson Integration (🔧 In Progress)
- ✅ Speech to Text: user speaks prompts instead of typing
- ✅ Text to Speech: Archon reads replies aloud
- Watson Assistant: power conversational chatbox natively
- AI Factsheets / governance: model monitoring for enterprise credibility
- Natural Language Understanding: analyze prompt intent before pipeline routing
- Goal: IBM AI Engineer application showcase + $200 cloud credit usage

### 10.4 App Type Lock (Archetype Guardrail) ✅
- Added `locked_ui_archetype` at the Project level.
- First successful build persists the detected `ui_archetype`.
- All subsequent iterations must reuse the locked archetype.
- Planner receives locked archetype context and cannot reclassify.
- Backend overrides planner output if archetype differs.
- Explicit app-type change requests return a chat response suggesting a new project.
- Preserves full Brief / Plan / Code artifact trail per version.
Impact:
- Prevents unintended app-type mutation (e.g., landing → dashboard).
- Enables stable, Lovable-style iteration while maintaining audit trail moat.

### Phase 11 — Pipeline Page Redesign (⬜ Planned)
- Three-panel layout for large screens:
  Left: conversation/chat (scrollable)
  Top right: agent pipeline status cards
  Bottom right: live preview iframe
- Enterprise/agency target — assumes large monitor
- Classifier sensitivity fix: opinion questions never trigger builds
- Chat panel max-height with internal scroll

### Phase 12 — Output Domain Personality (⬜ Planned)
- Generated apps reuse same shell structure regardless of domain
- "Uber clone" produces generic dashboard instead of ride-sharing UI
- Root cause: archetype lock picks shell correctly but injects no domain aesthetics
- Fix: engineer prompt needs domain context injection — color palette, component vocabulary, visual metaphors per industry
- Examples: ride-sharing = map tiles, driver cards, live ping aesthetic
-           fintech = green/red tickers, candlestick feel, data density
-           gaming = dark immersive, HUD elements, particle effects
- Approach: planner agent injects domain_personality block into engineer task
- This is the main quality gap vs Lovable/v0

### Phase 12.1 — Domain Personality Upgrade (✅ Completed Feb 2026)
- Injected Tailwind CDN + Alpine.js for visual pages
- 18 archetypes with domain-specific palettes, fonts, and components
- pollinations.ai for fictional character/game asset generation
- Anti-patterns list to prevent generic AI output
- Result: FF7 fan page output matches Lovable quality

### Phase 13.1 — Chat Message Persistence (✅ Completed)
- chat_messages TEXT column on executions table (JSON array)
- POST /api/projects/:id/chat saves user + Archon messages to active head
- GET /api/projects/:id/chat-history returns full conversation
- Frontend restores chat across refreshes and machines

### Phase 14 — Iteration Mode Fixes (✅ Completed Feb 2026)
- Scope enforcement path normalization (safe_write.py `_tail_after_code()`)
- Archetype lock conversion phrase detection (prevent false positives like "add a mini game")
- Ancestor chain traversal for failed versions (walk up to 5 hops to find last successful code)
- Design asset reuse on iterations (skip DALL-E regeneration, reuse ancestor's last_design_assets.json)
- Asset URL version extraction from local_path (correct /api/assets/{pid}/{version}/ URL)
- Planner iteration file constraints (force output_files to src/index.html + src/style.css only)
- Preview endpoint CSS/JS inlining (inline all *.css and *.js files from code/src/)
- Strengthen iteration_context in engineer prompt (5 strict surgical edit rules, placed before main prompt)

### Phase 15 — Consumer Frontend v2 (✅ Completed Feb 2026)
- Copied and wired Projects/frontend to repo as frontend-consumer (port 3002)
- Connected to Flask backend via orchestrator.ts service layer
- Real iframe preview with desktop/mobile viewport toggle
- **Versions page (THE MOAT)** — timeline + split panel + live preview per version
- Restore version functionality from versions timeline
- File viewer (Code tab) wired to real /api/projects/:id/versions/:v/files
- Non-technical wording pass (Brief, Build Plan, What Was Built, Publish)
- Korean/English language toggle with i18n.ts translation system (30+ keys)
- CORS allowlist updated for ports 3001 and 3002

### Phase 15.1 — Repo Cleanup (✅ Completed Feb 2026)
- Removed apps/offline-vite-react (unused old frontend)
- Added node_modules/, dist/, .venv/, .claude/ to .gitignore
- Merged enterprise-ui branch into main
- Deleted enterprise-ui local branch

### Phase 15.2 — Consumer Frontend Polish (✅ Completed Feb 2026)
- Renamed all "ai-dev-team" references to "Archon" (package.json, metadata, HTML, overlays)
- Versions timeline newest first (removed incorrect reverse, matching API DESC order)
- Versions right panel glow effect on iframe container
- Hide restore button on current/latest version (maxVersion guard)
- Version card glow/contrast polish (darker bg, indigo ring, gradient overlay on selected)
- Logo split corrected: "Arch" + "on" with violet accent
- Full Korean i18n coverage: sidebar (9 strings), logs tab, status badges, agent messages, chat suggestions
- Fixed versions preview URL bug (version field vs version_number mismatch with API)

### Phase 15.3 — Consumer UX Bug Fixes (🔧 Partially Complete Feb 2026)
- Reset localPrd/localPlan/localTasks/previewVersion on projectId change (stale data across project switches)
- Removed opacity-0/opacity-100 transition on workspace div (iframe invisible after build completes)
- Progress bar restored to smooth sessionStorage animation (minor rapid-navigation edge cases remain)
- Expanded getTechColor to match 7 keyword categories (frontend/backend/database/state/ml/hosting/styling)
- Tech map rendering handles no-colon entries (natural-language PRD format)
- Engineer prompt: added MOCK DATA REQUIREMENT block (no more empty-state generated apps)
- Failed projects no longer show progress bar overlay
- Code tab fixed: reads data.tree from /files endpoint (was reading data.files)
- Preview iframe regression: sometimes reverts to placeholder after build — pending fix


## Phase 15.4 - Enterprise UI (frontend) COMPLETED Feb 27, 2026

### What was built
- Copied Lovable-generated Enterprise design (archon-v4) to frontend/
- Vite + React + TypeScript + Tailwind + shadcn/ui running on port 8080
- 4-theme system foundation (Enterprise Light/Dark, Studio Light/Dark)
- Korean/English language toggle with localStorage persistence

### API Wiring Completed
- Projects page connected to real Flask API with 3s polling
- Fixed N+1 query - added version_count to Project.to_dict() in models.py
- Project row selection with shared selectedProjectId state
- Shared selectedVersion state flows between Versions, Artifacts, Navbar
- VersionsView: real versions list + real iframe preview per version
- ArtifactsView: real Brief (PRD), Plan, Code, Tasks, Logs
- Navbar: real project name + version in breadcrumb
- Favicon: lightning bolt SVG + Archon - Enterprise Build title

## Phase 15.5.S - Studio Dashboard Review (✅ Feb 28, 2026)
- Stats bar and Recent Activity feed were prototyped then reverted — not shipping
- Studio Projects page intentionally kept minimal: project count cards (Total/Running/Completed/Failed) + search/filter + full-width table
- Enterprise (frontend) retains its own stats bar and activity feed via `/api/stats` and `/api/activity` endpoints

## Phase 16 — UI Parity, Auth & Polish (🔧 In Progress Feb 2026)

### 16.2 — Branding (✅ Complete Feb 28, 2026)
- ✅ Tab titles: "Archon - Studio Build", "Archon - Consumer Build"
- ✅ Hexagon logo in frontend and frontend-consumer
- ✅ Hexagon SVG favicon in frontend and frontend-consumer
- ✅ load_dotenv fixed to always load backend/.env

### 16.4 — Watson STT/TTS for Enterprise (✅ Complete Feb 28, 2026)
- ✅ Mic (STT) + speaker (TTS) buttons in frontend pipeline
- ✅ Fixed WATSON_TTS_API_KEY / WATSON_STT_API_KEY env var mismatch

## Phase 15.5 - Enterprise UI Polish (🔧 IN PROGRESS)

### Completed
- ✅ Checkbox UX fix — no longer triggers row navigation
- ✅ Stats bar wired to real project counts (total/running/completed/failed)
- ✅ Activity feed wired to real recent executions with collapse/expand
- ✅ Avg build time stat with fallback for missing data
- ✅ Publish and Download buttons wired to real endpoints
- ✅ Pipeline tab — full chat UI with conversation panel, input bar, agent status cards
- ✅ Pipeline tab — /chat (conversational) and /iterate (build) endpoints wired
- ✅ Pipeline tab — chat history loaded from DB on project switch
- ✅ Pipeline tab — live output log panel with auto-scroll
- ✅ Replaced Sparkles icon with Zap (lightning bolt) to match Archon branding
- ✅ Added missing i18n keys for pipeline UI (designAgent, send, noMessages, etc.)
- ✅ New Project modal (Name + Description → POST /api/projects, auto-selects and opens Pipeline tab)
- ✅ "What Was Built" summary — real file + image counts from backend (e.g. "2 code files · 3 images generated")
- ✅ Backend returns images_generated count from last_design_assets.json per version
- ✅ VersionsView files changed count uses real files_generated from API
- ✅ ArtifactsView Code tab — fixed height, independent scroll for file tree and code viewer
- ✅ WelcomeBanner — live backend health check (green/red dot with 10s polling)
- ✅ i18n keys added: backendOffline, projectName, projectDescription, creating, create, cancel
- ✅ Artifact cards (Brief/Plan/Code) in VersionsView navigate to Artifacts tab with correct sub-tab pre-selected
- ✅ Code tab scrollbars fixed — outer grid overflow:hidden with calc height, pre overflow:auto, minWidth:0
- ✅ Renamed "Running" → "Building" (EN) / "빌딩 중" (KO) across i18n and ProjectTable
- ✅ Pipeline header status badge — colored rounded-full pills (blue/building, emerald/completed, red/failed, gray/idle)
- ✅ Agent pipeline status persists after reload — reads DB status (success/failed/running)
- ✅ Logs saved for successful builds (backend app.py)
- ✅ Backend health indicator — red dot + "Backend offline" when Flask unreachable
- ✅ Status badge colors — green/red/blue pills in Pipeline header and Projects table
- ✅ Search filter on Projects page — client-side case-insensitive name filtering
- ✅ Red dot pulse animation on "Backend offline" indicator (WelcomeBanner)
- ✅ Removed Description field from New Project modal (name only, sends empty string)
- ✅ Pipeline tab no longer auto-scrolls to bottom on initial load (guarded by ref + timer)

### Remaining work
- ✅ Live output + agent pipeline no longer bleeds across projects (pipeline state resets on project switch)
- ✅ Chat messages persist via sessionStorage keyed by project ID (survives tab/project switching)
- ✅ Pipeline tab scroll-to-top fixed (container ref + triple scroll target)
- ✅ JSON repair bug — fixed with json_repair + char-walking backslash fixer

## Phase 16 — UI Parity, Auth & Polish (🔧 In Progress Feb 2026)

### 16.2 — Branding (✅ Complete Feb 28, 2026)
- ✅ Tab titles: "Archon - Studio Build", "Archon - Consumer Build"
- ✅ Hexagon logo in frontend and frontend-consumer
- ✅ Hexagon SVG favicon in frontend and frontend-consumer
- ✅ load_dotenv fixed to always load backend/.env

### 16.4 — Watson STT/TTS for Enterprise (✅ Complete Feb 28, 2026)
- ✅ Mic (STT) + speaker (TTS) buttons in frontend pipeline
- ✅ Fixed WATSON_TTS_API_KEY / WATSON_STT_API_KEY env var mismatch

### 16.3 — Studio Feature Parity (✅ Complete Feb 28, 2026)
- ✅ Projects page kept minimal by design
- ✅ Korean/English toggle in Studio navbar (i18n.ts + LanguageContext + KO/EN pills)
- ✅ Studio Projects table column sort — clickable headers, ↑/↓ active indicator (Feb 28, 2026)
- ✅ Build Details card in Studio Pipeline page — enterprise stat row (Lucide icons, Vercel-style, no emojis) (Feb 28, 2026)
- ✅ Full Korean i18n — Studio + Enterprise all static strings translated (Feb 28, 2026)

### 16.1 — Bug Fixes (✅ Complete Feb 28, 2026)
- ✅ Enterprise chat persistence after Flask restart (Feb 28, 2026)
- ✅ Studio + Enterprise chat shared when switching design modes (Feb 28, 2026)
- ✅ Global build lock — friendly banner + chat reply, correct text (Feb 28, 2026)
- ✅ Enterprise chat scroll to bottom on load (Feb 28, 2026)
- ✅ Studio agent cards restore green on load + on project switch (Feb 28, 2026)
- ✅ Enterprise "Failed" badge suppressed during active build (Feb 28, 2026)
- ✅ EngineerAgent JSON repair — json_repair + char-walking backslash fixer (Feb 28, 2026)
- ✅ Live output logs restored after Flask restart (Feb 28, 2026)
- ✅ Build Details tokens/cost working (Feb 28, 2026)
- ✅ Studio build details stat row displays after build completes (Feb 28, 2026)
- 🔴 Live output logs still global (execution_state is server-wide — architectural fix needed)

### 16.5 — Authentication (✅ Complete Mar 3, 2026)
- ✅ Sign up / Login pages — Studio + Enterprise
- ✅ JWT + protected routes — AuthGuard on both frontends
- ✅ User-scoped projects (owner_id)
- ✅ Cross-origin token handoff via ?token= param
- ✅ JWT blacklist logout — server-side token invalidation
- ✅ Google OAuth — Studio + Enterprise
- ✅ Concurrent pipeline — per-project execution state

### 16.6 — Planner Archetype Expansion (✅ Complete Feb 28, 2026)

### Phase 17 — IBM Governance & NLU Integration (✅ Complete Mar 1, 2026)

#### 17.1 — Watson NLU Pre-Pipeline Analyzer (✅ Complete Feb 28, 2026)
- ✅ Watson NLU analyzes user prompt before PM Agent
- ✅ Extracts: sentiment, domain keywords, categories
- ✅ Smarter routing: frustrated sentiment (score < -0.5) → empathetic chat, not build
- ✅ NLU keyword context appended to project_context for classify_intent
- ✅ Graceful fallback when WATSON_NLU credentials missing (enabled=False, no crashes)
- IBM credential: WATSON_NLU_URL + WATSON_NLU_API_KEY in backend/.env ✅

#### 17.3 — Credit System (✅ Complete Feb 28, 2026)
- ✅ 1 credit = 2,500 tokens, minimum 1
- ✅ credits_used column on Execution model
- ✅ Credits calculated + saved on pipeline completion
- ✅ Build Details: credits used + model + duration (hides raw cost)
- ✅ Studio + Enterprise both display credits correctly
- ✅ Build Agent upgraded to claude-sonnet-4-6 (Feb 28, 2026)
- ✅ model_used display updated to "Claude Sonnet 4.6" (Feb 28, 2026)
- ✅ Navbar credit counter wired to real balance via /api/credits/balance (Feb 28, 2026)
- ✅ Build Details: "12 credits · 488 remaining" format (Feb 28, 2026)
- 🔴 Plan tiers: Starter 100/mo, Pro 500/mo, Agency unlimited (Phase 18 scope)
- ✅ /api/credits/balance endpoint — wired to navbar in Enterprise + Studio
- ✅ Enterprise BuildDetailsCard live refresh post-build (Feb 28, 2026)

#### 17.2 — Governance Agent (AI Factsheets) (✅ Complete Mar 1, 2026)
- ✅ GovernanceAgent runs after every successful pipeline completion
- ✅ Structured Factsheet per version: models used, tokens, cost, duration, archetype, quality indicators, compliance flags
- ✅ governance_log TEXT column on Execution model (safe ALTER TABLE migration)
- ✅ Factsheet saved to disk (last_factsheet.json) + DB (governance_log JSON)
- ✅ Governance sub-tab in Artifacts page — Enterprise (frontend) + Studio (frontend-studio/)
- ✅ Empty state message for old builds pre-dating GovernanceAgent
- ✅ /api/projects/<id>/versions/<ver>/factsheet endpoint (disk-first, DB fallback, 404 graceful)
- ✅ Korean/English i18n keys added in both frontends
- ✅ Watson NLU prompt quality scoring (0-100) — powered by IBM Watson NLU API (Mar 1, 2026)
- ✅ Build confidence scoring (0-100) — computed from files, archetype, images, speed (Mar 1, 2026)
- ✅ Human Review Required flag auto-triggers when prompt or build score < 50 (Mar 1, 2026)
- ✅ Factsheet v1.1 — scoring section added to existing layout (non-destructive)
- ✅ Governance scoring logic fixed — removed sentiment, design assets, build speed as gameable metrics (Mar 1, 2026)
- ✅ Governance UI polish — capitalization, layout, spacing, font sizes throughout factsheet (Mar 1, 2026)
- ✅ Watson NLU added to Model Registry in factsheet (Mar 1, 2026)
- ✅ Dashboard icon colors — Sparkles text-purple-400, Shield text-blue-400 (Mar 1, 2026)
- ✅ Backend build_confidence key fix in dashboard_stats() (Mar 1, 2026)
- ✅ PDF export — Client PDF + Internal PDF via WeasyPrint (Phase 17.4)
- ✅ 17.5 Delivery Readiness Gate — Quality Tier badges + inline metadata + PDF header placement (Mar 1, 2026)
- 🔴 Cross-run analytics endpoint: /api/governance/summary (future)
- Resume value: governed, auditable AI pipeline with IBM Watson scoring — rare even among senior IBM AEs

#### 17.3 — Dashboard Governance Metrics (✅ Mar 1, 2026)
- ✅ Replaced "Pipelines Today" with Avg Prompt Score (Sparkles icon, purple, /100 suffix)
- ✅ Replaced "Lines Generated" with Avg Build Score (Shield icon, blue, /100 suffix)
- ✅ GET /api/dashboard/stats endpoint — averages prompt + build scores from governance_log
- ✅ Nulls skipped — pre-v1.1 builds show "—" not 0
- ✅ Enterprise dashboard (frontend WelcomeBanner) updated
- ✅ Studio had no equivalent header cards — no changes needed

#### 17.4 — Dual PDF Export (✅ Complete Mar 1, 2026)
- ✅ Two buttons on Governance tab: "Download Client PDF" + "Download Internal PDF"
- ✅ WeasyPrint HTML→PDF renderer (enterprise-grade, pixel-perfect CSS rendering)
- ✅ GTK3 runtime installed on Windows for WeasyPrint support
- ✅ Client PDF: Archon cover bar, shield, project name, brief, build plan, AI models, build output, compliance. No scores, no tokens, no cost.
- ✅ Internal PDF: all client content + pipeline details, quality scoring with methodology note, credits+tokens, build score breakdown
- ✅ Scores displayed at top with big numbers, grade badges (green/amber/red), IBM Watson NLU + Archon Engine attribution
- ✅ Verified (green) + Auditable (blue+shield) enterprise trust badges in header
- ✅ Audit Trail, Version Controlled, AI Governed, Immutable Record trust strip
- ✅ Human review warning box — different wording for client vs internal
- ✅ Cryptographic/repetitive wording removed — clean enterprise copy
- ✅ Dark navy header (IBM enterprise aesthetic), hexagon logo
- ✅ Solves Phase 8.2 client audit trail requirement

#### 16.6 — Planner Archetype Expansion (✅ Complete Feb 28, 2026)
- ✅ Expanded planner.txt from 10 → 25 archetypes
- ✅ Added render_path A/B field for Tailwind vs Raw CSS routing
- ✅ Layout + content contracts for all 15 new archetypes
- ✅ Existing 10 archetypes untouched

---

## Phase 19 — Product Tour & Onboarding Walkthrough (🔴 Deferred)

First-time user guidance system. Pattern and scope TBD after beta user testing.

**Memo (Mar 1, 2026):** Deferring implementation until after initial user testing.
Will recruit 3-5 beta users to identify where they actually get stuck — rather than
guessing. Tour design will be driven by real friction points, not assumptions.

- Enterprise users may only need a minimal welcome modal + "?" help button
- Consumer users may need a full spotlight tour with Korean i18n
- Pattern choice (modal overlay vs spotlight tooltip) decided post-testing

### Planned sub-phases (scope pending user research)
- 🔴 19.1 Enterprise (frontend) — welcome moment + optional per-page tips
- 🔴 19.2 Studio (frontend-studio/) — minimal, same pattern as Enterprise
- 🔴 19.3 Consumer (frontend-consumer) — fuller guidance + Korean i18n

**Tech candidate:** Shepherd.js (spotlight tooltips, React-compatible, free)
**Revisit:** After first round of beta user sessions

---

## Phase 18 — Unified Auth + Plan-Based UI Routing (🔴 Planned)

**Business model:** Two plans, two UI experiences. One login, one backend.

| Plan | UI | Features |
|------|----|---------|
| Consumer | frontend-consumer (simplified) | Light theme only, standard builds, version history |
| Enterprise | frontend or frontend-studio/ (power) | Light + Dark mode, Studio or Enterprise design toggle, advanced pipeline controls |

**Flow:**
- User signs up → picks Consumer or Enterprise plan
- Routed to correct UI automatically based on plan
- Enterprise users can toggle between Studio (frontend-studio/) and Enterprise (frontend) designs
- Upgrade path: Consumer → Enterprise unlocks full UI switcher
- Same Flask backend serves both

**Key principle:** Consumer UI is simplified for non-technical clients. Enterprise UI is for agencies and power users who need full audit trail, pipeline controls, and theme flexibility.

- 🔴 18.1 Landing/pricing page with plan selector (Consumer vs Enterprise)
- 🔴 18.2 Auth gates: Consumer login → frontend-consumer, Enterprise login → frontend
- 🔴 18.3 Enterprise design switcher (Studio ↔ Enterprise toggle in navbar)
- 🔴 18.4 Plan-aware credit limits (Consumer: 100/mo, Enterprise: 500/mo)
- 🔴 18.5 Upgrade flow: Consumer → Enterprise upsell modal

---

## ✅ Parallel DALL-E Image Generation (Mar 1, 2026)
- `agents/design_agent.py` — replaced sequential for loop with `concurrent.futures.ThreadPoolExecutor(max_workers=4)`
- All images generate simultaneously — confirmed in Flask terminal
- Significant build time reduction for image-heavy projects
- Merged via PR from `feat/parallel-image-generation`

## ✅ Stuck Build Reset Button (Mar 1, 2026)
- `POST /api/projects/<id>/reset-build` — marks stuck running execution as failed in DB
- Reset button in Enterprise + Studio pipeline chat — appears after 8 min build with no completion
- Red filled button, hidden during normal operation
- Merged via PR from `feat/reset-button`

## ✅ UI Polish — Governance Shield Blue (Mar 1, 2026)
- Shield icon `text-blue-500` in Governance tab + factsheet header — Enterprise + Studio, light + dark mode
- Hexagon logo `text-blue-500` in light mode, `text-primary` in dark mode — Enterprise + Studio

## ✅ UI Polish — Hexagon Icons + Emoji Cleanup (Mar 1, 2026)
- Replaced all Zap/lightning bolt icons in Studio (frontend-studio/) with Archon hexagon SVG
- Replaced all Zap/lightning bolt icons in Enterprise (frontend/) with Archon hexagon SVG
- Replaced Bot icon in agent chat bubbles (Studio + Enterprise) with hexagon SVG
- Removed ⚡ emoji from "Got it! Starting the build now." agent reply — Studio + Enterprise
- Hexagon color: text-primary (blue) in both light and dark mode across all surfaces
- Files changed: pipeline-run.tsx, project-dashboard.tsx, PipelineStatus.tsx, ProjectTable.tsx, Index.tsx

## ✅ Korean i18n Polish (Mar 1, 2026)
- Studio Projects table: status badges now translated in KO mode
- Enterprise + Studio: date format yyyy.mm.dd in Korean mode
- Merged via PR from feat/ko-i18n-polish

## ✅ Phase 16.5 — Authentication (Complete Mar 3, 2026)
- ✅ Backend JWT auth — register, login, me, forgot-password, reset-password
- ✅ Google OAuth — Studio + Enterprise
- ✅ AuthGuard — redirects unauthenticated users to /login
- ✅ Login/Register/Forgot Password pages — dark split-layout, IBM Plex Sans
- ✅ Cross-origin token handoff via ?token= URL param
- ✅ JWT blacklist logout — server-side token invalidation
- ✅ User-scoped projects (owner_id)
- ✅ Concurrent pipeline — per-project execution state
- ✅ Studio ↔ Enterprise theme toggle button in navbar
- ✅ Folder rename refactor — frontend-v4→frontend, frontend→frontend-studio, frontend-consumer2→frontend-consumer

## ✅ DALL-E Content Filter Fallback (Mar 3, 2026)
- On content_policy_violation (error 400), retries with description-only prompt (character name stripped)
- Zell (FF8) and similar proper nouns now generate via fallback instead of failing

## ✅ Image Generation Regression Fix (Mar 3, 2026)
- iteration_context now only injected into EngineerAgent, not DesignAgent
- DALL-E prompt format restored to pre-Phase 14 quality
- Character likenesses accurate again (FF7 Cloud/Barrett confirmed)

---

## ✅ Phase 20.1 — Visual Reference Input (Mar 7, 2026)
- User attaches reference images (screenshots, mockups, inspiration) to prompt
- Images forwarded to Planner + Engineer + Design agents as vision context
- Gemini 2.5 Flash (Planner/Engineer/Design) supports vision input natively
- /iterate endpoint accepts multipart/form-data, saves to output/<pid>/v<ver>/references/
- Planner describes reference in plan context so Engineer knows target style
- Engineer receives images as inline Gemini vision parts to match layout/palette
- Design Agent uses Gemini vision to analyze reference before generating Imagen prompts
- Enterprise + Studio: Paperclip button, thumbnail strip, base64 image rendering in chat
- Backward compatible — builds without attachments work exactly as before

---

## Light Mode Contrast Fixes (✅ Complete Mar 9, 2026)
- Enterprise: All hexagon icons unified to `text-blue-600 dark:text-blue-500` across Navbar, ProjectTable, PipelineStatus, Index.tsx
- Studio: Same icon fix + navbar hover contrast + versions panel selected state + darkened muted-foreground CSS variable
- Google OAuth: Added localhost:8080 to authorized origins (console config, not code)
- Visually verified both frontends in light + dark mode

## Phase 22 — Consumer Frontend Overhaul (🔧 In Progress Mar 9, 2026)

Full rebuild of `frontend-consumer/` (port 3002) for non-technical agency clients.

**Phase A: Audit (✅ Complete Mar 9, 2026)**
Codex audited all consumer frontend files + ran build + tsc + live browser test.
Found 2 critical, 5 high, 5 medium issues + 7 feature gaps vs Enterprise/Studio.
Top blockers: no auth (JWT never sent), fake chat composer (never calls /iterate), developer-oriented UX.

**Phase B: Implementation (✅ Complete Mar 9, 2026)**
Codex rewrote consumer as indie-maker AI app builder (Lovable/v0 competitor positioning).
Prompt-first hero, founder-friendly copy, real chat/iterate API calls, auth headers, simplified settings.
7 bugs found and fixed during live testing: preview auto-refresh, tab data loading, light mode default, iteration quality. All verified working.
Consumer Restore Version works — Enterprise + Studio buttons need wiring (follow-up).

**Remaining phases:**
- B bug fixes (✅ Complete Mar 9, 2026)
- C: Auth + Seed Projects (✅ Complete Mar 9, 2026)
- D: Add Versions page (THE MOAT — timeline + preview + "what changed" narrative)
- E: Build Insights slide-up card (✅ Complete Mar 9, 2026)
- F: Mobile polish pass (responsive sidebar, project detail, preview iframe)

**Phase E: Build Insights — Post-Build Prompt Coaching Card**
Slide-up card appears on ProjectDetailPage after build completes. Shows prompt score, 2-4 actionable tips, and one-click "Apply suggestion" that pre-fills the iteration prompt. Non-blocking, collapsible, educational.
- Backend already exists: GET /api/projects/<id>/versions/<ver>/insights (Phase 21)
- Enterprise/Studio already have "Quality Recommendations" in Governance tab
- Consumer implementation: slide-up card below preview iframe on ProjectDetailPage
- Key UX: "Apply suggestion →" button pre-fills iteration input with the tip text
- Progressive: shows prompt score so users see improvement over iterations
- Stickiness play: users come back to keep improving their prompt skills

**Phase C: Auth + Seed Projects (✅ Complete Mar 9, 2026)**
Conversion funnel: users build first, register after seeing results.
- Consumer: guest build → post-build register modal → link guest project to account ✅
- Seed projects: POST /api/seed creates 2 FF7 demo projects from real peak-quality output (projects 71 + 38) ✅
- Imagen character art (Cloud, Tifa, Barret) committed to backend/seed_data/ ✅
- Auto-seeds on first login (0 projects) across all 3 frontends ✅
- Asset URL rewriting at seed time, regression test, swappable seed data ✅
- Enterprise + Studio try-before-register: deferred (lower priority)

**Design principles:** Simple > powerful, business language, mobile-first, light mode default, no developer jargon. Core flow: Describe → Build → Review → Revise.

## Phase 21 — Build Insights (Prompt Coaching) (✅ Complete Mar 8, 2026)

Post-build suggestions that help users write better prompts. Positioned as intelligent platform feedback, not a tutorial.

**Consumer frontend** (primary target): "Build Insights" card — friendly, educational tone. Non-technical users benefit most from guidance on how to describe what they want.

**Enterprise frontend**: "Quality Recommendations" section inside Governance tab — professional framing. Agencies can show clients how to improve next iteration.

**Data sources (already available):**
- Governance Agent: prompt_quality_score (Watson NLU, 0-100)
- Governance Agent: build_confidence_score (0-100)
- Planner: ui_archetype, quality_target (key_sections, must_have_content, avoid)
- PRD: what user asked for vs. what was built

**Implementation plan:**
- 21.1 Backend: POST-pipeline analysis — compare PRD against quality_target to identify gaps
- 21.2 Backend: /api/projects/<id>/versions/<ver>/insights endpoint returning structured suggestions
- 21.3 Enterprise: "Quality Recommendations" section in Governance tab (GovernanceView)
- 21.4 Consumer: "Build Insights" card in Artifacts or chat panel
- 21.5 i18n: Korean translations for all insight strings

**Design principles:**
- Max 3-4 suggestions per build (not overwhelming)
- Specific and actionable ("Add a color palette" not "Be more descriptive")
- Tied to real scoring data, not generic tips
- Never blocking — informational only, user can ignore

**Implementation (Mar 8, 2026):**
- ✅ 21.1 InsightsAgent (agents/insights_agent.py) — rule-based analysis of prompt length, color/font keywords, quality_target gaps, prompt score, domain hints
- ✅ 21.2 GET /api/projects/<id>/versions/<ver>/insights — returns { insights: [{ category, suggestion, priority }] }, reads from last_insights.json
- ✅ 21.3 Enterprise UI — "Quality Recommendations" section at bottom of Governance tab with category icons (AlignLeft/Palette/FileText/MessageSquare/Globe), priority badges (red/amber/gray), empty state with checkmark
- ✅ 21.4 Studio UI — matching section in Studio Governance tab, hardcoded English
- ✅ 21.5 i18n — 12 Korean translation keys for categories, priorities, section title/description/empty state
- Consumer UI deferred to full UX audit

## Eval Loop Optimization (✅ Complete Mar 10, 2026)
- Auth blocker fixed in eval/api_client.py — JWT auto-register/login for eval user
- 5-iteration overnight run across all 5 archetypes (dashboard, game, saas_landing, ecommerce, portfolio)
- Best scores: Ecommerce 88.5, Game 84.5, Portfolio 83.5, Dashboard 81.0, SaaS Landing 76.0
- Average: 82.7/100 (up from ~69.6 original baseline)
- Manual kit improvements (CSS + txt) for dashboard, game, saas_landing
- Score-only validation pass confirmed dimension-level improvements but prompt/kit tweaking hitting diminishing returns
- Conclusion: Next quality lever is Watson Discovery reference templates, not more prompt iteration

## Phase 23 — Watson Discovery Integration (✅ Complete Mar 10, 2026)

### 23.1 Expanded NLU — concepts, entities, prompt_richness fed into PM/Planner/Design agents
### 23.2 Discovery Client — 5 best builds ingested (ecommerce 88.5, game 84.5, portfolio 83.5, dashboard 81.0, saas_landing 76.0)
### 23.3 Pipeline Integration — Engineer queries Discovery for reference HTML/CSS on initial builds; eval auto-ingests 85+ scores

Learning loop: build → score → if 85+, ingest into Discovery → next build retrieves best reference → quality improves

New files: utils/watson_discovery.py, scripts/ingest_best_builds.py
Modified: agents/nlu_agent.py, agents/engineer_agent.py, agents/planner_agent.py, agents/design_agent.py, backend/app.py, eval/eval_runner.py

## Bug Fix Session (Mar 10, 2026)

- ✅ Quality Recommendations restored in Governance tab (Enterprise + Studio) — insights fetch with auth, category icons, priority badges (48d27ed)
- ✅ Imagen image rendering fixed — resilient asset resolver with multi-path fallback + prior version scan, preview URL normalization, nested path support (58a9f8f)
- ✅ Double NLU call eliminated — /chat forwards nlu_result to /iterate, skips re-analysis (d862863)
- ✅ Generated app interactivity — Zero Dead Buttons Policy in engineer_core.txt, planner quality_target interactivity dimension (18f0ce0)
- ✅ Notification sound fixed — AudioContext resume, pre-unlock on user gesture, transition-based triggers. Studio moved to global app-shell for chime on any page (61ab5b4, 1b10893)
- ✅ AuthGuard token expiry — validates JWT via /api/auth/me on mount, clears stale tokens, redirects to /login (d6b5d8d)

All 6 bugs resolved.

## Phase 24 — Asset Reuse Library (✅ Complete Mar 10, 2026)

Intelligent image fallback system that eliminates broken images and reduces Imagen costs.

**Problem:** Engineer Agent often creates more `<img>` slots than the Design Agent's generation cap allows (e.g. 12 image slots but only 5-10 generated). Excess slots show broken images.

**Solution:** When a generated HTML references an image that doesn't exist, pull a visually similar image from a library of previously generated assets instead of leaving it broken.

**Implementation:**
- ImageAsset SQLAlchemy model: filename, key, category, archetype, source_project_id, source_version, local_path, prompt
- 9 categories auto-detected from key name: hero_background, product_shot, character_portrait, lifestyle, collection, icon, pattern, abstract, other (prompt text fallback)
- Bulk ingestion: 872 images from 205 projects. Idempotent.
- Auto-ingest hook after Design Agent in pipeline
- Post-engineer filler: scans HTML for missing image refs, queries library by (category + archetype), copies best match
- Match priority: same archetype + same category > same category any archetype > same archetype any category

**Sub-phases:**
- ✅ 24.1 ImageAsset table + bulk ingestion + auto-ingest hook
- ✅ 24.2 Post-build missing image scanner + filler (utils/asset_filler.py)
- ✅ 24.3 Category detection (key heuristic + prompt fallback)
- 🔴 24.4 Admin UI (deferred)

Branch: `feat/asset-reuse-library`

**New files:** utils/image_asset_catalog.py, scripts/ingest_image_library.py, utils/asset_filler.py
**Modified:** backend/models.py, backend/app.py

