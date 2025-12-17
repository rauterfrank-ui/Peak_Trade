# src/strategies/regime_aware_portfolio.py
"""
Peak_Trade Regime-Aware Portfolio Strategy
==========================================

Portfolio-Strategie die mehrere Sub-Strategien kombiniert und ihre Gewichte
basierend auf Volatilitäts-Regime-Signalen skaliert.

Konzept:
- Kombiniert mehrere Sub-Strategien (z.B. Breakout, RSI-Reversion)
- Nutzt Vol-Regime-Filter um Regime zu bestimmen (Risk-On/Neutral/Risk-Off)
- Skaliert Strategie-Gewichte je nach Regime:
  - Risk-On (1): Volle Gewichte (z.B. 1.0)
  - Neutral (0): Reduzierte Gewichte (z.B. 0.5)
  - Risk-Off (-1): Keine Gewichte (0.0) oder Flat

Verwendung:
    >>> from src.strategies.regime_aware_portfolio import RegimeAwarePortfolioStrategy
    >>> strategy = RegimeAwarePortfolioStrategy(
    ...     components=["breakout_basic", "rsi_reversion_basic"],
    ...     base_weights={"breakout_basic": 0.6, "rsi_reversion_basic": 0.4},
    ...     regime_strategy="vol_regime_basic",
    ...     risk_on_scale=1.0,
    ...     neutral_scale=0.5,
    ...     risk_off_scale=0.0
    ... )
    >>> signals = strategy.generate_signals(df)
"""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from .base import BaseStrategy, StrategyMetadata

logger = logging.getLogger(__name__)


