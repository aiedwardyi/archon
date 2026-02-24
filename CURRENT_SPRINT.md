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
**Status:** ✅ Done
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

## Phase 8 UI Polish (✅ Done this session)

### 8.UI.1 — Artifact Cards Link to Artifacts Page
**Status:** ✅ Done
Brief, Build Plan, and Code cards on Versions page are now clickable buttons.
Each saves archon_selected_version to sessionStorage and navigates to
/artifacts?tab=brief|plan|code. ArtifactViewer reads initialTab prop and
sets the active tab on mount. artifacts/page.tsx reads ?tab query param via useSearchParams.

### 8.UI.2 — Account Modals (Profile, Settings, Pricing)
**Status:** ✅ Done
Avatar dropdown Profile, Settings, Pricing items now open modal overlays.
- Profile: mock user info (name, email, avatar initials, member since)
- Settings: masked API key inputs (OpenAI, Gemini, Anthropic) with save button
- Pricing: Free vs Pro plan cards with feature lists and Upgrade button
- Documentation: opens https://docs.archon.dev in new tab
- Upgrade to Pro button in dropdown also opens Pricing modal
New file: frontend/components/account-modals.tsx

## Working Directory
C:\Users\mredw\OneDrive\Desktop\ai-dev-team\

## Branch
enterprise-ui


## Phase 10 — IBM Watson Integration (🔧 In Progress)

### 10.1 — Speech to Text in Chatbox
**Status:** ✅ Done
Mic button in chat input bar. Records voice via MediaRecorder API.
Sends audio blob to POST /api/watson/stt (Flask + ibm-watson).
Transcript auto-populates the input field for user to review and send.
Uses WATSON_STT_URL + WATSON_STT_APIKEY env vars.### 10.2 — Text to Speech on Archon Reply Bubbles
**Status:** 🔧 In Progress
Speaker button on every Archon reply bubble.
POST /api/watson/tts → IBM Watson TTS → audio/mp3 → plays in browser.
Volume2 (idle), Loader2 (loading), VolumeX (playing/stop).
One audio at a time — clicking another stops current.
Uses WATSON_TTS_URL + WATSON_TTS_APIKEY env vars, en-US_AllisonV3Voice.

