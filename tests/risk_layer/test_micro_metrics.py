"""
Tests for Microstructure Metrics Extraction

Verifies:
- Tolerant extraction from multiple context layouts
- Invalid types → None (no crashes)
- Stable serialization
"""

import pytest
from src.risk_layer.micro_metrics import (
    MicrostructureMetrics,
    extract_micro_metrics,
    micro_metrics_to_dict,
)


class TestMicrostructureMetrics:
    """Test MicrostructureMetrics dataclass."""

    def test_empty_metrics(self):
        """Test empty metrics (all None)."""
        metrics = MicrostructureMetrics()
        assert metrics.spread_pct is None
        assert metrics.slippage_estimate_pct is None
        assert metrics.order_book_depth_notional is None
        assert metrics.adv_notional is None
        assert metrics.last_price is None
        assert metrics.realized_vol_pct is None
        assert metrics.timestamp_utc is None

    def test_full_metrics(self):
        """Test fully populated metrics."""
        metrics = MicrostructureMetrics(
            spread_pct=0.002,
            slippage_estimate_pct=0.005,
            order_book_depth_notional=50000.0,
            adv_notional=1_000_000.0,
            last_price=100.5,
            realized_vol_pct=0.25,
            timestamp_utc="2025-01-01T12:00:00Z",
        )
        assert metrics.spread_pct == 0.002
        assert metrics.slippage_estimate_pct == 0.005
        assert metrics.order_book_depth_notional == 50000.0
        assert metrics.adv_notional == 1_000_000.0
        assert metrics.last_price == 100.5
        assert metrics.realized_vol_pct == 0.25
        assert metrics.timestamp_utc == "2025-01-01T12:00:00Z"


class TestExtractMicroMetrics:
    """Test extract_micro_metrics function."""

    def test_extract_from_micro_key(self):
        """Test extraction from context['micro']."""
        context = {
            "micro": {
                "spread_pct": 0.003,
                "slippage_estimate_pct": 0.007,
                "order_book_depth_notional": 25000.0,
                "adv_notional": 500_000.0,
                "last_price": 50.25,
                "timestamp_utc": "2025-01-02T10:00:00Z",
            }
        }
        metrics = extract_micro_metrics(context)
        assert metrics.spread_pct == 0.003
        assert metrics.slippage_estimate_pct == 0.007
        assert metrics.order_book_depth_notional == 25000.0
        assert metrics.adv_notional == 500_000.0
        assert metrics.last_price == 50.25
        assert metrics.timestamp_utc == "2025-01-02T10:00:00Z"

    def test_extract_from_market_micro_key(self):
        """Test extraction from context['market']['micro']."""
        context = {
            "market": {
                "micro": {
                    "spread_pct": 0.004,
                    "slippage_estimate_pct": 0.008,
                    "order_book_depth_notional": 30000.0,
                }
            }
        }
        metrics = extract_micro_metrics(context)
        assert metrics.spread_pct == 0.004
        assert metrics.slippage_estimate_pct == 0.008
        assert metrics.order_book_depth_notional == 30000.0

    def test_extract_from_metrics_key(self):
        """Test extraction from context['metrics']."""
        context = {
            "metrics": {
                "spread_pct": 0.005,
                "adv_notional": 750_000.0,
                "last_price": 75.5,
            }
        }
        metrics = extract_micro_metrics(context)
        assert metrics.spread_pct == 0.005
        assert metrics.adv_notional == 750_000.0
        assert metrics.last_price == 75.5

    def test_extract_from_direct_keys(self):
        """Test extraction from direct context keys."""
        context = {
            "spread_pct": 0.006,
            "slippage_estimate_pct": 0.012,
            "last_price": 99.99,
        }
        metrics = extract_micro_metrics(context)
        assert metrics.spread_pct == 0.006
        assert metrics.slippage_estimate_pct == 0.012
        assert metrics.last_price == 99.99

    def test_extract_with_fallback_chain(self):
        """Test fallback chain (specific layouts take precedence)."""
        context = {
            "micro": {"spread_pct": 0.001},  # Most specific
            "metrics": {"spread_pct": 0.002},  # Less specific
            "spread_pct": 0.003,  # Direct (least specific)
            "slippage_estimate_pct": 0.010,  # Only in direct
        }
        metrics = extract_micro_metrics(context)
        # Should use micro (most specific) for spread
        assert metrics.spread_pct == 0.001
        # Should fall back to direct for slippage
        assert metrics.slippage_estimate_pct == 0.010

    def test_extract_empty_context(self):
        """Test extraction from empty context."""
        context = {}
        metrics = extract_micro_metrics(context)
        assert metrics.spread_pct is None
        assert metrics.slippage_estimate_pct is None
        assert metrics.order_book_depth_notional is None

    def test_extract_non_dict_context(self):
        """Test extraction from non-dict context (should not crash)."""
        context = "not a dict"
        metrics = extract_micro_metrics(context)
        assert metrics.spread_pct is None
        assert metrics.slippage_estimate_pct is None

    def test_extract_invalid_types_to_none(self):
        """Test that invalid types convert to None."""
        context = {
            "micro": {
                "spread_pct": "invalid",  # String (not numeric)
                "slippage_estimate_pct": None,  # Already None
                "order_book_depth_notional": [1, 2, 3],  # List
                "adv_notional": {"nested": "dict"},  # Dict
                "last_price": 100.0,  # Valid
            }
        }
        metrics = extract_micro_metrics(context)
        assert metrics.spread_pct is None
        assert metrics.slippage_estimate_pct is None
        assert metrics.order_book_depth_notional is None
        assert metrics.adv_notional is None
        assert metrics.last_price == 100.0

    def test_extract_numeric_strings(self):
        """Test that numeric strings are converted to floats."""
        context = {
            "micro": {
                "spread_pct": "0.003",
                "last_price": "50.25",
            }
        }
        metrics = extract_micro_metrics(context)
        assert metrics.spread_pct == 0.003
        assert metrics.last_price == 50.25

    def test_extract_timestamp_string(self):
        """Test that timestamp is extracted as string (not converted)."""
        context = {
            "micro": {
                "timestamp_utc": "2025-01-03T15:30:00Z",
            }
        }
        metrics = extract_micro_metrics(context)
        assert metrics.timestamp_utc == "2025-01-03T15:30:00Z"

    def test_extract_timestamp_invalid(self):
        """Test that invalid timestamp types are ignored."""
        context = {
            "micro": {
                "timestamp_utc": 12345,  # Not a string
            }
        }
        metrics = extract_micro_metrics(context)
        assert metrics.timestamp_utc is None


