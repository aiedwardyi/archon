"""
Test that protected endpoints return 401 without auth and 200 with auth.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app
from models import Project, User, get_session


TEST_EMAIL = "testguard@archon-test.com"
TEST_PASSWORD = "testpass123"


@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
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


def test_post_projects_requires_auth(client):
    """POST /api/projects without token should return 401."""
    resp = client.post("/api/projects", json={"name": "test"})
    assert resp.status_code == 401


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
