# Current Sprint — Phase 8: Publish + Client Deliverables

## Sprint Goal
Make Archon's output shareable and client-ready.
Agencies need to send clients a URL, not a zip file.

## Previous Sprints Complete ✅

### Phase 7D — UI Polish ✅
### Phase 7F — Chatbox Upgrades ✅
### Phase 7G — Output Quality v2 ✅
### Phase 7H — Conversational Chatbox ✅
- PM Agent routes build vs chat
- Archon reply bubbles in chatbox
- Chat history passed into build context
- Download project as zip with assets

## Phase 8 — Publish + Client Deliverables

### 8.1 — One-Click Publish
**Status:** 🔴 TODO
POST /api/projects/<id>/versions/<version>/publish
Copies code to published/<slug>/, stitches CSS inline, returns shareable URL.
GET /published/<slug> serves the app.
Publish button in Artifacts page with copy-to-clipboard URL.

### 8.2 — PDF Export
**Status:** 🔴 TODO
Export full build history as PDF — Brief + Plan + Code summary per version.
Client audit trail deliverable.

### 8.3 — Client Shareable Read-Only Link
**Status:** 🔴 TODO
Read-only view of Versions page for a specific project.
No login required. Shows all versions, artifacts, previews.

### 8.4 — White-Label Option
**Status:** 🔴 TODO
Agency branding on client-facing views.

## Working Directory
C:\Users\mredw\Desktop\ai-dev-team\

## Branch
enterprise-ui
