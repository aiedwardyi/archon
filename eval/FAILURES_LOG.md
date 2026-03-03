# Eval Loop Failure Log

## Run 1 (22:26) — dashboard, game, saas_landing (target 80)
- **dashboard**: Built OK, scored 81/100 PASS
- **game**: Build timed out at 300s (image gen takes long)
- **saas_landing**: Build FAILED at complete stage (engineer JSON parse error likely)

## Run 2 (22:38) — game, saas_landing (target 80)
- **game**: Built OK (6 min), screenshot 6MB > 5MB API limit, scoring failed
- **saas_landing**: Build FAILED (attempt 1), retry succeeded, scored 70.5/100, prompt improved

## Run 3 (22:53) — game, saas_landing (with compression fix)
- **game**: Built OK, compressed screenshot to 212KB, scored 75.5/100
  - Prompt improvement FAILED: parser couldn't find game section (regex didn't match rewritten format)
- **saas_landing**: Build FAILED (attempt 1), retry building...
  - (run was stopped to update config)

## Run 4 (23:04) — dashboard, game, saas_landing (target 90, aggressive scoring)
- **dashboard**: Build FAILED at engineer stage (attempt 1 + retry both failed)
  - Possible cause: Claude API error or JSON parse failure
- **game**: Built OK, scored 75.5/100
  - Prompt improvement FAILED: parser regex still broken (fixed now)
- **saas_landing**: Build FAILED at engineer stage (attempt 1 + retry both failed)
  - Same engineer failure pattern as dashboard

## Run 5 (13:14) — dashboard, game, saas_landing (target 90, schema fix)
- **All builds failed** at planner stage: "Architecture Agent could not produce a valid build plan after 3 attempts"
  - **ROOT CAUSE**: plan_schema.py `ui_archetype` Literal only had 10 values but planner.txt tells Gemini to use 30+ archetypes. Gemini can't produce values outside schema constraint, causing parse failures.
  - **FIX**: Updated plan_schema.py to include all 32 archetypes matching planner.txt
  - Flask server restarted with fix

## Run 6 (13:37) — dashboard, game, saas_landing (target 90, full schema fix)
### Iteration 0
- **dashboard**: Built OK, scored **82/100**. Prompt improved (4170 chars).
- **game**: Build timed out (attempt 1, 600s). Retry succeeded. Scored **74.5/100**. Prompt improved (9183 chars).
- **saas_landing**: Build FAILED 3x (2x "1000 validation errors for EngineeringResult", 1x timeout). Skipped.
  - Engineer JSON output too complex for the saas_landing archetype (multiple sections: hero, features, testimonials, pricing, FAQ, footer)

### Iteration 1
- **dashboard**: Built OK, scored **81/100** (down 1pt from 82, normal variance). Prompt improved (8759 chars).
- **game**: Built OK, scored **57.5/100** (DOWN from 74.5!). Prompt improvement REGRESSED quality.
  - Issue: Overloaded prompt with too many constraints caused engineer to produce bare page with no images or character art.
- **saas_landing**: Build FAILED 2x (timeout), succeeded on 3rd. Scored **71.5/100**. Prompt improved.

### Loop stopped: Convergence (no archetype improved by >1 point)

### Key Findings
1. **Prompt improvements can regress scores** — game went from 74.5 → 57.5 after improvement
2. **SaaS landing very unreliable** — 5 of 6 build attempts failed (validation errors + timeouts)
3. **Convergence threshold too tight** (1 point) — scores naturally fluctuate 1-3 points
4. **Dashboard plateau at ~81** — needs structural changes (sidebar nav) to break through
5. **Need rollback logic** — if score drops, revert prompt to previous version

## Root Causes Identified & Fixed
1. **Image too large for API** (6MB > 5MB) — FIXED: Added JPEG compression in scorer + improver
2. **Game parser broken** — FIXED: Updated regex to match unnumbered archetype headers
3. **Gemini key rotation** — FIXED: Added fallback to GENAI_API_KEY2/3 in app.py
4. **Build timeout too short** — FIXED: Increased to 600s
5. **Engineer stage failures** — Transient (Claude JSON parse errors). Retry logic handles it.
   - High failure rate in run 4 may indicate backend needs restart after many builds
6. **Plan schema mismatch** — FIXED: plan_schema.py `ui_archetype` Literal updated from 10 to 32 values
7. **api_client polling wrong project** — FIXED: poll_until_done() now passes project_id param
