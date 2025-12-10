# src/strategies/lopez_de_prado/meta_labeling_strategy.py
"""
Meta-Labeling Strategy – Research-Only
======================================

Diese Strategie implementiert das Meta-Labeling-Konzept nach
Marcos López de Prado als Meta-Layer über bestehenden Peak_Trade-Strategien.

⚠️ WICHTIG: RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

Diese Strategie ist ausschließlich für:
- Offline-Backtests
- Research & Analyse
- ML-Experimente mit Triple-Barrier-Labels

Hintergrund (López de Prado Meta-Labeling):
- Basis-Strategie generiert Richtungs-Signale (long/short)
- Triple-Barrier definiert Outcomes: TP, SL, oder Time-Exit
- Labels: +1 (profitabel), 0 (breakeven), -1 (verlustreich)
- Meta-Modell lernt, welche Signale tatsächlich gehandelt werden sollten

Vorteile:
- Entkopplung von Richtung (Primary Model) und Timing (Meta Model)
- Reduziert False Positives der Basis-Strategie
- Ermöglicht Bet-Sizing basierend auf Modell-Confidence

Ziel für Peak_Trade:
- Meta-Layer über bestehende Strategien (RSI, MA-Crossover, etc.)
- Verbesserung der Sharpe Ratio durch Signal-Filterung
- Foundation für ML-basiertes Trading

Warnung:
- ML-Modelle sind anfällig für Overfitting
- Sorgfältiges Feature Engineering erforderlich
- Nur für explorative Research-Analysen verwenden
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

import numpy as np
import pandas as pd

from ..base import BaseStrategy, StrategyMetadata


# =============================================================================
# CONFIG
# =============================================================================


@dataclass
class MetaLabelingConfig:
    """
    Konfiguration für Meta-Labeling Strategy.

    Attributes:
        base_strategy_id: ID der Basis-Strategie aus der Registry
        take_profit: Take-Profit-Schwelle (z.B. 0.02 = 2%)
        stop_loss: Stop-Loss-Schwelle (z.B. 0.01 = 1%)
        vertical_barrier_bars: Maximale Haltedauer in Bars
        prediction_horizon_bars: Vorhersage-Horizont für Labels
        use_triple_barrier: Ob Triple-Barrier-Method verwendet wird
        meta_model_type: Typ des Meta-Modells (Platzhalter)
        min_confidence: Minimale Modell-Confidence für Trade-Ausführung
    """

    base_strategy_id: str = "rsi_reversion"
    take_profit: Optional[float] = 0.02
    stop_loss: Optional[float] = 0.01
    vertical_barrier_bars: int = 20
    prediction_horizon_bars: int = 10
    use_triple_barrier: bool = True
    meta_model_type: str = "random_forest"  # Platzhalter
    min_confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Config zu Dictionary."""
        return {
            "base_strategy_id": self.base_strategy_id,
            "take_profit": self.take_profit,
            "stop_loss": self.stop_loss,
            "vertical_barrier_bars": self.vertical_barrier_bars,
            "prediction_horizon_bars": self.prediction_horizon_bars,
            "use_triple_barrier": self.use_triple_barrier,
            "meta_model_type": self.meta_model_type,
            "min_confidence": self.min_confidence,
        }


# =============================================================================
# STRATEGY
# =============================================================================


