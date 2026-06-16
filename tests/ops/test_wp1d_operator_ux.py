"""
Tests for WP1D - Operator UX

Tests:
- Registry operations deterministic
- Status overview tracking
- Alert routing returns expected severity
"""

from datetime import datetime, timedelta

import pytest

from src.live.ops.alerts import AlertPriority, OperatorAlerts
from src.live.ops.registry import SessionRegistry
from src.live.ops.status import StatusOverview


class TestSessionRegistry:
    """Test session registry."""

    def test_create_session(self):
        """Test session creation."""
        registry = SessionRegistry()

        status = registry.create_session(
            "shadow_001",
            metadata={"strategy": "ma_cross"},
        )

        assert status.session_id == "shadow_001"
        assert status.status == "started"
        assert status.metadata["strategy"] == "ma_cross"

    def test_get_status(self):
        """Test get session status."""
        registry = SessionRegistry()
        registry.create_session("shadow_001")

        status = registry.get_status("shadow_001")

        assert status is not None
        assert status.session_id == "shadow_001"

    def test_get_status_not_found(self):
        """Test get status for non-existent session."""
        registry = SessionRegistry()

        status = registry.get_status("nonexistent")

        assert status is None

    def test_update_status(self):
        """Test status update."""
        registry = SessionRegistry()
        registry.create_session("shadow_001")

        updated = registry.update_status("shadow_001", "running")

        assert updated is not None
        assert updated.status == "running"

        # Verify via get_status
        status = registry.get_status("shadow_001")
        assert status.status == "running"

    def test_list_sessions(self):
        """Test list all sessions."""
        registry = SessionRegistry()

        registry.create_session("shadow_001")
        registry.create_session("shadow_002")
        registry.create_session("shadow_003")

        sessions = registry.list_sessions()

        assert len(sessions) == 3
        assert {s.session_id for s in sessions} == {
            "shadow_001",
            "shadow_002",
            "shadow_003",
        }

    def test_list_sessions_with_filter(self):
        """Test list sessions with status filter."""
        registry = SessionRegistry()

        registry.create_session("shadow_001")
        registry.create_session("shadow_002")
        registry.update_status("shadow_002", "completed")

        # Filter by started
        started_sessions = registry.list_sessions(status_filter="started")
        assert len(started_sessions) == 1
        assert started_sessions[0].session_id == "shadow_001"

        # Filter by completed
        completed_sessions = registry.list_sessions(status_filter="completed")
        assert len(completed_sessions) == 1
        assert completed_sessions[0].session_id == "shadow_002"

    def test_get_summary(self):
        """Test get registry summary."""
        registry = SessionRegistry()

        registry.create_session("shadow_001")
        registry.create_session("shadow_002")
        registry.create_session("shadow_003")

        registry.update_status("shadow_002", "running")
        registry.update_status("shadow_003", "completed")

        summary = registry.get_summary()

        assert summary["total_sessions"] == 3
        assert summary["by_status"]["started"] == 1
        assert summary["by_status"]["running"] == 1
        assert summary["by_status"]["completed"] == 1

    def test_sessions_sorted_by_time(self, monkeypatch):
        """Test sessions sorted by start time (newest first)."""
        registry = SessionRegistry()
        base = datetime(2026, 1, 1, 12, 0, 0)
        utcnow_sequence = [
            base,
            base,
            base + timedelta(seconds=1),
            base + timedelta(seconds=1),
            base + timedelta(seconds=2),
            base + timedelta(seconds=2),
        ]
        utcnow_index = [0]

        def fake_utcnow():
            ts = utcnow_sequence[utcnow_index[0]]
            utcnow_index[0] += 1
            return ts

        class FakeDateTime:
            utcnow = staticmethod(fake_utcnow)

        monkeypatch.setattr("src.live.ops.registry.datetime", FakeDateTime)

        registry.create_session("shadow_001")
        registry.create_session("shadow_002")
        registry.create_session("shadow_003")

        sessions = registry.list_sessions()

        # Should be newest first
        assert sessions[0].session_id == "shadow_003"
        assert sessions[1].session_id == "shadow_002"
        assert sessions[2].session_id == "shadow_001"


class TestStatusOverview:
    """Test status overview."""

    def test_start_tracking(self, monkeypatch):
        """Test start tracking."""
        monotonic_values = iter([100.0, 100.0, 100.15])
        monkeypatch.setattr(
            "src.live.ops.status.time.monotonic",
            lambda: next(monotonic_values),
        )

        overview = StatusOverview()
        overview.start()

        status = overview.get_status()

        assert status.system_uptime_s == pytest.approx(0.15)
        assert status.data_feed_uptime_s == pytest.approx(0.15)

    def test_record_reconnect(self, monkeypatch):
        """Test record reconnect."""
        monotonic_values = iter([100.0, 100.05, 100.05, 100.20])
        monkeypatch.setattr(
            "src.live.ops.status.time.monotonic",
            lambda: next(monotonic_values),
        )

        overview = StatusOverview()
        overview.start()

        overview.record_reconnect()

        status = overview.get_status()

        assert status.last_reconnect_ts is not None
        assert status.system_uptime_s == pytest.approx(0.20)
        assert status.data_feed_uptime_s == pytest.approx(0.15)
        # Data feed uptime should reset after reconnect
        assert status.data_feed_uptime_s < status.system_uptime_s

    def test_record_drift_report(self):
        """Test record drift report."""
        overview = StatusOverview()
        overview.start()

        overview.record_drift_report()

        status = overview.get_status()

        assert status.last_drift_report_ts is not None

    def test_update_metadata(self):
        """Test update metadata."""
        overview = StatusOverview()
        overview.start()

        overview.update_metadata("strategy", "ma_cross")
        overview.update_metadata("symbols", ["BTC/USD", "ETH/USD"])

        status = overview.get_status()

        assert status.metadata["strategy"] == "ma_cross"
        assert status.metadata["symbols"] == ["BTC/USD", "ETH/USD"]

    def test_status_before_start(self):
        """Test status before start."""
        overview = StatusOverview()

        status = overview.get_status()

        assert status.system_uptime_s == 0.0
        assert status.data_feed_uptime_s == 0.0


