# Overnight Eval Optimization Summary

## Date: 2026-03-10

## Final Scorecard (Best per archetype)

| Archetype | Baseline (Mar 6) | Best Score (Mar 10 run) | Delta | Best Build |
|-----------|-------------------|--------------------------|-------|------------|
| Ecommerce | 87.0 | **88.5** | +1.5 | project 163 (iter3) |
| Game (FF8) | 83.2 | **84.5** | +1.3 | project 161 (iter3) |
| Portfolio | 81.8 | **83.5** | +1.7 | project 169 (iter4) |
| Dashboard | 79.0 | **81.0** | +2.0 | project 155 (iter2) |
| SaaS Landing | 78.2 | **76.0** | -2.2 | project 162 (iter3) |

**Average best score this run: 82.7/100**

## Key Findings

### What Worked
1. JWT auth support in `eval/api_client.py` unblocked all protected backend endpoints.
2. Running eval loop with elevated permissions resolved Playwright `WinError 5` screenshot failures.
3. Rollback guard prevented major regressions from becoming persistent prompt state.
4. Ecommerce and portfolio improved meaningfully within run progression, peaking at 88.5 and 83.5.

### What Didn't Work
1. Game and SaaS had high variance and occasional collapse in content quality despite prompt improvements.
2. Late-iteration regressions required rollback in multiple archetypes.
3. 90+ target was not achieved for any archetype in this run.

## Regressions Rolled Back
- Dashboard: 81.0 -> 71.0 (iter2 -> iter3), rollback applied
- Game: 84.5 -> 65.5 (iter3 -> iter4), rollback applied
- SaaS Landing: 76.0 -> 69.0 (iter3 -> iter4), rollback applied
- Ecommerce: 88.5 -> 84.5 (iter3 -> iter4), rollback applied

## Manual Design Kit Updates After Run
- `prompts/archetypes/dashboard.css`, `dashboard.txt`
  - Added stronger interaction chips, hover/focus cues, and explicit depth-polish requirements.
- `prompts/archetypes/game.css`, `game.txt`
  - Added focused interaction classes and stronger anti-placeholder/data-fallback requirements.
- `prompts/archetypes/saas_landing.css`, `saas_landing.txt`
  - Added contrast-safe text token usage, card-level interaction requirements, and tighter color-system guidance.

## Auth Blocker Resolution
- `eval/api_client.py` now:
  - Registers eval user (`eval@archon.dev`) and logs in on 409.
  - Handles both legacy and current auth routes (`/api/register` + `/api/auth/register`, `/api/login` + `/api/auth/login`).
  - Sets `Authorization: Bearer <token>` on the shared session for all requests.
  - Uses `/api/health` for backend reachability checks.

## Artifacts
- Iteration reports: `eval/results/report_iter_0.md` … `eval/results/report_iter_4.md`
- Final report: `eval/results/report_final.md`
- Checkpoint: `eval/results/checkpoint.md`