class MetaLabelingStrategy(BaseStrategy):
    """
    Meta-Labeling Strategy nach López de Prado.

    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

    Diese Strategie fungiert als Meta-Layer über einer bestehenden
    Peak_Trade-Strategie. Ein ML-Modell entscheidet, ob die Signale
    der Basis-Strategie tatsächlich gehandelt werden.

    Konzept:
    1. Basis-Strategie generiert Signale (long/short/flat)
    2. Triple-Barrier definiert Outcomes für jedes Signal
    3. Features werden für ML-Modell extrahiert
    4. Meta-Modell prognostiziert Signal-Qualität
    5. Nur Signale mit hoher Confidence werden durchgereicht

    Attributes:
        cfg: MetaLabelingConfig mit Strategie-Parametern
        base_strategy: Instanz der Basis-Strategie (lazy loaded)

    Args:
        base_strategy_id: ID der Basis-Strategie
        take_profit: TP-Schwelle für Triple-Barrier
        stop_loss: SL-Schwelle für Triple-Barrier
        vertical_barrier_bars: Zeit-Barriere in Bars
        config: Optional Config-Dict
        metadata: Optional StrategyMetadata

    Example:
        >>> # NUR FÜR RESEARCH
        >>> strategy = MetaLabelingStrategy(base_strategy_id="rsi_reversion")
        >>> signals = strategy.generate_signals(df)  # Research-Stub

    Notes:
        Diese Strategie ist ein Research-Stub. Die vollständige ML-Pipeline
        wird in einer späteren Phase implementiert nach:
        1. Implementierung der Triple-Barrier-Labeling-Funktion
        2. Feature-Engineering-Pipeline
        3. ML-Modell-Training und Evaluation
    """

    KEY = "meta_labeling"

    # Research-only Konstanten
    IS_LIVE_READY = False
    ALLOWED_ENVIRONMENTS = ["offline_backtest", "research"]
    TIER = "r_and_d"

    def __init__(
        self,
        base_strategy_id: str = "rsi_reversion",
        take_profit: Optional[float] = 0.02,
        stop_loss: Optional[float] = 0.01,
        vertical_barrier_bars: int = 20,
        prediction_horizon_bars: int = 10,
        use_triple_barrier: bool = True,
        meta_model_type: str = "random_forest",
        min_confidence: float = 0.5,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Meta-Labeling Strategy.

        Args:
            base_strategy_id: ID der Basis-Strategie in der Registry
            take_profit: Take-Profit-Schwelle (z.B. 0.02 = 2%)
            stop_loss: Stop-Loss-Schwelle (z.B. 0.01 = 1%)
            vertical_barrier_bars: Maximale Haltedauer in Bars
            prediction_horizon_bars: Vorhersage-Horizont
            use_triple_barrier: Ob Triple-Barrier verwendet wird
            meta_model_type: ML-Modell-Typ (Platzhalter)
            min_confidence: Minimale Confidence für Trade
            config: Optional Config-Dict
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "base_strategy_id": base_strategy_id,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "vertical_barrier_bars": vertical_barrier_bars,
            "prediction_horizon_bars": prediction_horizon_bars,
            "use_triple_barrier": use_triple_barrier,
            "meta_model_type": meta_model_type,
            "min_confidence": min_confidence,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Research-only Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Meta-Labeling v0 (López de Prado, Research)",
                description=(
                    "Meta-Layer-Strategie mit Triple-Barrier-Labeling. "
                    "⚠️ NICHT FÜR LIVE-TRADING FREIGEGEBEN. "
                    "Basiert auf Marcos López de Prados ML-Konzepten."
                ),
                version="0.1.0-research",
                author="Peak_Trade Research",
                regime="meta_layer",
                tags=["research", "lopez_de_prado", "meta_labeling", "triple_barrier", "ml"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Config-Objekt erstellen
        self.cfg = MetaLabelingConfig(
            base_strategy_id=self.config.get("base_strategy_id", base_strategy_id),
            take_profit=self.config.get("take_profit", take_profit),
            stop_loss=self.config.get("stop_loss", stop_loss),
            vertical_barrier_bars=self.config.get("vertical_barrier_bars", vertical_barrier_bars),
            prediction_horizon_bars=self.config.get("prediction_horizon_bars", prediction_horizon_bars),
            use_triple_barrier=self.config.get("use_triple_barrier", use_triple_barrier),
            meta_model_type=self.config.get("meta_model_type", meta_model_type),
            min_confidence=self.config.get("min_confidence", min_confidence),
        )

        # Lazy-loaded Basis-Strategie
        self._base_strategy: Optional[BaseStrategy] = None

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.meta_labeling",
    ) -> "MetaLabelingStrategy":
        """
        Fabrikmethode für Config-basierte Instanziierung.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            MetaLabelingStrategy-Instanz
        """
        base_id = cfg.get(f"{section}.base_strategy_id", "rsi_reversion")
        tp = cfg.get(f"{section}.take_profit", 0.02)
        sl = cfg.get(f"{section}.stop_loss", 0.01)
        vert_bars = cfg.get(f"{section}.vertical_barrier_bars", 20)
        pred_horizon = cfg.get(f"{section}.prediction_horizon_bars", 10)
        use_tb = cfg.get(f"{section}.use_triple_barrier", True)
        model_type = cfg.get(f"{section}.meta_model_type", "random_forest")
        min_conf = cfg.get(f"{section}.min_confidence", 0.5)

        return cls(
            base_strategy_id=base_id,
            take_profit=tp,
            stop_loss=sl,
            vertical_barrier_bars=vert_bars,
            prediction_horizon_bars=pred_horizon,
            use_triple_barrier=use_tb,
            meta_model_type=model_type,
            min_confidence=min_conf,
        )

    def _load_base_strategy(self) -> Optional[BaseStrategy]:
        """
        Lädt die Basis-Strategie aus der Registry.

        TODO: Implementierung mit echter Registry-Integration.

        Returns:
            Instanz der Basis-Strategie oder None
        """
        # TODO: Registry-Integration
        # from src.strategies.registry import get_strategy_spec, create_strategy_from_config
        # spec = get_strategy_spec(self.cfg.base_strategy_id)
        # return spec.cls()
        return None

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert gefilterte Signale via Meta-Labeling.

        ⚠️ RESEARCH-STUB: Aktuell wird ein Dummy-Signal (flat) zurückgegeben.
        Die vollständige ML-Pipeline erfolgt in einer späteren Phase.

        Geplante Logik (TODO):
        1. Basis-Strategie-Signale abrufen
        2. Triple-Barrier-Labels für jedes Signal berechnen
        3. Features für ML-Modell extrahieren
        4. Meta-Modell-Prediction für jedes Signal
        5. Nur Signale mit Confidence > min_confidence durchreichen

        Args:
            data: DataFrame mit OHLCV-Daten

        Returns:
            Series mit gefilterten Signalen (aktuell: 0 für alle Bars = flat)

        Notes:
            Die vollständige Implementierung würde umfassen:
            - Triple-Barrier-Labeling (compute_triple_barrier_labels)
            - Feature-Engineering (Volatility, Momentum, etc.)
            - ML-Modell (Random Forest, XGBoost, etc.)
            - Bet-Sizing basierend auf Confidence
        """
        # Validierung
        if "close" not in data.columns:
            raise ValueError(
                f"Spalte 'close' nicht in DataFrame. Verfügbar: {list(data.columns)}"
            )

        # =====================================================================
        # TODO: Meta-Labeling-Pipeline implementieren
        # =====================================================================
        #
        # Phase 1: Basis-Strategie-Signale
        # - base_strategy = self._load_base_strategy()
        # - base_signals = base_strategy.generate_signals(data)
        #
        # Phase 2: Triple-Barrier-Labels
        # - Für jedes Signal: TP, SL, Vertical Barrier definieren
        # - Label = +1 (TP reached), -1 (SL reached), 0 (vertical exit)
        # - labels = compute_triple_barrier_labels(
        #       data, base_signals, self.cfg.take_profit,
        #       self.cfg.stop_loss, self.cfg.vertical_barrier_bars
        #   )
        #
        # Phase 3: Feature-Engineering
        # - Volatility (rolling std, ATR)
        # - Momentum (returns, RSI, etc.)
        # - Market-Regime features
        # - features = self._extract_features(data, base_signals)
        #
        # Phase 4: Meta-Modell-Prediction
        # - Model nimmt Features, gibt Probability aus
        # - predictions = self._meta_model.predict_proba(features)
        #
        # Phase 5: Signal-Filterung
        # - Nur Signale mit Confidence > min_confidence
        # - Optional: Bet-Sizing basierend auf Confidence
        # - filtered_signals = base_signals.where(predictions > self.cfg.min_confidence, 0)
        # =====================================================================

        # Research-Stub: Flat-Signal für alle Bars
        signals = pd.Series(0, index=data.index, dtype=int)

        return signals

    def compute_triple_barrier_labels(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
    ) -> pd.Series:
        """
        Berechnet Triple-Barrier-Labels für Signale.

        TODO: Vollständige Implementierung nach López de Prado.

        Args:
            data: OHLCV-DataFrame
            signals: Basis-Strategie-Signale

        Returns:
            Labels: +1 (TP), -1 (SL), 0 (vertical barrier)
        """
        # Placeholder - gibt Nullen zurück
        return pd.Series(0, index=data.index, dtype=int)

    def _extract_features(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
    ) -> pd.DataFrame:
        """
        Extrahiert Features für das Meta-Modell.

        TODO: Feature-Engineering nach López de Prado:
        - Fractional Differentiation
        - Volatility-adjusted Returns
        - Market-Regime Indicators

        Args:
            data: OHLCV-DataFrame
            signals: Basis-Strategie-Signale

        Returns:
            Feature-DataFrame
        """
        # Placeholder - leeres DataFrame
        return pd.DataFrame(index=data.index)

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.cfg.take_profit is not None and self.cfg.take_profit <= 0:
            raise ValueError(
                f"take_profit ({self.cfg.take_profit}) muss > 0 sein"
            )
        if self.cfg.stop_loss is not None and self.cfg.stop_loss <= 0:
            raise ValueError(
                f"stop_loss ({self.cfg.stop_loss}) muss > 0 sein"
            )
        if self.cfg.vertical_barrier_bars < 1:
            raise ValueError(
                f"vertical_barrier_bars ({self.cfg.vertical_barrier_bars}) muss >= 1 sein"
            )
        if not 0 < self.cfg.min_confidence < 1:
            raise ValueError(
                f"min_confidence ({self.cfg.min_confidence}) muss zwischen 0 und 1 sein"
            )

    def __repr__(self) -> str:
        return (
            f"<MetaLabelingStrategy("
            f"base={self.cfg.base_strategy_id}, "
            f"tp={self.cfg.take_profit}, sl={self.cfg.stop_loss}, "
            f"vert={self.cfg.vertical_barrier_bars}bars) "
            f"[RESEARCH-ONLY]>"
        )


# =============================================================================
# LEGACY API (Falls benötigt für Backwards Compatibility)
# =============================================================================

def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility.

    DEPRECATED: Bitte MetaLabelingStrategy verwenden.
    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Signal-Series (0=flat für Research-Stub)
    """
    strategy = MetaLabelingStrategy(config=params)
    return strategy.generate_signals(df)


