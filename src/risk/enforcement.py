"""
Peak_Trade Risk Layer - Risk Limit Enforcement
===============================================
Enforcement-Engine für Risk-Limits mit Circuit-Breaker-Semantik.

Classes:
- RiskLimitsV2: Definition von Portfolio-Risk-Limits
- RiskEnforcer: Evaluiert Limits und produziert RiskDecision

Features:
- Gross/Net Exposure Limits
- Position Weight Limits
- VaR/CVaR Limits
- Correlation Limits
- Circuit-Breaker: HARD Breaches -> Trading Halt
"""

from dataclasses import dataclass
from typing import Optional, List
import pandas as pd
import numpy as np
import logging

from .types import PortfolioSnapshot, RiskBreach, RiskDecision, BreachSeverity
from .portfolio import compute_gross_exposure, compute_net_exposure, compute_weights
from .var import historical_var, historical_cvar

logger = logging.getLogger(__name__)


@dataclass
class RiskLimitsV2:
    """
    Portfolio-Risk-Limits für v1-Layer.

    Alle Limits sind Optional (None = nicht geprüft).

    Attributes:
        max_gross_exposure: Max Gross Exposure als Fraction of Equity (z.B. 1.5 = 150%)
        max_net_exposure: Max Abs(Net Exposure) als Fraction of Equity (z.B. 1.0 = 100%)
        max_position_weight: Max Weight einer einzelnen Position (z.B. 0.35 = 35%)
        max_var: Max VaR als Fraction of Equity (z.B. 0.08 = 8%)
        max_cvar: Max CVaR als Fraction of Equity (z.B. 0.12 = 12%)
        max_corr: Max pairwise Korrelation (z.B. 0.95)
        alpha: Alpha für VaR/CVaR (default: 0.05)
        window: Rolling-Window für Returns (default: 252 = 1 Jahr)

    Example:
        >>> limits = RiskLimitsV2(
        ...     max_gross_exposure=1.5,
        ...     max_position_weight=0.35,
        ...     max_var=0.08,
        ...     alpha=0.05
        ... )
    """

    max_gross_exposure: Optional[float] = None
    max_net_exposure: Optional[float] = None
    max_position_weight: Optional[float] = None
    max_var: Optional[float] = None
    max_cvar: Optional[float] = None
    max_corr: Optional[float] = None
    alpha: float = 0.05
    window: int = 252

    def __post_init__(self) -> None:
        """Validiere Limits."""
        if self.alpha <= 0 or self.alpha >= 1:
            raise ValueError(f"alpha must be in (0,1), got {self.alpha}")
        if self.window <= 0:
            raise ValueError(f"window must be > 0, got {self.window}")


