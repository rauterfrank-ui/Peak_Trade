"""
VaR Gate Layer
==============

Value-at-Risk evaluation gate for portfolio risk assessment.

Integrates with existing VaR calculations from src/risk/portfolio_var.py
and provides a gate interface for RiskGate orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

import pandas as pd

from src.core.peak_config import PeakConfig


@dataclass(frozen=True)
class VaRGateStatus:
    """
    Status of VaR Gate evaluation.

    Attributes:
        severity: OK (passed), WARN (near limit), BLOCK (exceeded limit)
        reason: Human-readable reason
        var_pct: Calculated VaR as percentage (e.g., 0.023 = 2.3%)
        threshold_block: Block threshold
        threshold_warn: Warning threshold (optional)
        confidence: Confidence level used
        horizon_days: Horizon in days
        method: VaR method used
        inputs_available: Whether required inputs were available
        timestamp_utc: ISO8601 timestamp
    """

    severity: Literal["OK", "WARN", "BLOCK"]
    reason: str
    var_pct: float | None = None
    threshold_block: float | None = None
    threshold_warn: float | None = None
    confidence: float | None = None
    horizon_days: int | None = None
    method: str | None = None
    inputs_available: bool = False
    timestamp_utc: str = ""


class VaRGate:
    """
    VaR Gate for portfolio risk evaluation.

    Evaluates portfolio VaR against configured thresholds.
    Safe defaults: missing data → OK (not applicable).

    Config keys:
        risk.var_gate.enabled (bool): Enable/disable gate (default: True)
        risk.var_gate.method (str): "parametric" or "historical" (default: "parametric")
        risk.var_gate.confidence (float): Confidence level (default: 0.95)
        risk.var_gate.horizon_days (int): Risk horizon (default: 1)
        risk.var_gate.max_var_pct (float): Block threshold (default: 0.03 = 3%)
        risk.var_gate.warn_var_pct (float|None): Warning threshold (default: None)
    """

    def __init__(self, cfg: PeakConfig) -> None:
        """
        Initialize VaR Gate.

        Args:
            cfg: PeakConfig instance
        """
        self.cfg = cfg

        # Read config
        self.enabled = cfg.get("risk.var_gate.enabled", True)
        self.method = cfg.get("risk.var_gate.method", "parametric")
        self.confidence = cfg.get("risk.var_gate.confidence", 0.95)
        self.horizon_days = cfg.get("risk.var_gate.horizon_days", 1)
        self.max_var_pct = cfg.get("risk.var_gate.max_var_pct", 0.03)
        self.warn_var_pct = cfg.get("risk.var_gate.warn_var_pct", None)

        # Validate method
        if self.method not in ("parametric", "historical"):
            raise ValueError(
                f"Invalid VaR method: {self.method}. Must be 'parametric' or 'historical'."
            )

        # Internal state
        self._last_status: VaRGateStatus | None = None

    def evaluate(self, context: dict | None = None) -> VaRGateStatus:
        """
        Evaluate VaR against thresholds.

        Args:
            context: Context dict with portfolio data
                Expected keys:
                - returns_df: pd.DataFrame with asset returns
                - weights: dict or array with portfolio weights
                - portfolio_value: float (optional, for absolute VaR)

        Returns:
            VaRGateStatus with evaluation result

        Safe behavior:
            - If disabled → OK
            - If missing inputs → OK (not applicable)
            - If calculation fails → OK (safe default, logged)
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # If disabled, return OK
        if not self.enabled:
            status = VaRGateStatus(
                severity="OK",
                reason="VaR gate disabled",
                threshold_block=self.max_var_pct,
                threshold_warn=self.warn_var_pct,
                confidence=self.confidence,
                horizon_days=self.horizon_days,
                method=self.method,
                inputs_available=False,
                timestamp_utc=timestamp,
            )
            self._last_status = status
            return status

        # Extract inputs from context
        if context is None:
            context = {}

        returns_df = context.get("returns_df")
        weights = context.get("weights")

        # Check if inputs available
        if returns_df is None or weights is None:
            status = VaRGateStatus(
                severity="OK",
                reason="VaR not applicable (missing returns or weights)",
                threshold_block=self.max_var_pct,
                threshold_warn=self.warn_var_pct,
                confidence=self.confidence,
                horizon_days=self.horizon_days,
                method=self.method,
                inputs_available=False,
                timestamp_utc=timestamp,
            )
            self._last_status = status
            return status

        # Validate inputs
        if not isinstance(returns_df, pd.DataFrame):
            status = VaRGateStatus(
                severity="OK",
                reason="VaR not applicable (invalid returns_df type)",
                threshold_block=self.max_var_pct,
                threshold_warn=self.warn_var_pct,
                confidence=self.confidence,
                horizon_days=self.horizon_days,
                method=self.method,
                inputs_available=False,
                timestamp_utc=timestamp,
            )
            self._last_status = status
            return status

        # Calculate VaR
        try:
            var_pct = self._calculate_var(returns_df, weights)
        except Exception as e:
            # Safe default: if calculation fails, allow (but log)
            import logging

            logging.getLogger(__name__).warning(
                f"VaR calculation failed: {e}. Allowing order (safe default)."
            )
            status = VaRGateStatus(
                severity="OK",
                reason=f"VaR calculation failed: {str(e)[:100]}",
                threshold_block=self.max_var_pct,
                threshold_warn=self.warn_var_pct,
                confidence=self.confidence,
                horizon_days=self.horizon_days,
                method=self.method,
                inputs_available=True,
                timestamp_utc=timestamp,
            )
            self._last_status = status
            return status

        # Evaluate thresholds
        if var_pct >= self.max_var_pct:
            # BLOCK
            status = VaRGateStatus(
                severity="BLOCK",
                reason=f"VaR {var_pct:.2%} exceeds limit {self.max_var_pct:.2%}",
                var_pct=var_pct,
                threshold_block=self.max_var_pct,
                threshold_warn=self.warn_var_pct,
                confidence=self.confidence,
                horizon_days=self.horizon_days,
                method=self.method,
                inputs_available=True,
                timestamp_utc=timestamp,
            )
        elif self.warn_var_pct is not None and var_pct >= self.warn_var_pct:
            # WARN
            status = VaRGateStatus(
                severity="WARN",
                reason=f"VaR {var_pct:.2%} near limit (warn threshold {self.warn_var_pct:.2%})",
                var_pct=var_pct,
                threshold_block=self.max_var_pct,
                threshold_warn=self.warn_var_pct,
                confidence=self.confidence,
                horizon_days=self.horizon_days,
                method=self.method,
                inputs_available=True,
                timestamp_utc=timestamp,
            )
        else:
            # OK
            status = VaRGateStatus(
                severity="OK",
                reason=f"VaR {var_pct:.2%} within limits",
                var_pct=var_pct,
                threshold_block=self.max_var_pct,
                threshold_warn=self.warn_var_pct,
                confidence=self.confidence,
                horizon_days=self.horizon_days,
                method=self.method,
                inputs_available=True,
                timestamp_utc=timestamp,
            )

        self._last_status = status
        return status

    def _calculate_var(self, returns_df: pd.DataFrame, weights: dict | list) -> float:
        """
        Calculate VaR using configured method.

        Args:
            returns_df: DataFrame with asset returns
            weights: Portfolio weights (dict or list)

        Returns:
            VaR as percentage (e.g., 0.023 = 2.3%)

        Raises:
            Exception: If calculation fails
        """
        # Import VaR functions from existing module
        from src.risk.portfolio_var import historical_var, parametric_var

        if self.method == "parametric":
            var_pct = parametric_var(
                returns_df=returns_df,
                weights=weights,
                confidence=self.confidence,
                horizon_days=self.horizon_days,
                use_mean=False,  # Conservative: ignore drift
            )
        elif self.method == "historical":
            var_pct = historical_var(
                returns_df=returns_df,
                weights=weights,
                confidence=self.confidence,
                horizon_days=self.horizon_days,
            )
        else:
            raise ValueError(f"Unknown VaR method: {self.method}")

        return float(var_pct)

    @property
    def last_status(self) -> VaRGateStatus | None:
        """
        Get last evaluation status.

        Returns:
            Last VaRGateStatus or None if not yet evaluated
        """
        return self._last_status


def status_to_dict(status: VaRGateStatus) -> dict:
    """
    Convert VaRGateStatus to dict for audit logs.

    Args:
        status: VaRGateStatus instance

    Returns:
        Dict with stable key order
    """
    return {
        "severity": status.severity,
        "reason": status.reason,
        "var_pct": status.var_pct,
        "threshold_block": status.threshold_block,
        "threshold_warn": status.threshold_warn,
        "confidence": status.confidence,
        "horizon_days": status.horizon_days,
        "method": status.method,
        "inputs_available": status.inputs_available,
        "timestamp_utc": status.timestamp_utc,
    }
