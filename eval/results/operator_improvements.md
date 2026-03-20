# Eval Improvements Log

Use one section per experiment. Update this file before moving to the next archetype, and persist it at least once per hour even if no prompt or kit change is accepted.

## Cycle Template

### Cycle 000 - YYYY-MM-DD HH:MM
- Archetype:
- Baseline average across 3 runs:
- Weakest dimensions:
- Exact change made:
- File changed:
- Test average across 3 runs:
- Delta:
- Verdict: committed | reverted
- Notes:
- Next hypothesis:

## Experiments

### Cycle 001 - 2026-03-11 14:00
- Archetype: Pending first operator run
- Baseline average across 3 runs: Pending
- Weakest dimensions: Pending
- Exact change made: Pending
- File changed: Pending
- Test average across 3 runs: Pending
- Delta: Pending
- Verdict: Pending
- Notes: Log created to standardize manual eval-loop experiments.
- Next hypothesis: Start with the weakest current archetype after reading `overnight_summary.md` and `checkpoint.md`.

### Cycle 019 - 2026-03-19 02:00
- Archetype: dashboard (build pipeline fixes)
- Baseline average across 3 runs: N/A (builds were failing)
- Weakest dimensions: Build failures — 60% of componentized builds failed
- Exact changes made:
  1. Added _repair_orphan_block_comment_close to strip stray */
  2. Added tsconfig pseudo-comment key stripping
  3. Added _repair_jsx_return_unclosed_tags for missing/misnested JSX closers
  4. Added JSX INTEGRITY section to engineer_componentized.txt
  5. Added data completeness rules to engineer_componentized.txt
  6. Created eval/eval_loop.py with retry-safe screenshots and dist/ verification
  7. Created eval/start_backend.py to run without watchdog reloader
- Files changed: utils/componentized_runtime.py, prompts/engineer_componentized.txt, eval/eval_loop.py, eval/start_backend.py
- Test average across 3 runs: 67.5 (single run — 3-run baseline pending)
- Delta: N/A (first scorable run on this branch)
- Verdict: committed (all changes)
- Notes: Component splitting prompt rules caused 0% success rate and were reverted. Data completeness rules helped (9/10 score). Build success rate still ~40-50%.
- Next hypothesis: Target dashboard depth_polish (6), interactivity_cues (6), layout_precision (6) via dashboard.txt tweaks.

### Cycle 020 - 2026-03-19 04:00
- Archetype: dashboard (prompt tuning experiments)
- Baseline average across 3 runs: 67.5 (single successful run)
- Weakest dimensions: layout_precision (6), depth_polish (6), interactivity_cues (6)
- Exact changes made:
  1. Added LAYOUT STRUCTURE section to dashboard.txt → REVERTED (0% build success)
  2. Added COMPONENT SPLITTING to engineer_componentized.txt → REVERTED (0% build success)
  3. Kept data completeness rules and JSX integrity rules
- Files changed: prompts/archetypes/dashboard.txt, prompts/engineer_componentized.txt
- Test average across 3 runs: 81.5 (1/3 runs scoreable due to build failures)
- Delta: +0.5 vs baseline (81.0)
- Verdict: committed (reverts + kept improvements)
- Notes: Prescriptive code structure rules consistently degrade build success. Data completeness rules (charts/tables/KPI minimums) consistently improve scores without hurting builds. The 81.5 score had data_completeness 10/10, layout_precision 9/10.
- Key learning: Less is more for prompt engineering with Gemini. Content requirements work; structural mandates break.
- Next hypothesis: Target typography (7) and interactivity_cues (7) as next weakest dimensions.

### Cycle 021 - 2026-03-19 06:30
- Archetype: fintech, portfolio, ecommerce (cross-archetype eval)
- Fintech single run: 71.0 (baseline 83.5, delta -12.5)
  - Built on first attempt! visual_hierarchy 8, data_completeness 9, typography 6, depth_polish 6
- Portfolio: 0/5 builds succeeded (all preview builds failed)
- Ecommerce: 0/5 builds succeeded (all preview builds failed)
- Dashboard 3-run baseline: 81.5 from 1 successful build (2/3 runs failed to build)
- Verdict: Build reliability is the #1 blocker. Dashboard and fintech can build; portfolio and ecommerce cannot.
- Notes: Build success rate varies dramatically by archetype. The portfolio and ecommerce archetypes produce more complex layouts that are harder for Gemini to generate syntactically correct JSX for.
- Next hypothesis: Focus build reliability improvements on the most common TSX error patterns across portfolio/ecommerce builds. Alternatively, try adjusting these archetype prompts to reduce JSX complexity.

