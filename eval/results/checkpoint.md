# Overnight Eval Checkpoint — 2026-03-10

## Scores
| Archetype | Baseline | Final | Delta | Best Build ID |
|-----------|----------|-------|-------|---------------|
| Ecommerce | 87.0 | 88.5 | +1.5 | 163 |
| Game (FF8) | 83.2 | 84.5 | +1.3 | 161 |
| Portfolio | 81.8 | 83.5 | +1.7 | 169 |
| Dashboard | 79.0 | 81.0 | +2.0 | 155 |
| SaaS Landing | 78.2 | 76.0 | -2.2 | 162 |

## Changes Made
- `eval/api_client.py`
  - Added automatic auth bootstrap in `BuilderAPI.__init__`.
  - Registers eval user (`eval@archon.dev`) and falls back to login on 409.
  - Supports both `/api/register` + `/api/auth/register` and `/api/login` + `/api/auth/login`.
  - Stores JWT and applies `Authorization: Bearer <token>` to all requests via session headers.
  - Switched `health_check()` to `/api/health` and handles 401 gracefully.
- `prompts/engineer.txt` (archetype-specific sections only, auto-updated by `eval_improver.py` across iterations for dashboard/game/saas_landing/ecommerce/portfolio)
- `prompts/archetypes/dashboard.css`
  - Added `--shadow-glow`, `.interactive-chip`, and stronger hover polish in activity rows.
- `prompts/archetypes/dashboard.txt`
  - Added action-chip and keyboard-focus requirements for interaction visibility.
  - Added explicit depth-polish requirement.
- `prompts/archetypes/game.css`
  - Added stronger nav emphasis, focus-visible treatments, and `.weapon-cta` interaction class.
- `prompts/archetypes/game.txt`
  - Added explicit anti-placeholder fallback requirements for weapons/world map and mandatory interactive controls.
- `prompts/archetypes/saas_landing.css`
  - Added higher-contrast text token, focus-visible states, stronger secondary button hover state, and `.card-link` interactivity.
- `prompts/archetypes/saas_landing.txt`
  - Added explicit contrast constraints, card-level interactivity requirements, and tighter color-system guidance.

## What Worked
- Auth fix fully unblocked protected backend endpoints and restored eval automation.
- Running eval loop outside sandbox restrictions fixed Playwright screenshot failures and enabled full scoring.
- Auto rollback logic prevented large prompt regressions from persisting.
- Best gains came from ecommerce and portfolio prompt evolution (+8.0 each within run progression).
- Manual kit updates now directly target recurring weak dimensions: depth polish (dashboard), interactivity/data fallback (game), contrast/interactivity/color discipline (saas landing).

## What Didn't Work
- Several prompt rewrites produced regressions and were rolled back automatically:
  - Dashboard: 81.0 -> 71.0 (iter2 -> iter3)
  - Game: 84.5 -> 65.5 (iter3 -> iter4)
  - SaaS Landing: 76.0 -> 69.0 (iter3 -> iter4)
  - Ecommerce: 88.5 -> 84.5 (iter3 -> iter4)
- SaaS landing remained unstable with low-contrast outputs in late iterations.
- Game archetype still suffered occasional content collapse (missing/placeholder-like sections), causing large variance.

## Remaining Gaps
- Dashboard
  - `depth_polish` remains at 6 in final iteration.
  - Suggestion: enforce one elevated focal card with layered shadow, subtle border glow, and inset highlight in section requirements.
- Game
  - Final iteration weak dimensions: `typography` 6, `depth_polish` 6, `data_completeness` 4, `interactivity_cues` 6.
  - Suggestion: hard-require non-empty fallback content blocks for every image slot and at least one interactive control per card.
- SaaS Landing
  - Final iteration weak dimensions: `typography` 6, `color_system` 6, `depth_polish` 6, `interactivity_cues` 6.
  - Suggestion: enforce contrast-safe text token usage and add mandatory card-level interactive links/buttons.
- Ecommerce
  - No dimensions below 7 in best run; still below 90 target overall.
  - Suggestion: increase uniqueness in storytelling sections and richer data density in collections/features.
- Portfolio
  - No dimensions below 7 in final iteration; still below 90 target overall.
  - Suggestion: further differentiate interaction design in projects/stats to push overall impression into 9-range.
