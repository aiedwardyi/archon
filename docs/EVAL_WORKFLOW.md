# Eval Loop Operator Runbook

This workflow is the authoritative runbook for manual eval optimization. It uses the repo's existing control points and does not add a wrapper script around the loop.

## Mission

The goal of this loop is not to "watch evals run." The goal is to improve design output quality and raise accepted scores by making the prompt and design-kit system better over time.

Treat API spend as optimization budget. If the loop is spending tokens on baseline runs, scoring, or failed cycles without producing better prompt or kit changes, that is a problem to solve immediately.

Operator stance:

- Be proactive, not passive.
- Remove blockers that prevent prompt or kit iteration.
- Prefer fixing the eval workflow when it is preventing optimization.
- Do not stop at reporting failures if a reasonable fix on `eval/loops` can unblock continued improvement.

## Scope

- Eval executor: `eval/eval_runner.py`
- Prompt evolution target: `prompts/engineer.txt`
- Manual design-kit targets: `prompts/archetypes/<archetype>.css` and `prompts/archetypes/<archetype>.txt`
- Optional tuning target after plateau only: `eval/eval_config.json`
- Result artifacts: `eval/results/<archetype>/iter_<n>/scores.json`
- Operator logs: `eval/results/codex_improvements.md`, `eval/results/overnight_summary.md`, `eval/results/checkpoint.md`

Out of scope for this loop:

- `utils/*`
- `backend/*`
- New orchestration or automation wrappers
- Merges, rebases, or branch switching away from `eval/loops` during an eval session

Allowed workflow fixes on `eval/loops` when they directly unblock optimization:

- `eval/*` fixes needed to keep the operator loop running
- Prompt parsing or section-detection fixes needed to reach the edit step
- Logging or loop-control fixes needed to prevent wasted repeated failures

Do not treat a broken eval harness as "out of scope" if fixing it is the shortest path to resume design improvement on `eval/loops`.

## Session Start

Run these commands in order before doing anything else:

```powershell
cd C:\Users\mredw\Desktop\ai-dev-team
git branch --show-current
git checkout eval/loops
git branch --show-current
git pull origin main --no-rebase
.\venv\Scripts\Activate
```

Branch rule:

- `git branch --show-current` must return `eval/loops`.
- If it does not, stop and run `git checkout eval/loops` before any eval, prompt, or log work.
- Never switch to another branch, merge, or rebase during the loop.

## Runtime Setup

Use the existing runtime flow only:

1. Start the backend in a separate terminal and keep it running:

```powershell
python backend/app.py
```

2. Run evals from the repo root:

```powershell
python eval/eval_runner.py --archetypes dashboard game saas_landing ecommerce portfolio --max-iterations 1 --score-only
python eval/eval_runner.py --archetypes <archetype> --max-iterations 3
```

3. Watch the backend terminal during runs for Discovery ingestion messages.

## Editable Surfaces

Only these files are valid experiment surfaces for the operator loop:

- `prompts/engineer.txt`
  - Edit only the section for the current weakest archetype.
- `prompts/archetypes/<archetype>.css`
- `prompts/archetypes/<archetype>.txt`
- `eval/eval_config.json`
  - Only after a documented plateau and only for prompt-selection tuning.
- `eval/results/codex_improvements.md`

Do not treat `prompts/engineer_core.txt`, `prompts/planner.txt`, `utils/*`, or `backend/*` as first-line tuning surfaces for this workflow.

Priority rule:

- If the eval harness can reach prompt or kit edits, keep experiments on the prompt and kit surfaces above.
- If the eval harness cannot reach prompt or kit edits due to a bug in `eval/*`, fix the harness first, then resume experiments immediately.

## One Full Operator Cycle

1. Read:
   - `eval/results/codex_improvements.md`
   - `eval/results/overnight_summary.md`
   - `eval/results/checkpoint.md`
2. Determine the weakest archetype across:
   - `dashboard`
   - `game`
   - `saas_landing`
   - `ecommerce`
   - `portfolio`
3. If comparable current scores are missing, run:

```powershell
python eval/eval_runner.py --archetypes dashboard game saas_landing ecommerce portfolio --max-iterations 1 --score-only
```

4. Run the baseline sample for the weakest archetype:

```powershell
python eval/eval_runner.py --archetypes <archetype> --max-iterations 3
```

5. Read:
   - `eval/results/<archetype>/iter_0/scores.json`
   - `eval/results/<archetype>/iter_1/scores.json`
   - `eval/results/<archetype>/iter_2/scores.json`
   - The current archetype section in `prompts/engineer.txt`
   - `prompts/archetypes/<archetype>.css`
   - `prompts/archetypes/<archetype>.txt`
6. Identify the 1-2 weakest dimensions under `7.0`.
7. Choose exactly one lever.
8. Make one surgical change only:
   - Either the matching archetype section inside `prompts/engineer.txt`
   - Or the matching archetype kit file under `prompts/archetypes/`
