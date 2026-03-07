# Quality Tuning Diagnostic Report

Date: 2026-03-08
Branch: feat/quality-target-tuning

## Low vs High Score Comparison

### SaaS Landing (71.5 vs 77.0)
- Low run issues:
  - Scorer marked lower layout precision/interactivity/data completeness (7/6/6) despite same build.
  - Visual issues visible in HTML/screenshot: generic logo cloud icons, relatively flat mockup visuals, and small low-contrast micro text in dark UI.
- High run strengths:
  - Strong section completeness and strong CTA coverage.
  - Includes working pricing toggle + FAQ accordion (Alpine), realistic plan prices ($0/$29/$79 monthly, annual variants), and robust content density.
- Key difference:
  - No source difference. `quality_tuning_v1` uses one screenshot and one HTML (`generated/132/v1/code/src/index.html`) for all 3 scores. Difference is scorer variance.
- HTML checks (same for low/high):
  - Sections: 9 `<section>` blocks (+ nav/footer).
  - Pricing with dollar amounts: Yes.
  - CTA styling/alignment: Mostly good; card CTAs are centered/full-width in pricing.
  - JavaScript interactivity: Yes (Alpine pricing toggle + FAQ expand/collapse).
  - Placeholder text: No lorem; no obvious generic placeholders.
  - Broken/overlap: No major overlap/breakage in screenshot.
  - Production feel: Good but somewhat template-like in visuals.

### Dashboard (61.5 vs 87.5)
- Low run issues:
  - Scorer penalized color/depth/layout heavily (5/5/6), and interactivity cues (5).
  - Real source issue: filter/sort affordances are subtle; several interactions are mostly visual (no true filter/sort behavior).
- High run strengths:
  - Excellent data completeness and layout structure (KPI row, chart, holdings table, watchlist, news).
  - Strong production-like look in screenshot; clean spacing and strong readability.
- Key difference:
  - No source difference. All 3 scores came from one screenshot and one HTML (`generated/133/v1/code/src/index.html`).
  - This is the clearest evidence of scorer instability (61.5 to 87.5 spread on identical input).
- HTML checks (same for low/high):
  - Sections: 0 literal `<section>` tags, but 5 major content regions/panels.
  - Pricing with dollar amounts: N/A (dashboard archetype).
  - CTA styling/alignment: Buttons are styled and aligned, but filter/sort are low-emphasis.
  - JavaScript interactivity: Yes (count-up animation, periodic row flash).
  - Placeholder text: No lorem; only normal input placeholder (`Search assets...`).
  - Broken/overlap: No visible overlap/breakage.
  - Production feel: Strongly production-like.

### Portfolio (68.0 vs 83.5)
- Low run issues:
  - Scorer downgraded typography/depth/overall (6/6/6).
  - Actual quality issues in source: generic persona (`Jane Doe`), form placeholders (`Your Name`, `your@email.com`), and mixed image style consistency.
- High run strengths:
  - Strong section coverage, complete portfolio content (skills, experience, projects, contact), and clear CTAs.
  - Good structural layout and content completeness.
- Key difference:
  - No source difference. All scores are from one screenshot/HTML (`generated/134/v1/code/src/index.html`).
- HTML checks (same for low/high):
  - Sections: 6 `<section>` blocks (+ hero/header/nav/footer).
  - Pricing with dollar amounts: N/A.
  - CTA styling/alignment: Generally styled/aligned correctly.
  - JavaScript interactivity: Yes (smooth-scroll links, contact form submit handler/alert).
  - Placeholder text: Present in contact form placeholders and generic identity content.
  - Broken/overlap: No hard overlap/breakage, but readability/visual consistency is weaker than dashboard.
  - Production feel: Mid; looks like a polished template rather than a distinct brand site.

## Previous Baseline Methodology
- Were previous bests single runs or averages?
  - Previous “best” numbers in `overnight_summary.md` (SaaS 78.2, Dashboard 79.0, Portfolio 81.8) match prior `*_scores.json` files that are 3-run averages (`num_runs: 3`, `averaged_total` equals those bests).
  - So they were not single-score snapshots; they were best-of-many-build averaged scores.
- If single runs, what would old averages likely look like?
  - Not applicable exactly (they were already 3-run averages), but they were cherry-picked best builds.
  - If averaging across multiple historical candidate builds (not just best):
    - SaaS historical mean (available runs): ~66.2
    - Dashboard historical mean (available runs): ~73.5
    - Portfolio historical mean (available runs): ~77.4
  - This indicates prior “best” values were optimistic upper-bound selections, not central tendency.

## Prompt Truncation Check
- Engineer prompt total tokens (approx):
  - `prompts/engineer_core.txt`: 18,155 chars (~4.5k tokens).
  - `prompts/engineer.txt`: 141,659 chars (~35.4k tokens).
  - Actual scaffold path for these builds used `engineer_core.txt + archetype file` (because `ui_archetype` is set), typically ~25k chars before task payload (~6-8k tokens, plus task/context).
- LLM context limit for engineer calls:
  - In code, no custom input truncation is applied.
  - Engineer calls use Gemini `gemini-2.5-flash` with `max_output_tokens: 65536` (output cap only).
  - Effective input context is model-side (large; no repo-side clipping logic found).
- Is truncation happening?
  - No evidence of truncation in repository code path.
  - Likelihood: low.
- Where do score-killers + self-check appear in the assembled prompt?
  - In `engineer_core.txt`, they are near the end of core prompt text.
  - In assembled prompt (`engineer_core + archetype + task`), they are before appended archetype instructions and task block (not at absolute tail).

## Root Cause Hypothesis
Primary cause of the apparent score drop is evaluation methodology and scorer variance, not a clear regression in generated HTML quality:
1. Current comparison uses 3-run averages from a single new build per archetype versus previous best-of-many-build averages.
2. Scorer variance is very high on identical screenshot input (especially Dashboard: 61.5 to 87.5).
3. Low/high “runs” in this quality tuning set are not different builds; they are repeated judgments of the same artifact.
4. Some real quality weakness exists (especially SaaS/Portfolio brand distinctiveness and subtle interactivity), but it does not explain the full deltas by itself.

## Recommended Next Steps
1. Separate build variance from scorer variance:
   - For each archetype, generate multiple builds (e.g., 5-10), score each build with fixed deterministic settings or larger replicate count, then compare distribution means.
2. Stop comparing against “best build ever” as primary KPI:
   - Track median and p25/p75 across a fixed build sample.
3. Stabilize scoring:
   - Reduce scorer randomness (temperature/seed if supported) and/or use consensus scoring across more runs.
4. Keep prompt-length concern lower priority:
   - No evidence of prompt truncation in engineer path; focus first on evaluation design and variance controls.