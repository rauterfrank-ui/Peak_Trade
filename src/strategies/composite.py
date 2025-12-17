# src/strategies/composite.py
"""
Peak_Trade Composite Strategy (Phase 40)
=========================================

Multi-Strategy Combiner der mehrere Strategien zu einem Portfolio kombiniert.

Konzept:
- Kombiniert mehrere Sub-Strategien mit Gewichtung
- Aggregiert Signale zu einem finalen Signal
- Unterstützt verschiedene Aggregationsmethoden (weighted, voting, unanimous)
- Kann Filter wie VolRegimeFilter integrieren

Verwendung:
    >>> from src.strategies.composite import CompositeStrategy
    >>> from src.strategies.rsi_reversion import RsiReversionStrategy
    >>> from src.strategies.breakout import BreakoutStrategy
    >>>
    >>> composite = CompositeStrategy(
    ...     strategies=[
    ...         (RsiReversionStrategy(), 0.5),
    ...         (BreakoutStrategy(), 0.5),
    ...     ],
    ...     aggregation="weighted",
    ...     signal_threshold=0.3,
    ... )
    >>> signals = composite.generate_signals(df)
"""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from .base import BaseStrategy, StrategyMetadata

logger = logging.getLogger(__name__)


class CompositeStrategy(BaseStrategy):
    """
    Composite Strategy - kombiniert mehrere Strategien (Phase 40).

    Aggregiert Signale von mehreren Sub-Strategien zu einem finalen Signal.
    Unterstützt verschiedene Aggregationsmethoden:

    - "weighted": Gewichtetes Mittel der Signale
    - "voting": Mehrheitsentscheidung
    - "unanimous": Alle müssen übereinstimmen
    - "any_long": Long wenn mindestens eine Long ist
    - "any_short": Short wenn mindestens eine Short ist

    Signale:
    - 1 (long): Aggregiertes Signal > threshold
    - -1 (short): Aggregiertes Signal < -threshold
    - 0: Neutral

    Args:
        strategies: Liste von (BaseStrategy, weight) Tupeln oder nur Strategien
        weights: Optional separate Gewichtsliste (wenn strategies nur Strategien enthält)
        aggregation: Aggregationsmethode ("weighted", "voting", "unanimous", "any_long", "any_short")
        signal_threshold: Schwelle für Long/Short-Entscheidung (default: 0.3)
        require_all_valid: Wenn True, müssen alle Strategien gültige Signale liefern
        filter_strategy: Optional Filter-Strategie (z.B. VolRegimeFilter)
        config: Optional Config-Dict
        metadata: Optional StrategyMetadata

    Example:
        >>> # Mit Tupeln
        >>> composite = CompositeStrategy(
        ...     strategies=[
        ...         (RsiReversionStrategy(), 0.4),
        ...         (BreakoutStrategy(), 0.4),
        ...         (VolRegimeFilter(), 0.2),
        ...     ]
        ... )

        >>> # Mit separaten Weights
        >>> composite = CompositeStrategy(
        ...     strategies=[RsiReversionStrategy(), BreakoutStrategy()],
        ...     weights=[0.6, 0.4]
        ... )

        >>> # Mit Filter
        >>> composite = CompositeStrategy(
        ...     strategies=[RsiReversionStrategy(), BreakoutStrategy()],
        ...     filter_strategy=VolRegimeFilter()
        ... )
    """

    KEY = "composite"

    def __init__(
        self,
        strategies: list[BaseStrategy | tuple[BaseStrategy, float]] | None = None,
        weights: list[float] | None = None,
        aggregation: str = "weighted",
        signal_threshold: float = 0.3,
        require_all_valid: bool = False,
        filter_strategy: BaseStrategy | None = None,
        config: dict[str, Any] | None = None,
        metadata: StrategyMetadata | None = None,
    ) -> None:
        """
        Initialisiert Composite Strategy.

        Args:
            strategies: Liste von Strategien (oder Tupeln mit Gewichten)
            weights: Separate Gewichtsliste (optional)
            aggregation: Aggregationsmethode
            signal_threshold: Schwelle für Signal-Entscheidung
            require_all_valid: Alle Strategien müssen gültige Signale liefern
            filter_strategy: Filter der auf das finale Signal angewendet wird
            config: Optional Config-Dict
            metadata: Optional Metadata
        """
        base_cfg: dict[str, Any] = {
            "aggregation": aggregation,
            "signal_threshold": signal_threshold,
            "require_all_valid": require_all_valid,
        }
        if config:
            base_cfg.update(config)

        meta = metadata or StrategyMetadata(
            name="Composite Strategy",
            description="Multi-Strategy Combiner (Phase 40)",
            version="1.0.0",
            author="Peak_Trade",
            regime="any",
            tags=["composite", "multi_strategy", "portfolio"],
        )

        super().__init__(config=base_cfg, metadata=meta)

        # Parameter extrahieren
        self.aggregation = str(self.config.get("aggregation", "weighted")).lower()
        self.signal_threshold = float(self.config.get("signal_threshold", 0.3))
        self.require_all_valid = bool(self.config.get("require_all_valid", False))

        # Strategien und Gewichte verarbeiten
        self.strategies: list[BaseStrategy] = []
        self.weights: list[float] = []
        self._process_strategies(strategies, weights)

        # Filter-Strategie
        self.filter_strategy = filter_strategy

        # Validierung
        self.validate()

    def _process_strategies(
        self,
        strategies: list[BaseStrategy | tuple[BaseStrategy, float]] | None,
        weights: list[float] | None,
    ) -> None:
        """
        Verarbeitet Strategien und Gewichte aus verschiedenen Eingabeformaten.

        Args:
            strategies: Liste von Strategien oder (Strategie, Weight)-Tupeln
            weights: Optional separate Gewichtsliste
        """
        if strategies is None:
            self.strategies = []
            self.weights = []
            return

        # Prüfe ob strategies Tupeln enthält
        if strategies and isinstance(strategies[0], tuple):
            # Format: [(strategy, weight), ...]
            for item in strategies:
                if isinstance(item, tuple) and len(item) == 2:
                    strategy, weight = item
                    if isinstance(strategy, BaseStrategy):
                        self.strategies.append(strategy)
                        self.weights.append(float(weight))
                    else:
                        raise ValueError(
                            f"Erwarte BaseStrategy, bekommen: {type(strategy)}"
                        )
                else:
                    raise ValueError(
                        f"Erwarte (strategy, weight) Tupel, bekommen: {item}"
                    )
        else:
            # Format: [strategy1, strategy2, ...]
            for strategy in strategies:
                if isinstance(strategy, BaseStrategy):
                    self.strategies.append(strategy)
                else:
                    raise ValueError(
                        f"Erwarte BaseStrategy, bekommen: {type(strategy)}"
                    )

            # Weights verarbeiten
            if weights is not None:
                if len(weights) != len(self.strategies):
                    raise ValueError(
                        f"Anzahl Weights ({len(weights)}) muss Anzahl Strategien "
                        f"({len(self.strategies)}) entsprechen"
                    )
                self.weights = [float(w) for w in weights]
            else:
                # Equal weights
                n = len(self.strategies)
                self.weights = [1.0 / n] * n if n > 0 else []

        # Normalisiere Gewichte auf Summe 1
        if self.weights:
            total = sum(self.weights)
            if abs(total - 1.0) > 0.01:
                logger.debug(
                    f"Normalisiere Gewichte von Summe {total:.3f} auf 1.0"
                )
                self.weights = [w / total for w in self.weights]

    def add_strategy(
        self,
        strategy: BaseStrategy,
        weight: float | None = None
    ) -> None:
        """
        Fügt eine Strategie zur Composite hinzu.

        Args:
            strategy: Strategie-Instanz
            weight: Optional Gewicht (default: equal weight)
        """
        if not isinstance(strategy, BaseStrategy):
            raise ValueError(f"Erwarte BaseStrategy, bekommen: {type(strategy)}")

        self.strategies.append(strategy)

        if weight is not None:
            self.weights.append(float(weight))
        else:
            # Recalculate equal weights
            n = len(self.strategies)
            self.weights = [1.0 / n] * n

        # Re-normalisiere
        total = sum(self.weights)
        if total > 0:
            self.weights = [w / total for w in self.weights]

    def validate(self) -> None:
        """Validiert Parameter."""
        valid_aggregations = ["weighted", "voting", "unanimous", "any_long", "any_short"]
        if self.aggregation not in valid_aggregations:
            raise ValueError(
                f"aggregation ({self.aggregation}) muss einer von {valid_aggregations} sein"
            )

        if not (0 <= self.signal_threshold <= 1):
            raise ValueError(
                f"signal_threshold ({self.signal_threshold}) muss zwischen 0 und 1 liegen"
            )

        if self.strategies and self.weights:
            if len(self.strategies) != len(self.weights):
                raise ValueError(
                    f"Anzahl Strategien ({len(self.strategies)}) != Anzahl Weights ({len(self.weights)})"
                )

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.composite",
    ) -> CompositeStrategy:
        """
        Fabrikmethode für Core-Config.

        Lädt Strategien dynamisch aus Config.

        Config-Format:
            [strategy.composite]
            components = ["rsi_reversion", "breakout"]
            weights = [0.5, 0.5]
            aggregation = "weighted"
            signal_threshold = 0.3

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            CompositeStrategy-Instanz
        """
        # Lazy import um zirkuläre Abhängigkeit zu vermeiden
        from .registry import create_strategy_from_config

        aggregation = cfg.get(f"{section}.aggregation", "weighted")
        signal_threshold = cfg.get(f"{section}.signal_threshold", 0.3)
        require_all_valid = cfg.get(f"{section}.require_all_valid", False)

        # Komponenten laden
        component_keys = cfg.get(f"{section}.components", [])
        weights = cfg.get(f"{section}.weights", None)

        strategies: list[BaseStrategy] = []
        for key in component_keys:
            try:
                strategy = create_strategy_from_config(key, cfg)
                strategies.append(strategy)
            except Exception as e:
                logger.warning(f"Konnte Strategie '{key}' nicht laden: {e}")

        # Filter laden (optional)
        filter_key = cfg.get(f"{section}.filter", None)
        filter_strategy = None
        if filter_key:
            try:
                filter_strategy = create_strategy_from_config(filter_key, cfg)
            except Exception as e:
                logger.warning(f"Konnte Filter '{filter_key}' nicht laden: {e}")

        return cls(
            strategies=strategies,
            weights=weights,
            aggregation=aggregation,
            signal_threshold=signal_threshold,
            require_all_valid=require_all_valid,
            filter_strategy=filter_strategy,
        )

    def _aggregate_signals_weighted(
        self,
        signal_matrix: pd.DataFrame
    ) -> pd.Series:
        """
        Aggregiert Signale via gewichtetes Mittel.

        Args:
            signal_matrix: DataFrame mit Signalen aller Strategien

        Returns:
            Aggregierte Signale
        """
        weighted_sum = pd.Series(0.0, index=signal_matrix.index)
        for i, col in enumerate(signal_matrix.columns):
            weighted_sum += signal_matrix[col] * self.weights[i]

        return weighted_sum

    def _aggregate_signals_voting(
        self,
        signal_matrix: pd.DataFrame
    ) -> pd.Series:
        """
        Aggregiert Signale via Mehrheitsentscheidung.

        Args:
            signal_matrix: DataFrame mit Signalen

        Returns:
            Aggregierte Signale (-1, 0, 1)
        """
        # Zähle Long, Short, Flat
        n_long = (signal_matrix > 0).sum(axis=1)
        n_short = (signal_matrix < 0).sum(axis=1)
        n_strategies = len(self.strategies)
        majority = n_strategies / 2

        result = pd.Series(0, index=signal_matrix.index, dtype=int)
        result = result.where(~(n_long > majority), 1)
        result = result.where(~(n_short > majority), -1)

        return result

    def _aggregate_signals_unanimous(
        self,
        signal_matrix: pd.DataFrame
    ) -> pd.Series:
        """
        Aggregiert Signale: Alle müssen übereinstimmen.

        Args:
            signal_matrix: DataFrame mit Signalen

        Returns:
            Aggregierte Signale
        """
        # Alle Long → 1, Alle Short → -1, sonst 0
        all_long = (signal_matrix > 0).all(axis=1)
        all_short = (signal_matrix < 0).all(axis=1)

        result = pd.Series(0, index=signal_matrix.index, dtype=int)
        result = result.where(~all_long, 1)
        result = result.where(~all_short, -1)

        return result

    def _aggregate_signals_any(
        self,
        signal_matrix: pd.DataFrame,
        direction: str
    ) -> pd.Series:
        """
        Aggregiert: Long/Short wenn mindestens eine Strategie das Signal gibt.

        Args:
            signal_matrix: DataFrame mit Signalen
            direction: "long" oder "short"

        Returns:
            Aggregierte Signale
        """
        if direction == "long":
            any_long = (signal_matrix > 0).any(axis=1)
            result = pd.Series(0, index=signal_matrix.index, dtype=int)
            result = result.where(~any_long, 1)
        else:  # short
            any_short = (signal_matrix < 0).any(axis=1)
            result = pd.Series(0, index=signal_matrix.index, dtype=int)
            result = result.where(~any_short, -1)

        return result

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert kombinierte Signale aus allen Sub-Strategien.

        Workflow:
        1. Für jede Sub-Strategie Signale generieren
        2. Signale gemäß aggregation-Methode kombinieren
        3. Optional: Filter anwenden
        4. Threshold für finale Long/Short-Entscheidung

        Args:
            data: DataFrame mit OHLCV-Daten

        Returns:
            Series mit kombinierten Signalen (1=long, -1=short, 0=flat)

        Raises:
            ValueError: Wenn keine Strategien definiert
        """
        if not self.strategies:
            raise ValueError("Keine Strategien in CompositeStrategy definiert")

        # Signale aller Strategien sammeln
        signal_dict: dict[str, pd.Series] = {}
        valid_strategies = 0

        for i, strategy in enumerate(self.strategies):
            try:
                signals = strategy.generate_signals(data)
                signal_dict[f"strategy_{i}_{strategy.key}"] = signals
                valid_strategies += 1
            except Exception as e:
                logger.warning(
                    f"Strategie {strategy.key} konnte keine Signale generieren: {e}"
                )
                if self.require_all_valid:
                    raise ValueError(
                        f"require_all_valid=True aber Strategie {strategy.key} fehlgeschlagen: {e}"
                    )
                # Fülle mit Nullen
                signal_dict[f"strategy_{i}_{strategy.key}"] = pd.Series(
                    0, index=data.index, dtype=int
                )

        if valid_strategies == 0:
            raise ValueError("Keine Strategie konnte gültige Signale generieren")

        # Signal-Matrix erstellen
        signal_matrix = pd.DataFrame(signal_dict)

        # Aggregation durchführen
        if self.aggregation == "weighted":
            aggregated = self._aggregate_signals_weighted(signal_matrix)

            # Threshold anwenden
            final_signals = pd.Series(0, index=data.index, dtype=int)
            final_signals = final_signals.where(
                ~(aggregated > self.signal_threshold), 1
            )
            final_signals = final_signals.where(
                ~(aggregated < -self.signal_threshold), -1
            )

        elif self.aggregation == "voting":
            final_signals = self._aggregate_signals_voting(signal_matrix)

        elif self.aggregation == "unanimous":
            final_signals = self._aggregate_signals_unanimous(signal_matrix)

        elif self.aggregation == "any_long":
            final_signals = self._aggregate_signals_any(signal_matrix, "long")

        elif self.aggregation == "any_short":
            final_signals = self._aggregate_signals_any(signal_matrix, "short")

        else:
            raise ValueError(f"Unbekannte Aggregation: {self.aggregation}")

        # Filter anwenden (falls vorhanden)
        if self.filter_strategy is not None:
            try:
                filter_mask = self.filter_strategy.generate_signals(data)
                final_signals = final_signals * filter_mask
            except Exception as e:
                logger.warning(f"Filter-Strategie fehlgeschlagen: {e}")

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
            Dict[strategy_key -> signals]
        """
        result = {}
        for strategy in self.strategies:
            try:
                signals = strategy.generate_signals(data)
                result[strategy.key] = signals
            except Exception as e:
                logger.warning(f"Strategie {strategy.key} fehlgeschlagen: {e}")
                result[strategy.key] = pd.Series(0, index=data.index)

        return result


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================


