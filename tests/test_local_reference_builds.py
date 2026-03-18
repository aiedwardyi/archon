from utils.reference_build_registry import (
    get_archetype_benchmark_guidance,
    infer_domain_overlay,
    infer_style_family,
    load_local_reference_build,
    suggest_reference_archetype,
)


def test_load_local_reference_build_returns_project_149_for_saas_landing():
    reference = load_local_reference_build("saas_landing")

    assert reference is not None
    assert reference["project_id"] == 149
    assert reference["source"] == "local_benchmark"
    assert "Build Products" in reference["html_code"]
    assert ".hero" in reference["css_code"]


def test_suggest_reference_archetype_matches_badass_site_prompt():
    match = suggest_reference_archetype("bbuild me a badass site")

    assert match is not None
    assert match["project_id"] == 149
    assert match["archetype"] == "saas_landing"


def test_saas_guidance_includes_pysimple_reference_notes():
    reference = load_local_reference_build("saas_landing")

    assert reference is not None
    assert reference["project_id"] == 149
    assert "legacy-pysimple-cli-saas" in reference["benchmark_guidance"]


def test_load_local_reference_build_supports_published_only_legacy_examples():
    reference = load_local_reference_build("game")

    assert reference is not None
    assert reference["project_id"] == 43
    assert "Charmander" in reference["html_code"]
    assert "--fire" in reference["css_code"]
    assert "premium-feeling transitions" in reference["benchmark_guidance"]
    assert "count-up hero stats" in reference["benchmark_guidance"]


def test_suggest_reference_archetype_matches_pokemon_prompt():
    match = suggest_reference_archetype(
        "can you build me a pokemon fan page website with charmander, bulbasaur, and squirtle characters?"
    )

    assert match is not None
    assert match["project_id"] == 43
    assert match["archetype"] == "game"


def test_suggest_reference_archetype_matches_ff7_prompt():
    match = suggest_reference_archetype(
        "Create me a Final Fantasy 7 theme fan page site with cloud, barrett, and tifa plus a map"
    )

    assert match is not None
    assert match["project_id"] == 38
    assert match["archetype"] == "game_ff7"


def test_load_local_reference_build_returns_ff7_specific_benchmark_subset():
    reference = load_local_reference_build("game_ff7")

    assert reference is not None
    assert reference["archetype"] == "game_ff7"
    assert reference["project_id"] == 76
    assert "Final Fantasy VII" in reference["html_code"]
    assert "Cloud Strife" in reference["html_code"]
    assert "Charmander" not in reference["html_code"]
    assert "legacy-ff7-legends-of-midgar" in reference["benchmark_guidance"]
    assert "legacy-pokemon-starters-fan-page" not in reference["benchmark_guidance"]


def test_load_local_reference_build_returns_ff8_specific_benchmark_subset():
    reference = load_local_reference_build("game_ff8")

    assert reference is not None
    assert reference["archetype"] == "game_ff8"
    assert reference["project_id"] == 171
    assert reference["label"] == "legacy-ff8-seed-operatives-fan-page"
    assert reference["render_mode"] == "legacy"
    assert "Squall Leonhart" in reference["html_code"]
    assert ".hero-title-name" in reference["css_code"]
    assert "branch-ff8-garden-archive-20260316" in reference["benchmark_guidance"]
    assert "legacy-ff8-seed-operatives-fan-page" in reference["benchmark_guidance"]
    assert "legacy-ff7-legends-of-midgar" not in reference["benchmark_guidance"]


def test_load_local_reference_build_uses_cinematic_family_for_digimon_prompt():
    reference = load_local_reference_build(
        "game",
        prompt_text="build a premium Digimon fan page with character profiles, weapons, world map, and cinematic lore interactions",
    )

    assert reference is not None
    assert reference["style_family"] == "cinematic_collector_fanpage"
    assert reference["selection_reason"] == "style_family"
    assert reference["project_id"] == 76
    assert reference["label"] == "legacy-ff7-legends-of-midgar"
    assert "STYLE FAMILY (cinematic_collector_fanpage)" in reference["benchmark_guidance"]
    assert "branch-ff8-garden-archive-20260316" in reference["benchmark_guidance"]
    assert "legacy-ff7-legends-of-midgar" in reference["benchmark_guidance"]
    assert "legacy-pokemon-starters-fan-page" not in reference["benchmark_guidance"]


def test_get_archetype_benchmark_guidance_merges_multiple_game_examples():
    guidance = get_archetype_benchmark_guidance("game")

    assert "legacy-pokemon-starters-fan-page" in guidance
    assert "branch-ff8-garden-archive-20260316" in guidance
    assert "legacy-ff9-zidane-vivi-tribute" in guidance
    assert "legacy-precision-calculator-ui" in guidance
    assert "legacy-alpha-launch-wizard" in guidance


def test_infer_style_family_defaults_editor_to_editorial_workspace():
    assert infer_style_family("editor") == "editorial_workspace"


def test_infer_style_family_defaults_dashboard_to_operator_console_workspace():
    assert infer_style_family("dashboard") == "operator_console_workspace"


def test_infer_domain_overlay_routes_logistics_prompt_to_operations_control_tower():
    prompt = (
        "Create a high-density operations control center for a logistics team with fleet status, "
        "route delays, shipment exceptions, and dispatch alerts."
    )

    family = infer_style_family("dashboard", prompt)

    assert family == "operator_console_workspace"
    assert infer_domain_overlay("dashboard", prompt, style_family=family) == "operations_control_tower"


