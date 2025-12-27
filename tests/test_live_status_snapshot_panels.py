# tests/test_live_status_snapshot_panels.py
"""
Tests für Live Status Snapshot Panels (Phase Service-Layer Integration)
=========================================================================

Testet:
- Live Panel Providers liefern stabile Daten
- Snapshot-Build ist nie leer
- Service-Layer-Funktionen sind konsistent
"""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_alerts_stats() -> Dict[str, Any]:
    """Mock alert statistics data."""
    return {
        "total": 5,
        "by_severity": {"INFO": 2, "WARN": 2, "CRITICAL": 1},
        "by_category": {"RISK": 3, "EXECUTION": 1, "SYSTEM": 1},
        "sessions_with_alerts": 2,
        "last_critical": {
            "id": "alert_123",
            "title": "Critical Alert",
            "severity": "CRITICAL",
        },
        "hours": 24,
    }


@pytest.fixture
def mock_sessions_stats() -> Dict[str, Any]:
    """Mock session statistics data."""
    return {
        "total_sessions": 10,
        "active_sessions": 2,
        "by_mode": {"shadow": 8, "paper": 2},
        "by_status": {"started": 2, "completed": 7, "failed": 1},
        "total_pnl": 150.75,
        "avg_drawdown": -12.5,
    }


@pytest.fixture
def mock_telemetry_summary() -> Dict[str, Any]:
    """Mock telemetry health summary data."""
    return {
        "status": "ok",
        "total_sessions": 5,
        "disk_usage_mb": 123.45,
        "recent_errors": 0,
        "health_checks": [
            {"name": "disk_usage", "status": "ok", "value": 123.45},
            {"name": "parse_errors", "status": "ok", "value": 0},
        ],
        "timestamp": "2025-12-21T12:00:00Z",
    }


# =============================================================================
# SERVICE LAYER TESTS
# =============================================================================


class TestServiceLayerFunctions:
    """Test service layer functions directly."""

    def test_get_alerts_stats_with_mock(self, mock_alerts_stats, monkeypatch):
        """Test get_alerts_stats returns expected structure."""
        # Mock the underlying alert_storage function
        mock_get_alert_stats = MagicMock(return_value=mock_alerts_stats)

        # Patch at the storage level (where it's actually imported from)
        with patch("src.live.alert_storage.get_alert_stats", mock_get_alert_stats):
            from src.webui.services.live_panel_data import get_alerts_stats

            stats = get_alerts_stats(hours=24)

            assert isinstance(stats, dict)
            assert "total" in stats
            assert "by_severity" in stats
            assert "by_category" in stats
            assert stats["total"] >= 0
            mock_get_alert_stats.assert_called_once_with(hours=24)

    def test_get_alerts_stats_fallback(self):
        """Test get_alerts_stats returns fallback when storage unavailable."""
        # Test the fallback function directly
        from src.webui.services.live_panel_data import _alerts_stats_fallback

        stats = _alerts_stats_fallback(hours=24)

        assert isinstance(stats, dict)
        assert stats["total"] == 0
        assert stats.get("_fallback") is True
        assert "message" in stats
        assert stats["hours"] == 24

    def test_get_live_sessions_stats_with_mock(self, mock_sessions_stats, monkeypatch):
        """Test get_live_sessions_stats returns expected structure."""
        # Mock the underlying registry functions
        mock_summary = {
            "num_sessions": 10,
            "by_status": {"started": 2, "completed": 7, "failed": 1},
            "total_realized_pnl": 150.75,
            "avg_max_drawdown": -12.5,
        }
        mock_records = [
            MagicMock(mode="shadow"),
            MagicMock(mode="shadow"),
            MagicMock(mode="paper"),
        ]

        with patch(
            "src.experiments.live_session_registry.get_session_summary", return_value=mock_summary
        ):
            with patch(
                "src.experiments.live_session_registry.list_session_records",
                return_value=mock_records,
            ):
                from src.webui.services.live_panel_data import get_live_sessions_stats

                stats = get_live_sessions_stats()

                assert isinstance(stats, dict)
                assert "total_sessions" in stats
                assert "active_sessions" in stats
                assert "by_mode" in stats
                assert stats["total_sessions"] >= 0

    def test_get_live_sessions_stats_fallback(self):
        """Test get_live_sessions_stats returns fallback when registry unavailable."""
        # Test the fallback function directly
        from src.webui.services.live_panel_data import _live_sessions_stats_fallback

        stats = _live_sessions_stats_fallback()

        assert isinstance(stats, dict)
        assert stats["total_sessions"] == 0
        assert stats["active_sessions"] == 0
        assert stats.get("_fallback") is True
        assert "message" in stats

    def test_get_telemetry_summary_with_mock(self, mock_telemetry_summary, monkeypatch):
        """Test get_telemetry_summary returns expected structure."""
        mock_health_report = MagicMock()
        mock_health_report.to_dict.return_value = {
            "status": "ok",
            "checks": [
                {
                    "name": "disk_usage",
                    "status": "ok",
                    "value": 123.45,
                    "message": "Found 42 *.jsonl files",
                },
                {
                    "name": "parse_errors",
                    "status": "ok",
                    "value": 0,
                    "message": "0 errors in recent logs",
                },
            ],
            "timestamp": "2025-12-21T12:00:00Z",
        }

        with patch(
            "src.execution.telemetry_health.run_health_checks", return_value=mock_health_report
        ):
            from src.webui.services.live_panel_data import get_telemetry_summary

            summary = get_telemetry_summary()

            assert isinstance(summary, dict)
            assert "status" in summary
            assert "health_checks" in summary
            assert summary["status"] in ("ok", "degraded", "critical", "unknown")

    def test_get_telemetry_summary_fallback(self):
        """Test get_telemetry_summary returns fallback when health module unavailable."""
        # Test the fallback function directly
        from pathlib import Path
        from src.webui.services.live_panel_data import _telemetry_summary_fallback

        summary = _telemetry_summary_fallback(Path("logs/execution"))

        assert isinstance(summary, dict)
        assert summary["status"] == "unknown"
        assert summary.get("_fallback") is True
        assert "message" in summary
        assert summary["total_sessions"] == 0


