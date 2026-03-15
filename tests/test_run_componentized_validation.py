from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from eval.api_client import BuildError
from eval import run_componentized_validation as runner


class RunComponentizedValidationTests(unittest.TestCase):
    def test_create_and_build_sync_forwards_enqueue_flag(self):
        builder = mock.Mock()
        builder.create_and_build.return_value = {"project_id": 1, "version": 1, "execution_id": 1}

        with mock.patch.object(runner, "BuilderAPI", return_value=builder) as builder_cls:
            result = runner._create_and_build_sync(
                base_url="http://127.0.0.1:5000",
                name="componentized_dashboard_test",
                description="Build a dashboard",
                timeout=30,
                enqueue_on_limit=True,
                queue_timeout=120,
            )

        builder_cls.assert_called_once_with(base_url="http://127.0.0.1:5000")
        builder.create_and_build.assert_called_once_with(
            name="componentized_dashboard_test",
            description="Build a dashboard",
            timeout=30,
            enqueue_on_limit=True,
            queue_timeout=120,
        )
        self.assertEqual(result["project_id"], 1)

    def test_load_preview_build_uses_fallback_file(self):
        with tempfile.TemporaryDirectory() as td:
            version_dir = Path(td) / "generated" / "101" / "v1"
            version_dir.mkdir(parents=True, exist_ok=True)
            fallback = {
                "status": "success",
                "dist_index": str(version_dir / "code" / "dist" / "index.html"),
            }
            (version_dir / "last_preview_build.json").write_text(
                json.dumps(fallback),
                encoding="utf-8",
            )

            self.assertEqual(runner._load_preview_build(version_dir), fallback)

    def test_ensure_backend_available_accepts_401(self):
        response = mock.Mock(status_code=401)

        with mock.patch("eval.run_componentized_validation.requests.get", return_value=response) as get_mock:
            runner._ensure_backend_available("http://127.0.0.1:5000")

        get_mock.assert_called_once_with("http://127.0.0.1:5000/api/health", timeout=5)

    def test_run_archetype_writes_result_file_on_build_error(self):
        with tempfile.TemporaryDirectory() as td:
            results_dir = Path(td)

            def fake_create_and_build_sync(*, base_url, name, description, timeout, enqueue_on_limit, queue_timeout):
                raise BuildError(
                    "simulated failure",
                    telemetry={"queue_observed": True, "queue_wait_seconds": 8.5, "max_queue_position": 3},
                )

            with mock.patch.object(runner, "_create_and_build_sync", side_effect=fake_create_and_build_sync):
                result = asyncio.run(
                    runner._run_archetype(
                        archetype="dashboard",
                        prompt=runner.PROMPTS["dashboard"],
                        results_dir=results_dir,
                        base_url="http://127.0.0.1:5000",
                        build_timeout=30,
                        enqueue_on_limit=False,
                        queue_timeout=120,
                        wait_seconds=0,
                        scorer_model="gemini-2.5-flash",
                        semaphore=asyncio.Semaphore(1),
                    )
                )

            self.assertEqual(result["score_error"], "build_failed")
            self.assertEqual(result["build_error"], "simulated failure")
            self.assertGreaterEqual(result["duration_seconds"], 0)

            result_path = results_dir / "dashboard" / "result.json"
            self.assertTrue(result_path.exists())
            written = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(written["score_error"], "build_failed")
            self.assertEqual(written["build_error"], "simulated failure")
            self.assertEqual(written["queue_telemetry"]["queue_wait_seconds"], 8.5)
            self.assertEqual(written["queue_telemetry"]["max_queue_position"], 3)

    def test_make_queue_summary_and_summary_include_aggregate_queue_metrics(self):
        results = [
            {
                "archetype": "dashboard",
                "project_id": 101,
                "version": 1,
                "scaffold_mode": "componentized",
                "preview_build": {"status": "success"},
                "preview_path": "/tmp/dashboard/index.html",
                "previous_site_path": "/tmp/baseline/index.html",
                "score": {"weighted_total": 82.0},
                "previous_best_score": 81.0,
                "previous_best_score_source": "baseline",
                "delta_vs_previous_best": 1.0,
                "queue_telemetry": {"queue_observed": True, "queue_wait_seconds": 12.5, "max_queue_position": 4},
            },
            {
                "archetype": "portfolio",
                "project_id": 102,
                "version": 1,
                "scaffold_mode": "componentized",
                "preview_build": {"status": "success"},
                "preview_path": "/tmp/portfolio/index.html",
                "previous_site_path": "/tmp/baseline-portfolio/index.html",
                "score": {"weighted_total": 80.0},
                "previous_best_score": 83.5,
                "previous_best_score_source": "baseline",
                "delta_vs_previous_best": -3.5,
                "queue_telemetry": {"queue_observed": False, "queue_wait_seconds": 0.0, "max_queue_position": None},
            },
        ]

        queue_summary = runner._make_queue_summary(results)
        summary_text = runner._make_summary(results)

        self.assertEqual(queue_summary["total_runs"], 2)
        self.assertEqual(queue_summary["observed_runs"], 1)
        self.assertEqual(queue_summary["average_queue_wait_seconds"], 12.5)
        self.assertEqual(queue_summary["max_queue_wait_seconds"], 12.5)
        self.assertEqual(queue_summary["worst_queue_position"], 4)
        self.assertIn("## Queue Overview", summary_text)
        self.assertIn("Runs with queue observed: 1/2", summary_text)
        self.assertIn("Worst queue position: 4", summary_text)


if __name__ == "__main__":
    unittest.main()
