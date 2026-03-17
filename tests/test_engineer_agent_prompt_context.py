from agents.engineer_agent import _build_componentized_family_prompt_block


def test_componentized_family_prompt_block_defaults_editor_to_editorial_workspace():
    block = _build_componentized_family_prompt_block(
        "editor",
        "Build a collaborative product brief editor with inline comments, document outline, and publish controls",
    )

    assert "--- GLOBAL QUALITY FAMILY ---" in block
    assert "style_family: editorial_workspace" in block
    assert "visible desktop workspace" in block
    assert "dominant center canvas" in block


def test_componentized_family_prompt_block_routes_trading_dashboard_to_market_terminal_workspace():
    block = _build_componentized_family_prompt_block(
        "dashboard",
        "Build a premium trading terminal dashboard with market chart, watchlist, order actions, and recent trades",
    )

    assert "style_family: market_terminal_workspace" in block
    assert "chart-first or market-control-first shell" in block
    assert "mono-friendly numeric treatment" in block


def test_componentized_family_prompt_block_adds_logistics_domain_overlay():
    block = _build_componentized_family_prompt_block(
        "dashboard",
        "Create a high-density operations control center for logistics with fleet status, route delays, shipment exceptions, and dispatch alerts",
    )

    assert "style_family: operator_console_workspace" in block
    assert "--- DOMAIN OVERLAY ---" in block
    assert "domain_overlay: operations_control_tower" in block
    assert "dispatch queue" in block or "dispatch alerts" in block


def test_componentized_family_prompt_block_adds_treasury_domain_overlay():
    block = _build_componentized_family_prompt_block(
        "dashboard",
        "Create a treasury operations terminal with cash positions, FX exposure, settlement queues, and funding windows",
    )

    assert "style_family: market_terminal_workspace" in block
    assert "domain_overlay: treasury_liquidity_terminal" in block
    assert "cash positions" in block
    assert "funding windows" in block
    assert "visible side rail" in block


def test_componentized_family_prompt_block_skips_iteration_mode():
    block = _build_componentized_family_prompt_block(
        "form",
        "Build a premium onboarding wizard with validation and success state",
        existing_code="export default function App() { return null; }",
    )

    assert block == ""
