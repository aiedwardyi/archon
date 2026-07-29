from agents import engineer_agent
from agents.engineer_agent import (
    EngineerAgent,
    _build_componentized_family_prompt_block,
    _build_componentized_specialized_contract_block,
)
from schemas.engineering_schema import EngineeringResult, FileArtifact
from schemas.plan_schema import Task


def _componentized_task() -> Task:
    return Task(
        id="PLAN-ENGINEER-1",
        description="Build a componentized test app",
        outputs=["code"],
        execution_hint="engineer",
        task_type="scaffold",
        scaffold_mode="componentized_app",
        output_files=["src/App.tsx"],
        ui_archetype="dashboard",
    )


def _dummy_engineering_result() -> EngineeringResult:
    return EngineeringResult(
        task_id="PLAN-ENGINEER-1",
        summary="ok",
        files=[FileArtifact(path="src/App.tsx", content="export default function App() { return null; }\n")],
    )


def test_componentized_family_prompt_block_defaults_editor_to_editorial_workspace():
    block = _build_componentized_family_prompt_block(
        "editor",
        "Build a collaborative product brief editor with inline comments, document outline, and publish controls",
    )

    assert "--- GLOBAL QUALITY FAMILY ---" in block
    assert "style_family: editorial_workspace" in block
    assert "visible desktop workspace" in block
    assert "dominant center canvas" in block
    assert "generic lane titles like `Workspace`, `Notes`, or `Inspector`" in block


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
    assert "reroute" in block or "escalate" in block


def test_componentized_family_prompt_block_adds_sales_domain_overlay():
    block = _build_componentized_family_prompt_block(
        "dashboard",
        "Create a live sales deal room for account executives with pipeline stages, champion risk, mutual action plans, and renewal pressure",
    )

    assert "style_family: operator_console_workspace" in block
    assert "domain_overlay: sales_deal_room" in block
    assert "mutual action plans" in block or "champion health" in block
    assert "log call" in block or "advance stage" in block


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
    assert "release" in block or "hedge" in block


def test_componentized_family_prompt_block_skips_iteration_mode():
    block = _build_componentized_family_prompt_block(
        "form",
        "Build a premium onboarding wizard with validation and success state",
        existing_code="export default function App() { return null; }",
    )

    assert block == ""


def test_componentized_specialized_contract_block_for_builder_prompt():
    block = _build_componentized_specialized_contract_block(
        "editor",
        "Build an AI startup builder workspace with prompt layers, live preview, variant runs, launch blockers, and QA notes",
        reference_code={"label": "legacy-designai-startup-builder"},
    )

    assert "SPECIALIZED BUILDER / STUDIO CONTRACT" in block
    assert "startup-builder or AI design studio" in block
    assert "Do not use a KPI row as the main focal point" in block
    assert "paper-like brief" in block
    assert "darker charcoal product chrome" in block
    assert "three identical raw textareas" in block
    assert "legacy-designai-startup-builder" in block


def test_componentized_specialized_contract_block_for_compliance_wizard_prompt():
    block = _build_componentized_specialized_contract_block(
        "form",
        "Build a vendor onboarding wizard with compliance documents, approval routing, blocker summary, and an application snapshot sidebar",
        reference_code={"label": "legacy-ai-automation-onboarding-wizard"},
    )

    assert "SPECIALIZED ENTERPRISE WIZARD CONTRACT" in block
    assert "enterprise onboarding or compliance workflow" in block
    assert "snapshot or status lane" in block
    assert "pending approvals" in block
    assert "legacy-ai-automation-onboarding-wizard" in block


def test_engineer_agent_skips_reference_images_when_internal_iteration_disables_them(tmp_path, monkeypatch):
    image_path = tmp_path / "reference.png"
    image_path.write_bytes(b"fake-image")
    captured: dict[str, object] = {}

    def _fake_run_gemini(_client, contents: str, ref_images=None):
        captured["contents"] = contents
        captured["ref_images"] = ref_images
        return _dummy_engineering_result()

    monkeypatch.setattr(engineer_agent, "_run_gemini", _fake_run_gemini)
    monkeypatch.setenv("ENGINEER_MODEL", "gemini")
    monkeypatch.setenv("OFFLINE_MODE", "false")

    agent = EngineerAgent(client=object())
    agent.run(
        _componentized_task(),
        user_prompt="Tighten the seeded content.",
        existing_code="export default function App() { return null; }",
        reference_images=[str(image_path)],
        attach_reference_images=False,
    )

    assert captured["ref_images"] is None
    assert "IMPORTANT: The user has provided visual reference images." not in str(captured["contents"])


def test_engineer_agent_keeps_reference_images_when_iteration_explicitly_allows_them(tmp_path, monkeypatch):
    image_path = tmp_path / "reference.png"
    image_path.write_bytes(b"fake-image")
    captured: dict[str, object] = {}

    def _fake_run_gemini(_client, contents: str, ref_images=None):
        captured["contents"] = contents
        captured["ref_images"] = ref_images
        return _dummy_engineering_result()

    monkeypatch.setattr(engineer_agent, "_run_gemini", _fake_run_gemini)
    monkeypatch.setenv("ENGINEER_MODEL", "gemini")
    monkeypatch.setenv("OFFLINE_MODE", "false")

    agent = EngineerAgent(client=object())
    agent.run(
        _componentized_task(),
        user_prompt="Match the uploaded visual reference.",
        existing_code="export default function App() { return null; }",
        reference_images=[str(image_path)],
        attach_reference_images=True,
    )

    ref_images = captured["ref_images"]
    assert isinstance(ref_images, list)
    assert ref_images[0][0] == "reference.png"
    assert "IMPORTANT: The user has provided visual reference images." in str(captured["contents"])
