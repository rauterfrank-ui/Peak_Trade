"""
Peak_Trade Risk Layer - Stress Testing
=======================================
Szenarien-basiertes Stress-Testing für Portfolio-Returns.

Classes:
- StressScenario: Definition eines Stress-Szenarios

Functions:
- apply_scenario_to_returns: Wendet Szenario auf Returns an
- run_stress_suite: Führt mehrere Szenarien aus und sammelt Metriken

Scenarios:
- shock: Plötzlicher Shock (z.B. -20% an einem Tag)
- vol_spike: Volatilitäts-Spike (std * multiplier)
- flash_crash: Extremer Drawdown über kurze Zeit
- regime_bear: Prolongierter Bärenmarkt (drift negativ)
- regime_sideways: Seitwärts-Markt (hohe Choppiness)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import logging

from .var import historical_var, historical_cvar

logger = logging.getLogger(__name__)


@dataclass
class StressScenario:
    """
    Definition eines Stress-Test-Szenarios.

    Attributes:
        name: Eindeutiger Name (z.B. "crash_2020")
        kind: Szenario-Typ ("shock", "vol_spike", "flash_crash", "regime_bear", "regime_sideways")
        params: Parameter für das Szenario (abhängig von kind)
        description: Optionale Beschreibung

    Example:
        >>> scenario = StressScenario(
        ...     name="crash_2020",
        ...     kind="shock",
        ...     params={"shock_pct": -0.20, "days": 5}
        ... )
    """

    name: str
    kind: str
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        """Validiere kind."""
        valid_kinds = {"shock", "vol_spike", "flash_crash", "regime_bear", "regime_sideways"}
        if self.kind not in valid_kinds:
            raise ValueError(f"Invalid scenario kind '{self.kind}'. Must be one of {valid_kinds}")


def apply_scenario_to_returns(
    returns: pd.Series,
    scenario: StressScenario,
) -> pd.Series:
    """
    Wendet Stress-Szenario auf Returns an.

    Args:
        returns: Original-Returns
        scenario: StressScenario-Definition

    Returns:
        Modifizierte Returns nach Szenario-Anwendung

    Notes:
        - Erzeugt neue Series (modifiziert nicht Original)
        - Verschiedene Szenarien haben unterschiedliche Effekte
        - Szenario-Parameter in scenario.params

    Scenario-Spezifika:

    1. shock: Plötzlicher Shock
       params: {"shock_pct": -0.20, "days": 5} -> -20% über 5 Tage verteilt

    2. vol_spike: Volatilitäts-Spike
       params: {"multiplier": 3.0} -> std * 3

    3. flash_crash: Extremer Drawdown
       params: {"crash_pct": -0.30, "recovery_days": 10}

    4. regime_bear: Prolongierter Bärenmarkt
       params: {"drift_pct": -0.02, "duration_days": 60}

    5. regime_sideways: Seitwärts-Markt
       params: {"chop_factor": 2.0, "duration_days": 30}

    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.03])
        >>> scenario = StressScenario("crash", "shock", {"shock_pct": -0.20})
        >>> stressed = apply_scenario_to_returns(returns, scenario)
    """
    if returns.empty:
        logger.warning(f"apply_scenario: Empty returns for scenario '{scenario.name}'")
        return returns.copy()

    stressed = returns.copy()

    if scenario.kind == "shock":
        stressed = _apply_shock(stressed, scenario.params)

    elif scenario.kind == "vol_spike":
        stressed = _apply_vol_spike(stressed, scenario.params)

    elif scenario.kind == "flash_crash":
        stressed = _apply_flash_crash(stressed, scenario.params)

    elif scenario.kind == "regime_bear":
        stressed = _apply_regime_bear(stressed, scenario.params)

    elif scenario.kind == "regime_sideways":
        stressed = _apply_regime_sideways(stressed, scenario.params)

    else:
        logger.warning(f"Unknown scenario kind '{scenario.kind}', returning unchanged")

    return stressed


def run_stress_suite(
    returns: pd.Series,
    scenarios: List[StressScenario],
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
    Führt mehrere Stress-Szenarien aus und sammelt Metriken.

    Args:
        returns: Original-Returns
        scenarios: Liste von StressScenarios
        alpha: Konfidenzniveau für VaR/CVaR

    Returns:
        DataFrame mit Metriken pro Szenario:
        - scenario: Szenario-Name
        - var: VaR (alpha)
        - cvar: CVaR (alpha)
        - mean: Mittlerer Return
        - std: Volatilität
        - min: Worst Return
        - max: Best Return
        - total_return: Kumulativer Return

    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.03, -0.01])
        >>> scenarios = [
        ...     StressScenario("baseline", "shock", {"shock_pct": 0.0}),
        ...     StressScenario("crash", "shock", {"shock_pct": -0.20}),
        ... ]
        >>> results = run_stress_suite(returns, scenarios)
        >>> print(results[['scenario', 'var', 'cvar']])
    """
    if returns.empty:
        logger.warning("run_stress_suite: Empty returns, returning empty DataFrame")
        return pd.DataFrame()

    results = []

    for scenario in scenarios:
        # Wende Szenario an
        stressed = apply_scenario_to_returns(returns, scenario)

        # Berechne Metriken
        metrics = {
            "scenario": scenario.name,
            "kind": scenario.kind,
            "var": historical_var(stressed, alpha),
            "cvar": historical_cvar(stressed, alpha),
            "mean": stressed.mean(),
            "std": stressed.std(),
            "min": stressed.min(),
            "max": stressed.max(),
            "total_return": (1 + stressed).prod() - 1,  # Kumulativ
        }

        results.append(metrics)

    df = pd.DataFrame(results)
    return df


