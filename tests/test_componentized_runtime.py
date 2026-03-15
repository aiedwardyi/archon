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
    collect_componentized_editable_files,
    collect_componentized_reverse_dependents,
    ensure_componentized_workspace_support,
    collect_existing_code_context,
    extract_feature_inventory,
    extract_visual_dna,
    infer_scaffold_mode,
    rewrite_componentized_asset_api_urls,
    rewrite_preview_file_references,
    rewrite_preview_runtime_asset_references,
    stage_componentized_design_assets,
)
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
                self.assertLess(main_source.index('import "./base.css";'), main_source.index('import "./index.css";'))
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
            self.assertIn(".watchlist-card", polish_guard)
            self.assertIn(".watchlist-feed-panel", polish_guard)
            self.assertIn(".news-feed-item", polish_guard)
            self.assertIn(".activity-item .activity-time", polish_guard)
            self.assertIn(".activity-feed .feed-header", polish_guard)
            self.assertIn(".data-table-wrapper", polish_guard)
            self.assertIn(".kpi-card:nth-child(4n + 1)", polish_guard)
            self.assertIn(".activity-feed::after", polish_guard)
            self.assertIn("button:focus-visible", polish_guard)
            self.assertIn("--guard-sidebar-offset", polish_guard)
            self.assertIn("Runtime shell polish guard for fintech", polish_guard)
            self.assertIn("requestAnimationFrame", polish_runtime)
            self.assertIn(".kpi-value", polish_runtime)
            self.assertIn(".text-mono", polish_runtime)
            self.assertIn("MONO_SELECTORS", polish_runtime)
            self.assertIn("guard-mono-count", polish_runtime)
            self.assertIn("applyNewsHierarchyGuard", polish_runtime)
            self.assertIn("applyActionGuard", polish_runtime)
            self.assertIn("applyShellLayoutGuard", polish_runtime)
            self.assertIn("schedulePolishGuard", polish_runtime)
            self.assertIn("guard-fixed-sidebar-shell", polish_runtime)
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
