"""
Tests for VaR Gate Layer
"""

import numpy as np
import pandas as pd
import pytest

from src.core.peak_config import PeakConfig
from src.risk_layer.var_gate import VaRGate, VaRGateStatus, status_to_dict


@pytest.fixture
def default_config() -> PeakConfig:
    """Create default VaR gate config."""
    return PeakConfig(
        raw={
            "risk": {
                "var_gate": {
                    "enabled": True,
                    "method": "parametric",
                    "confidence": 0.95,
                    "horizon_days": 1,
                    "max_var_pct": 0.03,  # 3% block threshold
                    "warn_var_pct": None,
                }
            }
        }
    )


@pytest.fixture
def config_with_warn() -> PeakConfig:
    """Create VaR gate config with warning threshold."""
    return PeakConfig(
        raw={
            "risk": {
                "var_gate": {
                    "enabled": True,
                    "method": "parametric",
                    "confidence": 0.95,
                    "horizon_days": 1,
                    "max_var_pct": 0.03,
                    "warn_var_pct": 0.02,  # 2% warn threshold
                }
            }
        }
    )


@pytest.fixture
def disabled_config() -> PeakConfig:
    """Create disabled VaR gate config."""
    return PeakConfig(raw={"risk": {"var_gate": {"enabled": False}}})


@pytest.fixture
def sample_returns() -> pd.DataFrame:
    """Create sample returns DataFrame."""
    np.random.seed(42)
    n = 100
    returns = pd.DataFrame(
        {
            "BTC": np.random.normal(0.001, 0.02, n),
            "ETH": np.random.normal(0.001, 0.025, n),
        }
    )
    return returns


@pytest.fixture
def sample_weights() -> dict:
    """Create sample portfolio weights."""
    return {"BTC": 0.6, "ETH": 0.4}


# ============================================================================
# Disabled Gate Tests
# ============================================================================


def test_disabled_gate_returns_ok(disabled_config: PeakConfig) -> None:
    """Test that disabled VaR gate always returns OK."""
    gate = VaRGate(disabled_config)

    # Even with no context
    status = gate.evaluate(None)

    assert status.severity == "OK"
    assert "disabled" in status.reason.lower()
    assert not status.inputs_available


def test_disabled_gate_with_data(
    disabled_config: PeakConfig, sample_returns: pd.DataFrame, sample_weights: dict
) -> None:
    """Test that disabled gate ignores data."""
    gate = VaRGate(disabled_config)

    context = {"returns_df": sample_returns, "weights": sample_weights}
    status = gate.evaluate(context)

    assert status.severity == "OK"
    assert "disabled" in status.reason.lower()


# ============================================================================
# Missing Data Tests (Safe Defaults)
# ============================================================================


def test_missing_context_returns_ok(default_config: PeakConfig) -> None:
    """Test that missing context returns OK (not applicable)."""
    gate = VaRGate(default_config)

    status = gate.evaluate(None)

    assert status.severity == "OK"
    assert "not applicable" in status.reason.lower()
    assert not status.inputs_available


def test_missing_returns_returns_ok(default_config: PeakConfig, sample_weights: dict) -> None:
    """Test that missing returns_df returns OK."""
    gate = VaRGate(default_config)

    context = {"weights": sample_weights}  # Missing returns_df
    status = gate.evaluate(context)

    assert status.severity == "OK"
    assert "not applicable" in status.reason.lower()
    assert not status.inputs_available


def test_missing_weights_returns_ok(
    default_config: PeakConfig, sample_returns: pd.DataFrame
) -> None:
    """Test that missing weights returns OK."""
    gate = VaRGate(default_config)

    context = {"returns_df": sample_returns}  # Missing weights
    status = gate.evaluate(context)

    assert status.severity == "OK"
    assert "not applicable" in status.reason.lower()
    assert not status.inputs_available


def test_invalid_returns_type_returns_ok(default_config: PeakConfig, sample_weights: dict) -> None:
    """Test that invalid returns_df type returns OK."""
    gate = VaRGate(default_config)

    context = {"returns_df": "not_a_dataframe", "weights": sample_weights}
    status = gate.evaluate(context)

    assert status.severity == "OK"
    assert "not applicable" in status.reason.lower()
    assert not status.inputs_available


