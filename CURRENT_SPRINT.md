# Current Sprint

## Branch Alignment — `feat/componentized-multi-run-experiments`

Short status update for the active branch:
- This branch was cut from `feat/componentized-builder-pipeline` after the March 15, 2026 dashboard/runtime recovery docs checkpoint so the validated builder work remains intact while scheduler experiments stay isolated.
- Added a tracked Stage 1 multi-run validation runner at `eval/run_componentized_validation.py` with bounded concurrency, isolated API clients per worker, lazy scorer-only imports, backend reachability checks that do not require auth bootstrapping, and per-archetype progress/result artifacts for smoke-run debugging.
- Added targeted regression coverage in `tests/test_run_componentized_validation.py` for preview-build fallback loading, backend health acceptance of 401, and result-file emission on build failure.
- March 15, 2026 bounded-parallel smoke-run status on this branch: `dashboard` (project 424 / execution 430) and `portfolio` (project 425 / execution 431) started within the same second, authenticated independently, created separate projects, and advanced through `pm`, `planner`, and `engineer` concurrently under `--max-parallel 2`, confirming that bounded parallel validation is viable locally across different projects.
- Extended Stage 2 in `backend/app.py` from hard rejection into opt-in queue admission: `/api/execute-task` and `/api/projects/<id>/iterate` now accept `enqueue_on_limit`, reserve queued work per project, expose `queued_pipelines`, `project_queued`, and `queue_position`, report queued work through `/api/execution-status` without breaking existing `RUNNING` consumers, and automatically dequeue the next job when a running slot is released.
- Extended the tracked multi-run harness to use the new backend path safely: `eval/api_client.py` can opt into queue-on-limit, and `eval/run_componentized_validation.py` now exposes `--enqueue-on-limit` so bounded parallel runs can wait for capacity instead of failing immediately when the backend cap is already saturated.
- Hardened the eval client against healthy queue wait: `eval/api_client.py` now treats queue wait separately from active build time, and `eval/run_componentized_validation.py` now exposes `--queue-timeout` so bounded parallel validation can tolerate backlog without misclassifying a queued job as a backend failure before it even starts running.
- Added queue telemetry to eval artifacts: `eval/api_client.py` now preserves trigger queue state, observed queue positions, queue wait seconds, and active run duration in `queue_telemetry`, while `eval/run_componentized_validation.py` writes that telemetry into per-archetype `result.json` files, adds an aggregate `queue_summary.json`, and surfaces both run-level and batch-level queue behavior in `summary.md`.
- Added a build-only smoke path to `eval/run_componentized_validation.py`: `--build-only` keeps project creation, build execution, preview-build inspection, and queue telemetry artifacts, but skips screenshots and scorer calls so queue-focused smoke runs do not pay the full scoring cost.
- March 15, 2026 queue-telemetry smoke evidence: under a forced single-worker backend cap (`ARCHON_MAX_CONCURRENT_PIPELINES=1`) with `--max-parallel 2 --enqueue-on-limit --build-only`, `dashboard` (project 427 / execution 432) ran immediately while `portfolio` (project 426 / execution 433) queued at position 1 for 330.7 seconds. The new `queue_summary.json` captured `observed_runs=1`, `average_queue_wait_seconds=330.7`, and `worst_queue_position=1`, confirming the eval artifacts are useful under real queued load even when preview builds later fail.
- Added preview-failure classification to `eval/run_componentized_validation.py`: result artifacts and `summary.md` now preserve a structured `preview_failure` block so build-only smoke runs report the actual preview blocker instead of collapsing everything to `preview_unavailable`. The March 15, 2026 queued smoke failure is now classified as `npm_cache_eperm`, which matches the shared `C:\\Users\\mredw\\AppData\\Local\\npm-cache\\_cacache\\tmp\\...` `EPERM` seen in projects 426 and 427 during `npm.cmd install`.
- Isolated componentized preview installs to a workspace-local npm cache in `utils/componentized_runtime.py`: `build_componentized_preview()` now writes `npm_config_cache` / `NPM_CONFIG_CACHE` to `<code_dir>/.npm-cache`, and `.npm-cache` is excluded from editable-context scans so cache files cannot leak into later repair prompts.
- March 15, 2026 direct preview concurrency smoke evidence: two temp componentized workspaces under `.tmp-preview-concurrency` ran `build_componentized_preview()` concurrently and both completed successfully after the cache isolation change, confirming that the earlier queued-run `npm_cache_eperm` was a shared-cache contention issue rather than a fundamental parallel-preview limitation.
- Added a minimal durable recovery layer on top of the queue path: pending executions already persisted in the DB can now be reconstructed into scheduler jobs on the first real backend request after restart, then requeued and dispatched up to the current worker cap. That recovery is skipped in test mode and can be disabled with `ARCHON_DISABLE_PIPELINE_RECOVERY`.
- Added queue-depth protection in `backend/app.py`: `ARCHON_MAX_QUEUED_PIPELINES` now bounds queued work, scheduler snapshots expose `max_queued_pipelines`, and overflow returns a distinct `queue_limit` rejection instead of allowing the queue to grow without bound.
- Added a Stage 3 ownership checkpoint in `backend/app.py` and `backend/models.py`: executions now persist scheduler claim metadata (`scheduler_worker_id`, `scheduler_claimed_at`, `scheduler_heartbeat_at`), workers atomically claim `pending` executions before doing pipeline work, log emission refreshes the DB heartbeat for the owning worker, stale `running` executions can be failed by heartbeat timeout instead of being left orphaned forever, and successful/error completions clear the claim metadata cleanly.
- Removed the old boot-time behavior that force-marked every `running` execution as failed inside `init_db()`. Restart recovery is now heartbeat-based in the scheduler layer instead of a blanket database reset on import.
- Extended the scheduler to reuse the persisted `pending` queue beyond startup: when a local worker slot opens, `backend/app.py` now re-scans DB-backed pending executions, adopts the oldest eligible job into the local queue, and dispatches it immediately instead of waiting for a backend restart. `/api/execution-status` also now clears stale local queued state when the DB shows another worker already claimed that execution, so queue position does not stay stuck after cross-process pickup.
- Added a lightweight background scheduler poller in `backend/app.py`: after the first real request bootstraps the scheduler, each backend process can now periodically run maintenance to dispatch any local queued work, fail stale `running` executions by heartbeat timeout, and adopt oldest persisted `pending` executions even when this process did not just release a slot. The poll interval is controlled by `ARCHON_SCHEDULER_POLL_INTERVAL_SECONDS`, and the poller can be disabled with `ARCHON_DISABLE_SCHEDULER_POLLER`.
- Added DB-ground-truth fallback for `/api/execution-status`: if a backend process has no local in-memory state for a project, it now falls back to the active-head execution in the database and reports `RUNNING` or `COMPLETED` from that record instead of incorrectly returning `FAILED`. That closes a real multi-process blind spot for status polling across workers after restarts or cross-node routing.
- Moved scheduler snapshots and route admission closer to DB truth: `backend/app.py` now combines local reservations with persisted `Execution.status` rows when reporting `active_pipelines`, `queued_pipelines`, `project_running`, and `project_queued`, and `/api/execute-task` now uses that durable view for same-project overlap, global worker-limit checks, and queue-limit checks. That closes another multi-process hole where a second backend could previously ignore running or queued work owned by a different process.
- Moved execution claiming earlier in the lifecycle: `backend/app.py` now claims the execution before starting a worker thread, and queued/direct starts skip launching a duplicate local thread if another process already claimed that pending execution. `run_full_pipeline_async` now accepts a preclaimed path so the worker does not waste time double-claiming a job it already owns.
- Reordered scheduler maintenance around durable queue order: `backend/app.py` now adopts persisted `pending` executions before dispatching local queued work, and queued jobs carry `created_at` so recovered older executions are inserted ahead of newer local queue entries. That means the oldest DB-backed pending execution now wins when a worker slot opens, instead of whichever process happened to have a newer local queue item ready first.
- Tightened worker-cap enforcement during dequeue and maintenance: `backend/app.py` now checks DB-aware scheduler snapshots before dispatching local queued jobs or adopting persisted pending work, so one backend will not start extra queued pipelines just because its own process-local running count is low while another backend already occupies the global cap.
- Fixed direct-start rollback when prestart execution claiming fails: `/api/execute-task` and `/api/projects/<id>/iterate` now clean up the just-created pending execution, restore project/head state, and return a scheduler busy response instead of incorrectly reporting `"started"` when no worker thread was actually launched.
- Added durable DB slot leases for actual execution starts: `backend/models.py` now persists `pipeline_slot_leases`, and `backend/app.py` now acquires a unique slot row before flipping an execution from `pending` to `running`. That gives competing backends a real DB-backed contention point for worker slots, and success/error/stale/reset cleanup now releases the lease with the execution claim.
- Extended scheduler snapshots and route admission to trust slot leases too: `backend/app.py` now treats slot-leased pending executions as active capacity instead of queued capacity, so same-project overlap and global worker-limit checks are lease-aware before another route tries to start work.
- Reduced scheduler dependence on local queue bootstrap: `dispatch_queued_pipelines()` can now query the oldest persisted `pending` executions directly from the database and adopt them into local worker starts even if the process never rebuilt or retained a matching in-memory queue entry.
- Reduced scheduler dependence on local queue ordering too: `dispatch_queued_pipelines()` now starts work from the durable oldest-`pending` execution set first, removes any matching in-memory queue entries once selected, and only falls back to purely local queue jobs when there is still spare capacity after the DB-backed picks. That closes another path where a newer local queue entry could otherwise outrank an older persisted pending execution.
- Hardened the scheduler regression fixtures for the shared SQLite test database: `backend/tests/test_execution_limits.py` now prunes stale `limits-%@archon-test.com` users, executions, projects, and slot leases before and after the suite so orphaned timed-out test runs do not poison durable queue ordering assertions.
- Added backend scheduler regression coverage in `backend/tests/test_execution_limits.py` for queued admission, dequeue dispatch, persisted pending-job recovery, direct durable-queue adoption without a local queue seed, recovery from missing local queue entries for a queued execution, direct oldest-pending-first dispatch even when a newer local queue entry exists, exclusive execution claims, durable slot-lease saturation during execution claim, slot-leased pending route admission, stale-running recovery with lease cleanup, durable-queue adoption on slot release, stale queued-status cleanup, background maintenance adoption, DB-backed active-head status fallback, DB-backed route admission/queue limits, prestart execution claiming, oldest-pending-first dispatch ordering, DB-running worker-cap saturation during dispatch/maintenance, and direct-start rollback before thread launch, plus targeted runner coverage in `tests/test_run_componentized_validation.py` for forwarding the queue flag. Focused `py_compile`, `unittest`, and the runner `--help` path passed on March 15, 2026.
- Current branch capacity is still intentionally modest: `backend/app.py` defaults `ARCHON_MAX_CONCURRENT_PIPELINES` to `2`, so only two pipelines run at once across all accounts by default, while `ARCHON_MAX_QUEUED_PIPELINES` defaults to `20`, so additional requests can wait in queue but are not active worker executions.
- Timeout behavior is now split cleanly between admission and completion: `/api/execute-task` and `/api/projects/<id>/iterate` return quickly with `started` or `queued` because the actual pipeline runs on background worker threads. On the client side, queue wait is now budgeted separately from active build time in `eval/api_client.py`, and the componentized validation runner defaults `--queue-timeout` to 1800 seconds so queued work is less likely to be misreported as a backend timeout before execution begins.
- March 16, 2026 eval-runner checkpoint: `eval/run_componentized_validation.py` now creates the results directory before managed backend startup, and managed backend launch failures now surface backend stdout/stderr tails instead of collapsing to a bare connection refusal. Focused regression coverage landed in `tests/test_run_componentized_validation.py`, and `py_compile` plus `unittest` passed.
- March 16, 2026 portfolio recovery checkpoint: broader runtime normalization in `utils/componentized_runtime.py` now repairs malformed `tsconfig.json` leading commas, repeated orphan `currentTarget` splits, orphan comment-close bleed inside string literals and URLs, comment-tail split identifiers, and stray filename labels such as `App.tsx` left behind after comments. That recovered portfolio from preview-build failure to a visible scored run: `.tmp-portfolio-build-smoke-20260316c` reached preview success, `support_module_gate_v38_portfolio_preview_recovery_baseline` scored `10.0` with a black screen, and `support_module_gate_v39_portfolio_runtime_recovery` improved to `51.5`.
- March 16, 2026 dashboard refresh checkpoint: `support_module_gate_v37_dashboard_branch_refresh` scored `69.5`. The branch is no longer blocked on dashboard preview stability, but the current dashboard prompt lineage on this branch still trails the stronger builder-branch benchmark and needs more work on typography hierarchy, surface depth, and sidebar tone rather than additional scheduler changes.
- March 16, 2026 ecommerce recovery checkpoint: the branch now has stronger image-heavy shell guidance plus additional componentized runtime recovery for swallowed JSX tag boundaries, Alpine-style directive bleed, malformed self-closing `Link` wrappers, stray orphan `}` lines inside JSX, and design-kit CSS import precedence. Those fixes turned the commerce path back into a scoreable preview: `support_module_gate_v40_ecommerce_branch_refresh` landed at `65.5`, two intermediate reruns exposed new JSX syntax families before preview, and `support_module_gate_v43_ecommerce_link_brace_repair` recovered preview success at `69.5`. The remaining ecommerce gap is now mostly design polish, not broken build/runtime syntax.
- March 16, 2026 game branch refresh checkpoint: `support_module_gate_v44_game_branch_refresh` scored `88.0`, beating the prior benchmark baseline of `84.5` by `+3.5`. Saved preview references for later summaries: local preview URL `http://127.0.0.1:5000/api/preview/440/1`, viewport screenshot `eval/results/support_module_gate_v44_game_branch_refresh/game/screenshot.png`, and full-page screenshot `eval/results/support_module_gate_v44_game_branch_refresh/game/screenshot_full.png`.
- March 16, 2026 game benchmark promotion checkpoint: the `88.0` FF8 run is now registered in `eval/archetype_benchmarks.json` as `branch-ff8-garden-archive-20260316`, the game eval baseline in `eval/run_componentized_validation.py` now points at that branch benchmark, and the local reference loader now accepts componentized benchmark source (`src/App.tsx` plus combined CSS) instead of only legacy `index.html`/`style.css`.
- March 16, 2026 game asset-guard checkpoint: tightened componentized design-asset instructions plus game-specific runtime fallback/polish handling so game pages stop inventing missing `generated-assets/*` files, missing `.svg` slots get safe local placeholders instead of broken bytes, and hero scroll/typography selectors are normalized for fan-page shells. Focused validation passed in `tests.test_componentized_runtime`.
- March 16, 2026 Pokemon rerun checkpoint: `support_module_gate_v47_game_pokemon_asset_guard` improved the Pokemon fan-page prompt from `77.0` to `83.5`. The new run generated and referenced a clean seven-asset set (`hero_background`, three portraits, `evolution_showcase`, `region_map`, `gym_badge_collection`) instead of inventing many missing filenames. Saved preview reference: `http://127.0.0.1:5000/api/preview/443/1`, screenshots in `eval/results/support_module_gate_v47_game_pokemon_asset_guard/game/`.
- March 16, 2026 Zelda probe note: `support_module_gate_v48_game_zelda_asset_guard` is not a promotion candidate. It did confirm the new asset contract path stays repo-safe by generating and referencing only six local assets with no missing-file sprawl, but the visual output collapsed to `45.5` and should be treated as a rejected variant, not a new benchmark.
- March 16, 2026 game follow-up runtime checkpoint: a fresh FF8 control rerun exposed another componentized preview failure family where generated files like `HeroSection.tsx`, `CharacterSection.tsx`, and `WeaponShowcase.tsx` were imported through stale aliases such as `./components/Hero`, `./components/CharacterCards`, and `./components/WeaponSection`. `utils/componentized_runtime.py` now rewrites those missing local imports to discovered component files before preview build, and focused regression coverage landed in `tests/test_componentized_runtime.py`.
- March 16, 2026 game shell-polish checkpoint: the game runtime/prompt path now forbids remote franchise badge or sprite fetches, rewrites remote badge URLs in badge-object data to local generated badge SVG placeholders, and adds stronger hero CTA/scroll spacing so the scroll label stays centered below the buttons instead of hiding behind them. That preserved the preferred Pokemon shell while keeping the page repo-safe and non-broken.
- March 16, 2026 game consistency rerun checkpoint: the FF8 control rerun recovered to `86.5` at `http://127.0.0.1:5000/api/preview/666/1`, the structurally stronger Zelda rerun landed at `80.5` at `http://127.0.0.1:5000/api/preview/668/1`, and the preferred Pokemon shell remains the rebuilt `667/1` preview after the local badge assets and scroll-indicator fixes were reapplied to the accepted layout. README showcase assets were refreshed from those accepted March 16, 2026 game runs.
- March 16, 2026 game concurrency-and-interaction checkpoint: the game runtime/prompt path now has stronger guardrails against dead card CTAs and literal map placeholder text, plus broader tsconfig JSON normalization and a stale-result-aware `/api/execution-status` fallback when a completed artifact exists. A live concurrent pair completed successfully on `678/1` (Halo) and `679/1` (Metroid), and both shipped working mid-page detail interactions instead of inert buttons. README showcase order now promotes Halo to the lead game demo and swaps the older second FF8 slot for Metroid.
- March 16, 2026 dashboard + ecommerce transfer checkpoint: this branch now carries stronger dashboard/ecommerce archetype guidance for meaningful click interactions, live support rails, resilient remote-image fallbacks, and composed tablet/mobile behavior, plus broader componentized runtime recovery for multiline natural-language comment bleed, orphan `*/` after array statements, next-line JSX text bleed, and safe `react-feather` dependency syncing. The latest live concurrent rerun pair proved the backend still overlaps two non-game builds cleanly: ecommerce recovered to a real successful preview at `http://127.0.0.1:5000/api/preview/688/1`, while dashboard also completed at `http://127.0.0.1:5000/api/preview/689/1` but still shows residual generated corruption (`*/ Search...` plus malformed SVG path data), so the concurrency path looks healthier than the archetype polish/runtime quality on dashboard.
- March 16, 2026 image-and-dialog polish checkpoint: game and ecommerce outputs now rewrite remote image URLs such as `via.placeholder.com` and Unsplash-style sources into local `generated-assets/*.svg` placeholders before preview build, even when `public/generated-assets` starts empty. The game runtime also converts `alert()`-style CTA handlers into inline detail panels instead of browser popups. Live validation: `693/1` and `694/1` no longer depend on remote image hosts, and `695/1` opens Halo atlas logs inline rather than triggering a native browser dialog.
- March 16, 2026 componentized code-browser safety checkpoint: `build_file_tree()` in `backend/app.py` now hides runtime/install directories (`node_modules`, `dist`, `.npm-cache`) from version file trees so the three frontend code tabs do not try to browse componentized preview artifacts instead of source files.
- March 16, 2026 random-archetype quality probe (new prompt surfaces): `eval_runner` score-only pass across `editor`, `form`, and `fintech` (`project 454/455/456`) confirmed a major cross-archetype reliability gap on this branch. `editor` scored `11.5` and `form` scored `10.0` because both rendered placeholder-only outputs instead of real app UIs, while `fintech` reached `70.5` in that pass. This run is a merge blocker for app-quality claims beyond the previously tuned archetypes.
- March 16, 2026 concurrent quality probe after scorer dependency repair: three-way validation on `dashboard`, `fintech`, and `portfolio` (`project 457/458/459`) completed with real scoring under bounded parallelism and queue telemetry (`max_position=1`, queue wait `369.8s`). Runtime concurrency behavior held, but quality regressed relative to local baselines: dashboard `72.5` vs `81.0`, fintech `10.0` vs `83.5`, portfolio `58.5` vs `83.5`.
- March 16, 2026 frontend integrity smoke: production builds for all three frontends (`frontend`, `frontend-studio`, `frontend-consumer`) passed locally, so the immediate regressions are concentrated in generated app output quality and archetype generalization rather than frontend bundle integrity.
- Current non-architecture caveat: a live managed-backend bounded-parallel smoke now starts correctly, but same-second `/api/execute-task` contention can still return `429` instead of queueing under some races. That issue is documented and deferred while the active task stays focused on app quality, runtime recovery, and design polish rather than more backend changes.
- Current gap on this branch: bounded multi-run now has runner-side concurrency, queue-aware timeouts, queue telemetry artifacts, a build-only smoke mode, explicit preview-failure classification, workspace-local npm-cache isolation for preview installs, DB-aware backend admission control, an in-memory queue, DB-backed pending-job recovery, direct durable-queue adoption when local queue state is missing, DB-first dispatch ordering even when local queue state exists, queue-depth protection, DB-backed claim/heartbeat ownership, slot-release adoption of persisted pending work, background maintenance polling, DB-backed status fallback, prestart claim protection against duplicate worker threads, durable oldest-pending-first dispatch during maintenance, DB-aware worker-cap enforcement when dequeuing queued work, rollback of failed direct starts before a false `"started"` response escapes the API, durable DB slot leases at actual execution start, and lease-aware route admission for active capacity, but production-safe scaling still needs a queue/storage stack stronger than the current SQLite-based coordination model and queue ownership that is less dependent on per-process bootstrap state. The next non-architecture gap is end-to-end rerun stability: the preview-install cache collision is fixed at the runtime layer, so the next validation step is another full queued smoke through the backend/eval harness to confirm the same improvement on live pipeline-generated work.
- Branching decision (March 16, 2026): do not merge this branch into `main` yet for global quality. Use this branch as the stable infrastructure checkpoint, then continue app-quality work on a new child branch focused on design globalization (`feat/globalized-design-foundation`). Scope for that branch is family-based quality contracts and fallback shells that generalize across many archetypes, instead of archetype-by-archetype prompt tuning.
- March 16, 2026 `feat/globalized-design-foundation` checkpoint: started the first reusable globalization slice instead of more per-archetype tuning. Added `utils/design_families.py` with canonical-archetype and small-family routing (`data_dense`, `workspace`, `guided_flow`, `commerce`, `showcase`, `marketing`), injected shared family guidance into `agents/engineer_agent.py`, and extended `backend/app.py` so shell-polish prompts and local quality heuristics now understand workspace/guided-flow shells in addition to dashboard/fintech/ecommerce.
- March 16, 2026 runtime hardening on `feat/globalized-design-foundation`: `utils/componentized_runtime.py` now repairs two failure families found in the random-archetype probe: raw brace/object-literal code samples inside JSX `<code>/<pre>` blocks, and post-comment natural-language instruction bleed like `functions to adhere to output_files constraint` before real declarations. Regression coverage was added in `tests/test_componentized_runtime.py`, including new workspace/guided-flow quality checks, and the full `python -m unittest tests.test_componentized_runtime` suite passed locally.
- March 16, 2026 handoff status on `feat/globalized-design-foundation`: a fresh live rerun for `editor` + `form` was started after the runtime/test pass, but the user intentionally interrupted it before scoring completed. No new merge-quality numbers should be inferred from that aborted attempt; the next operator should rerun those live probes first.
- March 16, 2026 follow-up repair checkpoint on `feat/globalized-design-foundation`: the interrupted rerun still produced useful failing workspaces (`generated/460` editor, `generated/461` form). Additional runtime recovery now handles JSX code-template literals with nested backticks, multiline block comments with `//` note bleed, and JSX expression identifier splits like `{form */\nData...}`. After reapplying `ensure_componentized_workspace_support()` to those captured workspaces, both `generated/460/v1/code` and `generated/461/v1/code` completed `npm run build` successfully, so the specific editor/form syntax families uncovered by the interrupted probe are now covered by deterministic repair plus tests.
- March 17, 2026 data-dense repair checkpoint on `feat/globalized-design-foundation`: runtime support now also strips inline JSX attribute comments like `y={chartHeight + 15} /* note */`, repairs malformed SVG namespace URLs such as `xmlns="http:www.w3.org/2000/svg"`, normalizes invalid seven-digit hex color tokens, and replaces the run-on broken responsive CSS tail that was taking the captured dashboard probe down before preview. Focused regression tests were added for those cases, and reapplying `ensure_componentized_workspace_support()` to `generated/478/v1/code` is now enough to turn that previously broken dashboard workspace into a successful `npm run build`. `generated/476/v1/code` fintech still remains the active follow-up because its chart-helper comment bleed is a different failure family.
- Production-architecture work is intentionally deferred, not abandoned: the current branch now proves the scheduler semantics we want, but scaling materially beyond the current limits will require a stronger backend shape such as Postgres for durable state, a real shared queue or broker, and separate worker processes or worker hosts instead of relying on SQLite plus in-process threads.
- Added a dual-path builder: legacy single-page fallback remains, while app-like requests can now generate a componentized React + TypeScript + Vite workspace.
- Updated planner/schema/backend flow to support multi-file scaffolds, multi-file iteration context, preview builds, and scoped file repair.
- Added visual direction persistence plus iteration identity locks so later edits preserve fonts, colors, spacing direction, and key interactive patterns.
- Added local recovery and quality gates: required-file contract checks, build-repair pass, density audit, semantic completeness checks, and targeted multi-file refinement/content fixes.
- Added curated benchmark/style-family routing so fan-page prompts can intentionally borrow the stronger cinematic collector shell across franchises while keeping content specific to the requested world.
- Added fan-page-aware density/semantic evaluation so archive-style game outputs are no longer forced through finance/dashboard heuristics.
- Added deterministic recovery for malformed support files and install-time JSON failures before the model-based repair loop runs.
- Added preview-safe generated-asset routing so componentized fan-page images now resolve through preview-served HTML, JS, and CSS instead of breaking at runtime.
- Added stricter dashboard/fintech density guards and runtime normalization for chart-helper scope plus safe dependency syncing so componentized previews recover more reliably before quality scoring.
- Added deterministic dashboard/fintech polish guards so support modules, action affordance, and support-rail hierarchy can improve in preview without relying on another prompt rewrite pass.
- Added tighter componentized refinement scoping so generated lockfiles, icon libraries, runtime polish guards, and low-signal stub CSS files no longer dilute dashboard/fintech repair passes.
- Added a runtime shell layout guard for fixed-sidebar grid dashboards plus broader watchlist/activity/button polish coverage so collapsed preview shells can recover before scoring.
- Added safer fintech polish-guard runtime behavior plus broader componentized syntax recovery for JSX handler bleed, main-entry import-note bleed, control-flow comment-close bleed, and swallowed array terminators so delayed preview capture no longer collapses rendered fintech shells and malformed support files recover more often.
- Current gap: the dashboard 900s timeout is fixed, and March 15, 2026 reruns now stepped from 73.5 in `support_module_gate_v10_dashboard_layout_guard` to 76.0 in `support_module_gate_v18_dashboard_title_activity_guard` and then 82.0 in `support_module_gate_v20_dashboard_panel_distinction_guard`, clearing the 81.0 branch benchmark; fintech still trails its benchmark, with the best recent scoreable retry holding at 72.5 in `support_module_gate_v16_fintech_typography_feed_guard_safe_retry`. The March 15, 2026 `support_module_gate_v34_fintech_table_trend_prompt_retry` black-screen path is now fixed locally by the safer polish runtime, but the follow-up rerun `support_module_gate_v35_fintech_table_trend_prompt_capture_fix` surfaced a separate generated syntax family before preview, so it did not produce a new scoreable fintech checkpoint.
- Branch strategy: keep `main` as the broad stable baseline, keep `feat/componentized-builder-pipeline` as the validated builder-pipeline checkpoint, and use `feat/componentized-multi-run-experiments` for scheduler/concurrency work so the parallel-eval path can evolve without destabilizing the recovery-heavy builder branch.
- Active task on this branch: the scheduler hardening checkpoint is documented and pushed through DB-first dispatch ordering. The next implementation phase is intentionally paused until we decide whether to start the larger production-architecture move to Postgres plus a real queue/worker stack.