class RegimeAwarePortfolioStrategy(BaseStrategy):
    """
    Regime-Aware Portfolio Strategy - kombiniert mehrere Strategien mit Regime-Skalierung.

    Diese Strategie kombiniert mehrere Sub-Strategien und skaliert ihre kombinierten
    Signale basierend auf Volatilitäts-Regime-Signalen.

    Signale:
    - 1 (long): Kombiniertes Signal nach Regime-Skalierung > 0
    - -1 (short): Kombiniertes Signal nach Regime-Skalierung < 0
    - 0: Neutral / Flat

    Args:
        components: Liste von Strategie-Namen (Config-Keys)
        base_weights: Dict[component_name -> weight] mit Basisgewichten
        regime_strategy: Name der Vol-Regime-Strategie (muss regime_mode=True haben)
        mode: Skalierungs-Modus ("scale" oder "filter")
        risk_on_scale: Skalierungsfaktor für Risk-On-Regime (default: 1.0)
        neutral_scale: Skalierungsfaktor für Neutral-Regime (default: 0.5)
        risk_off_scale: Skalierungsfaktor für Risk-Off-Regime (default: 0.0)
        signal_threshold: Schwelle für Signal-Entscheidung (default: 0.3)
        config: Optional Config-Dict
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = RegimeAwarePortfolioStrategy(
        ...     components=["breakout_basic", "rsi_reversion_basic"],
        ...     base_weights={"breakout_basic": 0.6, "rsi_reversion_basic": 0.4},
        ...     regime_strategy="vol_regime_basic",
        ...     risk_on_scale=1.0,
        ...     neutral_scale=0.5,
        ...     risk_off_scale=0.0
        ... )
    """

    KEY = "regime_aware_portfolio"

    def __init__(
        self,
        components: list[str] | None = None,
        base_weights: dict[str, float] | None = None,
        regime_strategy: str | None = None,
        mode: str = "scale",
        risk_on_scale: float = 1.0,
        neutral_scale: float = 0.5,
        risk_off_scale: float = 0.0,
        signal_threshold: float = 0.3,
        config: dict[str, Any] | None = None,
        metadata: StrategyMetadata | None = None,
    ) -> None:
        """
        Initialisiert Regime-Aware Portfolio Strategy.

        Args:
            components: Liste von Strategie-Namen
            base_weights: Basisgewichte pro Komponente
            regime_strategy: Name der Regime-Strategie
            mode: "scale" oder "filter"
            risk_on_scale: Skalierungsfaktor Risk-On
            neutral_scale: Skalierungsfaktor Neutral
            risk_off_scale: Skalierungsfaktor Risk-Off
            signal_threshold: Signal-Schwelle
            config: Optional Config-Dict
            metadata: Optional Metadata
        """
        base_cfg: dict[str, Any] = {
            "components": components or [],
            "base_weights": base_weights or {},
            "regime_strategy": regime_strategy,
            "mode": mode,
            "risk_on_scale": risk_on_scale,
            "neutral_scale": neutral_scale,
            "risk_off_scale": risk_off_scale,
            "signal_threshold": signal_threshold,
        }
        if config:
            base_cfg.update(config)

        meta = metadata or StrategyMetadata(
            name="Regime-Aware Portfolio Strategy",
            description="Portfolio-Strategie mit Vol-Regime-basierter Gewichtung",
            version="1.0.0",
            author="Peak_Trade",
            regime="any",
            tags=["portfolio", "regime", "multi_strategy", "volatility"],
        )

        super().__init__(config=base_cfg, metadata=meta)

        # Parameter extrahieren
        self.components = list(self.config.get("components", []))
        self.base_weights = dict(self.config.get("base_weights", {}))
        self.regime_strategy_name = str(self.config.get("regime_strategy", ""))
        self.mode = str(self.config.get("mode", "scale")).lower()
        self.risk_on_scale = float(self.config.get("risk_on_scale", 1.0))
        self.neutral_scale = float(self.config.get("neutral_scale", 0.5))
        self.risk_off_scale = float(self.config.get("risk_off_scale", 0.0))
        self.signal_threshold = float(self.config.get("signal_threshold", 0.3))

        # Strategie-Instanzen (werden bei generate_signals geladen)
        self._component_strategies: list[BaseStrategy] = []
        self._regime_strategy: BaseStrategy | None = None

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if not self.components:
            raise ValueError("components darf nicht leer sein")

        if not self.regime_strategy_name:
            raise ValueError("regime_strategy muss gesetzt sein")

        if self.mode not in ("scale", "filter"):
            raise ValueError(f"mode ({self.mode}) muss 'scale' oder 'filter' sein")

        if not (0 <= self.signal_threshold <= 1):
            raise ValueError(
                f"signal_threshold ({self.signal_threshold}) muss zwischen 0 und 1 liegen"
            )

        # Basisgewichte normalisieren
        if self.base_weights:
            total = sum(abs(w) for w in self.base_weights.values())
            if total > 0:
                self.base_weights = {
                    k: w / total for k, w in self.base_weights.items()
                }

        # Fehlende Komponenten bekommen equal weights
        if len(self.base_weights) < len(self.components):
            equal_weight = 1.0 / len(self.components)
            for component in self.components:
                if component not in self.base_weights:
                    self.base_weights[component] = equal_weight

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "portfolio.regime_aware_breakout_rsi",
    ) -> RegimeAwarePortfolioStrategy:
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            RegimeAwarePortfolioStrategy-Instanz
        """
        # Lazy import

        components = cfg.get(f"{section}.components", [])
        base_weights = cfg.get(f"{section}.base_weights", {})
        regime_strategy = cfg.get(f"{section}.regime_strategy", None)
        mode = cfg.get(f"{section}.mode", "scale")
        risk_on_scale = cfg.get(f"{section}.risk_on_scale", 1.0)
        neutral_scale = cfg.get(f"{section}.neutral_scale", 0.5)
        risk_off_scale = cfg.get(f"{section}.risk_off_scale", 0.0)
        signal_threshold = cfg.get(f"{section}.signal_threshold", 0.3)

        return cls(
            components=components,
            base_weights=base_weights,
            regime_strategy=regime_strategy,
            mode=mode,
            risk_on_scale=risk_on_scale,
            neutral_scale=neutral_scale,
            risk_off_scale=risk_off_scale,
            signal_threshold=signal_threshold,
        )

    def _load_strategies(self, data: pd.DataFrame) -> None:
        """
        Lädt Sub-Strategien aus Registry (lazy loading).

        Args:
            data: OHLCV-DataFrame (für Validierung)
        """
        if self._component_strategies:
            return  # Bereits geladen

        from ..core.peak_config import load_config
        from .registry import create_strategy_from_config

        cfg = load_config()

        # Lade Komponenten-Strategien
        for component_name in self.components:
            try:
                strategy = create_strategy_from_config(component_name, cfg)
                self._component_strategies.append(strategy)
            except Exception as e:
                logger.error(
                    f"Konnte Komponente '{component_name}' nicht laden: {e}"
                )
                raise ValueError(
                    f"Komponente '{component_name}' konnte nicht geladen werden: {e}"
                )

        # Lade Regime-Strategie
        try:
            self._regime_strategy = create_strategy_from_config(self.regime_strategy_name, cfg)
            # Prüfe ob Regime-Mode aktiviert ist
            if hasattr(self._regime_strategy, 'regime_mode') and not self._regime_strategy.regime_mode:
                logger.warning(
                    f"Regime-Strategie '{self.regime_strategy_name}' hat regime_mode=False. "
                    f"Erwarte regime_mode=True für korrekte Regime-Signale (1/-1/0)."
                )
        except Exception as e:
            logger.error(
                f"Konnte Regime-Strategie '{self.regime_strategy_name}' nicht laden: {e}"
            )
            raise ValueError(
                f"Regime-Strategie '{self.regime_strategy_name}' konnte nicht geladen werden: {e}"
            )

    def _get_regime_scale(self, regime_value: int) -> float:
        """
        Mappt Regime-Wert auf Skalierungsfaktor.

        Args:
            regime_value: Regime-Signal (1=Risk-On, 0=Neutral, -1=Risk-Off)

        Returns:
            Skalierungsfaktor (0.0 - 1.0)
        """
        if regime_value == 1:
            return self.risk_on_scale
        elif regime_value == 0:
            return self.neutral_scale
        elif regime_value == -1:
            return self.risk_off_scale
        else:
            # Fallback für unbekannte Werte
            logger.warning(f"Unbekannter Regime-Wert: {regime_value}, verwende neutral_scale")
            return self.neutral_scale

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert regime-aware kombinierte Signale.

        Workflow:
        1. Lade Sub-Strategien (lazy)
        2. Generiere Signale aller Komponenten
        3. Gewichte Signale mit Basisgewichten
        4. Hole Regime-Signal
        5. Skaliere kombinierte Signale basierend auf Regime
        6. Wende Threshold an für finale Long/Short-Entscheidung

        Args:
            data: DataFrame mit OHLCV-Daten

        Returns:
            Series mit kombinierten Signalen (1=long, -1=short, 0=flat)

        Raises:
            ValueError: Wenn keine Komponenten oder Regime-Strategie fehlt
        """
        if not self.components:
            raise ValueError("Keine Komponenten definiert")

        # Lade Strategien (lazy)
        self._load_strategies(data)

        # 1. Generiere Signale aller Komponenten
        component_signals: dict[str, pd.Series] = {}
        for i, strategy in enumerate(self._component_strategies):
            component_name = self.components[i]
            try:
                signals = strategy.generate_signals(data)
                component_signals[component_name] = signals
            except Exception as e:
                logger.warning(
                    f"Komponente '{component_name}' konnte keine Signale generieren: {e}"
                )
                # Fülle mit Nullen
                component_signals[component_name] = pd.Series(
                    0, index=data.index, dtype=int
                )

        # 2. Kombiniere Signale mit Basisgewichten
        combined_signals = pd.Series(0.0, index=data.index, dtype=float)
        for component_name, signals in component_signals.items():
            weight = self.base_weights.get(component_name, 0.0)
            combined_signals += signals * weight

        # 3. Hole Regime-Signal
        if self._regime_strategy is None:
            raise ValueError("Regime-Strategie nicht geladen")

        try:
            regime_signals = self._regime_strategy.generate_signals(data)
        except Exception as e:
            logger.error(f"Regime-Strategie konnte keine Signale generieren: {e}")
            raise ValueError(f"Regime-Strategie fehlgeschlagen: {e}")

        # 4. Skaliere kombinierte Signale basierend auf Regime
        regime_scaled_signals = pd.Series(0.0, index=data.index, dtype=float)

        for i in range(len(data)):
            regime_value = regime_signals.iloc[i]

            # Prüfe ob gültiger Wert (nicht NaN)
            if pd.isna(regime_value):
                regime_value = 0  # Default zu Neutral

            # Hole Skalierungsfaktor
            scale = self._get_regime_scale(int(regime_value))

            # Skaliere kombiniertes Signal
            if self.mode == "filter":
                # Filter-Mode: 0 wenn Risk-Off, sonst normal
                if regime_value == -1:
                    regime_scaled_signals.iloc[i] = 0.0
                else:
                    regime_scaled_signals.iloc[i] = combined_signals.iloc[i] * scale
            else:
                # Scale-Mode: Immer skalieren
                regime_scaled_signals.iloc[i] = combined_signals.iloc[i] * scale

        # 5. Wende Threshold an für finale Long/Short-Entscheidung
        final_signals = pd.Series(0, index=data.index, dtype=int)
        final_signals = final_signals.where(
            ~(regime_scaled_signals > self.signal_threshold), 1
        )
        final_signals = final_signals.where(
            ~(regime_scaled_signals < -self.signal_threshold), -1
        )

        final_signals.name = "signal"
        return final_signals

    def get_component_signals(
        self,
        data: pd.DataFrame
    ) -> dict[str, pd.Series]:
        """
        Gibt Signale aller Komponenten-Strategien zurück.

        Nützlich für Analyse und Debugging.

        Args:
            data: OHLCV-DataFrame

        Returns:
            Dict[component_name -> signals]
        """
        self._load_strategies(data)

        result = {}
        for i, strategy in enumerate(self._component_strategies):
            component_name = self.components[i]
            try:
                signals = strategy.generate_signals(data)
                result[component_name] = signals
            except Exception as e:
                logger.warning(f"Komponente '{component_name}' fehlgeschlagen: {e}")
                result[component_name] = pd.Series(0, index=data.index)

        return result

    def get_regime_signals(
        self,
        data: pd.DataFrame
    ) -> pd.Series:
        """
        Gibt Regime-Signale zurück.

        Args:
            data: OHLCV-DataFrame

        Returns:
            Regime-Signale (1=Risk-On, 0=Neutral, -1=Risk-Off)
        """
        self._load_strategies(data)

        if self._regime_strategy is None:
            raise ValueError("Regime-Strategie nicht geladen")

        return self._regime_strategy.generate_signals(data)


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================


def generate_signals(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility.

    DEPRECATED: Bitte RegimeAwarePortfolioStrategy verwenden.

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Kombinierte Signal-Series
    """
    config = {
        "components": params.get("components", []),
        "base_weights": params.get("base_weights", {}),
        "regime_strategy": params.get("regime_strategy"),
        "mode": params.get("mode", "scale"),
        "risk_on_scale": params.get("risk_on_scale", 1.0),
        "neutral_scale": params.get("neutral_scale", 0.5),
        "risk_off_scale": params.get("risk_off_scale", 0.0),
        "signal_threshold": params.get("signal_threshold", 0.3),
    }

    strategy = RegimeAwarePortfolioStrategy(config=config)
    return strategy.generate_signals(df)

