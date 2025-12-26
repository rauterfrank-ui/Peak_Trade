"""
Liquidity Gate - Pre-Trade Microstructure Guards

Protects against adverse execution conditions:
- Wide spreads
- High slippage estimates
- Insufficient order book depth
- Order size too large vs average daily volume

Design:
- Safe defaults (missing metrics → OK, not BLOCK)
- Optional require_micro_metrics for warnings
- Stricter thresholds for market orders
- Limit order exception for wide spreads (configurable)
- Deterministic, audit-stable evaluation
"""

from dataclasses import dataclass, asdict
from typing import Any, Optional
from enum import Enum
import logging
from datetime import datetime, timezone

from .micro_metrics import extract_micro_metrics, micro_metrics_to_dict, MicrostructureMetrics

logger = logging.getLogger(__name__)


class LiquiditySeverity(str, Enum):
    """Severity levels for liquidity gate evaluation."""

    OK = "OK"
    WARN = "WARN"
    BLOCK = "BLOCK"


@dataclass
class LiquidityGateConfig:
    """
    Configuration for Liquidity Gate.

    Safe defaults assume equities; crypto/research should override.
    """

    # Gate control
    enabled: bool = False
    require_micro_metrics: bool = False  # Warn if metrics missing

    # Spread thresholds
    max_spread_pct: float = 0.005  # 0.5% (EQUITY default)
    warn_spread_pct: Optional[float] = None  # Optional warning level

    # Slippage thresholds
    max_slippage_estimate_pct: float = 0.01  # 1%
    warn_slippage_estimate_pct: Optional[float] = None

    # Depth requirements
    min_book_depth_multiple: float = 1.5  # depth >= order_notional * multiple

    # Order size vs volume
    max_order_to_adv_pct: float = 0.02  # 2% of average daily volume

    # Order type policy
    strict_for_market_orders: bool = True  # Market orders use stricter (0.7x) thresholds
    allow_limit_orders_when_spread_wide: bool = True  # Limit orders exempt from spread BLOCK

    # Metadata
    profile_name: str = "default"
    notes: str = ""


@dataclass
class LiquidityGateStatus:
    """
    Result of liquidity gate evaluation.

    Always present in audit trail (even when disabled).
    """

    enabled: bool
    severity: LiquiditySeverity
    reason: str
    triggered_by: list[str]
    micro_metrics_snapshot: dict
    order_snapshot: dict
    thresholds_snapshot: dict
    timestamp_utc: str


