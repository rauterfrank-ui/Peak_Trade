"""
Risk Layer Types - Unified API
================================

Types for Risk Layer Roadmap features:
- Attribution Analytics
- Stress Testing
- Unified Results

Note: Core types (Violation, RiskDecision, RiskResult) are in models.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd


# ============================================================================
# Attribution Types (für Agent D)
# ============================================================================


@dataclass(frozen=True)
class ComponentVaR:
    """
    Component VaR für eine einzelne Position.

    Attributes:
        asset: Asset-Name (z.B. "BTC-EUR")
        weight: Portfolio-Gewicht (z.B. 0.6 für 60%)
        marginal_var: Marginal VaR (∂VaR/∂w_i)
        component_var: Component VaR (w_i * Marginal VaR)
        incremental_var: Incremental VaR (VaR mit - VaR ohne Asset)
        percent_contribution: Anteil am Gesamt-VaR (%)
    """

    asset: str
    weight: float
    marginal_var: float
    component_var: float
    incremental_var: float
    percent_contribution: float

    @property
    def diversification_benefit(self) -> float:
        """
        Diversifikations-Vorteil.

        Returns:
            Incremental VaR - Component VaR (sollte positiv sein)
        """
        return self.incremental_var - self.component_var


@dataclass(frozen=True)
class VaRDecomposition:
    """
    Vollständige VaR-Zerlegung für Portfolio.

    Attributes:
        portfolio_var: Gesamt-Portfolio VaR
        components: Dict von {asset: ComponentVaR}
        diversification_ratio: Sum(Standalone VaR) / Portfolio VaR
    """

    portfolio_var: float
    components: Dict[str, ComponentVaR]
    diversification_ratio: float

    def to_dataframe(self) -> pd.DataFrame:
        """Konvertiert zu DataFrame für Reporting."""
        data = []
        for asset, comp in self.components.items():
            data.append(
                {
                    "asset": asset,
                    "weight": comp.weight,
                    "marginal_var": comp.marginal_var,
                    "component_var": comp.component_var,
                    "incremental_var": comp.incremental_var,
                    "percent_contribution": comp.percent_contribution,
                    "diversification_benefit": comp.diversification_benefit,
                }
            )
        return pd.DataFrame(data)

    @property
    def top_contributors(self, n: int = 5) -> List[ComponentVaR]:
        """Top N Risiko-Beiträger (nach abs(component_var))."""
        sorted_comps = sorted(
            self.components.values(), key=lambda c: abs(c.component_var), reverse=True
        )
        return sorted_comps[:n]


@dataclass(frozen=True)
class PnLAttribution:
    """
    P&L Attribution für Portfolio.

    Attributes:
        total_pnl: Gesamt-P&L
        asset_contributions: Dict von {asset: pnl_contribution}
        factor_contributions: Optional Dict von {factor: pnl_contribution}
    """

    total_pnl: float
    asset_contributions: Dict[str, float]
    factor_contributions: Optional[Dict[str, float]] = None

    def to_dataframe(self) -> pd.DataFrame:
        """Konvertiert Asset-Contributions zu DataFrame."""
        data = [
            {"asset": asset, "pnl_contribution": pnl}
            for asset, pnl in self.asset_contributions.items()
        ]
        return pd.DataFrame(data)


# ============================================================================
# Stress Testing Types (für Agent E)
# ============================================================================


@dataclass(frozen=True)
class StressScenario:
    """
    Stress-Test-Szenario.

    Attributes:
        name: Szenario-Name (z.B. "Crypto Crash")
        description: Human-readable Beschreibung
        shocks: Dict von {asset: shock_return} (z.B. {"BTC-EUR": -0.50})
        metadata: Optional zusätzliche Daten
    """

    name: str
    description: str
    shocks: Dict[str, float]
    metadata: Optional[Dict] = None


@dataclass(frozen=True)
class ReverseStressResult:
    """
    Ergebnis eines Reverse Stress Tests.

    Attributes:
        target_loss: Ziel-Verlust (z.B. 0.20 für -20%)
        scenarios: Liste gefundener Szenarien
        portfolio_value: Aktueller Portfolio-Wert
        current_positions: Dict von {asset: position_value}
    """

    target_loss: float
    scenarios: List[StressScenario]
    portfolio_value: float
    current_positions: Dict[str, float]

    def to_dataframe(self) -> pd.DataFrame:
        """Konvertiert Szenarien zu DataFrame."""
        data = []
        for scenario in self.scenarios:
            for asset, shock in scenario.shocks.items():
                data.append(
                    {
                        "scenario": scenario.name,
                        "asset": asset,
                        "shock_return": shock,
                        "description": scenario.description,
                    }
                )
        return pd.DataFrame(data)


@dataclass(frozen=True)
class ForwardStressResult:
    """
    Ergebnis eines Forward Stress Tests.

    Attributes:
        scenario: Getestetes Szenario
        portfolio_loss: Absoluter Portfolio-Verlust
        portfolio_loss_pct: Portfolio-Verlust in %
        asset_contributions: Dict von {asset: loss_contribution}
        var_breach: Wurde VaR-Limit überschritten?
    """

    scenario: StressScenario
    portfolio_loss: float
    portfolio_loss_pct: float
    asset_contributions: Dict[str, float]
    var_breach: bool

    def to_dict(self) -> Dict:
        """Konvertiert zu Dict für Reporting."""
        return {
            "scenario": self.scenario.name,
            "description": self.scenario.description,
            "portfolio_loss": self.portfolio_loss,
            "portfolio_loss_pct": self.portfolio_loss_pct,
            "var_breach": self.var_breach,
            "asset_contributions": self.asset_contributions,
        }


# ============================================================================
# Unified Results
# ============================================================================


@dataclass(frozen=True)
class RiskLayerResult:
    """
    Unified Result für vollständige Risk Layer Analyse.

    Enthält alle Komponenten der Risk Layer Roadmap.

    Attributes:
        var: VaR (optional)
        cvar: CVaR (optional)
        kupiec_result: Kupiec POF Test Result (optional)
        traffic_light: Traffic Light Zone (optional)
        var_decomposition: VaR Decomposition (optional)
        pnl_attribution: P&L Attribution (optional)
        stress_results: Forward Stress Test Results (optional)
        reverse_stress: Reverse Stress Test Result (optional)
        kill_switch_active: Ist Kill Switch aktiv?
        timestamp: Zeitstempel
        portfolio_value: Portfolio-Wert
    """

    # VaR Core
    var: Optional[float] = None
    cvar: Optional[float] = None

    # VaR Validation
    kupiec_result: Optional[object] = None  # KupiecPOFOutput
    traffic_light: Optional[str] = None  # TrafficLightZone

    # Attribution (NEU)
    var_decomposition: Optional[VaRDecomposition] = None
    pnl_attribution: Optional[PnLAttribution] = None

    # Stress Testing (NEU)
    stress_results: Optional[List[ForwardStressResult]] = None
    reverse_stress: Optional[ReverseStressResult] = None

    # Kill Switch
    kill_switch_active: bool = False

    # Metadata
    timestamp: Optional[datetime] = None
    portfolio_value: float = 0.0

    def __post_init__(self):
        if self.timestamp is None:
            # Workaround for frozen dataclass
            object.__setattr__(self, "timestamp", datetime.utcnow())

    def summary(self) -> Dict:
        """Kompakte Zusammenfassung für Logging."""
        return {
            "var": self.var,
            "cvar": self.cvar,
            "kill_switch_active": self.kill_switch_active,
            "has_attribution": self.var_decomposition is not None,
            "has_stress": self.stress_results is not None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


# ============================================================================
# Sign Convention Helpers
# ============================================================================


def validate_var_positive(var: float, name: str = "VaR") -> None:
    """
    Validiert dass VaR als positive Zahl vorliegt.

    Convention: VaR ist IMMER positiv (potentieller Verlust).

    Args:
        var: VaR-Wert
        name: Name des Werts (für Error Message)

    Raises:
        ValueError: Wenn VaR negativ
    """
    if var < 0:
        raise ValueError(
            f"{name} muss positiv sein (potentieller Verlust). "
            f"Erhalten: {var}. "
            f"Tipp: Verwende abs() oder negiere das Ergebnis."
        )


def validate_confidence_level(confidence: float) -> None:
    """
    Validiert Confidence Level (0, 1).

    Args:
        confidence: Confidence Level

    Raises:
        ValueError: Wenn außerhalb (0, 1)
    """
    if not 0 < confidence < 1:
        raise ValueError(f"Confidence Level muss in (0, 1) liegen. Erhalten: {confidence}")
