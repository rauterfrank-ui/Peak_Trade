"""
VaR Backtest Runner
===================

Orchestriert den gesamten VaR-Backtest-Prozess mit Kupiec POF Test.

This module is designed for research and backtesting only.
It is NOT intended for real-time/live trading validation.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.risk_layer.var_backtest.kupiec_pof import (
    KupiecPOFOutput,
    kupiec_pof_test,
)
from src.risk_layer.var_backtest.violation_detector import (
    ViolationSeries,
    detect_violations,
)


@dataclass
class VaRBacktestResult:
    """
    Vollständiges Backtest-Ergebnis.

    Attributes:
        symbol: Asset/Portfolio-Bezeichnung
        start_date: Start der Backtest-Periode
        end_date: Ende der Backtest-Periode
        var_confidence: VaR-Konfidenzniveau (z.B. 0.99)
        var_method: VaR-Methode (z.B. "historical", "parametric")
        violations: ViolationSeries mit allen Violation-Daten
        kupiec: KupiecPOFOutput mit Test-Ergebnis
    """

    # Metadaten
    symbol: str
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    var_confidence: float
    var_method: str  # "historical", "parametric", "monte_carlo"

    # Violation-Daten
    violations: ViolationSeries

    # Kupiec Test
    kupiec: KupiecPOFOutput

    @property
    def is_valid(self) -> bool:
        """VaR-Modell gilt als valide."""
        return self.kupiec.is_valid

    def summary(self) -> dict:
        """
        Kompakte Zusammenfassung für Logging und Reporting.

        Returns:
            Dict mit allen wichtigen Metriken
        """
        return {
            "symbol": self.symbol,
            "period": f"{self.start_date.date()} - {self.end_date.date()}",
            "n_observations": self.kupiec.n_observations,
            "n_violations": self.kupiec.n_violations,
            "expected_rate": f"{self.kupiec.expected_violation_rate:.2%}",
            "observed_rate": f"{self.kupiec.observed_violation_rate:.2%}",
            "violation_ratio": f"{self.kupiec.violation_ratio:.2f}x",
            "kupiec_lr": f"{self.kupiec.lr_statistic:.4f}",
            "p_value": f"{self.kupiec.p_value:.4f}",
            "result": self.kupiec.result.value.upper(),
            "is_valid": self.is_valid,
        }


class VaRBacktestRunner:
    """
    Führt VaR-Backtests mit Kupiec POF Test durch.

    This class is designed for research and backtesting.
    It is NOT intended for live trading validation.

    Example:
        >>> runner = VaRBacktestRunner(confidence_level=0.99)
        >>> result = runner.run(
        ...     returns=portfolio_returns,
        ...     var_estimates=var_series,
        ...     symbol="BTC/EUR",
        ... )
        >>> print(result.summary())
    """

    def __init__(
        self,
        confidence_level: float = 0.99,
        significance_level: float = 0.05,
        min_observations: int = 250,
        var_method: str = "historical",
    ):
        """
        Initialize VaR Backtest Runner.

        Args:
            confidence_level: VaR confidence level (e.g., 0.99 for 99% VaR)
            significance_level: Significance level for hypothesis test (e.g., 0.05)
            min_observations: Minimum observations for valid test (Basel: 250)
            var_method: VaR method used (for metadata only)
        """
        self.confidence_level = confidence_level
        self.significance_level = significance_level
        self.min_observations = min_observations
        self.var_method = var_method

    def run(
        self,
        returns: pd.Series,
        var_estimates: pd.Series,
        symbol: str = "PORTFOLIO",
    ) -> VaRBacktestResult:
        """
        Führt vollständigen VaR-Backtest durch.

        Args:
            returns: Tägliche Portfolio-Returns (dezimal, z.B. -0.02 = -2%)
            var_estimates: VaR-Schätzungen (negativ, z.B. -0.015 = -1.5% VaR)
            symbol: Asset/Portfolio-Bezeichnung für Reporting

        Returns:
            VaRBacktestResult mit allen Ergebnissen

        Raises:
            ValueError: Bei ungültigen Eingabedaten
        """
        # 1. Violations erkennen
        violations = detect_violations(returns, var_estimates)

        # 2. Kupiec POF Test durchführen
        kupiec_result = kupiec_pof_test(
            violations=violations.violations.tolist(),
            confidence_level=self.confidence_level,
            significance_level=self.significance_level,
            min_observations=self.min_observations,
        )

        # 3. Ergebnis zusammenstellen
        return VaRBacktestResult(
            symbol=symbol,
            start_date=violations.dates.min(),
            end_date=violations.dates.max(),
            var_confidence=self.confidence_level,
            var_method=self.var_method,
            violations=violations,
            kupiec=kupiec_result,
        )
