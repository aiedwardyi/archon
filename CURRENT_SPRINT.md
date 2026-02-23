# Current Sprint — Phase 7H: Conversational Chatbox

## Sprint Goal
Make the chatbox smart — not every message triggers a full pipeline build.
Archon should reply conversationally for questions, advice, and clarifications.

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

### Phase 7G — Output Quality v2
- ✅ 7G.1 UI archetype lock (Planner classifies, Engineer enforces)
- ✅ 7G.2 Layout + content contracts (all 10 archetypes)
- ✅ 7G.3 Two-file output split (index.html + style.css)
- ✅ 7G.4 Preview inline CSS stitching
- ✅ 7G.5 CSS design seed (glow/glass/shimmer in engineer.txt)
- ✅ 7G.6 Pipeline real-time update bug fix

### Bonus wins
- ✅ Parallel pipeline (~30-40% faster)
- ✅ DALL-E content filter fix

## Phase 7H — Conversational Chatbox

### 7H.1 — PM Agent routing (build vs chat decision)
**Status:** 🔴 TODO
Add `classify_intent` method to PMAgent.
Returns {"type": "chat", "message": "..."} or {"type": "build"}.
Lightweight GPT call — decides if user wants to build or just talk.

### 7H.2 — Chat response as Archon message bubble
**Status:** 🔴 TODO
Update /iterate endpoint: if chat → return immediately with response_type: "chat".
Frontend: render messages array with role: "user" | "archon" as chat bubbles.

### 7H.3 — Publish button
**Status:** 🔴 TODO
Add Publish button to Pipeline page for completed builds.

## Working Directory
C:\Users\mredw\Desktop\ai-dev-team\

## Branch
enterprise-ui