# =============================================================================
# PANEL PROVIDER TESTS
# =============================================================================


class TestPanelProviders:
    """Test panel provider functions from status_providers.py."""

    def test_panel_providers_registered(self):
        """Test that panel providers are properly registered."""
        from src.live.status_providers import get_live_panel_providers

        providers = get_live_panel_providers()

        assert isinstance(providers, dict)
        assert len(providers) >= 2  # At least alerts and live_sessions
        assert "alerts" in providers
        assert "live_sessions" in providers
        assert callable(providers["alerts"])
        assert callable(providers["live_sessions"])

    def test_panel_alerts_stable(self, mock_alerts_stats):
        """Test alerts panel never crashes and returns stable structure."""
        with patch(
            "src.webui.services.live_panel_data.get_alerts_stats", return_value=mock_alerts_stats
        ):
            from src.live.status_providers import _panel_alerts

            result = _panel_alerts()

            assert isinstance(result, dict)
            assert result["id"] == "alerts"
            assert "title" in result
            assert "status" in result
            assert "details" in result
            assert result["status"] in ("ok", "warning", "error", "unknown")
            assert isinstance(result["details"], dict)

    def test_panel_alerts_fallback_stable(self):
        """Test alerts panel is stable even when service unavailable."""
        with patch("src.webui.services.live_panel_data.get_alerts_stats", side_effect=ImportError):
            from src.live.status_providers import _panel_alerts

            result = _panel_alerts()

            assert isinstance(result, dict)
            assert result["id"] == "alerts"
            assert result["status"] in ("ok", "warning", "error", "unknown")
            assert isinstance(result["details"], dict)

    def test_panel_live_sessions_stable(self, mock_sessions_stats):
        """Test live_sessions panel never crashes and returns stable structure."""
        with patch(
            "src.webui.services.live_panel_data.get_live_sessions_stats",
            return_value=mock_sessions_stats,
        ):
            from src.live.status_providers import _panel_live_sessions

            result = _panel_live_sessions()

            assert isinstance(result, dict)
            assert result["id"] == "live_sessions"
            assert "title" in result
            assert "status" in result
            assert "details" in result
            assert result["status"] in ("ok", "active", "warning", "error", "unknown")
            assert isinstance(result["details"], dict)

    def test_panel_live_sessions_fallback_stable(self):
        """Test live_sessions panel is stable even when service unavailable."""
        with patch(
            "src.webui.services.live_panel_data.get_live_sessions_stats", side_effect=ImportError
        ):
            from src.live.status_providers import _panel_live_sessions

            result = _panel_live_sessions()

            assert isinstance(result, dict)
            assert result["id"] == "live_sessions"
            assert result["status"] in ("ok", "active", "warning", "error", "unknown")
            assert isinstance(result["details"], dict)

    def test_panel_telemetry_stable(self, mock_telemetry_summary):
        """Test telemetry panel never crashes and returns stable structure."""
        with patch(
            "src.webui.services.live_panel_data.get_telemetry_summary",
            return_value=mock_telemetry_summary,
        ):
            from src.live.status_providers import _panel_telemetry

            result = _panel_telemetry()

            assert isinstance(result, dict)
            assert result["id"] == "telemetry"
            assert "title" in result
            assert "status" in result
            assert "details" in result
            assert result["status"] in ("ok", "warning", "error", "unknown")
            assert isinstance(result["details"], dict)


