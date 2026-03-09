import json
import os
import shutil
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import PUBLIC_DIR, app
from models import Execution, Project, User, get_session


TEST_PASSWORD = "testpass123"


@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _register_user(client):
    email = f"seed-{uuid.uuid4().hex[:12]}@archon-test.com"
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": TEST_PASSWORD,
            "name": "Seed Test",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    return email, data["token"], data["user"]["id"]


def _cleanup_user(email: str):
    db = get_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return

        project_ids = [project.id for project in db.query(Project).filter(Project.owner_id == user.id).all()]
        for project_id in project_ids:
            shutil.rmtree(PUBLIC_DIR / str(project_id), ignore_errors=True)
        for project in db.query(Project).filter(Project.owner_id == user.id).all():
            db.delete(project)
        db.delete(user)
        db.commit()
    finally:
        db.close()


def test_seed_endpoint_copies_and_rewrites_seed_projects(client):
    email, token, user_id = _register_user(client)

    try:
        first = client.post("/api/seed", headers={"Authorization": f"Bearer {token}"})
        assert first.status_code == 200

        payload = first.get_json()
        assert payload["seeded"] is True
        assert len(payload["projects"]) == 2

        db = get_session()
        try:
            projects = (
                db.query(Project)
                .filter(Project.owner_id == user_id)
                .order_by(Project.id.asc())
                .all()
            )
            assert len(projects) == 2

            names = {project.name for project in projects}
            assert names == {"FF7 — Avalanche Archive", "FF7 — Midgar Archives"}

            for project in projects:
                assert project.status == "completed"
                assert project.locked_ui_archetype == "game"

                execution = (
                    db.query(Execution)
                    .filter(Execution.project_id == project.id, Execution.version == 1)
                    .first()
                )
                assert execution is not None
                assert execution.status == "success"
                assert execution.is_active_head is True
                assert execution.model_used == "Gemini 2.5 Flash"
                assert execution.tokens_used == 18000
                assert execution.credits_used == 7
                assert execution.readiness_score == 86
                assert execution.quality_tier == "good"
                assert execution.prd_path and execution.plan_path and execution.result_path

                version_dir = PUBLIC_DIR / str(project.id) / "v1"
                assert version_dir.exists()

                html = (version_dir / "code" / "src" / "index.html").read_text(encoding="utf-8")
                css = (version_dir / "code" / "src" / "style.css").read_text(encoding="utf-8")
                assert f"/api/assets/{project.id}/1/" in html or f"/api/assets/{project.id}/1/" in css
                assert "/api/assets/71/1/" not in html
                assert "/api/assets/71/1/" not in css
                assert "/api/assets/38/1/" not in html
                assert "/api/assets/38/1/" not in css

                factsheet_path = version_dir / "last_factsheet.json"
                factsheet = factsheet_path.read_text(encoding="utf-8")
                assert f'"id": {project.id}' in factsheet
                assert f'"execution_id": {execution.id}' in factsheet

                result_data = json.loads((version_dir / "last_execution_result.json").read_text(encoding="utf-8"))
                expected_fragment = str(Path("generated") / str(project.id) / "v1")
                for write in result_data["outputs"]["writes"]:
                    assert expected_fragment in write["path"]
        finally:
            db.close()

        second = client.post("/api/seed", headers={"Authorization": f"Bearer {token}"})
        assert second.status_code == 200
        assert second.get_json() == {"seeded": False}
    finally:
        _cleanup_user(email)
