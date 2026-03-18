from __future__ import annotations

from agents.pm_agent import PMAgent, fallback_classify_intent


class _FailingModels:
    def generate_content(self, *args, **kwargs):
        raise RuntimeError("upstream unavailable")


class _FailingClient:
    models = _FailingModels()


def test_fallback_classifies_direct_build_command_as_build():
    result = fallback_classify_intent(
        "create me a final fantasy 10 fanpage landing page with 3 main characters, a weapon showcase and a game map"
    )

    assert result == {"type": "build"}


def test_fallback_classifies_question_as_chat():
    result = fallback_classify_intent("do you think adding a chatbox would help?")

    assert result["type"] == "chat"
    assert "built or changed" in result["message"]


def test_pm_agent_uses_heuristic_fallback_when_model_call_fails():
    agent = PMAgent(client=_FailingClient())

    result = agent.classify_intent("create me a final fantasy 10 website")

    assert result == {"type": "build"}


def test_pm_agent_uses_project_aware_chat_fallback_when_client_is_unavailable():
    agent = PMAgent(client=_FailingClient())
    agent.client = None
    agent._client_init_error = RuntimeError("missing client")

    result = agent.classify_intent(
        "should we add a sidebar",
        project_context="Project: Demo Workspace",
    )

    assert result["type"] == "chat"
    assert "this project" in result["message"]
