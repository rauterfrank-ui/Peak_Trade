"""Tests for PolicyEnforcerV0 env toggle PT_POLICY_ENFORCE_V0."""

import pytest

from src.execution.policy import PolicyEnforcerV0


def test_policy_enforcer_from_env_default_off(monkeypatch):
    monkeypatch.delenv("PT_POLICY_ENFORCE_V0", raising=False)
    en = PolicyEnforcerV0.from_env()
    assert en.enforce is False


def test_policy_enforcer_from_env_on_values(monkeypatch):
    for v in ["1", "true", "yes", "on", "TRUE", " Yes "]:
        monkeypatch.setenv("PT_POLICY_ENFORCE_V0", v)
        en = PolicyEnforcerV0.from_env()
        assert en.enforce is True


def test_policy_enforcer_from_env_off_values(monkeypatch):
    for v in ["0", "false", "no", "off", "FALSE", " 0 "]:
        monkeypatch.setenv("PT_POLICY_ENFORCE_V0", v)
        en = PolicyEnforcerV0.from_env()
        assert en.enforce is False