class RiskEnforcer:
    """
    Enforcement-Engine für Risk-Limits.

    Usage:
        >>> limits = RiskLimitsV2(max_gross_exposure=1.5, max_var=0.08)
        >>> enforcer = RiskEnforcer()
        >>> decision = enforcer.evaluate_portfolio(snapshot, returns, limits, alpha=0.05)
        >>> if not decision.allowed:
        ...     print(f"Trading HALTED: {decision.get_breach_summary()}")
    """

    def __init__(self) -> None:
        """Initialisiert RiskEnforcer."""
        pass

    def evaluate_portfolio(
        self,
        snapshot: PortfolioSnapshot,
        returns: Optional[pd.Series],
        limits: RiskLimitsV2,
        alpha: Optional[float] = None,
    ) -> RiskDecision:
        """
        Evaluiert Portfolio gegen Risk-Limits.

        Args:
            snapshot: Aktueller Portfolio-Snapshot
            returns: Rolling-Window-Returns für VaR/CVaR (optional)
            limits: Risk-Limits
            alpha: Override für limits.alpha (optional)

        Returns:
            RiskDecision mit allowed/breaches

        Notes:
            - Sammelt alle Breaches
            - HARD Breaches -> allowed=False, action="HALT"
            - Nur Warnings -> allowed=True, action="ALLOW"
        """
        alpha_used = alpha if alpha is not None else limits.alpha
        breaches: List[RiskBreach] = []

        # 1. Exposure Checks
        breaches.extend(self._check_exposures(snapshot, limits))

        # 2. Position Weight Checks
        breaches.extend(self._check_position_weights(snapshot, limits))

        # 3. VaR/CVaR Checks (nur wenn returns vorhanden)
        if returns is not None and not returns.empty:
            breaches.extend(self._check_var_cvar(returns, snapshot.equity, limits, alpha_used))

        # 4. Correlation Checks (noch nicht implementiert, optional)
        # breaches.extend(self._check_correlations(returns, limits))

        # Entscheidung treffen
        has_hard = any(b.severity == BreachSeverity.HARD for b in breaches)

        if has_hard:
            return RiskDecision(
                allowed=False,
                action="HALT",
                breaches=breaches,
                metadata={"reason": "HARD breach detected"},
            )
        elif breaches:
            return RiskDecision(
                allowed=True,
                action="ALLOW",
                breaches=breaches,
                metadata={"reason": "Only warnings, no hard breaches"},
            )
        else:
            return RiskDecision(
                allowed=True,
                action="ALLOW",
                breaches=[],
                metadata={"reason": "All limits OK"},
            )

    def _check_exposures(
        self,
        snapshot: PortfolioSnapshot,
        limits: RiskLimitsV2,
    ) -> List[RiskBreach]:
        """Prüft Gross/Net Exposure Limits."""
        breaches = []

        if snapshot.equity <= 0:
            breaches.append(
                RiskBreach(
                    code="INVALID_EQUITY",
                    message=f"Equity <= 0: {snapshot.equity:.2f}",
                    severity=BreachSeverity.HARD,
                    metrics={"equity": snapshot.equity},
                    timestamp=snapshot.timestamp,
                )
            )
            return breaches

        # Gross Exposure
        if limits.max_gross_exposure is not None:
            gross = compute_gross_exposure(snapshot.positions)
            gross_ratio = gross / snapshot.equity

            if gross_ratio > limits.max_gross_exposure:
                breaches.append(
                    RiskBreach(
                        code="MAX_GROSS_EXPOSURE",
                        message=(
                            f"Gross exposure {gross_ratio:.2%} exceeds limit "
                            f"{limits.max_gross_exposure:.2%}"
                        ),
                        severity=BreachSeverity.HARD,
                        metrics={
                            "gross_exposure": gross,
                            "gross_ratio": gross_ratio,
                            "limit": limits.max_gross_exposure,
                        },
                        timestamp=snapshot.timestamp,
                    )
                )

        # Net Exposure
        if limits.max_net_exposure is not None:
            net = compute_net_exposure(snapshot.positions)
            net_ratio = abs(net) / snapshot.equity

            if net_ratio > limits.max_net_exposure:
                breaches.append(
                    RiskBreach(
                        code="MAX_NET_EXPOSURE",
                        message=(
                            f"Net exposure {net_ratio:.2%} exceeds limit "
                            f"{limits.max_net_exposure:.2%}"
                        ),
                        severity=BreachSeverity.HARD,
                        metrics={
                            "net_exposure": net,
                            "net_ratio": net_ratio,
                            "limit": limits.max_net_exposure,
                        },
                        timestamp=snapshot.timestamp,
                    )
                )

        return breaches

    def _check_position_weights(
        self,
        snapshot: PortfolioSnapshot,
        limits: RiskLimitsV2,
    ) -> List[RiskBreach]:
        """Prüft einzelne Position Weights."""
        breaches = []

        if limits.max_position_weight is None:
            return breaches

        if snapshot.equity <= 0:
            return breaches  # Bereits in _check_exposures gemeldet

        weights = compute_weights(snapshot.positions, snapshot.equity)

        for symbol, weight in weights.items():
            if weight > limits.max_position_weight:
                breaches.append(
                    RiskBreach(
                        code="MAX_POSITION_WEIGHT",
                        message=(
                            f"Position {symbol} weight {weight:.2%} exceeds limit "
                            f"{limits.max_position_weight:.2%}"
                        ),
                        severity=BreachSeverity.HARD,
                        metrics={
                            "symbol": symbol,
                            "weight": weight,
                            "limit": limits.max_position_weight,
                        },
                        timestamp=snapshot.timestamp,
                    )
                )

        return breaches

    def _check_var_cvar(
        self,
        returns: pd.Series,
        equity: float,
        limits: RiskLimitsV2,
        alpha: float,
    ) -> List[RiskBreach]:
        """Prüft VaR/CVaR Limits."""
        breaches = []

        if equity <= 0:
            return breaches  # Bereits gemeldet

        # VaR-Check
        if limits.max_var is not None:
            var = historical_var(returns, alpha)

            if var > limits.max_var:
                breaches.append(
                    RiskBreach(
                        code="MAX_VAR",
                        message=(
                            f"VaR({alpha:.1%}) = {var:.2%} exceeds limit {limits.max_var:.2%}"
                        ),
                        severity=BreachSeverity.HARD,
                        metrics={
                            "var": var,
                            "limit": limits.max_var,
                            "alpha": alpha,
                        },
                    )
                )

        # CVaR-Check
        if limits.max_cvar is not None:
            cvar = historical_cvar(returns, alpha)

            if cvar > limits.max_cvar:
                breaches.append(
                    RiskBreach(
                        code="MAX_CVAR",
                        message=(
                            f"CVaR({alpha:.1%}) = {cvar:.2%} exceeds limit {limits.max_cvar:.2%}"
                        ),
                        severity=BreachSeverity.HARD,
                        metrics={
                            "cvar": cvar,
                            "limit": limits.max_cvar,
                            "alpha": alpha,
                        },
                    )
                )

        return breaches

    def _check_correlations(
        self,
        returns: pd.DataFrame,
        limits: RiskLimitsV2,
    ) -> List[RiskBreach]:
        """
        Prüft Correlation Limits (optional, für Multi-Asset-Portfolios).

        TODO: Implementierung für Multi-Asset-Support
        """
        # Placeholder für zukünftige Multi-Asset-Unterstützung
        return []
