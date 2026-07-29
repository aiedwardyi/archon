"""
Test that protected endpoints return 401 without auth and 200 with auth.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app
from models import Execution, Project, User, get_session


TEST_EMAIL = "testguard@archon-test.com"
TEST_PASSWORD = "testpass123"


@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "archon-test-secret-key-at-least-32-bytes"
    with app.test_client() as c:
        yield c


@pytest.fixture(scope="module")
def auth_token(client):
    """Register a test user and return their JWT token."""
    resp = client.post(
        "/api/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": "Test Guard",
        },
    )
    if resp.status_code == 409:
        resp = client.post(
            "/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )

    data = resp.get_json()
    token = data["token"]
    yield token

    db = get_session()
    try:
        user = db.query(User).filter(User.email == TEST_EMAIL).first()
        if user:
            db.query(Project).filter(Project.owner_id == user.id).delete(synchronize_session=False)
            db.delete(user)
            db.commit()
    finally:
        db.close()


PROTECTED_GET_ENDPOINTS = [
    "/api/projects",
    "/api/stats",
    "/api/activity",
    "/api/dashboard/stats",
]


@pytest.mark.parametrize("endpoint", PROTECTED_GET_ENDPOINTS)
def test_get_endpoints_require_auth(client, endpoint):
    """GET without token should return 401."""
    resp = client.get(endpoint)
    assert resp.status_code == 401, f"{endpoint} returned {resp.status_code}, expected 401"


def test_post_projects_allows_guest_creation(client):
    """POST /api/projects without auth should create a guest project."""
    resp = client.post("/api/projects", json={"name": "Guest Flow Test Project"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["owner_id"] is None

    db = get_session()
    try:
        project = db.get(Project, data["id"])
        if project:
            db.delete(project)
            db.commit()
    finally:
        db.close()


@pytest.mark.parametrize("endpoint", PROTECTED_GET_ENDPOINTS)
def test_get_endpoints_work_with_auth(client, auth_token, endpoint):
    """GET with valid token should return 200."""
    resp = client.get(endpoint, headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200, f"{endpoint} returned {resp.status_code}, expected 200"


def test_post_projects_works_with_auth(client, auth_token):
    """POST /api/projects with valid token should return 201."""
    resp = client.post(
        "/api/projects",
        json={"name": "Auth Guard Test Project"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 201, f"POST /api/projects returned {resp.status_code}, expected 201"


def test_claim_endpoint_claims_guest_project_for_existing_user(client, auth_token):
    guest_resp = client.post("/api/projects", json={"name": "Guest Claim Endpoint Project"})
    assert guest_resp.status_code == 201
    guest_project = guest_resp.get_json()

    claim_resp = client.post(
        f"/api/projects/{guest_project['id']}/claim",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert claim_resp.status_code == 200

    db = get_session()
    try:
        user = db.query(User).filter(User.email == TEST_EMAIL).first()
        project = db.get(Project, guest_project["id"])
        assert user is not None
        assert project is not None
        assert project.owner_id == user.id
    finally:
        db.close()


def test_register_claims_guest_project_and_executions(client):
    guest_resp = client.post("/api/projects", json={"name": "Guest Register Claim Project"})
    assert guest_resp.status_code == 201
    guest_project = guest_resp.get_json()

    db = get_session()
    try:
        execution = Execution(
            project_id=guest_project["id"],
            owner_id=None,
            status="pending",
            version=1,
            is_active_head=True,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        execution_id = execution.id
    finally:
        db.close()

    register_email = f"guest-claim-{guest_project['id']}@archon-test.com"
    register_resp = client.post(
        "/api/auth/register",
        json={
            "email": register_email,
            "password": TEST_PASSWORD,
            "name": "Guest Claim",
            "guest_project_id": guest_project["id"],
        },
    )
    assert register_resp.status_code == 201
    registered_user = register_resp.get_json()["user"]

    db = get_session()
    try:
        project = db.get(Project, guest_project["id"])
        execution = db.get(Execution, execution_id)
        user = db.get(User, registered_user["id"])

        assert project is not None
        assert execution is not None
        assert user is not None
        assert project.owner_id == user.id
        assert execution.owner_id == user.id

        db.delete(project)
        db.delete(user)
        db.commit()
    finally:
        db.close()


def test_forgot_password_hides_reset_token_by_default(client, monkeypatch):
    monkeypatch.delenv("ARCHON_EXPOSE_RESET_TOKEN", raising=False)
    email = "reset-hidden@archon-test.com"

    register_resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": TEST_PASSWORD, "name": "Reset Hidden"},
    )
    assert register_resp.status_code == 201

    reset_resp = client.post("/api/auth/forgot-password", json={"email": email})
    assert reset_resp.status_code == 200
    assert "_dev_token" not in reset_resp.get_json()

    db = get_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        assert user.reset_token
        db.delete(user)
        db.commit()
    finally:
        db.close()


@pytest.mark.parametrize("flag_value", ["true", "y", "on"])
def test_forgot_password_can_expose_reset_token_explicitly(client, monkeypatch, flag_value):
    monkeypatch.setenv("ARCHON_EXPOSE_RESET_TOKEN", flag_value)
    email = f"reset-visible-{flag_value}@archon-test.com"

    register_resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": TEST_PASSWORD, "name": "Reset Visible"},
    )
    assert register_resp.status_code == 201

    reset_resp = client.post("/api/auth/forgot-password", json={"email": email})
    assert reset_resp.status_code == 200
    assert reset_resp.get_json()["_dev_token"]

    db = get_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
            db.commit()
    finally:
        db.close()


def test_forgot_password_hides_reset_token_outside_local_environment(client, monkeypatch):
    monkeypatch.setenv("ARCHON_EXPOSE_RESET_TOKEN", "true")
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setitem(app.config, "TESTING", False)
    email = "reset-production@archon-test.com"

    register_resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": TEST_PASSWORD, "name": "Reset Production"},
    )
    assert register_resp.status_code == 201

    reset_resp = client.post("/api/auth/forgot-password", json={"email": email})
    assert reset_resp.status_code == 200
    assert "_dev_token" not in reset_resp.get_json()

    db = get_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
            db.commit()
    finally:
        db.close()
