from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from backend.app import (
    build_componentized_shell_polish_guidance,
    build_design_context,
    build_componentized_refinement_prompt,
    detect_componentized_quality_issues,
    expand_componentized_iteration_scaffold_scope,
    extend_componentized_scope,
    load_componentized_base_css,
    select_componentized_build_repair_scope,
    select_componentized_content_fix_scope,
    select_componentized_refinement_scope,
    validate_componentized_contract_outputs,
)
from utils.componentized_runtime import (
    build_componentized_preview,
    collect_componentized_editable_files,
    collect_componentized_reverse_dependents,
    ensure_componentized_workspace_support,
    _normalize_componentized_file,
    _repair_componentized_orphaned_parent_family_children,
    _normalize_run_on_natural_language_notes,
    collect_existing_code_context,
    extract_feature_inventory,
    extract_visual_dna,
    infer_scaffold_mode,
    rewrite_componentized_asset_api_urls,
    rewrite_preview_file_references,
    rewrite_preview_runtime_asset_references,
    stage_componentized_design_assets,
)
from utils.design_families import build_componentized_design_family_guidance
from utils.design_families import build_componentized_shell_family_guidance
from utils.design_families import should_apply_componentized_global_family_layer
from utils.componentized_quality import (
    classify_componentized_content_file,
    collect_quality_issue_codes,
    evaluate_componentized_density,
    evaluate_componentized_multi_file_completeness,
    evaluate_componentized_semantic_completeness,
    parse_componentized_build_errors,
)

TMP_ROOT = REPO_ROOT / ".tmp-tests"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


def _case_dir(name: str) -> Path:
    path = TMP_ROOT / name
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    return path


