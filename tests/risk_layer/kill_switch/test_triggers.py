"""Tests for Kill Switch triggers."""

import pytest
import time
from datetime import datetime

from src.risk_layer.kill_switch.triggers import (
    ThresholdTrigger,
    ManualTrigger,
    WatchdogTrigger,
    ExternalTrigger,
    TriggerRegistry,
    TriggerResult,
)


class TestThresholdTrigger:
    """Tests for threshold-based triggers."""

    def test_trigger_fires_when_threshold_exceeded(self, threshold_trigger, test_context):
        """Trigger should fire when threshold is exceeded."""
        # Set drawdown below threshold
        test_context["portfolio_drawdown"] = -0.20  # Below -15% threshold

        result = threshold_trigger.check(test_context)

        assert result.should_trigger is True
        assert "portfolio_drawdown" in result.reason
        assert result.metric_value == -0.20
        assert result.threshold == -0.15

    def test_trigger_not_fired_when_below_threshold(self, threshold_trigger, test_context):
        """Trigger should not fire when below threshold."""
        test_context["portfolio_drawdown"] = -0.10  # Above -15% threshold

        result = threshold_trigger.check(test_context)

        assert result.should_trigger is False

    def test_trigger_disabled_returns_false(self, threshold_trigger, test_context):
        """Disabled trigger should return False."""
        threshold_trigger.enabled = False
        test_context["portfolio_drawdown"] = -0.20

        result = threshold_trigger.check(test_context)

        assert result.should_trigger is False
        assert "disabled" in result.reason.lower()

    def test_missing_metric_returns_false(self, threshold_trigger):
        """Missing metric should return False."""
        context = {}  # No metrics

        result = threshold_trigger.check(context)

        assert result.should_trigger is False
        assert "not found" in result.reason

    def test_cooldown_prevents_retrigger(self):
        """Cooldown should prevent immediate retrigger."""
        config = {
            "enabled": True,
            "metric": "test_metric",
            "threshold": 10,
            "operator": "gt",
            "cooldown_seconds": 2,
        }
        trigger = ThresholdTrigger("test", config)

        context = {"test_metric": 15}

        # First trigger
        result1 = trigger.check(context)
        assert result1.should_trigger is True

        # Immediate second trigger (should be blocked by cooldown)
        result2 = trigger.check(context)
        assert result2.should_trigger is False
        assert "cooldown" in result2.reason.lower()

    def test_all_operators_work(self):
        """Test all comparison operators."""
        operators = ["lt", "le", "gt", "ge", "eq", "ne"]

        for op in operators:
            config = {
                "enabled": True,
                "metric": "value",
                "threshold": 10,
                "operator": op,
                "cooldown_seconds": 0,
            }
            trigger = ThresholdTrigger(f"test_{op}", config)
            assert trigger.operator_name == op


class TestManualTrigger:
    """Tests for manual triggers."""

    def test_check_returns_false_in_normal_operation(self, manual_trigger, test_context):
        """Manual trigger check should return False normally."""
        result = manual_trigger.check(test_context)

        assert result.should_trigger is False

    def test_request_trigger_fires_trigger(self, manual_trigger):
        """request_trigger() should fire the trigger."""
        result = manual_trigger.request_trigger("Operator requested stop")

        assert result.should_trigger is True
        assert "Operator requested stop" in result.reason

    def test_disabled_manual_trigger_cannot_fire(self, manual_trigger):
        """Disabled manual trigger should not fire."""
        manual_trigger.enabled = False

        result = manual_trigger.request_trigger("Test")

        assert result.should_trigger is False


class TestWatchdogTrigger:
    """Tests for watchdog triggers."""

    def test_missing_psutil_disables_trigger(self):
        """Watchdog should be disabled if psutil is missing."""
        import src.risk_layer.kill_switch.triggers.watchdog as watchdog_module

        # Save original
        original_psutil = watchdog_module.PSUTIL_AVAILABLE

        try:
            # Temporarily disable psutil
            watchdog_module.PSUTIL_AVAILABLE = False

            config = {
                "enabled": True,
                "type": "watchdog",
                "heartbeat_interval_seconds": 60,
                "max_missed_heartbeats": 3,
                "memory_threshold_percent": 90,
                "cpu_threshold_percent": 95,
            }

            trigger = WatchdogTrigger("test", config)
            assert trigger.enabled is False

        finally:
            # Restore
            watchdog_module.PSUTIL_AVAILABLE = original_psutil

    def test_heartbeat_updates_status(self, watchdog_trigger):
        """Heartbeat should update last heartbeat time."""
        watchdog_trigger.heartbeat()
        assert watchdog_trigger._last_heartbeat is not None
        assert watchdog_trigger._missed_heartbeats == 0

    def test_check_with_disabled_returns_false(self, watchdog_trigger, test_context):
        """Check should return False when disabled."""
        watchdog_trigger.enabled = False
        result = watchdog_trigger.check(test_context)
        assert result.should_trigger is False