def test_infer_domain_overlay_routes_sales_prompt_to_sales_deal_room():
    prompt = (
        "Create a collaborative sales workspace for account executives managing pipeline stages, "
        "call notes, next actions, and deal risks."
    )

    family = infer_style_family("dashboard", prompt)

    assert family == "operator_console_workspace"
    assert infer_domain_overlay("dashboard", prompt, style_family=family) == "sales_deal_room"


def test_infer_domain_overlay_routes_treasury_prompt_to_treasury_liquidity_terminal():
    prompt = (
        "Create a treasury operations terminal for monitoring cash positions, FX exposure, "
        "settlement queues, and funding windows."
    )

    family = infer_style_family("dashboard", prompt)

    assert family == "market_terminal_workspace"
    assert infer_domain_overlay("dashboard", prompt, style_family=family) == "treasury_liquidity_terminal"


def test_load_local_reference_build_defaults_editor_to_editorial_workspace_family():
    reference = load_local_reference_build("editor")

    assert reference is not None
    assert reference["project_id"] == 233
    assert reference["style_family"] == "editorial_workspace"
    assert reference["selection_reason"] == "style_family"
    assert "STYLE FAMILY (editorial_workspace)" in reference["benchmark_guidance"]
    assert "legacy-briefai-product-brief-editor" in reference["benchmark_guidance"]
    assert "save, publish, review, or collaborator state" in reference["benchmark_guidance"]


def test_load_local_reference_build_routes_ai_product_builder_prompt_to_editor_workspace_family():
    reference = load_local_reference_build(
        "ai_product",
        prompt_text="Build an AI web design assistant with a startup builder workspace, onboarding flow, and founder control surface",
    )

    assert reference is not None
    assert reference["project_id"] == 176
    assert reference["style_family"] == "product_builder_workspace"
    assert reference["selection_reason"] == "style_family"
    assert "STYLE FAMILY (product_builder_workspace)" in reference["benchmark_guidance"]
    assert "paper-like brief or document canvas" in reference["benchmark_guidance"]
    assert "darker premium tool shell" in reference["benchmark_guidance"]
    assert "Do not lead with KPI cards or a stack of plain textareas" in reference["benchmark_guidance"]
    assert "legacy-designai-startup-builder" in reference["benchmark_guidance"]


def test_load_local_reference_build_routes_dashboard_trading_prompt_to_fintech_family():
    reference = load_local_reference_build(
        "dashboard",
        prompt_text="Build a premium trading terminal dashboard with market chart, watchlist, order actions, and recent trades",
    )

    assert reference is not None
    assert reference["project_id"] == 190
    assert reference["style_family"] == "market_terminal_workspace"
    assert reference["selection_reason"] == "style_family"
    assert "STYLE FAMILY (market_terminal_workspace)" in reference["benchmark_guidance"]
    assert "legacy-tradeflow-terminal-fintech" in reference["benchmark_guidance"]


def test_load_local_reference_build_carries_logistics_overlay_guidance():
    reference = load_local_reference_build(
        "dashboard",
        prompt_text=(
            "Create a logistics control tower with fleet status, shipment exceptions, route delays, "
            "and dispatch alerts in a serious desktop-first workspace."
        ),
    )

    assert reference is not None
    assert reference["style_family"] == "operator_console_workspace"
    assert reference["domain_overlay"] == "operations_control_tower"
    assert "DOMAIN OVERLAY (operations_control_tower)" in reference["benchmark_guidance"]
    assert "reroute" in reference["benchmark_guidance"] or "escalate" in reference["benchmark_guidance"]


def test_load_local_reference_build_carries_sales_overlay_guidance():
    reference = load_local_reference_build(
        "dashboard",
        prompt_text=(
            "Create a sales deal room for account executives managing pipeline stages, champion risk, "
            "renewal pressure, and mutual action plans."
        ),
    )

    assert reference is not None
    assert reference["style_family"] == "operator_console_workspace"
    assert reference["domain_overlay"] == "sales_deal_room"
    assert "DOMAIN OVERLAY (sales_deal_room)" in reference["benchmark_guidance"]
    assert "log call" in reference["benchmark_guidance"] or "advance stage" in reference["benchmark_guidance"]


def test_load_local_reference_build_carries_treasury_overlay_guidance():
    reference = load_local_reference_build(
        "dashboard",
        prompt_text=(
            "Create a treasury operations terminal for cash positions, FX exposure, settlement queues, "
            "and funding windows."
        ),
    )

    assert reference is not None
    assert reference["style_family"] == "market_terminal_workspace"
    assert reference["domain_overlay"] == "treasury_liquidity_terminal"
    assert "DOMAIN OVERLAY (treasury_liquidity_terminal)" in reference["benchmark_guidance"]
    assert "release" in reference["benchmark_guidance"] or "hedge" in reference["benchmark_guidance"]


def test_load_local_reference_build_defaults_form_to_guided_setup_wizard_family():
    reference = load_local_reference_build("form")

    assert reference is not None
    assert reference["project_id"] == 220
    assert reference["style_family"] == "guided_setup_wizard"
    assert reference["selection_reason"] == "style_family"
    assert "STYLE FAMILY (guided_setup_wizard)" in reference["benchmark_guidance"]
    assert "legacy-ai-automation-onboarding-wizard" in reference["benchmark_guidance"]
    assert "visible snapshot or status lane" in reference["benchmark_guidance"]
    assert "pending counts and approval state visible" in reference["benchmark_guidance"]
