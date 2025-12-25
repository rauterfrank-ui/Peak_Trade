"""
Tests for KillSwitch Layer
"""

import pytest

from src.core.peak_config import PeakConfig
from src.risk_layer.kill_switch import KillSwitchLayer, to_violations


@pytest.fixture
def default_config() -> PeakConfig:
    """Create default kill switch config."""
    return PeakConfig(
        raw={
            "risk": {
                "kill_switch": {
                    "enabled": True,
                    "daily_loss_limit_pct": 0.05,
                    "max_drawdown_pct": 0.20,
                    "max_volatility_pct": None,
                }
            }
        }
    )


@pytest.fixture
def disabled_config() -> PeakConfig:
    """Create disabled kill switch config."""
    return PeakConfig(raw={"risk": {"kill_switch": {"enabled": False}}})


def test_disabled_does_not_arm(disabled_config: PeakConfig) -> None:
    """Test that disabled kill switch never arms."""
    ks = KillSwitchLayer(disabled_config)

    # Even with terrible metrics
    metrics = {"daily_pnl_pct": -0.50, "current_drawdown_pct": 0.90}
    status = ks.evaluate(metrics)

    assert not status.armed
    assert status.severity == "OK"
    assert "disabled" in status.reason.lower()


def test_daily_loss_arms_on_threshold(default_config: PeakConfig) -> None:
    """Test that daily loss at threshold arms the kill switch."""
    ks = KillSwitchLayer(default_config)

    # Exactly at threshold: -5%
    metrics = {"daily_pnl_pct": -0.05}
    status = ks.evaluate(metrics)

    assert status.armed
    assert status.severity == "BLOCK"
    assert "daily_loss_limit" in status.triggered_by
    assert "daily loss" in status.reason.lower()


def test_daily_loss_arms_below_threshold(default_config: PeakConfig) -> None:
    """Test that daily loss beyond threshold arms the kill switch."""
    ks = KillSwitchLayer(default_config)

    # Worse than threshold: -6%
    metrics = {"daily_pnl_pct": -0.06}
    status = ks.evaluate(metrics)

    assert status.armed
    assert status.severity == "BLOCK"
    assert "daily_loss_limit" in status.triggered_by


def test_daily_loss_not_arm_above_threshold(default_config: PeakConfig) -> None:
    """Test that daily loss above threshold does not arm."""
    ks = KillSwitchLayer(default_config)

    # Better than threshold: -4.9%
    metrics = {"daily_pnl_pct": -0.049}
    status = ks.evaluate(metrics)

    assert not status.armed
    assert status.severity == "OK"
    assert len(status.triggered_by) == 0


def test_drawdown_arms(default_config: PeakConfig) -> None:
    """Test that drawdown at/above threshold arms."""
    ks = KillSwitchLayer(default_config)

    # At threshold: 20%
    metrics = {"current_drawdown_pct": 0.20}
    status = ks.evaluate(metrics)

    assert status.armed
    assert "max_drawdown" in status.triggered_by

    # Above threshold: 21%
    ks2 = KillSwitchLayer(default_config)
    metrics2 = {"current_drawdown_pct": 0.21}
    status2 = ks2.evaluate(metrics2)

    assert status2.armed
    assert "max_drawdown" in status2.triggered_by


def test_drawdown_not_arm_below_threshold(default_config: PeakConfig) -> None:
    """Test that drawdown below threshold does not arm."""
    ks = KillSwitchLayer(default_config)

    metrics = {"current_drawdown_pct": 0.19}
    status = ks.evaluate(metrics)

    assert not status.armed
    assert len(status.triggered_by) == 0


def test_volatility_arms_when_configured(default_config: PeakConfig) -> None:
    """Test that volatility check works when configured."""
    # Configure with volatility limit
    config = PeakConfig(
        raw={
            "risk": {
                "kill_switch": {
                    "enabled": True,
                    "daily_loss_limit_pct": 0.05,
                    "max_drawdown_pct": 0.20,
                    "max_volatility_pct": 0.50,  # 50% vol limit
                }
            }
        }
    )

    ks = KillSwitchLayer(config)

    # At/above threshold
    metrics = {"realized_vol_pct": 0.50}
    status = ks.evaluate(metrics)

    assert status.armed
    assert "max_volatility" in status.triggered_by


def test_volatility_ignored_when_not_configured(default_config: PeakConfig) -> None:
    """Test that volatility is ignored when not configured."""
    ks = KillSwitchLayer(default_config)

    # High volatility but no limit configured
    metrics = {"realized_vol_pct": 0.99}
    status = ks.evaluate(metrics)

    assert not status.armed


def test_sticky_armed_until_reset(default_config: PeakConfig) -> None:
    """Test that kill switch stays armed until reset."""
    ks = KillSwitchLayer(default_config)

    # Arm it
    metrics_bad = {"daily_pnl_pct": -0.06}
    status1 = ks.evaluate(metrics_bad)
    assert status1.armed

    # Now metrics are good but should stay armed
    metrics_good = {"daily_pnl_pct": 0.02}
    status2 = ks.evaluate(metrics_good)
    assert status2.armed  # Sticky!

    # Reset
    reset_status = ks.reset("manual_reset")
    assert not reset_status.armed

    # Now good metrics -> not armed
    status3 = ks.evaluate(metrics_good)
    assert not status3.armed


