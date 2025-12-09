# src/strategies/armstrong/armstrong_cycle_strategy.py
"""
Armstrong Cycle Strategy – Research-Only
========================================

Diese Strategie implementiert Konzepte aus Martin Armstrongs Economic Confidence
Model (ECM) für explorative Research-Zwecke.

⚠️ WICHTIG: RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

Diese Strategie ist ausschließlich für:
- Offline-Backtests
- Research & Analyse
- Akademische Experimente

Die generate_signals-Logik ist ein Placeholder/Stub. Die eigentliche Implementierung
erfolgt in einer späteren Research-Phase nach wissenschaftlicher Validierung.

Hintergrund:
- ECM-Grundzyklus: 8,6 Jahre = 3141 Tage ≈ π × 1000
- Halb-/Teilzyklen für Timing-Signale
- Siehe: src/docs/armstrong_notes.md

Warnung:
- Armstrong-Zyklen sind NICHT wissenschaftlich validiert
- Hindsight-Bias ist ein bekanntes Problem
- Nutze diese Strategie nur für explorative Analysen
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..base import BaseStrategy, StrategyMetadata


class ArmstrongCycleStrategy(BaseStrategy):
    """
    Armstrong Economic Confidence Model (ECM) Cycle Strategy.

    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

    Diese Strategie nutzt ECM-Zyklen (8.6 Jahre / 3141 Tage) als
    Timing-Overlay für Makro-Regime-Detection.

    Konzept:
    - Zyklus-Hochpunkte: Potenziell erhöhtes Risiko / Regime-Wechsel
    - Zyklus-Tiefpunkte: Potenziell günstige Einstiegspunkte
    - Fenster um Turning-Points: Erhöhte Vorsicht

    Attributes:
        cycle_length_days: ECM-Zyklus-Länge (default: 3141 Tage)
        event_window_days: Tage um Turning-Points für Signal-Modulation
        reference_date: Referenz-Turning-Point (Armstrong: 2015.75)

    Args:
        cycle_length_days: Länge des ECM-Zyklus in Tagen
        event_window_days: Fenster um Events für Signal-Modulation
        reference_date: Referenz-Datum für Zyklusberechnung
        config: Optional Config-Dict
        metadata: Optional StrategyMetadata

    Example:
        >>> # NUR FÜR RESEARCH
        >>> strategy = ArmstrongCycleStrategy()
        >>> # Wirft NotImplementedError - Placeholder
        >>> signals = strategy.generate_signals(df)

    Raises:
        NotImplementedError: generate_signals ist noch nicht implementiert

    Notes:
        Diese Strategie ist ein Research-Stub. Die eigentliche Signal-Logik
        wird in einer späteren Phase implementiert, nachdem:
        1. ECM-Turning-Points systematisch gesammelt wurden
        2. Event-Studien durchgeführt wurden
        3. Statistische Signifikanz geprüft wurde
    """

    KEY = "armstrong_cycle"

    # Research-only Konstanten
    IS_LIVE_READY = False
    ALLOWED_ENVIRONMENTS = ["offline_backtest", "research"]
    TIER = "r_and_d"

    # ECM-Konstanten (aus Armstrong-Literatur)
    DEFAULT_CYCLE_LENGTH = 3141  # Tage (≈ π × 1000)
    DEFAULT_HALF_CYCLE = 1570    # Tage (≈ 4.3 Jahre)
    DEFAULT_REFERENCE_DATE = "2015-10-01"  # ECM 2015.75 Turning Point

    def __init__(
        self,
        cycle_length_days: int = DEFAULT_CYCLE_LENGTH,
        event_window_days: int = 90,
        reference_date: str = DEFAULT_REFERENCE_DATE,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Armstrong Cycle Strategy.

        Args:
            cycle_length_days: ECM-Zyklus-Länge in Tagen
            event_window_days: Fenster um Turning-Points
            reference_date: Referenz-Turning-Point (ISO-Format)
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "cycle_length_days": cycle_length_days,
            "event_window_days": event_window_days,
            "reference_date": reference_date,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Research-only Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Armstrong Cycle v0 (Research)",
                description=(
                    "ECM-basierte Zyklus-Strategie für Research-Zwecke. "
                    "⚠️ NICHT FÜR LIVE-TRADING FREIGEGEBEN. "
                    "Basiert auf Martin Armstrongs Economic Confidence Model."
                ),
                version="0.1.0-research",
                author="Peak_Trade Research",
                regime="macro_overlay",
                tags=["research", "armstrong", "cycle", "ecm", "macro"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.cycle_length_days = self.config.get("cycle_length_days", cycle_length_days)
        self.event_window_days = self.config.get("event_window_days", event_window_days)
        self.reference_date = pd.Timestamp(
            self.config.get("reference_date", reference_date)
        )

        # Abgeleitete Konstanten
        self.half_cycle_days = self.cycle_length_days // 2
        self.quarter_cycle_days = self.cycle_length_days // 4

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.armstrong_cycle",
    ) -> "ArmstrongCycleStrategy":
        """
        Fabrikmethode für Config-basierte Instanziierung.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            ArmstrongCycleStrategy-Instanz
        """
        cycle_length = cfg.get(f"{section}.cycle_length_days", cls.DEFAULT_CYCLE_LENGTH)
        event_window = cfg.get(f"{section}.event_window_days", 90)
        ref_date = cfg.get(f"{section}.reference_date", cls.DEFAULT_REFERENCE_DATE)

        return cls(
            cycle_length_days=cycle_length,
            event_window_days=event_window,
            reference_date=ref_date,
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale basierend auf ECM-Zyklen.

        ⚠️ RESEARCH-STUB: Aktuell wird ein Dummy-Signal (flat) zurückgegeben.
        Die vollständige Implementierung erfolgt nach Research-Validierung.

        Args:
            data: DataFrame mit OHLCV-Daten

        Returns:
            Series mit Signalen (aktuell: 0 für alle Bars = flat)

        Raises:
            NotImplementedError: Wenn research_mode=False (Default in Produktion)

        Notes:
            Die vollständige Implementierung würde:
            1. ECM-Turning-Points relativ zum Index berechnen
            2. Event-Fenster markieren
            3. Regime-Filter basierend auf Zyklus-Phase generieren

            Dies ist absichtlich ein Stub, um Research-Iteration zu ermöglichen,
            ohne Live-Trading-Risiken.
        """
        # Research-Stub: Flat-Signal für alle Bars
        # TODO: Implementierung nach ECM-Validierung in Research-Phase

        # Wir geben ein neutrales Signal zurück (0 = flat)
        # Dies erlaubt Backtests ohne echte Trades
        signals = pd.Series(0, index=data.index, dtype=int)

        # Optional: Zyklus-Phase-Info als Debug-Marker
        # (kann später für Analyse verwendet werden)
        if hasattr(data.index, "to_pydatetime"):
            # Berechne Tage seit Referenz-Datum
            # Handle timezone-aware vs naive datetime
            index_for_calc = data.index
            ref_date = self.reference_date
            if hasattr(index_for_calc, 'tz') and index_for_calc.tz is not None:
                # Index ist tz-aware, konvertiere zu tz-naive für Berechnung
                index_for_calc = index_for_calc.tz_localize(None)
            if hasattr(ref_date, 'tz') and ref_date.tz is not None:
                ref_date = ref_date.tz_localize(None)
            days_since_ref = (index_for_calc - ref_date).days
            cycle_phase = (days_since_ref % self.cycle_length_days) / self.cycle_length_days

            # Markiere Event-Fenster (nahe Turning-Point)
            near_turning_point = (
                (cycle_phase < self.event_window_days / self.cycle_length_days) |
                (cycle_phase > 1 - self.event_window_days / self.cycle_length_days)
            )

            # Speichere Zyklus-Info in Signal-Metadata (für spätere Analyse)
            signals.attrs["cycle_phase"] = cycle_phase
            signals.attrs["near_turning_point"] = near_turning_point

        return signals

    def get_cycle_info(self, date: pd.Timestamp) -> Dict[str, Any]:
        """
        Gibt ECM-Zyklus-Informationen für ein bestimmtes Datum zurück.

        Args:
            date: Datum für Zyklus-Berechnung

        Returns:
            Dict mit:
            - days_since_reference: Tage seit Referenz-Datum
            - cycle_phase: Position im Zyklus (0.0 - 1.0)
            - is_near_turning_point: Ob nahe einem Turning-Point
            - next_turning_point: Nächster Turning-Point (Datum)
        """
        days_since_ref = (date - self.reference_date).days
        cycle_phase = (days_since_ref % self.cycle_length_days) / self.cycle_length_days

        # Nächster Turning-Point
        days_to_next = self.cycle_length_days - (days_since_ref % self.cycle_length_days)
        next_turning_point = date + pd.Timedelta(days=days_to_next)

        # Event-Fenster-Check
        is_near_turning_point = (
            cycle_phase < self.event_window_days / self.cycle_length_days or
            cycle_phase > 1 - self.event_window_days / self.cycle_length_days
        )

        return {
            "days_since_reference": days_since_ref,
            "cycle_phase": cycle_phase,
            "is_near_turning_point": is_near_turning_point,
            "next_turning_point": next_turning_point,
            "cycle_length_days": self.cycle_length_days,
        }

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.cycle_length_days < 30:
            raise ValueError(
                f"cycle_length_days ({self.cycle_length_days}) muss >= 30 sein"
            )
        if self.event_window_days < 1:
            raise ValueError(
                f"event_window_days ({self.event_window_days}) muss >= 1 sein"
            )
        if self.event_window_days >= self.cycle_length_days // 2:
            raise ValueError(
                f"event_window_days ({self.event_window_days}) muss < "
                f"half cycle ({self.cycle_length_days // 2}) sein"
            )

    def __repr__(self) -> str:
        return (
            f"<ArmstrongCycleStrategy("
            f"cycle={self.cycle_length_days}d, "
            f"window={self.event_window_days}d, "
            f"ref={self.reference_date.date()}) "
            f"[RESEARCH-ONLY]>"
        )


# =============================================================================
# LEGACY API (Falls benötigt für Backwards Compatibility)
# =============================================================================

def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility.

    DEPRECATED: Bitte ArmstrongCycleStrategy verwenden.
    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Signal-Series (0=flat für Research-Stub)
    """
    strategy = ArmstrongCycleStrategy(config=params)
    return strategy.generate_signals(df)
