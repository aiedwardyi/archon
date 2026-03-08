# Re-Baseline Comparison - Fair Scoring

Date: 2026-03-08
Branch: feat/quality-target-tuning

## Methodology
- All screenshots scored 5 times each
- Trimmed mean: drop highest and lowest, average middle 3
- This eliminates the single-run-vs-average bias from previous comparison

## Screenshot Selection
- Old baseline screenshots (from original best-score JSON references):
  - SaaS Landing: `eval/results/saas_landing/iter3a/screenshot_full.png`
  - Dashboard: `eval/results/dashboard/iter3a/screenshot_full.png`
  - Portfolio: `eval/results/portfolio/iter2/screenshot_full.png`
- New quality tuning screenshots:
  - SaaS Landing: `eval/results/saas_landing/quality_tuning_v1/screenshot.png`
  - Dashboard: `eval/results/dashboard/quality_tuning_v1/screenshot.png`
  - Portfolio: `eval/results/portfolio/quality_tuning_v1/screenshot.png`

## Old Baseline Scores (5 runs each)

| Archetype | Original Single | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Trimmed Mean |
|-----------|----------------|-------|-------|-------|-------|-------|-------------|
| SaaS Landing | 78.2 | 80.5 | 74.5 | 79.0 | 80.0 | 72.0 | 77.83 |
| Dashboard | 79.0 | 76.5 | 80.5 | 76.5 | 79.0 | 79.5 | 78.33 |
| Portfolio | 81.8 | 82.5 | 72.5 | 82.5 | 79.0 | 85.0 | 81.33 |

## New Quality Tuning Scores (5 runs each)

| Archetype | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Trimmed Mean |
|-----------|-------|-------|-------|-------|-------|-------------|
| SaaS Landing | 72.0 | 77.0 | 71.5 | 74.5 | 75.0 | 73.83 |
| Dashboard | 61.5 | 79.0 | 87.5 | 88.0 | 80.0 | 82.17 |
| Portfolio | 80.5 | 68.0 | 83.5 | 46.5 | 83.5 | 77.33 |

## Fair Comparison (Trimmed Means)

| Archetype | Old Trimmed Mean | New Trimmed Mean | Delta | Verdict |
|-----------|-----------------|-----------------|-------|---------|
| SaaS Landing | 77.83 | 73.83 | -4.00 | regressed |
| Dashboard | 78.33 | 82.17 | +3.84 | improved |
| Portfolio | 81.33 | 77.33 | -4.00 | regressed |

## Scorer Variance Analysis

| Archetype | Old Range (max-min) | New Range (max-min) |
|-----------|-------------------|-------------------|
| SaaS Landing | 8.5 | 5.5 |
| Dashboard | 4.0 | 26.5 |
| Portfolio | 12.5 | 37.0 |

## Conclusions
- Prompt tuning result is mixed: Dashboard improved, but SaaS and Portfolio regressed on trimmed mean.
- Scorer reliability is unstable for some cases (especially new Dashboard/Portfolio), with variance larger than many observed deltas.
- A practical confidence rule from this run: do not trust deltas smaller than 5 points; for high-variance cases, require 10+ points or more runs.
- Recommendation: need more data before merge-level conclusions. Increase runs per archetype and/or use multiple scorers before deciding.
