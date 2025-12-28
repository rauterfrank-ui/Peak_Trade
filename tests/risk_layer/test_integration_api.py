"""
Integration API Smoke Tests
=============================

Stellt sicher dass die Public API korrekt funktioniert.
"""

import pytest


def test_import_core_types():
    """Test dass Core Types aus models.py importierbar sind."""
    from src.risk_layer.models import RiskDecision, RiskResult, Violation

    # Sollte keine ImportError werfen
    assert RiskDecision is not None
    assert RiskResult is not None
    assert Violation is not None


def test_import_new_types():
    """Test dass neue Types importierbar sind."""
    from src.risk_layer.types import RiskLayerResult

    assert RiskLayerResult is not None


def test_import_var_backtest():
    """Test dass VaR Backtest API importierbar ist."""
    from src.risk_layer.var_backtest import KupiecPOFOutput, KupiecResult, kupiec_pof_test

    assert kupiec_pof_test is not None
    assert KupiecPOFOutput is not None
    assert KupiecResult is not None


def test_import_attribution_types():
    """Test dass Attribution Types importierbar sind."""
    from src.risk_layer.types import ComponentVaR, PnLAttribution, VaRDecomposition

    assert ComponentVaR is not None
    assert VaRDecomposition is not None
    assert PnLAttribution is not None


def test_import_stress_types():
    """Test dass Stress Testing Types importierbar sind."""
    from src.risk_layer.types import (
        ForwardStressResult,
        ReverseStressResult,
        StressScenario,
    )

    assert StressScenario is not None
    assert ReverseStressResult is not None
    assert ForwardStressResult is not None


def test_import_kill_switch():
    """Test dass Kill Switch importierbar ist."""
    from src.risk_layer.kill_switch import ExecutionGate, KillSwitch, KillSwitchState

    assert KillSwitch is not None
    assert KillSwitchState is not None
    assert ExecutionGate is not None


def test_import_exceptions():
    """Test dass Exceptions importierbar sind."""
    from src.risk_layer.exceptions import (
        RiskLayerError,
        TradingBlockedError,
        ValidationError,
    )

    assert RiskLayerError is not None
    assert ValidationError is not None
    assert TradingBlockedError is not None


def test_risk_layer_result_creation():
    """Test RiskLayerResult creation."""
    from src.risk_layer.types import RiskLayerResult

    result = RiskLayerResult(
        var=1000.0,
        cvar=1500.0,
        kill_switch_active=False,
    )

    assert result.var == 1000.0
    assert result.cvar == 1500.0
    assert result.kill_switch_active is False
    assert result.timestamp is not None

    summary = result.summary()
    assert summary["var"] == 1000.0
    assert summary["kill_switch_active"] is False


def test_integration_adapter_creation():
    """Test RiskLayerAdapter creation."""
    from src.risk_layer.integration import RiskLayerAdapter

    config = {}  # Empty config
    adapter = RiskLayerAdapter(config)

    # Trading sollte erlaubt sein (kein Kill Switch)
    assert adapter.check_trading_allowed() is True

    # Kill Switch sollte None sein (nicht konfiguriert)
    assert adapter.kill_switch is None


def test_component_var_diversification_benefit():
    """Test ComponentVaR diversification_benefit property."""
    from src.risk_layer.types import ComponentVaR

    comp = ComponentVaR(
        asset="BTC-EUR",
        weight=0.6,
        marginal_var=100.0,
        component_var=60.0,
        incremental_var=80.0,
        percent_contribution=0.5,
    )

    # Diversification Benefit = Incremental - Component
    assert comp.diversification_benefit == 20.0


def test_var_decomposition_to_dataframe():
    """Test VaRDecomposition to_dataframe conversion."""
    from src.risk_layer.types import ComponentVaR, VaRDecomposition

    comp1 = ComponentVaR(
        asset="BTC-EUR",
        weight=0.6,
        marginal_var=100.0,
        component_var=60.0,
        incremental_var=80.0,
        percent_contribution=0.6,
    )

    comp2 = ComponentVaR(
        asset="ETH-EUR",
        weight=0.4,
        marginal_var=100.0,
        component_var=40.0,
        incremental_var=50.0,
        percent_contribution=0.4,
    )

    decomp = VaRDecomposition(
        portfolio_var=100.0, components={"BTC-EUR": comp1, "ETH-EUR": comp2}, diversification_ratio=1.3
    )

    df = decomp.to_dataframe()

    assert len(df) == 2
    assert "asset" in df.columns
    assert "component_var" in df.columns
    assert df["asset"].tolist() == ["BTC-EUR", "ETH-EUR"]


def test_pnl_attribution_to_dataframe():
    """Test PnLAttribution to_dataframe conversion."""
    from src.risk_layer.types import PnLAttribution

    attribution = PnLAttribution(
        total_pnl=1000.0,
        asset_contributions={"BTC-EUR": 600.0, "ETH-EUR": 400.0},
    )

    df = attribution.to_dataframe()

    assert len(df) == 2
    assert "asset" in df.columns
    assert "pnl_contribution" in df.columns
    assert df["pnl_contribution"].sum() == 1000.0
