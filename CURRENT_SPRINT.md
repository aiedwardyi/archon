# Current Sprint — Phase 7G: Output Quality v2

## Sprint Goal
Improve generated app visual quality to Lovable/v0 level through deterministic
UI geometry contracts, two-file CSS split, and premium CSS design seeds.

## Previous Sprints Complete ✅

### Phase 7D — UI Polish
- ✅ 7D.1 Navbar real project name + version
- ✅ 7D.2 Project ID column on Projects table
- ✅ 7D.3 Delete project + Delete All with confirmation
- ✅ 7D.4 Avatar dropdown (v0-style) with theme toggle, credits, upgrade
- ✅ 7D.5 Preview height increased to 700px
- ✅ 7D.6 Artifacts version sync via custom event bus

### Phase 7F — Chatbox Upgrades
- ✅ 7F.1 File + media upload with drag-and-drop
- ✅ 7F.2 Graceful agent reply for unsupported inputs
- ✅ 7F.3 Master log accumulation

### Bonus wins
- ✅ Parallel pipeline (Architecture + Design run simultaneously, ~30-40% faster)
- ✅ DALL-E content filter fix (IP name sanitizer)

## Phase 7G — Output Quality v2

### 7G.1 — UI Archetype Lock
**Status:** ✅ Done
Planner classifies ui_archetype, Engineer enforces it as hard constraint.
ArchetypeRules typed model with required_blocks, required_interactions, avoid.

### 7G.2 — Layout + Content Contracts
**Status:** ✅ Done
layout_contract: deterministic geometry (regions, sidebar, topbar, main_grid, density).
content_contract: kpi_labels, table_columns, seed_rows, required_states.
All 10 archetypes have full contracts in planner.txt.

### 7G.3 — Two-File Output Split
**Status:** ✅ Done
Engineer outputs src/index.html (500 lines, structure+JS) + src/style.css (400 lines, all CSS).
Preview base tag + static route added to serve CSS from src/ directory.

### 7G.4 — Preview Inline CSS Stitching
**Status:** 🔴 TODO
Replace base tag approach with Flask stitching index.html + style.css into single blob.
Fixes 404s on anchor href="#" links caused by base tag.

### 7G.5 — CSS Design Seed
**Status:** 🔴 TODO
Inject mandatory CSS pattern examples into engineer.txt:
glow effects, glass panels, gradient borders, shimmer keyframes, chart draw animation, stagger.

### 7G.6 — Pipeline Real-Time Update Bug
**Status:** 🔴 TODO
Agent cards stuck on "Building..." after pipeline completes.
Requires page navigation to refresh status.

## Working Directory
C:\Users\mredw\Desktop\ai-dev-team\

## Branch
enterprise-ui
