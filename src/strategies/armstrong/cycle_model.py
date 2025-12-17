# src/strategies/armstrong/cycle_model.py
"""
Armstrong Zyklus-Modell – Research-Only
=======================================

Implementiert das Armstrong Economic Confidence Model (ECM) als deterministisches
Zyklus-Modell für Research/Backtesting.

⚠️ WICHTIG: RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

Konzepte:
- ECM-Grundzyklus: 8,6 Jahre = 3141 Tage ≈ π × 1000
- Phasen: CRISIS, EXPANSION, CONTRACTION, PRE_CRISIS, POST_CRISIS
- Risk-Multiplier pro Phase für Position-Sizing

Warnung:
- Armstrong-Zyklen sind NICHT wissenschaftlich validiert
- Hindsight-Bias ist ein bekanntes Problem
- Nutze dieses Modell nur für explorative Analysen
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

import pandas as pd

# =============================================================================
# ARMSTRONG PHASE ENUM
# =============================================================================


class ArmstrongPhase(Enum):
    """
    Phasen des Armstrong Economic Confidence Model (ECM).

    Der ECM-Zyklus wird in fünf Phasen unterteilt:
    - CRISIS: Zyklusspitze / Crash-Phase (hohe Volatilität, Risk-Off)
    - EXPANSION: Wachstumsphase nach einem Tief (Risk-On)
    - CONTRACTION: Abschwungphase vor einem Hoch (Risk-Reduktion)
    - PRE_CRISIS: Kurz vor einem Turning-Point (erhöhte Vorsicht)
    - POST_CRISIS: Erholung nach einem Turning-Point (Stabilisierung)

    Attributes:
        value: Kurzbezeichnung der Phase
    """

    CRISIS = "crisis"
    EXPANSION = "expansion"
    CONTRACTION = "contraction"
    PRE_CRISIS = "pre_crisis"
    POST_CRISIS = "post_crisis"

    def __str__(self) -> str:
        return self.value


# =============================================================================
# ARMSTRONG CYCLE CONFIG
# =============================================================================


@dataclass
class ArmstrongCycleConfig:
    """
    Konfiguration für das Armstrong-Zyklus-Modell.

    Attributes:
        reference_peak_date: Referenzdatum eines bekannten Zyklus-Peaks (z.B. 2015.75)
        cycle_length_days: Gesamtlänge des Zyklus in Tagen (default: 3141 ≈ 8.6 Jahre)
        phase_distribution: Dict mit Phasenname → (start_pct, end_pct) im Zyklus

    Example:
        >>> config = ArmstrongCycleConfig(
        ...     reference_peak_date=date(2015, 10, 1),
        ...     cycle_length_days=3141,
        ... )
    """

    reference_peak_date: date
    cycle_length_days: int = 3141  # ≈ π × 1000 = 8.6 Jahre

    # Phasenverteilung als Prozent des Zyklus (start_pct, end_pct)
    # Default: Einfache gleichmäßige Verteilung mit Turning-Point-Fenstern
    phase_distribution: dict[str, tuple[float, float]] = field(
        default_factory=lambda: {
            # Post-Crisis: 0-15% des Zyklus (Erholung nach Peak)
            "post_crisis": (0.0, 0.15),
            # Expansion: 15-45% des Zyklus (Wachstumsphase)
            "expansion": (0.15, 0.45),
            # Pre-Crisis: 45-50% des Zyklus (Mid-Cycle Turning-Point naht)
            "pre_crisis_mid": (0.45, 0.50),
            # Contraction: 50-85% des Zyklus (Abschwungphase)
            "contraction": (0.50, 0.85),
            # Pre-Crisis: 85-95% des Zyklus (Haupt-Peak naht)
            "pre_crisis": (0.85, 0.95),
            # Crisis: 95-100% + 0-5% des nächsten Zyklus (Turning-Point-Fenster)
            "crisis": (0.95, 1.0),
        }
    )

    # Risk-Multiplier pro Phase (0.0 = kein Risiko, 1.0 = volles Risiko)
    risk_multipliers: dict[str, float] = field(
        default_factory=lambda: {
            "crisis": 0.3,           # Stark reduziert während Crisis
            "post_crisis": 0.5,      # Vorsichtig in Erholungsphase
            "expansion": 1.0,        # Volles Risiko in Expansion
            "pre_crisis_mid": 0.7,   # Reduziert vor Mid-Cycle
            "contraction": 0.6,      # Reduziert in Contraction
            "pre_crisis": 0.4,       # Stark reduziert vor Peak
        }
    )

    def __post_init__(self) -> None:
        """Validierung nach Initialisierung."""
        if self.cycle_length_days < 30:
            raise ValueError(
                f"cycle_length_days ({self.cycle_length_days}) muss >= 30 sein"
            )

    @classmethod
    def default(cls) -> ArmstrongCycleConfig:
        """
        Erstellt eine Standardkonfiguration mit ECM 2015.75 als Referenz.

        Returns:
            ArmstrongCycleConfig mit Default-Werten
        """
        return cls(
            reference_peak_date=date(2015, 10, 1),  # ECM 2015.75
            cycle_length_days=3141,
        )

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "reference_peak_date": self.reference_peak_date.isoformat(),
            "cycle_length_days": self.cycle_length_days,
            "phase_distribution": self.phase_distribution,
            "risk_multipliers": self.risk_multipliers,
        }


# =============================================================================
# ARMSTRONG CYCLE MODEL
# =============================================================================


class ArmstrongCycleModel:
    """
    Armstrong Economic Confidence Model (ECM) Zyklus-Modell.

    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

    Dieses Modell berechnet deterministisch die Zyklus-Phase für jedes Datum
    basierend auf einem Referenz-Peak und der Zykluslänge.

    Attributes:
        config: ArmstrongCycleConfig mit Zyklus-Parametern

    Example:
        >>> model = ArmstrongCycleModel.from_default()
        >>> phase = model.phase_for_date(date(2024, 1, 15))
        >>> print(f"Phase: {phase}")
        Phase: expansion

        >>> multiplier = model.risk_multiplier_for_date(date(2024, 1, 15))
        >>> print(f"Risk Multiplier: {multiplier}")
        Risk Multiplier: 1.0
    """

    def __init__(self, config: ArmstrongCycleConfig) -> None:
        """
        Initialisiert das Zyklus-Modell.

        Args:
            config: Konfiguration für das Modell
        """
        self.config = config

    @classmethod
    def from_default(cls) -> ArmstrongCycleModel:
        """
        Erstellt ein Modell mit Standardkonfiguration.

        Returns:
            ArmstrongCycleModel mit Default-Config
        """
        return cls(ArmstrongCycleConfig.default())

    @classmethod
    def from_config_dict(cls, config_dict: dict[str, Any]) -> ArmstrongCycleModel:
        """
        Erstellt ein Modell aus einem Config-Dictionary.

        Args:
            config_dict: Dictionary mit Konfiguration

        Returns:
            ArmstrongCycleModel-Instanz
        """
        ref_date_str = config_dict.get("reference_peak_date", "2015-10-01")
        if isinstance(ref_date_str, str):
            ref_date = date.fromisoformat(ref_date_str)
        else:
            ref_date = ref_date_str

        cycle_length = config_dict.get("cycle_length_days", 3141)

        config = ArmstrongCycleConfig(
            reference_peak_date=ref_date,
            cycle_length_days=cycle_length,
        )

        # Override phase_distribution wenn vorhanden
        if "phase_distribution" in config_dict:
            config.phase_distribution = config_dict["phase_distribution"]

        # Override risk_multipliers wenn vorhanden
        if "risk_multipliers" in config_dict:
            config.risk_multipliers = config_dict["risk_multipliers"]

        return cls(config)

    def _to_date(self, dt: date | datetime | pd.Timestamp) -> date:
        """
        Konvertiert verschiedene Datumsformate zu date.

        Args:
            dt: Datum in verschiedenen Formaten

        Returns:
            date-Objekt
        """
        if isinstance(dt, datetime):
            return dt.date()
        if isinstance(dt, pd.Timestamp):
            return dt.date()
        return dt

    def _days_since_reference(self, dt: date) -> int:
        """
        Berechnet die Tage seit dem Referenz-Peak.

        Args:
            dt: Datum

        Returns:
            Anzahl Tage (kann negativ sein wenn vor Referenz)
        """
        ref = self.config.reference_peak_date
        return (dt - ref).days

    def _cycle_position(self, dt: date) -> float:
        """
        Berechnet die Position im Zyklus (0.0 bis 1.0).

        Args:
            dt: Datum

        Returns:
            Position im Zyklus (0.0 = am Referenz-Peak, 0.5 = halber Zyklus)
        """
        days = self._days_since_reference(dt)
        cycle_length = self.config.cycle_length_days

        # Modulo für zyklische Position
        position = (days % cycle_length) / cycle_length

        return position

    def phase_for_date(
        self, dt: date | datetime | pd.Timestamp
    ) -> ArmstrongPhase:
        """
        Bestimmt die Armstrong-Phase für ein gegebenes Datum.

        Args:
            dt: Datum für Phasenbestimmung

        Returns:
            ArmstrongPhase (CRISIS, EXPANSION, CONTRACTION, PRE_CRISIS, POST_CRISIS)

        Example:
            >>> model = ArmstrongCycleModel.from_default()
            >>> phase = model.phase_for_date(date(2024, 6, 15))
            >>> print(phase)
            expansion
        """
        dt_date = self._to_date(dt)
        position = self._cycle_position(dt_date)

        # Phase basierend auf Position im Zyklus bestimmen
        dist = self.config.phase_distribution

        # Crisis: 95-100% (Ende des Zyklus, nahe am Turning-Point)
        if position >= dist["crisis"][0]:
            return ArmstrongPhase.CRISIS

        # Pre-Crisis: 85-95% (vor dem Haupt-Peak)
        if position >= dist["pre_crisis"][0]:
            return ArmstrongPhase.PRE_CRISIS

        # Contraction: 50-85% (Abschwung)
        if position >= dist["contraction"][0]:
            return ArmstrongPhase.CONTRACTION

        # Pre-Crisis Mid: 45-50% (vor Mid-Cycle Turning-Point)
        if position >= dist["pre_crisis_mid"][0]:
            return ArmstrongPhase.PRE_CRISIS

        # Expansion: 15-45% (Wachstum)
        if position >= dist["expansion"][0]:
            return ArmstrongPhase.EXPANSION

        # Post-Crisis: 0-15% (Erholung nach Peak)
        return ArmstrongPhase.POST_CRISIS

    def risk_multiplier_for_date(
        self, dt: date | datetime | pd.Timestamp
    ) -> float:
        """
        Gibt den Risk-Multiplier für ein Datum zurück.

        Der Risk-Multiplier skaliert das Position-Sizing basierend auf
        der aktuellen Zyklus-Phase:
        - 0.0 = Kein Risiko (sollte nicht vorkommen)
        - 0.3 = Stark reduziert (z.B. CRISIS)
        - 1.0 = Volles Risiko (z.B. EXPANSION)

        Args:
            dt: Datum

        Returns:
            Risk-Multiplier (float zwischen 0.0 und 1.0)

        Example:
            >>> model = ArmstrongCycleModel.from_default()
            >>> mult = model.risk_multiplier_for_date(date(2024, 1, 15))
            >>> print(f"Risk: {mult:.1%}")
            Risk: 100.0%
        """
        dt_date = self._to_date(dt)
        position = self._cycle_position(dt_date)
        multipliers = self.config.risk_multipliers

        # Phase basierend auf Position bestimmen
        dist = self.config.phase_distribution

        if position >= dist["crisis"][0]:
            return multipliers.get("crisis", 0.3)
        if position >= dist["pre_crisis"][0]:
            return multipliers.get("pre_crisis", 0.4)
        if position >= dist["contraction"][0]:
            return multipliers.get("contraction", 0.6)
        if position >= dist["pre_crisis_mid"][0]:
            return multipliers.get("pre_crisis_mid", 0.7)
        if position >= dist["expansion"][0]:
            return multipliers.get("expansion", 1.0)

        return multipliers.get("post_crisis", 0.5)

    def get_cycle_info(
        self, dt: date | datetime | pd.Timestamp
    ) -> dict[str, Any]:
        """
        Gibt umfassende Zyklus-Informationen für ein Datum zurück.

        Args:
            dt: Datum

        Returns:
            Dict mit:
            - phase: ArmstrongPhase
            - phase_name: String-Name der Phase
            - cycle_position: Position im Zyklus (0.0-1.0)
            - days_since_reference: Tage seit Referenz-Peak
            - days_in_current_cycle: Tage seit letztem Zyklus-Start
            - risk_multiplier: Risk-Multiplier für diese Phase
            - next_turning_point: Geschätztes Datum des nächsten Peaks
        """
        dt_date = self._to_date(dt)
        days = self._days_since_reference(dt_date)
        cycle_length = self.config.cycle_length_days
        position = self._cycle_position(dt_date)
        phase = self.phase_for_date(dt_date)

        # Tage bis zum nächsten Turning-Point (Zyklus-Ende)
        days_to_next = cycle_length - (days % cycle_length)
        next_tp = dt_date + pd.Timedelta(days=days_to_next)

        # Berechne Proximity zum Turning Point
        window_days = 90  # Event-Window für Turning-Point-Proximity
        is_near_tp = (days_to_next <= window_days) or ((days % cycle_length) <= window_days)

        return {
            "phase": phase,
            "phase_name": str(phase),
            "cycle_position": position,
            "cycle_phase": position,  # Alias für Backward Compatibility
            "days_since_reference": days,
            "days_in_current_cycle": days % cycle_length,
            "risk_multiplier": self.risk_multiplier_for_date(dt_date),
            "next_turning_point": next_tp,
            "cycle_length_days": cycle_length,
            "is_near_turning_point": is_near_tp,
        }

    def __repr__(self) -> str:
        return (
            f"<ArmstrongCycleModel("
            f"ref={self.config.reference_peak_date}, "
            f"cycle={self.config.cycle_length_days}d) "
            f"[RESEARCH-ONLY]>"
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def get_phase_for_date(
    dt: date | datetime | pd.Timestamp,
    reference_date: date | None = None,
    cycle_length: int = 3141,
) -> ArmstrongPhase:
    """
    Convenience-Funktion: Bestimmt die Phase für ein Datum.

    Args:
        dt: Datum
        reference_date: Referenz-Peak (default: 2015-10-01)
        cycle_length: Zykluslänge in Tagen

    Returns:
        ArmstrongPhase
    """
    ref = reference_date or date(2015, 10, 1)
    config = ArmstrongCycleConfig(
        reference_peak_date=ref,
        cycle_length_days=cycle_length,
    )
    model = ArmstrongCycleModel(config)
    return model.phase_for_date(dt)


def get_risk_multiplier_for_date(
    dt: date | datetime | pd.Timestamp,
    reference_date: date | None = None,
    cycle_length: int = 3141,
) -> float:
    """
    Convenience-Funktion: Gibt den Risk-Multiplier für ein Datum zurück.

    Args:
        dt: Datum
        reference_date: Referenz-Peak (default: 2015-10-01)
        cycle_length: Zykluslänge in Tagen

    Returns:
        Risk-Multiplier (0.0-1.0)
    """
    ref = reference_date or date(2015, 10, 1)
    config = ArmstrongCycleConfig(
        reference_peak_date=ref,
        cycle_length_days=cycle_length,
    )
    model = ArmstrongCycleModel(config)
    return model.risk_multiplier_for_date(dt)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Config
    "ArmstrongCycleConfig",
    # Model
    "ArmstrongCycleModel",
    # Enum
    "ArmstrongPhase",
    # Convenience Functions
    "get_phase_for_date",
    "get_risk_multiplier_for_date",
]



