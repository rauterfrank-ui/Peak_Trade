"""
Contract tests for public module-level constants in src.core.peak_config (v0).

Reads only stable public surface: PEAK_TRADE_CONFIG_ENV_VAR, AUTO_LIVE_OVERRIDES_PATH.
No subprocess, no TOML load, no assertions on underscore-prefixed module internals,
no assertions on filesystem existence for override paths.
"""

from __future__ import annotations

from pathlib import Path

from src.core import peak_config as pc


def test_peak_trade_config_env_var_public_contract() -> None:
    assert hasattr(pc, "PEAK_TRADE_CONFIG_ENV_VAR")
    raw = getattr(pc, "PEAK_TRADE_CONFIG_ENV_VAR")
    assert isinstance(raw, str)
    assert raw == "PEAK_TRADE_CONFIG_PATH"


def test_auto_live_overrides_path_public_contract() -> None:
    assert hasattr(pc, "AUTO_LIVE_OVERRIDES_PATH")
    p = getattr(pc, "AUTO_LIVE_OVERRIDES_PATH")
    assert isinstance(p, Path)
    assert p.name == "auto.toml"
    assert "live_overrides" in p.parts
