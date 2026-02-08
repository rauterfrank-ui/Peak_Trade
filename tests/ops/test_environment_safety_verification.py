# tests/ops/test_environment_safety_verification.py
"""
P0: Deterministic verification tests for environment/safety contracts.

No network, no external tools. Asserts that:
- create_default_environment() yields safe defaults (paper, no live, dry_run).
- get_environment_from_config() with empty/minimal config yields safe defaults.
- EnvironmentConfig.allows_real_orders invariants (paper/testnet_dry_run/live gates).
"""

from __future__ import annotations

import pytest

from src.core.environment import (
    TradingEnvironment,
    EnvironmentConfig,
    create_default_environment,
    get_environment_from_config,
)
from src.core.peak_config import PeakConfig


class TestCreateDefaultEnvironmentSafe:
    """create_default_environment() yields safe defaults."""

    def test_default_is_paper(self) -> None:
        """Default environment is PAPER."""
        cfg = create_default_environment()
        assert cfg.environment == TradingEnvironment.PAPER

    def test_default_live_disabled(self) -> None:
        """Default: enable_live_trading=False, live_mode_armed=False, live_dry_run_mode=True."""
        cfg = create_default_environment()
        assert cfg.enable_live_trading is False
        assert cfg.live_mode_armed is False
        assert cfg.live_dry_run_mode is True

    def test_default_allows_real_orders_false(self) -> None:
        """Default config does not allow real orders."""
        cfg = create_default_environment()
        assert cfg.allows_real_orders is False


class TestGetEnvironmentFromConfigSafeDefaults:
    """get_environment_from_config() with empty/minimal config yields safe defaults."""

    def test_empty_config_yields_paper_and_safe_flags(self) -> None:
        """PeakConfig(raw={}) yields paper, enable_live_trading=False, live_dry_run_mode=True."""
        peak = PeakConfig(raw={})
        cfg = get_environment_from_config(peak)
        assert cfg.environment == TradingEnvironment.PAPER
        assert cfg.enable_live_trading is False
        assert cfg.live_mode_armed is False
        assert cfg.live_dry_run_mode is True

    def test_empty_config_allows_real_orders_false(self) -> None:
        """Empty config must not allow real orders."""
        peak = PeakConfig(raw={})
        cfg = get_environment_from_config(peak)
        assert cfg.allows_real_orders is False


class TestEnvironmentConfigAllowsRealOrdersInvariants:
    """EnvironmentConfig.allows_real_orders invariants."""

    def test_paper_never_allows_real_orders(self) -> None:
        """Paper mode never allows real orders."""
        cfg = EnvironmentConfig(
            environment=TradingEnvironment.PAPER,
            enable_live_trading=True,
            live_mode_armed=True,
            live_dry_run_mode=False,
        )
        assert cfg.allows_real_orders is False

    def test_testnet_dry_run_blocks_real_orders(self) -> None:
        """Testnet with testnet_dry_run=True blocks real orders."""
        cfg = EnvironmentConfig(
            environment=TradingEnvironment.TESTNET,
            testnet_dry_run=True,
        )
        assert cfg.allows_real_orders is False

    def test_live_requires_enable_and_armed_and_no_dry_run(self) -> None:
        """Live allows real orders only when enable_live_trading, live_mode_armed, and not live_dry_run_mode."""
        cfg_blocked = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=True,
            live_dry_run_mode=True,  # blocks
        )
        assert cfg_blocked.allows_real_orders is False