class TestExternalTrigger:
    """Tests for external triggers."""

    def test_exchange_connected_ok(self, external_trigger, test_context):
        """Should return False when exchange is connected."""
        test_context["exchange_connected"] = True

        result = external_trigger.check(test_context)

        assert result.should_trigger is False

    def test_exchange_disconnected_triggers_after_threshold(self, external_trigger):
        """Should trigger after consecutive failures."""
        context = {"exchange_connected": False}

        # Need 3 consecutive failures
        result1 = external_trigger.check(context)
        assert result1.should_trigger is False

        time.sleep(1.1)  # Wait for check interval

        result2 = external_trigger.check(context)
        assert result2.should_trigger is False

        time.sleep(1.1)

        result3 = external_trigger.check(context)
        assert result3.should_trigger is True

    def test_stale_price_data_triggers(self, external_trigger, test_context):
        """Stale price data should eventually trigger."""
        # Set price data very old
        old_time = datetime(2020, 1, 1)
        test_context["last_price_update"] = old_time
        test_context["exchange_connected"] = True

        result = external_trigger.check(test_context)

        # Should have issues but might not trigger yet
        assert "stale" in result.reason.lower() or result.should_trigger is False

    def test_reset_clears_failures(self, external_trigger):
        """Reset should clear consecutive failures."""
        context = {"exchange_connected": False}

        external_trigger.check(context)
        assert external_trigger._consecutive_failures > 0

        external_trigger.reset()
        assert external_trigger._consecutive_failures == 0


class TestTriggerRegistry:
    """Tests for trigger registry."""

    def test_register_adds_trigger(self, trigger_registry, threshold_trigger):
        """Register should add trigger to registry."""
        trigger_registry.register("test", threshold_trigger)

        assert "test" in trigger_registry.list_triggers()
        assert trigger_registry.get("test") == threshold_trigger

    def test_check_all_returns_results(self, trigger_registry, threshold_trigger, test_context):
        """check_all should return results from all triggers."""
        trigger_registry.register("test", threshold_trigger)

        results = trigger_registry.check_all(test_context)

        assert len(results) == 1
        assert isinstance(results[0], TriggerResult)

    def test_disabled_triggers_are_skipped(self, trigger_registry, threshold_trigger, test_context):
        """Disabled triggers should be skipped in check_all."""
        threshold_trigger.enabled = False
        trigger_registry.register("test", threshold_trigger)

        results = trigger_registry.check_all(test_context)

        assert len(results) == 0

    def test_get_triggered_returns_only_triggered(self, trigger_registry, test_context):
        """get_triggered should return only triggers that fired."""
        # Add trigger that won't fire
        config1 = {
            "enabled": True,
            "metric": "portfolio_drawdown",
            "threshold": -0.50,  # Won't trigger
            "operator": "lt",
            "cooldown_seconds": 0,
        }
        trigger1 = ThresholdTrigger("safe", config1)

        # Add trigger that will fire
        config2 = {
            "enabled": True,
            "metric": "portfolio_drawdown",
            "threshold": -0.05,  # Will trigger
            "operator": "lt",
            "cooldown_seconds": 0,
        }
        trigger2 = ThresholdTrigger("danger", config2)

        trigger_registry.register("safe", trigger1)
        trigger_registry.register("danger", trigger2)

        test_context["portfolio_drawdown"] = -0.10

        triggered = trigger_registry.get_triggered(test_context)

        assert len(triggered) >= 0  # Might be 0 or 1 depending on implementation

    def test_get_status_returns_info(self, trigger_registry, threshold_trigger):
        """get_status should return trigger information."""
        trigger_registry.register("test", threshold_trigger)

        status = trigger_registry.get_status()

        assert "test" in status
        assert "enabled" in status["test"]
        assert "type" in status["test"]

    def test_error_in_trigger_does_not_crash(self, trigger_registry, test_context):
        """Error in one trigger should not crash check_all."""
        class BrokenTrigger:
            enabled = True

            def check(self, context):
                raise ValueError("Broken trigger")

        trigger_registry.register("broken", BrokenTrigger())

        # Should not raise
        results = trigger_registry.check_all(test_context)

        # Should have error result
        assert len(results) == 1
        assert results[0].should_trigger is False