# ============================================================================
# Private Szenario-Implementierungen
# ============================================================================


def _apply_shock(returns: pd.Series, params: Dict[str, Any]) -> pd.Series:
    """
    Shock-Szenario: Plötzlicher Return-Shock über N Tage.

    params:
        shock_pct: Gesamt-Shock (z.B. -0.20 = -20%)
        days: Anzahl Tage über die Shock verteilt wird (default: 1)
    """
    shock_pct = params.get("shock_pct", -0.10)
    days = params.get("days", 1)

    if days <= 0:
        days = 1

    # Schock pro Tag
    daily_shock = shock_pct / days

    # Füge Shock zu ersten N Returns hinzu
    stressed = returns.copy()
    n = min(days, len(stressed))
    stressed.iloc[:n] = stressed.iloc[:n] + daily_shock

    return stressed


def _apply_vol_spike(returns: pd.Series, params: Dict[str, Any]) -> pd.Series:
    """
    Volatility-Spike-Szenario: Multipliziere std mit Faktor.

    params:
        multiplier: Vol-Multiplikator (z.B. 3.0 -> 3x std)
    """
    multiplier = params.get("multiplier", 2.0)

    mean = returns.mean()
    std = returns.std()

    # Skaliere Returns: (returns - mean) * multiplier + mean
    stressed = (returns - mean) * multiplier + mean

    return stressed


def _apply_flash_crash(returns: pd.Series, params: Dict[str, Any]) -> pd.Series:
    """
    Flash-Crash-Szenario: Extremer Drawdown gefolgt von Recovery.

    params:
        crash_pct: Crash-Größe (z.B. -0.30 = -30%)
        recovery_days: Anzahl Tage bis Recovery (default: 10)
    """
    crash_pct = params.get("crash_pct", -0.20)
    recovery_days = params.get("recovery_days", 10)

    if len(returns) == 0:
        return returns

    stressed = returns.copy()

    # Crash an Tag 0
    stressed.iloc[0] = crash_pct

    # Recovery über N Tage (linear)
    n = min(recovery_days, len(stressed) - 1)
    if n > 0:
        recovery_per_day = -crash_pct / n
        for i in range(1, n + 1):
            stressed.iloc[i] = recovery_per_day

    return stressed


def _apply_regime_bear(returns: pd.Series, params: Dict[str, Any]) -> pd.Series:
    """
    Bear-Market-Regime: Negativer Drift über lange Zeit.

    params:
        drift_pct: Täglicher Drift (z.B. -0.02 = -2% pro Tag)
        duration_days: Dauer des Regimes (default: 60)
    """
    drift_pct = params.get("drift_pct", -0.01)
    duration_days = params.get("duration_days", 60)

    stressed = returns.copy()
    n = min(duration_days, len(stressed))

    # Addiere negativen Drift
    stressed.iloc[:n] = stressed.iloc[:n] + drift_pct

    return stressed


def _apply_regime_sideways(returns: pd.Series, params: Dict[str, Any]) -> pd.Series:
    """
    Sideways-Regime: Hohe Choppiness, kein Trend.

    params:
        chop_factor: Erhöhe std, reduziere Trend (default: 2.0)
        duration_days: Dauer des Regimes (default: 30)
    """
    chop_factor = params.get("chop_factor", 2.0)
    duration_days = params.get("duration_days", 30)

    stressed = returns.copy()
    n = min(duration_days, len(stressed))

    # Entferne Trend, erhöhe Vol
    segment = stressed.iloc[:n]
    mean = segment.mean()
    std = segment.std()

    # Zentriere um 0, erhöhe std
    stressed.iloc[:n] = (segment - mean) * chop_factor

    return stressed
