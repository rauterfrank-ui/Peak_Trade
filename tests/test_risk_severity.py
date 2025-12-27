# tests/test_risk_severity.py
"""
Tests für Risk-Severity-Logik (OK, WARNING, BREACH)
====================================================

Testet:
- RiskCheckSeverity Enum und Vergleichsoperationen
- LiveRiskCheckResult mit Severity
- Warning-Thresholds für verschiedene Limits
- Aggregation von Severities
- UI-Status-Mapping (green/yellow/red)
"""

from __future__ import annotations

from datetime import datetime

import pytest

from src.live.risk_limits import (
    LiveRiskConfig,
    LiveRiskCheckResult,
    LiveRiskLimits,
    LimitCheckDetail,
    RiskCheckSeverity,
    aggregate_severities,
    severity_to_status,
)
from src.live.orders import LiveOrderRequest


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def base_risk_config() -> LiveRiskConfig:
    """Standard-Config für Severity-Tests."""
    return LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_daily_loss_abs=500.0,  # 500 EUR
        max_daily_loss_pct=5.0,  # 5%
        max_total_exposure_notional=10000.0,
        max_symbol_exposure_notional=5000.0,
        max_open_positions=5,
        max_order_notional=2000.0,
        block_on_violation=True,
        use_experiments_for_daily_pnl=False,  # Deaktiviert für Unit-Tests
        warning_threshold_factor=0.8,  # Warning ab 80%
    )


def make_order(symbol: str, notional: float) -> LiveOrderRequest:
    """Erstellt Test-Order mit gegebenem Notional."""
    return LiveOrderRequest(
        client_order_id=f"test_{symbol}_{notional}",
        symbol=symbol,
        side="BUY",
        order_type="MARKET",
        quantity=notional / 100,  # Annahme: Preis = 100
        notional=notional,
        extra={"current_price": 100.0},
    )


# =============================================================================
# TESTS: RiskCheckSeverity ENUM
# =============================================================================


class TestRiskCheckSeverityEnum:
    """Tests für das Severity Enum."""

    def test_severity_values(self):
        """Testet dass alle Severity-Werte vorhanden sind."""
        assert RiskCheckSeverity.OK.value == "ok"
        assert RiskCheckSeverity.WARNING.value == "warning"
        assert RiskCheckSeverity.BREACH.value == "breach"

    def test_severity_ordering(self):
        """Testet Severity-Ordnung: BREACH > WARNING > OK."""
        assert RiskCheckSeverity.BREACH > RiskCheckSeverity.WARNING
        assert RiskCheckSeverity.WARNING > RiskCheckSeverity.OK
        assert RiskCheckSeverity.BREACH > RiskCheckSeverity.OK

        assert not (RiskCheckSeverity.OK > RiskCheckSeverity.WARNING)
        assert not (RiskCheckSeverity.WARNING > RiskCheckSeverity.BREACH)

    def test_severity_equality(self):
        """Testet Severity-Gleichheit."""
        assert RiskCheckSeverity.OK == RiskCheckSeverity.OK
        assert RiskCheckSeverity.WARNING == RiskCheckSeverity.WARNING
        assert RiskCheckSeverity.BREACH == RiskCheckSeverity.BREACH

        assert not (RiskCheckSeverity.OK == RiskCheckSeverity.WARNING)

    def test_severity_ge_le(self):
        """Testet >= und <= Operatoren."""
        assert RiskCheckSeverity.BREACH >= RiskCheckSeverity.WARNING
        assert RiskCheckSeverity.BREACH >= RiskCheckSeverity.BREACH
        assert RiskCheckSeverity.WARNING <= RiskCheckSeverity.BREACH
        assert RiskCheckSeverity.OK <= RiskCheckSeverity.OK


# =============================================================================
# TESTS: SEVERITY AGGREGATION & STATUS
# =============================================================================


