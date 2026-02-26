# Current Sprint — Phase 15: Consumer Frontend v2 + Iteration Hardening

## Sprint Goal
Ship a consumer-facing frontend with the Versions page as the core moat feature.
Harden iteration mode so edits are surgical, not full redesigns.

## Working Directory
C:\Users\mredw\OneDrive\Desktop\ai-dev-team\

## Branch
main (enterprise-ui merged and deleted)

---

## Completed This Sprint ✅

### Phase 14 — Iteration Mode Fixes ✅
- Scope enforcement path normalization (`safe_write.py` `_tail_after_code()`)
- Archetype lock conversion phrase detection (prevent false positives like "add a mini game")
- Ancestor chain traversal for failed versions (walk up to 5 hops to find last successful code)
- Design asset reuse on iterations (skip DALL-E regeneration, reuse ancestor's `last_design_assets.json`)
- Asset URL version extraction from `local_path` (correct `/api/assets/{pid}/{version}/` URL)
- Planner iteration file constraints (force `output_files` to `src/index.html` + `src/style.css` only)
- Preview endpoint CSS/JS inlining (inline all `*.css` and `*.js` files from `code/src/`)
- Strengthened `iteration_context` in engineer prompt (5 strict surgical edit rules, placed before main prompt)

### Phase 15 — Consumer Frontend v2 ✅
- Copied and wired Projects/frontend to repo as `frontend-consumer2/` (port 3002)
- Connected to Flask backend via `orchestrator.ts` service layer
- Real iframe preview with desktop/mobile viewport toggle
- **Versions page (THE MOAT)** — timeline + split panel + live preview per version
- Restore version functionality from versions timeline
- File viewer (Code tab) wired to real `/api/projects/:id/versions/:v/files`
- Non-technical wording pass (Brief, Build Plan, What Was Built, Publish)
- Korean/English language toggle with `i18n.ts` translation system (30+ keys)
- CORS allowlist updated for ports 3001 and 3002
- Fixed versions preview URL bug (`version` field vs `version_number`)
- Complete Korean translation coverage for all UI strings

### Phase 15.2 — Consumer Frontend Polish ✅
- Renamed all "ai-dev-team" references to "Archon" across 8 files
- Versions timeline displays newest first (matches API DESC order)
- Versions right panel iframe glow effect (indigo shadow + hover)
- Hide restore button on current/latest version (`maxVersion` guard)
- Version card glow/contrast polish (darker bg, indigo ring, gradient overlay)
- Logo split corrected: "Arch" + "on" (violet accent on "on")
- Korean translations wired to Sidebar (9 strings via `t()`)
- Korean translations wired to Logs tab (`runtimeLogs`, `simulateFault`)

### Phase 15.3 — Consumer UX Bug Fixes ✅
- Reset `localPrd`/`localPlan`/`localTasks`/`previewVersion` on `projectId` change (stale data across project switches)
- Removed `opacity-0`/`opacity-100` transition on workspace div (iframe invisible after build completes)
- Progress bar persisted to `sessionStorage` (survives navigate-away-and-back during builds)
- Expanded `getTechColor` to match 7 keyword categories (frontend/backend/database/state/ml/hosting/styling)
- Tech map rendering handles no-colon entries (natural-language PRD format)
- Engineer prompt: added MOCK DATA REQUIREMENT block (no more empty-state generated apps)
- Added bell notification instruction to CLAUDE.md

### Phase 15.1 — Repo Cleanup ✅
- Removed `apps/offline-vite-react` (unused old frontend)
- Added `node_modules/`, `dist/`, `.venv/`, `.claude/` to `.gitignore`
- Merged `enterprise-ui` branch into `main`
- Deleted `enterprise-ui` local branch

### Previously Completed ✅
- Phase 13.1 — Chat message persistence (DB-backed)
- Phase 13.2 — User model + owner_id foundation
- Phase 10.4 — App type lock (archetype guardrail)
- Phase 10.1-10.2 — Watson STT/TTS integration
- Phase 8.1 — One-click publish
- Phase 8.UI.1-2 — Artifact card linking + account modals

---

## What's Next

### Frontend Cleanup
- Decide between `frontend-consumer/` (port 3001) and `frontend-consumer2/` (port 3002)
- Remove the one we don't keep
- Single consumer frontend going forward

### Phase 8.3 — Client Share Link
- Read-only shareable URL for client deliverables
- No login required
- Shows all versions, artifacts, and previews

### Watson STT/TTS in Consumer Frontend
- Wire mic button + speaker button into `frontend-consumer2`
- Same Watson endpoints already working in enterprise frontend

### Image Generation Fix
- Character portrait blending in hero section
- DALL-E content filter edge cases

### Korean Translation — Remaining
- Delete confirmation modal strings
- Error messages and edge case strings
- Dynamic project names (leave untranslated)
