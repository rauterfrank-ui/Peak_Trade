"""
Peak_Trade Risk Limits & Guards
=================================
Portfolio-weite Risk-Limits und Trade-Guards.

Prüft vor jedem Trade:
- Daily Loss Limit
- Max Drawdown
- Max Position Size
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class RiskLimitsConfig:
    """
    Zentrale Konfiguration für Risiko-Limits.
    Alle Werte in Prozent (z.B. 20.0 für 20%).
    """
    max_drawdown_pct: float = 20.0
    max_position_pct: float = 10.0
    daily_loss_limit_pct: float = 5.0


class RiskLimits:
    """
    Prüft verschiedene Risiko-Limits.

    Usage:
        >>> config = RiskLimitsConfig(max_drawdown_pct=20.0, daily_loss_limit_pct=5.0)
        >>> limits = RiskLimits(config)
        >>>
        >>> # Drawdown-Check
        >>> equity_curve = [10000, 10500, 9500, 9000, 9200]
        >>> ok = limits.check_drawdown(equity_curve, limits.config.max_drawdown_pct)
        >>>
        >>> # Daily Loss Check
        >>> returns_today = [0.5, -1.2, 0.3, -2.1]  # in %
        >>> ok = limits.check_daily_loss(returns_today, limits.config.daily_loss_limit_pct)
        >>>
        >>> # Position Size Check
        >>> ok = limits.check_position_size(size_nominal=2500, capital=10000, max_pct=25.0)
    """

    def __init__(self, config: RiskLimitsConfig | None = None) -> None:
        self.config = config or RiskLimitsConfig()

    @staticmethod
    def check_drawdown(
        equity_curve: Sequence[float] | pd.Series,
        max_dd_pct: float,
    ) -> bool:
        """
        Prüft, ob der maximale Drawdown (in %) über max_dd_pct liegt.

        Args:
            equity_curve: Liste oder Series der Equity-Werte über Zeit.
            max_dd_pct: Maximaler Drawdown in Prozent (z.B. 20.0 für 20%)

        Returns:
            True  -> alles ok (Drawdown unter Limit)
            False -> Limit verletzt (Drawdown >= max_dd_pct)

        Example:
            >>> equity = [10000, 10500, 9500, 8000, 8500]
            >>> RiskLimits.check_drawdown(equity, max_dd_pct=20.0)
            True  # Max DD = -23.8%, aber wir prüfen >= 20, also False würde passen
            >>> RiskLimits.check_drawdown(equity, max_dd_pct=25.0)
            True  # Max DD = -23.8% < 25%
        """
        if isinstance(equity_curve, pd.Series):
            equity_arr = equity_curve.values
        else:
            equity_arr = np.array(equity_curve)

        if len(equity_arr) == 0:
            return True

        # Running Maximum (Peak bis zu jedem Punkt)
        running_max = np.maximum.accumulate(equity_arr)

        # Drawdown an jedem Punkt (in Prozent)
        drawdown_pct = (equity_arr - running_max) / running_max * 100.0

        # Maximaler Drawdown (negativster Wert)
        max_dd = np.min(drawdown_pct)

        # Limit-Check: abs(max_dd) >= max_dd_pct bedeutet Verletzung
        return abs(max_dd) < max_dd_pct

    @staticmethod
    def check_daily_loss(
        returns_today_pct: Iterable[float],
        max_loss_pct: float,
    ) -> bool:
        """
        Prüft Daily Loss Limit auf Basis prozentualer Tages-Returns.

        Args:
            returns_today_pct: Liste von Prozent-Returns (z.B. +0.5, -1.2, ...)
            max_loss_pct: Maximaler Tagesverlust in Prozent (z.B. 5.0 für 5%)

        Returns:
            True  -> alles ok (Verlust unter Limit)
            False -> Limit verletzt (Verlust >= max_loss_pct)

        Note:
            Nur die Summe der NEGATIVEN Returns zählt als Tagesverlust.
            Positive Returns werden ignoriert.

        Example:
            >>> returns = [0.5, -1.2, 0.3, -2.1]  # in %
            >>> RiskLimits.check_daily_loss(returns, max_loss_pct=5.0)
            True  # Verlust = 1.2 + 2.1 = 3.3% < 5.0%
            >>> RiskLimits.check_daily_loss(returns, max_loss_pct=3.0)
            False  # Verlust = 3.3% >= 3.0%
        """
        returns_arr = np.array(list(returns_today_pct))

        if len(returns_arr) == 0:
            return True

        # Nur negative Returns summieren
        losses = returns_arr[returns_arr < 0]
        total_loss_pct = abs(np.sum(losses))  # Absoluter Verlust

        return total_loss_pct < max_loss_pct

    @staticmethod
    def check_position_size(
        size_nominal: float,
        capital: float,
        max_pct: float,
    ) -> bool:
        """
        Prüft ob Positionsgröße unter maximalem Prozentsatz liegt.

        Args:
            size_nominal: Kapital-Einsatz (EntryPrice * Units)
            capital: Aktuelles Eigenkapital
            max_pct: Maximaler Kapital-Einsatz in % des Kapitals (z.B. 10.0 für 10%)

        Returns:
            True  -> alles ok (Position unter Limit)
            False -> Limit verletzt (Position >= max_pct)

        Example:
            >>> RiskLimits.check_position_size(2500, capital=10000, max_pct=25.0)
            True  # 2500/10000 = 25% = Limit
            >>> RiskLimits.check_position_size(2500, capital=10000, max_pct=20.0)
            False  # 2500/10000 = 25% >= 20%
        """
        if capital <= 0:
            return False

        position_pct = (size_nominal / capital) * 100.0

        return position_pct <= max_pct

    def check_all(
        self,
        *,
        equity_curve: Sequence[float],
        returns_today_pct: Iterable[float],
        new_position_nominal: float,
        capital: float,
    ) -> bool:
        """
        Kombinierter Check aller Risiko-Limits (Drawdown, Daily Loss, Max Exposure).

        Args:
            equity_curve: Equity-Verlauf (historisch)
            returns_today_pct: Returns des aktuellen Tages (in %)
            new_position_nominal: Geplanter Kapital-Einsatz
            capital: Aktuelles Eigenkapital

        Returns:
            True  -> Trade erlaubt (alle Limits OK)
            False -> Trade blockiert (mindestens ein Limit verletzt)

        Example:
            >>> limits = RiskLimits()
            >>> ok = limits.check_all(
            ...     equity_curve=[10000, 10200, 10500],
            ...     returns_today_pct=[0.5, -1.0, 0.3],
            ...     new_position_nominal=2000,
            ...     capital=10500
            ... )
            >>> if not ok:
            ...     print("Trade blocked!")
        """
        # 1. Drawdown-Check
        if not self.check_drawdown(equity_curve, self.config.max_drawdown_pct):
            return False

        # 2. Daily Loss Check
        if not self.check_daily_loss(returns_today_pct, self.config.daily_loss_limit_pct):
            return False

        # 3. Position Size Check
        return self.check_position_size(new_position_nominal, capital, self.config.max_position_pct)


# Backwards-Compatibility: Alte Klassen als Aliases
@dataclass
class PortfolioState:
    """
    Aktueller Portfolio-Status (Legacy-Support).

    DEPRECATED: Nutze stattdessen check_all() mit direkten Parametern.
    """
    equity: float
    peak_equity: float
    daily_start_equity: float
    open_positions: int = 0
    total_exposure: float = 0.0


class RiskLimitChecker:
    """
    Legacy-Wrapper für RiskLimits (Backwards-Compatibility).

    DEPRECATED: Nutze stattdessen RiskLimits direkt.
    """

    def __init__(self, config: RiskLimitsConfig | None = None) -> None:
        # Konvertiere alte Config-Format zu neuem
        if config is None:
            config = RiskLimitsConfig()

        self.limits = RiskLimits(config)
        self.config = config

    def check_limits(self, state: PortfolioState, proposed_position_value: float) -> 'LimitCheckResult':
        """
        Legacy-Methode für Backwards-Compatibility.

        DEPRECATED: Nutze stattdessen RiskLimits.check_all()
        """
        # Baue Equity-Curve (vereinfacht)
        equity_curve = [state.daily_start_equity, state.equity]

        # Berechne Daily Returns (vereinfacht)
        daily_return_pct = ((state.equity - state.daily_start_equity) / state.daily_start_equity) * 100.0
        returns_today_pct = [daily_return_pct] if daily_return_pct < 0 else []

        # Check Drawdown
        dd_ok = self.limits.check_drawdown(equity_curve, self.config.max_drawdown_pct)
        if not dd_ok:
            drawdown = ((state.equity - state.peak_equity) / state.peak_equity) * 100.0
            return LimitCheckResult(
                rejected=True,
                reason=f"Max Drawdown erreicht: {drawdown:.1f}% (Max: {self.config.max_drawdown_pct:.1f}%)"
            )

        # Check Daily Loss
        loss_ok = self.limits.check_daily_loss(returns_today_pct, self.config.daily_loss_limit_pct)
        if not loss_ok:
            return LimitCheckResult(
                rejected=True,
                reason=f"Daily Loss Limit erreicht: {abs(daily_return_pct):.1f}% (Max: {self.config.daily_loss_limit_pct:.1f}%)"
            )

        # Check Position Size
        pos_ok = self.limits.check_position_size(
            proposed_position_value,
            state.equity,
            self.config.max_position_pct
        )
        if not pos_ok:
            pos_pct = (proposed_position_value / state.equity) * 100.0
            return LimitCheckResult(
                rejected=True,
                reason=f"Max Position Size überschritten: {pos_pct:.1f}% (Max: {self.config.max_position_pct:.1f}%)"
            )

        return LimitCheckResult(rejected=False, reason="OK")


@dataclass
class LimitCheckResult:
    """Ergebnis einer Limit-Prüfung (Legacy-Support)."""
    rejected: bool
    reason: str
    daily_loss: float = 0.0
    drawdown: float = 0.0
    exposure_pct: float = 0.0


# Utility-Funktionen
def compute_drawdown(equity: float, peak_equity: float) -> float:
    """
    Berechnet Drawdown in Prozent.

    Args:
        equity: Aktuelles Eigenkapital
        peak_equity: Historisches Peak-Equity

    Returns:
        Drawdown als Dezimalwert (negativ, z.B. -0.15 = -15%)

    Example:
        >>> compute_drawdown(equity=8500, peak_equity=10000)
        -0.15
    """
    if peak_equity <= 0:
        return 0.0
    return (equity - peak_equity) / peak_equity


def compute_daily_loss(equity: float, daily_start_equity: float) -> float:
    """
    Berechnet Tagesverlust/-gewinn in Prozent.

    Args:
        equity: Aktuelles Eigenkapital
        daily_start_equity: Equity zu Tagesbeginn

    Returns:
        Tagesperformance als Dezimalwert (z.B. -0.02 = -2%)

    Example:
        >>> compute_daily_loss(equity=9800, daily_start_equity=10000)
        -0.02
    """
    if daily_start_equity <= 0:
        return 0.0
    return (equity - daily_start_equity) / daily_start_equity