def generate_signals(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility mit alter API.

    DEPRECATED: Bitte CompositeStrategy verwenden.

    Diese Funktion erwartet dass Strategien bereits instanziiert und
    in params["strategies"] übergeben werden.

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict mit "strategies" Liste

    Returns:
        Kombinierte Signal-Series
    """
    strategies = params.get("strategies", [])
    weights = params.get("weights")
    aggregation = params.get("aggregation", "weighted")
    signal_threshold = params.get("signal_threshold", 0.3)

    composite = CompositeStrategy(
        strategies=strategies,
        weights=weights,
        aggregation=aggregation,
        signal_threshold=signal_threshold,
    )

    return composite.generate_signals(df)


def get_strategy_description(params: dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    strategies = params.get("strategies", [])
    aggregation = params.get("aggregation", "weighted")
    threshold = params.get("signal_threshold", 0.3)

    strategy_names = [s.key if hasattr(s, "key") else str(s) for s in strategies]

    return f"""
Composite Strategy (Phase 40)
==============================
Aggregation:       {aggregation}
Signal Threshold:  {threshold}
Komponenten:       {', '.join(strategy_names) if strategy_names else 'Keine'}

Konzept:
- Kombiniert {len(strategies)} Strategien
- Aggregiert Signale via {aggregation}-Methode
- Long wenn aggregiert > {threshold}
- Short wenn aggregiert < -{threshold}
"""
