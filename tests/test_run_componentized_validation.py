from __future__ import annotations

import asyncio
import json
import unittest
from pathlib import Path
from unittest import mock
from uuid import uuid4

from eval.api_client import BuildError
from eval import run_componentized_validation as runner

LOCAL_TMP_ROOT = runner.ROOT / ".tmp-runner-tests"


def _make_scratch_dir(name: str) -> Path:
    path = LOCAL_TMP_ROOT / f"{name}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


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
        version_dir = _make_scratch_dir("preview-fallback") / "generated" / "101" / "v1"
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
        results_dir = _make_scratch_dir("build-error")

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
                    build_only=False,
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

    def test_run_archetype_build_only_skips_screenshots_and_scoring(self):
        temp_root = _make_scratch_dir("build-only")
        results_dir = temp_root / "results"
        version_dir = temp_root / "generated" / "201" / "v1"
        version_dir.mkdir(parents=True, exist_ok=True)
        (version_dir / "last_preview_build.json").write_text(
            json.dumps(
                {
                    "status": "success",
                    "dist_index": str(version_dir / "code" / "dist" / "index.html"),
                }
            ),
            encoding="utf-8",
        )

        def fake_create_and_build_sync(*, base_url, name, description, timeout, enqueue_on_limit, queue_timeout):
            return {
                "project_id": 201,
                "version": 1,
                "preview_url": "http://127.0.0.1:5000/api/preview/201/1",
                "queue_telemetry": {"queue_observed": True, "queue_wait_seconds": 4.0, "max_queue_position": 2},
            }

        with (
            mock.patch.object(runner, "ROOT", temp_root),
            mock.patch.object(runner, "_create_and_build_sync", side_effect=fake_create_and_build_sync),
            mock.patch.object(runner, "infer_scaffold_mode", return_value="componentized"),
            mock.patch.object(runner, "Screenshotter") as screenshotter_cls,
            mock.patch.object(runner, "_score_sync") as score_sync,
        ):
            result = asyncio.run(
                runner._run_archetype(
                    archetype="dashboard",
                    prompt=runner.PROMPTS["dashboard"],
                    results_dir=results_dir,
                    base_url="http://127.0.0.1:5000",
                    build_timeout=30,
                    enqueue_on_limit=True,
                    queue_timeout=120,
                    wait_seconds=0,
                    scorer_model="gemini-2.5-flash",
                    build_only=True,
                    semaphore=asyncio.Semaphore(1),
                )
            )

        screenshotter_cls.assert_not_called()
        score_sync.assert_not_called()
        self.assertTrue(result["score_skipped"])
        self.assertEqual(result["preview_build"]["status"], "success")
        self.assertIsNone(result["delta_vs_previous_best"])
        self.assertTrue(result["build_only"])

        written = json.loads((results_dir / "dashboard" / "result.json").read_text(encoding="utf-8"))
        self.assertTrue(written["build_only"])
        self.assertTrue(written["score_skipped"])
        self.assertEqual(written["queue_telemetry"]["queue_wait_seconds"], 4.0)

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

    def test_make_summary_marks_build_only_results_as_skipped(self):
        summary_text = runner._make_summary(
            [
                {
                    "archetype": "dashboard",
                    "project_id": 101,
                    "version": 1,
                    "build_only": True,
                    "scaffold_mode": "componentized",
                    "preview_build": {"status": "success"},
                    "preview_path": "/tmp/dashboard/index.html",
                    "previous_site_path": "/tmp/baseline/index.html",
                    "score_skipped": True,
                    "previous_best_score": 81.0,
                    "previous_best_score_source": "baseline",
                    "delta_vs_previous_best": None,
                    "queue_telemetry": {"queue_observed": True, "queue_wait_seconds": 7.0, "max_queue_position": 2},
                }
            ]
        )

        self.assertIn("Mode: build-only", summary_text)
        self.assertIn("New score: skipped (build-only mode)", summary_text)


if __name__ == "__main__":
    unittest.main()