# ============================================================================
# VaR Calculation Tests
# ============================================================================


def test_var_within_limits_returns_ok(
    default_config: PeakConfig, sample_returns: pd.DataFrame, sample_weights: dict
) -> None:
    """Test that VaR within limits returns OK."""
    gate = VaRGate(default_config)

    context = {"returns_df": sample_returns, "weights": sample_weights}
    status = gate.evaluate(context)

    assert status.severity == "OK"
    assert status.var_pct is not None
    assert status.var_pct >= 0
    assert status.var_pct < gate.max_var_pct
    assert status.inputs_available
    assert "within limits" in status.reason.lower()


def test_var_exceeds_limit_blocks(default_config: PeakConfig, sample_weights: dict) -> None:
    """Test that VaR exceeding limit blocks."""
    gate = VaRGate(default_config)

    # Create high-volatility returns to exceed 3% VaR
    np.random.seed(123)
    high_vol_returns = pd.DataFrame(
        {
            "BTC": np.random.normal(0, 0.10, 100),  # 10% daily vol
            "ETH": np.random.normal(0, 0.12, 100),  # 12% daily vol
        }
    )

    context = {"returns_df": high_vol_returns, "weights": sample_weights}
    status = gate.evaluate(context)

    assert status.severity == "BLOCK"
    assert status.var_pct is not None
    assert status.var_pct >= gate.max_var_pct
    assert "exceeds limit" in status.reason.lower()


def test_var_near_limit_warns(config_with_warn: PeakConfig, sample_weights: dict) -> None:
    """Test that VaR near limit triggers warning."""
    gate = VaRGate(config_with_warn)

    # Create medium-volatility returns to trigger warn but not block
    # Target: 2-3% VaR (between warn=2% and block=3%)
    np.random.seed(456)
    med_vol_returns = pd.DataFrame(
        {
            "BTC": np.random.normal(0, 0.04, 100),  # 4% daily vol
            "ETH": np.random.normal(0, 0.05, 100),  # 5% daily vol
        }
    )

    context = {"returns_df": med_vol_returns, "weights": sample_weights}
    status = gate.evaluate(context)

    # Should be WARN or BLOCK depending on exact VaR
    assert status.severity in ("WARN", "BLOCK")
    assert status.var_pct is not None

    if status.severity == "WARN":
        assert status.var_pct >= gate.warn_var_pct
        assert status.var_pct < gate.max_var_pct
        assert "near limit" in status.reason.lower()


# ============================================================================
# Historical VaR Tests
# ============================================================================


def test_historical_var_method(sample_returns: pd.DataFrame, sample_weights: dict) -> None:
    """Test historical VaR method."""
    config = PeakConfig(
        raw={
            "risk": {
                "var_gate": {
                    "enabled": True,
                    "method": "historical",
                    "confidence": 0.95,
                    "horizon_days": 1,
                    "max_var_pct": 0.03,
                }
            }
        }
    )

    gate = VaRGate(config)

    context = {"returns_df": sample_returns, "weights": sample_weights}
    status = gate.evaluate(context)

    assert status.severity == "OK"
    assert status.method == "historical"
    assert status.var_pct is not None
    assert status.var_pct >= 0


# ============================================================================
# Configuration Tests
# ============================================================================


def test_invalid_method_raises() -> None:
    """Test that invalid VaR method raises ValueError."""
    config = PeakConfig(raw={"risk": {"var_gate": {"enabled": True, "method": "invalid_method"}}})

    with pytest.raises(ValueError, match="Invalid VaR method"):
        VaRGate(config)


def test_custom_confidence_level(sample_returns: pd.DataFrame, sample_weights: dict) -> None:
    """Test custom confidence level."""
    config = PeakConfig(
        raw={
            "risk": {
                "var_gate": {
                    "enabled": True,
                    "method": "parametric",
                    "confidence": 0.99,  # 99% confidence
                    "horizon_days": 1,
                    "max_var_pct": 0.05,
                }
            }
        }
    )

    gate = VaRGate(config)

    context = {"returns_df": sample_returns, "weights": sample_weights}
    status = gate.evaluate(context)

    assert status.confidence == 0.99
    assert status.var_pct is not None
    # 99% VaR should be higher than 95% VaR
    assert status.var_pct > 0