class TestMicroMetricsToDict:
    """Test micro_metrics_to_dict serialization."""

    def test_serialize_empty(self):
        """Test serialization of empty metrics."""
        metrics = MicrostructureMetrics()
        result = micro_metrics_to_dict(metrics)

        # Check all keys present (None values preserved)
        assert "spread_pct" in result
        assert "slippage_estimate_pct" in result
        assert "order_book_depth_notional" in result
        assert "adv_notional" in result
        assert "last_price" in result
        assert "realized_vol_pct" in result
        assert "timestamp_utc" in result

        # All should be None
        assert all(v is None for v in result.values())

    def test_serialize_full(self):
        """Test serialization of fully populated metrics."""
        metrics = MicrostructureMetrics(
            spread_pct=0.002,
            slippage_estimate_pct=0.005,
            order_book_depth_notional=50000.0,
            adv_notional=1_000_000.0,
            last_price=100.5,
            realized_vol_pct=0.25,
            timestamp_utc="2025-01-01T12:00:00Z",
        )
        result = micro_metrics_to_dict(metrics)

        assert result["spread_pct"] == 0.002
        assert result["slippage_estimate_pct"] == 0.005
        assert result["order_book_depth_notional"] == 50000.0
        assert result["adv_notional"] == 1_000_000.0
        assert result["last_price"] == 100.5
        assert result["realized_vol_pct"] == 0.25
        assert result["timestamp_utc"] == "2025-01-01T12:00:00Z"

    def test_serialize_keys_sorted(self):
        """Test that serialized dict has sorted keys (deterministic)."""
        metrics = MicrostructureMetrics(
            spread_pct=0.002,
            last_price=100.0,
            adv_notional=500_000.0,
        )
        result = micro_metrics_to_dict(metrics)

        keys = list(result.keys())
        assert keys == sorted(keys), "Keys should be alphabetically sorted"

    def test_serialize_json_serializable(self):
        """Test that result is JSON-serializable."""
        import json

        metrics = MicrostructureMetrics(
            spread_pct=0.003,
            slippage_estimate_pct=0.007,
            order_book_depth_notional=None,  # None value
            last_price=75.5,
            timestamp_utc="2025-01-02T10:00:00Z",
        )
        result = micro_metrics_to_dict(metrics)

        # Should not raise
        json_str = json.dumps(result)
        assert json_str

        # Round-trip
        parsed = json.loads(json_str)
        assert parsed["spread_pct"] == 0.003
        assert parsed["order_book_depth_notional"] is None
