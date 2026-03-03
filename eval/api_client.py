"""
Thin wrapper for Flask API calls (create project, build, poll).
"""

import time
import logging
import requests

logger = logging.getLogger(__name__)


class BuildError(Exception):
    """Raised when a build fails or times out."""
    pass


class BuilderAPI:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def health_check(self) -> bool:
        """Check if the backend is running."""
        try:
            resp = self.session.get(self._url("/api/projects"), timeout=5)
            return resp.status_code == 200
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

    def trigger_build(self, project_id: int) -> dict:
        """Trigger a build via POST /api/execute-task.

        Returns dict with keys: execution_id, version, project_id.
        """
        payload = {"project_id": project_id}
        resp = self.session.post(self._url("/api/execute-task"), json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("response_type") == "chat":
            raise BuildError(f"Build rejected: {data.get('message')}")

        logger.info(
            f"Build started: project={data['project_id']} "
            f"execution={data['execution_id']} version={data['version']}"
        )
        return {
            "execution_id": data["execution_id"],
            "version": data["version"],
            "project_id": data["project_id"],
        }

    def poll_until_done(self, project_id: int = None, timeout: int = 300, poll_interval: float = 3.0) -> dict:
        """Poll GET /api/execution-status until COMPLETED or FAILED.

        Args:
            project_id: Project ID to poll. If provided, passes as query param.
            timeout: Max seconds to wait.
            poll_interval: Seconds between polls.

        Returns the final status response dict.
        """
        start = time.time()
        last_stage = None
        params = {}
        if project_id:
            params["project_id"] = project_id

        while time.time() - start < timeout:
            try:
                resp = self.session.get(self._url("/api/execution-status"), params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except (requests.ConnectionError, requests.Timeout) as e:
                logger.warning(f"Poll error: {e}, retrying...")
                time.sleep(poll_interval)
                continue

            status = data.get("status", "")
            stage = data.get("currentStage", "")

            if stage != last_stage:
                logger.info(f"Build stage: {stage} (status: {status})")
                last_stage = stage

            if status == "COMPLETED":
                logger.info("Build completed successfully")
                return data
            elif status == "FAILED":
                raise BuildError(f"Build failed at stage '{stage}'")

            time.sleep(poll_interval)

        raise BuildError(f"Build timed out after {timeout}s")

    def get_preview_url(self, project_id: int, version: int) -> str:
        """Return the preview URL for a given project/version."""
        return f"{self.base_url}/api/preview/{project_id}/{version}"

    def create_and_build(self, name: str, description: str, timeout: int = 300) -> dict:
        """Convenience: create project, set description, trigger build, poll to completion.

        Returns dict with: project_id, version, execution_id, preview_url.
        """
        project_id = self.create_project(name, description)
        build_info = self.trigger_build(project_id)
        result = self.poll_until_done(project_id=project_id, timeout=timeout)
        preview_url = self.get_preview_url(project_id, build_info["version"])
        return {
            "project_id": project_id,
            "version": build_info["version"],
            "execution_id": build_info["execution_id"],
            "preview_url": preview_url,
            "status": result.get("status"),
        }