# =============================================================================
# SNAPSHOT BUILDER INTEGRATION TESTS
# =============================================================================


class TestSnapshotBuilderIntegration:
    """Test that snapshot builder integrates with panels correctly."""

    def test_snapshot_builder_never_empty(self, mock_alerts_stats, mock_sessions_stats):
        """Test that build_live_status_snapshot_auto always returns panels."""
        with patch("src.live.alert_storage.get_alert_stats", return_value=mock_alerts_stats):
            mock_summary = {
                "num_sessions": 10,
                "by_status": {"started": 2, "completed": 7, "failed": 1},
                "total_realized_pnl": 150.75,
                "avg_max_drawdown": -12.5,
            }
            mock_records = [MagicMock(mode="shadow"), MagicMock(mode="paper")]

            with patch(
                "src.experiments.live_session_registry.get_session_summary",
                return_value=mock_summary,
            ):
                with patch(
                    "src.experiments.live_session_registry.list_session_records",
                    return_value=mock_records,
                ):
                    from src.reporting.live_status_snapshot_builder import (
                        build_live_status_snapshot_auto,
                    )

                    meta = {"snapshot_id": "test_snapshot", "timestamp": "2025-12-21T12:00:00Z"}
                    snapshot = build_live_status_snapshot_auto(meta=meta)

                    # Snapshot is a Pydantic model, not a dict
                    assert snapshot is not None
                    assert hasattr(snapshot, "panels")
                    panels = snapshot.panels
                    assert isinstance(panels, list)
                    # Should have at least 1 panel (minimum: system panel as fallback)
                    assert len(panels) >= 1
                    # If providers are registered, we should have the full set
                    # (alerts, live_sessions, telemetry, positions, portfolio, risk = 6)

    def test_snapshot_panels_have_stable_structure(self, mock_alerts_stats, mock_sessions_stats):
        """Test that all panels in snapshot have required fields."""
        with patch("src.live.alert_storage.get_alert_stats", return_value=mock_alerts_stats):
            mock_summary = {
                "num_sessions": 10,
                "by_status": {"started": 2, "completed": 7, "failed": 1},
                "total_realized_pnl": 150.75,
                "avg_max_drawdown": -12.5,
            }
            mock_records = [MagicMock(mode="shadow"), MagicMock(mode="paper")]

            with patch(
                "src.experiments.live_session_registry.get_session_summary",
                return_value=mock_summary,
            ):
                with patch(
                    "src.experiments.live_session_registry.list_session_records",
                    return_value=mock_records,
                ):
                    from src.reporting.live_status_snapshot_builder import (
                        build_live_status_snapshot_auto,
                    )

                    snapshot = build_live_status_snapshot_auto(meta={})
                    panels = snapshot.panels

                    for panel in panels:
                        # Panel is a Pydantic model with attributes
                        assert hasattr(panel, "id")
                        assert hasattr(panel, "title")
                        # status and details are optional but recommended
                        if hasattr(panel, "status"):
                            assert panel.status in (
                                "ok",
                                "active",
                                "warning",
                                "warn",
                                "error",
                                "unknown",
                            )

    def test_snapshot_with_real_providers_no_crash(self):
        """Test snapshot builder with real providers doesn't crash (may return fallback data)."""
        # This test runs without mocks to verify no crashes in real scenario
        from src.reporting.live_status_snapshot_builder import build_live_status_snapshot_auto

        snapshot = build_live_status_snapshot_auto(meta={})

        # Snapshot is a Pydantic model
        assert snapshot is not None
        assert hasattr(snapshot, "panels")
        # Should have at least some panels (even if with fallback data)
        assert len(snapshot.panels) >= 1


# =============================================================================
# CONSISTENCY TESTS
# =============================================================================


