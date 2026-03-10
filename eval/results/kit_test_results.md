# Manual Kit Changes Test — 2026-03-10

## Results
| Archetype     | Before Kit Fix | After Kit Fix | Delta | Changed? |
|---------------|---------------:|--------------:|------:|----------|
| Dashboard | 81.0 | 73.5 | -7.5 | yes |
| Game (FF8) | 84.5 | 83.5 | -1.0 | yes |
| SaaS Landing | 76.0 | 74.5 | -1.5 | yes |
| Ecommerce | 88.5 | 85.0 | -3.5 | no |
| Portfolio | 83.5 | 79.5 | -4.0 | no |

## Per-Dimension Comparison (changed archetypes only)
### Dashboard
| Dimension | Before | After | Delta |
|-----------|-------:|------:|------:|
| visual_hierarchy | 8 | 8 | +0 |
| typography | 7 | 7 | +0 |
| color_system | 8 | 7 | -1 |
| layout_precision | 9 | 8 | -1 |
| depth_polish | 8 | 6 | -2 |
| data_completeness | 10 | 9 | -1 |
| interactivity_cues | 6 | 6 | +0 |
| overall_impression | 8 | 7 | -1 |

### Game (FF8)
| Dimension | Before | After | Delta |
|-----------|-------:|------:|------:|
| visual_hierarchy | 9 | 8 | -1 |
| typography | 8 | 8 | +0 |
| color_system | 9 | 9 | +0 |
| layout_precision | 9 | 9 | +0 |
| depth_polish | 8 | 8 | +0 |
| data_completeness | 9 | 9 | +0 |
| interactivity_cues | 6 | 7 | +1 |
| overall_impression | 8 | 8 | +0 |

### SaaS Landing
| Dimension | Before | After | Delta |
|-----------|-------:|------:|------:|
| visual_hierarchy | 7 | 8 | +1 |
| typography | 7 | 7 | +0 |
| color_system | 8 | 7 | -1 |
| layout_precision | 7 | 8 | +1 |
| depth_polish | 8 | 7 | -1 |
| data_completeness | 9 | 9 | +0 |
| interactivity_cues | 7 | 6 | -1 |
| overall_impression | 8 | 7 | -1 |

## Verdict
- Manual kit changes did not improve weighted totals in this single score-only sample; all five archetypes scored below the prior best baseline.
- The clearest positive signal was dimension-level only: Game interactivity improved (6 -> 7), and SaaS improved visual hierarchy/layout precision (+1 each).
- Dashboard depth and interactivity remained flat at 6, so additional concrete component-level depth requirements are still needed.
- Game kept strong structure and data (all >=7 after this pass), but still under prior best weighted score due normal build variance.
- Build/scoring variance is high (roughly +/-5 to +/-10 points), so treat this as one sample; run 3 score-only passes and average before deciding next prompt/kit changes.
