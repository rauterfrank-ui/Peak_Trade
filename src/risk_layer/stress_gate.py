"""
Stress Testing Gate Layer
==========================

Scenario-based stress testing gate for portfolio risk assessment.

Applies deterministic stress scenarios to portfolio positions
and evaluates worst-case losses against configured thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

import pandas as pd
import numpy as np

from src.core.peak_config import PeakConfig


@dataclass(frozen=True)
class StressScenario:
    """
    Definition of a stress scenario.

    Attributes:
        name: Scenario identifier (e.g., "equity_down_5pct")
        description: Human-readable description
        shock_type: Type of shock ("return_shift", "vol_spike")
        shock_params: Parameters for the shock
    """

    name: str
    description: str
    shock_type: Literal["return_shift", "vol_spike"]
    shock_params: dict


@dataclass(frozen=True)
class StressGateStatus:
    """
    Status of Stress Gate evaluation.

    Attributes:
        severity: OK (passed), WARN (near limit), BLOCK (exceeded limit)
        reason: Human-readable reason
        worst_case_loss_pct: Worst-case loss across all scenarios (e.g., -0.045 = -4.5%)
        threshold_block: Block threshold
        threshold_warn: Warning threshold (optional)
        triggered_scenarios: List of scenario names that contributed to worst case
        scenarios_evaluated: Total number of scenarios evaluated
        inputs_available: Whether required inputs were available
        timestamp_utc: ISO8601 timestamp
    """

    severity: Literal["OK", "WARN", "BLOCK"]
    reason: str
    worst_case_loss_pct: float | None = None
    threshold_block: float | None = None
    threshold_warn: float | None = None
    triggered_scenarios: list[str] = field(default_factory=list)
    scenarios_evaluated: int = 0
    inputs_available: bool = False
    timestamp_utc: str = ""


class StressGate:
    """
    Stress Testing Gate for portfolio risk evaluation.

    Evaluates portfolio stress scenarios against configured thresholds.
    Safe defaults: missing data → OK (not applicable).

    Config keys:
        risk.stress_gate.enabled (bool): Enable/disable gate (default: True)
        risk.stress_gate.max_stress_loss_pct (float): Block threshold (default: 0.04 = 4%)
        risk.stress_gate.warn_stress_loss_pct (float|None): Warning threshold (default: None)
        risk.stress_gate.scenarios (list): List of scenario definitions
    """

    def __init__(self, cfg: PeakConfig) -> None:
        """
        Initialize Stress Gate.

        Args:
            cfg: PeakConfig instance
        """
        self.cfg = cfg

        # Read config
        self.enabled = cfg.get("risk.stress_gate.enabled", True)
        self.max_stress_loss_pct = cfg.get("risk.stress_gate.max_stress_loss_pct", 0.04)
        self.warn_stress_loss_pct = cfg.get("risk.stress_gate.warn_stress_loss_pct", None)

        # Load scenarios from config
        self.scenarios = self._load_scenarios()

        # Internal state
        self._last_status: StressGateStatus | None = None

    def _load_scenarios(self) -> list[StressScenario]:
        """
        Load stress scenarios from config.

        Returns:
            List of StressScenario objects
        """
        scenarios_cfg = self.cfg.get("risk.stress_gate.scenarios", [])

        scenarios = []
        for sc in scenarios_cfg:
            if not isinstance(sc, dict):
                continue

            name = sc.get("name", "unknown")
            description = sc.get("description", "")
            shock_type = sc.get("shock_type", "return_shift")
            shock_params = sc.get("shock_params", {})

            scenarios.append(
                StressScenario(
                    name=name,
                    description=description,
                    shock_type=shock_type,
                    shock_params=shock_params,
                )
            )

        # If no scenarios configured, use defaults
        if not scenarios:
            scenarios = self._default_scenarios()

        return scenarios

    def _default_scenarios(self) -> list[StressScenario]:
        """
        Default stress scenarios if none configured.

        Returns:
            List of default StressScenario objects
        """
        return [
            StressScenario(
                name="equity_down_5pct",
                description="5% equity market decline",
                shock_type="return_shift",
                shock_params={"shift": -0.05},
            ),
            StressScenario(
                name="equity_down_10pct",
                description="10% equity market decline",
                shock_type="return_shift",
                shock_params={"shift": -0.10},
            ),
            StressScenario(
                name="vol_spike",
                description="Volatility spike (2x normal)",
                shock_type="vol_spike",
                shock_params={"multiplier": 2.0},
            ),
        ]

    def evaluate(self, context: dict | None = None) -> StressGateStatus:
        """
        Evaluate stress scenarios against thresholds.

        Args:
            context: Context dict with portfolio data
                Expected keys:
                - returns_df: pd.DataFrame with asset returns
                - weights: dict or array with portfolio weights

        Returns:
            StressGateStatus with evaluation result

        Safe behavior:
            - If disabled → OK
            - If missing inputs → OK (not applicable)
            - If calculation fails → OK (safe default, logged)
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # If disabled, return OK
        if not self.enabled:
            status = StressGateStatus(
                severity="OK",
                reason="Stress gate disabled",
                threshold_block=self.max_stress_loss_pct,
                threshold_warn=self.warn_stress_loss_pct,
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
            status = StressGateStatus(
                severity="OK",
                reason="Stress test not applicable (missing returns or weights)",
                threshold_block=self.max_stress_loss_pct,
                threshold_warn=self.warn_stress_loss_pct,
                inputs_available=False,
                timestamp_utc=timestamp,
            )
            self._last_status = status
            return status

        # Validate inputs
        if not isinstance(returns_df, pd.DataFrame):
            status = StressGateStatus(
                severity="OK",
                reason="Stress test not applicable (invalid returns_df type)",
                threshold_block=self.max_stress_loss_pct,
                threshold_warn=self.warn_stress_loss_pct,
                inputs_available=False,
                timestamp_utc=timestamp,
            )
            self._last_status = status
            return status

        # Run stress scenarios
        try:
            worst_case_loss_pct, triggered_scenarios = self._run_stress_tests(returns_df, weights)
        except Exception as e:
            # Safe default: if calculation fails, allow (but log)
            import logging

            logging.getLogger(__name__).warning(
                f"Stress test calculation failed: {e}. Allowing order (safe default)."
            )
            status = StressGateStatus(
                severity="OK",
                reason=f"Stress test calculation failed: {str(e)[:100]}",
                threshold_block=self.max_stress_loss_pct,
                threshold_warn=self.warn_stress_loss_pct,
                inputs_available=True,
                timestamp_utc=timestamp,
            )
            self._last_status = status
            return status

        # Evaluate thresholds (worst_case_loss_pct is negative, e.g., -0.045)
        # Compare against negative thresholds (e.g., -0.04)
        if worst_case_loss_pct <= -self.max_stress_loss_pct:
            # BLOCK: loss exceeds limit
            status = StressGateStatus(
                severity="BLOCK",
                reason=f"Stress loss {worst_case_loss_pct:.2%} exceeds limit {-self.max_stress_loss_pct:.2%}",
                worst_case_loss_pct=worst_case_loss_pct,
                threshold_block=self.max_stress_loss_pct,
                threshold_warn=self.warn_stress_loss_pct,
                triggered_scenarios=triggered_scenarios,
                scenarios_evaluated=len(self.scenarios),
                inputs_available=True,
                timestamp_utc=timestamp,
            )
        elif (
            self.warn_stress_loss_pct is not None
            and worst_case_loss_pct <= -self.warn_stress_loss_pct
        ):
            # WARN: loss near limit
            status = StressGateStatus(
                severity="WARN",
                reason=f"Stress loss {worst_case_loss_pct:.2%} near limit (warn threshold {-self.warn_stress_loss_pct:.2%})",
                worst_case_loss_pct=worst_case_loss_pct,
                threshold_block=self.max_stress_loss_pct,
                threshold_warn=self.warn_stress_loss_pct,
                triggered_scenarios=triggered_scenarios,
                scenarios_evaluated=len(self.scenarios),
                inputs_available=True,
                timestamp_utc=timestamp,
            )
        else:
            # OK: within limits
            status = StressGateStatus(
                severity="OK",
                reason=f"Stress loss {worst_case_loss_pct:.2%} within limits",
                worst_case_loss_pct=worst_case_loss_pct,
                threshold_block=self.max_stress_loss_pct,
                threshold_warn=self.warn_stress_loss_pct,
                triggered_scenarios=triggered_scenarios,
                scenarios_evaluated=len(self.scenarios),
                inputs_available=True,
                timestamp_utc=timestamp,
            )

        self._last_status = status
        return status

    def _run_stress_tests(
        self, returns_df: pd.DataFrame, weights: dict | list
    ) -> tuple[float, list[str]]:
        """
        Run all stress scenarios and return worst case.

        Args:
            returns_df: DataFrame with asset returns
            weights: Portfolio weights (dict or list)

        Returns:
            Tuple of (worst_case_loss_pct, triggered_scenario_names)

        Raises:
            Exception: If calculation fails
        """
        # Convert weights to array aligned with returns_df columns
        weights_array = self._weights_to_array(returns_df, weights)

        worst_case_loss = 0.0  # Best case is no loss
        worst_scenarios = []

        for scenario in self.scenarios:
            # Apply scenario to returns
            stressed_returns = self._apply_scenario(returns_df, scenario)

            # Calculate portfolio loss under scenario
            # Simple approach: dot product of weights and mean stressed returns
            portfolio_loss = self._calculate_portfolio_loss(stressed_returns, weights_array)

            # Track worst case (most negative)
            if portfolio_loss < worst_case_loss:
                worst_case_loss = portfolio_loss
                worst_scenarios = [scenario.name]
            elif portfolio_loss == worst_case_loss and portfolio_loss < 0:
                worst_scenarios.append(scenario.name)

        return worst_case_loss, worst_scenarios

    def _weights_to_array(self, returns_df: pd.DataFrame, weights: dict | list) -> np.ndarray:
        """
        Convert weights to numpy array aligned with returns_df columns.

        Args:
            returns_df: DataFrame with asset returns
            weights: Portfolio weights (dict or list)

        Returns:
            Numpy array of weights aligned with returns_df columns
        """
        if isinstance(weights, dict):
            # Align dict weights with returns columns
            weights_array = np.array([weights.get(col, 0.0) for col in returns_df.columns])
        else:
            # Assume list/array is already aligned
            weights_array = np.array(weights)

        return weights_array

    def _apply_scenario(self, returns_df: pd.DataFrame, scenario: StressScenario) -> pd.DataFrame:
        """
        Apply stress scenario to returns.

        Args:
            returns_df: Original returns DataFrame
            scenario: Stress scenario to apply

        Returns:
            Stressed returns DataFrame
        """
        if scenario.shock_type == "return_shift":
            # Shift returns by fixed amount
            shift = scenario.shock_params.get("shift", 0.0)
            return returns_df + shift

        elif scenario.shock_type == "vol_spike":
            # Scale returns to increase volatility
            multiplier = scenario.shock_params.get("multiplier", 1.0)
            mean_returns = returns_df.mean()
            demeaned = returns_df - mean_returns
            scaled = demeaned * multiplier
            return scaled + mean_returns

        else:
            # Unknown shock type, return original
            return returns_df

    def _calculate_portfolio_loss(
        self, stressed_returns: pd.DataFrame, weights_array: np.ndarray
    ) -> float:
        """
        Calculate portfolio loss under stressed returns.

        Args:
            stressed_returns: Stressed returns DataFrame
            weights_array: Portfolio weights array

        Returns:
            Portfolio loss as percentage (negative value)
        """
        # Simple approach: weighted average of mean returns
        # This gives expected loss under scenario
        mean_stressed_returns = stressed_returns.mean(axis=0).values
        portfolio_loss = np.dot(weights_array, mean_stressed_returns)

        return float(portfolio_loss)

    @property
    def last_status(self) -> StressGateStatus | None:
        """
        Get last evaluation status.

        Returns:
            Last StressGateStatus or None if not yet evaluated
        """
        return self._last_status


def status_to_dict(status: StressGateStatus) -> dict:
    """
    Convert StressGateStatus to dict for audit logs.

    Args:
        status: StressGateStatus instance

    Returns:
        Dict with stable key order
    """
    return {
        "severity": status.severity,
        "reason": status.reason,
        "worst_case_loss_pct": status.worst_case_loss_pct,
        "threshold_block": status.threshold_block,
        "threshold_warn": status.threshold_warn,
        "triggered_scenarios": status.triggered_scenarios,
        "scenarios_evaluated": status.scenarios_evaluated,
        "inputs_available": status.inputs_available,
        "timestamp_utc": status.timestamp_utc,
    }
