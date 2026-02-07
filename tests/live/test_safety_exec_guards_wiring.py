"""
Unit tests for Runbook-B execution guards wiring in SafetyGuard.

Guards are default OFF; enabled via PEAK_EXEC_GUARDS_ENABLED=1.
When enabled, PEAK_EXEC_GUARDS_SECRET is required (env).
Tests are offline; no exchange calls.
"""
from __future__ import annotations

import importlib
import sys

import pytest

from src.core.environment import EnvironmentConfig, TradingEnvironment


def _reload_safety():
    """Reload safety module so env vars are read at runtime."""
    if "src.live.safety" in sys.modules:
        sys.modules.pop("src.live.safety", None)
    return importlib.import_module("src.live.safety")


def test_guards_default_off_does_not_require_secret(monkeypatch):
    monkeypatch.delenv("PEAK_EXEC_GUARDS_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_EXEC_GUARDS_SECRET", raising=False)
    m = _reload_safety()
    # Module loads; ensure_may_place_order exists and can be called when guards off
    config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
    guard = m.SafetyGuard(env_config=config)
    # PAPER mode raises PaperModeOrderError (expected), not RuntimeError for missing secret
    with pytest.raises(m.PaperModeOrderError):
        guard.ensure_may_place_order()


def test_guards_on_requires_secret(monkeypatch):
    monkeypatch.setenv("PEAK_EXEC_GUARDS_ENABLED", "1")
    monkeypatch.delenv("PEAK_EXEC_GUARDS_SECRET", raising=False)
    monkeypatch.delenv("PEAK_EXEC_GUARDS_TOKEN", raising=False)
    m = _reload_safety()
    config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
    guard = m.SafetyGuard(env_config=config)
    with pytest.raises(RuntimeError) as exc_info:
        guard.ensure_may_place_order()
    assert "PEAK_EXEC_GUARDS_SECRET" in str(exc_info.value)
