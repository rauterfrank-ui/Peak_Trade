"""Minimal safety tests for testnet execution events (import, no-raise when disabled)."""

import importlib

import pytest


def test_imports_ok() -> None:
    """Import execution_events module works."""
    importlib.import_module("src.observability.execution_events")


def test_emit_safe_does_not_raise_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """emit does not raise when PT_EXEC_EVENTS_ENABLED=false."""
    monkeypatch.setenv("PT_EXEC_EVENTS_ENABLED", "false")
    from src.observability.execution_events import emit

    emit(event_type="x", level="info")
