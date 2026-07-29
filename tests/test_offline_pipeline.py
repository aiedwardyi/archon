from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from backend import db_paths
from schemas.plan_schema import Plan
from schemas.prd_schema import PRDArtifact
from utils.offline_engineer_scaffold import build_vite_react_ts_scaffold
from utils.offline_seed import build_offline_plan, build_offline_prd_artifact, is_offline_mode


class OfflinePipelineTests(unittest.TestCase):
    def test_offline_mode_accepts_common_true_values(self):
        for value in ("1", "true", "yes", "y", "on"):
            with self.subTest(value=value), mock.patch.dict(os.environ, {"OFFLINE_MODE": value}):
                self.assertTrue(is_offline_mode())

    def test_offline_artifacts_satisfy_runtime_schemas(self):
        idea = "Build a task dashboard with three seeded tasks"

        prd = build_offline_prd_artifact(idea)
        plan = build_offline_plan(idea)

        self.assertIsInstance(prd, PRDArtifact)
        self.assertIsInstance(plan, Plan)
        self.assertEqual(plan.milestones[0].tasks[0].scaffold_mode, "componentized_app")
        self.assertEqual(plan.milestones[0].tasks[0].ui_archetype, "dashboard")
        self.assertEqual(prd.prd.prompt_quality_score, 50)

    def test_offline_archetype_matches_complete_words(self):
        cases = {
            "Build a SaaS platform": "landing",
            "Build an application for managing invoices": "landing",
            "Build an application form for grant requests": "form",
            "Build a sales dashboard": "dashboard",
        }

        for idea, expected in cases.items():
            with self.subTest(idea=idea):
                plan = build_offline_plan(idea)
                self.assertEqual(plan.milestones[0].tasks[0].ui_archetype, expected)

    def test_root_scaffold_contains_build_contract(self):
        files = build_vite_react_ts_scaffold(app_dir="").files

        self.assertTrue({"package.json", "index.html", "src/main.tsx", "src/App.tsx"} <= files.keys())
        self.assertNotIn("/package.json", files)

    def test_database_path_accepts_absolute_override(self):
        configured = db_paths.REPO_ROOT / ".tmp-tests" / "archon.db"

        with mock.patch.dict(os.environ, {"DATABASE_PATH": str(configured)}):
            self.assertEqual(db_paths.resolve_db_path(), configured)

    def test_database_path_resolves_relative_override_from_repo(self):
        with mock.patch.dict(os.environ, {"DATABASE_PATH": "data/archon.db"}):
            self.assertEqual(db_paths.resolve_db_path(), db_paths.REPO_ROOT / "data/archon.db")

    def test_prepare_database_path_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            configured = Path(tmpdir) / "nested" / "archon.db"
            with mock.patch.dict(os.environ, {"DATABASE_PATH": str(configured)}):
                resolved = db_paths.prepare_db_path()

            self.assertEqual(resolved, configured)
            self.assertTrue(configured.parent.is_dir())


if __name__ == "__main__":
    unittest.main()
