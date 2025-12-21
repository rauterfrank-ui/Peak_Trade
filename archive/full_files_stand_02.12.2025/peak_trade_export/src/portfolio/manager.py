"""
PortfolioManager: Multi-Strategie-Backtests mit Gewichtung.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
import pandas as pd

from src.backtest.engine import BacktestEngine
from src.backtest.results import BacktestResult
from src.strategies.registry import get_strategy


@dataclass
class StrategyConfig:
    """
    Konfiguration für eine Strategie im Portfolio.

    Attributes:
        name: Name der registrierten Strategie
        params: Strategie-Parameter
        weight: Gewichtung im Portfolio (default: 1.0)
    """

    name: str
    params: Dict[str, Any]
    weight: float = 1.0


class PortfolioManager:
    """
    Verwaltet Multi-Strategie-Portfolios.

    Kombiniert Signale mehrerer Strategien mit Gewichtung.
    """

    def __init__(self, engine: BacktestEngine) -> None:
        """
        Args:
            engine: BacktestEngine für Ausführung
        """
        self.engine = engine

    def run_portfolio(
        self,
        df: pd.DataFrame,
        strategies: List[StrategyConfig],
        initial_capital: float = 100_000.0,
        price_col: str = "close",
        normalize_weights: bool = True,
    ) -> BacktestResult:
        """
        Führt Multi-Strategie-Backtest durch.

        Args:
            df: Marktdaten
            strategies: Liste von StrategyConfig
            initial_capital: Startkapital
            price_col: Spaltenname für Preis
            normalize_weights: Gewichte auf Summe=1 normalisieren

        Returns:
            BacktestResult mit kombinierten Signalen

        Raises:
            ValueError: Wenn strategies leer oder Gewichtssumme=0
            TypeError: Wenn Strategie keine pd.Series zurückgibt
        """
        # Validierung
        if not strategies:
            raise ValueError("strategies-Liste darf nicht leer sein.")

        df = df.sort_index().copy()

        # Gewichtssumme berechnen
        if normalize_weights:
            weight_sum = sum(s.weight for s in strategies)
            if weight_sum == 0:
                raise ValueError("Gewichtssumme darf nicht 0 sein.")
        else:
            weight_sum = 1.0

        # Signale für jede Strategie generieren
        signals_dict = {}

        for sc in strategies:
            # Strategie laden
            StrategyCls = get_strategy(sc.name)
            strat = StrategyCls()

            # Signale generieren
            sig = strat.generate_signals(df, sc.params)

            # Validierung
            if not isinstance(sig, pd.Series):
                raise TypeError(
                    f"Strategie '{sc.name}' muss pd.Series zurückgeben, nicht {type(sig)}"
                )

            # Alignen
            sig = sig.sort_index()
            sig = sig.reindex(df.index).ffill().fillna(0.0).astype(float)

            # Effektives Gewicht
            if normalize_weights:
                eff_weight = sc.weight / weight_sum
            else:
                eff_weight = sc.weight

            # Speichern
            signals_dict[sc.name] = {
                "signals": sig,
                "weight": eff_weight,
                "params": sc.params,
            }

        # Signale kombinieren
        combined = pd.Series(0.0, index=df.index)

        for sc in strategies:
            sig_info = signals_dict[sc.name]
            combined += sig_info["signals"] * sig_info["weight"]

        # Auf [-1, +1] clippen
        combined = combined.clip(-1.0, 1.0)

        # Metadata vorbereiten
        metadata = {
            "mode": "portfolio",
            "portfolio_strategies": [
                {
                    "name": sc.name,
                    "params": sc.params,
                    "weight": signals_dict[sc.name]["weight"],
                }
                for sc in strategies
            ],
        }

        # Backtest ausführen
        result = self.engine.run_with_positions(
            df=df,
            target_positions=combined,
            initial_capital=initial_capital,
            price_col=price_col,
            metadata=metadata,
        )

        return result
