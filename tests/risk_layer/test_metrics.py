"""
Tests for Risk Metrics Schema and Extraction
"""

import pytest

from src.risk_layer.metrics import RiskMetrics, extract_risk_metrics, metrics_to_dict


# ============================================================================
# RiskMetrics Dataclass Tests
# ============================================================================


def test_risk_metrics_default_values() -> None:
    """Test that RiskMetrics has sensible defaults."""
    m = RiskMetrics()
    assert m.daily_pnl_pct is None
    assert m.current_drawdown_pct is None
    assert m.realized_vol_pct is None
    assert m.timestamp_utc is None


def test_risk_metrics_explicit_values() -> None:
    """Test RiskMetrics with explicit values."""
    m = RiskMetrics(
        daily_pnl_pct=-0.05,
        current_drawdown_pct=0.10,
        realized_vol_pct=0.25,
        timestamp_utc="2025-12-25T00:00:00Z",
    )
    assert m.daily_pnl_pct == -0.05
    assert m.current_drawdown_pct == 0.10
    assert m.realized_vol_pct == 0.25
    assert m.timestamp_utc == "2025-12-25T00:00:00Z"


def test_risk_metrics_immutable() -> None:
    """Test that RiskMetrics is frozen (immutable)."""
    m = RiskMetrics(daily_pnl_pct=-0.05)

    with pytest.raises(Exception):  # dataclass frozen raises FrozenInstanceError
        m.daily_pnl_pct = -0.10  # type: ignore[misc]


# ============================================================================
# extract_risk_metrics: Nested Context Layouts
# ============================================================================


def test_extract_nested_under_metrics() -> None:
    """Test extraction from context["metrics"]."""
    context = {
        "metrics": {
            "daily_pnl_pct": -0.05,
            "current_drawdown_pct": 0.10,
            "realized_vol_pct": 0.25,
        }
    }
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == -0.05
    assert m.current_drawdown_pct == 0.10
    assert m.realized_vol_pct == 0.25


def test_extract_nested_under_risk_metrics() -> None:
    """Test extraction from context["risk"]["metrics"]."""
    context = {
        "risk": {
            "metrics": {
                "daily_pnl_pct": -0.03,
                "current_drawdown_pct": 0.08,
            }
        }
    }
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == -0.03
    assert m.current_drawdown_pct == 0.08
    assert m.realized_vol_pct is None  # Not provided


def test_extract_direct_keys() -> None:
    """Test extraction from direct context keys."""
    context = {
        "daily_pnl_pct": -0.06,
        "current_drawdown_pct": 0.12,
        "other_field": "ignored",
    }
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == -0.06
    assert m.current_drawdown_pct == 0.12


def test_extract_priority_metrics_over_direct() -> None:
    """Test that nested metrics take priority over direct keys."""
    context = {
        "metrics": {"daily_pnl_pct": -0.05},
        "daily_pnl_pct": -0.10,  # Should be ignored
    }
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == -0.05  # From metrics, not direct


def test_extract_priority_risk_metrics_over_direct() -> None:
    """Test that risk.metrics takes priority over direct keys."""
    context = {
        "risk": {"metrics": {"daily_pnl_pct": -0.03}},
        "daily_pnl_pct": -0.10,  # Should be ignored
    }
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == -0.03


# ============================================================================
# extract_risk_metrics: Missing/None Handling
# ============================================================================


def test_extract_none_context() -> None:
    """Test extraction from None context."""
    m = extract_risk_metrics(None)
    assert m.daily_pnl_pct is None
    assert m.current_drawdown_pct is None
    assert m.realized_vol_pct is None


def test_extract_empty_context() -> None:
    """Test extraction from empty context."""
    m = extract_risk_metrics({})
    assert m.daily_pnl_pct is None
    assert m.current_drawdown_pct is None


def test_extract_missing_keys() -> None:
    """Test extraction when keys are missing."""
    context = {"metrics": {"some_other_field": 123}}
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct is None
    assert m.current_drawdown_pct is None


def test_extract_none_values() -> None:
    """Test extraction when values are explicitly None."""
    context = {
        "metrics": {
            "daily_pnl_pct": None,
            "current_drawdown_pct": None,
        }
    }
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct is None
    assert m.current_drawdown_pct is None


def test_extract_partial_metrics() -> None:
    """Test extraction when only some metrics are provided."""
    context = {"metrics": {"daily_pnl_pct": -0.05}}
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == -0.05
    assert m.current_drawdown_pct is None
    assert m.realized_vol_pct is None


# ============================================================================
# extract_risk_metrics: Invalid Type Handling
# ============================================================================


def test_extract_invalid_context_type() -> None:
    """Test extraction from non-dict context."""
    m = extract_risk_metrics("not a dict")  # type: ignore[arg-type]
    assert m.daily_pnl_pct is None


def test_extract_string_value_converts_to_float() -> None:
    """Test that string values are converted to float."""
    context = {"metrics": {"daily_pnl_pct": "-0.05"}}
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == -0.05


def test_extract_int_value_converts_to_float() -> None:
    """Test that int values are converted to float."""
    context = {"metrics": {"daily_pnl_pct": -5}}
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == -5.0


def test_extract_invalid_string_value_returns_none() -> None:
    """Test that non-numeric string returns None."""
    context = {"metrics": {"daily_pnl_pct": "not_a_number"}}
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct is None


def test_extract_list_value_returns_none() -> None:
    """Test that list values return None."""
    context = {"metrics": {"daily_pnl_pct": [1, 2, 3]}}
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct is None


def test_extract_dict_value_returns_none() -> None:
    """Test that dict values return None."""
    context = {"metrics": {"daily_pnl_pct": {"nested": "value"}}}
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct is None


