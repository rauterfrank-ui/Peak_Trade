"""
Risk Metrics Schema and Extraction
====================================

Canonical schema and extraction utilities for risk metrics.

This module provides:
- RiskMetrics: Typed dataclass for canonical risk metrics
- extract_risk_metrics: Tolerant extraction from various context layouts
- metrics_to_dict: Stable serialization for audit logs

Design principles:
- Tolerant: Handles nested/direct keys, missing data, invalid types
- Deterministic: Consistent output order and structure
- Non-crashing: Returns None for invalid/missing data instead of raising
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RiskMetrics:
    """
    Canonical risk metrics schema.

    All percentage values are expressed as decimals (e.g., 0.05 = 5%).

    Attributes:
        daily_pnl_pct: Daily PnL as percentage (e.g., -0.06 for -6% loss)
        current_drawdown_pct: Current drawdown from peak (e.g., 0.21 for 21% drawdown)
        realized_vol_pct: Realized volatility as percentage (optional)
        timestamp_utc: ISO8601 timestamp when metrics were captured (optional)
    """

    daily_pnl_pct: float | None = None
    current_drawdown_pct: float | None = None
    realized_vol_pct: float | None = None
    timestamp_utc: str | None = None


def extract_risk_metrics(context: Any) -> RiskMetrics:
    """
    Extract risk metrics from context dict (tolerant).

    Supports multiple context layouts:
    1. Nested under "metrics": context["metrics"]["daily_pnl_pct"]
    2. Nested under "risk.metrics": context["risk"]["metrics"]["daily_pnl_pct"]
    3. Direct keys: context["daily_pnl_pct"]

    Handles gracefully:
    - None/missing context
    - Missing keys
    - None values
    - Non-numeric values (returns None)
    - Invalid types (returns None)

    Args:
        context: Context dict or None

    Returns:
        RiskMetrics with extracted values (None for missing/invalid)

    Examples:
        >>> # Nested under metrics
        >>> ctx = {"metrics": {"daily_pnl_pct": -0.05}}
        >>> m = extract_risk_metrics(ctx)
        >>> m.daily_pnl_pct
        -0.05

        >>> # Direct keys
        >>> ctx = {"daily_pnl_pct": -0.03, "current_drawdown_pct": 0.10}
        >>> m = extract_risk_metrics(ctx)
        >>> m.daily_pnl_pct
        -0.03

        >>> # Missing data
        >>> ctx = {}
        >>> m = extract_risk_metrics(ctx)
        >>> m.daily_pnl_pct is None
        True
    """
    # Handle None/invalid context
    if context is None or not isinstance(context, dict):
        return RiskMetrics()

    # Try different extraction paths
    # Priority: metrics -> risk.metrics -> direct keys
    metrics_dict: dict = {}

    # Path 1: context["metrics"]
    if "metrics" in context and isinstance(context["metrics"], dict):
        metrics_dict = context["metrics"]
    # Path 2: context["risk"]["metrics"]
    elif "risk" in context and isinstance(context.get("risk"), dict):
        risk_dict = context["risk"]
        if "metrics" in risk_dict and isinstance(risk_dict["metrics"], dict):
            metrics_dict = risk_dict["metrics"]
    # Path 3: direct keys in context
    else:
        metrics_dict = context

    # Extract individual metrics (tolerant)
    daily_pnl_pct = _safe_extract_float(metrics_dict, "daily_pnl_pct")
    current_drawdown_pct = _safe_extract_float(metrics_dict, "current_drawdown_pct")
    realized_vol_pct = _safe_extract_float(metrics_dict, "realized_vol_pct")
    timestamp_utc = _safe_extract_str(metrics_dict, "timestamp_utc")

    return RiskMetrics(
        daily_pnl_pct=daily_pnl_pct,
        current_drawdown_pct=current_drawdown_pct,
        realized_vol_pct=realized_vol_pct,
        timestamp_utc=timestamp_utc,
    )


def metrics_to_dict(metrics: RiskMetrics) -> dict:
    """
    Convert RiskMetrics to dict with stable order.

    Returns a dict with canonical key order for audit logs.
    None values are preserved (not filtered).

    Args:
        metrics: RiskMetrics instance

    Returns:
        Dict with stable key order

    Example:
        >>> m = RiskMetrics(daily_pnl_pct=-0.05, current_drawdown_pct=0.10)
        >>> d = metrics_to_dict(m)
        >>> list(d.keys())
        ['daily_pnl_pct', 'current_drawdown_pct', 'realized_vol_pct', 'timestamp_utc']
    """
    return {
        "daily_pnl_pct": metrics.daily_pnl_pct,
        "current_drawdown_pct": metrics.current_drawdown_pct,
        "realized_vol_pct": metrics.realized_vol_pct,
        "timestamp_utc": metrics.timestamp_utc,
    }


def _safe_extract_float(d: dict, key: str) -> float | None:
    """
    Safely extract float value from dict.

    Args:
        d: Dict to extract from
        key: Key to extract

    Returns:
        Float value or None if missing/invalid
    """
    value = d.get(key)
    if value is None:
        return None

    # Try to convert to float
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_extract_str(d: dict, key: str) -> str | None:
    """
    Safely extract string value from dict.

    Args:
        d: Dict to extract from
        key: Key to extract

    Returns:
        String value or None if missing/invalid
    """
    value = d.get(key)
    if value is None:
        return None

    if isinstance(value, str):
        return value

    # Try to convert to string
    try:
        return str(value)
    except (TypeError, ValueError):
        return None
