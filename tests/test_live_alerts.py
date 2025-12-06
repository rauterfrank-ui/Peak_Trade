# tests/test_live_alerts.py
"""
Tests für src/live/alerts.py (Phase 34)

Testet das Alert-System:
- AlertRule und AlertEvent Dataclasses
- AlertEngine mit verschiedenen Regeln
- Debouncing
- Alert-Logging in Dateien
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from src.live.monitoring import LiveRunSnapshot
from src.live.alerts import (
    Severity,
    AlertsConfig,
    AlertRule,
    AlertEvent,
    AlertEngine,
    load_alerts_config,
    create_risk_blocked_rule,
    create_large_loss_abs_rule,
    create_large_loss_pct_rule,
    create_no_events_rule,
    create_alert_engine_from_config,
    append_alerts_to_file,
    load_alerts_from_file,
    render_alerts,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_snapshot() -> LiveRunSnapshot:
    """Erstellt einen Sample-Snapshot."""
    return LiveRunSnapshot(
        run_id="test_run_001",
        mode="paper",
        strategy_name="ma_crossover",
        symbol="BTC/EUR",
        timeframe="1m",
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
        ended_at=None,
        last_bar_time=datetime.now(timezone.utc) - timedelta(minutes=1),
        last_price=40000.0,
        position_size=0.1,
        cash=9000.0,
        equity=10000.0,
        realized_pnl=100.0,
        unrealized_pnl=50.0,
        total_steps=100,
        total_orders=10,
        total_blocked_orders=0,
    )


@pytest.fixture
def blocked_snapshot() -> LiveRunSnapshot:
    """Erstellt einen Snapshot mit blockierten Orders."""
    return LiveRunSnapshot(
        run_id="test_run_002",
        mode="paper",
        strategy_name="ma_crossover",
        symbol="BTC/EUR",
        timeframe="1m",
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
        ended_at=None,
        last_bar_time=datetime.now(timezone.utc) - timedelta(minutes=1),
        last_price=40000.0,
        position_size=0.1,
        cash=9000.0,
        equity=10000.0,
        realized_pnl=-100.0,
        unrealized_pnl=-50.0,
        total_steps=100,
        total_orders=10,
        total_blocked_orders=3,  # Blockierte Orders!
    )


@pytest.fixture
def loss_snapshot() -> LiveRunSnapshot:
    """Erstellt einen Snapshot mit großen Verlusten."""
    return LiveRunSnapshot(
        run_id="test_run_003",
        mode="paper",
        strategy_name="ma_crossover",
        symbol="BTC/EUR",
        timeframe="1m",
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
        ended_at=None,
        last_bar_time=datetime.now(timezone.utc) - timedelta(minutes=1),
        last_price=40000.0,
        position_size=0.1,
        cash=8000.0,
        equity=8500.0,
        realized_pnl=-600.0,  # Großer Verlust!
        unrealized_pnl=-100.0,
        total_steps=100,
        total_orders=10,
        total_blocked_orders=0,
    )


@pytest.fixture
def temp_run_dir() -> Path:
    """Erstellt ein temporäres Run-Verzeichnis."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "test_run"
        run_dir.mkdir(parents=True)
        yield run_dir


# =============================================================================
# Severity Tests
# =============================================================================


class TestSeverity:
    """Tests für Severity-Klasse."""

    def test_rank_info(self) -> None:
        """Test Rank für info."""
        assert Severity.rank("info") == 0

    def test_rank_warning(self) -> None:
        """Test Rank für warning."""
        assert Severity.rank("warning") == 1

    def test_rank_critical(self) -> None:
        """Test Rank für critical."""
        assert Severity.rank("critical") == 2

    def test_is_at_least_same(self) -> None:
        """Test is_at_least mit gleicher Severity."""
        assert Severity.is_at_least("warning", "warning") is True

    def test_is_at_least_higher(self) -> None:
        """Test is_at_least mit höherer Severity."""
        assert Severity.is_at_least("critical", "warning") is True

    def test_is_at_least_lower(self) -> None:
        """Test is_at_least mit niedrigerer Severity."""
        assert Severity.is_at_least("info", "warning") is False


