# src/live/alerts.py
"""
Peak_Trade: Live Alerts & Notifications (Phase 49 + 50)
========================================================

Leichtgewichtiges, erweiterbares Alert-System für Live-Trading.

Features:
- Alert-Level (INFO, WARNING, CRITICAL)
- Alert-Events mit Source, Code, Message, Context
- Alert-Sinks (Logging, Stderr, Webhook, Slack, Multi)
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

import json
import logging
import sys
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Protocol

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


class WebhookAlertSink:
    """
    Generischer HTTP-Webhook-Sink.

    Sendet AlertEvents als JSON-POST an eine oder mehrere URLs.
    Fehler (Timeouts, HTTP-Errors) werden geloggt, aber nicht weitergereicht.

    Attributes:
        _urls: Liste von Webhook-URLs
        _timeout_seconds: Timeout für HTTP-Requests
        _min_level: Minimaler Alert-Level
        _logger: Logger-Instanz
    """

    def __init__(
        self,
        urls: Sequence[str],
        timeout_seconds: float = 3.0,
        min_level: AlertLevel = AlertLevel.WARNING,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialisiert WebhookAlertSink.

        Args:
            urls: Liste von Webhook-URLs
            timeout_seconds: Timeout für HTTP-Requests (Default: 3.0)
            min_level: Minimaler Alert-Level (Default: WARNING)
            logger: Logger-Instanz (Default: peak_trade.live.alerts)
        """
        self._urls = [u for u in urls if u]
        self._timeout_seconds = float(timeout_seconds)
        self._min_level = min_level
        self._logger = logger or logging.getLogger("peak_trade.live.alerts")

    def send(self, alert: AlertEvent) -> None:
        """
        Sendet Alert als JSON-POST an alle konfigurierten URLs.

        Args:
            alert: Alert-Event
        """
        if alert.level < self._min_level:
            return
        if not self._urls:
            return

        payload = self._build_payload(alert)
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        for url in self._urls:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                # Response wird verworfen, wir interessieren uns nur für "best effort"
                with urllib.request.urlopen(req, timeout=self._timeout_seconds):
                    pass
            except Exception as exc:
                # Keine Exception nach außen – nur loggen
                self._logger.exception(
                    "Failed to send alert to webhook %r: %s", url, exc
                )

    def _build_payload(self, alert: AlertEvent) -> dict[str, Any]:
        """
        Baut JSON-Payload für Webhook.

        Args:
            alert: Alert-Event

        Returns:
            Dict mit strukturierten Alert-Daten
        """
        ctx = dict(alert.context) if alert.context else {}
        return {
            "ts": alert.ts.isoformat(),
            "level": alert.level.name,
            "source": alert.source,
            "code": alert.code,
            "message": alert.message,
            "context": ctx,
        }


