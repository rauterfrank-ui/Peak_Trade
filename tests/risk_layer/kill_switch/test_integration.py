"""Integration tests for Kill Switch system."""

import pytest
import time
import threading

from src.risk_layer.kill_switch import KillSwitch
from src.risk_layer.kill_switch.execution_gate import ExecutionGate, TradingBlockedError
from src.risk_layer.kill_switch.triggers import TriggerRegistry, ThresholdTrigger


class TestExecutionGateIntegration:
    """Test execution gate integration with kill switch."""

    def test_gate_allows_execution_when_active(self, kill_switch):
        """Gate should allow execution when kill switch is active."""
        gate = ExecutionGate(kill_switch)

        assert gate.check_can_execute() is True
        assert not gate.is_blocked()

    def test_gate_blocks_execution_when_killed(self, kill_switch):
        """Gate should block execution when kill switch is killed."""
        gate = ExecutionGate(kill_switch)

        kill_switch.trigger("Test")

        assert gate.is_blocked() is True

        with pytest.raises(TradingBlockedError):
            gate.check_can_execute()

    def test_gate_blocks_during_recovery(self, kill_switch):
        """Gate should block execution during recovery."""
        gate = ExecutionGate(kill_switch)

        kill_switch.trigger("Test")
        kill_switch.request_recovery("operator")

        assert gate.is_blocked() is True

        with pytest.raises(TradingBlockedError):
            gate.check_can_execute()

    def test_gate_allows_after_recovery(self, kill_switch):
        """Gate should allow execution after recovery completes."""
        gate = ExecutionGate(kill_switch)

        kill_switch.trigger("Test")
        kill_switch.request_recovery("operator")
        time.sleep(1.1)  # Wait for cooldown
        kill_switch.complete_recovery()

        assert gate.check_can_execute() is True
        assert not gate.is_blocked()

    def test_execute_with_gate_works(self, kill_switch):
        """execute_with_gate should work correctly."""
        gate = ExecutionGate(kill_switch)

        def mock_order():
            return "order_executed"

        result = gate.execute_with_gate(mock_order)
        assert result == "order_executed"

    def test_execute_with_gate_raises_when_blocked(self, kill_switch):
        """execute_with_gate should raise when blocked."""
        gate = ExecutionGate(kill_switch)
        kill_switch.trigger("Test")

        def mock_order():
            return "order_executed"

        with pytest.raises(TradingBlockedError):
            gate.execute_with_gate(mock_order)

    def test_gate_as_context_manager(self, kill_switch):
        """Gate should work as context manager."""
        gate = ExecutionGate(kill_switch)

        executed = False
        with gate:
            executed = True

        assert executed is True

    def test_gate_context_manager_raises_when_blocked(self, kill_switch):
        """Gate context manager should raise when blocked."""
        gate = ExecutionGate(kill_switch)
        kill_switch.trigger("Test")

        with pytest.raises(TradingBlockedError):
            with gate:
                pass


class TestTriggerIntegration:
    """Test trigger integration with kill switch."""

    def test_threshold_trigger_activates_kill_switch(self, kill_switch):
        """Threshold trigger should activate kill switch."""
        registry = TriggerRegistry()

        config = {
            "enabled": True,
            "metric": "portfolio_drawdown",
            "threshold": -0.15,
            "operator": "lt",
            "cooldown_seconds": 0,
        }
        trigger = ThresholdTrigger("drawdown", config)
        registry.register("drawdown", trigger)

        # Check with bad drawdown
        context = {"portfolio_drawdown": -0.20}
        results = registry.check_all(context)

        # If any triggered, activate kill switch
        for result in results:
            if result.should_trigger:
                kill_switch.trigger(result.reason, triggered_by="threshold")

        assert kill_switch.is_killed

    def test_multiple_triggers_can_fire(self):
        """Multiple triggers can fire simultaneously."""
        registry = TriggerRegistry()

        # Add multiple triggers
        config1 = {
            "enabled": True,
            "metric": "portfolio_drawdown",
            "threshold": -0.15,
            "operator": "lt",
            "cooldown_seconds": 0,
        }
        config2 = {
            "enabled": True,
            "metric": "daily_pnl",
            "threshold": -0.05,
            "operator": "lt",
            "cooldown_seconds": 0,
        }

        registry.register("drawdown", ThresholdTrigger("drawdown", config1))
        registry.register("daily_loss", ThresholdTrigger("daily_loss", config2))

        # Context that triggers both
        context = {
            "portfolio_drawdown": -0.20,
            "daily_pnl": -0.08,
        }

        results = registry.check_all(context)
        triggered = [r for r in results if r.should_trigger]

        assert len(triggered) == 2


class TestConcurrency:
    """Test concurrent access to kill switch."""

    def test_concurrent_triggers_are_safe(self, kill_switch):
        """Concurrent triggers should be thread-safe."""
        results = []

        def trigger_worker(reason):
            result = kill_switch.trigger(reason)
            results.append((reason, result))

        # Launch 10 concurrent triggers
        threads = [
            threading.Thread(target=trigger_worker, args=(f"Trigger-{i}",))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should return True (first triggers, rest are idempotent)
        assert all(r[1] for r in results)
        assert kill_switch.is_killed

    def test_concurrent_status_reads_are_safe(self, kill_switch):
        """Concurrent status reads should be thread-safe."""
        states = []

        def read_worker():
            for _ in range(100):
                state = kill_switch.state
                states.append(state.name)

        # Launch multiple readers
        threads = [threading.Thread(target=read_worker) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All reads should succeed (no errors)
        assert len(states) == 500

    def test_concurrent_trigger_and_recovery(self, kill_switch):
        """Concurrent trigger and recovery should be safe."""
        def trigger_loop():
            for i in range(10):
                kill_switch.trigger(f"Trigger-{i}")
                time.sleep(0.01)

        def recovery_loop():
            for i in range(10):
                if kill_switch.is_killed:
                    kill_switch.request_recovery(f"operator-{i}")
                time.sleep(0.01)

        t1 = threading.Thread(target=trigger_loop)
        t2 = threading.Thread(target=recovery_loop)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Should end in a consistent state
        assert kill_switch.state.name in ["KILLED", "RECOVERING", "ACTIVE"]


class TestFullWorkflow:
    """Test complete kill switch workflow."""

    def test_complete_workflow_trigger_to_recovery(self, kill_switch):
        """Test complete workflow from trigger to recovery."""
        # 1. Initial state
        assert kill_switch.is_active

        # 2. Trigger
        kill_switch.trigger("Emergency stop", triggered_by="operator")
        assert kill_switch.is_killed
        assert kill_switch.state.name == "KILLED"

        # 3. Request recovery
        kill_switch.request_recovery("operator", approval_code="TEST")
        assert kill_switch.state.name == "RECOVERING"

        # 4. Wait for cooldown
        time.sleep(1.1)

        # 5. Complete recovery
        result = kill_switch.complete_recovery()
        assert result is True
        assert kill_switch.is_active

        # 6. Check audit trail
        events = kill_switch.get_audit_trail()
        assert len(events) == 3  # KILLED, RECOVERING, ACTIVE

        # Verify event sequence
        assert events[0].new_state.name == "KILLED"
        assert events[1].new_state.name == "RECOVERING"
        assert events[2].new_state.name == "ACTIVE"