# =============================================================================
# Config Tests
# =============================================================================


class TestAlertsConfig:
    """Tests für AlertsConfig."""

    def test_default_values(self) -> None:
        """Test Default-Werte."""
        cfg = AlertsConfig()
        assert cfg.enabled is True
        assert cfg.min_severity == "warning"
        assert cfg.debounce_seconds == 60
        assert cfg.enable_risk_blocked is True
        assert cfg.enable_large_loss_abs is True
        assert cfg.large_loss_abs_threshold == -500.0

    def test_load_from_config(self) -> None:
        """Test Laden aus Mock-Config."""
        class MockConfig:
            def get(self, path: str, default: Any = None) -> Any:
                values = {
                    "alerts.enabled": True,
                    "alerts.min_severity": "critical",
                    "alerts.debounce_seconds": 120,
                    "alerts.rules.enable_risk_blocked": False,
                    "alerts.rules.large_loss_abs_threshold": -1000.0,
                }
                return values.get(path, default)

        cfg = load_alerts_config(MockConfig())
        assert cfg.min_severity == "critical"
        assert cfg.debounce_seconds == 120
        assert cfg.enable_risk_blocked is False
        assert cfg.large_loss_abs_threshold == -1000.0


# =============================================================================
# AlertRule Tests
# =============================================================================


class TestAlertRule:
    """Tests für AlertRule."""

    def test_rule_creation(self) -> None:
        """Test Regel-Erstellung."""
        rule = AlertRule(
            id="test_rule",
            description="Test rule",
            severity=Severity.WARNING,
        )
        assert rule.id == "test_rule"
        assert rule.severity == "warning"
        assert rule.enabled is True

    def test_rule_check_returns_none_when_no_fn(
        self, sample_snapshot: LiveRunSnapshot
    ) -> None:
        """Test check() ohne check_fn."""
        rule = AlertRule(
            id="test_rule",
            description="Test rule",
            severity=Severity.WARNING,
        )
        assert rule.check(sample_snapshot) is None

    def test_rule_check_disabled(self, sample_snapshot: LiveRunSnapshot) -> None:
        """Test check() bei deaktivierter Regel."""
        rule = AlertRule(
            id="test_rule",
            description="Test rule",
            severity=Severity.WARNING,
            enabled=False,
            check_fn=lambda s: "Alert!",
        )
        assert rule.check(sample_snapshot) is None


# =============================================================================
# Built-in Rules Tests
# =============================================================================


class TestRiskBlockedRule:
    """Tests für risk_blocked_rule."""

    def test_no_alert_when_not_blocked(self, sample_snapshot: LiveRunSnapshot) -> None:
        """Kein Alert wenn keine Orders blockiert."""
        rule = create_risk_blocked_rule()
        assert rule.check(sample_snapshot) is None

    def test_alert_when_blocked(self, blocked_snapshot: LiveRunSnapshot) -> None:
        """Alert wenn Orders blockiert."""
        rule = create_risk_blocked_rule()
        message = rule.check(blocked_snapshot)
        assert message is not None
        assert "3" in message  # 3 blockierte Orders
        assert "risk-blocked" in message.lower()

    def test_disabled_rule(self, blocked_snapshot: LiveRunSnapshot) -> None:
        """Deaktivierte Regel löst nicht aus."""
        rule = create_risk_blocked_rule(enabled=False)
        assert rule.check(blocked_snapshot) is None


class TestLargeLossAbsRule:
    """Tests für large_loss_abs_rule."""

    def test_no_alert_when_profit(self, sample_snapshot: LiveRunSnapshot) -> None:
        """Kein Alert bei Profit."""
        rule = create_large_loss_abs_rule(threshold=-500.0)
        assert rule.check(sample_snapshot) is None

    def test_alert_when_large_loss(self, loss_snapshot: LiveRunSnapshot) -> None:
        """Alert bei großem Verlust."""
        rule = create_large_loss_abs_rule(threshold=-500.0)
        message = rule.check(loss_snapshot)
        assert message is not None
        assert "-600" in message or "600" in message

    def test_custom_threshold(self, loss_snapshot: LiveRunSnapshot) -> None:
        """Test mit Custom-Threshold."""
        rule = create_large_loss_abs_rule(threshold=-1000.0)
        # -600 ist > -1000, also kein Alert
        assert rule.check(loss_snapshot) is None


