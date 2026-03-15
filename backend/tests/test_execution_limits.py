import os
import sys
import unittest
import uuid
import json
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import (
    app,
    execution_state,
    pipeline_queue,
    recover_pending_pipeline_jobs,
    release_and_dispatch_pipeline_slot,
)
from models import Execution, Project, User, get_session


TEST_PASSWORD = "testpass123"


def _register_user(client):
    email = f"limits-{uuid.uuid4().hex[:12]}@archon-test.com"
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": TEST_PASSWORD,
            "name": "Execution Limit Test",
        },
    )
    if response.status_code != 201:
        raise AssertionError(response.get_data(as_text=True))
    data = response.get_json()
    return data["token"], data["user"]["id"], email


def _create_project(client, token: str, name: str, description: str = "") -> int:
    response = client.post(
        "/api/projects",
        json={"name": name, "description": description},
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code != 201:
        raise AssertionError(response.get_data(as_text=True))
    return response.get_json()["id"]


def _running_state(execution_id: int) -> dict:
    return {
        "running": True,
        "queued": False,
        "started_at": 123.0,
        "queued_at": None,
        "current_execution_id": execution_id,
        "logs": [],
        "result_ready": False,
    }


def _queued_state(execution_id: int) -> dict:
    return {
        "running": False,
        "queued": True,
        "started_at": None,
        "queued_at": 456.0,
        "current_execution_id": execution_id,
        "logs": [],
        "result_ready": False,
    }


class ExecutionLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.token, cls.user_id, cls.email = _register_user(cls.client)

    @classmethod
    def tearDownClass(cls):
        db = get_session()
        try:
            user = db.get(User, cls.user_id)
            if user:
                db.query(Execution).filter(Execution.owner_id == user.id).delete(synchronize_session=False)
                db.query(Project).filter(Project.owner_id == user.id).delete(synchronize_session=False)
                db.delete(user)
                db.commit()
        finally:
            db.close()

    def setUp(self):
        db = get_session()
        try:
            db.query(Execution).filter(Execution.owner_id == self.user_id).delete(synchronize_session=False)
            db.query(Project).filter(Project.owner_id == self.user_id).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()
        execution_state.clear()
        pipeline_queue.clear()
        self._old_worker_limit = os.environ.get("ARCHON_MAX_CONCURRENT_PIPELINES")

    def tearDown(self):
        execution_state.clear()
        pipeline_queue.clear()
        if self._old_worker_limit is None:
            os.environ.pop("ARCHON_MAX_CONCURRENT_PIPELINES", None)
        else:
            os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = self._old_worker_limit

    def test_execute_task_rejects_same_project_overlap(self):
        project_id = _create_project(self.client, self.token, "Overlap Guard Project", "Build a dashboard")
        execution_state[project_id] = _running_state(999)

        response = self.client.post(
            "/api/execute-task",
            json={"project_id": project_id},
            headers={"Authorization": f"Bearer {self.token}"},
        )

        self.assertEqual(response.status_code, 409)
        payload = response.get_json()
        self.assertEqual(payload["reason"], "project_running")
        self.assertEqual(payload["project_id"], project_id)
        self.assertTrue(payload["project_running"])
        self.assertEqual(payload["active_pipelines"], 1)

        db = get_session()
        try:
            executions = db.query(Execution).filter(Execution.project_id == project_id).count()
            self.assertEqual(executions, 0)
        finally:
            db.close()

    def test_execute_task_rejects_when_global_worker_limit_is_full(self):
        running_project_id = _create_project(self.client, self.token, "Running Project")
        blocked_project_id = _create_project(self.client, self.token, "Blocked Project", "Build a portfolio")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        execution_state[running_project_id] = _running_state(1001)

        response = self.client.post(
            "/api/execute-task",
            json={"project_id": blocked_project_id},
            headers={"Authorization": f"Bearer {self.token}"},
        )

        self.assertEqual(response.status_code, 429)
        payload = response.get_json()
        self.assertEqual(payload["reason"], "worker_limit")
        self.assertEqual(payload["active_pipelines"], 1)
        self.assertEqual(payload["max_concurrent_pipelines"], 1)
        self.assertEqual(payload["project_id"], blocked_project_id)
        self.assertFalse(payload["project_running"])

        db = get_session()
        try:
            executions = db.query(Execution).filter(Execution.project_id == blocked_project_id).count()
            self.assertEqual(executions, 0)
        finally:
            db.close()

    def test_iterate_rejects_when_global_worker_limit_is_full(self):
        running_project_id = _create_project(self.client, self.token, "Running Iterate Project")
        blocked_project_id = _create_project(self.client, self.token, "Blocked Iterate Project")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        execution_state[running_project_id] = _running_state(1002)

        response = self.client.post(
            f"/api/projects/{blocked_project_id}/iterate",
            json={"prompt": "Tighten the spacing and improve the visual hierarchy."},
            headers={"Authorization": f"Bearer {self.token}"},
        )

        self.assertEqual(response.status_code, 429)
        payload = response.get_json()
        self.assertEqual(payload["reason"], "worker_limit")
        self.assertEqual(payload["active_pipelines"], 1)
        self.assertEqual(payload["max_concurrent_pipelines"], 1)
        self.assertEqual(payload["project_id"], blocked_project_id)
        self.assertFalse(payload["project_running"])

        db = get_session()
        try:
            executions = db.query(Execution).filter(Execution.project_id == blocked_project_id).count()
            self.assertEqual(executions, 0)
        finally:
            db.close()

    def test_execute_task_queues_when_global_worker_limit_is_full_and_requested(self):
        running_project_id = _create_project(self.client, self.token, "Running Queue Project")
        queued_project_id = _create_project(self.client, self.token, "Queued Project", "Build a portfolio")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        execution_state[running_project_id] = _running_state(1003)

        response = self.client.post(
            "/api/execute-task",
            json={"project_id": queued_project_id, "enqueue_on_limit": True},
            headers={"Authorization": f"Bearer {self.token}"},
        )

        self.assertEqual(response.status_code, 202)
        payload = response.get_json()
        self.assertEqual(payload["status"], "queued")
        self.assertEqual(payload["project_id"], queued_project_id)
        self.assertEqual(payload["queue_position"], 1)
        self.assertEqual(payload["active_pipelines"], 1)
        self.assertEqual(payload["queued_pipelines"], 1)
        self.assertEqual(payload["max_concurrent_pipelines"], 1)
        self.assertFalse(payload["project_running"])
        self.assertTrue(payload["project_queued"])

        db = get_session()
        try:
            execution = (
                db.query(Execution)
                .filter(Execution.project_id == queued_project_id)
                .order_by(Execution.id.desc())
                .first()
            )
            self.assertIsNotNone(execution)
            self.assertEqual(execution.status, "pending")
        finally:
            db.close()

        status_response = self.client.get(
            "/api/execution-status",
            query_string={"project_id": queued_project_id},
        )
        self.assertEqual(status_response.status_code, 200)
        status_payload = status_response.get_json()
        self.assertEqual(status_payload["status"], "RUNNING")
        self.assertEqual(status_payload["currentStage"], "pm")
        self.assertTrue(status_payload["project_queued"])
        self.assertEqual(status_payload["queue_position"], 1)

    def test_release_and_dispatch_pipeline_slot_starts_next_queued_job(self):
        running_project_id = _create_project(self.client, self.token, "Active Dispatch Project")
        queued_project_id = _create_project(self.client, self.token, "Queued Dispatch Project")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        execution_state[running_project_id] = _running_state(1004)
        execution_state[queued_project_id] = _queued_state(1005)
        pipeline_queue.append({
            "project_id": queued_project_id,
            "execution_id": 1005,
            "version": 1,
            "task_description": "Build a dashboard",
            "prompt_history": [{"role": "user", "content": "Build a dashboard"}],
            "reference_images": None,
            "nlu_result": {"intent": "build"},
        })

        with mock.patch("app.start_pipeline_job") as start_job:
            release_and_dispatch_pipeline_slot(running_project_id)

        start_job.assert_called_once()
        self.assertEqual(start_job.call_args.args[0]["project_id"], queued_project_id)
        self.assertTrue(start_job.call_args.kwargs["from_queue"])
        self.assertFalse(execution_state[running_project_id]["running"])
        self.assertTrue(execution_state[queued_project_id]["running"])
        self.assertFalse(execution_state[queued_project_id]["queued"])
        self.assertEqual(len(pipeline_queue), 0)

    def test_recover_pending_pipeline_jobs_requeues_pending_execution(self):
        project_id = _create_project(self.client, self.token, "Recovered Queue Project", "Build a recovery dashboard")

        db = get_session()
        try:
            project = db.get(Project, project_id)
            project.status = "in_progress"
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a recovery dashboard"}]),
                is_active_head=True,
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            execution_id = execution.id
        finally:
            db.close()

        with mock.patch("app.start_pipeline_job") as start_job:
            recovered = recover_pending_pipeline_jobs()

        self.assertEqual(recovered, 1)
        start_job.assert_called_once()
        job = start_job.call_args.args[0]
        self.assertEqual(job["project_id"], project_id)
        self.assertEqual(job["execution_id"], execution_id)
        self.assertEqual(job["task_description"], "Build a recovery dashboard")
        self.assertTrue(start_job.call_args.kwargs["from_queue"])
        self.assertTrue(execution_state[project_id]["running"])
        self.assertFalse(execution_state[project_id]["queued"])
        self.assertEqual(execution_state[project_id]["current_execution_id"], execution_id)
        self.assertEqual(len(pipeline_queue), 0)


if __name__ == "__main__":
    unittest.main()