## Completed Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 14 | Iteration Mode — scope enforcement, archetype lock, ancestor chain traversal | Done |
| 15 | Consumer Frontend v2 — Versions page, i18n, live preview | Done |
| 15.4 | Enterprise UI — Vite + React + shadcn/ui, 4-theme system, full API wiring | Done |
| 16.1 | Bug Fixes — chat persistence, JSON repair, build lock, agent state recovery | Done |
| 16.2 | Branding — hexagon logo + favicon across all 3 frontends | Done |
| 16.3 | Studio Feature Parity — sort, i18n, build details, Watson TTS | Done |
| 16.4 | Watson STT/TTS — Enterprise pipeline chat (mic + speaker) | Done |
| 16.5 | Authentication — JWT, Google OAuth, blacklist logout, concurrent pipeline | Done |
| 16.6 | Planner Archetype Expansion — 10 to 32 archetypes with layout/content contracts | Done |
| 17.1 | Watson NLU Pre-Pipeline — sentiment routing, keyword extraction | Done |
| 17.2 | Governance Agent — AI Factsheets, Watson NLU scoring, human review flag | Done |
| 17.3 | Dashboard Governance — Avg Prompt Score + Avg Build Score in header | Done |
| 17.4 | Dual PDF Export — Client PDF + Internal PDF from Governance tab | Done |
| 17.5 | Delivery Readiness Gate — Quality Tier badges (High/Good/Low) on Versions timeline | Done |
| 20.1 | Visual Reference Input — attach images to guide AI builds | Done |

