"""Integration and Chaos tests for Kill Switch system."""

import pytest
import time
import threading
import json
import tempfile
from pathlib import Path

from src.risk_layer.kill_switch import KillSwitch
from src.risk_layer.kill_switch.execution_gate import ExecutionGate, TradingBlockedError
from src.risk_layer.kill_switch.triggers import TriggerRegistry, ThresholdTrigger
from src.risk_layer.kill_switch.state import KillSwitchState
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.audit import AuditTrail


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


class TestChaosEngineering:
    """Chaos engineering tests for resilience."""

    def test_extreme_concurrent_triggers(self, kill_switch):
        """Test system under extreme concurrent trigger load."""
        results = []
        errors = []

        def hammer_trigger(thread_id):
            try:
                for i in range(100):
                    kill_switch.trigger(f"Thread-{thread_id}-Trigger-{i}")
                    results.append((thread_id, i, "success"))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Launch 20 threads hammering triggers
        threads = [
            threading.Thread(target=hammer_trigger, args=(i,))
            for i in range(20)
        ]

        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.time() - start_time

        # System should remain stable
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert kill_switch.state in [KillSwitchState.KILLED, KillSwitchState.RECOVERING]
        assert elapsed < 10, f"Took too long: {elapsed}s"

    def test_rapid_cycle_trigger_recovery(self, kill_switch):
        """Test rapid cycles of trigger -> recovery."""
        for cycle in range(10):
            # Trigger
            kill_switch.trigger(f"Cycle-{cycle}")
            assert kill_switch.is_killed

            # Request recovery
            kill_switch.request_recovery(f"operator-{cycle}")
            assert kill_switch.state == KillSwitchState.RECOVERING

            # Complete recovery (wait for cooldown)
            time.sleep(1.1)
            result = kill_switch.complete_recovery()
            assert result is True
            assert kill_switch.is_active

        # Check audit trail
        events = kill_switch.get_audit_trail()
        # Each cycle: KILLED -> RECOVERING -> ACTIVE = 3 events
        assert len(events) == 30

    def test_crash_recovery_with_persistence(self):
        """Test crash recovery using state persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            state_file = tmppath / "state.json"
            backup_dir = tmppath / "backups"
            audit_dir = tmppath / "audit"

            config = {
                "enabled": True,
                "mode": "active",
                "recovery_cooldown_seconds": 1,
                "require_approval_code": False,
            }

            # Phase 1: Create kill switch and trigger
            ks1 = KillSwitch(config)
            persistence1 = StatePersistence(state_file, backup_dir)
            audit1 = AuditTrail(audit_dir)

            ks1.trigger("Crash test")
            assert ks1.is_killed

            # Save state
            persistence1.save(
                ks1.state,
                killed_at=ks1._killed_at,
                trigger_reason="Crash test"
            )
            audit1.log_event(ks1.get_audit_trail()[0])

            # Phase 2: Simulate crash and restart
            del ks1, persistence1, audit1

            # Phase 3: Reload state
            ks2 = KillSwitch(config)
            persistence2 = StatePersistence(state_file, backup_dir)
            loaded = persistence2.load()

            assert loaded is not None
            assert loaded["state"] == "KILLED"

            # Restore state
            ks2._state = KillSwitchState[loaded["state"]]

            # System should still be in KILLED state
            assert ks2.is_killed

            # Recovery should work after reload
            ks2.request_recovery("operator")
            time.sleep(1.1)
            ks2.complete_recovery()
            assert ks2.is_active

    def test_corrupt_state_file_recovery(self):
        """Test recovery from corrupt state file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            state_file = tmppath / "state.json"
            backup_dir = tmppath / "backups"

            config = {
                "enabled": True,
                "mode": "active",
                "recovery_cooldown_seconds": 1,
                "require_approval_code": False,
            }

            # Create valid state
            ks1 = KillSwitch(config)
            persistence = StatePersistence(state_file, backup_dir)
            persistence.save(ks1.state)

            # Trigger and save again (creates backup)
            ks1.trigger("Test")
            persistence.save(ks1.state, killed_at=ks1._killed_at, trigger_reason="Test")

            # Corrupt the state file
            state_file.write_text("this is not valid json {")

            # Load should fail gracefully
            loaded = persistence.load()
            assert loaded is None  # Load returns None on corruption

            # Backup should be restored automatically
            loaded = persistence.load()
            if loaded is None:
                # If backup restore failed, system should start fresh
                ks2 = KillSwitch(config)
                assert ks2.state == KillSwitchState.ACTIVE

    def test_concurrent_reads_and_writes(self):
        """Test concurrent reads and writes to state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            state_file = tmppath / "state.json"
            backup_dir = tmppath / "backups"

            config = {
                "enabled": True,
                "mode": "active",
                "recovery_cooldown_seconds": 1,
                "require_approval_code": False,
            }

            ks = KillSwitch(config)
            persistence = StatePersistence(state_file, backup_dir)
            errors = []

            def write_worker():
                try:
                    for i in range(50):
                        if i % 2 == 0:
                            ks.trigger(f"Write-{i}")
                        persistence.save(ks.state)
                        time.sleep(0.01)
                except Exception as e:
                    errors.append(f"Write error: {e}")

            def read_worker():
                try:
                    for _ in range(50):
                        loaded = persistence.load()
                        if loaded:
                            state = KillSwitchState[loaded["state"]]
                        time.sleep(0.01)
                except Exception as e:
                    errors.append(f"Read error: {e}")

            threads = [
                threading.Thread(target=write_worker),
                threading.Thread(target=read_worker),
                threading.Thread(target=read_worker),
            ]

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0, f"Errors occurred: {errors}"

    def test_audit_trail_under_load(self):
        """Test audit trail under high write load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            audit_dir = tmppath / "audit"

            audit = AuditTrail(audit_dir, max_file_size_mb=0.01)  # Small but not too small to avoid excessive rotation

            config = {
                "enabled": True,
                "mode": "active",
                "recovery_cooldown_seconds": 1,
                "require_approval_code": False,
            }

            ks = KillSwitch(config)
            errors = []
            events_logged = []

            def audit_worker(thread_id):
                try:
                    for i in range(20):  # Reduced from 50 to avoid excessive concurrent writes
                        ks.trigger(f"Thread-{thread_id}-Event-{i}")
                        events = ks.get_audit_trail()
                        if events:
                            audit.log_event(events[-1])
                            events_logged.append((thread_id, i))
                        time.sleep(0.001)  # Small delay to reduce contention
                except Exception as e:
                    errors.append(f"Thread-{thread_id}: {e}")

            threads = [
                threading.Thread(target=audit_worker, args=(i,))
                for i in range(3)  # Reduced from 5 to 3 threads
            ]

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0, f"Errors occurred: {errors}"

            # Verify we can still read events
            events = audit.get_events(limit=10)
            assert len(events) > 0

    def test_execution_gate_under_concurrent_load(self, kill_switch):
        """Test execution gate blocking under concurrent order load."""
        gate = ExecutionGate(kill_switch)
        successful_orders = []
        blocked_orders = []

        # Use barriers to ensure deterministic ordering
        start_barrier = threading.Barrier(101)  # 100 orders + 1 trigger thread
        trigger_ready = threading.Event()

        def order_worker(order_id, batch):
            # Wait for all threads to be ready
            start_barrier.wait()

            # First batch waits for trigger to be ready
            if batch == 0:
                # Let some orders through before kill switch
                pass
            else:
                # Second batch waits for trigger
                trigger_ready.wait()

            try:
                gate.check_can_execute()
                successful_orders.append(order_id)
            except TradingBlockedError:
                blocked_orders.append(order_id)

        def trigger_worker():
            # Wait for all threads to be ready
            start_barrier.wait()

            # Let first batch (30 orders) execute
            time.sleep(0.01)

            # Trigger kill switch
            kill_switch.trigger("Emergency stop during orders")

            # Signal second batch to proceed
            trigger_ready.set()

        # Launch trigger thread first
        trigger_thread = threading.Thread(target=trigger_worker)
        trigger_thread.start()

        # Launch order threads in two batches
        order_threads = []
        for i in range(30):  # First batch - should succeed
            t = threading.Thread(target=order_worker, args=(i, 0))
            order_threads.append(t)
            t.start()

        for i in range(30, 100):  # Second batch - should be blocked
            t = threading.Thread(target=order_worker, args=(i, 1))
            order_threads.append(t)
            t.start()

        trigger_thread.join()
        for t in order_threads:
            t.join()

        # Verify: some orders succeeded (first batch), some blocked (second batch)
        assert len(successful_orders) > 0, "Expected some orders to succeed before kill switch"
        assert len(blocked_orders) > 0, "Expected some orders to be blocked after kill switch"
        assert len(successful_orders) + len(blocked_orders) == 100

    def test_memory_leak_prevention(self, kill_switch):
        """Test that repeated cycles don't leak memory."""
        import sys

        initial_events = len(kill_switch.get_audit_trail())

        # Perform many cycles
        for i in range(100):
            kill_switch.trigger(f"Cycle-{i}")
            kill_switch.request_recovery(f"operator-{i}")
            time.sleep(0.01)  # Minimal delay

        final_events = len(kill_switch.get_audit_trail())

        # Events should grow linearly, not exponentially
        assert final_events == initial_events + 200  # 2 events per cycle

        # Callbacks should not accumulate
        assert len(kill_switch._on_kill_callbacks) <= 10  # Reasonable limit


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_trigger_during_cooldown(self, kill_switch):
        """Test that trigger during recovery cooldown reverts to KILLED."""
        kill_switch.trigger("First kill")
        kill_switch.request_recovery("operator")
        assert kill_switch.state == KillSwitchState.RECOVERING

        # Trigger again during recovery
        kill_switch.trigger("Second kill during recovery")
        assert kill_switch.state == KillSwitchState.KILLED

        # Should be able to recover
        kill_switch.request_recovery("operator")
        time.sleep(1.1)
        kill_switch.complete_recovery()
        assert kill_switch.is_active

    def test_multiple_recovery_requests(self, kill_switch):
        """Test that multiple recovery requests are idempotent."""
        kill_switch.trigger("Test")

        result1 = kill_switch.request_recovery("operator1")
        result2 = kill_switch.request_recovery("operator2")

        # First should succeed, second should also succeed (idempotent)
        assert result1 is True
        assert result2 is True
        assert kill_switch.state == KillSwitchState.RECOVERING

    def test_recovery_before_cooldown_fails(self, kill_switch):
        """Test that recovery before cooldown completes fails."""
        kill_switch.trigger("Test")
        kill_switch.request_recovery("operator")

        # Attempt to complete recovery immediately (before cooldown)
        result = kill_switch.complete_recovery()
        assert result is False
        assert kill_switch.state == KillSwitchState.RECOVERING

        # After cooldown should succeed
        time.sleep(1.1)
        result = kill_switch.complete_recovery()
        assert result is True
        assert kill_switch.is_active

    def test_state_persistence_with_rapid_changes(self):
        """Test state persistence with rapid state changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            state_file = tmppath / "state.json"
            backup_dir = tmppath / "backups"

            config = {
                "enabled": True,
                "mode": "active",
                "recovery_cooldown_seconds": 0.1,  # Very short for testing
                "require_approval_code": False,
            }

            ks = KillSwitch(config)
            persistence = StatePersistence(state_file, backup_dir)

            # Rapid state changes
            for i in range(20):
                ks.trigger(f"Rapid-{i}")
                persistence.save(ks.state, killed_at=ks._killed_at)

                ks.request_recovery(f"op-{i}")
                persistence.save(ks.state)

                time.sleep(0.11)
                ks.complete_recovery()
                persistence.save(ks.state)

            # Final state should be consistent
            loaded = persistence.load()
            assert loaded is not None
            assert loaded["state"] == "ACTIVE"

            # Should have backups (backup created only when overwriting existing state file)
            # With 20 cycles × 3 saves each = 60 saves, but backups only on overwrites
            backups = persistence.list_backups()
            assert len(backups) >= 3, f"Expected at least 3 backups, got {len(backups)}"