class TestOperatorAlerts:
    """Test operator alerts."""

    def test_raise_p1_alert(self):
        """Test raise P1 alert."""
        alerts = OperatorAlerts()

        alert = alerts.raise_p1(
            "DRIFT_CRITICAL",
            "Critical drift detected",
            metadata={"drift": 0.5},
        )

        assert alert.priority == AlertPriority.P1
        assert alert.code == "DRIFT_CRITICAL"
        assert alert.message == "Critical drift detected"
        assert alert.metadata["drift"] == 0.5
        assert "drift_critical.md" in alert.runbook_link

    def test_raise_p2_alert(self):
        """Test raise P2 alert."""
        alerts = OperatorAlerts()

        alert = alerts.raise_p2(
            "DRIFT_HIGH",
            "High drift detected",
        )

        assert alert.priority == AlertPriority.P2
        assert alert.code == "DRIFT_HIGH"

    def test_runbook_mapping(self):
        """Test runbook link mapping."""
        alerts = OperatorAlerts()

        alert_critical = alerts.raise_p1("DRIFT_CRITICAL", "Test")
        alert_data = alerts.raise_p1("DATA_FEED_DOWN", "Test")
        alert_risk = alerts.raise_p1("RISK_LIMIT_BREACH", "Test")

        assert "drift_critical.md" in alert_critical.runbook_link
        assert "data_feed_down.md" in alert_data.runbook_link
        assert "risk_limit_breach.md" in alert_risk.runbook_link

    def test_runbook_fallback(self):
        """Test runbook fallback for unknown codes."""
        alerts = OperatorAlerts()

        alert = alerts.raise_p1("UNKNOWN_CODE", "Test")

        assert "general.md" in alert.runbook_link

    def test_get_recent_alerts(self):
        """Test get recent alerts."""
        alerts = OperatorAlerts()

        alerts.raise_p1("DRIFT_CRITICAL", "Test 1")
        alerts.raise_p2("DRIFT_HIGH", "Test 2")
        alerts.raise_p1("DATA_FEED_DOWN", "Test 3")

        recent = alerts.get_recent_alerts(hours=24)

        assert len(recent) == 3

    def test_get_recent_alerts_with_filter(self):
        """Test get recent alerts with priority filter."""
        alerts = OperatorAlerts()

        alerts.raise_p1("DRIFT_CRITICAL", "Test 1")
        alerts.raise_p2("DRIFT_HIGH", "Test 2")
        alerts.raise_p1("DATA_FEED_DOWN", "Test 3")

        p1_alerts = alerts.get_recent_alerts(hours=24, priority_filter=AlertPriority.P1)

        assert len(p1_alerts) == 2
        assert all(a.priority == AlertPriority.P1 for a in p1_alerts)

    def test_get_by_priority(self):
        """Test get alert count by priority."""
        alerts = OperatorAlerts()

        alerts.raise_p1("DRIFT_CRITICAL", "Test 1")
        alerts.raise_p1("DATA_FEED_DOWN", "Test 2")
        alerts.raise_p2("DRIFT_HIGH", "Test 3")

        counts = alerts.get_by_priority()

        assert counts["P1"] == 2
        assert counts["P2"] == 1
        assert counts["P3"] == 0

    def test_alerts_sorted_by_time(self, monkeypatch):
        """Test alerts sorted by timestamp (newest first)."""
        alerts = OperatorAlerts()
        base = datetime(2026, 1, 1, 12, 0, 0)
        utcnow_sequence = [
            base,
            base + timedelta(seconds=1),
            base + timedelta(seconds=2),
            base + timedelta(seconds=3),
        ]
        utcnow_index = [0]

        def fake_utcnow():
            ts = utcnow_sequence[utcnow_index[0]]
            utcnow_index[0] += 1
            return ts

        class FakeDateTime:
            utcnow = staticmethod(fake_utcnow)

        monkeypatch.setattr("src.live.ops.alerts.datetime", FakeDateTime)

        alerts.raise_p1("DRIFT_CRITICAL", "Test 1")
        alerts.raise_p2("DRIFT_HIGH", "Test 2")
        alerts.raise_p1("DATA_FEED_DOWN", "Test 3")

        recent = alerts.get_recent_alerts(hours=24)

        # Should be newest first
        assert recent[0].message == "Test 3"
        assert recent[1].message == "Test 2"
        assert recent[2].message == "Test 1"