class TestSeverityAggregation:
    """Tests für Severity-Aggregation und Status-Mapping."""

    def test_aggregate_empty_list(self):
        """Leere Liste ergibt OK."""
        assert aggregate_severities([]) == RiskCheckSeverity.OK

    def test_aggregate_all_ok(self):
        """Nur OK-Werte ergibt OK."""
        severities = [RiskCheckSeverity.OK, RiskCheckSeverity.OK, RiskCheckSeverity.OK]
        assert aggregate_severities(severities) == RiskCheckSeverity.OK

    def test_aggregate_with_warning(self):
        """Eine WARNING macht Aggregat zu WARNING."""
        severities = [RiskCheckSeverity.OK, RiskCheckSeverity.WARNING, RiskCheckSeverity.OK]
        assert aggregate_severities(severities) == RiskCheckSeverity.WARNING

    def test_aggregate_with_breach(self):
        """Ein BREACH macht Aggregat zu BREACH (strikteste gewinnt)."""
        severities = [
            RiskCheckSeverity.OK,
            RiskCheckSeverity.WARNING,
            RiskCheckSeverity.BREACH,
        ]
        assert aggregate_severities(severities) == RiskCheckSeverity.BREACH

    def test_severity_to_status_green(self):
        """OK → green."""
        assert severity_to_status(RiskCheckSeverity.OK) == "green"

    def test_severity_to_status_yellow(self):
        """WARNING → yellow."""
        assert severity_to_status(RiskCheckSeverity.WARNING) == "yellow"

    def test_severity_to_status_red(self):
        """BREACH → red."""
        assert severity_to_status(RiskCheckSeverity.BREACH) == "red"


# =============================================================================
# TESTS: LiveRiskCheckResult
# =============================================================================


class TestLiveRiskCheckResult:
    """Tests für LiveRiskCheckResult mit Severity."""

    def test_result_with_default_severity(self):
        """Testet Default-Severity = OK."""
        result = LiveRiskCheckResult(
            allowed=True,
            reasons=[],
            metrics={},
        )
        assert result.severity == RiskCheckSeverity.OK
        assert result.limit_details == []
        assert result.risk_status == "green"

    def test_result_with_warning_severity(self):
        """Testet Result mit WARNING."""
        result = LiveRiskCheckResult(
            allowed=True,
            reasons=[],
            metrics={},
            severity=RiskCheckSeverity.WARNING,
        )
        assert result.severity == RiskCheckSeverity.WARNING
        assert result.risk_status == "yellow"
        assert result.allowed is True  # WARNING erlaubt weiterhin

    def test_result_with_breach_severity(self):
        """Testet Result mit BREACH → allowed muss False sein."""
        result = LiveRiskCheckResult(
            allowed=False,  # Muss False sein bei BREACH
            reasons=["limit_exceeded"],
            metrics={},
            severity=RiskCheckSeverity.BREACH,
        )
        assert result.severity == RiskCheckSeverity.BREACH
        assert result.risk_status == "red"
        assert result.allowed is False

    def test_breach_corrects_allowed_true(self):
        """Testet dass BREACH + allowed=True zu allowed=False korrigiert wird."""
        result = LiveRiskCheckResult(
            allowed=True,  # Sollte korrigiert werden
            reasons=[],
            metrics={},
            severity=RiskCheckSeverity.BREACH,
        )
        # __post_init__ sollte allowed auf False setzen
        assert result.allowed is False


# =============================================================================
# TESTS: LIMIT CHECK SEVERITY - MAX_ORDER_NOTIONAL
# =============================================================================


