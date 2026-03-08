# Quality Tuning v2 — CSS Score-Killers Test

Date: 2026-03-08
Branch: feat/quality-target-tuning
Commit: 0059219 (added CSS rendering score-killers 14-16)

## Changes Tested
- Score-killer 14: Text overlapping images must have contrast overlay
- Score-killer 15: No clipped/truncated headings
- Score-killer 16: No identical repeated icons in logo clouds

## Results (5 runs, trimmed mean)

| Archetype | Old Baseline | v1 (regressed) | v2 (this run) | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Trimmed Mean | Delta vs Old | Delta vs v1 |
|-----------|-------------|----------------|---------------|-------|-------|-------|-------|-------|-------------|-------------|-------------|
| SaaS Landing | 77.83 | 73.83 | 70.67 | 76.50 | 59.50 | 74.50 | 66.50 | 71.00 | 70.67 | -7.16 | -3.16 |
| Portfolio | 81.33 | 77.33 | N/A (build failed) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

Trimmed mean formula used: drop highest and lowest of 5 runs, average middle 3.
- SaaS Landing sorted runs: 59.50, 66.50, 71.00, 74.50, 76.50
- Trimmed middle 3: 66.50, 71.00, 74.50 => (66.50 + 71.00 + 74.50) / 3 = 70.67

## Build Notes
- SaaS Landing project: `137` (completed)
- Portfolio project: `138` (failed)
- Portfolio retry policy: retried once (v1 and v2 executions both failed)
- Portfolio error on both attempts: `EngineerAgent: no JSON object found in model output`

## Visual Inspection
For each build, note:
- Are all headings fully visible (no clipping)?
- Does text over images have contrast overlays?
- Are logo cloud icons visually distinct (not identical SVGs)?
- Any other rendering issues?

### SaaS Landing
- Headings appear fully visible in the full-page screenshot; no obvious clipping/truncation.
- Text over imagery is readable; dark treatment/overlay appears to preserve contrast in hero and image sections.
- No explicit logo-cloud section observed in this render, so icon-distinctness check is not directly applicable.
- Other issues: overall visual polish remains inconsistent (dense dark blocks, limited spacing rhythm), with high scorer variance (59.5 to 76.5).

### Portfolio
- Build did not complete after one retry, so no generated UI was available for inspection.
- Captured preview is backend placeholder (`Live preview will appear here when your build is complete`).
- Heading/overlay/icon checks could not be evaluated due to missing rendered output.

## Conclusion
- Did the CSS score-killers fix the regression? no (SaaS remained below v1 and old baseline; Portfolio could not be scored due to build failure).
- Recommendation: iterate further.
  - Stabilize Portfolio pipeline parsing failure first (`no JSON object found in model output`) before quality comparison.
  - Re-run v2 on both archetypes after parser/build stability is restored.