def test_extract_nested_metrics_not_dict() -> None:
    """Test graceful handling when metrics is not a dict."""
    context = {"metrics": "not_a_dict"}
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct is None


def test_extract_nested_risk_not_dict() -> None:
    """Test graceful handling when risk is not a dict."""
    context = {"risk": "not_a_dict"}
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct is None


# ============================================================================
# extract_risk_metrics: Timestamp Handling
# ============================================================================


def test_extract_timestamp_string() -> None:
    """Test extraction of timestamp as string."""
    context = {"metrics": {"timestamp_utc": "2025-12-25T12:00:00Z"}}
    m = extract_risk_metrics(context)
    assert m.timestamp_utc == "2025-12-25T12:00:00Z"


def test_extract_timestamp_converts_to_string() -> None:
    """Test that non-string timestamp is converted to string."""
    context = {"metrics": {"timestamp_utc": 123456789}}
    m = extract_risk_metrics(context)
    assert m.timestamp_utc == "123456789"


def test_extract_timestamp_none() -> None:
    """Test that missing timestamp returns None."""
    context = {"metrics": {"daily_pnl_pct": -0.05}}
    m = extract_risk_metrics(context)
    assert m.timestamp_utc is None


# ============================================================================
# metrics_to_dict: Serialization
# ============================================================================


def test_metrics_to_dict_with_all_values() -> None:
    """Test conversion to dict with all values."""
    m = RiskMetrics(
        daily_pnl_pct=-0.05,
        current_drawdown_pct=0.10,
        realized_vol_pct=0.25,
        timestamp_utc="2025-12-25T00:00:00Z",
    )
    d = metrics_to_dict(m)

    assert d["daily_pnl_pct"] == -0.05
    assert d["current_drawdown_pct"] == 0.10
    assert d["realized_vol_pct"] == 0.25
    assert d["timestamp_utc"] == "2025-12-25T00:00:00Z"


def test_metrics_to_dict_with_none_values() -> None:
    """Test conversion to dict preserves None values."""
    m = RiskMetrics()
    d = metrics_to_dict(m)

    assert d["daily_pnl_pct"] is None
    assert d["current_drawdown_pct"] is None
    assert d["realized_vol_pct"] is None
    assert d["timestamp_utc"] is None


def test_metrics_to_dict_stable_key_order() -> None:
    """Test that dict keys are in stable order."""
    m = RiskMetrics(daily_pnl_pct=-0.05, realized_vol_pct=0.25)
    d = metrics_to_dict(m)

    keys = list(d.keys())
    expected_keys = [
        "daily_pnl_pct",
        "current_drawdown_pct",
        "realized_vol_pct",
        "timestamp_utc",
    ]
    assert keys == expected_keys


def test_metrics_to_dict_partial_values() -> None:
    """Test conversion with partial values."""
    m = RiskMetrics(daily_pnl_pct=-0.05, current_drawdown_pct=0.10)
    d = metrics_to_dict(m)

    assert d["daily_pnl_pct"] == -0.05
    assert d["current_drawdown_pct"] == 0.10
    assert d["realized_vol_pct"] is None
    assert d["timestamp_utc"] is None


# ============================================================================
# Integration: Round-trip
# ============================================================================


def test_round_trip_extraction_and_serialization() -> None:
    """Test that extract -> to_dict -> extract works correctly."""
    original_context = {
        "metrics": {
            "daily_pnl_pct": -0.05,
            "current_drawdown_pct": 0.10,
        }
    }

    # Extract
    m1 = extract_risk_metrics(original_context)

    # Convert to dict
    d = metrics_to_dict(m1)

    # Extract again from dict
    m2 = extract_risk_metrics(d)

    # Should be equivalent
    assert m2.daily_pnl_pct == m1.daily_pnl_pct
    assert m2.current_drawdown_pct == m1.current_drawdown_pct
    assert m2.realized_vol_pct == m1.realized_vol_pct


def test_metrics_to_dict_is_json_serializable() -> None:
    """Test that output dict can be JSON serialized."""
    import json

    m = RiskMetrics(daily_pnl_pct=-0.05, current_drawdown_pct=0.10)
    d = metrics_to_dict(m)

    # Should not raise
    json_str = json.dumps(d)
    assert json_str is not None


# ============================================================================
# Edge Cases
# ============================================================================


def test_extract_zero_values() -> None:
    """Test that zero values are preserved (not treated as None)."""
    context = {
        "metrics": {
            "daily_pnl_pct": 0.0,
            "current_drawdown_pct": 0.0,
            "realized_vol_pct": 0.0,
        }
    }
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == 0.0
    assert m.current_drawdown_pct == 0.0
    assert m.realized_vol_pct == 0.0


def test_extract_negative_zero() -> None:
    """Test that negative zero is handled."""
    context = {"metrics": {"daily_pnl_pct": -0.0}}
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == 0.0


def test_extract_very_large_values() -> None:
    """Test that very large values are preserved."""
    context = {
        "metrics": {
            "daily_pnl_pct": -999.999,
            "current_drawdown_pct": 999.999,
        }
    }
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == -999.999
    assert m.current_drawdown_pct == 999.999


def test_extract_very_small_values() -> None:
    """Test that very small values are preserved."""
    context = {"metrics": {"daily_pnl_pct": 1e-10}}
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == 1e-10


def test_extract_scientific_notation_string() -> None:
    """Test that scientific notation strings are converted."""
    context = {"metrics": {"daily_pnl_pct": "-5e-2"}}
    m = extract_risk_metrics(context)
    assert m.daily_pnl_pct == -0.05
