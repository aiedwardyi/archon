# Componentized Build Failure Audit

## Phase 1

### Pre-Fix Build Success Rate

- Sample: 10 fresh dashboard builds with usable `last_preview_build.json` results
- Successful preview builds: 2 / 10
- Failed preview builds: 8 / 10
- Pre-fix success rate: 20%
- Successful projects in this sample: `623`, `632`

Additional dashboard submissions during the audit hit long pipeline timeouts in `pm` and did not produce `last_preview_build.json`; those were excluded from the 10-build preview-success calculation because the failure family could not be classified from Vite output.

### Failure Table

| Project ID | Error Type | File | Line | Pattern Description | Existing Repair Covers It? |
|---|---|---|---|---|---|
| 625 | Unterminated regular expression | `src/components/Dashboard.tsx` | 219 | Ternary branch inside `kpis.map()` leaks an orphan `</div>` after the false branch value span, closing the card early and leaving the later delta span outside the JSX subtree. | Partial: similar to ternary orphan-closer repair, but current rule misses nested map/KPI branch shape. |
| 626 | Expected `)` but found `className` | `src/components/DashboardLayout.tsx` | 67 | Sidebar user block closes `</div></div></aside></div>` before `<main>`, leaving `<main className="main-content">` outside the active return tree. | Partial: related to orphaned parent-family/sidebar recovery, but current recovery does not re-home the leaked `<main>` sibling. |
| 628 | Unexpected `>=` | `src/components/Dashboard.tsx` | 211 | JSX attribute comparison is corrupted into `stroke={ticker.delta />= 0 ? ...}`; the `/>` splice turns a numeric comparison into malformed JSX syntax. | No: current arrow/handler repairs target `= />`, not `/>=` inside attribute expressions. |
| 634 | Expected `)` but found `for` | `src/components/ChartCard.tsx` | 11 | Multi-line prose note escapes a block comment and leaves a raw `Box (0-1000 for x...)` line in code before `const monthlyData`, breaking parsing. Build log also shows a duplicate `label` JSX prop in `src/components/KpiCards.tsx`. | Partial: comment-bleed repairs exist, but they do not absorb this free-standing prose line or the duplicate JSX prop. |
| 635 | Expected `)` but found `className` | `src/components/DashboardLayout.tsx` | 64 | Same family as `626`: sidebar footer closes the wrapper stack too early, then `<main>` starts after stray closers. | Partial: same gap as `626`. |
| 636 | Expected `)` but found `className` | `src/components/DashboardLayout.tsx` | 66 | Same family as `626`/`635`: leaked sidebar/user wrapper closers eject `<main>` from the return block. | Partial: same gap as `626`. |
| 639 | Expected `>` but found `(` | `src/components/Chart.tsx` | 37 | A multiline `<circle>` element loses the `fill=` attribute key, leaving a bare `var(--accent)"` token on the next line and collapsing the remainder of the SVG/tooltip JSX onto one malformed line. | No: current JSX/comment repairs do not restore missing attribute keys in split multiline SVG elements. |
| 640 | Invalid `}` in JSX element; expected `)` before `style` | `src/App.tsx` | 159 | Tooltip conditional drops the opening wrapper for `{tooltip && (...)}` and leaves a raw closing `)}` immediately before the next sibling `<div style=...>`. | Partial: related to JSX branch/root balancing, but current cleanup does not reconstruct this orphan conditional close pattern. |

### Corruption Families Found

| Pattern | Frequency | Representative Projects | Fix Needed |
|---|---|---|---|
| Nested JSX branch leaks orphan closing tags inside mapped KPI/dashboard cards | 2 | `625`, `640` | Strengthen structural branch repair so leaked `</div>` or `)}` closers are removed or rebalanced before JSX root balancing. |
| Sidebar/footer wrapper closes early and ejects `<main>` outside the return tree | 3 | `626`, `635`, `636` | Generalize parent-family/sibling repair to restore `<main>` under the layout root after premature `</aside></div>` leaks. |
| JSX attribute/operator splice corruption | 1 | `628` | Add deterministic repair for `/>=` corruption inside attribute expressions. |
| Comment/prose bleed into executable code plus duplicate JSX prop emission | 1 | `634` | Extend comment-note normalization to swallow raw prose continuation lines and add a duplicate-JSX-prop cleanup for repeated `label=` style collisions. |
| Multiline SVG element loses attribute key and collapses following JSX | 1 | `639` | Add structural repair for split SVG attributes where a line begins with a raw CSS/token value instead of `fill=` / another attribute name. |

### Notes

- The first attempt to use `python eval/eval_loop.py --archetype dashboard --runs 10 --skip-image-gen` generated fresh dashboard projects but stalled in the screenshot/score layer. Phase 1 was completed from the generated workspace artifacts plus a direct build-only audit loop against the same backend.
- Sampled failure projects used for the 10-build pre-fix rate: `623`, `625`, `626`, `628`, `632`, `634`, `635`, `636`, `639`, `640`.

## Post-Fix

Pending.
