# src/strategies/ehlers/ehlers_cycle_filter_strategy.py
"""
Ehlers Cycle Filter Strategy – Research-Only
=============================================

Diese Strategie implementiert DSP-Techniken (Digital Signal Processing) nach
John Ehlers für Cycle-Detection und verbesserte Intraday-Signalqualität.

⚠️ WICHTIG: RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

Diese Strategie ist ausschließlich für:
- Offline-Backtests
- Research & Analyse
- DSP-Filter-Experimente

Hintergrund (Ehlers DSP-Konzepte):
- Super Smoother: Bessere Glättung als EMA/SMA, weniger Lag
- Two-Pole/Three-Pole Butterworth Filter
- Bandpass Filter: Isoliert dominante Marktzyklen
- Instantaneous Trendline: Adaptive Trendbestimmung
- Hilbert Transform: Cycle-Period-Messung

Ziel für Peak_Trade:
- Bessere Intraday-Signalqualität durch Noise-Reduktion
- Cycle-basiertes Timing für Entries/Exits
- Kombination mit bestehenden Strategien als Filter-Layer

Warnung:
- DSP-Konzepte erfordern sorgfältige Parametrisierung
- Lookahead-Bias bei falscher Implementierung möglich
- Nur für explorative Research-Analysen verwenden
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional

import numpy as np
import pandas as pd

from ..base import BaseStrategy, StrategyMetadata


# =============================================================================
# CONFIG
# =============================================================================


@dataclass
class EhlersCycleFilterConfig:
    """
    Konfiguration für Ehlers Cycle Filter Strategy.

    Attributes:
        smoother_type: Typ des Smoothers ("super_smoother", "two_pole", "three_pole")
        min_cycle_length: Minimale Zykluslänge in Bars
        max_cycle_length: Maximale Zykluslänge in Bars
        cycle_threshold: Schwelle für Cycle-Signal-Stärke (0.0 - 1.0)
        bandpass_bandwidth: Bandbreite des Bandpass-Filters
        lookback: Benötigte Historie in Bars
        use_hilbert_transform: Ob Hilbert-Transform für Cycle-Detection verwendet wird
    """

    smoother_type: Literal["super_smoother", "two_pole", "three_pole"] = "super_smoother"
    min_cycle_length: int = 6
    max_cycle_length: int = 50
    cycle_threshold: float = 0.5
    bandpass_bandwidth: float = 0.3
    lookback: int = 100
    use_hilbert_transform: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Config zu Dictionary."""
        return {
            "smoother_type": self.smoother_type,
            "min_cycle_length": self.min_cycle_length,
            "max_cycle_length": self.max_cycle_length,
            "cycle_threshold": self.cycle_threshold,
            "bandpass_bandwidth": self.bandpass_bandwidth,
            "lookback": self.lookback,
            "use_hilbert_transform": self.use_hilbert_transform,
        }


# =============================================================================
# STRATEGY
# =============================================================================