### Cycle 022 - 2026-03-19 08:00
- Archetype: portfolio, ecommerce (build reliability + eval with new fixes)
- Build reliability fixes applied:
  1. Wrap sibling SVG child elements in React fragments
  2. Remove extra closing tags with no matching opener
  3. Distinguish HTML void tags (lowercase) from React components (capitalized)
- Portfolio: 83.0 (baseline 83.5, delta -0.5) — built on 3rd attempt
  - visual_hierarchy 9, typography 9, overall_impression 9, data_completeness 7
- Ecommerce: 0/5 builds succeeded — still failing consistently
- Verdict: committed fixes
- Notes: SVG fragment wrapping and void tag distinction fixed portfolio builds. Ecommerce builds have different failure patterns — likely needs ecommerce-specific investigation.
- Next hypothesis: Investigate ecommerce-specific build failure patterns (CartDrawer, HashRouter issues).

### Cycle 023 - 2026-03-19 09:00
- Archetype: ecommerce (SVG void element fix + continued investigation)
- Added SVG elements to VOID_JSX_ELEMENT_RE (circle, line, path, etc.)
- Ecommerce: still 0/5 builds despite fix
- Root cause: Gemini 2.5 Flash consistently produces minified single-line components for ecommerce (1000+ chars per line), plus CartProvider/Router context wrapping errors
- This is a model-level quality issue specific to ecommerce's complexity (routing, cart state, multi-page)
- Verdict: SVG void fix committed (helps other archetypes), ecommerce needs archetype-specific intervention
- Next hypothesis: Simplify the ecommerce prompt to reduce routing/state complexity, or switch to a simpler ecommerce pattern without React Router.

### Cycle 024 - 2026-03-19 11:00
- Archetype: fintech (self-check items reverted), ecommerce (Alpine→React swap tested)
- Fintech with self-check items: 63.5 (WORSE than 71.0 baseline — reverted)
- Ecommerce with Alpine→React swap: still 0/5 builds
- .map() callback JSX repair: committed (fixes unclosed tags in array renders)
- Verdict: ALL fintech prompt changes reverted. Ecommerce Alpine→React swap kept but doesn't fix builds.
- Key insight: The ORIGINAL archetype prompts (written by Codex) are already well-tuned. ANY additions — even self-check items — regress quality. The only safe place for additions is engineer_componentized.txt (the base engineer prompt), not archetype-specific files.
- Next hypothesis: Focus on build reliability (normalizer fixes) rather than prompt tuning. The normalizer improvements have been the most effective lever.

### Cycle 002 - 2026-03-11 14:42
- Archetype: saas_landing
- Baseline average across 3 runs: 81.33
- Weakest dimensions: None below 7.0
- Exact change made: Rewrote the saas_landing archetype section in prompts/engineer.txt to target the weakest baseline dimension.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/engineer.txt
- Test average across 3 runs: 77.17
- Delta: -4.16
- Verdict: reverted
- Notes: Branch eval/loops. Change reverted because delta did not exceed +1.0.
- Next hypothesis: Try the other editable surface for this archetype or target the next-lowest dimension.

### Cycle 003 - 2026-03-11 15:01
- Archetype: saas_landing
- Baseline average across 3 runs: 74.5
- Weakest dimensions: interactivity_cues, typography
- Exact change made: Updated saas_landing.txt with one targeted instruction cluster for interactivity_cues, typography.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/saas_landing.txt
- Test average across 3 runs: 71.33
- Delta: -3.17
- Verdict: reverted
- Notes: Branch eval/loops. Change reverted because delta did not exceed +1.0.
- Next hypothesis: Try the other editable surface for this archetype or target the next-lowest dimension.

### Cycle 004 - 2026-03-11 15:22
- Archetype: saas_landing
- Baseline average across 3 runs: 75.33
- Weakest dimensions: None below 7.0
- Exact change made: Rewrote the saas_landing archetype section in prompts/engineer.txt to target the weakest baseline dimension.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/engineer.txt
- Test average across 3 runs: 81.33
- Delta: +6.00
- Verdict: committed
- Notes: Branch eval/loops. Improvement exceeded +1.0.
- Next hypothesis: Move to the next weakest archetype.

