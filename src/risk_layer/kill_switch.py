"""
Kill Switch Layer
==================

Emergency safety stop for trading decisions based on risk thresholds.

The KillSwitch can block all trading when critical thresholds are exceeded:
- Daily loss limit
- Maximum drawdown
- Excessive volatility (optional)

Once armed, the KillSwitch remains sticky until explicitly reset.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from src.core.peak_config import PeakConfig
from src.risk_layer.metrics import RiskMetrics, metrics_to_dict
from src.risk_layer.models import Violation


@dataclass(frozen=True)
class KillSwitchStatus:
    """
    Status of the KillSwitch.

    Attributes:
        armed: Whether the kill switch is armed (blocks trading)
        severity: Severity level (OK when not armed, BLOCK when armed)
        reason: Human-readable reason for the status
        triggered_by: List of conditions that triggered the kill switch
        metrics_snapshot: Snapshot of metrics at evaluation time
        timestamp_utc: ISO8601 timestamp when status was determined
    """

    armed: bool
    severity: Literal["OK", "WARN", "BLOCK"]
    reason: str
    triggered_by: list[str] = field(default_factory=list)
    metrics_snapshot: dict = field(default_factory=dict)
    timestamp_utc: str = ""


class KillSwitchLayer:
    """
    Kill Switch safety layer.

    Monitors risk metrics and arms when thresholds are exceeded.
    Once armed, remains armed until explicitly reset.
    """

    def __init__(self, cfg: PeakConfig) -> None:
        """
        Initialize kill switch with config.

        Args:
            cfg: PeakConfig instance

        Config keys:
            risk.kill_switch.enabled (bool): Enable/disable kill switch (default: True)
            risk.kill_switch.daily_loss_limit_pct (float): Daily loss threshold (default: 0.05 = 5%)
            risk.kill_switch.max_drawdown_pct (float): Max drawdown threshold (default: 0.20 = 20%)
            risk.kill_switch.max_volatility_pct (float|None): Max volatility threshold (default: None)
        """
        self.cfg = cfg

        # Read config
        self.enabled = cfg.get("risk.kill_switch.enabled", True)
        self.daily_loss_limit_pct = cfg.get("risk.kill_switch.daily_loss_limit_pct", 0.05)
        self.max_drawdown_pct = cfg.get("risk.kill_switch.max_drawdown_pct", 0.20)
        self.max_volatility_pct = cfg.get("risk.kill_switch.max_volatility_pct", None)

        # Internal state
        self._armed = False
        self._last_status: KillSwitchStatus | None = None

    def evaluate(self, metrics: RiskMetrics | dict) -> KillSwitchStatus:
        """
        Evaluate metrics against thresholds.

        Args:
            metrics: RiskMetrics instance or dict with risk metrics
                - daily_pnl_pct (float): Daily PnL as percentage (e.g., -0.06 for -6%)
                - current_drawdown_pct (float): Current drawdown as percentage (e.g., 0.21 for 21%)
                - realized_vol_pct (float, optional): Realized volatility as percentage

        Returns:
            KillSwitchStatus indicating if kill switch is armed
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Convert to dict for snapshot (stable order)
        if isinstance(metrics, RiskMetrics):
            metrics_snapshot = metrics_to_dict(metrics)
            daily_pnl_pct = metrics.daily_pnl_pct
            current_drawdown_pct = metrics.current_drawdown_pct
            realized_vol_pct = metrics.realized_vol_pct
        else:
            # Legacy dict support (backwards compatibility)
            metrics_snapshot = dict(metrics) if metrics else {}
            daily_pnl_pct = metrics.get("daily_pnl_pct") if metrics else None
            current_drawdown_pct = metrics.get("current_drawdown_pct") if metrics else None
            realized_vol_pct = metrics.get("realized_vol_pct") if metrics else None

        # If disabled, always return OK
        if not self.enabled:
            status = KillSwitchStatus(
                armed=False,
                severity="OK",
                reason="Kill switch disabled",
                triggered_by=[],
                metrics_snapshot=metrics_snapshot,
                timestamp_utc=timestamp,
            )
            self._last_status = status
            return status

        # If already armed, stay armed (sticky)
        if self._armed:
            status = KillSwitchStatus(
                armed=True,
                severity="BLOCK",
                reason=self._last_status.reason if self._last_status else "Armed",
                triggered_by=(self._last_status.triggered_by if self._last_status else []),
                metrics_snapshot=metrics_snapshot,
                timestamp_utc=timestamp,
            )
            self._last_status = status
            return status

        # Check thresholds
        triggered_by: list[str] = []
        reasons: list[str] = []

        # Daily loss check
        if daily_pnl_pct is not None:
            if daily_pnl_pct <= -self.daily_loss_limit_pct:
                triggered_by.append("daily_loss_limit")
                reasons.append(
                    f"Daily loss {daily_pnl_pct:.1%} exceeded limit {-self.daily_loss_limit_pct:.1%}"
                )

        # Drawdown check
        if current_drawdown_pct is not None:
            if current_drawdown_pct >= self.max_drawdown_pct:
                triggered_by.append("max_drawdown")
                reasons.append(
                    f"Drawdown {current_drawdown_pct:.1%} exceeded limit {self.max_drawdown_pct:.1%}"
                )

        # Volatility check (optional)
        if self.max_volatility_pct is not None:
            if realized_vol_pct is not None:
                if realized_vol_pct >= self.max_volatility_pct:
                    triggered_by.append("max_volatility")
                    reasons.append(
                        f"Volatility {realized_vol_pct:.1%} exceeded limit {self.max_volatility_pct:.1%}"
                    )

        # Determine status
        if triggered_by:
            self._armed = True
            status = KillSwitchStatus(
                armed=True,
                severity="BLOCK",
                reason="; ".join(reasons),
                triggered_by=triggered_by,
                metrics_snapshot=metrics_snapshot,
                timestamp_utc=timestamp,
            )
        else:
            status = KillSwitchStatus(
                armed=False,
                severity="OK",
                reason="All thresholds within limits",
                triggered_by=[],
                metrics_snapshot=metrics_snapshot,
                timestamp_utc=timestamp,
            )

        self._last_status = status
        return status

    def reset(self, reason: str = "manual_reset") -> KillSwitchStatus:
        """
        Reset the kill switch (disarm).

        Args:
            reason: Reason for reset

        Returns:
            New status after reset
        """
        self._armed = False
        timestamp = datetime.now(timezone.utc).isoformat()

        status = KillSwitchStatus(
            armed=False,
            severity="OK",
            reason=f"Reset: {reason}",
            triggered_by=[],
            metrics_snapshot={},
            timestamp_utc=timestamp,
        )
        self._last_status = status
        return status

    @property
    def is_armed(self) -> bool:
        """Check if kill switch is currently armed."""
        return self._armed

    @property
    def last_status(self) -> KillSwitchStatus | None:
        """
        Get the last known kill switch status.

        Returns:
            Last KillSwitchStatus from evaluate() or reset(), or None if not yet evaluated
        """
        return self._last_status


def to_violations(status: KillSwitchStatus) -> list[Violation]:
    """
    Convert KillSwitchStatus to Violation objects.

    Args:
        status: KillSwitchStatus to convert

    Returns:
        List of Violation objects (empty if not armed)
    """
    if not status.armed:
        return []

    return [
        Violation(
            code="KILL_SWITCH_ARMED",
            message=f"Kill switch armed: {status.reason}",
            severity="CRITICAL",
            details={
                "triggered_by": status.triggered_by,
                "metrics_snapshot": status.metrics_snapshot,
                "timestamp_utc": status.timestamp_utc,
            },
        )
    ]