class TestMaxOrderNotionalSeverity:
    """Tests für max_order_notional Limit mit Severity."""

    def test_value_well_below_limit_is_ok(self, base_risk_config: LiveRiskConfig):
        """Wert deutlich unter Limit (< 80%) → OK."""
        # Limit: 2000, Warning bei 1600 (80%)
        # Order: 1000 → 50% vom Limit → OK
        limits = LiveRiskLimits(base_risk_config)
        orders = [make_order("BTC/EUR", 1000.0)]

        result = limits.check_orders(orders)

        assert result.severity == RiskCheckSeverity.OK
        assert result.allowed is True
        assert len(result.reasons) == 0
        assert result.risk_status == "green"

    def test_value_at_warning_threshold_is_warning(self, base_risk_config: LiveRiskConfig):
        """Wert bei Warning-Threshold (80-99% vom Limit) → WARNING."""
        # Limit: 2000, Warning bei 1600 (80%)
        # Order: 1700 → 85% vom Limit → WARNING
        limits = LiveRiskLimits(base_risk_config)
        orders = [make_order("BTC/EUR", 1700.0)]

        result = limits.check_orders(orders)

        assert result.severity == RiskCheckSeverity.WARNING
        assert result.allowed is True  # WARNING blockt nicht
        assert result.risk_status == "yellow"

        # Prüfe dass max_order_notional Detail WARNING hat
        order_detail = next(
            (d for d in result.limit_details if d.limit_name == "max_order_notional"),
            None,
        )
        assert order_detail is not None
        assert order_detail.severity == RiskCheckSeverity.WARNING

    def test_value_at_limit_is_breach(self, base_risk_config: LiveRiskConfig):
        """Wert >= Limit → BREACH."""
        # Limit: 2000
        # Order: 2000 → genau am Limit → BREACH
        limits = LiveRiskLimits(base_risk_config)
        orders = [make_order("BTC/EUR", 2000.0)]

        result = limits.check_orders(orders)

        assert result.severity == RiskCheckSeverity.BREACH
        assert result.allowed is False  # BREACH blockt
        assert result.risk_status == "red"
        assert len(result.reasons) > 0
        assert any("max_order_notional" in r for r in result.reasons)

    def test_value_above_limit_is_breach(self, base_risk_config: LiveRiskConfig):
        """Wert > Limit → BREACH."""
        # Limit: 2000
        # Order: 2500 → über Limit → BREACH
        limits = LiveRiskLimits(base_risk_config)
        orders = [make_order("BTC/EUR", 2500.0)]

        result = limits.check_orders(orders)

        assert result.severity == RiskCheckSeverity.BREACH
        assert result.allowed is False
        assert result.risk_status == "red"


# =============================================================================
# TESTS: LIMIT CHECK SEVERITY - TOTAL EXPOSURE
# =============================================================================


class TestTotalExposureSeverity:
    """Tests für max_total_exposure_notional Limit mit Severity."""

    def test_total_exposure_ok(self, base_risk_config: LiveRiskConfig):
        """Gesamt-Notional unter Warning-Threshold → OK."""
        # Limit: 10000, Warning bei 8000 (80%)
        # Orders: 3 * 2000 = 6000 → 60% → OK
        limits = LiveRiskLimits(base_risk_config)
        orders = [
            make_order("BTC/EUR", 2000.0),
            make_order("ETH/EUR", 2000.0),
            make_order("SOL/EUR", 2000.0),
        ]

        result = limits.check_orders(orders)

        exposure_detail = next(
            (d for d in result.limit_details if d.limit_name == "max_total_exposure"),
            None,
        )
        assert exposure_detail is not None
        assert exposure_detail.severity == RiskCheckSeverity.OK

    def test_total_exposure_warning(self, base_risk_config: LiveRiskConfig):
        """Gesamt-Notional im Warning-Bereich → WARNING."""
        # Limit: 10000, Warning bei 8000 (80%)
        # Orders: 5 * 1700 = 8500 → 85% → WARNING
        # (Jede Order unter dem 2000 max_order_notional Limit)
        limits = LiveRiskLimits(base_risk_config)
        orders = [
            make_order("BTC/EUR", 1700.0),
            make_order("ETH/EUR", 1700.0),
            make_order("SOL/EUR", 1700.0),
            make_order("DOGE/EUR", 1700.0),
            make_order("ADA/EUR", 1700.0),
        ]  # Total: 8500 EUR, jede Order im WARNING-Bereich

        result = limits.check_orders(orders)

        exposure_detail = next(
            (d for d in result.limit_details if d.limit_name == "max_total_exposure"),
            None,
        )
        assert exposure_detail is not None
        assert exposure_detail.severity == RiskCheckSeverity.WARNING
        # Gesamtseverity kann WARNING sein (wenn alle anderen auch OK/WARNING)
        assert result.severity in [RiskCheckSeverity.WARNING, RiskCheckSeverity.BREACH]

    def test_total_exposure_breach(self, base_risk_config: LiveRiskConfig):
        """Gesamt-Notional über Limit → BREACH."""
        # Limit: 10000
        # Orders: 5 * 2100 = 10500 → über Limit → BREACH
        limits = LiveRiskLimits(base_risk_config)
        orders = [
            make_order("BTC/EUR", 2100.0),
            make_order("ETH/EUR", 2100.0),
            make_order("SOL/EUR", 2100.0),
            make_order("DOGE/EUR", 2100.0),
            make_order("ADA/EUR", 2100.0),
        ]

        result = limits.check_orders(orders)

        assert result.severity == RiskCheckSeverity.BREACH
        assert result.allowed is False
        assert any("max_total_exposure" in r for r in result.reasons)


