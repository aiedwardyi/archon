# Codex Eval Improvements Log

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
