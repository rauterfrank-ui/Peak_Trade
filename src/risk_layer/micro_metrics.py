"""
Microstructure Metrics Extraction & Serialization

Provides tolerant extraction of pre-trade liquidity/microstructure data
from various context layouts, with stable serialization for audit trails.

Design:
- All fields Optional[float] (None allowed, never crash)
- Tolerant extraction from multiple context layouts
- Deterministic serialization for audit stability
"""

from dataclasses import dataclass, asdict
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class MicrostructureMetrics:
    """
    Pre-trade microstructure metrics (all optional).

    Fields:
    - spread_pct: bid-ask spread / mid price (0.01 = 1%)
    - slippage_estimate_pct: pre-trade slippage estimate
    - order_book_depth_notional: depth at top levels (quote currency)
    - adv_notional: average daily notional volume
    - last_price: last traded price
    - realized_vol_pct: realized volatility (annualized)
    - timestamp_utc: ISO8601 timestamp of metrics snapshot
    """

    spread_pct: Optional[float] = None
    slippage_estimate_pct: Optional[float] = None
    order_book_depth_notional: Optional[float] = None
    adv_notional: Optional[float] = None
    last_price: Optional[float] = None
    realized_vol_pct: Optional[float] = None
    timestamp_utc: Optional[str] = None


def _safe_float(value: Any) -> Optional[float]:
    """
    Convert value to float, return None if invalid.

    Args:
        value: Any value to convert

    Returns:
        Float value or None if conversion fails
    """
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_micro_metrics(context: Any) -> MicrostructureMetrics:
    """
    Tolerantly extract microstructure metrics from context.

    Supported layouts:
    1. context["micro"][field]
    2. context["market"]["micro"][field]
    3. context["metrics"][field]
    4. context[field] (direct keys)

    Invalid/missing values → None (never crashes).

    Args:
        context: Dictionary-like object containing market data

    Returns:
        MicrostructureMetrics instance (all fields may be None)
    """
    if not isinstance(context, dict):
        logger.debug("Context is not a dict, returning empty MicrostructureMetrics")
        return MicrostructureMetrics()

    # Try different layouts in order of specificity
    micro_sources = []

    # Layout 1: context["micro"]
    if "micro" in context and isinstance(context["micro"], dict):
        micro_sources.append(context["micro"])

    # Layout 2: context["market"]["micro"]
    if "market" in context and isinstance(context["market"], dict):
        market = context["market"]
        if "micro" in market and isinstance(market["micro"], dict):
            micro_sources.append(market["micro"])

    # Layout 3: context["metrics"]
    if "metrics" in context and isinstance(context["metrics"], dict):
        micro_sources.append(context["metrics"])

    # Layout 4: direct keys
    micro_sources.append(context)

    # Extract fields with fallback chain
    def get_field(field_name: str) -> Optional[float]:
        for source in micro_sources:
            if field_name in source:
                val = _safe_float(source[field_name])
                if val is not None:
                    return val
        return None

    # Build MicrostructureMetrics
    metrics = MicrostructureMetrics(
        spread_pct=get_field("spread_pct"),
        slippage_estimate_pct=get_field("slippage_estimate_pct"),
        order_book_depth_notional=get_field("order_book_depth_notional"),
        adv_notional=get_field("adv_notional"),
        last_price=get_field("last_price"),
        realized_vol_pct=get_field("realized_vol_pct"),
        timestamp_utc=None,  # string field, handle separately
    )

    # Handle timestamp (string field)
    for source in micro_sources:
        if "timestamp_utc" in source:
            ts = source["timestamp_utc"]
            if isinstance(ts, str) and ts:
                metrics.timestamp_utc = ts
                break

    return metrics


def micro_metrics_to_dict(metrics: MicrostructureMetrics) -> dict:
    """
    Stable serialization of MicrostructureMetrics.

    Guarantees:
    - Deterministic key order (alphabetical via dataclass asdict)
    - JSON-serializable (float, str, None only)
    - None values preserved (not filtered)

    Args:
        metrics: MicrostructureMetrics instance

    Returns:
        Dictionary with stable key order
    """
    # asdict preserves field order from dataclass definition
    result = asdict(metrics)

    # Ensure deterministic order (alphabetical)
    return dict(sorted(result.items()))
