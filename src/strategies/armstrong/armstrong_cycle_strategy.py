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

Hintergrund:
- ECM-Grundzyklus: 8,6 Jahre = 3141 Tage ≈ π × 1000
- Halb-/Teilzyklen für Timing-Signale
- Phasen: CRISIS, EXPANSION, CONTRACTION, PRE_CRISIS, POST_CRISIS

Warnung:
- Armstrong-Zyklen sind NICHT wissenschaftlich validiert
- Hindsight-Bias ist ein bekanntes Problem
- Nutze diese Strategie nur für explorative Analysen
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..base import BaseStrategy, StrategyMetadata
from .cycle_model import (
    ArmstrongPhase,
    ArmstrongCycleConfig,
    ArmstrongCycleModel,
)


# =============================================================================
# PHASE → POSITION MAPPING
# =============================================================================


# Default Mapping: Phase → Zielposition (1=long, 0=flat, -1=short)
DEFAULT_PHASE_POSITION_MAP: Dict[ArmstrongPhase, int] = {
    ArmstrongPhase.EXPANSION: 1,  # Long in Expansion
    ArmstrongPhase.POST_CRISIS: 1,  # Long nach Crisis (Erholung)
    ArmstrongPhase.CONTRACTION: 0,  # Flat in Contraction
    ArmstrongPhase.PRE_CRISIS: 0,  # Flat vor Crisis
    ArmstrongPhase.CRISIS: 0,  # Flat während Crisis (konservativ)
}

# Aggressives Mapping: Short in Crisis
AGGRESSIVE_PHASE_POSITION_MAP: Dict[ArmstrongPhase, int] = {
    ArmstrongPhase.EXPANSION: 1,  # Long in Expansion
    ArmstrongPhase.POST_CRISIS: 1,  # Long nach Crisis
    ArmstrongPhase.CONTRACTION: 0,  # Flat in Contraction
    ArmstrongPhase.PRE_CRISIS: -1,  # Short vor Crisis
    ArmstrongPhase.CRISIS: -1,  # Short während Crisis
}

# Konservatives Mapping: Nur Long in Expansion
CONSERVATIVE_PHASE_POSITION_MAP: Dict[ArmstrongPhase, int] = {
    ArmstrongPhase.EXPANSION: 1,  # Long nur in Expansion
    ArmstrongPhase.POST_CRISIS: 0,  # Flat sonst
    ArmstrongPhase.CONTRACTION: 0,
    ArmstrongPhase.PRE_CRISIS: 0,
    ArmstrongPhase.CRISIS: 0,
}