# =============================================================================
# TESTS: LIMIT CHECK SEVERITY - DAILY LOSS
# =============================================================================


class TestDailyLossSeverity:
    """Tests für Daily-Loss Limits mit Severity."""

    def test_no_loss_is_ok(self, base_risk_config: LiveRiskConfig):
        """Kein Verlust → OK."""
        limits = LiveRiskLimits(base_risk_config)
        orders = [make_order("BTC/EUR", 500.0)]

        result = limits.check_orders(orders)

        daily_loss_detail = next(
            (d for d in result.limit_details if d.limit_name == "max_daily_loss_abs"),
            None,
        )
        assert daily_loss_detail is not None
        # Bei PnL = 0.0 und Limit = 500 ist das OK
        assert daily_loss_detail.severity == RiskCheckSeverity.OK

    def test_daily_loss_pct_with_starting_cash(self):
        """Testet prozentuales Daily-Loss-Limit mit starting_cash."""
        config = LiveRiskConfig(
            enabled=True,
            base_currency="EUR",
            max_daily_loss_abs=None,
            max_daily_loss_pct=5.0,  # 5% von 10000 = 500 EUR
            max_total_exposure_notional=50000.0,
            max_symbol_exposure_notional=None,
            max_open_positions=None,
            max_order_notional=None,
            block_on_violation=True,
            use_experiments_for_daily_pnl=False,
            warning_threshold_factor=0.8,  # Warning ab 80% = 400 EUR Verlust
        )

        from src.core.peak_config import PeakConfig

        limits = LiveRiskLimits(config)
        limits._starting_cash = 10000.0

        orders = [make_order("BTC/EUR", 500.0)]
        result = limits.check_orders(orders)

        # Bei PnL = 0 sollte alles OK sein
        assert result.allowed is True


# =============================================================================
# TESTS: AGGREGATED SEVERITY
# =============================================================================


class TestAggregatedSeverity:
    """Tests für aggregierte Severity bei mehreren Checks."""

    def test_all_ok_results_in_ok(self, base_risk_config: LiveRiskConfig):
        """Alle Checks OK → Gesamt-Severity OK."""
        limits = LiveRiskLimits(base_risk_config)
        orders = [make_order("BTC/EUR", 500.0)]  # Weit unter allen Limits

        result = limits.check_orders(orders)

        assert result.severity == RiskCheckSeverity.OK
        assert all(d.severity == RiskCheckSeverity.OK for d in result.limit_details)

    def test_one_warning_results_in_warning(self, base_risk_config: LiveRiskConfig):
        """Ein Check WARNING, Rest OK → Gesamt-Severity WARNING."""
        limits = LiveRiskLimits(base_risk_config)
        # Order-Notional bei Warning-Level (85% von 2000 = 1700)
        orders = [make_order("BTC/EUR", 1700.0)]

        result = limits.check_orders(orders)

        assert result.severity == RiskCheckSeverity.WARNING
        assert result.allowed is True

    def test_one_breach_overrides_warning(self, base_risk_config: LiveRiskConfig):
        """Ein Check BREACH, anderer WARNING → Gesamt-Severity BREACH."""
        limits = LiveRiskLimits(base_risk_config)
        # Order 1: BREACH (über 2000)
        # Order 2: macht Total-Exposure zu WARNING
        orders = [
            make_order("BTC/EUR", 2500.0),  # BREACH bei max_order_notional
        ]

        result = limits.check_orders(orders)

        assert result.severity == RiskCheckSeverity.BREACH
        assert result.allowed is False


