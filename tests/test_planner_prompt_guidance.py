from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PLANNER_PROMPT = (REPO_ROOT / "prompts" / "planner.txt").read_text(encoding="utf-8")


def test_planner_prompt_routes_builder_workspaces_away_from_dashboard():
    assert "If the PRD mentions builder, studio, prompt layers, live preview rail, inspector, canvas, variant runs, or launch blockers -> editor, NOT dashboard" in PLANNER_PROMPT


def test_planner_prompt_routes_onboarding_flows_to_form():
    assert "If the PRD mentions onboarding, wizard, application flow, approvals, blocker summary, requirements summary, review sidebar, or compliance steps -> form, NOT dashboard" in PLANNER_PROMPT
    assert 'form      -> required_blocks: ["step_indicator", "active_step_panel", "review_sidebar", "submit_or_continue_bar"]' in PLANNER_PROMPT


def test_planner_prompt_reframes_ai_product_as_workspace_tool():
    assert "ai_product   -> AI/ML product apps, LLM workspaces, copilots, model ops tools, and multi-panel AI tools where the main surface is chat, runs, or model controls rather than a builder canvas" in PLANNER_PROMPT
    assert "saas_landing -> SaaS/tech product marketing, AI product homepages, pricing pages, docs-led marketing" in PLANNER_PROMPT
