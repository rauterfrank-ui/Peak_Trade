# tests/test_position_size_limits.py
"""
Tests für Position Size Limits (Issue #20 / D1-2).

Testet die harten Position-Size-Limits im Live-Risk-System:
- max_units_per_order: Maximale Einheiten pro Order
- max_notional_per_order: Maximales Notional pro Order
- per_symbol_max_units: Symbol-spezifische Limits
- allow_clip_position_size: Clippen vs. Reject Policy

WICHTIG: Diese Tests sind deterministisch und haben keine externen Dependencies.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from src.live.risk_limits import (
    LiveRiskLimits,
    LiveRiskConfig,
    RiskCheckSeverity,
)
from src.live.orders import LiveOrderRequest
from src.core.peak_config import PeakConfig


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def base_config() -> LiveRiskConfig:
    """Basis-Konfiguration ohne Position-Size-Limits."""
    return LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        max_total_exposure_notional=None,
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=False,
        warning_threshold_factor=0.8,
    )


@pytest.fixture
def config_with_units_limit() -> LiveRiskConfig:
    """Konfiguration mit max_units_per_order Limit."""
    return LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        max_total_exposure_notional=None,
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=False,
        max_units_per_order=1.0,  # Max 1.0 Einheiten pro Order
        allow_clip_position_size=False,  # REJECT bei Breach
        warning_threshold_factor=0.8,
    )


@pytest.fixture
def config_with_notional_limit() -> LiveRiskConfig:
    """Konfiguration mit max_notional_per_order Limit."""
    return LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        max_total_exposure_notional=None,
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=False,
        max_notional_per_order=50000.0,  # Max 50k EUR pro Order
        allow_clip_position_size=False,
        warning_threshold_factor=0.8,
    )


@pytest.fixture
def config_with_symbol_limits() -> LiveRiskConfig:
    """Konfiguration mit per-symbol max_units."""
    return LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        max_total_exposure_notional=None,
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=False,
        per_symbol_max_units={
            "BTC/EUR": 0.5,  # Max 0.5 BTC
            "ETH/EUR": 5.0,  # Max 5.0 ETH
        },
        allow_clip_position_size=False,
        warning_threshold_factor=0.8,
    )


@pytest.fixture
def config_with_clip_enabled() -> LiveRiskConfig:
    """Konfiguration mit allow_clip_position_size=True."""
    return LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        max_total_exposure_notional=None,
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=False,
        max_units_per_order=1.0,
        allow_clip_position_size=True,  # Clippen statt Reject
        warning_threshold_factor=0.8,
    )


# =============================================================================
# Test: max_units_per_order - Within Limits
# =============================================================================


def test_position_size_within_units_limit(config_with_units_limit: LiveRiskConfig):
    """
    Test: Order innerhalb des max_units_per_order Limits wird erlaubt.

    Gegeben: max_units_per_order = 1.0
    Wenn: Order mit quantity = 0.5 BTC
    Dann: allowed = True, severity = OK
    """
    limits = LiveRiskLimits(config_with_units_limit)

    order = LiveOrderRequest(
        client_order_id="test_001",
        symbol="BTC/EUR",
        side="BUY",
        order_type="MARKET",
        quantity=0.5,  # Innerhalb Limit (1.0)
        extra={"current_price": 50000.0},
    )

    result = limits.check_orders([order])

    assert result.allowed is True
    assert result.severity == RiskCheckSeverity.OK
    assert len(result.reasons) == 0


# =============================================================================
# Test: max_units_per_order - Breach (REJECT)
# =============================================================================


def test_position_size_units_breach_reject(config_with_units_limit: LiveRiskConfig):
    """
    Test: Order über max_units_per_order Limit wird rejected.

    Gegeben: max_units_per_order = 1.0, allow_clip = False
    Wenn: Order mit quantity = 1.5 BTC
    Dann: allowed = False, severity = BREACH, reason enthält 'max_units_per_order'
    """
    limits = LiveRiskLimits(config_with_units_limit)

    order = LiveOrderRequest(
        client_order_id="test_002",
        symbol="BTC/EUR",
        side="BUY",
        order_type="MARKET",
        quantity=1.5,  # Über Limit (1.0)
        extra={"current_price": 50000.0},
    )

    result = limits.check_orders([order])

    assert result.allowed is False
    assert result.severity == RiskCheckSeverity.BREACH
    assert any("max_units_per_order" in r for r in result.reasons)


# =============================================================================
# Test: max_notional_per_order - Breach
# =============================================================================


def test_position_size_notional_breach(config_with_notional_limit: LiveRiskConfig):
    """
    Test: Order über max_notional_per_order Limit wird rejected.

    Gegeben: max_notional_per_order = 50000 EUR
    Wenn: Order mit notional = 60000 EUR (1.2 BTC @ 50k)
    Dann: allowed = False, severity = BREACH
    """
    limits = LiveRiskLimits(config_with_notional_limit)

    order = LiveOrderRequest(
        client_order_id="test_003",
        symbol="BTC/EUR",
        side="BUY",
        order_type="MARKET",
        quantity=1.2,  # 1.2 BTC @ 50k = 60k EUR
        extra={"current_price": 50000.0},
    )

    result = limits.check_orders([order])

    assert result.allowed is False
    assert result.severity == RiskCheckSeverity.BREACH
    assert any("max_notional_per_order" in r for r in result.reasons)


# =============================================================================
# Test: per_symbol_max_units - Within Limits
# =============================================================================


def test_position_size_per_symbol_within_limit(config_with_symbol_limits: LiveRiskConfig):
    """
    Test: Order innerhalb des per-symbol Limits wird erlaubt.

    Gegeben: per_symbol_max_units["BTC/EUR"] = 0.5
    Wenn: Order mit quantity = 0.3 BTC
    Dann: allowed = True, severity = OK
    """
    limits = LiveRiskLimits(config_with_symbol_limits)

    order = LiveOrderRequest(
        client_order_id="test_004",
        symbol="BTC/EUR",
        side="BUY",
        order_type="MARKET",
        quantity=0.3,  # Innerhalb Limit (0.5)
        extra={"current_price": 50000.0},
    )

    result = limits.check_orders([order])

    assert result.allowed is True
    assert result.severity == RiskCheckSeverity.OK


# =============================================================================
# Test: per_symbol_max_units - Breach
# =============================================================================


def test_position_size_per_symbol_breach(config_with_symbol_limits: LiveRiskConfig):
    """
    Test: Order über per-symbol Limit wird rejected.

    Gegeben: per_symbol_max_units["BTC/EUR"] = 0.5
    Wenn: Order mit quantity = 0.8 BTC
    Dann: allowed = False, severity = BREACH
    """
    limits = LiveRiskLimits(config_with_symbol_limits)

    order = LiveOrderRequest(
        client_order_id="test_005",
        symbol="BTC/EUR",
        side="BUY",
        order_type="MARKET",
        quantity=0.8,  # Über Limit (0.5)
        extra={"current_price": 50000.0},
    )

    result = limits.check_orders([order])

    assert result.allowed is False
    assert result.severity == RiskCheckSeverity.BREACH
    assert any("per_symbol_max_units" in r for r in result.reasons)


# =============================================================================
# Test: allow_clip_position_size = True
# =============================================================================


def test_position_size_clip_enabled_logs_warning(
    config_with_clip_enabled: LiveRiskConfig, caplog
):
    """
    Test: Mit allow_clip_position_size=True wird Warnung geloggt.

    Gegeben: max_units_per_order = 1.0, allow_clip = True
    Wenn: Order mit quantity = 1.5 BTC (breach)
    Dann: Log-Warnung mit "[POSITION SIZE CLIP]"
          allowed = True (clippen erlaubt, aber check erkennt breach)

    WICHTIG: In dieser Implementierung wird nur geloggt, aber allowed=True.
             Die tatsächliche Order-Modifikation würde im Executor passieren.
    """
    limits = LiveRiskLimits(config_with_clip_enabled)

    order = LiveOrderRequest(
        client_order_id="test_006",
        symbol="BTC/EUR",
        side="BUY",
        order_type="MARKET",
        quantity=1.5,  # Über Limit (1.0)
        extra={"current_price": 50000.0},
    )

    with caplog.at_level("WARNING"):
        result = limits.check_orders([order])

    # Mit allow_clip = True wird die Order NICHT rejected
    # Stattdessen wird nur gewarnt und später würde Order geclippt
    assert "[POSITION SIZE CLIP]" in caplog.text
    assert "units clipped: 1.500000 -> 1.000000" in caplog.text


# =============================================================================
# Test: Multiple Orders - Mixed Results
# =============================================================================


def test_position_size_multiple_orders_mixed(config_with_units_limit: LiveRiskConfig):
    """
    Test: Mehrere Orders, eine davon verletzt Limit.

    Gegeben: max_units_per_order = 1.0
    Wenn: 3 Orders, davon eine mit quantity = 1.5 BTC
    Dann: allowed = False (wegen einer Breach), severity = BREACH
    """
    limits = LiveRiskLimits(config_with_units_limit)

    orders = [
        LiveOrderRequest(
            client_order_id="test_007a",
            symbol="BTC/EUR",
            side="BUY",
            quantity=0.5,  # OK
            extra={"current_price": 50000.0},
        ),
        LiveOrderRequest(
            client_order_id="test_007b",
            symbol="ETH/EUR",
            side="BUY",
            quantity=1.5,  # BREACH
            extra={"current_price": 3000.0},
        ),
        LiveOrderRequest(
            client_order_id="test_007c",
            symbol="BTC/EUR",
            side="SELL",
            quantity=0.3,  # OK
            extra={"current_price": 50000.0},
        ),
    ]

    result = limits.check_orders(orders)

    assert result.allowed is False
    assert result.severity == RiskCheckSeverity.BREACH
    assert len(result.reasons) >= 1


# =============================================================================
# Test: Config Integration - from_config()
# =============================================================================


def test_position_size_limits_from_config():
    """
    Test: Position Size Limits werden korrekt aus PeakConfig geladen.

    Testet das Parsen der Config-Werte:
    - max_units_per_order
    - max_notional_per_order
    - allow_clip_position_size
    - per_symbol_max_units
    """
    config_dict = {
        "live_risk": {
            "enabled": True,
            "base_currency": "EUR",
            "max_units_per_order": 1.0,
            "max_notional_per_order": 50000.0,
            "allow_clip_position_size": False,
            "block_on_violation": True,
            "use_experiments_for_daily_pnl": False,
        }
    }

    cfg = PeakConfig(config_dict)
    limits = LiveRiskLimits.from_config(cfg)

    assert limits.config.max_units_per_order == 1.0
    assert limits.config.max_notional_per_order == 50000.0
    assert limits.config.allow_clip_position_size is False


# =============================================================================
# Test: Deterministische Ausführung (keine externen Dependencies)
# =============================================================================


def test_position_size_deterministic_no_external_deps(config_with_units_limit: LiveRiskConfig):
    """
    Test: Risk-Check ist deterministisch und hat keine externen Dependencies.

    Gegeben: LiveRiskLimits mit max_units_per_order = 1.0
    Wenn: Gleiche Order 3x geprüft wird
    Dann: Identisches Ergebnis jedes Mal
    """
    limits = LiveRiskLimits(config_with_units_limit)

    order = LiveOrderRequest(
        client_order_id="test_008",
        symbol="BTC/EUR",
        side="BUY",
        quantity=1.5,
        extra={"current_price": 50000.0},
    )

    results = [limits.check_orders([order]) for _ in range(3)]

    # Alle Ergebnisse müssen identisch sein
    assert all(r.allowed == results[0].allowed for r in results)
    assert all(r.severity == results[0].severity for r in results)
    assert all(len(r.reasons) == len(results[0].reasons) for r in results)


# =============================================================================
# Test: Structured Logging - Metrics in Result
# =============================================================================


def test_position_size_metrics_in_result(config_with_units_limit: LiveRiskConfig):
    """
    Test: LiveRiskCheckResult enthält strukturierte Metriken.

    Gegeben: max_units_per_order = 1.0
    Wenn: Order mit quantity = 0.5 BTC
    Dann: result.metrics enthält relevante Keys
    """
    limits = LiveRiskLimits(config_with_units_limit)

    order = LiveOrderRequest(
        client_order_id="test_009",
        symbol="BTC/EUR",
        side="BUY",
        quantity=0.5,
        extra={"current_price": 50000.0},
    )

    result = limits.check_orders([order])

    # Strukturierte Metriken vorhanden
    assert "n_orders" in result.metrics
    assert "n_symbols" in result.metrics
    assert "base_currency" in result.metrics
    assert result.metrics["n_orders"] == 1
    assert result.metrics["n_symbols"] == 1


# =============================================================================
# Test: Warning Threshold
# =============================================================================


def test_position_size_warning_threshold(config_with_units_limit: LiveRiskConfig):
    """
    Test: WARNING wird bei 80%-90% des Limits ausgelöst.

    Gegeben: max_units_per_order = 1.0, warning_threshold_factor = 0.8
    Wenn: Order mit quantity = 0.85 BTC (85% des Limits)
    Dann: severity = WARNING, allowed = True
    """
    limits = LiveRiskLimits(config_with_units_limit)

    order = LiveOrderRequest(
        client_order_id="test_010",
        symbol="BTC/EUR",
        side="BUY",
        quantity=0.85,  # 85% des Limits (1.0)
        extra={"current_price": 50000.0},
    )

    result = limits.check_orders([order])

    assert result.allowed is True
    assert result.severity == RiskCheckSeverity.WARNING


# =============================================================================
# Test: Disabled Limits (enabled = False)
# =============================================================================


def test_position_size_limits_disabled():
    """
    Test: Mit enabled=False werden keine Limits geprüft.

    Gegeben: enabled = False
    Wenn: Order mit beliebiger quantity
    Dann: allowed = True, severity = OK
    """
    config = LiveRiskConfig(
        enabled=False,  # Limits deaktiviert
        base_currency="EUR",
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        max_total_exposure_notional=None,
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=False,
        max_units_per_order=1.0,
        allow_clip_position_size=False,
        warning_threshold_factor=0.8,
    )

    limits = LiveRiskLimits(config)

    order = LiveOrderRequest(
        client_order_id="test_011",
        symbol="BTC/EUR",
        side="BUY",
        quantity=999.0,  # Extrem hoch, aber limits disabled
        extra={"current_price": 50000.0},
    )

    result = limits.check_orders([order])

    assert result.allowed is True
    assert result.severity == RiskCheckSeverity.OK


# =============================================================================
# Test: LimitCheckDetail - Ratio Calculation
# =============================================================================


def test_position_size_limit_detail_ratio():
    """
    Test: LimitCheckDetail berechnet ratio korrekt.

    Gegeben: max_units_per_order = 1.0
    Wenn: Order mit quantity = 0.85 BTC
    Dann: detail.ratio = 0.85
    """
    config = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        max_total_exposure_notional=None,
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=False,
        max_units_per_order=1.0,
        allow_clip_position_size=False,
        warning_threshold_factor=0.8,
    )

    limits = LiveRiskLimits(config)

    order = LiveOrderRequest(
        client_order_id="test_012",
        symbol="BTC/EUR",
        side="BUY",
        quantity=0.85,
        extra={"current_price": 50000.0},
    )

    result = limits.check_orders([order])

    # Finde das relevante LimitCheckDetail
    unit_details = [d for d in result.limit_details if "max_units_per_order" in d.limit_name]
    assert len(unit_details) > 0

    detail = unit_details[0]
    assert abs(detail.ratio - 0.85) < 0.01  # Ratio ≈ 0.85