class TestLargeLossPctRule:
    """Tests für large_loss_pct_rule."""

    def test_no_alert_when_profit(self, sample_snapshot: LiveRunSnapshot) -> None:
        """Kein Alert bei Profit."""
        rule = create_large_loss_pct_rule(threshold=-10.0)
        assert rule.check(sample_snapshot) is None

    def test_no_alert_when_small_loss(self, sample_snapshot: LiveRunSnapshot) -> None:
        """Kein Alert bei kleinem Verlust."""
        # Snapshot mit kleinem Verlust
        snapshot = LiveRunSnapshot(
            run_id="test",
            mode="paper",
            strategy_name="test",
            symbol="BTC/EUR",
            timeframe="1m",
            started_at=None,
            ended_at=None,
            last_bar_time=None,
            last_price=40000.0,
            position_size=0.1,
            cash=9500.0,
            equity=9800.0,  # Equity
            realized_pnl=-50.0,  # -50 von (9800+50)=9850 = -0.5%
            unrealized_pnl=0.0,
            total_steps=100,
            total_orders=10,
            total_blocked_orders=0,
        )
        rule = create_large_loss_pct_rule(threshold=-10.0)
        assert rule.check(snapshot) is None


# =============================================================================
# AlertEngine Tests
# =============================================================================


class TestAlertEngine:
    """Tests für AlertEngine."""

    def test_engine_creation(self) -> None:
        """Test Engine-Erstellung."""
        rules = [
            create_risk_blocked_rule(),
            create_large_loss_abs_rule(),
        ]
        engine = AlertEngine(rules, min_severity="warning", debounce_seconds=60)
        assert len(engine.rules) == 2

    def test_evaluate_no_alerts(self, sample_snapshot: LiveRunSnapshot) -> None:
        """Test Evaluation ohne Alerts."""
        rules = [
            create_risk_blocked_rule(),
            create_large_loss_abs_rule(),
        ]
        engine = AlertEngine(rules, min_severity="warning", debounce_seconds=60)
        alerts = engine.evaluate_snapshot(sample_snapshot)
        assert len(alerts) == 0

    def test_evaluate_with_alert(self, blocked_snapshot: LiveRunSnapshot) -> None:
        """Test Evaluation mit Alert."""
        rules = [
            create_risk_blocked_rule(),
            create_large_loss_abs_rule(),
        ]
        engine = AlertEngine(rules, min_severity="warning", debounce_seconds=60)
        alerts = engine.evaluate_snapshot(blocked_snapshot)
        assert len(alerts) == 1
        assert alerts[0].rule_id == "risk_blocked"
        assert alerts[0].severity == Severity.CRITICAL

    def test_evaluate_multiple_alerts(self) -> None:
        """Test Evaluation mit mehreren Alerts."""
        # Snapshot mit blocked UND loss
        snapshot = LiveRunSnapshot(
            run_id="test",
            mode="paper",
            strategy_name="test",
            symbol="BTC/EUR",
            timeframe="1m",
            started_at=datetime.now(timezone.utc) - timedelta(hours=1),
            ended_at=None,
            last_bar_time=datetime.now(timezone.utc) - timedelta(minutes=1),
            last_price=40000.0,
            position_size=0.1,
            cash=8000.0,
            equity=8500.0,
            realized_pnl=-600.0,
            unrealized_pnl=0.0,
            total_steps=100,
            total_orders=10,
            total_blocked_orders=2,
        )
        rules = [
            create_risk_blocked_rule(),
            create_large_loss_abs_rule(threshold=-500.0),
        ]
        engine = AlertEngine(rules, min_severity="warning", debounce_seconds=60)
        alerts = engine.evaluate_snapshot(snapshot)
        assert len(alerts) == 2

    def test_severity_filter(self, blocked_snapshot: LiveRunSnapshot) -> None:
        """Test Severity-Filter."""
        rules = [
            create_risk_blocked_rule(),  # critical
        ]
        # Min-Severity auf critical -> Alert sollte durchkommen
        engine = AlertEngine(rules, min_severity="critical", debounce_seconds=60)
        alerts = engine.evaluate_snapshot(blocked_snapshot)
        assert len(alerts) == 1

    def test_debouncing(self, blocked_snapshot: LiveRunSnapshot) -> None:
        """Test Debouncing."""
        rules = [create_risk_blocked_rule()]
        engine = AlertEngine(rules, min_severity="warning", debounce_seconds=60)

        # Erster Aufruf -> Alert
        alerts1 = engine.evaluate_snapshot(blocked_snapshot)
        assert len(alerts1) == 1

        # Zweiter Aufruf (gleicher Run) -> kein Alert (debounced)
        alerts2 = engine.evaluate_snapshot(blocked_snapshot)
        assert len(alerts2) == 0

    def test_debouncing_different_runs(
        self, blocked_snapshot: LiveRunSnapshot
    ) -> None:
        """Test Debouncing für verschiedene Runs."""
        rules = [create_risk_blocked_rule()]
        engine = AlertEngine(rules, min_severity="warning", debounce_seconds=60)

        # Erster Run -> Alert
        alerts1 = engine.evaluate_snapshot(blocked_snapshot)
        assert len(alerts1) == 1

        # Anderer Run -> auch Alert (unterschiedliche run_id)
        other_snapshot = LiveRunSnapshot(
            run_id="other_run",  # Andere Run-ID
            mode="paper",
            strategy_name="test",
            symbol="BTC/EUR",
            timeframe="1m",
            started_at=None,
            ended_at=None,
            last_bar_time=datetime.now(timezone.utc),
            last_price=40000.0,
            position_size=0.1,
            cash=9000.0,
            equity=10000.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            total_steps=100,
            total_orders=10,
            total_blocked_orders=5,
        )
        alerts2 = engine.evaluate_snapshot(other_snapshot)
        assert len(alerts2) == 1

    def test_reset_debounce(self, blocked_snapshot: LiveRunSnapshot) -> None:
        """Test Debounce-Reset."""
        rules = [create_risk_blocked_rule()]
        engine = AlertEngine(rules, min_severity="warning", debounce_seconds=60)

        # Erster Aufruf -> Alert
        alerts1 = engine.evaluate_snapshot(blocked_snapshot)
        assert len(alerts1) == 1

        # Reset Debounce
        engine.reset_debounce()

        # Nochmal -> wieder Alert
        alerts2 = engine.evaluate_snapshot(blocked_snapshot)
        assert len(alerts2) == 1


