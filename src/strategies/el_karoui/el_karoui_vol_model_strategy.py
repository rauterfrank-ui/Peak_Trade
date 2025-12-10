# src/strategies/el_karoui/el_karoui_vol_model_strategy.py
"""
El Karoui Volatility Model Strategy – Research-Only
====================================================

Diese Strategie implementiert ein Vol-Regime-basiertes Trading-Konzept,
inspiriert von Nicole El Karouis Arbeiten zu stochastischen Volatilitätsmodellen.

⚠️ WICHTIG: RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

Diese Strategie ist ausschließlich für:
- Offline-Backtests
- Research & Analyse
- Akademische Experimente mit Volatilitätsmodellen

Konzept:
- Nutzt das ElKarouiVolModel zur Regime-Erkennung
- Klassifiziert Vol-Regime (LOW/MEDIUM/HIGH)
- Passt Exposure basierend auf Regime an:
  * LOW-Vol → volle Zielallokation (long)
  * MEDIUM-Vol → reduziertes Exposure (long mit reduzierter Gewichtung)
  * HIGH-Vol → stark reduziertes oder kein Exposure (flat/reduziert)

Hintergrund (El-Karoui-Kontext):
- Stochastische Differentialgleichungen (SDEs) für Asset-Preise
- Lokale und stochastische Volatilitätsmodelle
- Martingal-Ansatz und risikoneutrale Bewertung
- Volatilität als Mean-Reverting-Prozess

Warnung:
- Komplexe mathematische Modelle erfordern sorgfältige Kalibrierung
- Modell-Risiko ist bei stochastischen Vol-Modellen signifikant
- Regime-Wechsel können abrupt erfolgen
- Nutze diese Strategie nur für explorative Analysen
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ..base import BaseStrategy, StrategyMetadata
from .vol_model import (
    VolRegime,
    ElKarouiVolConfig,
    ElKarouiVolModel,
)


# =============================================================================
# REGIME → POSITION MAPPING
# =============================================================================


# Default Mapping: Regime → Zielposition (1=long, 0=flat)
DEFAULT_REGIME_POSITION_MAP: Dict[VolRegime, int] = {
    VolRegime.LOW: 1,      # Long bei niedriger Volatilität
    VolRegime.MEDIUM: 1,   # Long bei mittlerer Volatilität (reduziert durch Scaling)
    VolRegime.HIGH: 0,     # Flat bei hoher Volatilität (Risk-Off)
}

# Konservatives Mapping: Nur in LOW-Vol long
CONSERVATIVE_REGIME_POSITION_MAP: Dict[VolRegime, int] = {
    VolRegime.LOW: 1,      # Long nur bei niedriger Vol
    VolRegime.MEDIUM: 0,   # Flat bei mittlerer Vol
    VolRegime.HIGH: 0,     # Flat bei hoher Vol
}

# Aggressives Mapping: Immer long, nur Scaling unterschiedlich
AGGRESSIVE_REGIME_POSITION_MAP: Dict[VolRegime, int] = {
    VolRegime.LOW: 1,      # Long bei niedriger Vol
    VolRegime.MEDIUM: 1,   # Long bei mittlerer Vol
    VolRegime.HIGH: 1,     # Long auch bei hoher Vol (reduziert durch Scaling)
}


# =============================================================================
# EL KAROUI VOLATILITY STRATEGY
# =============================================================================


class ElKarouiVolatilityStrategy(BaseStrategy):
    """
    El Karoui Volatility Model Strategy.

    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

    Diese Strategie nutzt das ElKarouiVolModel zur Volatilitäts-Regime-Erkennung
    und passt das Exposure entsprechend an.

    Konzept:
    - Berechnet realisierte Volatilität aus historischen Returns
    - Klassifiziert Vol-Regime (LOW / MEDIUM / HIGH) basierend auf Perzentilen
    - Generiert Signale basierend auf Regime:
      * LOW-Vol → long (Risk-On, geringe Marktrisiken)
      * MEDIUM-Vol → long (mit reduziertem Exposure via Scaling)
      * HIGH-Vol → flat (Risk-Off, erhöhte Marktrisiken)
    - Optional: Vol-Target-Scaling für Position-Sizing

    Attributes:
        vol_model: ElKarouiVolModel-Instanz für Vol-Berechnung
        regime_position_map: Mapping Regime → Position
        use_vol_scaling: Ob Vol-Target-Scaling angewendet werden soll

    Args:
        vol_window: Fenster für Volatilitätsschätzung
        lookback_window: Fenster für Perzentil-Berechnung
        low_threshold: Schwelle für LOW-Regime
        high_threshold: Schwelle für HIGH-Regime
        vol_target: Ziel-Volatilität p.a. für Scaling
        use_ewm: Exponentiell gewichtete Volatilität
        use_vol_scaling: Ob Vol-Scaling für Position-Sizing verwendet wird
        regime_position_map: Mapping-Strategie (dict oder "default"/"conservative"/"aggressive")
        config: Optional Config-Dict
        metadata: Optional StrategyMetadata

    Example:
        >>> # NUR FÜR RESEARCH
        >>> strategy = ElKarouiVolatilityStrategy()
        >>> signals = strategy.generate_signals(df)
        >>> print(signals.value_counts())

    Raises:
        RnDLiveTradingBlockedError: Bei Versuch, in Live/Paper/Testnet zu laufen
    """

    KEY = "el_karoui_vol_v1"

    # R&D-Only Konstanten - NICHT ÄNDERN!
    IS_LIVE_READY = False
    ALLOWED_ENVIRONMENTS = ["offline_backtest", "research"]
    TIER = "r_and_d"

    # Default-Parameter
    DEFAULT_VOL_WINDOW = 20
    DEFAULT_LOOKBACK_WINDOW = 252
    DEFAULT_LOW_THRESHOLD = 0.30
    DEFAULT_HIGH_THRESHOLD = 0.70
    DEFAULT_VOL_TARGET = 0.10

    def __init__(
        self,
        vol_window: int = DEFAULT_VOL_WINDOW,
        lookback_window: int = DEFAULT_LOOKBACK_WINDOW,
        low_threshold: float = DEFAULT_LOW_THRESHOLD,
        high_threshold: float = DEFAULT_HIGH_THRESHOLD,
        vol_target: float = DEFAULT_VOL_TARGET,
        use_ewm: bool = True,
        use_vol_scaling: bool = True,
        annualization_factor: float = 252.0,
        regime_position_map: Optional[Dict[VolRegime, int] | str] = None,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert El Karoui Volatility Strategy.

        Args:
            vol_window: Fenster für Volatilitätsschätzung
            lookback_window: Fenster für Perzentil-Berechnung
            low_threshold: Schwelle für LOW-Regime (Perzentil)
            high_threshold: Schwelle für HIGH-Regime (Perzentil)
            vol_target: Ziel-Volatilität p.a. für Scaling
            use_ewm: Ob exponentiell gewichtete Schätzung verwendet wird
            use_vol_scaling: Ob Vol-Target-Scaling angewendet wird
            annualization_factor: Faktor für Annualisierung
            regime_position_map: Mapping-Strategie (dict oder String)
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "vol_window": vol_window,
            "lookback_window": lookback_window,
            "low_threshold": low_threshold,
            "high_threshold": high_threshold,
            "vol_target": vol_target,
            "use_ewm": use_ewm,
            "use_vol_scaling": use_vol_scaling,
            "annualization_factor": annualization_factor,
            "regime_position_map": regime_position_map or "default",
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Research-only Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="El Karoui Volatility Model",
                description=(
                    "Volatilitäts-Regime-basierte Strategie für Research-Zwecke. "
                    "⚠️ NICHT FÜR LIVE-TRADING FREIGEGEBEN. "
                    "Basiert auf Konzepten von Nicole El Karoui zu stoch. Vol-Modellen."
                ),
                version="1.0.0-r_and_d",
                author="Peak_Trade Research",
                regime="vol_regime",
                tags=["research", "el_karoui", "volatility", "regime", "r_and_d"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.vol_window = self.config.get("vol_window", vol_window)
        self.lookback_window = self.config.get("lookback_window", lookback_window)
        self.low_threshold = self.config.get("low_threshold", low_threshold)
        self.high_threshold = self.config.get("high_threshold", high_threshold)
        self.vol_target = self.config.get("vol_target", vol_target)
        self.use_ewm = self.config.get("use_ewm", use_ewm)
        self.use_vol_scaling = self.config.get("use_vol_scaling", use_vol_scaling)
        self.annualization_factor = self.config.get("annualization_factor", annualization_factor)

        # Vol-Model erstellen
        vol_config = ElKarouiVolConfig(
            vol_window=self.vol_window,
            lookback_window=self.lookback_window,
            low_threshold=self.low_threshold,
            high_threshold=self.high_threshold,
            use_ewm=self.use_ewm,
            annualization_factor=self.annualization_factor,
            vol_target=self.vol_target,
        )
        self.vol_model = ElKarouiVolModel(vol_config)

        # Regime→Position Mapping
        self.regime_position_map = self._resolve_regime_position_map(
            self.config.get("regime_position_map", regime_position_map or "default")
        )

        # Validierung
        self.validate()

    def _resolve_regime_position_map(
        self, mapping: Dict[VolRegime, int] | str | None
    ) -> Dict[VolRegime, int]:
        """
        Löst das Regime→Position Mapping auf.

        Args:
            mapping: Dict oder String ("default", "conservative", "aggressive")

        Returns:
            Regime→Position Dict
        """
        if mapping is None or mapping == "default":
            return DEFAULT_REGIME_POSITION_MAP.copy()
        if mapping == "conservative":
            return CONSERVATIVE_REGIME_POSITION_MAP.copy()
        if mapping == "aggressive":
            return AGGRESSIVE_REGIME_POSITION_MAP.copy()
        if isinstance(mapping, dict):
            return mapping.copy()

        # Fallback
        return DEFAULT_REGIME_POSITION_MAP.copy()

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.el_karoui_vol_v1",
    ) -> "ElKarouiVolatilityStrategy":
        """
        Fabrikmethode für Config-basierte Instanziierung.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            ElKarouiVolatilityStrategy-Instanz
        """
        vol_window = cfg.get(f"{section}.vol_window", cls.DEFAULT_VOL_WINDOW)
        lookback = cfg.get(f"{section}.lookback_window", cls.DEFAULT_LOOKBACK_WINDOW)
        low_thresh = cfg.get(f"{section}.low_threshold", cls.DEFAULT_LOW_THRESHOLD)
        high_thresh = cfg.get(f"{section}.high_threshold", cls.DEFAULT_HIGH_THRESHOLD)
        vol_target = cfg.get(f"{section}.vol_target", cls.DEFAULT_VOL_TARGET)
        use_ewm = cfg.get(f"{section}.use_ewm", True)
        use_scaling = cfg.get(f"{section}.use_vol_scaling", True)
        ann_factor = cfg.get(f"{section}.annualization_factor", 252.0)
        regime_map = cfg.get(f"{section}.regime_position_map", "default")

        return cls(
            vol_window=vol_window,
            lookback_window=lookback,
            low_threshold=low_thresh,
            high_threshold=high_thresh,
            vol_target=vol_target,
            use_ewm=use_ewm,
            use_vol_scaling=use_scaling,
            annualization_factor=ann_factor,
            regime_position_map=regime_map,
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale basierend auf Volatilitäts-Regime.

        Die Strategie:
        1. Berechnet Returns aus Close-Preisen
        2. Schätzt realisierte Volatilität
        3. Klassifiziert Vol-Regime (LOW/MEDIUM/HIGH)
        4. Mappt Regime auf Positionierungssignal

        Args:
            data: DataFrame mit OHLCV-Daten (mindestens 'close')

        Returns:
            Series mit Signalen:
            - 1 = long
            - 0 = flat

        Example:
            >>> strategy = ElKarouiVolatilityStrategy()
            >>> signals = strategy.generate_signals(df)
            >>> print(signals.value_counts())
        """
        # Validierung
        if "close" not in data.columns:
            raise ValueError(
                f"Spalte 'close' nicht in DataFrame. Verfügbar: {list(data.columns)}"
            )

        if len(data) == 0:
            return pd.Series([], dtype=int)

        min_required = max(self.vol_window, 10)
        if len(data) < min_required:
            # Fallback: Flat-Signale wenn zu wenig Daten
            return pd.Series(0, index=data.index, dtype=int)

        # Returns berechnen
        returns = data["close"].pct_change()

        # Volatilität und Regime berechnen
        vol = self.vol_model.calculate_realized_vol(returns)
        percentiles = self.vol_model.calculate_vol_percentile(vol)

        # Signale generieren
        signals = []
        regimes = []
        scaling_factors = []

        for i in range(len(data)):
            if i < self.vol_window or pd.isna(percentiles.iloc[i]):
                # Warmup-Phase: Flat
                regime = VolRegime.MEDIUM
                position = 0
                scaling = 0.5
            else:
                # Regime aus Perzentil bestimmen
                pct = percentiles.iloc[i]
                regime = self.vol_model.regime_for_percentile(pct)

                # Position aus Mapping
                position = self.regime_position_map.get(regime, 0)

                # Optional: Vol-Scaling
                if self.use_vol_scaling:
                    current_vol = vol.iloc[i]
                    if pd.isna(current_vol) or current_vol <= 0:
                        scaling = 1.0
                    else:
                        scaling = self.vol_target / current_vol
                        scaling = max(0.2, min(2.0, scaling))
                else:
                    scaling = 1.0

            regimes.append(regime)
            signals.append(position)
            scaling_factors.append(scaling)

        signal_series = pd.Series(signals, index=data.index, dtype=int)

        # Metadaten für Analyse speichern
        signal_series.attrs["regimes"] = [r.value for r in regimes]
        signal_series.attrs["scaling_factors"] = scaling_factors
        signal_series.attrs["vol_annualized"] = vol
        signal_series.attrs["vol_percentiles"] = percentiles
        signal_series.attrs["vol_window"] = self.vol_window
        signal_series.attrs["vol_target"] = self.vol_target

        return signal_series

    def get_vol_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Gibt detaillierte Volatilitätsanalyse zurück.

        Args:
            data: DataFrame mit OHLCV-Daten

        Returns:
            Dict mit Analyse-Ergebnissen vom ElKarouiVolModel
        """
        if "close" not in data.columns or len(data) < self.vol_window:
            return {
                "current_vol": None,
                "vol_regime": VolRegime.MEDIUM,
                "vol_percentile": None,
                "scaling_factor": None,
            }

        returns = data["close"].pct_change().dropna()
        return self.vol_model.get_vol_analysis(returns)

    def get_current_regime(self, data: pd.DataFrame) -> VolRegime:
        """
        Gibt das aktuelle Vol-Regime zurück.

        Args:
            data: DataFrame mit OHLCV-Daten

        Returns:
            VolRegime (LOW, MEDIUM, HIGH)
        """
        if "close" not in data.columns or len(data) < self.vol_window:
            return VolRegime.MEDIUM

        returns = data["close"].pct_change().dropna()
        return self.vol_model.regime_for_returns(returns)

    def get_position_for_regime(self, regime: VolRegime) -> int:
        """
        Gibt die Zielposition für ein Regime zurück.

        Args:
            regime: VolRegime

        Returns:
            Position (0 oder 1)
        """
        return self.regime_position_map.get(regime, 0)

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.vol_window < 2:
            raise ValueError(
                f"vol_window ({self.vol_window}) muss >= 2 sein"
            )
        if self.lookback_window < self.vol_window:
            raise ValueError(
                f"lookback_window ({self.lookback_window}) muss >= vol_window ({self.vol_window}) sein"
            )
        if not 0 < self.low_threshold < 1:
            raise ValueError(
                f"low_threshold ({self.low_threshold}) muss zwischen 0 und 1 sein"
            )
        if not 0 < self.high_threshold < 1:
            raise ValueError(
                f"high_threshold ({self.high_threshold}) muss zwischen 0 und 1 sein"
            )
        if self.low_threshold >= self.high_threshold:
            raise ValueError(
                f"low_threshold ({self.low_threshold}) muss < high_threshold ({self.high_threshold}) sein"
            )

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Gibt Strategy-Metadaten zurück (für Logs/Reports).

        Returns:
            Dict mit Strategy-Info inkl. Tier
        """
        return {
            "id": "el_karoui_vol_v1",
            "name": self.meta.name,
            "category": "volatility",
            "tier": self.TIER,
            "is_live_ready": self.IS_LIVE_READY,
            "allowed_environments": self.ALLOWED_ENVIRONMENTS,
            "vol_window": self.vol_window,
            "vol_target": self.vol_target,
            "thresholds": [self.low_threshold, self.high_threshold],
        }

    def __repr__(self) -> str:
        return (
            f"<ElKarouiVolatilityStrategy("
            f"window={self.vol_window}, "
            f"thresholds=[{self.low_threshold:.2f}, {self.high_threshold:.2f}], "
            f"target={self.vol_target:.0%}) "
            f"[R&D-ONLY, tier={self.TIER}]>"
        )


# =============================================================================
# ALIAS FÜR BACKWARDS COMPATIBILITY
# =============================================================================


# Alias für die alte Klasse (ElKarouiVolModelStrategy)
ElKarouiVolModelStrategy = ElKarouiVolatilityStrategy


# =============================================================================
# LEGACY API (Falls benötigt für Backwards Compatibility)
# =============================================================================


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility.

    DEPRECATED: Bitte ElKarouiVolatilityStrategy verwenden.
    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Signal-Series
    """
    strategy = ElKarouiVolatilityStrategy(config=params)
    return strategy.generate_signals(df)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ElKarouiVolatilityStrategy",
    "ElKarouiVolModelStrategy",  # Alias für Backwards Compatibility
    "generate_signals",
    # Regime-Position Mappings
    "DEFAULT_REGIME_POSITION_MAP",
    "CONSERVATIVE_REGIME_POSITION_MAP",
    "AGGRESSIVE_REGIME_POSITION_MAP",
]
