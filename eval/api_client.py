"""
Thin wrapper for Flask API calls (create project, build, poll).
"""

import time
import logging
import requests

logger = logging.getLogger(__name__)


class BuildError(Exception):
    """Raised when a build fails or times out."""

    def __init__(self, message: str, *, telemetry: dict | None = None):
        super().__init__(message)
        self.telemetry = telemetry or {}


class BuilderAPI:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self._authenticate()

    def _extract_token(self, data: dict) -> str | None:
        return data.get("token") or data.get("access_token")

    def _post_auth(self, paths: list[str], payload: dict, timeout: int = 10) -> requests.Response | None:
        """Try auth endpoints in order and return the first non-404 response."""
        for path in paths:
            resp = self.session.post(self._url(path), json=payload, timeout=timeout)
            if resp.status_code != 404:
                return resp
        return None

    def _authenticate(self) -> None:
        """Register/login eval user and attach bearer token to this session."""
        email = "eval@archon.dev"
        password = "evalpass123"
        name = "Eval Runner"

        register_paths = ["/api/register", "/api/auth/register"]
        login_paths = ["/api/login", "/api/auth/login"]

        register_resp = self._post_auth(
            register_paths,
            {"email": email, "password": password, "name": name},
        )
        if register_resp is None:
            raise BuildError("No register endpoint found (tried /api/register and /api/auth/register)")

        token = None
        if register_resp.status_code in (200, 201):
            token = self._extract_token(register_resp.json())
        elif register_resp.status_code == 409:
            login_resp = self._post_auth(login_paths, {"email": email, "password": password})
            if login_resp is None:
                raise BuildError("No login endpoint found (tried /api/login and /api/auth/login)")
            login_resp.raise_for_status()
            token = self._extract_token(login_resp.json())
        else:
            register_resp.raise_for_status()

        if not token:
            raise BuildError("Auth succeeded but no JWT token returned")

        self.session.headers.update({"Authorization": f"Bearer {token}"})
        logger.info("Authenticated eval API client")

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def health_check(self) -> bool:
        """Check if the backend is running."""
        try:
            resp = self.session.get(self._url("/api/health"), timeout=5)
            if resp.status_code == 200:
                return True
            if resp.status_code == 401:
                logger.warning("Health endpoint returned 401; backend reachable but auth may be required")
                return True
            return False
        except requests.ConnectionError:
            return False

    def create_project(self, name: str, description: str = None) -> int:
        """Create a project via POST /api/projects. Returns project_id."""
        payload = {"name": name}
        if description:
            payload["description"] = description
        resp = self.session.post(self._url("/api/projects"), json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        project_id = data["id"]
        logger.info(f"Created project {project_id}: {name}")
        return project_id

    def update_project_description(self, project_id: int, description: str) -> None:
        """Update a project's description via PUT /api/projects/<id>."""
        resp = self.session.put(
            self._url(f"/api/projects/{project_id}"),
            json={"description": description},
            timeout=10,
        )
        resp.raise_for_status()

    def trigger_build(self, project_id: int, enqueue_on_limit: bool = False) -> dict:
        """Trigger a build via POST /api/execute-task.

        Returns dict with keys: execution_id, version, project_id.
        """
        payload = {"project_id": project_id}
        if enqueue_on_limit:
            payload["enqueue_on_limit"] = True
        resp = self.session.post(self._url("/api/execute-task"), json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("response_type") == "chat":
            raise BuildError(f"Build rejected: {data.get('message')}")

        if data.get("status") == "queued":
            logger.info(
                "Build queued: project=%s execution=%s version=%s queue_position=%s",
                data["project_id"],
                data["execution_id"],
                data["version"],
                data.get("queue_position"),
            )
        else:
            logger.info(
                f"Build started: project={data['project_id']} "
                f"execution={data['execution_id']} version={data['version']}"
            )
        return {
            "execution_id": data["execution_id"],
            "version": data["version"],
            "project_id": data["project_id"],
            "trigger_status": data.get("status"),
            "initial_queue_position": data.get("queue_position"),
            "trigger_scheduler": {
                "project_queued": data.get("project_queued"),
                "queued_pipelines": data.get("queued_pipelines"),
                "active_pipelines": data.get("active_pipelines"),
            },
        }

    def poll_until_done(
        self,
        project_id: int = None,
        timeout: int = 300,
        poll_interval: float = 3.0,
        queue_timeout: int | None = None,
        started_queued: bool = False,
        initial_queue_position: int | None = None,
    ) -> dict:
        """Poll GET /api/execution-status until COMPLETED or FAILED.

        Args:
            project_id: Project ID to poll. If provided, passes as query param.
            timeout: Max seconds to wait once the build is actively running.
            poll_interval: Seconds between polls.
            queue_timeout: Max seconds to tolerate queue waiting before the active build starts.

        Returns the final status response dict.
        """
        active_timeout = max(1, timeout)
        queue_timeout = max(1, queue_timeout) if queue_timeout is not None else max(active_timeout, 900)
        now = time.time()
        active_started_at = now
        queue_started_at = now if started_queued else None
        queue_active = started_queued
        last_stage = None
        last_queue_position = initial_queue_position if started_queued else None
        telemetry = {
            "queue_observed": started_queued,
            "queue_wait_seconds": 0.0,
            "max_queue_position": initial_queue_position,
            "last_queue_position": last_queue_position,
            "queue_timeout_seconds": queue_timeout,
            "active_timeout_seconds": active_timeout,
            "poll_count": 0,
            "final_stage": None,
        }
        params = {}
        if project_id:
            params["project_id"] = project_id

        if started_queued:
            logger.info("Build initially queued (queue_position=%s)", initial_queue_position)

        while True:
            now = time.time()
            if queue_active:
                queued_for = now - (queue_started_at if queue_started_at is not None else now)
                if queued_for >= queue_timeout:
                    telemetry["queue_wait_seconds"] = round(queued_for, 1)
                    telemetry["final_stage"] = last_stage
                    raise BuildError(
                        f"Build stayed queued for over {queue_timeout}s",
                        telemetry=telemetry,
                    )
            elif now - active_started_at >= active_timeout:
                telemetry["final_stage"] = last_stage
                raise BuildError(
                    f"Build timed out after {active_timeout}s once active",
                    telemetry=telemetry,
                )

            try:
                resp = self.session.get(self._url("/api/execution-status"), params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except (requests.ConnectionError, requests.Timeout) as e:
                logger.warning(f"Poll error: {e}, retrying...")
                time.sleep(poll_interval)
                continue

            telemetry["poll_count"] += 1
            status = data.get("status", "")
            stage = data.get("currentStage", "")
            project_queued = bool(data.get("project_queued"))
            queue_position = data.get("queue_position")

            if project_queued:
                telemetry["queue_observed"] = True
                if queue_position is not None:
                    previous_max = telemetry.get("max_queue_position")
                    telemetry["max_queue_position"] = (
                        queue_position
                        if previous_max is None
                        else max(previous_max, queue_position)
                    )
                if not queue_active:
                    queue_started_at = time.time()
                    queue_active = True
                    last_queue_position = queue_position
                    logger.info("Build queued during polling (queue_position=%s)", queue_position)
                elif queue_position != last_queue_position:
                    logger.info("Build still queued (queue_position=%s)", queue_position)
                    last_queue_position = queue_position
                telemetry["last_queue_position"] = last_queue_position
            elif queue_active:
                queue_exit_time = time.time()
                queued_for = queue_exit_time - (
                    queue_started_at if queue_started_at is not None else queue_exit_time
                )
                logger.info("Build left queue after %.1fs", queued_for)
                telemetry["queue_wait_seconds"] = round(queued_for, 1)
                queue_active = False
                queue_started_at = None
                last_queue_position = None
                telemetry["last_queue_position"] = None
                active_started_at = queue_exit_time

            if stage != last_stage:
                logger.info(f"Build stage: {stage} (status: {status})")
                last_stage = stage
            telemetry["final_stage"] = stage

            if status == "COMPLETED":
                logger.info("Build completed successfully")
                if queue_active:
                    completed_at = time.time()
                    queued_for = completed_at - (
                        queue_started_at if queue_started_at is not None else completed_at
                    )
                    telemetry["queue_wait_seconds"] = round(queued_for, 1)
                telemetry["active_duration_seconds"] = round(max(time.time() - active_started_at, 0.0), 1)
                data["queue_telemetry"] = telemetry
                return data
            elif status == "FAILED":
                if queue_active:
                    failed_at = time.time()
                    queued_for = failed_at - (
                        queue_started_at if queue_started_at is not None else failed_at
                    )
                    telemetry["queue_wait_seconds"] = round(queued_for, 1)
                telemetry["active_duration_seconds"] = round(max(time.time() - active_started_at, 0.0), 1)
                raise BuildError(f"Build failed at stage '{stage}'", telemetry=telemetry)

            time.sleep(poll_interval)

    def get_preview_url(self, project_id: int, version: int) -> str:
        """Return the preview URL for a given project/version."""
        return f"{self.base_url}/api/preview/{project_id}/{version}"

    def create_and_build(
        self,
        name: str,
        description: str,
        timeout: int = 300,
        enqueue_on_limit: bool = False,
        queue_timeout: int | None = None,
    ) -> dict:
        """Convenience: create project, set description, trigger build, poll to completion.

        Returns dict with: project_id, version, execution_id, preview_url.
        """
        project_id = self.create_project(name, description)
        build_info = self.trigger_build(project_id, enqueue_on_limit=enqueue_on_limit)
        try:
            result = self.poll_until_done(
                project_id=project_id,
                timeout=timeout,
                queue_timeout=queue_timeout,
                started_queued=build_info.get("trigger_status") == "queued",
                initial_queue_position=build_info.get("initial_queue_position"),
            )
        except BuildError as exc:
            telemetry = dict(getattr(exc, "telemetry", {}) or {})
            telemetry.setdefault("trigger_status", build_info.get("trigger_status"))
            telemetry.setdefault("initial_queue_position", build_info.get("initial_queue_position"))
            telemetry.setdefault("trigger_scheduler", build_info.get("trigger_scheduler"))
            raise BuildError(str(exc), telemetry=telemetry) from exc
        preview_url = self.get_preview_url(project_id, build_info["version"])
        queue_telemetry = dict(result.get("queue_telemetry") or {})
        queue_telemetry.setdefault("trigger_status", build_info.get("trigger_status"))
        queue_telemetry.setdefault("initial_queue_position", build_info.get("initial_queue_position"))
        queue_telemetry.setdefault("trigger_scheduler", build_info.get("trigger_scheduler"))
        return {
            "project_id": project_id,
            "version": build_info["version"],
            "execution_id": build_info["execution_id"],
            "preview_url": preview_url,
            "status": result.get("status"),
            "queue_telemetry": queue_telemetry,
        }
