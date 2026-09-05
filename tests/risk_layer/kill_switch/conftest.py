"""Pytest fixtures for Kill Switch tests."""

import pytest

from src.risk_layer.kill_switch import KillSwitch


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
