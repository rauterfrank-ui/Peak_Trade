"""
Tests für Shadow Pipeline Guards.

KRITISCH: Diese Tests verifizieren die Defense-in-Depth Guards.
"""

from __future__ import annotations

import os

import pytest

from src.data.shadow._guards import (
    ShadowLiveForbidden,
    ShadowPipelineDisabled,
    check_config_guard,
    check_import_guard,
    check_runtime_guard,
)


def test_import_guard_passes_without_env(monkeypatch):
    """Import Guard passt wenn PEAK_TRADE_LIVE_MODE nicht gesetzt."""
    monkeypatch.delenv("PEAK_TRADE_LIVE_MODE", raising=False)
    check_import_guard()  # Should NOT raise


def test_import_guard_blocks_live_mode_1(monkeypatch):
    """Import Guard blockiert bei PEAK_TRADE_LIVE_MODE=1."""
    monkeypatch.setenv("PEAK_TRADE_LIVE_MODE", "1")
    with pytest.raises(ShadowLiveForbidden, match="PEAK_TRADE_LIVE_MODE ist aktiv"):
        check_import_guard()


def test_import_guard_blocks_live_mode_true(monkeypatch):
    """Import Guard blockiert bei PEAK_TRADE_LIVE_MODE=true."""
    monkeypatch.setenv("PEAK_TRADE_LIVE_MODE", "true")
    with pytest.raises(ShadowLiveForbidden):
        check_import_guard()


def test_import_guard_blocks_live_mode_yes(monkeypatch):
    """Import Guard blockiert bei PEAK_TRADE_LIVE_MODE=yes."""
    monkeypatch.setenv("PEAK_TRADE_LIVE_MODE", "yes")
    with pytest.raises(ShadowLiveForbidden):
        check_import_guard()


def test_runtime_guard_passes_safe_config(monkeypatch):
    """Runtime Guard passt bei safe Config."""
    monkeypatch.delenv("PEAK_TRADE_LIVE_MODE", raising=False)
    cfg = {"live": {"enabled": False}}
    check_runtime_guard(cfg)  # Should NOT raise


def test_runtime_guard_blocks_live_enabled():
    """Runtime Guard blockiert bei live.enabled=true."""
    cfg = {"live": {"enabled": True}}
    with pytest.raises(ShadowLiveForbidden, match="live.enabled=true"):
        check_runtime_guard(cfg)


def test_runtime_guard_blocks_env_even_if_config_safe(monkeypatch):
    """Runtime Guard blockiert ENV auch wenn Config safe."""
    monkeypatch.setenv("PEAK_TRADE_LIVE_MODE", "1")
    cfg = {"live": {"enabled": False}}
    with pytest.raises(ShadowLiveForbidden):
        check_runtime_guard(cfg)


def test_config_guard_passes_when_enabled():
    """Config Guard passt wenn pipeline enabled."""
    cfg = {"shadow": {"pipeline": {"enabled": True}}}
    check_config_guard(cfg)  # Should NOT raise


def test_config_guard_blocks_when_disabled():
    """Config Guard blockiert wenn pipeline disabled."""
    cfg = {"shadow": {"pipeline": {"enabled": False}}}
    with pytest.raises(ShadowPipelineDisabled, match="Pipeline ist disabled"):
        check_config_guard(cfg)


def test_config_guard_blocks_when_missing():
    """Config Guard blockiert wenn Config fehlt."""
    cfg = {}
    with pytest.raises(ShadowPipelineDisabled):
        check_config_guard(cfg)
