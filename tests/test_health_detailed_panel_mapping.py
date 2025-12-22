# tests/test_health_detailed_panel_mapping.py
"""
Tests für /health/detailed Panel-Status-Mapping
===============================================

Testet:
- Panel-Status-Aggregation
- Overall-Status-Berechnung (ok/degraded/blocked)
- HTTP-Status-Code-Mapping (200 vs 503)

Note: Diese Tests erfordern fastapi im Test-Environment.
"""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# Mark all tests in this module as requiring fastapi
pytestmark = pytest.mark.skipif(
    not pytest.importorskip("fastapi", reason="fastapi not available"),
    reason="fastapi not installed - skipping health endpoint tests",
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_all_panels_ok():
    """Mock all panels with OK status."""
    return {
        "alerts": {"id": "alerts", "status": "ok", "details": {"total": 5}},
        "live_sessions": {"id": "live_sessions", "status": "ok", "details": {"total_sessions": 2}},
        "telemetry": {"id": "telemetry", "status": "ok", "details": {"status": "ok"}},
        "positions": {"id": "positions", "status": "ok", "details": {"open_positions": 1}},
        "portfolio": {"id": "portfolio", "status": "ok", "details": {"total_pnl": 100.0}},
        "risk": {"id": "risk", "status": "ok", "details": {"status": "ok"}},
    }


@pytest.fixture
def mock_panels_with_unknown():
    """Mock panels with one unknown panel (degraded)."""
    return {
        "alerts": {"id": "alerts", "status": "ok", "details": {"total": 5}},
        "live_sessions": {
            "id": "live_sessions",
            "status": "unknown",
            "details": {"message": "No data"},
        },
        "telemetry": {"id": "telemetry", "status": "ok", "details": {"status": "ok"}},
        "positions": {"id": "positions", "status": "ok", "details": {"open_positions": 0}},
        "portfolio": {"id": "portfolio", "status": "ok", "details": {"total_pnl": 0.0}},
        "risk": {"id": "risk", "status": "ok", "details": {"status": "ok"}},
    }


@pytest.fixture
def mock_panels_with_blocked():
    """Mock panels with blocked risk (blocked overall)."""
    return {
        "alerts": {"id": "alerts", "status": "warning", "details": {"total": 100}},
        "live_sessions": {
            "id": "live_sessions",
            "status": "active",
            "details": {"active_sessions": 1},
        },
        "telemetry": {"id": "telemetry", "status": "ok", "details": {"status": "ok"}},
        "positions": {"id": "positions", "status": "active", "details": {"open_positions": 2}},
        "portfolio": {"id": "portfolio", "status": "active", "details": {"total_pnl": -500.0}},
        "risk": {
            "id": "risk",
            "status": "error",
            "details": {"status": "blocked", "violations": ["Drawdown exceeded"]},
        },
    }


# =============================================================================
# PANEL STATUS AGGREGATION TESTS
# =============================================================================


class TestPanelStatusAggregation:
    """Test _get_panel_status() function."""

    def test_all_panels_ok(self, mock_all_panels_ok):
        """Test panel status when all panels are OK."""

        def mock_provider_factory(panel_data):
            return lambda: panel_data

        mock_providers = {
            panel_id: mock_provider_factory(data) for panel_id, data in mock_all_panels_ok.items()
        }

        with patch(
            "src.live.status_providers.get_live_panel_providers", return_value=mock_providers
        ):
            from src.webui.health_endpoint import _get_panel_status

            result = _get_panel_status()

            assert result["overall_status"] == "ok"
            assert len(result["panels"]) == 6
            for panel_id, panel_info in result["panels"].items():
                assert panel_info["status"] in ("ok", "active")

    def test_panels_with_unknown(self, mock_panels_with_unknown):
        """Test panel status when one panel is unknown (degraded)."""

        def mock_provider_factory(panel_data):
            return lambda: panel_data

        mock_providers = {
            panel_id: mock_provider_factory(data)
            for panel_id, data in mock_panels_with_unknown.items()
        }

        with patch(
            "src.live.status_providers.get_live_panel_providers", return_value=mock_providers
        ):
            from src.webui.health_endpoint import _get_panel_status

            result = _get_panel_status()

            assert result["overall_status"] == "degraded"
            assert result["panels"]["live_sessions"]["status"] == "unknown"

    def test_panels_with_blocked(self, mock_panels_with_blocked):
        """Test panel status when risk is blocked."""

        def mock_provider_factory(panel_data):
            return lambda: panel_data

        mock_providers = {
            panel_id: mock_provider_factory(data)
            for panel_id, data in mock_panels_with_blocked.items()
        }

        with patch(
            "src.live.status_providers.get_live_panel_providers", return_value=mock_providers
        ):
            from src.webui.health_endpoint import _get_panel_status

            result = _get_panel_status()

            assert result["overall_status"] == "blocked"
            assert result["panels"]["risk"]["status"] == "error"

    def test_panel_status_with_provider_error(self):
        """Test panel status when one provider raises an exception."""

        def failing_provider():
            raise RuntimeError("Mock provider error")

        mock_providers = {
            "alerts": lambda: {"id": "alerts", "status": "ok", "details": {}},
            "failing_panel": failing_provider,
        }

        with patch(
            "src.live.status_providers.get_live_panel_providers", return_value=mock_providers
        ):
            from src.webui.health_endpoint import _get_panel_status

            result = _get_panel_status()

            # Should be degraded due to failing panel
            assert result["overall_status"] == "degraded"
            assert "failing_panel" in result["panels"]
            assert result["panels"]["failing_panel"]["status"] == "unknown"


# =============================================================================
# HEALTH ENDPOINT HTTP STATUS MAPPING TESTS
# =============================================================================


class TestHealthEndpointStatusCodes:
    """Test HTTP status code mapping for /health/detailed."""

    def test_health_detailed_ok_returns_200(self, mock_all_panels_ok):
        """Test that overall_status=ok returns HTTP 200."""

        def mock_provider_factory(panel_data):
            return lambda: panel_data

        mock_providers = {
            panel_id: mock_provider_factory(data) for panel_id, data in mock_all_panels_ok.items()
        }

        with patch(
            "src.live.status_providers.get_live_panel_providers", return_value=mock_providers
        ):
            with patch("core.resilience.health_check.get_status", return_value={"healthy": True}):
                with patch("core.metrics.metrics.get_summary", return_value={}):
                    from src.webui.health_endpoint import health_detailed
                    import asyncio

                    response = asyncio.run(health_detailed())

                    assert response.status_code == 200
                    # Check body contains overall_status
                    import json

                    body = json.loads(response.body)
                    assert body["overall_status"] == "ok"

    def test_health_detailed_degraded_returns_200(self, mock_panels_with_unknown):
        """Test that overall_status=degraded returns HTTP 200 (not 503)."""

        def mock_provider_factory(panel_data):
            return lambda: panel_data

        mock_providers = {
            panel_id: mock_provider_factory(data)
            for panel_id, data in mock_panels_with_unknown.items()
        }

        with patch(
            "src.live.status_providers.get_live_panel_providers", return_value=mock_providers
        ):
            with patch("core.resilience.health_check.get_status", return_value={"healthy": True}):
                with patch("core.metrics.metrics.get_summary", return_value={}):
                    from src.webui.health_endpoint import health_detailed
                    import asyncio

                    response = asyncio.run(health_detailed())

                    # Degraded should still return 200
                    assert response.status_code == 200
                    import json

                    body = json.loads(response.body)
                    assert body["overall_status"] == "degraded"

    def test_health_detailed_blocked_returns_503(self, mock_panels_with_blocked):
        """Test that overall_status=blocked returns HTTP 503."""

        def mock_provider_factory(panel_data):
            return lambda: panel_data

        mock_providers = {
            panel_id: mock_provider_factory(data)
            for panel_id, data in mock_panels_with_blocked.items()
        }

        with patch(
            "src.live.status_providers.get_live_panel_providers", return_value=mock_providers
        ):
            with patch("core.resilience.health_check.get_status", return_value={"healthy": True}):
                with patch("core.metrics.metrics.get_summary", return_value={}):
                    from src.webui.health_endpoint import health_detailed
                    import asyncio

                    response = asyncio.run(health_detailed())

                    # Blocked should return 503
                    assert response.status_code == 503
                    import json

                    body = json.loads(response.body)
                    assert body["overall_status"] == "blocked"
                    assert body["healthy"] is False


# =============================================================================
# PANEL STATUS MESSAGE EXTRACTION TESTS
# =============================================================================


class TestPanelStatusMessages:
    """Test message extraction from panel details."""

    def test_message_from_total(self):
        """Test message extraction when details have 'total' field."""

        def mock_provider():
            return {
                "id": "alerts",
                "status": "ok",
                "details": {"total": 42, "by_severity": {"CRITICAL": 5}},
            }

        with patch(
            "src.live.status_providers.get_live_panel_providers",
            return_value={"alerts": mock_provider},
        ):
            from src.webui.health_endpoint import _get_panel_status

            result = _get_panel_status()

            assert result["panels"]["alerts"]["message"] == "42 items"

    def test_message_from_sessions(self):
        """Test message extraction for sessions panel."""

        def mock_provider():
            return {
                "id": "live_sessions",
                "status": "active",
                "details": {"active_sessions": 3, "total_sessions": 10},
            }

        with patch(
            "src.live.status_providers.get_live_panel_providers",
            return_value={"live_sessions": mock_provider},
        ):
            from src.webui.health_endpoint import _get_panel_status

            result = _get_panel_status()

            assert result["panels"]["live_sessions"]["message"] == "3 active / 10 total"

    def test_message_from_fallback(self):
        """Test message extraction from fallback."""

        def mock_provider():
            return {
                "id": "risk",
                "status": "unknown",
                "details": {"_fallback": True, "message": "Risk data not available"},
            }

        with patch(
            "src.live.status_providers.get_live_panel_providers",
            return_value={"risk": mock_provider},
        ):
            from src.webui.health_endpoint import _get_panel_status

            result = _get_panel_status()

            assert result["panels"]["risk"]["message"] == "Risk data not available"
