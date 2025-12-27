"""
VaR Violation Detector
======================

Erkennt VaR-Überschreitungen in historischen Portfoliodaten.

Conventions:
- Returns and VaR estimates are expected as decimal returns (e.g., -0.02 for -2%)
- VaR is negative (e.g., -0.015 for 1.5% VaR at 99% confidence)
- Violation occurs when: return < var (both negative, loss exceeds VaR)
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class ViolationSeries:
    """
    Container für Violation-Daten.

    Attributes:
        dates: DatetimeIndex mit Beobachtungsdaten
        returns: Tägliche Portfolio-Returns (dezimal, z.B. -0.02 = -2%)
        var_estimates: VaR-Schätzungen (negativ, z.B. -0.015 = -1.5% VaR)
        violations: Boolean Series: True wenn Return < VaR
    """

    dates: pd.DatetimeIndex
    returns: pd.Series  # Tägliche Portfolio-Returns
    var_estimates: pd.Series  # VaR-Schätzungen (negativ!)
    violations: pd.Series  # bool: Return < VaR?

    @property
    def violation_dates(self) -> pd.DatetimeIndex:
        """Daten mit VaR-Überschreitung."""
        return self.dates[self.violations]

    @property
    def n_violations(self) -> int:
        """Anzahl Violations."""
        return int(self.violations.sum())

    @property
    def n_observations(self) -> int:
        """Anzahl Beobachtungen."""
        return len(self.violations)

    @property
    def violation_rate(self) -> float:
        """Violation Rate (N/T)."""
        if self.n_observations == 0:
            return 0.0
        return self.n_violations / self.n_observations


def detect_violations(
    returns: pd.Series,
    var_estimates: pd.Series,
) -> ViolationSeries:
    """
    Erkennt VaR-Überschreitungen durch Vergleich von Returns und VaR.

    Args:
        returns: Tägliche Portfolio-Returns (z.B. -0.02 für -2%)
            Index sollte DatetimeIndex sein
        var_estimates: VaR-Schätzungen (negativ, z.B. -0.015 für -1.5% VaR)
            Index sollte DatetimeIndex sein

    Returns:
        ViolationSeries mit allen Daten

    Note:
        - Violation tritt auf wenn: return < var (beide negativ!)
        - Beispiel: Return = -3%, VaR = -2% → Violation (Verlust größer als VaR)
        - NaN-Werte werden automatisch entfernt (dropna auf aligned data)
        - Nur überlappende Daten werden verwendet (inner join)

    Example:
        >>> returns = pd.Series([-0.01, -0.03, 0.02], index=dates)
        >>> var_estimates = pd.Series([-0.02, -0.02, -0.02], index=dates)
        >>> violations = detect_violations(returns, var_estimates)
        >>> violations.n_violations  # 1 (zweiter Tag: -3% < -2%)
        1
    """
    # Alignment und NaN-Handling
    aligned = pd.DataFrame(
        {"returns": returns, "var": var_estimates}
    ).dropna()

    # Violation: Return unterschreitet VaR (beide negativ!)
    # Mathematisch: return < var
    # Beispiel: -0.03 < -0.02 → True (3% Verlust > 2% VaR)
    violations = aligned["returns"] < aligned["var"]

    return ViolationSeries(
        dates=aligned.index,
        returns=aligned["returns"],
        var_estimates=aligned["var"],
        violations=violations,
    )