## Eval Loop System (eval/)

Automated design quality optimization pipeline:
- Build app, screenshot, score via Claude Vision, rewrite prompts, repeat
- Rollback logic prevents score regression
- Current best scores: Dashboard 82/100, Game 75/100, SaaS Landing 72/100

## Phase 20.1 — Visual Reference Input (✅ Complete Mar 7, 2026)

Attach images (screenshots, mockups, inspiration) to prompts so AI agents can reference them during builds.

- ✅ Backend: /iterate accepts multipart/form-data, saves images to output/<pid>/v<ver>/references/
- ✅ Orchestrator: Passes reference_images list through pipeline context to all agents
- ✅ Planner Agent: Uses Gemini vision to describe reference images, includes in plan context
- ✅ Engineer Agent: Passes reference images as Gemini inline_data parts, matches style/layout/palette
- ✅ Design Agent: Analyzes reference images via Gemini vision before generating Imagen prompts
- ✅ Enterprise + Studio: Paperclip button, file input, thumbnail strip, FormData on send
- ✅ Chat UI: Image thumbnails rendered inline in sent messages (base64 data URLs)
- ✅ Fix: Replaced blob URLs with base64 data URLs so images survive sessionStorage round-trip
- Consumer frontend skipped (read-only, doesn't call /iterate)

## QA Visual Pass (✅ Complete Mar 8, 2026)

Full visual QA of Enterprise + Studio frontends. Two fix branches merged into feat/quality-target-tuning.

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | Version mismatch v0 (Enterprise) vs v1 (Studio) | 🔴 Critical | ✅ Fixed |
| 2 | Versions vs Artifacts state contradiction | 🔴 Critical | ✅ Fixed |
| 3 | "Good afternoon, Jane" hardcoded greeting | 🟡 Medium | ✅ Fixed |
| 4 | Enterprise Profile modal: Jane Doe hardcoded | 🟡 Medium | ✅ Fixed |
| 5 | Studio Profile modal: Jane Doe hardcoded | 🟡 Medium | ✅ Fixed |
| 6 | Deep link /versions returns 404 | 🟡 Medium | ✅ Fixed |
| 7 | Studio Artifacts blank (no empty state) | 🟡 Medium | ✅ Fixed |
| 8 | Enterprise Zap icon on Upgrade to Pro | 🟢 Low | ✅ Fixed |
| 9 | Studio Zap icon on Upgrade to Pro | 🟢 Low | ✅ Fixed |

Files changed: WelcomeBanner.tsx, ProfileModal.tsx, Navbar.tsx, account-modals.tsx, avatar-dropdown.tsx, project-dashboard.tsx, App.tsx, Index.tsx, ArtifactsView.tsx, artifacts/page.tsx

### Backend API QA (Codex, Mar 8, 2026)
- 14/17 tests passed
- ✅ GET /api/projects auth guard fixed (Mar 8, 2026) — all 5 optional-auth endpoints now require JWT
- 10/10 regression tests passing (backend/tests/test_auth_guard.py)
- Register 409 and credits/balance object format were false positives

### Additional QA Fixes (Mar 8, 2026)
- ✅ Removed 💬 emoji from Enterprise Pipeline "Conversation" heading (Index.tsx)
- ✅ Removed emoji from ForgotPassword.tsx (found by Codex repo-wide scan)

## Phase 21 — Build Insights (🔧 In Progress Mar 8, 2026)

- ✅ 21.1 Backend: InsightsAgent generates 2-4 actionable prompt suggestions (agents/insights_agent.py)
- ✅ 21.2 Backend: /api/projects/<id>/versions/<ver>/insights endpoint (app.py)
- ✅ 21.3 Enterprise UI: "Quality Recommendations" section in Governance tab (ArtifactsView.tsx)
- ✅ 21.4 Studio UI: Matching insights section in Governance tab (artifact-viewer.tsx)
- ✅ 21.5 i18n: 12 Korean translation keys added (i18n.ts)
- 🔴 Studio font regression: Geist Sans replaced by IBM Plex Sans during Phase 16.5 auth work — Codex fixing (globals.css, layout.tsx, project-dashboard.tsx)

## Light Mode Contrast Fixes (✅ Complete Mar 9, 2026)

### Enterprise (`fix/enterprise-lightmode-icons`)
- ✅ All hexagon icons changed from `text-primary`/`text-blue-500` → `text-blue-600 dark:text-blue-500`
- Files: Navbar.tsx, ProjectTable.tsx, PipelineStatus.tsx, Index.tsx (pipeline header + chat bubbles)
- Visually verified: Projects, Pipeline, Versions pages in both light + dark mode

### Studio (`fix/studio-lightmode-contrast`)
- ✅ Navbar hexagon → `text-blue-600 dark:text-blue-500`, hover bg → `hover:bg-accent`
- ✅ Project row hexagon → `text-blue-600 dark:text-blue-500`
- ✅ Versions panel selected state → `bg-primary/10` (was `bg-accent`)
- ✅ Darkened `--muted-foreground` from `oklch(0.45)` → `oklch(0.40)` for better text contrast
- Files: navbar.tsx, project-dashboard.tsx, version-timeline.tsx, globals.css
- Visually verified: Projects, Versions, navbar hover in light + dark mode

### Google OAuth origin fix
- ✅ Added `http://localhost:8080` to Google Cloud Console authorized origins + redirect URIs
- Enterprise Google Sign-In now works on port 8080

## Phase 22 — Consumer Frontend Overhaul (🔧 In Progress Mar 9, 2026)

### Phase A: Audit (✅ Complete Mar 9, 2026)
Full audit of `frontend-consumer/` by Codex. Key findings:

**Critical:**
- No authentication — never reads/writes `archon_token`, never sends Authorization headers. All project flows dead against JWT-protected backend
- "Ask for changes" composer is fake — submits only append local log, never calls `/iterate` or `/chat` backend APIs

**High:**
- Connection state mis-modeled — any non-OK fetch = "backend offline" overlay, even for auth errors
- API base hardcoded to `http://localhost:5000` with no env abstraction
- TypeScript health broken — `tsc --noEmit` fails extensively despite strict config
- Multiple no-op controls: Publish, Browse, Source, Pro Features, most Settings fields
- Developer-oriented IA/copy: dark mode default, "Next-Gen Multi-Agent Swarm", PRDs, Runtime Logs, Simulate Fault, Reasoning Engine, Vibe coding level

**Medium:**
- i18n partial — large sections hardcoded English despite KO/EN toggle
- Settings modal mostly fake (profile, password, model selection don't hit backend)
- Error/empty states misleading — failures collapse to "build in progress"
- Dead/duplicated code: LivePreview, ProjectCard, StageStepper, mock gemini.ts unused
- index.html drifted: Tailwind CDN, Google font CDN, importmap remnants, missing /index.css

**Feature gaps vs Enterprise/Studio:**
- Auth (blocks everything else)
- Versions page (THE MOAT — no dedicated route, no comparison narrative)
- Build Insights / Prompt Coach (backend exists, consumer missing)
- Credit balance display
- Voice input (Watson STT/TTS)
- Visual reference image attachments
- Governance / quality summaries

**Recommended approach:**
- Add: auth → versions page → build insights → credits chip
- Simplify: remove dev chrome (logs, fault injection, reasoning engine, vibe coding, fake settings)
- Simplify copy: rename to client language, default light mode, core flow = Describe → Build → Review → Revise
- Mobile-first: reduce sidebar weight, responsive project detail, collapsible tabs

### Phase B: Implementation (✅ Complete Mar 9, 2026)
Codex rewrote consumer as indie-maker AI app builder (Lovable/v0 positioning):
- ✅ Landing page: prompt-first hero, "What can I build for you?", founder-friendly suggestions (Landing Page, Portfolio Site, Dashboard, Online Store)
- ✅ Copy rewrite: removed all developer jargon (Multi-Agent Swarm, PRD, Architecture, Pipeline, Vibe coding, Reasoning Engine)
- ✅ API layer: auth headers via `archon_token`, configurable API base, real `/chat` + `/iterate` calls
- ✅ Fake composer fixed: now calls real backend chat/iterate APIs
- ✅ Connection state: only shows "Backend Offline" for network errors, not 401/403
- ✅ Settings modal: simplified to theme + language only
- ✅ Dead code removed: LivePreview, ProjectCard, StageStepper, gemini.ts
- ✅ index.html cleaned: removed CDN scripts, importmap, duplicate tags
- ✅ Recent projects grid below hero on landing page
- ✅ "Every version saved. Undo anything." differentiator copy
- ✅ Tabs renamed: Preview, Brief, Build Plan, Code, What changed, Versions

**Bugs found during live testing (✅ All fixed Mar 9, 2026):**
- ✅ Preview iframe auto-refreshes after build completes
- ✅ Brief tab loads real brief data
- ✅ Build Plan tab loads real plan data
- ✅ "What changed" tab loads real file data
- ✅ Brief/Plan data no longer swapped on second build
- ✅ Light mode defaults correctly
- ✅ Iteration produces properly styled preview

**Discovered during testing:**
- ✅ Consumer has working Restore Version button — Enterprise + Studio restore buttons are static/unwired. Wire them up as a follow-up task.

### Remaining phases:
- ✅ Phase B bug fixes (Complete Mar 9, 2026)
- ✅ Phase C: Auth + Seed Projects (Complete Mar 9, 2026)
- 🔴 Phase D: Add Versions page (moat feature)
- ✅ Phase E: Build Insights slide-up card (Complete Mar 9, 2026)
- 🔴 Phase F: Mobile polish pass
- ✅ Wire Restore Version in Enterprise + Studio (Complete Mar 9, 2026)

### Phase C: Auth + Seed Projects (✅ Complete Mar 9, 2026)

**Part 1: Consumer Auth (✅ Complete Mar 9, 2026)**
- Guest build flow, login/register pages, Sign Out, post-build register modal
- Google OAuth button, account claiming via POST /api/projects/<id>/claim
- Backend guest mode: unauthenticated project creation, linked to account on register

**Part 2: Seed Projects (✅ Complete Mar 9, 2026)**
- POST /api/seed endpoint — seeds 2 demo projects from peak-quality FF7 output (projects 71 + 38)
- Real Imagen-generated character art (Cloud, Tifa, Barret) committed to backend/seed_data/
- Seed A: "FF7 — Avalanche Archive" (project 71, scored 83/100, Outfit font, hero + character cards + world map)
- Seed B: "FF7 — Midgar Archives" (project 38, search/filter/grid-list views, character detail modals)
- Asset URL rewriting at seed time: /api/assets/{old_id}/1/ → /api/assets/{new_id}/1/
- Auto-seeds on first login when user has 0 projects — Consumer, Enterprise, Studio
- No pipeline runs, no API cost — static file copy from committed seed_data
- Regression test: backend/tests/test_seed_projects.py
- Verified across all 3 frontends with working previews + character art
- Seed projects are swappable: replace backend/seed_data/{folder}/ contents + update original_project_id

**Implementation status:**
1. ✅ Consumer auth pages + guest build flow
2. ✅ Backend: guest project creation + account linking
3. ✅ Seed project system (all 3 frontends)
4. 🔴 Enterprise + Studio: try-before-register flow (deferred — lower priority)

## Consumer UX Declutter Pass (Queued)

**Problem:** Project detail page is too dense. New users don't know where to look — conversation, preview, tabs, AND Build Insights card all compete for attention in one view.

**User feedback:** Eddie's friend took a while to understand what he was looking at. Too many words and elements crammed into one page.

**Root cause:** Two-column layout (conversation left + preview/insights right) tries to show everything simultaneously. No visual hierarchy telling the user what matters most.

**Possible fixes (decide during implementation):**
1. **Progressive disclosure:** Hide insights card by default, show a small "View build tips" button that expands it. Don't auto-show on page load.
2. **Tab the right panel:** Preview is its own tab view. Insights could live as a tab instead of stacking below preview.
3. **Collapse conversation by default:** After build completes, conversation is less important than preview. Auto-collapse or minimize the chat column.
4. **Full-width preview:** Make preview the hero of the page. Move conversation to a slide-out drawer or collapsible panel.
5. **Reduce text density:** Shorter insight suggestions, bigger score number, fewer labels.
6. **Mobile-first rethink:** Stack vertically — preview on top, tabs below, insights as expandable accordion.

**Priority:** High — first impressions matter for conversion. Do this before showing to more friends/beta users.

## Quality Regression Investigation (Queued)

**Goal:** Find the commit that produced peak design quality and identify what changed.

**Reference projects (peak output):**
| Project | ID | Created | Versions | Notes |
|---|---|---|---|---|
| Pokemon Site | 3 | Feb 19 | 2 | |
| Pokemon 2 | 9 | Feb 20 | 1 | |
| v2-pokemon | 20 | Feb 22 | 4 | |
| ff7-fanpage-v3 | 38 | Feb 23 | 3 | Character animations — best example |
| ff7 | 68 | Feb 27 | 2 | |
| ff7-v2 | 71 | Feb 27 | 2 | |
| build-details-test | TBD | ~Feb 27 | — | |

**What made them great:** Character art, Apple-like bubbly cards, animations, nice fonts.

**Peak quality window:** Feb 19–27, 2026.

**Investigation steps:**
1. `git log --oneline --after="2026-02-18" --before="2026-02-28"` — list all commits in peak window
2. Read `output/38/v1/code/src/index.html` (ff7-fanpage-v3 v1) — inspect the actual generated HTML/CSS
3. Read `output/71/v1/code/src/index.html` (ff7-v2 v1) — compare
4. Diff `prompts/engineer.txt` at peak commit vs current HEAD — find what changed
5. Diff `prompts/planner.txt` at peak commit vs current HEAD
6. Diff `agents/engineer_agent.py` at peak commit vs current HEAD
7. Check if design kit system (base.css) replaced the raw CSS generation that produced peak quality
8. Identify specific regressions and create a fix plan

**Key question:** Did the design kit CSS class assembly system lose the raw creative CSS generation that produced the Apple-like aesthetic?

## Eval Loop Results (Mar 10, 2026)

### Overnight Run (5 iterations, all 5 archetypes)
Branch: eval/loops, commit 58f7fcc
- Auth blocker fixed in eval/api_client.py (JWT auto-register/login)
- Playwright permission issue resolved
- Manual kit improvements applied post-run to dashboard, game, saas_landing (.css + .txt)

| Archetype | Baseline (Mar 6) | Best (Mar 10) | Delta |
|-----------|-------------------|---------------|-------|
| Ecommerce | 87.0 | 88.5 | +1.5 |
| Game (FF8) | 83.2 | 84.5 | +1.3 |
| Portfolio | 81.8 | 83.5 | +1.7 |
| Dashboard | 79.0 | 81.0 | +2.0 |
| SaaS Landing | 78.2 | 76.0 | -2.2 |

Average: 82.7/100. Target: 90+.

### Score-Only Kit Test (commit 70f376d)
All archetypes dropped due to build variance (untouched archetypes also dropped 3-4 pts).
Dimension-level signal: Game interactivity 6→7, SaaS visual_hierarchy 7→8, layout 7→8.
Conclusion: Manual kit changes show targeted dimension improvements but prompt/kit tweaking alone has hit diminishing returns.

### Next lever: Watson Discovery feedback loop
Instead of prompt rewriting, feed actual high-scoring HTML/CSS as reference templates into the engineer agent. See Phase 23 below.

## Phase 23 — Watson Discovery Integration (✅ Complete Mar 10, 2026)

IBM Cloud Credit Usage ($200, expires in ~34 days)

### 23.1 — Expanded NLU (✅ Mar 10, 2026)
- ✅ Added ConceptsOptions + EntitiesOptions to NLU agent (agents/nlu_agent.py)
- ✅ New fields: concepts, entities, prompt_richness (rich/moderate/sparse)
- ✅ Richer NLU context passed to PM Agent classify_intent, Planner, and Design Agent
- ✅ Graceful fallback when credentials missing

### 23.2 — Watson Discovery Client + Best Builds Ingestion (✅ Mar 10, 2026)
- ✅ DiscoveryClient wrapper (utils/watson_discovery.py) — graceful fallback, lazy collection resolution, idempotent ingest
- ✅ Ingestion script (scripts/ingest_best_builds.py) — 5/5 best builds ingested
- ✅ Best builds: Ecommerce 88.5 (pid 163), Game 84.5 (161), Portfolio 83.5 (169), Dashboard 81.0 (155), SaaS Landing 76.0 (162)
- ✅ Query test confirmed all 5 archetypes retrievable

### 23.3 — Pipeline Integration + Eval Auto-Ingest (✅ Mar 10, 2026)
- ✅ EngineerAgent.run() accepts reference_code (dict) — injects Discovery HTML/CSS as reference context for initial builds only
- ✅ Pipeline queries Discovery before Engineer Agent runs, resolves archetype aliases via DESIGN_KIT_ALIASES
- ✅ Eval loop auto-ingests builds scoring >=85 into Discovery (lazy import, canonical archetype, non-fatal)
- ✅ Complete learning loop: build → score → if 85+, ingest → next build retrieves best reference

Branch: feat/watson-discovery (4 commits: 09dce26, da95bd8, 8b38ebe) → merged to main

## Phase 24 — Asset Reuse Library (✅ Complete Mar 10, 2026)

Eliminates broken images by filling missing `<img>` slots from a library of previously generated Imagen assets.

- ✅ 24.1 ImageAsset SQLite table + bulk ingestion script (scripts/ingest_image_library.py) + auto-ingest hook after Design Agent
- ✅ 24.2 Post-build missing image scanner + library lookup + file copy (utils/asset_filler.py)
- ✅ 24.3 Category detection: key-based heuristic (hero, product, character, lifestyle, collection, icon, pattern, abstract, other) + prompt text fallback
- 🔴 24.4 Admin UI (deferred)

Bulk ingestion: 872 images across 9 categories from 205 projects. Idempotent (0 on second run).

Branch: `feat/asset-reuse-library`

**New files:**
- backend/models.py (ImageAsset model)
- utils/image_asset_catalog.py (shared cataloging helper)
- scripts/ingest_image_library.py (bulk ingester)
- utils/asset_filler.py (post-build missing image scanner + filler)

**Modified:**
- backend/app.py (auto-catalog after Design Agent + fill_missing_assets after Engineer Agent)
- agents/design_agent.py (base64→PNG decode fix — Imagen API returns base64 string, not raw bytes)

**Critical bug found during testing:**
- Imagen 4 Ultra API returns image_bytes as base64-encoded string, not raw bytes
- All previously generated images on disk are base64 text files (broken in browser)
- Fix: design_agent.py detects `iVBOR` prefix and decodes before writing
- All future builds now produce valid PNG files
- Discovery/Image Catalog log messages removed from frontend Live Output (print-only now)

## Known Bugs

| Bug | Severity | Description |
|-----|----------|-------------|
| ~~AuthGuard token expiry~~ | ✅ Fixed Mar 10 | AuthGuard now validates token via /api/auth/me on mount. Clears stale tokens and redirects to /login on 401. Enterprise + Studio. Cross-origin handoff preserved. Commit d6b5d8d. |
| ~~Double NLU call~~ | ✅ Fixed Mar 10 | /chat returns nlu_result in response, frontend forwards to /iterate, /iterate skips re-analysis if present. Enterprise + Studio both patched. Commit d862863. |
| ~~Quality Recommendations missing~~ | ✅ Fixed Mar 10 | Restored Quality Recommendations section after Compliance in Governance tab (Enterprise + Studio). Added insights fetch with auth header, category icons, priority badges, empty state. Commit 48d27ed. |
| ~~Imagen images not rendering~~ | ✅ Fixed Mar 10 | Resilient asset resolver: checks current assets/, code/src/assets/, last_design_assets.json local_path, and prior version fallback. Preview rewriting normalizes relative asset URLs. Expanded asset route for nested paths + MIME detection. Commit 58a9f8f. |
| ~~Generated apps have no interactivity~~ | ✅ Fixed Mar 10 | Added JS interactivity requirements to engineer_core.txt (Zero Dead Buttons Policy) + planner.txt quality_target. Verified: filters, cart counter, nav scroll all working. Some footer anchors still missing targets. Commit 18f0ce0. |
| ~~Notification sound missing~~ | ✅ Fixed Mar 10 | AudioContext resume + pre-unlock on first user gesture. Transition-based triggers (RUNNING→COMPLETED/FAILED). Shared AudioContext via ref. Studio sound moved to global app-shell so chime plays from any page. Enterprise + Studio. Commits 61ab5b4, 1b10893. |
| PM Agent classify_intent flake | 🟡 Medium | Intermittent false negative: clear build prompts sometimes classified as unclear, returning "I'm not sure I understood that — could you rephrase?" Resubmitting the identical prompt succeeds. Observed on Enterprise Pipeline (Project #656, Mar 10). Same prompt worked on 2 other projects. Root cause likely in PM Agent classify_intent — GPT-4o occasionally misclassifies valid build prompts as ambiguous. Investigate: temperature setting, prompt length sensitivity, or NLU pre-analysis interfering with classification. Repro: "Build a pet adoption website with a hero banner showing happy rescued dogs, a grid of adoptable pet cards with photos and names, filter buttons for dogs cats and rabbits, an adoption application form, and a testimonials section with adopter stories". |
| ~~Testimonials text overlaps background image~~ | ✅ Fixed Mar 10 | Strengthened COMMON SCORE-KILLERS #14 in engineer_core.txt — explicitly requires solid/semi-transparent card backgrounds for text over images, calls out testimonials specifically, added dedicated Testimonials checklist item in QUALITY SELF-CHECK. Commit f429a15. |

## Pending Verification

| Feature | Branch | What to test |
|---------|--------|--------------|
| Smart image count from seed_rows | feat/smart-image-count (merged) | ✅ Verified Mar 11 — Flask log confirmed "targeting 7 images (seed_rows=6, image_item_count=5)". |
| Hide Asset Filler from Live Output | fix/hide-asset-filler-log (merged) | ✅ Verified Mar 11 — only in Flask terminal, not in Live Output panel. |
| Testimonial overlap prompt fix | fix/testimonial-overlap-prompt (merged) | ✅ Verified Mar 11 — semi-transparent cards over background photo, text readable. |

## fix/multi-bug-sprint (✅ Merged Mar 11, 2026)

5 fixes across backend + Enterprise + Studio frontends.

| Commit | Fix | Status |
|--------|-----|--------|
| bfd6910 | Discovery archetype mismatch — only inject reference if archetype matches engineer kit | ✅ Committed |
| 5ac7d09 | "Set as iteration base" UX — renamed Restore button, tooltip, Set ✓ confirmation flash, ↩ branched from vN label | ✅ Verified |
| 657d6c0 | Versions page auto-selects latest version when new build completes | ✅ Verified |
| 97fb517 | Notification sound regression — AudioContext pre-unlock, transition-based RUNNING→COMPLETED/FAILED trigger | ✅ Verified |
| 0b27cc2 | base.css copied forward on iteration builds — fixes CSS loss on v2+ previews | ✅ Verified (v3 fully styled) |

**Versioning strategy confirmed:** Restore to previous version + iterate = next sequential version number (v11, not v2a). Parent chain tracked via `parent_execution_id` in DB. Sidebar shows "↩ branched from vN" for non-sequential parents.

## Phase 22.G — Archetype Shimmer Skeleton (✅ Complete Mar 11, 2026)

During initial builds (no preview yet), the consumer preview panel now shows a fake browser window with shimmer skeleton blocks instead of an empty panel. The skeleton layout matches the detected archetype and updates live as the planner stage resolves `locked_ui_archetype`.

- ✅ `BuildSkeletonScreen` component in `ProjectDetailPage.tsx` — fake browser chrome (traffic-light dots, shimmer URL pill, stage status text) + archetype layout
- ✅ 5 archetype layouts: landing/saas_landing, dashboard, ecommerce, portfolio, game/default
- ✅ CSS shimmer keyframes injected via inline `<style>` — light + dark mode variants
- ✅ Stage text updates: pm → "Understanding your idea..." / planner → "Planning your layout..." / engineer → "Writing your code..."
- ✅ Skeleton disappears and iframe renders on build completion
- ✅ Iteration builds (v2+) never show skeleton — existing iframe continues
- ✅ Backend: `locked_ui_archetype` added to `/api/execution-status` response + `Project.to_dict()`
- ✅ Frontend: `uiArchetype` added to `Project` type, normalized in `orchestrator.ts`, updated live during polling
- ✅ Verified: dashboard build showed skeleton immediately, archetype layout matched, preview replaced skeleton on completion
- Branch: `feat/build-loading-cards`

**Known issues found during testing:**
- 🔴 Generated dashboard CSS has overlapping/broken text on bottom of page (pre-existing quality issue, unrelated to skeleton)
- 🔴 Build Insights returns 401 for guest users — insights endpoint needs optional-auth like preview endpoint

## Phase 22.H — Consumer V3 Animated Redesign (✅ Complete Mar 11, 2026)

Full animated reimagination of consumer frontend (port 3002). Three design branches created, v3 selected and merged to main.

- ✅ Animated gradient mesh background — 3 drifting orbs (indigo, violet, cyan), CSS @keyframes
- ✅ Headline gradient text shimmer animation (4s sweep)
- ✅ Inspiration cards with lift/glow hover animations (replaced suggestion pills)
- ✅ Prompt textarea glowing border pulse on focus
- ✅ Icon-only navigation rail on project detail (6 icons: Preview, Brief, Plan, Code, History, Versions)
- ✅ Neural network loading animation during builds (animated dots + lines)
- ✅ Version cards with scaled iframe thumbnails
- ✅ Live preview fills right panel as hero
- ✅ Sidebar: "WORLDS IN PROGRESS" branding, pulsing backend status dot, gradient Start Building button
- ✅ Branch: design/v3-reimagined → merged to main Mar 11

**Phase 22.I polish items (✅ Complete Mar 12, 2026):**
- ✅ Removed light/dark toggle from SettingsModal (dark-only app)
- ✅ SettingsModal redesigned to match v3 dark theme
- ✅ Language switch now applies instantly on Save (lang prop passed from App.tsx)
- ✅ Enter = submit prompt, Shift+Enter = newline (landing textarea)
- ✅ Menu/nav icon rail repositioned to not overlap chat panel
- ✅ Sign In button (top right) updated to dark glass style
- ✅ "Could not load" replaced with "Building..." message during active builds
- ✅ Tab switches and code file switches now scroll right panel to top
- ✅ Versions page: Restore button hidden when only 1 version or current version selected
- ✅ Recent projects on landing page now show live iframe preview thumbnails
- ✅ Sidebar project list now shows live iframe preview thumbnails
- ✅ Sign In / Register pages redesigned to match v3 dark theme
- ✅ Button hover animation lag fixed (backface-visibility, translateZ, scale reduced to 1.005)

**Phase 22.J — Remaining Polish (✅ Complete Mar 12, 2026):**

1. ✅ Google Sign-In button color fixed (`LoginPage.tsx`, `RegisterPage.tsx`) — dark glass style matching v3 theme
2. ✅ Thumbnail height fixed — `h-[140px]` on landing cards, `h-[72px]` on sidebar cards, `overflow-hidden` enforced, description text clamped
3. ✅ Thumbnail card edge radius fixed — `rounded-t-[1.8rem] overflow-hidden` matching outer card radius, no iframe border-radius bleed
4. ✅ Nav icon rail placement fixed — dedicated grid column, never overlaps panels, hidden on mobile
5. Mobile layout deferred to Phase 22.F (separate task)

**Phase 22.K — Consumer Rename + Bug Fixes (✅ Complete Mar 12, 2026):**
- ✅ Build Insights nav rail tab added — Build Insights accessible via icon rail in `ProjectDetailPage.tsx`
- ✅ Apply suggestion UX fixed — one-click pre-fills iteration prompt input
- ✅ Consumer sidebar project rename — double-click UX, hover cursor affordance, inline edit
- ✅ Backend: `PATCH /api/projects/<id>` route added to `backend/app.py` — updates project name, JWT-protected
- ✅ Frontend: `handleRenameProject` wired in `frontend-consumer/App.tsx` via `apiRequest` PATCH call
- ✅ Rename persists across refresh (verified end-to-end)

**Deferred (bigger features, separate phases):**
- Credit/token system (Phase 25)
- Deploy to GitHub / one-click repo (Phase 26)
- Host on Archon server / "Publish" feature (Phase 27)

## Up Next

| Phase | Description |
|-------|-------------|
| ~~22.I~~ | ~~Consumer V3 Polish Pass~~ ✅ Mar 12 |
| ~~22.J~~ | ~~Consumer V3 Remaining Polish (Google button, thumbnails, nav rail)~~ ✅ Mar 12 |
| ~~22.K~~ | ~~Consumer Rename + Bug Fixes~~ ✅ Mar 12 |
| 22.D | Consumer Versions page (THE MOAT — timeline + preview + narrative) |
| 22.F | Consumer mobile polish pass |
| 25 | Credit / token system |
| 26 | GitHub deployment — one-click repo + auto-commit on iterate |
| 27 | Publish to Archon hosting — "Publish" button, hosted preview link |
| — | Fix Build Insights for guest users (insights endpoint → optional-auth) |
| — | Quality Regression Investigation (compare Feb 19-27 peak vs current) |
| 8.3 | Client shareable read-only links (primary moat feature) |
| 18 | Unified Auth + Plan-Based UI Routing |

## Eval Loop Dual-PC Workflow

See `docs/EVAL_WORKFLOW.md` for the full parallel eval loop process.

## Overnight Eval Run — Mar 11→12, 2026

**Result: Harness bug fixed, no winning changes committed.**

### What happened
- Loop started on `eval/loops`, ran partial `saas_landing` cycle
- Baseline scores: 75.0, 82.0, 56.0 — B-test: 75.0 (no improvement, reverted)
- Backend + operator process died overnight — loop stopped early
- After restart, loop resumed on `dashboard` archetype
- Dashboard baselines: 83.0, 77.0, 84.5 — then harness crash before edit
- Root cause: `eval/prompt_parser.py` expected a `dashboard` section in `prompts/engineer.txt` — only `SAAS LANDING PAGE` section exists there
- Loop restarted, ran 63.0 + 76.5 dashboard baselines, then stopped in morning

### Harness fix (Mar 12, 2026)
- ✅ Added `has_section()` to `eval/prompt_parser.py`
- ✅ `eval/operator_loop.py` now checks section exists before targeting `engineer.txt`
- ✅ Fallback: archetypes without engineer.txt sections (dashboard, ecommerce, portfolio, game) now edit kit files in `prompts/archetypes/` instead of crashing
- ✅ Defensive degradation: if engineer-section editing fails mid-cycle, loop falls back to kit editing instead of burning API budget on repeated crashes
- ✅ Verified: full baseline → edit → B-test cycle completed without crash
  - Dashboard baseline: 73.5 → B-test: 52.0 → **correctly reverted**
- ✅ `docs/EVAL_WORKFLOW.md` updated: mission is to improve designs, not observe failures. Operators must fix local blockers, treat API spend as optimization budget, avoid passive repeat-fail cycles

### New files from overnight stabilization (untracked)
- `scripts/launch_operator_loop.py`
- `scripts/operator_supervisor.py`
- `scripts/run_operator_loop_forever.cmd`

### Current scores (unchanged from Mar 10)
| Archetype | Best Score |
|-----------|------------|
| Ecommerce | 88.5 |
| Game (FF8) | 84.5 |
| Portfolio | 83.5 |
| Dashboard | 81.0 |
| SaaS Landing | 76.0 |

**Next eval run:** Harness is now stable. Loop can iterate and reject bad changes. Commit the harness fixes, then restart overnight loop targeting all 5 archetypes.
