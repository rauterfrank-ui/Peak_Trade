# src/live/alerts.py
"""
Peak_Trade: Live Alerts & Notifications (Phase 49)
===================================================

Leichtgewichtiges, erweiterbares Alert-System für Live-Trading.

Features:
- Alert-Level (INFO, WARNING, CRITICAL)
- Alert-Events mit Source, Code, Message, Context
- Alert-Sinks (Logging, Stderr, Multi)
- Config-basierte Konfiguration

Usage:
    from src.live.alerts import (
        AlertLevel,
        AlertEvent,
        LiveAlertsConfig,
        build_alert_sink_from_config,
    )

    config = LiveAlertsConfig.from_dict({"enabled": True, "min_level": "warning"})
    sink = build_alert_sink_from_config(config)

    alert = AlertEvent(
        ts=datetime.now(timezone.utc),
        level=AlertLevel.CRITICAL,
        source="live_risk.orders",
        code="RISK_LIMIT_VIOLATION",
        message="Risk limit violation detected",
    )
    sink.send(alert)
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Mapping, Protocol, Sequence

logger = logging.getLogger(__name__)


class AlertLevel(IntEnum):
    """Alert-Level für Severity-Klassifizierung."""

    INFO = 10
    WARNING = 20
    CRITICAL = 30


@dataclass
class AlertEvent:
    """
    Ein Alert-Event.

    Attributes:
        ts: Zeitstempel des Events
        level: Alert-Level (INFO, WARNING, CRITICAL)
        source: Quelle des Alerts (z.B. "live_risk.orders", "live_risk.portfolio")
        code: Maschinenlesbarer Code (z.B. "RISK_LIMIT_VIOLATION_TOTAL_EXPOSURE")
        message: Menschenlesbare Kurzbeschreibung
        context: Zusätzliche Kontext-Daten (z.B. {"portfolio_total_notional": 12345.0})
    """

    ts: datetime
    level: AlertLevel
    source: str
    code: str
    message: str
    context: Mapping[str, Any] = field(default_factory=dict)


class AlertSink(Protocol):
    """Protokoll für Alert-Sinks."""

    def send(self, alert: AlertEvent) -> None:  # pragma: no cover
        """
        Sendet einen Alert.

        Args:
            alert: Alert-Event
        """
        ...


class LoggingAlertSink:
    """
    Alert-Sink, der Alerts über Python-Logging ausgibt.

    Attributes:
        _logger: Logger-Instanz
        _min_level: Minimaler Alert-Level, der geloggt wird
    """

    def __init__(
        self,
        logger: logging.Logger,
        min_level: AlertLevel = AlertLevel.WARNING,
    ) -> None:
        """
        Initialisiert LoggingAlertSink.

        Args:
            logger: Logger-Instanz
            min_level: Minimaler Alert-Level (Default: WARNING)
        """
        self._logger = logger
        self._min_level = min_level

    def send(self, alert: AlertEvent) -> None:
        """
        Sendet Alert über Logger.

        Args:
            alert: Alert-Event
        """
        if alert.level < self._min_level:
            return

        msg = f"[{alert.level.name}] {alert.source} - {alert.code}: {alert.message}"
        if alert.context:
            # Context bewusst kompakt halten
            context_str = str(alert.context)
            if len(context_str) > 200:
                context_str = context_str[:200] + "..."
            msg = f"{msg} | context={context_str}"

        if alert.level >= AlertLevel.CRITICAL:
            self._logger.error(msg)
        elif alert.level >= AlertLevel.WARNING:
            self._logger.warning(msg)
        else:
            self._logger.info(msg)


class StderrAlertSink:
    """
    Alert-Sink, der Alerts auf stderr ausgibt.

    Attributes:
        _min_level: Minimaler Alert-Level, der ausgegeben wird
    """

    def __init__(self, min_level: AlertLevel = AlertLevel.WARNING) -> None:
        """
        Initialisiert StderrAlertSink.

        Args:
            min_level: Minimaler Alert-Level (Default: WARNING)
        """
        self._min_level = min_level

    def send(self, alert: AlertEvent) -> None:
        """
        Sendet Alert auf stderr.

        Args:
            alert: Alert-Event
        """
        if alert.level < self._min_level:
            return

        ts_str = alert.ts.isoformat()
        msg = f"[{ts_str}] [{alert.level.name}] {alert.source} - {alert.code}: {alert.message}"
        if alert.context:
            context_str = str(alert.context)
            if len(context_str) > 200:
                context_str = context_str[:200] + "..."
            msg = f"{msg} | context={context_str}"

        print(msg, file=sys.stderr)


class MultiAlertSink:
    """
    Alert-Sink, der Alerts an mehrere Sinks weiterleitet.

    Attributes:
        _sinks: Liste von Alert-Sinks
    """

    def __init__(self, sinks: Sequence[AlertSink]) -> None:
        """
        Initialisiert MultiAlertSink.

        Args:
            sinks: Liste von Alert-Sinks
        """
        self._sinks = list(sinks)

    def send(self, alert: AlertEvent) -> None:
        """
        Sendet Alert an alle Sinks.

        Args:
            alert: Alert-Event
        """
        for sink in self._sinks:
            try:
                sink.send(alert)
            except Exception:
                # Keine Exception nach außen propagieren – Alerts dürfen nicht den Live-Flow crashen
                logging.getLogger("peak_trade.live.alerts").exception(
                    "Failed to send alert via %r", sink
                )


@dataclass
class LiveAlertsConfig:
    """
    Konfiguration für Live-Alerts.

    Attributes:
        enabled: Ob Alerts aktiviert sind
        min_level: Minimaler Alert-Level (INFO, WARNING, CRITICAL)
        sinks: Liste der aktiven Sink-Namen (z.B. ["log", "stderr"])
        log_logger_name: Logger-Name für Logging-Sink
    """

    enabled: bool = True
    min_level: AlertLevel = AlertLevel.WARNING
    sinks: list[str] = field(default_factory=lambda: ["log"])
    log_logger_name: str = "peak_trade.live.alerts"

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> LiveAlertsConfig:
        """
        Erstellt LiveAlertsConfig aus Dict (z.B. aus PeakConfig).

        Args:
            raw: Dict mit Config-Werten

        Returns:
            LiveAlertsConfig
        """
        enabled = bool(raw.get("enabled", True))

        level_str = str(raw.get("min_level", "warning")).lower()
        if level_str == "info":
            min_level = AlertLevel.INFO
        elif level_str == "critical":
            min_level = AlertLevel.CRITICAL
        else:
            min_level = AlertLevel.WARNING

        sinks_raw = raw.get("sinks", ["log"])
        if isinstance(sinks_raw, str):
            sinks = [sinks_raw]
        else:
            sinks = list(sinks_raw)

        log_logger_name = str(raw.get("log_logger_name", "peak_trade.live.alerts"))

        return cls(
            enabled=enabled,
            min_level=min_level,
            sinks=sinks,
            log_logger_name=log_logger_name,
        )


def build_alert_sink_from_config(cfg: LiveAlertsConfig) -> AlertSink | None:
    """
    Baut einen Alert-Sink aus Config.

    Args:
        cfg: LiveAlertsConfig

    Returns:
        AlertSink oder None (wenn disabled oder keine Sinks)
    """
    if not cfg.enabled:
        return None

    built_sinks: list[AlertSink] = []

    for sink_name in cfg.sinks:
        if sink_name == "log":
            logger = logging.getLogger(cfg.log_logger_name)
            built_sinks.append(LoggingAlertSink(logger, cfg.min_level))
        elif sink_name == "stderr":
            built_sinks.append(StderrAlertSink(cfg.min_level))
        else:
            # Unbekannte Sink-Namen ignorieren oder loggen
            logging.getLogger(cfg.log_logger_name).warning(
                "Unknown alert sink name %r in live_alerts.sinks", sink_name
            )

    if not built_sinks:
        return None
    if len(built_sinks) == 1:
        return built_sinks[0]
    return MultiAlertSink(built_sinks)