# =============================================================================
# ARMSTRONG CYCLE STRATEGY
# =============================================================================


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

    Features:
    - Verwendet ArmstrongCycleModel für Phasenbestimmung
    - Konfigurierbares Phase→Position Mapping
    - Risk-Multiplier basierend auf Zyklus-Phase
    - Deterministisch und gut testbar

    Attributes:
        cycle_model: ArmstrongCycleModel-Instanz
        phase_position_map: Mapping Phase → Position
        use_risk_scaling: Ob Risk-Multiplier angewendet werden soll

    Args:
        cycle_length_days: ECM-Zyklus-Länge in Tagen
        event_window_days: Fenster um Turning-Points
        reference_date: Referenz-Turning-Point (ISO-Format)
        phase_position_map: Dict oder String ("default", "aggressive", "conservative")
        use_risk_scaling: Ob Risk-Multiplier verwendet werden soll
        underlying: Underlying-Symbol (Index/Future/ETF)
        config: Optional Config-Dict
        metadata: Optional StrategyMetadata

    Example:
        >>> # NUR FÜR RESEARCH
        >>> strategy = ArmstrongCycleStrategy()
        >>> signals = strategy.generate_signals(df)

    Raises:
        RnDLiveTradingBlockedError: Bei Versuch, in Live/Paper/Testnet zu laufen
    """

    KEY = "armstrong_cycle"

    # R&D-Only Konstanten - NICHT ÄNDERN!
    IS_LIVE_READY = False
    ALLOWED_ENVIRONMENTS = ["offline_backtest", "research"]
    TIER = "r_and_d"

    # ECM-Konstanten (aus Armstrong-Literatur)
    DEFAULT_CYCLE_LENGTH = 3141  # Tage (≈ π × 1000)
    DEFAULT_HALF_CYCLE = 1570  # Tage (≈ 4.3 Jahre)
    DEFAULT_REFERENCE_DATE = "2015-10-01"  # ECM 2015.75 Turning Point

    def __init__(
        self,
        cycle_length_days: int = DEFAULT_CYCLE_LENGTH,
        event_window_days: int = 90,
        reference_date: str = DEFAULT_REFERENCE_DATE,
        phase_position_map: Optional[Dict[ArmstrongPhase, int] | str] = None,
        use_risk_scaling: bool = True,
        underlying: str = "SPX",
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Armstrong Cycle Strategy.

        Args:
            cycle_length_days: ECM-Zyklus-Länge in Tagen
            event_window_days: Fenster um Turning-Points
            reference_date: Referenz-Turning-Point (ISO-Format)
            phase_position_map: Mapping-Strategie (dict oder "default"/"aggressive"/"conservative")
            use_risk_scaling: Ob Risk-Multiplier angewendet werden soll
            underlying: Underlying-Symbol
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "cycle_length_days": cycle_length_days,
            "event_window_days": event_window_days,
            "reference_date": reference_date,
            "phase_position_map": phase_position_map or "default",
            "use_risk_scaling": use_risk_scaling,
            "underlying": underlying,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Research-only Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Armstrong Cycle Strategy",
                description=(
                    "ECM-basierte Zyklus-Strategie für Research-Zwecke. "
                    "⚠️ NICHT FÜR LIVE-TRADING FREIGEGEBEN. "
                    "Basiert auf Martin Armstrongs Economic Confidence Model."
                ),
                version="1.0.0-r_and_d",
                author="Peak_Trade Research",
                regime="macro_overlay",
                tags=["research", "armstrong", "cycle", "ecm", "macro", "r_and_d"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.cycle_length_days = self.config.get("cycle_length_days", cycle_length_days)
        self.event_window_days = self.config.get("event_window_days", event_window_days)
        self.reference_date_str = self.config.get("reference_date", reference_date)
        self.use_risk_scaling = self.config.get("use_risk_scaling", use_risk_scaling)
        self.underlying = self.config.get("underlying", underlying)

        # Referenz-Datum parsen
        self.reference_date = date.fromisoformat(self.reference_date_str)

        # Cycle-Model erstellen
        cycle_config = ArmstrongCycleConfig(
            reference_peak_date=self.reference_date,
            cycle_length_days=self.cycle_length_days,
        )
        self.cycle_model = ArmstrongCycleModel(cycle_config)

        # Phase→Position Mapping
        self.phase_position_map = self._resolve_phase_position_map(
            self.config.get("phase_position_map", phase_position_map or "default")
        )

        # Validierung
        self.validate()

    def _resolve_phase_position_map(
        self, mapping: Dict[ArmstrongPhase, int] | str | None
    ) -> Dict[ArmstrongPhase, int]:
        """
        Löst das Phase→Position Mapping auf.

        Args:
            mapping: Dict oder String ("default", "aggressive", "conservative")

        Returns:
            Phase→Position Dict
        """
        if mapping is None or mapping == "default":
            return DEFAULT_PHASE_POSITION_MAP.copy()
        if mapping == "aggressive":
            return AGGRESSIVE_PHASE_POSITION_MAP.copy()
        if mapping == "conservative":
            return CONSERVATIVE_PHASE_POSITION_MAP.copy()
        if isinstance(mapping, dict):
            return mapping.copy()

        # Fallback
        return DEFAULT_PHASE_POSITION_MAP.copy()

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
        phase_map = cfg.get(f"{section}.phase_position_map", "default")
        use_risk = cfg.get(f"{section}.use_risk_scaling", True)
        underlying = cfg.get(f"{section}.underlying", "SPX")

        return cls(
            cycle_length_days=cycle_length,
            event_window_days=event_window,
            reference_date=ref_date,
            phase_position_map=phase_map,
            use_risk_scaling=use_risk,
            underlying=underlying,
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale basierend auf ECM-Zyklen.

        Die Strategie bestimmt für jedes Datum die Zyklus-Phase und
        mappt diese auf eine Zielposition (long/flat/short).

        Args:
            data: DataFrame mit OHLCV-Daten (Index muss DatetimeIndex sein)

        Returns:
            Series mit Signalen:
            - 1 = long
            - 0 = flat
            - -1 = short

        Example:
            >>> strategy = ArmstrongCycleStrategy()
            >>> signals = strategy.generate_signals(df)
            >>> print(signals.value_counts())
        """
        # Validierung
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("DataFrame-Index muss ein DatetimeIndex sein")

        if len(data) == 0:
            return pd.Series([], dtype=int)

        # RESEARCH-STUB: Nur Flat-Signale zurückgeben
        # TODO: Implementiere echte ECM-Cycle-basierte Signale wenn validiert
        #
        # Die Logik für Cycle-Phase-Detection ist vorhanden im cycle_model,
        # aber für Research-Sicherheit geben wir nur Flat-Signale zurück.
        # Dies verhindert versehentlichen Einsatz in Live/Paper ohne explizite Freigabe.

        signal_series = pd.Series(0, index=data.index, dtype=int)

        # Metadaten für Analyse (auch bei Flat-Signalen nützlich)
        signal_series.attrs["cycle_length_days"] = self.cycle_length_days
        signal_series.attrs["reference_date"] = self.reference_date_str
        signal_series.attrs["is_research_stub"] = True

        return signal_series

    def get_cycle_info(self, dt: pd.Timestamp) -> Dict[str, Any]:
        """
        Gibt ECM-Zyklus-Informationen für ein bestimmtes Datum zurück.

        Args:
            dt: Datum für Zyklus-Berechnung

        Returns:
            Dict mit Zyklus-Informationen
        """
        return self.cycle_model.get_cycle_info(dt)

    def get_phase_for_date(self, dt: pd.Timestamp) -> ArmstrongPhase:
        """
        Gibt die Phase für ein Datum zurück.

        Args:
            dt: Datum

        Returns:
            ArmstrongPhase
        """
        return self.cycle_model.phase_for_date(dt)

    def get_position_for_phase(self, phase: ArmstrongPhase) -> int:
        """
        Gibt die Zielposition für eine Phase zurück.

        Args:
            phase: ArmstrongPhase

        Returns:
            Position (-1, 0, 1)
        """
        return self.phase_position_map.get(phase, 0)

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.cycle_length_days < 30:
            raise ValueError(f"cycle_length_days ({self.cycle_length_days}) muss >= 30 sein")
        if self.event_window_days < 1:
            raise ValueError(f"event_window_days ({self.event_window_days}) muss >= 1 sein")
        if self.event_window_days >= self.cycle_length_days // 2:
            raise ValueError(
                f"event_window_days ({self.event_window_days}) muss < "
                f"half cycle ({self.cycle_length_days // 2}) sein"
            )

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Gibt Strategy-Metadaten zurück (für Logs/Reports).

        Returns:
            Dict mit Strategy-Info inkl. Tier
        """
        return {
            "id": "armstrong_cycle_v1",
            "name": self.meta.name,
            "category": "cycles",
            "tier": self.TIER,
            "is_live_ready": self.IS_LIVE_READY,
            "allowed_environments": self.ALLOWED_ENVIRONMENTS,
            "cycle_length_days": self.cycle_length_days,
            "reference_date": self.reference_date_str,
            "underlying": self.underlying,
        }

    def __repr__(self) -> str:
        return (
            f"<ArmstrongCycleStrategy("
            f"cycle={self.cycle_length_days}d, "
            f"window={self.event_window_days}d, "
            f"ref={self.reference_date}) "
            f"[RESEARCH-ONLY, R&D-ONLY, tier={self.TIER}]>"
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
        Signal-Series
    """
    strategy = ArmstrongCycleStrategy(config=params)
    return strategy.generate_signals(df)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ArmstrongCycleStrategy",
    "generate_signals",
    # Phase-Position Mappings
    "DEFAULT_PHASE_POSITION_MAP",
    "AGGRESSIVE_PHASE_POSITION_MAP",
    "CONSERVATIVE_PHASE_POSITION_MAP",
]