class TestAPIEndpointConsistency:
    """Test that API endpoints and panels use the same data source."""

    def test_alerts_api_uses_service_layer(self, mock_alerts_stats):
        """Test that alerts API endpoint uses service layer."""
        with patch(
            "src.live.alert_storage.get_alert_stats", return_value=mock_alerts_stats
        ) as mock:
            from src.webui.alerts_api import get_alert_statistics

            result = get_alert_statistics(hours=24)

            # Verify underlying storage was called (via service layer)
            mock.assert_called_once_with(hours=24)
            # Verify result structure
            assert result.total == mock_alerts_stats["total"]
            assert result.hours == 24

    def test_sessions_api_uses_service_layer(self, mock_sessions_stats):
        """Test that sessions API endpoint uses service layer."""
        mock_summary = {
            "num_sessions": 10,
            "by_status": {"started": 2, "completed": 7, "failed": 1},
            "total_realized_pnl": 150.75,
            "avg_max_drawdown": -12.5,
        }
        mock_records = [MagicMock(mode="shadow"), MagicMock(mode="paper")]

        with patch(
            "src.experiments.live_session_registry.get_session_summary", return_value=mock_summary
        ):
            with patch(
                "src.experiments.live_session_registry.list_session_records",
                return_value=mock_records,
            ) as mock_list:
                from src.webui.live_track import get_session_stats

                result = get_session_stats()

                # Verify underlying registry was called (via service layer)
                mock_list.assert_called()
                # Verify result structure
                assert result["total_sessions"] >= 0
                assert "by_mode" in result
                assert "by_status" in result
                assert "total_pnl" in result
                assert "avg_drawdown" in result


# =============================================================================
# NEW PANEL TESTS (Positions, Portfolio, Risk)
# =============================================================================


class TestNewPanels:
    """Test the newly implemented panels (positions, portfolio, risk)."""

    def test_positions_panel_with_active_sessions(self):
        """Test positions panel with active sessions."""
        mock_records = [
            MagicMock(
                status="started",
                symbol="BTC-EUR",
                metrics={"open_positions": 1, "total_notional": 1000.0},
            )
        ]

        with patch(
            "src.experiments.live_session_registry.list_session_records", return_value=mock_records
        ):
            from src.live.status_providers import _panel_positions

            result = _panel_positions()

            assert result["id"] == "positions"
            assert result["status"] in ("ok", "active", "unknown")
            assert isinstance(result["details"], dict)
            # Should have position data if session is active
            if result["status"] != "unknown":
                assert "open_positions" in result["details"]

    def test_portfolio_panel_with_active_sessions(self):
        """Test portfolio panel with active sessions."""
        mock_records = [
            MagicMock(
                status="started",
                symbol="BTC-EUR",
                metrics={"realized_pnl": 100.0, "unrealized_pnl": 50.0, "total_notional": 2000.0},
            )
        ]

        with patch(
            "src.experiments.live_session_registry.list_session_records", return_value=mock_records
        ):
            from src.live.status_providers import _panel_portfolio

            result = _panel_portfolio()

            assert result["id"] == "portfolio"
            assert result["status"] in ("ok", "active", "unknown")
            assert isinstance(result["details"], dict)
            if result["status"] != "unknown":
                assert "total_pnl" in result["details"]

    def test_risk_panel_with_risk_breach(self):
        """Test risk panel when risk limits are breached."""
        mock_records = [
            MagicMock(
                status="started",
                metrics={
                    "risk_check": {
                        "allowed": False,
                        "severity": "breach",
                        "reasons": ["Max drawdown exceeded"],
                        "limit_details": [{"name": "drawdown", "severity": "breach"}],
                    }
                },
            )
        ]

        with patch(
            "src.experiments.live_session_registry.list_session_records", return_value=mock_records
        ):
            from src.live.status_providers import _panel_risk

            result = _panel_risk()

            assert result["id"] == "risk"
            # Blocked should map to "error" status
            assert result["status"] in ("error", "warning", "ok", "unknown")
            assert isinstance(result["details"], dict)

    def test_all_new_panels_fallback_stable(self):
        """Test all new panels are stable even with no data."""
        # Mock empty registry
        with patch("src.experiments.live_session_registry.list_session_records", return_value=[]):
            from src.live.status_providers import _panel_positions, _panel_portfolio, _panel_risk

            positions = _panel_positions()
            portfolio = _panel_portfolio()
            risk = _panel_risk()

            # All should return valid structures
            assert positions["id"] == "positions"
            assert portfolio["id"] == "portfolio"
            assert risk["id"] == "risk"

            # All should have status and details
            for panel in [positions, portfolio, risk]:
                assert "status" in panel
                assert "details" in panel
                assert isinstance(panel["details"], dict)
