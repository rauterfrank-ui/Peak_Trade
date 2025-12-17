# tests/test_risk_alert_helpers.py
"""
Tests für Risk-Alert-Helpers und Operator-Guidance
===================================================

Testet:
- OperatorGuidance Datenstruktur
- get_operator_guidance() für alle Status
- format_risk_alert_message() Formatierung
- format_slack_risk_alert() Slack-Format
- trigger_risk_alert() Alert-Trigger-Logik
- RiskAlertFormatter Terminal-/Compact-Formatierung
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.live.risk_alert_helpers import (
    RiskAlertFormatter,
    format_limit_detail,
    format_risk_alert_message,
    format_slack_risk_alert,
    get_guidance_for_result,
    get_operator_guidance,
    trigger_risk_alert,
)
from src.live.risk_limits import (
    LimitCheckDetail,
    LiveRiskCheckResult,
    RiskCheckSeverity,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def result_ok() -> LiveRiskCheckResult:
    """Result mit OK-Status."""
    return LiveRiskCheckResult(
        allowed=True,
        reasons=[],
        metrics={"total_notional": 1000.0},
        severity=RiskCheckSeverity.OK,
        limit_details=[
            LimitCheckDetail(
                limit_name="max_order_notional",
                current_value=500.0,
                limit_value=2000.0,
                severity=RiskCheckSeverity.OK,
            ),
        ],
    )


@pytest.fixture
def result_warning() -> LiveRiskCheckResult:
    """Result mit WARNING-Status."""
    return LiveRiskCheckResult(
        allowed=True,
        reasons=[],
        metrics={"total_notional": 8500.0},
        severity=RiskCheckSeverity.WARNING,
        limit_details=[
            LimitCheckDetail(
                limit_name="max_total_exposure",
                current_value=8500.0,
                limit_value=10000.0,
                warning_threshold=8000.0,
                severity=RiskCheckSeverity.WARNING,
                message="max_total_exposure_warning(at 85.0% of limit)",
            ),
            LimitCheckDetail(
                limit_name="max_order_notional",
                current_value=1000.0,
                limit_value=2000.0,
                severity=RiskCheckSeverity.OK,
            ),
        ],
    )


@pytest.fixture
def result_breach() -> LiveRiskCheckResult:
    """Result mit BREACH-Status."""
    return LiveRiskCheckResult(
        allowed=False,
        reasons=["max_daily_loss_abs_exceeded(limit=500.0, value=-600.0)"],
        metrics={"daily_realized_pnl_net": -600.0},
        severity=RiskCheckSeverity.BREACH,
        limit_details=[
            LimitCheckDetail(
                limit_name="max_daily_loss_abs",
                current_value=-600.0,
                limit_value=500.0,
                severity=RiskCheckSeverity.BREACH,
                message="max_daily_loss_abs_reached(limit=500.00, value=-600.00)",
            ),
        ],
    )


# =============================================================================
# TESTS: OPERATOR GUIDANCE
# =============================================================================


class TestOperatorGuidance:
    """Tests für OperatorGuidance."""

    def test_guidance_green(self):
        """Green Status gibt korrekte Guidance."""
        guidance = get_operator_guidance("green")

        assert guidance.risk_status == "green"
        assert guidance.severity_label == "OK"
        assert guidance.icon == "✅"
        assert "normal" in guidance.summary.lower() or "ok" in guidance.summary.lower()
        assert len(guidance.actions) > 0
        assert guidance.escalation is None

    def test_guidance_yellow(self):
        """Yellow Status gibt Warning-Guidance."""
        guidance = get_operator_guidance("yellow")

        assert guidance.risk_status == "yellow"
        assert guidance.severity_label == "WARNING"
        assert guidance.icon == "⚠️"
        assert len(guidance.actions) > 0
        assert guidance.escalation is not None
        assert "erhöht" in guidance.monitoring_interval.lower()

    def test_guidance_red(self):
        """Red Status gibt Breach-Guidance."""
        guidance = get_operator_guidance("red")

        assert guidance.risk_status == "red"
        assert guidance.severity_label == "BREACH"
        assert guidance.icon == "⛔"
        assert len(guidance.actions) > 5  # Viele Aktionen bei BREACH
        assert guidance.escalation is not None
        assert "kontinuierlich" in guidance.monitoring_interval.lower()

    def test_guidance_invalid_returns_green(self):
        """Unbekannter Status gibt Green zurück."""
        guidance = get_operator_guidance("invalid")
        assert guidance.risk_status == "green"

    def test_get_guidance_for_result(self, result_warning: LiveRiskCheckResult):
        """get_guidance_for_result nutzt risk_status."""
        guidance = get_guidance_for_result(result_warning)
        assert guidance.risk_status == "yellow"


# =============================================================================
# TESTS: FORMAT FUNCTIONS
# =============================================================================


class TestFormatFunctions:
    """Tests für Formatierungs-Funktionen."""

    def test_format_limit_detail_ok(self):
        """Formatiert OK-Detail korrekt."""
        detail = LimitCheckDetail(
            limit_name="max_order_notional",
            current_value=500.0,
            limit_value=2000.0,
            severity=RiskCheckSeverity.OK,
        )

        formatted = format_limit_detail(detail)

        assert "max_order_notional" in formatted
        assert "500.00" in formatted
        assert "2000.00" in formatted
        assert "25.0%" in formatted
        assert "✓" in formatted

    def test_format_limit_detail_warning(self):
        """Formatiert WARNING-Detail korrekt."""
        detail = LimitCheckDetail(
            limit_name="max_total_exposure",
            current_value=8500.0,
            limit_value=10000.0,
            severity=RiskCheckSeverity.WARNING,
        )

        formatted = format_limit_detail(detail)

        assert "⚠" in formatted
        assert "85.0%" in formatted

    def test_format_limit_detail_breach(self):
        """Formatiert BREACH-Detail korrekt."""
        detail = LimitCheckDetail(
            limit_name="max_daily_loss_abs",
            current_value=600.0,
            limit_value=500.0,
            severity=RiskCheckSeverity.BREACH,
        )

        formatted = format_limit_detail(detail)

        assert "✗" in formatted
        assert "120.0%" in formatted

    def test_format_risk_alert_message_ok(self, result_ok: LiveRiskCheckResult):
        """Formatiert OK-Result."""
        msg = format_risk_alert_message(result_ok)

        assert "OK" in msg
        assert "✅" in msg

    def test_format_risk_alert_message_warning(self, result_warning: LiveRiskCheckResult):
        """Formatiert WARNING-Result mit Details."""
        msg = format_risk_alert_message(result_warning, include_details=True)

        assert "WARNING" in msg
        assert "⚠️" in msg
        assert "max_total_exposure" in msg

    def test_format_risk_alert_message_breach(self, result_breach: LiveRiskCheckResult):
        """Formatiert BREACH-Result mit Reasons."""
        msg = format_risk_alert_message(result_breach, include_details=True)

        assert "BREACH" in msg
        assert "⛔" in msg
        assert "blockiert" in msg.lower() or "verletzt" in msg.lower()
        assert "Gründe" in msg

    def test_format_slack_risk_alert(self, result_warning: LiveRiskCheckResult):
        """Formatiert Slack-Alert mit Markdown."""
        msg = format_slack_risk_alert(
            result_warning,
            source="live_risk.orders",
            session_id="test_session_123",
        )

        assert "*RISK WARNING*" in msg
        assert "test_session_123" in msg
        assert "live_risk.orders" in msg
        assert "Empfohlene Aktionen" in msg


# =============================================================================
# TESTS: TRIGGER RISK ALERT
# =============================================================================


class TestTriggerRiskAlert:
    """Tests für trigger_risk_alert."""

    def test_trigger_alert_none_sink(self, result_warning: LiveRiskCheckResult):
        """None-Sink triggert keinen Alert."""
        triggered = trigger_risk_alert(result_warning, None)
        assert triggered is False

    def test_trigger_alert_ok_status(self, result_ok: LiveRiskCheckResult):
        """OK-Status triggert keinen Alert."""
        mock_sink = MagicMock()
        triggered = trigger_risk_alert(result_ok, mock_sink)

        assert triggered is False
        mock_sink.send.assert_not_called()

    def test_trigger_alert_warning(self, result_warning: LiveRiskCheckResult):
        """WARNING triggert Alert mit WARNING-Level."""
        mock_sink = MagicMock()
        triggered = trigger_risk_alert(
            result_warning,
            mock_sink,
            source="test_source",
            session_id="sess_123",
        )

        assert triggered is True
        mock_sink.send.assert_called_once()

        # Prüfe Alert-Details
        alert = mock_sink.send.call_args[0][0]
        assert alert.source == "test_source"
        assert alert.code == "RISK_LIMIT_WARNING"
        assert "sess_123" in alert.context.get("session_id", "")

    def test_trigger_alert_breach(self, result_breach: LiveRiskCheckResult):
        """BREACH triggert Alert mit CRITICAL-Level."""
        mock_sink = MagicMock()
        triggered = trigger_risk_alert(result_breach, mock_sink)

        assert triggered is True
        mock_sink.send.assert_called_once()

        alert = mock_sink.send.call_args[0][0]
        assert alert.code == "RISK_LIMIT_BREACH"

    def test_trigger_alert_includes_limit_summary(self, result_warning: LiveRiskCheckResult):
        """Alert enthält Limit-Summary im Context."""
        mock_sink = MagicMock()
        trigger_risk_alert(result_warning, mock_sink)

        alert = mock_sink.send.call_args[0][0]
        assert "limit_summary" in alert.context

        # Nur non-OK Limits im Summary
        summary = alert.context["limit_summary"]
        assert isinstance(summary, list)
        assert all(item["severity"] != "ok" for item in summary)


# =============================================================================
# TESTS: RISK ALERT FORMATTER
# =============================================================================


class TestRiskAlertFormatter:
    """Tests für RiskAlertFormatter."""

    def test_format_terminal_green(self, result_ok: LiveRiskCheckResult):
        """Terminal-Format für OK-Status."""
        formatter = RiskAlertFormatter(use_colors=False)
        output = formatter.format_terminal(result_ok)

        assert "RISK OK" in output
        assert "Status: GREEN" in output
        assert "Allowed: True" in output

    def test_format_terminal_warning_with_colors(self, result_warning: LiveRiskCheckResult):
        """Terminal-Format mit Farben für WARNING."""
        formatter = RiskAlertFormatter(use_colors=True)
        output = formatter.format_terminal(result_warning)

        # ANSI-Codes sollten vorhanden sein
        assert "\033[" in output
        assert "WARNING" in output

    def test_format_terminal_breach(self, result_breach: LiveRiskCheckResult):
        """Terminal-Format für BREACH."""
        formatter = RiskAlertFormatter(use_colors=False)
        output = formatter.format_terminal(result_breach)

        assert "BREACH" in output
        assert "Allowed: False" in output
        assert "Empfohlene Aktionen" in output

    def test_format_compact_ok(self, result_ok: LiveRiskCheckResult):
        """Compact-Format für OK."""
        formatter = RiskAlertFormatter()
        output = formatter.format_compact(result_ok)

        assert "OK" in output
        assert "eingehalten" in output or "Limits" in output

    def test_format_compact_warning(self, result_warning: LiveRiskCheckResult):
        """Compact-Format für WARNING."""
        formatter = RiskAlertFormatter()
        output = formatter.format_compact(result_warning)

        assert "WARNING" in output
        assert "1 Limit(s)" in output

    def test_format_compact_breach(self, result_breach: LiveRiskCheckResult):
        """Compact-Format für BREACH."""
        formatter = RiskAlertFormatter()
        output = formatter.format_compact(result_breach)

        assert "BREACH" in output
        assert "allowed=False" in output


# =============================================================================
# TESTS: EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Tests für Randfälle."""

    def test_empty_limit_details(self):
        """Result ohne Limit-Details."""
        result = LiveRiskCheckResult(
            allowed=True,
            reasons=[],
            metrics={},
            severity=RiskCheckSeverity.OK,
            limit_details=[],
        )

        msg = format_risk_alert_message(result)
        assert "OK" in msg

    def test_multiple_breach_limits(self):
        """Result mit mehreren BREACH-Limits."""
        result = LiveRiskCheckResult(
            allowed=False,
            reasons=["limit1_exceeded", "limit2_exceeded"],
            metrics={},
            severity=RiskCheckSeverity.BREACH,
            limit_details=[
                LimitCheckDetail(
                    limit_name="limit1",
                    current_value=150.0,
                    limit_value=100.0,
                    severity=RiskCheckSeverity.BREACH,
                ),
                LimitCheckDetail(
                    limit_name="limit2",
                    current_value=200.0,
                    limit_value=100.0,
                    severity=RiskCheckSeverity.BREACH,
                ),
            ],
        )

        msg = format_risk_alert_message(result, max_details=5)

        assert "limit1" in msg
        assert "limit2" in msg

    def test_trigger_alert_with_extra_context(self, result_warning: LiveRiskCheckResult):
        """Extra-Context wird zu Alert hinzugefügt."""
        mock_sink = MagicMock()
        trigger_risk_alert(
            result_warning,
            mock_sink,
            extra_context={"custom_field": "custom_value"},
        )

        alert = mock_sink.send.call_args[0][0]
        assert alert.context.get("custom_field") == "custom_value"