class LiquidityGate:
    """
    Pre-trade liquidity and slippage guard.

    Evaluates orders against microstructure metrics to prevent
    execution in adverse market conditions.
    """

    def __init__(self, config: LiquidityGateConfig):
        """
        Initialize LiquidityGate.

        Args:
            config: LiquidityGateConfig instance
        """
        self.config = config
        logger.info(
            f"LiquidityGate initialized: enabled={config.enabled}, "
            f"profile={config.profile_name}, "
            f"strict_market={config.strict_for_market_orders}"
        )

    def evaluate(self, order: dict, context: dict) -> LiquidityGateStatus:
        """
        Evaluate order against liquidity constraints.

        Args:
            order: Order dictionary with keys: symbol, side, quantity, order_type, limit_price (optional)
            context: Market context with microstructure metrics

        Returns:
            LiquidityGateStatus with evaluation result
        """
        timestamp_utc = datetime.now(timezone.utc).isoformat()

        # Extract metrics
        metrics = extract_micro_metrics(context)
        metrics_dict = micro_metrics_to_dict(metrics)

        # Build stable order snapshot
        order_snapshot = self._build_order_snapshot(order)

        # If disabled, return OK immediately
        if not self.config.enabled:
            return LiquidityGateStatus(
                enabled=False,
                severity=LiquiditySeverity.OK,
                reason="Liquidity gate disabled",
                triggered_by=[],
                micro_metrics_snapshot=metrics_dict,
                order_snapshot=order_snapshot,
                thresholds_snapshot=self._build_thresholds_snapshot(),
                timestamp_utc=timestamp_utc,
            )

        # Run evaluation logic
        return self._evaluate_enabled(order, order_snapshot, metrics, metrics_dict, timestamp_utc)

    def _evaluate_enabled(
        self,
        order: dict,
        order_snapshot: dict,
        metrics: MicrostructureMetrics,
        metrics_dict: dict,
        timestamp_utc: str,
    ) -> LiquidityGateStatus:
        """
        Core evaluation logic when gate is enabled.

        Args:
            order: Original order dict
            order_snapshot: Stable order snapshot
            metrics: Extracted MicrostructureMetrics
            metrics_dict: Serialized metrics for audit
            timestamp_utc: ISO timestamp

        Returns:
            LiquidityGateStatus
        """
        triggered_by = []
        severity = LiquiditySeverity.OK
        reasons = []

        # Determine if market order
        is_market_order = order.get("order_type", "").upper() == "MARKET"
        is_limit_order = order.get("order_type", "").upper() == "LIMIT"

        # Calculate order notional
        order_notional = self._calculate_order_notional(order, metrics)

        # Check if metrics are missing
        metrics_missing = self._check_metrics_missing(metrics)
        if metrics_missing and self.config.require_micro_metrics:
            triggered_by.append("missing_micro_metrics")
            severity = LiquiditySeverity.WARN
            reasons.append("Required microstructure metrics missing")

        # Spread check
        spread_result = self._check_spread(metrics.spread_pct, is_market_order, is_limit_order)
        if spread_result:
            triggered_by.append("spread")
            if spread_result["severity"] == "BLOCK" and severity != LiquiditySeverity.BLOCK:
                severity = LiquiditySeverity.BLOCK
            elif spread_result["severity"] == "WARN" and severity == LiquiditySeverity.OK:
                severity = LiquiditySeverity.WARN
            reasons.append(spread_result["reason"])

        # Slippage check
        slippage_result = self._check_slippage(metrics.slippage_estimate_pct, is_market_order)
        if slippage_result:
            triggered_by.append("slippage")
            if slippage_result["severity"] == "BLOCK":
                severity = LiquiditySeverity.BLOCK
            elif slippage_result["severity"] == "WARN" and severity == LiquiditySeverity.OK:
                severity = LiquiditySeverity.WARN
            reasons.append(slippage_result["reason"])

        # Depth check
        depth_result = self._check_depth(metrics.order_book_depth_notional, order_notional)
        if depth_result:
            triggered_by.append("depth")
            severity = LiquiditySeverity.BLOCK
            reasons.append(depth_result["reason"])

        # Order to ADV check
        adv_result = self._check_order_to_adv(order_notional, metrics.adv_notional)
        if adv_result:
            triggered_by.append("order_to_adv")
            severity = LiquiditySeverity.BLOCK
            reasons.append(adv_result["reason"])

        # Build final reason
        if not reasons:
            reason = "All liquidity checks passed"
        else:
            reason = "; ".join(reasons)

        return LiquidityGateStatus(
            enabled=True,
            severity=severity,
            reason=reason,
            triggered_by=triggered_by,
            micro_metrics_snapshot=metrics_dict,
            order_snapshot=order_snapshot,
            thresholds_snapshot=self._build_thresholds_snapshot(),
            timestamp_utc=timestamp_utc,
        )

    def _check_metrics_missing(self, metrics: MicrostructureMetrics) -> bool:
        """Check if critical metrics are missing."""
        return all(
            [
                metrics.spread_pct is None,
                metrics.slippage_estimate_pct is None,
                metrics.order_book_depth_notional is None,
                metrics.adv_notional is None,
            ]
        )

    def _check_spread(
        self, spread_pct: Optional[float], is_market: bool, is_limit: bool
    ) -> Optional[dict]:
        """
        Check spread against thresholds.

        Returns:
            dict with severity and reason, or None if OK
        """
        if spread_pct is None:
            return None

        # Determine threshold (stricter for market orders)
        max_threshold = self.config.max_spread_pct
        if is_market and self.config.strict_for_market_orders:
            max_threshold *= 0.7

        # Check BLOCK condition (with limit order exception)
        if spread_pct >= max_threshold:
            if is_limit and self.config.allow_limit_orders_when_spread_wide:
                # Downgrade to WARN for limit orders
                return {
                    "severity": "WARN",
                    "reason": f"Spread {spread_pct:.4f} >= {max_threshold:.4f} (limit order allowed)",
                }
            else:
                return {
                    "severity": "BLOCK",
                    "reason": f"Spread {spread_pct:.4f} >= {max_threshold:.4f}",
                }

        # Check WARN condition
        if self.config.warn_spread_pct and spread_pct >= self.config.warn_spread_pct:
            return {
                "severity": "WARN",
                "reason": f"Spread {spread_pct:.4f} >= warn threshold {self.config.warn_spread_pct:.4f}",
            }

        return None

    def _check_slippage(self, slippage_pct: Optional[float], is_market: bool) -> Optional[dict]:
        """Check slippage estimate against thresholds."""
        if slippage_pct is None:
            return None

        # Stricter for market orders
        max_threshold = self.config.max_slippage_estimate_pct
        if is_market and self.config.strict_for_market_orders:
            max_threshold *= 0.7

        if slippage_pct >= max_threshold:
            return {
                "severity": "BLOCK",
                "reason": f"Slippage estimate {slippage_pct:.4f} >= {max_threshold:.4f}",
            }

        if (
            self.config.warn_slippage_estimate_pct
            and slippage_pct >= self.config.warn_slippage_estimate_pct
        ):
            return {
                "severity": "WARN",
                "reason": f"Slippage estimate {slippage_pct:.4f} >= warn threshold {self.config.warn_slippage_estimate_pct:.4f}",
            }

        return None

    def _check_depth(
        self, depth_notional: Optional[float], order_notional: Optional[float]
    ) -> Optional[dict]:
        """Check if order book depth is sufficient."""
        if depth_notional is None or order_notional is None or order_notional <= 0:
            return None

        required_depth = order_notional * self.config.min_book_depth_multiple

        if depth_notional < required_depth:
            return {
                "severity": "BLOCK",
                "reason": f"Insufficient depth: {depth_notional:.2f} < required {required_depth:.2f} ({self.config.min_book_depth_multiple}x order)",
            }

        return None

    def _check_order_to_adv(
        self, order_notional: Optional[float], adv_notional: Optional[float]
    ) -> Optional[dict]:
        """Check if order is too large relative to average daily volume."""
        if order_notional is None or adv_notional is None or adv_notional <= 0:
            return None

        order_to_adv = order_notional / adv_notional

        if order_to_adv > self.config.max_order_to_adv_pct:
            return {
                "severity": "BLOCK",
                "reason": f"Order too large: {order_to_adv:.4f} ({order_to_adv * 100:.2f}%) of ADV exceeds {self.config.max_order_to_adv_pct * 100:.2f}%",
            }

        return None

    def _calculate_order_notional(
        self, order: dict, metrics: MicrostructureMetrics
    ) -> Optional[float]:
        """
        Calculate order notional value.

        Uses limit_price if available, else last_price from metrics.
        """
        qty = order.get("quantity", 0)
        if qty == 0:
            return None

        # Use limit price if available
        price = order.get("limit_price")
        if price is None:
            price = metrics.last_price

        if price is None or price <= 0:
            return None

        return abs(float(qty)) * float(price)

    def _build_order_snapshot(self, order: dict) -> dict:
        """
        Build deterministic order snapshot for audit.

        Only includes primitive values, sorted keys.
        """
        # Handle non-dict orders gracefully
        if not isinstance(order, dict):
            return {
                "_type": type(order).__name__,
                "_repr": str(order),
            }

        snapshot = {
            "symbol": order.get("symbol", ""),
            "side": order.get("side", ""),
            "quantity": float(order.get("quantity", 0)),
            "order_type": order.get("order_type", ""),
        }

        if "limit_price" in order:
            snapshot["limit_price"] = float(order["limit_price"])

        return dict(sorted(snapshot.items()))

    def _build_thresholds_snapshot(self) -> dict:
        """Build deterministic thresholds snapshot for audit."""
        thresholds = {
            "max_spread_pct": self.config.max_spread_pct,
            "warn_spread_pct": self.config.warn_spread_pct,
            "max_slippage_estimate_pct": self.config.max_slippage_estimate_pct,
            "warn_slippage_estimate_pct": self.config.warn_slippage_estimate_pct,
            "min_book_depth_multiple": self.config.min_book_depth_multiple,
            "max_order_to_adv_pct": self.config.max_order_to_adv_pct,
            "strict_for_market_orders": self.config.strict_for_market_orders,
            "allow_limit_orders_when_spread_wide": self.config.allow_limit_orders_when_spread_wide,
            "profile_name": self.config.profile_name,
        }
        return dict(sorted(thresholds.items()))


def liquidity_gate_status_to_dict(status: LiquidityGateStatus) -> dict:
    """
    Convert LiquidityGateStatus to stable dict for audit.

    Args:
        status: LiquidityGateStatus instance

    Returns:
        Dictionary with sorted keys
    """
    result = {
        "enabled": status.enabled,
        "severity": status.severity.value,
        "reason": status.reason,
        "triggered_by": sorted(status.triggered_by),
        "micro_metrics_snapshot": status.micro_metrics_snapshot,
        "order_snapshot": status.order_snapshot,
        "thresholds": status.thresholds_snapshot,
        "timestamp_utc": status.timestamp_utc,
    }
    return dict(sorted(result.items()))
