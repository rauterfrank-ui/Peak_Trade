# src/live/risk_alert_helpers.py
"""
Peak_Trade: Risk-Severity Alert-Helpers
========================================

Hilfsfunktionen für Severity-basiertes Alerting und Operator-Guidance.

Dieses Modul bietet:
1. Formatierte Alert-Messages für WARNING und BREACH
2. Integration mit dem bestehenden AlertSink-System
3. CLI-Ausgabe-Formatter für Operator-Dashboards
4. Runbook-Handlungsempfehlungen basierend auf risk_status

Usage:
    from src.live.risk_alert_helpers import (
        format_risk_alert_message,
        trigger_risk_alert,
        get_operator_guidance,
        RiskAlertFormatter,
    )

    # Bei einem Risk-Check-Result:
    result = limits.check_orders(orders)
    if result.severity != RiskCheckSeverity.OK:
        message = format_risk_alert_message(result)
        trigger_risk_alert(result, alert_sink)

    # Operator-Guidance abrufen:
    guidance = get_operator_guidance(result.risk_status)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence

if TYPE_CHECKING:
    from src.live.alerts import AlertEvent, AlertLevel, AlertSink
    from src.live.risk_limits import (
        LimitCheckDetail,
        LiveRiskCheckResult,
        RiskCheckSeverity,
        RiskStatus,
    )

logger = logging.getLogger(__name__)


# =============================================================================
# OPERATOR GUIDANCE - Handlungsempfehlungen pro Severity
# =============================================================================


@dataclass
class OperatorGuidance:
    """
    Handlungsempfehlung für Operator basierend auf risk_status.

    Attributes:
        risk_status: Der aktuelle Risk-Status (green/yellow/red)
        severity_label: Human-readable Label für die Severity
        icon: Emoji/Icon für das Dashboard
        summary: Kurze Zusammenfassung des Status
        actions: Liste empfohlener Aktionen
        escalation: Eskalations-Hinweis (falls notwendig)
        monitoring_interval: Empfohlenes Monitoring-Intervall
    """

    risk_status: str
    severity_label: str
    icon: str
    summary: str
    actions: List[str]
    escalation: Optional[str] = None
    monitoring_interval: Optional[str] = None


# Vordefinierte Guidance pro Status
_GUIDANCE_GREEN = OperatorGuidance(
    risk_status="green",
    severity_label="OK",
    icon="✅",
    summary="System läuft normal. Alle Limits komfortabel eingehalten.",
    actions=[
        "Routinemäßiges Monitoring fortsetzen",
        "Keine sofortigen Maßnahmen erforderlich",
        "Nächsten regulären Check-In abwarten",
    ],
    escalation=None,
    monitoring_interval="Standard (5-15 min)",
)

_GUIDANCE_YELLOW = OperatorGuidance(
    risk_status="yellow",
    severity_label="WARNING",
    icon="⚠️",
    summary="Mindestens ein Limit im Warnbereich. Erhöhte Aufmerksamkeit erforderlich.",
    actions=[
        "Positionen und offene Orders überprüfen",
        "Exposure-Verteilung (Konzentration) analysieren",
        "Trading-Intensität reduzieren oder auf defensive Strategien umschalten",
        "Daily-PnL im Auge behalten",
        "Ggf. Position-Sizing anpassen",
    ],
    escalation="Bei Annäherung an BREACH: Team informieren, Stop-Loss prüfen",
    monitoring_interval="Erhöht (1-5 min)",
)

_GUIDANCE_RED = OperatorGuidance(
    risk_status="red",
    severity_label="BREACH",
    icon="⛔",
    summary="Mindestens ein Limit verletzt. Neue Orders werden blockiert.",
    actions=[
        "SOFORT: Keine neuen Positionen eröffnen",
        "Offene Orders prüfen und ggf. stornieren",
        "Bestehende Positionen evaluieren - kontrollierter Abbau erwägen",
        "Ursache der Limit-Verletzung identifizieren (Gap? Akkumulation? Over-Exposure?)",
        "Incident-Log anlegen (Zeitpunkt, betroffene Limits, Kontext)",
        "Screenshots/Charts sichern für Postmortem",
        "Team/Eskalationskontakt informieren",
    ],
    escalation="Sofortige Eskalation erforderlich. Trading gestoppt bis Freigabe.",
    monitoring_interval="Kontinuierlich (Live-Watch)",
)

_GUIDANCE_MAP: Dict[str, OperatorGuidance] = {
    "green": _GUIDANCE_GREEN,
    "yellow": _GUIDANCE_YELLOW,
    "red": _GUIDANCE_RED,
}


def get_operator_guidance(risk_status: str) -> OperatorGuidance:
    """
    Gibt Operator-Handlungsempfehlungen für einen risk_status zurück.

    Args:
        risk_status: "green", "yellow" oder "red"

    Returns:
        OperatorGuidance mit empfohlenen Aktionen

    Example:
        >>> guidance = get_operator_guidance("yellow")
        >>> print(guidance.icon, guidance.summary)
        ⚠️ Mindestens ein Limit im Warnbereich. Erhöhte Aufmerksamkeit erforderlich.
        >>> for action in guidance.actions:
        ...     print(f"  - {action}")
    """
    return _GUIDANCE_MAP.get(risk_status, _GUIDANCE_GREEN)


def get_guidance_for_result(result: "LiveRiskCheckResult") -> OperatorGuidance:
    """
    Gibt Operator-Guidance für ein LiveRiskCheckResult zurück.

    Args:
        result: LiveRiskCheckResult mit risk_status

    Returns:
        OperatorGuidance
    """
    return get_operator_guidance(result.risk_status)


# =============================================================================
# ALERT MESSAGE FORMATTING
# =============================================================================


def format_limit_detail(detail: "LimitCheckDetail") -> str:
    """
    Formatiert ein LimitCheckDetail als einzeiligen String.

    Args:
        detail: LimitCheckDetail

    Returns:
        Formatierter String, z.B. "max_daily_loss_abs: 450.00 / 500.00 (90.0%)"
    """
    ratio_pct = detail.ratio * 100
    severity_icon = {
        "ok": "✓",
        "warning": "⚠",
        "breach": "✗",
    }.get(detail.severity.value, "?")

    return (
        f"{severity_icon} {detail.limit_name}: "
        f"{detail.current_value:.2f} / {detail.limit_value:.2f} ({ratio_pct:.1f}%)"
    )


def format_risk_alert_message(
    result: "LiveRiskCheckResult",
    *,
    source: str = "live_risk",
    include_details: bool = True,
    max_details: int = 5,
) -> str:
    """
    Formatiert ein LiveRiskCheckResult als Alert-Message.

    Args:
        result: LiveRiskCheckResult
        source: Alert-Quelle (z.B. "live_risk.orders", "live_risk.portfolio")
        include_details: Ob Limit-Details inkludiert werden sollen
        max_details: Maximale Anzahl Details (für lange Listen)

    Returns:
        Formatierte Alert-Message

    Example:
        >>> result = limits.check_orders(orders)
        >>> msg = format_risk_alert_message(result)
        >>> print(msg)
        ⚠️ Live-Risk WARNING – 2 Limits im Warnbereich
        ⚠ max_order_notional: 1700.00 / 2000.00 (85.0%)
        ⚠ max_total_exposure: 8500.00 / 10000.00 (85.0%)
    """
    guidance = get_operator_guidance(result.risk_status)
    icon = guidance.icon
    label = guidance.severity_label

    # Header
    lines = []

    if result.severity.value == "breach":
        lines.append(f"{icon} Live-Risk {label} – Limit(s) verletzt, Orders blockiert")
    elif result.severity.value == "warning":
        # Zähle WARNING-Details
        warn_count = sum(
            1 for d in result.limit_details if d.severity.value == "warning"
        )
        lines.append(f"{icon} Live-Risk {label} – {warn_count} Limit(s) im Warnbereich")
    else:
        lines.append(f"{icon} Live-Risk {label} – Alle Limits OK")

    # Details (nur nicht-OK)
    if include_details:
        non_ok_details = [
            d for d in result.limit_details if d.severity.value != "ok"
        ]

        if non_ok_details:
            for i, detail in enumerate(non_ok_details[:max_details]):
                lines.append(format_limit_detail(detail))

            if len(non_ok_details) > max_details:
                lines.append(f"... und {len(non_ok_details) - max_details} weitere")

    # Reasons bei BREACH
    if result.reasons and result.severity.value == "breach":
        lines.append("")
        lines.append("Gründe:")
        for reason in result.reasons[:3]:
            lines.append(f"  • {reason}")

    return "\n".join(lines)


def format_slack_risk_alert(
    result: "LiveRiskCheckResult",
    *,
    source: str = "live_risk",
    session_id: Optional[str] = None,
) -> str:
    """
    Formatiert ein LiveRiskCheckResult als Slack-Message.

    Nutzt Slack-Formatierung (Markdown, Emojis).

    Args:
        result: LiveRiskCheckResult
        source: Alert-Quelle
        session_id: Optional Session-ID für Kontext

    Returns:
        Slack-formatierte Message
    """
    guidance = get_operator_guidance(result.risk_status)

    # Header mit Severity-abhängigem Emoji
    if result.severity.value == "breach":
        header = f"🚨 *RISK BREACH* – Trading blockiert"
    elif result.severity.value == "warning":
        header = f"⚠️ *RISK WARNING* – Monitoring erhöhen"
    else:
        header = f"✅ Risk Status OK"

    lines = [header]

    # Kontext
    if session_id:
        lines.append(f"Session: `{session_id}`")
    lines.append(f"Source: `{source}`")
    lines.append(f"Status: `{result.risk_status}`")
    lines.append("")

    # Limit-Details als Tabelle
    if result.limit_details:
        lines.append("*Limit-Status:*")
        for detail in result.limit_details:
            if detail.severity.value == "ok":
                continue
            ratio_pct = detail.ratio * 100
            icon = "🔴" if detail.severity.value == "breach" else "🟡"
            lines.append(
                f"{icon} `{detail.limit_name}`: {detail.current_value:.2f} / "
                f"{detail.limit_value:.2f} ({ratio_pct:.1f}%)"
            )

    # Empfohlene Aktionen bei WARNING/BREACH
    if result.severity.value != "ok":
        lines.append("")
        lines.append("*Empfohlene Aktionen:*")
        for action in guidance.actions[:3]:
            lines.append(f"• {action}")

    return "\n".join(lines)


# =============================================================================
# ALERT TRIGGERING
# =============================================================================


def trigger_risk_alert(
    result: "LiveRiskCheckResult",
    alert_sink: Optional["AlertSink"],
    *,
    source: str = "live_risk",
    session_id: Optional[str] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Triggert einen Risk-Alert basierend auf dem LiveRiskCheckResult.

    Sendet nur bei WARNING oder BREACH. OK wird nicht alertet.

    Args:
        result: LiveRiskCheckResult
        alert_sink: AlertSink (None = kein Alert)
        source: Alert-Quelle (z.B. "live_risk.orders")
        session_id: Optional Session-ID
        extra_context: Zusätzliche Context-Daten

    Returns:
        True wenn Alert gesendet wurde, False sonst

    Example:
        >>> result = limits.check_orders(orders)
        >>> triggered = trigger_risk_alert(result, alert_sink, session_id="sess_123")
        >>> if triggered:
        ...     print("Alert gesendet!")
    """
    if alert_sink is None:
        return False

    if result.severity.value == "ok":
        # Kein Alert für OK-Status
        return False

    # Lazy import um zirkuläre Abhängigkeiten zu vermeiden
    from src.live.alerts import AlertEvent, AlertLevel

    # Alert-Level basierend auf Severity
    if result.severity.value == "breach":
        level = AlertLevel.CRITICAL
        code = "RISK_LIMIT_BREACH"
    else:
        level = AlertLevel.WARNING
        code = "RISK_LIMIT_WARNING"

    # Message formatieren
    message = format_risk_alert_message(result, source=source, include_details=True)

    # Context aufbauen
    context: Dict[str, Any] = {
        "risk_status": result.risk_status,
        "severity": result.severity.value,
        "allowed": result.allowed,
    }

    if session_id:
        context["session_id"] = session_id

    if result.metrics:
        context.update(result.metrics)

    if extra_context:
        context.update(extra_context)

    # Limit-Details als kompakte Liste
    if result.limit_details:
        context["limit_summary"] = [
            {
                "name": d.limit_name,
                "value": d.current_value,
                "limit": d.limit_value,
                "ratio": round(d.ratio, 3),
                "severity": d.severity.value,
            }
            for d in result.limit_details
            if d.severity.value != "ok"
        ]

    # Alert erstellen und senden
    alert = AlertEvent(
        ts=datetime.now(timezone.utc),
        level=level,
        source=source,
        code=code,
        message=message,
        context=context,
    )

    try:
        alert_sink.send(alert)
        logger.debug(f"Risk alert triggered: {code} from {source}")
        return True
    except Exception as e:
        logger.warning(f"Failed to send risk alert: {e}")
        return False


