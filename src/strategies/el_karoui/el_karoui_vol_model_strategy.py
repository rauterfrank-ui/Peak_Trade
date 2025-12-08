# src/strategies/el_karoui/el_karoui_vol_model_strategy.py
"""
El Karoui Stochastic Volatility Model Strategy – Research-Only
==============================================================

Diese Strategie implementiert Konzepte aus Nicole El Karouis Arbeiten zu
stochastischen Volatilitätsmodellen für explorative Research-Zwecke.

⚠️ WICHTIG: RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

Diese Strategie ist ausschließlich für:
- Offline-Backtests
- Research & Analyse
- Akademische Experimente mit Volatilitätsmodellen

Die generate_signals-Logik ist ein Placeholder/Stub. Die eigentliche Implementierung
erfolgt in einer späteren Research-Phase.

Hintergrund (El-Karoui-Kontext):
- Stochastische Differentialgleichungen (SDEs) für Asset-Preise
- Lokale und stochastische Volatilitätsmodelle
- Martingal-Ansatz und risikoneutrale Bewertung
- Siehe: src/docs/nicole_el_karoui_notes.md

Konzept:
- Nutzt Volatilitäts-Regime-Erkennung basierend auf SDE-Theorie
- Vergleicht realisierte vs. implizite Volatilität
- Identifiziert Misspricing / Relative-Value-Signale

Warnung:
- Komplexe mathematische Modelle erfordern sorgfältige Kalibrierung
- Modell-Risiko ist bei stochastischen Vol-Modellen signifikant
- Nutze diese Strategie nur für explorative Analysen
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..base import BaseStrategy, StrategyMetadata


class ElKarouiVolModelStrategy(BaseStrategy):
    """
    El Karoui Stochastic Volatility Model Strategy.

    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

    Diese Strategie nutzt Konzepte aus stochastischen Volatilitätsmodellen
    für Regime-Detection und Volatilitäts-basierte Signale.

    Konzept:
    - Schätzt lokale Volatilität aus historischen Daten
    - Identifiziert Volatilitäts-Regime (low/normal/high)
    - Generiert Signale basierend auf Vol-Regime-Wechseln

    Theoretischer Hintergrund:
    - Lokale Volatilität: σ(t, S_t) als Funktion von Zeit und Preis
    - Mean-Reversion der Volatilität (typisch für stoch. Vol-Modelle)
    - Volatilitäts-Surface-Analyse (für spätere Erweiterung)

    Attributes:
        vol_window: Fenster für Volatilitätsschätzung
        vol_threshold_low: Schwelle für "niedrige" Volatilität
        vol_threshold_high: Schwelle für "hohe" Volatilität
        use_ewm: Ob exponentiell gewichtete Schätzung verwendet wird

    Args:
        vol_window: Fenster für historische Volatilität
        vol_threshold_low: Untere Schwelle (z.B. 0.3 = 30. Perzentil)
        vol_threshold_high: Obere Schwelle (z.B. 0.7 = 70. Perzentil)
        use_ewm: Exponentiell gewichtete Volatilität
        config: Optional Config-Dict
        metadata: Optional StrategyMetadata

    Example:
        >>> # NUR FÜR RESEARCH
        >>> strategy = ElKarouiVolModelStrategy()
        >>> signals = strategy.generate_signals(df)  # Dummy-Signal

    Notes:
        Diese Strategie ist ein Research-Stub. Die vollständige Implementierung
        würde umfassen:
        1. Robuste Volatilitätsschätzung (realized vol, Parkinson, etc.)
        2. Volatilitäts-Regime-Klassifikation
        3. Optional: Vergleich mit impliziter Volatilität (wenn Optionsdaten verfügbar)
    """

    KEY = "el_karoui_vol_model"

    # Research-only Konstanten
    IS_LIVE_READY = False
    ALLOWED_ENVIRONMENTS = ["offline_backtest", "research"]
    TIER = "r_and_d"

    # Default-Parameter
    DEFAULT_VOL_WINDOW = 20
    DEFAULT_VOL_THRESHOLD_LOW = 0.3
    DEFAULT_VOL_THRESHOLD_HIGH = 0.7

    def __init__(
        self,
        vol_window: int = DEFAULT_VOL_WINDOW,
        vol_threshold_low: float = DEFAULT_VOL_THRESHOLD_LOW,
        vol_threshold_high: float = DEFAULT_VOL_THRESHOLD_HIGH,
        use_ewm: bool = True,
        annualization_factor: float = 252.0,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert El Karoui Vol Model Strategy.

        Args:
            vol_window: Fenster für Volatilitätsschätzung
            vol_threshold_low: Untere Schwelle für Regime-Klassifikation
            vol_threshold_high: Obere Schwelle für Regime-Klassifikation
            use_ewm: Ob exponentiell gewichtete Schätzung verwendet wird
            annualization_factor: Faktor für Annualisierung (252 für täglich)
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "vol_window": vol_window,
            "vol_threshold_low": vol_threshold_low,
            "vol_threshold_high": vol_threshold_high,
            "use_ewm": use_ewm,
            "annualization_factor": annualization_factor,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Research-only Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="El Karoui Vol Model v0 (Research)",
                description=(
                    "Stochastische Volatilitätsmodell-Strategie für Research-Zwecke. "
                    "⚠️ NICHT FÜR LIVE-TRADING FREIGEGEBEN. "
                    "Basiert auf Nicole El Karouis Arbeiten zu stoch. Vol-Modellen."
                ),
                version="0.1.0-research",
                author="Peak_Trade Research",
                regime="vol_regime",
                tags=["research", "el_karoui", "stochastic_vol", "volatility", "quant"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.vol_window = self.config.get("vol_window", vol_window)
        self.vol_threshold_low = self.config.get("vol_threshold_low", vol_threshold_low)
        self.vol_threshold_high = self.config.get("vol_threshold_high", vol_threshold_high)
        self.use_ewm = self.config.get("use_ewm", use_ewm)
        self.annualization_factor = self.config.get("annualization_factor", annualization_factor)

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.el_karoui_vol_model",
    ) -> "ElKarouiVolModelStrategy":
        """
        Fabrikmethode für Config-basierte Instanziierung.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            ElKarouiVolModelStrategy-Instanz
        """
        vol_window = cfg.get(f"{section}.vol_window", cls.DEFAULT_VOL_WINDOW)
        vol_low = cfg.get(f"{section}.vol_threshold_low", cls.DEFAULT_VOL_THRESHOLD_LOW)
        vol_high = cfg.get(f"{section}.vol_threshold_high", cls.DEFAULT_VOL_THRESHOLD_HIGH)
        use_ewm = cfg.get(f"{section}.use_ewm", True)
        ann_factor = cfg.get(f"{section}.annualization_factor", 252.0)

        return cls(
            vol_window=vol_window,
            vol_threshold_low=vol_low,
            vol_threshold_high=vol_high,
            use_ewm=use_ewm,
            annualization_factor=ann_factor,
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale basierend auf Volatilitäts-Regime.

        ⚠️ RESEARCH-STUB: Aktuell wird ein Dummy-Signal (flat) zurückgegeben.
        Die vollständige Implementierung erfolgt nach Research-Validierung.

        Args:
            data: DataFrame mit OHLCV-Daten (mindestens 'close')

        Returns:
            Series mit Signalen (aktuell: 0 für alle Bars = flat)

        Notes:
            Die vollständige Implementierung würde:
            1. Realisierte Volatilität berechnen
            2. Volatilitäts-Regime klassifizieren
            3. Signale basierend auf Regime-Wechseln generieren

            Dies ist absichtlich ein Stub, um Research-Iteration zu ermöglichen,
            ohne Live-Trading-Risiken.
        """
        # Validierung
        if "close" not in data.columns:
            raise ValueError(
                f"Spalte 'close' nicht in DataFrame. Verfügbar: {list(data.columns)}"
            )

        if len(data) < self.vol_window:
            raise ValueError(
                f"Brauche mind. {self.vol_window} Bars, habe nur {len(data)}"
            )

        # Berechne Returns
        returns = data["close"].pct_change()

        # Berechne realisierte Volatilität
        if self.use_ewm:
            vol = returns.ewm(span=self.vol_window, min_periods=self.vol_window).std()
        else:
            vol = returns.rolling(window=self.vol_window, min_periods=self.vol_window).std()

        # Annualisierte Volatilität
        vol_annualized = vol * np.sqrt(self.annualization_factor)

        # Volatilitäts-Regime klassifizieren (für Analyse)
        vol_quantiles = vol_annualized.rolling(
            window=min(252, len(data) // 2), min_periods=self.vol_window
        ).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False)

        # Regime-Klassifikation
        vol_regime = pd.Series("normal", index=data.index)
        vol_regime[vol_quantiles < self.vol_threshold_low] = "low"
        vol_regime[vol_quantiles > self.vol_threshold_high] = "high"

        # Research-Stub: Flat-Signal für alle Bars
        # Die eigentliche Trading-Logik würde hier basierend auf
        # vol_regime Signale generieren
        signals = pd.Series(0, index=data.index, dtype=int)

        # Speichere Vol-Info in Signal-Metadata (für spätere Analyse)
        signals.attrs["vol_annualized"] = vol_annualized
        signals.attrs["vol_regime"] = vol_regime
        signals.attrs["vol_quantiles"] = vol_quantiles

        return signals

    def get_vol_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Gibt detaillierte Volatilitätsanalyse zurück.

        Args:
            data: DataFrame mit OHLCV-Daten

        Returns:
            Dict mit:
            - current_vol: Aktuelle realisierte Volatilität
            - vol_regime: Aktuelles Volatilitäts-Regime
            - vol_percentile: Perzentil der aktuellen Volatilität
            - vol_history: Historische Volatilität (Series)
        """
        if "close" not in data.columns or len(data) < self.vol_window:
            return {
                "current_vol": None,
                "vol_regime": "unknown",
                "vol_percentile": None,
                "vol_history": None,
            }

        returns = data["close"].pct_change()

        if self.use_ewm:
            vol = returns.ewm(span=self.vol_window, min_periods=self.vol_window).std()
        else:
            vol = returns.rolling(window=self.vol_window, min_periods=self.vol_window).std()

        vol_annualized = vol * np.sqrt(self.annualization_factor)

        current_vol = vol_annualized.iloc[-1]
        vol_percentile = (vol_annualized < current_vol).mean()

        # Regime bestimmen
        if vol_percentile < self.vol_threshold_low:
            vol_regime = "low"
        elif vol_percentile > self.vol_threshold_high:
            vol_regime = "high"
        else:
            vol_regime = "normal"

        return {
            "current_vol": current_vol,
            "vol_regime": vol_regime,
            "vol_percentile": vol_percentile,
            "vol_history": vol_annualized,
        }

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.vol_window < 2:
            raise ValueError(
                f"vol_window ({self.vol_window}) muss >= 2 sein"
            )
        if not 0 < self.vol_threshold_low < 1:
            raise ValueError(
                f"vol_threshold_low ({self.vol_threshold_low}) muss zwischen 0 und 1 sein"
            )
        if not 0 < self.vol_threshold_high < 1:
            raise ValueError(
                f"vol_threshold_high ({self.vol_threshold_high}) muss zwischen 0 und 1 sein"
            )
        if self.vol_threshold_low >= self.vol_threshold_high:
            raise ValueError(
                f"vol_threshold_low ({self.vol_threshold_low}) muss < "
                f"vol_threshold_high ({self.vol_threshold_high}) sein"
            )

    def __repr__(self) -> str:
        return (
            f"<ElKarouiVolModelStrategy("
            f"window={self.vol_window}, "
            f"thresholds=[{self.vol_threshold_low:.2f}, {self.vol_threshold_high:.2f}], "
            f"ewm={self.use_ewm}) "
            f"[RESEARCH-ONLY]>"
        )


# =============================================================================
# LEGACY API (Falls benötigt für Backwards Compatibility)
# =============================================================================

def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility.

    DEPRECATED: Bitte ElKarouiVolModelStrategy verwenden.
    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Signal-Series (0=flat für Research-Stub)
    """
    strategy = ElKarouiVolModelStrategy(config=params)
    return strategy.generate_signals(df)
