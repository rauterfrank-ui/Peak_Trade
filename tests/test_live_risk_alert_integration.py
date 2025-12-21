# tests/test_live_risk_alert_integration.py
"""
Tests für Risk-Alert-Integration (Phase 49 + 50)
=================================================

Tests für:
- Order-Violation → Alert
- Portfolio-Violation → Alert
- Enabled=False → kein Alert
- Webhook-Integration (Phase 50)
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone

import pytest

from src.live.alerts import AlertEvent, AlertLevel, LiveAlertsConfig, build_alert_sink_from_config
from src.live.orders import LiveOrderRequest
from src.live.portfolio_monitor import LivePortfolioSnapshot, LivePositionSnapshot
from src.live.risk_limits import LiveRiskConfig, LiveRiskLimits

# =============================================================================
# FIXTURES
# =============================================================================


class CollectingAlertSink:
    """Alert-Sink, der Events sammelt (für Tests)."""

    def __init__(self) -> None:
        self.events: list[AlertEvent] = []

    def send(self, alert: AlertEvent) -> None:
        self.events.append(alert)


@pytest.fixture
def collecting_sink() -> CollectingAlertSink:
    """Erstellt einen CollectingAlertSink."""
    return CollectingAlertSink()


@pytest.fixture
def risk_config_low_limits() -> LiveRiskConfig:
    """Erstellt LiveRiskConfig mit niedrigen Limits (für Verletzungs-Tests)."""
    return LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=1000.0,  # Niedrig
        max_symbol_exposure_notional=500.0,  # Niedrig
        max_open_positions=2,  # Niedrig
        max_order_notional=500.0,  # Niedrig
        max_daily_loss_abs=100.0,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )


@pytest.fixture
def risk_config_ok_limits() -> LiveRiskConfig:
    """Erstellt LiveRiskConfig mit ausreichend hohen Limits (OK-Fall)."""
    return LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=50000.0,
        max_symbol_exposure_notional=20000.0,
        max_open_positions=10,
        max_order_notional=10000.0,
        max_daily_loss_abs=1000.0,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )


# =============================================================================
# ORDER VIOLATION TESTS
# =============================================================================


def test_order_violation_emits_alert(
    collecting_sink: CollectingAlertSink,
    risk_config_low_limits: LiveRiskConfig,
):
    """Testet dass Order-Violation einen Alert erzeugt."""
    risk_limits = LiveRiskLimits(risk_config_low_limits, alert_sink=collecting_sink)

    # Order-Batch, der Limits verletzt
    orders = [
        LiveOrderRequest(
            client_order_id="test_1",
            symbol="BTC/EUR",
            side="BUY",
            order_type="MARKET",
            quantity=1.0,
            notional=2000.0,  # Überschreitet max_total_exposure_notional (1000.0)
        ),
    ]

    result = risk_limits.check_orders(orders)

    # Prüfe dass Violation erkannt wurde
    assert result.allowed is False

    # Prüfe dass Alert erzeugt wurde
    assert len(collecting_sink.events) == 1
    alert = collecting_sink.events[0]

    assert alert.source == "live_risk.orders"
    assert alert.code == "RISK_LIMIT_VIOLATION_ORDERS"
    assert alert.level == AlertLevel.CRITICAL  # block_on_violation=True → CRITICAL
    assert "Live risk limit violation" in alert.message
    assert "num_orders" in alert.context


def test_order_violation_no_block_emits_warning(
    collecting_sink: CollectingAlertSink,
):
    """Testet dass Order-Violation ohne block_on_violation WARNING erzeugt."""
    config = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=1000.0,
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        block_on_violation=False,  # Nicht blockieren
        use_experiments_for_daily_pnl=True,
    )

    risk_limits = LiveRiskLimits(config, alert_sink=collecting_sink)

    orders = [
        LiveOrderRequest(
            client_order_id="test_1",
            symbol="BTC/EUR",
            side="BUY",
            order_type="MARKET",
            quantity=1.0,
            notional=2000.0,  # Überschreitet Limit
        ),
    ]

    result = risk_limits.check_orders(orders)

    assert result.allowed is False
    assert len(collecting_sink.events) == 1
    assert collecting_sink.events[0].level == AlertLevel.WARNING  # Nicht CRITICAL


def test_order_ok_no_alert(
    collecting_sink: CollectingAlertSink,
    risk_config_ok_limits: LiveRiskConfig,
):
    """Testet dass keine Alerts bei OK-Orders erzeugt werden."""
    risk_limits = LiveRiskLimits(risk_config_ok_limits, alert_sink=collecting_sink)

    # Order-Batch, der innerhalb der Limits liegt
    orders = [
        LiveOrderRequest(
            client_order_id="test_1",
            symbol="BTC/EUR",
            side="BUY",
            order_type="MARKET",
            quantity=0.1,
            notional=500.0,  # Innerhalb der Limits
        ),
    ]

    result = risk_limits.check_orders(orders)

    # Prüfe dass OK
    assert result.allowed is True

    # Prüfe dass kein Alert erzeugt wurde
    assert len(collecting_sink.events) == 0


def test_order_violation_no_alert_sink(risk_config_low_limits: LiveRiskConfig):
    """Testet dass keine Alerts erzeugt werden, wenn kein Alert-Sink konfiguriert ist."""
    risk_limits = LiveRiskLimits(risk_config_low_limits, alert_sink=None)

    orders = [
        LiveOrderRequest(
            client_order_id="test_1",
            symbol="BTC/EUR",
            side="BUY",
            order_type="MARKET",
            quantity=1.0,
            notional=2000.0,
        ),
    ]

    # Sollte nicht crashen
    result = risk_limits.check_orders(orders)

    assert result.allowed is False


# =============================================================================
# PORTFOLIO VIOLATION TESTS
# =============================================================================


def test_portfolio_violation_emits_alert(
    collecting_sink: CollectingAlertSink,
    risk_config_low_limits: LiveRiskConfig,
):
    """Testet dass Portfolio-Violation einen Alert erzeugt."""
    risk_limits = LiveRiskLimits(risk_config_low_limits, alert_sink=collecting_sink)

    # Portfolio-Snapshot, der Limits verletzt
    positions = [
        LivePositionSnapshot(
            symbol="BTC/EUR",
            side="long",
            size=1.0,
            mark_price=2000.0,
            notional=2000.0,  # Überschreitet max_total_exposure_notional (1000.0)
        ),
    ]

    snapshot = LivePortfolioSnapshot(
        as_of=datetime.now(timezone.utc),
        positions=positions,
    )

    result = risk_limits.evaluate_portfolio(snapshot)

    # Prüfe dass Violation erkannt wurde
    assert result.allowed is False

    # Prüfe dass Alert erzeugt wurde
    assert len(collecting_sink.events) == 1
    alert = collecting_sink.events[0]

    assert alert.source == "live_risk.portfolio"
    assert alert.code == "RISK_LIMIT_VIOLATION_PORTFOLIO"
    assert alert.level == AlertLevel.CRITICAL
    assert "Live risk limit violation" in alert.message
    assert "as_of" in alert.context
    assert "total_notional" in alert.context


def test_portfolio_ok_no_alert(
    collecting_sink: CollectingAlertSink,
    risk_config_ok_limits: LiveRiskConfig,
):
    """Testet dass keine Alerts bei OK-Portfolio erzeugt werden."""
    risk_limits = LiveRiskLimits(risk_config_ok_limits, alert_sink=collecting_sink)

    positions = [
        LivePositionSnapshot(
            symbol="BTC/EUR",
            side="long",
            size=0.1,
            mark_price=30000.0,
            notional=3000.0,  # Innerhalb der Limits
        ),
    ]

    snapshot = LivePortfolioSnapshot(
        as_of=datetime.now(timezone.utc),
        positions=positions,
    )

    result = risk_limits.evaluate_portfolio(snapshot)

    # Prüfe dass OK
    assert result.allowed is True

    # Prüfe dass kein Alert erzeugt wurde
    assert len(collecting_sink.events) == 0


# =============================================================================
# ENABLED=FALSE TESTS
# =============================================================================


def test_alerts_disabled_no_alerts(collecting_sink: CollectingAlertSink):
    """Testet dass bei enabled=False keine Alerts erzeugt werden."""
    config = LiveAlertsConfig(enabled=False)
    sink = build_alert_sink_from_config(config)

    assert sink is None

    # Auch wenn wir einen Sink hätten, sollte LiveRiskLimits ohne Sink keine Alerts erzeugen
    risk_config = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=1000.0,
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )

    risk_limits = LiveRiskLimits(risk_config, alert_sink=None)  # Kein Sink

    orders = [
        LiveOrderRequest(
            client_order_id="test_1",
            symbol="BTC/EUR",
            side="BUY",
            order_type="MARKET",
            quantity=1.0,
            notional=2000.0,
        ),
    ]

    result = risk_limits.check_orders(orders)

    assert result.allowed is False
    # Kein Alert-Sink → keine Events
    assert len(collecting_sink.events) == 0


# =============================================================================
# WEBHOOK INTEGRATION TESTS (Phase 50)
# =============================================================================


def test_risk_violation_triggers_webhook(monkeypatch):
    """Testet dass Risk-Violation einen Webhook-Aufruf auslöst."""
    called_urls = []
    called_payloads = []

    def fake_urlopen(req, timeout=0):
        called_urls.append(req.full_url)
        payload = json.loads(req.data.decode("utf-8"))
        called_payloads.append(payload)

        class DummyResp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return DummyResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    cfg_dict = {
        "enabled": True,
        "min_level": "warning",
        "sinks": ["webhook"],
        "webhook_urls": ["https://example.com/alert"],
        "webhook_timeout_seconds": 1.0,
    }
    alerts_cfg = LiveAlertsConfig.from_dict(cfg_dict)
    alert_sink = build_alert_sink_from_config(alerts_cfg)

    assert alert_sink is not None

    # Baue LiveRiskLimits mit sehr strengen Limits, damit eine Violation garantiert ist
    risk_cfg = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=1.0,  # Sehr niedrig
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )

    limits = LiveRiskLimits(config=risk_cfg, alert_sink=alert_sink)

    # Dummy-Order-Batch, der das Limit sicher überschreitet
    orders = [
        LiveOrderRequest(
            client_order_id="test_1",
            symbol="BTC/EUR",
            side="BUY",
            order_type="MARKET",
            quantity=1.0,
            notional=2000.0,  # Überschreitet Limit deutlich
        ),
    ]

    result = limits.check_orders(orders)

    assert result.allowed is False
    assert len(called_urls) == 1
    assert called_urls[0] == "https://example.com/alert"

    # Prüfe Payload
    assert len(called_payloads) == 1
    payload = called_payloads[0]
    assert payload["level"] == "CRITICAL"
    assert payload["source"] == "live_risk.orders"
    assert payload["code"] == "RISK_LIMIT_VIOLATION_ORDERS"
    assert "Live risk limit violation" in payload["message"]


def test_risk_violation_triggers_slack_webhook(monkeypatch):
    """Testet dass Risk-Violation einen Slack-Webhook-Aufruf auslöst."""
    called_urls = []
    called_payloads = []

    def fake_urlopen(req, timeout=0):
        called_urls.append(req.full_url)
        payload = json.loads(req.data.decode("utf-8"))
        called_payloads.append(payload)

        class DummyResp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return DummyResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    cfg_dict = {
        "enabled": True,
        "min_level": "warning",
        "sinks": ["slack_webhook"],
        "slack_webhook_urls": ["https://hooks.slack.com/services/AAA/BBB/CCC"],
        "webhook_timeout_seconds": 2.0,
    }
    alerts_cfg = LiveAlertsConfig.from_dict(cfg_dict)
    alert_sink = build_alert_sink_from_config(alerts_cfg)

    assert alert_sink is not None

    risk_cfg = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=1.0,
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )

    limits = LiveRiskLimits(config=risk_cfg, alert_sink=alert_sink)

    orders = [
        LiveOrderRequest(
            client_order_id="test_1",
            symbol="BTC/EUR",
            side="BUY",
            order_type="MARKET",
            quantity=1.0,
            notional=2000.0,
        ),
    ]

    result = limits.check_orders(orders)

    assert result.allowed is False
    assert len(called_urls) == 1
    assert "hooks.slack.com" in called_urls[0]

    # Prüfe Slack-Payload-Format
    assert len(called_payloads) == 1
    payload = called_payloads[0]
    assert "text" in payload
    assert "RISK_LIMIT_VIOLATION_ORDERS" in payload["text"]
    assert "CRITICAL" in payload["text"]


def test_portfolio_violation_triggers_webhook(monkeypatch):
    """Testet dass Portfolio-Violation einen Webhook-Aufruf auslöst."""
    called_urls = []

    def fake_urlopen(req, timeout=0):
        called_urls.append(req.full_url)

        class DummyResp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return DummyResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    cfg_dict = {
        "enabled": True,
        "min_level": "warning",
        "sinks": ["webhook"],
        "webhook_urls": ["https://example.com/alert"],
    }
    alerts_cfg = LiveAlertsConfig.from_dict(cfg_dict)
    alert_sink = build_alert_sink_from_config(alerts_cfg)

    risk_cfg = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=1.0,
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )

    limits = LiveRiskLimits(config=risk_cfg, alert_sink=alert_sink)

    positions = [
        LivePositionSnapshot(
            symbol="BTC/EUR",
            side="long",
            size=1.0,
            mark_price=2000.0,
            notional=2000.0,  # Überschreitet Limit
        ),
    ]

    snapshot = LivePortfolioSnapshot(
        as_of=datetime.now(timezone.utc),
        positions=positions,
    )

    result = limits.evaluate_portfolio(snapshot)

    assert result.allowed is False
    assert len(called_urls) == 1
    assert called_urls[0] == "https://example.com/alert"
