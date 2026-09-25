"""
Peak_Trade Risk Layer - Type Definitions
=========================================
Typed containers for Risk-Layer v1.

Structures:
- PositionSnapshot: Einzelne Position mit Notional/Weight
- PortfolioSnapshot: Vollständiges Portfolio mit Equity/Positions
- RiskBreach: Limit-Verletzung mit Schweregrad
- RiskDecision: Entscheidung (Erlauben/Blockieren) + Breaches
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import pandas as pd


class BreachSeverity(str, Enum):
    """Schweregrad einer Risk-Limit-Verletzung."""

    INFO = "INFO"  # Informativ, keine Action
    WARNING = "WARNING"  # Warnung, aber erlaubt
    HARD = "HARD"  # Harte Grenze, blockiert Trade


@dataclass
class PositionSnapshot:
    """
    Snapshot einer einzelnen Position zu einem Zeitpunkt.

    Attributes:
        symbol: Trading-Symbol (z.B. "BTC/EUR")
        units: Anzahl Units (positiv=long, negativ=short)
        price: Aktueller Preis
        notional: Positionswert (units * price), berechnet wenn None
        weight: Portfolio-Weight (0-1), berechnet wenn None
        timestamp: Optional Zeitstempel
    """

    symbol: str
    units: float
    price: float
    notional: Optional[float] = None
    weight: Optional[float] = None
    timestamp: Optional[pd.Timestamp] = None

    def __post_init__(self) -> None:
        """Berechnet abgeleitete Felder."""
        if self.notional is None:
            self.notional = abs(self.units * self.price)


@dataclass
class PortfolioSnapshot:
    """
    Snapshot eines Portfolios zu einem Zeitpunkt.

    Attributes:
        equity: Gesamtes Eigenkapital (Kapital + unrealisierte PnL)
        positions: Liste von PositionSnapshots
        cash: Verfügbares Cash (optional)
        timestamp: Zeitstempel des Snapshots
        metadata: Optionale Zusatz-Informationen
    """

    equity: float
    positions: List[PositionSnapshot] = field(default_factory=list)
    cash: Optional[float] = None
    timestamp: Optional[pd.Timestamp] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_gross_exposure(self) -> float:
        """Berechnet Gross Exposure (Summe aller |notional|)."""
        return sum(abs(pos.notional or 0.0) for pos in self.positions)

    def get_net_exposure(self) -> float:
        """Berechnet Net Exposure (long - short notionals)."""
        return sum((pos.units * pos.price) for pos in self.positions)

    def get_position(self, symbol: str) -> Optional[PositionSnapshot]:
        """Findet Position für Symbol."""
        for pos in self.positions:
            if pos.symbol == symbol:
                return pos
        return None


@dataclass
class RiskBreach:
    """
    Repräsentiert eine Risk-Limit-Verletzung.

    Attributes:
        code: Eindeutiger Code (z.B. "MAX_VAR", "MAX_POSITION_WEIGHT")
        message: Beschreibung der Verletzung
        severity: Schweregrad (INFO/WARNING/HARD)
        metrics: Zusätzliche Metriken (z.B. {"var": 0.08, "limit": 0.05})
        timestamp: Zeitstempel der Prüfung
    """

    code: str
    message: str
    severity: BreachSeverity = BreachSeverity.WARNING
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[pd.Timestamp] = None

    def __str__(self) -> str:
        return f"[{self.severity.value}] {self.code}: {self.message}"


@dataclass
class RiskDecision:
    """
    Entscheidung des Risk-Layers über eine geplante Action.

    Attributes:
        allowed: True = Action erlaubt, False = Action blockiert
        action: Empfohlene Action ("ALLOW", "HALT", "REDUCE", etc.)
        breaches: Liste aller festgestellten Breaches
        metadata: Zusätzliche Informationen
    """

    allowed: bool
    action: str = "ALLOW"
    breaches: List[RiskBreach] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_hard_breach(self) -> bool:
        """Prüft ob mindestens ein Hard Breach vorliegt."""
        return any(b.severity == BreachSeverity.HARD for b in self.breaches)

    def get_breach_summary(self) -> str:
        """Erstellt Zusammenfassung aller Breaches."""
        if not self.breaches:
            return "No breaches"
        lines = [f"Total breaches: {len(self.breaches)}"]
        for b in self.breaches:
            lines.append(f"  - {b}")
        return "\n".join(lines)