### Cycle 005 - 2026-03-11 15:41
- Archetype: saas_landing
- Baseline average across 3 runs: 72.5
- Weakest dimensions: typography, interactivity_cues
- Exact change made: Updated saas_landing.txt with one targeted instruction cluster for typography, interactivity_cues.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/saas_landing.txt
- Test average across 3 runs: 74.0
- Delta: +1.50
- Verdict: committed
- Notes: Branch eval/loops. Improvement exceeded +1.0.
- Next hypothesis: Move to the next weakest archetype.

### Cycle 006 - 2026-03-11 16:01
- Archetype: saas_landing
- Baseline average across 3 runs: 73.33
- Weakest dimensions: typography, interactivity_cues
- Exact change made: Updated saas_landing.txt with one targeted instruction cluster for typography, interactivity_cues.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/saas_landing.txt
- Test average across 3 runs: 75.17
- Delta: +1.84
- Verdict: committed
- Notes: Branch eval/loops. Improvement exceeded +1.0.
- Next hypothesis: Move to the next weakest archetype.

### Cycle 007 - 2026-03-12 10:02
- Archetype: dashboard
- Baseline average across 3 runs: 73.5
- Weakest dimensions: depth_polish, interactivity_cues
- Exact change made: Updated dashboard.css with one targeted instruction cluster for depth_polish, interactivity_cues.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/dashboard.css
- Test average across 3 runs: 52.0
- Delta: -21.50
- Verdict: reverted
- Notes: Branch eval/loops. Change reverted because delta did not exceed +1.0.
- Next hypothesis: Try the other editable surface for this archetype or target the next-lowest dimension.

### Cycle 008 - 2026-03-13 02:22
- Archetype: dashboard
- Baseline average across 3 runs: 66.0
- Weakest dimensions: data_completeness, depth_polish
- Exact change made: Updated dashboard.txt with one targeted instruction cluster for data_completeness, depth_polish.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/dashboard.txt
- Test average across 3 runs: 77.17
- Delta: +11.17
- Verdict: kept
- Notes: Branch eval/loops. Improvement exceeded +1.0.
- Next hypothesis: Move to the next weakest archetype.

### Cycle 009 - 2026-03-13 03:11
- Archetype: dashboard
- Baseline average across 3 runs: 66.83
- Weakest dimensions: data_completeness, depth_polish
- Exact change made: Updated dashboard.txt with one targeted instruction cluster for data_completeness, depth_polish.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/dashboard.txt
- Test average across 3 runs: 72.83
- Delta: +6.00
- Verdict: kept
- Notes: Branch eval/loops. Improvement exceeded +1.0.
- Next hypothesis: Move to the next weakest archetype.

### Cycle 010 - 2026-03-13 03:57
- Archetype: fintech
- Baseline average across 3 runs: 68.0
- Weakest dimensions: typography, depth_polish
- Exact change made: Updated fintech.txt with one targeted instruction cluster for typography, depth_polish.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/fintech.txt
- Test average across 3 runs: 76.17
- Delta: +8.17
- Verdict: kept
- Notes: Branch eval/loops. Improvement exceeded +1.0.
- Next hypothesis: Move to the next weakest archetype.

### Cycle 011 - 2026-03-13 04:43
- Archetype: editor
- Baseline average across 3 runs: 71.33
- Weakest dimensions: typography, depth_polish
- Exact change made: Updated editor.txt with one targeted instruction cluster for typography, depth_polish.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/editor.txt
- Test average across 3 runs: 78.5
- Delta: +7.17
- Verdict: kept
- Notes: Branch eval/loops. Improvement exceeded +1.0.
- Next hypothesis: Move to the next weakest archetype.

### Cycle 012 - 2026-03-13 05:22
- Archetype: editor
- Baseline average across 3 runs: 78.5
- Weakest dimensions: None below 7.0
- Exact change made: Updated editor.txt with one targeted instruction cluster for the weakest baseline dimension.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/editor.txt
- Test average across 3 runs: 75.17
- Delta: -3.33
- Verdict: reverted
- Notes: Branch eval/loops. Change reverted because delta did not exceed +1.0.
- Next hypothesis: Try the other editable surface for this archetype or target the next-lowest dimension.

### Cycle 013 - 2026-03-13 06:09
- Archetype: fintech
- Baseline average across 3 runs: 72.5
- Weakest dimensions: typography, depth_polish
- Exact change made: Updated fintech.txt with one targeted instruction cluster for typography, depth_polish.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/fintech.txt
- Test average across 3 runs: 67.83
- Delta: -4.67
- Verdict: reverted
- Notes: Branch eval/loops. Change reverted because delta did not exceed +1.0.
- Next hypothesis: Try the other editable surface for this archetype or target the next-lowest dimension.

