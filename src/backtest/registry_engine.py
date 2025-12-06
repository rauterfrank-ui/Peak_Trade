"""
Peak_Trade Backtest Engine - Registry Integration
==================================================
Erweitert die BacktestEngine um Registry-Support für Portfolio-Backtests.

NEU: run_portfolio_from_registry()
- Lädt Strategien automatisch aus config.toml
- Nutzt Portfolio-Config für Multi-Strategy-Backtests
- Integriert Metadata-Filtering (Regime, Timeframe, Risk-Level)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from ..core.config_registry import (
    get_config,
    get_active_strategies,
    get_strategy_config,
    get_strategies_by_regime,
    list_strategies,
)
from ..strategies import load_strategy
from .engine import BacktestEngine, BacktestResult

logger = logging.getLogger(__name__)


@dataclass
class PortfolioBacktestResult:
    """
    Ergebnis eines Portfolio-Backtests über mehrere Strategien.
    
    Attributes:
        strategy_results: Dict[strategy_name, BacktestResult]
        combined_equity: Combined Equity Curve (gleichgewichtet oder nach Portfolio-Config)
        combined_stats: Aggregierte Stats über alle Strategien
        portfolio_config: Verwendete Portfolio-Konfiguration
        active_strategies: Liste der gebacktesteten Strategien
    """
    strategy_results: Dict[str, BacktestResult]
    combined_equity: pd.Series
    combined_stats: Dict[str, float]
    portfolio_config: Dict[str, Any]
    active_strategies: List[str]
    
    def get_best_strategy(self, metric: str = "sharpe") -> str:
        """Gibt Namen der besten Strategie nach Metrik zurück."""
        best_name = None
        best_value = -np.inf
        
        for name, result in self.strategy_results.items():
            value = result.stats.get(metric, -np.inf)
            if value > best_value:
                best_value = value
                best_name = name
        
        return best_name or ""
    
    def get_strategy_weights(self) -> Dict[str, float]:
        """Berechnet Strategiegewichte basierend auf Portfolio-Config."""
        weights = self.portfolio_config.get("weights", {})
        
        if not weights:
            # Gleichgewichtung
            n = len(self.active_strategies)
            weights = {name: 1.0 / n for name in self.active_strategies}
        
        return weights


def run_portfolio_from_registry(
    df: pd.DataFrame,
    cfg: Optional[Dict[str, Any]] = None,
    regime_filter: Optional[str] = None,
    timeframe_filter: Optional[str] = None,
    risk_level_filter: Optional[str] = None,
    strategy_names: Optional[List[str]] = None,
    combine_method: str = "equal_weight",
) -> PortfolioBacktestResult:
    """
    Führt Portfolio-Backtest mit Strategien aus der Registry durch.
    
    Workflow:
    1. Lädt aktive Strategien aus config.toml (oder custom cfg)
    2. Optional: Filtert nach Regime/Timeframe/Risk-Level
    3. Lädt Strategy-Functions dynamisch
    4. Führt Backtest für jede Strategie aus
    5. Kombiniert Ergebnisse zu Portfolio-Equity
    
    Args:
        df: OHLCV-DataFrame (DatetimeIndex, Spalten: open, high, low, close, volume)
        cfg: Optional custom Config-Dict (default: lädt aus config.toml)
        regime_filter: Nur Strategien für dieses Regime ("trending", "ranging", "any")
        timeframe_filter: Nur Strategien für diesen Timeframe (z.B. "1h")
        risk_level_filter: Nur Strategien mit diesem Risk-Level (z.B. "low", "medium")
        strategy_names: Optional explizite Liste von Strategie-Namen (überschreibt active)
        combine_method: Wie Ergebnisse kombiniert werden:
            - "equal_weight": Gleichgewichtung
            - "portfolio_weights": Aus config.toml [portfolio.weights]
            - "sharpe_weighted": Gewichtet nach Sharpe-Ratio
    
    Returns:
        PortfolioBacktestResult mit Individual- und Combined-Ergebnissen
    
    Example:
        >>> from src.backtest.registry_engine import run_portfolio_from_registry
        >>> 
        >>> # Alle aktiven Strategien
        >>> result = run_portfolio_from_registry(df)
        >>> 
        >>> # Nur Trending-Strategien
        >>> result = run_portfolio_from_registry(df, regime_filter="trending")
        >>> 
        >>> # Explizite Strategien
        >>> result = run_portfolio_from_registry(
        ...     df, 
        ...     strategy_names=["ma_crossover", "momentum"]
        ... )
    """
    # Config laden
    if cfg is None:
        cfg = get_config()
    
    # Strategien auswählen
    if strategy_names is not None:
        # Explizit übergeben
        selected_strategies = strategy_names
    elif regime_filter is not None:
        # Nach Regime filtern
        selected_strategies = get_strategies_by_regime(regime_filter)
        # Nur aktive
        active = get_active_strategies()
        selected_strategies = [s for s in selected_strategies if s in active]
    else:
        # Alle aktiven
        selected_strategies = get_active_strategies()
    
    # Optional: Weitere Filter
    if timeframe_filter or risk_level_filter:
        filtered = []
        for name in selected_strategies:
            strat_cfg = get_strategy_config(name)
            
            # Timeframe-Check
            if timeframe_filter and strat_cfg.metadata:
                recommended = strat_cfg.metadata.get("recommended_timeframes", [])
                if timeframe_filter not in recommended:
                    continue
            
            # Risk-Level-Check
            if risk_level_filter and strat_cfg.metadata:
                risk_level = strat_cfg.metadata.get("risk_level", "")
                if risk_level != risk_level_filter:
                    continue
            
            filtered.append(name)
        
        selected_strategies = filtered
    
    if not selected_strategies:
        raise ValueError(
            f"Keine Strategien gefunden für Filter: "
            f"regime={regime_filter}, timeframe={timeframe_filter}, "
            f"risk_level={risk_level_filter}"
        )
    
    logger.info(f"Running portfolio backtest with {len(selected_strategies)} strategies: {selected_strategies}")
    
    # Engine initialisieren
    engine = BacktestEngine()
    
    # Backtest für jede Strategie
    strategy_results: Dict[str, BacktestResult] = {}
    
    for name in selected_strategies:
        logger.info(f"Backtesting strategy: {name}")
        
        # Strategie-Config laden
        strat_cfg = get_strategy_config(name)
        params = strat_cfg.to_dict()  # Merged defaults + strategy-specific
        
        # Strategy-Function laden
        try:
            strategy_fn = load_strategy(name)
        except Exception as e:
            logger.error(f"Failed to load strategy '{name}': {e}")
            continue
        
        # Backtest durchführen
        try:
            result = engine.run_realistic(
                df=df,
                strategy_signal_fn=strategy_fn,
                strategy_params=params,
            )
            result.strategy_name = name
            strategy_results[name] = result
            
            logger.info(
                f"✅ {name}: Sharpe={result.stats['sharpe']:.2f}, "
                f"Trades={result.stats['total_trades']}, "
                f"WinRate={result.stats['win_rate']:.1%}"
            )
        except Exception as e:
            logger.error(f"Backtest failed for '{name}': {e}")
            continue
    
    if not strategy_results:
        raise ValueError("No successful backtests!")
    
    # Portfolio-Equity kombinieren
    combined_equity, combined_stats = _combine_portfolio_results(
        strategy_results,
        method=combine_method,
        portfolio_config=cfg.get("portfolio", {}),
    )
    
    return PortfolioBacktestResult(
        strategy_results=strategy_results,
        combined_equity=combined_equity,
        combined_stats=combined_stats,
        portfolio_config=cfg.get("portfolio", {}),
        active_strategies=selected_strategies,
    )


def _combine_portfolio_results(
    strategy_results: Dict[str, BacktestResult],
    method: str,
    portfolio_config: Dict[str, Any],
) -> tuple[pd.Series, Dict[str, float]]:
    """
    Kombiniert Individual-Ergebnisse zu Portfolio-Equity.
    
    Args:
        strategy_results: Dict von BacktestResults
        method: Kombinations-Methode
        portfolio_config: Portfolio-Config aus TOML
    
    Returns:
        (combined_equity_series, combined_stats_dict)
    """
    if not strategy_results:
        raise ValueError("No strategy results to combine")
    
    # Equity-Curves sammeln
    equity_curves = {name: result.equity_curve for name, result in strategy_results.items()}
    
    # Returns berechnen für jede Strategie
    returns = {}
    for name, equity in equity_curves.items():
        returns[name] = equity.pct_change().fillna(0)
    
    returns_df = pd.DataFrame(returns)
    
    # Gewichte bestimmen
    if method == "equal_weight":
        weights = {name: 1.0 / len(strategy_results) for name in strategy_results.keys()}
    
    elif method == "portfolio_weights":
        weights = portfolio_config.get("weights", {})
        # Normalize falls nicht vorhanden
        if not weights:
            weights = {name: 1.0 / len(strategy_results) for name in strategy_results.keys()}
        # Normalize auf 1.0
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}
    
    elif method == "sharpe_weighted":
        # Gewichte nach Sharpe-Ratio
        sharpes = {name: result.stats.get("sharpe", 0.0) for name, result in strategy_results.items()}
        # Nur positive Sharpes
        sharpes = {k: max(v, 0.01) for k, v in sharpes.items()}
        total = sum(sharpes.values())
        weights = {k: v / total for k, v in sharpes.items()}
    
    else:
        raise ValueError(f"Unknown combine_method: {method}")
    
    logger.info(f"Portfolio weights ({method}): {weights}")
    
    # Gewichtete Returns
    weighted_returns = pd.Series(0.0, index=returns_df.index)
    for name, weight in weights.items():
        if name in returns_df.columns:
            weighted_returns += returns_df[name] * weight
    
    # Combined Equity
    initial_capital = list(strategy_results.values())[0].equity_curve.iloc[0]
    combined_equity = initial_capital * (1 + weighted_returns).cumprod()
    
    # Combined Stats
    from .stats import compute_basic_stats, compute_sharpe_ratio
    
    basic_stats = compute_basic_stats(combined_equity)
    sharpe = compute_sharpe_ratio(combined_equity)
    
    # Aggregierte Trade-Stats
    total_trades = sum(r.stats.get("total_trades", 0) for r in strategy_results.values())
    avg_win_rate = np.mean([r.stats.get("win_rate", 0) for r in strategy_results.values()])
    
    combined_stats = {
        **basic_stats,
        "sharpe": sharpe,
        "total_trades": total_trades,
        "avg_win_rate": avg_win_rate,
        "num_strategies": len(strategy_results),
        "combine_method": method,
    }
    
    return combined_equity, combined_stats


def run_single_strategy_from_registry(
    df: pd.DataFrame,
    strategy_name: str,
    cfg: Optional[Dict[str, Any]] = None,
) -> BacktestResult:
    """
    Führt Backtest für eine einzelne Strategie aus der Registry aus.
    
    Convenience-Funktion für Single-Strategy-Backtests mit Registry-Config.
    
    Args:
        df: OHLCV-DataFrame
        strategy_name: Name der Strategie (muss in config.toml definiert sein)
        cfg: Optional custom Config
    
    Returns:
        BacktestResult für die Strategie
    
    Example:
        >>> result = run_single_strategy_from_registry(df, "ma_crossover")
        >>> print(f"Sharpe: {result.stats['sharpe']:.2f}")
    """
    # Config laden
    if cfg is None:
        cfg = get_config()
    
    # Strategie-Config laden
    strat_cfg = get_strategy_config(strategy_name)
    params = strat_cfg.to_dict()
    
    # Strategy-Function laden
    strategy_fn = load_strategy(strategy_name)
    
    # Engine initialisieren & Backtest
    engine = BacktestEngine()
    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=strategy_fn,
        strategy_params=params,
    )
    result.strategy_name = strategy_name
    
    return result
