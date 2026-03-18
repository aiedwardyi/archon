from __future__ import annotations

import unittest
from unittest import mock

from eval.api_client import BuilderAPI, BuildError


def _response(payload: dict) -> mock.Mock:
    response = mock.Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


class BuilderAPITests(unittest.TestCase):
    def _make_api(self) -> BuilderAPI:
        api = object.__new__(BuilderAPI)
        api.base_url = "http://127.0.0.1:5000"
        api.session = mock.Mock()
        return api

    def test_poll_until_done_allows_queue_wait_before_active_timeout(self):
        api = self._make_api()
        api.session.get.side_effect = [
            _response({"status": "RUNNING", "currentStage": "pm", "project_queued": True, "queue_position": 2}),
            _response({"status": "RUNNING", "currentStage": "planner", "project_queued": False, "queue_position": None}),
            _response({"status": "COMPLETED", "currentStage": "engineer", "project_queued": False, "queue_position": None}),
        ]

        result = api.poll_until_done(project_id=101, timeout=1, queue_timeout=5, poll_interval=0)

        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(api.session.get.call_count, 3)
        self.assertTrue(result["queue_telemetry"]["queue_observed"])
        self.assertEqual(result["queue_telemetry"]["max_queue_position"], 2)

    def test_poll_until_done_raises_after_queue_timeout(self):
        api = self._make_api()
        api.session.get.return_value = _response(
            {"status": "RUNNING", "currentStage": "pm", "project_queued": True, "queue_position": 3}
        )

        current_time = {"value": 0.0}

        def fake_time() -> float:
            return current_time["value"]

        def fake_sleep(seconds: float) -> None:
            current_time["value"] += seconds

        with (
            mock.patch("eval.api_client.time.time", side_effect=fake_time),
            mock.patch("eval.api_client.time.sleep", side_effect=fake_sleep),
        ):
            with self.assertRaises(BuildError) as ctx:
                api.poll_until_done(project_id=101, timeout=30, queue_timeout=1, poll_interval=0.5)

        self.assertIn("queued", str(ctx.exception))
        self.assertEqual(ctx.exception.telemetry["max_queue_position"], 3)
        self.assertTrue(ctx.exception.telemetry["queue_observed"])

    def test_create_and_build_merges_trigger_and_poll_queue_telemetry(self):
        api = self._make_api()
        api.create_project = mock.Mock(return_value=101)
        api.trigger_build = mock.Mock(
            return_value={
                "project_id": 101,
                "execution_id": 12,
                "version": 3,
                "trigger_status": "queued",
                "initial_queue_position": 4,
                "trigger_scheduler": {"project_queued": True, "queued_pipelines": 4, "active_pipelines": 2},
            }
        )
        api.poll_until_done = mock.Mock(
            return_value={
                "status": "COMPLETED",
                "queue_telemetry": {
                    "queue_observed": True,
                    "queue_wait_seconds": 12.5,
                    "max_queue_position": 4,
                    "active_duration_seconds": 34.0,
                },
            }
        )

        result = api.create_and_build(
            name="Queued Build",
            description="Build a dashboard",
            timeout=30,
            queue_timeout=120,
            enqueue_on_limit=True,
        )

        api.poll_until_done.assert_called_once_with(
            project_id=101,
            timeout=30,
            queue_timeout=120,
            started_queued=True,
            initial_queue_position=4,
        )
        self.assertEqual(result["queue_telemetry"]["trigger_status"], "queued")
        self.assertEqual(result["queue_telemetry"]["initial_queue_position"], 4)
        self.assertEqual(result["queue_telemetry"]["queue_wait_seconds"], 12.5)


if __name__ == "__main__":
    unittest.main()
