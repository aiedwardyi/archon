# Current Sprint — Phase 15.5: Enterprise UI Polish

## Status: IN PROGRESS

## Completed This Sprint
- [x] frontend-v4 running on port 8080
- [x] Projects page wired to real API
- [x] version_count in backend (no more N+1 flood)
- [x] Project selection state shared across all tabs
- [x] VersionsView with real data + real iframe preview
- [x] ArtifactsView with real Brief, Plan, Code, Tasks, Logs
- [x] Navbar shows real project name + version
- [x] Archon favicon + page title
- [x] Encoding corruption fixed

## Next Up
- [ ] Checkbox fix in ProjectTable
- [ ] + New Project modal
- [ ] Delete selected projects with confirmation modal
- [ ] Files changed count in VersionsView
- [ ] Pipeline tab wired to real execution

## Ports
- Flask backend: 5000
- Enterprise UI (frontend-v4): 8080
- Studio frontend: 3000
- Consumer frontend: 3001/3002

## Key Files
- frontend-v4/src/pages/Index.tsx — main state management
- frontend-v4/src/services/api.ts — all API calls
- frontend-v4/src/components/ProjectTable.tsx
- frontend-v4/src/components/VersionsView.tsx
- frontend-v4/src/components/ArtifactsView.tsx
- backend/models.py — version_count added to to_dict()