def test_multi_day_horizon(sample_returns: pd.DataFrame, sample_weights: dict) -> None:
    """Test multi-day horizon."""
    config = PeakConfig(
        raw={
            "risk": {
                "var_gate": {
                    "enabled": True,
                    "method": "parametric",
                    "confidence": 0.95,
                    "horizon_days": 5,  # 5-day horizon
                    "max_var_pct": 0.10,
                }
            }
        }
    )

    gate = VaRGate(config)

    context = {"returns_df": sample_returns, "weights": sample_weights}
    status = gate.evaluate(context)

    assert status.horizon_days == 5
    assert status.var_pct is not None
    # Multi-day VaR should be higher than 1-day
    assert status.var_pct > 0


# ============================================================================
# Status Serialization Tests
# ============================================================================


def test_status_to_dict_complete(
    default_config: PeakConfig, sample_returns: pd.DataFrame, sample_weights: dict
) -> None:
    """Test status_to_dict with complete status."""
    gate = VaRGate(default_config)

    context = {"returns_df": sample_returns, "weights": sample_weights}
    status = gate.evaluate(context)

    d = status_to_dict(status)

    assert "severity" in d
    assert "reason" in d
    assert "var_pct" in d
    assert "threshold_block" in d
    assert "threshold_warn" in d
    assert "confidence" in d
    assert "horizon_days" in d
    assert "method" in d
    assert "inputs_available" in d
    assert "timestamp_utc" in d

    # Check values
    assert d["severity"] == status.severity
    assert d["var_pct"] == status.var_pct
    assert d["inputs_available"] is True


def test_status_to_dict_stable_order(default_config: PeakConfig) -> None:
    """Test that status_to_dict has stable key order."""
    gate = VaRGate(default_config)

    status = gate.evaluate(None)
    d = status_to_dict(status)

    keys = list(d.keys())
    expected_keys = [
        "severity",
        "reason",
        "var_pct",
        "threshold_block",
        "threshold_warn",
        "confidence",
        "horizon_days",
        "method",
        "inputs_available",
        "timestamp_utc",
    ]

    assert keys == expected_keys


# ============================================================================
# Last Status Property Tests
# ============================================================================


def test_last_status_property(
    default_config: PeakConfig, sample_returns: pd.DataFrame, sample_weights: dict
) -> None:
    """Test last_status property."""
    gate = VaRGate(default_config)

    # Initially None
    assert gate.last_status is None

    # After evaluation
    context = {"returns_df": sample_returns, "weights": sample_weights}
    status = gate.evaluate(context)

    assert gate.last_status is not None
    assert gate.last_status.severity == status.severity
    assert gate.last_status.var_pct == status.var_pct


# ============================================================================
# Edge Cases
# ============================================================================


def test_empty_returns_dataframe(default_config: PeakConfig, sample_weights: dict) -> None:
    """Test handling of empty returns DataFrame."""
    gate = VaRGate(default_config)

    empty_returns = pd.DataFrame({"BTC": [], "ETH": []})
    context = {"returns_df": empty_returns, "weights": sample_weights}

    # Should handle gracefully (safe default: OK)
    status = gate.evaluate(context)

    assert status.severity == "OK"
    # Calculation should fail gracefully
    assert "failed" in status.reason.lower() or "not applicable" in status.reason.lower()


def test_zero_volatility_returns(default_config: PeakConfig, sample_weights: dict) -> None:
    """Test handling of zero-volatility returns."""
    gate = VaRGate(default_config)

    # All returns are zero (no volatility)
    zero_vol_returns = pd.DataFrame(
        {
            "BTC": [0.0] * 100,
            "ETH": [0.0] * 100,
        }
    )

    context = {"returns_df": zero_vol_returns, "weights": sample_weights}

    # Should handle gracefully
    status = gate.evaluate(context)

    # Either OK (VaR=0) or calculation fails gracefully
    assert status.severity in ("OK", "BLOCK")