# =============================================================================
# Alert Logging Tests
# =============================================================================


class TestAlertLogging:
    """Tests für Alert-Logging."""

    def test_append_alerts_to_file(self, temp_run_dir: Path) -> None:
        """Test Alerts in Datei schreiben."""
        alerts = [
            AlertEvent(
                rule_id="test_rule",
                severity="warning",
                message="Test alert",
                run_id="test_run",
                timestamp=datetime.now(timezone.utc),
            )
        ]
        append_alerts_to_file(temp_run_dir, alerts)

        alerts_file = temp_run_dir / "alerts.jsonl"
        assert alerts_file.exists()

        with open(alerts_file, "r") as f:
            lines = f.readlines()
        assert len(lines) == 1

        data = json.loads(lines[0])
        assert data["rule_id"] == "test_rule"

    def test_append_multiple_alerts(self, temp_run_dir: Path) -> None:
        """Test mehrere Alerts anhängen."""
        for i in range(3):
            alerts = [
                AlertEvent(
                    rule_id=f"rule_{i}",
                    severity="warning",
                    message=f"Alert {i}",
                    run_id="test_run",
                    timestamp=datetime.now(timezone.utc),
                )
            ]
            append_alerts_to_file(temp_run_dir, alerts)

        alerts_file = temp_run_dir / "alerts.jsonl"
        with open(alerts_file, "r") as f:
            lines = f.readlines()
        assert len(lines) == 3

    def test_load_alerts_from_file(self, temp_run_dir: Path) -> None:
        """Test Alerts aus Datei laden."""
        # Alerts schreiben
        original_alerts = [
            AlertEvent(
                rule_id="test_rule",
                severity="warning",
                message="Test alert",
                run_id="test_run",
                timestamp=datetime.now(timezone.utc),
            )
        ]
        append_alerts_to_file(temp_run_dir, original_alerts)

        # Alerts laden
        loaded = load_alerts_from_file(temp_run_dir)
        assert len(loaded) == 1
        assert loaded[0].rule_id == "test_rule"
        assert loaded[0].message == "Test alert"

    def test_load_alerts_with_limit(self, temp_run_dir: Path) -> None:
        """Test Alerts laden mit Limit."""
        # 5 Alerts schreiben
        for i in range(5):
            alerts = [
                AlertEvent(
                    rule_id=f"rule_{i}",
                    severity="warning",
                    message=f"Alert {i}",
                    run_id="test_run",
                    timestamp=datetime.now(timezone.utc),
                )
            ]
            append_alerts_to_file(temp_run_dir, alerts)

        # Nur letzte 3 laden
        loaded = load_alerts_from_file(temp_run_dir, limit=3)
        assert len(loaded) == 3

    def test_load_alerts_empty_file(self, temp_run_dir: Path) -> None:
        """Test Laden aus nicht existierender Datei."""
        loaded = load_alerts_from_file(temp_run_dir)
        assert len(loaded) == 0