class EhlersCycleFilterStrategy(BaseStrategy):
    """
    Ehlers Cycle Filter Strategy – DSP-basierte Signalverbesserung.

    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

    Diese Strategie nutzt John Ehlers' DSP-Techniken zur Verbesserung der
    Signalqualität durch:
    - Noise-Reduktion via Super Smoother / Butterworth Filter
    - Cycle-Detection zur Identifikation dominanter Marktzyklen
    - Phase-basiertes Timing für optimale Entry/Exit-Punkte

    Konzept:
    - Preisdaten werden mit Ehlers-Filtern geglättet
    - Dominante Zyklusperiode wird gemessen (Hilbert Transform)
    - Bandpass-Filter isoliert die Cycle-Komponente
    - Entries bei Zyklus-Tief, Exits bei Zyklus-Hoch (oder umgekehrt)

    Attributes:
        cfg: EhlersCycleFilterConfig mit Strategie-Parametern

    Args:
        smoother_type: Art des Glättungsfilters
        min_cycle_length: Minimale Zykluslänge
        max_cycle_length: Maximale Zykluslänge
        cycle_threshold: Schwelle für Signal-Generierung
        config: Optional Config-Dict (überschreibt Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> # NUR FÜR RESEARCH
        >>> strategy = EhlersCycleFilterStrategy()
        >>> signals = strategy.generate_signals(df)

    Notes:
        Minimal-Slice: Super-Smoother auf ``close`` und einfache 0/1-Regel (Long, wenn
        ``close`` über dem geglätteten Wert liegt). Hilbert/Bandpass bleiben optional
        für spätere Phasen; Research-Only bleibt über Tier/``IS_LIVE_READY`` erzwungen.
    """

    KEY = "ehlers_cycle_filter"

    # Research-only Konstanten
    IS_LIVE_READY = False
    ALLOWED_ENVIRONMENTS = ["offline_backtest", "research"]
    TIER = "r_and_d"

    def __init__(
        self,
        smoother_type: str = "super_smoother",
        min_cycle_length: int = 6,
        max_cycle_length: int = 50,
        cycle_threshold: float = 0.5,
        bandpass_bandwidth: float = 0.3,
        lookback: int = 100,
        use_hilbert_transform: bool = True,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Ehlers Cycle Filter Strategy.

        Args:
            smoother_type: Typ des Smoothers
            min_cycle_length: Minimale Zykluslänge in Bars
            max_cycle_length: Maximale Zykluslänge in Bars
            cycle_threshold: Schwelle für Cycle-Signal-Stärke
            bandpass_bandwidth: Bandbreite des Bandpass-Filters
            lookback: Benötigte Historie in Bars
            use_hilbert_transform: Hilbert-Transform für Cycle-Detection
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "smoother_type": smoother_type,
            "min_cycle_length": min_cycle_length,
            "max_cycle_length": max_cycle_length,
            "cycle_threshold": cycle_threshold,
            "bandpass_bandwidth": bandpass_bandwidth,
            "lookback": lookback,
            "use_hilbert_transform": use_hilbert_transform,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Research-only Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Ehlers Cycle Filter v0 (Research)",
                description=(
                    "DSP-basierte Cycle-Filter-Strategie für verbesserte Signalqualität. "
                    "⚠️ NICHT FÜR LIVE-TRADING FREIGEGEBEN. "
                    "Basiert auf John Ehlers' Digital Signal Processing Techniken."
                ),
                version="0.1.0-research",
                author="Peak_Trade Research",
                regime="intraday_dsp",
                tags=["research", "ehlers", "dsp", "cycle", "filter", "intraday"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Config-Objekt erstellen
        self.cfg = EhlersCycleFilterConfig(
            smoother_type=self.config.get("smoother_type", smoother_type),
            min_cycle_length=self.config.get("min_cycle_length", min_cycle_length),
            max_cycle_length=self.config.get("max_cycle_length", max_cycle_length),
            cycle_threshold=self.config.get("cycle_threshold", cycle_threshold),
            bandpass_bandwidth=self.config.get("bandpass_bandwidth", bandpass_bandwidth),
            lookback=self.config.get("lookback", lookback),
            use_hilbert_transform=self.config.get("use_hilbert_transform", use_hilbert_transform),
        )

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.ehlers_cycle_filter",
    ) -> "EhlersCycleFilterStrategy":
        """
        Fabrikmethode für Config-basierte Instanziierung.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            EhlersCycleFilterStrategy-Instanz
        """
        smoother = cfg.get(f"{section}.smoother_type", "super_smoother")
        min_cycle = cfg.get(f"{section}.min_cycle_length", 6)
        max_cycle = cfg.get(f"{section}.max_cycle_length", 50)
        threshold = cfg.get(f"{section}.cycle_threshold", 0.5)
        bandwidth = cfg.get(f"{section}.bandpass_bandwidth", 0.3)
        lookback = cfg.get(f"{section}.lookback", 100)
        use_hilbert = cfg.get(f"{section}.use_hilbert_transform", True)

        return cls(
            smoother_type=smoother,
            min_cycle_length=min_cycle,
            max_cycle_length=max_cycle,
            cycle_threshold=threshold,
            bandpass_bandwidth=bandwidth,
            lookback=lookback,
            use_hilbert_transform=use_hilbert,
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus Super-Smoother und einfacher 0/1-Regel.

        Pro Bar: ``close`` wird mit dem Ehlers Super-Smoother geglättet; Long (1), wenn
        `close` über dem geglätteten Wert liegt, sonst Flat (0). Bei zu wenig Historie
        (``len < lookback``) werden nur Nullen zurückgegeben (kein harter Fehler).

        Args:
            data: DataFrame mit OHLCV-Daten (mindestens 'close')

        Returns:
            Series mit 0 (flat) oder 1 (long)
        """
        if "close" not in data.columns:
            raise ValueError(f"Spalte 'close' nicht in DataFrame. Verfügbar: {list(data.columns)}")

        if len(data) == 0:
            return pd.Series([], dtype=int)

        if len(data) < self.cfg.lookback:
            signals = pd.Series(0, index=data.index, dtype=int)
            signals.attrs["is_research_stub"] = False
            signals.attrs["insufficient_history"] = True
            return signals

        close = data["close"].astype(float)
        period = max(int(self.cfg.min_cycle_length), 2)

        # two_pole / three_pole: noch nicht separat — Super-Smoother als gemeinsamer Pfad
        smooth = self._super_smoother(close, period=period)

        # Einfache Regel: Long (1), wenn Close über dem Super-Smoother liegt
        signals = (close > smooth).astype(int)
        signals.attrs["is_research_stub"] = False
        signals.attrs["insufficient_history"] = False
        signals.attrs["smoother_period"] = period

        return signals

    def _super_smoother(self, series: pd.Series, period: int = 10) -> pd.Series:
        """
        Super Smoother Filter nach Ehlers (2-Pole Butterworth-ähnlich, rekursiv).

        Referenz: J. Ehlers — „Rocket Science for Traders“ / übliche Tradingview-Implementierung.

        Args:
            series: Input-Preisserie
            period: Glättungsperiode (≥ 2)

        Returns:
            Geglättete Serie (gleicher Index)
        """
        period = float(max(period, 2))
        x = series.to_numpy(dtype=float)
        n = len(x)
        if n == 0:
            return pd.Series([], dtype=float, index=series.index)

        a1 = np.exp(-np.sqrt(2.0) * np.pi / period)
        c2 = 2.0 * a1 * np.cos(np.sqrt(2.0) * np.pi / period)
        c3 = -a1 * a1
        c1 = 1.0 - c2 - c3

        out = np.zeros(n)
        for i in range(n):
            if i == 0:
                out[i] = x[i]
            elif i == 1:
                out[i] = c1 * (x[i] + x[i - 1]) / 2.0 + c2 * out[i - 1]
            else:
                out[i] = c1 * (x[i] + x[i - 1]) / 2.0 + c2 * out[i - 1] + c3 * out[i - 2]

        return pd.Series(out, index=series.index)

    def _measure_dominant_cycle(self, series: pd.Series) -> pd.Series:
        """
        Misst dominante Zyklusperiode via Hilbert Transform.

        TODO: Implementierung nach Ehlers:
        - Hilbert Transform für Quadratur-Komponente
        - Phase-Akkumulation für Periode-Messung
        - Adaptive Cycle-Period (6-50 Bars typisch)

        Args:
            series: Geglättete Preisserie

        Returns:
            Serie mit dominanter Zyklusperiode pro Bar
        """
        # Placeholder - konstante Periode
        return pd.Series(self.cfg.min_cycle_length, index=series.index)

    def _bandpass_filter(self, series: pd.Series, period: pd.Series, bandwidth: float) -> pd.Series:
        """
        Bandpass Filter zur Isolierung der Cycle-Komponente.

        TODO: Implementierung nach Ehlers:
        - Zentriert um dominante Frequenz
        - Bandwidth kontrolliert Selektivität
        - Output ist die isolierte Cycle-Komponente

        Args:
            series: Input-Serie
            period: Dominante Periode pro Bar
            bandwidth: Filter-Bandbreite

        Returns:
            Isolierte Cycle-Komponente
        """
        # Placeholder - gibt Nullen zurück
        return pd.Series(0.0, index=series.index)

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.cfg.min_cycle_length < 2:
            raise ValueError(f"min_cycle_length ({self.cfg.min_cycle_length}) muss >= 2 sein")
        if self.cfg.max_cycle_length <= self.cfg.min_cycle_length:
            raise ValueError(
                f"max_cycle_length ({self.cfg.max_cycle_length}) muss > "
                f"min_cycle_length ({self.cfg.min_cycle_length}) sein"
            )
        if not 0 < self.cfg.cycle_threshold < 1:
            raise ValueError(
                f"cycle_threshold ({self.cfg.cycle_threshold}) muss zwischen 0 und 1 sein"
            )
        if not 0 < self.cfg.bandpass_bandwidth < 1:
            raise ValueError(
                f"bandpass_bandwidth ({self.cfg.bandpass_bandwidth}) muss zwischen 0 und 1 sein"
            )

    def __repr__(self) -> str:
        return (
            f"<EhlersCycleFilterStrategy("
            f"smoother={self.cfg.smoother_type}, "
            f"cycle=[{self.cfg.min_cycle_length}-{self.cfg.max_cycle_length}], "
            f"threshold={self.cfg.cycle_threshold}) "
            f"[RESEARCH-ONLY]>"
        )


# =============================================================================
# LEGACY API (Falls benötigt für Backwards Compatibility)
# =============================================================================


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility.

    DEPRECATED: Bitte EhlersCycleFilterStrategy verwenden.
    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Signal-Series (0=flat, 1=long)
    """
    strategy = EhlersCycleFilterStrategy(config=params)
    return strategy.generate_signals(df)
