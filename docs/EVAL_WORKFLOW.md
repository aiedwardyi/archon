# Eval Loop Dual-PC Workflow

Run eval loops on one PC while developing features on the other. The eval loop continuously improves design quality through Watson Discovery's learning feedback loop.

## How It Works
```
[Home PC - Eval Loop]                    [Work PC - Feature Dev]
       |                                          |
  eval/loops branch                        feat/* branches
       |                                          |
  Build > Score > If 85+ > Ingest          Code > Test > Merge to main
  into Watson Discovery                           |
       |                                   Push + PR to main
  Checkpoint files updated                         |
       |                                   ROADMAP.md / CURRENT_SPRINT.md
  If kit changes needed >                          |
  Commit on eval branch >                         |
  PR to main                                      |
```

## The Learning Loop

1. Eval builds an app from a prompt
2. Screenshots it, scores via Claude Vision (0-100)
3. If score >= 85, auto-ingests the HTML/CSS into Watson Discovery
4. Next build queries Discovery for best reference > higher quality output
5. Repeat — quality improves over time as Discovery accumulates better references

## Setup

### Home PC (Eval Runner)
```powershell
cd C:\Users\mredw\Desktop\ai-dev-team
git checkout main
git pull origin main              # Get latest feature work from Work PC
git checkout -b eval/loops        # Or checkout existing eval branch
.\venv\Scripts\Activate
```

Set API keys:
```powershell
$env:GENAI_API_KEY = "your_gemini_key"
$env:WATSON_DISCOVERY_API_KEY = "your_key"
$env:WATSON_DISCOVERY_URL = "your_url"
$env:WATSON_DISCOVERY_PROJECT_ID = "your_project"
```

Run eval:
```powershell
python eval/eval_runner.py
```

### Work PC (Feature Dev)

Business as usual — feature branches, bug fixes, merge to main.
```powershell
cd C:\Users\mredw\OneDrive\Desktop\ai-dev-team
git checkout -b feat/new-feature
# ... work ...
git push -u origin feat/new-feature
# Merge PR to main
```

## Rules to Avoid Conflicts

| Rule | Why |
|------|-----|
| Eval PC only touches eval/, design kit .css/.txt files, and checkpoint files | No overlap with feature work |
| Feature PC never edits files in eval/ during an active eval run | Prevents merge conflicts |
| Always git pull main on eval PC before starting a new eval run | Picks up latest prompt/agent changes |
| Eval kit improvements go through a PR, not direct push to main | Code review, clean history |
| Note the commit hash in eval/results/checkpoint.md when starting a run | Know which version of prompts the eval tested |

## File Ownership

| Files | Owner | Notes |
|-------|-------|-------|
| eval/, eval/results/ | Home PC (eval) | Checkpoint files, scores, summaries |
| prompts/engineer_core.txt | Work PC (features) | Eval reads but never writes |
| prompts/planner.txt | Work PC (features) | Eval reads but never writes |
| agents/*.py | Work PC (features) | Eval reads but never writes |
| backend/app.py | Work PC (features) | Eval reads but never writes |
| design_kits/*.css, design_kits/*.txt | Either (via PR) | Eval may tune kits, but PRs to main |
| ROADMAP.md, CURRENT_SPRINT.md | Work PC (Teacher chat) | Updated after features ship |

## After an Eval Run

1. Check eval/results/overnight_summary.md for score improvements
2. If any build scored 85+, it was auto-ingested into Watson Discovery
3. If kit changes improved scores, commit them:
```powershell
   git add design_kits/
   git commit -m "eval: tune ecommerce kit — score 88.5 > 91.2"
   git push -u origin eval/loops
```
4. Open PR from eval/loops > main on GitHub
5. Work PC merges the PR

## What Discovery Stores

Each ingested build contains:
- archetype — which archetype this is the reference for
- html_code — the generated index.html
- css_code — the generated style.css
- base_css — the design kit base.css if used
- eval_score — the Claude Vision score (85+)
- prompt — the original user prompt
- plan_json — the Planner output

When the pipeline builds a new app, the Engineer Agent queries Discovery for the best reference build matching the archetype and uses it as a style/structure guide.

## Current Discovery Contents

| Archetype | Project ID | Score | Date |
|-----------|-----------|-------|------|
| Ecommerce | 163 | 88.5 | Mar 10, 2026 |
| Game (FF8) | 161 | 84.5 | Mar 10, 2026 |
| Portfolio | 169 | 83.5 | Mar 10, 2026 |
| Dashboard | 155 | 81.0 | Mar 10, 2026 |
| SaaS Landing | 162 | 76.0 | Mar 10, 2026 |

Target: Get all archetypes to 90+ so every new build has a high-quality reference.

## Monitoring

- eval/results/checkpoint.md — current eval state, which archetype/iteration is running
- eval/results/overnight_summary.md — final scores after a full run
- Flask terminal on eval PC — watch for [Discovery] Ingested project X messages
- Watson Discovery dashboard (IBM Cloud) — verify documents are being added
