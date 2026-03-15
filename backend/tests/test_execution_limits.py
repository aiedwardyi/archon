import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app, execution_state
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
        execution_state.clear()
        self._old_worker_limit = os.environ.get("ARCHON_MAX_CONCURRENT_PIPELINES")

    def tearDown(self):
        execution_state.clear()
        if self._old_worker_limit is None:
            os.environ.pop("ARCHON_MAX_CONCURRENT_PIPELINES", None)
        else:
            os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = self._old_worker_limit

    def test_execute_task_rejects_same_project_overlap(self):
        project_id = _create_project(self.client, self.token, "Overlap Guard Project", "Build a dashboard")
        execution_state[project_id] = {
            "running": True,
            "started_at": 123.0,
            "current_execution_id": 999,
            "logs": [],
            "result_ready": False,
        }

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

        execution_state[running_project_id] = {
            "running": True,
            "started_at": 123.0,
            "current_execution_id": 1001,
            "logs": [],
            "result_ready": False,
        }

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

        execution_state[running_project_id] = {
            "running": True,
            "started_at": 123.0,
            "current_execution_id": 1002,
            "logs": [],
            "result_ready": False,
        }

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


if __name__ == "__main__":
    unittest.main()