### Cycle 014 - 2026-03-13 07:04
- Archetype: fintech
- Baseline average across 3 runs: 72.33
- Weakest dimensions: depth_polish, interactivity_cues
- Exact change made: Updated fintech.css with one targeted instruction cluster for depth_polish, interactivity_cues.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/fintech.css
- Test average across 3 runs: 74.5
- Delta: +2.17
- Verdict: kept
- Notes: Branch eval/loops. Improvement exceeded +1.0.
- Next hypothesis: Move to the next weakest archetype.

### Cycle 015 - 2026-03-13 07:46
- Archetype: editor
- Baseline average across 3 runs: 72.83
- Weakest dimensions: typography, interactivity_cues
- Exact change made: Updated editor.txt with one targeted instruction cluster for typography, interactivity_cues.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/editor.txt
- Test average across 3 runs: 79.5
- Delta: +6.67
- Verdict: kept
- Notes: Branch eval/loops. Improvement exceeded +1.0.
- Next hypothesis: Move to the next weakest archetype.

### Cycle 016 - 2026-03-13 08:29
- Archetype: editor
- Baseline average across 3 runs: 70.67
- Weakest dimensions: depth_polish, interactivity_cues
- Exact change made: Updated editor.css with one targeted instruction cluster for depth_polish, interactivity_cues.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/editor.css
- Test average across 3 runs: 70.83
- Delta: +0.16
- Verdict: reverted
- Notes: Branch eval/loops. Change reverted because delta did not exceed +1.0.
- Next hypothesis: Try the other editable surface for this archetype or target the next-lowest dimension.

### Cycle 017 - 2026-03-13 09:09
- Archetype: editor
- Baseline average across 3 runs: 71.17
- Weakest dimensions: typography, depth_polish
- Exact change made: Updated editor.txt with one targeted instruction cluster for typography, depth_polish.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/editor.txt
- Test average across 3 runs: 76.67
- Delta: +5.50
- Verdict: kept
- Notes: Branch eval/loops. Improvement exceeded +1.0.
- Next hypothesis: Move to the next weakest archetype.

### Cycle 018 - 2026-03-13 09:51
- Archetype: fintech
- Baseline average across 3 runs: 71.33
- Weakest dimensions: typography, depth_polish
- Exact change made: Updated fintech.txt with one targeted instruction cluster for typography, depth_polish.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/fintech.txt
- Test average across 3 runs: 68.17
- Delta: -3.16
- Verdict: reverted
- Notes: Branch eval/loops. Change reverted because delta did not exceed +1.0.
- Next hypothesis: Try the other editable surface for this archetype or target the next-lowest dimension.

### Cycle 025 - 2026-03-19 15:12
- Archetype: dashboard
- Baseline average across 3 runs: 10.0
- Weakest dimensions: data_completeness, layout_precision
- Exact change made: Updated dashboard.txt with one targeted instruction cluster for data_completeness, layout_precision.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/dashboard.txt
- Test average across 3 runs: 10.0
- Delta: +0.00
- Verdict: reverted
- Notes: Branch feat/local-eval-models. Change reverted because delta did not exceed +1.0.
- Next hypothesis: Try the other editable surface for this archetype or target the next-lowest dimension.

### Cycle 026 - 2026-03-19 15:32
- Archetype: dashboard
- Baseline average across 3 runs: 10.0
- Weakest dimensions: data_completeness, layout_precision
- Exact change made: Updated dashboard.txt with one targeted instruction cluster for data_completeness, layout_precision.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/dashboard.txt
- Test average across 3 runs: 10.0
- Delta: +0.00
- Verdict: reverted
- Notes: Branch feat/local-eval-models. Change reverted because delta did not exceed +1.0.
- Next hypothesis: Try the other editable surface for this archetype or target the next-lowest dimension.

### Cycle 027 - 2026-03-19 22:52
- Archetype: dashboard
- Baseline average across 3 runs: 10.0
- Weakest dimensions: data_completeness, layout_precision
- Exact change made: Updated dashboard.txt with one targeted instruction cluster for data_completeness, layout_precision.
- File changed: C:/Users/mredw/Desktop/ai-dev-team/prompts/archetypes/dashboard.txt
- Test average across 3 runs: 10.0
- Delta: +0.00
- Verdict: reverted
- Notes: Branch main. Change reverted because delta did not exceed +1.0.
- Next hypothesis: Try the other editable surface for this archetype or target the next-lowest dimension.