class ComponentizedRuntimeTests(unittest.TestCase):
    def _assert_jsx_return_would_parse(self, source: str) -> None:
        match = re.search(r"return\s*\((?P<body>[\s\S]*?)\);\s*", source)
        self.assertIsNotNone(match, "expected a JSX return block")
        body = match.group("body")
        self.assertNotIn("<>", body)
        self.assertNotIn("</>", body)

        token_re = re.compile(r"</?(?P<tag>[A-Za-z][A-Za-z0-9.-]*)\b[^>]*?/?>")
        void_tags = {
            "area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr",
            "circle", "ellipse", "line", "path", "polygon", "polyline", "rect", "stop", "use",
        }

        stack: list[str] = []
        top_level_roots = 0
        for token_match in token_re.finditer(body):
            token = token_match.group(0)
            tag = token_match.group("tag")

            if token.startswith("</"):
                self.assertTrue(stack, f"unexpected closing tag </{tag}>")
                self.assertEqual(stack[-1], tag, f"misnested closing tag </{tag}>")
                stack.pop()
                continue

            is_void = token.endswith("/>") or (tag[0].islower() and tag.lower() in void_tags)
            if not stack:
                top_level_roots += 1
            if not is_void:
                stack.append(tag)

        self.assertFalse(stack, f"unclosed JSX tags: {stack}")
        self.assertEqual(top_level_roots, 1, "expected a single top-level JSX root")

    def test_game_archetypes_bypass_componentized_global_family_layer(self):
        self.assertFalse(should_apply_componentized_global_family_layer("game"))
        self.assertFalse(should_apply_componentized_global_family_layer("game_ff7"))
        self.assertFalse(should_apply_componentized_global_family_layer("fan_page"))
        self.assertTrue(should_apply_componentized_global_family_layer("fintech"))

    def test_game_archetypes_emit_no_global_family_guidance(self):
        self.assertEqual(build_componentized_design_family_guidance("game_ff8"), "")
        self.assertEqual(build_componentized_shell_family_guidance("game_ff9"), "")
        self.assertIn("design_family: data_dense", build_componentized_design_family_guidance("fintech"))

    def test_ai_product_builder_prompts_route_design_family_to_workspace(self):
        guidance = build_componentized_design_family_guidance(
            "ai_product",
            "Build an AI product builder workspace with prompt layers, variant runs, launch blockers, and a live preview rail.",
        )

        self.assertIn("design_family: workspace", guidance)
        self.assertIn("center canvas plus a visible preview", guidance)

    def test_ai_product_setup_prompts_route_design_family_to_guided_flow(self):
        guidance = build_componentized_design_family_guidance(
            "ai_product",
            "Build an onboarding wizard with integrations, compliance review sidebar, blocker summary, and approval routing.",
        )

        self.assertIn("design_family: guided_flow", guidance)
        self.assertIn("top product bar, visible step rail, and a compact summary or snapshot lane", guidance)

    def test_game_workspace_support_backfills_empty_region_images_with_local_asset(self):
        code_dir = _case_dir("componentized-runtime-game-region-images")
        try:
            asset_dir = code_dir / "public" / "generated-assets"
            asset_dir.mkdir(parents=True, exist_ok=True)
            (asset_dir / "hero_background.png").write_bytes(b"png")

            data_dir = code_dir / "src" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            data_path = data_dir / "pokemonData.ts"
            data_path.write_text(
                (
                    "export const REGIONS_DATA = [\n"
                    "  { id: 'kanto', image: '' },\n"
                    '  { id: "johto", image: "" },\n'
                    "];\n"
                ),
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir, ui_archetype="game")

            updated = data_path.read_text(encoding="utf-8")
            self.assertNotIn("image: ''", updated)
            self.assertNotIn('image: ""', updated)
            self.assertIn("generated-assets/hero_background.png", updated)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_game_workspace_support_replaces_literal_map_placeholder_cards(self):
        code_dir = _case_dir("componentized-runtime-game-map-placeholder")
        try:
            asset_dir = code_dir / "public" / "generated-assets"
            asset_dir.mkdir(parents=True, exist_ok=True)
            (asset_dir / "hero_background.png").write_bytes(b"png")

            component_dir = code_dir / "src" / "components"
            component_dir.mkdir(parents=True, exist_ok=True)
            component_path = component_dir / "LocationCard.tsx"
            component_path.write_text(
                (
                    "export default function LocationCard({ region }: { region: { name: string; image: string } }) {\n"
                    "  return (\n"
                    "    <div className=\"location-image-wrapper\">\n"
                    "      <div\n"
                    "        style={{ width: '100%', height: '200px' }}\n"
                    "      >Map Placeholder</div>\n"
                    "      <h3>{region.name}</h3>\n"
                    "    </div>\n"
                    "  );\n"
                    "}\n"
                ),
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir, ui_archetype="game")

            updated = component_path.read_text(encoding="utf-8")
            self.assertNotIn("Map Placeholder", updated)
            self.assertIn('<img className="location-image"', updated)
            self.assertIn('src={region.image || "generated-assets/hero_background.png"}', updated)
            self.assertIn('alt={`${region.name} map illustration`}', updated)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_data_dense_family_guidance_requires_explicit_typography_roles(self):
        guidance = build_componentized_design_family_guidance("fintech")

        self.assertIn("display face", guidance)
        self.assertIn("mono/tabular numeric face", guidance)
        self.assertIn("dominant center insight zone", guidance)
        self.assertIn("equal-height card mosaics", guidance)
        self.assertIn("Dashboard Overview", guidance)
        self.assertIn("`View` / `Details`", guidance)
        self.assertIn("`Watchlist`, `Activity`, or `Recent Updates`", guidance)

    def test_fintech_shell_polish_guidance_requires_mono_numeric_consistency(self):
        guidance = build_componentized_shell_polish_guidance("fintech")

        self.assertIn("Mono treatment is mandatory across every numeric surface", guidance)
        self.assertIn("JetBrains Mono or equivalent", guidance)
        self.assertIn("right rail should hold at least two stacked support modules", guidance)

    def test_dashboard_shell_polish_guidance_rejects_generic_dense_shell_copy(self):
        guidance = build_componentized_shell_polish_guidance("dashboard")

        self.assertIn("Dashboard Overview", guidance)
        self.assertIn("Portfolio Overview", guidance)
        self.assertIn("`View` / `Details`", guidance)
        self.assertIn("`Activity Feed`, `Recent Updates`, or plain `Watchlist` filler", guidance)

    def test_guided_flow_family_guidance_requires_review_and_blocker_context(self):
        guidance = build_componentized_design_family_guidance("form")

        self.assertIn("review, blocker, or readiness card", guidance)
        self.assertIn("one dominant active step plus one compact review/result preview", guidance)
        self.assertIn("ready to launch", guidance)
        self.assertIn("top product bar, visible step rail, and a compact summary or snapshot lane", guidance)

    def test_workspace_family_guidance_requires_authored_topbar_and_lane_labels(self):
        guidance = build_componentized_design_family_guidance("editor")

        self.assertIn("real topbar or command strip", guidance)
        self.assertIn("useful outline rows, comments, settings, tasks, or status modules", guidance)
        self.assertIn("`Workspace`, `Notes`, or `Inspector`", guidance)
        self.assertIn("darker premium tool shell", guidance)

    def test_guided_flow_shell_polish_guidance_requires_compact_review_states(self):
        guidance = build_componentized_shell_polish_guidance("form")

        self.assertIn("review, blocker, or readiness card", guidance)
        self.assertIn("equal-height stacked panels", guidance)
        self.assertIn("top product bar plus a compact summary or snapshot lane", guidance)

    def test_workspace_shell_polish_guidance_rejects_generic_lane_labels(self):
        guidance = build_componentized_shell_polish_guidance("editor")

        self.assertIn("real topbar or command bar", guidance)
        self.assertIn("`Workspace`, `Notes`, or `Inspector`", guidance)
        self.assertIn("both side rails visibly populated", guidance)

    def test_load_componentized_base_css_uses_builder_kit_for_builder_prompt(self):
        css = load_componentized_base_css(
            "editor",
            "Build an AI startup builder workspace with prompt layers, live preview, variant runs, launch blockers, and QA notes",
        )

        assert css is not None
        self.assertIn("IBM Plex Sans", css)
        self.assertIn("#00c896", css.lower())
        self.assertNotIn("Fraunces", css)

    def test_load_componentized_base_css_keeps_editorial_kit_for_regular_editor_prompt(self):
        css = load_componentized_base_css(
            "editor",
            "Build a collaborative product brief editor with comments, outline, and publish controls",
        )

        assert css is not None
        self.assertIn("Fraunces", css)

    def test_validate_componentized_contract_outputs_flags_missing_and_stubbed_files(self):
        files = [
            SimpleNamespace(path="package.json", content='{"name":"demo"}'),
            SimpleNamespace(path="index.html", content="<html><body></body></html>"),
            SimpleNamespace(path="src/main.tsx", content="import App from './App'\n"),
        ]

        report = validate_componentized_contract_outputs(files, ui_archetype="fintech")

        self.assertFalse(report["passed"])
        codes = {item["code"] for item in report["violations"]}
        self.assertIn("missing_file", codes)
        self.assertIn("too_short", codes)
        self.assertIn("no_doctype", codes)
        self.assertIn("no_root_mount", codes)

    def test_validate_componentized_contract_outputs_accepts_real_workspace_entry_files(self):
        files = [
            SimpleNamespace(
                path="package.json",
                content='{"name":"demo","private":true,"version":"0.0.0","scripts":{"dev":"vite","build":"vite build"},"dependencies":{"react":"^18.3.1"}}',
            ),
            SimpleNamespace(
                path="index.html",
                content="<!doctype html><html lang=\"en\"><head><meta charset=\"UTF-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" /><title>Demo</title></head><body><div id=\"root\"></div><script type=\"module\" src=\"/src/main.tsx\"></script></body></html>",
            ),
            SimpleNamespace(
                path="src/main.tsx",
                content=(
                    "import React from 'react';\n"
                    "import ReactDOM from 'react-dom/client';\n"
                    "import App from './App';\n"
                    "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n"
                ),
            ),
            SimpleNamespace(
                path="src/App.tsx",
                content=(
                    "export default function App() {\n"
                    "  return <main><section className=\"kpi-grid\" /><section className=\"chart-panel\" /><aside className=\"watchlist\" /></main>;\n"
                    "}\n"
                ),
            ),
        ]

        report = validate_componentized_contract_outputs(files, ui_archetype="fintech")

        self.assertTrue(report["passed"])
        self.assertEqual(report["violations"], [])

    def test_validate_componentized_contract_outputs_accepts_delegated_dense_dashboard_shell(self):
        files = [
            SimpleNamespace(
                path="package.json",
                content='{"name":"demo","private":true,"version":"0.0.0","scripts":{"dev":"vite","build":"vite build"},"dependencies":{"react":"^18.3.1"}}',
            ),
            SimpleNamespace(
                path="index.html",
                content="<!doctype html><html lang=\"en\"><head><meta charset=\"UTF-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" /><title>Demo</title></head><body><div id=\"root\"></div><script type=\"module\" src=\"/src/main.tsx\"></script></body></html>",
            ),
            SimpleNamespace(
                path="src/main.tsx",
                content=(
                    "import React from 'react';\n"
                    "import ReactDOM from 'react-dom/client';\n"
                    "import App from './App';\n"
                    "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n"
                ),
            ),
            SimpleNamespace(
                path="src/App.tsx",
                content=(
                    "import Dashboard from './pages/Dashboard';\n"
                    "export default function App() {\n"
                    "  return <Dashboard />;\n"
                    "}\n"
                ),
            ),
            SimpleNamespace(
                path="src/pages/Dashboard.tsx",
                content=(
                    "import KpiCards from '../components/KpiCards';\n"
                    "import HoldingsTable from '../components/HoldingsTable';\n"
                    "import ActivityFeed from '../components/ActivityFeed';\n"
                    "export default function Dashboard() {\n"
                    "  return <main><KpiCards /><section className=\"chart-panel\" /><HoldingsTable /><ActivityFeed /></main>;\n"
                    "}\n"
                ),
            ),
            SimpleNamespace(path="src/components/KpiCards.tsx", content="export default function KpiCards() { return <section>KPI</section>; }\n"),
            SimpleNamespace(path="src/components/HoldingsTable.tsx", content="export default function HoldingsTable() { return <section>Holdings Table</section>; }\n"),
            SimpleNamespace(path="src/components/ActivityFeed.tsx", content="export default function ActivityFeed() { return <aside>Activity Feed</aside>; }\n"),
        ]

        report = validate_componentized_contract_outputs(files, ui_archetype="dashboard")

        self.assertTrue(report["passed"])
        self.assertEqual(report["violations"], [])

    def test_collect_quality_issue_codes_uses_material_semantic_and_strong_file_weaknesses(self):
        issues = collect_quality_issue_codes(
            semantic_evaluation={
                "passed": True,
                "dimensions": {
                    "contextual_labeling": {
                        "score": 3,
                        "max": 10,
                        "issues": ["Charts lack comparison context."],
                    },
                    "metric_completeness": {
                        "score": 10,
                        "max": 10,
                        "issues": [],
                    },
                },
            },
            multi_file_evaluation={
                "weak_files": [],
                "strong_files": [
                    {
                        "path": "src/components/CandlestickChart.tsx",
                        "role": "chart",
                        "score": 75,
                        "weakness_codes": ["numeric_authenticity"],
                    }
                ],
            },
        )

        self.assertIn("contextual_labeling", issues)
        self.assertIn("numeric_authenticity", issues)

    def test_collect_existing_code_context_serializes_workspace_files(self):
        code_dir = _case_dir("componentized-runtime-context")
        try:
            (code_dir / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")
            (code_dir / "src").mkdir()
            (code_dir / "src" / "App.tsx").write_text("export default function App() { return null; }\n", encoding="utf-8")
            (code_dir / "node_modules").mkdir()
            (code_dir / "node_modules" / "ignored.js").write_text("ignored\n", encoding="utf-8")

            context = collect_existing_code_context(code_dir)

            self.assertIsNotNone(context)
            self.assertIn("--- FILE: package.json ---", context)
            self.assertIn("--- FILE: src/App.tsx ---", context)
            self.assertNotIn("ignored.js", context)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_infer_scaffold_mode_prefers_plan_then_workspace_shape(self):
        code_dir = _case_dir("componentized-runtime-infer")
        try:
            (code_dir / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")

            plan_data = {
                "milestones": [
                    {
                        "tasks": [
                            {
                                "execution_hint": "engineer",
                                "scaffold_mode": "legacy_single_page",
                            }
                        ]
                    }
                ]
            }

            self.assertEqual(infer_scaffold_mode(code_dir, plan_data=plan_data), "legacy_single_page")
            self.assertEqual(infer_scaffold_mode(code_dir), "componentized_app")
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_rewrite_preview_file_references_handles_dist_and_published_mounts(self):
        html = (
            '<link rel="stylesheet" href="/assets/index-abc.css">'
            '<script type="module" src="/assets/index-abc.js"></script>'
            '<img src="generated-assets/hero.png">'
        )

        preview_html = rewrite_preview_file_references(
            html,
            mount_prefix="/api/preview-files/7/3",
            root_dir="dist",
        )
        published_html = rewrite_preview_file_references(
            html,
            mount_prefix="/published/demo-app",
            root_dir="",
        )

        self.assertIn('/api/preview-files/7/3/dist/assets/index-abc.css', preview_html)
        self.assertIn('/api/preview-files/7/3/dist/assets/index-abc.js', preview_html)
        self.assertIn('/api/preview-files/7/3/dist/generated-assets/hero.png', preview_html)
        self.assertIn('/published/demo-app/assets/index-abc.css', published_html)
        self.assertIn('/published/demo-app/assets/index-abc.js', published_html)
        self.assertIn('/published/demo-app/generated-assets/hero.png', published_html)

    def test_rewrite_preview_file_references_keeps_existing_published_css_urls(self):
        html = (
            "<style>"
            "body { background-image: url('/published/demo-app/assets/hero_background.png'); }"
            "</style>"
        )

        published_html = rewrite_preview_file_references(
            html,
            mount_prefix="/published/demo-app",
            root_dir="src",
        )

        self.assertIn("/published/demo-app/assets/hero_background.png", published_html)
        self.assertNotIn("/published/demo-app/src/published/demo-app/assets/hero_background.png", published_html)

    def test_rewrite_preview_runtime_asset_references_rewrites_bundle_literals(self):
        bundle = (
            'const hero="generated-assets/hero.png";'
            'const map="/generated-assets/world_map.png";'
            'const css=\'url(generated-assets/hero.png)\';'
        )

        rewritten = rewrite_preview_runtime_asset_references(
            bundle,
            mount_prefix="/api/preview-files/7/3",
            root_dir="dist",
        )

        self.assertIn('/api/preview-files/7/3/dist/generated-assets/hero.png', rewritten)
        self.assertIn('/api/preview-files/7/3/dist/generated-assets/world_map.png', rewritten)

    def test_build_componentized_preview_skips_without_package_json(self):
        code_dir = _case_dir("componentized-runtime-build")
        try:
            result = build_componentized_preview(code_dir)
            self.assertEqual(result["status"], "skipped")
            self.assertIsNone(result["dist_index"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_build_componentized_preview_reinstalls_missing_safe_dependency_after_build_failure(self):
        code_dir = _case_dir("componentized-runtime-missing-safe-dependency")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "node_modules").mkdir(parents=True)
            (code_dir / "dist").mkdir(parents=True)
            (code_dir / "package.json").write_text(
                '{\n  "name": "demo-app",\n  "dependencies": {\n    "react": "^18.2.0",\n    "react-feather": "^2.0.10"\n  }\n}\n',
                encoding="utf-8",
            )
            (code_dir / "dist" / "index.html").write_text("<!doctype html>\n", encoding="utf-8")

            calls: list[list[str]] = []
            responses = [
                subprocess.CompletedProcess(
                    args=["npm.cmd", "run", "build"],
                    returncode=1,
                    stdout="",
                    stderr='[vite]: Rollup failed to resolve import "react-feather" from "src/components/Sidebar.tsx".',
                ),
                subprocess.CompletedProcess(
                    args=["npm.cmd", "install"],
                    returncode=0,
                    stdout="installed",
                    stderr="",
                ),
                subprocess.CompletedProcess(
                    args=["npm.cmd", "run", "build"],
                    returncode=0,
                    stdout="built",
                    stderr="",
                ),
            ]

            def _fake_run(command, **kwargs):
                calls.append(command)
                return responses[len(calls) - 1]

            with patch("utils.componentized_runtime.subprocess.run", side_effect=_fake_run):
                result = build_componentized_preview(code_dir, timeout_seconds=30)

            self.assertEqual(result["status"], "success")
            self.assertEqual(
                calls,
                [
                    ["npm.cmd", "run", "build"],
                    ["npm.cmd", "install"],
                    ["npm.cmd", "run", "build"],
                ],
            )
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_backfills_missing_entry_files(self):
        code_dir = _case_dir("componentized-runtime-entry-fallback")
        try:
            ensure_componentized_workspace_support(code_dir)

            self.assertTrue((code_dir / "index.html").exists())
            self.assertTrue((code_dir / "src" / "main.tsx").exists())
            self.assertTrue((code_dir / "src" / "App.tsx").exists())
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_rewrite_componentized_asset_api_urls_maps_backend_assets_to_public_assets(self):
        source = (
            '<img src="/api/assets/77/2/hero_background.png">'
            "background-image:url('/api/assets/77/2/world_map.png')"
        )

        rewritten = rewrite_componentized_asset_api_urls(source)

        self.assertIn('generated-assets/hero_background.png', rewritten)
        self.assertIn('generated-assets/world_map.png', rewritten)
        self.assertNotIn('/api/assets/77/2/', rewritten)

    def test_extract_visual_dna_collects_tokens_from_workspace(self):
        code_dir = _case_dir("componentized-runtime-visual-dna")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() { return <main className=\"shell\">Hello</main>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "index.css").write_text(
                "@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&display=swap');\n"
                ":root { --accent: #d4a574; --card-radius: 24px; }\n"
                ".shell { font-family: 'Playfair Display', serif; border-radius: 24px; box-shadow: 0 16px 48px rgba(0,0,0,0.5); }\n"
                "@keyframes glowPulse { from { opacity: 0.5; } to { opacity: 1; } }\n",
                encoding="utf-8",
            )

            visual_dna = extract_visual_dna(code_dir)

            self.assertIn("https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&display=swap", visual_dna["google_font_imports"])
            self.assertEqual(visual_dna["css_variables"]["--accent"], "#d4a574")
            self.assertIn("#d4a574", visual_dna["hex_colors"])
            self.assertIn("glowPulse", visual_dna["keyframes"])
            self.assertIn("24px", visual_dna["radius_values"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_extract_feature_inventory_detects_interactions_and_breakpoints(self):
        code_dir = _case_dir("componentized-runtime-feature-inventory")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  const handleClick = () => {};\n"
                "  const addToCart = () => {};\n"
                "  return (\n"
                "    <div>\n"
                "      <button onClick={handleClick}>Open modal</button>\n"
                "      <button onClick={addToCart}>Add to cart</button>\n"
                "      <button onClick={() => {}}>Wishlist</button>\n"
                "      <input onChange={() => {}} aria-label=\"Search\" />\n"
                "    </div>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "index.css").write_text(
                "@media (max-width: 768px) { .shell { padding: 16px; } }\n"
                "::-webkit-scrollbar { width: 10px; }\n"
                "::selection { background: #d4a574; }\n",
                encoding="utf-8",
            )

            inventory = extract_feature_inventory(code_dir)

            self.assertIn("click", inventory["event_handlers"])
            self.assertIn("change", inventory["event_handlers"])
            self.assertIn("cart", inventory["detected_features"])
            self.assertIn("wishlist", inventory["detected_features"])
            self.assertIn("search", inventory["detected_features"])
            self.assertIn("768px", inventory["responsive_breakpoints"])
            self.assertIn("custom_scrollbar", inventory["polish_features"])
            self.assertIn("selection_styling", inventory["polish_features"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_collect_componentized_reverse_dependents_finds_parent_chain(self):
        code_dir = _case_dir("componentized-runtime-reverse-dependents")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "pages").mkdir(parents=True)
            (code_dir / "src" / "data").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import Dashboard from './pages/Dashboard';\n"
                "export default function App() { return <Dashboard />; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "pages" / "Dashboard.tsx").write_text(
                "import Watchlist from '../components/Watchlist';\n"
                "import { watchlist } from '../data/watchlist';\n"
                "export default function Dashboard() { return <Watchlist items={watchlist} />; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "Watchlist.tsx").write_text(
                "export default function Watchlist({ items }: { items: { symbol: string }[] }) { return <div>{items.length}</div>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "data" / "watchlist.ts").write_text(
                "export const watchlist = [{ symbol: 'AAPL' }];\n",
                encoding="utf-8",
            )

            dependents = collect_componentized_reverse_dependents(
                code_dir,
                ["src/components/Watchlist.tsx"],
                max_depth=2,
            )

            self.assertIn("src/pages/Dashboard.tsx", dependents)
            self.assertIn("src/App.tsx", dependents)
            self.assertNotIn("src/data/watchlist.ts", dependents)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_adds_missing_support_and_rewrites_asset_urls(self):
        code_dir = _case_dir("componentized-runtime-support")
        try:
            (code_dir / "package.json").write_text(
                '{\n'
                '  "name": "demo-app",\n'
                '  "scripts": {\n'
                '    "build": "tsc -b && vite build"\n'
                "  }\n"
                '}\n',
                encoding="utf-8",
            )
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                'import React from "react";\n'
                'import ReactDOM from "react-dom/client";\n'
                'import App from "./App.tsx";\n'
                'import "../base.css";\n',
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                'import "./base.css";\n'
                'export default function App() { return <img src="/api/assets/9/1/hero.png" />; }\n',
                encoding="utf-8",
            )
            (code_dir / "src" / "index.css").write_text(
                ":root { font-family: system-ui; }\nbody { margin: 0; }\n.page { padding: 24px; }\n.card { margin-top: 16px; }\n.hero{background-image:url('/api/assets/9/1/bg.png');}\n",
                encoding="utf-8",
            )

            result = ensure_componentized_workspace_support(
                code_dir,
                base_css_content=":root { --accent: #10b981; }\n",
            )

            self.assertTrue((code_dir / "tsconfig.json").exists())
            self.assertTrue((code_dir / "tsconfig.node.json").exists())
            self.assertTrue((code_dir / "vite.config.ts").exists())
            self.assertTrue((code_dir / "src" / "vite-env.d.ts").exists())
            self.assertTrue((code_dir / "public" / "vite.svg").exists())
            self.assertTrue((code_dir / "src" / "base.css").exists())
            main_source = (code_dir / "src" / "main.tsx").read_text(encoding="utf-8")
            self.assertIn('import "./base.css";', main_source)
            self.assertIn('import App from "./App";', main_source)
            self.assertNotIn("../base.css", main_source)
            if 'import "./index.css";' in main_source:
                self.assertGreater(main_source.index('import "./base.css";'), main_source.index('import "./index.css";'))
            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn('generated-assets/hero.png', app_source)
            self.assertNotIn('base.css', app_source)
            index_css = (code_dir / "src" / "index.css").read_text(encoding="utf-8")
            self.assertNotIn("font-family: system-ui", index_css)
            self.assertIn("intentionally minimal", index_css)
            self.assertIn('"build": "vite build"', (code_dir / "package.json").read_text(encoding="utf-8"))
            self.assertIn('"noUnusedLocals": false', (code_dir / "tsconfig.json").read_text(encoding="utf-8"))
            self.assertIn("tsconfig.json", result["created_files"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_run_on_inline_comments(self):
        code_dir = _case_dir("componentized-runtime-inline-comments")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';import ReactDOM from 'react-dom/client';import App from './App';ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "import './index.css'; // keep overridesuseEffect(() => {}); // keep effectexport default function App() { return <div>Hello</div>; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* keep overrides */", app_source)
            self.assertIn("/* keep effect */", app_source)
            self.assertIn("useEffect(() => {})", app_source)
            self.assertIn("export default function App()", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_tsconfig_leading_comma_noise(self):
        code_dir = _case_dir("componentized-runtime-tsconfig-leading-comma")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() { return <div>Portfolio</div>; }\n",
                encoding="utf-8",
            )
            (code_dir / "tsconfig.json").write_text(
                "{\n"
                '  "compilerOptions": {\n'
                '    "target": "ES2020",\n'
                ',    "isolatedModules": true,\n'
                '    "jsx": "react-jsx"\n'
                "  }\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            tsconfig_source = (code_dir / "tsconfig.json").read_text(encoding="utf-8")
            self.assertIn('"isolatedModules": true', tsconfig_source)
            self.assertNotIn('\n,    "isolatedModules"', tsconfig_source)
            self.assertIn('"noUnusedLocals": false', tsconfig_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_multiline_run_on_comments(self):
        code_dir = _case_dir("componentized-runtime-multiline-inline-comments")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React, { useState } from 'react';\n"
                "export default function App() {\n"
                "  const [activeRange, setActiveRange] = useState('1M');\n"
                "  // Mock data for price action  const chartData = [\n"
                "    { x: 0, y: 150 },\n"
                "  ];\n"
                "  return <button onClick={() => setActiveRange('1Y')}>{activeRange}{chartData.length}</button>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* Mock data for price action */", app_source)
            self.assertIn("const chartData = [", app_source)
            self.assertNotIn("// Mock data for price action  const chartData", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_interface_comment_bleed_and_split_identifiers(self):
        code_dir = _case_dir("componentized-runtime-interface-comment-bleed")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "interface KPIData { label: string; dataCount?: number; /* For count-up animation} */\n"
                "interface AssetData { value: number;}interface WatchlistItem { id: string; }\n"
                "export default function App() {\n"
                "  /* Update assets table      set */\n"
                "Assets((prev) => prev);\n"
                "  return <div />;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("dataCount?: number; /* For count-up animation */", app_source)
            self.assertIn("}\ninterface AssetData", app_source)
            self.assertIn("}\ninterface WatchlistItem", app_source)
            self.assertIn("/* Update assets table */\nsetAssets((prev) => prev);", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_comments_bare_section_labels(self):
        code_dir = _case_dir("componentized-runtime-bare-section-labels")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React from 'react';\n"
                "Icons (simplified for inline SVG)\n"
                "const SearchIcon = () => <svg />;\n"
                "export default function App() { return <SearchIcon />; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* Icons (simplified for inline SVG) */", app_source)
            self.assertNotIn("\nIcons (simplified for inline SVG)\n", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_comments_bare_section_labels_before_comment_blocks(self):
        code_dir = _case_dir("componentized-runtime-bare-section-labels-before-comments")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React from 'react';\n"
                "const CandlestickChart: React.FC = () => {\n"
                "Component (static for now)\n"
                "  /* Data for 12 candlesticks */\n"
                "  const data = [{ o: 50, c: 55 }];\n"
                "  return <div>{data.length}</div>;\n"
                "};\n"
                "export default function App() { return <CandlestickChart />; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* Component (static for now) */", app_source)
            self.assertIn("/* Data for 12 candlesticks */", app_source)
            self.assertIn("const data = [{ o: 50, c: 55 }];", app_source)
            self.assertNotIn("\nComponent (static for now)\n", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_comments_run_on_explanatory_labels(self):
        code_dir = _case_dir("componentized-runtime-run-on-explanatory-labels")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React from 'react';\n"
                "export default function App() {\n"
                "  const chartHeight = 250;\n"
                "  const yMax = 100;\n"
                "  const yMin = 0; /* Min value for scaling */\n"
                "SVG (SVG Y-axis is inverted)  const scaleY = (value: number) => chartHeight - ((value - yMin) / (yMax - yMin)) * chartHeight;\n"
                "  return <div>{scaleY(50)}</div>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* SVG (SVG Y-axis is inverted) */", app_source)
            self.assertIn("const scaleY = (value: number) =>", app_source)
            self.assertNotIn("\nSVG (SVG Y-axis is inverted)  const scaleY", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_hoists_chart_helpers_outside_map_callbacks(self):
        code_dir = _case_dir("componentized-runtime-chart-helper-scope")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  const data = [{ high: 120, low: 90, open: 100, close: 110 }];\n"
                "  return (\n"
                "    <svg>\n"
                "      {data.map((candle, index) => {\n"
                "        const xPos = index * 10;\n"
                "        const scaleY = (value: number) => 300 - value;\n"
                "        return <line key={index} x1={xPos} y1={scaleY(candle.high)} x2={xPos} y2={scaleY(candle.low)} />;\n"
                "      })}\n"
                "      {[90, 120].map((value) => <text key={value} y={scaleY(value)}>{value}</text>)}\n"
                "    </svg>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertEqual(app_source.count("const scaleY = (value: number) => 300 - value;"), 1)
            self.assertLess(app_source.index("const scaleY = (value: number) => 300 - value;"), app_source.index("return ("))
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_unterminated_block_comment_line_notes(self):
        code_dir = _case_dir("componentized-runtime-unterminated-block-comment-line-note")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            chart_path = code_dir / "src" / "components" / "ChartContainer.tsx"
            chart_path.write_text(
                "import React, { useEffect } from 'react';\n"
                "const ChartContainer: React.FC = () => {\n"
                "  useEffect(() => {    /* This effect is mostly for demonstration;    // actual chart interaction would involve a charting library.    console.log('range');  }, []);\n"
                "  return <section className=\"chart-card\">ready</section>;\n"
                "};\n"
                "export default ChartContainer;\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            chart_source = chart_path.read_text(encoding="utf-8")
            self.assertIn(
                "/* This effect is mostly for demonstration; actual chart interaction would involve a charting library. */",
                chart_source,
            )
            self.assertIn("console.log('range');  }, []);", chart_source)
            self.assertNotIn("/* This effect is mostly for demonstration;    //", chart_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_control_flow_comment_bleed(self):
        code_dir = _case_dir("componentized-runtime-control-flow-comment-bleed")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React from 'react';\n"
                "export default function App() {\n"
                "  const current = 10;\n"
                "  const next = 12;\n"
                "  const isPositive = next >= current; /* Compare new price to old price if (next !== current) { */\n"
                "  return <div>{isPositive ? 'up' : 'down'}</div>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* Compare new price to old price */", app_source)
            self.assertIn("if (next !== current) {", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_preserves_closing_brace_after_run_on_label(self):
        code_dir = _case_dir("componentized-runtime-run-on-label-brace")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  if (true) {\n"
                "class after 500ms          }          return <div />;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* class after 500ms */", app_source)
            self.assertIn("}\nreturn <div />;", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_comment_bleed_inside_jsx(self):
        code_dir = _case_dir("componentized-runtime-jsx-comment-bleed")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React from 'react';/* --- Icon SVGs --- */\n"
                "const HomeIcon = () => (<svg xmlns=\"http:/* www.w3.org/2000/svg\"><path d=\"M1 1\" /></svg>); */\n"
                "const Header = () => { return <img src=\"https:/* www.gravatar.com/avatar/demo?s=32\" alt=\"avatar\" />; }; */\n"
                "export default function App() { return <main><HomeIcon /><Header /></main>; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn('xmlns="http://www.w3.org/2000/svg"', app_source)
            self.assertIn('src="https://www.gravatar.com/avatar/demo?s=32"', app_source)
            self.assertNotIn("http:/*", app_source)
            self.assertNotIn("https:/*", app_source)
            self.assertNotIn("); */", app_source)
            self.assertNotIn("}; */", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_normalizes_jsx_code_template_literals(self):
        code_dir = _case_dir("componentized-runtime-jsx-code-template-literal")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <code>\n"
                "{`function applyFormatting(text, format) {\n"
                "  console.log(`Applying ${format} to: ${text}`);\n"
                "  return `<span class=\"${format}\">${text}</span>`;\n"
                "}`}\n"
                "    </code>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn('function applyFormatting(text, format)', app_source)
            self.assertIn('console.log(`Applying $&#123;format&#125; to: $&#123;text&#125;`);', app_source)
            self.assertIn('return `&lt;span class=\\"$&#123;format&#125;\\"&gt;$&#123;text&#125;&lt;/span&gt;`;', app_source)
            self.assertNotIn("{`function applyFormatting", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_jsx_text_comment_close_bleed(self):
        code_dir = _case_dir("componentized-runtime-jsx-text-comment-close")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "Layout.tsx").write_text(
                "import React from 'react';\n"
                "interface LayoutProps { children: React.ReactNode; }\n"
                "export default function Layout({ children }: LayoutProps) {\n"
                "  return (\n"
                "    <aside className=\"sidebar-user\">\n"
                "      <span className=\"user-name\">Jane */\n"
                "Doe</span>\n"
                "      <div>{children}</div>\n"
                "    </aside>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            layout_source = (code_dir / "src" / "components" / "Layout.tsx").read_text(encoding="utf-8")
            self.assertIn('<span className="user-name">Jane Doe</span>', layout_source)
            self.assertNotIn("Jane */", layout_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_jsx_text_comment_close_bleed_before_next_line_closing_tag(self):
        code_dir = _case_dir("componentized-runtime-jsx-text-comment-close-next-line")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <button>\n"
                "      <svg></svg> Export */\n"
                "      CSV\n"
                "    </button>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("Export CSV", app_source)
            self.assertNotIn("Export */", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_self_closes_void_jsx_elements(self):
        code_dir = _case_dir("componentized-runtime-void-jsx-elements")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <section><img src=\"/avatar.png\" alt=\"Avatar\"><input aria-label=\"Search\"></section>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn('<img src="/avatar.png" alt="Avatar" />', app_source)
            self.assertIn('<input aria-label="Search" />', app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_guards_invalid_currency_formatting(self):
        code_dir = _case_dir("componentized-runtime-currency-guard")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "utils").mkdir(parents=True)
            (code_dir / "src" / "utils" / "helpers.ts").write_text(
                "export const formatCurrency = (value: number, currency: string = 'USD'): string => {\n"
                "  return new Intl.NumberFormat('en-US', {\n"
                "    style: 'currency',\n"
                "    currency: currency,\n"
                "    minimumFractionDigits: 2,\n"
                "    maximumFractionDigits: 2,\n"
                "  }).format(value);\n"
                "};\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "import { formatCurrency } from './utils/helpers';\n"
                "export default function App() {\n"
                "  return <div>{formatCurrency(30000, '')}</div>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            helper_source = (code_dir / "src" / "utils" / "helpers.ts").read_text(encoding="utf-8")
            self.assertIn("formatCurrency(30000)", app_source)
            self.assertNotIn("formatCurrency(30000, '')", app_source)
            self.assertIn("currency.toUpperCase()", helper_source)
            self.assertIn("'USD'", helper_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_preserves_base_kit_typography(self):
        code_dir = _case_dir("componentized-runtime-typography-guard")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "import './style.css';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <main><h1>Desk</h1><div className=\"kpi-value\">$123,456.78</div></main>;\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "style.css").write_text(
                ":root { --font-display: 'Inter', sans-serif; }\n"
                "h1, h2, h3 { font-family: 'Inter', sans-serif; }\n"
                ".kpi-value { font-family: 'Roboto Mono', monospace; }\n"
                ".font-mono { font-family: 'Fira Code', monospace; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(
                code_dir,
                base_css_content=(
                    "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&family=Space+Grotesk:wght@700&display=swap');\n"
                    "body { font-family: 'Inter', sans-serif; }\n"
                    ".page-title { font-family: 'Space Grotesk', sans-serif; }\n"
                    ".kpi-value { font-family: 'JetBrains Mono', monospace; }\n"
                ),
            )

            style_source = (code_dir / "src" / "style.css").read_text(encoding="utf-8")
            base_source = (code_dir / "src" / "base.css").read_text(encoding="utf-8")
            self.assertIn("'Space Grotesk', 'Inter', sans-serif", style_source)
            self.assertNotIn("Roboto Mono", style_source)
            self.assertNotIn("Fira Code", style_source)
            self.assertIn("JetBrains Mono", style_source)
            self.assertIn("Space+Grotesk", base_source)
            self.assertIn("JetBrains Mono", base_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_adds_polish_guard_for_fintech(self):
        code_dir = _case_dir("componentized-runtime-polish-guard-fintech")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "import './style.css';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <div className=\"fintech-shell\"><div className=\"topbar-brand\">Desk</div><div className=\"kpi-value\">$123,456.78</div></div>;\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "style.css").write_text(".fintech-shell { color: white; }\n", encoding="utf-8")

            ensure_componentized_workspace_support(code_dir, ui_archetype="fintech")

            main_source = (code_dir / "src" / "main.tsx").read_text(encoding="utf-8")
            polish_guard = (code_dir / "src" / "polish-guard.css").read_text(encoding="utf-8")
            polish_runtime = (code_dir / "src" / "polish-guard.ts").read_text(encoding="utf-8")
            self.assertIn('import "./polish-guard";', main_source)
            self.assertIn('import "./polish-guard.css";', main_source)
            self.assertGreater(
                main_source.index('import "./polish-guard.css";'),
                main_source.index('import "./style.css";'),
            )
            self.assertIn(".topbar-brand", polish_guard)
            self.assertIn(".h3", polish_guard)
            self.assertIn(".kpi-value", polish_guard)
            self.assertIn(".text-mono", polish_guard)
            self.assertIn(".guard-news-lead", polish_guard)
            self.assertIn(".guard-accent-action", polish_guard)
            self.assertIn(".guard-fixed-sidebar-shell", polish_guard)
            self.assertIn(".guard-direct-rail-shell", polish_guard)
            self.assertIn(".guard-nested-rail-shell", polish_guard)
            self.assertIn(".guard-main-rail-split", polish_guard)
            self.assertIn(".guard-main-rail-secondary", polish_guard)
            self.assertIn(".watchlist-card", polish_guard)
            self.assertIn(".watchlist-feed-panel", polish_guard)
            self.assertIn(".news-feed-item", polish_guard)
            self.assertIn(".activity-item .activity-time", polish_guard)
            self.assertIn(".activity-feed .feed-header", polish_guard)
            self.assertIn(".data-table-wrapper", polish_guard)
            self.assertIn(".asset-table td,\n.data-table td,\n.table-cell", polish_guard)
            self.assertIn(".left-sidebar", polish_guard)
            self.assertIn(".main-content-wrapper", polish_guard)
            self.assertIn(".kpi-card:nth-child(4n + 1)", polish_guard)
            self.assertIn(".activity-feed::after", polish_guard)
            self.assertIn("button:focus-visible", polish_guard)
            self.assertIn("--guard-sidebar-offset", polish_guard)
            self.assertIn("Runtime shell polish guard for fintech", polish_guard)
            self.assertIn("requestAnimationFrame", polish_runtime)
            self.assertIn(".kpi-value", polish_runtime)
            self.assertIn(".text-mono", polish_runtime)
            self.assertIn("MONO_SELECTORS", polish_runtime)
            self.assertIn('const COUNT_SELECTORS = [\n  "[data-countup]"\n] as const;', polish_runtime)
            self.assertIn("guard-mono-count", polish_runtime)
            self.assertIn("applyNewsHierarchyGuard", polish_runtime)
            self.assertIn("applyActionGuard", polish_runtime)
            self.assertIn("applyShellLayoutGuard", polish_runtime)
            self.assertIn("applyDirectRailGuard", polish_runtime)
            self.assertIn("applyNestedRailGuard", polish_runtime)
            self.assertIn("resetNestedRailGuard", polish_runtime)
            self.assertIn("SHELL_RIGHT_RAIL_SELECTOR", polish_runtime)
            self.assertIn('".app-shell"', polish_runtime)
            self.assertIn(".main-content-wrapper", polish_runtime)
            self.assertIn(".left-sidebar", polish_runtime)
            self.assertIn("schedulePolishGuard", polish_runtime)
            self.assertIn("window.addEventListener('resize', schedulePolishGuard);", polish_runtime)
            self.assertIn("guard-fixed-sidebar-shell", polish_runtime)
            self.assertIn("guard-direct-rail-shell", polish_runtime)
            self.assertIn("guard-main-rail-secondary", polish_runtime)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_adds_runtime_guard_even_when_css_guard_exists(self):
        code_dir = _case_dir("componentized-runtime-polish-guard-existing-css")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                'import "./polish-guard.css";\n'
                "import './style.css';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <div className=\"fintech-shell\"><div className=\"kpi-value\">$123,456.78</div></div>;\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "style.css").write_text(".fintech-shell { color: white; }\n", encoding="utf-8")
            (code_dir / "src" / "polish-guard.css").write_text("/* existing css */\n", encoding="utf-8")

            ensure_componentized_workspace_support(code_dir, ui_archetype="fintech")

            main_source = (code_dir / "src" / "main.tsx").read_text(encoding="utf-8")
            self.assertIn('import "./polish-guard";', main_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_adds_dashboard_specific_polish_guard_tuning(self):
        code_dir = _case_dir("componentized-runtime-polish-guard-dashboard")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <div className=\"dashboard-layout\"><div className=\"kpi-card\" /><table className=\"data-table\"><thead><tr><th>Price</th></tr></thead></table><span className=\"cell-action\">View</span><div className=\"activity-item\"><span className=\"activity-time\">2 min ago</span></div></div>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir, ui_archetype="dashboard")

            polish_guard = (code_dir / "src" / "polish-guard.css").read_text(encoding="utf-8")
            self.assertIn(".dashboard-layout .kpi-card", polish_guard)
            self.assertIn(".dashboard-layout .data-table thead th", polish_guard)
            self.assertIn(".dashboard-layout .cell-action", polish_guard)
            self.assertIn(".dashboard-layout .activity-item .activity-time", polish_guard)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_skips_polish_guard_for_non_app_density_archetypes(self):
        code_dir = _case_dir("componentized-runtime-polish-guard-skip")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "import './style.css';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() { return <div>Hello</div>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "style.css").write_text(".app { color: red; }\n", encoding="utf-8")

            ensure_componentized_workspace_support(code_dir, ui_archetype="portfolio")

            main_source = (code_dir / "src" / "main.tsx").read_text(encoding="utf-8")
            self.assertNotIn('import "./polish-guard";', main_source)
            self.assertNotIn('import "./polish-guard.css";', main_source)
            self.assertFalse((code_dir / "src" / "polish-guard.css").exists())
            self.assertFalse((code_dir / "src" / "polish-guard.ts").exists())
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_bare_react_fragment_closer(self):
        code_dir = _case_dir("componentized-runtime-react-fragment-closer")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React from 'react';\n"
                "export default function App() {\n"
                "  return (\n"
                "    <table>\n"
                "      <tbody>\n"
                "        {[1].map((item) => (\n"
                "          <React.Fragment key={item}>\n"
                "            <tr><td>{item}</td></tr>\n"
                "          </React>\n"
                "        ))}\n"
                "      </tbody>\n"
                "    </table>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir, ui_archetype="dashboard")

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("</React.Fragment>", app_source)
            self.assertNotIn("</React>\n", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_normalizes_one_line_main_entry_imports(self):
        code_dir = _case_dir("componentized-runtime-main-entry")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';import ReactDOM from 'react-dom/client';import App from './App.tsx';import '../base.css'; // Design system base stylesimport './style.css'; // App-specific stylesReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() { return <div>Hello</div>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "style.css").write_text(".app { color: red; }\n", encoding="utf-8")

            ensure_componentized_workspace_support(code_dir, base_css_content=":root { --accent: #10b981; }\n")

            main_source = (code_dir / "src" / "main.tsx").read_text(encoding="utf-8")
            self.assertIn("import App from './App';", main_source)
            self.assertIn('import "./base.css";', main_source)
            self.assertIn('import "./style.css";', main_source)
            self.assertEqual(main_source.count('base.css'), 1)
            self.assertGreater(main_source.index('import "./base.css";'), main_source.index('import "./style.css";'))
            self.assertNotIn("../base.css", main_source)
            self.assertNotIn("./App.tsx", main_source)
            self.assertIn("ReactDOM.createRoot", main_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_adds_safe_runtime_dependencies(self):
        code_dir = _case_dir("componentized-runtime-safe-deps")
        try:
            (code_dir / "package.json").write_text(
                '{\n'
                '  "name": "demo-app",\n'
                '  "dependencies": {\n'
                '    "react": "^18.2.0",\n'
                '    "react-dom": "^18.2.0"\n'
                "  }\n"
                '}\n',
                encoding="utf-8",
            )
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "import { Bell } from 'lucide-react';\n"
                "export default function App() { return <Bell />; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            package_json = (code_dir / "package.json").read_text(encoding="utf-8")
            self.assertIn('"lucide-react": "^0.564.0"', package_json)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_syncs_heroicons_dependency(self):
        code_dir = _case_dir("componentized-runtime-safe-heroicons")
        try:
            (code_dir / "package.json").write_text(
                '{\n'
                '  "name": "demo-app",\n'
                '  "dependencies": {\n'
                '    "react": "^18.2.0",\n'
                '    "react-dom": "^18.2.0"\n'
                "  }\n"
                '}\n',
                encoding="utf-8",
            )
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "import { BellIcon } from '@heroicons/react/24/solid';\n"
                "export default function App() { return <BellIcon />; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            package_json = (code_dir / "package.json").read_text(encoding="utf-8")
            self.assertIn('"@heroicons/react": "^2.2.0"', package_json)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_literal_escape_noise_in_package_json(self):
        code_dir = _case_dir("componentized-runtime-package-json-escape-noise")
        try:
            (code_dir / "package.json").write_text(
                '{\n'
                '  "name": "demo-app",\n'
                '  "private": true,\n'
                '  "version": "0.0.0",\\n  "type": "module",\n'
                '  "scripts": {\n'
                '    "build": "tsc -b && vite build"\n'
                "  }\n"
                '}\n',
                encoding="utf-8",
            )
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() { return <div>Hello</div>; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            package_json = (code_dir / "package.json").read_text(encoding="utf-8")
            self.assertIn('"type": "module"', package_json)
            self.assertNotIn("\\n", package_json)
            self.assertIn('"build": "vite build"', package_json)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_strips_sass_extend_from_plain_css(self):
        code_dir = _case_dir("componentized-runtime-strip-extend")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "index.css").write_text(
                ".panel-title {\n"
                "  font-size: 24px;\n"
                "}\n"
                "\n"
                ".kpi-label {\n"
                "  @extend .label-style;\n"
                "  margin-bottom: 8px;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            index_css = (code_dir / "src" / "index.css").read_text(encoding="utf-8")
            self.assertNotIn("@extend", index_css)
            self.assertIn("margin-bottom: 8px;", index_css)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_normalizes_run_on_imports(self):
        code_dir = _case_dir("componentized-runtime-run-on-imports")
        try:
            (code_dir / "vite.config.ts").write_text(
                "import { defineConfig } from 'vite'import react from '@vitejs/plugin-react'export default defineConfig({ plugins: [react()] })\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            vite_config = (code_dir / "vite.config.ts").read_text(encoding="utf-8")
            self.assertIn("from 'vite'\nimport react", vite_config)
            self.assertIn("plugin-react'\nexport default", vite_config)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_jsx_handler_comment_close_bleed(self):
        code_dir = _case_dir("componentized-runtime-jsx-handler-comment-close")
        try:
            (code_dir / "src").mkdir(parents=True)
            source_path = code_dir / "src" / "About.tsx"
            source_path.write_text(
                "export default function About() {\n"
                "  return (\n"
                "    <img\n"
                "      src=\"https://images.unsplash.com/photo-12345?w=600&q=80\"\n"
                "      alt=\"Portrait\"\n"
                "      onError={(e) => { */\n"
                "const target = e.target as HTMLImageElement;\n"
                "        target.src = 'https://via.placeholder.com/600x800/111/eee?text=Fallback';\n"
                "      }}\n"
                "    />\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir, ui_archetype="portfolio")

            source = source_path.read_text(encoding="utf-8")
            self.assertNotIn("*/", source)
            self.assertNotIn("images.unsplash.com", source)
            self.assertNotIn("via.placeholder.com", source)
            self.assertIn("generated-assets/portrait.svg", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_rewrites_missing_component_alias_imports(self):
        code_dir = _case_dir("componentized-runtime-component-import-aliases")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import Hero from './components/Hero';\n"
                "import CharacterCards from './components/CharacterCards';\n"
                "import WeaponSection from './components/WeaponSection';\n"
                "export default function App() { return <><Hero /><CharacterCards /><WeaponSection /></>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "HeroSection.tsx").write_text(
                "export default function HeroSection() { return <section>Hero</section>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "CharacterSection.tsx").write_text(
                "export default function CharacterSection() { return <section>Characters</section>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "WeaponShowcase.tsx").write_text(
                "export default function WeaponShowcase() { return <section>Weapons</section>; }\n",
                encoding="utf-8",
            )
            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("from './components/HeroSection'", app_source)
            self.assertIn("from './components/CharacterSection'", app_source)
            self.assertIn("from './components/WeaponShowcase'", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_converts_dead_game_ctas_to_inline_details(self):
        code_dir = _case_dir("componentized-runtime-game-detail-ctas")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  const weapons = [{ name: 'Needler', type: 'Projectile', owner: 'Covenant', description: 'Crystal shards.', atk: 75, mag: 80 }];\n"
                "  const locations = [{ name: 'Reach', region: 'Colony', description: 'Frontier world.' }];\n"
                "  return <><div>{weapons.map((weapon) => (<div><button className=\"btn-primary weapon-cta\">Inspect Weapon</button></div>))}</div><div>{locations.map((loc) => (<div><button className=\"btn-primary\">ACCESS LOGS</button></div>))}</div></>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir, ui_archetype="game")

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("<details className=\"runtime-inline-detail\">", app_source)
            self.assertIn("{weapon.name || weapon.title || \"Field Brief\"}", app_source)
            self.assertIn("{loc.name || loc.title || \"Field Brief\"}", app_source)
            self.assertNotIn(">Inspect Weapon</button>", app_source)
            self.assertNotIn(">ACCESS LOGS</button>", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_converts_alert_game_ctas_to_inline_details(self):
        code_dir = _case_dir("componentized-runtime-game-alert-detail-ctas")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React, { useState } from 'react';\n"
                "interface LocationCardProps { region: string; name: string; description: string; }\n"
                "const LocationCard: React.FC<LocationCardProps> = ({ region, name, description }) => {\n"
                "  const [showDetails, setShowDetails] = useState(false);\n"
                "  const handleAccessLogs = () => {\n"
                "    setShowDetails(!showDetails);\n"
                "    if (!showDetails) {\n"
                "      alert(`Accessing logs for ${name}...`);\n"
                "    }\n"
                "  };\n"
                "  return <button onClick={handleAccessLogs} className=\"btn-primary\">ACCESS LOGS</button>;\n"
                "};\n"
                "export default function App() { return <LocationCard region=\"Halo Ring\" name=\"ALPHA HALO\" description=\"Forerunner site.\" />; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir, ui_archetype="game")

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("<details className=\"runtime-inline-detail\">", app_source)
            self.assertIn("<div className=\"runtime-inline-detail-kicker\">{region}</div>", app_source)
            self.assertIn("<h4 className=\"runtime-inline-detail-title\">{name}</h4>", app_source)
            self.assertNotIn("alert(`Accessing logs", app_source)
            self.assertNotIn("const [showDetails, setShowDetails]", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_removes_dead_alert_handler_references_from_game_cards(self):
        code_dir = _case_dir("componentized-runtime-game-alert-card-wrapper")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React from 'react';\n"
                "interface LocationCardProps { region: { type: string; name: string; description: string; image: string }; }\n"
                "const LocationCard: React.FC<LocationCardProps> = ({ region }) => {\n"
                "  const handleExploreClick = () => {\n"
                "    alert(`Exploring ${region.name}!`);\n"
                "  };\n"
                "  return (\n"
                "    <div className=\"location-card\" onClick={handleExploreClick} role=\"button\">\n"
                "      <button onClick={handleExploreClick} className=\"btn-primary\">Explore</button>\n"
                "    </div>\n"
                "  );\n"
                "};\n"
                "export default function App() { return <LocationCard region={{ type: 'Mainland', name: 'Kanto Region', description: 'Starter region.', image: '' }} />; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir, ui_archetype="game")

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertNotIn("handleExploreClick", app_source)
            self.assertNotIn("onClick={handleExploreClick}", app_source)
            self.assertIn('<div className="runtime-inline-detail-kicker">{region.type || region.region || region.owner || "Archive Detail"}</div>', app_source)
            self.assertIn('<h4 className="runtime-inline-detail-title">{region.name || region.title || "Field Brief"}</h4>', app_source)
            self.assertIn('<p className="runtime-inline-detail-copy">{region.description || region.desc || region.lore || "This dossier uses local mock archive data to keep the interaction alive."}</p>', app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_replaces_game_map_placeholder_image(self):
        code_dir = _case_dir("componentized-runtime-game-map-placeholder")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <div className=\"world-map-image\"><img src=\"data:image/svg+xml,%3Csvg%3EImage Placeholder%3C/svg%3E\" alt=\"Map\" /></div>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir, ui_archetype="game")

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("runtime-world-map-fallback", app_source)
            self.assertIn("World Survey Interface", app_source)
            self.assertNotIn("Image Placeholder", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_block_comment_code_bleed(self):
        code_dir = _case_dir("componentized-runtime-comment-bleed")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import { useEffect } from 'react';function App() { useEffect(() => { const next = { price: 10, /* +/- 0.5%        delta: ( */\n"
                "Math.random() * 2 - 1) * 0.5 }; const watch = { symbol: 'AAPL', /* Initial delta from asset table          positive: asset */\n"
                "ToAdd.positive }; return () => {}; }, []); return <div />; }export default App;\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* +/- 0.5% */", app_source)
            self.assertIn("delta: (Math.random() * 2 - 1) * 0.5", app_source)
            self.assertIn("/* Initial delta from asset table */", app_source)
            self.assertIn("positive: assetToAdd.positive", app_source)
            self.assertNotIn("delta: ( */", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_jsx_expression_comment_split_identifiers(self):
        code_dir = _case_dir("componentized-runtime-jsx-expression-comment-split")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  const formData = { workspaceName: 'alpha team' };\n"
                "  return <span>https://app.ai-platform.com/{form */\n"
                "Data.workspaceName.toLowerCase().replace(/\\s/g, '-')}/</span>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("{formData.workspaceName.toLowerCase().replace(/\\s/g, '-')}", app_source)
            self.assertNotIn("{form */", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_escapes_jsx_code_block_brace_literals(self):
        code_dir = _case_dir("componentized-runtime-jsx-code-block-braces")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <pre>\n"
                "      <code>\n"
                "        const briefSchema = {{\n"
                "          title: 'string',\n"
                "          sections: [{{ heading: 'string' }}]\n"
                "        }}\n"
                "      </code>\n"
                "    </pre>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("const briefSchema = &#123;", app_source)
            self.assertIn("sections: [&#123; heading: 'string' &#125;]", app_source)
            self.assertIn("&#125;", app_source)
            self.assertNotIn("{{", app_source)
            self.assertNotIn("}}", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_normalizes_run_on_natural_language_notes(self):
        code_dir = _case_dir("componentized-runtime-natural-language-note")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  const next = (() => {\n"
                "    Return (simplified for mock)        const totalReturnChange = 42;\n"
                "    return totalReturnChange;\n"
                "  })();\n"
                "  return <div>{next}</div>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* simplified for mock */", app_source)
            self.assertIn("const totalReturnChange = 42;", app_source)
            self.assertNotIn("Return (simplified for mock)", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_merges_post_comment_run_on_note(self):
        code_dir = _case_dir("componentized-runtime-post-comment-note")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  useEffect(() => {\n"
                "    /* This effect ensures */\n"
                "    Alpine.js reacts to React's isCartOpen state\n"
                "    const next = window.Alpine;\n"
                "  }, []);\n"
                "  return null;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* This effect ensures Alpine.js reacts to React's isCartOpen state */", app_source)
            self.assertNotIn("Alpine.js reacts to React's isCartOpen state\n", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_merges_post_comment_instruction_note_with_underscores(self):
        code_dir = _case_dir("componentized-runtime-post-comment-note-underscores")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  /* Inline helper components/ */\n"
                "  functions to adhere to output_files constraint\n"
                "  const InputField = () => <input />;\n"
                "  return <InputField />;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* Inline helper components/ functions to adhere to output_files constraint */", app_source)
            self.assertIn("const InputField = () => <input />;", app_source)
            self.assertNotIn("functions to adhere to output_files constraint\n", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_normalizes_run_on_data_notes(self):
        code_dir = _case_dir("componentized-runtime-data-note")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "DashboardLayout.tsx").write_text(
                "import PortfolioBreakdown from './PortfolioBreakdown';\n"
                "import WatchlistTable from './WatchlistTable';\n"
                "Data (inlined as per output_files constraint)const kpis = [{ label: 'Portfolio Value', value: 185230.50 }];\n"
                "export default function DashboardLayout() { return <div />; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            layout_source = (code_dir / "src" / "components" / "DashboardLayout.tsx").read_text(encoding="utf-8")
            self.assertIn("/* inlined as per output_files constraint */", layout_source)
            self.assertIn("const kpis =", layout_source)
            self.assertNotIn("Data (inlined as per output_files constraint)const", layout_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_inline_block_comment_continuations(self):
        code_dir = _case_dir("componentized-runtime-inline-comment-continuation")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  setOpenPositions(prev => Math.max(1, prev + (Math.random() > 0.5 ? 1 : -1))); /* +/- 1    }, 3000);\n"
                "  return null;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("setOpenPositions(prev => Math.max(1, prev + (Math.random() > 0.5 ? 1 : -1))); /* +/- 1 */", app_source)
            self.assertIn("}, 3000);", app_source)
            self.assertNotIn("/* +/- 1    }, 3000);", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_multiline_block_comment_line_notes(self):
        code_dir = _case_dir("componentized-runtime-multiline-block-comment-line-note")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  if (true) {\n"
                "    /* No specific validation needed for integration selection, keys are optional\n"
                "    // Can add validation if integrations are required */\n"
                "  }\n"
                "  return null;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn(
                "/* No specific validation needed for integration selection, keys are optional Can add validation if integrations are required */",
                app_source,
            )
            self.assertNotIn("// Can add validation", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_orphan_comment_split_string_literals(self):
        code_dir = _case_dir("componentized-runtime-orphan-string-split")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <svg><rect fill={isBullish ? ' */\n"
                "var(--success)' : 'var(--danger)'} /></svg>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("fill={isBullish ? 'var(--success)' : 'var(--danger)'}", app_source)
            self.assertNotIn("' */", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_normalizes_lowercase_object_field_labels(self):
        code_dir = _case_dir("componentized-runtime-lowercase-object-label")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  const item = {\n"
                "constant for mock            value: 42,\n"
                "  };\n"
                "  return <pre>{item.value}</pre>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* constant for mock */", app_source)
            self.assertIn("value: 42,", app_source)
            self.assertNotIn("constant for mock            value:", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_jsx_event_handler_arrow_bleed(self):
        code_dir = _case_dir("componentized-runtime-jsx-arrow-bleed")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <>\n"
                "      <input onChange={e = /> setValue(e.target.value)} />\n"
                "      <input onChange={(e) = /> setFilter(e.target.value)} />\n"
                "    </>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("onChange={e => setValue(e.target.value)}", app_source)
            self.assertIn("onChange={(e) => setFilter(e.target.value)}", app_source)
            self.assertNotIn("onChange={e = />", app_source)
            self.assertNotIn("onChange={(e) = />", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_multiline_comment_code_bleed(self):
        code_dir = _case_dir("componentized-runtime-multiline-comment-code-bleed")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  const handleCommentBubbleClick = () => { setCommentsVisible(true); /* Open inspector to comments console.log('Comment bubble clicked, opening comments panel.');\n"
                "  };  // Simulate collaborator cursor movement for demonstration */\n"
                "  useEffect(() => {}, []);\n"
                "  return null;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("setCommentsVisible(true); /* Open inspector to comments */", app_source)
            self.assertIn("console.log('Comment bubble clicked, opening comments panel.');", app_source)
            self.assertIn("/* Simulate collaborator cursor movement for demonstration */", app_source)
            self.assertNotIn("comments console.log", app_source)
            self.assertNotIn("// Simulate collaborator cursor movement for demonstration */", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_generic_arrow_bleed(self):
        code_dir = _case_dir("componentized-runtime-generic-arrow-bleed")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  const labels = ['workspaceName'].map((key) => key.split(/(?=[A-Z])/).join(' ').replace(/^./, str = /> str.toUpperCase()));\n"
                "  return <div>{labels[0]}</div>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("replace(/^./, str => str.toUpperCase())", app_source)
            self.assertNotIn("str = />", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_normalize_componentized_file_repairs_project_617_ternary_branch_orphan_closers(self):
        source_path = REPO_ROOT / "generated" / "617" / "v1" / "code" / "src" / "App.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/App.tsx", source)

        self.assertRegex(
            normalized,
            re.compile(
                r"\)\s*:\s*\(\s*<Dashboard activities=\{activities\} />\s*\)\}",
                re.MULTILINE,
            ),
        )
        self.assertNotIn("</Dashboard>", normalized)
        self.assertNotIn("</TransactionForm>", normalized)
        self.assertRegex(
            normalized,
            re.compile(
                r"<TransactionForm[\s\S]*?/\>[\s\S]*?</Sidebar>\s*</div>\s*\);\s*}",
                re.MULTILINE,
            ),
        )

    def test_normalize_componentized_file_repairs_project_617_logical_and_branch_orphan_closers(self):
        source_path = REPO_ROOT / "generated" / "617" / "v1" / "code" / "src" / "components" / "TransactionForm.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/components/TransactionForm.tsx", source)

        self.assertEqual(normalized.count("</form>"), 1)
        self.assertRegex(
            normalized,
            re.compile(
                r"\{type !== 'transfer' && \(\s*<div className=\"form-group\">[\s\S]*?</div>\s*\)\}",
                re.MULTILINE,
            ),
        )

    def test_normalize_componentized_file_repairs_project_618_multi_param_arrow_bleed(self):
        source_path = REPO_ROOT / "generated" / "618" / "v1" / "code" / "src" / "components" / "Dashboard.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/components/Dashboard.tsx", source)

        self.assertEqual(normalized.count("chartData.values.map((val, i) => `L${"), 2)
        self.assertNotIn("= />", normalized)
        self.assertIn("currentPrice,", normalized)
        self.assertNotIn("/* currentPrice, */", normalized)
        self.assertEqual(normalized.count("/*"), normalized.count("*/"))

    def test_normalize_componentized_file_repairs_project_625_nested_kpi_branch_orphan_closer(self):
        source_path = REPO_ROOT / "generated" / "625" / "v1" / "code" / "src" / "components" / "Dashboard.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/components/Dashboard.tsx", source)

        self.assertNotRegex(
            normalized,
            re.compile(
                r"\)\s*:\s*\(\s*<span[\s\S]*?</span>\s*</div>\s*\)\}",
                re.MULTILINE,
            ),
        )
        self.assertRegex(
            normalized,
            re.compile(
                r"\{kpi.label === 'Best Performer' \? \([\s\S]*?\)\}\s*<span className=\{`kpi-delta[\s\S]*?</span>\s*</div>",
                re.MULTILINE,
            ),
        )
        self.assertIn("            </div>\n          ))}", normalized)
        self.assertEqual(normalized.count("<>"), normalized.count("</>"))

    def test_normalize_componentized_file_repairs_project_626_layout_main_wrapper_leak(self):
        source_path = REPO_ROOT / "generated" / "626" / "v1" / "code" / "src" / "components" / "DashboardLayout.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/components/DashboardLayout.tsx", source)

        self.assertRegex(
            normalized,
            re.compile(r"</aside>\s*<main className=\"main-content\">", re.MULTILINE),
        )
        self.assertRegex(
            normalized,
            re.compile(r"</main>\s*</div>\s*\);\s*$", re.MULTILINE),
        )
        self._assert_jsx_return_would_parse(normalized)

    def test_normalize_componentized_file_repairs_project_628_relational_operator_bleed(self):
        source_path = REPO_ROOT / "generated" / "628" / "v1" / "code" / "src" / "components" / "Dashboard.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/components/Dashboard.tsx", source)

        self.assertIn("stroke={ticker.delta >= 0 ? 'var(--accent)' : 'var(--danger)'}", normalized)
        self.assertNotIn("/>=", normalized)

    def test_normalize_componentized_file_repairs_project_634_orphan_prose_comment_line(self):
        source_path = REPO_ROOT / "generated" / "634" / "v1" / "code" / "src" / "components" / "ChartCard.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/components/ChartCard.tsx", source)

        self.assertNotRegex(normalized, re.compile(r"(?m)^Box \(0-1000 for x, 0-300 for y\)"))
        self.assertIn("/* Box (0-1000 for x, 0-300 for y)", normalized)
        self.assertEqual(normalized.count("/*"), normalized.count("*/"))

    def test_normalize_componentized_file_repairs_project_634_duplicate_kpi_label_prop_collision(self):
        source_path = REPO_ROOT / "generated" / "634" / "v1" / "code" / "src" / "components" / "KpiCards.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/components/KpiCards.tsx", source)

        self.assertIn("label,", normalized)
        self.assertNotIn("/* label, */", normalized)
        self.assertEqual(normalized.count("label="), 4)
        self.assertNotIn('valueFormat="percentage" label="ETH"', normalized)

    def test_normalize_componentized_file_repairs_project_639_split_svg_fill_attribute(self):
        source_path = REPO_ROOT / "generated" / "639" / "v1" / "code" / "src" / "components" / "Chart.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/components/Chart.tsx", source)

        self.assertIn('fill="var(--accent)"', normalized)
        self.assertNotRegex(normalized, re.compile(r"(?m)^\s*var\(--accent\)\"\s+stroke="))
        self.assertIn('stroke="var(--card-bg)"', normalized)
        self.assertIn("onMouseLeave={handleMouseLeave}", normalized)

    def test_normalize_componentized_file_repairs_project_640_missing_logical_branch_closer(self):
        source_path = REPO_ROOT / "generated" / "640" / "v1" / "code" / "src" / "App.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/App.tsx", source)

        self.assertRegex(
            normalized,
            re.compile(
                r"\{tooltip && \(\s*<div[\s\S]*?\{tooltip.content\}\s*</div>\s*\)\}",
                re.MULTILINE,
            ),
        )
        self._assert_jsx_return_would_parse(normalized)

    def test_normalize_componentized_file_repairs_project_649_self_closing_component_child_leak(self):
        source_path = REPO_ROOT / "generated" / "649" / "v1" / "code" / "src" / "App.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/App.tsx", source)

        self.assertIn("<ChartComponent onChipClick=", normalized)
        self.assertIn("</ChartComponent>", normalized)
        self.assertNotIn("<ChartComponent onChipClick={(action) => console.log(`Chart action: ${action}`)} />", normalized)
        self.assertIn("<HoldingsTable onManageClick=", normalized)
        self.assertIn("</HoldingsTable>", normalized)
        self.assertNotIn("<HoldingsTable onManageClick={(asset) => openModal(`Managing ${asset} details...`)} />", normalized)

    def test_normalize_componentized_file_repairs_project_650_logical_svg_sibling_condition(self):
        source_path = REPO_ROOT / "generated" / "650" / "v1" / "code" / "src" / "App.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/App.tsx", source)

        self.assertIn('{item === "Markets" && (<><path d="M3 3v18h18" /><path d="M18.7 8.3L12 15l-3.3-3.3L3 18" /></>)}', normalized)
        self.assertIn('{item === "Orders" && (<><rect x="2" y="7" width="20" height="14" rx="2" ry="2" /><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" /></>)}', normalized)
        self.assertNotRegex(normalized, re.compile(r'\{item === "Markets" && <path[\s\S]*?<path'))

    def test_normalize_componentized_file_repairs_project_653_bare_jsx_array_map_expression(self):
        source_path = REPO_ROOT / "generated" / "653" / "v1" / "code" / "src" / "components" / "Dashboard.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/components/Dashboard.tsx", source)

        self.assertIn("{/* Horizontal grid lines */}{[...Array(5)].map((_, i) => (", normalized)
        self.assertNotIn("{/* Horizontal grid lines */}[...Array(5)].map((_, i) => (", normalized)
        self.assertNotIn("</path>", normalized)

    def test_normalize_componentized_file_repairs_project_672_split_state_setter_and_component_closer_leaks(self):
        source_path = REPO_ROOT / "generated" / "672" / "v1" / "code" / "src" / "components" / "Dashboard.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/components/Dashboard.tsx", source)

        self.assertIn("setIsTransactionFormOpen(true)", normalized)
        self.assertNotIn("set\nIsTransactionFormOpen(true)", normalized)
        self.assertIn("<PortfolioSummary onAddHoldingClick={() => setIsTransactionFormOpen(true)}>", normalized)
        self.assertNotIn("<PortfolioSummary onAddHoldingClick={() => setIsTransactionFormOpen(true)} />", normalized)
        self.assertNotIn("</CryptoSearch>", normalized)
        self.assertNotIn("</TransactionForm>", normalized)

    def test_normalize_componentized_file_repairs_project_674_tsconfig_standalone_comma_noise(self):
        source_path = REPO_ROOT / "generated" / "674" / "v1" / "code" / "tsconfig.json"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("tsconfig.json", source)

        self.assertNotIn("\n    ,\n", normalized)
        data = json.loads(normalized)
        self.assertFalse(data["compilerOptions"]["noUnusedLocals"])
        self.assertFalse(data["compilerOptions"]["noUnusedParameters"])

    def test_normalize_componentized_file_repairs_project_681_modal_branch_missing_wrapper_close(self):
        source_path = REPO_ROOT / "generated" / "681" / "v1" / "code" / "src" / "App.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/App.tsx", source)

        self.assertIn("{modalContent}\n          </div>\n        </div>\n      )}", normalized)

    def test_normalize_componentized_file_repairs_project_683_inline_return_root_close_leak(self):
        source_path = REPO_ROOT / "generated" / "683" / "v1" / "code" / "src" / "pages" / "DashboardPage.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/pages/DashboardPage.tsx", source)

        self.assertRegex(normalized, r"return\s*\(\s*\n\s*<div className=\"dashboard-layout\">")
        self.assertRegex(normalized, r"</div>\s*\n\s*\);")
        self.assertNotIn("</div>  );", normalized)

    def test_normalize_componentized_file_repairs_project_684_layout_root_close_before_main_comment_gap(self):
        source_path = REPO_ROOT / "generated" / "684" / "v1" / "code" / "src" / "components" / "Dashboard.tsx"
        source = source_path.read_text(encoding="utf-8")

        normalized = _normalize_componentized_file("src/components/Dashboard.tsx", source)

        self.assertNotRegex(normalized, re.compile(r"</aside>\s*\n\s*</div>\s*\n\s*\{/\* Main Content \*/\}"))
        self.assertIn("{/* Main Content */}", normalized)
        self.assertIn("<main className=\"main-content\">", normalized)

    def test_normalize_componentized_file_repairs_inline_jsx_attribute_block_comment_bleed(self):
        source = """
const View = () => (
  <text
    key={`y-label-${index}`}
    x={-10} /* Position slightly outside to the left                  y={y + 5}
    textAnchor="start"
    className="chart-axis-label"
  >
    ${value}k
  </text>
);
""".lstrip()

        normalized = _normalize_componentized_file("src/pages/DashboardPage.tsx", source)

        self.assertIn("x={-10}", normalized)
        self.assertIn("textAnchor=\"start\"", normalized)
        self.assertNotIn("/* Position slightly outside to the left", normalized)

    def test_ensure_componentized_workspace_support_restores_missing_vite_bin_shims(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code_dir = Path(tmpdir)
            (code_dir / "package.json").write_text(
                (REPO_ROOT / "generated" / "675" / "v1" / "code" / "package.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (code_dir / "tsconfig.json").write_text(
                '{"compilerOptions":{"jsx":"react-jsx"},"include":["src"]}\n',
                encoding="utf-8",
            )
            (code_dir / "src").mkdir()
            (code_dir / "src" / "App.tsx").write_text("export default function App() { return <div />; }\n", encoding="utf-8")
            (code_dir / "node_modules" / "vite" / "bin").mkdir(parents=True)
            (code_dir / "node_modules" / "vite" / "bin" / "vite.js").write_text("console.log('vite');\n", encoding="utf-8")

            result = ensure_componentized_workspace_support(code_dir)

            self.assertIn("node_modules/.bin/vite.cmd", result["created_files"])
            self.assertTrue((code_dir / "node_modules" / ".bin" / "vite.cmd").exists())
            self.assertTrue((code_dir / "node_modules" / ".bin" / "vite").exists())

    def test_ensure_componentized_workspace_support_precreates_vite_bin_shims_from_package_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code_dir = Path(tmpdir)
            (code_dir / "package.json").write_text(
                (REPO_ROOT / "generated" / "682" / "v1" / "code" / "package.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (code_dir / "tsconfig.json").write_text(
                '{"compilerOptions":{"jsx":"react-jsx"},"include":["src"]}\n',
                encoding="utf-8",
            )
            (code_dir / "src").mkdir()
            (code_dir / "src" / "App.tsx").write_text("export default function App() { return <div />; }\n", encoding="utf-8")

            result = ensure_componentized_workspace_support(code_dir)

            self.assertIn("node_modules/.bin/vite.cmd", result["created_files"])
            self.assertTrue((code_dir / "node_modules" / ".bin" / "vite.cmd").exists())
            self.assertTrue((code_dir / "node_modules" / ".bin" / "vite").exists())

    def test_ensure_componentized_workspace_support_strips_main_entry_import_note_bleed(self):
        code_dir = _case_dir("componentized-runtime-main-entry-import-note-bleed")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <div>Desk</div>;\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';/* base.css is provided by the system, so we just */\n"
                "import it./* The actual content of base.css is assumed to be available. */\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir, ui_archetype="fintech")

            main_source = (code_dir / "src" / "main.tsx").read_text(encoding="utf-8")
            self.assertIn("import App from './App';", main_source)
            self.assertNotIn("import it.", main_source)
            self.assertIn('import "./base.css";', main_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_control_flow_orphan_comment_close(self):
        code_dir = _case_dir("componentized-runtime-control-flow-comment-close")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  const currentValue = 0; /* Only animate if target value changes significantly or on initial load */\n"
                "  if ( */\n"
                "    Math.abs(10 - currentValue) > 0.01\n"
                "  ) {\n"
                "    return <div>Desk</div>;\n"
                "  }\n"
                "  return null;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertNotIn("if ( */", app_source)
            self.assertIn("if (Math.abs(10 - currentValue) > 0.01", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_restores_array_close_after_comment_swallow(self):
        code_dir = _case_dir("componentized-runtime-array-close-comment-swallow")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "data.ts").write_text(
                "export const generateKpis = () => [\n"
                "  { label: 'Portfolio Value', value: 124832.14 },\n"
                "  { label: 'Top Performer', value: 7.1 }, /* TSLA  { label: 'Open Positions', value: 12 },]; */\n"
                "export const generatePortfolio = () => [\n"
                "  { asset: 'AAPL', value: 8760.0 },\n"
                "];\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            data_source = (code_dir / "src" / "data.ts").read_text(encoding="utf-8")
            self.assertIn("/* TSLA { label: 'Open Positions', value: 12 }, */", data_source)
            self.assertIn("];\nexport const generatePortfolio", data_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_strips_orphan_comment_close_after_array_statement(self):
        code_dir = _case_dir("componentized-runtime-array-orphan-comment-close")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "const items = [\n"
                "  'a',\n"
                "  'b',\n"
                "]; */\n"
                "export default function App() {\n"
                "  return <div>{items.join(', ')}</div>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("];\nexport default function App()", app_source)
            self.assertNotIn("]; */", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_css_data_uri_quote_bleed(self):
        code_dir = _case_dir("componentized-runtime-css-data-uri-quote-bleed")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "style.css").write_text(
                ".noise-overlay {\n"
                "  background-image: url('data:image/svg+xml,<svg opacity=\\'0.1\\'><filter id=\\'n\\'><feTurbulence type=\\'fractalNoise\\' baseFrequency=\\'0.9\\'\\'' numOctaves=\\'4\\' stitchTiles=\\'stitch\\'/></filter></svg>');\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            css_source = (code_dir / "src" / "style.css").read_text(encoding="utf-8")
            self.assertIn("baseFrequency=\\'0.9\\' numOctaves=\\'4\\'", css_source)
            self.assertNotIn("\\'\\'' numOctaves", css_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_strips_inline_jsx_attribute_comments(self):
        code_dir = _case_dir("componentized-runtime-jsx-attr-comment-bleed")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "const chartHeight = 200;\n"
                "export default function App() {\n"
                "  return (\n"
                "    <svg>\n"
                "      <text y={chartHeight + 15} /* Below the chart */ x={-5} // Left of the chart\n"
                "        textAnchor=\"middle\"\n"
                "      >Jan</text>\n"
                "    </svg>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("y={chartHeight + 15}", app_source)
            self.assertIn("x={-5}", app_source)
            self.assertNotIn("/* Below the chart */", app_source)
            self.assertNotIn("// Left of the chart", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_svg_namespace_protocol(self):
        code_dir = _case_dir("componentized-runtime-svg-xmlns-protocol")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <svg xmlns=\"http:www.w3.org/2000/svg\"><circle cx=\"12\" cy=\"12\" r=\"10\" /></svg>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn('xmlns="http://www.w3.org/2000/svg"', app_source)
            self.assertNotIn('xmlns="http:www.w3.org/2000/svg"', app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_normalizes_broken_responsive_css_tail(self):
        code_dir = _case_dir("componentized-runtime-broken-responsive-tail")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "index.css").write_text(
                ":root{--text-secondary:#A0A0AAB;}.activity-feed{color:#fff;}/* Responsive Adjustments */"
                "@media (max-width: 1200px) {.kpi-grid{grid-template-columns:1fr;}.content-area{padding:1rem;}.activity-feed{position:static;}}"
                ".activity-feed{max-height:400px;}.header-bar{padding:0 1rem;}.sidebar{border-right:none;}}"
                "@media (max-width: 768px) {.sidebar{display:none;}}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            css_source = (code_dir / "src" / "index.css").read_text(encoding="utf-8")
            self.assertIn("--text-secondary:#A0A0AA;", css_source)
            self.assertNotIn("#A0A0AAB", css_source)
            self.assertIn("@media (max-width: 1200px)", css_source)
            self.assertIn("max-height: 400px;", css_source)
            self.assertNotIn("}}.activity-feed", css_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_lightweight_chart_helper_corruption(self):
        code_dir = _case_dir("componentized-runtime-lightweight-chart-helper")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React, { useCallback, useEffect, useRef, useState } from 'react';\n"
                "import { createChart, IChartApi, ISeriesApi, CandlestickData, LineData, Time } from 'lightweight-charts';\n"
                "const generateRandomCandlestickData = (count: number, basePrice: number): CandlestickData[] => {  const data: CandlestickData[] = [];\n"
                "let lastPrice = basePrice;\n"
                "for (let i = 0; i < count; i++) {    const open = lastPrice + (Math.random() - 0.5) * 5;\n"
                "const close = open + (Math.random() - 0.5) * 10;\n"
                "const high = Math.max(open, close) + Math.random() * 5;\n"
                "const low = Math.min(open, close) - Math.random() * 5;    lastPrice = close;    data.push({      time: (1672531200 + i * 86400) as Time, /* Start from Jan 1, 2023      open,\n"
                "      high,\n"
                "      low,\n"
                "      close,\n"
                "    });  }\n"
                "return data;};\n"
                "const generateLineData = (count: number, basePrice: number): LineData[] => {  const data: LineData[] = [];\n"
                "let lastValue = basePrice;\n"
                "for (let i = 0; i < count; i++) {    lastValue += (Math.random() - 0.5) * 2; /* Simulate small fluctuations data.push({ */\n"
                "time: (1672531200 + i * 86400) as Time,\n"
                "      value: lastValue,\n"
                "    });  }\n"
                "return data;};\n"
                "export default function App() {\n"
                "  const [chartTimeframe] = useState<'1D' | '1W' | '1M' | '1Y' | 'ALL'>('1M');\n"
                "  const [currentChartData, setCurrentChartData] = useState<CandlestickData[]>([]);\n"
                "  const [currentVolumeData, setCurrentVolumeData] = useState<LineData[]>([]);\n"
                "  const chartContainerRef = useRef<HTMLDivElement>(null);\n"
                "  const chartRef = useRef<IChartApi | null>(null);\n"
                "  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);\n"
                "  const volumeSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);\n"
                "  const getChartDataForSymbol = useCallback((symbol: string, timeframe: typeof chartTimeframe) => {    /* This would fetch real data, here we simulate */\n"
                "const basePrice = (symbol === 'SPY' ? 500 : (symbol === 'GOOGL' ? 150 : 170)) + Math.random() * 20;\n"
                "let count = 60; /* Default for 1M if (timeframe === '1D') count = 30; Hourly */\n"
                "if (timeframe === '1W') count = 7;\n"
                "if (timeframe === '1Y') count = 250; // Daily    if (timeframe === 'ALL') count = 500; */\n"
                "const newCandlestickData = generateRandomCandlestickData(count, basePrice);\n"
                "const newVolumeData = newCandlestickData.map(d => ({\n"
                "      time: d.time,\n"
                "      value: Math.random() * 10000000 + 5000000, /* Simulate volume }));\n"
                "setCurrentChartData(newCandlestickData);    setCurrentVolumeData(newVolumeData);  }, []);\n"
                "useEffect(() => {    if (chartContainerRef.current) {      if (!chartRef.current) {\n"
                "        const chart = createChart(chartContainerRef.current, {\n"
                "          crosshair: {\n"
                "            mode: 0, /* Magnet mode }, */\n"
                "handleScroll: { vertTouchDrag: true, }, handleScale: { axisPressedMo/* useMove: true, */\n"
                "}        });\n"
                "        chartRef.current = chart;\n"
                "        candlestickSeriesRef.current = chart.addCandlestickSeries({ upColor: '#00C853', downColor: '#FF3D00', borderVisible: false, wickUpColor: '#00C853', wickDownColor: '#FF3D00' });\n"
                "        volumeSeriesRef.current = chart.addLineSeries({ color: '#A0A0A5', lineWidth: 1, priceFormat: { type: 'volume' }, overlay: true, scaleMargins: { top: 0.8, bottom: 0 } });\n"
                "      }\n"
                "    }  }, [currentChartData, currentVolumeData]);\n"
                "  return <div ref={chartContainerRef} />;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("open,", app_source)
            self.assertIn("const newVolumeData = newCandlestickData.map((datum) => ({", app_source)
            self.assertIn("if (timeframe === '1D') count = 30;", app_source)
            self.assertIn("handleScale: { axisPressedMouseMove: true }", app_source)
            self.assertNotIn("axisPressedMo/* useMove: true, */", app_source)
            self.assertNotIn("Simulate volume }));", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_inline_block_comment_note_code_bleed(self):
        code_dir = _case_dir("componentized-runtime-inline-note-code-bleed")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  useEffect(() => {    /* This */\n"
                "  useEffect is to trigger the price flash animation    tickers.forEach((ticker) => console.log(ticker));\n"
                "  }, [tickers]);\n"
                "  return null;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* This useEffect is to trigger the price flash animation */", app_source)
            self.assertIn("tickers.forEach((ticker) => console.log(ticker));", app_source)
            self.assertNotIn("useEffect is to trigger the price flash animation    tickers.forEach", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_rewrites_duplicate_label_object_fields(self):
        code_dir = _case_dir("componentized-runtime-duplicate-label-field")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  const kpis = [\n"
                "    { label: 'Best Performer', value: 3.2, deltaType: 'positive', unit: '%', label: 'TSLA' },\n"
                "  ];\n"
                "  return <pre>{JSON.stringify(kpis)}</pre>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("asset: 'TSLA'", app_source)
            self.assertNotIn("unit: '%', label: 'TSLA'", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_wraps_adjacent_jsx_roots_and_repairs_protocol_slashes(self):
        code_dir = _case_dir("componentized-runtime-adjacent-jsx-roots")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "Topbar.tsx").write_text(
                "import React from 'react';\n"
                "export default function Topbar() {\n"
                "  return (<header className=\"topbar\"><img src=\"https:api.dicebear.com/7.x/initials/svg?seed=JD\" alt=\"Avatar\" /></header><section className=\"ticker-row\"><span>BTC</span></section>);\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            topbar_source = (code_dir / "src" / "components" / "Topbar.tsx").read_text(encoding="utf-8")
            self.assertIn('src="https://api.dicebear.com/7.x/initials/svg?seed=JD"', topbar_source)
            self.assertIn("return (<><header", topbar_source)
            self.assertIn("</section></>);", topbar_source)
            self.assertNotIn('src="https:api.dicebear.com', topbar_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_tradingview_placeholder_corruption(self):
        code_dir = _case_dir("componentized-runtime-tradingview-placeholder")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "CandlestickChart.tsx").write_text(
                "import React from 'react';\n"
                "export const CandlestickChart: React.FC = () => {\n"
                "  /* This component would typically integrate a charting library like */\n"
                "TradingView.\n"
                "  /* React.useEffect(() => { const widget = new window.TradingView.widget({ */\n"
                "container_id: \"tradingview_chart\", symbol: \"BINANCE:BTCUSDT\" /* ... */\n"
                "return () =>widget.remove(); }, []); /* return<div id=\"tradingview_chart\" className=\"tradingview-chart-container\" />;\n"
                "const chartData = [{ x: 50, open: 200, close: 220, high: 230, low: 190, color: 'var(--success)' }];\n"
                "return <div />;\n"
                "};\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            chart_source = (code_dir / "src" / "components" / "CandlestickChart.tsx").read_text(encoding="utf-8")
            self.assertIn("type ChartDatum = {", chart_source)
            self.assertIn("export const CandlestickChart: React.FC = () => {", chart_source)
            self.assertIn("const chartData: ChartDatum[] = [", chart_source)
            self.assertIn("export default CandlestickChart;", chart_source)
            self.assertNotIn("return () =>widget.remove();", chart_source)
            self.assertNotIn("container_id: \"tradingview_chart\"", chart_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_orphan_comment_split_identifiers_in_jsx(self):
        code_dir = _case_dir("componentized-runtime-orphan-jsx-identifier-split")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  const liveTickers = [{ symbol: 'AAPL' }];\n"
                "  return <section>{live */\n"
                "Tickers.map((ticker) => <div key={ticker.symbol}>{ticker.symbol}</div>)}</section>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("{liveTickers.map((ticker)", app_source)
            self.assertNotIn("live */", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_repeated_orphan_current_target_splits(self):
        code_dir = _case_dir("componentized-runtime-orphan-current-target-split")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <img onError={(e) => { e.current */\n"
                "Target.src='fallback.png'; e.current */\n"
                "Target.style.backgroundColor='black'; e.currentTarget.style.objectFit='contain'; }} />;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertEqual(app_source.count("currentTarget"), 3)
            self.assertNotIn("current */", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_orphan_comment_close_inside_string_literals(self):
        code_dir = _case_dir("componentized-runtime-orphan-string-close")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "ProjectsGrid.tsx").write_text(
                "export default function ProjectsGrid() {\n"
                "  const projects = [\n"
                '    { tech: [" */\n'
                'Next.js", "D3.js"], image: "https://image.pollinations.ai/prompt/mobile%20meditation%20app%20 */\n'
                'interface?width=800" },\n'
                "  ];\n"
                "  return <div>{projects[0].tech[0]} {projects[0].image}</div>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "ProjectsGrid.tsx").read_text(encoding="utf-8")
            self.assertIn('"Next.js"', source)
            self.assertIn('"https://image.pollinations.ai/prompt/mobile%20meditation%20app%20interface?width=800"', source)
            self.assertNotIn('*/\nNext.js"', source)
            self.assertNotIn(" */\ninterface", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_jsx_comment_swallowed_tag_boundaries(self):
        code_dir = _case_dir("componentized-runtime-jsx-tag-boundary-comment")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "HeroBanner.tsx").write_text(
                "import React from 'react';\n"
                "const HeroBanner: React.FC = () => {  return (    <section className=\"hero-banner\">      <div        className=\"hero-bg\"        style={{ backgroundImage: `url('generated-assets/hero_background.png')` }}        /* onerror=\"this.style.background='linear-gradient(135deg,#1a1a1f,#222228)'\" JS onerror not valid in React style prop ></div> <div */\n"
                "        className=\"hero-overlay\"></div>      <div className=\"hero-content\">Hero</div>    </section>  );};\n"
                "export default HeroBanner;\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "components" / "HeroBanner.tsx").read_text(encoding="utf-8")
            self.assertNotIn("JS onerror not valid in React style prop", source)
            self.assertIn('style={{ backgroundImage: `url(\'generated-assets/hero_background.png\')` }}', source)
            self.assertIn("></div> <div", source)
            self.assertIn('className="hero-overlay"></div>', source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_strips_alpine_jsx_directives(self):
        code_dir = _case_dir("componentized-runtime-alpine-directives")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "CartDrawer.tsx").write_text(
                "import React from 'react';\n"
                "export default function CartDrawer({ cartOpen, toggleCart }) {\n"
                "  return (\n"
                "    <div className=\"cart-drawer\" x-data={`{ cartOpen: ${cartOpen} }`} x-show=\"cartOpen\" /* @ts-ignore */\n"
                "Alpine.js specific directive @click.away=\"cartOpen = false\" x-transition:enter=\"ease-out duration-300\">\n"
                "      <button onClick={toggleCart}>Close</button>\n"
                "    </div>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "components" / "CartDrawer.tsx").read_text(encoding="utf-8")
            self.assertIn('className="cart-drawer"', source)
            self.assertNotIn("x-data", source)
            self.assertNotIn("x-show", source)
            self.assertNotIn("@click.away", source)
            self.assertNotIn("Alpine.js specific directive", source)
            self.assertNotIn("@ts-ignore", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_self_closing_link_wrappers(self):
        code_dir = _case_dir("componentized-runtime-self-closing-link-wrapper")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "ProductCard.tsx").write_text(
                "import React from 'react';\n"
                "import { Link } from 'react-router-dom';\n"
                "export default function ProductCard() {\n"
                "  return (\n"
                "    <Link to=\"/product/1\" className=\"product-card\" />\n"
                "      <div className=\"product-info\">Product</div>\n"
                "    </Link>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "components" / "ProductCard.tsx").read_text(encoding="utf-8")
            self.assertIn('<Link to="/product/1" className="product-card">', source)
            self.assertNotIn('className="product-card" />', source)
            self.assertIn("</Link>", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_normalizes_browser_router_for_preview(self):
        code_dir = _case_dir("componentized-runtime-browser-router-preview")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';\n"
                "export default function App() {\n"
                "  return (\n"
                "    <Router>\n"
                "      <Routes>\n"
                "        <Route path=\"/\" element={<Navigate to=\"dashboard\" replace />} />\n"
                "      </Routes>\n"
                "    </Router>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("HashRouter as Router", source)
            self.assertNotIn("BrowserRouter as Router", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_removes_orphan_jsx_closing_brace_lines(self):
        code_dir = _case_dir("componentized-runtime-orphan-jsx-closing-brace")
        try:
            (code_dir / "src" / "pages").mkdir(parents=True)
            (code_dir / "src" / "pages" / "HomePage.tsx").write_text(
                "export default function HomePage() {\n"
                "  return (\n"
                "    <section>\n"
                "      <a href=\"#\" className=\"collection-card\">\n"
                "        <div className=\"collection-overlay\">\n"
                "          <span>8 Items</span>\n"
                "        }\n"
                "      </a>\n"
                "    </section>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "pages" / "HomePage.tsx").read_text(encoding="utf-8")
            self.assertNotIn("\n        }\n      </a>", source)
            self.assertIn("</div>\n      </a>", source)
            self.assertIn('<a href="#" className="collection-card">', source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_removes_orphan_jsx_closing_brace_before_next_tag(self):
        code_dir = _case_dir("componentized-runtime-orphan-jsx-closing-brace-next-tag")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <aside>\n"
                "      <div className=\"summary-item\">\n"
                "        <span className=\"value\">{formData.workspaceName || 'N/A'}</span>\n"
                "      }\n"
                "      <div className=\"summary-item\">\n"
                "        <span className=\"label\">Integrations</span>\n"
                "      </div>\n"
                "    </aside>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertNotIn("\n      }\n      <div className=\"summary-item\">", source)
            self.assertIn("</div>\n      <div className=\"summary-item\">", source)
            self.assertIn("<span className=\"label\">Integrations</span>", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_missing_sibling_closing_tags(self):
        code_dir = _case_dir("componentized-runtime-missing-sibling-closing-tags")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <aside>\n"
                "      <div className=\"summary-section\">\n"
                "        <div className=\"summary-item\">\n"
                "          <span className=\"value\">Workspace</span>\n"
                "        <div className=\"summary-item\">\n"
                "          <span className=\"label\">Integrations</span>\n"
                "          <span className=\"value\">3 Connected</span>\n"
                "        </div>\n"
                "      </div>\n"
                "    </aside>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("</div>\n        <div className=\"summary-item\">", source)
            self.assertIn("</div>\n    </aside>", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_orphaned_dashboard_sidebar_children(self):
        source = (
            "export default function Layout() {\n"
            "  return (\n"
            "    <div className=\"dashboard-layout\">\n"
            "      <aside className=\"sidebar\">\n"
            "        <nav className=\"sidebar-nav\">\n"
            "          <div className=\"sidebar-group\">\n"
            "            <span>Overview</span>\n"
            "          </div>\n"
            "        </nav>\n"
            "      </aside>\n"
            "\n"
            "      <div className=\"sidebar-user\">\n"
            "        <div className=\"user-avatar\">JD</div>\n"
            "      <div className=\"main-content\">\n"
            "        <span>Main</span>\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

        repaired = _repair_componentized_orphaned_parent_family_children(source)

        self.assertIn("</nav>\n      <div className=\"sidebar-user\">", repaired)
        self.assertIn("</div>\n      </aside>\n      <div className=\"main-content\">", repaired)
        self.assertNotIn("</aside>\n\n      <div className=\"sidebar-user\">", repaired)
        self._assert_jsx_return_would_parse(repaired)

    def test_ensure_componentized_workspace_support_repairs_orphaned_panel_children_after_section_close(self):
        source = (
            "export default function App() {\n"
            "  return (\n"
            "    <div className=\"workspace-shell\">\n"
            "      <section className=\"panel-shell\">\n"
            "        <nav className=\"panel-nav\">\n"
            "          <div className=\"panel-group\">\n"
            "            <div className=\"panel-link\">Home</div>\n"
            "          </div>\n"
            "          <div className=\"panel-group\">\n"
            "            <div className=\"panel-link\">Reports</div>\n"
            "          </div>\n"
            "        </nav>\n"
            "      </section>\n"
            "\n"
            "      <div className=\"panel-footer\">\n"
            "        <span>Support</span>\n"
            "\n"
            "      <main className=\"workspace-content\">\n"
            "        <h1>Overview</h1>\n"
            "      </main>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

        repaired = _repair_componentized_orphaned_parent_family_children(source)

        self.assertIn("</nav>\n      <div className=\"panel-footer\">", repaired)
        self.assertIn("</div>\n      </section>\n      <main className=\"workspace-content\">", repaired)
        self.assertNotIn("</section>\n\n      <div className=\"panel-footer\">", repaired)
        self._assert_jsx_return_would_parse(repaired)

    def test_ensure_componentized_workspace_support_repairs_inline_mismatched_closing_tags(self):
        code_dir = _case_dir("componentized-runtime-inline-closing-tag-mismatch")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "Editor.tsx").write_text(
                "export default function Editor() {\n"
                "  return (\n"
                "    <div className=\"editor-shell\">\n"
                "      <aside className=\"sidebar\">\n"
                "        <div className=\"toolbar\">Blocks</aside>\n"
                "      <main className=\"canvas\">\n"
                "        <section className=\"editor-frame\">\n"
                "          <div className=\"surface\">Draft</section>\n"
                "        </main>\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "components" / "Editor.tsx").read_text(encoding="utf-8")
            self.assertIn('<div className="toolbar">Blocks</div></aside>', source)
            self.assertIn('<div className="surface">Draft</div></section>', source)
            self.assertIn("</main>", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_merges_comment_filename_labels(self):
        code_dir = _case_dir("componentized-runtime-comment-filename-label")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "/* Inline StatsBand component for */\n"
                "App.tsx\n"
                "const StatsBand = () => <section />;\n"
                "export default StatsBand;\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("/* Inline StatsBand component for App.tsx */", source)
            self.assertNotIn("\nApp.tsx\n", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_comment_tail_split_identifiers(self):
        code_dir = _case_dir("componentized-runtime-comment-tail-split")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  /* entry.target.class */\n"
                "List.remove('is-visible');\n"
                "  return <div />;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("entry.target.classList.remove('is-visible');", source)
            self.assertNotIn("/* entry.target.class */", source)
            self.assertNotIn("\nList.remove('is-visible');", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_extracts_css_tails_from_tsx(self):
        code_dir = _case_dir("componentized-runtime-extract-css-tail")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "function App() {\n"
                "  return <div className=\"shell\">Hello</div>;\n"
                "}\n"
                ".shell {\n"
                "  min-height: 100vh;\n"
                "}\n"
                "export default App;\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            index_css = (code_dir / "src" / "index.css").read_text(encoding="utf-8")
            self.assertNotIn(".shell {", app_source)
            self.assertIn("export default App;", app_source)
            self.assertIn(".shell {", index_css)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_jsx_block_comment_bleed_in_map(self):
        code_dir = _case_dir("componentized-runtime-jsx-map-comment-bleed")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "Topbar.tsx").write_text(
                "import React from 'react';\n"
                "const formatCurrency = (value: number) => `$${value.toFixed(2)}`;\n"
                "export default function Topbar() {\n"
                "  const tickerData = [{ symbol: 'SPY', price: 500.23, change: 0.85, isPositive: true }];\n"
                "  return (    <div className=\"topbar-fixed\">      <div className=\"ticker-strip\">        {tickerData.concat(tickerData).map((ticker, index) => ( /* Duplicate for seamless scroll            <div key={index} className=\"ticker-card\">              <span className=\"symbol\">{ticker.symbol}</span>              <span className=\"price space-mono\">{format */\n"
                "Currency(ticker.price)}</span>              <span className={`delta space-mono ${ticker.isPositive ? 'delta-positive' : 'delta-negative'}`}>{ticker.change}%</span>            </div>          ))}      </div>    </div>  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            topbar_source = (code_dir / "src" / "components" / "Topbar.tsx").read_text(encoding="utf-8")
            self.assertIn("/* Duplicate for seamless scroll */", topbar_source)
            self.assertIn("{formatCurrency(ticker.price)}", topbar_source)
            self.assertNotIn("{format */", topbar_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_normalizes_dominant_field_aliases(self):
        code_dir = _case_dir("componentized-runtime-field-aliases")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "DashboardLayout.tsx").write_text(
                "interface TickerData { symbol: string; change: number; changePercent: number; positive: boolean; }\n"
                "const initialTickers: TickerData[] = [\n"
                "  { symbol: 'AAPL', change: 1.29, changePercent: 0.74, positive: true },\n"
                "  { symbol: 'AMZN', change: -1.43, change24hPercent: -0.79, positive: false },\n"
                "];\n"
                "export default function DashboardLayout() {\n"
                "  return <div>{initialTickers.map((ticker) => <span key={ticker.symbol}>{ticker.changePercent.toFixed(2)}</span>)}</div>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            layout_source = (code_dir / "src" / "components" / "DashboardLayout.tsx").read_text(encoding="utf-8")
            self.assertIn("changePercent: -0.79", layout_source)
            self.assertNotIn("change24hPercent", layout_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_backfills_missing_local_css_imports(self):
        code_dir = _case_dir("componentized-runtime-missing-css-import")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "import './style.css';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() { return <div>Hello</div>; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            self.assertTrue((code_dir / "src" / "style.css").exists())
            style_css = (code_dir / "src" / "style.css").read_text(encoding="utf-8")
            self.assertIn("fallback stylesheet", style_css)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_backfills_missing_utility_classes(self):
        code_dir = _case_dir("componentized-runtime-utility-backfill")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <div className=\"font-display text-color-primary-text text-h3 top-1/2 -translate-y-1/2\">Desk</div>;\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "base.css").write_text(
                ":root { --font-display: 'Space Grotesk', 'Inter', sans-serif; --color-primary-text: #f4f8fc; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            base_css = (code_dir / "src" / "base.css").read_text(encoding="utf-8")
            self.assertIn(".font-display", base_css)
            self.assertIn(".text-color-primary-text", base_css)
            self.assertIn(".text-h3", base_css)
            self.assertIn(".top-1\\/2", base_css)
            self.assertIn(".-translate-y-1\\/2", base_css)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_normalizes_index_html_shell(self):
        code_dir = _case_dir("componentized-runtime-index-html")
        try:
            (code_dir / "package.json").write_text('{"name":"demo-app"}\n', encoding="utf-8")
            (code_dir / "index.html").write_text(
                "<!doctype html>\n"
                "<html lang=\"en\">\n"
                "  <head>\n"
                "    <meta charset=\"UTF-8\" />\n"
                "    <title>Stock Trading Dashboard</title>\n"
                "    <link rel=\"stylesheet\" href=\"/src/base.css\">\n"
                "    <style>.noise-overlay{background-image:url('data:image/svg+xml,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'200\\'' numOctaves=\\'4\\'></svg>');}</style>\n"
                "  </head>\n"
                "  <body>\n"
                "    <div id=\"root\"></div>\n"
                "    <div class=\"noise-overlay\"></div>\n"
                "    <script type=\"module\" src=\"/src/main.tsx\"></script>\n"
                "  </body>\n"
                "</html>\n",
                encoding="utf-8",
            )
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() { return <div>Hello</div>; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            index_html = (code_dir / "index.html").read_text(encoding="utf-8")
            self.assertIn("<title>Stock Trading Dashboard</title>", index_html)
            self.assertNotIn("noise-overlay", index_html)
            self.assertNotIn("/src/base.css", index_html)
            self.assertIn('<div id="root"></div>', index_html)
            self.assertIn('<script type="module" src="/src/main.tsx"></script>', index_html)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_stage_componentized_design_assets_copies_assets_into_public_workspace(self):
        version_dir = _case_dir("componentized-runtime-assets")
        try:
            (version_dir / "assets").mkdir(parents=True)
            src = version_dir / "assets" / "hero_background.png"
            src.write_bytes(b"fakepng")

            staged = stage_componentized_design_assets(
                version_dir,
                [
                    {
                        "key": "hero_background",
                        "purpose": "Hero image",
                        "local_path": str(src),
                    }
                ],
            )

            self.assertEqual(staged[0]["path"], "generated-assets/hero_background.png")
            self.assertTrue((version_dir / "code" / "public" / "generated-assets" / "hero_background.png").exists())
        finally:
            shutil.rmtree(version_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_aliases_missing_generated_asset_names(self):
        code_dir = _case_dir("componentized-runtime-generated-asset-aliases")
        try:
            (code_dir / "public" / "generated-assets").mkdir(parents=True)
            (code_dir / "public" / "generated-assets" / "hero_background.png").write_bytes(b"hero")
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <img src='/generated-assets/world_map.png' alt='World Map' />;\n"
                "}\n",
                encoding="utf-8",
            )

            result = ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("generated-assets/world_map.png", app_source)
            self.assertNotIn("/generated-assets/world_map.png", app_source)
            alias_path = code_dir / "public" / "generated-assets" / "world_map.png"
            self.assertTrue(alias_path.exists())
            self.assertIn("public/generated-assets/world_map.png", result["created_files"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_creates_svg_placeholders_and_game_polish_guard(self):
        code_dir = _case_dir("componentized-runtime-game-svg-placeholder")
        try:
            (code_dir / "public" / "generated-assets").mkdir(parents=True)
            (code_dir / "public" / "generated-assets" / "hero_background.png").write_bytes(b"hero")
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\n"
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <section className='hero-cinematic'>\n"
                "      <div className='hero-content'>\n"
                "        <div className='scroll-indicator'><span className='scroll-indicator-text'>Scroll</span></div>\n"
                "        <div className='pokemon-name'>Pikachu</div>\n"
                "      </div>\n"
                "      <img src='generated-assets/icon_ultrahand.svg' alt='Ability icon' />\n"
                "    </section>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            result = ensure_componentized_workspace_support(code_dir, ui_archetype="game")

            svg_path = code_dir / "public" / "generated-assets" / "icon_ultrahand.svg"
            self.assertTrue(svg_path.exists())
            self.assertIn("<svg", svg_path.read_text(encoding="utf-8"))
            self.assertIn("public/generated-assets/icon_ultrahand.svg", result["created_files"])
            polish_guard = (code_dir / "src" / "polish-guard.css").read_text(encoding="utf-8")
            self.assertIn(".pokemon-name", polish_guard)
            self.assertIn(".scroll-indicator", polish_guard)
            self.assertIn("padding-bottom: clamp(5.5rem, 10vh, 7.5rem)", polish_guard)
            self.assertIn("display: inline-flex", polish_guard)
            self.assertIn(".fade-up-section", polish_guard)
            self.assertFalse((code_dir / "src" / "polish-guard.ts").exists())
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_prefers_showcase_aliases_for_game_badges(self):
        code_dir = _case_dir("componentized-runtime-game-badge-alias")
        try:
            (code_dir / "public" / "generated-assets").mkdir(parents=True)
            (code_dir / "public" / "generated-assets" / "character_charizard_portrait.png").write_bytes(b"charizard")
            (code_dir / "public" / "generated-assets" / "evolution_showcase_illustration.png").write_bytes(b"showcase")
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <img src='generated-assets/badge_boulder.png' alt='Boulder badge' />;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            alias_path = code_dir / "public" / "generated-assets" / "badge_boulder.png"
            self.assertTrue(alias_path.exists())
            self.assertEqual(alias_path.read_bytes(), b"showcase")
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_rewrites_remote_badge_urls_to_local_svg_placeholders(self):
        code_dir = _case_dir("componentized-runtime-remote-badge-urls")
        try:
            (code_dir / "public" / "generated-assets").mkdir(parents=True)
            (code_dir / "public" / "generated-assets" / "badge_collection.png").write_bytes(b"collection")
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "GymBadgeCollection.tsx").write_text(
                "const badges = [\n"
                "  { name: 'Boulder Badge', image: 'https://archives.bulbagarden.net/media/upload/d/d4/Boulder_Badge.png' },\n"
                "  { name: 'Cascade Badge', image: 'https://archives.bulbagarden.net/media/upload/c/c9/Cascade_Badge.png' },\n"
                "];\n"
                "export default function GymBadgeCollection() { return <div>{badges.length}</div>; }\n",
                encoding="utf-8",
            )

            result = ensure_componentized_workspace_support(code_dir, ui_archetype="game")

            source = (code_dir / "src" / "GymBadgeCollection.tsx").read_text(encoding="utf-8")
            self.assertIn("generated-assets/badge_boulder.svg", source)
            self.assertIn("generated-assets/badge_cascade.svg", source)
            self.assertNotIn("bulbagarden.net", source)
            self.assertTrue((code_dir / "public" / "generated-assets" / "badge_boulder.svg").exists())
            self.assertTrue((code_dir / "public" / "generated-assets" / "badge_cascade.svg").exists())
            self.assertIn("public/generated-assets/badge_boulder.svg", result["created_files"])
            self.assertIn("public/generated-assets/badge_cascade.svg", result["created_files"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_rewrites_remote_game_image_fields_to_local_placeholders(self):
        code_dir = _case_dir("componentized-runtime-remote-game-images")
        try:
            (code_dir / "public" / "generated-assets").mkdir(parents=True)
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "CharacterCards.tsx").write_text(
                "const cards = [\n"
                "  { name: 'Master Chief', image: 'https://via.placeholder.com/320x400/1a1e22/e6e8eb?text=Master+Chief' },\n"
                "  { name: 'Cortana', image: 'https://images.unsplash.com/photo-12345?w=600&q=80' },\n"
                "];\n"
                "export default function CharacterCards() { return <div>{cards.length}</div>; }\n",
                encoding="utf-8",
            )

            result = ensure_componentized_workspace_support(code_dir, ui_archetype="game")

            source = (code_dir / "src" / "CharacterCards.tsx").read_text(encoding="utf-8")
            self.assertNotIn("via.placeholder.com", source)
            self.assertNotIn("images.unsplash.com", source)
            self.assertIn("generated-assets/master_chief.svg", source)
            self.assertIn("generated-assets/cortana.svg", source)
            self.assertTrue((code_dir / "public" / "generated-assets" / "master_chief.svg").exists())
            self.assertTrue((code_dir / "public" / "generated-assets" / "cortana.svg").exists())
            self.assertIn("public/generated-assets/master_chief.svg", result["created_files"])
            self.assertIn("public/generated-assets/cortana.svg", result["created_files"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_rewrites_remote_ecommerce_images_to_local_placeholders(self):
        code_dir = _case_dir("componentized-runtime-remote-ecommerce-images")
        try:
            (code_dir / "public" / "generated-assets").mkdir(parents=True)
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "const products = [\n"
                "  { id: 1, name: 'Ceramic Vase', image: 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=600&q=80' },\n"
                "];\n"
                "export default function App() {\n"
                "  return <img src=\"https://images.unsplash.com/photo-1505740420928-5e560c06f2e0?q=80&w=2070\" alt=\"Limited Editions\" />;\n"
                "}\n",
                encoding="utf-8",
            )

            result = ensure_componentized_workspace_support(code_dir, ui_archetype="ecommerce")

            source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertNotIn("images.unsplash.com", source)
            self.assertIn("generated-assets/ceramic_vase.svg", source)
            self.assertIn("generated-assets/limited_editions.svg", source)
            self.assertTrue((code_dir / "public" / "generated-assets" / "ceramic_vase.svg").exists())
            self.assertTrue((code_dir / "public" / "generated-assets" / "limited_editions.svg").exists())
            self.assertIn("public/generated-assets/ceramic_vase.svg", result["created_files"])
            self.assertIn("public/generated-assets/limited_editions.svg", result["created_files"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_rewrites_remote_portfolio_images_to_local_placeholders(self):
        code_dir = _case_dir("componentized-runtime-remote-portfolio-images")
        try:
            (code_dir / "public" / "generated-assets").mkdir(parents=True)
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <section>\n"
                "      <img src=\"https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&q=80\" alt=\"Alex Mercer\" />\n"
                "      <div style={{ backgroundImage: 'url(https://via.placeholder.com/1200x800/101114/e5e7eb?text=Skills+Illustration)' }} />\n"
                "    </section>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            result = ensure_componentized_workspace_support(code_dir, ui_archetype="portfolio")

            source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertNotIn("images.unsplash.com", source)
            self.assertNotIn("via.placeholder.com", source)
            self.assertIn("generated-assets/alex_mercer.svg", source)
            self.assertIn("url(generated-assets/", source)
            self.assertTrue((code_dir / "public" / "generated-assets" / "alex_mercer.svg").exists())
            self.assertIn("public/generated-assets/alex_mercer.svg", result["created_files"])
            self.assertTrue(
                any(path.startswith("public/generated-assets/") and path.endswith(".svg") and "alex_mercer.svg" not in path for path in result["created_files"])
            )
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_build_design_context_for_componentized_apps_forbids_invented_asset_names(self):
        version_dir = _case_dir("componentized-design-context")
        try:
            hero = version_dir / "hero_background.png"
            hero.write_bytes(b"hero")
            context = build_design_context(
                version_dir=version_dir,
                design_assets=[
                    {
                        "key": "hero_background",
                        "purpose": "hero image",
                        "local_path": str(hero),
                    }
                ],
                project_id=99,
                version=1,
                scaffold_mode="componentized_app",
            )

            self.assertIn("Do not invent additional generated-assets filenames", context)
            self.assertIn("reuse one of the listed asset paths", context)
        finally:
            shutil.rmtree(version_dir, ignore_errors=True)

    def test_density_audit_flags_sparse_dashboard_shells(self):
        code_dir = _case_dir("componentized-quality-density")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <main>\n"
                "      <section>\n"
                "        <h1>Dashboard</h1>\n"
                "        <div>Metric 1</div>\n"
                "        <div>$10,000</div>\n"
                "      </section>\n"
                "    </main>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            audit = evaluate_componentized_density(code_dir, ui_archetype="dashboard")

            self.assertFalse(audit["passed"])
            weakness_codes = {item["code"] for item in audit["weaknesses"]}
            self.assertIn("kpi_sparse", weakness_codes)
            self.assertIn("table_sparse", weakness_codes)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_density_audit_requires_multiple_support_modules_for_strict_dashboards(self):
        code_dir = _case_dir("componentized-quality-support-modules")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "base.css").write_text(
                "body { font-family: Inter, sans-serif; }\n"
                ".kpi-value, .price { font-variant-numeric: tabular-nums; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "PerformanceChart.tsx").write_text(
                "const performanceSeries = [\n"
                "  { x: 'Mon', y: 182441 },\n"
                "  { x: 'Tue', y: 183206 },\n"
                "  { x: 'Wed', y: 183998 },\n"
                "  { x: 'Thu', y: 184221 },\n"
                "  { x: 'Fri', y: 184928 },\n"
                "  { x: 'After Hours', y: 185104 },\n"
                "  { x: 'Open', y: 184762 },\n"
                "];\n"
                "export default function PerformanceChart() {\n"
                "  const selectedRange = '1M';\n"
                "  return (\n"
                "    <section className='chart card'>\n"
                "      <h2>Portfolio Performance Chart</h2>\n"
                "      <p>Updated 5 minutes ago vs. prior close.</p>\n"
                "      <div className='range-group'>\n"
                "        <button onClick={() => null}>1D</button><button onClick={() => null}>1W</button><button onClick={() => null}>{selectedRange}</button><button onClick={() => null}>YTD</button>\n"
                "      </div>\n"
                "      <svg viewBox='0 0 700 320'>{performanceSeries.map((point) => <text key={point.x}>{point.x}:{point.y}</text>)}</svg>\n"
                "    </section>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "import PerformanceChart from './components/PerformanceChart';\n"
                "const kpis = [\n"
                "  { label: 'Portfolio Value', value: '$184,928.43', delta: '+2.4%', sparkline: [12, 14, 13, 15, 17, 18, 19] },\n"
                "  { label: 'Day P&L', value: '+$2,184.12', delta: '+1.3%', sparkline: [4, 5, 6, 7, 8, 8, 9] },\n"
                "  { label: 'Cash Balance', value: '$18,441.09', delta: '-0.6%', sparkline: [7, 6, 6, 5, 5, 4, 4] },\n"
                "  { label: 'Win Rate', value: '63.8%', delta: '+4.2%', sparkline: [42, 48, 51, 56, 58, 61, 64] },\n"
                "];\n"
                "const holdings = [\n"
                "  { symbol: 'NVDA', name: 'NVIDIA Corporation', price: '$906.18', value: '$28,114.82', shares: '31.03', status: 'Active' },\n"
                "  { symbol: 'MSFT', name: 'Microsoft Corporation', price: '$418.22', value: '$22,190.14', shares: '53.06', status: 'Active' },\n"
                "  { symbol: 'AMZN', name: 'Amazon.com Inc.', price: '$178.91', value: '$16,997.32', shares: '94.99', status: 'Buy' },\n"
                "  { symbol: 'AVGO', name: 'Broadcom Inc.', price: '$1,322.18', value: '$15,866.16', shares: '12.00', status: 'Hold' },\n"
                "  { symbol: 'TSM', name: 'Taiwan Semiconductor', price: '$164.55', value: '$12,670.35', shares: '77.00', status: 'Active' },\n"
                "  { symbol: 'SHOP', name: 'Shopify Inc.', price: '$84.36', value: '$8,604.72', shares: '102.00', status: 'Buy' },\n"
                "];\n"
                "const watchlist = [\n"
                "  { symbol: 'META', price: '$512.42', change: '+1.8%', thesis: 'Ad momentum holding into Q2' },\n"
                "  { symbol: 'ASML', price: '$947.10', change: '+0.9%', thesis: 'EUV order book stays firm' },\n"
                "  { symbol: 'SNOW', price: '$188.33', change: '-0.7%', thesis: 'Consumption trends stabilizing' },\n"
                "  { symbol: 'TTD', price: '$87.64', change: '+2.1%', thesis: 'CTV budgets firming up' },\n"
                "];\n"
                "export default function App() {\n"
                "  return (\n"
                "    <main>\n"
                "      <section className='hero card'>\n"
                "        <h1>Atlas Capital Terminal</h1>\n"
                "        <p>Cross-asset overview with refreshed pricing, conviction notes, and intraday positioning context for the growth sleeve.</p>\n"
                "        <div className='controls'>\n"
                "          <button>1D</button><button>1W</button><button>1M</button><button>YTD</button>\n"
                "          <button>Sort by Momentum</button>\n"
                "        </div>\n"
                "      </section>\n"
                "      <section className='kpi-grid'>\n"
                "        {kpis.map((item) => <article key={item.label} className='card kpi-card'><span>{item.label}</span><strong className='kpi-value'>{item.value}</strong><em>{item.delta}</em><small>{item.sparkline.join(', ')}</small></article>)}\n"
                "      </section>\n"
                "      <PerformanceChart />\n"
                "      <section className='table card'>\n"
                "        <h2>Core Holdings</h2>\n"
                "        <p>Showing 6 of 6 active positions in the momentum sleeve.</p>\n"
                "        <table><thead><tr><th>Symbol</th><th>Name</th><th>Price</th><th>Value</th><th>Shares</th><th>Status</th></tr></thead><tbody>{holdings.map((row) => <tr key={row.symbol}><td>{row.symbol}</td><td>{row.name}</td><td className='price'>{row.price}</td><td>{row.value}</td><td>{row.shares}</td><td>{row.status}</td></tr>)}</tbody></table>\n"
                "      </section>\n"
                "      <section className='watchlist card'>\n"
                "        <h2>Market Movers Watchlist</h2>\n"
                "        <p>Names flagged by the desk for near-term earnings and rotation risk.</p>\n"
                "        {watchlist.map((item) => <article key={item.symbol}><h3>{item.symbol}</h3><div className='price'>{item.price}</div><div>{item.change}</div><p>{item.thesis}</p></article>)}\n"
                "      </section>\n"
                "    </main>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            audit = evaluate_componentized_density(code_dir, ui_archetype="dashboard")

            self.assertFalse(audit["passed"])
            self.assertGreaterEqual(audit["score"], 60)
            self.assertEqual(audit["metrics"]["support_module_count"], 1)
            weakness_codes = {item["code"] for item in audit["weaknesses"]}
            self.assertIn("side_panel_thin", weakness_codes)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_density_audit_uses_fanpage_heuristics_for_game_archives(self):
        code_dir = _case_dir("componentized-quality-fanpage-density")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "const featuredCharacters = [\n"
                "  { name: 'Cloud Strife', image: '/generated-assets/cloud.png', role: 'Ex-SOLDIER', stats: { hp: 1783, attack: 126, defense: 91, speed: 104 } },\n"
                "  { name: 'Tifa Lockhart', image: '/generated-assets/tifa.png', role: 'Monk', stats: { hp: 1640, attack: 118, defense: 88, speed: 112 } },\n"
                "  { name: 'Barret Wallace', image: '/generated-assets/barret.png', role: 'Heavy Gunner', stats: { hp: 1938, attack: 132, defense: 104, speed: 72 } },\n"
                "];\n"
                "export default function App() {\n"
                "  return (\n"
                "    <main>\n"
                "      <section id='hero'>\n"
                "        <img src='/generated-assets/hero_midgar.png' alt='Midgar hero backdrop' />\n"
                "        <h1>Legends of Midgar</h1>\n"
                "      </section>\n"
                "      <section id='characters'>\n"
                "        <h2>Character Dossiers</h2>\n"
                "        {featuredCharacters.map((character) => <article key={character.name} className='character-card'><h3>{character.name}</h3><div>HP</div><div>ATK</div><div>DEF</div><div>SPD</div></article>)}\n"
                "      </section>\n"
                "      <section id='arsenal'><h2>Weapons Archive</h2><div>Buster Sword</div><div>Gatling Gun</div></section>\n"
                "      <section id='world'><h2>World Map</h2><div>Midgar</div><div>Junon</div></section>\n"
                "      <section id='lore'><h2>Lore Chronicle</h2><p>The lifestream remembers every chapter.</p></section>\n"
                "    </main>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            audit = evaluate_componentized_density(code_dir, ui_archetype="game_ff7")

            self.assertTrue(audit["passed"])
            weakness_codes = {item["code"] for item in audit["weaknesses"]}
            self.assertNotIn("kpi_sparse", weakness_codes)
            self.assertNotIn("chart_missing", weakness_codes)
            self.assertNotIn("table_sparse", weakness_codes)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_density_audit_counts_page_embedded_svg_charts_as_chart_regions(self):
        code_dir = _case_dir("componentized-quality-page-chart-density")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "const chartData = [\n"
                "  { x: 'Mon', open: 101, high: 109, low: 98, close: 105 },\n"
                "  { x: 'Tue', open: 105, high: 111, low: 103, close: 109 },\n"
                "  { x: 'Wed', open: 109, high: 114, low: 107, close: 112 },\n"
                "  { x: 'Thu', open: 112, high: 118, low: 110, close: 116 },\n"
                "  { x: 'Fri', open: 116, high: 121, low: 114, close: 119 },\n"
                "  { x: 'AH', open: 119, high: 123, low: 118, close: 121 },\n"
                "  { x: 'Open', open: 121, high: 124, low: 120, close: 122 },\n"
                "];\n"
                "export default function App() {\n"
                "  return (\n"
                "    <main>\n"
                "      <section className='chart-panel'>\n"
                "        <h2 className='chart-title'>AAPL Candlestick Chart</h2>\n"
                "        <svg className='candlestick-chart' viewBox='0 0 800 300'>{chartData.map((point) => <text key={point.x} className='axis-label'>{point.x}:{point.open}:{point.high}:{point.low}:{point.close}</text>)}</svg>\n"
                "      </section>\n"
                "    </main>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            audit = evaluate_componentized_density(code_dir, ui_archetype="dashboard")

            self.assertGreaterEqual(audit["metrics"]["chart_regions"], 1)
            weakness_codes = {item["code"] for item in audit["weaknesses"]}
            self.assertNotIn("chart_missing", weakness_codes)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_semantic_evaluation_flags_placeholder_content(self):
        code_dir = _case_dir("componentized-quality-semantic")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <main>\n"
                "      <section>\n"
                "        <h2>Chart Title</h2>\n"
                "        <div>Metric 1</div>\n"
                "        <div>$10,000</div>\n"
                "        <div>User 1</div>\n"
                "      </section>\n"
                "    </main>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            evaluation = evaluate_componentized_semantic_completeness(code_dir, ui_archetype="fintech")

            self.assertFalse(evaluation["passed"])
            self.assertEqual(evaluation["threshold"], 70)
            self.assertLess(evaluation["score"], 60)
            self.assertIn("Placeholder content is still visible in the app copy.", evaluation["findings"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_semantic_evaluation_flags_generic_dense_shell_copy(self):
        code_dir = _case_dir("componentized-quality-semantic-generic-dense-shell")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <main>\n"
                "      <header><h1>Portfolio Overview</h1></header>\n"
                "      <section><div>Revenue at Risk</div><div>$124,832.50</div></section>\n"
                "      <table><tbody><tr><td>North Hub</td><td><button>View</button></td></tr><tr><td>South Hub</td><td><button>Details</button></td></tr><tr><td>West Hub</td><td><button>View</button></td></tr></tbody></table>\n"
                "      <aside><section><h2>Watchlist</h2><p>Flagged item</p></section><section><h2>Recent Updates</h2><p>Status note posted.</p></section></aside>\n"
                "    </main>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            evaluation = evaluate_componentized_semantic_completeness(code_dir, ui_archetype="dashboard")

            self.assertFalse(evaluation["passed"])
            self.assertLess(evaluation["dimensions"]["placeholder_text"]["score"], 15)
            self.assertLess(evaluation["dimensions"]["contextual_labeling"]["score"], 10)
            self.assertIn(
                "Dense-shell copy still uses template titles or repeated generic row actions.",
                evaluation["findings"],
            )
            self.assertIn(
                "Support-rail modules still use generic labels instead of product-specific context.",
                evaluation["findings"],
            )
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_semantic_evaluation_does_not_require_kpis_for_game_archives(self):
        code_dir = _case_dir("componentized-quality-fanpage-semantic")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "const companions = [\n"
                "  { name: 'Agumon', image: '/generated-assets/agumon.png', type: 'Vaccine', role: 'Partner Digimon' },\n"
                "  { name: 'Gabumon', image: '/generated-assets/gabumon.png', type: 'Data', role: 'Loyal Scout' },\n"
                "  { name: 'Tai Kamiya', image: '/generated-assets/tai.png', type: 'Human', role: 'DigiDestined Leader' },\n"
                "];\n"
                "export default function App() {\n"
                "  return (\n"
                "    <main>\n"
                "      <section><h1>Digital World Compendium</h1><p>Archive Edition</p></section>\n"
                "      <section><h2>Character Profiles</h2>{companions.map((entry) => <article key={entry.name}><h3>{entry.name}</h3><p>{entry.role}</p><span>{entry.type}</span></article>)}</section>\n"
                "      <section><h2>Evolution Gallery</h2><p>Agumon, Greymon, MetalGreymon.</p></section>\n"
                "      <section><h2>World Map</h2><p>File Island, Server Continent, Primary Village.</p></section>\n"
                "      <section><h2>Lore Archive</h2><p>The Digital World expands with every data storm.</p></section>\n"
                "    </main>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            evaluation = evaluate_componentized_semantic_completeness(code_dir, ui_archetype="game")

            self.assertTrue(evaluation["passed"])
            self.assertEqual(evaluation["dimensions"]["metric_completeness"]["score"], 10)
            self.assertNotIn("The app is missing a convincing KPI layer.", evaluation["findings"])
            self.assertNotIn("The app needs real timestamps or dates.", evaluation["findings"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_multi_file_evaluation_targets_only_weak_content_files(self):
        code_dir = _case_dir("componentized-quality-multifile")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "data").mkdir(parents=True)
            (code_dir / "src" / "components" / "KPICards.tsx").write_text(
                "export default function KPICards() {\n"
                "  return (\n"
                "    <section>\n"
                "      <div>Portfolio Value</div>\n"
                "      <div>$127,483.92</div>\n"
                "      <div>Day P&L</div>\n"
                "      <div>+$1,247.83</div>\n"
                "    </section>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "data" / "metrics.ts").write_text(
                "export const metrics = [\n"
                "  { label: 'Metric 1', value: '$10,000' },\n"
                "  { label: 'Metric 2', value: '$20,000' },\n"
                "];\n",
                encoding="utf-8",
            )

            evaluation = evaluate_componentized_multi_file_completeness(code_dir, ui_archetype="fintech")

            weak_paths = {item["path"] for item in evaluation["weak_files"]}
            strong_paths = {item["path"] for item in evaluation["strong_files"]}
            self.assertEqual(evaluation["threshold"], 70)
            self.assertIn("src/data/metrics.ts", weak_paths)
            self.assertIn("src/components/KPICards.tsx", strong_paths)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_multi_file_evaluation_does_not_penalize_prop_driven_feed_components(self):
        code_dir = _case_dir("componentized-quality-prop-driven-feed")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "const initialActivities = [\n"
                "  { id: 'evt-201', type: 'trade', text: 'Bought 8 shares of NVDA at $1,042.18', time: '14 minutes ago' },\n"
                "  { id: 'evt-202', type: 'alert', text: 'MSFT crossed the 50-day moving average', time: 'Mar 13, 2026' },\n"
                "];\n"
                "export default function App() { return null; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "ActivityFeed.tsx").write_text(
                "interface ActivityItem { id: string; type: 'trade' | 'alert'; text: string; time: string; }\n"
                "interface ActivityFeedProps { activities: ActivityItem[]; }\n"
                "export default function ActivityFeed({ activities }: ActivityFeedProps) {\n"
                "  return <section className=\"activity-feed-card\"><h2>Recent Activity</h2>{activities.map((activity) => <div key={activity.id}>{activity.text}</div>)}</section>;\n"
                "}\n",
                encoding="utf-8",
            )

            evaluation = evaluate_componentized_multi_file_completeness(code_dir, ui_archetype="fintech")

            weak_paths = {item["path"] for item in evaluation["weak_files"]}
            strong_paths = {item["path"] for item in evaluation["strong_files"]}
            self.assertIn("src/components/ActivityFeed.tsx", strong_paths)
            self.assertNotIn("src/components/ActivityFeed.tsx", weak_paths)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_multi_file_evaluation_flags_fintech_tables_missing_trend_cues(self):
        code_dir = _case_dir("componentized-quality-fintech-table-trends")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "PortfolioBreakdownTable.tsx").write_text(
                "const holdings = [\n"
                "  { symbol: 'AAPL', price: 184.28, change: 1.24, holdings: 42, value: 7739.76, updated: '5 min ago' },\n"
                "  { symbol: 'NVDA', price: 1042.19, change: -0.88, holdings: 8, value: 8337.52, updated: 'Mar 14, 2026' },\n"
                "];\n"
                "export default function PortfolioBreakdownTable() {\n"
                "  return <table><tbody>{holdings.map((item) => <tr key={item.symbol}><td>{item.symbol}</td><td>{item.price}</td><td>{item.change}</td><td>{item.updated}</td></tr>)}</tbody></table>;\n"
                "}\n",
                encoding="utf-8",
            )

            evaluation = evaluate_componentized_multi_file_completeness(code_dir, ui_archetype="fintech")

            weak_report = next(item for item in evaluation["weak_files"] if item["path"] == "src/components/PortfolioBreakdownTable.tsx")
            self.assertIn("table_trend_missing", weak_report["weakness_codes"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_multi_file_evaluation_flags_generic_dense_shell_table_copy(self):
        code_dir = _case_dir("componentized-quality-dashboard-table-template-copy")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "QueueTable.tsx").write_text(
                "const rows = [\n"
                "  { name: 'North Hub', status: 'Open', updated: '2 hours ago' },\n"
                "  { name: 'South Hub', status: 'Pending', updated: 'Mar 14, 2026' },\n"
                "  { name: 'West Hub', status: 'Escalated', updated: '5 min ago' },\n"
                "];\n"
                "export default function QueueTable() {\n"
                "  return <table><tbody>{rows.map((item) => <tr key={item.name}><td>{item.name}</td><td>{item.status}</td><td>{item.updated}</td><td><button>View</button></td></tr>)}</tbody></table>;\n"
                "}\n",
                encoding="utf-8",
            )

            evaluation = evaluate_componentized_multi_file_completeness(code_dir, ui_archetype="dashboard")

            weak_report = next(item for item in evaluation["weak_files"] if item["path"] == "src/components/QueueTable.tsx")
            self.assertIn("placeholder_text", weak_report["weakness_codes"])
            self.assertIn("content_authenticity", weak_report["weakness_codes"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_multi_file_evaluation_accepts_fintech_tables_with_explicit_sparklines(self):
        code_dir = _case_dir("componentized-quality-fintech-table-sparkline")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "PortfolioBreakdownTable.tsx").write_text(
                "const holdings = [\n"
                "  { symbol: 'AAPL', price: 184.28, change: 1.24, holdings: 42, value: 7739.76, updated: '5 min ago', sparkline: 'M0 10 L12 8 L24 9 L36 6 L48 4 L60 5 L72 3' },\n"
                "  { symbol: 'NVDA', price: 1042.19, change: -0.88, holdings: 8, value: 8337.52, updated: 'Mar 14, 2026', sparkline: 'M0 6 L12 7 L24 8 L36 9 L48 11 L60 12 L72 13' },\n"
                "];\n"
                "export default function PortfolioBreakdownTable() {\n"
                "  return <table><tbody>{holdings.map((item) => <tr key={item.symbol}><td><span>{item.symbol}</span><svg className=\"row-sparkline\" viewBox=\"0 0 72 18\"><path d={item.sparkline} /></svg></td><td>{item.price}</td><td>{item.change}</td><td>{item.updated}</td></tr>)}</tbody></table>;\n"
                "}\n",
                encoding="utf-8",
            )

            evaluation = evaluate_componentized_multi_file_completeness(code_dir, ui_archetype="fintech")

            report = next(item for item in evaluation["strong_files"] if item["path"] == "src/components/PortfolioBreakdownTable.tsx")
            self.assertNotIn("table_trend_missing", report["weakness_codes"])
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_select_componentized_refinement_scope_includes_tables_for_table_trend_missing(self):
        code_dir = _case_dir("componentized-quality-refinement-table-trend")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text("export default function App() { return <div />; }\n", encoding="utf-8")
            (code_dir / "src" / "components" / "PortfolioBreakdownTable.tsx").write_text(
                "export default function PortfolioBreakdownTable() { return <table><tbody><tr><td>AAPL</td></tr></tbody></table>; }\n",
                encoding="utf-8",
            )

            scope = select_componentized_refinement_scope(
                code_dir,
                ["table_trend_missing"],
                weak_file_paths=["src/components/PortfolioBreakdownTable.tsx"],
            )

            self.assertIn("src/components/PortfolioBreakdownTable.tsx", scope)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_build_componentized_refinement_prompt_includes_table_trend_guidance(self):
        prompt = build_componentized_refinement_prompt(
            task_description_with_assets="Build a stock trading dashboard.",
            issues=["table_trend_missing"],
            ui_archetype="fintech",
        )

        self.assertIn("Table trend cues", prompt)
        self.assertIn("per-row trend context", prompt)

    def test_build_componentized_refinement_prompt_rejects_generic_dense_shell_copy(self):
        prompt = build_componentized_refinement_prompt(
            task_description_with_assets="Build an operations dashboard.",
            issues=["placeholder_text", "content_authenticity"],
            ui_archetype="dashboard",
        )

        self.assertIn("Dashboard Overview", prompt)
        self.assertIn("`View` / `Details`", prompt)
        self.assertIn("Dense shells should read like a real operations or market product", prompt)

    def test_parse_componentized_build_errors_extracts_paths_and_error_classes(self):
        code_dir = _case_dir("componentized-quality-build-errors")
        try:
            (code_dir / "src").mkdir(parents=True)
            build_result = {
                "logs": [
                    {
                        "stdout": "",
                        "stderr": (
                            "src/App.tsx:12:18: ERROR: Unterminated JSX contents\n"
                            "src/main.tsx:3:27: ERROR: Could not resolve \"./theme-context\"\n"
                            "src/components/Table.tsx:22:9: ERROR: No matching export in \"./row\" for import \"Row\"\n"
                        ),
                    }
                ]
            }

            errors = parse_componentized_build_errors(build_result, code_dir=code_dir)

            self.assertEqual(errors[0]["path"], "src/App.tsx")
            self.assertEqual(errors[0]["error_class"], "syntax")
            self.assertEqual(errors[1]["error_class"], "import")
            self.assertEqual(errors[2]["error_class"], "cross_file")
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_parse_componentized_build_errors_ignores_node_modules_stack_frames(self):
        code_dir = _case_dir("componentized-quality-build-errors-runtime")
        try:
            build_result = {
                "logs": [
                    {
                        "stdout": "",
                        "stderr": (
                            "src/App.tsx:12:18: ERROR: Unterminated JSX contents\n"
                            "node_modules/esbuild/lib/main.js:1472:15: ERROR: failureErrorWithLog\n"
                        ),
                    }
                ]
            }

            errors = parse_componentized_build_errors(build_result, code_dir=code_dir)

            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["path"], "src/App.tsx")
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_parse_componentized_build_errors_detects_package_json_install_parse_failures(self):
        code_dir = _case_dir("componentized-quality-package-json-build-errors")
        try:
            build_result = {
                "logs": [
                    {
                        "stdout": "",
                        "stderr": (
                            "npm error code EJSONPARSE\n"
                            "npm error JSON.parse Invalid package.json: JSONParseError: Expected double-quoted property name in JSON at position 79\n"
                            "npm error JSON.parse Failed to parse JSON data.\n"
                        ),
                    }
                ]
            }

            errors = parse_componentized_build_errors(build_result, code_dir=code_dir)

            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["path"], "package.json")
            self.assertEqual(errors[0]["error_class"], "syntax")
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_flat_single_font_dashboard_shells(self):
        code_dir = _case_dir("componentized-quality-visual-issues")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "base.css").write_text(
                "body { font-family: Inter, sans-serif; }\n"
                ".panel { box-shadow: 0 1px 2px rgba(0,0,0,0.2); }\n"
                ".button:hover { color: white; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <main><section className=\"panel\">Dashboard</section></main>;\n"
                "}\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="dashboard")

            self.assertIn("typography_hierarchy", issues)
            self.assertIn("weak_surface_depth", issues)
            self.assertIn("polish_flow", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_small_titles_and_flat_fintech_cards(self):
        code_dir = _case_dir("componentized-quality-fintech-visual-issues")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "base.css").write_text(
                "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@700&display=swap');\n"
                ".page-title { font-family: 'Space Grotesk', sans-serif; font-size: 28px; }\n"
                ".card { background-color: #111827; box-shadow: 0 10px 24px rgba(0,0,0,0.22); }\n"
                ".range-pill:hover { color: white; }\n"
                "button:focus-visible { outline: 2px solid #38bdf8; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <main><h1 className=\"page-title\">Dashboard Overview</h1><section className=\"card\">$124,832.50</section></main>;\n"
                "}\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="fintech")

            self.assertIn("typography_hierarchy", issues)
            self.assertIn("weak_surface_depth", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_generic_dense_shell_copy(self):
        code_dir = _case_dir("componentized-quality-generic-dense-shell-copy")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <main>\n"
                "      <header><h1>Dashboard Overview</h1></header>\n"
                "      <section className=\"kpi-grid\"><div className=\"kpi-card\">$124,832.50</div></section>\n"
                "      <table><tbody><tr><td>North Hub</td><td><button>View</button></td></tr><tr><td>South Hub</td><td><button>Details</button></td></tr><tr><td>West Hub</td><td><button>View</button></td></tr></tbody></table>\n"
                "      <aside>\n"
                "        <section><h2>Watchlist</h2><p>Flagged item</p></section>\n"
                "        <section><h2>Activity Feed</h2><p>Recent update</p></section>\n"
                "      </aside>\n"
                "    </main>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="dashboard")

            self.assertIn("placeholder_text", issues)
            self.assertIn("content_authenticity", issues)
            self.assertIn("text_density", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_remote_ecommerce_imagery_and_weak_polish(self):
        code_dir = _case_dir("componentized-quality-ecommerce-visual-issues")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "base.css").write_text(
                "body { font-family: Inter, sans-serif; }\n"
                ".hero-title { font-size: 30px; }\n"
                ".collection-card { box-shadow: 0 4px 14px rgba(0,0,0,0.22); }\n"
                ".product-card:hover { transform: translateY(-2px); }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "HomePage.tsx").write_text(
                "export default function HomePage() {\n"
                "  return (\n"
                "    <main>\n"
                "      <img src=\"https://images.unsplash.com/photo-1556906781-9a412961c28c?w=600&q=80\" alt=\"Hoodie\" />\n"
                "      <section className=\"collection-card\">Urban Capsule</section>\n"
                "    </main>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="ecommerce")

            self.assertIn("external_placeholder_assets", issues)
            self.assertIn("typography_hierarchy", issues)
            self.assertIn("polish_flow", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_understructured_workspace_shells(self):
        code_dir = _case_dir("componentized-quality-workspace-visual-issues")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "base.css").write_text(
                "body { font-family: Inter, sans-serif; }\n"
                ".panel { box-shadow: 0 4px 10px rgba(0,0,0,0.15); }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <main><section className=\"panel\">Editor</section></main>;\n"
                "}\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="editor")

            self.assertIn("workspace_shell_balance", issues)
            self.assertIn("typography_hierarchy", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_generic_workspace_lane_labels(self):
        code_dir = _case_dir("componentized-quality-workspace-generic-labels")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "base.css").write_text(
                "body { font-family: Inter, sans-serif; }\n"
                ".workspace-shell { box-shadow: 0 12px 32px rgba(0,0,0,0.18); }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <div className=\"workspace-shell\">\n"
                "      <header className=\"toolbar\"><span>Workspace</span><button>Open</button></header>\n"
                "      <main className=\"workspace-grid\">\n"
                "        <aside className=\"sidebar\">Notes</aside>\n"
                "        <section className=\"editor-panel\">Editor</section>\n"
                "        <aside className=\"inspector\">Inspector</aside>\n"
                "      </main>\n"
                "    </div>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="editor")

            self.assertIn("content_authenticity", issues)
            self.assertIn("workspace_shell_balance", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_guided_flow_shells_without_progression(self):
        code_dir = _case_dir("componentized-quality-guided-flow-visual-issues")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "base.css").write_text(
                "body { font-family: Inter, sans-serif; }\n"
                ".panel { box-shadow: 0 4px 10px rgba(0,0,0,0.15); }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return <main><section className=\"panel\"><input aria-label=\"Company name\" /></section></main>;\n"
                "}\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="form")

            self.assertIn("guided_flow_progression", issues)
            self.assertIn("typography_hierarchy", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_missing_material_icon_support(self):
        code_dir = _case_dir("componentized-quality-icon-font-support")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <header className=\"workspace-shell\">\n"
                "      <span className=\"material-symbols-outlined\">rocket_launch</span>\n"
                "      <span>Studio</span>\n"
                "    </header>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "base.css").write_text(
                "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&family=JetBrains+Mono:wght@500&display=swap');\n"
                ".workspace-shell { box-shadow: 0 12px 24px rgba(15, 23, 42, 0.18); }\n"
                ".workspace-shell:hover { transform: translateY(-2px); }\n"
                "button:focus-visible { outline: 2px solid #38bdf8; }\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="editor")

            self.assertIn("icon_font_support", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_missing_layout_selector_coverage(self):
        code_dir = _case_dir("componentized-quality-layout-selector-coverage")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <div className=\"app-shell\">\n"
                "      <div className=\"main-content-grid\">\n"
                "        <aside className=\"progress-rail\">Steps</aside>\n"
                "        <section className=\"review-sidebar\">Summary</section>\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "base.css").write_text(
                "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&family=JetBrains+Mono:wght@500&display=swap');\n"
                ".app-shell { box-shadow: 0 12px 24px rgba(15, 23, 42, 0.18); }\n"
                ".progress-rail { padding: 24px; }\n"
                ".review-sidebar { padding: 24px; }\n"
                ".review-sidebar:hover { transform: translateY(-2px); }\n"
                "button:focus-visible { outline: 2px solid #38bdf8; }\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="form")

            self.assertIn("layout_selector_coverage", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_workspace_textarea_heavy_builder_controls(self):
        code_dir = _case_dir("componentized-quality-workspace-control-density")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <div className=\"workspace-shell\">\n"
                "      <header className=\"toolbar\">Prompt Layer Studio</header>\n"
                "      <main className=\"workspace-grid\">\n"
                "        <section className=\"editor-panel\">\n"
                "          <h1>Prompt Layer Editor</h1>\n"
                "          <label>Layer Content</label>\n"
                "          <textarea rows={8} defaultValue=\"You are a helpful assistant\" />\n"
                "        </section>\n"
                "        <aside className=\"preview-panel\">Preview</aside>\n"
                "      </main>\n"
                "    </div>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "base.css").write_text(
                "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&family=JetBrains+Mono:wght@500&display=swap');\n"
                ".workspace-shell { box-shadow: 0 12px 24px rgba(15, 23, 42, 0.18); }\n"
                ".toolbar { display: flex; }\n"
                ".workspace-grid { display: grid; grid-template-columns: 1.4fr 0.8fr; gap: 24px; }\n"
                ".editor-panel { padding: 24px; }\n"
                ".preview-panel { padding: 24px; }\n"
                ".workspace-shell:hover { transform: translateY(-2px); }\n"
                "button:focus-visible, textarea:focus-visible { outline: 2px solid #38bdf8; }\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="editor")

            self.assertIn("workspace_control_density", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_workspace_preview_emphasis_gap(self):
        code_dir = _case_dir("componentized-quality-workspace-preview-emphasis")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <div className=\"workspace-shell\">\n"
                "      <header className=\"toolbar\">AI Builder Studio</header>\n"
                "      <main className=\"workspace-grid\">\n"
                "        <section className=\"editor-panel\">\n"
                "          <h1>Prompt Layer Editor</h1>\n"
                "          <textarea rows={8} defaultValue=\"You are a helpful assistant\" />\n"
                "        </section>\n"
                "        <aside className=\"preview-panel\">\n"
                "          <h2>Live Preview</h2>\n"
                "          <pre className=\"code-block\">{\\\"idea_name\\\":\\\"EcoCycle AI\\\"}</pre>\n"
                "        </aside>\n"
                "      </main>\n"
                "    </div>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "base.css").write_text(
                "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&family=JetBrains+Mono:wght@500&display=swap');\n"
                ".workspace-shell { box-shadow: 0 12px 24px rgba(15, 23, 42, 0.18); }\n"
                ".toolbar { display: flex; }\n"
                ".workspace-grid { display: grid; grid-template-columns: 1.4fr 0.8fr; gap: 24px; }\n"
                ".editor-panel, .preview-panel { padding: 24px; }\n"
                ".workspace-shell:hover { transform: translateY(-2px); }\n"
                "button:focus-visible, textarea:focus-visible { outline: 2px solid #38bdf8; }\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="editor")

            self.assertIn("workspace_preview_emphasis", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_builder_workspace_drift_from_document_shell(self):
        code_dir = _case_dir("componentized-quality-builder-workspace-drift")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <div className=\"workspace-shell\">\n"
                "      <header className=\"toolbar\">Builder Studio</header>\n"
                "      <main className=\"workspace-grid\">\n"
                "        <section className=\"canvas-paper\">\n"
                "          <div className=\"document-hero\">\n"
                "            <h1 className=\"doc-title\">AI Product Brief</h1>\n"
                "            <p className=\"doc-meta\">Last edited by Jordan, 15:30 Aug 23, 2024</p>\n"
                "          </div>\n"
                "          <div className=\"prompt-layer-card\">Prompt Layer 1</div>\n"
                "          <div className=\"preview-frame\">Live Preview</div>\n"
                "        </section>\n"
                "        <aside className=\"inspector-panel\">\n"
                "          <h2>Launch Blockers</h2>\n"
                "          <p>QA Notes</p>\n"
                "          <p>Variant Runs</p>\n"
                "        </aside>\n"
                "      </main>\n"
                "    </div>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "base.css").write_text(
                "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&family=JetBrains+Mono:wght@500&display=swap');\n"
                ".workspace-shell { box-shadow: 0 12px 24px rgba(15, 23, 42, 0.18); }\n"
                ".toolbar { display: flex; }\n"
                ".workspace-grid { display: grid; grid-template-columns: 1.4fr 0.8fr; gap: 24px; }\n"
                ".canvas-paper, .inspector-panel { padding: 24px; }\n"
                ".preview-frame { min-height: 240px; }\n"
                "button:focus-visible, textarea:focus-visible { outline: 2px solid #38bdf8; }\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="editor")

            self.assertIn("builder_workspace_drift", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_builder_workspace_drift_from_warm_editorial_tone(self):
        code_dir = _case_dir("componentized-quality-builder-workspace-tone")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <div className=\"workspace-shell\">\n"
                "      <header className=\"toolbar\">Builder Studio</header>\n"
                "      <main className=\"workspace-grid\">\n"
                "        <section className=\"builder-panel\">\n"
                "          <h1>Prompt Layer Stack</h1>\n"
                "          <div className=\"live-preview\">Live Preview</div>\n"
                "          <div className=\"variant-run\">Variant Runs</div>\n"
                "        </section>\n"
                "        <aside className=\"launch-blockers\">Launch Blockers</aside>\n"
                "      </main>\n"
                "    </div>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "base.css").write_text(
                "@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@700&family=JetBrains+Mono:wght@500&display=swap');\n"
                ":root { --bg: #f2ede3; --accent: #b45309; }\n"
                "body { background: linear-gradient(180deg, #f6f0e7, #ece5d8); font-family: 'Fraunces', serif; }\n"
                ".workspace-grid { display: grid; grid-template-columns: 1.4fr 0.8fr; gap: 24px; }\n"
                ".builder-panel, .launch-blockers { padding: 24px; border: 1px solid rgba(32, 21, 13, 0.09); }\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="editor")

            self.assertIn("builder_workspace_drift", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_detect_componentized_quality_issues_flags_thin_enterprise_snapshot_lane(self):
        code_dir = _case_dir("componentized-quality-guided-flow-snapshot-density")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() {\n"
                "  return (\n"
                "    <div className=\"wizard-shell\">\n"
                "      <aside className=\"review-sidebar\">\n"
                "        <h2>Application Snapshot</h2>\n"
                "        <p>Status: Blocked</p>\n"
                "        <p>Progress: 1/4 complete</p>\n"
                "        <p>Vendor onboarding for Acme Industrial</p>\n"
                "        <p>Compliance documents will be reviewed later.</p>\n"
                "      </aside>\n"
                "      <main className=\"active-step-panel\">Review & Submit</main>\n"
                "    </div>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "base.css").write_text(
                "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&family=JetBrains+Mono:wght@500&display=swap');\n"
                ".wizard-shell { display: grid; grid-template-columns: 320px 1fr; gap: 24px; }\n"
                ".review-sidebar, .active-step-panel { padding: 24px; box-shadow: 0 12px 24px rgba(15, 23, 42, 0.18); }\n"
                ".review-sidebar:hover { transform: translateY(-2px); }\n"
                "button:focus-visible, input:focus-visible { outline: 2px solid #38bdf8; }\n",
                encoding="utf-8",
            )

            issues = detect_componentized_quality_issues(code_dir, ui_archetype="form")

            self.assertIn("guided_flow_snapshot_density", issues)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_expand_componentized_iteration_scaffold_scope_uses_existing_workspace_files(self):
        code_dir = _case_dir("componentized-iteration-scaffold-scope")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "pages").mkdir(parents=True)
            (code_dir / "src" / "base.css").write_text(":root { --accent: #10b981; }\n", encoding="utf-8")
            (code_dir / "src" / "index.css").write_text(".app-shell { min-height: 100vh; }\n", encoding="utf-8")
            (code_dir / "src" / "App.tsx").write_text("export default function App() { return <div className=\"app-shell\" />; }\n", encoding="utf-8")
            (code_dir / "src" / "main.tsx").write_text("import './base.css';\nimport './index.css';\n", encoding="utf-8")
            (code_dir / "src" / "components" / "TopBar.tsx").write_text("export default function TopBar() { return <header />; }\n", encoding="utf-8")
            (code_dir / "src" / "pages" / "Dashboard.tsx").write_text("export default function Dashboard() { return <main />; }\n", encoding="utf-8")

            scope = expand_componentized_iteration_scaffold_scope(
                code_dir,
                ["package.json", "index.html", "src/main.tsx", "src/App.tsx"],
            )

            self.assertIn("src/components/TopBar.tsx", scope)
            self.assertIn("src/pages/Dashboard.tsx", scope)
            self.assertIn("src/base.css", scope)
            self.assertIn("src/index.css", scope)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_select_componentized_refinement_scope_includes_base_css_for_visual_polish(self):
        code_dir = _case_dir("componentized-quality-refinement-scope")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "base.css").write_text(":root { --accent: #10b981; }\n", encoding="utf-8")
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() { return <div className=\"panel\">Hello</div>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "index.css").write_text(".panel { padding: 24px; }\n", encoding="utf-8")

            scope = select_componentized_refinement_scope(
                code_dir,
                ["typography_hierarchy", "weak_surface_depth", "polish_flow"],
            )

            self.assertIn("src/base.css", scope)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_select_componentized_refinement_scope_keeps_content_repairs_off_shell_css(self):
        code_dir = _case_dir("componentized-quality-content-scope")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "pages").mkdir(parents=True)
            (code_dir / "src" / "data").mkdir(parents=True)
            (code_dir / "src" / "base.css").write_text(":root { --accent: #10b981; }\n", encoding="utf-8")
            (code_dir / "src" / "App.tsx").write_text("export default function App() { return <div />; }\n", encoding="utf-8")
            (code_dir / "src" / "pages" / "Dashboard.tsx").write_text("export default function Dashboard() { return <div />; }\n", encoding="utf-8")
            (code_dir / "src" / "components" / "NewsFeed.tsx").write_text("export default function NewsFeed() { return <div>User 1</div>; }\n", encoding="utf-8")
            (code_dir / "src" / "data" / "watchlist.ts").write_text("export const watchlist = [{ symbol: 'AAPL', time: 'Mar 14, 2026' }];\n", encoding="utf-8")

            scope = select_componentized_refinement_scope(
                code_dir,
                ["placeholder_text", "data_specificity", "temporal_realism"],
                weak_file_paths=["src/components/NewsFeed.tsx", "src/data/watchlist.ts"],
            )

            self.assertIn("src/components/NewsFeed.tsx", scope)
            self.assertIn("src/data/watchlist.ts", scope)
            self.assertIn("src/pages/Dashboard.tsx", scope)
            self.assertNotIn("src/base.css", scope)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_collect_componentized_editable_files_skips_generated_lockfile(self):
        code_dir = _case_dir("componentized-editable-files")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "package-lock.json").write_text('{"name":"demo","lockfileVersion":3}\n', encoding="utf-8")
            (code_dir / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() { return <main>Demo</main>; }\n",
                encoding="utf-8",
            )

            editable_files = collect_componentized_editable_files(code_dir)

            self.assertIn("package.json", editable_files)
            self.assertIn("src/App.tsx", editable_files)
            self.assertNotIn("package-lock.json", editable_files)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_classify_componentized_content_file_skips_icons_and_polish_guards(self):
        icon_report = classify_componentized_content_file(
            "src/components/Icons.tsx",
            "export const UserIcon = () => <svg><circle cx=\"12\" cy=\"7\" r=\"4\" /></svg>;\n",
        )
        guard_report = classify_componentized_content_file(
            "src/polish-guard.ts",
            "const COUNT_SELECTORS = ['.kpi-value']; export function applyPolishGuard() {}\n",
        )

        self.assertEqual("config", icon_report["role"])
        self.assertFalse(icon_report["is_content_bearing"])
        self.assertEqual("config", guard_report["role"])
        self.assertFalse(guard_report["is_content_bearing"])

    def test_select_componentized_refinement_scope_skips_generated_support_noise(self):
        code_dir = _case_dir("componentized-quality-shell-noise")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "base.css").write_text(":root { --accent: #3a82f6; }\n", encoding="utf-8")
            (code_dir / "src" / "index.css").write_text(
                "/* App-specific overrides live here. Keep this file intentionally minimal. */\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "styles.css").write_text(
                "/* This file is intentionally left blank. Custom overrides are in style.css */\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "polish-guard.css").write_text(
                ".chart-card { box-shadow: 0 20px 40px rgba(2, 6, 23, 0.3); }\n",
                encoding="utf-8",
            )
            (code_dir / "style.css").write_text(
                ".dashboard-shell { font-family: 'Space Grotesk', sans-serif; box-shadow: 0 20px 40px rgba(2, 6, 23, 0.3); }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "main.tsx").write_text(
                "import './base.css';\nimport './index.css';\nimport './styles.css';\nimport './polish-guard.css';\nimport '../style.css';\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() { return <div className=\"dashboard-shell\">Portfolio Value</div>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "Dashboard.tsx").write_text(
                "export default function Dashboard() { return <section><h2>Candlestick Chart</h2><div>Watchlist</div><div>2 hours ago</div></section>; }\n",
                encoding="utf-8",
            )
            (code_dir / "package-lock.json").write_text(
                '{"name":"demo","packages":{"":{"description":"watchlist chart delta"}}}\n',
                encoding="utf-8",
            )

            scope = select_componentized_refinement_scope(
                code_dir,
                ["typography_hierarchy", "chart_missing", "side_panel_thin", "text_density"],
            )

            self.assertIn("src/base.css", scope)
            self.assertIn("style.css", scope)
            self.assertIn("src/App.tsx", scope)
            self.assertIn("src/components/Dashboard.tsx", scope)
            self.assertNotIn("package-lock.json", scope)
            self.assertNotIn("src/polish-guard.css", scope)
            self.assertNotIn("src/index.css", scope)
            self.assertNotIn("src/styles.css", scope)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_select_componentized_content_fix_scope_targets_upstream_content_files(self):
        code_dir = _case_dir("componentized-content-fix-scope")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "data").mkdir(parents=True)
            (code_dir / "src" / "pages").mkdir(parents=True)
            (code_dir / "src" / "base.css").write_text(":root { --accent: #10b981; }\n", encoding="utf-8")
            (code_dir / "src" / "App.tsx").write_text(
                "import Dashboard from './pages/Dashboard';\n"
                "export default function App() { return <Dashboard />; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "pages" / "Dashboard.tsx").write_text(
                "import Watchlist from '../components/Watchlist';\n"
                "import { watchlist } from '../data/watchlist';\n"
                "export default function Dashboard() { return <Watchlist items={watchlist} />; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "data" / "watchlist.ts").write_text(
                "export const watchlist = [{ symbol: 'MSFT', price: 421.88, time: '2 hours ago' }];\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "Watchlist.tsx").write_text(
                "interface Props { items: { symbol: string }[] }\n"
                "export default function Watchlist({ items }: Props) { return <div className=\"watchlist-card\">Watchlist</div>; }\n",
                encoding="utf-8",
            )

            scope = select_componentized_content_fix_scope(
                code_dir,
                weak_file_paths=["src/components/Watchlist.tsx"],
            )

            self.assertIn("src/components/Watchlist.tsx", scope)
            self.assertIn("src/App.tsx", scope)
            self.assertIn("src/data/watchlist.ts", scope)
            self.assertIn("src/pages/Dashboard.tsx", scope)
            self.assertNotIn("index.html", scope)
            self.assertNotIn("src/main.tsx", scope)
            self.assertNotIn("src/base.css", scope)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_select_componentized_build_repair_scope_targets_broken_graph_only(self):
        code_dir = _case_dir("componentized-build-repair-graph-scope")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "pages").mkdir(parents=True)
            (code_dir / "src" / "data").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import Dashboard from './pages/Dashboard';\n"
                "import NewsFeed from './components/NewsFeed';\n"
                "export default function App() { return <><Dashboard /><NewsFeed /></>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "pages" / "Dashboard.tsx").write_text(
                "import Table from '../components/Table';\n"
                "export default function Dashboard() { return <Table />; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "Table.tsx").write_text(
                "import { Row } from './row';\n"
                "export default function Table() { return <Row />; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "row.tsx").write_text(
                "export function Cell() { return <div>Cell</div>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "NewsFeed.tsx").write_text(
                "export default function NewsFeed() { return <aside>News</aside>; }\n",
                encoding="utf-8",
            )

            scope = select_componentized_build_repair_scope(
                code_dir,
                [
                    {
                        "path": "src/components/Table.tsx",
                        "line": 1,
                        "error_class": "cross_file",
                        "message": "No matching export in \"./row\" for import \"Row\"",
                    }
                ],
            )

            self.assertIn("src/components/Table.tsx", scope)
            self.assertIn("src/components/row.tsx", scope)
            self.assertIn("src/pages/Dashboard.tsx", scope)
            self.assertIn("src/App.tsx", scope)
            self.assertNotIn("src/components/NewsFeed.tsx", scope)
            self.assertNotIn("index.html", scope)
            self.assertNotIn("src/main.tsx", scope)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_select_componentized_build_repair_scope_includes_support_files_for_package_json_errors(self):
        code_dir = _case_dir("componentized-build-repair-support-scope")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")
            (code_dir / "vite.config.ts").write_text("export default {};\n", encoding="utf-8")
            (code_dir / "tsconfig.json").write_text('{"compilerOptions":{}}\n', encoding="utf-8")
            (code_dir / "tsconfig.node.json").write_text('{"compilerOptions":{}}\n', encoding="utf-8")
            (code_dir / "index.html").write_text("<!doctype html><html><body><div id='root'></div></body></html>\n", encoding="utf-8")
            (code_dir / "src" / "vite-env.d.ts").write_text("/// <reference types='vite/client' />\n", encoding="utf-8")
            (code_dir / "src" / "main.tsx").write_text(
                "import ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "import './style.css';\nexport default function App() { return <div>Hello</div>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "style.css").write_text(".app { color: red; }\n", encoding="utf-8")
            (code_dir / "src" / "components" / "Sidebar.tsx").write_text(
                "export default function Sidebar() { return <aside>Side</aside>; }\n",
                encoding="utf-8",
            )

            scope = select_componentized_build_repair_scope(
                code_dir,
                [
                    {
                        "path": "package.json",
                        "line": None,
                        "error_class": "syntax",
                        "message": "Invalid package.json: JSONParseError",
                    }
                ],
            )

            self.assertIn("package.json", scope)
            self.assertIn("vite.config.ts", scope)
            self.assertIn("tsconfig.json", scope)
            self.assertIn("tsconfig.node.json", scope)
            self.assertIn("src/vite-env.d.ts", scope)
            self.assertIn("index.html", scope)
            self.assertIn("src/main.tsx", scope)
            self.assertIn("src/App.tsx", scope)
            self.assertNotIn("src/components/Sidebar.tsx", scope)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_tsconfig_missing_commas(self):
        code_dir = _case_dir("componentized-tsconfig-missing-commas")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "tsconfig.node.json").write_text(
                "{\n"
                "  \"compilerOptions\": {\n"
                "    \"target\": \"ES2020\"\n"
                "    \"allowSyntheticDefaultImports\": true\n"
                "  },\n"
                "  \"include\": [\"vite.config.ts\"]\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            tsconfig_source = (code_dir / "tsconfig.node.json").read_text(encoding="utf-8")
            self.assertIn('"target": "ES2020",', tsconfig_source)
            self.assertIn('"allowSyntheticDefaultImports": true', tsconfig_source)
            self.assertIn('"allowImportingTsExtensions": true', tsconfig_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_extend_componentized_scope_includes_direct_support_files_for_build_repairs(self):
        code_dir = _case_dir("componentized-build-repair-scope")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "pages").mkdir(parents=True)
            (code_dir / "src" / "styles").mkdir(parents=True)
            (code_dir / "index.html").write_text("<!doctype html><html><body><div id='root'></div></body></html>\n", encoding="utf-8")
            (code_dir / "src" / "main.tsx").write_text(
                "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\nReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "App.tsx").write_text(
                "import Layout from './components/Layout';\nimport Dashboard from './pages/Dashboard';\nexport default function App() { return <Layout><Dashboard /></Layout>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "Layout.tsx").write_text(
                "import '../styles/global.css';\nexport default function Layout({ children }: { children: React.ReactNode }) { return <main>{children}</main>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "pages" / "Dashboard.tsx").write_text(
                "export default function Dashboard() { return <section>Desk</section>; }\n",
                encoding="utf-8",
            )
            (code_dir / "src" / "styles" / "global.css").write_text(".shell { min-height: 100vh; }\n", encoding="utf-8")

            scope = extend_componentized_scope(
                code_dir,
                ["src/pages/Dashboard.tsx"],
                include_style_targets=False,
                include_direct_support=True,
            )

            self.assertIn("src/pages/Dashboard.tsx", scope)
            self.assertIn("src/App.tsx", scope)
            self.assertIn("src/components/Layout.tsx", scope)
            self.assertIn("src/styles/global.css", scope)
            self.assertIn("src/main.tsx", scope)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_syncs_react_feather_dependency(self):
        code_dir = _case_dir("componentized-react-feather-dependency")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "package.json").write_text(
                '{\n  "name": "demo",\n  "dependencies": {\n    "react": "^18.3.1"\n  }\n}\n',
                encoding="utf-8",
            )
            (code_dir / "src" / "components" / "Sidebar.tsx").write_text(
                "import { Home } from 'react-feather';\n"
                "export default function Sidebar() { return <Home />; }\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            package_json = (code_dir / "package.json").read_text(encoding="utf-8")
            self.assertIn('"react-feather": "^2.0.10"', package_json)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_invalid_react_icons_feather_exports(self):
        code_dir = _case_dir("componentized-react-icons-feather-export-fix")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React from 'react';\n"
                "import { FiUndo, FiRedo, FiSave } from 'react-icons/fi';\n"
                "export default function App() {\n"
                "  return <div><FiUndo /><FiRedo /><FiSave /></div>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("FiRotateCcw", app_source)
            self.assertIn("FiRotateCw", app_source)
            self.assertNotIn("FiUndo", app_source)
            self.assertNotIn("FiRedo", app_source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_normalize_run_on_natural_language_notes_merges_multiline_prose_after_comment(self):
        source = (
            "useEffect(() => {\n"
            "  /* This assumes */\n"
            "  Alpine.js is initialized and available on the window\n"
            "  // and that the x-data scope on this element can be accessed.\n"
            "  /* For mixed React/Alpine, React controls rendering, Alpine controls */\n"
            "  class/visibility.\n"
            "  if (isCartDrawerOpen) {\n"
            "    openDrawer();\n"
            "  }\n"
            "}, [isCartDrawerOpen]);\n"
        )

        normalized = _normalize_run_on_natural_language_notes(source)

        self.assertIn(
            "  /* This assumes Alpine.js is initialized and available on the window */\n",
            normalized,
        )
        self.assertIn(
            "  /* For mixed React/Alpine, React controls rendering, Alpine controls class/visibility. */\n",
            normalized,
        )
        self.assertNotIn("\n  Alpine.js is initialized and available on the window\n", normalized)
        self.assertNotIn("\n  class/visibility.\n", normalized)

    def test_normalize_run_on_natural_language_notes_merges_unindented_prose_after_comment(self):
        source = (
            "if (drawerRef.current) {\n"
            "  /* This assumes */\n"
            "Alpine.js is initialized and available on the window\n"
            "  // and that the x-data scope on this element can be accessed.\n"
            "  /* A more robust way would be to use */\n"
            "Alpine.data() if the component was Alpine-only.\n"
            "}\n"
        )

        normalized = _normalize_run_on_natural_language_notes(source)

        self.assertIn(
            "  /* This assumes Alpine.js is initialized and available on the window */\n",
            normalized,
        )
        self.assertIn(
            "  /* A more robust way would be to use Alpine.data() if the component was Alpine-only. */\n",
            normalized,
        )
        self.assertNotIn("\nAlpine.js is initialized and available on the window\n", normalized)
        self.assertNotIn("\nAlpine.data() if the component was Alpine-only.\n", normalized)

    def test_ensure_componentized_workspace_support_repairs_unterminated_inline_comment_and_dotted_orphan_close(self):
        code_dir = _case_dir("componentized-runtime-right-rail-comment-split")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "RightRail.tsx").write_text(
                "import React, { useState } from 'react';\n"
                "export default function RightRail() {\n"
                "  const [activeTab, setActiveTab] = useState('alerts');\n"
                "  const handleResolveAlert = (id: number) => { alert(`Resolving alert ${id}`); /* In a real app, this would update state to remove the alert\n"
                "  };\n"
                "  return (\n"
                "    <aside>\n"
                "      <button onClick={() => setActiveTab('activity')}>Activity</button>\n"
                "      <div>\n"
                "        {activeTab === 'activity' && (\n"
                "          <div>\n"
                "            {['event'].map((kind) => (\n"
                "              <div key={kind}>\n"
                "                {kind === 'update' && <span>Update</span>}\n"
                "                {kind. */\n"
                "type === 'event' && <span>Event</span>}\n"
                "              </div>\n"
                "            ))}\n"
                "          </div>\n"
                "        )}\n"
                "      </div>\n"
                "    </aside>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "components" / "RightRail.tsx").read_text(encoding="utf-8")
            self.assertIn(
                "/* In a real app, this would update state to remove the alert */",
                source,
            )
            self.assertIn("kind.type === 'event'", source)
            self.assertNotIn("kind. */", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_swallowed_push_call_after_inline_comment(self):
        code_dir = _case_dir("componentized-runtime-swallowed-push-call")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "MainContent.tsx").write_text(
                "export default function MainContent() {\n"
                "  const generateChartData = () => {\n"
                "    const data = [];\n"
                "    let currentValue = 1000;\n"
                "    for (let i = 0; i < 12; i++) { currentValue += Math.round(Math.random() * 200 - 100); /* +/- 100      data.push( */\n"
                "    Math.max(500, currentValue)); /* Ensure value doesn't go too low */\n"
                "    }\n"
                "    return data;\n"
                "  };\n"
                "  return <div>{generateChartData().length}</div>;\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "components" / "MainContent.tsx").read_text(encoding="utf-8")
            self.assertIn("/* +/- 100 */", source)
            self.assertIn("data.push(Math.max(500, currentValue));", source)
            self.assertNotIn("data.push( */", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_strips_inline_script_tags_from_components(self):
        code_dir = _case_dir("componentized-runtime-inline-script-tag")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "Layout.tsx").write_text(
                "import React from 'react';\n"
                "export default function Layout() {\n"
                "  return (\n"
                "    <div>\n"
                "      <main>Content</main>\n"
                "      <script>\n"
                "        document.querySelectorAll('a').forEach((node) => {\n"
                "          node.addEventListener('click', () => console.log(node));\n"
                "        });\n"
                "      </script>\n"
                "    </div>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "components" / "Layout.tsx").read_text(encoding="utf-8")
            self.assertNotIn("<script>", source)
            self.assertIn("{/* Removed broken inline script from generated component */}", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_jsx_tag_comment_lines_and_typed_handlers(self):
        code_dir = _case_dir("componentized-runtime-jsx-tag-comment-lines")
        try:
            (code_dir / "src" / "components").mkdir(parents=True)
            (code_dir / "src" / "components" / "Gallery.tsx").write_text(
                "import React from 'react';\n"
                "export default function Gallery() {\n"
                "  return (\n"
                "    <img\n"
                "      src=\"hero.png\" /* reuse hero image */\n"
                "/* constraint */\n"
                "      alt=\"Hero\"\n"
                "      onError={(e: any) = /> {\n"
                "        e.target.alt = 'Fallback';\n"
                "      }}\n"
                "    />\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "components" / "Gallery.tsx").read_text(encoding="utf-8")
            self.assertNotIn("/* constraint */", source)
            self.assertNotIn("reuse hero image", source)
            self.assertIn("onError={(e: any) => {", source)
            self.assertNotIn("= />", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_repairs_jsx_text_comment_close_bleed(self):
        code_dir = _case_dir("componentized-runtime-jsx-text-comment-close-bleed")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React from 'react';\n"
                "export default function App() {\n"
                "  return (\n"
                "    <button>\n"
                "      <svg viewBox=\"0 0 24 24\"></svg> Export */\n"
                "      CSV\n"
                "    </button>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn("</svg>Export CSV</button>", source.replace("\n", ""))
            self.assertNotIn("*/", source)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_ensure_componentized_workspace_support_removes_duplicate_closing_tag_lines(self):
        code_dir = _case_dir("componentized-runtime-duplicate-closing-tag-lines")
        try:
            (code_dir / "src").mkdir(parents=True)
            (code_dir / "src" / "App.tsx").write_text(
                "import React from 'react';\n"
                "export default function App() {\n"
                "  return (\n"
                "    <div>\n"
                "      <button><svg viewBox=\"0 0 24 24\"></svg>Export CSV</button>\n"
                "      </button>\n"
                "    </div>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertEqual(source.count("</button>"), 1)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
