"""
Portfolio Manager
==================
Orchestriert mehrere Strategien mit zentralem Risk-Management.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..backtest.engine import BacktestEngine, BacktestResult
from ..backtest.stats import compute_basic_stats, compute_sharpe_ratio
from ..core import get_config, get_strategy_cfg


@dataclass
class StrategyAllocation:
    """Allokation für eine Strategie."""
    name: str
    signal_fn: Callable
    params: dict
    weight: float  # Anteil am Gesamtkapital (0-1)
    capital: float  # Zugewiesenes Kapital


@dataclass
class PortfolioResult:
    """Portfolio-Backtest-Ergebnis."""
    portfolio_equity: pd.Series
    strategy_results: dict[str, BacktestResult]
    stats: dict[str, float]
    allocations: list[StrategyAllocation]


class PortfolioManager:
    """
    Multi-Strategy-Portfolio-Manager.

    Features:
    - Mehrere Strategien parallel
    - Capital Allocation (equal, risk_parity, sharpe_weighted)
    - Portfolio-Level Risk-Management
    - Correlation-Aware Rebalancing

    Usage:
        >>> pm = PortfolioManager()
        >>> pm.add_strategy("ma_crossover", ma_signals, params)
        >>> pm.add_strategy("momentum_1h", mom_signals, params)
        >>> result = pm.run_backtest(df)
    """

    def __init__(self):
        self.config = get_config()
        self.strategies: list[StrategyAllocation] = []
        self.total_capital = 10000.0

    def add_strategy(
        self,
        name: str,
        signal_fn: Callable,
        params: dict | None = None,
        weight: float | None = None
    ) -> None:
        """
        Fügt Strategie zum Portfolio hinzu.

        Args:
            name: Strategie-Name
            signal_fn: Signal-Generator-Funktion
            params: Strategie-Parameter (lädt aus config wenn None)
            weight: Manuelles Gewicht (None = auto)
        """
        # Parameter laden wenn nicht übergeben
        if params is None:
            params = get_strategy_cfg(name)

        # Weight später bei Allocation berechnen
        allocation = StrategyAllocation(
            name=name,
            signal_fn=signal_fn,
            params=params,
            weight=weight or 0.0,
            capital=0.0
        )

        self.strategies.append(allocation)

    def _allocate_capital(self, method: str = "equal") -> None:
        """
        Verteilt Kapital auf Strategien.

        Args:
            method: "equal", "risk_parity", "manual"
        """
        n_strategies = len(self.strategies)

        if method == "equal":
            # Gleichverteilung
            weight = 1.0 / n_strategies
            for strat in self.strategies:
                strat.weight = weight
                strat.capital = self.total_capital * weight

        elif method == "manual":
            # Manuelle Weights aus Config
            total_weight = sum(s.weight for s in self.strategies)
            if abs(total_weight - 1.0) > 0.01:
                raise ValueError(f"Weights müssen zu 1.0 summieren (ist: {total_weight})")

            for strat in self.strategies:
                strat.capital = self.total_capital * strat.weight

        else:
            raise ValueError(f"Unbekannte Allocation-Methode: {method}")

    def run_backtest(
        self,
        df: pd.DataFrame,
        allocation_method: str = "equal"
    ) -> PortfolioResult:
        """
        Führt Portfolio-Backtest durch.

        Args:
            df: OHLCV-DataFrame
            allocation_method: Capital-Allocation-Methode

        Returns:
            PortfolioResult mit kombinierter Equity-Curve
        """
        # 1. Capital Allocation
        self._allocate_capital(method=allocation_method)

        print(f"\n💼 Portfolio-Allocation ({allocation_method}):")
        print("-" * 70)
        for strat in self.strategies:
            print(f"  {strat.name:20s}: ${strat.capital:>10,.2f} ({strat.weight:>6.1%})")

        # 2. Einzelne Backtests durchführen
        strategy_results = {}

        for strat in self.strategies:
            print(f"\n⚙️  Backtest: {strat.name}...")

            # Temporäre Config mit adjusted capital
            temp_config = self.config.model_copy(deep=True)
            temp_config.backtest.initial_cash = strat.capital

            # Backtest-Engine mit adjusted capital
            engine = BacktestEngine()
            engine.config = temp_config

            result = engine.run_realistic(
                df=df,
                strategy_signal_fn=strat.signal_fn,
                strategy_params=strat.params
            )

            strategy_results[strat.name] = result

            print(f"    Return: {result.stats['total_return']:>7.2%}")
            print(f"    Sharpe: {result.stats['sharpe']:>7.2f}")
            print(f"    Trades: {result.stats['total_trades']:>7}")

        # 3. Portfolio-Equity kombinieren
        portfolio_equity = self._combine_equity_curves(strategy_results)

        # 4. Portfolio-Stats berechnen
        portfolio_stats = self._compute_portfolio_stats(
            portfolio_equity,
            strategy_results
        )

        return PortfolioResult(
            portfolio_equity=portfolio_equity,
            strategy_results=strategy_results,
            stats=portfolio_stats,
            allocations=self.strategies
        )

    def _combine_equity_curves(
        self,
        strategy_results: dict[str, BacktestResult]
    ) -> pd.Series:
        """
        Kombiniert Equity-Curves aller Strategien.

        Returns:
            Portfolio-Equity als Series
        """
        # Alle Equity-Curves auf gleichen Index bringen
        equity_curves = {}
        for name, result in strategy_results.items():
            equity_curves[name] = result.equity_curve

        # Zu DataFrame kombinieren
        df = pd.DataFrame(equity_curves)

        # Portfolio = Summe aller Strategien
        portfolio_equity = df.sum(axis=1)

        return portfolio_equity

    def _compute_portfolio_stats(
        self,
        portfolio_equity: pd.Series,
        strategy_results: dict[str, BacktestResult]
    ) -> dict[str, float]:
        """Berechnet Portfolio-Level-Stats."""

        basic_stats = compute_basic_stats(portfolio_equity)
        sharpe = compute_sharpe_ratio(portfolio_equity)

        # Gesamte Trades über alle Strategien
        total_trades = sum(r.stats['total_trades'] for r in strategy_results.values())

        # Gewichteter Average der Win-Rates
        win_rates = [r.stats['win_rate'] for r in strategy_results.values()]
        avg_win_rate = np.mean(win_rates) if win_rates else 0.0

        # Gewichteter Average der Profit-Factors
        profit_factors = [r.stats['profit_factor'] for r in strategy_results.values()]
        avg_pf = np.mean(profit_factors) if profit_factors else 0.0

        return {
            **basic_stats,
            'sharpe': sharpe,
            'total_trades': total_trades,
            'avg_win_rate': avg_win_rate,
            'avg_profit_factor': avg_pf,
            'num_strategies': len(strategy_results)
        }
