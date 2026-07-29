import os
import sys
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as backend_app
from agents.governance_agent import GovernanceAgent
from models import Project, get_session


def test_offline_nlu_uses_local_fallback(monkeypatch):
    monkeypatch.setenv("OFFLINE_MODE", "true")
    with mock.patch.object(backend_app.nlu_agent, "analyze", side_effect=AssertionError("provider called")):
        result = backend_app.analyze_prompt_nlu("Build a private project dashboard")

    assert result["domain"] == "general"
    assert result["keywords"] == []


def test_offline_governance_skips_nlu_client():
    with mock.patch("agents.nlu_agent.NLUAgent", side_effect=AssertionError("provider initialized")):
        agent = GovernanceAgent(enable_nlu=False)

    assert agent.nlu is None


def test_offline_chat_skips_model_classification(monkeypatch):
    monkeypatch.setenv("OFFLINE_MODE", "true")
    db = get_session()
    try:
        project = Project(name="Offline Guard Test", status="completed")
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id
    finally:
        db.close()

    try:
        with (
            backend_app.app.test_client() as client,
            mock.patch("agents.pm_agent.PMAgent", side_effect=AssertionError("provider initialized")),
        ):
            response = client.post(
                f"/api/projects/{project_id}/chat",
                json={"message": "Build a sales dashboard"},
            )

        assert response.status_code == 200
        assert response.get_json()["response_type"] == "build"
    finally:
        db = get_session()
        try:
            project = db.get(Project, project_id)
            if project:
                db.delete(project)
                db.commit()
        finally:
            db.close()
