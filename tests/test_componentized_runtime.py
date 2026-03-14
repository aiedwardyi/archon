from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from backend.app import (
    detect_componentized_quality_issues,
    extend_componentized_scope,
    select_componentized_build_repair_scope,
    select_componentized_content_fix_scope,
    select_componentized_refinement_scope,
    validate_componentized_contract_outputs,
)
from utils.componentized_runtime import (
    build_componentized_preview,
    collect_componentized_reverse_dependents,
    ensure_componentized_workspace_support,
    collect_existing_code_context,
    extract_feature_inventory,
    extract_visual_dna,
    infer_scaffold_mode,
    rewrite_componentized_asset_api_urls,
    rewrite_preview_file_references,
    stage_componentized_design_assets,
)
from utils.componentized_quality import (
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
            '<img src="/generated-assets/hero.png">'
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

    def test_build_componentized_preview_skips_without_package_json(self):
        code_dir = _case_dir("componentized-runtime-build")
        try:
            result = build_componentized_preview(code_dir)
            self.assertEqual(result["status"], "skipped")
            self.assertIsNone(result["dist_index"])
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

        self.assertIn('/generated-assets/hero_background.png', rewritten)
        self.assertIn('/generated-assets/world_map.png', rewritten)
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
                self.assertLess(main_source.index('import "./base.css";'), main_source.index('import "./index.css";'))
            app_source = (code_dir / "src" / "App.tsx").read_text(encoding="utf-8")
            self.assertIn('/generated-assets/hero.png', app_source)
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
            self.assertIn('import "./polish-guard.css";', main_source)
            self.assertGreater(
                main_source.index('import "./polish-guard.css";'),
                main_source.index('import "./style.css";'),
            )
            self.assertIn(".topbar-brand", polish_guard)
            self.assertIn(".kpi-value", polish_guard)
            self.assertIn("Runtime shell polish guard for fintech", polish_guard)
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
            self.assertNotIn('import "./polish-guard.css";', main_source)
            self.assertFalse((code_dir / "src" / "polish-guard.css").exists())
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
            self.assertLess(main_source.index('import "./base.css";'), main_source.index('import "./style.css";'))
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
                "import { defineConfig } from 'vite'import react from '@vitejs/plugin-react'\n"
                "export default defineConfig({ plugins: [react()] })\n",
                encoding="utf-8",
            )

            ensure_componentized_workspace_support(code_dir)

            vite_config = (code_dir / "vite.config.ts").read_text(encoding="utf-8")
            self.assertIn("from 'vite'\nimport react", vite_config)
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

            self.assertEqual(staged[0]["path"], "/generated-assets/hero_background.png")
            self.assertTrue((version_dir / "code" / "public" / "generated-assets" / "hero_background.png").exists())
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


if __name__ == "__main__":
    unittest.main()