# =============================================================================
# Factory Tests
# =============================================================================


class TestAlertEngineFactory:
    """Tests für create_alert_engine_from_config."""

    def test_create_from_config_enabled(self) -> None:
        """Test Factory mit aktivierten Alerts."""
        class MockConfig:
            def get(self, path: str, default: Any = None) -> Any:
                values = {
                    "alerts.enabled": True,
                    "alerts.min_severity": "warning",
                    "alerts.debounce_seconds": 60,
                    "alerts.rules.enable_risk_blocked": True,
                    "alerts.rules.enable_large_loss_abs": True,
                    "alerts.rules.large_loss_abs_threshold": -500.0,
                    "alerts.rules.enable_large_loss_pct": True,
                    "alerts.rules.large_loss_pct_threshold": -10.0,
                    "alerts.rules.enable_drawdown": False,
                    "alerts.rules.drawdown_threshold": -15.0,
                }
                return values.get(path, default)

        engine = create_alert_engine_from_config(MockConfig())
        assert engine is not None
        assert len(engine.rules) >= 3  # risk_blocked, loss_abs, loss_pct, no_events

    def test_create_from_config_disabled(self) -> None:
        """Test Factory mit deaktivierten Alerts."""
        class MockConfig:
            def get(self, path: str, default: Any = None) -> Any:
                if path == "alerts.enabled":
                    return False
                return default

        engine = create_alert_engine_from_config(MockConfig())
        assert engine is None


# =============================================================================
# Render Tests
# =============================================================================


class TestRenderAlerts:
    """Tests für render_alerts."""

    def test_render_empty(self) -> None:
        """Test Render ohne Alerts."""
        output = render_alerts([])
        assert output == ""

    def test_render_single_alert(self) -> None:
        """Test Render mit einem Alert."""
        alerts = [
            AlertEvent(
                rule_id="test_rule",
                severity="warning",
                message="Test alert message",
                run_id="test_run",
                timestamp=datetime.now(timezone.utc),
            )
        ]
        output = render_alerts(alerts, use_colors=False)
        assert "ALERTS" in output
        assert "test_rule" in output
        assert "Test alert message" in output

    def test_render_multiple_alerts(self) -> None:
        """Test Render mit mehreren Alerts."""
        alerts = [
            AlertEvent(
                rule_id="rule_1",
                severity="warning",
                message="Warning message",
                run_id="test_run",
                timestamp=datetime.now(timezone.utc),
            ),
            AlertEvent(
                rule_id="rule_2",
                severity="critical",
                message="Critical message",
                run_id="test_run",
                timestamp=datetime.now(timezone.utc),
            ),
        ]
        output = render_alerts(alerts, use_colors=False)
        assert "rule_1" in output
        assert "rule_2" in output
        assert "(2)" in output  # Anzahl