def test_missing_metrics_do_not_trigger(default_config: PeakConfig) -> None:
    """Test that missing/None metrics do not trigger kill switch."""
    ks = KillSwitchLayer(default_config)

    # Empty metrics
    status1 = ks.evaluate({})
    assert not status1.armed

    # None values
    metrics2 = {"daily_pnl_pct": None, "current_drawdown_pct": None}
    status2 = ks.evaluate(metrics2)
    assert not status2.armed


def test_multiple_triggers(default_config: PeakConfig) -> None:
    """Test that multiple conditions can trigger simultaneously."""
    ks = KillSwitchLayer(default_config)

    # Both daily loss and drawdown exceeded
    metrics = {"daily_pnl_pct": -0.06, "current_drawdown_pct": 0.25}
    status = ks.evaluate(metrics)

    assert status.armed
    assert len(status.triggered_by) == 2
    assert "daily_loss_limit" in status.triggered_by
    assert "max_drawdown" in status.triggered_by


def test_to_violations_when_armed() -> None:
    """Test that to_violations creates violations when armed."""
    from src.risk_layer.kill_switch import KillSwitchStatus

    status = KillSwitchStatus(
        armed=True,
        severity="BLOCK",
        reason="Test reason",
        triggered_by=["daily_loss_limit"],
        metrics_snapshot={"daily_pnl_pct": -0.06},
        timestamp_utc="2025-01-01T00:00:00Z",
    )

    violations = to_violations(status)

    assert len(violations) == 1
    assert violations[0].code == "KILL_SWITCH_ARMED"
    assert violations[0].severity == "CRITICAL"
    assert "armed" in violations[0].message.lower()
    assert "daily_loss_limit" in violations[0].details["triggered_by"]


def test_to_violations_when_not_armed() -> None:
    """Test that to_violations returns empty list when not armed."""
    from src.risk_layer.kill_switch import KillSwitchStatus

    status = KillSwitchStatus(
        armed=False,
        severity="OK",
        reason="OK",
        triggered_by=[],
        metrics_snapshot={},
        timestamp_utc="2025-01-01T00:00:00Z",
    )

    violations = to_violations(status)

    assert len(violations) == 0


def test_metrics_snapshot_captured(default_config: PeakConfig) -> None:
    """Test that metrics snapshot is captured in status."""
    ks = KillSwitchLayer(default_config)

    metrics = {"daily_pnl_pct": -0.06, "custom_field": "test"}
    status = ks.evaluate(metrics)

    assert status.metrics_snapshot == metrics
    assert "custom_field" in status.metrics_snapshot


def test_is_armed_property(default_config: PeakConfig) -> None:
    """Test the is_armed property."""
    ks = KillSwitchLayer(default_config)

    assert not ks.is_armed

    # Arm it
    metrics = {"daily_pnl_pct": -0.06}
    ks.evaluate(metrics)

    assert ks.is_armed

    # Reset
    ks.reset()
    assert not ks.is_armed


def test_reset_clears_state_completely(default_config: PeakConfig) -> None:
    """Test that reset clears all kill switch state."""
    ks = KillSwitchLayer(default_config)

    # Arm with multiple triggers
    metrics = {"daily_pnl_pct": -0.10, "current_drawdown_pct": 0.25}
    status_armed = ks.evaluate(metrics)
    assert status_armed.armed
    assert len(status_armed.triggered_by) == 2
    assert status_armed.severity == "BLOCK"

    # Reset
    status_reset = ks.reset("post_incident_review")
    assert not status_reset.armed
    assert status_reset.severity == "OK"
    assert len(status_reset.triggered_by) == 0
    assert "post_incident_review" in status_reset.reason

    # Verify internal state cleared
    assert not ks.is_armed


def test_last_status_property(default_config: PeakConfig) -> None:
    """Test the last_status property."""
    ks = KillSwitchLayer(default_config)

    # Initially None (not evaluated yet)
    assert ks.last_status is None

    # After evaluation, last_status is set
    metrics = {"daily_pnl_pct": -0.02}
    status1 = ks.evaluate(metrics)
    assert ks.last_status is not None
    assert ks.last_status.armed == status1.armed
    assert ks.last_status.reason == status1.reason

    # After arming, last_status reflects armed state
    metrics_bad = {"daily_pnl_pct": -0.10}
    status2 = ks.evaluate(metrics_bad)
    assert ks.last_status is not None
    assert ks.last_status.armed is True
    assert "daily_loss_limit" in ks.last_status.triggered_by

    # After reset, last_status reflects reset
    status_reset = ks.reset("test_reset")
    assert ks.last_status is not None
    assert ks.last_status.armed is False
    assert "test_reset" in ks.last_status.reason


def test_reset_preserves_reason_parameter(default_config: PeakConfig) -> None:
    """Test that reset includes the provided reason."""
    ks = KillSwitchLayer(default_config)

    # Arm it
    ks.evaluate({"daily_pnl_pct": -0.10})
    assert ks.is_armed

    # Reset with custom reason
    custom_reason = "incident_resolved_by_operator"
    status = ks.reset(custom_reason)

    assert not status.armed
    assert custom_reason in status.reason