class SlackWebhookAlertSink:
    """
    Slack-spezifischer Webhook-Sink.

    Nutzt das einfache Slack-Webhook-Format mit einem "text"-Feld.

    Attributes:
        _urls: Liste von Slack-Webhook-URLs
        _timeout_seconds: Timeout für HTTP-Requests
        _min_level: Minimaler Alert-Level
        _logger: Logger-Instanz
    """

    def __init__(
        self,
        urls: Sequence[str],
        timeout_seconds: float = 3.0,
        min_level: AlertLevel = AlertLevel.WARNING,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialisiert SlackWebhookAlertSink.

        Args:
            urls: Liste von Slack-Webhook-URLs
            timeout_seconds: Timeout für HTTP-Requests (Default: 3.0)
            min_level: Minimaler Alert-Level (Default: WARNING)
            logger: Logger-Instanz (Default: peak_trade.live.alerts)
        """
        self._urls = [u for u in urls if u]
        self._timeout_seconds = float(timeout_seconds)
        self._min_level = min_level
        self._logger = logger or logging.getLogger("peak_trade.live.alerts")

    def send(self, alert: AlertEvent) -> None:
        """
        Sendet Alert als Slack-Webhook ({"text": "..."}).

        Args:
            alert: Alert-Event
        """
        if alert.level < self._min_level:
            return
        if not self._urls:
            return

        text = self._build_text(alert)
        payload = {"text": text}
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        for url in self._urls:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self._timeout_seconds):
                    pass
            except Exception as exc:
                self._logger.exception(
                    "Failed to send alert to Slack webhook %r: %s", url, exc
                )

    def _build_text(self, alert: AlertEvent) -> str:
        """
        Baut Text für Slack-Webhook.

        Args:
            alert: Alert-Event

        Returns:
            Formatierter Text-String
        """
        base = f"[{alert.level.name}] {alert.source} - {alert.code}: {alert.message}"
        if alert.context:
            # Kontext kompakt anhängen – Slack kann das später auch als Codeblock formatiert bekommen
            return f"{base}\ncontext: {alert.context}"
        return base


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
        sinks: Liste der aktiven Sink-Namen (z.B. ["log", "stderr", "webhook", "slack_webhook"])
        log_logger_name: Logger-Name für Logging-Sink
        webhook_urls: Liste von generischen Webhook-URLs
        slack_webhook_urls: Liste von Slack-Webhook-URLs
        webhook_timeout_seconds: Timeout für HTTP-Requests (Default: 3.0)
    """

    enabled: bool = True
    min_level: AlertLevel = AlertLevel.WARNING
    sinks: list[str] = field(default_factory=lambda: ["log"])
    log_logger_name: str = "peak_trade.live.alerts"

    # Phase 50: Webhook & Slack
    webhook_urls: list[str] = field(default_factory=list)
    slack_webhook_urls: list[str] = field(default_factory=list)
    webhook_timeout_seconds: float = 3.0

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

        # Phase 50: Webhook & Slack URLs
        webhook_urls_raw = raw.get("webhook_urls", [])
        if isinstance(webhook_urls_raw, str):
            webhook_urls = [webhook_urls_raw]
        else:
            webhook_urls = list(webhook_urls_raw)

        slack_urls_raw = raw.get("slack_webhook_urls", [])
        if isinstance(slack_urls_raw, str):
            slack_webhook_urls = [slack_urls_raw]
        else:
            slack_webhook_urls = list(slack_urls_raw)

        timeout = float(raw.get("webhook_timeout_seconds", 3.0))

        return cls(
            enabled=enabled,
            min_level=min_level,
            sinks=sinks,
            log_logger_name=log_logger_name,
            webhook_urls=webhook_urls,
            slack_webhook_urls=slack_webhook_urls,
            webhook_timeout_seconds=timeout,
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
    base_logger = logging.getLogger(cfg.log_logger_name)

    for sink_name in cfg.sinks:
        if sink_name == "log":
            built_sinks.append(LoggingAlertSink(base_logger, cfg.min_level))
        elif sink_name == "stderr":
            built_sinks.append(StderrAlertSink(cfg.min_level))
        elif sink_name == "webhook":
            if cfg.webhook_urls:
                built_sinks.append(
                    WebhookAlertSink(
                        urls=cfg.webhook_urls,
                        timeout_seconds=cfg.webhook_timeout_seconds,
                        min_level=cfg.min_level,
                        logger=base_logger,
                    )
                )
            else:
                base_logger.warning(
                    "live_alerts.sinks includes 'webhook' but no webhook_urls are configured"
                )
        elif sink_name == "slack_webhook":
            if cfg.slack_webhook_urls:
                built_sinks.append(
                    SlackWebhookAlertSink(
                        urls=cfg.slack_webhook_urls,
                        timeout_seconds=cfg.webhook_timeout_seconds,
                        min_level=cfg.min_level,
                        logger=base_logger,
                    )
                )
            else:
                base_logger.warning(
                    "live_alerts.sinks includes 'slack_webhook' but no slack_webhook_urls are configured"
                )
        else:
            base_logger.warning(
                "Unknown alert sink name %r in live_alerts.sinks", sink_name
            )

    if not built_sinks:
        return None
    if len(built_sinks) == 1:
        return built_sinks[0]
    return MultiAlertSink(built_sinks)
