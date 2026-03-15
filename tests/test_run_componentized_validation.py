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

            def fake_create_and_build_sync(*, base_url, name, description, timeout):
                raise BuildError("simulated failure")

            with mock.patch.object(runner, "_create_and_build_sync", side_effect=fake_create_and_build_sync):
                result = asyncio.run(
                    runner._run_archetype(
                        archetype="dashboard",
                        prompt=runner.PROMPTS["dashboard"],
                        results_dir=results_dir,
                        base_url="http://127.0.0.1:5000",
                        build_timeout=30,
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


if __name__ == "__main__":
    unittest.main()
