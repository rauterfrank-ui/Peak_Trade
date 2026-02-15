import pytest

from src.ai.gates.ai_model_hard_gate_v1 import AIModelHardGateError, require_ai_models_allowed


def test_default_denies(monkeypatch):
    monkeypatch.delenv("PT_AI_MODELS_ENABLED", raising=False)
    monkeypatch.delenv("PT_PAPERTRAIL_READY", raising=False)
    monkeypatch.delenv("PT_AI_MODELS_ARMED", raising=False)

    with pytest.raises(AIModelHardGateError) as e:
        require_ai_models_allowed(context="test")
    assert "PT_AI_MODELS_ENABLED=YES" in str(e.value)
    assert "PT_PAPERTRAIL_READY=YES" in str(e.value)


def test_allows_when_enabled_and_ready(monkeypatch):
    monkeypatch.setenv("PT_AI_MODELS_ENABLED", "YES")
    monkeypatch.setenv("PT_PAPERTRAIL_READY", "YES")
    monkeypatch.delenv("PT_AI_MODELS_ARMED", raising=False)

    st = require_ai_models_allowed(context="test")
    assert st.ok is True


def test_armed_optional_if_set(monkeypatch):
    monkeypatch.setenv("PT_AI_MODELS_ENABLED", "YES")
    monkeypatch.setenv("PT_PAPERTRAIL_READY", "YES")
    monkeypatch.setenv("PT_AI_MODELS_ARMED", "NO")

    with pytest.raises(AIModelHardGateError):
        require_ai_models_allowed(context="test")

    monkeypatch.setenv("PT_AI_MODELS_ARMED", "YES")
    st = require_ai_models_allowed(context="test")
    assert st.ok is True


def test_create_model_client_live_blocked_by_default(monkeypatch):
    """Integration: create_model_client('live') raises without gate env vars."""
    monkeypatch.delenv("PT_AI_MODELS_ENABLED", raising=False)
    monkeypatch.delenv("PT_PAPERTRAIL_READY", raising=False)
    monkeypatch.delenv("PT_AI_MODELS_ARMED", raising=False)

    from src.ai_orchestration.model_client import create_model_client

    with pytest.raises(AIModelHardGateError):
        create_model_client("live")
