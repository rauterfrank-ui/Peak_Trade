"""Pytest fixtures for Kill Switch tests."""

import pytest
from datetime import datetime

from src.risk_layer.kill_switch import KillSwitch
from src.risk_layer.kill_switch.triggers import (
    ThresholdTrigger,
    ManualTrigger,
    WatchdogTrigger,
    ExternalTrigger,
    TriggerRegistry,
)


@pytest.fixture
def kill_switch_config():
    """Basic kill switch configuration for testing."""
    return {
        "enabled": True,
        "mode": "active",
        "recovery_cooldown_seconds": 1,  # Short for tests
        "require_approval_code": False,  # Disable for tests
        "persist_state": False,
    }


@pytest.fixture
def kill_switch(kill_switch_config):
    """Create a KillSwitch instance for testing."""
    return KillSwitch(kill_switch_config)


@pytest.fixture
def threshold_trigger():
    """Create a threshold trigger for testing."""
    config = {
        "enabled": True,
        "type": "threshold",
        "metric": "portfolio_drawdown",
        "threshold": -0.15,
        "operator": "lt",
        "cooldown_seconds": 0,
    }
    return ThresholdTrigger("test_threshold", config)


@pytest.fixture
def manual_trigger():
    """Create a manual trigger for testing."""
    config = {
        "enabled": True,
        "type": "manual",
    }
    return ManualTrigger("test_manual", config)


@pytest.fixture
def watchdog_trigger():
    """Create a watchdog trigger for testing."""
    config = {
        "enabled": True,
        "type": "watchdog",
        "heartbeat_interval_seconds": 1,
        "max_missed_heartbeats": 2,
        "memory_threshold_percent": 90,
        "cpu_threshold_percent": 95,
    }
    return WatchdogTrigger("test_watchdog", config)


@pytest.fixture
def external_trigger():
    """Create an external trigger for testing."""
    config = {
        "enabled": True,
        "type": "external",
        "check_interval_seconds": 1,
        "max_consecutive_failures": 3,
    }
    return ExternalTrigger("test_external", config)


@pytest.fixture
def trigger_registry():
    """Create an empty trigger registry for testing."""
    return TriggerRegistry()


@pytest.fixture
def test_context():
    """Create a test context for trigger checks."""
    return {
        "portfolio_drawdown": -0.10,
        "daily_pnl": -0.03,
        "realized_volatility_1h": 0.05,
        "exchange_connected": True,
        "last_price_update": datetime.utcnow(),
        "api_errors": 0,
    }