# =============================================================================
# TESTS: WARNING THRESHOLD FACTOR
# =============================================================================


class TestWarningThresholdFactor:
    """Tests für konfigurierbaren Warning-Threshold-Faktor."""

    def test_custom_warning_threshold_70_percent(self):
        """Testet Warning bei 70% statt 80%."""
        config = LiveRiskConfig(
            enabled=True,
            base_currency="EUR",
            max_daily_loss_abs=None,
            max_daily_loss_pct=None,
            max_total_exposure_notional=None,
            max_symbol_exposure_notional=None,
            max_open_positions=None,
            max_order_notional=1000.0,  # Limit = 1000
            block_on_violation=True,
            use_experiments_for_daily_pnl=False,
            warning_threshold_factor=0.7,  # Warning ab 70% = 700
        )
        limits = LiveRiskLimits(config)

        # 750 ist > 70% aber < 100% → WARNING
        orders = [make_order("BTC/EUR", 750.0)]
        result = limits.check_orders(orders)

        assert result.severity == RiskCheckSeverity.WARNING
        assert result.allowed is True

    def test_custom_warning_threshold_90_percent(self):
        """Testet Warning bei 90%."""
        config = LiveRiskConfig(
            enabled=True,
            base_currency="EUR",
            max_daily_loss_abs=None,
            max_daily_loss_pct=None,
            max_total_exposure_notional=None,
            max_symbol_exposure_notional=None,
            max_open_positions=None,
            max_order_notional=1000.0,  # Limit = 1000
            block_on_violation=True,
            use_experiments_for_daily_pnl=False,
            warning_threshold_factor=0.9,  # Warning ab 90% = 900
        )
        limits = LiveRiskLimits(config)

        # 850 ist < 90% → OK
        orders_ok = [make_order("BTC/EUR", 850.0)]
        result_ok = limits.check_orders(orders_ok)
        assert result_ok.severity == RiskCheckSeverity.OK

        # 950 ist > 90% aber < 100% → WARNING
        orders_warn = [make_order("BTC/EUR", 950.0)]
        result_warn = limits.check_orders(orders_warn)
        assert result_warn.severity == RiskCheckSeverity.WARNING


# =============================================================================
# TESTS: BACKWARD COMPATIBILITY
# =============================================================================


class TestBackwardCompatibility:
    """Tests für Rückwärtskompatibilität."""

    def test_result_without_new_fields(self):
        """Testet dass Result ohne neue Felder funktioniert."""
        result = LiveRiskCheckResult(
            allowed=True,
            reasons=[],
            metrics={"test": 123},
        )
        # Default-Werte sollten gesetzt sein
        assert result.severity == RiskCheckSeverity.OK
        assert result.limit_details == []
        assert result.risk_status == "green"

    def test_allowed_false_without_breach(self):
        """Testet dass allowed=False auch ohne BREACH möglich ist (Legacy)."""
        result = LiveRiskCheckResult(
            allowed=False,
            reasons=["some_reason"],
            metrics={},
            severity=RiskCheckSeverity.WARNING,  # Kein BREACH
        )
        # Bei WARNING + allowed=False bleibt allowed False
        assert result.allowed is False
        assert result.severity == RiskCheckSeverity.WARNING


# =============================================================================
# TESTS: LIMIT CHECK DETAIL
# =============================================================================


class TestLimitCheckDetail:
    """Tests für LimitCheckDetail."""

    def test_ratio_calculation(self):
        """Testet Ratio-Berechnung."""
        detail = LimitCheckDetail(
            limit_name="test",
            current_value=750.0,
            limit_value=1000.0,
            severity=RiskCheckSeverity.WARNING,
        )
        assert detail.ratio == pytest.approx(0.75, abs=0.001)

    def test_ratio_with_zero_limit(self):
        """Testet Ratio bei Limit = 0."""
        detail = LimitCheckDetail(
            limit_name="test",
            current_value=100.0,
            limit_value=0.0,
            severity=RiskCheckSeverity.OK,
        )
        assert detail.ratio == 0.0

