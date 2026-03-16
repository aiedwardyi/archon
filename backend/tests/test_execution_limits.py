import os
import sys
import unittest
import uuid
import json
from datetime import timedelta
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import (
    SCHEDULER_WORKER_ID,
    app,
    claim_execution_for_pipeline_start,
    dispatch_queued_pipelines,
    execution_state,
    get_version_dir,
    pipeline_queue,
    recover_pending_pipeline_jobs,
    recover_stale_running_executions,
    release_and_dispatch_pipeline_slot,
    run_scheduler_maintenance_once,
    start_pipeline_job,
    try_claim_execution_for_run,
    utcnow_naive,
)
from models import Execution, Project, User, get_session
from models import PipelineSlotLease


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


def _cleanup_test_users(*, exclude_user_id: int | None = None) -> None:
    db = get_session()
    try:
        users = db.query(User).filter(User.email.like("limits-%@archon-test.com")).all()
        users = [user for user in users if exclude_user_id is None or user.id != exclude_user_id]
        if not users:
            db.rollback()
            return

        user_ids = [user.id for user in users]
        execution_ids = [
            execution_id
            for (execution_id,) in db.query(Execution.id).filter(Execution.owner_id.in_(user_ids)).all()
        ]
        if execution_ids:
            db.query(PipelineSlotLease).filter(PipelineSlotLease.execution_id.in_(execution_ids)).delete(synchronize_session=False)
        db.query(Execution).filter(Execution.owner_id.in_(user_ids)).delete(synchronize_session=False)
        db.query(Project).filter(Project.owner_id.in_(user_ids)).delete(synchronize_session=False)
        for user in users:
            managed_user = db.get(User, user.id)
            if managed_user:
                db.delete(managed_user)
        db.commit()
    finally:
        db.close()


def _running_state(execution_id: int) -> dict:
    return {
        "running": True,
        "queued": False,
        "started_at": 123.0,
        "queued_at": None,
        "last_heartbeat_at": None,
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
        "last_heartbeat_at": None,
        "current_execution_id": execution_id,
        "logs": [],
        "result_ready": False,
    }


class ExecutionLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _cleanup_test_users()
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.token, cls.user_id, cls.email = _register_user(cls.client)

    @classmethod
    def tearDownClass(cls):
        _cleanup_test_users()
        db = get_session()
        try:
            user = db.get(User, cls.user_id)
            if user:
                execution_ids = [
                    execution_id
                    for (execution_id,) in db.query(Execution.id).filter(Execution.owner_id == user.id).all()
                ]
                if execution_ids:
                    db.query(PipelineSlotLease).filter(PipelineSlotLease.execution_id.in_(execution_ids)).delete(synchronize_session=False)
                db.query(Execution).filter(Execution.owner_id == user.id).delete(synchronize_session=False)
                db.query(Project).filter(Project.owner_id == user.id).delete(synchronize_session=False)
                db.delete(user)
                db.commit()
        finally:
            db.close()

    def setUp(self):
        _cleanup_test_users(exclude_user_id=self.user_id)
        db = get_session()
        try:
            execution_ids = [
                execution_id
                for (execution_id,) in db.query(Execution.id).filter(Execution.owner_id == self.user_id).all()
            ]
            if execution_ids:
                db.query(PipelineSlotLease).filter(PipelineSlotLease.execution_id.in_(execution_ids)).delete(synchronize_session=False)
            db.query(Execution).filter(Execution.owner_id == self.user_id).delete(synchronize_session=False)
            db.query(Project).filter(Project.owner_id == self.user_id).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()
        execution_state.clear()
        pipeline_queue.clear()
        self._old_worker_limit = os.environ.get("ARCHON_MAX_CONCURRENT_PIPELINES")
        self._old_queue_limit = os.environ.get("ARCHON_MAX_QUEUED_PIPELINES")
        self._old_stale_timeout = os.environ.get("ARCHON_EXECUTION_STALE_TIMEOUT_SECONDS")

    def tearDown(self):
        execution_state.clear()
        pipeline_queue.clear()
        if self._old_worker_limit is None:
            os.environ.pop("ARCHON_MAX_CONCURRENT_PIPELINES", None)
        else:
            os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = self._old_worker_limit
        if self._old_queue_limit is None:
            os.environ.pop("ARCHON_MAX_QUEUED_PIPELINES", None)
        else:
            os.environ["ARCHON_MAX_QUEUED_PIPELINES"] = self._old_queue_limit
        if self._old_stale_timeout is None:
            os.environ.pop("ARCHON_EXECUTION_STALE_TIMEOUT_SECONDS", None)
        else:
            os.environ["ARCHON_EXECUTION_STALE_TIMEOUT_SECONDS"] = self._old_stale_timeout

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

    def test_execute_task_rejects_same_project_overlap_from_db_running_execution(self):
        project_id = _create_project(self.client, self.token, "DB Running Overlap Project", "Build a dashboard")

        db = get_session()
        try:
            project = db.get(Project, project_id)
            project.status = "running"
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="running",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a dashboard"}]),
                is_active_head=True,
                scheduler_worker_id="remote-worker",
                scheduler_claimed_at=utcnow_naive(),
                scheduler_heartbeat_at=utcnow_naive(),
            )
            db.add(execution)
            db.commit()
        finally:
            db.close()

        response = self.client.post(
            "/api/execute-task",
            json={"project_id": project_id},
            headers={"Authorization": f"Bearer {self.token}"},
        )

        self.assertEqual(response.status_code, 409)
        payload = response.get_json()
        self.assertEqual(payload["reason"], "project_running")
        self.assertTrue(payload["project_running"])
        self.assertEqual(payload["active_pipelines"], 1)

    def test_execute_task_rejects_same_project_overlap_from_db_pending_execution(self):
        project_id = _create_project(self.client, self.token, "DB Pending Overlap Project", "Build a dashboard")

        db = get_session()
        try:
            project = db.get(Project, project_id)
            project.status = "in_progress"
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a dashboard"}]),
                is_active_head=True,
            )
            db.add(execution)
            db.commit()
        finally:
            db.close()

        response = self.client.post(
            "/api/execute-task",
            json={"project_id": project_id},
            headers={"Authorization": f"Bearer {self.token}"},
        )

        self.assertEqual(response.status_code, 409)
        payload = response.get_json()
        self.assertEqual(payload["reason"], "project_queued")
        self.assertTrue(payload["project_queued"])
        self.assertEqual(payload["queued_pipelines"], 1)
        self.assertEqual(payload["queue_position"], 1)

    def test_execute_task_rejects_same_project_overlap_from_slot_leased_pending_execution(self):
        project_id = _create_project(self.client, self.token, "Slot Leased Overlap Project", "Build a dashboard")

        db = get_session()
        try:
            project = db.get(Project, project_id)
            project.status = "in_progress"
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a dashboard"}]),
                is_active_head=True,
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            db.add(PipelineSlotLease(
                slot_index=1,
                execution_id=execution.id,
                worker_id="remote-worker",
                claimed_at=utcnow_naive(),
                heartbeat_at=utcnow_naive(),
            ))
            db.commit()
        finally:
            db.close()

        response = self.client.post(
            "/api/execute-task",
            json={"project_id": project_id},
            headers={"Authorization": f"Bearer {self.token}"},
        )

        self.assertEqual(response.status_code, 409)
        payload = response.get_json()
        self.assertEqual(payload["reason"], "project_running")
        self.assertTrue(payload["project_running"])
        self.assertFalse(payload["project_queued"])
        self.assertEqual(payload["active_pipelines"], 1)

    def test_execute_task_restores_execution_when_startup_fails_before_thread_launch(self):
        project_id = _create_project(self.client, self.token, "Startup Failure Project", "Build a startup-safe dashboard")

        with mock.patch("app.start_pipeline_job", return_value=False):
            response = self.client.post(
                "/api/execute-task",
                json={"project_id": project_id},
                headers={"Authorization": f"Bearer {self.token}"},
            )

        self.assertEqual(response.status_code, 429)
        payload = response.get_json()
        self.assertEqual(payload["reason"], "worker_limit")
        self.assertEqual(payload["project_id"], project_id)
        self.assertEqual(payload["active_pipelines"], 0)

        project_state = execution_state[project_id]
        self.assertFalse(project_state["running"])
        self.assertFalse(project_state["queued"])
        self.assertIsNone(project_state["current_execution_id"])

        db = get_session()
        try:
            executions = db.query(Execution).filter(Execution.project_id == project_id).count()
            self.assertEqual(executions, 0)
            project = db.get(Project, project_id)
            self.assertIsNotNone(project)
            self.assertEqual(project.status, "pending")
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

    def test_execute_task_rejects_when_global_worker_limit_is_full_from_db_running_execution(self):
        running_project_id = _create_project(self.client, self.token, "DB Running Project")
        blocked_project_id = _create_project(self.client, self.token, "DB Blocked Project", "Build a portfolio")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        db = get_session()
        try:
            running_project = db.get(Project, running_project_id)
            running_project.status = "running"
            execution = Execution(
                project_id=running_project_id,
                owner_id=running_project.owner_id,
                status="running",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a portfolio"}]),
                is_active_head=True,
                scheduler_worker_id="remote-worker",
                scheduler_claimed_at=utcnow_naive(),
                scheduler_heartbeat_at=utcnow_naive(),
            )
            db.add(execution)
            db.commit()
        finally:
            db.close()

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
        self.assertFalse(payload["project_running"])

        db = get_session()
        try:
            executions = db.query(Execution).filter(Execution.project_id == blocked_project_id).count()
            self.assertEqual(executions, 0)
        finally:
            db.close()

    def test_execute_task_rejects_when_global_worker_limit_is_full_from_db_slot_lease(self):
        running_project_id = _create_project(self.client, self.token, "DB Slot Lease Project")
        blocked_project_id = _create_project(self.client, self.token, "DB Slot Lease Blocked Project", "Build a portfolio")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        db = get_session()
        try:
            running_project = db.get(Project, running_project_id)
            running_project.status = "in_progress"
            execution = Execution(
                project_id=running_project_id,
                owner_id=running_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a portfolio"}]),
                is_active_head=True,
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            db.add(PipelineSlotLease(
                slot_index=1,
                execution_id=execution.id,
                worker_id="remote-worker",
                claimed_at=utcnow_naive(),
                heartbeat_at=utcnow_naive(),
            ))
            db.commit()
        finally:
            db.close()

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

    def test_release_and_dispatch_pipeline_slot_adopts_pending_database_execution(self):
        running_project_id = _create_project(self.client, self.token, "Running Durable Queue Project")
        adopted_project_id = _create_project(self.client, self.token, "Adopted Durable Queue Project", "Build a shared queue dashboard")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        db = get_session()
        try:
            project = db.get(Project, adopted_project_id)
            project.status = "in_progress"
            execution = Execution(
                project_id=adopted_project_id,
                owner_id=project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a shared queue dashboard"}]),
                is_active_head=True,
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            execution_id = execution.id
        finally:
            db.close()

        execution_state[running_project_id] = _running_state(1201)

        with mock.patch("app.start_pipeline_job") as start_job:
            release_and_dispatch_pipeline_slot(running_project_id)

        start_job.assert_called_once()
        self.assertEqual(start_job.call_args.args[0]["project_id"], adopted_project_id)
        self.assertEqual(start_job.call_args.args[0]["execution_id"], execution_id)
        self.assertTrue(start_job.call_args.kwargs["from_queue"])
        self.assertFalse(execution_state[running_project_id]["running"])
        self.assertTrue(execution_state[adopted_project_id]["running"])
        self.assertFalse(execution_state[adopted_project_id]["queued"])
        self.assertEqual(len(pipeline_queue), 0)

    def test_dispatch_queued_pipelines_respects_db_running_worker_limit(self):
        running_project_id = _create_project(self.client, self.token, "DB Running Dispatch Project")
        queued_project_id = _create_project(self.client, self.token, "Queued Dispatch Project", "Build a queue-safe dashboard")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        db = get_session()
        try:
            running_project = db.get(Project, running_project_id)
            running_project.status = "running"
            running_execution = Execution(
                project_id=running_project_id,
                owner_id=running_project.owner_id,
                status="running",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a queue-safe dashboard"}]),
                is_active_head=True,
                scheduler_worker_id="remote-worker",
                scheduler_claimed_at=utcnow_naive(),
                scheduler_heartbeat_at=utcnow_naive(),
            )
            db.add(running_execution)

            queued_project = db.get(Project, queued_project_id)
            queued_project.status = "in_progress"
            queued_execution = Execution(
                project_id=queued_project_id,
                owner_id=queued_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a queue-safe dashboard"}]),
                is_active_head=True,
            )
            db.add(queued_execution)
            db.commit()
            db.refresh(queued_execution)
            queued_execution_id = queued_execution.id
            queued_created_at = queued_execution.created_at
        finally:
            db.close()

        execution_state[queued_project_id] = _queued_state(queued_execution_id)
        pipeline_queue.append({
            "project_id": queued_project_id,
            "execution_id": queued_execution_id,
            "version": 1,
            "task_description": "Build a queue-safe dashboard",
            "prompt_history": [{"role": "user", "content": "Build a queue-safe dashboard"}],
            "reference_images": None,
            "nlu_result": {"intent": "build"},
            "created_at": queued_created_at,
        })

        with mock.patch("app.start_pipeline_job") as start_job:
            dispatched = dispatch_queued_pipelines()

        self.assertEqual(dispatched, 0)
        start_job.assert_not_called()
        self.assertTrue(execution_state[queued_project_id]["queued"])
        self.assertFalse(execution_state[queued_project_id]["running"])
        self.assertEqual(len(pipeline_queue), 1)
        self.assertEqual(pipeline_queue[0]["project_id"], queued_project_id)

    def test_dispatch_queued_pipelines_adopts_db_pending_execution_without_local_queue_seed(self):
        pending_project_id = _create_project(self.client, self.token, "Direct Durable Dispatch Project", "Build a queue-safe dashboard")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        db = get_session()
        try:
            pending_project = db.get(Project, pending_project_id)
            pending_project.status = "in_progress"
            pending_execution = Execution(
                project_id=pending_project_id,
                owner_id=pending_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a queue-safe dashboard"}]),
                is_active_head=True,
            )
            db.add(pending_execution)
            db.commit()
            db.refresh(pending_execution)
            pending_execution_id = pending_execution.id
        finally:
            db.close()

        with mock.patch("app.start_pipeline_job") as start_job:
            dispatched = dispatch_queued_pipelines()

        self.assertEqual(dispatched, 1)
        start_job.assert_called_once()
        self.assertEqual(start_job.call_args.args[0]["project_id"], pending_project_id)
        self.assertEqual(start_job.call_args.args[0]["execution_id"], pending_execution_id)
        self.assertTrue(start_job.call_args.kwargs["from_queue"])
        self.assertTrue(execution_state[pending_project_id]["running"])
        self.assertFalse(execution_state[pending_project_id]["queued"])
        self.assertEqual(len(pipeline_queue), 0)

    def test_dispatch_queued_pipelines_recovers_missing_local_queue_entry_for_same_execution(self):
        queued_project_id = _create_project(self.client, self.token, "Queue Drift Recovery Project", "Build a queue-safe dashboard")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        db = get_session()
        try:
            queued_project = db.get(Project, queued_project_id)
            queued_project.status = "in_progress"
            queued_execution = Execution(
                project_id=queued_project_id,
                owner_id=queued_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a queue-safe dashboard"}]),
                is_active_head=True,
            )
            db.add(queued_execution)
            db.commit()
            db.refresh(queued_execution)
            queued_execution_id = queued_execution.id
        finally:
            db.close()

        execution_state[queued_project_id] = _queued_state(queued_execution_id)

        with mock.patch("app.start_pipeline_job") as start_job:
            dispatched = dispatch_queued_pipelines()

        self.assertEqual(dispatched, 1)
        start_job.assert_called_once()
        self.assertEqual(start_job.call_args.args[0]["project_id"], queued_project_id)
        self.assertEqual(start_job.call_args.args[0]["execution_id"], queued_execution_id)
        self.assertTrue(start_job.call_args.kwargs["from_queue"])
        self.assertTrue(execution_state[queued_project_id]["running"])
        self.assertFalse(execution_state[queued_project_id]["queued"])
        self.assertEqual(len(pipeline_queue), 0)

    def test_dispatch_queued_pipelines_prefers_oldest_db_pending_over_newer_local_queue_entry(self):
        older_project_id = _create_project(self.client, self.token, "Direct Older Durable Project", "Build the older dashboard")
        newer_project_id = _create_project(self.client, self.token, "Direct Newer Local Project", "Build the newer dashboard")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        db = get_session()
        try:
            older_project = db.get(Project, older_project_id)
            older_project.status = "in_progress"
            older_execution = Execution(
                project_id=older_project_id,
                owner_id=older_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build the older dashboard"}]),
                is_active_head=True,
            )
            db.add(older_execution)
            db.commit()
            db.refresh(older_execution)

            newer_project = db.get(Project, newer_project_id)
            newer_project.status = "in_progress"
            newer_execution = Execution(
                project_id=newer_project_id,
                owner_id=newer_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build the newer dashboard"}]),
                is_active_head=True,
            )
            db.add(newer_execution)
            db.commit()
            db.refresh(newer_execution)
            older_execution_id = older_execution.id
            newer_execution_id = newer_execution.id
            newer_created_at = newer_execution.created_at
        finally:
            db.close()

        execution_state[newer_project_id] = _queued_state(newer_execution_id)
        pipeline_queue.append({
            "project_id": newer_project_id,
            "execution_id": newer_execution_id,
            "version": 1,
            "task_description": "Build the newer dashboard",
            "prompt_history": [{"role": "user", "content": "Build the newer dashboard"}],
            "reference_images": None,
            "nlu_result": {"intent": "build"},
            "created_at": newer_created_at,
        })

        with mock.patch("app.start_pipeline_job") as start_job:
            dispatched = dispatch_queued_pipelines()

        self.assertEqual(dispatched, 1)
        start_job.assert_called_once()
        self.assertEqual(start_job.call_args.args[0]["project_id"], older_project_id)
        self.assertEqual(start_job.call_args.args[0]["execution_id"], older_execution_id)
        self.assertTrue(start_job.call_args.kwargs["from_queue"])
        self.assertTrue(execution_state[older_project_id]["running"])
        self.assertFalse(execution_state[older_project_id]["queued"])
        self.assertTrue(execution_state[newer_project_id]["queued"])
        self.assertEqual(len(pipeline_queue), 1)
        self.assertEqual(pipeline_queue[0]["project_id"], newer_project_id)

    def test_run_scheduler_maintenance_once_recovers_stale_and_adopts_pending_work(self):
        stale_project_id = _create_project(self.client, self.token, "Stale Poller Project", "Build a stale-run dashboard")
        adopted_project_id = _create_project(self.client, self.token, "Poller Adoption Project", "Build a background queue dashboard")
        os.environ["ARCHON_EXECUTION_STALE_TIMEOUT_SECONDS"] = "60"

        db = get_session()
        try:
            stale_project = db.get(Project, stale_project_id)
            stale_project.status = "running"
            stale_execution = Execution(
                project_id=stale_project_id,
                owner_id=stale_project.owner_id,
                status="running",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a stale-run dashboard"}]),
                is_active_head=True,
                scheduler_worker_id="stale-worker",
                scheduler_claimed_at=utcnow_naive() - timedelta(seconds=180),
                scheduler_heartbeat_at=utcnow_naive() - timedelta(seconds=180),
            )
            db.add(stale_execution)

            adopted_project = db.get(Project, adopted_project_id)
            adopted_project.status = "in_progress"
            adopted_execution = Execution(
                project_id=adopted_project_id,
                owner_id=adopted_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a background queue dashboard"}]),
                is_active_head=True,
            )
            db.add(adopted_execution)
            db.commit()
            db.refresh(stale_execution)
            db.refresh(adopted_execution)
            stale_execution_id = stale_execution.id
            adopted_execution_id = adopted_execution.id
        finally:
            db.close()

        with mock.patch("app.start_pipeline_job") as start_job:
            result = run_scheduler_maintenance_once(source="background poll", recover_stale=True)

        self.assertEqual(result["local_dispatched"], 1)
        self.assertEqual(result["stale_recovered"], 1)
        self.assertEqual(result["pending_adopted"], 1)
        start_job.assert_called_once()
        self.assertEqual(start_job.call_args.args[0]["project_id"], adopted_project_id)
        self.assertEqual(start_job.call_args.args[0]["execution_id"], adopted_execution_id)
        self.assertTrue(start_job.call_args.kwargs["from_queue"])
        self.assertTrue(execution_state[adopted_project_id]["running"])
        self.assertFalse(execution_state[adopted_project_id]["queued"])

        db = get_session()
        try:
            stale_execution = db.get(Execution, stale_execution_id)
            stale_project = db.get(Project, stale_project_id)
            self.assertIsNotNone(stale_execution)
            self.assertEqual(stale_execution.status, "failed")
            self.assertIsNotNone(stale_project)
            self.assertEqual(stale_project.status, "failed")
        finally:
            db.close()

    def test_run_scheduler_maintenance_once_skips_pending_adoption_when_db_running_at_worker_limit(self):
        running_project_id = _create_project(self.client, self.token, "Maintenance DB Running Project")
        pending_project_id = _create_project(self.client, self.token, "Maintenance Deferred Pending Project", "Build a queue-safe dashboard")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        db = get_session()
        try:
            running_project = db.get(Project, running_project_id)
            running_project.status = "running"
            running_execution = Execution(
                project_id=running_project_id,
                owner_id=running_project.owner_id,
                status="running",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a queue-safe dashboard"}]),
                is_active_head=True,
                scheduler_worker_id="remote-worker",
                scheduler_claimed_at=utcnow_naive(),
                scheduler_heartbeat_at=utcnow_naive(),
            )
            db.add(running_execution)

            pending_project = db.get(Project, pending_project_id)
            pending_project.status = "in_progress"
            pending_execution = Execution(
                project_id=pending_project_id,
                owner_id=pending_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a queue-safe dashboard"}]),
                is_active_head=True,
            )
            db.add(pending_execution)
            db.commit()
            db.refresh(pending_execution)
            pending_execution_id = pending_execution.id
        finally:
            db.close()

        with mock.patch("app.start_pipeline_job") as start_job:
            result = run_scheduler_maintenance_once(source="background poll", recover_stale=False)

        self.assertEqual(result["stale_recovered"], 0)
        self.assertEqual(result["pending_adopted"], 0)
        self.assertEqual(result["local_dispatched"], 0)
        start_job.assert_not_called()
        self.assertEqual(len(pipeline_queue), 0)
        self.assertEqual(execution_state, {})

        db = get_session()
        try:
            pending_execution = db.get(Execution, pending_execution_id)
            self.assertEqual(pending_execution.status, "pending")
        finally:
            db.close()

    def test_run_scheduler_maintenance_once_prioritizes_oldest_db_pending_execution(self):
        older_project_id = _create_project(self.client, self.token, "Older Durable Queue Project", "Build the older dashboard")
        newer_project_id = _create_project(self.client, self.token, "Newer Local Queue Project", "Build the newer dashboard")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        db = get_session()
        try:
            older_project = db.get(Project, older_project_id)
            older_project.status = "in_progress"
            older_execution = Execution(
                project_id=older_project_id,
                owner_id=older_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build the older dashboard"}]),
                is_active_head=True,
            )
            db.add(older_execution)
            db.commit()
            db.refresh(older_execution)

            newer_project = db.get(Project, newer_project_id)
            newer_project.status = "in_progress"
            newer_execution = Execution(
                project_id=newer_project_id,
                owner_id=newer_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build the newer dashboard"}]),
                is_active_head=True,
            )
            db.add(newer_execution)
            db.commit()
            db.refresh(newer_execution)
            older_execution_id = older_execution.id
            newer_execution_id = newer_execution.id
            newer_created_at = newer_execution.created_at
        finally:
            db.close()

        execution_state[newer_project_id] = _queued_state(newer_execution_id)
        pipeline_queue.append({
            "project_id": newer_project_id,
            "execution_id": newer_execution_id,
            "version": 1,
            "task_description": "Build the newer dashboard",
            "prompt_history": [{"role": "user", "content": "Build the newer dashboard"}],
            "reference_images": None,
            "nlu_result": {"intent": "build"},
            "created_at": newer_created_at,
        })

        with mock.patch("app.start_pipeline_job") as start_job:
            result = run_scheduler_maintenance_once(source="background poll", recover_stale=False)

        self.assertEqual(result["pending_adopted"], 1)
        self.assertEqual(result["local_dispatched"], 1)
        start_job.assert_called_once()
        self.assertEqual(start_job.call_args.args[0]["project_id"], older_project_id)
        self.assertEqual(start_job.call_args.args[0]["execution_id"], older_execution_id)
        self.assertTrue(start_job.call_args.kwargs["from_queue"])
        self.assertTrue(execution_state[older_project_id]["running"])
        self.assertFalse(execution_state[older_project_id]["queued"])
        self.assertTrue(execution_state[newer_project_id]["queued"])
        self.assertEqual(len(pipeline_queue), 1)
        self.assertEqual(pipeline_queue[0]["project_id"], newer_project_id)

    def test_execute_task_rejects_when_queue_limit_is_full(self):
        running_project_id = _create_project(self.client, self.token, "Running Queue Limit Project")
        queued_project_id = _create_project(self.client, self.token, "Queued Queue Limit Project", "Build a portfolio")
        blocked_project_id = _create_project(self.client, self.token, "Blocked Queue Limit Project", "Build a dashboard")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"
        os.environ["ARCHON_MAX_QUEUED_PIPELINES"] = "1"

        execution_state[running_project_id] = _running_state(1101)
        execution_state[queued_project_id] = _queued_state(1102)
        pipeline_queue.append({
            "project_id": queued_project_id,
            "execution_id": 1102,
            "version": 1,
            "task_description": "Build a portfolio",
            "prompt_history": [{"role": "user", "content": "Build a portfolio"}],
            "reference_images": None,
            "nlu_result": {"intent": "build"},
        })

        response = self.client.post(
            "/api/execute-task",
            json={"project_id": blocked_project_id, "enqueue_on_limit": True},
            headers={"Authorization": f"Bearer {self.token}"},
        )

        self.assertEqual(response.status_code, 429)
        payload = response.get_json()
        self.assertEqual(payload["reason"], "queue_limit")
        self.assertEqual(payload["queued_pipelines"], 1)
        self.assertEqual(payload["max_queued_pipelines"], 1)
        self.assertEqual(payload["active_pipelines"], 1)
        self.assertFalse(payload["project_running"])
        self.assertFalse(payload["project_queued"])

        db = get_session()
        try:
            executions = db.query(Execution).filter(Execution.project_id == blocked_project_id).count()
            self.assertEqual(executions, 0)
        finally:
            db.close()

    def test_execute_task_rejects_when_queue_limit_is_full_from_db_pending_execution(self):
        running_project_id = _create_project(self.client, self.token, "DB Running Queue Limit Project")
        queued_project_id = _create_project(self.client, self.token, "DB Queued Queue Limit Project", "Build a portfolio")
        blocked_project_id = _create_project(self.client, self.token, "DB Blocked Queue Limit Project", "Build a dashboard")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"
        os.environ["ARCHON_MAX_QUEUED_PIPELINES"] = "1"

        db = get_session()
        try:
            running_project = db.get(Project, running_project_id)
            running_project.status = "running"
            db.add(Execution(
                project_id=running_project_id,
                owner_id=running_project.owner_id,
                status="running",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a dashboard"}]),
                is_active_head=True,
                scheduler_worker_id="remote-worker",
                scheduler_claimed_at=utcnow_naive(),
                scheduler_heartbeat_at=utcnow_naive(),
            ))

            queued_project = db.get(Project, queued_project_id)
            queued_project.status = "in_progress"
            db.add(Execution(
                project_id=queued_project_id,
                owner_id=queued_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a portfolio"}]),
                is_active_head=True,
            ))
            db.commit()
        finally:
            db.close()

        response = self.client.post(
            "/api/execute-task",
            json={"project_id": blocked_project_id, "enqueue_on_limit": True},
            headers={"Authorization": f"Bearer {self.token}"},
        )

        self.assertEqual(response.status_code, 429)
        payload = response.get_json()
        self.assertEqual(payload["reason"], "queue_limit")
        self.assertEqual(payload["active_pipelines"], 1)
        self.assertEqual(payload["queued_pipelines"], 1)
        self.assertEqual(payload["max_queued_pipelines"], 1)

    def test_try_claim_execution_for_run_is_exclusive(self):
        project_id = _create_project(self.client, self.token, "Claim Ownership Project", "Build a queue-safe dashboard")

        db = get_session()
        try:
            project = db.get(Project, project_id)
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a queue-safe dashboard"}]),
                is_active_head=True,
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            execution_id = execution.id
        finally:
            db.close()

        self.assertTrue(try_claim_execution_for_run(execution_id))
        self.assertFalse(try_claim_execution_for_run(execution_id))

        db = get_session()
        try:
            execution = db.get(Execution, execution_id)
            lease = db.query(PipelineSlotLease).filter(PipelineSlotLease.execution_id == execution_id).first()
            self.assertIsNotNone(execution)
            self.assertEqual(execution.status, "running")
            self.assertEqual(execution.scheduler_worker_id, SCHEDULER_WORKER_ID)
            self.assertIsNotNone(execution.scheduler_claimed_at)
            self.assertIsNotNone(execution.scheduler_heartbeat_at)
            self.assertIsNotNone(lease)
            self.assertEqual(lease.worker_id, SCHEDULER_WORKER_ID)
        finally:
            db.close()

    def test_try_claim_execution_for_run_respects_durable_slot_limit(self):
        first_project_id = _create_project(self.client, self.token, "First Slot Lease Project", "Build a queue-safe dashboard")
        second_project_id = _create_project(self.client, self.token, "Second Slot Lease Project", "Build a queue-safe dashboard")
        os.environ["ARCHON_MAX_CONCURRENT_PIPELINES"] = "1"

        db = get_session()
        try:
            first_project = db.get(Project, first_project_id)
            second_project = db.get(Project, second_project_id)
            first_execution = Execution(
                project_id=first_project_id,
                owner_id=first_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a queue-safe dashboard"}]),
                is_active_head=True,
            )
            second_execution = Execution(
                project_id=second_project_id,
                owner_id=second_project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a queue-safe dashboard"}]),
                is_active_head=True,
            )
            db.add(first_execution)
            db.add(second_execution)
            db.commit()
            db.refresh(first_execution)
            db.refresh(second_execution)
            first_execution_id = first_execution.id
            second_execution_id = second_execution.id
        finally:
            db.close()

        self.assertTrue(try_claim_execution_for_run(first_execution_id))
        self.assertFalse(try_claim_execution_for_run(second_execution_id))

        db = get_session()
        try:
            first_execution = db.get(Execution, first_execution_id)
            second_execution = db.get(Execution, second_execution_id)
            leases = db.query(PipelineSlotLease).all()
            self.assertEqual(first_execution.status, "running")
            self.assertEqual(second_execution.status, "pending")
            self.assertEqual(len(leases), 1)
            self.assertEqual(leases[0].execution_id, first_execution_id)
            self.assertEqual(leases[0].slot_index, 1)
        finally:
            db.close()

    def test_claim_execution_for_pipeline_start_claims_before_thread_launch(self):
        project_id = _create_project(self.client, self.token, "Preclaim Start Project", "Build a queue-safe dashboard")

        db = get_session()
        try:
            project = db.get(Project, project_id)
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a queue-safe dashboard"}]),
                is_active_head=True,
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            execution_id = execution.id
        finally:
            db.close()

        execution_state[project_id] = _running_state(execution_id)

        self.assertTrue(claim_execution_for_pipeline_start(project_id, execution_id))
        self.assertIsNotNone(execution_state[project_id]["last_heartbeat_at"])

        db = get_session()
        try:
            execution = db.get(Execution, execution_id)
            lease = db.query(PipelineSlotLease).filter(PipelineSlotLease.execution_id == execution_id).first()
            self.assertIsNotNone(execution)
            self.assertEqual(execution.status, "running")
            self.assertEqual(execution.scheduler_worker_id, SCHEDULER_WORKER_ID)
            self.assertIsNotNone(lease)
        finally:
            db.close()

    def test_start_pipeline_job_skips_duplicate_thread_when_execution_already_claimed(self):
        project_id = _create_project(self.client, self.token, "Duplicate Thread Guard Project", "Build a queue-safe dashboard")

        db = get_session()
        try:
            project = db.get(Project, project_id)
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="running",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a queue-safe dashboard"}]),
                is_active_head=True,
                scheduler_worker_id="remote-worker",
                scheduler_claimed_at=utcnow_naive(),
                scheduler_heartbeat_at=utcnow_naive(),
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            execution_id = execution.id
        finally:
            db.close()

        execution_state[project_id] = _running_state(execution_id)
        job = {
            "project_id": project_id,
            "execution_id": execution_id,
            "version": 1,
            "task_description": "Build a queue-safe dashboard",
            "prompt_history": [{"role": "user", "content": "Build a queue-safe dashboard"}],
            "reference_images": None,
            "nlu_result": {"intent": "build"},
        }

        with mock.patch("app.release_and_dispatch_pipeline_slot") as release_slot:
            with mock.patch("app.threading.Thread") as thread_cls:
                started = start_pipeline_job(job)

        self.assertFalse(started)
        release_slot.assert_called_once_with(project_id)
        thread_cls.assert_not_called()

    def test_recover_stale_running_executions_fails_expired_execution(self):
        project_id = _create_project(self.client, self.token, "Stale Recovery Project", "Build a resilient dashboard")
        os.environ["ARCHON_EXECUTION_STALE_TIMEOUT_SECONDS"] = "60"

        db = get_session()
        try:
            project = db.get(Project, project_id)
            project.status = "running"
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="running",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a resilient dashboard"}]),
                is_active_head=True,
                scheduler_worker_id="stale-worker",
                scheduler_claimed_at=utcnow_naive() - timedelta(seconds=180),
                scheduler_heartbeat_at=utcnow_naive() - timedelta(seconds=180),
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            execution_id = execution.id
            db.add(PipelineSlotLease(
                slot_index=1,
                execution_id=execution_id,
                worker_id="stale-worker",
                claimed_at=utcnow_naive() - timedelta(seconds=180),
                heartbeat_at=utcnow_naive() - timedelta(seconds=180),
            ))
            db.commit()
        finally:
            db.close()

        recovered = recover_stale_running_executions()
        self.assertEqual(recovered, 1)

        db = get_session()
        try:
            execution = db.get(Execution, execution_id)
            lease = db.query(PipelineSlotLease).filter(PipelineSlotLease.execution_id == execution_id).first()
            project = db.get(Project, project_id)
            self.assertIsNotNone(execution)
            self.assertEqual(execution.status, "failed")
            self.assertEqual(
                execution.error_message,
                "Scheduler heartbeat expired before pipeline completion.",
            )
            self.assertIsNone(execution.scheduler_worker_id)
            self.assertIsNone(execution.scheduler_claimed_at)
            self.assertIsNone(execution.scheduler_heartbeat_at)
            self.assertIsNone(lease)
            self.assertIsNotNone(project)
            self.assertEqual(project.status, "failed")
        finally:
            db.close()

    def test_start_pipeline_job_preclaims_execution_before_starting_thread(self):
        project_id = _create_project(self.client, self.token, "Thread Preclaim Project", "Build a queue-safe dashboard")

        db = get_session()
        try:
            project = db.get(Project, project_id)
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="pending",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a queue-safe dashboard"}]),
                is_active_head=True,
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            execution_id = execution.id
        finally:
            db.close()

        execution_state[project_id] = _running_state(execution_id)
        job = {
            "project_id": project_id,
            "execution_id": execution_id,
            "version": 1,
            "task_description": "Build a queue-safe dashboard",
            "prompt_history": [{"role": "user", "content": "Build a queue-safe dashboard"}],
            "reference_images": None,
            "nlu_result": {"intent": "build"},
        }

        with mock.patch("app.threading.Thread") as thread_cls:
            thread_cls.return_value.start.return_value = None
            started = start_pipeline_job(job)

        self.assertTrue(started)
        thread_cls.assert_called_once()
        self.assertTrue(thread_cls.call_args.kwargs["daemon"])
        self.assertEqual(thread_cls.call_args.kwargs["args"][-1], True)

        db = get_session()
        try:
            execution = db.get(Execution, execution_id)
            self.assertIsNotNone(execution)
            self.assertEqual(execution.status, "running")
            self.assertEqual(execution.scheduler_worker_id, SCHEDULER_WORKER_ID)
        finally:
            db.close()

    def test_execution_status_clears_stale_local_queue_after_remote_claim(self):
        project_id = _create_project(self.client, self.token, "Remote Claim Status Project", "Build a shared dashboard")

        db = get_session()
        try:
            project = db.get(Project, project_id)
            project.status = "in_progress"
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="running",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a shared dashboard"}]),
                is_active_head=True,
                scheduler_worker_id="other-worker",
                scheduler_claimed_at=utcnow_naive(),
                scheduler_heartbeat_at=utcnow_naive(),
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            execution_id = execution.id
        finally:
            db.close()

        execution_state[project_id] = _queued_state(execution_id)
        pipeline_queue.append({
            "project_id": project_id,
            "execution_id": execution_id,
            "version": 1,
            "task_description": "Build a shared dashboard",
            "prompt_history": [{"role": "user", "content": "Build a shared dashboard"}],
            "reference_images": None,
            "nlu_result": {"intent": "build"},
        })

        response = self.client.get(
            "/api/execution-status",
            query_string={"project_id": project_id},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "RUNNING")
        self.assertFalse(payload["project_queued"])
        self.assertIsNone(payload["queue_position"])
        self.assertEqual(len(pipeline_queue), 0)
        self.assertFalse(execution_state[project_id]["queued"])

    def test_execution_status_uses_db_active_head_when_local_state_is_missing_for_running(self):
        project_id = _create_project(self.client, self.token, "DB Fallback Running Project", "Build a distributed dashboard")

        db = get_session()
        try:
            project = db.get(Project, project_id)
            project.status = "in_progress"
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="running",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a distributed dashboard"}]),
                is_active_head=True,
                scheduler_worker_id="remote-worker",
                scheduler_claimed_at=utcnow_naive(),
                scheduler_heartbeat_at=utcnow_naive(),
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            execution_id = execution.id
        finally:
            db.close()

        response = self.client.get(
            "/api/execution-status",
            query_string={"project_id": project_id},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "RUNNING")
        self.assertEqual(payload["currentStage"], "pm")
        self.assertEqual(payload["execution_id"], execution_id)

    def test_execution_status_prefers_result_artifact_over_stale_running_row(self):
        project_id = _create_project(self.client, self.token, "Artifact Override Project", "Build a recovered dashboard")

        db = get_session()
        try:
            project = db.get(Project, project_id)
            project.status = "in_progress"
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="running",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a recovered dashboard"}]),
                is_active_head=True,
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            execution_id = execution.id
        finally:
            db.close()

        version_dir = get_version_dir(project_id, 1)
        version_dir.mkdir(parents=True, exist_ok=True)
        with open(version_dir / "last_execution_result.json", "w", encoding="utf-8") as handle:
            json.dump({"status": "success"}, handle)

        execution_state.pop(project_id, None)

        response = self.client.get(
            "/api/execution-status",
            query_string={"project_id": project_id},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "COMPLETED")
        self.assertEqual(payload["currentStage"], "engineer")
        self.assertEqual(payload["execution_id"], execution_id)

    def test_execution_status_uses_db_active_head_when_local_state_is_missing_for_completed(self):
        project_id = _create_project(self.client, self.token, "DB Fallback Completed Project", "Build a shipped dashboard")

        db = get_session()
        try:
            project = db.get(Project, project_id)
            project.status = "completed"
            execution = Execution(
                project_id=project_id,
                owner_id=project.owner_id,
                status="success",
                version=1,
                prompt_history=json.dumps([{"role": "user", "content": "Build a shipped dashboard"}]),
                is_active_head=True,
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            execution_id = execution.id
        finally:
            db.close()

        response = self.client.get(
            "/api/execution-status",
            query_string={"project_id": project_id},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "COMPLETED")
        self.assertEqual(payload["currentStage"], "engineer")
        self.assertEqual(payload["execution_id"], execution_id)


if __name__ == "__main__":
    unittest.main()