9. Run the same 3-build command again as the B test.
10. Average `weighted_total` across the three B-test runs and compare it to the baseline average.
11. Commit only if the improvement is greater than `+1.0`.
12. If the change does not clear `+1.0`, revert only the files changed in that experiment.
13. Update `eval/results/codex_improvements.md`.
14. Move to the second-weakest archetype and repeat.

## Blocker Handling

If the loop cannot complete a full baseline -> edit -> B-test cycle, do not keep burning API budget on repeated failed starts.

Required response to blockers:

1. Identify whether the failure is:
   - prompt/kit quality
   - eval harness bug
   - backend/runtime issue
   - external service/API issue
2. If the failure is in `eval/*` and blocks prompt or kit iteration, fix it on `eval/loops` before resuming.
3. If the failure is a prompt-surface mismatch, such as parser logic not finding a live archetype section in `prompts/engineer.txt`, treat that as a must-fix blocker, not as an observation to log and ignore.
4. If one tuning surface is blocked, switch to the other valid tuning surface when possible rather than stalling the loop.
5. Record the blocker, the fix, and the reason it was necessary in `eval/results/codex_improvements.md`.

Never let the loop sit in a repeat-fail pattern when a local code fix would restore useful optimization work.

## Lever Mapping

Use one lever per experiment:

- `visual_hierarchy` or `layout_precision`
  - Prefer the matching archetype section in `prompts/engineer.txt`
- `typography`, `depth_polish`, `interactivity_cues`, `color_system`
  - Prefer `prompts/archetypes/<archetype>.txt` or `.css`
- `data_completeness`
  - Prefer `prompts/engineer.txt` unless the kit already includes explicit content-count rules
- `overall_impression`
  - Do not target directly unless no subdimension is clearly weaker
  - Prefer the dominant lower subdimension instead

## Discovery Verification

Run this check after every eval:

1. Watch backend output for `[Discovery]` ingestion activity.
2. For any build scoring `85+`, expect either:
   - an ingest message, or
   - an explicit duplicate/already-present message
3. If a build scores `85+` and no ingestion message appears:
   - inspect `utils/watson_discovery.py`
   - inspect `backend/.env`
4. Required Discovery enablement set:
   - `WATSON_DISCOVERY_API` or `WATSON_DISCOVERY_API_KEY`
   - `WATSON_DISCOVERY_URL`
   - `WATSON_DISCOVERY_PROJECT_ID`
5. If those values exist and Discovery is still disabled, record the blocker in `eval/results/codex_improvements.md` and stop short of code changes.

Discovery diagnosis is operational only for this loop. Do not patch `utils/*` or `backend/*` as part of prompt/design experiments.

## Git Rules

- Stay on `eval/loops` for the actual eval session.
- Commit only the winning experiment files plus `eval/results/codex_improvements.md`.
- Commit harness fixes separately from prompt/kit wins when possible, with a message that makes the unblock explicit.
- Revert only the prompt or kit files changed in the failed experiment.
- Do not revert unrelated repo changes.
- Do not merge.
- Do not rebase.

## Logging Contract

Standardize each experiment entry in `eval/results/codex_improvements.md` with:

- Cycle number and timestamp
- Archetype
- Baseline average across 3 runs
- Weakest dimensions
- Exact change made
- File changed
- Test average across 3 runs
- Delta
- Verdict: committed or reverted
- Notes and next hypotheses

If a blocker fix was required, also log:

- Why the loop could not continue without the fix
- Whether API spend would have been wasted by continuing without it
- What exact file or logic was fixed to restore optimization

Hourly persistence rule:

- Even if no winning prompt or design change is committed, commit the updated log at least once per hour on `eval/loops`.

## Acceptance Criteria

A winning change must satisfy all of the following:

- B-test average exceeds the baseline average by more than `1.0`
- No build failures in the accepted sample set
- No screenshot or scoring failures in the accepted sample set
- No newly degraded dimension falls below `7.0`, unless the net gain is still clearly positive and the regression is explicitly documented

Session-level success criteria:

- The loop must actually reach prompt or kit edits and B-tests.
- Repeated baseline-only or crash-only cycles do not count as productive progress.
- If the loop is blocked by local code, the blocker should be fixed before more substantial eval spend is incurred.

## Test Discipline

For every cycle:

- Confirm `git branch --show-current` is `eval/loops`
- Confirm backend health before eval runs
- Compute the average `weighted_total` from exactly 3 runs per side
- If a sample has build variance, document it and deprioritize strong prompt conclusions from that cycle

## File Ownership Reality Check

Use repo reality, not stale path names:

- `prompts/archetypes/*` is the live design-kit surface
- `prompts/engineer.txt` is the live eval prompt surface
- `eval/results/` contains the checkpoint and score artifacts used by the operator loop

This runbook assumes a human-operated loop using the existing commands only.