# =============================================================================
# CLI / TERMINAL OUTPUT FORMATTER
# =============================================================================


class RiskAlertFormatter:
    """
    Formatter für Risk-Alerts in verschiedenen Ausgabeformaten.

    Unterstützt:
    - Terminal/CLI (mit ANSI-Farben)
    - Plain Text
    - Slack
    - JSON

    Example:
        >>> formatter = RiskAlertFormatter()
        >>> print(formatter.format_terminal(result))
    """

    # ANSI Farb-Codes
    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "green": "\033[92m",
        "cyan": "\033[96m",
    }

    def __init__(self, use_colors: bool = True):
        """
        Initialisiert den Formatter.

        Args:
            use_colors: Ob ANSI-Farben verwendet werden sollen (Default: True)
        """
        self.use_colors = use_colors

    def _color(self, text: str, color: str) -> str:
        """Wendet ANSI-Farbe an wenn aktiviert."""
        if not self.use_colors:
            return text
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"

    def format_terminal(self, result: "LiveRiskCheckResult") -> str:
        """
        Formatiert Result für Terminal-Ausgabe mit Farben.

        Args:
            result: LiveRiskCheckResult

        Returns:
            Farbig formatierter String für Terminal
        """
        guidance = get_operator_guidance(result.risk_status)

        # Header mit Farbe basierend auf Status
        if result.risk_status == "red":
            header = self._color(f"⛔ RISK BREACH", "red")
            status_color = "red"
        elif result.risk_status == "yellow":
            header = self._color(f"⚠️  RISK WARNING", "yellow")
            status_color = "yellow"
        else:
            header = self._color(f"✅ RISK OK", "green")
            status_color = "green"

        lines = [
            self._color("─" * 50, "cyan"),
            header,
            self._color("─" * 50, "cyan"),
        ]

        # Status-Zeile
        status_text = self._color(result.risk_status.upper(), status_color)
        lines.append(f"Status: {status_text}")
        lines.append(f"Allowed: {result.allowed}")
        lines.append("")

        # Limit-Details
        if result.limit_details:
            lines.append(self._color("Limit-Checks:", "bold"))
            for detail in result.limit_details:
                ratio_pct = detail.ratio * 100

                if detail.severity.value == "breach":
                    icon = self._color("✗", "red")
                    name = self._color(detail.limit_name, "red")
                elif detail.severity.value == "warning":
                    icon = self._color("⚠", "yellow")
                    name = self._color(detail.limit_name, "yellow")
                else:
                    icon = self._color("✓", "green")
                    name = detail.limit_name

                lines.append(
                    f"  {icon} {name}: {detail.current_value:.2f} / "
                    f"{detail.limit_value:.2f} ({ratio_pct:.1f}%)"
                )

        # Empfehlungen bei nicht-OK
        if result.risk_status != "green":
            lines.append("")
            lines.append(self._color("Empfohlene Aktionen:", "bold"))
            for action in guidance.actions[:3]:
                lines.append(f"  • {action}")

        lines.append(self._color("─" * 50, "cyan"))

        return "\n".join(lines)

    def format_compact(self, result: "LiveRiskCheckResult") -> str:
        """
        Formatiert Result als einzeilige Zusammenfassung.

        Args:
            result: LiveRiskCheckResult

        Returns:
            Kompakter einzeiliger String
        """
        guidance = get_operator_guidance(result.risk_status)

        # Zähle Probleme
        warn_count = sum(
            1 for d in result.limit_details if d.severity.value == "warning"
        )
        breach_count = sum(
            1 for d in result.limit_details if d.severity.value == "breach"
        )

        if breach_count > 0:
            return (
                f"{guidance.icon} BREACH: {breach_count} Limit(s) verletzt, "
                f"allowed={result.allowed}"
            )
        elif warn_count > 0:
            return (
                f"{guidance.icon} WARNING: {warn_count} Limit(s) im Warnbereich, "
                f"allowed={result.allowed}"
            )
        else:
            return f"{guidance.icon} OK: Alle Limits eingehalten"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Guidance
    "OperatorGuidance",
    "get_operator_guidance",
    "get_guidance_for_result",
    # Formatting
    "format_limit_detail",
    "format_risk_alert_message",
    "format_slack_risk_alert",
    "RiskAlertFormatter",
    # Alerting
    "trigger_risk_alert",
]
