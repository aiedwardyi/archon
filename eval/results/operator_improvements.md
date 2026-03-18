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
